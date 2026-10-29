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

# Estilização CSS Avançada para Cartões Clicáveis e Responsivos
st.markdown("""
    <style>
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
        
        /* Botões de métricas interativos */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
            border: none;
        }
        
        /* Estilização específica para os botões de filtro rápido */
        div[data-testid="column"] button {
            padding: 8px 4px;
            height: auto;
            min-height: 55px;
            font-size: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

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

# Gestão do Estado de Filtro Ativo via Cliques nos Cartões
if "filtro_ativo" not in st.session_state:
    st.session_state.filtro_ativo = "Todos"

# Função para comprimir imagem antes de enviar
def comprimir_imagem(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.thumbnail((800, 800))
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

# --- CARDS DE MÉTRICAS CLICÁVEIS (RESPONSIVOS) ---
if not df.empty:
    total = len(df)
    aberto = len(df[df["status"] == "Em Aberto"]) if "status" in df.columns else 0
    delegado = len(df[df["status"] == "Delegado"]) if "status" in df.columns else 0
    encerrado = len(df[df["status"] == "Encerrado"]) if "status" in df.columns else 0
    
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        if st.button(f"📊 Total\n\n{total}", key="btn_tot"):
            st.session_state.filtro_ativo = "Todos"
            st.rerun()
    with k2:
        if st.button(f"🟡 Aberto\n\n{aberto}", key="btn_ab"):
            st.session_state.filtro_ativo = "Em Aberto"
            st.rerun()
    with k3:
        if st.button(f"🟣 Deleg.\n\n{delegado}", key="btn_del"):
            st.session_state.filtro_ativo = "Delegado"
            st.rerun()
    with k4:
        if st.button(f"🟢 Encerr.\n\n{encerrado}", key="btn_enc"):
            st.session_state.filtro_ativo = "Encerrado"
            st.rerun()

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
        anexo = st.file_uploader("📎 Anexar Foto / Documento (Comprimido Auto)", type=["png", "jpg", "jpeg"])
        
        submitted = st.form_submit_button("💾 Guardar Atendimento", use_container_width=True)
        
        if submitted:
            if nome and demanda:
                try:
                    if anexo:
                        img_comprimida = comprimir_imagem(anexo)
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
        opcoes_filtro = ["Todos", "Em Aberto", "Delegado", "Encerrado"]
        idx_selecionado = opcoes_filtro.index(st.session_state.filtro_ativo) if st.session_state.filtro_ativo in opcoes_filtro else 0
        
        # Sincroniza o selectbox com o cartão clicado
        filtro_status = st.selectbox("Status", opcoes_filtro, index=idx_selecionado, label_visibility="collapsed")
        if filtro_status != st.session_state.filtro_ativo:
            st.session_state.filtro_ativo = filtro_status
            
    with col_f2:
        busca = st.text_input("Pesquisar", placeholder="🔍 Nome ou SUS...", label_visibility="collapsed")
        
    df_filtrado = df.copy()
    if st.session_state.filtro_ativo != "Todos" and "status" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["status"] == st.session_state.filtro_ativo]
        
    if busca and "nome" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["nome"].str.contains(busca, case=False, na=False) | 
            df_filtrado["cartao_sus"].str.contains(busca, case=False, na=False)
        ]

    st.markdown(f"### 📋 Atendimentos ({len(df_filtrado)}) — *Filtro: {st.session_state.filtro_ativo}*")

    for index, row in df_filtrado.iterrows():
        status_atual = row.get('status', 'Em Aberto')
        prioridade_atual = row.get('prioridade', 'Normal')
        previsao = row.get('data_previsao', 'N/A')
        
        prio_emoji = "🟢" if prioridade_atual == "Normal" else ("🟡" if prioridade_atual == "Média" else ("🟠" if prioridade_atual == "Alta" else "🔴"))
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
