---
tags:
  - 测试/迁移
  - 工具/Jest
  - 工具/Vitest
created: 2026-05-22
---

# 第14章：从 Jest 迁移到 Vitest

## 学习目标

- 理解从 Jest 迁移到 Vitest 的动机、风险和渐进策略
- 掌握 `jest.*` → `vi.*` 的全局 API 映射关系
- 能独立完成 `jest.config.js` → `vitest.config.ts` 的配置迁移
- 处理需要调整的特殊模式（`vi.importActual` 异步、`vi.hoisted`、ESM 差异）
- 通过 7 步检查清单完成一个项目的迁移

---

## 14.1 迁移动机与风险评估

### 为什么迁移

Jest 是前端测试框架的事实标准，但它的架构设计根植于 CommonJS 时代。Vitest 的出现不是简单的"又一个测试框架"——它利用了 Vite 的原生 ESM 能力和 HMR 架构，在开发体验上有本质区别：

| 维度 | Jest | Vitest |
|------|------|--------|
| **启动速度** | 需要初始化 Jest 自身的 transform 管道（babel-jest / ts-jest） | 原生继承 Vite 的 transform，几乎无额外启动成本 |
| **TypeScript** | 需要 `ts-jest` 或 `@babel/preset-typescript` | 通过 esbuild/swc 原生处理，无需额外配置 |
| **ESM 支持** | 实验性，需 `--experimental-vm-modules` | 原生 ESM（Vite 基于 ESM 构建） |
| **HMR / Watch** | 文件变更后重新运行测试套件 | 智能模块图缓存，变更仅重跑相关测试 |
| **配置复杂度** | Jest 配置与构建配置（webpack/vite）完全独立 | 继承 Vite 配置，`alias`、`plugins` 天然一致 |
| **并行性能** | 进程级隔离，内存开销大 | worker_threads / child_processes 灵活切换 |

选择 Vitest 的核心理由：**如果你的项目已经使用 Vite 构建，Vitest 零成本启动**。你不再需要维护一套平行于构建管的测试 transform 配置。`resolve.alias`、`plugins`、`define`——这些 Vite 里已经配置好的东西在测试中直接生效。

### 风险评估

并非所有项目都适合立即迁移。以下是兼容性矩阵：

| 场景 | 迁移难度 | 注意事项 |
|------|---------|---------|
| 纯 Jest API（`jest.fn`、`jest.mock`、`describe`、`it`、`expect`） | 低 | 全局替换 `jest` → `vi`，大部分 1:1 兼容 |
| 快照测试 | 低 | 格式完全兼容，`-u` 更新即可 |
| 配置（transform、moduleNameMapper、testEnvironment） | 中 | 映射到 Vite 体系，见 14.3 |
| `jest.requireActual` | 中 | 改为异步的 `vi.importActual` |
| `jest.mock` 工厂引用外部变量 | 中 | 需要用 `vi.hoisted()` |
| 自定义 Jest 环境（`@jest-environment`） | 中 | 改为 `@vitest-environment` |
| `jest-extended` 等三方 matcher | 中 | 需要找替代品或自己写适配 |
| 自定义 transformer（`jest-transform` 插件） | 高 | 需要改为 Vite plugin |
| 内联 `jest.d.ts` 类型扩展 | 中 | 需要改为 vitest 类型扩展 |

### 渐进式迁移策略

**不要一次全部重写。** 推荐的分步策略：

```
第 1 阶段：并行跑 —— 保留 Jest 配置，添加 Vitest 配置
  ├─ 迁移 20% 的业务逻辑测试到 Vitest
  └─ CI 中同时跑 Jest 和 Vitest，对比结果

第 2 阶段：主力迁移 —— 新测试全用 Vitest 写
  ├─ 迁移 60% 的测试
  ├─ 修复本阶段暴露的兼容性问题
  └─ 老测试仍用 Jest 跑

第 3 阶段：收尾 —— 迁移剩余测试
  ├─ 解决最后 20% 的顽固测试
  ├─ 移除 Jest 依赖
  └─ 清理 jest.config.ts 和 jest 相关类型
```

