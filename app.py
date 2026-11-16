"""Painel principal de visualização e navegação da aplicação."""
import streamlit as st
from utils.ui import aviso_amostra, obter_amostra, obter_web
from utils.api_client import verificar_api



def pagina_inicial():
    st.title("📊 Transparência Brasil")
    st.write(
        "Painel de transparência e análise de despesas públicas, associado ao "
        "**ODS 16 — Paz, Justiça e Instituições Eficazes**. A aplicação mantém "
        "separadas a amostra ilustrativa e a base oficial declarada ao Siconfi."
    )
    st.sidebar.success("Selecione uma seção no menu para explorar o projeto.")
    st.sidebar.caption("FastAPI: " + ("online ✓" if verificar_api() else "offline — inicie uvicorn"))

    try:
        despesas = obter_amostra()
        web = obter_web()
    except (OSError, ValueError) as erro:
        st.error(f"Não foi possível carregar a base: {erro}")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Registros na amostra", len(despesas))
    col2.metric("Estados comparados", despesas["sigla"].nunique())
    col3.metric("Páginas Web catalogadas", len(web))

    aviso_amostra()
    st.subheader("Recursos preservados")
    st.markdown(
        """
    - **Gastos públicos:** filtros e gráficos de comparação por estado e função.
    - **Estatísticas:** composição percentual, despesa por habitante, rankings, comparação direta e perfis da amostra ilustrativa.
    - **Dados oficiais:** despesas declaradas ao Siconfi dos governos estaduais e distrital (2021–2025), após coleta e validação.
    - **Conteúdo da Web:** fontes institucionais, extração com Beautiful Soup e Selenium, estatísticas e nuvem de palavras.
    - **API FastAPI integrada:** gráficos e consultas GET por HTTP e formulário POST diretamente na interface.
    - **Assistente IA:** resumo e explicação de textos usando o Qwen local via FastAPI. A recuperação documental (RAG) ainda não está disponível.
    """
    )
    st.caption("Use o menu de navegação na barra lateral para abrir cada página.")


# Menu explícito: as páginas Arquivos e Preparação para IA permanecem no código,
# mas não são expostas na navegação do produto.
st.set_page_config(page_title="Transparência Brasil", page_icon="📊", layout="wide")
pagina = st.navigation([
    st.Page(pagina_inicial, title="App", icon="🏠", default=True),
    st.Page("pages/1_Gastos_publicos.py", title="Gastos públicos", icon="💰"),
    st.Page("pages/4_Estatisticas.py", title="Estatísticas", icon="📊"),
    st.Page("pages/8_Dados_Oficiais.py", title="Dados oficiais", icon="🏛️"),
    st.Page("pages/2_Conteudo_da_Web.py", title="Conteúdo da Web", icon="🌐"),
    st.Page("pages/5_API_FastAPI.py", title="API FastAPI", icon="🔌"),
    st.Page("pages/7_Assistente_IA.py", title="Assistente IA", icon="🧠"),
])
pagina.run()
