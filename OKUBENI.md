# ASANSÖR ÇİZİM MODÜLÜ

Asansör kuyusunun **proje çizimlerini** girdilerden üreten bağımsız modül.
Çıktı hem **SVG** ( ekranda görmek için ) hem **DXF** ( AutoCAD ) olarak verilir.

Hesap programından ( `AVAN HESAPLAMA PROGRAMI` ) **tamamen ayrıdır**:  ondan
hiçbir şey import etmez, onun dosyalarına dokunmaz.  İleride ikisi bir köprüyle
birleştirilecek;  o zaman çizim girdisinin bir bölümü hesabın sonuçlarından
dolacak.

## Kurulum ve çalıştırma

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python calistir.py                      # kuyu planı  →  ornekler/
.venv/bin/python calistir.py --aski Doğrudan      # 1:1 askı düzeniyle
.venv/bin/python calistir.py --agirlik Arka       # karşı ağırlık arkada
.venv/bin/python -m unittest testler.test_cizim   # testler
```

## Klasörler

| Yol | Ne var |
|---|---|
| `cizim/girdi.py` | Çizim girdisinin **sözleşmesi**, doğrulaması ve deneme ölçüleri |
| `cizim/sabitler.py` | Ofisin ürün ölçüleri ( konsol, paten, kasa, pano … ) |
| `cizim/geometri.py` | Girdiden **çizim elemanları** üretir ( saf veri ) |
| `cizim/svg.py` | Elemanları SVG'ye yazar |
| `cizim/dxf.py` | **Aynı** elemanları DXF'e yazar ( ezdxf ) |
| `testler/test_cizim.py` | 38 test |
| `ornekler/` | `calistir.py`'nin ürettiği örnek çizimler |

## Kurallar

1. **Çizim sayı türetmez.**  Kuyu boyu, ray boyu, tampon stroku gibi değerler
   girdiden gelir;  ileride hesabın kendi sonuçlarından dolacak.  İki ayrı
   doğruluk kaynağı olmayacak.
2. **SVG ve DXF aynı eleman listesinden çıkar.**  İkinci bir çizici yazılmaz,
   yoksa zamanla ayrışırlar.
3. **Ölçü zincirleri kapanır.**  Parçaların toplamı toplam ölçüye eşit olmalı;
   test bunu arar.
4. **Standardın sınırları denetlenir.**  TS EN 81-20 m.5.2.5.3.1 ( kuyu iç yüzü
   – kabin ön yüzü ≤ 150 mm ) ve m.5.3.4.1 ( kabin eşiği – kat eşiği ≤ 35 mm ).
5. **Yerleşim seçilir, koda gömülmez.**  Askı düzeni ( kabin altı · kabin üstü ·
   doğrudan ), karşı ağırlık yeri ( sağ · sol · arka ), kapı tipi girdidendir.

## Bugün ne çiziliyor

**Kuyu planı** ( kabin hizasından yatay kesit ):  duvarlar ve kesit taraması,
kapı boşluğu · kasa · eşik · kanatlar · açılış oku, kabin panosu ve şasesi
( dikmeler + alt/üst kirişler ), kabin rayları T profiliyle, ray konsolları
( plaka + kol + cıvata delikleri ), patenler, karşı ağırlık çerçevesi ve
kasnağı, karşı ağırlık rayları ve konsolları, askı kasnakları ya da askı
noktaları, kumanda panosu, eksenler, 46 ölçü ve çerçeve + künye şeridi.

## Sırada ne var

1. Kuyu dibi yatay kesiti ( tamponlar, regülatör gergisi, merdiven )
2. Makine dairesi / kuyu üstü yatay kesiti
3. Düşey kesitler ( kabin en altta · en üstte · tampona oturmuş ) ve kat kotları
4. `cizim/kopru.py` — girdilerin hesap programından dolması
5. Ofis şablonuna ( TİP PROJE FORMATI ) yerleştirme

## Ölçülerin kaynağı

`cizim/sabitler.py` içindeki ürün ölçüleri, ELEport'un yayımlanmış örnek
projesinin çizim geometrisinden ölçülerek alındı;  ölçek 1/20 üzerinden
kalibre edildi ve kalibrasyon ray profilleriyle doğrulandı ( T89/B 89 × 62 ve
T70/A 70 × 65 tam çıktı ).  Tek bir projenin donanımıdır — tedarikçi verisi
gelince değiştirilmelidir.
