from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class ReportItem:
    """Rapor içindeki bir öğeyi temsil eder (örn. bir hasır veya etriye)"""
    description: str
    diameter: float
    weight: float
    count: int = 0
    length: float = 0
    spacing: float = 0

@dataclass
class Report:
    """Bir rapor dosyasını temsil eder"""
    type: str  # STIRRUP, MESH_WALL, MESH_SLAB, CONNECTION, REBAR, FOUNDATION
    mahal: str
    total_weight: float
    items: List[ReportItem]
    file_path: str
    date: Optional[datetime] = None
    
@dataclass
class MahalMultiplier:
    """Mahal çarpanını temsil eder"""
    mahal: str
    similar_mahals: List[str]
    multiplier: int

@dataclass
class SummaryResult:
    """Özet sonuçları temsil eder"""
    by_type: dict  # Tipe göre toplam ağırlıklar
    by_mahal: dict  # Mahale göre toplam ağırlıklar
    by_diameter: dict  # Çapa göre toplam ağırlıklar
    total_weight: float  # Genel toplam ağırlık 