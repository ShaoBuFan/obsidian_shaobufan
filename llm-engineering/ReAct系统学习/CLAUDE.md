# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## 目录用途

ReAct（Reasoning + Acting）Agent 架构的系统化学习笔记。从 Yao et al. 2022 的原始论文出发，追踪 2022-2026 年间 Agent 推理架构的演进——Plan-and-Solve、Reflexion、Tree-of-Thought 以及最新的 Co-ReAct、半形式化推理和 CodeAct。

## 笔记风格

- 费曼学习法和第一性原理推导**融合为连贯叙述**，不分区罗列，不出现"第一性原理"、"费曼法"之类的标签
- 第一性原理作为**推导方法**：每篇笔记从不可再简化的根本约束出发——"如果这个架构不存在，Agent 什么行为会崩溃？"——然后沿着"为什么"的链条往上重建
- 核心思想和实用 tips 使用 `>` 引用块承载
- 不使用 emoji
- 中文为主，每篇概念笔记末尾设思考题

## 关键规则

- **必须搜索验证**：论文数据、基准测试结果、架构声明、版本时间线必须通过 WebSearch 交叉验证
- 搜索关键词中英双语，优先查找 arXiv 论文、官方 GitHub 仓库、Google Research Blog
- 搜索结果与训练数据有出入时，以搜索结果为准
- 论文引用须注明 arXiv ID 和发表年份

## 笔记分类与格式

### 概念笔记（`1-核心概念/`）

- Feynman 叙事风格：从直觉到精确
- `==高亮==` 关键术语
- `>` blockquote 承载核心洞察
- 末尾设 2-3 个思考题
- 代码示例使用 Python

### 论文精读（`1-核心概念/`）

- 结构：元数据 → 核心问题 → 方法 → 关键实验 → 优势与局限 → 对本项目的启发 → 后续工作追踪
- YAML frontmatter 加 `paper: Author_Author_Year` 字段
- 附带 PDF 存放在 `参考文档/`

### 对比分析（`2-对比分析/`）

- 使用对比表呈现差异
- 每个差异点追溯到架构设计哲学的根源
- 末尾给出场景化的选择建议

### 工程实践（`3-工程实践/`）

- 执行清单，不是纯文档
- 每篇对应一个具体的代码实现任务
- 末尾设 `Lab Check: [ ] 已完成  [ ] 已验证`

## Obsidian 格式规范

- **链接**：标准 markdown 链接 `[text](path.md)`，**禁止** wikilinks
- **标签**：顶层 `ReAct系统学习`，嵌套用 `/` 如 `概念/agent-architecture`、`论文精读`
- **frontmatter**：至少含 `tags`（YAML 列表）和 `created`（YYYY-MM-DD）
- **高亮**：`==text==`
- **分隔**：`---` 用作章节分隔（不在文件最顶部单独出现）
- **注释**：`%%text%%`
- **不使用**：脚注、emoji、HTML 标签、callout 语法
- **strictLineBreaks**：段落间留空行

## 与 FunctionCalling 系统学习的关系

ReAct 是决策框架（while 循环），Function Calling 是执行机制（循环内部的 tool_calls）。两者正交但互补。在笔记中交叉引用时应使用跨项目相对路径：`[Function Calling 系统学习](../FunctionCalling系统学习/0-模块索引.md)`。
