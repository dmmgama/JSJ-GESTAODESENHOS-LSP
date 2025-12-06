"""
Schema Migration Script - Remove obsolete columns from desenhos table

This script:
1. Backs up the current database
2. Creates a new desenhos table with the correct schema
3. Migrates all data from old table to new table
4. Replaces old table with new table

OBSOLETE COLUMNS TO REMOVE:
- dwg_name (replaced by dwg_source)
- fase, fase_pfix, emissao, data (moved to projetos table)
- tipo_key, elemento_key, elemento_titulo (not used anymore)
- raw_attributes (not needed)
- created_at, updated_at (not used)

Run with: python migrate_schema.py
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


DB_PATH = "data/desenhos.db"


def backup_database():
    """Create a backup of the database before migration."""
    backup_path = f"data/desenhos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"OK - Backup criado: {backup_path}")
    return backup_path


def migrate_desenhos_table(conn):
    """
    Migrate desenhos table to new schema.

    New schema matches db.py:30-53 exactly.
    """
    cursor = conn.cursor()

    print("\nIniciando migracao da tabela desenhos...")

    # 1. Create new table with correct schema
    print("  1/5 Criando nova tabela desenhos_new...")
    cursor.execute("""
        CREATE TABLE desenhos_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layout_name TEXT NOT NULL,
            proj_num TEXT,
            proj_nome TEXT,
            dwg_source TEXT,
            escalas TEXT,
            pfix TEXT,
            tipo_display TEXT,
            elemento TEXT,
            titulo TEXT,
            des_num TEXT,
            r TEXT,
            r_data TEXT,
            r_desc TEXT,
            id_cad TEXT,
            estado_interno TEXT DEFAULT 'projeto',
            comentario TEXT,
            data_limite TEXT,
            responsavel TEXT,
            UNIQUE(layout_name)
        )
    """)

    # 2. Copy data from old table to new table
    print("  2/5 Copiando dados da tabela antiga...")
    cursor.execute("""
        INSERT INTO desenhos_new (
            id, layout_name, proj_num, proj_nome, dwg_source,
            escalas, pfix, tipo_display, elemento, titulo,
            des_num, r, r_data, r_desc, id_cad,
            estado_interno, comentario, data_limite, responsavel
        )
        SELECT
            id, layout_name, proj_num, proj_nome,
            COALESCE(dwg_source, dwg_name) as dwg_source,  -- Use dwg_source, fallback to dwg_name
            escalas, pfix, tipo_display, elemento, titulo,
            des_num, r, r_data, r_desc, id_cad,
            estado_interno, comentario, data_limite, responsavel
        FROM desenhos
    """)

    rows_migrated = cursor.rowcount
    print(f"  OK - {rows_migrated} desenhos migrados")

    # 3. Drop old table
    print("  3/5 Removendo tabela antiga...")
    cursor.execute("DROP TABLE desenhos")

    # 4. Rename new table to desenhos
    print("  4/5 Renomeando nova tabela...")
    cursor.execute("ALTER TABLE desenhos_new RENAME TO desenhos")

    # 5. Recreate indexes
    print("  5/5 Recriando indices...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_layout_name ON desenhos(layout_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_estado_interno ON desenhos(estado_interno)
    """)

    conn.commit()
    print("OK - Migracao da tabela desenhos concluida!\n")

    return rows_migrated


def verify_migration(conn):
    """Verify that migration was successful."""
    cursor = conn.cursor()

    print("Verificando migracao...")

    # Check table structure
    cursor.execute("PRAGMA table_info(desenhos)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"  OK - Nova tabela tem {len(columns)} colunas")

    # Verify obsolete columns are gone
    obsolete = ['dwg_name', 'fase', 'fase_pfix', 'emissao', 'data',
                'tipo_key', 'elemento_key', 'elemento_titulo', 'raw_attributes',
                'created_at', 'updated_at']

    found_obsolete = [col for col in obsolete if col in column_names]
    if found_obsolete:
        print(f"  AVISO: Colunas obsoletas ainda presentes: {found_obsolete}")
        return False
    else:
        print(f"  OK - Todas as colunas obsoletas foram removidas")

    # Verify required columns exist
    required = ['id', 'layout_name', 'dwg_source', 'proj_num', 'proj_nome',
                'escalas', 'pfix', 'tipo_display', 'elemento', 'titulo',
                'des_num', 'r', 'r_data', 'r_desc', 'id_cad',
                'estado_interno', 'comentario', 'data_limite', 'responsavel']

    missing = [col for col in required if col not in column_names]
    if missing:
        print(f"  ERRO: Colunas obrigatorias em falta: {missing}")
        return False
    else:
        print(f"  OK - Todas as colunas obrigatorias existem")

    # Count rows
    cursor.execute("SELECT COUNT(*) FROM desenhos")
    count = cursor.fetchone()[0]
    print(f"  OK - Total de desenhos na nova tabela: {count}")

    return True


def main():
    """Execute migration."""
    print("=" * 60)
    print("MIGRACAO DE SCHEMA - Gestao de Desenhos")
    print("=" * 60)
    print()

    # Check if database exists
    if not Path(DB_PATH).exists():
        print(f"ERRO: Base de dados nao encontrada: {DB_PATH}")
        return

    # Backup
    backup_path = backup_database()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    try:
        # Migrate desenhos table
        rows_migrated = migrate_desenhos_table(conn)

        # Verify migration
        if verify_migration(conn):
            print()
            print("=" * 60)
            print("MIGRACAO CONCLUIDA COM SUCESSO!")
            print("=" * 60)
            print()
            print(f"Estatisticas:")
            print(f"  - Desenhos migrados: {rows_migrated}")
            print(f"  - Backup guardado em: {backup_path}")
            print()
            print("Proximos passos:")
            print("  1. Testar a aplicacao: streamlit run app_enhanced.py")
            print("  2. Testar importacao de CSV")
            print("  3. Se tudo funcionar, pode apagar o backup")
            print()
        else:
            print()
            print("AVISO: Migracao completada mas com avisos.")
            print(f"   Verifique os logs acima e o backup: {backup_path}")
            print()

    except Exception as e:
        print()
        print(f"ERRO durante migracao: {e}")
        print(f"   A base de dados NAO foi alterada.")
        print(f"   Backup disponivel em: {backup_path}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
