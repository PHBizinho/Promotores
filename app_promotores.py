import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
import os
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURAÇÃO E ESTILO CORTE FÁCIL ---
st.set_page_config(page_title="Sistema MM Frios - Corte Fácil", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    :root {
        --vermelho: #E63946;
        --amarelo: #FFB703;
        --cinza: #F1F1F1;
    }
    .stApp { background-color: var(--cinza); }
    .stButton>button {
        background-color: var(--vermelho);
        color: white;
        border-radius: 8px;
        border: 2px solid var(--amarelo);
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid var(--vermelho);
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    h1, h2, h3 { color: var(--vermelho); }
    </style>
""", unsafe_allow_html=True)

# --- 2. BANCO DE DADOS E LÓGICA DE AUTO-ENCERRAMENTO ---
def gerenciar_banco():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, fornecedor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    
    # --- LOGICA 3.2: ENCERRAMENTO AUTOMÁTICO (FECHAMENTO DE ONTEM) ---
    # Busca todas as ENTRADAS que não possuem uma SAÍDA posterior do mesmo promotor
    df_v = pd.read_sql_query("SELECT * FROM visitas ORDER BY id ASC", conn)
    if not df_v.empty:
        for nome in df_v['nome'].unique():
            p_visitas = df_v[df_v['nome'] == nome].iloc[-1]
            if p_visitas['evento'] == 'ENTRADA':
                data_entrada = datetime.strptime(p_visitas['data_hora'], "%d/%m/%Y %H:%M:%S")
                # Se a entrada foi em um dia anterior ao hoje
                if data_entrada.date() < datetime.now().date():
                    # Registra saída automática 1 hora após a entrada
                    data_saida_auto = data_entrada + timedelta(hours=1)
                    data_saida_str = data_saida_auto.strftime("%d/%m/%Y %H:%M:%S")
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", 
                              (nome, "SAÍDA (AUTO)", data_saida_str))
    
    conn.commit()
    conn.close()

gerenciar_banco()

# --- 3. RECURSOS ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)

try:
    df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
    df_f['Display'] = df_f['Código'].astype(str) + " - " + df_f['Fornecedor'].astype(str)
    lista_fornecedores = sorted(df_f['Display'].dropna().unique().tolist())
except:
    lista_fornecedores = []

# --- 4. NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação:", ["Cadastro/Edição", "Entrada e Saída", "Relatórios Gerais", "Visão Comercial"])

# --- 5. CADASTRO E EDIÇÃO ---
if menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    tab_cad, tab_edit = st.tabs(["🆕 Novo", "✏️ Editar"])
    with tab_cad:
        with st.form("cad", clear_on_submit=True):
            n, c, f = st.text_input("Nome:"), st.text_input("CPF:"), st.selectbox("Fornecedor:", [""]+lista_fornecedores)
            if st.form_submit_button("Salvar"):
                conn = sqlite3.connect('dados_mmfrios.db')
                conn.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?,?,?)", (n.upper(), c, f))
                conn.commit()
                st.success("Salvo!")

# --- 6. ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Controle de Fluxo - Corte Fácil")
    conn = sqlite3.connect('dados_mmfrios.db')
    
    # Tabela de quem está na loja AGORA
    df_v = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    em_loja = []
    for nome in df_v['nome'].unique():
        ultimo = df_v[df_v['nome'] == nome].iloc[-1]
        if ultimo['evento'] == 'ENTRADA':
            em_loja.append(ultimo)
    
    if em_loja:
        st.subheader("📍 Promotores em Loja")
        st.table(pd.DataFrame(em_loja)[['nome', 'fornecedor', 'data_hora']])

    st.markdown("---")
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    df_p["display"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
    sel = st.selectbox("Selecione o Promotor:", [""] + df_p["display"].tolist())
    
    if sel:
        n_real = sel.split(" (")[0]
        na_loja = any(d['nome'] == n_real for d in em_loja)
        c1, c2 = st.columns(2)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with c1:
            if st.button("ENTRADA 🟢", disabled=na_loja, use_container_width=True):
                conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "ENTRADA", agora))
                conn.commit()
                st.rerun()
        with c2:
            if na_loja:
                with st.popover("SAÍDA 🔴", use_container_width=True):
                    if st.button("Confirmar Saída"):
                        conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "SAÍDA", agora))
                        conn.commit()
                        st.rerun()
    conn.close()

# --- 7. RELATÓRIOS GERAIS (FILTRO INTERVALO) ---
elif menu == "Relatórios Gerais":
    st.title("🔍 Auditoria de Passagens")
    conn = sqlite3.connect('dados_mmfrios.db')
    df = pd.read_sql_query("SELECT v.data_hora, v.nome, v.evento, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    df['dt_format'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
    
    col1, col2 = st.columns(2)
    with col1:
        p_sel = st.selectbox("Promotor:", ["TODOS"] + sorted((df['nome'] + " (" + df['fornecedor'] + ")").unique().tolist()))
    with col2:
        periodo = st.date_input("Intervalo de Datas:", value=(date.today() - timedelta(days=7), date.today()))

    # Filtro de Intervalo
    if len(periodo) == 2:
        df = df[(df['dt_format'].dt.date >= periodo[0]) & (df['dt_format'].dt.date <= periodo[1])]
    
    if p_sel != "TODOS":
        df = df[(df['nome'] + " (" + df['fornecedor'] + ")") == p_sel]
    
    st.dataframe(df[['data_hora', 'nome', 'fornecedor', 'evento']], use_container_width=True)
    conn.close()

# --- 8. VISÃO COMERCIAL (ESTILO TV) ---
elif menu == "Visão Comercial":
    st_autorefresh(interval=300000, key="tv")
    st.title("📊 Painel Comercial - Corte Fácil")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    df = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    conn.close()

    if not df.empty:
        df['dt'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_7d = df[df['dt'] >= (datetime.now() - timedelta(days=7))]

        # Lógica de agrupamento para KPI e Ranking Semanal
        res = []
        for (n, d), g in df_7d.groupby(['nome', df_7d['dt'].dt.date]):
            ent = g[g['evento'] == 'ENTRADA']['dt'].min()
            sai = g[g['evento'].str.contains('SAÍDA')]['dt'].max()
            minutos = (sai - ent).total_seconds()/60 if pd.notnull(sai) else 0
            res.append({"Forn": g['fornecedor'].iloc[0], "Min": minutos, "Status": "✅" if minutos > 0 else "🟢"})

        df_res = pd.DataFrame(res)
        c1, c2, c3 = st.columns(3)
        c1.metric("Empresas (7 dias)", df_res['Forn'].nunique())
        c2.metric("Total Visitas", len(df_res))
        c3.metric("Tempo Médio", f"{int(df_res[df_res['Min']>0]['Min'].mean() if not df_res.empty else 0)} min")

        st.subheader("🏆 Ranking Semanal de Assiduidade")
        rank = df_res['Forn'].value_counts().reset_index()
        st.dataframe(rank, column_config={"count": st.column_config.ProgressColumn("Visitas", min_value=0, max_value=int(rank['count'].max()))}, use_container_width=True, hide_index=True)

        st.markdown("---")
        # CSV com separador ; para Excel
        csv = df_res.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Exportar para Excel", csv, "comercial.csv", "text/csv")