(defun c:ExportToCSV (/ ss csv ent obj txt dimVal path adet cap boy)
  ; AutoCAD dosyasının bulunduğu klasörü al
  (setq path (strcat (getvar "dwgprefix") "DemirMetraj.csv"))
  
  ; CSV dosyasını aç
  (setq csv (open path "w"))
  (if csv
    (progn
      ; Başlık satırı (Yeni sütunlar eklendi)
      (write-line "Tip,Adet,Çap,Boy,Uzunluk" csv)
      
      ; Nesneleri seç
      (setq ss (ssget '((0 . "TEXT,DIMENSION"))))
      (if ss
        (progn
          (setq i 0)
          (repeat (sslength ss)
            (setq ent (ssname ss i))
            (setq obj (vlax-ename->vla-object ent))
            (cond
              ; TEXT nesneleri (Örnek: 2X20∅16)
              ((= (vla-get-objectname obj) "AcDbText")
                (setq txt (vl-string-translate "%" "∅" (vla-get-textstring obj))) ; %%C -> ∅
                ; Veriyi parçala: "2X20∅16" -> Adet=2, Çap=20, Boy=16
                (if (wcmatch txt "*X*∅*")
                  (progn
                    (setq adet (substr txt 1 (vl-string-position (ascii "X") txt)))
                    (setq cap (substr txt (+ (vl-string-position (ascii "X") txt 2) (vl-string-position (ascii "∅") txt)))
                    (setq boy (substr txt (+ (vl-string-position (ascii "∅") txt 2)))
                    (write-line (strcat "Text," adet "," cap "," boy ",") csv)
                  )
                  (write-line (strcat "Text,,,,,") csv) ; Hatalı format
                )
              )
              ; DIMENSION nesneleri
              ((wcmatch (vla-get-objectname obj) "*Dimension")
                (setq dimVal (rtos (vla-get-measurement obj)))
                (write-line (strcat "Dimension,,,," dimVal) csv)
              )
            )
            (setq i (1+ i))
          )
          (princ "\n Veriler CSV'ye kaydedildi!")
        )
        (princ "\n Hiç nesne seçilmedi!")
      )
      (close csv)
      ; CSV'yi Excel'de aç
      (startapp "excel.exe" path)
    )
    (princ "\n CSV dosyası oluşturulamadı!")
  )
  (princ)
)