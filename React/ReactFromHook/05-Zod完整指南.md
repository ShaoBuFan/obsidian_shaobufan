---
tags:
  - React
  - Zod
  - TypeScript
  - schema
  - 类型推导
  - discriminatedUnion
created: 2026-05-22
---

# 第五章：Zod 完整指南

> [上一章](04-当表单长大以后.md)我们引入了 Zod，但只用了它的表层。Zod 本身是一个强大的 TypeScript 运行时校验库——理解它的完整心智模型，能让你在面对任何校验需求时独立设计出干净、类型安全的方案。本章深入 Zod 的全部核心能力。

---

## 5.1 第一性原理：为什么需要 Zod

### TypeScript 做不到的事

```typescript
interface User {
  name: string;
  age: number;
  email: string;
}

function createUser(data: User) {
  // data 真的符合 User 吗？TypeScript 说"是"——但只在编译时
  console.log(data.name.toUpperCase()); // 如果 data.name 是 null？运行时直接 crash
}
```

TypeScript 的类型只在**编译时**存在。代码跑起来之后，类型就消失了——没人帮你检查 `data.name` 到底是不是 string。

打个比方：TypeScript 的类型是**建筑蓝图**——它告诉你房子应该盖成什么样，但工人可能走样。你需要一面**墙**——在运行时挡住不合规的数据。==Zod 就是这面墙。==

### 单一真相来源

```typescript
// TypeScript：编译时存在，运行时消失
interface User { name: string; age: number; }

// Zod：编译时在（类型推导），运行时也在（校验执行）
const UserSchema = z.object({ name: z.string(), age: z.number() });
type User = z.infer<typeof UserSchema>; // 自动推导，不用写第二遍
```

