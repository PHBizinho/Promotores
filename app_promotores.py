import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

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

# --- 3. RECURSOS EXTERNOS ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)

try:
    df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
    df_f['Display'] = df_f['Código'].astype(str) + " - " + df_f['Fornecedor'].astype(str)
    lista_fornecedores = df_f['Display'].dropna().unique().tolist()
    lista_fornecedores = sorted([f for f in lista_fornecedores if "#NOME?" not in f])
except:
    lista_fornecedores = []

# --- 4. NAVEGAÇÃO ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação:", ["Cadastro/Edição", "Entrada e Saída", "Relatórios Gerais", "Visão Comercial"])

# --- 5. CADASTRO E EDIÇÃO ---
if menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    tab_cad, tab_edit = st.tabs(["🆕 Novo Cadastro", "✏️ Editar Cadastro"])
    
    with tab_cad:
        with st.form("form_cadastro", clear_on_submit=True):
            nome = st.text_input("Nome Completo:")
            cpf = st.text_input("CPF (11 números):", max_chars=11)
            forn = st.selectbox("Fornecedor (Código - Nome):", [""] + lista_fornecedores)
            if st.form_submit_button("Finalizar Cadastro"):
                if nome and len(cpf) == 11 and forn:
                    conn = sqlite3.connect('dados_mmfrios.db')
                    check = pd.read_sql_query(f"SELECT cpf FROM promotores WHERE cpf = '{cpf}'", conn)
                    if not check.empty:
                        st.error(f"❌ CPF {cpf} já cadastrado!")
                    else:
                        c = conn.cursor()
                        c.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?, ?, ?)", 
                                  (nome.upper().strip(), cpf, forn))
                        conn.commit()
                        st.success(f"✅ {nome.upper()} cadastrado!")
                    conn.close()

    with tab_edit:
        senha = st.text_input("Senha para editar:", type="password")
        if senha == "admin123":
            conn = sqlite3.connect('dados_mmfrios.db')
            df_edit = pd.read_sql_query("SELECT * FROM promotores", conn)
            if not df_edit.empty:
                p_sel = st.selectbox("Selecionar Promotor:", df_edit['nome'].tolist())
                dados_p = df_edit[df_edit['nome'] == p_sel].iloc[0]
                with st.form("form_edicao"):
                    n_nome = st.text_input("Nome:", value=dados_p['nome'])
                    n_cpf = st.text_input("CPF:", value=dados_p['cpf'])
                    idx = lista_fornecedores.index(dados_p['fornecedor']) if dados_p['fornecedor'] in lista_fornecedores else 0
                    n_forn = st.selectbox("Fornecedor:", lista_fornecedores, index=idx)
                    if st.form_submit_button("Atualizar"):
                        c = conn.cursor()
                        c.execute("UPDATE promotores SET nome=?, cpf=?, fornecedor=? WHERE id=?", (n_nome.upper(), n_cpf, n_forn, dados_p['id']))
                        conn.commit()
                        st.success("Atualizado!")
                        st.rerun()
            conn.close()

# --- 6. ENTRADA E SAÍDA (COM CONFIRMAÇÃO) ---
elif menu == "Entrada e Saída":
    st.title("🕒 Controle de Fluxo")
    conn = sqlite3.connect('dados_mmfrios.db')
    
    # Status "Em Loja"
    q_status = "SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome WHERE v.id IN (SELECT MAX(id) FROM visitas GROUP BY nome)"
    df_status = pd.read_sql_query(q_status, conn)
    em_loja = df_status[df_status['evento'] == 'ENTRADA']

    if not em_loja.empty:
        st.info(f"📍 Atualmente {len(em_loja)} promotor(es) em loja.")
    
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    if not df_p.empty:
        df_p["display"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
        sel = st.selectbox("Identifique o Promotor:", [""] + df_p["display"].tolist())
        
        if sel:
            nome_real = sel.split(" (")[0]
            ta_na_loja = nome_real in em_loja['nome'].values
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("REGISTRAR ENTRADA 🟢", use_container_width=True, disabled=ta_na_loja):
                    conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "ENTRADA", agora))
                    conn.commit()
                    st.success("Entrada Registrada!")
                    st.rerun()
            
            with c2:
                # --- Lógica de Confirmação para Saída ---
                if ta_na_loja:
                    with st.popover("REGISTRAR SAÍDA 🔴", use_container_width=True):
                        st.warning(f"Confirmar saída para {nome_real}?")
                        if st.button("Sim, confirmar saída", type="primary"):
                            conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "SAÍDA", agora))
                            conn.commit()
                            st.rerun()
                else:
                    st.button("REGISTRAR SAÍDA 🔴", use_container_width=True, disabled=True)
    conn.close()

