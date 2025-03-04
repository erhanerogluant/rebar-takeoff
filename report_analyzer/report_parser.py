import os
import re
from datetime import datetime
from .data_models import Report, ReportItem
import logging

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/report_analyzer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ReportParser")

class ReportParser:
    def __init__(self):
        self.folder_path = ""
        self.report_files = []
    
    def set_folder(self, folder_path):
        """Rapor klasörünü ayarla ve dosyaları listele"""
        self.folder_path = folder_path
        self.report_files = []
        
        # Klasördeki tüm .txt dosyalarını bul
        for file in os.listdir(folder_path):
            if file.endswith(".txt"):
                self.report_files.append(os.path.join(folder_path, file))
        
        logger.info(f"Rapor klasörü ayarlandı: {folder_path}, {len(self.report_files)} dosya bulundu")
        return len(self.report_files)
    
    def get_mahal_list(self):
        """Tüm raporlardaki mahal listesini döndür"""
        mahaller = set()
        
        for file_path in self.report_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Mahal bilgisini bul
                    mahal_match = re.search(r'Mahal: (.+?)\n', content)
                    if mahal_match:
                        mahaller.add(mahal_match.group(1).strip())
            except Exception as e:
                logger.error(f"Mahal listesi alınırken hata: {str(e)}, dosya: {file_path}")
        
        logger.info(f"{len(mahaller)} farklı mahal bulundu")
        return sorted(list(mahaller))
    
    def parse_report(self, file_path):
        """Tek bir rapor dosyasını ayrıştır"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Rapor türünü belirle
            report_type = None
            if "ETRİYE RAPORU" in content:
                report_type = "STIRRUP"
            elif "PERDE HASIRLARI RAPORU" in content:
                report_type = "MESH_WALL"
            elif "DÖŞEME HASIRLARI RAPORU" in content:
                report_type = "MESH_SLAB"
            elif "ARA BAĞLANTI RAPORU" in content:
                report_type = "CONNECTION"
            elif "BOY DEMİRİ RAPORU" in content:
                report_type = "REBAR"
            elif "TEMEL DEMİRİ RAPORU" in content:
                report_type = "FOUNDATION"
            
            if not report_type:
                logger.warning(f"Bilinmeyen rapor türü: {file_path}")
                return None
            
            # Mahal ve tarih bilgisini çıkar
            mahal_match = re.search(r'Mahal: (.+?)\n', content)
            date_match = re.search(r'Tarih: (.+?)\n', content)
            
            mahal = mahal_match.group(1).strip() if mahal_match else "Bilinmiyor"
            date_str = date_match.group(1).strip() if date_match else None
            
            date = None
            if date_str:
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except:
                    logger.warning(f"Tarih ayrıştırma hatası: {date_str}")
            
            # Toplam ağırlık bilgisini çıkar
            total_weight_match = re.search(r'Toplam Ağırlık: (\d+\.\d+) kg', content)
            total_weight = float(total_weight_match.group(1)) if total_weight_match else 0
            
            # Rapor öğelerini çıkar
            items = []
            
            # Çap bazında grupları bul
            diameter_sections = re.findall(r'Ø(\d+\.\d+):\n(.*?)(?=Ø\d+\.\d+:|\nKategori Toplamı:)', content, re.DOTALL)
            
            for diameter_str, section in diameter_sections:
                diameter = float(diameter_str)
                
                # Bu çaptaki öğeleri bul
                item_matches = re.findall(r'\* (.+?)\n\s+Alan: .+?, Ağırlık: (\d+\.\d+) kg', section)
                
                for description, weight_str in item_matches:
                    weight = float(weight_str)
                    
                    # Adet bilgisini çıkar
                    count_match = re.search(r'(\d+)x', description)
                    count = int(count_match.group(1)) if count_match else 1
                    
                    # Boy bilgisini çıkar
                    length_match = re.search(r'L=(\d+\.\d+|\d+)', description)
                    length = float(length_match.group(1)) if length_match else 0
                    
                    # Aralık bilgisini çıkar
                    spacing_match = re.search(r'/(\d+\.\d+|\d+)', description)
                    spacing = float(spacing_match.group(1)) if spacing_match else 0
                    
                    items.append(ReportItem(
                        description=description.strip(),
                        diameter=diameter,
                        weight=weight,
                        count=count,
                        length=length,
                        spacing=spacing
                    ))
            
            # Rapor nesnesini oluştur
            report = Report(
                type=report_type,
                mahal=mahal,
                date=date,
                total_weight=total_weight,
                items=items,
                file_path=file_path
            )
            
            logger.info(f"Rapor ayrıştırıldı: {report_type}, {mahal}, {total_weight} kg, {len(items)} öğe")
            return report
            
        except Exception as e:
            logger.error(f"Rapor ayrıştırma hatası: {str(e)}, dosya: {file_path}")
            return None
    
    def parse_all_reports(self):
        """Tüm rapor dosyalarını ayrıştır"""
        reports = []
        
        for file_path in self.report_files:
            report = self.parse_report(file_path)
            if report:
                reports.append(report)
        
        logger.info(f"Toplam {len(reports)} rapor ayrıştırıldı")
        return reports 