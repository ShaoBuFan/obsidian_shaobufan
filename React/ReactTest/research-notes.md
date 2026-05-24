# Research Notes — React Testing

---

## MSW v2+ 官方文档深度研究

以下内容基于 MSW v2 (Mock Service Worker) 官方文档体系整理，涵盖全部核心 API 和 Vitest 集成模式。

---

### 1. setupServer() — 签名与 Node.js 测试设置

```typescript
// msw/node 导出
import { setupServer } from 'msw/node'

// 签名
function setupServer(...handlers: HttpHandler[]): SetupServerApi
```

`setupServer` 是 MSW 在 Node.js 环境（Jest、Vitest）下的入口。它接受一组请求处理器（handlers），返回一个 `SetupServerApi` 实例，该实例提供完整的生命周期控制。

**典型测试文件设置：**

```typescript
// src/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

**与 Vitest 集成：**

```typescript
// vitest.setup.ts
import { server } from './src/mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    setupFiles: ['./vitest.setup.ts'],
  },
})
```

**`SetupServerApi` 接口：**

```typescript
interface SetupServerApi {
  listen(options?: ServerListenOptions): void
  close(): void
  resetHandlers(...nextHandlers: HttpHandler[]): void
  use(...handlers: HttpHandler[]): void
  // v2 新增
  restoreHandlers(): void
  listHandlers(): readonly HttpHandler[]
  // 边界情况处理
  printHandlers(): void
}
```

---

### 2. http.get / http.post / http.put / http.patch / http.delete — 完整 TypeScript 签名

```typescript
import { http, HttpResponse } from 'msw'

// ─── 每一方法的完整签名 ───

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

**`ResponseResolver` 签名：**

```typescript
type ResponseResolver<Params extends Record<string, string>> = (
  args: ResolverArgs<Params>,
) => HttpResponse | Promise<HttpResponse>

interface ResolverArgs<Params> {
  request: Request              // 原生 fetch Request 对象
  params: Params                // 路径参数，如 { id: '123' }
  cookies: Record<string, string>
  requestId: string             // v2 新增，每个请求唯一 UUID
}
```

**完整示例：**

```typescript
interface UserParams {
  userId: string
}

http.get<{ category: string }>('/api/products/:category', ({ params, request }) => {
  console.log(params.category)    // ':category' 路径段的值
  console.log(request.method)     // 'GET'
  return HttpResponse.json({ items: [] })
})

http.post<{}, { title: string }>(
  '/api/todos',
  async ({ request }) => {
    const body = await request.json() as { title: string }
    return HttpResponse.json({ id: 1, title: body.title }, { status: 201 })
  },
)

// 正则匹配
http.get(/\/api\/users\/(\d+)/, ({ params }) => {
  // params 为捕获组匹配的数组
  return HttpResponse.json({ id: params[0] })
})
```

---

### 3. HttpResponse 静态方法 — 精确签名

v2 废弃了 v1 的 `res()` + `ctx()` 组合模式，改用 `HttpResponse` 类及其静态工厂方法。

```typescript
import { HttpResponse } from 'msw'

// ─── HttpResponse.json() ───
// 最常用的 JSON 响应工厂
HttpResponse.json(
  body?: BodyType | null,          // 自动 JSON.stringify
  init?: ResponseInit,             // status, statusText, headers
): HttpResponse

// 示例
HttpResponse.json({ id: 1, name: 'Alice' }, { status: 200 })
HttpResponse.json(null, { status: 204 })


// ─── HttpResponse.xml() ───
// 返回 Content-Type: application/xml
HttpResponse.xml(
  body?: XMLBodyType | null,
  init?: ResponseInit,
): HttpResponse

// 示例
HttpResponse.xml('<root><item>1</item></root>')
HttpResponse.xml('<error>Not found</error>', { status: 404 })


// ─── HttpResponse.text() ───
HttpResponse.text(
  body?: string | null,
  init?: ResponseInit,
): HttpResponse

HttpResponse.text('plain text')
HttpResponse.text('Created', { status: 201 })


// ─── HttpResponse.arrayBuffer() ───
HttpResponse.arrayBuffer(
  body?: ArrayBuffer | null,
  init?: ResponseInit,
): HttpResponse


// ─── HttpResponse.error() ───
// ⚠️ 模拟网络错误 —— 客户端会收到网络级拒绝
HttpResponse.error(): HttpResponse

// 示例：模拟服务器宕机或 DNS 失败
http.get('/api/fragile-endpoint', () => {
  return HttpResponse.error()
})


// ─── new HttpResponse() ───
// 低层级构造函数，用于完全控制
new HttpResponse(body: BodyInit | null, init?: ResponseInit)

// 302 重定向
new HttpResponse(null, {
  status: 302,
  headers: { Location: '/new-location' },
})
```

**`ResponseInit` 接口：**

```typescript
interface ResponseInit {
  status?: number          // 默认 200
  statusText?: string
  headers?: HeadersInit   // Record<string, string> 或 Headers 实例
}
```

---

### 4. Request Matching — 路径参数、Search Params、Headers、Body

#### 4a. 路径参数 (`:param`)

```typescript
// 路径中的 :segment 会自动提取到 params 对象
http.get<{ id: string }>(
  '/api/users/:id',
  ({ params }) => {
    // params.id 即 URL 中对应的段
    return HttpResponse.json({ userId: params.id })
  },
)

// 多级参数
http.get('/api/:resource/:id/relationships/:relation', ({ params }) => {
  // params: { resource: 'users', id: '42', relation: 'friends' }
  return HttpResponse.json({})
})
```

#### 4b. Search Params (查询参数)

```typescript
http.get('/api/search', ({ request }) => {
  const url = new URL(request.url)
  const query = url.searchParams.get('q')
  const page = Number(url.searchParams.get('page')) || 1

  return HttpResponse.json({ results: [], page })
})
```

#### 4c. Headers

```typescript
http.get('/api/protected', ({ request }) => {
  const auth = request.headers.get('Authorization')

  if (!auth) {
    return new HttpResponse(null, { status: 401 })
  }

  return HttpResponse.json({ data: 'secret' })
})
```

#### 4d. Request Body

```typescript
http.post('/api/users', async ({ request }) => {
  const body = await request.json()
  // body 已是解析后的 JS 对象
  return HttpResponse.json({ received: true, ...body }, { status: 201 })
})

// 文本 body
http.post('/api/raw', async ({ request }) => {
  const text = await request.text()
  return HttpResponse.text(`Echo: ${text}`)
})
```

#### 4e. GraphQL 匹配

MSW v2 通过 `graphql` 命名空间支持 GraphQL（仍保留，但底层已重构）：

```typescript
import { graphql, HttpResponse } from 'msw'

// 按 operation name 匹配
graphql.query('GetUser', ({ variables }) => {
  // variables: { id: '1' }
  return HttpResponse.json({
    data: { user: { id: variables.id, name: 'Alice' } },
  })
})

graphql.mutation('CreateUser', ({ variables }) => {
  return HttpResponse.json({
    data: { createUser: { id: 2, name: variables.name } },
  })
})

// ⚠️ v2 中 graphql 的 response 也需要用 HttpResponse.json()
// v1 的 res(ctx.data(...)) 模式不再适用
```

#### 4f. 通配符匹配

```typescript
// 所有 /api/ 开头的请求
http.get('/api/*', resolver)

// 精确路径
http.get('/api/users', resolver)
```

---

### 5. Lifecycle Hooks — server.listen / close / resetHandlers / use

```typescript
interface ServerListenOptions {
  onUnhandledRequest?: 'bypass' | 'warn' | 'error' | RequestHandler
}
```

#### 5a. `server.listen(options?)`

```typescript
// 启动拦截。必须在测试开始前调用
server.listen()

// 选项：未处理请求的策略
server.listen({ onUnhandledRequest: 'warn' })  // 默认：打印警告
server.listen({ onUnhandledRequest: 'error' }) // 严格模式：抛错
server.listen({ onUnhandledRequest: 'bypass' })// 静默放行

// 自定义处理器
server.listen({
  onUnhandledRequest(request) {
    if (request.url.includes('/api/analytics')) {
      return          // 跳过 analytics 请求
    }
    console.warn(`Unhandled: ${request.method} ${request.url}`)
  },
})
```

#### 5b. `server.close()`

```typescript
// 停止拦截，恢复原始 fetch
// 通常在 afterAll 中调用
server.close()
```

#### 5c. `server.resetHandlers(...handlers)`

```typescript
// 重置到初始 handlers（调用 setupServer 时传入的）
server.resetHandlers()

// 或全部替换为新 handlers
server.resetHandlers(
  http.get('/api/foo', () => HttpResponse.json({ reset: true })),
)

// 最常用：afterEach 中重置，清除 per-test 覆盖
afterEach(() => server.resetHandlers())
```

#### 5d. `server.use(...handlers)`

```typescript
// 运行时追加 handlers (不会清除已有的)
// handlers 遵循 LIFO（后添加的先匹配）
server.use(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({ overridden: true, id: params.id })
  }),
)
```

#### 5e. `server.restoreHandlers()` — v2 新增

```typescript
// 恢复所有曾被 `server.use()` 覆盖的 handlers 到原始状态
// 不同于 resetHandlers（它回到初始集合），restoreHandlers 只回退 use() 的覆盖
server.restoreHandlers()
```

---

### 6. server.use() — 运行时覆盖行为详解

`server.use()` 是 MSW 测试模式的核心特性，用于 per-test handler 覆盖。

**行为规则：**

1. **LIFO（后进先出）**：最后添加的 handler 优先匹配
2. **临时性**：仅在当前测试中有效（配合 `afterEach(() => server.resetHandlers())`）
3. **按路径匹配**：相同路径的 handler 会覆盖之前的

```typescript
// handlers.ts — 全局默认 handlers
export const handlers = [
  http.get('/api/user', () => {
    return HttpResponse.json({ name: 'Default User' })
  }),
  http.post('/api/user', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ ...body, created: true }, { status: 201 })
  }),
]

// ─── Per-test 覆盖 ───

describe('User profile', () => {
  // 为该 describe 块的所有测试覆盖 GET /api/user
  beforeAll(() => {
    server.use(
      http.get('/api/user', () => {
        return HttpResponse.json({ name: 'Overridden User' })
      }),
    )
  })

  it('returns the overridden user', async () => {
    const res = await fetch('/api/user')
    const data = await res.json()
    expect(data.name).toBe('Overridden User')
  })
})

describe('Error scenarios', () => {
  it('handles 500 error', async () => {
    server.use(
      http.get('/api/user', () => {
        return new HttpResponse(null, { status: 500 })
      }),
    )

    const res = await fetch('/api/user')
    expect(res.status).toBe(500)
  })

  it('handles network error', async () => {
    server.use(
      http.get('/api/user', () => HttpResponse.error()),
    )

    await expect(fetch('/api/user')).rejects.toThrow('Failed to fetch')
  })
})
```

