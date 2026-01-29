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

# --- 2. BANCO DE DADOS E AUTO-ENCERRAMENTO ---
def gerenciar_banco():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, fornecedor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    
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
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação:", ["Cadastro/Edição", "Entrada e Saída", "Relatórios Gerais", "Visão Comercial"])

# Rodapé na Coluna Fixa (3)
st.sidebar.markdown("---")
st.sidebar.caption("Desenvolvido por: Paulo Henrique - Setor Fiscal")

# --- 5. CADASTRO E EDIÇÃO ---
if menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    tab1, tab2 = st.tabs(["🆕 Novo Cadastro", "✏️ Editar Cadastro"])
    
    with tab1:
        with st.form("cad"):
            n = st.text_input("Nome Completo:")
            c = st.text_input("CPF:", max_chars=11)
            f = st.selectbox("Fornecedor:", [""] + lista_fornecedores)
            if st.form_submit_button("Salvar"):
                if n and len(c)==11:
                    conn = sqlite3.connect('dados_mmfrios.db')
                    conn.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?,?,?)", (n.upper().strip(), c, f))
                    conn.commit()
                    st.success("✅ Cadastrado!")
                else: st.error("⚠️ Verifique os dados.")

    with tab2:
        st.subheader("🔒 Área de Edição")
        senha = st.text_input("Senha de Administrador:", type="password")
        if senha == "admin123":
            conn = sqlite3.connect('dados_mmfrios.db')
            df_edit = pd.read_sql_query("SELECT * FROM promotores", conn)
            if not df_edit.empty:
                p_sel = st.selectbox("Selecionar Promotor:", df_edit['nome'].tolist())
                dados = df_edit[df_edit['nome'] == p_sel].iloc[0]
                with st.form("edit"):
                    en = st.text_input("Nome:", value=dados['nome'])
                    ec = st.text_input("CPF:", value=dados['cpf'])
                    idx = lista_fornecedores.index(dados['fornecedor']) if dados['fornecedor'] in lista_fornecedores else 0
                    ef = st.selectbox("Fornecedor:", lista_fornecedores, index=idx)
                    if st.form_submit_button("Atualizar Dados"):
                        conn.execute("UPDATE promotores SET nome=?, cpf=?, fornecedor=? WHERE id=?", (en.upper(), ec, ef, dados['id']))
                        conn.commit()
                        st.success("✅ Atualizado!")
                        st.rerun()
            conn.close()

# --- 6. ENTRADA E SAÍDA (1 e 4) ---
elif menu == "Entrada e Saída":
    st.title("🕒 Controle de Fluxo")
    conn = sqlite3.connect('dados_mmfrios.db')
    
    # 1. VISUALIZAÇÃO DE QUEM ESTÁ EM LOJA (Para troca de turno)
    df_v = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    em_loja = []
    if not df_v.empty:
        for nome in df_v['nome'].unique():
            ult = df_v[df_v['nome'] == nome].iloc[-1]
            if ult['evento'] == 'ENTRADA': em_loja.append(ult)
    
    st.subheader("📍 Promotores em Loja (Ativos)")
    if em_loja:
        df_presentes = pd.DataFrame(em_loja)[['nome', 'fornecedor', 'data_hora']]
        df_presentes.columns = ['Nome', 'Fornecedor', 'Hora de Entrada']
        st.dataframe(df_presentes, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum promotor em loja no momento.")

    st.markdown("---")

    # Registro de entrada/saída
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    df_p["disp"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
    
    # Selectbox com reset automático (4)
    sel = st.selectbox("Identifique o Promotor para Registro:", [""] + df_p["disp"].tolist(), key="reg_ponto")
    
    if sel:
        n_real = sel.split(" (")[0]
        check_loja = any(d['nome'] == n_real for d in em_loja)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("REGISTRAR ENTRADA 🟢", disabled=check_loja, use_container_width=True):
                conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "ENTRADA", agora))
                conn.commit()
                st.success(f"Entrada de {n_real} confirmada!")
                st.rerun()
        with c2:
            if check_loja:
                # 4. Saída volta para o estado inicial
                with st.popover("REGISTRAR SAÍDA 🔴", use_container_width=True):
                    st.write(f"Deseja finalizar a visita de {n_real}?")
                    if st.button("Sim, confirmar saída"):
                        conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?,?,?)", (n_real, "SAÍDA", agora))
                        conn.commit()
                        st.rerun() # Isso limpa a seleção e volta ao início
    conn.close()

