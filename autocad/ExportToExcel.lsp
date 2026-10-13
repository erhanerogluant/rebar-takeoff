(defun c:ExportToExcel (/ excel-app workbook worksheet ss ent obj dataList row)
  (vl-load-com)
  
  ; 1. Excel'i başlat
  (setq excel-app (vlax-get-or-create-object "Excel.Application"))
  (vlax-put-property excel-app 'Visible :vlax-true)
  
  ; 2. Yeni Workbook ve Worksheet oluştur
  (setq workbook (vlax-invoke (vlax-get-property excel-app 'Workbooks) 'Add))
  (setq worksheet (vlax-get-property workbook 'Worksheets 'Item 1))
  
  ; 3. Başlık satırlarını yaz
  (vlax-put-property (vlax-get-property worksheet 'Range "A1") 'Value2 "Type")
  (vlax-put-property (vlax-get-property worksheet 'Range "B1") 'Value2 "Value")
  (vlax-put-property (vlax-get-property worksheet 'Range "C1") 'Value2 "Length")
  
  ; 4. AutoCAD'den veri topla (Text ve Dimension)
  (setq ss (ssget '((0 . "TEXT,DIMENSION"))))
  (setq dataList '())
  (if ss
    (progn
      (setq i 0)
      (repeat (sslength ss)
        (setq ent (ssname ss i))
        (setq obj (vlax-ename->vla-object ent))
        (cond
          ; 4a. TEXT nesneleri
          ((= (vla-get-objectname obj) "AcDbText")
            (setq dataList (cons (list "Text" (vl-string-translate "%" "Φ" (vla-get-textstring obj)) dataList))
          )
          ; 4b. DIMENSION nesneleri
          ((wcmatch (vla-get-objectname obj) "*Dimension")
            (setq dataList (cons (list "Dimension" "" (rtos (vla-get-measurement obj))) dataList))
          )
        )
        (setq i (1+ i))
      )
    )
    (princ "\n Hiç nesne seçilmedi!")
  )
  
  ; 5. Verileri Excel'e yaz
  (setq row 2)
  (foreach data (reverse dataList)
    (vlax-put-property (vlax-get-property worksheet 'Range (strcat "A" (itoa row))) 'Value2 (nth 0 data))
    (vlax-put-property (vlax-get-property worksheet 'Range (strcat "B" (itoa row))) 'Value2 (nth 1 data))
    (vlax-put-property (vlax-get-property worksheet 'Range (strcat "C" (itoa row))) 'Value2 (nth 2 data))
    (setq row (1+ row))
  )
  
  ; 6. Sütun genişliklerini otomatik ayarla
  (vlax-invoke (vlax-get worksheet 'Columns) 'AutoFit)
  
  ; 7. Excel'i kapat ve temizle
  (vlax-release-object worksheet)
  (vlax-release-object workbook)
  (vlax-release-object excel-app)
  (princ "\n Veriler Excel'e aktarıldı!")
  (princ)
)