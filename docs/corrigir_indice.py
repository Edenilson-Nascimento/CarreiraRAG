import psycopg2

url = input("Cole a connection string e aperte Enter: ").strip()

conn = psycopg2.connect(url, connect_timeout=15)
cur = conn.cursor()

cur.execute("DROP INDEX IF EXISTS documentos_embedding_idx")
cur.execute(
    "CREATE INDEX documentos_embedding_idx "
    "ON documentos USING hnsw (embedding vector_cosine_ops)"
)
conn.commit()

cur.execute(
    "SELECT id FROM documentos "
    "ORDER BY embedding <=> (SELECT embedding FROM documentos LIMIT 1) LIMIT 5"
)
print("busca com o novo indice:", cur.fetchall())