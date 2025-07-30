import streamlit as st
import pandas as pd
from pandasai import PandasAI
from pandasai.llm.openai import OpenAI
from athena_loader import executar_athena_df
from tools import estatisticas_credito_pf

# Configuração
st.set_page_config(page_title="🤖 Oráculo de Dados - MaisTODOS")
st.title("🤖 Oráculo de Dados - MaisTODOS")

# Carregar DataFrame (com Athena)
@st.cache_data(show_spinner=False)
def load_df(query: str, database: str):
    return executar_athena_df(query, database)

# Seletor de agente
AGENTES = {
    "Crédito PF": {
        "query_padrao": "SELECT * FROM pdgt_maistodos_credito.fl_report_credito_refactor WHERE dt_merge >= date('2025-06-01') LIMIT 1000",
        "database_padrao": "pdgt_maistodos_credito"
    },
    "Cashback": {
        "query_padrao": "SELECT * FROM cashback_table LIMIT 1000",
        "database_padrao": "database_cashback"
    }
}
agente_escolhido = st.selectbox(
    "Escolha o agente de análise:",
    options=list(AGENTES.keys())
)
config = AGENTES[agente_escolhido]

# Inicialização do DataFrame
if st.button("Inicializar Oráculo"):
    with st.spinner("Carregando dados..."):
        df = load_df(config["query_padrao"], config["database_padrao"])
        if df.empty:
            st.warning("A consulta retornou 0 registros.")
            st.stop()
        st.session_state.df = df
        st.dataframe(df.head(10))
        st.success("Base carregada! Agora pergunte ao Oráculo.")

# Instancia o PandasAI se já tem DataFrame carregado
if "df" in st.session_state:
    # Configuração do LLM (OpenAI, mas pode ser outros compatíveis)
    llm = OpenAI(api_token=st.secrets["openai"]["api_key"])
    pandas_ai = PandasAI(llm)

    st.write("Colunas disponíveis:", st.session_state.df.columns.tolist())
    query = st.text_input("Pergunte sobre os dados:")

    if query:
        with st.spinner("Pensando..."):
            resposta = pandas_ai.run(st.session_state.df, prompt=query)
            st.markdown(f"**Resposta:** {resposta}")

    # (Opcional) Botão para estatísticas customizadas com sua tool
    if agente_escolhido == "Crédito PF":
        if st.button("Resumo Executivo Crédito PF"):
            resumo = estatisticas_credito_pf(st.session_state.df)
            st.markdown(resumo)
