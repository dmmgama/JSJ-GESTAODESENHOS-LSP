;; ============================================================================
;; JSJ-GESTAO DESENHOS AutoLISP - V41.0
;; Gestão de Legendas para desenhos estruturais
;; ============================================================================
;; ATRIBUTOS DO BLOCO LEGENDA_JSJ_V1:
;;   Globais: CLIENTE, OBRA, LOCALIZACAO, ESPECIALIDADE, FASE, DATA, PROJETOU,
;;            PROJ_NUM, PROJ_NOME, FASE_PFIX, EMISSAO, PFIX
;;   Individuais: DES_NUM, TIPO, ELEMENTO, TITULO, REV_A-E, DATA_A-E, DESC_A-E, R
;;   Calculados: ELEMENTO_TITULO (ELEMENTO + TITULO)
;; ============================================================================
;; FORMATO NOME TAB (FIXO):
;;   PROJ_NUM-"EST"-PFIX-DES_NUM-EMISSAO-R
;;   Exemplo: 779-EST-BA-01-E00-A (ou 779-EST-BA-01-E00 se sem revisão)
;; ============================================================================

;; Variáveis globais (persistem durante sessão)
(setq *JSJ_USER* nil)

;; ============================================================================
;; FUNCOES AUXILIARES BASICAS (devem estar no inicio)
;; ============================================================================
(defun IsTargetBlock (blk) 
  (and (= (vla-get-ObjectName blk) "AcDbBlockReference") 
       (= (strcase (vla-get-EffectiveName blk)) "LEGENDA_JSJ_V1"))
)

(defun GetAttValue (blk tag / atts val) 
  (setq atts (vlax-invoke blk 'GetAttributes) val "") 
  (foreach att atts 
    (if (= (strcase (vla-get-TagString att)) (strcase tag)) 
      (setq val (vla-get-TextString att)))) 
  val
)

(defun UpdateSingleTag (handle tag val / ename obj atts) 
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle)))) 
    (setq ename (handent handle))) 
  (if (and ename (setq obj (vlax-ename->vla-object ename))) 
    (progn 
      (setq atts (vlax-invoke obj 'GetAttributes)) 
      (foreach att atts 
        (if (= (strcase (vla-get-TagString att)) (strcase tag)) 
          (vla-put-TextString att val))) 
      (vla-Update obj)
      ;; Se alterou ELEMENTO ou TITULO, recalcular ELEMENTO_TITULO
      ;; Passa o tag alterado e o novo valor
      (if (= (strcase tag) "ELEMENTO")
        (UpdateElementoTitulo handle "ELEMENTO" val)
      )
      (if (= (strcase tag) "TITULO")
        (UpdateElementoTitulo handle "TITULO" val)
      )
    )
  )
)

;; ============================================================================
;; ELEMENTO_TITULO - Atributo calculado automaticamente
;; ============================================================================
;; Combina ELEMENTO + " - " + TITULO
;; Regras:
;;   - Ambos preenchidos: "<ELEMENTO> - <TITULO>"
;;   - Só ELEMENTO: "<ELEMENTO>"
;;   - Só TITULO: "<TITULO>"
;;   - Ambos vazios: ""
;; UpdateElementoTitulo - Recalcula ELEMENTO_TITULO
;; Parâmetros: changedTag = "ELEMENTO" ou "TITULO" ou nil
;;            newValue = novo valor do tag alterado
;; Se changedTag=nil, lê ambos do bloco
(defun UpdateElementoTitulo (handle changedTag newValue / ename obj elemento titulo resultado)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle))
  )
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (progn
      ;; Determinar valores de ELEMENTO e TITULO
      (cond
        ((= changedTag "ELEMENTO")
          ;; ELEMENTO foi alterado - usar newValue, ler TITULO do bloco
          (setq elemento (if newValue (vl-string-trim " " newValue) ""))
          (setq titulo (vl-string-trim " " (GetAttValue obj "TITULO")))
        )
        ((= changedTag "TITULO")
          ;; TITULO foi alterado - ler ELEMENTO do bloco, usar newValue
          (setq elemento (vl-string-trim " " (GetAttValue obj "ELEMENTO")))
          (setq titulo (if newValue (vl-string-trim " " newValue) ""))
        )
        (T
          ;; Ambos do bloco
          (setq elemento (vl-string-trim " " (GetAttValue obj "ELEMENTO")))
          (setq titulo (vl-string-trim " " (GetAttValue obj "TITULO")))
        )
      )
      
      ;; DEBUG - mostrar valores (remover depois)
      (princ (strcat "\n[DEBUG] ELEMENTO='" elemento "' TITULO='" titulo "'"))
      
      ;; Construir resultado baseado nas regras
      (cond
        ((and (= elemento "") (= titulo ""))
          (setq resultado "")
        )
        ((= elemento "")
          (setq resultado titulo)
        )
        ((= titulo "")
          (setq resultado elemento)
        )
        (T
          (setq resultado (strcat elemento " - " titulo))
        )
      )
      
      (princ (strcat " -> ELEMENTO_TITULO='" resultado "'"))
      
      ;; Gravar ELEMENTO_TITULO diretamente (sem recursao)
      (setq foundET nil)
      (foreach att (vlax-invoke obj 'GetAttributes)
        (if (= (strcase (vla-get-TagString att)) "ELEMENTO_TITULO")
          (progn
            (vla-put-TextString att resultado)
            (setq foundET T)
            (princ " [GRAVADO]")
          )
        )
      )
      (if (not foundET)
        (princ " [AVISO: Atributo ELEMENTO_TITULO nao encontrado!]")
      )
      (vla-Update obj)
    )
  )
)

(defun FormatNum (n) 
  (if (< n 10) (strcat "0" (itoa n)) (itoa n))
)
(defun FormatNum (n) 
  (if (< n 10) (strcat "0" (itoa n)) (itoa n))
)

(defun StrSplit (str del / pos len lst) 
  (setq len (strlen del)) 
  (while (setq pos (vl-string-search del str)) 
    (setq lst (cons (vl-string-trim " " (substr str 1 pos)) lst) 
          str (substr str (+ 1 pos len)))) 
  (reverse (cons (vl-string-trim " " str) lst))
)