# --- 7. RELATÓRIOS GERAIS (AUDITORIA E BUSCA) ---
elif menu == "Relatórios Gerais":
    st.title("🔍 Auditoria de Passagens")
    st.write("Utilize esta aba para consultar o histórico individual ou por data.")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    df_v = pd.read_sql_query("SELECT v.data_hora, v.nome, v.evento, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id DESC", conn)
    conn.close()

    col1, col2 = st.columns(2)
    with col1:
        filtro_nome = st.selectbox("Filtrar por Promotor:", ["TODOS"] + sorted(df_v['nome'].unique().tolist()))
    with col2:
        filtro_data = st.text_input("Filtrar por Data (Ex: 29/01/2026):")

    df_filtered = df_v.copy()
    if filtro_nome != "TODOS":
        df_filtered = df_filtered[df_filtered['nome'] == filtro_nome]
    if filtro_data:
        df_filtered = df_filtered[df_filtered['data_hora'].str.contains(filtro_data)]

    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

# --- 8. VISÃO COMERCIAL (DASHBOARD TV) ---
elif menu == "Visão Comercial":
    st_autorefresh(interval=300000, key="comercial_refresh")
    st.title("📊 Painel de Performance (TV)")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    query = "SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['data_hora'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df_semana = df[df['data_hora'] >= (datetime.now() - timedelta(days=7))].copy()

        resultados = []
        for nome, grupo in df_semana.groupby(['nome', df_semana['data_hora'].dt.date]):
            ent = grupo[grupo['evento'] == 'ENTRADA']['data_hora'].min()
            sai = grupo[grupo['evento'] == 'SAÍDA']['data_hora'].max()
            status = "🔴 Pendente"
            perm = "---"
            minutos = 0
            if pd.notnull(ent) and pd.notnull(sai) and sai > ent:
                diff = sai - ent
                minutos = diff.total_seconds() / 60
                status = "✅ Concluída"
                h, r = divmod(diff.total_seconds(), 3600)
                m, _ = divmod(r, 60)
                perm = f"{int(h)}h {int(m)}min"
            elif pd.notnull(ent): status = "🟢 Em Loja"

            resultados.append({
                "Data": nome[1].strftime("%d/%m/%Y"),
                "Fornecedor": grupo['fornecedor'].iloc[0],
                "Promotor": nome[0], "Permanência": perm, "Status": status, "minutos": minutos
            })

        df_res = pd.DataFrame(resultados)
        
        # KPIs e Ranking
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Empresas", df_res['Fornecedor'].nunique())
        k2.metric("Visitas", len(df_res))
        media = int(df_res[df_res['minutos'] > 0]['minutos'].mean() if not df_res[df_res['minutos'] > 0].empty else 0)
        k3.metric("Média Tempo", f"{media} min")
        k4.metric("Em Loja", len(df_res[df_res['Status'] == "🟢 Em Loja"]))

        st.subheader("🏆 Ranking de Assiduidade")
        ranking = df_res['Fornecedor'].value_counts().reset_index()
        ranking.columns = ['Fornecedor', 'Visitas']
        st.dataframe(ranking, column_config={"Visitas": st.column_config.ProgressColumn("Frequência", format="%d", min_value=0, max_value=int(ranking['Visitas'].max()))}, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        # Exportação corrigida (UTF-8-SIG e Ponto-e-vírgula)
        csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório Excel", csv, "relatorio_mmfrios.csv", "text/csv", use_container_width=True)
        st.dataframe(df_res.drop(columns=['minutos']).sort_values(by="Data", ascending=False), use_container_width=True)