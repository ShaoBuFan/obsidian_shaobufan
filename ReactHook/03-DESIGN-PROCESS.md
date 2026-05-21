# Module 3: 六步设计法——从问题到 Hook 的完整流程

> **模块目标**：掌握一个可重复的、不依赖灵感的、从"我有个问题"到"我有一个 Hook"的完整设计流程。

---

## R0: 前置检查

1. 列出五大自定义 Hook 模式，各举一个例子。
2. 所有模式中，哪一个是"只改变 API，不改变行为"的？
3. `useEffect` 和 `useState` 组合在一起能产生什么单独各自做不到的？

---

## 3.1 设计鸿沟：为什么"懂了"但"写不出"？

先诊断一个问题。说明白了 "懂了"和"能设计"之间到底差了什么。

**当你"读懂"一个 Hook 时，你的大脑在做这件事：**

```
代码 → 识别关键字(useState, useEffect...) → 理解每一行 → 拼接整体行为 → "哦，这个 Hook 做 X"
```

这是一种**自底向上的解码过程**。

**当你"设计"一个 Hook 时，你的大脑需要做的事完全不同：**

```
"我想做 X" → X 需要哪些会变化的值？ → 每个值属于哪种类型？ → 输入输出是什么？
→ 用哪些内置 Hook？ → 它们怎么配合？ → 写出来
```

这是一种**自顶向下的构建过程**。

解码和构建——它们调动的认知能力不是同一套。就像你读得懂一本小说不意味着你写得出一本小说。读代码锻炼的是**模式识别**，写代码需要的是**结构化分解 + 组合**。

六步设计法的目的就是给你一个**构建流程**——用科学的步骤代替灵感，让你每次"从零设计"时知道第一步做什么、第二步做什么、每一步的产出是什么。

---

## 3.2 六步设计法总览

```
Step 1: 识别响应式值
  "什么会变化？"
  产出：所有会随着时间/交互/数据而变化的东西

Step 2: 分类每个值
  "这个变化属于哪种类型？"
  产出：每个值 → 一个 Hook 类别

Step 3: 设计契约（先写接口签名！）
  "输入是什么？输出是什么？"
  产出：类型签名

Step 4: 选择原语 & 依赖图
  "用什么内置 Hook？它们之间怎么依赖？"
  产出：Hook 依赖关系图

Step 5: 实现
  "按顺序写出来，处理生命周期"
  产出：可工作的代码

Step 6: 审查
  "追踪渲染周期，检查边界情况"
  产出：经过验证的代码
```

### ⚡ 费曼检查 T1

> 读完这六个步骤后，用你自己的话写下来——每一步问的问题是什么？不许复制原文。

---

## 3.3 工作示例：useOnlineStatus（"我做"——全程演示）

现在跟着这个例子走。每个步骤的**推理过程**我都写出来，你观察的不是"最终代码"而是"每一步是怎么想的"。

### 问题

"我需要知道用户当前是在线还是离线，并且当网络状态改变时自动更新。"

### Step 1: 识别响应式值

拿起纸和笔（或者空白文件），写下这个问题中所有会**变化**的东西：

```
在线状态：是/否 —— 会变化
```

就是这一个值——用户可以从在线变成离线，也可以从离线变回在线。

**原则**：把一切会变化的都抓出来。哪怕是"可能变化"的也先记下来。后面可以删，但不能漏。

### Step 2: 分类每个值

| 值 | 类别 | 为什么？ |
|----|------|----------|
| 在线状态 | State | 需要触发 UI 重渲染（用户看到的状态要实时反映） |

只有一个值，分类很清楚。它需要触发渲染 → `useState`。

如果我们发现有值属于"推导值"（可以根据已有值算出来），那就不需要 state——直接计算。

### Step 3: 设计契约

**在写任何实现代码之前，先写好函数签名。**

```typescript
// 输入：无
// 输出：当前是否在线（boolean）
function useOnlineStatus(): boolean
```

先写签名是一个关键习惯。它迫使你在考虑"怎么做"之前先想清楚"这个 Hook 对外提供什么"。

