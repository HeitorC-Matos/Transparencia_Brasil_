from collections import Counter
from pathlib import Path
import re

import pandas as pd
import streamlit as st
from wordcloud import WordCloud

st.set_page_config(
    page_title="Transparência Brasil - TP2",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_DADOS = BASE_DIR / "data" / "amostra_dados.csv"
ARQUIVO_WEB = BASE_DIR / "data" / "conteudo_web.csv"


@st.cache_data
def carregar_csv(caminho):
    return pd.read_csv(caminho)


def formatar_reais(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# O session_state mantém os dados enviados pelo usuário durante a sessão.
if "dados_upload" not in st.session_state:
    st.session_state["dados_upload"] = None


df = carregar_csv(ARQUIVO_DADOS)

st.title("📊 Transparência Brasil - TP2")
st.caption(
    "Evolução da aplicação do TP1 para visualização de gastos públicos e "
    "conteúdo obtido da Web, relacionada ao ODS 16."
)

aba_dados, aba_web, aba_arquivos = st.tabs(
    ["Gastos públicos", "Conteúdo da Web", "Upload e Download"]
)


with aba_dados:
    st.header("Comparação de gastos públicos")

    estados = st.multiselect(
        "Selecione os estados:",
        options=sorted(df["estado"].unique()),
        default=sorted(df["estado"].unique()),
    )

    funcao = st.selectbox(
        "Selecione a função de despesa:",
        options=sorted(df["funcao"].unique()),
    )

    filtrado = df[
        (df["estado"].isin(estados)) &
        (df["funcao"] == funcao)
    ].copy()

    if filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros escolhidos.")
    else:
        total = filtrado["valor_despesa"].sum()
        st.metric("Total da despesa selecionada", formatar_reais(total))

        grafico = filtrado.set_index("estado")[["valor_despesa"]]
        st.bar_chart(grafico)

        st.subheader("Dados filtrados")
        tabela = filtrado[
            ["estado", "sigla", "ano", "funcao", "valor_despesa", "populacao"]
        ].copy()
        tabela["valor_despesa"] = tabela["valor_despesa"].apply(formatar_reais)
        st.dataframe(tabela, use_container_width=True, hide_index=True)


with aba_web:
    st.header("Conteúdo extraído da Web")
    st.write(
        "Os dados desta seção são gerados pelo arquivo `coleta_web.py`, "
        "utilizando Requests e Beautiful Soup."
    )

    if not ARQUIVO_WEB.exists():
        st.warning(
            "O arquivo conteudo_web.csv ainda não existe. "
            "Execute no terminal: python coleta_web.py"
        )
    else:
        web = carregar_csv(ARQUIVO_WEB).fillna("")

        st.metric("Páginas coletadas", len(web))
        st.dataframe(web[["titulo", "url"]], use_container_width=True, hide_index=True)

        texto = " ".join(web["texto"].astype(str))
        palavras = re.findall(r"[A-Za-zÀ-ÿ]{4,}", texto.lower())

        stopwords = {
            "para", "como", "mais", "pela", "pelo", "com", "dos", "das",
            "uma", "que", "por", "nos", "nas", "aos", "das", "seus", "suas"
        }
        palavras = [p for p in palavras if p not in stopwords]

        if palavras:
            contagem = Counter(palavras).most_common(10)
            freq = pd.DataFrame(contagem, columns=["Palavra", "Quantidade"])

            st.subheader("Palavras mais frequentes")
            st.bar_chart(freq.set_index("Palavra"))

            st.subheader("Nuvem de palavras")
            nuvem = WordCloud(
                width=900,
                height=400,
                background_color="white",
            ).generate(" ".join(palavras))
            st.image(nuvem.to_array(), use_container_width=True)


with aba_arquivos:
    st.header("Upload de arquivo CSV")

    arquivo = st.file_uploader("Selecione um arquivo CSV", type="csv")

    if arquivo is not None:
        dados_enviados = pd.read_csv(arquivo)
        st.session_state["dados_upload"] = dados_enviados

    if st.session_state["dados_upload"] is not None:
        st.success("Arquivo carregado durante esta sessão.")
        st.dataframe(
            st.session_state["dados_upload"],
            use_container_width=True,
            hide_index=True,
        )

        # Se o CSV tiver as mesmas colunas da base principal, ele complementa os dados.
        if set(df.columns).issubset(st.session_state["dados_upload"].columns):
            base_complementada = pd.concat(
                [df, st.session_state["dados_upload"][df.columns]],
                ignore_index=True,
            )
            st.write(f"Base original + arquivo enviado: {len(base_complementada)} registros.")
            st.subheader("Base complementada")
            st.dataframe(base_complementada, use_container_width=True, hide_index=True)
        else:
            st.info(
                "Para complementar a base principal, o CSV enviado deve possuir "
                "as mesmas colunas de amostra_dados.csv."
            )

        if st.button("Limpar arquivo enviado"):
            st.session_state["dados_upload"] = None
            st.rerun()

    st.header("Download dos dados")
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Baixar base de gastos públicos em CSV",
        data=csv,
        file_name="dados_transparencia_brasil.csv",
        mime="text/csv",
    )