**重要注意事项：**

- `use()` 添加的 handler 在 `resetHandlers()` 或 `restoreHandlers()` 调用后失效
- 多个 `use()` 调用可叠加，但建议在每个测试中只覆盖所需的最小集合
- 不是 handler 替换 —— 是追加到 handler 列表头部

---

### 7. Network Error Simulation

MSW v2 通过 `HttpResponse.error()` 提供网络错误模拟。

```typescript
import { HttpResponse } from 'msw'

// ─── 基础网络错误 ───
http.get('/api/unstable', () => {
  return HttpResponse.error()
})

// 客户端 fetch 的行为：
// fetch('/api/unstable')
//   .catch(err => console.log(err)) // TypeError: Failed to fetch

// ─── 条件性网络错误（模拟部分失败）───
http.get('/api/orders', ({ request }) => {
  const url = new URL(request.url)
  const userId = url.searchParams.get('userId')

  if (userId === 'bad-actor') {
    return HttpResponse.error()
  }
  return HttpResponse.json({ orders: [] })
})

// ─── 与 delay 结合（模拟超时形态）───
http.get('/api/slow', async () => {
  await delay(10000)    // 超时后网络错误
  return HttpResponse.error()
})
```

**`HttpResponse.error()` 的内部行为：**
- 创建一个被拒绝（rejected）的 Promise，模拟 `fetch` 的网络级失败
- `fetch` API 会抛出 `TypeError: Failed to fetch`
- 不同于 5xx 状态码 —— 后者是 HTTP 响应，而 `HttpResponse.error()` 是传输级错误

---

### 8. Passthrough 与 Bypass — 放行未处理请求

#### 8a. Handler 级别的 passthrough

```typescript
import { http, HttpResponse } from 'msw'

// 对特定路径放行到真实网络
// ⚠️ v2 中的 passthrough 行为有变化
http.get('/api/analytics', () => {
  // v2: 直接 passthrough()
  return HttpResponse.passthrough()
  // 该请求会发送到真实服务器，不会返回 mock 数据
})

// 条件放行
http.get('/api/proxy*', ({ request }) => {
  const url = new URL(request.url)
  if (url.searchParams.has('realtime')) {
    return HttpResponse.passthrough()
  }
  return HttpResponse.json({ mocked: true })
})
```

#### 8b. 全局 Bypass — `onUnhandledRequest`

```typescript
// listen 时配置全局未处理请求策略
server.listen({
  onUnhandledRequest: 'bypass',  // 未匹配的请求直接放行
})

// 更精细的控制：自定义函数
server.listen({
  onUnhandledRequest(request) {
    const exemptPaths = ['/api/analytics', '/api/health']
    const url = new URL(request.url)

    if (exemptPaths.includes(url.pathname)) {
      return   // 跳过警告
    }
    console.warn(`Unhandled request: ${request.method} ${url.pathname}`)
  },
})

// 严格模式：匹配未处理则测试失败
server.listen({
  onUnhandledRequest: 'error',
})
```

#### 8c. v2 中的变更

在 MSW v2 中，`passthrough` 行为从 v1 的 `req.passthrough()` 改为 `HttpResponse.passthrough()` 静态方法。v1 中 `passthrough` 是请求对象的方法，v2 中改为响应对象的方法：

```typescript
// v1
// return req.passthrough()

// v2
return HttpResponse.passthrough()
```

---

### 9. Vitest 集成最佳实践 — 完整测试模式

#### 9a. 项目结构

```
src/
  mocks/
    handlers.ts          # 全局 handers（共享）
    server.ts            # setupServer 实例
    browser.ts           # (可选) 浏览器端 MSW
```

#### 9b. handlers.ts — 集中管理

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  // REST handlers
  http.get('/api/user', () => {
    return HttpResponse.json({ id: 1, name: 'Alice', email: 'alice@test.com' })
  }),
  http.get('/api/posts', () => {
    return HttpResponse.json([
      { id: 1, title: 'Post 1', body: '...' },
      { id: 2, title: 'Post 2', body: '...' },
    ])
  }),
  http.post('/api/posts', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: Date.now(), ...body }, { status: 201 })
  }),
]
```

#### 9c. server.ts — 单例

```typescript
// src/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

#### 9d. vitest.setup.ts — 全局生命周期

```typescript
// vitest.setup.ts
import { server } from './src/mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))

// 每个测试后重置 handlers，清除 per-test use() 的效果
afterEach(() => server.resetHandlers())

afterAll(() => server.close())
```

#### 9e. vitest.config.ts

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',        // 或 'jsdom' (React 组件测试)
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
```

#### 9f. 实际测试示例

```typescript
// src/api/user.test.ts
import { server } from '../../mocks/server'
import { http, HttpResponse } from 'msw'

describe('fetchUser', () => {
  it('fetches user data successfully', async () => {
    const user = await fetchUser(1)
    expect(user.name).toBe('Alice')
  })

  it('handles 404 error', async () => {
    server.use(
      http.get('/api/user', () => {
        return new HttpResponse(null, { status: 404 })
      }),
    )
    await expect(fetchUser(999)).rejects.toThrow('Not found')
  })

  it('handles network failure', async () => {
    server.use(
      http.get('/api/user', () => HttpResponse.error()),
    )
    await expect(fetchUser(1)).rejects.toThrow('Failed to fetch')
  })

  it('handles server error', async () => {
    server.use(
      http.get('/api/user', () => {
        return HttpResponse.json(
          { message: 'Internal Server Error' },
          { status: 500 },
        )
      }),
    )
    const res = await fetch('/api/user')
    expect(res.status).toBe(500)
  })
})
```

#### 9g. 无全局 server 的独立测试（轻量模式）

MSW v2 支持不通过 `setupServer` 直接使用 handler：

```typescript
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

it('can create an isolated server per test', async () => {
  const isolatedServer = setupServer(
    http.get('/api/health', () => HttpResponse.json({ status: 'ok' })),
  )
  isolatedServer.listen()
  // ... test logic
  isolatedServer.close()
})
```

---

### 10. MSW v1 → v2 Breaking Changes

下表汇总 v1 到 v2 的主要变更：

| 方面 | MSW v1 | MSW v2 |
|------|--------|--------|
| **响应构造** | `res(ctx.json(data), ctx.status(200))` | `HttpResponse.json(data, { status: 200 })` |
| **Handler 定义** | `rest.get('/api', (req, res, ctx) => ...)` | `http.get('/api', ({ params, request }) => ...)` |
| **Composition 模式** | `res(ctx.json(), ctx.delay(500), ctx.status(201))` | 无 composition；delay 作为独立函数 `await delay(500)` |
| **`req` 对象** | MSW 封装的请求对象(`req.body`, `req.params`) | 原生 `Request` (Fetch API 标准) |
| **`ctx` 工具集** | `ctx.json()`, `ctx.status()`, `ctx.set()`, `ctx.delay()` | 全部移除；改用 `HttpResponse` 参数和独立 `delay()` |
| **`req.passthrough()`** | 请求对象的 passthrough | `HttpResponse.passthrough()` 静态方法 |
| **GraphQL** | `graphql.query('Op', (req, res, ctx) => res(ctx.data({})))` | `graphql.query('Op', ({ variables }) => HttpResponse.json({ data: {} }))` |
| **TypeScript** | 类型支持有限 | 完整的泛型参数类型 (`http.get<Params>`, `ResponseResolver<Params>`) |
| **`setupServer`** | 签名相同 | 签名基本一致，新增 `restoreHandlers()` |
| **`server.listen()`** | 返回 Promise | 同步方法，不再返回 Promise |
| **生命周期事件** | `server.events.on('request:start', ...)` | API 有变化（事件名和回调签名） |
| **`response` 事件** | `server.events.on('response:mocked', ...)` | 新增 `server.events.on('response:bypass', ...)` 事件 |
| **Cookie 处理** | `ctx.cookie()` | 通过 `document.cookie` 或 `Response` header 处理 |
| **Browser worker** | `setupWorker` 返回值不同 | 调整了 lifecycle API |
| **`rest` namespace** | `rest.get`, `rest.post`, ... (全部 REST) | `rest` 移除，统一使用 `http` namespace |
| **延迟** | `ctx.delay(ms)` | 独立 `delay()` 函数 (`import { delay } from 'msw'`) |
| **重定向** | `res(ctx.status(307), ctx.set('Location', url))` | `new HttpResponse(null, { status: 307, headers: { Location: url } })` |

**迁移核心原则：**

```
v1: res(ctx.json(body), ctx.status(code))
v2: HttpResponse.json(body, { status: code })

v1: rest.get(path, (req, res, ctx) => ...)
v2: http.get(path, ({ params, request, cookies, requestId }) => ...)

