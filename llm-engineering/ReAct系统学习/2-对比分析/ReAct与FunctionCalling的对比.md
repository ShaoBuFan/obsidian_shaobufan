---
tags:
  - ReAct系统学习
  - 对比分析
  - agent-architecture
  - tool-use
created: 2026-05-26
status: in-progress
---

# ReAct 与 Function Calling 的对比

## 它们是不同层面的东西

直接给结论：

> ReAct 是**决策框架**——决定"什么时候想、什么时候做、想什么、做什么"。
> Function Calling 是**执行机制**——决定"如何结构化地表达'做什么'"。

但这个分层在工程上远不够精确。把两者的关系说清楚，需要从五个维度拆解。

---

## 维度一：协议层 vs 策略层

| | ReAct | Function Calling |
|---|---|---|
| **层面** | 策略层（Agent 循环逻辑） | 协议层（API 接口规范） |
| **作用** | 定义 Thought → Action → Observation 的循环 | 定义 Action 的结构化表达（JSON Schema） |
| **谁控制** | 应用代码（while loop） | 模型 API（tool_calls） |
| **可替代方案** | Plan-Solve, Reflexion, ToT | 正则解析、结构化输出（json_schema） |

用代码来区分最清楚：

```python
# 策略层（ReAct 的职责）
while not task_complete:
    response = llm.generate(messages, tools)  # ← 协议层：Function Calling
    if response.has_tool_calls():
        for tc in response.tool_calls:
            result = execute_tool(tc)           # ← 协议层
            messages.append(tool_result(tc, result))  # ← 协议层
        # ReAct 的精髓在这行：将工具结果作为新的观察，让模型重新推理
        continue
    else:
        return response.content  # Final Answer
```

==ReAct 就是这个 `while` 循环==。Function Calling 是循环内部的 `tools` 参数和 `tool_calls` 响应。ReAct 不关心工具调用是用 Function Calling 实现的还是正则解析实现的——它只关心"循环要转几轮、每轮做什么决策"。

---

## 维度二：可靠性（从脆到稳的演进）

ReAct 原始论文的 Action 是自由文本：

```
Action: Search[Colorado orogeny]
Action: Lookup[eastern sector]
Action: Finish[1,800 to 7,000 ft]
```

解析这段文本需要正则表达式。格式错误率高达 ~23%——模型可能输出 `Action:Search[xxx]`（缺少空格）、`Action: Lookup[xxx]`（Lookup 不存在）、`Action: Let me search [xxx]`（自然语言）。

Function Calling 用 JSON Schema 约束替代了正则解析：

```json
{
  "tool_calls": [{
    "function": {
      "name": "web_search",
      "arguments": "{\"query\":\"Colorado orogeny\"}"
    }
  }]
}
```

| | ReAct 文本 Action | Function Calling |
|---|---|---|
| 格式保证 | 无 | `strict: true` 下 100% |
| 工具名称幻觉 | 可能出现不存在的工具 | 只能调用注册的工具 |
| 参数验证 | 开发者自己检查 | Schema 自动约束 |

> Function Calling 的出现让 ReAct 的 Action 执行从"脆弱的文本解析"变成了"可靠的 API 调用"。这是 ReAct 从学术概念走向生产系统的最关键一步。

---

## 维度三：可解释性（Function Calling 输掉的东西）

Function Calling 有一个被忽视的代价：==`tool_calls` JSON 替代了 Thought 文本==。

在 ReAct 中：
```
Thought: 我需要查科罗拉多造山运动，找到东部扇区，再查海拔。
Action: Search[Colorado orogeny]
```

在纯 Function Calling 中：
```
（没有 Thought）
tool_calls: [{"function": {"name": "web_search", "arguments": "{\"query\":\"Colorado orogeny\"}"}}]
```

当你需要审计"模型为什么调用了这个工具"时，ReAct 的 Thought 是有答案的——你看到模型的推理链。Function Calling 只给你 JSON，不给你解释。这对于：
- **调试**（为什么模型调用了错误工具？）
- **合规**（为什么触发了这个数据库操作？）
- **安全审计**（模型是否被 prompt injection 操控？）

——都是实际问题。

