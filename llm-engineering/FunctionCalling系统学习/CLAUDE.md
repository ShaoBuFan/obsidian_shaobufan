# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## 目录用途

Function Calling / Tool Use 的系统化学习笔记。从 LLM 调用外部工具的根本动机出发，深入分析 OpenAI 和 Anthropic 两大平台的工具调用实现，覆盖 API 设计、流式处理、错误处理、工程最佳实践等完整链路。

## 笔记风格

- 费曼学习法和第一性原理推导**融合为连贯叙述**，不分区罗列，不出现"第一性原理"、"费曼法"之类的标签
- 第一性原理作为**推导方法**：每篇笔记从不可再简化的根本约束出发——"如果这个能力不存在，什么会崩溃？"——然后沿着"为什么"的链条往上重建，直到触及实践细节
- 核心思想和实用 tips 使用 `>` 引用块承载
- 不使用 emoji
- 中文为主，每篇概念笔记末尾设思考题
- 技术分析笔记可使用对比表、代码块、ASCII 架构图

## 关键规则

- **必须搜索验证**：关键概念、API 参数细节、模型能力边界、版本变更必须通过 WebSearch 交叉验证，不能仅依赖模型训练数据
- 搜索关键词中英双语，优先查找官方文档（platform.openai.com、docs.anthropic.com）、官方 SDK 源码、权威技术博客
- 搜索结果与训练数据有出入时，以搜索结果为准
- API 参数、模型名称、版本号等精确信息必须注明来源和生效日期

## 笔记分类与格式

### 概念笔记（`1-核心概念/`）

- Feynman 叙事风格：从直觉到精确
- `==高亮==` 关键术语
- `>` blockquote 承载核心洞察
- 末尾设 2-3 个思考题
- 代码示例使用 Python 或 TypeScript

### 对比分析（`2-对比分析/`）

- 使用对比表呈现差异
- 每个差异点追溯到 API 设计哲学的根源
- 末尾给出场景化的选择建议

### 工程实践（`3-工程实践/`）

- 执行清单，不是纯文档
- 每篇对应一个具体的代码实现任务
- 末尾设 `Lab Check: [ ] 已完成  [ ] 已验证`

## Obsidian 格式规范

- **链接**：标准 markdown 链接 `[text](path.md)`，**禁止** wikilinks
- **标签**：顶层 `FunctionCalling系统学习`，嵌套用 `/` 如 `概念/tool-use`、`对比分析`
- **frontmatter**：至少含 `tags`（YAML 列表）和 `created`（YYYY-MM-DD）
- **高亮**：`==text==`
- **分隔**：`---` 用作章节分隔（不在文件最顶部单独出现）
- **注释**：`%%text%%`
- **不使用**：脚注、emoji、HTML 标签、callout 语法
- **strictLineBreaks**：段落间留空行
