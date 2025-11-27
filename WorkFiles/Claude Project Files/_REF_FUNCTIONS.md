# _REF_FUNCTIONS — Funções LISP (V29)

## Ficheiro: `JSJ-GestaoDesenhosV0.lsp`

### Menu Principal: `c:GESTAODESENHOSJSJ`
| Opção | Função | Descrição |
|-------|--------|-----------|
| 1 | `Menu_ModificarLegendas` | Submenu: Alterar campos |
| 2 | `Menu_Exportar` | Submenu: CSV, JSON |
| 3 | `Menu_Importar` | Submenu: CSV, JSON |
| 4 | `Menu_GerirLayouts` | Submenu: Gerar, Ordenar, Numerar |

### Submenu 1: Modificar Legendas
| Sub | Função | Descrição |
|-----|--------|-----------|
| 1 | `Run_GlobalVars_Selective_V29` | Alterar campo (global/seleção) |
| 2 | `ProcessManualReview` | Editar desenho individual |

### Submenu 2: Exportar
| Sub | Função | Descrição |
|-----|--------|-----------|
| 1 | `Run_GenerateCSV` | Exportar → CSV |
| 2 | (placeholder) | Exportar → JSON |

### Submenu 3: Importar
| Sub | Função | Descrição |
|-----|--------|-----------|
| 1 | `Run_ImportCSV` | Importar ← CSV |
| 2 | `ProcessJSONImport` | Importar ← JSON |

### Submenu 4: Gerir Layouts
| Sub | Função | Descrição |
|-----|--------|-----------|
| 1 | `Run_GenerateLayouts_FromTemplate_V26` | Criar layouts do TEMPLATE |
| 2 | `Run_SortLayouts_Engine` | Ordenar tabs |
| 3 | `AutoNumberByType` | Numerar por TIPO |
| 4 | `AutoNumberSequential` | Numerar sequencial |

### Funções Core
| Função | Input | Output | Uso |
|--------|-------|--------|-----|
| `IsTargetBlock` | blk | T/nil | Verifica se é LEGENDA_JSJ_V1 |
| `GetAttValue` | blk, tag | string | Lê atributo |
| `UpdateSingleTag` | handle, tag, val | — | Escreve atributo |
| `GetMaxRevision` | blk | (letra data desc) | Última revisão preenchida |
| `FormatNum` | n | "01"/"02" | Formata 2 dígitos |
| `GetDrawingList` | — | lista | (handle, num, tab, tipo) ordenada |
| `GetLayoutsRaw` | doc | lista layouts | Exclui Model e TEMPLATE |
| `StrSplit` | str, delim | lista | Divide string |
| `GetDWGName` | — | string | Nome do DWG sem path/extensão |
| `FindDuplicateDES_NUM` | dataList | string/nil | Detecta DES_NUM duplicados |

### Funções de Atualização
| Função | Descrição |
|--------|-----------|
| `UpdateBlockByHandle` | Atualiza múltiplos atributos via lista de pares |
| `UpdateBlockByHandleAndData` | Atualiza campos + revisão específica |
| `ApplyGlobalValue` | Aplica valor a TODOS os desenhos |

### Funções de Comparação
| Função | Descrição |
|--------|-----------|
| `IsNumberInList` | Compara DES_NUM com lista (smart: "04" = "4") |

### Notas Técnicas
- Layout `TEMPLATE` é sempre excluído das operações
- Handles são obtidos via `vla-get-Handle`
- Atributos acedidos via `vlax-invoke blk 'GetAttributes`
