---
tags:
  - 测试/Hook
  - 工具/Vitest
  - 工具/RTL
created: 2026-05-22
---

# 第8章：React Hook 测试

## 学习目标

- 掌握 `renderHook` API 的完整签名和使用方式
- 能测试简单逻辑 Hook（useCounter、useToggle）
- 能测试带副作用的 Hook（数据获取、清理）
- 能测试 Context 依赖和 Browser API 依赖的 Hook
- 能用假定时器测试 Timer 相关 Hook（useDebounce、useInterval）
- 识别 Hook 测试的反模式

---

## 8.1 renderHook 精讲

### API 签名

```typescript
import { renderHook, RenderHookOptions, RenderHookResult } from '@testing-library/react'

function renderHook<Props, Result>(
  callback: (props: Props) => Result,
  options?: RenderHookOptions<Props>,
): RenderHookResult<Result, Props>
```

### 返回值

```typescript
interface RenderHookResult<Result, Props> {
  // 当前 Hook 的返回值（每次渲染后更新）
  result: { current: Result }

  // 用新 props 重新渲染，触发 Hook 重新计算
  rerender: (newProps?: Props) => void

  // 卸载组件，触发 Hook 的清理函数
  unmount: () => void
}
```

### 核心使用模式

```typescript
import { renderHook, act } from '@testing-library/react'

// 最简单的 Hook：不接受参数
const { result } = renderHook(() => useCounter())

// 带初始参数
const { result } = renderHook(() => useCounter(10))

// 带 wrapper 注入 Provider
const { result } = renderHook(() => useTheme(), {
  wrapper: ThemeProvider,
})

// 接收动态 props（rerender 时更新）
const { result, rerender } = renderHook(
  ({ id }) => useUser(id),
  { initialProps: { id: 1 } },
)
rerender({ id: 2 }) // 触发 Hook 用新 id 重新计算
```

> **自我验证说明**：
> - `result.current` 引用的是 Hook 的返回值，不是 Hook 函数本身。每次 React 重新渲染后，`result.current` 会被更新为新的值。
> - **重要**：`result.current` 在多次渲染之间可能是同一个引用（对对象类型而言），因此不应该缓存 `const val = result.current` 然后依赖它——数组解构尤其危险。始终在断言时直接读取 `result.current`。
> - `act()` 在 Hook 测试中至关重要：任何导致 state 更新的操作（调用 Hook 返回的函数、推进假定时器）都应该包裹在 `act()` 中，确保 React 处理完所有 state 变更。

> **为什么：** 为什么 `renderHook` 需要 `wrapper` 而不是直接调用 Hook？
>
> 直接调用 Hook 函数违反了 React 的 Rules of Hooks —— "只在函数组件或自定义 Hook 中调用 Hook"。如果你尝试在普通函数中调用 `useState` 或 `useEffect`，React 会抛出 `Invalid hook call` 错误。`renderHook` 内部创建了一个**最小化函数组件**来调用你的回调，把这个组件渲染到 React 虚拟 DOM 中，从而让 Hook 在合法的 React 组件上下文中执行。
>
> ```typescript
> // renderHook 内部大致等价于：
> function TestComponent() {
>   const result = callback(props!)  // 你的 Hook 在这里被合法调用
>   useEffect(() => { /* 保证结果同步到 result.current */ })
>   return null  // 不渲染任何 DOM
> }
> ```
>
> `wrapper` 选项允许你在 TestComponent 外层包裹 Provider，等价于：
>
> ```typescript
> function TestComponentWithWrapper() {
>   return (
>     <UserProvider>     {/* wrapper 提供的 Context */}
>       <TestComponent />
>     </UserProvider>
>   )
> }
> ```
>
> 这就是 `wrapper` 能注入 Context 提供者的原因——被测试的 Hook 在 wrapper 内部渲染，可以访问 wrapper 提供的所有 Context。如果不用 `renderHook`，你需要手动创建一个测试组件、渲染它、通过 ref 或 state 暴露 Hook 的返回值——这本质上就是自己实现 `renderHook`。
>
> 另一个关键点是**生命周期管理**。直接调用 Hook 无法触发 `useEffect`——因为 `useEffect` 在组件渲染并提交到屏幕后才执行。`renderHook` 通过 React 的协调器管理渲染和 effect 执行，确保 `useEffect` 和 `useLayoutEffect` 按正确时机触发。这正是为什么 Effect Hook 测试需要 `waitFor` 的原因——`renderHook` 必须在一次完整的渲染周期后才能执行 effect。

