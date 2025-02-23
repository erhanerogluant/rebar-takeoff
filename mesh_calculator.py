from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class MeshData:
    type: str          # 'SLAB' or 'WALL'
    mesh_code: str     # Q257/257, R257, etc.
    width: float       # cm
    length: float      # cm
    count: int         # adet (2x gibi)
    area: float        # m2
    weight_per_m2: float  # kg/m2
    total_weight: float   # kg
    description: str

class MeshCalculator:
    def __init__(self):
        # Hasır donatı tipleri ve birim ağırlıkları (kg/m2)
        self.mesh_types = {
            'Q257/257': 5.14,  # kg/m2
            'R257': 2.57,
            'TR295': 2.95,
            'TR317': 3.17
        }
        
        self.pattern_handlers = {
            # Döşeme hasır pattern'leri
            r'(\d*[xX])?[QR](\d+)(?:/\d+)?': self._handle_slab_mesh,  # Q257/257, R257, 2xQ257/257
            r'TR(\d+)': self._handle_slab_mesh_tr,  # TR295, TR317
            
            # Perde hasır pattern'leri
            r'(\d+)[xX](\d+)': self._handle_wall_dimensions,  # 215x267
        }
        
        self.current_data = {}
        self.results: List[MeshData] = []

    def _handle_slab_mesh(self, match) -> dict:
        multiplier = match.group(1)
        count = int(multiplier.replace('x', '')) if multiplier else 1
        mesh_code = match.group(0).replace(multiplier if multiplier else '', '')
        
        print(f"Hasır donatı algılandı:")
        print(f"- Tip: {mesh_code}")
        print(f"- Adet: {count}")
        
        return {
            'type': 'SLAB',
            'mesh_code': mesh_code,
            'count': count
        }

    def _handle_slab_mesh_tr(self, match) -> dict:
        code = f"TR{match.group(1)}"
        
        print(f"TR Hasır donatı algılandı:")
        print(f"- Tip: {code}")
        
        return {
            'type': 'SLAB',
            'mesh_code': code,
            'count': 1
        }

    def _handle_wall_dimensions(self, match) -> dict:
        width = float(match.group(1))
        length = float(match.group(2))
        
        print(f"Perde boyutları algılandı:")
        print(f"- Genişlik: {width} cm")
        print(f"- Uzunluk: {length} cm")
        
        return {
            'width': width,
            'length': length
        }

    def calculate_area(self, width: float, length: float) -> float:
        """Alan hesapla (m2)"""
        return (width * length) / 10000  # cm2'den m2'ye çevir

    def calculate_weight(self, area: float, mesh_code: str) -> float:
        """Toplam ağırlığı hesapla (kg)"""
        weight_per_m2 = self.mesh_types.get(mesh_code, 0)
        return area * weight_per_m2

    def parse_text(self, text: str) -> dict:
        """Text'i parse et ve veri sözlüğü döndür"""
        print(f"Parse ediliyor: {text}")
        
        for pattern, handler in self.pattern_handlers.items():
            match = re.search(pattern, text)
            if match:
                print(f"Pattern eşleşti: {pattern}")
                result = handler(match)
                print(f"Handler sonucu: {result}")
                return result
                
        print(f"Hiçbir pattern eşleşmedi!")
        return {}

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
                    total_weight = self.calculate_weight(area * count, mesh_code)
                    
                    new_result = MeshData(
                        type='WALL',
                        mesh_code=mesh_code,
                        width=width,
                        length=length,
                        count=count,
                        area=area * count,
                        weight_per_m2=self.mesh_types[mesh_code],
                        total_weight=total_weight,
                        description=f"{count}x{mesh_code} ({width}x{length})"
                    )
                    
                    self.results.append(new_result)
                    print(f"\nPerde hasır hesabı tamamlandı:")
                    print(f"- Tip: {count}x{mesh_code}")
                    print(f"- Boyutlar: {width}x{length} cm")
                    print(f"- Alan: {area:.2f} m2")
                    print(f"- Toplam Alan: {area * count:.2f} m2")
                    print(f"- Birim Ağırlık: {self.mesh_types[mesh_code]:.2f} kg/m2")
                    print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False

    def process_text(self, text: str) -> bool:
        """Text'i işle ve başarılı olup olmadığını döndür"""
        print(f"\nİşlenen text: {text}")
        parsed_data = self.parse_text(text)
        if parsed_data:
            self.current_data.update(parsed_data)
            print(f"Güncel veri durumu: {self.current_data}")
            return True
        else:
            print("Text parse edilemedi!")
            return False

    def process_dimensions(self, width: float, length: float):
        """Boyutları işle ve sonucu kaydet"""
        if 'type' in self.current_data:
            area = self.calculate_area(width, length)
            total_weight = self.calculate_weight(area, self.current_data['mesh_code'])
            
            new_result = MeshData(
                type=self.current_data['type'],
                mesh_code=self.current_data['mesh_code'],
                width=width,
                length=length,
                count=self.current_data.get('count', 1),
                area=area,
                weight_per_m2=self.mesh_types[self.current_data['mesh_code']],
                total_weight=total_weight,
                description=f"{self.current_data.get('count', 1)}x{self.current_data['mesh_code']} ({width}x{length})"
            )
            
            self.results.append(new_result)
            print(f"\nHasır hesabı tamamlandı:")
            print(f"- Tip: {new_result.mesh_code}")
            print(f"- Boyutlar: {width}x{length} cm")
            print(f"- Alan: {area:.2f} m2")
            print(f"- Birim Ağırlık: {new_result.weight_per_m2:.2f} kg/m2")
            print(f"- Toplam Ağırlık: {total_weight:.2f} kg")

    def process_slab_mesh(self, mesh_text: str, width: float, length: float) -> bool:
        """Döşeme hasır hesabını yap"""
        try:
            # Hasır tipi işleme
            match = re.search(r'(\d*[xX])?([QR]\d+(?:/\d+)?|TR\d+)', mesh_text)
            if match:
                count = int(match.group(1).replace('x', '')) if match.group(1) else 1
                mesh_code = match.group(2)
                
                area = self.calculate_area(width, length)
                total_weight = self.calculate_weight(area * count, mesh_code)
                
                new_result = MeshData(
                    type='SLAB',
                    mesh_code=mesh_code,
                    width=width,
                    length=length,
                    count=count,
                    area=area * count,
                    weight_per_m2=self.mesh_types[mesh_code],
                    total_weight=total_weight,
                    description=f"{count}x{mesh_code} ({width}x{length})"
                )
                
                self.results.append(new_result)
                print(f"\nDöşeme hasır hesabı tamamlandı:")
                print(f"- Tip: {count}x{mesh_code}")
                print(f"- Boyutlar: {width}x{length} cm")
                print(f"- Alan: {area:.2f} m2")
                print(f"- Toplam Alan: {area * count:.2f} m2")
                print(f"- Birim Ağırlık: {self.mesh_types[mesh_code]:.2f} kg/m2")
                print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
                return True
                
            return False
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False 