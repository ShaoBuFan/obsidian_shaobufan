---
tags:
  - React
  - Redux
  - 测试/MSW
  - 分析
created: 2026-05-22
---

# vite-rtk-query 项目分析

## 1. 项目结构与用途

**定位**: 一个展示 Vite + Redux Toolkit + RTK Query + MSW 集成的最小化演示项目。来源可能是 RTK Query 官方示例或社区模板。

**技术栈**:
- React 19 + Vite 8 + TypeScript 5.9
- Redux Toolkit 2.12 / RTK Query (内置)
- React Router 7
- Tailwind CSS 4 (PostCSS)
- CSS Modules (每个 feature 自带的 `.module.css`)
- Axios (作为 RTK Query 的 HTTP client)
- MSW 2.x (浏览器 + 测试双模式)

**目录结构**:

```
vite-rtk-query/
  mocks/              # MSW mock 定义（独立于 src，与测试和开发共享）
    browser.ts        # 浏览器端 worker
    server.ts         # 测试端 node server
    handlers.ts       # 共享 handler 定义
  src/
    features/
      Counter/        # 传统 Redux slice 示例 (counterSlice + 组件)
      DocumentList/   # RTK Query 数据获取示例
    hooks/
      redux.ts        # 类型化的 useAppDispatch / useAppSelector
      useUpdateEffect.ts  # 模拟 componentDidUpdate 的自定义 hook
    services/
      docs.ts         # RTK Query createApi 定义 (自定义 axiosBaseQuery)
      types.ts        # DocsList 类型
    components/
      Spinner.tsx     # 通用加载指示器
    store.ts          # Redux store 配置
    App.tsx           # 根组件 (Provider + BrowserRouter + Routes)
    main.tsx          # 入口：开发模式先启动 MSW worker，再 render
    setupTests.ts     # 全局测试 setup (MSW server 生命周期)
  vitest.config.ts    # Vitest 配置
```

## 2. 测试配置

### vitest.config.ts

```ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/setupTests.ts'],
  },
})
```

- **environment: jsdom** — 标准的 DOM 模拟环境。
- **globals: true** — 启用全局 `describe`/`test`/`expect`/`vi`，无需手动 import。
- **setupFiles** — 指向 `src/setupTests.ts`。

### setupTests.ts（全局 setup）

```ts
import '@testing-library/jest-dom/vitest'
import { server } from '../mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => { server.close() })
```

标准的三段式 MSW 生命周期管理：
- `server.listen()` 启动 mock server，`onUnhandledRequest: 'error'` 确保所有未处理的请求都会导致测试失败（防止遗漏 mock）。
- `server.resetHandlers()` 在每次测试后重置 handler，防止跨测试泄漏。
- `server.close()` 在所有测试完成后关闭 server。

**注意**: `@testing-library/jest-dom/vitest` 是 `@testing-library/jest-dom` 的 Vitest 适配版本（v6+），直接作用于 Vitest 的 `expect`，不需要手动扩展。

### tsconfig.json 中的类型支持

```json
"types": ["vitest/globals", "@testing-library/jest-dom"]
```

两个全局类型声明均已配置，在 IDE 中可直接使用 `test`/`expect`/`vi` 和 `.toBeInTheDocument()` 等 matcher。

## 3. 测试模式分析

### 3.1 MSW 架构 — mock 与测试共享 Handler

mocks 目录独立于 src 之外，Handler 在测试和浏览器开发模式之间共享。

**handlers.ts** — 定义了一个 GET handler：

```ts
http.get('http://localhost:4000/api/docs_list', async () => {
  const data = [
    { name: 'Vite', url: 'https://vitejs.dev/' },
    // ... 共 9 个文档链接
  ]
  await sleep(3000)  // 模拟 3 秒延迟
  return HttpResponse.json(data)
})
```

关键细节：**`sleep(3000)` 模拟了 3 秒网络延迟**。测试中对应的 `waitFor` 设置了 `{ timeout: 4000 }`，恰好比延迟多 1 秒，确保了测试的可靠性。

**server.ts**（测试用）:
```ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'
export const server = setupServer(...handlers)
```

**browser.ts**（开发用）:
```ts
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'
export const worker = setupWorker(...(handlers as any[]))
```

注意 `browser.ts` 中的 `as any[]` 类型断言——这可能是因为 MSW 2.x 的类型定义在浏览器和 node 之间有差异，属于权宜之计。

### 3.2 入口文件中的 MSW 启动模式

`main.tsx` 展示了开发环境下的 MSW 集成模式：

```tsx
if (process.env.NODE_ENV === 'development') {
  import('../mocks/browser')
    .then(({ worker }) => { worker.start() })
    .then(() => root.render(<App />))
} else {
  root.render(<App />)
}
```

采用动态 `import()` 延迟加载 MSW，确保生产 bundle 不包含 mock 代码。这是一个**推荐的生产安全模式**。

### 3.3 App.test.tsx — 三种测试类型

**测试 1: 基础渲染** (`Show App Component`)
```tsx
test('Show App Component', () => {
  render(<App />)
  expect(screen.getByText('Hello Vite + Redux-Toolkit & RTK Query!')).toBeInTheDocument()
})
```
验证组件能否挂载并显示标题文本。不需要特殊的 store provider 包装——因为 `App` 组件自身包含了 `ReduxStoreProvider`，直接 render 即可。

**测试 2: Redux 交互** (`Working Counter`)
```tsx
test('Working Counter', async () => {
  const user = userEvent.setup()
  const { getByText } = render(<App />)
  expect(getByText('count is: 0')).toBeInTheDocument()
  await user.click(getByText('Increment'))
  expect(getByText('count is: 1')).toBeInTheDocument()
  await user.click(getByText('Increment'))
  expect(getByText('count is: 2')).toBeInTheDocument()
})
```
使用 `userEvent.setup()`（推荐的新 API），验证 Redux store 的初始状态和 dispatch 行为。注意这里没有对计数器做任何 mock——直接用了真实的 Redux store。

