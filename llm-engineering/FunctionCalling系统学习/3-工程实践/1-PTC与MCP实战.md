---
tags:
  - FunctionCalling系统学习
  - 工程实践
  - PTC
  - MCP
created: 2026-05-26
status: in-progress
---

# PTC 与 MCP 实战

## 目标

通过两个可运行的代码实验，理解 Anthropic 生态中最具差异化的两个工具调用能力：

1. **PTC（Programmatic Tool Calling）**：让模型写代码来编排多工具调用，而非逐一轮询
2. **MCP Server**：搭建一个标准化的工具服务器，让任何 MCP 兼容的 Agent 发现和调用你的工具

> 本实验使用 Python。前置依赖：`pip install anthropic mcp openai`（截止 2026 年 5 月，anthropic SDK ≥ 0.93.0，mcp SDK ≥ 1.29.0）。

---

## 实验一：PTC 多工具编排

### 背景

传统工具调用的痛点：三个工具需要三次 API 往返，每次往返都要把中间结果塞进上下文。如果中间结果很大（比如搜索结果），上下文会迅速膨胀，token 成本指数增长。

PTC 的解决方案：==模型生成 Python 代码→代码在沙箱中执行→代码内部调用工具→只有最终结果返回给模型==。往返次数从 N 次降为 1 次。

### 场景

查询"2026 年图灵奖得主的主要贡献，并与 2025 年得主做对比"。需要调用三个工具：`web_search`（两次，搜不同年份）、`web_fetch`（抓取详细页面）。

### 代码

```python
import anthropic
import json

client = anthropic.Anthropic()

# 定义工具（PTC 支持标准和 MCP 工具）
tools = [
    {
        "name": "web_search",
        "description": "搜索网页，返回结果列表",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"],
            "additionalProperties": False
        }
    },
    {
        "name": "web_fetch",
        "description": "抓取指定 URL 的完整内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "目标 URL"},
                "max_length": {"type": "integer", "description": "最大返回字符数"}
            },
            "required": ["url"],
            "additionalProperties": False
        }
    }
]

# PTC 模式使用支持代码执行的系统提示
# 模型会生成 Python 代码在沙箱中运行，代码内调用工具
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=(
        "你是一个研究助手。当需要多个搜索步骤时，使用 Python 代码一次性完成所有搜索和比较。"
        "可用函数：web_search(query) 和 web_fetch(url, max_length)。"
        "代码运行在沙箱中，只返回最终分析结果。"
    ),
    messages=[{
        "role": "user",
        "content": "2026 年图灵奖得主的主要贡献是什么？与 2025 年得主做对比。"
    }],
    tools=tools,
    # PTC 在实际 API 中需要 beta header（截止 2026 年 5 月）
    # betas=["advanced-tool-use-2025-11-20"]
)

# 处理响应：PTC 的响应中可能包含代码块或工具调用
for block in response.content:
    if block.type == "text":
        print(block.text)
    elif block.type == "tool_use":
        print(f"[工具调用] {block.name}: {json.dumps(block.input, ensure_ascii=False)}")
```

### PTC 的核心价值（用数字说话）

| 指标 | 传统 Tool Calling | PTC | 节省 |
|------|------------------|-----|------|
| API 往返次数 | N（工具数） | 1 | N-1 次 |
| Token 消耗（以 3 工具为例） | ~43,600 | ~27,300 | 37% |
| 上下文污染 | 每次中间结果都进入 | 只有最终结果进入 | 显著 |
| 适用场景 | 所有 | 工具数 > 5 或需要条件/循环 | — |

### 关键注意事项

1. ==PTC 不是免费的抽象==——它需要代码执行沙箱。在 Anthropic 托管 API 中，沙箱由平台提供。在自部署场景中，你需要自己实现安全的代码执行环境。
2. 沙箱必须限制：网络访问（只允许调用指定工具）、文件系统（只读或隔离）、执行时间（超时终止）、系统调用（最小集合）。
3. PTC 对简单单工具调用是负优化——增加了代码生成和沙箱启动的开销。

