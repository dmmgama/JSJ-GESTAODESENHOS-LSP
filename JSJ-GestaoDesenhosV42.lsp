;; ============================================================================
;; GESTAO DESENHOS JSJ V42.0
;; ============================================================================
;; V42: Template incluído em Dados Projeto; Export/Import Dados Gerais
;; Bloco alvo: LEGENDA_JSJ_V1
;; 
;; ATRIBUTOS SUPORTADOS:
;;   Projeto: PROJ_NUM, PROJ_NOME, CLIENTE, OBRA, LOCALIZACAO, ESPECIALIDADE, PROJETOU
;;   Fase: FASE, FASE_PFIX
;;   Emissão: EMISSAO, DATA
;;   Desenho: PFIX, DES_NUM, TIPO, ELEMENTO, TITULO, ELEMENTO_TITULO (calculado)
;;   Revisões: R, REV_A-E, DATA_A-E, DESC_A-E
;;
;; FORMATO TAB FIXO: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO-R
;; Exemplo: 669-EST-DIM-001-E00-A
;; ============================================================================

(vl-load-com)

;; ============================================================================
;; VARIÁVEIS GLOBAIS
;; ============================================================================
(setq *JSJ_USER* nil)

;; ============================================================================
;; SECÇÃO 1: FUNÇÕES CORE (Baixo Nível)
;; ============================================================================

;; Verifica se bloco é LEGENDA_JSJ_V1
(defun IsTargetBlock (blk)
  (and (= (vla-get-ObjectName blk) "AcDbBlockReference")
       (= (strcase (vla-get-EffectiveName blk)) "LEGENDA_JSJ_V1"))
)

;; Obtém valor de atributo por tag
(defun GetAttValue (blk tag / atts val)
  (setq atts (vlax-invoke blk 'GetAttributes) val "")
  (foreach att atts
    (if (= (strcase (vla-get-TagString att)) (strcase tag))
      (setq val (vla-get-TextString att))))
  val
)

;; Obtém valor de atributo por handle
(defun GetAttValueByHandle (handle tag / ename obj)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (GetAttValue obj tag)
    ""
  )
)

;; Atualiza um atributo específico
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
      (if (= (strcase tag) "ELEMENTO")
        (UpdateElementoTitulo handle "ELEMENTO" val))
      (if (= (strcase tag) "TITULO")
        (UpdateElementoTitulo handle "TITULO" val))
    )
  )
)

;; Atualiza ELEMENTO_TITULO (campo calculado)
(defun UpdateElementoTitulo (handle changedTag newValue / ename obj elemento titulo resultado)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (progn
      (cond
        ((= changedTag "ELEMENTO")
          (setq elemento (if newValue (vl-string-trim " " newValue) ""))
          (setq titulo (vl-string-trim " " (GetAttValue obj "TITULO"))))
        ((= changedTag "TITULO")
          (setq elemento (vl-string-trim " " (GetAttValue obj "ELEMENTO")))
          (setq titulo (if newValue (vl-string-trim " " newValue) "")))
        (T
          (setq elemento (vl-string-trim " " (GetAttValue obj "ELEMENTO")))
          (setq titulo (vl-string-trim " " (GetAttValue obj "TITULO")))))
      
      (cond
        ((and (= elemento "") (= titulo "")) (setq resultado ""))
        ((= elemento "") (setq resultado titulo))
        ((= titulo "") (setq resultado elemento))
        (T (setq resultado (strcat elemento " - " titulo))))
      
      (foreach att (vlax-invoke obj 'GetAttributes)
        (if (= (strcase (vla-get-TagString att)) "ELEMENTO_TITULO")
          (vla-put-TextString att resultado)))
      (vla-Update obj)
    )
  )
)

;; ============================================================================
;; SECÇÃO 2: FUNÇÕES UTILITÁRIAS
;; ============================================================================

;; Formata número para 3 dígitos (ex: 1 -> "001", 10 -> "010", 100 -> "100")
(defun FormatNum (n)
  (cond
    ((< n 10) (strcat "00" (itoa n)))
    ((< n 100) (strcat "0" (itoa n)))
    (T (itoa n)))
)

(defun StrSplit (str del / pos len lst)
  (setq len (strlen del))
  (while (setq pos (vl-string-search del str))
    (setq lst (cons (vl-string-trim " " (substr str 1 pos)) lst)
          str (substr str (+ 1 pos len))))
  (reverse (cons (vl-string-trim " " str) lst))
)

(defun CleanCSV (str)
  (if (= str nil) (setq str ""))
  (setq str (vl-string-translate ";" "," str))
  (vl-string-trim " \"" str)
)

;; Parse CSV line by separator (returns list of fields)
(defun ParseCSVLine (line sep / result pos)
  (setq result '())
  (while (setq pos (vl-string-search sep line))
    (setq result (cons (substr line 1 pos) result))
    (setq line (substr line (+ pos 2))))
  (setq result (cons line result))
  (reverse result)
)

(defun GetDWGName ( / rawName)
  (setq rawName (getvar "DWGNAME"))
  (if (or (= rawName "") (= rawName nil) (wcmatch (strcase rawName) "DRAWING*.DWG"))
    "SEM_NOME"
    (vl-filename-base rawName))
)

(defun GetTodayDate ()
  (menucmd "M=$(edtime,$(getvar,date),DD-MO-YYYY)")
)

(defun catch-apply (func params / result)
  (if (vl-catch-all-error-p (setq result (vl-catch-all-apply func params))) nil result)
)

;; Comparação inteligente número/texto
(defun IsNumberInList (valStr listStr / n1 n2 found item)
  (setq found nil n1 (atoi valStr))
  (foreach item listStr
    (setq n2 (atoi item))
    (if (or (= n1 n2) (= (strcase valStr) (strcase item)))
      (setq found T)))
  found
)

;; ============================================================================
;; SECÇÃO 3: FUNÇÕES DE DADOS
;; ============================================================================

;; Lista de desenhos ordenada por DES_NUM
(defun GetDrawingList ( / doc listOut desNum tipo name)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) listOut '())
  (vlax-for lay (vla-get-Layouts doc)
    (setq name (strcase (vla-get-Name lay)))
    (if (and (/= (vla-get-ModelType lay) :vlax-true) (/= name "TEMPLATE"))
      (vlax-for blk (vla-get-Block lay)
        (if (IsTargetBlock blk)
          (progn
            (setq desNum (GetAttValue blk "DES_NUM"))
            (setq tipo (GetAttValue blk "TIPO"))
            (if (= desNum "") (setq desNum "0"))
            (if (= tipo "") (setq tipo "ND"))
            (setq listOut (cons (list (vla-get-Handle blk) desNum (vla-get-Name lay) tipo) listOut)))))))
  (vl-sort listOut '(lambda (a b) (< (atoi (cadr a)) (atoi (cadr b)))))
)

;; Lista de layouts ordenada por TabOrder
(defun GetLayoutsRaw (doc / lays listLays name)
  (setq lays (vla-get-Layouts doc) listLays '())
  (vlax-for item lays
    (setq name (strcase (vla-get-Name item)))
    (if (and (/= (vla-get-ModelType item) :vlax-true) (/= name "TEMPLATE"))
      (setq listLays (cons item listLays))))
  (vl-sort listLays '(lambda (a b) (< (vla-get-TabOrder a) (vla-get-TabOrder b))))
)

;; Dados do bloco num layout
(defun GetBlockDataInLayout (blkDef blkName / valTipo valNum)
  (setq valTipo "" valNum "0")
  (vlax-for obj blkDef
    (if (and (= (vla-get-ObjectName obj) "AcDbBlockReference")
             (or (= (strcase (vla-get-Name obj)) (strcase blkName))
                 (= (strcase (vla-get-EffectiveName obj)) (strcase blkName))))
      (progn
        (setq valTipo (GetAttValue obj "TIPO"))
        (setq valNum (GetAttValue obj "DES_NUM")))))
  (list valTipo valNum)
)

;; Converte seleção "1,3,5" ou "2-5" em lista
(defun ParseSelectionToList (drawList selStr / result parts item startNum endNum i num)
  (setq result '() parts (StrSplit selStr ","))
  (foreach part parts
    (setq part (vl-string-trim " " part))
    (if (vl-string-search "-" part)
      (progn
        (setq startNum (atoi (car (StrSplit part "-"))))
        (setq endNum (atoi (cadr (StrSplit part "-"))))
        (setq i startNum)
        (while (<= i endNum)
          (if (and (> i 0) (<= i (length drawList)))
            (progn
              (setq item (nth (1- i) drawList))
              (if (not (member item result))
                (setq result (cons item result)))))
          (setq i (1+ i))))
      (progn
        (setq num (atoi part))
        (if (and (> num 0) (<= num (length drawList)))
          (progn
            (setq item (nth (1- num) drawList))
            (if (not (member item result))
              (setq result (cons item result))))))))
  (reverse result)
)

;; ============================================================================
;; SECÇÃO 4: SISTEMA DE LOGGING
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
      (close logFile)))
)

(defun SetCurrentUser ( / newUser)
  (setq newUser (getstring T (strcat "\nUtilizador atual: " (if *JSJ_USER* *JSJ_USER* "<vazio>") "\nNovo utilizador: ")))
  (if (and newUser (/= newUser ""))
    (progn
      (setq *JSJ_USER* newUser)
      (WriteLog (strcat "UTILIZADOR: Sessão iniciada por " newUser))
      (princ (strcat "\nUtilizador definido: " newUser)))
    (princ "\nUtilizador não alterado."))
)

;; ============================================================================
;; SECÇÃO 5: FORMATO TAB FIXO
;; ============================================================================
;; Formato: PROJ_NUM-EST-PFIX DES_NUM-EMISSAO-FASE_PFIX-R
;; Exemplo: 669-EST-DIM 003-E01-PB-C
;; Regras: PFIX separado do DES_NUM por espaço. FASE_PFIX antes do R.

(defun BuildTabName (blk / projNum pfix desNum emissao fasePfix revR result)
  (setq projNum (GetAttValue blk "PROJ_NUM"))
  (setq pfix (GetAttValue blk "PFIX"))
  (setq desNum (GetAttValue blk "DES_NUM"))
  (setq emissao (GetAttValue blk "EMISSAO"))
  (setq fasePfix (GetAttValue blk "FASE_PFIX"))
  (setq revR (GetAttValue blk "R"))
  
  ;; Base: PROJ_NUM-EST
  (setq result (strcat projNum "-EST"))
  
  ;; Adicionar PFIX DES_NUM (PFIX separado do DES_NUM por espaço)
  (if (and pfix (/= pfix "") (/= pfix " "))
    (setq result (strcat result "-" pfix " " desNum))
    ;; Se não há PFIX, só adiciona DES_NUM
    (if (and desNum (/= desNum ""))
      (setq result (strcat result "-" desNum))))
  
  ;; Adicionar EMISSAO se existir
  (if (and emissao (/= emissao "") (/= emissao " "))
    (setq result (strcat result "-" emissao)))
  
  ;; Adicionar FASE_PFIX se existir (antes do R)
  (if (and fasePfix (/= fasePfix "") (/= fasePfix " "))
    (setq result (strcat result "-" fasePfix)))
  
  ;; Adicionar R se existir
  (if (and revR (/= revR "") (/= revR " ") (/= revR "-"))
    (setq result (strcat result "-" revR)))
  
  result
)

;; Atualiza nome do tab de um layout específico
(defun UpdateTabName (handle / doc lay blk foundLay newTabName ename obj)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if ename (setq obj (vlax-ename->vla-object ename)))
  
  (if (and obj (IsTargetBlock obj))
    (progn
      (vla-Update obj)
      (setq foundLay nil)
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (not foundLay)
                 (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (and (not foundLay) (= (vla-get-Handle blk) handle))
              (setq foundLay lay)))))
      (if foundLay
        (progn
          (setq newTabName (BuildTabName obj))
          (if (and newTabName (/= newTabName ""))
            (vl-catch-all-apply 'vla-put-Name (list foundLay newTabName)))))))
)

;; Atualiza todos os nomes de tabs
(defun AtualizarNomesLayouts ( / doc count newTabName)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq count 0)
  (princ "\n\n=== ATUALIZAR NOMES DOS LAYOUTS ===")
  (princ "\nFormato: PROJ_NUM-EST-PFIX-DES_NUM-EMISSAO-R")
  
  (initget "Sim Nao")
  (if (= (getkword "\n\nAtualizar todos os tabs? [Sim/Nao] <Nao>: ") "Sim")
    (progn
      (princ "\nA processar...")
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (setq newTabName (BuildTabName blk))
                (if (and newTabName (/= newTabName ""))
                  (if (not (vl-catch-all-error-p
                             (vl-catch-all-apply 'vla-put-Name (list lay newTabName))))
                    (progn
                      (setq count (1+ count))
                      (princ (strcat "\n  " (vla-get-Name lay) " -> " newTabName))))))))))
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat "TABS: Atualizados " (itoa count) " layouts"))
      (alert (strcat "Concluído!\n\n" (itoa count) " tabs atualizados.")))
    (princ "\nCancelado."))
  (princ)
)

;; ============================================================================
;; SECÇÃO 6: REVISÕES
;; ============================================================================

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

(defun GetMaxRevisionLetter (blk / checkRev foundLetter)
  (setq foundLetter nil)
  (foreach letra '("E" "D" "C" "B" "A")
    (if (null foundLetter)
      (progn
        (setq checkRev (GetAttValue blk (strcat "REV_" letra)))
        (if (and checkRev (/= checkRev "") (/= checkRev " "))
          (setq foundLetter letra)))))
  foundLetter
)

(defun GetMaxRevisionLetterByHandle (handle / ename obj)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (GetMaxRevisionLetter obj)
    nil)
)

