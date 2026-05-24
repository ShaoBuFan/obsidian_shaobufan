---
tags:
  - 参考/练习
created: 2026-05-22
---

# 附录D：练习答案

> 选取各章最具教学价值的练习，提供完整的参考实现和自检说明。
>
> **使用指引**：先自己做，再对照。不要直接复制。理解答案的设计决策比通过测试更重要。

---

## [第1章：测试架构思维](01-测试架构思维.md)

### 练习 2：判断测试是行为还是实现细节

```typescript
// 原始测试（片段）：
it('increments count on button click', () => {
  const { result } = renderHook(() => useCounter(0))
  act(() => { result.current.increment() })
  expect(result.current.count).toBe(1)
})
```

**判断**：这是**实现细节**测试。理由：
- 直接断言了 `result.current.count`——这是内部状态名
- `count` 在重构中可能被改名为 `value`，但用户行为没有变化
- 用户看不懂 "count"，用户只看到界面上数字变了

**重写**：

```typescript
it('shows incremented number when button is clicked', async () => {
  const user = userEvent.setup()
  render(<Counter />)

  const display = screen.getByRole('status')
  expect(display).toHaveTextContent('0')

  await user.click(screen.getByRole('button', { name: /increment/i }))

  expect(display).toHaveTextContent('1')
})
```

**自检要点**：
- 不引用任何内部变量名（`count`、`value`、`increment`）
- 所有断言基于用户可见的 DOM 内容
- `getByRole('button', { name: /increment/i })` 同时验证了角色和文本

---

## [第2章：测试环境搭建](02-测试环境搭建.md)

### 练习 1：从零搭建完整配置

```typescript
// vite.config.ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
})
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

```json
// tsconfig.json 关键字段
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

```typescript
// src/App.test.tsx — 冒烟测试验证
import { render, screen } from '@testing-library/react'

function Hello({ name }: { name: string }) {
  return <h1>Hello, {name}!</h1>
}

describe('环境验证', () => {
  it('renders heading', () => {
    render(<Hello name="World" />)
    expect(
      screen.getByRole('heading', { name: /hello, world/i })
    ).toBeInTheDocument()
  })
})
```

**自检要点**：
- 运行 `npx vitest run` 应全部通过
- 故意去掉 `environment: 'jsdom'` 看 `document is not defined` 错误
- 故意去掉 `import '@testing-library/jest-dom/vitest'` 看 `toBeInTheDocument` 类型错误

---

## [第3章：Vitest 基础](03-Vitest基础.md)

### 练习 2：测试 throttle 函数

```typescript
// throttle.ts
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0
  return (...args: Parameters<T>) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      fn(...args)
    }
  }
}
```

```typescript
// throttle.test.ts
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { throttle } from './throttle'

describe('throttle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls function immediately on first invocation', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 1000)

    throttled()

    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('ignores calls within throttle window', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 1000)

    throttled()                // count = 1
    throttled()                // ignored
    throttled()                // ignored

    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('allows another call after throttle window', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 1000)

    throttled()                // count = 1
    vi.advanceTimersByTime(1000)
    throttled()                // count = 2

    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('passes arguments to original function', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 500)

    throttled('hello', 42)

    expect(fn).toHaveBeenCalledWith('hello', 42)
  })

  it('only uses last call args when throttled', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 1000)

    throttled('first')
    throttled('second')
    throttled('third')

    // throttle 不是 debounce——第一个调用应该成功，参数为 'first'
    // 最终 throttle 窗口结束后，下一次调用会用最新的参数
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('first')
  })
})
```

**自检要点**：
- `beforeEach` / `afterEach` 的成对定时器管理
- `vi.advanceTimersByTime(1000)` 恰好推进到 throttle window 边界
- throttle 和 debounce 的区别：throttle 在窗口开始时调用，debounce 在窗口结束时调用

---

## [第4章：查询的艺术](04-查询的艺术.md)

### 练习 2：Todo 应用的增删测试

