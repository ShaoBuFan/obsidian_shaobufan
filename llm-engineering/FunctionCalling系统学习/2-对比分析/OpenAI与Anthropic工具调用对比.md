---
tags:
  - FunctionCalling系统学习
  - 对比分析
  - 平台/OpenAI
  - 平台/Anthropic
created: 2026-05-26
status: in-progress
---

# OpenAI vs Anthropic 工具调用全面对比

## 先看全景

两家的工具调用能力在功能层面已经趋同——都能定义工具、控制调用行为、流式返回、并行调用、保证结构化输出。但==在 API 设计、架构选择、工程细节上，反映出根本不同的设计哲学==。

> OpenAI 把工具调用设计为**消息的一个属性**——它发生在 message 层面。
> Anthropic 把工具调用设计为**内容的一种类型**——它发生在 content block 层面。

这个分歧引出了之后几乎所有的差异。

## 核心架构对比

```
OpenAI 的消息模型（层级结构）:
message
  ├── role: "assistant"
  ├── content: "让我查一下..." | null
  └── tool_calls: [
        {id, type: "function", function: {name, arguments: "JSON字符串"}}
      ]

Anthropic 的 content block 模型（扁平序列）:
message
  └── content: [
        {type: "text", text: "让我查一下..."},
        {type: "tool_use", id: "toolu_xxx", name: "get_weather", input: {已解析的对象}},
        {type: "tool_result", tool_use_id: "toolu_xxx", content: "25°C"}
      ]
```

### 架构差异的连锁反应

| 维度 | OpenAI | Anthropic | 影响 |
|------|--------|-----------|------|
| 工具调用与文本的关系 | 分开的字段：`content` 和 `tool_calls` | 同级的 content block：`text`、`tool_use`、`tool_result` | Anthropic 可以自然地交错排列文本和工具调用，OpenAI 需要在 message 层面管理顺序 |
| 参数的格式 | JSON **字符串**（需手动 parse） | 已解析的 JSON **对象** | OpenAI 在流式场景下管理更简单（只管拼字符串），Anthropic 在非流式场景更方便 |
| 工具结果的角色 | 独立的 `role: "tool"` | `role: "user"` 内的 `tool_result` block | Anthropic 把工具结果视为用户提供的上下文；OpenAI 给予它独立身份 |
| 错误处理 | 无内置机制，靠约定 | 内置 `is_error: true` 字段 | Anthropic 的错误处理是 API 的一等语义，OpenAI 需要开发者自己实现 |

## API 参数对比

### 工具定义

| 维度 | OpenAI | Anthropic |
|------|--------|-----------|
| 嵌套层数 | 3 层（`tools[].function.parameters`） | 2 层（`tools[].input_schema`） |
| Schema 约束的严格程度 | `strict: true` 开启后严格遵守 | 始终严格（不支持的约束被 SDK 剥离） |
| `additionalProperties: false` | strict 模式下必须 | **始终必须** |
| 可选字段 | `"type": ["string", "null"]` 且必须列入 `required` | `"type": ["string", "null"]` 且必须列入 `required` |
| 顶层 `oneOf`/`anyOf` | 支持 | **不支持**（需改用判别字段 + 嵌套 anyOf） |
| 数值/字符串约束 | 支持 | 不支持（SDK 剥离） |

> OpenAI 的 Schema 支持更全面，但 Anthropic 的 SDK 做了客户端侧补全——两者的实践差距比规范差距小得多。

### `tool_choice` 控制

| 控制项 | OpenAI | Anthropic |
|--------|--------|-----------|
| 自动决策 | `"auto"` | `{"type": "auto"}` |
| 强制调用 | `"required"` | `{"type": "any"}` |
| 指定工具 | `{"type": "function", "function": {"name": "x"}}` | `{"type": "tool", "name": "x"}` |
| 禁用工具 | `"none"` | `{"type": "none"}` |
| 禁用并行 | `parallel_tool_calls: false`（独立字段） | `disable_parallel_tool_use: true`（tool_choice 的子字段） |
| 对推理链的影响 | 无文档说明 | `any`/`tool` 跳过可见推理链 |

> Anthropic 明确文档化了不同 `tool_choice` 值对推理行为的影响。OpenAI 在这方面相对不透明。

### 流式处理

