;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Rebar Data Extraction Utility - Geliştirilmiş Sürüm (Detaylı Hesaplama Açıklamasıyla)
;; CSV ve TXT çıktısına ek olarak her satır için hesaplama süreci açıklaması ekleniyor.
;;
;; Açıklamalar:
;; 1. Etriye Grubu:
;;    - "ƒ10 Etr. l=168" metninden parça boy (168 cm) ve çap (10) çıkarılır.
;;    - "Etr.%%C10/8" metninden aralık bilgisi (8 cm) çıkarılır.
;;    - Ardından gelen DIMENSION değeri (örneğin 291 cm) ile:
;;         adet = floor(291/8)  ve toplam etriye boy = adet x 168 hesaplanır.
;; 2. Donatı (Count Faktörlü) Grubu:
;;    - "2x%%C12/15 L=185" metninden count (2), parça boy (185 cm), aralık (15 cm) ve çap (12) çıkarılır.
;;    - Sonrasında gelen DIMENSION değeri (örneğin 171 cm) ile:
;;         adet = 2 x floor(171/15)  ve toplam donatı boy = adet x 185 hesaplanır.
;; 3. Donatı (Simple) Grubu:
;;    - "ƒ10/8" gibi metinlerde, ilk DIMENSION parça boy, ikinci DIMENSION genel boy olarak alınır.
;;    - Hesaplama, adet = floor(Boy/Aralık) ve toplam boy = adet x parça boy şeklinde yapılır.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; Hata mesajı fonksiyonu
(defun rebar-error (msg)
  (if (= msg "Function cancelled")
    (princ "\nFunction cancelled\n")
    (princ (strcat "\nError: " msg))
  )
  (setvar "CMDECHO" 1)
  (princ)
)

