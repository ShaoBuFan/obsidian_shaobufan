---
tags:
  - 参考/速查
  - 工具/Vitest
  - 工具/RTL
  - 工具/MSW
  - 工具/Jest
created: 2026-05-22
---

# 附录A：快速参考

> 速查表格式：每项一行，含 TypeScript 签名。不展开解释。

---

## A.1 Vitest API 速查

### 全局生命周期

```typescript
describe(name: string, fn: () => void): void
describe.skip(name: string, fn: () => void): void
describe.only(name: string, fn: () => void): void
it(name: string, fn: () => void | Promise<void>, timeout?: number): void
test(name: string, fn: () => void | Promise<void>, timeout?: number): void
it.skip(name: string, fn: () => void | Promise<void>): void
it.only(name: string, fn: () => void | Promise<void>): void
it.todo(name: string): void
it.each(cases: readonly T[])(name: string, fn: (...args) => void, timeout?: number): void
describe.each(cases: readonly T[])(name: string, fn: (...args) => void, timeout?: number): void
beforeAll(fn: () => void | Promise<void>, timeout?: number): void
afterAll(fn: () => void | Promise<void>, timeout?: number): void
beforeEach(fn: () => void | Promise<void>, timeout?: number): void
afterEach(fn: () => void | Promise<void>, timeout?: number): void
```

### vi Mock

```typescript
vi.fn<TArgs extends any[], TReturns>(fn?: (...args: TArgs) => TReturns): MockInstance<TArgs, TReturns>
vi.spyOn<T, K extends keyof T>(obj: T, method: K): MockInstance
vi.spyOn<T, K extends keyof T>(obj: T, method: K, accessType: 'get' | 'set'): MockInstance
vi.mock(path: string, factory?: () => any): void
vi.mock(path: string, factory?: (importOriginal: () => Promise<any>) => Promise<any>): void
vi.hoisted<T>(factory: () => T): T
vi.unmock(path: string): void
vi.importActual<T>(path: string): Promise<T>
vi.importMock<T>(path: string): Promise<T>
vi.clearAllMocks(): void
vi.resetAllMocks(): void
vi.restoreAllMocks(): void
```

### MockInstance 链式方法

```typescript
mock.mockImplementation(fn: (...args: TArgs) => TReturns): this
mock.mockImplementationOnce(fn: (...args: TArgs) => TReturns): this
mock.mockReturnValue(value: TReturns): this
mock.mockReturnValueOnce(value: TReturns): this
mock.mockResolvedValue(value: Awaited<TReturns>): this
mock.mockResolvedValueOnce(value: Awaited<TReturns>): this
mock.mockRejectedValue(error: unknown): this
mock.mockRejectedValueOnce(error: unknown): this
mock.mockClear(): this
mock.mockReset(): this
mock.mockRestore(): this
mock.getMockName(): string
mock.mockName(name: string): this
mock.getMockImplementation(): ((...args: TArgs) => TReturns) | undefined
```

### 断言 Matcher（Vitest 内置）

```typescript
expect(value: T): Assertion<T>
expect(value: T).toBe(expected: T): void
expect(value: T).toEqual(expected: T): void
expect(value: T).toStrictEqual(expected: T): void
expect(value: T).toBeTruthy(): void
expect(value: T).toBeFalsy(): void
expect(value: T).toBeNull(): void
expect(value: T).toBeUndefined(): void
expect(value: T).toBeDefined(): void
expect(value: T).toBeNaN(): void
expect(value: T).toBeGreaterThan(n: number): void
expect(value: T).toBeGreaterThanOrEqual(n: number): void
expect(value: T).toBeLessThan(n: number): void
expect(value: T).toBeLessThanOrEqual(n: number): void
expect(value: T).toBeCloseTo(n: number, numDigits?: number): void
expect(value: string).toMatch(pattern: string | RegExp): void
expect(value: string).toContain(substring: string): void
expect(value: T[]).toContain(item: T): void
expect(value: T).toHaveProperty(propPath: string, value?: any): void
expect(value: T).toHaveLength(n: number): void
expect(fn: () => T).toThrow(error?: string | RegExp | Error): void
expect(value: T).toMatchSnapshot(name?: string): void
expect(value: T).toMatchInlineSnapshot(snapshot?: string): void
expect(value: T).resolves: Assertion<Promise<T>>
expect(value: T).rejects: Assertion<Promise<T>>
expect.assertions(n: number): void
expect.hasAssertions(): void
expect.any(constructor: Constructor): AsymmetricMatcher
expect.anything(): AsymmetricMatcher
expect.arrayContaining(arr: readonly T[]): AsymmetricMatcher
expect.objectContaining(obj: Record<string, any>): AsymmetricMatcher
expect.stringContaining(str: string): AsymmetricMatcher
expect.stringMatching(pattern: RegExp): AsymmetricMatcher
```

