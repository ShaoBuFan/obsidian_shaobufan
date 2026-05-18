# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is a Chinese translation of John Ousterhout's *A Philosophy of Software Design* (2nd ed.). It is a documentation/translation project — there is no build, lint, or test pipeline.

Source: based on [yingang/aposd-zh](https://github.com/yingang/aposd-zh) (1st ed. translation), incrementally updated for the 2nd ed.

## File structure

- `README.md` — Book intro, full TOC, translation notes, and terminology table. Serves as the project index.
- `preface.md` — Author's preface
- `ch01.md` through `ch22.md` — Chapter translations (22 chapters)
- `summary.md` — Design principles summary and red flags checklist
- `figures/` — Expected directory for images (e.g., `cover.jpeg`); currently missing from the repo

## Chapter file conventions

- Start with `# 第 X 章 title` (Chinese chapter heading)
- Cross-references use relative links: `[第 2.4 节](ch02.md)`
- No YAML frontmatter (unlike the rest of the Obsidian vault)
- Paragraphs separated by blank lines

## Translation conventions

Key terminology mappings (full list in README.md):

| EN | ZH | Note |
|---|---|---|
| bug | 缺陷 / 代码缺陷 | Not 错误 (avoids confusion with error) |
| complexity | 复杂性 | Not 复杂度 |
| deep/shallow module | 深/浅模块 | Not 深层的/浅层的 |
| information leakage | 信息泄露 | Not 泄漏 |
| obvious | 易理解的 | When describing code; otherwise 明显的 |
| pass-through | 透传 | For methods, variables, parameters |
| clean | 整洁的 | Consistent with *Clean Code* translations |

## Key rules

- This is a translation project — preserve the original book's meaning, structure, and examples
- Use standard Markdown links `[text](file.md)`, consistent with the rest of the vault
- The 2nd edition adds Chapter 21 ("Decide What Matters"); Chapter 22 is the conclusion
- `figures/cover.jpeg` is referenced in README.md but the directory and file are missing
