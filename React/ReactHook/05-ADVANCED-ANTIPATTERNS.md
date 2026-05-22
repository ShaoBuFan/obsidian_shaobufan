---
tags:
  - ReactHook
  - ReactHook/antipatterns
created: 2026-05-22
---

# Module 5: 反模式与进阶——培养判断力

> **模块目标**：识别和修复常见的 Hook 设计错误，知道"什么时候不该这么做"和"遇到问题怎么修"。

---

## R0: 前置检查

1. ==闭包==是什么？为什么 React Hook 中闭包会导致"过期值"的问题？
2. `useRef` 和 `useState` 的区别是什么？各自适用什么场景？
3. 一个值可以从已有 props/state 推导出来，应该怎么处理？

---

## 5.1 过期闭包：最隐蔽的 Hook Bug

### 它是什么？

==过期闭包==（Stale Closure）是 Hook 中最常见也最隐蔽的 Bug。它发生在：**一个函数"捕获"了创建时的值，但后来这个值变了，函数里用的还是旧值。**

**过期闭包不是 React 的 bug，而是 React 设计模型的必然结果。** React 的每一次渲染都是一次独立的函数调用，产生一套独立的闭包。依赖数组 `[]` 告诉 React "不要重建这个 effect"——这也就意味着 effect 里的闭包永远锁在第一次渲染的变量上。这不是设计缺陷，而是 React "每次渲染 = 一次快照"模型的自然推论。理解这一点比记住修复方法更重要。

### 直观例子

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      console.log('当前 count 值:', count);  // 永远是 0！
    }, 1000);
    return () => clearInterval(timer);
  }, []);  // 空 deps → effect 只在挂载时执行一次

  return (
    <div>
      <p>count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>+1</button>
    </div>
  );
}
```

运行这段代码。你不断点 +1 按钮，屏幕上的 count 从 0 变到了 10。但控制台每秒输出的永远是 `当前 count 值: 0`。

**为什么？**

因为 `useEffect` 的 deps 是 `[]`，所以 effect 只在组件第一次渲染时执行。`setInterval` 里的回调函数捕获了第一次渲染时的 `count` 值——也就是 `0`。而且因为 effect 永远不再重新执行，这个 `0` 被永远"锁"在了闭包里。

### 类比

过期闭包就像**一张 10 年前的照片**。照片里的人看起来还是你的朋友，但他现在可能完全不一样了。

### 三种修复方式

**方式一：函数式更新**（适用于 setState 场景）

```javascript
useEffect(() => {
  const timer = setInterval(() => {
    setCount(prevCount => prevCount + 1);  // prevCount 始终是最新的
  }, 1000);
  return () => clearInterval(timer);
}, []);
```

**方式二：把依赖加入 deps**（适用于需要读取最新值但不能用函数式更新的场景）

```javascript
useEffect(() => {
  const timer = setInterval(() => {
    console.log('当前 count 值:', count);
  }, 1000);
  return () => clearInterval(timer);
}, [count]);  // count 变化时重建 interval
// 但这样每次 count 变化，interval 都会被清除并重建——有时候这不是你想要的
```

**方式三：useRef 中转**（适用于不想重建 effect 但又需要最新值的场景）

```javascript
function useLatest(value) {
  const ref = useRef(value);
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref;
}