### Step 4: 选择原语 & 依赖图

需要什么内置 Hook？

```
useState  —— 存储在线状态 → 触发渲染
useEffect —— 订阅/取消订阅 online/offline 事件
```

依赖关系很简单：

```
useEffect (订阅浏览器事件)
    │
    │ 事件触发时
    v
setState (更新在线状态)
    │
    v
useState 返回新值 → 触发渲染
```

### Step 5: 实现

```javascript
function useOnlineStatus() {
  // Step 4 原语 1: 存储在线状态
  const [isOnline, setIsOnline] = useState(
    () => typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  // Step 4 原语 2: 订阅浏览器事件
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 清理
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
```

**注意一个细节**：`useState` 的初始值没用简单的 `true`，而是读了 `navigator.onLine`（如果可用）。这是一个实用性决策——初始值应该尽可能反映当前真实状态。

### Step 6: 审查

逐项检查：

**渲染追踪：**

- **挂载**：`useState` 创建状态节点（值 = navigator.onLine），`useEffect` 添加事件监听
- **网络断开**：`handleOffline` 被调用 → `setIsOnline(false)` → 触发重渲染 → 组件拿到 `false`
- **网络恢复**：`handleOnline` 被调用 → `setIsOnline(true)` → 触发重渲染
- **卸载**：`useEffect` 的清理函数移除事件监听

**检查清单：**

| 检查项 | 状态 |
|--------|------|
| 有需要清理的副作用吗？ | ✅ 事件监听已清理 |
| 有遗漏的依赖吗？ | ✅ deps 数组 `[]` 是正确的（事件监听器不变） |
| 有过期闭包吗？ | ✅ handleOnline/handleOffline 内部调用的 `setIsOnline` 是 dispatch 函数，不会过期 |
| 边界情况：SSR? | ✅ 使用 `typeof navigator !== 'undefined'` 保护 |
| 边界情况：初始值正确吗？ | ✅ 从 navigator.onLine 读取 |

Hook 完成。从问题出发，六步抵达一个生产就绪的 Hook。

---

## 3.4 引导练习：useIntersectionObserver（"我们一起做"）

现在轮到你来主导。我会给出每一步的提示，但**你来做决策和写代码**。准备好附录 D 的工作手册模板。

### 问题

"我需要知道某个 DOM 元素当前是否在视口中可见（用于懒加载、曝光统计等场景）。"

### Step 1（你来做）：识别响应式值

列出所有会变化的东西：

```
_______________________
_______________________
_______________________
```

### Step 2（你来做）：分类

| 值 | 类别 | 为什么？ |
|----|------|----------|
| | | |
| | | |
| | | |

（提示：有一项不需要用 Hook——它只是函数的参数。）

### Step 3（你来做）：设计契约

```typescript
function useIntersectionObserver(____________): ____________
```

（提示：需要知道观察哪个元素、IntersectionObserver 的配置项。）

### Step 4（你来做）：选择原语 & 依赖图

需要的 Hook：

```
______  —— 存储是否在视口中的状态
______  —— 创建和管理 IntersectionObserver
______  —— 存储 callback 的最新引用（避免过期闭包）
```

### Step 5（你来做）：实现

```javascript
function useIntersectionObserver(ref, options = {}) {
  // 你的代码
}
```

（提示：IntersectionObserver 的构造函数接收 callback 和 options。callback 在元素进入/离开视口时被调用。）

### Step 6（你来做）：审查

- 清理：IntersectionObserver 需要 `disconnect()` 吗？
- 过期闭包：callback 中引用的 state 是最新的吗？
- 边界情况：ref.current 为 null 时怎么办？

完成后再看下面的参考答案。

---

### 参考答案

```javascript
function useIntersectionObserver(ref, options = {}) {
  const [isIntersecting, setIsIntersecting] = useState(false);

  // 保存最新的 setIsIntersecting（实际上状态更新函数本身是稳定的，所以这里可以不存）
  // 但为了展示模式，保留这个 ref
  const optionsRef = useRef(options);
  optionsRef.current = options;

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      optionsRef.current
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [ref]);

  return isIntersecting;
}
```

