---
tags:
  - ReactHook
  - ReactHook/appendix
created: 2026-05-22
---
# 附录 E: 闭包专题——从 JavaScript 基础到 Hook 进阶

> **使用说明**：本附录是 Module 0 第 0.1 节的延伸和深化。当你遇到闭包相关的困惑（尤其是过期闭包）时随时查阅。不需要一次性读完，每次读一个小节。

---

## E.0 闭包的起源与设计动机——为什么需要闭包？

> 这一节回答的不是"闭包是什么"，而是"人们为什么要发明它"。理解动机比记住定义更重要。

### E.0.1 数学根源：λ 演算如何"推导"出闭包

==闭包==不是某个工程师拍脑袋设计的。它来自数学——具体说，来自阿隆佐·丘奇（Alonzo Church）在 1936 年提出的 **==λ 演算==**（Lambda Calculus）。要理解闭包的根源，需要理解 λ 演算试图解决什么问题。

#### 背景：数学的第三次危机与丘奇的动机

19 世纪末到 20 世纪初，数学界接连遭受重击：

**罗素悖论（1901）**。罗素构造了一个集合：*"所有不包含自身的集合的集合"*。这个集合包含自身吗？如果包含，按定义它不应该包含；如果不包含，按定义它又应该包含。一句话让集合论的地基崩裂——数学的基础语言有矛盾。

**希尔伯特计划（1920s）**。希尔伯特向整个数学界发出号召：把所有数学真理建立在一个**完全形式化、不存在矛盾**的公理系统上。如果成功，所有数学命题都可以用有限的机械规则去验证——数学将获得绝对确定性。

**哥德尔不完备定理（1931）**。哥德尔证明希尔伯特的目标不可能实现。任何足够强的形式系统，要么自相矛盾，要么存在"正确但永远无法被证明"的命题。确定性梦碎了一半。

但还有一锤子悬而未决。希尔伯特在 1928 年提出**判定问题**（Entscheidungsproblem）：

> 是否存在一个机械过程，能判定任意数学命题是否可证明？

要回答这个问题，首先得定义什么叫**"机械过程"**——什么能被算，什么不能被算。在 1930 年代，这个定义还不存在。

丘奇就是为了回答这个问题才搞出 λ 演算的。他的思路是：**废除"机器"概念，用纯数学的"函数"来定义"计算"**。一切计算本质上都是函数作用于函数——如果能用最简的函数语言表达所有可计算的东西，就抓住了"计算"的本质。

同一年（1936），图灵用完全不同的思路攻击同一个问题——他想象了一条无限长的纸带和一个在上面读写的机械头。图灵机是**物理直觉**（"人拿纸和笔能算什么"），λ 演算是**数学直觉**（"函数的组合能表达什么"）。

图灵在 1937 年证明了 λ 演算和图灵机**计算能力完全等价**。这就是**丘奇-图灵论题**的核心结果：λ 演算和图灵机是"可计算"这同一枚硬币的两面。

#### λ 演算的历史存续

这个纯粹为数学问题而生的系统没有被扔进档案馆。它活了下来，并且成了你每天写的 JavaScript 的祖先：

| 时间 | 事件 |
|------|------|
| 1936 | 丘奇发表 λ 演算，试图定义"可计算" |
| 1937 | 图灵证明 λ 演算纯计算部分与图灵机等价 |
| 1958 | John McCarthy 受 λ 演算启发，设计 **LISP**——第一个函数式编程语言。函数是一等公民、用 λ 做参数传递——全是 λ 演算的遗产 |
| 1975 | Guy Steele 和 Gerald Sussman 设计 **Scheme**（LISP 方言），采用==词法作用域== |
| 1995 | Brendan Eich 被要求"给浏览器写一个 Scheme"，最终做成了 **JavaScript**。JS 的函数模型（一等公民、词法作用域、闭包）直接来自 Scheme → LISP → λ 演算 |
| 2019 | React Hooks 发布。`useEffect`、`useCallback` 的闭包行为——根在 λ 演算的"函数携带定义时环境" |

丘奇搞 λ 演算不是为了闭包，也不是为了编程语言。他只是想回答"什么是可计算"这个纯数学问题。闭包是 λ 演算核心理念（词法作用域、函数是一等公民）在工程世界中一层层沉淀下来的结果。

#### λ 演算：只有三条规则的计算模型

