import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. TRATAMENTO AUTOMÁTICO DA CHAVE ---
def preparar_conexao():
    try:
        # Pega a chave do secrets.toml e limpa espaços e caracteres de escape mal formatados
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            key_bruta = st.secrets["connections"]["gsheets"]["private_key"]
            # Limpa \n literais e espaços extras nas pontas
            st.secrets["connections"]["gsheets"]["private_key"] = key_bruta.replace("\\n", "\n").strip()
        
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Erro ao carregar segredos: {e}")
        st.stop()

conn = preparar_conexao()
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"

# --- 3. MENU LATERAL ---
st.sidebar.title("🛡️ Prevenção de Perdas")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotor", "Entrada e Saída", "Relatórios"])

# --- 4. ABA: CADASTRO ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotores")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (11 números):", max_chars=11)
        submit = st.form_submit_button("Salvar na Base de Dados")

        if submit:
            if nome and len(cpf) == 11:
                try:
                    # Lê para manter a "memória"
                    df_antigo = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
                    novo = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    df_final = pd.concat([df_antigo, novo], ignore_index=True)
                    
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_final)
                    st.success(f"✅ {nome.upper()} cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("⚠️ Preencha Nome e CPF (11 dígitos) corretamente.")

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
                        conn.update(spreadsheet=URL_PLANILHA, worksheet="VISITAS", data=pd.concat([df_v, nova_v], ignore_index=True))
                        st.success(f"Entrada de {selecionado} às {agora}")
                
                with col2:
                    if st.button("REGISTRAR SAÍDA", use_container_width=True):
                        df_v = conn.read(spreadsheet=URL_PLANILHA, worksheet="VISITAS")
                        nova_v = pd.DataFrame([{"NOME": selecionado, "EVENTO": "SAÍDA", "DATA_HORA": agora}])
                        conn.update(spreadsheet=URL_PLANILHA, worksheet="VISITAS", data=pd.concat([df_v, nova_v], ignore_index=True))
                        st.warning(f"Saída de {selecionado} às {agora}")
        else:
            st.warning("Nenhum promotor cadastrado.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# --- 6. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Painel de Controle")
    aba = st.radio("Visualizar:", ["Promotores", "Visitas"], horizontal=True)
    try:
        ws = "CADASTRO" if aba == "Promotores" else "VISITAS"
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=ws)
        st.dataframe(df, use_container_width=True)
    except:
        st.info("Aguardando registros...")