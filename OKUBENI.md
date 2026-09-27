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
| `cizim/kuyu_dibi.py` | Kuyu dibi planı:  tamponlar, perde, gergi, sığınma alanı, merdiven |
| `cizim/kuyu_ustu.py` | Kuyu üstü planı ( MRL ):  makine, halat bağlantıları, regülatör, acil pano |
| `cizim/makine_dairesi.py` | Makine dairesi planı + döşeme halat delik planı |
| `cizim/dusey.py` | Düşey kesitler:  kuyu dibi ( kabin tamponda ) ve kuyu üstü ( kabin en üstte ) |
| `cizim/svg.py` | Elemanları SVG'ye yazar |
| `cizim/dxf.py` | **Aynı** elemanları DXF'e yazar ( ezdxf ) |
| `testler/test_cizim.py` | 81 test |
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

**Kuyu dibi planı** ( kuyu tabanından yatay kesit ):  duvarlar, raylar ve
konsollar kuyu planından;  kabinin izi ve kat kapısı yalnız yer göstermek için
kesik çizilir.  Kuyu tabanına yük aktaran noktalar hesap paftasının 9.
bölümündeki adlarla işaretlenir:  **FKR** kabin rayı · **Fkt** kabin tamponu ·
**FAR** ağırlık rayı · **Fat** ağırlık tamponu ( değerleri köprüyle gelecek ).

