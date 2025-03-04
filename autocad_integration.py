import win32com.client
from rebar_calculator import RebarCalculator, RebarData
import time
import msvcrt
import re
import logging
import os
from datetime import datetime
import numpy as np

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
            # Önce AutoCAD'in açık olup olmadığını kontrol et
            try:
                self.acad = win32com.client.GetActiveObject("AutoCAD.Application")
                print("Mevcut AutoCAD oturumuna bağlandı.")
            except:
                # AutoCAD açık değilse yeni bir oturum başlat
                print("Mevcut AutoCAD oturumu bulunamadı. Yeni oturum başlatılıyor...")
                self.acad = win32com.client.Dispatch("AutoCAD.Application")
                self.acad.Visible = True
                print("Yeni AutoCAD oturumu başlatıldı.")
            
            # AutoCAD'in hazır olmasını bekle
            time.sleep(1)
            
            # Aktif dokümanı al
            try:
                self.doc = self.acad.ActiveDocument
            except:
                # Aktif doküman yoksa yeni bir doküman aç
                print("Aktif doküman bulunamadı. Yeni doküman açılıyor...")
                self.acad.Documents.Add()
                self.doc = self.acad.ActiveDocument
            
            # Utility nesnesini al
            self.util = self.doc.Utility
            
            # Hesaplayıcıyı başlat
            self.calculator = RebarCalculator()
            
            print("AutoCAD bağlantısı başarılı!")
        except Exception as e:
            print(f"AutoCAD başlatma hatası: {str(e)}")
            import traceback
            print(traceback.format_exc())
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
        """Kullanıcıdan birden fazla öğe seçmesini iste ve seçilen öğelerin listesini döndür"""
        try:
            print(f"\n{prompt_message} (Çıkmak için 'Q' tuşuna basın)")
            print("Lütfen AutoCAD'de öğeleri seçin...")
            
            # Önce mevcut seçim setini temizle
            try:
                # Eğer varsa, mevcut seçim setini sil
                old_selection = self.doc.SelectionSets.Item("TempSelection")
                old_selection.Delete()
            except:
                # Seçim seti yoksa hata yok
                pass
            
            # Seçim seti oluştur
            selection = self.doc.SelectionSets.Add("TempSelection")
            
            # Kullanıcıdan seçim yapmasını iste
            try:
                selection.SelectOnScreen()
            except:
                print("Seçim iptal edildi!")
                selection.Delete()
                return []
            
            # Seçilen öğeleri işle
            selected_items = []
            
            for i in range(selection.Count):
                try:
                    obj = selection.Item(i)
                    
                    # Öğe tipini kontrol et
                    object_name = obj.ObjectName
                    print(f"Seçilen öğe tipi: {object_name}")
                    
                    # Metin türleri için
                    if object_name == "AcDbText":
                        try:
                            # Önce Text olarak dene
                            text_obj = self.doc.HandleToObject(obj.Handle)
                            text_value = text_obj.TextString.strip()
                            selected_items.append(text_value)
                            print(f"Seçilen text: {text_value}")
                        except:
                            print("Text değeri okunamadı, alternatif yöntem deneniyor...")
                            try:
                                # Alternatif yöntem
                                text_value = obj.TextString.strip()
                                selected_items.append(text_value)
                                print(f"Seçilen text (alternatif): {text_value}")
                            except:
                                print("Text değeri okunamadı!")
                    elif object_name == "AcDbMText":
                        try:
                            # Önce MText olarak dene
                            mtext_obj = self.doc.HandleToObject(obj.Handle)
                            text_value = mtext_obj.TextString.strip()
                            selected_items.append(text_value)
                            print(f"Seçilen mtext: {text_value}")
                        except:
                            print("MText değeri okunamadı, alternatif yöntem deneniyor...")
                            try:
                                # Alternatif yöntem
                                text_value = obj.TextString.strip()
                                selected_items.append(text_value)
                                print(f"Seçilen mtext (alternatif): {text_value}")
                            except:
                                print("MText değeri okunamadı!")
                    # Dimension için
                    elif object_name == "AcDbDimension" or "Dimension" in object_name:
                        try:
                            dim_value = str(obj.Measurement)
                            selected_items.append(dim_value)
                            print(f"Seçilen dimension: {dim_value}")
                        except:
                            print(f"Dimension değeri okunamadı: {object_name}")
                    # Diğer metin benzeri öğeler için
                    elif hasattr(obj, "TextString"):
                        try:
                            text_value = obj.TextString.strip()
                            selected_items.append(text_value)
                            print(f"Seçilen diğer metin: {text_value}")
                        except:
                            print("Diğer metin değeri okunamadı!")
                    else:
                        # Diğer öğeler için (atla)
                        print(f"Uyarı: Desteklenmeyen öğe tipi seçildi: {object_name}")
                        
                        # Alternatif yöntem - manuel giriş
                        print("Metin değerini manuel olarak girmek ister misiniz? (E/H)")
                        reply = input()
                        if reply.upper() == 'E':
                            text_value = input("Metin değerini girin: ")
                            if text_value:
                                selected_items.append(text_value)
                                print(f"Manuel girilen metin: {text_value}")
                except Exception as e:
                    print(f"Öğe işleme hatası: {str(e)}")
                    continue
            
            # Seçim setini temizle
            selection.Delete()
            
            # Eğer hiç geçerli öğe seçilmediyse, kullanıcıya bilgi ver
            if not selected_items:
                print("Uyarı: Hiç geçerli metin öğesi seçilmedi!")
                print("Lütfen sadece metin (Text veya MText) öğeleri seçin.")
                
                # Kullanıcıya manuel giriş seçeneği sun
                reply = input("Metin değerini manuel girmek ister misiniz? (E/H): ")
                if reply.upper() == 'E':
                    text_value = input("Metin değerini girin: ")
                    if text_value:
                        selected_items.append(text_value)
                        print(f"Manuel girilen metin: {text_value}")
                else:
                    # Kullanıcıya yeniden seçim yapma şansı ver
                    reply = input("Yeniden seçim yapmak ister misiniz? (E/H): ")
                    if reply.upper() == 'E':
                        return self.select_multiple_entities(prompt_message)
        
            return selected_items
            
        except Exception as e:
            print(f"Seçim hatası: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # Hata durumunda da seçim setini temizlemeye çalış
            try:
                selection = self.doc.SelectionSets.Item("TempSelection")
                selection.Delete()
            except:
                pass
            
            return []

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

    def select_multiple_texts(self, prompt_message="Textleri seçin"):
        """Kullanıcıdan birden fazla text seçmesini iste"""
        try:
            print(f"\n{prompt_message} (Çıkmak için 'Q' tuşuna basın)")
            print("Lütfen AutoCAD'de birden fazla öğe seçin...")
            
            # Seçim işlemini başlat
            self.doc.Utility.Prompt(f"\n{prompt_message}. Seçimi tamamlamak için Enter'a basın.\n")
            
            # Önce varsa eski seçim setini temizle
            try:
                old_ss = self.doc.SelectionSets.Item("TempSS")
                old_ss.Delete()
            except:
                pass
            
            selection_set = self.doc.SelectionSets.Add("TempSS")
            
            try:
                # Filtre olmadan seçim yap
                selection_set.SelectOnScreen()
                
                # Seçilen nesneleri kontrol et
                if selection_set.Count == 0:
                    print("Hiçbir nesne seçilmedi.")
                    return []
                
                print(f"Toplam {selection_set.Count} nesne seçildi, text nesneleri filtreleniyor...")
                
                # Seçilen textleri al
                selected_texts = []
                for i in range(selection_set.Count):
                    try:
                        # Nesneyi al
                        obj = selection_set.Item(i)
                        
                        # Nesne tipini kontrol et
                        obj_type = obj.EntityName if hasattr(obj, 'EntityName') else obj.ObjectName
                        print(f"Nesne {i+1}: Tip = {obj_type}")
                        
                        # Doğrudan Text özelliğini almayı dene
                        try:
                            if hasattr(obj, 'TextString'):
                                text_value = obj.TextString
                                print(f"  - TextString ile içerik: {text_value}")
                                selected_texts.append(text_value)
                                continue
                            
                            if hasattr(obj, 'Text'):
                                text_value = obj.Text
                                print(f"  - Text ile içerik: {text_value}")
                                selected_texts.append(text_value)
                                continue
                            
                            # AutoCAD 2021 için özel yöntem
                            # Text nesnesini farklı şekilde almayı dene
                            text_value = None
                            
                            # Text nesnesi için
                            if "Text" in obj_type:
                                # Koordinatları al
                                try:
                                    # Utility ile text içeriğini al
                                    point = obj.InsertionPoint
                                    text_value = self.doc.Utility.GetEntity("", point)[0].TextString
                                    print(f"  - Utility ile içerik: {text_value}")
                                    selected_texts.append(text_value)
                                    continue
                                except:
                                    pass
                                
                                # Alternatif yöntem
                                try:
                                    # Handle ile text içeriğini al
                                    handle = obj.Handle
                                    text_obj = self.doc.HandleToObject(handle)
                                    if hasattr(text_obj, 'TextString'):
                                        text_value = text_obj.TextString
                                        print(f"  - Handle ile içerik: {text_value}")
                                        selected_texts.append(text_value)
                                        continue
                                except:
                                    pass
                                
                            print(f"  - Text içeriği alınamadı")
                            
                        except Exception as text_err:
                            print(f"  - Text değeri alınırken hata: {str(text_err)}")
                            
                    except Exception as e:
                        print(f"Nesne {i+1} işlenirken hata: {str(e)}")
                        continue
                
                print(f"{len(selected_texts)} adet text seçildi.")
                return selected_texts
                
            finally:
                # Seçim setini temizle
                selection_set.Delete()
                
        except Exception as e:
            print(f"Text seçim hatası: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def process_foundation_rebar_selection(self):
        """Temel demiri seçim işlemini yönet"""
        logging.info("Temel demiri seçim işlemi başlatıldı")
        
        try:
            # İlk dimension seçimi
            first_dimension = None
            
            while True:
                # 1. Temel demiri text seçimi
                foundation_text = self.select_entity("Temel demiri textini seçin (örn: ƒ8/20 L= 685 ALT) veya çıkmak için boş seçim yapın")
                if not foundation_text:
                    logging.info("Temel demiri seçimi tamamlandı")
                    break
                
                logging.info(f"Seçilen text: {foundation_text}")
                
                # Çap, aralık ve boy bilgilerini çıkar
                # ƒ8/20 L= 685 ALT formatını işle
                pattern = r'[ƒØ∅](\d+)/(\d+)\s*[Ll]\s*=\s*(\d+)\s*(ALT|ÜST|alt|üst|Üst|Alt)?'
                match = re.search(pattern, foundation_text)
                
                if not match:
                    logging.warning("Temel demiri text'i işlenemedi")
                    continue
                
                diameter = float(match.group(1))
                spacing = float(match.group(2))
                length = float(match.group(3))
                position = match.group(4) if match.group(4) else "ALT"  # Varsayılan olarak ALT
                
                logging.info(f"Temel Demiri Bilgileri:")
                logging.info(f"- Çap: Ø{diameter}")
                logging.info(f"- Aralık: {spacing} cm")
                logging.info(f"- Boy: {length} cm")
                logging.info(f"- Pozisyon: {position}")
                
                # İlk dimension değerini sakla
                if first_dimension is None:
                    # 2. Dimension seçimi (sadece ilk seferde)
                    dimension = self.select_entity("Temel genişliğini seçin (dimension)")
                    if dimension is None:
                        logging.warning("Dimension seçimi iptal edildi")
                        break
                    
                    try:
                        first_dimension = float(dimension)
                        logging.info(f"- Temel genişliği: {first_dimension} cm")
                    except ValueError:
                        logging.error("Geçersiz dimension değeri")
                        break
                
                # Sonraki seçimlerde ilk dimension değerini kullan
                width = first_dimension
                logging.info(f"- Temel genişliği (kaydedilmiş): {width} cm")
                
                # Hesaplamaları yap
                success = self.calculator.process_foundation_rebar(diameter, spacing, length, width, position)
                
                if success:
                    logging.info("Temel demiri hesabı başarıyla tamamlandı")
                else:
                    logging.warning("Temel demiri hesabı başarısız oldu")
                
                # Kullanıcıya devam etmek isteyip istemediğini sor
                print("\nBaşka temel demiri seçmek için devam edin veya çıkmak için boş seçim yapın")
                
            # İşlem bittiğinde özeti göster
            print("\nTEMEL DEMİRİ HESABI ÖZETİ")
            self.calculator.show_summary('FOUNDATION')
            self.calculator.log_summary('FOUNDATION')
            return True
                
        except Exception as e:
            logging.error(f"Temel demiri seçim hatası: {str(e)}")
            return False

    def select_multiple_foundation_rebars(self):
        """Çoklu temel demiri seçimi yap"""
        try:
            print("\nÇoklu temel demiri seçimi başlatıldı (Seçimi tamamladıktan sonra ENTER'a basın)")
            print("Lütfen AutoCAD'de temel demiri textlerini seçin...")
            
            # Varsa önceki seçim setini temizle
            try:
                old_selection = self.doc.SelectionSets.Item("TempFoundationSel")
                old_selection.Delete()
                print("Önceki seçim seti temizlendi")
            except:
                print("Önceki seçim seti bulunamadı")
            
            print("Yeni seçim seti oluşturuluyor...")
            selection = self.doc.SelectionSets.Add("TempFoundationSel")
            
            # AutoCAD'de seçim komutunu başlat
            print("Seçim komutu başlatılıyor...")
            self.doc.Utility.Prompt("\nTemel demiri textlerini seçin ve ENTER'a basın: ")
            
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
                    if item.ObjectName == "AcDbText" or item.ObjectName == "AcDbMText":
                        try:
                            # COM nesnesini al
                            text_obj = self.doc.HandleToObject(item.Handle)
                            text_value = text_obj.TextString.strip()
                            print(f"Text bulundu: {text_value}")
                            
                            # Rengi kırmızı yap (AutoCAD renk kodu: 1 = Kırmızı)
                            try:
                                text_obj.TrueColor = self.doc.Application.GetInterfaceObject("AutoCAD.AcCmColor.24")
                                text_obj.TrueColor.SetRGB(255, 0, 0)  # Kırmızı
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
            
            return selected_texts
            
        except Exception as e:
            print(f"Çoklu seçim hatası: {str(e)}")
            return []

    def process_multiple_foundation_rebars(self):
        """Çoklu temel demiri seçim işlemini yönet"""
        logging.info("Çoklu temel demiri seçim işlemi başlatıldı")
        
        try:
            # Temel demiri textlerini seç
            selected_texts = self.select_multiple_foundation_rebars()
            
            if not selected_texts:
                logging.warning("Temel demiri seçimi iptal edildi veya hiç text seçilmedi")
                return False
            
            logging.info(f"Seçilen text sayısı: {len(selected_texts)}")
            
            # Dimension seçimi (sadece bir kez)
            dimension = self.select_entity("Temel genişliğini seçin (dimension)")
            if dimension is None:
                logging.warning("Dimension seçimi iptal edildi")
                return False
            
            try:
                width = float(dimension)
                logging.info(f"- Temel genişliği: {width} cm")
            except ValueError:
                logging.error("Geçersiz dimension değeri")
                return False
            
            # Her bir text için işlem yap
            success_count = 0
            for text in selected_texts:
                logging.info(f"İşlenen text: {text}")
                
                # Çap, aralık ve boy bilgilerini çıkar
                pattern = r'[ƒØ∅](\d+)/(\d+)\s*[Ll]\s*=\s*(\d+)\s*(ALT|ÜST|alt|üst|Üst|Alt)?'
                match = re.search(pattern, text)
                
                if not match:
                    logging.warning(f"Text işlenemedi: {text}")
                    continue
                
                diameter = float(match.group(1))
                spacing = float(match.group(2))
                length = float(match.group(3))
                position = match.group(4) if match.group(4) else "ALT"  # Varsayılan olarak ALT
                
                logging.info(f"Temel Demiri Bilgileri:")
                logging.info(f"- Çap: Ø{diameter}")
                logging.info(f"- Aralık: {spacing} cm")
                logging.info(f"- Boy: {length} cm")
                logging.info(f"- Pozisyon: {position}")
                
                # Hesaplamaları yap
                if self.calculator.process_foundation_rebar(diameter, spacing, length, width, position):
                    success_count += 1
                    logging.info(f"Temel demiri hesabı başarıyla tamamlandı: {text}")
                else:
                    logging.warning(f"Temel demiri hesabı başarısız oldu: {text}")
            
            # İşlem bittiğinde özeti göster
            if success_count > 0:
                print(f"\n{success_count} adet temel demiri hesabı başarıyla tamamlandı.")
                print("\nTEMEL DEMİRİ HESABI ÖZETİ")
                self.calculator.show_summary('FOUNDATION')
                self.calculator.log_summary('FOUNDATION')
                return True
            else:
                logging.warning("Hiçbir temel demiri hesaplanamadı")
                return False
                
        except Exception as e:
            logging.error(f"Çoklu temel demiri seçim hatası: {str(e)}")
            return False

    def process_wall_mesh(self, mahal_bilgisi):
        """Perde hasırı seçimini işle"""
        try:
            print("\nPerde hasırı seçimi başlatıldı...")
            print(f"Mahal: {mahal_bilgisi}")
            
            # Hasır kodunu seç
            mesh_codes = self.select_multiple_entities("Hasır kodlarını seçin (örn: Q188, Q221, vb.)")
            if not mesh_codes:
                print("Hasır kodu seçilmedi veya işlem iptal edildi!")
                return False
            
            # Ebat bilgisi için metin seç
            dimensions_texts = self.select_multiple_entities("Hasır ebatlarını seçin (örn: 320/215 veya 215x336)")
            if not dimensions_texts:
                print("Hasır ebatı seçilmedi veya işlem iptal edildi!")
                return False
            
            # Seçilen hasır kodları ve ebatları işle
            for mesh_code in mesh_codes:
                # Hasır kodunu temizle ve işle
                mesh_code = mesh_code.strip().upper()
                print(f"Hasır kodu: {mesh_code}")
                
                # Çoklu hasır kontrolü (örn: 2xQ317/317)
                multiplier = 1
                multiplier_match = re.search(r'(\d+)X', mesh_code)
                if multiplier_match:
                    multiplier = int(multiplier_match.group(1))
                    mesh_code = mesh_code.split('X', 1)[1]  # Çarpan kısmını kaldır
                
                print(f"Hasır tipi: {mesh_code}, Çarpan: {multiplier}")
                
                # Her hasır kodu için bir ebat seç
                if dimensions_texts:
                    dimensions_text = dimensions_texts.pop(0)  # İlk ebatı al ve listeden çıkar
                else:
                    print("Uyarı: Hasır ebatı kalmadı, varsayılan değer kullanılacak!")
                    dimensions_text = "100x100"  # Varsayılan ebat
                
                # Ebat bilgisini işle
                dimensions_match = re.search(r'(\d+)[xX×/](\d+)', dimensions_text)
                if dimensions_match:
                    width = float(dimensions_match.group(1))
                    height = float(dimensions_match.group(2))
                    area_cm2 = width * height
                    area_m2 = area_cm2 / 10000
                    print(f"Seçilen ebat: {width}x{height} cm = {area_cm2} cm² = {area_m2:.2f} m²")
                else:
                    # Ebat formatı tanınmadıysa, varsayılan değer kullan
                    print("Uyarı: Geçersiz ebat formatı, varsayılan değer kullanılacak!")
                    area_m2 = 1.0  # Varsayılan alan (m²)
                    area_cm2 = area_m2 * 10000
                    width = 100
                    height = 100
                
                print(f"Hasır alanı: {area_cm2} cm² = {area_m2:.2f} m²")
                
                # Hasır ağırlığını hesapla
                from mesh_data import MeshData
                weight_per_m2 = MeshData.get_weight_per_m2(mesh_code)
                if weight_per_m2 <= 0:
                    print(f"Uyarı: {mesh_code} için birim ağırlık bulunamadı!")
                    weight_per_m2 = 3.0  # Varsayılan değer
                
                # Çarpan ile toplam ağırlığı hesapla
                total_weight = area_m2 * weight_per_m2 * multiplier
                print(f"Birim ağırlık: {weight_per_m2:.2f} kg/m²")
                print(f"Toplam ağırlık: {total_weight:.2f} kg ({multiplier} kat)")
                
                # Hasır çap ve aralık bilgilerini al
                diameter, spacing = MeshData.get_properties(mesh_code)
                
                # Sonucu oluştur
                from rebar_calculator import RebarData
                result = RebarData(
                    type="MESH_WALL",
                    mesh_code=mesh_code,
                    diameter=diameter,
                    spacing=spacing,
                    area=area_m2,
                    width=width,
                    height=height,
                    unit_weight=weight_per_m2,
                    total_weight=total_weight,
                    description=f"Perde Hasırı {multiplier}x{mesh_code} {dimensions_text} - {area_m2:.2f} m²"
                )
                
                # Sonucu kaydet
                self.calculator.results.append(result)
            
            # Metraj raporunu oluştur
            self.calculator.write_mesh_report(mahal_bilgisi, "WALL")
            
            print("\nPerde hasırı hesabı başarıyla tamamlandı!")
            return True
            
        except Exception as e:
            import traceback
            print(f"\nPerde hasırı hesaplama hatası: {str(e)}")
            print(traceback.format_exc())
            return False

    def process_slab_mesh(self, mahal_bilgisi):
        """Döşeme hasırı seçimini işle"""
        try:
            print("\nDöşeme hasırı seçimi başlatıldı...")
            print(f"Mahal: {mahal_bilgisi}")
            
            # Hasır kodlarını seç
            mesh_codes = self.select_multiple_entities("Hasır kodlarını seçin (örn: Q188, Q221, vb.)")
            if not mesh_codes:
                print("Hasır kodu seçilmedi veya işlem iptal edildi!")
                return False
            
            # Seçilen hasır kodları işle
            for i, mesh_code_text in enumerate(mesh_codes):
                # Hasır kodunu temizle ve işle
                mesh_code_text = mesh_code_text.strip().upper()
                print(f"Hasır kodu: {mesh_code_text}")
                
                # Çoklu hasır kontrolü (örn: 2xQ317/317)
                multiplier = 1
                multiplier_match = re.search(r'(\d+)X', mesh_code_text)
                if multiplier_match:
                    multiplier = int(multiplier_match.group(1))
                    mesh_code_text = mesh_code_text.split('X', 1)[1]  # Çarpan kısmını kaldır
                
                # R tipi hasır kontrolü ve ebat bilgisi çıkarma
                is_r_type = False
                dimensions_match = None
                
                if mesh_code_text.startswith('R'):
                    print(f"R tipi hasır tespit edildi: {mesh_code_text}")
                    is_r_type = True
                    
                    # R tipi hasır formatı: "R257  360/215" -> kod: "R257", ebat: "360/215"
                    dimensions_match = re.search(r'R\d+\s+(\d+)[/xX×](\d+)', mesh_code_text)
                    if dimensions_match:
                        width = float(dimensions_match.group(1))
                        height = float(dimensions_match.group(2))
                        print(f"Hasır ebatı tespit edildi: {width}x{height} cm")
                    
                    # Hasır kodunu temizle (örn: "R257 360/215" -> "R257")
                    mesh_code = re.match(r'(R\d+)', mesh_code_text).group(1)
                else:
                    # Q tipi hasır için sadece kodu al
                    mesh_code = mesh_code_text
                
                print(f"Hasır tipi: {mesh_code}, Çarpan: {multiplier}")
                
                # Ebat bilgisi için metin seç (eğer R tipi hasırdan çıkarılmadıysa)
                if not dimensions_match:
                    dimensions_texts = self.select_multiple_entities("Hasır ebatlarını seçin (örn: 320/215 veya 215x336)")
                    if not dimensions_texts:
                        print("Hasır ebatı seçilmedi veya işlem iptal edildi!")
                        return False
                    
                    # Her hasır kodu için bir ebat seç
                    if i < len(dimensions_texts):
                        dimensions_text = dimensions_texts[i]
                    else:
                        print("Uyarı: Hasır ebatı kalmadı, varsayılan değer kullanılacak!")
                        dimensions_text = "100x100"  # Varsayılan ebat
                    
                    # Ebat bilgisini işle
                    dimensions_match = re.search(r'(\d+)[xX×/](\d+)', dimensions_text)
                    if dimensions_match:
                        width = float(dimensions_match.group(1))
                        height = float(dimensions_match.group(2))
                    else:
                        # Ebat formatı tanınmadıysa, varsayılan değer kullan
                        print("Uyarı: Geçersiz ebat formatı, varsayılan değer kullanılacak!")
                        width = 100
                        height = 100
                
                # Alan hesapla
                area_cm2 = width * height
                area_m2 = area_cm2 / 10000
                print(f"Seçilen ebat: {width}x{height} cm = {area_cm2} cm² = {area_m2:.2f} m²")
                print(f"Hasır alanı: {area_cm2} cm² = {area_m2:.2f} m²")
                
                # Hasır ağırlığını hesapla
                from mesh_data import MeshData
                weight_per_m2 = MeshData.get_weight_per_m2(mesh_code)
                
                # R tipi hasırlar için özel birim ağırlık kontrolü
                if is_r_type and weight_per_m2 <= 0:
                    # R tipi hasırlar için birim ağırlık tablosu
                    r_type_weights = {
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
                        'R589': 5.66
                    }
                    
                    if mesh_code in r_type_weights:
                        weight_per_m2 = r_type_weights[mesh_code]
                        print(f"R tipi hasır için birim ağırlık: {weight_per_m2} kg/m²")
                    else:
                        print(f"Uyarı: {mesh_code} için birim ağırlık bulunamadı!")
                        weight_per_m2 = 3.0  # Varsayılan değer
                elif weight_per_m2 <= 0:
                    print(f"Uyarı: {mesh_code} için birim ağırlık bulunamadı!")
                    weight_per_m2 = 3.0  # Varsayılan değer
                
                # Çarpan ile toplam ağırlığı hesapla
                total_weight = area_m2 * weight_per_m2 * multiplier
                print(f"Birim ağırlık: {weight_per_m2:.2f} kg/m²")
                print(f"Toplam ağırlık: {total_weight:.2f} kg ({multiplier} kat)")
                
                # Hasır çap ve aralık bilgilerini al
                diameter, spacing = MeshData.get_properties(mesh_code)
                
                # Sonucu oluştur
                from rebar_calculator import RebarData
                result = RebarData(
                    type="MESH_SLAB",
                    mesh_code=mesh_code,
                    diameter=diameter,
                    spacing=spacing,
                    area=area_m2,
                    width=width,
                    height=height,
                    unit_weight=weight_per_m2,
                    total_weight=total_weight,
                    description=f"Döşeme Hasırı {multiplier}x{mesh_code} {width}x{height} - {area_m2:.2f} m²"
                )
                
                # Sonucu kaydet
                self.calculator.results.append(result)
            
            # Metraj raporunu oluştur
            self.calculator.write_mesh_report(mahal_bilgisi, "SLAB")
            
            print("\nDöşeme hasırı hesabı başarıyla tamamlandı!")
            return True
            
        except Exception as e:
            import traceback
            print(f"\nDöşeme hasırı hesaplama hatası: {str(e)}")
            print(traceback.format_exc())
            
            # Hata durumunda da seçim setini temizlemeye çalış
            try:
                selection = self.doc.SelectionSets.Item("TempSelection")
                selection.Delete()
            except:
                pass
            
            return False

    def select_area(self):
        """Alan seçimi yap ve cm² cinsinden döndür"""
        try:
            # Kullanıcıdan alan değerini manuel girmesini iste
            area_text = self.select_entity("Alan değerini içeren metni seçin (örn: 12.5 m² veya 215x336)")
            if not area_text:
                print("Alan değeri seçilmedi!")
                return 0
            
            # Alan değerini çıkar
            area_match = re.search(r'(\d+[.,]?\d*)\s*m²', area_text)
            if area_match:
                # m² cinsinden alan değeri
                area_m2 = float(area_match.group(1).replace(',', '.'))
                area_cm2 = area_m2 * 10000  # m² -> cm² dönüşümü
                print(f"Seçilen alan: {area_m2} m² = {area_cm2} cm²")
                return area_cm2
            
            # Sonra "AxB" formatını kontrol et (örn: 215x336 veya 320/215)
            dimensions_match = re.search(r'(\d+)[xX×/](\d+)', area_text)
            if dimensions_match:
                width = float(dimensions_match.group(1))
                height = float(dimensions_match.group(2))
                area_cm2 = width * height
                area_m2 = area_cm2 / 10000
                print(f"Seçilen boyutlar: {width}x{height} cm = {area_cm2} cm² = {area_m2:.2f} m²")
                return area_cm2
            
            # Eğer özel formatlar eşleşmezse, sayı olarak dene
            area_match = re.search(r'(\d+[.,]?\d*)', area_text)
            if area_match:
                # Sayı olarak alan değeri (varsayılan birim m²)
                area_m2 = float(area_match.group(1).replace(',', '.'))
                area_cm2 = area_m2 * 10000  # m² -> cm² dönüşümü
                print(f"Seçilen alan: {area_m2} m² = {area_cm2} cm²")
                return area_cm2
            
            print("Geçerli bir alan değeri bulunamadı!")
            return 0
            
        except Exception as e:
            print(f"Alan seçim hatası: {str(e)}")
            return 0