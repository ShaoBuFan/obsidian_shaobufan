---
tags:
  - 参考/排错
  - 工具/Vitest
  - 工具/RTL
  - 工具/MSW
created: 2026-05-22
---

# 附录B：常见错误排查

> 每个错误列出根因和修复方案。按失误率排序。

---

## B.1 "An update to Component inside a test was not wrapped in act()"

### 错误信息

```
Warning: An update to Component inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => { /* fire events that update state */ });
```

### 根因

React 检测到某个状态更新发生在了 `act()` 环境之外。RTL 的 `render()`、`userEvent`、`fireEvent`、`findBy*` 都已自动用 `act()` 包裹，但以下情况会漏掉：

1. **异步副作用未等待**——组件内的 `setTimeout`、`setInterval`、`fetch` 回调在测试结束（或断言执行完）后触发了状态更新

2. **未等待 userEvent 完成**——`user.click(el)` 没有 `await`，click 的事件处理（包括状态更新）在断言执行时尚未完成

3. **全局状态更新**——事件监听器、订阅、外部状态管理器的更新不在 React 的事件系统中

### 修复方案

```typescript
// 方案 1：等待异步操作完成
it('waits for async update', async () => {
  render(<ComponentWithAsyncData />)

  // 用 findBy* 等待异步渲染
  await screen.findByText('Data loaded')

  // 或：用 waitFor 等待条件满足
  await waitFor(() => {
    expect(screen.getByRole('status')).toHaveTextContent('Done')
  })
})

// 方案 2：清理未完成的定时器
afterEach(async () => {
  // 等待所有 pending 的 act() 完成
  await act(async () => {})

  // 如果使用了假定时器，确保恢复
  vi.useRealTimers()
})

// 方案 3：fake timers 场景
it('advances timer inside act', () => {
  vi.useFakeTimers()
  render(<ComponentWithTimer />)

  act(() => {
    vi.advanceTimersByTime(5000)
  })

  expect(screen.getByText('Timer done')).toBeInTheDocument()
  vi.useRealTimers()
})
```

### 诊断步骤

1. 看警告中提到的组件名——它是哪个组件在 `act()` 外更新了状态
2. 检查该组件是否有 `setTimeout`、`fetch`、`setInterval`、`requestAnimationFrame` 等副作用
3. 检查测试中是否缺少 `await`（如 `userEvent` 方法前没加 `await`）
4. 如果确认是测试结束后 cleanup 触发的无关更新，可以在 `afterEach` 中添加 `await act(async () => {})` 抑制——但**不推荐作为默认做法**

---

## B.2 "Unable to find role"

### 错误信息

```
TestingLibraryElementError: Unable to find an accessible element with the role "button"
and name "Submit"

Here are the accessible roles:

  heading "My Form" (name matched from content):
    <h1 />

  button "Cancel" (name matched from content):
    <button>Cancel</button>
```

### 根因

`getByRole('button', { name: 'Submit' })` 没匹配到。原因可能是：

1. **元素不具有该 ARIA role**——你可能在查 `button` 但实际元素是 `<div>` 或 `<span>`
2. **accessible name 不匹配**——按钮文本是 "Submit Form" 但你查的是 "Submit"
3. **元素不可见**——`display: none`、`visibility: hidden` 或 `aria-hidden="true"` 的元素默认被 `getByRole` 忽略
4. **元素被嵌套在不可见的容器中**——父容器不可见，子元素也不可访问

### 修复方案

```typescript
// 步骤 1：logTestingPlaygroundURL —— 可视化的 DOM 状态快照
it('debug accessible roles', () => {
  render(<MyComponent />)
  screen.logTestingPlaygroundURL()
  // 将输出的 URL 粘贴到浏览器中查看
})

// 步骤 2：debug() —— 打印 DOM 结构
it('debug DOM', () => {
  render(<MyComponent />)
  screen.debug()
  // 检查元素是否存在，以及它的文本和属性
})

// 步骤 3：检查元素的 role
// <button>Submit</button>           → role="button", name="Submit"
// <div>Submit</div>                 → 没有 role（查询不会匹配）
// <button aria-label="Submit">S</button> → role="button", name="Submit"
// <button disabled>Submit</button>  → 仍可匹配，但 checked 等属性不同

// 步骤 4：检查隐藏元素
// 默认 hidden 元素不参与匹配，需要显式指定
screen.getByRole('button', { hidden: true })

// 步骤 5：正则匹配 —— 避免空格/大小写问题
screen.getByRole('button', { name: /submit/i })
```

