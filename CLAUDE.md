# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is an Obsidian vault for personal knowledge management. It is not a software project — there is no build, lint, or test pipeline.

## Vault structure

- `llm-engineering/` — LLM 系统工程学习项目集合。
  - `FunctionCalling系统学习/` — Function Calling / Tool Use 系统研究（OpenAI + Anthropic）。4 篇核心笔记 + 3 篇工程实践（PTC、MCP、Prompt Injection 防护）。Has its own [CLAUDE.md](llm-engineering/FunctionCalling系统学习/CLAUDE.md).
  - `RAG系统学习/` — 检索增强生成系统学习，从嵌入数学到生产工程。15 篇概念笔记 + 8 篇论文精读 + 2 篇工程笔记。Has its own [CLAUDE.md](llm-engineering/RAG系统学习/CLAUDE.md).
  - `向量记忆库/` — 个人向量记忆系统。`design/` = 8 篇架构文档 (00-08)；`src/` = Python 实现（from-scratch TF-IDF + ChromaDB pipeline）。
  - `ReAct系统学习/` — Agent 推理架构系统学习。从 ReAct (Yao et al. 2022) 到 Plan-Solve、Reflexion、Tree-of-Thought 及 2026 演进。Has its own [CLAUDE.md](llm-engineering/ReAct系统学习/CLAUDE.md).
- 整体学习路线见 [llm-engineering/00-学习路线](llm-engineering/00-学习路线.md)。
- `代码重构哲学/` — John Ousterhout's *A Philosophy of Software Design* (2nd ed., 22 chapters). `讲义/` = study notes (one `.md` per chapter, Feynman-style, Chinese); `课本/` = Chinese translation source. Has its own [CLAUDE.md](代码重构哲学/讲义/CLAUDE.md) with writing rules.
- `React/` — Two courses: `ReactHook/` (8 modules + 5 appendices) and `ReactFromHook/` (10 chapters on react-hook-form).
- `CS自学/` — CS self-study roadmap based on [csdiy.wiki](https://csdiy.wiki/). 12 category folders with course indices. Active course: UCB CS61A.
- `小说/` — Creative writing drafts.
- `AttachmentLab/` — Obsidian attachment storage (excluded from search).
- `.obsidian/` — Obsidian configuration (JSON).
- `README.md` — Vault homepage.
- `参考-Obsidian语法.md` — Quick reference for Obsidian Markdown syntax.

## Sub-CLAUDE.md files

When working in these directories, read their CLAUDE.md first:

| Directory | CLAUDE.md | Key rules |
|-----------|-----------|-----------|
| `llm-engineering/` | [link](llm-engineering/CLAUDE.md) | Shared writing rules + learning curve for all four sub-projects |
| `llm-engineering/FunctionCalling系统学习/` | [link](llm-engineering/FunctionCalling系统学习/CLAUDE.md) | Feynman + first principles fused into one narrative; Chinese; no emoji; 思考题 at chapter end |
| `llm-engineering/RAG系统学习/` | [link](llm-engineering/RAG系统学习/CLAUDE.md) | Feynman + first-principles narrative (derived from constraints, never labeled); concept notes end with 思考题; technical notes use comparison tables and ASCII diagrams |
| `llm-engineering/ReAct系统学习/` | [link](llm-engineering/ReAct系统学习/CLAUDE.md) | Feynman + first-principles; concept notes end with 思考题; paper deep-reads with arXiv ID; architecture comparison tables |
| `代码重构哲学/讲义/` | [link](代码重构哲学/讲义/CLAUDE.md) | Feynman + first principles fused into one narrative; 思考题 at chapter end; Chinese; no emoji |

## Writing rules (vault-wide)

All notes follow these conventions. For the full reference, see `参考-Obsidian语法.md`.

- **Links**: Standard `[text](path.md)` only. ==Never wikilinks `[[...]]`.==
- **Frontmatter**: Every file starts with YAML frontmatter containing at least `tags` (list, no `#` prefix) and `created` (YYYY-MM-DD). Optional: `updated`, `status`.
- **Highlights**: `==text==` for key terms.
- **Blockquotes**: `>` for core ideas and practical tips. Do not use callout syntax `> [!type]`.
- **Tags**: Written inline as `#tag` or `#parent/child`. Nested tags are hierarchical (searching `tag:设计` matches `#设计` and all `#设计/xxx`).
- **Strict line breaks**: Single Enter does not create a new line in reading view. Use blank lines (double Enter) between paragraphs.
- **Horizontal rules**: `---` for section breaks — but never at the very top of a file (collides with YAML frontmatter boundary).
- **Comments**: `%%text%%` for editor-only notes.
- **Do not use**: emoji, footnotes (`[^1]`), HTML tags, wikilinks, callouts.

## Research rules

- **Must search to verify**: Key concepts, author quotes, algorithm details, model parameters, and benchmark data must be cross-checked via WebSearch. Do not rely solely on model training data.
- Use bilingual (Chinese + English) search keywords. Prefer official docs, arXiv papers, authoritative blogs, and GitHub.
- When search results and training data conflict, search results take precedence.

## 向量记忆库 project

```bash
# Educational version (pure Python, zero dependencies)
python3 llm-engineering/向量记忆库/src/from_scratch.py ingest [目录]
python3 llm-engineering/向量记忆库/src/from_scratch.py search "查询内容" [top_k]

# Full pipeline (requires chromadb + sentence-transformers)
pip3 install --no-cache-dir chromadb sentence-transformers
python3 llm-engineering/向量记忆库/src/ingest_notes.py [目录]
python3 llm-engineering/向量记忆库/src/search.py "查询内容" --top-k 5 --type note
```

Both versions share the same pipeline: read files → strip frontmatter → chunk by paragraph boundaries → embed → store → cosine similarity search. Only the embedding step differs (TF-IDF vs SentenceTransformer).

## Custom skills

`.claude/skills/obsidian-md/` — Invoked via `/obsidian-md`. Enforces vault conventions (standard MD links, frontmatter, tags, highlights) during editing tasks.

## Code examples

When demonstrating a design principle with code, use Python or TypeScript. Keep examples short and focused.