> **Jest 对比：@testing-library/react-hooks vs renderHook 的演变**
>
> 在 React Testing Library v13 之前（约 2022 年），Hook 测试需要使用独立的包 `@testing-library/react-hooks` 提供的 `renderHook`：

> ```typescript
> // 旧方式（@testing-library/react-hooks）
> import { renderHook, act } from '@testing-library/react-hooks'
>
> const { result } = renderHook(() => useCounter())
> ```
>
> 从 v13 开始，`renderHook` 被合并到 `@testing-library/react` 中。这个合并对 Jest 和 Vitest 用户的影响相同——只需要修改导入路径。
>
> 但有一个行为差异需要注意：**旧版 `renderHook` 在 `act()` 外同步更新 `result.current`，而新版在 `act()` 外是异步的**。这是因为新版使用了 React 18 的并发特性。如果你的测试从 Jest + 旧版 react-hooks 包迁移到 Vitest + 新版 @testing-library/react，可能需要为一些之前不需要 `act()` 的断言添加 `act()` 包裹。
>
> ```typescript
> // 旧版（@testing-library/react-hooks）：可能直接断言
> act(() => { result.current.increment() })
> expect(result.current.count).toBe(1) // 同步，直接工作
>
> // 新版（@testing-library/react v14+）：需要 waitFor 或 act 包裹的断言
> act(() => { result.current.increment() })
> await waitFor(() => expect(result.current.count).toBe(1))
> // 或者仍然使用 act() 包裹 + 直接断言
> ```

### 渐进式示例：从简单 Hook 到复杂 Hook 的测试演进

同一个"计数器"概念，随着需求复杂度增长，测试策略也随之变化。

**阶段 1：纯逻辑 Hook（无副作用、无依赖）**

```typescript
// useCounter — 纯状态管理，不依赖任何外部环境
function useCounter(initial = 0) {
  const [count, setCount] = useState(initial)
  const increment = () => setCount((c) => c + 1)
  return { count, increment }
}

// 测试最简单——直接 renderHook + act + 断言
it('increments count', () => {
  const { result } = renderHook(() => useCounter(0))
  act(() => { result.current.increment() })
  expect(result.current.count).toBe(1)
})
```

**阶段 2：Context 依赖 Hook**

```typescript
// useUser — 依赖 UserContext
function useUser() {
  const { user } = useUserContext()
  return { displayName: user ? `${user.name} (${user.role})` : 'Guest' }
}

// 测试需要 wrapper 注入 Provider
it('shows display name from context', () => {
  const { result } = renderHook(() => useUser(), {
    wrapper: UserProvider,
  })
  // Provider 的初始值决定了 Hook 返回值
  expect(result.current.displayName).toBe('Guest')
})
```

**阶段 3：Timer 依赖 Hook**

```typescript
// useCountdown — 依赖 setTimeout 递减
function useCountdown(seconds: number, onComplete: () => void) {
  const [remaining, setRemaining] = useState(seconds)
  useEffect(() => {
    if (remaining <= 0) { onComplete(); return }
    const timer = setTimeout(() => setRemaining((r) => r - 1), 1000)
    return () => clearTimeout(timer)
  }, [remaining, onComplete])
  return remaining
}

// 测试需要假定时器控制时间流逝
it('counts down to zero', () => {
  vi.useFakeTimers()
  const onComplete = vi.fn()
  const { result } = renderHook(() => useCountdown(3, onComplete))

  vi.advanceTimersByTime(3000)
  expect(result.current).toBe(0)
  expect(onComplete).toHaveBeenCalled()
  vi.useRealTimers()
})
```

> **这个演进揭示的规律**：Hook 测试的复杂度与 Hook 依赖的外部环境数量正相关。纯逻辑 Hook 只需要 `renderHook` + `act`，Context 依赖需要 `wrapper`，Timer 依赖需要假定时器。每增加一种外部依赖，测试就需要多一层配置。这正是 React 设计 Hooks 的意图——将外部依赖显式化为副作用（`useEffect`、`useContext`），让测试可以针对性地提供这些依赖的替身。

---

## 8.2 简单 Hook 测试

### useCounter

