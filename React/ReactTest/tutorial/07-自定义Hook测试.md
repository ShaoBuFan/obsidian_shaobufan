---
tags:
  - tutorial
  - hook-testing
created: 2026-05-22
---

# 第七章：自定义 Hook 测试

## 学习目标

- 掌握 `renderHook` 的 API 和使用模式
- 能测试带 Provider 依赖的 Hook
- 能测试异步 Hook 的 loading/data/error 三态
- 能测试 Hook 的清理逻辑
- 了解与 MSW 配合的方式

---

## 7.1 renderHook 基础

`renderHook` 已内置在 `@testing-library/react` 中（不再需要独立包 `@testing-library/react-hooks`）。

```typescript
import { renderHook, act } from '@testing-library/react'

// 简单的同步 Hook
function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue)

  const increment = useCallback(() => setCount((c) => c + 1), [])
  const decrement = useCallback(() => setCount((c) => c - 1), [])
  const reset = useCallback(() => setCount(initialValue), [initialValue])

  return { count, increment, decrement, reset }
}
```

```typescript
// useCounter.test.ts
import { renderHook, act } from '@testing-library/react'

describe('useCounter', () => {
  it('返回初始值', () => {
    const { result } = renderHook(() => useCounter(5))
    expect(result.current.count).toBe(5)
  })

  it('increment 增加计数', () => {
    const { result } = renderHook(() => useCounter(0))

    act(() => {
      result.current.increment()
    })

    expect(result.current.count).toBe(1)
  })

  it('reset 恢复到初始值', () => {
    const { result } = renderHook(() => useCounter(10))

    act(() => {
      result.current.increment()
      result.current.increment()
    })
    expect(result.current.count).toBe(12)

    act(() => {
      result.current.reset()
    })
    expect(result.current.count).toBe(10)
  })
})
```

### result.current 不可解构

这是一个**机械规则**：永远不要解构 `result.current`。

```typescript
// ❌ 错误：解构的值不会更新
const { count, increment } = result.current
act(() => increment())
expect(count).toBe(1) // 失败！count 仍是旧值 0

// ✅ 正确：始终通过 result.current 访问
act(() => result.current.increment())
expect(result.current.count).toBe(1) // 正确
```

原因是 `result.current` 是一个**可变引用**——每次 Hook 重新渲染时 RTL 都会更新 `result.current` 的指向，但解构出来的变量不会跟着变。

---

## 7.2 renderHook 的完整 API

```typescript
const {
  result,           // { current: 返回值 }
  rerender,         // (newProps?) => void — 用新 props 重新渲染
  unmount,          // () => void — 卸载，触发 useEffect cleanup
} = renderHook(
  (props) => useMyHook(props),
  {
    initialProps: { id: '1' },
    wrapper: ({ children }) => <Provider>{children}</Provider>,
  }
)
```

### rerender

测试 props 变化时 Hook 的行为：

```typescript
it('props 变化时重新发送请求', async () => {
  const { result, rerender } = renderHook(
    ({ userId }) => useUser(userId),
    { initialProps: { userId: '1' } }
  )

  await waitFor(() => {
    expect(result.current.data?.id).toBe('1')
  })

  // 更换 userId
  rerender({ userId: '2' })

  await waitFor(() => {
    expect(result.current.data?.id).toBe('2')
  })
})
```

### unmount

测试清理逻辑：

```typescript
it('卸载时取消订阅', () => {
  const unsubscribe = vi.fn()
  // 模拟一个返回 cleanup 函数的 Hook
  const { unmount } = renderHook(() => {
    useEffect(() => {
      return () => unsubscribe() // cleanup
    }, [])
  })

  unmount()
  expect(unsubscribe).toHaveBeenCalledTimes(1)
})
```

---

## 7.3 异步 Hook 测试