> 2025-2026 年的趋势是在 Function Calling **之上**恢复 ReAct 的可解释性：在 prompt 中要求模型先输出思考再调用工具（OpenAI 的 reasoning、Anthropic 的 thinking），或者将思考作为独立的 content block 类型。

---

## 维度四：并行能力（Function Calling 的结构优势）

ReAct 的原始设计是严格串行的：Thought₁ → Action₁ → Observation₁ → Thought₂ → ...

Function Calling 原生支持并行工具调用——一个 `tool_calls` 数组可以包含多个独立调用。以 Function Calling 为 Action 层的 ReAct 实现可以得到并行能力：

```python
# 并行 ReAct
response = llm.generate(messages, tools)
# response.tool_calls = [
#   {"name": "search", "args": {"query": "科罗拉多造山运动"}},
#   {"name": "search", "args": {"query": "东部扇区海拔"}},
#   {"name": "search", "args": {"query": "High Plains elevation"}}
# ]
# 三个搜索同时执行
results = await asyncio.gather(*[execute(tc) for tc in response.tool_calls])
```

文本 Action 的 ReAct 做不到这一点——除非你在 prompt 里显式教模型输出多个 Action 行。

---

## 维度五：可移植性（ReAct 的生存空间）

ReAct 只需要一个足够强的语言模型 + 精巧的 prompt。==它不要求模型支持 Function Calling API==。这意味着：

| 场景 | ReAct（文本 Action） | Function Calling |
|------|---------------------|-------------------|
| 开源模型（Llama, Phi） | 可用 | 取决于模型是否微调了 tool calling |
| 自定义微调模型 | 可用 | 需要专门的 tool calling 训练数据 |
| 教学、概念验证 | 可用（简单） | 需要 API 配置 |
| 生产级商业 API | 可用但不推荐 | 推荐 |

> ReAct 的文本 Action 模式在 Function Calling 不可用时是 fallback。在 2026 年，生产系统几乎全部使用 Function Calling + ReAct 的混合架构，但 ReAct 的文本模式仍然在开源模型和教学中占有一席之地。

---

## 综合：混合架构是唯一正确解

把五个维度的选择整合到一个决策框架中：

```
┌──────────────────────────────────────────────────┐
│                Agent 架构决策树                      │
├──────────────────────────────────────────────────┤
│                                                    │
│  模型支持 Function Calling 吗？                      │
│    ├─ 是 → 用 Function Calling 做 Action 执行       │
│    │      需要可解释的推理？                          │
│    │        ├─ 是 → ReAct 循环 + Thought 文本        │
│    │        └─ 否 → 简化循环（无显式 Thought）        │
│    │      需要全局规划？→ Plan-Solve 替代 ReAct       │
│    │      需要迭代改进？→ Reflexion 包裹              │
│    │      需要最优解搜索？→ Tree-of-Thought           │
│    │                                                │
│    └─ 否 → ReAct 文本 Action 模式                    │
│            可靠性和并行能力受限于正则解析              │
│                                                    │
└──────────────────────────────────────────────────┘
```

**2026 年生产级 Agent 的标准配置**：ReAct 做决策循环 + Function Calling 做 Action 执行 + MCP 做工具标准化 + Thinking/Reasoning 做可解释性恢复。四层叠加。[Function Calling 系统学习](../FunctionCalling系统学习/0-模块索引.md) 覆盖了第二层和第三层，ReAct 系统学习覆盖第一层——两者互补。

---

## 思考题

1. Function Calling 的 `tool_choice: "required"` 强制模型调用工具——这与 ReAct 的"让模型自己决定是否需要 Action"存在张力。在混合架构中，这个参数应该如何设置才不破坏 ReAct 的决策灵活性？
2. 文本 Action 的 ReAct 可以跨任意 LLM 移植，但格式脆弱。有没有一种介于"自由文本"和"Function Calling API"之间的中间方案——比如用 Markdown 表格格式输出 Action，兼顾可移植性和解析可靠性？
3. 2026 年有人提出"Agentic Engineering 99% 的时间在编排 Agent 而非写代码"——如果 Agent 决策框架（ReAct 等）已经标准化到了像 React 前端框架那样的程度，开发者还需要理解 ReAct 的原始论文吗？
