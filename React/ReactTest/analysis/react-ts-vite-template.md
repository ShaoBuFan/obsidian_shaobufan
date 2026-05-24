# 项目分析: react-ts-vite-template

> GitHub: [SalahAdDin/react-ts-vite-template](https://github.com/SalahAdDin/react-ts-vite-template)  
> 分析日期: 2026-05-22  
> 本地路径: `F:/NoteLab/React/ReactTest/reference-projects/react-ts-vite-template/`

---

## 1. 完整项目结构

```
react-ts-vite-template/
├── .editorconfig
├── .env                          # 环境变量配置
├── .gitignore
├── .husky/                       # Git hooks (lint-staged, commit-msg)
├── .lintstagedrc                 # lint-staged 配置
├── .nvmrc                        # Node 版本锁定
├── .prettierignore
├── .prettierrc
├── .releaserc                    # semantic-release 配置
├── .github/workflows/            # GitHub Actions (release)
├── CHANGELOG.md
├── LICENSE
├── README.md
├── commitlint.config.cts         # 提交消息规范
├── eslint.config.js              # ESLint flat config (v9)
├── index.html                    # 入口 HTML
├── package.json
├── playwright.config.ts          # E2E (Playwright) 配置
├── pnpm-lock.yaml
├── tsconfig.json                 # TS 根配置 (project references)
├── tsconfig.app.json             # 应用 TS 配置
├── tsconfig.node.json            # Node 端 TS 配置 (vite.config.ts)
├── vite.config.ts                # Vite + Vitest 合并配置
│
├── mocks/                        # MSW 模拟层
│   ├── browser.ts                # MSW browser worker
│   ├── handlers.ts               # 请求处理器
│   ├── server.ts                 # MSW node server (测试用)
│   ├── service.ts                # faker 数据工厂 (已注释)
│   ├── utils.ts                  # Fisher-Yates shuffle 工具
│   └── entities/
│       └── users.json            # 20 条 mock 用户数据
│
├── public/
│   └── assets/
│
├── src/                          # 应用源码 (Clean Architecture)
│   ├── environment.d.ts          # NodeJS.ProcessEnv 类型声明
│   ├── index.css                 # Tailwind CSS 入口
│   ├── main.tsx                  # 应用入口 (含 MSW 启动)
│   ├── reportWebVitals.ts        # Web Vitals 报告
│   ├── vite-env.d.ts             # Vite ImportMeta 类型声明
│   ├── vitest.setup.ts           # Vitest 全局 setup
│   │
│   ├── application/              # 业务逻辑层
│   │   ├── context.tsx           # React Context
│   │   ├── provider.tsx          # Context Provider
│   │   └── utils/
│   │       └── test-utils.tsx    # 自定义测试工具
│   │
│   ├── domain/                   # 领域模型层 (空目录)
│   │
│   ├── infrastructure/           # 基础设施层
│   │   └── api/
│   │       ├── client.ts         # Axios client
│   │       ├── endpoint.ts       # API 端点 (空对象)
│   │       └── service.ts        # API 服务 (仅 getSomething)
│   │
│   └── presentation/            # 表现层
│       ├── App.tsx               # 根组件 (Router Outlet 已注释)
│       ├── router.ts             # TanStack Router (已注释)
│       └── components/
│           ├── Layout.tsx         # 布局组件
│           ├── ErrorBox/
│           │   ├── ErrorBox.tsx       # 错误提示组件
│           │   └── ErrorBox.test.tsx  # 单元测试
│           └── Spinner/
│               ├── Spinner.tsx        # 加载动画组件
│               └── Spiner.test.tsx    # 单元测试 (文件名拼写错误)
│
└── tests/                        # E2E 测试
    └── App.e2e.test.ts           # Playwright E2E (标记为 fail)
```

---

## 2. 包依赖及版本

### 生产依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `react` | 18.3.1 | UI 框架 |
| `react-dom` | 18.3.1 | DOM 渲染 |
| `@tanstack/react-query` | 5.66.0 | 服务端状态管理 (缓存/去重/失效) |
| `@tanstack/react-router` | 1.102.5 | 路由 (当前已注释禁用) |
| `axios` | 1.7.9 | HTTP 客户端 |
| `react-hook-form` | 7.54.2 | 表单管理 |
| `@hookform/resolvers` | 4.0.0 | 表单校验解析器 |
| `valibot` | 1.0.0-rc.0 | Schema 校验 |
| `million` | 3.1.11 | React 编译优化 |
| `dotenv` | 16.4.7 | 环境变量加载 |

### 测试相关开发依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `vitest` | 3.0.5 | 测试运行器 |
| `@vitest/coverage-v8` | 3.0.5 | V8 覆盖率 |
| `@vitest/ui` | 3.0.5 | Vitest UI 模式 |
| `@testing-library/react` | 16.2.0 | React 组件测试 |
| `@testing-library/dom` | 10.4.0 | DOM 查询方法 |
| `@testing-library/user-event` | 14.6.1 | 用户事件模拟 |
| `happy-dom` | 17.1.0 | DOM 环境 (比 jsdom 更快) |
| `msw` | 2.7.0 | 网络层 Mock |
| `vitest-dom` | 0.1.1 | Vitest DOM 匹配器扩展 |
| `vitest-preview` | 0.0.1 | 测试视觉预览 |
| `@faker-js/faker` | 9.5.0 | 假数据生成 |
| `@playwright/test` | 1.50.1 | E2E 测试 |

### ESLint 测试插件

| 包名 | 版本 | 用途 |
|------|------|------|
| `eslint-plugin-testing-library` | 7.1.1 | Testing Library 规则 |
| `eslint-plugin-jest-dom` | 5.5.0 | jest-dom 匹配器规则 |
| `eslint-plugin-playwright` | 2.2.0 | Playwright 规则 |
| `@vitest/eslint-plugin` | 1.1.30 | Vitest 规则 |
| `eslint-plugin-sonarjs` | 3.0.1 | 代码质量规则 |

---

## 3. Vitest 配置 (vite.config.ts 内联)

配置嵌在 `vite.config.ts` 的 `test` 字段中，未使用独立的 `vitest.config.ts`：

```typescript
// vite.config.ts (关键片段)
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  return {
    // ... Vite 配置 (plugins, resolve alias, build, server)
    test: {
      globals: true,            // 全局 API (describe/it/expect 无需 import)
      clearMocks: true,         // 每个测试后自动清除 mock
      css: true,                // 解析 CSS 导入
      include: ["src/**/*.{test,spec}.?(c|m)[jt]s?(x)"],  // 测试文件范围
      exclude: ["tests"],       // 排除 E2E 测试目录
      watch: false,             // 默认不 watch
      coverage: {
        provider: "v8",         // V8 覆盖率引擎
        reporter: ["text", "html"],
        exclude: [
          ...coverageConfigDefaults.exclude,
          "src/application/utils/test-utils.tsx",  // 排除测试工具本身
        ],
        thresholds: {           // 覆盖率阈值
          branches: 90,
          functions: 95,
          lines: 80,
          statements: 80,
        },
      },
      passWithNoTests: true,    // 无测试文件时不报错
      environment: "happy-dom", // DOM 环境 (非 jsdom)
      setupFiles: "./src/vitest.setup.ts",
    },
  };
});
```

### 关键要点

- **happy-dom** 替代 jsdom，启动速度更快，API 兼容性略低但足以覆盖常见场景
- **globals: true** 启用 Vitest 全局 API，测试文件无需手动 `import { describe, it, expect }`
- **覆盖率阈值很高**: branches 90%, functions 95%, lines 80% — 这对小型组件库有强制约束力
- **setupFiles** 指向 `src/vitest.setup.ts`，在测试启动前运行

---

## 4. MSW 配置模式

### 目录结构

```
mocks/
├── browser.ts        # MSW browser worker (开发环境用)
├── server.ts         # MSW Node server (测试环境用)
├── handlers.ts       # 请求处理器定义
├── service.ts        # faker 数据工厂 (已注释)
├── utils.ts          # Fisher-Yates shuffle
└── entities/
    └── users.json    # 20 条 mock 用户数据
```

### server.ts (测试用)

```typescript
import { setupServer } from "msw/node";
import handlers from "./handlers";

const server = setupServer(...handlers);
export default server;
```

### browser.ts (开发用)

```typescript
import { setupWorker } from "msw/browser";
import handlers from "./handlers";

const worker = setupWorker(...handlers);
export default worker;
```

### handlers.ts (请求处理器)

当前只有一条 mock 路由，其余 CRUD 操作被注释：

```typescript
import { http, HttpResponse } from "msw";

const handlers = [
  http.get("/users", () => {
    return HttpResponse.json({ name: "John" });
  }),
  // ... 注释掉的 POST/PATCH/DELETE 处理
];
export default handlers;
```

### 在 main.tsx 中启动 MSW (开发环境)

```typescript
async function enableMocking() {
  if (process.env.NODE_ENV !== "development") {
    return null;
  }
  const { default: worker } = await import("../mocks/browser");
  return worker.start();
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
        <QueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </React.StrictMode>
  );
});
```

MSW 在开发环境通过 Service Worker 拦截请求，在测试环境通过 Node server 拦截，**应用代码无需任何修改**。这是 MSW 的核心优势：网络层拦截，代码零入侵。

---

## 5. 测试文件模式

### 5.1 单元测试 (Vitest + Testing Library)

#### ErrorBox.test.tsx

```typescript
import { render, screen } from "@application/utils/test-utils";
import ErrorBox from "./ErrorBox";

const DUMMY_ERROR = "Connection Error with 400 code.";

describe("errorBox", () => {
  it("should render the ErrorBox component when a message is provided", () => {
    const message = DUMMY_ERROR;
    render(<ErrorBox message={message} />);

    const alertElement = screen.getByRole("alert");
    expect(alertElement).toBeInTheDocument();

    const svgElement = screen.getByRole("img", { hidden: true });
    expect(svgElement).toBeInTheDocument();
    expect(svgElement).toHaveAttribute("xmlns", "http://www.w3.org/2000/svg");
    expect(svgElement).toHaveAttribute("fill", "none");
    expect(svgElement).toHaveAttribute("viewBox", "0 0 24 24");
    expect(svgElement).toHaveAttribute("height", "100");
    expect(svgElement).toHaveAttribute("width", "100");

    const errorMessage = screen.getByText(DUMMY_ERROR);
    expect(errorMessage).toBeInTheDocument();
  });

  it("should render the default SVG icon when the component is rendered", () => {
    render(<ErrorBox message="Error message" />);
    const svgElement = screen.getByRole("img", { hidden: true });
    expect(svgElement).toBeInTheDocument();
  });

  it("should render the heading and message correctly when the component is rendered", () => {
    const message = "This is an error message";
    render(<ErrorBox message={message} />);

    const headingElement = screen.getByRole("heading", { name: /Error/i });
    expect(headingElement).toBeInTheDocument();
    expect(headingElement).toHaveClass("mt-12 text-3xl text-gray-800 md:text-4xl lg:text-5xl");

    const messageElement = screen.getByText(message).parentElement;
    expect(messageElement).toBeInTheDocument();
    expect(messageElement).toHaveClass("mt-8 text-gray-600 md:text-lg lg:text-xl");
  });
});
```

#### Spiner.test.tsx (文件名拼写错误: Spiner 而非 Spinner)

```typescript
import { render, screen } from "@application/utils/test-utils";
import Spinner from "./Spinner";

describe("spinner", () => {
  it("should render the Spinner component when the it is rendered", () => {
    render(<Spinner />);
    const statusElement = screen.getByRole("status");
    expect(statusElement).toBeInTheDocument();
  });

  it("should render the SVG with correct attributes when the it is rendered", () => {
    render(<Spinner />);
    const svgElement = screen.getByRole("img", { hidden: true });
    expect(svgElement).toBeInTheDocument();
    expect(svgElement).toHaveAttribute("xmlns", "http://www.w3.org/2000/svg");
    expect(svgElement).toHaveAttribute("fill", "none");
    expect(svgElement).toHaveAttribute("viewBox", "0 0 100 101");
  });

  it("should contains the loading path elements when it is rendered", () => {
    render(<Spinner />);
    const svgElement = screen.getByRole("img", { hidden: true });
    expect(svgElement).toContainHTML("<path d='M100 50.5908...'>");
  });

  it("should have a visually hidden loading text when it is rendered", () => {
    render(<Spinner />);
    const loadingText = screen.getByText("Loading...");
    expect(loadingText).toBeInTheDocument();
    expect(loadingText).toHaveClass("sr-only");
  });
});
```

### 5.2 E2E 测试 (Playwright)

文件: `tests/App.e2e.test.ts`

```typescript
import { test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test.describe("App", () => {
  test.fail("The user navigates back and forth.", async ({ page }) => {
    // 导航流程: Users -> User Detail -> Album -> 返回
    await expect(page.getByText("Users")).toBeVisible();
    await page.getByText("Leanne Graham").click();
    // ...
  });

  test.fail("Click on fist User, click on first Album, watch all photos.", async ({ page }) => {
    // 数据验证: 11 行表格, 10 个链接, 50 张图片
    // ...
  });
});
```

**注意**: 所有 E2E 测试均标记为 `test.fail`，表明它们是对未来功能的占位，当前预期不通过。测试涉及 Users/Albums/Photos 的数据遍历，但该功能尚未实现。

---

## 6. TypeScript 配置 (测试相关)

### tsconfig.app.json 测试相关配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "resolveJsonModule": true,       // 允许 import JSON
    "allowImportingTsExtensions": true,
    "noEmit": true,
    "types": ["vitest/globals"],     // 全局 Vitest 类型
    "paths": {
      "@/*": ["src/*"],
      "@application/*": ["application/*"],
      "@domain/*": ["domain/*"],
      "@infrastructure/*": ["infrastructure/*"],
      "@presentation/*": ["presentation/*"]
    }
  },
  "include": [
    "mocks",
    "src",
    "tests",
    "commitlint.config.cts",
    "playwright.config.ts",
    "tailwind.config.ts",
    "vite.config.ts"
  ]
}
```

### 关键点

- **`"types": ["vitest/globals"]`** — 允许全局 `describe` / `it` / `expect` 类型推断
- **路径别名** 与 Vite resolve alias 一致，测试中可用 `@application/utils/test-utils`
- **`resolveJsonModule: true`** — MSW mock 实体可以直接 import JSON

---

## 7. 自定义测试工具

### src/application/utils/test-utils.tsx

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// 基础 render (无 wrapper)
const customRender = (ui: React.ReactElement, options = {}) =>
  render(ui, {
    wrapper: ({ children }) => children,
    ...options,
  });

// 创建测试专用的 QueryClient (禁用 retry)
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,  // 测试中不重试，避免超时
      },
    },
  });

// 带 QueryClientProvider 的 render
const renderWithClient = (ui: React.ReactElement) => {
  const testQueryClient = createTestQueryClient();
  const { rerender, ...result } = render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  );

  return {
    ...result,
    rerender: (rerenderUi: React.ReactElement) =>
      rerender(
        <QueryClientProvider client={testQueryClient}>
          {rerenderUi}
        </QueryClientProvider>
      ),
  };
};

// 带路由的 render (手动 pushState)
const renderWithRouter = (ui: React.ReactElement, { route = "/" } = {}) => {
  window.history.pushState({}, "Test page", route);
  return {
    user: userEvent.setup(),
  };
};

export * from "@testing-library/dom";
export { default as userEvent } from "@testing-library/user-event";
export { customRender as render, renderWithClient, renderWithRouter };
```

