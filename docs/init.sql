CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('curriculo', 'vaga')),
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    embedding VECTOR(1536),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS documentos_embedding_idx
    ON documentos USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE TABLE IF NOT EXISTS perguntas (
    id SERIAL PRIMARY KEY,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);