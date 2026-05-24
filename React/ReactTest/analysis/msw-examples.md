# MSW + Vitest 官方示例分析

分析对象：
- `with-vitest` — ESM 版本
- `with-vitest-cjs` — CommonJS 版本

基于 mswjs/examples 仓库，MSW v2.11.2。

---

## 1. 项目结构（精确文件树）

两个项目结构完全一致：

```
with-vitest (或 with-vitest-cjs)/
├── mocks/
│   ├── handlers.ts          # MSW handler 定义（REST + GraphQL）
│   └── node.ts              # 用 setupServer 创建 server 实例
├── vitest.setup.ts          # Vitest 全局 setup：server lifecycle
├── vitest.config.ts         # Vitest 配置
├── example.test.ts          # 测试用例（node 环境）
├── example-jsdom.test.ts    # 测试用例（jsdom 环境）
├── tsconfig.json            # TypeScript 配置
├── package.json
└── README.md
```

两个项目的区别仅在于文件内容细节（import 扩展名、GraphQL query 名等），结构完全镜像。

---

## 2. vitest.config.ts 配置

**ESM 和 CJS 版本完全一致：**

```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    root: __dirname,
    setupFiles: ['./vitest.setup.ts'],
  },
})
```

关键配置项：

| 配置项 | 值 | 作用 |
|---|---|---|
| `globals: true` | 允许测试文件中直接使用 `describe`、`it`、`expect`、`beforeAll` 等，无需 import |
| `root: __dirname` | 将项目根目录设为 vitest 查找路径的基准 |
| `setupFiles` | 在所有测试文件运行前执行 `vitest.setup.ts`，用于初始化 MSW |

现代 vitest (>=1.0) 中 `globals` 也可在 `tsconfig.json` 的 `types` 中声明类型支持。

---

## 3. MSW Server 搭建模式（三层架构）

### 3.1 `mocks/handlers.ts` — Handler 定义层

**ESM 版本：**

```ts
import { http, graphql, HttpResponse } from 'msw'

export const handlers = [
  http.get('https://api.example.com/user', () => {
    return HttpResponse.json({
      firstName: 'John',
      lastName: 'Maverick',
    })
  }),
  graphql.query('ListMovies', () => {
    return HttpResponse.json({
      data: {
        movies: [
          { title: 'The Lord of The Rings' },
          { title: 'The Matrix' },
          { title: 'Star Wars: The Empire Strikes Back' },
        ],
      },
    })
  }),
]
```

**CJS 版本：**

```ts
import { http, graphql, HttpResponse } from 'msw'

export const handlers = [
  http.get('https://api.example.com/user', () => {
    return HttpResponse.json({
      firstName: 'John',
      lastName: 'Maverick',
    })
  }),
  graphql.query('GetUser', () => {
    return HttpResponse.json({
      data: {
        user: {
          firstName: 'John',
          lastName: 'Maverick',
        },
      },
    })
  }),
]
```

区别：GraphQL operation name 不同（ListMovies vs GetUser）以及返回数据形状不同。

### 3.2 `mocks/node.ts` — Server 实例创建层

**ESM 版本：**

```ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers.js'   // <-- 显式 .js 扩展名

export const server = setupServer(...handlers)
```

**CJS 版本：**

```ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'      // <-- 无扩展名

export const server = setupServer(...handlers)
```

核心模式：
- 使用 `setupServer(...handlers)` 创建 server 实例（这是 MSW 的 node.js 集成）
- 使用展开运算符 `...handlers` 将 handlers 数组传入
- 导出 server 供 setup 文件使用

### 3.3 `vitest.setup.ts` — 生命周期管理

**ESM 版本：**

```ts
import { server } from './mocks/node.js'   // <-- 显式 .js 扩展名

beforeAll(() => {
  server.listen()
})

afterEach(() => {
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
```

**CJS 版本：**

```ts
import { server } from './mocks/node'      // <-- 无扩展名

beforeAll(() => {
  server.listen()
})

afterEach(() => {
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
```

---

## 4. 测试写法模式

### 4.1 环境声明

每个测试文件顶部使用 `@vitest-environment` 注释声明运行环境：

```ts
/**
 * @vitest-environment node
 */
```

或：

```ts
/**
 * @vitest-environment jsdom
 */
```

