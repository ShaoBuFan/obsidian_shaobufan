---
tags:
  - React
  - 测试/Vitest
  - 测试/RTL
  - 分析
created: 2026-05-22
---

# EpicWeb React Component Testing with Vitest — Workshop Analysis

> Workshop: https://www.epicweb.dev/workshops/react-component-testing-with-vitest
> Instructor: Artem Zakharchenko (kettanaito)
> Repo: https://github.com/epicweb-dev/react-component-testing-with-vitest

---

## 1. Workshop Structure

### Overall layout

```
exercises/
  01.sunsetting-jsdom/            # Module 1: Why abandon JSDOM
    README.mdx
    FINISHED.mdx
    01.problem.break-jsdom/
    01.solution.break-jsdom/
  02.vitest-browser-mode/         # Module 2: Setting up Vitest Browser Mode
    README.mdx
    FINISHED.mdx
    01.problem.installation-and-setup/
    01.solution.installation-and-setup/
    02.problem.migrate-the-test/
    02.solution.migrate-the-test/
    03.problem.playwright/
    03.solution.playwright/
    04.problem.shared-assets/
    04.solution.shared-assets/
    05.problem.multiple-workspaces/
    05.solution.multiple-workspaces/
  03.best-practices/              # Module 3: Core testing best practices
    README.mdx
    FINISHED.mdx
    01.problem.queries/
    01.solution.queries/
    02.problem.user-events/
    02.solution.user-events/
    03.problem.network-mocking/
    03.solution.network-mocking/
    04.problem.element-presence/
    04.solution.element-presence/
    05.problem.page-navigation/
    05.solution.page-navigation/
  04.debugging/                   # Module 4: Debugging techniques
    README.mdx
    FINISHED.mdx
    01.problem.dom-snapshots/
    01.solution.dom-snapshots/
    02.problem.debugger/
    02.solution.debugger/
    03.problem.breakpoints/
    03.solution.breakpoints/
  05.extras/                      # Module 5: Bonus content
    README.mdx
    FINISHED.mdx
    01.problem.vitest-4.0/
    01.solution.vitest-4.0/
```

### Problem/Solution pattern

Each exercise is split into **problem** (student starts here with incomplete test files and TODO comments) and **solution** (completed reference). Problem files use `🐨` (todo), `💰` (hint), and `💣` (remove) markers in comments to guide the student.

### Module summaries

| Module | Title | What it teaches |
|--------|-------|----------------|
| 01 | Sunsetting JSDOM | Why JSDOM is unreliable: demonstrates `Blob.prototype.text` not implemented, causing tests to fail for valid code |
| 02 | Vitest Browser Mode | 5-step migration: install deps, migrate test syntax, add Playwright provider, share CSS assets via setup file, split unit/browser workspaces |
| 03 | Best Practices | 5 exercises: queries by role/label, real user events (fill/click), MSW network mocking, element presence (toBeInTheDocument), routing wrapper |
| 04 | Debugging | DOM snapshots via `debug()`, debugger statements in browser mode, VS Code conditional breakpoints |
| 05 | Extras | Migrating to Vitest 4.0 (breaking changes: `@vitest/browser` removed, providers as packages, imports from `vitest/browser`) |

---

## 2. Package Dependencies and Versions

### Root package.json workspace (npm workspaces)

Each exercise subdirectory is its own npm workspace (`exercises/*/*`).

### Core dependencies per exercise

```
react: ^19.0.0
react-dom: ^19.0.0
react-router: ^7.x (added in page-navigation exercise)

DevDependencies:
  vitest: ^3.2.0
  @vitest/browser: ^3.2.0     (removed in Vitest 4.0 extra)
  vitest-browser-react: ^0.2.0
  @vitejs/plugin-react: ^4.3.4
  @tailwindcss/vite: ^4.0.11
  tailwindcss: ^4.0.11
  playwright: ^1.49.1         (added in playwright exercise)
  msw: ^x.x.x                 (added in network-mocking exercise)
  @testing-library/react: ^16.1.0       (used only in Module 01, replaced by vitest-browser-react)
  @testing-library/jest-dom: ^6.6.3     (used only in Module 01)
  @testing-library/dom: ^10.4.0         (indirect)
  @testing-library/user-event: ^14.5.2  (not used in browser mode — use Playwright interactions)
  jsdom: ^26.0.0                        (used only in Module 01)
  @types/react: ^19.0.6
  @types/react-dom: ^19.0.3
  @types/node: ^22.10.6       (added in multiple-workspaces for unit tests)
  vite: ^6.2.0
```

