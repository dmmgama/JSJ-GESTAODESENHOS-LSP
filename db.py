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
    Create desenhos, revisoes, and historico_comentarios tables if they don't exist.
    """
    cursor = conn.cursor()
    
    # Table: desenhos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_name TEXT NOT NULL,
            dwg_name TEXT NOT NULL,
            proj_num TEXT,
            proj_nome TEXT,
            cliente TEXT,
            obra TEXT,
            localizacao TEXT,
            especialidade TEXT,
            fase TEXT,
            fase_pfix TEXT,
            emissao TEXT,
            projetou TEXT,
            escalas TEXT,
            pfix TEXT,
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
            id_cad TEXT,
            raw_attributes TEXT,
            estado_interno TEXT DEFAULT 'projeto',
            comentario TEXT,
            data_limite TEXT,
            responsavel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(layout_name, dwg_name)
        )
    """)
    
    # Add new columns if they don't exist (for migration)
    new_columns = [
        ("proj_num", "TEXT"),
        ("proj_nome", "TEXT"),
        ("fase_pfix", "TEXT"),
        ("emissao", "TEXT"),
        ("pfix", "TEXT"),
        ("id_cad", "TEXT"),
        ("elemento", "TEXT"),
        ("titulo", "TEXT"),
        ("r_data", "TEXT"),
        ("r_desc", "TEXT"),
        ("estado_interno", "TEXT DEFAULT 'projeto'"),
        ("comentario", "TEXT"),
        ("data_limite", "TEXT"),
        ("responsavel", "TEXT"),
    ]
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE desenhos ADD COLUMN {col_name} {col_type}")
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
    
    # Table: historico_comentarios (para histórico de comentários internos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            desenho_id INTEGER NOT NULL,
            comentario TEXT,
            estado_anterior TEXT,
            estado_novo TEXT,
            data_limite TEXT,
            responsavel TEXT,
            autor TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    
    # Index on estado_interno for filtering
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_estado_interno ON desenhos(estado_interno)
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
                proj_num = ?,
                proj_nome = ?,
                cliente = ?,
                obra = ?,
                localizacao = ?,
                especialidade = ?,
                fase = ?,
                fase_pfix = ?,
                emissao = ?,
                projetou = ?,
                escalas = ?,
                pfix = ?,
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
                id_cad = ?,
                raw_attributes = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            desenho_data.get('dwg_name', ''),
            desenho_data.get('proj_num', ''),
            desenho_data.get('proj_nome', ''),
            desenho_data.get('cliente', ''),
            desenho_data.get('obra', ''),
            desenho_data.get('localizacao', ''),
            desenho_data.get('especialidade', ''),
            desenho_data.get('fase', ''),
            desenho_data.get('fase_pfix', ''),
            desenho_data.get('emissao', ''),
            desenho_data.get('projetou', ''),
            desenho_data.get('escalas', ''),
            desenho_data.get('pfix', ''),
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
            desenho_data.get('id_cad', ''),
            desenho_data.get('raw_attributes', ''),
            datetime.now().isoformat(),
            desenho_id
        ))
    else:
        # INSERT
        cursor.execute("""
            INSERT INTO desenhos (
                layout_name, dwg_name, proj_num, proj_nome, cliente, obra, localizacao,
                especialidade, fase, fase_pfix, emissao, projetou, escalas, pfix, tipo_display,
                tipo_key, elemento, titulo, elemento_titulo, elemento_key, des_num,
                r, r_data, r_desc, data, id_cad, raw_attributes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            desenho_data['layout_name'],
            desenho_data.get('dwg_name', ''),
            desenho_data.get('proj_num', ''),
            desenho_data.get('proj_nome', ''),
            desenho_data.get('cliente', ''),
            desenho_data.get('obra', ''),
            desenho_data.get('localizacao', ''),
            desenho_data.get('especialidade', ''),
            desenho_data.get('fase', ''),
            desenho_data.get('fase_pfix', ''),
            desenho_data.get('emissao', ''),
            desenho_data.get('projetou', ''),
            desenho_data.get('escalas', ''),
            desenho_data.get('pfix', ''),
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
            desenho_data.get('id_cad', ''),
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


# ============================================
# FUNÇÕES PARA ESTADO INTERNO E COMENTÁRIOS
# ============================================

ESTADOS_VALIDOS = ['projeto', 'needs_revision', 'built']


def update_estado_interno(conn, desenho_id: int, novo_estado: str, autor: str = None) -> bool:
    """
    Update the internal state of a desenho and log to history.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        novo_estado: New state (projeto, needs_revision, built)
        autor: Optional author of the change
        
    Returns:
        True if updated successfully
    """
    if novo_estado not in ESTADOS_VALIDOS:
        return False
    
    cursor = conn.cursor()
    
    # Get current state
    cursor.execute("SELECT estado_interno, comentario, data_limite, responsavel FROM desenhos WHERE id = ?", (desenho_id,))
    row = cursor.fetchone()
    
    if not row:
        return False
    
    estado_anterior = row[0] or 'projeto'
    
    # Only log if state changed
    if estado_anterior != novo_estado:
        # Log to history
        cursor.execute("""
            INSERT INTO historico_comentarios 
            (desenho_id, comentario, estado_anterior, estado_novo, data_limite, responsavel, autor)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            desenho_id,
            row[1],  # current comment
            estado_anterior,
            novo_estado,
            row[2],  # data_limite
            row[3],  # responsavel
            autor
        ))
    
    # Update state
    cursor.execute("""
        UPDATE desenhos SET estado_interno = ?, updated_at = ? WHERE id = ?
    """, (novo_estado, datetime.now().isoformat(), desenho_id))
    
    conn.commit()
    return True


