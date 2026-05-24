---
tags:
  - 参考/类型
  - 工具/TypeScript
  - 工具/RTL
created: 2026-05-22
---

# 附录C：TypeScript 类型工具

> 覆盖测试中常用的类型定义、类型扩展、常见 TS 错误修复。

---

## C.1 RTL 核心类型

### Matcher 类型体系

```typescript
// 来自 @testing-library/dom（所有查询的基础类型）

// Matcher：最通用的匹配器类型
// 字符串 / 正则 / 自定义函数
type Matcher = string | RegExp | ((content: string, element: Element | null) => boolean)

// ByRoleMatcher：getByRole 专用的 name/description 匹配
// 第一个参数是计算后的 accessible name，第二个是元素本身
type ByRoleMatcher = string | RegExp | ((accessibleName: string, element: Element) => boolean)

// MatcherOptions：大多数 query 的通用选项
interface MatcherOptions {
  exact?: boolean                   // 默认 false（子串匹配）
  normalizer?: (text: string) => string  // 自定义文本规范化
}

// ByRoleOptions：getByRole 专用选项
interface ByRoleOptions extends MatcherOptions {
  name?: ByRoleMatcher              // 按 accessible name 筛选
  description?: ByRoleMatcher       // 按 accessible description 筛选
  hidden?: boolean                  // 是否包含隐藏元素（默认 false）
  selected?: boolean                // 仅匹配 selected 状态
  checked?: boolean                 // 仅匹配 checked 状态
  pressed?: boolean                 // 仅匹配 pressed 状态（aria-pressed）
  expanded?: boolean                // 仅匹配 expanded 状态
  level?: number                    // heading 层级（h1-h6）
  current?: boolean | string        // aria-current 值
  queryFallbacks?: boolean          // 是否查询 fallback role
  suggest?: boolean                 // 匹配失败时推荐其他 role（调试用）
}

// NormalizerOptions：文本规范化控制
interface NormalizerOptions {
  trim?: boolean
  collapseWhitespace?: boolean
}
```

### 使用场景：自定义 MatcherFunction

```typescript
// 场景：匹配以特定前缀开头的文本
import { MatcherFunction } from '@testing-library/react'

const startsWithHello: MatcherFunction = (content, element) =>
  content.startsWith('Hello')

// 使用
screen.getByText(startsWithHello)

// 场景：精确匹配一个元素下的多个文本条件
const matchComplexLabel: MatcherFunction = (_content, element) => {
  const el = element as HTMLElement | null
  if (!el) return false
  return (
    el.querySelector('[data-role="primary"]') !== null &&
    el.textContent?.includes('Required') === true
  )
}

screen.getByText(matchComplexLabel)
```

---

## C.2 扩展 jest-dom Matcher 类型

### 标准扩展方式

在 Vitest 中使用 `@testing-library/jest-dom/vitest` 会自动处理类型扩展：

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'

