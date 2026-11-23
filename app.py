"""Apresentação e navegação do projeto Transparência Brasil.

Os gráficos e a IA fiscal estão concentrados na seção Gastos públicos.
"""

import streamlit as st
from utils.api_client import verificar_api


def pagina_inicial():
    st.title("📊 Transparência Brasil")
    st.sidebar.success("Selecione uma seção no menu para explorar o projeto.")
    st.sidebar.caption("FastAPI: " + ("online ✓" if verificar_api() else "offline — inicie uvicorn"))

    st.markdown(
        "O **Transparência Brasil** é uma aplicação de consulta e análise de despesas "
        "públicas estaduais e distritais. Seu objetivo é facilitar o acesso aos dados, "
        "a comparação entre unidades da Federação e a compreensão de informações "
        "fiscais com apoio da inteligência artificial."
    )
    st.caption("Projeto acadêmico de Ciência de Dados • Transparência e governança pública • ODS 16")

    st.subheader("O que você encontra aqui")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 💰 Gastos públicos")
        st.write(
            "Dashboard interativo com as 27 UFs, filtros de 2021 a 2025, gráficos, "
            "rankings, comparações e insights produzidos pelo Qwen local."
        )
    with col2:
        st.markdown("### 🏛️ Dados oficiais")
        st.write(
            "Consulta dos registros declarados ao Siconfi, critérios de coleta, "
            "cobertura, fontes e exportação dos dados."
        )
    with col3:
        st.markdown("### 🧠 Assistente IA")
        st.write(
            "Perguntas sobre dados fiscais, sumarização de documentos coletados "
            "e processamento de textos com o Qwen."
        )

    st.subheader("Do dado à informação")
    st.markdown(
        "**1. Coleta:** API do Siconfi e conteúdos públicos obtidos por Requests/Beautiful Soup e Selenium.\n\n"
        "**2. Tratamento:** verificação de estrutura, seleção das funções fiscais e organização dos textos.\n\n"
        "**3. Análise:** indicadores, rankings, séries históricas e comparações calculados em Python.\n\n"
        "**4. Inteligência artificial:** Qwen local para resumir documentos e explicar resultados já calculados.\n\n"
        "**5. Apresentação:** dashboards, filtros, perguntas, resultados e referências para conferência."
    )
    st.info(
        "Os dados fiscais abrangem Educação, Saúde e Segurança Pública, no 6º bimestre "
        "de 2021 a 2025, conforme declarações ao Siconfi (RREO, Anexo 02). "
        "Os valores são despesas liquidadas nominais, não incluem municípios nem "
        "todas as funções de governo e não comprovam eficiência dos serviços públicos."
    )
    with st.expander("Recursos preservados do Transparência Brasil"):
        st.subheader("Recursos preservados")
        st.markdown(
            "- **Gastos públicos:** dashboard oficial, análises detalhadas e explicações com Qwen.\n"
            "- **Dados oficiais:** registros, fonte e metodologia do Siconfi.\n"
            "- **Conteúdo da Web:** textos coletados de sites institucionais.\n"
            "- **Assistente IA:** sumarização, consultas fiscais e texto livre.\n"
            "- **API FastAPI:** serviços, contratos de resposta e tratamento de erros.\n"
            "- **Amostra ilustrativa histórica:** preservada no código e nos testes, fora do menu."
        )


# A navegação explícita mantém páginas históricas no repositório sem apresentá-las no menu.
st.set_page_config(page_title="Transparência Brasil", page_icon="📊", layout="wide")
pagina = st.navigation([
    st.Page(pagina_inicial, title="App", icon="🏠", default=True),
    st.Page("pages/4_Estatisticas.py", title="Gastos públicos", icon="💰"),
    st.Page("pages/8_Dados_Oficiais.py", title="Dados oficiais", icon="🏛️"),
    st.Page("pages/2_Conteudo_da_Web.py", title="Conteúdo da Web", icon="🌐"),
    st.Page("pages/5_API_FastAPI.py", title="API FastAPI", icon="🔌"),
    st.Page("pages/7_Assistente_IA.py", title="Assistente IA", icon="🧠"),
])
pagina.run()
