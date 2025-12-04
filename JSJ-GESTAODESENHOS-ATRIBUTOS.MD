# JSJ Drawing Management System

**Sistema LISP para gestão de legendas de desenhos de estruturas em AutoCAD. Ficheiro com indicação de atributos do Bloco LEGENDA_JSJ_V1 e para que servem, bem como indicação dos que são exportados pela LSP para um ficheiro CSV***



#ATRIBUTOS DAS LEGENDAS DOS LAYOUTS DE UM DWG DE UM PROJETO DA JSJ (BLOCO É O "LEGENDA_JSJ_V1")

**estes atributos correspondem aos que existem no bloco LEGENDA_JSJ_V1

##ATRIBUTOS FIXOS (NÃO MUDAM NUNCA):

  ESCALAS = 'INDICADAS'

##ATRIBUTOS GERAIS - DADOS DO PROJETO (são sempre comuns a todos os desenhos/layouts. Visiveis na legenda a não ser que seja indicado o contrario)


  PROJ_NUM = ''   #define o numero do projeto (é o ID principal de um projeto) - invisivel na legenda
  PROJ_NOME = ''  #define o nome do projeto (nome oficial do projeto na JSJ) - invisivel na legenda
  CLIENTE = ''    #define o nome do projeto (nome oficial do projeto na JSJ) - invisivel na legenda
  OBRA = ''		  #define o tipo de Obra (Edifício de Habitação, Reabilitação, etc)
  LOCALIZACAO = ''   #define o local
  ESPECIALIDADE = 'ESTRUTURA E FUNDAÇÕES' #define a especialidade (a não ser que indicado em contrário, por defeito é "Estrutura e Fundações"
  PROJETOU = ''    #define os projetistas responsáveis (ex: João Almeida, David Gama, etc.)
  
##ATRIBUTOS GERAIS - FASE DO PROJETO (Definem a que fase do projeto se referem os desenhos. são sempre comuns a todos os desenhos/layouts. Visiveis na legenda a não ser que seja indicado o contrario)
  
  
  FASE = ''  #define a fase do projeto (ex: Licenciamento, Execução, etc) 
  FASE_PFIX = ''  #define o prefixo da fase a usar no "tab" do layout que a lsp preenche automaticamente (ex: PB, PE, etc)
  
##ATRIBUTOS GERAIS - EMISSÃO (Definem qual o número da emissão dos desenhos, na fase em que se encontram (num Proj Execução pode haver a emissão E00, a E01, etc. Numa emissão, todos os desenhos são emitidos e "zeradas" as revisões. são sempre comuns a todos os desenhos/layouts. Visiveis na legenda a não ser que seja indicado o contrario)
  
  EMISSAO = '' #define o numero da emissão. formato: EXX . Exemplo: 1a emissão é a E01, 2a emissão é a E02....
  DATA = ''  #define a data da emissão

##ATRIBUTOS DE UM CONJUNTO DE DESENHOS  

  TIPO = ''  #define o tipo de desenho (Dimensionamento, Betão Armado, etc). Normalmente é um conjunto de desenhos. 
  ELEMENTO = '' #define o tipo de elemento a que se refere o desenho (ex: Lajes, Núcleos, Pilares...). é invisivel na legenda. mas deve sair no CSV para lista de desenhos.
  PFIX = ''  #define o prefixo a utilizar no desenho (ex: DIM, LAJ, etc). é Visivel: quando existe, antes de DES_NUM e no Tab. Quando este valor é vazio, normalmente a numeração dos desenhos é sequencial e não e projeto nao numera desenhos por "PFIX" (ex: 001, 002, 003.....) Quando este atributo existe, por norma a numeração é feita por conjunto de desenhos com o mesmo PFIX
  
  
  ##ATRIBUTOS DE UM DESENHO INDIVIDUAL (cada legenda tem estes atributos unicos)
  
  TITULO = '' #Define o titulo de um desenho (ex: Armaduras Superiores. é invisivel na legenda. mas deve sair no CSV para lista de desenhos.
  ELEMENTO_TITULO = 'ELEMENTO - TITULO' #é o que aparece na linha que descreve o desenho, abaixo de "tipo". agrega os atributos Elemento e Titulo. É gerado pela lsp apenas para visualização na legenda. não é exportado nos ficheiros CSV.

  DES_NUM = '' #Define o numero do desenho. o formato é com 3 algarismos. exemplo: 001, 010, 100....
  R = ''  #atributo para na legenda ao lado de DES_NUM mostrar qual a ultima revisao (se existir). é obtido do quadro de revisoes pela Lsp
  DATA_E = '' #atributo para no quadro de revisões com a data da Revisão E
  DESC_E = '' #atributo para no quadro de revisões com a Descrição da Revisão E
  REV_E = ''  #atributo para no quadro de revisões com o valor "E" pois nessa linha a revisão é a E. 
  DATA_D = '' #atributo para no quadro de revisões com a data da Revisão D
  DESC_D = '' #atributo para no quadro de revisões com a Descrição da Revisão D
  REV_D = ''  #atributo para no quadro de revisões com o valor "D" pois nessa linha a revisão é a D. 
  DATA_C = '' #atributo para no quadro de revisões com a data da Revisão C
  DESC_C = '' #atributo para no quadro de revisões com a Descrição da Revisão C
  REV_C = ''  #atributo para no quadro de revisões com o valor "C" pois nessa linha a revisão é a C. 
  DATA_B = '' #atributo para no quadro de revisões com a data da Revisão B
  DESC_B = '' #atributo para no quadro de revisões com a Descrição da Revisão B
  REV_B = ''  #atributo para no quadro de revisões com o valor "B" pois nessa linha a revisão é a B. 
  DATA_A = '' #atributo para no quadro de revisões com a data da Revisão A
  DESC_A = '' #atributo para no quadro de revisões com a Descrição da Revisão A
  REV_A = ''  #atributo para no quadro de revisões com o valor "A" pois nessa linha a revisão é a A. 


#ATRIBUTOS QUE LSP EXPORTA PARA CSV / IMPORTA DE CSV

**estes atributos correspondem aos que são exportados nos ficheiros CSV (os que não estão na lista não são exportados). cada layout (exceto o layout template) é lido pela lsp e preenchida uma linha com os atributos seguintes (pela ordem seguinte). No CSV a primeira linha é os "Headers" (ou seja, os Nomes dos atributos)
**da lista seguinte apenas DWG_SOURCE, ID_CAD não são atributos. Mas LSP exporta no CSV. identificam, respetivamente: Nome do ficheiro DWG e ID unico de cada desenho. 

PROJ_NUM, PROJ_NOME, CLIENTE, OBRA, LOCALIZACAO, ESPECIALIDADE, PROJETOU, FASE, FASE_PFIX, EMISSAO, DATA, PFIX, LAYOUT, DES_NUM, TIPO, ELEMENTO, TITULO, REV_A, DATA_A, DESC_A, REV_B, DATA_B, DESC_B, REV_C, DATA_C, DESC_C, REV_D, DATA_D, DESC_D, REV_E, DATA_E, DESC_E, DWG_SOURCE, ID_CAD