def update_comentario_interno(
    conn, 
    desenho_id: int, 
    comentario: str, 
    data_limite: str = None, 
    responsavel: str = None,
    autor: str = None
) -> bool:
    """
    Update internal comment, deadline and responsible for a desenho.
    Logs the previous state to history.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        comentario: New comment text
        data_limite: Optional deadline date (YYYY-MM-DD)
        responsavel: Optional responsible person
        autor: Optional author of the change
        
    Returns:
        True if updated successfully
    """
    cursor = conn.cursor()
    
    # Get current values
    cursor.execute("""
        SELECT estado_interno, comentario, data_limite, responsavel 
        FROM desenhos WHERE id = ?
    """, (desenho_id,))
    row = cursor.fetchone()
    
    if not row:
        return False
    
    # Log to history if comment changed
    old_comentario = row[1] or ''
    if old_comentario != comentario:
        cursor.execute("""
            INSERT INTO historico_comentarios 
            (desenho_id, comentario, estado_anterior, estado_novo, data_limite, responsavel, autor)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            desenho_id,
            old_comentario,
            row[0],  # estado_interno stays same
            row[0],
            row[2],  # old data_limite
            row[3],  # old responsavel
            autor
        ))
    
    # Update fields
    cursor.execute("""
        UPDATE desenhos SET 
            comentario = ?, 
            data_limite = ?, 
            responsavel = ?,
            updated_at = ? 
        WHERE id = ?
    """, (comentario, data_limite, responsavel, datetime.now().isoformat(), desenho_id))
    
    conn.commit()
    return True


def update_estado_e_comentario(
    conn,
    desenho_id: int,
    estado: str = None,
    comentario: str = None,
    data_limite: str = None,
    responsavel: str = None,
    autor: str = None
) -> bool:
    """
    Update state and/or comment in one operation.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        estado: New state (optional)
        comentario: New comment (optional)
        data_limite: Deadline date (optional)
        responsavel: Responsible person (optional)
        autor: Author of change (optional)
        
    Returns:
        True if updated successfully
    """
    if estado and estado not in ESTADOS_VALIDOS:
        return False
    
    cursor = conn.cursor()
    
    # Get current values
    cursor.execute("""
        SELECT estado_interno, comentario, data_limite, responsavel 
        FROM desenhos WHERE id = ?
    """, (desenho_id,))
    row = cursor.fetchone()
    
    if not row:
        return False
    
    estado_anterior = row[0] or 'projeto'
    novo_estado = estado if estado else estado_anterior
    comentario_anterior = row[1] or ''
    novo_comentario = comentario if comentario is not None else comentario_anterior
    data_limite_anterior = row[2]
    nova_data_limite = data_limite if data_limite is not None else data_limite_anterior
    responsavel_anterior = row[3]
    novo_responsavel = responsavel if responsavel is not None else responsavel_anterior
    
    # Log to history if anything important changed
    if estado_anterior != novo_estado or comentario_anterior != novo_comentario:
        cursor.execute("""
            INSERT INTO historico_comentarios 
            (desenho_id, comentario, estado_anterior, estado_novo, data_limite, responsavel, autor)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            desenho_id,
            comentario_anterior,
            estado_anterior,
            novo_estado,
            data_limite_anterior,
            responsavel_anterior,
            autor
        ))
    
    # Update all fields
    cursor.execute("""
        UPDATE desenhos SET 
            estado_interno = ?,
            comentario = ?, 
            data_limite = ?, 
            responsavel = ?,
            updated_at = ? 
        WHERE id = ?
    """, (novo_estado, novo_comentario, nova_data_limite, novo_responsavel, 
          datetime.now().isoformat(), desenho_id))
    
    conn.commit()
    return True