---

## 14.2 全局 API 对照

### 核心映射

```typescript
// ─── 通用 API ───
jest.fn()              → vi.fn()
jest.mock()            → vi.mock()
jest.spyOn()           → vi.spyOn()
jest.unmock()          → vi.unmock()
jest.clearAllMocks()   → vi.clearAllMocks()
jest.resetAllMocks()   → vi.resetAllMocks()
jest.restoreAllMocks() → vi.restoreAllMocks()

// ─── 定时器 ───
jest.useFakeTimers()   → vi.useFakeTimers()
jest.useRealTimers()   → vi.useRealTimers()
jest.advanceTimersByTime() → vi.advanceTimersByTime()
jest.runAllTimers()    → vi.runAllTimers()
jest.runOnlyPendingTimers() → vi.runOnlyPendingTimers()

// ─── 模块操作 ───
jest.requireActual()   → vi.importActual()       // ⚠️ 异步，返回 Promise
jest.requireMock()     → vi.importMock()          // ⚠️ 异步，返回 Promise
jest.createMockFromModule() → vi.importMock()     // ⚠️ 行为不同，用 vi.mock + factory

// ─── 配置 ───
jest.setTimeout(ms)    → vi.setConfig({ testTimeout: ms })
jest.getTimerCount()   → vi.getTimerCount()
```

