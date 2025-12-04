"""
Script para importar o arquivo o.csv para o banco de dados.
"""
from csv_importer import import_single_csv
from db import get_connection

if __name__ == "__main__":
    csv_path = "ListaTipo.csv"
    
    print(f"📂 Importando arquivo: {csv_path}")
    
    conn = get_connection()
    try:
        stats = import_single_csv(csv_path, conn)
        print(f"\n✅ Importação concluída!")
        print(f"   Desenhos importados: {stats.get('desenhos_imported', 0)}")
    except Exception as e:
        print(f"\n❌ Erro durante a importação: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