对比你的实现：
- 有没有遗漏 `observer.disconnect()` 清理？
- 初始值为什么是 `false`？（因为默认假设元素不在视口中）
- `options` 用 ref 存储而不是直接放在 deps 里——为什么？（因为 `options` 通常是对象字面量，每次渲染都是新的引用，如果放在 deps 里会导致 effect 频繁重建）

---

## 3.5 脚手架练习：useFetch（"你用模板做"）

现在用附录 D 的工作手册模板。我已经给你填了部分内容，空白部分你来完成。

### 问题

"我需要从 API 获取数据。Hook 应该处理 loading、error、data 三种状态，并且支持重新获取。"

### 工作手册

```
Step 1: 识别响应式值
  - data（响应数据）—— 会变化
  - error（错误信息）—— 会变化
  - loading（加载状态）—— 会变化
  - ______（还有什么变化？）

Step 2: 分类
  Value          → Category → Why?
  data           → [______]  → UI 需要显示，变化时需要渲染
  error          → [______]  → [______]
  loading        → [______]  → [______]

Step 3: 契约
  function useFetch(______): ______

Step 4: 原语
  ______  ← data
  ______  ← error
  ______  ← loading
  ______  ← 封装 fetch 逻辑
  ______  ← 触发 fetch

Step 5: 实现

  function useFetch(url, options = {}) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchData = useCallback(async () => {
      // 你的代码
    }, [url]);

    useEffect(() => {
      // 你的代码
    }, [fetchData]);

    return { data, error, loading, refetch: fetchData };
  }

Step 6: 审查
  - 组件卸载时如果请求还在进行中，会发生什么？
  - 快速切换 URL 时，旧的请求结果会不会覆盖新的请求结果？
  - 如何处理 HTTP 错误状态码（如 404, 500）？
```

（完成后查看附录 A 中 Module 4 下的 E11 参考答案，特别是 Step 6 中的"竞态条件"问题。基础版 useFetch 也在 Module 4 的 4.1 节有详细解剖。）

### ⚡ 费曼检查 T3

> 录制一段 3 分钟的讲解："六步设计法是什么？为什么需要它？"目标听众：一个和当初的你一样——能读懂 Hook 但不会自己设计——的开发者。如果你的讲解中出现了"呃……"或说不清楚的地方，那就是你还需要强化的步骤。

---

## 3.6 独立练习：useMediaQuery（"你自己做"）

现在只给你问题和工作手册空白模板。不提供任何提示。

### 问题

"我需要根据 CSS 媒体查询（如 `(max-width: 768px)`）来获取一个布尔值，用于响应式布局逻辑。"

### 你的工作手册

打开附录 D 的设计过程工作手册模板，填写所有 6 个步骤。实现你的 `useMediaQuery`。

要求：
- 支持传入媒体查询字符串，如 `'(max-width: 768px)'`
- 当查询结果变化时，Hook 应该返回新值并触发重渲染
- 正确处理事件监听器的清理

### 挑战版

再加两个要求（如果你觉得上面太简单）：
- 支持 SSR（服务端渲染）环境
- 支持传入一个默认值作为 SSR 时的返回值

完成后对照附录 A 的参考答案。

---

## 3.7 逆向工程：从代码回到设计

这是最强大的学习方法之一。给定一个已经完成的 Hook，**重构它背后的设计决策**。

### 待逆向的 Hook：useKeyPress

```javascript
function useKeyPress(targetKey) {
  const [keyPressed, setKeyPressed] = useState(false);

  useEffect(() => {
    const downHandler = (e) => {
      if (e.key === targetKey) setKeyPressed(true);
    };
    const upHandler = (e) => {
      if (e.key === targetKey) setKeyPressed(false);
    };

    window.addEventListener('keydown', downHandler);
    window.addEventListener('keyup', upHandler);

    return () => {
      window.removeEventListener('keydown', downHandler);
      window.removeEventListener('keyup', upHandler);
    };
  }, [targetKey]);

  return keyPressed;
}
```

