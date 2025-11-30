"""
Streamlit app - UI for JSJ Drawing Management LPP Sync.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from db import get_connection, criar_tabelas, get_all_desenhos, get_revisoes_by_desenho_id, get_desenho_by_layout, get_dwg_list, delete_all_desenhos, delete_desenhos_by_dwg, get_db_stats, get_all_desenhos_with_revisoes
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
        st.info("📝 **Modo Edição Ativo** - Edite os campos diretamente na tabela. Ao guardar na DB, a TAG DO LAYOUT é atualizada automaticamente se o DES_NUM mudar.")
        
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
        st.subheader("📤 Exportar CSV")
        
        # Seleção de DWG
        dwg_list = filtered_df['dwg_name'].dropna().unique().tolist() if 'dwg_name' in filtered_df.columns else []
        dwg_options = ["Todos os DWGs"] + sorted(dwg_list)
        
        col_dwg, col_order = st.columns(2)
        
        with col_dwg:
            selected_dwg = st.selectbox("🗂️ Qual DWG exportar?", dwg_options, key="export_dwg")
        
        # Ordenação por múltiplos critérios
        with col_order:
            st.markdown("**📊 Ordenação (arrastar para reordenar)**")
        
        # Colunas disponíveis para ordenação
        sort_columns_available = {
            'des_num': 'Nº Desenho',
            'tipo_display': 'Tipo',
            'elemento_key': 'Elemento',
            'layout_name': 'Layout',
            'r': 'Revisão'
        }
        
        # Seleção de critérios de ordenação
        col_sort1, col_sort2, col_sort3 = st.columns(3)
        
        with col_sort1:
            sort1 = st.selectbox("1º Critério", list(sort_columns_available.values()), index=0, key="sort1")
        with col_sort2:
            sort2 = st.selectbox("2º Critério", ["(nenhum)"] + list(sort_columns_available.values()), index=0, key="sort2")
        with col_sort3:
            sort3 = st.selectbox("3º Critério", ["(nenhum)"] + list(sort_columns_available.values()), index=0, key="sort3")
        
        # Converter nomes amigáveis de volta para nomes de colunas
        name_to_col = {v: k for k, v in sort_columns_available.items()}
        
        sort_by = []
        if sort1 and sort1 in name_to_col:
            sort_by.append(name_to_col[sort1])
        if sort2 and sort2 != "(nenhum)" and sort2 in name_to_col:
            sort_by.append(name_to_col[sort2])
        if sort3 and sort3 != "(nenhum)" and sort3 in name_to_col:
            sort_by.append(name_to_col[sort3])
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # Export edited data as CSV for AutoLISP import
            if st.button("📤 Exportar CSV para AutoCAD", use_container_width=True):
                # Usar filtered_df para ter todos os campos da DB
                export_df = filtered_df.copy()
                
                # Filtrar por DWG
                if selected_dwg != "Todos os DWGs" and 'dwg_name' in export_df.columns:
                    export_df = export_df[export_df['dwg_name'] == selected_dwg]
                
                # Ordenar
                if sort_by:
                    existing_sort = [col for col in sort_by if col in export_df.columns]
                    if existing_sort:
                        export_df = export_df.sort_values(by=existing_sort)
                
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
                            'ELEMENTO': d.get('elemento', ''),
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
                        })
                    
                    export_df = pd.DataFrame(export_data)
                    
                    # Ordenar se especificado
                    if sort_by:
                        # Mapear colunas internas para colunas de export
                        sort_map = {
                            'layout_name': 'TAG DO LAYOUT',
                            'tipo_display': 'TIPO',
                            'des_num': 'NUMERO DE DESENHO',
                            'elemento': 'ELEMENTO',
                            'titulo': 'TITULO',
                            'dwg_name': 'NOME DWG',
                            'r': 'REVISÃO A'  # Fallback para revisão
                        }
                        export_sort = [sort_map.get(col, col) for col in sort_by if sort_map.get(col) in export_df.columns]
                        if export_sort:
                            export_df = export_df.sort_values(by=export_sort)
                    
                    # Save to output folder
                    output_filename = f"ALTERACOES_PARA_AUTOCAD_{selected_dwg.replace(' ', '_')}.csv" if selected_dwg != "Todos os DWGs" else "ALTERACOES_PARA_AUTOCAD.csv"
                    output_path = Path(f"output/{output_filename}")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    export_df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
                    
                    dwg_info = f" (DWG: {selected_dwg})" if selected_dwg != "Todos os DWGs" else ""
                    sort_info = f" | Ordenado por: {', '.join([sort_columns_available[c] for c in sort_by])}" if sort_by else ""
                    st.success(f"✅ CSV exportado para: {output_path} ({len(export_df)} desenhos){dwg_info}{sort_info}")
                    st.info("💡 Formato: 29 campos no formato exato da LSP (compatível com importação)")
        
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
                    
                    updated_count = 0
                    layout_updated_count = 0
                    
                    for idx, row in edited_df.iterrows():
                        old_layout_name = str(row['layout_name']) if pd.notna(row['layout_name']) else ''
                        new_des_num = str(row.get('des_num', '')) if pd.notna(row.get('des_num')) else ''
                        new_r = str(row.get('r', '')) if pd.notna(row.get('r')) else ''
                        
                        # Buscar valores originais da DB
                        cursor.execute("SELECT des_num, r FROM desenhos WHERE layout_name = ?", (old_layout_name,))
                        result = cursor.fetchone()
                        old_des_num = str(result[0]) if result and result[0] else ''
                        old_r = str(result[1]) if result and len(result) > 1 and result[1] else ''
                        
                        # Reconstruir layout_name se DES_NUM ou R mudaram
                        # Formato LSP: "[NumProj]"-"EST"-(DES_NUM)-"PE"-"E[NumEmissao]"-(R)
                        # Com R:    669-EST-01-PE-E00-D   (6 partes)
                        # Sem R:    669-EST-01-PE-E00     (5 partes)
                        new_layout_name = old_layout_name
                        
                        if old_layout_name and '-' in old_layout_name:
                            parts = old_layout_name.split('-')
                            # Mínimo 5 partes: NumProj-EST-DES_NUM-PE-E00
                            if len(parts) >= 5:
                                # parts[0] = NUMPROJETO (669)
                                # parts[1] = EST (especialidade)
                                # parts[2] = DES_NUM (01, 02, FUN01, etc)
                                # parts[3] = PE (fase)
                                # parts[4] = E00 (emissão)
                                # parts[5] = R (D) - OPCIONAL, pode não existir
                                
                                layout_changed = False
                                
                                # Atualizar DES_NUM (posição 2)
                                if new_des_num and old_des_num != new_des_num:
                                    parts[2] = new_des_num
                                    layout_changed = True
                                
                                # Atualizar R - lógica igual à LSP
                                if old_r != new_r:
                                    if new_r and new_r != '-':
                                        # Tem revisão nova: adicionar ou substituir
                                        if len(parts) == 5:
                                            # Não tinha R, adicionar
                                            parts.append(new_r)
                                        else:
                                            # Tinha R, substituir
                                            parts[5] = new_r
                                        layout_changed = True
                                    else:
                                        # R vazio ou "-": remover se existir
                                        if len(parts) == 6:
                                            parts = parts[:5]  # Remover R
                                            layout_changed = True
                                
                                if layout_changed:
                                    new_layout_name = '-'.join(parts)
                                    layout_updated_count += 1
                        
                        # Atualizar todos os campos incluindo layout_name
                        cursor.execute("""
                            UPDATE desenhos SET
                                layout_name = ?,
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
                            new_layout_name,
                            row.get('cliente', ''),
                            row.get('obra', ''),
                            row.get('localizacao', ''),
                            row.get('especialidade', ''),
                            row.get('fase', ''),
                            row.get('data', ''),
                            row.get('projetou', ''),
                            new_des_num,
                            row.get('tipo_display', ''),
                            row.get('elemento_key', ''),
                            row.get('elemento_titulo', ''),
                            new_r if new_r else row.get('r', ''),
                            old_layout_name
                        ))
                        updated_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    msg = f"✅ {updated_count} registos atualizados na base de dados!"
                    if layout_updated_count > 0:
                        msg += f"\n📋 {layout_updated_count} TAGs de Layout atualizadas (DES_NUM ou R alterados)"
                    st.success(msg)
                    st.rerun()  # Recarregar para mostrar novos layout_names
                    
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
