import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
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
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)
else:
    st.sidebar.title("❄️ MM FRIOS")

try:
    df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
    lista_fornecedores = df_f['Fornecedor'].dropna().astype(str)
    lista_fornecedores = lista_fornecedores[~lista_fornecedores.str.contains('#NOME?')].unique().tolist()
    lista_fornecedores = sorted(lista_fornecedores)
except Exception as e:
    st.sidebar.error(f"Erro ao carregar fornecedores: {e}")
    lista_fornecedores = []

# --- 4. NAVEGAÇÃO ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Menu de Operações:", ["Cadastro de Promotor", "Entrada e Saída", "Relatórios", "Visão Comercial"])

# --- 5. CADASTRO ---
if menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Novos Promotores")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        cpf = st.text_input("CPF (somente 11 números):", max_chars=11)
        fornecedor_sel = st.selectbox("Selecione a Empresa Representada:", [""] + lista_fornecedores)
        submit = st.form_submit_button("Salvar Registro")

        if submit:
            if nome and len(cpf) == 11 and fornecedor_sel:
                conn = sqlite3.connect('dados_mmfrios.db')
                c = conn.cursor()
                c.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?, ?, ?)", 
                          (nome.upper().strip(), cpf, fornecedor_sel))
                conn.commit()
                conn.close()
                st.success(f"✅ {nome.upper()} cadastrado com sucesso!")
                st.balloons()
            else:
                st.error("⚠️ Preencha Nome, CPF (11 dígitos) e selecione a Empresa.")

# --- 6. ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Registro de Fluxo (Check-in / Check-out)")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    conn.close()

    if not df_p.empty:
        df_p["display"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
        selecionado = st.selectbox("Identifique o Promotor:", [""] + df_p["display"].tolist())
        
        if selecionado:
            nome_real = selecionado.split(" (")[0]
            col1, col2 = st.columns(2)
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            with col1:
                if st.button("REGISTRAR ENTRADA 🟢", type="primary", use_container_width=True):
                    conn = sqlite3.connect('dados_mmfrios.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "ENTRADA", agora))
                    conn.commit()
                    conn.close()
                    st.success(f"Entrada registrada: {agora}")
            
            with col2:
                if st.button("REGISTRAR SAÍDA 🔴", use_container_width=True):
                    conn = sqlite3.connect('dados_mmfrios.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "SAÍDA", agora))
                    conn.commit()
                    conn.close()
                    st.warning(f"Saída registrada: {agora}")
    else:
        st.info("ℹ️ Nenhum promotor cadastrado.")

# --- 7. RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Monitoramento e Histórico")
    tipo_rel = st.radio("Escolha a base de dados:", ["Promotores Cadastrados", "Histórico de Visitas"], horizontal=True)
    conn = sqlite3.connect('dados_mmfrios.db')
    tabela = "promotores" if tipo_rel == "Promotores Cadastrados" else "visitas"
    df_rel = pd.read_sql_query(f"SELECT * FROM {tabela} ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_rel, use_container_width=True)

# --- 8. NOVO: VISÃO COMERCIAL (Semana Atual) ---
elif menu == "Visão Comercial":
    st.title("📊 Performance Semanal de Fornecedores")
    st.subheader("Fornecedores que enviaram promotores nos últimos 7 dias")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    # Pegamos as visitas e os dados dos promotores para saber de qual fornecedor eles são
    query = """
    SELECT v.nome, v.evento, v.data_hora, p.fornecedor 
    FROM visitas v
    JOIN promotores p ON v.nome = p.nome
    """
    df_comercial = pd.read_sql_query(query, conn)
    conn.close()

    if not df_comercial.empty:
        # Converter a coluna de data para o formato datetime do Python para poder filtrar
        df_comercial['data_hora'] = pd.to_datetime(df_comercial['data_hora'], format="%d/%m/%Y %H:%M:%S")
        
        # Filtro: Últimos 7 dias
        uma_semana_atras = datetime.now() - timedelta(days=7)
        df_semana = df_comercial[df_comercial['data_hora'] >= uma_semana_atras]

        if not df_semana.empty:
            # Lista única de fornecedores que apareceram
            fornecedores_ativos = df_semana['fornecedor'].unique()
            
            col_metric, col_table = st.columns([1, 2])
            
            with col_metric:
                st.metric("Total de Fornecedores na Semana", len(fornecedores_ativos))
                st.write("✅ **Empresas Ativas:**")
                for f in sorted(fornecedores_ativos):
                    st.write(f"- {f}")
            
            with col_table:
                st.write("📋 **Detalhamento de Visitas (Semana)**")
                # Formatando a data para exibição mais bonita
                df_exibir = df_semana.copy()
                df_exibir['data_hora'] = df_exibir['data_hora'].dt.strftime('%d/%m (%a) - %H:%M')
                st.dataframe(df_exibir[['fornecedor', 'nome', 'data_hora', 'evento']], use_container_width=True)
        else:
            st.warning("Nenhuma visita registrada nos últimos 7 dias.")
    else:
        st.info("Ainda não há dados de visitas para analisar.")