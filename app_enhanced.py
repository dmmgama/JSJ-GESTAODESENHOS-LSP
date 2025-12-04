"""
Streamlit app - UI for JSJ Drawing Management LPP Sync (Enhanced Version).
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date

# Enhanced UI components
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from streamlit_option_menu import option_menu
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
import plotly.express as px
import plotly.graph_objects as go

from db import (
    get_connection, criar_tabelas, get_all_desenhos, get_revisoes_by_desenho_id, 
    get_desenho_by_layout, get_dwg_list, delete_all_desenhos, delete_desenhos_by_dwg, 
    delete_desenhos_by_tipo, delete_desenhos_by_elemento, delete_desenho_by_layout, 
    get_db_stats, get_all_desenhos_with_revisoes, get_unique_tipos, get_unique_elementos, 
    get_all_layout_names, update_estado_interno, update_estado_e_comentario,
    get_historico_comentarios, get_desenhos_by_estado, get_desenhos_em_atraso,
    get_desenho_by_id, get_stats_by_estado, ESTADOS_VALIDOS,
    get_unique_revision_dates, get_desenhos_at_date
)
from db_projects import (
    get_all_projetos, get_projeto_by_num, upsert_projeto,
    get_desenhos_by_projeto, get_projeto_stats, get_unique_dwg_sources,
    inicializar_multiproject
)
from json_importer import import_all_json
from csv_importer import import_all_csv, import_single_csv
from lpp_builder import build_lpp_from_db

# Estado interno colors and labels
ESTADO_CONFIG = {
    'projeto': {'label': '📋 Projeto', 'color': '#6c757d', 'bg': '#f8f9fa'},
    'needs_revision': {'label': '⚠️ Precisa Revisão', 'color': '#dc3545', 'bg': '#fff3cd'},
    'built': {'label': '✅ Construído', 'color': '#28a745', 'bg': '#d4edda'}
}

# ========================================
# CUSTOM CSS THEME
# ========================================
def load_custom_css():
    """Inject custom CSS for compact, professional UI"""
    st.markdown("""
    <style>
        /* Main app - subtle background */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* Sidebar - darker with good contrast */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1f2e 0%, #2c3e50 100%);
        }
        
        /* Sidebar text colors - specific selectors */
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #ffffff !important;
        }
        
        /* Keep inputs/selects readable */
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] textarea {
            color: #1a1f2e !important;
            background-color: #ffffff !important;
        }
        
        /* Compact metric cards */
        [data-testid="stMetricValue"] {
            font-size: 20px !important;
            font-weight: 600;
            color: #2c3e50;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 12px !important;
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 13px !important;
        }
        
        div[data-testid="metric-container"] {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 8px 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        
        /* Sidebar metrics - darker background to match sidebar */
        [data-testid="stSidebar"] div[data-testid="metric-container"] {
            background-color: #34495e !important;
            border: 1px solid #4a5f7f;
        }
        
        [data-testid="stSidebar"] [data-testid="stMetricValue"],
        [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
            color: #ffffff !important;
        }
        
        /* Compact buttons */
        .stButton>button {
            padding: 6px 16px !important;
            font-size: 14px !important;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        
        .stButton>button[kind="primary"] {
            background: #556B2F;
            color: white;
            border: none;
        }
        
        .stButton>button[kind="secondary"] {
            background: white;
            color: #556B2F;
            border: 1px solid #556B2F;
        }
        
        /* Compact headers */
        h1 {
            font-size: 26px !important;
            color: #1a1f2e;
            margin-bottom: 16px !important;
            padding-bottom: 8px;
            border-bottom: 3px solid #556B2F;
        }
        
        h2 {
            font-size: 20px !important;
            color: #2c3e50;
            margin-top: 16px !important;
            margin-bottom: 12px !important;
        }
        
        h3 {
            font-size: 16px !important;
            color: #34495e;
            margin-top: 12px !important;
            margin-bottom: 8px !important;
        }
        
        /* Reduce spacing */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* Tables */
        .dataframe {
            font-size: 13px !important;
        }
        
        /* Compact selectbox and inputs */
        .stSelectbox, .stTextInput {
            margin-bottom: 8px !important;
        }
        
        .stSelectbox label, .stTextInput label {
            font-size: 13px !important;
            margin-bottom: 4px !important;
        }
        
        /* Alert boxes */
        .stAlert {
            padding: 8px 12px !important;
            font-size: 13px !important;
            border-radius: 6px;
        }
        
        /* Info boxes more compact */
        .stInfo, .stWarning, .stSuccess, .stError {
            padding: 10px 14px !important;
            font-size: 13px !important;
        }
        
        /* Make expanders more subtle */
        .streamlit-expanderHeader {
            background-color: #f0f2f6;
            font-size: 14px !important;
            padding: 8px 12px !important;
        }
        
        /* Sidebar elements smaller */
        [data-testid="stSidebar"] .stButton>button {
            font-size: 13px !important;
            padding: 8px 12px !important;
        }
        
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            font-size: 16px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="JSJ - LPP Sync Enhanced",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Initialize database
def init_db():
    """Initialize database - create tables if needed."""
    conn = get_connection()
    criar_tabelas(conn)
    conn.close()

init_db()

# Initialize multi-project support (V42+)
try:
    inicializar_multiproject()
except Exception:
    pass  # Already initialized

# Initialize session state for multi-project
if 'projeto_ativo' not in st.session_state:
    st.session_state['projeto_ativo'] = None
if 'projetos_mode' not in st.session_state:
    st.session_state['projetos_mode'] = 'list'

# ========================================
# SIDEBAR NAVIGATION
# ========================================
with st.sidebar:
    # JSJ Logo
    try:
        st.image("assets/jsj_logo.jpg", use_container_width=True)
    except:
        st.markdown("### JSJ Engenharia")
    st.markdown("## 🔧 Navegação")
    
    selected_page = option_menu(
        menu_title=None,
        options=["Projetos", "Gestão de Desenhos", "Dashboard", "Histórico", "Configurações"],
        icons=["folder", "pencil-square", "speedometer2", "clock-history", "gear"],
        menu_icon="cast",
        default_index=1,  # Start on "Gestão de Desenhos"
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#ffffff", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "3px",
                "color": "#ffffff",
                "border-radius": "6px",
                "padding": "8px 12px",
            },
            "nav-link-selected": {
                "background": "#556B2F",
                "font-weight": "600",
            },
        }
    )
    
    st.markdown("---")
    
    # Projeto Ativo Indicator
    if st.session_state.get('projeto_ativo'):
        conn = get_connection()
        projeto = get_projeto_by_num(conn, st.session_state['projeto_ativo'])
        conn.close()
        
        if projeto:
            st.success(f"📂 **Projeto Ativo:**\n{projeto['proj_num']} - {projeto['proj_nome']}")
            if st.button("🔄 Limpar Seleção", use_container_width=True):
                st.session_state['projeto_ativo'] = None
                st.rerun()
    else:
        st.warning("⚠️ Nenhum projeto selecionado")
        st.caption("Vá a 'Projetos' para selecionar")
    
    st.markdown("---")
    
    # Quick stats in sidebar
    conn = get_connection()
    db_stats = get_db_stats(conn)
    conn.close()
    
    st.markdown(f"### 📊 Quick Stats")
    st.metric("Total Desenhos", db_stats['total_desenhos'], label_visibility="visible")
    st.metric("DWG Files", db_stats['total_dwgs'], label_visibility="visible")

