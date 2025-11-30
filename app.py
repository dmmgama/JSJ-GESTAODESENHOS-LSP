"""
Streamlit app - UI for JSJ Drawing Management LPP Sync.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from db import get_connection, criar_tabelas, get_all_desenhos, get_revisoes_by_desenho_id, get_desenho_by_layout, get_dwg_list, delete_all_desenhos, delete_desenhos_by_dwg, get_db_stats
from json_importer import import_all_json
from csv_importer import import_all_csv, import_single_csv
from lpp_builder import build_lpp_from_db


# Page config
st.set_page_config(
    page_title="JSJ - LPP Sync",
    page_icon="📐",
    layout="wide"
)

# Initialize database (create tables once)
def init_db():
    """Initialize database - create tables if needed."""
    conn = get_connection()
    criar_tabelas(conn)
    conn.close()

init_db()

# Sidebar
st.sidebar.title("🔧 Operações")

st.sidebar.markdown("---")

# Import section
st.sidebar.subheader("1. Atualizar DB")

# Import JSON
if st.sidebar.button("📥 Importar JSON", use_container_width=True):
    with st.spinner("Importando JSON files..."):
        try:
            conn = get_connection()
            stats = import_all_json("data/json_in", conn)
            conn.close()
            st.sidebar.success(
                f"✅ Importação JSON concluída!\n\n"
                f"Ficheiros: {stats['files_processed']}\n"
                f"Desenhos: {stats['desenhos_imported']}"
            )
        except Exception as e:
            st.sidebar.error(f"❌ Erro: {e}")

# Import CSV
if st.sidebar.button("📄 Importar CSV", use_container_width=True):
    with st.spinner("Importando CSV files..."):
        try:
            conn = get_connection()
            stats = import_all_csv("data/csv_in", conn)
            conn.close()
            st.sidebar.success(
                f"✅ Importação CSV concluída!\n\n"
                f"Ficheiros: {stats['files_processed']}\n"
                f"Desenhos: {stats['desenhos_imported']}"
            )
        except Exception as e:
            st.sidebar.error(f"❌ Erro: {e}")

# Upload CSV directly
uploaded_csv = st.sidebar.file_uploader("📤 Selecionar CSV", type=['csv'], key="csv_uploader")

if uploaded_csv is not None:
    st.sidebar.caption(f"📄 Ficheiro: {uploaded_csv.name}")
    
    if st.sidebar.button("➕ Importar para DB", use_container_width=True, type="primary"):
        # Save file
        temp_path = Path("data/csv_in") / uploaded_csv.name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_csv.getbuffer())
        
        with st.spinner(f"Importando {uploaded_csv.name}..."):
            try:
                conn = get_connection()
                stats = import_single_csv(str(temp_path), conn)
                conn.close()
                st.sidebar.success(
                    f"✅ Importado!\n\n"
                    f"Desenhos: {stats['desenhos_imported']}"
                )
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Erro: {e}")

st.sidebar.markdown("---")

# Generate LPP
st.sidebar.subheader("2. Gerar LPP")

# Upload template
uploaded_template = st.sidebar.file_uploader("📋 Template LPP (Excel)", type=['xlsx', 'xls'], key="template_uploader")
if uploaded_template is not None:
    template_path = Path("data") / "LPP_TEMPLATE.xlsx"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    with open(template_path, 'wb') as f:
        f.write(uploaded_template.getbuffer())
    st.sidebar.success("✅ Template carregado!")

# Check if template exists
template_path = Path("data/LPP_TEMPLATE.xlsx")
template_exists = template_path.exists()

if not template_exists:
    st.sidebar.warning("⚠️ Faça upload do template LPP primeiro")

if st.sidebar.button("📊 Gerar/Atualizar LPP.xlsx", use_container_width=True, disabled=not template_exists):
    output_path = "output/LPP.xlsx"
    Path("output").mkdir(parents=True, exist_ok=True)
    
    with st.spinner("Gerando LPP.xlsx..."):
        try:
            conn = get_connection()
            build_lpp_from_db(str(template_path), output_path, conn)
            conn.close()
            st.sidebar.success(f"✅ LPP gerado com sucesso!\n\nFicheiro: {output_path}")
        except Exception as e:
            st.sidebar.error(f"❌ Erro ao gerar LPP: {e}")

st.sidebar.markdown("---")

# DB Management section
st.sidebar.subheader("3. Gestão da DB")

# Get DB stats
conn = get_connection()
db_stats = get_db_stats(conn)
conn.close()

st.sidebar.caption(f"📊 **{db_stats['total_desenhos']} desenhos** de **{db_stats['total_dwgs']} DWG(s)**")

# Show DWG list
if db_stats['dwg_list']:
    dwg_info = ", ".join([f"{d['dwg_name']}({d['count']})" for d in db_stats['dwg_list']])
    st.sidebar.caption(f"📁 {dwg_info}")

# Delete all button
if db_stats['total_desenhos'] > 0:
    if st.sidebar.button("🗑️ Apagar TODA a DB", type="secondary", use_container_width=True):
        st.session_state['confirm_delete_all'] = True

    if st.session_state.get('confirm_delete_all', False):
        st.sidebar.warning(f"⚠️ Apagar TODOS os {db_stats['total_desenhos']} desenhos?")
        col_yes, col_no = st.sidebar.columns(2)
        with col_yes:
            if st.button("✅ Sim", key="yes_all"):
                conn = get_connection()
                deleted = delete_all_desenhos(conn)
                conn.close()
                st.session_state['confirm_delete_all'] = False
                st.rerun()
        with col_no:
            if st.button("❌ Não", key="no_all"):
                st.session_state['confirm_delete_all'] = False
                st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Como usar:**\n\n"
    "1. Selecione CSV\n"
    "2. Clique 'Importar para DB'\n"
    "3. Repita para mais DWGs\n\n"
    "Os dados são **agregados** - novos layouts adicionados, existentes atualizados."
)

# Main area
st.title("📐 JSJ - Gestão de Desenhos LPP")
st.markdown("---")

# Load data (fresh connection each time)
def load_data():
    """Load desenhos from database."""
    conn = get_connection()
    desenhos = get_all_desenhos(conn)
    conn.close()
    if desenhos:
        df = pd.DataFrame(desenhos)
        return df
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ Nenhum desenho na base de dados. Importe JSON ou CSV primeiro.")
else:
    st.success(f"✅ **{len(df)} desenhos** na base de dados")
    
    # Filters
    st.subheader("🔍 Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tipo_options = ["Todos"] + sorted(df['tipo_display'].dropna().unique().tolist())
        tipo_filter = st.selectbox("TIPO", tipo_options)
    
    with col2:
        elemento_options = ["Todos"] + sorted(df['elemento_key'].dropna().unique().tolist())
        elemento_filter = st.selectbox("ELEMENTO", elemento_options)
    
    with col3:
        r_options = ["Todos"] + sorted(df['r'].dropna().unique().tolist())
        r_filter = st.selectbox("Revisão (R)", r_options)
    
    with col4:
        search_text = st.text_input("🔎 Procurar (DES_NUM ou LAYOUT)", "")
    
    # Apply filters
    filtered_df = df.copy()
    
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
    
    st.markdown(f"**Resultados:** {len(filtered_df)} desenhos")
    
    # Toggle between view and edit mode
    col_mode1, col_mode2, col_mode3 = st.columns([1, 1, 3])
    with col_mode1:
        edit_mode = st.toggle("✏️ Modo Edição", value=False)
    with col_mode2:
        show_column_selector = st.toggle("⚙️ Colunas", value=False)
    
    # All available columns with friendly names
    all_columns = {
        'des_num': 'Nº Desenho',
        'layout_name': 'Layout',
        'tipo_display': 'Tipo',
        'elemento': 'Elemento',
        'titulo': 'Título',
        'elemento_key': 'Elemento (Agrup.)',
        'elemento_titulo': 'Elemento + Título',
        'r': 'Revisão',
        'r_data': 'Data Revisão',
        'r_desc': 'Descrição Revisão',
        'data': 'Data 1ª Emissão',
        'cliente': 'Cliente',
        'obra': 'Obra',
        'localizacao': 'Localização',
        'especialidade': 'Especialidade',
        'fase': 'Fase',
        'projetou': 'Projetou',
        'dwg_name': 'Ficheiro DWG'
    }
    
    # Default columns to show
    default_cols = ['des_num', 'layout_name', 'tipo_display', 'elemento', 'titulo', 'r', 'r_data', 'r_desc', 'cliente']
    
    # Column selector
    if show_column_selector:
        st.markdown("**Selecione as colunas a mostrar:**")
        available_cols = [col for col in all_columns.keys() if col in filtered_df.columns]
        
        # Use session state to persist column selection
        if 'selected_columns' not in st.session_state:
            st.session_state.selected_columns = default_cols
        
        # Create checkboxes in columns
        col_checks = st.columns(4)
        selected_cols = []
        for i, col in enumerate(available_cols):
            with col_checks[i % 4]:
                if st.checkbox(all_columns[col], value=col in st.session_state.selected_columns, key=f"col_{col}"):
                    selected_cols.append(col)
        
        st.session_state.selected_columns = selected_cols if selected_cols else default_cols
        view_cols = st.session_state.selected_columns
    else:
        # Use default or session state columns
        if 'selected_columns' in st.session_state:
            view_cols = [col for col in st.session_state.selected_columns if col in filtered_df.columns]
        else:
            view_cols = [col for col in default_cols if col in filtered_df.columns]
    
    # Editable columns (fields that can be changed and synced back to AutoCAD)
    edit_cols = [
        'layout_name', 'cliente', 'obra', 'localizacao', 'especialidade', 'fase',
        'data', 'projetou', 'des_num', 'tipo_display', 'elemento_key', 'elemento_titulo', 'r'
    ]
    
    # Ensure columns exist
    view_cols = [col for col in view_cols if col in filtered_df.columns]
    edit_cols = [col for col in edit_cols if col in filtered_df.columns]
    
    # Rename columns for display
    display_df = filtered_df[view_cols].copy()
    display_df.columns = [all_columns.get(col, col) for col in view_cols]
    
    if not edit_mode:
        # Normal view mode
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
    else:
        # Edit mode with data_editor
        st.info("📝 **Modo Edição Ativo** - Edite os campos diretamente na tabela. Depois exporte o CSV para importar no AutoCAD.")
        
        # Prepare editable dataframe
        edit_df = filtered_df[edit_cols].copy()
        
        # Use data_editor for editing
        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            height=400,
            num_rows="fixed",
            key="data_editor"
        )
        
        # Export buttons
        st.markdown("---")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # Export edited data as CSV for AutoLISP import
            if st.button("📤 Exportar CSV para AutoCAD", use_container_width=True):
                # Prepare CSV with ID_CAD (layout_name is the key)
                export_df = edited_df.copy()
                
                # Rename columns to match AutoLISP expected format
                column_rename = {
                    'layout_name': 'TAG DO LAYOUT',
                    'cliente': 'CLIENTE',
                    'obra': 'OBRA', 
                    'localizacao': 'LOCALIZAÇÃO',
                    'especialidade': 'ESPECIALIDADE',
                    'fase': 'FASE',
                    'data': 'DATA 1ª EMISSÃO',
                    'projetou': 'PROJETOU',
                    'des_num': 'NUMERO DE DESENHO',
                    'tipo_display': 'TIPO',
                    'elemento_key': 'ELEMENTO',
                    'elemento_titulo': 'TITULO',
                    'r': 'REVISÃO'
                }
                export_df = export_df.rename(columns=column_rename)
                
                # Save to output folder
                output_path = Path("output/ALTERACOES_PARA_AUTOCAD.csv")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                export_df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
                
                st.success(f"✅ CSV exportado para: {output_path}")
                st.info("💡 No AutoCAD, use JSJ → Importar → Importar CSV para aplicar as alterações")
        
        with col_exp2:
            # Download button
            csv_data = edited_df.to_csv(sep=';', index=False).encode('utf-8-sig')
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name="desenhos_editados.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp3:
            # Save changes to database
            if st.button("💾 Guardar na DB", use_container_width=True):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    for idx, row in edited_df.iterrows():
                        layout_name = row['layout_name']
                        cursor.execute("""
                            UPDATE desenhos SET
                                cliente = ?,
                                obra = ?,
                                localizacao = ?,
                                especialidade = ?,
                                fase = ?,
                                data = ?,
                                projetou = ?,
                                des_num = ?,
                                tipo_display = ?,
                                elemento_key = ?,
                                elemento_titulo = ?,
                                r = ?
                            WHERE layout_name = ?
                        """, (
                            row.get('cliente', ''),
                            row.get('obra', ''),
                            row.get('localizacao', ''),
                            row.get('especialidade', ''),
                            row.get('fase', ''),
                            row.get('data', ''),
                            row.get('projetou', ''),
                            row.get('des_num', ''),
                            row.get('tipo_display', ''),
                            row.get('elemento_key', ''),
                            row.get('elemento_titulo', ''),
                            row.get('r', ''),
                            layout_name
                        ))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {len(edited_df)} registos atualizados na base de dados!")
                except Exception as e:
                    st.error(f"❌ Erro ao guardar: {e}")
    
    # Statistics
    st.markdown("---")
    st.subheader("📊 Estatísticas")
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Total Desenhos", len(filtered_df))
    
    with stat_col2:
        unique_tipos = filtered_df['tipo_display'].nunique()
        st.metric("Tipos Únicos", unique_tipos)
    
    with stat_col3:
        unique_elementos = filtered_df['elemento_key'].nunique()
        st.metric("Elementos Únicos", unique_elementos)
    
    with stat_col4:
        latest_rev = filtered_df['r'].mode()[0] if not filtered_df['r'].empty else "-"
        st.metric("Revisão Mais Comum", latest_rev)
    
    # Detailed view expander
    with st.expander("🔍 Ver detalhes e histórico de revisões"):
        if not filtered_df.empty:
            selected_layout = st.selectbox(
                "Selecione layout:",
                filtered_df['layout_name'].tolist()
            )
            
            desenho_detail = filtered_df[filtered_df['layout_name'] == selected_layout].iloc[0]
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**📋 Informação Geral:**")
                st.text(f"Layout: {desenho_detail.get('layout_name', '-')}")
                st.text(f"DWG: {desenho_detail.get('dwg_name', '-')}")
                st.text(f"DES_NUM: {desenho_detail.get('des_num', '-')}")
                st.text(f"Data 1ª Emissão: {desenho_detail.get('data', '-')}")
                st.text(f"Cliente: {desenho_detail.get('cliente', '-')}")
                st.text(f"Obra: {desenho_detail.get('obra', '-')}")
            
            with col_b:
                st.markdown("**📐 Conteúdo:**")
                st.text(f"TIPO: {desenho_detail.get('tipo_display', '-')}")
                st.text(f"ELEMENTO: {desenho_detail.get('elemento_key', '-')}")
                st.text(f"TITULO: {desenho_detail.get('elemento_titulo', '-')}")
                st.text(f"Especialidade: {desenho_detail.get('especialidade', '-')}")
                st.text(f"Fase: {desenho_detail.get('fase', '-')}")
                st.text(f"Projetou: {desenho_detail.get('projetou', '-')}")
            
            # Histórico de Revisões
            st.markdown("---")
            st.markdown(f"**📜 Histórico de Revisões** (Atual: **{desenho_detail.get('r', '-')}**)")
            
            # Obter revisões da DB
            desenho_id = desenho_detail.get('id')
            if desenho_id:
                conn = get_connection()
                revisoes = get_revisoes_by_desenho_id(conn, desenho_id)
                conn.close()
                
                if revisoes:
                    rev_df = pd.DataFrame(revisoes)
                    rev_df.columns = ['Revisão', 'Data', 'Descrição']
                    st.dataframe(rev_df, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ Sem histórico de revisões registado. Importe um CSV com todos os campos para registar revisões.")
            else:
                st.warning("⚠️ ID do desenho não encontrado")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "JSJ Engenharia - Sistema de Gestão de Desenhos | v1.0"
    "</div>",
    unsafe_allow_html=True
)
