"""
Database extension for multi-project support (V42+)

This module extends the existing db.py with multi-project functionality
without modifying the original file. Safe to import alongside db.py.

New features:
- projetos table for project metadata
- New columns in desenhos: proj_num, proj_nome, dwg_source, fase_pfix, emissao, pfix, id_cad
- CRUD operations for projects
- Query functions filtered by project
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from db import get_connection, DB_PATH


# ============================================
# TABLE CREATION & MIGRATION
# ============================================

def criar_tabela_projetos(conn):
    """
    Create projetos table for multi-project support.
    Safe to call multiple times (IF NOT EXISTS).
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proj_num TEXT UNIQUE NOT NULL,
            proj_nome TEXT,
            cliente TEXT,
            obra TEXT,
            localizacao TEXT,
            especialidade TEXT,
            projetou TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()


def adicionar_colunas_v42(conn):
    """
    Add V42 columns to desenhos table if they don't exist.
    Safe migration function - skips if columns already exist.
    """
    cursor = conn.cursor()
    
    migration_columns = [
        ("proj_num", "TEXT"),
        ("proj_nome", "TEXT"),
        ("dwg_source", "TEXT"),
        ("fase_pfix", "TEXT"),
        ("emissao", "TEXT"),
        ("pfix", "TEXT"),
        ("id_cad", "TEXT"),
    ]
    
    for col_name, col_type in migration_columns:
        try:
            cursor.execute(f"ALTER TABLE desenhos ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added column: {col_name}")
        except sqlite3.OperationalError:
            # Column already exists, skip
            pass
    
    conn.commit()