```typescript
// src/hooks/useCounter.ts
import { useState, useCallback } from 'react'

export function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue)

  const increment = useCallback(() => setCount((c) => c + 1), [])
  const decrement = useCallback(() => setCount((c) => c - 1), [])
  const reset = useCallback(() => setCount(initialValue), [initialValue])

  return { count, increment, decrement, reset }
}
```

```typescript
// src/hooks/useCounter.test.ts
import { renderHook, act } from '@testing-library/react'
import { useCounter } from './useCounter'

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useCounter())

    expect(result.current.count).toBe(0)
  })

  it('initializes with custom value', () => {
    const { result } = renderHook(() => useCounter(10))

    expect(result.current.count).toBe(10)
  })

  it('increments count', () => {
    const { result } = renderHook(() => useCounter(0))

    act(() => { result.current.increment() })

    expect(result.current.count).toBe(1)
  })

  it('decrements count', () => {
    const { result } = renderHook(() => useCounter(5))

    act(() => { result.current.decrement() })

    expect(result.current.count).toBe(4)
  })

  it('resets to initial value', () => {
    const { result } = renderHook(() => useCounter(100))

    act(() => { result.current.increment() })
    expect(result.current.count).toBe(101)

    act(() => { result.current.reset() })
    expect(result.current.count).toBe(100)
  })

  it('is stable across multiple operations', () => {
    const { result } = renderHook(() => useCounter(0))

    act(() => {
      result.current.increment()
      result.current.increment()
      result.current.increment()
    })

    expect(result.current.count).toBe(3)
  })
})
```

### useToggle

```typescript
// src/hooks/useToggle.ts
import { useState, useCallback } from 'react'

export function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue)

  const toggle = useCallback(() => setValue((v) => !v), [])
  const setTrue = useCallback(() => setValue(true), [])
  const setFalse = useCallback(() => setValue(false), [])

  return { value, toggle, setTrue, setFalse }
}
```

```typescript
// src/hooks/useToggle.test.ts
import { renderHook, act } from '@testing-library/react'
import { useToggle } from './useToggle'

describe('useToggle', () => {
  it('initializes with false by default', () => {
    const { result } = renderHook(() => useToggle())

    expect(result.current.value).toBe(false)
  })

  it('toggles from false to true', () => {
    const { result } = renderHook(() => useToggle(false))

    act(() => { result.current.toggle() })

    expect(result.current.value).toBe(true)
  })

  it('toggles multiple times', () => {
    const { result } = renderHook(() => useToggle(false))

    act(() => { result.current.toggle() })  // true
    act(() => { result.current.toggle() })  // false
    act(() => { result.current.toggle() })  // true

    expect(result.current.value).toBe(true)
  })

  it('sets to true and false directly', () => {
    const { result } = renderHook(() => useToggle(false))

    act(() => { result.current.setTrue() })
    expect(result.current.value).toBe(true)

    act(() => { result.current.setFalse() })
    expect(result.current.value).toBe(false)
  })
})
```

> **自我验证说明**：
> - 在简单 Hook 测试中，`act()` 包裹在调用 Hook 返回的函数外部。如果不用 `act()`，Vitest 会抛出 `act()` 警告，提示有未包裹的 state 更新。
> - 多个操作可以放在同一个 `act()` 回调中：`act(() => { increment(); increment(); })`。React 会在一次 `act()` 中批量处理所有 state 更新。
> - 注意没有使用 `waitFor`——这些操作是同步的，state 更新在 `act()` 返回后立即生效。

---

## 8.3 Effect Hook 测试

### 数据获取 Hook

```typescript
// src/hooks/useFetch.ts
import { useState, useEffect } from 'react'

interface UseFetchState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export function useFetch<T>(url: string): UseFetchState<T> {
  const [state, setState] = useState<UseFetchState<T>>({
    data: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let ignore = false
    setState({ data: null, loading: true, error: null })

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json() as T
      })
      .then((data) => {
        if (!ignore) setState({ data, loading: false, error: null })
      })
      .catch((error) => {
        if (!ignore) setState({ data: null, loading: false, error })
      })

    return () => { ignore = true }
  }, [url])

  return state
}
```

