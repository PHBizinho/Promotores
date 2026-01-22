import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Controle de Promotores", layout="centered")

# --- FUNÇÃO PARA CARREGAR OS DADOS DO EXCEL ---
def buscar_fornecedores():
    try:
        # Carrega o arquivo Excel que você criou
        # O parâmetro engine='openpyxl' ajuda a evitar erros de leitura
        df = pd.read_excel("APP_PROMOTORES/BASE_FORNECEDORES.xlsx")
        
        # Limpa espaços em branco que possam vir do Excel
        df['Fornecedor'] = df['Fornecedor'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}")
        # Retorna um DataFrame vazio se der erro para não travar o app
        return pd.DataFrame(columns=['Código', 'Fornecedor'])

st.title("📲 Registro de Promotores")
st.info("Utilizando base temporária em Excel")
st.markdown("---")

# --- INTERFACE DO PROMOTOR ---
df_forn = buscar_fornecedores()

if not df_forn.empty:
    with st.container():
        # Campo de seleção do fornecedor usando a coluna do Excel
        fornecedor_selecionado = st.selectbox(
            "Selecione o seu Fornecedor:", 
            options=df_forn['Fornecedor'].unique()
        )
        
        # Campo de CPF
        cpf = st.text_input("Digite seu CPF (apenas números):", max_chars=11)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Registrar ENTRADA", use_container_width=True):
                if cpf:
                    agora = datetime.now().strftime("%H:%M:%S")
                    st.success(f"Entrada registrada! {fornecedor_selecionado} - CPF: {cpf} às {agora}")
                else:
                    st.error("Por favor, informe o CPF.")

        with col2:
            if st.button("Registrar SAÍDA", use_container_width=True):
                if cpf:
                    agora = datetime.now().strftime("%H:%M:%S")
                    st.warning(f"Saída registrada para o CPF {cpf} às {agora}")
                else:
                    st.error("Por favor, informe o CPF.")
else:
    st.warning("Aguardando preenchimento da base de fornecedores.")