### Key ecosystem version notes

- React 19
- Vite 6
- Vitest 3.x (with `@vitest/browser` as the browser mode package)
- Vitest 4.0 (extra module covers breaking changes: provider packages, `vitest/browser` import path, no separate `@vitest/browser` package)
- Playwright as browser provider (not WebdriverIO)
- MSW for network mocking (Fetch API-based handlers)
- Tailwind CSS v4 for styling

---

## 3. Vitest Configuration and Test Setup

### Evolution of vite.config.ts across modules

**Module 01 (JSDOM baseline):**
```ts
test: {
  globals: true,
  environment: 'jsdom',
}
```

**Module 02.01 (Browser mode enabled):**
```ts
test: {
  globals: true,
  browser: {
    enabled: true,
    instances: [{ browser: 'chromium' }],
  },
}
```

**Module 02.03 (Playwright provider):**
```ts
test: {
  globals: true,
  browser: {
    enabled: true,
    provider: 'playwright',
    instances: [{ browser: 'chromium' }],
  },
}
```

**Module 02.04 (Shared CSS via setup file):**
```ts
test: {
  globals: true,
  browser: {
    enabled: true,
    provider: 'playwright',
    instances: [
      {
        browser: 'chromium',
        setupFiles: ['./vitest.browser.setup.ts'],
      },
    ],
  },
}
```

**Module 02.05 (Multiple workspaces — unit + browser):**
```ts
test: {
  workspace: [
    {
      test: {
        name: 'unit',
        globals: true,
        environment: 'node',
        include: ['./src/**/*.test.ts'],
        exclude: [...configDefaults.exclude, 'src/**/*.browser.test.ts(x)?'],
      },
    },
    {
      extends: true,
      test: {
        name: 'browser',
        globals: true,
        include: ['./src/**/*.browser.test.ts(x)?'],
        browser: {
          enabled: true,
          provider: 'playwright',
          instances: [{ browser: 'chromium', setupFiles: ['./vitest.browser.setup.ts'] }],
        },
      },
    },
  ],
}
```

**Module 04 (headless with DEBUG env var toggle):**
```ts
browser: {
  enabled: true,
  headless: !process.env.DEBUG,    // show browser when debugging
  provider: 'playwright',
  instances: [{ browser: 'chromium', setupFiles: ['./vitest.browser.setup.ts'] }],
}
```

### TypeScript configurations

Multiple tsconfig files per exercise, referencing each other:
- `tsconfig.json` — root with project references
- `tsconfig.base.json` — shared compiler options
- `tsconfig.app.json` — app source code
- `tsconfig.node.json` — Vite/Node config files
- `tsconfig.test.json` — initial test config (later split)
- `tsconfig.test.browser.json` — browser tests: includes `@vitest/browser/providers/playwright` types
- `tsconfig.test.unit.json` — unit tests: includes `node` + `vitest/globals` types

### Browser setup file

`vitest.browser.setup.ts`:
```ts
/// <reference path="./src/vite-env.d.ts" />
import './src/index.css'
```

This imports global CSS so component tests have proper styles. It's referenced from the browser instance's `setupFiles` config.

---

## 4. MSW Usage Patterns

### Architecture

```
src/mocks/
  handlers.ts      — defines request handlers
  browser.ts       — setupWorker with handlers

test-extend.ts     — custom test context using vitest.extend()
```

`test-extend.ts` (custom test context):
```ts
import { test as testBase } from 'vitest'
import { worker } from './src/mocks/browser'

type TestContext = { worker: typeof worker }

export const test = testBase.extend<TestContext>({
  worker: [
    async ({}, use) => {
      await worker.start({ quiet: true, onUnhandledRequest: 'error' })
      await use(worker)
      worker.resetHandlers()
      worker.stop()
    },
    { auto: true },  // auto-initialize even if not referenced
  ],
})
```