```typescript
// src/hooks/useFetch.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useFetch } from './useFetch'

interface Todo {
  id: number
  title: string
  completed: boolean
}

describe('useFetch', () => {
  it('fetches data successfully', async () => {
    server.use(
      http.get('/api/todos', () => {
        return HttpResponse.json<Todo[]>([
          { id: 1, title: 'Learn testing', completed: false },
        ])
      }),
    )

    const { result } = renderHook(() => useFetch<Todo[]>('/api/todos'))

    // 初始加载中
    expect(result.current.loading).toBe(true)
    expect(result.current.data).toBeNull()

    // 等待加载完成
    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data![0].title).toBe('Learn testing')
    expect(result.current.error).toBeNull()
  })

  it('handles fetch error', async () => {
    server.use(
      http.get('/api/todos', () => {
        return new HttpResponse(null, { status: 500 })
      }),
    )

    const { result } = renderHook(() => useFetch<Todo[]>('/api/todos'))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data).toBeNull()
    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toContain('500')
  })

  it('refetches when url changes', async () => {
    const { result, rerender } = renderHook(
      ({ url }) => useFetch<Todo[]>(url),
      { initialProps: { url: '/api/todos/1' } },
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    // 切换 URL
    rerender({ url: '/api/todos/2' })

    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))
  })

  it('cleans up on unmount', () => {
    const { result, unmount } = renderHook(() => useFetch<Todo[]>('/api/todos'))

    // unmount 应该在 loading 完成前调用
    unmount()

    // 卸载后 result.current 不再更新，所以无法断言
    // 但我们可以验证 unmount 不会抛出错误（清理函数正常执行）
    expect(() => unmount()).not.toThrow()
  })
})
```

### 清理函数验证

```typescript
// src/hooks/useSubscription.ts
import { useEffect } from 'react'

export function useSubscription(
  channel: string,
  onMessage: (data: unknown) => void,
) {
  useEffect(() => {
    const subscription = { channel, id: Date.now() }
    console.log('Subscribed to', channel)

    // 模拟订阅
    const interval = setInterval(() => {
      onMessage({ channel, time: Date.now() })
    }, 1000)

    return () => {
      clearInterval(interval)
      console.log('Unsubscribed from', channel)
    }
  }, [channel, onMessage])
}
```

```typescript
// src/hooks/useSubscription.test.ts
import { renderHook } from '@testing-library/react'
import { useSubscription } from './useSubscription'

describe('useSubscription', () => {
  it('cleans up subscription on unmount', () => {
    const onMessage = vi.fn()
    const consoleSpy = vi.spyOn(console, 'log')

    const { unmount } = renderHook(
      ({ channel }) => useSubscription(channel, onMessage),
      { initialProps: { channel: 'test-channel', onMessage } },
    )

    expect(consoleSpy).toHaveBeenCalledWith('Subscribed to', 'test-channel')

    unmount()

    expect(consoleSpy).toHaveBeenCalledWith('Unsubscribed from', 'test-channel')

    consoleSpy.mockRestore()
  })

  it('resubscribes when channel changes', () => {
    const onMessage = vi.fn()
    const consoleSpy = vi.spyOn(console, 'log')

    const { rerender } = renderHook(
      ({ channel }) => useSubscription(channel, onMessage),
      { initialProps: { channel: 'channel-a', onMessage } },
    )

    expect(consoleSpy).toHaveBeenCalledWith('Subscribed to', 'channel-a')

    rerender({ channel: 'channel-b', onMessage })

    expect(consoleSpy).toHaveBeenCalledWith('Unsubscribed from', 'channel-a')
    expect(consoleSpy).toHaveBeenCalledWith('Subscribed to', 'channel-b')

    consoleSpy.mockRestore()
  })
})
```

> **自我验证说明**：
> - Effect Hook 测试的核心挑战是时序。`useEffect` 在渲染后才执行，所以 `result.current.loading` 初始值检查必须在 `waitFor` 之前。
> - 清理函数验证有两种方式：`unmount()` 后检查副作用是否被清理；或者改变依赖重新触发 effect，验证旧 side effect 被清理。
> - 使用 `vi.spyOn(console, 'log')` 验证副作用的调用是合理的——我们测试的是 Hook 的行为（"是否在卸载时取消订阅"），不是实现细节。

---

## 8.4 Context 依赖 Hook 测试

### Context Provider 注入

```typescript
// src/contexts/UserContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react'

interface User {
  id: number
  name: string
  role: 'admin' | 'user'
}

interface UserContextValue {
  user: User | null
  setUser: (user: User | null) => void
}

const UserContext = createContext<UserContextValue | null>(null)

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUserContext(): UserContextValue {
  const ctx = useContext(UserContext)
  if (!ctx) throw new Error('useUserContext must be used within UserProvider')
  return ctx
}
```