```typescript
// TodoApp.tsx（参考组件）
function TodoApp() {
  const [todos, setTodos] = useState<string[]>([])
  const [input, setInput] = useState('')

  function addTodo() {
    if (input.trim()) {
      setTodos([...todos, input.trim()])
      setInput('')
    }
  }

  function removeTodo(index: number) {
    setTodos(todos.filter((_, i) => i !== index))
  }

  return (
    <div>
      <h1>Todo List</h1>
      <form onSubmit={(e) => { e.preventDefault(); addTodo() }}>
        <input
          aria-label="New todo"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit">Add</button>
      </form>
      <ul>
        {todos.map((todo, i) => (
          <li key={i}>
            {todo}
            <button aria-label={`Delete ${todo}`} onClick={() => removeTodo(i)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

```typescript
// TodoApp.test.tsx
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TodoApp } from './TodoApp'

describe('TodoApp', () => {
  it('adds a todo and displays it in the list', async () => {
    const user = userEvent.setup()
    render(<TodoApp />)

    const input = screen.getByRole('textbox', { name: /new todo/i })
    const addButton = screen.getByRole('button', { name: /add/i })

    await user.type(input, 'Buy milk')
    await user.click(addButton)

    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(1)
    expect(listItems[0]).toHaveTextContent('Buy milk')
  })

  it('removes a todo when delete is clicked', async () => {
    const user = userEvent.setup()
    render(<TodoApp />)

    // 添加两个 todo
    const input = screen.getByRole('textbox', { name: /new todo/i })
    const addButton = screen.getByRole('button', { name: /add/i })

    await user.type(input, 'Buy milk')
    await user.click(addButton)
    await user.type(input, 'Walk dog')
    await user.click(addButton)

    expect(screen.getAllByRole('listitem')).toHaveLength(2)

    // 删除 "Buy milk"
    const deleteBtn = screen.getByRole('button', { name: /delete buy milk/i })
    await user.click(deleteBtn)

    const remainingItems = screen.getAllByRole('listitem')
    expect(remainingItems).toHaveLength(1)
    expect(remainingItems[0]).toHaveTextContent('Walk dog')
    expect(remainingItems[0]).not.toHaveTextContent('Buy milk')
  })

  it('verifies list is empty after deleting all todos', async () => {
    const user = userEvent.setup()
    render(<TodoApp />)

    const input = screen.getByRole('textbox', { name: /new todo/i })
    const addButton = screen.getByRole('button', { name: /add/i })

    // 添加一个 todo
    await user.type(input, 'Temporary')
    await user.click(addButton)

    // 删除它
    await user.click(screen.getByRole('button', { name: /delete temporary/i }))

    // 确认列表为空
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
  })

  it('does not add empty todos', async () => {
    const user = userEvent.setup()
    render(<TodoApp />)

    const addButton = screen.getByRole('button', { name: /add/i })
    await user.click(addButton)

    // 没有 listitem
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
  })
})
```

**自检要点**：
- 没有使用 `getByTestId`——所有查询都是语义的（`role` + `aria-label` + `getByText`）
- `queryByRole` 用于断言元素不存在
- 添加后在列表中找到新项目，验证了状态更新和渲染
- `aria-label` 为删除按钮提供了明确的 accessible name

---

## [第5章：用户事件模拟](05-用户事件模拟.md)

### 练习：完整交互测试

```typescript
// UserForm.tsx（参考组件）
function UserForm({ onSubmit }: { onSubmit: (data: any) => void }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [file, setFile] = useState<File | null>(null)

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit({ name, email, file }) }}>
      <label htmlFor="name">Name</label>
      <input id="name" value={name} onChange={(e) => setName(e.target.value)} />

      <label htmlFor="email">Email</label>
      <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />

      <label htmlFor="avatar">Avatar</label>
      <input id="avatar" type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />

      <button type="submit">Submit</button>
    </form>
  )
}
```

```typescript
// UserForm.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UserForm } from './UserForm'

