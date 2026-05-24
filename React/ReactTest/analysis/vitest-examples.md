# Vitest Monorepo Examples 分析报告

> 分析日期：2026-05-22
> 来源：`vitest-monorepo/examples/` (Vitest 官方 monorepo)

---

## 1. 全部示例目录清单

| 目录 | 包名 | 说明 |
|------|------|------|
| **basic** | `@vitest/example-test` | 最基础的 Vitest 示例：基本断言、snapshot、suite 结构。最小化配置。 |
| **fastify** | `@vitest/example-fastify` | Fastify HTTP 服务测试：HTTP injection、supertest、fetch 三种模式。 |
| **in-source-test** | `@vitest/example-in-source-test` | 源码内联测试：`import.meta.vitest` 模式将测试与源码共存。 |
| **lit** | `@vitest/example-lit` | Lit Web Component 测试：browser 模式 + Playwright + DOM 交互。 |
| **opentelemetry** | `@vitest/example-opentelemetry` | OpenTelemetry 集成：在测试中使用 tracing span，browser 模式可选。 |
| **profiling** | `@vitest/example-profiling` | CPU/Heap profiling 集成：`--cpu-prof`、`--heap-prof`、`globalSetup`。 |
| **projects** | `@vitest/example-projects` | **Monorepo workspace 测试：含 React 客户端 + Fastify 服务端两个 package。** |
| **typecheck** | `@vitest/example-typecheck` | TypeScript 类型测试：`expectTypeOf`、`test-d.ts` 类型断言文件。 |

---

## 2. vitest.config.ts 模式总结

### 模式 A：最简配置（basic, typecheck）

```ts
/// <reference types="vitest/config" />

import { defineConfig } from 'vite'

export default defineConfig({
  test: {
    // globals: true,  // 注释掉了，需要显式 import
  },
})
```

- 使用 `vite` 的 `defineConfig` 而非 `vitest/config` 的（两者都可用）
- 三项式 reference 注释提供类型提示
- 不设 `globals: true`，测试文件需 `import { describe, test, expect } from 'vitest'`

### 模式 B：in-source-test 配置

```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    includeSource: ['src/**/*.{js,ts}'],
  },
})
```

- 从 `vitest/config` 导入 `defineConfig`（提供更精确的类型）
- `includeSource` 让 `src/` 下的文件也被视为测试（配合 `import.meta.vitest`）

### 模式 C：browser 模式（lit, opentelemetry）

```ts
import { playwright } from '@vitest/browser-playwright'
import { defineConfig } from 'vite'

export default defineConfig({
  test: {
    browser: {
      enabled: true,
      provider: playwright(),
      instances: [
        { browser: 'chromium' },
      ],
    },
  },
})
```

- `@vitest/browser-playwright` 作为 provider
- `browser.instances` 数组指定多浏览器（此处仅 chromium）
- opentelemetry 示例中 `enabled: false` 通过 CLI 标志 `--browser.enabled=true` 开启

### 模式 D：workspace/projects 模式

```ts
// 根 vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    projects: ['packages/*'],
  },
})
```

- 通过 `test.projects` 指向子 package 目录
- 每个子 package **可以有自己的 `vitest.config.ts`**，根配置会合并子配置

### 子 package 的 vitest.config.ts（React 客户端）

```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: './vitest.setup.ts',
  },
})
```

- `environment: 'jsdom'` 提供浏览器 API 模拟
- `setupFiles` 指向 `vitest.setup.ts`，用于一次性的全局设置

### 模式 E：profiling 配置

```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    watch: false,
    globalSetup: './global-setup.ts',
    fileParallelism: false,
    execArgv: [
      '--cpu-prof',
      '--cpu-prof-dir=vitest-profile',
      '--heap-prof',
      '--heap-prof-dir=vitest-profile',
    ],
  },
})
```

- `globalSetup` 运行全局 setup 脚本
- `fileParallelism: false` 单文件串行执行（生成单份 profile）
- `execArgv` 传递 Node.js CPU/heap profiler 参数

