import sys

import psycopg2

if len(sys.argv) < 2:
    print('Uso: python docs/configurar_banco.py "postgresql://..."')
    sys.exit(1)

url = sys.argv[1]

sql = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('curriculo', 'vaga')),
    titulo TEXT NOT NULL,
    chunk_index INT NOT NULL DEFAULT 0,
    conteudo TEXT NOT NULL,
    embedding VECTOR(768),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS documentos_embedding_idx
    ON documentos USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS perguntas (
    id SERIAL PRIMARY KEY,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

print("Conectando...")
conn = psycopg2.connect(url, connect_timeout=15)
cur = conn.cursor()
cur.execute(sql)
conn.commit()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
print("Tabelas criadas:", [linha[0] for linha in cur.fetchall()])

cur.close()
conn.close()
print("Pronto!")
