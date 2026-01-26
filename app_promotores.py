import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. BANCO DE DADOS ---
def criar_tabelas():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, fornecedor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    conn.commit()
    conn.close()

criar_tabelas()

# --- 3. LOGO E FORNECEDORES ---
# Exibe a logo se o arquivo existir na pasta PILOTO/APP_PROMOTORES
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)
else:
    st.sidebar.title("🛡️ MM FRIOS")

# Carrega fornecedores da Coluna B do Excel
try:
    # Lendo o Excel e focando na coluna 'Fornecedor'
    df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
    
    # Filtramos para pegar a coluna B, remover vazios e erros de fórmula (#NOME?)
    lista_fornecedores = df_f['Fornecedor'].dropna().astype(str)
    lista_fornecedores = lista_fornecedores[~lista_fornecedores.str.contains('#NOME?')].unique().tolist()
    lista_fornecedores = sorted(lista_fornecedores)
except Exception as e:
    st.sidebar.error(f"Erro ao carregar Excel: {e}")
    lista_fornecedores = ["FORNECEDOR NÃO ENCONTRADO"]

# --- 4. MENU LATERAL ---
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["Cadastro de Promotor", "Entrada e Saída", "Relatórios"])

# --- 5. ABA: CADASTRO ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotores")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo do Promotor:")
        cpf = st.text_input("CPF (11 números):", max_chars=11)
        
        # Agora a lista de fornecedores deve aparecer aqui
        fornecedor_sel = st.selectbox("Selecione a Empresa (Fornecedor):", [""] + lista_fornecedores)
        
        submit = st.form_submit_button("Salvar Cadastro")

        if submit:
            if nome and len(cpf) == 11 and fornecedor_sel != "":
                conn = sqlite3.connect('dados_mmfrios.db')
                c = conn.cursor()
                c.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?, ?, ?)", 
                          (nome.upper().strip(), cpf, fornecedor_sel))
                conn.commit()
                conn.close()
                st.success(f"✅ {nome.upper()} vinculado à {fornecedor_sel} com sucesso!")
            else:
                st.warning("⚠️ Preencha Nome, CPF e selecione um Fornecedor.")

# --- 6. ABA: ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Registro de Acesso")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    conn.close()

    if not df_p.empty:
        df_p["display"] = df_p["nome"] + " - " + df_p["fornecedor"]
        selecionado = st.selectbox("Selecione o Promotor:", [""] + df_p["display"].tolist())
        
        if selecionado:
            nome_real = selecionado.split(" - ")[0]
            col1, col2 = st.columns(2)
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with col1:
                if st.button("REGISTRAR ENTRADA", type="primary", use_container_width=True):
                    conn = sqlite3.connect('dados_mmfrios.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "ENTRADA", agora))
                    conn.commit()
                    conn.close()
                    st.success(f"Entrada de {nome_real} registrada às {agora}")
            
            with col2:
                if st.button("REGISTRAR SAÍDA", use_container_width=True):
                    conn = sqlite3.connect('dados_mmfrios.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "SAÍDA", agora))
                    conn.commit()
                    conn.close()
                    st.warning(f"Saída de {nome_real} registrada às {agora}")
    else:
        st.info("Nenhum promotor cadastrado ainda.")

# --- 7. ABA: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Painel de Controle")
    aba = st.radio("Visualizar:", ["Promotores Cadastrados", "Histórico de Visitas"], horizontal=True)
    
    conn = sqlite3.connect('dados_mmfrios.db')
    tab = "promotores" if aba == "Promotores Cadastrados" else "visitas"
    df = pd.read_sql_query(f"SELECT * FROM {tab} ORDER BY id DESC", conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)