```typescript
// src/contexts/useUserContext.test.ts
import { renderHook, act } from '@testing-library/react'
import { useUserContext, UserProvider } from './UserContext'

describe('useUserContext', () => {
  it('provides user from context', () => {
    const { result } = renderHook(() => useUserContext(), {
      wrapper: UserProvider,
    })

    expect(result.current.user).toBeNull()
  })

  it('updates user via context', () => {
    const { result } = renderHook(() => useUserContext(), {
      wrapper: UserProvider,
    })

    act(() => {
      result.current.setUser({ id: 1, name: 'Alice', role: 'admin' })
    })

    expect(result.current.user).toEqual({
      id: 1,
      name: 'Alice',
      role: 'admin',
    })
  })

  it('throws error when used outside provider', () => {
    // 不使用 wrapper，直接在无 Provider 的环境下渲染
    expect(() => renderHook(() => useUserContext())).toThrow(
      'useUserContext must be used within UserProvider',
    )
  })
})
```

### 自定义 Context Value

有时需要测试特定 Context value 下的 Hook 行为，可以通过自定义 wrapper 实现：

```typescript
// 使用自定义 wrapper 注入特定值
it('works with a specific context value', () => {
  const testUser: User = { id: 99, name: 'Test', role: 'admin' }

  const { result } = renderHook(() => useUserContext(), {
    wrapper: ({ children }) => (
      <UserContext.Provider value={{ user: testUser, setUser: vi.fn() }}>
        {children}
      </UserContext.Provider>
    ),
  })

  expect(result.current.user).toEqual(testUser)
})
```

### Context Value 变化

```typescript
// 测试 Context value 变化后 Hook 的响应
it('reacts to context value changes', () => {
  const { result, rerender } = renderHook(
    ({ user }) => useCustomHook(user),
    {
      initialProps: { user: { id: 1, name: 'Alice', role: 'user' as const } },
      wrapper: ({ children }) => <>{children}</>, // 或者不需要 wrapper
    },
  )

  // 初始值
  expect(result.current.isAdmin).toBe(false)

  // 更新 props，模拟 context 变化
  rerender({ user: { id: 1, name: 'Alice', role: 'admin' as const } })

  expect(result.current.isAdmin).toBe(true)
})
```

> **自我验证说明**：
> - `wrapper` 组件接收 `{ children }` props，包裹渲染 Hook 的组件。在 Hook 测试中，被测试的 Hook 会在 wrapper 内部渲染。
> - 自定义 wrapper 可以接受外部传入的 props（通过闭包），也可以直接在 wrapper 组件内部写死值。
> - 测试 "Context 未提供" 的场景很重要——这验证了你的错误提示是否清晰。

---

## 8.5 Browser API 依赖 Hook 测试

### useMediaQuery

```typescript
// src/hooks/useMediaQuery.ts
import { useState, useEffect } from 'react'

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const mql = window.matchMedia(query)
    setMatches(mql.matches)

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
    mql.addEventListener('change', handler)

    return () => mql.removeEventListener('change', handler)
  }, [query])

  return matches
}
```

```typescript
// src/hooks/useMediaQuery.test.ts
import { renderHook, act } from '@testing-library/react'
import { useMediaQuery } from './useMediaQuery'

describe('useMediaQuery', () => {
  // 保存原始 matchMedia
  const originalMatchMedia = window.matchMedia

  afterEach(() => {
    window.matchMedia = originalMatchMedia
  })

  it('returns true when media query matches', () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))

    const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))

    expect(result.current).toBe(true)
  })

  it('returns false when media query does not match', () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))

    const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))

    expect(result.current).toBe(false)
  })

  it('responds to media query changes', () => {
    const listeners: Array<() => void> = []
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn((_: string, cb: () => void) => {
        listeners.push(cb)
      }),
      removeEventListener: vi.fn(),
    }))

    const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))

    expect(result.current).toBe(false)

    // 模拟媒体查询变化
    act(() => {
      // 重新 mock matches 为 true
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: true,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }))
      // 触发所有 listener
      listeners.forEach((cb) => cb())
    })

    // 注意：上述实现可能不会更新 result，因为 Hook 中的 addEventListener
    // 回调使用的是闭包中的 mql。
    // 更准确的测试应该触发实际的 MediaQueryListEvent
  })
})
```

更精确的测试方式：

