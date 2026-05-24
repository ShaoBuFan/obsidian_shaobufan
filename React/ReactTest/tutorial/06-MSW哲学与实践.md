---
tags:
  - 测试/MSW
  - 工具/MSW
  - 工具/Vitest
created: 2026-05-22
---

# 第6章：MSW 哲学与实践

## 学习目标

- 理解网络层 mock 相比模块级 mock 的根本优势
- 掌握 MSW 架构模型：Handler → Server → 请求拦截 三层
- 熟练使用 `http.get/post/put/patch/delete` 定义 handler，包括 TypeScript 泛型参数
- 掌握 `HttpResponse` 的所有响应构造方法
- 理解 `server.listen`/`close`/`resetHandlers`/`use`/`restoreHandlers` 的生命周期语义
- 掌握 per-test handler 覆盖模式和各种网络策略
- 了解 MSW v1 → v2 迁移的核心变化

---

## 6.1 为什么要做网络层 Mock

### 模块级 mock 的脆弱性

在引入 MSW 之前，最常见的网络请求 mock 方式是使用 `vi.mock` 直接替换 HTTP 客户端模块：

```typescript
// 方案 A：模块级 mock
import { vi } from 'vitest'

vi.mock('../api/user', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
}))
```

这个模式有三个隐藏问题：

**问题 1：与实现耦合**

```typescript
// 你 mock 了 fetchUser，但组件可能改用了 getUser
vi.mock('../api/user', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: 1 }),
}))

// 如果某天重构把 fetchUser 改名为 getUser，mock 也要改
// 更糟糕的是：如果忘记改 mock，测试仍然通过（因为 mock 创建了一个不存在的导出）
```

**问题 2：跳过真实请求流程**

```typescript
// 模块级 mock 跳过了 fetch 调用、URL 拼接、header 设置、响应解析……
import { vi } from 'vitest'

vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({ data: { id: 1 } }),
    // 你的 apiClient.get 内部可能：
    // 1. 拼接 URL：baseURL + path
    // 2. 设置 Authorization header
    // 3. 处理 401 自动刷新 token
    // 4. 解析响应格式
    // 所有这些逻辑都被跳过了
  },
}))
```

**问题 3：更换 HTTP 库测试全灭**

```typescript
// 从 fetch 切换到 axios，所有模块级 mock 都需要重写
// 因为 vi.mock 针对的是具体模块的导出接口
```

### MSW 的网络层拦截

MSW 在**协议层**进行拦截，与组件使用的 HTTP 库无关：

```typescript
// 方案 B：网络层拦截（MSW）
import { http, HttpResponse } from 'msw'

server.use(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({ id: Number(params.id), name: 'Alice' })
  })
)
```

无论组件内部用 `fetch`、`axios`、`ky` 还是 `react-query`，只要最终发 HTTP 请求，MSW 就能拦截。测试覆盖了从组件调用 → HTTP 请求 → 网络传输 → 响应解析的完整链路。