### 你的任务

在纸上或用脑回答以下问题：

1. **Step 1（识别响应式值）**：设计者识别出了哪些会变化的值？
2. **Step 2（分类）**：`keyPressed` 为什么被分类为 State 而不是 Ref？
3. **Step 3（契约）**：为什么输入是 `targetKey: string` 而不是 `KeyboardEvent`？
4. **Step 4（原语）**：为什么用了 `useEffect` 而不是 `useLayoutEffect`？
5. **Step 5（实现）**：为什么 `downHandler` 和 `upHandler` 在 `useEffect` 内部定义而不是在外面？
6. **Step 6（审查）**：`[targetKey]` 作为 deps 数组正确吗？会不会有什么问题？

### ⚡ 费曼检查 T2

> 如果你要向另一个开发者解释如何设计 useKeyPress，你会怎么说？把六步法里每一步的关键决策讲清楚。记录并自我检查——有没有哪个决策你说不清楚"为什么"？

---

## 3.8 六步法的常见陷阱

### 陷阱 1：在 Step 1 遗漏响应式值

**症状**：实现后发现有东西"应该变但没变"。
**解决**：Step 1 时宁可多列，不要少列。列多了可以在 Step 2 删除（因为有些东西不需要 Hook），列少了就只能补丁。

### 陷阱 2：在 Step 2 把所有值都归类为 State

**症状**：过多的 `useState` 导致不必要的渲染。
**解决**：严格按这个优先级分类：直接计算 > useRef > useMemo > useState。

### 陷阱 3：跳过 Step 3 直接写代码

**症状**：写到一半发现输入输出不确定，反复修改。
**解决**：先写类型签名。类型签名就是设计文档——不写签名就开始写代码 = 没有图纸就开始盖房子。

### 陷阱 4：在 Step 5 中过早优化

**症状**：一上来就加 `useCallback` / `useMemo` "以防万一"。
**解决**：先让 Hook 功能正确。完成 Step 6 的审查后，如果发现性能问题再优化。过早优化是万恶之源。

---

## 3.9 模块回顾

### 练习 E10：从零设计 useClipboard

这是一个完全独立的练习。使用六步法设计 `useClipboard`：

**需求**："我需要一个 Hook 来读取和写入系统剪贴板。"

功能：
- `copy(text)`：将文本复制到剪贴板
- `isCopied`：布尔值，表示最近一次复制是否成功
- 复制成功后 2 秒自动重置 `isCopied` 为 false

请使用附录 D 的工作手册，完整走一遍六步法。

### R4: 跨模块综合

1. 看 Module 2 中的 `useForm`（Coordinator 模式），用六步法分析它的设计过程。Step 1 识别出了哪些响应式值？
2. 六步法中的 Step 4（选择原语）和 Module 2 中的模式分类有什么关系？模式是不是 Step 4 的"快捷方式"？
3. 如果一个 Hook 只需要 Step 1-6 中的某几步就能完成（比如 Wrapper 模式基本不需要 Step 4 的依赖图），这正常吗？

### 核心概念速查

| 步骤 | 问自己 | 常见错误 |
|------|--------|----------|
| Step 1 | "什么会变？" | 遗漏隐含的变化 |
| Step 2 | "变了之后要怎样？" | 全归类为 State |
| Step 3 | "输入什么？输出什么？" | 跳过直接写代码 |
| Step 4 | "用什么 Hook？怎么连？" | 选错 Hook 类型 |
| Step 5 | "按顺序写出来" | 过早优化 |
| Step 6 | "追踪检查" | 漏掉清理和边界 |

---

**完成 Module 3 后**，你应该能：
- 拿到任何一个需要有状态逻辑的需求，用六步法独立设计出 Hook
- 对每个步骤的决策说出"为什么"
- 在审查阶段发现并修复过期闭包和遗漏清理的问题

**下一步** → [04-REAL-WORLD-CATEGORIES.md](./04-REAL-WORLD-CATEGORIES.md)
