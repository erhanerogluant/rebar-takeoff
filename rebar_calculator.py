import ezdxf
import re
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional
import logging
from datetime import datetime
import os

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

class RebarCalculator:
    def __init__(self):
        # Demir çapı - birim ağırlık tablosu (kg/mt)
        self.weight_table = {
            8: 0.395,
            10: 0.617,
            12: 0.888,
            14: 1.208,
            16: 1.578,
            18: 1.998,
            20: 2.466,
            22: 2.984
        }
        
        # Hasır donatı tipleri ve birim ağırlıkları (kg/m2)
        self.mesh_types = {
            # Q Tipi Hasırlar
            'Q106/106': 1.66,
            'Q131/131': 2.06,
            'Q158/158': 2.49,
            'Q188/188': 2.96,
            'Q221/221': 3.47,
            'Q257/257': 4.03,
            'Q257/188': 3.49,
            'Q295/295': 4.62,
            'Q295/257': 4.33,
            'Q295/221': 4.04,
            'Q295/188': 3.79,
            'Q295/158': 3.56,
            'Q317/317': 5.00,
            'Q317/295': 4.81,
            'Q317/257': 4.52,
            'Q317/221': 4.24,
            'Q317/188': 3.98,
            'Q335/335': 5.26,
            'Q335/317': 5.13,
            'Q335/295': 4.94,
            'Q335/257': 4.64,
            'Q335/221': 4.37,
            'Q335/188': 4.11,
            'Q377/377': 5.94,
            'Q377/335': 5.60,
            'Q377/317': 5.47,
            'Q377/295': 5.28,
            'Q377/257': 4.98,
            'Q377/221': 4.71,
            'Q377/188': 4.45,
            'Q424/424': 6.66,
            'Q424/377': 6.30,
            'Q424/335': 5.96,
            'Q424/317': 5.98,
            'Q424/295': 5.64,
            'Q424/257': 5.34,
            'Q424/221': 5.07,
            'Q443/443': 6.96,
            'Q443/377': 6.45,
            'Q443/335': 6.11,
            'Q443/317': 5.98,
            'Q443/295': 5.79,
            'Q443/257': 5.49,
            'Q443/221': 5.22,
            'Q473/473': 7.42,
            'Q503/503': 7.89,
            'Q513/513': 8.09,
            'Q513/257': 6.06,
            'Q524/524': 8.22,
            'Q524/443': 7.59,
            'Q524/424': 7.44,
            'Q524/377': 7.08,
            'Q524/335': 6.74,
            'Q524/317': 6.61,
            'Q524/295': 6.42,
            'Q524/257': 6.12,
            'Q589/589': 9.24,
            'Q589/503': 8.61,
            'Q589/378': 7.64,
            'Q589/335': 7.30,
            'Q589/317': 7.17,
            'Q589/295': 6.98,
            'Q634/634': 9.95,
            'Q636/636': 9.99,
            'Q636/424': 8.32,
            'Q709/424': 8.89,
            'Q754/754': 11.84,
            'Q785/785': 12.33,
            'Q785/295': 8.48,
            'Q785/257': 8.18,
            'Q950/950': 14.92,
            'Q1131/1131': 17.76,

            # R Tipi Hasırlar
            'R106': 1.33,
            'R131': 1.65,
            'R158': 1.86,
            'R188': 2.10,
            'R221': 2.36,
            'R257': 2.63,
            'R295': 2.93,
            'R317': 3.11,
            'R335': 3.25,
            'R377': 3.58,
            'R443': 4.22,
            'R513': 4.92,
            'R589': 5.66,

            # TR Tipi Hasırlar
            'TR131': 1.59,
            'TR158': 1.81,
            'TR188': 2.04,
            'TR221': 2.29,
            'TR257': 2.57,
            'TR295': 2.86,
            'TR317': 3.04,
            'TR335': 3.18,
            'TR377': 3.51,
            'TR443': 4.13,
            'TR513': 4.81,
            'TR524': 4.90,
            'TR589': 5.54
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
        
        # Loglama sistemi kurulumu
        self.setup_logging()

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

    def log_summary(self, category_type=None):
        """Özet raporu logla"""
        try:
            if not self.results:
                return
            
            summary = "\nÖZET RAPOR\n" + "="*50
            
            totals = self.calculate_totals()
            
            if category_type:
                if totals[category_type]:
                    summary += f"\n\n{category_type} HESABI ÖZETİ:"
                    summary += self.format_category_summary(category_type, totals[category_type])
            else:
                for cat_type, data in totals.items():
                    if data:
                        summary += f"\n\n{cat_type} HESABI ÖZETİ:"
                        summary += self.format_category_summary(cat_type, data)
            
            total_weight = sum(sum(item['weight'] for item in cat.values())
                             for cat in totals.values())
            
            summary += f"\n\nGENEL TOPLAM:"
            summary += f"\nToplam Ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)"
            
            self.logger.info(summary)
            
        except Exception as e:
            self.logger.error(f"Özet loglama hatası: {str(e)}")

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
                type='SLAB',
                diameter=0,  # Hasır için çap kullanılmıyor
                spacing=None,
                length=length,
                count=count,
                total_length=0,  # Hasır için boy yerine alan kullanılıyor
                weight_per_meter=weight_per_m2,  # kg/m2
                total_weight=total_weight,
                description=f"Döşeme Hasır {count}x{mesh_code} ({length}x{width})",
                mesh_code=mesh_code,
                area=area * count,
                width=width
            )
            
            self.results.append(new_result)
            print(f"\nDöşeme hasır hesabı tamamlandı:")
            print(f"- Tip: {count}x{mesh_code}")
            print(f"- Boyutlar: {length}x{width} cm")
            print(f"- Alan: {area:.2f} m2")
            print(f"- Toplam Alan: {area * count:.2f} m2")
            print(f"- Birim Ağırlık: {weight_per_m2:.2f} kg/m2")
            print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
            
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

    def show_summary(self, result_type=None):
        """Seçilen tip için özet rapor göster"""
        if not self.results:
            print("\nHenüz hesaplanmış sonuç yok!")
            return

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

        # Özet raporu göster
        if result_type:
            self._print_category_summary(result_type, totals[result_type])
        else:
            print("\nÖZET RAPOR")
            print("=" * 50)
            
            # Etriyeler
            if totals['STIRRUP']:
                print("\nETRİYELER:")
                print("-" * 30)
                self._print_category_summary('STIRRUP', totals['STIRRUP'])
            
            # Boy demirleri
            if totals['REBAR']:
                print("\nBOY DEMİRLERİ:")
                print("-" * 30)
                self._print_category_summary('REBAR', totals['REBAR'])
            
            # Ara bağlantılar
            if totals['CONNECTION']:
                print("\nARA BAĞLANTILAR:")
                print("-" * 30)
                self._print_category_summary('CONNECTION', totals['CONNECTION'])
            
            # Perde hasırları
            if totals['WALL']:
                print("\nPERDE HASIRLARI:")
                print("-" * 30)
                self._print_category_summary('WALL', totals['WALL'])
            
            # Döşeme hasırları
            if totals['SLAB']:
                print("\nDÖŞEME HASIRLARI:")
                print("-" * 30)
                self._print_category_summary('SLAB', totals['SLAB'])
            
            # Genel toplam
            total_weight = sum(sum(item['weight'] for item in category.values())
                             for category in totals.values())
            print("\nGENEL TOPLAM")
            print("=" * 30)
            print(f"Toplam Ağırlık: {total_weight:.2f} kg ({total_weight/1000:.3f} ton)")

    def _print_category_summary(self, category_type, data):
        """Kategori özetini yazdır"""
        total_weight = sum(item['weight'] for item in data.values())
        
        if category_type in ['WALL', 'SLAB']:
            total_area = sum(item['area'] for item in data.values())
            total_count = sum(item['count'] for item in data.values())
            
            for mesh_code, values in data.items():
                print(f"\n{mesh_code}:")
                print(f"- Toplam Alan: {values['area']:.2f} m²")
                print(f"- Toplam Adet: {values['count']} adet")
                print(f"- Toplam Ağırlık: {values['weight']:.2f} kg")
            
            print(f"\nKategori Toplamı:")
            print(f"- Toplam Alan: {total_area:.2f} m²")
            print(f"- Toplam Adet: {total_count} adet")
            print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
        else:
            total_length = sum(item['length'] for item in data.values())
            total_count = sum(item['count'] for item in data.values())
            
            for diameter, values in data.items():
                print(f"\n{diameter}:")
                print(f"- Toplam Boy: {values['length']/100:.2f} m")
                print(f"- Toplam Adet: {values['count']} adet")
                print(f"- Toplam Ağırlık: {values['weight']:.2f} kg")
            
            print(f"\nKategori Toplamı:")
            print(f"- Toplam Boy: {total_length/100:.2f} m")
            print(f"- Toplam Adet: {total_count} adet")
            print(f"- Toplam Ağırlık: {total_weight:.2f} kg")

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