### 测试工具分析

| 函数 | 用途 | 当前使用状态 |
|------|------|-------------|
| `render` | 基础 render (带空 wrapper) | 被 ErrorBox / Spinner 测试使用 |
| `renderWithClient` | 带 QueryClientProvider 的 render | 项目中未被使用 |
| `renderWithRouter` | 手动设置路由的 render (不渲染 Router 组件) | 项目中未被使用 |

`renderWithRouter` 的设计值得注意：它只调用 `window.history.pushState` 来设置当前 URL，并返回 `userEvent.setup()` 实例，但**不实际渲染任何 Router provider**。这意味着组件内部使用 `useRouter` 等 hook 时会失败 — 这个工具函数可能是一个 incomplete 的实现。

---

## 8. 测试模式总结

### 8.1 查询模式

- **优先使用 Accessibility 查询**: `getByRole("alert")`, `getByRole("status")`, `getByRole("heading", { name: /Error/i })`, `getByRole("img", { hidden: true })`
- **Text 查询**: `getByText("Loading...")` — 用于查找隐藏的 visually-hidden 文本
- **属性断言**: `toHaveAttribute("xmlns", "...")`, `toHaveClass("sr-only")`
- **HTML 内容断言**: `toContainHTML("<path d='...")` — **注意**: `toContainHTML` 通常不推荐，因为不够健壮

