import streamlit as st
import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory


path_file_onboarding = st.secrets["path_file_onboarding"]

@st.cache_data
def load_df_cashback_onboarding():
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

# Cache para modelo e memória
@st.cache_resource
def get_model_and_memory():
    chat = ChatOpenAI(model= 'gpt-4.1-nano')
    memory = ConversationBufferMemory(return_messages=True, memory_key='chat_history')
    return chat, memory

df = load_df_cashback_onboarding()
chat, memory = get_model_and_memory()

def consulta_cashback_onboarding(pergunta, contexto_negocio='onboarding cashback'):
    prompt_template = ChatPromptTemplate.from_messages([
     ("system", 
         "Você é um analista de negócios especialista em cashback da Mais Todos. Sua responsabilidade é analisar o programa de onboarding de parceiros no cashback (30 dias) e fornecer insights acionáveis baseados em dados.\n\n"
         
         "CONTEXTO TEMPORAL:\n"
         "- Estamos analisando dados do programa de onboarding até julho de 2025\n" #### lembrar de alterar após conectar no lake
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
         " Só use os passos 3 e 4 quando necessário ou for pedido"
         
         "INSTRUÇÕES TÉCNICAS:\n"
         "- Formate números grandes com separadores (ex: R$ 1.234.567,89)\n"
         "- Use percentuais quando apropriado\n"
         "- Sempre importe as bibliotecas necessárias no código\n\n"
         "- Use tabelas, correlações e benchmarks do mercado para enriquecer a análise\n"
         
         "LIMITAÇÕES:\n"
         "Se não conseguir responder com os dados disponíveis, seja transparente sobre as limitações e sugira que dados adicionais seriam necessários."),
        MessagesPlaceholder(variable_name='chat_history'),
        ("user", 
         "Pergunta: {pergunta}\nContexto: {contexto_negocio}\n\n"
         "INSTRUÇÃO: Analise o DataFrame usando pandas, gere tabelas e forneça insights de negócio com recomendações práticas. "
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