# --- 7. RELATÓRIOS ---
elif menu == "Relatórios Gerais":
    st.title("🔍 Auditoria de Passagens")
    conn = sqlite3.connect('dados_mmfrios.db')
    df = pd.read_sql_query("SELECT v.data_hora, v.nome, v.evento, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id DESC", conn)
    p_filtro = st.selectbox("Promotor:", ["TODOS"] + sorted((df['nome'] + " (" + df['fornecedor'] + ")").unique().tolist()))
    periodo = st.date_input("Período:", value=(date.today() - timedelta(days=7), date.today()))
    
    df['dt_p'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
    if len(periodo) == 2:
        df = df[(df['dt_p'].dt.date >= periodo[0]) & (df['dt_p'].dt.date <= periodo[1])]
    if p_filtro != "TODOS":
        df = df[(df['nome'] + " (" + df['fornecedor'] + ")") == p_filtro]
    st.dataframe(df[['data_hora', 'nome', 'fornecedor', 'evento']], use_container_width=True, hide_index=True)
    conn.close()

# --- 8. VISÃO COMERCIAL (2) ---
elif menu == "Visão Comercial":
    st_autorefresh(interval=300000, key="auto")
    st.title("📊 Painel de Performance de Fornecedores")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    df_raw = pd.read_sql_query("SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome", conn)
    conn.close()

    if not df_raw.empty:
        df_raw['dt'] = pd.to_datetime(df_raw['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_7d = df_raw[df_raw['dt'] >= (datetime.now() - timedelta(days=7))].copy()

        f_data = []
        for (nome, dia), gp in df_7d.groupby(['nome', df_7d['dt'].dt.date]):
            ent = gp[gp['evento'] == 'ENTRADA']['dt'].min()
            sai = gp[gp['evento'].str.contains('SAÍDA')]['dt'].max()
            minutos = (sai - ent).total_seconds()/60 if pd.notnull(sai) else 0
            f_data.append({
                "Data": dia.strftime("%d/%m/%Y"), "Fornecedor": gp['fornecedor'].iloc[0],
                "Promotor": nome, "Permanência": f"{int(minutos//60)}h {int(minutos%60)}min" if minutos > 0 else "Em Loja",
                "Status": "✅ Concluída" if minutos > 0 else "🟢 Ativo", "min": minutos
            })

        df_final = pd.DataFrame(f_data)
        c1, c2, c3 = st.columns(3)
        c1.metric("Empresas/Semana", df_final['Fornecedor'].nunique())
        c2.metric("Total Visitas", len(df_final))
        media = int(df_final[df_final['min']>0]['min'].mean() if not df_final[df_final['min']>0].empty else 0)
        c3.metric("Média Permanência", f"{media} min")

        st.subheader("🏆 Ranking de Assiduidade (Visitas Totais)")
        rank = df_final['Fornecedor'].value_counts().reset_index()
        rank.columns = ['Fornecedor', 'Visitas']
        
        # 2. Ranking mostrando números reais (format="%d")
        st.dataframe(
            rank, 
            column_config={
                "Visitas": st.column_config.ProgressColumn(
                    "Quantidade de Visitas",
                    format="%d",
                    min_value=0,
                    max_value=int(rank['Visitas'].max())
                )
            }, 
            use_container_width=True, 
            hide_index=True
        )

        st.subheader("📋 Relatório Detalhado")
        st.dataframe(df_final.drop(columns=['min']).sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)
        
        csv = df_final.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório (Excel/CSV)", csv, "performance.csv", "text/csv", use_container_width=True)