---
tags:
  - tutorial
  - migration
  - jest
created: 2026-05-22
---

# 第十一章：从 Jest 迁移到 Vitest

## 学习目标

- 评估从 Jest 迁移到 Vitest 的成本与收益
- 掌握 API 对照关系
- 掌握配置文件迁移步骤
- 能制定分阶段迁移策略

---

## 11.1 迁移的价值

如果以下条件中的**任意三条**成立，迁移到 Vitest 将带来显著收益：

1. 项目已使用 Vite 作为构建工具
2. 团队抱怨 CI 测试太慢
3. Jest 的 ESM/CJS 配置让你头疼
4. 测试环境行为与生产构建有差异（模块解析不一致等）
5. 项目使用 TypeScript，需要 ts-jest 转译
6. 你希望减少测试相关依赖包数量

实证数据（来自 Cabify 等公司的迁移实践）：

- CI 测试时间减少 24-50%
- 测试相关 npm 依赖从 8-10 个减少到 1-2 个
- 配置文件从 50+ 行减少到约 18 行
- 开发服务器热重载几乎即时

---

## 11.2 API 对照表

Vitest 的 API 设计**刻意与 Jest 高度兼容**，大部分情况下只需要替换导入源：

| Jest | Vitest | 说明 |
|---|---|---|
| `jest.fn()` | `vi.fn()` | 创建 mock 函数 |
| `jest.spyOn()` | `vi.spyOn()` | 监听对象方法 |
| `jest.mock()` | `vi.mock()` | Mock 模块 |
| `jest.unmock()` | `vi.unmock()` | 取消 mock |
| `jest.requireActual()` | `vi.importActual()` | 导入真实模块 |
| `jest.useFakeTimers()` | `vi.useFakeTimers()` | 虚拟计时器 |
| `jest.useRealTimers()` | `vi.useRealTimers()` | 真实计时器 |
| `jest.advanceTimersByTime()` | `vi.advanceTimersByTime()` | 快进时间 |
| `jest.runAllTimers()` | `vi.runAllTimers()` | 运行所有定时器 |
| `jest.clearAllMocks()` | `vi.clearAllMocks()` | 清除 mock 记录 |
| `jest.resetAllMocks()` | `vi.resetAllMocks()` | 重置 mock 记录+实现 |
| `jest.restoreAllMocks()` | `vi.restoreAllMocks()` | 恢复原始实现 |
| `jest.setSystemTime()` | `vi.setSystemTime()` | 设置系统时间 |

`describe`、`it`、`test`、`expect` 完全兼容，无需更改。

### 不兼容的 API

| Jest | Vitest 替代方案 |
|---|---|
| `jest.retryTimes()` | `it.retry()` 或在 vitest.config 中配置 `retry` |
| `jest.isolateModules()` | `vi.isolateModules()` |
| `jest.genMockFromModule()` | `vi.importActual()` + 手动构造 |
| `jest.setTimeout()` (全局) | vitest.config 中配置 `testTimeout` |

---

## 11.3 配置文件迁移

### Jest 配置 → Vitest 配置

```javascript
// Jest: jest.config.js (~50 行)
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  moduleNameMapper: {
    '\\.(css|less)$': 'identity-obj-proxy',
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterFramework: ['./jest.setup.ts'],
  collectCoverageFrom: ['src/**/*.{ts,tsx}'],
  coverageThreshold: {
    global: { lines: 70 },
  },
  testMatch: ['**/__tests__/**/*.test.{ts,tsx}'],
}
```

```typescript
// Vitest: vitest.config.ts (~18 行)
import { defineConfig } from 'vitest/config'
import path from 'node:path'

export default defineConfig({
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      thresholds: { lines: 70 },
    },
  },
})
```

关键变化：
- 不需要 `transform`（Vite 原生处理 TS）
- 不需要 `moduleNameMapper`（用 `resolve.alias` 替代）
- `setupFilesAfterFramework` → `setupFiles`
- `testMatch` → `include`
- 删除了 ts-jest, babel-jest, identity-obj-proxy 等额外依赖

