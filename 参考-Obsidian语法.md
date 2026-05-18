---
tags:
  - 参考
  - Obsidian
created: 2026-05-17
---
# Obsidian Markdown 语法参考

> 此文件可用作 Claude Code 在此 vault 中编辑时的语法速查。每次编辑笔记前调用 `Read` 此文件即可刷新规则。

## 当前 vault 配置

| 配置 | 值 | 影响 |
|------|-----|------|
| `useMarkdownLinks` | `true` | **禁止** `[[wikilinks]]`，统一 `[text](path.md)` |
| `strictLineBreaks` | `true` | 单回车不换行，双回车分段 |
| `defaultViewMode` | `preview` | 默认阅读视图 |
| `newLinkFormat` | `relative` | 相对路径链接 |
| `attachmentFolderPath` | `./AttachmentLab` | 附件存储位置 |

## 编辑行为（Strict Line Breaks）

| 输入 | 效果 |
|------|------|
| 单次回车 | 行在阅读视图合并（不是换行） |
| 行尾两个空格 + 回车 | `<br>` 真正换行 |
| 双回车（空行） | 新段落 `<p>` |

**规则**：段落间留空行。段内不随意换行。`Shift+Enter` = 带两个空格的换行。

## 语法速查

### 本 vault 使用的

| 元素 | 语法 | 示例 |
|------|------|------|
| 标题 | `#` ~ `######` | `## 二级标题` |
| 粗体 | `**text**` | `**重要概念**` |
| 斜体 | `*text*` | `*emphasis*` |
| 高亮 | `==text==` | `==关键术语==` |
| 行内代码 | `` `code` `` | `` `map()` `` |
| 代码块 | ` ```lang ` | ` ```python ` |
| 引用块 | `> text` | `> 核心思想` |
| 水平线 | `---` | 章节分隔（**文件顶部会被解析为 YAML 边界**） |
| 无序列表 | `- item` | |
| 有序列表 | `1. item` | |
| 任务列表 | `- [ ]` / `- [x]` | `- [ ] 待办` |
| 标签 | `#tag` 在正文中 | `#设计/深模块` |
| 链接 | `[text](path.md)` | `[第4章](第4章-深模块.md)` |
| 图片 | `![alt](path)` | |
| 注释 | `%%text%%` | 编辑可见，阅读隐藏 |
| 转义 | `\*text\*` | 取消格式化 |
| LaTeX | `$inline$` / `$$block$$` | `$E=mc^2$` |
| Frontmatter | 文件顶部 `---` 包裹 YAML | 见下方 |

### 本 vault 不使用的

| 元素 | 原因 |
|------|------|
| `[[wikilinks]]` | `useMarkdownLinks: true` |
| `![[embed]]` | 未使用 |
| `> [!callout]` | 用普通 `>` 引用，14 种类型备查但不主动用 |
| `[^footnotes]` | 核心插件已关闭 |
| Emoji | 不含 `:shortcode:` |

## Frontmatter / Properties

支持 7 种类型：**Text**、**List**（`- value`）、**Number**、**Checkbox**（`true`/`false`）、**Date**（`YYYY-MM-DD`）、**DateTime**（`YYYY-MM-DDTHH:MM:SS`）、**Tags**（仅限 `tags` 属性，YAML 列表不带 `#`）。

```yaml
---
tags:
  - book/软件设计的哲学
  - 概念/深模块
status: 进行中
created: 2026-05-17
---
```

**规则**：
- wikilinks 在 frontmatter 中必须加引号 `"[[Note]]"`
- 属性内不支持 Markdown 渲染
- 弃用旧名：`tag` → `tags`、`alias` → `aliases`、`cssclass` → `cssclasses`

## 标签详细规则

- 嵌套：`#设计/深模块` — 父标签搜索匹配所有子标签
- 大小写不敏感（显示用首次输入的大小写）
- 至少包含一个非数字字符（`#1984` 无效，`#y1984` 有效）
- 标签内无空格，多词用 `#camelCase` 或 `#kebab-case`
- 正文中标签写在段落任意位置，不须跟在行首

## 本 vault 的核心插件

Canvas（白板 `.canvas`）、Backlink、Outgoing-link、Graph、Bookmarks、Outline、Slash-commands、Properties、Bases、Tag-pane。

## 编辑清单

- [ ] 用标准 MD 链接，不用 wikilinks
- [ ] Frontmatter 放在文件最顶部，后面空一行
- [ ] 段落间留空行
- [ ] 关键术语用 `==高亮==`
- [ ] 标签写在正文中（不用在 frontmatter 里重复定义，除非是 tags 属性）
- [ ] 文件顶部 `---` 会被解析为 YAML 边界——不要在那里放水平分隔线
