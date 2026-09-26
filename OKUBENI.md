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
| `cizim/geometri.py` | Girdiden **çizim elemanları** üretir ( saf veri ) — kuyu planı |
| `cizim/kabin_ustu.py` | Kabin üstü planı:  kuyu planının elemanlarını okur, tavanı ekler |
| `cizim/svg.py` | Elemanları SVG'ye yazar |
| `cizim/dxf.py` | **Aynı** elemanları DXF'e yazar ( ezdxf ) |
| `testler/test_cizim.py` | 67 test |
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
   Parçalar da birbirine göre denetlenir:  karşı ağırlık kendi rayları
   arasına ( genişlik < DBGW ), kabin şasesi kabin rayları arasına ( < DBG )
   sığar, kat kapısı kabinin önüne düşer, ağırlık yandaysa o taraftaki kabin
   rayının ara kirişi ağırlıkla ray arasına sığar.
5. **Yerleşim seçilir, koda gömülmez.**  Askı düzeni ( kabin altı · kabin üstü ·
   doğrudan ), karşı ağırlık yeri ( sağ · sol · arka ), kapı tipi girdidendir.
6. **Uzatma çizgisi yoktur, yazı kendi ölçüsünün yanındadır.**  Ölçü çizgisi
   yalnız iki uçtaki kısa çizgiyle çizilir ( SVG ve DXF — `dimse1/dimse2` ).
   Bir iç parçayı ölçen ölçü ( eşikler, askı aralığı ve kaçıklığı ) planın
   dışında değil, parçanın yanında durur.  Yazının yeri geometride bulunur
   ( `_yazilari_yerlestir` );  sığmayan yazı sıranın ucunun dışına ya da bir
   kat dışarı alınır, başka bir sıranın üstüne itilmez.  Test:  hiçbir iki
   ölçü yazısı üst üste binmez, hepsi çerçevenin içindedir.

## Bugün ne çiziliyor

**Kuyu planı** ( kabin hizasından yatay kesit ):  duvarlar ve kesit taraması,
kapı boşluğu · kasa · eşik · kanatlar · açılış oku, kabin panosu ve şasesi
( dikmeler + alt/üst kirişler ), kabin rayları T profiliyle, ray konsolları
( plaka + kol + cıvata delikleri ), patenler, karşı ağırlık çerçevesi ve
kasnağı, karşı ağırlık rayları ve konsolları, askı kasnakları ya da askı
noktaları, kumanda panosu, eksenler, 46 ölçü ve çerçeve + künye şeridi.

**Kabin üstü planı** ( kabin tavanı hizasından yatay kesit ):  duvarlar, raylar,
konsollar ve karşı ağırlık kuyu planından aynen alınır ( ikinci kez
hesaplanmaz );  ön duvar dolu çizilir ( kesit kapı lentosunun üstünden geçer ).
Tavanda:  kabin tavanı ve şase dikmeleri, kapı operatörü ( kapı tipine göre
kanatların kaydığı boy ), askı ( kabin üstünde kasnaklar · kabin altında
halatların tavan dışından geçtiği yer · doğrudan askıda askı noktaları ).
Standarttan hesaplananlar:

| Kural | Madde | Ne yapılır |
|---|---|---|
| Tavan kenarından duvara boşluk **> 0,30 m** ise korkuluk | m.5.4.7.2 b | Her kenar ayrı;  gerekli kenara küpeşte çizilir |
| Küpeşte kuyudaki parçalardan **≥ 0,10 m** | m.5.4.7.4 d | Gerekirse kenardan içeri alınır, ölçüsü yazılır |
| Küpeşte kenardan **≤ 0,15 m** içeride | m.5.4.7.4 c | Aşılırsa çizim reddedilir |
| Yükseklik:  küpeşte – duvar **≤ 0,50 m → 0,70 m**, aşarsa **1,10 m** | m.5.4.7.4 b | Küpeştenin yanına yazılır |
| Sığınma alanı **0,40 × 0,50** ( dik duruş ) / **0,50 × 0,70** ( çömelme ) | m.5.2.5.7.1 · Çizelge 3 | Korkulukların içinde, operatör ve askı dışında, kapıya en yakın yere konur;  yer yoksa reddedilir |

Ayrıca:  kabin altı askıda halat kuyudaki bir parçanın içinden geçemez;
kabin üstü kasnağı korkuluğun yolunu kesemez;  pano halatın ve konsolların
yolundan kayar;  kabin rayı ekseni kabinin derinliği içinden geçmelidir.
Çizilmeyenler:  şase üst kirişi ve revizyon kutusu ( tedarikçi ölçüsü yok ),
etek tahtası ( planda tavan kenarıyla çakışır ).

## Sırada ne var

1. Kuyu dibi yatay kesiti ( tamponlar, regülatör gergisi, merdiven )
2. Makine dairesi / kuyu üstü yatay kesiti
3. Düşey kesitler ( kabin en altta · en üstte · tampona oturmuş ) ve kat kotları
4. `cizim/kopru.py` — girdilerin hesap programından dolması.  Önce iki tanım
   eşitlenmeli:  ray – kapı arası hesapta kat kapısı düzleminden ( RK ),
   çizimde kuyu iç yüzünden;  kabin kaçıklığı hesapta ray ekseninden ( yc ),
   çizimde kuyu ortasından ölçülüyor.
5. Ofis şablonuna ( TİP PROJE FORMATI ) yerleştirme

**Başka bir referans:**  kullanıcının LiftDesigner çıktıları ( `12744-3 lift.dwg` ):
kuyu planı, düşey kesit, makine odası, kuyu üstü ve kuyu dibi kesitleri, kuyu
dibi görünüşü, giriş görünüşleri, kasnak düzenlemesi ( sarım açısı ) ve iskele
planı.  Ölçüler SW · SD · CW · CD · DW · PLW · PLD · DBG · BG kısaltmalarıyla
verilir;  uzatma çizgileri kısadır, planı kesmez.

## Ölçülerin kaynağı

`cizim/sabitler.py` içindeki ürün ölçüleri ve `girdi.ORNEK`, ELEport'un
yayımlanmış örnek projesinin çizim geometrisinden ölçülerek alındı ( karşı
ağırlık çerçevesi 790 × 160, kapı kasaya 610 → boşluğa 730, kasnaklar arası
690 + 690 = 1.380, ara kiriş 50 );  ölçek 1/20 üzerinden
kalibre edildi ve kalibrasyon ray profilleriyle doğrulandı ( T89/B 89 × 62 ve
T70/A 70 × 65 tam çıktı ).  Tek bir projenin donanımıdır — tedarikçi verisi
gelince değiştirilmelidir.
