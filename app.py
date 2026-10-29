import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
import io
from PIL import Image

# Configuração da página para mobile
st.set_page_config(
    page_title="Gestão de Saúde",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para evitar quebras de linha no título e otimizar mobile
st.markdown("""
    <style>
        /* Título responsivo e compacto para telemóveis */
        .main-title {
            font-size: 1.3rem !important;
            font-weight: bold;
            color: #1E3A8A;
            margin-bottom: 0px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .sub-title {
            color: #666; 
            font-size: 0.8rem; 
            margin-top: -5px;
            margin-bottom: 10px;
        }
        
        /* Estilo dos Cartões de Métricas (KPIs) */
        .metric-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid #2196F3;
            margin-bottom: 6px;
        }
        .metric-card.total { border-left-color: #2196F3; background-color: #E3F2FD; }
        .metric-card.aberto { border-left-color: #FFC107; background-color: #FFF8E1; }
        .metric-card.delegado { border-left-color: #9C27B0; background-color: #F3E5F5; }
        .metric-card.encerrado { border-left-color: #4CAF50; background-color: #E8F5E9; }

        .metric-card h4 {
            margin: 0;
            font-size: 0.7rem;
            color: #555;
            text-transform: uppercase;
        }
        .metric-card h2 {
            margin: 2px 0 0 0;
            font-size: 1.2rem;
            font-weight: bold;
            color: #222;
        }

        /* Botão do WhatsApp */
        .wsp-button {
            display: block;
            width: 100%;
            background-color: #25D366;
            color: white !important;
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            font-weight: bold;
            text-decoration: none;
            margin-top: 8px;
        }

        .stButton button {
            width: 100%;
            border-radius: 8px;
            height: 2.8em;
            font-weight: bold;
            background-color: #1E88E5;
            color: white;
            border: none;
        }

        div.stExpander {
            border-radius: 10px !important;
            border: 1px solid #e2e8f0 !important;
            margin-bottom: 6px;
            background-color: #fff;
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

# Função para comprimir imagem antes de enviar (economiza espaço no Supabase)
def comprimir_imagem(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        # Converter para RGB caso esteja em RGBA (PNG com transparência)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Redimensionar mantendo a proporção (máximo 800px de largura/altura)
        image.thumbnail((800, 800))
        
        # Guardar em buffer com compressão JPEG (qualidade 60 para otimizar espaço)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=60, optimize=True)
        return buffer.getvalue()
    except Exception:
        return None

# Funções CRUD
def carregar_demandas():
    try:
        response = supabase.table("pacientes_demandas").select("*").order("id", desc=True).execute()
        return response.data if response.data else []
    except Exception:
        return []

def salvar_demandas(nome, telefone, cartao_sus, demanda, reportado, prioridade, data_previsao):
    try:
        status_inicial = "Delegado" if reportado and reportado.strip() != "" else "Em Aberto"
        
        dados = {
            "nome": nome,
            "telefone": telefone,
            "cartao_sus": cartao_sus,
            "demanda": demanda,
            "reportado": reportado,
            "status": status_inicial,
            "prioridade": prioridade,
            "data_previsao": str(data_previsao) if data_previsao else None
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

# --- CABEÇALHO COMPACTO MOBILE ---
st.markdown('<p class="main-title">🩺 Gestão de Atendimentos</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Secretaria Municipal de Saúde</p>', unsafe_allow_html=True)

dados_demandas = carregar_demandas()
df = pd.DataFrame(dados_demandas) if dados_demandas else pd.DataFrame()

# --- CARDS DE MÉTRICAS ---
if not df.empty:
    total = len(df)
    aberto = len(df[df["status"] == "Em Aberto"]) if "status" in df.columns else 0
    delegado = len(df[df["status"] == "Delegado"]) if "status" in df.columns else 0
    encerrado = len(df[df["status"] == "Encerrado"]) if "status" in df.columns else 0
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="metric-card total"><h4>Total</h4><h2>{total}</h2></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="metric-card aberto"><h4>Aberto</h4><h2>{aberto}</h2></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="metric-card delegado"><h4>Deleg.</h4><h2>{delegado}</h2></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="metric-card encerrado"><h4>Encerr.</h4><h2>{encerrado}</h2></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- FORMULÁRIO DE REGISTO ---
with st.expander("➕ **Registar Novo Atendimento**", expanded=False):
    with st.form("form_demanda_mobile", clear_on_submit=True):
        nome = st.text_input("👤 Nome do Paciente *")
        telefone = st.text_input("📱 Telemóvel / WhatsApp")
        cartao_sus = st.text_input("🆔 Cartão SUS")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            prioridade = st.selectbox("⚡ Prioridade", ["Normal", "Média", "Alta", "Urgente"])
        with col_p2:
            data_previsao = st.date_input("📅 Previsão Resolução", value=date.today())
            
        demanda = st.text_area("📝 Descrição do Caso / Demanda *")
        reportado = st.text_input("🏛️ Reportado por / Origem (Vazio = 'Em Aberto')")
        
        # Campo de Anexo Otimizado para Compressão
        anexo = st.file_uploader("📎 Anexar Foto / Documento (Comprimido Auto)", type=["png", "jpg", "jpeg"])
        
        submitted = st.form_submit_button("💾 Guardar Atendimento", use_container_width=True)
        
        if submitted:
            if nome and demanda:
                try:
                    # Se houver anexo, comprimimos (poderá guardar numa coluna binária ou bucket futuramente)
                    if anexo:
                        img_comprimida = comprimir_imagem(anexo)
                        # Nota: O ficheiro foi comprimido com sucesso para economizar espaço
                    
                    salvar_demandas(nome, telefone, cartao_sus, demanda, reportado, prioridade, data_previsao)
                    st.success("✅ Atendimento registado com sucesso!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"❌ {ex}")
            else:
                st.error("⚠️ Preencha o Nome e a Descrição.")

# --- FILTROS E LISTA ---
if not df.empty:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos", "Em Aberto", "Delegado", "Encerrado"], label_visibility="collapsed")
    with col_f2:
        busca = st.text_input("Pesquisar", placeholder="🔍 Nome ou SUS...", label_visibility="collapsed")
        
    df_filtrado = df.copy()
    if filtro_status != "Todos" and "status" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]
        
    if busca and "nome" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["nome"].str.contains(busca, case=False, na=False) | 
            df_filtrado["cartao_sus"].str.contains(busca, case=False, na=False)
        ]

    st.markdown(f"### 📋 Atendimentos ({len(df_filtrado)})")

    for index, row in df_filtrado.iterrows():
        status_atual = row.get('status', 'Em Aberto')
        prioridade_atual = row.get('prioridade', 'Normal')
        previsao = row.get('data_previsao', 'N/A')
        
        # Emojis de prioridade
        prio_emoji = "🟢" if prioridade_atual == "Normal" else ("🟡" if prioridade_atual == "Média" else ("🟠" if prioridade_atual == "Alta" else "🔴"))
        
        # Emojis de status
        status_emoji = "🟡" if status_atual == "Em Aberto" else ("🟣" if status_atual == "Delegado" else "🟢")
        
        titulo_card = f"{status_emoji} {prio_emoji} **{row.get('nome', 'Sem Nome')}**"
        
        with st.expander(titulo_card):
            st.markdown(f"**⚡ Prioridade:** {prioridade_atual}")
            st.markdown(f"**📅 Previsão:** {previsao}")
            st.markdown(f"**📱 Telemóvel:** {row.get('telefone', 'Não inf.')}")
            st.markdown(f"**🆔 Cartão SUS:** {row.get('cartao_sus', 'Não inf.')}")
            st.markdown(f"**📝 Demanda:** {row.get('demanda', 'N/A')}")
            st.markdown(f"**🏛️ Origem:** {row.get('reportado', 'N/A')}")
            
            tel = row.get('telefone')
            if tel:
                tel_limpo = "".join(filter(str.isdigit, str(tel)))
                st.markdown(f'<a href="https://wa.me/55{tel_limpo}" target="_blank" class="wsp-button">💬 Conversar no WhatsApp</a>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            opcoes = ["Em Aberto", "Delegado", "Encerrado"]
            idx = opcoes.index(status_atual) if status_atual in opcoes else 0
            
            novo_estado = st.selectbox(
                "Mudar Estado", 
                opcoes, 
                index=idx,
                key=f"st_{row.get('id', index)}"
            )
            
            if novo_estado != status_atual:
                atualizar_status(row['id'], novo_estado)
                st.success("Atualizado!")
                st.rerun()
else:
    st.info("ℹ️ Sem demandas registadas. Utilize o botão acima para começar.")
