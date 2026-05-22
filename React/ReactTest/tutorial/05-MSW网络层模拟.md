---
tags:
  - tutorial
  - msw
created: 2026-05-22
---

# 第五章：MSW — 网络层模拟的哲学与实践

## 学习目标

- 理解 MSW 的网络层拦截原理
- 掌握 MSW v2 核心 API（http, HttpResponse, delay, passthrough）
- 掌握 handler 的组织方式（按域分组、barrel export）
- 理解初始 handler 与运行时覆盖（server.use()）的分工
- 能处理 GraphQL mock 与 WebSocket/SSE mock
- 了解 MSW 内存数据库（@mswjs/data）的使用

---

## 5.1 为什么要在网络层 Mock

假设你有一个用户列表组件，它调用了封装好的 API 函数：

```typescript
// api/users.ts
export async function fetchUsers(): Promise<User[]> {
  const res = await fetch('/api/users')
  if (!res.ok) throw new Error('Failed to fetch')
  return res.json()
}
```

传统的 mock 方式：

```typescript
// ❌ 传统方式：mock 模块
vi.mock('./api/users', () => ({
  fetchUsers: vi.fn().mockResolvedValue([
    { id: 1, name: 'Alice' },
  ]),
}))
```

问题：
1. **绑定了具体模块路径**：如果后来把 `fetchUsers` 移到别的文件，所有 mock 都要更新
2. **没测试到真实的请求逻辑**：`res.ok` 检查、`res.json()` 调用、HTTP 状态码处理全部被跳过了
3. **换了 HTTP 客户端就要重写所有 mock**：从 `fetch` 换成 `axios` 或 `ky`？全废

MSW 的方式：

```typescript
// ✅ MSW 方式：在网络层拦截（在 setup 中全局配置）
import { http, HttpResponse } from 'msw'

const handlers = [
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice' },
    ])
  }),
]
```

现在 `fetchUsers` 函数**完全不需要知道自己在被 mock**——它照常发出 `fetch` 请求，MSW 在请求离开进程之前将其拦截，返回 mock 响应。整个请求-响应周期——`res.ok`、`res.json()`、状态码检查——全部在真实执行。

---

## 5.2 MSW v2 核心 API

### HTTP Handlers

```typescript
import { http, HttpResponse } from 'msw'

const handlers = [
  // GET 请求
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' },
    ])
  }),

  // GET 带路径参数
  http.get('/api/users/:userId', ({ params }) => {
    const { userId } = params
    return HttpResponse.json({ id: Number(userId), name: 'Alice' })
  }),

  // POST — 读取请求体
  http.post('/api/users', async ({ request }) => {
    const body = await request.json() as { name: string }
    return HttpResponse.json({ id: 3, name: body.name }, { status: 201 })
  }),

  // PUT
  http.put('/api/users/:userId', async ({ params, request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: Number(params.userId), ...(body as object) })
  }),

  // DELETE
  http.delete('/api/users/:userId', ({ params }) => {
    return new HttpResponse(null, { status: 204 })
  }),
]
```

### HttpResponse 的完整 API

```typescript
// JSON 响应
HttpResponse.json({ data: 'value' })
HttpResponse.json({ error: 'msg' }, { status: 400 })

// 纯文本
HttpResponse.text('Hello, World!')

// XML
HttpResponse.xml('<root><item>value</item></root>')

// 表单数据
HttpResponse.formData(formData)

// 空响应体
new HttpResponse(null, { status: 204 })
new HttpResponse(null, {
  status: 401,
  headers: { 'X-Custom': 'value' },
})

// 网络错误（模拟断网）
HttpResponse.error()
```

### delay：模拟网络延迟

```typescript
import { http, HttpResponse, delay } from 'msw'

http.get('/api/slow-resource', async () => {
  await delay(1500) // 模拟 1.5 秒延迟
  return HttpResponse.json({ data: 'slow' })
})
```

### passthrough：放行请求

```typescript
import { http, passthrough } from 'msw'

http.get('/api/external-service', () => {
  return passthrough() // 不拦截，让请求到真实网络
})
```

### { once: true }：一次性 Handler

```typescript
http.post('/api/login',
  () => HttpResponse.json({ message: '密码错误' }, { status: 401 }),
  { once: true } // 只拦截第一次匹配的请求
)
```

---

## 5.3 handler 组织方式

### 按功能域分组

```
src/test/mocks/handlers/
  auth.ts          # 登录、注册、注销
  users.ts         # 用户 CRUD
  products.ts      # 商品 CRUD
  orders.ts        # 订单
  index.ts         # barrel export
```

```typescript
// handlers/auth.ts
import { http, HttpResponse } from 'msw'

export const authHandlers = [
  http.post('/api/auth/login', async ({ request }) => {
    const { email, password } = await request.json() as {
      email: string; password: string
    }
    if (email === 'test@example.com' && password === 'password') {
      return HttpResponse.json({ token: 'jwt-token', user: { id: 1, email } })
    }
    return HttpResponse.json(
      { message: '邮箱或密码错误' },
      { status: 401 }
    )
  }),

  http.post('/api/auth/logout', () => {
    return HttpResponse.json({ message: '已登出' })
  }),
]
```