---

## 3. 测试结构模式

### 目录结构约定

```
src/           # 源码
  basic.ts     # 实现
test/          # 测试
  basic.test.ts    # 对应测试
  suite.test.ts    # 更多测试
  __snapshots__/   # snapshot 自动生成
    suite.test.ts.snap
```

- 测试文件统一放在 `test/` 目录下
- 源码放在 `src/` 目录下
- Snapshot 由 Vitest 自动生成到 `test/__snapshots__/` 目录

### 测试文件基本结构

```ts
import { assert, describe, expect, it, test } from 'vitest'
import { squared } from '../src/basic.js'

test('Math.sqrt()', () => {
  expect(Math.sqrt(4)).toBe(2)
})

describe('suite name', () => {
  it('foo', () => {
    assert.equal(Math.sqrt(4), 2)
  })

  it('snapshot', () => {
    expect({ foo: 'bar' }).toMatchSnapshot()
  })
})
```

- 导入方式：显式从 `'vitest'` 导入 API
- 支持 `test` + `describe`/`it` 两种顶层结构
- 同时提供 `expect`（更可读）和 `assert`（Chai 兼容）两种断言风格

### in-source-test 结构

```ts
// src/index.ts - 源码中有测试
export function add(...args: number[]) {
  return args.reduce((a, b) => a + b, 0)
}

if (import.meta.vitest) {
  const { it, expect } = import.meta.vitest
  it('add', () => {
    expect(add()).toBe(0)
    expect(add(1)).toBe(1)
    expect(add(1, 2, 3)).toBe(6)
  })
}
```

- `import.meta.vitest` 仅在 Vitest 运行时存在，生产构建时被 tree-shake
- 测试代码通过 `if (import.meta.vitest)` 守卫，生产包不包含

---

## 4. TypeScript 配置模式

### 通用 tsconfig.json（basic, projects, typecheck）

```json
{
  "compilerOptions": {
    "target": "es2020",
    "module": "node16",
    "moduleResolution": "Node16",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "verbatimModuleSyntax": true
  },
  "include": ["src", "test"],
  "exclude": ["node_modules"]
}
```

- `strict: true` 强类型
- `verbatimModuleSyntax: true` 强制 ESM 风格的导入/导出（import 带 `.js` 扩展名）
- `include` 同时覆盖 `src` 和 `test`
- 测试文件中也使用 `.js` 扩展名导入（如 `import { squared } from '../src/basic.js'`）

### React 项目的 tsconfig.json（projects/client）

```json
{
  "compilerOptions": {
    "target": "esnext",
    "jsx": "react",
    "lib": ["esnext", "dom"],
    "module": "node16",
    "moduleResolution": "node16",
    "types": ["@testing-library/jest-dom"],
    "strict": true,
    "declaration": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    "./vitest.setup.ts"
  ]
}
```

**关键差异：**
- `jsx: "react"` — 启用 JSX 支持
- `lib: ["esnext", "dom"]` — DOM 类型支持
- `types: ["@testing-library/jest-dom"]` — 引入 jest-dom 的 `toBeInTheDocument()` 等匹配器类型
- `noEmit: true` — 不输出编译文件
- `include` 包含 `tsx` 文件和 `vitest.setup.ts`

### in-source-test 的特殊 types

```json
{
  "compilerOptions": {
    "types": ["vitest/importMeta"]
  }
}
```

- `vitest/importMeta` 类型声明提供 `import.meta.vitest` 的类型

---

## 5. React 特定示例（projects/client）

### package 版本

| 包 | 版本 |
|---|------|
| `react` | `^19.2.4` |
| `@types/react` | `^19.2.14` |
| `@vitejs/plugin-react` | `^5.1.4` |
| `@testing-library/react` | `^16.3.2` |
| `@testing-library/jest-dom` | `^6.9.1` |
| `@testing-library/user-event` | `^14.6.1` |
| `jsdom` | `^27.4.0` |
| `vitest` | `latest` |