### 8.2 用户事件

项目中导出了 `userEvent` 但**测试文件中未实际使用 userEvent** — 两个单元测试都是纯渲染 + 断言，没有交互操作。

### 8.3 Mock 策略

- MSW 在 `vitest.setup.ts` 中全局启动/重置/关闭
- QueryClient 通过 `renderWithClient` 注入，设置 `retry: false`
- **当前测试未使用 MSW** — ErrorBox 和 Spinner 都是纯 UI 组件，不涉及网络请求

### 8.4 ESLint 测试规则

```typescript
// eslint.config.js 中测试文件的规则
{
  files: ["src/**/*.test.[tj]s?(x)"],
  ignores: ["src/**/*.e2e.test.[tj]s?(x)"],
  ...jestDOM.configs["flat/recommended"],
  ...testingLibrary.configs["flat/react"],
  rules: {
    ...vitest.configs.recommended.rules,
    "vitest/valid-title": [
      "error",
      {
        mustMatch: {
          it: ["^should.*when.+$", "Test title must include 'should' and 'when'"],
        },
      },
    ],
  },
}
```

**关键**: `vitest/valid-title` 规则强制 `it()` 标题必须符合 `should...when...` 格式。这意味着测试描述必须形如 `"should render the ErrorBox component when a message is provided"`。