`src/mocks/handlers.ts`:
```ts
import { http, HttpResponse } from 'msw'
import type { Discount } from '../discount-code-form'

export const handlers = [
  http.post<never, string, Discount>(
    'https://api.example.com/discount/code',
    async ({ request }) => {
      const code = await request.text()
      return HttpResponse.json({ code, amount: 20 })
    },
  ),
]
```

### How MSW is used in tests

1. **Default handler** (in `handlers.ts`): provides baseline mock for happy path.
2. **Per-test overrides** via `worker.use()`: in individual tests, override specific handlers to test edge cases (legacy codes, server errors).
3. **Auto cleanup**: the `auto: true` fixture ensures `worker.resetHandlers()` is called after each test.

### Three scenarios tested with MSW

| Test | Usage pattern |
|------|--------------|
| Happy path (apply code) | Default handler (amount: 20) |
| Legacy code warning | `worker.use()` with `isLegacy: true` response |
| Server error | `worker.use()` with `new HttpResponse(null, { status: 500 })` |

---

## 5. Test Patterns Taught

### Pattern 1: Queries by accessibility (accessibility-first selectors)

| Locator | Usage |
|---------|-------|
| `page.getByRole('button', { name: 'Apply discount' })` | Role-based queries with accessible name |
| `page.getByLabelText('Discount code')` | Form inputs by their label |
| `page.getByText('Discount: EPIC2025 (-20%)')` | Text content matching |
| `page.getByRole('alert')` | Notification/alerts |
| `page.getByRole('link', { name: 'Back to cart' })` | Links by accessible name |

Principle: **find elements the way users do** — by role, label, text. Never by class name, test-id, or CSS selector.

### Pattern 2: User events (real interactions)

```ts
await discountInput.fill('EPIC2025')          // type into input
await applyDiscountButton.click()              // click button
```

Key teaching: **remove visibility assertions before interactions** — if you're going to interact with an element, you don't need to assert it's visible first. The interaction itself implies discoverability.

### Pattern 3: Assertions

```ts
await expect.element(locator).toBeVisible()        // check visibility
await expect.element(locator).toHaveTextContent()  // check text
await expect.element(locator).not.toBeInTheDocument()  // check absence
await expect.element(locator).toHaveAttribute('href', '/cart')  // check attributes
```

Key difference from RTL: Vitest Browser Mode wraps assertions in `await expect.element()` — an auto-retrying assertion model.

### Pattern 4: MSW network mocking

```ts
import { http, HttpResponse } from 'msw'
import { test } from '../test-extend'

test('scenario', async ({ worker }) => {
  worker.use(
    http.post<never, string, Discount>(
      'https://api.example.com/discount/code',
      async ({ request }) => {
        const code = await request.text()
        return HttpResponse.json({ code, amount: 10, isLegacy: true })
      },
    ),
  )
  // ... render, interact, assert
})
```

### Pattern 5: Custom wrappers for routing

```ts
import { MemoryRouter } from 'react-router'

const wrapper = ({ children }: { children: React.ReactNode }) => {
  return <MemoryRouter>{children}</MemoryRouter>
}

render(<DiscountCodeForm />, { wrapper })
```

For tests that need specific routes:
```ts
render(<MainMenu />, {
  wrapper({ children }) {
    return (
      <MemoryRouter initialEntries={['/dashboard/analytics']}>
        {children}
      </MemoryRouter>
    )
  },
})
```

### Pattern 6: DOM debugging

```ts
const { debug } = render(<TicTacToe />)
// ... interact ...
debug() // prints current DOM state
```

### Pattern 7: Unit tests (Node.js workspace)

Pure function tests that don't need the browser:
```ts
import { readFile } from './read-file'

test('returns contents of a text file', async () => {
  await expect(readFile(new File(['hello world'], 'file.txt'))).resolves.toBe('hello world')
})
```

---

## 6. Progressive Conceptual Difficulty

### Naming convention
- Module 01 files: `*.test.tsx` (RTL + JSDOM)
- Module 02.01-02.04: `*.test.tsx` (direct rename, browser mode)
- Module 02.05 onward: `*.browser.test.tsx` (separate from `*.test.ts` unit tests)

