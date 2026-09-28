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

.venv/bin/python calistir.py                      # kuyu planı  →  cikti/ ( git'e girmez )
.venv/bin/python calistir.py --aski Doğrudan      # 1:1 askı düzeniyle
.venv/bin/python calistir.py --agirlik Arka       # karşı ağırlık arkada
.venv/bin/python calistir.py --cizim kuyu_kesiti_yan  # A-A tam boy düşey kesit ( 1/50 )
.venv/bin/python calistir.py --cizim kuyu_kesiti_on   # B-B tam boy düşey kesit ( 1/50 )
.venv/bin/python calistir.py --cizim kuyu_kesiti_on --makine "Makine dairesi"   # makine daireli
.venv/bin/python calistir.py --pafta               # bütün çizimler TİP PROJE FORMATINDA ( DXF + SVG önizleme )
.venv/bin/python -m unittest discover -s testler     # testler ( hepsi )

# Örnek tam projeler ( hesap + çizim, tek pafta ) → ornekler/ — hesap programının
# motorunu çağırır, onun .venv'iyle:
"…/AVAN HESAPLAMA PROGRAMI/.venv/bin/python" ornekler/uret.py
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
| `cizim/dusey.py` | Düşey kesitlerin yerleşimi ve açıklık denetimleri |
| `cizim/donanim.py` | Kuyu donanımının KOTLARI:  makine, şase, bağlantılar, regülatör, gergi, raylar, konsollar, karşı ağırlık |
| `cizim/kesit_parcalari.py` | Düşey kesitlerde parça çizimi ( yan ve ön bakış ortak ) |
| `cizim/kuyu_kesiti.py` | Tam boy A-A ( yan ) ve B-B ( ön ) kuyu düşey kesitleri, 1/50 ( gerekirse kırık ) |
| `cizim/cizimler.py` | Çizimlerin listesi:  doğrulama, çizici, başlık, ölçek ( calistir ve pafta ortak ) |
| `cizim/pafta.py` | Çizimleri ofisin TİP PROJE FORMATINA yerleştirir, anteti doldurur |
| `sablon/proje_formati.dxf` | Ofisin pafta şablonu ( TİP PROJE FORMATI.dwg'den;  hesap programınınkiyle aynı ) |
| `cizim/svg.py` | Elemanları SVG'ye yazar |
| `cizim/dxf.py` | **Aynı** elemanları DXF'e yazar ( ezdxf ) |
| `testler/` | 187 test ( `test_cizim.py`, `test_fiziksel_tutarlilik.py`, `test_girdi_sinirlari.py` ) |
| `ornekler/` | Yalnız iki örnek tam proje ( `.dwg` + `.pdf` ):  **makine dairesiz** ( ELEport PROJE 5 ) ve **makine daireli dişli** ( aynı asansör );  onları üreten `uret.py` ve `hesap_girdi.py` |
| `cikti/` | `calistir.py`'nin tek tek çizimleri ( git'e girmez ) |

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
   kat dışarı alınır, başka bir sıranın üstüne itilmez.  Sığmayan bir ARA
   ölçünün yazısı ortada bir parçanın ( ray, konsol, şase, tampon … —
   `PARCA_KATMANLARI` ) üstüne düşüyorsa uzatma çizgisinin hemen dışına, geniş
   komşu tarafa yazılır ( AutoCAD gibi;  kabin duvarının "75"i şase dikmesinin
   üstündeydi ).  Testler:  hiçbir iki ölçü yazısı üst üste binmez, hepsi
   çerçevenin içindedir, hiçbir çizimde ölçü yazısı bir parçanın ya da etiketin
   üstüne düşmez.  Çerçeve yazıların enini ve hizasını da kapsar.
7. **Yazı boyu SVG'de ve DXF'te aynıdır.**  Geometri yazının boyunu em
   ( font-size ) olarak verir;  DXF'te TEXT ve ölçü yazısı yüksekliği büyük harf
   yüksekliğidir ( Arial 0,716 em ) — `dxf.BUYUK_HARF` ile çarpılır.  Eskiden DXF
   yazıları 1,4 kat büyük çıkıyor, pafta ve DWG'de ayrılan yere sığmıyordu.

## Plan ve kesitte ortak donanım

Şase dikmesinin plan derinliği, yan kesitte de kullanılan
`sase_dikme_derinlik` değeridir ( örnekte 300 mm ); dikmeler ray eksenine
ortalanır. Kabin üstü korkulukları plan, düşey kesit ve açıklık kontrolünde
aynı konumları kullanır; kesit kırığı korkuluğu kesmez.

Regülatör gergisinin kasnağı, taşıyıcı kolu ve ağırlığı kuyu dibi planında
birlikte gösterilir. Kol ve ağırlığın plan kutuları düşey kesitte de
kullanılır; merdiven ve sığınma alanı bu kutuların dışında yerleştirilir.
Kolun raydaki bağlantısı bilinçlidir; ağırlığın rayla veya tamponla
çakışmasına izin verilmez.

