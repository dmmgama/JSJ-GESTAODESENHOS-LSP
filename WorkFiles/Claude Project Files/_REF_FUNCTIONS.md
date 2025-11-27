# _REF_FUNCTIONS — Funções LISP (V29)

## Ficheiro: `JSJ-GestaoDesenhosV0.lsp`

### Menu Principal: `c:GESTAODESENHOSJSJ`
| Opção | Função | Descrição |
|-------|--------|-----------|
| 1 | `Run_MasterImport_Menu` | Submenu: JSON, Campos Gerais, Numerar |
| 2 | `Run_GlobalVars_Selective_V29` | Alterar campo (global/seleção) |
| 3 | `Run_GenerateCSV` | Exportar → CSV |
| 4 | `Run_ImportCSV` | Importar ← CSV |
| 5 | `Run_ImportExcel_Flexible` | Legacy (→ CSV) |
| 6 | `Run_GenerateLayouts_FromTemplate_V26` | Criar layouts do TEMPLATE |
| 7 | `Run_SortLayouts_Engine` | Ordenar tabs |

### Submenu Opção 1: `Run_MasterImport_Menu`
| Sub | Função | Descrição |
|-----|--------|-----------|
| 1 | `ProcessJSONImport` | Importar de JSON |
| 2 | `ProcessGlobalVariables` | Definir campos globais |
| 3 | `ProcessManualReview` | Editar desenho individual |
| 4 | `AutoNumberByType` | Numerar por TIPO |
| 5 | `AutoNumberSequential` | Numerar sequencial |

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