// 这行 import 会：
// 1. 调用 expect.extend() 注册所有 jest-dom matcher
// 2. 扩展 Vitest 的 Assertion 接口 + AsymmetricMatchersContaining 接口
// 3. 使 toBeInTheDocument() 等方法有正确的 TypeScript 类型
```

### 手动扩展（如果需要自定义 matcher）

```typescript
// src/test/matchers.ts
import { expect } from 'vitest'
import { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers'

// 声明自定义 matcher（类型安全）
interface CustomMatchers<R = unknown> {
  toBeWithinRange(min: number, max: number): R
  toBeValidEmail(): R
}

// 实现
expect.extend({
  toBeWithinRange(received: number, min: number, max: number) {
    const pass = received >= min && received <= max
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be within range (${min}..${max})`
          : `expected ${received} to be within range (${min}..${max})`,
    }
  },
  toBeValidEmail(received: string) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const pass = emailRegex.test(received)
    return {
      pass,
      message: () =>
        pass
          ? `expected "${received}" not to be a valid email`
          : `expected "${received}" to be a valid email`,
    }
  },
})

// 类型声明合并（关键步骤）
declare module 'vitest' {
  interface Assertion<T = any> extends CustomMatchers<T> {}
  interface AsymmetricMatchersContaining extends CustomMatchers {}
}
```

### 当 jest-dom 类型不生效时的诊断

```typescript
// 问题：toHaveTextContent 报类型错误
const el = screen.getByRole('button')
expect(el).toHaveTextContent('Submit')
//        ^^^^^^^^^^^^^^^^ Property 'toHaveTextContent' does not exist

// 诊断步骤：

// 1. 确认 setup 文件导入了正确路径
import '@testing-library/jest-dom/vitest'     // ✅ 正确路径
import '@testing-library/jest-dom'              // ❌ 不含 /vitest，类型不匹配

// 2. 检查 vitest.config.ts 的 globals 设置
test: { globals: true }                        // 需要确保与 tsconfig 一致

// 3. 检查 tsconfig.json 的 types 字段
{
  "compilerOptions": {
    "types": ["vitest/globals"]                // ✅ 确保包含
  }
}

// 4. 备选方案：手动声明
// src/test/vitest.d.ts
/// <reference types="@testing-library/jest-dom/vitest" />
```

---

## C.3 自定义 Render 的类型推导

### 基本包装

```typescript
// src/test/utils.tsx
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ReactElement } from 'react'

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string
}

// 返回类型：保持 RenderResult 的所有类型信息
function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult {
  const { initialRoute = '/', ...renderOptions } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[initialRoute]}>
        {children}
      </MemoryRouter>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}
```

### 增强返回类型

```typescript
// src/test/utils.tsx —— 带额外返回值的增强版
import { render, RenderOptions, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UserEvent } from '@testing-library/user-event/dist/types/setup/setup'
import { MemoryRouter } from 'react-router-dom'

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string
}

// 扩展 RenderResult 的返回类型
interface CustomRenderResult extends ReturnType<typeof render> {
  user: UserEvent
}

function renderWithProviders(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
): CustomRenderResult {
  const { initialRoute = '/', ...renderOptions } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[initialRoute]}>
        {children}
      </MemoryRouter>
    )
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    user: userEvent.setup(),
  }
}

// 使用 —— user 自动可用，类型正确
it('uses enhanced render', async () => {
  const { user } = renderWithProviders(<MyComponent />)
  // user.click — 类型安全
  await user.click(screen.getByRole('button'))
})
```

### 带 QueryClient 的完整类型

```typescript
// src/test/utils.tsx
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,              // React Query v5: gcTime, v4: cacheTime
      },
    },
  })
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string
}

// 返回类型包含 queryClient，供测试直接访问缓存
interface CustomRenderResult extends RenderResult {
  queryClient: QueryClient
}

function renderWithProviders(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
): CustomRenderResult {
  const queryClient = createTestQueryClient()

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  }
}
```

---

## C.4 常见 TypeScript 错误及修复

### 错误 1：`Property 'toBeInTheDocument' does not exist`

```
Property 'toBeInTheDocument' does not exist on type 'Assertion<HTMLElement>'.
```

**修复**：

```typescript
// 检查 setup 文件导入了什么
import '@testing-library/jest-dom/vitest'   // ✅
// NOT import '@testing-library/jest-dom'    // ❌ 旧路径

// 检查 tsconfig.json
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

### 错误 2：`Type 'undefined' is not assignable to type 'string'`

```typescript
// 场景：queryBy* 返回可能为 null
const button = screen.queryByRole('button') // HTMLElement | null
button.textContent                          // Object is possibly 'null'
```

**修复**：

```typescript
// 方案 1：用 getBy*（如果不期望 null）
const button = screen.getByRole('button')
button.textContent // string | null（没 null 问题了）

// 方案 2：类型守卫
const button = screen.queryByRole('button')
if (button) {
  button.textContent // string | null（但按钮存在了）
}

// 方案 3：可选链
screen.queryByRole('button')?.textContent
```

### 错误 3：`Argument of type 'string' is not assignable to parameter of type 'ARIARole'`

```typescript
// 场景：自定义 role 名
screen.getByRole('my-custom-role')
// ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
// Argument of type '"my-custom-role"' is not assignable to parameter of type 'ARIARole'
```

**修复**：

```typescript
// 方案 1：断言为 string（标准 role 集之外的字符串）
screen.getByRole('my-custom-role' as string)

// 方案 2：扩展 ARIARole 类型
declare module '@testing-library/dom' {
  interface ARIARole {
    'my-custom-role': string
  }
}

// 方案 3：用 getByTestId 作为退路
screen.getByTestId('custom-role-element')
```

### 错误 4：vi.mock 中的类型丢失

```typescript
// ❌ 类型丢失
vi.mock('./api')
import { fetchUser } from './api'
// fetchUser 类型是 Mock<...>，丢失了原始签名

// ✅ 保留原始类型
vi.mock('./api', async (importOriginal) => {
  const mod = await importOriginal<typeof import('./api')>()
  return {
    ...mod,
    fetchUser: vi.fn<Parameters<typeof mod.fetchUser>, ReturnType<typeof mod.fetchUser>>(),
  }
})
```

### 错误 5：`Module '"@testing-library/react"' has no exported member 'renderHook'`

```typescript
// @testing-library/react v16+ 已重新引入 renderHook
// 旧版本需要从 @testing-library/react-hooks 导入
```

**修复**：

```bash
npm install -D @testing-library/react-hooks
```

```typescript
import { renderHook } from '@testing-library/react-hooks'

// 或在 @testing-library/react v16+ 中：
import { renderHook } from '@testing-library/react'
// 如果版本不支持，回退到 react-hooks 包
```

> **自我验证说明**：`@testing-library/react` v16 重新引入了 `renderHook`。如果使用 v15 或更早版本，需要从 `@testing-library/react-hooks` 导入。参考 [React Testing Library 版本说明](https://github.com/testing-library/react-testing-library/releases)。

---

## C.5 测试工厂的工具类型

### 基于 Partial 的工厂函数

```typescript
// userFactory.ts
import { faker } from '@faker-js/faker'

export interface User {
  id: number
  name: string
  email: string
  role: 'admin' | 'user' | 'guest'
  createdAt: Date
  isActive: boolean
}

// 基于 Partial<Overrides> 的工厂
export function buildUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.number.int({ min: 1, max: 99999 }),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    role: 'user',
    createdAt: faker.date.past(),
    isActive: true,
    ...overrides,
  }
}

// 使用
const admin = buildUser({ role: 'admin' })
// admin.role 类型为 'admin'（字面量类型保持）
```

### 泛型工厂

```typescript
// 对任意实体类型适用的泛型工厂
function buildList<T>(
  factory: (index: number) => T,
  count: number = 3
): T[] {
  return Array.from({ length: count }, (_, i) => factory(i))
}

// 使用
const users = buildList(() => buildUser(), 10)
// users: User[] ✓

const posts = buildList(
  (i) => ({ id: i, title: `Post ${i}`, author: buildUser() }),
  5
)
// posts: { id: number; title: string; author: User }[] ✓
```

### 基于 DeepPartial 的工厂

```typescript
// 深层 Partial 类型（复杂嵌套对象场景）
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

interface Order {
  id: number
  customer: {
    name: string
    address: {
      street: string
      city: string
      zip: string
    }
  }
  items: Array<{ productId: number; quantity: number }>
}

export function buildOrder(overrides: DeepPartial<Order> = {}): Order {
  return {
    id: faker.number.int(),
    customer: {
      name: faker.person.fullName(),
      address: {
        street: faker.location.streetAddress(),
        city: faker.location.city(),
        zip: faker.location.zipCode(),
        ...overrides.customer?.address,
      },
      ...overrides.customer,
    },
    items: overrides.items ?? [
      { productId: faker.number.int(), quantity: 1 },
    ],
    ...overrides,
  }
}
```

### MSW handler 工厂

```typescript
// 带类型的 MSW handler 工厂
import { http, HttpResponse } from 'msw'
import { buildUser, User } from './userFactory'

interface UserHandlerOptions {
  status?: number
  user?: Partial<User> | 'error'
  delay?: number
}

export function createUserHandlers(options: UserHandlerOptions = {}) {
  const { status = 200, user, delay: delayMs = 0 } = options

  return [
    http.get('/api/users/:id', async ({ params }) => {
      if (delayMs) await delay(delayMs)

      if (user === 'error') {
        return HttpResponse.json(
          { message: 'Internal Server Error' },
          { status: 500 }
        )
      }

      if (status >= 400) {
        return new HttpResponse(null, { status })
      }

      return HttpResponse.json(
        user ? buildUser(user) : buildUser(),
        { status }
      )
    }),
  ]
}

// 使用
it('handles user not found', async () => {
  server.use(...createUserHandlers({ status: 404 }))
  // ...
})

it('handles slow network', async () => {
  server.use(...createUserHandlers({ delay: 1000 }))
  // ...
})
```

---

## C.6 vitest 配置的环境类型问题

### globals 类型不一致

```typescript
// 问题：tsconfig.json 配置了 "types": ["vitest/globals"]
// 但 vitest.config.ts 中 globals: false
// 运行时：describe 是 undefined
// 编辑器：describe 有类型但无法运行
```

**保持类型和运行时一致。**

### 多环境 workspace 的类型问题

```typescript
// vitest.workspace.ts
export default defineWorkspace([
  {
    test: {
      name: 'dom',
      environment: 'jsdom',
      globals: true,
    },
  },
  {
    test: {
      name: 'node',
      environment: 'node',
      globals: false,
    },
  },
])
```

```json
// tsconfig.json —— 使用项目引用来隔离不同类型环境
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  },
  "references": [
    { "path": "./tsconfig.dom.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

### userEvent.setup 的类型不匹配

```typescript
// ❌ 忘记 await，TS 不报错但是运行时 bug
async function test() {
  const user = userEvent.setup()
  user.click(button) // Promise<undefined>，没有 await
}
// ✅ eslint-plugin-testing-library 推荐安装来捕获此类错误
```

## 关联章节
- [第2章：测试环境搭建](02-测试环境搭建.md) — TypeScript 配置与 setup 文件体系（C.2/C.6）
- [第4章：查询的艺术](04-查询的艺术.md) — Matcher 类型体系（C.1/C.4）
- [第8章：React Hook 测试](08-React-Hook测试.md) — renderHook 类型与 renderWithProviders（C.3/C.4）
- [第12章：测试可维护性](12-测试可维护性.md) — 自定义 render 与测试工厂（C.3/C.5）