λ 演算是一种极简语言，只有三条规则就能表达所有计算：

| 构造 | 写法 | 含义 |
|------|------|------|
| 变量 | `x` | 一个名字 |
| 抽象 | `λx.M` | 定义函数：参数是 x，函数体是 M |
| 应用 | `M N` | 调用函数 M，传入实参 N |

这就是全部。没有数字、没有加法、没有循环、没有对象——只有这三样，却能表达所有可计算的东西。数字、布尔值、条件、循环都是用函数模拟出来的。

用今天的 JavaScript 近似表达：

```javascript
// λx.M          ≈  (x) => M
// M N           ≈  M(N)

// 恒等函数: λx.x
const identity = (x) => x;

// 应用: (λx.x) 5
identity(5); // 5
```

#### 为什么一次只收一个参数？

你现在看到了 `(x) => (y) => x + y` 这种写法。直觉反应是：*多别扭——把 x 和 y 一起传不好吗？*

这个问题值得停下来仔细回答。它不只是一个语法偏好——它是闭包**为什么必然存在**的关键。

**不是"不想一起传"，是"不能"。** λ 演算的抽象规则只允许一个参数：

```
λ⟨单个变量⟩.⟨体⟩
```

不是丘奇嫌麻烦。构建数学系统有一条铁律：**原子越少越好，能用一个概念表达的东西绝不用两个。** 多参数 `λ(x, y).M` 需要引入"元组/积类型"——一个新概念，得额外定义规则。单参数 `λx.λy.M` 用已有的东西（函数返回函数）实现——零新概念。

所以 `λx.λy.x+y` 不是"分两次传参"。它是：**一个单参数函数，返回另一个单参数函数。** 这是两件独立的事：

```javascript
const add = (x) => {
  // x 在这个作用域中
  return (y) => {
    // 内部函数访问了外部的 x
    return x + y;
  };
};
```

内层函数引用了外层的 `x`。当 `add(5)` 返回内层函数时，这个内层函数**逃离了** `add` 的作用域。但它仍然需要 `x` 才能在将来被调用。于是它只能做一件事：**携带 `x = 5` 这个环境一起走。** 这就是闭包——不是刻意设计的功能，而是单参数嵌套这种编码方式的数学必然。

反过来想：如果 λ 演算原生支持多参数 `λ(x, y).x+y`：
- `add(5, 3)` 一步算完，没有"中间状态"
- 没有"内部函数被返回出去"这回事
- 没有携带环境的需求
- **没有闭包**

闭包之所以存在，是因为丘奇选择了"单参数 + 柯里化"作为表达多参数的方式。一旦函数可以返回函数，内层函数就可能在其创建环境之外被调用，它就必须记住回家的路——携带定义时的环境。

换一种说法：**闭包是柯里化的伴生物。有多参数转为单参数嵌套的需求，就必然有闭包。** 丘奇不是为了闭包而设计闭包——闭包是 λ 演算极简设计的一个"自然副作用"，然后被沿着 LISP → Scheme → JavaScript 一路继承下来，最后沉淀到了 React Hooks 中。

#### 插一句：柯里化是什么？

你可能注意到上文中好几次出现了"柯里化"这个词。它就是上面那个单参数 → 多参数的转化模式，值得明确一下。

**柯里化（Currying）**：把一个"一次收多个参数"的函数，转成"每次只收一个参数，返回一个等下一个参数的函数"的链。

名字来自 Haskell Curry——同一位 Curry 也是 Haskell 语言的命名来源。

```javascript
// ===== 普通版：一次传所有参数 =====
function normalAdd(x, y) {
  return x + y;
}
normalAdd(2, 3);              // 5 —— 一步到位

// ===== 柯里化版：每次只收一个参数 =====
function curriedAdd(x) {
  return function(y) {        // 返回一个"等待 y"的函数
    return x + y;             // x 被闭包携带
  };
}
curriedAdd(2)(3);             // 5 —— 分两步
//            ↑
//     两个括号——两次调用，每次一个参数
```

**柯里化的价值**不在"分步调用"本身，而在于**中间状态可以被保存、复用、传递**：

```javascript
// 冻住第一个参数，得到一个"特化版"函数
const add5 = curriedAdd(5);   // (y) => 5 + y —— 携带 x=5 的闭包
const add10 = curriedAdd(10); // (y) => 10 + y —— 携带 x=10 的闭包

add5(3);  // 8
add5(7);  // 12
add10(3); // 13

// add5 可以在不同时间、不同地方被调用
// 它自己"记住"了 x=5，不需要调用者再传
// 这整个机制——"记住创建时的参数供以后使用"——就是闭包
```