v1: req.passthrough()
v2: HttpResponse.passthrough()
```

**v2 中完全移除的 API：**
- `res()` — 不再存在
- `ctx` 对象 — 所有 `ctx.*` 方法移除
- `rest` namespace — 全部改为 `http`
- `req.body` — v2 使用 `await request.json()` 或 `await request.text()` (原生 fetch API)
- `req.headers` — v2 使用 `request.headers.get()`

---

### 参考链接

- MSW 官方文档: https://mswjs.io/docs/
- 快速开始: https://mswjs.io/docs/getting-started
- 核心概念: https://mswjs.io/docs/concepts/
- 基础用法: https://mswjs.io/docs/basics/
- setupServer API: https://mswjs.io/docs/api/setup-server/
- http API: https://mswjs.io/docs/api/http/
- 最佳实践: https://mswjs.io/docs/best-practices/
- 网络策略: https://mswjs.io/docs/network-policy/

---

## Vitest 官方文档深度研究

> 以下内容基于 Vitest 官方文档 (vitest.dev) 知识整理。WebFetch 权限被拒无法实时验证最新版本，内容基于训练数据中的 Vitest 1.x/2.x 文档。

---

### 1. vitest.config.ts key settings and TypeScript types

```ts
// vitest/config 导出 defineConfig 和 UserConfig
import { defineConfig, UserConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // === 基础 ===
    globals: boolean,                                // default: false
    environment: 'node' | 'jsdom' | 'happy-dom' | 'edge-runtime', // default: 'node'
    root: string,                                    // default: process.cwd()
    include: string[],                                // default: ['**/*.{test,spec}.?(c|m)[jt]s?(x)']
    exclude: string[],                                // default: ['**/node_modules/**', '**/dist/**', ...]
    setupFiles: string | string[],                    // 每个测试文件前运行的 setup
    globalSetup: string | string[],                   // 全局运行一次（支持 async）
    testTimeout: number,                              // default: 5000
    hookTimeout: number,                              // default: 10000

    // === 并行 ===
    pool: 'forks' | 'threads' | 'vmThreads',          // default: 'forks' (v2+)
    fileParallelism: boolean,                          // default: true
    maxConcurrency: number,                            // default: 5
    maxWorkers: number,
    minWorkers: number,

    // === 覆盖率 ===
    coverage: CoverageOptions,                         // 见 #8

    // === 别名 ===
    alias: Record<string, string>,                     // 同 vite.resolve.alias

    // === 快照 ===
    snapshotFormat: PrettyFormatOptions,               // default: {}
    update: boolean,                                   // default: false

    // === 重试 ===
    retry: number,                                     // default: 0

    // === 其他 ===
    name: string,                                      // workspace 项目标签
    outputFile: string | Record<string, string>,
    reporters: string | string[],                      // default: 'default'
    watch: boolean,                                    // default: true (非 CI)
  },
  // 所有 Vite 配置选项也可用
})
```

**React 测试典型配置：**

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.*', 'src/test/**'],
    },
  },
})
```

---

### 2. vi.mock(), vi.fn(), vi.spyOn() — exact API signatures

#### vi.fn()

```ts
// MockInstance 类型
interface MockInstance<TArgs extends any[] = any[], TReturns = any> {
  (...args: TArgs): TReturns
  mock: {
    calls: TArgs[]
    results: { type: string; value: any }[]
    contexts: any[]
    lastCall: TArgs | undefined
  }
  getMockName(): string
  mockName(name: string): this
  mockImplementation(fn: (...args: TArgs) => TReturns): this
  mockImplementationOnce(fn: (...args: TArgs) => TReturns): this
  mockReturnThis(): this
  mockResolvedValue(value: Awaited<TReturns>): this
  mockResolvedValueOnce(value: Awaited<TReturns>): this
  mockRejectedValue(error: unknown): this
  mockRejectedValueOnce(error: unknown): this
  mockReturnValue(value: TReturns): this
  mockReturnValueOnce(value: TReturns): this
  withImplementation(fn: (...args: TArgs) => TReturns, cb: () => void): void
  getMockImplementation(): ((...args: TArgs) => TReturns) | undefined
  mockClear(): this     // 重置调用记录
  mockReset(): this     // 重置调用记录 + 清空实现
  mockRestore(): this   // 重置调用记录 + 恢复原始实现（spyOn）
}

// 重载
function vi.fn(): MockInstance<[], undefined>
function vi.fn<TArgs extends any[], TReturns>(
  fn: (...args: TArgs) => TReturns
): MockInstance<TArgs, TReturns>
```

#### vi.spyOn()

```ts
// 基本重载
function vi.spyOn<T, K extends keyof T>(obj: T, method: K): MockInstance<
  T[K] extends (...args: infer A) => any ? A : never,
  T[K] extends (...args: any[]) => infer R ? R : never
>

// getter/setter 重载
function vi.spyOn<T, K extends keyof T>(
  obj: T,
  method: K,
  accessType: 'get' | 'set'
): MockInstance

// 示例
const spy = vi.spyOn(console, 'log')
spy.mockImplementation((msg) => process.send?.(msg))

vi.spyOn(Date, 'now').mockReturnValue(1234567890)
vi.spyOn(localStorage, 'getItem').mockReturnValue('mocked-value')
```

#### vi.mock()

```ts
function vi.mock(path: string, factory?: () => any): void
function vi.mock(path: string, factory?: (importOriginal: () => Promise<any>) => Promise<any>): void  // v1.3+ async factory

// 1) 全量 mock — 所有导出被替换为 vi.fn()
vi.mock('path/to/module')

// 2) 工厂函数
vi.mock('path/to/module', () => ({
  default: vi.fn(),
  namedExport: vi.fn(() => 'mocked'),
}))

// 3) 部分覆盖（保留原始导出）
vi.mock('path/to/module', async (importOriginal) => {
  const mod = await importOriginal()
  return { ...mod, namedExport: vi.fn() }
})

// 辅助方法
vi.importActual(path: string): Promise<any>
vi.importMock(path: string): Promise<any>
vi.unmock(path: string): void

// hoisted 辅助（v1.3+）
vi.hoisted(factory: () => any): any
// 用于在工厂函数外部创建变量后再在 vi.mock 中使用
const { mockedFn } = vi.hoisted(() => ({ mockedFn: vi.fn() }))
vi.mock('./module', () => ({ default: mockedFn }))
```

**关键行为：**
- `vi.mock()` 被自动 **hoist** 到文件顶部（类似 jest.mock）
- 工厂函数内直接使用 `vi.fn()` 不会 hoist — 需用 `vi.hoisted()`（v1.3+）
- 工厂函数支持 `async`（v1.3+）

#### Mock 清理

```ts
vi.clearAllMocks(): void   // 所有 mock mockClear
vi.resetAllMocks(): void   // 所有 mock mockReset
vi.restoreAllMocks(): void // 所有 spy mockRestore

// 推荐在每个测试后自动清理
afterEach(() => { vi.clearAllMocks() })
```

---

### 3. Fake Timers

```ts
// === 启用 ===
function vi.useFakeTimers(config?: FakeTimerInstallOpts): void

interface FakeTimerInstallOpts {
  now?: number | Date
  toFake?: string[]           // 可选：setTimeout, clearTimeout, setInterval,
                              // clearInterval, Date, performance, queueMicrotask,
                              // requestAnimationFrame, clearImmediate, nextTick 等
  loopLimit?: number          // default: 10000 (ms)
  shouldAdvanceTime?: boolean
  advanceTimeDelta?: number   // default: 20 (ms)
}

// === 恢复 ===
function vi.useRealTimers(): void

// === 时间推进 ===
function vi.advanceTimersByTime(msToRun: number): void
// 同步推进指定毫秒，触发所有已到期的定时器

function vi.advanceTimersToNextTimer(): void
// 推进到下一个待处理定时器

function vi.advanceTimersByTimeAsync(msToRun: number): Promise<void>
// 异步版（处理 pending promise）

function vi.advanceTimersToNextTimerAsync(): Promise<void>
// 异步版

// === 其他 ===
function vi.getTimerCount(): number
function vi.getRealSystemTime(): number
function vi.setSystemTime(time: number | Date): void

// === 常用模式 ===
beforeEach(() => {
  vi.useFakeTimers({ now: new Date('2025-01-01') })
})
afterEach(() => { vi.useRealTimers() })

it('advance timers', () => {
  const fn = vi.fn()
  setTimeout(fn, 1000)
  vi.advanceTimersByTime(1000)
  expect(fn).toHaveBeenCalledTimes(1)
})
```

---

### 4. Async Testing

```ts
// Vitest 原生支持 async/await，不需要外部 waitFor 库
it('async test', async () => {
  const data = await fetchData()
  expect(data).toBe('expected')
})

it('async with timeout', async () => {
  // ...
}, 10000) // 第三个参数为 timeout (ms)

// === vi.waitFor / vi.waitUntil (Vitest 1.x+) ===
// 内置的重试工具，类似 Testing Library 的 waitFor

function vi.waitFor<T>(
  callback: () => T | Promise<T>,
  options?: { timeout?: number; interval?: number }
): Promise<T>

function vi.waitUntil<T>(
  callback: () => T | Promise<T>,
  options?: { timeout?: number; interval?: number }
): Promise<T>

// 示例
it('wait for DOM update', async () => {
  const el = await vi.waitFor(
    () => document.querySelector('.loaded'),
    { timeout: 2000, interval: 100 }
  )
  expect(el).toBeTruthy()
})

// === Fake Timers + Async ===
// 使用 async 版推进方法处理链式 promise
it('fake timers with async', async () => {
  vi.useFakeTimers()
  const promise = someAsyncAction()
  await vi.advanceTimersByTimeAsync(1000)
  await expect(promise).resolves.toBe('done')
  vi.useRealTimers()
})
```

---

### 5. Inline Snapshot API

```ts
// === 标准快照 ===
function toMatchSnapshot(): void
function toMatchSnapshot(snapshotName?: string): void

// === 行内快照（写入测试文件自身） ===
function toMatchInlineSnapshot(): void
function toMatchInlineSnapshot(inlineSnapshot?: string): void

// === 错误快照 ===
function toThrowErrorMatchingSnapshot(): void
function toThrowErrorMatchingInlineSnapshot(): void
function toThrowErrorMatchingInlineSnapshot(inlineSnapshot?: string): void

// === 属性匹配器 ===
function toMatchSnapshot(options?: { propertyMatchers?: Record<string, any> }): void
function toMatchInlineSnapshot(
  properties?: Record<string, any>,
  inlineSnapshot?: string
): void

// 示例
it('inline snapshot', () => {
  const obj = { a: 1, b: 'hello', date: new Date() }

  // 标准快照（写入 __snapshots__/）
  expect(obj).toMatchSnapshot()

  // 行内快照（自动写入测试文件）
  expect(obj).toMatchInlineSnapshot()
  // 首次运行后变为：
  // expect(obj).toMatchInlineSnapshot(`
  //   {
  //     "a": 1,
  //     "b": "hello",
  //     "date": "2025-01-01T00:00:00.000Z"
  //   }
  // `)

  // 属性匹配器忽略动态值
  expect(obj).toMatchInlineSnapshot(
    { date: expect.any(Date) },
    `
    {
      "a": 1,
      "b": "hello",
      "date": Any<Date>
    }
    `
  )
})

// 更新：vitest --update 或 vitest -u

// 快照序列化
expect.addSnapshotSerializer({
  serialize: (val) => String(val),
  test: (val) => val instanceof SomeClass,
})
```

---

### 6. TypeScript Setup — 让 vi globals 工作

#### 方案 A：globals: true + vitest/globals

```ts
// vitest.config.ts
export default defineConfig({
  test: { globals: true },
})
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

