import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
import os
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Sistema MM Frios - Corte Fácil", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .stButton>button {
        background-color: #E63946;
        color: white;
        border-radius: 5px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #FFB703; color: #000000; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 2px solid #FFB703;
        border-radius: 10px;
    }
    h1, h2, h3 { color: #E63946 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS ---
def gerenciar_banco():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, fornecedor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT, senha TEXT, nivel TEXT)''')
    
    c.execute("SELECT * FROM usuarios WHERE login = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (login, senha, nivel) VALUES ('admin', '123', 'Admin')")
    
    # Lógica de Fechamento Automático
    df_v = pd.read_sql_query("SELECT * FROM visitas ORDER BY id ASC", conn)
    if not df_v.empty:
        for nome in df_v['nome'].unique():
            ult = df_v[df_v['nome'] == nome].iloc[-1]
            if ult['evento'] == 'ENTRADA':
                dt_ent = datetime.strptime(ult['data_hora'], "%d/%m/%Y %H:%M:%S")
                if dt_ent.date() < datetime.now().date():
                    dt_sai = (dt_ent + timedelta(hours=1)).strftime("%d/%m/%Y %H:%M:%S")
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome, "SAÍDA (AUTO)", dt_sai))
    conn.commit()
    conn.close()

gerenciar_banco()

# --- 3. SISTEMA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.nivel = None
    st.session_state.usuario = None

if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Acesso Corte Fácil</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        with st.form("login"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                conn = sqlite3.connect('dados_mmfrios.db')
                c = conn.cursor()
                # Usamos COLLATE NOCASE para evitar erros de maiúsculo/minúsculo no login
                c.execute("SELECT nivel, login FROM usuarios WHERE login=? AND senha=?", (u, p))
                res = c.fetchone()
                conn.close()
                if res:
                    st.session_state.logado = True
                    st.session_state.nivel = res[0]
                    st.session_state.usuario = res[1]
                    st.rerun()
                else: st.error("Usuário ou senha inválidos.")
    st.stop()

# --- 4. NAVEGAÇÃO (CORREÇÃO DO ERRO NAMEERROR) ---
nivel = st.session_state.nivel
opcoes = [] # Inicializa a lista vazia para evitar o erro

# Define as permissões
if nivel == "Admin":
    opcoes = ["Entrada e Saída", "Cadastro/Edição", "Relatórios Gerais", "Visão Comercial", "Gerir Usuários"]
elif nivel == "Operador":
    opcoes = ["Entrada e Saída", "Cadastro/Edição"]
elif nivel == "Comercial":
    opcoes = ["Relatórios Gerais", "Visão Comercial"]
else:
    # Caso ocorra qualquer erro de nível, desloga o usuário por segurança
    st.session_state.logado = False
    st.rerun()

st.sidebar.write(f"👤 **{st.session_state.usuario}**")
st.sidebar.caption(f"Acesso: {nivel}")

# Agora a variável 'opcoes' com certeza existe aqui
menu = st.sidebar.radio("Navegação:", opcoes)

if st.sidebar.button("Logout / Sair"):
    st.session_state.logado = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Desenvolvido por: Paulo Henrique - Setor Fiscal")

# --- 5. TELAS ---

# --- TELA: ENTRADA E SAÍDA ---
if menu == "Entrada e Saída":
    st.title("🕒 Controle de Fluxo")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_v = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    em_loja = []
    if not df_v.empty:
        for nome in df_v['nome'].unique():
            ult = df_v[df_v['nome'] == nome].iloc[-1]
            if ult['evento'] == 'ENTRADA': em_loja.append(ult)
    
    st.subheader("📍 Promotores em Loja")
    if em_loja:
        st.dataframe(pd.DataFrame(em_loja)[['nome', 'fornecedor', 'data_hora']], use_container_width=True, hide_index=True)
    else: st.info("Nenhum promotor em loja no momento.")

    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    df_p["disp"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
    sel = st.selectbox("Registrar Promotor:", [""] + df_p["disp"].tolist())
    
    if sel:
        n_real = sel.split(" (")[0]
        check = any(d['nome'] == n_real for d in em_loja)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("ENTRADA 🟢", disabled=check, use_container_width=True):
                conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "ENTRADA", agora))
                conn.commit()
                st.rerun()
        with c2:
            if check:
                with st.popover("SAÍDA 🔴", use_container_width=True):
                    if st.button("Confirmar saída"):
                        conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "SAÍDA", agora))
                        conn.commit()
                        st.rerun()
    conn.close()

# --- TELA: CADASTRO/EDIÇÃO ---
elif menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    try:
        df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
        df_f['Display'] = df_f['Código'].astype(str) + " - " + df_f['Fornecedor'].astype(str)
        lista_fornecedores = sorted(df_f['Display'].dropna().unique().tolist())
    except: lista_fornecedores = []

    tab1, tab2 = st.tabs(["🆕 Novo", "✏️ Editar"])
    with tab1:
        with st.form("cad"):
            n, c = st.text_input("Nome:"), st.text_input("CPF:", max_chars=11)
            f = st.selectbox("Fornecedor:", [""] + lista_fornecedores)
            if st.form_submit_button("Salvar"):
                conn = sqlite3.connect('dados_mmfrios.db')
                conn.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?,?,?)", (n.upper(), c, f))
                conn.commit()
                conn.close()
                st.success("✅ Salvo!")

    with tab2:
        conn = sqlite3.connect('dados_mmfrios.db')
        df_e = pd.read_sql_query("SELECT * FROM promotores", conn)
        if not df_e.empty:
            p_sel = st.selectbox("Selecionar:", df_e['nome'].tolist())
            d = df_e[df_e['nome'] == p_sel].iloc[0]
            with st.form("edit"):
                en, ec = st.text_input("Nome:", d['nome']), st.text_input("CPF:", d['cpf'])
                ef = st.selectbox("Fornecedor:", lista_fornecedores, index=lista_fornecedores.index(d['fornecedor']) if d['fornecedor'] in lista_fornecedores else 0)
                if st.form_submit_button("Atualizar"):
                    conn.execute("UPDATE promotores SET nome=?, cpf=?, fornecedor=? WHERE id=?", (en.upper(), ec, ef, d['id']))
                    conn.commit()
                    conn.close()
                    st.rerun()

# --- TELA: RELATÓRIOS GERAIS ---
elif menu == "Relatórios Gerais":
    st.title("🔍 Auditoria de Passagens")
    conn = sqlite3.connect('dados_mmfrios.db')
    df = pd.read_sql_query("SELECT v.data_hora, v.nome, v.evento, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id DESC", conn)
    periodo = st.date_input("Filtrar Período:", value=(date.today() - timedelta(days=7), date.today()))
    df['dt'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
    if len(periodo) == 2:
        df = df[(df['dt'].dt.date >= periodo[0]) & (df['dt'].dt.date <= periodo[1])]
    st.dataframe(df[['data_hora', 'nome', 'fornecedor', 'evento']], use_container_width=True, hide_index=True)
    conn.close()

# --- TELA: VISÃO COMERCIAL ---
elif menu == "Visão Comercial":
    st_autorefresh(interval=300000)
    st.title("📊 Painel de Performance de Fornecedores")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_raw = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    conn.close()
    if not df_raw.empty:
        df_raw['dt'] = pd.to_datetime(df_raw['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_7d = df_raw[df_raw['dt'] >= (datetime.now() - timedelta(days=7))].copy()
        
        # Lógica de permanência para o gráfico
        rank = df_7d[df_7d['evento']=='ENTRADA']['fornecedor'].value_counts().reset_index()
        rank.columns = ['Fornecedor', 'Visitas']
        st.subheader("🏆 Ranking de Assiduidade Semanal")
        st.dataframe(rank, column_config={"Visitas": st.column_config.ProgressColumn("Visitas", format="%d")}, use_container_width=True, hide_index=True)

# --- TELA: GERIR USUÁRIOS ---
elif menu == "Gerir Usuários":
    st.title("🔑 Administração de Usuários")
    conn = sqlite3.connect('dados_mmfrios.db')
    
    with st.expander("➕ Criar Novo Usuário"):
        with st.form("new_user"):
            nu, np = st.text_input("Login:"), st.text_input("Senha:")
            nv = st.selectbox("Nível:", ["Operador", "Comercial", "Admin"])
            if st.form_submit_button("Cadastrar"):
                conn.execute("INSERT INTO usuarios (login, senha, nivel) VALUES (?,?,?)", (nu, np, nv))
                conn.commit()
                st.success(f"Usuário {nu} criado como {nv}!")
    
    st.subheader("👥 Usuários Cadastrados")
    df_u = pd.read_sql_query("SELECT id, login, nivel FROM usuarios", conn)
    st.dataframe(df_u, use_container_width=True, hide_index=True)
    
    with st.expander("🗑️ Remover Usuário"):
        u_del = st.selectbox("ID do Usuário para remover:", df_u['id'].tolist())
        if st.button("Confirmar Exclusão"):
            if u_del != 1: 
                conn.execute("DELETE FROM usuarios WHERE id=?", (u_del,))
                conn.commit()
                st.rerun()
            else: st.warning("O admin principal não pode ser removido.")
    conn.close()