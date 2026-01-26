import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. FUNÇÕES DO BANCO DE DADOS (SQLite) ---
def criar_tabelas():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    # Tabela de Promotores
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT)''')
    # Tabela de Visitas
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    conn.commit()
    conn.close()

criar_tabelas()

# --- 3. MENU LATERAL ---
st.sidebar.title("🛡️ Prevenção de Perdas")
menu = st.sidebar.radio("Navegação", ["Cadastro de Promotor", "Entrada e Saída", "Relatórios"])

# --- 4. ABA: CADASTRO ---
if menu == "Cadastro de Promotor":
    st.title("👤 Novo Cadastro de Promotor")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (11 números):", max_chars=11)
        submit = st.form_submit_button("Salvar no Banco")

        if submit:
            if nome and len(cpf) == 11:
                conn = sqlite3.connect('dados_mmfrios.db')
                c = conn.cursor()
                c.execute("INSERT INTO promotores (nome, cpf) VALUES (?, ?)", (nome.upper().strip(), cpf))
                conn.commit()
                conn.close()
                st.success(f"✅ {nome.upper()} cadastrado com sucesso!")
            else:
                st.warning("Preencha os dados corretamente.")

# --- 5. ABA: ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Fluxo de Acesso")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_p = pd.read_sql_query("SELECT nome FROM promotores", conn)
    conn.close()

    if not df_p.empty:
        lista = sorted(df_p["nome"].unique().tolist())
        selecionado = st.selectbox("Selecione o Promotor:", [""] + lista)
        
        if selecionado:
            col1, col2 = st.columns(2)
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with col1:
                if st.button("REGISTRAR ENTRADA", type="primary", use_container_width=True):
                    conn = sqlite3.connect('dados_mmfrios.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", 
                              (selecionado, "ENTRADA", agora))
                    conn.commit()
                    conn.close()
                    st.success(f"Entrada registrada: {agora}")
            
            with col2:
                if st.button("REGISTRAR SAÍDA", use_container_width=True):
                    conn = sqlite3.connect('dados_mmfrios.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", 
                              (selecionado, "SAÍDA", agora))
                    conn.commit()
                    conn.close()
                    st.warning(f"Saída registrada: {agora}")
    else:
        st.info("Cadastre um promotor primeiro.")

# --- 6. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Histórico Geral")
    aba = st.radio("Ver:", ["Promotores", "Visitas"], horizontal=True)
    
    conn = sqlite3.connect('dados_mmfrios.db')
    tabela = "promotores" if aba == "Promotores" else "visitas"
    df = pd.read_sql_query(f"SELECT * FROM {tabela} ORDER BY id DESC", conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)