(defun GetNextRevisionLetter (currentLetter)
  (cond
    ((null currentLetter) "A")
    ((= currentLetter "") "A")
    ((= currentLetter "A") "B")
    ((= currentLetter "B") "C")
    ((= currentLetter "C") "D")
    ((= currentLetter "D") "E")
    ((= currentLetter "E") nil)
    (T "A"))
)

(defun UpdateAttributeR (handle / ename obj maxRevLetter)
  (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle))))
    (setq ename (handent handle)))
  (if (and ename (setq obj (vlax-ename->vla-object ename)))
    (if (IsTargetBlock obj)
      (progn
        (setq maxRevLetter (GetMaxRevisionLetter obj))
        (if maxRevLetter
          (UpdateSingleTag handle "R" maxRevLetter)
          (UpdateSingleTag handle "R" ""))
        (UpdateTabName handle))))
)

(defun EmitirRevisaoBloco (handle revLetter revData revDesc)
  (UpdateSingleTag handle (strcat "REV_" revLetter) revLetter)
  (UpdateSingleTag handle (strcat "DATA_" revLetter) revData)
  (UpdateSingleTag handle (strcat "DESC_" revLetter) revDesc)
  (UpdateAttributeR handle)
)

;; Validação de datas
(defun ParseDateToNum (dateStr / parts d m y)
  (if (and dateStr (/= dateStr "") (/= dateStr "-") (/= dateStr " "))
    (progn
      (setq parts (StrSplit dateStr "-"))
      (if (>= (length parts) 3)
        (progn
          (setq d (atoi (nth 0 parts)))
          (setq m (atoi (nth 1 parts)))
          (setq y (atoi (nth 2 parts)))
          (+ (* y 10000) (* m 100) d))
        0))
    0)
)

(defun ValidateRevisionDates (blk / dataA dataB dataC dataD dataE errors)
  (setq errors "")
  (setq dataA (ParseDateToNum (GetAttValue blk "DATA_A")))
  (setq dataB (ParseDateToNum (GetAttValue blk "DATA_B")))
  (setq dataC (ParseDateToNum (GetAttValue blk "DATA_C")))
  (setq dataD (ParseDateToNum (GetAttValue blk "DATA_D")))
  (setq dataE (ParseDateToNum (GetAttValue blk "DATA_E")))
  (if (and (> dataA 0) (> dataB 0) (< dataB dataA)) (setq errors (strcat errors "DATA_B < DATA_A; ")))
  (if (and (> dataB 0) (> dataC 0) (< dataC dataB)) (setq errors (strcat errors "DATA_C < DATA_B; ")))
  (if (and (> dataC 0) (> dataD 0) (< dataD dataC)) (setq errors (strcat errors "DATA_D < DATA_C; ")))
  (if (and (> dataD 0) (> dataE 0) (< dataE dataD)) (setq errors (strcat errors "DATA_E < DATA_D; ")))
  (if (= errors "") nil errors)
)

;; ============================================================================
;; SECÇÃO 7: MENU PRINCIPAL
;; ============================================================================

(defun c:GESTAODESENHOSJSJ ( / loop opt)
  (vl-load-com)
  (setq loop T)
  
  (while loop
    (textscr)
    (princ "\n\n==============================================")
    (princ "\n          GESTAO DESENHOS JSJ V42.0          ")
    (princ "\n==============================================")
    (princ "\n 1. Modificar Legendas")
    (princ "\n 2. Exportar Lista de Desenhos")
    (princ "\n 3. Importar Lista de Desenhos")
    (princ "\n 4. Dados do Projeto")
    (princ "\n 5. Gerir Layouts")
    (princ "\n----------------------------------------------")
    (princ "\n 9. Navegar (ver desenho)")
    (princ "\n 0. Sair")
    (princ "\n==============================================")
    
    (initget "1 2 3 4 5 9 0")
    (setq opt (getkword "\nEscolha uma opcao [1/2/3/4/5/9/0]: "))
    
    (cond
      ((= opt "1") (Menu_ModificarLegendas))
      ((= opt "2") (Menu_Exportar))
      ((= opt "3") (Menu_Importar))
      ((= opt "4") (Menu_DadosProjeto))
      ((= opt "5") (Menu_GerirLayouts))
      ((= opt "9") (ModoNavegacao))
      ((= opt "0") (setq loop nil))
      ((= opt nil) (setq loop nil))))
  
  (graphscr)
  (princ "\nGestao Desenhos JSJ V42 Terminada.")
  (princ)
)

(defun ModoNavegacao ()
  (graphscr)
  (princ "\n*** MODO NAVEGACAO ***")
  (princ "\nPode agora navegar pelos layouts e verificar os desenhos.")
  (princ "\nQuando terminar, prima ENTER para voltar ao menu.")
  (getstring "\n[ENTER para voltar ao menu]: ")
  (princ)
)

;; ============================================================================
;; SECÇÃO 8: SUBMENU 1 - MODIFICAR LEGENDAS
;; ============================================================================

(defun Menu_ModificarLegendas ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- MODIFICAR LEGENDAS ---")
    (princ (strcat "\n   [Utilizador: " (if *JSJ_USER* *JSJ_USER* "JSJ") "]"))
    (princ "\n   1. Emitir Revisao")
    (princ "\n   2. Editar Titulo de Desenho")
    (princ "\n   3. Editar Tipo em desenhos")
    (princ "\n   4. Editar Elemento em desenhos")
    (princ "\n   5. Editar Pfix em desenhos")
    (princ "\n   6. Definir Utilizador")
    (princ "\n   9. Navegar (ver desenho)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 5 6 9 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/5/6/9/0]: "))
    (cond
      ((= optSub "1") (EmitirRevisao_Unificado))
      ((= optSub "2") (EditarTituloDesenho))
      ((= optSub "3") (EditarCampoEmDesenhos "TIPO"))
      ((= optSub "4") (EditarCampoEmDesenhos "ELEMENTO"))
      ((= optSub "5") (EditarCampoEmDesenhos "PFIX"))
      ((= optSub "6") (SetCurrentUser))
      ((= optSub "9") (ModoNavegacao))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))))
)

;; Editar TITULO de um desenho específico
(defun EditarTituloDesenho ( / doc drawList i item userIdx selectedHandle desNum currentTitulo newTitulo)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq drawList (GetDrawingList))
  
  (if (null drawList)
    (alert "Nenhum desenho encontrado.")
    (progn
      (princ "\n\n=== EDITAR TITULO DE DESENHO ===")
      (princ "\n\nDesenhos disponiveis:")
      (setq i 1)
      (foreach item drawList
        (princ (strcat "\n " (itoa i) ". DES_NUM=" (cadr item) " | " (caddr item)))
        (setq i (1+ i)))
      
      (setq userIdx (getint (strcat "\nEscolha o desenho (1-" (itoa (1- i)) ") ou 0 para cancelar: ")))
      
      (if (and userIdx (> userIdx 0) (<= userIdx (length drawList)))
        (progn
          (setq selectedHandle (car (nth (1- userIdx) drawList)))
          (setq desNum (cadr (nth (1- userIdx) drawList)))
          (setq currentTitulo (GetAttValueByHandle selectedHandle "TITULO"))
          (princ (strcat "\nTitulo atual: " (if (= currentTitulo "") "(vazio)" currentTitulo)))
          
          (setq newTitulo (getstring T "\nNovo Titulo: "))
          
          (if (/= newTitulo "")
            (progn
              (UpdateSingleTag selectedHandle "TITULO" newTitulo)
              (vla-Regen doc acActiveViewport)
              (WriteLog (strcat "TITULO: Des " desNum " alterado para '" newTitulo "'"))
              (alert (strcat "Titulo atualizado!\n\nDesenho: " desNum "\nNovo titulo: " newTitulo)))
            (princ "\nCancelado - titulo vazio.")))
        (princ "\nCancelado."))))
  (princ)
)

;; Editar campo em múltiplos desenhos (TIPO, ELEMENTO, PFIX)
(defun EditarCampoEmDesenhos (tagName / doc newVal targets targetList count desNum isVazio)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq isVazio nil)
  
  (princ (strcat "\n\n=== EDITAR " tagName " EM DESENHOS ==="))
  (princ "\n[Digite 'VAZIO' para limpar o campo]")
  (setq newVal (getstring T (strcat "\nNovo valor para " tagName ": ")))
  
  ;; Verificar se é para deixar vazio
  (if (= (strcase newVal) "VAZIO")
    (progn
      (setq newVal "")
      (setq isVazio T)))
  
  (if (or (/= newVal "") isVazio)
    (progn
      (princ "\n\n--> Aplicar a quais desenhos?")
      (princ "\n    Enter = TODOS")
      (princ "\n    Lista = 1,3,5 ou 1-10")
      (setq targets (getstring T "\nDesenhos: "))
      
      (setq targetList nil)
      (if (/= targets "") (setq targetList (StrSplit targets ",")))
      
      (princ (strcat "\nA aplicar " tagName (if isVazio " (VAZIO)" "") "... "))
      (setq count 0)
      
      (vlax-for lay (vla-get-Layouts doc)
        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (setq desNum (GetAttValue blk "DES_NUM"))
                (if (or (null targetList) (IsNumberInList desNum targetList))
                  (progn
                    (UpdateSingleTag (vla-get-Handle blk) tagName newVal)
                    (UpdateTabName (vla-get-Handle blk))
                    (setq count (1+ count)))))))))
      
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat tagName ": '" (if isVazio "VAZIO" newVal) "' em " (itoa count) " desenhos"))
      (alert (strcat "Concluido!\n\n" tagName " = '" (if isVazio "(vazio)" newVal) "'\nAtualizado em " (itoa count) " desenhos.")))
    (princ "\nCancelado - valor vazio."))
  (princ)
)

;; Emitir Revisão
(defun EmitirRevisao_Unificado ( / doc drawList i item handle desNum currentLetter nextLetter revData revDesc dateStr targets selectedList count)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq drawList (GetDrawingList))
  
  (if (null drawList)
    (alert "Nenhum desenho encontrado.")
    (progn
      (princ "\n\n=== EMITIR REVISAO ===")
      (princ (strcat "\nTotal de desenhos: " (itoa (length drawList))))
      (princ "\n\nEstado atual das revisoes:")
      (setq i 0)
      (foreach item drawList
        (setq handle (car item) desNum (cadr item))
        (setq currentLetter (GetMaxRevisionLetterByHandle handle))
        (setq nextLetter (GetNextRevisionLetter currentLetter))
        (setq i (1+ i))
        (if nextLetter
          (princ (strcat "\n  " (itoa i) ". Des " desNum ": " (if currentLetter currentLetter "-") " -> " nextLetter))
          (princ (strcat "\n  " (itoa i) ". Des " desNum ": " currentLetter " (MAX)"))))
      
      (princ "\n\n--> Em quais desenhos emitir revisao?")
      (princ "\n    Enter = TODOS | Lista = 1,3,5 ou 2-5")
      (setq targets (getstring T "\nOpcao: "))
      
      (if (= targets "")
        (setq selectedList drawList)
        (setq selectedList (ParseSelectionToList drawList targets)))
      
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
                (setq handle (car item) desNum (cadr item))
                (setq currentLetter (GetMaxRevisionLetterByHandle handle))
                (setq nextLetter (GetNextRevisionLetter currentLetter))
                (if nextLetter
                  (progn
                    (EmitirRevisaoBloco handle nextLetter revData revDesc)
                    (setq count (1+ count))
                    (princ (strcat "\n  Des " desNum ": Emitida REV_" nextLetter)))
                  (princ (strcat "\n  Des " desNum ": Ja esta no maximo (E)"))))
              
              (vla-Regen doc acActiveViewport)
              (if (> count 0)
                (WriteLog (strcat "EMITIR REVISAO: " (itoa count) " desenhos - " revData " - " revDesc)))
              (alert (strcat "Revisao emitida em " (itoa count) " desenhos.")))
            (princ "\nOperacao cancelada."))))))
  (graphscr)
  (princ)
)

