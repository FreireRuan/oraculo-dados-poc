import streamlit as st
import pandas as pd
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

AGENTES = {
    "Crédito PF": {
        "nome": "Agente de Crédito PF",
        "prompt": (
            '''Você é um analista especialista em crédito para pessoa física (PF).
            Utilize os dados da consulta para analisar aprovações, reprovações, score e tendências.
            Os dados de consulta estão {df} dataframe refere-se à tabela refinada sobre propostas de pacientes e solicitações de crédito das financiadoras,
            com os seguintes campos:
                id: Identificador único
                id_funil_fluxo: ID do funil
                funil_fluxo: Descrição do funil
                tp_fluxo: Tipo de fluxo
                cliente_nome: Nome do cliente
                cliente_cpf: CPF
                cliente_cpf_num: CPF numérico
                pre_proposta_status: Status pré-proposta
                proposta_status: Status da proposta
                proposta_sub_status: Substatus da proposta
                financiadoras: Lista de financiadoras
                nm_financiadora: Nome da financiadora
                produto: Produto solicitado
                segmento: Segmento da operação
                vlr_requerido: Valor requerido
                vlr_total: Valor total
                unidade_negocio: Unidade de negócio
                cnpj: CNPJ texto
                cnpj_num: CNPJ numérico
                dt_criacao_pre_proposta: Data criação pré-proposta
                dt_criacao_proposta: Data criação proposta
                dt_criacao_oferta: Data criação oferta
        '''
        )
    }
}

st.set_page_config(page_title="🤖 Oráculo de Dados - CSV")
st.title("🤖 Oráculo de Dados - CSV")

@st.cache_data(show_spinner=False)
def load_df_csv(path: str):
    return pd.read_csv(path, delimiter=";", encoding="utf-8")

# Seleção de agente (expansão futura)
agente_escolhido = st.selectbox(
    "Escolha o agente de análise:",
    options=list(AGENTES.keys()),
    format_func=lambda x: AGENTES[x]["nome"]
)
config = AGENTES[agente_escolhido]

caminho_csv = st.text_input(
    "Caminho do arquivo CSV:",
    value=r"C:\Users\ruan.morais\Desktop\sandbox_freire\oraculo-dados\fl_report_credito_refactor_03_a_06_2025.csv"
)

# Inicializar apenas uma vez!
if "df" not in st.session_state and st.button("Inicializar Oráculo"):
    with st.spinner(f"Iniciando {config['nome']}..."):
        try:
            df = load_df_csv(caminho_csv)
            if df.empty:
                st.warning("O CSV está vazio.")
                st.stop()
            st.session_state['df'] = df
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao carregar o CSV: {e}")
            st.stop()

# Exibe o DataFrame
if "df" in st.session_state:
    st.dataframe(st.session_state['df'].head(10))

# Monta o chain se não existir
if "chain" not in st.session_state and "df" in st.session_state:
    prompt = ChatPromptTemplate.from_messages([
        ('system', config["prompt"]),
        ('placeholder', '{chat_history}'),
        ('user', '{input}')
    ])
    chat = ChatOpenAI(model="gpt-4o", api_key=st.secrets["openai"]["api_key"])
    chain = prompt | chat
    st.session_state['chain'] = chain
    st.session_state['memoria'] = ConversationBufferMemory()

# Agora sim, o chat aparece sempre que chain e memoria existem
if "chain" in st.session_state and "memoria" in st.session_state:
    memoria = st.session_state['memoria']

    # Mostra histórico (se quiser)
    for mensagem in memoria.buffer_as_messages:
        chat_display = st.chat_message(mensagem.type)
        chat_display.markdown(mensagem.content)

    # Input e resposta
    input_usuario = st.chat_input('Fale com o oráculo')
    if input_usuario:
        st.chat_message('human').markdown(input_usuario)
        resposta = st.session_state['chain'].invoke({
            'input': input_usuario,
            'chat_history': memoria.buffer_as_messages
        })['content']
        st.chat_message('ai').markdown(resposta)
        memoria.chat_memory.add_user_message(input_usuario)
        memoria.chat_memory.add_ai_message(resposta)
        st.session_state['memoria'] = memoria