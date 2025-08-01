import streamlit as st
import pandas as pd
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import matplotlib.pyplot as plt

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
    df_credito['dt_criacao_proposta'] = pd.to_datetime(df_credito['dt_criacao_proposta'], format='%Y-%m-%d', errors='coerce').dt.date
    df_credito['dt_criacao_oferta'] = pd.to_datetime(df_credito['dt_criacao_oferta'], format='%Y-%m-%d', errors='coerce').dt.date
    df_credito['dt_merge'] = pd.to_datetime(df_credito['dt_merge'], format='%Y-%m-%d', errors='coerce').dt.date
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
    gerar_grafico = False
    if "gráfico" in pergunta.lower() or "grafico" in pergunta.lower():
        gerar_grafico = True
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
        "Você é um analista de negócios especialista em crédito pessoa física da MaisTODOS.\n"
        "Sua responsabilidade é analisar o programa de crédito PF e fornecer insights acionáveis baseados em dados.\n"
        "Sempre explique o raciocínio e traga sugestões práticas para o negócio.\n"
        "A MaisTODOS é a fintech do grupo TODOS e do ecossistema cartão de todos e amor saúde que conecta cashback, pagamentos, conta digital e linhas de crédito.\n" 
        "Dentro desse portfólio, o crédito PF é voltado principalmente a clientes que precisam financiar tratamentos médicos, odontológicos e estéticos de forma rápida e sem a burocracia bancária tradicional.\n"
        
        "CONTEXTO TEMPORAL:\n"
        "- Estamos analisando dados do programa de crédito PF até julho de 2025\n" #### lembrar de alterar após conectar no lake
        "- O programa de crédito PF tem diversas financiadoras e cada financiadora tem sua política de crédito.\n"
        "- As datas são reais e representam períodos de aquisição do crédito \n\n"
        
        "DICIONÁRIO DE DADOS:\n"

        "Propósito desse DataFrame: Este dataframe centraliza, integra e rastreia toda a jornada do cliente PF na obtenção de crédito, desde a pré-análise até a concessão final.\n"
        "Os passos do funil/etapas do processo são esses, não troque a ordem:'p1 simulado', 'p1 aprovado', 'p2 simulado', 'p2 aprovado', 'cancelado' e 'contratado' e podem ser utilizados pela coluna 'funil_fluxo' e pode ser ordenado também pela coluna 'id_funil_fluxo'\n" 
        "Assegura governança, rastreabilidade e compliance, suportando decisões automáticas e manuais, monitoramento de risco, personalização de ofertas e otimização da operação de crédito.\n"
        "O cliente é simulado em diversas financiadoras e pode ser aprovado ou não em qualquer etapa.\n\n"
        
        "id_funil_fluxo: id de identificação da etapa do processo, essencial para ordenar as etapas do processo de crédito.\n"
        "funil_fluxo: Nome descritivo do estágio atual do processo (ex: 'p1 simulado', 'p1 aprovado', 'p2 simulado', 'p2 aprovado', 'cancelado' e 'contratado'), facilitando o acompanhamento operacional.\n"
        "tp_fluxo: Tipo de fluxo operacional (p1 ou p2), dispensável e não necessária.\n"
        "cliente_nascimento: Data de nascimento, utilizada para cálculo de idade e validação de faixa etária.\n"
        "cliente_idade: Idade calculada, critério essencial para elegibilidade e oferta de produtos.\n"
        "cliente_faixa_etaria: Faixa etária categorizada, possibilita análises demográficas e ajustes de risco.\n"
        "cliente_sexo: Gênero do cliente, útil para relatórios demográficos.\n"
        "cliente_pais: Localização do cliente, relevante para entendimento de perfil regional, políticas locais e risco geográfico.\n"
        "cliente_estado: Localização do cliente, relevante para entendimento de perfil regional, políticas locais e risco geográfico.\n"
        "cliente_cidade: Localização do cliente, relevante para entendimento de perfil regional, políticas locais e risco geográfico.\n"
        "cliente_score: Score de crédito, principal insumo de decisão automática de crédito.\n"
        "cliente_score_fx: Faixa do score, para segmentação de políticas e ofertas.\n"
        "cliente_status_civil: Estado civil, indicador de estabilidade ou risco associado ao perfil familiar.\n"
        "cliente_habitacao: Tipo de moradia (própria, alugada), indicador indireto de capacidade de pagamento e estabilidade.\n"
        "cliente_renda_mensal: Renda declarada, insumo primário para análise de capacidade de pagamento.\n"
        "fx_renda_mensal: Faixa categorizada da renda, utilizada em relatórios gerenciais e segmentação de produtos.\n"
        "cliente_patrimonio: Valor de bens declarados, suporte à avaliação de risco e ofertas diferenciadas.\n"
        "cliente_ocupacao, cliente_profissao: Ocupação e profissão, importantes para perfis de risco e ofertas personalizadas.\n"
        "cliente_tempo_servico: Tempo no emprego atual, indicador de estabilidade profissional.\n"
        "cliente_policamente_exposto: Sinaliza se o cliente é Pessoa Politicamente Exposta (PPE), essencial para compliance.\n"
        "cliente_relacao_pessoas_policamente_expostas: Identifica relação com PPEs, reforçando controles de prevenção à lavagem de dinheiro.\n"
        "pre_proposta_status: Status da pré-proposta.\n"
        "proposta_status: Status da proposta formal.\n"
        "proposta_sub_status: Substatus detalhado para acompanhamento granular do processo.\n"
        "financiadoras: Nome(s) das financiadoras que estão analisando ou participaram da proposta.\n"
        "vlr_requerido: Valor solicitado pelo cliente, base para cálculo de parcelas, taxas e análise de risco.\n"
        "vlr_total: Valor total aprovado ou contratado, fundamental para análise de conversão e carteira.\n"
        "unidade_negocio: Unidade de negócio responsável pela origem do crédito, importante para gestão interna.\n"
        "cnpj, cnpj_num: Identificação da empresa/unidade que está originando a proposta (quando aplicável).\n"
        "dt_criacao_pre_proposta, dt_criacao_proposta, dt_criacao_oferta: Datas de cada etapa, importantes para medir tempo de resposta, eficiência operacional e SLA.\n"
        "cliente_nome_adaptado: Versão padronizada ou abreviada do nome do cliente (útil para exibição, privacidade ou integração).\n"
        "nm_financiadora: Nome da financiadora que efetivou a concessão, para controle de carteira.\n"
        "produto: Produto de crédito ofertado, relevante para gestão de portfólio.\n"
        "segmento: Segmentação do produto (ex: medicina, odontologia, estética), importante para reporting e estratégia.\n"
        "dt_merge: Data de consolidação principal do registro, daqui que deve ser utilizada a data de referência.\n"
        "id_usuario_pre_proposta, nm_usuario_pre_proposta: Identificadores do responsável pela criação da pré-proposta.\n"
        "id_usuario_proposta, nm_usuario_proposta: Identificadores do responsável pela formalização da proposta.\n"
        "origem: Fonte de entrada da proposta, para análise de conversão por canal.\n"
        "resposta_integracao_p1, resposta_decisao_p1, resposta_error_p1, resposta_mensagem_p1: Campos para auditoria e análise das respostas automáticas da primeira etapa de decisão (P1).\n"
        "resposta_integracao_p2, resposta_decisao_p2, resposta_error_p2, resposta_message_p2: Campos equivalentes da segunda etapa de decisão (P2).\n"
        "dt_update_tb: Data/hora da última atualização do registro, garantindo governança, versionamento e compliance.\n"
         
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
        "- Use matplotlib.pyplot ou seaborn ou plotly para visualizações\n"
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
    prompt = prompt_template.format_messages(
        pergunta=pergunta,
        contexto_negocio=contexto_negocio,
        agent_scratchpad=[],
        chat_history=[]
    )
    resultado = agente.invoke(prompt)
    texto_resposta = resultado['output']

    fig = None 
    if gerar_grafico:
        fig, ax = plt.subplots()
        df_credito['cliente_idade'].hist(ax=ax)
        ax.set_title("Distribuição da idade dos clientes")
        ax.set_xlabel("Idade")
        ax.set_ylabel("Contagem")

    return texto_resposta, fig