;; Exportar Dados Gerais (nova opção 4)
(defun ExportarDadosGerais ( / doc path projNum csvFile fileDes blk
                               projNome cliente obra localizacao especialidade projetou
                               fase fasePfix emissao data)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  
  (princ "\n\n=== EXPORTAR DADOS GERAIS ===")
  (princ "\nExporta apenas os dados de projeto, fase e emissão.\n")
  
  ;; Recolher dados do primeiro desenho (exceto TEMPLATE)
  (vlax-for lay (vla-get-Layouts doc)
    (if (and (not projNum)
             (/= (vla-get-ModelType lay) :vlax-true)
             (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
      (vlax-for blk (vla-get-Block lay)
        (if (and (not projNum) (IsTargetBlock blk))
          (progn
            (setq projNum (GetAttValue blk "PROJ_NUM"))
            (setq projNome (GetAttValue blk "PROJ_NOME"))
            (setq cliente (GetAttValue blk "CLIENTE"))
            (setq obra (GetAttValue blk "OBRA"))
            (setq localizacao (GetAttValue blk "LOCALIZACAO"))
            (setq especialidade (GetAttValue blk "ESPECIALIDADE"))
            (setq projetou (GetAttValue blk "PROJETOU"))
            (setq fase (GetAttValue blk "FASE"))
            (setq fasePfix (GetAttValue blk "FASE_PFIX"))
            (setq emissao (GetAttValue blk "EMISSAO"))
            (setq data (GetAttValue blk "DATA")))))))
  
  (if (not projNum)
    (progn
      (alert "Nenhum desenho encontrado para recolher dados.")
      (princ "\nOperação cancelada."))
    (progn
      ;; Mostrar dados a exportar
      (princ "\n\nDados a exportar:")
      (princ (strcat "\n  PROJ_NUM: " projNum))
      (princ (strcat "\n  PROJ_NOME: " projNome))
      (princ (strcat "\n  CLIENTE: " cliente))
      (princ (strcat "\n  OBRA: " obra))
      (princ (strcat "\n  LOCALIZACAO: " localizacao))
      (princ (strcat "\n  ESPECIALIDADE: " especialidade))
      (princ (strcat "\n  PROJETOU: " projetou))
      (princ (strcat "\n  FASE: " fase))
      (princ (strcat "\n  FASE_PFIX: " fasePfix))
      (princ (strcat "\n  EMISSAO: " emissao))
      (princ (strcat "\n  DATA: " data))
      
      ;; Nome do ficheiro: PROJ_NUM-DadosProjeto.csv
      (setq csvFile (getfiled "Guardar Dados Gerais" 
                              (strcat path projNum "-DadosProjeto.csv") 
                              "csv" 1))
      
      (if csvFile
        (progn
          (setq fileDes (open csvFile "w"))
          (if fileDes
            (progn
              ;; Header completo
              (write-line "PROJ_NUM;PROJ_NOME;CLIENTE;OBRA;LOCALIZACAO;ESPECIALIDADE;PROJETOU;FASE;FASE_PFIX;EMISSAO;DATA;PFIX;LAYOUT;DES_NUM;TIPO;ELEMENTO;TITULO;REV_A;DATA_A;DESC_A;REV_B;DATA_B;DESC_B;REV_C;DATA_C;DESC_C;REV_D;DATA_D;DESC_D;REV_E;DATA_E;DESC_E;DWG_SOURCE;ID_CAD" fileDes)
              
              ;; Linha de dados: só os 11 primeiros preenchidos, resto vazio
              (write-line (strcat 
                projNum ";" 
                projNome ";" 
                cliente ";" 
                obra ";" 
                localizacao ";" 
                especialidade ";" 
                projetou ";" 
                fase ";" 
                fasePfix ";" 
                emissao ";" 
                data ";" 
                ";;;;;;;;;;;;;;;;;;;;;;;;") fileDes)
              
              (close fileDes)
              (WriteLog (strcat "EXPORT DADOS GERAIS: " csvFile))
              (alert (strcat "Dados gerais exportados!\n\nFicheiro: " csvFile)))
            (alert "Erro ao criar ficheiro.")))
        (princ "\nCancelado."))))
  (princ)
)

;; Importar Dados Gerais (nova opção 5)
(defun ImportarDadosGerais ( / doc csvFile fileDes line fields confirma count
                               projNum projNome cliente obra localizacao especialidade projetou
                               fase fasePfix emissao data)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== IMPORTAR DADOS GERAIS ===")
  (princ "\nSelecione o ficheiro CSV com os dados gerais.\n")
  
  ;; Pedir ficheiro CSV
  (setq csvFile (getfiled "Selecionar CSV Dados Gerais" "" "csv" 0))
  
  (if (not csvFile)
    (princ "\nOperação cancelada.")
    (progn
      (setq fileDes (open csvFile "r"))
      (if (not fileDes)
        (alert "Erro ao abrir ficheiro.")
        (progn
          ;; Ler header (ignorar)
          (read-line fileDes)
          
          ;; Ler primeira linha de dados
          (setq line (read-line fileDes))
          (close fileDes)
          
          (if (not line)
            (alert "Ficheiro vazio ou sem dados.")
            (progn
              ;; Separar campos por ;
              (setq fields (ParseCSVLine line ";"))
              
              ;; Extrair os 11 campos
              (setq projNum (nth 0 fields))
              (setq projNome (nth 1 fields))
              (setq cliente (nth 2 fields))
              (setq obra (nth 3 fields))
              (setq localizacao (nth 4 fields))
              (setq especialidade (nth 5 fields))
              (setq projetou (nth 6 fields))
              (setq fase (nth 7 fields))
              (setq fasePfix (nth 8 fields))
              (setq emissao (nth 9 fields))
              (setq data (nth 10 fields))
              
              ;; Mostrar dados e pedir confirmação
              (princ "\n\nDados a importar:")
              (princ (strcat "\n  PROJ_NUM: " projNum))
              (princ (strcat "\n  PROJ_NOME: " projNome))
              (princ (strcat "\n  CLIENTE: " cliente))
              (princ (strcat "\n  OBRA: " obra))
              (princ (strcat "\n  LOCALIZACAO: " localizacao))
              (princ (strcat "\n  ESPECIALIDADE: " especialidade))
              (princ (strcat "\n  PROJETOU: " projetou))
              (princ (strcat "\n  FASE: " fase))
              (princ (strcat "\n  FASE_PFIX: " fasePfix))
              (princ (strcat "\n  EMISSAO: " emissao))
              (princ (strcat "\n  DATA: " data))
              
              (princ "\n\nConfirmar importação?")
              (initget "Sim Nao")
              (setq confirma (getkword "\n[Sim/Nao] <Sim>: "))
              
              (if (or (= confirma "Sim") (= confirma nil))
                (progn
                  (princ "\nA aplicar dados a todos os desenhos (incluindo TEMPLATE)...")
                  (setq count 0)
                  
                  (vlax-for lay (vla-get-Layouts doc)
                    (if (/= (vla-get-ModelType lay) :vlax-true)
                      (vlax-for blk (vla-get-Block lay)
                        (if (IsTargetBlock blk)
                          (progn
                            (if (/= projNum "") (UpdateSingleTag (vla-get-Handle blk) "PROJ_NUM" projNum))
                            (if (/= projNome "") (UpdateSingleTag (vla-get-Handle blk) "PROJ_NOME" projNome))
                            (if (/= cliente "") (UpdateSingleTag (vla-get-Handle blk) "CLIENTE" cliente))
                            (if (/= obra "") (UpdateSingleTag (vla-get-Handle blk) "OBRA" obra))
                            (if (/= localizacao "") (UpdateSingleTag (vla-get-Handle blk) "LOCALIZACAO" localizacao))
                            (if (/= especialidade "") (UpdateSingleTag (vla-get-Handle blk) "ESPECIALIDADE" especialidade))
                            (if (/= projetou "") (UpdateSingleTag (vla-get-Handle blk) "PROJETOU" projetou))
                            (if (/= fase "") (UpdateSingleTag (vla-get-Handle blk) "FASE" fase))
                            (if (/= fasePfix "") (UpdateSingleTag (vla-get-Handle blk) "FASE_PFIX" fasePfix))
                            (if (/= emissao "") (UpdateSingleTag (vla-get-Handle blk) "EMISSAO" emissao))
                            (if (/= data "") (UpdateSingleTag (vla-get-Handle blk) "DATA" data))
                            (UpdateTabName (vla-get-Handle blk))
                            (setq count (1+ count)))))))
                  
                  (vla-Regen doc acActiveViewport)
                  (WriteLog (strcat "IMPORT DADOS GERAIS: " (itoa count) " desenhos atualizados"))
                  (alert (strcat "Dados importados com sucesso!\n\n" (itoa count) " desenhos atualizados.")))
                (princ "\nImportação cancelada.")))))))
  (princ)
)

;; ============================================================================
;; SECÇÃO 9: SUBMENU 4 - DADOS DO PROJETO (NOVO)
;; ============================================================================

(defun Menu_DadosProjeto ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- DADOS DO PROJETO ---")
    (princ "\n   1. Definir Dados do Projeto")
    (princ "\n   2. Definir Fase")
    (princ "\n   3. Definir Emissao")
    (princ "\n   4. Exportar Dados do Projeto")
    (princ "\n   5. Importar Dados do Projeto")
    (princ "\n   9. Navegar (ver desenho)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 5 9 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/5/9/0]: "))
    (cond
      ((= optSub "1") (DefinirDadosProjeto))
      ((= optSub "2") (DefinirFase))
      ((= optSub "3") (DefinirEmissao))
      ((= optSub "4") (ExportarDadosGerais))
      ((= optSub "5") (ImportarDadosGerais))
      ((= optSub "9") (ModoNavegacao))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))))
)

;; Definir Dados do Projeto (7 campos globais)
(defun DefinirDadosProjeto ( / doc count projNum projNome cliente obra localizacao especialidade projetou)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== DEFINIR DADOS DO PROJETO ===")
  (princ "\nEstes dados são aplicados a TODOS os desenhos (INCLUINDO TEMPLATE).\n")
  
  ;; Mostrar valores atuais do primeiro desenho
  (vlax-for lay (vla-get-Layouts doc)
    (if (and (not projNum)
             (/= (vla-get-ModelType lay) :vlax-true))
      (vlax-for blk (vla-get-Block lay)
        (if (and (not projNum) (IsTargetBlock blk))
          (progn
            (princ (strcat "\nValores atuais:"))
            (princ (strcat "\n  PROJ_NUM: " (GetAttValue blk "PROJ_NUM")))
            (princ (strcat "\n  PROJ_NOME: " (GetAttValue blk "PROJ_NOME")))
            (princ (strcat "\n  CLIENTE: " (GetAttValue blk "CLIENTE")))
            (princ (strcat "\n  OBRA: " (GetAttValue blk "OBRA")))
            (princ (strcat "\n  LOCALIZACAO: " (GetAttValue blk "LOCALIZACAO")))
            (princ (strcat "\n  ESPECIALIDADE: " (GetAttValue blk "ESPECIALIDADE")))
            (princ (strcat "\n  PROJETOU: " (GetAttValue blk "PROJETOU")))
            (setq projNum T))))))
  
  (princ "\n\n--- Novos valores (Enter para manter atual) ---")
  (setq projNum (getstring T "\nPROJ_NUM (ex: 669): "))
  (setq projNome (getstring T "\nPROJ_NOME: "))
  (setq cliente (getstring T "\nCLIENTE: "))
  (setq obra (getstring T "\nOBRA: "))
  (setq localizacao (getstring T "\nLOCALIZACAO: "))
  (setq especialidade (getstring T "\nESPECIALIDADE (ex: ESTRUTURA E FUNDAÇÕES): "))
  (setq projetou (getstring T "\nPROJETOU: "))
  
  (princ "\nA aplicar dados do projeto...")
  (setq count 0)
  
  (vlax-for lay (vla-get-Layouts doc)
    (if (/= (vla-get-ModelType lay) :vlax-true)
      (vlax-for blk (vla-get-Block lay)
        (if (IsTargetBlock blk)
          (progn
            (if (/= projNum "") (UpdateSingleTag (vla-get-Handle blk) "PROJ_NUM" projNum))
            (if (/= projNome "") (UpdateSingleTag (vla-get-Handle blk) "PROJ_NOME" projNome))
            (if (/= cliente "") (UpdateSingleTag (vla-get-Handle blk) "CLIENTE" cliente))
            (if (/= obra "") (UpdateSingleTag (vla-get-Handle blk) "OBRA" obra))
            (if (/= localizacao "") (UpdateSingleTag (vla-get-Handle blk) "LOCALIZACAO" localizacao))
            (if (/= especialidade "") (UpdateSingleTag (vla-get-Handle blk) "ESPECIALIDADE" especialidade))
            (if (/= projetou "") (UpdateSingleTag (vla-get-Handle blk) "PROJETOU" projetou))
            (UpdateTabName (vla-get-Handle blk))
            (setq count (1+ count)))))))
  
  (vla-Regen doc acActiveViewport)
  (WriteLog (strcat "DADOS PROJETO: Atualizados " (itoa count) " desenhos"))
  (alert (strcat "Dados do projeto atualizados!\n\n" (itoa count) " desenhos afetados."))
  (princ)
)

;; Definir Fase
(defun DefinirFase ( / doc newFase newFasePfix zerarRevs count countRev)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== DEFINIR FASE DO PROJETO ===")
  (princ "\nExemplos: PROJETO DE EXECUÇÃO, LICENCIAMENTO, ESTUDO PRÉVIO")
  
  (setq newFase (getstring T "\nFASE: "))
  (setq newFasePfix (getstring T "\nFASE_PFIX (prefixo para tab, ex: PE): "))
  
  (if (or (/= newFase "") (/= newFasePfix ""))
    (progn
      (princ "\nA aplicar fase...")
      (setq count 0)
      
      (vlax-for lay (vla-get-Layouts doc)
        (if (/= (vla-get-ModelType lay) :vlax-true)
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (if (/= newFase "") (UpdateSingleTag (vla-get-Handle blk) "FASE" newFase))
                (if (/= newFasePfix "") (UpdateSingleTag (vla-get-Handle blk) "FASE_PFIX" newFasePfix))
                (UpdateTabName (vla-get-Handle blk))
                (setq count (1+ count)))))))
      
      (princ (strcat "\n" (itoa count) " desenhos atualizados."))
      
      ;; Perguntar se quer zerar revisões
      (princ "\n\n--> Pretende APAGAR todas as revisões (zerar projeto)?")
      (initget "Sim Nao")
      (setq zerarRevs (getkword "\n    [Sim/Nao] <Nao>: "))
      
      (if (= zerarRevs "Sim")
        (progn
          (princ "\nA apagar revisões...")
          (setq countRev 0)
          (vlax-for lay (vla-get-Layouts doc)
            (if (and (/= (vla-get-ModelType lay) :vlax-true)
                     (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
              (vlax-for blk (vla-get-Block lay)
                (if (IsTargetBlock blk)
                  (progn
                    (foreach letra '("A" "B" "C" "D" "E")
                      (UpdateSingleTag (vla-get-Handle blk) (strcat "REV_" letra) "")
                      (UpdateSingleTag (vla-get-Handle blk) (strcat "DATA_" letra) "")
                      (UpdateSingleTag (vla-get-Handle blk) (strcat "DESC_" letra) ""))
                    (UpdateSingleTag (vla-get-Handle blk) "R" "")
                    (UpdateTabName (vla-get-Handle blk))
                    (setq countRev (1+ countRev)))))))
          (princ (strcat (itoa countRev) " desenhos zerados."))
          (WriteLog (strcat "FASE: Revisões apagadas em " (itoa countRev) " desenhos"))))
      
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat "FASE: '" newFase "' PFIX:'" newFasePfix "' em " (itoa count) " desenhos"))
      (alert (strcat "Fase atualizada!\n\n" (itoa count) " desenhos afetados.")))
    (princ "\nCancelado - valores vazios."))
  (princ)
)

