# JSJ Drawing Management System

**Sistema LISP para gestão de legendas de desenhos de estruturas em AutoCAD**

---

## 📋 Visão Geral

O **JSJ-GestaoDesenhos** é uma ferramenta AutoLISP desenvolvida para gabinetes de engenharia de estruturas que gerem projetos com múltiplos desenhos técnicos (betão armado, estrutura metálica, fundações).

O sistema automatiza a gestão de legendas em ficheiros AutoCAD com dezenas de layouts, garantindo consistência de informação e rastreabilidade de revisões.

---

## 🎯 Problema Resolvido

| Desafio | Solução JSJ |
|---------|-------------|
| Atualizar cliente/obra em 50+ layouts manualmente | Opção 2: Alteração global de campos |
| Manter tabela de revisões consistente | Sistema A→E com auto-cálculo de R |
| Criar novos desenhos com formatação correta | Opção 6: Cópia de TEMPLATE |
| Exportar lista para Excel mestre (LPP) | Opção 3: Geração de CSV |
| Sincronizar alterações do Excel para DWG | Opção 4: Importação de CSV |

---

## 🏗️ Arquitetura

### Componentes Principais

```
┌─────────────────────────────────────────────────────┐
│                   FICHEIRO .DWG                     │
├─────────────────────────────────────────────────────┤
│  Layout: TEMPLATE (base para novos desenhos)        │
│  Layout: EST_01  → Bloco LEGENDA_JSJ_V1            │
│  Layout: EST_02  → Bloco LEGENDA_JSJ_V1            │
│  Layout: EST_03  → Bloco LEGENDA_JSJ_V1            │
│  ...                                                │
└─────────────────────────────────────────────────────┘
           ↓ Export (CSV)     ↑ Import (CSV/JSON)
┌─────────────────────────────────────────────────────┐
│              EXCEL MESTRE (LPP.xlsx)                │
└─────────────────────────────────────────────────────┘
```

### Workflow Típico
1. **Setup:** Criar layout TEMPLATE com bloco `LEGENDA_JSJ_V1`
2. **Gerar:** Opção 6 copia TEMPLATE → novos layouts numerados
3. **Preencher:** Opção 2 define campos globais (cliente, obra, etc.)
4. **Exportar:** Opção 3 gera CSV para controlo externo
5. **Sincronizar:** Opção 4 importa alterações do CSV/Excel

---

## 📁 Ficheiros do Projeto

| Ficheiro | Descrição |
|----------|-----------|
| `JSJ-GestaoDesenhosV0.lsp` | Código principal LISP (V29) |
| `Legenda.dwg` | Template com bloco LEGENDA_JSJ_V1 |
| `WorkFiles/Claude Project Files/_REF_ATTRIBUTES.md` | Dicionário de atributos do bloco |
| `WorkFiles/Claude Project Files/_REF_FUNCTIONS.md` | Documentação das funções LISP |
| `WorkFiles/Claude Project Files/_REF_ROADMAP.md` | Fases de desenvolvimento |
| `WorkFiles/Claude Project Files/_REF_CODEBRIDGE.md` | Template para ordens ao Claude Code |
| `*_Lista.csv` | Ficheiros de exportação/importação |

---

## 🖥️ Menu Principal

Comando: `GESTAODESENHOSJSJ`

| Opção | Função | Descrição |
|-------|--------|-----------|
| **1** | Modificar Legendas | Submenu: importar JSON, definir globais, numerar |
| **2** | Alterar Campo | Edita um atributo em todos ou alguns desenhos |
| **3** | Gerar CSV | Exporta lista de desenhos com revisões |
| **4** | Importar CSV | Atualiza desenhos a partir de CSV editado |
| **5** | Import Excel | Legacy (redireciona para CSV) |
| **6** | Gerar Layouts | Cria N layouts a partir do TEMPLATE |
| **7** | Ordenar Layouts | Reordena tabs por TIPO ou DES_NUM |

### Submenu Opção 1
| Sub | Função |
|-----|--------|
| 1 | Importar de ficheiro JSON |
| 2 | Definir campos globais (CLIENTE, OBRA, etc.) |
| 3 | Alterar desenho individual (revisões) |
| 4 | Auto-numerar por TIPO |
| 5 | Auto-numerar sequencial |

---

## 🏷️ Sistema de Atributos

### Bloco: `LEGENDA_JSJ_V1`

#### Campos Globais (iguais em todos os desenhos)
| Tag | Exemplo |
|-----|---------|
| `CLIENTE` | "ALTIS" |
| `OBRA` | "AMPLIAÇÃO HOTEL" |
| `LOCALIZAÇÃO` | "LISBOA" |
| `ESPECIALIDADE` | "ESTRUTURA E FUNDAÇÕES" |
| `FASE` | "PROJETO DE EXECUÇÃO" |
| `PROJETOU` | "DAVID GAMA" |
| `ESCALAS` | "1:50" |

