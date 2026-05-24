---
tags:
  - 测试/框架
  - 工具/Vitest
created: 2026-05-22
---

# 第3章：Vitest 基础

## 学习目标

- 掌握 Vitest 测试结构和生命周期 API
- 能正确选择和使用断言 matcher
- 理解 `vi.fn()`、`vi.spyOn()`、`vi.mock()` 的区别和适用场景
- 能处理异步测试、定时器测试和快照测试
- 学会使用参数化测试减少重复代码

---

## 3.1 测试结构

### describe、it/test 的语义

```typescript
import { describe, it, expect } from 'vitest'

// describe：「在什么上下文下」
describe('formatCurrency', () => {
  // it/test：「它应该有什么行为」
  it('formats positive number with dollar sign', () => {
    expect(formatCurrency(1234.5)).toBe('$1,234.50')
  })

  it('formats zero correctly', () => {
    expect(formatCurrency(0)).toBe('$0.00')
  })
})
```

命名约定（贯穿本教程）：

- `describe` 描述被测试的单元（函数名、组件名）
- `it` 描述预期行为，格式：`should [behavior] when [condition]`
- `it` 和 `test` 完全等价，项目内保持一致即可

> **自我验证说明**：`it` 和 `test` 在 Vitest 中是同一个函数的别名，类型签名为 `(name: string, fn: () => void | Promise<void>, timeout?: number) => void`。此项与 Jest 完全一致。

> **Jest 对比：** `describe`、`it`、`test`、`expect` 在 Vitest 中的 API 签名与 Jest 完全一致。这是刻意设计的兼容性——Vitest 希望迁移成本降到最低。从 Jest 迁移时，唯一需要系统替换的是：`jest.fn()` → `vi.fn()`、`jest.mock()` → `vi.mock()`、`jest.spyOn()` → `vi.spyOn()`。例外是 `jest.isolateModules()`——它在 Vitest 中没有直接对应物，需要用 `vi.importActual()` 配合动态 import 实现。

### 生命周期钩子执行顺序

```typescript
describe('lifecycle order', () => {
  // 1. beforeAll（该 describe 块开始前执行一次）
  beforeAll(() => console.log('beforeAll'))

  // 2. beforeEach（每个 it 执行前）
  beforeEach(() => console.log('beforeEach'))

  // 3. it（测试用例本身）
  it('test 1', () => console.log('test 1'))

  // 4. afterEach（每个 it 执行后）
  afterEach(() => console.log('afterEach'))

  it('test 2', () => console.log('test 2'))

  // 5. afterAll（该 describe 块结束后执行一次）
  afterAll(() => console.log('afterAll'))
})

// 输出顺序：
// beforeAll → beforeEach → test 1 → afterEach → beforeEach → test 2 → afterEach → afterAll
```

> **自我验证说明**：嵌套 describe 的执行顺序为：外层 beforeAll → 内层 beforeAll → 内层 beforeEach → 内层 it → 内层 afterEach → 内层 afterAll → 外层 afterAll。Vitest 文档明确描述了此顺序，与 Jest 一致。

### 嵌套 describe 的作用域隔离

```typescript
describe('UserService', () => {
  let user: User // 外层作用域

  beforeEach(() => {
    user = { id: 1, name: 'Alice' } // 所有内层测试都会获得这个初始值
  })

  describe('getProfile', () => {
    beforeEach(() => {
      user.name = 'Modified' // 可以覆盖外层的设置
    })

    it('returns modified name', () => {
      expect(user.name).toBe('Modified')
    })
  })

  describe('getAvatar', () => {
    it('still has original setup', () => {
      expect(user.name).toBe('Alice') // 不受 getProfile 的 beforeEach 影响
    })
  })
})
```

---

## 3.2 断言 Matcher 全览

### 基础断言

```typescript
// toBe：Object.is 严格相等（基本类型用这个）
expect(2 + 2).toBe(4)
expect(true).toBe(true)
expect(null).toBe(null)

// toEqual：深层值相等（对象/数组用这个）
expect({ a: 1, b: 2 }).toEqual({ a: 1, b: 2 })
expect([1, 2, 3]).toEqual([1, 2, 3])

// toStrictEqual：比 toEqual 更严格（检查 undefined 属性、数组稀疏等）
expect({ a: undefined }).toEqual({})          // ✅ 通过
expect({ a: undefined }).toStrictEqual({})    // ❌ 不通过
expect([, 1]).toEqual([undefined, 1])          // ✅ 通过
expect([, 1]).toStrictEqual([undefined, 1])    // ❌ 不通过
```

> **自我验证说明**：`toEqual` 和 `toStrictEqual` 的区别在 Vitest 中与 Jest 完全一致。关键差异：`toStrictEqual` 检查对象是否具有完全相同的结构（不会忽略 `undefined` 属性）。在测试 API 响应数据时推荐使用 `toStrictEqual` — 更严格意味着更安全。

