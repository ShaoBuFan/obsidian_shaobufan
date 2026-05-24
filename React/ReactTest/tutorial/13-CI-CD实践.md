---
tags:
  - 测试/CI
  - 工具/Vitest
created: 2026-05-22
---

# 第13章：CI/CD 实践

## 学习目标

- 理解测试在 CI 流程中的角色——PR 门禁和分支保护
- 掌握 GitHub Actions 测试工作流的完整配置
- 学会配置 Vitest 覆盖率（provider、报告格式、阈值）
- 了解 Codecov/Coveralls 集成方式
- 能识别和优化慢测试（pool、sharding、隔离策略）

---

## 13.1 测试在 CI 中的角色

### PR 门禁：测试即关卡

在团队协作中，测试不是"可选质量改进"——它是合并代码的硬性关卡：

```
开发者提 PR
  └→ CI 自动运行
       ├─ 类型检查 (tsc --noEmit)
       ├─ Lint 检查 (ESLint)
       ├─ 单元测试 (vitest run)
       └─ 集成测试 (vitest run)
            │
            ├─ 全部通过 → 可以合并
            └─ 任何失败 → 阻止合并
```

### 分支保护规则

在 GitHub 仓库 Settings → Branches → Add rule 中配置：

```yaml
# 分支保护的核心规则
- Require a pull request before merging
  - Require approvals: 1
- Require status checks to pass before merging
  - Required checks:
    - "test (18)"       # Node 18 下的测试
    - "test (20)"       # Node 20 下的测试
    - "lint"            # Lint 检查
- Require branches to be up to date
```

### CI 时间的硬约束

```
CI 总时间 = 单次测试时间 × 修改次数 × 开发者数量

假设：
  单次 CI 运行：5 分钟
  每天合并 PR：10 个
  等待开发者：5 人

每天浪费的等待时间：5 × 10 = 50 人·分钟
每月浪费：约 17 小时
```

CI 测试速度是一个团队效率问题，不是个人偏好。**10 分钟是 CI 运行时间的上限**——超过这个阈值，开发者会开始切上下文，导致注意力碎片化。

---

## 13.2 GitHub Actions 配置

### 基础 Workflow：checkout → install → test

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm run test:run

      - name: Run type check
        run: npx tsc --noEmit
```

### 缓存策略

正确配置缓存可以将 CI 安装时间从 2-3 分钟降低到 10-20 秒：

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'           # 自动缓存 ~/.npm

      - name: Install dependencies
        run: npm ci

      - name: Cache Vitest
        uses: actions/cache@v4
        with:
          path: |
            node_modules/.cache/vitest
            .vitest-cache
          key: vitest-cache-${{ runner.os }}-${{ hashFiles('vitest.config.ts') }}
          restore-keys: |
            vitest-cache-${{ runner.os }}-
```

> **自我验证说明**：`actions/cache@v4` 的 `key` 决定了缓存的唯一性。`hashFiles('vitest.config.ts')` 确保配置变化时缓存自动失效。`restore-keys` 提供回退匹配：如果精确 key 未命中，使用最近匹配的缓存。Node 缓存通过 `setup-node` 的 `cache: 'npm'` 自动处理 npm 缓存目录。

### Matrix 测试

Matrix 策略让你在多个 Node 版本和操作系统上并行运行测试：

```yaml
jobs:
  test:
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest]
        include:
          - node-version: 20
            os: windows-latest   # 只在 Node 20 上跑 Windows

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci
      - run: npm run test:run
      - run: npx vitest run --coverage
        if: matrix.node-version == 20  # 只在 Node 20 上收集覆盖率
```

### 并行执行与分片

Vitest 内置分片功能，可以将测试文件分配到多个 CI job 并行执行：

```yaml
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]    # 分成 4 个分片

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci
      - run: npx vitest run --shard=${{ matrix.shard }}/4
```

分片 vs 不分的性能对比（假设 100 个测试文件，每个平均 3 秒）：

```
无分片：100 × 3s  = 300s (5 分钟)   ← 在 1 个 runner 上串行
4 分片：25 × 3s   = 75s  (1.25 分钟) ← 在 4 个 runner 上并行
```

