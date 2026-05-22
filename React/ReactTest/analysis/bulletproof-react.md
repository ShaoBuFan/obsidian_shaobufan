---
tags:
  - analysis
  - reference-project
created: 2026-05-22
---

# bulletproof-react 测试架构分析

## 项目概览
- 仓库：alan2207/bulletproof-react
- 定位：React 项目最佳实践样板，被业界广泛引用
- 测试栈：Vitest + RTL + MSW v2 + @mswjs/data
- 分析目标：react-vite app

## vitest.config 关键设置

项目使用 Vite 的 `vite.config.ts` 统一管理（Vitest 天然复用 Vite 配置）：

```ts
// 关键配置：
// - environment: 'jsdom'
// - globals: true
// - setupFiles: ['./src/testing/setup-tests.ts']
// - 覆盖率使用 v8 provider
```

## 目录结构

```
src/testing/
  setup-tests.ts          # 全局 setup：MSW 生命周期 + ResizeObserver polyfill + DB 初始化
  test-utils.tsx           # renderApp, createUser, loginAsUser, waitForLoadingToFinish
  data-generators.ts       # createUser/createTeam/createDiscussion/createComment 工厂
  mocks/
    server.ts              # setupServer(...handlers)
    browser.ts             # setupWorker(...handlers)
    db.ts                  # @mswjs/data 内存数据库定义 + 持久化
    utils.ts               # hash, authenticate, requireAuth, networkDelay
    handlers/
      index.ts             # barrel export
      auth.ts              # register, login, logout, me
      users.ts             # CRUD
      discussions.ts       # CRUD
      comments.ts          # CRUD
      teams.ts             # CRUD
```

## MSW 初始化模式

在 `setup-tests.ts` 中统一管理：
- `beforeAll`: `server.listen({ onUnhandledRequest: 'error' })`
- `afterAll`: `server.close()`
- `beforeEach`: `initializeDb()` + `vi.mock('zustand')` + `ResizeObserver polyfill`
- `afterEach`: `server.resetHandlers()` + `resetDb()`

关键点：
- zustand 被全局 mock，因为状态管理不是大多数测试的关注点
- ResizeObserver polyfill 解决 jsdom 缺失问题
- @mswjs/data 提供完整的内存数据库，支持 where/findFirst/create 等操作
- 数据库在 beforeEach 中初始化，在 afterEach 中清除 localStorage

## vi.mock 与 MSW 互补

- **MSW**：处理所有 HTTP 层（auth, users, discussions, comments, teams）
- **vi.mock('zustand')**：全局禁用 zustand store，避免状态管理干扰 UI 测试
- **vi.stubGlobal('ResizeObserver', ...)**：polyfill 浏览器 API

项目展示了清晰的边界：网络层用 MSW，非网络依赖用 Vitest mock 工具。

## 异步处理

- `networkDelay()` 函数：测试环境固定 200ms，非测试环境随机 300-1000ms
- `waitForLoadingToFinish()`：封装 waitForElementToBeRemoved，等待所有 loading/spinner 消失
- 登录流程异步处理（createUser → loginAsUser）

## TypeScript 应用

- 所有 handler 内显式类型标注（RegisterBody, LoginBody 等）
- 数据生成器使用泛型支持 overrides：`createUser<T extends Partial<...>>(overrides?: T)`
- test-utils 提供类型安全的 renderApp 函数
- db 模型定义使用 @mswjs/data 的类型系统

## 可复用测试工具

1. **renderApp**：自动处理认证、路由、Provider 包装
2. **createUser / createDiscussion**：测试数据工厂
3. **loginAsUser**：认证辅助
4. **waitForLoadingToFinish**：等待加载完成
5. **@mswjs/data** 内存数据库：让 handler 能真正执行 CRUD

## 可改进点

1. test-utils.tsx 中大量 `any` 类型，可加强类型安全
2. 缺少 renderHook 的封装（如带 Provider 的 renderHook）
3. 测试文件使用 __tests__ 子目录而非 co-located 模式
4. data-generators 与 db 的 create 操作有职责重叠
5. 未使用 `server.use()` 做运行时覆盖的示范（缺少错误边界测试示例）