# ========================================
# PAGE: PROJETOS
# ========================================
if selected_page == "Projetos":
    st.title("📂 Gestão de Projetos")
    
    # Display mode selection
    col_mode1, col_mode2, col_mode3 = st.columns([1, 1, 3])
    with col_mode1:
        if st.button("📋 Listar Projetos", use_container_width=True, type="primary" if st.session_state.get('projetos_mode', 'list') == 'list' else "secondary"):
            st.session_state['projetos_mode'] = 'list'
            st.rerun()
    with col_mode2:
        if st.button("➕ Novo Projeto", use_container_width=True, type="primary" if st.session_state.get('projetos_mode') == 'create' else "secondary"):
            st.session_state['projetos_mode'] = 'create'
            st.rerun()
    
    st.markdown("---")
    
    # LIST MODE
    if st.session_state.get('projetos_mode', 'list') == 'list':
        conn = get_connection()
        projetos = get_all_projetos(conn)
        conn.close()
        
        if not projetos:
            st.info("ℹ️ Nenhum projeto encontrado. Importe um CSV para criar projetos automaticamente.")
        else:
            st.markdown("### 📊 Projetos Disponíveis")
            
            # Create table data
            projeto_data = []
            for p in projetos:
                conn = get_connection()
                stats = get_projeto_stats(conn, p['proj_num'])
                conn.close()
                
                projeto_data.append({
                    'PROJ_NUM': p['proj_num'],
                    'NOME': p['proj_nome'] or '-',
                    'CLIENTE': p['cliente'] or '-',
                    'OBRA': p['obra'] or '-',
                    'DESENHOS': stats['total_desenhos'],
                    'DWGs': stats['dwg_sources_count']
                })
            
            df_projetos = pd.DataFrame(projeto_data)
            
            # Display with AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_projetos)
            gb.configure_selection('single', use_checkbox=False)
            gb.configure_default_column(filterable=True, sorteable=True, resizable=True)
            gb.configure_pagination(paginationPageSize=20)
            gb.configure_column("PROJ_NUM", header_name="Projeto", width=100, pinned='left')
            gb.configure_column("NOME", header_name="Nome", width=250)
            gb.configure_column("CLIENTE", header_name="Cliente", width=200)
            gb.configure_column("OBRA", header_name="Obra", width=200)
            gb.configure_column("DESENHOS", header_name="Desenhos", width=100)
            gb.configure_column("DWGs", header_name="DWGs", width=100)
            
            grid_response = AgGrid(
                df_projetos,
                gridOptions=gb.build(),
                height=400,
                theme='streamlit',
                update_mode=GridUpdateMode.SELECTION_CHANGED
            )
            
            st.markdown("---")
            st.info("💡 **Como ativar um projeto:** Selecione uma linha na tabela acima e clique no botão 'Ativar Projeto' abaixo.")
            
            # Selection handler
            selected_rows = grid_response['selected_rows']
            if selected_rows is not None and len(selected_rows) > 0:
                selected = selected_rows.iloc[0] if isinstance(selected_rows, pd.DataFrame) else selected_rows[0]
                proj_num = selected['PROJ_NUM']
                
                col_sel1, col_sel2 = st.columns([3, 1])
                with col_sel1:
                    st.success(f"**✓ Selecionado:** {proj_num} - {selected['NOME']}")
                with col_sel2:
                    if st.button(f"✅ Ativar Projeto", type="primary", use_container_width=True, key="btn_ativar_projeto"):
                        st.session_state['projeto_ativo'] = proj_num
                        st.success(f"Projeto {proj_num} ativado!")
                        st.rerun()
            else:
                st.warning("⚠️ Nenhum projeto selecionado. Clique numa linha da tabela acima.")
    
    # CREATE MODE
    elif st.session_state['projetos_mode'] == 'create':
        st.markdown("### ➕ Criar Novo Projeto")
        
        with st.form("create_projeto"):
            col1, col2 = st.columns(2)
            
            with col1:
                proj_num = st.text_input("PROJ_NUM *", help="Número único do projeto (ex: 669)")
                proj_nome = st.text_input("Nome do Projeto")
                cliente = st.text_input("Cliente")
                obra = st.text_input("Obra")
            
            with col2:
                localizacao = st.text_input("Localização")
                especialidade = st.text_input("Especialidade", value="ESTRUTURAS")
                projetou = st.text_input("Projetou")
            
            col_submit1, col_submit2 = st.columns([1, 3])
            with col_submit1:
                submitted = st.form_submit_button("💾 Criar Projeto", type="primary", use_container_width=True)
            with col_submit2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state['projetos_mode'] = 'list'
                    st.rerun()
            
            if submitted:
                if not proj_num:
                    st.error("❌ PROJ_NUM é obrigatório")
                else:
                    projeto_data = {
                        'proj_num': proj_num,
                        'proj_nome': proj_nome,
                        'cliente': cliente,
                        'obra': obra,
                        'localizacao': localizacao,
                        'especialidade': especialidade,
                        'projetou': projetou
                    }
                    
                    try:
                        conn = get_connection()
                        upsert_projeto(conn, projeto_data)
                        conn.close()
                        
                        st.success(f"✅ Projeto {proj_num} criado com sucesso!")
                        st.session_state['projetos_mode'] = 'list'
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao criar projeto: {e}")