### 诊断技巧

```
1. 检查元素是否真的在 DOM 中：screen.debug()
2. 检查 role 是否正确：元素的隐式 role 是什么？
3. 检查 visible name：文本里有没有多余的空格？
4. 检查是否被 hidden：元素是否被 CSS 隐藏？
5. 报错信息中列出的 accessible roles 就是你的答案——从里面找
```

---

## B.3 "Unhandled request"

### 错误信息

```
[MSW] Warning: intercepted a request without a matching request handler:

  • GET /api/products

If you still wish to intercept this request, please create a request handler for it.
Read more: https://mswjs.io/docs/getting-started
```

### 根因

测试中发出了 HTTP 请求，但 MSW 没有找到匹配的 handler。原因：

1. **路径不匹配**——handler 注册的是 `/api/users`，但请求发的是 `/api/user`
2. **方法不匹配**——handler 注册的是 `http.get`，但请求是 `POST`
3. **未注册该 handler**——新加的功能，忘了添加 MSW handler
4. **handler 被 `resetHandlers()` 清除**——`afterEach` 中 `resetHandlers()` 清除了 per-test 覆盖，但如果该 handler 不在初始列表中也会丢失

### 修复方案

```typescript
// 方案 1：配置 onUnhandledRequest
// 开发时：warn（只在终端打印警告，不影响测试）
server.listen({ onUnhandledRequest: 'warn' })

// CI 时：error（未处理请求直接导致测试失败）
server.listen({ onUnhandledRequest: 'error' })

// 方案 2：排除不需要 mock 的请求（如 analytics）
server.listen({
  onUnhandledRequest(request) {
    const url = new URL(request.url)

    if (url.pathname.startsWith('/api/analytics')) {
      return // 跳过，不报错
    }

    console.warn(`Unhandled: ${request.method} ${url.pathname}`)
  },
})

// 方案 3：在测试中添加缺失的 handler
it('fetches new endpoint', async () => {
  server.use(
    http.get('/api/products', () => {
      return HttpResponse.json([{ id: 1, name: 'Widget' }])
    })
  )

  render(<ProductList />)
  expect(await screen.findByText('Widget')).toBeInTheDocument()
})

// 方案 4：用 printHandlers 列出当前活跃的 handler
it('debug handlers', () => {
  server.printHandlers()
  // 输出当前所有 handler 的路径和方法
})
```

---

## B.4 "vi.mock is not hoisted"

### 错误信息

```
[vitest] The "vi.mock" factory was not called. This likely means
that the factory function references a variable that is not defined
at the time of hoisting.

Consider using vi.hoisted() to hoist the referenced variable.
```

### 根因

`vi.mock()` 被编译阶段提升到文件顶部。如果工厂函数引用了外部变量（如 `vi.fn()` 创建的 mock 函数、数据对象），这些变量在提升后的位置**尚未初始化**，值为 `undefined`。

```typescript
// ❌ 这样写会报错
const mockFn = vi.fn()                     // 运行时执行
vi.mock('./api', () => ({                  // 编译时提升到顶部
  fetch: mockFn,                           // 此时 mockFn 是 undefined
}))
```

### 修复方案

```typescript
// ✅ 用 vi.hoisted()
const { mockFn } = vi.hoisted(() => ({
  mockFn: vi.fn(),
}))

vi.mock('./api', () => ({
  fetch: mockFn,
}))

// ✅ 多个变量
const { mockFn, mockData } = vi.hoisted(() => {
  const mockFn = vi.fn()
  const mockData = { id: 1, name: 'test' }
  return { mockFn, mockData }
})

// ✅ vi.hoisted 执行顺序
// vi.hoisted 在文件中按出现顺序执行（全部在 vi.mock 之前）
const { a } = vi.hoisted(() => ({ a: 1 }))
const { b } = vi.hoisted(() => ({ b: a + 1 }))  // ✅ 可以引用前面的 hoisted 变量
```

### 额外陷阱：vi.mock 的工厂必须返回对象

```typescript
// ❌ 工厂返回了非对象
vi.mock('./api', () => 'string')  // Error!

// ✅ 工厂必须返回模块形状的对象
vi.mock('./api', () => ({
  default: { fetch: vi.fn() },
  fetch: vi.fn(),
}))
```

---

## B.5 "toEqual vs toStrictEqual 选择错误"

### 场景 1：toEqual 通过了你不想要的匹配