回到 λ 演算：丘奇用单参数 + 柯里化表达多参数，不是语法偏好，是唯一选择。这个选择触发了连锁反应：

```
λ 演算只有单参数
    → 多参数必须柯里化（嵌套返回函数）
    → 内层函数引用外层参数
    → 内层函数被返回 → 携带定义时环境
    → 闭包
```

**柯里化是这条链上"单参数模型"和"闭包"之间的桥梁。** 没有柯里化的需求，就没有嵌套返回函数；没有嵌套返回函数，就没有函数逃离定义环境；没有函数逃离，就不需要闭包。丘奇发明 λ 演算时想的不是柯里化也不是闭包——他想的是"可计算性"。但单参数 → 柯里化 → 闭包这条链，是 λ 演算不可拆分的整体——你可以视为同一个设计决策的三个面孔。

#### 关键问题：函数体内的 x 到底指什么？

考虑这个 λ 表达式：

```
(λx.λy.x) a b
```

一步一步来看这个表达式里发生了什么。`(λx.λy.x)` 是一个接收 `x` 并返回 `λy.x`（一个接收 y 但忽略 y 直接返回 x 的函数）的函数。计算过程：

```
(λx.λy.x) a b
= (λy.a) b        // 把 x 替换为 a。注意：λy 内部的 x 被替换成了 a
= a               // 把 y 替换为 b。但函数体里没有 y，所以直接返回 a
```

最终结果是 `a`——我们丢弃了 `b`，返回了第一个参数。这看起来很自然。但现在考虑一个**更微妙的表达式**：

```
(λx.λy.x) y
```

这里的 `y` 同时出现在两个位置：外层作为实参传入 `x`，内层通过 `λy` 绑定了另一个 `y`。按直觉：

```
(λx.λy.x) y
= λy.y           // 把 x 替换为 y？然后 λy 里原来的 x 变成了 y？
                 // 等等——λy 自己也绑定了一个参数叫 y
                 // 这两个 y 是同一个东西吗？
```

如果我们执行替换 `[y/x]`（把 x 替换为 y）：

```
(λx.λy.x) y
→ 把 x 替换为 y
→ λy.y          // 函数体 .x 变成 .y
```

但这里的 `λy.y` 的含义完全变了——它不再是"一个返回 x（第一个参数）的函数"，而变成了恒等函数 `λy.y`！因为外层的实参 `y` 和内层参数 `y` 发生了**名字冲突**。实参 `y` 被内层的参数绑定 `λy` **捕获**（capture）了。

这就是 λ 演算中的核心问题：**变量捕获（Variable Capture）**。

#### 自由变量与约束变量

为了精确描述这个问题，丘奇定义了：

- **约束变量（Bound Variable）**：在 `λx.M` 中，`M` 内部出现的 `x` 被 `λx` 这个抽象**约束**住了——它是"这个函数的参数"，不是外来的。
- **自由变量（Free Variable）**：函数体中出现但**没有被任何 λ 约束**的变量。它的含义由"函数定义时所在的外部环境"决定。

```javascript
// 看这个表达式：λx.(x y)

// x：约束变量——被 λx 约束
// y：自由变量——没有被任何 λ 约束，来自"外部"

// 翻译成 JS:
const fn = (x) => x + y;
// x 是参数（约束）
// y 来自外部作用域（自由）
```

#### 解决变量捕获：词法作用域

变量捕获问题（`(λx.λy.x) y` 中实参 `y` 被内层 `λy` 意外捕获）在数学上有两种解决思路：

| 方案 | 规则 | 代表语言 |
|------|------|----------|
| 动态作用域 | 变量指向**调用时**最近的同名绑定 | 早期 Lisp 方言、Bash |
| 词法作用域（静态作用域） | 变量指向**定义时**最近的同名绑定 | λ 演算、Scheme、JavaScript、几乎所有现代语言 |

丘奇在 λ 演算中选择了**词法作用域**：一个变量的含义，由阅读代码时看到的结构（"词法"）决定，而不是由运行时调用链（"动态"）决定。

这意味着：**嵌套函数中出现的自由变量，由包裹该函数的最内层 λ 绑定决定——也就是函数被"写下来"时所在的环境。**