;; Debug yardımcı fonksiyonu
(defun debug-print (msg value)
  (princ (strcat "\nDEBUG - " msg ": "))
  (princ value)
  (princ)
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Yardımcı Fonksiyonlar: extract_digits ve extraction fonksiyonları
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; Verilen bir dizedeki sadece rakam karakterlerini döndürür.
(defun extract_digits (str / result i ch)
  (setq result "")
  (setq i 1)
  (while (<= i (strlen str))
    (setq ch (substr str i 1))
    (if (wcmatch ch "[0-9]")
      (setq result (strcat result ch))
    )
    (setq i (1+ i))
  )
  result
)

;; Metin içerisindeki "ƒ" karakterinden sonraki rakamları alarak çap değerini döndürür.
(defun extract_diameter_f (txt / pos digitStr)
  (setq pos (vl-string-search "ƒ" txt))
  (if pos
    (progn
      (setq pos (+ pos 1))  ; "ƒ" karakterinden sonraya geç
      (while (and (< pos (strlen txt)) (equal (substr txt pos 1) " "))
        (setq pos (1+ pos))
      )
      (setq digitStr (extract_digits (substr txt pos (+ 1 (- (strlen txt) pos)))))
      (if (> (strlen digitStr) 0)
          (read digitStr)
          nil
      )
    )
    nil
  )
)

;; Metin içerisindeki "%%C" dizgisinden sonraki rakamları alarak çap değerini döndürür.
(defun extract_diameter_percent (txt / pos digitStr)
  (setq pos (vl-string-search "%%C" txt))
  (if pos
    (progn
      (setq pos (+ pos 4))  ; "%%C" sonrasına geç
      (while (and (< pos (strlen txt)) (equal (substr txt pos 1) " "))
        (setq pos (1+ pos))
      )
      (setq digitStr (extract_digits (substr txt pos (+ 1 (- (strlen txt) pos)))))
      (if (> (strlen digitStr) 0)
          (read digitStr)
          nil
      )
    )
    nil
  )
)

;; Metin içerisindeki "L=" veya "l=" ifadesinden sonraki rakamları alarak parça boyunu döndürür.
(defun extract_length (txt / pos digitStr)
  (setq pos (or (vl-string-search "L=" (strcase txt))
                (vl-string-search "l=" txt)))
  (if pos
    (progn
      (setq pos (+ pos 2))  ; "L=" den sonraki karaktere geç
      (while (and (< pos (strlen txt))
                  (or (equal (substr txt pos 1) " ")
                      (equal (substr txt pos 1) "\t")))
        (setq pos (1+ pos))
      )
      (setq digitStr (extract_digits (substr txt pos (+ 1 (- (strlen txt) pos)))))
      (if (> (strlen digitStr) 0)
          (read digitStr)
          nil
      )
    )
    nil
  )
)

;; Metin içerisindeki "/" karakterinden sonraki rakamları alır (arayüz değeri).
(defun extract_spacing (txt / pos digitStr)
  (setq pos (vl-string-search "/" txt))
  (if pos
    (progn
      (setq pos (+ pos 2))
      (setq digitStr (extract_digits (substr txt pos (+ 1 (- (strlen txt) pos)))))
      (if (> (strlen digitStr) 0)
          (read digitStr)
          nil
      )
    )
    nil
  )
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Hesaplama Fonksiyonları
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun calculate_count (boy spacing)
  (if (and boy spacing (> spacing 0))
    (fix (/ boy spacing))
    0
  )
)

(defun calculate_total_length (count piece_length)
  (* count piece_length)
)

(defun calculate_donati_total_length (count_factor boy spacing piece_length)
  (let ((n (calculate_count boy spacing)))
    (* count_factor n piece_length)
  )
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Pattern Eşleştirme ve Etiketleme
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun process_entity (ent / type_obj txt)
  (setq entdata (entget ent))
  (setq type_obj (cdr (assoc 0 entdata)))
  (setq txt (cdr (assoc 1 entdata)))
  (cond 
    ;; ETRİYE metni: örn. "ƒ10 Etr. l=168"
    ((and txt (wcmatch (strcase txt) "*ETR.*L=*") (vl-string-search "ƒ" txt))
      (setq dia (extract_diameter_f txt))
      (setq len (extract_length txt))
      (debug-print "EtriyeText - Text" txt)
      (list "EtriyeText" dia nil len)
    )
    ;; ETRİYE aralık metni: örn. "Etr.%%C10/8"
    ((and txt (wcmatch (strcase txt) "*ETR*%%C*/?*"))
      (setq spc (extract_spacing txt))
      (setq dia (extract_diameter_percent txt))
      (debug-print "EtriyeSpacing - Text" txt)
      (list "EtriyeSpacing" dia spc nil)
    )
    ;; DONATİ count faktörlü: örn. "2x%%C12/15 L=185"
    ((and txt (wcmatch (strcase txt) "*X%%C*/* L=*"))
      (setq cnt (extract_count txt))
      (setq dia (extract_diameter_percent txt))
      (setq spc (extract_spacing txt))
      (setq len (extract_length txt))
      (debug-print "DonatiCount - Text" txt)
      (list "DonatiCount" dia spc len cnt)
    )
    ;; DONATİ basit: örn. "ƒ10/8" (Etriye kelimesi yoksa)
    ((and txt (wcmatch (strcase txt) "*ƒ*/*") (not (wcmatch (strcase txt) "*ETR*")))
      (setq dia (extract_diameter_f txt))
      (setq spc (extract_spacing txt))
      (debug-print "DonatiSimple - Text" txt)
      (list "DonatiSimple" dia spc nil)
    )
    ;; Sadece L= içeren metin (uzunluk objesi gibi)
    ((and txt (wcmatch (strcase txt) "L=*"))
      (setq len (extract_length txt))
      (debug-print "LengthOnly - Text" txt)
      (list "LengthOnly" nil nil len)
    )
    ;; Eğer ent tipi DIMENSION ise
    ((= type_obj "DIMENSION")
      (setq measure (cdr (assoc 42 entdata)))
      (debug-print "Dimension" (vl-princ-to-string measure))
      (list "Dimension" nil nil nil measure)
    )
    (T
      (debug-print "No match" txt)
      nil
    )
  )
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Veri Toplama, Gruplama ve Hesaplama
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun collect_data ( / ss ent i data main_list)
  (setq main_list '())
  (setq ss (ssget '((0 . "TEXT,MTEXT,DIMENSION"))))
  (if ss
    (progn
      (setq i 0)
      (repeat (sslength ss)
        (setq ent (ssname ss i))
        (setq data (process_entity ent))
        (if data
          (progn
            (debug-print "Processing entity index" (itoa i))
            (debug-print "Entity data" (vl-princ-to-string data))
            (setq main_list (append main_list (list data)))
          )
        )
        (setq i (1+ i))
      )
    )
  )
  (debug-print "Collected data list" (vl-princ-to-string main_list))
  main_list
)

(defun calculate_final_values (data / final i rec type dia spc piece boy cnt adet tot explanation)
  (setq final '())
  (setq i 0)
  (while (< i (length data))
    (setq rec (nth i data))
    (setq type (nth 0 rec))
    (cond
      ;; ETRİYE grubu: sırasıyla EtriyeText, EtriyeSpacing, Dimension
      ((equal type "EtriyeText")
       (if (and (>= (length data) (+ i 2))
                (equal (nth 0 (nth (1+ i) data)) "EtriyeSpacing")
                (equal (nth 0 (nth (+ i 2) data)) "Dimension"))
         (progn
           (setq dia (nth 1 rec))
           (setq piece (nth 3 rec))           ; parça boy (L= değeri)
           (setq spc (nth 2 (nth (1+ i) data)))
           (setq boy (nth 4 (nth (+ i 2) data))) ; Dimension değeri (boy)
           (setq adet (calculate_count boy spc))
           (setq tot (calculate_total_length adet piece))
           (setq explanation 
             (strcat "Etriye hesaplaması: Parça boy = " (vl-princ-to-string piece)
                     " cm, Aralık = " (vl-princ-to-string spc) " cm, Boy = " (vl-princ-to-string boy)
                     " cm. Adet = floor(" (vl-princ-to-string boy) "/" (vl-princ-to-string spc)
                     ") = " (itoa adet) ", Toplam Boy = " (itoa adet) " x " (vl-princ-to-string piece)
                     " = " (itoa tot) " cm." ))
           (debug-print "Group Etriye hesap" explanation)
           (setq final (append final (list (list "Etriye" dia spc boy adet tot "Stirrups" explanation))))
           (setq i (+ i 3))
         )
         (setq i (1+ i))
       )
      )
      ;; DONATİ count faktörlü grubu: sırasıyla DonatiCount, Dimension
      ((equal type "DonatiCount")
       (if (and (>= (length data) (+ i 1))
                (equal (nth 0 (nth (1+ i) data)) "Dimension"))
         (progn
           (setq cnt (nth 4 rec))
           (setq dia (nth 1 rec))
           (setq spc (nth 2 rec))
           (setq piece (nth 3 rec))
           (setq boy (nth 4 (nth (1+ i) data)))
           (setq adet (* cnt (calculate_count boy spc)))
           (setq tot (calculate_donati_total_length cnt boy spc piece))
           (setq explanation 
             (strcat "Donatı hesaplaması: Count = " (itoa cnt)
                     ", Parça boy = " (vl-princ-to-string piece) " cm, Aralık = " (vl-princ-to-string spc)
                     " cm, Boy = " (vl-princ-to-string boy) " cm. Adet = " (itoa cnt)
                     " x floor(" (vl-princ-to-string boy) "/" (vl-princ-to-string spc)
                     ") = " (itoa adet) ", Toplam Boy = " (itoa adet) " x " (vl-princ-to-string piece)
                     " = " (itoa tot) " cm." ))
           (debug-print "Group DonatiCount hesap" explanation)
           (setq final (append final (list (list "Donatı" dia spc boy adet tot "Rebar" explanation))))
           (setq i (+ i 2))
         )
         (setq i (1+ i))
       )
      )
      ;; DONATİ basit grubu: sırasıyla DonatiSimple, Dimension, Dimension
      ((equal type "DonatiSimple")
       (if (and (>= (length data) (+ i 2))
                (equal (nth 0 (nth (1+ i) data)) "Dimension")
                (equal (nth 0 (nth (+ i 2) data)) "Dimension"))
         (progn
           (setq dia (nth 1 rec))
           (setq spc (nth 2 rec))
           (setq piece (nth 4 (nth (1+ i) data)))  ; ilk Dimension = parça boy
           (setq boy (nth 4 (nth (+ i 2) data)))    ; ikinci Dimension = genel boy
           (setq adet (calculate_count boy spc))
           (setq tot (calculate_total_length adet piece))
           (setq explanation 
             (strcat "Donatı Simple hesaplaması: Parça boy = " (vl-princ-to-string piece)
                     " cm, Aralık = " (vl-princ-to-string spc) " cm, Boy = " (vl-princ-to-string boy)
                     " cm. Adet = floor(" (vl-princ-to-string boy) "/" (vl-princ-to-string spc)
                     ") = " (itoa adet) ", Toplam Boy = " (itoa adet) " x " (vl-princ-to-string piece)
                     " = " (itoa tot) " cm." ))
           (debug-print "Group DonatiSimple hesap" explanation)
           (setq final (append final (list (list "Donatı" dia spc boy adet tot "Rebar" explanation))))
           (setq i (+ i 3))
         )
         (setq i (1+ i))
       )
      )
      (T (setq i (1+ i)))
    )
  )
  (debug-print "Final grouped data" (vl-princ-to-string final))
  final
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Dışa Aktarım Fonksiyonları (CSV ve TXT) - Açıklama sütunu eklendi
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun export_to_csv (data filepath / file)
  (setq file (open filepath "w"))
  (write-line "Tip,Çap,Aralık,Boy,Adet,Toplam Boy,Tür,Açıklama" file)
  (foreach row data
    (write-line 
      (strcat 
        (nth 0 row) "," 
        (vl-princ-to-string (nth 1 row)) "," 
        (vl-princ-to-string (nth 2 row)) ","
        (vl-princ-to-string (nth 3 row)) "," 
        (vl-princ-to-string (nth 4 row)) "," 
        (vl-princ-to-string (nth 5 row)) "," 
        (nth 6 row) "," 
        (nth 7 row)
      )
      file
    )
  )
  (close file)
)

(defun export_to_txt (data filepath / file)
  (setq file (open filepath "w"))
  (write-line "Tip\tÇap\tAralık\tBoy\tAdet\tToplam Boy\tTür\tAçıklama" file)
  (foreach row data
    (write-line 
      (strcat 
        (nth 0 row) "\t" 
        (vl-princ-to-string (nth 1 row)) "\t" 
        (vl-princ-to-string (nth 2 row)) "\t"
        (vl-princ-to-string (nth 3 row)) "\t" 
        (vl-princ-to-string (nth 4 row)) "\t"
        (vl-princ-to-string (nth 5 row)) "\t"
        (nth 6 row) "\t" 
        (nth 7 row)
      )
      file
    )
  )
  (close file)
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Ana Fonksiyon: Verileri Topla, Grupla, Hesapla ve Dışa Aktar
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun c:EXPORTREBAR ( / main_list final_list file_path)
  (setq main_list (collect_data))
  (setq final_list (calculate_final_values main_list))
  (if (and final_list (> (length final_list) 0))
    (progn
      (setq file_path (getvar "DWGPREFIX"))
      (export_to_csv final_list (strcat file_path "rebar_data.csv"))
      (export_to_txt final_list (strcat file_path "rebar_data.txt"))
      (princ "\nData exported successfully with calculated values and explanations\n")
      (debug-print "Exported group count" (itoa (length final_list)))
    )
    (princ "\nNo grouped data found to export\n")
  )
  (princ)
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Layer Standardization Utility (Aynı Kalıyor)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun c:STANDARDIZELAYERS ( / *error*)
  (defun std-error (msg)
    (if (= msg "Function cancelled")
      (princ "\nFunction cancelled\n")
      (princ (strcat "\nError: " msg))
    )
    (setvar "CMDECHO" 1)
    (princ)
  )
  (command "._-layer" "M" "COLOR" "7" "*" "")
  (command "._-layer" "M" "LTYPE" "CONTINUOUS" "*" "")
  (princ "\nLayers standardized\n")
  (princ)
)
