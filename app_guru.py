import streamlit as st
from athena_loader import executar_athena_df
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.memory import ConversationBufferMemory

# Configuração da página
st.set_page_config(page_title="🤖 Oráculo de Dados - MaisTODOS")
st.title("🤖 Oráculo de Dados - MaisTODOS")

# Inputs iniciais
database = st.text_input(
    "Database Athena", 
    value="pdgt_maistodos_credito"
)
query = st.text_area(
    "Query SQL",
    value="""
SELECT *
FROM pdgt_maistodos_credito.fl_report_credito_refactor
LIMIT 100
"""
)

# Inicializa agente ao executar Athena
if st.button("Inicializar Oráculo"):
    with st.spinner("Executando Athena e criando agente..."):
        df = executar_athena_df(query, database)
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=st.secrets["openai"]["api_key"])
        memoria = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            verbose=False,
            memory=memoria,
            allow_dangerous_code=True
        )
        st.session_state.agent = agent
        st.session_state.memoria = memoria
        st.success("Oráculo pronto! Pergunte abaixo.")

# Chat interativo
if "agent" in st.session_state:
    pergunta = st.chat_input("Pergunte sobre os dados:")
    if pergunta:
        st.chat_message("user").markdown(pergunta)
        resposta = st.session_state.agent.invoke({"input": pergunta})
        st.chat_message("assistant").markdown(resposta)