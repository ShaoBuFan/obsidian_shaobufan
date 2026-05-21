# Module 2: 自定义 Hook 的五大模式——设计的词汇表

> **模块目标**：建立识别和应用五种基本自定义 Hook 模式的能力。这是从"读懂 Hook"到"设计 Hook"的桥梁。

---

## R0: 前置检查

1. 自定义 Hook 在运行时和组件函数有什么区别？
2. 自定义 Hook 中调用的 `useState` 在 Fiber 链表上属于谁？
3. `useEffect` 的清理函数在什么时机会执行？
4. `useCallback` 和 `useMemo` 的区别是什么？

---

## 2.1 什么是自定义 Hook？

**自定义 Hook 就是一个普通的 JavaScript 函数，它恰好调用了其他 Hook。**

React 运行时完全不知道你的函数叫 `useFormInput` 还是 `useSomethingElse`。运行时只看到：
- 哦，`useState` 被调用了 → 在链表上追加节点
- 哦，`useEffect` 被调用了 → 在链表上追加节点
- 哦，又一个 `useState` → 追加节点

对 React 来说，自定义 Hook 和组件函数里直接调用 Hook **没有任何区别**。

### 为什么要提取自定义 Hook？

两个理由，缺一不可：
1. **复用**：多个组件需要相同的有状态逻辑
2. **组织**：一个组件太复杂，需要把相关逻辑分组

第二个理由往往更重要。

### ⚡ 费曼检查 T1

> 用一句话解释：自定义 Hook 和组件函数有什么区别？

提示答案：组件函数返回 JSX（或 null），自定义 Hook 可以返回任何东西。

---

## 2.2 模式框架

在深入具体模式之前，先建立理解框架。每一个自定义 Hook 都可以从三个维度分析：

```
        输入（参数）
           |
           v
    ┌──────────────┐
    │  Custom Hook  │ ← 内部调用若干内置 Hook
    └──────────────┘
           |
           v
        输出（返回值）
```

而"内部调用若干内置 Hook"的方式决定了它属于哪种模式。

### 模式一览

| 模式 | 核心操作 | 典型例子 | 类比 |
|------|----------|----------|------|
| Wrapper | 包装一个内置 Hook，简化 API | `useToggle` 包装 `useState` | "老规矩，一杯拿铁"代替每次都念配方 |
| Composer | 组合多个 Hook 产生新行为 | `useDebounce` = `useState` + `useEffect` | 食谱：面粉+鸡蛋+糖 = 蛋糕 |
| Extractor | 把逻辑从组件里移出去 | `useDocumentTitle` 提取 `useEffect` | 整理桌子，把东西分类放进文件夹 |
| Facade | 多个 Hook 打包成统一接口 | `useAuth` 封装登录/登出/状态 | 电视遥控器，隐藏复杂的电路 |
| Coordinator | 管理多个 Hook 之间的互动 | `useForm` 协调字段、验证、提交 | 十字路口的交通指挥员 |

---

## 2.3 模式一：Wrapper（包装器）

### 核心思想

> 内置 Hook 的 API 太通用 → 给它一个更语义化的"别名"

### 模式特征

- 内部**几乎只有一种**内置 Hook
- 返回值是**经过转换**的、更具体的 API
- 不引入新的行为，只是**表达方式的变化**

### 示例 1：useToggle

```javascript
// 不用 useToggle 的时候
function Component() {
  const [isOpen, setIsOpen] = useState(false);

  const open = () => setIsOpen(true);
  const close = () => setIsOpen(false);
  const toggle = () => setIsOpen(prev => !prev);

  return (
    <div>
      <button onClick={toggle}>切换</button>
      <button onClick={open}>打开</button>
      <button onClick={close}>关闭</button>
      {isOpen && <Panel />}
    </div>
  );
}
```

```javascript
// 有了 useToggle
function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => setValue(v => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse };
}

// 使用时语义更清晰
function Component() {
  const { value: isOpen, toggle, setTrue: open, setFalse: close } = useToggle(false);
  // ...
}
```

### 示例 2：useBoolean

`useToggle` 只能 true/false 切换，`useBoolean` 更明确：

```javascript
function useBoolean(initialValue = false) {
  const [value, setValue] = useState(initialValue);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);
  const toggle = useCallback(() => setValue(v => !v), []);
  return [value, { setTrue, setFalse, toggle }];
}
```

### 示例 3：useCounter

```javascript
function useCounter(initialValue = 0, { min, max } = {}) {
  const [count, setCount] = useState(initialValue);

  const increment = useCallback(() => {
    setCount(c => (max !== undefined && c >= max ? c : c + 1));
  }, [max]);

  const decrement = useCallback(() => {
    setCount(c => (min !== undefined && c <= min ? c : c - 1));
  }, [min]);

  const reset = useCallback(() => setCount(initialValue), [initialValue]);

  return { count, increment, decrement, reset };
}
```

