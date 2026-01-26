import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Prevenção de Perdas", layout="wide", page_icon="🛡️")

# --- 2. CONEXÃO ---
# Localmente, o Streamlit busca as chaves no arquivo .streamlit/secrets.toml
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error("Erro de conexão. Verifique se o arquivo secrets.toml está na pasta .streamlit")
    st.stop()

# --- 3. MENU LATERAL ---
st.sidebar.title("🛡️ Sistema de controle - Fluxo de promotores")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotores", "Controle de Acesso", "Relatórios"])

# --- 4. ABA: CADASTRO DE PROMOTOR ---
if menu == "Cadastro de Promotores":
    st.title("👤 Novo Cadastro")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Promotor:")
        with col2:
            cpf = st.text_input("CPF (11 números):", max_chars=11)
            
        submit = st.form_submit_button("Salvar na Base de Dados")

        if submit:
            if nome and len(cpf) == 11:
                try:
                    # Lógica de Memória: Lê o atual, adiciona o novo, salva tudo
                    df_atual = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
                    novo_promotor = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    df_final = pd.concat([df_atual, novo_promotor], ignore_index=True)
                    
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_final)
                    
                    st.success(f"Registro de {nome.upper()} salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha Nome e CPF corretamente.")

# --- 5. ABA: CONTROLE DE ACESSO (ONDE O FUNCIONÁRIO TRABALHARÁ) ---
elif menu == "Controle de Acesso":
    st.title("🕒 Entrada e Saída")
    
    # Busca a lista de promotores cadastrados para o funcionário escolher
    try:
        df_promotores = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        lista_nomes = df_promotores["NOME"].tolist()
        
        selecionado = st.selectbox("Selecione o Promotor:", [""] + lista_nomes)
        
        col_ent, col_sai = st.columns(2)
        with col_ent:
            if st.button("Registrar ENTRADA", use_container_width=True):
                st.info(f"Entrada de {selecionado} registrada!") # Aqui faremos a lógica de salvar na aba VISITAS
        with col_sai:
            if st.button("Registrar SAÍDA", use_container_width=True):
                st.info(f"Saída de {selecionado} registrada!")
    except:
        st.error("Nenhum promotor cadastrado para registrar acesso.")

# --- 6. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Base de Dados")
    df = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
    st.dataframe(df, use_container_width=True)