import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="🏢")

# --- CONFIGURAÇÃO DA PLANILHA (VIA EXPORT CSV) ---
# Usar o ID direto é muito mais seguro contra erros de conexão
ID_PLANILHA = "1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI"

# Função para gerar o link de exportação de cada aba
def link_aba(gid):
    return f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid={gid}"

# IDs das abas (GIDs) que estão na sua URL do navegador quando você clica nelas
GID_CADASTROS = "0"  # Geralmente a primeira aba é 0
GID_VISITAS = "1792671569" # Ajuste conforme o número que aparece no final do seu link da aba Visitas

# --- FUNÇÃO DE BUSCA DE FORNECEDORES (EXCEL LOCAL) ---
def buscar_fornecedores():
    try:
        df = pd.read_excel("BASE_FORNECEDORES.xlsx", skiprows=1)
        df.columns = ['Código', 'Fornecedor', 'CNPJ_CPF', 'Fantasia']
        df = df.dropna(subset=['Fornecedor', 'Código'])
        df['Código'] = df['Código'].astype(int).astype(str)
        df['Busca'] = df['Código'] + " - " + df['Fornecedor']
        return df.sort_values('Fornecedor')
    except Exception as e:
        return pd.DataFrame()

# --- SIDEBAR (MENU) ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", width=150)
menu = st.sidebar.radio("Navegação", ["Check-in/Out", "Cadastro de Promotor", "Relatórios"])

# --- TELA 1: CHECK-IN / CHECK-OUT ---
if menu == "Check-in/Out":
    st.title("📲 Registro de Visita")
    df_forn = buscar_fornecedores()
    
    try:
        # Leitura direta via Pandas (Evita o erro 400 do conector GSheets)
        df_cadastros = pd.read_csv(link_aba(GID_CADASTROS))
        
        with st.container(border=True):
            cpf_visita = st.text_input("Digite seu CPF para identificar:", max_chars=11)
            
            if cpf_visita:
                # Localiza o promotor pelo CPF
                promotor = df_cadastros[df_cadastros['CPF'].astype(str) == cpf_visita]
                
                if not promotor.empty:
                    nome_logado = promotor.iloc[0]['NOME']
                    st.success(f"Bem-vindo, **{nome_logado}**!")
                    
                    fornecedor = st.selectbox("Selecione o Fornecedor:", options=df_forn['Busca'].unique(), index=None)
                    
                    col1, col2 = st.columns(2)
                    agora = datetime.now()

                    if col1.button("🔴 Registrar Entrada", use_container_width=True):
                        if fornecedor:
                            st.info(f"Entrada de {nome_logado} processada às {agora.strftime('%H:%M:%S')}")
                            st.warning("⚠️ Nota: Para gravar na planilha online, precisamos configurar as credenciais JSON ou usar o Streamlit Cloud.")
                        else:
                            st.error("Selecione o fornecedor!")

                    if col2.button("🟢 Registrar Saída", use_container_width=True):
                        st.warning("Saída processada localmente.")
                else:
                    st.error("CPF não cadastrado! Vá ao menu 'Cadastro de Promotor'.")
    except Exception as e:
        st.error(f"Erro ao conectar com a Planilha: {e}")
        st.info("Verifique se a planilha está compartilhada como 'Qualquer pessoa com o link'.")

# --- TELA 2: CADASTRO DE PROMOTOR ---
elif menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    try:
        df_cadastros = pd.read_csv(link_aba(GID_CADASTROS))
        
        with st.form("cad_promotor"):
            nome_c = st.text_input("Nome Completo")
            cpf_c = st.text_input("CPF (Somente números)", max_chars=11)
            if st.form_submit_button("Salvar Cadastro"):
                if cpf_c in df_cadastros['CPF'].astype(str).values:
                    st.error("Erro: Este CPF já está cadastrado!")
                elif nome_c and cpf_c:
                    st.success(f"Dados prontos para salvar: {nome_c} - {cpf_c}")
                    st.info("A gravação direta requer autenticação Private ou deploy no Streamlit Cloud.")
                else:
                    st.warning("Preencha todos os campos.")
    except:
        st.error("Não foi possível carregar a lista de cadastros.")

# --- TELA 3: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatório de Visitas")
    try:
        df_v = pd.read_csv(link_aba(GID_VISITAS))
        st.dataframe(df_v, use_container_width=True)
    except:
        st.warning("Nenhum dado de visita encontrado na planilha.")

st.markdown("---")
st.caption(f"MM Frios - Controle Interno | {datetime.now().strftime('%d/%m/%Y')}")