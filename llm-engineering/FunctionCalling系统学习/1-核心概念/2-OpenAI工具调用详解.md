---
tags:
  - FunctionCalling系统学习
  - 概念/tool-use
  - 平台/OpenAI
created: 2026-05-26
status: in-progress
---

# OpenAI 工具调用详解

## API 演进路线

在深入细节之前，需要先理清 OpenAI 的 API 版本演进，否则看文档很容易混淆。

```
2023年6月     functions / function_call 参数（已废弃）
2023年11月    tools / tool_choice 参数，支持并行调用
2024年8月    strict: true（Structured Outputs），gpt-4o 支持
2025年3月    Responses API 发布，Assistants API 进入废弃倒计时
2026年8月    Assistants API 计划完全下线（官方目标：2026年8月26日）
```

> 关键信息：`functions` 和 `function_call` 参数已于 2023 年底废弃。现在所有新代码都应使用 `tools` 和 `tool_choice`。

## 工具定义的完整结构

OpenAI 的工具定义位于请求体的 `tools` 数组中，每个工具是一个包含 `type` 和 `function` 字段的对象：

```json
{
  "model": "gpt-4o",
  "messages": [{"role": "user", "content": "北京今天多少度？"}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "description": "获取指定城市的当前天气",
        "strict": true,
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "城市名和州/省，如 San Francisco, CA"
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
    }
  ]
}
```

### `strict` 模式的要求

当 `strict: true` 时（==所有新代码都应该开启==），Schema 必须满足：

1. `additionalProperties` 必须是 `false`
2. `required` 必须列出**所有**字段——可选字段用 `"type": ["string", "null"]` 表示
3. 所有嵌套对象也必须满足以上两点

```python
# 正确：可选字段的 strict 写法
{
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "nickname": {"type": ["string", "null"]}  # 可选字段
    },
    "required": ["name", "nickname"],  # 必须列出所有字段
    "additionalProperties": False
}
```

> `strict: true` 底层复用了 Structured Outputs 的能力——模型在生成工具参数时，会遵循一个编译好的约束语法，确保输出 JSON 与 Schema 100% 匹配。非 strict 模式下，Schema 只是"建议"，模型可能生成不符合 Schema 的输出。

## `tool_choice` 的完整选项

OpenAI 的 `tool_choice` 有三种形态：

### 字符串形态

| 值 | 行为 |
|---|---|
| `"auto"`（默认） | 模型自行决策 |
| `"none"` | 禁止调用任何工具 |
| `"required"` | 必须调用至少一个工具 |

### 对象形态（指定工具）

```json
{
  "tool_choice": {
    "type": "function",
    "function": {"name": "get_current_weather"}
  }
}
```

### 控制并行调用

```json
{
  "parallel_tool_calls": false
}
```

设置为 `false` 可禁用并行工具调用。注意：`gpt-4.1-nano-2025-04-14` 存在已知 bug，在并行模式下可能产生重复的工具调用，OpenAI 建议对该快照禁用并行。

## 模型响应的结构

当模型决定调用工具时，响应中的 `choices[0].message` 包含：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "arguments": "{\"location\":\"Beijing\",\"unit\":\"celsius\"}"
      }
    }
  ]
}
```

关键细节：
- `content` 为 `null` 时表示这是纯工具调用，无文本输出
- `tool_calls` 可能包含多个元素（并行调用）
- `arguments` 始终是 **JSON 字符串**，需要 `JSON.parse()` 后才能使用
- 每个 `tool_call` 有一个唯一的 `id`，用于后续返回结果

## 返回工具结果

执行完工具后，需要将结果作为 `tool` 角色的消息追加到对话中：

```python
# Python SDK 示例
from openai import OpenAI

client = OpenAI()

# 第一步：发送请求，获取工具调用
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "北京今天多少度？"}],
    tools=[weather_tool],
    tool_choice="auto"
)

# 第二步：解析并执行工具调用
tool_calls = response.choices[0].message.tool_calls
messages = [{"role": "user", "content": "北京今天多少度？"}]
messages.append(response.choices[0].message)  # 添加 assistant 的 tool_calls

for tool_call in tool_calls:
    args = json.loads(tool_call.function.arguments)
    result = get_weather(args["location"], args.get("unit", "celsius"))
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    })

