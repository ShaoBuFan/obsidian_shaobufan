---
tags:
  - ReactHook
  - ReactHook/testing
created: 2026-05-22
---
# Module 6: Hook 测试——验证设计的正确性

> **模块目标**：学会用 `renderHook` 和 `act` 对自定义 Hook 进行行为测试。测试是验证设计的最强工具。

---

## R0: 前置检查

1. `useEffect` 的清理函数在什么时机执行？
2. 什么是==过期闭包==？如何在测试中验证一个 Hook 没有过期闭包问题？
3. 竞态条件（race condition）在数据获取 Hook 中如何产生？

---

## 6.1 为什么测试 Hook？

> "测试一个 Hook 就像碰撞测试一辆车。你不关心引擎内部怎么运作，你关心的是——踩油门，车往前走；踩刹车，车停下来。"

Hook 测试是**==行为测试==**：测试 Hook 对外暴露的 API 在特定操作下是否产生预期行为。你不测试内部实现细节（用了几个 `useState`、有没有 `useEffect`）。

### 一个重要的前置判断：你该直接测试 Hook 吗？

在投入 `renderHook` 之前，先回答一个问题：**这个 Hook 只被一个组件使用，还是会被多个组件/项目复用？**

Kent C. Dodds（React Testing Library 作者）的观点是：**大多数情况下，自定义 Hook 不应该被直接测试。** Hook 是组件的实现细节，通过测试使用它的组件来间接覆盖 Hook 的行为，测试更贴近用户行为，也更抗重构。

直接测试 Hook 的场景：
- 你在构建一个 **Hook 库**（如 react-use、TanStack Query），Hook 本身就是产品
- Hook 的**逻辑足够复杂**，通过组件测试难以穷举所有状态组合
- Hook 被**多个组件共享**，且你希望测试独立于任何一个具体组件

本模块教 `renderHook` 是因为这门课的目标是**设计 Hook**——你需要独立验证 Hook 在不同输入下的行为。但在实际项目中，优先考虑通过组件测试来覆盖 Hook。

### 好的测试回答这些问题

- 初始状态正确吗？
- 调用返回的操作函数后，状态正确更新了吗？
- ==副作用==正确执行和==清理==了吗？
- 边界情况处理了吗？

---

## 6.2 工具：renderHook 和 act

### renderHook

来自 `@testing-library/react`。它在隔离环境中渲染你的 Hook，不需要包装在一个真实组件中。

```javascript
import { renderHook } from '@testing-library/react';

const { result } = renderHook(() => useCounter(0));
// result.current 是 Hook 的返回值
console.log(result.current.count); // 0
```

### act

来自 `react`（或 `@testing-library/react`，它只是重新导出）。用来包裹任何会导致状态更新的操作，确保 React 完成所有渲染和 effect 执行后再继续。

```javascript
import { act } from '@testing-library/react';

act(() => {
  result.current.increment();
});
// 此时所有状态更新和 effect 都已执行完毕
```

### 为什么需要 act？

React 的状态更新是异步的（批量更新）。如果你在 `act` 外面调用 `setState`，然后立即读取 `result.current`，你可能读到**更新前**的值。`act` 确保你读到的是更新后的值。

### ⚠ 关键警告：永远不要解构 `result.current`

```javascript
// 错误！解构捕获的是初始值，后续更新不会反映
const { result } = renderHook(() => useCounter(0));
const { count, increment } = result.current;  // count = 0，永远不变
act(() => { increment(); });
console.log(count);  // 还是 0！

// 正确：每次通过 result.current 读取最新值
const { result } = renderHook(() => useCounter(0));
act(() => { result.current.increment(); });
console.log(result.current.count);  // 1
```

`result` 是一个可变引用（类似 `useRef`），renderHook 在每次重渲染后更新 `result.current`。解构会捕获创建时那一瞬间的值——之后 `result.current` 更新了，但被解构出来的变量不会变。

### waitFor：替代手动 setTimeout

测试异步 Hook 时，比起 `await act(async () => { await new Promise(r => setTimeout(r, 0)); })`，更好的做法是用 `waitFor`：

```javascript
import { renderHook, waitFor } from '@testing-library/react';

const { result } = renderHook(() => useFetch('/api/user'));

await waitFor(() => {
  expect(result.current.loading).toBe(false);
});
// 现在可以安全断言 data 和 error
expect(result.current.data).toEqual({ name: 'Alice' });
```

