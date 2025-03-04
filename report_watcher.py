import os
import re
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QWidget, QPushButton, QHBoxLayout, QLabel, QFileDialog, QTableWidget, QHeaderView, QTableWidgetItem
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon

# Rapor analiz modüllerini içe aktar
from report_analyzer.report_parser import ReportParser
from report_analyzer.report_calculator import ReportCalculator

# Loglama yapılandırması
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/report_watcher.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ReportWatcher")

class ReportAnalyzerSignals(QObject):
    update_signal = pyqtSignal(str, float)  # mahal, ağırlık
    add_report_signal = pyqtSignal(str, str, float)  # dosya_adı, mahal, ağırlık

class ReportChangeHandler(FileSystemEventHandler):
    def __init__(self, report_folder, analyzer_signals):
        self.report_folder = report_folder
        self.parser = ReportParser()
        self.calculator = ReportCalculator()
        self.parser.set_folder(report_folder)
        self.analyzer_signals = analyzer_signals
        self.last_processed_time = {}
        self.total_weight = 0
        
        # Başlangıçta mevcut dosyaları işle
        self.process_existing_files()
        
    def process_existing_files(self):
        """Klasördeki mevcut dosyaları işle"""
        # Önce tüm dosyaları işaretle
        for file in os.listdir(self.report_folder):
            if file.endswith(".txt"):
                file_path = os.path.join(self.report_folder, file)
                self.last_processed_time[file_path] = os.path.getmtime(file_path)
        
        # Sonra izleme başladıktan sonra işle
        # Bu sayede event_handler oluşturulduktan sonra sinyaller gönderilir
        QTimer.singleShot(100, self._process_initial_files)

    def _process_initial_files(self):
        """Başlangıçtaki dosyaları işle (gecikmeli)"""
        for file_path in self.last_processed_time.keys():
            self.process_report_file(file_path)
    
    def on_modified(self, event):
        """Dosya değiştiğinde çağrılır"""
        if not event.is_directory and event.src_path.endswith(".txt"):
            # Dosya değişiklik zamanını kontrol et
            current_time = os.path.getmtime(event.src_path)
            last_time = self.last_processed_time.get(event.src_path, 0)
            
            # Eğer dosya son işlemeden sonra değiştiyse
            if current_time > last_time:
                logger.info(f"Değişiklik algılandı: {event.src_path}")
                self.last_processed_time[event.src_path] = current_time
                self.process_report_file(event.src_path)
    
    def on_created(self, event):
        """Yeni dosya oluşturulduğunda çağrılır"""
        if not event.is_directory and event.src_path.endswith(".txt"):
            logger.info(f"Yeni dosya oluşturuldu: {event.src_path}")
            self.last_processed_time[event.src_path] = os.path.getmtime(event.src_path)
            self.process_report_file(event.src_path)
    
    def process_report_file(self, file_path):
        """Rapor dosyasını işle ve ağırlık bilgisini çıkar"""
        try:
            # Dosyayı oku
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Mahal bilgisini çıkar
            mahal_match = re.search(r'Mahal: (.+?)\n', content)
            mahal = mahal_match.group(1).strip() if mahal_match else "Bilinmiyor"
            
            # Toplam ağırlık bilgisini çıkar - Kategori Toplamı altında arama yap
            weight_match = re.search(r'Kategori Toplamı:.*?Toplam Ağırlık: (\d+\.\d+) kg', content, re.DOTALL)
            
            if weight_match:
                weight = float(weight_match.group(1))
                logger.info(f"Ağırlık bilgisi bulundu: {mahal} - {weight} kg")
                
                # Toplam ağırlığı güncelle
                self.total_weight += weight
                
                # Sinyal gönder
                self.analyzer_signals.update_signal.emit(mahal, weight)
                
                logger.info(f"Toplam ağırlık: {self.total_weight} kg")
                
                # Rapor listesine ekle
                file_name = os.path.basename(file_path)
                self.analyzer_signals.add_report_signal.emit(file_name, mahal, weight)
            else:
                logger.warning(f"Ağırlık bilgisi bulunamadı: {file_path}")
                
        except Exception as e:
            logger.error(f"Dosya işleme hatası: {str(e)}, dosya: {file_path}")

