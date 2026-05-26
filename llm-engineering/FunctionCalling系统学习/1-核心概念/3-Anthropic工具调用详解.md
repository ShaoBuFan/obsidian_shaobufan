---
tags:
  - FunctionCalling系统学习
  - 概念/tool-use
  - 平台/Anthropic
created: 2026-05-26
status: in-progress
---

# Anthropic 工具调用详解

## 哲学差异：先理解后行动

在研究 Anthropic 的 API 细节之前，有必要先理解它在设计哲学上与 OpenAI 的根本差异。

> Anthropic 的工具调用设计假设是：模型应该在**充分推理**之后才决定是否调用工具。这与 OpenAI 的"把工具调用当作一种带约束的输出模式"不同——Anthropic 更强调工具调用与思考过程的**连续性**。

这一哲学差异体现在多个设计细节中——我们会在下文中逐一指出。

## 工具定义结构

Anthropic 的工具定义结构比 OpenAI 更扁平。工具放在请求体的 `tools` 数组中，每个工具直接包含 `name`、`description`、`input_schema`：

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 1024,
  "messages": [
    {"role": "user", "content": "北京今天多少度？"}
  ],
  "tools": [
    {
      "name": "get_weather",
      "description": "获取指定城市的当前天气",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "城市和州/省，如 San Francisco, CA"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "温度单位"
          }
        },
        "required": ["location"],
        "additionalProperties": false
      }
    }
  ]
}
```

与 OpenAI 的关键差异：
- 不需要外层 `{"type": "function", "function": {...}}` 嵌套
- Schema 字段名叫 `input_schema` 而非 `parameters`
- `additionalProperties: false` 是**强制要求**（所有对象都必须设置）

Anthropic 也支持 ==Strict Tool Use==——在工具定义中设置 `"strict": true`，模型保证生成的参数 JSON 与 Schema 100% 匹配。底层原理与 OpenAI 的 `strict: true` 类似：首次请求有一次性的语法编译开销（约 200-500ms），结果缓存 24 小时。要求 Sonnet 4.5、Opus 4.5 及以上模型。

### JSON Schema 支持范围（截止 2026 年 5 月）

Anthropic 的 Schema 支持比 OpenAI 更受限（截止 2026 年 5 月）：

**支持的**：
- 基本类型：`object`、`array`、`string`、`integer`、`number`、`boolean`、`null`
- `enum`、`const`
- `$ref`/`$def`
- 嵌套在 `properties` 内部的 `anyOf`（用于可选字段等场景）
- 字符串格式：`date-time`、`time`、`date`、`duration`、`hostname`、`uri`、`ipv4`、`ipv6`、`uuid`

**不支持的**：
- **顶层** `oneOf`、`anyOf`、`allOf`（API 直接返回 400）
- 数值约束：`minimum`、`maximum`、`multipleOf`
- 字符串约束：`minLength`、`maxLength`、`pattern`
- 复杂数组约束
- 递归 Schema

> 一个重要的工程细节：Python 和 TypeScript SDK 会自动**剥离**不支持的约束并做客户端侧校验。但顶层的 `oneOf`/`anyOf` SDK 无法自动修复——你需要改用判别字段（`kind`/`type`）模式，在嵌套 `properties` 内使用 `anyOf`。

### Server Tool Use 与 MCP

Anthropic 支持将工具定义在服务端侧（通过 API 配置或 MCP Server），而不是每次请求都传入完整的工具列表。

> Server Tool Use 的核心价值是将**工具管理**（有哪些工具、Schema 怎么定义、权限怎么控制）与**请求逻辑**（这次对话要做什么）分离。对于有大量工具的企业应用，这避免了每次请求都传几十个工具定义的浪费——既省 token，也减少模型被过多工具干扰的风险。

==MCP（Model Context Protocol）== 是 Anthropic 于 2024 年 11 月开源的标准化工具协议，目前已成为连接 AI Agent 与外部工具的**行业基础设施**。截止 2026 年初，MCP 月 SDK 下载量从 10 万增长到 9700 万，已于 2025 年 12 月捐赠给 Linux Foundation 的 Agentic AI Foundation（与 Block 和 OpenAI 共同创立）。

MCP 的关键特性：
- **工具发现**：到 2026 年 1 月，Anthropic 推出了 Tool Search——用语义搜索按需选取 3-5 个相关工具，而非预加载全部工具定义。token 消耗从 ~134K 降至 ~5K（减少 85%）
- **工具调用示例**：支持在工具定义中附带 few-shot 示例，将参数准确率从 72% 提升到 90%
- **Protocol Architecture**：基于 JSON-RPC 2.0，三种原语——Tools（可调用操作）、Resources（只读上下文数据）、Prompts（可复用模板）

## `tool_choice` 的完整选项

Anthropic 的 `tool_choice` 始终是对象格式（不提供字符串简写）：

```json
// 自动模式（默认）
{"type": "auto"}

