# SUMMARY — 研究总览

> 对《A Philosophy of Software Design》(2nd ed.) 的持续精读研究。
> 研究开始：2026-05-18
> 当前轮次：第 6 轮完成

---

## 研究产出总表

| 文件 | 内容规模 | 关键内容 |
|------|---------|---------|
| `DEEP_NOTES.md` | ~15,000 字 | 22章+前言完整分析 |
| `CASE_STUDIES.md` | ~5,500 字 | 11 个详细案例 |
| `PHILOSOPHY_MAP.md` | ~7,000 字 | 概念网络 + 14 种设计思想比较 |
| `CONTRADICTIONS.md` | ~5,000 字 | 13 个矛盾/张力 |
| `QUESTIONS.md` | ~3,500 字 | 15+开放问题 + 实证验证表 |
| `REAL_WORLD_EXAMPLES.md` | ~5,000 字 | 分类案例 + 实证研究 |
| `SUMMARY.md` | ~1,000 字 | 本文件 |

**总计**: ~42,000 字的深度研究产出

---

## 全书论证结构

```
第 1 层：定义问题 (Ch01-03)
第 2 层：核心设计原则 (Ch04-10)
第 3 层：设计过程 (Ch11)
第 4 层：沟通设计 (Ch12-15)
第 5 层：持续演进 (Ch16-18)
第 6 层：应用与反思 (Ch19-22)
```

## 比较过的设计思想/作品（14种）

Brooks / Parnas / Martin (Clean Code) / Hunt & Thomas (Pragmatic Programmer) / McConnell (Code Complete) / Evans (DDD) / Minsky (Make Illegal States) / Fowler & Beck (Agile, TDD) / Normand (FP critique) / Penner (Monads critique) / Unix 哲学 / Simon (The Sciences of the Artificial) / Hickey (Simple Made Easy) / Yegor Bugayenko (Fail Fast)

## 核心发现 Top 10

1. **深模块概念是 Ousterhout 最独特的贡献**，但也面临最有力的批评（Koppel/Normand："深度"无法客观测量）
2. **Ousterhout vs Martin 辩论**是软件设计领域最重要的方法论对立
3. **核心论点被实证支持**但具体数字（10-20%）未经验证
4. **AI 编码助手 = 战术龙卷风**（2025 年核心论述），使设计技能更加重要
5. **类型系统是最大盲区**——"使非法状态不可表示"是"定义不存在的错误"的编译时版本
6. **"定义不存在的错误" vs "Fail Fast"** 互补而非对立
7. **Ousterhout 用了 35 年 4 个项目**（Tcl → Raft → RAMCloud → Homa）持续验证自己的哲学
8. **设计两次 = ADR 的前身**（过程 vs 产物）
9. **书中缺失**: 系统级架构、FP、实证、权衡分析、组织因素
10. **兼容性**: 与 Brooks/Parnas/Pragmatic Programmer/Code Complete 共享核心理念但提供独特的"深度"透镜