> **自我验证说明**：`vitest --shard` 从 v1.0 开始支持，签名 `--shard=<index>/<total>`。分片逻辑基于测试文件的哈希值分配，而非文件名排序或随机分配——这确保同一分片在不同运行中保持一致的分组。分片粒度是文件级，不是测试用例级。GitHub Actions 免费计划支持最多 20 个并行 job（2026-05 当前限制）。

### 完整 Workflow 示例

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx eslint src/

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx tsc --noEmit

  test:
    needs: [lint, type-check]
    strategy:
      matrix:
        shard: [1, 2]
        node-version: [18, 20]

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci

      - name: Cache Vitest
        uses: actions/cache@v4
        with:
          path: node_modules/.cache/vitest
          key: vitest-${{ runner.os }}-${{ matrix.node-version }}-${{ hashFiles('vitest.config.ts') }}

      - run: npx vitest run --shard=${{ matrix.shard }}/2 --coverage
        env:
          CI: true

      - name: Upload coverage
        if: matrix.node-version == 20 && matrix.shard == 1
        uses: codecov/codecov-action@v4
        with:
          directory: ./coverage
```

---

## 13.3 覆盖率策略

### Provider 选择：v8 vs istanbul

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',             // 推荐：更快、内置 V8 引擎
      // provider: 'istanbul',    // 备选：更慢但更精确的行映射
    },
  },
})
```

| 维度 | v8 | istanbul |
|------|----|----------|
| **速度** | 快（原生 V8 采样） | 慢（源码插桩） |
| **安装** | `@vitest/coverage-v8` | `@vitest/coverage-istanbul` |
| **精度** | 函数级/行级 | 分支级/语句级（更细） |
| **Source Map** | 依赖 V8 内置 | 依赖 Babel/TS 的 source map |
| **推荐场景** | 绝大多数项目 | 需要精确分支覆盖率的合规场景 |

**本教程推荐 v8**。对于前端项目，v8 提供的信息量已经足够，速度优势显著。

### 报告格式

```typescript
coverage: {
  provider: 'v8',
  reporter: [
    'text',       // CI 控制台输出（开发者直接查看）
    'html',       // 本地浏览器查看（`npx vitest --coverage` 后打开 coverage/index.html）
    'lcov',       // 上报 Codecov/Coveralls 使用的格式
    'clover',     // CI 工具（如 Jenkins）集成
    'json-summary', // 机器可读的摘要数据（可用于自定义脚本）
  ],
  reportsDirectory: './coverage',
}
```

### 覆盖率阈值

```typescript
coverage: {
  provider: 'v8',
  thresholds: {
    lines: 80,            // 行覆盖率 ≥ 80%
    functions: 80,        // 函数覆盖率 ≥ 80%
    branches: 75,         // 分支覆盖率 ≥ 75%（分支通常比行更难覆盖）
    statements: 80,       // 语句覆盖率 ≥ 80%

    perFile: true,        // 每个文件单独检查阈值
    // 如果 perFile: false，只检查全局平均
  },
}
```

### 阈值设多少才合理

```
项目类型          lines    branches   推荐策略
─────────────────────────────────────────────
新项目（刚起步）    90-95    85-90       高门槛保质量
成熟项目（未测过）  60-70    50-60       先设低门槛，逐步提高
工具库/组件库      95-100   90-100      接近全量覆盖
SSR/API 项目       80-85    75-80       分支覆盖率可以略低
```

**警告**：覆盖率门槛不是目的，是安全网。设太高（`lines: 100`）会导致团队为了凑覆盖率写无意义的测试。设太低（`lines: 30`）则安全网毫无意义。80/75（lines/branches）是大多数项目的平衡点。

### 覆盖率文件排除