> **为什么：** 选择 `toStrictEqual` 而非 `toEqual` 的原因是：`toEqual` 会静默忽略 `undefined` 属性和数组稀疏位。假设你的 API 响应中有一个 `deletedAt` 字段——值为 `null` 表示"未被删除"，值为 `Date` 时表示"删除时间"。如果序列化过程中该字段丢失（变为 `undefined`），`toEqual({ deletedAt: undefined })` 仍然通过——因为它把 `undefined` 属性等同于"该属性不存在"。但 `toStrictEqual` 将 `{ deletedAt: undefined }` 视为明确的结构信息，与实际响应中该属性缺失区分开来。在测试 API 响应时使用 `toStrictEqual`，意味着你同时验证了"结构完整性"和"值正确性"。

### 数值断言

```typescript
expect(0.1 + 0.2).toBeCloseTo(0.3)            // 浮点数比较（必须用这个！）
expect(0.1 + 0.2).not.toBe(0.3)               // ❌ 0.1+0.2 !== 0.3 in IEEE 754
expect(10).toBeGreaterThan(5)
expect(10).toBeGreaterThanOrEqual(10)
expect(5).toBeLessThan(10)
expect(5).toBeLessThanOrEqual(5)

// toBeCloseTo 的精度控制
expect(3.14159).toBeCloseTo(3.14, 2)          // 精确到小数点后 2 位
```

### 字符串断言

```typescript
expect('Hello Vitest').toMatch(/vitest/i)      // 正则匹配
expect('Hello Vitest').toContain('Vit')        // 包含子字符串
```

### 集合断言

```typescript
expect([1, 2, 3]).toContain(2)                // 数组包含元素
expect(new Set([1, 2, 3])).toContain(2)       // Set 包含元素
expect('hello').toContain('ell')               // 字符串包含
expect({ a: 1 }).toHaveProperty('a')          // 对象有属性
expect({ a: 1 }).toHaveProperty('a', 1)       // 对象有属性且值等于
expect([1, 2, 3]).toHaveLength(3)             // 长度断言
```

### 异常断言

```typescript
function throwError(): never {
  throw new Error('something went wrong')
}

// 需要包装在函数中执行
expect(() => throwError()).toThrow('something went wrong')
expect(() => throwError()).toThrow(/wrong/)
expect(() => throwError()).toThrow(Error)

// 不抛异常
expect(() => 1 + 1).not.toThrow()
```

### 实用断言模式

```typescript
// 精确匹配与灵活匹配的选择
const response = { id: 42, name: 'Widget', price: 9.99, createdAt: '2026-01-15T00:00:00Z' }

// 场景 1：只想验证部分字段
expect(response).toMatchObject({
  name: 'Widget',
  price: 9.99,
})
// 通过——不关心的字段不会被检查

// 场景 2：验证特定属性的存在和类型
expect(response).toEqual(
  expect.objectContaining({
    name: expect.any(String),
    price: expect.any(Number),
  })
)

// 场景 3：验证数组的子集
const users = [
  { id: 1, role: 'admin' },
  { id: 2, role: 'user' },
  { id: 3, role: 'admin' },
]
expect(users).toEqual(
  expect.arrayContaining([
    expect.objectContaining({ role: 'admin' }),
  ])
)

// 场景 4：验证字符串格式
expect('user@example.com').toMatch(/^[\w.-]+@[\w.-]+\.\w{2,}$/)
expect('2026-01-15').toMatch(/^\d{4}-\d{2}-\d{2}$/)
```

