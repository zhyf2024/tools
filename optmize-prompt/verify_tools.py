import sys
from sentence_transformers import SentenceTransformer
from pgvector import Vector
from pgvector.psycopg import register_vector
import psycopg

sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg.connect("host=127.0.0.1 port=5432 dbname=agent_db user=admin password=admin", autocommit=True)
register_vector(conn)

print("ext:", conn.execute("select extname, extversion from pg_extension where extname='vector'").fetchone())
print("cols:", conn.execute("select column_name, data_type from information_schema.columns where table_name='tools' order by ordinal_position").fetchall())
print("count:", conn.execute("select count(*) from tools").fetchone()[0])


from ingest_tools import MODEL_NAME

model = SentenceTransformer(MODEL_NAME, device="cpu", local_files_only=True)
for q in ["我要查 CA1501 航班到点了没", "把这张图片压小一点", "100 美元换多少人民币"]:
    qv = model.encode([q], normalize_embeddings=True)[0].tolist()
    hits = conn.execute(
        "select id, name as n, round((1 - (embedding <=> %s))::numeric, 4) as score from tools order by embedding <=> %s limit 2",
        (Vector(qv), Vector(qv)),
    ).fetchall()
    print(q, "->", [(str(id)+n, float(s)) for id, n, s in hits])
conn.close()