```typescript
coverage: {
  include: ['src/**/*.{ts,tsx}'],          // 只统计 src/ 下的文件
  exclude: [
    'src/**/*.test.*',                      // 排除测试文件本身
    'src/**/*.spec.*',
    'src/test/**',                           // 排除测试工具文件
    'src/**/index.ts',                      // 排除 barrel export
    'src/**/*.d.ts',                        // 排除类型声明
    'src/vite-env.d.ts',                    // 排除 Vite 类型
    'src/**/*.stories.*',                   // 排除 Storybook stories
    'src/**/*.mock.*',                      // 排除 mock 数据文件
  ],
}
```

> **自我验证说明**：覆盖率阈值的类型签名：
> ```typescript
> interface Thresholds {
>   perFile?: boolean          // default: false
>   autoUpdate?: boolean       // default: false（自动更新阈值为当前值）
>   100?: boolean              // 是否要求 100%（快捷方式）
>   statements?: number        // 语句覆盖率下限（0-100）
>   branches?: number          // 分支覆盖率下限
>   functions?: number         // 函数覆盖率下限
>   lines?: number             // 行覆盖率下限
> }
> ```
> 当覆盖率低于阈值时，`vitest run --coverage` 会以非零退出码退出，CI 流程将其标记为失败。

> **Jest 对比：覆盖率配置**
>
> Jest 的覆盖率配置方式与 Vitest 类似，但字段名和 provider 不同：
>
> ```typescript
> // Jest — jest.config.js
> module.exports = {
>   collectCoverage: true,
>   collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/**/*.test.*'],
>   coverageThreshold: {
>     global: { lines: 80, branches: 75, functions: 80, statements: 80 },
>   },
>   coverageReporters: ['text', 'html', 'lcov'],
> }
>
> // Vitest — vitest.config.ts
> export default defineConfig({
>   test: {
>     coverage: {
>       provider: 'v8',
>       thresholds: { lines: 80, branches: 75, functions: 80, statements: 80 },
>       reporter: ['text', 'html', 'lcov'],
>     },
>   },
> })
> ```
>
> 关键差异：
> | 维度 | Jest | Vitest |
> |------|------|--------|
> | 配置字段 | `coverageThreshold`（嵌套在 global 下） | `thresholds`（直接配置） |
> | 文件过滤 | `collectCoverageFrom`（glob 模式） | `include`/`exclude`（独立字段） |
> | Provider | 仅 istanbul（通过 babel-jest 插桩） | v8（默认）或 istanbul（可选） |
> | 速度 | 较慢（babel 源码插桩） | 较快（V8 原生覆盖率采样） |
>
> 从 Jest 迁移到 Vitest 时，覆盖率配置是最简单的部分——字段名不同，但概念一一对应。

> **为什么：覆盖率阈值应该是底线而非目标**
>
> 覆盖率阈值是一个容易产生误解的指标。常见的两个极端：
>
> 极端 A：设 100%，然后团队开始写"为覆盖率而测"的测试——验证 getter 返回了值、验证组件渲染了 div、验证常量文件被导出了。这些测试对代码正确性的贡献为零，但增加了维护负担。
>
> 极端 B：不设阈值，然后代码覆盖率自由落体到 20%，没人知道哪些代码没有测试覆盖。
>
> 正确的理解：**80% 阈值不是"测到 80% 就够了"，而是"覆盖率低于 80% 意味着你的测试策略有盲区"。** 它是一个安全网，不是工作量指标。
>
> 覆盖率的真正价值不在数字本身，而在趋势：
> - PR 导致覆盖率下降 → 新增代码没测试 → 需要补测
> - 覆盖率长期稳定但 bug 频发 → 测试方向不对 → 需要反思测试策略
> - 覆盖率上升但维护成本也在上升 → 可能过度测试了低价值代码
>
> 实际建议：设 80/75（lines/branches）作为安全网，用 Codecov 的 patch 覆盖率监控 PR 级别的"新增代码是否被测"，用人工 Code Review 判断测试质量。**数字是信号，不是命令。**

---

## 13.4 覆盖率上报

### Codecov 集成

```yaml
# .github/workflows/test.yml 中的 coverage job
- name: Run tests with coverage
  run: npx vitest run --coverage

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    directory: ./coverage          # 覆盖率报告目录
    flags: unittests               # 标记区分不同测试类型
    name: codecov-umbrella          # 报告名称
    fail_ci_if_error: true         # 上传失败则 CI 失败
    verbose: true                  # 调试时开启
```

