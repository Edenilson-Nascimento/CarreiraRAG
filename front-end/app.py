import os
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="CarreiraRAG", page_icon="💼")
st.title("💼 CarreiraRAG")
st.caption("Assistente de compatibilidade entre currículo e vagas, com RAG")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


with st.sidebar:
    st.header("📄 Cadastrar documento")

    with st.form("form_cadastro", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["curriculo", "vaga"])
        titulo = st.text_input("Título (ex: Vaga Desenvolvedor Python ou Currículo João Silva)")
        conteudo = st.text_area("Conteúdo (ex: Informações sobre a vaga ou o candidato)", height=200)
        enviar = st.form_submit_button("Cadastrar", use_container_width=True)

    if enviar:
        if not titulo or not conteudo:
            st.warning("Preencha título e conteúdo.")
        else:
            with st.spinner("Gerando embeddings e salvando..."):
                resposta = requests.post(
                    f"{API_URL}/documentos",
                    json={"tipo": tipo, "titulo": titulo, "conteudo": conteudo},
                )
            if resposta.status_code == 201:
                dados = resposta.json()
                st.success(f"Salvo em {dados['chunks_criados']} pedaço(s).")
            else:
                st.error(f"Erro: {resposta.text}")

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
        st.info("O servidor está iniciando (plano gratuito). Aguarde cerca de 1 minuto e recarregue a página.")

    st.write("---")

    st.caption("© 2026 - Edenilson Nascimento.")


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
                    texto_resposta = "O servidor não respondeu como esperado. Tente novamente em instantes."
                st.warning(texto_resposta)
        except requests.exceptions.RequestException:
            texto_resposta = "Não consegui falar com o servidor. Ele pode estar iniciando (plano gratuito); aguarde cerca de 1 minuto e tente de novo."
            st.warning(texto_resposta)
        st.session_state.mensagens.append(("assistant", texto_resposta))


    
