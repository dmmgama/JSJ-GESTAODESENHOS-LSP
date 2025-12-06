"""
CSV importer - reads CSV files from data/csv_in/ and imports to database.
Supports the 34-field "Todos os Campos" export from AutoLISP (V42+).
"""
import csv
import os
from pathlib import Path
from typing import List, Dict, Any

from db import upsert_desenho, replace_revisoes, get_connection
from db_projects import upsert_projeto
from utils import normalize_tipo_display_to_key, normalize_elemento_to_key


# Mapeamento de headers CSV para campos internos (V42 - 34 campos)
CSV_HEADER_MAP = {
    # Projeto
    'PROJ_NUM': 'proj_num',
    'PROJ_NOME': 'proj_nome',
    'TAG DO LAYOUT': 'layout_name',
    'LAYOUT': 'layout_name',
    'CLIENTE': 'cliente',
    'OBRA': 'obra',
    'LOCALIZAÇÃO': 'localizacao',
    'LOCALIZACAO': 'localizacao',
    'ESPECIALIDADE': 'especialidade',
    'PROJETOU': 'projetou',
    # Fase e Emissão
    'FASE': 'fase',
    'FASE_PFIX': 'fase_pfix',
    'EMISSAO': 'emissao',
    'EMISSÃO': 'emissao',
    'DATA': 'data',
    'DATA 1ª EMISSÃO': 'data',
    'DATA 1ª EMISSAO': 'data',
    # Desenho
    'PFIX': 'pfix',
    'NUMERO DE DESENHO': 'des_num',
    'DES_NUM': 'des_num',
    'TIPO': 'tipo_display',
    'ELEMENTO': 'elemento',
    'TITULO': 'titulo',
    'TÍTULO': 'titulo',
    # Revisões A
    'REVISÃO A': 'rev_a',
    'REVISAO A': 'rev_a',
    'REV_A': 'rev_a',
    'DATA REVISAO A': 'data_a',
    'DATA_A': 'data_a',
    'DESCRIÇÃO REVISÃO A': 'desc_a',
    'DESCRICAO REVISAO A': 'desc_a',
    'DESC_A': 'desc_a',
    # Revisões B
    'REVISÃO B': 'rev_b',
    'REVISAO B': 'rev_b',
    'REV_B': 'rev_b',
    'DATA REVISAO B': 'data_b',
    'DATA_B': 'data_b',
    'DESCRIÇÃO REVISÃO B': 'desc_b',
    'DESCRICAO REVISAO B': 'desc_b',
    'DESC_B': 'desc_b',
    # Revisões C
    'REVISÃO C': 'rev_c',
    'REVISAO C': 'rev_c',
    'REV_C': 'rev_c',
    'DATA REVISAO C': 'data_c',
    'DATA_C': 'data_c',
    'DESCRIÇÃO REVISÃO C': 'desc_c',
    'DESCRICAO REVISAO C': 'desc_c',
    'DESC_C': 'desc_c',
    # Revisões D
    'REVISÃO D': 'rev_d',
    'REVISAO D': 'rev_d',
    'REV_D': 'rev_d',
    'DATA REVISAO D': 'data_d',
    'DATA_D': 'data_d',
    'DESCRIÇÃO REVISÃO D': 'desc_d',
    'DESCRICAO REVISAO D': 'desc_d',
    'DESC_D': 'desc_d',
    # Revisões E
    'REVISÃO E': 'rev_e',
    'REVISAO E': 'rev_e',
    'REV_E': 'rev_e',
    'DATA REVISAO E': 'data_e',
    'DATA_E': 'data_e',
    'DESCRIÇÃO REVISÃO E': 'desc_e',
    'DESCRICAO REVISAO E': 'desc_e',
    'DESC_E': 'desc_e',
    # Sistema
    'NOME DWG': 'dwg_source',  # V42: usar dwg_source em vez de dwg_name
    'DWG_SOURCE': 'dwg_source',
    'ID_CAD': 'id_cad',
}


def normalize_header(header: str) -> str:
    """Normalize header name to internal field name."""
    if not header or header is None:
        return ""
    header_upper = header.strip().upper()
    return CSV_HEADER_MAP.get(header_upper, header_upper.lower())


