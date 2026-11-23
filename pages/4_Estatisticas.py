"""Dashboard oficial de Gastos públicos — nome histórico do arquivo preservado.

A página antiga da amostra ilustrativa não é mais exibida no menu.
"""
import streamlit as st

from utils.dashboard_ui import exibir_dashboard

st.set_page_config(page_title="Gastos públicos", page_icon="💰", layout="wide")
st.title("💰 Gastos públicos")
st.caption("Dashboard nacional • Dados oficiais do Siconfi • Estatísticas e insights com Qwen")
exibir_dashboard()
