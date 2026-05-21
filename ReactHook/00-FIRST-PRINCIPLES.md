# Module 0: 第一性原理——Hook 到底是什么？

> **模块目标**：理解 Hook 在 React 内部的实际运作机制。不满足于 API 文档，追踪到 JavaScript 执行层面。

---

## R0: 前置检查

在开始之前，快速回答（心里过一遍就行）：

1. JavaScript 中，一个函数执行完后，它的局部变量还在吗？
2. 什么是闭包？你能在 30 秒内向一个初级开发者解释清楚吗？
3. React 调用你的函数组件时，它拿到的是什么？
4. 你凭直觉回答：Hook 为什么必须以 `use` 开头？

如果对第 2 题不确定，请先阅读本章 0.1 节（闭包深度讲解）再继续。需要更系统的学习可以看附录 E。

---

## 0.1 JavaScript 基础：闭包——函数记住世界的方式

### 0.1.1 函数没有记忆

先回到最基础的地方。看这段代码：

```javascript
function createCounter() {
  let count = 0;
  count = count + 1;
  return count;
}

createCounter(); // 1
createCounter(); // 1 —— 为什么还是 1？
```

为什么第二次调用还是返回 1？因为**函数执行完毕后，它的局部变量（作用域）就被销毁了**。每次调用都是一张全新的白纸。这是 JavaScript 引擎的基本行为。

### 0.1.2 然后看这段代码——闭包改变了规则

```javascript
function createCounter() {
  let count = 0;                    // 局部变量
  return function increment() {     // 返回一个内部函数
    count = count + 1;               // 内部函数引用了外部函数的变量
    return count;
  };
}

const myCounter = createCounter();  // createCounter 执行完毕……了吗？

myCounter(); // 1
myCounter(); // 2
myCounter(); // 3 —— 变量居然"活"下来了！
```

**发生了什么？**

`createCounter()` 执行完毕后，按理说 `count` 应该被垃圾回收销毁。但它没有。因为 `increment` 函数（被返回的内部函数）仍然"抓着" `count` 的引用。JavaScript 引擎发现这个变量还有人要用，就不回收它。

这就是**闭包**：

> **闭包 = 函数 + 函数能访问的外部变量（词法环境）**

更通俗地说：**一个函数，加上它"出生地"的变量，打包在一起就是闭包。**

### ⚡ 费曼检查 T0（闭包前置检查）

> 向一个只学过 JavaScript 基础语法的同事解释：什么是闭包？用你刚刚读到的内容，30 秒讲清楚。要求：不许念定义，必须用生活类比。

（类比提示：你租了一间办公室，合同到期了，但你留了一把备用钥匙。虽然你不再租了，你还是能用那把钥匙进去拿东西。）

### 0.1.3 闭包捕获的是变量，不是值

这是闭包最关键也最容易误解的特性。看代码：

```javascript
function demo() {
  let message = 'hello';

  const fn = () => {
    console.log(message);  // 闭包"捕获"了 message
  };

  message = 'world';       // 在 fn 执行之前改了 message
  fn();                    // 输出什么？
}

demo(); // 输出: "world"，不是 "hello"！
```

如果闭包捕获的是**值**（创建 `fn` 那一瞬间 `message` 的值），输出应该是 `"hello"`。但闭包捕获的是**变量本身**——一个对 `message` 所在内存位置的引用。所以当 `message` 被改成 `"world"` 后，`fn` 读到的自然也是 `"world"`。

这对理解 Hook 至关重要——**当你在 `useEffect` 里读取 state 时，你读到的是闭包捕获的那个"版本的"变量。而哪个版本取决于 effect 是什么时候创建的。**

### 0.1.4 闭包的第一个经典陷阱：循环里的 var

这几乎是每个 JavaScript 开发者都会踩的坑：

```javascript
// 你觉得这个代码会输出什么？
for (var i = 1; i <= 3; i++) {
  setTimeout(() => {
    console.log(i);
  }, i * 1000);
}
// 输出: 4, 4, 4（不是 1, 2, 3！）
```

**为什么？**

`var i` 是函数级作用域的——整个循环共享同一个 `i` 变量。循环先跑完（`i` 变成了 `4`），然后三个 `setTimeout` 的回调才逐一执行——此时它们读到的都是同一个 `i`，值已经是 `4` 了。

三个回调函数各自形成了一个闭包，但它们**捕获的是同一个变量** `i`。

**修复（用 let）**：