```typescript
it('responds to media query change events', () => {
  type Listener = (event: { matches: boolean }) => void
  const listeners = new Set<Listener>()

  const mockMql = {
    matches: false,
    media: '(min-width: 768px)',
    addEventListener: vi.fn((_: string, cb: Listener) => listeners.add(cb)),
    removeEventListener: vi.fn((_: string, cb: Listener) => listeners.delete(cb)),
  }

  window.matchMedia = vi.fn().mockReturnValue(mockMql)

  const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))

  expect(result.current).toBe(false)

  // 通过触发 listener 模拟媒体查询变化
  act(() => {
    listeners.forEach((cb) => cb({ matches: true }))
  })

  expect(result.current).toBe(true)
})
```

### useLocalStorage

```typescript
// src/hooks/useLocalStorage.ts
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored !== null ? JSON.parse(stored) : initialValue
    } catch {
      return initialValue
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // localStorage 满时静默失败
    }
  }, [key, value])

  return [value, setValue] as const
}
```

```typescript
// src/hooks/useLocalStorage.test.ts
import { renderHook, act } from '@testing-library/react'
import { useLocalStorage } from './useLocalStorage'

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('uses initial value when nothing is stored', () => {
    const { result } = renderHook(() => useLocalStorage('theme', 'light'))

    expect(result.current[0]).toBe('light')
  })

  it('reads existing value from localStorage', () => {
    localStorage.setItem('theme', JSON.stringify('dark'))

    const { result } = renderHook(() => useLocalStorage('theme', 'light'))

    expect(result.current[0]).toBe('dark')
  })

  it('persists value to localStorage on change', () => {
    const { result } = renderHook(() => useLocalStorage('theme', 'light'))

    act(() => {
      result.current[1]('dark')
    })

    expect(result.current[0]).toBe('dark')
    expect(JSON.parse(localStorage.getItem('theme')!)).toBe('dark')
  })

  it('handles JSON parse errors gracefully', () => {
    localStorage.setItem('config', '{invalid json}')

    const { result } = renderHook(() => useLocalStorage('config', { retries: 3 }))

    expect(result.current[0]).toEqual({ retries: 3 })
  })
})
```

> **自我验证说明**：
> - `vi.spyOn(window, 'matchMedia')` 是 mock browser API 的标准方式。返回的 mock 对象必须包含 `matches`、`addEventListener`、`removeEventListener` 三个属性。
> - `localStorage` 的 `clear()` 在每个测试前调用，确保测试间隔离。jsdom 提供了完整的 `localStorage` 实现，不需要额外 mock。
> - 对于 `useLocalStorage`，验证 `localStorage.setItem` 确实被调用比只检查 Hook 返回值更重要——持久化是 localStorage Hook 的核心功能。

---

## 8.6 Timer 依赖 Hook 测试

### useDebounce

```typescript
// src/hooks/useDebounce.ts
import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
```

```typescript
// src/hooks/useDebounce.test.ts
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
    const { result } = renderHook(() => useDebounce('hello', 300))

    expect(result.current).toBe('hello')
  })

  it('does not update before delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'hello' } },
    )

    rerender({ value: 'world' })

    // 延迟时间还没到，值不变
    vi.advanceTimersByTime(299)
    expect(result.current).toBe('hello')
  })

  it('updates after the delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'hello' } },
    )

    rerender({ value: 'world' })

    vi.advanceTimersByTime(300)

    expect(result.current).toBe('world')
  })

  it('resets timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } },
    )

    rerender({ value: 'ab' })
    vi.advanceTimersByTime(100)

    rerender({ value: 'abc' })
    vi.advanceTimersByTime(100)

    rerender({ value: 'abcd' })
    vi.advanceTimersByTime(100)

    // 总共只过了 300ms，但每次 rerender 都重置了 timer
    // 所以 300ms 时 debounce timer 刚启动 100ms
    expect(result.current).toBe('a')

    // 再等 200ms，触发最后一次 timer
    vi.advanceTimersByTime(200)

    expect(result.current).toBe('abcd')
  })
})
```

### useInterval

```typescript
// src/hooks/useInterval.ts
import { useEffect, useRef } from 'react'

export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (delay === null) return

    const id = setInterval(() => savedCallback.current(), delay)
    return () => clearInterval(id)
  }, [delay])
}
```

