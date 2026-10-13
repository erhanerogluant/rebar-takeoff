(defun c:METRAJ (/ old-error *error* dcl_id)
  ;; Hata yakalama fonksiyonu
  (defun *error* (msg)
    (if (= msg "Function cancelled")
        (princ "\nİşlem iptal edildi.")
        (princ (strcat "\nHata: " msg))
    )
    (clean-up)
    (setq *error* old-error)
    (princ)
  )

  ;; Temizleme fonksiyonu
  (defun clean-up ()
    (if excel
        (progn
          (vla-quit excel)
          (vlax-release-object excel)
        )
    )
  )

  ;; Excel'i başlat
  (vl-load-com)
  (setq old-error *error*)
  
  (if (setq excel (vlax-get-or-create-object "Excel.Application"))
    (progn
      (vlax-put-property excel 'Visible :vlax-true)
      
      ;; Yeni workbook ve sheet
      (setq wb (vlax-invoke-method (vlax-get-property excel 'Workbooks) 'Add))
      (setq sheet (vlax-get-property wb 'ActiveSheet))
      
      ;; Başlıkları yaz
      (vlax-put-property (vlax-invoke-method sheet 'Range "A1") 'Value "Adet")
      (vlax-put-property (vlax-invoke-method sheet 'Range "B1") 'Value "Çap")
      (vlax-put-property (vlax-invoke-method sheet 'Range "C1") 'Value "Aralık")
      (vlax-put-property (vlax-invoke-method sheet 'Range "D1") 'Value "L")
      (vlax-put-property (vlax-invoke-method sheet 'Range "E1") 'Value "=")
      (vlax-put-property (vlax-invoke-method sheet 'Range "F1") 'Value "Boy")
      (vlax-put-property (vlax-invoke-method sheet 'Range "G1") 'Value "Dimension")
      
      (setq row 2)
      
      ;; Ana döngü
      (while
        (progn
          (initget 1)
          (setq ent (entsel "\nEleman seçin veya ENTER ile çıkın: "))
          ent
        )
        
        (if (= "TEXT" (cdr (assoc 0 (entget (car ent)))))
          (progn
            (setq txt (cdr (assoc 1 (entget (car ent)))))
            
            ;; Text analizi
            (cond
              ;; 2x∅12/15 formatı
              ((vl-string-search "x" txt)
               (progn
                 (setq adet (substr txt 1 1))
                 (if (vl-string-search "∅" txt)
                   (setq cap (substr txt 
                                   (+ (vl-string-search "∅" txt) 2)
                                   2))
                 )
                 (if (vl-string-search "/" txt)
                   (setq aralik (substr txt 
                                      (+ (vl-string-search "/" txt) 1)
                                      2))
                 )
               )
              )
              
              ;; Etr.∅10/8 formatı
              ((vl-string-search "∅" txt)
               (progn
                 (setq adet "1")
                 (setq cap (substr txt 
                                 (+ (vl-string-search "∅" txt) 2)
                                 2))
                 (if (vl-string-search "/" txt)
                   (setq aralik (substr txt 
                                      (+ (vl-string-search "/" txt) 1)
                                      2))
                 )
               )
              )
            )
            
            ;; Excel'e yaz
            (vlax-put-property (vlax-invoke-method sheet 'Cells row 1) 'Value adet)
            (vlax-put-property (vlax-invoke-method sheet 'Cells row 2) 'Value cap)
            (vlax-put-property (vlax-invoke-method sheet 'Cells row 3) 'Value aralik)
            
            ;; L=110 formatı kontrolü
            (if (or (vl-string-search "L=" txt) (vl-string-search "l=" txt))
              (progn
                (vlax-put-property (vlax-invoke-method sheet 'Cells row 4) 'Value "L")
                (vlax-put-property (vlax-invoke-method sheet 'Cells row 5) 'Value "=")
                (if (vl-string-search "=" txt)
                  (setq boy_deger (substr txt 
                                        (+ (vl-string-search "=" txt) 2)))
                )
                (vlax-put-property (vlax-invoke-method sheet 'Cells row 6) 'Value boy_deger)
              )
            )
          )
        )
        
        ;; Dimension kontrolü
        (if (= "DIMENSION" (cdr (assoc 0 (entget (car ent)))))
          (progn
            (setq dim_deger (rtos (cdr (assoc 42 (entget (car ent)))) 2 0))
            (vlax-put-property (vlax-invoke-method sheet 'Cells row 7) 'Value dim_deger)
          )
        )
        
        (setq row (1+ row))
      )
      
      ;; Dosyayı kaydet ve kapat
      (vla-saveas wb (strcat (getvar "DWGPREFIX") "metraj.xlsx"))
      (vla-close wb)
      (clean-up)
    )
    (prompt "\nExcel başlatılamadı!")
  )
  (princ)
)