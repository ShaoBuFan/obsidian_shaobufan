# Module 1: 内置 Hook 深度剖析——从 API 到选择直觉

> **模块目标**：对每个内置 Hook 建立准确的"场景→选择"直觉，知道在什么情况下该用哪个 Hook。

---

## R0: 前置检查

1. React 用什么数据结构存储 Hook 的状态？
2. 为什么 Hook 的调用顺序必须一致？
3. 自定义 Hook 在运行时和普通函数有什么本质区别？
4. 闭包是如何让 Hook 在多次渲染之间"记住"值的？

（如果不能流畅回答，回 Module 0 复习）

---

## 1.1 认识你的工具箱

React 内置了这些 Hook。先对它们有一个整体印象：

```
┌─────────────────────────────────────────────────────┐
│                    React Hooks                       │
├───────────────┬─────────────────────────────────────┤
│ 数据         │ useState, useReducer                 │
├───────────────┼─────────────────────────────────────┤
│ 副作用       │ useEffect, useLayoutEffect           │
├───────────────┼─────────────────────────────────────┤
│ 引用         │ useRef, useImperativeHandle            │
├───────────────┼─────────────────────────────────────┤
│ 记忆化       │ useMemo, useCallback                 │
├───────────────┼─────────────────────────────────────┤
│ 上下文       │ useContext                            │
├───────────────┼─────────────────────────────────────┤
│ 调试/工具    │ useDebugValue, useId, useDeferredValue │
└───────────────┴─────────────────────────────────────┘
```

本模块不展开全部细节，而是聚焦在每一个 Hook 的**本质**——它解决的是哪一类问题。

---

## 1.2 useState：状态单元

### 是什么？

`useState` 在链表中创建一个**状态节点**。节点里存着当前值和用于更新值的 dispatch 函数。

```javascript
const [value, setValue] = useState(initialValue);
```

### 类比

一个**带遥控器的盒子**。`value` 是盒子里现在装的东西。`setValue(newValue)` 是遥控器——按下去盒子里的东西就变了，React 就重绘屏幕。

### 什么时候用？

当一个值满足两个条件时用 `useState`：
1. **它在渲染之间需要保持**（不是每次都重新计算）
2. **改变它需要触发重新渲染**（UI 需要跟着变）

### 什么时候不用？

- 值需要保持，但改变时**不需要**触发渲染 → 用 `useRef`
- 值可以从已有 state/props **推导**出来 → 直接计算，不用 state
- 值的更新逻辑很复杂（多种 action 类型）→ 考虑 `useReducer`

### 关键细节

**懒初始化**：如果初始值计算很昂贵，传一个函数：

```javascript
// 不好：每次渲染都执行一次读取（虽然只有第一次的结果被使用）
const [data, setData] = useState(readFromLocalStorage('key'));

// 好：readFromLocalStorage 只在第一次渲染时执行
const [data, setData] = useState(() => readFromLocalStorage('key'));
```

**函数式更新**：当新值依赖旧值时，用函数形式：

```javascript
// 有风险：如果 count 在闭包中是旧值
setCount(count + 1);

// 安全：React 保证 prev 是当前最新值
setCount(prev => prev + 1);
```

这两者的区别在 Module 5（过期闭包）中会深入探讨。

### ⚡ 费曼检查 T1

> 用三句话解释 `useState`：它是什么？它和普通变量有什么区别？什么时候该用它？

---

## 1.3 useEffect：与外部世界同步

### 是什么？

`useEffect` 在链表中创建一个**副作用节点**。React 在屏幕绘制完成后执行你提供的函数。

```javascript
useEffect(() => {
  // 副作用代码（在 paint 之后执行）
  return () => {
    // 清理代码（在下一次 effect 执行前 / 组件卸载时执行）
  };
}, [dependency1, dependency2]);
```

### 类比

**画干之后做家务**。React 先把屏幕画好（paint），然后执行你的 effect。如果 effect 里需要打扫上一次的遗留（比如移除旧的事件监听），就从 effect 里返回一个清理函数。

### 执行时机

```
渲染开始 → 执行组件函数 → React 更新 DOM → 浏览器绘制屏幕
                                                    ↓
                                            执行 useEffect
```

### 什么时候用？

