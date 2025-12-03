# _REF_ATTRIBUTES — Dicionário de Atributos

**Versão LSP:** V39.5 - ELEMENTO_TITULO  
**Última Atualização:** 29-11-2025

## Bloco: `LEGENDA_JSJ_V1`

### Estrutura Visual
```
┌─────────────────────────────────────┐
│ TABELA REVISÕES (topo, baixo→cima) │
│ Linha 5: REV_E | DESC_E | DATA_E   │
│ Linha 4: REV_D | DESC_D | DATA_D   │
│ Linha 3: REV_C | DESC_C | DATA_C   │
│ Linha 2: REV_B | DESC_B | DATA_B   │
│ Linha 1: REV_A | DESC_A | DATA_A   │ ← Primeira revisão
├─────────────────────────────────────┤
│ CLIENTE | OBRA | LOCALIZAÇÃO       │
│ TIPO | FASE                        │
│ [ELEMENTO_TITULO] (visível)        │  ← AUTO-CALCULADO
│ DATA | ESCALAS | PROJETOU          │
│ DESENHO Nº [DES_NUM]    R: [R]     │
└─────────────────────────────────────┘
```

### Campos Globais (iguais em todos os desenhos)
| Tag | Exemplo | Editável Globalmente | Notas |
|-----|---------|---------------------|-------|
| `CLIENTE` | "ROCKBUILDING" | ✅ | |
| `OBRA` | "REABILITAÇÃO" | ✅ | |
| `LOCALIZACAO` | "LISBOA" | ✅ | |
| `ESPECIALIDADE` | "ESTRUTURAS" | ✅ | |
| `FASE` | "EXECUÇÃO" | ✅ | Menu dedicado (zerar revisões) |
| `PROJETOU` | "DAVID GAMA" | ✅ | |
| `ESCALAS` | "INDICADAS" | ✅ | |
| `DATA` | "OUTUBRO 2025" | ✅ | Data do projeto/primeira emissão |

### Campos Variáveis (podem ser globais OU específicos)
| Tag | Exemplo | Editável Globalmente | Notas |
|-----|---------|---------------------|-------|
| `TIPO` | "DIMENSIONAMENTO" | ✅ | Pode ser igual em todos (ex: "PLANTA") ou diferente por desenho |
| `ELEMENTO` | "LAJES" / "PILARES" | ✅ | Menu opção 6 dedicado. Pode ser igual (ex: "ESTRUTURAS") ou específico |

**IMPORTANTE:** Estes campos podem ter:
- **Valor global**: Ex: todos desenhos com TIPO="PLANTA" 
- **Valores diferentes**: Ex: ELEMENTO="LAJES" no Des01, ELEMENTO="PILARES" no Des02

### Campos Específicos (sempre únicos por desenho)
| Tag | Exemplo | Editável Globalmente | Notas |
|-----|---------|---------------------|-------|
| `TITULO` | "PISO 1" | ❌ | Sempre único por desenho |
| `DES_NUM` | "01", "02" | ❌ | 2 dígitos, auto-numerado |

### Nomenclatura de Ficheiros
**CRUCIAL: Nome do TAB ≠ Nome do DWG**

| Conceito | Origem | Uso | Exemplo |
|----------|--------|-----|---------|
| **Nome DWG** | Ficheiro AutoCAD | Armazenamento | `Projeto_Estruturas.dwg` |
| **Nome TAB** | Layout/Tab do AutoCAD | **Nome ficheiro export PDF/DWF** | `669-EST-01-PE-E00` |
| `DWG_SOURCE` | Nome do DWG | Campo CSV (origem) | `Projeto_Estruturas` |

**Regra de Export:**
- PDF/DWF → Nome = **Nome do TAB** (não do DWG)
- Função `UpdateTabName` calcula: `<Num_Projeto>-<Especialidade>-<DES_NUM>-<FASE>-<R><DES_NUM>`
- Exemplo: TAB `669-EST-01-PE-E00` → Export PDF: `669-EST-01-PE-E00.pdf`

> **Nota:** O DWG pode ter múltiplos TABs, cada um gera um PDF diferente.