def get_historico_comentarios(conn, desenho_id: int) -> List[Dict[str, Any]]:
    """
    Get comment history for a desenho.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        
    Returns:
        List of history entries, newest first
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, comentario, estado_anterior, estado_novo, data_limite, 
               responsavel, autor, created_at
        FROM historico_comentarios 
        WHERE desenho_id = ?
        ORDER BY created_at DESC
    """, (desenho_id,))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_desenhos_by_estado(conn, estado: str) -> List[Dict[str, Any]]:
    """
    Get all desenhos with a specific internal state.
    
    Args:
        conn: Database connection
        estado: State to filter by (projeto, needs_revision, built)
        
    Returns:
        List of desenho dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM desenhos 
        WHERE estado_interno = ? OR (estado_interno IS NULL AND ? = 'projeto')
        ORDER BY tipo_key, elemento_key, des_num
    """, (estado, estado))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_desenhos_em_atraso(conn) -> List[Dict[str, Any]]:
    """
    Get all desenhos with needs_revision state and past deadline.
    
    Returns:
        List of desenho dictionaries that are overdue
    """
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT * FROM desenhos 
        WHERE estado_interno = 'needs_revision' 
        AND data_limite IS NOT NULL 
        AND data_limite != ''
        AND data_limite < ?
        ORDER BY data_limite, tipo_key, elemento_key
    """, (today,))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_desenho_by_id(conn, desenho_id: int) -> Dict[str, Any]:
    """
    Get a single desenho by ID.
    
    Args:
        conn: Database connection
        desenho_id: ID of the desenho
        
    Returns:
        Desenho dictionary or None
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM desenhos WHERE id = ?", (desenho_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_stats_by_estado(conn) -> Dict[str, int]:
    """
    Get count of desenhos by each state.
    
    Returns:
        Dict with counts: {projeto: N, needs_revision: N, built: N, em_atraso: N}
    """
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    stats = {}
    
    # Count by estado
    cursor.execute("""
        SELECT COALESCE(estado_interno, 'projeto') as estado, COUNT(*) as count
        FROM desenhos
        GROUP BY COALESCE(estado_interno, 'projeto')
    """)
    for row in cursor.fetchall():
        stats[row[0]] = row[1]
    
    # Ensure all states have a value
    for estado in ESTADOS_VALIDOS:
        if estado not in stats:
            stats[estado] = 0
    
    # Count overdue
    cursor.execute("""
        SELECT COUNT(*) FROM desenhos 
        WHERE estado_interno = 'needs_revision' 
        AND data_limite IS NOT NULL 
        AND data_limite != ''
        AND data_limite < ?
    """, (today,))
    stats['em_atraso'] = cursor.fetchone()[0]
    
    return stats


