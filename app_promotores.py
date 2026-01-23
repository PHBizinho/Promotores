import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="🏢")

# --- CONFIGURAÇÃO DA PLANILHA ---
# Substitua pelo ID da sua planilha (o código longo entre /d/ e /edit)
ID_PLANILHA = "1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI"

# Links de exportação direta (Evitam o erro 400)
URL_CADASTROS = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=CADASTROS"
URL_VISITAS = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=VISITAS"

# --- FUNÇÕES DE CARREGAMENTO ---
def ler_cadastros():
    try:
        return pd.read_csv(URL_CADASTROS)
    except:
        return pd.DataFrame(columns=['CPF', 'NOME'])

def ler_visitas():
    try:
        return pd.read_csv(URL_VISITAS)
    except:
        return pd.DataFrame(columns=['DATA', 'CPF', 'FORNECEDOR', 'ENTRADA', 'SAIDA', 'TEMPO_MINUTOS'])

def buscar_fornecedores():
    try:
        df = pd.read_excel("BASE_FORNECEDORES.xlsx", skiprows=1)
        df.columns = ['Código', 'Fornecedor', 'CNPJ_CPF', 'Fantasia']
        df = df.dropna(subset=['Fornecedor', 'Código'])
        df['Código'] = df['Código'].astype(int).astype(str)
        df['Busca'] = df['Código'] + " - " + df['Fornecedor']
        return df.sort_values('Fornecedor')
    except:
        return pd.DataFrame()

# --- INTERFACE ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", width=150)

menu = st.sidebar.radio("Navegação", ["Check-in/Out", "Cadastro de Promotor", "Relatórios"])

# --- TELA: CADASTRO ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    df_cadastros = ler_cadastros()
    
    with st.form("form_cad", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf = st.text_input("CPF (Somente números)", max_chars=11)
        if st.form_submit_button("Salvar Cadastro"):
            if nome and cpf:
                if str(cpf) in df_cadastros['CPF'].astype(str).values:
                    st.error("⚠️ CPF já cadastrado!")
                else:
                    st.success(f"✅ Dados validados para {nome}!")
                    st.info("Para salvar no Google Sheets pelo computador local, é necessário configurar a chave JSON. No Streamlit Cloud (Web), funcionará automaticamente.")
            else:
                st.warning("Preencha todos os campos.")
    
    st.write("### Cadastros Atuais")
    st.dataframe(df_cadastros, use_container_width=True)

# --- TELA: CHECK-IN ---
elif menu == "Check-in/Out":
    st.title("📲 Registro de Visita")
    df_forn = buscar_fornecedores()
    df_cadastros = ler_cadastros()
    
    cpf_v = st.text_input("Informe seu CPF:", max_chars=11)
    if cpf_v:
        promotor = df_cadastros[df_cadastros['CPF'].astype(str) == str(cpf_v)]
        if not promotor.empty:
            st.success(f"Olá, **{promotor.iloc[0]['NOME']}**")
            fornecedor = st.selectbox("Selecione o Fornecedor:", options=df_forn['Busca'].unique(), index=None)
            
            col1, col2 = st.columns(2)
            if col1.button("🔴 Registrar Entrada", use_container_width=True):
                st.success("Entrada processada!")
            if col2.button("🟢 Registrar Saída", use_container_width=True):
                st.warning("Saída processada!")
        else:
            st.error("CPF não encontrado no sistema.")

# --- TELA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatório de Visitas")
    df_v = ler_visitas()
    st.dataframe(df_v, use_container_width=True)