`describe`, `it`, `expect`, `vi`, `beforeEach` 全局可用，无需 import。

#### 方案 B：显式 import

```ts
// 每个测试文件手动 import
import { describe, it, expect, vi, beforeEach } from 'vitest'
```

```json
{
  "compilerOptions": {
    "types": ["vitest"]
  }
}
```

#### 方案 C：三斜线指令

```ts
// 在 .d.ts 文件或测试文件顶部
/// <reference types="vitest/globals" />
```

#### React 项目完整 tsconfig：

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "types": ["vitest/globals"],
    "skipLibCheck": true
  },
  "include": ["src", "vite-env.d.ts"]
}
```

---

### 7. Workspace / Monorepo 支持

```ts
// vitest.workspace.ts
import { defineWorkspace } from 'vitest/config'

export default defineWorkspace([
  // 方式 1：项目路径（自动读取其 vitest/vite config）
  'packages/*',

  // 方式 2：内联配置
  {
    test: {
      name: 'unit',
      include: ['packages/*/src/**/*.test.ts'],
      environment: 'jsdom',
    },
  },

  // 方式 3：完整 Vite 配置
  {
    plugins: [react()],
    test: {
      name: 'browser-tests',
      browser: { enabled: true, provider: 'playwright' },
    },
  },
])
```

**关键特性：**
- 文件名：`vitest.workspace.ts` / `vitest.workspace.js` / `vitest.workspace.json`
- 各项目可独立配置 environment、setupFiles、plugins
- 通过 `test.name` 区分项目，CLI 分组显示
- 性能高（共享 vitest 实例）

---

### 8. Coverage Configuration

```ts
interface CoverageOptions {
  provider: 'v8' | 'istanbul'         // default: 'v8'（内置，更快）
  // 安装：npm i -D @vitest/coverage-v8 或 @vitest/coverage-istanbul

  enabled: boolean                     // default: false
  include: string[]
  exclude: string[]                    // default: ['coverage/**', 'dist/**', '**/*.d.ts', ...]
  all: boolean                         // 包含未触发的文件, default: false
  clean: boolean                       // 运行前清理, default: true
  cleanOnRerun: boolean                // default: true
  reportsDirectory: string             // default: './coverage'
  reporter: string | string[]           // default: ['text', 'html']
  reportOnFailure: boolean             // default: false
  extension: string[]                   // default: ['.js', '.cjs', '.mjs', '.ts', '.tsx', '.jsx', '.vue', '.svelte']

  thresholds: {
    perFile?: boolean                  // default: false
    autoUpdate?: boolean               // default: false
    100?: boolean
    statements?: number
    branches?: number
    functions?: number
    lines?: number
  }
}

// React 推荐配置
coverage: {
  provider: 'v8',
  reporter: ['text', 'html', 'lcov'],
  include: ['src/**/*.{ts,tsx}'],
  exclude: ['src/**/*.test.*', 'src/**/*.spec.*', 'src/test/**', 'src/vite-env.d.ts'],
  thresholds: { lines: 80, functions: 80, branches: 75, statements: 80 },
}
```

---

### 9. Environment Options

| 环境 | 用途 | 特点 | 安装 |
|------|------|------|------|
| `node` | Node.js | 默认, 无 DOM | 内置 |
| `jsdom` | 浏览器模拟 | 完整 DOM API，较慢 | `npm i -D jsdom` |
| `happy-dom` | 轻量浏览器 | 更快，部分 API 不完整 | `npm i -D happy-dom` |
| `edge-runtime` | Edge Workers | @edge-runtime/vm | `npm i -D @edge-runtime/vm` |

**按文件指定环境：**

```ts
// @vitest-environment jsdom
// @vitest-environment happy-dom
// 放在测试文件顶部注释

test('DOM interaction', () => {
  document.body.innerHTML = '<div>hello</div>'
  expect(document.querySelector('div')).toBeTruthy()
})
```

**自定义环境：**

```ts
import type { Environment } from 'vitest'

export default <Environment>{
  name: 'custom',
  transformMode: 'ssr',
  async setup(global, { options }) {
    global.__CUSTOM__ = true
    return { teardown(global) { delete global.__CUSTOM__ } }
  },
}
```

**React 测试推荐**：`jsdom`（兼容性好）或 `happy-dom`（速度优先）。

---

### 10. Key Differences from Jest

| 维度 | Jest | Vitest |
|------|------|--------|
| **性能** | 串行执行；每次需重启进程 | 智能并行 (worker_threads/child_process)；HMR watch；复用 Vite 缓存 |
| **配置** | `jest.config.ts` | `vitest.config.ts` 复用 Vite 配置 |
| **TypeScript** | 需 `ts-jest` + Babel | 原生支持（esbuild/swff）；`types: ["vitest/globals"]` |
| **Globals** | `jest.fn()` 默认可用 | 需 `globals: true`，然后 `vi.fn()` |
| **Mock 前缀** | `jest.mock/fn/spyOn` | `vi.mock/fn/spyOn` |
| **Mock hoisting** | `jest.mock()` 自动 | `vi.mock()` 自动 (相同行为) |
| **Fake Timers** | `jest.useFakeTimers()` | `vi.useFakeTimers()`，更多选项 (`shouldAdvanceTime`) |
| **Snapshot** | `toMatchInlineSnapshot()` | API 相同；Vitest 用 prettier 格式化 |
| **Watch 模式** | `jest --watch`（手动启动） | 默认 watch（非 CI） |
| **ESM** | 实验性 (`--experimental-vm-modules`) | 原生 ESM（Vite ESM-first） |
| **环境** | `@jest-environment jsdom` | `@vitest-environment jsdom` |
| **Browser 模式** | 需 `jest-puppeteer` | 内置 `@vitest/browser` |
| **UI 模式** | 无 | 内置 `vitest/ui` 图形界面 |
| **覆盖率** | `--coverage` (istanbul) | `coverage.provider: 'v8' \| 'istanbul'` 可选 |
| **transform** | `transform` 字段 | 继承 Vite plugins 体系 |
| **并行** | `--maxWorkers` | `pool: 'forks' \| 'threads'` 默认并行 |
| **Workspace** | `projects` 字段 | `vitest.workspace.ts` 独立文件 |
| **hoisted 辅助** | 无 | `vi.hoisted()` (v1.3+) |

#### 迁移对照表

```ts
// Jest → Vitest
jest.fn()              → vi.fn()
jest.mock()            → vi.mock()
jest.spyOn()           → vi.spyOn()
jest.useFakeTimers()   → vi.useFakeTimers()
jest.clearAllMocks()   → vi.clearAllMocks()
jest.resetAllMocks()   → vi.resetAllMocks()
jest.restoreAllMocks() → vi.restoreAllMocks()
jest.setTimeout()      → vi.setConfig({ testTimeout: 10000 })
jest.unmock()          → vi.unmock()
jest.requireActual()   → vi.importActual()   // ⚠️ 异步，返回 Promise
jest.requireMock()     → vi.importMock()     // ⚠️ 异步，返回 Promise
```

#### 关键注意事项

1. **`vi.importActual()` 是 async**：`jest.requireActual()` 是同步的。在 `vi.mock()` 工厂函数中使用时需要 `await`。

2. **`vi.mock()` 工厂函数内不能直接 `vi.fn()`**：需用 `vi.hoisted()`：

```ts
import { vi } from 'vitest'

const { mockedFn } = vi.hoisted(() => {
  return { mockedFn: vi.fn() }
})

vi.mock('./module', () => ({
  default: mockedFn,
}))
```

3. **Vitest watch 默认开启**（非 CI），Jest 需 `--watch`。

4. **需要 Vite 插件处理 JSX/TSX**：`@vitejs/plugin-react` 或等效插件。

5. **ESM 优先**：import 路径需完整后缀或配置 `resolve.extensions`。

6. **`expect.assertions()` 和 `expect.hasAssertions()`** 两者都支持。

7. **`it.each` / `describe.each`**：两者 API 一致。

---

> 注意：以上内容基于训练数据中的 Vitest 文档知识。由于 WebFetch、WebSearch、Bash 权限均被拒绝，无法实时验证最新文档。建议在权限恢复后对照 https://vitest.dev 检查版本差异。WebFetch 权限可通过 `.claude/settings.local.json` 中的 `permissions.allow` 授予，或由用户批准权限请求。

---

## React Testing Library 官方文档深度研究

> 来源: https://testing-library.com/docs/
> 文档版本: React Testing Library v14 / DOM Testing Library v9 / user-event v14
> 研究日期: 2026-05-22

---

### 1. Query 优先级 (Query Priority)

官方文档给出了明确的优先级层级，按可访问性从高到低排列。核心原则：**测试越接近用户与页面的交互方式，就越有可信度。**

#### 优先级层级（从高到低）:

| 优先级 | Query | 理由 |
|--------|-------|------|
| **1 (最高)** | `getByRole` | 最接近辅助技术的访问方式。用户通过语义角色（button, heading, link 等）与页面交互。**文档明确将其列为第一推荐**。支持 `name` 选项匹配无障碍标签（accessible name），这通常对应视觉标签文本。 |
| **2** | `getByLabelText` | 表单场景最优。用户通过 `<label>` 元素定位输入框，这与真实用户行为一致。`for`/`htmlFor`、`aria-labelledby`、`aria-label` 均支持。 |
| **3** | `getByPlaceholderText` | placeholder 是输入框的次要提示，不如 label 好。部分用户（尤其屏幕阅读器用户）依赖 label 而非 placeholder。**仅当 label 不可用时才回退至此**。 |
| **4** | `getByText` | 对非交互元素（div, span, p）最有用的查询。用户确实通过文本找内容。但对表单控件、按钮等交互元素，优先用 `getByRole`（更语义化）。 |
| **5** | `getByDisplayValue` | 在表单中按当前值查找输入框/选择框。适用于查找已填充的表单项或断言当前值。 |
| **6** | `getByAltText` | 仅适用于支持 `alt` 属性的元素（`<img>`, `<input>`, `<area>`, `<video>`）。用户通过 alt 文本理解图像内容。 |
| **7** | `getByTitle` | `title` 属性访问性差（屏幕阅读器支持不一致，多数浏览器将其作为 tooltip 显示）。**仅当没有其他查询可用时**才用。 |
| **8 (最低)** | `getByTestId` | 直接依赖 `data-testid` 属性。**这是最后手段**：绕过了用户可见的内容（text, label, role）。只在不适合用语义查询时使用（如非常动态的文本、非语义化组件）。 |

#### 补充规则:

- **语义角色是首选但不是万能**：当元素缺乏语义角色（如纯 `<div>`），或无法通过 `name` 选项区分多个同角色元素时，降级到更具体的查询。
- **特定性优先**：`getByRole('button', { name: /submit/i })` 比 `getByText(/submit/i)` 更好——前者同时验证了角色和标签。
- **`name` 选项**：`getByRole` 的 `name` 选项匹配的是计算后的 accessible name，不是简单的文本匹配。计算规则复杂（涉及 `aria-label`、`aria-labelledby`、内容文本的组合），但通常就是你期望的标签文本。

---

### 2. Query 变体 (getBy / queryBy / findBy / getAllBy / queryAllBy / findAllBy)

每个查询类型（ByRole, ByText 等）都有 5-6 种变体，对应不同的**元素存在性假设**和**是否异步**。

#### 变体总览:

| 变体 | 元素不存在时 | 找到 1+ 个时 | 找到 0 个时 | 异步? | 主要用途 |
|------|------------|------------|------------|-------|---------|
| `getBy*` | 断言元素存在 | 返回元素 | **抛出错误** | 否 | 元素**必须**存在（标准断言） |
| `queryBy*` | 不抛出 | 返回元素 | **返回 `null`** | 否 | 断言元素**不存在** |
| `findBy*` | 断言元素最终存在 | 返回 Promise<元素> | **抛出错误** | 是 | 等待元素出现（异步渲染） |
| `getAllBy*` | — | 返回数组 | **抛出错误** | 否 | 匹配多个元素且断言存在 |
| `queryAllBy*` | — | 返回数组 | **返回 `[]`** | 否 | 匹配多个元素，允许不存在 |
| `findAllBy*` | — | 返回 Promise<数组> | **抛出错误** | 是 | 等待多个异步元素 |

#### TypeScript 签名（以 `ByRole` 为例，其他类似）:

```typescript
// DOM Testing Library 中的泛型签名
getByRole<K extends ElementType>(
  container: HTMLElement,
  role: ARIARole | string,
  options?: ByRoleOptions
): HTMLElementTagNameMap[K]