### jest-dom 扩展 Matcher

```typescript
expect(element: HTMLElement).toBeInTheDocument(): void
expect(element: HTMLElement).toBeVisible(): void
expect(element: HTMLElement).toBeEmptyDOMElement(): void
expect(element: HTMLElement).toBeDisabled(): void
expect(element: HTMLElement).toBeEnabled(): void
expect(element: HTMLElement).toBeChecked(): void
expect(element: HTMLElement).toBeRequired(): void
expect(element: HTMLElement).toHaveFocus(): void
expect(element: HTMLElement).toHaveAttribute(attr: string, value?: string | RegExp): void
expect(element: HTMLElement).toHaveClass(...classNames: string[]): void
expect(element: HTMLElement).toHaveStyle(css: string | Record<string, any>): void
expect(element: HTMLElement).toHaveTextContent(text: string | RegExp, options?: { normalizeWhitespace?: boolean }): void
expect(element: HTMLElement).toHaveValue(value: string | string[] | number): void
expect(element: HTMLElement).toHaveDisplayValue(value: string | RegExp | Array<string | RegExp>): void
expect(element: HTMLElement).toBePartiallyChecked(): void
expect(element: HTMLElement).toHaveErrorMessage(text: string | RegExp): void
expect(element: HTMLElement).toContainElement(element: HTMLElement | null): void
expect(element: HTMLElement).toContainHTML(html: string): void
```

### 定时器

```typescript
vi.useFakeTimers(config?: FakeTimerInstallOpts): void
vi.useRealTimers(): void
vi.advanceTimersByTime(ms: number): void
vi.advanceTimersByTimeAsync(ms: number): Promise<void>
vi.advanceTimersToNextTimer(): void
vi.advanceTimersToNextTimerAsync(): Promise<void>
vi.runAllTimers(): void
vi.runAllTimersAsync(): Promise<void>
vi.runOnlyPendingTimers(): void
vi.getTimerCount(): number
vi.getRealSystemTime(): number
vi.setSystemTime(time: number | Date): void

FakeTimerInstallOpts:
{ now?: number | Date; toFake?: string[]; loopLimit?: number; shouldAdvanceTime?: boolean; advanceTimeDelta?: number }
```

### 配置

```typescript
vi.setConfig(config: { testTimeout?: number; hookTimeout?: number }): void
vi.stubGlobal(name: string, value: any): void
vi.unstubAllGlobals(): void
vi.waitFor<T>(callback: () => T | Promise<T>, options?: { timeout?: number; interval?: number }): Promise<T>
vi.waitUntil<T>(callback: () => T | Promise<T>, options?: { timeout?: number; interval?: number }): Promise<T>
```

---

## A.2 RTL Query 速查

### 查询类型签名