```typescript
// ❌ toEqual 忽略了 undefined 属性
expect({ a: 1, b: undefined }).toEqual({ a: 1 })        // ✅ 通过
expect({ a: 1, b: undefined }).toStrictEqual({ a: 1 })  // ❌ 不通过

// ❌ toEqual 忽略了数组空洞
expect([, 1]).toEqual([undefined, 1])         // ✅ 通过
expect([, 1]).toStrictEqual([undefined, 1])   // ❌ 不通过
```

### 场景 2：toStrictEqual 检查类实例

```typescript
class User {
  constructor(public name: string) {}
}

expect(new User('Alice')).toEqual({ name: 'Alice' })            // ✅ 通过（忽略原型链）
expect(new User('Alice')).toStrictEqual({ name: 'Alice' })      // ❌ 不通过（原型链不同）
```

### 选择原则

| 场景 | 用哪个 |
|------|--------|
| 基本类型（string, number, boolean） | `toBe` |
| 对象字面量（普通 {} ） | `toEqual` 或 `toStrictEqual` |
| 对象可能有 undefined 属性 | `toEqual` |
| 严格对象结构匹配 | `toStrictEqual` |
| 类实例比较 | `toEqual`（除非你关心原型） |
| API 响应验证 | `toStrictEqual`（更安全） |

---

## B.6 "Fake timers + async" 超时陷阱

### 问题

```typescript
vi.useFakeTimers()

it('test async with fake timers', async () => {
  const fn = vi.fn()

  // Component 内部有 async 操作
  render(<AsyncComponent onDone={fn} />)

  vi.advanceTimersByTime(5000)

  // ❌ fn 没有被调用！
  // 原因：async 操作内部的 Promise 还没有 resolve
  expect(fn).toHaveBeenCalled()
})
```

### 根因

假定时器替换了 `setTimeout` 和 `setInterval`，但 `Promise` 没有被替换（且不应该被替换）。当下面的序列发生时：

1. `async` 函数启动 → 创建 Promise
2. `setTimeout` 被 `advanceTimersByTime` 触发 → 调用了 `resolve()` 
3. `resolve()` 将微任务（microtask）放入队列
4. **假定时器没有执行微任务队列**

结果是：计时器到了，回调执行了，但 Promise 的 `.then()` 回调还没有跑。

### 修复方案

```typescript
// 方案 1：使用 async 版推进方法
await vi.advanceTimersByTimeAsync(5000)

// 方案 2：手动 flush Promise
vi.advanceTimersByTime(5000)
await vi.waitFor(() => {
  // waitFor 内部做了微任务 flush
  expect(fn).toHaveBeenCalled()
})

// 方案 3：用 real timers 测试含 async 操作的场景
vi.useRealTimers()
it('test async without fake timers', async () => {
  render(<AsyncComponent />)
  await screen.findByText('Done')
})

// 方案 4：只在需要同步控制定时器的地方用 fake timers
it('debounce with async', async () => {
  vi.useFakeTimers()
  const fn = vi.fn()
  const debounced = debounce(fn, 300)

  debounced()
  await vi.advanceTimersByTimeAsync(300)

  expect(fn).toHaveBeenCalledTimes(1)
  vi.useRealTimers()
})
```

---

## B.7 环境错误

### "document is not defined"

```
ReferenceError: document is not defined
```

**根因**：`environment` 设置为 `'node'`（默认值），但测试中使用了 DOM API。

**修复**：

```typescript
// vitest.config.ts
test: {
  environment: 'jsdom',  // 或 'happy-dom'
}

// 或按文件覆盖
// @vitest-environment jsdom
// 放在测试文件顶部注释
```

### "describe is not defined"

```
ReferenceError: describe is not defined
```

**根因**：`globals: false`（默认值）但测试中直接使用 `describe`、`it`、`expect` 而未显式 import。

**修复**：

```typescript
// 方案 A：开启 globals
// vitest.config.ts
test: { globals: true }

// 方案 B：显式导入
import { describe, it, expect } from 'vitest'
```

### "Property 'toBeInTheDocument' does not exist"

```
TS2339: Property 'toBeInTheDocument' does not exist on type 'Assertion<HTMLElement>'.
```

**根因**：未导入 `@testing-library/jest-dom` 的 Vitest 类型扩展。

**修复**：

```typescript
// 在 setup 文件中添加
import '@testing-library/jest-dom/vitest'

// 或单独的 .d.ts 文件
// src/test/vitest.d.ts
/// <reference types="@testing-library/jest-dom/vitest" />
```

