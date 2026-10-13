(vl-load-com) ;; COM kütüphanelerini yükleyelim.
(princ "COM kütüphanesi yüklendi.\n") ;; Yükleme tamamlandığında mesaj verir.

;; Excel uygulamasını başlatıyoruz
(setq excelApp (vlax-get-or-create-object "Excel.Application"))
(princ "Excel uygulaması başlatıldı.\n")

;; Excel görünürlüğünü açıyoruz (kullanıcıya gösterilecek)
(vlax-put-property excelApp 'Visible :vlax-true)
(princ "Excel görünürlüğü açıldı.\n")

;; Workbooks koleksiyonunu alıyoruz
(setq workbooks (vlax-get-property excelApp 'Workbooks))
(princ "Workbooks koleksiyonu alındı.\n")

;; Yeni bir workbook ekliyoruz
(setq wb (vlax-invoke-method workbooks 'Add))
(princ "Yeni bir workbook oluşturuldu.\n")

;; İlk worksheet'e erişim sağlıyoruz
(setq ws (vlax-get-property (vlax-get-property wb 'Worksheets) 'Item 1))
(princ "İlk worksheet alındı.\n")

;; Autocad'den boyut (dimension) değerini alalım
(setq selected-obj (car (entsel "\nBoyut (Dimension) seçin: ")))

;; Seçilen objenin boyut değerini alalım
(if (and selected-obj (= (vla-get-objectname (vlax-ename->vla-object selected-obj)) "AcDbDimension"))
    (progn
      (setq dimObj (vlax-ename->vla-object selected-obj)) ;; Dimension objesine dönüşüm
      (setq dimValue (vla-get-textstring dimObj)) ;; Boyut değerini al
      (princ (strcat "Seçilen boyut: " dimValue "\n"))
      
      ;; String formatına çevir (eğer gerekirse)
      (setq dimValueStr (rtos (atof dimValue) 2 2)) ;; Sayıyı string'e çevir
      
      ;; Excel hücresine değer yazalım (A1 hücresine)
      (vlax-put-property (vlax-get-property ws 'Cells) 'Item 1 1 dimValueStr)
      (princ "Boyut değeri A1 hücresine yazıldı.\n")
    )
    (princ "\nSeçilen obje bir boyut (dimension) değil.\n")
)

;; Hücre A1'deki değeri kontrol edelim
(setq value (vlax-get-property (vlax-get-property ws 'Cells) 'Item 1 1))
(princ (strcat "Hücre A1'deki değer: " value "\n"))