---

## 9. 代码质量指标

### 测试数量

| 类型 | 文件数 | Test Case 数 | 状态 |
|------|--------|-------------|------|
| 单元测试 (呈现层组件) | 2 | 7 | 全部通过 |
| E2E 测试 (Playwright) | 1 | 2 | 标记为 `test.fail` |

### 覆盖率配置

```
branches:  90%
functions: 95%
lines:     80%
statements: 80%
```

> 当前项目的实际覆盖率未知（覆盖率运行需要安装依赖并执行测试），但鉴于只有两个小型组件被测试且代码库有大量未测试的模块，**当前实际覆盖率很可能远低于阈值**。

### 代码库规模

| 项目 | 数量 |
|------|------|
| 源文件 (src/) | 14 |
| TS 类型声明文件 | 3 |
| 测试文件 | 3 |
| MSW mock 文件 | 6 |
| 配置/构建文件 | 10+ |

---

## 10. 可借鉴的经验

### 10.1 值得采用的模式

1. **MSW + Vitest 集成模式**
   - `setupFiles` 中调用 `server.listen()` / `server.resetHandlers()` / `server.close()`
   - MSW Node server 与 Browser worker 共享同一套 handlers
   - 这是 React 测试领域当前最推荐的 API mock 方案

2. **Test Utilities 导出模式**
   ```typescript
   export * from "@testing-library/dom";
   export { default as userEvent } from "@testing-library/user-event";
   export { customRender as render, renderWithClient, renderWithRouter };
   ```
   重新导出所有 testing-library 方法 + 自定义 render，测试文件只需 `import { render, screen } from "@application/utils/test-utils"`