| 维度 | OpenAI | Anthropic |
|------|--------|-----------|
| 事件粒度 | Chunk（消息级） | Event（内容块级） |
| 工具调用增量 | `delta.tool_calls[].function.arguments` 字符串片段 | `content_block_delta` 的 `partial_json` 字符串片段 |
| 多工具并行区分 | `tool_calls[].index` | `content_block_start.index` |
| 块边界语义 | 无显式的块开始/结束事件 | 三件套：`content_block_start` → `content_block_delta`* → `content_block_stop` |
| 增量工具流式（参数级） | 不支持 | Fine-Grained Tool Streaming（GA，`fine_grained=True`） |
| 心跳 | 无 | `ping` 事件 |
| 代码级工具编排 | 不支持 | Programmatic Tool Calling（PTC） |
| 标准化工具协议 | MCP（通过 Agents SDK） | MCP（原生深度整合，已捐赠 Linux Foundation） |

Anthropic 的流式事件设计更加结构化——每个 content block 有明确的开始、增量、结束生命周期。这带来一个实际好处：==你可以在 `content_block_start` 时就知道这个块是什么类型的==（文本还是工具调用），而不必等到内容到达。

```
OpenAI 流式（需猜测）:
  收到 delta.tool_calls[0].id → "哦，原来这是一个工具调用"

Anthropic 流式（提前知道）:
  收到 content_block_start, type="tool_use" → "这是一个工具调用，准备缓冲 JSON"
```

## 设计哲学的深层分歧

### 1. 工具调用是否"打断"文本生成

**OpenAI**：工具调用从 message 层面"替代"了内容——当 `tool_calls` 存在时，`content` 通常为 null。这暗示着一种"要么生成文字，要么调用工具"的二元思维。

**Anthropic**：文本块和工具调用块可以自然交替——模型可以生成一段推理文字，再调用一个工具，再生成一段文字，再调用另一个工具。这体现了"思考和行动是连续的"这一哲学。

### 2. 是否区分 user 和 tool

**OpenAI**：有 `role: "user"`、`role: "assistant"`、`role: "tool"`、`role: "system"` 四种角色。工具结果有自己的身份。

**Anthropic**：只有 `role: "user"` 和 `role: "assistant"`。工具结果放在 user message 的 content block 中，类型为 `tool_result`。

> 这一差异直接影响多轮对话管理。OpenAI 的方案让你可以按 role 筛选消息（"把所有 tool 消息取出来"），Anthropic 的方案需要按 content block type 筛选。在实现对话历史管理时，这两种策略对应不同的数据结构设计。

### 3. 安全哲学的差异

**OpenAI**：在文档中反复强调安全最佳实践——验证、确认、最小权限、防御注入。把安全责任放在**开发者**身上。

**Anthropic**：通过 API 设计本身内置了更多安全约束。例如：
- `is_error` 让错误处理成为 API 语义而非约定
- 更严格（且文档化）的 tool_choice 行为差异
- Content block 体系天然防止 tool_use 和 tool_result 的 ID 不匹配

> OpenAI 给你更大的灵活性，但需要你自己承担安全责任。Anthropic 通过约束设计来减少出错空间，但代价是灵活性稍低。

### 4. Token 消耗模型对比

工具调用涉及三种 token 消耗，两平台的计费方式不同：

| 消耗来源 | OpenAI | Anthropic |
|----------|--------|-----------|
| 工具定义（每次请求传入） | 计入 input tokens，按标准费率 | 计入 input tokens，按标准费率 |
| 模型生成的工具调用 | 计入 output tokens | 计入 output tokens |
| 工具结果（你返回的） | 计入 input tokens（下轮对话） | 计入 input tokens（下轮对话） |
| Server-side 工具定义 | 不支持 | 不计入单次请求的 input tokens |

> 工具定义本身消耗 token 是很多人忽略的成本。一个复杂的工具 Schema 可能有 500-1000 个等效 token。如果你有 20 个工具，每次请求都传，相当于每次请求都在为工具定义付费。Anthropic 的 Server Tool Use 和 OpenAI 的 Responses API 内置工具都是在试图降低这部分开销。

### 5. Prompt Injection 防护对比

两个平台都面临同样的威胁：用户输入中可能包含恶意指令，诱导模型产生不合预期的工具调用。

| 防护维度 | OpenAI | Anthropic |
|----------|--------|-----------|
| 内置输入过滤 | 无（依赖开发者自行实现） | 无（依赖开发者自行实现） |
| 文档中的安全指引 | 详细的安全最佳实践文档 | 通过 API 设计约束减少攻击面 |
| 工具调用验证 | `strict: true` 保证格式，不保证值的合法性 | `strict: true` 保证格式，不保证值的合法性 |
| 破坏性操作防护 | 文档建议加人工确认（无 API 级支持） | 文档建议加人工确认（无 API 级支持） |

