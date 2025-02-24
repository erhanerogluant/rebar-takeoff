import os
from datetime import datetime

class ReportManager:
    def __init__(self):
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.report_dir = os.path.join(os.getcwd(), f"metraj_raporlari_{self.current_date}")
        os.makedirs(self.report_dir, exist_ok=True)
        
    def write_report(self, results):
        """Metraj raporu oluştur"""
        try:
            # Klasörü oluştur
            if not os.path.exists(self.report_dir):
                os.makedirs(self.report_dir)
            
            report_path = os.path.join(self.report_dir, "metraj_raporu.txt")
            
            # Dosyayı yazma modunda aç
            with open(report_path, 'w', encoding='utf-8') as f:
                # Başlık
                f.write(f"{'='*70}\n")
                f.write(f"HASIR DONATISI METRAJ RAPORU\n")
                f.write(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write(f"{'='*70}\n\n")
                
                # Hasır gruplarını oluştur ve yaz
                mesh_groups = {}
                for result in results:
                    if result.mesh_code not in mesh_groups:
                        mesh_groups[result.mesh_code] = {
                            'items': [],
                            'total_area': 0,
                            'total_weight': 0,
                            'count': 0
                        }
                    group = mesh_groups[result.mesh_code]
                    group['items'].append(result)
                    group['total_area'] += result.area
                    group['total_weight'] += result.total_weight
                    group['count'] += result.count

                # Tablo başlığı
                f.write("1. HASIR TİPLERİNE GÖRE METRAJ\n")
                f.write(f"{'-'*70}\n")
                f.write("Hasır     Boyut        Adet    Alan      Birim Ağr.   Toplam Ağr.\n")
                f.write("Tipi      (cm)         (ad)    (m²)      (kg/m²)     (kg)\n")
                f.write(f"{'-'*70}\n")

                # Detayları yaz
                for mesh_code, group in mesh_groups.items():
                    for item in group['items']:
                        f.write(f"{mesh_code:<9} {item.width:>3}×{item.height:<6} {item.count:>4}    {item.area:>6.2f}    {item.weight_per_meter:>6.2f}     {item.total_weight:>7.2f}\n")
                    
                    if len(group['items']) > 1:
                        f.write(f"{'-'*70}\n")
                        f.write(f"{'ARA TOPLAM':<21} {group['count']:>4}    {group['total_area']:>6.2f}              {group['total_weight']:>7.2f}\n")
                        f.write(f"{'-'*70}\n\n")

                # Genel toplam
                total_area = sum(g['total_area'] for g in mesh_groups.values())
                total_weight = sum(g['total_weight'] for g in mesh_groups.values())
                total_count = sum(g['count'] for g in mesh_groups.values())

                f.write(f"\n2. GENEL TOPLAM\n")
                f.write(f"{'-'*70}\n")
                f.write(f"Toplam Hasır Adedi: {total_count:>6} adet\n")
                f.write(f"Toplam Alan: {total_area:>11.2f} m²\n")
                f.write(f"Toplam Ağırlık: {total_weight:>8.2f} kg ({total_weight/1000:.3f} ton)\n")
                f.write(f"{'-'*70}\n")

                # Alt bilgi
                f.write(f"\nNOTLAR:\n")
                f.write("1. Hasır donatı ağırlıkları teorik değerlerdir.\n")
                f.write("2. Bindirme payları dahil değildir.\n")
                f.write("3. Fire oranları dahil değildir.\n")
            
            return True
            
        except Exception as e:
            print(f"Rapor oluşturma hatası: {str(e)}")
            return False 