### Progression

| Step | Concept | Test file suffix |
|------|---------|-----------------|
| 1 | Why not JSDOM? | `.test.tsx` |
| 2.1 | Install browser mode deps | `.test.tsx` |
| 2.2 | Migrate RTL imports → Vitest browser imports | `.test.tsx` |
| 2.3 | Playwright browser provider | `.test.tsx` |
| 2.4 | Global CSS via setup file | `.test.tsx` |
| 2.5 | Split unit vs browser workspaces + file naming | `.browser.test.tsx` / `.test.ts` |
| 3.1 | Accessibility queries (`getByRole`, `getByLabelText`) | `.browser.test.tsx` |
| 3.2 | User interactions (`fill`, `click`) — remove redundant assertions | `.browser.test.tsx` |
| 3.3 | MSW network mocking (fixtures, per-test overrides) | `.browser.test.tsx` |
| 3.4 | Element presence (`not.toBeInTheDocument`) | `.browser.test.tsx` |
| 3.5 | Routing wrappers (`MemoryRouter`) | `.browser.test.tsx` |
| 4.1 | DOM debugging (`debug()`) | `.browser.test.tsx` |
| 4.2-4.3 | Debugger statements, conditional breakpoints | `.browser.test.tsx` |
| Extra | Vitest 4.0 migration | `.browser.test.tsx` |

### Component evolution

The component under test (`<DiscountCodeForm />`) evolves across the workshop:
1. **Module 02**: Simple `FilePreview` component with `file.text()` (demonstrates JSDOM breakage)
2. **Module 03.01**: Stateless form with input + button
3. **Module 03.02-03.03**: Form with real `fetch()` call, `useReducer` state machine, notification system
4. **Module 03.04**: Form with remove discount functionality (DELETE request)
5. **Module 03.05**: Form with `<Link>` to cart page (React Router integration)
6. **Module 04**: Tic-tac-toe game (debugging), main menu with `NavLink`

---

## 7. Key Teaching Patterns Adaptable for Our Tutorial

### 7.1 Problem-first, then solution

Each exercise starts with a **broken test** or **missing test code**. The student must fix it to understand the concept. This is more effective than reading about the concept and then doing an exercise.

### 7.2 Guided TODO comments

Problem files use consistent markers:
- `🐨` — task to complete
- `💰` — hint/suggestion
- `💣` — code to delete

This gives structure without removing the thinking required.

### 7.3 README.mdx as narrative

Each README is a conversational tutorial that:
1. Explains the **why** (motivation)
2. Provides **step-by-step instructions** with code blocks
3. Uses inline annotations (`add=1` / `remove=1` / `highlight=1`)
4. Has a **companion video** (via `<EpicVideo>` component)

The README can be read independently from the code, making it useful both before and during the exercise.

### 7.4 Progressive replacement, not addition

When transitioning from RTL to Vitest Browser Mode, the workshop doesn't introduce new concepts — it shows how **the same patterns** (render, getByRole, toBeVisible) are done in the new system:
- `render` from `@testing-library/react` → `render` from `vitest-browser-react`
- `screen.getByText()` → `page.getByText()`
- `expect(x).toBeVisible()` → `await expect.element(x).toBeVisible()`

### 7.5 Component complexity mirrors testing complexity

The same component gets refactored across exercises, adding:
- Network calls → need for MSW
- Routing → need for wrappers
- Conditional rendering → need for element presence checks

The student learns testing patterns as natural consequences of code changes.

### 7.6 Vitest.extend() for test infrastructure

MSW integration uses Vitest's built-in fixture system (`test.extend()`), not global setup hooks. This is a key mental model: test infrastructure is set up per-scope, not globally. The `{ auto: true }` pattern makes fixtures run automatically even when not referenced.

### 7.7 Separate TypeScript configs per test type

Browser tests and unit tests have different type requirements:
- Browser: `@vitest/browser/providers/playwright` types
- Unit: `node` + `vitest/globals` types

This is enforced via separate `tsconfig.test.browser.json` and `tsconfig.test.unit.json` files, each targeting specific file patterns.

