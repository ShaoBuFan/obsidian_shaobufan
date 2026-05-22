---
tags:
  - analysis
  - reference-project
created: 2026-05-22
---

# MSW 官方示例 (mswjs/examples) 分析

## 项目概览
- 仓库：mswjs/examples
- 定位：MSW 官方示例集合，涵盖多种环境集成
- 关注重点：with-vitest 和 with-vitest-cjs 示例

## vitest.config 关键设置

```ts
// examples/with-vitest/vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
    root: __dirname,
    setupFiles: ['./vitest.setup.ts'],
  },
})
```

特点：
- 极其精简，展示最小可用配置
- 未指定 environment（默认 node），但通过文件内注释切换到 jsdom
- 使用 `__dirname` 作为 root

## 目录结构

```
examples/with-vitest/
  vitest.config.ts
  vitest.setup.ts
  mocks/
    node.ts          # setupServer(...handlers)
    handlers.ts      # HTTP + GraphQL 示例 handler
  example.test.ts        # node 环境测试
  example-jsdom.test.ts  # jsdom 环境测试
  package.json
  tsconfig.json
```

## MSW 初始化模式

在 `vitest.setup.ts` 中：
```ts
import { server } from './mocks/node.js'
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

注意：
- 使用 `.js` 扩展名导入（ESM 规范）
- 未设置 `onUnhandledRequest: 'error'`（简化示例，生产项目应加上）
- server 从独立的 mocks/node.ts 导入

## handler 组织

```ts
// handlers.ts
import { http, graphql, HttpResponse } from 'msw'
export const handlers = [
  http.get('https://api.example.com/user', () => {...}),
  graphql.query('ListMovies', () => {...}),
]
```

特点：
- 单一文件包含所有 handler（小型项目适用）
- 同时展示 HTTP 和 GraphQL handler
- 无运行时覆盖示例

## 环境切换

通过 JSDoc 注释切换测试环境：
- `/** @vitest-environment node */` → 默认
- `/** @vitest-environment jsdom */` → 需要 DOM API 的测试

这是一种轻量级的环境切换方式，适合小型项目。大型项目建议在 vitest.config 中统一指定。

## 可改进点

1. 缺少 `onUnhandledRequest: 'error'` 设置
2. 未展示 handler 按域分组的最佳实践
3. 未展示运行时覆盖（server.use()）
4. 缺少 React 组件测试的集成示范
5. 未使用 @mswjs/data 或类似内存数据库
6. 无自定义 render 封装示例
