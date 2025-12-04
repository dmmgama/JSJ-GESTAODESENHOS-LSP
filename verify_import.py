"""
Script para verificar os dados importados no banco de dados.
"""
from db import get_connection

if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar total de desenhos
    cursor.execute("SELECT COUNT(*) FROM desenhos")
    total = cursor.fetchone()[0]
    print(f"📊 Total de desenhos no banco: {total}")
    
    # Verificar desenhos do projeto 717
    cursor.execute("SELECT COUNT(*) FROM desenhos WHERE proj_num = '717'")
    proj_717 = cursor.fetchone()[0]
    print(f"📁 Desenhos do projeto 717: {proj_717}")
    
    # Listar alguns desenhos
    cursor.execute("""
        SELECT id, des_num, tipo, elemento, titulo, rev_atual, dwg_source 
        FROM desenhos 
        WHERE proj_num = '717'
        LIMIT 5
    """)
    
    print("\n📋 Primeiros 5 desenhos importados:")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | Rev: {row[5]} | DWG: {row[6]}")
    
    conn.close()