### "Cannot use import statement outside a module"

```
SyntaxError: Cannot use import statement outside a module
```

**根因**：某个依赖是 ESM 格式，但 Vitest 没有正确处理它。常见于 CJS + ESM 混合的项目。

**修复**：

```typescript
// vitest.config.ts
test: {
  deps: {
    interopDefault: true,
    inline: ['problematic-package'], // 需要内联处理的包
  },
}
```

### "The module factory of `vi.mock()` is not allowed to reference any out-of-scope variables"

```
Error: The module factory of `vi.mock()` is not allowed to reference any out-of-scope variables.
```

**根因**：`vi.mock()` 工厂引用了未在 `vi.hoisted()` 中定义的变量。

**修复**：

```typescript
// 把所有外部引用放到 vi.hoisted() 中
const { myVar } = vi.hoisted(() => ({ myVar: 'value' }))
vi.mock('./mod', () => ({ export: myVar }))
```

### 环境错误快速排查表

| 错误 | 可能原因 | 检查方向 |
|------|---------|---------|
| `document is not defined` | environment 不是 jsdom | `vitest.config.ts` 的 `environment` 字段 |
| `describe is not defined` | globals 未开启且未 import | `globals: true` 或添加显式 import |
| `toBeInTheDocument` 类型错误 | jest-dom 类型未扩展 | 检查 setup 文件和 `tsconfig.json` 中的 `types` 配置 |
| import 语法错误 | CJS/ESM 混合问题 | 配置 `deps.interopDefault` 或 `deps.inline` |
| `vi.mock` 工厂变量错误 | 外部变量未 hoist | 改用 `vi.hoisted()` |
| `act()` 警告 | 异步状态更新未捕获 | 检查未 await 的 userEvent 和未清理的定时器 |
| 测试超时 | 异步操作未正确 mock 或 await | 检查 MSW handler 匹配、异步操作是否 mock |

---

## B.8 其他常见问题

### "Can't perform a React state update on an unmounted component"

```
Warning: Can't perform a React state update on an unmounted component.
This is a no-op, but it indicates a memory leak in your application.
```

**根因**：组件卸载后，某个异步回调（fetch 的 `.then`、setTimeout 的回调）尝试更新状态。

**修复**：

```typescript
// 方案 1：在 afterEach 中清理所有未完成的请求
afterEach(async () => {
  await act(async () => {})
})

// 方案 2：组件内检查是否已卸载（但这是修症状而非根因）
useEffect(() => {
  let cancelled = false
  fetch('/api/data').then((data) => {
    if (!cancelled) setData(data)
  })
  return () => { cancelled = true }
}, [])

// 方案 3：在测试中等待所有副作用完成
it('properly cleans up', async () => {
  const { unmount } = render(<Component />)
  await screen.findByText('Loaded')
  unmount()
  // 卸载后不应再有状态更新警告
})
```

### "Received value must be a mock or spy function"

```
Error: Received value must be a mock or spy function.
```

**根因**：对非 mock 函数调用了 `toHaveBeenCalled()` 等 mock 相关断言。

**修复**：

```typescript
// ❌ 错误
const fn = () => {}
expect(fn).toHaveBeenCalled()  // Error!

// ✅ 正确
const fn = vi.fn()
expect(fn).toHaveBeenCalled()
```

### "TestingLibraryElementError: Found multiple elements with the role"

```
Found multiple elements with the role "button"
```

**根因**：使用了 `getByRole`（期望单元素），但匹配了多个元素。

**修复**：

```typescript
// 方案 1：使用 name 选项缩小范围
screen.getByRole('button', { name: /submit/i })

// 方案 2：使用 getAllByRole
const buttons = screen.getAllByRole('button')

// 方案 3：使用 within 限定上下文
const dialog = screen.getByRole('dialog')
within(dialog).getByRole('button', { name: /confirm/i })
```

---

## B.9 "fetch is not a function"

### 错误信息

```
TypeError: fetch is not a function
```

### 根因

MSW 依赖 `fetch` API 拦截请求，但当前环境没有提供全局 `fetch`。常见场景：

1. **Node.js 版本低于 18**——Node 18+ 才内置 `fetch`（基于 undici）
2. **测试文件使用 `@vitest-environment node`**——Node 环境没有 fetch（即使 Node 18+ 也需要手动启用）
3. **错误地导入了 MSW browser 包**——`msw/browser` 的 `setupWorker` 在 Node 环境中运行时找不到 fetch
4. **jsdom 环境下 fetch 被 mock 或 polyfill 覆盖**——某些 polyfill 可能意外移除全局 fetch

