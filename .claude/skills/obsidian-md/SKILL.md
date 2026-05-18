---
name: obsidian-md
description: 在当前 Obsidian vault 中执行编辑任务。自动遵循 vault 的语法约定（标准 MD 链接、frontmatter、标签、高亮等）。
argument-hint: "[编辑要求]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch
---

你正在一个 Obsidian vault 中工作。用户通过 `/obsidian-md` 提出了编辑任务。你的工作是执行 `$ARGUMENTS` 中描述的任务，同时严格遵守以下 vault 约定。

## 不可违反的规则

1. **链接**：只用标准 `[text](path.md)`，禁止 `[[wikilinks]]`（vault 配置 `useMarkdownLinks: true`）
2. **换行**：`strictLineBreaks: true` — 单回车不换行，双回车才分段。段内不随意换行
3. **Emoji**：不使用
4. **文件顶部 `---`**：只用于 YAML frontmatter，不用于水平分隔线
5. **Callout**：不用 `> [!type]`，用普通 `>` 引用
6. **脚注**：核心插件已关闭，不用

## 编辑时遵循的约定

- **Frontmatter**：新建文件必须加，至少含 `tags` 和 `created`。用 YAML 格式，支持 7 种类型：Text、List（`- value`）、Number、Checkbox（`true`/`false`）、Date（`YYYY-MM-DD`）、DateTime（`YYYY-MM-DDTHH:MM:SS`）、Tags（仅限 `tags` 属性，列表不带 `#`）
- **高亮**：关键术语首次出现时用 `==高亮==`
- **标签**：在正文中写 `#标签名`，嵌套用 `/`（如 `#设计/深模块`）。标签内无空格、至少一个非数字字符
- **链接**：交叉引用用相对路径 `[显示文字](文件名.md)`
- **注释**：编辑备注用 `%%text%%`（阅读视图隐藏）

## 任务执行

用户任务：$ARGUMENTS

1. 理解用户的需求，确定要操作的文件
2. Read 文件后执行编辑
3. 用 Edit 工具精确修改
4. 如果用户要求"新建"，用 Write 创建文件，顶部写 frontmatter，正文用 `# 标题` 开始
5. 完成后自检：无 wikilinks、frontmatter 格式正确、段落间有空行、无 emoji

## 常见场景

- **新建笔记**：建文件 → frontmatter → `# 标题` → 内容 → `==高亮==` 关键术语
- **加 frontmatter**：在文件最顶部插入 `---` 包裹的 YAML
- **加标签**：在正文合适位置加 `#标签`，或在 frontmatter 的 `tags` 列表中追加
- **加链接**：用 `[文字](目标文件.md)`，目标文件必须存在（先 Glob 确认）
- **格式检查**：读文件，对照规则列出违规项并修复