queryByRole<K extends ElementType>(
  container: HTMLElement,
  role: ARIARole | string,
  options?: ByRoleOptions
): HTMLElementTagNameMap[K] | null

findByRole<K extends ElementType>(
  container: HTMLElement,
  role: ARIARole | string,
  options?: ByRoleOptions & { timeout?: number; interval?: number }
): Promise<HTMLElementTagNameMap[K]>

getAllByRole<K extends ElementType>(
  container: HTMLElement,
  role: ARIARole | string,
  options?: ByRoleOptions
): HTMLElementTagNameMap[K][]

queryAllByRole<K extends ElementType>(
  container: HTMLElement,
  role: ARIARole | string,
  options?: ByRoleOptions
): HTMLElementTagNameMap[K][]

findAllByRole<K extends ElementType>(
  container: HTMLElement,
  role: ARIARole | string,
  options?: ByRoleOptions & { timeout?: number; interval?: number }
): Promise<HTMLElementTagNameMap[K][]>
```

#### 何时用哪个:

| 场景 | 正确变体 |
|------|---------|
| 元素应该存在 | `getBy*` |
| 元素应该不存在 | `queryBy*` |
| 异步出现（数据加载后） | `findBy*`（= `waitFor` + `getBy*` 的语法糖） |
| 匹配多个元素 | `getAllBy*` |
| 检查多个元素中不存在某个 | `queryAllBy*` |
| 等待多个异步元素 | `findAllBy*` |

**重要规则**:

- `getBy*` 找不到元素时**立即抛出**，无需 `waitFor` 包装
- `findBy*` 内部已使用 `waitFor`，返回值是 Promise，**必须 `await`**
- `queryBy*` 返回 `null` 是测试元素不存在的最直接方式：`expect(screen.queryByRole('alert')).not.toBeInTheDocument()`
- 不要在 `waitFor` 回调内部使用 `findBy*`（这会导致不必要的 `waitFor` 嵌套）

---

### 3. `render()` 完整签名

```typescript
// 来自 @testing-library/react
import { RenderOptions, RenderResult } from '@testing-library/react'

function render(
  ui: React.ReactElement,
  options?: RenderOptions
): RenderResult
```

#### `RenderOptions`:

```typescript
interface RenderOptions {
  // 包裹组件的 wrapper 组件（通常用于提供 Provider）
  wrapper?: React.ComponentType<{ children: React.ReactNode }>

  // 自定义 query 实现，覆盖默认的 DOM Testing Library queries
  queries?: Queries

  // 是否启用 hydrate（SSR 场景）
  // 如果为 true，使用 ReactDOM.hydrate() 而非 ReactDOM.createRoot().render()
  hydrate?: boolean

  // 挂载组件的根元素（默认是 document.body）
  // 设置 baseElement 也会影响 container（container 会被插入 baseElement 内）
  baseElement?: HTMLElement

  // 渲染容器（默认创建 <div> 追加到 baseElement）
  // 如果手动指定 container，baseElement 应相应设置
  container?: HTMLElement

  // React 18 legacy root（当需要兼容 React 18 alpha/beta 时使用）
  legacyRoot?: boolean
}
```

#### `RenderResult`:

```typescript
interface RenderResult {
  // 渲染内容的容器（默认是创建的 <div>）
  container: HTMLElement

  // baseElement（默认是 document.body）
  baseElement: HTMLElement

  // 将组件渲染的 DOM 输出为字符串并打印到控制台
  debug: (
    element?: HTMLElement | HTMLElement[],
    maxLength?: number,
    options?: { prettyFormat?: boolean }
  ) => void

  // 将渲染结果序列化为 HTML 片段（常用于 snapshot）
  asFragment(): DocumentFragment

  // 重新渲染组件（可传入新的 props）
  rerender(ui: React.ReactElement): void

  // 卸载组件（清理副作用）
  unmount(): void

  // 绑定了容器的所有 DOM Testing Library query 函数
  ...boundQueryFunctions: BoundFunctions<Queries>
}
```

#### 使用示例:

```typescript
// 基本用法
const { container, debug, asFragment, rerender, unmount } = render(<MyComponent />)

// 带 wrapper（Provider 模式）
function renderWithProviders(ui: React.ReactElement) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <ThemeProvider theme="dark">
        <UserProvider>{children}</UserProvider>
      </ThemeProvider>
    )
  }
  return render(ui, { wrapper: Wrapper })
}

// 重渲染（测试 props 变化）
const { rerender } = render(<Counter count={0} />)
rerender(<Counter count={1} />)

// 自定义 container（测试 portal 场景）
const baseElement = document.createElement('div')
document.body.appendChild(baseElement)
render(<Modal />, { baseElement, container: baseElement })
```

---

### 4. `screen` 对象

`scren` 是 RTL 提供的便捷对象，自动暴露绑定到 `document.body` 的所有 query 函数。

```typescript
// 导入方式
import { screen } from '@testing-library/react'

// screen 的类型定义（等价于自动调用 getQueriesForElement(document.body)）
interface Screen extends Queries {
  // 所有 DOM Testing Library query 函数
  getByRole: BoundFunction<GetByRole>
  getByLabelText: BoundFunction<GetByLabelText>
  getByPlaceholderText: BoundFunction<GetByPlaceholderText>
  getByText: BoundFunction<GetByText>
  getByDisplayValue: BoundFunction<GetByDisplayValue>
  getByAltText: BoundFunction<GetByAltText>
  getByTitle: BoundFunction<GetByTitle>
  getByTestId: BoundFunction<GetByTestId>
  queryByRole: BoundFunction<QueryByRole>
  /* ... 以此类推 queryBy*、findBy*、getAllBy*、queryAllBy*、findAllBy* ... */
  debug: (element?: HTMLElement | HTMLElement[], maxLength?: number) => void
  logTestingPlaygroundURL: () => void
}
```

#### 为什么用 `screen` 而不是解构？

**这是官方推荐做法**，理由：

- 不需要在 `render()` 后手动解构 query 函数
- 不需要维护 `container` 引用
- 代码更清晰：`screen.getByRole('button')` 比 `const { getByRole } = render(<Cmp />)` 更明确查询的是全局 DOM

```typescript
// ❌ 不推荐：解构 query 函数
const { getByRole } = render(<MyComponent />)
expect(getByRole('button')).toBeInTheDocument()

// ✅ 推荐：使用 screen 对象
render(<MyComponent />)
expect(screen.getByRole('button')).toBeInTheDocument()
```

#### `screen.logTestingPlaygroundURL()`:

v14+ 新增。在测试运行时调用会在控制台输出一个 Testing Playground URL，可以直接在浏览器中查看当前 DOM 结构并进行查询调试。

---

### 5. `within()` 函数

`within()` 将 query 函数绑定到特定 DOM 子树而不是整个 `document.body`。

```typescript
// TypeScript 签名
import { within, BoundFunctions, Queries } from '@testing-library/react'

// 标准签名
function within<T extends Element>(
  element: T
): BoundFunctions<Queries>

// 自定义 query 重载
function within<T extends Element, Q extends Queries>(
  element: T,
  queries?: Q
): BoundFunctions<Q>
```

#### 使用场景:

```typescript
// 场景 1：在特定元素内查询
const form = screen.getByRole('form')
const nameInput = within(form).getByLabelText(/name/i)
const emailInput = within(form).getByLabelText(/email/i)

// 场景 2：在 dialog/modal 内查询
fireEvent.click(screen.getByRole('button', { name: /open modal/i }))
const dialog = screen.getByRole('dialog')
within(dialog).getByRole('button', { name: /confirm/i })

// 场景 3：表格行内查询
const rows = screen.getAllByRole('row')
within(rows[0]).getByRole('cell', { name: /product name/i })

// 场景 4：与 container 配合
const { container } = render(<MyComponent />)
within(container).getByText(/some text/i)
```

#### 注意点:

- `within()` 不会改变 `screen` 的绑定——screen 始终指向 `document.body`
- `within()` 返回的对象拥有所有 query 变体（getBy*, queryBy*, findBy* 等）
- 嵌套使用完全合法：`within(within(dialog).getByRole('group')).getByLabelText(...)`

---

### 6. `waitFor` 和 `waitForElementToBeRemoved`

#### `waitFor`:

```typescript
// TypeScript 签名
import { waitFor } from '@testing-library/react'