# ========================================
# PAGE: DASHBOARD
# ========================================
elif selected_page == "Dashboard":
    st.title("📊 Dashboard - Visão Geral")
    
    # Load data
    conn = get_connection()
    desenhos = get_all_desenhos(conn)
    estado_stats = get_stats_by_estado(conn)
    conn.close()
    
    if desenhos:
        df = pd.DataFrame(desenhos)
        if 'estado_interno' not in df.columns:
            df['estado_interno'] = 'projeto'
        df['estado_interno'] = df['estado_interno'].fillna('projeto')
        
        # Top metrics with styled cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Desenhos", len(df), delta=None)
        with col2:
            st.metric("📋 Projeto", estado_stats.get('projeto', 0))
        with col3:
            st.metric("⚠️ Precisa Revisão", estado_stats.get('needs_revision', 0))
        with col4:
            st.metric("✅ Construído", estado_stats.get('built', 0))
        with col5:
            em_atraso = estado_stats.get('em_atraso', 0)
            st.metric("🚨 Em Atraso", em_atraso, delta=f"-{em_atraso}" if em_atraso > 0 else None)
        
        style_metric_cards()
        
        st.markdown("---")
        
        # Charts row 1
        colored_header(
            label="Distribuição de Estados e Tipos",
            description="Análise visual dos desenhos por estado e tipo",
            color_name="blue-70"
        )
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Pie chart - Distribution by Estado
            estado_counts = df['estado_interno'].value_counts()
            estado_labels = [ESTADO_CONFIG.get(e, {}).get('label', e) for e in estado_counts.index]
            
            fig_estado = px.pie(
                values=estado_counts.values,
                names=estado_labels,
                title="Distribuição por Estado Interno",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig_estado.update_traces(textposition='inside', textinfo='percent+label')
            fig_estado.update_layout(height=280, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_estado, use_container_width=True)
        
        with col_chart2:
            # Bar chart - Top 10 Tipos
            if 'tipo_display' in df.columns:
                tipo_counts = df['tipo_display'].value_counts().head(10)
                fig_tipos = px.bar(
                    x=tipo_counts.values,
                    y=tipo_counts.index,
                    orientation='h',
                    title="Top 10 Tipos de Desenho",
                    labels={'x': 'Quantidade', 'y': 'Tipo'},
                    color=tipo_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_tipos.update_layout(height=280, showlegend=False, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_tipos, use_container_width=True)
        
        st.markdown("---")
        
        # Charts row 2
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            # Bar chart - Top 10 Elementos
            if 'elemento_key' in df.columns:
                elemento_counts = df['elemento_key'].value_counts().head(10)
                fig_elementos = px.bar(
                    x=elemento_counts.index,
                    y=elemento_counts.values,
                    title="Top 10 Elementos",
                    labels={'x': 'Elemento', 'y': 'Quantidade'},
                    color=elemento_counts.values,
                    color_continuous_scale='Greens'
                )
                fig_elementos.update_layout(height=280, showlegend=False, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_elementos, use_container_width=True)
        
        with col_chart4:
            # Distribution by DWG
            if 'dwg_name' in df.columns:
                dwg_counts = df['dwg_name'].value_counts()
                fig_dwg = px.bar(
                    x=dwg_counts.index,
                    y=dwg_counts.values,
                    title="Desenhos por DWG",
                    labels={'x': 'DWG', 'y': 'Quantidade'},
                    color=dwg_counts.values,
                    color_continuous_scale='Oranges'
                )
                fig_dwg.update_layout(height=280, showlegend=False, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_dwg, use_container_width=True)
        
        # Timeline of revisions
        st.markdown("---")
        colored_header(
            label="Timeline de Revisões",
            description="Histórico de revisões ao longo do tempo",
            color_name="green-70"
        )
        
        if 'r_data' in df.columns and df['r_data'].notna().any():
            # Filter valid dates
            df_timeline = df[df['r_data'].notna() & (df['r_data'] != '')].copy()
            if not df_timeline.empty:
                df_timeline['r_data'] = pd.to_datetime(df_timeline['r_data'], errors='coerce')
                df_timeline = df_timeline.dropna(subset=['r_data'])
                
                if not df_timeline.empty:
                    # Count revisions by date
                    rev_timeline = df_timeline.groupby(df_timeline['r_data'].dt.date).size().reset_index()
                    rev_timeline.columns = ['Data', 'Nº Revisões']
                    
                    fig_timeline = px.line(
                        rev_timeline,
                        x='Data',
                        y='Nº Revisões',
                        title="Revisões ao Longo do Tempo",
                        markers=True
                    )
                    fig_timeline.update_traces(line_color='#556B2F', line_width=3)
                    fig_timeline.update_layout(height=250, margin=dict(t=40, b=20, l=20, r=20))
                    st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum desenho na base de dados. Importe dados primeiro.")

# ========================================
# PAGE: GESTÃO DE DESENHOS
# ========================================
elif selected_page == "Gestão de Desenhos":
    st.title("📐 Gestão de Desenhos")
    
    # Load data
    conn = get_connection()
    desenhos = get_all_desenhos(conn)
    estado_stats = get_stats_by_estado(conn)
    conn.close()
    
    if not desenhos:
        st.warning("⚠️ Nenhum desenho na base de dados. Importe dados primeiro.")
    else:
        df = pd.DataFrame(desenhos)
        if 'estado_interno' not in df.columns:
            df['estado_interno'] = 'projeto'
        df['estado_interno'] = df['estado_interno'].fillna('projeto')
        
        # Quick stats
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total", len(df))
        with col2:
            st.metric("📋 Projeto", estado_stats.get('projeto', 0))
        with col3:
            st.metric("⚠️ Precisa Revisão", estado_stats.get('needs_revision', 0))
        with col4:
            st.metric("✅ Construído", estado_stats.get('built', 0))
        with col5:
            em_atraso = estado_stats.get('em_atraso', 0)
            st.metric("🚨 Em Atraso", em_atraso)
        
        style_metric_cards()
        
        st.markdown("---")
        
        # Filters
        st.markdown("### 🔍 Filtros")
        
        # Project and DWG Source filters
        col_proj, col_dwg = st.columns(2)
        
        with col_proj:
            conn = get_connection()
            projetos = get_all_projetos(conn)
            conn.close()
            
            projeto_options = ["Todos"]
            if projetos:
                projeto_options += [f"{p['proj_num']} - {p['proj_nome']}" for p in projetos]
            
            # Get default index based on active project
            default_idx = 0
            if st.session_state.get('projeto_ativo'):
                for idx, opt in enumerate(projeto_options):
                    if opt.startswith(st.session_state['projeto_ativo']):
                        default_idx = idx
                        break
            
            projeto_filter_label = st.selectbox(
                "📂 PROJETO", 
                projeto_options,
                index=default_idx,
                key="projeto_filter_select"
            )
            
            # Extract proj_num from selection
            if projeto_filter_label != "Todos":
                projeto_filter = projeto_filter_label.split(" - ")[0]
            else:
                projeto_filter = "Todos"
        
        with col_dwg:
            if projeto_filter != "Todos":
                conn = get_connection()
                dwg_sources = get_unique_dwg_sources(conn, projeto_filter)
                conn.close()
                dwg_options = ["Todos"] + [d for d in dwg_sources if d]
            else:
                dwg_options = ["Todos"]
            
            dwg_filter = st.selectbox("📁 DWG SOURCE", dwg_options, key="dwg_filter_select")
        
        # Estado filter buttons
        estado_col1, estado_col2, estado_col3, estado_col4, estado_col5 = st.columns(5)
        
        if 'estado_filter' not in st.session_state:
            st.session_state.estado_filter = 'Todos'
        
        with estado_col1:
            if st.button("🔄 Todos", use_container_width=True, 
                         type="primary" if st.session_state.estado_filter == 'Todos' else "secondary"):
                st.session_state.estado_filter = 'Todos'
                st.rerun()
        with estado_col2:
            if st.button("📋 Projeto", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'projeto' else "secondary"):
                st.session_state.estado_filter = 'projeto'
                st.rerun()
        with estado_col3:
            if st.button("⚠️ Precisa Revisão", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'needs_revision' else "secondary"):
                st.session_state.estado_filter = 'needs_revision'
                st.rerun()
        with estado_col4:
            if st.button("✅ Construído", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'built' else "secondary"):
                st.session_state.estado_filter = 'built'
                st.rerun()
        with estado_col5:
            if st.button("🚨 Em Atraso", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'em_atraso' else "secondary"):
                st.session_state.estado_filter = 'em_atraso'
                st.rerun()
        
        # Other filters
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            tipo_options = ["Todos"] + sorted(df['tipo_display'].dropna().unique().tolist())
            tipo_filter = st.selectbox("TIPO", tipo_options)
        
        with col_f2:
            elemento_options = ["Todos"] + sorted(df['elemento_key'].dropna().unique().tolist())
            elemento_filter = st.selectbox("ELEMENTO", elemento_options)
        
        with col_f3:
            r_options = ["Todos"] + sorted(df['r'].dropna().unique().tolist())
            r_filter = st.selectbox("Revisão (R)", r_options)
        
        with col_f4:
            search_text = st.text_input("🔎 Procurar", "")
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply project and DWG filters
        if projeto_filter != "Todos":
            if 'proj_num' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['proj_num'] == projeto_filter]
        
        if dwg_filter != "Todos":
            if 'dwg_source' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['dwg_source'] == dwg_filter]
        
        if st.session_state.estado_filter == 'em_atraso':
            today = datetime.now().strftime('%Y-%m-%d')
            filtered_df = filtered_df[
                (filtered_df['estado_interno'] == 'needs_revision') & 
                (filtered_df['data_limite'].notna()) & 
                (filtered_df['data_limite'] != '') &
                (filtered_df['data_limite'] < today)
            ]
        elif st.session_state.estado_filter != 'Todos':
            filtered_df = filtered_df[filtered_df['estado_interno'] == st.session_state.estado_filter]
        
        if tipo_filter != "Todos":
            filtered_df = filtered_df[filtered_df['tipo_display'] == tipo_filter]
        
        if elemento_filter != "Todos":
            filtered_df = filtered_df[filtered_df['elemento_key'] == elemento_filter]
        
        if r_filter != "Todos":
            filtered_df = filtered_df[filtered_df['r'] == r_filter]
        
        if search_text:
            mask = (
                filtered_df['des_num'].str.contains(search_text, case=False, na=False) |
                filtered_df['layout_name'].str.contains(search_text, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        st.info(f"**Resultados:** {len(filtered_df)} desenhos encontrados")
        
        st.markdown("---")
        
        # AgGrid Table
        st.markdown("### 📋 Tabela de Desenhos")
        
        # Column Selection
        st.markdown("#### 🔧 Seleção de Colunas")
        
        # All available columns from the dataframe
        all_columns = [
            'id', 'des_num', 'layout_name', 'tipo_display', 'tipo_key', 'elemento', 'elemento_key',
            'titulo', 'r', 'r_data', 'r_desc', 'estado_interno', 'comentario', 'data_limite',
            'responsavel', 'dwg_name', 'dwg_source', 'cliente', 'obra', 'localizacao',
            'especialidade', 'fase', 'projetou', 'escalas', 'data', 'proj_num', 'proj_nome',
            'fase_pfix', 'emissao', 'pfix', 'id_cad', 'created_at', 'updated_at'
        ]
        
        # Default visible columns
        default_visible = [
            'id', 'des_num', 'layout_name', 'tipo_display', 'elemento', 'titulo',
            'r', 'r_data', 'estado_interno', 'comentario', 'data_limite', 'dwg_name'
        ]
        
        # Initialize session state for visible columns
        if 'visible_columns' not in st.session_state:
            st.session_state['visible_columns'] = default_visible
        
        # Filter to only show columns that exist in the filtered dataframe
        available_columns = [col for col in all_columns if col in filtered_df.columns]
        
        # Column selector
        col_selector1, col_selector2 = st.columns([3, 1])
        with col_selector1:
            selected_columns = st.multiselect(
                "Escolha as colunas a visualizar:",
                options=available_columns,
                default=[col for col in st.session_state['visible_columns'] if col in available_columns],
                key="column_selector"
            )
        
        with col_selector2:
            if st.button("🔄 Restaurar Padrão", use_container_width=True):
                st.session_state['visible_columns'] = default_visible
                st.rerun()
        
        # Update session state
        if selected_columns:
            st.session_state['visible_columns'] = selected_columns
            display_columns = selected_columns
        else:
            st.info("⚠️ Selecione pelo menos uma coluna para visualizar")
            display_columns = default_visible
        
        # Ensure 'id' is always included for functionality (but can be hidden in display)
        if 'id' not in display_columns and 'id' in filtered_df.columns:
            aggrid_df = filtered_df[['id'] + [col for col in display_columns if col in filtered_df.columns]].copy()
        else:
            aggrid_df = filtered_df[[col for col in display_columns if col in filtered_df.columns]].copy()
        
        # Store original data for comparison
        if 'original_data' not in st.session_state:
            st.session_state['original_data'] = aggrid_df.copy()
        
        # Format estado_interno for display
        if 'estado_interno' in aggrid_df.columns:
            # Keep original values for editing, just display formatted
            aggrid_df['estado_interno_display'] = aggrid_df['estado_interno'].apply(
                lambda x: ESTADO_CONFIG.get(x, ESTADO_CONFIG['projeto'])['label'] if x else 'projeto'
            )
        
        # Build AgGrid options
        gb = GridOptionsBuilder.from_dataframe(aggrid_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
        gb.configure_side_bar()
        gb.configure_default_column(filterable=True, sorteable=True, resizable=True, editable=True)
        gb.configure_selection('multiple', use_checkbox=True, pre_selected_rows=[])
        
        # Special column configurations
        if 'id' in aggrid_df.columns:
            gb.configure_column("id", header_name="ID", width=80, pinned='left', editable=False)
        if 'des_num' in aggrid_df.columns:
            gb.configure_column("des_num", header_name="Nº Desenho", width=150, pinned='left')
        if 'layout_name' in aggrid_df.columns:
            gb.configure_column("layout_name", header_name="Layout", width=200)
        if 'tipo_display' in aggrid_df.columns:
            gb.configure_column("tipo_display", header_name="Tipo", width=150)
        if 'elemento' in aggrid_df.columns:
            gb.configure_column("elemento", header_name="Elemento", width=150)
        if 'titulo' in aggrid_df.columns:
            gb.configure_column("titulo", header_name="Título", width=250)
        if 'r' in aggrid_df.columns:
            gb.configure_column("r", header_name="Rev", width=80)
        if 'r_data' in aggrid_df.columns:
            gb.configure_column("r_data", header_name="Data Rev", width=120)
        if 'estado_interno' in aggrid_df.columns:
            # Use dropdown for estado_interno
            gb.configure_column("estado_interno", header_name="Estado", width=150, 
                              cellEditor='agSelectCellEditor',
                              cellEditorParams={'values': ['projeto', 'needs_revision', 'built']})
        if 'comentario' in aggrid_df.columns:
            gb.configure_column("comentario", header_name="Comentário", width=250)
        if 'data_limite' in aggrid_df.columns:
            gb.configure_column("data_limite", header_name="Data Limite", width=120)
        if 'responsavel' in aggrid_df.columns:
            gb.configure_column("responsavel", header_name="Responsável", width=150)
        if 'dwg_name' in aggrid_df.columns:
            gb.configure_column("dwg_name", header_name="DWG", width=150)
        if 'dwg_source' in aggrid_df.columns:
            gb.configure_column("dwg_source", header_name="DWG Source", width=150)
        if 'proj_num' in aggrid_df.columns:
            gb.configure_column("proj_num", header_name="Proj Nº", width=100)
        if 'proj_nome' in aggrid_df.columns:
            gb.configure_column("proj_nome", header_name="Projeto", width=200)
        
        gridOptions = gb.build()
        
        # Render AgGrid
        grid_response = AgGrid(
            aggrid_df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=False,
            theme='streamlit',
            height=500,
            allow_unsafe_jscode=True,
            reload_data=False
        )
        
        # Save Changes Button
        st.markdown("---")
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        
        with col_save1:
            if st.button("💾 Guardar Alterações", type="primary", use_container_width=True):
                if grid_response['data'] is not None:
                    edited_df = pd.DataFrame(grid_response['data'])
                    
                    # Compare with original and update database
                    changes_made = 0
                    errors = []
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    try:
                        for idx, row in edited_df.iterrows():
                            if 'id' in row and pd.notna(row['id']):
                                desenho_id = int(row['id'])
                                
                                # Build update dict with all editable fields
                                update_fields = {}
                                for col in edited_df.columns:
                                    if col != 'id' and col != 'estado_interno_display':
                                        value = row[col]
                                        # Convert NaN to None
                                        if pd.isna(value):
                                            update_fields[col] = None
                                        else:
                                            update_fields[col] = str(value) if value is not None else None
                                
                                # Build UPDATE query dynamically
                                if update_fields:
                                    set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
                                    values = list(update_fields.values()) + [desenho_id]
                                    
                                    query = f"UPDATE desenhos SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                                    cursor.execute(query, values)
                                    changes_made += 1
                        
                        conn.commit()
                        st.success(f"✅ {changes_made} desenho(s) atualizado(s) com sucesso!")
                        
                        # Update original data
                        st.session_state['original_data'] = edited_df.copy()
                        
                        # Refresh page
                        st.rerun()
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Erro ao guardar alterações: {e}")
                        errors.append(str(e))
                    finally:
                        conn.close()
                else:
                    st.warning("⚠️ Nenhum dado para guardar")
        
        with col_save2:
            st.caption("💡 Edite as células diretamente na tabela e clique em 'Guardar Alterações'")
        
        with col_save3:
            if st.button("🔄 Recarregar Dados", use_container_width=True):
                if 'original_data' in st.session_state:
                    del st.session_state['original_data']
                st.rerun()

        
        # Handle selection
        selected_rows = grid_response['selected_rows']
        if selected_rows is not None and len(selected_rows) > 0:
            st.markdown("---")
            st.subheader(f"📋 Detalhes do Desenho Selecionado")
            selected = selected_rows.iloc[0] if isinstance(selected_rows, pd.DataFrame) else selected_rows[0]
            
            # Find original row in df to get ID
            layout = selected.get('layout_name', '')
            original_row = filtered_df[filtered_df['layout_name'] == layout]
            
            if not original_row.empty:
                desenho_id = original_row.iloc[0].get('id')
                
                if desenho_id:
                    conn = get_connection()
                    desenho = get_desenho_by_id(conn, desenho_id)
                    revisoes = get_revisoes_by_desenho_id(conn, desenho_id)
                    conn.close()
                    
                    if desenho:
                        col_info, col_edit = st.columns([1, 1])
                        
                        with col_info:
                            st.markdown("**📐 Informação:**")
                            st.text(f"Layout: {desenho.get('layout_name', '-')}")
                            st.text(f"DES_NUM: {desenho.get('des_num', '-')}")
                            st.text(f"Tipo: {desenho.get('tipo_display', '-')}")
                            st.text(f"Elemento: {desenho.get('elemento_key', '-')}")
                            st.text(f"Título: {desenho.get('titulo', '-')}")
                            st.text(f"Revisão: {desenho.get('r', '-')}")
                            st.text(f"DWG: {desenho.get('dwg_name', '-')}")
                        
                        with col_edit:
                            st.markdown("**✏️ Editar Estado:**")
                            
                            estado_atual = desenho.get('estado_interno') or 'projeto'
                            estado_options = ['projeto', 'needs_revision', 'built']
                            estado_labels = {e: ESTADO_CONFIG[e]['label'] for e in estado_options}
                            
                            novo_estado = st.selectbox(
                                "Estado:",
                                estado_options,
                                index=estado_options.index(estado_atual),
                                format_func=lambda x: estado_labels[x],
                                key=f"edit_estado_{desenho_id}"
                            )
                            
                            novo_comentario = st.text_area(
                                "Comentário:",
                                value=desenho.get('comentario') or '',
                                height=100,
                                key=f"edit_comentario_{desenho_id}"
                            )
                            
                            if st.button("💾 Guardar", type="primary", use_container_width=True):
                                conn = get_connection()
                                success = update_estado_e_comentario(
                                    conn, desenho_id,
                                    estado=novo_estado,
                                    comentario=novo_comentario,
                                    data_limite=None,
                                    responsavel=None,
                                    autor="Streamlit User"
                                )
                                conn.close()
                                if success:
                                    st.success("✅ Guardado!")
                                    st.rerun()
        
        # Export button
        st.markdown("---")
        csv_export = aggrid_df.to_csv(sep=';', index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download CSV Filtrado",
            data=csv_export,
            file_name=f"desenhos_filtrados_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ========================================
# PAGE: HISTÓRICO
# ========================================
elif selected_page == "Histórico":
    st.title("📜 Histórico de Revisões")
    
    conn = get_connection()
    datas_unicas = get_unique_revision_dates(conn)
    conn.close()
    
    if not datas_unicas:
        st.warning("⚠️ Nenhuma data de revisão encontrada na base de dados.")
    else:
        col_date, col_info = st.columns([2, 3])
        
        with col_date:
            data_selecionada = st.selectbox(
                "📅 Selecione uma data:",
                datas_unicas,
                key="historico_data"
            )
        
        with col_info:
            st.info(f"💡 {len(datas_unicas)} datas com revisões registadas")
        
        if data_selecionada:
            st.markdown("---")
            colored_header(
                label=f"Estado em {data_selecionada}",
                description=f"Desenhos registados nesta data",
                color_name="green-70"
            )
            
            conn = get_connection()
            desenhos_na_data = get_desenhos_at_date(conn, data_selecionada)
            conn.close()
            
            if not desenhos_na_data:
                st.warning(f"⚠️ Nenhum desenho encontrado para {data_selecionada}")
            else:
                df_hist = pd.DataFrame(desenhos_na_data)
                
                # Stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Desenhos", len(df_hist))
                with col2:
                    tipos_unicos = df_hist['tipo_display'].nunique() if 'tipo_display' in df_hist.columns else 0
                    st.metric("Tipos Únicos", tipos_unicos)
                with col3:
                    revisoes = df_hist['r'].value_counts().to_dict() if 'r' in df_hist.columns else {}
                    rev_info = ", ".join([f"{k}:{v}" for k, v in revisoes.items() if k and k != '-'])
                    st.metric("Revisões", rev_info if rev_info else "-")
                
                style_metric_cards()
                
                st.markdown("---")
                
                # Display with AgGrid
                hist_columns = ['des_num', 'layout_name', 'tipo_display', 'elemento', 'titulo', 'r', 'r_data', 'r_desc', 'dwg_name']
                hist_df = df_hist[[c for c in hist_columns if c in df_hist.columns]]
                
                gb_hist = GridOptionsBuilder.from_dataframe(hist_df)
                gb_hist.configure_pagination(paginationPageSize=20)
                gb_hist.configure_side_bar()
                gb_hist.configure_default_column(filterable=True, sorteable=True)
                
                AgGrid(
                    hist_df,
                    gridOptions=gb_hist.build(),
                    height=400,
                    theme='streamlit'
                )
                
                # Export
                csv_hist = hist_df.to_csv(sep=';', index=False).encode('utf-8-sig')
                st.download_button(
                    label=f"📥 Download CSV ({data_selecionada})",
                    data=csv_hist,
                    file_name=f"historico_{data_selecionada.replace('-', '_')}.csv",
                    mime="text/csv"
                )

# ========================================
# PAGE: CONFIGURAÇÕES
# ========================================
elif selected_page == "Configurações":
    st.title("⚙️ Configurações e Operações")
    
    tab1, tab2, tab3 = st.tabs(["📥 Importar Dados", "📊 Gerar LPP", "🗑️ Gestão DB"])
    
    # TAB 1: Import
    with tab1:
        colored_header(
            label="Importar Dados",
            description="Importe ficheiros JSON ou CSV para a base de dados",
            color_name="blue-70"
        )
        
        col_imp1, col_imp2 = st.columns(2)
        
        with col_imp1:
            st.subheader("JSON Files")
            if st.button("📥 Importar JSON", use_container_width=True, type="primary"):
                with st.spinner("Importando JSON..."):
                    try:
                        conn = get_connection()
                        stats = import_all_json("data/json_in", conn)
                        conn.close()
                        st.success(
                            f"✅ Importação JSON concluída!\n\n"
                            f"Ficheiros: {stats['files_processed']}\n"
                            f"Desenhos: {stats['desenhos_imported']}"
                        )
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
        
        with col_imp2:
            st.subheader("CSV Files")
            if st.button("📄 Importar CSV", use_container_width=True, type="primary"):
                with st.spinner("Importando CSV..."):
                    try:
                        conn = get_connection()
                        stats = import_all_csv("data/csv_in", conn)
                        conn.close()
                        st.success(
                            f"✅ Importação CSV concluída!\n\n"
                            f"Ficheiros: {stats['files_processed']}\n"
                            f"Desenhos: {stats['desenhos_imported']}"
                        )
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
        
        st.markdown("---")
        
        # Upload CSV directly with project selection
        st.subheader("📤 Upload CSV com Seleção de Projeto")
        uploaded_csv = st.file_uploader("Escolha um ficheiro CSV", type=['csv'], key="csv_uploader_main")
        
        if uploaded_csv is not None:
            # Initialize session state for CSV import if not exists
            if 'csv_import_mode' not in st.session_state:
                st.session_state['csv_import_mode'] = None
            if 'csv_target_project' not in st.session_state:
                st.session_state['csv_target_project'] = None
            
            st.info(f"**Ficheiro selecionado:** {uploaded_csv.name}")
            
            # Project selection
            st.markdown("### 📂 Escolha o Projeto")
            
            col_mode1, col_mode2 = st.columns(2)
            
            with col_mode1:
                if st.button("🆕 Criar Novo Projeto", use_container_width=True, 
                            type="primary" if st.session_state.get('csv_import_mode') == 'new' else "secondary"):
                    st.session_state['csv_import_mode'] = 'new'
                    st.rerun()
            
            with col_mode2:
                if st.button("📁 Adicionar a Projeto Existente", use_container_width=True,
                            type="primary" if st.session_state.get('csv_import_mode') == 'existing' else "secondary"):
                    st.session_state['csv_import_mode'] = 'existing'
                    st.rerun()
            
            # Show appropriate options based on mode
            if st.session_state.get('csv_import_mode') == 'new':
                st.success("✓ Modo: **Criar Novo Projeto**")
                st.caption("Os dados do projeto serão extraídos automaticamente do CSV (PROJ_NUM, PROJ_NOME, CLIENTE, etc.)")
                
                if st.button("➕ Importar e Criar Projeto", type="primary", use_container_width=True, key="btn_import_new"):
                    temp_path = Path("data/csv_in") / uploaded_csv.name
                    temp_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_csv.getbuffer())
                    
                    with st.spinner(f"Importando {uploaded_csv.name} e criando projeto..."):
                        try:
                            conn = get_connection()
                            stats = import_single_csv(str(temp_path), conn, target_proj_num=None)
                            conn.close()
                            st.success(f"✅ Importado! Desenhos: {stats['desenhos_imported']}")
                            # Reset state
                            st.session_state['csv_import_mode'] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
            
            elif st.session_state.get('csv_import_mode') == 'existing':
                st.success("✓ Modo: **Adicionar a Projeto Existente**")
                
                # Get list of existing projects
                conn = get_connection()
                projetos = get_all_projetos(conn)
                conn.close()
                
                if not projetos:
                    st.warning("⚠️ Nenhum projeto existente. Crie um projeto primeiro ou use 'Criar Novo Projeto'.")
                else:
                    projeto_options = [f"{p['proj_num']} - {p['proj_nome']}" for p in projetos]
                    selected_projeto = st.selectbox(
                        "Selecione o projeto:",
                        projeto_options,
                        key="csv_target_project_select"
                    )
                    
                    if selected_projeto:
                        target_proj_num = selected_projeto.split(' - ')[0]
                        st.caption(f"Os desenhos do CSV serão associados ao projeto **{target_proj_num}**")
                        
                        if st.button("➕ Importar para Projeto", type="primary", use_container_width=True, key="btn_import_existing"):
                            temp_path = Path("data/csv_in") / uploaded_csv.name
                            temp_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(temp_path, 'wb') as f:
                                f.write(uploaded_csv.getbuffer())
                            
                            with st.spinner(f"Importando {uploaded_csv.name} para projeto {target_proj_num}..."):
                                try:
                                    conn = get_connection()
                                    stats = import_single_csv(str(temp_path), conn, target_proj_num=target_proj_num)
                                    conn.close()
                                    st.success(f"✅ Importado para projeto {target_proj_num}! Desenhos: {stats['desenhos_imported']}")
                                    # Reset state
                                    st.session_state['csv_import_mode'] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {e}")
            else:
                st.info("💡 Escolha um modo acima para continuar")
    
    # TAB 2: Generate LPP
    with tab2:
        colored_header(
            label="Gerar LPP",
            description="Gere ficheiro Excel LPP a partir da base de dados",
            color_name="green-70"
        )
        
        uploaded_template = st.file_uploader("📋 Upload Template LPP (Excel)", type=['xlsx', 'xls'])
        
        if uploaded_template is not None:
            template_path = Path("data") / "LPP_TEMPLATE.xlsx"
            template_path.parent.mkdir(parents=True, exist_ok=True)
            with open(template_path, 'wb') as f:
                f.write(uploaded_template.getbuffer())
            st.success("✅ Template carregado!")
        
        template_path = Path("data/LPP_TEMPLATE.xlsx")
        template_exists = template_path.exists()
        
        if not template_exists:
            st.warning("⚠️ Faça upload do template LPP primeiro")
        
        if st.button("📊 Gerar LPP.xlsx", use_container_width=True, type="primary", disabled=not template_exists):
            output_path = "output/LPP.xlsx"
            Path("output").mkdir(parents=True, exist_ok=True)
            
            with st.spinner("Gerando LPP.xlsx..."):
                try:
                    conn = get_connection()
                    build_lpp_from_db(str(template_path), output_path, conn)
                    conn.close()
                    st.success(f"✅ LPP gerado! Ficheiro: {output_path}")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
    
    # TAB 3: DB Management
    with tab3:
        colored_header(
            label="Gestão da Base de Dados",
            description="Elimine dados ou visualize estatísticas",
            color_name="red-70"
        )
        
        conn = get_connection()
        db_stats = get_db_stats(conn)
        conn.close()
        
        col_db1, col_db2 = st.columns(2)
        
        with col_db1:
            st.metric("Total Desenhos", db_stats['total_desenhos'])
            st.metric("Total DWGs", db_stats['total_dwgs'])
        
        with col_db2:
            if db_stats['dwg_list']:
                dwg_info = ", ".join([f"{d['dwg_name']}({d['count']})" for d in db_stats['dwg_list']])
                st.info(f"📁 **DWGs:** {dwg_info}")
        
        style_metric_cards()
        
        if db_stats['total_desenhos'] > 0:
            st.markdown("---")
            st.warning("**🗑️ Opções de Limpeza (CUIDADO!)**")
            
            delete_type = st.selectbox(
                "Apagar por:",
                ["Escolher...", "Tudo", "Por DWG", "Por Tipo", "Por Elemento"],
                key="config_delete_type"
            )
            
            if delete_type == "Tudo":
                if st.button("⚠️ Apagar TODA a DB", type="secondary"):
                    st.session_state['confirm_delete_config'] = 'all'
            
            elif delete_type == "Por DWG":
                conn = get_connection()
                dwg_list = [d['dwg_name'] for d in get_dwg_list(conn)]
                conn.close()
                if dwg_list:
                    selected_dwg = st.selectbox("DWG:", dwg_list, key="config_del_dwg")
                    if st.button(f"🗑️ Apagar {selected_dwg}"):
                        st.session_state['confirm_delete_config'] = ('dwg', selected_dwg)
            
            # Confirmation
            if st.session_state.get('confirm_delete_config'):
                delete_info = st.session_state['confirm_delete_config']
                
                if delete_info == 'all':
                    st.error(f"⚠️ Apagar TODOS os {db_stats['total_desenhos']} desenhos?")
                elif delete_info[0] == 'dwg':
                    st.error(f"⚠️ Apagar DWG '{delete_info[1]}'?")
                
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Confirmar", key="config_yes"):
                        conn = get_connection()
                        deleted = 0
                        
                        if delete_info == 'all':
                            deleted = delete_all_desenhos(conn)
                        elif delete_info[0] == 'dwg':
                            deleted = delete_desenhos_by_dwg(conn, delete_info[1])
                        
                        conn.close()
                        st.session_state['confirm_delete_config'] = None
                        st.success(f"✅ {deleted} desenho(s) apagado(s)")
                        st.rerun()
                
                with col_no:
                    if st.button("❌ Cancelar", key="config_no"):
                        st.session_state['confirm_delete_config'] = None
                        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "JSJ Engenharia - Sistema de Gestão de Desenhos | Enhanced UI v3.0"
    "</div>",
    unsafe_allow_html=True
)
