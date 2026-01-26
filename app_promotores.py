import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.stop()

# --- 3. MENU LATERAL ---
# Tentativa de carregar a logo local. Se não encontrar, ele não trava o app.
caminho_logo = "LOGO_CORTE-FACIL2.png"
if os.path.exists(caminho_logo):
    st.sidebar.image(caminho_logo, use_container_width=True)
else:
    # Caso o nome do arquivo tenha extensão diferente (ex: .jpg) ou não subiu
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1067/1067566.png", width=100)

st.sidebar.title("Menu de Gestão")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotor", "Relatórios"])

# --- 4. ABA: CADASTRO DE PROMOTOR ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    st.markdown("---")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo:", placeholder="Ex: João Silva")
        
        with col2:
            cpf = st.text_input("CPF (apenas 11 números):", max_chars=11, placeholder="00011122233")
            
        submit = st.form_submit_button("Finalizar e Salvar Cadastro")

        if submit:
            if nome and len(cpf) == 11 and cpf.isdigit():
                try:
                    novo_dado = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    conn.create(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=novo_dado)
                    st.success(f"✅ {nome.upper()} cadastrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")
            elif not cpf.isdigit():
                st.error("⚠️ O CPF deve conter apenas números.")
            elif len(cpf) != 11:
                st.error("⚠️ O CPF deve ter exatamente 11 dígitos.")
            else:
                st.warning("⚠️ Preencha o nome completo.")

    st.markdown("### Promotores Ativos")
    try:
        df_lista = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        if not df_lista.empty:
            st.dataframe(df_lista.sort_index(ascending=False), use_container_width=True)
    except:
        st.info("Aguardando novos registros...")

# --- 5. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Painel de Controle")
    st.markdown("---")
    
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        if not df.empty:
            st.metric("Total de Promotores", len(df))
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar Lista (CSV)", csv, "promotores.csv", "text/csv")
        else:
            st.warning("Nenhum promotor cadastrado ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")