// 必须使用至少一个工具
{"type": "any"}

// 必须使用指定工具
{"type": "tool", "name": "get_weather"}

// 禁止使用工具
{"type": "none"}
```

### 并行调用控制

任何 `tool_choice` 值都可以附加 `disable_parallel_tool_use: true` 来禁用并行调用：

```json
{
  "tool_choice": {
    "type": "auto",
    "disable_parallel_tool_use": true
  }
}
```

### 行为差异

不同 `tool_choice` 值会影响模型的推理行为：

| tool_choice | 推理链 | 何时使用 |
|---|---|---|
| `auto` | 保留完整思维链 | 对话型应用，模型需要自行判断 |
| `any` / `tool` | 跳过可见推理，直接生成工具调用 | 确保结构化输出，或你已知需要调用工具 |
| `none` | 纯文本推理 | 隔离工具上下文，或纯对话场景 |

> `any` 和 `tool` 跳过推理链意味着更少的输出 token 和更低的延迟——但代价是失去了模型"思考要不要调用工具"的过程。对于复杂的工具决策场景，这可能降低准确性。

## Content Block 体系

这是 Anthropic API 设计中最区别于 OpenAI 的地方。Anthropic 不把工具调用当作 message 的一个附属字段，而是当作 ==content block==——与文本块、图片块平级的**一等内容单元**。

### 请求中的 Content Block 类型

```
message.content = [
    {"type": "text",     "text": "..."},
    {"type": "image",    "source": {...}},
    {"type": "tool_use",  "id": "toolu_xxx", "name": "...", "input": {...}},
    {"type": "tool_result", "tool_use_id": "toolu_xxx", "content": "..."}
]
```

### tool_use block（模型生成的工具调用）

```json
{
  "type": "tool_use",
  "id": "toolu_01ABC123...",
  "name": "get_weather",
  "input": {
    "location": "Beijing",
    "unit": "celsius"
  }
}
```

关键点：
- `input` 是**已解析的 JSON 对象**，不是字符串——不需要手动 `JSON.parse()`
- `id` 以 `toolu_` 为前缀，由模型生成
- `name` 直接是工具名，没有中间嵌套

### tool_result block（你返回的工具执行结果）

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01ABC123...",
  "content": [
    {
      "type": "text",
      "text": "北京当前温度 25°C，晴"
    }
  ],
  "is_error": false
}
```

关键点：
- `content` 可以是字符串或 content block 数组（支持多模态结果）
- `tool_use_id` 匹配模型生成的 tool_use block 的 id
- `is_error: true` 标记工具执行失败——==设置此标记后模型会自动重试或被引导到错误处理路径==

> `is_error` 是一个被严重低估的设计。它让错误处理变成了 API 的内置语义，而不是需要你在 prompt 里教的"约定"。当工具失败时，设置 `is_error: true` 比返回 `{"error": "xxx"}` 字符串远更可靠。

## Anthropic 独有的特性

### 1. Programmatic Tool Calling（PTC，2025 年 11 月发布）

PTC 是 Anthropic 工具调用栈中最具差异化的能力。传统工具调用是一个工具一次往返——调用 tool_A → 等结果 → 调用 tool_B → 等结果——每次中间结果都塞进上下文窗口。PTC 改变了这个范式：==模型编写 Python 代码来编排多个工具调用，代码在沙箱中执行，只有最终输出进入上下文窗口==。

```
传统 Tool Calling:  模型 → tool_A → 模型 → tool_B → 模型 → tool_C → 模型
PTC:                模型 → code(tool_A, tool_B, tool_C) → 最终结果 → 模型
```

官方的性能数据：
- 复杂研究任务 token 消耗从 43,588 降至 27,297（减少 37%）
- BrowseComp 和 DeepsearchQA 准确率平均提升 11%，输入 token 减少 24%
- Opus 4.6 + PTC 登顶 LMarena Search Arena 第一名