```javascript
for (let i = 1; i <= 3; i++) {
  setTimeout(() => {
    console.log(i);
  }, i * 1000);
}
// 输出: 1, 2, 3
```

`let` 是块级作用域的——每次循环迭代创建一个**新的** `i` 变量。三个回调各自捕获了不同的 `i`。

**修复（用闭包手动创建新作用域，ES5 时代的方式）**：

```javascript
for (var i = 1; i <= 3; i++) {
  (function(capturedI) {
    setTimeout(() => {
      console.log(capturedI);
    }, capturedI * 1000);
  })(i);
}
// 输出: 1, 2, 3
```

每次迭代立即执行一个函数，把当前的 `i` **作为参数传入**——参数是新函数作用域里的局部变量，不受循环中 `i` 变化的影响。

### 0.1.5 闭包和 React Hook 的关系

现在把闭包知识应用到 Hook。看这段代码——它是 React 中最常见的闭包 bug：

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      console.log('当前 count:', count);  // 永远输出 0！
    }, 1000);
    return () => clearInterval(timer);
  }, []);  // ← 空 deps 数组

  return (
    <div>
      <p>count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>+1</button>
    </div>
  );
}
```

你不断点击 +1，屏幕上 count 从 0 变成了 10。但控制台每秒输出的永远是 `当前 count: 0`。

**逐层拆解原因：**

**第一层：闭包层面**

`useEffect` 的回调函数形成了一个闭包。这个闭包捕获了**第一次渲染时**的 `count` 变量——值是 `0`。deps 是 `[]`，意味着这个 effect 永远不会重新执行。所以那个闭包里锁住的 `count` 永远是 `0`。

把这个逻辑提取出来看，它和循环陷阱的模式一模一样：

```javascript
// React 的行为，本质上是：
function firstRender() {
  const count = 0;                              // 第一次渲染的 state
  const effectCallback = () => console.log(count); // 闭包捕获 count = 0
  // effect 被 React 存储，以后只重复调用 effectCallback
  // 永远看不到后续渲染中的 count = 1, 2, 3...
}
```

**第二层：Hook 链表层面（用 Module 0 后面的知识）**

每次渲染时，`useState(0)` 在 Fiber 链表上找到自己的节点，取出最新的 `count` 值——所以屏幕上 count 能正确递增。但 `useEffect` 的链表节点上存储的回调**还是第一次渲染时创建的那一个**——因为 deps 是 `[]`，React 认为"不需要更新这个 effect"。旧回调 + 新 state = 过期闭包。

**修复方式（对应 0.1.4 中学到的三种闭包修复思路）**：

| 思路 | 对应闭包修复 | 代码 |
|------|-------------|------|
| 函数式更新 | 不读外部变量，读参数 | `setCount(prev => prev + 1)` |
| 加 deps 重建 | 每次创建新的闭包（类似 let） | `[count]` |
| useRef 中转 | 手动创建"盒子"引用（类似 IIFE） | `ref.current = count` |

```javascript
// 方式一：函数式更新（推荐，如果只需要 setState）
useEffect(() => {
  const timer = setInterval(() => {
    setCount(prev => prev + 1);  // prev 是参数，不是闭包变量
  }, 1000);
  return () => clearInterval(timer);
}, []);

// 方式二：把 count 加入 deps
useEffect(() => {
  const timer = setInterval(() => {
    console.log('当前 count:', count);  // count 变化时 effect 重建，闭包更新
  }, 1000);
  return () => clearInterval(timer);
}, [count]);  // 每次 count 变化，重建 interval

// 方式三：useRef 中转（不想重建 effect 但想读最新值）
function useLatest(value) {
  const ref = useRef(value);
  ref.current = value;  // 每次渲染更新 ref，但 ref 是同一个对象
  return ref;
}

function Counter() {
  const [count, setCount] = useState(0);
  const latestCount = useLatest(count);  // latestCount 对象不变，.current 变

  useEffect(() => {
    const timer = setInterval(() => {
      console.log('当前 count:', latestCount.current);  // 始终读到最新值
    }, 1000);
    return () => clearInterval(timer);
  }, []);  // interval 不需要重建
  // ...
}
```

### 0.1.6 闭包 & Hook 心智模型总结

```
每次渲染 = 一次函数调用 = 一套全新的闭包

第一次渲染:                       第二次渲染:
  count = 0                          count = 1
  effectCB 闭包捕获 count=0    effectCB 闭包捕获 count=1
  onClick 闭包捕获 count=0     onClick 闭包捕获 count=1

