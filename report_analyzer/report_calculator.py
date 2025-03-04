from .data_models import MahalMultiplier, SummaryResult
import pandas as pd
import logging
import os
from datetime import datetime

# Loglama yapılandırması
logger = logging.getLogger("ReportCalculator")

class ReportCalculator:
    def __init__(self):
        self.multipliers = []  # MahalMultiplier nesneleri listesi
        self.reports = []
        self.results = None
    
    def add_multiplier(self, mahal, similar_mahals, multiplier):
        """Mahal çarpanı ekle"""
        # Boş string ve boşluk içeren öğeleri temizle
        similar_mahals = [m.strip() for m in similar_mahals if m.strip()]
        
        self.multipliers.append(MahalMultiplier(
            mahal=mahal,
            similar_mahals=similar_mahals,
            multiplier=multiplier
        ))
        logger.info(f"Mahal çarpanı eklendi: {mahal}, benzer mahaller: {similar_mahals}, çarpan: {multiplier}")
        return True
    
    def remove_multiplier(self, index):
        """Mahal çarpanını kaldır"""
        if 0 <= index < len(self.multipliers):
            removed = self.multipliers.pop(index)
            logger.info(f"Mahal çarpanı kaldırıldı: {removed.mahal}")
            return True
        return False
    
    def get_multiplier_for_mahal(self, mahal):
        """Belirli bir mahal için çarpan faktörünü döndür"""
        for m in self.multipliers:
            if mahal == m.mahal or mahal in m.similar_mahals:
                return m.multiplier
        return 1  # Varsayılan çarpan
    
    def analyze_reports(self, reports):
        """Raporları analiz et ve özet sonuçları hesapla"""
        self.reports = reports
        
        # Sonuç sözlükleri
        by_type = {}
        by_mahal = {}
        by_diameter = {}
        total_weight = 0
        
        # Rapor türü adlandırmaları
        type_names = {
            "STIRRUP": "Etriye",
            "MESH_WALL": "Perde Hasırı",
            "MESH_SLAB": "Döşeme Hasırı",
            "CONNECTION": "Ara Bağlantı",
            "REBAR": "Boy Demiri",
            "FOUNDATION": "Temel Demiri"
        }
        
        # Tüm raporları işle
        for report in reports:
            # Mahal için çarpan faktörünü al
            multiplier = self.get_multiplier_for_mahal(report.mahal)
            
            # Rapor tipine göre toplam
            type_name = type_names.get(report.type, report.type)
            if type_name not in by_type:
                by_type[type_name] = 0
            by_type[type_name] += report.total_weight * multiplier
            
            # Mahale göre toplam
            if report.mahal not in by_mahal:
                by_mahal[report.mahal] = 0
            by_mahal[report.mahal] += report.total_weight * multiplier
            
            # Rapor öğelerini işle
            for item in report.items:
                # Çapa göre toplam
                diameter_key = f"Ø{item.diameter}"
                if diameter_key not in by_diameter:
                    by_diameter[diameter_key] = 0
                by_diameter[diameter_key] += item.weight * multiplier
            
            # Genel toplam
            total_weight += report.total_weight * multiplier
        
        # Sonuçları oluştur
        self.results = SummaryResult(
            by_type=by_type,
            by_mahal=by_mahal,
            by_diameter=by_diameter,
            total_weight=total_weight
        )
        
        logger.info(f"Rapor analizi tamamlandı: {len(reports)} rapor, toplam ağırlık: {total_weight:.2f} kg")
        return self.results
    
    def export_to_excel(self, file_path):
        """Sonuçları Excel dosyasına aktar"""
        if not self.results:
            logger.warning("Excel'e aktarma başarısız: Sonuç bulunamadı")
            return False
        
        try:
            # Excel yazıcı oluştur
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            workbook = writer.book
            
            # Başlık formatı
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })
            
            # Sayı formatı
            number_format = workbook.add_format({'num_format': '#,##0.00'})
            
            # Tipe göre özet
            df_type = pd.DataFrame({
                'Tip': list(self.results.by_type.keys()),
                'Ağırlık (kg)': list(self.results.by_type.values()),
                'Ağırlık (ton)': [w/1000 for w in self.results.by_type.values()]
            })
            df_type = df_type.sort_values('Ağırlık (kg)', ascending=False)
            df_type.to_excel(writer, sheet_name='Tipe Göre Özet', index=False)
            
            # Tipe göre özet sayfasını biçimlendir
            type_sheet = writer.sheets['Tipe Göre Özet']
            type_sheet.set_column('A:A', 20)
            type_sheet.set_column('B:C', 15, number_format)
            
            # Başlıkları biçimlendir
            for col_num, value in enumerate(df_type.columns.values):
                type_sheet.write(0, col_num, value, header_format)
            
            # Mahale göre özet
            df_mahal = pd.DataFrame({
                'Mahal': list(self.results.by_mahal.keys()),
                'Ağırlık (kg)': list(self.results.by_mahal.values()),
                'Ağırlık (ton)': [w/1000 for w in self.results.by_mahal.values()],
                'Çarpan': [self.get_multiplier_for_mahal(m) for m in self.results.by_mahal.keys()]
            })
            df_mahal = df_mahal.sort_values('Ağırlık (kg)', ascending=False)
            df_mahal.to_excel(writer, sheet_name='Mahale Göre Özet', index=False)
            
            # Mahale göre özet sayfasını biçimlendir
            mahal_sheet = writer.sheets['Mahale Göre Özet']
            mahal_sheet.set_column('A:A', 25)
            mahal_sheet.set_column('B:C', 15, number_format)
            mahal_sheet.set_column('D:D', 10)
            
            # Başlıkları biçimlendir
            for col_num, value in enumerate(df_mahal.columns.values):
                mahal_sheet.write(0, col_num, value, header_format)
            
            # Çapa göre özet
            df_diameter = pd.DataFrame({
                'Çap': list(self.results.by_diameter.keys()),
                'Ağırlık (kg)': list(self.results.by_diameter.values()),
                'Ağırlık (ton)': [w/1000 for w in self.results.by_diameter.values()]
            })
            df_diameter = df_diameter.sort_values('Ağırlık (kg)', ascending=False)
            df_diameter.to_excel(writer, sheet_name='Çapa Göre Özet', index=False)
            
            # Çapa göre özet sayfasını biçimlendir
            diameter_sheet = writer.sheets['Çapa Göre Özet']
            diameter_sheet.set_column('A:A', 15)
            diameter_sheet.set_column('B:C', 15, number_format)
            
            # Başlıkları biçimlendir
            for col_num, value in enumerate(df_diameter.columns.values):
                diameter_sheet.write(0, col_num, value, header_format)
            
            # Tüm raporlar
            report_data = []
            for report in self.reports:
                multiplier = self.get_multiplier_for_mahal(report.mahal)
                report_data.append({
                    'Tip': report.type,
                    'Mahal': report.mahal,
                    'Tarih': report.date.strftime('%Y-%m-%d %H:%M:%S') if report.date else '',
                    'Ağırlık (kg)': report.total_weight,
                    'Çarpan': multiplier,
                    'Toplam Ağırlık (kg)': report.total_weight * multiplier,
                    'Dosya': os.path.basename(report.file_path)
                })
            
            df_reports = pd.DataFrame(report_data)
            df_reports = df_reports.sort_values(['Tip', 'Mahal'])
            df_reports.to_excel(writer, sheet_name='Tüm Raporlar', index=False)
            
            # Tüm raporlar sayfasını biçimlendir
            reports_sheet = writer.sheets['Tüm Raporlar']
            reports_sheet.set_column('A:A', 15)
            reports_sheet.set_column('B:B', 25)
            reports_sheet.set_column('C:C', 20)
            reports_sheet.set_column('D:D', 15, number_format)
            reports_sheet.set_column('E:E', 10)
            reports_sheet.set_column('F:F', 15, number_format)
            reports_sheet.set_column('G:G', 30)
            
            # Başlıkları biçimlendir
            for col_num, value in enumerate(df_reports.columns.values):
                reports_sheet.write(0, col_num, value, header_format)
            
            # Genel toplam
            df_total = pd.DataFrame({
                'Açıklama': ['Genel Toplam'],
                'Ağırlık (kg)': [self.results.total_weight],
                'Ağırlık (ton)': [self.results.total_weight / 1000]
            })
            df_total.to_excel(writer, sheet_name='Genel Toplam', index=False)
            
            # Genel toplam sayfasını biçimlendir
            total_sheet = writer.sheets['Genel Toplam']
            total_sheet.set_column('A:A', 20)
            total_sheet.set_column('B:C', 15, number_format)
            
            # Başlıkları biçimlendir
            for col_num, value in enumerate(df_total.columns.values):
                total_sheet.write(0, col_num, value, header_format)
            
            # Excel dosyasını kaydet
            writer.close()
            
            logger.info(f"Excel dosyası kaydedildi: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Excel'e aktarma hatası: {str(e)}")
            return False 