"""Textos extraídos com Beautiful Soup e, opcionalmente, Selenium."""
import pandas as pd
import streamlit as st
from wordcloud import WordCloud

from utils.analises import palavras_frequentes
from utils.api_client import APIIndisponivel, consultar_conteudo_web
from utils.ui import obter_web

st.set_page_config(page_title="Conteúdo Web — TP3", page_icon="🌐", layout="wide")
st.title("🌐 Conteúdo coletado na Web")
st.caption("Requests + Beautiful Soup e coletor Selenium opcional, com fontes identificadas.")

try:
    web = consultar_conteudo_web()
    st.success("Conteúdo principal obtido via FastAPI: GET /conteudo-web.")
except (APIIndisponivel, ValueError) as erro:
    st.warning(f"API indisponível ({erro}); exibindo conteúdo Web local.")
    web = obter_web()

if web.empty:
    st.warning("Ainda não há conteúdo. Execute: python coleta_web.py")
    st.stop()

st.metric("Fontes Web catalogadas", len(web))
campos = [col for col in ("titulo", "url", "metodo", "data_coleta") if col in web.columns]
st.dataframe(web[campos], use_container_width=True, hide_index=True)

frequencias = palavras_frequentes(web["texto"].tolist())
if frequencias:
    tabela = pd.DataFrame(frequencias, columns=["Palavra", "Quantidade"])
    st.subheader("Palavras mais frequentes")
    st.bar_chart(tabela.set_index("Palavra"))
    st.subheader("Nuvem de palavras")
    nuvem = WordCloud(width=900, height=400, background_color="white").generate(
        " ".join([palavra for palavra, vezes in frequencias for _ in range(vezes)])
    )
    st.image(nuvem.to_array(), use_container_width=True)
else:
    st.info("Não existem textos suficientes para gerar estatísticas de palavras.")

st.subheader("Trechos catalogados")
for _, registro in web.iterrows():
    with st.expander(str(registro["titulo"])):
        st.write(str(registro["texto"]))
        st.caption("Fonte: " + str(registro["url"]))