> PTC 的适用场景：工具数超过 5 个的多步编排、需要条件分支和循环的工具调用链、大规模数据处理和聚合。对于简单的单工具调用，PTC 反而增加了不必要的代码执行开销。

### 2. 计算机使用（Computer Use）

Anthropic 提供了专门的 `computer_20250124` 工具，让模型直接操控桌面环境——移动鼠标、点击、输入文字、截图分析。这超出了 Function Calling 的范畴，属于 ==agentic tool use==——工具不再是"查个天气"这种单次调用，而是一个持续的、带反馈回路的交互过程。

> Computer Use 暗示了 Tool Use 的演进方向：从"模型调用你的工具"到"模型本身就是工具的操控者"。当工具足够通用（比如一台计算机），模型的工具调用能力就成了通用 agent 能力的底座。

### 3. Fine-Grained Tool Streaming（GA，2026 年 2 月随 Opus 4.6 发布）

标准流式需要等待整个工具调用的 JSON 生成完成才能解析——Fine-Grained Tool Streaming 允许**增量地**获取参数值。已于 2026 年 2 月随 Opus 4.6 正式 GA，启用方式为 `fine_grained=True`（不再需要 beta header）。

关键行为：
- 参数值逐片段到达，不等整个 JSON 完成
- 接收到的片段可能是**不完整的或不合法的 JSON**
- 如果 `stop_reason` 是 `max_tokens`，流可能在参数中间截断
- 向模型返回错误时，不完整的 JSON 需要这样包装：`{"INVALID_JSON": "<truncated json string>"}`

> 这个特性对于大参数工具调用（比如 code execution 传入几百行代码）特别有价值——你可以在代码还在流式生成时就开始 token 级别的处理，大幅降低感知延迟。

### 4. Structured Outputs（GA，2026 年 2 月发布）

Anthropic 的 Structured Outputs 已于 2026 年 2 月 4 日正式 GA，无需 beta header。注意 API 的重大变化：==`output_format` 已废弃，替换为 `output_config.format`==（随 Opus 4.6 引入的 breaking change）。

与 Strict Tool Use 不同，Structured Outputs 是针对**纯文本输出**的 Schema 保证——不涉及工具调用，而是让模型直接返回符合 JSON Schema 的结构化文本：

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["name", "email"],
                "additionalProperties": False
            }
        }
    }
)
```

支持的模型：Opus 4.7、Opus 4.6、Sonnet 4.6、Sonnet 4.5、Opus 4.5、Haiku 4.5。

> 三个概念的区分：==Tool Use== 是模型表达"我想调用这个工具"；==Strict Tool Use==（工具定义中的 `strict: true`）确保工具参数严格匹配 Schema；==Structured Outputs==（`output_config.format`）确保纯文本输出匹配 Schema，不涉及工具。前两者是一起用的，后者是独立功能。还有一个重要限制：每个请求最多 ~24 个可选参数和 20 个 strict 工具。

## 流式处理完整流程

Anthropic 的 SSE 流式事件序列是两平台中最详细的（以下示例使用 `claude-sonnet-4-6`）：

```
message_start           →  message.id, model, usage.input_tokens
  │
  ├─ content_block_start   →  index=0, content_block.type="text"
  ├─ content_block_delta   →  index=0, delta.type="text_delta", text="让我查一下..."
  └─ content_block_stop    →  index=0
  │
  ├─ content_block_start   →  index=1, type="tool_use", name="get_weather", id="toolu_01ABC..."
  ├─ content_block_delta   →  index=1, delta.type="input_json_delta", partial_json='{"lo'
  ├─ content_block_delta   →  index=1, delta.type="input_json_delta", partial_json='cation"'
  └─ content_block_stop    →  index=1  ← 此时解析完整的 JSON
  │
message_delta            →  stop_reason="tool_use", usage.output_tokens
message_stop             →  流结束
```

各事件类型的含义：

| 事件 | 含义 | 关键字段 |
|------|------|----------|
| `message_start` | 消息开始 | `message.id`, `model`, `usage` |
| `content_block_start` | 内容块开始 | `index`, `content_block.type`, `tool_use` 时还有 `name` 和 `id` |
| `content_block_delta` | 内容块增量 | `index`, `delta.type`（`text_delta` / `input_json_delta` / `thinking_delta`） |
| `content_block_stop` | 内容块结束 | `index` |
| `message_delta` | 消息级更新 | `stop_reason`, `usage.output_tokens` |
| `message_stop` | 消息结束 | — |
| `ping` | 心跳 | — |

### 流式工具调用的解析策略

```python
# 核心解析逻辑
import json

