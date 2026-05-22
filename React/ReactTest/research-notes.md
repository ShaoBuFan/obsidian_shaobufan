---
tags:
  - research
  - testing
created: 2026-05-22
---

# 研究笔记：Vitest + RTL + MSW + React + TypeScript 技术栈

## 一、官方文档关键发现

### Vitest
- v3.2 起 `workspace` 废弃，改用 `projects`
- `setupFiles` 在每个测试文件之前于同一进程中运行
- `globals: true` 使 describe/it/expect/vi 全局可用
- 覆盖率推荐 `v8` provider，比 istanbul 更快
- `environment: 'jsdom'` 或 `happy-dom`（后者更轻量）
- `pool: 'forks'` 适合 monorepo 或分片场景
- `fileParallelism: true` 开启文件间并行
- 与 Vite 共享配置：别名、插件、CSS 处理自动对齐

### MSW v2
- `http.*` 替代 `rest.*`，`HttpResponse` 替代 `res(ctx.*)`
- `setupServer` 从 `msw/node` 导入，内部拦截 Node 的 http/https 模块
- handler 回调接收 `({ request, params, cookies })` 单一对象参数
- `server.use()` prepend 运行时 handler，优先级高于初始 handler
- `server.resetHandlers()` 移除所有运行时 handler（test isolation 关键）
- `{ once: true }` 选项让 handler 在一次匹配后自动失效
- `onUnhandledRequest: 'error'` 让未拦截的请求显式失败
- `HttpResponse.error()` 模拟网络错误（非服务器错误）
- `delay()` 从 msw 导入，可模拟加载状态
- `passthrough()` 让请求绕过 MSW 到真实网络
- v2.12.0 新增 `sse()` API 用于 Server-Sent Events
- `ws.link()` 支持原始 WebSocket 模拟
- GraphQL 订阅仍在讨论中（Discussion #2352）

### React Testing Library
- 查询优先级：getByRole > getByLabelText > getByPlaceholderText > getByText > getByDisplayValue > getByTestId
- `userEvent.setup()` 返回的实例所有方法返回 Promise，必须 await
- `findBy*` = `getBy*` + `waitFor`，内置重试逻辑
- `waitFor` 默认 timeout 1000ms，interval 50ms
- `renderHook` 已合并到 @testing-library/react（React 18+），不再需要独立包
- `cleanup()` 在 afterEach 中调用确保组件卸载
- `@testing-library/jest-dom/vitest` 直接支持 Vitest

## 二、Vitest vs Jest 对比（决定使用 Vitest 的理由）

| 维度 | Vitest | Jest |
|---|---|---|
| ESM 支持 | 原生，零配置 | 需 ts-jest/babel-jest 转译 |
| TypeScript | 通过 esbuild 原生支持 | 需额外配置 |
| Vite 集成 | 完美，共享 vite.config | 独立配置 |
| 冷启动 | ~0.3s | ~8s（约27倍） |
| Watch 模式 | 智能 HMR，仅重跑受影响测试 | 较慢 |
| 配置复杂度 | ~18行 | ~50+行 + 8-10个依赖 |
| API 兼容性 | 高度兼容 Jest（vi.fn ↔ jest.fn） | N/A |
| 迁移成本 | 低（API 映射清晰） | N/A |

## 三、社区最佳实践汇总

### 目录结构共识
```
src/
  testing/
    setup.ts           # MSW 生命周期 + cleanup
    test-utils.tsx      # 自定义 render wrapper
    data-generators.ts  # 测试数据工厂
    mocks/
      server.ts         # setupServer 实例
      browser.ts        # setupWorker 实例
      db.ts             # @mswjs/data 内存数据库
      utils.ts          # 认证、延迟等工具函数
      handlers/
        index.ts        # barrel export
        auth.ts         # 按域分组
        users.ts
```

### 核心模式
1. **default handlers = happy path, server.use() = edge cases**
2. **@mswjs/data 提供内存数据库**，让 handler 真正 CRUD 而非返回固定数据
3. **自定义 render** 封装 Router + QueryClient + 其他 Provider
4. **测试数据工厂** 使用 falso 或手写 builder
5. **MSW 处理 HTTP 层，vi.fn 处理非 HTTP 依赖**
6. **测试与源码同目录**：Component.test.tsx 紧邻 Component.tsx

### 测试奖杯策略
```
        E2E (Playwright) — 3-5 条关键流程
       Integration (Vitest + RTL + MSW) — 最大层
      Unit (Vitest, hooks/utils/stores)
     Static (TypeScript strict + ESLint)
```

## 四、克隆项目分析摘要

### bulletproof-react
- 业界公认的 React 最佳实践样板
- 使用 @mswjs/data 做内存数据库，handler 内真实 CRUD
- 认证基于 cookie + JWT 编解码
- test-utils 提供 createUser/createDiscussion/loginAsUser 等测试辅助
- renderApp 自动处理认证初始化 + 路由设置
- waitForLoadingToFinish 模式：等待所有 loading indicator 消失
- 数据生成器使用 @ngneat/falso

### MSW 官方示例 (with-vitest)
- 极简示范，展示最小可用配置
- 同时包含 node 和 jsdom 两种环境的测试
- setup 文件直接调用 server.listen/resetHandlers/close
- handlers 包含 HTTP 和 GraphQL 示例

### RTL + Vitest + MSW 教程系列 (arnobt78)
- 5 个递进教程：Boilerplate → Fundamentals → TDD → MSW → GraphQL
- 每个教程独立完整的 Vite + React + TS 项目
- MSW 教程中 server 通过 beforeAll/afterEach/afterAll 管理
- GraphQL 教程用 Apollo Client + MSW graphql handler
- 所有测试 globals: true，environment: jsdom

## 五、已知陷阱与注意事项

1. Jest + jsdom 中 TextEncoder/ReadableStream 缺失 → 使用 jest-fixed-jsdom
2. userEvent v14 异步化 → 所有操作必须 await
3. MSW handler 覆盖顺序 → 后 prepend 的优先级更高
4. server.use() 中的 handler 需显式 return，否则 fall through
5. renderHook 中不能解构 result.current → 值会过时
6. Vitest 的 vi.mock 提升到顶层 → 不能动态调用
7. 并发测试需 server.boundary() 或 --runInBand
8. worker.start() 必须 await，否则有竞态条件
9. 同一个 URL 的不同 method handler 需在同一次 use() 中覆盖
10. TypeScript strict 模式下 handler 泛型要显式标注