function Counter() {
  const [count, setCount] = useState(0);
  const latestCount = useLatest(count);

  useEffect(() => {
    const timer = setInterval(() => {
      console.log('当前 count 值:', latestCount.current);  // 始终最新！
    }, 1000);
    return () => clearInterval(timer);
  }, []);  // interval 不需要重建

  return (
    <div>
      <p>count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>+1</button>
    </div>
  );
}
```

### 诊断清单

遇到 Hook 读不到最新值时，按这个顺序排查：

1. 值是不是在函数（callback/effect）的闭包里？
2. 函数有没有在 deps 数组中？（如果 effect/callback 没重建，里面的值就不会更新）
3. 能不能用函数式更新代替？（`setState(prev => ...)`）
4. 能不能把值放进 deps？（如果可以接受重建的代价）
5. 如果以上都不行 → 用 `useRef` + `useLatest`

### ⚡ 费曼检查 T1

> 用你自己的话向一个同事解释：什么是过期闭包？它为什么在 Hook 中特别常见？三种修复方式各在什么场景下用？

---

## 5.2 useEffect 误用：最常见的反模式

### 误用一：用 Effect 计算派生值

```javascript
// 错误：用 effect 计算 derived state
function Component({ firstName, lastName }) {
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    setFullName(`${firstName} ${lastName}`);
  }, [firstName, lastName]);

  return <p>{fullName}</p>;
}
```

**问题**：组件先渲染一次（此时 `fullName` 还是旧值），然后 effect 执行，更新 state，再渲染一次。**两次渲染**，而且第一次显示的是过期的 `fullName`。

```javascript
// 正确：直接在渲染期间计算
function Component({ firstName, lastName }) {
  const fullName = `${firstName} ${lastName}`;  // 不需要 state，不需要 effect
  return <p>{fullName}</p>;
}
```

**规则**：凡是能从已有 props/state 直接推导的值，绝不用 ==useEffect==。

### 误用二：用 Effect 处理事件

```javascript
// 错误
function Form() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  useEffect(() => {
    fetchResults(query).then(setResults);
  }, [query]);

  return (
    <>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button onClick={() => {
        // 我想搜索，但查询已经在 effect 中处理了...
      }}>搜索</button>
    </>
  );
}
```

**问题**：搜索逻辑放在了 effect 中，但搜索本质上是**用户点击按钮触发的行为**（事件），不是"状态同步"（effect 的本意）。

```javascript
// 正确：把逻辑放在事件处理器中
function Form() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const data = await fetchResults(query);
    setResults(data);
  };

  return (
    <>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button onClick={handleSearch}>搜索</button>
    </>
  );
}
```

**规则**：如果代码在响应用户的**特定行为**（点击、按键），放在事件处理器中。如果代码在保持**两个系统同步**（React state ↔ 外部 API），放在 useEffect 中。

### 判断框架

```
这个逻辑是？
    │
    ├── 响应用户的特定操作？
    │   └──→ 事件处理器（onClick, onChange, onSubmit...）
    │
    ├── 从已有数据推导新值？
    │   └──→ 渲染期间直接计算
    │
    └── 保持系统间同步？
        └──→ useEffect
```

---

## 5.3 依赖数组的纪律

### 缺失依赖：lint 规则不要关

`react-hooks/exhaustive-deps` 这个 lint 规则**几乎永远不要关闭**。它能捕获的 bug 比你想象的更多。

```javascript
// Lint 会警告：React Hook useEffect has a missing dependency: 'fetchData'
useEffect(() => {
  fetchData(userId);
}, []);  // userId 没有在 deps 里！
```

### 对象/数组依赖的陷阱

```javascript
function Component() {
  const options = { threshold: 0.5 };  // 每次渲染都是新对象！

  useEffect(() => {
    // ...
  }, [options]);  // effect 每次都执行，因为 options 每次都是一个新引用
}
```

**修复方式**：

```javascript
// 方式一：用 useMemo 稳定引用
const options = useMemo(() => ({ threshold: 0.5 }), []);