#### Campos Específicos (variam por desenho)
| Tag | Exemplo | Notas |
|-----|---------|-------|
| `TIPO` | "PLANTA" / "CORTE" | Tipologia do desenho |
| `TITULO` | "FUNDAÇÕES BLOCO A" | Título único |
| `DES_NUM` | "01", "02" | Número (2 dígitos) |
| `DATA` | "NOVEMBRO 2025" | Data primeira emissão |

#### Sistema de Revisões (A → E)
A tabela de revisões preenche-se de **baixo para cima**:

```
┌──────────────────────────────────────┐
│ REV_E │ DESC_E              │ DATA_E │  ← 5ª revisão
│ REV_D │ DESC_D              │ DATA_D │
│ REV_C │ DESC_C              │ DATA_C │
│ REV_B │ DESC_B              │ DATA_B │
│ REV_A │ DESC_A              │ DATA_A │  ← 1ª revisão
└──────────────────────────────────────┘
```

| Atributo | Editável | Notas |
|----------|----------|-------|
| `REV_A` a `REV_E` | ✅ | Letra da revisão |
| `DATA_A` a `DATA_E` | ✅ | Data da revisão |
| `DESC_A` a `DESC_E` | ✅ | Descrição/motivo |
| `R` | ❌ Auto | Última revisão ativa (calculado) |

---

## 🗺️ Roadmap

### FASE 1: Fundações (Single DWG) — **EM CURSO**
| ID | Tarefa | Estado |
|----|--------|--------|
| 1.1 | Validar DES_NUM duplicados | ⬜ |
| 1.2 | Coluna DWG_SOURCE no CSV | ⬜ |
| 1.3 | Auto-calcular atributo R | ⬜ |
| 1.4 | Validar Data Rev B > Rev A | ⬜ |
| 1.5 | Sistema de logging (.log) | ⬜ |

### FASE 2: Produtividade (Single DWG Advanced)
| ID | Tarefa | Estado |
|----|--------|--------|
| 2.1 | "Emitir Revisão" (congela A → abre B) | ⬜ |
| 2.2 | Verificar escala Viewport vs Legenda | ⬜ |
| 2.3 | Batch Rename: Tab = DES_NUM_TIPO | ⬜ |
| 2.4 | Relatório de desenhos | ⬜ |

### FASE 3: Enterprise (Multi-DWG + Excel)
| ID | Tarefa | Estado |
|----|--------|--------|
| 3.1 | Definir ID único (GUID vs Chave) | ⬜ |
| 3.2 | Leitura Excel via ActiveX/Python | ⬜ |
| 3.3 | Filtrar LPP por DWG aberto | ⬜ |
| 3.4 | Sync bidirecional DWG ↔ Excel | ⬜ |
| 3.5 | Lock/Conflict detection | ⬜ |

---

## ⚠️ Desafio Core: Problema Multi-DWG

O sistema atual funciona perfeitamente num **único ficheiro DWG**. O desafio da Fase 3 é a gestão de **múltiplos DWGs** sincronizados com um Excel mestre.

### O Problema
- **Handles AutoCAD** são únicos apenas dentro do mesmo DWG
- Ao abrir outro ficheiro, os handles podem colidir
- Não existe identificador nativo cross-file

### Soluções em Estudo
| Abordagem | Prós | Contras |
|-----------|------|---------|
| Chave composta `DWG+DES_NUM` | Simples | Quebra se renomear DWG |
| GUID em atributo oculto | Único global | Requer migração |
| Hash do path+handle | Automático | Complexo |

---

## 🤝 Como Contribuir

O desenvolvimento é feito com auxílio de **Claude Code**. Para solicitar alterações ou novas funcionalidades, use o formato definido em `_REF_CODEBRIDGE.md`:

```markdown
>_ TO CLAUDE CODE

### Contexto
[Módulo/função afetada]

### Ficheiros
- `JSJ-GestaoDesenhosV0.lsp` → função `X`

### Objetivo
1. [Passo 1]
2. [Passo 2]

### Restrições
- [ ] Backup função antiga (sufixo _OLD)
- [ ] Compatível AutoCAD 2018+
- [ ] Sem bibliotecas externas
- [ ] Manter encoding UTF-8

### Critério de Sucesso
[Teste concreto para validar]
```

### Regras de Desenvolvimento
1. Concluir Fase N antes de iniciar N+1
2. Tarefas de prioridade Alta antes de Média/Baixa
3. Testar cada funcionalidade antes de marcar como concluída
4. Manter `_REF_*.md` atualizados

---

## 📄 Licença

Projeto interno JSJ Engenharia.

---

## 📞 Contacto

Desenvolvido para gestão de projetos de estruturas.
Versão atual: **V29 — Smart Number Match**