def parse_csv_row(row: Dict[str, str], headers_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse a CSV row into a normalized dictionary.
    
    Args:
        row: Raw CSV row dictionary
        headers_map: Mapping from original headers to normalized names
        
    Returns:
        Normalized dictionary with field values
    """
    parsed = {}
    for original_header, value in row.items():
        # Skip None or empty headers
        if not original_header:
            continue
        normalized = headers_map.get(original_header, original_header.lower())
        # Safely handle None values
        parsed[normalized] = value.strip() if value is not None else ''
    return parsed


def extract_revisoes_from_row(parsed: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Extract revision data from parsed row.
    
    Args:
        parsed: Normalized row dictionary
        
    Returns:
        List of revision dictionaries
    """
    revisoes = []
    for letter in ['a', 'b', 'c', 'd', 'e']:
        rev_code = parsed.get(f'rev_{letter}', '').strip()
        rev_date = parsed.get(f'data_{letter}', '').strip()
        rev_desc = parsed.get(f'desc_{letter}', '').strip()
        
        # Only add if there's at least a revision code
        if rev_code and rev_code != '-':
            revisoes.append({
                'rev_code': rev_code,
                'rev_date': rev_date,
                'rev_desc': rev_desc
            })
    
    return revisoes


def get_max_revision(revisoes: List[Dict[str, str]]) -> Dict[str, str]:
    """Get the latest revision data from list.
    
    Returns:
        Dict with 'rev_code', 'rev_date', 'rev_desc' of latest revision
    """
    if not revisoes:
        return {'rev_code': '', 'rev_date': '', 'rev_desc': ''}
    
    last_rev = revisoes[-1]
    return {
        'rev_code': last_rev.get('rev_code', ''),
        'rev_date': last_rev.get('rev_date', ''),
        'rev_desc': last_rev.get('rev_desc', '')
    }


def load_csv_file(csv_path: str, delimiter: str = ';') -> List[Dict[str, str]]:
    """
    Load a CSV file and return list of row dictionaries.
    
    Args:
        csv_path: Path to CSV file
        delimiter: CSV delimiter (default ';')
        
    Returns:
        List of row dictionaries
    """
    rows = []
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
                print(f"Loaded {csv_path} with encoding {encoding}")
                break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error loading {csv_path}: {e}")
            return []
    
    return rows


def import_csv_to_db(csv_path: str, conn, target_proj_num: str = None) -> int:
    """
    Import one CSV file into database.
    
    Args:
        csv_path: Path to CSV file
        conn: Database connection
        target_proj_num: Optional project number to assign all drawings to (overrides CSV data)
        
    Returns:
        Number of desenhos imported
    """
    rows = load_csv_file(csv_path)
    
    if not rows:
        print(f"No data in {csv_path}")
        return 0
    
    # Build headers map from first row's keys
    first_row = rows[0]
    headers_map = {h: normalize_header(h) for h in first_row.keys()}
    
    count = 0
    
    for row in rows:
        parsed = parse_csv_row(row, headers_map)
        
        # Get layout name - required field
        layout_name = parsed.get('layout_name', '')
        if not layout_name:
            print(f"Warning: Row without layout_name, skipping")
            continue
        
        # V42+: Extract project data and auto-create/update project
        # If target_proj_num is provided, use it; otherwise use CSV data
        if target_proj_num:
            proj_num = target_proj_num
        else:
            proj_num = parsed.get('proj_num', '')
        
        # NORMALIZED: Project fields stored ONLY in projetos table
        if proj_num:
            projeto_data = {
                'proj_num': proj_num,
                'proj_nome': parsed.get('proj_nome', ''),
                'cliente': parsed.get('cliente', ''),
                'obra': parsed.get('obra', ''),
                'localizacao': parsed.get('localizacao', ''),
                'especialidade': parsed.get('especialidade', ''),
                'projetou': parsed.get('projetou', ''),
                'fase': parsed.get('fase', ''),
                'fase_pfix': parsed.get('fase_pfix', ''),
                'emissao': parsed.get('emissao', ''),
                'data': parsed.get('data', ''),
            }
            try:
                upsert_projeto(conn, projeto_data)
            except Exception as e:
                print(f"Warning: Could not upsert project {proj_num}: {e}")
        # Remove campos globais do desenho antes de inserir
        for k in ['fase', 'fase_pfix', 'emissao', 'data']:
            if k in parsed:
                parsed.pop(k)
        
        # Extract data
        dwg_source = parsed.get('dwg_source', 'UNKNOWN')
        
        tipo_display = parsed.get('tipo_display', '')
        tipo_key = normalize_tipo_display_to_key(tipo_display)
        
        elemento = parsed.get('elemento', '')
        titulo = parsed.get('titulo', '')
        elemento_titulo = f"{elemento} - {titulo}" if elemento and titulo else elemento or titulo
        elemento_key = normalize_elemento_to_key(elemento)
        
        # Extract revisoes
        revisoes = extract_revisoes_from_row(parsed)
        max_rev = get_max_revision(revisoes)
        r = max_rev['rev_code']
        r_data = max_rev['rev_date']
        r_desc = max_rev['rev_desc']
        
        # Prepare desenho data - NORMALIZED: no project fields duplicated
        # Project data (cliente, obra, localizacao, especialidade, projetou)
        # is accessed via JOIN on proj_num
        desenho_data = {
            'layout_name': layout_name,
            'dwg_name': dwg_source,  # Maintain compatibility
            'dwg_source': dwg_source,
            'id_cad': parsed.get('id_cad', ''),
            'proj_num': proj_num,
            'proj_nome': parsed.get('proj_nome', ''),
            'fase': parsed.get('fase', ''),
            'fase_pfix': parsed.get('fase_pfix', ''),
            'emissao': parsed.get('emissao', ''),
            'data': parsed.get('data', ''),
            'escalas': '',  # Not in CSV
            'pfix': parsed.get('pfix', ''),
            'des_num': parsed.get('des_num', ''),
            'tipo_display': tipo_display,
            'tipo_key': tipo_key,
            'elemento': elemento,
            'titulo': titulo,
            'elemento_titulo': elemento_titulo,
            'elemento_key': elemento_key,
            'r': r,
            'r_data': r_data,
            'r_desc': r_desc,
            'raw_attributes': str(parsed)  # Store original parsed data
        }
        
        # Upsert desenho
        desenho_id = upsert_desenho(conn, desenho_data)
        
        # Replace revisoes
        replace_revisoes(conn, desenho_id, revisoes)
        
        count += 1
        print(f"  Imported: {layout_name} (ID: {desenho_id})")
    
    return count


def import_all_csv(csv_dir: str, conn) -> Dict[str, int]:
    """
    Import all CSV files from directory into database.
    
    Args:
        csv_dir: Path to directory with CSV files
        conn: Database connection
        
    Returns:
        Dictionary with stats: files_processed, desenhos_imported
    """
    csv_path = Path(csv_dir)
    
    if not csv_path.exists():
        print(f"Warning: Directory {csv_dir} does not exist")
        csv_path.mkdir(parents=True, exist_ok=True)
        return {'files_processed': 0, 'desenhos_imported': 0}
    
    total_desenhos = 0
    files_processed = 0
    
    for csv_file in csv_path.glob("*.csv"):
        print(f"\nProcessing: {csv_file.name}")
        count = import_csv_to_db(str(csv_file), conn)
        total_desenhos += count
        files_processed += 1
    
    return {
        'files_processed': files_processed,
        'desenhos_imported': total_desenhos
    }


def import_single_csv(csv_path: str, conn, target_proj_num: str = None) -> Dict[str, int]:
    """
    Import a single CSV file into database.
    
    Args:
        csv_path: Path to CSV file
        conn: Database connection
        target_proj_num: Optional project number to assign all drawings to
        
    Returns:
        Dictionary with stats
    """
    if not Path(csv_path).exists():
        return {'files_processed': 0, 'desenhos_imported': 0, 'error': 'File not found'}
    
    count = import_csv_to_db(csv_path, conn, target_proj_num)
    
    return {
        'files_processed': 1,
        'desenhos_imported': count
    }
