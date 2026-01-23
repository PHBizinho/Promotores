import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Sistema MM Frios", layout="wide", page_icon="🏢")

# --- CONEXÃO COM GOOGLE SHEETS ---
# O Streamlit buscará as credenciais automaticamente nos 'Secrets' que você salvou
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÃO DE BUSCA DE FORNECEDORES (EXCEL LOCAL) ---
def buscar_fornecedores():
    try:
        # Carrega a base do Excel que está no seu GitHub
        df = pd.read_excel("BASE_FORNECEDORES.xlsx", skiprows=1)
        df.columns = ['Código', 'Fornecedor', 'CNPJ_CPF', 'Fantasia']
        df = df.dropna(subset=['Fornecedor', 'Código'])
        # Garante que os códigos sejam strings para evitar erros de busca
        df['Código'] = df['Código'].astype(int).astype(str)
        # Cria a coluna de busca para o Selectbox
        df['Busca'] = df['Código'] + " - " + df['Fornecedor']
        return df.sort_values('Fornecedor')
    except Exception as e:
        st.error(f"Erro ao carregar Excel de fornecedores: {e}")
        return pd.DataFrame()

# --- SIDEBAR (MENU) ---
if os.path.exists("LOGO_CORTE-FACIL2.png"):
    st.sidebar.image("LOGO_CORTE-FACIL2.png", width=150)
menu = st.sidebar.radio("Navegação", ["Check-in/Out", "Cadastro de Promotor", "Relatórios"])

df_forn = buscar_fornecedores()

# --- TELA 1: CHECK-IN / CHECK-OUT ---
if menu == "Check-in/Out":
    st.title("📲 Registro de Visita")
    
    # Busca cadastros existentes na aba CADASTROS
    # ttl=0 garante que ele não use memória antiga e pegue o dado real da planilha
    df_cadastros = conn.read(worksheet="CADASTROS", ttl=0)
    
    with st.container(border=True):
        cpf_visita = st.text_input("Digite seu CPF para identificar:", max_chars=11)
        
        if cpf_visita:
            # Verifica se CPF está cadastrado
            promotor = df_cadastros[df_cadastros['CPF'].astype(str) == str(cpf_visita)]
            
            if not promotor.empty:
                nome_logado = promotor.iloc[0]['NOME']
                forn_cadastrado = promotor.iloc[0]['FORNECEDOR']
                st.success(f"Bem-vindo, **{nome_logado}**! (Empresa: {forn_cadastrado})")
                
                col1, col2 = st.columns(2)
                agora = datetime.now()

                if col1.button("🔴 Registrar Entrada", use_container_width=True):
                    # Grava na aba VISITAS
                    df_v_atual = conn.read(worksheet="VISITAS", ttl=0)
                    nova_v = pd.DataFrame([{
                        "DATA": agora.strftime("%d/%m/%Y"), 
                        "CPF": cpf_visita, 
                        "FORNECEDOR": forn_cadastrado,
                        "ENTRADA": agora.strftime("%H:%M:%S"), 
                        "SAIDA": "", 
                        "TEMPO_MINUTOS": ""
                    }])
                    df_final = pd.concat([df_v_atual, nova_v], ignore_index=True)
                    conn.update(worksheet="VISITAS", data=df_final)
                    st.balloons()
                    st.success("Entrada Registrada com sucesso!")

                if col2.button("🟢 Registrar Saída", use_container_width=True):
                    df_v_atual = conn.read(worksheet="VISITAS", ttl=0)
                    # Busca a última entrada aberta deste CPF
                    mask = (df_v_atual['CPF'].astype(str) == str(cpf_visita)) & (df_v_atual['SAIDA'].isna() | (df_v_atual['SAIDA'] == ""))
                    
                    if mask.any():
                        idx = df_v_atual[mask].index[-1]
                        h_entrada_str = df_v_atual.at[idx, 'ENTRADA']
                        h_entrada = datetime.strptime(h_entrada_str, "%H:%M:%S")
                        
                        # Cálculo de tempo
                        dif = (agora.hour * 60 + agora.minute) - (h_entrada.hour * 60 + h_entrada.minute)
                        
                        df_v_atual.at[idx, 'SAIDA'] = agora.strftime("%H:%M:%S")
                        df_v_atual.at[idx, 'TEMPO_MINUTOS'] = dif
                        conn.update(worksheet="VISITAS", data=df_v_atual)
                        st.warning(f"Saída registrada! Permanência: {dif} min.")
                    else:
                        st.error("Nenhuma entrada aberta encontrada para este CPF.")
            else:
                st.error("CPF não cadastrado! Vá ao menu 'Cadastro de Promotor'.")

# --- TELA 2: CADASTRO DE PROMOTOR ---
elif menu == "Cadastro de Promotor":
    st.title("👤 Cadastro de Promotor")
    df_cadastros = conn.read(worksheet="CADASTROS", ttl=0)
    
    with st.form("cad_promotor", clear_on_submit=True):
        nome_c = st.text_input("Nome Completo")
        cpf_c = st.text_input("CPF (Somente números)", max_chars=11)
        # Campo Fornecedor adicionado conforme solicitado
        fornecedor_v = st.selectbox(
            "Selecione o Fornecedor vinculado:", 
            options=df_forn['Busca'].unique() if not df_forn.empty else [],
            index=None,
            placeholder="Escolha a empresa..."
        )
        
        if st.form_submit_button("Salvar Cadastro"):
            if nome_c and cpf_c and fornecedor_v:
                if str(cpf_c) in df_cadastros['CPF'].astype(str).values:
                    st.error("Erro: Este CPF já está cadastrado!")
                else:
                    novo_p = pd.DataFrame([{"CPF": cpf_c, "NOME": nome_c, "FORNECEDOR": fornecedor_v}])
                    df_novo_cad = pd.concat([df_cadastros, novo_p], ignore_index=True)
                    conn.update(worksheet="CADASTROS", data=df_novo_cad)
                    st.success("Cadastro realizado e salvo no Google Sheets!")
                    st.cache_data.clear() # Limpa o cache para mostrar o novo nome na tabela abaixo
            else:
                st.warning("Preencha todos os campos (Nome, CPF e Fornecedor).")

    st.write("---")
    st.write("### Promotores Cadastrados")
    st.dataframe(df_cadastros, use_container_width=True)

# --- TELA 3: RELATÓRIOS ---
elif menu == "Relatórios":
    st.title("📊 Relatório de Visitas")
    df_v = conn.read(worksheet="VISITAS", ttl=0)
    st.dataframe(df_v, use_container_width=True)
    
    if not df_v.empty:
        total_min = pd.to_numeric(df_v['TEMPO_MINUTOS'], errors='coerce').sum()
        st.metric("Total de Horas em Loja (Geral)", f"{total_min/60:.1f} hrs")