---
tags:
  - tutorial
  - vitest
created: 2026-05-22
---

# 第二章：Vitest 基础

## 学习目标

- 掌握 Vitest 的断言 API 和匹配器分类
- 理解测试套件的组织结构（describe/it/beforeEach 等）
- 熟练使用 vi.fn、vi.spyOn、vi.mock 创建和管理模拟
- 掌握定时器模拟（fake timers）与异步测试
- 理解覆盖率配置与意义

---

## 2.1 断言与匹配器

Vitest 的断言语法与 Jest **完全兼容**。如果你从 Jest 迁移，几乎不需要学习成本。

### 基础比较

```typescript
describe('Basic Matchers', () => {
  it('toBe — 严格相等（===）', () => {
    expect(2 + 2).toBe(4)
    expect('hello').toBe('hello')
    // expect({ a: 1 }).toBe({ a: 1 }) // ❌ 失败！对象引用不同
  })

  it('toEqual — 深度相等（值相同即可）', () => {
    expect({ a: 1, b: [2, 3] }).toEqual({ a: 1, b: [2, 3] }) // ✅
    expect([1, 2, 3]).toEqual([1, 2, 3])                        // ✅
  })

  it('toStrictEqual — 严格深度相等（含 undefined 属性检查）', () => {
    expect({ a: 1, b: undefined }).toEqual({ a: 1 })        // ✅ 通过
    expect({ a: 1, b: undefined }).toStrictEqual({ a: 1 })  // ❌ 失败
    // toStrictEqual 要求结构完全一致
  })
})
```

> **自我验证说明**：`toBe`、`toEqual`、`toStrictEqual` 是 Vitest 内建匹配器，继承自 Chai，与 Jest 行为完全一致。

### 真假值

```typescript
describe('Truthiness', () => {
  it('toBeTruthy / toBeFalsy', () => {
    expect('hello').toBeTruthy()
    expect('').toBeFalsy()
    expect(0).toBeFalsy()
    expect(null).toBeFalsy()
    expect(undefined).toBeFalsy()
  })

  it('toBeNull / toBeUndefined / toBeDefined', () => {
    expect(null).toBeNull()
    expect(undefined).toBeUndefined()
    expect('hello').toBeDefined()
  })
})
```

### 数值

```typescript
describe('Numbers', () => {
  it('基础比较', () => {
    expect(5).toBeGreaterThan(3)
    expect(5).toBeGreaterThanOrEqual(5)
    expect(5).toBeLessThan(10)
    expect(5).toBeLessThanOrEqual(5)
  })

  it('浮点数 — 用 toBeCloseTo 而非 toBe', () => {
    // expect(0.1 + 0.2).toBe(0.3) // ❌ 失败：浮点数精度
    expect(0.1 + 0.2).toBeCloseTo(0.3) // ✅
    expect(0.1 + 0.2).toBeCloseTo(0.3, 5) // 第二个参数是小数位数精度
  })
})
```

### 字符串与数组

```typescript
describe('Strings & Arrays', () => {
  it('字符串匹配', () => {
    expect('Hello, World!').toMatch(/world/i)
    expect('Hello, World!').toContain('World')
  })

  it('数组', () => {
    const items = ['apple', 'banana', 'orange']
    expect(items).toHaveLength(3)
    expect(items).toContain('banana')
    expect(items).toContainEqual('orange') // 与 toContain 等价于基本类型
  })

  it('对象数组 — toContainEqual', () => {
    const users = [
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' },
    ]
    expect(users).toHaveLength(2)
    expect(users).toContainEqual({ id: 1, name: 'Alice' })
  })
})
```

### 异常

```typescript
describe('Error Handling', () => {
  function throwError(message: string): never {
    throw new Error(message)
  }

  it('toThrow — 验证异常被抛出', () => {
    expect(() => throwError('oops')).toThrow()
    expect(() => throwError('oops')).toThrow('oops')
    expect(() => throwError('oops')).toThrow(/oops/)
  })

  it('验证特定错误类型', () => {
    expect(() => {
      throw new TypeError('wrong type')
    }).toThrow(TypeError)
  })
})
```

### DOM 扩展匹配器

通过 `@testing-library/jest-dom/vitest` 注册的自定义匹配器：

```typescript
describe('DOM Matchers', () => {
  it('toBeInTheDocument — 元素在 DOM 中', () => {
    render(<div>Hello</div>)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('toHaveTextContent — 元素包含文本', () => {
    render(<button>Click me</button>)
    expect(screen.getByRole('button')).toHaveTextContent('Click')
  })

  it('toBeDisabled / toBeEnabled', () => {
    render(<button disabled>Submit</button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('toHaveAttribute — 元素有特定属性', () => {
    render(<a href="/home">Home</a>)
    expect(screen.getByRole('link')).toHaveAttribute('href', '/home')
  })

  it('toHaveClass — 元素有特定 CSS 类', () => {
    render(<div className="container active">Content</div>)
    expect(screen.getByText('Content')).toHaveClass('active')
  })
})
```

