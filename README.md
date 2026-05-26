# obsidian_shaobufan

个人 Obsidian 知识管理仓库，专注于软件设计哲学、LLM 系统工程和 CS 自学。

## 目录结构

| 目录 | 内容 |
|------|------|
| `llm-engineering/` | LLM 系统工程学习项目集合（RAG → 向量记忆库 → Function Calling → ReAct） |
| `代码重构哲学/` | 《软件设计的哲学》(Ousterhout) 学习笔记与中文译本 |
| `React/` | React Hook 设计与 react-hook-form 课程 |
| `CS自学/` | CS 自学路线，当前主攻 UCB CS61A |
| `小说/` | 创作草稿 |

详见 [llm-engineering/00-学习路线](llm-engineering/00-学习路线.md)。

## llm-engineering 项目

| 项目 | 阶段 | 说明 |
|------|------|------|
| RAG系统学习 | 一 | 检索增强生成：从嵌入数学到生产工程（15 篇概念笔记 + 8 篇论文精读） |
| 向量记忆库 | 二 | 个人向量记忆系统（8 篇设计文档 + Python 实现） |
| Function Calling 系统学习 | 三 | OpenAI + Anthropic 工具调用机制（4 篇核心笔记 + 3 篇工程实践） |
| ReAct 系统学习 | 四 | Agent 推理架构：从 Yao et al. 2022 到 2026 演进 |

### 向量记忆库

```bash
# 纯标准库版本（零依赖）
python3 llm-engineering/向量记忆库/src/from_scratch.py ingest
python3 llm-engineering/向量记忆库/src/from_scratch.py search "查询内容"

# 完整版（需要 ChromaDB + sentence-transformers）
pip3 install --no-cache-dir chromadb sentence-transformers
python3 llm-engineering/向量记忆库/src/ingest_notes.py
python3 llm-engineering/向量记忆库/src/search.py "查询内容"
```

详见 [向量记忆库/design/00-总览](llm-engineering/向量记忆库/design/00-总览.md)。

## 笔记规范

- 标准 Markdown 链接 `[text](path.md)`，不用 wikilinks
- YAML frontmatter（tags + created）
- `==高亮==` 标记关键术语，`>` 承载核心思想
- 无 emoji
