import ezdxf
import re
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional
import logging
from datetime import datetime
import os
from report_manager import ReportManager

@dataclass
class RebarData:
    type: str          # 'STIRRUP', 'REBAR', 'WALL', or 'SLAB'
    diameter: float
    spacing: Optional[float]
    length: float
    count: int
    total_length: float
    weight_per_meter: float  # kg/mt veya kg/m2
    total_weight: float      # kg
    description: str
    mesh_code: Optional[str] = None  # Hasır kodu (Q257/257, R257, vs.)
    area: Optional[float] = None     # Hasır alanı (m2)
    width: Optional[float] = None    # Hasır genişliği (cm)
    height: Optional[float] = None    # Hasır yüksekliği (cm)

class RebarCalculator:
    def __init__(self):
        """Hesaplayıcıyı başlat"""
        # Demir çapına göre birim ağırlık tablosu (kg/m)
        self.weight_table = {
            6: 0.222,
            8: 0.395,
            10: 0.617,
            12: 0.888,
            14: 1.208,
            16: 1.578,
            18: 1.998,
            20: 2.466,
            22: 2.984,
            24: 3.551,
            26: 4.168,
            28: 4.834,
            30: 5.549,
            32: 6.313,
        }
        
        # Hasır tipleri için birim ağırlık tablosu (kg/m²)
        self.mesh_types = {
            'Q106': 1.06,
            'Q131': 1.31,
            'Q158': 1.58,
            'Q188': 1.88,
            'Q221': 2.21,
            'Q257': 2.57,
            'Q295': 2.95,
            'Q317': 3.17,
            'Q335': 3.35,
            'Q377': 3.77,
            'Q424': 4.24,
            'Q503': 5.03,
            'Q513': 5.13,
            'Q524': 5.24,
            'Q589': 5.89,
            'Q636': 6.36,
            'Q785': 7.85,
            
            'R106': 1.06,
            'R131': 1.31,
            'R158': 1.58,
            'R188': 1.88,
            'R221': 2.21,
            'R257': 2.57,
            'R295': 2.95,
            'R317': 3.17,
            'R335': 3.35,
            'R377': 3.77,
            'R443': 4.43,
            'R513': 5.13,
            'R524': 5.24,
            'R589': 5.89
        }
        
        # Hasır standart ebatları (cm)
        self.mesh_dimensions = {
            'Q': {'length': 500, 'width': 215},  # Q tipi hasırlar için
            'R': {'length': 500, 'width': 215},  # R tipi hasırlar için
            'TR': {'length': 500, 'width': 215}  # TR tipi hasırlar için
        }
        
        self.pattern_handlers = {
            # Etriye pattern'leri
            r'[ƒ∅](\d+)\s*Etr\.\s*[lL]\s*=\s*(\d+)ÿ*': self._handle_stirrup_length,
            r'Etr\.(?:%%C|[ƒ∅])(\d+)/(\d+)': self._handle_stirrup_spacing,
            
            # Boy demiri pattern'leri
            r'(\d+)[xX](\d+)(?:%%C|[ƒ∅])(\d+)': self._handle_rebar_count,  # 2X13∅20 formatı için
            r'[lL]\s*=\s*(\d+)': self._handle_length_only  # L=397 formatı için
        }
        self.current_data = {}
        self.results: List[RebarData] = []
        
        # Kategori bazlı verileri saklamak için sözlük
        self.category_data = {}
        
        # Logger'ı ayarla
        self.logger = logging.getLogger('RebarCalculator')
        self.logger.setLevel(logging.INFO)
        
        # Dosya handler'ı
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f'rebar_calc_{datetime.now().strftime("%Y-%m-%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(file_handler)

        self.report_manager = ReportManager()

    def setup_logging(self):
        """Loglama sistemini kur"""
        # Log klasörü oluştur
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Günlük log dosyası adı
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = f'logs/rebar_calc_{today}.log'
        
        # Logger ayarları
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # GUI handler
        class GUIHandler(logging.Handler):
            def __init__(self, gui_callback):
                super().__init__()
                self.gui_callback = gui_callback
                
            def emit(self, record):
                msg = self.format(record)
                self.gui_callback(msg)
        
        # Logger setup
        self.logger = logging.getLogger('rebar_calculator')
        self.logger.setLevel(logging.INFO)
        
        # Önceki handler'ları temizle
        self.logger.handlers = []
        
        # Handler'ları ekle
        self.logger.addHandler(file_handler)
        self.gui_handler = None  # GUI handler için yer tutucu

    def log_calculation(self, calc_type: str, input_data: str, result: RebarData):
        """Hesaplama sonucunu logla"""
        try:
            if calc_type in ['WALL', 'SLAB']:
                self.logger.info(
                    f"\nHASIR HESABI ({calc_type}):"
                    f"\nGirdi: {input_data}"
                    f"\nTip: {result.mesh_code}"
                    f"\nBoyutlar: {result.width}x{result.length} cm"
                    f"\nAdet: {result.count}"
                    f"\nAlan: {result.area:.2f} m²"
                    f"\nBirim Ağırlık: {result.weight_per_meter:.2f} kg/m²"
                    f"\nToplam Ağırlık: {result.total_weight:.2f} kg"
                )
            else:
                self.logger.info(
                    f"\n{calc_type} HESABI:"
                    f"\nGirdi: {input_data}"
                    f"\nÇap: Ø{result.diameter}"
                    f"\nAralık: {result.spacing if result.spacing else '-'} cm"
                    f"\nBoy: {result.length} cm"
                    f"\nAdet: {result.count}"
                    f"\nToplam Boy: {result.total_length/100:.2f} m"
                    f"\nBirim Ağırlık: {result.weight_per_meter:.3f} kg/mt"
                    f"\nToplam Ağırlık: {result.total_weight:.2f} kg"
                )
        except Exception as e:
            self.logger.error(f"Loglama hatası: {str(e)}")

    def log_summary(self, result_type):
        """Hesaplama sonuçlarını logla"""
        try:
            # İlgili sonuçları filtrele
            results = [r for r in self.results if r.type == result_type]
            
            # Özeti logla
            if results:
                total_weight = sum(r.total_weight for r in results)
                self.logger.info(
                    f"\n{result_type} HESABI ÖZETİ:"
                    f"\nToplam sonuç sayısı: {len(results)}"
                    f"\nToplam ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)"
                )
            
        except Exception as e:
            print(f"Loglama hatası: {str(e)}")
            self.logger.error(f"Loglama hatası: {str(e)}")

    def _handle_stirrup_length(self, match) -> dict:
        diameter = float(match.group(1))
        length = float(match.group(2))
        return {'diameter': diameter, 'length': length, 'type': 'STIRRUP'}

    def _handle_stirrup_spacing(self, match) -> dict:
        diameter = float(match.group(1))
        spacing = float(match.group(2))
        print(f"Algılanan değerler - Çap: {diameter}, Aralık: {spacing} cm")
        return {'diameter': diameter, 'spacing': spacing}

    def _handle_rebar_count(self, match) -> dict:
        multiplier = int(match.group(1))  # 2
        count = int(match.group(2))       # 13
        diameter = float(match.group(3))  # 20
        total_count = multiplier * count  # 2 * 13 = 26
        
        print(f"Boy demiri algılandı:")
        print(f"- {multiplier} x {count} adet")
        print(f"- Çap: Ø{diameter}")
        print(f"- Toplam adet: {total_count}")
        
        return {
            'type': 'REBAR',
            'count': total_count,
            'diameter': diameter
        }

    def _handle_length_only(self, match) -> dict:
        return {'length': float(match.group(1))}

    def parse_text(self, text: str) -> dict:
        print(f"Parse ediliyor: {text}")  # Debug için
        for pattern, handler in self.pattern_handlers.items():
            match = re.search(pattern, text)
            if match:
                print(f"Pattern eşleşti: {pattern}")  # Debug için
                result = handler(match)
                print(f"Handler sonucu: {result}")  # Debug için
                return result
        print(f"Hiçbir pattern eşleşmedi!")  # Debug için
        return {}

    def calculate_rebar_count(self, total_length: float, spacing: float) -> int:
        # Toplam uzunluğu aralığa böl ve yukarı yuvarla
        count = int((total_length / spacing) + 1)
        print(f"\nEtriye Adedi Hesabı:")
        print(f"Kolon boyu: {total_length} cm")
        print(f"Etriye aralığı: {spacing} cm")
        print(f"Hesaplama: {total_length} cm / {spacing} cm + 1 = {count} adet")
        return count

    def calculate_total_length(self, piece_length: float, count: int) -> float:
        # Parça boyu ile adet çarpımı
        total = piece_length * count
        meters = total / 100  # cm'den metreye çevir
        print(f"\nToplam Boy Hesabı:")
        print(f"Etriye boyu: {piece_length} cm")
        print(f"Etriye adedi: {count}")
        print(f"Toplam boy: {piece_length} cm × {count} adet = {total} cm")
        print(f"Metre cinsinden: {meters:.2f} m")
        return total

    def calculate_weight(self, diameter: float, total_length: float) -> float:
        """Toplam ağırlığı hesapla (kg)"""
        weight_per_meter = self.weight_table.get(diameter, 0)
        total_meters = total_length / 100  # cm'den metreye çevir
        total_weight = total_meters * weight_per_meter
        return total_weight, weight_per_meter

    def calculate_area(self, width: float, length: float) -> float:
        """Alan hesapla (m2)"""
        return (width * length) / 10000  # cm2'den m2'ye çevir

    def process_text(self, text):
        """Text'i işle ve sonucu hesapla"""
        try:
            print(f"İşlenen text: {text}")
            
            # Etriye formatı kontrolü
            if "Etr." in text:
                # Çap bilgisini al (ƒ10 formatı için)
                diameter_match = re.search(r'[ƒØ∅](\d+)', text)
                if not diameter_match:
                    # %%C10 formatı için kontrol et
                    diameter_match = re.search(r'%%C(\d+)', text)
                    if not diameter_match:
                        print("Çap bilgisi bulunamadı!")
                        return False
                
                diameter = float(diameter_match.group(1))
                print(f"Çap: Ø{diameter}")
                
                # Boy bilgisini al (ÿ karakterlerini temizle)
                text = text.replace('ÿ', '')
                length_match = re.search(r'[Ll]\s*=\s*(\d+)', text)
                if not length_match:
                    print("Boy bilgisi bulunamadı!")
                    return False
                length = float(length_match.group(1))
                print(f"Boy: {length} cm")
                
                # Aralık bilgisini al (/8 formatı için)
                spacing_match = re.search(r'/(\d+)', text)
                if spacing_match:
                    spacing = float(spacing_match.group(1))
                    print(f"Aralık: {spacing} cm")
                else:
                    spacing = None
                    print("Aralık bilgisi bulunamadı")
                
                # Geçici veriyi kaydet
                self.current_data = {
                    'type': 'STIRRUP',
                    'diameter': diameter,
                    'length': length,
                    'spacing': spacing
                }
                
                print(f"Etriye bilgileri kaydedildi: {self.current_data}")
                return True
                
        except Exception as e:
            print(f"Text işleme hatası: {str(e)}")
            return False

    def process_dimension(self, measurement: float):
        """Etriye hesabını yap"""
        try:
            print(f"\nEtriye Hesabı Başlatıldı:")
            print(f"- Kolon boyu (dimension): {measurement} cm")
            
            if not self.current_data or 'type' not in self.current_data:
                print("Hata: Etriye verisi bulunamadı!")
                return False
            
            if self.current_data['type'] == 'STIRRUP':
                diameter = self.current_data['diameter']
                length = self.current_data['length']  # Etriye boyu (168 cm)
                spacing = self.current_data['spacing']  # Aralık (8 cm)
                
                print(f"- Etriye çapı: Ø{diameter}")
                print(f"- Etriye boyu: {length} cm")
                print(f"- Etriye aralığı: {spacing} cm")
                
                # Adet hesabı: Kolon boyu / aralık + 1
                count = int(measurement / spacing) + 1
                print(f"- Etriye adedi: {measurement} cm / {spacing} cm + 1 = {count} adet")
                
                # Toplam boy hesabı: Etriye boyu × adet
                total_length = length * count
                print(f"- Toplam boy: {length} cm × {count} adet = {total_length} cm ({total_length/100:.2f} m)")
                
                # Ağırlık hesabı
                weight_per_meter = self.weight_table.get(diameter, 0)
                total_weight = (total_length / 100) * weight_per_meter  # cm'yi metreye çevir
                
                print(f"- Birim ağırlık: {weight_per_meter:.3f} kg/mt")
                print(f"- Toplam ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)")
                
                # Sonucu kaydet
                new_result = RebarData(
                    type='STIRRUP',
                    diameter=diameter,
                    spacing=spacing,
                    length=length,
                    count=count,
                    total_length=total_length,
                    weight_per_meter=weight_per_meter,
                    total_weight=total_weight,
                    description=f"Etriye Ø{diameter}/{spacing}"
                )
                
                self.results.append(new_result)
                return True
                
        except Exception as e:
            print(f"Hesaplama hatası: {str(e)}")
            return False

    def export_results(self, filename: str):
        # CSV'ye kaydet
        df = pd.DataFrame([vars(result) for result in self.results])
        df.to_csv(f"{filename}.csv", index=False)
        
        # Text dosyasına detaylı rapor
        with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
            f.write("DEMIR METRAJI RAPORU\n")
            f.write("=" * 50 + "\n\n")
            
            # Hasır ve nervürlü demir için ayrı toplamlar
            totals = {
                'REBAR': {},  # Nervürlü demirler için
                'MESH': {},   # Hasırlar için
                'total_weight': 0
            }
            
            # Detaylı liste
            f.write("DETAYLI LİSTE\n")
            f.write("=" * 30 + "\n\n")
            
            for result in self.results:
                f.write(f"Tip: {result.type}\n")
                if result.type in ['WALL', 'SLAB']:  # Hasır hesabı
                    f.write(f"Hasır Tipi: {result.mesh_code}\n")
                    f.write(f"Boyutlar: {result.width}x{result.length} cm\n")
                    f.write(f"Adet: {result.count}\n")
                    f.write(f"Alan: {result.area:.2f} m²\n")
                    f.write(f"Birim Ağırlık: {result.weight_per_meter:.3f} kg/m²\n")
                    
                    # Hasır toplamlarını güncelle
                    if result.mesh_code not in totals['MESH']:
                        totals['MESH'][result.mesh_code] = {
                            'area': 0,
                            'weight': 0
                        }
                    totals['MESH'][result.mesh_code]['area'] += result.area
                    totals['MESH'][result.mesh_code]['weight'] += result.total_weight
                    
                else:  # Nervürlü demir hesabı
                    f.write(f"Çap: Ø{result.diameter}\n")
                    if result.spacing:
                        f.write(f"Aralık: {result.spacing} cm\n")
                    f.write(f"Boy: {result.length} cm\n")
                    f.write(f"Adet: {result.count}\n")
                    f.write(f"Toplam Boy: {result.total_length} cm ({result.total_length/100:.2f} m)\n")
                    f.write(f"Birim Ağırlık: {result.weight_per_meter:.3f} kg/mt\n")
                    
                    # Nervürlü demir toplamlarını güncelle
                    if result.diameter not in totals['REBAR']:
                        totals['REBAR'][result.diameter] = {
                            'length': 0,
                            'weight': 0
                        }
                    totals['REBAR'][result.diameter]['length'] += result.total_length
                    totals['REBAR'][result.diameter]['weight'] += result.total_weight
                
                f.write(f"Toplam Ağırlık: {result.total_weight:.2f} kg\n")
                f.write(f"Açıklama: {result.description}\n")
                f.write("-" * 30 + "\n")
                
                totals['total_weight'] += result.total_weight
            
            # Özet rapor
            f.write("\nÖZET RAPOR\n")
            f.write("=" * 30 + "\n")
            
            # Nervürlü demir özeti
            if totals['REBAR']:
                f.write("\nNERVÜRLÜ DEMİRLER:\n")
                f.write("-" * 20 + "\n")
                for diameter in sorted(totals['REBAR'].keys()):
                    data = totals['REBAR'][diameter]
                    meters = data['length'] / 100
                    f.write(f"Ø{diameter}:\n")
                    f.write(f"- Toplam Boy: {meters:.2f} metre\n")
                    f.write(f"- Toplam Ağırlık: {data['weight']:.2f} kg\n")
            
            # Hasır özeti
            if totals['MESH']:
                f.write("\nHASIR DONATILAR:\n")
                f.write("-" * 20 + "\n")
                for mesh_code in sorted(totals['MESH'].keys()):
                    data = totals['MESH'][mesh_code]
                    f.write(f"{mesh_code}:\n")
                    f.write(f"- Toplam Alan: {data['area']:.2f} m²\n")
                    f.write(f"- Toplam Ağırlık: {data['weight']:.2f} kg\n")
            
            # Genel toplam
            f.write("\nGENEL TOPLAM\n")
            f.write("=" * 30 + "\n")
            f.write(f"Toplam Ağırlık: {totals['total_weight']:.2f} kg ({totals['total_weight']/1000:.3f} ton)\n")

    def process_wall_mesh(self, mesh_text: str, dimensions_text: str) -> bool:
        """Perde hasır hesabını yap"""
        try:
            # Hasır tipi işleme
            match = re.search(r'(\d+)[xX]([QR]\d+(?:/\d+)?)', mesh_text)
            if match:
                count = int(match.group(1))
                mesh_code = match.group(2)
                
                # Boyutlar işleme
                dim_match = re.search(r'(\d+)[xX](\d+)', dimensions_text)
                if dim_match:
                    width = float(dim_match.group(1))
                    length = float(dim_match.group(2))
                    
                    area = self.calculate_area(width, length)
                    weight_per_m2 = self.mesh_types.get(mesh_code, 0)
                    total_weight = area * count * weight_per_m2
                    
                    new_result = RebarData(
                        type='WALL',
                        diameter=0,  # Hasır için çap kullanılmıyor
                        spacing=None,
                        length=length,
                        count=count,
                        total_length=0,  # Hasır için boy yerine alan kullanılıyor
                        weight_per_meter=weight_per_m2,  # kg/m2
                        total_weight=total_weight,
                        description=f"Perde Hasır {count}x{mesh_code} ({width}x{length})",
                        mesh_code=mesh_code,
                        area=area * count,
                        width=width
                    )
                    
                    self.results.append(new_result)
                    print(f"\nPerde hasır hesabı tamamlandı:")
                    print(f"- Tip: {count}x{mesh_code}")
                    print(f"- Boyutlar: {width}x{length} cm")
                    print(f"- Alan: {area:.2f} m2")
                    print(f"- Toplam Alan: {area * count:.2f} m2")
                    print(f"- Birim Ağırlık: {weight_per_m2:.2f} kg/m2")
                    print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
                    
                    # Sonucu logla
                    self.log_calculation('WALL', f"{mesh_text} - {dimensions_text}", new_result)
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False

    def process_slab_mesh(self, mesh_text: str) -> bool:
        """Döşeme hasır hesabını yap"""
        try:
            # Q ve R tipi hasır formatı: "Q257/257  450/215" şeklinde
            qr_match = re.search(r'([QR]\d+(?:/\d+)?)\s*(\d+)/(\d+)', mesh_text)
            if qr_match:
                mesh_code = qr_match.group(1)  # Q257/257
                length = float(qr_match.group(2))  # 450
                width = float(qr_match.group(3))  # 215
                count = 1  # Varsayılan adet
                
                # Eğer başında adet varsa (örn: 2xQ257/257)
                count_match = re.search(r'(\d+)[xX]', mesh_text)
                if count_match:
                    count = int(count_match.group(1))
            
            area = self.calculate_area(width, length)
            weight_per_m2 = self.mesh_types.get(mesh_code, 0)
            total_weight = area * count * weight_per_m2
            
            new_result = RebarData(
                type='SLAB',  # 'MESH_SLAB' yerine 'SLAB' kullan
                diameter=0,
                spacing=None,
                length=length,
                count=count,
                total_length=0,
                weight_per_meter=weight_per_m2,
                total_weight=total_weight,
                description=f"Döşeme Hasır {count}x{mesh_code} ({length}x{width})",
                mesh_code=mesh_code,
                area=area * count,
                width=width,
                height=length
            )
            
            self.results.append(new_result)
            
            # Sonucu logla
            self.log_calculation('SLAB', mesh_text, new_result)
            return True
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False

    def extract_length(self, text: str) -> Optional[float]:
        """Text içinden boy uzunluğunu çıkar"""
        length_match = re.search(r'[lL]\s*=\s*(\d+)', text)
        if length_match:
            return float(length_match.group(1))
        return None

    def process_connection_rebar(self, text: str, length_text: str = None, dimension: float = None) -> bool:
        """Ara bağlantı demiri hesabını yap"""
        try:
            # 2X∅12/15 veya 2xƒ8/20 veya ∅8/20 formatları için
            match = re.search(r'(?:(\d+)[xX])?[ƒ∅%%C](\d+)/(\d+)', text)
            if match:
                count_multiplier = int(match.group(1)) if match.group(1) else 1
                diameter = float(match.group(2))
                spacing = float(match.group(3))
                
                # Önce text içinde L= var mı kontrol et
                piece_length = self.extract_length(text)
                if not piece_length and length_text:
                    piece_length = self.extract_length(length_text)
                
                if not piece_length:
                    print("Hata: Boy uzunluğu bulunamadı!")
                    return False
                
                # Aralığa göre toplam adet hesabı
                total_count = round(dimension / spacing) + 1  # +1 başlangıç için
                total_count *= count_multiplier  # Çarpan ile çarp (2x ise 2 ile)
                
                # Toplam boy ve ağırlık hesabı
                total_length = total_count * piece_length  # cm cinsinden
                total_weight, weight_per_meter = self.calculate_weight(diameter, total_length)
                
                new_result = RebarData(
                    type='CONNECTION',
                    diameter=diameter,
                    spacing=spacing,
                    length=piece_length,
                    count=total_count,
                    total_length=total_length,
                    weight_per_meter=weight_per_meter,
                    total_weight=total_weight,
                    description=f"Ara Bağlantı {count_multiplier}x∅{diameter}/{spacing}"
                )
                
                self.results.append(new_result)
                print(f"\nAra bağlantı hesabı tamamlandı:")
                print(f"- Tip: {count_multiplier}x∅{diameter}/{spacing}")
                print(f"- Boy: {piece_length} cm")
                print(f"- Aralık: {spacing} cm")
                print(f"- Hesap uzunluğu: {dimension} cm")
                print(f"- Adet: {total_count}")
                print(f"- Toplam Boy: {total_length} cm ({total_length/100:.2f} m)")
                print(f"- Birim Ağırlık: {weight_per_meter:.3f} kg/mt")
                print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
                
                # Sonucu logla
                self.log_calculation('CONNECTION', f"{text} - {length_text} - {dimension}", new_result)
                return True
                
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False

    def show_summary(self, result_type):
        """Hesaplama özetini göster"""
        try:
            results = [r for r in self.results if r.type == result_type]
            if not results:
                return

            print("\nÖZET RAPOR")
            print("="*50)
            print("\nDÖŞEME HASIRLARI:")
            print("-"*30)

            # Hasır gruplarını oluştur
            mesh_groups = {}
            for result in results:
                if result.mesh_code not in mesh_groups:
                    mesh_groups[result.mesh_code] = {
                        'area': 0,
                        'count': 0,
                        'weight': 0
                    }
                group = mesh_groups[result.mesh_code]
                group['area'] += result.area
                group['count'] += result.count
                group['weight'] += result.total_weight

            # Grupları yazdır
            for mesh_code, group in mesh_groups.items():
                print(f"\n{mesh_code}:")
                print(f"- Alan: {group['area']:.2f} m²")
                print(f"- Adet: {group['count']} adet")
                print(f"- Ağırlık: {group['weight']:.2f} kg")

            # Genel toplam
            total_area = sum(g['area'] for g in mesh_groups.values())
            total_count = sum(g['count'] for g in mesh_groups.values())
            total_weight = sum(g['weight'] for g in mesh_groups.values())

            print("\nGENEL TOPLAM")
            print("="*30)
            print(f"Toplam Alan: {total_area:.2f} m²")
            print(f"Toplam Adet: {total_count} adet")
            print(f"Toplam Ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)")

        except Exception as e:
            print(f"Özet gösterme hatası: {str(e)}")

    def calculate_totals(self):
        totals = {
            'STIRRUP': {},    # Etriyeler için
            'REBAR': {},      # Boy demirleri için
            'CONNECTION': {},  # Ara bağlantılar için
            'WALL': {},       # Perde hasırları için
            'SLAB': {},       # Döşeme hasırları için
        }

        # Sonuçları kategorilere ayır
        for result in self.results:
            if result.type in ['WALL', 'SLAB']:
                # Hasır hesapları için
                if result.mesh_code not in totals[result.type]:
                    totals[result.type][result.mesh_code] = {
                        'area': 0,
                        'weight': 0,
                        'count': 0
                    }
                totals[result.type][result.mesh_code]['area'] += result.area
                totals[result.type][result.mesh_code]['weight'] += result.total_weight
                totals[result.type][result.mesh_code]['count'] += result.count
            else:
                # Nervürlü demirler için
                key = f"Ø{result.diameter}"
                if key not in totals[result.type]:
                    totals[result.type][key] = {
                        'length': 0,
                        'weight': 0,
                        'count': 0
                    }
                totals[result.type][key]['length'] += result.total_length
                totals[result.type][key]['weight'] += result.total_weight
                totals[result.type][key]['count'] += result.count

        return totals

    def format_category_summary(self, category_type, data):
        summary = ""
        total_weight = sum(item['weight'] for item in data.values())
        
        if category_type in ['WALL', 'SLAB']:
            total_area = sum(item['area'] for item in data.values())
            total_count = sum(item['count'] for item in data.values())
            
            for mesh_code, values in data.items():
                summary += f"\n{mesh_code}:"
                summary += f"\n- Toplam Alan: {values['area']:.2f} m²"
                summary += f"\n- Toplam Adet: {values['count']} adet"
                summary += f"\n- Toplam Ağırlık: {values['weight']:.2f} kg"
            
            summary += f"\n\nKategori Toplamı:"
            summary += f"\n- Toplam Alan: {total_area:.2f} m²"
            summary += f"\n- Toplam Adet: {total_count} adet"
            summary += f"\n- Toplam Ağırlık: {total_weight:.2f} kg"
        else:
            total_length = sum(item['length'] for item in data.values())
            total_count = sum(item['count'] for item in data.values())
            
            for diameter, values in data.items():
                summary += f"\n{diameter}:"
                summary += f"\n- Toplam Boy: {values['length']/100:.2f} m"
                summary += f"\n- Toplam Adet: {values['count']} adet"
                summary += f"\n- Toplam Ağırlık: {values['weight']:.2f} kg"
            
            summary += f"\n\nKategori Toplamı:"
            summary += f"\n- Toplam Boy: {total_length/100:.2f} m"
            summary += f"\n- Toplam Adet: {total_count} adet"
            summary += f"\n- Toplam Ağırlık: {total_weight:.2f} kg"
        
        return summary

    def calculate_mesh(self, mesh_type, width, height):
        """Hasır hesaplamalarını yap"""
        try:
            # Hasır tipinden çap bilgisini al
            if '/' in mesh_type:  # Q257/257 formatı
                mesh_code = mesh_type.split('/')[0]  # Q257
            else:  # R257 formatı
                mesh_code = mesh_type
            
            # Çap ve aralık bilgilerini al
            diameter, spacing = self.get_mesh_properties(mesh_code)
            
            # Alan hesabı (m2)
            area = (width * height) / 10000
            
            # Ağırlık hesabı
            weight_per_m2 = self.mesh_types.get(mesh_code, 0)
            total_weight = area * weight_per_m2
            
            # Kategori tipini belirle
            category_type = 'SLAB'  # 'MESH_SLAB' yerine 'SLAB' kullan
            
            print(f"\nDEBUG: Hasır tipi belirlendi: {category_type}")
            
            # Sonucu kaydet
            result = RebarData(
                type=category_type,  # Burada da 'SLAB' kullanılacak
                diameter=diameter,
                length=height,
                count=1,
                total_length=0,
                weight_per_meter=weight_per_m2,
                total_weight=total_weight,
                description=f"{mesh_type} {width}×{height}",
                mesh_code=mesh_code,
                width=width,
                height=height,
                spacing=spacing,
                area=area
            )
            
            self.results.append(result)
            
            # Log mesajını oluştur
            log_message = f"\nHasır Hesaplama Sonucu:"
            log_message += f"\n- Tip: {mesh_type}"
            log_message += f"\n- Boyutlar: {width}×{height} cm"
            log_message += f"\n- Alan: {area:.2f} m²"
            log_message += f"\n- Birim Ağırlık: {weight_per_m2:.2f} kg/m²"
            log_message += f"\n- Toplam Ağırlık: {total_weight:.2f} kg"
            
            # Genel toplam ağırlığı hesapla ve ekle
            total_weight_all = sum(r.total_weight for r in self.results)
            log_message += f"\n\nGenel Toplam Ağırlık: {total_weight_all:.2f} kg ({total_weight_all/1000:.3f} ton)"
            
            # Logger'a gönder
            self.logger.info(log_message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Hasır hesaplama hatası: {str(e)}")
            return False

    def get_mesh_properties(self, mesh_code):
        """Hasır özelliklerini al"""
        try:
            # Q ve R tipi hasırlar için çap ve aralık tablosu
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
                
                # R tipi hasırlar için
                'R106': (4.0, 15),
                'R131': (4.5, 15),
                'R158': (5.0, 15),
                'R188': (5.5, 15),
                'R221': (6.0, 15),
                'R257': (6.5, 15),
                'R295': (7.0, 15),
                'R317': (7.2, 15),
                'R335': (7.4, 15),
                'R377': (7.9, 15),
                'R443': (8.6, 15),
                'R513': (9.2, 15),
                'R524': (9.3, 15),
                'R589': (9.8, 15)
            }
            
            # Mesh kodunu temizle (Q257/257 -> Q257)
            clean_code = mesh_code.split('/')[0] if '/' in mesh_code else mesh_code
            
            if clean_code in mesh_properties:
                return mesh_properties[clean_code]
            else:
                print(f"Uyarı: {mesh_code} için özellikler bulunamadı!")
                return (0, 0)  # Varsayılan değerler
        
        except Exception as e:
            print(f"Hasır özellikleri alınırken hata: {str(e)}")
            return (0, 0)
