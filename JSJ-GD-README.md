# JSJ-GestaoDesenhos - Guia de Utilização

## O que é?

**JSJ-GestaoDesenhos** é uma aplicação LISP para AutoCAD que permite gerir legendas de desenhos técnicos de forma centralizada. Em vez de editar manualmente cada desenho, pode usar menus interativos para:

- Atualizar dados do projeto em todos os desenhos de uma vez
- Emitir revisões com controlo automático
- Exportar e importar listas de desenhos em CSV
- Criar novos desenhos a partir de um template
- Numerar e ordenar desenhos automaticamente

---

## Como Carregar

1. Abra o ficheiro DWG no AutoCAD
2. Digite `APPLOAD` na linha de comando
3. Selecione o ficheiro `JSJ-GestaoDesenhosV41.lsp`
4. Clique em "Load"
5. Digite `GD` na linha de comando para abrir o menu principal

> **Nota:** O ficheiro DWG deve conter um bloco chamado `LEGENDA_JSJ_V1` nos layouts (não no Model Space).

---

## Menu Principal

Ao digitar `GD`, aparece o menu principal:

```
==============================================
          GESTAO DESENHOS JSJ V41.0          
==============================================
 1. Modificar Legendas
 2. Exportar Lista de Desenhos
 3. Importar Lista de Desenhos
 4. Dados do Projeto
 5. Gerir Layouts
----------------------------------------------
 9. Navegar (ver desenho)
 0. Sair
==============================================
```

### Opção 9 - Navegar
A qualquer momento pode usar a opção **9** para sair do menu e navegar visualmente pelos layouts do desenho. Prima ENTER para voltar ao menu.

---

## 1. Modificar Legendas

Este submenu permite editar campos específicos das legendas:

```
--- MODIFICAR LEGENDAS ---
[Utilizador: JSJ]
1. Emitir Revisao
2. Editar Titulo de Desenho
3. Editar Tipo em desenhos
4. Editar Elemento em desenhos
5. Editar Pfix em desenhos
6. Definir Utilizador
9. Navegar (ver desenho)
0. Voltar
```

### 1.1 Emitir Revisão
Emite uma nova revisão para um ou mais desenhos. O sistema:
- Mostra a lista de desenhos com a revisão atual
- Permite selecionar desenhos individualmente, por intervalo, ou todos
- Pede a descrição da alteração
- Atualiza automaticamente os campos de revisão (REV_A, REV_B, etc.)
- Atualiza a data e o utilizador

### 1.2 Editar Título de Desenho
Altera o título de um desenho específico:
- Mostra lista de desenhos com títulos atuais
- Selecione o desenho pelo número
- Digite o novo título

### 1.3 Editar Tipo em Desenhos
Altera o campo TIPO (ex: PLANTA, CORTE, PORMENOR):
- Mostra desenhos agrupados por TIPO
- Selecione os desenhos a alterar
- Digite o novo valor (ou "VAZIO" para limpar)

### 1.4 Editar Elemento em Desenhos
Altera o campo ELEMENTO (ex: FUNDAÇÕES, PILARES):
- Funciona igual ao TIPO
- Use "VAZIO" para limpar o campo

### 1.5 Editar PFIX em Desenhos
Altera o prefixo dos desenhos (ex: DIM, ARM, FUN):
- O PFIX ajuda a agrupar desenhos por especialidade
- Use "VAZIO" para limpar o prefixo

### 1.6 Definir Utilizador
Define o nome do utilizador atual:
- Este nome aparece nas revisões emitidas
- Por defeito é "JSJ"

---

## 2. Exportar Lista de Desenhos

Gera ficheiros CSV com os dados dos desenhos:

```
--- EXPORTAR LISTA DE DESENHOS ---
1. Gerar CSV (Campos Principais)
2. Gerar CSV (Todos os Campos)
3. Gerar CSV (Configuração Personalizada)
0. Voltar
```

> **Aviso:** Se existirem desenhos com DES_NUM duplicado, o sistema avisa antes de exportar.

### 2.1 Campos Principais
Exporta os campos mais usados:
- DWG_SOURCE, PROJ_NUM, PFIX, DES_NUM, TIPO, ELEMENTO, TITULO
- Última revisão (letra, data, descrição)
- LAYOUT, ID_CAD

### 2.2 Todos os Campos
Exporta todos os 34 campos do bloco, incluindo:
- Dados do projeto (PROJ_NUM, PROJ_NOME, CLIENTE, OBRA, etc.)
- Fase e emissão
- Todas as 5 revisões (A a E)
- ID_CAD para reimportação

### 2.3 Configuração Personalizada
Usa o ficheiro `csv_config.json` para definir quais colunas exportar:
```json
{
  "columns": ["DES_NUM", "TIPO", "TITULO"],
  "separator": ";",
  "includeHeader": true
}
```

---

## 3. Importar Lista de Desenhos

Atualiza os desenhos a partir de um ficheiro CSV:

```
--- IMPORTAR LISTA DE DESENHOS ---
1. Importar CSV (por ID_CAD)
2. Importar CSV (por Layout)
0. Voltar
```

### 3.1 Por ID_CAD (Recomendado)
- Usa a coluna ID_CAD para identificar cada desenho
- Mais fiável porque o ID não muda
- O CSV deve ter sido exportado pela opção "Todos os Campos"

