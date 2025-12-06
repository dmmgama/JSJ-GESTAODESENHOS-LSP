import os
from db import get_connection, init_db, upsert_desenho, get_desenhos_by_layout_name
from db_projects import upsert_project

db_path = "data/desenhos.db"

# Reset: Apaga BD antiga
if os.path.exists(db_path):
    os.remove(db_path)
print("BD removida.")

# Inicializa nova BD
conn = get_connection(db_path)
init_db(conn)
print("BD inicializada.")

# Mock Project
mock_project = {
    'proj_num': 999,
    'proj_nome': 'Projeto Teste',
    'cliente': 'Cliente Teste',
    'especialidade': 'ARQ',
    'fase': 'LIC',
    'fase_pfix': 'LIC',
    'obra': 'Obra Teste',
    'projetou': 'Arq. Teste',
    'localizacao': 'Lisboa'
}
upsert_project(conn, mock_project)
print("Projeto mock inserido.")

# Mock Import Desenho
mock_desenho = {
    'proj_num': 999,
    'tipo': 'ARQ',
    'elemento': 'PLANTA',
    'des_num': '001',
    'pfix': 'LIC',
    'emissao': '2025-12-06',
    'fase_pfix': 'LIC',
    'rev': '',
    'layout_name': '',
    'dwg_source': 'mock.dwg',
    'data_limite': '2025-12-31',
    'created_at': '2025-12-06',
    'updated_at': '2025-12-06',
    'titulo': 'Planta Teste',
    'id_cad': 'CAD001',
    'escalas': '1:100',
    'estado_interno': 'Novo',
    'comentario': '',
    'responsavel': 'Arq. Teste'
}
desenho_id = upsert_desenho(conn, mock_desenho)
print("Desenho mock inserido.")

# Teste de Reatividade
layout_name_inicial = get_desenhos_by_layout_name(conn, mock_desenho['layout_name'])
print(f"Layout inicial: {layout_name_inicial['layout_name'] if layout_name_inicial else 'N/A'}")

# Altera des_num e atualiza
mock_desenho['des_num'] = '002'
desenho_id = upsert_desenho(conn, mock_desenho)
layout_name_novo = get_desenhos_by_layout_name(conn, mock_desenho['layout_name'])
print(f"Layout após alteração: {layout_name_novo['layout_name'] if layout_name_novo else 'N/A'}")

conn.close()