`waitFor` 会不断重试回调直到断言通过或超时，比手动刷新 Promise 队列更稳健。

### 关于 `@testing-library/react-hooks`

如果你在一些老项目中看到 `import { renderHook } from '@testing-library/react-hooks'`，注意：**React 18 起，`renderHook` 已内置在 `@testing-library/react` 中。** 独立包 `@testing-library/react-hooks` 已废弃。本模块所有示例使用 `@testing-library/react`。

---

## 6.3 测试状态型 Hook

### 示例：测试 useCounter

```javascript
// useCounter.js
function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);
  const increment = useCallback(() => setCount(c => c + 1), []);
  const decrement = useCallback(() => setCount(c => c - 1), []);
  const reset = useCallback(() => setCount(initialValue), [initialValue]);
  return { count, increment, decrement, reset };
}
```

```javascript
// useCounter.test.js
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('应该返回初始值', () => {
    const { result } = renderHook(() => useCounter(10));
    expect(result.current.count).toBe(10);
  });

  it('应该递增 count', () => {
    const { result } = renderHook(() => useCounter(0));

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it('应该递减 count', () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.decrement();
    });

    expect(result.current.count).toBe(4);
  });

  it('应该重置到初始值', () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.increment();
      result.current.increment();
    });
    expect(result.current.count).toBe(7);

    act(() => {
      result.current.reset();
    });
    expect(result.current.count).toBe(5);
  });
});
```

### 练习 E16：测试 useToggle

为 Module 2 中的 `useToggle` 写测试：

```javascript
function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);
  const toggle = useCallback(() => setValue(v => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);
  return { value, toggle, setTrue, setFalse };
}
```

需要测试的场景：
- 默认初始值为 false
- 可以指定初始值为 true
- toggle 切换值
- setTrue 设为 true
- setFalse 设为 false

（答案在附录 A）

---

## 6.4 测试副作用型 Hook

### 挑战

副作用型 Hook 不与外部 API 交互时很难直接验证（比如 `useDocumentTitle` 改变了 `document.title`）。与其 ==mock== `document.title`，不如**直接读取副作用的结果**。

### 示例：测试 useDebounce

```javascript
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

测试需要处理==异步==时间：

```javascript
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from './useDebounce';

// 使用 jest.useFakeTimers 控制时间
describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('应该立即返回初始值', () => {
    const { result } = renderHook(() => useDebounce('hello', 500));
    expect(result.current).toBe('hello');
  });

  it('应该在 delay 之后更新值', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    );

    // 更新 value
    rerender({ value: 'world', delay: 500 });

    // 在 delay 之前，值不应该变化
    act(() => {
      jest.advanceTimersByTime(400);
    });
    expect(result.current).toBe('hello');

    // delay 之后，值应该更新
    act(() => {
      jest.advanceTimersByTime(100);
    });
    expect(result.current).toBe('world');
  });

  it('在 delay 内多次更新应该只保留最新值', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'a' } }
    );

    // 快速连续更新
    rerender({ value: 'b' });
    act(() => { jest.advanceTimersByTime(200); });

    rerender({ value: 'c' });
    act(() => { jest.advanceTimersByTime(200); });

    // 从第一次更新算起才过了 400ms，debouncedValue 应该仍是 'a'
    expect(result.current).toBe('a');

    // 从最后一次更新再等 500ms
    act(() => { jest.advanceTimersByTime(500); });
    expect(result.current).toBe('c');
  });
});
```

### 关键学习点

1. **`jest.useFakeTimers()`** 让你控制时间，不需要真的等 500ms
2. **`rerender`** 用来更新 Hook 的参数，模拟 props 变化
3. **`advanceTimersByTime`** 精确控制时间流逝，验证 debounce 的去抖逻辑
4. 第三个测试验证了 debounce 的核心行为：多次快速更新只保留最后一个

---

## 6.5 测试异步 Hook

### 示例：测试 useFetch

```javascript
import { renderHook, waitFor } from '@testing-library/react';
import { useFetch } from './useFetch';

