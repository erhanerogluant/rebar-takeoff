import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QWidget, QTabWidget, 
                           QTableWidget, QTableWidgetItem, QSpinBox, QLineEdit, 
                           QComboBox, QGroupBox, QMessageBox, QSplitter, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import logging

# Loglama dizinini oluştur
if not os.path.exists('logs'):
    os.makedirs('logs')

# Rapor analiz modüllerini içe aktar
from report_analyzer.report_parser import ReportParser
from report_analyzer.report_calculator import ReportCalculator
from report_analyzer.data_models import SummaryResult

class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.tight_layout()

class ReportViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.reports = []
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Rapor listesi
        self.report_table = QTableWidget(0, 5)
        self.report_table.setHorizontalHeaderLabels(["Tip", "Mahal", "Tarih", "Ağırlık (kg)", "Dosya"])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.report_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.report_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.report_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.report_table.itemSelectionChanged.connect(self.show_report_details)
        
        # Rapor detayları
        self.report_details = QLabel("Rapor detayları burada görüntülenecek")
        self.report_details.setWordWrap(True)
        self.report_details.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.report_details.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.report_table)
        splitter.addWidget(self.report_details)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
    
    def set_reports(self, reports):
        self.reports = reports
        self.update_report_table()
    
    def update_report_table(self):
        self.report_table.setRowCount(0)
        
        # Rapor türü adlandırmaları
        type_names = {
            "STIRRUP": "Etriye",
            "MESH_WALL": "Perde Hasırı",
            "MESH_SLAB": "Döşeme Hasırı",
            "CONNECTION": "Ara Bağlantı",
            "REBAR": "Boy Demiri",
            "FOUNDATION": "Temel Demiri"
        }
        
        for i, report in enumerate(self.reports):
            self.report_table.insertRow(i)
            
            # Tip
            type_name = type_names.get(report.type, report.type)
            self.report_table.setItem(i, 0, QTableWidgetItem(type_name))
            
            # Mahal
            self.report_table.setItem(i, 1, QTableWidgetItem(report.mahal))
            
            # Tarih
            date_str = report.date.strftime("%Y-%m-%d %H:%M") if report.date else "-"
            self.report_table.setItem(i, 2, QTableWidgetItem(date_str))
            
            # Ağırlık
            weight_item = QTableWidgetItem(f"{report.total_weight:.2f}")
            weight_item.setData(Qt.ItemDataRole.DisplayRole, report.total_weight)
            self.report_table.setItem(i, 3, weight_item)
            
            # Dosya
            self.report_table.setItem(i, 4, QTableWidgetItem(os.path.basename(report.file_path)))
    
    def set_mahal_list(self, mahaller):
        pass  # Bu sınıfta kullanılmıyor
    
    def show_report_details(self):
        selected_rows = self.report_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.reports):
            return
        
        report = self.reports[row]
        
        # Rapor detaylarını göster
        details = f"<h2>{report.mahal} - {os.path.basename(report.file_path)}</h2>"
        
        if report.date:
            details += f"<p><b>Tarih:</b> {report.date.strftime('%Y-%m-%d %H:%M:%S')}</p>"
        
        details += f"<p><b>Toplam Ağırlık:</b> {report.total_weight:.2f} kg</p>"
        
        # Öğeleri çapa göre grupla
        items_by_diameter = {}
        for item in report.items:
            diameter_key = f"Ø{item.diameter}"
            if diameter_key not in items_by_diameter:
                items_by_diameter[diameter_key] = []
            items_by_diameter[diameter_key].append(item)
        
        # Her çap için detayları göster
        for diameter, items in items_by_diameter.items():
            details += f"<h3>{diameter}:</h3>"
            details += "<ul>"
            for item in items:
                details += f"<li>{item.description} - {item.weight:.2f} kg</li>"
            details += "</ul>"
        
        self.report_details.setText(details)