> **自我验证说明**：上述映射表基于 Vitest 官方迁移指南和 Jest API 对照表。`vi.fn()`、`vi.mock()`、`vi.spyOn()` 的签名与 Jest 版本几乎 1:1 兼容。参考 [Vitest 迁移指南](https://vitest.dev/guide/migration.html)。

### 关键差异详解

#### 1. `vi.fn()` —— 签名 1:1 兼容

```typescript
// Jest
const fn = jest.fn()
const add = jest.fn((a: number, b: number) => a + b)

// Vitest
const fn = vi.fn()
const add = vi.fn((a: number, b: number) => a + b)

// 链式调用完全一致
vi.fn().mockReturnValue(42)
vi.fn().mockResolvedValue('data')
vi.fn().mockImplementation(() => 'impl')
vi.fn().mockReturnValueOnce(1).mockReturnValueOnce(2)
```

`MockInstance` 的接口在 Vitest 和 Jest 中几乎一致：
- `mock.calls`、`mock.results`、`mock.contexts`、`mock.lastCall`
- `mockClear()`、`mockReset()`、`mockRestore()`
- `getMockName()`、`mockName()`

#### 2. `vi.mock()` —— hoist 行为一致

```typescript
// Jest
jest.mock('./api', () => ({
  fetchUsers: jest.fn().mockResolvedValue([]),
}))

// Vitest
vi.mock('./api', () => ({
  fetchUsers: vi.fn().mockResolvedValue([]),
}))
```

两者的 hoist 行为完全一致：`vi.mock()` / `jest.mock()` 都会被提升到文件顶部，在 import 执行前生效。

关键差异在工厂函数内的变量引用（见 14.4）。

#### 3. `vi.spyOn()` —— 完全兼容

```typescript
// Jest
const spy = jest.spyOn(console, 'log')
spy.mockImplementation(() => {})

// Vitest
const spy = vi.spyOn(console, 'log')
spy.mockImplementation(() => {})

// getter/setter spy
vi.spyOn(localStorage, 'getItem', 'get').mockReturnValue('mocked')
vi.spyOn(document, 'title', 'set')
```

`mockRestore()` 在两者中行为一致：仅对 spy 有效，恢复原始实现。

#### 4. 定时器——API 类似但有细微差异

```typescript
// Jest
jest.useFakeTimers({ now: new Date('2025-01-01') })
jest.advanceTimersByTime(1000)

// Vitest
vi.useFakeTimers({ now: new Date('2025-01-01') })
vi.advanceTimersByTime(1000)
```

Vitest 额外支持：
- `vi.advanceTimersByTimeAsync(ms)` —— 异步版，处理 pending promise
- `vi.advanceTimersToNextTimerAsync()` —— 异步版
- `vi.getRealSystemTime()` —— 获取真实系统时间
- `vi.setSystemTime(time)` —— 设置系统时间

#### 5. `jest.setTimeout` → `vi.setConfig`

```typescript
// Jest
jest.setTimeout(10000)

// Vitest（方式 1：全局配置）
vi.setConfig({ testTimeout: 10000 })

// Vitest（方式 2：单测试超时）
it('slow test', async () => {
  // ...
}, 10000) // 第三个参数

// Vitest（方式 3：describe 级超时）
describe('slow suite', () => {
  it('test', async () => { /* ... */ })
}, 10000)
```

---

## 14.3 配置迁移

### 对照表

```typescript
// jest.config.js
module.exports = {
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testEnvironment: 'jsdom',
  setupFiles: ['./jest.setup.ts'],
  globals: {
    'ts-jest': { tsconfig: 'tsconfig.json' },
  },
  roots: ['<rootDir>/src'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
}
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],                   // Vite plugins 替代 Jest transform
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'), // 替代 moduleNameMapper
    },
  },
  test: {
    environment: 'jsdom',               // 替代 testEnvironment
    setupFiles: ['./vitest.setup.ts'],  // 替代 setupFiles
    globals: true,                      // 替代 Jest 的 globals
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist'],
    css: true,                          // 处理 CSS 导入
  },
})
```

### Transform → Plugins

Jest 需要用 `transform` 字段告诉它怎么处理非 JS 文件。Vitest 继承 Vite 的插件体系，不需要独立的 transform 配置：

| Jest transform | Vitest 等价 |
|---------------|------------|
| `ts-jest` | `@vitejs/plugin-react` 或 esbuild（内置 TS 支持） |
| `babel-jest` | `@vitejs/plugin-react`（内置 JSX transform） |
| 自定义 transform | 写一个 Vite plugin |
| `file-mock` | `vi.mock('*.svg')` 或配置 `test.server.deps.inline` |

**核心差异**：Jest 的 transform 是测试独有的；Vitest 的 plugins 与 Vite 构建共享——你已经配好了，不需要再配一次。

### moduleNameMapper → resolve.alias

```typescript
// Jest
moduleNameMapper: {
  '^@/(.*)$': '<rootDir>/src/$1',
  '\\.(css|less|scss)$': 'identity-obj-proxy',
}

// Vitest 方式 1：resolve.alias（推荐，与 Vite 共享）
resolve: {
  alias: {
    '@': path.resolve(__dirname, 'src'),
  },
}

// Vitest 方式 2：test alias（仅测试环境）
test: {
  alias: {
    '@': path.resolve(__dirname, 'src'),
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
}
```

> **自我验证说明**：`resolve.alias` 和 `test.alias` 的区别在于作用域。`resolve.alias` 同时在构建和测试中生效；`test.alias` 仅测试生效。CSS mock 可以放在 `test.alias` 中，不影响构建配置。

### setupFiles 配置一致

```typescript
// Jest
setupFiles: ['./jest.setup.ts']

// Vitest
setupFiles: ['./vitest.setup.ts']
```

Jest 和 Vitest 都使用 `setupFiles` 配置项。在 Vitest 中，`setupFiles` 在每个测试文件执行前运行一次，行为与 Jest 基本一致。区别在于 Jest 早期的版本区分 `setupFiles`（框架初始化前）和 `setupTestFrameworkScriptFile`（框架初始化后），而 Vitest 只有一个 `setupFiles`，简化了配置。

### 环境头部注释

```typescript
// Jest（文件级环境声明）
// @jest-environment jsdom

// Vitest
// @vitest-environment jsdom

// 也支持覆盖为其他环境
// @vitest-environment node
// @vitest-environment happy-dom
```

---

## 14.4 需要调整的模式

### 1. `jest.requireActual` → `vi.importActual`（异步！）

这是迁移中最容易被忽略的差异：

```typescript
// Jest（同步）
const actualModule = jest.requireActual('./utils')

// Vitest（异步！）
const actualModule = await vi.importActual('./utils')
```

在 `vi.mock` 工厂函数中使用时：

```typescript
// Jest
jest.mock('./utils', () => ({
  ...jest.requireActual('./utils'),
  greet: jest.fn(),
}))

// Vitest
vi.mock('./utils', async (importOriginal) => {
  const mod = await importOriginal<typeof import('./utils')>()
  return { ...mod, greet: vi.fn() }
})
```

> **自我验证说明**：`vi.importActual` 返回 `Promise<any>`。`vi.mock()` 的工厂函数从 Vitest v1.3 开始支持 async factory，可以直接 `async (importOriginal) => {...}`。参考 [Vitest mock 文档](https://vitest.dev/guide/mocking.html#partial-mocking-with-importoriginal)。

### 2. `vi.hoisted()`——处理工厂函数中的外部变量

这是另一个最常见的迁移陷阱：

```typescript
// ❌ Jest 中合法的写法在 Vitest 中会静默失败
import { vi } from 'vitest'

const mockUser = { name: 'Alice' }          // 这行会在运行时执行
vi.mock('./api', () => ({                   // 这行被 hoist 到文件顶部
  fetchUser: vi.fn().mockResolvedValue(mockUser), // mockUser 此时是 undefined！
}))

// ✅ Vitest 的正确写法
import { vi } from 'vitest'

const { mockUser } = vi.hoisted(() => ({    // 这行也被 hoist 到文件顶部
  mockUser: { name: 'Alice' },
}))

vi.mock('./api', () => ({
  fetchUser: vi.fn().mockResolvedValue(mockUser), // ✅ 现在可以用了
}))
```

**为什么？**

`vi.mock()` 在编译阶段被提升（hoist）到文件顶部，在 import 语句之前执行。而工厂函数内的变量引用在提升后指向的是未初始化的变量——因为 `const mockUser = ...` 没有被提升。

`vi.hoisted()` 是 Vitest 提供的解决方案：它将其回调也提升到文件顶部，在 `vi.mock()` 之前执行。这样创建的变量在工厂函数中可用。

**多个 hoisted 变量的组合：**

```typescript
const { mockFn, mockData } = vi.hoisted(() => {
  return {
    mockFn: vi.fn(),
    mockData: { id: 1, name: 'Test' },
  }
})

vi.mock('./service', () => ({
  process: mockFn,
  default: { fetch: vi.fn().mockResolvedValue(mockData) },
}))
```

### 3. `jest.enableAutomock` / `jest.disableAutomock`

Jest 的自动 mock 功能在 Vitest 中不支持：

```typescript
// Jest
jest.enableAutomock()
const utils = require('./utils') // 所有导出被自动 mock
jest.disableAutomock()

// Vitest —— 无直接等价，需要显式 vi.mock()
vi.mock('./utils') // 手动 mock
const utils = await import('./utils') // 所有导出是 vi.fn()
```

> 自动 mock 在实践中并不常用，迁移时手动替换即可。

---

## 14.5 模块 Mock 的差异

### ESM/CJS 混合处理

Vitest 原生基于 ESM，处理 CJS 模块的方式与 Jest 不同：

```typescript
// Jest —— 对 CJS 模块的 mock 直截了当
jest.mock('lodash', () => ({
  debounce: jest.fn((fn) => fn),
}))

// Vitest —— 同样支持，但 CJS 模块可能需要配置 deps
// vitest.config.ts
test: {
  deps: {
    // 将 CJS 模块转换为 ESM
    interopDefault: true,
    // 某些 CJS 模块需要显式注入
    inline: ['lodash'],
  },
}
```

> **自我验证说明**：Vitest 的 `deps.inline` 选项控制哪些依赖应在测试时被内联处理。对 CJS 模块，如果 `vi.mock` 不生效，尝试在 `vitest.config.ts` 中配置 `deps.interopDefault: true`。参考 [Vitest deps 文档](https://vitest.dev/config/#deps)。

### `__mocks__` 目录行为

Jest 支持通过 `__mocks__` 目录自动 mock 模块：

```
src/
  __mocks__/
    api.ts          // jest.mock('./api') 时自动使用这个文件
  api.ts
```

Vitest **不支持** `__mocks__` 目录的自动发现。你需要显式使用 `vi.mock()`：

```typescript
// Jest —— 自动使用 __mocks__/api.ts
jest.mock('./api')

// Vitest —— 没有自动 __mocks__ 发现
vi.mock('./api')                    // 所有导出变为 vi.fn()
vi.mock('./api', () => ({
  // 需要手动写 factory，或异步保留部分原始
}))                                 // 自定义 mock
```

迁移方式：

```typescript
// 将 __mocks__/api.ts 的内容转换为 vi.mock factory
vi.mock('./api', () => ({
  fetchUsers: vi.fn().mockResolvedValue([
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
  ]),
  saveUser: vi.fn().mockResolvedValue({ id: 3 }),
}))
```

### `importOriginal` 的异步特性

```typescript
// Vitest 的异步 factory 模式

vi.mock('./config', async (importOriginal) => {
  // importOriginal 返回 Promise<typeof module>
  const config = await importOriginal<typeof import('./config')>()

  return {
    ...config,                   // 保留原始导出
    FEATURE_FLAG: false,         // 只覆盖这一个
  }
})
```

关键认知：

1. `importOriginal` 始终返回 Promise——无论模块是 ESM 还是 CJS
2. 泛型参数 `<typeof import('./config')>` 是可选的，但推荐使用以获得类型安全
3. async factory 支持从 Vitest v1.3+ 开始；之前的版本需要同步 factory

### `jest.createMockFromModule` 替代

```typescript
// Jest
const mockModule = jest.createMockFromModule('./user')

// Vitest
// 方式 1：使用 vi.importMock（异步）
const mockModule = await vi.importMock('./user')

// 方式 2：参考实现（手动）
vi.mock('./user', () => ({
  User: class User { /* 手动 mock 实现 */ },
  createUser: vi.fn(),
  validateUser: vi.fn(),
}))
```

> **为什么：Vitest 的 ESM 方案对模块 Mock 至关重要**
>
> Jest 诞生于 CommonJS 时代，它的模块 mock 机制（`jest.mock`、`jest.requireActual`）基于 Node.js 的 `require.cache` 操作——在模块被 require 之前拦截它，替换为 mock 版本。这在 CJS 中工作良好，因为 `require` 是同步的、可拦截的。
>
> Vitest 基于 Vite 的 ESM 体系。ESM 的 `import` 是静态的、异步的、在模块图解析阶段就确定了的。你不能像操作 `require.cache` 那样拦截 ESM 的 `import`。这意味着：
>
> 1. **`vi.mock` 必须在编译阶段 hoist**——在模块代码执行之前，模块图解析阶段就替换掉模块引用。这就是为什么 `vi.mock` 会被提升到文件顶部
> 2. **`vi.importActual` 必须是异步的**——ESM 的 `import()` 天生返回 Promise，同步读取在 ESM 中不可能实现
> 3. **`vi.hoisted` 是必要的**——因为 hoist 后的 `vi.mock` 工厂函数生命周期早于普通变量初始化，必须用同样被 hoist 的代码来创建变量
>
> 这解释了为什么从 Jest 迁移时最常踩的两个坑都是 ESM 相关的：`vi.importActual` 是异步的、`vi.mock` 工厂不能引用外部变量（需要 `vi.hoisted`）。这些不是 Vitest 的设计缺陷——它们是 ESM 架构的必然结果。
>
> **长远来看，ESM 是前端标准**。Vite/Vitest 的 ESM 原生支持意味着你的测试环境和生产环境使用相同的模块解析机制，不会出现 Jest 中 CJS 转 ESM 时常见的兼容性问题（如 `jest.mock('node-fetch')` 不工作、ESM-only 的第三方库无法测试等）。选择 Vitest 不仅是选择一个测试框架，更是选择了一致的模块体系。

---

## 14.6 迁移检查清单

### 步骤 1：安装 Vitest 并创建配置文件

```bash
npm install -D vitest
```

创建或修改 `vitest.config.ts`：

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
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

### 步骤 2：替换 setup 文件

```typescript
// src/test/setup.ts
// 替换 jest.setup.ts

import '@testing-library/jest-dom/vitest'

// 调整 MOCK 前缀：jest → vi
// 如果之前用了 jest-dom 的 expect.extend，改为 vitest 版本
```

### 步骤 3：全局替换 jest → vi

大部分替换是文本级别的：

```bash
# 全局替换（大部分场景）
# jest.fn() → vi.fn()
# jest.mock() → vi.mock()
# jest.spyOn() → vi.spyOn()
# jest.useFakeTimers() → vi.useFakeTimers()
```

危险：`jest` 也可能出现在非测试代码中（如 StoryBook 的 jest 配置），替换时注意范围。

### 步骤 4：处理 jest.requireActual → vi.importActual

搜索所有 `jest.requireActual` 调用：

```typescript
// 同步 → 异步
const utils = jest.requireActual('./utils')
// 改为：
const utils = await vi.importActual('./utils')
```

在 `vi.mock` factory 中使用时：

```typescript
vi.mock('./utils', async (importOriginal) => {
  const mod = await importOriginal()
  return { ...mod, greet: vi.fn() }
})
```

### 步骤 5：处理 jest.mock 工厂中的外部变量

搜索所有 `vi.mock()` 工厂函数，检查是否引用了外部变量：

```typescript
// ❌ 有问题的模式
const mockData = { name: 'test' }
vi.mock('./api', () => ({
  fetch: vi.fn().mockResolvedValue(mockData), // mockData 可能是 undefined
}))

// ✅ 修复
const { mockData } = vi.hoisted(() => ({
  mockData: { name: 'test' },
}))
vi.mock('./api', () => ({
  fetch: vi.fn().mockResolvedValue(mockData),
}))
```

### 步骤 6：验证快照兼容性

```bash
# 重新生成所有快照
npx vitest run -u
```

Vitest 的快照格式与 Jest 高度相似，但可能因 `snapshotFormat` 配置有细微差异。常见的调整：

```typescript
// vitest.config.ts
test: {
  snapshotFormat: {
    // 控制快照序列化格式
    printBasicPrototype: true,
  },
}
```

### 步骤 7：运行全部测试，修复剩余差异

```bash
npx vitest run
```

常见问题及修复：

| 错误 | 原因 | 修复 |
|------|------|------|
| `TypeError: environment is not defined` | `testEnvironment` → `environment` | 在 vitest.config.ts 中使用 `environment` |
| `Error: defineConfig is not defined` | 导入了错误的 defineConfig | 使用 `vitest/config` 而非 `vite` |
| `Cannot find module 'xxx'` | alias 没有正确映射 | 检查 `resolve.alias` 配置 |
| `vi.mock factory must return an object` | factory 返回了非对象 | factory 必须返回模块形状的对象 |
| `[vitest] No "vi.mock" factory is defined` | `vi.mock` 无 factory 且模块不在 `__mocks__` | 添加 factory 或使用 `vi.mock('./mod', () => ({}))` |
| `async callback must return a promise` | `vi.mock` 的 factory 的 async 签名问题 | 检查版本，Vitest v1.3+ 才支持 async factory |

> **渐进式示例：逐步迁移一个 Jest 测试文件**
>
> 以最常见的组件测试为例，展示从 Jest 到 Vitest 的逐步迁移过程：
>
> **原始文件（Jest）**
> ```typescript
> // __tests__/UserProfile.test.tsx
> import { render, screen } from '@testing-library/react'
> import { UserProfile } from '../UserProfile'
>
> jest.mock('../api', () => ({
>   fetchUser: jest.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
> }))
>
> import { fetchUser } from '../api'
>
> it('displays user name', async () => {
>   render(<UserProfile userId={1} />)
>   expect(await screen.findByText('Alice')).toBeInTheDocument()
>   expect(fetchUser).toHaveBeenCalledWith(1)
> })
> ```
>
> **第 1 步：替换全局 API（纯文本替换，60% 的测试到此结束）**
> ```typescript
> import { vi } from 'vitest'
>
> vi.mock('../api', () => ({
>   fetchUser: vi.fn().mockResolvedValue({ id: 1, name: 'Alice' }),
> }))
> ```
>
> **第 2 步：处理 vi.mock 的外部变量引用（30% 的测试需要）**
> ```typescript
> // 如果 factory 中引用了外部变量，用 vi.hoisted() 包裹
> const { mockUser } = vi.hoisted(() => ({
>   mockUser: { id: 1, name: 'Alice' },
> }))
>
> vi.mock('../api', () => ({
>   fetchUser: vi.fn().mockResolvedValue(mockUser),
> }))
> ```
>
> **第 3 步：处理 __mocks__ 自动发现和 requireActual（10% 的测试需要）**
> ```typescript
> // 如果之前依赖 __mocks__/ 目录的自动发现，改为显式 vi.mock + factory
> // 如果之前用了 jest.requireActual，改为 await vi.importActual
> vi.mock('./api', async (importOriginal) => {
>   const mod = await importOriginal()
>   return { ...mod, fetchUser: vi.fn() }
> })
> ```
>
> **迁移预估**：一个 100 个测试文件的项目，约 60 个只需要第 1 步（纯文本替换），30 个需要第 2 步（hoisted 调整），10 个需要第 3 步（requireActual 或 `__mocks__` 改造）。这正是渐进式迁移策略可行性的基础。

---

## 14.7 迁移完整示例

### 迁移前（Jest）

```typescript
// jest.config.js
module.exports = {
  transform: { '^.+\\.tsx?$': 'ts-jest' },
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/src/$1' },
  testEnvironment: 'jsdom',
  setupFiles: ['./jest.setup.ts'],
  roots: ['<rootDir>/src'],
}

// jest.setup.ts
import '@testing-library/jest-dom'

// jest.mock 工厂引用外部变量
const mockData = { id: 1, name: 'Alice' }

jest.mock('./api', () => ({
  fetchUser: jest.fn().mockResolvedValue(jest.requireActual('./api').DEFAULT_USER),
  updateUser: jest.fn().mockResolvedValue(mockData),
}))

// user.test.ts
import { fetchUser, updateUser } from './api'

describe('user API', () => {
  it('fetches default user', async () => {
    const user = await fetchUser()
    expect(user.name).toBe('Default')
  })

  it('updates user', async () => {
    const result = await updateUser({ name: 'Alice' })
    expect(result.name).toBe('Alice')
  })
})
```

### 迁移后（Vitest）

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})

// src/test/setup.ts
import '@testing-library/jest-dom/vitest'

// user.test.ts
import { vi } from 'vitest'

const { mockData } = vi.hoisted(() => ({
  mockData: { id: 1, name: 'Alice' },
}))

vi.mock('./api', async (importOriginal) => {
  const mod = await importOriginal<typeof import('./api')>()
  return {
    ...mod,
    fetchUser: vi.fn().mockResolvedValue(mod.DEFAULT_USER),
    updateUser: vi.fn().mockResolvedValue(mockData),
  }
})

import { fetchUser, updateUser } from './api'

describe('user API', () => {
  it('fetches default user', async () => {
    const user = await fetchUser()
    expect(user.name).toBe('Default')
  })

  it('updates user', async () => {
    const result = await updateUser({ name: 'Alice' })
    expect(result.name).toBe('Alice')
  })
})
```

### 迁移要点总结

| 迁移项 | 操作 |
|--------|------|
| `jest.fn()` | 全局替换为 `vi.fn()` |
| `jest.requireActual('./x')` | 改为 `await vi.importActual('./x')` |
| 外部变量在 mock factory 中 | 用 `vi.hoisted()` 包裹 |
| `jest.mock('./x')` 自动 __mocks__ 发现 | 改为显式 `vi.mock('./x', factory)` |
| `jest.config.js` | 改为 `vitest.config.ts`，复用 Vite 配置 |
| `transform` | 改为 Vite plugins |
| `moduleNameMapper` | 改为 `resolve.alias` |
| `testEnvironment` | 改为 `environment` |
| `setupFiles` | 名称不变（行为一致） |
| `@jest-environment` 注释 | 改为 `@vitest-environment` |
| `jest.setTimeout(ms)` | 改为 `vi.setConfig({ testTimeout: ms })` |

---

## 14.8 本章练习

1. **配置迁移**：将以下 Jest 配置完整迁移到 Vitest：

```javascript
// jest.config.js
module.exports = {
  transform: { '^.+\\.tsx?$': 'ts-jest' },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.svg$': '<rootDir>/__mocks__/svgMock.js',
  },
  testEnvironment: 'jsdom',
  setupFiles: ['./jest.setup.ts'],
  globals: { 'ts-jest': { tsconfig: 'tsconfig.test.json' } },
  testTimeout: 15000,
  roots: ['<rootDir>/src'],
}
```

2. **修复 mock 工厂**：以下代码在 Vitest 中不工作，请修复：

```typescript
import { vi } from 'vitest'

