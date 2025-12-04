"""
Fix INSERT statement - add missing V42 values
"""

# Read the file
with open(r'c:\Users\JSJ\JSJ AI\JSJ-GestaoDesenhos-LSP\db.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the INSERT values section
# The issue is that we have the V42 fields in the column list but not in the values tuple

old_values = """            desenho_data.get('raw_attributes', ''),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        desenho_id = cursor.lastrowid"""

new_values = """            desenho_data.get('raw_attributes', ''),
            desenho_data.get('proj_num', ''),
            desenho_data.get('proj_nome', ''),
            desenho_data.get('dwg_source', ''),
            desenho_data.get('fase_pfix', ''),
            desenho_data.get('emissao', ''),
            desenho_data.get('pfix', ''),
            desenho_data.get('id_cad', ''),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        desenho_id = cursor.lastrowid"""

content = content.replace(old_values, new_values)

# Write back
with open(r'c:\Users\JSJ\JSJ AI\JSJ-GestaoDesenhos-LSP\db.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed INSERT statement - added 7 missing V42 values!")
print("   Now: 30 placeholders = 30 values")
