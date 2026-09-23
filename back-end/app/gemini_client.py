import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODELO_EMBEDDING = "gemini-embedding-001"
MODELO_CHAT = "gemini-2.0-flash"
DIMENSOES_EMBEDDING = 768


def gerar_embedding(texto: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    resposta = client.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=texto,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=DIMENSOES_EMBEDDING,
        ),
    )
    return resposta.embeddings[0].values


def gerar_resposta(prompt: str) -> str:
    resposta = client.models.generate_content(
        model=MODELO_CHAT,
        contents=prompt,
    )
    return resposta.text