### 7.8 The "remove redundant assertions" technique

Exercise 03.02 explicitly tells students to **remove** visibility assertions before user interactions. This teaches:
- Interactions imply discoverability (if you can interact, it's visible)
- Removing redundant assertions reduces false-positive risks
- Tests should be minimal: assert only what matters

---

## 8. Unique Approaches and Conventions

### 8.1 No `@testing-library/user-event`

Unlike traditional RTL testing, the workshop does **not** use `@testing-library/user-event`. Browser Mode uses Playwright's native `element.fill()` and `element.click()` — real browser interactions, not simulated ones.

### 8.2 `await expect.element()` semantics

Vitest Browser Mode wraps assertions in `expect.element()` which returns an auto-retrying assertion object. This is similar to Playwright's `expect(locator).toBeVisible()` but with Vitest's assertion API.

### 8.3 File naming convention for test types

| Pattern | Purpose |
|---------|---------|
| `*.test.ts` | Unit tests (Node.js) |
| `*.browser.test.tsx` | Browser/integration tests |
| `*.test.tsx` | Legacy (pre-workspace-split) tests |

### 8.4 No `@testing-library/jest-dom/vitest` in browser mode

Browser mode tests get matchers built into `@vitest/browser`. The `@testing-library/jest-dom` import is removed when migrating away from JSDOM.

### 8.5 MSW Service Worker in `/public`

MSW generates a `mockServiceWorker.js` file in the `public/` directory. This is necessary for MSW in browser mode (the service worker script must be served as a static asset).

### 8.6 epicshop CLI tooling

The workshop uses the `epicshop` CLI for managing exercises. Each exercise is an isolated npm workspace with its own `package.json`, `vite.config.ts`, and TypeScript configs. This allows students to focus on one exercise at a time without cross-contamination.

### 8.7 Three-test-case pattern per exercise

Most best-practice exercises have exactly three test cases:
1. Happy path (applies discount successfully)
2. Edge case (legacy code warning, or similar)
3. Error case (server failure)

This creates a predictable rhythm for learners.

### 8.8 Debugger integration with VS Code

The debugging module teaches how to:
- Add a `.vscode/launch.json` with compound tasks for Node.js + Chrome debugger
- Use `--inspect-brk` with Vitest
- Set `headless: !process.env.DEBUG` for visible browser during debugging
- Use conditional breakpoints on component code (not test code)

### 8.9 Cross-reference external articles

The workshop repeatedly links to Kent C. Dodds' articles:
- [Why I Won't Use JSDOM](https://www.epicweb.dev/why-i-won-t-use-jsdom)
- [The Golden Rule of Assertions](https://www.epicweb.dev/the-golden-rule-of-assertions)
- [The True Purpose of Testing](https://www.epicweb.dev/the-true-purpose-of-testing)
- [What Is a Test Boundary](https://www.epicweb.dev/what-is-a-test-boundary)
- [Inverse Assertions](https://www.epicweb.dev/inverse-assertions)
- [Writing Tests That Fail](https://www.epicweb.dev/writing-tests-that-fail)

These serve as optional deep-dives for students who want more theory.

---

## 9. Summary of Key API Differences (RTL vs Vitest Browser Mode)

| Concern | React Testing Library | Vitest Browser Mode |
|---------|----------------------|---------------------|
| Render | `render(component)` from `@testing-library/react` | `render(component)` from `vitest-browser-react` |
| Queries | `screen.getByText()` / `screen.getByRole()` | `page.getByText()` / `page.getByRole()` from `@vitest/browser/context` |
| Assertions | `expect(el).toBeVisible()` | `await expect.element(page.getByRole()).toBeVisible()` |
| Events | `fireEvent.click()` or `userEvent.click()` | `element.click()`, `element.fill()` (native Playwright) |
| Async | `waitFor()` / `findBy*` queries | Built-in retry in `expect.element()` |
| Matchers | Import `@testing-library/jest-dom/vitest` | Built into `@vitest/browser` |
| Network | `msw` + `setupServer` for Node | `msw` + `setupWorker` for browser + vitest fixture |
| Debug | `screen.debug()` | `render()` returns `{ debug }` function |
