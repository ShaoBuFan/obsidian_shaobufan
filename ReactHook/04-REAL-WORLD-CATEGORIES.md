# Module 4: 真实场景分类——六步法实战

> **模块目标**：在六大真实场景中反复使用六步设计法，直到每个决策变成肌肉记忆。

---

## R0: 前置检查

1. 默写六步设计法每一步的名称和核心问题。
2. 使用 `useState` 和 `useRef` 的分类标准是什么？
3. 一个值可以从其他值推导出来，应该用 State 还是直接计算？

---

## 4.1 类别一：数据获取

### 核心挑战

这是最常见的 Hook 类别。需要管理三态（loading / error / data）、处理竞态条件、可能还需要缓存和重新获取。

### 解剖 useFetch

我们在 Module 3 设计了基础版 `useFetch`。现在推进到**生产级版本**。

#### 基础版的问题

```javascript
function useFetch(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return { data, error, loading };
}
```

**问题 1：竞态条件**

如果 URL 变化很快（从 `/users/1` 变成 `/users/2`），结果返回的顺序不一致可能导致显示错误的数据。

```
时间线：
  请求 /users/1 发出 ──────────────────→ 返回（慢）
  请求 /users/2 发出 ──────→ 返回（快）
                                    ↓
                              UI 先显示 user 2（正确）
                                    ↓
                              UI 被覆盖为 user 1（错误！）
```

**修复**：

```javascript
function useFetch(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;  // 关键！

    setLoading(true);
    setError(null);

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (!cancelled) setData(data);
      })
      .catch(err => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;  // 当 effect 重新运行时，标记上一次请求为"已取消"
    };
  }, [url]);

  return { data, error, loading };
}
```

**原理**：每次 effect 重新执行时，React 先运行上一次的清理函数。清理函数把 `cancelled` 设为 `true`，因此哪怕旧请求最终返回了，`setData` 也不会被调用。

#### 问题 2：没有 refetch

```javascript
const refetch = useCallback(() => {
  setLoading(true);
  setError(null);
  fetch(url)
    .then(res => res.json())
    .then(setData)
    .catch(setError)
    .finally(() => setLoading(false));
}, [url]);
```

把 `refetch` 暴露出去，让用户可以在不改变 URL 的情况下重新获取。

#### 问题 3：HTTP 错误没有被当作错误处理

```javascript
.then(res => {
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
})
```

`fetch` 只在网络错误时 reject。HTTP 错误状态码（404, 500 等）不会触发 reject，需要手动检查 `res.ok`。

### 练习 E11：扩展 useFetch

给 useFetch 添加缓存功能：

```javascript
// 目标：同一个 URL 不重复请求
const cache = new Map(); // 放在模块级别

function useFetch(url) {
  // 改造逻辑：
  // 1. 如果 cache 中有结果，直接返回
  // 2. 如果没有，发起请求并存入 cache
  // 3. refetch 时忽略 cache 中的值
}
```

（答案在附录 A）

---

## 4.2 类别二：DOM 交互

### 核心挑战

需要获取 DOM 元素引用（`useRef`），设置事件监听（`useEffect`），并且**在 JavaScript 闭包中一直拿到最新值**。

### 解剖 useEventListener

```javascript
function useEventListener(target, event, handler, options) {
  const savedHandler = useRef(handler);

  // 每次渲染更新 savedHandler，确保 handler 始终是最新的
  useEffect(() => {
    savedHandler.current = handler;
  }, [handler]);

  useEffect(() => {
    const element = target?.current ?? target;
    if (!element?.addEventListener) return;

    const listener = (event) => savedHandler.current(event);
    element.addEventListener(event, listener, options);

    return () => element.removeEventListener(event, listener, options);
  }, [target, event, options]);
}
```

**关键设计决策：**

1. **为什么用 `savedHandler`？** 因为 event listener 在第一次 effect 执行时被添加到 DOM。如果 handler 变了（因为闭包引用了新值），但我们不想 remove + add listener，只需要让 listener 调用的函数指针指向最新的 handler。`savedHandler` 就是做这个"指针转发"的。

