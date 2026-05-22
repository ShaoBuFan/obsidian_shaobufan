---
tags:
  - tutorial
  - appendix
  - typescript
created: 2026-05-22
---

# 附录 A：类型定义速查表

## Vitest 全局类型

```typescript
// 在 tsconfig.json 中配置 "types": ["vitest/globals"] 后，以下全局可用：

// 测试结构
declare function describe(name: string, fn: () => void): void
declare function it(name: string, fn: () => void | Promise<void>): void
declare function test(name: string, fn: () => void | Promise<void>): void

// 生命周期
declare function beforeAll(fn: () => void | Promise<void>): void
declare function beforeEach(fn: () => void | Promise<void>): void
declare function afterAll(fn: () => void | Promise<void>): void
declare function afterEach(fn: () => void | Promise<void>): void

// 断言
declare const expect: ExpectStatic

// Mock 工具
declare const vi: {
  fn: <T extends (...args: any[]) => any>(impl?: T) => Mock<T>
  spyOn: <T extends object, K extends keyof T>(obj: T, method: K) => Mock<T[K]>
  mock: (path: string, factory?: () => unknown) => void
  unmock: (path: string) => void
  importActual: <T>(path: string) => Promise<T>
  useFakeTimers: () => void
  useRealTimers: () => void
  advanceTimersByTime: (ms: number) => void
  advanceTimersToNextTimer: () => void
  runAllTimers: () => void
  setSystemTime: (date: Date | number) => void
  stubGlobal: (name: string, stub: unknown) => void
  clearAllMocks: () => void
  resetAllMocks: () => void
  restoreAllMocks: () => void
}
```

## Mock 函数类型

```typescript
interface Mock<T extends (...args: any[]) => any> {
  // 调用信息
  mock: {
    calls: Parameters<T>[]
    results: { type: 'return' | 'throw'; value: unknown }[]
    instances: unknown[]
    contexts: unknown[]
    lastCall: Parameters<T> | undefined
  }

  // 行为设置
  mockImplementation: (impl: T) => this
  mockReturnValue: (value: ReturnType<T>) => this
  mockResolvedValue: (value: Awaited<ReturnType<T>>) => this
  mockRejectedValue: (error: unknown) => this
  mockReturnValueOnce: (value: ReturnType<T>) => this
  mockImplementationOnce: (impl: T) => this

  // 清理
  mockClear: () => this
  mockReset: () => this
  mockRestore: () => void
}

// 类型辅助
declare function mocked<T>(item: T, deep?: boolean): Mocked<T>
```

## RTL 渲染与查询类型

```typescript
// render 返回值
interface RenderResult {
  container: HTMLElement
  baseElement: HTMLElement
  debug: (element?: HTMLElement | HTMLElement[]) => void
  rerender: (ui: React.ReactElement) => void
  unmount: () => void
  asFragment: () => DocumentFragment
}

// screen 对象
const screen: {
  // getBy* — 找不到抛错
  getByRole: (role: string, options?: ByRoleOptions) => HTMLElement
  getByLabelText: (text: Matcher, options?: SelectorMatcherOptions) => HTMLElement
  getByPlaceholderText: (text: Matcher, options?: SelectorMatcherOptions) => HTMLElement
  getByText: (text: Matcher, options?: SelectorMatcherOptions) => HTMLElement
  getByDisplayValue: (value: Matcher, options?: SelectorMatcherOptions) => HTMLElement
  getByTestId: (id: Matcher, options?: MatcherOptions) => HTMLElement

  // queryBy* — 找不到返回 null
  queryByRole: (role: string, options?: ByRoleOptions) => HTMLElement | null
  // ... 其他 queryBy 签名类似

  // findBy* — 返回 Promise，超时抛错
  findByRole: (role: string, options?: ByRoleOptions) => Promise<HTMLElement>
  // ... 其他 findBy 签名类似

  // getAllBy* / queryAllBy* / findAllBy* — 返回数组
  getAllByRole: (role: string, options?: ByRoleOptions) => HTMLElement[]
}

// ByRole 选项
interface ByRoleOptions {
  name?: string | RegExp
  level?: number       // 仅 heading
  checked?: boolean    // 仅 checkbox/radio
  pressed?: boolean    // 仅 button
  expanded?: boolean
  selected?: boolean
  hidden?: boolean
}

// Matcher 类型
type Matcher = string | RegExp | ((content: string, element: HTMLElement) => boolean)
```

## MSW v2 Handler 类型

```typescript
import { http, graphql, HttpResponse, delay, passthrough } from 'msw'
import { setupServer } from 'msw/node'
import { setupWorker } from 'msw/browser'

// HTTP Handler 泛型签名
// http.get<Params, RequestBodyType, ResponseBodyType, Path>(...)
http.get<{ userId: string }, never, { id: string; name: string }>(
  '/api/users/:userId',
  ({ params, request, cookies }) => {
    // params: { userId: string }
    // request: Request (标准 Fetch API)
    // cookies: Record<string, string>
    return HttpResponse.json({ id: params.userId, name: 'Alice' })
  }
)

// HttpResponse 静态方法
HttpResponse.json<T>(body: T, init?: ResponseInit): StrictResponse<T>
HttpResponse.text(body: string, init?: ResponseInit): StrictResponse<string>
HttpResponse.xml(body: string, init?: ResponseInit): StrictResponse<string>
HttpResponse.formData(body: FormData, init?: ResponseInit): StrictResponse<FormData>
HttpResponse.error(): NetworkErrorResponse

// Server API
interface SetupServerApi {
  listen: (options?: { onUnhandledRequest?: 'bypass' | 'warn' | 'error' }) => void
  close: () => void
  use: (...handlers: HttpHandler[]) => void
  resetHandlers: (...handlers?: HttpHandler[]) => void
  restoreHandlers: () => void
  boundary: <T>(callback: () => Promise<T>) => Promise<T>
}

// GraphQL Handler
graphql.query<QueryType, VariablesType>(operationName, resolver)
graphql.mutation<MutationType, VariablesType>(operationName, resolver)
```

## userEvent 类型

```typescript
import userEvent from '@testing-library/user-event'

interface UserEvent {
  click: (element: Element) => Promise<void>
  dblClick: (element: Element) => Promise<void>
  tripleClick: (element: Element) => Promise<void>
  type: (element: Element, text: string, options?: { skipClick?: boolean }) => Promise<void>
  keyboard: (text: string) => Promise<void>
  clear: (element: Element) => Promise<void>
  selectOptions: (element: Element, values: string | string[]) => Promise<void>
  hover: (element: Element) => Promise<void>
  unhover: (element: Element) => Promise<void>
  tab: () => Promise<void>
  paste: (element: Element, text: string) => Promise<void>
  upload: (element: HTMLElement, file: File | File[]) => Promise<void>
}

interface UserEventSetupOptions {
  advanceTimers?: (ms: number) => void
  skipHover?: boolean
  pointerEventsCheck?: 0 | 1 | 2
  skipAutoCleanup?: boolean
  writeToClipboard?: boolean
}

function userEvent.setup(options?: UserEventSetupOptions): UserEvent
```
