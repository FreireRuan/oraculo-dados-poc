import streamlit as st
import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

path_file_credito = st.secrets["path_file_credito"]

@st.cache_data
def load_df_credito():
    df_credito = pd.read_csv(path_file_credito)
    df_credito['cliente_nascimento'] = pd.to_datetime(df_credito['cliente_nascimento'], format='%Y-%m-%d', errors='coerce').dt.date
    df_credito['cliente_idade'] = df_credito['cliente_idade'].astype(int)
    df_credito['cliente_score'] = df_credito['cliente_score'].astype(float)
    df_credito['cliente_renda_mensal'] = df_credito['cliente_renda_mensal'].astype(float)
    df_credito['cliente_patrimonio'] = df_credito['cliente_patrimonio'].astype(float)
    df_credito['vlr_requerido'] = df_credito['vlr_requerido'].astype(float)
    df_credito['vlr_total'] = df_credito['vlr_total'].astype(float)
    df_credito['cnpj_num'] = df_credito['cnpj_num'].astype(int)
    df_credito['dt_criacao_pre_proposta'] = pd.to_datetime(df_credito['dt_criacao_pre_proposta'], format='%Y-%m-%d', errors='coerce').dt.date
    return df_credito

# Cache para modelo e memória
@st.cache_resource
def get_model_and_memory():
    chat = ChatOpenAI(model= 'gpt-4.1-nano')
    memory = ConversationBufferMemory(return_messages=True, memory_key='chat_history')
    return chat, memory

df_credito = load_df_credito()
chat, memory = get_model_and_memory()