> **自我验证说明**：`toBeInTheDocument`、`toHaveTextContent`、`toBeDisabled` 等来自 `@testing-library/jest-dom` v6.x，通过 `import '@testing-library/jest-dom/vitest'` 注册到 Vitest。

---

## 2.2 测试组织

### describe 与 it

```typescript
describe('UserService', () => {
  // describe 块创建测试分组，可嵌套
  // it 和 test 完全等价，选择一种保持一致性即可

  describe('getUser', () => {
    it('returns user when found', () => { /* ... */ })
    it('throws when user not found', () => { /* ... */ })
  })

  describe('createUser', () => {
    it('creates user with valid data', () => { /* ... */ })
    it('rejects duplicate email', () => { /* ... */ })
  })
})
```

### 生命周期钩子

```typescript
describe('Lifecycle Demo', () => {
  let counter: number

  // 所有测试之前，只执行一次
  beforeAll(() => {
    console.log('beforeAll — 建立数据库连接')
  })

  // 每个测试之前都执行
  beforeEach(() => {
    counter = 0
    console.log('beforeEach — 重置计数器')
  })

  // 每个测试之后都执行
  afterEach(() => {
    console.log('afterEach — 清理测试数据')
  })

  // 所有测试之后，只执行一次
  afterAll(() => {
    console.log('afterAll — 关闭数据库连接')
  })

  it('increments counter', () => {
    counter++
    expect(counter).toBe(1)
  })

  it('starts from zero each time', () => {
    expect(counter).toBe(0) // beforeEach 保证了这一点
  })
})
```

**执行顺序**（关键！）：

```
outer beforeAll
  outer beforeEach
    inner beforeAll
      inner beforeEach
        test 1
      inner afterEach
    inner afterAll
  outer afterEach
  outer beforeEach
    inner beforeAll
      inner beforeEach
        test 2
      inner afterEach
    inner afterAll
  outer afterEach
outer afterAll
```

### test.each：参数化测试

消除重复测试代码的最佳工具：

```typescript
describe('validateEmail', () => {
  const testCases = [
    { email: 'user@example.com', expected: true, desc: 'standard email' },
    { email: 'user+tag@example.com', expected: true, desc: 'email with tag' },
    { email: 'user@sub.example.com', expected: true, desc: 'subdomain email' },
    { email: '', expected: false, desc: 'empty string' },
    { email: 'not-an-email', expected: false, desc: 'no @ sign' },
    { email: '@example.com', expected: false, desc: 'missing local part' },
    { email: 'user@', expected: false, desc: 'missing domain' },
  ] as const

  test.each(testCases)(
    '$desc: $email → $expected',
    ({ email, expected }) => {
      expect(validateEmail(email)).toBe(expected)
    }
  )
})
```

`test.each` 的两种语法：

```typescript
// 方式一：数组参数
test.each([
  [1, 1, 2],
  [1, 2, 3],
  [2, 3, 5],
])('add(%i, %i) = %i', (a, b, expected) => {
  expect(add(a, b)).toBe(expected)
})

// 方式二：对象参数（更可读，推荐）
test.each([
  { a: 1, b: 1, expected: 2 },
  { a: 1, b: 2, expected: 3 },
])('add($a, $b) = $expected', ({ a, b, expected }) => {
  expect(add(a, b)).toBe(expected)
})
```

### test.skip / test.only / test.todo

```typescript
describe('Test Modifiers', () => {
  // skip：暂时跳过（适用于已知 bug、功能未完成等）
  it.skip('feature not implemented yet', () => {
    // 不会执行
  })

  // only：只运行这个测试（调试时用，切勿提交到仓库）
  // it.only('debug this test', () => { ... })

  // todo：占位符——记录应该写但还没写的测试
  it.todo('should handle network timeout gracefully')
  it.todo('should retry on 429 rate limit')
})
```

---

## 2.3 Mock 函数：vi.fn 与 vi.spyOn

### vi.fn 基础

