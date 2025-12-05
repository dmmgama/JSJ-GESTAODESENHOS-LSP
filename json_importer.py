"""
JSON importer - reads JSON files from data/json_in/ and imports to database.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from db import upsert_desenho, replace_revisoes
from utils import normalize_tipo_display_to_key, normalize_elemento_to_key


def load_all_json_files(json_dir: str) -> List[Dict[str, Any]]:
    """
    Load all .json files from directory.
    
    Args:
        json_dir: Path to directory containing JSON files
        
    Returns:
        List of parsed JSON objects
    """
    json_objects = []
    json_path = Path(json_dir)
    
    if not json_path.exists():
        print(f"Warning: Directory {json_dir} does not exist")
        return json_objects
    
    for json_file in json_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                json_objects.append(data)
                print(f"Loaded: {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file.name}: {e}")
    
    return json_objects


def import_json_to_db(json_obj: Dict[str, Any], conn) -> int:
    """
    Import one JSON object into database.
    
    Args:
        json_obj: Parsed JSON with dwg_name/dwg_source and desenhos[]
        conn: Database connection
        
    Returns:
        Number of desenhos imported
    """
    # Support both dwg_name and dwg_source for backwards compatibility
    dwg_source = json_obj.get('dwg_source') or json_obj.get('dwg_name', 'UNKNOWN')
    desenhos = json_obj.get('desenhos', [])
    
    count = 0
    
    for desenho in desenhos:
        layout_name = desenho.get('layout_name', '')
        attributes = desenho.get('attributes', {})
        revisoes = desenho.get('revisoes', [])
        
        if not layout_name:
            print("Warning: Desenho without layout_name, skipping")
            continue
        
        # Extract main fields from attributes
        tipo_display = attributes.get('TIPO', '')
        tipo_key = normalize_tipo_display_to_key(tipo_display)
        
        elemento_raw = attributes.get('ELEMENTO', '')
        elemento_key = normalize_elemento_to_key(elemento_raw)
        
        # Prepare desenho data
        desenho_data = {
            'layout_name': layout_name,
            'dwg_name': dwg_source,  # Keep for DB compatibility
            'dwg_source': dwg_source,
            'cliente': attributes.get('CLIENTE', ''),
            'obra': attributes.get('OBRA', ''),
            'localizacao': attributes.get('LOCALIZACAO', ''),
            'especialidade': attributes.get('ESPECIALIDADE', ''),
            'fase': attributes.get('FASE', ''),
            'projetou': attributes.get('PROJETOU', ''),
            'escalas': attributes.get('ESCALAS', ''),
            'tipo_display': tipo_display,
            'tipo_key': tipo_key,
            'elemento_titulo': attributes.get('ELEMENTO_TITULO', ''),
            'elemento_key': elemento_key,
            'des_num': attributes.get('DES_NUM', ''),
            'r': attributes.get('R', ''),
            'data': attributes.get('DATA', ''),
            'raw_attributes': json.dumps(attributes, ensure_ascii=False)
        }
        
        # Upsert desenho
        desenho_id = upsert_desenho(conn, desenho_data)
        
        # Replace revisoes
        replace_revisoes(conn, desenho_id, revisoes)
        
        count += 1
        print(f"  Imported: {layout_name} (ID: {desenho_id})")
    
    return count


def import_all_json(json_dir: str, conn) -> Dict[str, int]:
    """
    Import all JSON files from directory into database.
    
    Args:
        json_dir: Path to directory with JSON files
        conn: Database connection
        
    Returns:
        Dictionary with stats: files_processed, desenhos_imported
    """
    json_objects = load_all_json_files(json_dir)
    
    total_desenhos = 0
    
    for json_obj in json_objects:
        count = import_json_to_db(json_obj, conn)
        total_desenhos += count
    
    return {
        'files_processed': len(json_objects),
        'desenhos_imported': total_desenhos
    }