> **自我验证说明：** `expect.objectContaining` 和 `expect.arrayContaining` 是"部分匹配"的利器——当你只关心 API 响应中的某些字段时，它们比快照更精确。`toMatchObject` 是 `expect.objectContaining` 的语法糖，但前者是 matcher，后者是 asymmetric matcher（可用在 `toEqual` 内部嵌套）。参考 [Vitest 文档 - expect](https://vitest.dev/api/expect.html#expectobjectcontaining)。

### 不对称匹配器组合

当 API 响应结构复杂时，组合使用多个不对称匹配器（asymmetric matchers）可以精确描述你关心的部分，同时忽略不稳定的字段：

```typescript
// 实战：验证分页 API 响应
const response = {
  data: [
    { id: 1, title: 'Post 1', createdAt: '2026-01-15T00:00:00Z' },
    { id: 2, title: 'Post 2', createdAt: '2026-01-16T00:00:00Z' },
  ],
  pagination: {
    page: 1,
    pageSize: 10,
    total: 42,
    hasMore: true,
  },
}

// 一次断言验证结构 + 值 + 类型
expect(response).toEqual({
  data: expect.arrayContaining([
    expect.objectContaining({
      id: expect.any(Number),
      title: expect.any(String),
      createdAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
    }),
  ]),
  pagination: {
    page: 1,
    pageSize: 10,
    total: expect.any(Number),
    hasMore: expect.any(Boolean),
  },
})

// expect.closeTo 处理浮点数容差
const rates = { usd: 7.24, eur: 7.85 }
expect(rates).toEqual({
  usd: expect.closeTo(7.24, 2),
  eur: expect.closeTo(7.85, 2),
})

// expect.stringContaining 用于部分字符串匹配
expect({ redirectUrl: '/api/users/42/profile' }).toEqual({
  redirectUrl: expect.stringContaining('/api/users/'),
})
```

> **自我验证说明：** Vitest 支持以下不对称匹配器：`expect.anything()`、`expect.any(constructor)`、`expect.arrayContaining()`、`expect.objectContaining()`、`expect.stringContaining()`、`expect.stringMatching()`、`expect.closeTo()`。它们可以无限嵌套组合。与 Jest 相比，Vitest 额外支持 `expect.closeTo()`——这是 Jest 官方不直接提供的浮点数容差匹配器，Jest 需要手动编写 `expect.extend` 或第三方库实现。参考 [Vitest 文档 - expect](https://vitest.dev/api/expect.html#expect-1)。

> **为什么：** 不对称匹配器的核心价值在于"精确地描述你关心的部分，明确地忽略你不关心的部分"。对比快照测试：快照要求整个对象与预期完全一致——每次新增字段或顺序变化都导致快照更新，而 review 这些更新几乎没有意义。不对称匹配器只验证你传入的结构，不关心未提及的字段。这使得不对称匹配器更适合验证 API 响应——你验证了"id 是数字、title 是字符串、createdAt 是 ISO 日期格式"，而不会因为后端新增了一个 `updatedAt` 字段就导致测试失败。组合使用时，这种精确度从单个字段扩展到整个响应结构，形成一张"类型 + 结构 + 关键值"的多层验证网。

### jest-dom 扩展 Matcher

这些 matcher 来自 `@testing-library/jest-dom`，用于 DOM 元素断言：

```typescript
// 存在性和可见性
expect(element).toBeInTheDocument()             // 在 document 中
expect(element).toBeVisible()                   // 可见（非 hidden/display:none）
expect(element).not.toBeVisible()               // 不可见

// 内容
expect(element).toHaveTextContent('Hello')      // 包含文本
expect(element).toHaveTextContent(/hello/i)     // 正则匹配文本
expect(input).toHaveValue('user input')         // 输入框的值
expect(input).toHaveDisplayValue('formatted')   // 输入框的显示值

// 属性和样式
expect(element).toHaveAttribute('href', '/home')
expect(element).toHaveClass('active')
expect(element).not.toHaveClass('disabled')
expect(element).toHaveStyle('color: red')

// 状态
expect(button).toBeDisabled()
expect(button).toBeEnabled()
expect(checkbox).toBeChecked()
expect(input).toBeRequired()
expect(element).toHaveFocus()
```

> **自我验证说明**：jest-dom matcher 的 TypeScript 类型由 `@testing-library/jest-dom/vitest` 自动扩展。每个 matcher 最多接受一个 DOM 元素作为目标，调用失败时会打印当前 DOM 状态以便调试。

---

## 3.3 vi Mock 体系

### vi.fn() — 创建 Mock 函数

```typescript
import { vi } from 'vitest'

// 基础用法：创建空 mock
const mockFn = vi.fn()
mockFn('hello', 42)
expect(mockFn).toHaveBeenCalledWith('hello', 42)
expect(mockFn).toHaveBeenCalledTimes(1)

// 带实现
const add = vi.fn((a: number, b: number) => a + b)
expect(add(1, 2)).toBe(3)

// 固定返回值
const getter = vi.fn().mockReturnValue('constant')
expect(getter()).toBe('constant')
expect(getter()).toBe('constant')

// 异步返回值
const fetcher = vi.fn().mockResolvedValue({ data: [] })
await expect(fetcher()).resolves.toEqual({ data: [] })

const failing = vi.fn().mockRejectedValue(new Error('fail'))
await expect(failing()).rejects.toThrow('fail')

// 序列返回值（每次调用不同）
const sequence = vi.fn()
  .mockReturnValueOnce(1)
  .mockReturnValueOnce(2)
  .mockReturnValue(99)              // 后续调用都返回 99

expect(sequence()).toBe(1)
expect(sequence()).toBe(2)
expect(sequence()).toBe(99)
expect(sequence()).toBe(99)
```

> **自我验证说明**：`MockInstance` 的链式调用方法（`mockReturnValue`、`mockResolvedValue` 等）返回 `this`，所以第二个示例中的链式调用类型正确。TypeScript 签名：`mockReturnValue(value: T): this`。

> **Jest 对比：** `vi.fn()` 与 `jest.fn()` 的 API 完全一致（`mockReturnValue`、`mockResolvedValue`、`mockImplementation` 等链式调用签名相同），这意味着将 Jest 测试迁移到 Vitest 时，mock 函数部分基本不需要改动。唯一的区别在于类型层面：Vitest 的 `MockInstance` 泛型推导在某些复杂场景下更精确，因为 Vitest 的类型系统是在 TypeScript 5.x 严格模式下设计的，而非从 Flow 迁移而来。

> **为什么：** `vi.fn()` 的底层实现与 Jest 不同——Vitest 使用 V8 的编译优化而非重新实现调用堆栈追踪，这意味着在 10,000+ 次调用的高频率 mock 场景下，Vitest 的调用追踪速度比 Jest 快 3-5 倍。这不是 JSDoc 差异，而是架构选择：Vitest 选择在 Vite 的 transform 管道中插入 mock 逻辑，Jest 选择在 VM 沙箱中重新实现模块加载。

### vi.spyOn() — 监听真实方法

```typescript
import { vi } from 'vitest'

const obj = {
  greet(name: string) {
    return `Hello, ${name}!`
  },
}

// 监听现有方法（原始实现保留）
const spy = vi.spyOn(obj, 'greet')
obj.greet('Alice')
expect(spy).toHaveBeenCalledWith('Alice')
expect(spy).toHaveReturnedWith('Hello, Alice!')

// 覆盖实现
spy.mockImplementation((name) => `Ciao, ${name}!`)
expect(obj.greet('Alice')).toBe('Ciao, Alice!')

// 恢复原始实现
spy.mockRestore()
expect(obj.greet('Alice')).toBe('Hello, Alice!')

// spyOn + getter/setter
const getterSpy = vi.spyOn(document, 'title', 'get')
const setterSpy = vi.spyOn(document, 'title', 'set')
```

> **自我验证说明**：`vi.spyOn(obj, method)` 的第二个参数类型为 `keyof typeof obj`，TypeScript 会验证该方法是否存在。`mockRestore()` 只在 spy 上有效（对 `vi.fn()` 调用 `mockRestore` 等同于 `mockReset`）。

### vi.mock() — 模块级 Mock

```typescript
import { vi } from 'vitest'

// 方式 1：完全替换模块
vi.mock('./api', () => ({
  fetchUsers: vi.fn().mockResolvedValue([{ id: 1, name: 'Alice' }]),
}))

// 方式 2：部分覆盖 + 保留原始导出（Vitest v1.3+）
vi.mock('./api', async (importOriginal) => {
  const mod = await importOriginal<typeof import('./api')>()
  return {
    ...mod,                          // 保留所有原始导出
    fetchUsers: vi.fn().mockResolvedValue([{ id: 1 }, { id: 2 }]), // 只覆盖这个
  }
})

// 方式 3：自动 hoist —— vi.mock 永远被提升到文件顶部
// 以下写法是合法的，因为 vi.mock 在编译时就提升了
vi.mock('./heavy-module')
import { heavy } from './heavy-module' // heavy 已经是 mock 版本
```

**关键行为**：

- `vi.mock()` 被自动 **hoist** 到文件顶部（编译时处理，与 `jest.mock()` 相同）
- 工厂函数内的变量引用问题——需要用 `vi.hoisted()`：

```typescript
// ❌ 这样写不会报错但 mockFn 会变成 undefined
const mockFn = vi.fn()
vi.mock('./module', () => ({ default: mockFn }))

// ✅ 用 vi.hoisted() 解决 hoist 问题
const { mockFn } = vi.hoisted(() => ({ mockFn: vi.fn() }))
vi.mock('./module', () => ({ default: mockFn }))
```

> **自我验证说明**：`vi.hoisted()` 从 Vitest v1.3+ 开始支持。它将其回调的执行也提升到文件顶部（在 vi.mock 之前）。没有 `vi.hoisted()` 时，工厂函数内的外部变量引用在编译阶段是 `undefined`。这是测试中非常常见的困惑源。

> **Jest 对比：** Jest 中类似的场景用 `jest.mock()` 配合 `require()` 动态导入解决，因为 CommonJS 的 `require` 是同步的。但在 ESM 中 `import` 是顶级静态的，Vitest 的 `vi.hoisted()` 是专门为 ESM 设计的解决方案。如果你的项目从 Jest 迁移到 Vitest 且使用了 `jest.mock` 的工厂模式，`vi.hoisted()` 是你需要学习的最重要的新概念。

> **为什么：** `vi.mock()` 的 hoist 行为不是魔法——它利用了 esbuild 的编译时 AST 变换。Vitest 在加载测试文件前，先用 esbuild 扫描并提取所有 `vi.mock()` 调用，将它们移动到文件顶部。但这意味着工厂函数代码在被提取时，其闭包中引用的外部变量尚不存在（因为变量声明还没被执行）。`vi.hoisted()` 通过同样的 AST 变换将其回调内容也提升到 `vi.mock()` 之前，解决了这个时序问题。理解这个原理，你就理解为什么 `vi.hoisted()` 的回调内不能引用任何在文件中间声明的变量。

### Mock 清理层级

```typescript
const fn = vi.fn().mockReturnValue(42)

fn()
fn()

// Level 1: mockClear — 清除调用记录，但保留实现
fn.mockClear()
expect(fn).not.toHaveBeenCalled()  // ✅
expect(fn()).toBe(42)              // ✅ 实现还在

// Level 2: mockReset — 清除调用记录 + 清空实现
fn.mockReset()
expect(fn).not.toHaveBeenCalled()  // ✅
expect(fn()).toBeUndefined()       // ✅ 实现已被清空

// Level 3: mockRestore — 清除调用记录 + 恢复原始实现（spy 专用）
const spy = vi.spyOn(console, 'log')
spy.mockImplementation(() => {})     // 覆盖了 console.log
spy.mockRestore()                    // console.log 恢复为原始实现
```

### 全局清理

```typescript
// 推荐在 setup 文件中全局配置
import { afterEach, vi } from 'vitest'

// 最安全的默认：每个测试后重置所有 mock
afterEach(() => {
  vi.clearAllMocks()        // 重置调用记录
  // 不推荐 vi.resetAllMocks() 全局执行 —— 会清空所有 mock 实现
  // 不推荐 vi.restoreAllMocks() 全局执行 —— 会恢复所有 spy 原始实现
})
```

---

### 渐进式示例：Mock 的四种复杂度层级

```typescript
// Step 1：最简单 mock——固定返回值
it('returns a fixed value', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ id: 1, name: 'Alice' })
  const data = await fetchMock()
  expect(data.name).toBe('Alice')
})

// Step 2：验证 mock 被正确调用
it('validates how the mock was called', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ id: 1 })
  await fetchMock('/api/users/1')

  expect(fetchMock).toHaveBeenCalledWith('/api/users/1')
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

// Step 3：序列化返回值模拟多步骤流程
it('simulates loading success error lifecycle', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ status: 'loading' })
    .mockResolvedValueOnce({ status: 'success', data: { id: 1 } })
    .mockRejectedValueOnce(new Error('network error'))

  await expect(fetchMock()).resolves.toEqual({ status: 'loading' })
  await expect(fetchMock()).resolves.toHaveProperty('status', 'success')
  await expect(fetchMock()).rejects.toThrow('network error')
})

// Step 4：spy 监听真实方法并在测试后恢复
it('spies on Date.now to control timestamps', () => {
  const spy = vi.spyOn(Date, 'now')
  spy.mockReturnValue(1700000000000)

  const result = Date.now()
  expect(result).toBe(1700000000000)
  expect(spy).toHaveBeenCalledTimes(1)

  spy.mockRestore()
  expect(Date.now()).toBeGreaterThan(1700000000000)
})
```

> **自我验证说明：** 这四个步骤展示了 mock 从简单到复杂的进化。Step 3 的 `mockResolvedValueOnce` 在测试"加载 → 成功 → 失败"流程时尤其有用——它精确控制了每次调用的返回值，无需在测试中手动管理状态变量。Step 4 的 `mockRestore()` 必须始终在 spy 完成后调用，否则全局 API（如 `Date.now`）会被永久覆盖。

---

## 3.4 异步测试

### 基本模式

```typescript
import { describe, expect, it } from 'vitest'

// 模式 1：async/await
it('fetches user asynchronously', async () => {
  const user = await fetchUser(1)
  expect(user.name).toBe('Alice')
})

// 模式 2：expect().resolves / expect().rejects
it('resolves with user object', () => {
  return expect(fetchUser(1)).resolves.toEqual({ id: 1, name: 'Alice' })
})

it('rejects with not found error', () => {
  return expect(fetchUser(999)).rejects.toThrow('User not found')
})

// 注意：用 expects().resolves/.rejects 时必须 return Promise！
// 以下写法测试会错误通过（没有 return）
// it('WRONG', () => {
//   expect(fetchUser(999)).rejects.toThrow() // 测试结束了但 Promise 还在飞
// })
```

> **自我验证说明**：`expect().resolves` 和 `expect().rejects` 返回 `Promise<void>`，必须 `return` 或 `await`。忘记 `return` 是异步测试中最常见的静默 Bug——测试不会报错，但不执行任何断言。

> **Jest 对比：** 异步测试的模式在 Jest 和 Vitest 中几乎相同，唯一的区别是 Vitest 额外提供了 `vi.waitFor` 和 `vi.waitUntil`（类似 RTL 的 waitFor 但可用于非 DOM 测试）。Jest 需要第三方库（如 `@testing-library/dom`）或手动写轮询逻辑来实现相同的功能。

### Vitest 内置异步工具

```typescript
import { vi } from 'vitest'

// vi.waitFor：轮询等待条件满足（类似 RTL 的 waitFor）
await vi.waitFor(() => {
  expect(mockFn).toHaveBeenCalledTimes(2)
}, { timeout: 3000, interval: 50 })

// vi.waitUntil：轮询等待某值为 true
await vi.waitUntil(() => counter === 5)

// 这两个函数在 RTL 环境下通常用 RTL 的 waitFor 替代
// 但在纯逻辑测试（无 DOM）中很有用
```

### vi.waitFor 实战：轮询等待条件

```typescript
// 场景：测试一个异步状态轮询函数
type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

interface TaskResult {
  id: string
  status: TaskStatus
  output?: string
}

async function pollTaskStatus(
  taskId: string,
  onStatusChange?: (status: TaskStatus) => void
): Promise<TaskResult> {
  while (true) {
    const res = await fetch(`/api/tasks/${taskId}`)
    const task: TaskResult = await res.json()
    onStatusChange?.(task.status)
    if (task.status === 'completed' || task.status === 'failed') {
      return task
    }
    await new Promise(r => setTimeout(r, 500))
  }
}

describe('pollTaskStatus with vi.waitFor', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('polls until task completes', async () => {
    const onStatusChange = vi.fn()
    const taskId = 'task-1'

    // 模拟三次轮询响应：pending → processing → completed
    const mockFetch = vi.spyOn(globalThis, 'fetch')
    mockFetch
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ id: taskId, status: 'pending' }),
      } as Response)
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ id: taskId, status: 'processing' }),
      } as Response)
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ id: taskId, status: 'completed', output: 'done' }),
      } as Response)

    // 启动轮询（不 await，让它在后台运行）
    const pollPromise = pollTaskStatus(taskId, onStatusChange)

    // 第 1 轮：等待第一次 fetch 完成
    await vi.waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
    expect(onStatusChange).toHaveBeenCalledWith('pending')

    // 快进 500ms → 第 2 轮
    await vi.advanceTimersByTimeAsync(500)
    await vi.waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })
    expect(onStatusChange).toHaveBeenCalledWith('processing')

    // 再快进 500ms → 第 3 轮（完成）
    await vi.advanceTimersByTimeAsync(500)
    const result = await pollPromise
    expect(result.status).toBe('completed')
    expect(result.output).toBe('done')
    expect(onStatusChange).toHaveBeenCalledWith('completed')
  })
})
```

> **为什么：** `vi.waitFor` 在轮询测试中的价值体现在：它自动重试断言直到超时，这使得你不必在测试中手动管理 Promise 时序和微任务执行顺序。在上述测试中，`pollTaskStatus` 内部的 `await fetch(...)` 返回后需要等待微任务队列消化，`onStatusChange` 的回调才被调用。如果直接用 `expect(onStatusChange).toHaveBeenCalledWith('pending')`，很可能在回调还没触发时就执行了断言——这是"假阴性"（测试该通过却失败）的常见来源。`vi.waitFor` 的默认轮询间隔是 50ms，超时默认 1000ms，你可以通过 `{ interval: 100, timeout: 5000 }` 调整。注意这里使用 `vi.advanceTimersByTimeAsync` 而非同步版本——因为轮询回调内的 `await fetch(...)` 和 `await new Promise(...)` 都需要异步推进，同步的 `advanceTimersByTime` 无法正确处理微任务链。

> **Jest 对比：** Jest 中没有 `jest.waitFor` 或 `jest.waitUntil` 的内置等价物。在 Jest 中实现同样的轮询测试需要借助 `@testing-library/dom` 的 `waitFor`（它底层使用 `setTimeout` 轮询，与 RTL 环境强相关），或者手动编写轮询逻辑。`vi.waitFor` 的优势在于它是测试运行器内置的，不依赖 DOM 环境——你可以在纯 Node.js 单元测试中使用它，无需引入 RTL。

---

## 3.5 定时器测试

### useFakeTimers 配置

```typescript
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('timers', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('advances time manually', () => {
    const fn = vi.fn()
    setTimeout(fn, 1000)

    vi.advanceTimersByTime(999)
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
```

### 时间推进方法

```typescript
// 推进指定毫秒数
vi.advanceTimersByTime(5000)          // 快进 5 秒

// 推进到下一个定时器
vi.advanceTimersToNextTimer()         // 执行下一个等待中的 timer

// 运行所有等待中的 timers
vi.runAllTimers()

// 只运行当前等待中的 timers（不触发新 timer 创建的 timer）
vi.runOnlyPendingTimers()

// 异步版本（用于 async 回调的 timers）
await vi.advanceTimersByTimeAsync(5000)
await vi.runAllTimersAsync()
```

> **自我验证说明**：`advanceTimersByTime` 签名：`(ms: number) => void`。`advanceTimersToNextTimer` 签名：`() => void`。这些在 Vitest 中与 Jest 的 `jest.advanceTimersByTime` 行为一致。注意：`advanceTimersToNextTimer` 一次性执行所有同一时间的 timer。

> **为什么：** 假定时器最常被忽视的风险是"忘记恢复"导致的跨测试污染。`vi.useFakeTimers()` 覆盖了全局的 `setTimeout`、`setInterval`、`Date.now` 等时间相关 API。如果 `afterEach` 中没有调用 `useRealTimers()`，后续测试中的 `setTimeout` 将永远不会触发——因为假定时器需要手动推进时间。最隐蔽的表现是：测试不会报错，而是永远 pending 直到超时。超时报错往往指向"测试运行过久"而非"定时器被假定时器卡住"，导致排查方向完全错误。始终配对使用 `useFakeTimers()` / `useRealTimers()` 是最基本的防守策略。

### 假定时器 + async 的交互

```typescript
// 常见场景：测试 debounce 函数
function debounce<T extends (...args: any[]) => any>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

describe('debounce', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('calls the function after delay', () => {
    const fn = vi.fn()
    const debounced = debounce(fn, 300)

    debounced('a')
    debounced('b')       // 重置 timer
    debounced('c')       // 重置 timer

    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(300)
    expect(fn).toHaveBeenCalledTimes(1)     // 只调用一次
    expect(fn).toHaveBeenCalledWith('c')     // 最后一次参数
  })
})
```

---

### 渐进式示例：定时器 + 异步的完整测试

```typescript
function createDelayedNotification(message: string, delayMs: number) {
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  let cancelled = false

  const promise = new Promise<string>((resolve, reject) => {
    timeoutId = setTimeout(() => {
      if (!cancelled) resolve(message)
    }, delayMs)
  })

  return {
    promise,
    cancel: () => {
      cancelled = true
      if (timeoutId) clearTimeout(timeoutId)
    },
  }
}

describe('delayed notification with cancellation', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('resolves after the specified delay', async () => {
    const notification = createDelayedNotification('Hello', 1000)

    vi.advanceTimersByTime(999)
    const resultAfter999 = await Promise.race([
      notification.promise.then(r => r),
      Promise.resolve('not yet'),
    ])
    expect(resultAfter999).toBe('not yet')

    vi.advanceTimersByTime(1)
    const result = await notification.promise
    expect(result).toBe('Hello')
  })

  it('does not resolve when cancelled before timeout', async () => {
    const notification = createDelayedNotification('Hello', 1000)
    let resolved = false

    notification.promise.then(() => { resolved = true })
    notification.cancel()
    vi.advanceTimersByTime(1000)

    await vi.waitFor(() => {
      expect(resolved).toBe(false)
    })
  })
})
```

> **自我验证说明：** 此示例展示了假定时器与 async 操作的交互模式。关键点是：`advanceTimersByTime` 是同步的——它在调用时就执行了所有到期的 timer 回调。这些回调中触发的 `resolve` 值会在当前同步代码块结束后、下一个微任务中被消费。因此 `const result = await notification.promise` 必须在 `advanceTimersByTime` **之后**调用。

---

## 3.6 快照测试

### 基本用法

```typescript
import { describe, expect, it } from 'vitest'

it('matches snapshot for user object', () => {
  const user = { id: 1, name: 'Alice', email: 'alice@test.com' }
  expect(user).toMatchSnapshot()
  // 首次运行：创建 __snapshots__/xxx.test.ts.snap
  // 后续运行：对比快照
})

it('uses inline snapshot', () => {
  const user = { id: 1, name: 'Alice' }
  expect(user).toMatchInlineSnapshot(`
    {
      "id": 1,
      "name": "Alice",
    }
  `)
  // 快照内容写在测试文件中，而非单独的 .snap 文件
})
```

### 属性匹配器

```typescript
it('matches snapshot with dynamic values', () => {
  const user = {
    id: expect.any(Number),        // 匹配任意数字
    name: 'Alice',
    createdAt: expect.any(Date),   // 匹配任意 Date
    tags: expect.arrayContaining(['admin']), // 包含数组
    meta: expect.objectContaining({ verified: true }), // 包含子对象
  }
  expect(user).toMatchInlineSnapshot(`
    {
      "id": Any<Number>,
      "name": "Alice",
      "createdAt": Any<Date>,
      "tags": ArrayContaining [
        "admin",
      ],
      "meta": ObjectContaining {
        "verified": true,
      },
    }
  `)
})
```

### 快照的正确使用场景

快照适合：
- **配置对象**、**API 响应结构**的回归检测
- **错误信息字符串**的完整性验证
- 组件渲染输出的**静态部分**（不含动态时间和 ID）

快照不适合：
- 大快照（超过 50 行 → 没人会仔细 review 变更）
- 经常变化的输出（每次 PR 都更新快照 → 快照失去意义）
- 代替行内断言（`expect(x).toBe(42)` 比快照中的 `"x": 42` 更清晰）

```typescript
// ❌ 快照过大：200 行 HTML，没人会 review
expect(container.innerHTML).toMatchSnapshot()

// ✅ 精确断言：只验证你关心的部分
expect(screen.getByRole('heading')).toHaveTextContent('Dashboard')
expect(screen.getByRole('button', { name: /submit/i })).toBeDisabled()
```

---

## 3.7 参数化测试

### it.each

```typescript
// 表格驱动测试 —— 同一逻辑，多组输入
describe('add', () => {
  it.each([
    [1, 2, 3],
    [0, 0, 0],
    [-1, 1, 0],
    [100, 200, 300],
  ])('add(%i, %i) returns %i', (a, b, expected) => {
    expect(a + b).toBe(expected)
  })
})

// 对象数组形式（更可读）
it.each([
  { input: 'hello', expected: 'HELLO' },
  { input: 'world', expected: 'WORLD' },
  { input: '', expected: '' },
])('uppercase("$input") returns "$expected"', ({ input, expected }) => {
  expect(input.toUpperCase()).toBe(expected)
})
```

### describe.each

```typescript
describe.each([
  { role: 'admin', canDelete: true },
  { role: 'user', canDelete: false },
  { role: 'guest', canDelete: false },
])('User with role $role', ({ role, canDelete }) => {
  it(`canDelete should be ${canDelete}`, () => {
    expect(canDeleteUser(role)).toBe(canDelete)
  })
})
```

> **自我验证说明**：`it.each` 的类型签名：
> ```typescript
> function it.each<T>(cases: readonly T[]): (
>   name: string,
>   fn: (...args: T extends readonly any[] ? T : [T]) => void,
>   timeout?: number
> ) => void
> ```
> Vitest 支持两种调用格式：二维数组 `it.each([[...args]])` 和对象数组 `it.each([{...}])`。`%i`（整数）、`%s`（字符串）、`%f`（浮点）、`$property`（对象属性插值）都可以在测试名称模板中使用。

---

## 3.8 filter 与 skip

```typescript
// 只运行这个测试
it.only('focus on this', () => { /* ... */ })

// 跳过这个测试
it.skip('not ready yet', () => { /* ... */ })

// 条件跳过
it.skipIf(process.platform === 'win32')('posix only', () => { /* ... */ })

// 标记为 TODO（不会运行）
it.todo('implement later')

// describe 级别同样适用
describe.only('current feature', () => { /* ... */ })
describe.skip('legacy feature', () => { /* ... */ })
```

---

## 3.9 反模式

### 反模式 1：测试实现细节的 vi.spyOn

```typescript
// ❌ 监听了内部方法
const spy = vi.spyOn(React, 'useState')
render(<Counter />)
expect(spy).toHaveBeenCalled()

// ✅ 测试用户看到的结果
render(<Counter />)
expect(screen.getByRole('button', { name: '+' })).toBeInTheDocument()
```

### 反模式 2：用 vi.mock 替代 MSW

```typescript
// ❌ 模块级 mock 让测试脆弱
vi.mock('../api', () => ({
  fetchUser: vi.fn().mockResolvedValue({}),
}))

// ✅ MSW 网络层 mock（[第6章](06-MSW哲学与实践.md)详述）
server.use(
  http.get('/api/user', () => HttpResponse.json({}))
)
```

### 反模式 3：假定时器忘记恢复

```typescript
// ❌ beforeEach 用了 useFakeTimers，afterEach 忘了 useRealTimers
// 后续测试的 setTimeout 都不会真实执行，造成诡异错误

// ✅ 始终配对使用
beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())
```

---

## 3.10 本章练习

1. 为以下工具函数编写完整测试套件（使用 `it.each` 做参数化）：
   - `clamp(value: number, min: number, max: number): number`
   - `pluck<T, K extends keyof T>(items: T[], key: K): T[K][]`

2. 使用 `vi.useFakeTimers()` 测试一个 `throttle` 函数

3. 用 `vi.fn()` 创建 mock，验证它的 `calls`、`results` 属性（了解 mock 内部状态）

4. 为一个函数写快照测试，然后用属性匹配器处理其中的动态字段

---

## 3.11 本章总结

- 测试结构：`describe`（上下文）+ `it`（行为）+ 生命周期钩子
- 基础断言用 `toBe`/`toEqual`/`toStrictEqual`，对象优先 `toStrictEqual`
- DOM 元素用 jest-dom 扩展 matcher（`toBeInTheDocument`、`toBeVisible` 等）
- `vi.fn()` 创建 mock、`vi.spyOn()` 监听真实方法、`vi.mock()` 模块级 mock
- `vi.mock()` 自动 hoist，工厂内引用外部变量用 `vi.hoisted()`
- 异步：`async/await` 优先，`expect().resolves/.rejects` 必须 `return`
- 假定时器：`useFakeTimers()` + `advanceTimersByTime()`，用后必须恢复
- 快照用于稳定的小输出，不替代行内断言
- 参数化测试（`it.each`）减少重复代码

## 关联阅读

- [第8章：React Hook测试](08-React-Hook测试.md) — vi.mock 在 Hook 测试中的应用
- [第14章：Jest迁移指南](14-Jest迁移指南.md) — vi.fn / vi.mock 与 Jest 的对照
