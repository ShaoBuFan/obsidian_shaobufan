---
tags:
  - RAG系统学习
  - 论文精读
  - 论文/selfrag
  - 概念/AgenticRAG
created: 2026-05-26
paper: asai2023
---

# Self-RAG · Learning to Retrieve, Generate, and Critique through Self-Reflection

Asai et al. (University of Washington / Allen AI), ICLR 2024. Agentic RAG 的里程碑。

## 核心问题

传统 RAG 有两个根深蒂固的假设：（1）**每个查询都需要检索**——实际上很多查询不需要（闲聊、常识推理、模型已知的知识）；（2）**检索结果总是有用的**——实际上检索可能返回不相关甚至误导性的内容。LLM 有没有能力自己决定**何时检索、怎么用检索结果、什么时候该重新检索**？

## 方法

训练 LLM 生成特殊的 ==reflection token==——在生成过程中穿插的元标签，控制检索和验证行为：

| Token | 含义 |
|-------|------|
| `<Retrieve>` | 需要检索 |
| `<NoRetrieve>` | 不需要检索，直接回答 |
| `<Relevant>` | 检索段落相关，可以使用 |
| `<Irrelevant>` | 检索段落不相关 |
| `<Cite>` | 接下来的陈述引用来源 |
| `<NoCite>` | 接下来的陈述不需要引用（常识） |

**推理流程：**
```
输入: "什么是DPR？"
    → 生成 <Retrieve>                    ← 判断：需要检索
    → 检索: 返回5个段落
    → 对每个段落生成 <Relevant> 或 <Irrelevant>
    → 对相关段落生成 <Cite> + 答案片段
    → 对不需要引用的部分生成 <NoCite> + 补充说明
    → 输出完整答案
```

**训练方式：**

Self-RAG 的训练数据构造很巧妙——
1. 用 GPT-4 对已有 QA 数据集自动标注 reflection token（哪个检索段落相关、哪句需要引用）
2. 用标注数据训练一个 critic 模型（判断检索质量）
3. 用标注数据 + critic 评分联合训练 generator

> 关键创新不是 reflection token 本身——是**用 GPT-4 自动构造训练数据**绕过了手工标注 reflection token 的瓶颈。

## 关键实验

- 在六个数集上全面优于标准 RAG（检索-拼接-生成）
- 幻觉率显著降低：Self-RAG 的 Faithfulness 指标比标准 RAG 提高了约 10%
- `<NoRetrieve>` 的使用率：约 30-40% 的输入不需要检索——这意味着标准 RAG 在这些输入上做了不必要的检索，无谓地增加了延迟和成本
- Critic 模型的效果：用 critic 过滤掉不相关的检索段落后，答案质量提升明显

## 优势与局限

**优势：**
- 首次把"when to retrieve"和"how to use"统一到端到端训练中
- 显式的 reflection token 使决策过程可解释——你能看到模型为什么决定检索或不检索
- 自动训练数据构造方法降低了推广到新领域的成本

**局限：**
- 需要 fine-tune LLM——不能即插即用到任意预训练模型上。对于 Claude API 用户来说不可行（无法 fine-tune）
- Reflection token 的生成可能不稳定——在某些输入上可能生成错误的 `<Relevant>` 判断
- 实验集中在英文 QA 数据集，中文场景和多语言混合场景未充分评估

## 对本项目的启发

1. **你的向量记忆库已经部分实现了 Self-RAG 的理念**：Claude Code 作为 Agent 框架，当 MCP `search_notes` 注册后，Claude 自己就能判断"我需要检索笔记吗"——这就是 `<Retrieve>` 和 `<NoRetrieve>` 的效果。区别在于 Claude 的判断基于自身推理而非显式 fine-tune 的 reflection token。

2. **检索质量判断是缺失环节**：Self-RAG 有一个 critic 步骤判断检索结果好不好。你的向量记忆库缺这个——检索到的 5 个 chunk 质量好不好，目前没有自动判断机制。==复合评分的四维公式可以充当轻量级的 critic==——如果重排后分数最高的 chunk 仍然低于某个阈值，可能意味着检索质量差。

3. **不需要检索的情况比你想象的多**：Self-RAG 的 30-40% `<NoRetrieve>` 比率是一个有用的锚点。在你的场景中，如果 Claude 已经有足够的知识回答（比如解释"什么是 RAG"），强制检索可能反而干扰。

---

*关联笔记：[Agentic RAG](../4-进阶专题/2-AgenticRAG.md) | [重排序](../2-索引与检索/7-重排序.md) | [RAG 评估维度与指标](../3-生成与评估/4-RAG评估维度与指标.md)*