describe('UserForm', () => {
  it('fills out and submits the form', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()
    render(<UserForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/name/i), 'Alice')
    await user.type(screen.getByLabelText(/email/i), 'alice@test.com')

    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Alice',
        email: 'alice@test.com',
      })
    )
  })

  it('uploads a file', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()
    render(<UserForm onSubmit={onSubmit} />)

    const file = new File(['avatar content'], 'avatar.png', { type: 'image/png' })
    await user.upload(screen.getByLabelText(/avatar/i), file)

    await user.type(screen.getByLabelText(/name/i), 'Alice')
    await user.type(screen.getByLabelText(/email/i), 'alice@test.com')

    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        file: expect.objectContaining({
          name: 'avatar.png',
          type: 'image/png',
        }),
      })
    )
  })

  it('navigates form with keyboard', async () => {
    const user = userEvent.setup()
    render(<UserForm onSubmit={vi.fn()} />)

    // 初始焦点在 name
    await user.tab()
    expect(screen.getByLabelText(/name/i)).toHaveFocus()

    // Tab 到 email
    await user.tab()
    expect(screen.getByLabelText(/email/i)).toHaveFocus()

    // Tab 到 file 输入
    await user.tab()
    expect(screen.getByLabelText(/avatar/i)).toHaveFocus()

    // Tab 到 submit
    await user.tab()
    expect(screen.getByRole('button', { name: /submit/i })).toHaveFocus()

    // Enter 提交
    await user.keyboard('{Enter}')
  })
})
```

**自检要点**：
- 所有 `userEvent` 方法前都加了 `await`
- `userEvent.setup()` 在测试内创建（不在 `beforeEach` 中全局共享）
- 文件上传使用了 `new File()` 构造 File 对象
- 键盘导航覆盖了 Tab 顺序和 Enter 提交

---

## [第6章：MSW 哲学与实践](06-MSW哲学与实践.md)

### 练习：搭建完整 MSW 配置并测试 CRUD

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

interface Post {
  id: number
  title: string
  body: string
}

let posts: Post[] = [
  { id: 1, title: 'First Post', body: 'Hello world' },
  { id: 2, title: 'Second Post', body: 'Another post' },
]

export const handlers = [
  // GET /api/posts
  http.get('/api/posts', () => {
    return HttpResponse.json(posts)
  }),

  // GET /api/posts/:id
  http.get<{ id: string }>('/api/posts/:id', ({ params }) => {
    const post = posts.find((p) => p.id === Number(params.id))
    if (!post) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(post)
  }),

  // POST /api/posts
  http.post('/api/posts', async ({ request }) => {
    const body = (await request.json()) as { title: string; body: string }
    const newPost: Post = {
      id: posts.length + 1,
      title: body.title,
      body: body.body,
    }
    posts.push(newPost)
    return HttpResponse.json(newPost, { status: 201 })
  }),

  // DELETE /api/posts/:id
  http.delete<{ id: string }>('/api/posts/:id', ({ params }) => {
    const id = Number(params.id)
    posts = posts.filter((p) => p.id !== id)
    return new HttpResponse(null, { status: 204 })
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
import '@testing-library/jest-dom/vitest'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

```typescript
// src/api/posts.test.ts
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