(defun GetExampleTags ( / doc tagList found atts tag) 
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) 
        tagList '() 
        found nil) 
  (vlax-for lay (vla-get-Layouts doc) 
    (if (not found) 
      (vlax-for blk (vla-get-Block lay) 
        (if (IsTargetBlock blk) 
          (progn 
            (foreach att (vlax-invoke blk 'GetAttributes) 
              (setq tag (strcase (vla-get-TagString att))) 
              ;; Excluir campos calculados, de sistema e únicos por desenho
              (if (and (/= tag "DES_NUM") 
                       (/= tag "FASE") 
                       (/= tag "R")
                       (/= tag "TITULO")           ;; Único por desenho (não editável globalmente)
                       (/= tag "ELEMENTO_TITULO") ;; Campo calculado
                       (not (wcmatch tag "REV_?,DATA_?,DESC_?"))) 
                (setq tagList (cons tag tagList)))) 
            (setq found T)))))) 
  (vl-sort tagList '<)
)

(defun GetDrawingList ( / doc listOut atts desNum tipo name) 
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) 
        listOut '()) 
  (vlax-for lay (vla-get-Layouts doc) 
    (setq name (strcase (vla-get-Name lay))) 
    (if (and (/= (vla-get-ModelType lay) :vlax-true) 
             (/= name "TEMPLATE")) 
      (vlax-for blk (vla-get-Block lay) 
        (if (IsTargetBlock blk) 
          (progn 
            (setq desNum "0" tipo "ND") 
            (foreach att (vlax-invoke blk 'GetAttributes) 
              (if (= (strcase (vla-get-TagString att)) "DES_NUM") 
                (setq desNum (vla-get-TextString att))) 
              (if (= (strcase (vla-get-TagString att)) "TIPO") 
                (setq tipo (vla-get-TextString att)))) 
            (setq listOut (cons (list (vla-get-Handle blk) desNum (vla-get-Name lay) tipo) listOut))))))) 
  (setq listOut (vl-sort listOut '(lambda (a b) (< (atoi (cadr a)) (atoi (cadr b)))))) 
  listOut
)

(defun GetDWGName ( / rawName baseName) 
  (setq rawName (getvar "DWGNAME")) 
  (if (or (= rawName "") (= rawName nil) (wcmatch (strcase rawName) "DRAWING*.DWG")) 
    "SEM_NOME" 
    (vl-filename-base rawName))
)

;; Extrai apenas a parte numerica de uma string (ignora prefixos/sufixos)
;; Ex: "A-001" -> "001", "FUN-12" -> "12", "001" -> "001"
(defun ExtractNumericPart (str / i ch result)
  (if (or (null str) (= str ""))
    ""
    (progn
      (setq result "")
      (setq i 1)
      (while (<= i (strlen str))
        (setq ch (substr str i 1))
        (if (and (>= (ascii ch) 48) (<= (ascii ch) 57))  ;; 0-9
          (setq result (strcat result ch))
        )
        (setq i (1+ i))
      )
      result
    )
  )
)

(defun CleanCSV (str) 
  (if (= str nil) (setq str "")) 
  (setq str (vl-string-translate ";" "," str)) 
  (vl-string-trim " \"" str)
)

(defun GetLayoutsRaw (doc / lays listLays name) 
  (setq lays (vla-get-Layouts doc)) 
  (setq listLays '()) 
  (vlax-for item lays 
    (setq name (strcase (vla-get-Name item))) 
    (if (and (/= (vla-get-ModelType item) :vlax-true) 
             (/= name "TEMPLATE")) 
      (setq listLays (cons item listLays)))) 
  (vl-sort listLays '(lambda (a b) (< (vla-get-TabOrder a) (vla-get-TabOrder b))))
)

(defun GetMaxRevision (blk / checkRev finalRev finalDate finalDesc) 
  (setq finalRev "-" finalDate "-" finalDesc "-") 
  (foreach letra '("E" "D" "C" "B" "A") 
    (if (= finalRev "-") 
      (progn 
        (setq checkRev (GetAttValue blk (strcat "REV_" letra))) 
        (if (and (/= checkRev "") (/= checkRev " ")) 
          (progn 
            (setq finalRev checkRev) 
            (setq finalDate (GetAttValue blk (strcat "DATA_" letra))) 
            (setq finalDesc (GetAttValue blk (strcat "DESC_" letra)))))))) 
  (list finalRev finalDate finalDesc)
)

(defun ParseDateToNum (dateStr / parts d m y)
  (if (and dateStr (/= dateStr "") (/= dateStr "-") (/= dateStr " "))
    (progn
      (setq parts (StrSplit dateStr "-"))
      (if (>= (length parts) 3)
        (progn
          (setq d (atoi (nth 0 parts)))
          (setq m (atoi (nth 1 parts)))
          (setq y (atoi (nth 2 parts)))
          (+ (* y 10000) (* m 100) d)
        )
        0
      )
    )
    0
  )
)

(defun ValidateRevisionDates (blk / dataA dataB dataC dataD dataE errors)
  (setq errors "")
  (setq dataA (ParseDateToNum (GetAttValue blk "DATA_A")))
  (setq dataB (ParseDateToNum (GetAttValue blk "DATA_B")))
  (setq dataC (ParseDateToNum (GetAttValue blk "DATA_C")))
  (setq dataD (ParseDateToNum (GetAttValue blk "DATA_D")))
  (setq dataE (ParseDateToNum (GetAttValue blk "DATA_E")))
  
  (if (and (> dataA 0) (> dataB 0) (< dataB dataA))
    (setq errors (strcat errors "DATA_B < DATA_A; "))
  )
  (if (and (> dataB 0) (> dataC 0) (< dataC dataB))
    (setq errors (strcat errors "DATA_C < DATA_B; "))
  )
  (if (and (> dataC 0) (> dataD 0) (< dataD dataC))
    (setq errors (strcat errors "DATA_D < DATA_C; "))
  )
  (if (and (> dataD 0) (> dataE 0) (< dataE dataD))
    (setq errors (strcat errors "DATA_E < DATA_D; "))
  )
  
  (if (= errors "") nil errors)
)

(defun FindDuplicateDES_NUM (dataList / duplicates item num seen result)
  (setq seen '() duplicates '())
  
  ;; Assumir que dataList é uma lista de listas, e precisamos procurar DES_NUM
  ;; A função antiga esperava (DWG TIPO NUM TITULO ...) onde NUM é índice 2
  ;; Como agora pode variar, vamos assumir que sempre existe DES_NUM
  
  (foreach item dataList
    ;; Tentar encontrar DES_NUM na posição típica ou procurar
    (setq num nil)
    
    ;; Se a lista tem pelo menos 3 elementos, assumir índice 2 (compatibilidade)
    (if (>= (length item) 3)
      (setq num (nth 2 item))
    )
    
    (if num
      (if (assoc num seen)
        (setq duplicates (cons (strcat "DES_NUM " num) duplicates))
        (setq seen (cons (cons num T) seen))
      )
    )
  )
  
  (if duplicates
    (progn
      (setq result "")
      (foreach dup (reverse duplicates)
        (setq result (strcat result dup "\n"))
      )
      result
    )
    nil
  )
)

;; Versão melhorada que recebe o índice de DES_NUM
(defun FindDuplicateDES_NUM_ByIndex (dataList desNumIdx / duplicates item num seen result)
  (setq seen '() duplicates '())
  
  (foreach item dataList
    (if (and (>= (length item) (1+ desNumIdx)) desNumIdx)
      (progn
        (setq num (nth desNumIdx item))
        (if (and num (/= num ""))
          (if (assoc num seen)
            (setq duplicates (cons (strcat "DES_NUM " num) duplicates))
            (setq seen (cons (cons num T) seen))
          )
        )
      )
    )
  )
  
  (if duplicates
    (progn
      (setq result "")
      (foreach dup (reverse duplicates)
        (setq result (strcat result dup "\n"))
      )
      result
    )
    nil
  )
)

;; ============================================================================
;; MENU PRINCIPAL
;; ============================================================================
(defun c:GESTAODESENHOSJSJ ( / loop opt)
  (vl-load-com)
  (setq loop T)

  (while loop
    (textscr)
    (princ "\n\n==============================================")
    (princ "\n       GESTAO DESENHOS JSJ V41.0 - MENU       ")
    (princ "\n==============================================")
    (princ "\n 0. Dados do Projeto")
    (princ "\n 1. Modificar Legendas")
    (princ "\n 2. Exportar Lista de Desenhos")
    (princ "\n 3. Importar Lista de Desenhos")
    (princ "\n 4. Gerir Layouts")
    (princ "\n----------------------------------------------")
    (princ "\n 9. Navegar (ver desenho)")
    (princ "\n X. Sair")
    (princ "\n==============================================")

    (initget "0 1 2 3 4 9 X")
    (setq opt (getkword "\nEscolha uma opcao [0/1/2/3/4/9/X]: "))

    (cond
      ((= opt "0") (Menu_DadosProjeto))
      ((= opt "1") (Menu_ModificarLegendas))
      ((= opt "2") (Menu_Exportar))
      ((= opt "3") (Menu_Importar))
      ((= opt "4") (Menu_GerirLayouts))
      ((= opt "9") (ModoNavegacao))
      ((= opt "X") (setq loop nil))
      ((= opt nil) (setq loop nil)) 
    )
  )
  (graphscr)
  (princ "\nGestao Desenhos JSJ Terminada.")
  (princ)
)

;; ============================================================================
;; SUBMENU 0: DADOS DO PROJETO
;; ============================================================================
(defun Menu_DadosProjeto ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- DADOS DO PROJETO ---")
    (princ (strcat "\n   [Utilizador: " (if *JSJ_USER* *JSJ_USER* "JSJ") "]"))
    (princ "\n   1. Editar Campos Globais")
    (princ "\n   2. Definir Utilizador")
    (princ "\n   3. Alterar Fase do Projeto")
    (princ "\n   0. Voltar")
    (initget "1 2 3 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/0]: "))
    (cond
      ((= optSub "1") (EditarCampoGlobal '("CLIENTE" "OBRA" "LOCALIZACAO" "ESPECIALIDADE" 
                                           "DATA" "PROJETOU" "PROJ_NUM" "PROJ_NOME" 
                                           "FASE_PFIX" "EMISSAO" "PFIX")))
      ((= optSub "2") (SetCurrentUser))
      ((= optSub "3") (AlterarFaseProjeto))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
)

;; ============================================================================
;; DIAGNOSTICO - Lista todos atributos do primeiro bloco LEGENDA_JSJ_V1
;; ============================================================================
(defun c:JSJDIAG ( / doc found)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq found nil)
  (textscr)
  (princ "\n\n=== DIAGNOSTICO BLOCO LEGENDA_JSJ_V1 ===\n")
  (vlax-for lay (vla-get-Layouts doc)
    (if (not found)
      (vlax-for blk (vla-get-Block lay)
        (if (and (not found) (IsTargetBlock blk))
          (progn
            (princ (strcat "\nLayout: " (vla-get-Name lay)))
            (princ "\n\nAtributos encontrados:")
            (foreach att (vlax-invoke blk 'GetAttributes)
              (princ (strcat "\n  " (vla-get-TagString att) " = '" (vla-get-TextString att) "'"))
            )
            (setq found T)
          )
        )
      )
    )
  )
  (if (not found)
    (princ "\nERRO: Nenhum bloco LEGENDA_JSJ_V1 encontrado!")
  )
  (princ "\n")
  (princ)
)

;; ============================================================================
;; MODO NAVEGACAO - Permite ver/alterar layouts e voltar ao menu
;; ============================================================================
(defun ModoNavegacao ( / )
  (graphscr)
  (princ "\n*** MODO NAVEGACAO ***")
  (princ "\nPode agora navegar pelos layouts e verificar os desenhos.")
  (princ "\nQuando terminar, prima ENTER para voltar ao menu.")
  (getstring "\n[ENTER para voltar ao menu]: ")
  (princ)
)

;; ============================================================================
;; SUBMENU 1: MODIFICAR LEGENDAS
;; ============================================================================
(defun Menu_ModificarLegendas ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- MODIFICAR LEGENDAS ---")
    (princ (strcat "\n   [Utilizador: " (if *JSJ_USER* *JSJ_USER* "JSJ") "]"))
    (princ "\n   1. Emitir Revisao")
    (princ "\n   2. Alterar Campo (Global ou Selecao)")
    (princ "\n   3. Alterar Desenho Individual")
    (princ "\n   4. Atualizar Nomes Layouts")
    (princ "\n   9. Navegar (ver desenho)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 9 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/9/0]: "))
    (cond
      ((= optSub "1") (Menu_EmitirRevisao))
      ((= optSub "2") (Run_GlobalVars_Selective_V29))
      ((= optSub "3") (ProcessManualReview))
      ((= optSub "4") (AtualizarNomesLayouts))
      ((= optSub "9") (ModoNavegacao))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
)

;; ============================================================================
;; SUBMENU: EMITIR REVISAO (2.1) - Simplificado
;; ============================================================================
(defun Menu_EmitirRevisao ( / )
  (EmitirRevisao_Unificado)
)

;; ============================================================================
;; ALTERAR FASE DE PROJETO - Muda fase e pode zerar revisoes
;; ============================================================================
(defun AlterarFaseProjeto ( / doc newFase zerarRevs alterarData newData count countRev lay blk handle)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== ALTERAR FASE DE PROJETO ===")
  (princ "\nExemplos: PROJETO DE EXECUCAO, LICENCIAMENTO, ESTUDO PREVIO")
  (setq newFase (getstring T "\nNova FASE: "))
  
  (if (and newFase (/= newFase ""))
    (progn
      ;; Aplicar nova fase a todos os desenhos
      (princ "\nA aplicar nova fase... ")
      (setq count 0)
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (UpdateSingleTag (vla-get-Handle blk) "FASE" newFase)
                (setq count (1+ count))
              )
            )
          )
        )
      )
      (princ (strcat (itoa count) " desenhos atualizados."))
      (WriteLog (strcat "FASE: Alterada para '" newFase "' em " (itoa count) " desenhos"))
      
      ;; Perguntar se quer zerar revisoes
      (princ "\n\n--> Pretende APAGAR todas as revisoes (zerar projeto)?")
      (initget "Sim Nao")
      (setq zerarRevs (getkword "\n    [Sim/Nao] <Nao>: "))
      
      (if (= zerarRevs "Sim")
        (progn
          (princ "\nA apagar revisoes... ")
          (setq countRev 0)
          (vlax-for lay (vla-get-Layouts doc)
            (if (and (/= (vla-get-ModelType lay) :vlax-true)
                     (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
              (vlax-for blk (vla-get-Block lay)
                (if (IsTargetBlock blk)
                  (progn
                    (setq handle (vla-get-Handle blk))
                    ;; Apagar todas as revisoes A-E
                    (foreach letra '("A" "B" "C" "D" "E")
                      (UpdateSingleTag handle (strcat "REV_" letra) "")
                      (UpdateSingleTag handle (strcat "DATA_" letra) "")
                      (UpdateSingleTag handle (strcat "DESC_" letra) "")
                    )
                    ;; Limpar R
                    (UpdateSingleTag handle "R" "")
                    (setq countRev (1+ countRev))
                  )
                )
              )
            )
          )
          (princ (strcat (itoa countRev) " desenhos zerados."))
          (WriteLog (strcat "FASE: Revisoes apagadas em " (itoa countRev) " desenhos"))
        )
      )
      
      ;; Perguntar se quer alterar DATA (data do projeto/primeira emissao)
      (princ "\n\n--> Pretende alterar a DATA do projeto (primeira emissao)?")
      (initget "Sim Nao")
      (setq alterarData (getkword "\n    [Sim/Nao] <Nao>: "))
      
      (if (= alterarData "Sim")
        (progn
          (princ "\nExemplo: NOVEMBRO 2025")
          (setq newData (getstring T "\nNova DATA: "))
          (if (and newData (/= newData ""))
            (progn
              (princ "\nA aplicar nova data... ")
              (setq count 0)
              (vlax-for lay (vla-get-Layouts doc)
                (if (and (/= (vla-get-ModelType lay) :vlax-true)
                         (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                  (vlax-for blk (vla-get-Block lay)
                    (if (IsTargetBlock blk)
                      (progn
                        (UpdateSingleTag (vla-get-Handle blk) "DATA" newData)
                        (setq count (1+ count))
                      )
                    )
                  )
                )
              )
              (princ (strcat (itoa count) " desenhos atualizados."))
              (WriteLog (strcat "FASE: DATA alterada para '" newData "' em " (itoa count) " desenhos"))
            )
          )
        )
      )
      
      (vla-Regen doc acActiveViewport)
      (alert (strcat "Fase de Projeto alterada!\n\nNova Fase: " newFase))
    )
    (princ "\nCancelado - fase vazia.")
  )
  (princ)
)

;; ============================================================================
;; EDITAR CAMPO GLOBAL - Função genérica para editar qualquer campo
;; ============================================================================
;; Recebe uma lista de tags permitidos e permite ao utilizador escolher qual editar
;; Suporta aplicar a todos os desenhos ou a uma seleção específica
(defun EditarCampoGlobal (tagList / doc i choice selectedTag newVal targets targetList count desNum blkHandle currentVal)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== EDITAR CAMPO GLOBAL ===")
  (princ "\n\nCampos disponiveis:")
  
  ;; Listar campos
  (setq i 1)
  (foreach tag tagList
    (princ (strcat "\n " (itoa i) ". " tag))
    (setq i (1+ i))
  )
  (princ "\n 0. Cancelar")
  
  (princ "\n-----------------------------------------")
  (setq choice (getint "\nEscolha o campo: "))
  
  (if (and choice (> choice 0) (<= choice (length tagList)))
    (progn
      (setq selectedTag (nth (1- choice) tagList))
      
      ;; Mostrar valor atual do primeiro desenho encontrado
      (setq currentVal nil)
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (not currentVal)
                 (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (and (not currentVal) (IsTargetBlock blk))
              (setq currentVal (GetAttValue blk selectedTag))
            )
          )
        )
      )
      (if currentVal
        (princ (strcat "\n\nValor atual: '" currentVal "'"))
      )
      
      (princ (strcat "\n--> A editar: " selectedTag))
      (setq newVal (getstring T "\nNovo Valor: "))
      
      ;; Escolher desenhos alvo
      (princ "\n\n--> Aplicar a quais desenhos?")
      (princ "\n    Enter = TODOS")
      (princ "\n    Lista = 1,2,5 ou 1-10")
      (setq targets (getstring T "\nDesenhos: "))
      
      (setq targetList nil)
      (if (/= targets "")
        (setq targetList (StrSplit targets ","))
      )
      
      (princ "\nA aplicar alteracoes... ")
      (setq count 0)
      
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (setq desNum (GetAttValue blk "DES_NUM"))
                (setq blkHandle (vla-get-Handle blk))
                
                (if (or (null targetList) 
                        (IsNumberInList desNum targetList))
                  (progn
                    (UpdateSingleTag blkHandle selectedTag newVal)
                    (setq count (1+ count))
                  )
                )
              )
            )
          )
        )
      )
      
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat "GLOBAL: " selectedTag " = '" newVal "' em " (itoa count) " desenhos"))
      (alert (strcat "Concluido!\nO campo '" selectedTag "' foi atualizado em " (itoa count) " desenhos."))
    )
    (if (/= choice 0)
      (princ "\nOpcao invalida.")
      (princ "\nCancelado.")
    )
  )
  (princ)
)

;; ============================================================================
;; EXTRAIR NUMERO DE UMA STRING (remove letras, mantém dígitos)
;; Ex: "DIM01" -> "01", "BA02" -> "02", "03" -> "03"
;; ============================================================================
(defun ExtractNumberFromDesNum (str / result char i)
  (setq result "")
  (setq i 1)
  (repeat (strlen str)
    (setq char (substr str i 1))
    (if (and (>= (ascii char) 48) (<= (ascii char) 57))  ;; 0-9
      (setq result (strcat result char))
    )
    (setq i (1+ i))
  )
  (if (= result "") "00" result)
)

