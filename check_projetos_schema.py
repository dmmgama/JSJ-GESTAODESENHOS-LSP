import sqlite3

conn = sqlite3.connect('data/desenhos.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(projetos)')

print('SCHEMA DA TABELA PROJETOS:')
print('=' * 50)

cols = cursor.fetchall()
print(f'Total de colunas: {len(cols)}\n')

for col in cols:
    print(f'{col[1]:20} {col[2]:10} NotNull={col[3]}')

conn.close()
