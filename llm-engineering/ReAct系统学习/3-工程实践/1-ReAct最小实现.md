---
tags:
  - ReAct系统学习
  - 工程实践
  - agent-architecture
created: 2026-05-26
status: in-progress
---

# ReAct 最小实现

## 目标

从零构建一个 ReAct Agent，不使用 LangChain 等框架。理解每一步的工程决策——为什么这样设计循环终止条件、为什么这样管理消息历史、为什么这样处理错误。

> 这个实现可以对接 OpenAI 的 Function Calling（推荐）或纯文本解析模式（用于不支持 tool calling 的模型）。完成后你将拥有一个 ~100 行的 Agent 核心，可以扩展为任何实际应用。

---

## 版本一：基础 ReAct + Function Calling

```python
# react_agent_v1.py
# 依赖: pip install openai
import json
from openai import OpenAI

client = OpenAI()

class ReactAgent:
    """
    最小的 ReAct Agent：Thought → Action → Observation 循环。
    Action 使用 Function Calling 执行，Observation 由工具返回。
    """

    def __init__(self, tools: list[dict], max_turns: int = 10):
        self.tools = tools
        self.max_turns = max_turns

    def run(self, user_query: str) -> str:
        messages = [{
            "role": "system",
            "content": (
                "You are a helpful assistant with access to tools. "
                "For each step, think about what you need to do, "
                "then call the appropriate tool. "
                "When you have enough information, answer directly."
            )
        }, {
            "role": "user",
            "content": user_query
        }]

        for turn in range(self.max_turns):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            msg = response.choices[0].message

            # 没有工具调用 → 模型认为信息足够，返回最终答案
            if not msg.tool_calls:
                return msg.content

            # 有工具调用 → 执行并追加结果
            messages.append(msg)  # assistant 的 tool_calls
            for tc in msg.tool_calls:
                result = self._execute_tool(
                    tc.function.name,
                    json.loads(tc.function.arguments)
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        return "Agent reached maximum turns without final answer."

    def _execute_tool(self, name: str, args: dict) -> dict:
        """实际工具执行——替换为你的工具实现"""
        raise NotImplementedError("Override this method with your tools")


# 使用示例
def weather_search(location: str) -> dict:
    """模拟天气查询工具"""
    return {"location": location, "temperature": 22, "condition": "sunny"}

class WeatherAgent(ReactAgent):
    def _execute_tool(self, name: str, args: dict) -> dict:
        if name == "get_weather":
            return weather_search(args["location"])
        return {"error": f"Unknown tool: {name}"}

# 运行
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名"}
            },
            "required": ["location"],
            "additionalProperties": False
        }
    }
}]

agent = WeatherAgent(tools=tools, max_turns=5)
answer = agent.run("北京和上海今天哪个更暖和？")
print(answer)
```

### 关键设计决策

1. **循环终止条件**：`msg.tool_calls` 为空时终止。这意味着模型**自己决定**什么时候信息足够了。备选终止条件包括：达到最大轮数（防止无限循环）、用户自定义的 `stop` 标记。

2. **消息追加策略**：assistant 的 tool_calls 和 tool 结果按顺序追加到 `messages` 数组。这意味着上下文随每轮线性增长——第 5 轮时前 4 轮的 Thought（隐式）+ Action + Observation + 结果都在上下文中。==工具结果的大小是上下文增长的主要驱动因素==。

3. **tool_choice 设置**：使用 `"auto"` 而非 `"required"`，让模型自己判断是否需要工具。如果用 `"required"`，闲聊场景（用户说"你好"）也会被强制调用工具。

---

## 版本二：带显式 Thought 的 ReAct

版本一使用 Function Calling，Thought 是隐式的——模型在生成 `tool_calls` 之前可能在内部"思考"，但这对开发者不可见。如果需要可解释性和调试，可以强制模型先输出 Thought 再调用工具。

```python
# react_agent_v2.py —— 带显式 Thought
class ReactAgentV2(ReactAgent):
    """在 prompt 中强制模型先 Think 再 Act"""

    def run(self, user_query: str) -> str:
        messages = [{
            "role": "system",
            "content": (
                "You follow a strict Think → Act → Observe cycle.\n\n"
                "RULES:\n"
                "1. ALWAYS start with 'Thought:' to reason about what to do next.\n"
                "2. If you need information, call a tool.\n"
                "3. After receiving a tool result, start your next response "
                "with 'Observation:' summarizing what you learned, then "
                "'Thought:' for your next step.\n"
                "4. When you have the final answer, respond without calling any tools.\n\n"
                "NEVER skip the Thought step."
            )
        }, {
            "role": "user",
            "content": user_query
        }]

        for turn in range(self.max_turns):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content

            # 记录 Thought（如果有文本内容的话）
            if msg.content:
                print(f"[TURN {turn + 1}] {msg.content}")

            messages.append(msg)
            for tc in msg.tool_calls:
                print(f"  → Action: {tc.function.name}({tc.function.arguments})")
                result = self._execute_tool(
                    tc.function.name,
                    json.loads(tc.function.arguments)
                )
                print(f"  ← Observation: {json.dumps(result, ensure_ascii=False)[:80]}...")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        return "Max turns reached."
```