;; ============================================================================
;; NUMERAR DESENHOS (Menu Layouts)
;; Modos: 1) Geral (sequencial), 2) Por Tipo, 3) Por Elemento
;; ============================================================================
(defun NumerarDesenhos ( / doc prefix modoNumerar tipoList elementoList i item count numSeq desenhosGrupo blkHandle newDesNum currentTipo currentElemento targets targetList)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== NUMERAR DESENHOS ===")
  (princ "\nRenumera DES_NUM: 01, 02, 03...")
  
  (setq prefix (getstring T "\nPrefixo (Enter para nenhum): "))
  
  (princ "\n\n--> Modo de numeracao:")
  (princ "\n    1. GERAL (sequencial)")
  (princ "\n    2. Por TIPO (reinicia em cada tipo)")
  (princ "\n    3. Por ELEMENTO (reinicia em cada elemento)")
  (initget "1 2 3")
  (setq modoNumerar (getkword "\n    Opcao [1/2/3] <1>: "))
  (if (null modoNumerar) (setq modoNumerar "1"))
  
  (cond
    ;; GERAL - sequencial
    ((= modoNumerar "1")
     (princ "\n\n--> Quais desenhos? (Enter=TODOS, ou 1,2,5): ")
     (setq targets (getstring T ""))
     (setq targetList nil)
     (if (/= targets "") (setq targetList (StrSplit targets ",")))
     
     (setq count 0)
     (setq numSeq 1)
     (vlax-for lay (vla-get-Layouts doc)
       (if (and (/= (vla-get-ModelType lay) :vlax-true)
                (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
         (vlax-for blk (vla-get-Block lay)
           (if (IsTargetBlock blk)
             (progn
               (setq blkHandle (vla-get-Handle blk))
               (if (or (null targetList) 
                       (IsNumberInList (ExtractNumberFromDesNum (GetAttValue blk "DES_NUM")) targetList))
                 (progn
                   (setq newDesNum (strcat prefix (FormatNum numSeq)))
                   (UpdateSingleTag blkHandle "DES_NUM" newDesNum)
                   (UpdateTabName blkHandle nil)
                   (setq count (1+ count))
                   (princ (strcat "\n  -> " newDesNum))
                   (setq numSeq (1+ numSeq))
                 )
               )
             )
           )
         )
       )
     )
     (vla-Regen doc acActiveViewport)
     (alert (strcat "Numerados " (itoa count) " desenhos."))
    )
    
    ;; Por TIPO
    ((= modoNumerar "2")
     ;; Listar tipos
     (setq tipoList '())
     (vlax-for lay (vla-get-Layouts doc)
       (if (and (/= (vla-get-ModelType lay) :vlax-true)
                (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
         (vlax-for blk (vla-get-Block lay)
           (if (IsTargetBlock blk)
             (progn
               (setq currentTipo (GetAttValue blk "TIPO"))
               (if (and currentTipo (/= currentTipo ""))
                 (if (not (member currentTipo tipoList))
                   (setq tipoList (cons currentTipo tipoList))
                 )
               )
             )
           )
         )
       )
     )
     (setq tipoList (reverse tipoList))
     
     (princ "\n\nTIPOS:")
     (setq i 1)
     (foreach item tipoList (princ (strcat "\n  " (itoa i) ". " item)) (setq i (1+ i)))
     
     (princ "\n\n--> Quais TIPOS? (Enter=TODOS): ")
     (setq targets (getstring T ""))
     (setq targetList nil)
     (if (/= targets "") (setq targetList (StrSplit targets ",")))
     
     (setq count 0)
     (setq i 1)
     (foreach item tipoList
       (if (or (null targetList) (member (itoa i) targetList))
         (progn
           (setq numSeq 1)
           (setq desenhosGrupo '())
           (vlax-for lay (vla-get-Layouts doc)
             (if (and (/= (vla-get-ModelType lay) :vlax-true)
                      (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
               (vlax-for blk (vla-get-Block lay)
                 (if (IsTargetBlock blk)
                   (if (= (GetAttValue blk "TIPO") item)
                     (setq desenhosGrupo (cons (vla-get-Handle blk) desenhosGrupo))
                   )
                 )
               )
             )
           )
           (setq desenhosGrupo (reverse desenhosGrupo))
           (foreach blkHandle desenhosGrupo
             (setq newDesNum (strcat prefix (FormatNum numSeq)))
             (UpdateSingleTag blkHandle "DES_NUM" newDesNum)
             (UpdateTabName blkHandle nil)
             (setq count (1+ count))
             (princ (strcat "\n  [" item "] -> " newDesNum))
             (setq numSeq (1+ numSeq))
           )
         )
       )
       (setq i (1+ i))
     )
     (vla-Regen doc acActiveViewport)
     (alert (strcat "Numerados " (itoa count) " desenhos por TIPO."))
    )
    
    ;; Por ELEMENTO
    ((= modoNumerar "3")
     ;; Listar elementos
     (setq elementoList '())
     (vlax-for lay (vla-get-Layouts doc)
       (if (and (/= (vla-get-ModelType lay) :vlax-true)
                (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
         (vlax-for blk (vla-get-Block lay)
           (if (IsTargetBlock blk)
             (progn
               (setq currentElemento (GetAttValue blk "ELEMENTO"))
               (if (and currentElemento (/= currentElemento ""))
                 (if (not (member currentElemento elementoList))
                   (setq elementoList (cons currentElemento elementoList))
                 )
               )
             )
           )
         )
       )
     )
     (setq elementoList (reverse elementoList))
     
     (princ "\n\nELEMENTOS:")
     (setq i 1)
     (foreach item elementoList (princ (strcat "\n  " (itoa i) ". " item)) (setq i (1+ i)))
     
     (princ "\n\n--> Quais ELEMENTOS? (Enter=TODOS): ")
     (setq targets (getstring T ""))
     (setq targetList nil)
     (if (/= targets "") (setq targetList (StrSplit targets ",")))
     
     (setq count 0)
     (setq i 1)
     (foreach item elementoList
       (if (or (null targetList) (member (itoa i) targetList))
         (progn
           (setq numSeq 1)
           (setq desenhosGrupo '())
           (vlax-for lay (vla-get-Layouts doc)
             (if (and (/= (vla-get-ModelType lay) :vlax-true)
                      (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
               (vlax-for blk (vla-get-Block lay)
                 (if (IsTargetBlock blk)
                   (if (= (GetAttValue blk "ELEMENTO") item)
                     (setq desenhosGrupo (cons (vla-get-Handle blk) desenhosGrupo))
                   )
                 )
               )
             )
           )
           (setq desenhosGrupo (reverse desenhosGrupo))
           (foreach blkHandle desenhosGrupo
             (setq newDesNum (strcat prefix (FormatNum numSeq)))
             (UpdateSingleTag blkHandle "DES_NUM" newDesNum)
             (UpdateTabName blkHandle nil)
             (setq count (1+ count))
             (princ (strcat "\n  [" item "] -> " newDesNum))
             (setq numSeq (1+ numSeq))
           )
         )
       )
       (setq i (1+ i))
     )
     (vla-Regen doc acActiveViewport)
     (alert (strcat "Numerados " (itoa count) " desenhos por ELEMENTO."))
    )
  )
  (princ)
)

;; ============================================================================
;; SUBMENU 2: EXPORTAR
;; ============================================================================
(defun Menu_Exportar ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- EXPORTAR LISTA DE DESENHOS ---")
    (princ "\n   1. Gerar CSV (Default)")
    (princ "\n   2. Gerar CSV (Configurar Colunas)")
    (princ "\n   3. Gerar CSV (Todos os Campos)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/0]: "))
    (cond
      ((= optSub "1") (Run_GenerateCSV_Default))
      ((= optSub "2") (Run_GenerateCSV_Custom))
      ((= optSub "3") (Run_GenerateCSV_AllFields))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
)

;; ============================================================================
;; EXPORTAR CSV - DEFAULT (colunas principais)
;; ============================================================================
(defun Run_GenerateCSV_Default ( / )
  ;; Default simplificado: campos principais
  (Run_GenerateCSV_Engine '("DWG_SOURCE" "TIPO" "DES_NUM" "ELEMENTO" "TITULO" "REVISAO_ATUAL" "ID_CAD"))
)

;; ============================================================================
;; EXPORTAR CSV - TODOS OS CAMPOS (29 colunas)
;; ============================================================================
(defun Run_GenerateCSV_AllFields ( / )
  ;; Todos os campos na ordem especificada
  (Run_GenerateCSV_Engine nil)
)

;; ============================================================================
;; EXPORTAR CSV - CUSTOM (escolher colunas)
;; ============================================================================
(defun Run_GenerateCSV_Custom ( / allTags selectedTags i choice userInput tagList)
  ;; Obter todos os tags disponíveis
  (setq allTags (GetAllAvailableTags))
  
  (if (null allTags)
    (princ "\nNenhum desenho encontrado.")
    (progn
      (princ "\n\n=== CONFIGURAR COLUNAS CSV ===")
      (princ "\n\nTags disponiveis:")
      (setq i 1)
      (foreach tag allTags
        (princ (strcat "\n " (itoa i) ". " tag))
        (setq i (1+ i))
      )
      
      (princ "\n\n--> Selecione os tags a exportar:")
      (princ "\n    (Exemplo: 1,3,5 ou 2-8 ou 1,3-5,9)")
      (princ "\n    Enter = TODOS")
      (setq userInput (getstring T "\nOpcao: "))
      
      (if (= userInput "")
        ;; TODOS
        (setq selectedTags allTags)
        ;; SELECAO
        (setq selectedTags (ParseTagSelection allTags userInput))
      )
      
      (if (null selectedTags)
        (princ "\nNenhum tag selecionado.")
        (progn
          ;; Forcar inclusao de campos obrigatorios (DES_NUM e ID_CAD)
          (setq mandatoryTags '("DES_NUM" "ID_CAD"))
          (foreach mandatory mandatoryTags
            (if (not (member mandatory selectedTags))
              (progn
                (setq selectedTags (cons mandatory selectedTags))
                (princ (strcat "\n[INFO] Campo obrigatorio adicionado automaticamente: " mandatory))
              )
            )
          )
          
          (princ (strcat "\n\nTags selecionados: " (itoa (length selectedTags))))
          (foreach tag selectedTags
            (princ (strcat "\n  - " tag))
          )
          
          ;; Perguntar ordem
          (princ "\n\n--> Alterar ordem das colunas?")
          (initget "Sim Nao")
          (if (= (getkword "\n    [Sim/Nao] <Nao>: ") "Sim")
            (setq selectedTags (ReorderTags selectedTags))
          )
          
          ;; Exportar com tags customizados
          (Run_GenerateCSV_Engine selectedTags)
        )
      )
    )
  )
)

;; Obtem todos os tags disponiveis (DES_NUM sempre incluido, revisoes compactadas)
;; ELEMENTO_TITULO é excluído pois é campo calculado (não exportável)
(defun GetAllAvailableTags ( / doc found blk allTags tag)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq allTags '())
  (setq found nil)
  
  (vlax-for lay (vla-get-Layouts doc)
    (if (and (not found) 
             (/= (vla-get-ModelType lay) :vlax-true))
      (vlax-for blk (vla-get-Block lay)
        (if (IsTargetBlock blk)
          (progn
            (foreach att (vlax-invoke blk 'GetAttributes)
              (setq tag (strcase (vla-get-TagString att)))
              ;; Excluir revisoes individuais e ELEMENTO_TITULO (calculado)
              (if (and (not (wcmatch tag "REV_?,DATA_?,DESC_?"))
                       (/= tag "ELEMENTO_TITULO")
                       (not (member tag allTags)))
                (setq allTags (cons tag allTags))
              )
            )
            ;; Adicionar "REVISAO_ATUAL" como campo virtual
            (if (not (member "REVISAO_ATUAL" allTags))
              (setq allTags (cons "REVISAO_ATUAL" allTags))
            )
            (setq found T)
          )
        )
      )
    )
  )
  
  (vl-sort allTags '<)
)

;; Converte string de selecao (ex: "1,3" ou "2-5") em lista de tags
(defun ParseTagSelection (allTags selStr / result parts part startNum endNum i num)
  (setq result '())
  (setq parts (StrSplit selStr ","))
  
  (foreach part parts
    (setq part (vl-string-trim " " part))
    (if (vl-string-search "-" part)
      ;; Range
      (progn
        (setq startNum (atoi (car (StrSplit part "-"))))
        (setq endNum (atoi (cadr (StrSplit part "-"))))
        (setq i startNum)
        (while (<= i endNum)
          (if (and (> i 0) (<= i (length allTags)))
            (if (not (member (nth (1- i) allTags) result))
              (setq result (cons (nth (1- i) allTags) result))
            )
          )
          (setq i (1+ i))
        )
      )
      ;; Numero unico
      (progn
        (setq num (atoi part))
        (if (and (> num 0) (<= num (length allTags)))
          (if (not (member (nth (1- num) allTags) result))
            (setq result (cons (nth (1- num) allTags) result))
          )
        )
      )
    )
  )
  
  (reverse result)
)

;; Permite reordenar tags
(defun ReorderTags (tagList / newOrder i currentTag newPos loop)
  (setq newOrder '())
  (setq i 1)
  
  (princ "\n\n=== REORDENAR COLUNAS ===")
  (princ "\nDigite a ordem desejada (1,2,3...)")
  (princ "\nOu pressione Enter para manter ordem atual\n")
  
  (foreach tag tagList
    (princ (strcat "\n" (itoa i) ". " tag))
    (setq i (1+ i))
  )
  
  (princ "\n\nNova ordem (ex: 3,1,2,4): ")
  (setq userInput (getstring T))
  
  (if (= userInput "")
    tagList
    (progn
      (setq parts (StrSplit userInput ","))
      (foreach part parts
        (setq num (atoi (vl-string-trim " " part)))
        (if (and (> num 0) (<= num (length tagList)))
          (setq newOrder (cons (nth (1- num) tagList) newOrder))
        )
      )
      (reverse newOrder)
    )
  )
)

;; ============================================================================
;; MOTOR DE EXPORTACAO CSV (com tags configuráveis)
;; ============================================================================
(defun Run_GenerateCSV_Engine (customTags / doc path dwgName defaultName csvFile fileDes layoutList dataList sortMode 
                                             duplicates continueExport userChoice dateErrors allDateErrors 
                                             blk layName header row tags desNumIdx)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq dwgName (GetDWGName))
  
  ;; Definir tags a exportar
  (if customTags
    (setq tags customTags)
    ;; Default: Ordem completa conforme especificação
    (setq tags '("LAYOUT" "CLIENTE" "OBRA" "LOCALIZACAO" "ESPECIALIDADE" "FASE" 
                 "DATA" "PROJETOU" "DES_NUM" "TIPO" "ELEMENTO" "TITULO"
                 "REV_A" "DATA_A" "DESC_A"
                 "REV_B" "DATA_B" "DESC_B"
                 "REV_C" "DATA_C" "DESC_C"
                 "REV_D" "DATA_D" "DESC_D"
                 "REV_E" "DATA_E" "DESC_E"
                 "DWG_SOURCE" "ID_CAD"))
  )
  
  ;; Encontrar índice de DES_NUM para validação de duplicados
  (setq desNumIdx (GetTagIndex tags "DES_NUM"))
  
  (princ "\nA recolher dados (Ignorando TEMPLATE)... ")
  (setq dataList '())
  (setq allDateErrors "")
  (setq layoutList (GetLayoutsRaw doc))
  
  (foreach lay layoutList
    (vlax-for blk (vla-get-Block lay)
      (if (IsTargetBlock blk)
        (progn
          (setq layName (vla-get-Name lay))
          (setq dateErrors (ValidateRevisionDates blk))
          (if dateErrors
            (setq allDateErrors (strcat allDateErrors "Des " (GetAttValue blk "DES_NUM") " (" layName "): " dateErrors "\n"))
          )
          ;; Coletar dados baseado nos tags selecionados
          (setq row (CollectRowData blk layName dwgName tags))
          (setq dataList (cons row dataList))
        )
      )
    )
  )
  
  ;; Validar duplicados apenas se DES_NUM estiver presente
  (if desNumIdx
    (setq duplicates (FindDuplicateDES_NUM_ByIndex dataList desNumIdx))
    (setq duplicates nil)
  )
  
  (setq continueExport T)
  
  (if duplicates
    (progn
      (alert (strcat "AVISO: DES_NUM DUPLICADOS!\n\n" duplicates))
      (initget "Sim Nao")
      (setq userChoice (getkword "\nContinuar exportação? [Sim/Nao] <Nao>: "))
      (if (or (null userChoice) (= userChoice "Nao"))
        (setq continueExport nil)
      )
    )
  )
  
  (if (and continueExport (/= allDateErrors ""))
    (progn
      (alert (strcat "AVISO: DATAS DE REVISÃO INCOERENTES!\n\n" allDateErrors))
      (initget "Sim Nao")
      (setq userChoice (getkword "\nContinuar exportação? [Sim/Nao] <Sim>: "))
      (if (= userChoice "Nao")
        (setq continueExport nil)
      )
    )
  )
  
  (if continueExport
    (progn
      (setq defaultName (strcat path dwgName "_Lista.csv"))
      (setq csvFile (getfiled "Guardar Lista CSV" defaultName "csv" 1))
      (if csvFile
        (progn
          (initget "1 2")
          (setq sortMode (getkword "\nOrdenar por? [1] Tipo / [2] Número <2>: "))
          (if (not sortMode) (setq sortMode "2"))
          
          ;; Ordenar dados
          (setq dataList (SortDataList dataList tags sortMode))
          
          ;; Escrever ficheiro
          (setq fileDes (open csvFile "w"))
          (if fileDes
            (progn
              ;; Header
              (setq header (BuildCSVHeader tags))
              (write-line header fileDes)
              
              ;; Dados
              (foreach row dataList
                (write-line (BuildCSVRow row) fileDes)
              )
              (close fileDes)
              (alert (strcat "Sucesso! Ficheiro criado:\n" csvFile "\n\nColunas: " (itoa (length tags))))
            )
            (alert "Erro: Ficheiro aberto?")
          )
        )
        (princ "\nCancelado.")
      )
    )
    (princ "\nExportação cancelada.")
  )
  (princ)
)

;; Coletar dados de uma linha baseado nos tags
(defun CollectRowData (blk layName dwgName tags / row value maxRev)
  (setq row '())
  (foreach tag tags
    (cond
      ((= tag "DWG_SOURCE") (setq value dwgName))
      ((= tag "ID_CAD") (setq value (vla-get-Handle blk)))
      ((= tag "LAYOUT") (setq value layName))
      ((= tag "REVISAO_ATUAL")
        (setq maxRev (GetMaxRevision blk))
        (setq value (strcat (CleanCSV (car maxRev)) ";" 
                           (CleanCSV (cadr maxRev)) ";" 
                           (CleanCSV (caddr maxRev))))
      )
      ;; Campos de revisão individuais (mapeamento)
      ((= tag "REV_A") (setq value (CleanCSV (GetAttValue blk "REV_A"))))
      ((= tag "DATA_A") (setq value (CleanCSV (GetAttValue blk "DATA_A"))))
      ((= tag "DESC_A") (setq value (CleanCSV (GetAttValue blk "DESC_A"))))
      ((= tag "REV_B") (setq value (CleanCSV (GetAttValue blk "REV_B"))))
      ((= tag "DATA_B") (setq value (CleanCSV (GetAttValue blk "DATA_B"))))
      ((= tag "DESC_B") (setq value (CleanCSV (GetAttValue blk "DESC_B"))))
      ((= tag "REV_C") (setq value (CleanCSV (GetAttValue blk "REV_C"))))
      ((= tag "DATA_C") (setq value (CleanCSV (GetAttValue blk "DATA_C"))))
      ((= tag "DESC_C") (setq value (CleanCSV (GetAttValue blk "DESC_C"))))
      ((= tag "REV_D") (setq value (CleanCSV (GetAttValue blk "REV_D"))))
      ((= tag "DATA_D") (setq value (CleanCSV (GetAttValue blk "DATA_D"))))
      ((= tag "DESC_D") (setq value (CleanCSV (GetAttValue blk "DESC_D"))))
      ((= tag "REV_E") (setq value (CleanCSV (GetAttValue blk "REV_E"))))
      ((= tag "DATA_E") (setq value (CleanCSV (GetAttValue blk "DATA_E"))))
      ((= tag "DESC_E") (setq value (CleanCSV (GetAttValue blk "DESC_E"))))
      (T (setq value (CleanCSV (GetAttValue blk tag))))
    )
    (setq row (cons value row))
  )
  (reverse row)
)

;; Constroi header CSV com nomes amigáveis
(defun BuildCSVHeader (tags / header friendlyName)
  (setq header "")
  (foreach tag tags
    (cond
      ((= tag "REVISAO_ATUAL") (setq friendlyName "REVISAO;DATA;DESCRICAO"))
      ((= tag "LAYOUT") (setq friendlyName "TAG DO LAYOUT"))
      ((= tag "DATA") (setq friendlyName "DATA 1ª EMISSÃO"))
      ((= tag "DES_NUM") (setq friendlyName "NUMERO DE DESENHO"))
      ((= tag "REV_A") (setq friendlyName "REVISÃO A"))
      ((= tag "DATA_A") (setq friendlyName "DATA REVISAO A"))
      ((= tag "DESC_A") (setq friendlyName "DESCRIÇÃO REVISÃO A"))
      ((= tag "REV_B") (setq friendlyName "REVISÃO B"))
      ((= tag "DATA_B") (setq friendlyName "DATA REVISAO B"))
      ((= tag "DESC_B") (setq friendlyName "DESCRIÇÃO REVISÃO B"))
      ((= tag "REV_C") (setq friendlyName "REVISÃO C"))
      ((= tag "DATA_C") (setq friendlyName "DATA REVISAO C"))
      ((= tag "DESC_C") (setq friendlyName "DESCRIÇÃO REVISÃO C"))
      ((= tag "REV_D") (setq friendlyName "REVISÃO D"))
      ((= tag "DATA_D") (setq friendlyName "DATA REVISAO D"))
      ((= tag "DESC_D") (setq friendlyName "DESCRIÇÃO REVISÃO D"))
      ((= tag "REV_E") (setq friendlyName "REVISÃO E"))
      ((= tag "DATA_E") (setq friendlyName "DATA REVISAO E"))
      ((= tag "DESC_E") (setq friendlyName "DESCRIÇÃO REVISÃO E"))
      ((= tag "DWG_SOURCE") (setq friendlyName "NOME DWG"))
      (T (setq friendlyName tag))
    )
    (setq header (strcat header (if (/= header "") ";" "") friendlyName))
  )
  header
)

;; Constroi linha CSV
(defun BuildCSVRow (row / line)
  (setq line "")
  (foreach value row
    (setq line (strcat line (if (/= line "") ";" "") value))
  )
  line
)

;; Ordenar dados
(defun SortDataList (dataList tags sortMode / typeIdx numIdx)
  (setq typeIdx (GetTagIndex tags "TIPO"))
  (setq numIdx (GetTagIndex tags "DES_NUM"))
  
  (cond
    ((= sortMode "1")
      (if (and typeIdx numIdx)
        (vl-sort dataList 
          '(lambda (a b)
            (if (= (strcase (nth typeIdx a)) (strcase (nth typeIdx b)))
              (< (atoi (nth numIdx a)) (atoi (nth numIdx b)))
              (< (strcase (nth typeIdx a)) (strcase (nth typeIdx b)))
            )
          )
        )
        dataList
      )
    )
    ((= sortMode "2")
      (if numIdx
        (vl-sort dataList 
          '(lambda (a b) (< (atoi (nth numIdx a)) (atoi (nth numIdx b))))
        )
        dataList
      )
    )
    (T dataList)
  )
)

;; Obter indice de um tag na lista
(defun GetTagIndex (tags targetTag / i found index)
  (setq i 0 found nil index nil)
  (while (and (< i (length tags)) (not found))
    (if (= (nth i tags) targetTag)
      (progn
        (setq index i)
        (setq found T)
      )
    )
    (setq i (1+ i))
  )
  index
)

;; ============================================================================
;; SUBMENU 3: IMPORTAR
;; ============================================================================
(defun Menu_Importar ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (princ "\n\n   --- IMPORTAR LISTA DE DESENHOS ---")
    (princ "\n   1. Importar CSV (por ID_CAD)")
    (princ "\n   2. Importar CSV de Alterações (por Layout)")
    (princ "\n   3. Importar de DB (todos os campos)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/0]: "))
    (cond
      ((= optSub "1") (Run_ImportCSV))
      ((= optSub "2") (Run_ImportCSV_ByLayout))
      ((= optSub "3") (Run_ImportFromDB))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
)

;; ============================================================================
;; SUBMENU 4: GERIR LAYOUTS
;; ============================================================================
(defun Menu_GerirLayouts ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (princ "\n\n   --- GERIR LAYOUTS ---")
    (princ "\n   1. Gerar Novos (TEMPLATE)")
    (princ "\n   2. Ordenar Tabs")
    (princ "\n   3. Numerar Desenhos")
    (princ "\n   4. Apagar Desenhos")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/0]: "))
    (cond
      ((= optSub "1") (Run_GenerateLayouts_FromTemplate_V26))
      ((= optSub "2") (Run_SortLayouts_Engine))
      ((= optSub "3") (NumerarDesenhos))
      ((= optSub "4") (ApagarDesenhos))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
)

;; ============================================================================
;; APAGAR DESENHOS (Nova funcionalidade)
;; ============================================================================
;; Permite apagar todos os layouts ou uma selecao especifica
;; A selecao funciona pelo numero do desenho (parte numerica do DES_NUM)
(defun ApagarDesenhos ( / doc drawList optMode targets selectedList confirmMsg count layToDelete)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq drawList (GetDrawingList))
  
  (if (or (null drawList) (= (length drawList) 0))
    (progn
      (alert "Nenhum desenho encontrado!")
      (princ "\nNenhum desenho para apagar.")
    )
    (progn
      (princ "\n\n=== APAGAR DESENHOS ===")
      (princ (strcat "\nTotal de desenhos: " (itoa (length drawList))))
      
      ;; Listar desenhos com numeracao
      (princ "\n\n--- DESENHOS DISPONIVEIS ---")
      (setq i 1)
      (foreach item drawList
        (princ (strcat "\n " (itoa i) ". DES_NUM=" (cadr item) " | Layout=" (caddr item)))
        (setq i (1+ i))
      )
      
      ;; Escolher modo
      (princ "\n\n-----------------------------------------")
      (princ "\n[T] Apagar TODOS")
      (princ "\n[S] Apagar SELECAO (ex: 1,3,5 ou 2-5)")
      (princ "\n[0] Cancelar")
      (initget "T S 0")
      (setq optMode (getkword "\n\nOpcao [T/S/0]: "))
      
      (cond
        ;; TODOS
        ((= optMode "T")
          (setq selectedList drawList)
          (setq confirmMsg (strcat "ATENCAO!\n\nVai apagar TODOS os " (itoa (length drawList)) " desenhos!\n\nTem a certeza?"))
        )
        
        ;; SELECAO
        ((= optMode "S")
          (princ "\n\n--> Indique os numeros dos desenhos a apagar:")
          (princ "\n    (Use a numeracao da lista, nao o DES_NUM)")
          (princ "\n    Exemplos: 1,3,5 ou 2-5 ou 1,3-5,8")
          (setq targets (getstring T "\n\nSelecao: "))
          
          (if (and targets (/= targets ""))
            (progn
              (setq selectedList (ParseSelectionToList drawList targets))
              (if (and selectedList (> (length selectedList) 0))
                (setq confirmMsg (strcat "Vai apagar " (itoa (length selectedList)) " desenho(s):\n\n"
                                         (apply 'strcat 
                                                (mapcar '(lambda (x) (strcat "- DES_NUM=" (cadr x) " (" (caddr x) ")\n")) 
                                                        selectedList))
                                         "\nTem a certeza?"))
                (progn
                  (princ "\nSelecao invalida ou vazia.")
                  (setq selectedList nil)
                )
              )
            )
            (progn
              (princ "\nCancelado - nenhuma selecao.")
              (setq selectedList nil)
            )
          )
        )
        
        ;; CANCELAR
        (T
          (princ "\nOperacao cancelada.")
          (setq selectedList nil)
        )
      )
      
      ;; Executar apagamento se ha selecao
      (if (and selectedList (> (length selectedList) 0))
        (progn
          (initget "Sim Nao")
          (if (= (getkword (strcat "\n" confirmMsg " [Sim/Nao] <Nao>: ")) "Sim")
            (progn
              (princ "\nA apagar layouts...")
              (setq count 0)
              
              (foreach item selectedList
                ;; item = (handle desNum layoutName tipo)
                (setq layToDelete nil)
                
                ;; Encontrar o layout pelo nome
                (vlax-for lay (vla-get-Layouts doc)
                  (if (and (not layToDelete)
                           (= (strcase (vla-get-Name lay)) (strcase (caddr item))))
                    (setq layToDelete lay)
                  )
                )
                
                ;; Apagar o layout
                (if layToDelete
                  (if (not (vl-catch-all-error-p 
                             (vl-catch-all-apply 'vla-Delete (list layToDelete))))
                    (progn
                      (setq count (1+ count))
                      (princ (strcat "\n  Apagado: " (caddr item) " (DES_NUM=" (cadr item) ")"))
                      (WriteLog (strcat "APAGAR: Layout '" (caddr item) "' DES_NUM=" (cadr item) " eliminado"))
                    )
                    (princ (strcat "\n  ERRO ao apagar: " (caddr item)))
                  )
                  (princ (strcat "\n  Layout nao encontrado: " (caddr item)))
                )
              )
              
              (vla-Regen doc acActiveViewport)
              (alert (strcat "Concluido!\n\n" (itoa count) " layout(s) apagado(s)."))
            )
            (princ "\nOperacao cancelada pelo utilizador.")
          )
        )
      )
    )
  )
  (princ)
)

;; ============================================================================
;; MOTOR DE CONSTRUCAO DO NOME DO TAB - V41.0 (Formato Fixo)
;; ============================================================================
;; Formato FIXO: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO-R
;; Exemplo: 779-EST-BA-01-E00-A (ou 779-EST-BA-01-E00 se R vazio)
;; 
;; Atributos utilizados:
;;   PROJ_NUM - Número do projeto (ex: 779)
;;   PFIX     - Prefixo do tipo de desenho (ex: BA, DIM)
;;   DES_NUM  - Número do desenho (ex: 01, 02)
;;   EMISSAO  - Código de emissão (ex: E00)
;;   R        - Letra da revisão atual (ex: A, B, vazio)
;; ============================================================================
(defun BuildTabName (blk revOverride / projNum pfix desNum emissao revVal result)
  ;; Obter valores dos atributos do bloco
  (setq projNum (GetAttValue blk "PROJ_NUM"))
  (setq pfix (GetAttValue blk "PFIX"))
  (setq desNum (GetAttValue blk "DES_NUM"))
  (setq emissao (GetAttValue blk "EMISSAO"))
  
  ;; Se revOverride fornecido, usar esse valor, senão ler do bloco
  (if revOverride
    (setq revVal revOverride)
    (setq revVal (GetAttValue blk "R"))
  )
  
  ;; Construir nome: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO[-R]
  ;; EST é fixo para "Estabilidade"
  (setq result "")
  
  ;; PROJ_NUM (se existir)
  (if (and projNum (/= projNum ""))
    (setq result projNum)
  )
  
  ;; -EST (fixo)
  (setq result (strcat result (if (/= result "") "-" "") "EST"))
  
  ;; -PFIX (se existir)
  (if (and pfix (/= pfix ""))
    (setq result (strcat result "-" pfix))
  )
  
  ;; -DES_NUM (obrigatório)
  (if (and desNum (/= desNum ""))
    (setq result (strcat result "-" desNum))
    (setq result (strcat result "-00"))  ;; Default se não existir
  )
  
  ;; -EMISSAO (se existir)
  (if (and emissao (/= emissao ""))
    (setq result (strcat result "-" emissao))
  )
  
  ;; -R (apenas se existir e não vazio)
  (if (and revVal (/= revVal "") (/= revVal "-") (/= revVal " "))
    (setq result (strcat result "-" revVal))
  )
  
  result
)

;; ============================================================================
;; ATUALIZAR NOME DE TAB DE UM BLOCO ESPECIFICO
;; ============================================================================
;; Atualiza o nome do tab do layout onde está o bloco
;; revOverride - valor opcional de R para usar (evita problemas de cache)
(defun UpdateTabName (handle revOverride / doc lay blk foundLay foundBlk newTabName atts ename obj)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  ;; Obter o bloco diretamente pelo handle (garante valores atualizados)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if ename
    (setq obj (vlax-ename->vla-object ename)))
  
  (if (and obj (IsTargetBlock obj))
    (progn
      ;; Forçar refresh do bloco
      (vla-Update obj)
      
      ;; Agora procurar o layout onde está este bloco (para renomear)
      (setq foundLay nil)
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (not foundLay)
                 (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (and (not foundLay) 
                     (= (vla-get-Handle blk) handle))
              (setq foundLay lay)
            )
          )
        )
      )
      
      ;; Se encontrou o layout, renomear usando formato fixo
      (if foundLay
        (progn
          (setq newTabName (BuildTabName obj revOverride))
          (if (and newTabName (/= newTabName ""))
            (vl-catch-all-apply 'vla-put-Name (list foundLay newTabName))
          )
        )
      )
    )
  )
)

;; ============================================================================
;; ATUALIZAR NOMES DE TODOS OS LAYOUTS
;; ============================================================================
;; Percorre todos os layouts (exceto Model e TEMPLATE) e atualiza os nomes
;; baseado no formato fixo: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO-R
(defun AtualizarNomesLayouts ( / doc count newTabName oldName blk lay)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== ATUALIZAR NOMES DOS LAYOUTS ===")
  (princ "\nFormato: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO-R")
  (princ "\nExemplo: 779-EST-BA-01-E00-A")
  
  (initget "Sim Nao")
  (if (= (getkword "\n\nRenomear todos os layouts? [Sim/Nao] <Nao>: ") "Sim")
    (progn
      (setq count 0)
      (princ "\nA processar...")
      
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (setq newTabName (BuildTabName blk nil))
                (if (and newTabName (/= newTabName ""))
                  (progn
                    (setq oldName (vla-get-Name lay))
                    (if (not (vl-catch-all-error-p 
                               (vl-catch-all-apply 'vla-put-Name (list lay newTabName))))
                      (progn
                        (setq count (1+ count))
                        (princ (strcat "\n  " oldName " -> " newTabName))
                      )
                      (princ (strcat "\n  [ERRO] " oldName))
                    )
                  )
                )
              )
            )
          )
        )
      )
      
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat "ATUALIZAR NOMES: " (itoa count) " layouts renomeados"))
      (alert (strcat "Concluido!\n\n" (itoa count) " layouts renomeados."))
    )
    (princ "\nCancelado.")
  )
  (princ)
)

;; ============================================================================
;; MÓDULO 2: EDIÇÃO SELETIVA (AGORA INTELIGENTE)
;; ============================================================================
(defun Run_GlobalVars_Selective_V29 ( / validTags i attList choice idx selectedTag newVal targets targetList doc count desNum targetNum blkNum)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq validTags (GetExampleTags)) 
  
  (princ "\n\n=== ESCOLHA O CAMPO A ALTERAR ===")
  (setq i 1)
  (setq attList '())
  (foreach tName validTags 
    (princ (strcat "\n " (itoa i) ". " tName))
    (setq attList (cons tName attList))
    (setq i (1+ i))
  )
  (setq attList (reverse attList)) 
  
  (princ "\n-----------------------------------------")
  (setq choice (getint "\nDigite o número do campo: "))
  
  (if (and choice (> choice 0) (<= choice (length attList)))
    (progn
      (setq selectedTag (nth (1- choice) attList))
      
      (princ (strcat "\n\n--> A editar: " selectedTag))
      (setq newVal (getstring T "\nNovo Valor: "))

      (princ "\n\n--> Aplicar a quais desenhos?")
      (princ "\n(Enter = TODOS | Lista = 2,04,9)")
      (setq targets (getstring T "\nOpção: "))
      
      (setq targetList nil)
      (if (/= targets "")
        (setq targetList (StrSplit targets ","))
      )

      (princ "\nA aplicar alterações... ")
      (setq count 0)
      
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (setq desNum (GetAttValue blk "DES_NUM"))
                
                ;; --- LÓGICA DE COMPARAÇÃO INTELIGENTE ---
                (if (or (null targetList) ;; Se for todos
                        (IsNumberInList desNum targetList)) ;; Nova Função de Comparação
                  (progn
                     (UpdateSingleTag (vla-get-Handle blk) selectedTag newVal)
                     (setq count (1+ count))
                  )
                )
              )
            )
          )
        )
      )
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat "GLOBAL: " selectedTag " = '" newVal "' em " (itoa count) " desenhos"))
      (alert (strcat "Concluído!\nO campo '" selectedTag "' foi atualizado em " (itoa count) " desenhos."))
    )
    (princ "\nOpção inválida.")
  )
  (graphscr)
)

;; NOVA FUNÇÃO DE COMPARAÇÃO (Texto vs Inteiro)
(defun IsNumberInList (valStr listStr / n1 n2 found item)
  (setq found nil)
  (setq n1 (atoi valStr)) ;; Converte desenho atual para inteiro (ex: "04" -> 4)
  
  (foreach item listStr
    (setq n2 (atoi item)) ;; Converte item da lista para inteiro (ex: "4" -> 4)
    ;; Compara números OU strings diretas (para casos alfanuméricos tipo "1A")
    (if (or (= n1 n2) (= (strcase valStr) (strcase item)))
      (setq found T)
    )
  )
  found
)

;; ============================================================================
;; FUNÇÕES OPERACIONAIS
;; ============================================================================

;; ============================================================================
;; SISTEMA DE LOGGING (1.5) - Apenas alteracoes em legendas
;; ============================================================================
(defun WriteLog (msg / logPath logFile timestamp dateStr timeStr userStr)
  (setq logPath (strcat (getvar "DWGPREFIX") (GetDWGName) ".log"))
  (setq dateStr (menucmd "M=$(edtime,$(getvar,date),DD-MO-YYYY)"))
  (setq timeStr (menucmd "M=$(edtime,$(getvar,date),HH:MM:SS)"))
  (setq timestamp (strcat dateStr " " timeStr))
  (setq userStr (if *JSJ_USER* *JSJ_USER* "JSJ"))
  (setq logFile (open logPath "a"))
  (if logFile
    (progn
      (write-line (strcat "[" timestamp "] [" userStr "] " msg) logFile)
      (close logFile)
    )
  )
)

;; Função para definir utilizador
(defun SetCurrentUser ( / newUser)
  (setq newUser (getstring T (strcat "\nUtilizador atual: " (if *JSJ_USER* *JSJ_USER* "<vazio>") "\nNovo utilizador: ")))
  (if (and newUser (/= newUser ""))
    (progn
      (setq *JSJ_USER* newUser)
      (WriteLog (strcat "UTILIZADOR: Sessão iniciada por " newUser))
      (princ (strcat "\nUtilizador definido: " newUser)))
    (princ "\nUtilizador não alterado.")
  )
)

;; ============================================================================
;; AUTO-CALCULAR ATRIBUTO R (1.3) - Corrigido para detectar letra da revisão
;; ============================================================================
(defun UpdateAttributeR (handle / ename obj maxRevLetter)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (if (IsTargetBlock obj)
      (progn
        ;; Determina qual a letra da última revisão preenchida (E→D→C→B→A)
        (setq maxRevLetter (GetMaxRevisionLetter obj))
        ;; Atualiza R (pode ser nil se nao houver revisoes)
        (if maxRevLetter
          (UpdateSingleTag handle "R" maxRevLetter)
          (UpdateSingleTag handle "R" "")
        )
        ;; SEMPRE atualizar o nome do tab - passa o valor de R explicitamente
        ;; para evitar problemas de cache do AutoCAD
        (UpdateTabName handle maxRevLetter)
      )
    )
  )
)

;; Função auxiliar: retorna a LETRA da última revisão preenchida (não o valor do atributo)
(defun GetMaxRevisionLetter (blk / checkRev foundLetter)
  (setq foundLetter nil)
  (foreach letra '("E" "D" "C" "B" "A")
    (if (null foundLetter)
      (progn
        (setq checkRev (GetAttValue blk (strcat "REV_" letra)))
        (if (and checkRev (/= checkRev "") (/= checkRev " "))
          (setq foundLetter letra)
        )
      )
    )
  )
  foundLetter
)

;; Função auxiliar: retorna a próxima letra de revisão
(defun GetNextRevisionLetter (currentLetter)
  (cond
    ((null currentLetter) "A")
    ((= currentLetter "") "A")
    ((= currentLetter "A") "B")
    ((= currentLetter "B") "C")
    ((= currentLetter "C") "D")
    ((= currentLetter "D") "E")
    ((= currentLetter "E") nil) ;; Máximo atingido
    (T "A")
  )
)

;; ============================================================================
;; EMITIR REVISAO - UNIFICADO (TODOS ou SELECAO)
;; ============================================================================
(defun EmitirRevisao_Unificado ( / doc drawList i item handle desNum currentLetter nextLetter revData revDesc dateStr targets targetList count selectedList)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq drawList (GetDrawingList))
  
  (if (null drawList)
    (progn
      (alert "Nenhum desenho encontrado.")
      (princ "\nNenhum desenho encontrado.")
    )
    (progn
      (princ "\n\n=== EMITIR REVISAO ===")
      (princ (strcat "\nTotal de desenhos: " (itoa (length drawList))))
      
      ;; Mostrar estado atual de cada desenho
      (princ "\n\nEstado atual das revisoes:")
      (setq i 0)
      (foreach item drawList
        (setq handle (car item))
        (setq desNum (cadr item))
        (setq currentLetter (GetMaxRevisionLetterByHandle handle))
        (setq nextLetter (GetNextRevisionLetter currentLetter))
        (setq i (1+ i))
        (if nextLetter
          (princ (strcat "\n  " (itoa i) ". Des " desNum ": " (if currentLetter currentLetter "-") " -> " nextLetter " (" (caddr item) ")"))
          (princ (strcat "\n  " (itoa i) ". Des " desNum ": " currentLetter " (MAX) (" (caddr item) ")"))
        )
      )
      
      (princ "\n\n--> Em quais desenhos emitir revisao?")
      (princ "\n    Enter = TODOS | Lista = 1,3,5 ou 2-5")
      (setq targets (getstring T "\nOpcao: "))
      
      ;; Determinar lista de desenhos selecionados
      (if (= targets "")
        ;; TODOS
        (setq selectedList drawList)
        ;; SELECAO
        (setq selectedList (ParseSelectionToList drawList targets))
      )
      
      (if (null selectedList)
        (princ "\nNenhum desenho valido selecionado.")
        (progn
          (princ (strcat "\n\nDesenhos selecionados: " (itoa (length selectedList))))
          
          (initget "Sim Nao")
          (if (= (getkword "\nConfirmar emissao? [Sim/Nao] <Nao>: ") "Sim")
            (progn
              (setq dateStr (GetTodayDate))
              (setq revData (getstring T (strcat "\nData da revisao [" dateStr "]: ")))
              (if (= revData "") (setq revData dateStr))
              (setq revDesc (getstring T "\nDescricao da revisao: "))
              
              (setq count 0)
              (foreach item selectedList
                (setq handle (car item))
                (setq desNum (cadr item))
                (setq currentLetter (GetMaxRevisionLetterByHandle handle))
                (setq nextLetter (GetNextRevisionLetter currentLetter))
                
                (if nextLetter
                  (progn
                    (EmitirRevisaoBloco handle nextLetter revData revDesc)
                    (setq count (1+ count))
                    (princ (strcat "\n  Des " desNum ": Emitida REV_" nextLetter))
                  )
                  (princ (strcat "\n  Des " desNum ": Ja esta no maximo (E)"))
                )
              )
              
              (vla-Regen doc acActiveViewport)
              (if (> count 0)
                (WriteLog (strcat "EMITIR REVISAO: " (itoa count) " desenhos - " revData " - " revDesc))
              )
              (alert (strcat "Revisao emitida em " (itoa count) " desenhos."))
            )
            (princ "\nOperacao cancelada.")
          )
        )
      )
    )
  )
  (graphscr)
  (princ)
)

;; Converte string de selecao (ex: "1,3,5" ou "2-5" ou "1,3-5,8") em lista de desenhos
(defun ParseSelectionToList (drawList selStr / result parts item startNum endNum i num)
  (setq result '())
  (setq parts (StrSplit selStr ","))
  
  (foreach part parts
    (setq part (vl-string-trim " " part))
    (if (vl-string-search "-" part)
      ;; Range (ex: "2-5")
      (progn
        (setq startNum (atoi (car (StrSplit part "-"))))
        (setq endNum (atoi (cadr (StrSplit part "-"))))
        (setq i startNum)
        (while (<= i endNum)
          (if (and (> i 0) (<= i (length drawList)))
            (progn
              (setq item (nth (1- i) drawList))
              (if (not (member item result))
                (setq result (cons item result))
              )
            )
          )
          (setq i (1+ i))
        )
      )
      ;; Numero unico
      (progn
        (setq num (atoi part))
        (if (and (> num 0) (<= num (length drawList)))
          (progn
            (setq item (nth (1- num) drawList))
            (if (not (member item result))
              (setq result (cons item result))
            )
          )
        )
      )
    )
  )
  
  (reverse result)
)

;; ============================================================================
;; FUNCOES AUXILIARES PARA EMITIR REVISAO
;; ============================================================================

;; Emite revisão num bloco específico
(defun EmitirRevisaoBloco (handle revLetter revData revDesc)
  (UpdateSingleTag handle (strcat "REV_" revLetter) revLetter)
  (UpdateSingleTag handle (strcat "DATA_" revLetter) revData)
  (UpdateSingleTag handle (strcat "DESC_" revLetter) revDesc)
  (UpdateAttributeR handle)
  ;; UpdateAttributeR já chama UpdateTabName, não precisa duplicar
)

;; Obtém a letra da última revisão por handle
(defun GetMaxRevisionLetterByHandle (handle / ename obj)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (GetMaxRevisionLetter obj)
    nil
  )
)

;; Retorna a data de hoje no formato DD-MM-YYYY
(defun GetTodayDate ( / dateStr)
  (setq dateStr (menucmd "M=$(edtime,$(getvar,date),DD-MO-YYYY)"))
  dateStr
)

;; ============================================================================
;; VALIDAR DATAS REVISÕES (1.4) - Validação em tempo real
;; ============================================================================

;; Função para converter data DD-MM-YYYY para número comparável
(defun ParseDateToNum (dateStr / parts d m y)
  (if (and dateStr (/= dateStr "") (/= dateStr "-") (/= dateStr " "))
    (progn
      (setq parts (StrSplit dateStr "-"))
      (if (>= (length parts) 3)
        (progn
          (setq d (atoi (nth 0 parts)))
          (setq m (atoi (nth 1 parts)))
          (setq y (atoi (nth 2 parts)))
          (+ (* y 10000) (* m 100) d)
        )
        0
      )
    )
    0
  )
)

;; Valida se nova data é posterior à revisão anterior (para uso em tempo real)
(defun ValidateNewRevisionDate (handle newRevLetter newDateStr / ename obj prevLetter prevDateStr prevDateNum newDateNum)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (progn
      ;; Determina a revisão anterior
      (setq prevLetter (cond
        ((= newRevLetter "B") "A")
        ((= newRevLetter "C") "B")
        ((= newRevLetter "D") "C")
        ((= newRevLetter "E") "D")
        (T nil)
      ))
      (if prevLetter
        (progn
          (setq prevDateStr (GetAttValue obj (strcat "DATA_" prevLetter)))
          (setq prevDateNum (ParseDateToNum prevDateStr))
          (setq newDateNum (ParseDateToNum newDateStr))
          ;; Se ambas as datas existem e a nova é anterior, retorna aviso
          (if (and (> prevDateNum 0) (> newDateNum 0) (< newDateNum prevDateNum))
            (strcat "AVISO: Data " newDateStr " é anterior a REV_" prevLetter " (" prevDateStr ")")
            nil
          )
        )
        nil
      )
    )
    nil
  )
)

;; Validação completa para exportação CSV
(defun ValidateRevisionDates (blk / dataA dataB dataC dataD dataE errors)
  (setq errors "")
  (setq dataA (ParseDateToNum (GetAttValue blk "DATA_A")))
  (setq dataB (ParseDateToNum (GetAttValue blk "DATA_B")))
  (setq dataC (ParseDateToNum (GetAttValue blk "DATA_C")))
  (setq dataD (ParseDateToNum (GetAttValue blk "DATA_D")))
  (setq dataE (ParseDateToNum (GetAttValue blk "DATA_E")))
  
  (if (and (> dataA 0) (> dataB 0) (< dataB dataA))
    (setq errors (strcat errors "DATA_B < DATA_A; "))
  )
  (if (and (> dataB 0) (> dataC 0) (< dataC dataB))
    (setq errors (strcat errors "DATA_C < DATA_B; "))
  )
  (if (and (> dataC 0) (> dataD 0) (< dataD dataC))
    (setq errors (strcat errors "DATA_D < DATA_C; "))
  )
  (if (and (> dataD 0) (> dataE 0) (< dataE dataD))
    (setq errors (strcat errors "DATA_E < DATA_D; "))
  )
  
  (if (= errors "") nil errors)
)
(defun Run_SortLayouts_Engine ( / doc layouts templateLay layoutList sortMode i item layObj blkInfo valTipo valNum) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq layouts (vla-get-Layouts doc)) (initget "1 2") (setq sortMode (getkword "\nCritério de Ordenação? [1] Por TIPO (e Numero) / [2] Apenas NUMERO <2>: ")) (if (not sortMode) (setq sortMode "2")) (princ "\nA ler atributos... ") (setq layoutList '()) (vlax-for lay layouts (if (and (/= (vla-get-ModelType lay) :vlax-true) (/= (strcase (vla-get-Name lay)) "TEMPLATE")) (progn (setq blkInfo (GetBlockDataInLayout (vla-get-Block lay) "LEGENDA_JSJ_V1")) (setq valTipo (car blkInfo)) (setq valNum (cadr blkInfo)) (setq layoutList (cons (list lay valTipo (atoi valNum)) layoutList))))) (cond ((= sortMode "1") (setq layoutList (vl-sort layoutList '(lambda (a b) (if (= (strcase (cadr a)) (strcase (cadr b))) (< (caddr a) (caddr b)) (< (strcase (cadr a)) (strcase (cadr b)))))))) ((= sortMode "2") (setq layoutList (vl-sort layoutList '(lambda (a b) (< (caddr a) (caddr b))))))) (princ "\nA reordenar... ") (if (not (vl-catch-all-error-p (setq templateLay (vla-Item layouts "TEMPLATE")))) (vla-put-TabOrder templateLay 1)) (setq i 2) (foreach item layoutList (setq layObj (car item)) (vl-catch-all-apply 'vla-put-TabOrder (list layObj i)) (setq i (1+ i))) (vla-Regen doc acActiveViewport) (alert "Layouts Reordenados!") (princ))
(defun GetBlockDataInLayout (blkDef blkName / valTipo valNum) (setq valTipo "" valNum "0") (vlax-for obj blkDef (if (and (= (vla-get-ObjectName obj) "AcDbBlockReference") (or (= (strcase (vla-get-Name obj)) (strcase blkName)) (= (strcase (vla-get-EffectiveName obj)) (strcase blkName)))) (progn (setq valTipo (GetAttValue obj "TIPO")) (setq valNum (GetAttValue obj "DES_NUM"))))) (list valTipo valNum))
(defun Run_GenerateLayouts_FromTemplate_V26 ( / doc layouts legendBlkName startNum endNum prefix globalData layName count refBlock foundLegend paperSpace) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq layouts (vla-get-Layouts doc)) (setq legendBlkName "LEGENDA_JSJ_V1") (if (not (catch-apply 'vla-Item (list layouts "TEMPLATE"))) (progn (alert "ERRO: Layout 'TEMPLATE' não existe.") (exit))) (setq startNum (getint "\nNúmero do Primeiro Desenho a criar (ex: 6): ")) (setq endNum (getint "\nNúmero do Último Desenho a criar (ex: 8): ")) (setq prefix (getstring "\nPrefixo do Nome do Layout (ex: EST_PISO_): ")) (setq refBlock (FindDrawingOne doc legendBlkName)) (if refBlock (setq globalData (InteractiveDataInheritance refBlock legendBlkName)) (setq globalData (GetGlobalDefinitions legendBlkName))) (setq count 0) (setq i startNum) (while (<= i endNum) (setq layName (strcat prefix (FormatNum i))) (if (not (catch-apply 'vla-Item (list layouts layName))) (progn (princ (strcat "\nA criar " layName "... ")) (setvar "CMDECHO" 0) (command "_.LAYOUT" "_Copy" "TEMPLATE" layName) (command "_.LAYOUT" "_Move" layName "") (setvar "CMDECHO" 1) (setvar "CTAB" layName) (setq paperSpace (vla-get-PaperSpace doc)) (setq foundLegend (FindBlockInLayout paperSpace legendBlkName)) (if (and foundLegend (= (vla-get-HasAttributes foundLegend) :vlax-true)) (foreach att (vlax-invoke foundLegend 'GetAttributes) (setq tag (strcase (vla-get-TagString att))) (if (= tag "DES_NUM") (vla-put-TextString att (FormatNum i))) (setq val (cdr (assoc tag globalData))) (if (and val (/= val "")) (vla-put-TextString att val)))) (setq count (1+ count))) (princ (strcat "\nLayout " layName " já existe."))) (setq i (1+ i))) (vla-Regen doc acActiveViewport) (alert (strcat "Sucesso!\nGerados " (itoa count) " layouts.\n\nUse 'Gerir Layouts > Ordenar Tabs' para reordenar.")) (princ))
(defun FindBlockInLayout (space blkName / foundObj) (setq foundObj nil) (vlax-for obj space (if (and (= (vla-get-ObjectName obj) "AcDbBlockReference") (or (= (strcase (vla-get-Name obj)) (strcase blkName)) (= (strcase (vla-get-EffectiveName obj)) (strcase blkName)))) (setq foundObj obj))) foundObj)
(defun FindDrawingOne (doc blkName / foundBlk val) (setq foundBlk nil) (vlax-for lay (vla-get-Layouts doc) (if (and (/= (vla-get-ModelType lay) :vlax-true) (null foundBlk)) (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (progn (setq val (GetAttValue blk "DES_NUM")) (if (or (= val "1") (= val "01")) (setq foundBlk blk))))))) foundBlk)
(defun InteractiveDataInheritance (refBlock blkName / atts attList i userSel idx chosenIdxs finalData tag currentVal newVal) (princ "\n\n=== DADOS DO DESENHO 01 ===") (setq atts (vlax-invoke refBlock 'GetAttributes)) (setq attList '()) (setq i 1) (foreach att atts (setq tag (strcase (vla-get-TagString att))) (setq val (vla-get-TextString att)) (if (not (wcmatch tag "DES_NUM,REV_*,DATA_*,DESC_*")) (progn (princ (strcat "\n " (itoa i) ". " tag ": " val)) (setq attList (cons (list i tag val) attList)) (setq i (1+ i))))) (setq attList (reverse attList)) (princ "\n-------------------------------------------") (princ "\nQuais valores copiar? (Separador: VÍRGULA)") (setq userSel (getstring T "\nDigite números (ex: 1,2) ou Enter para nenhum: ")) (setq chosenIdxs (StrSplit userSel ",")) (setq finalData '()) (princ "\n\n--- DEFINIR RESTANTES ---") (foreach item attList (setq idx (itoa (car item))) (setq tag (cadr item)) (setq currentVal (caddr item)) (if (member idx chosenIdxs) (progn (setq finalData (cons (cons tag currentVal) finalData)) (princ (strcat "\n" tag " -> Copiado."))) (progn (setq newVal (getstring T (strcat "\nValor para '" tag "' (Enter = Vazio): "))) (setq finalData (cons (cons tag newVal) finalData))))) (graphscr) finalData)
(defun GetLayoutsRaw (doc / lays listLays name) (setq lays (vla-get-Layouts doc)) (setq listLays '()) (vlax-for item lays (setq name (strcase (vla-get-Name item))) (if (and (/= (vla-get-ModelType item) :vlax-true) (/= name "TEMPLATE")) (setq listLays (cons item listLays)))) (vl-sort listLays '(lambda (a b) (< (vla-get-TabOrder a) (vla-get-TabOrder b)))))
;; Função auxiliar: retorna nome do DWG sem path nem extensão
(defun GetDWGName ( / rawName baseName) (setq rawName (getvar "DWGNAME")) (if (or (= rawName "") (= rawName nil) (wcmatch (strcase rawName) "DRAWING*.DWG")) "SEM_NOME" (vl-filename-base rawName)))
(defun Run_GenerateCSV ( / doc path dwgName defaultName csvFile fileDes layoutList dataList sortMode sortOrder valTipo valNum valTit maxRev revLetra revData revDesc valHandle duplicates continueExport userChoice dateErrors allDateErrors layName) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq path (getvar "DWGPREFIX")) (setq dwgName (GetDWGName)) (princ "\nA recolher dados (Ignorando TEMPLATE)... ") (setq dataList '()) (setq allDateErrors "") (setq layoutList (GetLayoutsRaw doc)) (foreach lay layoutList (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (progn (setq valTipo (CleanCSV (GetAttValue blk "TIPO"))) (setq valNum (CleanCSV (GetAttValue blk "DES_NUM"))) (setq valTit (CleanCSV (GetAttValue blk "TITULO"))) (setq maxRev (GetMaxRevision blk)) (setq revLetra (CleanCSV (car maxRev))) (setq revData (CleanCSV (cadr maxRev))) (setq revDesc (CleanCSV (caddr maxRev))) (setq valHandle (vla-get-Handle blk)) (setq layName (vla-get-Name lay)) (setq dateErrors (ValidateRevisionDates blk)) (if dateErrors (setq allDateErrors (strcat allDateErrors "Des " valNum " (" layName "): " dateErrors "\n"))) (setq dataList (cons (list dwgName valTipo valNum valTit revLetra revData revDesc valHandle layName) dataList)))))) (setq duplicates (FindDuplicateDES_NUM dataList)) (setq continueExport T) (if duplicates (progn (alert (strcat "AVISO: DES_NUM DUPLICADOS!\n\n" duplicates)) (initget "Sim Nao") (setq userChoice (getkword "\nContinuar exportação? [Sim/Nao] <Nao>: ")) (if (or (null userChoice) (= userChoice "Nao")) (setq continueExport nil)))) (if (and continueExport (/= allDateErrors "")) (progn (alert (strcat "AVISO: DATAS DE REVISÃO INCOERENTES!\n\n" allDateErrors)) (initget "Sim Nao") (setq userChoice (getkword "\nContinuar exportação? [Sim/Nao] <Sim>: ")) (if (= userChoice "Nao") (setq continueExport nil)))) (if continueExport (progn (setq defaultName (strcat path dwgName "_Lista.csv")) (setq csvFile (getfiled "Guardar Lista CSV" defaultName "csv" 1)) (if csvFile (progn (initget "1 2") (setq sortMode (getkword "\nOrdenar por? [1] Tipo / [2] Número <2>: ")) (if (not sortMode) (setq sortMode "2")) (cond ((= sortMode "1") (setq dataList (vl-sort dataList '(lambda (a b) (if (= (strcase (nth 1 a)) (strcase (nth 1 b))) (< (atoi (nth 2 a)) (atoi (nth 2 b))) (< (strcase (nth 1 a)) (strcase (nth 1 b)))))))) ((= sortMode "2") (setq dataList (vl-sort dataList '(lambda (a b) (< (atoi (nth 2 a)) (atoi (nth 2 b)))))))) (setq fileDes (open csvFile "w")) (if fileDes (progn (write-line "DWG_SOURCE;TIPO;NÚMERO DE DESENHO;TITULO;REVISAO;DATA;DESCRICAO;ID_CAD" fileDes) (foreach row dataList (write-line (strcat (nth 0 row) ";" (nth 1 row) ";" (nth 2 row) ";" (nth 3 row) ";" (nth 4 row) ";" (nth 5 row) ";" (nth 6 row) ";" (nth 7 row)) fileDes)) (close fileDes) (alert (strcat "Sucesso! Ficheiro criado:\n" csvFile))) (alert "Erro: Ficheiro aberto?"))) (princ "\nCancelado."))) (princ "\nExportação cancelada.")) (princ))
;; Função auxiliar: encontra DES_NUM duplicados e retorna string formatada
(defun FindDuplicateDES_NUM (dataList / numList duplicates item num layName seen result) (setq seen '() duplicates '()) (foreach item dataList (setq num (nth 2 item)) (setq layName (nth 8 item)) (if (assoc num seen) (setq duplicates (cons (strcat "DES_NUM " num " -> Layout: " layName) duplicates)) (setq seen (cons (cons num layName) seen)))) (if duplicates (progn (setq result "") (foreach dup (reverse duplicates) (setq result (strcat result dup "\n"))) result) nil))

;; ============================================================================
;; IMPORTAR CSV DE ALTERAÇÕES (por nome de Layout)
;; ============================================================================
;; Formato esperado: TAG DO LAYOUT;CLIENTE;OBRA;LOCALIZAÇÃO;ESPECIALIDADE;FASE;
;;                   DATA 1ª EMISSÃO;PROJETOU;NUMERO DE DESENHO;TIPO;ELEMENTO;TITULO;REVISÃO
(defun Run_ImportCSV_ByLayout ( / doc path csvFile fileDes line parts headers headerMap
                                  layoutName cliente obra localizacao especialidade fase
                                  data projetou desNum tipo elemento titulo revisao
                                  countUpdates countNotFound lay blk handle foundBlock)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq csvFile (getfiled "Selecione o CSV de Alterações" path "csv" 4))
  
  (if (and csvFile (findfile csvFile))
    (progn
      (setq fileDes (open csvFile "r"))
      (if fileDes
        (progn
          (princ "\nA processar CSV de alterações...")
          (setq countUpdates 0)
          (setq countNotFound 0)
          
          ;; Ler header e criar mapeamento de colunas
          (setq line (read-line fileDes))
          (setq headers (StrSplit line ";"))
          (setq headerMap (BuildHeaderMap headers))
          
          ;; Processar cada linha
          (while (setq line (read-line fileDes))
            (setq parts (StrSplit line ";"))
            
            ;; Obter valores pelo mapeamento de headers
            (setq layoutName (GetCSVValue parts headerMap "TAG DO LAYOUT"))
            (if (or (null layoutName) (= layoutName ""))
              (setq layoutName (GetCSVValue parts headerMap "LAYOUT_NAME"))
            )
            
            (if (and layoutName (/= layoutName ""))
              (progn
                ;; Obter restantes valores
                (setq cliente (GetCSVValue parts headerMap "CLIENTE"))
                (setq obra (GetCSVValue parts headerMap "OBRA"))
                (setq localizacao (GetCSVValue parts headerMap "LOCALIZAÇÃO"))
                (if (null localizacao) (setq localizacao (GetCSVValue parts headerMap "LOCALIZACAO")))
                (setq especialidade (GetCSVValue parts headerMap "ESPECIALIDADE"))
                (setq fase (GetCSVValue parts headerMap "FASE"))
                (setq data (GetCSVValue parts headerMap "DATA 1ª EMISSÃO"))
                (if (null data) (setq data (GetCSVValue parts headerMap "DATA")))
                (setq projetou (GetCSVValue parts headerMap "PROJETOU"))
                (setq desNum (GetCSVValue parts headerMap "NUMERO DE DESENHO"))
                (if (null desNum) (setq desNum (GetCSVValue parts headerMap "DES_NUM")))
                (setq tipo (GetCSVValue parts headerMap "TIPO"))
                (setq elemento (GetCSVValue parts headerMap "ELEMENTO"))
                (setq titulo (GetCSVValue parts headerMap "TITULO"))
                (setq revisao (GetCSVValue parts headerMap "REVISÃO"))
                (if (null revisao) (setq revisao (GetCSVValue parts headerMap "R")))
                
                ;; Procurar bloco pelo nome do layout
                (setq foundBlock nil)
                (setq handle nil)
                (vlax-for lay (vla-get-Layouts doc)
                  (if (and (not foundBlock)
                           (= (strcase (vla-get-Name lay)) (strcase layoutName)))
                    (vlax-for blk (vla-get-Block lay)
                      (if (and (not foundBlock) (IsTargetBlock blk))
                        (progn
                          (setq foundBlock blk)
                          (setq handle (vla-get-Handle blk))
                        )
                      )
                    )
                  )
                )
                
                ;; Atualizar bloco se encontrado
                (if (and foundBlock handle)
                  (progn
                    (if (and cliente (/= cliente "")) (UpdateSingleTag handle "CLIENTE" cliente))
                    (if (and obra (/= obra "")) (UpdateSingleTag handle "OBRA" obra))
                    (if (and localizacao (/= localizacao "")) (UpdateSingleTag handle "LOCALIZACAO" localizacao))
                    (if (and especialidade (/= especialidade "")) (UpdateSingleTag handle "ESPECIALIDADE" especialidade))
                    (if (and fase (/= fase "")) (UpdateSingleTag handle "FASE" fase))
                    (if (and data (/= data "")) (UpdateSingleTag handle "DATA" data))
                    (if (and projetou (/= projetou "")) (UpdateSingleTag handle "PROJETOU" projetou))
                    (if (and desNum (/= desNum "")) 
                      (progn
                        (UpdateSingleTag handle "DES_NUM" desNum)
                        (UpdateTabName handle nil)
                      )
                    )
                    (if (and tipo (/= tipo "")) (UpdateSingleTag handle "TIPO" tipo))
                    (if (and elemento (/= elemento "")) (UpdateSingleTag handle "ELEMENTO" elemento))
                    (if (and titulo (/= titulo "")) (UpdateSingleTag handle "TITULO" titulo))
                    ;; Nota: REVISÃO não é atualizada diretamente - usar Emitir Revisão
                    
                    (princ ".")
                    (setq countUpdates (1+ countUpdates))
                  )
                  (progn
                    (princ (strcat "\n  [!] Layout não encontrado: " layoutName))
                    (setq countNotFound (1+ countNotFound))
                  )
                )
              )
            )
          )
          
          (close fileDes)
          (vla-Regen doc acActiveViewport)
          
          (if (> countUpdates 0)
            (WriteLog (strcat "IMPORTAR CSV ALTERAÇÕES: " (itoa countUpdates) " desenhos atualizados"))
          )
          
          (alert (strcat "Importação concluída!\n\n"
                        "Desenhos atualizados: " (itoa countUpdates) "\n"
                        "Layouts não encontrados: " (itoa countNotFound)))
        )
        (alert "Erro ao abrir ficheiro.")
      )
    )
    (princ "\nCancelado.")
  )
  (princ)
)

;; Função auxiliar: construir mapa de headers (nome -> índice)
(defun BuildHeaderMap (headers / map idx header)
  (setq map '())
  (setq idx 0)
  (foreach header headers
    (setq map (cons (cons (strcase (vl-string-trim " " header)) idx) map))
    (setq idx (1+ idx))
  )
  map
)

;; Função auxiliar: obter valor do CSV pelo nome do header
(defun GetCSVValue (parts headerMap headerName / idx)
  (setq idx (cdr (assoc (strcase headerName) headerMap)))
  (if (and idx (< idx (length parts)))
    (vl-string-trim " " (nth idx parts))
    nil
  )
)

;; ============================================================================
;; Run_ImportFromDB - Importar CSV completo da DB (29 campos)
;; Formato: TAG DO LAYOUT;CLIENTE;OBRA;LOCALIZACAO;ESPECIALIDADE;FASE;DATA 1ª EMISSÃO;
;;          PROJETOU;NUMERO DE DESENHO;TIPO;ELEMENTO;TITULO;REVISÃO A;DATA REVISAO A;
;;          DESCRIÇÃO REVISÃO A;...B...C...D...E...;NOME DWG;ID_CAD
;; ============================================================================
(defun Run_ImportFromDB ( / doc path csvFile fileDes line parts headers headerMap
                           idCad cliente obra localizacao especialidade fase
                           data projetou desNum tipo elemento titulo
                           revA dataA descA revB dataB descB revC dataC descC
                           revD dataD descD revE dataE descE
                           countUpdates countNotFound ename obj handle foundBlock)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq csvFile (getfiled "Selecione o CSV exportado da DB" path "csv" 4))
  
  (if (and csvFile (findfile csvFile))
    (progn
      (setq fileDes (open csvFile "r"))
      (if fileDes
        (progn
          (princ "\nA processar CSV da DB...")
          (setq countUpdates 0)
          (setq countNotFound 0)
          
          ;; Ler header e criar mapeamento de colunas
          (setq line (read-line fileDes))
          (setq headers (StrSplit line ";"))
          (setq headerMap (BuildHeaderMap headers))
          
          ;; Processar cada linha
          (while (setq line (read-line fileDes))
            (setq parts (StrSplit line ";"))
            
            ;; Obter ID_CAD (handle) - campo obrigatório
            (setq idCad (GetCSVValue parts headerMap "ID_CAD"))
            
            (if (and idCad (/= idCad ""))
              (progn
                ;; Verificar se o bloco existe pelo handle
                (setq foundBlock nil)
                (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list idCad))))
                  (progn
                    (setq ename (handent idCad))
                    (if ename
                      (progn
                        (setq obj (vlax-ename->vla-object ename))
                        (if (IsTargetBlock obj)
                          (setq foundBlock T)
                        )
                      )
                    )
                  )
                )
                
                (if foundBlock
                  (progn
                    ;; Obter todos os valores do CSV
                    (setq cliente (GetCSVValue parts headerMap "CLIENTE"))
                    (setq obra (GetCSVValue parts headerMap "OBRA"))
                    (setq localizacao (GetCSVValue parts headerMap "LOCALIZACAO"))
                    (if (null localizacao) (setq localizacao (GetCSVValue parts headerMap "LOCALIZAÇÃO")))
                    (setq especialidade (GetCSVValue parts headerMap "ESPECIALIDADE"))
                    (setq fase (GetCSVValue parts headerMap "FASE"))
                    (setq data (GetCSVValue parts headerMap "DATA 1ª EMISSÃO"))
                    (if (null data) (setq data (GetCSVValue parts headerMap "DATA 1ª EMISSAO")))
                    (setq projetou (GetCSVValue parts headerMap "PROJETOU"))
                    (setq desNum (GetCSVValue parts headerMap "NUMERO DE DESENHO"))
                    (if (null desNum) (setq desNum (GetCSVValue parts headerMap "DES_NUM")))
                    (setq tipo (GetCSVValue parts headerMap "TIPO"))
                    (setq elemento (GetCSVValue parts headerMap "ELEMENTO"))
                    (setq titulo (GetCSVValue parts headerMap "TITULO"))
                    
                    ;; Revisões A-E
                    (setq revA (GetCSVValue parts headerMap "REVISÃO A"))
                    (if (null revA) (setq revA (GetCSVValue parts headerMap "REVISAO A")))
                    (setq dataA (GetCSVValue parts headerMap "DATA REVISAO A"))
                    (setq descA (GetCSVValue parts headerMap "DESCRIÇÃO REVISÃO A"))
                    (if (null descA) (setq descA (GetCSVValue parts headerMap "DESCRICAO REVISAO A")))
                    
                    (setq revB (GetCSVValue parts headerMap "REVISÃO B"))
                    (if (null revB) (setq revB (GetCSVValue parts headerMap "REVISAO B")))
                    (setq dataB (GetCSVValue parts headerMap "DATA REVISAO B"))
                    (setq descB (GetCSVValue parts headerMap "DESCRIÇÃO REVISÃO B"))
                    (if (null descB) (setq descB (GetCSVValue parts headerMap "DESCRICAO REVISAO B")))
                    
                    (setq revC (GetCSVValue parts headerMap "REVISÃO C"))
                    (if (null revC) (setq revC (GetCSVValue parts headerMap "REVISAO C")))
                    (setq dataC (GetCSVValue parts headerMap "DATA REVISAO C"))
                    (setq descC (GetCSVValue parts headerMap "DESCRIÇÃO REVISÃO C"))
                    (if (null descC) (setq descC (GetCSVValue parts headerMap "DESCRICAO REVISAO C")))
                    
                    (setq revD (GetCSVValue parts headerMap "REVISÃO D"))
                    (if (null revD) (setq revD (GetCSVValue parts headerMap "REVISAO D")))
                    (setq dataD (GetCSVValue parts headerMap "DATA REVISAO D"))
                    (setq descD (GetCSVValue parts headerMap "DESCRIÇÃO REVISÃO D"))
                    (if (null descD) (setq descD (GetCSVValue parts headerMap "DESCRICAO REVISAO D")))
                    
                    (setq revE (GetCSVValue parts headerMap "REVISÃO E"))
                    (if (null revE) (setq revE (GetCSVValue parts headerMap "REVISAO E")))
                    (setq dataE (GetCSVValue parts headerMap "DATA REVISAO E"))
                    (setq descE (GetCSVValue parts headerMap "DESCRIÇÃO REVISÃO E"))
                    (if (null descE) (setq descE (GetCSVValue parts headerMap "DESCRICAO REVISAO E")))
                    
                    ;; Atualizar todos os atributos
                    (if (and cliente (/= cliente "")) (UpdateSingleTag idCad "CLIENTE" cliente))
                    (if (and obra (/= obra "")) (UpdateSingleTag idCad "OBRA" obra))
                    (if (and localizacao (/= localizacao "")) (UpdateSingleTag idCad "LOCALIZACAO" localizacao))
                    (if (and especialidade (/= especialidade "")) (UpdateSingleTag idCad "ESPECIALIDADE" especialidade))
                    (if (and fase (/= fase "")) (UpdateSingleTag idCad "FASE" fase))
                    (if (and data (/= data "")) (UpdateSingleTag idCad "DATA" data))
                    (if (and projetou (/= projetou "")) (UpdateSingleTag idCad "PROJETOU" projetou))
                    (if (and tipo (/= tipo "")) (UpdateSingleTag idCad "TIPO" tipo))
                    (if (and elemento (/= elemento "")) (UpdateSingleTag idCad "ELEMENTO" elemento))
                    (if (and titulo (/= titulo "")) (UpdateSingleTag idCad "TITULO" titulo))
                    (if (and desNum (/= desNum "")) 
                      (progn
                        (UpdateSingleTag idCad "DES_NUM" desNum)
                        ;; Forçar refresh do bloco após mudar DES_NUM
                        (vl-catch-all-apply 'vla-Update (list obj))
                      )
                    )
                    
                    ;; Atualizar revisões A-E
                    (if (and revA (/= revA "") (/= revA "-"))
                      (progn
                        (UpdateSingleTag idCad "REV_A" revA)
                        (if dataA (UpdateSingleTag idCad "DATA_A" dataA))
                        (if descA (UpdateSingleTag idCad "DESC_A" descA))
                      )
                    )
                    (if (and revB (/= revB "") (/= revB "-"))
                      (progn
                        (UpdateSingleTag idCad "REV_B" revB)
                        (if dataB (UpdateSingleTag idCad "DATA_B" dataB))
                        (if descB (UpdateSingleTag idCad "DESC_B" descB))
                      )
                    )
                    (if (and revC (/= revC "") (/= revC "-"))
                      (progn
                        (UpdateSingleTag idCad "REV_C" revC)
                        (if dataC (UpdateSingleTag idCad "DATA_C" dataC))
                        (if descC (UpdateSingleTag idCad "DESC_C" descC))
                      )
                    )
                    (if (and revD (/= revD "") (/= revD "-"))
                      (progn
                        (UpdateSingleTag idCad "REV_D" revD)
                        (if dataD (UpdateSingleTag idCad "DATA_D" dataD))
                        (if descD (UpdateSingleTag idCad "DESC_D" descD))
                      )
                    )
                    (if (and revE (/= revE "") (/= revE "-"))
                      (progn
                        (UpdateSingleTag idCad "REV_E" revE)
                        (if dataE (UpdateSingleTag idCad "DATA_E" dataE))
                        (if descE (UpdateSingleTag idCad "DESC_E" descE))
                      )
                    )
                    
                    ;; Atualizar R (revisão atual) e ELEMENTO_TITULO
                    (vl-catch-all-apply 'UpdateAttributeR (list idCad))
                    (vl-catch-all-apply 'UpdateElementoTitulo (list idCad))
                    
                    ;; Atualizar nome da TAB (formato fixo V41.0)
                    (vl-catch-all-apply 'UpdateTabName (list idCad nil))
                    
                    (princ ".")
                    (setq countUpdates (1+ countUpdates))
                  )
                  (progn
                    (princ (strcat "\n  [!] ID_CAD não encontrado: " idCad))
                    (setq countNotFound (1+ countNotFound))
                  )
                )
              )
            )
          )
          
          (close fileDes)
          
          ;; Regen com error handling
          (vl-catch-all-apply 'vla-Regen (list doc acActiveViewport))
          
          (if (> countUpdates 0)
            (WriteLog (strcat "IMPORTAR DB: " (itoa countUpdates) " desenhos atualizados (todos os campos)"))
          )
          
          ;; Mensagem de conclusão
          (alert (strcat "Importação da DB concluída!\n\n"
                        "Desenhos atualizados: " (itoa countUpdates) "\n"
                        "ID_CAD não encontrados: " (itoa countNotFound) "\n\n"
                        "Todos os campos atualizados:\n"
                        "- Dados gerais (Cliente, Obra, etc.)\n"
                        "- DES_NUM, TIPO, ELEMENTO, TITULO\n"
                        "- Revisões A a E\n"
                        "- Nomes das TABs"))
        )
        (alert "Erro ao abrir ficheiro.")
      )
    )
    (princ "\nCancelado.")
  )
  (princ)
)

;; Run_ImportCSV - Importar CSV com formato: DWG_SOURCE;TIPO;DES_NUM;ELEMENTO;TITULO;REV;DATA;DESC;ID_CAD
(defun Run_ImportCSV ( / doc path defaultName csvFile fileDes line parts valDwgSource valTipo valNum valElemento valTit valRev valData valDesc valHandle countUpdates) 
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) 
  (setq path (getvar "DWGPREFIX")) 
  (setq csvFile (getfiled "Selecione o ficheiro CSV" path "csv" 4)) 
  (if (and csvFile (findfile csvFile)) 
    (progn 
      (setq fileDes (open csvFile "r")) 
      (if fileDes 
        (progn 
          (princ "\nA processar CSV... ") 
          (setq countUpdates 0) 
          (read-line fileDes) ;; Skip header
          (while (setq line (read-line fileDes)) 
            (setq parts (StrSplit line ";")) 
            ;; Formato: DWG_SOURCE;TIPO;DES_NUM;ELEMENTO;TITULO;REV;DATA;DESC;ID_CAD (9 colunas)
            (if (>= (length parts) 9) 
              (progn 
                (setq valDwgSource (nth 0 parts)) 
                (setq valTipo (nth 1 parts)) 
                (setq valNum (nth 2 parts)) 
                (setq valElemento (nth 3 parts))
                (setq valTit (nth 4 parts)) 
                (setq valRev (nth 5 parts)) 
                (setq valData (nth 6 parts)) 
                (setq valDesc (nth 7 parts)) 
                (setq valHandle (nth 8 parts)) 
                (if (and valHandle (/= valHandle "")) 
                  (if (UpdateBlockByHandleAndData valHandle valTipo valNum valElemento valTit valRev valData valDesc) 
                    (setq countUpdates (1+ countUpdates))
                  )
                )
              )
            )
          ) 
          (close fileDes) 
          (vla-Regen doc acActiveViewport) 
          (if (> countUpdates 0) 
            (WriteLog (strcat "IMPORTAR CSV: " (itoa countUpdates) " desenhos atualizados"))
          ) 
          (alert (strcat "Concluído!\n" (itoa countUpdates) " desenhos atualizados."))
        ) 
        (alert "Erro ao abrir ficheiro.")
      )
    ) 
    (princ "\nCancelado.")
  ) 
  (princ)
)
(defun CleanCSV (str) (if (= str nil) (setq str "")) (setq str (vl-string-translate ";" "," str)) (vl-string-trim " \"" str))
(defun StrSplit (str del / pos len lst) (setq len (strlen del)) (while (setq pos (vl-string-search del str)) (setq lst (cons (vl-string-trim " " (substr str 1 pos)) lst) str (substr str (+ 1 pos len)))) (reverse (cons (vl-string-trim " " str) lst)))
(defun UpdateBlockByHandleAndData (handle tipo num elemento tit rev dataStr descStr / ename obj atts revTag dataTag descTag success) 
  (setq success nil) 
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle)))) 
    (setq ename (handent handle))
  ) 
  (if (and ename (setq obj (vlax-ename->vla-object ename))) 
    (if (IsTargetBlock obj) 
      (progn 
        (UpdateSingleTag handle "TIPO" tipo) 
        (UpdateSingleTag handle "DES_NUM" num)
        (UpdateTabName handle) ;; Auto-atualizar tab quando DES_NUM muda
        (UpdateSingleTag handle "ELEMENTO" elemento) ;; UpdateSingleTag chama UpdateElementoTitulo
        (UpdateSingleTag handle "TITULO" tit) ;; UpdateSingleTag chama UpdateElementoTitulo
        (if (and rev (/= rev "") (/= rev "-")) 
          (progn 
            (setq revTag (strcat "REV_" rev)) 
            (setq dataTag (strcat "DATA_" rev)) 
            (setq descTag (strcat "DESC_" rev)) 
            (UpdateSingleTag handle revTag rev) 
            (UpdateSingleTag handle dataTag dataStr) 
            (UpdateSingleTag handle descTag descStr) 
            (UpdateAttributeR handle) ;; UpdateAttributeR já chama UpdateTabName
          )
        ) 
        (princ ".") 
        (setq success T)
      )
    )
  ) 
  success
)
(defun GetMaxRevision (blk / checkRev finalRev finalDate finalDesc) (setq finalRev "-" finalDate "-" finalDesc "-") (foreach letra '("E" "D" "C" "B" "A") (if (= finalRev "-") (progn (setq checkRev (GetAttValue blk (strcat "REV_" letra))) (if (and (/= checkRev "") (/= checkRev " ")) (progn (setq finalRev checkRev) (setq finalDate (GetAttValue blk (strcat "DATA_" letra))) (setq finalDesc (GetAttValue blk (strcat "DESC_" letra)))))))) (list finalRev finalDate finalDesc))
(defun GetGlobalDefinitions (blkName / doc blocks blkDef atts tag val dataList) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq blocks (vla-get-Blocks doc)) (setq dataList '()) (if (not (vl-catch-all-error-p (setq blkDef (vla-Item blocks blkName)))) (vlax-for obj blkDef (if (and (= (vla-get-ObjectName obj) "AcDbAttributeDefinition") (not (wcmatch (strcase (vla-get-TagString obj)) "DES_NUM,REV_*,DATA_*,DESC_*"))) (progn (setq tag (vla-get-TagString obj)) (setq val (getstring T (strcat "\nValor para '" tag "': "))) (if (/= val "") (setq dataList (cons (cons (strcase tag) val) dataList))))))) dataList)
(defun catch-apply (func params / result) (if (vl-catch-all-error-p (setq result (vl-catch-all-apply func params))) nil result))
(defun ProcessManualReview ( / loop drawList i item userIdx selectedHandle field revLet revData revDesc dateWarning desNum doc)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq drawList (GetDrawingList))
  (if (null drawList)
    (progn
      (alert "Nenhum desenho encontrado com bloco LEGENDA_JSJ_V1.")
      (princ "\nNenhum desenho encontrado.")
    )
    (progn
      (setq loop T)
      (while loop
        (setq drawList (GetDrawingList))
        (princ "\n\n=== LISTA DE DESENHOS (ORDENADA) ===\n")
        (setq i 0)
        (foreach item drawList
          (princ (strcat "\n " (itoa (1+ i)) ". [Des: " (cadr item) "] (" (nth 3 item) ") - Tab: " (caddr item)))
          (setq i (1+ i))
        )
        (setq userIdx (getint (strcat "\nEscolha o numero (1-" (itoa i) ") ou 0 para sair: ")))
        (cond
          ((or (null userIdx) (= userIdx 0))
            (setq loop nil)
          )
          ((and (> userIdx 0) (<= userIdx i))
            (setq selectedHandle (car (nth (1- userIdx) drawList)))
            (setq desNum (cadr (nth (1- userIdx) drawList)))
            (initget "1 2 3")
            (setq field (getkword "\nAtualizar? [1] Tipo / [2] Elemento / [3] Titulo: "))
            (cond
              ((= field "1")
                (UpdateSingleTag selectedHandle "TIPO" (getstring T "\nNovo TIPO: "))
                (vla-Regen doc acActiveViewport)
                (WriteLog (strcat "MODIFICAR: Des " desNum " - TIPO alterado"))
              )
              ((= field "2")
                (UpdateSingleTag selectedHandle "ELEMENTO" (getstring T "\nNovo ELEMENTO: "))
                (vla-Regen doc acActiveViewport)
                (WriteLog (strcat "MODIFICAR: Des " desNum " - ELEMENTO alterado"))
              )
              ((= field "3")
                (UpdateSingleTag selectedHandle "TITULO" (getstring T "\nNovo TITULO: "))
                (vla-Regen doc acActiveViewport)
                (WriteLog (strcat "MODIFICAR: Des " desNum " - TITULO alterado"))
              )
            )
            (initget "Sim Nao")
            (if (/= (getkword "\nModificar outro desenho? [Sim/Nao] <Nao>: ") "Sim")
              (setq loop nil)
            )
          )
          (T (princ "\nNumero invalido.")))
        )
      )
    )
  )
  (graphscr)
  (princ)
)
(defun AutoNumberByType ( / doc dataList blk typeVal handleVal tabOrd sortedList curType count i) 
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) 
  (setq dataList '()) 
  (princ "\n\nA analisar...") 
  (vlax-for lay (vla-get-Layouts doc) 
    (if (/= (vla-get-ModelType lay) :vlax-true) 
      (vlax-for blk (vla-get-Block lay) 
        (if (IsTargetBlock blk) 
          (progn 
            (setq typeVal (GetAttValue blk "TIPO")) 
            (if (= typeVal "") (setq typeVal "INDEFINIDO")) 
            (setq handleVal (vla-get-Handle blk)) 
            (setq tabOrd (vla-get-TabOrder lay)) 
            (setq dataList (cons (list typeVal tabOrd handleVal) dataList))
          )
        )
      )
    )
  ) 
  (setq sortedList (vl-sort dataList '(lambda (a b) 
    (if (= (strcase (car a)) (strcase (car b))) 
      (< (cadr a) (cadr b)) 
      (< (strcase (car a)) (strcase (car b)))
    )
  ))) 
  (setq curType "" count 0 i 0) 
  (foreach item sortedList 
    (if (/= (strcase (car item)) curType) 
      (progn 
        (setq curType (strcase (car item))) 
        (setq count 1)
      ) 
      (setq count (1+ count))
    ) 
    (UpdateSingleTag (caddr item) "DES_NUM" (FormatNum count))
    (UpdateTabName (caddr item)) ;; Auto-atualizar tab quando DES_NUM muda
    (setq i (1+ i))
  ) 
  (vla-Regen doc acActiveViewport) 
  (alert (strcat "Concluído: " (itoa i)))
)
(defun AutoNumberSequential ( / doc sortedLayouts count i) 
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) 
  (initget "Sim Nao") 
  (if (= (getkword "\nNumerar sequencialmente? [Sim/Nao] <Nao>: ") "Sim") 
    (progn 
      (setq sortedLayouts (GetLayoutsRaw doc)) 
      (setq sortedLayouts (vl-sort sortedLayouts '(lambda (a b) (< (vla-get-TabOrder a) (vla-get-TabOrder b))))) 
      (setq count 1 i 0) 
      (foreach lay sortedLayouts 
        (vlax-for blk (vla-get-Block lay) 
          (if (IsTargetBlock blk) 
            (progn 
              (UpdateSingleTag (vla-get-Handle blk) "DES_NUM" (FormatNum count))
              (UpdateTabName (vla-get-Handle blk)) ;; Auto-atualizar tab quando DES_NUM muda
              (setq count (1+ count)) 
              (setq i (1+ i))
            )
          )
        )
      ) 
      (vla-Regen doc acActiveViewport) 
      (alert (strcat "Concluído: " (itoa i)))
    )
  )
)
(defun ReleaseObject (obj) (if (and obj (not (vlax-object-released-p obj))) (vlax-release-object obj)))
;; NOTA: IsTargetBlock, GetAttValue, UpdateSingleTag, UpdateBlockByHandle estão definidos no início do ficheiro
;; ApplyGlobalValue - Aplica valor a tag específico em todos os blocos
;; Quando ELEMENTO é alterado, recalcula ELEMENTO_TITULO (TITULO é único por desenho)
(defun ApplyGlobalValue (targetTag targetVal / doc blkHandle) 
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) 
  (vlax-for lay (vla-get-Layouts doc) 
    (if (/= (vla-get-ModelType lay) :vlax-true) 
      (vlax-for blk (vla-get-Block lay) 
        (if (IsTargetBlock blk) 
          (progn
            (foreach att (vlax-invoke blk 'GetAttributes) 
              (if (= (strcase (vla-get-TagString att)) targetTag) 
                (vla-put-TextString att targetVal)
              )
            )
            ;; Se ELEMENTO foi alterado, recalcular ELEMENTO_TITULO
            ;; Passa o novo valor para evitar ler valor desatualizado
            (if (= targetTag "ELEMENTO")
              (progn
                (setq blkHandle (vla-get-Handle blk))
                (UpdateElementoTitulo blkHandle "ELEMENTO" targetVal)
              )
            )
          )
        )
      )
    )
  ) 
  (vla-Regen doc acActiveViewport)
)

;; ============================================================================
;; MENSAGEM DE CARREGAMENTO
;; ============================================================================
(princ "\n========================================")
(princ "\n GESTAO DESENHOS JSJ V41.0")
(princ "\n========================================")
(princ "\n Comandos disponiveis:")
(princ "\n   GESTAODESENHOSJSJ - Menu principal")
(princ "\n   JSJDIAG - Diagnostico de atributos")
(princ "\n========================================")
(princ "\n Formato Tab: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO-R")
(princ "\n========================================")
(princ)