`example.test.ts` 使用 `node` 环境（可在 Node 原生 fetch 下测试）。
`example-jsdom.test.ts` 使用 `jsdom` 环境（模拟浏览器环境）。

注意：由于 `globals: true`，测试文件中无需 import `describe`、`it`、`expect`。

### 4.2 REST API 测试

```ts
it('fetches the user info', async () => {
  const response = await fetch('https://api.example.com/user')

  expect(response.status).toBe(200)
  expect(response.statusText).toBe('OK')
  expect(await response.json()).toEqual({
    firstName: 'John',
    lastName: 'Maverick',
  })
})
```

### 4.3 GraphQL API 测试

```ts
it('fetches the list of movies', async () => {
  const response = await fetch('https://api.example.com/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: `
        query ListMovies {
          movies {
            title
          }
        }
      `,
    }),
  })

  expect(response.status).toBe(200)
  expect(response.statusText).toBe('OK')
  expect(await response.json()).toEqual({
    data: {
      movies: [
        { title: 'The Lord of The Rings' },
        { title: 'The Matrix' },
        { title: 'Star Wars: The Empire Strikes Back' },
      ],
    },
  })
})
```

### 4.4 测试模式总结

| 方面 | 模式 |
|---|---|
| 断言风格 | `toBe`（原始值）、`toEqual`（对象/数组深比较） |
| 异步处理 | `async/await`，MSW 的 handler 本身也是异步友好的 |
| 环境切换 | 文件级 `@vitest-environment` 注释 |
| 不 mocking `fetch` | 这是 MSW 的核心优势——在网络层拦截，不需要替换 `global.fetch` |
| 不使用 `render` | 这些不是组件测试，是纯 MSW 集成测试 |

---

## 5. TypeScript 用法细节

### 5.1 根 tsconfig（两个 example 共用）

路径：`examples/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "~/*": ["./*"]
    }
  },
  "include": ["**/*"],
  "exclude": ["node_modules"]
}
```

### 5.2 项目级 tsconfig（两个 example 各自）

**ESM 版本：**

```json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "types": ["vitest/globals"]
  },
  "include": ["./**/*.ts"]
}
```

**CJS 版本：**

```json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "types": ["vitest/globals"],
  },
  "include": ["./**/*.ts"]
}
```

唯一区别：CJS 版本在 `"vitest/globals"` 后有尾逗号，ESM 版本没有。

关键点：
- `"types": ["vitest/globals"]` 启用 `describe`、`it`、`expect` 等的全局类型，不需要在每个测试文件中 import
- `extends` 机制避免重复配置
- `"module": "nodenext"` 和 `"moduleResolution": "nodenext"` 是让 TypeScript 正确解析 `.js` 扩展名 import 的关键

### 5.3 类型层面的 ESM vs CJS

根 tsconfig 的 `"module": "nodenext"` 是 MSW 示例正确使用 ESM 的关键设定。它要求 TypeScript 在 ESM 项目中使用显式 `.js` 扩展名，在 CJS 项目中不允许（或不需要）扩展名。这与两个项目的 `package.json` 里的 `"type": "module"` 配置一致。

---

## 6. 包依赖与版本

### 6.1 两个版本的 package.json

**ESM 版本（`with-vitest/package.json`）：**

```json
{
  "name": "with-vitest",
  "type": "module",
  "scripts": {
    "test": "vitest run"
  },
  "devDependencies": {
    "jsdom": "^21.1.1",
    "msw": "2.11.2",
    "typescript": "^5.0.4",
    "vitest": "^0.30.1"
  }
}
```

**CJS 版本（`with-vitest-cjs/package.json`）：**

```json
{
  "name": "with-vitest-cjs",
  "scripts": {
    "test": "vitest run"
  },
  "devDependencies": {
    "jsdom": "^21.1.1",
    "msw": "2.11.2",
    "typescript": "^5.0.4",
    "vitest": "^0.30.1"
  }
}
```

### 6.2 版本对比表

| 包 | ESM 版版本 | CJS 版版本 | 精确性 |
|---|---|---|---|
| msw | 2.11.2 | 2.11.2 | 精确锁定（无 ^） |
| vitest | ^0.30.1 | ^0.30.1 | 范围（可到 0.x） |
| jsdom | ^21.1.1 | ^21.1.1 | 范围 |
| typescript | ^5.0.4 | ^5.0.4 | 范围 |