describe('Posts API', () => {
  it('fetches all posts', async () => {
    const res = await fetch('/api/posts')
    const data = await res.json()

    expect(res.status).toBe(200)
    expect(data).toHaveLength(2)
    expect(data[0]).toHaveProperty('title', 'First Post')
  })

  it('fetches a single post by id', async () => {
    const res = await fetch('/api/posts/1')
    const data = await res.json()

    expect(res.status).toBe(200)
    expect(data.title).toBe('First Post')
  })

  it('returns 404 for non-existent post', async () => {
    const res = await fetch('/api/posts/999')
    expect(res.status).toBe(404)
  })

  it('creates a new post', async () => {
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New Post', body: 'Content' }),
    })
    const data = await res.json()

    expect(res.status).toBe(201)
    expect(data).toHaveProperty('id')
    expect(data.title).toBe('New Post')

    // 验证已创建的 post 出现在列表中
    const listRes = await fetch('/api/posts')
    const list = await listRes.json()
    expect(list).toHaveLength(3)
  })

  it('handles 500 error', async () => {
    server.use(
      http.get('/api/posts', () => {
        return HttpResponse.json(
          { message: 'Internal Server Error' },
          { status: 500 }
        )
      })
    )

    const res = await fetch('/api/posts')
    expect(res.status).toBe(500)
  })

  it('handles network error', async () => {
    server.use(
      http.get('/api/posts', () => HttpResponse.error())
    )

    await expect(fetch('/api/posts')).rejects.toThrow('Failed to fetch')
  })
})
```

**自检要点**：
- `server.use()` 只覆盖当前测试的 handler
- `afterEach(() => server.resetHandlers())` 确保 per-test 覆盖不泄漏
- `onUnhandledRequest: 'error'` 在开发时捕获所有未匹配请求
- 内存数组 `posts` 在测试间共享——需要时可用 `beforeEach` 重置

---

## [第8章：React Hook 测试](08-React-Hook测试.md)

### 练习：测试 useDebounce

```typescript
// useDebounce.ts
import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}
```

```typescript
// useDebounce.test.ts
import { renderHook, act } from '@testing-library/react'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 500))

    expect(result.current).toBe('hello')
  })

  it('does not update value before delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    )

    rerender({ value: 'world', delay: 500 })

    // delay 未到之前，值仍然是 'hello'
    vi.advanceTimersByTime(499)
    expect(result.current).toBe('hello')
  })

  it('updates value after delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    )

    rerender({ value: 'world', delay: 500 })

    vi.advanceTimersByTime(500)

    expect(result.current).toBe('world')
  })

  it('resets timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'a', delay: 500 } }
    )

    rerender({ value: 'ab', delay: 500 })
    vi.advanceTimersByTime(300) // 还剩 200ms

    rerender({ value: 'abc', delay: 500 }) // 重置定时器
    vi.advanceTimersByTime(300) // 还剩 200ms（不是 500+300）

    // 'abc' 还没到时间
    expect(result.current).toBe('a')

    vi.advanceTimersByTime(200)

    // 'abc' 应该现在更新
    expect(result.current).toBe('abc')
  })

  it('cleans up timer on unmount', () => {
    const { result, rerender, unmount } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    )

    rerender({ value: 'world', delay: 500 })
    unmount()

    // 卸载后推进时间，不应触发状态更新
    vi.advanceTimersByTime(500)

    // 组件已卸载，result.current 不会变（也不应有 act() 警告）
  })
})
```

**自检要点**：
- 使用 `renderHook` 的 `rerender` 改变 props 模拟输入变化
- `vi.advanceTimersByTime` 精确控制时间推进
- 验证了 debounce 的核心行为：多次变化只取最后一次
- 验证了清理函数（unmount 后定时器取消）

---

## [第9章：表单测试](09-表单测试.md)

### 练习：注册表单完整测试

```typescript
// RegistrationForm.tsx（参考组件）
interface FormData {
  username: string
  email: string
  password: string
  confirmPassword: string
}