buffers = {}  # index → {"type": str, "id": str, "name": str, "input_json": str}

for event in stream:
    if event.type == "content_block_start":
        idx = event.index
        block = event.content_block
        if block.type == "tool_use":
            buffers[idx] = {
                "id": block.id,
                "name": block.name,
                "input_json": ""
            }

    elif event.type == "content_block_delta":
        if event.delta.type == "input_json_delta":
            buffers[event.index]["input_json"] += event.delta.partial_json

    elif event.type == "content_block_stop":
        idx = event.index
        if idx in buffers:
            # 零参数工具可能没有 delta，回退到 "{}"
            raw = buffers[idx]["input_json"] or "{}"
            buffers[idx]["input"] = json.loads(raw)

    elif event.type == "message_delta":
        if event.delta.stop_reason == "tool_use":
            # 需要执行工具
            execute_tools(buffers.values())
```

> 零参数工具是一个容易漏掉的边界情况：它会直接 `content_block_start` → `content_block_stop`，中间没有任何 `content_block_delta`。所以解析时需要对 `input_json` 做 `or "{}"` 回退。

## 多轮工具调用

Anthropic 的多轮工具调用遵循严格的 content block 追加模式：

```
第1轮:
  user:     [{"type": "text", "text": "北京天气？"}]
  assistant: [{"type": "text", "text": "让我查一下..."},
              {"type": "tool_use", "id": "toolu_01", "name": "get_weather", "input": {...}}]
  stop_reason: "tool_use"

第2轮:
  user:     [{"type": "tool_result", "tool_use_id": "toolu_01", "content": "25°C"}]
  assistant: [{"type": "text", "text": "北京现在 25 度，挺舒服的。"}]
  stop_reason: "end_turn"
```

注意：==Anthropic 不区分 user message 和 tool message==——工具结果是一个 type 为 `tool_result` 的 content block，放在 user role 的 message 中。这与 OpenAI 使用独立的 `tool` role 有根本区别。

### Python SDK 完整多轮示例

```python
import anthropic

client = anthropic.Anthropic()

# 定义工具
tools = [{
    "name": "get_weather",
    "description": "获取指定城市的当前天气",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "城市名"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location"],
        "additionalProperties": False
    }
}]

# 第一轮：用户提问
messages = [{"role": "user", "content": "北京今天多少度？"}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

# 如果模型决定调用工具
if response.stop_reason == "tool_use":
    # 将 assistant 的响应追加到对话历史
    messages.append({
        "role": "assistant",
        "content": [block.model_dump() for block in response.content]
    })

    # 执行工具并构造 tool_result
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            # 执行实际工具（这里是模拟）
            result = f"{block.input['location']}当前温度 25°C"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
            })

    # 将工具结果作为 user message 追加
    messages.append({"role": "user", "content": tool_results})

    # 第二轮：获取最终回复
    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=messages
    )
    print(final_response.content[0].text)
```

> 对比 OpenAI 版本的代码：Anthropic 需要操作 content block 数组，而不是消息数组。对于同时包含文本块和工具调用块的响应，需要按 index 顺序处理每一个 block——不能假设响应里只有工具调用。

## 思考题

1. PTC 将工具编排从"多次 API 往返"变成了"一次代码执行"。这种范式变化带来了 token 消耗的大幅降低，但也引入了新的安全风险——模型生成的代码在沙箱中执行，如果沙箱逃逸会发生什么？PTC 的安全边界应该画在哪里？
2. Anthropic 选择将 `tool_result` 放在 `user` role 中（而非独立的 `tool` role），但通过 content block type 来区分。这种设计与 OpenAI 的独立 `role: "tool"` 相比，在实现多轮对话管理时有哪些不同的复杂度？
3. MCP 已成为连接 AI Agent 与外部工具的行业标准，但它在协议层面不解决 prompt injection、权限控制、审计追踪等问题。如果你在构建一个调用敏感工具（如数据库写入）的 MCP 生态，这些缺口应该如何填补？
4. Anthropic 的 `output_format` 在 Opus 4.6 中废弃，改为 `output_config.format`——这是一个 breaking change。如果你是 Anthropic 的 API 设计者，你会选择何种策略来减少这类迁移的痛苦？