```typescript
// handlers/users.ts
import { http, HttpResponse } from 'msw'

export const usersHandlers = [
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice', email: 'alice@example.com' },
      { id: 2, name: 'Bob', email: 'bob@example.com' },
    ])
  }),

  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: Number(params.id),
      name: 'Alice',
      email: 'alice@example.com',
    })
  }),
]
```

```typescript
// handlers/index.ts
import { authHandlers } from './auth'
import { usersHandlers } from './users'

export const handlers = [
  ...authHandlers,
  ...usersHandlers,
]
```

> **自我验证说明**：这种按域分组的模式直接来自 bulletproof-react 项目（`apps/react-vite/src/testing/mocks/handlers/`），该模式在 MSW 官方文档的 "Structuring handlers" 章节中也有推荐。

### 工厂函数：创建可配置 Handler

```typescript
import { http, HttpResponse, delay, HttpHandler } from 'msw'

interface UsersHandlerConfig {
  shouldError?: boolean
  simulatedDelay?: number
  emptyList?: boolean
}

export function createUsersHandlers(config: UsersHandlerConfig = {}): HttpHandler[] {
  const { shouldError = false, simulatedDelay = 0, emptyList = false } = config

  return [
    http.get('/api/users', async () => {
      if (simulatedDelay > 0) await delay(simulatedDelay)
      if (shouldError) {
        return HttpResponse.json(
          { message: '服务器内部错误' },
          { status: 500 }
        )
      }
      if (emptyList) return HttpResponse.json([])
      return HttpResponse.json([
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
      ])
    }),
  ]
}
```

---

## 5.4 初始 handler 与运行时覆盖

**初始 handler**（传递给 `setupServer()` 的）：定义**默认的快乐路径**——API 一切正常。

**运行时覆盖**（`server.use()`）：在单个测试中覆盖特定端点，引入**边界情况**——500 错误、401、空列表、网络错误等。

```typescript
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'

describe('UserList', () => {
  // 快乐路径：默认 handler 返回正常数据
  it('显示用户列表', async () => {
    render(<UserList />)
    expect(await screen.findByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  // 边界：500 错误
  it('服务器错误时显示错误提示', async () => {
    server.use(
      http.get('/api/users', () =>
        new HttpResponse(null, { status: 500 })
      )
    )
    render(<UserList />)
    expect(await screen.findByRole('alert')).toHaveTextContent('服务器错误')
  })

  // 边界：空状态
  it('空列表时显示空状态提示', async () => {
    server.use(
      http.get('/api/users', () => HttpResponse.json([]))
    )
    render(<UserList />)
    expect(await screen.findByText('暂无用户')).toBeInTheDocument()
  })

  // 边界：网络错误
  it('网络错误时显示重试按钮', async () => {
    server.use(
      http.get('/api/users', () => HttpResponse.error())
    )
    render(<UserList />)
    expect(await screen.findByRole('button', { name: '重试' })).toBeInTheDocument()
  })
})
```

**server.use() 的行为规则**：

1. `server.use(...)` prepend 新 handler，**优先级高于**初始 handler
2. `server.resetHandlers()` 移除所有运行时 handler（在 afterEach 中调用）
3. `server.use(handler, { once: true })` 创建一次性 handler
4. 每次 `use()` 只影响当前添加的 handler，不会覆盖之前的运行时 handler

---

## 5.5 请求验证在 Handler 内部

MSW 官方建议：**不要用 `expect(fetch).toHaveBeenCalledWith(...)` 来验证请求**——这种做法绑定了 HTTP 客户端的具体实现。取而代之，在 handler 内部验证请求：

```typescript
// ✅ Handler 内部验证请求正确性
http.post('/api/orders', async ({ request }) => {
  const body = await request.json() as { productId: string; quantity: number }

  // 请求验证在 handler 中完成
  if (!body.productId) {
    return HttpResponse.json(
      { message: '商品 ID 不能为空' },
      { status: 400 }
    )
  }
  if (body.quantity <= 0) {
    return HttpResponse.json(
      { message: '数量必须大于 0' },
      { status: 400 }
    )
  }

  return HttpResponse.json({ orderId: 'order-123' }, { status: 201 })
})

// 测试端只断言用户可见的行为
it('数量为 0 时显示错误', async () => {
  const user = userEvent.setup()
  render(<OrderForm />)

  await user.type(screen.getByLabelText('数量'), '0')
  await user.click(screen.getByRole('button', { name: '下单' }))

  // 断言用户看到的——不是断言 fetch 被调用
  expect(await screen.findByText('数量必须大于 0')).toBeInTheDocument()
})
```

---

## 5.6 GraphQL Mock