```typescript
describe('vi.fn', () => {
  it('创建独立的 mock 函数', () => {
    const mockFn = vi.fn()
    mockFn('hello', 42)

    expect(mockFn).toHaveBeenCalled()
    expect(mockFn).toHaveBeenCalledTimes(1)
    expect(mockFn).toHaveBeenCalledWith('hello', 42)
  })

  it('mockReturnValue — 设置返回值', () => {
    const mockFn = vi.fn().mockReturnValue('mocked')
    expect(mockFn()).toBe('mocked')
    expect(mockFn(1, 2, 3)).toBe('mocked') // 参数被忽略
  })

  it('mockImplementation — 自定义行为', () => {
    const mockFn = vi.fn((x: number) => x * 2)
    expect(mockFn(5)).toBe(10)
    expect(mockFn(100)).toBe(200)
  })

  it('mockResolvedValue / mockRejectedValue — 异步', async () => {
    const mockFn = vi.fn().mockResolvedValue({ id: 1, name: 'Alice' })
    const result = await mockFn()
    expect(result).toEqual({ id: 1, name: 'Alice' })

    const errorFn = vi.fn().mockRejectedValue(new Error('Network error'))
    await expect(errorFn()).rejects.toThrow('Network error')
  })

  it('mockReturnValueOnce — 序列返回值', () => {
    const mockFn = vi.fn()
      .mockReturnValueOnce('first call')
      .mockReturnValueOnce('second call')
      .mockReturnValue('default')

    expect(mockFn()).toBe('first call')
    expect(mockFn()).toBe('second call')
    expect(mockFn()).toBe('default')
    expect(mockFn()).toBe('default')
  })
})
```

### vi.spyOn 基础

`vi.spyOn` 监听**已有对象的方法**，而不替换整个函数：

```typescript
describe('vi.spyOn', () => {
  it('监听对象方法', () => {
    const calculator = {
      add: (a: number, b: number) => a + b,
    }

    const spy = vi.spyOn(calculator, 'add')
    const result = calculator.add(2, 3)

    expect(result).toBe(5)            // 原函数仍然正常执行
    expect(spy).toHaveBeenCalledWith(2, 3)
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('替换实现但不替换整个对象', () => {
    const api = {
      fetchUser: (id: string) => Promise.resolve({ id, name: 'John' }),
    }

    const spy = vi.spyOn(api, 'fetchUser').mockResolvedValue({ id: '1', name: 'Mocked' })

    // 原始实现被替换
    const user = await api.fetchUser('1')
    expect(user.name).toBe('Mocked')
    expect(spy).toHaveBeenCalledWith('1')
  })
})
```

### mockClear vs mockReset vs mockRestore

这三个方法经常被混淆，它们的区别至关重要：

```typescript
describe('Mock Cleanup Methods', () => {
  const mockFn = vi.fn()

  // mockFn.mock.calls:      [[arg1, arg2], ...] 所有调用的参数记录
  // mockFn.mock.results:    [{ type: 'return', value: ... }, ...] 返回值记录
  // mockFn.mock.instances:  [instance1, ...] 通过 new 创建的实例
  // mockFn.mock.contexts:   [context1, ...] this 上下文

  it('mockClear — 清除调用记录，保留实现', () => {
    mockFn.mockReturnValue('hello')
    mockFn('arg1')

    mockFn.mockClear()

    expect(mockFn).not.toHaveBeenCalled()           // 调用记录已清除
    expect(mockFn()).toBe('hello')                  // 实现仍在
  })

  // mockReset — 清除调用记录 + 清除实现（回退到返回 undefined 的空函数）
  // mockRestore — 清除记录 + 恢复原始实现（仅对 spyOn 有效）
})
```

最佳实践：在 `afterEach` 中统一清理。

---

## 2.4 模块 Mock：vi.mock

`vi.mock` 替换整个模块。Vitest 会自动将其**提升（hoist）到文件顶部**，在 imports 之前执行。

```typescript
// 自动提升到顶层，在 import 之前执行
vi.mock('./api', () => ({
  fetchUsers: vi.fn().mockResolvedValue([
    { id: 1, name: 'Alice' },
  ]),
}))

import { fetchUsers } from './api'
// fetchUsers 此时已经是 mock 版本

it('uses mocked fetchUsers', async () => {
  const users = await fetchUsers()
  expect(users).toHaveLength(1)
  expect(vi.mocked(fetchUsers)).toHaveBeenCalled()
})
```

### vi.importActual：部分 Mock

```typescript
// 只 mock 部分导出，其余保持原样
vi.mock('./api', async () => {
  const actual = await vi.importActual<typeof import('./api')>('./api')
  return {
    ...actual,
    fetchUsers: vi.fn().mockResolvedValue([]), // 只 mock 这一个
  }
})
```

### vi.mock 与 MSW 的分工

这是一个重要的架构决策：