```typescript
// src/hooks/useInterval.test.ts
import { renderHook } from '@testing-library/react'
import { useInterval } from './useInterval'

describe('useInterval', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls callback repeatedly at interval', () => {
    const callback = vi.fn()

    renderHook(() => useInterval(callback, 1000))

    expect(callback).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(2)
  })

  it('stops when delay is null', () => {
    const callback = vi.fn()

    const { rerender } = renderHook(
      ({ delay }) => useInterval(callback, delay),
      { initialProps: { delay: 1000 as number | null } },
    )

    vi.advanceTimersByTime(3000)
    expect(callback).toHaveBeenCalledTimes(3)

    // 停止 interval
    rerender({ delay: null })

    vi.advanceTimersByTime(5000)
    // 停止后不再调用
    expect(callback).toHaveBeenCalledTimes(3)
  })

  it('does not start interval when delay is null initially', () => {
    const callback = vi.fn()

    renderHook(() => useInterval(callback, null))

    vi.advanceTimersByTime(10000)
    expect(callback).not.toHaveBeenCalled()
  })
})
```

### useThrottle

```typescript
// src/hooks/useThrottle.ts
import { useState, useEffect, useRef } from 'react'

export function useThrottle<T>(value: T, delay: number): T {
  const [throttled, setThrottled] = useState(value)
  const lastRan = useRef(Date.now())

  useEffect(() => {
    const now = Date.now()
    const remaining = delay - (now - lastRan.current)

    if (remaining <= 0) {
      setThrottled(value)
      lastRan.current = now
    }
  }, [value, delay])

  return throttled
}
```

```typescript
// src/hooks/useThrottle.test.ts
describe('useThrottle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(0) // 固定时间起点
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('updates immediately on first change', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useThrottle(value, 1000),
      { initialProps: { value: 'initial' } },
    )

    rerender({ value: 'updated' })

    expect(result.current).toBe('updated')
  })

  it('ignores rapid changes within throttle window', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useThrottle(value, 1000),
      { initialProps: { value: 'a' } },
    )

    rerender({ value: 'b' })
    expect(result.current).toBe('b') // 第一次立即更新

    rerender({ value: 'c' })
    // 还在 throttle window 内，不更新
    expect(result.current).toBe('b')
  })
})
```

> **自我验证说明**：
> - 假定时器的配对使用是硬性要求：`beforeEach(() => vi.useFakeTimers())` + `afterEach(() => vi.useRealTimers())`。忘记恢复假定时器会导致后续测试的 `setTimeout` 永远不会触发。
> - `vi.advanceTimersByTime(ms)` 同步推进时间，触发所有到期的定时器回调。debounce 的 "重置" 行为测试了多次 `rerender` 在 delay 窗口内不断重置 timer。
> - `useInterval` 测试中，`vi.advanceTimersByTime(3000)` 会触发三次 `setInterval` 回调（每秒一次）。注意 `setInterval` 是第一次延迟后开始调用，不是立即。
> - `act()` 在假定时器测试中通常不是必需的，因为 `advanceTimersByTime` 是同步的。但在一些复杂场景中（timer 回调触发了 React state 更新后需要断言），用 `act()` 包裹更安全。

> **Jest 对比：vi.useFakeTimers 与 jest.useFakeTimers 的配置差异**
>
> 从 Jest 迁移时需要注意一个关键差异：**Jest 27+ 默认使用 `@sinonjs/fake-timers`，而 Vitest 也使用相同的底层库，但配置参数名不同。**
>
> ```typescript
> // Jest 方式：配置通过参数对象
> jest.useFakeTimers({
>   legacyFakeTimers: false,      // 使用 @sinonjs/fake-timers（非旧版）
>   advanceTimers: false,         // 是否自动推进
>   doNotFake: ['nextTick'],      // 排除的定时器
> })
>
> // Vitest 方式：配置通过 toFake / toReal
> vi.useFakeTimers({
>   toFake: ['setTimeout', 'setInterval', 'clearTimeout', 'Date'],
>   shouldAdvanceTime: false,
> })
> ```
>
> **实践建议**：如果你的测试依赖 `Date.now()`（如 `useThrottle` 中的例子），在 Jest 中需要额外 mock `Date`，而在 Vitest 中只需调用 `vi.setSystemTime(0)` 固定时间起点。`vi.setSystemTime` 是 Vitest 独有的 API，Jest 没有直接等效方法。
>
> ```typescript
> // Vitest 独有：固定 Date.now() 返回值
> vi.useFakeTimers()
> vi.setSystemTime(new Date('2026-01-01'))
>
> // Jest 中需要额外 mock Date
> jest.useFakeTimers()
> jest.setSystemTime(new Date('2026-01-01')) // Jest 27+ 也支持
> ```

