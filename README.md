# JSJ Drawing Management System

**Sistema LISP para gestão de legendas de desenhos de estruturas em AutoCAD**

**Versão atual: V39.5** | Fase 2 em desenvolvimento

---

## 📋 Visão Geral

O **JSJ-GestaoDesenhos** é uma ferramenta AutoLISP desenvolvida para gabinetes de engenharia de estruturas que gerem projetos com múltiplos desenhos técnicos (betão armado, estrutura metálica, fundações).

O sistema automatiza a gestão de legendas em ficheiros AutoCAD com dezenas de layouts, garantindo consistência de informação e rastreabilidade de revisões.

---

## 🎯 Problema Resolvido

| Desafio | Solução JSJ |
|---------|-------------|
| Atualizar cliente/obra em 50+ layouts manualmente | Alteração global de campos |
| Manter tabela de revisões consistente | Sistema A→E com auto-cálculo de R |
| Emitir nova revisão em múltiplos desenhos | Emitir Revisão (TODOS ou seleção) |
| Criar novos desenhos com formatação correta | Gerar Layouts a partir de TEMPLATE |
| Exportar lista para Excel mestre (LPP) | Geração de CSV com DWG_SOURCE |
| Sincronizar alterações do Excel para DWG | Importação de CSV |

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
2. **Gerar:** Opção 4 copia TEMPLATE → novos layouts numerados
3. **Preencher:** Alterar Campo define campos globais (cliente, obra, etc.)
4. **Emitir:** Opção 1 permite emitir revisões em lote
5. **Exportar:** Gera CSV para controlo externo
6. **Sincronizar:** Importa alterações do CSV/Excel

---

## 📁 Ficheiros do Projeto

| Ficheiro | Descrição |
|----------|-----------|
| `JSJ-GestaoDesenhosV0.lsp` | Código principal LISP (V39.5) |
| `Legenda.dwg` | Template com bloco LEGENDA_JSJ_V1 |
| `WorkFiles/Claude Project Files/_REF_ATTRIBUTES.md` | Dicionário de atributos do bloco |
| `WorkFiles/Claude Project Files/_REF_FUNCTIONS.md` | Documentação das funções LISP |
| `WorkFiles/Claude Project Files/_REF_ROADMAP.md` | Fases de desenvolvimento |
| `WorkFiles/Claude Project Files/_REF_CODEBRIDGE.md` | Template para ordens ao Claude Code |
| `*_Lista.csv` | Ficheiros de exportação/importação |

---

## 🖥️ Estrutura de Menus

Comando: `GESTAODESENHOSJSJ`

### Menu Principal
| Opção | Função | Descrição |
|-------|--------|-----------|
| **1** | Modificar Legendas | Submenu com emissão de revisões e edição |
| **2** | Exportar Lista | Gera CSV com todos os desenhos |
| **3** | Importar Lista | Atualiza desenhos a partir de CSV |
| **4** | Gerir Layouts | Criar e ordenar layouts |
| **9** | Navegar | Pausa para ver layouts, ENTER volta ao menu |
| **0** | Sair | Termina o programa |

### Submenu 2: Exportar Lista
| Opção | Função | Descrição |
|-------|--------|-----------|----------|
| **1** | CSV Default | Exporta colunas standard (DWG_SOURCE, TIPO, DES_NUM, TITULO, REVISAO_ATUAL, ID_CAD) |
| **2** | CSV Customizado | Seleciona e reordena colunas (DES_NUM e ID_CAD sempre incluídos) |
| **3** | JSON | Exporta estrutura completa em JSON |
| **0** | Voltar | Regressa ao menu principal |

### Submenu 1: Modificar Legendas
| Opção | Função | Descrição |
|-------|--------|-----------|----------|
| **1** | Emitir Revisão | Nova revisão (TODOS ou seleção: 1,3,5 ou 2-5) |
| **2** | Alterar Campo | Edita atributo global ou em seleção |
| **3** | Alterar Desenho Individual | Edita TIPO/TITULO de um desenho |
| **4** | Definir Utilizador | Define nome para logging |
| **5** | Alterar Fase de Projeto | Altera fase, limpa revisões, atualiza data |
| **6** | Alterar ELEMENTO (Global) | Altera ELEMENTO em TODOS ou seleção (recalcula ELEMENTO_TITULO) |
| **9** | Navegar | Ver layouts |
| **0** | Voltar | Regressa ao menu principal |

### Submenu 4: Gerir Layouts
| Opção | Função | Descrição |
|-------|--------|-----------|
| **1** | Gerar Layouts | Cria N layouts a partir de TEMPLATE |
| **2** | Ordenar Tabs | Reordena por TIPO ou DES_NUM |
| **0** | Voltar | Regressa ao menu principal |

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

#### Campos Variáveis (podem ser globais OU específicos)
| Tag | Exemplo | Notas |
|-----|---------|-------|
| `TIPO` | "PLANTA" / "CORTE" | Tipologia do desenho |
| `ELEMENTO` | "LAJES" / "PILARES" | Elemento estrutural (invisível) |

#### Campos Específicos (sempre únicos por desenho)
| Tag | Exemplo | Notas |
|-----|---------|-------|
| `TITULO` | "PISO 1" / "FUNDAÇÕES BLOCO A" | Título único (invisível) |
| `ELEMENTO_TITULO` | "LAJES - PISO 1" | **Auto-calculado** de ELEMENTO + TITULO (visível) |
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
| `DATA_A` a `DATA_E` | ✅ | Data da revisão (DD-MM-YYYY) |
| `DESC_A` a `DESC_E` | ✅ | Descrição/motivo |
| `R` | ❌ Auto | Última revisão ativa (A-E) - calculado automaticamente |

