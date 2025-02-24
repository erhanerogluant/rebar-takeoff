import win32com.client
from rebar_calculator import RebarCalculator
import time
import msvcrt
import re
import logging
import os
from datetime import datetime

class AutoCADIntegration:
    # Hasır tipi ağırlık tablosu
    MESH_WEIGHTS = {
        # Q tipi hasırlar
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
        'Q443/443': 6.96,
        # ... diğer Q tipi hasırlar eklenebilir
        
        # R tipi hasırlar
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
        
        # TR tipi hasırlar
        'TR131': 17.09,
        'TR158': 19.43,
        'TR188': 21.91,
        'TR221': 24.61,
        'TR257': 27.59,
        'TR295': 30.78,
        'TR317': 32.70,
        'TR335': 34.19,
        'TR377': 37.73,
        'TR443': 44.44,
        'TR513': 51.73,
        'TR524': 52.66,
        'TR589': 59.57
    }

    def __init__(self):
        try:
            self.acad = win32com.client.Dispatch("AutoCAD.Application")
            self.doc = self.acad.ActiveDocument
            self.util = self.doc.Utility
            self.calculator = RebarCalculator()
            print("AutoCAD bağlantısı başarılı!")
        except Exception as e:
            print(f"AutoCAD başlatma hatası: {str(e)}")
            raise

    def get_mesh_weight(self, mesh_type):
        """
        Verilen hasır tipinin birim ağırlığını döndürür
        Args:
            mesh_type (str): Hasır tipi (örn: 'Q257/257', 'R257', 'TR257')
        Returns:
            float: Birim ağırlık (kg/m²)
        """
        try:
            # Hasır tipini normalize et (boşlukları kaldır)
            mesh_type = mesh_type.strip().replace(' ', '')
            
            # Ağırlığı bul
            weight = self.MESH_WEIGHTS.get(mesh_type)
            if weight is None:
                print(f"Uyarı: {mesh_type} için ağırlık bilgisi bulunamadı!")
                return 0.0
                
            return weight
            
        except Exception as e:
            print(f"Hasır ağırlığı bulma hatası: {str(e)}")
            return 0.0

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

    def select_multiple_entities(self, prompt_message):
        """Çoklu seçim yap ve seçilen textleri kırmızı yap"""
        try:
            print(f"\n{prompt_message} (Seçimi tamamladıktan sonra ENTER'a basın)")
            print("Lütfen AutoCAD'de seçim yapın...")
            
            # Varsa önceki seçim setini temizle
            try:
                old_selection = self.doc.SelectionSets.Item("TempSel")
                old_selection.Delete()
                print("Önceki seçim seti temizlendi")
            except:
                print("Önceki seçim seti bulunamadı")
            
            print("Yeni seçim seti oluşturuluyor...")
            selection = self.doc.SelectionSets.Add("TempSel")
            
            # AutoCAD'de seçim komutunu başlat
            print("Seçim komutu başlatılıyor...")
            self.doc.Utility.Prompt("\nSeçim yapın ve ENTER'a basın: ")
            
            # Seçim yap
            print("SelectOnScreen bekleniyor...")
            selection.SelectOnScreen()
            print(f"Seçim tamamlandı. Seçilen öğe sayısı: {selection.Count}")
            
            selected_texts = []
            
            # Seçilen her öğe için
            print("\nSeçilen öğeler kontrol ediliyor...")
            for i, item in enumerate(selection):
                try:
                    print(f"Öğe {i+1} kontrol ediliyor: {item.ObjectName}")
                    
                    # Text nesnesini doğrudan kullan
                    if item.ObjectName == "AcDbText":
                        try:
                            # COM nesnesini al
                            text_obj = self.doc.HandleToObject(item.Handle)
                            text_value = text_obj.TextString.strip()
                            print(f"Text bulundu: {text_value}")
                            
                            # Rengi kırmızı yap (AutoCAD renk kodu: 1 = Kırmızı)
                            try:
                                text_obj.TrueColor = self.doc.Application.GetInterfaceObject("AutoCAD.AcCmColor.24")
                                text_obj.TrueColor.SetRGB(255, 0, 0)  # Kırmızı
                            except:
                                try:
                                    text_obj.Color = 1  # AutoCAD kırmızı renk kodu
                                except:
                                    try:
                                        text_obj.EntityColor = 1
                                    except Exception as color_error:
                                        print(f"Renk değiştirme hatası (önemli değil): {str(color_error)}")
                        
                            # Text değerini listeye ekle
                            selected_texts.append(text_value)
                            
                        except Exception as text_error:
                            print(f"Text okuma hatası: {str(text_error)}")
                            continue
                        
                except Exception as e:
                    print(f"Öğe işlenirken hata: {str(e)}")
                    continue
            
            print("\nSeçim seti temizleniyor...")
            selection.Delete()
            
            if selected_texts:
                print(f"\nSeçilen text sayısı: {len(selected_texts)}")
                print("Seçilen textler:")
                for text in selected_texts:
                    print(f"- {text}")
                
                # Hasır tipine göre grupla ve hesapla
                mesh_texts = []
                for text in selected_texts:
                    if 'Q' in text or 'R' in text:  # Hasır text'lerini bul
                        parts = text.split()  # Boşluğa göre ayır
                        if len(parts) >= 2:  # En az 2 parça olmalı
                            mesh_type = parts[0]  # Q257/257 veya R257
                            # Boyutları bul (son parçada olmalı)
                            for part in parts:
                                if '/' in part and all(c.isdigit() or c == '/' for c in part):
                                    dimensions = part
                                    mesh_texts.append((mesh_type, dimensions))
                                    break
                
                print("\nHasır hesaplamaları başlıyor...")
                for mesh_type, dimensions in mesh_texts:
                    try:
                        width, height = map(float, dimensions.split('/'))
                        print(f"\nHasır tipi: {mesh_type}")
                        print(f"Boyutlar: {width}x{height} cm")
                        
                        # Hasır hesaplama fonksiyonunu çağır
                        self.calculator.calculate_mesh(mesh_type, width, height)
                    except Exception as calc_error:
                        print(f"Hasır hesaplama hatası: {str(calc_error)}")
                
                # AutoCAD'i yenile
                print("\nAutoCAD güncelleniyor...")
                self.doc.Application.Update()
                
                print("İşlem başarıyla tamamlandı!")
                return selected_texts
            
            else:
                print("Hiç text seçilemedi!")
                return None
            
        except Exception as e:
            print(f"Seçim hatası: {str(e)}")
            print("Hata detayları:")
            import traceback
            traceback.print_exc()
            return None

    def process_stirrup_selection(self):
        """Etriye seçim işlemini yönet"""
        try:
            while True:
                # 1. İlk seçim - Etriye bilgileri
                etriye_text = self.select_entity("Etriye textini seçin (örn: ƒ10 Etr. l=200)")
                if not etriye_text:
                    break

                # Çap ve boy bilgilerini çıkar
                diameter_match = re.search(r'[ƒØ∅](\d+)|%%C(\d+)', etriye_text)
                length_match = re.search(r'[Ll]\s*=\s*(\d+)', etriye_text)
                
                if not (diameter_match and length_match):
                    print("Geçersiz etriye formatı!")
                    continue

                diameter = float(diameter_match.group(1) or diameter_match.group(2))
                length = float(length_match.group(1))

                # 2. İkinci seçim - Aralık bilgisi
                spacing_text = self.select_entity("Aralık textini seçin (örn: Etr.%%C10/8)")
                if not spacing_text:
                    break

                spacing_match = re.search(r'/(\d+)', spacing_text)
                if not spacing_match:
                    print("Geçersiz aralık formatı!")
                    continue

                spacing = float(spacing_match.group(1))

                # 3. Üçüncü seçim - Dimension
                dimension = self.select_entity("Dimension ölçüsünü seçin")
                if dimension is None:
                    break

                dimension = float(dimension)

                # Bilgileri göster
                print("\nSeçilen Bilgiler:")
                print(f"- Çap: Ø{diameter}")
                print(f"- Boy: {length} cm")
                print(f"- Aralık: {spacing} cm")
                print(f"- Kolon boyu: {dimension} cm")

                # Hesaplamaları yap
                print("\nHESAPLAMA SONUÇLARI:")
                print("--------------------")

                # 1. Etriye adedi hesabı
                count = int((dimension / spacing) + 1)
                print(f"1. Etriye adedi: {count} adet")
                print(f"   {dimension} cm / {spacing} cm + 1 = {count} adet")

                # 2. Toplam boy hesabı
                total_length = length * count
                print(f"2. Toplam boy: {total_length} cm = {total_length/100:.2f} m")
                print(f"   {length} cm × {count} adet = {total_length} cm")

                # 3. Ağırlık hesabı
                weight_per_meter = self.calculator.weight_table.get(diameter, 0)
                total_weight = (total_length / 100) * weight_per_meter
                print(f"3. Toplam ağırlık: {total_weight:.2f} kg")
                print(f"   {total_length/100:.2f} m × {weight_per_meter:.3f} kg/m = {total_weight:.2f} kg")

                # Sonucu kaydet
                result = RebarData(
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
                
                self.calculator.results.append(result)
                print("\nHesaplama başarıyla kaydedildi!")

                # Devam etmek istiyor mu?
                retry = input("\nBaşka etriye hesaplamak ister misiniz? (E/H): ")
                if retry.upper() != 'E':
                    break

            return True

        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
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
            while True:
                if mesh_type == 'WALL':
                    # Perde hasır seçimi
                    while True:
                        mesh_text = self.select_entity("Perde hasır tipini seçin (örn: 2xQ257/257)")
                        if not mesh_text:
                            break  # Seçim yapılmadıysa ana döngüye dön
                        
                        # TR prefix'ini kaldır
                        mesh_text = mesh_text.replace('TR', 'R')
                        
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
                    while True:
                        mesh_text = self.select_entity("Döşeme hasır tipini seçin")
                        if not mesh_text:
                            break
                        
                        mesh_text = mesh_text.replace('TR', 'R')
                        
                        if self.calculator.process_slab_mesh(mesh_text):
                            print("\nBaşka hasır seçmek için devam edin veya çıkmak için ENTER'a basın")
                        else:
                            retry = input("\nGeçersiz format. Tekrar denemek ister misiniz? (E/H): ")
                            if retry.upper() != 'E':
                                break
                
                if not mesh_text:
                    retry = input("\nHasır hesabına devam etmek ister misiniz? (E/H): ")
                    if retry.upper() != 'E':
                        print("\nHesaplama tamamlandı...")
                        
                        # Sadece bir kez özet göster ve rapor oluştur
                        self.calculator.show_summary('SLAB')
                        if self.calculator.report_manager.write_report(self.calculator.results):
                            print("Metraj raporu oluşturuldu.")
                        return True
        
            return True

        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
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

    def process_text(self, text):
        """Text'i işle ve sonucu hesapla"""
        try:
            print(f"İşlenen text: {text}")
            
            # Eğer mevcut veriler yoksa yeni oluştur
            if not hasattr(self, 'current_data'):
                self.current_data = {'type': 'STIRRUP'}
            
            # Etriye formatı kontrolü
            if "Etr." in text:
                # Çap bilgisini al (ƒ10 veya %%C10 formatı için)
                diameter_match = re.search(r'[ƒØ∅](\d+)|%%C(\d+)', text)
                if diameter_match:
                    diameter = float(diameter_match.group(1) or diameter_match.group(2))
                    print(f"Çap: Ø{diameter}")
                    self.current_data['diameter'] = diameter
                
                # Boy bilgisini al (L=200 formatı için)
                length_match = re.search(r'[Ll]\s*=\s*(\d+)', text)
                if length_match:
                    length = float(length_match.group(1))
                    print(f"Boy: {length} cm")
                    self.current_data['length'] = length
                
                # Aralık bilgisini al (/8 formatı için)
                spacing_match = re.search(r'/(\d+)', text)
                if spacing_match:
                    spacing = float(spacing_match.group(1))
                    print(f"Aralık: {spacing} cm")
                    self.current_data['spacing'] = spacing
                
                print(f"Etriye bilgileri güncellendi: {self.current_data}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Text işleme hatası: {str(e)}")
            return False

    def process_dimension(self, dimension: float):
        """Dimension değerini kullanarak hesaplama yap"""
        try:
            if hasattr(self, 'current_data') and self.current_data.get('type') == 'STIRRUP':
                data = self.current_data
                if all(key in data for key in ['diameter', 'length', 'spacing']):
                    # Etriye adedi hesabı
                    count = int((dimension / data['spacing']) + 1)
                    
                    # Toplam boy hesabı
                    total_length = data['length'] * count
                    
                    # Ağırlık hesabı
                    weight_per_meter = self.calculator.weight_table.get(data['diameter'], 0)
                    total_weight = (total_length / 100) * weight_per_meter
                    
                    # Sonucu oluştur
                    result = RebarData(
                        type='STIRRUP',
                        diameter=data['diameter'],
                        spacing=data['spacing'],
                        length=data['length'],
                        count=count,
                        total_length=total_length,
                        weight_per_meter=weight_per_meter,
                        total_weight=total_weight,
                        description=f"Etriye Ø{data['diameter']}/{data['spacing']}"
                    )
                    
                    # Sonucu kaydet
                    self.calculator.results.append(result)
                    
                    print(f"\nEtriye hesabı tamamlandı:")
                    print(f"- Çap: Ø{data['diameter']}")
                    print(f"- Boy: {data['length']} cm")
                    print(f"- Aralık: {data['spacing']} cm")
                    print(f"- Etriye adedi: {count} adet")
                    print(f"- Toplam Boy: {total_length/100:.2f} m")
                    print(f"- Birim Ağırlık: {weight_per_meter:.3f} kg/mt")
                    print(f"- Toplam Ağırlık: {total_weight:.2f} kg")
                    
                    # İşlem tamamlandıktan sonra current_data'yı temizle
                    self.current_data = {}
                    return True
                else:
                    print("Eksik bilgi var:", data)
                    return False
            
            return False
            
        except Exception as e:
            print(f"Hesaplama hatası: {str(e)}")
            return False

    def select_texts(self):
        """
        AutoCAD'deki text objelerini kullanıcının seçmesini sağlar
        Returns:
            list: Seçilen text objelerinin listesi
        """
        try:
            selected_texts = self.select_multiple_entities("Text objelerini seçin")
            if selected_texts:
                return selected_texts
            return []
            
        except Exception as e:
            logging.error(f"Text seçme işlemi sırasında hata oluştu: {str(e)}")
            raise Exception(f"Text seçme işlemi başarısız: {str(e)}")