### Coveralls 集成

```yaml
- name: Run tests with coverage
  run: npx vitest run --coverage

- name: Coveralls
  uses: coverallsapp/github-action@v2
  with:
    file: ./coverage/lcov.info     # lcov 格式报告路径
```

### PR 覆盖率评论

配置 Codecov 后，PR 页面会自动出现覆盖率变更评论：

```
# Codecov Report
Merging #42 (abc123) into main (def456)

|           | Before | After | ±   |
|-----------|--------|-------|-----|
| Lines     | 82.3%  | 83.1% | +0.8% ✅ |
| Branches  | 75.1%  | 74.5% | -0.6% ❌ |
| Functions | 80.0%  | 81.2% | +1.2% ✅ |

🔥 New changes don't meet coverage threshold (80%):
  - src/components/UserProfile.tsx (72.3%)
```

### 覆盖率衰减检测

Codecov 可以配置当 PR 导致覆盖率下降时阻止合并：

```yaml
# codecov.yml — 放在项目根目录
coverage:
  status:
    project:
      default:
        target: 80%          # 项目总覆盖率不低于 80%
        threshold: 1%        # 允许 1% 的波动

    patch:
      default:
        target: 80%          # PR 中修改的代码覆盖率不低于 80%
        threshold: 0%        # 修改的代码不允许降覆盖率
```

---

## 13.5 测试性能优化

### 识别慢测试

```bash
# 方式 1：Verbose Reporter 显示每个测试耗时
npx vitest run --reporter=verbose

# 输出示例
# ✓ src/components/UserProfile.test.tsx (12ms)
# ✓ src/utils/format.test.ts (3ms)
# ✓ src/hooks/useUser.test.ts (8432ms) ← 慢测试！
# ✓ src/pages/Dashboard.test.tsx (234ms)

# 方式 2：Vitest 内置 Slow Test Threshold
# vitest.config.ts
test: {
  slowTestThreshold: 1000,  // 超过 1000ms 的测试会在报告中高亮
}
```

### Pool：threads vs forks

Vitest v2+ 默认使用 `pool: 'forks'`。这个设置在测试性能和隔离性之间做了权衡：

```typescript
// vitest.config.ts
test: {
  pool: 'threads',       // 使用 worker_threads（更轻量，更快）
  // pool: 'forks',     // 使用 child_process（更重，隔离性更好，默认）
}
```

| Pool | 机制 | 速度 | 隔离性 | 适用场景 |
|------|------|------|--------|---------|
| `threads` | worker_threads | 快（共享进程内存） | 中（模块状态可能泄漏） | 纯逻辑测试、无副作用的单元测试 |
| `forks` | child_process | 较慢（独立进程） | 高（完全隔离） | 组件测试、需要 DOM 的集成测试 |

**实际建议**：大多数项目不需要改这个设置。只有碰到测试间状态污染时才考虑从 `threads` 切到 `forks`（或反之用于加速）。

### fileParallelism

```typescript
test: {
  pool: 'threads',
  fileParallelism: true,    // 默认：跨文件并行执行
  maxWorkers: 4,            // 最大并行 worker 数（默认：CPU 核心数）
  minWorkers: 1,            // 最小并行 worker 数
}
```

CI 环境下，`maxWorkers` 应该匹配可用 CPU 核心数：

```yaml
# .github/workflows/test.yml
- run: npx vitest run --maxWorkers=2
```

### isolation

```typescript
test: {
  pool: 'threads',
  isolate: true,   // 默认：每个测试文件独立环境
  // isolate: false,  // 关闭隔离（更快，但可能状态污染）
}
```

关闭隔离（`isolate: false`）对测试速度的提升非常显著——在某些项目中可以达到 2-3 倍加速。但代价是测试之间可能共享模块级状态：