```typescript
// 所有 getBy / queryBy / findBy 变体
getByRole<K extends ElementType>(role: ARIARole | string, options?: ByRoleOptions): HTMLElementTagNameMap[K]
queryByRole<K extends ElementType>(role: ARIARole | string, options?: ByRoleOptions): HTMLElementTagNameMap[K] | null
findByRole<K extends ElementType>(role: ARIARole | string, options?: ByRoleOptions & { timeout?: number }): Promise<HTMLElementTagNameMap[K]>
getAllByRole<K extends ElementType>(role: ARIARole | string, options?: ByRoleOptions): HTMLElementTagNameMap[K][]
queryAllByRole<K extends ElementType>(role: ARIARole | string, options?: ByRoleOptions): HTMLElementTagNameMap[K][]
findAllByRole<K extends ElementType>(role: ARIARole | string, options?: ByRoleOptions & { timeout?: number }): Promise<HTMLElementTagNameMap[K][]>

// ByLabelText
getByLabelText(text: Matcher, options?: { selector?: string }): HTMLElement

// ByPlaceholderText
getByPlaceholderText(text: Matcher, options?: MatcherOptions): HTMLElement

// ByText
getByText(text: Matcher, options?: { selector?: string; ignore?: string | boolean }): HTMLElement

// ByDisplayValue
getByDisplayValue(value: Matcher, options?: MatcherOptions): HTMLElement

// ByAltText
getByAltText(text: Matcher, options?: MatcherOptions): HTMLElement

// ByTitle
getByTitle(text: Matcher, options?: MatcherOptions): HTMLElement

// ByTestId
getByTestId(text: Matcher, options?: { allowMultiple?: boolean }): HTMLElement

// Matcher 类型
type Matcher = string | RegExp | ((content: string, element: Element | null) => boolean)
type ByRoleMatcher = string | RegExp | ((accessibleName: string, element: Element) => boolean)
```

### ByRoleOptions

```typescript
interface ByRoleOptions {
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
  exact?: boolean
  normalizer?: (text: string) => string
}
```

### render

```typescript
render(ui: React.ReactElement, options?: RenderOptions): RenderResult

RenderOptions:
{ wrapper?: React.ComponentType<{ children: React.ReactNode }>; hydrate?: boolean; container?: HTMLElement; baseElement?: HTMLElement; legacyRoot?: boolean }

RenderResult:
{ container: HTMLElement; baseElement: HTMLElement; debug(element?: HTMLElement, maxLength?: number): void; rerender(ui: React.ReactElement): void; unmount(): void; asFragment(): DocumentFragment }

// screen —— 全局查询对象
screen.getByRole(...): ...  // 所有 query 方法
screen.logTestingPlaygroundURL(): void

// within —— 绑定到子树
within(element: HTMLElement): BoundFunctions<Queries>

// waitFor
waitFor<T>(callback: () => T | Promise<T>, options?: { timeout?: number; interval?: number; onTimeout?: (error: Error) => Error }): Promise<T>

// waitForElementToBeRemoved
waitForElementToBeRemoved<T>(callback: (() => T) | T, options?: { timeout?: number; interval?: number; container?: HTMLElement }): Promise<void>

// act
act(callback: () => void | Promise<void>): void
```

---

## A.3 userEvent 速查

```typescript
import userEvent from '@testing-library/user-event'

// setup
userEvent.setup(options?: UserEventOptions): UserEventInstance

UserEventOptions:
{ delay?: number; advanceTimers?: (delay: number) => void; skipAccessibilityCheck?: boolean; document?: Document; onDisabledClick?: 'error' | 'skip' | 'ignore' }

// 指针操作
user.click(target: Element, options?: PointerOptions): Promise<void>
user.dblClick(target: Element, options?: PointerOptions): Promise<void>
user.tripleClick(target: Element, options?: PointerOptions): Promise<void>
user.pointerDown(target: Element, options?: PointerOptions): Promise<void>
user.pointerUp(target: Element, options?: PointerOptions): Promise<void>
user.hover(target: Element, options?: PointerOptions): Promise<void>
user.unhover(target: Element, options?: PointerOptions): Promise<void>

// 键盘操作
user.type(target: Element, text: string, options?: { delay?: number; skipAccessibilityCheck?: boolean; initialSelectionStart?: number; initialSelectionEnd?: number }): Promise<void>
user.clear(target: Element): Promise<void>
user.keyboard(text: string, options?: { delay?: number }): Promise<void>
user.tab(options?: { shift?: boolean }): Promise<void>

// 表单操作
user.selectOptions(target: Element, values: HTMLElement | HTMLElement[] | string | string[]): Promise<void>
user.deselectOptions(target: Element, values: HTMLElement | HTMLElement[] | string | string[]): Promise<void>
user.upload(target: Element, files: File | File[]): Promise<void>

// 剪贴板
user.copy(target?: Element): Promise<void>
user.cut(target?: Element): Promise<void>
user.paste(target?: Element): Promise<void>
```

