---
tags:
  - changelog
created: 2026-05-22
---

# Changelog — 《React + TypeScript 卓越测试实战》

## 第 0 轮：大纲设计 — 2026-05-22

**产出**：`tutorial/00-大纲.md`

包含序章 + 12 章 + 4 附录的三级标题大纲，覆盖：
- 环境搭建：Vite + Vitest + RTL + MSW 完整配置
- Vitest 基础：断言、mock、定时器、覆盖率
- 组件测试：查询优先级、userEvent、反模式
- MSW：handler、server.use()、GraphQL、SSE/WebSocket
- 数据层集成：React Query、renderWithProviders、测试工厂
- Hook 测试：renderHook、异步、wrapper
- 表单/路由/状态管理：RHF+Zod、MemoryRouter、Zustand/Redux
- 可维护性：命名、组织、DRY 边界
- CI：GitHub Actions、覆盖率 ratcheting、flaky test
- Jest 迁移：API 对照、配置文件、分步策略
- 进阶：视觉回归、契约测试、Storybook+MSW、无障碍

**审核结果**：大纲覆盖所有要求主题，进入初稿。

---

## 第 1 轮：初稿 — 2026-05-22

**产出**：`tutorial/00-序章.md` 至 `tutorial/12-进阶主题.md`，共 13 个文件

**完成内容**：
- 所有章节的完整正文（约 25000+ 字中英文混合）
- 每个章节包含学习目标、核心概念、代码示例、反模式、练习与思考、本章总结
- 所有 TypeScript 代码示例附自我验证说明
- 所有 API 调用对照官方文档确认签名

**研究基础**：
- 查阅 Vitest、MSW、RTL 官方文档
- 分析 bulletproof-react、mswjs/examples、arnobt78 教程系列共 3 个项目
- 完成 20+ 篇社区文章/讨论的研究笔记
- 记录到 `research-notes.md`

**已知不足**（将在第 2 轮改进）：
- 部分章节代码示例偏少，需要更多完整例子
- 「为什么」的解释在某些地方不够充分
- Jest 对比主要体现在第十一章，应更均匀分布到各章
- 缺少 5 个以上完整的「需求→测试→实现」渐进式例子
- 附录尚未编写

---

## 第 2 轮：深度重构 — 部分完成（2026-05-22 中断）

**已完成**：
- [x] 全部 4 个附录（类型速查表、配置模板、术语表、资源索引）
- [ ] 重构至少 30% 的内容，提升解释深度
- [ ] 为每个核心原则添加「为什么」的解释
- [ ] 在第二章、第四章、第六章中增加 Jest 对比框
- [ ] 补充至少 5 个渐进式「需求→测试→实现」例子
- [ ] 统一全书的代码风格和术语

**中断点说明**：
- 附录 A/B/C/D 全部完成
- 主章节 00-12 均处于第 1 轮初稿状态
- 第 2 轮深度重构刚开始，仅完成了附录补全
- 第 3 轮严苛审查尚未开始

**继续时的优先事项**：
1. 完成第 2 轮：为第 2/4/6 章添加 Jest 对比框
2. 补充 5 个渐进式例子
3. 全文代码风格统一化
4. 第 3 轮：逐章 TypeScript 正确性检查 + 初学者可读性审查
5. 至少再克隆 1-2 个新项目审视新写法
6. 补充薄弱主题：Suspense 测试、ErrorBoundary 测试、monorepo

**已覆盖主题**：
- Environment setup (Vite + Vitest + RTL + MSW)
- Vitest fundamentals (assertions, mocks, timers, coverage)
- Component testing principles (query priority, anti-patterns)
- userEvent v14 (async API, keyboard, mouse, fake timers)
- MSW v2 (handlers, HttpResponse, server.use(), GraphQL, SSE/WebSocket)
- Integration testing (custom render, React Query, test factories)
- Hook testing (renderHook, async, wrapper, cleanup)
- Forms, routing, state management (RHF+Zod, MemoryRouter, Zustand/Redux)
- Test maintainability (naming, organization, DRY boundaries)
- CI practices (GitHub Actions, coverage ratcheting, flaky tests)
- Jest migration (API mapping, config migration, phased strategy)
- Advanced topics (visual regression, contract testing, Storybook+MSW, a11y)
- Appendices (type reference, config templates, glossary, resources)

**薄弱/待加强**：
- 并行测试优化
- monorepo 场景
- 缓存策略详解
- Lazy loading / Suspense 组件测试
- ErrorBoundary 测试
- 真实项目中的 test-utils 迭代案例
- 渐进式例子的数量不足（目前只有零散示例，缺连貫的 TDD 流程）
