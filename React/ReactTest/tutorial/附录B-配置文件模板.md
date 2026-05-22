---
tags:
  - tutorial
  - appendix
  - config
created: 2026-05-22
---

# 附录 B：配置文件模板

## B.1 最小化测试环境（新项目快速启动）

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => { server.resetHandlers(); cleanup() })
afterAll(() => server.close())
```

```typescript
// src/test/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'
export const server = setupServer(...handlers)
```

## B.2 企业级完整配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  test: {
    // 全局设置
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],

    // 测试文件匹配
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', '.git'],

    // CSS/资源处理
    css: true,

    // 超时与重试
    testTimeout: 10000,
    hookTimeout: 10000,
    retry: process.env.CI ? 2 : 0,     // CI 中自动重试 flaky test

    // 并发控制
    pool: 'threads',                     // threads | forks
    fileParallelism: true,

    // 覆盖率
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/*.d.ts',
        'src/types/',
        'src/**/index.ts',
      ],
      thresholds: {
        lines: 75,
        functions: 75,
        branches: 70,
        statements: 75,
      },
      watermarks: {
        statements: [70, 90],    // <70 红, 70-90 黄, >90 绿
        lines: [70, 90],
      },
    },
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

## B.3 Monorepo 配置

```typescript
// vitest.workspace.ts（顶层）
import { defineWorkspace } from 'vitest/config'

export default defineWorkspace([
  'packages/*',
  'apps/*',
])

// 各子包可覆盖公共配置
// packages/ui/vitest.config.ts
import { defineConfig } from 'vitest/config'
import baseConfig from '../../vitest.config'

export default defineConfig({
  ...baseConfig,
  test: {
    ...baseConfig.test,
    environment: 'jsdom',
  },
})
```

### Turborepo 集成

```json
// turbo.json
{
  "tasks": {
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"],
      "cache": true
    }
  }
}
```

## B.4 package.json scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui",
    "test:bench": "vitest bench",
    "test:typecheck": "tsc --noEmit"
  },
  "msw": {
    "workerDirectory": ["public"]
  }
}
```
