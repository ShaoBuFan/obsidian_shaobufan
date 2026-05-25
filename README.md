# obsidian_shaobufan

个人 Obsidian 知识管理仓库，专注于软件设计哲学、React 工程化和 CS 自学。

## 目录结构

| 目录 | 内容 |
|------|------|
| `代码重构哲学/` | 《软件设计的哲学》(Ousterhout) 学习笔记与中文译本 |
| `向量记忆库/` | 个人向量记忆系统（设计文档 + Python 实现） |
| `React/` | React Hook 设计与 react-hook-form 课程 |
| `CS自学/` | CS 自学路线，当前主攻 UCB CS61A |
| `小说/` | 创作草稿 |

## 向量记忆库

基于 RAG 的个人记忆系统，支持语义检索历史笔记和对话。

```bash
# 纯标准库版本（零依赖）
python3 向量记忆库/src/from_scratch.py ingest
python3 向量记忆库/src/from_scratch.py search "查询内容"

# 完整版（需要 ChromaDB + sentence-transformers）
pip3 install --no-cache-dir chromadb sentence-transformers
python3 向量记忆库/src/ingest_notes.py
python3 向量记忆库/src/search.py "查询内容"
```

详见 `向量记忆库/design/00-总览.md`。

## 笔记规范

- 标准 Markdown 链接 `[text](path.md)`，不用 wikilinks
- YAML frontmatter（tags + created）
- `==高亮==` 标记关键术语，`>` 承载核心思想
- 无 emoji