2. **为什么 `target` 同时接受 ref 和原始值？** 灵活性——`useEventListener(ref, ...)` 和 `useEventListener(window, ...)` 都可以。

3. **为什么 `event` 变化时要重建 listener？** 因为不同事件类型需要不同的 listener，无法避免 remove + add。

### 练习 E12：useClickOutside

设计一个 Hook，检测用户是否点击了指定元素的外部（常用于关闭下拉菜单、弹窗等）。

需求：
- 接收一个 ref（要监听的元素）
- 接收一个 callback（点击外部时执行）
- 正确清理事件监听

（答案在附录 A）

---

## 4.3 类别三：浏览器 API 封装

### 核心挑战

这些 API 存在于 React 外部。需要用 `useEffect` 做同步桥梁，用 `useState` 把外部值"拉"进 React 的渲染系统。

### 解剖 useGeolocation

```javascript
function useGeolocation(options = {}) {
  const [state, setState] = useState({
    loading: true,
    accuracy: null,
    altitude: null,
    altitudeAccuracy: null,
    heading: null,
    latitude: null,
    longitude: null,
    speed: null,
    error: null,
  });

  const optionsRef = useRef(options);
  optionsRef.current = options;  // 保持 options 最新但不重新触发 effect

  useEffect(() => {
    if (!navigator.geolocation) {
      setState(s => ({ ...s, loading: false, error: new Error('Geolocation not supported') }));
      return;
    }

    const onSuccess = (position) => {
      setState(s => ({
        ...s,
        loading: false,
        ...position.coords,
      }));
    };

    const onError = (error) => {
      setState(s => ({ ...s, loading: false, error }));
    };

    const watchId = navigator.geolocation.watchPosition(
      onSuccess,
      onError,
      optionsRef.current
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  return state;
}
```

**关键设计决策：**

| 决策 | 为什么 |
|------|--------|
| 所有地理位置属性放在一个对象 state 里 | 它们总是一起更新，分开多个 state 没有意义 |
| `options` 用 ref 存储 | 如果 options 在 deps 里，每次对象字面量都会重建 watch |
| 用 `watchPosition` 而不是 `getCurrentPosition` | 需要持续追踪位置变化 |
| 返回 `state` 对象而不是解构 | 用户可以用 `state.latitude` 等语义化方式访问，也可以 `...state` 展开 |

### ⚡ 费曼检查 T1

> `useGeolocation` 使用了一个 "大 state 对象" 而不是拆成 8 个小 state。在什么情况下大 state 对象更好？什么情况下拆成多个 state 更好？

---

## 4.4 类别四：表单管理

### 核心挑战

表单是 Coordinator 模式的典型应用。需要管理多个字段、验证逻辑、提交状态和错误展示之间的协调。

我们在 Module 2 已看到基本版本的 `useForm`。这里重点讨论一个更深入的模式。

### 模式：受控 vs 非受控表单 Hook

**受控型**（Hook 管理所有状态）：

```javascript
const { values, getFieldProps, handleSubmit } = useForm({ ... });
<input {...getFieldProps('email')} />
```

**非受控型**（DOM 管理状态，Hook 只负责提交时读取）：

```javascript
const { register, handleSubmit } = useForm();
<input {...register('email')} />
```

两种各有适用场景。受控型适合需要实时验证的场景，非受控型适合表单简单、不需要实时验证的场景（更少的渲染，更好的性能）。

### 设计选择对照表

| 考量 | 受控型 | 非受控型 |
|------|--------|----------|
| 实时验证 | 容易 | 困难 |
| 条件字段 | 容易 | 困难 |
| 性能 | 每个按键都渲染 | 只在提交时读取 |
| 代码量 | 较多 | 较少 |
| 适用场景 | 复杂表单、多步骤表单 | 登录/注册、设置页 |

---

## 4.5 类别五：动画与计时

### 核心挑战

时间是一个"外部世界"的概念。React 的渲染循环和 JavaScript 的计时器循环是两套独立的系统。计时 Hook 的本质是**用 effect 桥接这两套系统**。