这正是闭包的定义。丘奇没有"发明"闭包，他只是在定义 λ 演算的语义时，选择了词法作用域来避免变量捕获——而词法作用域自然要求每个函数"携带"定义时的环境。**闭包是词法作用域的必然实现方式，词法作用域是解决变量捕获问题的数学选择。**

#### 用 JavaScript 亲手验证两种作用域的区别

JavaScript 是词法作用域的（和 λ 演算一致）。没有内置的动态作用域，但我们可以手动模拟来对比：

```javascript
// 词法作用域（JavaScript 的真实行为，和 λ 演算一致）
function outer() {
  const x = 'outer 的 x';

  function inner() {
    console.log(x);     // x 是自由变量
  }

  return inner;
}

function caller() {
  const x = 'caller 的 x';  // 动态作用域会读这个
  const fn = outer();
  fn();                     // 输出 "outer 的 x"（词法作用域：读定义时的 x）
}

caller();
// 输出: "outer 的 x"（不是 "caller 的 x"）
// inner 在 outer 内部定义 → x 绑定到 outer 的 x
// 无论在哪里调用 inner，x 永远指向 outer 的 x
```

如果 JavaScript 是动态作用域，`inner` 被 `caller` 调用时，`x` 会先查调用者 `caller` 的作用域——输出 `"caller 的 x"`。这正是 `this` 在非箭头函数中的行为（`this` 是 JavaScript 中唯一接近动态作用域的机制）。

#### λ 演算 → 词法作用域 → 闭包 → JavaScript → React Hook 的完整链条

现在把所有环节串起来：

```
λ 演算中，丘奇为函数体中的自由变量选择了词法作用域
    → 自由变量的含义由定义时环境决定，不是调用时
    → 实现词法作用域的机制：函数必须"携带"定义时的环境
    → 函数 + 定义时环境 = 闭包
    → JavaScript 采用词法作用域 → JavaScript 天然有闭包
    → React 函数组件每次渲染被调用 → 新闭包 = 新"定义时环境"
    → useEffect/useCallback 等闭包捕获当前渲染的 props/state
    → deps 为 [] → 永远用第一次渲染的闭包 → 过期闭包 bug
```

每一步都不是偶然的。过期闭包的根源可以一路追溯到 1936 年丘奇在 λ 演算中选择词法作用域那一步。

#### 一个可以直接验证的 λ 演算 → Hook 映射

```javascript
// λ 演算层面：
// λcount.λonClick.(count)    —— 内层函数引用外层参数 count
// 应用: (λcount.λonClick.(count)) 0
// = λonClick.(0)             —— count 被替换为 0，然后闭包永远记住 0

// JavaScript 层面：
function Counter() {
  const [count, setCount] = useState(0);
  // count 是这个"λ 抽象"的参数

  useEffect(() => {
    console.log(count);
    // 这个回调是内层函数，count 是自由变量（被外层"约束"）
  }, []);
  // deps 为 [] → React 永远不重新计算这个 effect
  // → 闭包永远锁定 count = 0
  // → 等价于 λ 演算中的替换只发生一次
}
```

**核心洞察**：React 的 deps 数组本质上是在告诉 React"请重新做一次变量替换"。`[count]` = "每次 count 变化就重新做替换，让闭包捕获最新的 count"。`[]` = "只替换一次"——就像 `(λx.λy.x) 0` 只把 x 替换为 0 一次，之后永远如此。

### ⚡ 费曼检查 T0E

> 用你自己的话，向你身边一个没有数学背景的同事解释：
> 1. λ 演算中，"变量捕获"是什么问题？为什么需要词法作用域来解决它？
> 2. 这个词法作用域的选择，是怎么一路引向 React Hook 中的过期闭包 bug 的？
> 
> 要求：不许用"词法作用域"、"约束变量"、"自由变量"这些术语。只能讲故事和类比。

### E.0.2 工程动机一：用函数封装状态

没有闭包时，让一个函数"记住"私有状态极其麻烦。你的选择是：

**方案 A：全局变量（坏）**

```javascript
let count = 0;  // 全局污染
function increment() { return ++count; }
function decrement() { return --count; }
// 任何代码都能直接改 count，没有任何封装可言
```

**方案 B：面向对象（重）**