---

## 8.7 反模式

### 反模式 1：直接调用 Hook 函数

```typescript
// ❌ 直接调用 Hook（违反了 React 的规则）
const { count, increment } = useCounter()
act(() => { increment() })
expect(count).toBe(1)

// 问题：React 的 Rules of Hooks 要求 Hook 在组件中调用
// 直接调用会报错：Invalid hook call

// ✅ 通过 renderHook
const { result } = renderHook(() => useCounter())
act(() => { result.current.increment() })
expect(result.current.count).toBe(1)
```

### 反模式 2：在 act() 外部修改 Hook 状态

```typescript
// ❌ 不使用 act()
const { result } = renderHook(() => useCounter())
result.current.increment()
expect(result.current.count).toBe(1)

// 问题：React 会给出 act() 警告，在某些情况下断言可能失败
// 因为 state 更新未同步

// ✅ 使用 act()
const { result } = renderHook(() => useCounter())
act(() => { result.current.increment() })
expect(result.current.count).toBe(1)
```

### 反模式 3：测试 Hook 内部实现细节

```typescript
// ❌ 测试 Hook 内部使用了什么
// 测试检查了 useState 是否被调用、useEffect 是否返回清理函数等
const spy = vi.spyOn(React, 'useEffect')
renderHook(() => useDebounce('hello', 300))
expect(spy).toHaveBeenCalledTimes(2) // 实现细节！

// ✅ 测试 Hook 的行为
const { result, rerender } = renderHook(
  ({ value }) => useDebounce(value, 300),
  { initialProps: { value: 'hello' } },
)
rerender({ value: 'world' })
vi.advanceTimersByTime(300)
expect(result.current).toBe('world') // 行为：值在延迟后更新
```

### 反模式 4：在非 jsdom 环境测试 Browser API Hook

```typescript
// ❌ 在 node 环境下运行
// @vitest-environment node
it('tests useMediaQuery', () => {
  const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))
  // 报错：window is not defined
})

// ✅ 设置正确的环境
// @vitest-environment jsdom
it('tests useMediaQuery', () => {
  window.matchMedia = vi.fn().mockReturnValue({ matches: true, ... })
  const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'))
  expect(result.current).toBe(true)
})
```

---

## 8.8 本章练习

1. 为以下 Hook 编写测试：
   - `usePrevious<T>(value: T): T | undefined` — 返回上一次渲染时的值
   - `useDocumentTitle(title: string): void` — 设置 `document.title`

2. 为 `useLocalStorage` 编写测试，覆盖以下场景：
   - localStorage 存储空间满时（`setItem` 抛出异常）的降级行为
   - 多个 key 之间的隔离性
   - 值为复杂对象（嵌套结构）的序列化与反序列化

3. 使用假定时器测试一个 `useCountdown(seconds: number)` Hook，它从指定秒数递减到 0 并调用 `onComplete` 回调。

4. 思考题：为什么 `renderHook` 在测试 Effect Hook 时需要配合 `waitFor`，而测试简单 Hook 时不需要？

---

## 8.9 本章总结

- `renderHook` 的三个返回值：`result.current` 读取最新值、`rerender` 更新 props、`unmount` 触发清理
- 简单 Hook 测试用 `act()` 包裹状态变更回调，直接断言 `result.current`
- Effect Hook 测试需要 `waitFor` 等待副作用完成，验证清理函数在 `unmount` 时被调用
- Context Hook 测试通过 `wrapper` 选项注入 Provider，也可以自定义 wrapper 注入特定值
- Browser API Hook 测试用 `vi.spyOn` 或直接赋值 `window.matchMedia`，注意 jsdom 环境要求
- Timer Hook 测试用 `vi.useFakeTimers()` + `vi.advanceTimersByTime()`，必须配对 `useRealTimers()`
- 反模式：直接调用 Hook、跳过 `act()`、测试实现细节、错误的环境

## 关联阅读

- [第3章：Vitest基础](03-Vitest基础.md) — vi.fn 和假定时器基础
- [第7章：数据层测试](07-数据层测试.md) — useFetch 数据 Hook 测试
- [第11章：状态管理测试](11-状态管理测试.md) — Context wrapper 进阶
