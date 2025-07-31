import streamlit as st
from credit_agent import consulta_credito
from cashback_agent import consulta_cashback_onboarding 

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

# Inicialize o histórico na sessão
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Agente de Dados MaisTODOS")

produto = st.selectbox("Escolha o produto:", ["Crédito", "Cashback"])

# Exibe o histórico do chat
for msg in st.session_state.chat_history:
    cols = st.columns([2, 2])
    with cols[0]:
        st.markdown(
            f"""
            <div style="
                text-align:left;
                background-color:#F0F2F6;
                border-radius:8px;
                padding:10px;
                margin-bottom:2px
                color:#000000
            ">
                <b>Você:</b><br>{msg['pergunta']}
                </div>
            """,
            unsafe_allow_html=True
        )
    with cols[1]:
        st.markdown(
            f"""
            <div style="
                text-align:left;
                background-color:#E6F4EA;
                border-radius:12px;
                padding:18px 16px;
                margin-bottom:8px;
                min-width:300px;
                max-width:520px;
                font-size:1.1rem;
                box-shadow:0 2px 8px #a3c9b7aa;
                color:#000000
            ">
                <b>Oráculo:</b><br>{msg['resposta']}
                </div>
            """,
            unsafe_allow_html=True
        )

# Aqui começa o form
with st.form(key="form_pergunta", clear_on_submit=True):
    pergunta = st.text_input("Digite sua pergunta:", key="input_pergunta")
    submitted = st.form_submit_button("Enviar")

if submitted and pergunta:
    if produto == "Crédito":
        resposta = consulta_credito(pergunta)
    if produto == "Cashback":
        resposta = consulta_cashback_onboarding(pergunta)
    # Adiciona ao histórico
    st.session_state.chat_history.append({
        "pergunta": pergunta,
        "resposta": resposta
    })
    st.experimental_rerun()