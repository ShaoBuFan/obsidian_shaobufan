---
tags:
  - ReactHook
  - ReactHook/appendix
created: 2026-05-22
---
# 附录 A: 练习参考答案

> **使用说明**：先自己尝试完成练习，再来看答案。先看答案会让你失去"自己推出来"的认知收益。

---

## Module 0 练习

### E1: 追踪链表

```jsx
function TraceMe() {
  const [count, setCount] = useState(0);       // Hook 1
  const [showExtra, setShowExtra] = useState(true); // Hook 2
  const extraRef = useRef(null);                // Hook 3

  if (showExtra) {
    useEffect(() => {                           // Hook 4 —— 在条件语句里！
      console.log('extra effect');
    });
  }

  useCallback(() => {                           // Hook 5（或 Hook 4，取决于条件）
    console.log(count);
  }, [count]);

  return <div>{count}</div>;
}
```

**问题**：`useEffect` 在 `if (showExtra)` 条件语句里。

**第一次渲染**（`showExtra = true`）：
```
链表: [useState(count)] → [useState(showExtra)] → [useRef] → [useEffect] → [useCallback]
       节点 1                节点 2                     节点 3      节点 4         节点 5
```

**第二次渲染**（`showExtra = false`，假设用户切换了）：
```
链表: [useState(count)] → [useState(showExtra)] → [useRef] → [useCallback]
       节点 1                节点 2                     节点 3      节点 4（但 React 期望这是 effect 节点！）
```

React 把 `useCallback` 的返回值放在了原本属于 `useEffect` 的位置，导致状态错乱。

### E2: 扩展迷你 React —— useRef

```javascript
function useRef(initialValue) {
  const index = hookIndex;

  if (hookStates[index] === undefined) {
    hookStates[index] = { current: initialValue };
  }

  hookIndex++;
  return hookStates[index];
}
```

与 `useState` 的关键区别：
- `useRef` 不会触发重新渲染——它只是一个数据存储
- `useRef` 存储的是 `{ current: value }` 对象，不是原始值
- `useRef` 没有返回 setter 函数

---

## Module 1 练习

### E3: 选 Hook

| # | 场景 | 答案 | 原因 |
|---|------|------|------|
| 1 | 用户输入的表单文本 | useState | UI 需要反映 |
| 2 | setTimeout 返回的 timer ID | useRef | 不需要触发渲染 |
| 3 | 一个 DOM 元素引用 | useRef | DOM 引用本身不触发渲染 |
| 4 | 一个计数器显示在页面上 | useState | UI 需要反映 |
| 5 | 记录"上一次渲染时的值" | useRef | 存储但不触发渲染 |

### E4: useState 转 useReducer

```javascript
const initialState = { count: 0, step: 1, history: [] };

function counterReducer(state, action) {
  switch (action.type) {
    case 'INCREMENT':
      return {
        ...state,
        count: state.count + state.step,
        history: [...state.history, `+${state.step}`],
      };
    case 'CHANGE_STEP':
      return { ...state, step: action.payload };
    default:
      return state;
  }
}

function Counter() {
  const [state, dispatch] = useReducer(counterReducer, initialState);

  const increment = () => dispatch({ type: 'INCREMENT' });
  const changeStep = (newStep) => dispatch({ type: 'CHANGE_STEP', payload: newStep });

  return (
    <div>
      <p>count: {state.count}</p>
      <p>step: {state.step}</p>
      <p>history: {state.history.join(', ')}</p>
      <button onClick={increment}>+{state.step}</button>
      <input
        type="number"
        value={state.step}
        onChange={e => changeStep(Number(e.target.value))}
      />
    </div>
  );
}
```

### E5: 场景匹配

| # | 场景 | 答案 |
|---|------|------|
| 1 | 保存用户的搜索输入 | useState |
| 2 | 输入变化后 500ms 执行搜索 | useState + useEffect |
| 3 | 获取一个 input DOM 元素 | useRef |
| 4 | 复杂的购物车逻辑 | useReducer |
| 5 | 监听窗口大小变化 | useEffect |
| 6 | 缓存一个过滤后的大列表 | useMemo |
| 7 | 把函数传给 memo 后的子组件 | useCallback |
| 8 | 存储 setTimeout ID | useRef |
| 9 | 读取全局主题配置 | useContext |
| 10 | 读取 DOM 尺寸并在绘制前更新位置 | useLayoutEffect |

---

## Module 2 练习

### E6: useList

```javascript
function useList(initialList = []) {
  const [list, setList] = useState(initialList);

  const add = useCallback((item) => {
    setList(prev => [...prev, item]);
  }, []);

  const remove = useCallback((index) => {
    setList(prev => prev.filter((_, i) => i !== index));
  }, []);

  const updateAt = useCallback((index, newItem) => {
    setList(prev => prev.map((item, i) => (i === index ? newItem : item)));
  }, []);

  const clear = useCallback(() => {
    setList([]);
  }, []);

  return [list, { add, remove, updateAt, clear }];
}
```

### E7: useTimeout