> 关键结论：两个平台都没有在 API 层面解决 prompt injection 问题。这意味着防范注入的责任完全在开发者——无论用哪个平台，你都需要自己做输入过滤、参数验证、权限控制和破坏性操作确认。

## 场景选择指南

| 场景 | 推荐平台 | 原因 |
|------|----------|------|
| 快速原型、实验性项目 | OpenAI | 生态成熟、文档丰富、社区方案多 |
| 需要复杂推理 + 工具调用的场景 | Anthropic | 推理链 + content block 自然交替 |
| 多模态工具调用（图片作为工具输入/输出） | Anthropic | `tool_result.content` 支持多模态数组 |
| 多工具编排（5+ 工具，条件/循环逻辑） | Anthropic | PTC 大幅减少 token 和往返次数 |
| 高吞吐、低延迟的简单工具调用 | OpenAI | 更简洁的消息模型、更低的事件开销 |
| 需要同时调用大量工具的并行场景 | 持平 | 两家都支持，但都有各自的坑 |
| 错误处理要求高的场景 | Anthropic | `is_error` 内置语义 |
| 需要自定义 JSON Schema 约束的场景 | OpenAI | 支持更多 Schema 关键字 |
| 与 LangChain/LlamaIndex 等框架集成 | OpenAI | 生态支持更早更成熟 |
| 需要逐参数流式的大型工具调用 | Anthropic | Fine-Grained Tool Streaming（GA） |
| 需要标准化工具发现和管理 | 持平 | MCP 已成为行业标准，两家都支持 |

## 最新的趋势：向 Agents API 收敛

2025 年以来，两个平台都在从"提供工具调用的 API"转向"提供 Agent 的 API"。截止 2026 年 5 月，双方的能力版图：

- **OpenAI**：Responses API（GA）统一了多 API 能力，内置 web search、file search、code interpreter、image generation、shell tool。Chat Completions 无限期支持。Assistants API 将于 2026 年 8 月下线。已通过 Agents SDK 原生支持 MCP。
- **Anthropic**：Server Tool Use 与 MCP 深度整合，MCP 已成为行业基础设施（97M 月下载量，Linux Foundation 治理）。Programmatic Tool Calling（PTC）实现了代码级工具编排。Fine-Grained Tool Streaming 和 Structured Outputs 已于 2026 年 2 月 GA。

> 两个平台都在向同一个方向收敛：**工具调用逐渐变成底层细节，开发者更多地在 Agent 层面工作**——定义能力边界、管理工具生命周期、通过 MCP 标准化工具发现。差异在于：OpenAI 走的是"平台内置工具"路线（把 web search、code interpreter 做成托管服务），Anthropic 走的是"协议标准化"路线（通过 MCP 让任何工具服务器都能接入）。

## 不应该忽视的坑

### OpenAI

1. `gpt-4.1-nano` 并行调用 bug：在并行模式下可能产生重复的工具调用（截止 2026 年 5 月仍有社区报告），建议对该快照禁用并行
2. `strict: true` 要求 `required` 列出所有字段：可选字段必须用 `["string", "null"]` 并列入 required——这是一个反直觉的设计
3. `arguments` 是字符串：不要忘了 `JSON.parse()`，也没有类型提示
4. GPT-5.x 系列 strict 模式默认开启：可能导致旧的宽松 Schema 请求失败，需要显式关闭

### Anthropic

1. `additionalProperties: false` 忘记设置会导致 API 400 错误
2. 数值/字符串约束静默失败：SDK 会剥离不支持的约束，你可能以为传了但实际没传
3. 零参数工具没有 delta：解析时必须处理 `input_json` 为空字符串的边界情况
4. 顶层 `oneOf`/`anyOf` API 直接拒绝（400）：需改用判别字段模式
5. `output_format` 已在 Opus 4.6+ 中废弃：必须迁移到 `output_config.format`
6. Opus 4.6 移除了 assistant message prefill 功能
7. Opus 4.7 使用新 tokenizer（相同输入可能多消耗 35% token），且拒绝非默认 temperature/top_p/top_k

## 定价与延迟定量对比（2026 年 5 月）

工具调用的实际成本不仅包括 API 的 token 价格，还包括工具定义本身的 token 消耗和多次往返的累积效应。以下数据基于两平台官方定价页面和第三方基准测试。

### 主力模型 Token 定价（每百万 token，美元）