> **为什么：** MSW 的网络层拦截在架构上优于模块级 mock，根本原因在于**关注点分离**。模块级 mock（`vi.mock`）将"模拟网络响应"和"替换模块导出"两个语义耦合在一起——你 mock 的不是"这个请求返回什么"，而是"这个模块的函数调用返回什么"。当你重构代码时（比如从 `fetch` 切换到 `axios`，或者将 API 调用从 `api.getUser` 重命名为 `api.fetchUser`），模块级 mock 的语义就断裂了。MSW 的 handler 定义在**网络协议层**，与你的代码如何发出请求完全无关——"对 `/api/user` 的 GET 请求返回 200 和 JSON 体"这个描述不会因为你的代码结构变化而失效。这也是 MSW 团队将 handler 称为 "service layer" 而非 "mock layer" 的原因——它们描述的是服务端的行为，而非客户端代码的行为。
>
> 更深层的原因是**测试的保真度（fidelity）**。模块级 mock 跳过了 URL 拼接、header 设置、响应解析、错误处理等完整流程，只 mock 了函数调用结果。但真实用户的操作路径经过的是完整的网络请求链路——URL 拼错一个斜杠、header 名大小写不一致、JSON 解析失败，这些 bug 在模块级 mock 的测试中全部无法发现。MSW 拦截真实请求意味着你的测试覆盖了与生产环境一致的请求路径，只有网络传输本身被替代。Martin Fowler 在谈论测试替身时强调：测试替身的抽象层次越高，测试的保真度越低（[TestDouble](https://martinfowler.com/bliki/TestDouble.html)）。MSW 在协议层工作，是你能达到的最高保真度的测试替身。

> **Jest 对比：模块 mock 在 Jest 和 Vitest 中的行为差异**
>
> 如果你从 Jest 迁移，`vi.mock` 与 `jest.mock` 的核心行为一致——它们都使用自动提升（hoisting）机制将 mock 声明移动到文件顶部。但有一个实践上的区别：**Jest 的 `jest.mock` 只能在文件顶层调用**（尽管 hoisting 让它看起来可以放在 import 之前），而 **Vitest 的 `vi.mock` 允许在 `beforeAll`/`beforeEach` 中调用**，这使得按测试动态 mock 成为可能。
>
> 更重要的区别在 mock 清理策略上：
> - Jest: `jest.resetAllMocks()` 重置所有 mock 的实现为 `undefined`
> - Vitest: `vi.clearAllMocks()` / `vi.resetAllMocks()` 对应相同的语义
>
> 但无论 Jest 还是 Vitest，**模块级 mock 的架构局限是相同的**——它们都绑定到具体的模块导出。这也是为什么跨框架迁移时，MSW 的 handler 可以原封不动地复用，而模块级 mock 往往需要重写。
>
> ```typescript
> // Jest 写法
> jest.mock('../api/user', () => ({ fetchUser: jest.fn() }))
>
> // Vitest 写法（基本相同）
> vi.mock('../api/user', () => ({ fetchUser: vi.fn() }))
>
> // MSW 写法（两框架完全一致，无需改动）
> http.get('/api/user', () => HttpResponse.json({ id: 1 }))
> ```

### MSW 的核心洞察

MSW 的创造者 Artem Zakharchenko 的核心洞察是：**Service Worker API 是浏览器原生网络拦截标准**。MSW 在浏览器端利用 Service Worker 拦截真实请求，在 Node.js 测试环境利用 `http` 模块的拦截能力模拟同样的行为。两者共用同一套 handler。这意味着：

- 开发环境（浏览器）：用 `setupWorker` + Service Worker → 真实拦截
- 测试环境（Node）：用 `setupServer` + 请求拦截 → 同一套 handler

```typescript
// src/mocks/handlers.ts — 一套 handlers，两种环境
export const handlers = [
  http.get('/api/users', () => HttpResponse.json([{ id: 1, name: 'Alice' }])),
  http.post('/api/users', async ({ request }) => {
    const user = await request.json()
    return HttpResponse.json({ id: 2, ...user }, { status: 201 })
  }),
]
```

```typescript
// src/mocks/server.ts — Node 测试环境
import { setupServer } from 'msw/node'
import { handlers } from './handlers'
export const server = setupServer(...handlers)
```

```typescript
// src/mocks/browser.ts — 浏览器开发环境
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'
export const worker = setupWorker(...handlers)
```

> **自我验证说明**：`setupWorker` 使用 Service Worker API（浏览器原生），`setupServer` 使用 Node.js 的 `http` 模块拦截（通过 `node-request-interceptor`）。两者在 handler 定义层面完全兼容——同一组 handlers 可以同时用于测试和开发环境。参考 [MSW 文档 - 核心概念](https://mswjs.io/docs/concepts/)。

### 渐进式示例：从 no mock 到 MSW

用一个相同的测试场景，逐步展示三种 mock 策略的差异。场景：测试 `UserProfile` 组件显示用户名称。

**阶段 1：无 mock（依赖真实服务端）**

```typescript
// 依赖真实 API 服务
// 问题：测试脆弱、依赖外部环境、运行慢
it('displays user name (with real API)', async () => {
  // 假设有一个真实的 API 正在运行
  render(<UserProfile userId={1} />)
  expect(await screen.findByText('Alice')).toBeInTheDocument()
  // 如果服务端返回的不是 Alice，测试失败
  // 如果服务端宕机，测试失败
  // 如果网络延迟，测试很慢
})
```

**阶段 2：模块级 mock（vi.mock）**

```typescript
// 替换具体的 API 函数
vi.mock('../api/user', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
}))

it('displays user name (with vi.mock)', async () => {
  render(<UserProfile userId={1} />)
  expect(await screen.findByText('Alice')).toBeInTheDocument()
})
// 改善了可靠性和速度，但引入了耦合问题
// 如果组件内部改用了组件自己的状态管理方案而非 api.getUser？
// 如果 fetchUser 的导入路径变了？
// 如果底层从 fetch 换成了 axios？
```

**阶段 3：网络层 mock（MSW）**

```typescript
// 在协议层拦截，与组件实现无关
it('displays user name (with MSW)', async () => {
  server.use(
    http.get('/api/users/:id', () => {
      return HttpResponse.json({ id: 1, name: 'Alice' })
    }),
  )

  render(<UserProfile userId={1} />)
  expect(await screen.findByText('Alice')).toBeInTheDocument()
})
// 不依赖具体模块、覆盖完整请求链路、handler 可跨测试和跨环境复用
```

> **这个渐进式示例揭示了一个核心洞察**：mock 的抽象层次决定了测试的保真度。`vi.mock` 在函数调用层工作（保真度最低），MSW 在网络协议层工作（保真度最高）。层次越高，测试对重构的容忍度越好，测试覆盖的代码路径越完整。

---

## 6.2 MSW 架构模型

### 三层模型

```
─────────────────────────────────────────
  Layer 1: Handler 定义
   ─ 描述"什么请求该返回什么响应"
   ─ http.get('/api/users', resolver)
─────────────────────────────────────────
  Layer 2: Server 实例
   ─ 管理 handlers 的注册、覆盖、清理
   ─ 提供 listen/close/resetHandlers/use 等生命周期
─────────────────────────────────────────
  Layer 3: 请求拦截器
   ─ 捕获实际发出的 HTTP 请求
   ─ 在 Node 中拦截 http.request / fetch
   ─ 在浏览器中通过 Service Worker 拦截
─────────────────────────────────────────
```

### 三层模型的运行时行为

实际运行时，handler 的优先级形成更精细的三层结构：

```
Layer 1: Runtime handlers（server.use() 追加）
  └→ 测试运行时动态添加，优先级最高
  └→ 在初始 handlers 之前匹配
  └→ afterEach 中 resetHandlers() 清除

Layer 2: Initial handlers（setupServer(...handlers) 注册）
  └→ 全局默认 handler，所有测试共享
  └→ resetHandlers() 恢复到这里

Layer 3: Real network（未被 MSW 拦截的请求）
  └→ onUnhandledRequest 策略控制行为
  └→ 测试中几乎不会真正发出——bypass 策略除外
```

**LIFO 匹配顺序**：`server.use()` 追加的 handler 插入到列表头部。匹配从头开始遍历，找到第一个匹配的 handler 就执行。这意味着**后 use() 的先匹配**。如果两个 handler 匹配同一个请求路径，最后注册的那个生效。

```typescript
server.use(
  http.get('/api/user', () => HttpResponse.json({ name: 'First' }))
)
server.use(
  http.get('/api/user', () => HttpResponse.json({ name: 'Second' }))
)
// 请求 /api/user → 返回 { name: 'Second' }
```

> **为什么要有三层结构？** 这种设计复用了一个经典的模式——**中间件架构**。Express.js 的中间件栈、Redux 的 middleware、甚至 Node.js 的 `http` 模块本身都使用类似的分层结构。每层只关注自己的职责：初始 handlers 提供全局默认值，runtime handlers 覆盖特定测试场景，真实网络是兜底。这种分层让测试既不需要为每个测试重新注册所有 handler（通过初始 handlers），又能灵活覆盖特定场景（通过 runtime handlers）。

### 请求匹配流程

MSW 收到请求后按以下顺序匹配 handler：

```
收到请求：GET /api/users/42?page=1
  │
  ├→ 1. 按注册顺序遍历 handlers（后注册的优先）
  │
  ├→ 2. 匹配方法：http.get → GET 请求 ✓（如果是 http.post 则跳过）
  │
  ├→ 3. 匹配路径模式：/api/users/:id
  │     → /api/users/42 匹配 ✓
  │     → params: { id: '42' }
  │
  ├→ 4. （可选）在 resolver 中检查 search params、headers、body
  │
  ├→ 5. 匹配 → 执行 resolver，返回响应
  │
  └→ 6. 都不匹配 → onUnhandledRequest 策略处理
```

### setupServer 完整签名

```typescript
import { setupServer } from 'msw/node'

// 签名
function setupServer(...handlers: HttpHandler[]): SetupServerApi

// SetupServerApi 接口
interface SetupServerApi {
  listen(options?: ServerListenOptions): void
  close(): void
  resetHandlers(...nextHandlers: HttpHandler[]): void
  use(...handlers: HttpHandler[]): void
  restoreHandlers(): void         // v2 新增
  listHandlers(): readonly HttpHandler[]
  printHandlers(): void
}
```

> **自我验证说明**：`setupServer` 是 MSW v2 中 Node 环境的唯一入口。它接受展开的 handler 数组。与 v1 相比，v2 新增了 `restoreHandlers()` 和 `listHandlers()` 方法。参考 [MSW 文档 - setupServer](https://mswjs.io/docs/api/setup-server/)。

---

## 6.3 Handler 定义

### 完整 TypeScript 签名

```typescript
import { http, HttpResponse } from 'msw'

// ─── 每一方法的泛型签名 ───

http.get<Params extends Record<string, string> = Record<string, string>>(
  path: string | RegExp,
  resolver: ResponseResolver<Params>,
): HttpHandler

http.post<Params = {}>(
  path: string | RegExp,
  resolver: ResponseResolver<Params>,
): HttpHandler

http.put<Params = {}>(
  path: string | RegExp,
  resolver: ResponseResolver<Params>,
): HttpHandler

http.patch<Params = {}>(
  path: string | RegExp,
  resolver: ResponseResolver<Params>,
): HttpHandler

http.delete<Params = {}>(
  path: string | RegExp,
  resolver: ResponseResolver<Params>,
): HttpHandler

// head / options 也支持
http.head(path, resolver)
http.options(path, resolver)
```

### ResponseResolver 签名

```typescript
type ResponseResolver<Params extends Record<string, string>> = (
  args: ResolverArgs<Params>,
) => HttpResponse | Promise<HttpResponse>

interface ResolverArgs<Params> {
  request: Request               // 原生 fetch Request 对象
  params: Params                 // 路径参数，如 { id: '42' }
  cookies: Record<string, string>
  requestId: string              // v2 新增，每个请求唯一 UUID
}
```

> **自我验证说明**：v2 中的 `request` 是**原生 Fetch API 的 Request 对象**，而非 MSW 封装的请求对象。这意味着 `request.body` 不可直接读取——必须使用 `await request.json()` 或 `await request.text()`。这是 v1 → v2 最重要的变化之一。

### 基础 Handler 示例

```typescript
import { http, HttpResponse } from 'msw'

const handlers = [
  // GET — 获取用户列表
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice', email: 'alice@test.com' },
      { id: 2, name: 'Bob', email: 'bob@test.com' },
    ])
  }),

  // GET — 动态路径参数
  http.get<{ id: string }>('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: Number(params.id),
      name: 'Alice',
      email: 'alice@test.com',
    })
  }),

  // POST — 创建资源
  http.post('/api/users', async ({ request }) => {
    const body = await request.json() as { name: string; email: string }

    return HttpResponse.json(
      { id: Date.now(), ...body },
      { status: 201 }
    )
  }),

  // PUT — 更新资源
  http.put<{ id: string }>('/api/users/:id', async ({ request, params }) => {
    const body = await request.json()
    return HttpResponse.json({ id: Number(params.id), ...body })
  }),

  // DELETE — 删除资源
  http.delete<{ id: string }>('/api/users/:id', ({ params }) => {
    return new HttpResponse(null, { status: 204 })
  }),
]
```

### 条件响应：基于请求参数返回不同数据

```typescript
http.get('/api/search', ({ request }) => {
  const url = new URL(request.url)
  const query = url.searchParams.get('q')
  const page = Number(url.searchParams.get('page')) || 1

  if (!query) {
    return HttpResponse.json(
      { error: 'Query parameter is required' },
      { status: 400 }
    )
  }

  // 基于分页返回不同数据
  const results = query === 'react'
    ? page === 1
      ? [{ id: 1, title: 'React Guide' }]
      : [{ id: 2, title: 'React Advanced' }]
    : []

  return HttpResponse.json({ results, page, totalPages: 2 })
})
```

### Header 验证

```typescript
http.get('/api/protected', ({ request }) => {
  const auth = request.headers.get('Authorization')

  if (!auth) {
    return new HttpResponse(null, { status: 401 })
  }

  if (!auth.startsWith('Bearer ')) {
    return HttpResponse.json(
      { error: 'Invalid token format' },
      { status: 403 }
    )
  }

  return HttpResponse.json({ data: 'secret' })
})
```

> **自我验证说明**：`request.headers.get('Authorization')` 是原生 Headers API。注意 header 名是大小写不敏感的（`get('authorization')` 也能匹配）。参考 [Fetch API - Headers](https://developer.mozilla.org/en-US/docs/Web/API/Headers)。

---

## 6.4 响应策略

### HttpResponse 静态方法

```typescript
import { HttpResponse } from 'msw'

// ─── HttpResponse.json() ───
// JSON 响应（自动设置 Content-Type: application/json）
HttpResponse.json(
  body?: BodyType | null,
  init?: ResponseInit,
): HttpResponse

// ─── HttpResponse.text() ───
// 纯文本响应（Content-Type: text/plain）
HttpResponse.text(
  body?: string | null,
  init?: ResponseInit,
): HttpResponse

// ─── HttpResponse.xml() ───
// XML 响应（Content-Type: application/xml）
HttpResponse.xml(
  body?: XMLBodyType | null,
  init?: ResponseInit,
): HttpResponse

// ─── HttpResponse.arrayBuffer() ───
// 二进制响应
HttpResponse.arrayBuffer(
  body?: ArrayBuffer | null,
  init?: ResponseInit,
): HttpResponse

// ─── HttpResponse.error() ───
// 网络错误模拟（非 HTTP 响应，是传输级错误）
HttpResponse.error(): HttpResponse

// ─── HttpResponse.passthrough() ───
// 放行请求到真实网络
HttpResponse.passthrough(): HttpResponse
```

### ResponseInit

```typescript
interface ResponseInit {
  status?: number        // 默认 200
  statusText?: string    // 默认 'OK'
  headers?: HeadersInit  // Record<string, string> 或 Headers 实例
}
```

### 状态码策略速查

```typescript
// 200 — 成功（get 列表/详情）
HttpResponse.json({ id: 1, name: 'Alice' }, { status: 200 })

// 201 — 创建成功（post 后）
HttpResponse.json({ id: 2, name: 'Bob' }, { status: 201 })

// 204 — 无内容（delete 成功或 put 成功）
new HttpResponse(null, { status: 204 })

// 400 — 参数错误
HttpResponse.json({ error: 'Email is required' }, { status: 400 })

// 401 — 未认证
new HttpResponse(null, { status: 401 })

// 403 — 无权限
HttpResponse.json({ error: 'Insufficient permissions' }, { status: 403 })

// 404 — 资源不存在
HttpResponse.json({ error: 'User not found' }, { status: 404 })

// 500 — 服务端错误
HttpResponse.json({ error: 'Internal server error' }, { status: 500 })

// 网络错误（不是 HTTP 响应！客户端收到 TypeError）
HttpResponse.error()

// 302 重定向
new HttpResponse(null, {
  status: 302,
  headers: { Location: '/new-location' },
})
```

> **自我验证说明**：`HttpResponse.error()` 与 5xx 状态码有本质区别。5xx 仍然是 HTTP 响应——`fetch` 的 Promise 会 resolve，只是 `response.ok` 为 false。而 `HttpResponse.error()` 导致 `fetch` 的 Promise reject，抛出 `TypeError: Failed to fetch`。测试中一定要区分这两种场景。参考 [MSW 文档 - network error](https://mswjs.io/docs/basics/response/error)。

---

## 6.5 Server 生命周期

### 标准集成模式

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/user', () => {
    return HttpResponse.json({ id: 1, name: 'Alice' })
  }),
  http.get('/api/posts', () => {
    return HttpResponse.json([
      { id: 1, title: 'Post 1' },
      { id: 2, title: 'Post 2' },
    ])
  }),
]
```

```typescript
// src/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

```typescript
// vitest.setup.ts
import { server } from './src/mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))

// 每个测试后重置 handler，清除 per-test use() 的效果
afterEach(() => server.resetHandlers())

afterAll(() => server.close())
```

### 生命周期方法详解

```typescript
// ─── server.listen(options?) ───
// 启动拦截。必须在测试开始前调用
server.listen()
server.listen({ onUnhandledRequest: 'warn' })
server.listen({ onUnhandledRequest: 'error' })
server.listen({ onUnhandledRequest: 'bypass' })
// 自定义：
server.listen({
  onUnhandledRequest(request) {
    if (request.url.includes('/api/analytics')) return    // 放行 analytics
    console.warn(`Unhandled: ${request.method} ${request.url}`)
  },
})

// ─── server.close() ───
// 停止拦截，恢复原始 fetch
server.close()

// ─── server.resetHandlers() ───
// 重置到初始 handler 列表（setupServer 时传入的）
server.resetHandlers()
// 也可以替换为新列表：
server.resetHandlers(
  http.get('/api/foo', () => HttpResponse.json({ reset: true })),
)

// ─── server.use(...handlers) ───
// 运行时追加 handlers（LIFO：最后添加的优先匹配）
server.use(
  http.get('/api/user', () => {
    return HttpResponse.json({ overridden: true })
  }),
)

// ─── server.restoreHandlers() (v2 新增) ───
// 只回退 use() 的覆盖，不重置到初始状态
server.restoreHandlers()

// ─── server.listHandlers() (v2 新增) ───
// 返回当前所有 handlers（只读）
const currentHandlers = server.listHandlers()
```

### 生命周期执行时序

```
vitest 启动
  └→ beforeAll: server.listen()
  └→ 测试文件 1:
       ├→ beforeEach（如有）
       ├→ it: 测试用例（如有 use()，在此执行）
       │     └→ server.use(overrideHandler)  // 覆盖特定 handler
       │     └→ 组件发送请求 → MSW 拦截 → 返回 mock 响应
       └→ afterEach: server.resetHandlers()   // 清除 use 效果
  └→ 测试文件 2:
       └→ ...（resetHandlers 保证了 handler 列表回到初始状态）
  └→ afterAll: server.close()
```

> **自我验证说明**：`resetHandlers()` 和 `restoreHandlers()` 的区别常被误解。`resetHandlers()` 将 handlers 列表**重置到 setupServer 时传入的初始状态**，会消除 `use()` 和 `resetHandlers(新 handlers)` 的所有影响。`restoreHandlers()` 仅回退 `use()` 追加的 handlers，保留通过 `resetHandlers(新 handlers)` 设置的状态。在 per-test 覆盖模式中，推荐在 `afterEach` 中使用 `resetHandlers()`（最安全）。

> **Jest 对比：重置策略的思维转换**
>
> 从 Jest 迁移到 Vitest + MSW 时，一个常见的困惑是 `server.resetHandlers()` 和 `jest.resetAllMocks()` 的对应关系。它们看起来都是"重置"，但语义完全不同：
>
> - `jest.resetAllMocks()`：将 **mock 函数的实现** 重置为 `undefined`。调用后 `mockFn()` 返回 `undefined`。
> - `jest.clearAllMocks()`：只清空调用记录（`mock.calls`, `mock.instances`），**保留实现**。
> - `server.resetHandlers()`：将 handler **列表** 重置为 `setupServer` 时的初始状态。调用后所有 `use()` 追加的 handler 被移除。
>
> MSW 没有 `clearHandlers()` 的概念——handler 没有被"调用"或"不调用"的状态，只有"存在"或"不存在"。每次收到请求时，MSW 从 handler 列表中查找匹配。所以重置的本质是**列表恢复**，而非函数复位。
>
> ```typescript
> // Jest：重置 mock 函数
> beforeEach(() => jest.resetAllMocks())
> afterEach(() => jest.clearAllMocks())
>
> // Vitest + MSW：重置 handler 列表
> afterEach(() => server.resetHandlers())
> ```
>
> 如果你的团队以前用 Jest + 模块级 mock，迁移到 Vitest + MSW 后，`afterEach` 中的 `resetHandlers()` 承担了 `resetAllMocks()` 的角色——它确保测试间 handler 隔离。但两者的机制完全不同：前者恢复的是"从 setupServer 开始的初始 handler 列表"，后者是"没有实现"。

---

## 6.6 Per-test Handler 覆盖模式

### 在单个测试中覆盖

```typescript
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

describe('UserProfile', () => {
  it('displays user data on success', async () => {
    render(<UserProfile userId={1} />)

    expect(await screen.findByText('Alice')).toBeInTheDocument()
  })

  it('shows error on 404', async () => {
    // 覆盖默认 handler：返回 404
    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.json({ error: 'Not found' }, { status: 404 })
      })
    )

    render(<UserProfile userId={999} />)

    expect(await screen.findByText(/not found/i)).toBeInTheDocument()
  })

  it('shows error message on network failure', async () => {
    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.error()
      })
    )

    render(<UserProfile userId={1} />)

    expect(await screen.findByText(/network error/i)).toBeInTheDocument()
  })
})
```

### 在 describe 块中覆盖

```typescript
describe('UserProfile error scenarios', () => {
  // 这个 describe 块中的所有测试都使用 500 响应
  beforeAll(() => {
    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.json(
          { error: 'Server error' },
          { status: 500 }
        )
      })
    )
  })

  it('shows error state', async () => {
    render(<UserProfile userId={1} />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/server error/i)
  })

  it('shows retry button', async () => {
    render(<UserProfile userId={1} />)
    expect(await screen.findByRole('button', { name: /retry/i })).toBeInTheDocument()
  })
})
// afterEach 的 resetHandlers() 自动清理 use 的效果
```

### 覆盖的叠加与优先级

```typescript
// server.use() 遵循 LIFO：后添加的先匹配
// 多个 handler 可以匹配同一个请求，但最后一个 use() 的优先级最高

it('demonstrates LIFO order', async () => {
  // 默认 handler 返回 { name: 'Alice' }

  server.use(
    http.get('/api/user', () => {
      return HttpResponse.json({ name: 'Override 1' })
    })
  )

  server.use(
    http.get('/api/user', () => {
      return HttpResponse.json({ name: 'Override 2' })
    })
  )

  const res = await fetch('/api/user')
  const data = await res.json()
  expect(data.name).toBe('Override 2') // 最后的 use 优先
})
```

> **自我验证说明**：`server.use()` 是追加操作，不是替换。handler 列表的行为类似栈：最后的 handler 最先匹配。这意味着 `use()` 的调用顺序很重要——后调用的覆盖先调用的。`resetHandlers()` 清空整个栈回到初始状态。

### { once: true } — 一次性 Handler

MSW 2.x 支持 `{ once: true }` 选项，让 handler 在匹配一次后自动移除。这在需要测试"第一次请求失败、重试后成功"的场景中非常有用：

```typescript
it('first request fails, retry succeeds', async () => {
  server.use(
    http.get('/api/unstable', () => HttpResponse.error(), { once: true }),
    http.get('/api/unstable', () => HttpResponse.json({ status: 'ok' })),
  )

  // 第一次请求触发第一个 handler（once），返回网络错误
  await expect(fetch('/api/unstable')).rejects.toThrow('Failed to fetch')

  // 第一个 handler 已被移除，第二次匹配第二个 handler
  const res = await fetch('/api/unstable')
  expect(await res.json()).toEqual({ status: 'ok' })
})
```

> **注意**：`{ once: true }` 的 handler 在匹配后会被**立即移除**。如果它是唯一的匹配 handler，后续同一请求会 fall through 到下一个 handler 或触发 onUnhandledRequest。这在测试重试逻辑时尤其有用——不需要手动管理计数器。

### 不要替换 globalThis.fetch

```typescript
// ❌ 严重错误：用 vi.fn() 替换 fetch 会破坏 MSW
beforeEach(() => {
  // 这条语句会让 MSW 完全失效
  globalThis.fetch = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ data: 'mocked' }))
  )
})

// 问题：MSW 通过包装原生 fetch 实现拦截
// 当你替换 globalThis.fetch 时，MSW 的包装层也被替换了
// 测试中所有的 server.use() 都不会生效
// 更糟糕的是：测试仍然可能通过，因为 vi.fn() 返回了 mock 数据
// 但实际 MSW handler 根本没有被触发
// 如果有一天你移除了 vi.fn() 替换，测试就全失败了

// ✅ 正确做法：让 MSW 管理网络层
// vitest.setup.ts 中已经配置了 server.listen()
// 测试中通过 server.use() 覆盖 handler，而不是替换 fetch

// 如果你确实需要 mock 一个特定的网络请求：
// 1. 用 MSW 拦截：server.use(http.get('/api/data', resolver))
// 2. 不要碰 globalThis.fetch
// 3. 如果你担心测试中发出了真实请求，设置 onUnhandledRequest: 'error'
```

> **最佳实践**：在你的 `vitest.setup.ts` 中加入以下配置，防止任何测试意外替换 fetch：
>
> ```typescript
> // vitest.setup.ts
> afterEach(() => {
>   server.resetHandlers()
> })
>
> // 可选：阻止替换 fetch
> const originalFetch = globalThis.fetch
> afterEach(() => {
>   if (globalThis.fetch !== originalFetch) {
>     console.warn('WARNING: globalThis.fetch was replaced! MSW may be broken.')
>     globalThis.fetch = originalFetch
>   }
> })
> ```

### 工厂模式：参数化 Handler

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

type User = { id: number; name: string; email: string }

// 导出工厂函数，支持参数化响应
export function createUserHandler(overrides?: Partial<User>) {
  const defaultUser: User = { id: 1, name: 'Alice', email: 'alice@test.com' }
  return http.get('/api/user', () => {
    return HttpResponse.json({ ...defaultUser, ...overrides })
  })
}

export const handlers = [
  createUserHandler(),
]

// ─── 在测试中使用 ───
it('displays custom user name', async () => {
  server.use(createUserHandler({ name: 'Bob', email: 'bob@test.com' }))

  render(<UserProfile />)
  expect(await screen.findByText('Bob')).toBeInTheDocument()
})
```

---

## 6.7 网络策略

### onUnhandledRequest 三种内置策略

```typescript
// ─── 'warn'（默认）───
// 未匹配的请求打印警告，不影响测试
server.listen({ onUnhandledRequest: 'warn' })
// 控制台输出: [MSW] Warning: captured a request without a matching handler
//   · GET /api/analytics/track

// ─── 'error' ───
// 未匹配的请求直接抛错，适合严格模式
server.listen({ onUnhandledRequest: 'error' })
// 未匹配的请求会导致测试失败

// ─── 'bypass' ───
// 未匹配的请求直接放行到真实网络（测试中极少使用）
server.listen({ onUnhandledRequest: 'bypass' })
```

### 自定义筛选逻辑

```typescript
server.listen({
  onUnhandledRequest(request) {
    const url = new URL(request.url)

    // 排除 analytics 和 health check 端点
    const exemptPaths = ['/api/analytics', '/api/health']
    if (exemptPaths.includes(url.pathname)) {
      return   // 不做任何处理，静默放行
    }

    // 排除静态资源请求
    if (url.pathname.startsWith('/static/')) {
      return
    }

    // 其余未匹配请求打印警告
    console.warn(
      `[MSW] Unhandled ${request.method} ${url.pathname}`,
    )
  },
})
```

### 为什么应该使用 'warn' 或 'error' 而非 'bypass'

```typescript
// 如果你设置了 'bypass'，MSW 会对未匹配的请求静默放行
// 后果：你可能在测试中发出真实网络请求（虽然测试环境通常不会真的发出）
// 更严重的是：你永远不会发现没有给某个请求写 handler

// 推荐的开发策略：
// ─ 全局 onUnhandledRequest: 'warn'
// ─ 对已知不需要 handler 的请求（analytics、telemetry 等）在自定义函数中静默
```

> **自我验证说明**：在 jsdom 或 Node 环境中，`'bypass'` 不会真的发出 HTTP 请求（因为没有真实的网络栈）。`'bypass'` 的含义是"不拦截这个请求"，在测试环境中相当于对这个请求不做任何处理。参考 [MSW 文档 - network policy](https://mswjs.io/docs/network-policy/)。

---

## 6.8 GraphQL Mock

MSW v2 仍然支持 GraphQL mocking，但响应构造方式已经统一为 `HttpResponse.json()`：

```typescript
import { graphql, HttpResponse } from 'msw'

// ─── Query 匹配 ───
graphql.query('GetUser', ({ variables }) => {
  // variables: { id: '1' }
  return HttpResponse.json({
    data: {
      user: {
        id: variables.id,
        name: 'Alice',
        email: 'alice@test.com',
      },
    },
  })
})

// ─── Mutation 匹配 ───
graphql.mutation('CreateUser', ({ variables }) => {
  // variables: { name: 'Bob', email: 'bob@test.com' }
  return HttpResponse.json({
    data: {
      createUser: {
        id: 2,
        name: variables.name,
        email: variables.email,
      },
    },
  })
})

// ─── GraphQL 错误响应 ───
graphql.query('GetUser', () => {
  return HttpResponse.json(
    {
      errors: [
        {
          message: 'User not found',
          locations: [{ line: 2, column: 3 }],
        },
      ],
    },
    { status: 200 }  // GraphQL 错误通常用 200 + errors 字段
  )
})
```

### graphql.query/graphql.mutation 的签名

```typescript
import { graphql } from 'msw'

// 按 operation name 匹配 Query
graphql.query<VariablesType, DataType>(
  operationName: string,
  resolver: GraphQLResponseResolver<VariablesType, DataType>,
): GraphQLHandler

// 按 operation name 匹配 Mutation
graphql.mutation<VariablesType, DataType>(
  operationName: string,
  resolver: GraphQLResponseResolver<VariablesType, DataType>,
): GraphQLHandler
```

```typescript
// 完整类型安全的 GraphQL handler
type GetUserVariables = { id: string }
type GetUserData = {
  user: { id: string; name: string; email: string }
}

graphql.query<GetUserVariables, GetUserData>('GetUser', ({ variables }) => {
  return HttpResponse.json({
    data: {
      user: {
        id: variables.id,
        name: 'Alice',
        email: 'alice@test.com',
      },
    },
  })
})
```

> **自我验证说明**：MSW 的 GraphQL 拦截是通过监听 `/graphql` 路径（默认）并检查请求体中的 `operationName` 字段实现的。`graphql.query('GetUser')` 匹配 `operationName: 'GetUser'` 的 query 请求。这与 REST handler 的路径匹配不同——GraphQL 所有请求通常发往同一个 URL。参考 [MSW 文档 - GraphQL](https://mswjs.io/docs/basics/graphql/)。

---

## 6.9 MSW v1 → v2 迁移速查

### 核心变化对照表

| 方面 | MSW v1 | MSW v2 |
|------|--------|--------|
| **响应构造** | `res(ctx.json(data), ctx.status(200))` | `HttpResponse.json(data, { status: 200 })` |
| **Handler 定义** | `rest.get('/api', (req, res, ctx) => ...)` | `http.get('/api', ({ params, request }) => ...)` |
| **请求对象** | MSW 封装的 `req`（`req.body`, `req.params`） | 原生 `Request`（`await request.json()`） |
| **Context 工具** | `ctx.json()`, `ctx.status()`, `ctx.set()`, `ctx.delay()` | 全部移除，改用 `HttpResponse` 参数 + 独立 `delay()` |
| **Passthrough** | `req.passthrough()` | `HttpResponse.passthrough()` |
| **延迟** | `ctx.delay(ms)` | 独立 `delay()` 函数 (`import { delay } from 'msw'`) |
| **REST namespace** | `rest.get`, `rest.post` ... | `http.get`, `http.post` ...（`rest` 移除） |
| **GraphQL 响应** | `res(ctx.data({ user }))` | `HttpResponse.json({ data: { user } })` |
| **重定向** | `res(ctx.status(307), ctx.set('Location', url))` | `new HttpResponse(null, { status: 307, headers: { Location: url } })` |
| **server.listen()** | 返回 Promise | 同步方法，不再返回 Promise |

### 迁移示例

```typescript
// ────── v1 ──────
import { rest } from 'msw'

rest.get('/api/users/:id', (req, res, ctx) => {
  const { id } = req.params
  return res(
    ctx.json({ id: Number(id), name: 'Alice' }),
    ctx.status(200),
    ctx.delay(100),
  )
})

rest.post('/api/users', (req, res, ctx) => {
  const body = req.body
  return res(ctx.json({ ...body, id: 1 }), ctx.status(201))
})

// ────── v2 ──────
import { http, HttpResponse, delay } from 'msw'

http.get<{ id: string }>('/api/users/:id', async ({ params }) => {
  await delay(100)
  return HttpResponse.json({ id: Number(params.id), name: 'Alice' })
})

http.post('/api/users', async ({ request }) => {
  const body = await request.json()
  return HttpResponse.json({ ...body, id: 1 }, { status: 201 })
})
```

### 迁移检查清单

| 步骤 | v1 写法 | v2 写法 |
|------|---------|---------|
| 1. 导入 | `import { rest } from 'msw'` | `import { http } from 'msw'` |
| 2. Handler | `rest.get(path, (req, res, ctx) => ...)` | `http.get(path, ({ params, request }) => ...)` |
| 3. 响应 | `res(ctx.json(body), ctx.status(n))` | `HttpResponse.json(body, { status: n })` |
| 4. 路径参数 | `req.params.id` | `params.id` |
| 5. 请求体 | `req.body` | `await request.json()` |
| 6. 请求头 | `req.headers.get('X')` | `request.headers.get('X')`（实际上相同） |
| 7. 搜索参数 | `req.url.searchParams.get('q')` | `new URL(request.url).searchParams.get('q')` |
| 8. 延迟 | `ctx.delay(100)` | `await delay(100)` |
| 9. Cookie | `req.cookies` | `cookies`（参数解构） |
| 10. 错误 | `res(ctx.status(500))` | `new HttpResponse(null, { status: 500 })` |
| 11. 网络错误 | `res.networkError()` | `HttpResponse.error()` |
| 12. 放行 | `req.passthrough()` | `HttpResponse.passthrough()` |

> **自我验证说明**：`delay()` 现在是 msw 的独立导出，不再通过 `ctx` 对象。`delay()` 默认范围是 100-200ms 的随机延迟。如果需要精确延迟，传入具体毫秒数：`await delay(300)`。如果使用了 v1 的 `ctx.delay()` 语法，在 v2 中会直接报错——这个 API 已经完全移除。参考 [MSW v2 Migration Guide](https://mswjs.io/docs/migrations/1.x-to-2.x/)。

---

## 6.10 反模式

### 反模式 1：在测试中直接使用 vi.mock 替代 MSW

```typescript
// ❌ 错误：模块级 mock 跳过真实网络请求流程
vi.mock('../api/user', () => ({
  fetchUser: vi.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
}))
// 如果 fetchUser 内部读取某个环境变量来拼接 URL，这个逻辑被跳过
// 如果组件后来改用 react-query，mock 完全无效

// ✅ 正确：MSW 网络层 mock
server.use(
  http.get('/api/user', () => {
    return HttpResponse.json({ id: 1, name: 'Alice' })
  })
)
// 组件使用 fetchUser 内部调用 fetch('/api/user') → MSW 拦截
// 完整的请求→响应链路被覆盖
```

### 反模式 2：在 MSW handler 中写复杂业务逻辑

```typescript
// ❌ 错误：handler 中复现了服务端逻辑
http.post('/api/orders', async ({ request }) => {
  const order = await request.json()

  // 在 mock 中复现复杂的价格计算和库存验证
  const totalPrice = order.items.reduce((sum, item) => {
    const discount = item.quantity > 10 ? 0.9 : 1.0
    return sum + item.price * item.quantity * discount
  }, 0)

  if (totalPrice > 10000) {
    return HttpResponse.json({ error: 'Order exceeds limit' }, { status: 400 })
  }
  // 问题：这些逻辑与真实服务端逻辑可能不一致
  // 测试通过了，但真实 API 可能返回不同结果
  return HttpResponse.json({ id: 1, totalPrice })
})

// ✅ 正确：handler 只返回固定 mock 数据
http.post('/api/orders', async ({ request }) => {
  const order = await request.json()
  // 固定返回，不重复业务逻辑
  return HttpResponse.json(
    { id: 1, ...order, totalPrice: 99.99 },
    { status: 201 }
  )
})
```

### 反模式 3：忘记重置 handler 导致测试间污染

```typescript
// ❌ 错误：某个测试用 server.use 覆盖了 handler 但没有 reset
it('test A - overrides handler', async () => {
  server.use(
    http.get('/api/user', () => new HttpResponse(null, { status: 500 }))
  )
  // 测试逻辑...
  // 忘记在 afterEach 中 resetHandlers
})

it('test B - expects default handler', async () => {
  // 但 test A 的覆盖仍然生效，返回 500 而非 200
  render(<UserProfile />)
  // 测试失败，因为 handler 还是 test A 覆盖后的状态
})

// ✅ 正确：在 vitest.setup.ts 中配置全局 reset
afterEach(() => server.resetHandlers())
```

### 反模式 4：未处理网络错误和 HTTP 错误的区别

```typescript
// ❌ 错误：把网络错误当作 HTTP 500 处理
it('handles network error', async () => {
  server.use(
    http.get('/api/user', () => HttpResponse.error())
  )

  // 网络错误导致 fetch Promise reject —— 不能用 response.ok 判断
  // 应该用 try/catch 或 .catch()
  const response = await fetch('/api/user')
  expect(response.status).toBe(500)  // ❌ 永远不会执行——fetch 已经抛错了
})

// ✅ 正确：区分两种错误
it('handles HTTP 500 error', async () => {
  server.use(
    http.get('/api/user', () => new HttpResponse(null, { status: 500 }))
  )
  const response = await fetch('/api/user')
  expect(response.status).toBe(500)
  expect(response.ok).toBe(false)
})

it('handles network error (fetch rejection)', async () => {
  server.use(
    http.get('/api/user', () => HttpResponse.error())
  )
  await expect(fetch('/api/user')).rejects.toThrow('Failed to fetch')
})
```

### 反模式 5：handler 路径模式过于宽泛

```typescript
// ❌ 错误：通配符 * 匹配过多请求
http.get('/api/*', () => HttpResponse.json({}))  // 拦截所有 /api/ 下的 GET
// 后续添加的细粒度 handler 永远不会被触发

// ✅ 正确：尽可能精确
http.get('/api/users', () => HttpResponse.json([]))
http.get('/api/users/:id', ({ params }) => HttpResponse.json({ id: params.id }))
```

---

## 6.11 本章练习

1. 搭建完整的 MSW 项目结构：

```
src/mocks/
├── handlers.ts     # 全局 handler
├── server.ts       # setupServer 实例
└── browser.ts      # (可选) setupWorker 实例
```

在 `handlers.ts` 中创建覆盖以下场景的 handler：
- `GET /api/todos` — 返回 todo 列表
- `POST /api/todos` — 创建 todo，返回 201
- `PATCH /api/todos/:id` — 更新 todo 完成状态
- `DELETE /api/todos/:id` — 删除 todo，返回 204

2. 为 Todo 应用组件编写测试，覆盖：
- 初始加载显示 todo 列表
- 添加新的 todo
- 切换 todo 完成状态
- 删除 todo
- 服务器返回 500 时的错误处理
- 网络错误（`HttpResponse.error()`）时的错误处理

3. 练习 per-test handler 覆盖：
- 在一个 describe 块中覆盖 GET /api/todos 返回空数组
- 在另一个 describe 块中让 GET /api/todos 一直返回 loading
- 使用 `server.use()` 在单个测试中让 POST /api/todos 返回 400

4. 思考题：如果你的项目使用 GraphQL，如何为 `graphql.query('GetTodos')` 编写 MSW handler？它与 REST handler 的匹配方式有什么区别？

---

## 6.12 本章总结

- 网络层 mock（MSW）优于模块级 mock（vi.mock），因为前者与实现解耦、覆盖完整链路、跨环境共享
- MSW 三层架构：Handler 定义 → Server 实例 → 请求拦截器
- `http.get/post/put/patch/delete` 使用 TypeScript 泛型约束路径参数类型
- `HttpResponse.json()`/`text()`/`xml()`/`error()`/`passthrough()` 覆盖所有响应需求
- Server 生命周期：`listen` → `use` → `resetHandlers` → `close`
- Per-test handler 覆盖使用 `server.use()`（LIFO 优先级），`afterEach` 中用 `resetHandlers()` 清理
- 区分 HTTP 错误（5xx）和网络错误（`HttpResponse.error()` 导致 fetch reject）
- GraphQL 通过 `graphql.query`/`graphql.mutation` 按 operation name 匹配
- v1 → v2 核心变化：`rest` → `http`，`res(ctx.json())` → `HttpResponse.json()`，`req.body` → `await request.json()`

## 关联阅读

- [第7章：数据层测试](07-数据层测试.md) — MSW handler 在数据层的实战
- [第2章：测试环境搭建](02-测试环境搭建.md) — MSW 在 setup 文件中的配置
- [第15章：进阶测试场景](15-进阶测试场景.md) — MSW WebSocket/GraphQL 拦截
