---
tags:
  - ReAct系统学习
  - 概念/agent-architecture
created: 2026-05-26
status: in-progress
---

# ReAct 的本质

## 从两个失败案例出发

### 案例一：Chain-of-Thought 的盲区

CoT 让模型"一步一步想"。面对"2023 年奥斯卡最佳影片的导演是谁？"这个问题，模型写出漂亮的推理链："首先我需要回忆 2023 年的奥斯卡获奖影片，我记得是 Everything Everywhere All at Once，导演是 Daniel Kwan 和 Daniel Scheinert。"

完全合理。唯一的问题是：==模型的知识截止于 2022 年初，2023 年的奥斯卡它根本没见过==。推理链看起来无懈可击，但结论是编的。

CoT 解决的是"模型不擅长推理"的问题，但它解决的只是**内部推理**。当推理需要外部信息时——事实查询、数据验证、实时状态——CoT 不仅帮不上忙，还会产生看起来更有说服力的幻觉。

### 案例二：纯 Act 的短视

另一个极端：模型只输出 Action，不输出 Thought。"查询 2023 年奥斯卡最佳影片。""查询该片的导演。"——每一步都精准，但为什么选择了查奥斯卡而不是查 IMDb 年度榜单？为什么只查了 2023 年而不是 2022-2024 三年的数据来对比？纯 Act 模型不告诉你它的策略，你也无从判断它是深思熟虑还是随机碰运气。

> CoT 的缺陷是**只推理不行动**——信息不足时硬猜。纯 Act 的缺陷是**只行动不推理**——缺乏高层次的计划、无法动态调整策略。

## ReAct 的核心洞察

Yao et al. (2022) 的发现可以用一句话概括：

==Thought 和 Action 不是两种独立的模式，而是一个反馈回路的两个半周期。==

- **Thought → Action**：推理缩小了行动空间。模型在 Thought 中决定"我需要查天气数据"，然后 Action 只做这一件事，不会随机地调用 delete_database。
- **Action → Thought**：行动提供了推理的锚点。模型执行搜索后看到返回结果，Thought 基于真实数据重新推理，而不是凭空猜测。

把这个反馈回路画出来：

```
Thought₁: "需要查 2023 年奥斯卡获奖影片"
    → Action₁: Search("2023 Oscar Best Picture winner")
    → Observation₁: "Everything Everywhere All at Once"

Thought₂: "EEAAO 获奖了，现在需要查导演。也可能有多个导演。"
    → Action₂: Lookup("Everything Everywhere All at Once directors")
    → Observation₂: "Daniel Kwan and Daniel Scheinert (The Daniels)"

Thought₃: "信息足够，可以回答了。"
    → Final Answer: "2023 年奥斯卡最佳影片是《瞬息全宇宙》，导演是关家永和丹尼尔·施纳特。"
```

关键点是 Thought₂——模型基于 Observation₁ 调整了策略。它不是提前规划好的，而是在每一步根据新信息重新推理。

## 为什么这个反馈回路有效

从信息论的角度，ReAct 的每次循环都在做一件事：==用外部信息降低内部推理的不确定性==。

1. 模型内部状态是一个高维概率分布，关于"2023 年奥斯卡是哪部电影"这个问题，分布在多部候选影片上
2. 执行 Search Action 后，Observation 提供了外部信息——这个信息以接近 1.0 的概率将 EEAAO 确定为正确答案
3. 模型将此外部信息纳入内部状态，概率分布坍缩，后续推理的确定性大幅提升

> ReAct 不是让模型"更聪明"，而是让模型**不再依赖它不确定的内部知识**。不确定的时候，查一下。

## ReAct 与 Function Calling 的关系

这是本系列与 [Function Calling 系统学习](../FunctionCalling系统学习/0-模块索引.md) 交叉的核心点。

ReAct 是**决策框架**——定义"什么时候该想，什么时候该做，想什么，做什么"。Function Calling 是**执行机制**——定义"如何结构化地表达'做什么'"。

两者是正交的：

| | 思考 | 行动 |
|---|---|---|
| **ReAct（决策层）** | Thought 文本 | Action 文本 |
| **Function Calling（执行层）** | — | tool_calls JSON |

在 2022 年的原始 ReAct 论文中，Action 是自由文本，需要用正则解析。在 2025+ 的实际实现中，Action 步骤直接对接 Function Calling——模型输出 `tool_calls` 而非 `Action: Search[xxx]`。

> 理解这个分层是关键：Function Calling 给了你可靠的 Action 执行机制，但它不告诉你**什么时候该调用、如何根据结果调整策略**——这些是 ReAct 提供的。

## 思考题

1. ReAct 的反馈回路依赖 Observation 的质量。如果 Search 返回了错误结果（比如搜索引擎把 2022 年的结果排在了前面），模型在 Thought₂ 中会如何处理？它有可能自己纠正吗？什么条件下能纠正，什么条件下不能？
2. ReAct 每步都需要一次 LLM 调用（Thought 生成）和一次工具执行（Action）。对于一个需要 5 步的任务，这至少是 10 次串行操作。有没有可能并行化某些步骤？代价是什么？
3. CoT 解决内部推理，Function Calling 解决外部行动，ReAct 把两者连接起来。这三者之间还存在什么"空缺"是现有架构没有填补的？
