# ASANSÖR PROJE PROGRAMI  ( HESAP + ÇİZİM )

Asansörün **uygulama projesini** tek girdiden üretir:  hesap ( mukavemet,
elektrik, topraklama ) ve kuyunun **proje çizimleri** ( düşey kesitler ve
planlar ) aynı paftada.  Çizimler ekranda **SVG**, paftada **DXF / DWG** olur.

İki parça:

- `hesap/` — hesap programının ( `AVAN HESAPLAMA PROGRAMI` ) **kopyası**.
  Orijinaline dokunulmaz;  kopyanın farkları yalnız bağlantı noktalarıdır
  ( aşağıda ).
- `cizim/` — çizim modülü.  Hesap programından bağımsız da çalışır
  ( `calistir.py`, deneme girdisi `cizim/girdi.ORNEK` ).

## Hesap ile çizimin bağlantısı

**Tek girdi, tek şema.**  Ekrandaki form hem hesabı hem çizimi besler.  Bütün
girdiler **tasarım şemasında** ( `tasarim/alanlar.py` ) tasarım sırasıyla bir kez
tanımlıdır:  etiketi, birimi, seçenekleri, varsayılanı, formdaki grubu, doğrulama
bayrakları ve **kaynağı** — GİRDİ ( tasarım kararı ), KURAL ( boşsa yerleşim
kuralından ), KATALOG ( ürün / imalatçı verisi ), ÇİZİM ( yerleşimden ölçülür ),
HESAP ( hesabın kendi türettiği ).  Hesap motorunun, elektrik hesaplarının ve
köprünün alan listeleri, formun grupları, "Gelişmiş" alanları, ⓘ metinleri ve
sayı sözlüğü ( `tasarim/sozluk.py` ) bu şemadan türetilir ( `tasarim/gorunum.py` ).

Form gruplarının sırası tasarımın sırasıdır:  **Asansör ve düzen** ( yük, hız,
makine yeri, askı oranı, askı kasnaklarının yeri, karşı ağırlığın yeri ) →
Kuyu ve katlar → Kabin ve kapı → Raylar ve patenler → Karşı ağırlık → Askı ve
halatlar → Makine → Makine dairesi → Tamponlar → Hız regülatörü → Elektrik ve
topraklama.  Makine dairesizde 1:1 askı seçilemez ( çizim 2:1 çizer ).

**Farklı kat yükseklikleri.** Kuyu ve katlar grubundaki isteğe bağlı
"Kat yükseklikleri" alanına en alt duraktan başlayarak aralıklar mm cinsinden
girilebilir: `3400; 3000; 3200`. Aralık sayısı durak adedinden bir eksik,
toplamı seyir mesafesiyle aynı olmalıdır. Boş bırakılırsa mevcut eşit kat
dağılımı kullanılır. Kesitlerin kapı ve döşeme kotları bu aralıklardan çıkar.
Kapı yüksekliği, üst payı ve duvar boşluğuna montajdaki eşik alt payı
ardışık kapı boşlukları arasına sığmıyorsa çizim reddedilir. Kabin ve karşı
ağırlık tamponlarının ezilme miktarı kendi boylarını aşamaz. SVG önizlemesi
gizli çizgi ve dairelerde de katmanın kesikli desenini kullanır.

**Formda sorulmayanlar.**  Çizimin tek çizebildiği değerler ( iki kabin ve iki
ağırlık rayı;  kabin iki rayın, askı kabinin ortasında — yc = ys = 0 ) ve
çizimden gelenler ( saptırma kasnaklarının çapı D2 · Ds, kabin tamponu kaidesi )
formda yoktur;  eski bir proje dosyasında yazılı olsalar da okunmazlar.  Hesap
motoru onları hâlâ bekler ( doğrudan çağrıda verilebilir, çizim o zaman
uyuşmazlığı söyler ).  Kuyu tabanına ve ray konsollarına gelen kuvvetler
hesabın **sonucundan** çizime yazılır.

**Çizimden gelen hesap girdileri** ( `kopru.CIZIMDEN`;  askı kaçıklığı ve sarılma
açısı formda sorulur, boşsa çizimden — ekranda kutunun içinde gri yazar ):

| Hesap girdisi | Çizimden |
|---|---|
| Askı noktasının x kaçıklığı ( xs ) | Kabin altı / kabin üstü 2:1, ağırlık yanda:  halatlar karşı ağırlık kasnağının kabine yakın teğetinden düşey iner ( referans proje:  −250 ).  1:1:  0 ( bağlantı ray eksenindeki üst kirişte ) |
| D2 · Ds ( saptırma kasnakları ortalaması · en küçüğü ) | Çizilen kasnaklar:  iki kabin kasnağı, ağırlık kasnağı, makine dairesinde saptırma kasnağı.  Hiç kasnak yoksa ( 1:1, saptırmasız ) tahrik kasnağının çapı — hesapta etkisiz ( Kp = 1 ).  Ds boşsa D2 girilmiş olsa da çizimden ( hesabın kendi kuralı Ds'yi D2'ye, yani ortalamaya düşürürdü — 240'lık kasnağın D/d'si 294 ile ölçülürdü );  girilen D2 en küçük kasnaktan da küçükse türetilmez, çizim D2'nin uyuşmadığını söyler |
| Kabin tamponu kaidesi | Kuyu dibi zinciri:  kuyu dibi − tampon − çarpma arası − kabinin şase altı ( 480 ) |
| Sarılma açısı α | Yalnız açı sabitse:  tahrik kasnağının iki inişi düşey ( 180° ) ya da makine dairesinde saptırma kasnağı ( ortak teğetler — makine daireli 1:1 örnekte 134,3° ).  Makine dairesizde ağırlık tarafındaki iniş kasnağın düzleminde eğikse ( kuyu üstü planında HALAT SAPMASI ) açı ağırlığın konumuyla değişir — ağırlık tepedeyken halat kısa, sapma birkaç derece tutar;  hesabın tek açısı buradan seçilemez ( çekiş ve kayma denetimleri açıya ters yönde bağlıdır, hesap programının α kuralının sebebi ) ve türetilmez.  Çift sarımda ( çizim tek sarım çizer ) ya da çizim kurulamıyorsa da türetilmez:  girilmezse tahrik kontrolleri HESAP EKSİK |

**Yerleşimin ölçü listesi** ( `cizim/olculer.py` ).  Çizim de girdilerden
kurulur;  "çizimden" demek girdi değil, girdilerin yerleşimde ortaya çıkardığı
ölçü demektir.  Hesap aşağıdaki büyüklükleri eskiden kendi kaba formülleriyle
tahmin ediyordu ve aynı girdiden çizimle iki ayrı sayı çıkıyordu;  artık
program hesabı onları çizimin kurduğu yerleşimden okur ( `girdi.yerlesim_olculeri`,
raporda kaynak **ÇİZİMDEN** ).  Formda kutuları yoktur.  Çizim kurulamazsa hesap
eski yaklaşığıyla sürer ve raporda KABUL yazar;  hesap motoru doğrudan
çağrılınca ( hesap programının kendi referans testleri ) bu adım yoktur.