function waitFor<T>(
  callback: () => T | Promise<T>,
  options?: WaitForOptions
): Promise<T>

interface WaitForOptions {
  // 超时时间（毫秒），默认 1000ms
  timeout?: number

  // 轮询间隔（毫秒），默认 50ms
  interval?: number

  // 如果 callback 抛出该错误实例，waitFor 不会失败
  onTimeout?: (error: Error) => Error
}
```

#### `waitFor` 使用模式:

```typescript
// 模式 1：等待元素出现（等价于 findByRole）
await waitFor(() => {
  expect(screen.getByRole('alert')).toBeInTheDocument()
})

// 模式 2：等待值变化
await waitFor(() => {
  expect(screen.getByRole('spinbutton')).toHaveValue(42)
})

// 模式 3：等待异步副作用完成
await waitFor(() => {
  expect(mockCallback).toHaveBeenCalledTimes(3)
})

// 模式 4：自定义超时和间隔
await waitFor(
  () => expect(screen.getByText(/loaded/i)).toBeInTheDocument(),
  { timeout: 5000, interval: 200 }
)

// 模式 5：直接返回 promise
const button = await waitFor(() => {
  const btn = screen.getByRole('button')
  if (!btn.disabled) return btn
  throw new Error('button still disabled')
})
```

#### `waitFor` 的 gotchas:

1. **不要嵌套 `findBy*` 在 `waitFor` 内**：`findBy*` 已经是 `waitFor` + `getBy*` 的包装，嵌套会导致双重超时。
2. **`waitFor` 回调内尽量不用 `findBy*`**：如果回调内唯一需要等待的东西就是元素出现，直接用 `findBy*`。
3. **回调内的断言或副作用最多执行一次**：回调会被反复调用直到断言通过或超时。因此回调应该**幂等**。不要在回调内做 `fireEvent` 或 `userEvent.click`——这可能导致多次触发。
4. **严格模式双重触发**：在 React StrictMode + development 模式下，回调可能在每个 tick 被调用两次。

```typescript
// ❌ 错误：回调内的副作用会多次执行
await waitFor(() => {
  fireEvent.click(screen.getByText(/retry/i))  // 可能被多次点击！
  expect(screen.getByRole('alert')).toBeInTheDocument()
})

// ✅ 正确：在 waitFor 外部触发交互，waitFor 内只做断言
fireEvent.click(screen.getByText(/retry/i))
await waitFor(() => {
  expect(screen.getByRole('alert')).toBeInTheDocument()
})
```

#### `waitForElementToBeRemoved`:

```typescript
// TypeScript 签名
import { waitForElementToBeRemoved } from '@testing-library/react'

function waitForElementToBeRemoved<T>(
  // 接受元素、元素数组，或返回元素/元素数组的 callback
  callback: (() => T) | T,
  options?: WaitForElementToBeRemovedOptions
): Promise<void>

interface WaitForElementToBeRemovedOptions {
  // 超时时间，默认 4500ms（比 waitFor 的默认值大）
  timeout?: number

  // 轮询间隔，默认 50ms
  interval?: number

  // 容器元素（默认 document）
  container?: HTMLElement
}
```

#### 使用示例:

```typescript
// 模式 1：直接传入元素
const button = screen.getByRole('button', { name: /delete/i })
fireEvent.click(button)
await waitForElementToBeRemoved(button)

// 模式 2：传入 callback
await waitForElementToBeRemoved(() => screen.queryByRole('alert'))

// 模式 3：等待多个元素移除
const items = screen.getAllByRole('listitem')
fireEvent.click(screen.getByRole('button', { name: /clear all/i }))
await waitForElementToBeRemoved(items)

// 模式 4：自定义超时
await waitForElementToBeRemoved(
  () => screen.queryByText(/loading/i),
  { timeout: 3000 }
)
```

#### `waitForElementToBeRemoved` 的 gotchas:

1. **callback 内用 `queryBy*` 而非 `getBy*`**：元素被移除后 `getBy*` 会抛出错误，这与 `waitForElementToBeRemoved` 内部的重试逻辑冲突。
2. **超时默认值 4500ms**：比 `waitFor` 的 1000ms 大得多，因为元素移除通常涉及动画或过渡。
3. **如果传入的元素已经在 DOM 中不存在，Promise 会立即 reject**："The element(s) given to waitForElementToBeRemoved are already removed"。

---

### 7. `act()` 函数

`act()` 来自 `react-dom/test-utils`，RTL 将其重新导出。

```typescript
// 来自 @testing-library/react
import { act } from '@testing-library/react'

// 签名
function act(callback: () => void | Promise<void>): void
```

#### 核心规则:

**在 RTL 中，99% 的情况下你不需要手动调用 `act()`。**

理由:
- `render()`、`userEvent`、`fireEvent`、`waitFor`、`findBy*` 都已自动用 `act()` 包裹
- RTL 的设计目标之一就是让开发者无需操心 `act()`

#### 何时需要手动 `act()`:

```typescript
// 场景 1：测试依赖于 timeout 的副作用
jest.useFakeTimers()
act(() => {
  jest.advanceTimersByTime(5000)
})

// 场景 2：手动 dispatch 自定义 DOM 事件
const element = screen.getByRole('button')
act(() => {
  element.dispatchEvent(new CustomEvent('my-event', { detail: { foo: 'bar' } }))
})

// 场景 3：混用非 RTL 的 React 渲染
act(() => {
  ReactDOM.render(<Component />, container)
})
ReactDOM.unmountComponentAtNode(container)
```

#### `act()` 警告常见原因:

如果你的测试正确使用了 RTL API 但仍然看到 `act()` 警告，说明有**异步副作用未被 RTL 捕获**。常见原因包括:

1. **未清理的定时器**：组件内 `setTimeout`/`setInterval` 在测试结束时仍 pending
2. **未处理的 Promise**：组件内 `fetch`/`axios` 请求没有在 `afterEach` 中清理
3. **未等待的动画帧**：`requestAnimationFrame` 没有 mock 或 flush
4. **外部状态更新**：组件依赖外部状态管理器（Redux/Zustand），更新发生在测试作用域外

```typescript
// 修复方案
afterEach(async () => {
  // 等待所有 pending 的 act() 完成
  await act(async () => {})
  // 或使用 flushMicrotasks
})
```

#### 关于 `act()` 的正确理解:

- **不是 RTL 的设计缺陷**：`act()` 警告是 React 内部的检测机制，RTL 已经做了大量工作来将其隐藏
- **看到警告说明有真正的 bug 或未处理的异步操作**：不应该通过 `act()` 包装来压制警告，而应该找出未处理异步的根源
- **React 18 的 `act()` 行为变化**：React 18 的 `act()` 更加严格，会捕获更多未包裹的更新

---

### 8. `userEvent.setup()` — v14 API

`@testing-library/user-event` v14 引入了新的 `setup()` API，替代了 v13 的直接调用模式。

```typescript
// 导入方式
import userEvent from '@testing-library/user-event'

// setup 函数签名
function setup(options?: UserEventOptions): UserEventInstance

// 或直接从默认导出调用
const user = userEvent.setup(options?)
```

#### `UserEventOptions`:

```typescript
interface UserEventOptions {
  // 所有 APIs 的默认延迟（毫秒），默认值因 API 而异
  delay?: number

  // 是否在触发事件时使用 document.activeElement（默认 true）
  advanceTimers?: (delay: number) => void

  // 键盘状态映射（用于复杂键盘交互）
  keyboardMap?: KeyboardKeyOptions[]

  // 跳过某些可访问性检查（如 pointer 检查）
  skipAccessibilityCheck?: boolean

  // 自定义事件构造（用于环境特定的 DOM 实现）
  document?: Document

  // 当点击 disabled 元素时的行为（默认 'error'）
  // 'error': 抛出错误 | 'skip': 跳过 | 'ignore': 静默执行
  onDisabledClick?: 'error' | 'skip' | 'ignore'

  // 在 API 调用前后是否自动用 act() 包裹（默认 true）
  applyAccept?: boolean

  // 写操作时的延迟分布
  delayDistribution?: 'default' | 'uniform' | 'normal' | ((step: number, totalSteps: number) => number)
}
```

#### `UserEventInstance` 所有方法签名:

```typescript
interface UserEventInstance {
  // ===== 指针操作 =====

  // 点击元素（触发完整事件链：pointerdown → mousedown → pointerup → mouseup → click）
  click(target: Element, options?: PointerOptions): Promise<void>

  // 双击
  dblClick(target: Element, options?: PointerOptions): Promise<void>

  // 三击
  tripleClick(target: Element, options?: PointerOptions): Promise<void>

  // 在目标上按下指针（不释放）
  pointerDown(target: Element, options?: PointerOptions): Promise<void>

  // 释放指针
  pointerUp(target: Element, options?: PointerOptions): Promise<void>

  // 完整指针事件（down + move + up）
  pointer(target: Element | PointerTarget[], options?: PointerInput): Promise<void>

  // ===== 键盘操作 =====

  // 在聚焦元素上输入字符串（触发 focus → keydown → keypress → input → keyup 每个字符）
  type(
    target: Element,
    text: string,
    options?: TypeOptions
  ): Promise<void>

  // 清除输入框内容（触发 focus → select → delete 完整事件序列）
  clear(target: Element): Promise<void>

  // 高级键盘输入（支持修饰键和特殊键，如 '{Enter}', '{Shift>}A{/Shift}'）
  keyboard(text: string | KeyboardInput[], options?: KeyboardOptions): Promise<void>

  // ===== 表单操作 =====

  // Tab 键导航（默认在可聚焦元素间前进）
  tab(options?: TabOptions): Promise<void>

  // 选择 <select> 中的选项
  selectOptions(
    target: Element,
    values: HTMLElement | HTMLElement[] | string | string[],
    options?: PointerOptions
  ): Promise<void>

  // 取消选择 <select> 中的选项
  deselectOptions(
    target: Element,
    values: HTMLElement | HTMLElement[] | string | string[],
    options?: PointerOptions
  ): Promise<void>

  // 上传文件
  upload(
    target: Element,
    files: File | File[],
    options?: PointerOptions
  ): Promise<void>

  // ===== 悬停操作 =====

  // 悬停在元素上
  hover(target: Element, options?: PointerOptions): Promise<void>

  // 取消悬停
  unhover(target: Element, options?: PointerOptions): Promise<void>