```typescript
import { graphql, HttpResponse } from 'msw'

export const graphqlHandlers = [
  // 查询
  graphql.query('GetUser', ({ variables }) => {
    const { userId } = variables as { userId: string }

    if (userId === '999') {
      return HttpResponse.json({
        errors: [{ message: '用户不存在' }],
      })
    }

    return HttpResponse.json({
      data: {
        user: {
          id: userId,
          name: 'Alice',
          email: 'alice@example.com',
        },
      },
    })
  }),

  // 变更
  graphql.mutation('CreatePost', ({ variables }) => {
    const { title, content } = variables as { title: string; content: string }
    return HttpResponse.json({
      data: {
        createPost: {
          id: 'new-post-id',
          title,
          content,
        },
      },
    })
  }),
]
```

> **自我验证说明**：`graphql.query()` 和 `graphql.mutation()` 来自 `msw`。第一个参数是**操作名称**（operation name），需要与客户端发送的查询名称匹配。响应格式为 `{ data: {...} }` 或 `{ errors: [...] }`，与 GraphQL 规范一致。

---

## 5.7 @mswjs/data — 内存数据库

对于需要真实 CRUD 行为（创建 → 列表中出现新记录、删除 → 列表中消失）的测试，使用 `@mswjs/data` 构建内存数据库：

```bash
npm install -D @mswjs/data
```

```typescript
// mocks/db.ts
import { factory, primaryKey } from '@mswjs/data'

export const db = factory({
  user: {
    id: primaryKey(String),
    name: String,
    email: String,
    role: String,
  },
})

// 在每个测试前初始化种子数据
export function seedDatabase() {
  db.user.create({ id: '1', name: 'Alice', email: 'alice@example.com', role: 'admin' })
  db.user.create({ id: '2', name: 'Bob', email: 'bob@example.com', role: 'user' })
}
```

在 handler 中使用：

```typescript
// handlers/users.ts
import { http, HttpResponse } from 'msw'
import { db } from '../db'

export const usersHandlers = [
  http.get('/api/users', () => {
    const users = db.user.getAll()
    return HttpResponse.json(users)
  }),

  http.get('/api/users/:id', ({ params }) => {
    const user = db.user.findFirst({
      where: { id: { equals: params.id as string } },
    })
    if (!user) {
      return HttpResponse.json({ message: '用户不存在' }, { status: 404 })
    }
    return HttpResponse.json(user)
  }),

  http.post('/api/users', async ({ request }) => {
    const body = await request.json() as { name: string; email: string }
    const newUser = db.user.create({
      id: String(Date.now()),
      name: body.name,
      email: body.email,
      role: 'user',
    })
    return HttpResponse.json(newUser, { status: 201 })
  }),

  http.delete('/api/users/:id', ({ params }) => {
    db.user.delete({
      where: { id: { equals: params.id as string } },
    })
    return new HttpResponse(null, { status: 204 })
  }),
]
```

现在 handler 真正执行了 CRUD，而不只是返回固定数据。创建用户后，再次请求列表会包含新用户。删除后的下一次请求则不再包含该用户。

---

## 5.8 WebSocket 与 SSE Mock（进阶）

### WebSocket

```typescript
import { ws } from 'msw'

const chatWs = ws.link('wss://chat.example.com')

export const handlers = [
  chatWs.addEventListener('connection', ({ client }) => {
    client.addEventListener('message', (event) => {
      // 回显消息给所有客户端
      chatWs.broadcast(event.data)
    })

    // 连接时发送欢迎消息
    client.send('欢迎加入聊天室')
  }),
]
```

### Server-Sent Events (SSE)

```typescript
import { sse } from 'msw'

export const handlers = [
  sse('https://api.example.com/events', ({ client }) => {
    // 每秒推送一次数据
    const interval = setInterval(() => {
      client.send({
        data: { timestamp: Date.now(), value: Math.random() },
      })
    }, 1000)

    // 客户端断开时清理
    client.addEventListener('close', () => {
      clearInterval(interval)
    })
  }),
]
```

> **自我验证说明**：`sse()` API 在 MSW v2.12.0 正式发布。`ws.link()` API 在 MSW v2.x 中已可用。两者在 `setupServer`（Node 测试环境）和 `setupWorker`（浏览器）中均可使用。

---

## 练习与思考

1. 为一个电商 API 设计 MSW handler 结构：商品（CRUD）、购物车（添加/删除/结账）、订单（列表/详情）
2. 使用 `server.use()` 为订单列表组件写 5 个测试：正常列表、空列表、500 错误、网络错误、401 未授权
3. 用工厂函数模式重构第 2 题的 handler，使其可配置
4. 讨论：什么情况下应该用 `@mswjs/data` 做内存数据库？什么时候直接返回静态数据就够了？

---

## 本章总结

- MSW 在网络层拦截请求，让测试在「真实」HTTP 环境中运行
- v2 核心 API：`http.*` + `HttpResponse.*`，完全替代 v1 的 `rest.*` + `res(ctx.*)`
- handler 按功能域分组，通过 index.ts barrel export
- 初始 handler = 快乐路径，`server.use()` = 单测边界覆盖
- 请求验证放在 handler 内部，测试端只断言用户可见行为
- `@mswjs/data` 提供内存数据库，让 handler 能真实执行 CRUD
- `ws.link()` 和 `sse()` 支持 WebSocket 和 SSE 模拟
