from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                           QTreeWidgetItem, QStatusBar, QMessageBox, QFileDialog,
                           QDialog, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
import sys
from autocad_integration import AutoCADIntegration
from rebar_calculator import RebarData
import os
from datetime import datetime
import logging
import re

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
        """Boy demiri seçim işlemini yönet"""
        self.is_operation_running = True
        self.current_operation = 'REBAR'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Boy demiri seçimi başlatıldı...")
        
        try:
            # 1. Boy demiri text seçimi
            rebar_text = self.acad.select_entity("Boy demiri textini seçin (örn: 2X13∅20)")
            if not rebar_text:
                return
            
            # Çap ve adet bilgilerini çıkar
            pattern = r'(\d+)X(\d+)[ƒØ∅](\d+)|(\d+)X(\d+)%%C(\d+)'
            match = re.search(pattern, rebar_text)
            
            if not match:
                print("Geçersiz boy demiri formatı!")
                return
            
            # Grupları kontrol et ve değerleri al
            groups = match.groups()
            if groups[0]:  # İlk format (ƒØ∅)
                count = int(groups[0]) * int(groups[1])
                diameter = float(groups[2])
            else:  # İkinci format (%%C)
                count = int(groups[3]) * int(groups[4])
                diameter = float(groups[5])
            
            print("\nBoy Demiri Bilgileri:")
            print(f"- Çap: Ø{diameter}")
            print(f"- Adet: {count}")
            
            # 2. Boy uzunluğu seçimi
            length_text = self.acad.select_entity("Boy uzunluğunu seçin (örn: L=397)")
            if not length_text:
                return
            
            length_match = re.search(r'[Ll]\s*=\s*(\d+)', length_text)
            if not length_match:
                print("Geçersiz boy formatı!")
                return
            
            length = float(length_match.group(1))
            print(f"- Boy: {length} cm")
            
            # Hesaplamaları yap
            print("\nHESAPLAMA SONUÇLARI:")
            print("--------------------")
            
            # 1. Toplam boy hesabı
            total_length = length * count
            print(f"1. Toplam boy: {total_length} cm = {total_length/100:.2f} m")
            print(f"   {length} cm × {count} adet = {total_length} cm")
            
            # 2. Ağırlık hesabı
            weight_per_meter = self.acad.calculator.weight_table.get(diameter, 0)
            total_weight = (total_length / 100) * weight_per_meter
            print(f"2. Toplam ağırlık: {total_weight:.2f} kg")
            print(f"   {total_length/100:.2f} m × {weight_per_meter:.3f} kg/m = {total_weight:.2f} kg")
            
            # Sonucu kaydet
            result = RebarData(
                type='REBAR',
                diameter=diameter,
                count=count,
                length=length,
                total_length=total_length,
                weight_per_meter=weight_per_meter,
                total_weight=total_weight,
                description=f"{count}×Ø{diameter} L={length}",
                spacing=None  # Boy demiri için spacing None olabilir
            )
            
            self.acad.calculator.results.append(result)
            print("\nHesaplama başarıyla kaydedildi!")
            
            # GUI'yi güncelle
            self.add_result_to_tree("Boy Demiri", f"{count}×Ø{diameter} L={length}")
            self.update_summary()
            self.statusBar.showMessage("Boy demiri hesabı tamamlandı!")
            
            # Metraj raporunu kaydet
            self.save_metraj_report()
            
        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            self.statusBar.showMessage("Hata oluştu!")

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
                
                # Log alanını güncelle (pop-up olmadan)
                self.log_text.append(f"\nYeni hesaplama eklendi: {type_name} - {details} - {weight:.2f} kg")
            
        except Exception as e:
            print(f"Ağaca ekleme hatası: {str(e)}")
            # Pop-up mesajını kaldırdık
            # QMessageBox.warning(self, "Hata", f"Sonuç ağaca eklenirken hata oluştu: {str(e)}")
            
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
        """Etriye seçim işlemini yönet"""
        self.is_operation_running = True
        self.current_operation = 'STIRRUP'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Etriye seçimi başlatıldı...")
        
        while self.is_operation_running:  # Sürekli seçim için döngü
            try:
                # 1. İlk seçim - Etriye bilgileri
                etriye_text = self.acad.select_entity("Etriye textini seçin (örn: ƒ10 Etr. l=168)")
                if not etriye_text:
                    break  # Seçim iptal edilirse döngüden çık
                
                # Çap ve boy bilgilerini çıkar
                diameter_match = re.search(r'[ƒØ∅](\d+)|%%C(\d+)', etriye_text)
                length_match = re.search(r'[Ll]\s*=\s*(\d+)', etriye_text)
                
                if not (diameter_match and length_match):
                    print("Geçersiz etriye formatı!")
                    break
                
                diameter = float(diameter_match.group(1) or diameter_match.group(2))
                length = float(length_match.group(1))
                
                print("\nEtriye Bilgileri:")
                print(f"- Çap: Ø{diameter}")
                print(f"- Boy: {length} cm")
                
                # 2. İkinci seçim - Aralık bilgisi
                spacing_text = self.acad.select_entity("Aralık textini seçin (örn: Etr.%%C10/8)")
                if not spacing_text:
                    break
                
                spacing_match = re.search(r'/(\d+)', spacing_text)
                if not spacing_match:
                    print("Geçersiz aralık formatı!")
                    break
                
                spacing = float(spacing_match.group(1))
                print(f"- Aralık: {spacing} cm")
                
                # 3. Üçüncü seçim - Dimension
                dimension = self.acad.select_entity("Dimension ölçüsünü seçin")
                if dimension is None:
                    break
                
                try:
                    total_length = float(dimension)
                except:
                    print("Geçersiz dimension değeri!")
                    break
                
                print(f"- Toplam Uzunluk: {total_length} cm")
                
                # Hesaplamaları yap
                print("\nHESAPLAMA SONUÇLARI:")
                print("--------------------")
                
                # 1. Etriye adedi hesabı
                count = int((total_length / spacing) + 1)
                print(f"1. Etriye adedi: {count} adet")
                print(f"   {total_length} cm ÷ {spacing} cm = {count} adet")
                
                # 2. Toplam boy hesabı
                total_length_all = length * count
                print(f"2. Toplam boy: {total_length_all} cm = {total_length_all/100:.2f} m")
                print(f"   {length} cm × {count} adet = {total_length_all} cm")
                
                # 3. Ağırlık hesabı
                weight_per_meter = self.acad.calculator.weight_table.get(diameter, 0)
                total_weight = (total_length_all / 100) * weight_per_meter
                print(f"3. Toplam ağırlık: {total_weight:.2f} kg")
                print(f"   {total_length_all/100:.2f} m × {weight_per_meter:.3f} kg/m = {total_weight:.2f} kg")
                
                # Sonucu kaydet
                result = RebarData(
                    type='STIRRUP',
                    diameter=diameter,
                    spacing=spacing,
                    length=length,
                    count=count,
                    total_length=total_length_all,
                    weight_per_meter=weight_per_meter,
                    total_weight=total_weight,
                    description=f"Etriye Ø{diameter}/{spacing} L={length}"
                )
                
                self.acad.calculator.results.append(result)
                print("\nHesaplama başarıyla kaydedildi!")
                
                # GUI'yi güncelle
                self.add_result_to_tree("Etriye", f"Ø{diameter}/{spacing} L={length}")
                self.update_summary()
                
                # Metraj raporunu kaydet
                self.save_metraj_report()
                
                # Kullanıcıya devam edip etmeyeceğini sor
                reply = QMessageBox.question(
                    self,
                    'Devam Et',
                    'Başka etriye seçmek istiyor musunuz?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    print("\nEtriye hesaplaması tamamlandı.")
                    break
                else:
                    print("\nBir sonraki etriye için seçime devam edin...")
            
            except Exception as e:
                print(f"\nHata oluştu: {str(e)}")
                self.statusBar.showMessage("Hata oluştu!")
                break
        
        # İşlem durumunu sıfırla
        self.is_operation_running = False
        self.current_operation = None
        self.btn_stop.setEnabled(False)
        self.statusBar.showMessage("Etriye hesabı tamamlandı!")

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
            print(f"\nDöşeme hasırlarını seçin (Seçimi tamamladıktan sonra ENTER'a basın)")
            
            # Seçilen textleri al
            selected_texts = self.acad.select_texts()
            if not selected_texts:
                return
            
            print("\nHasır hesaplamaları başlıyor...")
            
            for mesh_text in selected_texts:
                try:
                    # Q ve R tipi hasır formatı: "Q257/257  450/215" şeklinde
                    match = re.search(r'([QR]\d+(?:/\d+)?)\s*(\d+)/(\d+)', mesh_text)
                    if match:
                        mesh_code = match.group(1)  # Q257/257
                        width = float(match.group(2))  # 450
                        height = float(match.group(3))  # 215
                        
                        print(f"\nHasır tipi: {mesh_code}")
                        print(f"Boyutlar: {width}x{height} cm")
                        
                        # Hesaplamayı yap
                        if self.acad.calculator.calculate_mesh(mesh_code, width, height):
                            # GUI'yi güncelle - Burayı ekledik
                            result = self.acad.calculator.results[-1]  # Son eklenen sonuç
                            item = QTreeWidgetItem(self.result_tree)
                            item.setText(0, "Döşeme Hasırı")
                            item.setText(1, f"{result.mesh_code} {result.width}×{result.height}")
                            item.setText(2, f"{result.total_weight:.2f} kg")
                            
                            # Özeti güncelle
                            self.update_summary()
                            
                except Exception as e:
                    print(f"Hasır işleme hatası ({mesh_text}): {str(e)}")
                    continue
            
            print("\nAutoCAD güncelleniyor...")
            self.statusBar.showMessage("İşlem başarıyla tamamlandı!")
            
        except Exception as e:
            print(f"\nHata: {str(e)}")
            self.statusBar.showMessage("Hata oluştu!")

    def start_connection_selection(self):
        """Ara bağlantı seçim işlemini yönet"""
        self.is_operation_running = True
        self.current_operation = 'CONNECTION'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Ara bağlantı seçimi başlatıldı...")
        
        try:
            # 1. Ara bağlantı text seçimi
            conn_text = self.acad.select_entity("Ara bağlantı textini seçin (örn: 2X∅12/15)")
            if not conn_text:
                return
            
            # Çap ve adet bilgilerini çıkar
            pattern = r'(\d+)X[ƒØ∅](\d+)/(\d+)'
            match = re.search(pattern, conn_text)
            
            if not match:
                print("Geçersiz ara bağlantı formatı!")
                return
            
            count = int(match.group(1))
            diameter = float(match.group(2))
            spacing = float(match.group(3))
            
            print("\nAra Bağlantı Bilgileri:")
            print(f"- Çap: Ø{diameter}")
            print(f"- Adet: {count}")
            print(f"- Aralık: {spacing} cm")
            
            # 2. Boy uzunluğu seçimi
            length_text = self.acad.select_entity("Boy uzunluğunu seçin (örn: L=185)")
            if not length_text:
                return
            
            length_match = re.search(r'[Ll]\s*=\s*(\d+)', length_text)
            if not length_match:
                print("Geçersiz boy formatı!")
                return
            
            length = float(length_match.group(1))
            print(f"- Boy: {length} cm")
            
            # Hesaplamaları yap
            print("\nHESAPLAMA SONUÇLARI:")
            print("--------------------")
            
            # Toplam boy hesabı
            total_length = length * count
            print(f"1. Toplam boy: {total_length} cm = {total_length/100:.2f} m")
            print(f"   {length} cm × {count} adet = {total_length} cm")
            
            # Ağırlık hesabı
            weight_per_meter = self.acad.calculator.weight_table.get(diameter, 0)
            total_weight = (total_length / 100) * weight_per_meter
            print(f"2. Toplam ağırlık: {total_weight:.2f} kg")
            print(f"   {total_length/100:.2f} m × {weight_per_meter:.3f} kg/m = {total_weight:.2f} kg")
            
            # Sonucu kaydet
            result = RebarData(
                type='CONNECTION',
                diameter=diameter,
                length=length,
                count=count,
                total_length=total_length,
                weight_per_meter=weight_per_meter,
                total_weight=total_weight,
                description=f"{count}×Ø{diameter}/15 L={length}",
                spacing=spacing
            )
            
            self.acad.calculator.results.append(result)
            print("\nHesaplama başarıyla kaydedildi!")
            
            # GUI'yi güncelle
            self.add_result_to_tree("Ara Bağlantı", f"{count}×Ø{diameter}/15 L={length}")
            self.update_summary()
            self.statusBar.showMessage("Ara bağlantı hesabı tamamlandı!")
            
            # Metraj raporunu kaydet
            self.save_metraj_report()
            
        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            self.statusBar.showMessage("Hata oluştu!")

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
            
            # Mevcut işlem için son raporu kaydet
            if self.current_operation == 'STIRRUP':
                print("\nEtriye hesabı durduruluyor...")
                self.save_metraj_report()
                print("Etriye hesabı kaydedildi.")
            elif self.current_operation == 'REBAR':
                print("\nBoy demiri hesabı durduruluyor...")
                self.save_metraj_report()
                print("Boy demiri hesabı kaydedildi.")
            
            # İşlem tipini sıfırla
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
            
            # Kullanıcıya bilgi ver
            message = "İşlem durduruldu ve hesaplamalar kaydedildi.\n\n"
            message += "Yeni bir hesaplama yapmak için:\n"
            message += "1. Boy Demiri\n"
            message += "2. Etriye\n"
            message += "3. Hasır\n"
            message += "4. Ara Bağlantı\n"
            message += "\nSeçeneklerinden birini seçebilirsiniz."
            
            QMessageBox.information(
                self,
                'İşlem Durduruldu',
                message
            )
            
            self.statusBar.showMessage("İşlem durduruldu ve hesaplamalar kaydedildi. Yeni bir hesaplama seçebilirsiniz.")
            
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

    def calculate_results(self):
        """Seçilen öğelerin hesaplamasını yap"""
        try:
            if not self.acad.calculator.results:
                QMessageBox.warning(self, "Uyarı", "Henüz hesaplanmış sonuç yok!")
                return
            
            # Özeti güncelle
            self.update_summary()
            
            # Başarı mesajı
            total_weight = sum(r.total_weight for r in self.acad.calculator.results)
            message = f"Hesaplama tamamlandı!\n\nToplam Ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)"
            QMessageBox.information(self, "Başarılı", message)
            
            self.statusBar.showMessage("Hesaplama tamamlandı!")
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
            self.statusBar.showMessage("Hesaplama sırasında hata oluştu!")

    def save_metraj_report(self):
        """Metraj raporunu kaydet"""
        try:
            # Rapor klasörü oluştur
            today = datetime.now().strftime('%Y-%m-%d')
            report_dir = f"metraj_raporlari_{today}"
            print(f"\nDEBUG: Rapor dizini: {report_dir}")
            
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            # Kategori dosyaları
            files = {
                'REBAR': os.path.join(report_dir, "boy_demirleri.txt"),
                'STIRRUP': os.path.join(report_dir, "etriyeler.txt"),
                'MESH_WALL': os.path.join(report_dir, "perde_hasirlari.txt"),
                'MESH_SLAB': os.path.join(report_dir, "doseme_hasirlari.txt"),
                'CONNECTION': os.path.join(report_dir, "ara_baglanti.txt")
            }
            
            print("\nDEBUG: Tüm sonuçlar:")
            for r in self.acad.calculator.results:
                print(f"- Tip: {r.type}, Açıklama: {r.description}")
            
            # Her kategori için rapor oluştur
            for category, filename in files.items():
                print(f"\nDEBUG: Kategori işleniyor: {category}")
                
                # Sonuçları filtrele
                results = [r for r in self.acad.calculator.results if r.type == category]
                
                if not results:
                    print(f"DEBUG: {category} için sonuç bulunamadı")
                    continue
                
                print(f"DEBUG: {len(results)} sonuç bulundu")
                
                # Rapor dosyasını oluştur
                with open(filename, 'w', encoding='utf-8') as f:
                    # Başlık
                    if category == 'MESH_WALL':
                        f.write("\nPERDE HASIRLARI RAPORU\n")
                    elif category == 'MESH_SLAB':
                        f.write("\nDÖŞEME HASIRLARI RAPORU\n")
                    elif category == 'REBAR':
                        f.write("\nBOY DEMİRLERİ RAPORU\n")
                    elif category == 'STIRRUP':
                        f.write("\nETRİYE RAPORU\n")
                    f.write("="*50 + "\n\n")
                    
                    # Tarih ve saat bilgisi
                    f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Çapa göre grupla
                    by_diameter = {}
                    for r in results:
                        if r.diameter not in by_diameter:
                            by_diameter[r.diameter] = []
                        by_diameter[r.diameter].append(r)
                    
                    # Her çap için detayları yaz
                    for diameter, items in by_diameter.items():
                        total_count = sum(r.count for r in items)
                        total_weight = sum(r.total_weight for r in items)
                        
                        f.write(f"Ø{diameter}:\n")
                        f.write(f"- Toplam Boy: 0.00 m\n")
                        f.write(f"- Toplam Adet: {total_count} adet\n")
                        f.write(f"- Toplam Ağırlık: {total_weight:.2f} kg\n\n")
                        
                        # Her hasır için detay
                        for r in items:
                            area = (r.width * r.height)/10000
                            f.write(f"  * Hasır {r.description}\n")
                            f.write(f"    Alan: {area:.2f} m², Ağırlık: {r.total_weight:.2f} kg\n")
                        f.write("\n")
                    
                    # Kategori toplamı
                    category_weight = sum(r.total_weight for r in results)
                    category_area = sum((r.width * r.height)/10000 for r in results)
                    
                    f.write("\nKategori Toplamı:\n")
                    f.write("="*30 + "\n")
                    f.write(f"Toplam Alan: {category_area:.2f} m²\n")
                    f.write(f"Toplam Ağırlık: {category_weight:.2f} kg ({category_weight/1000:.3f} ton)\n")
                
                print(f"DEBUG: {filename} dosyası oluşturuldu")
            
            print("\nDEBUG: Tüm raporlar tamamlandı")
            
        except Exception as e:
            print(f"\nDEBUG: Hata: {str(e)}")
            import traceback
            traceback.print_exc()

    def get_mesh_properties(self, mesh_code):
        """Hasır özelliklerini al"""
        try:
            # Q tipi hasırlar için çap ve aralık tablosu
            mesh_properties = {
                'Q106': (4.0, 15),  # (çap, aralık)
                'Q131': (4.5, 15),
                'Q158': (5.0, 15),
                'Q188': (5.5, 15),
                'Q221': (6.0, 15),
                'Q257': (6.5, 15),
                'Q295': (7.0, 15),
                'Q317': (7.2, 15),
                'Q335': (7.4, 15),
                'Q377': (7.9, 15),
                'Q424': (8.4, 15),
                'Q503': (9.1, 15),
                'Q513': (9.2, 15),
                'Q524': (9.3, 15),
                'Q589': (9.8, 15),
                'Q636': (10.2, 15),
                'Q785': (11.4, 15),
                
                # TR tipi hasırlar için
                'TR131': (4.5, 15),
                'TR158': (5.0, 15),
                'TR188': (5.5, 15),
                'TR221': (6.0, 15),
                'TR257': (6.5, 15),
                'TR295': (7.0, 15),
                'TR317': (7.2, 15),
                'TR335': (7.4, 15),
                'TR377': (7.9, 15),
                'TR443': (8.6, 15),
                'TR513': (9.2, 15),
                'TR524': (9.3, 15),
                'TR589': (9.8, 15)
            }
            
            if mesh_code in mesh_properties:
                return mesh_properties[mesh_code]
            else:
                print(f"Uyarı: {mesh_code} için özellikler bulunamadı!")
                return (0, 0)  # Varsayılan değerler
            
        except Exception as e:
            print(f"Hasır özellikleri alınırken hata: {str(e)}")
            return (0, 0)

def main():
    app = QApplication(sys.argv)
    window = RebarCalculatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 