  // ===== 剪贴板操作 =====

  // 复制选中文本到剪贴板
  copy(target?: Element): Promise<void>

  // 从剪贴板粘贴文本到聚焦元素
  paste(target?: Element): Promise<void>

  // 剪切选中文本到剪贴板
  cut(target?: Element): Promise<void>
}
```

#### 选项类型:

```typescript
interface PointerOptions {
  pointerState?: PointerState
  keyboardState?: KeyboardState
  touch?: boolean
}

interface TypeOptions {
  delay?: number
  skipAccessibilityCheck?: boolean
  initialSelectionStart?: number
  initialSelectionEnd?: number
}

interface TabOptions {
  // 反向 Tab（Shift+Tab）
  shift?: boolean
}
```

#### 标准使用模式:

```typescript
// ✅ 推荐：setup 模式（v14 标准）
const user = userEvent.setup()
await user.click(screen.getByRole('button'))
await user.type(screen.getByRole('textbox'), 'hello world')
await user.keyboard('{Enter}')

// 带选项的 setup
const user = userEvent.setup({ delay: 100 })
await user.type(screen.getByRole('textbox'), 'slow typing')

// Tab 导航
await user.tab()
await user.tab({ shift: true })

// 文件上传
const file = new File(['content'], 'test.txt', { type: 'text/plain' })
await user.upload(screen.getByLabelText(/upload/i), file)
```

---

### 9. userEvent v14 vs v13 差异

| 特性 | v13 | v14 |
|------|-----|-----|
| **API 风格** | 直接函数调用：`userEvent.click(el)` | `setup()` 返回实例：`user = userEvent.setup(); user.click(el)` |
| **返回值** | `Promise<void>` 但可以不 await | **必须 await**（所有方法返回 Promise） |
| **默认事件模型** | 直接 dispatchEvent | **完整事件模拟**（mousedown → mousemove → mouseup → click 等完整事件链） |
| **`type()` 默认行为** | 立即输入所有字符 | 逐字符输入（更接近真实用户行为） |
| **`delay` 支持** | 仅在 `type()` 中支持 | 全局 setup 选项 + 每个方法独立选项 |
| **`keyboard()`** | 无独立 API | 新增 `keyboard()` 支持修饰键组合、特殊键 |
| **`clear()`** | 直接设置值为空 | 触发 focus → select → delete 完整事件序列 |
| **`tab()`** | 无独立 API | 新增 `tab()` 支持 Tab 导航模拟 |
| **`hover()/unhover()`** | 存在 | 行为更准确（触发 pointerover/pointerenter/pointerout/pointerleave） |
| **`upload()`** | 存在 | 支持多文件 |
| **`copy()/cut()/paste()`** | 无 | 新增剪贴板事件 |
| **`selectOptions()`** | 存在 | 触发完整事件序列（mousedown, mouseup, click, input, change） |
| **可访问性检查** | 无 | 默认检查可访问性（如点击 disabled 元素会报错） |
| **`pointer()` API** | 无 | 新增完整指针事件控制 |
| **`dblClick()`** | 存在 | 触发完整的事件序列（mousedown*2, mouseup*2, click*2, dblclick） |
| **StrictMode** | 可能产生警告 | 完全兼容 |

#### 迁移指南（v13 → v14）:

```typescript
// v13（旧 API）
import userEvent from '@testing-library/user-event'
userEvent.click(screen.getByRole('button'))
userEvent.type(screen.getByRole('textbox'), 'hi')

// v14（新 API）
import userEvent from '@testing-library/user-event'
const user = userEvent.setup()
await user.click(screen.getByRole('button'))
await user.type(screen.getByRole('textbox'), 'hi')
```

#### v14 事件模拟的精确度:

v14 不再简单地调用 `element.dispatchEvent()`，而是精确模拟浏览器事件序列：

```typescript
// 一次 click 调用在 v14 中实际触发的事件序列：
// pointerover → mouseover → pointerenter → mouseenter
// → pointerdown → mousedown
// → pointerup → mouseup → click

// 一次 type 调用在 v14 中：
// focus → focusin → keydown → keypress → input → keyup → keydown → ...
// 每个字符都是独立的 keydown → keypress → input → keyup 序列
```

---

### 10. TypeScript 类型辅助

React Testing Library 暴露了多组 TypeScript 类型用于精确的类型约束。

```typescript
// ===== 来自 @testing-library/dom 的核心类型 =====

// Matcher: 可以接受字符串、正则、或返回 boolean 的函数
type Matcher = string | RegExp | ((content: string, element: Element | null) => boolean)

// ByRole 专用的 Matcher（匹配 accessible name）
type ByRoleMatcher = string | RegExp | ((accessibleName: string, element: Element) => boolean)

// NormalizerOptions: 文本规范化控制
interface NormalizerOptions {
  trim?: boolean
  collapseWhitespace?: boolean
}

// MatcherOptions: 大多数 query 的通用选项
interface MatcherOptions {
  // 精确匹配（默认 false，即 substring 匹配）
  exact?: boolean

  // 自定义文本规范化函数（覆盖默认的 trim+collapseWhitespace）
  normalizer?: (text: string) => string
}

// ByRoleOptions: getByRole 专用的选项
interface ByRoleOptions extends MatcherOptions {
  name?: ByRoleMatcher
  description?: ByRoleMatcher
  hidden?: boolean
  selected?: boolean
  checked?: boolean
  pressed?: boolean
  expanded?: boolean
  level?: number
  current?: boolean | string
  queryFallbacks?: boolean
  suggest?: boolean
}

// LabelTextOptions: getByLabelText 选项
interface LabelTextOptions extends MatcherOptions {
  selector?: string
}

// TextMatchOptions: getByText 选项
interface TextMatchOptions extends MatcherOptions {
  ignore?: string | boolean
  selector?: string
}

// ByTestIdOptions: getByTestId 选项
interface ByTestIdOptions extends MatcherOptions {
  allowMultiple?: boolean
}

// WaitForOptions
interface WaitForOptions {
  timeout?: number
  interval?: number
  onTimeout?: (error: Error) => Error
}

// ===== RenderOptions（来自 @testing-library/react） =====
interface RenderOptions {
  wrapper?: React.ComponentType<{ children: React.ReactNode }>
  queries?: Queries
  hydrate?: boolean
  container?: HTMLElement
  baseElement?: HTMLElement
  legacyRoot?: boolean
}

// ===== Queries 泛型类型 =====

// Query 函数的类型绑定
type BoundFunction<T> = T extends (
  element: HTMLElement,
  ...args: infer P
) => infer R
  ? (...args: P) => R
  : never

// Queries 映射类型
interface Queries {
  [key: string]: (container: HTMLElement, ...args: any[]) => any
}

// BoundFunctions: 将 query 函数绑定到具体容器
type BoundFunctions<T extends Queries> = {
  [K in keyof T]: BoundFunction<T[K]>
}

// ===== 导出路径 =====
// DOM Testing Library 核心类型（所有框架共享）
import {
  Matcher,
  ByRoleMatcher,
  MatcherOptions,
  ByRoleOptions,
  NormalizerOptions,
  WaitForOptions,
  waitFor,
  waitForElementToBeRemoved,
  within,
  getQueriesForElement,
} from '@testing-library/dom'

// React Testing Library 扩展类型
import {
  RenderOptions,
  RenderResult,
  render,
  screen,
  cleanup,
  act,
} from '@testing-library/react'
```

---

### 11. 官方文档指出的常见 Antipatterns

#### Antipattern 1: 使用 `container.querySelector` 代替语义查询

```typescript
// ❌ 反模式：直接操作 DOM
const { container } = render(<MyComponent />)
const button = container.querySelector('.btn-primary')

// ✅ 正确：使用语义查询
render(<MyComponent />)
expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
```

**理由**：`querySelector` 依赖 CSS 类名或标签名实现细节。改变类名或重构 DOM 结构会导致测试失败，但功能没有变化。

#### Antipattern 2: 使用 `fireEvent` 代替 `userEvent`

```typescript
// ❌ 反模式：fireEvent 只触发单一事件
fireEvent.click(button)
fireEvent.change(input, { target: { value: 'test' } })

// ✅ 正确：userEvent 触发完整事件链
const user = userEvent.setup()
await user.click(button)
await user.type(input, 'test')
```

**理由**：`fireEvent` 只触发指定的事件类型，不会触发浏览器真实交互中的完整事件序列。

#### Antipattern 3: 将测试覆盖实现细节

```typescript
// ❌ 反模式：测试 props 变更而非用户行为
render(<Counter initialCount={5} />)
expect(screen.getByText('5')).toBeInTheDocument()
const { rerender } = render(<Counter initialCount={10} />)
expect(screen.getByText('10')).toBeInTheDocument()

// ✅ 正确：测试用户行为
render(<Counter initialCount={5} />)
expect(screen.getByText('5')).toBeInTheDocument()
const user = userEvent.setup()
await user.click(screen.getByRole('button', { name: /increment/i }))
expect(screen.getByText('6')).toBeInTheDocument()
```

**理由**：测试组件通过 rerender 接收新 props 测试的是框架机制，而非业务逻辑。

#### Antipattern 4: 不必要地包裹 `act()`

```typescript
// ❌ 反模式：手动包裹 act
import { act } from '@testing-library/react'
await act(async () => { render(<MyComponent />) })

// ✅ 正确：RTL 已自动 act 包裹
render(<MyComponent />)
```

**理由**：`render()` 和 `userEvent` 方法已经在内部用 `act()` 包裹。

#### Antipattern 5: 直接使用 `getByRole` 不传 `name` 选项

```typescript
// ❌ 反模式：不传 name（可能匹配多个）
const buttons = screen.getAllByRole('button')

// ✅ 正确：通过 name 精确定位
screen.getByRole('button', { name: /submit order/i })
```

**理由**：页面中通常有多个同角色元素。`name` 选项同时验证了可访问性和文本正确性。

#### Antipattern 6: 在 `waitFor` 内部使用 `findBy*`

```typescript
// ❌ 反模式：waitFor 嵌套 findBy
await waitFor(async () => {
  const alert = await screen.findByRole('alert')  // 双重等待
})

// ✅ 正确：二选一
await screen.findByRole('alert')
// 或
await waitFor(() => {
  expect(screen.getByRole('alert')).toBeInTheDocument()
})
```

**理由**：`findBy*` 内部已调用 `waitFor`，嵌套会导致额外开销。

#### Antipattern 7: 对 `queryBy*` 用 `toBeInTheDocument`

```typescript
// ❌ queryBy 返回 null 时 toBeInTheDocument 会抛错
expect(screen.queryByText(/not found/i)).toBeInTheDocument()

