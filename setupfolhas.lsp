(defun c:SETUPFOLHAS (/ *error* doc sel i obj effName dynProps prop foundSize userSize 
                       mediaMap mediaName minPt maxPt layout plotSet)
  (vl-load-com)

  ;; --- CONFIGURAÇÕES ---
  (setq targetBlockName "JSJ-Esquadrias")
  (setq targetPlotter "DWG To PDF.pc3")
  (setq targetCTB "PRETO-1A7-CINZENTO.ctb")
  
  ;; Mapeamento: O que tu escolhes -> Nome interno da folha no AutoCAD
  ;; Verifica se os teus nomes ISO full bleed correspondem a estes.
  (setq mediaMap (list
    '("A0" . "ISO_full_bleed_A0_(841.00_x_1189.00_MM)")
    '("A1" . "ISO_full_bleed_A1_(841.00_x_594.00_MM)")
    '("A2" . "ISO_full_bleed_A2_(594.00_x_420.00_MM)")
    '("A3" . "ISO_full_bleed_A3_(420.00_x_297.00_MM)")
  ))
  ;; ---------------------

  (defun *error* (msg)
    (if (and msg (not (wcmatch (strcase msg) "*BREAK*,*CANCEL*,*EXIT*")))
      (princ (strcat "\nErro: " msg))
    )
    (vla-EndUndoMark (vla-get-ActiveDocument (vlax-get-acad-object)))
    (princ)
  )

  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (vla-StartUndoMark doc)

  ;; 1. Pedir o Tamanho Desejado
  (initget "A0 A1 A2 A3")
  (setq userSize (getkword "\nEscolha o formato da folha [A0/A1/A2/A3]: "))
  (if (not userSize) (setq userSize "A1")) ; Default para A1 se der Enter
  
  ;; Obter o nome técnico da folha (Canonical Media Name)
  (setq mediaName (cdr (assoc userSize mediaMap)))

  (princ (strcat "\nSelecione os blocos '" targetBlockName "' para configurar..."))
  
  ;; 2. Selecionar Blocos
  (if (setq sel (ssget '((0 . "INSERT"))))
    (progn
      (repeat (setq i (sslength sel))
        (setq obj (vlax-ename->vla-object (ssname sel (setq i (1- i)))))
        
        ;; Verificar o nome efetivo (para blocos dinâmicos)
        (setq effName (vla-get-EffectiveName obj))
        
        (if (wcmatch (strcase effName) (strcase targetBlockName))
          (progn
            (princ (strcat "\nA processar layout: " (vla-get-Layout obj) "..."))
            
            ;; --- PASSO A: MUDAR TAMANHO DO BLOCO ---
            (setq dynProps (vla-GetDynamicBlockProperties obj))
            (setq foundSize nil)
            
            ;; Tenta encontrar a propriedade que aceita "A1", "A0", etc.
            (vlax-for prop dynProps
              (if (eq (vla-get-ReadOnly prop) :vlax-false)
                (progn
                  ;; Tenta definir o valor. Se falhar, ignora (catch-all-apply)
                  (if (not (vl-catch-all-error-p 
                             (vl-catch-all-apply 'vla-put-Value (list prop userSize))))
                    (setq foundSize T)
                  )
                )
              )
            )
            
            (if foundSize
              (princ (strcat " Tamanho alterado para " userSize "."))
              (princ " (Aviso: Não consegui mudar o tamanho do bloco. Verifique se o parâmetro dinâmico aceita o texto exato).")
            )
            
            ;; --- PASSO B: OBTER COORDENADAS PARA A WINDOW ---
            ;; Obter BoundingBox atualizada
            (vla-GetBoundingBox obj 'minPt 'maxPt)
            ;; minPt e maxPt são safearrays, precisamos deles assim para o SetWindowToPlot
            
            ;; --- PASSO C: CONFIGURAR O LAYOUT ---
            ;; Aceder ao Layout onde o bloco está
            (setq layout (vla-Item (vla-get-Layouts doc) (vla-get-Layout obj)))
            
            ;; Forçar atualização das configurações
            (vla-RefreshPlotDeviceInfo layout)
            
            ;; 1. Plotter
            (vl-catch-all-apply 'vla-put-ConfigName (list layout targetPlotter))
            
            ;; 2. CTB
            (vl-catch-all-apply 'vla-put-StyleSheet (list layout targetCTB))
            
            ;; 3. Tamanho do Papel (Canonical Name)
            (vl-catch-all-apply 'vla-put-CanonicalMediaName (list layout mediaName))
            
            ;; 4. Tipo de Plot: Window
            (vla-put-PlotType layout acWindow)
            
            ;; 5. Definir a Janela (Window) - É preciso converter Safearray para Array de Doubles 2D
            (vla-SetWindowToPlot layout minPt maxPt)
            
            ;; 6. Escala Personalizada (1 mm = 0.1 Unidades)
            (vla-put-StandardScale layout acScaleCustom)
            (vla-SetCustomScale layout 1.0 0.1) ;; Numerador (Papel), Denominador (Desenho)
            
            ;; 7. Outras definições
            (vla-put-PlotRotation layout ac0degrees) ;; Landscape (Normalmente 0 ou 90 dependendo do plotter, ajusta se sair rodado)
            (vla-put-CenterPlot layout :vlax-true)
            
            (princ " Layout configurado.")
          )
        )
      )
      (vla-Regen doc acAllViewports)
      (alert (strcat "Processo concluído!\n\nDefinido para: " userSize "\nEscala: 1mm = 0.1un"))
    )
    (princ "\nNenhum bloco selecionado.")
  )
  (vla-EndUndoMark doc)
  (princ)
)
(princ "\nComando carregado: SETUPFOLHAS")