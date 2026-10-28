import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date

# Configuração da página
st.set_page_config(
    page_title="Gestão de Demandas de Saúde",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Conexão com Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Funções CRUD com esquema public explícito
def carregar_demandas():
    response = supabase.schema("public").table("pacientes_demandas").select("*").order("id", desc=True).execute()
    return response.data

def salvar_demandas(nome, telefone, cartao_sus, demanda, reportado, data_limite):
    dados = {
        "nome": nome,
        "telefone": telefone,
        "cartao_sus": cartao_sus,
        "demanda": demanda,
        "reportado": reportado,
        "status": "Em Andamento",
        "data_limite": str(data_limite) if data_limite else None
    }
    supabase.schema("public").table("pacientes_demandas").insert(dados).execute()

def atualizar_status(demanda_id, novo_status):
    atualizacao = {"status": novo_status}
    if novo_status == "Resolvido":
        atualizacao["data_resolucao"] = datetime.now().isoformat()
    supabase.schema("public").table("pacientes_demandas").update(atualizacao).eq("id", demanda_id).execute()

# Interface Principal
st.title("🩺 Gestão de Atendimentos - Secretaria de Saúde")
st.markdown("---")

# Barra Lateral para Registo de Nova Demanda
st.sidebar.header("Novo Atendimento")

with st.sidebar.form("form_demanda", clear_on_submit=True):
    nome = st.text_input("Nome do Paciente *")
    telefone = st.text_input("Telefone / WhatsApp (ex: 912345678)")
    cartao_sus = st.text_input("Cartão SUS")
    demanda = st.text_area("Descrição da Demanda / Caso *")
    reportado = st.text_input("Reportado por / Origem")
    data_limite = st.date_input("Data Limite / Prazo", value=date.today())
    
    submitted = st.form_submit_button("Registar Demanda")
    
    if submitted:
        if nome and demanda:
            salvar_demandas(nome, telefone, cartao_sus, demanda, reportado, data_limite)
            st.sidebar.success("Demanda registada com sucesso!")
            st.rerun()
        else:
            st.sidebar.error("Preencha os campos obrigatórios (Nome e Demanda).")

# Carregar Dados e Apresentar no Painel
try:
    dados_demandas = carregar_demandas()
    
    if not dados_demandas:
        st.info("Ainda não existem demandas registadas. Utilize o menu lateral para criar o primeiro atendimento.")
    else:
        df = pd.DataFrame(dados_demandas)
        
        # Filtros Rápidos
        st.subheader("Filtros e Controlo")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Em Andamento", "Resolvido", "Pendente"])
        
        with col_f2:
            busca_nome = st.text_input("Pesquisar por Nome ou Cartão SUS")
            
        df_filtrado = df.copy()
        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]
            
        if busca_nome:
            df_filtrado = df_filtrado[
                df_filtrado["nome"].str.contains(busca_nome, case=False, na=False) | 
                df_filtrado["cartao_sus"].str.contains(busca_nome, case=False, na=False)
            ]

        st.markdown("---")
        st.subheader(f"Lista de Atendimentos ({len(df_filtrado)})")
        
        for index, row in df_filtrado.iterrows():
            with st.expander(f"👤 {row['nome']} | Status: {row['status']} | Prazo: {row.get('data_limite', 'N/A')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Telefone:** {row.get('telefone', 'Não informado')}")
                    st.write(f"**Cartão SUS:** {row.get('cartao_sus', 'Não informado')}")
                    st.write(f"**Demanda:** {row['demanda']}")
                    st.write(f"**Reportado por:** {row.get('reportado', 'N/A')}")
                    
                    tel = row.get('telefone')
                    if tel:
                        tel_limpo = "".join(filter(str.isdigit, str(tel)))
                        st.markdown(f"[💬 Enviar Mensagem WhatsApp](https://wa.me/55{tel_limpo})", unsafe_allow_html=True)

                with col2:
                    status_atual = row['status']
                    novo_estado = st.selectbox(
                        "Alterar Status", 
                        ["Em Andamento", "Pendente", "Resolvido"], 
                        index=["Em Andamento", "Pendente", "Resolvido"].index(status_atual) if status_atual in ["Em Andamento", "Pendente", "Resolvido"] else 0,
                        key=f"status_{row['id']}"
                    )
                    
                    if novo_estado != status_atual:
                        atualizar_status(row['id'], novo_estado)
                        st.success("Atualizado!")
                        st.rerun()

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