| Kural | Madde | Ne yapılır |
|---|---|---|
| Kabin ve karşı ağırlık tamponu | m.5.8.1.1 | Kabin tamponu kabin ekseninde, ray ekseni üstünde;  ağırlık tamponu ağırlığın ortasında ( 1 ya da 2 adet ).  Ağırlığın / kabinin altına düşmezse, raya çarparsa reddedilir |
| Karşı ağırlık perdesi, en az ağırlık genişliğinde | m.5.2.5.5.1 d | Ağırlık rayları arasının tamamı boyunca, ağırlığın kuyuya bakan yüzünde |
| Kabin ile karşı ağırlık arası **≥ 50 mm** | m.5.2.5.5.1 h | Kuyu planının doğrulamasında ( önce 20 mm'lik bir çizim kalkanıydı ) |
| Sığınma alanı **0,40 × 0,50** / **0,50 × 0,70** / **0,70 × 1,00** | m.5.2.5.8.1 · Çizelge 4 | Kabinin izinin altında, tampon / gergi / merdiven dışında, kapıya en yakın yere |
| Kuyu dibi **≤ 2,50 m** ise merdiven, aşarsa erişim kapısı | m.5.2.2.4 | Merdiven yalnız 2,50 m'ye kadar çizilir |
| Merdiven kat girişinin kenarına **≤ 800 mm** | Ek F.5 b | Kapıya yakın yan duvara yaslanır;  sığmazsa reddedilir.  Ölçüsü 350 × 100 ( Ek F.3 ) |

Regülatör gergi kasnağı seçilen yandaki kabin rayının hizasında, ray
ekseninin arkasında durur ( girdi:  yan, eksene uzaklık, kasnak çapı ).
Çizilmeyenler:  kuyu dibi durdurma düğmesi ve revizyon kutusu ( yer kuralları
m.5.2.1.5.1 — ölçüleri yok ).

**Kuyu üstü planı** ( makine dairesiz — kuyu tepesinden yatay kesit;  ELEport'un
MRL paftasındaki "Machine Room" çizimi ):  duvarlar, raylar, konsollar kuyu
planından;  kabin, karşı ağırlık ve kat kapısı yalnız izleriyle ( kesik ).

- **Halatlar düşey iner.**  Tahrik kasnağının bir teğeti kabinin yakın
  halatının ( kabin kasnağının dış teğeti ) hizasındadır;  öbür teğetinden inen
  halat karşı ağırlık kasnağının teğetine düşmelidir.  Düşmüyorsa sapma
  **HALAT SAPMASI** ölçüsüyle gösterilir.  ELEport'ta birebir tutar:
  370 − 240 = 130 ( ağırlık ekseni ).
- **Makine** tahrik kasnağının ağırlık eksenine bakan tarafında;  **halat
  bağlantıları** ağırlık kasnağının öbür teğetinin ve kabinin uzak halatının
  üstünde;  **regülatör** kuyu dibindeki gergi kasnağının tam üstünde.
- **Acil kurtarma ve test panosu** ( m.5.2.6.6 ) kuyunun dışında, en üst katta
  kapının seçilen yanında;  önünde **0,70 m** derin, **en az 0,50 m** ya da pano
  eni kadar çalışma alanı ( m.5.2.6.6.4 → m.5.2.6.3.2.1 a ).
- Ölçüler ELEport'un makinesinden ( `sabitler.py` ):  kasnak 240 × 105, gövde
  298 × 279, bağlantı plakaları 264 × 120 ve 127 × 200, regülatör 80 × 300
  ( gövde 130 × 180 ), pano 400 × 300.  Başka makinede katalogdan değiştirilir.
- Karşı ağırlığın ekseni artık girdidir ( `agirlik.eksen_kaciklik`, ELEport
  −50 ):  kabin ray ekseninde sabit dururken halat ağırlık kasnağına 95 mm
  kaçık düşüyordu.
- Bugün yalnız yandaki karşı ağırlık + kabin altı 2:1 askı çizilir;  öteki
  düzenler açıkça reddedilir.

**Makine dairesi planı** ve **kuyu üstü döşeme halat delik planı** ( makine
daireli asansör ):  makinenin, halatların, bağlantıların ve regülatörün yeri
kuyu üstü planıyla AYNIDIR ( `kuyu_ustu.yerlesim(…, acil_pano=False)` ) —
halatlar aynı noktalardan iner, bu kez döşeme deliklerinden geçer.

| Kural | Madde | Ne yapılır |
|---|---|---|
| Kapı en az **0,60 m** | m.5.2.3.2 a | Altı reddedilir |
| Kumanda panosunun önünde **0,70 m** derin, **en az 0,50 m** ya da pano eni | m.5.2.6.3.2.1 a | Pano seçilen duvar boyunca kapıya en yakın boş yere;  sığmazsa reddedilir |
| Makinenin başında **0,50 × 0,60 m** bakım alanı | m.5.2.6.3.2.1 b | Makineye bitişik ilk boş yere;  yoksa reddedilir |
| Döşeme delikleri **amacı için en küçük** | m.5.2.6.3.3 | Halat demeti ( n halat, aralık 1,6 · dh ) + çevresine `halat_delik_payi` ( 30 mm, çizim kabulü );  regülatör halatı 200 × 200 ( LiftDesigner ) |

Delik planı delikleri **eksenlerinden** ölçer ve boyutlarını üstlerine yazar.
Kapının önü ( kapı eni × 0,70 m ) boş bırakılır.  Deliklerin kenarındaki
en az 50 mm'lik bilezik ( m.5.2.6.3.3 ) düşey bir ölçüdür, planda görünmez.
Örnek oda 3.800 × 2.600 ( hesap programının test verisi ), pano 600 × 400
( LiftDesigner ).

**Düşey kesitler** ( kuyunun derinliği boyunca;  yatay eksen plandakiyle aynı ):
kuyu dibi kesiti kabini **tam ezilmiş tamponunda**, kuyu üstü kesiti **en üst
konumunda** ( karşı ağırlık tam ezilmiş tamponunda + 0,035·v², m.5.2.5.6.1 )
gösterir.  Kabinin düşey ölçüleri ELEport kabininden ölçüldü ( iç 2.250,
tavan 60, taban 120, şase altı −480, üst kiriş −480 + paten arası, paten 140,
fren bloğu 350, kasnak merkezi −295 );  etek 750 ( m.5.4.5.1 ).

| Açıklık | Madde | En az |
|---|---|---|
| Kuyu dibi sığınma yüksekliği | m.5.2.5.8.1 · Çizelge 4 | 2,00 / 1,00 / 0,50 m |
| Kuyu tabanı – kabinin en alt kısmı | m.5.2.5.8.2 a | 0,50 m |
| Kuyu tabanı – etek | m.5.2.5.8.2 a 1 | 0,10 m |
| Kuyu tabanı – şase / paten / fren bloğu ( raya yakın ) | m.5.2.5.8.2 a 2 · Şekil 7 | 0,10 m |
| Kabin üstü sığınma yüksekliği | m.5.2.5.7.1 · Çizelge 3 | 2,00 / 1,00 m |
| Üst paten – kuyu tavanı | m.5.2.5.7.2 b | 0,10 m |
| Korkuluk – kuyu tavanı | m.5.2.5.7.2 c | 0,30 m |
| Üst paten – rayın üst ucu | m.5.2.5.6.1 | 0,10 m |

**Kuyu dibi zinciri kabinle kapanmalı:**  kaide + tampon + çarpma arası +
şase altı = kuyu dibi ( ELEport:  764 + 160 + 96 + 480 = 1.500 );  tutmazsa
reddedilir.  **Hesap programıyla fark:**  onun sığınma satırları ofisin
paylarıyla hesaplanır ( üst paten bir satırda 2.700, bir başkasında 2.900;
varsayılan girdiler şase altını örtük 350 alır ) — bu kabin modeline göre
düzeltilene kadar iki program aynı açıklığa farklı sayı verir.

## Sırada ne var

1. Tam boy kuyu düşey kesiti ( 1/50, kat kotlarıyla ) — girdisi hazır
   ( `dusey.durak_adedi` · `kat_yuksekligi` )
2. `cizim/kopru.py` — girdilerin hesap programından dolması.  Önce iki tanım
   eşitlenmeli:  ray – kapı arası hesapta kat kapısı düzleminden ( RK ),
   çizimde kuyu iç yüzünden;  kabin kaçıklığı hesapta ray ekseninden ( yc ),
   çizimde kuyu ortasından ölçülüyor.
3. Ofis şablonuna ( TİP PROJE FORMATI ) yerleştirme

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
