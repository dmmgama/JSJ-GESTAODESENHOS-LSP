# _REF_ROADMAP — Fases e Tarefas

## Estado Atual
| Campo | Valor |
|-------|-------|
| **Versão** | V35.1 |
| **Fase** | 2 — Produtividade |
| **Tarefa** | 2.2 — Verificar Escala Viewport (próxima) |
| **Blockers** | Nenhum |

---

## FASE 1: Fundações (Single DWG) ✅ COMPLETA
**Objetivo:** Motor básico infalível num só ficheiro.

| ID | Tarefa | Prio | Estado |
|----|--------|------|--------|
| 1.0 | Reorganizar menus | Alta | ✅ |
| 1.1 | Validar DES_NUM duplicados | Alta | ✅ |
| 1.2 | Coluna DWG_SOURCE no CSV | Alta | ✅ |
| 1.3 | Auto-calcular atributo R | Média | ✅ |
| 1.4 | Sanity: Data Rev B > Rev A | Média | ✅ |
| 1.5 | Logging (.log) | Baixa | ✅ |

---

## FASE 2: Produtividade (Single DWG Advanced)
**Objetivo:** Funcionalidades de valor para Engenheiro.

| ID | Tarefa | Prio | Estado |
|----|--------|------|--------|
| 2.1 | "Emitir Revisão" (congela A → abre B) | Alta | ✅ |
| 2.2 | Verificar escala Viewport vs Legenda | Média | ⬜ |
| 2.3 | Batch Rename: Tab = DES_NUM_TIPO | Média | ⬜ |
| 2.4 | Relatório de Desenhos | Baixa | ⬜ |

---

## FASE 3: Enterprise (Multi-DWG + Excel)
**Objetivo:** Integração com LPP.xlsx

| ID | Tarefa | Prio | Estado |
|----|--------|------|--------|
| 3.1 | Definir ID único (GUID vs Chave) | Alta | ⬜ |
| 3.2 | Leitura Excel (ActiveX/Python) | Alta | ⬜ |
| 3.3 | Filtrar LPP por DWG aberto | Alta | ⬜ |
| 3.4 | Sync bidirecional DWG ↔ Excel | Alta | ⬜ |
| 3.5 | Lock/Conflict detection | Média | ⬜ |

---

## Alterações Extra (não previstas inicialmente)

### UX / Navegação
| ID | Descrição | Versão | Estado |
|----|-----------|--------|--------|
| X.1 | Modo Navegação (opção 9) - ver layouts sem sair do menu | V35 | ✅ |
| X.2 | Restaurar textscr para menus visíveis em caixa separada | V35 | ✅ |
| X.3 | Remover opção Revisão de "Alterar Desenho Individual" (obsoleta) | V35.1 | ✅ |

### Correções de Bugs
| ID | Descrição | Versão | Estado |
|----|-----------|--------|--------|
| B.1 | Fix crash ProcessManualReview com lista vazia | V33 | ✅ |
| B.2 | Fix atributo R mostrar letra (A-E) em vez do valor do campo | V33 | ✅ |
| B.3 | Fix validação de data em tempo real ao adicionar revisão | V33 | ✅ |
| B.4 | Fix logging - apenas alterações em legendas, utilizador default "JSJ" | V33.1 | ✅ |

### Melhorias Emitir Revisão
| ID | Descrição | Versão | Estado |
|----|-----------|--------|--------|
| E.1 | Unificar TODOS e seleção (1,3,5 ou 2-5 ou 1,3-5,8) | V33.2 | ✅ |
| E.2 | Data automática (hoje) como default | V33.2 | ✅ |

---

## Regras de Progressão
1. Concluir Fase N antes de iniciar Fase N+1
2. Tarefas Alta antes de Média/Baixa
3. Testar cada tarefa antes de marcar ✅