function RegistrationForm({ onSubmit }: { onSubmit: (data: FormData) => Promise<void> }) {
  const [formData, setFormData] = useState<FormData>({
    username: '', email: '', password: '', confirmPassword: '',
  })
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  function validate(): boolean {
    const newErrors: typeof errors = {}
    if (!formData.username) newErrors.username = 'Username is required'
    if (!formData.email) newErrors.email = 'Email is required'
    if (!formData.password) newErrors.password = 'Password is required'
    if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters'
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = 'Passwords do not match'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    setIsSubmitting(true)
    try {
      await onSubmit(formData)
    } catch (err: any) {
      setServerError(err.message || 'Submission failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {serverError && <div role="alert">{serverError}</div>}

      <label htmlFor="username">Username</label>
      <input id="username" value={formData.username}
        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
        aria-invalid={!!errors.username}
        aria-describedby={errors.username ? 'username-error' : undefined} />
      {errors.username && <span id="username-error" role="alert">{errors.username}</span>}

      <label htmlFor="email">Email</label>
      <input id="email" type="email" value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        aria-invalid={!!errors.email} />
      {errors.email && <span role="alert">{errors.email}</span>}

      <label htmlFor="password">Password</label>
      <input id="password" type="password" value={formData.password}
        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        aria-invalid={!!errors.password} />
      {errors.password && <span role="alert">{errors.password}</span>}

      <label htmlFor="confirmPassword">Confirm Password</label>
      <input id="confirmPassword" type="password" value={formData.confirmPassword}
        onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
        aria-invalid={!!errors.confirmPassword} />
      {errors.confirmPassword && <span role="alert">{errors.confirmPassword}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Register'}
      </button>
    </form>
  )
}
```

```typescript
// RegistrationForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { RegistrationForm } from './RegistrationForm'

describe('RegistrationForm', () => {
  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<RegistrationForm onSubmit={onSubmit} />)

    await user.click(screen.getByRole('button', { name: /register/i }))

    expect(screen.getByText(/username is required/i)).toBeInTheDocument()
    expect(screen.getByText(/email is required/i)).toBeInTheDocument()
    expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('validates password length', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<RegistrationForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/password/i), 'abc')
    await user.click(screen.getByRole('button', { name: /register/i }))

    expect(screen.getByText(/at least 6 characters/i)).toBeInTheDocument()
  })

  it('validates password confirmation match', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<RegistrationForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/username/i), 'Alice')
    await user.type(screen.getByLabelText(/email/i), 'alice@test.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'different')

    await user.click(screen.getByRole('button', { name: /register/i }))

    expect(screen.getByText(/do not match/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits successfully with valid data', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<RegistrationForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/username/i), 'Alice')
    await user.type(screen.getByLabelText(/email/i), 'alice@test.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')

    await user.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        username: 'Alice',
        email: 'alice@test.com',
        password: 'password123',
        confirmPassword: 'password123',
      })
    })
  })

  it('shows submitting state', async () => {
    const user = userEvent.setup()
    // 延迟 resolve 以观察 submitting 状态
    const onSubmit = vi.fn().mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 1000)))

    render(<RegistrationForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/username/i), 'Alice')
    await user.type(screen.getByLabelText(/email/i), 'alice@test.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')

    await user.click(screen.getByRole('button', { name: /register/i }))

    // 按钮应变为提交中状态
    expect(screen.getByRole('button', { name: /submitting/i })).toBeDisabled()
  })

  it('shows server error on submission failure', async () => {
    const user = userEvent.setup()
    render(<RegistrationForm
      onSubmit={() => Promise.reject(new Error('Email already taken'))}
    />)

    await user.type(screen.getByLabelText(/username/i), 'Alice')
    await user.type(screen.getByLabelText(/email/i), 'existing@test.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')

    await user.click(screen.getByRole('button', { name: /register/i }))

    await screen.findByRole('alert')
    expect(screen.getByText(/email already taken/i)).toBeInTheDocument()
  })

  it('supports keyboard navigation and submission', async () => {
    const user = userEvent.setup()
    render(<RegistrationForm onSubmit={vi.fn()} />)

    // Tab 遍历表单控件
    await user.tab()
    expect(screen.getByLabelText(/username/i)).toHaveFocus()

    await user.tab()
    expect(screen.getByLabelText(/email/i)).toHaveFocus()

    await user.tab()
    expect(screen.getByLabelText(/password/i)).toHaveFocus()

    await user.tab()
    expect(screen.getByLabelText(/confirm password/i)).toHaveFocus()

    await user.tab()
    expect(screen.getByRole('button', { name: /register/i })).toHaveFocus()
  })
})
```

**自检要点**：
- 使用 `getByLabelText` 查找输入框——和用户行为一致
- `aria-invalid`、`aria-describedby` 用于可访问性断言
- 验证了 `isSubmitting` 状态下的按钮禁用
- 通过 `mockResolvedValue(undefined)` 和 `mockRejectedValue` 分别测试成功和失败路径

---

## [第10章：路由测试](10-路由测试.md)

### 练习：带守卫的多页面路由测试

```typescript
// App.tsx（参考组件）
function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/users/:id" element={
        <ProtectedRoute requiredRole="admin">
          <UserProfile />
        </ProtectedRoute>
      } />
    </Routes>
  )
}
```

```typescript
// App.test.tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { App } from './App'

function renderWithRouter(initialRoute: string = '/') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>
  )
}

