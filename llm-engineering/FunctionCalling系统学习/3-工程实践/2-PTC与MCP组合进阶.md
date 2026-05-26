---
tags:
  - FunctionCalling系统学习
  - 工程实践
  - PTC
  - MCP
created: 2026-05-26
status: in-progress
---

# PTC 与 MCP 组合进阶

## 目标

将 PTC 和 MCP 组合使用，解决一个真实的多工具多数据源场景。验证组合模式相比传统逐次调用的 token 效率提升。

> 前置：完成 [实验一和实验二](1-PTC与MCP实战.md)。本实验假设你已有一个可用的 MCP Server 和 PTC 的基本理解。

---

## 场景

"分析 GitHub 上 React 和 Vue 两个仓库最近一周的活跃度，对比它们的 issue 关闭率和 contributor 数量，如果某仓库 issue 关闭率低于 50%，自动创建一个分析任务卡片。"

涉及四个操作：查询 GitHub 仓库数据（两个仓库分别查询）→ 对比分析 → 条件判断 → 创建任务卡片。如果逐次调用，需要 4-5 次往返。使用 PTC + MCP 组合，一次代码执行完成。

### 架构

```
                  ┌──────────────────────┐
                  │   Claude + PTC        │
                  │   (代码编排层)         │
                  └──────┬───────────────┘
                         │ MCP 协议
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │ GitHub   │  │ GitHub   │  │ Linear/Jira   │
   │ MCP      │  │ MCP      │  │ MCP           │
   │ (read)   │  │ (read)   │  │ (write)       │
   └──────────┘  └──────────┘  └──────────────┘
```

---

## 代码

### 步骤一：定义 MCP 工具集

```python
# mcp_tools_definition.py
# 在实际部署中，这些工具由 MCP Server 暴露，Agent 自动发现
# 这里显式定义以模拟 MCP 工具在 PTC 沙箱中可用的接口

MCP_TOOLS = {
    "github_get_repo": {
        "server": "github-mcp",
        "description": "获取 GitHub 仓库的基本信息和统计数据",
        "parameters": {"owner": "string", "repo": "string"}
    },
    "github_list_issues": {
        "server": "github-mcp",
        "description": "列出仓库的 issues，支持状态过滤",
        "parameters": {
            "owner": "string", "repo": "string",
            "state": "string", "since": "string",
            "limit": "integer"
        }
    },
    "linear_create_issue": {
        "server": "linear-mcp",
        "description": "在 Linear 中创建分析任务",
        "parameters": {"title": "string", "description": "string", "priority": "string"}
    }
}
```

### 步骤二：PTC 编排脚本（模型生成）

```python
# 以下代码由 PTC 生成，在沙箱中执行
# 实际使用时，模型会根据场景自动生成类似逻辑

import json
from datetime import datetime, timedelta

# === 沙箱提供的 MCP 调用接口 ===
# 这些函数由 PTC 运行时注入，内部通过 MCP 协议调用远程 Server

async def mcp_call(server: str, tool: str, params: dict):
    """沙箱注入函数：通过 MCP 协议调用指定 Server 的工具"""
    # 实际实现由 PTC 运行时处理
    pass

async def analyze_repo_activity():
    since = (datetime.now() - timedelta(days=7)).isoformat()

    # First batch: fetch repo data in parallel (these are independent calls)
    react_data, vue_data = await asyncio.gather(
        mcp_call("github-mcp", "get_repo", {"owner": "facebook", "repo": "react"}),
        mcp_call("github-mcp", "get_repo", {"owner": "vuejs", "repo": "vue"})
    )

    # Second batch: fetch issues for both repos in parallel
    react_issues, vue_issues = await asyncio.gather(
        mcp_call("github-mcp", "list_issues",
                 {"owner": "facebook", "repo": "react", "state": "all", "since": since, "limit": 100}),
        mcp_call("github-mcp", "list_issues",
                 {"owner": "vuejs", "repo": "vue", "state": "all", "since": since, "limit": 100})
    )

    # Analysis logic stays in code — doesn't pollute model context
    def calc_close_rate(issues):
        if not issues:
            return 0.0
        closed = sum(1 for i in issues if i.get("state") == "closed")
        return closed / len(issues)

    react_close_rate = calc_close_rate(react_issues)
    vue_close_rate = calc_close_rate(vue_issues)

    report = {
        "react": {
            "stars": react_data["stargazers_count"],
            "open_issues": react_data["open_issues_count"],
            "contributors_last_week": len(set(i.get("user", {}).get("id") for i in react_issues)),
            "issue_close_rate": f"{react_close_rate:.1%}",
            "flag": react_close_rate < 0.5
        },
        "vue": {
            "stars": vue_data["stargazers_count"],
            "open_issues": vue_data["open_issues_count"],
            "contributors_last_week": len(set(i.get("user", {}).get("id") for i in vue_issues)),
            "issue_close_rate": f"{vue_close_rate:.1%}",
            "flag": vue_close_rate < 0.5
        }
    }

    # Conditional action: create task only for flagged repos
    tasks_created = []
    for repo_name, data in report.items():
        if data["flag"]:
            task = await mcp_call("linear-mcp", "create_issue", {
                "title": f"[分析] {repo_name} issue 关闭率偏低 ({data['issue_close_rate']})",
                "description": (
                    f"{repo_name} 最近一周 issue 关闭率为 {data['issue_close_rate']}，"
                    f"低于 50% 阈值。stars: {data['stars']}，"
                    f"open issues: {data['open_issues']}，"
                    f"contributors: {data['contributors_last_week']}。"
                    f"建议排查是否有阻塞性问题。"
                ),
                "priority": "medium"
            })
            tasks_created.append({"repo": repo_name, "task_id": task.get("id")})

    # Only the report summary enters model context — not the raw issue lists
    return {
        "report": report,
        "tasks_created": tasks_created,
        "data_points_processed": len(react_issues) + len(vue_issues)
    }

# 执行并返回最终结果
result = await analyze_repo_activity()
```

