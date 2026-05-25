"""
将 Obsidian 笔记索引到 ChromaDB 向量记忆库。

使用方式：python3 ingest_notes.py [目录路径]
默认索引 代码重构哲学/讲义/
"""

import sys
import os
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime

from sentence_transformers import SentenceTransformer
import chromadb


# ============================================================
# 配置
# ============================================================

DB_PATH = "./vector_memory_db"
COLLECTION_NAME = "memory"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_MAX_LEN = 800  # 每段最多多少字符
MANIFEST_PATH = f"{DB_PATH}/manifest.json"


# ============================================================
# 工具函数
# ============================================================

def strip_frontmatter(text: str) -> str:
    """去掉 YAML frontmatter（--- 之间的内容）"""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def chunk_by_boundary(text: str, max_len: int = CHUNK_MAX_LEN) -> list[dict]:
    """按段落边界切分，合并短段落直到接近 max_len"""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    current_section = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        # 追踪当前所在的小节标题
        header_match = re.match(r"^#{1,3}\s+(.+)", p)
        if header_match:
            current_section = header_match.group(1)

        if len(current) + len(p) < max_len:
            current += "\n\n" + p if current else p
        else:
            if current:
                chunks.append({"text": current, "section": current_section})
            current = p

    if current:
        chunks.append({"text": current, "section": current_section})

    return chunks


def file_md5(filepath: str) -> str:
    return hashlib.md5(open(filepath, "rb").read()).hexdigest()


def load_manifest() -> dict:
    if os.path.exists(MANIFEST_PATH):
        return json.load(open(MANIFEST_PATH))
    return {}


def save_manifest(m: dict):
    os.makedirs(DB_PATH, exist_ok=True)
    json.dump(m, open(MANIFEST_PATH, "w"), indent=2, ensure_ascii=False)


def detect_changes(file_list: list[str]) -> tuple[list[str], list[str]]:
    """返回 (changed_files, deleted_files)"""
    old = load_manifest()
    changed = []
    new_manifest = {}

    for fpath in file_list:
        md5 = file_md5(fpath)
        new_manifest[fpath] = md5
        if old.get(fpath) != md5:
            changed.append(fpath)

    deleted = list(set(old.keys()) - set(new_manifest.keys()))
    save_manifest(new_manifest)
    return changed, deleted


def extract_title(text: str) -> str:
    """提取 # 标题"""
    m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    return m.group(1) if m else os.path.basename


def extract_tags(text: str) -> str:
    """从正文中提取 #标签"""
    # 排除代码块和 frontmatter 里的
    tags = re.findall(r"(?<!\w)#([\w/一-鿿-]+)", text)
    return ",".join(tags[:10])  # 最多取10个


# ============================================================
# 核心逻辑
# ============================================================

def ingest_file(filepath: str, collection, model) -> int:
    """索引单个文件，返回 chunk 数"""
    print(f"  Indexing: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    text = strip_frontmatter(raw)
    title = extract_title(text)
    file_tags = extract_tags(raw)
    chunks = chunk_by_boundary(text)
    f_md5 = file_md5(filepath)

    embeddings = model.encode([c["text"] for c in chunks])

    collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{
            "source": filepath,
            "title": title,
            "section": c["section"],
            "tags": file_tags,
            "type": "note",
            "md5": f_md5,
            "embedding_model": MODEL_NAME,
            "date": datetime.now().isoformat(),
            "chunk_index": i
        } for i, c in enumerate(chunks)],
        ids=[f"{filepath}#{i}" for i in range(len(chunks))],
        embeddings=embeddings.tolist()
    )

    return len(chunks)


def main():
    source_dir = sys.argv[1] if len(sys.argv) > 1 else "代码重构哲学/讲义"

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Connecting to ChromaDB: {DB_PATH}")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    # 收集文件
    md_files = [str(p) for p in Path(source_dir).glob("*.md")
                if not p.name.startswith("CLAUDE")]

    if not md_files:
        print(f"No .md files found in {source_dir}")
        return

    # 变更检测
    changed, deleted = detect_changes(md_files)

    # 处理删除
    for f in deleted:
        print(f"  Removing: {f}")
        collection.delete(where={"source": f})

    if not changed:
        print("No changes detected. Up to date.")
        return

    # 处理变更：先删旧 chunks，再插入新的
    total = 0
    for fpath in changed:
        collection.delete(where={"source": fpath})
        n = ingest_file(fpath, collection, model)
        total += n

    print(f"\nDone. {len(changed)} files, {total} chunks indexed.")


if __name__ == "__main__":
    main()
