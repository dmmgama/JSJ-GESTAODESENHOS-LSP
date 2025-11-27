;; ============================================================================
;; FERRAMENTA UNIFICADA: GESTAO DESENHOS JSJ (V37 - CSV CONFIGURAVEL)
;; ============================================================================

;; Variável global para o utilizador (persiste durante sessão)
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
      (vla-Update obj)))
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
              (if (and (/= tag "DES_NUM") 
                       (/= tag "FASE") 
                       (/= tag "R") 
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
    (princ "\n          GESTAO DESENHOS JSJ - MENU          ")
    (princ "\n==============================================")
    (princ "\n 1. Modificar Legendas")
    (princ "\n 2. Exportar Lista de Desenhos")
    (princ "\n 3. Importar Lista de Desenhos")
    (princ "\n 4. Gerir Layouts")
    (princ "\n----------------------------------------------")
    (princ "\n 9. Navegar (ver desenho)")
    (princ "\n 0. Sair")
    (princ "\n==============================================")

    (initget "1 2 3 4 9 0")
    (setq opt (getkword "\nEscolha uma opcao [1/2/3/4/9/0]: "))

    (cond
      ((= opt "1") (Menu_ModificarLegendas))
      ((= opt "2") (Menu_Exportar))
      ((= opt "3") (Menu_Importar))
      ((= opt "4") (Menu_GerirLayouts))
      ((= opt "9") (ModoNavegacao))
      ((= opt "0") (setq loop nil))
      ((= opt nil) (setq loop nil)) 
    )
  )
  (graphscr)
  (princ "\nGestao Desenhos JSJ Terminada.")
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
    (princ "\n   4. Definir Utilizador")
    (princ "\n   5. Alterar Fase de Projeto")
    (princ "\n   9. Navegar (ver desenho)")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 5 9 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/5/9/0]: "))
    (cond
      ((= optSub "1") (Menu_EmitirRevisao))
      ((= optSub "2") (Run_GlobalVars_Selective_V29))
      ((= optSub "3") (ProcessManualReview))
      ((= optSub "4") (SetCurrentUser))
      ((= optSub "5") (AlterarFaseProjeto))
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
;; SUBMENU 2: EXPORTAR
;; ============================================================================
(defun Menu_Exportar ( / loopSub optSub)
  (setq loopSub T)
  (while loopSub
    (textscr)
    (princ "\n\n   --- EXPORTAR LISTA DE DESENHOS ---")
    (princ "\n   1. Gerar CSV (Default)")
    (princ "\n   2. Gerar CSV (Configurar Colunas)")
    (princ "\n   3. Exportar JSON")
    (princ "\n   0. Voltar")
    (initget "1 2 3 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/0]: "))
    (cond
      ((= optSub "1") (Run_GenerateCSV_Default))
      ((= optSub "2") (Run_GenerateCSV_Custom))
      ((= optSub "3") (princ "\nEm desenvolvimento."))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
)

;; ============================================================================
;; EXPORTAR CSV - DEFAULT (colunas fixas)
;; ============================================================================
(defun Run_GenerateCSV_Default ( / )
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
              (if (and (not (wcmatch tag "REV_?,DATA_?,DESC_?"))
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
    ;; Default: DWG_SOURCE, TIPO, DES_NUM, TITULO, REVISAO_ATUAL (3 colunas), ID_CAD
    (setq tags '("DWG_SOURCE" "TIPO" "DES_NUM" "TITULO" "REVISAO_ATUAL" "ID_CAD"))
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
      (T (setq value (CleanCSV (GetAttValue blk tag))))
    )
    (setq row (cons value row))
  )
  (reverse row)
)

;; Constroi header CSV
(defun BuildCSVHeader (tags / header)
  (setq header "")
  (foreach tag tags
    (if (= tag "REVISAO_ATUAL")
      (setq header (strcat header (if (/= header "") ";" "") "REVISAO;DATA;DESCRICAO"))
      (setq header (strcat header (if (/= header "") ";" "") tag))
    )
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
    (princ "\n   1. Importar CSV")
    (princ "\n   2. Importar JSON")
    (princ "\n   0. Voltar")
    (initget "1 2 0")
    (setq optSub (getkword "\n   Opcao [1/2/0]: "))
    (cond
      ((= optSub "1") (Run_ImportCSV))
      ((= optSub "2") (ProcessJSONImport))
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
    (princ "\n   3. Numerar por TIPO")
    (princ "\n   4. Numerar SEQUENCIAL")
    (princ "\n   0. Voltar")
    (initget "1 2 3 4 0")
    (setq optSub (getkword "\n   Opcao [1/2/3/4/0]: "))
    (cond
      ((= optSub "1") (Run_GenerateLayouts_FromTemplate_V26))
      ((= optSub "2") (Run_SortLayouts_Engine))
      ((= optSub "3") (AutoNumberByType))
      ((= optSub "4") (AutoNumberSequential))
      ((= optSub "0") (setq loopSub nil))
      ((= optSub nil) (setq loopSub nil))
    )
  )
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
        (if maxRevLetter
          (UpdateSingleTag handle "R" maxRevLetter)
        )
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
(defun Run_ImportCSV ( / doc path defaultName csvFile fileDes line parts valDwgSource valTipo valNum valTit valRev valData valDesc valHandle countUpdates) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq path (getvar "DWGPREFIX")) (setq csvFile (getfiled "Selecione o ficheiro CSV" path "csv" 4)) (if (and csvFile (findfile csvFile)) (progn (setq fileDes (open csvFile "r")) (if fileDes (progn (princ "\nA processar CSV... ") (setq countUpdates 0) (read-line fileDes) (while (setq line (read-line fileDes)) (setq parts (StrSplit line ";")) (if (>= (length parts) 8) (progn (setq valDwgSource (nth 0 parts)) (setq valTipo (nth 1 parts)) (setq valNum (nth 2 parts)) (setq valTit (nth 3 parts)) (setq valRev (nth 4 parts)) (setq valData (nth 5 parts)) (setq valDesc (nth 6 parts)) (setq valHandle (nth 7 parts)) (if (and valHandle (/= valHandle "")) (if (UpdateBlockByHandleAndData valHandle valTipo valNum valTit valRev valData valDesc) (setq countUpdates (1+ countUpdates))))))) (close fileDes) (vla-Regen doc acActiveViewport) (if (> countUpdates 0) (WriteLog (strcat "IMPORTAR CSV: " (itoa countUpdates) " desenhos atualizados"))) (alert (strcat "Concluído!\n" (itoa countUpdates) " desenhos atualizados."))) (alert "Erro ao abrir ficheiro."))) (princ "\nCancelado.")) (princ))
(defun CleanCSV (str) (if (= str nil) (setq str "")) (setq str (vl-string-translate ";" "," str)) (vl-string-trim " \"" str))
(defun StrSplit (str del / pos len lst) (setq len (strlen del)) (while (setq pos (vl-string-search del str)) (setq lst (cons (vl-string-trim " " (substr str 1 pos)) lst) str (substr str (+ 1 pos len)))) (reverse (cons (vl-string-trim " " str) lst)))
(defun UpdateBlockByHandleAndData (handle tipo num tit rev dataStr descStr / ename obj atts revTag dataTag descTag success) (setq success nil) (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle)))) (setq ename (handent handle))) (if (and ename (setq obj (vlax-ename->vla-object ename))) (if (IsTargetBlock obj) (progn (UpdateSingleTag handle "TIPO" tipo) (UpdateSingleTag handle "DES_NUM" num) (UpdateSingleTag handle "TITULO" tit) (if (and rev (/= rev "") (/= rev "-")) (progn (setq revTag (strcat "REV_" rev)) (setq dataTag (strcat "DATA_" rev)) (setq descTag (strcat "DESC_" rev)) (UpdateSingleTag handle revTag rev) (UpdateSingleTag handle dataTag dataStr) (UpdateSingleTag handle descTag descStr) (UpdateAttributeR handle))) (princ ".") (setq success T)))) success)
(defun GetMaxRevision (blk / checkRev finalRev finalDate finalDesc) (setq finalRev "-" finalDate "-" finalDesc "-") (foreach letra '("E" "D" "C" "B" "A") (if (= finalRev "-") (progn (setq checkRev (GetAttValue blk (strcat "REV_" letra))) (if (and (/= checkRev "") (/= checkRev " ")) (progn (setq finalRev checkRev) (setq finalDate (GetAttValue blk (strcat "DATA_" letra))) (setq finalDesc (GetAttValue blk (strcat "DESC_" letra)))))))) (list finalRev finalDate finalDesc))
(defun GetGlobalDefinitions (blkName / doc blocks blkDef atts tag val dataList) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq blocks (vla-get-Blocks doc)) (setq dataList '()) (if (not (vl-catch-all-error-p (setq blkDef (vla-Item blocks blkName)))) (vlax-for obj blkDef (if (and (= (vla-get-ObjectName obj) "AcDbAttributeDefinition") (not (wcmatch (strcase (vla-get-TagString obj)) "DES_NUM,REV_*,DATA_*,DESC_*"))) (progn (setq tag (vla-get-TagString obj)) (setq val (getstring T (strcat "\nValor para '" tag "': "))) (if (/= val "") (setq dataList (cons (cons (strcase tag) val) dataList))))))) dataList)
(defun catch-apply (func params / result) (if (vl-catch-all-error-p (setq result (vl-catch-all-apply func params))) nil result))
(defun ProcessJSONImport ( / jsonFile fileDes line posSep handleVal attList inAttributes tag rawContent cleanContent countUpdates path) (setq path (getvar "DWGPREFIX")) (setq jsonFile (getfiled "Selecione JSON" path "json" 4)) (if (and jsonFile (findfile jsonFile)) (progn (setq fileDes (open jsonFile "r")) (setq handleVal nil attList '() inAttributes nil countUpdates 0) (princ "\nA processar JSON... ") (while (setq line (read-line fileDes)) (setq line (vl-string-trim " \t" line)) (cond ((vl-string-search "\"handle_bloco\":" line) (setq posSep (vl-string-search ":" line)) (if posSep (progn (setq rawContent (substr line (+ posSep 2))) (setq handleVal (vl-string-trim " \"," rawContent)) (setq attList '()) ))) ((vl-string-search "\"atributos\": {" line) (setq inAttributes T)) ((and inAttributes (vl-string-search "}" line)) (setq inAttributes nil) (if (and handleVal attList) (UpdateBlockByHandle handleVal attList)) (setq handleVal nil)) (inAttributes (setq posSep (vl-string-search "\": \"" line)) (if posSep (progn (setq tag (substr line 2 (- posSep 1))) (setq rawContent (substr line (+ posSep 5))) (setq cleanContent (vl-string-trim " \"," rawContent)) (setq cleanContent (StringUnescape cleanContent)) (setq attList (cons (cons (strcase tag) cleanContent) attList))))))) (close fileDes) (vla-Regen (vla-get-ActiveDocument (vlax-get-acad-object)) acActiveViewport) (alert (strcat "Concluido: " (itoa countUpdates)))) (princ "\nCancelado.")))
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
            (initget "1 2")
            (setq field (getkword "\nAtualizar? [1] Tipo / [2] Titulo: "))
            (cond
              ((= field "1")
                (UpdateSingleTag selectedHandle "TIPO" (getstring T "\nNovo TIPO: "))
                (vla-Regen doc acActiveViewport)
                (WriteLog (strcat "MODIFICAR: Des " desNum " - TIPO alterado"))
              )
              ((= field "2")
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
(defun AutoNumberByType ( / doc dataList blk typeVal handleVal tabOrd sortedList curType count i) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (setq dataList '()) (princ "\n\nA analisar...") (vlax-for lay (vla-get-Layouts doc) (if (/= (vla-get-ModelType lay) :vlax-true) (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (progn (setq typeVal (GetAttValue blk "TIPO")) (if (= typeVal "") (setq typeVal "INDEFINIDO")) (setq handleVal (vla-get-Handle blk)) (setq tabOrd (vla-get-TabOrder lay)) (setq dataList (cons (list typeVal tabOrd handleVal) dataList))))))) (setq sortedList (vl-sort dataList '(lambda (a b) (if (= (strcase (car a)) (strcase (car b))) (< (cadr a) (cadr b)) (< (strcase (car a)) (strcase (car b))))))) (setq curType "" count 0 i 0) (foreach item sortedList (if (/= (strcase (car item)) curType) (progn (setq curType (strcase (car item))) (setq count 1)) (setq count (1+ count))) (UpdateSingleTag (caddr item) "DES_NUM" (FormatNum count)) (setq i (1+ i))) (vla-Regen doc acActiveViewport) (alert (strcat "Concluído: " (itoa i))))
(defun AutoNumberSequential ( / doc sortedLayouts count i) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (initget "Sim Nao") (if (= (getkword "\nNumerar sequencialmente? [Sim/Nao] <Nao>: ") "Sim") (progn (setq sortedLayouts (GetLayoutsRaw doc)) (setq sortedLayouts (vl-sort sortedLayouts '(lambda (a b) (< (vla-get-TabOrder a) (vla-get-TabOrder b))))) (setq count 1 i 0) (foreach lay sortedLayouts (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (progn (UpdateSingleTag (vla-get-Handle blk) "DES_NUM" (FormatNum count)) (setq count (1+ count)) (setq i (1+ i)))))) (vla-Regen doc acActiveViewport) (alert (strcat "Concluído: " (itoa i))))))
(defun ReleaseObject (obj) (if (and obj (not (vlax-object-released-p obj))) (vlax-release-object obj)))
(defun IsTargetBlock (blk) (and (= (vla-get-ObjectName blk) "AcDbBlockReference") (= (strcase (vla-get-EffectiveName blk)) "LEGENDA_JSJ_V1")))
(defun GetAttValue (blk tag / atts val) (setq atts (vlax-invoke blk 'GetAttributes) val "") (foreach att atts (if (= (strcase (vla-get-TagString att)) (strcase tag)) (setq val (vla-get-TextString att)))) val)
(defun UpdateSingleTag (handle tag val / ename obj atts) (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle)))) (setq ename (handent handle))) (if (and ename (setq obj (vlax-ename->vla-object ename))) (progn (setq atts (vlax-invoke obj 'GetAttributes)) (foreach att atts (if (= (strcase (vla-get-TagString att)) (strcase tag)) (vla-put-TextString att val))) (vla-Update obj))))
(defun UpdateBlockByHandle (handle pairList / ename obj atts tagVal foundVal) (if (not (vl-catch-all-error-p (vl-catch-all-apply 'handent (list handle)))) (setq ename (handent handle))) (if (and ename (setq obj (vlax-ename->vla-object ename))) (if (and (= (vla-get-ObjectName obj) "AcDbBlockReference") (= (vla-get-HasAttributes obj) :vlax-true)) (foreach att (vlax-invoke obj 'GetAttributes) (setq tagVal (strcase (vla-get-TagString att)) foundVal (cdr (assoc tagVal pairList))) (if foundVal (vla-put-TextString att foundVal))))))
(defun ApplyGlobalValue (targetTag targetVal / doc) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object))) (vlax-for lay (vla-get-Layouts doc) (if (/= (vla-get-ModelType lay) :vlax-true) (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (foreach att (vlax-invoke blk 'GetAttributes) (if (= (strcase (vla-get-TagString att)) targetTag) (vla-put-TextString att targetVal))))))) (vla-Regen doc acActiveViewport))
(defun GetDrawingList ( / doc listOut atts desNum tipo name) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) listOut '()) (vlax-for lay (vla-get-Layouts doc) (setq name (strcase (vla-get-Name lay))) (if (and (/= (vla-get-ModelType lay) :vlax-true) (/= name "TEMPLATE")) (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (progn (setq desNum "0" tipo "ND") (foreach att (vlax-invoke blk 'GetAttributes) (if (= (strcase (vla-get-TagString att)) "DES_NUM") (setq desNum (vla-get-TextString att))) (if (= (strcase (vla-get-TagString att)) "TIPO") (setq tipo (vla-get-TextString att)))) (setq listOut (cons (list (vla-get-Handle blk) desNum (vla-get-Name lay) tipo) listOut))))))) (setq listOut (vl-sort listOut '(lambda (a b) (< (atoi (cadr a)) (atoi (cadr b)))))) listOut)
(defun GetExampleTags ( / doc tagList found atts tag) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) tagList '() found nil) (vlax-for lay (vla-get-Layouts doc) (if (not found) (vlax-for blk (vla-get-Block lay) (if (IsTargetBlock blk) (progn (foreach att (vlax-invoke blk 'GetAttributes) (setq tag (strcase (vla-get-TagString att))) (if (and (/= tag "DES_NUM") (/= tag "FASE") (/= tag "R") (not (wcmatch tag "REV_?,DATA_?,DESC_?"))) (setq tagList (cons tag tagList)))) (setq found T)))))) (vl-sort tagList '<))
(defun FormatNum (n) (if (< n 10) (strcat "0" (itoa n)) (itoa n)))
(defun EscapeJSON (str / i char result len) (setq result "" len (strlen str) i 1) (while (<= i len) (setq char (substr str i 1)) (cond ((= char "\\") (setq result (strcat result "\\\\"))) ((= char "\"") (setq result (strcat result "\\\""))) (t (setq result (strcat result char)))) (setq i (1+ i))) result)
(defun StringUnescape (str / result i char nextChar len) (setq result "" len (strlen str) i 1) (while (<= i len) (setq char (substr str i 1)) (if (and (= char "\\") (< i len)) (progn (setq nextChar (substr str (1+ i) 1)) (cond ((= nextChar "\\") (setq result (strcat result "\\"))) ((= nextChar "\"") (setq result (strcat result "\""))) (t (setq result (strcat result char)))) (setq i (1+ i))) (setq result (strcat result char))) (setq i (1+ i))) result)