"""
Script para verificar o schema da tabela desenhos.
"""
from db import get_connection

if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar schema da tabela desenhos
    cursor.execute("PRAGMA table_info(desenhos)")
    columns = cursor.fetchall()
    
    print("📋 Colunas da tabela 'desenhos':")
    print("-" * 80)
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Verificar total de desenhos
    cursor.execute("SELECT COUNT(*) FROM desenhos")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total de desenhos no banco: {total}")
    
    # Listar alguns desenhos com as colunas corretas
    cursor.execute("SELECT * FROM desenhos LIMIT 1")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM desenhos LIMIT 3")
        print("\n📋 Primeiros 3 desenhos importados:")
        print("-" * 80)
        for row in cursor.fetchall():
            print(f"ID: {row[0]} | des_num: {row[2]}")
    
    conn.close()
