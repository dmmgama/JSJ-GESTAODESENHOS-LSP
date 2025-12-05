"""
Streamlit app - UI for JSJ Drawing Management LPP Sync (Enhanced Version).
"""
import streamlit as st
import pandas as pd
import time
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
    get_unique_revision_dates, get_desenhos_at_date,
    delete_desenho_by_id, delete_desenhos_by_ids, delete_desenhos_by_projeto_and_dwg_source,
    delete_desenhos_by_projeto_and_pfix, delete_all_desenhos_by_projeto
)
from db_projects import (
    get_all_projetos, get_projeto_by_num, upsert_projeto, delete_projeto,
    get_desenhos_by_projeto, get_projeto_stats, get_unique_dwg_sources,
    inicializar_multiproject
)
from json_importer import import_all_json
from csv_importer import import_all_csv, import_single_csv
from lpp_builder import build_lpp_from_db
import io

# ========================================
# CSV EXPORT FUNCTION
# ========================================
CSV_EXPORT_HEADERS = [
    'PROJ_NUM', 'PROJ_NOME', 'CLIENTE', 'OBRA', 'LOCALIZACAO', 'ESPECIALIDADE', 
    'PROJETOU', 'FASE', 'FASE_PFIX', 'EMISSAO', 'DATA', 'PFIX', 'LAYOUT', 
    'DES_NUM', 'TIPO', 'ELEMENTO', 'TITULO', 'REV_A', 'DATA_A', 'DESC_A', 
    'REV_B', 'DATA_B', 'DESC_B', 'REV_C', 'DATA_C', 'DESC_C', 'REV_D', 
    'DATA_D', 'DESC_D', 'REV_E', 'DATA_E', 'DESC_E', 'DWG_SOURCE', 'ID_CAD'
]

def export_desenhos_to_csv(desenhos_with_revisoes: list, proj_num: str = None) -> str:
    """
    Export desenhos to CSV string in the standard format.
    
    Args:
        desenhos_with_revisoes: List of desenho dicts with revision fields expanded
        proj_num: Project number (for filename, optional)
    
    Returns:
        CSV content as string
    """
    lines = [';'.join(CSV_EXPORT_HEADERS)]
    
    for d in desenhos_with_revisoes:
        row = [
            d.get('proj_num', '') or '',
            d.get('proj_nome', '') or '',
            d.get('cliente', '') or '',
            d.get('obra', '') or '',
            d.get('localizacao', '') or '',
            d.get('especialidade', '') or '',
            d.get('projetou', '') or '',
            d.get('fase', '') or '',
            d.get('fase_pfix', '') or '',
            d.get('emissao', '') or '',
            d.get('data', '') or '',
            d.get('pfix', '') or '',
            d.get('layout_name', '') or '',
            d.get('des_num', '') or '',
            d.get('tipo_display', '') or '',
            d.get('elemento', '') or '',
            d.get('titulo', '') or '',
            d.get('rev_a', '') or '',
            d.get('data_a', '') or '',
            d.get('desc_a', '') or '',
            d.get('rev_b', '') or '',
            d.get('data_b', '') or '',
            d.get('desc_b', '') or '',
            d.get('rev_c', '') or '',
            d.get('data_c', '') or '',
            d.get('desc_c', '') or '',
            d.get('rev_d', '') or '',
            d.get('data_d', '') or '',
            d.get('desc_d', '') or '',
            d.get('rev_e', '') or '',
            d.get('data_e', '') or '',
            d.get('desc_e', '') or '',
            d.get('dwg_source', '') or '',
            d.get('id_cad', '') or ''
        ]
        lines.append(';'.join(str(v) for v in row))
    
    return '\n'.join(lines)


def get_desenhos_by_dwg_source_with_revisoes(conn, dwg_source: str) -> list:
    """Get desenhos for a specific DWG source with revisions expanded."""
    from db import get_desenho_with_revisoes
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id FROM desenhos d
        WHERE d.dwg_source = ?
        ORDER BY d.des_num
    """, (dwg_source,))
    
    result = []
    for row in cursor.fetchall():
        desenho = get_desenho_with_revisoes(conn, row[0])
        if desenho:
            result.append(desenho)
    
    return result


def get_all_desenhos_with_revisoes_sorted(conn) -> list:
    """Get all desenhos with revisions, sorted by DWG_SOURCE."""
    from db import get_desenho_with_revisoes
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id FROM desenhos d
        ORDER BY d.dwg_source, d.des_num
    """)
    
    result = []
    for row in cursor.fetchall():
        desenho = get_desenho_with_revisoes(conn, row[0])
        if desenho:
            result.append(desenho)
    
    return result


# Estado interno options and configuration
ESTADO_OPTIONS = [
    "Desenvolvimento de Projeto",
    "Emissão de Projeto",
    "Precisa Revisão",
    "Construído",
    "Em Atraso"
]

ESTADO_DEFAULT = "Emissão de Projeto"

