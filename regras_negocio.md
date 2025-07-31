# Visão Geral
a maistodos é a fintech do ecossistema cartão de todos / amor saúde que conecta cashback, pagamentos, conta digital e linhas de crédito. dentro desse portfólio, o crédito pf (“crédito para pessoas”) é voltado principalmente a clientes de renda média‑baixa que precisam financiar despesas pontuais – sobretudo tratamentos médicos, odontológicos e estéticos – de forma rápida e sem a burocracia bancária tradicional. 

# proposta de valor do crédito pf
aspecto	detalhes principais
modalidade	crédito direto ao consumidor (cdc) não consignado, 100 % digital
uso típico	procedimentos de saúde (odontologia, oftalmo, pequenas cirurgias) e demais necessidades pessoais
canal	app Cartão de Todos, POS/portal em clínicas e landing pages white‑label
desembolso	pagamento direto ao prestador (clínica / parceiro) para evitar risco de desvio de finalidade
cobrança	boletos registrados, pix recorrente ou débito automático

# fluxo operacional
simulação – cliente ou atendente preenche CPF, valor solicitado, quantidade de parcelas e dados básicos (nome, nasc., cep, telefone).

simulação P1 – motor de pré‑qualificação em tempo real retorna: aprovado, pendente docs ou rejeitado.

simulação p2 – 

formalização – assinatura eletrônica do contrato, upload de selfie + documento e geração de cédula de crédito eletrônica (CCE).

liquidação – repasse ao parceiro via subconta na adquirente; cobrança ao cliente inicia no mês seguinte. todos os eventos são enviados para o data lake (s3) e replicados no redshift/athena para analytics.