# _REF_ROADMAP — Fases e Tarefas

## Estado Atual
| Campo | Valor |
|-------|-------|
| **Fase** | 1 — Fundações (COMPLETA) |
| **Tarefa** | Pronto para Fase 2 |
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
| 2.1 | "Emitir Revisão" (congela A → abre B) | Alta | ⬜ |
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

## Regras de Progressão
1. Concluir Fase N antes de iniciar Fase N+1
2. Tarefas Alta antes de Média/Baixa
3. Testar cada tarefa antes de marcar ✅
