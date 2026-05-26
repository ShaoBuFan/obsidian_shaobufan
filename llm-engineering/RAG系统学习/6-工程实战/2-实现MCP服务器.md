---
tags:
  - RAG系统学习
  - 工程实战
  - MCP
created: 2026-05-26
updated: 2026-05-26
---

# 6.2 · 实现 MCP 服务器

向量记忆库已经有可工作的代码（索引 + 搜索）。但 Claude Code 不知道它们存在。MCP 服务器是让它知道的唯一入口——把已有的 Python 函数暴露为 Claude Code 可以调用的工具。

这个问题不能推后。复合评分、对话入库、同步触发器都依赖 MCP 服务器先存在——没有它，向量记忆库对 Claude Code 是隐形的。

## 三个工具

**search_notes** — 语义搜索笔记。输入 `query`、`top_k`（默认 5）、`source_type`（"note"/"conversation"/"all"）。输出带分数和元数据的 chunk 列表。核心逻辑：嵌入查询 → ChromaDB 查询 Top-K → 可选的复合评分重排 → 返回。

**save_to_memory** — 显式持久化。用户主动说"记住这个"时的入口。不是自动采集（那是对话入库的事）。

**sync_notes** — 触发笔记同步。扫描指定目录，对比 MD5，增量更新 ChromaDB。

## 实现关键点

MCP 服务器是独立进程，通过 stdio 和 Claude Code 通信。启动时加载嵌入模型和 ChromaDB 连接。错误处理要优雅降级——ChromaDB 不在时返回错误信息而非崩溃。个人使用场景下并发冲突概率极低（Claude Code 单线程调用）。

设计文档 [04](../../向量记忆库/design/04-MCP服务设计.md) 中有约 130 行的代码框架——可以直接基于它实现。

## 注册

实现后在项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "vector-memory": {
      "command": "python3",
      "args": ["向量记忆库/src/mcp_server.py"],
      "cwd": "/home/user/Desktop/WorkSpace"
    }
  }
}
```

## Lab Check

- [ ] 已完成 `mcp_server.py` 编写
- [ ] `search_notes("深模块")` 返回相关 chunk，分数递减
- [ ] `save_to_memory("测试", tags=["test"])` 成功写入
- [ ] `sync_notes("代码重构哲学/讲义/")` 返回增量统计
- [ ] 三个工具在 Claude Code 会话中可正常调用

---

*关联文档：[向量记忆库 · MCP 服务设计](../../向量记忆库/design/04-MCP服务设计.md) | [向量记忆库项目复盘](1-向量记忆库项目复盘.md)*