**`useEffect` 是同步工具**。当 React 的 state 和外部世界需要保持一致时用它：
- 订阅/取消订阅（事件监听、WebSocket、数据源）
- 根据 state 更新 document.title、localStorage
- 组件挂载时发起数据请求
- 与第三方非 React 库交互

### 什么时候不用？

- 在事件处理中能做的事（用户点击时的逻辑）→ 不用 effect
- 可以从 props/state 直接推算的值 → 在渲染期间计算，不用 effect

这条规则如此重要，Module 5 会专门深入讲。

### 依赖数组

React 用 `Object.is()` 比较依赖数组的每一项：

```javascript
useEffect(() => {
  console.log(`name changed to: ${name}`);
}, [name]);  // 只有当 name 变化时才执行
```

- `[]`：只在挂载时执行一次，卸载时执行一次清理
- `[a, b]`：当 `a` 或 `b` 变化时重新执行
- 不传第二个参数：每次渲染后都执行（极少需要）

### 清理函数

```javascript
useEffect(() => {
  const handleResize = () => console.log(window.innerWidth);
  window.addEventListener('resize', handleResize);

  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []); // 只在挂载时添加，卸载时移除
```

**注意**：清理函数不仅在组件卸载时执行，也在**每次 effect 重新执行之前**执行。

```
挂载：    setup()
更新：    cleanup() → setup()
更新：    cleanup() → setup()
卸载：    cleanup()
```

### ⚡ 费曼检查 T2

> 用三句话解释 `useEffect`：它是什么？它什么时候执行？setup / cleanup 模式是什么意思？

---

## 1.4 useRef：穿越渲染的"秘密口袋"

### 是什么？

`useRef` 在链表中创建一个引用节点。节点里存着一个有 `.current` 属性的对象。React 保证**每次渲染返回的都是同一个对象**。

```javascript
const ref = useRef(initialValue);
// ref = { current: initialValue }
```

### 类比

**一个秘密口袋**。你可以把任何东西放进去（`ref.current = anything`），在下一次渲染时它还在那里。但改变口袋里的东西不会触发重新渲染。React 不管你在口袋里放了什么。

### `useRef` vs `useState`：核心区别

| | useState | useRef |
|---|---|---|
| 值改变触发重渲染？ | 是 | 否 |
| 值在渲染中是最新的？ | 是 | 是（但如果是直接修改，渲染不会自动看到更新） |
| 修改方式 | `setState(newVal)` | `ref.current = newVal` |
| 用途 | UI 需要反映的数据 | 渲染不需要反映的数据 |

### 三种主要用途

**用途一：DOM 引用**

```javascript
function InputFocus() {
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current.focus();
  }, []);

  return <input ref={inputRef} />;
}
```

**用途二：存储不需要触发渲染的值**

```javascript
function Timer() {
  const intervalRef = useRef(null);
  const [count, setCount] = useState(0);

  const startTimer = () => {
    intervalRef.current = setInterval(() => {
      setCount(c => c + 1);
    }, 1000);
  };

  const stopTimer = () => {
    clearInterval(intervalRef.current);
  };

  return (
    <div>
      <p>{count}</p>
      <button onClick={startTimer}>开始</button>
      <button onClick={stopTimer}>停止</button>
    </div>
  );
}
```

为什么 `intervalRef` 不用 `useState`？因为 interval ID 不需要显示在 UI 上，也不应该触发渲染。

**用途三：保存"最新的值"，解决过期闭包问题**

这是 `useRef` 最微妙的用法。Module 5 会详细展开，这里先给一个预览：

```javascript
function useLatest(value) {
  const ref = useRef(value);
  ref.current = value;  // 每次渲染都同步更新
  return ref;
}

// 用法：在 callback 中读取最新的值而不需要把它放进 deps 数组
function Chat() {
  const [message, setMessage] = useState('');
  const latestMessage = useLatest(message);

  useEffect(() => {
    const timer = setInterval(() => {
      // 需要在 interval 中读取最新的 message
      // 但不想因为 message 变化而重启 interval
      console.log('Latest message:', latestMessage.current);
    }, 5000);
    return () => clearInterval(timer);
  }, []); // 空 deps，interval 不会重启
}
```

### 练习 E3：选 Hook

以下场景分别该用 `useState` 还是 `useRef`？

