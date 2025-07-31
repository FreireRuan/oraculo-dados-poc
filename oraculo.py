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
    st.markdown(f"**Você:** {msg['pergunta']}")
    st.markdown(f"**Oráculo:** {msg['resposta']}")

pergunta = st.text_input("Digite sua pergunta:")

if st.button("Enviar"):
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