**重要的版本观察：**

1. MSW v2.11.2 精确锁定——这是 MSW 官方示例仓库的惯例，确保示例总是可运行
2. vitest 使用 ^0.30.1 —— 这是一个较早期版本（当前最新已是 v3.x）。这意味着该示例有些 API 可能在新版 vitest 中已弃用或变更
3. msw v2.11.2 已经是在 `HttpResponse` API（v2 引入）之上的版本，不再使用 v1 的 `res()` / `ctx()` 模式
4. jsdom ^21.1.1 仅用于 jsdom 环境的测试

### 6.3 关键区别：ESM vs CJS

| 方面 | ESM (`with-vitest`) | CJS (`with-vitest-cjs`) |
|---|---|---|
| `"type"` 字段 | `"module"` | 无（默认 commonjs） |
| import 扩展名 | 需要 `.js` 后缀 | 无扩展名 |
| 理由 | Node.js ESM 要求显式扩展名 | CJS 解析策略不要求扩展名 |

---

## 7. Handler 定义模式

### 7.1 REST handler

```ts
http.get('https://api.example.com/user', () => {
  return HttpResponse.json({
    firstName: 'John',
    lastName: 'Maverick',
  })
})
```

模式要点：
- 使用 `http.get()` 匹配 GET 请求（还有 `http.post()`、`http.put()` 等）
- URL 是**完整 URL**（含协议和域名）
- MSW v2 使用 `HttpResponse.json()` 返回 JSON 响应
- handler 可以返回 `HttpResponse.json()`、`HttpResponse.text()` 或 `new Response()`

### 7.2 GraphQL handler

```ts
graphql.query('ListMovies', () => {
  return HttpResponse.json({
    data: {
      movies: [
        { title: 'The Lord of The Rings' },
        { title: 'The Matrix' },
        { title: 'Star Wars: The Empire Strikes Back' },
      ],
    },
  })
})
```

模式要点：
- `graphql.query(operationName)` 匹配指定 operation name 的 GraphQL query
- `graphql.mutation(operationName)` 匹配 mutation
- GraphQL handler 的 URL 默认为 `/graphql`（但可以在 URL 中指定特定端点）
- 响应必须包含 `data` 字段（符合 GraphQL 规范）

### 7.3 关键观察

1. 两个示例都定义了 `handlers` 数组并导出，而不是导出单个 handler
2. 数组通过 `...handlers` 展开传入 `setupServer`
3. handler 定义为纯函数，没有外部状态依赖
4. 响应数据是静态硬编码的（没有动态逻辑）

---

## 8. 测试生命周期管理

### 8.1 完全生命周期流程图

```
Vitest 启动
  │
  ├── 读取 vitest.config.ts
  │   └── setupFiles: ['./vitest.setup.ts']
  │
  ├── 执行 vitest.setup.ts（在所有测试之前）
  │   ├── beforeAll  →  server.listen()        ← 启动 MSW
  │   ├── afterEach  →  server.resetHandlers()  ← 每个测试后重置 handler
  │   └── afterAll   →  server.close()          ← 关闭 MSW
  │
  ├── 运行所有测试文件
  │   ├── example.test.ts        (node 环境)
  │   └── example-jsdom.test.ts  (jsdom 环境)
  │
  └── 退出
```

### 8.2 每个生命周期钩子的作用

| 钩子 | 调用时机 | 作用 | 为什么重要 |
|---|---|---|---|
| `server.listen()` | `beforeAll`（全部测试前） | 启动 MSW 拦截所有网络请求 | 如果放在 `beforeEach` 中，会在每个测试前重复启动，浪费性能 |
| `server.resetHandlers()` | `afterEach`（每个测试后） | 清除测试期间动态添加/覆盖的 handler，恢复 handlers.ts 的初始状态 | 防止测试间 handler 污染 |
| `server.close()` | `afterAll`（全部测试后） | 关闭 MSW 拦截，恢复原始 `fetch` | 没有这个会泄漏 mock，影响其他测试套件 |

### 8.3 为什么这个生命周期模式是「最佳实践」

1. **`setupFiles` 优于每个测试文件重复 setup**：所有 setup 逻辑集中在一处
2. **`afterEach` + `resetHandlers()` 优于 `afterEach` + `listen()`**：重置 handler 比重启 server 更轻量
3. **`server.close()` 是必要的清理**：防止 MSW 在测试结束后仍拦截网络请求