def get_unique_revision_dates(conn) -> List[str]:
    """
    Get all unique revision dates from revisoes table.
    Returns dates sorted descending (most recent first).
    
    Returns:
        List of date strings in format DD-MM-YYYY
    """
    cursor = conn.cursor()
    
    # Get all unique dates from revisoes table
    cursor.execute("""
        SELECT DISTINCT rev_date 
        FROM revisoes 
        WHERE rev_date IS NOT NULL 
        AND rev_date != '' 
        AND rev_date != '-'
        ORDER BY 
            SUBSTR(rev_date, 7, 4) DESC,
            SUBSTR(rev_date, 4, 2) DESC,
            SUBSTR(rev_date, 1, 2) DESC
    """)
    
    return [row[0] for row in cursor.fetchall()]


def get_desenhos_at_date(conn, target_date: str) -> List[Dict[str, Any]]:
    """
    Get all desenhos with their latest revision as of a specific date.
    For each desenho, shows the revision that was current on that date.
    
    Args:
        conn: Database connection
        target_date: Date string in format DD-MM-YYYY
        
    Returns:
        List of desenhos with revision info at that date
    """
    cursor = conn.cursor()
    
    # Parse target date to comparable format (YYYY-MM-DD for SQLite comparison)
    try:
        parts = target_date.split('-')
        if len(parts) == 3:
            target_date_iso = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            target_date_iso = target_date
    except:
        target_date_iso = target_date
    
    # Get all desenhos
    cursor.execute("""
        SELECT d.id, d.layout_name, d.dwg_name, d.des_num, d.tipo_display, 
               d.elemento, d.elemento_key, d.titulo, d.elemento_titulo,
               d.cliente, d.obra, d.data
        FROM desenhos d
        ORDER BY d.layout_name
    """)
    
    desenhos = []
    
    for row in cursor.fetchall():
        desenho = {
            'id': row[0],
            'layout_name': row[1],
            'dwg_name': row[2],
            'des_num': row[3],
            'tipo_display': row[4],
            'elemento': row[5],
            'elemento_key': row[6],
            'titulo': row[7],
            'elemento_titulo': row[8],
            'cliente': row[9],
            'obra': row[10],
            'data': row[11],
            'r': '-',
            'r_data': '-',
            'r_desc': '-'
        }
        
        # Get the latest revision on or before the target date
        cursor.execute("""
            SELECT rev_code, rev_date, rev_desc
            FROM revisoes
            WHERE desenho_id = ?
            AND rev_date IS NOT NULL
            AND rev_date != ''
            AND rev_date != '-'
            AND (
                SUBSTR(rev_date, 7, 4) || '-' || SUBSTR(rev_date, 4, 2) || '-' || SUBSTR(rev_date, 1, 2)
            ) <= ?
            ORDER BY 
                SUBSTR(rev_date, 7, 4) DESC,
                SUBSTR(rev_date, 4, 2) DESC,
                SUBSTR(rev_date, 1, 2) DESC,
                rev_code DESC
            LIMIT 1
        """, (row[0], target_date_iso))
        
        rev_row = cursor.fetchone()
        if rev_row:
            desenho['r'] = rev_row[0]
            desenho['r_data'] = rev_row[1]
            desenho['r_desc'] = rev_row[2]
        
        # Only include desenhos that had revisions on or before this date
        # Check if desenho existed by looking at any revision <= target date
        # or if the first emission date <= target date
        first_emission_date = desenho.get('data', '')
        has_first_emission = False
        if first_emission_date and first_emission_date not in ['', '-']:
            try:
                ep = first_emission_date.split('-')
                if len(ep) == 3:
                    first_iso = f"{ep[2]}-{ep[1]}-{ep[0]}"
                    has_first_emission = first_iso <= target_date_iso
            except:
                pass
        
        if rev_row or has_first_emission:
            desenhos.append(desenho)
    
    return desenhos