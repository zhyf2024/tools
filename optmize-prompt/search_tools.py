import argparse
import sys

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from sentence_transformers import CrossEncoder, SentenceTransformer

from ingest_tools import DBNAME, DBPWD, DBUSER, DSN, MODEL_NAME

RERANKER_NAME = "BAAI/bge-reranker-v2-m3"
DEFAULT_CANDIDATES = 10
DEFAULT_TOP_K = 3

_encoder: SentenceTransformer | None = None
_reranker: CrossEncoder | None = None
_conn = None


def encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        print(f"loading embedding model {MODEL_NAME} ...")
        _encoder = SentenceTransformer(MODEL_NAME, device="cpu", local_files_only=True)
    return _encoder


def reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        print(f"loading reranker {RERANKER_NAME} ...")
        _reranker = CrossEncoder(RERANKER_NAME, device="cpu", local_files_only=True)
    return _reranker


def connection():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(
            host=DSN["host"],
            port=DSN["port"],
            dbname=DBNAME,
            user=DBUSER,
            password=DBPWD,
            autocommit=True,
        )
        register_vector(_conn)
    return _conn


def recall(query: str, limit: int) -> list[dict]:
    qvec = encoder().encode([query], normalize_embeddings=True)[0].tolist()
    rows = connection().execute(
        """
        select name, description, content,
               1 - (embedding <=> %s) as recall_score
        from tools
        order by embedding <=> %s
        limit %s
        """,
        (Vector(qvec), Vector(qvec), limit),
    ).fetchall()
    return [
        {"name": n, "description": d, "content": c, "recall_score": float(s)}
        for n, d, c, s in rows
    ]


def search_tools(query: str, top_k: int = DEFAULT_TOP_K, candidates: int = DEFAULT_CANDIDATES) -> list[dict]:
    docs = recall(query, max(candidates, top_k))
    if not docs:
        return []
    scores = reranker().predict(
        [(query, doc["content"]) for doc in docs],
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    for doc, score in zip(docs, scores):
        doc["rerank_score"] = float(score)
    docs.sort(key=lambda d: d["rerank_score"], reverse=True)
    for rank, doc in enumerate(docs, start=1):
        doc["rank"] = rank
    return docs[:top_k]


def main() -> int:
    parser = argparse.ArgumentParser(description="Stella 召回 + bge-reranker 精排")
    parser.add_argument("query", help="用户查询")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--candidates", type=int, default=DEFAULT_CANDIDATES)
    parser.add_argument("--show-candidates", action="store_true", help="打印召回阶段的完整候选")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    candidates = recall(args.query, max(args.candidates, args.top_k))
    if args.show_candidates:
        print(f"recall top-{len(candidates)}:")
        for i, doc in enumerate(candidates, 1):
            print(f"  {i:2d}. [{doc['recall_score']:.4f}] {doc['name']}")

    results = search_tools(args.query, top_k=args.top_k, candidates=args.candidates)
    print(f"reranked top-{len(results)} for: {args.query}")
    for doc in results:
        print(
            f"  {doc['rank']:2d}. {doc['name']}  rerank={doc['rerank_score']:.4f} "
            f"recall={doc['recall_score']:.4f}  {doc['description']}"
        )
    connection().close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