---

## A.4 MSW Handler 速查

### HTTP Handler

```typescript
import { http, HttpResponse } from 'msw'

// Handler 定义
http.get<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler
http.post<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler
http.put<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler
http.patch<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler
http.delete<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler
http.head<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler
http.options<Params = {}>(path: string | RegExp, resolver: ResponseResolver<Params>): HttpHandler

// ResponseResolver 签名
type ResponseResolver<Params> = (args: {
  request: Request
  params: Params
  cookies: Record<string, string>
  requestId: string
}) => HttpResponse | Promise<HttpResponse>

// 路径参数类型（需手写泛型）
http.get<{ id: string }>('/api/users/:id', ({ params }) => { /* params.id */ })
http.get<{ category: string; productId: string }>('/api/:category/:productId', ({ params }) => { /* ... */ })
```

### HttpResponse

```typescript
HttpResponse.json(body?: any, init?: ResponseInit): HttpResponse
HttpResponse.text(body?: string | null, init?: ResponseInit): HttpResponse
HttpResponse.xml(body?: string | null, init?: ResponseInit): HttpResponse
HttpResponse.arrayBuffer(body?: ArrayBuffer | null, init?: ResponseInit): HttpResponse
HttpResponse.error(): HttpResponse       // 网络错误（TypeError: Failed to fetch）
HttpResponse.passthrough(): HttpResponse  // 放行到真实网络（v2 静态方法）

new HttpResponse(body: BodyInit | null, init?: ResponseInit): HttpResponse

// ResponseInit
{ status?: number; statusText?: string; headers?: HeadersInit }

// 常用响应模式
HttpResponse.json(data, { status: 200 })       // 成功
HttpResponse.json(data, { status: 201 })        // 创建成功
new HttpResponse(null, { status: 204 })         // 无内容
new HttpResponse(null, { status: 400 })         // 客户端错误
new HttpResponse(null, { status: 401 })         // 未认证
new HttpResponse(null, { status: 403 })         // 无权限
new HttpResponse(null, { status: 404 })         // 未找到
HttpResponse.json({ error: 'Server Error' }, { status: 500 }) // 服务器错误
HttpResponse.error()                            // 网络错误
```

### Server Lifecycle

```typescript
import { setupServer } from 'msw/node'

// 创建
const server = setupServer(...handlers: HttpHandler[]): SetupServerApi

// SetupServerApi 接口
server.listen(options?: { onUnhandledRequest?: 'bypass' | 'warn' | 'error' | ((req: Request) => void) }): void
server.close(): void
server.resetHandlers(...nextHandlers: HttpHandler[]): void
server.use(...handlers: HttpHandler[]): void          // LIFO 覆盖
server.restoreHandlers(): void                        // 仅回退 use()
server.listHandlers(): readonly HttpHandler[]
server.printHandlers(): void
```

### WebSocket

```typescript
import { ws } from 'msw'

ws.link(url: string): WebSocketLink

WebSocketLink.addEventListener(type: 'connection', listener: (args: {
  client: { id: string; url: string; send(data: string): void; addEventListener(type: string, listener: (event: MessageEvent) => void): void }
}) => void): void

// 客户端方法
client.send(data: string): void             // 从服务端发消息给客户端
client.addEventListener(type: 'message', listener: (event: MessageEvent) => void): void  // 监听客户端消息
client.addEventListener(type: 'close', listener: () => void): void
client.close(): void
```

