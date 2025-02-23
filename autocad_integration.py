import win32com.client
from rebar_calculator import RebarCalculator
import time
import msvcrt

class AutoCADIntegration:
    def __init__(self):
        try:
            self.acad = win32com.client.Dispatch("AutoCAD.Application")
            self.doc = self.acad.ActiveDocument
            self.util = self.doc.Utility  # Utility nesnesini başlangıçta al
            self.calculator = RebarCalculator()
            print("AutoCAD bağlantısı başarılı!")
        except Exception as e:
            print(f"AutoCAD başlatma hatası: {str(e)}")
            raise

    def reconnect_autocad(self):
        """AutoCAD bağlantısını yeniden kur"""
        try:
            # Mevcut bağlantıyı temizle
            self.acad = None
            self.doc = None
            self.util = None
            
            # 3 deneme hakkı
            for attempt in range(3):
                try:
                    self.acad = win32com.client.Dispatch("AutoCAD.Application")
                    self.doc = self.acad.ActiveDocument
                    self.util = self.doc.Utility
                    print("AutoCAD bağlantısı yenilendi!")
                    return True
                except Exception as e:
                    print(f"Bağlantı denemesi {attempt + 1} başarısız: {str(e)}")
                    time.sleep(1)  # 1 saniye bekle
            
            raise Exception("AutoCAD bağlantısı kurulamadı!")
            
        except Exception as e:
            print(f"Bağlantı hatası: {str(e)}")
            return False

    def select_entity(self, prompt: str):
        """AutoCAD'den nesne seç"""
        try:
            print(f"\n{prompt} (Çıkmak için 'Q' tuşuna basın)")
            print("Lütfen AutoCAD'de bir öğe seçin...")
            
            # Kullanıcı girişini kontrol et
            if msvcrt.kbhit():  # Tuşa basıldı mı?
                key = msvcrt.getch().decode().upper()
                if key == 'Q':
                    print("\nİşlem kullanıcı tarafından durduruldu.")
                    return None
            
            time.sleep(0.5)  # Kısa bir bekleme
            
            # Seçim işlemini gerçekleştir
            self.util.Prompt(f"\n{prompt}: ")
            entity = self.util.GetEntity()
            
            if entity and entity[0]:
                selected = entity[0]
                
                if selected.ObjectName in ['AcDbText', 'AcDbMText']:
                    text = selected.TextString
                    print(f"Seçilen text: {text}")
                    return text
                    
                elif selected.ObjectName in ['AcDbDimension', 'AcDbAlignedDimension', 'AcDbRotatedDimension']:
                    measurement = selected.Measurement
                    print(f"Seçilen ölçü: {measurement}")
                    return measurement
                    
                else:
                    print(f"Uyarı: Seçilen öğe tipi desteklenmiyor ({selected.ObjectName})")
            
            # ESC tuşuna basıldığında veya seçim iptal edildiğinde
            if not entity:
                return None
            
        except Exception as e:
            print(f"Seçim hatası: {str(e)}")
            # AutoCAD bağlantısını yenilemeyi dene
            if self.reconnect_autocad():
                return self.select_entity(prompt)  # Tekrar dene
            
        return None

    def process_stirrup_selection(self):
        """Etriye seçim işlemini yönet"""
        try:
            while True:
                # Etriye text seçimi
                text = self.select_entity("Etriye textini seçin (örn: ƒ10 Etr. l=246)")
                if not text:
                    break
                
                # Text içinde L= yoksa boy uzunluğu iste
                if not self.calculator.extract_length(text):
                    length_text = self.select_entity("Boy uzunluğunu seçin (örn: L=246)")
                    if not length_text:
                        break
                    text = text + " " + length_text  # Boy bilgisini texte ekle
                
                # Aralık text seçimi
                spacing_text = self.select_entity("Aralık textini seçin (örn: Etr.%%C10/8)")
                if not spacing_text:
                    break
                
                # Dimension seçimi
                dimension = self.select_entity("Dimension ölçüsünü seçin")
                if dimension is None:
                    break
                
                # Hesaplama ve sonuç ekleme
                success = False
                if self.calculator.process_text(text):
                    if self.calculator.process_text(spacing_text):
                        if self.calculator.process_dimension(float(dimension)):
                            success = True
                            print("\nEtriye hesabı başarıyla tamamlandı!")
                            print("Başka etriye seçmek için devam edin veya çıkmak için Q tuşuna basın")
                
                if not success:
                    retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                    if retry.upper() != 'E':
                        break
            
            # İşlem bittiğinde özeti göster
            if self.calculator.results:
                print("\nETRİYE HESABI ÖZETİ")
                self.calculator.show_summary('STIRRUP')
                self.calculator.log_summary('STIRRUP')
            return True

        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            print("İşlem iptal edildi.")
            return False

    def process_rebar_selection(self):
        """Boy demiri seçim işlemini yönet"""
        try:
            while True:
                # Boy demiri text seçimi
                text = self.select_entity("Boy demiri textini seçin (örn: 2X13∅20 L=397) veya çıkmak için boş seçim yapın")
                if not text:
                    break  # Boş seçim yapıldıysa çık
                
                # Text içinde L= yoksa boy uzunluğu iste
                if not self.calculator.extract_length(text):
                    length_text = self.select_entity("Boy uzunluğunu seçin (örn: L=397)")
                    if not length_text:
                        break  # Boş seçim yapıldıysa çık
                    text = text + " " + length_text  # Boy bilgisini texte ekle
                
                if not self.calculator.process_text(text):
                    retry = input("\nGeçersiz boy demiri texti. Tekrar denemek ister misiniz? (E/H): ")
                    if retry.upper() != 'E':
                        break
            
            # İşlem bittiğinde özeti göster
            print("\nBOY DEMİRİ HESABI ÖZETİ")
            self.calculator.show_summary('REBAR')
            self.calculator.log_summary('REBAR')
            return True

        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            print("İşlem iptal edildi.")
            return False

    def process_mesh_selection(self, mesh_type='SLAB'):
        """Hasır donatı seçim işlemini yönet"""
        try:
            while True:  # Ana döngü - birden fazla hasır seçimi için
                if mesh_type == 'WALL':
                    # Perde hasır seçimi
                    while True:
                        mesh_text = self.select_entity("Perde hasır tipini seçin (örn: 2xQ257/257)")
                        if not mesh_text:
                            break  # Seçim yapılmadıysa ana döngüye dön
                        
                        dim_text = self.select_entity("Boyutları seçin (örn: 215x267)")
                        if not dim_text:
                            break
                        
                        if self.calculator.process_wall_mesh(mesh_text, dim_text):
                            print("\nBaşka perde hasırı seçmek için devam edin veya çıkmak için boş seçim yapın")
                        else:
                            retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                            if retry.upper() != 'E':
                                break
                else:
                    # Döşeme hasır seçimi
                    while True:
                        mesh_text = self.select_entity("Döşeme hasır tipini seçin (örn: Q257/257 450/215)")
                        if not mesh_text:
                            break  # Seçim yapılmadıysa ana döngüye dön
                        
                        if self.calculator.process_slab_mesh(mesh_text):
                            print("\nBaşka döşeme hasırı seçmek için devam edin veya çıkmak için boş seçim yapın")
                        else:
                            retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                            if retry.upper() != 'E':
                                break
                
                # Devam etmek istiyor mu?
                if not mesh_text:  # Boş seçim yapıldıysa
                    retry = input("\nHasır hesabına devam etmek ister misiniz? (E/H): ")
                    if retry.upper() != 'E':
                        break
            
            # İşlem bittiğinde özeti göster
            print("\nHASIR HESABI ÖZETİ")
            self.calculator.show_summary(mesh_type)
            self.calculator.log_summary(mesh_type)
            return True

        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            print("İşlem iptal edildi.")
            return False

    def process_connection_selection(self):
        """Ara bağlantı demiri seçim işlemini yönet"""
        try:
            while True:
                # Ara bağlantı demiri text seçimi
                text = self.select_entity("Ara bağlantı textini seçin (örn: 2X∅12/15 L=185 veya ∅8/20)")
                if not text:
                    break
                
                # Text içinde L= yoksa boy uzunluğu iste
                if not self.calculator.extract_length(text):
                    length_text = self.select_entity("Boy uzunluğunu seçin (örn: L=185)")
                    if not length_text:
                        break
                else:
                    length_text = None  # Text içinde L= varsa None gönder
                
                # Dimension seçimi
                dimension = self.select_entity("Dimension ölçüsünü seçin")
                if dimension is None:
                    break
                
                if self.calculator.process_connection_rebar(text, length_text, float(dimension)):
                    print("\nBaşka ara bağlantı seçmek için devam edin veya çıkmak için boş seçim yapın")
                else:
                    retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                    if retry.upper() != 'E':
                        break
            
            # İşlem bittiğinde özeti göster
            print("\nARA BAĞLANTI HESABI ÖZETİ")
            self.calculator.show_summary('CONNECTION')
            self.calculator.log_summary('CONNECTION')
            return True

        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            print("İşlem iptal edildi.")
            return False