### React 组件示例

```tsx
import React, { useState } from 'react'

const STATUS = {
  HOVERED: 'hovered',
  NORMAL: 'normal',
}

function Link({ page, children }: React.PropsWithChildren<{ page: string }>) {
  const [status, setStatus] = useState(STATUS.NORMAL)

  const onMouseEnter = () => setStatus(STATUS.HOVERED)
  const onMouseLeave = () => setStatus(STATUS.NORMAL)

  return (
    <a
      className={status}
      href={page || '#'}
      aria-label={`Link is ${status}`}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {children}
    </a>
  )
}

export default Link
```

### React 测试文件

```tsx
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'
import { expect, test } from 'vitest'
import Link from '../components/Link.js'

test('Link changes the state when hovered', async () => {
  render(
    <Link page="http://antfu.me">Anthony Fu</Link>,
  )

  const link = screen.getByText('Anthony Fu')

  expect(link).toHaveAccessibleName('Link is normal')

  await userEvent.hover(link)

  await expect.poll(() => link).toHaveAccessibleName('Link is hovered')

  await userEvent.unhover(link)

  await expect.poll(() => link).toHaveAccessibleName('Link is normal')
})
```

### React 测试要点总结

1. **环境**：`environment: 'jsdom'` 提供 DOM 模拟
2. **Setup 文件**：`vitest.setup.ts` 导入 `@testing-library/jest-dom/vitest` 注入 DOM 匹配器
3. **渲染**：使用 `@testing-library/react` 的 `render()` + `screen` 查询
4. **用户交互**：使用 `@testing-library/user-event`（高于 `fireEvent` 的推荐方式）
5. **同步断言**：直接 `expect(link).toHaveAccessibleName('Link is normal')`
6. **异步断言**：使用 **`await expect.poll(() => link).toHaveAccessibleName('Link is hovered')`** — 这是 Vitest 内置的轮询等待机制，等效于 `waitFor`
7. **状态验证**：通过 `aria-label` 断言组件内部状态变化
8. 测试中使用的是**导入的 `expect`**（非 global）

---

## 6. Workspace/Monorepo 测试模式

### 架构

```
projects/
  vitest.config.ts          # 根配置：projects: ['packages/*']
  tsconfig.json             # 根 tsconfig
  packages/
    client/                 # React 前端
      vitest.config.ts      # environment: jsdom + setupFiles
      vitest.setup.ts       # @testing-library/jest-dom/vitest
      tsconfig.json         # jsx: react + dom lib
      components/Link.tsx
      test/basic.test.tsx
    server/                 # Fastify 后端
      src/app.ts
      src/index.ts
      test/app.test.ts
      mockData.ts
```

### 配置传递规则

- 根 `vitest.config.ts` 使用 `test.projects: ['packages/*']` 建立 workspace
- Vitest 会**自动发现**每个子 package 中的 `vitest.config.ts`
- 子配置与根配置**合并**，子配置优先级更高
- server package **没有自己的 `vitest.config.ts`** — 它隐式继承根配置（但测试仍能运行，因为 server 测试不依赖 jsdom）

### Workspace 优势

- 不同 package 可设置不同的 `environment`（client 用 jsdom，server 用默认 node）
- 独立的 `setupFiles`、`tsconfig`
- 统一入口运行 `vitest` 即可执行所有 package 的测试

---

## 7. 测试文件命名约定

| 模式 | 文件 | 说明 |
|------|------|------|
| `<name>.test.ts` | `basic.test.ts`, `app.test.ts` | 标准测试文件 |
| `<name>.test.tsx` | `basic.test.tsx` | 含 JSX 的测试 |
| `<name>.test-d.ts` | `type.test-d.ts` | TypeScript 类型测试（仅类型检查，不执行） |
| `__snapshots__/<name>.test.ts.snap` | `suite.test.ts.snap` | 自动生成的 snapshot 文件 |

**Vitest 默认查找模式**（可通过 `test.include` 配置）：