```javascript
class Counter {
  constructor() { this.count = 0; }
  increment() { return ++this.count; }
  decrement() { return --this.count; }
}
// 需要 new、this、构造函数、原型链——
// 只是为了让一个函数记住一个数字？
const c1 = new Counter();
const c2 = new Counter();
```

**方案 C：闭包（恰好）**

```javascript
function makeCounter() {
  let count = 0;                         // count 是私有的
  return {
    increment: () => ++count,           // 行为 + 状态打包在一起
    decrement: () => --count,
  };
}
// 没有 this，没有 class，没有 prototype
// count 对外界完全不可见——真正的封装
const c1 = makeCounter();
const c2 = makeCounter();
c1.increment(); // 1
c2.increment(); // 1 —— 各自独立
```

闭包在这里充当了**最轻量级的"有状态函数"**。`makeCounter` 每次调用创建一个独立的环境，返回的函数指向这个环境——天然隔离，天然封装。

**对 Hook 的启示**：这就是 `useState` 的模式原型。`makeCounter()` 对应组件函数的渲染调用，`count` 对应 state，返回的 `increment` 对应 `setState`。每次组件渲染创建新的环境，但 React 通过 Fiber 链表在多个环境之间搬运状态——保留闭包的封装优势，同时跨渲染保持状态。

### E.0.3 工程动机二：异步回调必须"记住"上下文

JavaScript 的核心交互模型是**事件驱动**——用户点击按钮、网络请求返回、定时器到点。你在"现在"注册一个回调，回调在"未来"执行。问题来了：**未来那一天，回调怎么知道现在是为什么被注册的？**

```javascript
// 想象一个没有闭包的世界——
// 你需要把"上下文"显式传递给每个回调：

function attachHandler(buttonId, context) {
  document.getElementById(buttonId)
    .addEventListener('click', function() {
      handleClick(context.userId, context.productId, context.page);
      // context 必须一层层手动传递
    });
}

// 有闭包的真实世界——
// 回调自己"记住"了当时的一切：

function attachHandler(buttonId, userId, productId) {
  const btn = document.getElementById(buttonId);
  btn.addEventListener('click', () => {
    addToCart(userId, productId);
    // userId 和 productId 被闭包自动携带——不需要 context 参数
  });
}
```

没有闭包，你需要在代码里维护一条从"注册点"到"执行点"的数据脐带。闭包让每个回调**自带记忆**——注册的那一刻，所有在作用域内的变量都被自动"保存"下来，在未来的执行时可用。

**对 Hook 的启示**：`useEffect`、`useCallback`、事件处理函数——每个都是"在渲染时注册、在未来执行"的回调。闭包让它们自动记住当前渲染的 props 和 state 值。这也解释了为什么 **deps 是 `[]` 时会出现过期闭包**——因为你告诉 React"永远用第一次注册的版本"，那当然就只能读到第一次渲染时的值。

### E.0.4 工程动机三：用闭包模拟"私有"，而不是靠语言特性

JavaScript 长期没有原生的私有字段（直到 ES2022 的 `#` 语法）。在很长一段时间里，闭包是创建**真正私有**变量的唯一方式：

```javascript
// 闭包实现真正私有
function createBankAccount(initialBalance) {
  let balance = initialBalance;        // 外界完全无法访问
  return {
    deposit: (amount) => { balance += amount; },
    getBalance: () => balance,
  };
}

const account = createBankAccount(1000);
account.deposit(500);
console.log(account.getBalance()); // 1500
console.log(account.balance);      // undefined —— 完全访问不到

// 对比：即使是用 Symbol 或 WeakMap，
// 仍然可以通过 Object.getOwnPropertySymbols 等方式访问到
// 闭包是唯一做到"物理不可访问"的封装方式
```

**对 Hook 的启示**：自定义 Hook 同理——Hook 内部的 `useState`、`useRef` 对外界是不可见的。外界只能通过 Hook 返回的值和方法来操作。这就是"有状态逻辑的封装"。一个 `useAuth()` 内部有三个 `useState` 和一个 `useEffect`，但使用它的组件不知道也不关心——组件只看到 `{ user, login, logout }`。

### E.0.5 三条动机的汇总

