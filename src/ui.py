# src/ui.py
import streamlit as st

def back_home():
    # Botão simples para voltar à Home
    if st.button("← Voltar para Home"):
        st.switch_page("app.py")
