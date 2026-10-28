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

# Funções CRUD robustas com tratamento de rotas
def carregar_demandas():
    try:
        response = supabase.table("pacientes_demandas").select("*").order("id", desc=True).execute()
        return response.data if response.data else []
    except Exception:
        return []

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
    # Utiliza o método direto na tabela para inserção sem falhas de caminho
    supabase.table("pacientes_demandas").insert(dados).execute()

def atualizar_status(demanda_id, novo_status):
    atualizacao = {"status": novo_status}
    if novo_status == "Resolvido":
        atualizacao["data_resolucao"] = datetime.now().isoformat()
    supabase.table("pacientes_demandas").update(atualizacao).eq("id", demanda_id).execute()

# Interface Principal
st.title("🩺 Gestão de Atendimentos - Secretaria de Saúde")
st.markdown("---")

# Barra Lateral para Registo de Nova Demanda
st.sidebar.header("📝 Novo Atendimento")

with st.sidebar.form("form_demanda", clear_on_submit=True):
    nome = st.text_input("Nome do Paciente *")
    telefone = st.text_input("Telefone / WhatsApp (ex: 912345678)")
    cartao_sus = st.text_input("Cartão SUS")
    demanda = st.text_area("Descrição da Demanda / Caso *")
    reportado = st.text_input("Reportado por / Origem")
    data_limite = st.date_input("Data Limite / Prazo", value=date.today())
    
    submitted = st.form_submit_button("Registar Demanda", use_container_width=True)
    
    if submitted:
        if nome and demanda:
            try:
                salvar_demandas(nome, telefone, cartao_sus, demanda, reportado, data_limite)
                st.sidebar.success("Demanda registada com sucesso!")
                st.rerun()
            except Exception as ex:
                st.sidebar.error(f"Erro ao guardar: {ex}")
        else:
            st.sidebar.error("Preencha os campos obrigatórios (Nome e Demanda).")

# Carregar Dados e Apresentar no Painel
try:
    dados_demandas = carregar_demandas()
    
    if not dados_demandas:
        st.info("Ainda não existem demandas registadas. Utilize o menu lateral para criar o primeiro atendimento.")
    else:
        df = pd.DataFrame(dados_demandas)
        
        # --- Secção de Métricas (KPIs) ---
        total_atendimentos = len(df)
        em_andamento = len(df[df["status"] == "Em Andamento"]) if "status" in df.columns else 0
        pendentes = len(df[df["status"] == "Pendente"]) if "status" in df.columns else 0
        resolvidos = len(df[df["status"] == "Resolvido"]) if "status" in df.columns else 0
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total de Atendimentos", total_atendimentos)
        kpi2.metric("Em Andamento", em_andamento)
        kpi3.metric("Pendentes", pendentes)
        kpi4.metric("Resolvidos", resolvidos)
        
        st.markdown("---")
        
        # --- Filtros e Controlo ---
        st.subheader("🔍 Filtros e Pesquisa")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Em Andamento", "Pendente", "Resolvido"])
        
        with col_f2:
            busca_nome = st.text_input("Pesquisar por Nome ou Cartão SUS", placeholder="Digite o nome ou cartão...")
            
        df_filtrado = df.copy()
        if filtro_status != "Todos" and "status" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]
            
        if busca_nome and "nome" in df_filtrado.columns:
            df_filtrado = df_filtrado[
                df_filtrado["nome"].str.contains(busca_nome, case=False, na=False) | 
                df_filtrado["cartao_sus"].str.contains(busca_nome, case=False, na=False)
            ]

        st.markdown("---")
        st.subheader(f"📋 Lista de Atendimentos ({len(df_filtrado)})")
        
        for index, row in df_filtrado.iterrows():
            status_atual = row.get('status', 'Em Andamento')
            
            emoji_status = "🟡" if status_atual == "Em Andamento" else ("🟠" if status_atual == "Pendente" else "🟢")
            
            with st.expander(f"{emoji_status} **{row.get('nome', 'Sem Nome')}** — Status: **{status_atual}** | Prazo: {row.get('data_limite', 'N/A')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**📞 Telefone:** {row.get('telefone', 'Não informado')}")
                    st.markdown(f"**🆔 Cartão SUS:** {row.get('cartao_sus', 'Não informado')}")
                    st.markdown(f"**📝 Demanda:** {row['demanda']}")
                    st.markdown(f"**👤 Reportado por:** {row.get('reportado', 'N/A')}")
                    
                    tel = row.get('telefone')
                    if tel:
                        tel_limpo = "".join(filter(str.isdigit, str(tel)))
                        st.markdown(f"[💬 Enviar Mensagem WhatsApp](https://wa.me/55{tel_limpo})", unsafe_allow_html=True)

                with col2:
                    opcoes_status = ["Em Andamento", "Pendente", "Resolvido"]
                    idx_atual = opcoes_status.index(status_atual) if status_atual in opcoes_status else 0
                    
                    novo_estado = st.selectbox(
                        "Atualizar Status", 
                        opcoes_status, 
                        index=idx_atual,
                        key=f"status_{row.get('id', index)}"
                    )
                    
                    if novo_estado != status_atual:
                        atualizar_status(row['id'], novo_estado)
                        st.success("Estado atualizado com sucesso!")
                        st.rerun()

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