---

## 9. 显著模式与反模式

### 9.1 显著模式

**正面模式：**

1. **三层架构分离**：handlers（定义）→ node（实例）→ setup（生命周期），职责清晰
2. **测试文件级环境声明**：使用 `@vitest-environment` 注释，同一项目可同时运行 node 环境和 jsdom 环境的测试
3. **`globals: true` + `"types": ["vitest/globals"]`**：减少样板 import，测试文件更简洁
4. **集中式 setup**：setupFiles 机制让所有测试共享同一套 MSW 生命周期
5. **MSW v2 `HttpResponse` API**：比 v1 的 `res(ctx.json(...))` 更直观
6. **GraphQL 和 REST 在同一个 handler 数组**：可以混合匹配不同类型的 API

**可增强的方面（虽然不是反模式）：**

1. **没有 `describe` 分组**：示例只有顶层 `it`，没有 `describe` 块。在真实项目中应根据功能/组件分组
2. **没有动态 handler**：所有响应都是静态的。真实项目需要 `http.get('/api/...', ({ params }) => ...)` 动态响应
3. **没有错误场景测试**：只测试了成功路径。应该测试 4xx/5xx 响应、网络错误等
4. **没有测试组件**：这些是纯 MSW 集成测试，不涉及 React 组件渲染。React 教程需要额外集成 `@testing-library/react`

### 9.2 反模式（无）

这是一个简洁规范的示例，没有明显反模式。需要注意的（非反模式，但需要了解）：
- `vitest ^0.30.1` 已过时，新项目中应使用 `vitest ^3.x`
- `jsdom ^21.1.1` 也已过时，新项目中应使用 `jsdom ^25.x` 或 `happy-dom`

---

## 10. ESM 与 CJS 版本差异详解

### 10.1 差异总表

| 差异点 | ESM (`with-vitest`) | CJS (`with-vitest-cjs`) |
|---|---|---|
| `package.json` 的 `"type"` | `"module"` | 无（默认 commonjs） |
| import 扩展名 | 需要 `.js` | 不需要扩展名 |
| GraphQL operation name | `ListMovies` | `GetUser` |
| GraphQL 响应数据 | `{ data: { movies: [...] } }` | `{ data: { user: {...} } }` |
| 测试用例描述 | `'fetches the user info'` / `'fetches the list of movies'` | `'receives a mocked response to a REST API request'` / `'receives a mocked response to a GraphQL API request'` |
| GraphQL query 内容 | `query ListMovies { movies { title } }` | `query GetUser { user { firstName lastName } }` |
| tsconfig 尾逗号 | `"vitest/globals"]` | `"vitest/globals"],` |

### 10.2 import 扩展名差异——最重要的区别

**ESM 版本：** 显式 `.js` 扩展名（即使源文件是 `.ts`）

```ts
// vitest.setup.ts
import { server } from './mocks/node.js'

// mocks/node.ts
import { handlers } from './handlers.js'
```

**CJS 版本：** 无扩展名

```ts
// vitest.setup.ts
import { server } from './mocks/node'

// mocks/node.ts
import { handlers } from './handlers'
```

**原因：** 当 `package.json` 有 `"type": "module"` 时，Node.js ESM 解析要求 import 路径包含文件扩展名。TypeScript 编译时不会自动添加 `.js` 扩展名，所以源文件必须写 `.js`。这个 `.js` 在 TypeScript 的 `nodenext` 模块解析策略下会被正确映射回对应的 `.ts` 文件。

### 10.3 GraphQL query 差异

两个版本的 GraphQL 内容不同，但没有技术上的深意——仅是为了展示多样化。CJS 版本展示的是 `GetUser` query（返回单个对象），ESM 版本展示的是 `ListMovies` query（返回数组）。

### 10.4 两个项目相同的模式（差异不存在的地方）

以下方面两个项目完全一致：
- vitest.config.ts 配置（完全相同的代码）
- vitest 生命周期管理模式（完全相同）
- 测试文件数量和组织（完全相同）
- 包依赖版本（完全相同）
- 使用的 MSW API（完全相同：`http.get`、`graphql.query`、`HttpResponse.json`、`setupServer`）

---

## 11. 对 React 测试教程的启示和应用

### 11.1 可以直接采用的模式

