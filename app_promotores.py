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
        padding: 10px;
    }
    h1, h2, h3 { color: #E63946 !important; }
    </style>
""", unsafe_allow_html=True)

DEPTOS = [
    "CARNES", "PEIXES E CRUSTACEOS", "PERECIVEIS LACTEOS", "PERECIVEIS RESF E CONG",
    "AVES INTEIRAS E CORTES", "BAZAR", "DESCARTAVEIS", "MATINAIS", "MERCEARIA ALTO GIRO",
    "MERCEARIA LIQUIDA", "LIMPEZA", "MERCEARIA DOCE", "HIGIENE E BELEZA", "HORTIFRUTI",
    "PADARIA", "PETS", "AUTOMOTIVOS", "CONFEITARIA"
]

# --- 2. BANCO DE DADOS ---
def gerenciar_banco():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, fornecedor TEXT, departamento TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT, senha TEXT, nivel TEXT)''')
    try: c.execute("SELECT departamento FROM promotores LIMIT 1")
    except: c.execute("ALTER TABLE promotores ADD COLUMN departamento TEXT DEFAULT 'N/A'")
    c.execute("SELECT * FROM usuarios WHERE login = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (login, senha, nivel) VALUES ('admin', '123456', 'Admin')")
    conn.commit()
    conn.close()

gerenciar_banco()

# --- 3. LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.nivel, st.session_state.usuario = False, None, None

if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Acesso Corte Fácil</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        if os.path.exists("LOGO_CORTE-FACIL2.png"): st.image("LOGO_CORTE-FACIL2.png", use_container_width=True)
        with st.form("login"):
            u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                conn = sqlite3.connect('dados_mmfrios.db')
                res = conn.execute("SELECT nivel, login FROM usuarios WHERE login=? AND senha=?", (u, p)).fetchone()
                conn.close()
                if res:
                    st.session_state.logado, st.session_state.nivel, st.session_state.usuario = True, res[0], res[1]
                    st.rerun()
                else: st.error("Incorreto.")
    st.stop()

# --- 4. BARRA LATERAL ---
if os.path.exists("LOGO_CORTE-FACIL2.png"): st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)
st.sidebar.markdown(f"👤 **{st.session_state.usuario}** ({st.session_state.nivel})")
st.sidebar.markdown("---")

opcoes = ["Entrada e Saída", "Cadastro/Edição", "Relatórios Gerais", "Visão Comercial", "Gerir Usuários"] if st.session_state.nivel == "Admin" else ["Entrada e Saída", "Cadastro/Edição"] if st.session_state.nivel == "Operador" else ["Relatórios Gerais", "Visão Comercial"]
menu = st.sidebar.radio("Navegação:", opcoes)

if st.sidebar.button("Logout / Sair"):
    st.session_state.logado = False
    st.rerun()

# --- 5. TELAS ---

if menu == "Entrada e Saída":
    st.title("🕒 Controle de Fluxo")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_v = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor, p.departamento FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    em_loja = [df_v[df_v['nome'] == n].iloc[-1] for n in df_v['nome'].unique() if df_v[df_v['nome'] == n].iloc[-1]['evento'] == 'ENTRADA'] if not df_v.empty else []
    
    st.subheader("📍 Promotores em Loja")
    if em_loja: st.dataframe(pd.DataFrame(em_loja)[['nome', 'fornecedor', 'departamento', 'data_hora']], use_container_width=True, hide_index=True)
    else: st.info("Ninguém em loja.")

    df_p = pd.read_sql_query("SELECT nome, fornecedor, departamento FROM promotores", conn)
    df_p["disp"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
    sel = st.selectbox("Registrar Promotor:", [""] + df_p["disp"].tolist())
    
    if sel:
        n_real = sel.split(" (")[0]
        check = any(d['nome'] == n_real for d in em_loja)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        c1, c2 = st.columns(2)
        with c1:
            if not check:
                with st.popover("ENTRADA 🟢", use_container_width=True):
                    if st.button("Confirmar Entrada"):
                        conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "ENTRADA", agora))
                        conn.commit()
                        st.success(f"Entrada de {n_real} registrada!")
                        st.rerun()
        with c2:
            if check:
                with st.popover("SAÍDA 🔴", use_container_width=True):
                    if st.button("Confirmar Saída"):
                        conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "SAÍDA", agora))
                        conn.commit()
                        st.success(f"Saída de {n_real} registrada!")
                        st.rerun()
    conn.close()

elif menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    try:
        df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
        df_f['Display'] = df_f['Código'].astype(str) + " - " + df_f['Fornecedor'].astype(str)
        lista_fornecedores = sorted(df_f['Display'].dropna().unique().tolist())
    except: lista_fornecedores = []

    tab1, tab2 = st.tabs(["🆕 Novo", "✏️ Editar"])
    with tab1:
        with st.form("cad_p"):
            n, c = st.text_input("Nome:"), st.text_input("CPF:", max_chars=11)
            f, d_s = st.selectbox("Fornecedor:", [""] + lista_fornecedores), st.selectbox("Departamento:", [""] + DEPTOS)
            if st.form_submit_button("Salvar Cadastro"):
                if n and c and f and d_s:
                    conn = sqlite3.connect('dados_mmfrios.db')
                    conn.execute("INSERT INTO promotores (nome, cpf, fornecedor, departamento) VALUES (?,?,?,?)", (n.upper(), c, f, d_s))
                    conn.commit(); conn.close()
                    st.success(f"✅ Promotor {n.upper()} cadastrado com sucesso!")
                else: st.warning("Preencha tudo.")

    with tab2:
        conn = sqlite3.connect('dados_mmfrios.db')
        df_e = pd.read_sql_query("SELECT * FROM promotores", conn)
        if not df_e.empty:
            p_sel = st.selectbox("Selecionar Promotor:", df_e['nome'].tolist())
            d = df_e[df_e['nome'] == p_sel].iloc[0]
            # RESET DO FORMULÁRIO: O uso de key contendo o ID garante atualização total
            with st.form(key=f"edit_p_form_{d['id']}"):
                en = st.text_input("Nome:", value=d['nome'])
                ec = st.text_input("CPF:", value=d['cpf'])
                ef = st.selectbox("Fornecedor:", lista_fornecedores, index=lista_fornecedores.index(d['fornecedor']) if d['fornecedor'] in lista_fornecedores else 0)
                ed = st.selectbox("Departamento:", DEPTOS, index=DEPTOS.index(d['departamento']) if d['departamento'] in DEPTOS else 0)
                if st.form_submit_button("Atualizar Dados"):
                    conn.execute("UPDATE promotores SET nome=?, cpf=?, fornecedor=?, departamento=? WHERE id=?", (en.upper(), ec, ef, ed, d['id']))
                    conn.commit(); conn.close()
                    st.success(f"✅ Cadastro de {en.upper()} atualizado!")
                    st.rerun()
        conn.close()

elif menu == "Relatórios Gerais":
    st.title("🔍 Auditoria")
    conn = sqlite3.connect('dados_mmfrios.db')
    df = pd.read_sql_query("SELECT v.data_hora, v.nome, v.evento, p.fornecedor, p.departamento FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id DESC", conn)
    periodo = st.date_input("Filtrar:", value=(date.today() - timedelta(days=7), date.today()))
    df['dt'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
    if len(periodo) == 2:
        df = df[(df['dt'].dt.date >= periodo[0]) & (df['dt'].dt.date <= periodo[1])]
    st.dataframe(df[['data_hora', 'nome', 'fornecedor', 'departamento', 'evento']], use_container_width=True, hide_index=True)
    conn.close()

elif menu == "Visão Comercial":
    st_autorefresh(interval=300000)
    st.title("📊 Painel de Indicadores")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_raw = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor, p.departamento FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    conn.close()
    if not df_raw.empty:
        df_raw['dt'] = pd.to_datetime(df_raw['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_7d = df_raw[df_raw['dt'] >= (datetime.now() - timedelta(days=7))].copy()
        f_data = []
        for (nome, dia), gp in df_7d.groupby(['nome', df_7d['dt'].dt.date]):
            ent, sai = gp[gp['evento'] == 'ENTRADA']['dt'].min(), gp[gp['evento'].str.contains('SAÍDA')]['dt'].max()
            minutos = (sai - ent).total_seconds()/60 if pd.notnull(sai) and len(gp) > 1 else 0
            f_data.append({"Data": dia.strftime("%d/%m/%Y"), "Fornecedor": gp['fornecedor'].iloc[0], "Departamento": gp['departamento'].iloc[0], "Promotor": nome, "Permanência": f"{int(minutos//60)}h {int(minutos%60)}min" if minutos > 0 else "Em Loja", "min": round(minutos, 2)})
        df_final = pd.DataFrame(f_data)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Empresas/Semana", df_final['Fornecedor'].nunique())
        c2.metric("Total Visitas", len(df_final))
        media = int(df_final[df_final['min']>0]['min'].mean() if not df_final[df_final['min']>0].empty else 0)
        c3.metric("Média Permanência", f"{media} min")

        st.subheader("🏆 Ranking de Assiduidade")
        rank = df_final['Fornecedor'].value_counts().reset_index()
        rank.columns = ['Fornecedor', 'Visitas']
        st.dataframe(rank, column_config={"Visitas": st.column_config.ProgressColumn("Qtd Visitas", format="%d", min_value=0, max_value=int(rank['Visitas'].max()))}, use_container_width=True, hide_index=True)

        st.subheader("📋 Relatório Detalhado")
        st.dataframe(df_final.drop(columns=['min']).sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)
        csv = df_final.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar CSV", csv, "performance.csv", "text/csv", use_container_width=True)

elif menu == "Gerir Usuários":
    st.title("🔑 Administração de Usuários")
    conn = sqlite3.connect('dados_mmfrios.db')
    t1, t2, t3 = st.tabs(["➕ Novo Usuário", "✏️ Editar Usuário", "🗑️ Remover Usuário"])
    with t1:
        with st.form("new_u_form"):
            nu, np = st.text_input("Login:"), st.text_input("Senha (mín. 6):", type="password")
            nv = st.selectbox("Nível:", ["Operador", "Comercial", "Admin"])
            if st.form_submit_button("Confirmar Cadastro"):
                if len(np) < 6: st.error("Mínimo 6 dígitos.")
                else:
                    conn.execute("INSERT INTO usuarios (login, senha, nivel) VALUES (?,?,?)", (nu, np, nv))
                    conn.commit()
                    st.success(f"✅ Usuário '{nu}' criado com sucesso!")
                    st.rerun()
    with t2:
        df_u = pd.read_sql_query("SELECT * FROM usuarios", conn)
        u_ed = st.selectbox("Selecionar Usuário para editar:", df_u['login'].tolist())
        du = df_u[df_u['login'] == u_ed].iloc[0]
        with st.form(key=f"edit_u_form_{du['id']}"):
            nl, ns = st.text_input("Login:", value=du['login']), st.text_input("Senha:", value=du['senha'], type="password")
            nv = st.selectbox("Nível:", ["Operador", "Comercial", "Admin"], index=["Operador", "Comercial", "Admin"].index(du['nivel']))
            if st.form_submit_button("Salvar Alterações"):
                if len(ns) < 6: st.error("Mínimo 6 dígitos.")
                else:
                    conn.execute("UPDATE usuarios SET login=?, senha=?, nivel=? WHERE id=?", (nl, ns, nv, du['id']))
                    conn.commit()
                    st.success(f"✅ Alterações no usuário '{nl}' salvas com sucesso!")
                    st.rerun()
    with t3:
        df_u = pd.read_sql_query("SELECT * FROM usuarios", conn)
        u_rm = st.selectbox("Selecionar usuário para remover:", df_u['id'].tolist(), format_func=lambda x: df_u[df_u['id']==x]['login'].values[0])
        if st.button("Confirmar Remoção Permanente"):
            login_del = df_u[df_u['id']==u_rm]['login'].values[0]
            if u_rm != 1: 
                conn.execute("DELETE FROM usuarios WHERE id=?", (u_rm,))
                conn.commit()
                st.success(f"✅ Usuário '{login_del}' removido com sucesso!")
                st.rerun()
            else: st.warning("O administrador principal não pode ser removido.")
    conn.close()