### 修复方案

```typescript
// 方案 1：升级到 Node 18+（推荐）
// Node 18+ 内置 fetch，vitest 默认使用

// 方案 2：vitest.config.ts 中启用 jsdom 环境
// vitest.config.ts
test: {
  environment: 'jsdom',        // jsdom 提供 fetch polyfill
}

// 方案 3：手动 polyfill（Node < 18）
// vitest.setup.ts 或测试文件顶部
import { fetch, Headers, Request, Response } from 'undici'
Object.assign(globalThis, { fetch, Headers, Request, Response })

// 方案 4：确认导入的是正确的 MSW 入口
// ✅ Node 测试环境
import { setupServer } from 'msw/node'
// ❌ 不要在 Node 环境中使用这个
// import { setupWorker } from 'msw/browser'
```

### 诊断步骤

1. 确认 Node 版本：`node --version`（需要 ≥ 18）
2. 检查测试文件的 `@vitest-environment` 注释
3. 检查 MSW 的 import 路径——是 `msw/node` 还是 `msw/browser`
4. 在测试中写入 `console.log(typeof fetch)` 确认 fetch 是否存在

---

## B.10 "Cannot find module 'msw/node'"

### 错误信息

```
Error: Cannot find module 'msw/node'
Require stack:
- /path/to/test/file.test.ts
```

### 根因

MSW v2 将 Node 和 Browser 的入口分离为独立的子路径。`msw/node` 是 Node 环境的入口——它需要安装 `msw` 的 Node 特定依赖（如 `@mswjs/interceptors`）。常见原因：

1. **MSW 版本不对**——MSW v1.x 没有 `msw/node` 子路径，统一用 `msw` 入口
2. **安装了 browser-only 版本的 msw**——某些 CDN/registry 上的 msw 可能不包含 Node 支持
3. **TypeScript 路径映射（paths）未配置**——`tsconfig.json` 的 `paths` 重写了模块解析
4. **包管理器安装不完整**——`npm install msw --save-dev` 后 `@mswjs/interceptors` 等依赖未正确下载

### 修复方案

```typescript
// 方案 1：升级到 MSW v2
npm install msw@latest --save-dev

// 方案 2：确认使用正确的 import 路径
// ✅ MSW v2 — Node 环境
import { setupServer } from 'msw/node'

// ✅ MSW v2 — 浏览器环境
import { setupWorker } from 'msw/browser'

// ✅ MSW v1（旧版本）
import { setupServer } from 'msw'  // v1 统一入口

// 方案 3：检查 tsconfig.json 的 paths 是否冲突
// ❌ 如果配置了以下 paths，会导致模块解析错误
{
  "paths": {
    "msw/*": ["node_modules/msw/*"]  // 可能引起冲突
  }
}

// ✅ 确保 paths 配置不覆盖 msw 的子路径
{
  "paths": {
    "@/*": ["src/*"]  // 只映射项目内部路径
  }
}

// 方案 4：重新安装依赖
npm install msw@latest --save-dev  // 确保所有 peerDependencies 正确安装
```

### 诊断步骤

1. 检查 `package.json` 中的 MSW 版本：`npm ls msw`
2. 确认 import 路径是否匹配 MSW 版本：
   - MSW v1: `import { setupServer } from 'msw'`
   - MSW v2: `import { setupServer } from 'msw/node'`
3. 检查 `tsconfig.json` 中是否有覆盖 msw 路径的 `paths` 或 `baseUrl` 配置
4. 尝试直接运行 `node -e "require('msw/node')"` 验证模块是否可以加载

## 关联章节
- [第2章：测试环境搭建](02-测试环境搭建.md) — 环境配置与 setup 文件体系（B.7 环境错误）
- [第3章：Vitest 基础](03-Vitest基础.md) — 断言 Matcher、vi.mock 体系、定时器（B.4/B.5/B.6）
- [第4章：查询的艺术](04-查询的艺术.md) — getByRole 语义查询与调试（B.2）
- [第5章：用户事件模拟](05-用户事件模拟.md) — userEvent 异步交互（B.1 act 警告）
- [第6章：MSW 哲学与实践](06-MSW哲学与实践.md) — MSW handler 与 server 生命周期（B.3/B.9/B.10）
