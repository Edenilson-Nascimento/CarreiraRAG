from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.chunking import dividir_em_chunks
from app.database import get_connection
from app.gemini_client import gerar_embedding, gerar_resposta

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


class PerguntaIn(BaseModel):
    pergunta: str


class PerguntaOut(BaseModel):
    pergunta: str
    resposta: str
    fontes: list[str]


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


def buscar_chunks_relevantes(embedding_pergunta: list[float], limite: int = 5, limiar_maximo: float = 0.65) -> list[dict]:
    conn = get_connection()
    vetor_str = "[" + ",".join(str(x) for x in embedding_pergunta) + "]"
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tipo, titulo, conteudo, embedding <=> %s::vector AS distancia
                FROM documentos
                WHERE embedding <=> %s::vector < %s
                ORDER BY distancia
                LIMIT %s
                """,
                (vetor_str, vetor_str, limiar_maximo, limite),
            )
            return cur.fetchall()
    finally:
        conn.close()


def montar_prompt(pergunta: str, chunks: list[dict]) -> str:
    documentos_formatados = []
    for c in chunks:
        doc = f"""---
[DOCUMENTO: {c['titulo']} | TIPO: {c['tipo']}]
{c['conteudo']}
---"""
        documentos_formatados.append(doc)

    contexto = "\n\n".join(documentos_formatados)

    return f"""Você é um assistente técnico especializado em recrutamento e análise de compatibilidade entre candidatos e vagas.

Sua tarefa é responder à pergunta do usuário baseando-se EXCLUSIVAMENTE nas informações fornecidas na seção CONTEXTO abaixo.

REGRAS OBRIGATÓRIAS:
1. Responda apenas com base em fatos expressamente declarados no contexto.
2. Não invente, deduza ou extrapole informações ausentes.
3. Se o contexto não contiver dados suficientes para responder com certeza, afirme claramente: "Não há informações suficientes nos documentos fornecidos para responder a essa pergunta."
4. Ao citar uma experiência, habilidade ou requisito, mencione o nome do documento de origem de onde a informação foi extraída.
5. Seja direto, conciso e profissional em português.

CONTEXTO:
{contexto}

PERGUNTA DO USUÁRIO:
{pergunta}

RESPOSTA:"""


@app.post("/perguntar", response_model=PerguntaOut)
def perguntar(pergunta: PerguntaIn):
    embedding_pergunta = gerar_embedding(pergunta.pergunta, task_type="RETRIEVAL_QUERY")

    chunks = buscar_chunks_relevantes(embedding_pergunta)
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="Nenhum documento cadastrado ainda. Cadastre um currículo ou vaga primeiro.",
        )

    prompt = montar_prompt(pergunta.pergunta, chunks)
    resposta_texto = gerar_resposta(prompt)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO perguntas (pergunta, resposta) VALUES (%s, %s)",
                (pergunta.pergunta, resposta_texto),
            )
            conn.commit()
    finally:
        conn.close()

    fontes = sorted({c["titulo"] for c in chunks})
    return PerguntaOut(pergunta=pergunta.pergunta, resposta=resposta_texto, fontes=fontes)


class PerguntaHistoricoOut(BaseModel):
    id: int
    pergunta: str
    resposta: str
    criado_em: datetime


class HistoricoResumo(BaseModel):
    total: int


@app.get("/historico", response_model=list[PerguntaHistoricoOut])
def listar_historico(
    pergunta_exata: str | None = Query(default=None, description="Filtra por texto exato da pergunta"),
    limite: int = Query(default=10, ge=1, le=100),
    pagina: int = Query(default=1, ge=1),
):
    offset = (pagina - 1) * limite

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if pergunta_exata:
                cur.execute(
                    """
                    SELECT id, pergunta, resposta, criado_em
                    FROM perguntas
                    WHERE pergunta = %s
                    ORDER BY criado_em DESC
                    LIMIT %s OFFSET %s
                    """,
                    (pergunta_exata, limite, offset),
                )
            else:
                cur.execute(
                    """
                    SELECT id, pergunta, resposta, criado_em
                    FROM perguntas
                    ORDER BY criado_em DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limite, offset),
                )
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/historico/total", response_model=HistoricoResumo)
def total_perguntas():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM perguntas")
            return cur.fetchone()
    finally:
        conn.close()
