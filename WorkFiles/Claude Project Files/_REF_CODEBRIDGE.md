# _REF_CODEBRIDGE — Template Claude Code

## Formato de Ordem

```markdown
>_ TO CLAUDE CODE

### Contexto
[1-2 linhas: módulo/função afetada]

### Ficheiros
- `JSJ-GestaoDesenhosV0.lsp` → função `X`

### Objetivo
1. [Passo 1]
2. [Passo 2]
3. [...]

### Restrições
- [ ] Backup função antiga (sufixo _OLD) antes de alterar
- [ ] Compatível AutoCAD 2018+
- [ ] Sem bibliotecas externas sem aprovação
- [ ] Manter encoding UTF-8

### Critério de Sucesso
[Teste concreto para validar]

### Pseudo-código (se necessário)
[Estrutura lógica, NÃO código final]
```

---

## Exemplos de Uso

### Exemplo: Adicionar Validação
```markdown
>_ TO CLAUDE CODE

### Contexto
Função `Run_GenerateCSV` — adicionar validação de duplicados.

### Ficheiros
- `JSJ-GestaoDesenhosV0.lsp` → `Run_GenerateCSV`

### Objetivo
1. Antes de escrever CSV, verificar se há DES_NUM duplicados
2. Se houver, mostrar alerta com lista dos duplicados
3. Perguntar se quer continuar ou cancelar

### Restrições
- [ ] Não alterar estrutura do CSV existente
- [ ] Alerta deve listar: DES_NUM + Nome do Layout

### Critério de Sucesso
- Criar 2 layouts com DES_NUM="05"
- Executar opção 3 (Gerar CSV)
- Deve aparecer alerta a avisar do duplicado
```

### Exemplo: Nova Função
```markdown
>_ TO CLAUDE CODE

### Contexto
Criar função auxiliar para obter nome do DWG atual.

### Ficheiros
- `JSJ-GestaoDesenhosV0.lsp` → nova função `GetDWGName`

### Objetivo
1. Criar função que retorna nome do ficheiro sem path nem extensão
2. Usar `(getvar "DWGNAME")` como base

### Restrições
- [ ] Retornar só o nome (sem .dwg)
- [ ] Funcionar mesmo se ficheiro não guardado

### Critério de Sucesso
- Abrir ficheiro "Lajes_Piso1.dwg"
- `(GetDWGName)` deve retornar "Lajes_Piso1"
```

---

## Checklist Pré-Ordem
Antes de enviar ordem ao Claude Code:

- [ ] Contexto claro?
- [ ] Ficheiros identificados?
- [ ] Objetivo em passos numerados?
- [ ] Restrições definidas?
- [ ] Teste de validação concreto?