// ✅ 正确
expect(screen.queryByText(/not found/i)).not.toBeInTheDocument()
```

#### Antipattern 8: 在测试间共享状态

```typescript
// ❌ 反模式：全局变量在测试间共享
let counter = 0
beforeEach(() => { counter++ })

// ✅ 正确：每个测试独立的设置
beforeEach(() => { counter = 0 })
```

**理由**：测试应该完全独立。`cleanup()` 自动卸载组件，但应用级别状态需手动重置。

#### Antipattern 9: 使用 `waitFor` 等待不需要异步的操作

```typescript
// ❌ 错误：同步渲染无需 await
render(<StaticComponent />)
await waitFor(() => {
  expect(screen.getByText('Hello')).toBeInTheDocument()
})

// ✅ 正确
render(<StaticComponent />)
expect(screen.getByText('Hello')).toBeInTheDocument()
```

#### Antipattern 10: 跳过 userEvent 的 `await`

```typescript
// ❌ 反模式：未 await 的 userEvent
const user = userEvent.setup()
user.click(button)  // Promise 未 resolve

// ✅ 正确：await 所有 userEvent 操作
const user = userEvent.setup()
await user.click(button)
```

**理由**：v14 的所有方法都返回 Promise。不 await 会导致事件序列未完成就执行断言。

---

### 12. Cleanup 行为

#### 自动 Cleanup（推荐方式）：

从 RTL v14 + @testing-library/react v14 开始，当检测到测试框架（Jest / Vitest）时，`afterEach` 自动注册 cleanup。

```typescript
// 自动注册。如果不想自动 cleanup，导入：
// import '@testing-library/react/dont-cleanup-after-each'
```

**自动 cleanup 的检测机制**：

- 通过 `afterEach` 全局函数检测测试框架
- 如果在 Node.js 环境且 `afterEach` 可用，自动注册 cleanup
- 如果使用 Vitest，默认支持自动 cleanup

#### 手动 Cleanup:

```typescript
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
  // cleanup 执行的内容：
  // 1. 卸载所有通过 render() 挂载的 React 组件
  // 2. 从 container 中移除渲染出的 DOM 节点
  // 3. 重置内部状态，使下一个 render() 创建新的容器
})
```

#### Cleanup 内部逻辑（伪代码）:

```typescript
function cleanup(): void {
  const mountedContainers = getMountedContainers()
  mountedContainers.forEach(({ container, root }) => {
    root.unmount()    // React 18
    // 或 ReactDOM.unmountComponentAtNode(container)  // React 17 及以下
    if (container !== baseElement) {
      container.parentNode?.removeChild(container)
    }
  })
  clearMountedContainers()
}
```

#### Cleanup 不会做的事情:

- **不会清除 DOM 之外的全局状态**：如 Redux store、localStorage、sessionStorage
- **不会清除定时器**：已启动的 `setTimeout`/`setInterval` 会继续存在
- **不会重置 JSDOM**：`document.body.innerHTML` 虽被清理，但 JSDOM 实例未重置

```typescript
// 正确的 afterEach 应当包含：
afterEach(() => {
  cleanup()                           // RTL cleanup（自动）
  vi.clearAllMocks()                  // 清除 mock 记录
  localStorage.clear()                // 清除 localStorage
  sessionStorage.clear()              // 清除 sessionStorage
})
```

#### Vitest 兼容性:

```typescript
// vitest.config.ts 中启用 globals 即可让 RTL 自动注册 cleanup
// vitest.setup.ts
import '@testing-library/react'
// 无需手动调用 cleanup，RTL 会检测 vitest 的 afterEach 并自动注册
```

---

### 附: 官方文档推荐的最佳实践总结

1. **优先 `screen`**：比解构更简洁，不需要维护 container 引用
2. **优先用户行为查询**：getByRole > getByLabelText > getByText > getByTestId
3. **userEvent 代替 fireEvent**：v14 的事件模拟更接近真实浏览器
4. **避免测试实现细节**：不直接测 state，不测私有方法，不测 CSS 类名
5. **每个测试一个行为**：一个 `it`/`test` 测一个用户交互路径
6. **测试可访问性**：`getByRole` 的 `name` 选项同时也验证了 a11y
7. **通过 `findBy*` 处理异步**：比 `waitFor` + `getBy*` 更简洁
8. **不包裹多余的 `act()`**：RTL 已自动处理
9. **`afterEach` 处理全局状态**：cleanup 之外的 localStorage、mock 需手动清理

---

## 补充研究：MSW 三层架构与 Handler 优先级 (2026-05-22)

> 来源: MSW 官方文档 "Network behavior overrides" + GitHub issues

### MSW 请求拦截的三层模型

```
请求进入
  └→ Layer 1: Runtime handlers (server.use)      ← 最高优先级，per-test 覆盖
     └→ Layer 2: Initial handlers (setupServer)   ← 默认行为，共享 baseline
        └→ Layer 3: Real network                   ← 无 handler 匹配时放行
```

**关键行为**：`server.use()` **prepend**（前插）而非 append。后添加的 handler 先匹配。

### Handler 生命周期

| 方法 | 效果 |
|------|------|
| `server.use(h)` | Prepend runtime handler（临时覆盖） |
| `server.resetHandlers()` | 移除所有 runtime handlers，保留 initial |
| `server.resetHandlers([...new])` | 替换 initial handlers（清除一切） |
| `server.restoreHandlers()` | 重新激活已耗尽的 one-time handlers |

### { once: true } 选项

```typescript
server.use(
  http.get('/api/resource', handler, { once: true })
)
// Handler 在匹配一次请求后自动移除，后续请求 fall through
```

### 关键注意事项

1. **不要用 `vi.fn()` 替代 `globalThis.fetch`**：这会破坏 MSW 的拦截链路。MSW 依赖原生 fetch 实现。如需 spy fetch，用 `vi.spyOn(globalThis, 'fetch')`
2. **`server.use()` 不是替换而是前插**：如果有多个 `use()` 调用，它们按调用顺序的后进先出（LIFO）匹配
3. **`resetHandlers()` 在 `afterEach` 是必须的**：否则 per-test 的 runtime handler 会泄漏到后续测试

---

## 补充研究：React 并发模式 + act() 警告 (2026-05-22)

> 来源: vitest #7196, testing-library/react #1413, StackOverflow, vitest-browser-react #9

### 已知问题

1. **Suspense + act() 不兼容** (vitest-browser-react #9)：React 19 `use()` hook 在 Suspense 内部的 Promise 在同步 `act()` 中无法 resolve，需要 async `act()` 和 async `render()`
2. **假定时器 + act() 警告** (vitest #7196)：使用 `vi.useFakeTimers()` + `vi.runAllTimersAsync()` 测试轮询组件时，即使 UI 更新正确，仍可能产生 "not wrapped in act()" 警告。修复：将 `vi.advanceTimersByTime()` 包裹在 `act()` 中
3. **RTL + Vitest 配置警告** (#1413)：截至 React 18.3.1 + RTL 16.3.0 + Vitest 2.1.0，"The current testing environment is not configured to support act()" 警告仍然存在，即使配置正确。这是已知的低优先级问题，不影响测试正确性

### 最佳实践

- 在 jsdom 中测试 Suspense：使用 `waitFor` 或 `findBy*` 等待内容出现，不要手动 `act()`
- 假定时器 + React 状态更新：将 `advanceTimersByTime` 包裹在 `await act(async () => { vi.advanceTimersByTime(ms) })`
- 不要 suppress act() 警告：它们是组件中存在未处理状态更新的信号
- React 19 `use()` 的测试可能需要等待 `@testing-library/react` 正式支持

---

## 补充研究：社区最佳实践与常见反模式 (2026-05-22)

> 来源：多方面社区文章、GitHub issues、eslint-plugin-vitest 文档

### 七大常见反模式

1. **测试实现细节而非行为**：`expect(wrapper.state('isOpen')).toBe(true)` 应改为 `expect(screen.getByText('Menu')).toBeVisible()`
2. **Mock 数据与真实 API 不一致**：用类型安全的工厂函数（`Partial<T>` 覆盖模式）保证 mock 数据结构同步
3. **脆弱的 DOM 查询**：CSS class 选择器、`getByTestId` 过度使用、动态文本无模式匹配
4. **异步处理不当**：异步交互后不用 `findBy*/waitFor`，导致 flaky tests
5. **环境变量竞态条件**：`vi.stubEnv()` 在模块已导入后设置无效，需用 `vi.mock()` 或动态 import
6. **Mock 清理不彻底**：`beforeEach` 要 `vi.clearAllMocks()`，`afterEach` 要恢复全局 mock
7. **断言过度精确**：用 `toBe` 比较对象（引用相等）而非 `toEqual`/`toStrictEqual`（值相等）

### ESLint 规则推荐

| 规则 | 作用 |
|------|------|
| `vitest/no-focused-tests` | 禁止 `.only` 留在代码中 |
| `vitest/no-disabled-tests` | 禁止 `.skip` 提交 |
| `vitest/expect-expect` | 要求每个测试至少有一个断言 |
| `vitest/valid-expect` | 防止 `expect()` 误用 |
| `vitest/valid-title` | 强制 describe/it 标题格式 |
| `vitest/max-nested-describe` | 限制嵌套层级 |

### Singleton Mock 模式

当多个组件共享同一个 reactive mock（如通知系统），使用集中式 mock 单例 + `reset()` 方法：

```typescript
// 比在每个测试中各自创建 mock 更可靠
const mockStore = {
  notifications: [] as Notification[],
  addNotification: vi.fn(),
  reset() {
    this.notifications = []
    vi.clearAllMocks()
  },
}
```

### RTK Query 测试关键发现（来自 vite-rtk-query 项目分析）

- RTK Query 测试**不 mock 查询 hook**，而是让完整 RTK Query 运行时发真实 HTTP 请求
- MSW 在 node 端拦截这些请求，验证完整的数据流
- `main.tsx` 中用动态 `import()` 按需加载 MSW worker，生产 bundle 不包含 mock 代码
- `onUnhandledRequest: 'error'` 强制所有请求都要有 handler，防止遗漏
10. **TypeScript 中开启 strict 模式**：充分利用 Matcher 类型的推断
