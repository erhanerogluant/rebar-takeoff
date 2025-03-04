from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                           QTreeWidgetItem, QStatusBar, QMessageBox, QFileDialog,
                           QDialog, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon
import sys
from autocad_integration import AutoCADIntegration
from rebar_calculator import RebarData
import os
from datetime import datetime
import logging
import re
import math
import traceback


class SelectionThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, acad, parent=None):
        super().__init__(parent)
        self.acad = acad
        self.running = True
        self.operation_type = None  # İşlem tipini saklamak için
    
    def stop(self):
        self.running = False
    
    def set_operation(self, operation_type):
        """İşlem tipini ayarla"""
        self.operation_type = operation_type
    
    def run(self):
        try:
            if not self.running:
                return
                
            # İşlem tipine göre uygun fonksiyonu çağır
            if self.operation_type == 'FOUNDATION':
                # Temel demiri seçim işlemini başlat
                # Burada doğrudan işlem yapmıyoruz, sadece thread'i bitiriyoruz
                # Asıl işlem process_foundation_selection'da yapılacak
                pass
            
            # Diğer işlem tipleri için de benzer kontroller eklenebilir
            
            # Thread'i bitir
            self.finished.emit()
                
        except Exception as e:
            self.error.emit(str(e))

class RebarCalculatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demir Metraj Hesaplama")
        self.setGeometry(100, 100, 1200, 800)
        
        # AutoCAD entegrasyonu
        self.acad = AutoCADIntegration()
        
        # Log handler'ı bağla
        self.setup_log_handler()
        
        # Mahal bilgisi için değişken
        self.mahal_bilgisi = "Belirtilmemiş"
        
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
        self.btn_foundation = QPushButton("Temel Demiri")
        self.btn_foundation.setIcon(QIcon("icons/foundation.png"))
        
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
        self.btn_foundation.setStyleSheet(button_style)
        
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
        operation_layout.addWidget(self.btn_foundation)
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
        self.btn_stop.clicked.connect(self.stop_operation)
        self.btn_refresh.clicked.connect(self.refresh_application)
        self.btn_foundation.clicked.connect(self.start_foundation_selection)
        
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
        self.shortcut_esc.activated.connect(self.stop_operation)
        
        # Selection thread
        self.selection_thread = None
        
        # Butonları aktifleştir
        self.enable_buttons(True)
        self.btn_stop.setEnabled(False)  # İşlem başlamadan durdurma butonu pasif
        
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
            # Önce mahal bilgisini al
            self.get_mahal_bilgisi()
            
            # Sürekli seçim döngüsü
            continue_selection = True
            
            while continue_selection and self.is_operation_running:
                # 1. Boy demiri text seçimi
                rebar_text = self.acad.select_entity("Boy demiri textini seçin (örn: 2X13∅20)")
                if not rebar_text:
                    break  # Kullanıcı seçimi iptal etti
                
                # Çap ve adet bilgilerini çıkar
                pattern = r'(\d+)X(\d+)[ƒØ∅](\d+)|(\d+)X(\d+)%%C(\d+)'
                match = re.search(pattern, rebar_text)
                
                if not match:
                    print("Geçersiz boy demiri formatı!")
                    continue  # Yeni bir seçim yap
                
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
                    continue  # Yeni bir seçim yap
                
                length_match = re.search(r'[Ll]\s*=\s*(\d+)', length_text)
                if not length_match:
                    print("Geçersiz boy formatı!")
                    continue  # Yeni bir seçim yap
                
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
                    piece_count=count,
                    length=length,
                    total_length=total_length,
                    unit_weight=weight_per_meter,
                    total_weight=total_weight,
                    description=f"{count}×Ø{diameter} L={length}"
                )
                
                self.acad.calculator.results.append(result)
                print("\nHesaplama başarıyla kaydedildi!")
                
                # GUI'yi güncelle
                self.add_result_to_tree("Boy Demiri", f"{count}×Ø{diameter} L={length}")
                self.update_summary('REBAR')
                
                # Log alanına bilgi ekleyin
                self.log_text.append(f"<span style='color:green'>Boy demiri hesaplandı: {count}×Ø{diameter} L={length} - {total_weight:.2f} kg</span>")
                
                # Metraj raporunu kaydet
                self.save_metraj_report()
                
                # Popup yerine durum çubuğuna mesaj
                self.statusBar.showMessage("Başka boy demiri hesaplamak için seçime devam edin veya İşlemi Durdur butonuna basın.")
                
                # Popup mesajı yerine durum çubuğu mesajı ve log mesajı
                self.log_text.append("<span style='color:blue'>Devam etmek için yeni bir boy demiri seçin, bitirmek için İşlemi Durdur butonuna basın</span>")
            
            # İşlemi tamamla
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("Boy demiri hesabı tamamlandı!")
            
        except Exception as e:
            print(f"\nHata: {str(e)}")
            print(traceback.format_exc())
            logging.error(f"Boy demiri hesaplama hatası: {str(e)}")
            self.log_text.append(f"<span style='color:red'>Boy demiri hesaplama hatası: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
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
                print(f"Adet: {last_result.piece_count}")
                print(f"Toplam Boy: {last_result.total_length/100:.2f} m")
                print(f"Birim Ağırlık: {last_result.unit_weight:.3f} kg/mt")
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
            
    def update_summary(self, result_type=None):
        """Özet bilgileri güncelle"""
        try:
            # Eğer result_type belirtilmemişse, tüm sonuçları göster
            if result_type is None:
                self.acad.calculator.show_summary()
            else:
                # Belirli bir tip için özeti göster
                self.acad.calculator.show_summary(result_type)
                self.acad.calculator.log_summary(result_type)  # result_type parametresini geçir
        except Exception as e:
            print(f"Özet güncellenirken hata: {str(e)}")
            import traceback
            print(traceback.format_exc())

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
                                f.write(f"Adet: {result.piece_count}\n")
                                f.write(f"Toplam Boy: {result.total_length/100:.2f} m\n")
                                total_length += result.total_length
                            
                            f.write(f"Birim Ağırlık: {result.unit_weight:.3f} kg/mt\n")
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
                    report += f"Adet: {result.piece_count}\n"
                    report += f"Toplam Boy: {result.total_length/100:.2f} m\n"
                report += f"Birim Ağırlık: {result.unit_weight:.3f} kg/mt\n"
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
        # Başka bir işlem çalışıyorsa uyarı ver
        if self.is_operation_running:
            QMessageBox.warning(self, "İşlem Devam Ediyor", "Başka bir işlem devam ediyor. Lütfen önce onu tamamlayın.")
            return
        
        self.is_operation_running = True
        self.current_operation = 'STIRRUP'
        self.btn_stop.setEnabled(True)
        
        self.statusBar.showMessage("Etriye seçimi başlatıldı...")
        
        try:
            # Önce mahal bilgisini al
            self.get_mahal_bilgisi()
            
            # Sürekli etriye seçimi için döngü
            while self.is_operation_running:
                # Etriye seçimini işle
                success = self.acad.process_stirrup(self.mahal_bilgisi)
                
                if success:
                    self.log_text.append("<span style='color:green'>Etriye hesabı tamamlandı</span>")
                    
                    # Sonuçları güncelle
                    if self.acad.calculator.results:
                        last_result = self.acad.calculator.results[-1]
                        self.add_result_to_tree("Etriye", last_result.description)
                        self.update_summary('STIRRUP')
                    
                    # Devam etmek isteyip istemediğini sor
                    self.statusBar.showMessage("Başka etriye hesaplamak için seçime devam edin veya İşlemi Durdur butonuna basın.")
                    
                    # GUI güncellemesini zorla
                    QApplication.processEvents()
                else:
                    # Kullanıcı seçim yapmadı veya iptal etti
                    break
            
            # İşlemi tamamla
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("Etriye hesabı tamamlandı!")
            
        except Exception as e:
            print(f"\nHata: {str(e)}")
            print(traceback.format_exc())
            logging.error(f"Etriye hesaplama hatası: {str(e)}")
            self.log_text.append(f"<span style='color:red'>Etriye hesaplama hatası: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("Hata oluştu!")

    def start_mesh_selection(self, mesh_type=None):
        """Hasır seçim işlemini yönet"""
        # Başka bir işlem çalışıyorsa uyarı ver
        if self.is_operation_running:
            QMessageBox.warning(self, "İşlem Devam Ediyor", "Başka bir işlem devam ediyor. Lütfen önce onu tamamlayın.")
            return
        
        self.is_operation_running = True
        self.current_operation = 'MESH'
        self.btn_stop.setEnabled(True)
        
        # Eğer mesh_type belirtilmişse, doğrudan o tipe geç
        if mesh_type:
            self.statusBar.showMessage(f"{mesh_type} seçimi başlatıldı...")
            self.process_mesh_selection(mesh_type)
            return
        
        # Mesh_type belirtilmemişse, kullanıcıya sor
        self.statusBar.showMessage("Hasır seçimi başlatıldı...")
        try:
            # Önce mahal bilgisini al
            self.get_mahal_bilgisi()
            
            # Hasır tipi seçimi
            dialog = QDialog(self)
            dialog.setWindowTitle("Hasır Tipi Seçin")
            dialog.setMinimumWidth(300)
            
            layout = QVBoxLayout(dialog)
            
            # Hasır tipi seçenekleri
            mesh_type_group = QGroupBox("Hasır Tipi")
            mesh_type_layout = QVBoxLayout()
            
            # Döşeme hasırı seçeneği
            slab_button = QPushButton("Döşeme Hasırı")
            slab_button.clicked.connect(lambda: self.process_mesh_selection('SLAB'))
            mesh_type_layout.addWidget(slab_button)
            
            # Perde hasırı seçeneği
            wall_button = QPushButton("Perde Hasırı")
            wall_button.clicked.connect(lambda: self.process_mesh_selection('WALL'))
            mesh_type_layout.addWidget(wall_button)
            
            mesh_type_group.setLayout(mesh_type_layout)
            layout.addWidget(mesh_type_group)
            
            # İptal butonu
            cancel_button = QPushButton("İptal")
            cancel_button.clicked.connect(dialog.reject)
            layout.addWidget(cancel_button)
            
            # Dialog'u göster
            if dialog.exec() == QDialog.DialogCode.Rejected:
                # Kullanıcı iptal etti
                self.is_operation_running = False
                self.current_operation = None
                self.btn_stop.setEnabled(False)
                self.statusBar.showMessage("İşlem iptal edildi")
                return
            
        except Exception as e:
            print(f"\nHata: {str(e)}")
            print(traceback.format_exc())
            logging.error(f"Hasır seçim hatası: {str(e)}")
            self.log_text.append(f"<span style='color:red'>Hasır seçim hatası: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("Hata oluştu!")

    def start_connection_selection(self):
        """Ara bağlantı seçim işlemini yönet"""
        self.is_operation_running = True
        self.current_operation = 'CONNECTION'
        self.btn_stop.setEnabled(True)
        self.statusBar.showMessage("Ara bağlantı seçimi başlatıldı...")
        
        try:
            # Önce mahal bilgisini al
            self.get_mahal_bilgisi()
            
            # Sürekli seçim döngüsü
            continue_selection = True
            
            while continue_selection and self.is_operation_running:
                # 1. Ara bağlantı text seçimi
                conn_text = self.acad.select_entity("Ara bağlantı textini seçin (örn: 2X∅12/15, ƒ8/20, %%C8/20, 2X%%C12/15 L=185, 2X13%%C20 L=235)")
                if not conn_text:
                    break  # Kullanıcı seçimi iptal etti
                
                print(f"Seçilen text: {conn_text}")
                
                # Çap, aralık, çarpan ve boy bilgilerini çıkar - Genişletilmiş regex
                # Format 1: 2X∅12/15 L=185 veya 2X%%C12/15 L=185
                # Format 2: ∅8/20 veya %%C8/20 veya ƒ8/20
                # Format 3: 2X13%%C20 L=235 (2 çarpan, 13 adet, 20mm çap)
                
                # Önce L= değerini kontrol et ve ayır
                length_value = None
                length_match = re.search(r'[Ll]\s*=\s*(\d+)', conn_text)
                if length_match:
                    length_value = int(length_match.group(1))
                    # L= kısmını metinden çıkar
                    conn_text = conn_text.replace(length_match.group(0), '').strip()
                
                # Yeni format: 2X13%%C20 (2 çarpan, 13 adet, 20mm çap)
                new_format_match = re.search(r'(\d+)[Xx](\d+)(?:%%C|[∅ƒØ])(\d+)', conn_text)
                if new_format_match:
                    multiplier = int(new_format_match.group(1))
                    count = int(new_format_match.group(2))
                    diameter = int(new_format_match.group(3))
                    spacing = 0  # Bu formatta aralık belirtilmiyor
                    
                    print(f"Yeni format tespit edildi: {multiplier}X{count}Ø{diameter}")
                else:
                    # Eski formatlar için mevcut regex'leri kullan
                    # Format: 2X∅12/15 veya 2X%%C12/15
                    multiplier_match = re.search(r'(\d+)[Xx]', conn_text)
                    multiplier = int(multiplier_match.group(1)) if multiplier_match else 1
                    
                    # Çap ve aralık: ∅12/15 veya %%C12/15 veya ƒ12/15
                    diameter_spacing_match = re.search(r'(?:%%C|[∅ƒØ])(\d+)/(\d+)', conn_text)
                    if diameter_spacing_match:
                        diameter = int(diameter_spacing_match.group(1))
                        spacing = int(diameter_spacing_match.group(2))
                        
                        # Boy bilgisi kontrolü
                        if length_value is None:
                            # Boy bilgisi yoksa, kullanıcıdan seç
                            length_text = self.acad.select_entity("Boy uzunluğunu seçin (örn: L=185)")
                            if not length_text:
                                continue  # Yeni bir seçim yap
                            
                            length_match = re.search(r'[Ll]\s*=\s*(\d+)', length_text)
                            if not length_match:
                                print("Geçersiz boy formatı!")
                                continue  # Yeni bir seçim yap
                            
                            length_value = int(length_match.group(1))
                        
                        print(f"- Boy: {length_value} cm")
                        
                        # Adet bilgisi için dimension seçimi
                        dimension = self.acad.select_entity("Adet için dimension seçin")
                        if not dimension:
                            continue  # Yeni bir seçim yap
                        
                        try:
                            # Dimension değerini aralık değerine böl ve yukarı yuvarla
                            dimension_value = float(dimension)
                            count = math.ceil(dimension_value / spacing)  # Yukarı yuvarlama
                            print(f"- Adet: {count} (Dimension: {dimension_value} cm ÷ Aralık: {spacing} cm = {dimension_value/spacing:.1f} → {count})")
                        except:
                            print("Geçersiz dimension değeri!")
                            continue
                
                # Eğer hiçbir format eşleşmezse hata ver
                if not new_format_match and not diameter_spacing_match:
                    raise ValueError(f"Geçersiz ara bağlantı formatı: {conn_text}")
                
                # Eğer boy değeri belirtilmemişse varsayılan değer kullan
                if length_value is None:
                    length_value = 100  # Varsayılan boy (cm)
                    print(f"Boy değeri belirtilmemiş, varsayılan değer kullanılıyor: {length_value} cm")
                
                # Hesaplamaları yap
                print("\nHESAPLAMA SONUÇLARI:")
                print("--------------------")
                
                # Eğer yeni format kullanılıyorsa (2X13%%C20)
                if new_format_match:
                    # Adet zaten belirtilmiş
                    print(f"1. Toplam adet: {count * multiplier} adet")
                    print(f"   {count} adet × {multiplier} = {count * multiplier} adet")
                    
                    # Toplam boy hesabı
                    total_length_cm = count * multiplier * length_value
                    print(f"2. Toplam boy: {total_length_cm} cm = {total_length_cm/100:.2f} m")
                    print(f"   {count * multiplier} adet × {length_value} cm = {total_length_cm} cm")
                else:
                    # Eski format için hesaplama (aralık belirtilmiş)
                    # 1. Toplam boy hesabı
                    total_length_cm = count * multiplier * length_value
                    print(f"1. Toplam boy: {total_length_cm} cm = {total_length_cm/100:.2f} m")
                    print(f"   {count} adet × {multiplier} × {length_value} cm = {total_length_cm} cm")
                
                # Ağırlık hesabı
                weight_per_meter = self.acad.calculator.get_unit_weight(diameter)
                total_weight = (total_length_cm / 100) * weight_per_meter
                print(f"3. Toplam ağırlık: {total_weight:.2f} kg")
                print(f"   {total_length_cm/100:.2f} m × {weight_per_meter:.3f} kg/m = {total_weight:.2f} kg")
                
                # Açıklama metni oluştur
                if new_format_match:
                    description = f"{multiplier}X{count}Ø{diameter} L={length_value}"
                else:
                    description = f"{multiplier}X Ø{diameter}/{spacing} L={length_value}" if multiplier > 1 else f"Ø{diameter}/{spacing} L={length_value}"
                
                # Sonucu oluştur
                result = RebarData(
                    type='CONNECTION',
                    diameter=diameter,
                    spacing=spacing,
                    length=length_value,
                    piece_count=count * multiplier,
                    total_length=total_length_cm,
                    unit_weight=weight_per_meter,
                    total_weight=total_weight,
                    description=description
                )
                
                # Sonucu kaydet
                self.acad.calculator.results.append(result)
                print("\nHesaplama başarıyla kaydedildi!")
                
                # GUI'yi güncelle
                self.add_result_to_tree("Ara Bağlantı", result.description)
                self.update_summary('CONNECTION')
                
                # Log alanına bilgi ekleyin
                self.log_text.append(f"<span style='color:green'>Ara bağlantı hesaplandı: {result.description} - {total_weight:.2f} kg</span>")
                
                # Metraj raporunu kaydet (save_connection_report yerine)
                self.save_metraj_report()
                
                # Popup yerine durum çubuğuna mesaj
                self.statusBar.showMessage("Başka ara bağlantı hesaplamak için seçime devam edin veya İşlemi Durdur butonuna basın.")
                
                # Log alanına mesaj
                self.log_text.append("<span style='color:blue'>Devam etmek için yeni bir ara bağlantı seçin, bitirmek için İşlemi Durdur butonuna basın</span>")
                
                # GUI güncellemesini zorla
                QApplication.processEvents()
            
            # İşlemi tamamla
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("İşlem başarıyla tamamlandı!")
                
        except Exception as e:
            print(f"\nHata: {str(e)}")
            print(traceback.format_exc())
            logging.error(f"Ara bağlantı hesaplama hatası: {str(e)}")
            self.log_text.append(f"<span style='color:red'>Ara bağlantı hesaplama hatası: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("Hata oluştu!")

    def stop_operation(self):
        """Devam eden işlemi durdur"""
        if not self.is_operation_running:
            self.statusBar.showMessage("Durdurmak için aktif bir işlem yok.")
            return
        
        print("İşlem durduruldu.")
        self.statusBar.showMessage("İşlem durduruldu.")
        self.log_text.append("<span style='color:red'>İşlem kullanıcı tarafından durduruldu.</span>")
        
        # Thread varsa durdur
        if hasattr(self, 'selection_thread') and self.selection_thread:
            self.selection_thread.stop()
        
        # Durum değişkenlerini güncelle
        self.is_operation_running = False
        self.current_operation = None
        
        # Butonları aktifleştir
        self.enable_buttons(True)
        self.btn_stop.setEnabled(False)

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
            # Sonuçları kategorilere ayır
            categorized_results = {
                'REBAR': [],
                'STIRRUP': [],
                'MESH_WALL': [],
                'MESH_SLAB': [],
                'CONNECTION': [],
                'FOUNDATION': []
            }
            
            # Kategori etiketleri
            categories = {
                'REBAR': {'label': 'Boy Demirleri', 'filename': 'boy_demirleri.txt'},
                'STIRRUP': {'label': 'Etriyeler', 'filename': 'etriyeler.txt'},
                'MESH_WALL': {'label': 'Perde Hasırları', 'filename': 'perde_hasirlari.txt'},
                'MESH_SLAB': {'label': 'Döşeme Hasırları', 'filename': 'doseme_hasirlari.txt'},
                'CONNECTION': {'label': 'Ara Bağlantılar', 'filename': 'ara_baglantilar.txt'},
                'FOUNDATION': {'label': 'Temel Demirleri', 'filename': 'temel_demirleri.txt'}
            }
            
            # Sonuçları kategorilere ayır
            for result in self.acad.calculator.results:
                if result.type == 'REBAR':
                    categorized_results['REBAR'].append(result)
                elif result.type == 'STIRRUP':
                    categorized_results['STIRRUP'].append(result)
                elif result.type == 'MESH_WALL':
                    categorized_results['MESH_WALL'].append(result)
                elif result.type == 'MESH_SLAB':
                    categorized_results['MESH_SLAB'].append(result)
                elif result.type == 'CONNECTION':
                    categorized_results['CONNECTION'].append(result)
                elif result.type == 'FOUNDATION':
                    categorized_results['FOUNDATION'].append(result)
            
            # Raporları kaydet
            import os
            import datetime
            
            # Klasör oluştur
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            report_dir = f"metraj_raporlari_{timestamp}"
            
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            # Kaydedilen dosyaların listesi
            saved_files = []
            
            # Her kategori için rapor oluştur
            for category, results in categorized_results.items():
                if not results:
                    continue  # Boş kategorileri atla
                
                # Dosya adı
                filename = categories[category]['filename']
                filepath = os.path.join(report_dir, filename)
                
                # Dosyayı oluştur
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"{categories[category]['label']} METRAJ RAPORU\n")
                    f.write("="*50 + "\n\n")
                    f.write(f"Mahal: {self.mahal_bilgisi}\n")
                    f.write(f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
                    
                    # Çapa göre grupla
                    by_diameter = {}
                    for r in results:
                        if r.diameter not in by_diameter:
                            by_diameter[r.diameter] = []
                        by_diameter[r.diameter].append(r)
                    
                    # Her çap için detayları yaz
                    for diameter, items in by_diameter.items():
                        total_count = sum(r.piece_count for r in items)
                        total_weight = sum(r.total_weight for r in items)
                        total_length = sum(r.total_length for r in items) / 100  # cm'den m'ye çevir
                        
                        f.write(f"Ø{diameter}:\n")
                        
                        if category == 'FOUNDATION':
                            f.write(f"- Toplam Boy: {total_length:.2f} m\n")
                            f.write(f"- Toplam Adet: {total_count} adet\n")
                            f.write(f"- Toplam Ağırlık: {total_weight:.2f} kg\n\n")
                            
                            # Her temel demiri için detay
                            for r in items:
                                f.write(f"  * {r.description}\n")
                                f.write(f"    Adet: {r.piece_count}, Boy: {r.length} cm, Toplam Boy: {r.total_length/100:.2f} m, Ağırlık: {r.total_weight:.2f} kg\n")
                        else:
                            f.write(f"- Toplam Boy: {total_length:.2f} m\n")
                            f.write(f"- Toplam Adet: {total_count} adet\n")
                            f.write(f"- Toplam Ağırlık: {total_weight:.2f} kg\n\n")
                            
                            # Her hasır için detay
                            for r in items:
                                if hasattr(r, 'width') and hasattr(r, 'height'):
                                    area = (r.width * r.height)/10000
                                    f.write(f"  * Hasır {r.description}\n")
                                    f.write(f"    Alan: {area:.2f} m², Ağırlık: {r.total_weight:.2f} kg\n")
                        f.write("\n")
                    
                    # Kategori toplamı
                    category_weight = sum(r.total_weight for r in results)
                    
                    f.write("\nKATEGORİ TOPLAMI\n")
                    f.write("="*30 + "\n")
                    
                    if category in ['MESH_WALL', 'MESH_SLAB']:
                        category_area = sum((r.width * r.height)/10000 for r in results if hasattr(r, 'width') and hasattr(r, 'height'))
                        f.write(f"Toplam Alan: {category_area:.2f} m²\n")
                    elif category == 'FOUNDATION':
                        category_length = sum(r.total_length for r in results) / 100  # cm'den m'ye çevir
                        category_count = sum(r.piece_count for r in results)
                        f.write(f"Toplam Boy: {category_length:.2f} m\n")
                        f.write(f"Toplam Adet: {category_count} adet\n")
                    
                    f.write(f"Toplam Ağırlık: {category_weight:.2f} kg ({category_weight/1000:.3f} ton)\n")
                
                    saved_files.append(filepath)
            
            # Genel toplam dosyası
            total_filename = f"metraj_genel_toplam_{timestamp}.txt"
            total_filepath = os.path.join(report_dir, total_filename)
            
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
            print(f"\nHata: {str(e)}")
            print(traceback.format_exc())
            logging.error(f"Metraj raporu kaydetme hatası: {str(e)}")
            self.log_text.append(f"<span style='color:red'>Metraj raporu kaydetme hatası: {str(e)}</span>")
            QMessageBox.warning(self, "Hata", f"Metraj raporu kaydedilirken hata oluştu: {str(e)}")

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
                'Q443': (8.6, 15),  # Q443 eklendi
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
                # Varsayılan değerler - 0 yerine makul değerler kullan
                return (8.0, 15)  # Varsayılan çap ve aralık
            
        except Exception as e:
            print(f"Hasır özellikleri alınırken hata: {str(e)}")
            return (8.0, 15)  # Hata durumunda varsayılan değerler

    def start_foundation_selection(self):
        """Temel demiri seçim işlemini başlat"""
        try:
            # Başka bir işlem çalışıyorsa uyarı ver
            if self.is_operation_running:
                QMessageBox.warning(self, "İşlem Devam Ediyor", "Başka bir işlem devam ediyor. Lütfen önce onu tamamlayın.")
                return
            
            # Önce mahal bilgisini al
            self.get_mahal_bilgisi()
            
            # İşlem durumunu güncelle
            self.is_operation_running = True
            self.current_operation = "FOUNDATION"
            
            # Durum çubuğunu güncelle
            self.statusBar.showMessage("Temel demiri seçimi başlatıldı...")
            self.log_text.append("<span style='color:blue'>Temel demiri seçimi başlatıldı...</span>")
            
            # Seçim thread'ini başlat
            self.selection_thread = SelectionThread(self.acad)
            self.selection_thread.set_operation('FOUNDATION')
            self.selection_thread.finished.connect(self.process_foundation_selection)
            self.selection_thread.error.connect(self.handle_selection_error)
            self.selection_thread.start()
            
        except Exception as e:
            logging.error(f"Temel demiri seçim hatası: {str(e)}")
            self.statusBar.showMessage(f"Hata: {str(e)}")
            self.log_text.append(f"<span style='color:red'>HATA: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None

    def process_foundation_selection(self):
        """Temel demiri seçim işlemini tamamla"""
        try:
            # Çoklu temel demiri seçim işlemini başlat
            success = self.acad.process_multiple_foundation_rebars()
            
            if success:
                self.statusBar.showMessage("Temel demiri hesabı tamamlandı")
                self.log_text.append("<span style='color:green'>Temel demiri hesabı tamamlandı</span>")
                self.update_results()
            else:
                self.statusBar.showMessage("Temel demiri hesabı başarısız oldu")
                self.log_text.append("<span style='color:orange'>Temel demiri hesabı başarısız oldu</span>")
            
            # İşlem durumunu güncelle
            self.is_operation_running = False
            self.current_operation = None
            self.selection_thread = None
            
        except Exception as e:
            logging.error(f"Temel demiri işleme hatası: {str(e)}")
            self.statusBar.showMessage(f"Hata: {str(e)}")
            self.log_text.append(f"<span style='color:red'>HATA: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None
            self.selection_thread = None

    def update_results(self):
        """Sonuçları güncelle"""
        try:
            # Son eklenen sonucu al
            if self.acad.calculator.results:
                last_result = self.acad.calculator.results[-1]
                
                # Sonuç tipine göre ağaca ekle
                if last_result.type == 'FOUNDATION':
                    self.add_result_to_tree("Temel Demiri", f"Ø{last_result.diameter}/{last_result.spacing} L={last_result.length}")
                
                # Log alanını güncelle
                self.log_text.append(f"Yeni hesaplama eklendi: {last_result.description} - {last_result.total_weight:.2f} kg")
                
        except Exception as e:
            logging.error(f"Sonuçları güncelleme hatası: {str(e)}")

    def handle_selection_error(self, error_message):
        """Seçim işlemi sırasında oluşan hataları işle"""
        self.is_operation_running = False
        self.current_operation = None
        self.btn_stop.setEnabled(False)
        
        # Hata mesajını göster
        self.statusBar.showMessage(f"Hata: {error_message}", 5000)
        self.log_text.append(f"<span style='color:red'>HATA: {error_message}</span>")
        
        # Kullanıcıya bilgi ver
        QMessageBox.warning(self, "Seçim Hatası", f"Seçim işlemi sırasında bir hata oluştu:\n{error_message}")
        
        logging.error(f"Seçim hatası: {error_message}")

    def enable_buttons(self, enable=True):
        """GUI butonlarını aktifleştir/pasifleştir"""
        # Ana kategori butonları
        self.btn_rebar.setEnabled(enable)
        self.btn_stirrup.setEnabled(enable)
        self.btn_mesh.setEnabled(enable)
        self.btn_connection.setEnabled(enable)
        self.btn_foundation.setEnabled(enable)
        
        # İşlem butonları
        self.btn_calculate.setEnabled(enable)
        self.btn_refresh.setEnabled(enable)
        self.btn_stop.setEnabled(enable)

    def get_mahal_bilgisi(self):
        """Kullanıcıdan mahal bilgisini al"""
        try:
            # AutoCAD'den mahal bilgisi textini seç
            mahal_text = self.acad.select_entity("Mahal bilgisi textini seçin (örn: 1. Kat, A Blok, vb.)")
            
            if mahal_text:
                # Mahal bilgisini kaydet
                self.mahal_bilgisi = mahal_text.strip()
                self.log_text.append(f"<span style='color:blue'>Mahal bilgisi: {self.mahal_bilgisi}</span>")
                self.statusBar.showMessage(f"Mahal bilgisi alındı: {self.mahal_bilgisi}")
                return True
            else:
                # Kullanıcı seçim yapmadıysa varsayılan değeri kullan
                self.log_text.append("<span style='color:orange'>Mahal bilgisi seçilmedi, varsayılan değer kullanılacak</span>")
                return False
        except Exception as e:
            self.log_text.append(f"<span style='color:red'>Mahal bilgisi alınırken hata: {str(e)}</span>")
            return False

    def process_mesh_selection(self, mesh_type):
        """Hasır seçim işlemini işle"""
        try:
            # Önce mahal bilgisini al (eğer daha önce alınmadıysa)
            if self.mahal_bilgisi == "Belirtilmemiş":
                self.get_mahal_bilgisi()
            
            self.log_text.append(f"<span style='color:blue'>{mesh_type} hasır seçimi başlatıldı...</span>")
            
            # Sürekli hasır seçimi için döngü
            while self.is_operation_running:
                # Hasır seçimini işle
                if mesh_type == 'WALL':
                    # Perde hasırı seçimi
                    success = self.acad.process_wall_mesh(self.mahal_bilgisi)
                elif mesh_type == 'SLAB':
                    # Döşeme hasırı seçimi
                    success = self.acad.process_slab_mesh(self.mahal_bilgisi)
                else:
                    raise ValueError(f"Bilinmeyen hasır tipi: {mesh_type}")
                
                if success:
                    self.log_text.append(f"<span style='color:green'>{mesh_type} hasır hesabı tamamlandı</span>")
                    
                    # Sonuçları güncelle
                    if self.acad.calculator.results:
                        last_result = self.acad.calculator.results[-1]
                        if mesh_type == 'WALL':
                            self.add_result_to_tree("Perde Hasırı", last_result.description)
                        else:
                            self.add_result_to_tree("Döşeme Hasırı", last_result.description)
                    
                    # Devam etmek isteyip istemediğini sor
                    self.statusBar.showMessage(f"Başka {mesh_type} hasırı hesaplamak için seçime devam edin veya İşlemi Durdur butonuna basın.")
                    
                    # GUI güncellemesini zorla
                    QApplication.processEvents()
                else:
                    # Kullanıcı seçim yapmadı veya iptal etti
                    break
            
            # İşlemi tamamla
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage(f"{mesh_type} hasır hesabı tamamlandı")
            
        except Exception as e:
            print(f"\nHata: {str(e)}")
            print(traceback.format_exc())
            logging.error(f"Hasır işleme hatası: {str(e)}")
            self.log_text.append(f"<span style='color:red'>Hasır işleme hatası: {str(e)}</span>")
            self.is_operation_running = False
            self.current_operation = None
            self.btn_stop.setEnabled(False)
            self.statusBar.showMessage("Hata oluştu!")

def main():
    app = QApplication(sys.argv)
    window = RebarCalculatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 