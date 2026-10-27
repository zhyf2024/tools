import json
import os
import sys

import psycopg
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "dunzhang/stella-mrl-large-zh-v3.5-1792d"
EMBED_DIM = 1792

load_dotenv(os.path.join(BASE_DIR, ".env"))

DBURL = os.environ["DBURL"]
DBUSER = os.environ["DBUSER"]
DBPWD = os.environ["DBPWD"]
DBNAME = os.environ["DBNAME"]


def split_dsn(url: str) -> dict:
    hostport = url.split("//", 1)[1]
    hostport, _, dbname = hostport.partition("/")
    host, _, port = hostport.partition(":")
    return {"host": host or "127.0.0.1", "port": int(port or 5432), "dbname": dbname or DBNAME}


DSN = split_dsn(DBURL)


def connect(dbname: str):
    return psycopg.connect(
        host=DSN["host"], port=DSN["port"], dbname=dbname, user=DBUSER, password=DBPWD, autocommit=True
    )


def ensure_database():
    with connect("postgres") as conn:
        exists = conn.execute("select 1 from pg_database where datname = %s", (DBNAME,)).fetchone()
        if not exists:
            conn.execute(f'create database "{DBNAME}"')
            print(f"created database {DBNAME}")
    conn = connect(DBNAME)
    conn.execute("create extension if not exists vector")
    register_vector(conn)
    return conn


def load_model() -> SentenceTransformer:
    print(f"loading model {MODEL_NAME} ...")
    try:
        return SentenceTransformer(MODEL_NAME, device="cpu", local_files_only=True)
    except Exception as exc:
        print(f"local cache miss ({exc.__class__.__name__}), downloading ...")
        return SentenceTransformer(MODEL_NAME, device="cpu")


def table_dim(conn):
    row = conn.execute(
        """
        select a.atttypmod
        from pg_attribute a
        join pg_class c on a.attrelid = c.oid
        join pg_namespace n on c.relnamespace = n.oid
        where n.nspname = 'public' and c.relname = 'tools'
          and a.attname = 'embedding' and a.attnum > 0 and not a.attisdropped
        """
    ).fetchone()
    return row[0] if row else None


def reset_if_dim_changed(conn, dim: int):
    cur = table_dim(conn)
    if cur is None:
        return
    if cur != dim:
        conn.execute("drop table tools")
        print(f"dropped table tools: embedding dim {cur} -> {dim}")
    else:
        print(f"table tools embedding dim {cur} matches, keeping data")


def load_tools() -> list[dict]:
    with open(os.path.join(BASE_DIR, "tools.json"), encoding="utf-8") as f:
        return json.load(f)


def build_content(tool: dict) -> str:
    lines = [f"工具名称: {tool['name']}", f"功能描述: {tool['description']}"]
    params = tool.get("parameters") or {}
    if params:
        lines.append("参数说明:")
        for key, spec in params.items():
            ptype = spec.get("type", "") if isinstance(spec, dict) else ""
            pdesc = spec.get("description", "") if isinstance(spec, dict) else str(spec)
            lines.append(f"- {key} ({ptype}): {pdesc}")
    return "\n".join(lines)


def create_table(conn, dim: int):
    conn.execute("create extension if not exists vector")
    conn.execute(
        f"""
        create table if not exists tools (
            id serial primary key,
            name text not null unique,
            description text not null,
            parameters jsonb not null default '{{}}'::jsonb,
            content text not null,
            embedding vector({dim}),
            created_at timestamptz not null default now()
        )
        """
    )
    conn.execute(
        """
        create index if not exists tools_embedding_idx
        on tools using hnsw (embedding vector_cosine_ops)
        """
    )


def upsert(conn, rows: list[dict]):
    sql = """
        insert into tools (name, description, parameters, content, embedding)
        values (%s, %s, %s, %s, %s)
        on conflict (name) do update
        set description = excluded.description,
            parameters = excluded.parameters,
            content = excluded.content,
            embedding = excluded.embedding
    """
    with conn.cursor() as cur:
        cur.executemany(
            sql,
            [
                (
                    r["name"],
                    r["description"],
                    Jsonb(r.get("parameters") or {}),
                    r["content"],
                    Vector(r["embedding"]),
                )
                for r in rows
            ],
        )


def main():
    tools = load_tools()
    print(f"loaded {len(tools)} tools from tools.json")

    conn = ensure_database()
    try:
        model = load_model()
        dim = model.get_embedding_dimension()
        if dim != EMBED_DIM:
            raise SystemExit(f"unexpected embedding dim {dim}, expected {EMBED_DIM}")
        print(f"embedding dim: {dim}")

        contents = [build_content(t) for t in tools]
        embeddings = model.encode(
            contents, batch_size=8, show_progress_bar=True, normalize_embeddings=True
        )
        print(f"encoded -> shape {embeddings.shape}")

        rows = []
        for tool, content, emb in zip(tools, contents, embeddings):
            rows.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("parameters") or {},
                    "content": content,
                    "embedding": emb.tolist(),
                }
            )

        reset_if_dim_changed(conn, dim)
        create_table(conn, dim)
        upsert(conn, rows)
        total = conn.execute("select count(*) from tools").fetchone()[0]
        print(f"table tools now holds {total} rows")

        query = "帮我算一下 50 万贷款 30 年 利率 4.5% 每月还多少"
        qvec = model.encode([query], normalize_embeddings=True)[0].tolist()
        hits = conn.execute(
            """
            select id, name, description, 1 - (embedding <=> %s) as score
            from tools
            order by embedding <=> %s
            limit 3
            """,
            (Vector(qvec), Vector(qvec)),
        ).fetchall()
        print("sample query:", query)
        for id, name, desc, score in hits:
            print(f"  {score:.4f} {id} {name}  {desc}")
    finally:
        conn.close()

    print("done")


if __name__ == "__main__":
    sys.exit(main())
