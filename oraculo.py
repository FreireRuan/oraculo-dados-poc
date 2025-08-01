import streamlit as st
from credit_agent import consulta_credito
from cashback_agent import consulta_cashback_onboarding 

password = st.secrets["password_streamlit"]

# === Tela de proteção por senha ===
def check_password():
    def password_entered():
        if st.session_state["password"] == password:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        ## Bem-vindo ao Agente de Dados MaisTODOS!  
        ### Instruções de uso:
        - Escolha o produto (Cashback ou Crédito) após o login.
        - É sugestivo usar o primeiro prompt abaixo para ganhar entendimento sobre os agentes e os dados que o compõem:\n
            > Apresente quais dados estão disponíveis. O que posso tirar de dúvidas e insights deles?  \n 
        - Após, fique aberto para realizar novas perguntas de negócio ou técnicas relacionadas aos produtos.
        - Aguarde o processamento e veja a resposta do Oráculo.    :)
        #### Criado por: Ruan Freire e Samuel Ferreira
        ---
        """, unsafe_allow_html=True)
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        return False

    elif not st.session_state["password_correct"]:
        st.markdown("""
        ## Bem-vindo ao Agente de Dados MaisTODOS!  
        ### Instruções de uso:
        - Escolha o produto (Cashback ou Crédito) após o login.
        - É sugestivo usar o primeiro prompt abaixo para ganhar entendimento sobre os agentes e os dados que o compõem:\n
            > Apresente quais dados estão disponíveis. O que posso tirar de dúvidas e insights deles?  \n 
        - Após, fique aberto para realizar novas perguntas de negócio ou técnicas relacionadas aos produtos.
        - Aguarde o processamento e veja a resposta do Oráculo.    :)
        #### Criado por: Ruan Freire e Samuel Ferreira
        ---
        """, unsafe_allow_html=True)
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        st.error("Senha incorreta")
        return False

    else:
        return True

if not check_password():
    st.stop()
# ===========================

# Inicialize o histórico na sessão
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Agente de Dados MaisTODOS")
st.subheader("Criado por: Ruan Freire & Samuel Ferreira")

produto = st.selectbox("Escolha o produto:", ["Cashback", "Crédito"])

for msg in st.session_state.chat_history:
    # Pergunta do usuário
    st.markdown(
        f"""
        <div style="
            background-color:#E3ECFA;
            border-radius:8px;
            padding:10px 16px;
            margin-bottom:4px;
            margin-top:12px;
            color:#1a237e;
            font-weight:500;
            width:fit-content;
            max-width:80%;
            ">
            <b>VOCÊ 👤:</b><br>{msg['pergunta']}
        </div>
        """,
        unsafe_allow_html=True
    )
    # Exibe a resposta em markdown
    st.markdown(
        f"""
        <div style="background-color:#E6F4EA; 
            border-radius:12px; 
            padding:14px 18px;
            margin-bottom:8px;
            margin-left:24px;
            color:#155724;
            width:fit-content;
            max-width:88%;
            font-size:1.08rem;
            box-shadow:0 2px 8px #a3c9b7aa;
            ">
            <b>ORÁCULO 🧑‍🚀:</b><br>{msg['resposta']}
        </div>
        """,
        unsafe_allow_html=True
    )
    # Exibe o gráfico, se houver
    if msg.get("figura") is not None:
        st.pyplot(msg["figura"])

# Aqui começa o form
with st.form(key="form_pergunta", clear_on_submit=True):
    if len(st.session_state.chat_history) == 0:
        valor_sugerido = "Apresente quais dados estão disponíveis. O que posso tirar de dúvidas e insights deles?"
    else:
        valor_sugerido = ""
    pergunta = st.text_input("Digite sua pergunta:", key="input_pergunta", value=valor_sugerido)
    submitted = st.form_submit_button("Enviar")

if submitted and pergunta:
    with st.spinner("⏳ Agente está processando sua resposta..."):
        if produto == "Crédito":
            resposta, figura = consulta_credito(pergunta)
        if produto == "Cashback":
            resposta, figura = consulta_cashback_onboarding(pergunta)
    st.session_state.chat_history.append({
        "pergunta": pergunta,
        "resposta": resposta,
        "figura": figura
    })
    st.rerun()