### GraphQL

```typescript
import { graphql, HttpResponse } from 'msw'

graphql.query(operationName: string, resolver: (args: { query: string; variables: Record<string, any> }) => HttpResponse): HttpHandler
graphql.mutation(operationName: string, resolver: (args: { query: string; variables: Record<string, any> }) => HttpResponse): HttpHandler

// 示例
graphql.query('GetUser', ({ variables }) => {
  return HttpResponse.json({ data: { user: { id: variables.id, name: 'Alice' } } })
})
```

---

## A.6 Jest → Vitest 速查对照

> 从 Jest 迁移到 Vitest 时最常用的 API 映射。左侧 Jest API，右侧 Vitest 等价写法。

| Jest | Vitest | 差异 |
|------|--------|------|
| `jest.fn()` | `vi.fn()` | 签名 1:1 兼容 |
| `jest.mock(path, factory)` | `vi.mock(path, factory)` | Hoist 行为一致；factory 引用外部变量需 `vi.hoisted()` |
| `jest.spyOn(obj, method)` | `vi.spyOn(obj, method)` | 签名 1:1 兼容 |
| `jest.useFakeTimers()` | `vi.useFakeTimers()` | Vitest 额外支持 Async 版本 |
| `jest.advanceTimersByTime(ms)` | `vi.advanceTimersByTime(ms)` | Vitest 额外支持 `Async` 后缀 |
| `jest.runAllTimers()` | `vi.runAllTimers()` | 签名一致 |
| `jest.requireActual(path)` | `vi.importActual(path)` | **异步**：返回 `Promise` |
| `jest.setTimeout(ms)` | `vi.setConfig({ testTimeout: ms })` | 签名不同；也支持 `it(name, fn, timeout)` |
| `jest.clearAllMocks()` | `vi.clearAllMocks()` | 签名 1:1 |
| `jest.resetAllMocks()` | `vi.resetAllMocks()` | 签名 1:1 |
| `jest.restoreAllMocks()` | `vi.restoreAllMocks()` | 签名 1:1 |
| `jest.createMockFromModule()` | `vi.importMock()` | **异步**：返回 `Promise` |
| `jest.unmock(path)` | `vi.unmock(path)` | 签名 1:1 |
| `jest.enableAutomock()` | 不支持 | 手动 `vi.mock()` 替代 |
| `jest.getTimerCount()` | `vi.getTimerCount()` | 签名 1:1 |
| `jest.config.js` | `vitest.config.ts` | `transform` → `plugins`；`moduleNameMapper` → `resolve.alias` |
| `testEnvironment: 'jsdom'` | `environment: 'jsdom'` | 字段名不同 |
| `setupFilesAfterFramework` | `setupFiles` | 字段名不同 |
| `@jest-environment jsdom` | `@vitest-environment jsdom` | 文件头注释格式 |
| `__mocks__/` 自动发现 | 不支持 | 需显式 `vi.mock(path, factory)` |

> **自我验证说明**：上表中标"**异步**"的是迁移中最容易踩坑的地方。`vi.importActual` 和 `vi.importMock` 都是 `async` 函数，必须在 `await ` 或 `then()` 中使用。`vi.mock` 的 async factory 从 Vitest v1.3 开始支持。

## 关联章节
- [第3章：Vitest 基础](03-Vitest基础.md) — Vitest API 速查
- [第4章：查询的艺术](04-查询的艺术.md) — RTL Query API 速查
- [第5章：用户事件模拟](05-用户事件模拟.md) — userEvent 方法速查
- [第6章：MSW 哲学与实践](06-MSW哲学与实践.md) — MSW Handler 速查
- [第14章：Jest 迁移指南](14-Jest迁移指南.md) — Jest → Vitest 速查对照
