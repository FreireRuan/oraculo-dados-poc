import pandas as pd
from langchain.agents import tool, create_openai_functions_agent, AgentExecutor

@tool
def estatisticas_credito_pf(df) -> str:
    """
    Gera resumo executivo de estatísticas para Crédito PF a partir de um DataFrame.
    Indicado para DataFrames resultantes do Athena com colunas padronizadas.
    """
    try:
        required_cols = [
            "proposta_status", "funil_fluxo", "vlr_total", "financiadoras", "nm_financiadora", 
            "segmento", "cliente_cpf", "dt_criacao_proposta"
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return f"Erro: As colunas obrigatórias não estão presentes: {', '.join(missing)}"
        
        total_propostas = len(df)
        aprovadas = df[df["funil_fluxo"].str.lower().str.contains("contratado")]
        reprovadas = df[df["funil_fluxo"].str.lower().str.contains("reprov")]
        
        pct_aprov = len(aprovadas) / total_propostas * 100 if total_propostas else 0
        pct_reprov = len(reprovadas) / total_propostas * 100 if total_propostas else 0

        valor_aprovado = aprovadas["vlr_total"].sum()
        valor_reprovado = reprovadas["vlr_total"].sum()
        ticket_medio_aprov = aprovadas["vlr_total"].mean() if not aprovadas.empty else 0
        ticket_medio_reprov = reprovadas["vlr_total"].mean() if not reprovadas.empty else 0
        ticket_medio_geral = df["vlr_total"].mean() if not df.empty else 0

        top_financiadoras = aprovadas.groupby("nm_financiadora")["vlr_total"].sum().nlargest(3)
        propostas_por_cliente = df["cliente_cpf"].nunique()
        top_segmentos = aprovadas.groupby("segmento")["vlr_total"].sum().nlargest(3)

        resultado = f"""
📊 ESTATÍSTICAS GERAIS - CRÉDITO PF
===================================
• Total de Propostas: {total_propostas:,}
• Propostas Aprovadas: {len(aprovadas):,} ({pct_aprov:.1f}%)
• Propostas Reprovadas: {len(reprovadas):,} ({pct_reprov:.1f}%)

• Valor Total Aprovado: R$ {valor_aprovado:,.2f}
• Valor Total Reprovado: R$ {valor_reprovado:,.2f}
• Ticket Médio (Aprovadas): R$ {ticket_medio_aprov:,.2f}
• Ticket Médio (Reprovadas): R$ {ticket_medio_reprov:,.2f}
• Ticket Médio Geral: R$ {ticket_medio_geral:,.2f}

• Total de Clientes Únicos: {propostas_por_cliente:,}

🏦 TOP 3 FINANCIADORAS POR VALOR APROVADO:
"""
        for nome, valor in top_financiadoras.items():
            resultado += f"  - {nome}: R$ {valor:,.2f}\n"

        resultado += "\n🏷️ TOP 3 SEGMENTOS POR VALOR APROVADO:\n"
        for seg, valor in top_segmentos.items():
            resultado += f"  - {seg}: R$ {valor:,.2f}\n"

        if "dt_criacao_proposta" in aprovadas.columns:
            aprovadas = aprovadas.copy()
            aprovadas['mes'] = pd.to_datetime(aprovadas['dt_criacao_proposta']).dt.to_period('M')
            por_mes = aprovadas.groupby('mes')["vlr_total"].sum()
            if not por_mes.empty:
                resultado += "\n📆 Evolução Mensal (Aprovado):\n"
                for mes, valor in por_mes.items():
                    resultado += f"  - {mes}: R$ {valor:,.2f}\n"

        return resultado

    except Exception as e:
        return f"Erro ao calcular estatísticas de crédito PF: {str(e)}"