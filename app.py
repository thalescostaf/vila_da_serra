import streamlit as st

# Configuração da página
st.set_page_config(page_title="Vila da Serra — Home", page_icon="🏠", layout="wide")

# Título e breve instrução (texto normal para o usuário)
st.title("🏠 Vila da Serra — Home")
st.write("Selecione um módulo para continuar.")

# Função utilitária para navegação entre páginas
def go(label: str, page_path: str):
    # Um botão por linha, ocupando toda a largura
    if st.button(label, use_container_width=True, type="primary"):
        # Navega para a página correspondente (arquivos estão em /pages)
        st.switch_page(page_path)

# Botões (um por linha)
go("📈 Métricas", "pages/1_Metricas.py")
go("📝 Ocorrências", "pages/2_Ocorrencias.py")
go("💰 Fluxo de Caixa", "pages/3_Fluxo_de_Caixa.py")
go("🗓️ Agenda", "pages/4_Agenda.py")
go("👥 Moradores", "pages/5_Moradores.py")
