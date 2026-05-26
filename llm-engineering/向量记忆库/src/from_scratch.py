"""
从零实现向量记忆库（纯 Python 标准库，无 numpy、无 chromadb、无 sentence-transformers）

管道：
  1. 读取 markdown 文件 → 去 frontmatter
  2. 按段落边界切分为 chunks
  3. 构建词汇表 → 计算 TF-IDF 向量
  4. 查询 → TF-IDF 向量 → 余弦相似度 → top-K

使用：
  python3 from_scratch.py ingest    # 索引笔记
  python3 from_scratch.py search "深模块的好处"  # 搜索
"""

import sys
import os
import re
import json
import math
from collections import Counter
from pathlib import Path


# ============================================================
# 第 1 步：中文分词（字符 n-gram）
# ============================================================
# 没有 jieba 等分词工具时，用字符级别的 bigram + trigram
# 对中文效果不错："深模块" → ["深模", "模块", "深模块"]
# 同时保留英文单词边界

def tokenize(text: str) -> list[str]:
    """中文字符 n-gram + 英文单词 混合分词"""
    tokens = []

    # 分离中文连续块和英文/数字/标点
    segments = re.split(r'([一-鿿]+)', text.lower())

    for seg in segments:
        if not seg.strip():
            continue
        if re.match(r'[一-鿿]+', seg):
            # 中文：字符 bigram + trigram
            chars = list(seg)
            for i in range(len(chars) - 1):
                tokens.append(chars[i] + chars[i+1])       # bigram
            for i in range(len(chars) - 2):
                tokens.append(chars[i] + chars[i+1] + chars[i+2])  # trigram
            if len(chars) <= 2:
                tokens.extend(chars)  # 短字符串保留单字
        else:
            # 英文/数字：按单词边界分
            words = re.findall(r'[a-z0-9]+', seg)
            tokens.extend(words)

    return tokens


# ============================================================
# 第 2 步：TF-IDF 向量化
# ============================================================

