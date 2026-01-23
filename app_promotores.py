import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="🏢")

# --- CONFIGURAÇÃO DA PLANILHA (LEITURA) ---
ID_PLANILHA = "1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI"
# Link para ler a aba CADASTROS via CSV
URL_CADASTROS = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet=CADASTROS"

# --- FUNÇÕES DE CARREGAMENTO ---
def buscar_fornecedores():
    try:
        # Carrega a base do Excel que está na sua pasta
        df = pd.read_excel("BASE_FORNECEDORES.xlsx", skiprows=1)
        df.columns = ['Código', 'Fornecedor', 'CNPJ_CPF', 'Fantasia']
        df = df.dropna(subset=['Fornecedor', 'Código'])
        df['Código'] = df['Código'].astype(int).astype(str)
        df['Busca'] = df['Código'] + " - " + df['Fornecedor']
        return df.sort_values('Fornecedor')
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        return pd.DataFrame()

def ler_cadastros_sheets():
    try:
        return pd.read_csv(URL_CADASTROS)
    except:
        return pd.DataFrame(columns=['CPF', 'NOME', 'FORNECEDOR'])

# --- INTERFACE ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", width=150)

menu = st.sidebar.radio("Navegação", ["Check-in/Out", "Cadastro de Promotor", "Relatórios"])
df_fornecedores = buscar_fornecedores()

# --- TELA 2: CADASTRO DE PROMOTOR ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    df_cadastros = ler_cadastros_sheets()
    
    with st.form("form_cad", clear_on_submit=True):
        st.write("### Vincular Promotor ao Fornecedor")
        nome = st.text_input("Nome Completo do Promotor")
        cpf = st.text_input("CPF (Somente números)", max_chars=11)
        
        # Aqui o promotor seleciona o fornecedor dele no ato do cadastro
        fornecedor_vinculo = st.selectbox(
            "Selecione o Fornecedor deste Promotor:",
            options=df_fornecedores['Busca'].unique() if not df_fornecedores.empty else [],
            index=None,
            placeholder="Digite o nome ou código..."
        )
        
        if st.form_submit_button("Salvar Cadastro"):
            if nome and cpf and fornecedor_vinculo:
                if str(cpf) in df_cadastros['CPF'].astype(str).values:
                    st.error("⚠️ Este CPF já está cadastrado!")
                else:
                    # Simulação de salvamento (Para salvar real, precisa do Deploy no Streamlit Cloud)
                    st.success(f"✅ Promotor {nome} vinculado ao fornecedor {fornecedor_vinculo}!")
                    st.info("Para gravar no Google Sheets, o próximo passo é o Deploy no GitHub.")
            else:
                st.warning("Preencha Nome, CPF e selecione um Fornecedor.")
    
    st.write("### Lista de Cadastros (Lido do Google Sheets)")
    st.dataframe(df_cadastros, use_container_width=True)

# --- TELA 1: CHECK-IN / CHECK-OUT ---
elif menu == "Check-in/Out":
    st.title("📲 Registro de Visita")
    df_cadastros = ler_cadastros_sheets()
    
    cpf_v = st.text_input("Informe seu CPF para entrar/sair:", max_chars=11)
    if cpf_v:
        promotor = df_cadastros[df_cadastros['CPF'].astype(str) == str(cpf_v)]
        if not promotor.empty:
            # Puxa automaticamente o fornecedor vinculado no cadastro
            forn_vinculado = promotor.iloc[0]['FORNECEDOR'] if 'FORNECEDOR' in promotor.columns else "Não vinculado"
            st.success(f"Olá, **{promotor.iloc[0]['NOME']}**! (Empresa: {forn_vinculado})")
            
            col1, col2 = st.columns(2)
            if col1.button("🔴 Registrar Entrada", use_container_width=True):
                st.balloons()
                st.write(f"Entrada registrada às {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.error("CPF não identificado. Faça o cadastro primeiro.")

# --- TELA 3: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatórios")
    st.info("Os dados aparecerão aqui assim que o deploy for concluído e as gravações começarem.")