```typescript
// useFetch — 一个典型的异步数据获取 Hook
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    setIsLoading(true)
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        if (!cancelled) {
          setData(data as T)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [url])

  return { data, error, isLoading }
}
```

### 配合 MSW 的完整测试

```typescript
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mocks/server'

describe('useFetch', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/data', () =>
        HttpResponse.json({ message: 'hello' })
      )
    )
  })

  it('加载中状态 → 数据加载成功', async () => {
    const { result } = renderHook(() => useFetch<{ message: string }>('/api/data'))

    // 初始状态：正在加载
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeNull()

    // 等待加载完成
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual({ message: 'hello' })
    expect(result.current.error).toBeNull()
  })

  it('服务器返回错误时的 error 状态', async () => {
    server.use(
      http.get('/api/data', () =>
        new HttpResponse(null, { status: 500 })
      )
    )

    const { result } = renderHook(() => useFetch('/api/data'))

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBeDefined()
    expect(result.current.error?.message).toContain('500')
  })
})
```

---

## 7.4 带 Provider 的 Hook 测试

当 Hook 依赖 Context（如 React Query、React Router、自定义 Context）时，用 `wrapper` 选项注入：

```typescript
// 测试依赖 QueryClient 的 Hook
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

it('测试使用 React Query 的 Hook', async () => {
  const { result } = renderHook(
    () => useQuery({ queryKey: ['users'], queryFn: fetchUsers }),
    { wrapper: createWrapper() }
  )

  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true)
  })
})
```

### 封装可复用的 wrapper 工厂

```typescript
// src/test/test-utils.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

export function createTestWrapper({
  route = '/',
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  }),
} = {}) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

// 使用
const { result } = renderHook(() => useUser('123'), {
  wrapper: createTestWrapper(),
})
```

---

## 7.5 常见陷阱

### 陷阱 1：在 waitFor 之外断言异步值

```typescript
// ❌ 错误 — 在 waitFor 外部访问异步值
renderHook(() => useAsyncHook())
// ...没有 waitFor
expect(result.current.data).toBeDefined() // 此时可能仍是 null

// ✅ 正确
await waitFor(() => {
  expect(result.current.data).toBeDefined()
})
```

### 陷阱 2：不必要的 act 包装

```typescript
// ❌ 不必要 — waitFor 内部已处理 act
await act(async () => {
  await waitFor(() => {
    expect(result.current.data).toBeDefined()
  })
})

// ✅ waitFor 已经包含 act 语义
await waitFor(() => {
  expect(result.current.data).toBeDefined()
})
```

### 陷阱 3：在 waitFor 中放置副作用

```typescript
// ❌ waitFor 的 callback 可能执行多次！
await waitFor(() => {
  result.current.increment() // 被调用了多次！
  expect(result.current.count).toBe(1)
})

// ✅ 副作用放外面
act(() => result.current.increment())
await waitFor(() => {
  expect(result.current.count).toBe(1)
})
```

---

## 练习与思考

1. 编写 `useDebounce` Hook 的测试：
   - 输入 `"hello"` 后 300ms 内 debouncedValue 仍是 `""`
   - 300ms 后 debouncedValue 变为 `"hello"`
   - 快速连续输入时只保留最后一次
2. 编写 `useLocalStorage` Hook 的测试，包括：
   - 从 localStorage 读取初始值
   - setValue 后 localStorage 更新
   - 多个 Hook 实例共享同一 key 时保持同步
3. 为第六章中的 `useMutation` Hook 编写独立的 renderHook 测试

---

## 本章总结

- `renderHook` 从 `@testing-library/react` 导入，不再需要独立包
- `result.current` 是可变引用，**严禁解构**
- `rerender` 测试 props 变化，`unmount` 测试清理逻辑
- 异步 Hook 测试：`waitFor` 等待特定条件 + MSW 控制 API 响应
- `wrapper` 选项注入 Provider 依赖
- `waitFor` 的 callback 不应包含副作用