```javascript
function useTimeout(callback, delay) {
  const savedCallback = useRef(callback);

  // 保持 callback 引用最新
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null || delay === undefined) return;

    const id = setTimeout(() => savedCallback.current(), delay);
    return () => clearTimeout(id);
  }, [delay]);
}
```

### E8: 识别模式

- **Hook A (useWindowSize)**：==Composer==（useState + useEffect 组合产生新行为——窗口大小追踪）
- **Hook B (useHover)**：==Extractor==（把 hover 逻辑从组件中移出）
- **Hook C (useShoppingCart)**：==Coordinator==（多个 state + useMemo + useEffect 协调互动）

### E9: 综合模式匹配

| # | 问题 | 模式 | 理由 |
|---|------|------|------|
| 1 | "同步 document.title" | Extractor | 只是把 useEffect 从组件中移出来 |
| 2 | "useState 管理 boolean 太啰嗦" | ==Wrapper== | 只是换个 API，不添加新行为 |
| 3 | "表单验证、提交、重置混在一起" | Coordinator | 多个状态需要彼此协调 |
| 4 | "用户信息分散在 3 个组件" | ==Facade== | 打包成统一服务 |
| 5 | "搜索防抖" | Composer | useState + useEffect 组合创造新能力 |

---

## Module 3 练习

### E10: useClipboard

**Step 1-2：响应式值与分类**

| 值 | 类别 | 为什么 |
|----|------|--------|
| isCopied | State | 需要触发 UI 渲染 |
| timeout ID | Ref | 不需要触发渲染 |

**Step 3：契约**

```typescript
function useClipboard(): { copy: (text: string) => Promise<void>; isCopied: boolean }
```

**Step 5：实现**

```javascript
function useClipboard({ resetDelay = 2000 } = {}) {
  const [isCopied, setIsCopied] = useState(false);
  const timeoutRef = useRef(null);

  const copy = useCallback(async (text) => {
    await navigator.clipboard.writeText(text);
    setIsCopied(true);

    // 清除之前的定时器
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    timeoutRef.current = setTimeout(() => {
      setIsCopied(false);
    }, resetDelay);
  }, [resetDelay]);

  // 清理
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return { copy, isCopied };
}
```

### useMediaQuery

```javascript
function useMediaQuery(query, defaultValue = false) {
  // SSR 安全
  const getMatches = (query) => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return defaultValue;
  };

  const [matches, setMatches] = useState(() => getMatches(query));

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event) => setMatches(event.matches);
    mediaQuery.addEventListener('change', handler);

    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
```

---

## Module 4 练习

### E11: useFetch 加缓存

```javascript
const cache = new Map();

function useFetch(url, options = {}) {
  const { skipCache = false } = options;
  const [data, setData] = useState(() => skipCache ? null : cache.get(url) ?? null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(() => !skipCache && !cache.has(url));

  // refetch 使用递增计数器触发
  const [refetchCount, setRefetchCount] = useState(0);
  const refetch = useCallback(() => setRefetchCount(c => c + 1), []);

  useEffect(() => {
    let cancelled = false;

    const doFetch = async () => {
      // 如果 refetchCount > 0，跳过缓存
      const shouldSkipCache = refetchCount > 0;
      if (!shouldSkipCache && cache.has(url)) {
        if (!cancelled) { setData(cache.get(url)); setLoading(false); }
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (!cancelled) {
          cache.set(url, json);
          setData(json);
        }
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    doFetch();
    return () => { cancelled = true; };
  }, [url, refetchCount]);

  return { data, error, loading, refetch };
}
```

### E14: 综合练习

三种 Hook 的实现要点：

**useNetworkStatus**（选择此题的参考）：

```javascript
function useNetworkStatus() {
  const [status, setStatus] = useState(() => ({
    online: typeof navigator !== 'undefined' ? navigator.onLine : true,
    effectiveType: typeof navigator !== 'undefined' ? navigator.connection?.effectiveType : null,
  }));

  useEffect(() => {
    const update = () => {
      setStatus({
        online: navigator.onLine,
        effectiveType: navigator.connection?.effectiveType ?? null,
      });
    };

    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    navigator.connection?.addEventListener('change', update);

    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
      navigator.connection?.removeEventListener('change', update);
    };
  }, []);

  return status;
}
```

**useIdle**（选择此题的参考）：

```javascript
function useIdle(timeout = 3000) {
  const [isIdle, setIsIdle] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    const reset = () => {
      setIsIdle(false);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setIsIdle(true), timeout);
    };

    const events = ['mousemove', 'keydown', 'scroll', 'click'];
    events.forEach(e => window.addEventListener(e, reset));
    reset(); // 初始化定时器

    return () => {
      events.forEach(e => window.removeEventListener(e, reset));
      clearTimeout(timerRef.current);
    };
  }, [timeout]);

  return isIdle;
}
```

**useScrollPosition**（选择此题的参考）：

