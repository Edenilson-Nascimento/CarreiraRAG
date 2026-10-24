import os
import time
import requests
import streamlit as st
import streamlit.components.v1 as components

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="CarreiraRAG", page_icon="💼")
st.title("💼 CarreiraRAG")
st.caption("Assistente de compatibilidade entre currículo e vagas, com RAG")


def verificar_e_acordar_backend():
    """Garante que o backend acordou do modo sleep antes de carregar o restante do app."""
    if st.session_state.get("backend_online", False):
        return True

    # Pede ao NAVEGADOR do visitante para acordar o backend (equivale a abrir o
    # link do backend numa aba). A resposta é opaca: só precisamos que o pedido saia.
    components.html(
        f"<script>fetch('{API_URL}/health', {{mode: 'no-cors'}}).catch(() => {{}});</script>",
        height=0,
    )

    status_placeholder = st.empty()
    tentativas = 15
    intervalo = 8

    for i in range(tentativas):
        try:
            resposta = requests.get(f"{API_URL}/health", timeout=15)
            if resposta.status_code == 200:
                status_placeholder.empty()
                st.session_state.backend_online = True
                return True
        except requests.exceptions.RequestException:
            pass

        status_placeholder.warning(
            f"⏳ Conectando ao servidor (instância gratuita inicializando)... "
            f"Tentativa {i + 1}/{tentativas}. Isso pode levar até 2 minutos."
        )
        time.sleep(intervalo)

    status_placeholder.error("❌ O servidor demorou para responder.")
    st.link_button("Abrir o servidor para acordá-lo", f"{API_URL}/health")
    st.caption('Quando aparecer {"status":"ok",...}, volte aqui e recarregue esta página.')
    return False


# Se o backend ainda não responder, interrompe a renderização para não travar nos requests
if not verificar_e_acordar_backend():
    st.stop()

# ----------------- Estado de Sessão -----------------
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "form_id" not in st.session_state:
    st.session_state.form_id = 0


# ----------------- Barra Lateral -----------------
with st.sidebar:
    st.header("📄 Cadastrar documento")

    n = st.session_state.form_id
    with st.form(f"form_cadastro_{n}"):
        tipo = st.selectbox("Tipo", ["curriculo", "vaga"], key=f"tipo_{n}")
        titulo = st.text_input(
            "Título (ex: Vaga Desenvolvedor Python ou Currículo João Silva)",
            key=f"titulo_{n}",
        )
        conteudo = st.text_area(
            "Conteúdo (ex: Informações sobre a vaga ou o candidato)",
            height=200,
            key=f"conteudo_{n}",
        )
        enviar = st.form_submit_button("Cadastrar", use_container_width=True)

    if "aviso_cadastro" in st.session_state:
        st.success(st.session_state.pop("aviso_cadastro"))

    if enviar:
        if not titulo or not conteudo:
            st.warning("Preencha título e conteúdo.")
        else:
            try:
                with st.spinner("Gerando embeddings e salvando..."):
                    resposta = requests.post(
                        f"{API_URL}/documentos",
                        json={"tipo": tipo, "titulo": titulo, "conteudo": conteudo},
                        timeout=120,
                    )
                if resposta.status_code == 201:
                    dados = resposta.json()
                    st.session_state.aviso_cadastro = (
                        f"Salvo em {dados['chunks_criados']} pedaço(s)."
                    )
                    st.session_state.form_id += 1
                    st.rerun()
                elif resposta.status_code in (502, 503, 504):
                    st.warning(
                        "O servidor está iniciando (plano gratuito). Seu texto foi mantido: "
                        "aguarde cerca de 1 minuto e clique em Cadastrar de novo."
                    )
                else:
                    try:
                        detalhe = resposta.json().get("detail", "erro inesperado")
                    except ValueError:
                        detalhe = "erro inesperado"
                    st.error(f"Não foi possível cadastrar: {detalhe}")
            except requests.exceptions.RequestException:
                st.warning(
                    "Não consegui falar com o servidor. Ele pode estar iniciando (plano gratuito). "
                    "Seu texto foi mantido: aguarde cerca de 1 minuto e tente de novo."
                )

    st.divider()
    st.header("📚 Documentos cadastrados")
    try:
        resposta_docs = requests.get(f"{API_URL}/documentos", timeout=90)
        resposta_docs.raise_for_status()
        docs = resposta_docs.json()
        titulos_unicos = sorted({d["titulo"] for d in docs})
        if titulos_unicos:
            for t in titulos_unicos:
                st.write(f"- {t}")
        else:
            st.write("Nenhum documento ainda.")
    except (requests.exceptions.RequestException, ValueError):
        st.info("Aguardando carregamento da lista de documentos...")

    st.write("---")
    st.caption("© 2026 - Edenilson Nascimento.")


# ----------------- Chat Principal -----------------
for autor, texto in st.session_state.mensagens:
    with st.chat_message(autor):
        st.write(texto)

pergunta = st.chat_input("Pergunte sobre compatibilidade entre currículo e vaga...")

if pergunta:
    st.session_state.mensagens.append(("user", pergunta))
    with st.chat_message("user"):
        st.write(pergunta)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Buscando contexto e gerando resposta..."):
                resposta = requests.post(
                    f"{API_URL}/perguntar", json={"pergunta": pergunta}, timeout=90
                )
            if resposta.status_code == 200:
                dados = resposta.json()
                texto_resposta = dados["resposta"]
                st.write(texto_resposta)
                if dados["fontes"]:
                    st.caption("Fontes: " + ", ".join(dados["fontes"]))
            else:
                try:
                    texto_resposta = resposta.json().get("detail", resposta.text)
                except ValueError:
                    texto_resposta = (
                        "O servidor não respondeu como esperado. Tente novamente em instantes."
                    )
                st.warning(texto_resposta)
        except requests.exceptions.RequestException:
            texto_resposta = (
                "Não consegui falar com o servidor. Ele pode estar iniciando (plano gratuito); "
                "aguarde cerca de 1 minuto e tente de novo."
            )
            st.warning(texto_resposta)
        st.session_state.mensagens.append(("assistant", texto_resposta))