Gergi ağırlığının merkezi kasnak merkezinden 300 mm ötededir ( ELEport regülatör
hesabı, "A = 300";  ağırlık 160 boyunda:  kasnağın 220 – 380 ötesi ).  Kesitteki
sembolden 340 ölçülmüştü;  ELEport'un 280'lik regülatör kaçıklığında ağırlık
kuyudan taşıyor, örnek 260'a çekilmişti ( arka duvara 3 mm ).  Örnek yine
ELEport'un 280'i:  `1167 + 280 + 380 = 1827`, duvara 23 mm.  Ağırlık duvarlara
en az çizimin çakışma payı ( `girdi.ASGARI_ACIKLIK`, 20 ) kadar uzak durur;
bir yönde sığmazsa kol öbür yöne döner, ikisinde de sığmazsa çizim durur.  Üst
regülatör aynı girdiyi kullanarak gergi kasnağıyla hizalı kalır.

Patenlerin MERKEZLERİ arası hesap programının paten arasıdır
( `dusey.kabin_paten_arasi` 3.300, `dusey.agirlik_paten_arasi` 2.920 ):
kabinde şasenin alt ve üst kirişine, karşı ağırlıkta çerçevenin alt ve üst
ucuna ortalı — iki çerçevenin yüksekliği de hesabın paten arasıdır.  Eskiden
paten arası şase yüksekliği gibi kullanılıp patenler onun dışına ekleniyordu
( merkezler kabinde 3.440, ağırlıkta 3.060 ), sonra ağırlıkta 1.500 aralıkla
2.920'lik çerçevenin ortasına dizilmişti.  ELEport'un kendisi de tutarsız:
hesabı ağırlıkta 1.500 alır, çiziminde patenler 2.920'lik çerçevenin
uçlarındadır;  örnek hesap girdisi çizimi izler ( 2.920 ).  Kasnağına ve
patenlerine yetmeyen çerçeve reddedilir.

Kesitte raylar, konsollar, karşı ağırlık, tamponlar ve gergi bakana
uzaklıklarına göre çizilir ( uzaktaki önce ):  A-A'da ağırlık tarafındaki kabin
rayı ve ara kiriş karşı ağırlığın önündedir ( eskiden ağırlık hep en son
çiziliyor, ray ağırlık boyunca kayboluyordu ).

Kabin altı kasnakların şaseye, kuyu tepesindeki kabin halat bağlantısı
plakasının kabin rayının başına bağlantısı ŞEMATİK çizgiyle gösterilir
( `baglantilar.py`;  plan ve kesit aynı üç boyutlu çizgilerden ):  taşıyıcının
profili, yatağı ve cıvatası girdide yok, ölçü uydurulmaz.  Makine dairesinde
kabin halat bağlantısı döşemededir, yol çizilmez.

## Bugün ne çiziliyor

**Kuyu planı** ( kabin hizasından yatay kesit ):  duvarlar ve kesit taraması,
kapı boşluğu · kasa · eşik · kanatlar · açılış oku, kabin panosu ve şasesi
( dikmeler + alt/üst kirişler ), kabin rayları T profiliyle, ray konsolları
( plaka + kol + cıvata delikleri ), patenler, karşı ağırlık çerçevesi ve
kasnağı, karşı ağırlık rayları ve konsolları, askı kasnakları ya da askı
noktaları, eksenler, 46 ölçü ve çerçeve + künye şeridi.  Kumanda panosu
kuyuda değildir:  makine dairesizde kuyunun dışındaki acil panoda, makine
dairelide makine dairesinde ( eskiden kuyu planında kaynağı belirsiz bir
"PANO" vardı;  kesitlerde yoktu, makine dairelide çift oluyordu ).

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
kabin üstü kasnağı korkuluğun yolunu kesemez;  yan korkuluk kapı operatörünün
arka yüzünden başlar ( eskiden tavanın bütün derinliğince çiziliyor, ön dikmesi
operatörün içinde duruyordu );  kabin rayı ekseni kabinin derinliği içinden
geçmelidir.
Çizilmeyenler:  şase üst kirişi ve revizyon kutusu ( tedarikçi ölçüsü yok ),
etek tahtası ( planda tavan kenarıyla çakışır ).