React 的规则：
  - 如果 deps 没变 → 复用上一次的闭包（这就是 bug 的来源）
  - 如果 deps 变了 → 创建新闭包（"更新"了）
  - 函数式更新 setState(prev => ...) → 绕开闭包，prev 是参数
  - useRef → 所有渲染共享同一个对象引用，绕开闭包
```

**关键认知**：Hook 的本质是闭包在多次函数调用（渲染）之间的接力。每一次渲染创建一个新闭包，React 通过 Fiber 链表在这些闭包之间传递状态。理解了闭包，就理解了 Hook 的一半。

> **深度阅读**：附录 E 提供了完整的闭包专题教程，包括作用域链、执行上下文、垃圾回收与闭包的关系、更多 Hook 相关的闭包案例和诊断练习。建议在遇到闭包相关困惑时随时查阅。
> → [APPENDIX-E-CLOSURES.md](./APPENDIX-E-CLOSURES.md)

---

## 0.2 第一次调用 vs 第二次调用

React 在执行 `Counter()` 之前，会先准备好一个"记忆空间"，把这个"记忆空间"和当前组件关联起来。当函数内部调用 `useState(0)` 时：

- **第一次**：在这个"记忆空间"里创建一个新格子，存入初始值 `0`
- **第二次**：找到上次创建的那个格子，取出里面的值，忽略传入的 `0`

但 "记忆空间" 具体是什么？让我们追溯到 React 的架构。

## 0.3 Fiber 架构简述

React 在内存中维护了一棵树。这棵树的每个节点叫 **Fiber 节点**。

```
FiberRoot
  └── Fiber (App)
        ├── Fiber (Header)
        │     ├── Fiber (h1)
        │     └── Fiber (nav)
        └── Fiber (Counter)        ← 你的组件在这里
              └── Fiber (button)
```

每个 Fiber 节点对应一个组件实例或 DOM 元素。节点上有一个关键属性：

```
fiber.memoizedState
```

这个属性是一个**单向链表**的头节点。而链表的每个节点——正是一个 Hook 的数据。

## 0.4 Hook 链表：核心模型

假设你有这样一个组件：

```jsx
function Example() {
  const [name, setName] = useState('Alice');    // Hook 1
  const [age, setAge] = useState(25);            // Hook 2
  const inputRef = useRef(null);                 // Hook 3
  useEffect(() => {                              // Hook 4
    document.title = name;
  }, [name]);

  return <input ref={inputRef} value={name} />;
}
```

React 第一次渲染这个组件时，`fiber.memoizedState` 指向的链表长这样：

```
memoizedState
    |
    v
  ┌─────────────────┐
  │ Hook 1: useState │  state: 'Alice'
  │ next ──────────────>
  └─────────────────┘
                      ┌─────────────────┐
                      │ Hook 2: useState │  state: 25
                      │ next ──────────────>
                      └─────────────────┘
                                          ┌─────────────────┐
                                          │ Hook 3: useRef   │  current: null
                                          │ next ──────────────>
                                          └─────────────────┘
                                                              ┌────────────────────┐
                                                              │ Hook 4: useEffect  │  effect fn, deps: ['Alice']
                                                              │ next → null        │
                                                              └────────────────────┘
```

**每个 Hook 调用都在链表上追加一个新节点。** 节点的顺序就是 Hook 调用的顺序。

第二次渲染时，React **按照同样的顺序遍历链表**，从每个节点取出上一次存储的状态：

1. 走到 Hook 1 → `useState('Alice')` 被调用，但返回值来自链表节点上的状态，不是参数 `'Alice'`
2. 走到 Hook 2 → 同上
3. 走到 Hook 3 → 返回同一个 ref 对象
4. 走到 Hook 4 → 比较 `[name]` 的新旧值，决定是否重新执行 effect

这就是 Hook 的全部魔法。**没有神秘的黑盒，只有一个按调用顺序遍历的链表。**

### ⚡ 费曼检查 T1

> 用你的话向一个非 React 开发者解释：为什么 React 的函数组件可以"记住"变量的值？要求：不能使用"链表"、"Fiber"、"memoizedState"这些术语。用一个生活类比。

提示类比方向：储物柜、笔记本、书签……

---

## 0.5 为什么 Hook 不能放在条件语句里——用链表解释

现在你已经知道了链表模型，那 Hook 的规则就完全自明了：

```jsx
function Broken() {
  const [a, setA] = useState(1);   // 链表节点 1

  if (a > 0) {
    const [b, setB] = useState(2); // 链表节点 2 —— 但有条件！
  }

  const [c, setC] = useState(3);   // 期望是节点 3
}
```

**第一次渲染**（`a` 初始值为 1，条件为 true）：
```
链表: [useState(a)] -> [useState(b)] -> [useState(c)]
       节点 1            节点 2            节点 3
