"""
Streamlit app - UI for JSJ Drawing Management LPP Sync.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from db import get_connection, criar_tabelas, get_all_desenhos, get_revisoes_by_desenho_id, get_desenho_by_layout, get_dwg_list, delete_all_desenhos, delete_desenhos_by_dwg, delete_desenhos_by_tipo, delete_desenhos_by_elemento, delete_desenho_by_layout, get_db_stats, get_all_desenhos_with_revisoes, get_unique_tipos, get_unique_elementos, get_all_layout_names
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

# Opções de limpeza da DB
if db_stats['total_desenhos'] > 0:
    st.sidebar.markdown("**🗑️ Limpar Base de Dados**")
    
    # Escolha do tipo de limpeza
    delete_type = st.sidebar.selectbox(
        "Apagar por:",
        ["Escolher...", "Tudo", "Por DWG", "Por Tipo", "Por Elemento", "Desenho Individual"],
        key="delete_type"
    )
    
    if delete_type == "Tudo":
        if st.sidebar.button("⚠️ Apagar TODA a DB", type="secondary", use_container_width=True):
            st.session_state['confirm_delete'] = 'all'
    
    elif delete_type == "Por DWG":
        conn = get_connection()
        dwg_list = [d['dwg_name'] for d in get_dwg_list(conn)]
        conn.close()
        if dwg_list:
            selected_dwg_del = st.sidebar.selectbox("Selecione DWG:", dwg_list, key="del_dwg")
            if st.sidebar.button(f"🗑️ Apagar {selected_dwg_del}", use_container_width=True):
                st.session_state['confirm_delete'] = ('dwg', selected_dwg_del)
    
    elif delete_type == "Por Tipo":
        conn = get_connection()
        tipos = get_unique_tipos(conn)
        conn.close()
        if tipos:
            selected_tipo_del = st.sidebar.selectbox("Selecione Tipo:", tipos, key="del_tipo")
            if st.sidebar.button(f"🗑️ Apagar tipo '{selected_tipo_del}'", use_container_width=True):
                st.session_state['confirm_delete'] = ('tipo', selected_tipo_del)
        else:
            st.sidebar.info("Nenhum tipo encontrado")
    
    elif delete_type == "Por Elemento":
        conn = get_connection()
        elementos = get_unique_elementos(conn)
        conn.close()
        if elementos:
            selected_elem_del = st.sidebar.selectbox("Selecione Elemento:", elementos, key="del_elem")
            if st.sidebar.button(f"🗑️ Apagar elemento '{selected_elem_del}'", use_container_width=True):
                st.session_state['confirm_delete'] = ('elemento', selected_elem_del)
        else:
            st.sidebar.info("Nenhum elemento encontrado")
    
    elif delete_type == "Desenho Individual":
        conn = get_connection()
        layouts = get_all_layout_names(conn)
        conn.close()
        if layouts:
            selected_layout_del = st.sidebar.selectbox("Selecione Layout:", layouts, key="del_layout")
            if st.sidebar.button(f"🗑️ Apagar '{selected_layout_del}'", use_container_width=True):
                st.session_state['confirm_delete'] = ('layout', selected_layout_del)
        else:
            st.sidebar.info("Nenhum layout encontrado")
    
    # Confirmação de exclusão
    if st.session_state.get('confirm_delete'):
        delete_info = st.session_state['confirm_delete']
        
        if delete_info == 'all':
            st.sidebar.error(f"⚠️ Apagar TODOS os {db_stats['total_desenhos']} desenhos?")
        elif delete_info[0] == 'dwg':
            st.sidebar.error(f"⚠️ Apagar todos os desenhos do DWG '{delete_info[1]}'?")
        elif delete_info[0] == 'tipo':
            st.sidebar.error(f"⚠️ Apagar todos os desenhos do tipo '{delete_info[1]}'?")
        elif delete_info[0] == 'elemento':
            st.sidebar.error(f"⚠️ Apagar todos os desenhos do elemento '{delete_info[1]}'?")
        elif delete_info[0] == 'layout':
            st.sidebar.error(f"⚠️ Apagar o layout '{delete_info[1]}'?")
        
        col_yes, col_no = st.sidebar.columns(2)
        with col_yes:
            if st.button("✅ Confirmar", key="yes_delete"):
                conn = get_connection()
                deleted = 0
                
                if delete_info == 'all':
                    deleted = delete_all_desenhos(conn)
                elif delete_info[0] == 'dwg':
                    deleted = delete_desenhos_by_dwg(conn, delete_info[1])
                elif delete_info[0] == 'tipo':
                    deleted = delete_desenhos_by_tipo(conn, delete_info[1])
                elif delete_info[0] == 'elemento':
                    deleted = delete_desenhos_by_elemento(conn, delete_info[1])
                elif delete_info[0] == 'layout':
                    deleted = delete_desenho_by_layout(conn, delete_info[1])
                
                conn.close()
                st.session_state['confirm_delete'] = None
                st.sidebar.success(f"✅ {deleted} desenho(s) apagado(s)")
                st.rerun()
        
        with col_no:
            if st.button("❌ Cancelar", key="no_delete"):
                st.session_state['confirm_delete'] = None
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
    
    # ========================================
    # ORDENAÇÃO (sempre visível, fora do modo edição)
    # ========================================
    st.markdown("---")
    st.subheader("📊 Ordenação")
    
    # Colunas disponíveis para ordenação
    sort_columns_available = {
        'des_num': 'Nº Desenho',
        'tipo_display': 'Tipo',
        'elemento_key': 'Elemento',
        'layout_name': 'Layout',
        'r': 'Revisão'
    }
    
    # Detectar se DES_NUM tem prefixos de tipo ou elemento
    def has_prefix_pattern(df):
        """Verifica se os DES_NUM têm padrão de prefixo tipo/elemento"""
        if 'des_num' not in df.columns:
            return False
        des_nums = df['des_num'].dropna().astype(str).tolist()
        with_prefix = sum(1 for d in des_nums if d and d[0].isalpha())
        return with_prefix > len(des_nums) * 0.3
    
    has_prefixes = has_prefix_pattern(filtered_df)
    
    # Inicializar session_state para ordenação
    if 'sort_criteria_1' not in st.session_state:
        st.session_state.sort_criteria_1 = 'tipo_display' if has_prefixes else 'des_num'
    if 'sort_criteria_2' not in st.session_state:
        st.session_state.sort_criteria_2 = 'elemento_key'
    if 'sort_values_order_1' not in st.session_state:
        st.session_state.sort_values_order_1 = []
    if 'sort_values_order_2' not in st.session_state:
        st.session_state.sort_values_order_2 = []
    
    # 1º Critério
    col_crit1, col_vals1 = st.columns([1, 2])
    
    with col_crit1:
        if has_prefixes:
            sort1_options = {k: v for k, v in sort_columns_available.items() if k != 'des_num'}
            st.caption("⚠️ DES_NUM tem prefixos")
        else:
            sort1_options = sort_columns_available
        
        default_idx_1 = list(sort1_options.keys()).index(st.session_state.sort_criteria_1) if st.session_state.sort_criteria_1 in sort1_options else 0
        
        sort1_col = st.selectbox(
            "1º Critério", 
            list(sort1_options.keys()),
            format_func=lambda x: sort1_options[x],
            index=default_idx_1,
            key="sort1_select"
        )
        st.session_state.sort_criteria_1 = sort1_col
    
    with col_vals1:
        if sort1_col in filtered_df.columns:
            unique_vals_1 = sorted(filtered_df[sort1_col].dropna().unique().tolist())
            if unique_vals_1:
                if set(st.session_state.sort_values_order_1) != set(unique_vals_1):
                    st.session_state.sort_values_order_1 = unique_vals_1
                
                st.caption("📋 Ordem (selecione na ordem desejada):")
                new_order_1 = st.multiselect(
                    "Valores 1º critério",
                    options=unique_vals_1,
                    default=st.session_state.sort_values_order_1,
                    key="order_vals_1",
                    label_visibility="collapsed"
                )
                if new_order_1:
                    remaining = [v for v in unique_vals_1 if v not in new_order_1]
                    st.session_state.sort_values_order_1 = new_order_1 + remaining
    
    # 2º Critério
    col_crit2, col_vals2 = st.columns([1, 2])
    
    with col_crit2:
        sort2_options = {"": "(nenhum)"} | {k: v for k, v in sort_columns_available.items() if k != sort1_col}
        
        if st.session_state.sort_criteria_2 in sort2_options:
            default_idx_2 = list(sort2_options.keys()).index(st.session_state.sort_criteria_2)
        else:
            default_idx_2 = 0
        
        sort2_col = st.selectbox(
            "2º Critério",
            list(sort2_options.keys()),
            format_func=lambda x: sort2_options[x],
            index=default_idx_2,
            key="sort2_select"
        )
        st.session_state.sort_criteria_2 = sort2_col
    
    with col_vals2:
        if sort2_col and sort2_col in filtered_df.columns:
            unique_vals_2 = sorted(filtered_df[sort2_col].dropna().unique().tolist())
            if unique_vals_2:
                if set(st.session_state.sort_values_order_2) != set(unique_vals_2):
                    st.session_state.sort_values_order_2 = unique_vals_2
                
                st.caption("📋 Ordem:")
                new_order_2 = st.multiselect(
                    "Valores 2º critério",
                    options=unique_vals_2,
                    default=st.session_state.sort_values_order_2,
                    key="order_vals_2",
                    label_visibility="collapsed"
                )
                if new_order_2:
                    remaining = [v for v in unique_vals_2 if v not in new_order_2]
                    st.session_state.sort_values_order_2 = new_order_2 + remaining
    
    # Construir lista de ordenação
    sort_by = []
    if sort1_col:
        sort_by.append(sort1_col)
    if sort2_col:
        sort_by.append(sort2_col)
    
    # Aplicar ordenação ao DataFrame
    def apply_custom_sort(df, sort_cols, order1, order2):
        """Aplica ordenação personalizada ao DataFrame"""
        if not sort_cols:
            return df
        
        result_df = df.copy()
        
        # Aplicar ordenação em ordem inversa (último critério primeiro)
        for i, col in enumerate(reversed(sort_cols)):
            if col in result_df.columns:
                if i == len(sort_cols) - 1 and order1:  # 1º critério
                    order_map = {v: idx for idx, v in enumerate(order1)}
                    result_df['_sort_key'] = result_df[col].map(lambda x: order_map.get(x, 999))
                    result_df = result_df.sort_values('_sort_key', kind='stable')
                    result_df = result_df.drop('_sort_key', axis=1)
                elif i == len(sort_cols) - 2 and order2:  # 2º critério
                    order_map = {v: idx for idx, v in enumerate(order2)}
                    result_df['_sort_key'] = result_df[col].map(lambda x: order_map.get(x, 999))
                    result_df = result_df.sort_values('_sort_key', kind='stable')
                    result_df = result_df.drop('_sort_key', axis=1)
                else:
                    result_df = result_df.sort_values(col, kind='stable')
        
        return result_df
    
    # Aplicar ordenação ao filtered_df
    sorted_df = apply_custom_sort(
        filtered_df, 
        sort_by, 
        st.session_state.sort_values_order_1, 
        st.session_state.sort_values_order_2
    )
    
    # ========================================
    # TABELA (visualização ou edição)
    # ========================================
    st.markdown("---")
    
    # Rename columns for display
    display_df = sorted_df[view_cols].copy()
    display_df.columns = [all_columns.get(col, col) for col in view_cols]
    
    if not edit_mode:
        # Normal view mode - mostra tabela ordenada
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
    else:
        # Edit mode with data_editor
        st.info("📝 **Modo Edição Ativo** - Edite os campos diretamente na tabela.")
        
        # Prepare editable dataframe (usa sorted_df para manter ordenação)
        edit_df = sorted_df[edit_cols].copy()
        
        # Use data_editor for editing
        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            height=400,
            num_rows="fixed",
            key="data_editor"
        )
        
        # Botões de guardar
        col_save1, col_save2, col_save3 = st.columns(3)
        
        with col_save1:
            if st.button("💾 Guardar na DB", use_container_width=True, type="primary"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    updated_count = 0
                    layout_updated_count = 0
                    
                    for idx, row in edited_df.iterrows():
                        old_layout_name = str(row['layout_name']) if pd.notna(row['layout_name']) else ''
                        new_des_num = str(row.get('des_num', '')) if pd.notna(row.get('des_num')) else ''
                        new_r = str(row.get('r', '')) if pd.notna(row.get('r')) else ''
                        
                        cursor.execute("SELECT des_num, r FROM desenhos WHERE layout_name = ?", (old_layout_name,))
                        result = cursor.fetchone()
                        old_des_num = str(result[0]) if result and result[0] else ''
                        old_r = str(result[1]) if result and len(result) > 1 and result[1] else ''
                        
                        new_layout_name = old_layout_name
                        
                        if old_layout_name and '-' in old_layout_name:
                            parts = old_layout_name.split('-')
                            if len(parts) >= 5:
                                layout_changed = False
                                
                                if new_des_num and old_des_num != new_des_num:
                                    parts[2] = new_des_num
                                    layout_changed = True
                                
                                if old_r != new_r:
                                    if new_r and new_r != '-':
                                        if len(parts) == 5:
                                            parts.append(new_r)
                                        else:
                                            parts[5] = new_r
                                        layout_changed = True
                                    else:
                                        if len(parts) == 6:
                                            parts = parts[:5]
                                            layout_changed = True
                                
                                if layout_changed:
                                    new_layout_name = '-'.join(parts)
                                    layout_updated_count += 1
                        
                        cursor.execute("""
                            UPDATE desenhos SET
                                layout_name = ?, cliente = ?, obra = ?, localizacao = ?,
                                especialidade = ?, fase = ?, data = ?, projetou = ?,
                                des_num = ?, tipo_display = ?, elemento_key = ?,
                                elemento_titulo = ?, r = ?
                            WHERE layout_name = ?
                        """, (
                            new_layout_name, row.get('cliente', ''), row.get('obra', ''),
                            row.get('localizacao', ''), row.get('especialidade', ''),
                            row.get('fase', ''), row.get('data', ''), row.get('projetou', ''),
                            new_des_num, row.get('tipo_display', ''), row.get('elemento_key', ''),
                            row.get('elemento_titulo', ''), new_r if new_r else row.get('r', ''),
                            old_layout_name
                        ))
                        updated_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    msg = f"✅ {updated_count} registos atualizados!"
                    if layout_updated_count > 0:
                        msg += f" ({layout_updated_count} layouts renomeados)"
                    st.success(msg)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao guardar: {e}")
        
        with col_save2:
            csv_data = edited_df.to_csv(sep=';', index=False).encode('utf-8-sig')
            st.download_button(
                label="💾 Download CSV editado",
                data=csv_data,
                file_name="desenhos_editados.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # ========================================
    # EXPORTAR CSV (sempre visível)
    # ========================================
    st.markdown("---")
    st.subheader("📤 Exportar CSV para AutoCAD")
    
    # Seleção de DWG
    dwg_list = sorted_df['dwg_name'].dropna().unique().tolist() if 'dwg_name' in sorted_df.columns else []
    dwg_options = ["Todos os DWGs"] + sorted(dwg_list)
    
    col_exp_dwg, col_exp_btn = st.columns([2, 1])
    
    with col_exp_dwg:
        selected_dwg = st.selectbox("🗂️ Qual DWG exportar?", dwg_options, key="export_dwg")
    
    with col_exp_btn:
        if st.button("📤 Exportar CSV", use_container_width=True, type="primary"):
            # Obter desenhos com todas as revisões do banco de dados
            conn = get_connection()
            dwg_filter = selected_dwg if selected_dwg != "Todos os DWGs" else None
            desenhos_full = get_all_desenhos_with_revisoes(conn, dwg_filter)
            conn.close()
            
            if not desenhos_full:
                st.warning("⚠️ Nenhum desenho encontrado para exportar")
            else:
                # Converter para DataFrame com todos os 29 campos na ordem exata da LSP
                export_data = []
                for d in desenhos_full:
                    export_data.append({
                        'TAG DO LAYOUT': d.get('layout_name', ''),
                        'CLIENTE': d.get('cliente', ''),
                        'OBRA': d.get('obra', ''),
                        'LOCALIZACAO': d.get('localizacao', ''),
                        'ESPECIALIDADE': d.get('especialidade', ''),
                        'FASE': d.get('fase', ''),
                        'DATA 1ª EMISSÃO': d.get('data', ''),
                        'PROJETOU': d.get('projetou', ''),
                        'NUMERO DE DESENHO': d.get('des_num', ''),
                        'TIPO': d.get('tipo_display', ''),
                        'ELEMENTO': d.get('elemento_key', ''),
                        'TITULO': d.get('titulo', ''),
                        'REVISÃO A': d.get('rev_a', ''),
                        'DATA REVISAO A': d.get('data_a', ''),
                        'DESCRIÇÃO REVISÃO A': d.get('desc_a', ''),
                        'REVISÃO B': d.get('rev_b', ''),
                        'DATA REVISAO B': d.get('data_b', ''),
                        'DESCRIÇÃO REVISÃO B': d.get('desc_b', ''),
                        'REVISÃO C': d.get('rev_c', ''),
                        'DATA REVISAO C': d.get('data_c', ''),
                        'DESCRIÇÃO REVISÃO C': d.get('desc_c', ''),
                        'REVISÃO D': d.get('rev_d', ''),
                        'DATA REVISAO D': d.get('data_d', ''),
                        'DESCRIÇÃO REVISÃO D': d.get('desc_d', ''),
                        'REVISÃO E': d.get('rev_e', ''),
                        'DATA REVISAO E': d.get('data_e', ''),
                        'DESCRIÇÃO REVISÃO E': d.get('desc_e', ''),
                        'NOME DWG': d.get('dwg_name', ''),
                        'ID_CAD': d.get('id_cad', ''),
                        '_tipo_display': d.get('tipo_display', ''),
                        '_elemento_key': d.get('elemento_key', ''),
                        '_des_num': d.get('des_num', ''),
                    })
                
                export_df = pd.DataFrame(export_data)
                
                # Aplicar ordenação personalizada
                if sort_by:
                    sort_map = {
                        'tipo_display': '_tipo_display',
                        'elemento_key': '_elemento_key',
                        'des_num': '_des_num',
                        'layout_name': 'TAG DO LAYOUT',
                        'r': 'REVISÃO A'
                    }
                    
                    for i, col in enumerate(reversed(sort_by)):
                        export_col = sort_map.get(col, col)
                        if export_col in export_df.columns:
                            if i == len(sort_by) - 1 and st.session_state.sort_values_order_1:
                                order_map = {v: idx for idx, v in enumerate(st.session_state.sort_values_order_1)}
                                export_df['_sort_key'] = export_df[export_col].map(lambda x: order_map.get(x, 999))
                                export_df = export_df.sort_values('_sort_key', kind='stable')
                                export_df = export_df.drop('_sort_key', axis=1)
                            elif i == len(sort_by) - 2 and st.session_state.sort_values_order_2:
                                order_map = {v: idx for idx, v in enumerate(st.session_state.sort_values_order_2)}
                                export_df['_sort_key'] = export_df[export_col].map(lambda x: order_map.get(x, 999))
                                export_df = export_df.sort_values('_sort_key', kind='stable')
                                export_df = export_df.drop('_sort_key', axis=1)
                            else:
                                export_df = export_df.sort_values(export_col, kind='stable')
                
                # Remover colunas internas
                export_df = export_df.drop(['_tipo_display', '_elemento_key', '_des_num'], axis=1, errors='ignore')
                
                # Save to output folder
                output_filename = f"ALTERACOES_PARA_AUTOCAD_{selected_dwg.replace(' ', '_')}.csv" if selected_dwg != "Todos os DWGs" else "ALTERACOES_PARA_AUTOCAD.csv"
                output_path = Path(f"output/{output_filename}")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                export_df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
                
                dwg_info = f" (DWG: {selected_dwg})" if selected_dwg != "Todos os DWGs" else ""
                sort_info = f" | Ordenado por: {', '.join([sort_columns_available.get(c, c) for c in sort_by])}" if sort_by else ""
                st.success(f"✅ CSV exportado: {output_path} ({len(export_df)} desenhos){dwg_info}{sort_info}")
    
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