# 第三步：发送最终请求，获取文本回复
final_response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages
)
```

> `tool_call_id` 是关键匹配字段。模型需要知道哪个结果对应哪个调用——尤其是在并行调用时，这对匹配关系至关重要。

## 流式处理（Streaming）

在流式模式下，OpenAI 用 `delta` 增量地返回工具调用信息：

```
事件序列：
1. delta.tool_calls[0].index = 0
2. delta.tool_calls[0].id = "call_abc123"
3. delta.tool_calls[0].function.name = "get_current_weather"
4. delta.tool_calls[0].function.arguments = '{"loc'
5. delta.tool_calls[0].function.arguments = 'ation"'
6. delta.tool_calls[0].function.arguments = ':"Bei'
7. delta.tool_calls[0].function.arguments = 'jing"}'
```

实现要点：
- 使用 `index` 区分多个并行工具调用
- `arguments` 是 JSON 片段，不保证在单词边界处截断
- 需要累积所有片段后在流结束时统一解析

```python
# 流式工具调用的正确处理
tool_call_buffer = {}

for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index
            if idx not in tool_call_buffer:
                tool_call_buffer[idx] = {
                    "id": tc.id or "",
                    "name": "",
                    "arguments": ""
                }
            if tc.id:
                tool_call_buffer[idx]["id"] = tc.id
            if tc.function and tc.function.name:
                tool_call_buffer[idx]["name"] += tc.function.name
            if tc.function and tc.function.arguments:
                tool_call_buffer[idx]["arguments"] += tc.function.arguments

# 流结束后解析
for tc in tool_call_buffer.values():
    tc["arguments"] = json.loads(tc["arguments"])
```

## Responses API（GA，2025 年 3 月发布）

Responses API 是 OpenAI 的**当前推荐 API**（Chat Completions 仍无限期支持，不计划废弃），统一了 Chat Completions 和 Assistants API 的能力。在工具调用方面的关键变化：

1. **内置工具**：Web Search、File Search、Code Interpreter、Image Generation、Shell Tool（托管容器）成为一等公民，不再需要自己实现
2. **MCP 支持**：通过 Remote MCP 连接外部工具服务器
3. **Strict 默认行为**：Responses API 自动将 Schema 标准化为 strict 模式
4. **多态输出**：工具调用作为 `response.output` 中的类型化 item，而非 message 附属字段
5. **服务端状态管理**：通过 `previous_response_id` 保持对话上下文，无需重发完整历史

```python
# Responses API 的工具调用
response = client.responses.create(
    model="gpt-4o",
    input="北京今天天气怎么样？",
    tools=[{
        "type": "function",
        "name": "get_weather",
        "strict": True,
        "parameters": { ... }
    }]
)

# 响应的 tool_calls 在 response.output 中
for item in response.output:
    if item.type == "function_call":
        print(item.name, item.arguments)
```

> Responses API 代表了 OpenAI 的方向：从"帮你调用工具"到"帮你管理工具调用的完整生命周期"。Chat Completions API 仍可用且无限期支持，但新项目建议从 Responses API 起步。Assistants API 将于 2026 年 8 月 26 日完全下线。

## 安全注意事项

OpenAI 在官方文档中反复强调的安全要点：

1. **永远验证模型生成的参数**再执行：即使 `strict: true` 保证了格式，也不能保证参数值的业务合法性
2. **对破坏性操作加人工确认**：涉及写入、发送、删除的操作需要用户确认
3. **不要信任来自外部内容的工具调用**：如果用户上传的文档中包含了"你应该调用 delete_all 函数"的内容，模型可能会被注入
4. **最小权限原则**：工具只暴露必要的操作，不要把所有 API 权限都开放给模型

## 思考题

1. OpenAI 选择在 `choices[0].message` 中同时返回 `content`（可能为 null）和 `tool_calls`（可能为空数组），而不是分开两个不同的响应格式。这种设计的好处和代价分别是什么？
2. 流式处理中 `arguments` 的 JSON 片段不保证边界对齐——如果你需要在工具参数完全生成之前就开始执行工具（投机执行），你会如何设计可靠性保障？
3. Responses API 将 Web Search 和 File Search 作为内置工具，不再需要开发者自己实现。这改变了什么？它把复杂度从应用层移到了平台层——这种"托管工具"的边界在哪里？