;; Definir Emissão
(defun DefinirEmissao ( / doc newEmissao newData zerarRevs count countRev)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== DEFINIR EMISSÃO ===")
  (princ "\nExemplos: EMISSAO=E00, DATA=OUTUBRO 2025")
  
  (setq newEmissao (getstring T "\nEMISSAO (ex: E00): "))
  (setq newData (getstring T "\nDATA (ex: OUTUBRO 2025): "))
  
  (if (or (/= newEmissao "") (/= newData ""))
    (progn
      (princ "\nA aplicar emissão...")
      (setq count 0)
      
      (vlax-for lay (vla-get-Layouts doc)
        (if (/= (vla-get-ModelType lay) :vlax-true)
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (if (/= newEmissao "") (UpdateSingleTag (vla-get-Handle blk) "EMISSAO" newEmissao))
                (if (/= newData "") (UpdateSingleTag (vla-get-Handle blk) "DATA" newData))
                (UpdateTabName (vla-get-Handle blk))
                (setq count (1+ count)))))))
      
      (princ (strcat "\n" (itoa count) " desenhos atualizados."))
      
      ;; Perguntar se quer zerar revisões
      (princ "\n\n--> Pretende APAGAR todas as revisões (zerar projeto)?")
      (initget "Sim Nao")
      (setq zerarRevs (getkword "\n    [Sim/Nao] <Nao>: "))
      
      (if (= zerarRevs "Sim")
        (progn
          (princ "\nA apagar revisões...")
          (setq countRev 0)
          (vlax-for lay (vla-get-Layouts doc)
            (if (and (/= (vla-get-ModelType lay) :vlax-true)
                     (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
              (vlax-for blk (vla-get-Block lay)
                (if (IsTargetBlock blk)
                  (progn
                    (foreach letra '("A" "B" "C" "D" "E")
                      (UpdateSingleTag (vla-get-Handle blk) (strcat "REV_" letra) "")
                      (UpdateSingleTag (vla-get-Handle blk) (strcat "DATA_" letra) "")
                      (UpdateSingleTag (vla-get-Handle blk) (strcat "DESC_" letra) ""))
                    (UpdateSingleTag (vla-get-Handle blk) "R" "")
                    (UpdateTabName (vla-get-Handle blk))
                    (setq countRev (1+ countRev)))))))
          (princ (strcat (itoa countRev) " desenhos zerados."))
          (WriteLog (strcat "EMISSAO: Revisões apagadas em " (itoa countRev) " desenhos"))))
      
      (vla-Regen doc acActiveViewport)
      (WriteLog (strcat "EMISSAO: '" newEmissao "' DATA:'" newData "' em " (itoa count) " desenhos"))
      (alert (strcat "Emissão atualizada!\n\n" (itoa count) " desenhos afetados."
                     (if (= zerarRevs "Sim") (strcat "\nRevisões apagadas em " (itoa countRev) " desenhos.") ""))))
    (princ "\nCancelado - valores vazios."))
  (princ)
)

;; ============================================================================
;; SECÇÃO 10: SUBMENU 2 - EXPORTAR
;; ============================================================================

