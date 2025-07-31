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
    df['dt_ativacao'] = pd.to_datetime(df['dt_ativacao'], format='%Y-%m-%d', errors='coerce').dt.date
    df['dt_fim_onboarding'] = pd.to_datetime(df['dt_fim_onboarding'], format='%Y-%m-%d', errors='coerce').dt.date
    df['tpv_meta'] = df['tpv_meta'].astype(float)
    df['vendas_meta'] = df['vendas_meta'].astype(float)
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
    df['cliente_nascimento'] = pd.to_datetime(df['cliente_nascimento'], format='%Y-%m-%d', errors='coerce').dt.date
    df['cliente_idade'] = df['cliente_idade'].astype(int)
    df['cliente_score'] = df['cliente_score'].astype(int)
    df['cliente_renda_mensal'] = df['cliente_renda_mensal'].astype(float)
    df['cliente_patrimonio'] = df['cliente_patrimonio'].astype(float)
    df['cliente_tempo_servico'] = df['cliente_tempo_servico'].astype(int)
    df['vlr_requerido'] = df['vlr_requerido'].astype(float)
    df['vlr_total'] = df['vlr_total'].astype(float)
    df['cnpj_num'] = df['cnpj_num'].astype(int)
    df['dt_criacao_pre_proposta'] = pd.to_datetime(df['dt_criacao_pre_proposta'], format='%Y-%m-%d', errors='coerce').dt.date
    df['dt_criacao_proposta'] = pd.to_datetime(df['dt_criacao_proposta'], format='%Y-%m-%d', errors='coerce').dt.date
    df['dt_criacao_oferta'] = pd.to_datetime(df['dt_criacao_oferta'], format='%Y-%m-%d', errors='coerce').dt.date
    df['dt_merge'] = pd.to_datetime(df['dt_merge'], format='%Y-%m-%d', errors='coerce').dt.date
    return df_credito

# Cache para modelo e memória
@st.cache_resource
def get_model_and_memory():
    chat = ChatOpenAI(model= 'gpt-4-turbo')
    memory = ConversationBufferMemory(return_messages=True, memory_key='chat_history')
    return chat, memory

df = load_df()
df_credito = load_df_credito()
chat, memory = get_model_and_memory()

def consulta_cashback_onboarding(pergunta, contexto_negocio='onboarding cashback'):
    prompt_template = ChatPromptTemplate.from_messages([
     ("system", 
         "Você é um analista de negócios especialista em cashback da Mais Todos. Sua responsabilidade é analisar o programa de onboarding de parceiros no cashback (30 dias) e fornecer insights acionáveis baseados em dados.\n\n"
         
         "CONTEXTO TEMPORAL:\n"
         "- Estamos analisando dados do programa de onboarding até julho de 2025\n"
         "- O programa de onboarding tem duração de 30 dias corridos\n"
         "- As datas são reais e representam períodos de ativação e conclusão do onboarding\n\n"
         
         "DICIONÁRIO DE DADOS:\n"
         "• dt_ativacao: Data de início do onboarding do parceiro (formato YYYY-MM-DD)\n"
         "• dt_fim_onboarding: Data de término do período de onboarding (30 dias após ativação)\n"
         "• tpv_meta: Meta de TPV (Total Payment Volume) estabelecida para o parceiro no onboarding\n"
         "• vendas_meta: Meta de número de vendas estabelecida para o parceiro no onboarding\n"
         "• tpv: TPV real alcançado pelo parceiro durante o onboarding\n"
         "• vlr_cashback: Valor total de cashback pago ao parceiro no período\n"
         "• vendas: Número real de vendas realizadas pelo parceiro\n"
         "• usuarios_unicos: Quantidade de usuários únicos que compraram do parceiro\n"
         "• perc_tpv: Percentual de atingimento da meta de TPV (tpv/tpv_meta * 100)\n"
         "• perc_venda: Percentual de atingimento da meta de vendas (vendas/vendas_meta * 100)\n"
         "• ticket_medio: Valor médio por transação (tpv/vendas)\n"
         "• vendas_usuarios: Média de vendas por usuário único (vendas/usuarios_unicos)\n"
         "• receita_p_transacao: Receita média por transação para a empresa\n"
         "• nv_engaj_score: Score de engajamento do parceiro (0-100, onde 100 é máximo engajamento)\n\n"
         
         "COMPORTAMENTO ESPERADO:\n"
         "- Sempre use pandas para cálculos e análises\n"
         "- Crie visualizações (gráficos) sempre que possível para ilustrar insights\n"
         "- Apresente dados de forma didática e organizada\n"
         "- Seja proativo em identificar padrões, tendências e oportunidades\n"
         "- Contextualize números com comparações e benchmarks quando relevante\n"
         "- Considere o contexto temporal ao analisar tendências\n\n"
         
         "ESTRUTURA DE RESPOSTA:\n"
         "1. **ANÁLISE**: Apresente os dados relevantes com cálculos\n"
         "2. **INSIGHTS**: Interprete os resultados e identifique padrões\n"
         "3. **RECOMENDAÇÕES**: Sugira ações práticas e específicas\n"
         "4. **PRÓXIMOS PASSOS**: Indique análises complementares se necessário\n\n"
         
         "INSTRUÇÕES TÉCNICAS:\n"
         "- Use matplotlib.pyplot ou seaborn para visualizações\n"
         "- Para análises temporais, considere agrupamentos por mês/semana\n"
         "- Formate números grandes com separadores (ex: R$ 1.234.567,89)\n"
         "- Use percentuais quando apropriado\n"
         "- Sempre importe as bibliotecas necessárias no código\n\n"
         
         "LIMITAÇÕES:\n"
         "Se não conseguir responder com os dados disponíveis, seja transparente sobre as limitações e sugira que dados adicionais seriam necessários."),
        MessagesPlaceholder(variable_name='chat_history'),
        ("user", 
         "Pergunta: {pergunta}\nContexto: {contexto_negocio}\n\n"
         "INSTRUÇÃO: Analise o DataFrame usando pandas, gere visualizações quando apropriado, e forneça insights de negócio com recomendações práticas. "
         "Seja específico com números e percentuais, e sempre explique o significado dos resultados para o negócio. "
         "Lembre-se que estamos em 2025 e os dados refletem o programa de onboarding atual."),
        MessagesPlaceholder(variable_name='agent_scratchpad')
    ])
    agente = create_pandas_dataframe_agent(
        chat,
        df,
        verbose=True,
        agent_type='tool-calling',
        allow_dangerous_code=True,
        max_iterations=100,
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