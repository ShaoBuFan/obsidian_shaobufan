# CLAUDE.md

This file provides guidance to Claude Code when working with this directory.

## 目录用途

`llm-engineering/` 是 LLM 系统工程的学习项目集合。四个子项目按学习曲线组织——从检索到工具调用到 Agent 架构。

## 项目结构与学习曲线

```
llm-engineering/
├── RAG系统学习/          ← 第一阶段：检索基础（嵌入、索引、检索、生成）
├── 向量记忆库/           ← 第二阶段：RAG 的工程实践（设计文档 + Python 实现）
├── FunctionCalling系统学习/ ← 第三阶段：工具调用机制（OpenAI + Anthropic API）
└── ReAct系统学习/        ← 第四阶段：Agent 推理架构（决策框架层）
```

逻辑线：**从"给 LLM 喂资料"（RAG）→ 到"让 LLM 调用工具"（Function Calling）→ 到"让 LLM 自主决策"（ReAct）**。

详细学习路线见 [00-学习路线](00-学习路线.md)。

## 共享写作规范

所有子项目遵循统一的 Obsidian 笔记规范。各项目的 `CLAUDE.md` 继承本文件的基础规则，仅覆盖项目特定的差异。

### 格式规范（全项目适用）

- **链接**：标准 markdown `[text](path.md)`，禁止 wikilinks `[[...]]`
- **Frontmatter**：每文件 `tags`（YAML 列表，无 `#` 前缀）+ `created`（YYYY-MM-DD）。可选 `updated`、`status`
- **高亮**：`==text==` 标注关键术语
- **引用**：`>` 承载核心思想和实用 tips，不使用 callout `> [!type]`
- **分隔**：`---` 用作章节分隔，不出现在文件最顶部
- **注释**：`%%text%%` 写编辑备注
- **标签**：`#父标签/子标签`，嵌套层级
- **行断**：strictLineBreaks，段落间留空行
- **禁止**：emoji、脚注、HTML 标签、wikilinks、callout

### 写作风格（全项目适用）

- 费曼学习法和第一性原理推导**融合为连贯叙述**，不区分"第一性原理"、"费曼法"等标签
- 第一性原理作为**推导方法**："如果 X 不存在，什么会崩溃？"→ 沿"为什么"链条重建
- 中文为主
- 概念笔记末尾设 2-3 道思考题
- 技术分析可使用对比表、代码块、ASCII 架构图
- 代码示例用 Python 或 TypeScript

### 研究规则（全项目适用）

- **必须搜索验证**：关键概念、API 参数、模型数据、版本信息必须 WebSearch 交叉验证
- 搜索中英双语关键词，优先官方文档、arXiv、权威博客
- 搜索结果与训练数据冲突时，以搜索结果为准

### 笔记分类模式（全项目适用）

| 目录 | 类型 | 特征 |
|------|------|------|
| `1-核心概念/` 或 `N-xxx/` | 概念笔记 | Feynman 叙事、思考题、`==高亮==` |
| `2-对比分析/` | 对比笔记 | 对比表、场景选择指南、分歧追溯 |
| `3-工程实践/` 或 `6-工程实战/` | 工程笔记 | 执行清单、可运行代码、`Lab Check` |
| `5-论文精读/` | 论文精读 | 核心问题→方法→实验→局限→启发 |
| `参考文档/` | 参考 | 外部资源索引、速查数据 |

## 子项目 CLAUDE.md

| 项目 | CLAUDE.md | 独有规则 |
|------|-----------|---------|
| RAG系统学习 | [CLAUDE.md](RAG系统学习/CLAUDE.md) | 模块索引结构、论文精读格式、版本号注明 |
| FunctionCalling系统学习 | [CLAUDE.md](FunctionCalling系统学习/CLAUDE.md) | API 参数精确溯源、对比分析格式 |
| ReAct系统学习 | [CLAUDE.md](ReAct系统学习/CLAUDE.md) | 论文精读格式、架构对比表 |

## 跨项目交叉引用约定

- 项目间引用使用**相对路径**：`[ReAct](../ReAct系统学习/0-模块索引.md)`
- 同一项目内使用**项目内相对路径**：`[对比分析](2-对比分析/xxx.md)`
- 参考文档统一存放在 `参考文档/` 目录下
