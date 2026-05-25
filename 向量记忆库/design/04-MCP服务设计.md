---
tags:
  - 向量数据库
  - RAG
  - Claude-Code
  - MCP
created: 2026-05-25
---

# MCP 服务设计

## 为什么是 MCP

Claude Code CLI 通过 MCP（Model Context Protocol）接入外部工具。向量记忆库通过一个 MCP Server 暴露三个工具，对话中 Claude 可以直接调用。

```
Claude Code ←→ MCP Server ←→ 向量记忆库 (ChromaDB)
             stdio 传输        search / save / sync
```

## 完整服务定义

```python
# mcp_server.py
from mcp import Server
from sentence_transformers import SentenceTransformer
import chromadb
import hashlib, json, os, uuid
from datetime import datetime

server = Server("vector-memory")
model = SentenceTransformer('all-MiniLM-L6-v2')
db = chromadb.PersistentClient(path="./vector_memory_db")
collection = db.get_or_create_collection("memory")

# ═══════════════════════════════════════════
# 工具 1：检索
# ═══════════════════════════════════════════

@server.tool("search_notes")
def search_notes(query: str, top_k: int = 5, source_type: str = "all"):
    """
    在个人知识库中语义搜索。
    source_type: "notes" / "conversations" / "all"
    """
    vec = model.encode(query).tolist()

    where_filter = None
    if source_type != "all":
        where_filter = {"type": source_type}

    results = collection.query(
        query_embeddings=[vec],
        n_results=min(top_k * 5, 50),  # 多召回一些给 rerank 用
        where=where_filter
    )

    # 复合评分重排（见 07-记忆权重与复合评分）
    scored = compound_rerank(results, query_vec=vec)

    return [
        {
            "text": item["text"],
            "source": item["meta"]["source"],
            "score": round(item["score"], 3),
            "date": item["meta"].get("date", "")
        }
        for item in scored[:top_k]
    ]

# ═══════════════════════════════════════════
# 工具 2：显式保存
# ═══════════════════════════════════════════

@server.tool("save_to_memory")
def save_to_memory(content: str, tags: list[str] = [],
                   importance: str = "medium"):
    """将重要信息显式存入向量记忆库"""
    weight_map = {"low": 1, "medium": 3, "high": 5, "critical": 10}

    vec = model.encode(content).tolist()
    content_hash = hashlib.md5(content.encode()).hexdigest()

    # 去重检查
    existing = collection.get(where={"hash": content_hash})
    if existing["ids"]:
        return {"status": "skipped", "reason": "内容已存在"}

    collection.add(
        documents=[content],
        metadatas=[{
            "source": "explicit_save",
            "type": "explicit_save",
            "tags": ",".join(tags),
            "importance": importance,
            "importance_weight": weight_map[importance],
            "hash": content_hash,
            "date": datetime.now().isoformat()
        }],
        ids=[str(uuid.uuid4())],
        embeddings=[vec]
    )
    return {"status": "saved"}

# ═══════════════════════════════════════════
# 工具 3：同步笔记
# ═══════════════════════════════════════════

@server.tool("sync_notes")
def sync_notes(source_dir: str = "代码重构哲学/讲义"):
    """检测笔记变更并同步到向量库"""
    from glob import glob

    files = glob(f"{source_dir}/*.md")
    changed, deleted = detect_changes(files)

    for f in deleted:
        collection.delete(where={"source": f})

    for f in changed:
        sync_file_safe(f)

    return {
        "synced": len(changed),
        "deleted": len(deleted),
        "files": changed
    }
```

## 注册到 Claude Code

三种方式：

| 方式 | 命令/文件 | 适用 |
|------|-----------|------|
| 命令行 | `claude mcp add --transport stdio vector-memory -- python3 向量记忆库/mcp_server.py` | 快速注册 |
| `.mcp.json` | 项目根目录，可提交 git | 团队共享 |
| `settings.local.json` | `.claude/` 下，不提交 | 个人私有 |

```json
// .mcp.json（推荐）
{
  "mcpServers": {
    "vector-memory": {
      "command": "python3",
      "args": ["向量记忆库/mcp_server.py"]
    }
  }
}
```

权限配置（`settings.local.json`）：

```json
{
  "permissions": {
    "allow": [
      "mcp__vector-memory__search_notes",
      "mcp__vector-memory__save_to_memory",
      "mcp__vector-memory__sync_notes"
    ]
  }
}
```

## 对话中的实际效果

```
用户：我之前对 React Hook 的本质有什么理解？

Claude（内部调用 search_notes("React Hook 本质 闭包")）
  → 检索到：
    1. [0.92] "React Hook 的本质是闭包..." (session/e4c9e773, 2024-03-15)
    2. [0.87] "useEffect 的 cleanup..." (session/a1f0866e, 2024-06-02)

Claude 回答：你在 2024年3月的一次对话中提到 React Hook 的本质
是闭包，当时你把它和函数作用域做了类比。6月又深入讨论了
useEffect 的 cleanup 时机……
```

## 三种集成深度

| 层级 | 做法 | Claude 的行为 |
|------|------|--------------|
| **被动工具**（当前） | MCP 暴露检索工具 | 你问 → Claude 决定要不要查 → 查 → 回答 |
| **自动注入** | Hook 在每轮对话前检索并注入 | 任何问题，相关记忆自动出现在上下文 |
| **主动画像** | 维护用户画像文件，每次对话加载 | Claude "了解"你的偏好，无需每次检索 |

第一层是基础，后两层见 [08-三层架构](08-三层架构.md)。

## 性能注意

- MCP Server 每次工具调用启动一个进程（stdio 传输），嵌入模型加载需要 1-3 秒。缓解方案：
  - 用 API embedding（OpenAI `text-embedding-3-small`）消除本地加载延迟
  - 或将 embedding 服务独立常驻（如一个小型 HTTP 服务），MCP Server 调它而不是每次加载模型
- `depth_score` 在 rerank 阶段对每个候选再做一次向量查询——如果候选量大（50条），这是一个 50 次查询的开销。实际运行后如果太慢，可以把深度分换成从 metadata 里读"重复提及数"而非实时计算
