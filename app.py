import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Configuração da página otimizada para dispositivos móveis
st.set_page_config(
    page_title="Gestão de Saúde",
    page_icon="🩺",
    layout="centered", # Layout centrado adapta-se muito melhor a telemóveis
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para uma experiência mobile limpa e touch-friendly
st.markdown("""
    <style>
        /* Aumentar áreas de toque e legibilidade em mobile */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            font-weight: bold;
        }
        .stSelectbox, .stTextInput, .stTextArea {
            margin-bottom: 0.5rem;
        }
        /* Estética dos cartões de atendimento */
        div.stExpander {
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
    </style>
""", unsafe_allow_html=True)

# Inicialização Oficial do Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"].rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-8]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Funções CRUD
def carregar_demandas():
    try:
        response = supabase.table("pacientes_demandas").select("*").order("id", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        return []

def salvar_demandas(nome, telefone, cartao_sus, demanda, reportado):
    try:
        status_inicial = "Delegado" if reportado and reportado.strip() != "" else "Em Aberto"
        
        dados = {
            "nome": nome,
            "telefone": telefone,
            "cartao_sus": cartao_sus,
            "demanda": demanda,
            "reportado": reportado,
            "status": status_inicial
        }
        response = supabase.table("pacientes_demandas").insert(dados).execute()
        return response
    except Exception as e:
        raise Exception(f"Erro ao guardar: {e}")

def atualizar_status(demanda_id, novo_status):
    try:
        atualizacao = {"status": novo_status}
        if novo_status == "Encerrado":
            atualizacao["data_resolucao"] = datetime.now().isoformat()
            
        supabase.table("pacientes_demandas").update(atualizacao).eq("id", demanda_id).execute()
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")

# --- CABEÇALHO MOBILE-FRIENDLY ---
st.markdown("### 🩺 Gestão de Atendimentos")
st.caption("Secretaria de Saúde — Painel Mobile")

# Carregar Dados Inicialmente para Métricas
dados_demandas = carregar_demandas()
df = pd.DataFrame(dados_demandas) if dados_demandas else pd.DataFrame()

# --- MÉTRICAS (KPIs Compactos) ---
if not df.empty:
    total = len(df)
    aberto = len(df[df["status"] == "Em Aberto"]) if "status" in df.columns else 0
    delegado = len(df[df["status"] == "Delegado"]) if "status" in df.columns else 0
    encerrado = len(df[df["status"] == "Encerrado"]) if "status" in df.columns else 0
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total", total)
    k2.metric("Abertos", aberto)
    k3.metric("Delegados", delegado)
    k4.metric("Encerrados", encerrado)

st.markdown("---")

# --- NOVO ATENDIMENTO (Expansor de Acesso Rápido no Topo) ---
with st.expander("➕ Registar Novo Atendimento", expanded=False):
    with st.form("form_demanda_mobile", clear_on_submit=True):
        nome = st.text_input("Nome do Paciente *")
        telefone = st.text_input("Telemóvel / WhatsApp")
        cartao_sus = st.text_input("Cartão SUS")
        demanda = st.text_area("Descrição do Caso / Demanda *")
        reportado = st.text_input("Reportado por / Origem (Deixe vazio para 'Em Aberto')")
        
        submitted = st.form_submit_button("Guardar Atendimento", use_container_width=True)
        
        if submitted:
            if nome and demanda:
                try:
                    salvar_demandas(nome, telefone, cartao_sus, demanda, reportado)
                    st.success("Registado com sucesso!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"{ex}")
            else:
                st.error("Preencha o Nome e a Descrição.")

# --- FILTROS E PESQUISA ---
if not df.empty:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos", "Em Aberto", "Delegado", "Encerrado"], label_visibility="collapsed")
    with col_f2:
        busca = st.text_input("Pesquisar", placeholder="Nome ou SUS...", label_visibility="collapsed")
        
    df_filtrado = df.copy()
    if filtro_status != "Todos" and "status" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]
        
    if busca and "nome" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["nome"].str.contains(busca, case=False, na=False) | 
            df_filtrado["cartao_sus"].str.contains(busca, case=False, na=False)
        ]

    st.markdown(f"**Atendimentos ({len(df_filtrado)})**")

    # --- LISTA DE CARTÕES ---
    for index, row in df_filtrado.iterrows():
        status_atual = row.get('status', 'Em Aberto')
        
        # Cores para os emojis de status
        emoji = "🟡" if status_atual == "Em Aberto" else ("🔵" if status_atual == "Delegado" else "🟢")
        
        with st.expander(f"{emoji} {row.get('nome', 'Sem Nome')} ({status_atual})"):
            st.markdown(f"**📱 Tel:** {row.get('telefone', 'Não inf.')}")
            st.markdown(f"**🆔 SUS:** {row.get('cartao_sus', 'Não inf.')}")
            st.markdown(f"**📝 Demanda:** {row.get('demanda', 'N/A')}")
            st.markdown(f"**👤 Origem:** {row.get('reportado', 'N/A')}")
            
            # Atalho rápido para WhatsApp se houver telefone
            tel = row.get('telefone')
            if tel:
                tel_limpo = "".join(filter(str.isdigit, str(tel)))
                st.markdown(f"[💬 Abrir no WhatsApp](https://wa.me/55{tel_limpo})", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Atualização de Status Otimizada para Mobile
            opcoes = ["Em Aberto", "Delegado", "Encerrado"]
            idx = opcoes.index(status_atual) if status_atual in opcoes else 0
            
            novo_estado = st.selectbox(
                "Mudar Status", 
                opcoes, 
                index=idx,
                key=f"st_{row.get('id', index)}"
            )
            
            if novo_estado != status_atual:
                atualizar_status(row['id'], novo_estado)
                st.success("Atualizado!")
                st.rerun()
else:
    st.info("Ainda não existem demandas registadas. Utilize o botão acima para começar.")