1. 用户输入的表单文本 → `______`
2. setTimeout 返回的 timer ID → `______`
3. 一个 DOM 元素引用 → `______`
4. 一个计数器显示在页面上 → `______`
5. 记录"上一次渲染时的值" → `______`

（答案在附录 A）

---

## 1.5 useMemo：缓存计算结果

### 是什么？

`useMemo` 在链表中缓存**计算的结果**。只有依赖变化时才重新计算。

```javascript
const memoizedValue = useMemo(() => expensiveComputation(a, b), [a, b]);
```

### 类比

**记住一道数学题的答案**。只要题目不变（依赖不变），就不用重新算。题目变了，再算一遍。

### 什么时候用？

两个条件同时满足：
1. 计算是**昂贵的**（遍历大数组、复杂数学运算、递归）
2. 计算依赖的值**不经常变**

### 什么时候不用？

- 计算很快（简单加减、字符串拼接）→ 直接算，`useMemo` 自己也有开销
- 计算结果需要作为其他组件的 prop 且该组件用了 `React.memo` → 用 `useMemo` 保持引用稳定

### 注意

React **不保证** `useMemo` 一定会缓存。在未来的 React 版本中，React 可能选择"忘记"缓存值来释放内存。所以**不要把 `useMemo` 当成语义保证**——只当成性能优化。

### ⚡ 费曼检查 T3

> `useMemo(() => a + b, [a, b])` 和直接 `const result = a + b` 区别是什么？为什么前者不一定更快？

---

## 1.6 useCallback：缓存函数引用

### 是什么？

```javascript
const memoizedFn = useCallback(() => doSomething(a, b), [a, b]);

// 等价于
const memoizedFn = useMemo(() => () => doSomething(a, b), [a, b]);
```

### 什么时候用？

两个条件同时满足：
1. 函数作为 prop 传给子组件**且**子组件用了 `React.memo`
2. 函数作为其他 Hook（`useEffect`, `useMemo`）的依赖

### 什么时候不用？

- 函数只用作事件处理器（`onClick`, `onChange` 等）且子组件没有 memo → 不需要
- 函数作为 `useEffect` 的依赖，但你其实可以直接把 effect 放在事件处理器里 → 重构，不要用 `useCallback` 来"修补"

### ⚡ 费曼检查 T4

> `useCallback(fn, deps)` 和 `useMemo(() => fn, deps)` 有什么区别？（提示：几乎没区别，但有一个微小的……）

---

## 1.7 useReducer：复杂状态逻辑

### 是什么？

```javascript
const [state, dispatch] = useReducer(reducer, initialState);

// reducer 是一个纯函数
function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + 1 };
    case 'decrement':
      return { ...state, count: state.count - 1 };
    default:
      return state;
  }
}
```

### 类比

**一个更正规的盒子**。`useState` 是直接换里面的东西。`useReducer` 是你发一个指令（action），有一个专门的处理程序（reducer）决定盒子里的东西怎么变。

### 什么时候用 `useReducer` 而不是 `useState`？

1. **下一状态依赖上一状态且逻辑复杂**：如果你的 `setState(prev => ...)` 已经有了多层嵌套逻辑
2. **多个 state 总是一起更新**：比如表单的多个字段
3. **需要测试状态转换逻辑**：reducer 是纯函数，可以脱离 React 单独测试
4. **状态更新有明确的"动作类型"**：如 `FETCH_START`, `FETCH_SUCCESS`, `FETCH_ERROR`

### 练习 E4：useState 转 useReducer

把下面的 `useState` 版本改成 `useReducer` 版本：

```javascript
function Counter() {
  const [count, setCount] = useState(0);
  const [step, setStep] = useState(1);
  const [history, setHistory] = useState([]);

  const increment = () => {
    setCount(c => c + step);
    setHistory(h => [...h, `+${step}`]);
  };

  const changeStep = (newStep) => {
    setStep(newStep);
  };

  // 你的 useReducer 版本
}
```

（答案在附录 A）

---

## 1.8 useLayoutEffect：浏览器绘制之前

### 和 useEffect 的唯一区别

```
useEffect:         渲染 → 绘制到屏幕 → 执行 effect
useLayoutEffect:   渲染 → 执行 effect → 绘制到屏幕
```

### 什么时候用 `useLayoutEffect` 而不是 `useEffect`？