describe('Routing', () => {
  it('renders home page at /', () => {
    renderWithRouter('/')
    expect(screen.getByRole('heading', { name: /home/i })).toBeInTheDocument()
  })

  it('renders login page at /login', () => {
    renderWithRouter('/login')
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
  })

  it('redirects to login when accessing dashboard without auth', () => {
    renderWithRouter('/dashboard')
    // 未认证 → 重定向到 /login
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument()
  })

  it('renders dashboard when authenticated', () => {
    // 模拟认证状态
    vi.spyOn(auth, 'isAuthenticated').mockReturnValue(true)

    renderWithRouter('/dashboard')
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
  })

  it('redirects to 403 when user lacks admin role', () => {
    vi.spyOn(auth, 'isAuthenticated').mockReturnValue(true)
    vi.spyOn(auth, 'getRole').mockReturnValue('user')

    renderWithRouter('/users/1')
    expect(screen.getByText(/403/i)).toBeInTheDocument()
  })

  it('navigates to user detail page', () => {
    vi.spyOn(auth, 'isAuthenticated').mockReturnValue(true)
    vi.spyOn(auth, 'getRole').mockReturnValue('admin')

    renderWithRouter('/users/42')

    // 组件应读取 :id 参数并显示
    expect(screen.getByText(/user 42/i)).toBeInTheDocument()
  })
})
```

**自检要点**：
- `MemoryRouter` + `initialEntries` 设置初始路由路径
- 不 mock `useParams`、`useNavigate`——使用真实的 Router 行为
- 路由守卫通过在 `beforeEach` 中 mock 认证状态来控制

---

## [第11章：状态管理测试](11-状态管理测试.md)

### 练习：TanStack Query 列表页面测试

```typescript
// ProductList.tsx（参考组件）
function ProductList() {
  const { data: products, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => fetch('/api/products').then((r) => r.json()),
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading products</div>

  return (
    <ul>
      {products?.map((p: any) => (
        <li key={p.id}>{p.name} - ${p.price}</li>
      ))}
    </ul>
  )
}
```

```typescript
// ProductList.test.tsx
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { ProductList } from './ProductList'

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('ProductList', () => {
  it('shows loading state initially', () => {
    renderWithQueryClient(<ProductList />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders products after fetching', async () => {
    server.use(
      http.get('/api/products', () => {
        return HttpResponse.json([
          { id: 1, name: 'Widget', price: 9.99 },
          { id: 2, name: 'Gadget', price: 19.99 },
        ])
      })
    )

    renderWithQueryClient(<ProductList />)

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Widget')
    expect(items[1]).toHaveTextContent('Gadget')
  })

  it('does not send duplicate requests on re-render', async () => {
    // 验证 queryClient 的缓存行为
    server.use(
      http.get('/api/products', () => {
        return HttpResponse.json([{ id: 1, name: 'Widget', price: 9.99 }])
      })
    )

    const { rerender } = renderWithQueryClient(<ProductList />)
    await screen.findByText('Widget')

    // 重新渲染不会触发新的请求
    rerender(
      <QueryClientProvider client={new QueryClient({
        defaultOptions: { queries: { retry: false, gcTime: 0 } },
      })}>
        <ProductList />
      </QueryClientProvider>
    )

    // 数据应直接从缓存读取
    expect(await screen.findByText('Widget')).toBeInTheDocument()
  })
})
```

**自检要点**：
- `QueryClient` 配置了 `retry: false` 防止测试超时
- `gcTime: 0` 确保缓存即时清理
- `wrapper`（通过 `renderWithQueryClient`）提供 QueryClientProvider
- MSW handler 在测试中覆盖以提供测试数据

---

## [第12/13章：综合选做](12-测试可维护性.md) / [第13章：CI/CD 实践](13-CI-CD实践.md)

### 练习：renderWithProviders + 数据工厂

```typescript
// src/test/utils.tsx
import { render, RenderResult } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UserEvent } from '@testing-library/user-event/dist/types/setup/setup'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactElement } from 'react'

interface ProviderOptions {
  initialRoute?: string
}

interface RenderWithProvidersResult extends RenderResult {
  user: UserEvent
  queryClient: QueryClient
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  })
}

export function renderWithProviders(
  ui: ReactElement,
  options: ProviderOptions = {}
): RenderWithProvidersResult {
  const queryClient = createQueryClient()
  const { initialRoute = '/' } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  return {
    ...render(ui, { wrapper: Wrapper }),
    user: userEvent.setup(),
    queryClient,
  }
}
```

```typescript
// src/test/factories.ts
import { faker } from '@faker-js/faker'

export interface Product {
  id: number
  name: string
  price: number
  description: string
  inStock: boolean
  category: string
}

export function buildProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: faker.number.int({ min: 1, max: 99999 }),
    name: faker.commerce.productName(),
    price: parseFloat(faker.commerce.price()),
    description: faker.commerce.productDescription(),
    inStock: true,
    category: faker.commerce.department(),
    ...overrides,
  }
}

export function buildProductList(count = 5, overrides: Partial<Product> = {}): Product[] {
  return Array.from({ length: count }, (_, i) => buildProduct({ ...overrides, id: i + 1 }))
}
```

### 综合使用

```typescript
// ProductDashboard.test.tsx
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { renderWithProviders, buildProduct, buildProductList } from '../test/utils'
import { ProductDashboard } from './ProductDashboard'