> Lab Check: [ ] 已完成 PTC 代码运行  [ ] 已验证 token 节省量  [ ] 已验证沙箱安全边界

---

## 实验二：搭建 MCP Server

### 背景

MCP（Model Context Protocol）是连接 AI Agent 与外部工具的标准化协议。写一个 MCP Server，你的工具就能被 Claude Desktop、Claude Code、VS Code、Cursor、以及任何 MCP 兼容的 Agent 发现和调用。

MCP 的核心抽象：==写一次工具服务器，处处可用==——不用为每个 Agent 平台重复实现工具逻辑。

### 架构

```
┌──────────────┐     JSON-RPC 2.0      ┌──────────────┐
│  MCP Client  │ ◄──────────────────► │  MCP Server  │
│  (Claude,    │    via STDIO or       │  (你的代码)   │
│   VS Code)   │    Streamable HTTP    │              │
└──────────────┘                       └──────┬───────┘
                                              │
                                         ┌────▼────┐
                                         │ 实际工具  │
                                         │ (DB, API)│
                                         └─────────┘
```

### 场景

搭建一个天气查询 MCP Server，提供两个工具：`get_current_weather`（当前天气）和 `get_forecast`（未来几天预报）。

### 代码：MCP Server 实现

```python
# weather_server.py
import json
import sys
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建 MCP Server 实例
server = Server("weather-server")

# 注册工具列表
@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="get_current_weather",
            description="获取指定城市的当前天气",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 Beijing"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_forecast",
            description="获取指定城市未来几天的天气预报",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "days": {
                        "type": "integer",
                        "description": "预报天数，1-7"
                    }
                },
                "required": ["city", "days"],
                "additionalProperties": False
            }
        )
    ]

# 实现工具调用处理
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_current_weather":
        city = arguments["city"]
        unit = arguments.get("unit", "celsius")
        # 实际场景中，这里调用真实的天气 API
        weather_data = _mock_weather_api(city, unit)
        return [TextContent(
            type="text",
            text=json.dumps(weather_data, ensure_ascii=False)
        )]

    elif name == "get_forecast":
        city = arguments["city"]
        days = arguments["days"]
        forecast_data = _mock_forecast_api(city, days)
        return [TextContent(
            type="text",
            text=json.dumps(forecast_data, ensure_ascii=False)
        )]

    else:
        raise ValueError(f"未知工具: {name}")

def _mock_weather_api(city: str, unit: str) -> dict:
    """模拟天气 API——实际中替换为真实 API 调用"""
    return {
        "city": city,
        "temperature": 25,
        "unit": unit,
        "condition": "晴",
        "humidity": 45,
        "wind_speed": 12
    }

def _mock_forecast_api(city: str, days: int) -> dict:
    """模拟预报 API"""
    return {
        "city": city,
        "forecasts": [
            {"date": f"2026-05-{26+i}", "high": 26+i, "low": 18+i, "condition": "晴"}
            for i in range(min(days, 7))
        ]
    }

# 启动服务器（STDIO transport）
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationCapabilities(
                sampling={},
                experimental={},
                roots={},
            ),
            NotificationOptions(),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 配置 Claude Desktop 使用 MCP Server

在 Claude Desktop 的配置文件中注册你的 server：

```json
// ~/.claude/claude_desktop_config.json (macOS)
// %APPDATA%\Claude\claude_desktop_config.json (Windows)
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/weather_server.py"]
    }
  }
}
```

重启 Claude Desktop 后，`get_current_weather` 和 `get_forecast` 会自动出现在可用工具列表中。

### 代码：MCP Client 测试

你也可以用代码测试 MCP Server，而不依赖 Claude Desktop：

```python
# test_mcp_client.py
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def test_weather_server():
    # 启动 weather server 作为子进程
    server_params = StdioServerParameters(
        command="python",
        args=["weather_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化会话
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print("可用工具:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # 调用当前天气工具
            result = await session.call_tool(
                "get_current_weather",
                arguments={"city": "Beijing", "unit": "celsius"}
            )
            print(f"\n当前天气: {result.content[0].text}")

            # 调用预报工具
            result = await session.call_tool(
                "get_forecast",
                arguments={"city": "Beijing", "days": 3}
            )
            print(f"天气预报: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(test_weather_server())
```

### MCP Server 的工程考量

1. **传输方式选择**：STDIO 适合本地工具（低延迟，无需网络配置）；Streamable HTTP 适合远程工具（可跨机器，需 OAuth 2.0 认证）。SSE transport 已于 2025 年 3 月被废弃。
2. **工具 Schema 设计**：MCP Server 的工具 Schema 被发送到不同模型（Claude、GPT、Gemini），需要考虑跨模型的 Schema 兼容性。避免使用仅某平台支持的 Schema 特性。
3. **错误处理**：工具调用失败时返回结构化的错误信息（`is_error: true` 在 Anthropic API 中，或 error content 在 MCP 中），不要只返回字符串。
4. **工具发现开销**：如果 Server 提供大量工具（>20），考虑实现 MCP Tool Search 能力——让 Agent 按需搜索工具，而非列出全部。

> Lab Check: [ ] 已完成 MCP Server 运行  [ ] 已通过 MCP Client 测试  [ ] 已在 Claude Desktop 中注册并验证  [ ] 已验证错误处理路径

---

## 实验三（进阶）：PTC + MCP 组合

PTC 和 MCP 不是竞争关系——它们可以组合使用：

```
MCP Server 提供工具 → Agent 发现工具 → PTC 编排多工具调用
```

PTC 做编排（减少往返），MCP 做工具标准化（一次编写，多处使用）。两者的结合产生了一个强大的模式：==标准化的工具生态 + 代码级的编排效率==。

```python
# 伪代码：PTC + MCP 的组合模式
# MCP Server 已经在配置中注册，Agent 自动发现工具
# 当用户请求涉及多个 MCP 工具时，PTC 自动介入编排

# 用户："对比 GitHub 上 React 和 Vue 的 star 数趋势，
#        然后检查两个仓库最近的 5 个 issue"

# PTC 生成代码（伪代码，展示逻辑）：
# results = {}
# results["react_stars"] = await mcp_call("github", "get_repo", {"repo": "facebook/react"})
# results["vue_stars"] = await mcp_call("github", "get_repo", {"repo": "vuejs/vue"})
# results["react_issues"] = await mcp_call("github", "list_issues", {"repo": "facebook/react", "limit": 5})
# results["vue_issues"] = await mcp_call("github", "list_issues", {"repo": "vuejs/vue", "limit": 5})
#
# # 分析逻辑在代码中完成，只有结果进入模型上下文
# comparison = analyze_star_trends(results["react_stars"], results["vue_stars"])
# issue_summary = summarize_issues(results["react_issues"], results["vue_issues"])
# return {"star_comparison": comparison, "issue_summary": issue_summary}
```

> 这个组合模式适合工具数量大（>10）、调用链路长（>3 步）、中间结果大的场景。对于简单的单工具查询，直接用 MCP 工具调用即可，不需要 PTC 的额外开销。

> Lab Check: [ ] 已完成 PTC + MCP 组合实验  [ ] 已记录 token 消耗对比  [ ] 已验证编排逻辑在沙箱中安全运行

---

## 关联资源

- 本系列概念笔记：[PTC 详解](../1-核心概念/3-Anthropic工具调用详解.md#1-programmatic-tool-callingptc2025-年-11-月发布)
- 本系列对比笔记：[定价与延迟分析](../2-对比分析/OpenAI与Anthropic工具调用对比.md#定价与延迟定量对比2026-年-5-月)
- MCP 官方文档：[modelcontextprotocol.io](https://modelcontextprotocol.io)
- MCP 官方 Registry：[registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io)
- Anthropic PTC Cookbook：[platform.claude.com/cookbook](https://platform.claude.com/cookbook/tool-use-programmatic-tool-calling-ptc)
