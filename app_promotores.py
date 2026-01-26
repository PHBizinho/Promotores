import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. CONEXÃO ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.stop()

# --- 3. MENU ---
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
            if nome and len(cpf) == 11 and cpf.isdigit():
                try:
                    df_antigo = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
                    novo = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    df_final = pd.concat([df_antigo, novo], ignore_index=True)
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_final)
                    st.success(f"✅ {nome.upper()} salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha os dados corretamente.")

# --- 5. ABA: ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Fluxo de Acesso")
    try:
        # Busca promotores cadastrados
        df_promotores = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        lista = sorted(df_promotores["NOME"].unique().tolist())
        selecionado = st.selectbox("Selecione o Promotor:", [""] + lista)
        
        if selecionado:
            col1, col2 = st.columns(2)
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with col1:
                if st.button("Registrar ENTRADA", type="primary", use_container_width=True):
                    try:
                        df_visitas = conn.read(spreadsheet=URL_PLANILHA, worksheet="VISITAS")
                        nova_v = pd.DataFrame([{"NOME": selecionado, "EVENTO": "ENTRADA", "DATA_HORA": agora}])
                        df_v_final = pd.concat([df_visitas, nova_v], ignore_index=True)
                        conn.update(spreadsheet=URL_PLANILHA, worksheet="VISITAS", data=df_v_final)
                        st.success(f"Entrada de {selecionado} às {agora}")
                    except Exception as e:
                        st.error(f"Erro ao registrar entrada: {e}")
            
            with col2:
                if st.button("Registrar SAÍDA", use_container_width=True):
                    try:
                        df_visitas = conn.read(spreadsheet=URL_PLANILHA, worksheet="VISITAS")
                        nova_v = pd.DataFrame([{"NOME": selecionado, "EVENTO": "SAÍDA", "DATA_HORA": agora}])
                        df_v_final = pd.concat([df_visitas, nova_v], ignore_index=True)
                        conn.update(spreadsheet=URL_PLANILHA, worksheet="VISITAS", data=df_v_final)
                        st.warning(f"Saída de {selecionado} às {agora}")
                    except Exception as e:
                        st.error(f"Erro ao registrar saída: {e}")
    except:
        st.info("Cadastre um promotor antes de registrar acessos.")

# --- 6. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Base de Dados")
    tab1, tab2 = st.tabs(["Lista de Promotores", "Histórico de Visitas"])
    
    with tab1:
        try:
            df = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
            st.dataframe(df, use_container_width=True)
        except:
            st.write("Sem dados de cadastro.")
            
    with tab2:
        try:
            df_v = conn.read(spreadsheet=URL_PLANILHA, worksheet="VISITAS")
            st.dataframe(df_v.sort_index(ascending=False), use_container_width=True)
        except:
            st.write("Sem histórico de visitas.")