const userId = 'test-user-123'
const mockApi = vi.fn().mockResolvedValue({ data: [] })

vi.mock('./api', () => ({
  fetchData: mockApi,
  getUserId: vi.fn().mockReturnValue(userId),
}))
```

3. **迁移 requireActual**：将以下 Jest 测试迁移到 Vitest：

```typescript
jest.mock('./config', () => ({
  ...jest.requireActual('./config'),
  getFeatureFlag: jest.fn().mockReturnValue(false),
}))
```

4. **完整项目迁移**：找一个你已有的 Jest 项目（或示例项目），按 14.6 的 7 步检查清单完成完整迁移。至少覆盖：
   - 模拟函数（`jest.fn()`）
   - 模块 mock（`jest.mock()`）
   - 监听（`jest.spyOn()`）
   - 快照测试
   - 定时器测试

---

## 14.9 本章总结

- 迁移的核心收益：零额外 transform 配置、原生 ESM、更快的 watch 模式
- 渐进式迁移策略：并行跑 → 主力迁移 → 收尾，不要一次全部重写
- **最大陷阱**：`jest.requireActual` 是同步的，`vi.importActual` 是异步的
- **第二大陷阱**：`vi.mock` 工厂中引用外部变量需要用 `vi.hoisted()`
- 配置迁移的核心思路：Jest 自有配置 → Vite 体系（plugins、alias）
- 快照兼容性高，但建议重新生成
- 迁移完成后移除 Jest 依赖和 `jest.config`，避免混淆

## 关联阅读

- [第3章：Vitest基础](03-Vitest基础.md) — vi.fn / vi.mock 基础 API
- [第1章：测试架构思维](01-测试架构思维.md) — Vitest vs Jest 的架构级对比
- [附录A：快速参考](附录A-快速参考.md) — Jest→Vitest 速查对照表
