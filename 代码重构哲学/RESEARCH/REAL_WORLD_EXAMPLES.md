# REAL_WORLD_EXAMPLES — 真实世界案例

> 从 GitHub、博客、Reddit、Hacker News、StackOverflow 收集的真实工程案例。

---

## 收集来源

### GitHub
- [johnousterhout/aposd-vs-clean-code](https://github.com/johnousterhout/aposd-vs-clean-code) — Ousterhout vs Robert Martin 辩论
- [leung018/refactor-prime-generator](https://github.com/leung018/refactor-prime-generator) — 社区成员基于 APOSD 原则重构 PrimeGenerator
- [20150723/A-Philosophy-of-Software-Design](https://github.com/20150723/A-Philosophy-of-Software-Design) — 中文翻译版

### 博客 / 书评
- **Pathsensitive (Jimmy Koppel)**: [Book Review: A Philosophy of Software Design](https://www.pathsensitive.com/2018/10/book-review-philosophy-of-software.html) — 最重要的批评性书评
- **16elt.com**: [Ideas from "A Philosophy of Software Design"](https://www.16elt.com/2024/09/25/first-book-of-byte-sized-tech/) — 2024 年深度博客
- **Futurum.dev**: [Ideas from A Philosophy of Software Design](https://www.futurum.dev/bookmark/2024-12-22-ideas-from--a-philosophy-of-software-design-.html)
- **Pragmatic Engineer**: [The Philosophy of Software Design – with John Ousterhout](https://newsletter.pragmaticengineer.com/p/the-philosophy-of-software-design) — 深度访谈

### 社区讨论
- **Lobsters**: [Default To Large Modules](https://lobste.rs/s/d2qryv/default_large_modules)
- **豆瓣**: [Software Design Book 小记](https://book.douban.com/review/14696143/) — 中文社区批评
- **掘金**: [爆赞！完全认同！](https://juejin.cn/post/7547912749645987890)
- **美团技术博客**: [降低软件复杂性一般原则和方法](https://tech.meituan.com/2019/09/19/common-method-of-reduce-complexity.html)

### 作者相关
- Stanford CS 190: [Software Design Studio](https://web.stanford.edu/~ouster/cs190-winter24/)
- Homa Transport Protocol (2024-2025) — Ousterhout 将原则应用于 Linux 内核网络协议
- RAMCloud — 分布式内存存储系统，Ousterhout 的代码被 Koppel 评为"最干净"

---

## 真实工程案例分类

### 深模块的正例
| 系统 | 接口 | 封装的内容 | 来源 |
|------|------|-----------|------|
| Unix File I/O | 5 syscalls | 磁盘布局、缓存、权限、调度 | 书中 |
| Garbage Collector (Go/Java) | 零接口 | 内存管理、标记清除、分代回收 | 书中 |
| SQL/关系数据库 | SQL 语句 | B树、查询优化、事务日志 | 扩展 |
| Redis | 约 200 条命令 | 复杂数据结构、持久化、复制 | 扩展 |
| Docker/容器 | `docker run` | cgroups, namespaces, 文件系统层叠 | 扩展 |

### 浅模块/多类症的反例
| 系统 | 问题 | 症状 |
|------|------|------|
| Java I/O (旧版) | 3 个对象才能读文件 | 多类症 |
| J2EE/早期 EJB | Home/Local/Remote 接口层 | 过度抽象 |
| 早期 AWS Java SDK | Client → Config → Request → Response 多重对象 | 接口过宽 |
| Android `AsyncTask` | 3 个泛型参数 + 4 个回调方法 | 认知负荷高 |

### 战略式 vs 战术式的真实案例
| 公司 | 方法 | 结果 |
|------|------|------|
| Google | 战略式 | 强大的技术文化，顶级的招聘吸引力 |
| VMware | 战略式 | 复杂系统稳定运行 |
| Facebook/Meta | 战术式（早期）→ 试图转战略式 | 商业成功，但代码库难以维护 |
| 多数初创公司 | 战术式 | 技术债务累积 |

---

## 值得进一步调查的声称

1. **Ousterhout 声称战略式编程在 6-18 个月收回成本** — 无实证数据
2. **"差的代码质量至少使开发速度降低 20%"** — 无引用来源
3. **"最好的工程师对良好的设计深感兴趣"** — 招聘市场的实际证据？
4. **RAMCloud 是"最干净代码"** — 仅 Koppel 一人评价，样本量不足

---

## 第二轮研究发现

### Ousterhout 自己的实践：Homa 传输协议 (2025)

**来源**: Linux netdev 邮件列表 (v16 patches, Oct 2025), Phoronix, Pragmatic Engineer 播客

**Homa 是什么**: 一个从零设计的传输协议，替代 TCP 用于数据中心环境。无连接、面向消息、可靠、流控。在短消息尾延迟上比 TCP 低 10-100 倍。

**如何体现深模块原则**:
- **接口**: 简单的 `send`/`receive` 语义，每个应用一个 socket（vs TCP 的每对端一个 socket）
- **实现**: ~15,000 行代码处理优先级、接收端驱动流控、pacing、定时器、对端跟踪、RPC 复用
- **模块分解**: `homa_pool`, `homa_peer`, `homa_sock`, `homa_rpc`, `homa_incoming`, `homa_outgoing`, `homa_pacer`, `homa_timer`, `homa_plumbing` — 每个模块职责聚焦但内部深度足够

**意义**: 这是 Ousterhout 在 2025 年亲自将自己的设计哲学应用于 Linux 内核级代码的活案例。

### "定义不存在的错误" vs "使非法状态不可表示"

**Minsky 的方法** (编译时/类型层):
- 用代数数据类型 (enum/sum type) 建模数据，使不可能的状态组合在代码中无法表达
- 例：`Loading | Error(msg) | Success(data)` 替代 `loading: bool, error: bool, data: Option<T>`
- 编译器保证只有一个状态活跃

**Ousterhout 的方法** (运行时/接口层):
- 在模块内部处理异常情况，使调用者不需要关心
- 例：`unset` 确保变量不存在，即使删除不存在的变量也是正常的

**关系**: 互补而非竞争。Minsky 操作在类型层（"如果它不应该发生，让编译器保证它不会发生"），Ousterhout 操作在接口层（"如果它发生了，模块内部处理好，不要麻烦调用者"）。两者共同目标是降低复杂性，但使用了不同的"杠杆"。

### 函数式编程社区对 Ousterhout 的回应

**批评方**:
- "本书中讨论的大多数问题不适用于函数式编程。FP 本身就解决了大部分问题" — 匿名评论者
- Brikman (2025): "这本书完全聚焦 C++/Java/类 OOP 语言，完全遗漏了函数式编程和强大类型系统的许多重要教训"

**有趣的平行发展** (Chris Penner, 2025):
- "Monads Are Too Powerful" — 从 FP 内部提出的批评，认为 Monad 过于表达力强以至于丧失了静态分析能力
- 这与 Ousterhout 的"过度抽象会导致复杂性"有深刻的平行关系
- Penner 在寻找 Applicative → Selective → Monad 之间的"甜点"，类似 Ousterhout 在通用和专用之间的平衡

### ADR 作为设计两次的制度化

**ADR (Architecture Decision Record)** 的 "Alternatives Considered" 部分是 Ousterhout "设计两次" 的自然延伸：
- 设计两次 = 过程（生成多个方案）
- ADR = 产物（记录选择了什么、为什么、拒绝了什么）
- 微软 Well-Architected Framework 和 MADR 模板都强调记录被拒绝的替代方案

---

## 第三轮研究发现

### 实证验证：支持 Ousterhout 核心论点的独立研究

| 研究 | 规模 | 关键发现 |
|------|------|---------|
| Google ICSE 2025 | 1252 项目, 7200 调查 | 高架构复杂性 → 更多时间修缺陷 |
| Code Red (2022) | 39 代码库 | 低质量代码: 缺陷 15×, 开发时间 +124% |
| Besker et al. (2019) | 43 开发者, 7 周 | 23% 时间被技术债务浪费 |
| CMU AI 研究 (2024-25) | 806 GitHub 项目 | AI 加速 +281%, 复杂性 +40%, 收益 2 月消失 |
| Sturtevant (2013) | MIT/HBS | 架构复杂性 → 50% 生产率下降 |

**结论**: Ousterhout 的 10-20% / 6-18 月具体数字未经验证，但核心论点（战术式 → 复杂性累积 → 长期生产力下降）是软件工程研究中最充分验证的命题之一。

### 前端架构中的深模块应用

**来源**: dev.to 2025

**浅服务（反模式）**: 仅包装 `http.get` — 组件需自行管理加载/错误/重试
**深服务**: 集成 `rxResource`, 缓存, 重试, signal-based 状态 — 组件只需 `.value()`, `.isLoading()`
**检验标准**: "如果我删除这个抽象, 调用者是否变得有意义地更复杂?"

### CS 190 课程详情

- 最后开设: Winter 2024 (Ousterhout 已退休)
- 三个项目: Raft 共识 (Leader Election + Log + Replicated Shell) + 正则表达式解析器
- 团队 2 人, Java, 代码审查驱动的教学
- 课程目标: "Change the way you think about programming"
