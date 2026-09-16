from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.database import get_connection

app = FastAPI(title="CarreiraRAG API")


class DocumentoIn(BaseModel):
    tipo: str
    titulo: str
    conteudo: str


class DocumentoOut(BaseModel):
    id: int
    tipo: str
    titulo: str
    conteudo: str
    criado_em: datetime


@app.get("/health")
def health_check():
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "banco": "conectado"}
    except Exception as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponível: {erro}")


@app.post("/documentos", response_model=DocumentoOut, status_code=201)
def criar_documento(documento: DocumentoIn):
    if documento.tipo not in ("curriculo", "vaga"):
        raise HTTPException(status_code=422, detail="tipo deve ser 'curriculo' ou 'vaga'")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documentos (tipo, titulo, conteudo)
                VALUES (%s, %s, %s)
                RETURNING id, tipo, titulo, conteudo, criado_em
                """,
                (documento.tipo, documento.titulo, documento.conteudo),
            )
            novo = cur.fetchone()
            conn.commit()
            return novo
    finally:
        conn.close()


@app.get("/documentos", response_model=list[DocumentoOut])
def listar_documentos():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, tipo, titulo, conteudo, criado_em FROM documentos ORDER BY criado_em DESC"
            )
            return cur.fetchall()
    finally:
        conn.close()