| 动机 | 要解决的问题 | 对应 Hook 概念 |
|------|------------|-------------|
| λ 演算 | 函数怎么绑定自由变量？ | 每次渲染 = 一个 λ 环境 |
| 封装状态 | 怎么用函数记住私有数据？ | `useState` = 闭包封装的升级版 |
| 异步回调记忆 | 未来的回调怎么记住现在的上下文？ | `useEffect`/`useCallback` = 携带渲染快照的回调 |
| 真正的私有 | 怎么防止外部代码修改内部数据？ | 自定义 Hook 对调用方隐藏内部 Hook |

### ⚡ 费曼检查 T0E

> 给你的同事解释：为什么 JavaScript 需要闭包？用三个具体的工程场景（不要只说"封装"这个词，要说出具体封装了什么）。

---

## E.1 闭包的定义——从三个方面理解

### 技术定义

> 闭包是一个函数与其词法环境的组合。这个函数可以访问在其创建时作用域内的变量，即使创建它的函数已经执行完毕。

### 运行时视角

```javascript
function outer(x) {
  const y = 10;
  function inner() {
    console.log(x + y);
  }
  return inner;
}

const fn = outer(5);
// outer 已经执行完毕。
// x 和 y 应该被销毁了。
// 但——

fn(); // 15！闭包让 inner 仍然能访问 x 和 y
```

JavaScript 引擎在执行 `outer(5)` 时，发现 `inner` 引用了 `x` 和 `y`。所以即使 `outer` 返回了，引擎也不会释放这些变量。它们被保存在一个叫 **[[Environment]]**（或 **[[Scopes]]**）的内部属性中。

### 内存视角

```
outer(5) 调用：
  ┌─────────────────────┐
  │ 执行上下文（已销毁） │
  │   x = 5             │ ← 但 inner.[[Scopes]] 仍引用它
  │   y = 10            │ ← 所以引擎不回收
  │   inner 函数──────────→ 被返回给外部变量 fn
  └─────────────────────┘

fn 存在 → inner 存在 → inner.[[Scopes]] 引用 outer 的变量 → 变量不会被 GC
fn = null → inner 可被 GC → outer 的变量也可被 GC → 闭包释放
```

### ⚡ 费曼检查 T1

> 用你自己的话解释：闭包在内存中是怎么"存活"的？为什么垃圾回收器无法回收闭包中引用的变量？

---

## E.2 闭包的三个关键机制

### 机制一：捕获变量，不是值

这是整个 React Hook 闭包问题的根源。

```javascript
function demo() {
  let value = 0;

  const getValue = () => value;     // 返回当前值
  const setValue = (v) => { value = v; };

  console.log(getValue());          // 0
  setValue(42);
  console.log(getValue());          // 42 —— getValue 读到了变化后的值！
}

demo();
```

`getValue` 不拥有 `value` 的一份"快照"。它拥有一条**通往 `value` 所在内存地址的活链接**。

**Hook 的含义**：每次 React 渲染都创建了一个新闭包，捕获了当前渲染的 state。如果你用 `[]` 作为 deps，就永远用第一次渲染的闭包——读到的是第一次渲染的 state 值。

### 机制二：每次函数调用创建独立的闭包

```javascript
function createPrinter(name) {
  return () => console.log(name);
}

const p1 = createPrinter('Alice');
const p2 = createPrinter('Bob');

p1(); // "Alice"
p2(); // "Bob"
// p1 和 p2 是两个独立闭包，各自有各自的 name
```

**Hook 的含义**：每次渲染都是一次"函数调用"——每次都创建新的闭包。这正是 Hook 能工作的基础，也是过期闭包的来源。

### 机制三：内部函数可以修改外部变量

```javascript
function createSharedCounter() {
  let count = 0;
  return {
    increment: () => { count++; },
    get: () => count,
  };
}

const counter = createSharedCounter();
counter.increment();
counter.increment();
console.log(counter.get()); // 2
```

多个内部函数共享同一个外部变量。它们之间通过闭包通信——这就是 `useState` 返回的 `[value, setValue]` 模式的原型。

---

## E.3 作用域链与闭包

闭包之所以能访问外部变量，是因为 JavaScript 的==作用域链==机制：

```javascript
const globalVar = 'global';

function outer() {
  const outerVar = 'outer';

  function middle() {
    const middleVar = 'middle';

    function inner() {
      const innerVar = 'inner';
      console.log(innerVar);    // 自己的作用域
      console.log(middleVar);    // 上级作用域（闭包）
      console.log(outerVar);     // 上上级作用域（闭包）
      console.log(globalVar);    // 全局作用域
    }

    return inner;
  }

  return middle();
}

const fn = outer();
fn(); // 依次输出 inner, middle, outer, global
```