### 解剖 useInterval

`setInterval` 的最常见陷阱是**过期闭包**：

```javascript
// 错误的 useInterval
function useInterval(callback, delay) {
  useEffect(() => {
    const id = setInterval(callback, delay);
    return () => clearInterval(id);
  }, [delay]);  // callback 没有在 deps 里！
}
// 问题：如果 callback 引用了某个 state，它永远是第一次渲染时的值
```

**正确的 useInterval（Dan Abramov 版本）**：

```javascript
function useInterval(callback, delay) {
  const savedCallback = useRef(callback);

  // 每次渲染更新最新的 callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // 设置 interval
  useEffect(() => {
    if (delay === null) return;

    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
```

**设计要点：**
- callback 的最新引用通过 ref 传递，不放进 deps
- delay 放在 deps 里——delay 变化时应该重建 interval
- `delay === null` 时暂停 interval

### 练习 E13：useCountdown

实现一个倒计时 Hook：

```javascript
function useCountdown(initialSeconds) {
  // 需求：
  // - seconds: 当前剩余秒数
  // - isRunning: 是否正在倒计时
  // - start(): 开始倒计时
  // - pause(): 暂停
  // - reset(): 重置到初始值
  // - 到 0 时自动停止
}
```

（答案在附录 A）

---

## 4.6 类别六：状态管理

### 核心挑战

当多个组件需要共享状态时，`useState` 不够用——每个 `useState` 只在当前组件内有效。需要将状态"提升"到共享层。

### 模式一：useReducer + Context

```javascript
// 1. 创建 Context
const CountContext = createContext(null);
const CountDispatchContext = createContext(null);

// 2. Provider 组件
function CountProvider({ children }) {
  const [state, dispatch] = useReducer(countReducer, { count: 0 });
  return (
    <CountContext.Provider value={state}>
      <CountDispatchContext.Provider value={dispatch}>
        {children}
      </CountDispatchContext.Provider>
    </CountContext.Provider>
  );
}

// 3. 消费 Hook
function useCount() {
  const state = useContext(CountContext);
  const dispatch = useContext(CountDispatchContext);
  if (state === null) throw new Error('useCount must be used within CountProvider');
  return { state, dispatch };
}
```

### 模式二：外部 Store 订阅

```javascript
function useStore(store) {
  // 从外部 store 读取初始值
  const [state, setState] = useState(store.getState());

  useEffect(() => {
    // 订阅 store 变化 → 同步到 React state
    const unsubscribe = store.subscribe((newState) => {
      setState(newState);
    });
    return unsubscribe;
  }, [store]);

  return state;
}
```

这是 Redux、Zustand 等库的核心原理——用 `useEffect` 把外部 Store 的发布/订阅机制桥接到 React 的渲染系统。

### ⚡ 费曼检查 T2

> 解释 `useStore` 的工作原理。为什么需要 `useState` + `useEffect` 两个 Hook？只用一个行不行？

---

## 4.7 模块回顾

### 练习 E14：综合

从以下三个中选择一个，用六步法设计：

1. **useNetworkStatus**：除了在线/离线，还要能获取网络连接类型（4g、wifi 等）
2. **useIdle**：检测用户是否在指定时间内没有任何交互
3. **useScrollPosition**：返回当前页面的滚动位置（x, y），含节流

### R4: 跨模块综合

1. 对比六个类别中各自最常用的内置 Hook 组合。能找到模式吗？
2. "将外部世界同步到 React" 是所有类别的共同主题吗？有没有哪个类别不是这样？
3. 你现在能不看任何参考资料，独立完成这六个类别的基础版本吗？如果不能，哪个类别需要重练？

---

**完成 Module 4 后**，你应该能：
- 在六大真实场景中熟练运用六步设计法
- 识别并处理竞态条件
- 理解"受控 vs 非受控"的设计取舍
- 用 `useEffect` 将任何浏览器 API 桥接到 React

**下一步** → [05-ADVANCED-ANTIPATTERNS.md](./05-ADVANCED-ANTIPATTERNS.md)
