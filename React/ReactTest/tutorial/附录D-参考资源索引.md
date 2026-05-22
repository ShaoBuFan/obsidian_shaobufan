---
tags:
  - tutorial
  - appendix
  - resources
created: 2026-05-22
---

# 附录 D：参考资源索引

## 官方文档

| 资源 | URL | 说明 |
|---|---|---|
| Vitest | https://vitest.dev | 官方文档：配置、API、迁移指南 |
| Vitest API Reference | https://vitest.dev/api/ | vi.fn, vi.mock, expect 等完整 API |
| React Testing Library | https://testing-library.com/react | 官方文档：查询、render、userEvent |
| RTL Common Mistakes | https://kentcdodds.com/blog/common-mistakes-with-react-testing-library | Kent C. Dodds 写的常见反模式 |
| MSW | https://mswjs.io | 官方文档：handlers、HttpResponse、best practices |
| MSW Network Overrides | https://mswjs.io/docs/best-practices/network-behavior-overrides | server.use() 和运行时覆盖 |
| MSW 1.x → 2.x Migration | https://mswjs.io/docs/migrations/1.x-to-2.x | v1 → v2 迁移完整指南 |
| @testing-library/jest-dom | https://github.com/testing-library/jest-dom | toBeInTheDocument 等 DOM matchers |
| @testing-library/user-event | https://testing-library.com/user-event | userEvent v14 完整文档 |
| React Query (TanStack) | https://tanstack.com/query | useQuery/useMutation 测试最佳实践 |
| React Router | https://reactrouter.com | MemoryRouter 等测试工具 |
| React Hook Form | https://react-hook-form.com | register/handleSubmit/formState |

## GitHub 示例项目

| 项目 | URL | 亮点 |
|---|---|---|
| bulletproof-react | https://github.com/alan2207/bulletproof-react | @mswjs/data 内存数据库、renderApp 模式、数据生成器 |
| MSW Examples | https://github.com/mswjs/examples | 官方集成示例：Vitest、Jest、Playwright、Angular 等 |
| RTL+Vitest+MSW 教程 | https://github.com/arnobt78/React-Testing-Library-RTL-Vitest-TDD-MSW-API-Test-Automation-Tutorials | 5 个递进教程，从入门到 GraphQL |
| Epic React (Kent C. Dodds) | https://github.com/kentcdodds/epic-react-dev | React 测试的权威教学项目 |
| Testing React Query (TkDodo) | https://github.com/TkDodo/testing-react-query | TanStack Query 测试的专项教程 |
| MSW + React + Vite | https://github.com/rakeshongithub/msw-vite-react-example | 最小化集成示例 |
| React Mock Auth | https://github.com/mmdrn/react-mock-authentication | MSW + Jest + Cypress auth mock |

## 推荐阅读

- Kent C. Dodds, *"Testing Implementation Details"* — 为什么不该测试实现细节
- Kent C. Dodds, *"The Testing Trophy and Testing Classifications"* — 前端测试分层模型
- Kent C. Dodds, *"Fix the 'not wrapped in act(...)' warning"* — act() 警告的真正根源
- Mark Erikson, *"The State of Frontend Testing"* — 前端测试全景概述
- TkDodo, *"React Query Testing"* 系列 — React Query 测试的实践指南
- Artem Zakharchenko (kettanaito), *"Best Practices for MSW"* — MSW 作者的最佳实践

## 工具

| 工具 | 用途 |
|---|---|
| @vitest/ui | Vitest 可视化测试浏览器 |
| @vitest/coverage-v8 | 基于 V8 的快速覆盖率 |
| @mswjs/data | MSW 内存数据库 |
| @hookform/resolvers | React Hook Form + Zod 验证适配器 |
| eslint-plugin-testing-library | RTL 代码规范检查 |
| eslint-plugin-jest-dom | jest-dom 代码规范检查 |
| @ngneat/falso | 随机假数据生成 |
| vitest-axe | 无障碍测试 axe 集成 |
| msw-storybook-addon | Storybook 的 MSW 集成 |
| chromatic | 视觉回归测试平台 |

## 社区

- [MSW GitHub Discussions](https://github.com/mswjs/msw/discussions) — MSW 功能提案与问题讨论
- [Vitest GitHub Issues](https://github.com/vitest-dev/vitest/issues) — Bug 报告与功能请求
- [/r/reactjs](https://reddit.com/r/reactjs) — Reddit React 社区
- [Reactiflux Discord](https://reactiflux.com) — React 开发者 Discord 社区