```typescript
// ❌ 关闭隔离后，模块级状态的副作用会泄漏
// counter-store.ts
let count = 0
export function getCount() { return count }
export function increment() { count++ }

// test-a.test.ts
import { increment } from './counter-store'
increment()  // count = 1

// test-b.test.ts（关闭隔离后）
import { getCount } from './counter-store'
getCount()   // 1（不是 0！因为 test-a 的副作用还在）
```

**实际建议**：`isolate: false` 只推荐在 CI 环境中谨慎使用，且仅在测试之间确实没有模块级状态共享时。对于使用 Zustand、Context 等状态管理的项目，不建议关闭隔离。

### 避免不必要的 beforeEach 重渲染

```typescript
// ❌ 每个测试都重新渲染，即使它们测试的是同一次渲染
describe('UserProfile', () => {
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    user = userEvent.setup()
    renderWithProviders(<UserProfile userId={1} />)
  })

  it('shows user name', () => {
    expect(screen.getByText('Alice')).toBeInTheDocument()  // 又渲染了一次
  })
})

// ✅ 在需要的地方显式渲染
describe('UserProfile', () => {
  it('shows user name', async () => {
    renderWithProviders(<UserProfile userId={1} />)
    expect(await screen.findByText('Alice')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    renderWithProviders(<SlowUserProfile userId={1} />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })
})
```

### Vitest 性能配置速查

```typescript
// vitest.config.ts — 性能优化配置汇总
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // === 并行策略 ===
    pool: 'threads',                 // 更快的工作池模式
    fileParallelism: true,           // 跨文件并行
    maxWorkers: 4,                   // 限制并行 worker（CI 中重要）
    maxConcurrency: 10,              // 每个文件的并发测试数

    // === 隔离策略 ===
    isolate: true,                   // 文件级隔离（安全）
    // isolate: false,               // 关闭隔离（更快，需确保状态独立）

    // === 超时 ===
    testTimeout: 10000,              // 单测试超时（默认 5000）
    hookTimeout: 15000,              // hook 超时（默认 10000）

    // === 报告 ===
    slowTestThreshold: 1000,         // 慢测试标记阈值

    // === 重试 ===
    retry: 0,                        // 失败重试次数（CI 中建议 2）

    // === 覆盖率 ===
    coverage: {
      provider: 'v8',
      enabled: false,                // 默认不收集，CI 中通过 --coverage 开启
    },
  },
})
```

> **自我验证说明**：以上配置项可以在 `vitest.config.ts` 中设置，也可以通过 CLI 参数覆盖（如 `npx vitest run --pool=forks`）。CI 环境中建议在配置文件中设置合理的默认值，CI workflow 中通过 CLI 参数覆盖（如 `--shard`、`--maxWorkers`）。Pool 切换需要重启 Vitest，不支持 watch 模式下的热替换。

> **渐进式示例：CI 工作流的三步优化**
>
> 一个项目的 CI 测试流程通常会经历三个阶段：
>
> **阶段 1：基础流程（跑通即可）**
> ```yaml
> - run: npm ci
> - run: npm run test:run
> ```
> 优点：简单直接；痛点：每次 CI 重新下载依赖需 2-3 分钟，测试串行执行需 5-10 分钟。
>
> **阶段 2：缓存优化（降低安装时间）**
> ```yaml
> - uses: actions/setup-node@v4
>   with:
>     node-version: 20
>     cache: 'npm'           # 缓存 node_modules
> - run: npm ci              # 有缓存时 10-30 秒
> - run: npx vitest run      # 仍然串行
> ```
> 优点：安装时间从分钟级降到秒级；痛点：测试集增大后串行执行时间线性增长。
>
> **阶段 3：并行执行（降低测试时间）**
> ```yaml
> strategy:
>   matrix:
>     shard: [1, 2, 3, 4]    # 分 4 片并行
> - run: npx vitest run --shard=${{ matrix.shard }}/4
> ```
> 优点：总 CI 时间 = 最慢分片时间，理论提速 N 倍（N = 分片数）；痛点：需要确保测试文件间无状态依赖，否则分片产生的不确定顺序可能暴露隐式依赖。
>
> 每个阶段解决上一个阶段的瓶颈：安装慢 → 缓存，测试慢 → 分片。不要在一开始就追求最优配置——先跑通，再优化。

