import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
import os

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Sistema MM Frios - Corte Fácil", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .stButton>button {
        background-color: #E63946; color: white; border-radius: 5px; font-weight: bold; width: 100%;
    }
    h1, h2, h3 { color: #E63946 !important; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #E63946; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 10px; padding: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS E FUNÇÕES DE SUPORTE ---
def init_db():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, 
                  fornecedor_fantasia TEXT, comprador TEXT, departamento TEXT, dias_visita TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT, senha TEXT, nivel TEXT)''')
    
    finalizar_visitas_esquecidas(conn)
    
    c.execute("SELECT * FROM usuarios WHERE login = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (login, senha, nivel) VALUES ('admin', '123456', 'Administrador')")
    conn.commit()
    return conn

def finalizar_visitas_esquecidas(conn):
    cursor = conn.cursor()
    df_v = pd.read_sql_query("SELECT * FROM visitas", conn)
    if df_v.empty: return
    hoje_str = date.today().strftime("%d/%m/%Y")
    for nome in df_v['nome'].unique():
        visitas_p = df_v[df_v['nome'] == nome].sort_values('id')
        ultima = visitas_p.iloc[-1]
        if ultima['evento'] == 'ENTRADA':
            data_entrada_str = ultima['data_hora'].split(' ')[0]
            if data_entrada_str != hoje_str:
                try:
                    dt_ent = datetime.strptime(ultima['data_hora'], "%d/%m/%Y %H:%M:%S")
                    dt_saida = dt_ent + timedelta(hours=1)
                    saida_str = dt_saida.strftime("%d/%m/%Y %H:%M:%S")
                    cursor.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, 'SAÍDA', ?)", (nome, saida_str))
                except: pass
    conn.commit()

@st.cache_data
def carregar_base_fornecedores():
    try:
        df = pd.read_excel("BASE_FORNECEDORES.xlsx")
        df['FANTASIA'] = df['FANTASIA'].astype(str).str.strip().str.upper()
        df['COMPRADOR'] = df['COMPRADOR'].fillna("N/A").astype(str).str.strip().str.upper()
        mapa = dict(zip(df['FANTASIA'], df['COMPRADOR']))
        lista = sorted([f for f in df['FANTASIA'].unique() if f != "NAN"])
        return lista, mapa
    except: return [], {}

LISTA_FANTASIA, MAPA_COMPRADORES = carregar_base_fornecedores()
DEPTOS = ["CARNES", "PEIXES E CRUSTACEOS", "PERECIVEIS LACTEOS", "PERECIVEIS RESF E CONG", 
          "AVES INTEIRAS E CORTES", "BAZAR", "DESCARTAVEIS", "MATINAIS", "MERCEARIA ALTO GIRO", 
          "MERCEARIA LIQUIDA", "LIMPEZA", "MERCEARIA DOCE", "HIGIENE E BELZA", "HORTIFRUTI", 
          "PADARIA", "PETS", "AUTOMOTIVOS", "CONFEITARIA"]
DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
NIVEIS_ACESSO = ["Operador", "Comercial", "Administrador", "Master"]

# --- 3. LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.update({'logado': False, 'nivel': None, 'usuario': None})

if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Acesso Corte Fácil</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        if os.path.exists("LOGO_CORTE-FACIL2.png"): st.image("LOGO_CORTE-FACIL2.png")
        with st.form("login"):
            u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                conn = init_db()
                res = conn.execute("SELECT nivel, login FROM usuarios WHERE login=? AND senha=?", (u, p)).fetchone()
                conn.close()
                if res:
                    st.session_state.update({'logado': True, 'nivel': res[0], 'usuario': res[1]})
                    st.rerun()
                else: st.error("Incorreto.")
    st.stop()

# --- 4. BARRA LATERAL ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)
st.sidebar.markdown(f"👤 **{st.session_state.usuario}**\n\n🎯 Nível: `{st.session_state.nivel}`")

opcoes_menu = ["Entrada e Saída", "Cadastro/Edição", "Relatórios", "Visão Comercial"]
nivel_user = str(st.session_state.nivel).upper()
if "ADMIN" in nivel_user or "MASTER" in nivel_user:
    opcoes_menu.append("Gestão de Usuários")

menu = st.sidebar.radio("Navegação:", opcoes_menu)
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- 5. TELAS ---

if menu == "Entrada e Saída":
    st.title("🕒 Portaria - Controle de Fluxo")
    conn = init_db()
    df_v = pd.read_sql_query("SELECT * FROM visitas", conn)
    em_loja_nomes = []
    horarios_checkin = {}
    if not df_v.empty:
        for nome in df_v['nome'].unique():
            ult = df_v[df_v['nome'] == nome].iloc[-1]
            if ult['evento'] == 'ENTRADA':
                em_loja_nomes.append(nome)
                horarios_checkin[nome] = ult['data_hora']

    st.subheader("📍 Promotores em Loja")
    if em_loja_nomes:
        df_p = pd.read_sql_query(f"SELECT nome, fornecedor_fantasia, comprador FROM promotores WHERE nome IN ({','.join(['?']*len(em_loja_nomes))})", conn, params=em_loja_nomes)
        df_p['Horário Check-in'] = df_p['nome'].map(horarios_checkin)
        st.dataframe(df_p, use_container_width=True, hide_index=True)
    
    df_lista = pd.read_sql_query("SELECT nome, fornecedor_fantasia FROM promotores", conn)
    df_lista["display"] = df_lista["nome"] + " - (" + df_lista["fornecedor_fantasia"] + ")"
    sel = st.selectbox("Registrar Movimentação:", [""] + df_lista["display"].tolist())
    if sel:
        n_sel = sel.split(" - (")[0]
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if n_sel not in em_loja_nomes:
            if st.button("CONFIRMAR ENTRADA 🟢"):
                conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, 'ENTRADA', ?)", (n_sel, agora))
                conn.commit(); st.success(f"Entrada registrada para {n_sel}"); st.rerun()
        else:
            if st.button("CONFIRMAR SAÍDA 🔴"):
                conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, 'SAÍDA', ?)", (n_sel, agora))
                conn.commit(); st.warning(f"Saída registrada para {n_sel}"); st.rerun()
    conn.close()

elif menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    tab1, tab2 = st.tabs(["Novo Cadastro", "Editar/Excluir"])
    with tab1:
        with st.form("novo_p", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo:")
            cpf = c2.text_input("CPF (Exatos 11 números):", max_chars=11)
            fantasia = st.selectbox("Fornecedor (Fantasia):", [""] + LISTA_FANTASIA)
            depto = st.selectbox("Departamento:", DEPTOS)
            dias = st.multiselect("Dias previstos de visita:", DIAS_SEMANA)
            if st.form_submit_button("Salvar Cadastro"):
                if len(cpf) == 11 and cpf.isdigit() and nome and fantasia and dias:
                    conn = init_db()
                    comp = MAPA_COMPRADORES.get(fantasia, "N/A")
                    conn.execute("INSERT INTO promotores (nome, cpf, fornecedor_fantasia, comprador, departamento, dias_visita) VALUES (?,?,?,?,?,?)",
                                 (nome.upper(), cpf, fantasia, comp, depto, ", ".join(dias)))
                    conn.commit(); conn.close(); st.success("Cadastrado com sucesso!")
                else: st.error("Verifique os campos.")
    with tab2:
        conn = init_db()
        df_edit = pd.read_sql_query("SELECT * FROM promotores", conn)
        if not df_edit.empty:
            p_alvo = st.selectbox("Editar Promotor:", df_edit['nome'].tolist())
            d = df_edit[df_edit['nome'] == p_alvo].iloc[0]
            with st.form("edit_p"):
                en = st.text_input("Nome:", value=d['nome'])
                ef = st.selectbox("Fornecedor:", LISTA_FANTASIA, index=LISTA_FANTASIA.index(d['fornecedor_fantasia']) if d['fornecedor_fantasia'] in LISTA_FANTASIA else 0)
                ed = st.selectbox("Departamento:", DEPTOS, index=DEPTOS.index(d['departamento']) if d['departamento'] in DEPTOS else 0)
                edias = st.multiselect("Dias:", DIAS_SEMANA, default=d['dias_visita'].split(", ") if d['dias_visita'] else [])
                if st.form_submit_button("Atualizar"):
                    conn.execute("UPDATE promotores SET nome=?, fornecedor_fantasia=?, comprador=?, departamento=?, dias_visita=? WHERE id=?", 
                                 (en.upper(), ef, MAPA_COMPRADORES.get(ef, "N/A"), ed, ", ".join(edias), d['id']))
                    conn.commit(); st.success("Cadastro atualizado com sucesso!"); st.rerun()
        conn.close()

elif menu == "Relatórios":
    st.title("📋 Relatório Detalhado")
    c1, c2, c3 = st.columns([1,1,2])
    di = c1.date_input("De:", value=date.today() - timedelta(days=7))
    dfim = c2.date_input("Até:", value=date.today())
    f_forn = c3.text_input("🔍 Filtrar por Fornecedor (Ex: ACIOLY):").strip().upper()
    
    conn = init_db()
    df_v = pd.read_sql_query("SELECT * FROM visitas", conn)
    df_p = pd.read_sql_query("SELECT nome, fornecedor_fantasia, comprador, departamento FROM promotores", conn)
    conn.close()
    
    if not df_v.empty:
        df = pd.merge(df_v, df_p, on='nome')
        df['dt_obj'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_f = df[(df['dt_obj'].dt.date >= di) & (df['dt_obj'].dt.date <= dfim)].copy()
        
        if f_forn:
            df_f = df_f[df_f['fornecedor_fantasia'].str.contains(f_forn, na=False)]

        st.dataframe(df_f.drop(columns=['dt_obj']), use_container_width=True, hide_index=True)

elif menu == "Visão Comercial":
    st.title("📊 Indicadores Comerciais")
    
    c1, c2, c3 = st.columns([1,1,2])
    di = c1.date_input("Início:", value=date.today() - timedelta(days=30))
    dfim = c2.date_input("Fim:", value=date.today())
    
    conn = init_db()
    df_v = pd.read_sql_query("SELECT * FROM visitas", conn)
    df_p = pd.read_sql_query("SELECT nome, fornecedor_fantasia, comprador FROM promotores", conn)
    conn.close()
    
    if not df_v.empty:
        df = pd.merge(df_v, df_p, on='nome')
        df['dt'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_f = df[(df['dt'].dt.date >= di) & (df['dt'].dt.date <= dfim)].copy()
        
        lista_compradores = ["TODOS"] + sorted([c for c in df_f['comprador'].unique() if c])
        comp_sel = c3.selectbox("Filtrar por Comprador:", lista_compradores)
        if comp_sel != "TODOS":
            df_f = df_f[df_f['comprador'] == comp_sel]

        # --- Cálculo de Permanência para KPIs ---
        entradas = df_f[df_f['evento'] == 'ENTRADA'].copy()
        saidas = df_f[df_f['evento'] == 'SAÍDA'].copy()
        tempos = []
        for i, ent in entradas.iterrows():
            prox_saida = saidas[(saidas['nome'] == ent['nome']) & (saidas['dt'] > ent['dt'])].sort_values('dt')
            if not prox_saida.empty:
                diff = prox_saida.iloc[0]['dt'] - ent['dt']
                tempos.append(diff.total_seconds() / 60)
            else: tempos.append(None)
        entradas['Minutos'] = tempos
        df_limpo = entradas.dropna(subset=['Minutos'])

        # --- KPI's Superiores ---
        k1, k2, k3 = st.columns(3)
        k1.metric("Visitas no Período", len(entradas))
        k2.metric("Tempo Médio de Loja", f"{round(df_limpo['Minutos'].mean(), 1)} min" if not df_limpo.empty else "0 min")
        k3.metric("Forn. mais Ativo (Visitas)", entradas['fornecedor_fantasia'].mode()[0] if not entradas.empty else "-")

        st.markdown("---")

        # --- 1. SEÇÃO DE VISITAS (VOLUME) ---
        st.subheader("🏆 Ranking por Volume de Visitas")
        if not entradas.empty:
            ranking_visitas = entradas['fornecedor_fantasia'].value_counts().reset_index()
            ranking_visitas.columns = ['Fornecedor', 'Total de Visitas']
            st.bar_chart(ranking_visitas.set_index('Fornecedor'))
            st.dataframe(ranking_visitas, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- 2. SEÇÃO DE PERMANÊNCIA (MÉDIA) ---
        st.subheader("⏱️ Média de Permanência por Fornecedor (Minutos)")
        if not df_limpo.empty:
            media_forn = df_limpo.groupby('fornecedor_fantasia')['Minutos'].mean().sort_values(ascending=False).reset_index()
            media_forn.columns = ['Fornecedor', 'Média (Min)']
            st.bar_chart(media_forn.set_index('Fornecedor'))
            st.dataframe(media_forn, use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados suficientes para gerar médias de permanência.")

elif menu == "Gestão de Usuários":
    st.title("🔐 Administração de Usuários")
    conn = init_db()
    tab_list, tab_edit = st.tabs(["Cadastrar / Listar", "Editar Usuário"])
    with tab_list:
        with st.form("novo_u"):
            c1, c2, c3 = st.columns(3)
            nu, ns, nn = c1.text_input("Login"), c2.text_input("Senha"), c3.selectbox("Nível", NIVEIS_ACESSO)
            if st.form_submit_button("Criar Usuário"):
                conn.execute("INSERT INTO usuarios (login, senha, nivel) VALUES (?,?,?)", (nu, ns, nn))
                conn.commit(); st.success("Usuário criado!"); st.rerun()
        df_u = pd.read_sql_query("SELECT id, login, nivel FROM usuarios", conn)
        st.dataframe(df_u, use_container_width=True, hide_index=True)
    with tab_edit:
        user_edit = st.selectbox("Selecione o usuário para editar:", df_u['login'].tolist())
        u_dados = conn.execute("SELECT * FROM usuarios WHERE login=?", (user_edit,)).fetchone()
        
        # CORREÇÃO DO ERRO list.index(x)
        nivel_db = u_dados[3]
        if nivel_db in NIVEIS_ACESSO:
            idx_nivel = NIVEIS_ACESSO.index(nivel_db)
        else:
            idx_nivel = 0 # Valor padrão caso não encontre
            
        with st.form("edit_u"):
            nl, ns = st.text_input("Login", u_dados[1]), st.text_input("Senha", u_dados[2])
            nv = st.selectbox("Nível", NIVEIS_ACESSO, index=idx_nivel)
            if st.form_submit_button("Atualizar Usuário"):
                conn.execute("UPDATE usuarios SET login=?, senha=?, nivel=? WHERE id=?", (nl, ns, nv, u_dados[0]))
                conn.commit(); st.success("Usuário atualizado com sucesso!"); st.rerun()
    conn.close()