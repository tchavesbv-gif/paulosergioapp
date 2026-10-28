import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Configuração da página para mobile
st.set_page_config(
    page_title="Gestão de Saúde",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS Avançada com Cores e Design Moderno
st.markdown("""
    <style>
        /* Estilo dos Cartões de Métricas (KPIs) */
        .metric-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 5px solid #2196F3;
            margin-bottom: 8px;
        }
        .metric-card.total { border-left-color: #2196F3; background-color: #E3F2FD; }
        .metric-card.aberto { border-left-color: #FFC107; background-color: #FFF8E1; }
        .metric-card.delegado { border-left-color: #9C27B0; background-color: #F3E5F5; }
        .metric-card.encerrado { border-left-color: #4CAF50; background-color: #E8F5E9; }

        .metric-card h4 {
            margin: 0;
            font-size: 0.8rem;
            color: #555555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-card h2 {
            margin: 4px 0 0 0;
            font-size: 1.5rem;
            font-weight: bold;
            color: #222222;
        }

        /* Botão do WhatsApp Destacado */
        .wsp-button {
            display: block;
            width: 100%;
            background-color: #25D366;
            color: white !important;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            text-decoration: none;
            margin-top: 10px;
            box-shadow: 0 2px 4px rgba(37,211,102,0.3);
        }

        /* Estilização dos Botões Streamlit */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            font-weight: bold;
            background-color: #1E88E5;
            color: white;
            border: none;
        }

        /* Expander Arredondado e Moderno */
        div.stExpander {
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
            margin-bottom: 8px;
            background-color: #ffffff;
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
    except Exception:
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
        return supabase.table("pacientes_demandas").insert(dados).execute()
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

# --- CABEÇALHO COM ÍCONES E COR ---
st.markdown("## 🩺 **Gestão de Atendimentos**")
st.markdown("<p style='color: #666; font-size: 0.9rem; margin-top: -15px;'>🏛️ Secretaria Municipal de Saúde</p>", unsafe_allow_html=True)

dados_demandas = carregar_demandas()
df = pd.DataFrame(dados_demandas) if dados_demandas else pd.DataFrame()

# --- CARDS DE MÉTRICAS COLORIDOS ---
if not df.empty:
    total = len(df)
    aberto = len(df[df["status"] == "Em Aberto"]) if "status" in df.columns else 0
    delegado = len(df[df["status"] == "Delegado"]) if "status" in df.columns else 0
    encerrado = len(df[df["status"] == "Encerrado"]) if "status" in df.columns else 0
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="metric-card total"><h4>📊 Total</h4><h2>{total}</h2></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="metric-card aberto"><h4>🟡 Aberto</h4><h2>{aberto}</h2></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="metric-card delegado"><h4>🟣 Delegado</h4><h2>{delegado}</h2></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="metric-card encerrado"><h4>🟢 Encerrado</h4><h2>{encerrado}</h2></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- FORMULÁRIO DE REGISTO ---
with st.expander("➕ **Registar Novo Atendimento**", expanded=False):
    with st.form("form_demanda_mobile", clear_on_submit=True):
        nome = st.text_input("👤 Nome do Paciente *")
        telefone = st.text_input("📱 Telemóvel / WhatsApp")
        cartao_sus = st.text_input("🆔 Cartão SUS")
        demanda = st.text_area("📝 Descrição do Caso / Demanda *")
        reportado = st.text_input("🏛️ Reportado por / Origem (Deixe vazio para 'Em Aberto')")
        
        submitted = st.form_submit_button("💾 Guardar Atendimento", use_container_width=True)
        
        if submitted:
            if nome and demanda:
                try:
                    salvar_demandas(nome, telefone, cartao_sus, demanda, reportado)
                    st.success("✅ Atendimento registado com sucesso!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"❌ {ex}")
            else:
                st.error("⚠️ Preencha os campos obrigatórios (Nome e Descrição).")

# --- FILTROS E LISTA ---
if not df.empty:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos", "Em Aberto", "Delegado", "Encerrado"], label_visibility="collapsed")
    with col_f2:
        busca = st.text_input("Pesquisar", placeholder="🔍 Pesquisar por Nome ou SUS...", label_visibility="collapsed")
        
    df_filtrado = df.copy()
    if filtro_status != "Todos" and "status" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]
        
    if busca and "nome" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["nome"].str.contains(busca, case=False, na=False) | 
            df_filtrado["cartao_sus"].str.contains(busca, case=False, na=False)
        ]

    st.markdown(f"### 📋 Lista de Pacientes ({len(df_filtrado)})")

    for index, row in df_filtrado.iterrows():
        status_atual = row.get('status', 'Em Aberto')
        
        # Identificação visual por cores e emojis
        if status_atual == "Em Aberto":
            tag_status = "🟡 **Em Aberto**"
        elif status_atual == "Delegado":
            tag_status = "🟣 **Delegado**"
        else:
            tag_status = "🟢 **Encerrado**"
        
        with st.expander(f"{tag_status} — **{row.get('nome', 'Sem Nome')}**"):
            st.markdown(f"**📱 Telemóvel:** {row.get('telefone', 'Não informado')}")
            st.markdown(f"**🆔 Cartão SUS:** {row.get('cartao_sus', 'Não informado')}")
            st.markdown(f"**📝 Demanda:** {row.get('demanda', 'N/A')}")
            st.markdown(f"**🏛️ Origem / Reportado:** {row.get('reportado', 'N/A')}")
            
            # Botão verde estilizado para abrir WhatsApp
            tel = row.get('telefone')
            if tel:
                tel_limpo = "".join(filter(str.isdigit, str(tel)))
                st.markdown(f'<a href="https://wa.me/55{tel_limpo}" target="_blank" class="wsp-button">💬 Conversar no WhatsApp</a>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Seletor de alteração de estado
            opcoes = ["Em Aberto", "Delegado", "Encerrado"]
            idx = opcoes.index(status_atual) if status_atual in opcoes else 0
            
            novo_estado = st.selectbox(
                "Mudar Estado do Atendimento", 
                opcoes, 
                index=idx,
                key=f"st_{row.get('id', index)}"
            )
            
            if novo_estado != status_atual:
                atualizar_status(row['id'], novo_estado)
                st.success("Status atualizado!")
                st.rerun()
else:
    st.info("ℹ️ Ainda não existem demandas registadas. Utilize o botão acima para criar o primeiro atendimento.")
