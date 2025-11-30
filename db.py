"""
Database connection and CRUD operations for SQLite desenhos.db
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


DB_PATH = "data/desenhos.db"


def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def criar_tabelas(conn):
    """
    Create desenhos and revisoes tables if they don't exist.
    """
    cursor = conn.cursor()
    
    # Table: desenhos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_name TEXT NOT NULL,
            dwg_name TEXT NOT NULL,
            cliente TEXT,
            obra TEXT,
            localizacao TEXT,
            especialidade TEXT,
            fase TEXT,
            projetou TEXT,
            escalas TEXT,
            tipo_display TEXT,
            tipo_key TEXT,
            elemento TEXT,
            titulo TEXT,
            elemento_titulo TEXT,
            elemento_key TEXT,
            des_num TEXT,
            r TEXT,
            r_data TEXT,
            r_desc TEXT,
            data TEXT,
            raw_attributes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(layout_name, dwg_name)
        )
    """)
    
    # Add new columns if they don't exist (for migration)
    try:
        cursor.execute("ALTER TABLE desenhos ADD COLUMN elemento TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE desenhos ADD COLUMN titulo TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE desenhos ADD COLUMN r_data TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE desenhos ADD COLUMN r_desc TEXT")
    except:
        pass
    
    # Table: revisoes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revisoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            desenho_id INTEGER NOT NULL,
            rev_code TEXT,
            rev_desc TEXT,
            rev_date TEXT,
            FOREIGN KEY (desenho_id) REFERENCES desenhos(id) ON DELETE CASCADE
        )
    """)
    
    # Index on layout_name for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_layout_name ON desenhos(layout_name)
    """)
    
    # Index on tipo_key and elemento_key for LPP generation
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tipo_elemento ON desenhos(tipo_key, elemento_key)
    """)
    
    conn.commit()


def upsert_desenho(conn, desenho_data: Dict[str, Any]) -> int:
    """
    Insert or update a desenho based on layout_name.
    
    Args:
        conn: Database connection
        desenho_data: Dictionary with desenho fields
        
    Returns:
        desenho_id of the inserted/updated record
    """
    cursor = conn.cursor()
    
    # Check if layout_name + dwg_name exists (composite key)
    cursor.execute(
        "SELECT id FROM desenhos WHERE layout_name = ? AND dwg_name = ?",
        (desenho_data['layout_name'], desenho_data.get('dwg_name', ''))
    )
    existing = cursor.fetchone()
    
    if existing:
        # UPDATE
        desenho_id = existing[0]
        cursor.execute("""
            UPDATE desenhos SET
                dwg_name = ?,
                cliente = ?,
                obra = ?,
                localizacao = ?,
                especialidade = ?,
                fase = ?,
                projetou = ?,
                escalas = ?,
                tipo_display = ?,
                tipo_key = ?,
                elemento = ?,
                titulo = ?,
                elemento_titulo = ?,
                elemento_key = ?,
                des_num = ?,
                r = ?,
                r_data = ?,
                r_desc = ?,
                data = ?,
                raw_attributes = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            desenho_data.get('dwg_name', ''),
            desenho_data.get('cliente', ''),
            desenho_data.get('obra', ''),
            desenho_data.get('localizacao', ''),
            desenho_data.get('especialidade', ''),
            desenho_data.get('fase', ''),
            desenho_data.get('projetou', ''),
            desenho_data.get('escalas', ''),
            desenho_data.get('tipo_display', ''),
            desenho_data.get('tipo_key', ''),
            desenho_data.get('elemento', ''),
            desenho_data.get('titulo', ''),
            desenho_data.get('elemento_titulo', ''),
            desenho_data.get('elemento_key', ''),
            desenho_data.get('des_num', ''),
            desenho_data.get('r', ''),
            desenho_data.get('r_data', ''),
            desenho_data.get('r_desc', ''),
            desenho_data.get('data', ''),
            desenho_data.get('raw_attributes', ''),
            datetime.now().isoformat(),
            desenho_id
        ))
    else:
        # INSERT
        cursor.execute("""
            INSERT INTO desenhos (
                layout_name, dwg_name, cliente, obra, localizacao,
                especialidade, fase, projetou, escalas, tipo_display,
                tipo_key, elemento, titulo, elemento_titulo, elemento_key, des_num,
                r, r_data, r_desc, data, raw_attributes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            desenho_data['layout_name'],
            desenho_data.get('dwg_name', ''),
            desenho_data.get('cliente', ''),
            desenho_data.get('obra', ''),
            desenho_data.get('localizacao', ''),
            desenho_data.get('especialidade', ''),
            desenho_data.get('fase', ''),
            desenho_data.get('projetou', ''),
            desenho_data.get('escalas', ''),
            desenho_data.get('tipo_display', ''),
            desenho_data.get('tipo_key', ''),
            desenho_data.get('elemento', ''),
            desenho_data.get('titulo', ''),
            desenho_data.get('elemento_titulo', ''),
            desenho_data.get('elemento_key', ''),
            desenho_data.get('des_num', ''),
            desenho_data.get('r', ''),
            desenho_data.get('r_data', ''),
            desenho_data.get('r_desc', ''),
            desenho_data.get('data', ''),
            desenho_data.get('raw_attributes', ''),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        desenho_id = cursor.lastrowid
    
    conn.commit()
    return desenho_id


def replace_revisoes(conn, desenho_id: int, revisoes_list: List[Dict[str, str]]):
    """
    Delete all existing revisoes for desenho_id and insert new ones.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        revisoes_list: List of revision dicts with keys: rev_code/rev, rev_date/data, rev_desc/desc
    """
    cursor = conn.cursor()
    
    # Delete existing revisoes
    cursor.execute("DELETE FROM revisoes WHERE desenho_id = ?", (desenho_id,))
    
    # Insert new revisoes (support both key naming conventions)
    for rev in revisoes_list:
        rev_code = rev.get('rev_code', rev.get('rev', ''))
        rev_date = rev.get('rev_date', rev.get('data', ''))
        rev_desc = rev.get('rev_desc', rev.get('desc', ''))
        
        if rev_code:  # Only insert if there's a revision code
            cursor.execute("""
                INSERT INTO revisoes (desenho_id, rev_code, rev_date, rev_desc)
                VALUES (?, ?, ?, ?)
            """, (
                desenho_id,
                rev_code,
                rev_date,
                rev_desc
            ))
    
    conn.commit()


def get_all_desenhos(conn) -> List[Dict[str, Any]]:
    """
    Get all desenhos from database.
    
    Returns:
        List of desenho dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM desenhos ORDER BY tipo_key, elemento_key, des_num")
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append(dict(row))
    
    return result


def get_desenhos_by_tipo_elemento(conn, tipo_key: str, elemento_key: str) -> List[Dict[str, Any]]:
    """
    Get desenhos filtered by tipo_key and elemento_key.
    
    Args:
        conn: Database connection
        tipo_key: Normalized TIPO key
        elemento_key: Normalized ELEMENTO key
        
    Returns:
        List of desenho dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM desenhos 
        WHERE tipo_key = ? AND elemento_key = ?
        ORDER BY des_num
    """, (tipo_key, elemento_key))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_revisoes_by_desenho_id(conn, desenho_id: int) -> List[Dict[str, Any]]:
    """
    Get all revisions for a specific desenho.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        
    Returns:
        List of revision dictionaries ordered by rev_code
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rev_code, rev_date, rev_desc 
        FROM revisoes 
        WHERE desenho_id = ?
        ORDER BY rev_code
    """, (desenho_id,))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_desenho_by_layout(conn, layout_name: str) -> Dict[str, Any]:
    """
    Get a single desenho by layout_name.
    
    Args:
        conn: Database connection
        layout_name: Name of the layout
        
    Returns:
        Desenho dictionary or None
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM desenhos WHERE layout_name = ?", (layout_name,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_dwg_list(conn) -> List[Dict[str, Any]]:
    """
    Get list of all DWG files in database with counts.
    
    Returns:
        List of dicts with dwg_name and count
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dwg_name, COUNT(*) as count 
        FROM desenhos 
        GROUP BY dwg_name 
        ORDER BY dwg_name
    """)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def delete_all_desenhos(conn) -> int:
    """
    Delete ALL desenhos and revisoes from database.
    
    Returns:
        Number of desenhos deleted
    """
    cursor = conn.cursor()
    
    # Count before delete
    cursor.execute("SELECT COUNT(*) FROM desenhos")
    count = cursor.fetchone()[0]
    
    # Delete revisoes first (foreign key)
    cursor.execute("DELETE FROM revisoes")
    
    # Delete desenhos
    cursor.execute("DELETE FROM desenhos")
    
    conn.commit()
    return count


def delete_desenhos_by_dwg(conn, dwg_name: str) -> int:
    """
    Delete all desenhos from a specific DWG file.
    
    Args:
        conn: Database connection
        dwg_name: Name of the DWG file
        
    Returns:
        Number of desenhos deleted
    """
    cursor = conn.cursor()
    
    # Get IDs of desenhos to delete
    cursor.execute("SELECT id FROM desenhos WHERE dwg_name = ?", (dwg_name,))
    ids = [row[0] for row in cursor.fetchall()]
    count = len(ids)
    
    if ids:
        # Delete revisoes for these desenhos
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f"DELETE FROM revisoes WHERE desenho_id IN ({placeholders})", ids)
        
        # Delete desenhos
        cursor.execute("DELETE FROM desenhos WHERE dwg_name = ?", (dwg_name,))
    
    conn.commit()
    return count


def get_db_stats(conn) -> Dict[str, Any]:
    """
    Get database statistics.
    
    Returns:
        Dict with total_desenhos, total_dwgs, dwg_list
    """
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM desenhos")
    total_desenhos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT dwg_name) FROM desenhos")
    total_dwgs = cursor.fetchone()[0]
    
    dwg_list = get_dwg_list(conn)
    
    return {
        'total_desenhos': total_desenhos,
        'total_dwgs': total_dwgs,
        'dwg_list': dwg_list
    }


def delete_desenhos_by_tipo(conn, tipo: str) -> int:
    """
    Delete all desenhos with a specific tipo_display.
    
    Args:
        conn: Database connection
        tipo: Value of tipo_display to delete
        
    Returns:
        Number of desenhos deleted
    """
    cursor = conn.cursor()
    
    # Get IDs of desenhos to delete
    cursor.execute("SELECT id FROM desenhos WHERE tipo_display = ?", (tipo,))
    ids = [row[0] for row in cursor.fetchall()]
    count = len(ids)
    
    if ids:
        # Delete revisoes for these desenhos
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f"DELETE FROM revisoes WHERE desenho_id IN ({placeholders})", ids)
        
        # Delete desenhos
        cursor.execute("DELETE FROM desenhos WHERE tipo_display = ?", (tipo,))
    
    conn.commit()
    return count


def delete_desenhos_by_elemento(conn, elemento: str) -> int:
    """
    Delete all desenhos with a specific elemento_key.
    
    Args:
        conn: Database connection
        elemento: Value of elemento_key to delete
        
    Returns:
        Number of desenhos deleted
    """
    cursor = conn.cursor()
    
    # Get IDs of desenhos to delete
    cursor.execute("SELECT id FROM desenhos WHERE elemento_key = ?", (elemento,))
    ids = [row[0] for row in cursor.fetchall()]
    count = len(ids)
    
    if ids:
        # Delete revisoes for these desenhos
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f"DELETE FROM revisoes WHERE desenho_id IN ({placeholders})", ids)
        
        # Delete desenhos
        cursor.execute("DELETE FROM desenhos WHERE elemento_key = ?", (elemento,))
    
    conn.commit()
    return count


def delete_desenho_by_layout(conn, layout_name: str) -> int:
    """
    Delete a single desenho by layout_name.
    
    Args:
        conn: Database connection
        layout_name: Layout name to delete
        
    Returns:
        Number of desenhos deleted (0 or 1)
    """
    cursor = conn.cursor()
    
    # Get ID of desenho to delete
    cursor.execute("SELECT id FROM desenhos WHERE layout_name = ?", (layout_name,))
    row = cursor.fetchone()
    
    if row:
        desenho_id = row[0]
        # Delete revisoes for this desenho
        cursor.execute("DELETE FROM revisoes WHERE desenho_id = ?", (desenho_id,))
        # Delete desenho
        cursor.execute("DELETE FROM desenhos WHERE id = ?", (desenho_id,))
        conn.commit()
        return 1
    
    return 0


def get_unique_tipos(conn) -> List[str]:
    """Get list of unique tipo_display values."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tipo_display FROM desenhos WHERE tipo_display IS NOT NULL AND tipo_display != '' ORDER BY tipo_display")
    return [row[0] for row in cursor.fetchall()]