### 步骤三：完整的 PTC 调用

```python
# ptc_mcp_orchestration.py
import anthropic
import json

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=(
        "你是一个 DevOps 分析助手。当需要跨多个数据源执行分析+条件操作时，"
        "生成 Python 代码在沙箱中一次性完成。可用 MCP 服务："
        "github-mcp (get_repo, list_issues)、linear-mcp (create_issue)。"
        "代码运行在沙箱中。只返回最终分析报告，不要返回原始数据。"
    ),
    messages=[{
        "role": "user",
        "content": (
            "分析 React (facebook/react) 和 Vue (vuejs/vue) 最近一周活跃度，"
            "对比 issue 关闭率和 contributor 数量。"
            "如果某仓库 issue 关闭率低于 50%，在 Linear 创建分析任务。"
        )
    }],
    tools=[
        # GitHub MCP 工具
        {
            "name": "github_get_repo",
            "input_schema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"}
                },
                "required": ["owner", "repo"],
                "additionalProperties": False
            }
        },
        {
            "name": "github_list_issues",
            "input_schema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {"type": "string", "enum": ["open", "closed", "all"]},
                    "since": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["owner", "repo"],
                "additionalProperties": False
            }
        },
        # Linear MCP 工具
        {
            "name": "linear_create_issue",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
                },
                "required": ["title", "description"],
                "additionalProperties": False
            }
        }
    ],
    # betas=["advanced-tool-use-2025-11-20"]  # PTC beta header（截止 2026 年 5 月）
)

# 解析 PTC 响应
for block in response.content:
    if block.type == "text":
        print(block.text)
```

---

## 效率对比

用一个量化表格来理解组合模式的价值：

| 维度 | 传统逐次调用 | PTC + MCP 组合 |
|------|-------------|---------------|
| API 往返次数 | 5-7 | 1 |
| 独立工具调用的并行化 | 手动管理 | `asyncio.gather` 自动并行 |
| 中间数据进入上下文 | 所有 issue 列表（可能数千 token） | 只进入代码变量（0 token） |
| 条件分支 | 模型判断 → 调用工具 → 返回 → 判断下一步 | 代码内 `if` 语句（0 延迟） |
| 错误处理 | 每步检查 → 重试逻辑由模型决策 | `try/except` 在代码中 |
| 估算 token 消耗（4 工具场景） | ~40,000+ | ~25,000 |

> 组合模式的核心价值不是"更快"——单次 API 调用时间可能类似——而是**让数据在代码中流转，而不是在上下文中累积**。上下文 = 成本，代码变量 ≠ 成本。

---

## PTC 沙箱的安全配置

组合模式引入了新的风险面——模型生成的代码需要在有工具访问权限的环境中运行。沙箱配置是最关键的安全边界：

```python
# 沙箱安全配置（概念示例，非 Anthropic 实际 API 参数）
SANDBOX_CONFIG = {
    "execution_timeout_seconds": 30,
    "max_memory_mb": 256,
    "filesystem": "read-only",
    "network": {
        "allowed_hosts": [],  # 禁止任意网络访问
        "mcp_only": True      # 只允许通过 MCP 协议调用注册的工具
    },
    "available_tools": {       # 精确指定允许的工具
        "github-mcp": ["get_repo", "list_issues"],  # 只读！
        "linear-mcp": ["create_issue"]              # 允许创建，但限制项目
    },
    "tool_rate_limit": {
        "max_calls_per_execution": 20,
        "max_write_calls_per_execution": 3
    },
    "secrets": {
        # MCP credentials 由运行时注入，代码不可见
        "injection_mode": "runtime_only"
    }
}
```

> Lab Check: [ ] 已运行 PTC + MCP 组合代码  [ ] 已验证 token 消耗量  [ ] 已验证沙箱安全配置  [ ] 已验证条件分支正确执行  [ ] 已记录关键日志

---

## 关联资源

- [实验一：PTC 基础](1-PTC与MCP实战.md#实验一ptc-多工具编排)
- [实验二：MCP Server 搭建](1-PTC与MCP实战.md#实验二搭建-mcp-server)
- [Prompt Injection 防护实战](3-Prompt-Injection防护实战.md)
- Wikipedia PTC：[Programmatic tool calling (PTC)](https://platform.claude.com/cookbook/tool-use-programmatic-tool-calling-ptc)
