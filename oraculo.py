import streamlit as st
from credit_agent import consulta_credito
from cashback_agent import consulta_cashback_onboarding 

password = st.secrets["password_streamlit"]

# === Tela de proteção por senha ===
def check_password():
    # Instruções de uso
    st.markdown("""
    ## Bem-vindo ao Agente de Dados MaisTODOS!  
    - Escolha o produto (Cashback ou Crédito) após o login.
    - É sugestivo usar o primeiro prompt abaixo para ganhar entendimento sobre os agentes e os dados que o compõem:
        "Apresente quais dados estão disponíveis. O que posso tirar de dúvidas e insights deles?"   
    - Após, fique aberto para realizar perguntas de negócio ou técnicas relacionadas aos produtos.
    - Aguarde o processamento e veja a resposta do Oráculo. :)
    ---
    """, unsafe_allow_html=True)

    def password_entered():
        if st.session_state["password"] == password:
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

# Inicialize o histórico na sessão
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Agente de Dados MaisTODOS")
st.subheader("Criado por: Ruan Freire & Samuel Ferreira")

produto = st.selectbox("Escolha o produto:", ["Cashback", "Crédito"])

for msg in st.session_state.chat_history:
    # Pergunta do usuário (bolha clara, fonte escura)
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
    # Exibe a resposta em markdown (texto explicativo)
    st.markdown(
        f"""
        <div style="
            background-color:#E6F4EA;
            border-radius:12px;
            padding:14px 18px;
            margin-bottom:8px;
            margin-left:24px;
            color:#155724;
            width:fit-content;
            max-width:88%;
            font-size:1.08rem;
            box-shadow:0 2px 8px #a3c9b7aa;">
            <b>ORÁCULO 🧑‍🚀:</b><br>{msg['resposta']}
        </div>
        """,
        unsafe_allow_html=True
    )

# Aqui começa o form
with st.form(key="form_pergunta", clear_on_submit=True):
    pergunta = st.text_input("Digite sua pergunta:", key="input_pergunta")
    submitted = st.form_submit_button("Enviar")

if submitted and pergunta:
    with st.spinner("⏳ Agente está processando sua resposta..."):
        if produto == "Crédito":
            resposta = consulta_credito(pergunta)
        if produto == "Cashback":
            resposta = consulta_cashback_onboarding(pergunta)
    # Adiciona ao histórico
    st.session_state.chat_history.append({
        "pergunta": pergunta,
        "resposta": resposta
    })
    st.rerun()