```javascript
function useScrollPosition(throttleMs = 100) {
  const [position, setPosition] = useState({
    x: typeof window !== 'undefined' ? window.scrollX : 0,
    y: typeof window !== 'undefined' ? window.scrollY : 0,
  });

  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          setPosition({ x: window.scrollX, y: window.scrollY });
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return position;
}
```

### E12: useClickOutside

```javascript
function useClickOutside(ref, handler) {
  const savedHandler = useRef(handler);
  savedHandler.current = handler;

  useEffect(() => {
    const listener = (event) => {
      const el = ref.current;
      if (!el || el.contains(event.target)) return;
      savedHandler.current(event);
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref]);
}
```

### E13: useCountdown

```javascript
function useCountdown(initialSeconds) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);

  const start = useCallback(() => {
    setIsRunning(true);
  }, []);

  const pause = useCallback(() => {
    setIsRunning(false);
  }, []);

  const reset = useCallback(() => {
    setIsRunning(false);
    setSeconds(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => {
    if (!isRunning || seconds <= 0) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    intervalRef.current = setInterval(() => {
      setSeconds(s => {
        if (s <= 1) {
          setIsRunning(false);
          return 0;
        }
        return s - 1;
      });
    }, 1000);

    return () => clearInterval(intervalRef.current);
  }, [isRunning, seconds]);

  // 卸载时清理
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return { seconds, isRunning, start, pause, reset };
}
```

---

## Module 5 练习

### E15: Bug 狩猎

`useSearch` Hook 中 5 个 bug：

**Bug 1：竞态条件**
```javascript
useEffect(() => {
  setLoading(true);
  fetch(`/api/search?q=${query}`)
    .then(res => res.json())
    .then(data => {
      setResults(data);
      setLoading(false);
    });
}, [query]);
// 修复：添加 cancelled 标记
```

**Bug 2：第二个 useEffect 没有清理事件监听**
```javascript
useEffect(() => {
  const handler = (e) => { if (e.key === 'Escape') { ... } };
  document.addEventListener('keydown', handler);
  // 缺少 return () => document.removeEventListener('keydown', handler);
}, []);
```

**Bug 3：`search` 函数有竞态但没有 cancelled 标记**

参见 Bug 1 的修复。

**Bug 4：`search` 函数没有设置 loading 状态**

用户直接调用 `search()` 时，loading 不会变成 true。

**Bug 5：`setResults` 之后没有 `setLoading(false)` 的竞态保护**

如果组件在请求过程中卸载了，setState 会产生内存泄漏警告。

**修复后的完整版本：**

```javascript
function useSearch(initialQuery = '') {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch(`/api/search?q=${query}`)
      .then(res => res.json())
      .then(data => {
        if (!cancelled) {
          setResults(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [query]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') {
        setQuery('');
        setResults([]);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  const search = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/search?q=${query}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      // handle error
    } finally {
      setLoading(false);
    }
  }, [query]);

  return { query, setQuery, results, loading, search };
}
```

---

## Module 6 练习

### E16: 测试 useToggle

```javascript
import { renderHook, act } from '@testing-library/react';
import { useToggle } from './useToggle';

describe('useToggle', () => {
  it('默认初始值为 false', () => {
    const { result } = renderHook(() => useToggle());
    expect(result.current.value).toBe(false);
  });

  it('可以指定初始值为 true', () => {
    const { result } = renderHook(() => useToggle(true));
    expect(result.current.value).toBe(true);
  });

  it('toggle 切换值', () => {
    const { result } = renderHook(() => useToggle(false));
    act(() => { result.current.toggle(); });
    expect(result.current.value).toBe(true);
    act(() => { result.current.toggle(); });
    expect(result.current.value).toBe(false);
  });

  it('setTrue 设为 true', () => {
    const { result } = renderHook(() => useToggle(false));
    act(() => { result.current.setTrue(); });
    expect(result.current.value).toBe(true);
    // 重复调用应该保持 true
    act(() => { result.current.setTrue(); });
    expect(result.current.value).toBe(true);
  });

  it('setFalse 设为 false', () => {
    const { result } = renderHook(() => useToggle(true));
    act(() => { result.current.setFalse(); });
    expect(result.current.value).toBe(false);
  });
});
```

### E17: 测试 useCountdown

关键测试用例的框架：

```javascript
describe('useCountdown', () => {
  beforeEach(() => { jest.useFakeTimers(); });
  afterEach(() => { jest.useRealTimers(); });

  it('初始秒数正确', () => { /* renderHook(() => useCountdown(10)), expect seconds = 10 */ });
  it('默认不运行', () => { /* expect isRunning = false */ });
  it('start 后每秒减 1', () => {
    // start(), advanceTime by 1000, expect seconds = 9
    // advanceTime by 1000, expect seconds = 8
  });
  it('到 0 时自动停止', () => { /* advanceTime until 0, expect isRunning = false */ });
  it('pause 后暂停', () => { /* start, advance 2s, pause, advance 1s, still same value */ });
  it('reset 恢复初始值', () => { /* start, advance, reset, expect back to initial */ });
  it('卸载时清理定时器', () => { /* unmount, advance, no more updates */ });
});
```