```

**第二次渲染**（假设 `a` 变成了 0，条件为 false）：
```
链表: [useState(a)] -> [useState(c)]
       节点 1            节点 2 ← 但这是 c 的调用！React 以为这是 b！
```

第二次渲染时，React 把 `useState(c)` 的结果放在了原本属于 `useState(b)` 的位置。**顺序变了，对应关系全乱了。** 这就是为什么 Hook 必须无条件调用，且顺序必须一致。

### 练习 E1：追踪链表

画出以下组件的 Hook 链表在第一次和第二次渲染时的状态（假设 `showExtra` 初始为 `true`，然后变为 `false`）：

```jsx
function TraceMe() {
  const [count, setCount] = useState(0);
  const [showExtra, setShowExtra] = useState(true);
  const extraRef = useRef(null);

  if (showExtra) {
    useEffect(() => {
      console.log('extra effect');
    });
  }

  useCallback(() => {
    console.log(count);
  }, [count]);

  return <div>{count}</div>;
}
```

这个组件有什么问题？哪些 Hook 调用在条件语句里？

（答案在附录 A）

---

## 0.6 自定义 Hook 没有特殊地位

记住这个事实——**自定义 Hook 只是一个普通的 JavaScript 函数，它恰好调用了其他 Hook。**

```javascript
function useFormInput(initialValue) {
  const [value, setValue] = useState(initialValue);
  const handleChange = useCallback((e) => setValue(e.target.value), []);
  return { value, onChange: handleChange };
}
```

`useFormInput` 不创建新的 Fiber 节点。它创建的 Hook 节点直接挂在**调用它的组件**的 Fiber 链表上。

React 运行时看不到 "useFormInput" 这个名字。它只看到：
1. 一个 `useState` 调用 → 追加节点
2. 一个 `useCallback` 调用 → 追加节点

这就是为什么**自定义 Hook 也必须遵守 Hook 规则**——它们只是把规则代理给了调用方。

### ⚡ 费曼检查 T2

> 自定义 Hook 和普通函数有什么区别？为什么自定义 Hook 必须以 `use` 开头？

提示：区别不在于函数做了什么，而在于 React 的 lint 规则需要靠函数名来判断……

---

## 0.7 自建迷你 React：用数组实现 Hook

最有力的理解方式是自己动手。让我们实现一个**只能运行在特定条件下的玩具 React**。

```javascript
// 迷你 React：用数组存储 Hook 状态
function createMiniReact() {
  let hookStates = [];       // 所有 Hook 的状态存在数组里
  let hookIndex = 0;         // 当前正在处理的 Hook 索引
  let pendingRender = null;  // 待重新渲染的组件

  function useState(initialValue) {
    const index = hookIndex;  // 锁定当前 Hook 的索引

    // 如果是第一次渲染，初始化状态
    if (hookStates[index] === undefined) {
      hookStates[index] = initialValue;
    }

    const setState = (newValue) => {
      hookStates[index] = newValue;
      hookIndex = 0;  // 重置索引，准备重新渲染
      pendingRender(); // 触发重新渲染
    };

    hookIndex++;  // 移动到下一个 Hook
    return [hookStates[index], setState];
  }

  function useEffect(fn, deps) {
    const index = hookIndex;
    const oldDeps = hookStates[index];

    // 检查依赖是否变化
    let hasChanged = true;
    if (oldDeps) {
      hasChanged = deps.some((dep, i) => dep !== oldDeps[i]);
    }

    if (hasChanged) {
      fn();
      hookStates[index] = deps;  // 存储新依赖
    }

    hookIndex++;
  }

  function render(Component) {
    hookIndex = 0;  // 每次渲染前重置索引
    pendingRender = () => render(Component);
    return Component();
  }

  return { useState, useEffect, render };
}
```

现在用这个玩具 React 运行一个组件：

```javascript
const MiniReact = createMiniReact();
const { useState, useEffect, render } = MiniReact;