---

## 13.6 反模式

### 反模式 1：CI 覆盖率门槛 + 本地不检查

```yaml
# ❌ 只有 CI 检查覆盖率，开发者本地发现不了问题
# CI 上跑 5 分钟后被告知覆盖率不足 → 重新修改 → 再等 5 分钟

# ✅ 本地也配置 pre-commit check
# package.json
{
  "scripts": {
    "test:coverage": "vitest run --coverage --thresholds.lines=80"
  }
}
```

### 反模式 2：Matrix 用了太多不需要的组合

```yaml
# ❌ 测试 12 种组合（3 OS × 4 Node），其中大部分从来不发现问题
matrix:
  os: [ubuntu, windows, macos]
  node-version: [16, 18, 20, 22]

# ✅ 只在主要环境测全覆盖，其他环境测快检
matrix:
  os: [ubuntu]
  node-version: [18, 20]
  include:
    - os: windows
      node-version: 20
```

### 反模式 3：CI 和本地使用不同的 Vitest 配置

```typescript
// ❌ 两个配置文件，行为不一致
// vitest.config.ts（本地）
export default defineConfig({
  test: { pool: 'threads' }
})

// vitest.ci.config.ts（CI）
export default defineConfig({
  test: { pool: 'forks' }
})

// ✅ 统一配置文件，环境变量区分
export default defineConfig({
  test: {
    pool: process.env.CI ? 'forks' : 'threads',
    coverage: { enabled: !!process.env.CI },
  },
})
```

### 反模式 4：CI 中安装了所有依赖但不做缓存

```yaml
# ❌ 每次 CI 运行都重新下载所有依赖（5-15 分钟）
- run: npm install

# ✅ 使用 npm ci + 缓存（10-30 秒）
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'
- run: npm ci
```

### 反模式 5：测试文件之间的隐式执行顺序依赖

```typescript
// test-a.test.ts — 创建了一个全局状态
globalThis.__sharedState = 'initialized'

// test-b.test.ts — 依赖 test-a 创建的状态
it('uses shared state', () => {
  expect(globalThis.__sharedState).toBe('initialized') // 可能通过，也可能失败
})
```

在 `isolate: true` 时这个反模式不会触发，但关闭隔离后（`isolate: false`）这是最常见的错误源。

---

## 13.7 本章练习

1. **编写 GitHub Actions Workflow**
   为项目创建一个 `.github/workflows/test.yml`，包含：
   - checkout + setup-node + npm ci
   - 缓存 node_modules 和 Vitest 缓存
   - vitest run + tsc --noEmit 两步
   - 2 个分片

2. **配置覆盖率阈值**
   在 `vitest.config.ts` 中配置：
   - v8 provider
   - text + lcov 报告格式
   - lines: 80, branches: 75 的阈值
   - src/ 目录下的排除规则

3. **性能分析**
   在当前项目上运行 `npx vitest run --reporter=verbose`，识别出最慢的 3 个测试。分析它们为什么慢，写出优化方案。

4. **覆盖率报告上传**
   配置 Codecov 或 Coveralls 集成，确保 PR 页面显示覆盖率变更。

---

## 13.8 本章总结

- 测试在 CI 中是硬性门禁：类型检查 → Lint → 测试 → 覆盖率，层层递进
- GitHub Actions 基础三件套：checkout → setup-node → npm ci → vitest run
- 缓存策略可将 CI 安装时间从分钟级降到秒级
- Matrix 测试和分片是 CI 并行化的核心手段
- v8 provider 快于 istanbul，推荐作为默认选择
- 覆盖率阈值设 80/75（lines/branches），过低无意义、过高促生虚假测试
- 性能优化：pool 切换、isolate 权衡、避免重复渲染、限制并行 worker
- CI 配置和本地配置应保持统一，通过环境变量区分

## 关联阅读

- [第2章：测试环境搭建](02-测试环境搭建.md) — vitest.config.ts 配置基础
- [第12章：测试可维护性](12-测试可维护性.md) — 好的测试习惯降低 CI 噪音