### 练习 E6：写你自己的 Wrapper

实现 `useList`——包装 `useState` 来管理数组：

```javascript
// 目标 API：
const [list, { add, remove, clear, updateAt }] = useList([1, 2, 3]);
// add(4) → [1, 2, 3, 4]
// remove(1) → [1, 3, 4] （按索引删除）
// updateAt(0, 99) → [99, 2, 3, 4]
// clear() → []

function useList(initialList = []) {
  // 你的代码
}
```

（答案在附录 A）

---

## 2.4 模式二：Composer（组合器）

### 核心思想

> 单个内置 Hook 的能力不够 → 组合两三个 Hook 创造新行为

### 模式特征

- 内部有**两到三个**不同类型的内置 Hook
- Hook 之间彼此依赖（一个 Hook 的输出是另一个 Hook 的输入）
- 产生**单一内置 Hook 无法单独实现**的行为

### 示例 1：useDebounce

这是最经典的 Composer 模式。延迟更新值的经典实现：

```javascript
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // 每次 value 变化时，设置一个定时器
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 如果 value 在 delay 内再次变化，清除旧定时器
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// 用法
function SearchBox() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);

  useEffect(() => {
    if (debouncedQuery) {
      fetchSearchResults(debouncedQuery);
    }
  }, [debouncedQuery]);

  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

**分析这个 Hook 的内部关系：**

```
value ──→ useState (存储 debounced 后的值)
    │
    └──→ useEffect (设置/清除定时器)
             │
             └──→ 调用 setState（更新 debounced 值）
```

`useState` 和 `useEffect` 协作——各自单独做不了这件事。

### 示例 2：usePrevious

```javascript
function usePrevious(value) {
  const ref = useRef();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;  // 返回的是上一轮的值
}

// 用法
function Counter() {
  const [count, setCount] = useState(0);
  const prevCount = usePrevious(count);
  // prevCount 总是比 count 慢一步
  return <p>现在: {count}, 之前: {prevCount}</p>;
}
```

### 练习 E7：实现 useTimeout

实现在组件挂载 `delay` 毫秒后执行回调的 Hook：

```javascript
function useTimeout(callback, delay) {
  // 你的代码
  // 提示：需要 useRef 存储 callback + useEffect 管理定时器
  // 进阶要求：如果 delay 变化，取消旧定时器，启动新定时器
  // 进阶要求：组件卸载时取消定时器
}
```

（答案在附录 A）

---

## 2.5 模式三：Extractor（提取器）

### 核心思想

> 组件里有一段逻辑让函数变得臃肿 → 把逻辑完整地搬出去

### 模式特征

- 和 Wrapper 的区别：Wrapper 简化 Hook 本身，Extractor 把**一段完整的逻辑**从组件中移出
- 不改变行为——提取前和提取后，组件的行为完全一致
- 纯粹是**组织上的改进**

### 示例 1：useDocumentTitle

提取前：

```jsx
function ProfilePage({ user }) {
  const [profile, setProfile] = useState(null);
  // ... 数据获取逻辑 ...

  // 与 document.title 同步的逻辑混在这里
  useEffect(() => {
    document.title = profile ? `${profile.name} 的个人主页` : '加载中...';
  }, [profile]);

  return <div>...</div>;
}
```

提取后：

```javascript
function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title;
  }, [title]);
}

