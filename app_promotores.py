import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. TRATAMENTO DE SEGURANÇA DA CHAVE ---
# Este bloco força a correção de formatação da private_key antes de conectar
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        secret_dict = st.secrets["connections"]["gsheets"]
        if "private_key" in secret_dict:
            # Remove espaços extras e garante que o \n seja lido como quebra de linha real
            raw_key = secret_dict["private_key"].strip()
            fixed_key = raw_key.replace("\\n", "\n")
            st.secrets.connections.gsheets.private_key = fixed_key
except Exception as e:
    st.error(f"Erro ao processar as chaves de segurança: {e}")

# --- 3. CONEXÃO COM GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error("Erro crítico na conexão com o Google. Verifique os Secrets no painel do Streamlit.")
    st.stop()

# --- 4. FUNÇÕES DE DADOS ---
def carregar_dados(aba):
    try:
        return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba)
    except:
        return pd.DataFrame()

# --- 5. INTERFACE (MENU) ---
st.sidebar.title("Menu de Gestão")
menu = st.sidebar.radio("Navegação", ["Check-in/Out", "Cadastro de Promotor", "Relatórios"])

if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    
    with st.form("form_cadastro"):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (apenas números):")
        submit = st.form_submit_button("Salvar no Google Sheets")

        if submit:
            if nome and cpf:
                try:
                    # Carrega dados atuais para verificar duplicados ou anexar
                    df_existente = carregar_dados("CADASTRO")
                    novo_dado = pd.DataFrame([{"NOME": nome, "CPF": cpf}])
                    
                    if not df_existente.empty:
                        df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
                    else:
                        df_final = novo_dado
                    
                    # Atualiza a planilha
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_final)
                    st.success(f"✅ {nome} cadastrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha todos os campos.")

    st.subheader("Lista de Promotores")
    df_lista = carregar_dados("CADASTRO")
    if not df_lista.empty:
        st.dataframe(df_lista, use_container_width=True)

elif menu == "Check-in/Out":
    st.title("📅 Registro de Visita")
    st.info("Funcionalidade em desenvolvimento. Use a aba de Cadastro para testar a conexão.")

elif menu == "Relatórios":
    st.title("📊 Histórico")
    df_visitas = carregar_dados("VISITAS")
    st.dataframe(df_visitas, use_container_width=True)