import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="❄️")

# --- 2. BANCO DE DADOS (Estrutura Robusta) ---
def criar_tabelas():
    conn = sqlite3.connect('dados_mmfrios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS promotores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT, fornecedor TEXT)''')
    try:
        c.execute("ALTER TABLE promotores ADD COLUMN fornecedor TEXT")
    except:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS visitas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, evento TEXT, data_hora TEXT)''')
    conn.commit()
    conn.close()

criar_tabelas()

# --- 3. RECURSOS EXTERNOS (Logo e Excel) ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)

try:
    df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
    lista_fornecedores = df_f['Fornecedor'].dropna().astype(str)
    lista_fornecedores = lista_fornecedores[~lista_fornecedores.str.contains('#NOME?')].unique().tolist()
    lista_fornecedores = sorted(lista_fornecedores)
except:
    lista_fornecedores = []
    st.sidebar.warning("Arquivo 'BASE_FORNECEDORES.xlsx' não encontrado.")

# --- 4. NAVEGAÇÃO LATERAL ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação Principal:", ["Cadastro/Edição", "Entrada e Saída", "Relatórios Gerais", "Visão Comercial"])

# --- 5. TELA: CADASTRO E EDIÇÃO ---
if menu == "Cadastro/Edição":
    st.title("👤 Gestão de Promotores")
    tab_cad, tab_edit = st.tabs(["🆕 Novo Cadastro", "✏️ Editar Cadastro"])
    
    with tab_cad:
        with st.form("form_cadastro", clear_on_submit=True):
            nome = st.text_input("Nome Completo:")
            cpf = st.text_input("CPF (11 números):", max_chars=11)
            forn = st.selectbox("Fornecedor Representado:", [""] + lista_fornecedores)
            if st.form_submit_button("Finalizar Cadastro"):
                if nome and len(cpf) == 11 and forn:
                    conn = sqlite3.connect('dados_mmfrios.db')
                    check = pd.read_sql_query(f"SELECT cpf FROM promotores WHERE cpf = '{cpf}'", conn)
                    if not check.empty:
                        st.error(f"❌ CPF {cpf} já está cadastrado!")
                    else:
                        c = conn.cursor()
                        c.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?, ?, ?)", 
                                  (nome.upper().strip(), cpf, forn))
                        conn.commit()
                        st.success(f"✅ {nome.upper()} cadastrado com sucesso!")
                    conn.close()
                else:
                    st.warning("Preencha todos os campos corretamente.")

    with tab_edit:
        conn = sqlite3.connect('dados_mmfrios.db')
        df_edit = pd.read_sql_query("SELECT * FROM promotores", conn)
        if not df_edit.empty:
            p_lista = df_edit['nome'].tolist()
            p_sel = st.selectbox("Selecione para editar:", p_lista)
            dados_p = df_edit[df_edit['nome'] == p_sel].iloc[0]
            
            with st.form("form_edicao"):
                novo_n = st.text_input("Nome:", value=dados_p['nome'])
                novo_c = st.text_input("CPF:", value=dados_p['cpf'], max_chars=11)
                idx = lista_fornecedores.index(dados_p['fornecedor']) if dados_p['fornecedor'] in lista_fornecedores else 0
                novo_f = st.selectbox("Fornecedor:", lista_fornecedores, index=idx)
                if st.form_submit_button("Atualizar Dados"):
                    c = conn.cursor()
                    c.execute("UPDATE promotores SET nome=?, cpf=?, fornecedor=? WHERE id=?", (novo_n.upper(), novo_c, novo_f, dados_p['id']))
                    conn.commit()
                    st.success("Dados atualizados!")
                    st.rerun()
        conn.close()

# --- 6. TELA: ENTRADA E SAÍDA (Lógica de Persistência) ---
elif menu == "Entrada e Saída":
    st.title("🕒 Controle de Acesso em Tempo Real")
    conn = sqlite3.connect('dados_mmfrios.db')
    
    # Lista de quem está na loja agora (último evento = ENTRADA)
    q_status = "SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome WHERE v.id IN (SELECT MAX(id) FROM visitas GROUP BY nome)"
    df_status = pd.read_sql_query(q_status, conn)
    em_loja = df_status[df_status['evento'] == 'ENTRADA']

    st.subheader("📍 Promotores Ativos na Loja")
    if not em_loja.empty:
        for _, row in em_loja.iterrows():
            st.info(f"🟢 **{row['nome']}** ({row['fornecedor']}) - Entrou em: {row['data_hora']}")
    else:
        st.write("Não há promotores com visita aberta.")

    st.markdown("---")
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    if not df_p.empty:
        df_p["display"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
        selecionado = st.selectbox("Selecione o Promotor:", [""] + df_p["display"].tolist())
        if selecionado:
            nome_real = selecionado.split(" (")[0]
            ta_na_loja = nome_real in em_loja['nome'].values
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("REGISTRAR ENTRADA 🟢", use_container_width=True, disabled=ta_na_loja):
                    conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "ENTRADA", agora))
                    conn.commit()
                    st.rerun()
            with c2:
                if st.button("REGISTRAR SAÍDA 🔴", use_container_width=True, disabled=not ta_na_loja):
                    conn.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "SAÍDA", agora))
                    conn.commit()
                    st.rerun()
    conn.close()

# --- 7. TELA: RELATÓRIOS GERAIS ---
elif menu == "Relatórios Gerais":
    st.title("📊 Histórico de Registros")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_v = pd.read_sql_query("SELECT * FROM visitas ORDER BY id DESC", conn)
    st.dataframe(df_v, use_container_width=True)
    conn.close()

# --- 8. TELA: VISÃO COMERCIAL (O DIFERENCIAL) ---
elif menu == "Visão Comercial":
    st.title("📊 Dashboard Comercial - Performance de Fornecedores")
    
    conn = sqlite3.connect('dados_mmfrios.db')
    query = "SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome ORDER BY v.id ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['data_hora'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
        hoje = datetime.now()
        df_semana = df[df['data_hora'] >= (hoje - timedelta(days=7))].copy()

        # Processamento de permanência
        resultados = []
        for nome, grupo in df_semana.groupby(['nome', df_semana['data_hora'].dt.date]):
            entrada = grupo[grupo['evento'] == 'ENTRADA']['data_hora'].min()
            saida = grupo[grupo['evento'] == 'SAÍDA']['data_hora'].max()
            forn_at = grupo['fornecedor'].iloc[0]
            
            minutos = 0
            status = "🔴 Pendente Saída"
            perm = "---"
            
            if pd.notnull(entrada) and pd.notnull(saida) and saida > entrada:
                diff = saida - entrada
                minutos = diff.total_seconds() / 60
                status = "✅ Concluída"
                h, r = divmod(diff.total_seconds(), 3600)
                m, _ = divmod(r, 60)
                perm = f"{int(h)}h {int(m)}min"
            elif pd.notnull(entrada):
                status = "🟢 Em Loja"

            resultados.append({
                "Data": nome[1].strftime("%d/%m/%Y"),
                "Fornecedor": forn_at,
                "Promotor": nome[0],
                "Permanência": perm,
                "Status": status,
                "minutos": minutos
            })

        df_res = pd.DataFrame(resultados)

        # --- KPI CARDS ---
        st.markdown("### Indicadores da Semana")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Empresas Ativas", df_res['Fornecedor'].nunique())
        k2.metric("Total Visitas", len(df_res))
        media_min = df_res[df_res['minutos'] > 0]['minutos'].mean()
        k3.metric("Tempo Médio", f"{int(media_min if not pd.isna(media_min) else 0)} min")
        k4.metric("Em Loja Agora", len(df_res[df_res['Status'] == "🟢 Em Loja"]))

        st.markdown("---")
        
        # --- RANKING E DETALHAMENTO ---
        col_rank, col_table = st.columns([1, 2])
        
        with col_rank:
            st.subheader("🏆 Ranking Presença")
            ranking = df_res['Fornecedor'].value_counts().reset_index()
            ranking.columns = ['Fornecedor', 'Visitas']
            st.dataframe(ranking, hide_index=True)

        with col_table:
            st.subheader("📋 Detalhes (Últimos 7 dias)")
            f_forn = st.multiselect("Filtrar Empresa:", sorted(df_res['Fornecedor'].unique()))
            df_disp = df_res.copy()
            if f_forn:
                df_disp = df_disp[df_disp['Fornecedor'].isin(f_forn)]
            
            st.dataframe(df_disp.drop(columns=['minutos']).sort_values(by="Data", ascending=False), use_container_width=True)

        # --- EXPORTAÇÃO ---
        st.markdown("---")
        csv = df_disp.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório Comercial (Excel/CSV)", csv, "relatorio_comercial.csv", "text/csv")
    else:
        st.info("Sem dados de visitas na última semana.")