function ProfilePage({ user }) {
  const [profile, setProfile] = useState(null);
  // ... 数据获取逻辑 ...

  useDocumentTitle(profile ? `${profile.name} 的个人主页` : '加载中...');

  return <div>...</div>;
}
```

### 示例 2：useEventListener

```javascript
function useEventListener(target, event, handler) {
  const savedHandler = useRef(handler);

  // 保持 handler 引用最新
  useEffect(() => {
    savedHandler.current = handler;
  }, [handler]);

  useEffect(() => {
    const element = target?.current ?? target ?? window;
    if (!element?.addEventListener) return;

    const eventListener = (event) => savedHandler.current(event);
    element.addEventListener(event, eventListener);

    return () => element.removeEventListener(event, eventListener);
  }, [target, event]);
}
```

### ⚡ 费曼检查 T2

> Extractor 和 Wrapper 有什么区别？用一句话各描述一个场景：同是包装 `useEffect`，什么情况下是 Wrapper，什么情况下是 Extractor？

---

## 2.6 模式四：Facade（外观）

### 核心思想

> 多个相关 Hook 分散在组件各处 → 打包成一个有意义的整体 API

### 模式特征

- 内部使用**多种不同类型**的内置 Hook
- 把分散的 state, effect, callback, context 打包成一个"服务"
- 对外暴露一个**语义完整**的接口（通常返回一个对象）

### 示例 1：useAuth

```javascript
function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const login = useCallback(async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.login(credentials);
      setUser(response.user);
      localStorage.setItem('token', response.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('token');
  }, []);

  // 页面加载时检查已有 token
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.validateToken(token)
        .then(user => setUser(user))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  return { user, loading, error, login, logout };
}
```

**分析内部结构：**

```
useAuth 内部
├── useState('user')     ──┐
├── useState('loading')  ──┤ 状态簇
├── useState('error')    ──┘
├── useCallback('login')  ── 封装异步逻辑
├── useCallback('logout') ── 封装同步逻辑
└── useEffect             ── 副作用：初始化 + localStorage 同步
```

对外只有一个 `{ user, loading, error, login, logout }` 对象。使用者不需要关心内部有 3 个 state、2 个 callback、1 个 effect。

### 示例 2：useLocalStorage

```javascript
function useLocalStorage(key, initialValue) {
  // 懒初始化：从 localStorage 读取
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  // 包装 setState，同步写入 localStorage
  const setValue = useCallback((value) => {
    setStoredValue(prev => {
      const newValue = typeof value === 'function' ? value(prev) : value;
      localStorage.setItem(key, JSON.stringify(newValue));
      return newValue;
    });
  }, [key]);

  return [storedValue, setValue];
}
```

### ⚡ 费曼检查 T3

> 完成这个类比："Facade 模式就像电视遥控器，因为______。"

---

## 2.7 模式五：Coordinator（协调器）

### 核心思想

> 多个独立的状态需要对彼此的变化做出反应 → 需要一个"交通指挥员"来协调

### 模式特征

- 管理**多个彼此互动的 Hook 之间的关系**
- 内部逻辑描述的是"Hook A 变化时，Hook B 如何反应"
- 复杂度最高，也最有价值

### 示例：useForm

这是 Coordinator 模式最经典的应用。逐步构建：

**第一步：管理一个字段**

```javascript
function useField(initialValue = '') {
  const [value, setValue] = useState(initialValue);
  const [touched, setTouched] = useState(false);

  const onChange = useCallback((e) => {
    setValue(e.target.value);
  }, []);

  const onBlur = useCallback(() => {
    setTouched(true);
  }, []);

  return { value, touched, onChange, onBlur };
}
```

**第二步：管理多个字段 + 验证 + 提交**

```javascript
function useForm({ initialValues, validate, onSubmit }) {
  const [values, setValues] = useState(initialValues);
  const [touched, setTouched] = useState({});
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 当 values 变化时，重新验证
  useEffect(() => {
    if (validate) {
      setErrors(validate(values));
    }
  }, [values, validate]);

  const setFieldValue = useCallback((field, value) => {
    setValues(prev => ({ ...prev, [field]: value }));
  }, []);

  const setFieldTouched = useCallback((field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  }, []);

  const getFieldProps = useCallback((field) => ({
    value: values[field],
    onChange: (e) => setFieldValue(field, e.target.value),
    onBlur: () => setFieldTouched(field),
  }), [values, setFieldValue, setFieldTouched]);

  const handleSubmit = useCallback(async (e) => {
    e?.preventDefault();
    // 把所有字段标记为 touched
    const allTouched = Object.keys(values).reduce(
      (acc, key) => ({ ...acc, [key]: true }), {}
    );
    setTouched(allTouched);

    // 检查是否有错误
    const currentErrors = validate?.(values) ?? {};
    if (Object.keys(currentErrors).length > 0) {
      setErrors(currentErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } finally {
      setIsSubmitting(false);
    }
  }, [values, validate, onSubmit]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    getFieldProps,
    handleSubmit,
  };
}
```

**分析协调关系：**

```
values (useState) ──→ 触发 ──→ 重新验证 (useEffect)
                                │
                                └──→ errors (useState)

touched (useState) ──→ 影响 ──→ 显示错误的条件
isSubmitting (useState) ──→ 影响 ──→ 按钮 disabled
```

### 练习 E8：识别模式

阅读以下 Hook，判断它属于哪种模式：

**Hook A:**
```javascript
function useWindowSize() {
  const [size, setSize] = useState({ width: window.innerWidth, height: window.innerHeight });
  useEffect(() => {
    const handler = () => setSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);
  return size;
}
```
模式：`______`

**Hook B:**
```javascript
function useHover(ref) {
  const [isHovered, setIsHovered] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const enter = () => setIsHovered(true);
    const leave = () => setIsHovered(false);
    el.addEventListener('mouseenter', enter);
    el.addEventListener('mouseleave', leave);
    return () => { el.removeEventListener('mouseenter', enter); el.removeEventListener('mouseleave', leave); };
  }, [ref]);
  return isHovered;
}
```
模式：`______`

**Hook C:**
```javascript
function useShoppingCart() {
  const [items, setItems] = useState([]);
  const totalPrice = useMemo(() => items.reduce((sum, i) => sum + i.price * i.qty, 0), [items]);
  const itemCount = useMemo(() => items.reduce((sum, i) => sum + i.qty, 0), [items]);
  const [discount, setDiscount] = useState(0);
  const finalPrice = useMemo(() => totalPrice * (1 - discount), [totalPrice, discount]);

  // 满 5 件自动打 9 折
  useEffect(() => {
    setDiscount(itemCount >= 5 ? 0.1 : 0);
  }, [itemCount]);

  const addItem = useCallback((item) => {
    setItems(prev => { /* ... */ });
  }, []);

  return { items, totalPrice, itemCount, discount, finalPrice, addItem };
}
```
模式：`______`

（答案在附录 A）

---

## 2.8 模式选择决策树

当你准备设计一个自定义 Hook 时，先问自己：

```
你需要的是...？

  只是换个更语义化的 API
  （不引入新行为）
       │
       └──→ Wrapper
            useToggle, useCounter, useList, useBoolean

  需要一种内置 Hook 给不了的行为
  （需要组合两三个 Hook）
       │
       ├── 只是把逻辑从组件搬出去
       │   └──→ Extractor
       │        useDocumentTitle, useEventListener
       │
       └── 组合创造出新能力
           └──→ Composer
                useDebounce, usePrevious, useTimeout

  需要把一组相关 Hook 打包
  （对外是一个整体服务）
       │
       └──→ Facade
            useAuth, useLocalStorage

  需要管理多个 Hook 之间的相互作用
  （一个变化触发另一个变化）
       │
       └──→ Coordinator
            useForm, useShoppingCart, useWizard
