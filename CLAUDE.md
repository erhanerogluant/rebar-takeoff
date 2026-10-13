# CLAUDE.md — Rebar Take-off

AutoCAD çizimlerinden demir metrajı çıkaran Windows masaüstü uygulaması (Python, PyQt6,
AutoCAD COM, AutoLISP). Ayrıntı: [README.md](README.md).

**Yeni bir oturumda önce [docs/GECMIS.md](docs/GECMIS.md) dosyasını oku.** Konuşulanlar,
hangi sürümün neden seçildiği, düzeltilen hatalar ve açık işler orada. Yeni karar ve
gelişmeleri oraya tarihli olarak (en yeni en üstte) ekle.

## Kurallar
- Kullanıcıyla Türkçe konuş; kod, commit mesajı İngilizce.
- Hesap değerleri (birim ağırlıklar, hasır tablosu) tek kaynaktan gelir: çap ağırlıkları
  `RebarCalculator.weight_table`, hasırlar `mesh_data.py`. Tablo dışı değerde tahmin yapma,
  uyar ve reddet.
- Metraj sonucunu etkileyen her değişikliğe elle hesaplanmış değerli test ekle.
- AutoCAD'e bağlanan kodu (`rebar_gui.RebarCalculatorGUI()`, `AutoCADIntegration()`) testte
  çalıştırma: AutoCAD'i arka planda başlatır.

## Komutlar
```bash
install.bat                                   # .venv + paketler + testler
run.bat                                       # GUI (AutoCAD açıkken)
.venv\Scripts\python -m unittest discover -s tests -v
```
