import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Controle de Promotores", layout="centered", page_icon="📲")

# --- FUNÇÃO PARA CARREGAR OS DADOS DO EXCEL ---
def buscar_fornecedores():
    try:
        # Lê o Excel pulando a primeira linha (título mesclado)
        df = pd.read_excel("BASE_FORNECEDORES.xlsx", skiprows=1)
        
        # Define os nomes das colunas baseados na sua planilha
        df.columns = ['Código', 'Fornecedor', 'CNPJ_CPF', 'Fantasia']
        
        # --- LIMPEZA DOS DADOS ---
        df = df.dropna(subset=['Fornecedor', 'Código'])
        
        # Converte Código para número inteiro (remove o .0) e depois para texto
        df['Código'] = df['Código'].astype(int).astype(str)
        df['Fornecedor'] = df['Fornecedor'].astype(str).str.strip()
        
        # Filtra erros de fórmula
        df = df[~df['Fornecedor'].str.contains('#', na=False)]
        
        # CRIA A COLUNA DE BUSCA: "Código - Fornecedor"
        df['Busca'] = df['Código'] + " - " + df['Fornecedor']
        
        return df.sort_values('Fornecedor')
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}")
        return pd.DataFrame()

# --- EXIBIÇÃO DA LOGO ---
# Tentamos carregar a logo (ajuste a extensão se for .png ou .jpg)
nome_logo = "LOGO_CORTE-FACIL2.png" 

if os.path.exists(nome_logo):
    st.image(nome_logo, width=200)
else:
    # Caso a extensão seja diferente, tentamos .jpg
    if os.path.exists("LOGO_CORTE-FACIL2.jpg"):
        st.image("LOGO_CORTE-FACIL2.jpg", width=200)

# --- TELA PRINCIPAL ---
st.title("📲 Registro de Promotores")
st.markdown("---")

df_forn = buscar_fornecedores()

if not df_forn.empty:
    with st.container():
        # Seletor aprimorado: Busca por Código ou Nome
        opcao_selecionada = st.selectbox(
            "Selecione ou Digite o Código/Descrição:", 
            options=df_forn['Busca'].unique(),
            index=None,
            placeholder="Ex: 2213 ou MOB2CON..."
        )
        
        # Campo de CPF
        cpf = st.text_input("Digite seu CPF (apenas números):", max_chars=11)
        
        st.write("") 
        col1, col2 = st.columns(2)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        with col1:
            if st.button("🔴 Registrar ENTRADA", use_container_width=True):
                if cpf and opcao_selecionada:
                    st.success(f"**ENTRADA CONFIRMADA!**\n\n🕒 {agora}\n\n👤 CPF: {cpf}\n\n🏢 {opcao_selecionada}")
                else:
                    st.warning("Preencha o CPF e o Fornecedor.")

        with col2:
            if st.button("🟢 Registrar SAÍDA", use_container_width=True):
                if cpf and opcao_selecionada:
                    st.warning(f"**SAÍDA CONFIRMADA!**\n\n🕒 {agora}\n\n👤 CPF: {cpf}\n\n🏢 {opcao_selecionada}")
                else:
                    st.warning("Preencha o CPF e o Fornecedor.")
else:
    st.warning("⚠️ Base de dados não encontrada.")

st.markdown("---")
st.caption("Desenvolvido para MM Frios - Setor Fiscal")