from autocad_integration import AutoCADIntegration
import time
from rebar_calculator import RebarCalculator

def main():
    try:
        print("\nAutoCAD entegrasyonu başlatılıyor...")
        acad_integration = AutoCADIntegration()
        print("AutoCAD bağlantısı başarılı!")

        while True:
            print("\nLütfen seçim yapın:")
            print("1. Yeni demir hesabı")
            print("2. Hasır donatı hesabı")
            print("3. Ara bağlantı hesabı")
            print("4. Sonuçları göster")
            print("5. Sonuçları kaydet")
            print("6. Çıkış")
            
            choice = input("\nSeçiminiz (1-6): ")
            
            if choice == "1":
                while True:
                    print("\nHesap türünü seçin:")
                    print("1. Etriye hesabı")
                    print("2. Boy demiri hesabı")
                    print("3. Ana menüye dön")
                    
                    calc_type = input("\nSeçiminiz (1-3): ")
                    
                    if calc_type == "1":
                        print("\nEtriye hesabı başlatılıyor...")
                        success = acad_integration.process_stirrup_selection()
                        if success:
                            print("\nBaşka etriye hesabı yapmak ister misiniz? (E/H): ")
                            if input().upper() != 'E':
                                break
                        else:
                            print("\nİşlem tamamlanamadı. Tekrar denemek ister misiniz? (E/H): ")
                            if input().upper() != 'E':
                                break
                                
                    elif calc_type == "2":
                        print("\nBoy demiri hesabı başlatılıyor...")
                        success = acad_integration.process_rebar_selection()
                        if success:
                            print("\nBaşka boy demiri hesabı yapmak ister misiniz? (E/H): ")
                            if input().upper() != 'E':
                                break
                        else:
                            print("\nİşlem tamamlanamadı. Tekrar denemek ister misiniz? (E/H): ")
                            if input().upper() != 'E':
                                break
                                
                    elif calc_type == "3":
                        break
                    
                    else:
                        print("\nGeçersiz seçim!")
                
            elif choice == "2":
                while True:
                    print("\nHasır tipi seçin:")
                    print("1. Döşeme hasırı")
                    print("2. Perde hasırı")
                    print("3. Ana menüye dön")
                    
                    mesh_type = input("\nSeçiminiz (1-3): ")
                    
                    if mesh_type == "1":
                        success = acad_integration.process_mesh_selection('SLAB')
                    elif mesh_type == "2":
                        success = acad_integration.process_mesh_selection('WALL')
                    elif mesh_type == "3":
                        break
                    
            elif choice == "3":
                acad_integration.process_connection_selection()
                
            elif choice == "4":
                # Sonuçları göster
                if acad_integration.calculator.results:
                    print("\nHesaplanan Sonuçlar:")
                    for i, result in enumerate(acad_integration.calculator.results, 1):
                        print(f"\nSonuç {i}:")
                        print(f"Tip: {result.type}")
                        print(f"Çap: Ø{result.diameter}")
                        if result.spacing:
                            print(f"Aralık: {result.spacing} cm")
                        print(f"Boy: {result.length} cm")
                        print(f"Adet: {result.count}")
                        print(f"Toplam Boy: {result.total_length} cm")
                        print(f"Toplam Boy (metre): {result.total_length/100:.2f} m")
                        print(f"Birim Ağırlık: {result.weight_per_meter:.3f} kg/mt")
                        print(f"Toplam Ağırlık: {result.total_weight:.2f} kg")
                        print("-" * 30)
                else:
                    print("\nHenüz hesaplanmış sonuç yok!")
                
            elif choice == "5":
                # Sonuçları kaydet
                if acad_integration.calculator.results:
                    filename = input("\nKayıt dosyası adı: ")
                    acad_integration.calculator.export_results(filename)
                    print(f"Sonuçlar '{filename}' olarak kaydedildi!")
                else:
                    print("\nKaydedilecek sonuç yok!")
                
            elif choice == "6":
                print("\nProgram sonlandırılıyor...")
                break
            
            else:
                print("\nGeçersiz seçim!")

    except Exception as e:
        print(f"\nHata oluştu: {str(e)}")

def test_calculation():
    calculator = RebarCalculator()
    
    print("\n=== Test: Etriye Hesabı ===")
    
    # Test verisi
    print("\nTest Verileri:")
    print("1. Etriye boyu: ƒ10 Etr. l= 246ÿÿÿÿ")  # Etriye boyu 246 cm
    print("2. Etriye aralığı: Etr.∅10/8")  # 8 cm arayla
    print("3. Kolon boyu: 291.0")  # 291 cm uzunluk
    
    calculator.process_text("ƒ10 Etr. l= 246ÿÿÿÿ")
    calculator.process_text("Etr.∅10/8")
    calculator.process_dimension(291.0)
    
    # Sonuçları kontrol et ve kaydet
    if calculator.results:
        print("\nHesaplanan Sonuçlar:")
        for i, result in enumerate(calculator.results, 1):
            print(f"\nSonuç {i}:")
            print(f"Tip: {result.type}")
            print(f"Çap: Ø{result.diameter}")
            print(f"Aralık: {result.spacing} cm")
            print(f"Boy: {result.length} cm")
            print(f"Adet: {result.count}")
            print(f"Toplam Boy: {result.total_length} cm")
            print(f"Toplam Boy (metre): {result.total_length/100:.2f} m")
            print("-" * 30)
        
        calculator.export_results("test_sonuc")
        print("\nSonuçlar 'test_sonuc' olarak kaydedildi.")
    else:
        print("Hata: Sonuç üretilemedi!")

if __name__ == "__main__":
    try:
        print("Test hesaplaması yapılıyor...")
        test_calculation()
        
        print("\nAutoCAD entegrasyonuna geçiliyor...")
        main()
    except Exception as e:
        print(f"Hata oluştu: {str(e)}") 