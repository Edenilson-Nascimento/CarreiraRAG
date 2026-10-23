# 💼 CarreiraRAG

> Um assistente que lê o seu currículo e as vagas que você quer, e responde perguntas como *"eu atendo os requisitos dessa vaga?"*, sem inventar nada.

**🔗 Teste agora:** https://carreirarag-frontend.onrender.com

> ⏳ O projeto está hospedado em planos gratuitos. Na primeira visita depois de um tempo sem uso, a página pode levar cerca de **1 minuto para abrir**. Se aparecer um aviso de erro, é só esperar um pouco e recarregar.

<!-- Adicione aqui um print da tela, por exemplo: ![Tela do CarreiraRAG](docs/img/chat.png) -->

---

## A ideia em 30 segundos

Quem procura emprego precisa, o tempo todo, comparar o próprio currículo com cada vaga: ler os requisitos, lembrar o que já fez e descobrir o que falta. É um trabalho repetitivo.

O CarreiraRAG faz essa leitura por você. Você cadastra o currículo e as vagas, escreve uma pergunta do jeito que falaria com uma pessoa, e recebe uma resposta **baseada apenas nos documentos que você cadastrou**, dizendo de onde tirou a informação.

## Veja como funciona

**Pergunta:** *Esse candidato tem experiência com Python e APIs?*

**Resposta:** *Sim. O currículo lista Python entre as habilidades e menciona FastAPI e integração com APIs de IA.* (Fonte: Currículo)

E quando a resposta não está nos documentos, o assistente admite em vez de inventar:

**Pergunta:** *Qual a capital da França?*

**Resposta:** *Não há informações suficientes nos documentos fornecidos para responder a essa pergunta.*

## Como usar

1. **Cadastre** um currículo e uma ou mais vagas, na barra lateral.
2. **Pergunte** no chat, em português normal.
3. **Leia** a resposta, que vem com o nome do documento de onde saiu.

## Por que isso é diferente de um chatbot comum?

Um chatbot comum responde "de memória" e às vezes inventa informações que parecem corretas. O CarreiraRAG funciona como uma **prova com consulta**: antes de responder, a IA procura nos seus documentos os trechos mais relacionados à pergunta e só então escreve a resposta, usando apenas esse material. Essa técnica se chama **RAG** (*Retrieval-Augmented Generation*, ou "geração de texto com busca prévia").

## Como funciona por dentro (versão simples)

```mermaid
flowchart LR
    A["Você"] --> B["Site (tela de chat)"]
    B --> C["Servidor"]
    C --> D[("Banco de documentos")]
    C --> E["IA (Gemini)"]
```

1. **Guardar:** o texto que você cadastra é cortado em pedaços pequenos e guardado no banco de dados.
2. **Entender o significado:** cada pedaço é transformado em uma espécie de "impressão digital de significado" (o nome técnico é *embedding*). Textos sobre assuntos parecidos geram impressões parecidas.
3. **Buscar:** quando você pergunta, o sistema compara a sua pergunta com todos os pedaços e separa os mais próximos em significado, mesmo que usem palavras diferentes.
4. **Responder:** a IA recebe a pergunta junto com esses trechos e escreve a resposta usando só eles.

## Detalhes técnicos

Para quem quer ver o que existe por baixo, abra as seções abaixo.

<details>
<summary><b>Decisões técnicas e problemas resolvidos</b></summary>

- **Busca por significado dentro do próprio Postgres (pgvector):** um único banco guarda os dados comuns e os vetores, o que simplifica a infraestrutura.
- **Textos divididos em pedaços com sobreposição:** um vetor para o currículo inteiro "dilui" os detalhes. Pedaços menores deixam a busca mais precisa, e a sobreposição evita cortar uma ideia no meio.
- **Tipos de embedding diferentes para documento e pergunta** (`RETRIEVAL_DOCUMENT` e `RETRIEVAL_QUERY`), o que melhora a qualidade da busca.
- **Índice HNSW em vez de IVFFlat:** o IVFFlat, criado com a tabela vazia, devolvia resultados incompletos em produção. O HNSW não depende de dados para ser "treinado" e resolveu o problema.
- **Duas camadas contra respostas inventadas:** um limite de distância na busca (trechos pouco relacionados são descartados) e uma regra explícita no prompt para admitir quando não há informação suficiente.
- **SQL escrito à mão com consultas parametrizadas**, o que protege contra SQL injection e deixa cada consulta visível.
- **Troca automática de modelo da IA:** se um modelo do Gemini estiver indisponível (erro 503), o servidor tenta o próximo da lista.

</details>

<details>
<summary><b>Rotas da API</b></summary>

Documentação interativa (Swagger): https://carreirarag-backend.onrender.com/docs

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica se a API e o banco estão no ar |
| POST | `/documentos` | Cadastra currículo ou vaga |
| GET | `/documentos` | Lista os documentos cadastrados |
| POST | `/perguntar` | Responde uma pergunta usando RAG |
| GET | `/historico` | Histórico de perguntas, com paginação e filtro |
| GET | `/historico/total` | Total de perguntas já feitas |

</details>

<details>
<summary><b>Rodar no seu computador</b></summary>

**Pré-requisitos:** Python 3.11+, Docker e uma chave gratuita da API do Gemini ([Google AI Studio](https://aistudio.google.com/apikey)).

```bash
git clone https://github.com/Edenilson-Nascimento/CarreiraRAG.git
cd CarreiraRAG
cp .env.example .env        # preencha GOOGLE_API_KEY
docker compose up -d        # sobe o Postgres com pgvector (porta 5433)
```

Servidor (backend):

```bash
cd back-end
python -m venv venv
source venv/bin/activate    # no Windows (Git Bash): source venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Site (frontend), em outro terminal:

```bash
cd front-end
python -m venv venv
source venv/bin/activate    # no Windows (Git Bash): source venv/Scripts/activate
pip install -r requirements.txt
streamlit run app.py
```

Abra http://localhost:8501. Para apontar o site para outro servidor, defina a variável de ambiente `API_URL`.

Para criar as tabelas em um banco Postgres já existente (por exemplo, na nuvem):

```bash
python docs/configurar_banco.py "postgresql://usuario:senha@host/banco"
```

**Publicação:** banco no [Neon](https://neon.tech) (PostgreSQL com pgvector) e dois serviços no [Render](https://render.com) (backend e frontend), construídos a partir dos Dockerfiles de `back-end/` e `front-end/`.

</details>

## Limitações e próximos passos

- Qualquer pessoa com o link pode usar o sistema: ainda não há login nem limite de uso.
- O cadastro é feito colando texto. Enviar o currículo em PDF é o próximo passo natural.
- Não há testes automatizados ainda.
- Por ser gratuito, o serviço "dorme" quando fica parado, e o primeiro acesso é mais lento.

## O que este projeto demonstra

| Competência | Onde aparece no projeto |
|---|---|
| Python | Backend (FastAPI) e frontend (Streamlit) |
| API REST e JSON | Rotas com validação de entrada e saída via Pydantic |
| API de IA generativa | Google Gemini, para embeddings e geração de respostas |
| Prompt engineering | Prompt com regras numeradas, contexto delimitado e instrução anti-invenção |
| RAG e banco vetorial | Chunking, embeddings e busca por similaridade com pgvector |
| SQL e PostgreSQL | Queries escritas à mão, paginação, agregação e índice HNSW |
| Docker e deploy | Dockerfiles, Render (aplicações) e Neon (banco) |
| Git/GitHub | Histórico de commits por etapa de desenvolvimento |

## Autor

**Edenilson Nascimento** · [GitHub](https://github.com/Edenilson-Nascimento)