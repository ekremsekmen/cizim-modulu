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
| Kabin · ağırlık ray boyu | seyir + son kat + tabliye − 200 + kuyu dibi − 300 | en uzun çizilen ray:  kuyu tabanından tavanın 200 altına |
| Askı halatı boyu ( lh ) | kuyu boyu − yığın + 5 m | halatın çizilen yolu, kabin en alt durakta ( 2:1'de kabin kasnaklarının altından tavandaki bağlantıya ) |
| Regülatör halatı boyu | ( alt duraktan tavana + tabliye − 200 ) × 2 | regülatör – gergi kasnağı arası iki kez + iki yarım sarım |
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
Revizyon kutusunun yüksekliği de oradadır ( çizim onu henüz çizmez — karar 10 ).

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
projenin karşı ağırlığına göre seçilir.  Sığmıyorsa bölüm gereken paten
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
.venv/bin/python -m unittest discover -s testler     # çizim ve köprü testleri
cd hesap && ../.venv/bin/python testler/calistir.py  # hesabın doğrulama paketi
# ( arayüz testleri 3 · 5 · 6 · 13 açık bir programa karşı:  AVAN_TEST_URL=http://127.0.0.1:8790 )

# Örnek tam projeler ( hesap + çizim, tek pafta ) → ornekler/ — programın
# "Projeyi paketle" yolundan:
.venv/bin/python ornekler/uret.py
```

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
| `testler/` | 355 test ( `test_cizim.py`, `test_fiziksel_tutarlilik.py`, `test_girdi_sinirlari.py`, `test_kopru.py`, `test_olcu_kaynagi.py`, `test_yerlesim_saglamligi.py` — standart asansörler varsayılan çizim ayarlarıyla çizilir, `test_tasarim.py` — tasarım şeması, `test_olculer.py` — yerleşimin ölçü listesi, `test_arka_aski.py` — arkadaki ağırlıkla 2:1, `test_kararlar.py` — makaralı kabin pateni, çift sarım, dolgu, tek katalog, `test_gercek_projeler.py` — ofisin altı gerçek projesi ( veri `gercek_projeler.py` ), `test_gorunusler.py` — kasnak düzenlemesi ve giriş görünüşü ) |
| `ornekler/` | Yalnız iki örnek tam proje ( `.dwg` + `.pdf` ):  **makine dairesiz** ( referans proje ) ve **makine daireli dişli** ( aynı asansör );  onları üreten `uret.py` ve formun girdisi `hesap_girdi.py` |
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

Patenlerin MERKEZLERİ arası hesap programının paten arasıdır
( `dusey.kabin_paten_arasi`, `dusey.agirlik_paten_arasi` — varsayılan 2.420 ve
3.300, referans projenin örneğinde 3.300 ve 2.920 ):
kabinde şasenin alt ve üst kirişine, karşı ağırlıkta çerçevenin alt ve üst
ucuna ortalı — iki çerçevenin yüksekliği de hesabın paten arasıdır.  Eskiden
paten arası şase yüksekliği gibi kullanılıp patenler onun dışına ekleniyordu
( merkezler kabinde 3.440, ağırlıkta 3.060 ), sonra ağırlıkta 1.500 aralıkla
2.920'lik çerçevenin ortasına dizilmişti.  Referans projenin kendisi de tutarsız:
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
| Sığınma alanı **0,40 × 0,50** ( dik duruş ) / **0,50 × 0,70** ( çömelme ) | m.5.2.5.7.1 · Çizelge 3 | Korkulukların içinde, operatör ve askı dışında, kapıya en yakın yere konur ( 25 mm adımla;  dar boşlukta engelin kenarına yaslanarak );  yer yoksa reddedilir |

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
| Sığınma alanı **0,40 × 0,50** / **0,50 × 0,70** / **0,70 × 1,00** | m.5.2.5.8.1 · Çizelge 4 | Önce kabinin izinin altında, tampon / gergi / merdiven ve kabin altı kasnaklarıyla aralarındaki halat dışında, kapıya en yakın yere;  sığmazsa kuyu tabanının başka yerinde ( madde yalnız "kuyu tabanında" der ), karşı ağırlığın şeridine girmeden.  25 mm'lik ızgaraya sığmayan dar boşlukta alan engelin kenarına yaslanır |
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
tavan 60, taban 50, şase altı −320, alt paten merkezi şase altının 170 üstünde
( `alt_paten_payi`:  −150 ), üst paten merkezi alt patenin paten arası kadar üstünde
( varsayılan 2.420:  2.270 ), paten 140, fren bloğu 270 ( en alt parça −320 ), kabin
altı kasnak merkezi −425, eni 75, yan pano 15, arka pano 20;  etek 750
( m.5.4.5.1 ).  Paten arası 2.420 LiftDesigner'ın;  Has Asansör MRL şase kılavuzunda
da aralık kabin yüksekliği + 200 – 400.  Referans projenin örneği kendi kabiniyle
çizilir ( `sabitler.REFERANS_PROJE_KABINI`:  taban 120, şase altı −480, alt paten
payı 0, fren bloğu 350, kasnak −295 / 92, pano 45 / 33;  iç 2.250, paten arası 3.300 ).

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

Korkuluk açıklığı kenar kenar ölçülür:  her kenarın küpeştesi kendi
yüksekliğiyle ( 0,70 / 1,10 ) kendi üstündeki en alçak parçaya ( eskiden en
yüksek korkuluk bütün kenarlara uygulanıyordu;  yan panolar incelince gereken
0,70'lik yan korkuluklar yanlışlıkla reddediliyordu ).

**"Kuyu tavanının en alt kısmı" tavanın altındaki parçaları da kapsar**
( m.5.2.5.7.2 ):  makine dairesizde makine şasesi, kabin ve ağırlık halat
bağlantıları, regülatör.  Her açıklık kendi üstündeki en alçak parçaya
ölçülür ( `donanim.tavan_engeli` );  örnekte paten ve korkuluk şaseye,
sığınma kuyu tavanına gider.  Karşı ağırlık en üst konumunda ( kabin tam
ezilmiş tamponunda + 0,035·v² ) makine şasesine çarpıyorsa çizim durur.

**Kuyu dibi zinciri kabinle kapanmalı:**  kaide + tampon + çarpma arası +
şase altı = kuyu dibi ( referans proje:  764 + 160 + 96 + 480 = 1.500 );  tutmazsa
reddedilir.  **Hesap programıyla fark:**  onun sığınma satırları ofisin
paylarıyla hesaplanır ( üst paten bir satırda 2.700, bir başkasında 2.900;
varsayılan girdiler şase altını örtük 350 alır ) — bu kabin modeline göre
düzeltilene kadar iki program aynı açıklığa farklı sayı verir.

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

Kapının olduğu duvar boşluğun iki yanında iki parçadır, tarama boşluktan
geçmez:  kuyu planında ( C-C, kapı hizası ) ön duvar kapı boşluğunda ( duvar
boşluğuna montajda kasayla birlikte ), A-A'da kapı ünitesi duvardaysa boşluk
eşiğin altından başlar, makine dairesi planında oda kapısında.  Kapının üstünden
ya da altından kesilen planlarda ( kabin üstü, kuyu dibi, kuyu üstü, delik
planı ) ön duvar kesintisizdir ( `geometri.plan(…, kapi_duzeyi=False)` ).

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
bunları onarır.  Kesik ve eksen çizgilerine ölçek × 2,5 çizgi tipi ölçeği
verilir — yoksa desen paftada 0,1 mm'ye iner, çizgi düz görünürdü.

## Sırada ne var

1. Çizimin henüz modellemediği düzenler:  kabin raylara göre kaçık ( yc ),
   yana kaçık askı ( ys ) — ikisi de çizimde söylenir;  makine dairesizde 1:1;
   yandaki ağırlıkta makine yükü "Bina yapısına" iken duvardan duvara kiriş
   ( karar 3 — arkadaki ağırlıkta çiziliyor ).
2. Revizyon kutusu ( karar 10 ):  planda eni × boyu, yüksekliği ve kabin
   üstündeki yeri gelince çizilecek, bölüm 11'in satırı çizimden ölçülecek
   ( bugün kabinin bütün izdüşümüyle, Sabitler'deki 500 yükseklikle ).
   Makaralı kabin pateninin ölçüleri gelince o da çizilecek ( karar 2 ).
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
