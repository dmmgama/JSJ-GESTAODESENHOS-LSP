"""
Migration script: Normalize database schema.

Removes duplicate project fields from desenhos table.
Project data (CLIENTE, OBRA, LOCALIZACAO, ESPECIALIDADE, PROJETOU) 
is now stored ONLY in projetos table, accessed via JOIN on proj_num.

Run this script ONCE after backing up the database.
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = "data/desenhos.db"
BACKUP_SUFFIX = "_backup_prenormalize"


def backup_database():
    """Create backup of database before migration."""
    db_path = Path(DB_PATH)
    if not db_path.exists():
        print("Database does not exist, nothing to migrate.")
        return False
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{db_path.stem}{BACKUP_SUFFIX}_{timestamp}.db"
    backup_path = db_path.parent / backup_name
    shutil.copy(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return True


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_projetos_have_data(conn):
    """
    Ensure all projects have data populated from desenhos.
    If a project exists but has empty fields, populate from first desenho.
    """
    cursor = conn.cursor()
    
    # Get all unique proj_num from desenhos
    cursor.execute("""
        SELECT DISTINCT proj_num FROM desenhos 
        WHERE proj_num IS NOT NULL AND proj_num != ''
    """)
    proj_nums = [row[0] for row in cursor.fetchall()]
    
    for proj_num in proj_nums:
        # Check if project exists
        cursor.execute("SELECT * FROM projetos WHERE proj_num = ?", (proj_num,))
        projeto = cursor.fetchone()
        
        if not projeto:
            # Create project from first desenho data
            cursor.execute("""
                SELECT cliente, obra, localizacao, especialidade, projetou, proj_nome
                FROM desenhos WHERE proj_num = ? LIMIT 1
            """, (proj_num,))
            desenho = cursor.fetchone()
            
            if desenho:
                cursor.execute("""
                    INSERT INTO projetos (proj_num, proj_nome, cliente, obra, localizacao, especialidade, projetou, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proj_num,
                    desenho['proj_nome'] or '',
                    desenho['cliente'] or '',
                    desenho['obra'] or '',
                    desenho['localizacao'] or '',
                    desenho['especialidade'] or '',
                    desenho['projetou'] or '',
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                print(f"  ✓ Created project: {proj_num}")
        else:
            # Project exists - check if it has empty fields that desenhos have
            if not projeto['cliente'] or not projeto['obra']:
                cursor.execute("""
                    SELECT cliente, obra, localizacao, especialidade, projetou
                    FROM desenhos WHERE proj_num = ? AND cliente != '' LIMIT 1
                """, (proj_num,))
                desenho = cursor.fetchone()
                
                if desenho:
                    cursor.execute("""
                        UPDATE projetos SET
                            cliente = COALESCE(NULLIF(cliente, ''), ?),
                            obra = COALESCE(NULLIF(obra, ''), ?),
                            localizacao = COALESCE(NULLIF(localizacao, ''), ?),
                            especialidade = COALESCE(NULLIF(especialidade, ''), ?),
                            projetou = COALESCE(NULLIF(projetou, ''), ?),
                            updated_at = ?
                        WHERE proj_num = ?
                    """, (
                        desenho['cliente'] or '',
                        desenho['obra'] or '',
                        desenho['localizacao'] or '',
                        desenho['especialidade'] or '',
                        desenho['projetou'] or '',
                        datetime.now().isoformat(),
                        proj_num
                    ))
                    print(f"  ✓ Updated project with desenho data: {proj_num}")
    
    conn.commit()


def create_new_desenhos_table(conn):
    """
    Create new desenhos table without duplicate project fields.
    """
    cursor = conn.cursor()
    
    # Check if migration already done (by checking if cliente column exists)
    cursor.execute("PRAGMA table_info(desenhos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'cliente' not in columns:
        print("  ℹ Migration already completed (cliente column not found)")
        return False
    
    # Create new table structure (without cliente, obra, localizacao, especialidade, projetou)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desenhos_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_name TEXT NOT NULL,
            dwg_name TEXT NOT NULL,
            proj_num TEXT,
            proj_nome TEXT,
            dwg_source TEXT,
            fase TEXT,
            fase_pfix TEXT,
            emissao TEXT,
            data TEXT,
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
    
    # Copy data from old table to new (excluding duplicate fields)
    cursor.execute("""
        INSERT INTO desenhos_new (
            id, layout_name, dwg_name, proj_num, proj_nome, dwg_source,
            fase, fase_pfix, emissao, data, escalas, pfix,
            tipo_display, tipo_key, elemento, titulo, elemento_titulo, elemento_key,
            des_num, r, r_data, r_desc, id_cad, raw_attributes,
            estado_interno, comentario, data_limite, responsavel,
            created_at, updated_at
        )
        SELECT 
            id, layout_name, dwg_name, proj_num, proj_nome, dwg_source,
            fase, fase_pfix, emissao, data, escalas, pfix,
            tipo_display, tipo_key, elemento, titulo, elemento_titulo, elemento_key,
            des_num, r, r_data, r_desc, id_cad, raw_attributes,
            estado_interno, comentario, data_limite, responsavel,
            created_at, updated_at
        FROM desenhos
    """)
    
    # Drop old table
    cursor.execute("DROP TABLE desenhos")
    
    # Rename new table
    cursor.execute("ALTER TABLE desenhos_new RENAME TO desenhos")
    
    # Recreate indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_layout_name ON desenhos(layout_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tipo_elemento ON desenhos(tipo_key, elemento_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_estado_interno ON desenhos(estado_interno)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_num ON desenhos(proj_num)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dwg_source ON desenhos(dwg_source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_id_cad ON desenhos(id_cad)")
    
    conn.commit()
    print("  ✓ Created new normalized desenhos table")
    return True


def verify_migration(conn):
    """Verify migration was successful."""
    cursor = conn.cursor()
    
    # Check columns
    cursor.execute("PRAGMA table_info(desenhos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    removed_cols = ['cliente', 'obra', 'localizacao', 'especialidade', 'projetou']
    still_present = [col for col in removed_cols if col in columns]
    
    if still_present:
        print(f"  ⚠ Warning: These columns still exist: {still_present}")
        return False
    
    # Check data counts
    cursor.execute("SELECT COUNT(*) FROM desenhos")
    desenhos_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM projetos")
    projetos_count = cursor.fetchone()[0]
    
    print(f"  ✓ Desenhos: {desenhos_count}")
    print(f"  ✓ Projetos: {projetos_count}")
    
    # Check all desenhos have valid proj_num in projetos
    cursor.execute("""
        SELECT COUNT(*) FROM desenhos d
        WHERE d.proj_num IS NOT NULL AND d.proj_num != ''
        AND NOT EXISTS (SELECT 1 FROM projetos p WHERE p.proj_num = d.proj_num)
    """)
    orphans = cursor.fetchone()[0]
    
    if orphans > 0:
        print(f"  ⚠ Warning: {orphans} desenhos have proj_num not in projetos table")
    else:
        print("  ✓ All desenhos have valid project references")
    
    return True


def run_migration():
    """Run the full migration."""
    print("\n" + "="*60)
    print("DATABASE NORMALIZATION MIGRATION")
    print("="*60)
    
    # Step 1: Backup
    print("\n[1/4] Creating backup...")
    if not backup_database():
        return False
    
    conn = get_connection()
    
    try:
        # Step 2: Ensure projetos have data
        print("\n[2/4] Ensuring projects have data from desenhos...")
        ensure_projetos_have_data(conn)
        
        # Step 3: Create new normalized table
        print("\n[3/4] Creating normalized desenhos table...")
        create_new_desenhos_table(conn)
        
        # Step 4: Verify
        print("\n[4/4] Verifying migration...")
        verify_migration(conn)
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nDuplicate columns removed from desenhos:")
        print("  - cliente")
        print("  - obra")  
        print("  - localizacao")
        print("  - especialidade")
        print("  - projetou")
        print("\nThese fields are now accessed via JOIN with projetos table.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Database backup is available for restore.")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