### 3.2 Por Layout
- Usa o nome do layout para identificar o desenho
- Útil quando não tem ID_CAD
- Pode falhar se os nomes dos layouts mudaram

---

## 4. Dados do Projeto

Configura dados globais do projeto:

```
--- DADOS DO PROJETO ---
1. Definir Dados do Projeto
2. Definir Fase
3. Definir Emissao
9. Navegar (ver desenho)
0. Voltar
```

### 4.1 Definir Dados do Projeto
Atualiza 7 campos em **todos os desenhos** de uma vez:
- PROJ_NUM (número do projeto)
- PROJ_NOME (nome do projeto)
- CLIENTE
- OBRA
- LOCALIZACAO
- ESPECIALIDADE
- PROJETOU

> **Dica:** Prima ENTER para manter o valor atual de um campo.

### 4.2 Definir Fase
Define a fase do projeto:
- FASE (ex: Projeto de Execução)
- FASE_PFIX (abreviatura, ex: PB, PE, PP)

### 4.3 Definir Emissão
Define o código de emissão:
- EMISSAO (ex: E01, E02, E03)
- DATA (data da emissão)
- Opção para limpar todas as revisões (útil para nova emissão)

---

## 5. Gerir Layouts

Gestão de layouts/tabs do desenho:

```
--- GERIR LAYOUTS ---
1. Gerar Novos Desenhos
2. Adicionar Desenho Intermedio
3. Apagar Desenhos
4. Numerar Desenhos
5. Ordenar Desenhos
6. Atualizar Nomes Layouts
9. Navegar (ver desenho)
0. Voltar
```

### 5.1 Gerar Novos Desenhos
Cria novos layouts copiando do TEMPLATE:
- Funciona em loop (pode criar vários)
- Pergunta quantos desenhos criar
- Opção para preencher atributos (PFIX, TIPO, ELEMENTO, TITULO)
- Copia dados do projeto automaticamente

### 5.2 Adicionar Desenho Intermédio
Insere um desenho no meio da sequência:

**Modo Sequencial:**
- Escolhe o número do novo desenho
- Renumera os existentes para abrir espaço
- Limpa o PFIX de todos os desenhos (numeração global)

**Modo Por PFIX:**
- Escolhe o PFIX (ex: DIM, ARM)
- Só renumera desenhos desse PFIX
- Mantém os outros grupos intactos

### 5.3 Apagar Desenhos
Remove layouts selecionados:
- Mostra lista de desenhos
- Selecione por número, intervalo, ou todos
- Pede confirmação antes de apagar
- Não pode apagar o TEMPLATE

### 5.4 Numerar Desenhos
Atribui números aos desenhos:

**Modo Sequencial:**
- Numera todos os desenhos: 001, 002, 003...
- Ignora o PFIX

**Modo Por PFIX:**
- Cada grupo PFIX tem sua sequência
- Ex: DIM→001,002; ARM→001,002,003

### 5.5 Ordenar Desenhos
Reorganiza a ordem dos tabs:

**Por DES_NUM:**
- Ordena pelos números: 001, 002, 003...
- Ideal para numeração sequencial

**Por PFIX:**
- Agrupa por prefixo
- Define ordem dos prefixos (ex: DIM, ARM, FUN)
- Dentro de cada grupo, ordena por número

### 5.6 Atualizar Nomes Layouts
Renomeia os tabs conforme o formato padrão:
```
PROJ_NUM-EST-PFIX DES_NUM-EMISSAO-FASE_PFIX-R
```
Exemplo: `669-EST-DIM 03-E01-PB-C`

---

## Formato do Nome do Tab

O nome de cada tab/layout segue este formato:

```
PROJ_NUM-EST-PFIX DES_NUM-EMISSAO-FASE_PFIX-R
```

| Componente | Descrição | Exemplo |
|------------|-----------|---------|
| PROJ_NUM | Número do projeto | 669 |
| EST | Fixo (especialidade) | EST |
| PFIX | Prefixo do desenho | DIM |
| DES_NUM | Número do desenho (3 dígitos) | 03 |
| EMISSAO | Código de emissão | E01 |
| FASE_PFIX | Abreviatura da fase | PB |
| R | Letra da revisão atual | C |

**Resultado:** `669-EST-DIM 03-E01-PB-C`

> **Nota:** Se não houver PFIX, o formato fica: `669-EST-03-E01-PB-C`

---

## Requisitos

- **AutoCAD** com suporte a Visual LISP
- **Bloco** `LEGENDA_JSJ_V1` nos layouts
- **Layout TEMPLATE** para criar novos desenhos

---

## Atalhos

| Comando | Descrição |
|---------|-----------|
| `GD` | Abre o menu principal |
| `APPLOAD` | Carrega o ficheiro LSP |

---

## Dicas

1. **Sempre guarde o DWG** antes de fazer alterações em massa
2. **Use TEMPLATE** como base para novos desenhos - não o apague
3. **Exporte CSV completo** antes de fazer grandes alterações (backup)
4. **Use ID_CAD** para reimportar dados - é mais fiável que nome do layout
5. **Limpe as revisões** ao mudar de emissão (E01→E02)

---

## Suporte

Para questões ou problemas, contacte a equipa JSJ.

**Versão:** V41.0  
**Data:** Dezembro 2024