describe('useFetch', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it('应该从 loading 状态开始', () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ name: 'Alice' }),
    });

    const { result } = renderHook(() => useFetch('/api/user'));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('成功获取数据后应该返回数据', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ name: 'Alice' }),
    });

    const { result } = renderHook(() => useFetch('/api/user'));

    // waitFor 自动重试直到 loading 变为 false
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual({ name: 'Alice' });
    expect(result.current.error).toBe(null);
  });

  it('HTTP 错误应该设置 error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    const { result } = renderHook(() => useFetch('/api/missing'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.data).toBe(null);
  });

  it('refetch 应该重新获取', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ v: 1 }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ v: 2 }) });

    const { result } = renderHook(() => useFetch('/api/data'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual({ v: 1 });

    // 手动 refetch
    act(() => { result.current.refetch(); });
    await waitFor(() => {
      expect(result.current.data).toEqual({ v: 2 });
    });
  });
});
```

---

## 6.6 测试 Ref 型 Hook

### 示例：测试 usePrevious

```javascript
function usePrevious(value) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}
```

```javascript
describe('usePrevious', () => {
  it('第一次渲染应该返回 undefined', () => {
    const { result } = renderHook(() => usePrevious(5));
    expect(result.current).toBeUndefined();
  });

  it('更新后应该返回上一个值', () => {
    const { result, rerender } = renderHook(
      (props) => usePrevious(props.value),
      { initialProps: { value: 5 } }
    );

    rerender({ value: 10 });

    expect(result.current).toBe(5);

    rerender({ value: 20 });

    expect(result.current).toBe(10);
  });
});
```

---

## 6.7 测试清理逻辑

### 验证 useEffect 的清理函数被执行

```javascript
describe('useEventListener', () => {
  it('卸载时应该移除事件监听', () => {
    const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
    const handler = jest.fn();

    const { unmount } = renderHook(() =>
      useEventListener(window, 'resize', handler)
    );

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith(
      'resize',
      expect.any(Function)
    );

    removeEventListenerSpy.mockRestore();
  });
});
```

---

## 6.8 测试原则总结

### ⚡ 费曼检查 T1

> 向一个同事解释：行为测试和实现测试的区别是什么？如果一个测试在 Hook 重构后不需要修改，它属于哪种测试？为什么？

### 测试 WHAT，不测试 HOW

```javascript
// 不好：测试实现细节
// "Hook 应该调用 useState"
// "Hook 应该有一个 useEffect"

// 好：测试行为
// "当 increment 被调用时，count 应该加 1"
// "当 value 改变时，应该在 delay 后更新 debouncedValue"
```

### 每个测试只测一件事

```javascript
// 不好：一个测试覆盖太多
it('useCounter 工作正常', () => {
  // 测试 10 个操作...
});

// 好：专注
it('increment 使 count 加 1', () => { ... });
it('decrement 使 count 减 1', () => { ... });
it('reset 恢复 count 到初始值', () => { ... });
```

### 异步操作用 waitFor

异步状态更新用 `waitFor`，避免手动刷新 Promise 队列。只在需要精确控制时间的情况下使用 fake timers + `act`。

### ⚡ 费曼检查 T2

> `act` 的作用是什么？如果不加 `act` 包裹异步状态更新，会发生什么？结合 React 的批量更新机制解释。

---

## 6.9 模块回顾

### 练习 E17：测试 useCountdown

为 Module 4 中的 `useCountdown` 写测试（或使用你之前实现的版本）：

```javascript
// 需要测试的场景：
// 1. 初始秒数正确
// 2. 默认不运行
// 3. start() 后每秒减 1
// 4. 到 0 时自动停止
// 5. pause() 暂停倒计时
// 6. reset() 恢复到初始值
// 7. 卸载时清理定时器
```

### R4: 跨模块综合

1. 测试和六步设计法（Module 3）有什么联系？测试可以帮助验证 Step 6（审查）的哪些检查项？
2. 如果在测试中发现一个 Hook 很难测试，这是否意味着 Hook 的设计有问题？
3. 反模式（Module 5）中有哪些是测试可以自动发现的？哪些是测试无法捕捉的？

---

**完成 Module 6 后**，你应该能：
- 用 `renderHook` 和 `act` 测试任何自定义 Hook
- 区分行为测试和==实现测试==
- 用 fake timer 测试时间相关的 Hook
- 用 mock fetch 测试异步数据获取 Hook
- 验证清理逻辑

**下一步** → [07-CAPSTONE.md](./07-CAPSTONE.md)