class SummaryView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.results = None
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Özet bilgileri
        self.summary_text = QLabel("Özet bilgileri burada görüntülenecek")
        self.summary_text.setWordWrap(True)
        self.summary_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.summary_text.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")
        
        # Grafikler
        charts_layout = QHBoxLayout()
        
        # Tipe göre pasta grafik
        self.type_chart = ChartCanvas(self, width=4, height=3)
        type_chart_container = QGroupBox("Tipe Göre Dağılım")
        type_chart_layout = QVBoxLayout(type_chart_container)
        type_chart_layout.addWidget(self.type_chart)
        
        # Çapa göre çubuk grafik
        self.diameter_chart = ChartCanvas(self, width=4, height=3)
        diameter_chart_container = QGroupBox("Çapa Göre Dağılım")
        diameter_chart_layout = QVBoxLayout(diameter_chart_container)
        diameter_chart_layout.addWidget(self.diameter_chart)
        
        charts_layout.addWidget(type_chart_container)
        charts_layout.addWidget(diameter_chart_container)
        
        layout.addWidget(self.summary_text)
        layout.addLayout(charts_layout)
    
    def set_results(self, results):
        self.results = results
        self.update_summary()
        self.update_charts()
    
    def update_summary(self):
        if not self.results:
            return
        
        # Özet metni oluştur
        summary = "<h2>RAPOR ANALİZ SONUÇLARI</h2>"
        summary += f"<p><b>Toplam Ağırlık:</b> {self.results.total_weight:.2f} kg ({self.results.total_weight/1000:.3f} ton)</p>"
        
        # Tipe göre dağılım
        summary += "<h3>Tipe Göre Dağılım:</h3>"
        summary += "<ul>"
        for type_name, weight in sorted(self.results.by_type.items(), key=lambda x: x[1], reverse=True):
            summary += f"<li><b>{type_name}:</b> {weight:.2f} kg ({weight/1000:.3f} ton)</li>"
        summary += "</ul>"
        
        # Çapa göre dağılım
        summary += "<h3>Çapa Göre Dağılım:</h3>"
        summary += "<ul>"
        for diameter, weight in sorted(self.results.by_diameter.items(), key=lambda x: x[1], reverse=True):
            summary += f"<li><b>{diameter}:</b> {weight:.2f} kg ({weight/1000:.3f} ton)</li>"
        summary += "</ul>"
        
        self.summary_text.setText(summary)
    
    def update_charts(self):
        if not self.results:
            return
        
        # Tipe göre pasta grafik
        self.type_chart.ax.clear()
        labels = list(self.results.by_type.keys())
        sizes = list(self.results.by_type.values())
        
        # En fazla 6 dilim göster, geri kalanını "Diğer" olarak birleştir
        if len(labels) > 6:
            top_labels = labels[:5]
            top_sizes = sizes[:5]
            other_size = sum(sizes[5:])
            top_labels.append("Diğer")
            top_sizes.append(other_size)
            labels = top_labels
            sizes = top_sizes
        
        self.type_chart.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        self.type_chart.ax.axis('equal')
        self.type_chart.draw()
        
        # Çapa göre çubuk grafik
        self.diameter_chart.ax.clear()
        labels = list(self.results.by_diameter.keys())
        values = list(self.results.by_diameter.values())
        
        # Değerlere göre sırala
        sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        
        # En fazla 10 çap göster
        if len(labels) > 10:
            labels = labels[:10]
            values = values[:10]
        
        x = np.arange(len(labels))
        self.diameter_chart.ax.bar(x, values)
        self.diameter_chart.ax.set_xticks(x)
        self.diameter_chart.ax.set_xticklabels(labels, rotation=45, ha='right')
        self.diameter_chart.ax.set_ylabel('Ağırlık (kg)')
        self.diameter_chart.fig.tight_layout()
        self.diameter_chart.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rapor Analiz ve Toplama Uygulaması")
        self.setMinimumSize(1000, 700)
        
        self.report_parser = ReportParser()
        self.report_calculator = ReportCalculator()
        
        self.init_ui()
        
        # Otomatik yenileme için timer ekle
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        
        # Otomatik yenileme butonu
        self.btn_auto_refresh = QPushButton("Otomatik Yenileme")
        self.btn_auto_refresh.setCheckable(True)
        self.btn_auto_refresh.toggled.connect(self.toggle_auto_refresh)
        self.control_layout.addWidget(self.btn_auto_refresh)
        
    def init_ui(self):
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Üst kontrol paneli
        control_panel = QGroupBox("Kontrol Paneli")
        control_layout = QHBoxLayout(control_panel)
        self.control_layout = control_layout  # Sınıf üyesi olarak kaydet
        
        # Rapor klasörü seçme butonu
        self.btn_select_folder = QPushButton("Rapor Klasörü Seç")
        self.btn_select_folder.clicked.connect(self.select_report_folder)
        control_layout.addWidget(self.btn_select_folder)
        
        # Analiz butonu
        self.btn_analyze = QPushButton("Raporları Analiz Et")
        self.btn_analyze.clicked.connect(self.analyze_reports)
        control_layout.addWidget(self.btn_analyze)
        
        # Excel'e aktar butonu
        self.btn_export = QPushButton("Excel'e Aktar")
        self.btn_export.clicked.connect(self.export_to_excel)
        control_layout.addWidget(self.btn_export)
        
        main_layout.addWidget(control_panel)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Rapor görüntüleme sekmesi
        self.report_viewer = ReportViewer()
        self.tab_widget.addTab(self.report_viewer, "Raporlar")
        
        # Mahal çarpanları sekmesi
        self.multiplier_widget = QWidget()
        multiplier_layout = QVBoxLayout(self.multiplier_widget)
        
        # Mahal çarpanları tablosu
        self.multiplier_table = QTableWidget(0, 3)
        self.multiplier_table.setHorizontalHeaderLabels(["Mahal", "Benzer Mahaller", "Çarpan"])
        self.multiplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.multiplier_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        multiplier_layout.addWidget(self.multiplier_table)
        
        # Yeni çarpan ekleme kontrolleri
        add_multiplier_layout = QHBoxLayout()
        
        self.mahal_combo = QComboBox()
        add_multiplier_layout.addWidget(QLabel("Mahal:"))
        add_multiplier_layout.addWidget(self.mahal_combo)
        
        self.similar_mahal_edit = QLineEdit()
        self.similar_mahal_edit.setPlaceholderText("Benzer mahaller (virgülle ayırın)")
        add_multiplier_layout.addWidget(QLabel("Benzer Mahaller:"))
        add_multiplier_layout.addWidget(self.similar_mahal_edit)
        
        self.multiplier_spin = QSpinBox()
        self.multiplier_spin.setMinimum(1)
        self.multiplier_spin.setMaximum(100)
        self.multiplier_spin.setValue(1)
        add_multiplier_layout.addWidget(QLabel("Çarpan:"))
        add_multiplier_layout.addWidget(self.multiplier_spin)
        
        self.btn_add_multiplier = QPushButton("Ekle")
        self.btn_add_multiplier.clicked.connect(self.add_multiplier)
        add_multiplier_layout.addWidget(self.btn_add_multiplier)
        
        multiplier_layout.addLayout(add_multiplier_layout)
        
        # Çarpan silme butonu
        self.btn_remove_multiplier = QPushButton("Seçili Çarpanı Sil")
        self.btn_remove_multiplier.clicked.connect(self.remove_multiplier)
        multiplier_layout.addWidget(self.btn_remove_multiplier)
        
        self.tab_widget.addTab(self.multiplier_widget, "Mahal Çarpanları")
        
        # Özet sekmesi
        self.summary_view = SummaryView()
        self.tab_widget.addTab(self.summary_view, "Özet")
        
        main_layout.addWidget(self.tab_widget)
        
        # Durum çubuğu
        self.statusBar().showMessage("Hazır")
    
    def select_report_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Rapor Klasörü Seç")
        if folder:
            self.statusBar().showMessage(f"Seçilen klasör: {folder}")
            file_count = self.report_parser.set_folder(folder)
            if file_count > 0:
                self.update_mahal_list()
                QMessageBox.information(self, "Bilgi", f"{file_count} rapor dosyası bulundu.")
            else:
                QMessageBox.warning(self, "Uyarı", "Seçilen klasörde rapor dosyası bulunamadı.")
    
    def update_mahal_list(self):
        # Mahal listesini güncelle
        mahaller = self.report_parser.get_mahal_list()
        self.mahal_combo.clear()
        self.mahal_combo.addItems(mahaller)
    
    def add_multiplier(self):
        mahal = self.mahal_combo.currentText()
        if not mahal:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir mahal seçin.")
            return
            
        similar_mahals = self.similar_mahal_edit.text().split(",")
        multiplier = self.multiplier_spin.value()
        
        # Çarpan ekle
        self.report_calculator.add_multiplier(mahal, similar_mahals, multiplier)
        
        # Tabloyu güncelle
        row = self.multiplier_table.rowCount()
        self.multiplier_table.insertRow(row)
        self.multiplier_table.setItem(row, 0, QTableWidgetItem(mahal))
        self.multiplier_table.setItem(row, 1, QTableWidgetItem(", ".join(similar_mahals)))
        self.multiplier_table.setItem(row, 2, QTableWidgetItem(str(multiplier)))
        
        # Alanları temizle
        self.similar_mahal_edit.clear()
        self.multiplier_spin.setValue(1)
        
        self.statusBar().showMessage(f"Mahal çarpanı eklendi: {mahal}")
    
    def remove_multiplier(self):
        selected_rows = self.multiplier_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bir çarpan seçin.")
            return
            
        row = selected_rows[0].row()
        mahal = self.multiplier_table.item(row, 0).text()
        
        # Çarpanı kaldır
        if self.report_calculator.remove_multiplier(row):
            self.multiplier_table.removeRow(row)
            self.statusBar().showMessage(f"Mahal çarpanı silindi: {mahal}")
    
    def analyze_reports(self):
        if not self.report_parser.report_files:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir rapor klasörü seçin.")
            return
            
        self.statusBar().showMessage("Raporlar analiz ediliyor...")
        
        # Raporları ayrıştır
        reports = self.report_parser.parse_all_reports()
        
        if not reports:
            QMessageBox.warning(self, "Uyarı", "Ayrıştırılabilir rapor bulunamadı.")
            self.statusBar().showMessage("Analiz başarısız")
            return
        
        # Raporları analiz et
        results = self.report_calculator.analyze_reports(reports)
        
        # Sonuçları göster
        self.report_viewer.set_reports(reports)
        self.summary_view.set_results(results)
        
        self.statusBar().showMessage(f"Analiz tamamlandı: {len(reports)} rapor, toplam {results.total_weight:.2f} kg")
        self.tab_widget.setCurrentIndex(2)  # Özet sekmesine geç
    
    def export_to_excel(self):
        if not self.report_calculator.results:
            QMessageBox.warning(self, "Uyarı", "Önce raporları analiz etmelisiniz.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Excel Dosyasını Kaydet", "", "Excel Files (*.xlsx)")
        if file_path:
            self.statusBar().showMessage("Excel'e aktarılıyor...")
            if self.report_calculator.export_to_excel(file_path):
                QMessageBox.information(self, "Bilgi", f"Excel dosyası kaydedildi:\n{file_path}")
                self.statusBar().showMessage(f"Excel dosyası kaydedildi: {file_path}")
            else:
                QMessageBox.warning(self, "Hata", "Excel dosyası kaydedilemedi.")
                self.statusBar().showMessage("Excel'e aktarma başarısız")

    def toggle_auto_refresh(self, checked):
        """Otomatik yenilemeyi aç/kapat"""
        if checked:
            # 10 saniyede bir yenile
            self.refresh_timer.start(10000)
            self.statusBar().showMessage("Otomatik yenileme açık (10 saniye)")
        else:
            self.refresh_timer.stop()
            self.statusBar().showMessage("Otomatik yenileme kapalı")
    
    def auto_refresh(self):
        """Otomatik yenileme işlemi"""
        if self.report_parser.report_files:
            self.statusBar().showMessage("Raporlar yenileniyor...")
            
            # Raporları yeniden ayrıştır
            reports = self.report_parser.parse_all_reports()
            
            if reports:
                # Raporları analiz et
                results = self.report_calculator.analyze_reports(reports)
                
                # Sonuçları güncelle
                self.report_viewer.set_reports(reports)
                self.summary_view.set_results(results)
                
                self.statusBar().showMessage(f"Yenileme tamamlandı: {len(reports)} rapor, toplam {results.total_weight:.2f} kg")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 