# Estado interno colors and labels
ESTADO_CONFIG = {
    'Desenvolvimento de Projeto': {'label': '🔧 Desenvolvimento de Projeto', 'color': '#6c757d', 'bg': '#f8f9fa'},
    'Emissão de Projeto': {'label': '📋 Emissão de Projeto', 'color': '#17a2b8', 'bg': '#d1ecf1'},
    'Precisa Revisão': {'label': '⚠️ Precisa Revisão', 'color': '#ffc107', 'bg': '#fff3cd'},
    'Construído': {'label': '✅ Construído', 'color': '#28a745', 'bg': '#d4edda'},
    'Em Atraso': {'label': '🚨 Em Atraso', 'color': '#dc3545', 'bg': '#f8d7da'}
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
    col_mode1, col_mode2, col_mode3, col_mode4, col_mode5 = st.columns([1, 1, 1, 1, 1])
    with col_mode1:
        if st.button("📋 Listar Projetos", use_container_width=True, type="primary" if st.session_state.get('projetos_mode', 'list') == 'list' else "secondary"):
            st.session_state['projetos_mode'] = 'list'
            st.rerun()
    with col_mode2:
        # Show current active project info or prompt to select
        projeto_ativo_atual = st.session_state.get('projeto_ativo')
        if projeto_ativo_atual:
            st.button(f"📂 Ativo: {projeto_ativo_atual}", use_container_width=True, type="primary", disabled=True)
        else:
            st.button("⚠️ Nenhum Ativo", use_container_width=True, type="secondary", disabled=True)
    with col_mode3:
        if st.button("➕ Novo Projeto", use_container_width=True, type="primary" if st.session_state.get('projetos_mode') == 'create' else "secondary"):
            st.session_state['projetos_mode'] = 'create'
            st.rerun()
    with col_mode4:
        if st.button("✏️ Editar Projeto", use_container_width=True, type="primary" if st.session_state.get('projetos_mode') == 'edit' else "secondary"):
            st.session_state['projetos_mode'] = 'edit'
            st.rerun()
    with col_mode5:
        if st.button("🗑️ Apagar Projeto", use_container_width=True, type="primary" if st.session_state.get('projetos_mode') == 'delete' else "secondary"):
            st.session_state['projetos_mode'] = 'delete'
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
                    'PROJ_NOME': p['proj_nome'] or '-',
                    'CLIENTE': p['cliente'] or '-',
                    'OBRA': p['obra'] or '-',
                    'DESENHOS': stats['total_desenhos'],
                    'DWGs': stats['dwg_sources_count']
                })
            
            df_projetos = pd.DataFrame(projeto_data)
            
            # Display with AgGrid - with checkbox for selection
            gb = GridOptionsBuilder.from_dataframe(df_projetos)
            gb.configure_selection('single', use_checkbox=True, pre_selected_rows=[])
            gb.configure_default_column(filterable=True, sorteable=True, resizable=True)
            gb.configure_pagination(paginationPageSize=20)
            gb.configure_column("PROJ_NUM", header_name="PROJ_NUM", width=100, pinned='left')
            gb.configure_column("PROJ_NOME", header_name="PROJ_NOME", width=250)
            gb.configure_column("CLIENTE", header_name="CLIENTE", width=200)
            gb.configure_column("OBRA", header_name="OBRA", width=200)
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
            
            # Selection handler
            selected_rows = grid_response['selected_rows']
            if selected_rows is not None and len(selected_rows) > 0:
                selected = selected_rows.iloc[0] if isinstance(selected_rows, pd.DataFrame) else selected_rows[0]
                proj_num = selected['PROJ_NUM']
                
                # Store selection for reference
                st.session_state['projeto_selecionado_para_ativar'] = proj_num
                
                col_sel1, col_sel2 = st.columns([3, 1])
                with col_sel1:
                    st.success(f"**✓ Selecionado:** {proj_num} - {selected['PROJ_NOME']}")
                with col_sel2:
                    if st.button("✅ Ativar Este Projeto", type="primary", use_container_width=True, key="btn_ativar_selecionado"):
                        st.session_state['projeto_ativo'] = proj_num
                        st.session_state['projeto_selecionado_para_ativar'] = None
                        st.success(f"Projeto {proj_num} ativado!")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.session_state['projeto_selecionado_para_ativar'] = None
                st.warning("⚠️ Nenhum projeto selecionado. Clique numa linha da tabela acima.")
    
    # EDIT MODE
    elif st.session_state.get('projetos_mode') == 'edit':
        st.markdown("### ✏️ Editar Dados de Projeto")
        
        conn = get_connection()
        projetos = get_all_projetos(conn)
        conn.close()
        
        if not projetos:
            st.warning("⚠️ Nenhum projeto disponível para editar.")
        else:
            # Select project to edit
            projeto_options = [f"{p['proj_num']} - {p['proj_nome'] or 'Sem nome'}" for p in projetos]
            selected_projeto_label = st.selectbox("Selecione o Projeto a Editar:", projeto_options)
            
            if selected_projeto_label:
                selected_proj_num = selected_projeto_label.split(" - ")[0]
                
                # Get current project data
                conn = get_connection()
                projeto = get_projeto_by_num(conn, selected_proj_num)
                stats = get_projeto_stats(conn, selected_proj_num)
                conn.close()
                
                if projeto:
                    st.info(f"📊 Este projeto tem **{stats['total_desenhos']} desenhos** associados.")
                    
                    with st.form("edit_projeto"):
                        st.markdown("#### Dados do Projeto")
                        st.caption("⚠️ PROJ_NUM é o identificador único e não pode ser alterado.")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.text_input("PROJ_NUM", value=projeto['proj_num'], disabled=True, help="Identificador único do projeto - não editável")
                            edit_proj_nome = st.text_input("PROJ_NOME", value=projeto['proj_nome'] or '', help="Nome do projeto")
                            edit_cliente = st.text_input("CLIENTE", value=projeto['cliente'] or '', help="Nome do cliente")
                            edit_obra = st.text_input("OBRA", value=projeto['obra'] or '', help="Nome da obra")
                        
                        with col2:
                            edit_localizacao = st.text_input("LOCALIZAÇÃO", value=projeto['localizacao'] or '')
                            edit_especialidade = st.text_input("ESPECIALIDADE", value=projeto['especialidade'] or '')
                            edit_projetou = st.text_input("PROJETOU", value=projeto['projetou'] or '')
                        
                        col_submit1, col_submit2 = st.columns([1, 3])
                        with col_submit1:
                            submitted = st.form_submit_button("💾 Atualizar DB", type="primary", use_container_width=True)
                        with col_submit2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state['projetos_mode'] = 'list'
                                st.rerun()
                        
                        if submitted:
                            # Update project data
                            projeto_data = {
                                'proj_num': selected_proj_num,
                                'proj_nome': edit_proj_nome,
                                'cliente': edit_cliente,
                                'obra': edit_obra,
                                'localizacao': edit_localizacao,
                                'especialidade': edit_especialidade,
                                'projetou': edit_projetou
                            }
                            
                            try:
                                conn = get_connection()
                                upsert_projeto(conn, projeto_data)
                                conn.close()
                                
                                st.success(f"✅ Projeto {selected_proj_num} atualizado com sucesso!")
                                st.session_state['projetos_mode'] = 'list'
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar projeto: {e}")
    
    # DELETE MODE
    elif st.session_state.get('projetos_mode') == 'delete':
        st.markdown("### 🗑️ Apagar Projeto")
        st.warning("⚠️ **ATENÇÃO:** Apagar um projeto irá remover **TODOS os desenhos** associados a esse projeto da base de dados!")
        
        conn = get_connection()
        projetos = get_all_projetos(conn)
        conn.close()
        
        if not projetos:
            st.info("ℹ️ Nenhum projeto disponível para apagar.")
        else:
            # Select project to delete
            projeto_options = ["-- Selecione --"] + [f"{p['proj_num']} - {p['proj_nome'] or 'Sem nome'}" for p in projetos]
            selected_projeto_label = st.selectbox("Selecione o Projeto a Apagar:", projeto_options, key="delete_projeto_select")
            
            if selected_projeto_label and selected_projeto_label != "-- Selecione --":
                selected_proj_num = selected_projeto_label.split(" - ")[0]
                
                # Get project stats
                conn = get_connection()
                projeto = get_projeto_by_num(conn, selected_proj_num)
                stats = get_projeto_stats(conn, selected_proj_num)
                conn.close()
                
                if projeto:
                    st.markdown("---")
                    st.markdown("#### 📋 Dados do Projeto Selecionado:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**PROJ_NUM:** {projeto['proj_num']}")
                        st.markdown(f"**PROJ_NOME:** {projeto['proj_nome'] or '-'}")
                        st.markdown(f"**CLIENTE:** {projeto['cliente'] or '-'}")
                        st.markdown(f"**OBRA:** {projeto['obra'] or '-'}")
                    with col2:
                        st.markdown(f"**LOCALIZAÇÃO:** {projeto['localizacao'] or '-'}")
                        st.markdown(f"**ESPECIALIDADE:** {projeto['especialidade'] or '-'}")
                        st.markdown(f"**PROJETOU:** {projeto['projetou'] or '-'}")
                    
                    st.markdown("---")
                    st.error(f"🚨 **Serão apagados {stats['total_desenhos']} desenhos** de {stats['dwg_sources_count']} ficheiros DWG!")
                    
                    # Confirmation
                    confirm_text = st.text_input(
                        f"Para confirmar, escreva o PROJ_NUM: **{selected_proj_num}**",
                        help="Escreva o número do projeto para confirmar a eliminação"
                    )
                    
                    col_del1, col_del2 = st.columns([1, 3])
                    with col_del1:
                        if st.button("🗑️ APAGAR PROJETO", type="primary", use_container_width=True, disabled=(confirm_text != selected_proj_num)):
                            try:
                                conn = get_connection()
                                result = delete_projeto(conn, selected_proj_num, delete_desenhos=True)
                                conn.close()
                                
                                if result['success']:
                                    st.success(f"✅ Projeto {selected_proj_num} e {result['desenhos_deleted']} desenhos apagados com sucesso!")
                                    # Clear active project if it was the deleted one
                                    if st.session_state.get('projeto_ativo') == selected_proj_num:
                                        st.session_state['projeto_ativo'] = None
                                    st.session_state['projetos_mode'] = 'list'
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
                            except Exception as e:
                                st.error(f"❌ Erro ao apagar projeto: {e}")
                    with col_del2:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state['projetos_mode'] = 'list'
                            st.rerun()
                    
                    if confirm_text and confirm_text != selected_proj_num:
                        st.warning("⚠️ O texto introduzido não corresponde ao PROJ_NUM.")
    
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
            df['estado_interno'] = ESTADO_DEFAULT
        df['estado_interno'] = df['estado_interno'].fillna(ESTADO_DEFAULT)
        
        # Auto-update to "Em Atraso" if data_limite is past
        today = date.today()
        if 'data_limite' in df.columns:
            for idx, row in df.iterrows():
                data_limite_val = row.get('data_limite')
                if data_limite_val and pd.notna(data_limite_val) and data_limite_val != '':
                    try:
                        # Parse date in DD-MM-YYYY format
                        if isinstance(data_limite_val, str) and '-' in data_limite_val:
                            parts = data_limite_val.split('-')
                            if len(parts) == 3:
                                if len(parts[0]) == 4:  # YYYY-MM-DD
                                    dt = date(int(parts[0]), int(parts[1]), int(parts[2]))
                                else:  # DD-MM-YYYY
                                    dt = date(int(parts[2]), int(parts[1]), int(parts[0]))
                                if dt < today and row.get('estado_interno') != 'Em Atraso':
                                    df.at[idx, 'estado_interno'] = 'Em Atraso'
                    except (ValueError, TypeError):
                        pass
        
        # Top metrics with styled cards - recalculate from df after Em Atraso auto-update
        estado_counts_dash = df['estado_interno'].value_counts()
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total Desenhos", len(df), delta=None)
        with col2:
            st.metric("🔧 Desenvolvimento", estado_counts_dash.get('Desenvolvimento de Projeto', 0))
        with col3:
            st.metric("📋 Emissão", estado_counts_dash.get('Emissão de Projeto', 0))
        with col4:
            st.metric("⚠️ Precisa Revisão", estado_counts_dash.get('Precisa Revisão', 0))
        with col5:
            st.metric("✅ Construído", estado_counts_dash.get('Construído', 0))
        with col6:
            em_atraso = estado_counts_dash.get('Em Atraso', 0)
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
            if 'dwg_source' in df.columns:
                dwg_counts = df['dwg_source'].value_counts()
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
            df['estado_interno'] = ESTADO_DEFAULT
        df['estado_interno'] = df['estado_interno'].fillna(ESTADO_DEFAULT)
        
        # Auto-update to "Em Atraso" if data_limite is past and persist to DB
        today = date.today()
        ids_to_update_atraso = []
        if 'data_limite' in df.columns:
            for idx, row in df.iterrows():
                data_limite_val = row.get('data_limite')
                if data_limite_val and pd.notna(data_limite_val) and data_limite_val != '':
                    try:
                        # Parse date in DD-MM-YYYY or YYYY-MM-DD format
                        if isinstance(data_limite_val, str) and '-' in data_limite_val:
                            parts = data_limite_val.split('-')
                            if len(parts) == 3:
                                if len(parts[0]) == 4:  # YYYY-MM-DD
                                    dt = date(int(parts[0]), int(parts[1]), int(parts[2]))
                                else:  # DD-MM-YYYY
                                    dt = date(int(parts[2]), int(parts[1]), int(parts[0]))
                                if dt < today and row.get('estado_interno') != 'Em Atraso':
                                    df.at[idx, 'estado_interno'] = 'Em Atraso'
                                    if 'id' in row and pd.notna(row['id']):
                                        ids_to_update_atraso.append(int(row['id']))
                    except (ValueError, TypeError):
                        pass
        
        # Persist "Em Atraso" updates to database
        if ids_to_update_atraso:
            conn = get_connection()
            cursor = conn.cursor()
            for desenho_id in ids_to_update_atraso:
                cursor.execute("UPDATE desenhos SET estado_interno = 'Em Atraso', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (desenho_id,))
            conn.commit()
            conn.close()
        
        # Recalculate estado stats after auto-update
        estado_counts = df['estado_interno'].value_counts()
        
        # Quick stats
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total", len(df))
        with col2:
            st.metric("🔧 Desenvolvimento", estado_counts.get('Desenvolvimento de Projeto', 0))
        with col3:
            st.metric("📋 Emissão", estado_counts.get('Emissão de Projeto', 0))
        with col4:
            st.metric("⚠️ Precisa Revisão", estado_counts.get('Precisa Revisão', 0))
        with col5:
            st.metric("✅ Construído", estado_counts.get('Construído', 0))
        with col6:
            st.metric("🚨 Em Atraso", estado_counts.get('Em Atraso', 0))
        
        style_metric_cards()
        
        st.markdown("---")
        
        # Filters
        st.markdown("### 🔍 Filtros")
        
        # Check if project is active - filter data by active project
        projeto_ativo = st.session_state.get('projeto_ativo')
        if not projeto_ativo:
            st.warning("⚠️ Nenhum projeto ativo. Selecione um projeto no menu 'Projetos' para ver os desenhos.")
            st.stop()
        
        # Filter df by active project
        if 'proj_num' in df.columns:
            df = df[df['proj_num'] == projeto_ativo]
        
        if df.empty:
            st.warning(f"⚠️ Nenhum desenho encontrado para o projeto {projeto_ativo}.")
            st.stop()
        
        # Get DWG sources for active project only
        conn = get_connection()
        dwg_sources_proj = get_unique_dwg_sources(conn, projeto_ativo)
        conn.close()
        
        # Estado filter buttons - 6 options
        estado_col1, estado_col2, estado_col3, estado_col4, estado_col5, estado_col6 = st.columns(6)
        
        if 'estado_filter' not in st.session_state:
            st.session_state.estado_filter = 'Todos'
        
        with estado_col1:
            if st.button("🔄 Todos", use_container_width=True, 
                         type="primary" if st.session_state.estado_filter == 'Todos' else "secondary"):
                st.session_state.estado_filter = 'Todos'
                st.rerun()
        with estado_col2:
            if st.button("🔧 Desenv.", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'Desenvolvimento de Projeto' else "secondary"):
                st.session_state.estado_filter = 'Desenvolvimento de Projeto'
                st.rerun()
        with estado_col3:
            if st.button("📋 Emissão", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'Emissão de Projeto' else "secondary"):
                st.session_state.estado_filter = 'Emissão de Projeto'
                st.rerun()
        with estado_col4:
            if st.button("⚠️ Precisa Rev.", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'Precisa Revisão' else "secondary"):
                st.session_state.estado_filter = 'Precisa Revisão'
                st.rerun()
        with estado_col5:
            if st.button("✅ Construído", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'Construído' else "secondary"):
                st.session_state.estado_filter = 'Construído'
                st.rerun()
        with estado_col6:
            if st.button("🚨 Em Atraso", use_container_width=True,
                         type="primary" if st.session_state.estado_filter == 'Em Atraso' else "secondary"):
                st.session_state.estado_filter = 'Em Atraso'
                st.rerun()
        
        # Dropdown filters - Order: Ficheiro DWG, Prefixo, Tipo de Desenho, Elemento, Revisão
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        
        with col_f1:
            dwg_options = ["Todos"] + [d for d in dwg_sources_proj if d]
            dwg_filter = st.selectbox("Ficheiro DWG", dwg_options, key="dwg_filter_select")
        
        with col_f2:
            pfix_options = ["Todos"] + sorted([p for p in df['pfix'].dropna().unique().tolist() if p])
            pfix_filter = st.selectbox("Prefixo", pfix_options, key="pfix_filter_select")
        
        with col_f3:
            tipo_options = ["Todos"] + sorted(df['tipo_display'].dropna().unique().tolist())
            tipo_filter = st.selectbox("Tipo de Desenho", tipo_options)
        
        with col_f4:
            elemento_options = ["Todos"] + sorted(df['elemento_key'].dropna().unique().tolist())
            elemento_filter = st.selectbox("Elemento", elemento_options)
        
        with col_f5:
            r_options = ["Todos"] + sorted([r for r in df['r'].dropna().unique().tolist() if r])
            r_filter = st.selectbox("Revisão", r_options)
        
        # Search box
        search_text = st.text_input("🔎 Procurar", "", key="search_desenhos")
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply DWG filter
        if dwg_filter != "Todos":
            if 'dwg_source' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['dwg_source'] == dwg_filter]
        
        # Apply PFIX filter
        if pfix_filter != "Todos":
            if 'pfix' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['pfix'] == pfix_filter]
        
        # Apply estado filter - Em Atraso now stored directly in estado_interno
        if st.session_state.estado_filter != 'Todos':
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
        
        # ========================================
        # SORTING PRIORITY - 3 Levels
        # ========================================
        st.markdown("### 📊 Ordenação")
        
        # Sort options mapping: UI label -> DB column
        SORT_OPTIONS = {
            "Prefixo": "pfix",
            "Tipo de Desenho": "tipo_display",
            "NºDesenho": "des_num",
            "DWG": "dwg_source"
        }
        sort_labels = list(SORT_OPTIONS.keys())
        
        # Initialize session state for sort priorities
        if 'sort_priority_1' not in st.session_state:
            st.session_state['sort_priority_1'] = "Prefixo"
        if 'sort_priority_2' not in st.session_state:
            st.session_state['sort_priority_2'] = "Tipo de Desenho"
        if 'sort_priority_3' not in st.session_state:
            st.session_state['sort_priority_3'] = "NºDesenho"
        
        sort_col1, sort_col2, sort_col3 = st.columns(3)
        
        with sort_col1:
            sort_1 = st.selectbox(
                "1ª Prioridade",
                sort_labels,
                index=sort_labels.index(st.session_state['sort_priority_1']),
                key="sort_select_1"
            )
            st.session_state['sort_priority_1'] = sort_1
        
        with sort_col2:
            sort_2 = st.selectbox(
                "2ª Prioridade",
                sort_labels,
                index=sort_labels.index(st.session_state['sort_priority_2']),
                key="sort_select_2"
            )
            st.session_state['sort_priority_2'] = sort_2
        
        with sort_col3:
            sort_3 = st.selectbox(
                "3ª Prioridade",
                sort_labels,
                index=sort_labels.index(st.session_state['sort_priority_3']),
                key="sort_select_3"
            )
            st.session_state['sort_priority_3'] = sort_3
        
        # Apply multi-level sorting
        sort_columns = [
            SORT_OPTIONS[st.session_state['sort_priority_1']],
            SORT_OPTIONS[st.session_state['sort_priority_2']],
            SORT_OPTIONS[st.session_state['sort_priority_3']]
        ]
        
        # Only include columns that exist in the dataframe
        valid_sort_columns = [col for col in sort_columns if col in filtered_df.columns]
        
        if valid_sort_columns:
            filtered_df = filtered_df.sort_values(by=valid_sort_columns, ascending=True, na_position='last')
        
        st.markdown("---")
        
        # AgGrid Table
        st.markdown("### 📋 Tabela de Desenhos")
        
        # Column Selection
        st.markdown("#### 🔧 Seleção de Colunas")
        
        # Mapeamento de atributos BD -> Títulos UI
        COLUMN_TITLES = {
            'id': 'ID',
            'tipo_display': 'Tipo de Desenho',
            'pfix': 'Prefixo',
            'des_num': 'NºDesenho',
            'elemento': 'Elemento',
            'titulo': 'Titulo',
            'r': 'Ultima Revisão',
            'r_data': 'Data Revisão',
            'estado_interno': 'Estado do Desenho',
            'layout_name': 'Layout',
            'tipo_key': 'Tipo Key',
            'elemento_key': 'Elemento Key',
            'r_desc': 'Descrição Revisão',
            'comentario': 'Comentário',
            'data_limite': 'Data Limite',
            'responsavel': 'Responsável',
            'dwg_source': 'DWG_SOURCE',
            'cliente': 'Cliente',
            'obra': 'Obra',
            'localizacao': 'Localização',
            'especialidade': 'Especialidade',
            'fase': 'Fase',
            'projetou': 'Projetou',
            'escalas': 'Escalas',
            'data': 'Data',
            'proj_num': 'Proj Nº',
            'proj_nome': 'Projeto',
            'fase_pfix': 'Fase Pfix',
            'emissao': 'Emissão',
            'id_cad': 'ID CAD',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em',
            'elemento_titulo': 'Elemento Título'
        }
        
        # All available columns from the dataframe
        all_columns = [
            'id', 'tipo_display', 'pfix', 'des_num', 'elemento', 'titulo',
            'r', 'r_data', 'estado_interno', 'layout_name', 'tipo_key', 'elemento_key',
            'r_desc', 'comentario', 'data_limite', 'responsavel', 'dwg_source', 
            'cliente', 'obra', 'localizacao', 'especialidade', 'fase', 'projetou', 
            'escalas', 'data', 'proj_num', 'proj_nome', 'fase_pfix', 'emissao', 
            'id_cad', 'created_at', 'updated_at'
        ]
        
        # Default visible columns (ordem pretendida)
        default_visible = [
            'tipo_display', 'pfix', 'des_num', 'elemento', 'titulo',
            'r', 'r_data', 'estado_interno', 'data_limite'
        ]
        
        # Initialize session state for visible columns and column order
        if 'visible_columns' not in st.session_state:
            st.session_state['visible_columns'] = default_visible.copy()
        if 'column_order' not in st.session_state:
            st.session_state['column_order'] = None  # Will store user's column order
        
        # Filter to only show columns that exist in the filtered dataframe
        available_columns = [col for col in all_columns if col in filtered_df.columns]
        
        # Column selector with expander button
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            show_column_selector = st.button("🔧 Escolher Colunas", use_container_width=True)
        with col_btn2:
            if st.button("🔄 Restaurar Padrão", use_container_width=True):
                st.session_state['visible_columns'] = default_visible.copy()
                st.session_state['column_order'] = None
                st.rerun()
        
        # Show column selector in expander when button is clicked
        if show_column_selector or st.session_state.get('show_column_selector', False):
            st.session_state['show_column_selector'] = True
            with st.expander("📋 Selecionar Colunas a Visualizar", expanded=True):
                st.caption("Marque as colunas que deseja adicionar à tabela:")
                
                # Create checkboxes in columns for better layout
                cols_per_row = 4
                checkbox_cols = st.columns(cols_per_row)
                
                selected_additional = []
                for idx, col in enumerate(available_columns):
                    if col == 'id':  # Skip ID, always included internally
                        continue
                    col_idx = idx % cols_per_row
                    with checkbox_cols[col_idx]:
                        # Check if column is in default or currently selected
                        is_default = col in default_visible
                        is_selected = col in st.session_state['visible_columns']
                        label = f"{COLUMN_TITLES.get(col, col)}"
                        if is_default:
                            label += " ⭐"  # Mark default columns
                        if st.checkbox(label, value=is_selected, key=f"col_check_{col}"):
                            selected_additional.append(col)
                
                # Update button
                if st.button("✅ Atualizar Tabela", type="primary", use_container_width=True):
                    # Maintain order: default columns first (if selected), then additional
                    new_visible = []
                    for col in default_visible:
                        if col in selected_additional:
                            new_visible.append(col)
                    for col in selected_additional:
                        if col not in new_visible:
                            new_visible.append(col)
                    st.session_state['visible_columns'] = new_visible if new_visible else default_visible.copy()
                    st.session_state['show_column_selector'] = False
                    st.rerun()
        
        # Get display columns - use saved order if available
        display_columns = st.session_state['visible_columns'] if st.session_state['visible_columns'] else default_visible
        
        # Apply saved column order if exists
        if st.session_state.get('column_order'):
            # Reorder display_columns based on saved order
            saved_order = st.session_state['column_order']
            ordered_columns = []
            for col in saved_order:
                if col in display_columns:
                    ordered_columns.append(col)
            # Add any columns not in saved order
            for col in display_columns:
                if col not in ordered_columns:
                    ordered_columns.append(col)
            display_columns = ordered_columns
        
        # Ensure 'id' is always included for functionality (but can be hidden in display)
        if 'id' not in display_columns and 'id' in filtered_df.columns:
            aggrid_df = filtered_df[['id'] + [col for col in display_columns if col in filtered_df.columns]].copy()
        else:
            aggrid_df = filtered_df[[col for col in display_columns if col in filtered_df.columns]].copy()
        
        # Store original data for comparison
        if 'original_data' not in st.session_state:
            st.session_state['original_data'] = aggrid_df.copy()
        
        # Fill estado_interno empty values with default
        if 'estado_interno' in aggrid_df.columns:
            aggrid_df['estado_interno'] = aggrid_df['estado_interno'].fillna(ESTADO_DEFAULT)
            aggrid_df['estado_interno'] = aggrid_df['estado_interno'].replace('', ESTADO_DEFAULT)
        
        # Build AgGrid options
        gb = GridOptionsBuilder.from_dataframe(aggrid_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
        gb.configure_side_bar()
        gb.configure_default_column(filterable=True, sorteable=True, resizable=True, editable=True)
        gb.configure_selection('multiple', use_checkbox=True, pre_selected_rows=[])
        
        # Configure all columns with proper titles from COLUMN_TITLES
        for col in aggrid_df.columns:
            title = COLUMN_TITLES.get(col, col)
            width = 150  # Default width
            editable = True
            pinned = None
            
            # Special configurations per column
            if col == 'id':
                width = 60
                pinned = 'left'
                editable = False
            elif col == 'tipo_display':
                title = 'Tipo de Desenho'
                width = 150
            elif col == 'pfix':
                title = 'Prefixo'
                width = 100
            elif col == 'des_num':
                title = 'NºDesenho'
                width = 120
            elif col == 'elemento':
                title = 'Elemento'
                width = 150
            elif col == 'titulo':
                title = 'Titulo'
                width = 250
            elif col == 'r':
                title = 'Ultima Revisão'
                width = 100
            elif col == 'r_data':
                title = 'Data Revisão'
                width = 120
            elif col == 'estado_interno':
                title = 'Estado do Desenho'
                width = 180
                gb.configure_column(col, header_name=title, width=width, editable=editable,
                                  cellEditor='agSelectCellEditor',
                                  cellEditorParams={'values': ESTADO_OPTIONS})
                continue
            elif col == 'data_limite':
                title = 'Data Limite'
                width = 130
                # Configure as date with DD-MM-YYYY format display
                gb.configure_column(col, header_name=title, width=width, editable=editable,
                                  type=['dateColumnFilter', 'customDateTimeFormat'],
                                  custom_format_string='dd-MM-yyyy',
                                  valueFormatter="x ? x.split('-').reverse().join('-') : ''")
                continue
            elif col == 'layout_name':
                width = 200
            elif col == 'comentario':
                width = 250
            elif col == 'dwg_source':
                width = 180
            elif col == 'proj_nome':
                width = 200
            
            gb.configure_column(col, header_name=title, width=width, editable=editable, pinned=pinned)
        
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
                    
                    # Save column order from the current grid state
                    # The columns in edited_df reflect the current order
                    current_column_order = [col for col in edited_df.columns if col != 'estado_interno_display']
                    st.session_state['column_order'] = current_column_order
                    st.session_state['visible_columns'] = [col for col in current_column_order if col in st.session_state.get('visible_columns', default_visible)]
                    
                    # Define valid columns that exist in the desenhos table
                    # These are the ONLY columns we can update
                    valid_desenho_columns = {
                        'layout_name', 'proj_num', 'proj_nome', 'dwg_source',
                        'fase', 'fase_pfix', 'emissao', 'data', 'escalas', 'pfix',
                        'tipo_display', 'tipo_key', 'elemento', 'titulo', 'elemento_titulo',
                        'elemento_key', 'des_num', 'r', 'r_data', 'r_desc', 'id_cad',
                        'raw_attributes', 'estado_interno', 'comentario', 'data_limite', 'responsavel'
                    }
                    
                    # Columns to exclude from update (virtual/derived columns from JOIN)
                    excluded_columns = {'id', 'estado_interno_display', 'cliente', 'obra', 
                                       'localizacao', 'especialidade', 'projetou', 
                                       'created_at', 'updated_at'}
                    
                    # Compare with original and update database
                    changes_made = 0
                    errors = []
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    try:
                        for idx, row in edited_df.iterrows():
                            if 'id' in row and pd.notna(row['id']):
                                desenho_id = int(row['id'])
                                
                                # Build update dict with only valid editable fields
                                update_fields = {}
                                for col in edited_df.columns:
                                    # Only include columns that exist in desenhos table and not excluded
                                    if col in valid_desenho_columns and col not in excluded_columns:
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
                        
                        # Clear original data to force reload from DB
                        if 'original_data' in st.session_state:
                            del st.session_state['original_data']
                        
                        # Clear filter selections to force refresh with new data
                        for key in list(st.session_state.keys()):
                            if key.endswith('_filter_select') or key == 'estado_filter':
                                del st.session_state[key]
                        
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
            st.caption("💡 Edite células na tabela. A ordem das colunas também é guardada.")
        
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
                            st.text(f"DWG_SOURCE: {desenho.get('dwg_source', '-')}")
                        
                        with col_edit:
                            st.markdown("**✏️ Editar Estado:**")
                            
                            estado_atual = desenho.get('estado_interno') or ESTADO_DEFAULT
                            # Ensure estado_atual is a valid option
                            if estado_atual not in ESTADO_OPTIONS:
                                estado_atual = ESTADO_DEFAULT
                            estado_labels = {e: ESTADO_CONFIG[e]['label'] for e in ESTADO_OPTIONS}
                            
                            novo_estado = st.selectbox(
                                "Estado do Desenho:",
                                ESTADO_OPTIONS,
                                index=ESTADO_OPTIONS.index(estado_atual),
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
        
        # Export buttons
        st.markdown("---")
        st.markdown("### 📥 Exportar Dados")
        
        col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])
        
        # Download CSV Filtrado
        with col_exp1:
            csv_export = aggrid_df.to_csv(sep=';', index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download CSV Filtrado",
                data=csv_export,
                file_name=f"desenhos_filtrados_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Download CSV Completo
        with col_exp2:
            # Build options for selectbox - only for active project
            export_options = ["-- Selecione --"]
            if dwg_sources_proj:
                export_options += dwg_sources_proj
            export_options += ["📦 Todos DWG Separados", "📋 Todos DWG Juntos"]
            
            export_choice = st.selectbox(
                "CSV Completo - Escolha:",
                export_options,
                key="csv_export_select",
                label_visibility="collapsed"
            )
        
        with col_exp3:
            if export_choice and export_choice != "-- Selecione --":
                today_str = datetime.now().strftime('%Y-%m-%d')
                
                if export_choice == "📦 Todos DWG Separados":
                    # Generate ZIP with multiple CSVs
                    import zipfile
                    
                    # Create ZIP in memory
                    zip_buffer = io.BytesIO()
                    conn = get_connection()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for dwg in dwg_sources_proj:
                            desenhos_dwg = get_desenhos_by_dwg_source_with_revisoes(conn, dwg)
                            # Filter by project
                            desenhos_dwg = [d for d in desenhos_dwg if d.get('proj_num') == projeto_ativo]
                            if desenhos_dwg:
                                csv_content = export_desenhos_to_csv(desenhos_dwg)
                                # Clean DWG name for filename
                                dwg_clean = dwg.replace('.dwg', '').replace('.DWG', '')
                                filename = f"{dwg_clean}-LD-{today_str}.csv"
                                zf.writestr(filename, csv_content.encode('utf-8-sig'))
                    
                    conn.close()
                    zip_buffer.seek(0)
                    
                    zip_filename = f"{projeto_ativo}-LD-SEPARADOS-{today_str}.zip"
                    
                    st.download_button(
                        label="📥 Download ZIP (Separados)",
                        data=zip_buffer.getvalue(),
                        file_name=zip_filename,
                        mime="application/zip",
                        key="download_zip_separated",
                        use_container_width=True
                    )
                
                elif export_choice == "📋 Todos DWG Juntos":
                    # Generate single CSV with all DWGs for active project
                    conn = get_connection()
                    desenhos_all = get_all_desenhos_with_revisoes_sorted(conn)
                    conn.close()
                    
                    # Filter by active project
                    desenhos_all = [d for d in desenhos_all if d.get('proj_num') == projeto_ativo]
                    
                    if desenhos_all:
                        csv_content = export_desenhos_to_csv(desenhos_all)
                        filename = f"{projeto_ativo}-LD-COMPLETA-{today_str}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV Completo",
                            data=csv_content.encode('utf-8-sig'),
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True,
                            key="download_csv_all"
                        )
                    else:
                        st.warning("Nenhum desenho para exportar.")
                
                else:
                    # Single DWG source
                    conn = get_connection()
                    desenhos_dwg = get_desenhos_by_dwg_source_with_revisoes(conn, export_choice)
                    conn.close()
                    
                    # Filter by active project
                    desenhos_dwg = [d for d in desenhos_dwg if d.get('proj_num') == projeto_ativo]
                    
                    if desenhos_dwg:
                        csv_content = export_desenhos_to_csv(desenhos_dwg)
                        dwg_clean = export_choice.replace('.dwg', '').replace('.DWG', '')
                        filename = f"{dwg_clean}-LD-{today_str}.csv"
                        
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_content.encode('utf-8-sig'),
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True,
                            key="download_csv_single"
                        )
                    else:
                        st.warning(f"Nenhum desenho encontrado para {export_choice}.")

        # ========================================
        # DELETE DESENHOS SECTION
        # ========================================
        st.markdown("---")
        st.markdown("### 🗑️ Eliminar Desenhos")
        
        with st.expander("⚠️ Opções de Eliminação", expanded=False):
            st.warning("**Atenção:** As operações de eliminação são irreversíveis!")
            
            # Option 1: Delete selected rows
            st.markdown("#### 1️⃣ Eliminar Selecionados na Tabela")
            selected_rows_for_delete = grid_response['selected_rows']
            if selected_rows_for_delete is not None and len(selected_rows_for_delete) > 0:
                if isinstance(selected_rows_for_delete, pd.DataFrame):
                    selected_ids = selected_rows_for_delete['id'].tolist() if 'id' in selected_rows_for_delete.columns else []
                else:
                    selected_ids = [r.get('id') for r in selected_rows_for_delete if r.get('id')]
                
                selected_count = len(selected_ids)
                st.info(f"📋 **{selected_count} desenho(s) selecionado(s)**")
                
                if st.button(f"🗑️ Eliminar {selected_count} Selecionado(s)", type="primary", key="btn_delete_selected"):
                    if st.session_state.get('confirm_delete_selected'):
                        conn = get_connection()
                        deleted = delete_desenhos_by_ids(conn, selected_ids)
                        conn.close()
                        st.success(f"✅ {deleted} desenho(s) eliminado(s)!")
                        st.session_state['confirm_delete_selected'] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state['confirm_delete_selected'] = True
                        st.warning("⚠️ Clique novamente para confirmar a eliminação!")
            else:
                st.caption("💡 Selecione desenhos na tabela acima usando as checkboxes")
            
            st.markdown("---")
            
            # Option 2: Delete by PFIX
            st.markdown("#### 2️⃣ Eliminar por PFIX")
            col_pfix1, col_pfix2 = st.columns([2, 1])
            
            with col_pfix1:
                # Get unique PFIX values for the active project
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT pfix FROM desenhos 
                    WHERE proj_num = ? AND pfix IS NOT NULL AND pfix != '' 
                    ORDER BY pfix
                """, (projeto_ativo,))
                pfix_options = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if pfix_options:
                    selected_pfix = st.selectbox(
                        "Escolha o PFIX:",
                        ["-- Selecione --"] + pfix_options,
                        key="delete_pfix_select"
                    )
                else:
                    selected_pfix = None
                    st.caption("Nenhum PFIX encontrado no projeto ativo")
            
            with col_pfix2:
                if selected_pfix and selected_pfix != "-- Selecione --":
                    if st.button(f"🗑️ Eliminar PFIX: {selected_pfix}", type="secondary", key="btn_delete_pfix"):
                        if st.session_state.get('confirm_delete_pfix'):
                            conn = get_connection()
                            deleted = delete_desenhos_by_projeto_and_pfix(conn, projeto_ativo, selected_pfix)
                            conn.close()
                            st.success(f"✅ {deleted} desenho(s) eliminado(s) com PFIX '{selected_pfix}'!")
                            st.session_state['confirm_delete_pfix'] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.session_state['confirm_delete_pfix'] = True
                            st.warning("⚠️ Clique novamente para confirmar!")
            
            st.markdown("---")
            
            # Option 3: Delete by DWG_Source
            st.markdown("#### 3️⃣ Eliminar por DWG_Source")
            col_dwg1, col_dwg2 = st.columns([2, 1])
            
            with col_dwg1:
                if dwg_sources_proj:
                    selected_dwg_source = st.selectbox(
                        "Escolha o DWG_Source:",
                        ["-- Selecione --"] + dwg_sources_proj,
                        key="delete_dwg_source_select"
                    )
                else:
                    selected_dwg_source = None
                    st.caption("Nenhum DWG_Source encontrado no projeto ativo")
            
            with col_dwg2:
                if selected_dwg_source and selected_dwg_source != "-- Selecione --":
                    if st.button(f"🗑️ Eliminar DWG: {selected_dwg_source[:20]}...", type="secondary", key="btn_delete_dwg_source"):
                        if st.session_state.get('confirm_delete_dwg_source'):
                            conn = get_connection()
                            deleted = delete_desenhos_by_projeto_and_dwg_source(conn, projeto_ativo, selected_dwg_source)
                            conn.close()
                            st.success(f"✅ {deleted} desenho(s) eliminado(s) do DWG '{selected_dwg_source}'!")
                            st.session_state['confirm_delete_dwg_source'] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.session_state['confirm_delete_dwg_source'] = True
                            st.warning("⚠️ Clique novamente para confirmar!")
            
            st.markdown("---")
            
            # Option 4: Delete ALL from project
            st.markdown("#### 4️⃣ Eliminar TODOS os Desenhos do Projeto")
            st.error(f"**⚠️ PERIGO:** Esta opção eliminará TODOS os desenhos do projeto **{projeto_ativo}**!")
            
            # Get count
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM desenhos WHERE proj_num = ?", (projeto_ativo,))
            total_desenhos_projeto = cursor.fetchone()[0]
            conn.close()
            
            st.info(f"📊 Total de desenhos no projeto: **{total_desenhos_projeto}**")
            
            # Require typing project number to confirm
            confirm_text = st.text_input(
                f"Digite '{projeto_ativo}' para confirmar:",
                key="confirm_delete_all_input"
            )
            
            if st.button("🗑️ ELIMINAR TODOS DO PROJETO", type="primary", key="btn_delete_all"):
                if confirm_text == projeto_ativo:
                    conn = get_connection()
                    deleted = delete_all_desenhos_by_projeto(conn, projeto_ativo)
                    conn.close()
                    st.success(f"✅ {deleted} desenho(s) eliminado(s) do projeto {projeto_ativo}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Digite '{projeto_ativo}' corretamente para confirmar a eliminação.")

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
                hist_columns = ['des_num', 'layout_name', 'tipo_display', 'elemento', 'titulo', 'r', 'r_data', 'r_desc', 'dwg_source']
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
            # Initialize session state for CSV import
            if 'csv_import_section_key' not in st.session_state:
                st.session_state['csv_import_section_key'] = 0
            
            csv_section_key = f"csv_import_{st.session_state['csv_import_section_key']}"
            csv_file = st.file_uploader("Escolha ficheiro CSV", type=['csv'], key=csv_section_key)
            
            if csv_file is not None:
                if st.button("📄 Importar CSV Selecionado", use_container_width=True, type="primary"):
                    with st.spinner(f"Importando {csv_file.name}..."):
                        try:
                            # Save uploaded file temporarily
                            temp_path = Path("data/csv_in") / csv_file.name
                            temp_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(temp_path, 'wb') as f:
                                f.write(csv_file.getbuffer())
                            
                            conn = get_connection()
                            stats = import_single_csv(str(temp_path), conn, target_proj_num=None)
                            conn.close()
                            
                            # Cleanup temp file
                            if temp_path.exists():
                                temp_path.unlink()
                            
                            st.success(
                                f"✅ Importação CSV concluída!\n\n"
                                f"Ficheiro: {csv_file.name}\n"
                                f"Desenhos: {stats['desenhos_imported']}"
                            )
                            # Clear uploader
                            st.session_state['csv_import_section_key'] += 1
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
            else:
                st.caption("💡 Selecione um ficheiro CSV para importar")
        
        st.markdown("---")
        
        # Upload CSV directly with project selection
        st.subheader("📤 Upload CSV com Seleção de Projeto")
        # Use dynamic key to allow clearing the uploader after import
        csv_uploader_key = f"csv_uploader_main_{st.session_state.get('csv_file_uploader_key', 0)}"
        uploaded_csv = st.file_uploader("Escolha um ficheiro CSV", type=['csv'], key=csv_uploader_key)
        
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
                            
                            # Clean up: delete temp file after import
                            if temp_path.exists():
                                temp_path.unlink()
                            
                            st.success(f"✅ Importado! Desenhos: {stats['desenhos_imported']}")
                            # Reset state and clear uploader
                            st.session_state['csv_import_mode'] = None
                            if 'csv_uploader_main' in st.session_state:
                                del st.session_state['csv_uploader_main']
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                            # Clean up on error too
                            if temp_path.exists():
                                temp_path.unlink()
            
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
                                    # Cleanup temp file
                                    if temp_path.exists():
                                        temp_path.unlink()
                                    # Reset state and clear file uploader
                                    st.session_state['csv_import_mode'] = None
                                    st.session_state['csv_file_uploader_key'] = st.session_state.get('csv_file_uploader_key', 0) + 1
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {e}")
                                    # Cleanup temp file even on error
                                    if temp_path.exists():
                                        temp_path.unlink()
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
                dwg_info = ", ".join([f"{d['dwg_source']}({d['count']})" for d in db_stats['dwg_list']])
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
                dwg_list = [d['dwg_source'] for d in get_dwg_list(conn)]
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