> Zod 的核心理念是 ==Single Source of Truth（单一真相来源）==：你定义一次 schema，同时得到 TypeScript 类型和运行时校验——不需要在两个地方维护两套东西。关于这个原则的深入讨论，见 [附录](10-附录-常见问题.md#a6-drysostsoc-三者怎么配合)。

---

## 5.2 基础类型

### 字符串

```typescript
z.string()                              // 任意字符串
z.string().min(2)                       // 最少 2 个字符
z.string().max(50)                      // 最多 50 个字符
z.string().email()                      // 邮箱格式
z.string().url()                        // URL 格式
z.string().uuid()                       // UUID
z.string().regex(/^\d+$/)               // 自定义正则
z.string().startsWith('CN-')            // 前缀
z.string().endsWith('.com')             // 后缀
z.string().trim()                       // 自动去首尾空格（transform）
z.string().toLowerCase()                // 转小写（transform）
```

### 数字

```typescript
z.number()                              // 任意数字
z.number().int()                        // 整数
z.number().positive()                   // 正数（>0）
z.number().nonnegative()                // 非负数（>=0）
z.number().min(0).max(100)              // 范围
z.number().multipleOf(5)                // 能被 5 整除
z.number().finite()                     // 有限数（非 Infinity/NaN）
```

### 其他基础

```typescript
z.boolean()                             // true / false
z.date()                                // Date 对象
z.literal('hello')                      // 只能是 'hello' 这个具体值——精确匹配
z.enum(['admin', 'user', 'guest'])      // 只能是这三者之一
z.nativeEnum(MyEnum)                    // TypeScript enum
z.undefined()                           // undefined
z.null()                                // null
z.any()                                 // 任意类型，跳过校验（慎用）
z.unknown()                             // 任意类型，但要求你显式处理
z.void()                                // 接受 undefined
z.never()                               // 永不通过校验——你永远不想用到它
```

---

## 5.3 复合类型

### 对象

```typescript
const PersonSchema = z.object({
  name: z.string(),
  age: z.number(),
});

// .shape 访问子 schema——方便复用
const NameSchema = PersonSchema.shape.name;

// .extend() 扩展现有 schema——不修改原 schema
const EmployeeSchema = PersonSchema.extend({
  employeeId: z.string(),
});
```

### 数组

```typescript
z.array(z.string())                     // string[]
z.string().array()                      // 等效写法

z.array(z.string()).min(1)              // 至少 1 个元素
z.array(z.string()).max(10)             // 最多 10 个
z.array(z.string()).nonempty()          // 不能是空数组
```

### 元组

```typescript
z.tuple([z.string(), z.number()])       // [string, number]——固定长度，每位置独立类型
```

### 联合（Union）——"或"

```typescript
z.union([z.string(), z.number()])       // string | number
z.string().or(z.number())               // 等效简写
```

### Record 和 Map

```typescript
z.record(z.string())                    // { [key: string]: string }
z.record(z.string(), z.number())        // { [key: string]: number }
z.map(z.string(), z.number())           // Map<string, number>
z.set(z.string())                       // Set<string>
```

---

## 5.4 修饰符：可选、可空、默认值

```typescript
z.string().optional()                   // string | undefined
z.string().nullable()                   // string | null
z.string().nullish()                    // string | null | undefined——等于 .optional().nullable()

z.string().default('未设置')            // undefined 时自动填入默认值

const schema = z.object({
  theme: z.enum(['light', 'dark']).default('light'),
});
// parse({}) → { theme: 'light' }
```

### catch：校验失败时的备选值

```typescript
z.string().catch('默认值')              // 校验失败也不报错，用备选值
z.number().catch(0)
```

---

## 5.5 转换（Transform）：校验 + 修改

Zod 不仅能**检查**值，还能**处理**值。这是它区别于纯校验库的关键能力。

### 基础 transform

```typescript
const NumberFromString = z.string().transform((val, ctx) => {
  const parsed = Number(val);
  if (isNaN(parsed)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: '无法转换为数字',
    });
    return z.NEVER; // 终止处理
  }
  return parsed;
});

NumberFromString.parse('42');   // → 42 (number)
NumberFromString.parse('abc');  // → 抛出 ZodError
```

### coerce：强制类型转换

```typescript
// coerce 是 transform 的快捷语法糖
z.coerce.number()                      // 把 '42' → 42
z.coerce.boolean()                     // 把 'true' → true
z.coerce.date()                        // 把 ISO 字符串 → Date
z.coerce.string()                      // 把数字/布尔 → 字符串
z.coerce.bigint()                      // 把字符串/数字 → BigInt
```

`coerce` 的本质是在 schema 校验**之前**做一次预处理。等效于：

```typescript
z.preprocess((val) => {
  if (typeof val === 'string') return Number(val);
  return val;
}, z.number());
```

### 管道的实际用法

```typescript
// 用户输入可能是字符串 '123'，但你需要数字
const userIdSchema = z
  .string()
  .regex(/^\d+$/, '必须全是数字')
  .transform(Number)
  .pipe(z.number().int().positive());
```

---

## 5.6 判别联合：条件校验的最佳方式

很多表单的校验规则**取决于另一个字段的值**。比如"通知方式"选短信时手机号必填，选邮件时邮箱必填：

```typescript
const NotificationSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('sms'),
    phone: z.string().regex(/^1\d{10}$/, '手机号格式不对'),
  }),
  z.object({
    type: z.literal('email'),
    email: z.string().email(),
  }),
]);

type Notification = z.infer<typeof NotificationSchema>;
// TypeScript 自动收窄：type === 'sms' → 一定有 phone；type === 'email' → 一定有 email
```

==Discriminated Union（判别联合）==利用一个字面量字段（discriminator）区分分支。Zod 先读 discriminator 的值，然后只执行匹配分支的校验规则。TypeScript 也同步收窄类型——这是 Zod 和 TypeScript 配合得最好的地方。

如果没有 `discriminatedUnion`，你需要把所有字段都设为 optional，然后用 `superRefine` 手动写条件逻辑——代码量翻倍，类型收窄失效。

---

## 5.7 类型推导：从 Schema 到 TypeScript

### z.infer

```typescript
const UserSchema = z.object({
  name: z.string(),
  age: z.number().optional(),
});

type User = z.infer<typeof UserSchema>;
// { name: string; age?: number }
```

### z.input vs z.output：当有 transform 时

```typescript
const schema = z.object({
  age: z.coerce.number(), // transform 会把字符串转成数字
});

type Input = z.input<typeof schema>;
// { age: string | number }  — 原始输入可以是字符串

type Output = z.output<typeof schema>;
// { age: number }           — transform 之后一定是数字
```

在 react-hook-form 中使用时，`useForm<z.infer<typeof schema>>` 推导的是 **output 类型**——也就是校验通过后的数据类型。这正是你 `onSubmit` 里收到的。

---

## 5.8 在 react-hook-form 中的完整对接

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// 1. 定义 schema——可以放在独立文件（schemas.ts）
const schema = z.object({
  name: z.string().min(2).max(20),
  age: z.coerce.number().min(1).max(150),
});

// 2. 类型自动跟上
type FormData = z.infer<typeof schema>;

// 3. 使用
const form = useForm<FormData>({
  resolver: zodResolver(schema),
});
```

**这就是"单一真相来源"**——你定义了 `schema`，拿到了三样东西：校验规则、TypeScript 类型、运行时错误消息。register 里不需要再写一遍规则。这三个东西**永远同步**——改 schema，类型自动更新，错误消息自动更新，不会有"类型改了但校验没改"的 bug。

---

## 本章要点

- TypeScript 类型只在编译时存在；Zod 让校验在**运行时**也生效
- `z.infer<typeof schema>` 从 schema 推导类型——==定义一次，类型和校验永不分离==
- 基础类型自带丰富校验方法；复合类型（object、array、union）覆盖所有数据结构
- `optional()`、`nullable()`、`default()` 处理缺失值和空值
- `transform` 和 `coerce` 做类型转换——把字符串变成数字，把 ISO 字符串变成 Date
- `discriminatedUnion` 让条件校验的类型窄化自然、类型安全
- `z.input` vs `z.output` 区分 transform 前后的类型差异

## 思考题

1. `z.coerce.number()` 把空字符串 `""` 转成了 `0`。这是合理的默认行为吗？如果你希望空字符串算校验失败，怎么写？
2. `discriminatedUnion` 要求 discriminator 字段是 literal 类型。如果 discriminator 是动态的（比如从 API 配置里读的），这个模式还能用吗？如果不能，替代方案是什么？
3. Zod 的 `.default()` 和 `.catch()` 有什么区别？在 react-hook-form 的上下文中，什么时候用哪个？
