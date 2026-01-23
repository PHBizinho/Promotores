import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configurações Iniciais
st.set_page_config(page_title="Sistema MM Frios", layout="wide")

# Link exato da sua planilha que você enviou
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"

# 2. Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÕES DE APOIO ---
def carregar_dados(aba):
    try:
        # Forçamos o parâmetro spreadsheet para evitar o erro da imagem image_a39810
        return conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0)
    except Exception:
        if aba == "CADASTROS":
            return pd.DataFrame(columns=['CPF', 'NOME'])
        return pd.DataFrame(columns=['DATA', 'CPF', 'FORNECEDOR', 'ENTRADA', 'SAIDA', 'TEMPO_MINUTOS'])

# --- MENU ---
st.sidebar.title("Menu de Gestão")
menu = st.sidebar.radio("Navegação", ["Check-in/Out", "Cadastro de Promotor", "Relatórios"])

if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    df_cad = carregar_dados("CADASTROS")
    
    with st.form("novo_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (apenas números):", max_chars=11)
        
        if st.form_submit_button("Salvar no Google Sheets"):
            if nome and cpf:
                # Criamos o novo dado
                novo_dado = pd.DataFrame([{"CPF": str(cpf), "NOME": nome}])
                # Juntamos com o que já existe
                df_atualizado = pd.concat([df_cad, novo_dado], ignore_index=True).drop_duplicates()
                
                try:
                    # O segredo está aqui: passar o spreadsheet=URL_PLANILHA novamente
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTROS", data=df_atualizado)
                    st.success(f"✅ {nome} cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro de Autenticação: Verifique se a Private Key nos Secrets está correta.")
                    st.info("O erro 'Public Spreadsheet' significa que o Streamlit não reconheceu sua Service Account.")
            else:
                st.warning("Preencha todos os campos.")

    st.subheader("Lista de Promotores")
    st.dataframe(df_cad, use_container_width=True)

elif menu == "Check-in/Out":
    st.title("📲 Registro de Visita")
    # ... (mesma lógica de busca de CPF usando a função carregar_dados("CADASTROS"))
    st.info("Para testar a gravação, use a aba 'Cadastro de Promotor' primeiro.")

elif menu == "Relatórios":
    st.title("📊 Histórico")
    st.dataframe(carregar_dados("VISITAS"), use_container_width=True)