class TFIDF:
    """从零实现 TF-IDF"""

    def __init__(self):
        self.vocab: dict[str, int] = {}   # word → id
        self.idf: dict[str, float] = {}   # word → idf 值
        self.doc_count = 0

    def fit(self, documents: list[str]):
        """构建词汇表 + 计算 IDF"""
        # 对每个文档分词
        tokenized = [tokenize(doc) for doc in documents]
        self.doc_count = len(tokenized)

        # 文档频率 DF：每个词出现在多少篇文档中
        df = Counter()
        for tokens in tokenized:
            unique = set(tokens)
            for t in unique:
                df[t] += 1

        # 按频率排序，取前 10000 个词（控制向量维度）
        top_words = [w for w, _ in df.most_common(10000)]
        self.vocab = {w: i for i, w in enumerate(top_words)}

        # IDF = log(总文档数 / 包含该词的文档数) + 1（平滑）
        for word, idx in self.vocab.items():
            self.idf[word] = math.log(self.doc_count / (df[word] + 1)) + 1

        print(f"  Vocabulary size: {len(self.vocab)}")

    def transform(self, text: str) -> list[float]:
        """将文本转为 TF-IDF 向量"""
        tokens = tokenize(text)
        if not tokens:
            return [0.0] * len(self.vocab)

        # TF：词频
        tf = Counter(tokens)
        vec = [0.0] * len(self.vocab)

        for word, count in tf.items():
            if word in self.vocab:
                idx = self.vocab[word]
                tf_val = count / len(tokens)          # 归一化词频
                vec[idx] = tf_val * self.idf[word]    # TF × IDF

        return vec

    def to_json(self) -> str:
        return json.dumps({
            "vocab": self.vocab,
            "idf": self.idf,
            "doc_count": self.doc_count
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "TFIDF":
        data = json.loads(s)
        tfidf = cls()
        tfidf.vocab = data["vocab"]
        tfidf.idf = data["idf"]
        tfidf.doc_count = data["doc_count"]
        return tfidf


# ============================================================
# 第 3 步：余弦相似度
# ============================================================

def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: list[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def cosine_sim(a: list[float], b: list[float]) -> float:
    """余弦相似度，返回 [0, 1]"""
    na, nb = norm(a), norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return dot(a, b) / (na * nb)


# ============================================================
# 第 4 步：Markdown 处理
# ============================================================

def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def chunk_text(text: str, max_len: int = 600) -> list[dict]:
    """按段落边界切分"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for p in paragraphs:
        if len(current) + len(p) < max_len:
            current += "\n\n" + p if current else p
        else:
            if current:
                chunks.append({"text": current})
            current = p

    if current:
        chunks.append({"text": current})

    return chunks


# ============================================================
# 第 5 步：向量记忆库
# ============================================================

class VectorMemory:
    """从零实现的向量记忆库"""

    def __init__(self, db_path: str = "vector_memory_db/scratch"):
        self.db_path = db_path
        self.tfidf = TFIDF()
        self.chunks: list[dict] = []  # [{text, metadata, vector}]

    # ---- 索引 ----

    def ingest(self, source_dir: str):
        """读取 markdown 文件 → 切分 → TF-IDF → 存储"""
        md_files = sorted(Path(source_dir).glob("*.md"))
        md_files = [f for f in md_files if not f.name.startswith("CLAUDE")]

        if not md_files:
            print(f"No .md files in {source_dir}")
            return

        # 1. 读取 + 切分（先收集所有 chunk 文本用于训练 TF-IDF）
        raw_chunks = []
        for fpath in md_files:
            with open(fpath, encoding="utf-8") as f:
                text = strip_frontmatter(f.read())
            for c in chunk_text(text):
                c["source"] = str(fpath)
                raw_chunks.append(c)

        print(f"  Chunks: {len(raw_chunks)}")

        # 2. 训练 TF-IDF（在所有 chunk 上）
        print("  Building TF-IDF vocabulary...")
        self.tfidf.fit([c["text"] for c in raw_chunks])

        # 3. 向量化每个 chunk
        print("  Vectorizing chunks...")
        self.chunks = []
        for c in raw_chunks:
            vec = self.tfidf.transform(c["text"])
            self.chunks.append({
                "text": c["text"],
                "source": c["source"],
                "vector": vec
            })

        # 4. 持久化
        self._save()
        print(f"  Indexed {len(self.chunks)} chunks from {len(md_files)} files.\n")

    # ---- 搜索 ----

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """查询 → 向量化 → 余弦相似度 → top-K"""
        if not self.chunks:
            print("No chunks indexed. Run 'ingest' first.")
            return []

        q_vec = self.tfidf.transform(query)
        scored = []
        for c in self.chunks:
            sim = cosine_sim(q_vec, c["vector"])
            scored.append((sim, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, c in scored[:top_k]:
            results.append({
                "text": c["text"][:500],
                "source": c["source"],
                "similarity": round(sim, 4)
            })
        return results

    # ---- 持久化 ----

    def _save(self):
        os.makedirs(self.db_path, exist_ok=True)

        # 保存 TF-IDF 模型
        with open(f"{self.db_path}/tfidf.json", "w", encoding="utf-8") as f:
            f.write(self.tfidf.to_json())

        # 保存 chunks（向量 + 元数据）
        with open(f"{self.db_path}/chunks.jsonl", "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps({
                    "text": c["text"],
                    "source": c["source"],
                    "vector": c["vector"]
                }, ensure_ascii=False) + "\n")

    def load(self):
        tfidf_path = f"{self.db_path}/tfidf.json"
        chunks_path = f"{self.db_path}/chunks.jsonl"

        if not os.path.exists(tfidf_path):
            print(f"No index found at {self.db_path}. Run 'ingest' first.")
            return False

        with open(tfidf_path, encoding="utf-8") as f:
            self.tfidf = TFIDF.from_json(f.read())

        self.chunks = []
        with open(chunks_path, encoding="utf-8") as f:
            for line in f:
                self.chunks.append(json.loads(line))

        print(f"  Loaded {len(self.chunks)} chunks, vocab={len(self.tfidf.vocab)}")
        return True


# ============================================================
# CLI
# ============================================================

def cmd_ingest():
    src = sys.argv[2] if len(sys.argv) > 2 else "代码重构哲学/讲义"
    print(f"Ingesting from: {src}")
    vm = VectorMemory()
    vm.ingest(src)


def cmd_search():
    if len(sys.argv) < 3:
        print("Usage: python3 from_scratch.py search <query>")
        return

    query = sys.argv[2]
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    vm = VectorMemory()
    if not vm.load():
        return

    results = vm.search(query, top_k=top_k)

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    for i, r in enumerate(results):
        print(f"\n--- {i+1}. [sim={r['similarity']:.4f}] {r['source']} ---")
        print(r["text"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 from_scratch.py ingest [dir]")
        print("  python3 from_scratch.py search <query> [top_k]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "ingest":
        cmd_ingest()
    elif cmd == "search":
        cmd_search()
    else:
        print(f"Unknown command: {cmd}")
