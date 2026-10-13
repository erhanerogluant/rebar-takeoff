(defun c:ExportRebarData (/ ss csv file data txt dimval dwgprefix path)
  ; Proje klasörünü al
  (setq dwgprefix (getvar "dwgprefix"))
  (if (or (null dwgprefix) (= dwgprefix ""))
    (setq path "RebarData.csv") ; Eğer dosya kaydedilmemişse
    (progn
      ; Klasör sonunda \\ yoksa ekle
      (if (/= (substr dwgprefix (strlen dwgprefix)) "\\")
        (setq dwgprefix (strcat dwgprefix "\\"))
      )
      (setq path (strcat dwgprefix "RebarData.csv"))
    )
  )
  
  ; CSV dosyasını aç
  (setq csv (open path "w"))
  (if (null csv)
    (princ "\n Dosya oluşturulamadı! Yazma izninizi kontrol edin.")
    (progn
      ; Başlık satırı
      (write-line "Type,Value,Length" csv)
      
      ; Nesneleri seç
      (setq ss (ssget '((0 . "TEXT,DIMENSION"))))
      (if ss
        (progn
          (setq i 0)
          (repeat (sslength ss)
            (setq ent (ssname ss i))
            (setq obj (vlax-ename->vla-object ent))
            (cond
              ; TEXT nesneleri
              ((= (vla-get-objectname obj) "AcDbText")
                (setq txt (vla-get-textstring obj))
                (write-line (strcat "Text," txt ",") csv)
              )
              ; DIMENSION nesneleri
              ((= (vla-get-objectname obj) "AcDbAlignedDimension")
                (setq dimval (vla-get-measurement obj))
                (write-line (strcat "Dimension," "," (rtos dimval)) csv)
              )
            )
            (setq i (1+ i))
          )
          (princ "\n Veriler başarıyla CSV'ye aktarıldı!")
        )
        (princ "\n Nesne seçilmedi!")
      )
      (close csv)
    )
  )
  (princ)
)