class DropArea(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self.setText("Rapor dosyalarını buraya sürükleyip bırakın")
        self.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #aaa; padding: 20px;")
        self.parent_window = parent
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith('.txt'):
                files.append(path)
        
        if files:
            self.parent_window.process_dropped_files(files)
            self.setText("Rapor dosyalarını buraya sürükleyip bırakın")
        else:
            self.setText("Sadece .txt dosyaları kabul edilir")

class ReportWatcherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rapor İzleyici")
        self.setMinimumSize(800, 600)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Durum bilgisi
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Rapor Klasörü:"))
        self.folder_label = QLabel()
        status_layout.addWidget(self.folder_label)
        status_layout.addStretch()
        
        # Toplam ağırlık
        self.weight_label = QLabel("Toplam Ağırlık: 0.00 kg")
        self.weight_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Rapor yükleme butonu
        upload_layout = QHBoxLayout()
        self.btn_upload = QPushButton("Rapor Dosyası Ekle")
        self.btn_upload.clicked.connect(self.upload_reports)
        
        self.btn_upload_folder = QPushButton("Rapor Klasörü Ekle")
        self.btn_upload_folder.clicked.connect(self.upload_folder)
        
        upload_layout.addWidget(self.btn_upload)
        upload_layout.addWidget(self.btn_upload_folder)
        
        # Sürükle-bırak alanı
        self.drop_area = DropArea(self)
        self.drop_area.setFixedHeight(100)
        
        # Rapor listesi
        self.report_list = QTableWidget(0, 3)
        self.report_list.setHorizontalHeaderLabels(["Dosya Adı", "Mahal", "Ağırlık (kg)"])
        self.report_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.report_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # Butonlar
        button_layout = QHBoxLayout()
        self.btn_start = QPushButton("İzlemeyi Başlat")
        self.btn_start.clicked.connect(self.start_watching)
        self.btn_stop = QPushButton("İzlemeyi Durdur")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_watching)
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_stop)
        
        # Layout'a ekle
        main_layout.addLayout(status_layout)
        main_layout.addWidget(self.weight_label)
        main_layout.addLayout(upload_layout)
        main_layout.addWidget(self.drop_area)
        main_layout.addWidget(QLabel("Yüklenen Raporlar:"))
        main_layout.addWidget(self.report_list)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log_text)
        main_layout.addLayout(button_layout)
        
        # İzleyici değişkenleri
        self.observer = None
        self.event_handler = None
        self.signals = ReportAnalyzerSignals()
        self.signals.update_signal.connect(self.update_report_info)
        self.signals.add_report_signal.connect(self.add_report_to_list)
        
        # Toplam ağırlık
        self.total_weight = 0
        
        # Rapor klasörü
        self.report_folder = os.path.join(os.getcwd(), "metraj_raporlari_2025-03-03")
        if os.path.exists(self.report_folder):
            self.folder_label.setText(self.report_folder)
            self.log_text.append(f"<span style='color:blue'>Rapor klasörü hazır: {self.report_folder}</span>")
        else:
            self.log_text.append("<span style='color:red'>Rapor klasörü bulunamadı!</span>")
    
    def start_watching(self):
        """Klasör izlemeyi başlat"""
        if not os.path.exists(self.report_folder):
            self.log_text.append("<span style='color:red'>Rapor klasörü bulunamadı!</span>")
            return
        
        try:
            # İzleyiciyi başlat
            self.event_handler = ReportChangeHandler(self.report_folder, self.signals)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, self.report_folder, recursive=False)
            self.observer.start()
            
            # Buton durumlarını güncelle
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            
            self.log_text.append(f"<span style='color:green'>İzleme başlatıldı: {self.report_folder}</span>")
            
            # Mevcut toplam ağırlığı güncelle
            self.total_weight = self.event_handler.total_weight
            self.weight_label.setText(f"Toplam Ağırlık: {self.total_weight:.2f} kg")
            
        except Exception as e:
            self.log_text.append(f"<span style='color:red'>İzleme başlatma hatası: {str(e)}</span>")
    
    def stop_watching(self):
        """Klasör izlemeyi durdur"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
            # Buton durumlarını güncelle
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            
            self.log_text.append("<span style='color:orange'>İzleme durduruldu</span>")
    
    def update_report_info(self, mahal, weight):
        """Rapor bilgilerini güncelle"""
        self.log_text.append(f"<span style='color:blue'>Yeni rapor: {mahal} - {weight:.2f} kg</span>")
        
        # Toplam ağırlığı güncelle
        if self.event_handler:
            self.total_weight = self.event_handler.total_weight
        else:
            self.total_weight += weight
        
        self.weight_label.setText(f"Toplam Ağırlık: {self.total_weight:.2f} kg")
    
    def closeEvent(self, event):
        """Pencere kapatıldığında izleyiciyi durdur"""
        self.stop_watching()
        event.accept()

    def upload_reports(self):
        """Rapor dosyalarını seç ve ekle"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Rapor Dosyalarını Seç", "", "Metin Dosyaları (*.txt)"
        )
        
        if not file_paths:
            return
        
        self.log_text.append(f"<span style='color:blue'>{len(file_paths)} rapor dosyası seçildi</span>")
        
        # Seçilen dosyaları işle
        for file_path in file_paths:
            try:
                # Dosyayı metraj_raporlari klasörüne kopyala
                file_name = os.path.basename(file_path)
                target_path = os.path.join(self.report_folder, file_name)
                
                # Eğer dosya zaten varsa üzerine yazma
                if os.path.exists(target_path):
                    self.log_text.append(f"<span style='color:orange'>Dosya zaten var, üzerine yazılıyor: {file_name}</span>")
                
                # Dosyayı kopyala
                import shutil
                shutil.copy2(file_path, target_path)
                
                # Dosyayı işle
                if self.event_handler:
                    self.event_handler.process_report_file(target_path)
                    self.log_text.append(f"<span style='color:green'>Rapor eklendi: {file_name}</span>")
                
            except Exception as e:
                self.log_text.append(f"<span style='color:red'>Rapor ekleme hatası: {str(e)}, dosya: {file_path}</span>")
        
        # Toplam ağırlığı güncelle
        if self.event_handler:
            self.total_weight = self.event_handler.total_weight
            self.weight_label.setText(f"Toplam Ağırlık: {self.total_weight:.2f} kg")

    def upload_folder(self):
        """Rapor klasörünü seç ve içindeki tüm raporları ekle"""
        folder_path = QFileDialog.getExistingDirectory(self, "Rapor Klasörünü Seç")
        
        if not folder_path:
            return
        
        self.log_text.append(f"<span style='color:blue'>Rapor klasörü seçildi: {folder_path}</span>")
        
        # Klasördeki tüm .txt dosyalarını bul
        import glob
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        
        if not txt_files:
            self.log_text.append(f"<span style='color:orange'>Seçilen klasörde rapor dosyası bulunamadı</span>")
            return
        
        self.log_text.append(f"<span style='color:blue'>{len(txt_files)} rapor dosyası bulundu</span>")
        
        # Dosyaları işle
        for file_path in txt_files:
            try:
                # Dosyayı metraj_raporlari klasörüne kopyala
                file_name = os.path.basename(file_path)
                target_path = os.path.join(self.report_folder, file_name)
                
                # Eğer dosya zaten varsa üzerine yazma
                if os.path.exists(target_path):
                    self.log_text.append(f"<span style='color:orange'>Dosya zaten var, üzerine yazılıyor: {file_name}</span>")
                
                # Dosyayı kopyala
                import shutil
                shutil.copy2(file_path, target_path)
                
                # Dosyayı işle
                if self.event_handler:
                    self.event_handler.process_report_file(target_path)
                    self.log_text.append(f"<span style='color:green'>Rapor eklendi: {file_name}</span>")
                
            except Exception as e:
                self.log_text.append(f"<span style='color:red'>Rapor ekleme hatası: {str(e)}, dosya: {file_path}</span>")
        
        # Toplam ağırlığı güncelle
        if self.event_handler:
            self.total_weight = self.event_handler.total_weight
            self.weight_label.setText(f"Toplam Ağırlık: {self.total_weight:.2f} kg")

    def process_dropped_files(self, file_paths):
        """Sürükle-bırak ile eklenen dosyaları işle"""
        self.log_text.append(f"<span style='color:blue'>{len(file_paths)} rapor dosyası ekleniyor...</span>")
        
        # Seçilen dosyaları işle
        for file_path in file_paths:
            try:
                # Dosyayı metraj_raporlari klasörüne kopyala
                file_name = os.path.basename(file_path)
                target_path = os.path.join(self.report_folder, file_name)
                
                # Eğer dosya zaten varsa üzerine yazma
                if os.path.exists(target_path):
                    self.log_text.append(f"<span style='color:orange'>Dosya zaten var, üzerine yazılıyor: {file_name}</span>")
                
                # Dosyayı kopyala
                import shutil
                shutil.copy2(file_path, target_path)
                
                # Dosyayı işle
                if self.event_handler:
                    self.event_handler.process_report_file(target_path)
                    self.log_text.append(f"<span style='color:green'>Rapor eklendi: {file_name}</span>")
                
            except Exception as e:
                self.log_text.append(f"<span style='color:red'>Rapor ekleme hatası: {str(e)}, dosya: {file_path}</span>")
        
        # Toplam ağırlığı güncelle
        if self.event_handler:
            self.total_weight = self.event_handler.total_weight
            self.weight_label.setText(f"Toplam Ağırlık: {self.total_weight:.2f} kg")

    def add_report_to_list(self, file_name, mahal, weight):
        """Rapor listesine yeni rapor ekle"""
        # Tabloda aynı dosya adı var mı kontrol et
        for row in range(self.report_list.rowCount()):
            if self.report_list.item(row, 0).text() == file_name:
                # Varsa güncelle
                self.report_list.item(row, 1).setText(mahal)
                self.report_list.item(row, 2).setText(f"{weight:.2f}")
                return
        
        # Yoksa yeni satır ekle
        row = self.report_list.rowCount()
        self.report_list.insertRow(row)
        self.report_list.setItem(row, 0, QTableWidgetItem(file_name))
        self.report_list.setItem(row, 1, QTableWidgetItem(mahal))
        self.report_list.setItem(row, 2, QTableWidgetItem(f"{weight:.2f}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportWatcherWindow()
    window.show()
    sys.exit(app.exec()) 