**1. 三层 MSW 架构（必须采用）**

```
mocks/
├── handlers.ts      # 定义所有 API handler
├── node.ts          # setupServer(...handlers)
└── browser.ts       # setupWorker(...handlers)  —— 用于浏览器开发环境
```

注意 MSW 在浏览器中使用 `setupWorker`（在 `msw/browser` 中），在 Node 测试中使用 `setupServer`（在 `msw/node` 中）。本示例只展示了 node 端，但 React 教程也应该介绍 `setupWorker` 用于开发环境。

**2. vitest.setup.ts 生命周期（必须采用）**

直接在 `setupFiles` 中使用标准的 `beforeAll`/`afterEach`/`afterAll` 模式。这个模式是 MSW 官方推荐的最佳实践，适用于所有规模的项目。

**3. `globals: true` + `"types": ["vitest/globals"]`（强烈推荐）**

减少测试文件的样板 import，专注于测试逻辑本身。

**4. 文件级环境声明（视需要采用）**

```ts
/**
 * @vitest-environment jsdom
 */
```

在 React 组件测试中，默认应为 `jsdom` 或 `happy-dom`。纯逻辑/API 测试可以使用 `node` 环境以获得更好性能。

### 11.2 需要补充/增强的模式

**1. 添加测试工具函数**

示例没有封装常用的测试模式。React 教程应添加：

```ts
// test-utils.tsx
import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'

function AllTheProviders({ children }: { children: React.ReactNode }) {
  return <SomeProvider>{children}</SomeProvider>
}

function customRender(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: AllTheProviders, ...options })
}

export * from '@testing-library/react'
export { customRender as render }
```

**2. 示例 handler 过于简单**

真实 handler 应包含：
- 动态请求参数解析 `http.get('/api/user/:id', ({ params }) => ...)`
- 请求体解析 `http.post('/api/login', async ({ request }) => { const body = await request.json() })`
- 条件响应（不同输入返回不同数据）
- 错误响应
- 延迟模拟 `await delay(100)`

**3. 测试覆盖不足**

示例只覆盖了成功路径。React 教程应涵盖：
- 加载状态（延迟响应）
- 空数据状态
- 错误状态（4xx、5xx、网络错误）
- 边界情况（大量列表、特殊字符）

**4. `vitest ^0.30.1` 过旧**

React 教程应使用最新 vitest v3.x，配合最新 jsdom 或 happy-dom。MSW 应使用 v2.x 最新版（当前至少 v2.7.x+，示例使用 2.11.2 已是最新）。

**5. 缺少 browser worker 示例**

示例只展示了 `setupServer`（用于测试）。React 教程还应展示：

```ts
// mocks/browser.ts
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers.js'

export const worker = setupWorker(...handlers)
```

用于开发环境（Vite 插件方式集成或条件性启动）。

### 11.3 推荐的新项目 package.json 依赖

```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^6.x",
    "@testing-library/react": "^16.x",
    "@testing-library/user-event": "^14.x",
    "jsdom": "^25.x",
    "msw": "^2.x",
    "typescript": "^5.x",
    "vitest": "^3.x"
  }
}
```

### 11.4 vitest.config.ts 完整推荐配置

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
})
```

**变化的说明：**
- 添加 `@vitejs/plugin-react` 以支持 JSX 转换
- 设置 `environment: 'jsdom'` 作为默认环境（无需每个文件声明）
- 设置 `css: true` 让 CSS import 不会报错（或使用 `css: { modules: { ... } }`）

### 11.5 vitest.setup.ts 完整推荐配置

```ts
import '@testing-library/jest-dom/vitest'
import { server } from './mocks/node'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

**变化说明：**
- 添加 `@testing-library/jest-dom/vitest` 以获得 `toBeInTheDocument()` 等 DOM 断言
- 使用 `server.listen({ onUnhandledRequest: 'error' })` 在测试中捕获未 mock 的请求（防止遗漏）

---

## 附：测试输出示例

运行 `vitest run` 的输出（两个项目类似）：

```
✓ example.test.ts (1 test) 413ms
✓ example-jsdom.test.ts (1 test) 503ms

Tests  4 passed (4)
Files  2 of 2 passed
  Time  1.02s
```

每条测试文件内包含 2 个 it 块（REST + GraphQL），总计 4 个测试通过。
