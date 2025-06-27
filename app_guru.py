import streamlit as st
from athena_loader import executar_athena_df
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# Configuração da página
st.set_page_config(page_title="🤖 Oráculo de Dados - MaisTODOS")
st.title("🤖 Oráculo de Dados - MaisTODOS")

# Função para carregar DataFrame com cache
@st.cache_data(show_spinner=False)
def load_df(query: str, database: str):
    return executar_athena_df(query, database)

# Inputs do usuário
database = st.text_input("Database Athena", value="pdgt_maistodos_credito")
query = st.text_area(
    "Query SQL",
    value=(
        "select * from pdgt_maistodos_credito.fl_report_credito_refactor where dt_merge >= date('2025-06-01')"
    )
)

if st.button("Inicializar Oráculo"):
    with st.spinner("Executando Athena e criando agente..."):
        # Carrega o DF e trata erros
        try:
            df = load_df(query, database)
            if df.empty:
                st.warning("A consulta retornou 0 registros.")
                st.stop()
        except Exception as e:
            st.error(f"Erro ao executar consulta Athena: {e}")
            st.stop()

        # (1) inicializa LLM e memória
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=st.secrets["openai"]["api_key"])
        memoria = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # (2) define prompt sem placeholders de histórico
        prompt = PromptTemplate(
            input_variables=["input"],
            template=(
                "Você é um assistente Analista de Negócios. Utilize os dados da última consulta Athena para responder "
                "de forma clara, objetiva e com insights que um analista de BI forneceria. Sempre justifique com base nas colunas "
                "e valores disponíveis. Pergunta: {input}"
            )
        )

        # (3) monta LLMChain
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            memory=memoria,
            verbose=False
        )

        # (4) cria agente DataFrame
        agent = create_pandas_dataframe_agent(
            llm=llm,  # passa o modelo diretamente
            df=df,
            verbose=False,
            allow_dangerous_code=True,
            max_iterations=100
        )

        # Armazena em session_state para o chat
        st.session_state.agent = agent
        st.session_state.memory = memoria
        st.success("Oráculo pronto! Pergunte abaixo.")

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