def consulta_credito(pergunta, contexto_negocio='analista de credito'):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
        "Você é um analista de negócios especialista em crédito pessoa física da MaisTODOS.\n"
        "Sua responsabilidade é analisar o programa de crédito PF e fornecer insights acionáveis baseados em dados.\n"
        "Sempre explique o raciocínio e traga sugestões práticas para o negócio.\n"
        "Dentro desse portfólio, o crédito PF é voltado principalmente a clientes que precisam financiar tratamentos médicos, odontológicos e estéticos de forma rápida e sem a burocracia bancária tradicional.\n"
        
        "CONTEXTO TEMPORAL:\n"
        "- Estamos analisando dados do programa de crédito PF até julho de 2025\n"
        "- O programa de crédito PF tem diversas financiadoras e cada financiadora tem sua política de crédito.\n"
        "- As datas são reais e representam períodos de aquisição do crédito \n\n"
        
        "DICIONÁRIO DE DADOS:\n"

        "Propósito desse DataFrame: Este dataframe centraliza, integra e rastreia toda a jornada do cliente PF na obtenção de crédito, desde a pré-análise até a concessão final.\n"
        "Os passos do funil/etapas do processo são esses, não troque a ordem:'p1 simulado', 'p1 aprovado', 'p2 simulado', 'p2 aprovado', 'cancelado' e 'contratado' e podem ser utilizados pela coluna 'funil_fluxo' e pode ser ordenado também pela coluna 'id_funil_fluxo'\n" 
        "Assegura governança, rastreabilidade e compliance, suportando decisões automáticas e manuais, monitoramento de risco, personalização de ofertas e otimização da operação de crédito.\n"
        "O cliente é simulado em diversas financiadoras e pode ser aprovado ou não em qualquer etapa.\n\n"
        
        "id_funil_fluxo: id de identificação da etapa do processo, essencial para ordenar as etapas do processo de crédito.\n"
        "funil_fluxo: Nome descritivo do estágio atual do processo (ex: 'p1 simulado', 'p1 aprovado', 'p2 simulado', 'p2 aprovado', 'cancelado' e 'contratado'), facilitando o acompanhamento operacional.\n"
        "cliente_nascimento: Data de nascimento.\n"
        "cliente_idade: Idade calculada.\n"
        "cliente_faixa_etaria: Faixa etária categorizada.\n"
        "cliente_sexo: Gênero do cliente.\n"
        "cliente_pais: Localização do cliente.\n"
        "cliente_estado: Localização do cliente.\n"
        "cliente_cidade: Localização do cliente.\n"
        "cliente_score: Score de crédito.\n"
        "cliente_score_fx: Faixa do score.\n"
        "cliente_status_civil: Estado civil.\n"
        "cliente_habitacao: Tipo de moradia (própria, alugada).\n"
        "cliente_renda_mensal: Renda declarada.\n"
        "fx_renda_mensal: Faixa categorizada da renda.\n"
        "cliente_patrimonio: Valor de bens declarados.\n"
        "cliente_ocupacao, cliente_profissao: Ocupação e profissão.\n"
        "cliente_tempo_servico: Tempo no emprego atual.\n"
        "cliente_policamente_exposto: Sinaliza se o cliente é Pessoa Politicamente Exposta (PPE).\n"
        "cliente_relacao_pessoas_policamente_expostas: Identifica relação com PPEs.\n"
        "financiadoras: Nome(s) das financiadoras que estão analisando ou participaram da proposta.\n"
        "vlr_requerido: Valor solicitado pelo cliente.\n"
        "vlr_total: Valor total aprovado ou contratado.\n"
        "unidade_negocio: Unidade de negócio responsável pela origem do crédito.\n"
        "cnpj, cnpj_num: Identificação da empresa/unidade que está originando a proposta.\n"
        "dt_criacao_pre_proposta: Data da criação da pré proposta.\n"
        "nm_financiadora: Nome da financiadora que efetivou a concessão.\n"
        "produto: Produto de crédito.\n"
        "segmento: Segmentação do produto (ex: medicina, odontologia, estética).\n"
        "id_usuario_pre_proposta, nm_usuario_pre_proposta: Identificadores do responsável pela criação da pré-proposta.\n"
        "id_usuario_proposta, nm_usuario_proposta: Identificadores do responsável pela formalização da proposta.\n"
        "origem: Fonte de entrada da proposta, para análise de conversão por canal.\n"
         
        "FUNÇÔES\n"
        "- Para calcular o valor contratado, use o id_funil_fluxo = 7 e some o vlr_total. Com isso, o valor contratado poderá ser exibido em segmentos, datas, financiadoras entre outras dimensões."

        "COMPORTAMENTO ESPERADO:\n"
        "- Sempre use pandas para cálculos e análises\n"
        "- Apresente dados de forma didática e organizada\n"
        "- Seja proativo em identificar padrões, tendências e oportunidades\n"
        "- Contextualize números com comparações e benchmarks quando relevante\n"
        "- Considere o contexto temporal ao analisar tendências\n\n"
        
        "ESTRUTURA DE RESPOSTA:\n"
        "1. **ANÁLISE**: Apresente os dados relevantes com cálculos\n"
        "2. **INSIGHTS**: Interprete os resultados e identifique padrões\n"
        "3. **RECOMENDAÇÕES**: Sugira ações práticas e específicas\n"
        "4. **PRÓXIMOS PASSOS**: Indique análises complementares se necessário\n\n"
        " Só use os passos 3 e 4 quando realmente for necessário ou for pedido"
        
        "INSTRUÇÕES TÉCNICAS:\n"
        "- Para análises temporais, considere agrupamentos por mês/semana\n"
        "- Formate números grandes com separadores (ex: R$ 1.234.567,89)\n"
        "- Use percentuais quando apropriado\n"
        "- Sempre importe as bibliotecas necessárias no código\n\n"

        "LIMITAÇÕES:\n"
        "Se não conseguir responder com os dados disponíveis, seja transparente sobre as limitações e sugira que dados adicionais seriam necessários."),
        MessagesPlaceholder(variable_name='chat_history'),
        ("user",
        "Pergunta: {pergunta}\nContexto: {contexto_negocio}\n\n"
        "INSTRUÇÃO: Analise o DataFrame usando pandas e forneça insights de negócio com recomendações práticas. "
        "Seja específico com números e percentuais, e sempre explique o significado dos resultados para o negócio. "
        "Lembre-se que estamos em 2025 e os dados refletem o programa de crédito pessoa física atual."),
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