| 模型 | Input | Output | Output/Input 倍数 | 上下文窗口 |
|------|-------|--------|-------------------|-----------|
| **GPT-5** | $1.25 | $10.00 | 8x | 400K |
| **GPT-5.2** | $1.75 | $14.00 | 8x | 400K |
| **GPT-4.1**（GPT-4o 继任者） | $2.00 | $8.00 | 4x | 1M |
| **GPT-4o-mini** | $0.15 | $0.60 | 4x | 128K |
| **Claude Opus 4.6** | $5.00 | $25.00 | 5x | 1M |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | 5x | 1M |
| **Claude Haiku 4.5** | $1.00 | $5.00 | 5x | 200K |

> Anthropic 的所有模型保持统一的 5x 输出/输入比，OpenAI 的 GPT-5 系列和 GPT-4.1 系列的 ratio 不一致（4x-8x），在估算成本时需要注意。

### 成本节约选项

| 选项 | OpenAI | Anthropic |
|------|--------|-----------|
| **Batch API**（异步，24h） | 50% 折扣 | 50% 折扣 |
| **Prompt Caching** | 50% 折扣（自动，>1024 token 前缀匹配） | Cache write 1.25x input，cache read 0.1x input（手动标记断点） |
| **长上下文附加费**（>200K input） | GPT-4.1 不收费，GPT-5 系列有阶梯定价 | Input 2x，Output 1.5x |
| **Server Tool Use / MCP 工具** | 免工具定义 token（内置工具） | 免工具定义 token（服务端注入） |

### 工具调用的实际成本模型

一次典型的工具调用包含三轮 token 消耗：

```
第 1 轮：工具定义（input） + 用户消息（input） → 工具调用（output）
第 2 轮：工具结果（input） → 可能的新工具调用（output）
第 3 轮：累积上下文（input） → 最终回复（output）
```

以 Sonnet 4.6 为例，假设 3 个工具（每个约 200 token 定义）、用户消息 100 token、单次工具调用 50 output token、工具结果 500 token、最终回复 300 token：

- 第 1 轮：~700 input + 50 output = $0.00285
- 第 2 轮：~1250 input（含历史）+ 0 output = $0.00375
- 第 3 轮：~1250 input + 300 output = $0.00825
- **总计**：~$0.015

> 工具结果的大小是成本的最大变量。一个返回 8000 token 的工具结果（比如搜索结果或文档片段）会让后续每轮的 input token 膨胀，形成"成本复利"。==控制工具结果的粒度是控制成本最重要的杠杆，比选择模型更重要==。

### 延迟特征

基于 BFCL（Berkeley Function-Calling Leaderboard）和 AutoBench 的公开数据：

| 场景 | 典型延迟范围 | 关键影响因素 |
|------|------------|------------|
| 单次简单工具调用 | 4-9 秒 | 模型推理速度（TTFT + token/s） |
| 并行多工具调用（2-4 个） | 6-15 秒 | 模型并行生成开销，工具执行时间 |
| 多步工具编排（3-5 轮） | 15-60 秒 | 往返次数 ×（推理时间 + 工具执行时间） |
| 复杂 Agentic 流程 | 60-300+ 秒 | 同上，加上推理链生成和决策分支 |

关键发现：
- **工具执行时间通常大于模型推理时间**——实际 API 调用、数据库查询、网页抓取的时间是延迟的主要成分
- **PTC 减少往返次数可降低延迟 30-50%**——将 N 次往返压缩为 1 次代码执行
- **流式工具调用（Fine-Grained Streaming）可降低感知延迟**——不等 JSON 完成就开始处理
- **学术基准测试常低估真实延迟**——BFCL 等用 mock 后端，实际浏览器搜索等工具增加 5-10 秒额外延迟

### 性价比总结

```
如果你关心成本：GPT-5 ($1.25/$10) > Sonnet 4.6 ($3/$15) > Opus 4.6 ($5/$25)
如果你关心延迟：Fine-Grained Streaming + PTC 减少往返 > 单纯选快的模型
如果你关心工具调用质量：BFCL V4 排行榜 > 只看价格
如果你两者都要：Sonnet 4.6 + Batch API + Prompt Caching + 工具结果截断
```

## 思考题

1. 如果你需要开发一个同时支持 OpenAI 和 Anthropic 的工具调用框架，你会选择抽象到哪个层级？content block 级还是 message 级？为什么？
2. Anthropic 选择让 SDK 剥离不支持的 Schema 约束并做客户端校验。这是一个"静默修正"的设计——好处是使用方便，坏处是开发者可能不知道约束被忽略了。你认同这个设计吗？有什么更好的替代方案？
3. 随着 Agents API 的标准化（OpenAI Responses API、Anthropic MCP），Function Calling 会变成像 TCP 一样的"底层协议"——开发者很少直接操作它，而是通过更高层的 Agent 框架。你同意这个预测吗？如果同意，今天学习 Function Calling 的细节还有什么价值？