### Sistema ELEMENTO_TITULO (V39+)
**NOVIDADE V39:** Campo calculado automaticamente

| Tag | Tipo | Regra de Cálculo | User Editável |
|-----|------|------------------|---------------|
| `ELEMENTO` | Invisível | Input manual | ✅ (Menu 6 ou opção 2) |
| `TITULO` | Invisível | Input manual | ✅ (Só individual) |
| `ELEMENTO_TITULO` | **Visível** | **AUTO-CALCULADO** | ❌ Não |

**Lógica de Cálculo:**
- Ambos preenchidos: `"<ELEMENTO> - <TITULO>"` → Ex: `"LAJES - PISO 1"`
- Só ELEMENTO: `"<ELEMENTO>"` → Ex: `"LAJES"`
- Só TITULO: `"<TITULO>"` → Ex: `"PISO 1"`
- Ambos vazios: `""`

**Função:** `UpdateElementoTitulo(handle, changedTag, newValue)`
- Chamada automaticamente quando ELEMENTO ou TITULO são alterados
- Recalcula em edições manuais, globais e CSV import

### Sistema de Revisões
**REGRA:** Tabela preenche-se de BAIXO para CIMA (A→B→C→D→E)

| Tag | Descrição | User Editável | Notas |
|-----|-----------|---------------|-------|
| `REV_A` | Letra revisão A | ✅ | |
| `DATA_A` | Data revisão A | ✅ | Formato: DD-MM-YYYY |
| `DESC_A` | Descrição revisão A | ✅ | Ex: "GERAL" |
| `REV_B` ... `REV_E` | Idem para B-E | ✅ | |
| `DATA_B` ... `DATA_E` | Idem | ✅ | |
| `DESC_B` ... `DESC_E` | Idem | ✅ | |

### Atributos Auto-Calculados
| Tag | Comportamento | User Editável | Função |
|-----|---------------|---------------|--------|
| `R` | Última revisão preenchida (A→E) | ❌ Não | `GetMaxRevision` |
| `ELEMENTO_TITULO` | `ELEMENTO - TITULO` | ❌ Não | `UpdateElementoTitulo` |

> **R:** Se REV_C existe → R="C". Auto-atualiza em emissões de revisão.

### Identificação Interna (CSV/JSON)
| Tag | Origem | Uso | Notas |
|-----|--------|-----|-------|
| Handle / `ID_CAD` | AutoCAD | Export CSV/JSON | Único dentro do DWG |
| `DWG_SOURCE` | Nome ficheiro | Export CSV | Auto-preenchido |
| `REVISAO_ATUAL` | Virtual | Export CSV | Compacta REV+DATA+DESC |

### Exemplo Real (Output JSJDIAG)
```
ESPECIALIDADE = 'ESTRUTURAS'
LOCALIZACAO = 'LISBOA'
PROJETOU = 'DAVID GAMA'
DATA = 'OUTUBRO 2025'
TIPO = 'DIMENSIONAMENTO'
FASE = 'EXECUÇÃO'
OBRA = 'REABILITAÇÃO'
CLIENTE = 'ROCKBUILDING'
ESCALAS = 'INDICADAS'
DES_NUM = '01'
TITULO = 'PISO 1'              ← Invisível (input)
ELEMENTO = ''                  ← Invisível (input)
ELEMENTO_TITULO = 'PISO 1'     ← VISÍVEL (calculado)
R = 'C'                        ← Auto-calculado
REV_A = 'A'
DATA_A = '28-11-2025'
DESC_A = 'GERAL'
REV_B = 'B'
DATA_B = '28-11-2025'
DESC_B = 'GERAL'
REV_C = 'C'
DATA_C = '28-11-2025'
DESC_C = 'nova'
REV_D = ''
REV_E = ''
```

### Exclusões CSV Export
**Não exportados (calculados ou internos):**
- `ELEMENTO_TITULO` (calculado, usa-se ELEMENTO e TITULO separados)
- `R` (calculado)
- `FASE` (interno do sistema)
- Revisões individuais `REV_A-E`, `DATA_A-E`, `DESC_A-E` (usa-se REVISAO_ATUAL)