3. **Vitest globals 模式**
   启用 `globals: true` + `types: ["vitest/globals"]`，测试文件无需手动 import describe/it/expect，减少模板代码

4. **QueryClient 测试封装**
   ```typescript
   const createTestQueryClient = () => new QueryClient({
     defaultOptions: { queries: { retry: false } },
   });
   ```
   测试中禁用 retry 是必要模式，否则查询失败会重试导致超时

5. **ESLint 强制测试命名规范**
   `vitest/valid-title` 规则强制 `should X when Y` 格式，统一团队测试风格

6. **组件与测试同目录 (co-location)**
   ```
   components/ErrorBox/
   ├── ErrorBox.tsx
   └── ErrorBox.test.tsx
   ```

### 10.2 需要避免/改进的模式

1. **文件名拼写错误**: `Spiner.test.tsx` 应为 `Spinner.test.tsx`
2. **不完整的 renderWithRouter**: 只设置了 `window.history.pushState` 但没有实际提供 Router context，应使用 `MemoryRouter` 或 `createRouter` 的测试封装
3. **toContainHTML 断言**: 对 SVG path 的完整 HTML 字符串断言过于脆弱，应使用更细粒度的 attribute/text 断言
4. **覆盖率阈值与实际不符**: 设置了很高的覆盖率阈值但大量代码未被覆盖，应渐进式提升阈值
5. **大量注释代码**: router.ts、App.tsx、main.tsx 中有大量被注释的代码，降低可维护性
6. **MSW handlers 过于简陋**: 仅支持 `/users` GET，应用程序实际应有一组完整的 mock handlers
7. **Happy-DOM 限制**: happy-dom 不支持所有 DOM API，在复杂场景下可能需要切换回 jsdom