> 显式 Thought 的代价是多消耗 token——模型每步都先生成一段文本再调用工具。但换来了完整的可审计轨迹。对于调试 Agent 行为、排查"为什么调用了错误工具"这类问题，显式 Thought 的价值远超它的 token 成本。

---

## 版本三：文本 Action 模式（纯 ReAct，无 Function Calling）

当模型不支持 Function Calling 时（开源模型、教学场景），回退到 ReAct 的原始文本解析模式：

```python
# react_agent_v3.py —— 文本 Action 模式
import re

class TextReActAgent:
    """纯文本 ReAct，不依赖 Function Calling API。适用任意 LLM。"""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.tools = {}  # name → callable
        self.action_pattern = re.compile(r"Action:\s*(\w+)\[(.*)\]")

    def register_tool(self, name: str, fn):
        self.tools[name] = fn

    def _parse_action(self, text: str):
        """从文本中解析 Action——最脆弱但最灵活的部分"""
        match = self.action_pattern.search(text)
        if not match:
            return None, None
        return match.group(1), match.group(2)

    def _build_prompt(self, history: list[dict]) -> str:
        """构建 ReAct prompt——包含示例轨迹"""
        examples = """
Example:
Question: What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
Thought 1: I need to search Colorado orogeny, find the eastern sector, then find the elevation range.
Action 1: Search[Colorado orogeny]
Observation 1: The Colorado orogeny was an episode of mountain building in Colorado and surrounding areas.
Thought 2: It doesn't mention the eastern sector. Let me look up "eastern sector".
Action 2: Lookup[eastern sector]
Observation 2: The eastern sector extends into the High Plains.
Thought 3: The eastern sector extends into the High Plains. I need the elevation range of High Plains.
Action 3: Search[High Plains elevation range]
Observation 3: High Plains refers to ... rises from 1,800 to 7,000 ft.
Thought 4: 1,800 to 7,000 ft. I can answer now.
Action 4: Finish[1,800 to 7,000 ft]

Now your turn. Follow the exact same format.
"""
        prompt = examples + "\n"
        for h in history:
            prompt += f"{h['role']}: {h['content']}\n"
        return prompt

    def run(self, user_query: str) -> str:
        history = [{"role": "Question", "content": user_query}]

        for turn in range(self.max_turns):
            prompt = self._build_prompt(history)
            response = self._call_llm(prompt)  # 可以是任意 LLM
            history.append({"role": "Assistant", "content": response})

            tool_name, tool_args = self._parse_action(response)
            if tool_name is None:
                return response  # 无法解析 → 当作最终答案
            if tool_name == "Finish":
                return tool_args  # 显式的 Finish Action

            # 执行工具
            if tool_name in self.tools:
                result = self.tools[tool_name](tool_args)
                history.append({"role": "Observation", "content": str(result)})
            else:
                history.append({
                    "role": "Observation",
                    "content": f"Error: Tool '{tool_name}' not found."
                })

        return "Max turns reached."

    def _call_llm(self, prompt: str) -> str:
        """替换为实际 LLM 调用"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
```

> 文本 Action 模式的核心脆弱性在 `_parse_action()` 里——一个正则表达式决定了整个 Agent 的可靠性。在 2026 年，生产环境几乎不使用这种模式，但它的教育价值在于让你看清 ReAct 循环的本质：**prompt 构建 → LLM 调用 → 文本解析 → 工具执行 → 追加 Observation → 重复**。理解了这五个步骤，就理解了所有 Agent 框架的底层循环。

---

## 工程要点总结

| 决策点 | 推荐做法 | 为什么 |
|--------|---------|--------|
| 行动执行 | Function Calling（有 API 支持时） | 100% 格式可靠，并行调用 |
| Thought 可见性 | 生产→根据可解释性需求；调试→始终可见 | 可解释性 vs token 成本的权衡 |
| 循环终止 | 模型自主判断 + `max_turns` 硬限制 | 两者都要——模型可能陷入循环 |
| 工具结果大小 | 设置截断上限（如 5000 字符） | 防止上下文爆炸 |
| 错误处理 | 工具失败时返回结构化错误 + `is_error`（Anthropic） | 错误信息也是 Observation |
| 上下文管理 | 超过一定轮数后做摘要或滑动窗口 | 第 20 轮的 Thought 不应该包括第 1 轮的全部原始数据 |

> Lab Check: [ ] 已完成版本一（基础 ReAct + Function Calling）  [ ] 已完成版本二（带显式 Thought）  [ ] 已完成版本三（文本 Action 模式）  [ ] 已验证循环终止逻辑  [ ] 已验证错误处理路径  [ ] 已验证多工具并行调用