**测试 3: RTK Query 数据获取** (`working with msw`)
```tsx
test('working with msw', async () => {
  const user = userEvent.setup()
  const { getByRole } = render(<App />)
  // 点击导航链接跳转到 /doclist
  await user.click(getByRole('link'))
  // 等待 MSW mock 返回数据
  await waitFor(() => {
    expect(screen.getByText('Redux Toolkit')).toBeInTheDocument()
    expect(screen.getByText('MSW')).toBeInTheDocument()
    expect(screen.getByText('Tailwind CSS')).toBeInTheDocument()
  }, { timeout: 4000 })
})
```

这是 RTK Query 测试的关键模式：
1. 用户操作触发路由跳转（"点击链接 -> React Router 导航到 /doclist"）。
2. DocumentList 组件挂载，`useGetDocsListQuery()` 自动 dispatch 请求。
3. RTK Query 的 middleware 拦截到 query，通过 `axiosBaseQuery` 发起 HTTP GET 请求到 `http://localhost:4000/api/docs_list`。
4. MSW node server 拦截该请求，返回 mock 数据。
5. 测试使用 `waitFor` + `timeout: 4000` 等待异步数据加载完成。
6. 验证特定文档名称出现在 DOM 中。

**注意**: 测试中没有 mock `fetch` 或 `axios`，也没有 mock `useGetDocsListQuery` 的返回值——它依赖完整的 RTK Query 运行时 + MSW 网络层 mock。这是 **RTK Query 推荐的真实集成测试模式**。

### 3.4 useUpdateEffect.test.ts — Hook 测试

```tsx
test('useUpdateEffect simulates componentDidUpdate', () => {
  const effect = vi.fn()
  const { rerender } = renderHook(() => useUpdateEffect(effect))
  expect(effect).toHaveBeenCalledTimes(0)  // 首次不执行
  rerender()
  expect(effect).toHaveBeenCalledTimes(1)  // 更新后执行
  rerender()
  expect(effect).toHaveBeenCalledTimes(2)
})
```

使用 `renderHook` 单独测试自定义 hook。模式：验证首次渲染不执行 effect，后续每次 rerender 都执行。

## 4. 对教程有用的内容

### 4.1 值得借鉴的模式

| 模式 | 说明 |
|------|------|
| **MSW handler 共享** | `mocks/handlers.ts` 同时用于测试 (node) 和开发 (browser)，减少重复定义 |
| **三段式 setup** | `beforeAll listen -> afterEach reset -> afterAll close` 是 MSW 标准生命周期，可直接复用 |
| **axiosBaseQuery** | 自定义 RTK Query baseQuery 的完整实现，展示了如何处理 `BaseQueryFn` 类型和错误转换 |
| **未处理请求的错误策略** | `server.listen({ onUnhandledRequest: 'error' })` 强制要求所有请求都有 mock，防止遗漏 |
| **延迟模拟 + 超时设置** | mock handler 中 `sleep(3000)`，测试中 `waitFor` 设置 `timeout: 4000`，形成可预期的时序 |
| **userEvent.setup()** | 使用最新的 `userEvent` API（v14），非 `fireEvent` |
| **CSS Modules 测试** | 引入 `.module.css` 文件但不影响测试逻辑 |

### 4.2 项目限制

- **没有独立的测试 store 配置**：测试直接使用真实 `store.ts`（含 RTK Query middleware），没有使用 `setupStore` 工厂函数。这对于真实 HTTP 请求测试是可行的，但如果需要控制初始状态或添加自定义 middleware，建议提取出 `setupStore` 工厂。
- **没有 server-side handler 覆盖测试**：如果需要在单个测试中添加额外 handler，可以使用 `server.use()`。
- **没有 loading/error 状态的显式测试**：只测试了成功状态，没有单独测试 loading spinner 存在或错误显示。

## 5. 值得注意的唯一模式

1. **CSS Modules + Tailwind 共存**：项目同时使用了 CSS Modules（`.module.css`）和 Tailwind（Spinner 组件中的 `className`），展示了混合方案。

2. **axiosBaseQuery 工厂**：RTK Query 默认使用 `fetchBaseQuery`（基于 fetch），但该项目自定义了 `axiosBaseQuery`，返回 `{ data }` 或 `{ error }` 符合 RTK Query 的 `BaseQueryFn` 签名。这在团队已有 Axios 封装时是有用的参考。

3. **Spinner 组件中的 memo + 恒定返回值**:
   ```tsx
   const Spinner = memo(({ ... }: SpinnerProps) => { ... }, () => true)
   ```
   `() => true` 作为 `areEqual` 参数意味着组件永不重新渲染。这是**极端的性能优化**（除非 props 真的从不变化），不建议在教程中推举此模式。

4. **React Router v7 的 import 路径**: 使用 `react-router` 而非 `react-router-dom`。React Router v7 统一了包名，从此无需区分 `react-router` 和 `react-router-dom`。

5. **开发环境动态 import MSW**：`main.tsx` 中 `import('../mocks/browser')` 是动态 import，确保 mock 代码仅在开发环境被加载。这是**生产安全的 MSW 集成模式**，值得推荐。

6. **@types 目录**：项目包含 `@types/utility.d.ts`，用于放置全局类型声明。

7. **typecheck 脚本**: `tsc --noEmit` 独立于 build 做类型检查，这是 CI 中的好习惯。
