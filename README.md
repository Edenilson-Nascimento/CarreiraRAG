# CarreiraRAG

Assistente que responde perguntas sobre compatibilidade entre um currículo e
descrições de vagas, usando RAG (Retrieval-Augmented Generation) com
PostgreSQL + pgvector e a API da Claude.

## Stack
- Backend: FastAPI (Python)
- Banco: PostgreSQL + extensão pgvector
- IA: API da Anthropic (Claude)
- Frontend: Streamlit
- Infra: Docker Compose, deploy no Render