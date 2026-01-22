import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle de Promotores", layout="centered", page_icon="📲")

# --- FUNÇÃO PARA CARREGAR OS DADOS DO EXCEL ---
def buscar_fornecedores():
    try:
        # Lê o Excel pulando a primeira linha (título mesclado)
        df = pd.read_excel("BASE_FORNECEDORES.xlsx", skiprows=1)
        
        # Define os nomes das colunas baseados na sua planilha
        df.columns = ['Código', 'Fornecedor', 'CNPJ_CPF', 'Fantasia']
        
        # --- LIMPEZA DOS DADOS PARA EVITAR ERROS ---
        # Remove linhas onde o fornecedor está vazio
        df = df.dropna(subset=['Fornecedor'])
        
        # Converte para texto, remove espaços e remove erros de fórmula como "#NOME?"
        df['Fornecedor'] = df['Fornecedor'].astype(str).str.strip()
        df = df[~df['Fornecedor'].str.contains('#', na=False)]
        
        # Ordena por nome para facilitar a busca
        df = df.sort_values('Fornecedor')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}")
        return pd.DataFrame()

# --- TELA PRINCIPAL ---
st.title("📲 Registro de Promotores")
st.info("Sistema de Controle de Entrada e Saída (Base Excel)")
st.markdown("---")

# Carrega a lista de fornecedores
df_forn = buscar_fornecedores()

if not df_forn.empty:
    with st.container():
        # Seletor de Fornecedor
        # O .unique() garante que não existam nomes duplicados na lista
        lista_fornecedores = df_forn['Fornecedor'].unique().tolist()
        
        fornecedor_selecionado = st.selectbox(
            "Selecione o seu Fornecedor:", 
            options=lista_fornecedores,
            index=None,
            placeholder="Clique para escolher..."
        )
        
        # Campo de CPF
        cpf = st.text_input("Digite seu CPF (apenas números):", max_chars=11)
        
        st.write("") # Espaçamento
        col1, col2 = st.columns(2)
        
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        with col1:
            if st.button("🔴 Registrar ENTRADA", use_container_width=True):
                if cpf and fornecedor_selecionado:
                    st.success(f"**ENTRADA CONFIRMADA!**\n\n🕒 {agora}\n\n👤 CPF: {cpf}\n\n🏢 {fornecedor_selecionado}")
                    # LOGICA FUTURA: Aqui entrará o código para salvar na Google Sheets ou Banco
                else:
                    st.warning("Preencha o CPF e selecione o Fornecedor.")

        with col2:
            if st.button("🟢 Registrar SAÍDA", use_container_width=True):
                if cpf and fornecedor_selecionado:
                    st.warning(f"**SAÍDA CONFIRMADA!**\n\n🕒 {agora}\n\n👤 CPF: {cpf}\n\n🏢 {fornecedor_selecionado}")
                    # LOGICA FUTURA: Aqui entrará o código para salvar na Google Sheets ou Banco
                else:
                    st.warning("Preencha o CPF e selecione o Fornecedor.")
else:
    st.warning("⚠️ Não foi possível carregar a lista de fornecedores. Verifique o arquivo Excel.")

# --- RODAPÉ ---
st.markdown("---")
st.caption("Desenvolvido para MM Frios - Setor Fiscal")