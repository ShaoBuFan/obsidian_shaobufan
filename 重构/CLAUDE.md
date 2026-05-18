# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 目录用途

用户学习《软件设计的哲学》第2版（A Philosophy of Software Design, John Ousterhout）的思考笔记空间。全书 22 章，每章一个 md 文件。

## 笔记风格

- 费曼学习法、第一性原理、设计哲学**融合为连贯叙述**，不分区罗列不同"方法"
- 不使用 emoji
- 核心思想和实用 tips 使用 `>` 引用块承载
- 中文为主，每章末尾设思考题
- 闪光点.md 是全书核心洞见汇总，每条三行（根本约束 / 一句话 / 最关键洞见）

## 关键规则

- **必须搜索验证**：关键概念、作者原话、案例细节必须通过 WebSearch 搜索交叉验证，不能仅依赖模型训练数据
- 搜索关键词中英双语，优先找 GitHub 上的中文翻译版、Stanford 课程页面、以及详细的英文总结
- 搜索结果与训练数据有出入时，以搜索结果为准
- 第2版比第1版多一章（第21章 "Decide What Matters"），结论章为第22章

## Obsidian 格式规范

### 编辑器行为

vault 已开启 `strictLineBreaks: true`：**单次回车不换行**（行在阅读视图合并），**两次回车**才生成新段落。如需段内换行，用 `Shift+Enter`（插入行尾两个空格 + 回车）。写笔记得落笔空行。

### 语法约定

- **链接**：使用标准 markdown 链接 `[text](path.md)`，**禁止** wikilinks `[[...]]`（vault 已配置 `useMarkdownLinks: true`）
- **标签**：在正文中使用 `#标签名`。嵌套用 `/` 如 `#设计/深模块`。大小写不敏感，搜索父标签匹配所有子标签。不用在 frontmatter 中定义
- **引用**：核心思想和 tips 用 `>` 块引用，**不使用** callout 语法 `> [!type]`
- **分隔**：`---` 用作章节分隔。注意：文件顶部 `---` 会被解析为 YAML frontmatter 边界，笔记正文开始前不要单独写 `---`
- **高亮**：`==text==` 标注关键术语（Obsidian 扩展）
- **注释**：`%%text%%` 写编辑备注，阅读视图下隐藏，可跨行
- **任务列表**：`- [ ]` / `- [x]` 追踪待办
- **转义**：`\` 取消特殊字符格式化效果，如 `\*\*不粗\*\*`
- **不使用**：脚注（插件已关闭）、emoji、HTML 标签

## 练习代码

如果用户要求用代码演示某个设计原则，用 Python 或 TypeScript，保持示例短小聚焦。
