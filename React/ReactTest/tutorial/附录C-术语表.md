---
tags:
  - tutorial
  - appendix
  - glossary
created: 2026-05-22
---

# 附录 C：术语表

| 英文 | 中文 | 说明 |
|---|---|---|
| **Arrange-Act-Assert (AAA)** | 准备-执行-断言 | 测试代码的标准三段式结构 |
| **assertion** | 断言 | `expect(value).toBe(x)` 中的判断语句 |
| **barrel export** | 桶导出 | `index.ts` 中统一 re-export 所有子模块的导出 |
| **cleanup** | 清理 | RTL 的 `cleanup()` 函数，卸载所有已渲染的组件 |
| **code coverage** | 代码覆盖率 | 测试执行过程中覆盖的代码行/分支/函数百分比 |
| **contract testing** | 契约测试 | 验证前后端接口格式一致性的测试 |
| **coverage ratcheting** | 覆盖率抬升 | 覆盖率只允许上升不允许下降的策略 |
| **custom render** | 自定义渲染 | 封装了 Provider 的 `render` 函数 |
| **end-to-end (E2E) test** | 端到端测试 | 在真实浏览器中运行完整应用的测试 |
| **fake timer** | 虚拟计时器 | `vi.useFakeTimers()` 拦截 setTimeout/setInterval，让时间可控 |
| **factory function** | 工厂函数 | 生成测试数据的函数，支持 overrides 参数 |
| **findBy\*** | 异步查询 | 返回 Promise 的查询，内置 waitFor 重试逻辑 |
| **fixture** | 测试夹具 | 预设的测试数据 |
| **flaky test** | 不稳定测试 | 时过时不过的测试 |
| **getBy\*** | 同步查询 | 元素存在则返回，不存在则抛错 |
| **globals** | 全局 API | Vitest 的 `globals: true` 使 describe/it/expect 全局可用 |
| **handler** | 请求处理器 | MSW 中定义网络行为的函数 |
| **happy path** | 快乐路径 | 一切正常的默认流程 |
| **hoisting** | 提升 | `vi.mock` 被自动提升到文件顶部执行 |
| **integration test** | 集成测试 | 测试多个模块/组件协同工作的测试 |
| **jsdom** | jsdom | 在 Node.js 中模拟浏览器 DOM 环境的库 |
| **matcher** | 匹配器 | `toBe`、`toEqual`、`toBeInTheDocument` 等断言方法 |
| **mock** | 模拟 | 用假实现替代真实现以隔离测试 |
| **mutation** | 数据变更 | 创建、更新、删除操作（REST: POST/PUT/DELETE; GraphQL: mutation） |
| **passthrough** | 放行 | MSW 中让请求穿透到真实网络 |
| **polyfill** | 垫片 | 在缺少某 API 的环境中提供该 API 的实现 |
| **queryBy\*** | 安全同步查询 | 元素存在则返回，不存在返回 null（不抛错） |
| **query priority** | 查询优先级 | RTL 的查询方法选择顺序：getByRole > getByLabelText > ... |
| **renderHook** | Hook 渲染 | RTL 提供的测试自定义 Hook 的方法 |
| **resolve.alias** | 路径别名解析 | Vitest/Vite 中 `@/` → `src/` 的路径映射 |
| **runtime override** | 运行时覆盖 | `server.use()` 在单个测试中覆盖 handler |
| **Service Worker** | Service Worker | 浏览器中拦截网络请求的后台脚本 |
| **setup file** | 全局设置文件 | 每个测试文件运行前执行的配置脚本 |
| **sharding** | 分片 | 将测试拆分到多个 CI 机器并行运行 |
| **snapshot test** | 快照测试 | 将当前输出与存储的快照文件比较 |
| **spy** | 间谍函数 | `vi.spyOn` 监听已有对象方法的调用情况 |
| **SSE** | 服务器推送事件 | Server-Sent Events，服务器向客户端单向推送数据 |
| **stub** | 桩函数 | 替换真实行为的假实现 |
| **test isolation** | 测试隔离 | 每个测试完全独立，不依赖其他测试的状态 |
| **Testing Trophy** | 测试奖杯 | Kent C. Dodds 提出的前端测试分层模型 |
| **unit test** | 单元测试 | 测试单个函数/组件/模块的最细粒度测试 |
| **userEvent** | 用户事件模拟 | 模拟完整用户交互序列的库（v14 全异步） |
| **visual regression test** | 视觉回归测试 | 通过截图对比检测 UI 视觉变化 |
| **wrapper** | 包装器 | renderHook/render 中的 Provider 包装组件 |
