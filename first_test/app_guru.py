import streamlit as st
from athena_loader import executar_athena_df
from langchain.agents import tool, create_openai_functions_agent, AgentExecutor
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from tools import estatisticas_credito_pf
#from langchain_openai import ChatOpenAI

AGENTES = {
    "Crédito PF": {
        "nome": "Agente de Crédito PF",
        "prompt": (
            "Você é um analista especialista em crédito para pessoa física (PF). "
            "Utilize os dados da consulta para analisar aprovações, reprovações, score e tendências. "
            "O DataFrame retornado refere-se à tabela refinada sobre propostas de pacientes e solicitações de crédito das financiadoras, "
            "com os seguintes campos:\n\n"
            "id: Identificador único\n"
            "id_funil_fluxo: ID do funil\n"
            "funil_fluxo: Descrição do funil\n"
            "tp_fluxo: Tipo de fluxo\n"
            "cliente_nome: Nome do cliente\n"
            "cliente_cpf: CPF\n"
            "cliente_cpf_num: CPF numérico\n"
            "pre_proposta_status: Status pré-proposta\n"
            "proposta_status: Status da proposta\n"
            "proposta_sub_status: Substatus da proposta\n"
            "financiadoras: Lista de financiadoras\n"
            "nm_financiadora: Nome da financiadora\n"
            "produto: Produto solicitado\n"
            "segmento: Segmento da operação\n"
            "vlr_requerido: Valor requerido\n"
            "vlr_total: Valor total\n"
            "unidade_negocio: Unidade de negócio\n"
            "cnpj: CNPJ texto\n"
            "cnpj_num: CNPJ numérico\n"
            "dt_criacao_pre_proposta: Data criação pré-proposta\n"
            "dt_criacao_proposta: Data criação proposta\n"
            "dt_criacao_oferta: Data criação oferta\n"
        ),
        "query_padrao": "SELECT * FROM pdgt_maistodos_credito.fl_report_credito_refactor WHERE dt_merge between date('2025-06-01') and date('2025-06-02')",
        "database_padrao": "pdgt_maistodos_credito"
    },
    "Cashback": {
        "nome": "Agente de Cashback",
        "prompt": (
            "Você é um analista especialista em cashback. Utilize os dados carregados para gerar insights, identificar padrões, "
            "explicar variações e sugerir melhorias nos processos de cashback."
        ),
        "query_padrao": "SELECT * FROM cashback_table LIMIT 1000",  # Ajust para real tabela de cashback
        "database_padrao": "database_cashback"
    }
}

# Configuração da página
st.set_page_config(page_title="🤖 Oráculo de Dados - MaisTODOS")
st.title("🤖 Oráculo de Dados - MaisTODOS")

# Função para carregar DataFrame com cache
@st.cache_data(show_spinner=False)
def load_df(query: str, database: str):
    return executar_athena_df(query, database)

agente_escolhido = st.selectbox(
    "Escolha o agente de análise:",
    options=list(AGENTES.keys()),
    format_func=lambda x: AGENTES[x]["nome"]
)
config = AGENTES[agente_escolhido]


if st.button("Inicializar Oráculo"):
    with st.spinner(f"Iniciando {config['nome']}..."):
        try:
            df = load_df(config["query_padrao"], config["database_padrao"])
            if df.empty:
                st.warning("A consulta retornou 0 registros.")
                st.stop()
            st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"Erro ao executar consulta Athena: {e}")
            st.stop()

        prompt = PromptTemplate(
            input_variables=["input"],
            template=config["prompt"] + "\nPergunta: {input}"
        )

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=st.secrets["openai"]["api_key"])
        memoria = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        llm_chain = LLMChain(llm=llm, prompt=prompt, memory=memoria, verbose=False)
        
        # Plugando sua tool personalizada
        tools = [estatisticas_credito_pf]

        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            verbose=True,
            allow_dangerous_code=True,
            max_iterations=30,
            additional_tools=tools
        )

        # executor_agent = AgentExecutor(
        #     agent=agent,
        #     tools=tools,
        #     verbose=True,
        #     handle_parsing_errors=True,
        #     max_iterations=5,
        #     max_execution_time=60
        # )

        st.session_state.agent = agent
        st.session_state.memory = memoria
        st.success(f"{config['nome']} pronto! Faça sua pergunta.")

# Chat interativo
if "agent" in st.session_state:
    pergunta = st.chat_input("Pergunte sobre os dados:")
    if pergunta:
        # Mostra pergunta do usuário
        st.chat_message("user").markdown(pergunta)
        try:
            resposta = st.session_state.agent.run(pergunta)
            st.chat_message("assistant").markdown(resposta)
        except Exception as e:
            st.chat_message("assistant").error(f"Erro ao rodar agente: {e}")