---

## 🗺️ Roadmap

### FASE 1: Fundações (Single DWG) ✅ COMPLETA
| ID | Tarefa | Estado |
|----|--------|--------|
| 1.0 | Reorganizar menus | ✅ |
| 1.1 | Validar DES_NUM duplicados | ✅ |
| 1.2 | Coluna DWG_SOURCE no CSV | ✅ |
| 1.3 | Auto-calcular atributo R | ✅ |
| 1.4 | Validar Data Rev B > Rev A | ✅ |
| 1.5 | Sistema de logging (.log) | ✅ |

### FASE 2: Produtividade (Single DWG Advanced) — **EM CURSO**
| ID | Tarefa | Estado |
|----|--------|--------|
| 2.1 | "Emitir Revisão" (TODOS ou seleção) | ✅ |
| 2.2 | ELEMENTO_TITULO: Auto-cálculo ELEMENTO + TITULO | ✅ V39.5 |
| 2.3 | Alterar ELEMENTO (Global) com seleção | ✅ V39.5 |
| 2.4 | Verificar escala Viewport vs Legenda | ⬜ |
| 2.5 | Batch Rename: Tab = DES_NUM_TIPO | ⬜ |
| 2.6 | Relatório de desenhos | ⬜ |

### FASE 3: Enterprise (Multi-DWG + Excel)
| ID | Tarefa | Estado |
|----|--------|--------|
| 3.1 | Definir ID único (GUID vs Chave) | ⬜ |
| 3.2 | Leitura Excel via ActiveX/Python | ⬜ |
| 3.3 | Filtrar LPP por DWG aberto | ⬜ |
| 3.4 | Sync bidirecional DWG ↔ Excel | ⬜ |
| 3.5 | Lock/Conflict detection | ⬜ |

---

## ✨ Funcionalidades Destacadas

### ELEMENTO_TITULO: Atributo Auto-Calculado (V39.5) ✅
- Novo campo **ELEMENTO_TITULO** combina automaticamente ELEMENTO + " - " + TITULO
- **ELEMENTO** e **TITULO** são invisíveis (só para edição)
- **ELEMENTO_TITULO** é visível na legenda (só leitura)
- **Lógica de cálculo:**
  - Ambos preenchidos: `"LAJES - PISO 1"`
  - Só ELEMENTO: `"LAJES"`
  - Só TITULO: `"PISO 1"`
  - Ambos vazios: `""`
- Auto-atualiza ao modificar ELEMENTO ou TITULO
- **CSV:** Exporta ELEMENTO e TITULO separados (ELEMENTO_TITULO não exportável)

### Alterar ELEMENTO (Global) (V39.5) ✅
- Menu opção **6**: Edição dedicada do campo ELEMENTO
- Permite alterar em **TODOS** os desenhos ou **seleção** (ex: `1,3-5,8`)
- Mostra valor atual de cada desenho antes de aplicar
- Recalcula automaticamente **ELEMENTO_TITULO** após alteração
- Ideal para padronizar elemento estrutural em múltiplos desenhos mantendo TITULOs únicos

### Emitir Revisão (V37) ✅
- Emite nova revisão em **TODOS** os desenhos ou **seleção**
- Seleção flexível: `1,3,5` (individual) ou `2-5` (range) ou `1,3-5,8` (misto)
- Data automática (hoje) como default
- Validação: data da nova revisão deve ser >= anterior
- Auto-atualiza atributo R

### Alterar Fase de Projeto (V36) ✅
- Altera fase do projeto em todas as legendas
- Opção de limpar todas as revisões (volta ao início)
- Opção de atualizar DATA para mês/ano atual
- Útil para transição entre fases (Anteprojeto → Projeto de Execução)

### CSV Configurável (V37) ✅
- **Exportação Default:** Colunas padrão (DWG_SOURCE, TIPO, DES_NUM, ELEMENTO, TITULO, REVISAO_ATUAL, ID_CAD)
- **Exportação Customizada:** Seleciona colunas a exportar (ex: `1,3,5` ou `2-8`)
- **Reordenação:** Opção de alterar ordem das colunas no CSV
- **Campos Obrigatórios:** DES_NUM e ID_CAD sempre incluídos automaticamente
- **Campo Especial:** REVISAO_ATUAL expande-se em 3 colunas (Nº, Data, Desc)
- **Nota V39:** ELEMENTO e TITULO são exportados separadamente; ELEMENTO_TITULO é campo calculado (não exportável)

### Modo Navegação (V35) ✅
- Opção **9** em qualquer menu permite navegar pelos layouts
- Útil para verificar desenhos sem sair do programa
- **ENTER** para voltar ao menu

### Logging (V33) ✅
- Ficheiro `.log` regista alterações em legendas
- Utilizador configurável (default: JSJ)
- Formato: `[TIMESTAMP] [USER] AÇÃO: Detalhes`

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

O desenvolvimento é feito com auxílio de **Claude Code**. Para solicitar alterações ou novas funcionalidades, use o formato definido em `_REF_CODEBRIDGE.md`.

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
Versão atual: **V39.5**
