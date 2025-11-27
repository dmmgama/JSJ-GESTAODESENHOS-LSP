# _REF_ATTRIBUTES — Dicionário de Atributos

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
│ ESPECIALIDADE | FASE               │
│ TÍTULO                             │
│ DATA | ESCALAS | PROJETOU          │
│ DESENHO Nº [DES_NUM]    R: [R]     │
└─────────────────────────────────────┘
```

### Campos Globais (iguais em todos os desenhos)
| Tag | Exemplo | Notas |
|-----|---------|-------|
| `CLIENTE` | "ALTIS" | |
| `OBRA` | "AMPLIAÇÃO" | |
| `LOCALIZAÇÃO` | "LISBOA" | |
| `ESPECIALIDADE` | "ESTRUTURA E FUNDAÇÕES" | |
| `FASE` | "ESTUDO PRÉVIO" | |
| `PROJETOU` | "DAVID GAMA" | |
| `ESCALAS` | "INDICADAS" / "1:50" | |

### Campos Específicos (variam por desenho)
| Tag | Exemplo | Notas |
|-----|---------|-------|
| `TIPO` | "PLANTA" / "CORTE" | Tipologia |
| `TITULO` | "DIMENSIONAMENTO PISO 3" | Título único |
| `DES_NUM` | "01", "02" | 2 dígitos |
| `DATA` | "SETEMBRO 2025" | Data 1ª emissão (sem revisões) |

### Sistema de Revisões
**REGRA:** Tabela preenche-se de BAIXO para CIMA (A→B→C→D→E)

| Tag | Descrição | User Editável |
|-----|-----------|---------------|
| `REV_A` | Letra revisão A | ✅ |
| `DATA_A` | Data revisão A | ✅ |
| `DESC_A` | Descrição revisão A | ✅ |
| `REV_B` ... `REV_E` | Idem para B-E | ✅ |
| `DATA_B` ... `DATA_E` | Idem | ✅ |
| `DESC_B` ... `DESC_E` | Idem | ✅ |

### Atributo Especial
| Tag | Comportamento | User Editável |
|-----|---------------|---------------|
| `R` | **AUTO-CALCULADO** = última revisão preenchida | ❌ Não |

> Se REV_B existe → R="B". Função `GetMaxRevision` já faz isto.

### Identificação Interna
| Tag | Origem | Notas |
|-----|--------|-------|
| Handle / `ID_CAD` | AutoCAD | Único só dentro do DWG |
| `DWG_SOURCE` | **A IMPLEMENTAR** | Nome do ficheiro origem |