describe('ProductDashboard', () => {
  it('displays products from API', async () => {
    const products = buildProductList(3)

    server.use(
      http.get('/api/products', () => HttpResponse.json(products))
    )

    const { user } = renderWithProviders(<ProductDashboard />)

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent(products[0].name)
  })

  it('handles empty product list', async () => {
    server.use(
      http.get('/api/products', () => HttpResponse.json([]))
    )

    renderWithProviders(<ProductDashboard />)

    await screen.findByText(/no products/i)
  })
})
```

**自检要点**：
- `renderWithProviders` 提供了 `user` 和 `queryClient`，测试不需要额外 setup
- 数据工厂（`buildProduct`）生成真实感数据
- `buildProductList` 方便地批量生成测试数据
- MSW handler 在每个测试中用 `server.use()` 覆盖

---

## [第14章：Jest 迁移](14-Jest迁移指南.md)

### 练习 2：修复 mock 工厂

```typescript
// ❌ 原始代码（不工作）
const userId = 'test-user-123'
const mockApi = vi.fn().mockResolvedValue({ data: [] })

vi.mock('./api', () => ({
  fetchData: mockApi,
  getUserId: vi.fn().mockReturnValue(userId),
}))

// ✅ 修复后
const { mockApi, userId } = vi.hoisted(() => ({
  mockApi: vi.fn().mockResolvedValue({ data: [] }),
  userId: 'test-user-123',
}))

vi.mock('./api', () => ({
  fetchData: mockApi,
  getUserId: vi.fn().mockReturnValue(userId),
}))
```

### 练习 3：迁移 requireActual

```typescript
// Jest
jest.mock('./config', () => ({
  ...jest.requireActual('./config'),
  getFeatureFlag: jest.fn().mockReturnValue(false),
}))

// Vitest
vi.mock('./config', async (importOriginal) => {
  const mod = await importOriginal<typeof import('./config')>()
  return {
    ...mod,
    getFeatureFlag: vi.fn().mockReturnValue(false),
  }
})
```

**自检要点**：
- `vi.hoisted()` 将变量创建提升到文件顶部
- `vi.mock()` 的 async factory 使用 `await importOriginal()`
- 泛型 `typeof import('./config')` 保留原始模块的类型

---

## [第15章：进阶场景（选做）](15-进阶测试场景.md)

### Error Boundary 完整测试

```typescript
// 对应[第15章 15.4 节](15-进阶测试场景.md)
// 参考本章正文内容中的 ErrorBoundary 测试代码即可
```

### 核心要点

- 必须用 `vi.spyOn(console, 'error').mockImplementation(() => {})` 抑制 React 报错日志
- `componentDidCatch` 接收两个参数：`(error, info)`，`info.componentStack` 包含组件栈
- 错误恢复需要同时 reset ErrorBoundary 的 state 和修复子组件的 props
- 验证恢复后的 UI 应该使用 `expect(screen.getByText('Recovered')).toBeInTheDocument()`

---

## 附录说明

参考答案的目的是**展示思路**，不是唯一解。以下情况需要你自行调整：

- **组件名称不同**：根据你的实际组件名修改 `describe` 和查询的 `name` 选项
- **状态管理不同**：如果使用 Zustand、Redux 而非 TanStack Query，Provider 注入方式不同
- **路由库不同**：本教程基于 React Router v6，如果是 v5 有 API 差异
- **文件结构不同**：根据你的项目结构调整 import 路径

好测试的共同特征：断言行为而非实现、使用语义查询、每个测试验证一个路径、可读性强。

## 关联章节
- [第1章：测试架构思维](01-测试架构思维.md)
- [第2章：测试环境搭建](02-测试环境搭建.md)
- [第3章：Vitest 基础](03-Vitest基础.md)
- [第4章：查询的艺术](04-查询的艺术.md)
- [第5章：用户事件模拟](05-用户事件模拟.md)
- [第6章：MSW 哲学与实践](06-MSW哲学与实践.md)
- [第8章：React Hook 测试](08-React-Hook测试.md)
- [第9章：表单测试](09-表单测试.md)
- [第10章：路由测试](10-路由测试.md)
- [第11章：状态管理测试](11-状态管理测试.md)
- [第12章：测试可维护性](12-测试可维护性.md) / [第13章：CI/CD 实践](13-CI-CD实践.md)
- [第14章：Jest 迁移](14-Jest迁移指南.md)
- [第15章：进阶测试场景](15-进阶测试场景.md)