---

## 11.4 全局替换

最简单的迁移方式：使用正则全局替换。

```bash
# 将所有 jest.fn() 替换为 vi.fn()
find src -name "*.test.*" -exec sed -i 's/jest\.fn()/vi.fn()/g' {} +

# 将所有 jest.mock 替换为 vi.mock
find src -name "*.test.*" -exec sed -i 's/jest\.mock/vi.mock/g' {} +

# 将所有 jest.spyOn 替换为 vi.spyOn
find src -name "*.test.*" -exec sed -i 's/jest\.spyOn/vi.spyOn/g' {} +
```

### 需要手动修改的情况

1. **__mocks__ 目录**：Vitest 的 `vi.mock` 提升行为与 Jest 略有不同。如果 `__mocks__/` 下的 mock 文件内部使用了 `vi` API，可能需要调整。

2. **timer mock 高级用法**：Jest 的 `jest.advanceTimersByTime` 和 Vitest 的 `vi.advanceTimersByTime` 在 fake timer 的实现上有些微差异。如果你使用了 `jest.runOnlyPendingTimers` 等 Jest 特有 API，需要找到 Vitest 的等价方法。

3. **ESM/CJS 混用**：Jest 对 CJS 更宽容。Vitest 原生 ESM，如果你的某些 mock 依赖了 CJS 的模块级变量（如 `__dirname`），可能需要调整。

---

## 11.5 分步迁移策略

### 推荐：两阶段法

**第一阶段：构建工具迁移（如果尚未使用 Vite）**

1. 从 Webpack/CRA 迁移到 Vite
2. 验证开发服务器、构建产物正常
3. 此阶段 Jest 测试可继续运行（通过 `@vitejs/plugin-react` + Jest adapter 或保持 Webpack 用于测试）

**第二阶段：测试框架迁移**

1. 安装 Vitest：`npm i -D vitest @vitest/coverage-v8`
2. 创建 `vitest.config.ts`
3. 运行 `npx vitest run` 查看失败数
4. 按文件逐个迁移：
   - 替换 `jest.fn()` → `vi.fn()` 等 API
   - 运行该文件的测试，确认 100% 通过
5. 迁移完成后，删除 Jest 相关依赖

### 并行过渡期

在迁移过程中，可以**同时运行 Jest 和 Vitest**：

```json
{
  "scripts": {
    "test:jest": "jest",
    "test:vitest": "vitest run",
    "test": "vitest run" // 迁移完成后切换默认
  }
}
```

### 迁移检查清单

```
□ 安装 vitest、@vitest/coverage-v8、@vitest/ui
□ 创建 vitest.config.ts
□ 将 jest.setup.ts 内容迁移到 vitest.setup.ts
□ @testing-library/jest-dom → @testing-library/jest-dom/vitest
□ jest.fn → vi.fn / jest.spyOn → vi.spyOn / jest.mock → vi.mock
□ 删除 ts-jest、babel-jest、@types/jest 等依赖
□ 在 CI 中替换 jest → vitest run
□ 所有测试通过后删除 jest.config.js
```

---

## 练习与思考

1. 评估一个你正在使用的 Jest 项目，按照 11.1 节的条件打分。迁移的 ROI 如何？
2. 为一个 10 个测试文件的项目执行完整迁移，记录每个步骤的时间和遇到的问题
3. 如果一个项目的测试重度依赖 `__mocks__/` 目录和 Jest 的自动 mock 功能，迁移时需要注意什么？

---

## 本章总结

- Vitest 的 API 与 Jest 高度兼容，90% 的替换是机械的
- 配置文件从 50+ 行简化到 18 行，依赖从 8-10 个减少到 1-2 个
- 迁移策略：构建工具迁移先 → 测试框架迁移后；可并行运行过渡期
- `jest.fn → vi.fn` 是最主要的 API 替换
- 使用 codemod 或 find+sed 加速批量替换