```

### ⚡ 费曼检查 T4

> 拿你最近在项目中遇到的一个组件，尝试用这个决策树分析：如果需要提取一个自定义 Hook，它会属于哪个模式？

---

## 2.9 模式混合：真实世界的 Hook 常是"混血儿"

现实中的自定义 Hook 往往混合了多种模式。比如 `useFetch`：

```javascript
function useFetch(url) {
  const [data, setData] = useState(null);       // state
  const [loading, setLoading] = useState(true);   // state
  const [error, setError] = useState(null);       // state

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      const json = await response.json();
      setData(json);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
```

**分析它的"血统"：**
- **Facade**：把 data/loading/error 三个 state + fetch 逻辑打包成一个"数据获取服务"
- **Composer**：`useState` × 3 + `useCallback` + `useEffect` 组合产生数据获取能力

---

## 2.10 模块回顾

### 练习 E9：综合模式匹配

下面有 5 个问题描述，请为每个问题选择最合适的模式，并简要说明理由：

| # | 问题 | 模式 | 为什么？ |
|---|------|------|----------|
| 1 | "我需要在多个组件中同步 document.title" | | |
| 2 | "useState 管理 boolean 的 toggle/on/off 语义太啰嗦" | | |
| 3 | "我的组件有表单验证、提交、重置三种逻辑混在一起" | | |
| 4 | "用户信息、登录、登出、token 管理分散在 3 个组件里" | | |
| 5 | "我需要一个能延迟更新的值，用于搜索防抖" | | |

### R4: 跨模块综合

1. 回到 Module 0 的链表模型：如果一个组件调用了一个 Facade 模式的 Hook（比如 `useAuth`），它的 Fiber 链表长什么样？画出链表结构。
2. Coordinator 模式中的多个 `useState` 在链表中是连续的吗？它们之间有没有"协调器节点"？
3. 如果一个 Composer 模式的 Hook 内部调用了一个 Wrapper 模式的 Hook，对 React 运行时来说，这和直接在组件中调用两个独立 Hook 有什么区别？

### 核心概念速查

| 模式 | 一句话 | 信号词 |
|------|--------|--------|
| Wrapper | 换一个更语义化的 API | "简化 API" |
| Composer | 组合 Hook 创造新行为 | "创造新行为" |
| Extractor | 把逻辑移出组件 | "组织代码" |
| Facade | 打包成统一服务 | "打包服务" |
| Coordinator | 管理 Hook 间的互动 | "协调互动" |

---

**完成 Module 2 后**，你应该能：
- 识别一个已有的自定义 Hook 使用了哪些模式
- 为给定的问题选择匹配的模式
- 实现 Wrapper 和简单的 Composer 模式 Hook

**下一步** → [03-DESIGN-PROCESS.md](./03-DESIGN-PROCESS.md)（核心模块——六步设计法）