def get_unique_elementos(conn) -> List[str]:
    """Get list of unique elemento_key values."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT elemento_key FROM desenhos WHERE elemento_key IS NOT NULL AND elemento_key != '' ORDER BY elemento_key")
    return [row[0] for row in cursor.fetchall()]


def get_all_layout_names(conn) -> List[str]:
    """Get list of all layout_names."""
    cursor = conn.cursor()
    cursor.execute("SELECT layout_name FROM desenhos ORDER BY layout_name")
    return [row[0] for row in cursor.fetchall()]


def get_desenho_with_revisoes(conn, desenho_id: int) -> Dict[str, Any]:
    """
    Get a desenho with all revisões A-E expanded.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        
    Returns:
        Dict with desenho fields and rev_a, data_a, desc_a through rev_e, data_e, desc_e
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM desenhos WHERE id = ?", (desenho_id,))
    row = cursor.fetchone()
    
    if not row:
        return {}
    
    desenho = dict(row)
    
    # Get revisoes
    revisoes = get_revisoes_by_desenho_id(conn, desenho_id)
    
    # Initialize all revision fields
    for letter in ['a', 'b', 'c', 'd', 'e']:
        desenho[f'rev_{letter}'] = ''
        desenho[f'data_{letter}'] = ''
        desenho[f'desc_{letter}'] = ''
    
    # Map revisoes to fields
    for rev in revisoes:
        code = rev.get('rev_code', '').upper()
        if code in ['A', 'B', 'C', 'D', 'E']:
            letter = code.lower()
            desenho[f'rev_{letter}'] = code
            desenho[f'data_{letter}'] = rev.get('rev_date', '')
            desenho[f'desc_{letter}'] = rev.get('rev_desc', '')
    
    # Extract id_cad from raw_attributes if available
    raw = desenho.get('raw_attributes', '')
    if raw:
        try:
            # raw_attributes is stored as str(dict), try to parse it
            import ast
            parsed = ast.literal_eval(raw)
            desenho['id_cad'] = parsed.get('id_cad', '')
        except:
            desenho['id_cad'] = ''
    else:
        desenho['id_cad'] = ''
    
    return desenho


def get_all_desenhos_with_revisoes(conn, dwg_name: str = None) -> List[Dict[str, Any]]:
    """
    Get all desenhos with revisões A-E expanded.
    
    Args:
        conn: Database connection
        dwg_name: Optional DWG name filter
        
    Returns:
        List of desenhos with all revision fields
    """
    cursor = conn.cursor()
    
    if dwg_name:
        cursor.execute("SELECT id FROM desenhos WHERE dwg_name = ?", (dwg_name,))
    else:
        cursor.execute("SELECT id FROM desenhos")
    
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        desenho = get_desenho_with_revisoes(conn, row['id'])
        if desenho:
            result.append(desenho)
    
    return result