| Ölçü | Eski tahmin | Çizimden |
|---|---|---|
| Kabin merkezi – kabin ray ekseni ( xc ) | derinlik / 2 + 130 − RK ( varsayılanda 155 ) | ön yüz + derinlik / 2 − ray ekseni ( 145 ) |
| Eşik kuvvetinin noktası ( xi ) | − RK ( kapı çizgisi, −650 ) | eşiğin ortası, m.5.7.2.3.6 ( −575 ) |
| Kabin · ağırlık ray boyu | seyir + son kat − 200 + kuyu dibi − 300 ( 5 Eki'ye kadar + tabliye ) | en uzun çizilen ray:  kuyu tabanından tavanın 200 altına |
| Askı halatı boyu ( lh ) | kuyu boyu − yığın + 5 m | halatın çizilen yolu, kabin en alt durakta ( 2:1'de kabin kasnaklarının altından tavandaki bağlantıya ) |
| Regülatör halatı boyu | ( alt duraktan tavana − 200 ) × 2 ( 5 Eki'ye kadar + tabliye ) | regülatör – gergi kasnağı arası iki kez + iki yarım sarım |
| Nps · Npr ( Ek E ) | askı oranından | çizilen kasnaklar ( makine dairesinde saptırma kasnağı dahil );  Npr 0 |
| Atalete giren kasnaklar | ofis:  kabin 2 · ağırlık 1;  saptırma kasnağı 0 | çizilen kasnaklar;  makine dairesindeki sabit saptırma kasnağı koşul II'ye mDP = J / R² · r² ( m.5.11.2.2 ) |
| Makine kirişinin açıklığı ( L, yan yatak boyu ) | girdi ( varsayılan 1.400 ) | makine dairesinde kaidenin dikine kirişleri arası ( aşağıda "Makine kaidesi" );  makine dairesizde karşı ağırlık rayları arası ( DBGW ).  Formda kutusu yok;  çizimden gelmezse bölüm 2 HESAP EKSİK |
| Makinenin kirişteki yeri ( X ) | L − 335 | tahrik kasnağının aynı kirişte mesnede uzaklığı |

**Makine kaidesi** ( 29 Eyl, kullanıcı kararı;  kaynaklar:  S. Tavaslıoğlu
"Asansörde karkas imalatları", LiftDesigner örnek projeleri, ofisin Excel
hesabı ).  Kaide makinenin ve saptırma kasnağının izini her yana 100 sarar;
halatların ( tahrik ve saptırma kasnağından inenler ) ortası kaidenin
ortasıdır — enine eksende her zaman ( iki yan yatağa eşit yük:  hesabın
F1 = F / 2'si ), uzun eksende oda, döşeme delikleri, kumanda panosunun
çalışma alanı ve makinenin başındaki bakım alanı yer verdiği kadar ( dişli
makinede motor kasnaktan uzağa uzanır;  tam ortalı kaide 2,8 m olup panonun
önünü kapatıyordu ).  Açıklık L ve kasnağın yeri X buradan:  dişlisiz 2:1'de
kasnak açıklığın ortasında ve açıklık kısa ( varsayılanda L 773 ), dişli
örnekte X = 360 ( ofisin eski "L − 335" kuralı ve LiftDesigner 800 KG'nin
355'i gibi ).  Kolonların burkulmasında en yüklü kolon alınır:
σb = max( FA ; FB ) · ω / A ( X = L − 335'te yük hep B'ye yakındı ).

**Karar 3:**  makine dairesizde "Makine yükünün yolu" varsayılanı "Kılavuz
raylara";  "Bina yapısına" ( duvardan duvara kiriş ) henüz çizilmiyor —
çizim durur, bölüm 2 HESAP EKSİK.

**Kurma ile denetim ayrıdır.**  Çizimin denetim hataları ( çakışma, sığınma
alanı … ) ölçüleri durdurmaz;  yalnız geometri kurulamazsa ( girdi eksik, kaide
makineye sığmıyor, ağırlık halatının yolu çözülmüyor ) ilgili ölçü verilmez.
Ağırlık halatı tahrik kasnağının öbür teğetinden içeride inmeliyse ( ya da
saptırma kasnağının çapı yoksa ) sarılma açısı ve kasnak sayıları çizimden
alınmaz.

**Sığınma alanları ve açıklıklar ( hesabın bölüm 11'i ) çizimden ölçülür.**
Kabin ve karşı ağırlık uç konumlarındayken parçaların gerçek kotları ve
plandaki yerleri kullanılır ( `cizim/dusey.py` ):  kuyu tavanının en alt kısmı
sığınma alanının, patenlerin, korkuluğun tam üstündeki parçadır ( makine
şasesi, halat bağlantısı, regülatör ).  Paftadaki tablo ile kesitteki ölçü aynı
sayıdır.  Eskiden hesap ofis paylarıyla ayrı bir model kuruyordu ( kabin gövdesi
2.400, üst paten bir satırda 2.700, bir başkasında 2.900;  girilen paten arası
kullanılmıyordu ) ve hesabın varsayılan asansöründe çizim üst patenin kuyu
tavanına 150 mm girdiğini bulurken hesap "uygun" diyordu.  Çizim kurulamıyorsa
bölüm 11 **HESAP EKSİK** der ve sebebini yazar.

**Tek katalog** ( karar 12 ).  Çizimin bütün ürün ölçüleri — konsollar, paten,
kabin ( düşey ölçüleri dahil ), kabin kasnakları, kapı ve katlar, karşı ağırlık,
kuyu dibi, makine, kuyu üstü, makine dairesi — hesabın **Sabitler** sekmesindedir
( ③a – ③j, bölümleri `cizim/sabitler.BOLUMLER` );  çizim, yerleşimin ölçü
listesi ve bölüm 11 aynı sayıyı kullanır ( `kopru.OFIS_SABITLERI`;  fabrika
ayarı `cizim/sabitler.py` ).  Makine bölümü tek bir makinenindir ( referans
projenin dişlisiz makinesi ) — başka makinede oradan değiştirilir.  Aralık
dışındaki değer hesabı durdurur ve çizime de geçmez ( `sabitler.aralik`:  sıfır
yalnız boşluk ve paylarda — ray boyu sıfır olamaz ).  Kuyu tavanı payının adı
Sabitler'de eskisi gibi `tavan_payi`'dır ( kayıtlı projeler onu taşır ).
Revizyon kutusunun yüksekliği de oradadır ( çizim onu çizmez — karar 10:
LiftDesigner da çizmiyor, ölçüsü yok;  bölüm 11 bu yükseklikle kabinin bütün
izdüşümünde denetler ).

**Karşı ağırlık dolgusu** ( karar 11 ).  Karşı ağırlık rayları bölümü dolgunun
çerçeveye sığdığını denetler:  gereken yükseklik Hd = Mcwt / ( ρ × Gx × Gy ),
çerçevede kalan Hç çizimden ( paten arası − alt ve üst kiriş;  2:1'de ağırlık
kasnağının altına ).  Çerçevenin ve kasnağın kütlesi yok sayılır ( güvenli
taraf ).  ρ blokların dış ölçüsüne göre, Sabitler ②e:  barit 2.800 kg/m³
( standart blok 960 × 155 × 120 mm, 50 kg — Tiraslift · Egeser katalogları ),
pik döküm 7.200 ( katı dökme demir;  blok kataloğu yok, denetim iyimser ).
Varsayılan çerçeve ( kullanıcı kararları 30 Eyl ):  derinlik ( Gx ) barit
bloğunun derinliği 155 ( eskiden 150 ), paten arası 3.300 ( eskiden 3.000 ) —
formun varsayılan asansöründe ( 800 kg yük, tablodan 800 kg kabin → karşı
ağırlık 1.200 kg, 2:1 ) 24 blok × 120 = 2.880 mm dolgu, kalan 2.980.  Her yüke
uyan tek varsayılan yoktur:  çerçevenin boyu, eni, derinliği ve malzemesi
projenin karşı ağırlığına göre seçilir.  **Genişlik ( Gy ) boşsa ağırlık
rayları arasından gelir** ( DBGW − 60:  iki uçta paten payı, referans proje 790
çerçevede 850 );  DBGW boşsa tersine Gy + 60, ikisi de boşsa Gy 960
( `tasarim/alanlar.AGIRLIK_PATEN_PAYI`;  kullanıcı kararı 1 Eki — eskiden Gy
hep 960'tı, ray arası 1.700 girilen 1022'de çerçeve ile ray arasında her
yanda 370 mm kalıyordu ).  Kesitte dolgu da aynı sınırda biter
( `donanim.agirlik_dolgu_kotlari` — eskiden kasnağın içine 300 mm giriyordu ).
Sığmıyorsa bölüm gereken paten
arasını yazar ( "paten arası en az 4.500 mm olmalı" — kalan yükseklik paten
arasıyla birebir büyür ).  Motor doğrudan çağrılınca ( çizim yok ) denetim
yapılmaz;  motorun elle doğrulanan örneği kendi değerleriyle ( 150 · 3.000 ).

**Askı düzenleri** ( hepsi hem çizilir hem bölüm 11'de ölçülür ):

| Düzen | Makine dairesiz | Makine daireli |
|---|---|---|
| 2:1 kabin altı, ağırlık yanda | ✓ | ✓ |
| 2:1 kabin üstü, ağırlık yanda | ✓ | ✓ ( varsayılan kasnak arasıyla dişli makine plakada üst bağlantılarla çakışabilir — çizim reddeder, söyler ) |
| 1:1, ağırlık yanda ya da arkada | ✗ reddedilir | ✓ |
| 2:1 kabin üstü, ağırlık arkada ( çapraz kasnaklar ) | ✓ | ✓ |
| 2:1 kabin altı, ağırlık arkada | ✗ reddedilir | ✗ reddedilir |

- **Kabin üstü 2:1, ağırlık yanda:**  iki kasnak kabin şasesinin üst kirişinin üstünde;
  kasnağın alt ucu kirişten 30 mm yukarıda ( `kabin_ustu_kasnak_boslugu` —
  ÇİZİM KABULÜ, tedarikçi ölçüsü gelince değişir ).  Bölüm 11'de kasnağın
  tepesi ile kuyu tavanı arası ayrı satırdır ( m.5.2.5.7.2 a:  ≥ 0,50 m ).
- **1:1** ( LiftDesigner 12744-3 ):  halatlar kabin şasesinin üst kirişinin
  ortasındaki tek bağlantıda biter ( ray ekseninde;  bağlantı yüksekliği
  365 = kabin bağlantısının alt − üst ucu );  tahrik kasnağının yakın teğeti
  bağlantının tam üstündedir, saptırma kasnağı halatı karşı ağırlığın eksenine
  taşır.  Kuyu tavanında halat bağlantısı yoktur.  Bölüm 11'de bağlantının
  tepesi ile kuyu tavanı ayrı satırdır.
- **Arkadaki ağırlıkla 2:1** ( `cizim/arka_aski.py`;  kullanıcı kararı 30 Eyl:
  "çapraz, iki taraf dengeli";  ofisin 12495-18'i — 1275'te kasnaklar düz,
  ağırlık kasnağı ağırlıktan kaçık ):  kabin kasnakları KABİN ÜSTÜNDE, çapraz
  bir düşey düzlemde.  Karşı ağırlık kasnağı ağırlığın ortasında, düzlemi
  genişlik boyunca;  tahrik kasnağının düzlemi derinlik boyunca, inişleri
  ağırlık kasnağının teğetinde ( W ) ve D1 önünde ( P );  kabin bağlantısı
  ( H ) P'nin kabin merkezine göre aynası — askı kabin merkezinde ( hesabın
  xs'i kabin merkezi – ray ekseni ).  Kasnakların dış teğetleri P ve H'de,
  aralıkları geometriden.  Ağırlık – duvar ölçüsü boşsa ağırlık kabine göre
  konur:  P kabin tavanının arka kenarından korkuluk payı ( 100 ) içeride,
  ağırlık kabine en az 50 mm.  Makine dairesizde makine DUVARDAN DUVARA iki
  kirişe oturur ( karar 3'ün platformu — yük bina yapısına ):  kirişler
  derinlik boyunca ön ve arka duvarın iç yüzleri arasında, uçlarda bağlantı
  levhası, tahrik kasnağının iki yanında simetrik ( her birine F / 2;
  referans projede kasnak kirişlerin dışında taşkındı ) — hesabın L'si kuyu
  derinliği, X tahrik kasnağının merkezi.  Makine ve kirişler kabinin
  üstündedir.  Kasnaklar kabin tavanına oturur ( alt uçları tavanın 80
  üstünde, `kabin_tavani_kasnak_boslugu`;  12495-18'de kabin tepesi 2.000,
  Ø 240 kasnaklar 2.080 – 2.320, 1275'te de öyle ) — aralarındaki halat
  şasenin üst kirişinin altından geçer.  Makinenin tepesi tavanın 50 altında
  ( `duvar_kirisi_tepe_boslugu`;  12495-18:  makine 3.750 – 4.150, UPN 100
  kiriş 3.650 – 3.750 );  raylara oturan makinede 250 kalır.  Son kat:
  1.100 × 1.100 kabinde, ofisin kabiniyle ( 2.000 ) 4.270, kabin 2.200 ile 4.470.  Sınırı
  arkadaki 1,10 m'lik korkuluk koyar ( kabin – arka duvar 0,50 m'den fazla;
  küpeşte ile kiriş arası ≥ 0,30 m, m.5.2.5.7.2 c ).  LiftDesigner 12495-18'i
  4.200 ile çiziyor ama korkuluğu denetlemiyor:  kendi ölçüleriyle ( kabin
  tepesi 2.000, kirişin altı 3.650 ) bizim 275 mm yükselmemizle küpeşte
  kirişe 275 mm kalır.
  Standart kabinlerde kuyu kabinden 700 derin olunca çizilir ( 450'de ağırlık
  kabinin arkasına sığmaz ).
- **Reddedilenler** ( `kuyu_ustu.duzen_hatalari`;  kesitteki öteki hatalardan
  önce söylenir ):  makine dairesizde 1:1 — halatın tahrik kasnağından kabinin
  ortasına ve ağırlığa inmesi için kuyu tepesinde saptırma düzeni gerekir,
  referansı yok;  arkadaki ağırlıkla kabin altı 2:1 — iki referans da kabin
  üstü.
- Ağırlık arkadayken halat düzlemi y yönündedir:  makine, saptırma ve plaka
  delikleri aynı fonksiyonlarla çizilir, eksenler takas edilir
  ( `kuyu_ustu.Duzlem`, `makine.takas` ).

**Girilmişse denetlenir.**  Değer girilmişse kullanılır ve çizimle
karşılaştırılır;  uyuşmazsa çizim durur ve doğru değeri söyler
( `kopru.tutarlilik` ):  halat sarılma açısı, D2 · Ds, kuyu dibi zinciri,
makine kirişleri raylara oturuyorsa mesnet aralığı = ağırlık rayları arası
( DBGW ).  α yalnız çizim onu tek bir sayı olarak biliyorsa karşılaştırılır
( `kopru.sarim_acisi` ).  Boş bırakılmış bir alan formdaki adıyla söylenir
( "Karşı ağırlık yeri:  seçilmemiş" — çizim modülünün iç adı ya da "None"
değil ).  Çizimin henüz modellemediği kaçıklıklar ( kabin merkezi yc, askı
ys ≠ 0 ) ve çift sarımlı kanal açıkça söylenir ( çift sarımda bölüm 11 yine
çizimden ölçülür — kuyunun geometrisi sarım sayısından bağımsızdır;  karar 6 ).
Makaralı KABİN pateni ( karar 2 ) seçilince çizim durur:  kabin patenlerinin
ölçüsü referans projenin kaymalı patenlerinden, bölüm 11'in paten açıklıkları
ölçülemez ( HESAP EKSİK ) — makaralı kabin pateninin ölçüleri gelene kadar.
Karşı ağırlıkta makaralı paten çizilir:  referans projenin ( çizimin bütün
ölçülerinin kaynağı ) ağırlık patenleri makaralıdır, çizim ikisinde aynı izi
kullanır ( kullanıcı kararı 30 Eyl ).

**Ekran.**  Asansör sekmesinin sağ sütunu **Hesap | Çizimler** arasında
geçer;  çizimler aktif asansörün, girdi değiştikçe tazelenir
( `hesap/static/uygulama.js`, uç `POST /api/uygulama/cizimler` —
`hesap/api/cizim.py` ).

**Tuval** ( kullanıcı isteği:  "AutoCAD gibi yan yana, istediğimde
yakınlaştırayım" ):  çizimler alt alta değil, tek düzlemde yan yana durur —
LiftDesigner paftalarının model alanı gibi.  Her çizim kendi ölçeğiyle
( kesit 1/50, plan 1/20 ) pafta milimetresine küçültülür, yazıları hepsinde
aynı boydadır;  paftanın sırasıyla ( önce düşey kesitler, sonra planlar )
sütun sütun dizilir, sütunun boyu tuvalin en–boy oranına göre seçilir ( 25
aday — çizimleri ekranda en büyük gösteren ).  Açılışta hepsi sığar, tuval
pencerenin altına kadar uzanır.  Tekerlek imlecin altındaki noktayı yerinde
tutarak yakınlaştırır ( dokunmatik yüzeyde iki parmak sıkıştırma da ),
sürükleme ( sol ya da orta tuş ) kaydırır — sürüklemeden sonraki tık ölçü
açmaz;  bir çizime çift tıklamak ona yaklaşır, boş yere çift tıklamak ya da
"Sığdır" ( klavyede 0 ) hepsini sığdırır;  + / − düğmeleri ve tuşları.
"Tam ekran" tarayıcının tam ekranı, izin verilmezse tuval pencereyi kaplar
( Esc çıkar ).  Yakınlaştırma CSS ölçeği değildir:  her çizimin ekrandaki eni
ve boyu yeniden hesaplanır, tarayıcı SVG'yi o boyda yeniden çizer — her
yakınlıkta çizgiler ve yazılar keskindir ( kütüphane yok;  bir projenin bütün
çizimleri ~2.000 eleman, SVG'ye hafif ).  Tuval kalıcıdır:  ölçüden değişiklik
çizimleri yenileyince görünüm ve tam ekran yerinde kalır, ölçü kutusu ölçünün
yanında durur ( kaydırınca izler ).

**Hatalı girdide çizim yerinde kalır** ( kullanıcı isteği 2 Eki ):  çizim
kurulamayınca ekranda son geçerli girdilerin çizimi durur ( tuvalin kenarı
kırmızımsı ), sebepler tuvalin sağ üstünde liste olarak durur ve düzeltilince
kendiliğinden kalkar ( `mTuvalHata` );  tam ekrandan çıkılmaz.  Eskiden çizimler
kapanıyor, yerine kırmızı bir uyarı geliyordu.  Kalan çizimin ölçüleri
tıklanır:  kaynakları o çizimin girdileriyle bulunur ( `M_CIZIM_GECERLI` —
formun bugünkü hâliyle çizim kurulamıyor ), kutu formdaki değeri de söyler
( "şimdi 2400 mm ( çizimde;  formda 1200 )" ), yazılan değer formun bugünkü
hâline yazılır — hata yanlış ölçüyü yeniden tıklayarak da düzeltilir.  Hiç
geçerli çizim yoksa ( hatalı girdiyle açılan proje ) tuval boş, liste aynı yerde.
Liste yazarken açılmaz:  çizim 1,2 saniye kurulamamış kalırsa açılır
( `TUVAL_HATA_GECIKME`;  kutu silinip sayı yavaş yazılırken boş ve yarım değer
geçersizdir, liste her tuşta açılıp kapanıyordu ), açıksa içeriği hemen yenilenir.
Uyarıların kendisi değişmedi:  program eskiden hangi durumda "çizim kurulamadı"
diyorsa yine yalnız onlarda söyler.

**Ölçüye tıklama.**  Çizimlerdeki her ölçü tıklanır ( klavyeyle de ):  küçük
bir kutu ölçünün **hangi girdiden geldiğini** söyler ve yeni değer yazılabilir.
Çizim elle değişmez — yeni değer ölçünün geldiği **girdi kutusuna** yazılır,
form kendi akışıyla hesabı ve çizimi yeniler ( hesap ile çizim aynı sayıyı
kullanmaya devam eder ).  "Formda göster" alanın grubunu açıp alanı gösterir.

- **Kaynak ölçülür, elle etiketlenmez** ( `cizim/olcu_kaynagi.py` ):  her
  girdi 1 mm oynatılıp çizim yeniden kurulur, ölçünün değişimine bakılır
  ( eğim ).  Yüz kadar ölçü ve zincirleri — sonradan eklenenler de —
  kendiliğinden kapsanır.  Kaynak türleri:  formun sayı kutusu
  ( değiştirilir ), tam sayı ve seçim kutusu ( gösterilir;  sayılı seçimde
  seçenek seçilir ), Sabitler sekmesindeki ofis standardı ( çizimin ürün
  ölçüleri dahil — tek katalog;  gösterilir ).  Ölçünün kendisi olan girdi
  ( değeri eşit, eğimi 1 ) önce gelir:  DBGW'nin kaynağı "boşsa Gy + 60"
  kuralından önce ağırlık rayları arası kutusudur ( `kopru.KURALLI` —
  kuralla dolan alanların etkin değeri ).  Bir girdiye bağlı olmayan ölçü
  dayandığı kuralı söyler ( sığınma alanının yeri, pano önü çalışma alanı —
  `geometri._olcu(kural=…)` ).  Test:  bütün düzenlerde her ölçünün bir
  kaynağı ya da kuralı var.
- **Kurallı konumlar çözümlemede yerinde tutulur:**  regülatörün boş
  bırakılmış yeri program tarafından aranır ( varsayılan xs'in işaretine göre
  ±280, gergi çarpıyorsa başka yer );  1 mm oynatmada arama başka yere
  atlayınca ölçü zinciri değişiyor, 1022'de ray ekseninin 880'lik ölçüsü
  "askı kaçıklığına bağlı" görünüyordu.  Çözümlemede regülatör tabandaki
  yerinde tutulur ( seçim kutularında düzen kuralla yeniden kurulur ).
- **Değiştirme doğrulanır:**  yeni değer eğimden bulunur, çizim adım adım
  yeniden kurularak ölçü izlenir ( zincirde uçlar yer değiştirir, konsol
  sayısı değişir ) ve hedefte olduğu görülür;  doğrusal değilse kiriş
  yöntemi.  Birden çok girdiye bağlı ölçüde hangisinin değişeceği sorulur.
  Hedef doğrulanamazsa:  bağıntı doğrusal ve ölçü yeni çizimde iki ardışık
  parçaya bölünmüşse ( kabin kuyu ortasının öbür yanına geçince "995"
  "5 + 1.000" olur ) doğrusal tahmin yazılır, "iki parçaya bölündü" denir;
  değilse ( ölçü bir eşikte sıçrıyor, bu yönde değişmiyor, sığınma alanı gibi
  adımla kayıyor ) kutuya bir şey yazılmaz, sebebi söylenir — eskiden kiriş
  yöntemi bölünen ölçüde başka aralığı izleyip saçma değer yazıyordu ( kabin
  genişliği 58.430, kaçıklık −15 yerine −5 ).  Negatif ölçü reddedilir.
  Tarama:  7 proje × bütün çizimler × her ölçünün her sayı kaynağı ±10 mm
  ( 3.408 değişiklik ):  hata yok, saçma değer yok.
- **Bağlı büyüklükler birlikte değişir:**  girilmiş kaide ile kuyu dibi
  ( zincir:  kuyu dibi 1.500 → 1.600, kaide 306 → 406 ), girilmiş D2 · Ds · α çizimdeki
  değere ( `kopru.tutarlilik_duzeltmeleri` — tutarlılık denetimiyle aynı yerde ).
- **Çizimi bozacak değer önce sorulur:**  sebepleriyle ( kuyu genişleyince
  korkuluk gerekir, tavana sığmaz … ) "Yine de uygula / Vazgeç";  uygulanan
  değişiklik çizim kurulamasa da panelde yazar.
- Çözümleme bir çizim için 0,1 – 3 saniye ( en ağırı düşey kesitler );  fare
  çizimin üstüne gelince önceden istenir, sunucu önbelleğinde tutulur;  o
  bitmeden tıklanırsa ikinci istek birincisini bekler ( eskiden aynı iş iki
  kez, paralel yapılıyordu — 1022'de tıklama 12 saniye bekliyordu ).
  Çözümlemede çizim yalnız ölçüleri için kurulur ( `geometri.yalniz_olculer`:
  kuyu dibinin yük kutuları yerleşmez ) ve regülatör araması kuyu dibinde
  çarpan yerde makine dairesini kurmaz.  Uçlar
  `POST /api/uygulama/olcu` ( kaynaklar ) ve `/api/uygulama/olcu_degistir`.

**Paket.**  "Projeyi paketle" her asansörün çizimlerini hesap sayfalarının
sağına ekler ( çok asansörlüde şeritte asansörün adı ).  Bir asansörün çizimi
kurulamıyorsa paket inmez, sebebi söylenir — eksik proje teslim edilmesin
( hesap PDF'i yine iner ).

**Kopyanın orijinalden farkları** ( `hesap/` ):  `api/cizim.py` ( yeni ),
`api/uygulama.py` ( çizim alanları, paket ), `main.py` ( port 8780, çizim
uçları ), `exports/dxf_export.py` ( paketin son işlemi ), `static/` ( Hesap |
Çizimler, ölçüye tıklama );  hesap motorunda `engine/uygulama/mukavemet.py` ( bölüm 11 çizimden ),
`mukavemet_girdi.py` ( alan tanımları, gruplar, "Gelişmiş" listesi, ⓘ metinleri ve
doğrulama listeleri artık tasarım şemasından türetilir — `tasarim/alanlar.py`;
motorun sözleşmesinin biçimi ve içeriği aynı kaldı.  Çizimden türeyen beş girdi:
varsayılanı boş, `tamamla` türetir;  son kat yüksekliğinin varsayılanı 3.750 → 4.200 — projelerde girilen
değer;  3.750'de varsayılan asansörün üst pateni kuyu tavanına giriyordu ), `sabitler.py` ( kabinin düşey ölçüleri ), `girdi.py` ( elektrik alanları ve formun sözleşmesi şemadan;  makine yerleşimine göre gizlenen alanlar şemanın yerleşim bayrağından — ekran, API ve motor tek liste ), `__init__.py`
( çizim modülünün yolu ).  Testler yeni modele göre güncellendi, TEST 7 ve
TEST 10'un dondurulmuş referansları farklar incelenerek yeniden üretildi
( fark:  bölüm 11, xs'in ray hesabı, D2'nin halat ve tahrik hesabı;  α'nın çizimden geldiği senaryolarda tahrik sınırları — düşey inişli 180°, makine daireli 1:1'de 134,3° — ve α uyarısının metni ).  Motor doğrudan çağrılınca da ( testler ) türetme uygulama alanlarının varsayılanlarıyla yapılır — program ile motor aynı α'yı, aynı D2'yi bulur.
Arayüz testleri ( TEST 5 ) birleşik formun sözleşmesine göre:  tasarım sırasıyla 11 grup, hesaptan kaldırılan KD · ağırlık ray arası · ray–duvar kendi tasarım grubunda bir kez ( aynı anlam, hesaba girmez ), D2 formda yok, son kat 4.200;  çizimlerde tuval ( açılışta hepsi sığar, tekerlek imlecin altında yakınlaştırır, sürükleme kaydırır ve ölçü açmaz, Sığdır, değişiklikten sonra görünüm yerinde ) ve ölçüye tıklama ( kutu, önce sorma, uygulama, Formda göster ).  Testlerin varsayılan adresi 8780.

## Kurulum ve çalıştırma

`baslat.command` ( Windows:  `baslat.bat` ) çift tıklanır:  ilk açılışta
`.venv` kurulur, program **http://127.0.0.1:8780**'de açılır ( orijinal hesap
programı 8760'ta açık kalabilir, çakışmazlar ).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python hesap/main.py                    # birleşik program ( 8780 )

.venv/bin/python calistir.py                      # kuyu planı  →  cikti/ ( git'e girmez )
.venv/bin/python calistir.py --aski Doğrudan      # 1:1 askı düzeniyle
.venv/bin/python calistir.py --agirlik Arka       # karşı ağırlık arkada
.venv/bin/python calistir.py --cizim kuyu_kesiti_yan  # A-A tam boy düşey kesit ( 1/50 )
.venv/bin/python calistir.py --cizim kuyu_kesiti_on   # B-B tam boy düşey kesit ( 1/50 )
.venv/bin/python calistir.py --cizim kuyu_kesiti_on --makine "Makine dairesi"   # makine daireli
.venv/bin/python calistir.py --pafta               # bütün çizimler TİP PROJE FORMATINDA ( DXF + SVG önizleme )

# DENETİM — tek komut ( kontrol.py;  adımlar sırayla koşar )
.venv/bin/python -m pip install -r requirements-gelistirme.txt   # ruff, pytest ( bir kez )
.venv/bin/python kontrol.py           # hızlı:  lint + biçim, hesap, çizim ( yavaş test hariç ), node  ( ~3 dk )
.venv/bin/python kontrol.py tam       # + yavaş test ( her ölçünün kaynağı, ~7 dk )
.venv/bin/python kontrol.py bicim     # biçimi ve düzeltilebilir lint bulgularını düzeltir
.venv/bin/python kontrol.py arayuz    # arayüz testleri:  programı 8790'da açar, kapatır ( ~20 dk )
.venv/bin/python kontrol.py tarama    # girdi taraması:  378 düzen, hükümler kayıtla ( ~15 dk )

# Örnek tam projeler ( hesap + çizim, tek pafta ) → ornekler/ — programın
# "Projeyi paketle" yolundan:
.venv/bin/python ornekler/uret.py
```

## Denetim

Her değişiklikte en az `kontrol.py` ( hızlı ), commit'ten önce `tam`,
`arayuz` ve çizimi etkileyen değişiklikte `tarama`.  GitHub'da her push'ta
hızlı denetim kendiliğinden koşar ( `.github/workflows/denetim.yml`;  tam
denetim Actions sekmesinden elle başlatılır ).  Ortam `requirements-kilit.txt`
ile birebir kurulur ( sabitlenmiş sürümler ).

**Dondurulmuş çıktılar** — kodu düzenlerken ( refactor ) davranışın
değişmediğini kanıtlar;  biri değişirse test hangi düzende, hangi çizimde,
hangi elemanda olduğunu söyler.  Yeniden üretmek **davranışı değiştirme
iznidir**:  yalnız kasıtlı bir değişiklikten sonra, farklar incelenince.

| Dosya | Ne dondurulur | Yeniden üretme |
|---|---|---|
| `testler/altin_cizim.json.gz` | 35 düzenin tam paftası ( her çizimin elemanları + SVG ) | `.venv/bin/python -m testler.altin_cizim` |
| `testler/tarama_hukumleri.json` | 378 düzenin hükmü ( çizildi / ret ve sebebi ) | `.venv/bin/python -m araclar.tarama --yenile` |
| `hesap/dogrulama/altin_*.json.gz` | hesabın tam çıktısı ( trafik, avan, uygulama ) | `cd hesap && ../.venv/bin/python dogrulama/altin_uret.py` |
| `hesap/dogrulama/referans_*.json.gz` | hesabın ara değerleri ve hükümleri | `cd hesap && ../.venv/bin/python dogrulama/tarama_uret.py` |

Yavaş testler `testler/yavas.py`'deki `@yavas(...)` ile işaretlenir:
hızlı denetimde atlanır ( çıktıda "skipped" ), tam denetimde koşar.

**Kod üslubu** ( `pyproject.toml` ):  biçimi `ruff format` verir ( satır 110,
elle hizalama yapılmaz );  `ruff check` yalnız hata yakalayan kuralları
uygular — kullanılmayan ad, döngü değişkenini yakalayan iç fonksiyon, genel
`except` ( her biri `# noqa: BLE001 — sebep` ile bilinçli olmalı ).  Çizim
testleri pytest ile paralel koşar ( `KONTROL_IS`, varsayılan 4 işçi ).  Biçim
commit'leri `.git-blame-ignore-revs`'te:  `git config blame.ignoreRevsFile
.git-blame-ignore-revs`.

**Kayıt** ( `logging` ):  uçların genel `except`'i kullanıcıya iletiyi
döndürür ve hatayı kaydeder ( `api/ortak.hata_kaydi`:  girdiden doğan ret
bilgi, beklenmeyen hata izleriyle hata düzeyinde );  çizimin yedek değere
düştüğü yerler ayrıntı düzeyinde.  Düzey:  `AVAN_KAYIT=DEBUG|INFO|WARNING|ERROR`
( varsayılan WARNING ).

## Klasörler

| Yol | Ne var |
|---|---|
| `hesap/` | Hesap programının kopyası ( sunucu, arayüz, hesap motoru, kendi testleri ) |
| `baslat.command` · `baslat.bat` | Birleşik programın başlatıcıları ( `.venv` + `hesap/main.py` ) |
| `tasarim/alanlar.py` | **Tasarım şeması**:  bütün girdilerin tek tanımı, tasarım sırasıyla ( grup, kaynak, formda mı, yerleşim, doğrulama bayrakları, ⓘ metni ) |
| `tasarim/gorunum.py` | Şemadan türetilenler:  motorların alan sözleşmeleri, form, yerleşime göre gizlenenler, çizimden gelenler |
| `tasarim/sozluk.py` | Sayı sözlüğü:  her sayının kaynağı, açık sorunlar ve hesabın içindeki geometri tahminleri |
| `cizim/kopru.py` | **Hesap → çizim köprüsü**:  çizim girdisinin kurulması, çizimden türeyen hesap girdileri, tutarlılık denetimi |
| `cizim/arka_aski.py` | **Arkadaki ağırlıkla 2:1**:  kabin üstünde çapraz kasnakların, tahrik ve ağırlık kasnağı inişlerinin ve bağlantıların plandaki geometrisi ( tek yerde ) |
| `cizim/olculer.py` | **Yerleşimin ölçü listesi**:  hesabın çizimden aldığı geometri ( xc · xi · ray ve halat boyları · kasnak sayıları · makinenin kirişteki yeri ) |
| `cizim/girdi.py` | Çizim girdisinin **sözleşmesi**, doğrulaması ve deneme ölçüleri |
| `cizim/sabitler.py` | Ofisin ürün ölçüleri ( konsol, paten, kasa, pano … ) — fabrika ayarı;  Sabitler sekmesindeki bölümleri ( `BOLUMLER` ), geçerli aralıkları ( `aralik` ) |
| `cizim/geometri.py` | Girdiden **çizim elemanları** üretir ( saf veri ) — kuyu planı |
| `cizim/kabin_ustu.py` | Kabin üstü planı:  kuyu planının elemanlarını okur, tavanı ekler |
| `cizim/kuyu_dibi.py` | Kuyu dibi planı:  tamponlar, perde, gergi, sığınma alanı, merdiven |
| `cizim/hareketli.py` | Kabinin ve karşı ağırlığın parçaları ( plandaki iz + alt / üst kot ) — sığınma, açıklık ve çarpışma denetimleri buradan okur |
| `cizim/kapi_kesiti.py` | Kapı yan kesiti ( 1/20 ):  kasa, üst kutu, eşik ve konsolu, eşik altı sacı, kabin eşiği, önlük |
| `cizim/kuyu_ustu.py` | Kuyu üstü planı ( MRL ):  makine, halat bağlantıları, regülatör, acil pano |
| `cizim/makine_dairesi.py` | Makine dairesi planı + döşeme halat delik planı |
| `cizim/dusey.py` | Düşey kesitlerin yerleşimi ve açıklık denetimleri |
| `cizim/donanim.py` | Kuyu donanımının KOTLARI:  makine, şase, bağlantılar, regülatör, gergi, raylar, konsollar, karşı ağırlık |
| `cizim/kesit_parcalari.py` | Düşey kesitlerde parça çizimi ( yan ve ön bakış ortak ) |
| `cizim/kuyu_kesiti.py` | Tam boy A-A ( yan ) ve B-B ( ön ) kuyu düşey kesitleri, 1/50 ( gerekirse kırık ) |
| `cizim/kasnak_duzeni.py` | Kasnak düzenlemesi ( LiftDesigner gibi ):  tahrik ve saptırma kasnağı, halatlar, sarım açısı, 1/20 |
| `cizim/giris.py` | Giriş görünüşü ( LiftDesigner gibi ):  en alt durağın kat kapısı durak tarafından, 1/20 |
| `cizim/cizimler.py` | Çizimlerin listesi:  doğrulama, çizici, başlık, ölçek ( calistir ve pafta ortak ) |
| `cizim/pafta.py` | Çizimleri ofisin TİP PROJE FORMATINA yerleştirir, anteti doldurur |
| `sablon/proje_formati.dxf` | Ofisin pafta şablonu ( TİP PROJE FORMATI.dwg'den;  hesap programınınkiyle aynı ) |
| `cizim/svg.py` | Elemanları SVG'ye yazar ( ekranda ölçüler tıklanır ) |
| `cizim/olcu_kaynagi.py` | Ölçünün kaynağı ( girdiler oynatılarak ) ve ölçüden değiştirme ( doğrulamalı ) |
| `cizim/dxf.py` | **Aynı** elemanları DXF'e yazar ( ezdxf ) |
| `testler/` | 376 test ( `test_kapilar.py` — kanat sayısı ve kanat cebi, `test_cizim.py`, `test_fiziksel_tutarlilik.py`, `test_girdi_sinirlari.py`, `test_kopru.py`, `test_olcu_kaynagi.py`, `test_yerlesim_saglamligi.py` — standart asansörler varsayılan çizim ayarlarıyla çizilir, `test_tasarim.py` — tasarım şeması, `test_olculer.py` — yerleşimin ölçü listesi, `test_arka_aski.py` — arkadaki ağırlıkla 2:1, `test_kararlar.py` — makaralı kabin pateni, çift sarım, dolgu, tek katalog, `test_gercek_projeler.py` — ofisin altı gerçek projesi ( veri `gercek_projeler.py` ), `test_gorunusler.py` — kasnak düzenlemesi ve giriş görünüşü, `test_kesit_yerlesim_regresyon.py` — şase üst kirişi, ağırlık patenleri, dolgu, ağırlık genişliği, kabin – ağırlık ölçüleri, duvarlar ) |
| `ornekler/` | Yalnız iki örnek tam proje ( `.dwg` + `.pdf` ):  **makine dairesiz** ( referans proje ) ve **makine daireli dişli** ( aynı asansör );  onları üreten `uret.py` ve formun girdisi `hesap_girdi.py` |
| `cikti/` | `calistir.py`'nin tek tek çizimleri, taramanın ayrıntılı sonuçları ( git'e girmez ) |
| `kontrol.py` | Bütün denetimler tek komutta ( hızlı · tam · arayüz · tarama · biçim ) |
| `yollar.py` | Programın import kökleri ( depo kökü, `hesap/`, `ornekler/` ) — giriş noktaları bir kez kurar, kütüphane modülleri `sys.path`'e dokunmaz |
| `hesap/dogrulama/` | Hesabın doğrulama paketi ( `calistir.py`;  eski adı `hesap/testler` — depo kökündeki `testler/` ile çakışıyordu ) |
| `araclar/` | Girdi taraması ( `tarama.py` ) ve yazı – çizgi kesişmeleri ( `kesisme.py` ) |
| `requirements-kilit.txt` | Sabitlenmiş bağımlılıklar ( CI ve sunucu bunu kurar ) |

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
   rayının ara kirişi ağırlıkla ray arasına sığar.  Kabinin iç yüksekliği ve kat
   kapısının yüksekliği en az 2.000 mm ( m.5.4.1 · m.5.3.1.1 ), kapı kabinin iç
   yüksekliğinden yüksek değil ( `girdi.dogrula`, 4 Eki — eskiden 1.500'lük kabin
   ve kabinden yüksek kapı sessizce çiziliyordu ).

   **Kuyunun geometrisi kurulamıyorsa HESAP DA DURUR** ( kullanıcı kararı 4 Eki ):
   hesap geometriyi çizimden alırken ( `engine/uygulama/girdi.yerlesim_olculeri` )
   çizimin plan doğrulamasını ( `girdi.dogrula` ) da koşar;  hata varsa hesap
   kurulmaz, aynı iletiler söylenir ( çok asansörlü projede asansörün adıyla ).
   Eskiden kabin kuyuya sığmasa da hesap kuruluyor, özet yalnız "engelleyici"
   diyordu — imkânsız bir kuyunun raporu yazdırılabiliyordu.  Çizimin yalnız
   ÇİZEMEDİĞİ durumlarda ( makaralı kabin pateni, 3 tampon, yana kaçık askı —
   köprünün iletileri ) hesap sürer.  Not:  formda karşı ağırlık sola alınıp
   kapı ( varsayılan Teleskopik Sol ) değiştirilmezse kapı ağırlığa doğru açılır,
   kanat cebi ara kirişe çarpar — artık hesap da durur, ileti "kapıyı öbür yana
   açın" der.

   **Tampon adedi** tam sayıdır, sıfır olamaz ( hesap da durur );  çizim 1 ya da
   2 tampon çizer, ikisinde "Kabin / Ağırlık tamponları arası" ( Gelişmiş ) girilir.
   Eskiden 0 ve 1,5 sessizce 1 sayılıyor, 2'de istenen aralığın formda kutusu yoktu.
   Testler:  `testler/test_mantik_denetimi.py`.
5. **Yerleşim seçilir, koda gömülmez.**  Askı düzeni ( kabin altı · kabin üstü ·
   doğrudan ), karşı ağırlık yeri ( sağ · sol · arka ), kapı tipi girdidendir.
6. **Uzatma çizgisi yoktur, yazı kendi ölçüsünün yanındadır.**  Ölçü çizgisi
   yalnız iki uçtaki kısa çizgiyle çizilir ( SVG ve DXF — `dimse1/dimse2` ).
   Bir iç parçayı ölçen ölçü ( askı aralığı ve kaçıklığı ) planın dışında
   değil, parçanın yanında durur;  eşik zinciri ise "KAPI ARASI"nı böldüğü için
   onun yanında, dış sıradadır ( aşağıda:  girdi taraması ).  Yazının yeri geometride bulunur
   ( `_yazilari_yerlestir` );  sığmayan yazı sıranın ucunun dışına ya da bir
   kat dışarı alınır, başka bir sıranın üstüne itilmez.  Sığmayan bir ARA
   ölçünün yazısı ortada bir parçanın ( ray, konsol, şase, tampon … —
   `PARCA_KATMANLARI` ) üstüne düşüyorsa uzatma çizgisinin hemen dışına, geniş
   komşu tarafa yazılır ( AutoCAD gibi;  kabin duvarının "75"i şase dikmesinin
   üstündeydi ).  Testler:  hiçbir iki ölçü yazısı üst üste binmez, hepsi
   çerçevenin içindedir, hiçbir çizimde ölçü yazısı bir parçanın ya da etiketin
   üstüne düşmez.  Çerçeve yazıların enini ve hizasını da kapsar.

   **Girdi taraması** ( 4 Eki;  kullanıcı:  "girdilerin ve gerçek projelerin
   tamamında doğru çıktı, kusursuz doğruluk" ):  378 düzen ( 9 yük × ağırlık
   sağ / sol / arka × makine dairesiz / daireli × askı, 7 kapı tipi, sığınma
   tipleri, kapı montajı, hız ) programın yolundan ( `api_cizimler` ) geçti;  her
   çizilen düzende bütün çizimler kuruldu, ölçü zincirleri, yazı – yazı ve ölçü
   yazısı – parça çakışmaları sayıldı.  Önce 100 düzenin 94'ünde çakışma vardı
   ( testler yalnız birkaç örneğe bakıyordu ), şimdi hiçbirinde yok.  Düzeltilenler:
   * Kuyu planında eşik zinciri ( KAT KAPISI · aradaki açıklık · KABİN EŞİĞİ )
     **sağdaki dış sıralarda, "KAPI ARASI"nın hemen içindedir** ( LiftDesigner
     gibi ):  kapının yanındaki şerit kanat cepleri, kasa ve ara kirişle doluyor,
     yazılar onların üstüne düşüyordu;  "şerit varsa içeride" de olmadı — girdi
     oynayınca yer değiştiriyor, ölçüye tıklayınca kaynağı bulunamıyordu.
   * Karşı ağırlığın yazısı bloğun içine düşüyorsa kasnağın çap yazısıyla tek
     yazıdır ( "KARŞI AĞIRLIK  ø 400" ).
   * Kabinin içindeki yazılar ( kasnak çapı, askı yazısı, kabin yazısı, askı
     kaçıklığı ) çakışırsa sıradaki boş adaya taşınır ( `_yazilari_coz` );
     parçaya binen ölçü yazısı kendi ölçüsü boyunca ya da ucunun dışında boş
     yere kayar ( `_yazilari_yerlestir(kaydir=True)` kuyu planı ve kabin üstünde,
     `_parcadan_kaydir` kuyu dibinde yük kutuları konduktan sonra — önce
     kaydırılınca bir düzende yük kutusuna yer kalmıyordu ).
   * Kabin üstünde sığınma alanının iki ölçü sırası adayları denenerek seçilir
     ( yazılar gerçekten yerleştirilir, çakışmalar sayılır );  korkuluk yazısı
     çizilen küpeşteye göre konur ( ön korkuluk operatörün arkasındadır — yazısı
     tavanın kenarına göre konup operatöre biniyordu ), sığmazsa küpeştenin
     dışına, o da olmazsa kısa yazıyla ( "h = 700" ).
   * Kuyu üstünde HALAT SAPMASI yazısı duvara ve makineye binmeyen yere.
   * B-B'de "KARŞI AĞIRLIK" yazısı ağırlık rayının yanına ( rayın altında kalıyordu ).
7. **Yazı boyu ve yeri SVG'de ve DXF'te aynıdır.**  Geometri yazının boyunu em
   ( font-size ) ve ORTASINI verir;  DXF'te etiket ( MTEXT ) ve ölçü yazısı
   yüksekliği büyük harf yüksekliğidir ( Arial 0,716 em ) — `dxf.BUYUK_HARF` ile
   çarpılır, hizası MIDDLE;  SVG taban çizgisine yazar, 0,35·h aşağı.  Eskiden DXF
   yazıları 1,4 kat büyük çıkıyor, pafta ve DWG'de ayrılan yere sığmıyordu;
   ekrandaki etiketler de DXF'tekinden 0,35·h yukarıdaydı ( çizimin başlığı
   şeridin çizgisine biniyordu — 5 Eki ).
8. **Yazı boyları LiftDesigner paftalarındaki gibidir.**  LiftDesigner örneklerinde
   ( 1022 · 1250 KG · 1275 · 800 KG · 4815-6 · 12495-18;  bloklar açılıp yazı
   yükseklikleri sayıldı ) kâğıtta büyük harf:  ölçü stili LIFT `dimtxt` **2,5 mm**,
   yazıların çoğu **2,5 mm** ( küçükleri 1,4 – 1,75 ), çizim başlığı **5 mm**.
   Eskiden ölçü 1,86 mm, etiketler 1,1 – 1,6 mm, başlık 3,4 mm idi;  AutoCAD'de
   okunmuyordu.  Bütün etiketler `geometri.YAZI_CARPANI` ( 70 / 52 ) ile büyür —
   `_yazi()` boyu `yb()` ile verir, aralarındaki sıra korunur;  ölçü yazısı
   `OLCU_YAZI` = 70 em ( 1/20'de 2,5 mm ), başlık 140 em.  Yazının yeri hesaplanırken
   de aynı `yb()` kullanılır ( `_yazi_eni(…, CGE.yb(40))` ).  Büyüyen yazılar için:
   * Üst üste konan ölçü yazılarının sıra adımı `KAT_ARALIGI` ( yazı boyu + 10 );
     yazı yalnız kendi sırasındakilere değil, başka sıraların yazılarına da
     bakılarak yerleşir ( kuyu planının köşesinde iki "DUVAR 150" biniyordu ).
   * Her çizimin son adımı `etiketleri_ayir`:  bir yazıya binen etiket en yakın
     boş yere kayar ( 20 mm'lik ızgarada, ±300 mm ), daha çok parçaya binmez.
   * Kasnak düzenlemesinde halatlar yakınsa KABİNE / AĞIRLIĞA halatların dış
     yanlarına yazılır;  makine dairesinde alan adları alanın ölçülerinden kaçar.
9. **Çizgi yazının üstünden geçmez ( ISO 128 ):  yazılar maskelidir.**  AutoCAD'de
   eksen, gizli çizgi ve komşu ölçünün çizgisi yazıların içinden geçiyordu
   ( "KABİN 1350 x 1400" kabinin iki ekseninin kesiştiği yerde, "ASKI ARASI"
   askı ekseninin üstünde;  girdi taramasında örnek projede 110 kesişme ).
   * DXF:  etiket arka planı zemin rengiyle örtülen MTEXT'tir ( "Background
     Mask · Use drawing background color", `dxf.MASKE_PAYI` 1,25 ), ölçü
     yazısında `dimtfill` 1.  Örtü yalnız kendinden önce çizileni örter:
     parçalar önce, sonra ölçüler, en son etiketler yazılır.
   * SVG:  harflerin çevresinde zemin renginde hale ( `svg.HALE` 0,6 em;
     ölçü yazısından büyük yazılarda ölçü yazısınınki kadar ), aynı sıra.
   * Önizleme ( ezdxf MTEXT arka planını çizmez ):  kopyada her maskenin
     yerine yazısının kutusu kadar WIPEOUT ( `pafta._maskeleri_ac` ).
   * Maske yalnız MASKELENEBİLİR çizgileri keser ( `geometri.MASKELI_KATMANLAR`:
     eksen, ölçü, gizli, alan sınırı, seviye, kesit işareti, halat ).  Öbürleri PARÇA
     KENARIDIR ( `parca_kenarlari` ):  yazı kenarın üstüne düşerse maske kenarı
     siler, düşmemelidir.  Etiket `etiketleri_ayir`'da kenara da binmeyen,
     duvarın ( taramalı kesit ) içinde durmayan, eskisinden çok parçanın içine
     girmeyen en yakın yere kayar ( 300 mm;  ölçeğe göre — 1/50'de 750 );
     yoksa 900 mm'ye kadar hiçbir parçanın içinde olmayan yere konur ve
     parçasına OKLU ÇİZGİYLE bağlanır ( dar yan karşı ağırlıkta KARŞI AĞIRLIK
     ø 400 kasnağın üstündeydi;  yeri kuyunun dışı, ok ağırlığı gösterir );  ölçü yazısı
     `_yazilari_yerlestir`'de adaylarından kenara binmeyenini seçer ( yoksa
     eskisi gibi ).  Düzelenler:  kuyu üstünde HALAT BAĞLANTISI / ø / REGÜLATÖR
     makine şasesinin, kabin üstünde HALAT şase kirişinin, kesitlerde KARŞI
     AĞIRLIK konsolların, kuyu planında kabin duvarının "75"i kabinin
     çizgilerinin üstündeydi;  B-B'de durak numarası kanat ayrımının üstündeydi
     — artık ortaya en yakın kanadın ortasında.
   * Girdi taraması ( `tara.py` ) yazının parça kenarına binmesini ve etiketin
     duvarın içinde durmasını da sayar.
   * Kenarlar ızgarada aranır ( `KenarIzgarasi` ):  hesap kuyu planını bir
     projede binlerce kez kurar;  her aday yer için bütün kenarları denemek
     hesap testini 163 sn'den 5.486 sn'ye çıkarmıştı.
10. **Ölçüler camgöbeği, ondalık ayırıcı virgül** ( kullanıcı 5 Eki ).  OLCU
   katmanı ACI 4:  AutoCAD'in koyu zemininde mavi ( 5 ) ölçü zor okunuyordu
   ( LiftDesigner da mavi );  çizgi ve yazı katmanın rengini alır ( `dimclrt`
   BYBLOCK ) — katmanın rengi hepsini değiştirir.  Önizlemede ( beyaz zemin )
   ölçüler mavi.  Yazılardaki ondalık nokta virgül olur ( `ondalik_virgul`,
   son adım:  "AĞIRLIK RAYI 127,5";  kotlar kaynağında "+3,40" );  madde
   numaraları ( "m.5.2.6.3.2.4" ) değişmez.  Ölçü kaynağı sayıyı ikisinde de
   tanır.
11. **Teknik resim üslubu ( ISO 128 ):  siyah çizgi, kalınlık anlam taşır**
   ( kullanıcı 6 Eki:  çizimler "oyuncak gibi" duruyordu — parçalar renkli
   dolguluydu ).  Kâğıtta 0,50 kesilen duvar / kesit / çerçeve · 0,35 ana
   parça · 0,25 ikincil parça · 0,18 ince parça ve gizli çizgi · 0,13 ölçü,
   eksen, tarama ( `svg.KALEM`;  1/20'de birim 10 · 7 · 5 · 3,6 · 2,6 ).
   Renkli kalan yalnız ölçü ( koyu mavi ) ve eksen ( koyu kırmızı );  dolgu
   yalnız örtmek için beyaz.  DXF'in katman renkleri AutoCAD'in koyu zemini
   içindir, ayrıdır.
12. **Parçaların gerçek biçimi:  zarf mantık içindir, biçim çizim içindir**
   ( `cizim/parcalar.py` ).  Yerleşim, çakışma, ölçü ve testler parçayı
   dikdörtgen zarfıyla bilir;  zarfa `bicim` yazılır ( dünya koordinatında
   kapalı çokgen ya da açık sac profil, `dolu` kesit, `ince` ayrıntı ) ve SVG
   ile DXF dikdörtgenin yerine onu çizer — zarf değişmediği için hiçbir
   denetim değişmez.  Her ölçünün kaynağı yanında yazılır ( standart · üretici
   kataloğu ), yoksa ÇİZİM KABULÜ diye işaretlenir.  **Markasız:**  hiçbir
   parça tek bir üreticinin kopyası değildir — standardın sabitledikleri
   birebir, projeye özgü ölçüler girdiden, üreticiye göre değişen ayrıntı
   birkaç üreticinin ORTAK biçiminden ( kullanıcı 6 Eki ).  Bugün:  kılavuz
   rayı ( ISO 8100-33 / 7465 kesiti — çokgen alanı ISO'nun S'si %1 ),
   kaymalı paten ( sac gövde + astar:  Metroplast 804'ün ray boyunca kesiti —
   yuva 30, çene 5, levha 4, yan destekler;  referans projenin 50 × 100 zarfında;
   dil ucunda 1 mm — Has şase kılavuzu ), makaralı paten ( karşı ağırlıkta, tip
   "Makaralı" ise:  üç makara ø100 × 25 — Metroplast 302, çizimden ölçüldü ),
   kabin şasesinin dikmesi ( aşağıda ), kat ve kabin kapısı ( kasa, eşik + oluk, kanat —
   aşağıda ), duvara dayanan kabin rayı konsolu:  TSE K 179 tipi çift L ( duvar
   konsolu + ray konsolu, yatay ayaklar Savera'nın C'si kadar bindirilir, iki
   M12 cıvata;  Savera standart konsolu — İTÜ tezi Çizelge 3.9 ) ve ray tırnakları
   ( Donati GF;  cıvata başı ve somun ISO 4017 / 4032 ).  Konsolun zarfları
   ( plaka, dar kol ) mantık için eskisi gibi;  biçim ikisinin kapsadığı
   dikdörtgende çizilir.  Karşı ağırlık
   konsolu LiftDesigner'ın ağırlık çerçevesi gibidir ( K431 · K111 · 1250 KG;
   profiller planda 40 ):  her ağırlık rayı tabanının dış yanındaki ray
   profiline dayanır ( yandaki ağırlıkta duvardan ara kirişe — kabin
   tarafındaki boyuna profil, kabin rayı ona bağlı;  arkadakinde duvardan
   tırnakların ötesine );  ağırlık ile duvar arasında profil + 20 mm çakışma
   payı varsa duvar profili de çizilir ( K431 ), yoksa çizilmez ( 4815-6 ) —
   20 mm standardın değil programın payı ( TS EN 81-20'de ağırlık – duvar için
   en küçük ölçü yok ).  Kabin kapısı operatörü kesitin üstündedir:  kesik.  Testler
   `testler/test_parcalar.py`.

## Plan ve kesitte ortak donanım

**Kabin şasesinin dikmesi** ( 8 Eki;  `parcalar.dikme_bicimi` ) her kabin
rayında raya açılan U'dur:  sırtı patenin arkasında ( paten sırta bağlı ),
kanatları patenin iki yanından dilin ucunu 25 geçer.  Kaynaklar:  LiftDesigner
K431 planı ( C dikme, kanatları raya, paten içinde ), referans projenin yatay
kesiti ( patenin arkasında levha, iki 50'lik C kirişin uçları dilin ucunu ~24
geçer, dış ölçü 300 ), Has Asansör şase kılavuzu Şekil 1 ( iki kiriş, paten
aralarında ).  Eskiden kabinin dış yüzüne yapışık 30'luk bir kutuydu:  patenle
arasında 30 mm boşluk kalıyor, paten havada duruyordu.  `sase_dikme` ( 30 ) artık
dil ucundan dikmenin sırtının arkasına:  paten_en / 2 + 5 mm sac ( ÇİZİM KABULÜ )
— girdinin "kabin dışı + 2 × 30 < DBG" denetimi böylece "kabin dikmenin sırtına
değmez" demektir ( referans projede sırt ile kabin arası 25, ofis kabininde 55 ).
Şasenin kirişleri ( planda kesik ) iki dikmenin sırtını bağlar.  Plan
derinliği yan kesitte de kullanılan `sase_dikme_derinlik` değeridir ( örnekte
300 mm );  dikmeler ray eksenine ortalanır.  **Karşı ağırlığın patenleri**
planda da çizilir ( eskiden yalnız kesitlerde vardı ):  kesitlerin kutusuyla aynı
zarf ( kullanıcı kararı 30 Eyl:  iki tipte aynı iz ), biçim formdaki "Karşı
ağırlık paten tipi"ne göre;  makaralının makaraları zarfın dışına taşar
( ağırlığın çerçevesinin üstünde / altındadırlar ).  Kabinin üst paten açıklığı
( m.5.2.5.7.2 b ) yalnız kabin patenlerini sayar. Kabin üstü korkulukları plan, düşey kesit ve açıklık kontrolünde
aynı konumları kullanır; kesit kırığı korkuluğu kesmez.

Regülatör gergisinin kasnağı, taşıyıcı kolu ve ağırlığı kuyu dibi planında
birlikte gösterilir. Kol ve ağırlığın plan kutuları düşey kesitte de
kullanılır; merdiven ve sığınma alanı bu kutuların dışında yerleştirilir.
Kolun raydaki bağlantısı bilinçlidir; ağırlığın rayla veya tamponla
çakışmasına izin verilmez.

Gergi ağırlığının merkezi kasnak merkezinden 300 mm ötededir ( referans proje regülatör
hesabı, "A = 300";  ağırlık 160 boyunda:  kasnağın 220 – 380 ötesi ).  Kesitteki
sembolden 340 ölçülmüştü;  referans projenin 280'lik regülatör kaçıklığında ağırlık
kuyudan taşıyor, örnek 260'a çekilmişti ( arka duvara 3 mm ).  Örnek yine
referans projenin 280'i:  `1167 + 280 + 380 = 1827`, duvara 23 mm.  Ağırlığın
planda duvara dik ENİ 82, kasnak düzlemine ortalı ( `gergi_agirlik_eni` ):  referans
proje vermiyor ( yalnız 35 kg, A 300, B 150 ve yan kesit );  eskiden boyuyla aynı
160 sayılıyordu ve rayları duvara 35 – 45 mm olan 1022'de ağırlık duvarı aşıyordu.
Gerçek gergiler ( ASPAR / Akşöz OSG-A/B kılavuzu ) kabin rayına tırnakla, tabandan
~450'de bağlanır ve duvara paralel ince bir dilimdedir:  25 kg ağırlık
296 × 150 × 82 kasnak düzleminde asılı, gövde 103;  12 kg 2 × 53;  yaylı
108 – 133.  Ağırlık duvarlara
en az çizimin çakışma payı ( `girdi.ASGARI_ACIKLIK`, 20 ) kadar uzak durur;
bir yönde sığmazsa kol öbür yöne döner, ikisinde de sığmazsa çizim durur.  Üst
regülatör aynı girdiyi kullanarak gergi kasnağıyla hizalı kalır.

Patenlerin MERKEZLERİ arası hesap programının paten arasıdır ( TS EN 81-50'nin
kuvvet kolu h;  `dusey.kabin_paten_arasi`, `dusey.agirlik_paten_arasi` — varsayılan
2.660 ve 3.400, referans projenin örneğinde 3.300 ve 3.060 ).  **PATENLER
KİRİŞLERİN VE ÇERÇEVENİN DIŞINDADIR** ( 8 Eki — LiftDesigner'ın ön kesitleri K431 ·
4815-6 · 1022 ve referans projenin kesitleri, çizimlerin vektörlerinden ölçüldü ):
kabinde alt paten şasenin en altında, alt kiriş onun üstünde ( 140 ), üst kiriş
üst patenin hemen altında ( 140;  referans projede 200 — UPN 200 );  karşı ağırlıkta
patenler çerçevenin üstünde ve altında, çerçeve paten arasından bir paten boyu
kısa.  LiftDesigner'ın 2.000'lik kabini:  alt paten −320 / −220, alt kiriş −220 / −80,
üst kiriş 2.200 / 2.340, üst paten 2.340 / 2.440 ( paten 100, merkezler arası 2.660 ).
30 Eyl – 8 Eki arası kirişler paten sanılmış, patenler kirişlerin yerine konmuştu
( varsayılan 2.420, kiriş 10 mm'lik simge ):  şasenin tepesi gerçekte 100 mm
yukarıdadır, kuyu tepesi açıklıkları o kadar iyimser çıkıyordu.  Referans projenin
çiziminde ağırlığın 140'lık patenleri 2.920'lik çerçevenin üstünde ve altında
( merkezler 3.060 — örnek girdi bunu kullanır;  hesabı ağırlıkta 1.500 alır,
kendi çizimiyle tutarsız );  kabinde hesabının h'si ( 3.300 ) kirişlerin dış
yüzleri arasıdır, program merkezler arası sayar.  Kasnağına ve kirişlerine
yetmeyen çerçeve, kabin tavanına giren üst kiriş ( gereken paten arası söylenir )
ve platforma giren alt kiriş reddedilir.

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
kapı boşluğu · kasa · eşik · kanatlar · açılış oku ( menteşeli kapıda açık konum
ve çeyrek yay — ISO 128 ince çizgi, kata açılır, "Manuel Sağ" kattan bakınca sağa
açılır, menteşe sağda ( kullanıcı 8 Eki;  DIN 107 ile aynı );  alttaki ölçü sıraları yayın altına iner;  8 Eki ), kabin
panosu ve şasesi ( dikmeler + alt/üst kirişler ), kabin rayları T profiliyle, ray
konsolları ( plaka + kol + cıvata delikleri ), kabin ve karşı ağırlık patenleri,
karşı ağırlık çerçevesi ve
kasnağı, karşı ağırlık rayları ve konsolları, askı kasnakları ya da askı
noktaları, eksenler, 46 ölçü ve çerçeve + künye şeridi.  Kumanda panosu
kuyuda değildir:  makine dairesizde kuyunun dışındaki acil panoda, makine
dairelide makine dairesinde ( eskiden kuyu planında kaynağı belirsiz bir
"PANO" vardı;  kesitlerde yoktu, makine dairelide çift oluyordu ).
**Kabin ile karşı ağırlık arası ölçülür** ( kullanıcı isteği 1 Eki — LiftDesigner
gibi;  eskiden hiçbir planda yoktu ):  yandaki ağırlıkta üstteki şase zinciri
duvar → ağırlığın çerçevesi → çerçeve → kabinin dış yüzü ( 4815-6:  100 · 150 · 225 ·
KABİN DIŞI — LiftDesigner'la birebir;  8 Eki'ye dek kabin + 2 × 30'luk "ŞASE DIŞI"
ve 195 );  arkadaki ağırlıkta soldaki zincir RAY EKSENİ · KABİN RAYI – AĞIRLIK
RAYI · ağırlık ekseni – arka duvar ( 800 KG:  840 · 980 · 180 — LiftDesigner
850 · 970 · 180, fark kapı bölgesinin 10'u ), sağdaki zincir kabin → çerçeve →
arka duvar ( 105 · 150 · 105 ).  Hesaba girmez ( m.5.2.5.5.1 h'nin 50'si
girdi.dogrula'da denetlenir );  ölçüye tıklanıp değiştirilebilir ( kaynakları:
kuyu derinliği, ray – kapı arası, ağırlık ekseni – duvar … ).  Kabinle ağırlık o
yönde ayrık değilse zincir bölünmez.
**Duvarlar ayrı ayrı** ( kullanıcı isteği 2 Eki ):  formda ortak "Kuyu duvarı
kalınlığı" ve "Gelişmiş"te ön · arka · sol · sağ duvar ( boşsa ortak kalınlık —
LiftDesigner projelerinde farklı:  800 KG ön · arka 200, yanlar 250;  4815-6 arka
250 ).  Planda dört duvar da ölçülür ( ön ve arka eskiden yalnız dış ölçünün
içindeydi );  "DUVAR" ölçüsüne tıklanınca yalnız o duvarın kutusu değişir
( ölçü kaynağı:  eşitlikte kuralla dolan alanın kendisi önce — `api/cizim._kaynaklar` ).
Kuyu dibinin ve makine dairesizde kuyu tavanının döşemesi ortak kalınlıktadır
( `kuyu.doseme`;  eskiden ön duvarınkiydi ).

**Kabin üstü planı** ( kabin tavanı hizasından yatay kesit ):  duvarlar, raylar,
konsollar ve karşı ağırlık kuyu planından aynen alınır ( ikinci kez
hesaplanmaz ).  **Kapı kesit kotuna göre** ( `kabin_ustu.kapi_gorunusu` ):  kesit
kabin iç + tavan kalınlığından geçer ( 2.000 + 60 = 2.060 ), kaba boşluğun üstü
kapı + 240 ( 2.240 ) — kesit boşluğun içindeyse ön duvar boşlukludur ve kasa
kesilir, üstündeyse duvar dolu, boşluk kesikli ( duvar boşluğuna monte kasa da ).
Kanatların üstü kesitin altındadır:  kat ve kabin kapısı ( eşik, kanatlar, cep )
yukarıdan görünür — LiftDesigner 1022'nin kabin üstü kesiti ( X-X ) gibi.  ( 5 Eki'ye kadar ön duvar hep
dolu çiziliyor, kapı bölgesi boş kalıyordu — kullanıcı "kapının görünmemesi
saçma". )
Tavanda:  kabin tavanı, şase dikmeleri ve **şasenin üst kirişi** ( ray ekseninde
dikmeden dikmeye;  kuyu planındaki kiriş zarfı, `sase_dikme_derinlik` 300 —
ÇİZİM KABULÜ, tedarikçi profili yok ), askı ( kabin üstünde kasnaklar · kabin altında
halatların tavan dışından geçtiği yer · doğrudan askıda askı noktaları ).
Standarttan hesaplananlar:

| Kural | Madde | Ne yapılır |
|---|---|---|
| Tavan kenarından duvara boşluk **> 0,30 m** ise korkuluk | m.5.4.7.2 b | Her kenar ayrı;  gerekli kenara küpeşte çizilir |
| Küpeşte kuyudaki parçalardan **≥ 0,10 m** | m.5.4.7.4 d | Gerekirse kenardan içeri alınır, ölçüsü yazılır |
| Küpeşte kenardan **≤ 0,15 m** içeride | m.5.4.7.4 c | Aşılırsa çizim reddedilir |
| Yükseklik:  küpeşte – duvar **≤ 0,50 m → 0,70 m**, aşarsa **1,10 m** | m.5.4.7.4 b | Küpeştenin yanına yazılır |
| Sığınma alanı **0,40 × 0,50** ( dik duruş ) / **0,50 × 0,70** ( çömelme ) | m.5.2.5.7.1 · Çizelge 3 | Korkulukların içinde, operatör, şasenin üst kirişi, kasnaklar ve aralarındaki halat ( `hareketli.kabin_parcalari` ) dışında, kapıya en yakın yere konur ( 25 mm adımla;  dar boşlukta engelin kenarına yaslanarak );  yer yoksa reddedilir |

Kabin kapısı operatörü **çizilmez** ( LiftDesigner 1022 X-X da çizmez;  kullanıcı
kararı 5 Eki ), yerleşimde engeldir:  enine kanatların yolu ( kapı + cep, dar
kabinde tavandan taşar ), derine tavanın üstünde kabin kapısı mekanizma kutusu
boyu 140, önde kabin eşiğinin ön kenarına kadar;  korkuluk ve sığınma alanı onun
dışında kalır, taşan ucu kuyudaki bir parçaya değerse çizim reddedilir.
Ayrıca:  kabin altı askıda halat kuyudaki bir parçanın içinden geçemez;
kabin üstü kasnağı korkuluğun yolunu kesemez;  yan korkuluk kapı operatörünün
arka yüzünden başlar ( eskiden tavanın bütün derinliğince çiziliyor, ön dikmesi
operatörün içinde duruyordu );  kabin rayı ekseni kabinin derinliği içinden
geçmelidir.
Çizilmeyenler:  revizyon kutusu ( tedarikçi ölçüsü yok ), etek tahtası ( planda
tavan kenarıyla çakışır ).  ( Üst kiriş 3 Eki'ye kadar çizilmiyordu:  kullanıcı
"kabin üstü kesitinde süspansiyon görünmeli".  Sığınma alanının yer ölçüleri
kirişe binmeyen sıraya, korkuluk yazısı kirişin dışına konur.  **Sığınma alanı kirişin altına girmez**
( kabin altı ve doğrudan askıda;  kullanıcı kararı 4 Eki ):  çömelme hacmi
1,0 m yüksektir, kiriş tavandan ~0,2 m yukarıdan geçer.  Eskiden alan kirişin
altına giriyordu ( gerçek projelerde 30 – 300 mm, 1022 ve 800 KG'de tamamen );
şimdi kirişin önüne / arkasına kayar — dört gerçek projede de sığar,
yükseklikler aynı kalır.  320 kg'ın ( 900 × 1.000 ) yan ağırlıklı 2:1
düzenlerinde kiriş tavanı ikiye böler, çömelme alanına yer kalmaz:  çizim
söyler ( kirişin eni `sase_dikme_derinlik` 300 — ÇİZİM KABULÜ;  tedarikçinin
şasesi darsa Sabitler'den küçültülür ).  Hesabın referans taraması bu yüzden
yeniden üretildi ( yalnız 320 kg'ın sığınma ara değerleri ).  **Kabin üstü
askıda henüz sayılmaz:**  kasnaklar askı ekseninde, kiriş ray ekseninde iki
ayrı bant olur, tavan dar şeritlere bölünür ( köprü testinin düzeninde 461 · 54 ·
386 mm ) ve kabin üstü askılı düzenlerin çoğu, 12495-18 de, "yer yok" derdi.
Gerçekte kasnaklar genelde kirişin üstüne oturur;  kasnaklar kirişe alınınca
kural oraya da uygulanır. )

**Kuyu planında ( C-C ) askı:**  plan kabinin ortasından kesilir, yukarıdan
bakılır.  Şase dikmeleri kesilir ( düz );  üst kiriş, kabin üstü kasnaklar ve 1:1
bağlantısı kesitin üstünde, alt kiriş ve kabin altı kasnaklar ile taşıyıcıları
kabin döşemesinin altında kalır:  **kesik çizgiyle** ( GIZLI ) çizilir, askı
ölçüleri yerinde kalır.  Kabin altı kasnağın kabinin dışına taşan ucu açıktadır,
düz çizilir ( halat oradan iner ).  LiftDesigner'ın kuyu planı şase kirişlerini
hiç çizmez, kabin altı kasnağın yalnız dışarıdaki ucunu çizer ( 4815-6 );
referans projenin yatay kesiti kabin altındakileri kesik çizer.  Eskiden hepsi
düz çiziliyor, şase ve kasnaklar kabinin içinden geçiyor görünüyordu ( 3 Eki,
kullanıcı:  "kabin içinden geçen kesitte süspansiyon görünmemeli" ).

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
yer yoksa kutu sığınma alanının yüzeyine binebilir, o da olmazsa kuyunun
**dışına**, duvarın en az 20 mm ötesine — ok yine noktayı gösterir;  yazılar
büyüyünce dört düzen içeride yer bulamıyordu ).  Kuvvet tablosu kutulardan sonra,
hepsinin sağına konur.  Perde etiketi okların arasına kayar, sığmazsa kısalır.  Değerler `kuyu_dibi.kuvvetler`'den ( N );
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
| Perde ucu ile duvar arası 0,30 m'yi aşarsa o bölge de korunur | m.5.2.5.5.1 e | Perde o yanda duvara ya da araya giren ilk sabit parçaya ( konsol, kabin rayı, tampon, gergi, en alt durağın kapı ünitesi ) uzar;  perde ile duvar arasında kalan bölgede merdiven durmaz.  Eskiden perde rayların hizasında bitiyordu:  54 standart düzenin 50'sinde ucu ile duvar arası 340 – 365 mm kalıyordu |
| Kabin ile karşı ağırlık arası **≥ 50 mm** | m.5.2.5.5.1 h | Kuyu planının doğrulamasında ( önce 20 mm'lik bir çizim kalkanıydı ) |
| Sığınma alanı **0,40 × 0,50** / **0,50 × 0,70** / **0,70 × 1,00** | m.5.2.5.8.1 · Çizelge 4 | Önce kabinin izinin altında, tampon / gergi / merdiven, kabin altı kasnaklarıyla aralarındaki halat ve sığınma yüksekliğine inen kabin parçaları ( alt şase kirişi … ) dışında, kapıya en yakın yere;  sığmazsa kuyu tabanının başka yerinde ( madde yalnız "kuyu tabanında" der ), karşı ağırlığın şeridine girmeden.  25 mm'lik ızgaraya sığmayan dar boşlukta alan engelin kenarına yaslanır |
| Kuyu dibi **≤ 2,50 m** ise merdiven, aşarsa erişim kapısı | m.5.2.2.4 | Merdiven yalnız 2,50 m'ye kadar çizilir |
| Merdiven kat girişinin kenarına **≤ 800 mm** | Ek F.5 b | Kapıya yakın yan duvara yaslanır;  yan duvar uzaksa ön duvara, kapının yanına ( kapıdan 25 mm adımla en çok 800 );  ikisi de olmazsa reddedilir.  Ölçüsü 350 × 100 ( Ek F.3 ) |

Regülatör gergi kasnağı seçilen yandaki kabin rayının hizasında, ray
ekseninin arkasında durur ( girdi:  yan, eksene uzaklık, kasnak çapı ).
Eksene uzaklık boşsa program, gergi kolu ve ağırlığı tampona ya da raya,
regülatör tepede makineye ya da bağlantılara çarpmayan en yakın yeri seçer;
ağırlık arkadayken yan "karşı ağırlığın karşısı" ise öbür kabin rayını da dener.
Girilen değer değiştirilmez ( çarpıyorsa çizim söyler ).  Gergi kasnağı en
alttaki ray konsolunun hizasındadır ( konsol 440 – 500, kasnak 520 ± D/2 ):
kasnak konsola değiyorsa program onu raydan uzaklaştırır ( 1022:  280'de
değiyor, 360 ).
Çizilmeyenler:  kuyu dibi durdurma düğmesi ve revizyon kutusu ( yer kuralları
m.5.2.1.5.1 — ölçüleri yok ).

**Kuyu üstü planı** ( makine dairesiz — kuyu tepesinden yatay kesit;  referans projenin
MRL paftasındaki "Machine Room" çizimi ):  duvarlar, raylar, konsollar kuyu
planından;  kabin, karşı ağırlık ve kat kapısı yalnız izleriyle ( kesik ).

- **Halatlar düşey iner.**  Tahrik kasnağının bir teğeti kabinin yakın
  halatının ( kabin kasnağının dış teğeti ) hizasındadır;  öbür teğetinden inen
  halat karşı ağırlık kasnağının teğetine düşmelidir.  Düşmüyorsa sapma
  **HALAT SAPMASI** ölçüsüyle gösterilir.  Referans projede birebir tutar:
  370 − 240 = 130 ( ağırlık ekseni ).  Kabin kasnakları arası boşsa program
  onu halat ağırlığa düşey inecek biçimde seçer ( sapma 0, α çizimden 180° );
  halat kabinin panosuna ya da ray ara kirişine çarpacaksa eski kural
  ( kabin genişliği + 30 — halat eğik iner, α girilir ).
- **Makine** tahrik kasnağının ağırlık eksenine bakan tarafında;  **halat
  bağlantıları** ağırlık kasnağının öbür teğetinin ve kabinin uzak halatının
  üstünde;  **regülatör** kuyu dibindeki gergi kasnağının tam üstünde.
- **Acil kurtarma ve test panosu** ( m.5.2.6.6 ) kuyunun dışında, en üst katta
  kapının seçilen yanında;  önünde **0,70 m** derin, **en az 0,50 m** ya da pano
  eni kadar çalışma alanı ( m.5.2.6.6.4 → m.5.2.6.3.2.1 a ).
- Ölçüler referans projenin makinesinden ( `sabitler.py` ):  kasnak 240 × 105, gövde
  298 × 279, bağlantı plakaları 264 × 120 ve 127 × 200, regülatör 80 × 300
  ( gövde 130 × 180 ), pano 400 × 300.  Başka makinede katalogdan değiştirilir.
- Karşı ağırlığın ekseni artık girdidir ( `agirlik.eksen_kaciklik`, referans proje
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
| Dişlisiz | 4815-6 ( MRL ) | kasnak ekseni üstünde:  kasnak · göbek ø100 × 15 · flanş ø220 × 28 · yatak flanşı ø320 × 50 · gövde ø400 × 206 · fren ø320 × 70 · fren diski ø240 × 18 · enkoder ø270 × 102 ( toplam 489 ) + klemens kutusu.  Biçim bu;  ölçü projenin makine ZARFINA oranlanır ( referans projenin makinesi ø298 × 279 ve kotları ölçülü ) |
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
| 2 yan yatak | kuyu üstü | `makine.yan_yatak` ( referans proje:  UPN 200, Wx 191 cm³ ) | karşı ağırlık rayları boyunca, sırtları dışta, raylara oturur ( mesnet aralığı raylar arası — hesabın L'si;  referans proje 850 );  aralarında üstle aynı hizada 700 mm motor plakası, uçlarda bağlantı levhaları.  Plakadan inen halatlar ( karşı ağırlık tarafı ve bağlantısı ) için plakada delik ( eskiden deliksiz plakanın içinden geçiyorlardı ).  Şase üstü referans projeninki ( tavandan 595 ), altı profil yüksekliği kadar aşağıda |
| Kaide | makine dairesi ( HER ZAMAN — hesap burada kolonların burkulmasını da denetler ) | `makine_dairesi.sase_yuksekligi` · `dikine_kiris`, `makine.yan_yatak` | dört dikine kiriş ( kolon ) döşemeden şase yüksekliği kadar, üstleri hizasında iki yan yatak makinenin uzun ekseni boyunca;  dikine kirişlerin eksenleri arası = hesabın L'si ( çizimden ).  Kaide makinenin ve saptırma kasnağının izini her yana 100 sarar ve halatlara ortalanır ( yukarıda "Makine kaidesi" ).  Uçlarda kısa kirişler UPN 100 ve ayak plakaları 150 × 150 × 20 ( LiftDesigner 12744-3 ).  Makine yan yatakların arasındaki, üstleri hizasındaki **makine plakasına** oturur ( yük iki yan yatağa — hesabın F / 2'si;  eskiden plaka yoktu, makine iki kirişin arasında havada duruyordu );  plakayı kesen halatlar için delik, eğik saptırma halatı için kestiği yerde delik, plakanın altına sarkan tahrik kasnağı için yuva;  saptırma kasnağının askıları plakaya asılır.  Ayak plakası bir döşeme deliğine basıyorsa pay büyür ( 200, 300 — önce enine );  oda, pano önü ve bakım alanı yer vermiyorsa kaide ortaya en yakın konumu alır |

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
| Döşeme delikleri **amacı için en küçük** | m.5.2.6.3.3 | Halat demeti ( n halat, aralık 1,6 · dh ) + çevresine `halat_delik_payi` ( 30 mm, çizim kabulü );  regülatör halatı da aynı kuralla:  `kuyu_dibi.regulator_halat_capi` + 2 × pay ( referans proje ø6 → 66 × 66;  eskiden LiftDesigner'ın 200 × 200'ü — ø240 regülatörde iki delik arasında 40 mm, duvara 14 mm kalıyordu ) |

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
dairesi planı F-F ).  Kabinin düşey ölçüleri **ofisin LiftDesigner kabininden**
( kullanıcı kararı, 5. adım — altı projenin altısında aynı ):  iç 2.000 ( varsayılan ),
tavan 60, taban 50, şase altı −320, alt paten merkezi şase altının 50 üstünde
( `alt_paten_payi`:  −270 ), üst paten merkezi alt patenin paten arası kadar üstünde
( varsayılan 2.660:  2.390 ), paten 100, alt ve üst kiriş 140 ( `sase_alt_kiris`,
`sase_ust_kiris` ), fren bloğu 270 ( en alt parça −320 ), kabin
altı kasnak merkezi −425, eni 75, yan pano 15, arka pano 20;  etek ( önlük,
m.5.4.5 ) kabin eşiğinin kat tarafındaki kenarında, dik kısmı 750, altında 20 × 35
pah ( 60,3° ):  en alt noktası −785 ( 7 Eki;  eskiden kabinin ön yüzündeydi, pahsız,
−750 — kuyu dibi açıklığı 35 mm iyimser çıkıyordu ).  Paten arası 2.660 LiftDesigner'ın
( 8 Eki'ye dek 2.420 — kirişleri paten sanmıştık );  Has Asansör MRL şase kılavuzunda
aralık kabin yüksekliği + 200 – 400.  Referans projenin örneği kendi kabiniyle
çizilir ( `sabitler.REFERANS_PROJE_KABINI`:  taban 120, şase altı −480, alt paten
şase altının 70 altında ( −620 / −480 ), paten 140, alt kiriş 350, üst kiriş 200,
fren bloğu 350, kasnak −295 / 92, pano 45 / 33;  iç 2.250, paten arası 3.300 ).

| Açıklık | Madde | En az |
|---|---|---|
| Kuyu dibi sığınma yüksekliği | m.5.2.5.8.1 · Çizelge 4 | 2,00 / 1,00 / 0,50 m |
| Kuyu tabanı – kabinin en alt kısmı | m.5.2.5.8.2 a | 0,50 m |
| Kuyu tabanı – etek ( önlüğün pahının ucu ) | m.5.2.5.8.2 a 1 | 0,10 m |
| Kuyu tabanı – şase / paten / fren bloğu ( raya yakın ) | m.5.2.5.8.2 a 2 · Şekil 7 | 0,10 m |
| Kabin üstü sığınma yüksekliği | m.5.2.5.7.1 · Çizelge 3 | 2,00 / 1,00 m |
| Üst paten – 0,40 m yakınındaki tavan parçası | m.5.2.5.7.2 b | 0,10 m |
| Korkuluk – kabin izdüşümündeki tavan parçası | m.5.2.5.7.2 c 1 | 0,30 m |
| Korkuluk – korkuluğun dışındaki tavan parçası | m.5.2.5.7.2 c 1 | 0,10 m |
| Kabin üst pateni – rayın üst ucu ( kabin en üstte ) | m.5.2.5.6.2 | 0,10 m |
| Karşı ağırlık üst pateni – rayın üst ucu ( ağırlık en üstte ) | m.5.2.5.6.2 | 0,10 m |

Korkuluk açıklığı kenar kenar ölçülür:  her kenarın küpeştesi kendi
yüksekliğiyle ( 0,70 / 1,10 ) kendi üstündeki en alçak parçaya ( eskiden en
yüksek korkuluk bütün kenarlara uygulanıyordu;  yan panolar incelince gereken
0,70'lik yan korkuluklar yanlışlıkla reddediliyordu ).

**"Kuyu tavanının en alt kısmı" tavanın altındaki parçaları da kapsar**
( m.5.2.5.7.2 ):  makine dairesizde makine şasesi, kabin ve ağırlık halat
bağlantıları, regülatör.  Her açıklık kendi üstündeki en alçak parçaya
ölçülür ( `donanim.tavan_engeli` );  örnekte paten ve korkuluk şaseye,
sığınma kuyu tavanına gider.

**Hareketli parçalar tek tanımdan** ( `cizim/hareketli.py`, 10 Eki ):  kabinin
ve karşı ağırlığın her parçası ( kabin tabanı, şasenin alt / üst kirişi,
dikmeler, patenler, fren bloğu, kasnaklar ve aralarındaki halat — çapraz
düzende çapraz şerit —, 1:1 halat bağlantısı;  ağırlığın çerçevesi, patenleri,
kasnağı ) plandaki izi ve alt / üst kotuyla.  Sığınma alanları, açıklıklar ve
çarpışmalar bu listeden okunur:  kuyu dibinde alan, sığınma yüksekliğine inen
parçaların ( alt şase kirişi … ) dışında aranır, yüksekliği üstündeki en alçak
parçaya ölçülür ( hesapta parçanın adı yazılır );  "kabinin en alt kısmı"
şasenin alt kirişini de sayar ( raya yakın patenler ve fren bloğu ayrı —
m.5.2.5.8.2 a 2 );  kabin üstünde şasenin üst kirişi, kasnaklar ve aralarındaki
halat her askıda engeldir.  Karşı ağırlık en üst konumunda ( kabin tam
ezilmiş tamponunda + 0,035·v² ) her parçası izinin üstündeki en alçak tavan
parçasının ( makine şasesi, bağlantılar, tavan kirişi payı ) altında, tamponu
tam ezilmişken kuyu tabanının üstünde kalmalı;  kalmazsa çizim durur, bölüm 11
UYGUN DEĞİL der.  Eskiden kuyu dibinde yalnız kabin altı kasnakları, kabin
üstünde yalnız kasnak kutuları sayılıyor, karşı ağırlığın yalnız makine
dairesizde makine şasesine çarpması denetleniyordu ( denetim 8–10 Eki:  alt
kiriş sığınma alanının üstünde, çapraz halat kabin üstündeki alanın içinde,
ağırlığın kasnağı tavanda, alt pateni tabanın altında — hepsi UYGUN çıkıyordu ).
Sonuç:  arkadaki ağırlıkla 2:1'de ( çapraz kasnaklar ) standart kabinlerden
320, 450 ve 630 kg'ınkilerin ( 1.100 × 1.400'e kadar ) tavanında çömelme
alanına yer kalmaz;  kabin üstü askıda kasnaklar kirişten
ayrı bir bantta kalırsa ( askı noktası ray ekseninden uzak ) tavan dar
şeritlere bölünebilir.

**Kuyu dibi zinciri kabinle kapanmalı:**  kaide + tampon + çarpma arası +
şase altı = kuyu dibi ( referans proje:  764 + 160 + 96 + 480 = 1.500 );  tutmazsa
reddedilir.  **Hesap programıyla fark:**  onun sığınma satırları ofisin
paylarıyla hesaplanır ( üst paten bir satırda 2.700, bir başkasında 2.900;
varsayılan girdiler şase altını örtük 350 alır ) — bu kabin modeline göre
düzeltilene kadar iki program aynı açıklığa farklı sayı verir.

**Kabinin üst şase kirişi kabin tavanının üstünde kalmalı** ( 1 Eki ):  kiriş
üst patenin hemen altındadır;  kabin iç yüksekliği paten arasına göre büyükse
( 2.500 iç yükseklik, 2.660 paten arası:  gereken 3.020 ) çizim durur ve gereken
paten arasını söyler — girilen ölçü değiştirilmez.  Alt kiriş de platforma
girmemeli ( Sabitler'in şase ölçüleri çelişirse çizim durur ).  **Karşı ağırlığın patenleri raylarını
kavrar** ( `baglantilar.agirlik_patenleri`, kabin patenleri gibi ray yüzünde ):
eskiden arkadaki ağırlıkta da çerçevenin önüne / arkasına konuyor, raydan
uzakta duruyordu.  Kabin üstü kasnaklarına taşıyıcı çizilmez ( kaynağı yok —
kullanıcı kararı 1 Eki );  kabin altı askının taşıyıcısı ölçüsüz bağlantı
yoludur ( `baglantilar.kasnak_tasiyicilari` ).

**Kasnak düzenlemesi ve giriş görünüşü** ( 1/20 — kullanıcı isteği 1 Eki:
"LiftDesigner örneklerinde bunlar da var, biz de ekleyelim" ):  paftanın ve
ekranın sonunda.

- **Kasnak düzenlemesi** ( `kasnak_duzeni.py` ):  tahrik kasnağının ekseni
  boyunca ( kasnak daire görünür ) makine ve kaidesi ( makine dairesizde
  şasesi ), saptırma kasnağı, makine dairesinde döşeme ( üstünden 300, altı
  kırık çizgi ), halatların inişleri ( KABİNE · AĞIRLIĞA ), tahrik kasnağında
  halatın sardığı yay ve SARIM AÇISI ( hesabın kullandığı — `kopru.sarim_acisi` ).
  Ölçüler:  Ø D1, Ø Ds, merkezler arası ( yatay, düşey ), HALAT ARASI ( iki
  iniş — LiftDesigner RDA / RDB;  makine dairesinde döşeme deliklerinin arasıyla
  aynı ), merkezlerin döşemeden ( makine dairesizde kuyu tavanına ) yüksekliği.
  Düşey kesitlerin yerleşiminden çizilir.  LiftDesigner'la:  800 KG ( Ø500 /
  Ø400 ) 152,1° / 151°, 1022 ( Ø480 / Ø400 ) 153,0° / 152°;  merkezler arası
  530 / 520, halat arası 980 / 970 ( 10 mm:  kapı bölgesi farkı ).  Makine
  dairesizde LiftDesigner "Sarım açısı 0" yazar — burada 180°.  Her projede
  aynı 1.600'ü çizilmez ( anlamı belli değil ).
- **Giriş görünüşü** ( `giris.py` ):  en alt durağın kapısı, ön duvara durak
  tarafından bakılarak ( x planınki — durakta duranın sağı +x ):  kuyunun iç
  yüzleri ( kesik ), duvardaki kaba boşluk, kasa, kanatlar ( otomatikte iki,
  ortada birleşir;  elle açılanda tek ), eşik plakası, kat göstergesi, kat butonu
  ve duvardaki yuvası ( kesik ), kapı ekseni, döşemenin kotu.  Ölçüler
  LiftDesigner'ın "Giriş"inin kuralıyla ( kullanıcı kararı ):  kaba boşluk
  kapıdan 2 × 140 geniş ( `kaba_bosluk_yan_payi` ), 240 yüksek ( `kapi_ust_payi`
  — eskiden 200, referans proje;  referans projenin örneği kendi 200'ünü
  korur ), kasa üstü kapının 220 üstünde ( `kasa_ust` ), eşik 50 ( eskiden 30,
  kaynaksız ), gösterge 500 × 124 kapının 100 üstünde, buton kutusu 90 × 240
  ortası 1.200 ve kapının kenarından 240, yuvası 160 × 290.  800 KG ve 1022'de
  LiftDesigner'ınkiyle birebir:  470 · 1.180 · 350 ve 235 · 1.180 · 585,
  KAPI BOŞLUĞU 2.240.  ÇİZİM KABULÜ:  kat butonu kapının açıldığı yanın
  karşısında ( "Sağ"a açılıyorsa solda ).  Çizilmeyenler ( anlamları belli
  değil ):  LiftDesigner'ın kapının yanındaki kesikli 100 mm'lik dikdörtgeni,
  2.500'deki çizgisi, kasanın ve eşiğin bağlantı noktaları.

**Tam boy kuyu düşey kesitleri** ( 1/50, `kuyu_kesiti.py` ):  LiftDesigner'ın
"Dikey 1:50"si gibi gerçek ölçekte, bütün duraklarla ( referans proje ara katları
kırarak 1/30 çizer ).  İki kesit, planda A-A ve B-B işaretleriyle:

| Kesit | Bakış | Kabin | Karşı ağırlık |
|---|---|---|---|
| A-A yan | kuyu derinliği boyunca, kabin ekseninden karşı ağırlığa;  kat kapıları solda | en alt durakta | seyir kadar yukarıda |
| B-B ön | kuyunun arkasından kat kapılarına ( plandaki sol sağda görünür ) | en üst durakta | tamponunun çarpma arası üstünde |

**Kabin opaktır** ( `kesit_parcalari.kabin_arkasi`, 4 Eki ):  bakış yönünde kabinin
uzak yüzünün ötesinde kalan parçalar ( A-A'da ağırlık rayları, konsollar,
halatlar, regülatör halatı;  B-B'de en üst durağın kat kapısı, kasası ve durak
numarası ) kabinin görünüşü içinde ( kabinin izi × taban altı – tavan )
çizilmez — kabinin altında ve üstünde iki parça kalırlar.  A-A'da **kabin rayı ve
şase** kabinin üstünden görünür:  referans projenin yan kesitinin düzlemi rayın
ekseninden geçer, LiftDesigner da rayı ve şaseyi kabinin üstüne çizer;  arkada
kalan halatı ikisi de kabinin hizasında keser.  Eskiden kabinin yalnız SVG'deki
beyaz dolgusu örtüyordu:  ekranda gizli olan raylar, konsollar ve kat kapısı DXF'te
( DWG, pafta ) kabinin içinden geçiyordu, ekranda ise kabin rayı da gizleniyordu.

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
görünür ( referans proje de iki yan kesitte ayrı gösterir ).  B-B kabinin arkasından
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
yüksekliği ( referans proje:  1.500 + 29.000 + 5.000 = 35.500 );  sağda konsol
zinciri tabandan tavana ( ilk konsol, konsollar arası, ray ucu ), A-A'da
makine ( şase = yan yatak 200 · makine 345 · tepe 250 ), B-B'de karşı ağırlık ( çarpma
arası, çerçeve );  altta kuyu derinliği / genişliği.

Kuyu tepesi ve karşı ağırlığın kotları referans proje kesitlerinin vektörlerinden
ölçüldü ( `sabitler.py`, "KUYU ÜSTÜ DONANIMININ DÜŞEY ÖLÇÜLERİ" );  planda
aynı parçaların yeri kuyu_ustu.yerlesim'dekiyle birebir tuttu.  Makinenin
yeri `makine.yeri` ( "Kuyu üstü" / "Makine dairesi" ).

Kuyu tavanının en alt kısmı ( hesap programının "kuyu tavanı payı", 150:
kirişler vb. ) bir KABULDÜR:  kesitte kesik bir sınır çizgisi olarak çizilir
( eskiden taralı bir beton katman gibi çiziliyor, tavan iki kat kalın
görünüyordu ).  Raylar ona değmez:  şasede bitmeyen raylar bu çizginin
`kabin_rayi_tepe` ( 50, referans projede tavanın 50 altı ) altında biter — eskiden
uzak kabin rayı ( makine dairelide bütün raylar ) çizgiye tam değiyordu.

**Makine daireli projede** oda kuyunun üstündedir ( plan yeri
`makine_dairesi.x · y · genislik · derinlik` ).  Kuyunun üstündeki beton hesap
programının **tabliyesidir** ( `makine_dairesi.tabliye` ):  kuyunun üstünü kuyu
döşemesi kalınlığında beton kapatır, makine, bağlantılar ve regülatör onun
üstündedir;  oda zemini tabliyenin üstünden `tabliye_yuksekligi` ( "Tabliye
beton yüksekliği";  zemin tabliyeyle aynı hizadaysa 0 — köprü 10 Eki'ye dek
reddediyordu ) kadar aşağıdadır — LiftDesigner'ın makine daireli üç
projesi ( 1022 · 1275 · 800 KG ):  tabliye 1.200 zeminden, döşeme 120, en üst
durak + son kat = kuyu tavanı = zemin + 1.200 − 120.  Kesitte "TABLİYE" ölçüsü
zeminden tabliyenin üstüne;  oda zemini yalnız kuyunun dışında.  Kumanda
panosu ile önündeki çalışma alanı tek kotta, makinenin başındaki bakım alanı
ve kaide tabliyenin üstünde ( kaide sığmazsa tabliyeye kaydırılır, o yanda
payı daralır );  kapının önü tek kotta.  Temiz yükseklik zeminde ve
tabliyenin üstünde ≥ 2,10 m;  kot farkı 0,50 m'yi aşarsa planda merdiven ve
korkuluk notu ( m.5.2.6.3.2.4 ), tabliye ile duvar arasında 0,05 – 0,50 m
kalırsa "üstü örtülür" notu ( m.5.2.6.3.2.5 ).  ( 5 Eki'ye kadar tabliye kuyu
tavanının üstünde 1.200 kalın beton sanılıyor, oda zemini onun üstüne
konuyordu — kullanıcı "tabliye beton yüksekliği betonun kalınlığı mı?". )
Öbür girdiler:  `yukseklik` ( temiz;  LiftDesigner "477-8" 3.500 ),
`kapi_yukseklik` ( standardın en azı 2.000 );  çatı 150 ( LiftDesigner,
`md_cati_kalinlik` ).  Makine kaidede ( yukarıdaki tablo;  kesitte "ŞASE" ),
halat bağlantıları ve regülatör tabliyede,
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

Ölçüler referans projenin kuyu planı vektörlerinden ve "Door Detail 1/35" paftasından:
kat kapısı ünitesi kasa 60 + eşik 90;  kanatlar 40 kalın ve **EŞİĞİN ÜSTÜNDE**
( teleskopikte iki düzlem, 45 arayla );  kabin eşiği 90, kabin kapısı
kanatları onun üstünde.  `kapi.montaj`:

| Montaj | Kasa | Kat eşiği | Kapı hattı | m.5.2.5.3.1'in "kuyu iç yüzü" |
|---|---|---|---|---|
| Duvar boşluğuna | −60 – 0 ( duvarda ) | 0 – 90 | 90 | duvar |
| Kuyu içine ( referans proje ) | 0 – 60 | 60 – 150 | 150 | kapı hattı ( kapı altı / üstü sac kaplama ) |

Açıklıklar kabin EŞİĞİNİN ön kenarından ölçülür:  eşik aralığı 0 – 35 mm
( m.5.3.4.1 ), kuyu yüzü – kabin eşiği ≤ 150 ( m.5.2.5.3.1 ).  `kabin_ray.kapi_arasi`
kuyunun ön İÇ yüzünden ölçülür — hesap programının RK'sı kapı hattındandır
( referans proje:  iç yüzden 1.167 = kapı hattından 1.017 ).

**Duvardaki kaba boşluk ve kasa her görünüşte aynıdır** ( `girdi.kaba_bosluk`;
1 Eki ):  boşluk kapıdan iki yanda 140 geniş, döşemeden 2.240 yüksek ( kapı
+ 240 ) — LiftDesigner 800 KG'nin planında ve giriş görünüşünde 470 · 1.180 ·
350;  kasa yanda 120, kapının 220 üstüne ( 2.220 ).  Eskiden planda boşluk
yalnız kapı genişliği kadardı ( 900 ), kasa yan kesitte kapının boyunda bitiyor
( 2.000, üst başlığı yoktu ), arkadan kesitte 2.240'a çıkıyordu.  Duvar
boşluğuna montajda kasa boşluğa sığmalıdır ( Sabitler'deki paylar kasadan
küçükse çizim durur — referans projenin 200'lük üst payına 220'lik kasa
sığmaz;  onun kapısı kuyu içindedir ).

Kapının olduğu duvar boşluğun iki yanında iki parçadır, tarama boşluktan
geçmez:  kuyu planında ( C-C, kapı hizası ) ön duvar kaba boşlukta ( duvar
boşluğuna montajda kasa da boşlukta ), A-A'da kapı ünitesi duvardaysa boşluk
eşiğin altından başlar, makine dairesi planında oda kapısında.  Kapının üstünden
ya da altından kesilen planlarda ( kabin üstü, kuyu dibi, kuyu üstü, delik
planı ) ön duvar kesintisizdir ( `geometri.plan(…, kapi_duzeyi=False)` ).

### Kapı parçalarının biçimi ( 6 Eki )

Üç üreticinin kapı detaylarının ortak biçimi ( Wittur Hydra teknik broşürü
s.7–8 · 17, Merih B-01 MLT kataloğu, KONE planlama kılavuzu ) — `parcalar`:

* **Kasa:**  sac bükme profil;  kat tarafında yüz, açıklığın kenarı boyunca
  derinliğe dönüş ( eşiğin önünde biter ), dış kenarda duvara kanca.  Wittur'un
  standart kasa derinliği 60 = programınki.
* **Eşik:**  cebin altından da süren tek parça ( Fermator 40/10:  T2 eşiği
  1,5·PL + 40 ) — eşik ile cep arasında çizgi yoktur.  Her kanat düzleminin
  kılavuz oluğu ince çizgiyle, kanadın ve durdurucunun örtmediği yerde
  görünür;  menteşeli kapıda oluk yoktur.  Derinlikler üreticilerle tutar:
  2 kanat teleskopik 90 ( Wittur 90 · Merih 95 ), 3 kanat 135 ( Wittur 136 ·
  Merih 135 );  üreticilerin eşik aralığı Wittur 30 – 35, Merih 30
  ( standardın sınırı 35 — yukarıda ).
* **Kanat:**  sac tepsi;  düz yüz kat kapısında kata, kabin kapısında kabine
  bakar, uçlar dönük, arkada dudak.
* Kasa ve kanat dudağı 20 · 15, oluk eni 10:  üreticilerin çizimlerinde
  ölçülü değil, oranlarından — ÇİZİM KABULÜ ( `parcalar.KASA_DUDAK`,
  `KANAT_DUDAK`, `OLUK` ).

### Kapı yan kesiti ( 7 Eki )

`cizim/kapi_kesiti.py` — LiftDesigner'ın "Front Entrance Side View"ü ve Wittur'un
kat kapısı montaj kesiti ( SB.2.007539 s.17 ) gibi, en alt durağın kapısının
ortasından düşey kesit ( 1/20, paftanın sonunda ):  kat tarafındaki duvar ve
döşeme, kasa, üst kutu ( kasanın üstüne — 2.220;  içindeki askı mekanizması
kesik ) ve onu duvara bağlayan L konsol, oluklu eşik ve L konsolu ( Wittur
standart konsolu 205 ), kanatlar;  kabin durakta:  kabin eşiği, kanatlar, önlük.
Yerler planla aynı kaynaktan ( `girdi.kapi_bolgesi`, kanat düzlemleri ) —
kanatlar planla birebir aynı yerde ( test ).  Standardın iki parçası:

| Parça | Madde | Çizilen |
|---|---|---|
| Eşik altı sacı | m.5.2.5.3.2 · m.5.3.8.1 | Eşiğin kuyu kenarından iner:  en az kilit bölgesinin yarısı + 50;  kilit bölgesi otomatik kapıda ±0,35'e kadar olabildiği için ( bilinmiyor — emniyetli yön ) 400, elle açılanda 250;  sonra 60° pahla duvara ( d 2 ) |
| Kabin önlüğü | m.5.4.5 | Kabin eşiğinin kat tarafındaki kenarından, dik kısmı döşemeden 750;  altında 60°, 20 mm pah, kabine doğru |

### Kanat sayısı ve kanat cebi ( 3 Eki )

Otomatik kapının kanatları açılınca kapı boşluğunun yanında üst üste durur:
kat ve kabin kapısı ünitesi o yanda **bir kanat eni + 30** uzanır ( kanat cebi,
`girdi.kanat_cepleri`;  `Sabitler › kanat_cebi_payi` 30 ).  Kaynaklar:

* LiftDesigner'ın altı projesi ( 2 kanatlı teleskopik ):  DW 800 → 430,
  900 → 480, 1.100 → 580 — çizimimiz dördünde birebir aynı yerde ( `testler/test_kapilar.py` ).
* Fermator 40/10 katalogu:  kanat eni PL / n + 39, ünite eni T2 1,5·PL + 40,
  T3 1,35·PL + 40, T4 1,25·PL + 40, C2 2·PL + 40, C4 1,5·PL + 40 — aynı kural
  3 ve 4 kanat için de geçer.
* Referans proje ( Door Detail 1/35 ):  2 kanatlı teleskopik, 900'lük kapıda ünite 1.390 – 1.400.

Tip `kat_kapisi_tipi`'nden okunur ( `girdi.kapi_tipi` ):

| Tip | Kanat | Düzlem | Cep | Eşik |
|---|---|---|---|---|
| Teleskopik Sol / Sağ | 2 | 2 | açıldığı yanda DW/2 + 30 | 90 |
| Teleskopik 3 Kanat Sol / Sağ | 3 | 3 | açıldığı yanda DW/3 + 30 | 135 ( Fermator T3 ) |
| Otomatik Merkezi | 2 | 1 | iki yanda DW/2 + 30 | 90 |
| Otomatik Merkezi 4 Kanat | 4 | 2 | iki yanda DW/4 + 30 | 90 |
| Manuel | 1 | 1 | yok ( ok çizilmez ) | 90 |

Eşik = 90 + ( düzlem − 2 ) × 45 ( kanat aralığı );  kabin eşiği de aynı.
Teleskopikte cebe en yakın kanat duvar tarafındaki düzlemdedir.  Planda cep
ile her düzlemin durdurucusu çizilir;  B-B'de düzlem ayrımları, kabin üstü
planında operatör cebin üstüne uzanır.  Yeni üç tip hesap programının kapı
listesine de eklendi ( kapı kablosu 24 x 0,75, öteki otomatiklerle aynı ).

Denetim ( `girdi.dogrula` ):  cep kuyunun içinde kalmalıdır — kalmazsa çizim
durur ve **sığan tipleri** söyler;  sığıyorsa planda cep ( kat ve kabin kapısı )
karşı ağırlığın ön rayına / konsoluna / bloğuna, kabin rayının plakasına,
koluna ve ara kirişine çarpmamalıdır ( `geometri.kanat_cebi_carpismalari` ).
Bulgular:  yan ağırlıklı 26 standart düzenin 23'ünde kapı ağırlığa doğru
açılınca cep ağırlığın ön rayına çarpar, tersine açılınca hiçbirinde çarpmaz —
**kapı karşı ağırlığın tersine açılır**.  2.000 / 2.500 kg ( kapı 1.300 / 1.400 )
2 kanatla standart kuyuya sığmaz ( cep 680 – 730, yer 575 );  3 kanatlı
teleskopik ya da 4 kanatlı merkezi gerekir.

( Eskiden kanat sayısı yoktu:  planda hep 2 kanat, cep çizilmiyordu, Manuel
kapıda da açılma oku vardı. )

( Eskiden kanatlar eşiğin arkasına, kabin eşiğinin ve kabinin içine düşüyordu;
örnek girdi referans projenin 1017'sini iç yüzden okuyup arka duvarı 150 mm geride
bırakıyordu.  Duvar taraması da kapı boşluklarından geçiyordu — önizleme
taramayı seyrek çizdiği için görünmüyordu, DWG'de vardı.  Hepsi düzeltildi. )

## Tam proje ( hesap + çizim, tek pafta )

`ornekler/uret.py` yayımlanmış gerçek bir referans projenin
girdileriyle hesap programının MOTORUNU çağırır ( program değiştirilmez ),
kapak ve hesap paftalarını hesap programının kendi dışa aktarımıyla şablona
dizer, çizimleri `pafta.birlestir` ile son hesap sayfasının sağına ekler.  İki
örnek üretir, her biri `.dwg` ( AutoCAD çekirdeğinde AUDIT'ten geçirilip
kaydedilir ) + `.pdf` ( paftanın görüntüsü );  git'e girmezler:

| Örnek | Ne |
|---|---|
| ÖRNEK PROJE - Makine Dairesiz | referans projenin kendisi:  dişlisiz, kuyu üstünde |
| ÖRNEK PROJE - Makine Daireli Dişli | aynı asansör ( kuyu, kabin, raylar, halatlar, tamponlar ), makine kuyunun üstündeki odada, dişli ( referans projede yok ).  Değişen girdiler ve kaynakları `hesap_girdi.ASANSOR_MD`'de:  Gm 350 ( ofisin 12744-3 hesabı, A 160 ), verim ofisin dişli sabiti 0,50 → gereken 12,75 kW, motor bir üstteki IEC gücü 15 kW;  tabliye ve kaide hesap programının varsayılanları ( 1.200 · 1.100 · NPU 120 · NPU 140 ), kaidenin açıklığı çizimden ( L 1.400, X 360 ), oda 3.800 × 2.600.  Tst referans proje makinesinin 3.400'ü ( A 160'ın katalog değeri elde yok ) |

Çizim girdisi hesap girdisinden kurulur ve betik tutarlılığı DENETLER:  makine
tipi, yeri, tahrik kasnağı, yan yatak aynı;  makine dairesinde tabliye, kaide ve
oda ölçüleri aynı;  çizimin halat geometrisinden çıkan sarım açısı hesabın α'sına
eşit;  tampon adetleri aynı.  Birisi tutmazsa proje üretilmez.

Makine dairesiz tesiste makine şasesi raylara oturur ( referans proje "Motor Bedplate
Calculation" ):  hesap girdisinde "Makine yükünün yolu = Kılavuz raylara" ve
makine ağırlığı 250 kg ( referans proje motoru ).  Hesap programı bir raya
( Gm + Tst ) / 4 = 4.490 N yükler ( m.5.7.2.3.7 );  referans proje aynı yere kendi
kabulüyle 800 kg ( ray hesabında 1.000 kg ) koyar.  **Hesap programının
modelinde olmayanlar** ( çizim işi bitince ele alınacak ):  şasenin kendi
ağırlığı ( referans proje 150 kg ) ve şaseye bağlı halat bağlantısının yükü ( referans proje
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
kırılır ( referans proje ve LiftDesigner gibi ):  alttan ve üstten SIĞAN EN ÇOK
durak kalır, kırık kabine ve karşı ağırlığa değmez;  kırığı geçen ölçüler
gerçek değerini yazar ( "5 × 3000", "SEYİR 21000" ).

**Antet:**  çizimin bildiği değerler yazılır ( hız, durak, seyir, kabin,
askı, ray, ölçek );  bilmedikleri ( taşıma kapasitesi, sınıf, motor gücü )
BOŞ kalır — şablonun örnek değerleri projeyi yanlış tanıtırdı.  Şablon
değişirse ( çerçeve, kapak hücresi, antet hücreleri ) pafta üretilmez.

**AutoCAD ile doğrulandı:**  AutoCAD 2027'nin AcCoreConsole'unda açılıp
REGENALL, AUDIT ( 0 hata ) ve DWG kaydı.  Şablonun dört katmanı olmayan
malzeme / çizim stili kayıtlarını gösteriyordu ( AUDIT 16 hata );  pafta
bunları onarır.  Şablonun görünmez çöp çizgileri ( YAZı1'de iki çizgi z = −150
milyon mm'de, iki de sıfır boylu;  dosyanın EXTMIN'ini bozuyordu ) paftada ve
hesap paketinde silinir — şablon dosyasına dokunulmaz.

**Çizgi tipi ölçeği:**  AutoCAD bloğun içindeki çizgi desenini bloğun
ölçeğiyle KÜÇÜLTMEZ — desen dünya biriminde kurulur ( LiftDesigner da 0,05'lik
bloklarında ltscale 1 kullanır;  AutoCAD 2027'de ekranda görüldü ).  Paftadaki
blokta eksen ve kesik çizgiye 2,5 ( CENTER paftada 12,7 mm ), gerçek ölçüde
tek başına açılan DXF'te ölçek × 2,5 verilir.  Eskiden blokta da ölçek × 2,5
veriliyordu:  desen paftada 254 mm oluyor, eksenler ve gizli çizgiler AutoCAD'de
DÜZ çizgi görünüyordu ( 5 Eki ).

## Sırada ne var

1. Çizimin henüz modellemediği düzenler:  kabin raylara göre kaçık ( yc ),
   yana kaçık askı ( ys ) — ikisi de çizimde söylenir;  makine dairesizde 1:1;
   yandaki ağırlıkta makine yükü "Bina yapısına" iken duvardan duvara kiriş
   ( karar 3 — arkadaki ağırlıkta çiziliyor ).
2. Makaralı kabin pateninin ölçüleri gelince o da çizilecek ( karar 2 ).
   Revizyon kutusu çizilmez ( karar 10, 1 Eki — LiftDesigner da çizmiyor ):
   bölüm 11'in satırı kabinin bütün izdüşümünde, Sabitler'deki 500 yükseklikle.
3. Elle çizilmiş 800 KG ( yandan ağırlık, makine daireli ):  makine dairesinin
   ölçüleri gelince gerçek projelere eklenecek.

**Gerçek projeler ( 5. adım,** `testler/test_gercek_projeler.py` **):**
`~/Desktop/örnekliftler`'deki altı LiftDesigner projesi formdan girilmiş gibi
programın yolundan geçer;  ölçüler projelerin DWG'lerinden ( AutoCAD'in
DXFOUT'u, ölçü çarpanıyla ) okundu, eşleme `gercek_projeler.py`'nin başında
( RK = EE − 20:  LiftDesigner EE'yi kabinin DIŞ önünden ölçer ).  Kullanıcı
kararı:  denetimler projeye uysun diye değiştirilmez — programın hükmü ve
sebebi kilitlenir.

| Proje | Düzen | Programın hükmü |
|---|---|---|
| 4815-6 | MRL 2:1 kabin altı, ağırlık solda | Çizilir, bölüm 11 uygun;  kabin halatı sol duvardan 415 ( projeyle aynı ) |
| 1275 | MD 2:1 kabin üstü, ağırlık arkada | Çizilir, uygun;  tahrik kasnağının kabin inişi y 2.230 ( aynı ) |
| 800 KG | MD 1:1, ağırlık arkada | Çizilir, uygun;  ağırlık deliği y 1.820 ( aynı ), kabininki 10 önde ( LiftDesigner'ın kapı bölgesi 10 derin ) |
| 1022 | MD 1:1, ağırlık arkada | Çizilir, uygun ( gergi ağırlığının eni düzeltildikten sonra — yukarıda ) |
| 12495-18 | MRL 2:1 kabin üstü, ağırlık arkada | **Ret:**  arkadaki 1,10 m korkuluk – makine kirişi 230 < 300 ( m.5.2.5.7.2 c;  LiftDesigner denetlemiyor ).  4.270'te çizilir |
| 1250 KG | MRL 2:1 kabin altı, son kat 3.400 | **Ret:**  sığınma 915 < 1.000, üst paten 50 < 100, ağırlık şaseye çarpar …  ( LiftDesigner'ın kendi kesitinde de üst paten şaseyi 65 aşıyor ) |

Hesabın öbür bölümleri karşılaştırılmaz:  halat, motor, sarılma açısı
LiftDesigner'ın veri bloğunda yok, varsayılanla hesaplanır.

( Köprü ve hesap paftalarıyla çizimlerin aynı şeritte birleşmesi yapıldı —
yukarıda "Hesap ile çizimin bağlantısı".  RK ile çizimin ray ekseni:  kapi_arasi
= kapı hattı + RK;  hesabın yc'si ile çizimin kaciklik_y'si ayrı büyüklüklerdir:
çizim kabini kuyuda kaydırır, raylar kabinle birlikte kayar. )

**Başka bir referans:**  kullanıcının LiftDesigner çıktıları ( `12744-3 lift.dwg` ):
kuyu planı, düşey kesit, makine odası, kuyu üstü ve kuyu dibi kesitleri, kuyu
dibi görünüşü, giriş görünüşleri, kasnak düzenlemesi ( sarım açısı ) ve iskele
planı.  Ölçüler SW · SD · CW · CD · DW · PLW · PLD · DBG · BG kısaltmalarıyla
verilir;  uzatma çizgileri kısadır, planı kesmez.

## Ölçülerin kaynağı

`cizim/sabitler.py` içindeki ürün ölçüleri ve `girdi.ORNEK`, referans projenin
yayımlanmış örnek projesinin çizim geometrisinden ölçülerek alındı ( karşı
ağırlık çerçevesi 790 × 160, kapı kasaya 610 → boşluğa 730, kasnaklar arası
690 + 690 = 1.380, ara kiriş 50 );  ölçek 1/20 üzerinden
kalibre edildi ve kalibrasyon ray profilleriyle doğrulandı ( T89/B 89 × 62 ve
T70/A 70 × 65 tam çıktı ).  Tek bir projenin donanımıdır — tedarikçi verisi
gelince değiştirilmelidir.
