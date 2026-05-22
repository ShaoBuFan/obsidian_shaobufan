---
tags:
  - analysis
  - reference-project
created: 2026-05-22
---

# RTL + Vitest + MSW 教程系列分析

## 项目概览
- 仓库：arnobt78/React-Testing-Library-RTL-Vitest-TDD-MSW-API-Test-Automation-Tutorials
- 定位：5 个递进式教学项目，从入门到 GraphQL 集成测试
- 5 个项目：
  1. Vitest Boilerplate（基础配置 + 单元测试）
  2. RTL Fundamentals（组件测试基础）
  3. TDD Tutorial（测试驱动开发流程）
  4. MSW Tutorial（MSW + 组件集成测试）
  5. GitHub Users Search（Apollo GraphQL + MSW + 完整项目）

## vitest.config 关键设置

所有子项目的配置模式一致：
```ts
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/vitest.setup.ts',
  },
})
```

特点：
- 统一在 vite.config.ts 中配置（Vite + Vitest 合一）
- 所有项目使用 jsdom + globals
- setup 文件路径各项目一致

## 目录结构（以 MSW Tutorial 为例）

```
src/
  vitest.setup.ts          # MSW 生命周期 + @testing-library/jest-dom 匹配器
  mocks/
    server.ts              # setupServer(...handlers)
    handlers.ts            # 所有 handler
    browser.ts             # setupWorker(...handlers)
  __tests__/
    Item.test.tsx
    List.test.tsx
    Form.test.tsx
  App.tsx
  App.test.tsx
```

## MSW 初始化模式

```ts
// vitest.setup.ts
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import server from './mocks/server';

expect.extend(matchers);

afterEach(() => cleanup());
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

特点：
- `expect.extend(matchers)` 扩展匹配器（toBeInTheDocument 等）
- `cleanup()` 确保每个测试后卸载组件
- 两个 afterEach：一个清理 DOM，一个重置 handler

## handler 模式

```ts
// 04-MSW 项目：REST API
export const handlers = [
  http.get('/api/items', () => HttpResponse.json(mockItems)),
  http.post('/api/items', async ({ request }) => {...}),
  http.delete('/api/items/:id', ({ params }) => {...}),
]

// 05-GitHub 项目：GraphQL API
export const handlers = [
  graphql.query('GetUser', ({ variables }) => {
    // 根据 variables 返回不同响应（错误、空数据、正常数据）
  }),
]
```

特点：
- GraphQL 项目中通过 variables 值来分支返回（login === 'request-error' 等）
- 这是一种替代 server.use() 的运行时分支方式
- 单一 handlers 文件，适合中小型项目

## 值得借鉴的模式

1. **渐进式教学架构**：5 个项目从简到繁，每个独立可运行
2. **GraphQL handler 中的条件分支**：通过 variables 值控制返回
3. **fixture 数据与 handler 分离**：mockItems/mockRepositories 从独立文件导入
4. **co-located 测试**：每个组件旁边有对应的测试文件

## 可改进点

1. handler 未按域拆分（所有 handler 在一个文件）
2. 未使用 @mswjs/data 做内存数据库（返回静态 mock 数据）
3. 缺少自定义 render wrapper（每个测试自行处理 Provider）
4. 未展示 server.use() 运行时覆盖模式（依赖 handler 内条件分支）
5. GraphQL 项目中未处理 loading/error 状态的测试覆盖
