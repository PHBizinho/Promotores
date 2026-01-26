import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. CONEXÃO COM LIMPEZA DE CHAVE ---
try:
    # Pequeno truque para limpar quebras de linha mal formatadas na chave
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        raw_key = st.secrets["connections"]["gsheets"]["private_key"]
        # Isso corrige se a chave vier com \n literais em vez de quebras reais
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error(f"Erro crítico na configuração: {e}")
    st.stop()

# --- 3. MENU LATERAL ---
st.sidebar.title("🛡️ Prevenção de Perdas")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotor", "Entrada e Saída", "Relatórios"])

# --- 4. ABA: CADASTRO ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotores")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (11 números):", max_chars=11)
        submit = st.form_submit_button("Salvar Cadastro")

        if submit:
            if nome and len(cpf) == 11:
                try:
                    # Tenta ler a aba CADASTRO
                    df_antigo = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
                    novo = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    df_final = pd.concat([df_antigo, novo], ignore_index=True)
                    
                    # Salva
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_final)
                    st.success(f"✅ {nome.upper()} cadastrado!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    st.info("Dica: Verifique se você compartilhou a planilha com o e-mail do Service Account.")

# --- 5. ABA: ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Fluxo de Acesso")
    try:
        df_p = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        if not df_p.empty:
            lista = sorted(df_p["NOME"].unique().tolist())
            selecionado = st.selectbox("Selecione o Promotor:", [""] + lista)
            
            if selecionado:
                col1, col2 = st.columns(2)
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                with col1:
                    if st.button("REGISTRAR ENTRADA", type="primary", use_container_width=True):
                        df_v = conn.read(spreadsheet=URL_PLANILHA, worksheet="VISITAS")
                        nova_v = pd.DataFrame([{"NOME": selecionado, "EVENTO": "ENTRADA", "DATA_HORA": agora}])
                        conn.update(spreadsheet=URL_PLANILHA, worksheet="VISITAS", data=pd.concat([df_v, nova_v]))
                        st.success(f"Entrada registrada: {agora}")
                
                with col2:
                    if st.button("REGISTRAR SAÍDA", use_container_width=True):
                        df_v = conn.read(spreadsheet=URL_PLANILHA, worksheet="VISITAS")
                        nova_v = pd.DataFrame([{"NOME": selecionado, "EVENTO": "SAÍDA", "DATA_HORA": agora}])
                        conn.update(spreadsheet=URL_PLANILHA, worksheet="VISITAS", data=pd.concat([df_v, nova_v]))
                        st.warning(f"Saída registrada: {agora}")
        else:
            st.warning("Cadastre um promotor primeiro.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# --- 6. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatórios")
    aba = st.radio("Ver base de:", ["Promotores", "Visitas"], horizontal=True)
    try:
        nome_aba = "CADASTRO" if aba == "Promotores" else "VISITAS"
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=nome_aba)
        st.dataframe(df, use_container_width=True)
    except:
        st.write("Sem dados para exibir.")