function App() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('World');

  useEffect(() => {
    console.log(`Count is now: ${count}`);
  }, [count]);

  console.log(`Rendering: count=${count}, name=${name}`);

  return { count, setCount, name, setName };
}

// 第一次渲染
let result = render(App);
// 输出: "Rendering: count=0, name=World"
// 输出: "Count is now: 0"

// 用户点击按钮，count + 1
result.setCount(1);
// 输出: "Rendering: count=1, name=World"
// （useEffect 没有重新执行，因为 count 变了，deps 变了——等等，会执行！
//  因为 oldDeps 的比较检测到了变化）
```

### 关键发现

观察 `setState` 的实现：

```javascript
const setState = (newValue) => {
  hookStates[index] = newValue;  // 直接修改数组
  hookIndex = 0;
  pendingRender();               // 再次调用 Component()
};
```

这里有一个重要的简化：我们的迷你 React 是**同步**重新渲染的（`setState` 直接触发 `render`）。真正的 React 是**异步批量**的。但在核心概念上——"用数组/链表存储状态，用索引/顺序标识 Hook"——完全一致。

### 练习 E2：扩展迷你 React

在我们的小 React 中实现 `useRef`。提示：`useRef` 和 `useState` 非常相似，但它返回的是一个有 `.current` 属性的对象，而且修改 `.current` 不会触发重新渲染。

```javascript
function useRef(initialValue) {
  // 你的代码在这里
}
```

（答案在附录 A）

---

## 0.8 从第一性原理出发：设计 Hook 的本质是什么？

现在我们有了完整的底层模型：

1. **渲染** = React 调用你的函数
2. **Hook** = 函数内部向 Fiber 链表追加节点的操作
3. **状态保持** = 下次渲染时，按相同顺序遍历链表，取出之前存入的值
4. **自定义 Hook** = 一个普通函数，它执行的 Hook 调用会追加到调用者的链表上

这些事实导出一个重要推论：**设计 Hook = 设计一组在渲染之间保持其状态的值和行为的组合。**

你不需要理解神秘的黑盒。你只需要回答：

- 哪些值需要在渲染之间保持？（→ `useState`, `useRef`）
- 哪些值可以从其他值推导？（→ 直接计算，或 `useMemo`）
- 哪些行为需要在特定时机触发？（→ `useEffect`）
- 哪些函数需要保持引用稳定？（→ `useCallback`）

设计 Hook 不是魔法。它是**用 JavaScript 语言特性（闭包）+ React 运行时约定（有序链表）来组织有状态逻辑**。

---

## 0.9 模块回顾

### ⚡ 费曼检查 T3（模块结业检查）

> 录制一段 2 分钟的语音，或用纸笔写出答案："React Hook 是什么？React 是怎么让它工作的？"要求：你的解释必须让一个只学过 JavaScript 基础但没有接触过 React 的人听懂。

如果你在解释时发现某个地方说不清楚——那就是你需要回去重读的部分。

### R4: 跨模块综合

在继续 Module 1 之前，思考这些连接：

1. 闭包（0.1）和 Hook 链表（0.4）之间是什么关系？Hook 链表里的值是怎么通过闭包被 `setState` 引用的？
2. 自定义 Hook（0.6）为什么不需要创建自己的 Fiber 节点？
3. 我们自建的迷你 React 用数组存储状态。真正的 React 为什么选择链表而不是数组？

### 核心概念速查

| 概念 | 一句话 |
|------|--------|
| 函数没有记忆 | 普通函数调用结束后局部变量销毁 |
| Fiber 节点 | 每个组件实例的内存表示 |
| memoizedState | Fiber 上指向 Hook 链表头节点的指针 |
| Hook 链表 | 单向链表，每个节点是一次 Hook 调用的数据 |
| 调用顺序 = 身份 | React 靠调用顺序识别 Hook，不是靠名字 |
| 自定义 Hook | 普通 JS 函数，其 Hook 调用追加到调用者的链表 |
| 设计 Hook | 决定在链表中存储什么值，以及值之间如何互动 |

---

**完成 Module 0 后**，你应该能：
- 画出任意组件对应的 Hook 链表
- 解释为什么 Hook 不能放在条件语句里
- 理解自定义 Hook 和普通函数在运行时的区别
- 用第一性原理（而非 API 记忆）去推理 Hook 的行为

如果以上任何一项不确定，重读相关章节后再进入 Module 1。

**下一步** → [01-BUILDING-BLOCKS.md](./01-BUILDING-BLOCKS.md)