**Kuyu dibi planı** ( kuyu tabanından yatay kesit ):  duvarlar, raylar ve
konsollar kuyu planından;  kabin bu kesitte yoktur ve çizilmez, kat kapısı
yalnız yer göstermek için kesik çizilir.  Kuyu tabanına yük aktaran noktalar
hesap paftasının 9. bölümündeki adlarla işaretlenir ( LiftDesigner "View of
Pit" gibi, ama değeriyle ):  her rayın ve tamponun ortasına **ok**, çerçeveli
**kutuda** adı ve değeri — **FKR** bir kabin rayı · **FAR** bir ağırlık rayı ·
**Fkt** kabin tamponu · **Fat** ağırlık tamponu ( iki tamponda her birine düşen
**Fkt1** / **Fat1**, kN ).  Kutu noktanın çevresinde, kuyunun içinde, hiçbir
parçaya, yazıya, ölçüye ve başka kutuya binmeyen yere konur;  ok başka bir
kutuyu, yazıyı ya da oku kesmez ( en sıkışık nokta önce, gerekirse geri izleme;
yer yoksa kutu sığınma alanının yüzeyine binebilir ).  Perde etiketi okların
arasına kayar, sığmazsa kısalır.  Değerler `kuyu_dibi.kuvvetler`'den ( N );
girilmezse kutuda yalnız ad yazar.

| Değer | Kaynak ( hesap programı ) | Nerede |
|---|---|---|
| FKR · FAR | 9. bölüm | Her rayın altında, oklu kutuda |
| Fkt · Fat ( Fkt1 · Fat1 ) | 9. bölüm | Her tamponun altında, oklu kutuda |
| Kabin rayı Fx · Fy | 7. bölüm:  bütün yük durumlarının ( C.2.1 · C.2.2 · C.2.3 ) en büyüğü | "RAY KONSOLUNA YATAY YÜKLER" tablosu — her konsola gelir, tek noktaya değil |
| Ağırlık rayı Fx · Fy | 8. bölüm | Aynı tablo |

Tablonun altındaki ray şeması yönleri gösterir:  **Fx** ray ağzına yandan, **Fy**
ağzın doğrultusunda ( EN 81-50 m.5.10.5:  "Fx … by a guide shoe to the flange" ).
Tam proje örneği değerleri hesap motorundan okur.

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

**Makine ve şase** ( `makine.py` ):  makine ve şase üç boyutlu basit
cisimlerdir ( silindir, kutu, profil kenarı );  plan, A-A ve B-B aynı cisimlerin
izdüşümünü çizer — ekseni bakış yönündeki silindir daire, öbürü dikdörtgen;
kesit düzleminin gerisi çizilmez, bakana yakın olan öne gelir.  Tip girdiden
( `makine.tip`:  Dişlisiz / Dişli — hesap programının "Makine tipi" ).
Ölçüler ofisin LiftDesigner projelerinden ( kullanıcı kararı ):

| Tip | Kaynak | Parçalar |
|---|---|---|
| Dişlisiz | 4815-6 ( MRL ) | kasnak ekseni üstünde:  kasnak · göbek ø100 × 15 · flanş ø220 × 28 · yatak flanşı ø320 × 50 · gövde ø400 × 206 · fren ø320 × 70 · fren diski ø240 × 18 · enkoder ø270 × 102 ( toplam 489 ) + klemens kutusu.  Biçim bu;  ölçü projenin makine ZARFINA oranlanır ( ELEport'un makinesi ø298 × 279 ve kotları ölçülü ) |
| Dişli | 12744-3 A 160 ( makine daireli ) | sonsuz vidalı:  motor ekseni kasnak eksenine dik — el çarkı, motor ø300 + klemens, motor flanşı, fren ve fren kasnağı ø260, dişli kutusu 320 × 260 × 422, vida yuvası, arka yatak, taban;  kasnak dişli kutusunun yanında, dış yataklı.  Zarf 1.316 × 590 × 600, kasnak ekseni tabanın 195 üstünde |

Makine dairesizde yalnız dişlisiz çizilir ( dişli makine kuyu tepesindeki
şaseye sığmaz ).  Dişli makinenin yönü ( dişli kutusu kasnağın hangi yanında,
motor hangi yöne ) bağlantılara ve regülatöre binmeyen, odaya sığan ilk düzendir.

Şase HESAP PROGRAMININ bölüm 2'sindeki yapıdır ( "Makine konstrüksiyonu" );
profiller ve ölçüler onun girdileri, adları da aynı — pafta ile hesap aynı
şeyi söyler.  Profiller NPU ( UPN ), DIN 1026-1 ölçüleriyle ( `makine.NPU`,
anahtarları hesap programının NPU listesi ).

| Şase | Nerede | Girdi | Ne |
|---|---|---|---|
| 2 yan yatak | kuyu üstü | `makine.yan_yatak` ( ELEport:  UPN 200, Wx 191 cm³ ) | karşı ağırlık rayları boyunca, sırtları dışta, raylara oturur ( mesnet aralığı raylar arası — hesabın L'si;  ELEport 850 );  aralarında üstle aynı hizada 700 mm motor plakası, uçlarda bağlantı levhaları.  Plakadan inen halatlar ( karşı ağırlık tarafı ve bağlantısı ) için plakada delik ( eskiden deliksiz plakanın içinden geçiyorlardı ).  Şase üstü ELEport'unki ( tavandan 595 ), altı profil yüksekliği kadar aşağıda |
| Kaide | makine dairesi ( HER ZAMAN — hesap burada kolonların burkulmasını da denetler ) | `makine_dairesi.sase_yuksekligi` · `dikine_kiris` · `yan_yatak_boyu`, `makine.yan_yatak` | dört dikine kiriş ( kolon ) döşemeden şase yüksekliği kadar, üstleri hizasında iki yan yatak makinenin uzun ekseni boyunca;  dikine kirişlerin eksenleri arası = yan yatak boyu ( L ).  Uçlarda kısa kirişler UPN 100 ve ayak plakaları 150 × 150 × 20 ( LiftDesigner 12744-3 ).  Makine yan yatakların arasındaki, üstleri hizasındaki **makine plakasına** oturur ( yük iki yan yatağa — hesabın F / 2'si;  eskiden plaka yoktu, makine iki kirişin arasında havada duruyordu );  plakayı kesen halatlar için delik, eğik saptırma halatı için kestiği yerde delik, plakanın altına sarkan tahrik kasnağı için yuva;  saptırma kasnağının askıları plakaya asılır.  Enine makinenin ( ve saptırma kasnağının ) izinden her yana 100.  Ayak plakası bir döşeme deliğine basıyorsa kaide önce uzun ekseninde kayar ( 25'er ), kayacak yer yoksa enine büyür ( 200, 300 ).  Makine kaideye sığmıyorsa ( izi > L + dikine kiriş ) çizilmez, yan yatak boyunu büyütmesi söylenir |

**Saptırma kasnağı** ( makine dairesi ):  karşı ağırlık halatı tahrik
kasnağının öbür teğetinden daha dışarıda inmeliyse ( halat aralığı kasnak
çapından büyük ) saptırma kasnağı onu ağırlık kasnağının teğetine indirir —
çerçevenin içinde, döşemenin 400 üstünde ( LiftDesigner ), döşemedeki bir
bağlantının üstüne düşerse 50 mm açık kalacak kadar yukarıda;  çapı girdiden
( `makine.saptirma_kasnak_capi`, hesap programında "Saptırma kasnağı çapı" ).
İçeride inmesi gerekiyorsa saptırma kasnağıyla çözülmez, reddedilir.
**Sarım açısı** iki kasnağın ortak dış teğetinden hesaplanır ve B-B'de
yazılır ( saptırmasız 180° );  LiftDesigner 12744-3'ün kendi ölçüleriyle
( ø540 · ø480 · 560 yana · 842 aşağı ) 148° — paftasındaki "Sarim acisi 148".

**Makine dairesi planı** ve **kuyu üstü döşeme halat delik planı** ( makine
daireli asansör ):  makinenin, halatların, bağlantıların ve regülatörün yeri
kuyu üstü planıyla AYNIDIR ( `kuyu_ustu.yerlesim(…, acil_pano=False)` ) —
halatlar aynı noktalardan iner, bu kez döşeme deliklerinden geçer.

| Kural | Madde | Ne yapılır |
|---|---|---|
| Kapı en az **0,60 m** | m.5.2.3.2 a | Altı reddedilir |
| Kumanda panosunun önünde **0,70 m** derin, **en az 0,50 m** ya da pano eni | m.5.2.6.3.2.1 a | Pano seçilen duvar boyunca kapıya en yakın boş yere;  sığmazsa reddedilir |
| Makinenin başında **0,50 × 0,60 m** bakım alanı | m.5.2.6.3.2.1 b | Makineye bitişik ilk boş yere;  yoksa reddedilir |
| Döşeme delikleri **amacı için en küçük** | m.5.2.6.3.3 | Halat demeti ( n halat, aralık 1,6 · dh ) + çevresine `halat_delik_payi` ( 30 mm, çizim kabulü );  regülatör halatı da aynı kuralla:  `kuyu_dibi.regulator_halat_capi` + 2 × pay ( ELEport ø6 → 66 × 66;  eskiden LiftDesigner'ın 200 × 200'ü — ø240 regülatörde iki delik arasında 40 mm, duvara 14 mm kalıyordu ) |

Delik planı delikleri **eksenlerinden** ölçer ve boyutlarını üstlerine yazar.
Kapının önü ( kapı eni × 0,70 m ) boş bırakılır.  Deliklerin kenarındaki
en az 50 mm'lik bilezik ( m.5.2.6.3.3 ) düşey bir ölçüdür, planda görünmez.
Örnek oda 3.800 × 2.600 ( hesap programının test verisi ), pano 600 × 400
( LiftDesigner ).

**Düşey açıklıklar** ( `dusey.py` ):  kuyu dibinde kabin **tam ezilmiş
tamponunda**, kuyu üstünde **en üst konumunda** ( karşı ağırlık tam ezilmiş
tamponunda + 0,035·v², m.5.2.5.6.1 Çizelge 2 ) denetlenir.  Kuyu dibi ve kuyu
üstü ayrıca düşey detay kesitle ÇİZİLMEZ:  ofisin paftalarında ( 477-8,
12744-3 ) ikisi de yatay kesittir ( kuyu dibi planı E-E, kuyu üstü / makine
dairesi planı F-F ).  Kabinin düşey ölçüleri ELEport kabininden ölçüldü ( iç 2.250,
tavan 60, taban 120, şase altı −480, üst kiriş −480 + paten arası, paten 140
( kirişlere ortalı ),
fren bloğu 350, kasnak merkezi −295 );  etek 750 ( m.5.4.5.1 ).

| Açıklık | Madde | En az |
|---|---|---|
| Kuyu dibi sığınma yüksekliği | m.5.2.5.8.1 · Çizelge 4 | 2,00 / 1,00 / 0,50 m |
| Kuyu tabanı – kabinin en alt kısmı | m.5.2.5.8.2 a | 0,50 m |
| Kuyu tabanı – etek | m.5.2.5.8.2 a 1 | 0,10 m |
| Kuyu tabanı – şase / paten / fren bloğu ( raya yakın ) | m.5.2.5.8.2 a 2 · Şekil 7 | 0,10 m |
| Kabin üstü sığınma yüksekliği | m.5.2.5.7.1 · Çizelge 3 | 2,00 / 1,00 m |
| Üst paten – 0,40 m yakınındaki tavan parçası | m.5.2.5.7.2 b | 0,10 m |
| Korkuluk – kabin izdüşümündeki tavan parçası | m.5.2.5.7.2 c 1 | 0,30 m |
| Korkuluk – korkuluğun dışındaki tavan parçası | m.5.2.5.7.2 c 1 | 0,10 m |
| Kabin üst pateni – rayın üst ucu ( kabin en üstte ) | m.5.2.5.6.2 | 0,10 m |
| Karşı ağırlık üst pateni – rayın üst ucu ( ağırlık en üstte ) | m.5.2.5.6.2 | 0,10 m |

**"Kuyu tavanının en alt kısmı" tavanın altındaki parçaları da kapsar**
( m.5.2.5.7.2 ):  makine dairesizde makine şasesi, kabin ve ağırlık halat
bağlantıları, regülatör.  Her açıklık kendi üstündeki en alçak parçaya
ölçülür ( `donanim.tavan_engeli` );  örnekte paten ve korkuluk şaseye,
sığınma kuyu tavanına gider.  Karşı ağırlık en üst konumunda ( kabin tam
ezilmiş tamponunda + 0,035·v² ) makine şasesine çarpıyorsa çizim durur.

**Kuyu dibi zinciri kabinle kapanmalı:**  kaide + tampon + çarpma arası +
şase altı = kuyu dibi ( ELEport:  764 + 160 + 96 + 480 = 1.500 );  tutmazsa
reddedilir.  **Hesap programıyla fark:**  onun sığınma satırları ofisin
paylarıyla hesaplanır ( üst paten bir satırda 2.700, bir başkasında 2.900;
varsayılan girdiler şase altını örtük 350 alır ) — bu kabin modeline göre
düzeltilene kadar iki program aynı açıklığa farklı sayı verir.

**Tam boy kuyu düşey kesitleri** ( 1/50, `kuyu_kesiti.py` ):  LiftDesigner'ın
"Dikey 1:50"si gibi gerçek ölçekte, bütün duraklarla ( ELEport ara katları
kırarak 1/30 çizer ).  İki kesit, planda A-A ve B-B işaretleriyle:

| Kesit | Bakış | Kabin | Karşı ağırlık |
|---|---|---|---|
| A-A yan | kuyu derinliği boyunca, kabin ekseninden karşı ağırlığa;  kat kapıları solda | en alt durakta | seyir kadar yukarıda |
| B-B ön | kuyunun arkasından kat kapılarına ( plandaki sol sağda görünür ) | en üst durakta | tamponunun çarpma arası üstünde |

**Planların seviyeleri** ( LiftDesigner'ın X-X · Y-Y · Z-Z'si gibi ):  her iki
kesitte kesik çizgi, uçlarında ▽ ve harf;  plan başlıkları aynı harfi taşır
( "KUYU PLANI  C-C" ).  A ve B düşey kesitlerindir.  Çok yakın iki seviyeden
alttakinin işareti dışarı kayar.

| Harf | Plan | Hangi yükseklikten |
|---|---|---|
| C | kuyu planı | en alt durakta kapının orta yüksekliği |
| D | kabin üstü planı | kesitteki kabinin tavanı |
| E | kuyu dibi planı | en alt duraktaki kabinin en alt noktasıyla ilk konsolun üstü arasının ortası — kabin bu planda yoktur ve çizilmez |
| F | kuyu üstü planı / makine dairesi planı | tahrik kasnağının ekseni |
| G | döşeme halat delik planı ( makine daireli ) | makine dairesi döşemesinin ortası |

**Kesit düzleminin gerisi çizilmez:**  A-A karşı ağırlık tarafını gösterir
( makine, şase, ağırlık bağlantısı, ağırlık rayları ve o yandaki kabin rayı );
öbür yandaki regülatör, kabin halat bağlantısı, gergi ve kabin rayı B-B'de
görünür ( ELEport da iki yan kesitte ayrı gösterir ).  B-B kabinin arkasından
bakar;  makine dairesinin arka yarısındaki pano görünmez.

İkisinde de:  kuyu duvarları, kuyu dibi ve tavan döşemesi, kat döşemeleri
( 150 ), kat kapıları ( yanda kasa · eşik · kanatlar;  önde kasa · boşluk ·
durak numarası ), ▽ kotlar ve durak adları;  kabin ve karşı ağırlık
raylarının tamamı üst uçlarıyla, **konsolları** ( tabandan 500, sonra
`dusey.kabin_konsol_arasi` / `agirlik_konsol_arasi` — hesap programının
"konsollar arası" girdileri ) ve **ek yerleri** ( 5.000'de bir );  kabin
( şase, patenler, fren blokları, 2:1 kasnakları );  karşı ağırlık ( çerçeve =
ağırlık paten arası, kasnak, patenler );  kuyu tepesinde **makine şasesi, makine, tahrik
kasnağı, halat bağlantıları, hız regülatörü**;  kuyu dibinde tamponlar ve
**gergi düzeni**;  **askı halatları** ( 2:1:  kabin kasnaklarından tahrik
kasnağına ve bağlantıya, tahrik kasnağından ağırlık kasnağına ) ve
**regülatör halatı**.  Kasnaklar dönme düzlemine göre bir kesitte daire,
öbüründe dikdörtgen görünür;  halatlar dairelere teğettir ( test ).

Ölçüler:  solda kuyu dibi + kat yükseklikleri + son kat zinciri, seyir, kuyu
yüksekliği ( ELEport:  1.500 + 29.000 + 5.000 = 35.500 );  sağda konsol
zinciri tabandan tavana ( ilk konsol, konsollar arası, ray ucu ), A-A'da
makine ( şase = yan yatak 200 · makine 345 · tepe 250 ), B-B'de karşı ağırlık ( çarpma
arası, çerçeve );  altta kuyu derinliği / genişliği.

Kuyu tepesi ve karşı ağırlığın kotları ELEport kesitlerinin vektörlerinden
ölçüldü ( `sabitler.py`, "KUYU ÜSTÜ DONANIMININ DÜŞEY ÖLÇÜLERİ" );  planda
aynı parçaların yeri kuyu_ustu.yerlesim'dekiyle birebir tuttu.  Makinenin
yeri `makine.yeri` ( "Kuyu üstü" / "Makine dairesi" ).

Kuyu tavanının en alt kısmı ( hesap programının "kuyu tavanı payı", 150:
kirişler vb. ) bir KABULDÜR:  kesitte kesik bir sınır çizgisi olarak çizilir
( eskiden taralı bir beton katman gibi çiziliyor, tavan iki kat kalın
görünüyordu ).  Raylar ona değmez:  şasede bitmeyen raylar bu çizginin
`kabin_rayi_tepe` ( 50, ELEport'ta tavanın 50 altı ) altında biter — eskiden
uzak kabin rayı ( makine dairelide bütün raylar ) çizgiye tam değiyordu.

**Makine daireli projede** oda kuyunun üstündedir ( plan yeri
`makine_dairesi.x · y · genislik · derinlik` ).  Odanın döşemesi hesap
programının **tabliyesidir**:  `tabliye_yuksekligi` ( "Tabliye beton
yüksekliği" — kuyu tavanından oda döşemesinin üstüne;  kesitte "TABLİYE" ).
Öbür girdiler:  `yukseklik` ( temiz;  LiftDesigner "477-8" 3.500 ),
`kapi_yukseklik` ( standardın en azı 2.000 );  çatı 150 ( LiftDesigner,
`md_cati_kalinlik` ).  Makine kaidede ( yukarıdaki tablo;  kesitte "ŞASE" ),
halat bağlantıları ve regülatör döşemede,
kumanda panosu 2.000 yüksek ( LiftDesigner ), halatlar döşeme deliklerinden
iner ( kesik ).  Kesilen oda duvarında kapı kesitteyse boşluk, karşı duvarda
ise görünüş olarak çizilir.  Denetimler:

| Kural | Madde | Sınır |
|---|---|---|
| Makine dairesinin temiz yüksekliği | m.5.2.6.3.2.1 | ≥ 2,10 m |
| Tahrik kasnağının üstünde boşluk | m.5.2.6.3.2.3 | ≥ 0,30 m |
| Makine dairesi kapısının yüksekliği | m.5.2.3.2 a | ≥ 2,0 m |

`kat_yuksekligi` tek sayı ya da alttan üste `durak_adedi − 1` sayılık liste
( LiftDesigner örneği 3.400, 3.400, 3.000 … ).  Ardışık iki eşik arası 11 m'yi
aşarsa çizim durur ( m.5.2.3.1:  ara acil kapı gerekir, bu çizim çizmez );
kat yüksekliği kat kapısından büyük olmalı.

Yazılar, oklar, kalem kalınlıkları ve tarama 1/20'ye göre tanımlıdır;  başka
ölçekte `olcek / 20` ile büyür, paftada aynı boyda kalır.

## Kapı bölgesi ( kat kapısı · eşikler · kabin kapısı )

Ölçüler ELEport'un kuyu planı vektörlerinden ve "Door Detail 1/35" paftasından:
kat kapısı ünitesi kasa 60 + eşik 90;  kanatlar 40 kalın ve **EŞİĞİN ÜSTÜNDE**
( teleskopikte iki düzlem, 45 arayla );  kabin eşiği 90, kabin kapısı
kanatları onun üstünde.  `kapi.montaj`:

| Montaj | Kasa | Kat eşiği | Kapı hattı | m.5.2.5.3.1'in "kuyu iç yüzü" |
|---|---|---|---|---|
| Duvar boşluğuna | −60 – 0 ( duvarda ) | 0 – 90 | 90 | duvar |
| Kuyu içine ( ELEport ) | 0 – 60 | 60 – 150 | 150 | kapı hattı ( kapı altı / üstü sac kaplama ) |

Açıklıklar kabin EŞİĞİNİN ön kenarından ölçülür:  eşik aralığı 0 – 35 mm
( m.5.3.4.1 ), kuyu yüzü – kabin eşiği ≤ 150 ( m.5.2.5.3.1 ).  `kabin_ray.kapi_arasi`
kuyunun ön İÇ yüzünden ölçülür — hesap programının RK'sı kapı hattındandır
( ELEport:  iç yüzden 1.167 = kapı hattından 1.017 ).

Kapının olduğu duvar boşluğun iki yanında iki parçadır, tarama boşluktan
geçmez:  kuyu planında ( C-C, kapı hizası ) ön duvar kapı boşluğunda ( duvar
boşluğuna montajda kasayla birlikte ), A-A'da kapı ünitesi duvardaysa boşluk
eşiğin altından başlar, makine dairesi planında oda kapısında.  Kapının üstünden
ya da altından kesilen planlarda ( kabin üstü, kuyu dibi, kuyu üstü, delik
planı ) ön duvar kesintisizdir ( `geometri.plan(…, kapi_duzeyi=False)` ).

( Eskiden kanatlar eşiğin arkasına, kabin eşiğinin ve kabinin içine düşüyordu;
örnek girdi ELEport'un 1017'sini iç yüzden okuyup arka duvarı 150 mm geride
bırakıyordu.  Duvar taraması da kapı boşluklarından geçiyordu — önizleme
taramayı seyrek çizdiği için görünmüyordu, DWG'de vardı.  Hepsi düzeltildi. )

## Tam proje ( hesap + çizim, tek pafta )

`ornekler/uret.py` gerçek bir projenin ( ELEport PROJE 5 · Elevator 3 )
girdileriyle hesap programının MOTORUNU çağırır ( program değiştirilmez ),
kapak ve hesap paftalarını hesap programının kendi dışa aktarımıyla şablona
dizer, çizimleri `pafta.birlestir` ile son hesap sayfasının sağına ekler.  İki
örnek üretir, her biri `.dwg` ( AutoCAD çekirdeğinde AUDIT'ten geçirilip
kaydedilir ) + `.pdf` ( paftanın görüntüsü );  git'e girmezler:

| Örnek | Ne |
|---|---|
| ELEport PROJE 5 - Makine Dairesiz | ELEport'un kendisi:  dişlisiz, kuyu üstünde |
| ELEport PROJE 5 - Makine Daireli Dişli | aynı asansör ( kuyu, kabin, raylar, halatlar, tamponlar ), makine kuyunun üstündeki odada, dişli ( ELEport'ta yok ).  Değişen girdiler ve kaynakları `hesap_girdi.ASANSOR_MD`'de:  Gm 350 ( ofisin 12744-3 hesabı, A 160 ), verim ofisin dişli sabiti 0,50 → gereken 12,75 kW, motor bir üstteki IEC gücü 15 kW;  tabliye ve kaide hesap programının varsayılanları ( 1.200 · 1.100 · NPU 120 · NPU 140 · 1.400 ), oda 3.800 × 2.600.  Tst ELEport makinesinin 3.400'ü ( A 160'ın katalog değeri elde yok ) |

Çizim girdisi hesap girdisinden kurulur ve betik tutarlılığı DENETLER:  makine
tipi, yeri, tahrik kasnağı, yan yatak aynı;  makine dairesinde tabliye, kaide ve
oda ölçüleri aynı;  kuyu üstünde yan yatak boyu ( L ) karşı ağırlık rayları
arasına eşit;  çizimin halat geometrisinden çıkan sarım açısı hesabın α'sına
eşit;  tampon adetleri aynı.  Birisi tutmazsa proje üretilmez.

Makine dairesiz tesiste makine şasesi raylara oturur ( ELEport "Motor Bedplate
Calculation" ):  hesap girdisinde "Makine yükünün yolu = Kılavuz raylara" ve
makine ağırlığı 250 kg ( ELEport motoru ).  Hesap programı bir raya
( Gm + Tst ) / 4 = 4.490 N yükler ( m.5.7.2.3.7 );  ELEport aynı yere kendi
kabulüyle 800 kg ( ray hesabında 1.000 kg ) koyar.  **Hesap programının
modelinde olmayanlar** ( çizim işi bitince ele alınacak ):  şasenin kendi
ağırlığı ( ELEport 150 kg ) ve şaseye bağlı halat bağlantısının yükü ( ELEport
M3 = 686 kg ).

## Pafta ( TİP PROJE FORMATI )

`pafta.py` ofisin şablonunu okur ( 3.242 × 600 mm:  solda notlar ve antet,
sağda serbest alan ) ve çizimleri gerçek ölçüde BLOK olarak tanımlayıp
paftaya 1/ölçek ile yerleştirir — CAD'de blok açılınca ölçüler gerçek boyda.
Sıra ofisin 477-8 projesindeki gibi:  düşey kesitler ( 1/50 ), sonra planlar
( 1/20 ), konu sırasıyla sütun sütun;  alan yetmezse
çerçeve SAĞA uzar ( hesap programı gibi ).

Önizleme ( pafta PDF'i ) ezdxf'in çizicisiyle DXF'ten çizilir.  ezdxf 1.4
ölçekli bloğun içindeki taramanın desenini ölçeklemiyordu ( 1/50 kesitte
duvarda tek çizgi );  önizleme bir kopyada taramaları bloklardan çıkarıp
desenlerini yeniden kurar — DXF'e dokunulmaz, AutoCAD deseni zaten doğru
ölçekler.  Önizleme Pillow ister ( `requirements.txt` ).

**Kırık kesit:**  1/50 düşey kesit 600 mm'lik paftaya sığmazsa ara katlar
kırılır ( ELEport ve LiftDesigner gibi ):  alttan ve üstten SIĞAN EN ÇOK
durak kalır, kırık kabine ve karşı ağırlığa değmez;  kırığı geçen ölçüler
gerçek değerini yazar ( "5 × 3000", "SEYİR 21000" ).

**Antet:**  çizimin bildiği değerler yazılır ( hız, durak, seyir, kabin,
askı, ray, ölçek );  bilmedikleri ( taşıma kapasitesi, sınıf, motor gücü )
BOŞ kalır — şablonun örnek değerleri projeyi yanlış tanıtırdı.  Şablon
değişirse ( çerçeve, kapak hücresi, antet hücreleri ) pafta üretilmez.

**AutoCAD ile doğrulandı:**  AutoCAD 2027'nin AcCoreConsole'unda açılıp
REGENALL, AUDIT ( 0 hata ) ve DWG kaydı.  Şablonun dört katmanı olmayan
malzeme / çizim stili kayıtlarını gösteriyordu ( AUDIT 16 hata );  pafta
bunları onarır.  Kesik ve eksen çizgilerine ölçek × 2,5 çizgi tipi ölçeği
verilir — yoksa desen paftada 0,1 mm'ye iner, çizgi düz görünürdü.

## Sırada ne var

1. `cizim/kopru.py` — girdilerin hesap programından dolması.  Önce iki tanım
   eşitlenmeli:  ray – kapı arası hesapta kat kapısı düzleminden ( RK ),
   çizimde kuyu iç yüzünden;  kabin kaçıklığı hesapta ray ekseninden ( yc ),
   çizimde kuyu ortasından ölçülüyor.
2. Hesap paftalarıyla çizimlerin aynı şeritte birleşmesi ( köprüyle )

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
