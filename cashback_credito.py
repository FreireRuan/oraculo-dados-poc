import streamlit as st
import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv, find_dotenv
import os

# === Proteção por senha ===
def check_password():
    def password_entered():
        if st.session_state["password"] == "MaisTODOS":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        st.error("Senha incorreta")
        return False
    else:
        return True

if not check_password():
    st.stop()
# ===========================

# _ = load_dotenv(find_dotenv("credencial.env"))

# path_file_credito = os.getenv("path_file_credito")  
# path_file_onboarding = os.getenv("path_file_onboarding")  

path_file_credito = st.secrets["path_file_credito"]
path_file_onboarding = st.secrets["path_file_onboarding"]

# Cache para DataFrames
@st.cache_data # Carrega o DataFrame de onboarding
def load_df():
    df = pd.read_csv(path_file_onboarding)  
    df['dt_ativacao'] = pd.to_datetime(df['dt_ativacao'], format='%d/%m/%Y', errors='coerce')
    df['dt_fim_onboarding'] = pd.to_datetime(df['dt_fim_onboarding'], format='%d/%m/%Y', errors='coerce')
    df['tpv_meta'] = df['tpv_meta'].str.replace(',', '.').astype(float)
    df['vendas_meta'] = df['vendas_meta'].str.replace(',', '.').astype(float)
    df['tpv'] = df['tpv'].astype(float)
    df['vlr_cashback'] = df['vlr_cashback'].astype(float)
    df['vendas'] = df['vendas'].astype(float)
    df['usuarios_unicos'] = df['usuarios_unicos'].astype(int)
    df['perc_tpv'] = df['perc_tpv'].astype(float)
    df['perc_venda'] = df['perc_venda'].astype(float)
    df['ticket_medio'] = df['ticket_medio'].astype(float)
    df['vendas_usuarios'] = df['vendas_usuarios'].astype(float)
    df['receita_p_transacao'] = df['receita_p_transacao'].astype(float)
    df['nv_engaj_score'] = df['nv_engaj_score'].astype(float)
    return df

@st.cache_data
def load_df_credito():
    df_credito = pd.read_csv(path_file_credito)
    return df_credito

# Cache para modelo e memória
@st.cache_resource
def get_model_and_memory():
    chat = ChatOpenAI(model='gpt-3.5-turbo-0125', temperature=0.2)
    memory = ConversationBufferMemory(return_messages=True, memory_key='chat_history')
    return chat, memory

df = load_df()
df_credito = load_df_credito()
chat, memory = get_model_and_memory()

def consulta_cashback_onboarding(pergunta, contexto_negocio='onboarding cashback'):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", 
         "Você é um analista de dados e negócios da Mais Todos e analisa o onboarding de parceiros que entraram no programa de cashback. "
         "O programa de onboarding leva 30 dias e eles são classificados de acordo com o nível de engajamento. "
         "Você pode atuar como analista de dados e responder perguntas sobre os dados do onboarding, gerando gráficos e insights. "
         "Se não souber responder à pergunta, diga que não sabe e que precisa de mais informações. "
         "Sempre explique o raciocínio e traga sugestões práticas para o negócio."),
        MessagesPlaceholder(variable_name='chat_history'),
        ("user", 
         "Pergunta: {pergunta}\nContexto: {contexto_negocio}\nResponda à pergunta usando o DataFrame, gere insights, recomendações e possíveis ações para o negócio."),
        MessagesPlaceholder(variable_name='agent_scratchpad')
    ])
    agente = create_pandas_dataframe_agent(
        chat,
        df,
        verbose=True,
        agent_type='tool-calling',
        allow_dangerous_code=True,
        max_iterations=10,
        memory=memory  
    )
    prompt = prompt_template.format_messages(pergunta=pergunta, contexto_negocio=contexto_negocio, agent_scratchpad=[], chat_history=[])
    resultado = agente.invoke(prompt)
    return resultado['output']

def consulta_credito(pergunta, contexto_negocio='analista de credito'):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "Você é um analista de dados e crédito da Mais Todos e analisa os dados de simulação de crédito de clientes nas financiadoras parceiras. "
         "Os passos do funil são esses, não troque a ordem:'p1 simulado', 'p1 aprovado', 'p2 simulado', 'p2 aprovado', 'cancelado' e 'contratado'"
         "O cliente é simulado em várias etapas e financiadoras e pode ser aprovado ou não em qualquer etapa. "
         "Você pode atuar como analista de dados e responder perguntas sobre os dados de crédito, gerando gráficos e insights. "
         "Se não houver resposta à pergunta, responda que não sabe e que precisa de mais informações. "
         "Sempre explique o raciocínio e traga sugestões práticas para o negócio."),
        MessagesPlaceholder(variable_name='chat_history'),
        ("user",
         "Pergunta: {pergunta}\nContexto: {contexto_negocio}\nResponda à pergunta usando o DataFrame, gere insights, recomendações e possíveis ações para o negócio."),
        MessagesPlaceholder(variable_name='agent_scratchpad')
    ])
    agente = create_pandas_dataframe_agent(
        chat,
        df_credito,
        verbose=True,
        agent_type='tool-calling',
        allow_dangerous_code=True,
        max_iterations=10,
        memory=memory  
    )
    prompt = prompt_template.format_messages(pergunta=pergunta, contexto_negocio=contexto_negocio, agent_scratchpad=[], chat_history=[])
    resultado = agente.invoke(prompt)
    return resultado['output']

# Inicialize o histórico na sessão
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Oráculo Mais Todos")

produto = st.selectbox("Escolha o produto:", ["crédito", "cashback"])

# Exibe o histórico do chat
for msg in st.session_state.chat_history:
    st.markdown(f"**Você:** {msg['pergunta']}")
    st.markdown(f"**Oráculo:** {msg['resposta']}")

pergunta = st.text_input("Digite sua pergunta:")

if st.button("Enviar"):
    if produto == "crédito":
        resposta = consulta_credito(pergunta)
    else:
        resposta = consulta_cashback_onboarding(pergunta)
    # Adiciona ao histórico
    st.session_state.chat_history.append({
        "pergunta": pergunta,
        "resposta": resposta
    })
    st.rerun()  # Atualiza a tela para mostrar a nova mensagem