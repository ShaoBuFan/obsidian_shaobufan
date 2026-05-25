"""
命令行语义搜索工具。直接在终端搜你的向量记忆库。

使用方式：python3 search.py "查询内容" [--top-k 5] [--type note|conversation|all]
"""

import sys
import argparse
from sentence_transformers import SentenceTransformer
import chromadb


DB_PATH = "./vector_memory_db"
COLLECTION_NAME = "memory"
MODEL_NAME = "all-MiniLM-L6-v2"


def main():
    parser = argparse.ArgumentParser(description="搜索向量记忆库")
    parser.add_argument("query", type=str, help="搜索内容")
    parser.add_argument("--top-k", type=int, default=5, help="返回条数（默认5）")
    parser.add_argument("--type", type=str, default="all",
                        choices=["note", "conversation", "all"],
                        help="内容类型过滤")
    args = parser.parse_args()

    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Connecting to ChromaDB: {DB_PATH}")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    where = None if args.type == "all" else {"type": args.type}

    vec = model.encode(args.query).tolist()
    results = collection.query(
        query_embeddings=[vec],
        n_results=args.top_k,
        where=where
    )

    print(f"\n{'='*60}")
    print(f"Query: {args.query}")
    print(f"{'='*60}\n")

    if not results["documents"][0]:
        print("No results found.")
        return

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        sim = 1 - dist  # 距离转相似度
        source = meta.get("source", "unknown")
        title = meta.get("title", "")
        section = meta.get("section", "")
        date = meta.get("date", "")

        print(f"--- Result {i+1} [similarity: {sim:.3f}] ---")
        print(f"Source:  {source}")
        if title:
            print(f"Title:   {title}")
        if section:
            print(f"Section: {section}")
        if date:
            print(f"Date:    {date[:10]}")
        print(f"Text:\n{doc[:500]}")
        if len(doc) > 500:
            print("...")
        print()


if __name__ == "__main__":
    main()