- `**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}`
- `**/__tests__/**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}`

---

## 8. Mock 模式

该示例目录中**没有使用 `vi.mock`、`vi.fn`、`vi.spyOn` 的案例**。Vitest 的 mock API 在 monorepo 核心测试套件中，但不在此 examples 目录中。

不过，从观察到的模式可以推断：
- 所有示例使用**真实依赖**（Fastify 直接启动服务、Lit 直接渲染真实组件）
- `mockData.ts` 被用于提供**测试数据常量**而非真正的 mock 函数
- 推荐策略：用真实实例 + `afterAll` 清理的方式代替 mock，直到必须 mock 时才使用 `vi.mock()`

---

## 9. 异步测试模式

### 直接 async/await

```ts
test('with HTTP injection', async () => {
  const response = await app.inject({
    method: 'GET',
    url: '/users',
  })
  expect(response.statusCode).toBe(200)
})
```

### 用户事件 + await

```ts
await userEvent.hover(link)
await expect.poll(() => link).toHaveAccessibleName('Link is hovered')
```

- `userEvent.hover()` 返回 Promise，需要 `await`
- 状态变化后使用 **`await expect.poll()`**（Vitest 特性，非 waitFor）轮询直到断言通过

### 传统 setTimeout（测试中）

```ts
test('one plus one', async () => {
  await sleep(100)
  expect(1 + 1).toBe(2)
})
```

### HTTP 服务生命周期管理

```ts
afterAll(async () => {
  await app.close()
})
```

### 使用超时选项

```ts
// 在 browser mode 中可设置 timeout
await expect.element(page.getByRole('button'), { timeout: 3000 }).toHaveTextContent('3')
```

---

## 10. 对 React 测试教程的启示

### 可复用的模式

1. **最小 vitest.config.ts 模板**

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
```

2. **Setup 文件（vitest.setup.ts）**

```ts
import '@testing-library/jest-dom/vitest'
```

3. **推荐测试结构**

```
src/
  components/
    Button.tsx
  test/
    setup.ts
    Button.test.tsx
```

4. **推荐的 React 测试写法**（从 basic.test.tsx 提取）

```tsx
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { expect, test } from 'vitest'
import Component from '../Component.jsx'

test('description', async () => {
  render(<Component prop="value" />)

  const el = screen.getByText('expected text')
  expect(el).toBeInTheDocument()

  await userEvent.click(el)
  await expect.poll(() => screen.getByText('after click')).toBeInTheDocument()
})
```

5. **异步最佳实践**

- 使用 `await expect.poll()` 替代 `waitFor`（Vitest 原生）
- 不要使用 `act()` 包装 — `@testing-library/react` 已自动处理
- 用户交互始终用 `@testing-library/user-event`（模拟真实事件，非 `fireEvent`）

6. **类型配置**

- tsconfig.json 中设置 `jsx: "react"`，`types: ["@testing-library/jest-dom"]`
- 测试文件中导入 `.jsx` 扩展名（`verbatimModuleSyntax` 要求）

7. **Monorepo 多环境测试**

- React package：`environment: 'jsdom'`
- Node/API package：默认 node 环境
- 通过 `test.projects` 统一管理

### 未覆盖但需要补充的内容

以下模式在 examples 目录中缺失，但对 React 测试教程至关重要：
- `vi.mock()` 模拟外部模块
- `vi.fn()` 模拟函数
- `vi.spyOn()` 监听方法
- 配合 MSW（Mock Service Worker）的 HTTP mock
- snapshot 测试在 React 组件中的应用
- coverage 配置
- 自定义匹配器

---

## 附录：SnapShot 格式

```ts
// Vitest Snapshot v1, https://vitest.dev/guide/snapshot.html

exports[`suite name > snapshot 1`] = `
{
  "foo": "bar",
}
`;
```

- 自动生成到 `test/__snapshots__/<test-file>.snap`
- 格式清晰，版本标记为 v1
- 可通过 `vitest update` 更新