### 10.3 可用于 React 测试教程的素材

| 主题 | 素材来源 |
|------|---------|
| Vitest + Vite 集成 | `vite.config.ts` test 配置 |
| MSW setup 最佳实践 | `mocks/server.ts` + `vitest.setup.ts` |
| 自定义 test-utils 模式 | `src/application/utils/test-utils.tsx` |
| Testing Library 查询模式 | `ErrorBox.test.tsx` 中的 getByRole / getByText |
| ESLint 测试规则配置 | `eslint.config.js` 中针对测试文件的 rules |
| Vitest 覆盖率配置 | `vite.config.ts` coverage 字段 |
| 组件 co-location 组织 | `ErrorBox/` 和 `Spinner/` 目录结构 |
| Playwright E2E 集成 | `playwright.config.ts` + `tests/App.e2e.test.ts` |

---

## 附: 测试运行命令

```bash
pnpm test              # 运行所有单元测试 (vitest)
pnpm test:watch        # watch 模式运行单元测试
pnpm test:coverage     # 运行测试 + 覆盖率报告
pnpm test:ui           # Vitest UI 模式
pnpm test:e2e          # Playwright E2E (需安装浏览器)
pnpm test:e2e:install  # 安装 Playwright 浏览器
pnpm test:preview      # vitest-preview 可视化调试
```

**注意**: 项目使用 pnpm 作为包管理器 (`packageManager: "pnpm@9.6.0"`)，在 `package.json` 的 `msw.workerDirectory` 字段中指定了 `public` 目录用于存放 MSW Service Worker 文件。
