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

;; Eğer worksheet alınamazsa alternatif bir yöntem deneyelim:
;; (Alternatif 1: Eğer 'Item 1' hatalıysa, Worksheets koleksiyonunu kontrol edelim)
;; (Alternatif 2: Veya Worksheet koleksiyonundan direkt olarak erişelim)

;; Hücre A1'e değer yazıyoruz
(vlax-put-property (vlax-get-property ws 'Cells) 'Item 1 1 "Test Değeri")
(princ "Hücre A1'e değer yazıldı.\n")

;; Hücre A1'deki değeri kontrol edelim
(setq value (vlax-get-property (vlax-get-property ws 'Cells) 'Item 1 1))
(princ (strcat "Hücre A1'deki değer: " value "\n"))