// 方式二：提取基本类型值放在 deps 里
useEffect(() => {
  observer.current = new IntersectionObserver(callback, { threshold: 0.5 });
}, []);  // 配置不变，用空数组
```

---

## 5.4 过度抽象：什么时候不该提取 Hook

### 症状

- 一个 Hook 只被一个组件使用（没有复用）
- Hook 的逻辑比组件还难理解
- 提取后组件没有变简单，只是变短了

### 什么时候不该提取

**规则**：提取 Hook 应该满足这两条中的至少一条：
1. **复用**：至少有两个地方使用
2. **简化**：提取后的组件**理解成本显著降低**

如果提取只是把代码从一个地方搬到另一个文件，而没有让理解变容易——就不要提取。

### 例子：不该提取的情况

```javascript
// 过度提取：useProductData 只被一个组件使用，且逻辑很简单
function useProductData(productId) {
  const [product, setProduct] = useState(null);
  useEffect(() => {
    fetchProduct(productId).then(setProduct);
  }, [productId]);
  return product;
}
```

这段代码只有 5 行。提取成 Hook 增加了间接层，但没有降低理解成本。

### ⚡ 费曼检查 T2

> 你有一个 200 行的组件，其中有一段 20 行的表单处理逻辑。这段逻辑只在当前组件使用。你应该提取成 Hook 吗？为什么？

---

## 5.5 上帝 Hook

### 症状

一个 Hook 做了太多事情，返回十几个值，内部有 5+ 个 `useState` 和 3+ 个 `useEffect`。

### 例子

```javascript
function useDashboardData(userId) {
  const [profile, setProfile] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  // ... 4 个 useEffect 各自获取不同数据 ...
  // ... 返回 10+ 个值 ...
}
```

### 修复：拆分

```javascript
function useDashboardData(userId) {
  const { profile, loading: profileLoading } = useProfile(userId);
  const { notifications, loading: notifLoading } = useNotifications(userId);
  const { analytics, loading: analyticsLoading } = useAnalytics(userId);
  const { settings, loading: settingsLoading } = useSettings(userId);

  const loading = profileLoading || notifLoading || analyticsLoading || settingsLoading;

  return { profile, notifications, analytics, settings, loading };
}
```

每个子 Hook 做一件事，做好它。父 Hook 只负责组合。

### 判断标准

如果你的 Hook 在 Step 2（分类==响应式值==）时列出了超过 5 个不同类别的值——考虑拆分成多个子 Hook。

---

## 5.6 状态同步反模式

### 症状

两个 `useState` 总是同时更新，保持某种关系：

```javascript
const [items, setItems] = useState([]);
const [selectedIndex, setSelectedIndex] = useState(-1);
const [selectedItem, setSelectedItem] = useState(null);  // 冗余！

useEffect(() => {
  setSelectedItem(items[selectedIndex] ?? null);
}, [selectedIndex, items]);
```

### 修复：单源真理

```javascript
const [items, setItems] = useState([]);
const [selectedIndex, setSelectedIndex] = useState(-1);

// selectedItem 是派生值，不需要 state
const selectedItem = items[selectedIndex] ?? null;
```

**规则**：如果你发现自己在写 `useEffect(() => { setA(deriveFromB(b)); }, [b])`，考虑 A 是不是可以直接从 B 推导。

---

## 5.7 Bug 狩猎练习

### 练习 E15：找出 5 个 Bug

下面的 Hook 中有 5 个 bug。找出并修复它们：

```javascript
function useSearch(initialQuery = '') {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/search?q=${query}`)
      .then(res => res.json())
      .then(data => {
        setResults(data);
        setLoading(false);
      });
  }, [query]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') {
        setQuery('');
        setResults([]);
      }
    };
    document.addEventListener('keydown', handler);
  }, []);

  const search = () => {
    fetch(`/api/search?q=${query}`)
      .then(res => res.json())
      .then(setResults);
  };

  return { query, setQuery, results, loading, search };
}
```

（答案在附录 A）

---

## 5.8 模块回顾

### R4: 跨模块综合

1. 回顾 Module 3 ==六步设计法==中的 Step 6（审查）。本模块的内容（过期闭包、useEffect 误用、状态同步）构成了 Step 6 审查清单的核心条目。试着把本模块的知识组织到 Step 6 的审查框架中。
2. "==过度抽象==" 和 Module 2 中的 ==Extractor== 模式有什么界限？什么时候提取是 Extractor，什么时候提取是过度抽象？
3. 设计一个你自己遇到过的（或想象到的）有 Bug 的 Hook，然后修复它。这是最好的学习方式。

### Bug 诊断快速参考

| 症状 | 可能原因 | 修复 |
|------|----------|------|
| 值总是旧值 | 过期闭包 | 函数式更新 / useRef / 补 deps |
| 不必要的两次渲染 | 用 ==useEffect 算派生值== | 渲染期间直接计算 |
| Effect 执行太频繁 | deps 中有对象/数组字面量 | useMemo 稳定引用 / 提取基本值 |
| 逻辑混乱、难以修改 | ==上帝 Hook== | 拆分成多个专注的子 Hook |
| 两个状态总是同步变化 | ==冗余状态== | 单源真理：一个 state + 派生值 |
| Hook 用完反而更难理解 | 过度抽象 | 内联回组件 |

---

**完成 Module 5 后**，你应该能：
- 诊断并修复过期闭包 bug
- 判断 useEffect 的使用是否合理
- 评估一个 Hook 是否应该被提取（或不应该）
- 审查一个 Hook 并找出潜在问题

**下一步** → [06-TESTING.md](./06-TESTING.md)