| 场景 | 用 vi.mock | 用 MSW |
|---|---|---|
| 网络请求（fetch/axios 等） | ❌ | ✅ |
| 文件系统 (fs) | ✅ | ❌ |
| 环境变量 | ✅ | ❌ |
| 日期/时间 | ✅ | ❌ |
| 第三方 SDK（无 HTTP 层） | ✅ | ❌ |
| 纯业务逻辑函数 | ✅ | ❌ |

**经验法则**：能通过网络层解决的问题用 MSW，其余的用 vi.mock。

---

## 2.5 定时器模拟

```typescript
describe('Fake Timers', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('vi.advanceTimersByTime — 快进指定毫秒', () => {
    const callback = vi.fn()
    setTimeout(callback, 1000)

    expect(callback).not.toHaveBeenCalled()
    vi.advanceTimersByTime(500)
    expect(callback).not.toHaveBeenCalled()
    vi.advanceTimersByTime(500)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('vi.advanceTimersToNextTimer — 跳到下一个定时器', () => {
    const callback1 = vi.fn()
    const callback2 = vi.fn()

    setTimeout(callback1, 1000)
    setTimeout(callback2, 2000)

    vi.advanceTimersToNextTimer()
    expect(callback1).toHaveBeenCalled()
    expect(callback2).not.toHaveBeenCalled()

    vi.advanceTimersToNextTimer()
    expect(callback2).toHaveBeenCalled()
  })

  it('vi.runAllTimers — 跑完所有定时器', () => {
    const callback = vi.fn()
    setTimeout(callback, 500)
    setInterval(callback, 1000)

    vi.runAllTimers()
    expect(callback).toHaveBeenCalledTimes(2) // timeout + interval 各一次
  })

  it('fake timers 下的 async/await', async () => {
    // MSW 的 delay() 在 fake timers 下也能正常工作
    // 但 userEvent 需要特殊配置——见第四章
    const promise = new Promise<string>((resolve) => {
      setTimeout(() => resolve('done'), 1000)
    })

    vi.advanceTimersByTime(1000)
    const result = await promise
    expect(result).toBe('done')
  })
})
```

> **自我验证说明**：`vi.useFakeTimers`、`vi.useRealTimers`、`vi.advanceTimersByTime` 等 API 与 Jest 的 `jest.useFakeTimers()` 等一一对应，行为完全一致。来源：Vitest 官方文档 Mocking 章节。

---

## 2.6 覆盖率

```bash
npx vitest --coverage
```

覆盖率报告解读：

| 指标 | 含义 |
|---|---|
| Lines | 代码行是否被执行过 |
| Functions | 函数是否被调用过 |
| Branches | 每个条件分支（if/else/switch 等）是否都被覆盖 |
| Statements | 每个语句是否被执行过 |

合理的覆盖率目标：

- 新项目：可以从 60% 起步，逐步提升
- 成熟项目：80-90% 是常见的生产标准
- **不要追求 100%**——最后 10% 的投入往往不划算

**覆盖率不能告诉你的事**：
- 测试的质量（断言是否合理）
- 边界条件是否被覆盖
- 用户体验是否正确

覆盖率是一个**下限指标**，不是一个质量指标。100% 覆盖率 = 每行代码都被执行过，但绝不意味着每个 bug 都被发现了。

---

## 练习与思考

1. 为一组数学工具函数（add/subtract/multiply/divide）写完整测试，覆盖正常值、边界值（0、负数、Infinity）和异常（除以零）
2. 使用 `test.each` 重构上一题中重复的边界值测试，使其更简洁
3. 用 `vi.spyOn` 监听 `console.log`，写一个函数调用 `console.log`，验证 spy 可以断言调用参数
4. 写一个依赖 `setInterval` 的轮询函数，用 fake timers 测试它在指定时间内的调用次数
5. 思考：什么情况下应该用 `vi.mock`，什么情况下应该用 MSW？你的项目中有没有可以用 MSW 替代的 vi.mock？

---

## 本章总结

- Vitest 的断言语法与 Jest 完全兼容，迁移几乎零成本
- `toEqual` 深度比较 vs `toBe` 引用比较 vs `toStrictEqual` 严格结构比较
- `test.each` 是消除重复测试代码的最强工具
- `vi.fn` 创建独立 mock，`vi.spyOn` 监听已有方法——理解 mockClear/mockReset/mockRestore 的区别
- `vi.mock` 自动提升到文件顶层，需要部分 mock 时用 `vi.importActual`
- MSW 处理网络层，vi.mock 处理非 HTTP 依赖——二者互补而非互斥
- Fake timers 让时间依赖测试变得确定性和快速
- 覆盖率是下限指标，80% 以上即可，不用追求 100%