def criar_indices_v42(conn):
    """
    Create indexes for V42 multi-project queries.
    Safe to call multiple times (IF NOT EXISTS).
    """
    cursor = conn.cursor()
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_num ON desenhos(proj_num)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dwg_source ON desenhos(dwg_source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_id_cad ON desenhos(id_cad)")
    
    conn.commit()


def inicializar_multiproject():
    """
    Initialize all multi-project database structures.
    Call this once when upgrading to V42.
    
    Returns:
        Dict with migration status
    """
    conn = get_connection()
    
    try:
        print("\n=== Inicializando suporte multi-projeto ===")
        
        # Create projetos table
        criar_tabela_projetos(conn)
        print("✓ Tabela 'projetos' criada/verificada")
        
        # Add new columns to desenhos
        print("\nAdicionando colunas ao 'desenhos'...")
        adicionar_colunas_v42(conn)
        
        # Create indexes
        criar_indices_v42(conn)
        print("✓ Índices criados")
        
        print("\n✅ Migração concluída com sucesso!")
        
        return {
            'success': True,
            'message': 'Multi-project support initialized successfully'
        }
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()


# ============================================
# CRUD - PROJETOS
# ============================================

def upsert_projeto(conn, projeto_data: Dict[str, Any]) -> int:
    """
    Insert or update a projeto based on proj_num.
    
    Args:
        conn: Database connection
        projeto_data: Dictionary with projeto fields
          Required: proj_num
          Optional: proj_nome, cliente, obra, localizacao, especialidade, projetou
    
    Returns:
        projeto_id of the inserted/updated record
    """
    cursor = conn.cursor()
    
    # Check if proj_num exists
    cursor.execute(
        "SELECT id FROM projetos WHERE proj_num = ?",
        (projeto_data['proj_num'],)
    )
    existing = cursor.fetchone()
    
    if existing:
        # UPDATE
        projeto_id = existing[0]
        cursor.execute("""
            UPDATE projetos SET
                proj_nome = ?,
                cliente = ?,
                obra = ?,
                localizacao = ?,
                especialidade = ?,
                projetou = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            projeto_data.get('proj_nome', ''),
            projeto_data.get('cliente', ''),
            projeto_data.get('obra', ''),
            projeto_data.get('localizacao', ''),
            projeto_data.get('especialidade', ''),
            projeto_data.get('projetou', ''),
            datetime.now().isoformat(),
            projeto_id
        ))
    else:
        # INSERT
        cursor.execute("""
            INSERT INTO projetos (
                proj_num, proj_nome, cliente, obra, localizacao,
                especialidade, projetou, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            projeto_data['proj_num'],
            projeto_data.get('proj_nome', ''),
            projeto_data.get('cliente', ''),
            projeto_data.get('obra', ''),
            projeto_data.get('localizacao', ''),
            projeto_data.get('especialidade', ''),
            projeto_data.get('projetou', ''),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        projeto_id = cursor.lastrowid
    
    conn.commit()
    return projeto_id


def get_all_projetos(conn) -> List[Dict[str, Any]]:
    """
    Get all projects from database.
    
    Returns:
        List of projeto dictionaries ordered by proj_num
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projetos ORDER BY proj_num")
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


def get_projeto_by_num(conn, proj_num: str) -> Optional[Dict[str, Any]]:
    """
    Get a single projeto by proj_num.
    
    Args:
        conn: Database connection
        proj_num: Project number
    
    Returns:
        Projeto dictionary or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projetos WHERE proj_num = ?", (proj_num,))
    row = cursor.fetchone()
    
    return dict(row) if row else None


def delete_projeto(conn, proj_num: str, delete_desenhos: bool = False) -> Dict[str, Any]:
    """
    Delete a project and optionally its associated drawings.
    
    Args:
        conn: Database connection
        proj_num: Project number to delete
        delete_desenhos: If True, also delete associated desenhos
    
    Returns:
        Dict with deletion stats
    """
    cursor = conn.cursor()
    
    # Count associated desenhos
    cursor.execute("SELECT COUNT(*) FROM desenhos WHERE proj_num = ?", (proj_num,))
    desenhos_count = cursor.fetchone()[0]
    
    if desenhos_count > 0 and not delete_desenhos:
        return {
            'success': False,
            'error': f'Project has {desenhos_count} associated desenhos. Set delete_desenhos=True to force delete.',
            'desenhos_count': desenhos_count
        }
    
    # Delete associated desenhos if requested
    if delete_desenhos and desenhos_count > 0:
        # Delete revisoes first (foreign key)
        cursor.execute("""
            DELETE FROM revisoes WHERE desenho_id IN (
                SELECT id FROM desenhos WHERE proj_num = ?
            )
        """, (proj_num,))
        
        # Delete desenhos
        cursor.execute("DELETE FROM desenhos WHERE proj_num = ?", (proj_num,))
    
    # Delete project
    cursor.execute("DELETE FROM projetos WHERE proj_num = ?", (proj_num,))
    
    conn.commit()
    
    return {
        'success': True,
        'desenhos_deleted': desenhos_count if delete_desenhos else 0
    }


# ============================================
# QUERY - DESENHOS BY PROJECT
# ============================================

def get_desenhos_by_projeto(conn, proj_num: str) -> List[Dict[str, Any]]:
    """
    Get all desenhos for a specific project with project data.
    
    Args:
        conn: Database connection
        proj_num: Project number
    
    Returns:
        List of desenho dictionaries with project fields
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*,
               p.cliente,
               p.obra,
               p.localizacao,
               p.especialidade,
               p.projetou
        FROM desenhos d
        LEFT JOIN projetos p ON d.proj_num = p.proj_num
        WHERE d.proj_num = ?
        ORDER BY d.des_num
    """, (proj_num,))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_desenhos_by_dwg_source(conn, dwg_source: str) -> List[Dict[str, Any]]:
    """
    Get all desenhos from a specific DWG source file.
    Used for reconciliation (detecting deleted drawings).
    
    Args:
        conn: Database connection
        dwg_source: DWG source filename
    
    Returns:
        List of desenho dictionaries with project fields
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*,
               p.cliente,
               p.obra,
               p.localizacao,
               p.especialidade,
               p.projetou
        FROM desenhos d
        LEFT JOIN projetos p ON d.proj_num = p.proj_num
        WHERE d.dwg_source = ?
        ORDER BY d.des_num
    """, (dwg_source,))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_projeto_stats(conn, proj_num: str) -> Dict[str, Any]:
    """
    Get statistics for a project.
    
    Args:
        conn: Database connection
        proj_num: Project number
    
    Returns:
        Dict with stats (total_desenhos, dwg_sources, tipos, etc.)
    """
    cursor = conn.cursor()
    
    # Total desenhos
    cursor.execute("SELECT COUNT(*) FROM desenhos WHERE proj_num = ?", (proj_num,))
    total_desenhos = cursor.fetchone()[0]
    
    # Distinct DWG sources
    cursor.execute("SELECT COUNT(DISTINCT dwg_source) FROM desenhos WHERE proj_num = ?", (proj_num,))
    dwg_sources_count = cursor.fetchone()[0]
    
    # Tipos distribution
    cursor.execute("""
        SELECT tipo_display, COUNT(*) as count 
        FROM desenhos 
        WHERE proj_num = ? 
        GROUP BY tipo_display
    """, (proj_num,))
    tipos = {row[0]: row[1] for row in cursor.fetchall()}
    
    return {
        'proj_num': proj_num,
        'total_desenhos': total_desenhos,
        'dwg_sources_count': dwg_sources_count,
        'tipos': tipos
    }


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_unique_dwg_sources(conn, proj_num: Optional[str] = None) -> List[str]:
    """
    Get list of unique DWG sources, optionally filtered by project.
    
    Args:
        conn: Database connection
        proj_num: Optional project number filter
    
    Returns:
        List of DWG source names
    """
    cursor = conn.cursor()
    
    if proj_num:
        cursor.execute("""
            SELECT DISTINCT dwg_source 
            FROM desenhos 
            WHERE proj_num = ? AND dwg_source IS NOT NULL AND dwg_source != ''
            ORDER BY dwg_source
        """, (proj_num,))
    else:
        cursor.execute("""
            SELECT DISTINCT dwg_source 
            FROM desenhos 
            WHERE dwg_source IS NOT NULL AND dwg_source != ''
            ORDER BY dwg_source
        """)
    
    return [row[0] for row in cursor.fetchall()]


# ============================================
# MIGRATION HELPER
# ============================================

def migrate_dwg_name_to_dwg_source(conn) -> int:
    """
    Helper function to migrate existing dwg_name values to dwg_source.
    Useful for upgrading from V41 to V42.
    
    Returns:
        Number of records updated
    """
    cursor = conn.cursor()
    
    # Copy dwg_name to dwg_source where dwg_source is NULL
    cursor.execute("""
        UPDATE desenhos 
        SET dwg_source = dwg_name 
        WHERE dwg_source IS NULL OR dwg_source = ''
    """)
    
    count = cursor.rowcount
    conn.commit()
    
    return count
