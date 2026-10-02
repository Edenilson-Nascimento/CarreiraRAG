import os
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODELO_EMBEDDING = "gemini-embedding-001"
MODELOS_CHAT_PRIORIDADE = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-3.8-flash",
]
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
    ultimo_erro = None
    for modelo in MODELOS_CHAT_PRIORIDADE:
        try:
            resposta = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            return resposta.text
        except ServerError as e:
            # Captura erro 503 e tenta o próximo modelo da lista
            ultimo_erro = e
            time.sleep(1)
            continue
        except Exception as e:
            ultimo_erro = e
            break

    raise ultimo_erro