import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
import os
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURAÇÃO E ESTILO CORTE FÁCIL (BRANCO COM DETALHES COLORIDOS) ---
st.set_page_config(page_title="Sistema MM Frios - Corte Fácil", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    /* Fundo Branco e Clean */
    .stApp { background-color: #FFFFFF; }
    
    /* Botões em Vermelho com texto Branco */
    .stButton>button {
        background-color: #E63946;
        color: white;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #FFB703; /* Amarelo no hover */
        color: #000000;
    }
    
    /* Quadros de Métricas (Branco com borda Amarela) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 2px solid #FFB703;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Títulos em Vermelho */
    h1, h2, h3 { color: #E63946 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Estilo das Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
    }
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
    
    # Lógica de Fechamento Automático (Meia-noite)
    df_v = pd.read_sql_query("SELECT * FROM visitas ORDER BY id ASC", conn)
    if not df_v.empty:
        for nome in df_v['nome'].unique():
            ultimo_registro = df_v[df_v['nome'] == nome].iloc[-1]
            if ultimo_registro['evento'] == 'ENTRADA':
                dt_entrada = datetime.strptime(ultimo_registro['data_hora'], "%d/%m/%Y %H:%M:%S")
                if dt_entrada.date() < datetime.now().date():
                    dt_saida_auto = (dt_entrada + timedelta(hours=1)).strftime("%d/%m/%Y %H:%M:%S")
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", 
                              (nome, "SAÍDA (AUTO)", dt_saida_auto))
    conn.commit()
    conn.close()

gerenciar_banco()

# --- 3. RECURSOS LATERAIS ---
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
    tab1, tab2 = st.tabs(["🆕 Novo Cadastro", "✏️ Editar Cadastro"])
    with tab1:
        with st.form("cad"):
            n = st.text_input("Nome Completo:")
            c = st.text_input("CPF (apenas números):", max_chars=11)
            f = st.selectbox("Fornecedor:", [""] + lista_fornecedores)
            if st.form_submit_button("Salvar Registro"):
                if n and len(c)==11 and f:
                    conn = sqlite3.connect('dados_mmfrios.db')
                    conn.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?,?,?)", (n.upper(), c, f))
                    conn.commit()
                    st.success("✅ Promotor cadastrado!")
                else: st.error("⚠️ Preencha todos os campos corretamente.")

# --- 6. ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Controle de Fluxo")
    conn = sqlite3.connect('dados_mmfrios.db')
    
    # Status Atual
    df_v = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    em_loja = []
    for nome in df_v['nome'].unique():
        ult = df_v[df_v['nome'] == nome].iloc[-1]
        if ult['evento'] == 'ENTRADA': em_loja.append(ult)
    
    if em_loja:
        st.subheader("📍 Ativos no Momento")
        st.dataframe(pd.DataFrame(em_loja)[['nome', 'fornecedor', 'data_hora']], use_container_width=True, hide_index=True)

    st.markdown("---")
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    df_p["disp"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
    sel = st.selectbox("Selecione para bater o ponto:", [""] + df_p["disp"].tolist())
    
    if sel:
        n_real = sel.split(" (")[0]
        check_loja = any(d['nome'] == n_real for d in em_loja)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("REGISTRAR ENTRADA 🟢", disabled=check_loja, use_container_width=True):
                conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "ENTRADA", agora))
                conn.commit()
                st.rerun()
        with c2:
            if check_loja:
                with st.popover("REGISTRAR SAÍDA 🔴", use_container_width=True):
                    st.write(f"Confirmar saída de {n_real}?")
                    if st.button("Confirmar", type="primary"):
                        conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "SAÍDA", agora))
                        conn.commit()
                        st.rerun()
    conn.close()

# --- 7. RELATÓRIOS GERAIS (AUDITORIA COM INTERVALO) ---
elif menu == "Relatórios Gerais":
    st.title("🔍 Auditoria e Histórico")
    conn = sqlite3.connect('dados_mmfrios.db')
    df = pd.read_sql_query("SELECT v.data_hora, v.nome, v.evento, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id DESC", conn)
    df['dt_p'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
    
    c1, c2 = st.columns(2)
    with c1:
        p_filtro = st.selectbox("Promotor:", ["TODOS"] + sorted((df['nome'] + " (" + df['fornecedor'] + ")").unique().tolist()))
    with c2:
        periodo = st.date_input("Período (Início e Fim):", value=(date.today() - timedelta(days=7), date.today()))

    if len(periodo) == 2:
        df = df[(df['dt_p'].dt.date >= periodo[0]) & (df['dt_p'].dt.date <= periodo[1])]
    if p_filtro != "TODOS":
        df = df[(df['nome'] + " (" + df['fornecedor'] + ")") == p_filtro]
    
    st.dataframe(df[['data_hora', 'nome', 'fornecedor', 'evento']], use_container_width=True, hide_index=True)
    conn.close()

# --- 8. VISÃO COMERCIAL (RANKING + RELATÓRIO COMPLETO) ---
elif menu == "Visão Comercial":
    st_autorefresh(interval=300000, key="comercial_auto")
    st.title("📊 Gestão de Performance Comercial")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    df_raw = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    conn.close()

    if not df_raw.empty:
        df_raw['dt'] = pd.to_datetime(df_raw['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_7d = df_raw[df_raw['dt'] >= (datetime.now() - timedelta(days=7))].copy()

        # Processamento de Visitas
        final_data = []
        for (nome, dia), gp in df_7d.groupby(['nome', df_7d['dt'].dt.date]):
            ent = gp[gp['evento'] == 'ENTRADA']['dt'].min()
            sai = gp[gp['evento'].str.contains('SAÍDA')]['dt'].max()
            forn = gp['fornecedor'].iloc[0]
            
            minutos = (sai - ent).total_seconds()/60 if pd.notnull(sai) else 0
            tempo_fmt = f"{int(minutos//60)}h {int(minutos%60)}min" if minutos > 0 else "Em Loja..."
            
            final_data.append({
                "Data": dia.strftime("%d/%m/%Y"),
                "Fornecedor": forn,
                "Promotor": nome,
                "Permanência": tempo_fmt,
                "Status": "✅ Concluída" if minutos > 0 else "🟢 Ativo",
                "min": minutos
            })

        df_final = pd.DataFrame(final_data)

        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Empresas na Semana", df_final['Fornecedor'].nunique())
        c2.metric("Total de Visitas", len(df_final))
        media = int(df_final[df_final['min']>0]['min'].mean() if not df_final[df_final['min']>0].empty else 0)
        c3.metric("Média Permanência", f"{media} min")

        st.markdown("---")
        
        # Ranking de Assiduidade
        st.subheader("🏆 Ranking Semanal de Assiduidade")
        rank = df_final['Fornecedor'].value_counts().reset_index()
        rank.columns = ['Fornecedor', 'Visitas']
        st.dataframe(rank, column_config={"Visitas": st.column_config.ProgressColumn("Volume", format="%d", min_value=0, max_value=int(rank['Visitas'].max()))}, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        # Relatório Detalhado
        st.subheader("📋 Relatório Detalhado das Atividades")
        st.dataframe(df_final.drop(columns=['min']).sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)
        
        # Botão de Exportação
        csv = df_final.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório Completo (Excel)", csv, f"relatorio_comercial_{date.today()}.csv", "text/csv", use_container_width=True)
    else:
        st.info("Nenhuma visita registrada na última semana.")