**几乎永远不需要。** 只有当你需要在浏览器绘制之前**同步地**读取或修改 DOM，避免用户看到闪烁时：

```javascript
// 测量 DOM 尺寸，避免闪烁
function Tooltip({ children, content }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const ref = useRef(null);

  useLayoutEffect(() => {
    const rect = ref.current.getBoundingClientRect();
    setPosition({ x: rect.x, y: rect.y + rect.height });
  }, []);

  return (
    <>
      <span ref={ref}>{children}</span>
      <div style={{ position: 'absolute', left: position.x, top: position.y }}>
        {content}
      </div>
    </>
  );
}
```

**默认用 `useEffect`。只有当出现视觉闪烁问题时，再尝试换成 `useLayoutEffect`。**

---

## 1.9 useContext：穿越组件树的隧道

### 是什么？

```javascript
const ThemeContext = createContext('light');

// Provider 在上层
function App() {
  return (
    <ThemeContext.Provider value="dark">
      <DeepChild />
    </ThemeContext.Provider>
  );
}

// Consumer 在下层
function DeepChild() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>...</div>;
}
```

### 类比

**对讲机广播**。Provider 在顶层喊话，不管中间隔了多少层组件，下面的组件通过 `useContext` 直接收听。

### 什么时候用？

- 多个层级需要访问同一个值（主题、语言、认证状态）
- 避免 props drilling（把 props 一层层往下传）

### 什么时候不用？

- 只有一两层需要传 → 直接用 props，更简单
- 值变化非常频繁 → context 会导致所有 consumer 重渲染，考虑状态管理库

---

## 1.10 场景匹配练习

### 练习 E5：为每个场景选择合适的 Hook

| # | 场景 | 选择 |
|---|------|------|
| 1 | 保存用户的搜索输入 | `____` |
| 2 | 输入变化后 500ms 执行搜索 | `____` + `____` |
| 3 | 获取一个 input DOM 元素 | `____` |
| 4 | 复杂的购物车逻辑（增删改查 + 折扣计算） | `____` |
| 5 | 监听窗口大小变化 | `____` |
| 6 | 缓存一个过滤后的大列表 | `____` |
| 7 | 把函数传给 memo 后的子组件 | `____` |
| 8 | 存储 setTimeout ID | `____` |
| 9 | 读取全局主题配置 | `____` |
| 10 | 读取 DOM 尺寸并在绘制前更新位置 | `____` |

（答案在附录 A）

---

## 1.11 模块回顾

### R4: 跨模块综合

1. 用 Module 0 的链表模型解释：为什么 `useRef` 返回的对象在整个生命周期中是同一个？（提示：链表的节点没有被替换……）
2. `useEffect` 的依赖数组比较机制和链表模型有什么关系？
3. 如果在一个自定义 Hook 里调用 `useState`，这个 state 在 Fiber 链表上属于谁——自定义 Hook 还是调用它的组件？

### 核心概念速查

| Hook | 核心问题 | 选择信号 |
|------|----------|----------|
| useState | "这个值需要在渲染间保持，且变化时触发渲染吗？" | UI 需要反映的数据 |
| useEffect | "React 外部世界需要和这个 state 同步吗？" | API、订阅、DOM 操作 |
| useRef | "这个值需要在渲染间保持，但变化时不触发渲染吗？" | DOM、timer ID、最新值缓存 |
| useMemo | "这个计算结果可以缓存直到依赖变化吗？" | 昂贵计算、引用稳定 |
| useCallback | "这个函数引用需要在依赖变化前保持稳定吗？" | memo 子组件 prop、effect 依赖 |
| useReducer | "状态逻辑复杂到需要显式的 action 类型吗？" | 多子状态、明确的状态转换 |
| useLayoutEffect | "这个副作用必须在用户看到之前执行吗？" | 测量 DOM、避免闪烁 |
| useContext | "这个值需要穿越多个层级传递吗？" | 主题、认证、全局配置 |

---

**完成 Module 1 后**，你应该能：
- 为常见场景立即匹配正确的内置 Hook
- 理解每个 Hook 什么时候用，什么时候**不用**
- 能解释 useState/useRef/useMemo/useCallback 之间的选择判断

**下一步** → [02-CUSTOM-HOOK-PATTERNS.md](./02-CUSTOM-HOOK-PATTERNS.md)