**作用域链的查找顺序**：自己的作用域 → 上一层作用域 → 再上一层 → ... → 全局作用域。

当引擎在 `inner` 内部找不到 `middleVar` 时，它沿着作用域链向上查找——在 `middle` 的作用域中找到了。这就是闭包让你"穿越"函数边界访问变量的方式。

### 练习 E1：追踪作用域链

下面代码的输出是什么？画处作用域链的查找路径。

```javascript
let x = 1;

function outer() {
  let x = 2;
  function inner() {
    let x = 3;
    return x;
  }
  return inner;
}

const fn = outer();
console.log(fn()); // ?
```

（答案：`3`。`inner` 自己的作用域里有 `x = 3`，不需要往上找。）

---

## E.4 闭包的经典陷阱及其在 React 中的表现

### 陷阱一：循环中的闭包（经典版）

前面 0.1.4 已经详述。核心结论：**`var` 共享变量，`let` 每次迭代创建新变量。**

### 陷阱二：异步回调中的闭包（Hook 版）

```javascript
function SearchComponent() {
  const [query, setQuery] = useState('');

  const handleSearch = () => {
    // 这是正确的——handleSearch 每次渲染都是新的闭包，
    // 捕获的是当前渲染的 query 值
    fetchResults(query);
  };

  // 但这里有问题：
  useEffect(() => {
    const id = setTimeout(() => {
      // 如果 deps 是 []，这个回调捕获的是第一次渲染的 query
      sendAnalytics(query);
    }, 3000);
    return () => clearTimeout(id);
  }, []); // ← bug!

  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

**诊断**：`setTimeout` 的回调形成了一个闭包，捕获了 `query`。如果 deps 是 `[]`，它永远不会重新创建，`query` 永远是初始值。

**修复**：把 `query` 加入 deps，或用 `useRef` 中转。

### 陷阱三：事件监听器中的闭包

这也是 Module 4 中 `useEventListener` 为什么需要 `savedHandler` 的原因。

```javascript
function Modal() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        // 如果 deps 是 []，这个闭包永远看到 isOpen = false
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []); // ← 如果这里不加 isOpen，handleKeyDown 里的 isOpen 是旧值
}
```

**修复**：

| 场景 | 修复方式 |
|------|----------|
| 只需要 setState | `setIsOpen(false)` 不受影响——setState 函数引用本身是稳定的 |
| 需要读值 | `setIsOpen(prev => !prev)` 用==函数式更新== |
| 需要读值且不能函数式更新 | 用 `useRef` 保存最新值 |

---

## E.5 闭包与 React 渲染模型的深度映射

### 每一次渲染都是一次全新的闭包世界

```jsx
function Profile({ userId }) {
  const [user, setUser] = useState(null);

  // 渲染 #1: userId = 1, user = null
  //   → 下面的所有函数都捕获 { userId: 1, user: null }
  //   → 它们形成了一个"闭包快照"

  // 渲染 #2: userId = 2, user = null
  //   → 所有函数重新创建，捕获 { userId: 2, user: null }
  //   → 这是一套全新的闭包

  useEffect(() => {
    fetchUser(userId).then(setUser);
    // 渲染 #1: 捕获 userId = 1 → 请求 user 1
    // 渲染 #2: 捕获 userId = 2 → 请求 user 2
    // 如果渲染 #1 的请求在渲染 #2 之后返回 →
    // 竞态条件！（Module 4 有详解）
  }, [userId]);

  const handleSave = () => {
    // 渲染 #1: 捕获 user = null → 保存 null（bug！）
    // 渲染 #2: 捕获 user = { id: 2, name: 'Bob' } → 保存 Bob（正确）
    saveUser(user);
  };

  return <button onClick={handleSave}>保存</button>;
}
```

### 关键表格：什么在每次渲染时变化？

| 东西 | 每次渲染？ | 说明 |
|------|----------|------|
| props 和 state 值 | 可能变化 | 新渲染有新的值 |
| 组件函数内部创建的所有函数 | **全部重新创建** | `() => {}` 每次都是新引用 |
| `useRef` 返回的对象 | **不变化** | 同一个对象，`.current` 可读写 |
| `useState` 返回的 setter | **不变化** | React 保证 setState 引用稳定 |
| `useReducer` 返回的 dispatch | **不变化** | React 保证 dispatch 引用稳定 |
| `useEffect` 的回调（如果 deps 未变） | **不变化** | React 复用上次的回调 |
| `useCallback` 返回的函数（如果 deps 未变） | **不变化** | 返回上次缓存的函数 |
| `useMemo` 返回的值（如果 deps 未变） | **不变化** | 返回上次缓存的值 |

理解这个表格，闭包 Bug 的原因就一目了然：
- **不变化的东西读取变化的东西** → ==过期闭包==
- **变化的东西依赖不变化的东西** → 没问题

---

## E.6 闭包诊断——五步定位法

当你怀疑一个 Hook Bug 和闭包有关时，按这个流程诊断：

### Step 1: 确定"它读到了旧值"

```javascript
// 添加诊断日志
useEffect(() => {
  console.log('Effect 执行时 count =', count);
}, [count]);
```

### Step 2: 确定"读取动作在哪个闭包中"

```javascript
// 是 useEffect 的回调？
// 是 useCallback 的回调？
// 是 setTimeout/setInterval 的回调？
// 是 addEventListener 的回调？
```

### Step 3: 确定"这个闭包多久创建一次"

```javascript
// 看 deps 数组：
// [] → 只创建一次 → 闭包永远是第一次的值
// [count] → 每次 count 变化都重新创建 → 闭包是最新的
// 无 deps → 每次渲染都重新创建 → 闭包是最新的
```

### Step 4: 选择修复策略

```javascript
// 优先级：
// A. 函数式更新（如果可以） → setState(prev => ...)
// B. 加入 deps（如果可以接受重新创建） → [count]
// C. useRef 中转（如果需要保持引用稳定） → ref.current = value
```

### Step 5: 验证

```javascript
// 确认修复后，值和预期一致
useEffect(() => {
  console.log('修复后 count =', count);  // 应该是当前值
}, [count]);
```

---

## E.7 练习

### 练习 E2：诊断这个 Hook 的闭包问题

```javascript
function useDelayedAlert(message, delay) {
  useEffect(() => {
    const timer = setTimeout(() => {
      alert(message);
    }, delay);
    return () => clearTimeout(timer);
  }, []); // ← 有 bug

  // 这个 Hook 有什么问题？
  // 用户传入不同的 message 时，alert 会显示什么？
  // 怎么修复？
}
```

### 练习 E3：闭包与 useCallback

```javascript
function Parent() {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    console.log(count);
  }, []); // ← 有 bug

  return <Child onClick={handleClick} />;
}
```

`handleClick` 中的 `count` 是什么值？为什么？

### 练习 E4：设计无闭包 Bug 的 Hook

设计 `useInterval(callback, delay)`，要求：
1. `callback` 始终能读到最新 state
2. `delay` 变化时重启 interval
3. `delay` 不变化时 interval 不重启
4. 组件卸载时清理 interval

用你学到的三种闭包修复策略之一（或组合）完成。

---

## E.8 闭包速查表

| 概念 | 一句话 | Hook 中的表现 |
|------|--------|-------------|
| 闭包定义 | 函数 + 它能访问的外部变量 | 每个渲染创建一个闭包 |
| 捕获变量不是值 | 闭包持有变量引用 | deps `[]` → 旧闭包 → 旧值 |
| 每次调用新闭包 | 每次函数调用创建独立作用域 | 每次渲染是新闭包 |
| 作用域链 | 内层能访问外层变量 | 组件函数内所有 Hook 共享作用域 |
| ==垃圾回收== | 闭包引用阻止变量回收 | 组件卸载 → Fiber 释放 → 闭包释放 |
| var vs let | var 共享，let 每次迭代新建 | ==useRef==(始终同一对象) vs useState(每次新值) |
| IIFE | 立即执行创建隔离作用域 | 类似 useRef 手动做作用域隔离 |

---

## E.9 延伸阅读

- **Module 0, 0.1 节**：闭包与 Hook 的入门关系
- **Module 5, 5.1 节**：过期闭包的完整修复指南
- **Module 4, 4.2 节**：`useEventListener` 中闭包处理 —— `savedHandler` 模式
- **Module 4, 4.5 节**：`useInterval` 中闭包处理 —— Dan Abramov 的经典实现
- **附录 B**：所有 Hook 和模式的快速参考

---

**当你发现自己想不明白"为什么这个值不对"时，回到这里走一遍五步诊断法。**
