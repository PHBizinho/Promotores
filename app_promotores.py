import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
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

# --- 3. RECURSOS EXTERNOS ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", use_container_width=True)

try:
    df_f = pd.read_excel("BASE_FORNECEDORES.xlsx")
    lista_fornecedores = df_f['Fornecedor'].dropna().astype(str)
    lista_fornecedores = lista_fornecedores[~lista_fornecedores.str.contains('#NOME?')].unique().tolist()
    lista_fornecedores = sorted(lista_fornecedores)
except:
    lista_fornecedores = []

# --- 4. NAVEGAÇÃO ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação:", ["Cadastro/Edição", "Entrada e Saída", "Relatórios", "Visão Comercial"])

# --- 5. CADASTRO E EDIÇÃO ---
if menu == "Cadastro/Edição":
    tab_cad, tab_edit = st.tabs(["🆕 Novo Cadastro", "✏️ Editar Promotor"])
    
    with tab_cad:
        with st.form("form_cadastro", clear_on_submit=True):
            nome = st.text_input("Nome Completo:")
            cpf = st.text_input("CPF (11 números):", max_chars=11)
            forn = st.selectbox("Fornecedor:", [""] + lista_fornecedores)
            if st.form_submit_button("Salvar Registro"):
                if nome and len(cpf) == 11 and forn:
                    conn = sqlite3.connect('dados_mmfrios.db')
                    # Validação de CPF Duplicado
                    check = pd.read_sql_query(f"SELECT cpf FROM promotores WHERE cpf = '{cpf}'", conn)
                    if not check.empty:
                        st.error(f"❌ Erro: O CPF {cpf} já está cadastrado no sistema!")
                    else:
                        c = conn.cursor()
                        c.execute("INSERT INTO promotores (nome, cpf, fornecedor) VALUES (?, ?, ?)", 
                                  (nome.upper().strip(), cpf, forn))
                        conn.commit()
                        st.success(f"✅ {nome.upper()} cadastrado com sucesso.")
                    conn.close()
                else:
                    st.warning("Preencha todos os campos corretamente.")

    with tab_edit:
        conn = sqlite3.connect('dados_mmfrios.db')
        df_edit = pd.read_sql_query("SELECT * FROM promotores", conn)
        if not df_edit.empty:
            promotor_edit = st.selectbox("Selecione quem deseja editar:", df_edit['nome'].tolist())
            dados_p = df_edit[df_edit['nome'] == promotor_edit].iloc[0]
            
            with st.form("form_edicao"):
                novo_nome = st.text_input("Nome:", value=dados_p['nome'])
                novo_cpf = st.text_input("CPF:", value=dados_p['cpf'], max_chars=11)
                novo_forn = st.selectbox("Fornecedor:", lista_fornecedores, index=lista_fornecedores.index(dados_p['fornecedor']) if dados_p['fornecedor'] in lista_fornecedores else 0)
                
                if st.form_submit_button("Atualizar Dados"):
                    c = conn.cursor()
                    c.execute("UPDATE promotores SET nome=?, cpf=?, fornecedor=? WHERE id=?", 
                              (novo_nome.upper(), novo_cpf, novo_forn, dados_p['id']))
                    conn.commit()
                    st.success("✅ Cadastro atualizado!")
                    st.rerun()
        conn.close()

# --- 6. ENTRADA E SAÍDA ---
elif menu == "Entrada e Saída":
    st.title("🕒 Registro de Fluxo")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_p = pd.read_sql_query("SELECT nome, fornecedor FROM promotores", conn)
    if not df_p.empty:
        df_p["display"] = df_p["nome"] + " (" + df_p["fornecedor"] + ")"
        selecionado = st.selectbox("Identifique o Promotor:", [""] + df_p["display"].tolist())
        if selecionado:
            nome_real = selecionado.split(" (")[0]
            col1, col2 = st.columns(2)
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            with col1:
                if st.button("ENTRADA 🟢", use_container_width=True):
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "ENTRADA", agora))
                    conn.commit()
                    st.success(f"Entrada registrada: {agora}")
            with col2:
                if st.button("SAÍDA 🔴", use_container_width=True):
                    c = conn.cursor()
                    c.execute("INSERT INTO visitas (nome, evento, data_hora) VALUES (?, ?, ?)", (nome_real, "SAÍDA", agora))
                    conn.commit()
                    st.warning(f"Saída registrada: {agora}")
    conn.close()

# --- 7. RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Histórico Geral")
    conn = sqlite3.connect('dados_mmfrios.db')
    df_v = pd.read_sql_query("SELECT * FROM visitas ORDER BY id DESC", conn)
    st.dataframe(df_v, use_container_width=True)
    conn.close()

# --- 8. VISÃO COMERCIAL (COM CÁLCULO DE TEMPO) ---
elif menu == "Visão Comercial":
    st.title("📊 Gestão de Permanência em Loja")
    conn = sqlite3.connect('dados_mmfrios.db')
    query = "SELECT v.nome, v.evento, v.data_hora, p.fornecedor FROM visitas v JOIN promotores p ON v.nome = p.nome"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['data_hora'] = pd.to_datetime(df['data_hora'], format="%d/%m/%Y %H:%M:%S")
        df['data_apenas'] = df['data_hora'].dt.date
        df_semana = df[df['data_hora'] >= (datetime.now() - timedelta(days=7))].copy()

        if not df_semana.empty:
            # Lógica para calcular o tempo de permanência
            resultados = []
            for (nome, data), group in df_semana.groupby(['nome', 'data_apenas']):
                entrada = group[group['evento'] == 'ENTRADA']['data_hora'].min()
                saida = group[group['evento'] == 'SAÍDA']['data_hora'].max()
                fornecedor = group['fornecedor'].iloc[0]
                
                tempo_loja = "Em loja..."
                if pd.notnull(entrada) and pd.notnull(saida) and saida > entrada:
                    diff = saida - entrada
                    horas, rem = divmod(diff.seconds, 3600)
                    minutos, _ = divmod(rem, 60)
                    tempo_loja = f"{horas}h {minutos}min"
                
                resultados.append({
                    "Fornecedor": fornecedor,
                    "Promotor": nome,
                    "Data": data.strftime("%d/%m/%Y"),
                    "Tempo em Loja": tempo_loja
                })
            
            df_final = pd.DataFrame(resultados).sort_values(by="Data", ascending=False)
            st.table(df_final) # Tabela em destaque
        else:
            st.info("Nenhuma visita nos últimos 7 dias.")