"""
Test script for db_projects.py multi-project functionality

Run this to:
1. Initialize multi-project support (migrate DB)
2. Test CRUD operations
3. Verify everything works

Usage:
    python test_multiproject.py
"""
from db_projects import (
    inicializar_multiproject,
    get_all_projetos,
    upsert_projeto,
    get_projeto_by_num,
    get_projeto_stats,
    get_connection
)


def test_migration():
    """Test 1: Database migration"""
    print("\n" + "="*50)
    print("TEST 1: Database Migration")
    print("="*50)
    
    result = inicializar_multiproject()
    
    if result['success']:
        print("✅ Migration successful!")
    else:
        print(f"❌ Migration failed: {result.get('error')}")
        return False
    
    return True


def test_crud_projetos():
    """Test 2: CRUD operations on projetos"""
    print("\n" + "="*50)
    print("TEST 2: CRUD Operations on Projetos")
    print("="*50)
    
    conn = get_connection()
    
    # Create test project
    print("\n1. Creating test project...")
    projeto_data = {
        'proj_num': '999',
        'proj_nome': 'TESTE MULTI-PROJETO',
        'cliente': 'CLIENTE TESTE',
        'obra': 'OBRA TESTE',
        'localizacao': 'LISBOA',
        'especialidade': 'ESTRUTURAS',
        'projetou': 'TESTE'
    }
    
    projeto_id = upsert_projeto(conn, projeto_data)
    print(f"   ✓ Created project ID: {projeto_id}")
    
    # Retrieve project
    print("\n2. Retrieving project by num...")
    projeto = get_projeto_by_num(conn, '999')
    
    if projeto:
        print(f"   ✓ Found project: {projeto['proj_nome']}")
        print(f"     Cliente: {projeto['cliente']}")
        print(f"     Obra: {projeto['obra']}")
    else:
        print("   ❌ Project not found!")
        conn.close()
        return False
    
    # Update project
    print("\n3. Updating project...")
    projeto_data['proj_nome'] = 'TESTE ATUALIZADO'
    projeto_data['cliente'] = 'NOVO CLIENTE'
    upsert_projeto(conn, projeto_data)
    
    projeto = get_projeto_by_num(conn, '999')
    if projeto['proj_nome'] == 'TESTE ATUALIZADO':
        print(f"   ✓ Project updated successfully")
        print(f"     Novo nome: {projeto['proj_nome']}")
        print(f"     Novo cliente: {projeto['cliente']}")
    else:
        print("   ❌ Update failed!")
        conn.close()
        return False
    
    # List all projects
    print("\n4. Listing all projects...")
    projetos = get_all_projetos(conn)
    print(f"   ✓ Total projects in DB: {len(projetos)}")
    for p in projetos:
        print(f"     - {p['proj_num']}: {p['proj_nome']}")
    
    # Get stats
    print("\n5. Getting project stats...")
    stats = get_projeto_stats(conn, '999')
    print(f"   ✓ Stats for project 999:")
    print(f"     Total desenhos: {stats['total_desenhos']}")
    print(f"     DWG sources: {stats['dwg_sources_count']}")
    
    conn.close()
    return True


def test_cleanup():
    """Test 3: Cleanup test data"""
    print("\n" + "="*50)
    print("TEST 3: Cleanup")
    print("="*50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Delete test project
    print("\nRemoving test project...")
    cursor.execute("DELETE FROM projetos WHERE proj_num = '999'")
    conn.commit()
    
    # Verify deletion
    cursor.execute("SELECT COUNT(*) FROM projetos WHERE proj_num = '999'")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("✓ Test project removed")
    else:
        print("❌ Cleanup failed!")
        conn.close()
        return False
    
    conn.close()
    return True


def main():
    """Run all tests"""
    print("\n" + "#"*50)
    print("# Multi-Project Support Test Suite")
    print("#"*50)
    
    try:
        # Test 1: Migration
        if not test_migration():
            print("\n❌ Migration test failed. Stopping.")
            return
        
        # Test 2: CRUD
        if not test_crud_projetos():
            print("\n❌ CRUD test failed. Stopping.")
            return
        
        # Test 3: Cleanup
        if not test_cleanup():
            print("\n❌ Cleanup test failed.")
            return
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        print("\nMulti-project support is ready to use.")
        print("Next step: Update csv_importer.py to use new fields.")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
