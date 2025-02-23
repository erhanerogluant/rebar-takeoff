from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                           QTreeWidgetItem, QStatusBar, QMessageBox, QFileDialog,
                           QDialog, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
import sys
from autocad_integration import AutoCADIntegration
import os
from datetime import datetime
import logging

class SelectionThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, acad, parent=None):
        super().__init__(parent)
        self.acad = acad
        self.running = True
    
    def stop(self):
        self.running = False
    
    def run(self):
        try:
            while self.running:
                # Seçim işlemleri burada
                pass
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class RebarCalculatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demir Metraj Hesaplama")
        self.setGeometry(100, 100, 1200, 800)
        
        # AutoCAD entegrasyonu
        self.acad = AutoCADIntegration()
        
        # Log handler'ı bağla
        self.setup_log_handler()
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Sol panel - Kategori seçimi
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Kategori butonları
        self.btn_rebar = QPushButton("Boy Demiri")
        self.btn_stirrup = QPushButton("Etriye")
        self.btn_mesh = QPushButton("Hasır")
        self.btn_connection = QPushButton("Ara Bağlantı")
        
        # Butonlara stil ekle
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """
        
        self.btn_rebar.setStyleSheet(button_style)
        self.btn_stirrup.setStyleSheet(button_style)
        self.btn_mesh.setStyleSheet(button_style)
        self.btn_connection.setStyleSheet(button_style)
        
        # İşlem butonları
        self.btn_calculate = QPushButton("Hesapla")
        self.btn_calculate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
        """)
        
        # İşlemi Durdur butonu
        self.btn_stop = QPushButton("İşlemi Durdur")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        
        # Yenile butonu
        self.btn_refresh = QPushButton("Yenile")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        
        # Tüm butonları aktif yap
        self.btn_calculate.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.btn_stop.setEnabled(True)  # İşlemi Durdur butonu da aktif
        
        # Buton grupları için frame'ler
        operation_frame = QGroupBox("İşlemler")
        operation_layout = QVBoxLayout(operation_frame)
        operation_layout.addWidget(self.btn_rebar)
        operation_layout.addWidget(self.btn_stirrup)
        operation_layout.addWidget(self.btn_mesh)
        operation_layout.addWidget(self.btn_connection)
        operation_layout.addStretch()
        
        control_frame = QGroupBox("Kontroller")
        control_layout = QVBoxLayout(control_frame)
        control_layout.addWidget(self.btn_calculate)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_refresh)
        control_layout.addStretch()
        
        # Butonları bağla
        self.btn_rebar.clicked.connect(self.start_rebar_selection)
        self.btn_stirrup.clicked.connect(self.start_stirrup_selection)
        self.btn_mesh.clicked.connect(self.start_mesh_selection)
        self.btn_connection.clicked.connect(self.start_connection_selection)
        self.btn_calculate.clicked.connect(self.calculate_results)
        self.btn_stop.clicked.connect(self.stop_current_operation)
        self.btn_refresh.clicked.connect(self.refresh_application)
        
        # Sol panel düzeni
        left_layout.addWidget(operation_frame)
        left_layout.addSpacing(10)
        left_layout.addWidget(control_frame)
        
        # İşlem durumu için flag
        self.current_operation = None
        self.is_operation_running = False
        
        # Seçilen öğeleri tutacak liste
        self.current_selections = []
        
        # Sağ panel - İşlem alanı
        right_panel = QWidget()
        self.right_layout = QVBoxLayout(right_panel)
        
        # Log görüntüleme alanı
        log_group = QGroupBox("İşlem Logları")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 10pt;")
        log_layout.addWidget(self.log_text)
        
        # Sonuç ağacı
        tree_group = QGroupBox("Sonuçlar")
        tree_layout = QVBoxLayout(tree_group)
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["Tip", "Detay", "Ağırlık"])
        tree_layout.addWidget(self.result_tree)
        
        # Genel Toplam Label'ı
        total_widget = QWidget()
        total_layout = QHBoxLayout(total_widget)
        total_layout.addStretch()
        self.total_label = QLabel("Genel Toplam: 0.00 kg (0.000 ton)")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        total_layout.addWidget(self.total_label)
        
        # Layout'a widget'ları ekle
        self.right_layout.addWidget(log_group, 1)  # Log alanı
        self.right_layout.addWidget(tree_group, 2) # Sonuç ağacı
        self.right_layout.addWidget(total_widget)  # Toplam label
        
        # Layout'ları ana layout'a ekle
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 4)
        
        # Durum çubuğu
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Araç çubuğu
        self.setup_toolbar()
        
        # Kısayol tuşları ekle
        self.shortcut_esc = QShortcut(QKeySequence('Esc'), self)
        self.shortcut_esc.activated.connect(self.stop_current_operation)
        
        # Selection thread
        self.selection_thread = None
        
    def setup_toolbar(self):
        toolbar = self.addToolBar("Araç Çubuğu")
        
        # Yeni Proje
        new_action = toolbar.addAction("Yeni Proje")
        new_action.triggered.connect(self.new_project)
        
        # Kaydet
        save_action = toolbar.addAction("Kaydet")
        save_action.triggered.connect(self.save_project)
        
        # Rapor Al
        report_action = toolbar.addAction("Rapor Al")
        report_action.triggered.connect(self.generate_report)
        
    def start_rebar_selection(self):
        self.is_operation_running = True
        self.current_operation = 'REBAR'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Boy demiri seçimi başlatıldı...")
        try:
            while True:
                text = self.acad.select_entity("Boy demiri seçin veya çıkmak için ESC")
                if not text:
                    break
                
                # Hesaplama ve sonuç ekleme
                if self.acad.calculator.process_text(text):
                    self.add_result_to_tree("Boy Demiri", text)
                    
            self.update_summary()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
            
    def add_result_to_tree(self, type_name, details):
        """Sonucu ağaca ekle"""
        try:
            # Yeni öğe oluştur
            item = QTreeWidgetItem(self.result_tree)
            item.setText(0, type_name)
            item.setText(1, details)
            
            # Son eklenen sonucun ağırlığını al
            if self.acad.calculator.results:
                last_result = self.acad.calculator.results[-1]
                weight = last_result.total_weight
                item.setText(2, f"{weight:.2f} kg")
                
                # Detaylı bilgiyi konsola yazdır
                print(f"\nHesaplama Sonucu:")
                print(f"Tip: {type_name}")
                print(f"Detay: {details}")
                print(f"Çap: Ø{last_result.diameter}")
                print(f"Boy: {last_result.length} cm")
                print(f"Adet: {last_result.count}")
                print(f"Toplam Boy: {last_result.total_length/100:.2f} m")
                print(f"Birim Ağırlık: {last_result.weight_per_meter:.3f} kg/mt")
                print(f"Toplam Ağırlık: {weight:.2f} kg")
                
                # Ağacı güncelle
                self.result_tree.scrollToItem(item)
                self.result_tree.setCurrentItem(item)
                
                # Log alanını güncelle
                self.log_text.append(f"\nYeni hesaplama eklendi: {type_name} - {details} - {weight:.2f} kg")
            
        except Exception as e:
            print(f"Ağaca ekleme hatası: {str(e)}")
            QMessageBox.warning(self, "Hata", f"Sonuç ağaca eklenirken hata oluştu: {str(e)}")
            
    def update_summary(self):
        """Özet bilgileri güncelle"""
        try:
            # Calculator'da özeti göster ve logla
            self.acad.calculator.show_summary()
            self.acad.calculator.log_summary()
            
            # Genel toplamı güncelle
            if self.acad.calculator.results:
                total_weight = sum(r.total_weight for r in self.acad.calculator.results)
                self.total_label.setText(f"Genel Toplam: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)")
            
            # Log alanını en alta kaydır
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            QMessageBox.warning(self, "Özet Güncelleme Hatası", str(e))

    def new_project(self):
        """Yeni proje başlat"""
        try:
            reply = QMessageBox.question(self, 'Yeni Proje', 
                                       'Mevcut hesaplamalar silinecek. Emin misiniz?',
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                # Sonuçları temizle
                self.acad.calculator.results.clear()
                self.result_tree.clear()
                # Genel toplamı sıfırla
                self.total_label.setText("Genel Toplam: 0.00 kg (0.000 ton)")
                self.statusBar.showMessage("Yeni proje başlatıldı")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def save_project(self):
        """Projeyi kaydet"""
        try:
            if not self.acad.calculator.results:
                QMessageBox.warning(self, "Uyarı", "Kaydedilecek sonuç bulunamadı!")
                return
            
            # Ana dizin kontrolü
            if not os.path.exists('metraj_raporlari'):
                os.makedirs('metraj_raporlari')
            
            # Kategori klasörleri ve etiketleri
            categories = {
                'REBAR': {'folder': 'boy_demirleri', 'label': 'BOY DEMİRLERİ'},
                'STIRRUP': {'folder': 'etriyeler', 'label': 'ETRİYELER'},
                'CONNECTION': {'folder': 'ara_baglanti', 'label': 'ARA BAĞLANTILAR'},
                'WALL': {'folder': 'perde_hasir', 'label': 'PERDE HASIRLARI'},
                'SLAB': {'folder': 'doseme_hasir', 'label': 'DÖŞEME HASIRLARI'}
            }
            
            # Her kategori için klasör oluştur
            for cat_info in categories.values():
                folder_path = os.path.join('metraj_raporlari', cat_info['folder'])
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
            
            # Sonuçları kategorilere ayır
            categorized_results = {}
            for result in self.acad.calculator.results:
                if result.type not in categorized_results:
                    categorized_results[result.type] = []
                categorized_results[result.type].append(result)
            
            # Timestamp oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_files = []
            
            # Her kategori için ayrı dosya oluştur
            for cat_type, results in categorized_results.items():
                if results and cat_type in categories:
                    cat_info = categories[cat_type]
                    filename = f"metraj_{cat_info['folder']}_{timestamp}.txt"
                    filepath = os.path.join('metraj_raporlari', cat_info['folder'], filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"METRAJ RAPORU - {cat_info['label']}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        # Kategori toplamları
                        total_weight = 0
                        total_length = 0
                        total_area = 0
                        
                        # Her sonuç için detayları yaz
                        for result in results:
                            f.write(f"Tip: {result.description}\n")
                            if cat_type in ['WALL', 'SLAB']:
                                f.write(f"Alan: {result.area:.2f} m²\n")
                                total_area += result.area
                            else:
                                f.write(f"Çap: Ø{result.diameter}\n")
                                if result.spacing:
                                    f.write(f"Aralık: {result.spacing} cm\n")
                                f.write(f"Boy: {result.length} cm\n")
                                f.write(f"Adet: {result.count}\n")
                                f.write(f"Toplam Boy: {result.total_length/100:.2f} m\n")
                                total_length += result.total_length
                            
                            f.write(f"Birim Ağırlık: {result.weight_per_meter:.3f} kg/mt\n")
                            f.write(f"Toplam Ağırlık: {result.total_weight:.2f} kg\n")
                            f.write("-" * 30 + "\n")
                            total_weight += result.total_weight
                        
                        # Kategori özeti
                        f.write("\nKATEGORİ TOPLAMI\n")
                        f.write("=" * 30 + "\n")
                        if cat_type in ['WALL', 'SLAB']:
                            f.write(f"Toplam Alan: {total_area:.2f} m²\n")
                        else:
                            f.write(f"Toplam Boy: {total_length/100:.2f} m\n")
                        f.write(f"Toplam Ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)\n")
                    
                    saved_files.append(filepath)
            
            # Genel toplam dosyası
            total_filename = f"metraj_genel_toplam_{timestamp}.txt"
            total_filepath = os.path.join('metraj_raporlari', total_filename)
            
            with open(total_filepath, 'w', encoding='utf-8') as f:
                f.write("GENEL METRAJ RAPORU\n")
                f.write("=" * 50 + "\n\n")
                
                grand_total = 0
                for cat_type, results in categorized_results.items():
                    if results and cat_type in categories:
                        cat_total = sum(r.total_weight for r in results)
                        grand_total += cat_total
                        f.write(f"{categories[cat_type]['label']}:\n")
                        f.write(f"Toplam Ağırlık: {cat_total:.2f} kg\n")
                        f.write("-" * 30 + "\n")
                
                f.write(f"\nGENEL TOPLAM: {grand_total:.2f} kg ({grand_total/1000:.3f} ton)\n")
            
            saved_files.append(total_filepath)
            
            # Başarı mesajı
            message = "Dosyalar kaydedildi:\n\n" + "\n".join(saved_files)
            QMessageBox.information(self, "Kayıt Başarılı", message)
            self.statusBar.showMessage(f"Metraj raporları kaydedildi: {timestamp}")
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def generate_report(self):
        """Detaylı rapor oluştur"""
        try:
            if not self.acad.calculator.results:
                QMessageBox.warning(self, "Uyarı", "Henüz hesaplanmış sonuç yok!")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Metraj Raporu")
            dialog.setGeometry(200, 200, 800, 600)
            
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            # Rapor içeriğini oluştur
            report = "DEMIR METRAJI RAPORU\n"
            report += "=" * 50 + "\n\n"
            
            # Kategorilere göre sonuçları ekle
            categories = {
                'REBAR': 'BOY DEMİRLERİ',
                'STIRRUP': 'ETRİYELER',
                'CONNECTION': 'ARA BAĞLANTILAR',
                'WALL': 'PERDE HASIRLARI',
                'SLAB': 'DÖŞEME HASIRLARI'
            }
            
            for result in self.acad.calculator.results:
                report += f"\n{categories.get(result.type, 'DİĞER')}:\n"
                report += "-" * 30 + "\n"
                report += f"Tip: {result.description}\n"
                if result.type in ['WALL', 'SLAB']:
                    report += f"Alan: {result.area:.2f} m²\n"
                else:
                    report += f"Çap: Ø{result.diameter}\n"
                    if result.spacing:
                        report += f"Aralık: {result.spacing} cm\n"
                    report += f"Boy: {result.length} cm\n"
                    report += f"Adet: {result.count}\n"
                    report += f"Toplam Boy: {result.total_length/100:.2f} m\n"
                report += f"Birim Ağırlık: {result.weight_per_meter:.3f} kg/mt\n"
                report += f"Toplam Ağırlık: {result.total_weight:.2f} kg\n"
            
            # Özet ekle
            report += "\nÖZET\n" + "=" * 30 + "\n"
            total_weight = sum(r.total_weight for r in self.acad.calculator.results)
            report += f"Toplam Ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)\n"
            
            text_edit.setText(report)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def start_stirrup_selection(self):
        """Etriye seçim işlemini başlat"""
        # İşlem seçim dialogu
        dialog = QDialog(self)
        dialog.setWindowTitle("İşlem Seçimi")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        
        # İşlem seçenekleri
        layout.addWidget(QLabel("Yapmak istediğiniz işlemi seçin:"))
        
        btn_new = QPushButton("Yeni Etriye Seçimi")
        btn_continue = QPushButton("Mevcut Seçimleri Hesapla")
        btn_cancel = QPushButton("İptal")
        
        layout.addWidget(btn_new)
        layout.addWidget(btn_continue)
        layout.addWidget(btn_cancel)
        
        def start_new():
            dialog.accept()
            self.start_new_stirrup_selection()
        
        def continue_calc():
            dialog.accept()
            self.calculate_results()
        
        def cancel_op():
            dialog.reject()
        
        btn_new.clicked.connect(start_new)
        btn_continue.clicked.connect(continue_calc)
        btn_cancel.clicked.connect(cancel_op)
        
        dialog.exec()

    def start_new_stirrup_selection(self):
        """Yeni etriye seçim işlemini başlat"""
        # İşlem durumunu güncelle
        self.is_operation_running = True
        self.current_operation = 'STIRRUP'
        
        # Butonları güncelle
        self.btn_stop.setEnabled(True)
        self.btn_calculate.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        
        # İşlem butonlarını devre dışı bırak
        self.btn_rebar.setEnabled(False)
        self.btn_stirrup.setEnabled(False)
        self.btn_mesh.setEnabled(False)
        self.btn_connection.setEnabled(False)
        
        self.statusBar.showMessage("Etriye seçimi başlatıldı... (Q tuşu ile seçimi sonlandırabilirsiniz)")
        
        try:
            while self.is_operation_running:
                # İşlem seçim dialogu
                dialog = QDialog(self)
                dialog.setWindowTitle("Etriye Seçim İşlemi")
                dialog.setMinimumWidth(300)
                layout = QVBoxLayout(dialog)
                
                layout.addWidget(QLabel("Ne yapmak istiyorsunuz?"))
                
                btn_select = QPushButton("Yeni Etriye Seç")
                btn_calc = QPushButton("Seçimleri Hesapla")
                btn_finish = QPushButton("İşlemi Bitir")
                
                layout.addWidget(btn_select)
                layout.addWidget(btn_calc)
                layout.addWidget(btn_finish)
                
                result = [None]  # Dialog sonucunu tutmak için liste
                
                def do_select():
                    result[0] = "select"
                    dialog.accept()
                
                def do_calc():
                    result[0] = "calc"
                    dialog.accept()
                
                def do_finish():
                    result[0] = "finish"
                    dialog.accept()
                
                btn_select.clicked.connect(do_select)
                btn_calc.clicked.connect(do_calc)
                btn_finish.clicked.connect(do_finish)
                
                dialog.exec()
                
                if result[0] == "select":
                    # Etriye seçim işlemi
                    success = self.select_single_stirrup()
                    if not success:
                        continue
                elif result[0] == "calc":
                    self.calculate_results()
                else:  # finish
                    break
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            self.stop_current_operation()

    def select_single_stirrup(self):
        """Tek bir etriye seçimi yap"""
        try:
            # Etriye text seçimi
            text = self.acad.select_entity("Etriye seçin")
            if not text:
                return False
            
            # Text içinde L= yoksa boy uzunluğu iste
            length_text = None
            if not self.acad.calculator.extract_length(text):
                length_text = self.acad.select_entity("Boy uzunluğunu seçin")
                if not length_text:
                    return False
            
            # Aralık seçimi
            spacing_text = self.acad.select_entity("Aralık textini seçin")
            if not spacing_text:
                return False
            
            # Dimension seçimi
            dimension = self.acad.select_entity("Dimension ölçüsünü seçin")
            if dimension is None:
                return False
            
            # Seçimleri kaydet
            self.current_selections.append({
                'text': text,
                'length_text': length_text,
                'spacing_text': spacing_text,
                'dimension': dimension,
                'type': 'STIRRUP'
            })
            
            # Her seçimden sonra hesapla
            if self.calculate_current_selection(self.current_selections[-1]):
                self.statusBar.showMessage(f"{len(self.current_selections)} adet etriye hesaplandı.")
                return True
            
            return False
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
            return False

    def calculate_current_selection(self, selection):
        """Mevcut seçimi hesapla"""
        try:
            text = selection['text']
            if selection['length_text']:
                text += " " + selection['length_text']
            
            if selection['type'] == 'STIRRUP':
                if (self.acad.calculator.process_text(text) and 
                    self.acad.calculator.process_text(selection['spacing_text'])):
                    self.acad.calculator.process_dimension(float(selection['dimension']))
                    self.add_result_to_tree("Etriye", text)
                    self.update_summary()
                    return True
        except Exception as e:
            print(f"Hesaplama hatası: {str(e)}")
            return False

    def calculate_results(self):
        """Tüm seçimleri hesapla"""
        try:
            if not self.current_selections:
                QMessageBox.warning(self, "Uyarı", "Hesaplanacak seçim bulunamadı!")
                return
            
            success_count = 0
            for selection in self.current_selections:
                try:
                    text = selection['text']
                    if selection['length_text']:
                        text += " " + selection['length_text']
                    
                    if selection['type'] == 'STIRRUP':
                        # Etriye hesaplama işlemi
                        if self.acad.calculator.process_text(text):
                            print(f"Etriye text işlendi: {text}")
                            
                            if self.acad.calculator.process_text(selection['spacing_text']):
                                print(f"Aralık text işlendi: {selection['spacing_text']}")
                                
                                dimension = float(selection['dimension'])
                                if self.acad.calculator.process_dimension(dimension):
                                    print(f"Dimension işlendi: {dimension}")
                                    
                                    # Sonucu ağaca ekle
                                    self.add_result_to_tree("Etriye", text)
                                    success_count += 1
                                    print(f"Etriye başarıyla hesaplandı: {text}")
                                    
                                    # Her başarılı hesaplamadan sonra özeti güncelle
                                    self.update_summary()
                                else:
                                    print("Dimension işlenemedi!")
                            else:
                                print("Aralık text işlenemedi!")
                        else:
                            print("Etriye text işlenemedi!")
                    
                    # GUI güncellemelerini yap
                    QApplication.processEvents()
                    
                except Exception as calc_error:
                    print(f"Hesaplama hatası: {str(calc_error)}")
                    QMessageBox.warning(self, "Hesaplama Hatası", str(calc_error))
            
            # Son durumu göster
            if success_count > 0:
                message = f"{success_count} adet etriye başarıyla hesaplandı."
                QMessageBox.information(self, "Hesaplama Tamamlandı", message)
                self.statusBar.showMessage(message)
                
                # Genel toplamı güncelle
                total_weight = sum(r.total_weight for r in self.acad.calculator.results)
                self.total_label.setText(f"Genel Toplam: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)")
            else:
                QMessageBox.warning(self, "Uyarı", "Hiçbir hesaplama yapılamadı!")
            
        except Exception as e:
            print(f"Genel hata: {str(e)}")
            QMessageBox.warning(self, "Hesaplama Hatası", str(e))

    def start_mesh_selection(self):
        self.is_operation_running = True
        self.current_operation = 'MESH'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Hasır seçimi başlatıldı...")
        try:
            # Hasır tipi seçimi
            dialog = QDialog(self)
            dialog.setWindowTitle("Hasır Tipi Seçimi")
            layout = QVBoxLayout(dialog)
            
            btn_slab = QPushButton("Döşeme Hasırı")
            btn_wall = QPushButton("Perde Hasırı")
            
            layout.addWidget(btn_slab)
            layout.addWidget(btn_wall)
            
            def start_slab():
                dialog.accept()
                self.process_mesh_selection('SLAB')
                
            def start_wall():
                dialog.accept()
                self.process_mesh_selection('WALL')
                
            btn_slab.clicked.connect(start_slab)
            btn_wall.clicked.connect(start_wall)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def process_mesh_selection(self, mesh_type):
        """Hasır seçim işlemini yönet"""
        try:
            while True:
                if mesh_type == 'WALL':
                    # Perde hasır seçimi
                    text = self.acad.select_entity("Perde hasır tipini seçin (örn: 2xQ257/257) veya çıkmak için ESC")
                    if not text:
                        break
                    
                    dim_text = self.acad.select_entity("Boyutları seçin (örn: 215x267)")
                    if not dim_text:
                        break
                    
                    if self.acad.calculator.process_wall_mesh(text, dim_text):
                        self.add_result_to_tree("Perde Hasır", f"{text} - {dim_text}")
                    else:
                        retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                        if retry.upper() != 'E':
                            break
                else:
                    # Döşeme hasır seçimi
                    text = self.acad.select_entity("Döşeme hasır tipini seçin (örn: Q257/257 450/215) veya çıkmak için ESC")
                    if not text:
                        break
                    
                    if self.acad.calculator.process_slab_mesh(text):
                        self.add_result_to_tree("Döşeme Hasır", text)
                    else:
                        retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                        if retry.upper() != 'E':
                            break
            
            self.update_summary()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def start_connection_selection(self):
        self.is_operation_running = True
        self.current_operation = 'CONNECTION'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Ara bağlantı seçimi başlatıldı...")
        try:
            while True:
                # Ara bağlantı text seçimi
                text = self.acad.select_entity("Ara bağlantı seçin (örn: 2X∅12/15 L=185) veya çıkmak için ESC")
                if not text:
                    break
                
                # Text içinde L= yoksa boy uzunluğu iste
                if not self.acad.calculator.extract_length(text):
                    length_text = self.acad.select_entity("Boy uzunluğunu seçin")
                    if not length_text:
                        break
                    text = text + " " + length_text
                
                # Dimension seçimi
                dimension = self.acad.select_entity("Dimension ölçüsünü seçin")
                if dimension is None:
                    break
                
                # Hesaplama ve sonuç ekleme
                if self.acad.calculator.process_connection_rebar(text, None, float(dimension)):
                    self.add_result_to_tree("Ara Bağlantı", text)
            
            self.update_summary()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def stop_current_operation(self):
        """Mevcut işlemi durdur"""
        try:
            # Seçim thread'ini durdur
            if self.selection_thread:
                self.selection_thread.stop()
                self.selection_thread.wait()
                self.selection_thread = None
            
            # İşlem durumunu güncelle
            self.is_operation_running = False
            self.current_operation = None
            
            # Butonları aktif et
            self.btn_stop.setEnabled(True)     # Her zaman aktif
            self.btn_calculate.setEnabled(True) # Her zaman aktif
            self.btn_refresh.setEnabled(True)   # Her zaman aktif
            self.btn_rebar.setEnabled(True)
            self.btn_stirrup.setEnabled(True)
            self.btn_mesh.setEnabled(True)
            self.btn_connection.setEnabled(True)
            
            # Özeti güncelle
            self.update_summary()
            self.statusBar.showMessage("İşlem durduruldu ve özet güncellendi")
            
            # Kaydetmek isteyip istemediğini sor
            if self.current_selections:  # Seçim varsa sor
                reply = QMessageBox.question(
                    self,
                    'İşlemi Durdur',
                    'Mevcut işlemi kaydetmek istiyor musunuz?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.save_project()
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İşlem durdurulurken hata oluştu: {str(e)}")

    def setup_log_handler(self):
        """GUI log handler'ını ayarla"""
        def log_to_gui(message):
            self.log_text.append(message)
            # Otomatik olarak en alta kaydır
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # GUI handler'ı oluştur ve bağla
        gui_handler = logging.Handler()
        gui_handler.emit = lambda record: log_to_gui(gui_handler.format(record))
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        
        # Calculator'a handler'ı ekle
        self.acad.calculator.logger.addHandler(gui_handler)
        self.acad.calculator.gui_handler = gui_handler

    def refresh_application(self):
        """Uygulamayı yenile"""
        try:
            # Kullanıcıya sor
            reply = QMessageBox.question(
                self,
                'Yenile',
                'Tüm işlemler sıfırlanacak ve AutoCAD bağlantısı yenilenecek. Devam etmek istiyor musunuz?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # AutoCAD bağlantısını yenile
                if self.acad.reconnect_autocad():
                    # Tüm verileri sıfırla
                    self.acad.calculator.results.clear()
                    self.result_tree.clear()
                    self.current_selections = []
                    self.log_text.clear()
                    
                    # Butonları varsayılan duruma getir
                    self.btn_calculate.setEnabled(False)
                    self.btn_stop.setEnabled(False)
                    self.btn_rebar.setEnabled(True)
                    self.btn_stirrup.setEnabled(True)
                    self.btn_mesh.setEnabled(True)
                    self.btn_connection.setEnabled(True)
                    
                    # İşlem durumunu sıfırla
                    self.is_operation_running = False
                    self.current_operation = None
                    
                    # Genel toplamı sıfırla
                    self.total_label.setText("Genel Toplam: 0.00 kg (0.000 ton)")
                    
                    # Kullanıcıya bilgi ver
                    self.statusBar.showMessage("Uygulama başarıyla yenilendi!")
                    QMessageBox.information(self, "Başarılı", "Uygulama yenilendi ve tüm veriler sıfırlandı.")
                else:
                    QMessageBox.warning(self, "Hata", "AutoCAD bağlantısı yenilenemedi!")
                    
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yenileme sırasında hata oluştu: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = RebarCalculatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 