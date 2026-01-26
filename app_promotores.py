import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
# O Streamlit buscará as credenciais automaticamente no painel de Secrets (TOML)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Wsx93H2clHbwc95J3vZ4j0AMDeOHOg3wBKiomtyDljI/edit#gid=0"
except Exception as e:
    st.error(f"Erro de conexão: Verifique os Secrets no Streamlit Cloud.")
    st.stop()

# --- 3. MENU LATERAL ---
# Verifica se a logo existe na pasta do projeto
caminho_logo = "LOGO_CORTE-FACIL2.png"
if os.path.exists(caminho_logo):
    st.sidebar.image(caminho_logo, use_container_width=True)
else:
    # Logo reserva caso o arquivo não seja encontrado
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1067/1067566.png", width=80)

st.sidebar.title("Menu de Gestão")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotor", "Relatórios"])

# --- 4. ABA: CADASTRO DE PROMOTOR ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    st.markdown("---")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo:", placeholder="Ex: João Silva")
        
        with col2:
            cpf = st.text_input("CPF (apenas 11 números):", max_chars=11, placeholder="00011122233")
            
        submit = st.form_submit_button("Finalizar e Salvar Cadastro")

        if submit:
            # Validação simples de preenchimento
            if nome and len(cpf) == 11 and cpf.isdigit():
                try:
                    # 1. Lê os dados atuais da aba CADASTRO
                    df_existente = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
                    
                    # 2. Prepara o novo registro
                    novo_registro = pd.DataFrame([{"NOME": nome.upper().strip(), "CPF": cpf}])
                    
                    # 3. Une o novo registro à lista que já existia
                    df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
                    
                    # 4. Salva a planilha inteira atualizada
                    conn.update(spreadsheet=URL_PLANILHA, worksheet="CADASTRO", data=df_atualizado)
                    
                    st.success(f"✅ {nome.upper()} cadastrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")
            else:
                st.warning("⚠️ Preencha o nome e o CPF corretamente (11 números).")

    # Exibe a lista de promotores logo abaixo
    st.markdown("### Promotores Ativos")
    try:
        df_lista = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        if not df_lista.empty:
            st.dataframe(df_lista.sort_index(ascending=False), use_container_width=True)
        else:
            st.info("Nenhum promotor cadastrado ainda.")
    except:
        st.info("Aguardando sincronização com o Google Sheets...")

# --- 5. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Painel de Controle")
    st.markdown("---")
    
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="CADASTRO")
        if not df.empty:
            st.metric("Total de Promotores", len(df))
            st.dataframe(df, use_container_width=True)
            
            # Opção de download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar Lista (CSV)", csv, "promotores.csv", "text/csv")
        else:
            st.warning("Nenhum dado disponível para gerar relatório.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")