from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.chunking import dividir_em_chunks
from app.database import get_connection
from app.gemini_client import gerar_embedding

app = FastAPI(title="CarreiraRAG API")


class DocumentoIn(BaseModel):
    tipo: str
    titulo: str
    conteudo: str


class DocumentoOut(BaseModel):
    id: int
    tipo: str
    titulo: str
    chunk_index: int
    conteudo: str
    criado_em: datetime


class DocumentoCriadoResumo(BaseModel):
    titulo: str
    chunks_criados: int
    ids: list[int]


@app.get("/health")
def health_check():
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "banco": "conectado"}
    except Exception as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponível: {erro}")


@app.post("/documentos", response_model=DocumentoCriadoResumo, status_code=201)
def criar_documento(documento: DocumentoIn):
    if documento.tipo not in ("curriculo", "vaga"):
        raise HTTPException(status_code=422, detail="tipo deve ser 'curriculo' ou 'vaga'")

    chunks = dividir_em_chunks(documento.conteudo)

    conn = get_connection()
    ids_criados = []
    try:
        with conn.cursor() as cur:
            for indice, chunk in enumerate(chunks):
                embedding = gerar_embedding(chunk, task_type="RETRIEVAL_DOCUMENT")
                cur.execute(
                    """
                    INSERT INTO documentos (tipo, titulo, chunk_index, conteudo, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (documento.tipo, documento.titulo, indice, chunk, embedding),
                )
                ids_criados.append(cur.fetchone()["id"])
            conn.commit()
    finally:
        conn.close()

    return DocumentoCriadoResumo(
        titulo=documento.titulo,
        chunks_criados=len(ids_criados),
        ids=ids_criados,
    )


@app.get("/documentos", response_model=list[DocumentoOut])
def listar_documentos():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tipo, titulo, chunk_index, conteudo, criado_em
                FROM documentos
                ORDER BY titulo, chunk_index
                """
            )
            return cur.fetchall()
    finally:
        conn.close()