;; ---------------------------------------------------------------------
;; CHECK DUPLICATES DES_NUM
;; Retorna lista de DES_NUM duplicados: ((desNum . count) ...)
;; ---------------------------------------------------------------------
(defun CheckDuplicateDES_NUM ( / doc duplicates desNumList desNum countMap item)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq desNumList '())
  
  ;; Recolher todos os DES_NUM
  (vlax-for lay (vla-get-Layouts doc)
    (if (and (/= (vla-get-ModelType lay) :vlax-true)
             (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
      (vlax-for blk (vla-get-Block lay)
        (if (IsTargetBlock blk)
          (progn
            (setq desNum (GetAttValue blk "DES_NUM"))
            (if (and desNum (/= desNum "") (/= desNum " "))
              (setq desNumList (cons desNum desNumList))))))))
  
  ;; Contar ocorrências
  (setq countMap '())
  (foreach desNum desNumList
    (if (assoc desNum countMap)
      (setq countMap (subst (cons desNum (1+ (cdr (assoc desNum countMap))))
                           (assoc desNum countMap)
                           countMap))
      (setq countMap (cons (cons desNum 1) countMap))))
  
  ;; Filtrar apenas duplicados (count > 1)
  (setq duplicates '())
  (foreach item countMap
    (if (> (cdr item) 1)
      (setq duplicates (cons item duplicates))))
  
  duplicates
)

;; Mostrar aviso de duplicados
(defun WarnDuplicateDES_NUM (duplicates / msg item)
  (if duplicates
    (progn
      (setq msg "AVISO: DES_NUM duplicados encontrados!\n")
      (foreach item duplicates
        (setq msg (strcat msg "\n  DES_NUM=" (car item) " (" (itoa (cdr item)) "x)")))
      (setq msg (strcat msg "\n\nRecomendação: Verifique antes de exportar."))
      (alert msg)
      T)
    nil)
)

;; ---------------------------------------------------------------------
;; CSV CONFIG SYSTEM
;; Lê csv_config.json se existir no mesmo diretório do DWG
;; ---------------------------------------------------------------------

;; Ler ficheiro de texto completo
(defun ReadFileContents (filepath / fh content line)
  (setq content "")
  (if (findfile filepath)
    (progn
      (setq fh (open filepath "r"))
      (if fh
        (progn
          (while (setq line (read-line fh))
            (setq content (strcat content line)))
          (close fh)))))
  content
)

;; Parser JSON simples para csv_config.json
;; Retorna lista associativa: (("columns" . lista) ("separator" . ";") ("includeHeader" . T))
(defun ParseCSVConfig (jsonStr / result columns sep incHeader startPos endPos colStr colList tempStr)
  (setq result nil columns nil sep ";" incHeader T)
  
  (if (and jsonStr (/= jsonStr ""))
    (progn
      ;; Extrair separator
      (if (vl-string-search "\"separator\"" jsonStr)
        (progn
          (setq startPos (vl-string-search "\"separator\"" jsonStr))
          (setq startPos (vl-string-search ":" jsonStr startPos))
          (setq startPos (vl-string-search "\"" jsonStr (1+ startPos)))
          (setq endPos (vl-string-search "\"" jsonStr (1+ startPos)))
          (if (and startPos endPos)
            (setq sep (substr jsonStr (+ startPos 2) (- endPos startPos 1))))))
      
      ;; Extrair includeHeader
      (if (vl-string-search "false" jsonStr)
        (setq incHeader nil))
      
      ;; Extrair columns array
      (if (vl-string-search "\"columns\"" jsonStr)
        (progn
          (setq startPos (vl-string-search "[" jsonStr))
          (setq endPos (vl-string-search "]" jsonStr))
          (if (and startPos endPos (< startPos endPos))
            (progn
              (setq colStr (substr jsonStr (+ startPos 2) (- endPos startPos 1)))
              ;; Parse column names
              (setq colList '())
              (while (vl-string-search "\"" colStr)
                (setq startPos (vl-string-search "\"" colStr))
                (setq endPos (vl-string-search "\"" colStr (1+ startPos)))
                (if (and startPos endPos)
                  (progn
                    (setq colList (cons (substr colStr (+ startPos 2) (- endPos startPos 1)) colList))
                    (setq colStr (substr colStr (+ endPos 2))))))
              (setq columns (reverse colList))))))
      
      (setq result (list 
        (cons "columns" columns)
        (cons "separator" sep)
        (cons "includeHeader" incHeader)))))
  result
)

;; Carregar CSV config do diretório do DWG
(defun LoadCSVConfig ( / path configFile jsonStr)
  (setq path (getvar "DWGPREFIX"))
  (setq configFile (strcat path "csv_config.json"))
  (if (findfile configFile)
    (progn
      (setq jsonStr (ReadFileContents configFile))
      (ParseCSVConfig jsonStr))
    nil)
)

;; Obter valor de atributo por nome (para configuração dinâmica)
(defun GetAttValueDynamic (blk attrName / result maxRev)
  (cond
    ((= (strcase attrName) "REVISAO")
      (setq maxRev (GetMaxRevision blk))
      (car maxRev))
    ((= (strcase attrName) "DATA_REV")
      (setq maxRev (GetMaxRevision blk))
      (cadr maxRev))
    ((= (strcase attrName) "DESC_REV")
      (setq maxRev (GetMaxRevision blk))
      (caddr maxRev))
    ((= (strcase attrName) "HANDLE")
      (vla-get-Handle blk))
    (T
      (CleanCSV (GetAttValue blk attrName))))
)

(defun Menu_Exportar ( / loopSub optSub duplicates)
  (setq loopSub T)
  
  ;; Verificar duplicados ao entrar no menu
  (setq duplicates (CheckDuplicateDES_NUM))
  (WarnDuplicateDES_NUM duplicates)
  
  (while loopSub
    (textscr)
    (princ "\n\n   --- EXPORTAR LISTA DE DESENHOS ---")
    (princ "\n   1. Gerar CSV (Campos Principais)")
    (princ "\n   2. Gerar CSV (Todos os Campos)")
    (princ "\n   3. Gerar CSV (Configuração Personalizada)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/0]: "))
    (cond
      ((= optSub "1") (ExportarCSV_Principal))
      ((= optSub "2") (ExportarCSV_Completo))
      ((= optSub "3") (ExportarCSV_Personalizado))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))))
)

;; Exportar CSV Principal
(defun ExportarCSV_Principal ( / doc path dwgName csvFile fileDes layoutList dataList row blk layName maxRev)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq dwgName (GetDWGName))
  
  (princ "\nA recolher dados...")
  (setq dataList '())
  (setq layoutList (GetLayoutsRaw doc))
  
  (foreach lay layoutList
    (vlax-for blk (vla-get-Block lay)
      (if (IsTargetBlock blk)
        (progn
          (setq layName (vla-get-Name lay))
          (setq maxRev (GetMaxRevision blk))
          (setq row (list
            dwgName
            (CleanCSV (GetAttValue blk "PROJ_NUM"))
            (CleanCSV (GetAttValue blk "PFIX"))
            (CleanCSV (GetAttValue blk "DES_NUM"))
            (CleanCSV (GetAttValue blk "TIPO"))
            (CleanCSV (GetAttValue blk "ELEMENTO"))
            (CleanCSV (GetAttValue blk "TITULO"))
            (CleanCSV (car maxRev))
            (CleanCSV (cadr maxRev))
            (CleanCSV (caddr maxRev))
            (vla-get-Handle blk)
            layName))
          (setq dataList (cons row dataList))))))
  
  (setq dataList (vl-sort dataList '(lambda (a b) (< (atoi (nth 3 a)) (atoi (nth 3 b))))))
  
  (setq csvFile (getfiled "Guardar Lista CSV" (strcat path dwgName "_Lista.csv") "csv" 1))
  (if csvFile
    (progn
      (setq fileDes (open csvFile "w"))
      (if fileDes
        (progn
          (write-line "DWG_SOURCE;PROJ_NUM;PFIX;DES_NUM;TIPO;ELEMENTO;TITULO;REVISAO;DATA;DESCRICAO;ID_CAD;LAYOUT" fileDes)
          (foreach row dataList
            (write-line (strcat (nth 0 row) ";" (nth 1 row) ";" (nth 2 row) ";" (nth 3 row) ";"
                               (nth 4 row) ";" (nth 5 row) ";" (nth 6 row) ";" (nth 7 row) ";"
                               (nth 8 row) ";" (nth 9 row) ";" (nth 10 row) ";" (nth 11 row)) fileDes))
          (close fileDes)
          (WriteLog (strcat "EXPORT CSV: " (itoa (length dataList)) " desenhos"))
          (alert (strcat "Sucesso!\n\nFicheiro: " csvFile "\nDesenhos: " (itoa (length dataList)))))
        (alert "Erro ao criar ficheiro.")))
    (princ "\nCancelado."))
  (princ)
)

;; Exportar CSV Completo (todos os campos)
(defun ExportarCSV_Completo ( / doc path dwgName csvFile fileDes layoutList blk layName row dataList)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq dwgName (GetDWGName))
  
  (princ "\nA recolher dados...")
  (setq dataList '())
  (setq layoutList (GetLayoutsRaw doc))
  
  (foreach lay layoutList
    (vlax-for blk (vla-get-Block lay)
      (if (IsTargetBlock blk)
        (progn
          (setq layName (vla-get-Name lay))
          (setq row (list
            (CleanCSV (GetAttValue blk "PROJ_NUM"))
            (CleanCSV (GetAttValue blk "PROJ_NOME"))
            (CleanCSV (GetAttValue blk "CLIENTE"))
            (CleanCSV (GetAttValue blk "OBRA"))
            (CleanCSV (GetAttValue blk "LOCALIZACAO"))
            (CleanCSV (GetAttValue blk "ESPECIALIDADE"))
            (CleanCSV (GetAttValue blk "PROJETOU"))
            (CleanCSV (GetAttValue blk "FASE"))
            (CleanCSV (GetAttValue blk "FASE_PFIX"))
            (CleanCSV (GetAttValue blk "EMISSAO"))
            (CleanCSV (GetAttValue blk "DATA"))
            (CleanCSV (GetAttValue blk "PFIX"))
            layName
            (CleanCSV (GetAttValue blk "DES_NUM"))
            (CleanCSV (GetAttValue blk "TIPO"))
            (CleanCSV (GetAttValue blk "ELEMENTO"))
            (CleanCSV (GetAttValue blk "TITULO"))
            (CleanCSV (GetAttValue blk "REV_A"))
            (CleanCSV (GetAttValue blk "DATA_A"))
            (CleanCSV (GetAttValue blk "DESC_A"))
            (CleanCSV (GetAttValue blk "REV_B"))
            (CleanCSV (GetAttValue blk "DATA_B"))
            (CleanCSV (GetAttValue blk "DESC_B"))
            (CleanCSV (GetAttValue blk "REV_C"))
            (CleanCSV (GetAttValue blk "DATA_C"))
            (CleanCSV (GetAttValue blk "DESC_C"))
            (CleanCSV (GetAttValue blk "REV_D"))
            (CleanCSV (GetAttValue blk "DATA_D"))
            (CleanCSV (GetAttValue blk "DESC_D"))
            (CleanCSV (GetAttValue blk "REV_E"))
            (CleanCSV (GetAttValue blk "DATA_E"))
            (CleanCSV (GetAttValue blk "DESC_E"))
            dwgName
            (vla-get-Handle blk)))
          (setq dataList (cons row dataList))))))
  
  ;; Ordenar por DES_NUM (agora está na posição 13, index 13)
  (setq dataList (vl-sort dataList '(lambda (a b) (< (atoi (nth 13 a)) (atoi (nth 13 b))))))
  
  (setq csvFile (getfiled "Guardar Lista CSV Completa" (strcat path dwgName "_ListaCompleta.csv") "csv" 1))
  (if csvFile
    (progn
      (setq fileDes (open csvFile "w"))
      (if fileDes
        (progn
          (write-line "PROJ_NUM;PROJ_NOME;CLIENTE;OBRA;LOCALIZACAO;ESPECIALIDADE;PROJETOU;FASE;FASE_PFIX;EMISSAO;DATA;PFIX;LAYOUT;DES_NUM;TIPO;ELEMENTO;TITULO;REV_A;DATA_A;DESC_A;REV_B;DATA_B;DESC_B;REV_C;DATA_C;DESC_C;REV_D;DATA_D;DESC_D;REV_E;DATA_E;DESC_E;DWG_SOURCE;ID_CAD" fileDes)
          (foreach row dataList
            (write-line (apply 'strcat (mapcar '(lambda (x) (strcat x ";")) row)) fileDes))
          (close fileDes)
          (WriteLog (strcat "EXPORT CSV COMPLETO: " (itoa (length dataList)) " desenhos"))
          (alert (strcat "Sucesso!\n\nFicheiro: " csvFile "\nDesenhos: " (itoa (length dataList)))))
        (alert "Erro ao criar ficheiro.")))
    (princ "\nCancelado."))
  (princ)
)

;; Exportar CSV Personalizado (usando csv_config.json)
(defun ExportarCSV_Personalizado ( / doc path dwgName csvFile fileDes config columns sep incHeader
                                     layoutList dataList row blk layName col headerLine dataLine)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq dwgName (GetDWGName))
  
  ;; Carregar configuração
  (setq config (LoadCSVConfig))
  
  (if (null config)
    (progn
      (alert (strcat "Ficheiro csv_config.json não encontrado!\n\n"
                     "Crie o ficheiro em:\n" path "csv_config.json\n\n"
                     "Exemplo de conteúdo:\n"
                     "{\n"
                     "  \"columns\": [\"DES_NUM\", \"TIPO\", \"TITULO\"],\n"
                     "  \"separator\": \";\",\n"
                     "  \"includeHeader\": true\n"
                     "}"))
      (princ "\nConfiguração não encontrada."))
    (progn
      (setq columns (cdr (assoc "columns" config)))
      (setq sep (cdr (assoc "separator" config)))
      (setq incHeader (cdr (assoc "includeHeader" config)))
      
      (if (null columns)
        (alert "Erro: Nenhuma coluna definida em csv_config.json")
        (progn
          (princ (strcat "\n\n=== EXPORTAR CSV PERSONALIZADO ==="))
          (princ (strcat "\nColunas: " (itoa (length columns))))
          (princ (strcat "\nSeparador: '" sep "'"))
          (princ "\nA recolher dados...")
          
          (setq dataList '())
          (setq layoutList (GetLayoutsRaw doc))
          
          (foreach lay layoutList
            (vlax-for blk (vla-get-Block lay)
              (if (IsTargetBlock blk)
                (progn
                  (setq layName (vla-get-Name lay))
                  (setq row '())
                  ;; Construir linha com base nas colunas configuradas
                  (foreach col columns
                    (cond
                      ((= (strcase col) "DWG_SOURCE") (setq row (cons dwgName row)))
                      ((= (strcase col) "LAYOUT") (setq row (cons layName row)))
                      ((= (strcase col) "ID_CAD") (setq row (cons (vla-get-Handle blk) row)))
                      ((= (strcase col) "REVISAO") 
                        (setq row (cons (CleanCSV (car (GetMaxRevision blk))) row)))
                      ((= (strcase col) "DATA_REV") 
                        (setq row (cons (CleanCSV (cadr (GetMaxRevision blk))) row)))
                      ((= (strcase col) "DESC_REV") 
                        (setq row (cons (CleanCSV (caddr (GetMaxRevision blk))) row)))
                      (T (setq row (cons (CleanCSV (GetAttValue blk col)) row)))))
                  (setq row (reverse row))
                  (setq dataList (cons row dataList))))))
          
          ;; Ordenar por DES_NUM se existir na lista
          (if (member "DES_NUM" (mapcar 'strcase columns))
            (progn
              (setq desNumIdx (- (length columns) 1 (length (member "DES_NUM" (reverse (mapcar 'strcase columns))))))
              (if (>= desNumIdx 0)
                (setq dataList (vl-sort dataList 
                  '(lambda (a b) (< (atoi (nth desNumIdx a)) (atoi (nth desNumIdx b)))))))))
          
          (setq csvFile (getfiled "Guardar Lista CSV" (strcat path dwgName "_ListaConfig.csv") "csv" 1))
          (if csvFile
            (progn
              (setq fileDes (open csvFile "w"))
              (if fileDes
                (progn
                  ;; Escrever cabeçalho se configurado
                  (if incHeader
                    (progn
                      (setq headerLine "")
                      (foreach col columns
                        (setq headerLine (strcat headerLine (if (= headerLine "") "" sep) col)))
                      (write-line headerLine fileDes)))
                  
                  ;; Escrever dados
                  (foreach row dataList
                    (setq dataLine "")
                    (foreach val row
                      (setq dataLine (strcat dataLine (if (= dataLine "") "" sep) val)))
                    (write-line dataLine fileDes))
                  
                  (close fileDes)
                  (WriteLog (strcat "EXPORT CSV CONFIG: " (itoa (length dataList)) " desenhos, " (itoa (length columns)) " colunas"))
                  (alert (strcat "Sucesso!\n\nFicheiro: " csvFile 
                                "\nDesenhos: " (itoa (length dataList))
                                "\nColunas: " (itoa (length columns)))))
                (alert "Erro ao criar ficheiro.")))
            (princ "\nCancelado."))))))
  (princ)
)

;; ============================================================================
;; SECÇÃO 11: SUBMENU 3 - IMPORTAR
;; ============================================================================

(defun Menu_Importar ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- IMPORTAR LISTA DE DESENHOS ---")
    (princ "\n   1. Importar CSV (por ID_CAD)")
    (princ "\n   2. Importar CSV (por Layout)")
    (princ "\n   0. Voltar")
    (initget "1 2 0")
    (setq optSub (getkword "\n   Opcao [1/2/0]: "))
    (cond
      ((= optSub "1") (ImportarCSV_PorHandle))
      ((= optSub "2") (ImportarCSV_PorLayout))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))))
)

;; Importar por Handle (ID_CAD)
(defun ImportarCSV_PorHandle ( / doc path csvFile fileDes line parts headers headerMap
                                 idCad countUpdates countNotFound ename obj foundBlock)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq csvFile (getfiled "Selecione o CSV" path "csv" 4))
  
  (if (and csvFile (findfile csvFile))
    (progn
      (setq fileDes (open csvFile "r"))
      (if fileDes
        (progn
          (princ "\nA processar CSV...")
          (setq countUpdates 0 countNotFound 0)
          
          (setq line (read-line fileDes))
          (setq headers (StrSplit line ";"))
          (setq headerMap (BuildHeaderMap headers))
          
          (while (setq line (read-line fileDes))
            (setq parts (StrSplit line ";"))
            (setq idCad (GetCSVValue parts headerMap "ID_CAD"))
            
            (if (and idCad (/= idCad ""))
              (progn
                (setq foundBlock nil)
                (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list idCad))))
                  (progn
                    (setq ename (handent idCad))
                    (if ename
                      (progn
                        (setq obj (vlax-ename->vla-object ename))
                        (if (IsTargetBlock obj) (setq foundBlock T))))))
                
                (if foundBlock
                  (progn
                    (ImportarCamposCSV idCad parts headerMap)
                    (UpdateTabName idCad)
                    (princ ".")
                    (setq countUpdates (1+ countUpdates)))
                  (progn
                    (princ (strcat "\n  [!] ID_CAD não encontrado: " idCad))
                    (setq countNotFound (1+ countNotFound)))))))
          
          (close fileDes)
          (vla-Regen doc acActiveViewport)
          (if (> countUpdates 0)
            (WriteLog (strcat "IMPORT CSV: " (itoa countUpdates) " desenhos")))
          (alert (strcat "Importação concluída!\n\nAtualizados: " (itoa countUpdates)
                        "\nNão encontrados: " (itoa countNotFound))))
        (alert "Erro ao abrir ficheiro.")))
    (princ "\nCancelado."))
  (princ)
)

;; Função auxiliar para importar campos
(defun ImportarCamposCSV (handle parts headerMap / val)
  ;; Campos do projeto
  (if (setq val (GetCSVValue parts headerMap "PROJ_NUM")) (if (/= val "") (UpdateSingleTag handle "PROJ_NUM" val)))
  (if (setq val (GetCSVValue parts headerMap "PROJ_NOME")) (if (/= val "") (UpdateSingleTag handle "PROJ_NOME" val)))
  (if (setq val (GetCSVValue parts headerMap "CLIENTE")) (if (/= val "") (UpdateSingleTag handle "CLIENTE" val)))
  (if (setq val (GetCSVValue parts headerMap "OBRA")) (if (/= val "") (UpdateSingleTag handle "OBRA" val)))
  (if (setq val (GetCSVValue parts headerMap "LOCALIZACAO")) (if (/= val "") (UpdateSingleTag handle "LOCALIZACAO" val)))
  (if (setq val (GetCSVValue parts headerMap "ESPECIALIDADE")) (if (/= val "") (UpdateSingleTag handle "ESPECIALIDADE" val)))
  (if (setq val (GetCSVValue parts headerMap "PROJETOU")) (if (/= val "") (UpdateSingleTag handle "PROJETOU" val)))
  ;; Fase e emissão
  (if (setq val (GetCSVValue parts headerMap "FASE")) (if (/= val "") (UpdateSingleTag handle "FASE" val)))
  (if (setq val (GetCSVValue parts headerMap "FASE_PFIX")) (if (/= val "") (UpdateSingleTag handle "FASE_PFIX" val)))
  (if (setq val (GetCSVValue parts headerMap "EMISSAO")) (if (/= val "") (UpdateSingleTag handle "EMISSAO" val)))
  (if (setq val (GetCSVValue parts headerMap "DATA")) (if (/= val "") (UpdateSingleTag handle "DATA" val)))
  ;; Desenho
  (if (setq val (GetCSVValue parts headerMap "PFIX")) (if (/= val "") (UpdateSingleTag handle "PFIX" val)))
  (if (setq val (GetCSVValue parts headerMap "DES_NUM")) (if (/= val "") (UpdateSingleTag handle "DES_NUM" val)))
  (if (setq val (GetCSVValue parts headerMap "TIPO")) (if (/= val "") (UpdateSingleTag handle "TIPO" val)))
  (if (setq val (GetCSVValue parts headerMap "ELEMENTO")) (if (/= val "") (UpdateSingleTag handle "ELEMENTO" val)))
  (if (setq val (GetCSVValue parts headerMap "TITULO")) (if (/= val "") (UpdateSingleTag handle "TITULO" val)))
)

;; Importar por Layout
(defun ImportarCSV_PorLayout ( / doc path csvFile fileDes line parts headers headerMap
                                 layoutName countUpdates countNotFound foundBlock handle)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq path (getvar "DWGPREFIX"))
  (setq csvFile (getfiled "Selecione o CSV" path "csv" 4))
  
  (if (and csvFile (findfile csvFile))
    (progn
      (setq fileDes (open csvFile "r"))
      (if fileDes
        (progn
          (princ "\nA processar CSV...")
          (setq countUpdates 0 countNotFound 0)
          
          (setq line (read-line fileDes))
          (setq headers (StrSplit line ";"))
          (setq headerMap (BuildHeaderMap headers))
          
          (while (setq line (read-line fileDes))
            (setq parts (StrSplit line ";"))
            (setq layoutName (GetCSVValue parts headerMap "LAYOUT"))
            (if (null layoutName) (setq layoutName (GetCSVValue parts headerMap "TAG DO LAYOUT")))
            
            (if (and layoutName (/= layoutName ""))
              (progn
                (setq foundBlock nil handle nil)
                (vlax-for lay (vla-get-Layouts doc)
                  (if (and (not foundBlock)
                           (= (strcase (vla-get-Name lay)) (strcase layoutName)))
                    (vlax-for blk (vla-get-Block lay)
                      (if (and (not foundBlock) (IsTargetBlock blk))
                        (progn
                          (setq foundBlock T)
                          (setq handle (vla-get-Handle blk)))))))
                
                (if foundBlock
                  (progn
                    (ImportarCamposCSV handle parts headerMap)
                    (UpdateTabName handle)
                    (princ ".")
                    (setq countUpdates (1+ countUpdates)))
                  (progn
                    (princ (strcat "\n  [!] Layout não encontrado: " layoutName))
                    (setq countNotFound (1+ countNotFound)))))))
          
          (close fileDes)
          (vla-Regen doc acActiveViewport)
          (if (> countUpdates 0)
            (WriteLog (strcat "IMPORT CSV LAYOUT: " (itoa countUpdates) " desenhos")))
          (alert (strcat "Importação concluída!\n\nAtualizados: " (itoa countUpdates)
                        "\nNão encontrados: " (itoa countNotFound))))
        (alert "Erro ao abrir ficheiro.")))
    (princ "\nCancelado."))
  (princ)
)

;; Funções auxiliares para CSV
(defun BuildHeaderMap (headers / map idx header)
  (setq map '() idx 0)
  (foreach header headers
    (setq map (cons (cons (strcase (vl-string-trim " " header)) idx) map))
    (setq idx (1+ idx)))
  map
)

(defun GetCSVValue (parts headerMap headerName / idx)
  (setq idx (cdr (assoc (strcase headerName) headerMap)))
  (if (and idx (< idx (length parts)))
    (vl-string-trim " " (nth idx parts))
    nil)
)

;; ============================================================================
;; SECÇÃO 12: SUBMENU 5 - GERIR LAYOUTS
;; ============================================================================

(defun Menu_GerirLayouts ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- GERIR LAYOUTS ---")
    (princ "\n   1. Gerar Novos Desenhos")
    (princ "\n   2. Adicionar Desenho Intermedio")
    (princ "\n   3. Apagar Desenhos")
    (princ "\n   4. Numerar Desenhos")
    (princ "\n   5. Ordenar Desenhos")
    (princ "\n   6. Atualizar Nomes Layouts")
    (princ "\n   9. Navegar (ver desenho)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 5 6 9 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/5/6/9/0]: "))
    (cond
      ((= optSub "1") (GerarLayoutsTemplate))
      ((= optSub "2") (AdicionarDesenhoIntermedio))
      ((= optSub "3") (ApagarDesenhos))
      ((= optSub "4") (NumerarDesenhos))
      ((= optSub "5") (OrdenarTabs))
      ((= optSub "6") (AtualizarNomesLayouts))
      ((= optSub "9") (ModoNavegacao))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))))
)

;; Adicionar Desenho Intermédio
(defun AdicionarDesenhoIntermedio ( / doc layouts modeOpt insertNum pfixList selectedPfix
                                      layoutList blkPfix blkNum maxNum countRenumbered
                                      layName paperSpace targetPfix i newHandle
                                      ;; Dados do projeto (copiados do primeiro desenho)
                                      projNum projNome cliente obra localizacao especialidade projetou
                                      fase fasePfix emissao dataEmissao
                                      ;; Novos dados pedidos ao user
                                      newPfix newTipo newElemento newTitulo
                                      ;; Ordenação
                                      templateLay layObj valNum)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq layouts (vla-get-Layouts doc))
  
  ;; Verificar se TEMPLATE existe
  (if (not (catch-apply 'vla-Item (list layouts "TEMPLATE")))
    (progn (alert "ERRO: Layout 'TEMPLATE' não existe.") (exit)))
  
  ;; Recolher dados do projeto do primeiro desenho existente
  (setq projNum nil)
  (vlax-for lay layouts
    (if (and (not projNum)
             (/= (vla-get-ModelType lay) :vlax-true)
             (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
      (vlax-for blk (vla-get-Block lay)
        (if (and (not projNum) (IsTargetBlock blk))
          (progn
            (setq projNum (GetAttValue blk "PROJ_NUM"))
            (setq projNome (GetAttValue blk "PROJ_NOME"))
            (setq cliente (GetAttValue blk "CLIENTE"))
            (setq obra (GetAttValue blk "OBRA"))
            (setq localizacao (GetAttValue blk "LOCALIZACAO"))
            (setq especialidade (GetAttValue blk "ESPECIALIDADE"))
            (setq projetou (GetAttValue blk "PROJETOU"))
            (setq fase (GetAttValue blk "FASE"))
            (setq fasePfix (GetAttValue blk "FASE_PFIX"))
            (setq emissao (GetAttValue blk "EMISSAO"))
            (setq dataEmissao (GetAttValue blk "DATA")))))))
  
  (princ "\n\n=== ADICIONAR DESENHO INTERMEDIO ===")
  (princ "\n\n  [1] Numeracao Sequencial")
  (princ "\n  [2] Numeracao por PFIX")
  (princ "\n  [0] Cancelar")
  
  (initget "1 2 0")
  (setq modeOpt (getkword "\n\nOpcao [1/2/0]: "))
  
  (cond
    ;; Opção 1: Numeração Sequencial
    ((= modeOpt "1")
      (progn
        ;; Mostrar desenhos atuais
        (princ "\n\nDesenhos atuais:")
        (setq maxNum 0)
        (vlax-for lay layouts
          (if (and (/= (vla-get-ModelType lay) :vlax-true)
                   (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
            (vlax-for blk (vla-get-Block lay)
              (if (IsTargetBlock blk)
                (progn
                  (setq blkNum (atoi (GetAttValue blk "DES_NUM")))
                  (if (> blkNum maxNum) (setq maxNum blkNum))
                  (princ (strcat "\n  " (FormatNum blkNum))))))))
        
        (princ (strcat "\n\nMax atual: " (FormatNum maxNum)))
        (setq insertNum (getint "\nNumero do desenho a INSERIR (ex: 3): "))
        
        (if (and insertNum (> insertNum 0) (<= insertNum (1+ maxNum)))
          (progn
            ;; 1. Renumerar desenhos >= insertNum (de trás para frente)
            ;; Na numeração sequencial, limpar PFIX de todos os desenhos
            (princ "\nA renumerar desenhos existentes (limpando PFIX)...")
            (setq countRenumbered 0)
            (setq i maxNum)
            (while (>= i insertNum)
              (vlax-for lay layouts
                (if (and (/= (vla-get-ModelType lay) :vlax-true)
                         (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                  (vlax-for blk (vla-get-Block lay)
                    (if (IsTargetBlock blk)
                      (if (= (atoi (GetAttValue blk "DES_NUM")) i)
                        (progn
                          (UpdateSingleTag (vla-get-Handle blk) "DES_NUM" (FormatNum (1+ i)))
                          ;; Limpar PFIX na numeração sequencial
                          (UpdateSingleTag (vla-get-Handle blk) "PFIX" "")
                          (UpdateTabName (vla-get-Handle blk))
                          (setq countRenumbered (1+ countRenumbered))))))))
              (setq i (1- i)))
            
            ;; 2. Pedir dados do novo desenho
            (princ "\n\n--- DADOS DO NOVO DESENHO ---")
            (setq newPfix (getstring T "\nPFIX (ex: DIM, ARM, FUN) [Enter=vazio]: "))
            (setq newTipo (getstring T "\nTIPO: "))
            (setq newElemento (getstring T "\nELEMENTO: "))
            (setq newTitulo (getstring T "\nTITULO: "))
            
            ;; 3. Criar novo layout
            (setq layName (strcat "Desenho_" (FormatNum insertNum)))
            (princ (strcat "\nA criar " layName "..."))
            (setvar "CMDECHO" 0)
            (command "_.LAYOUT" "_Copy" "TEMPLATE" layName)
            (setvar "CMDECHO" 1)
            (setvar "CTAB" layName)
            
            ;; 4. Preencher atributos no novo layout
            (setq paperSpace (vla-get-PaperSpace doc))
            (vlax-for blk paperSpace
              (if (IsTargetBlock blk)
                (progn
                  (setq newHandle (vla-get-Handle blk))
                  ;; Dados do projeto (copiados)
                  (if projNum (UpdateSingleTag newHandle "PROJ_NUM" projNum))
                  (if projNome (UpdateSingleTag newHandle "PROJ_NOME" projNome))
                  (if cliente (UpdateSingleTag newHandle "CLIENTE" cliente))
                  (if obra (UpdateSingleTag newHandle "OBRA" obra))
                  (if localizacao (UpdateSingleTag newHandle "LOCALIZACAO" localizacao))
                  (if especialidade (UpdateSingleTag newHandle "ESPECIALIDADE" especialidade))
                  (if projetou (UpdateSingleTag newHandle "PROJETOU" projetou))
                  ;; Fase e Emissão (copiados)
                  (if fase (UpdateSingleTag newHandle "FASE" fase))
                  (if fasePfix (UpdateSingleTag newHandle "FASE_PFIX" fasePfix))
                  (if emissao (UpdateSingleTag newHandle "EMISSAO" emissao))
                  (if dataEmissao (UpdateSingleTag newHandle "DATA" dataEmissao))
                  ;; DES_NUM
                  (UpdateSingleTag newHandle "DES_NUM" (FormatNum insertNum))
                  ;; Novos dados
                  (if (/= newPfix "") (UpdateSingleTag newHandle "PFIX" newPfix))
                  (if (/= newTipo "") (UpdateSingleTag newHandle "TIPO" newTipo))
                  (if (/= newElemento "") (UpdateSingleTag newHandle "ELEMENTO" newElemento))
                  (if (/= newTitulo "") (UpdateSingleTag newHandle "TITULO" newTitulo))
                  ;; Atualizar nome do tab
                  (UpdateTabName newHandle))))
            
            ;; 5. Ordenar por DES_NUM (sequencial)
            (princ "\nA ordenar desenhos...")
            (setq layoutList '())
            (vlax-for lay layouts
              (if (and (/= (vla-get-ModelType lay) :vlax-true)
                       (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                (vlax-for blk (vla-get-Block lay)
                  (if (IsTargetBlock blk)
                    (setq layoutList (cons (list lay (atoi (GetAttValue blk "DES_NUM"))) layoutList))))))
            (setq layoutList (vl-sort layoutList '(lambda (a b) (< (cadr a) (cadr b)))))
            (if (not (vl-catch-all-error-p (setq templateLay (vla-Item layouts "TEMPLATE"))))
              (vla-put-TabOrder templateLay 1))
            (setq i 2)
            (foreach item layoutList
              (setq layObj (car item))
              (vl-catch-all-apply 'vla-put-TabOrder (list layObj i))
              (setq i (1+ i)))
            
            (vla-Regen doc acActiveViewport)
            (WriteLog (strcat "INSERIR SEQ: Desenho " (FormatNum insertNum) " inserido, " (itoa countRenumbered) " renumerados"))
            (alert (strcat "Sucesso!\n\nDesenho " (FormatNum insertNum) " inserido.\n" (itoa countRenumbered) " desenhos renumerados.\nLayouts ordenados.")))
          (princ "\nNumero invalido."))))
    
    ;; Opção 2: Numeração por PFIX
    ((= modeOpt "2")
      (progn
        ;; Recolher lista de PFIX existentes
        (setq pfixList '())
        (vlax-for lay layouts
          (if (and (/= (vla-get-ModelType lay) :vlax-true)
                   (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
            (vlax-for blk (vla-get-Block lay)
              (if (IsTargetBlock blk)
                (progn
                  (setq blkPfix (GetAttValue blk "PFIX"))
                  (if (or (null blkPfix) (= blkPfix "") (= blkPfix " "))
                    (setq blkPfix "_SEM_PFIX_"))
                  (if (not (member blkPfix pfixList))
                    (setq pfixList (append pfixList (list blkPfix)))))))))
        
        (if (null pfixList)
          (alert "Nenhum PFIX encontrado!")
          (progn
            ;; Mostrar PFIX disponíveis
            (princ "\n\nPrefixos disponiveis:")
            (setq i 1)
            (foreach pf pfixList
              (princ (strcat "\n  " (itoa i) ". " pf))
              (setq i (1+ i)))
            
            (setq i (getint "\nEscolha o PFIX (numero): "))
            (if (and i (> i 0) (<= i (length pfixList)))
              (progn
                (setq selectedPfix (nth (1- i) pfixList))
                (if (= selectedPfix "_SEM_PFIX_") (setq targetPfix "") (setq targetPfix selectedPfix))
                
                ;; Mostrar desenhos deste PFIX
                (princ (strcat "\n\nDesenhos com PFIX=" selectedPfix ":"))
                (setq maxNum 0)
                (vlax-for lay layouts
                  (if (and (/= (vla-get-ModelType lay) :vlax-true)
                           (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                    (vlax-for blk (vla-get-Block lay)
                      (if (IsTargetBlock blk)
                        (progn
                          (setq blkPfix (GetAttValue blk "PFIX"))
                          (if (or (null blkPfix) (= blkPfix "") (= blkPfix " "))
                            (setq blkPfix "_SEM_PFIX_"))
                          (if (= blkPfix selectedPfix)
                            (progn
                              (setq blkNum (atoi (GetAttValue blk "DES_NUM")))
                              (if (> blkNum maxNum) (setq maxNum blkNum))
                              (princ (strcat "\n  " (FormatNum blkNum))))))))))
                
                (princ (strcat "\n\nMax atual em " selectedPfix ": " (FormatNum maxNum)))
                (setq insertNum (getint "\nNumero do desenho a INSERIR: "))
                
                (if (and insertNum (> insertNum 0) (<= insertNum (1+ maxNum)))
                  (progn
                    ;; 1. Renumerar desenhos >= insertNum DENTRO deste PFIX (de trás para frente)
                    (princ "\nA renumerar desenhos existentes...")
                    (setq countRenumbered 0)
                    (setq i maxNum)
                    (while (>= i insertNum)
                      (vlax-for lay layouts
                        (if (and (/= (vla-get-ModelType lay) :vlax-true)
                                 (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                          (vlax-for blk (vla-get-Block lay)
                            (if (IsTargetBlock blk)
                              (progn
                                (setq blkPfix (GetAttValue blk "PFIX"))
                                (if (or (null blkPfix) (= blkPfix "") (= blkPfix " "))
                                  (setq blkPfix "_SEM_PFIX_"))
                                (if (and (= blkPfix selectedPfix)
                                         (= (atoi (GetAttValue blk "DES_NUM")) i))
                                  (progn
                                    (UpdateSingleTag (vla-get-Handle blk) "DES_NUM" (FormatNum (1+ i)))
                                    (UpdateTabName (vla-get-Handle blk))
                                    (setq countRenumbered (1+ countRenumbered)))))))))
                      (setq i (1- i)))
                    
                    ;; 2. Pedir dados do novo desenho (PFIX já definido)
                    (princ "\n\n--- DADOS DO NOVO DESENHO ---")
                    (princ (strcat "\nPFIX: " targetPfix " (ja definido)"))
                    (setq newTipo (getstring T "\nTIPO: "))
                    (setq newElemento (getstring T "\nELEMENTO: "))
                    (setq newTitulo (getstring T "\nTITULO: "))
                    
                    ;; 3. Criar novo layout
                    (setq layName (strcat "Desenho_" selectedPfix "_" (FormatNum insertNum)))
                    (princ (strcat "\nA criar " layName "..."))
                    (setvar "CMDECHO" 0)
                    (command "_.LAYOUT" "_Copy" "TEMPLATE" layName)
                    (setvar "CMDECHO" 1)
                    (setvar "CTAB" layName)
                    
                    ;; 4. Preencher atributos no novo layout
                    (setq paperSpace (vla-get-PaperSpace doc))
                    (vlax-for blk paperSpace
                      (if (IsTargetBlock blk)
                        (progn
                          (setq newHandle (vla-get-Handle blk))
                          ;; Dados do projeto (copiados)
                          (if projNum (UpdateSingleTag newHandle "PROJ_NUM" projNum))
                          (if projNome (UpdateSingleTag newHandle "PROJ_NOME" projNome))
                          (if cliente (UpdateSingleTag newHandle "CLIENTE" cliente))
                          (if obra (UpdateSingleTag newHandle "OBRA" obra))
                          (if localizacao (UpdateSingleTag newHandle "LOCALIZACAO" localizacao))
                          (if especialidade (UpdateSingleTag newHandle "ESPECIALIDADE" especialidade))
                          (if projetou (UpdateSingleTag newHandle "PROJETOU" projetou))
                          ;; Fase e Emissão (copiados)
                          (if fase (UpdateSingleTag newHandle "FASE" fase))
                          (if fasePfix (UpdateSingleTag newHandle "FASE_PFIX" fasePfix))
                          (if emissao (UpdateSingleTag newHandle "EMISSAO" emissao))
                          (if dataEmissao (UpdateSingleTag newHandle "DATA" dataEmissao))
                          ;; DES_NUM e PFIX
                          (UpdateSingleTag newHandle "DES_NUM" (FormatNum insertNum))
                          (UpdateSingleTag newHandle "PFIX" targetPfix)
                          ;; Novos dados
                          (if (/= newTipo "") (UpdateSingleTag newHandle "TIPO" newTipo))
                          (if (/= newElemento "") (UpdateSingleTag newHandle "ELEMENTO" newElemento))
                          (if (/= newTitulo "") (UpdateSingleTag newHandle "TITULO" newTitulo))
                          ;; Atualizar nome do tab
                          (UpdateTabName newHandle))))
                    
                    ;; 5. Ordenar por PFIX (mantém ordem existente)
                    (princ "\nA ordenar desenhos por PFIX...")
                    (setq layoutList '())
                    (vlax-for lay layouts
                      (if (and (/= (vla-get-ModelType lay) :vlax-true)
                               (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                        (vlax-for blk (vla-get-Block lay)
                          (if (IsTargetBlock blk)
                            (progn
                              (setq blkPfix (GetAttValue blk "PFIX"))
                              (setq valNum (atoi (GetAttValue blk "DES_NUM")))
                              (if (or (null blkPfix) (= blkPfix "") (= blkPfix " "))
                                (setq blkPfix "_SEM_PFIX_"))
                              (setq layoutList (cons (list lay blkPfix valNum) layoutList)))))))
                    ;; Ordenar: por posição do PFIX na lista, depois por DES_NUM
                    (setq layoutList (vl-sort layoutList
                      '(lambda (a b)
                        (if (= (cadr a) (cadr b))
                          (< (caddr a) (caddr b))
                          (< (vl-position (cadr a) pfixList) (vl-position (cadr b) pfixList))))))
                    (if (not (vl-catch-all-error-p (setq templateLay (vla-Item layouts "TEMPLATE"))))
                      (vla-put-TabOrder templateLay 1))
                    (setq i 2)
                    (foreach item layoutList
                      (setq layObj (car item))
                      (vl-catch-all-apply 'vla-put-TabOrder (list layObj i))
                      (setq i (1+ i)))
                    
                    (vla-Regen doc acActiveViewport)
                    (WriteLog (strcat "INSERIR PFIX: " selectedPfix " " (FormatNum insertNum) " inserido, " (itoa countRenumbered) " renumerados"))
                    (alert (strcat "Sucesso!\n\nDesenho " selectedPfix "-" (FormatNum insertNum) " inserido.\n" (itoa countRenumbered) " desenhos renumerados.\nLayouts ordenados por PFIX.")))
                  (princ "\nNumero invalido.")))
              (princ "\nOpcao invalida."))))))
    
    ;; Cancelar
    (T (princ "\nCancelado.")))
  (princ)
)

;; Ordenar Desenhos
(defun OrdenarTabs ( / doc layouts templateLay layoutList sortMode i item layObj blkInfo valPfix valNum
                       hasDuplicates desNumList pfixList pfixOrder newOrder orderStr idx)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq layouts (vla-get-Layouts doc))
  
  (princ "\n\n=== ORDENAR DESENHOS ===")
  (princ "\n\n  [1] Por Numero de Desenho (DES_NUM)")
  (princ "\n  [2] Por Prefixo (PFIX)")
  (princ "\n  [0] Cancelar")
  
  (initget "1 2 0")
  (setq sortMode (getkword "\n\nOpcao [1/2/0]: "))
  
  (cond
    ;; Opção 1: Por Número de Desenho
    ((= sortMode "1")
      (progn
        ;; Verificar se existem DES_NUM duplicados (numeração por PFIX)
        (setq desNumList '())
        (setq hasDuplicates nil)
        (vlax-for lay layouts
          (if (and (/= (vla-get-ModelType lay) :vlax-true)
                   (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
            (vlax-for blk (vla-get-Block lay)
              (if (IsTargetBlock blk)
                (progn
                  (setq valNum (GetAttValue blk "DES_NUM"))
                  (if (member valNum desNumList)
                    (setq hasDuplicates T)
                    (setq desNumList (cons valNum desNumList))))))))
        
        (if hasDuplicates
          ;; Existem duplicados - avisar utilizador
          (alert "AVISO: Existem DES_NUM duplicados!\n\nIsso indica numeração por PFIX.\nPara ordenar por número, primeiro use\n'Numerar Desenhos > Sequencialmente'.")
          ;; Não há duplicados - ordenar por DES_NUM
          (progn
            (princ "\nA ler atributos...")
            (setq layoutList '())
            (vlax-for lay layouts
              (if (and (/= (vla-get-ModelType lay) :vlax-true)
                       (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
                (vlax-for blk (vla-get-Block lay)
                  (if (IsTargetBlock blk)
                    (setq layoutList (cons (list lay (atoi (GetAttValue blk "DES_NUM"))) layoutList))))))
            
            ;; Ordenar por DES_NUM
            (setq layoutList (vl-sort layoutList '(lambda (a b) (< (cadr a) (cadr b)))))
            
            ;; Aplicar ordem
            (princ "\nA reordenar...")
            (if (not (vl-catch-all-error-p (setq templateLay (vla-Item layouts "TEMPLATE"))))
              (vla-put-TabOrder templateLay 1))
            
            (setq i 2)
            (foreach item layoutList
              (setq layObj (car item))
              (vl-catch-all-apply 'vla-put-TabOrder (list layObj i))
              (setq i (1+ i)))
            
            (vla-Regen doc acActiveViewport)
            (WriteLog (strcat "ORDENAR DES_NUM: " (itoa (length layoutList)) " layouts reordenados"))
            (alert (strcat "Ordenados " (itoa (length layoutList)) " desenhos por DES_NUM!"))))))
    
    ;; Opção 2: Por Prefixo
    ((= sortMode "2")
      (progn
        ;; Recolher lista de PFIX existentes (ordem atual)
        (setq pfixList '())
        (setq layoutList '())
        (vlax-for lay layouts
          (if (and (/= (vla-get-ModelType lay) :vlax-true)
                   (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
            (vlax-for blk (vla-get-Block lay)
              (if (IsTargetBlock blk)
                (progn
                  (setq valPfix (GetAttValue blk "PFIX"))
                  (setq valNum (atoi (GetAttValue blk "DES_NUM")))
                  (if (or (null valPfix) (= valPfix "") (= valPfix " "))
                    (setq valPfix "_SEM_PFIX_"))
                  ;; Adicionar PFIX à lista se ainda não existir
                  (if (not (member valPfix pfixList))
                    (setq pfixList (append pfixList (list valPfix))))
                  ;; Guardar layout com PFIX e DES_NUM
                  (setq layoutList (cons (list lay valPfix valNum) layoutList)))))))
        
        ;; Mostrar PFIX na ordem atual
        (princ "\n\nPrefixos encontrados (ordem atual):")
        (setq idx 1)
        (foreach pf pfixList
          (princ (strcat "\n  " (itoa idx) ". " pf))
          (setq idx (1+ idx)))
        
        ;; Perguntar se quer alterar ordem
        (initget "Sim Nao")
        (if (= (getkword "\n\nAlterar ordem dos prefixos? [Sim/Nao] <Nao>: ") "Sim")
          (progn
            (princ "\nDigite a nova ordem separada por virgulas.")
            (princ (strcat "\nExemplo: " (car pfixList) "," (if (cadr pfixList) (cadr pfixList) "XXX")))
            (setq orderStr (getstring T "\nNova ordem: "))
            (if (and orderStr (/= orderStr ""))
              (progn
                (setq newOrder (StrSplit orderStr ","))
                ;; Validar e limpar
                (setq pfixOrder '())
                (foreach pf newOrder
                  (setq pf (vl-string-trim " " pf))
                  (if (member pf pfixList)
                    (if (not (member pf pfixOrder))
                      (setq pfixOrder (append pfixOrder (list pf))))))
                ;; Adicionar PFIX que não foram mencionados no final
                (foreach pf pfixList
                  (if (not (member pf pfixOrder))
                    (setq pfixOrder (append pfixOrder (list pf)))))
                (setq pfixList pfixOrder))))
          ;; Manter ordem atual
          (setq pfixOrder pfixList))
        
        ;; Ordenar layoutList: primeiro por PFIX (ordem definida), depois por DES_NUM
        (setq layoutList (vl-sort layoutList
          '(lambda (a b)
            (if (= (cadr a) (cadr b))
              ;; Mesmo PFIX: ordenar por DES_NUM
              (< (caddr a) (caddr b))
              ;; PFIX diferente: ordenar pela posição na lista pfixList
              (< (vl-position (cadr a) pfixList) (vl-position (cadr b) pfixList))))))
        
        ;; Aplicar ordem
        (princ "\nA reordenar...")
        (if (not (vl-catch-all-error-p (setq templateLay (vla-Item layouts "TEMPLATE"))))
          (vla-put-TabOrder templateLay 1))
        
        (setq i 2)
        (foreach item layoutList
          (setq layObj (car item))
          (vl-catch-all-apply 'vla-put-TabOrder (list layObj i))
          (setq i (1+ i)))
        
        (vla-Regen doc acActiveViewport)
        ;; Mostrar ordem final
        (setq orderStr "")
        (foreach pf pfixList
          (setq orderStr (strcat orderStr (if (= orderStr "") "" ", ") pf)))
        (WriteLog (strcat "ORDENAR PFIX: " (itoa (length layoutList)) " layouts - Ordem: " orderStr))
        (alert (strcat "Ordenados " (itoa (length layoutList)) " desenhos!\n\nOrdem PFIX:\n" orderStr))))
    
    ;; Cancelar
    (T (princ "\nCancelado.")))
  (princ)
)

;; Numerar Desenhos
(defun NumerarDesenhos ( / doc drawList count numSeq modeOpt pfixMap currentPfix blkPfix)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  
  (princ "\n\n=== NUMERAR DESENHOS ===")
  (princ "\nRenumera DES_NUM pela ordem atual dos tabs.")
  (princ "\n\n  [1] Sequencialmente (001, 002, 003...)")
  (princ "\n  [2] Por PFIX (cada PFIX começa em 001)")
  (princ "\n  [0] Cancelar")
  
  (initget "1 2 0")
  (setq modeOpt (getkword "\n\nOpcao [1/2/0]: "))
  
  (cond
    ;; Opção 1: Sequencialmente
    ((= modeOpt "1")
      (progn
        (princ "\nA numerar sequencialmente...")
        (setq count 0 numSeq 1)
        (setq drawList (GetLayoutsRaw doc))
        
        (foreach lay drawList
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                (UpdateSingleTag (vla-get-Handle blk) "DES_NUM" (FormatNum numSeq))
                (UpdateTabName (vla-get-Handle blk))
                (setq count (1+ count))
                (setq numSeq (1+ numSeq))))))
        
        (vla-Regen doc acActiveViewport)
        (WriteLog (strcat "NUMERAR SEQ: " (itoa count) " desenhos renumerados"))
        (alert (strcat "Numerados " (itoa count) " desenhos sequencialmente."))))
    
    ;; Opção 2: Por PFIX
    ((= modeOpt "2")
      (progn
        (princ "\nA numerar por PFIX...")
        (setq count 0)
        (setq pfixMap '())  ;; Mapa de contadores por PFIX: (("DIM" . 3) ("ARM" . 2) ...)
        (setq drawList (GetLayoutsRaw doc))
        
        (foreach lay drawList
          (vlax-for blk (vla-get-Block lay)
            (if (IsTargetBlock blk)
              (progn
                ;; Obter PFIX do bloco
                (setq blkPfix (GetAttValue blk "PFIX"))
                (if (or (null blkPfix) (= blkPfix "") (= blkPfix " "))
                  (setq blkPfix "_SEM_PFIX_"))
                
                ;; Obter contador atual para este PFIX ou iniciar em 0
                (if (assoc blkPfix pfixMap)
                  (setq numSeq (1+ (cdr (assoc blkPfix pfixMap))))
                  (setq numSeq 1))
                
                ;; Atualizar mapa
                (if (assoc blkPfix pfixMap)
                  (setq pfixMap (subst (cons blkPfix numSeq) (assoc blkPfix pfixMap) pfixMap))
                  (setq pfixMap (cons (cons blkPfix numSeq) pfixMap)))
                
                ;; Aplicar numeração
                (UpdateSingleTag (vla-get-Handle blk) "DES_NUM" (FormatNum numSeq))
                (UpdateTabName (vla-get-Handle blk))
                (setq count (1+ count))))))
        
        (vla-Regen doc acActiveViewport)
        ;; Mostrar resumo por PFIX
        (setq pfixMsg "")
        (foreach item pfixMap
          (setq pfixMsg (strcat pfixMsg "\n  " (car item) ": " (itoa (cdr item)) " desenhos")))
        (WriteLog (strcat "NUMERAR PFIX: " (itoa count) " desenhos renumerados"))
        (alert (strcat "Numerados " (itoa count) " desenhos por PFIX:" pfixMsg))))
    
    ;; Cancelar
    (T (princ "\nCancelado.")))
  (princ)
)

;; Gerar Layouts a partir do Template
(defun GerarLayoutsTemplate ( / doc layouts startNum endNum layName count paperSpace totalGerados
                                ;; Dados do projeto (copiados do primeiro desenho)
                                projNum projNome cliente obra localizacao especialidade projetou
                                fase fasePfix emissao dataEmissao
                                ;; Opcoes do user
                                useDadosProjeto useTipo useElemento usePfix
                                newTipo newElemento newPfix
                                ;; Loop
                                continuar i newHandle)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq layouts (vla-get-Layouts doc))
  (setq totalGerados 0)
  
  (if (not (catch-apply 'vla-Item (list layouts "TEMPLATE")))
    (progn (alert "ERRO: Layout 'TEMPLATE' não existe.") (exit)))
  
  ;; Recolher dados do projeto do primeiro desenho existente
  (setq projNum nil)
  (vlax-for lay layouts
    (if (and (not projNum)
             (/= (vla-get-ModelType lay) :vlax-true)
             (/= (strcase (vla-get-Name lay)) "TEMPLATE"))
      (vlax-for blk (vla-get-Block lay)
        (if (and (not projNum) (IsTargetBlock blk))
          (progn
            (setq projNum (GetAttValue blk "PROJ_NUM"))
            (setq projNome (GetAttValue blk "PROJ_NOME"))
            (setq cliente (GetAttValue blk "CLIENTE"))
            (setq obra (GetAttValue blk "OBRA"))
            (setq localizacao (GetAttValue blk "LOCALIZACAO"))
            (setq especialidade (GetAttValue blk "ESPECIALIDADE"))
            (setq projetou (GetAttValue blk "PROJETOU"))
            (setq fase (GetAttValue blk "FASE"))
            (setq fasePfix (GetAttValue blk "FASE_PFIX"))
            (setq emissao (GetAttValue blk "EMISSAO"))
            (setq dataEmissao (GetAttValue blk "DATA")))))))
  
  (princ "\n\n=== GERAR NOVOS DESENHOS ===")
  
  ;; Loop principal
  (setq continuar T)
  (while continuar
    
    ;; 1. Perguntar numeros a gerar
    (princ "\n\n--- NUMEROS DOS DESENHOS ---")
    (setq startNum (getint "\nNumero do Primeiro Desenho (ex: 1): "))
    (setq endNum (getint "\nNumero do Ultimo Desenho (ex: 5): "))
    
    (if (and startNum endNum (> endNum 0) (>= endNum startNum))
      (progn
        ;; 2. Preencher com Dados do Projeto?
        (initget "Sim Nao")
        (setq useDadosProjeto (getkword "\nPreencher com Dados do Projeto, Fase e Emissao? [Sim/Nao] <Sim>: "))
        (if (null useDadosProjeto) (setq useDadosProjeto "Sim"))
        
        ;; 3. Definir TIPO?
        (initget "Sim Nao")
        (setq useTipo (getkword "\nDefinir TIPO para estes desenhos? [Sim/Nao] <Nao>: "))
        (if (= useTipo "Sim")
          (setq newTipo (getstring T "\nTIPO: "))
          (setq newTipo nil))
        
        ;; 4. Definir ELEMENTO?
        (initget "Sim Nao")
        (setq useElemento (getkword "\nDefinir ELEMENTO para estes desenhos? [Sim/Nao] <Nao>: "))
        (if (= useElemento "Sim")
          (setq newElemento (getstring T "\nELEMENTO: "))
          (setq newElemento nil))
        
        ;; 5. Definir PFIX?
        (initget "Sim Nao")
        (setq usePfix (getkword "\nDefinir PFIX para estes desenhos? [Sim/Nao] <Nao>: "))
        (if (= usePfix "Sim")
          (setq newPfix (getstring T "\nPFIX (ex: DIM, ARM, FUN): "))
          (setq newPfix nil))
        
        ;; Gerar layouts
        (princ "\nA gerar desenhos...")
        (setq count 0)
        (setq i startNum)
        (while (<= i endNum)
          (setq layName (strcat "Desenho_" (FormatNum i)))
          (if (not (catch-apply 'vla-Item (list layouts layName)))
            (progn
              (princ (strcat "\n  Criando " layName "..."))
              (setvar "CMDECHO" 0)
              (command "_.LAYOUT" "_Copy" "TEMPLATE" layName)
              (setvar "CMDECHO" 1)
              (setvar "CTAB" layName)
              
              ;; Preencher atributos no novo layout
              (setq paperSpace (vla-get-PaperSpace doc))
              (vlax-for blk paperSpace
                (if (IsTargetBlock blk)
                  (progn
                    (setq newHandle (vla-get-Handle blk))
                    ;; DES_NUM sempre
                    (UpdateSingleTag newHandle "DES_NUM" (FormatNum i))
                    
                    ;; Dados do projeto (se escolhido)
                    (if (= useDadosProjeto "Sim")
                      (progn
                        (if projNum (UpdateSingleTag newHandle "PROJ_NUM" projNum))
                        (if projNome (UpdateSingleTag newHandle "PROJ_NOME" projNome))
                        (if cliente (UpdateSingleTag newHandle "CLIENTE" cliente))
                        (if obra (UpdateSingleTag newHandle "OBRA" obra))
                        (if localizacao (UpdateSingleTag newHandle "LOCALIZACAO" localizacao))
                        (if especialidade (UpdateSingleTag newHandle "ESPECIALIDADE" especialidade))
                        (if projetou (UpdateSingleTag newHandle "PROJETOU" projetou))
                        (if fase (UpdateSingleTag newHandle "FASE" fase))
                        (if fasePfix (UpdateSingleTag newHandle "FASE_PFIX" fasePfix))
                        (if emissao (UpdateSingleTag newHandle "EMISSAO" emissao))
                        (if dataEmissao (UpdateSingleTag newHandle "DATA" dataEmissao))))
                    
                    ;; TIPO (se definido)
                    (if (and newTipo (/= newTipo ""))
                      (UpdateSingleTag newHandle "TIPO" newTipo))
                    
                    ;; ELEMENTO (se definido)
                    (if (and newElemento (/= newElemento ""))
                      (UpdateSingleTag newHandle "ELEMENTO" newElemento))
                    
                    ;; PFIX (se definido)
                    (if (and newPfix (/= newPfix ""))
                      (UpdateSingleTag newHandle "PFIX" newPfix))
                    
                    ;; Atualizar nome do tab
                    (UpdateTabName newHandle))))
              
              (setq count (1+ count))
              (setq totalGerados (1+ totalGerados)))
            (princ (strcat "\n  Layout " layName " ja existe.")))
          (setq i (1+ i)))
        
        (vla-Regen doc acActiveViewport)
        (princ (strcat "\n\nGerados " (itoa count) " desenhos nesta serie."))
        (WriteLog (strcat "GERAR: " (itoa count) " layouts criados"
                         (if newPfix (strcat " PFIX=" newPfix) "")
                         (if newTipo (strcat " TIPO=" newTipo) ""))))
      (princ "\nParametros invalidos."))
    
    ;; 6. Gerar mais desenhos?
    (initget "Sim Nao")
    (if (/= (getkword "\n\nGerar mais desenhos? [Sim/Nao] <Nao>: ") "Sim")
      (setq continuar nil)))
  
  (alert (strcat "Concluido!\n\nTotal de desenhos gerados: " (itoa totalGerados)))
  (princ)
)

;; Apagar Desenhos
(defun ApagarDesenhos ( / doc drawList optMode targets selectedList confirmMsg count layToDelete i item)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq drawList (GetDrawingList))
  
  (if (null drawList)
    (alert "Nenhum desenho encontrado!")
    (progn
      (princ "\n\n=== APAGAR DESENHOS ===")
      (princ (strcat "\nTotal de desenhos: " (itoa (length drawList))))
      
      (princ "\n\n--- DESENHOS DISPONIVEIS ---")
      (setq i 1)
      (foreach item drawList
        (princ (strcat "\n " (itoa i) ". DES_NUM=" (cadr item) " | " (caddr item)))
        (setq i (1+ i)))
      
      (princ "\n\n-----------------------------------------")
      (princ "\n[T] Apagar TODOS")
      (princ "\n[S] Apagar SELECAO (ex: 1,3,5 ou 2-5)")
      (princ "\n[0] Cancelar")
      (initget "T S 0")
      (setq optMode (getkword "\n\nOpcao [T/S/0]: "))
      
      (cond
        ((= optMode "T")
          (setq selectedList drawList)
          (setq confirmMsg (strcat "ATENÇÃO!\n\nVai apagar TODOS os " (itoa (length drawList)) " desenhos!\n\nTem a certeza?")))
        ((= optMode "S")
          (setq targets (getstring T "\nSelecao: "))
          (if (/= targets "")
            (progn
              (setq selectedList (ParseSelectionToList drawList targets))
              (if selectedList
                (setq confirmMsg (strcat "Vai apagar " (itoa (length selectedList)) " desenho(s).\n\nTem a certeza?"))
                (princ "\nSeleção inválida.")))
            (princ "\nCancelado.")))
        (T (princ "\nCancelado.")))
      
      (if (and selectedList (> (length selectedList) 0))
        (progn
          (initget "Sim Nao")
          (if (= (getkword (strcat "\n" confirmMsg " [Sim/Nao] <Nao>: ")) "Sim")
            (progn
              (princ "\nA apagar layouts...")
              (setq count 0)
              (foreach item selectedList
                (setq layToDelete nil)
                (vlax-for lay (vla-get-Layouts doc)
                  (if (and (not layToDelete)
                           (= (strcase (vla-get-Name lay)) (strcase (caddr item))))
                    (setq layToDelete lay)))
                (if layToDelete
                  (if (not (vl-catch-all-error-p
                             (vl-catch-all-apply 'vla-Delete (list layToDelete))))
                    (progn
                      (setq count (1+ count))
                      (princ (strcat "\n  Apagado: " (caddr item)))
                      (WriteLog (strcat "APAGAR: Layout '" (caddr item) "' eliminado")))
                    (princ (strcat "\n  ERRO ao apagar: " (caddr item))))
                  (princ (strcat "\n  Layout não encontrado: " (caddr item)))))
              (vla-Regen doc acActiveViewport)
              (alert (strcat "Concluído!\n\n" (itoa count) " layout(s) apagado(s).")))
            (princ "\nCancelado."))))))
  (princ)
)

;; ============================================================================
;; SECÇÃO 13: DIAGNÓSTICO
;; ============================================================================

(defun c:JSJDIAG ( / doc found)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq found nil)
  (textscr)
  (princ "\n\n=== DIAGNÓSTICO BLOCO LEGENDA_JSJ_V1 ===\n")
  (vlax-for lay (vla-get-Layouts doc)
    (if (not found)
      (vlax-for blk (vla-get-Block lay)
        (if (and (not found) (IsTargetBlock blk))
          (progn
            (princ (strcat "\nLayout: " (vla-get-Name lay)))
            (princ "\n\nAtributos encontrados:")
            (foreach att (vlax-invoke blk 'GetAttributes)
              (princ (strcat "\n  " (vla-get-TagString att) " = '" (vla-get-TextString att) "'")))
            (setq found T))))))
  (if (not found)
    (princ "\nERRO: Nenhum bloco LEGENDA_JSJ_V1 encontrado!"))
  (princ "\n")
  (princ)
)

;; ============================================================================
;; MENSAGEM DE CARREGAMENTO
;; ============================================================================
(princ "\n========================================")
(princ "\n GESTAO DESENHOS JSJ V42.0")
(princ "\n========================================")
(princ "\n Comandos disponiveis:")
(princ "\n   GESTAODESENHOSJSJ - Menu principal")
(princ "\n   JSJDIAG - Diagnostico de atributos")
(princ "\n========================================")
(princ "\n Novos atributos suportados:")
(princ "\n   PROJ_NUM, PROJ_NOME, FASE_PFIX,")
(princ "\n   EMISSAO, PFIX")
(princ "\n========================================")
(princ "\n Formato TAB:")
(princ "\n   PROJ_NUM-EST-PFIX DES_NUM-EMISSAO-FASE_PFIX-R")
(princ "\n   Ex: 669-EST-DIM 003-E01-PB-C")
(princ "\n========================================")
(princ)