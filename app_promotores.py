import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
try:
    # Código simplificado: o Streamlit lerá os segredos direto do painel Cloud
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error(f"Erro na conexão com o Google. Verifique os Secrets no painel do Streamlit.")
    st.stop()

# --- 3. MENU LATERAL ---
caminho_logo = "LOGO_CORTE-FACIL2.png"
if os.path.exists(caminho_logo):
    st.sidebar.image(caminho_logo, use_container_width=True)

st.sidebar.title("Menu de Gestão")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotor", "Relatórios"])

# --- 4. ABA: CADASTRO DE PROMOTOR ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo:")
        with col2:
            cpf = st.text_input("CPF (11 números):", max_chars=11)
            
        submit = st.form_submit_button("Finalizar e Salvar Cadastro")

        if submit:
            if nome and len(cpf) == 11:
                try:
                    # Lê o que já existe
                    df_antigo = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
                    # Cria o novo
                    novo = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    # Junta e Salva
                    df_final = pd.concat([df_antigo, novo], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_final)
                    
                    st.success(f"✅ {nome.upper()} cadastrado!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha os dados corretamente.")

# --- 5. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatórios")
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        st.dataframe(df, use_container_width=True)
    except:
        st.info("Nenhum dado encontrado.")