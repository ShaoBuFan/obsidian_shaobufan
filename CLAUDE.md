# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is an Obsidian vault for personal knowledge management. It is not a software project — there is no build, lint, or test pipeline.

## Vault structure

- `代码重构哲学/` — Two related subdirectories for John Ousterhout's *A Philosophy of Software Design* (2nd ed., 22 chapters):
  - `讲义/` — Study notes. Each chapter is a `.md` file with YAML frontmatter, tags, internal links, and `==highlights==`. Also contains `闪光点.md` (core insights distilled to 3-line entries per chapter) and `全书结构分析.canvas` (visual map). Has its own `CLAUDE.md` with detailed writing rules.
  - `课本/` — Standalone Chinese translation source text (based on [yingang/aposd-zh](https://github.com/yingang/aposd-zh)). Plain Markdown chapters (`ch01.md`–`ch22.md`) plus `preface.md` and `summary.md`.
- `React/` — Two React courses:
  - `ReactHook/` — 8-module course teaching Hook design from first principles to capstone, plus 5 appendices (exercise solutions, quick reference, Feynman checklist, design workbook, closures primer).
  - `ReactFromHook/` — 10-chapter course on react-hook-form: from first principles through real-world patterns (Zod integration, MUI/Ant Design, useFieldArray, FormProvider).
- `CS自学/` — CS self-study roadmap based on [csdiy.wiki](https://csdiy.wiki/). 12 category folders with course indices and learning paths. Current active course: UCB CS61A with progress tracking.
- `向量记忆库/` — Personal vector memory system for semantic search over notes and conversations.
  - `design/` — 8 design documents (00-08) covering architecture, chunking strategies, MCP integration, compound scoring, and three-layer design.
  - `src/` — Python implementation (from-scratch and ChromaDB versions).
  - `reference/` — Reference papers (Word2Vec, etc.).
- `小说/` — Creative writing drafts.
- `AttachmentLab/` — Obsidian attachment storage (excluded from search via Obsidian settings).
- `.obsidian/` — Obsidian configuration (JSON files).
- `WELLCOME.md` — Vault homepage/entry point.
- `参考-Obsidian语法.md` — Quick reference for Obsidian Markdown syntax used in this vault.
- `.claude/skills/obsidian-md/` — Custom `/obsidian-md` skill for enforcing vault conventions during editing.

## Note-taking conventions (`代码重构哲学/讲义/`)

When writing or editing chapter notes under `代码重构哲学/讲义/`, follow the rules in `代码重构哲学/讲义/CLAUDE.md`:

- Feynman technique, first principles, and design philosophy are **fused into one coherent narrative** — never sectioned by methodology.
- Core ideas and practical tips use `>` blockquotes.
- Written in Chinese. Each chapter ends with thought questions (思考题).
- No emoji.
- `代码重构哲学/讲义/闪光点.md` holds distilled insights: each entry is exactly three lines (fundamental constraint / one-sentence summary / most critical insight).

## Key rules for research

- **Must search to verify**: Key concepts, author quotes, and case details must be cross-checked via WebSearch. Do not rely solely on model training data.
- Use bilingual (Chinese + English) search keywords. Prefer GitHub Chinese translations, Stanford course pages, and detailed English summaries.
- When search results and training data conflict, search results take precedence.
- The 2nd edition adds Chapter 21 ("Decide What Matters"); the concluding chapter is Chapter 22.

## Obsidian Markdown syntax

This vault uses **standard Markdown with a few Obsidian extensions**. Never use wikilinks — this vault uses standard `[text](path.md)` links exclusively.

### Editor behavior: Strict Line Breaks

`strictLineBreaks: true` 已开启。编辑行为如下：

| 操作 | 结果 |
|------|------|
| 单次回车 | 行在阅读视图中合并（不是换行） |
| 行尾两个空格 + 回车 | `<br>` 真正换行 |
| 双回车（空行） | 新段落 `<p>` |

实际写作建议：段落间留空行（双回车），段内不要随意换行。`Shift+Enter` 可插入带两个空格的换行。

### Syntax in use

| 功能 | 语法 | 说明 |
|------|------|------|
| 标签 | `#标签名` | 写在正文中即可，不需要 frontmatter。tag-pane 插件已开启 |
| 引用块 | `> text` | 用于承载核心思想和实用 tips |
| 水平线 | `---` | 章节分隔。**注意：** 如果出现在文件最顶部，会被解析为 YAML frontmatter 边界 |
| 任务列表 | `- [ ]` / `- [x]` | 可用于追踪待办 |
| 高亮 | `==text==` | 标记关键词（Obsidian 扩展语法） |
| 注释 | `%%text%%` | 编辑视图可见，阅读视图隐藏。可跨行 |
| 代码块 | ` ```lang ` | 语法高亮代码块 |
| LaTeX | `$inline$` / `$$block$$` | 数学公式（KaTeX） |
| 转义 | `\*text\*` | 反斜杠取消特殊字符的格式化效果 |

### Tags in detail

- 嵌套标签用 `/`：`#设计/深模块`
- 大小写不敏感（`#TAG` = `#tag`），显示用首次输入时的大小写
- 搜索 `tag:设计` 会匹配 `#设计` 及其所有子标签（`#设计/xxx`）
- 正文中标签写在段落任意位置即可，不用跟在行首
- 标签必须包含至少一个非数字字符（`#1984` 无效，`#y1984` 有效）
- 标签内不能有空格，多词用 `#camelCase` 或 `#kebab-case`

### Frontmatter / Properties

Properties 核心插件已开启，所有笔记均使用 YAML frontmatter（至少含 `tags` 和 `created`）。格式如下：

```yaml
---
tags:
  - tag1
  - tag2
created: 2026-05-16
---
```

Obsidian properties 支持 7 种类型：**Text**、**List**（每行 `- value`）、**Number**、**Checkbox**（`true`/`false`）、**Date**（`YYYY-MM-DD`）、**DateTime**（`YYYY-MM-DDTHH:MM:SS`）、**Tags**（仅限 `tags` 属性，YAML 列表不带 `#`）。

关键规则：
- wikilinks 在 frontmatter 中必须加引号 `"[[Note]]"`
- 属性内不支持 Markdown 渲染
- 不支持的旧名（已弃用）：`tag` → `tags`、`alias` → `aliases`、`cssclass` → `cssclasses`

### Syntax deliberately not used

- **Wikilinks `[[...]]`** — 配置 `useMarkdownLinks: true`，统一用标准 markdown 链接
- **Callouts `> [!type]`** — 当前未使用，用普通 `>` 引用即可。如需使用，Obsidian 内置 14 种类型（`note` `tip` `warning` `danger` `info` `question` `success` `failure` `bug` `example` `abstract` `todo` `quote`），支持折叠（`> [!note]-`）和嵌套
- **脚注 `[^1]`** — core plugin 已关闭
- **嵌入 `![[...]]`** — 当前未使用

### Other enabled plugins (for reference)

Canvas (白板 `.canvas` 文件，支持卡片连线分组)、Backlink、Outgoing-link、Graph、Bookmarks、Outline、Slash-commands、Properties、Bases。

## 向量记忆库 project

Two implementations, two stages:

### From-scratch version (`向量记忆库/src/from_scratch.py`)

Pure Python standard library — zero dependencies. Uses TF-IDF + character n-grams as a simplified embedding for educational purposes. Runs on any machine.

```bash
# Index notes into vector memory
python3 向量记忆库/src/from_scratch.py ingest [目录]

# Semantic search
python3 向量记忆库/src/from_scratch.py search "查询内容" [top_k]
```

### Full pipeline (`向量记忆库/src/ingest_notes.py`, `search.py`)

Requires `chromadb` + `sentence-transformers`. Real embedding model (all-MiniLM-L6-v2, 384-dim). Swap-in when the hardware supports it.

```bash
pip3 install --no-cache-dir chromadb sentence-transformers
python3 向量记忆库/src/ingest_notes.py [目录]
python3 向量记忆库/src/search.py "查询内容" --top-k 5 --type note
```

### Architecture

The core pipeline is identical in both versions: read files → strip frontmatter → chunk by paragraph boundaries → embed → store → cosine similarity search. The `from_scratch.py` implementation exists so the full pipeline can be understood without heavy dependencies; only the embedding step differs (TF-IDF vs SentenceTransformer).

## Code examples

If asked to demonstrate a design principle with code, use Python or TypeScript. Keep examples short and focused.
