# ASANSÖR PROJE PROGRAMI

Asansör projelerinin hesaplarını yapan, sonuçları **PDF** ve **CAD** olarak
veren yerel program.  Açılışta hangi projenin hazırlanacağı seçilir:

| Bölüm | Kapsam | Kaynak |
|---|---|---|
| **AVAN PROJE** | Trafik hesabı · avan hesapları · proje kapağı | MMO/697 (2. Baskı, Ocak 2020) · TS EN 81-20 · ISO 8100-32:2020 · IEEE Std 80 · IEC 60364-5-52 |
| **UYGULAMA PROJESİ** | Mukavemet ( 10 bölüm ) + kabin ve kuyu aydınlatması, kurulu güç, gerilim düşümü, makine dairesi aydınlatması, temel topraklama | TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465 · MMO 208/4 · MMO 208/7 · IEEE Std 80 · IEC 60364-5-52 |

**Mukavemet tarafı avandan ayrıdır** — tabloları ve kabulleri kendi kaynağından
gelir. Elektrik ve topraklama hesapları ise avan projesindekilerin **aynısıdır**;
kopyalanmadı, aynı motor çağrılıyor ( `motor/avan/avan_hesabi.py` ). Sekme şeridi moda göre
değişir, yalnız **Sabitler / Ofis Standardı** iki modda da durur — ofis standardı
ikisinde de aynıdır.

### Ortak girdiler bir kez girilir

Mukavemet ile elektrik hesapları aynı büyüklüklerin çoğunu paylaşır. Aynı değeri
iki kez sormak yalnız zahmet değil, **hata kaynağıdır**: biri düzeltilip öteki
unutulduğunda iki hesap sessizce ayrışır ve pafta kendi içinde çelişir. Bu yüzden
ortak girdiler **yalnız mukavemet alanlarında** durur ve elektrik tarafına
kendiliğinden köprülenir:

| Girilen ( mukavemet alanı ) | Elektrik hesabında |
|---|---|
| Beyan yükü | Q |
| Beyan hızı | V |
| Boş kabin ağırlığı | Gk |
| Kabin derinliği | a ( kabin boyu ) |
| Kabin genişliği | b |
| Kuyu boyu ( seyir + son kat + kuyu dibi ) | Hk |
| Motor gücü | Nsç |
| Askı oranı | i |
| Kabin rayı profili | gr ( ray metre ağırlığı ) |

Bu liste ekranda formun başında da yazılıdır. **Yalnız elektrik hesabına ait**
olan girdiler ( kuyu genişliği, kablo kesit ve uzunlukları, temel ölçüleri,
makine dairesi ) ayrı bir grupta toplanmıştır.

**Avanın motor gücü ve kuvvet hesapları uygulama projesine alınmaz:** motor gücünü
mukavemet bölüm 1 zaten MMO 208/7 §2.4'e göre hesaplar, kuvvetleri de bölüm 7-9
verir. İkisini birden basmak paftada iki farklı motor gücü gösterirdi.

Hesap motorları ofisin eski Excel dosyalarından yola çıkarak yazıldı, değerler
hücre hücre karşılaştırılarak doğrulandı ve standardın gerektirdiği yerlerde
TS EN 81-20 / TS EN 81-50'ye göre düzeltildi. **Bugün hesabın tek kaynağı
programın kendisidir** — program Excel üretmez ve okumaz.

**Sürüm 3.2** — referans örnek projeyle yapılan kıyasta ve bağımsız incelemelerde bulunan düzeltmeler.

| | Önce | Sonra |
|---|---|---|
| **Paten tipi** | Tek seçim iki raya birden uygulanıyordu;  kabinde kaymalı, karşı ağırlıkta makaralı paten ( yaygın düzen ) girilemiyordu ve karşı ağırlık rayının flanş gerilmesi yanlış formülle hesaplanıyordu | **Kabin paten tipi** ve **karşı ağırlık paten tipi** ayrı seçilir ( EN 81-50 m.5.10.5 ).  Girilen balata uzunluğu ℓ **kabin pateninindir**;  karşı ağırlığın kaymalı pateninde ℓ kendi rayından türetilir |
| **Makine dairesiz ( MRL ) projede bölüm 2** | Hüküm "UYGULANMAZ" derken paftada var olmayan bir kaidenin kiriş satırları ve kırmızı "UYGUN DEĞİL" kontrolleri basılıyordu | Bölüm yerinde kalır ( numaralar kaymaz ) ve yalnız neden uygulanmadığını yazar.  Kaide kirişi alanları MRL'de ekranda gizlenir ve doğrulanmaz.  *( Sonradan:  MRL'de makine kirişi hesaplanır — bkz. "MRL'de makine kirişi" satırı. )* |
| **Çok asansörlü uygulama projesinin PDF'i ve paketi** | Yalnız o an açık asansörün formu gönderiliyordu:  ekran iki asansörü hesaplarken indirilen pafta birini içeriyordu | Çıktı, ekranın hesap isteğinin **aynısıyla** üretilir |
| **Hızlı yük değişiminde kabin ağırlığı** | 1000 kg'ın hesabı yoldayken yük 1600 kg yapılınca eski yanıt 950 kg'ı kutuya yazıyor, 1600 kg'lık hesap 950 ile gidiyordu ( 1350 olmalı ) | Tablodan yenileme her değişikliğe numara verir;  yanıt yalnız kendi değişikliği hâlâ en sonuncusuysa yazar |
| **İki asansörde art arda yük değişimi** | Yenilenecek asansör tek bir işaretle tutuluyordu;  ikinci asansörün değişikliği birincinin işaretini siliyor, o asansörün kabin ağırlığı eski değerde kalıyordu | İşaret her asansörde ayrı;  hesap reddedilirse işaret açık kalır ve girdi düzelince tablo gelir |
| **Çok asansörlü projede ortak topraklama iletkenleri** | Binaya ait bölümler ilk asansörün kendi hesabından alınıyordu;  iletkenler yalnız o asansörün koruma iletkenini görüyordu.  Kolon kesiti 16 ve 95 mm² olan iki asansörde sıraya göre topraklama iletkeni 16 ya da 50, ana potansiyel dengeleme 10 ya da 25 mm² çıkıyordu | Makine dairesi aydınlatması ve temel topraklama bütün asansörler hesaplandıktan sonra, **tesisteki en büyük koruma iletkeniyle** bir kez hesaplanır ( avan projesiyle aynı kural );  asansörlerin sırası sonucu değiştirmez |
| **Yük değiştirilip hemen kaydedilen proje** | Kabin ağırlığı kutusu tablo değeri gelene kadar eski kütleyi taşıyordu;  o arada kaydedilen dosyaya ( ve tarayıcı belleğine ) 1600 kg yükün yanına 800 kg kabin yazılıyor, açılınca hesap o değerle yapılıyordu ( kabin tamponu 116,29 yerine 94,71 kN ) | Yük değişince kutu hemen boşalır ( boş = tablodan gelecek );  boş kutuyla açılan proje tablo değerini ister |
| **Ofis standardında belirsiz ya da okunamayan sayı ( avan )** | "1.200" ve "abc" hata vermeden varsayılana dönüyordu:  β = 1.200 yazan kullanıcının topraklama direnci 150 Ω·m ile hesaplanıyordu;  kablo tipine yazılan "NYY" NHXMH FE180 oluyordu | İki proje ofis standardını aynı kuralla okur:  belirsiz ya da okunamayan sayı hesabı durdurur ve sebebini yazar, metin alanı metin kalır |
| **Gizli alan projeyi durduruyordu ( uygulama )** | Makine dairesizde gizli makine dairesi ölçüsü ya da kaide alanı, makine dairelide gizli "raya binen yük" içinde kalmış "4.000" · "-3" gibi bir değer bütün projeyi reddettiriyordu — kullanıcı alanı göremiyor, düzeltemiyordu | Makine yerleşimine göre hesaba girmeyen alanlar tek listede ( `motor/uygulama/uygulama_girdisi.uygulanmayan_alanlar` );  ekran onları gizler, API okumaz, motor doğrulamaz |
| **Kurulu güç şebekeden çekilen güçle yazılıyordu** | Kolon hattı akımı doğru çıksın diye cetvele motorun şebekeden çektiği güç ( Nsç / ηm ) yazılıyor, asansörün kurulu gücü de ~%18 büyük bildiriliyordu ( 11 kW motor → 12,94 kW ) | Kurulu güç tanımına döndü:  cetvelde motorun **etiket gücü** ( Elektrik İç Tesisleri Proje Hazırlama Yönetmeliği m.5-19 · TS EN 60034-1 m.5.5.3 ).  Kolon hattı akımı ve gerilim düşümü bölüm 6'daki ayrı satırla ( P1 = Pşeb + aydınlatma + priz ) hesaplanmaya devam eder — **kesit, sigorta ve gerilim düşümü değişmez** |
| **Kabin ağırlığının kaynağı** | Tablodan gelen değer ilk hesapta ofis tablosunu, sonraki hesaplarda ve indirilen paftada "GİRİŞ" yazıyordu | Kaynak değerden okunur:  değer o beyan yükünün tablo değeriyse kaynak tablodur |
| **Kablo akım taşıma kapasitesi ( Iz )** | Tablo IEC 60364-5-52 B.52.4 Yöntem C diyordu ama 25 mm² ve üstü o tablonun değerleri değildi ( 101 · 125 · 151 · 192 · 232 · 269 A ) — %4-5 fazla.  Örneğin 48 kW motor + 25 mm² kolon hattı ( I = 97,4 A ) "uygundur" çıkıyordu | B.52.4 Yöntem C:  **96 · 119 · 144 · 184 · 223 · 259 A**.  16 mm² ve altı zaten doğruydu |
| **Makine dairesi aydınlatması** | Bölge indeksinde h = 1,0 m alınıyordu — kabinin ölçüm düzlemi ( döşemeden 1 m yukarıda ).  Makine dairesinde 200 lüks **döşeme seviyesinde** istenir;  k iki kat, armatür %20-30 az çıkıyordu ( 4 × 3 m daire:  4 yerine 5 armatür gerekir ) | h = **2,10 m** ( armatür–döşeme;  TS EN 81-20 m.5.2.1.4.2 · m.5.2.6.3.2.1 asgari net yükseklik ).  Kabin ve kuyu aynı kalır |
| **Paftadaki işlem satırları** | Sonuç doğru, işlem satırı yanlış yazılmış altı bağıntı:  2:1 askıda halat boyunda köşeli parantez yoktu ( "… / 1000 + 5 × 2" ), \| Fx \| bağıntısına işaretli Fx yazılıyordu, bina nüfusu B ve kuvvetler ( P1 · P2 · PR · PK · Fs ) yuvarlanıyor ama satır bunu söylemiyordu, "Sapd = 0,5 · 4 = 6" asgariyi göstermiyordu, ε satırında κ = 44,4 "44" basılıyordu | Her satır yazılı sayılarıyla yeniden hesaplanınca basılan sonucu verir;  yuvarlama ve asgari adımları satırda yazılıdır |
| **Kat yükseklikleri** | Her durak tek tek giriliyordu ( 15 katlı binada 15 kez "3000" ), seyir mesafesi ve son kat yüksekliği bu listeden türetiliyordu.  Hesap listeden yalnız TOPLAMI ( ray ve regülatör halatı boyu ) ve SON ELEMANI kullanıyordu | Liste kaldırıldı:  **seyir mesafesi + son kat yüksekliği** girilir ( referans projenin ve TS EN 81-50'nin kullandığı büyüklük ).  Toplam = seyir × 1000 + son kat;  176 senaryonun hiçbirinde bir sayı değişmedi, yalnız iki pafta satırının yazımı "Σ durak" yerine "H × 1000 + son kat" oldu |
| **Kabin kapısı ağırlığı** | Her asansörde ayrı bir kutuya elle giriliyordu ( varsayılan 75 kg, kaynağı yok ) | **Ofis standardına** taşındı ( ② mukavemet kabulleri ).  Değer imalatçı kataloğundan:  Fermator 40/10 PM otomatik kabin kapısı, 2 panel teleskopik, 800 × 2.000 mm, sac panel — **62 kg**.  Paftada ayrı satırda, kaynağı **KATALOG** yazar.  Kapı genişliği ağırlığı birkaç kg değiştirir ( ray gerilmesinde %1 mertebesi ), bu yüzden asansör bazında sorulmaz.  75 → 62 kg, kabin rayı sehimi sınırda olan dört senaryoda hükmü çevirdi ( δx 5,03 – 5,12 mm > 5 mm ) |
| **Bir raya düşen makine yükü ( MRL )** | Makine yükünün yolu "Bina yapısına" seçiliyken de soruluyordu;  "Kılavuz raylara"da boş bırakılırsa eşit dağıtılıyor, doluysa imalatçı değeri olarak okunuyordu | Kutu **kaldırıldı**.  "Bina yapısına"da hesaba girmez;  "Kılavuz raylara"da makinenin yükü ( Gm + Tst ) kabin raylarına **eşit** dağıtılır ve paftada "( Gm + Tst ) / 2 ray" yazar |
| **Gelişmiş bölümleri** | Her grupta hep aynı girilen ofis / ürün değerleri ( pervaz, kapı mekanizma payı, regülatör kasnağı, tampon ölçüleri, ray sayıları … ) her projede projeye özgü ölçülerle yan yana duruyordu | 101 girdiden 58'i grubun altındaki kapalı **Gelişmiş** bölümündedir;  hesaba ve paftaya aynen girerler.  Seçim beş projede her girdiyi gerçekçi değerlere çekerek yapıldı.  Görünür kalanlar her projede değişenler ve yanlış kalınca sonucu çok değiştiren beyanlardır ( askı oranı, ray–kapı arası, üç kaçıklık — kabin merkezi y · askı xs · ys, varsayılan 0 —, güvenlik tertibatı tipi, karşı ağırlıkta tertibat, α ).  **Hız regülatörü** grubunun bütün alanları Gelişmiş'tedir.  Gizli değer sessiz kalmaz:  varsayılandan farklı değer sayısı başlıkta yazar ve alan işaretlenir, hesabı durduran hata gizli bir alandaysa bölüm kendiliğinden açılır, arama gizli alanları da bulur.  Yeni projede kabin ağırlığı kutusu boş açılır ve tablodan dolar ( eskiden örnek projenin 700 kg'ıyla, "elle girilmiş" sayılarak açılıyordu ) |
| **Elastisite modülü E** | Ray sehimlerinde `E = 206.010 N/mm²` kullanılıyordu — 21.000 kgf/mm² × 9,81, yani kgf biriminden çevrilmiş eski teknik değer;  kodda gerekçesi yazılı değildi.  Bütün sehimler **%1,94 büyük** çıkıyordu:  yön emniyetliydi ama δ/δperm oranı 0,981 – 1,000 bandına düşen bir tasarımı standarda göre geçerken reddediyorduk.  Üstelik pafta formülü `48 × E × Iy` diye bassa da **E'nin sayısını göstermiyor**;  hesabı elden denetleyen 210.000 alıp %1,94 farklı bir sonuç buluyor ve bizde aritmetik hata arıyordu | **E = 210.000 N/mm²**.  Standardın kendi verdiği tek çelik değeri budur ( EN 81-50 m.5.13:  *"for steel: E = 2,1 × 10⁵ N/mm²"*;  ray maddesi m.5.10.4 ve Ek C sayı vermez ), yapı çeliğinin bağlayıcı değeri de aynıdır ( EN 1993-1-1 m.3.2.6 ).  Referans proje, ofisin Excel'i ve *new block* paftası da 210.000 kullanır — paftamız artık elden doğrulanabilir.  155 senaryoda **yalnız δx ve δy değişti ( 1.387 değer ), hiçbir projenin hükmü değişmedi**;  avan ve trafik motorlarının altın çıktıları birebir aynı kaldı |
| **Ofis γ 38° → 45°** | Ofis kabulü `γ = 38°` idi ve gerekçesi yazılı değildi.  **Akış Asansör'ün Kullanım Kılavuzu** ( Rev.02 · 11.01.2023, bölüm 16 ) tahrik kasnağının kodlama şemasını verir ve örnek kasnağı *"altı kesik kanallı Ɣ:45° , β:90° açılı"* diye çözer — yani açılar **kasnağın kodunda** yazılıdır.  Ofisin kendi Excel şablonu da w = 45° kullanıyor.  38°, referans projenin makinesinin ( Y-2/1-01 ) değeriydi, ofisin kullandığı makinenin değil | **γ = 45°**, kaynağı koda yazıldı.  **β = 90° değişmedi** — Akış'ın yayımlanmış değeriyle zaten birebir aynıydı.  155 senaryoda **tek bir bölüm hükmü** değişti ( *D/d 240/6,5 belgeli*:  askı halatları UYGUN DEĞİL → UYGUN ), **hiçbir projenin genel sonucu değişmedi**.  Etkisi ağırlıklı olarak Çizelge 2'dedir:  Nequiv(t) 12 → 6,5, yani gereken halat güvenlik katsayısı düşer — bu bilinçli bir **gevşemedir** ve imalatçının yayımlanmış değerine dayanır.  Tahrik sürtünmesine yalnız sertleştirilmiş V kanalda girer;  bloke durumunun f'si de düşer |
| **Testler ofis sabitini izliyor** | Üç test ofis γ'sını **sayı olarak** sabitlemişti ( 38 · Nequiv 12 );  varsayılan değişince kırıldılar ve denetledikleri şey ( pafta ile hesabın AYNI γ'yı kullanması, altı kesik V'nin V satırından okunması ) gözden kayboluyordu | Beklenen değerler artık `US.sabitler()` ve `MT.kanal_nequiv_t()` üzerinden **sabitin kendisini izliyor**.  Dış kaynak tablosuyla karşılaştırma da kaynağın KENDİ açısıyla yapılıyor — ofis kabulünün aynılığı değil, bağıntının aynılığı denetleniyor |
| **Kasnak kanal açıları γ · β** | İkisi de **yalnız ofis sabitiydi**.  Oysa TS EN 81-50 m.5.11.2.3.1.1 açıkça *"The value of the groove angle γ shall be **given by the manufacturer**"* der ve gerçek projelerde değişir:  referans projenin makinesi ( Y-2/1-01 ) **γ = 38°**, ofisin Excel'i **γ = 45°**, EN 81-50 hesaplarının yayımlanmış örneği **γ = 50° · β = 105°**.  Tek bir projeyi modellemek için genel sabiti değiştirmek gerekiyordu — bu da ofisteki bütün projeleri sessizce kaydırıyor ve paftada izi kalmıyordu | Askı halatları · **Gelişmiş**'e iki isteğe bağlı kutu.  Boşsa ofis değeri kullanılır ( 155 senaryoda yeni girdi anahtarları dışında **tek bir sayı değişmedi** ), girilirse paftada kaynağı **KATALOG · kasnak föyü** yazar.  **Bölüm 4 ile bölüm 6 aynı kaynaktan okur** ( `MG.kanal_acilari` ):  Nequiv(t) eskiden doğrudan ofis sabitinden okunuyordu, projeye girilen γ yalnız tahrike işleseydi pafta kendi içinde çelişirdi.  Sınırlar doğrulanır:  V kanalda 35° ≤ γ ≤ 90°, yarım dairede 25°'den, β ise 0 < β ≤ 105°;  alt kesilmesi olmayan kanala β girilirse reddedilir |
| **γ iki yönlüdür — ofis varsayılanı "emniyetli taraf" olamaz** | — | Belgeye geçirildi:  büyük γ tahrikte sürtünmeyi **düşürür** ( emniyetli ) ama Çizelge 2'de Nequiv(t)'yi de düşürür, yani gereken **halat güvenlik katsayısını gevşetir** ( γ = 38° → 12 · γ = 50° → 5 ).  β ise yalnız tahriki etkiler;  altı kesik V'de Nequiv(t) β'dan bağımsızdır.  Bu yüzden γ'nın varsayılanı **ölçülerek** değiştirildi ( 38° → 45°, bkz. üstteki satır:  155 senaryo, tek bölüm hükmü ) ve **β = 90° korundu** — Akış'ın yayımlanmış değeriyle zaten aynıydı |
| **Yukarı kaçmaya karşı koruma** | Karşı ağırlık tampona oturmuşken makine yukarı dönmeye devam ederse kabin tavana çekilebilir.  Program buna karşı yalnız *halatın kayması* şartını ( `T1/T2 ≥ e^(f·α)` ) ve **koşulsuz** uyguluyordu.  Oysa **TS EN 81-20 m.5.5.3 c) İKİ yol tanır**:  1) halat kasnakta kayacak, **ya da** 2) makine elektrikli bir güvenlik tertibatıyla duracak — EN 81-50 m.5.11.2.1 de eşitsizliği açıkça *"where protection … is provided by limiting of traction"* diye koşula bağlar.  Uzun seyirde halat kütlesi yüzünden T2 küçülmez, kayma güvenilmez olur ve tesis 2. yola geçer;  bizde bu proje haksız yere kalıyordu | Askı halatları · **Gelişmiş**'e tek seçim:  *Halatın kayması* ( varsayılan ) / *Elektrikli güvenlik tertibatı*.  İkincisi beyan edilirse **bloke satırı yine hesaplanır ve paftada durur** ( T1 · T2 · oran gerçek bilgidir ve sahada m.6.3.3 deneyiyle karşılaştırılır ), yalnız bölümün hükmünü belirlemez ve dayanağını yazar.  Varsayılan bugünkü davranışı **birebir** korur:  155 senaryoda yeni girdi anahtarı dışında tek bir sayı ya da hüküm değişmedi |
| **Tahrik kalınca sebebi yazmıyordu** | Bölümün hükmü yalnız `UYGUN DEĞİLDİR` idi.  Dört yük durumundan hangisinin kaldığı da, ne yapılacağı da yazmıyordu — öteki bütün bölümler uygulanabilir bir öğüt veriyor ( *"halat çapını artırın"*, *"en az 173 mm strok gerekir"* ) | Hüküm kalan durumu **adıyla** yazar ve öğüdünü verir.  İki frenleme durumu ayırt edilir ( *dolu kabin altta* · *boş kabin üstte* ).  Öğüt yöne göre değişir:  ilk üç durumda kayma İSTENMEZ → *sarılma açısını ya da sürtünmeyi artırın*;  blokede kayma İSTENİR → *halat kaymıyor, m.5.5.3 c) 2 yolunu beyan edin* |
| **Hüküm gerekçesi düşen kontrolden yazılıyor** | Beş bölüm, hangi alt kontrolün kaldığına bakmadan **sabit** bir gerekçe basıyordu.  En kötüsü tamponda görüldü:  1,6 m/s'de 400 mm stroklu yaylı tampon için pafta *"en az 346 mm strok gerekir"* diyordu — oysa strok satırı **UYGUN**du ( 400 ≥ 346 ), asıl engel m.5.8.1.5'ti ( enerji biriktirmeli tampon 1 m/s üstünde **hiçbir strokla** kullanılamaz ).  Mühendis daha uzun yay arayıp aynı duvara çarpardı.  Regülatörde beş kontrolün üçü düşünce metin **tamamen boştu** ( çıplak `UYGUN DEĞİLDİR` ).  Sığınmada on ikiye yakın kontrolün hepsine *"kuyu üst/alt boşluğunu artırın"* yazılıyordu — Ç.3/Ç.4 **sığınma hacmi** düştüğünde bu yanlış yöndür, hacim kabin planına ve beyan edilen duruşa bağlıdır.  Makinede yan yatak ( NPU F ) ile dikine kiriş ( NPU E ) **ayrı elemanlar**dı, ikisine de aynı cümle çıkıyordu.  Raylarda *"konsol aralığını küçültün"* öğüdü **flanş** ( σF ) ve **basma** ( σv ) kontrollerinde fizikçe yanlıştır:  konsol aralığı l bu iki bağıntıya hiç girmez | Beş bölümün hükmü de gerekçesini **gerçekten düşen kontrolden** üretir.  Raylarda kontroller türe ayrıldı ( gerilme · burkulma · sehim · flanş · basma ) ve **çözüme göre gruplanır** — aynı çare üç kez tekrarlanmaz.  Flanş ve basma için *"konsol aralığı bu kontrole GİRMEZ"* açıkça yazar.  σ hesaplanamadığında ( ω çizelgesi λ aralığı dışında ) *"aşıyor"* denmez, **denetlenemedi** denir ve λ yazılır.  Yalnız `sonuc.metin` değişti:  480 projelik taramada `uygunlar` ile tür listesinin uzunluğu **birebir** eşit çıktı, altın çıktıda üç fark oluştu ve üçü de metindi — biri ( senaryo 12 ) hatayı birebir gösteriyordu:  eski metin *"kuyu boşluğunu artırın"* derken gerçek sebep **Ç.4 kuyu dibi sığınma hacmi**ydi |
| **Acil frenleme yavaşlaması a:  0,8 → 0,5** | Varsayılan `a = 0,8 m/s²` idi ve **kaynağı kodda yazılı değildi**.  Bu sayı ofisin Excel'indeki `b = 0,67·v² + 0,13·v` bağıntısının **yalnız v = 1 m/s değeridir** ( aynı bağıntı v = 1,6'da 1,92, v = 2,5'te 4,51 der ) — yani hıza bağlı bir değer sabitlenmişti.  TS EN 81-50 m.5.11.2.2.2 ise *"Each moving element shall be considered with its **proper** rate of retardation … In no case shall the rate of retardation to consider be less than 0,5 m/s²"* der:  **0,5 bir tabandır**, doğrusu makinenin gerçek fren yavaşlamasıdır.  Referans program ( referans proje ) da 0,5 kullanır.  Etkisi tek bölümde ama başattır:  `a` tahrike `( gn + a ) / ( gn − a )` çarpanıyla girer ve 12 gerçek saha projesinde **a = 0,8'de 2'si, a = 0,5'te 10'u** geçiyordu — *"çoğu projem tahrikten kalıyor"* şikâyetinin tek kaynağı buydu | Varsayılan `ACIL_FRENLEME_ASGARI` = **0,5 m/s²**;  alan tek kaynaktan okur, kaynağı ve ofis formülüyle ilişkisi koda yazıldı.  ⓘ açıklaması bunun **standardın tabanı** olduğunu ve makinenin gerçek değeri biliniyorsa imalatçıdan girilmesi gerektiğini söyler.  Doğrulama alt sınırı zaten koruyordu ( 0,5'in altı reddedilir, üst sınır 1 gn ).  155 senaryoda **985 değerin tamamı `a`'ya bağlı çıktı** — 888'i `tahrik.fren_alt` / `fren_ust` ( T1 · T2 · oran ), 85'i girdinin kendisi, 12'si tahrik hükmü;  **ray · motor · tampon · kuyu tabanı hiç değişmedi**.  12 hükmün 12'si de `UYGUN DEĞİL → UYGUN` yönünde, hiçbiri ters yöne gitmedi.  Sapma TEST 8'in `BILEREK_DEGISEN_VARSAYILAN` listesine gerekçesiyle kaydedildi |
| **Tampon kendi boyundan fazla ezilemiyor** | Kuyu dibindeki bütün açıklıklar tek bir sayıdan türer:  `a_dip = baba + ( tampon boyu − ezilme )` — kabinin, TAM EZİLMİŞ tamponun üstünde durduğu kot.  Ezilme boyu aşınca parantez negatife dönüyor, `a_dip` fiziksel anlamını yitiriyor ve ondan türeyen **a · a.1 · a.2 · b** açıklıkları ile **Ç.4 sığınma hacmi** sessizce bozuluyordu.  Denetimde 100 mm'lik tampona **5.000 mm** ezilme girilebildiği, `a_dip = −3.900 mm` çıktığı ve **hiçbir uyarı verilmediği** görüldü.  Gerçek saha denemesinde bu, dört projenin kuyu dibi bölümünü sebepsiz düşürüyordu | `dogrula`'ya tek kontrol:  **ezilme ≤ boyu**.  Hata iki sayıyı da yazar ve hangi hesapların bu farktan türediğini söyler.  Sınır kabul edilir ( ezilme = boyu ).  Kontrol, **testlerin kendi senaryolarında dört fizikseldışı tampon buldu** ( 100 mm boya 500 · 400 · 421 · 900 mm ezilme ) — hepsi tutarlı hale getirildi;  o testler stroku denetliyordu, tamponun boyunu değil |
| **Birbirine bağlı girdilerde tutarlılık** | Tek tek geçerli ama **birlikte olanaksız** değerler sessizce kabul ediliyor ve hesabı bozuyordu.  ① **Ds > D2:**  Ds *"saptırma kasnaklarının EN KÜÇÜK çapı"*, D2 ise ortalaması — tanım gereği Ds ≤ D2.  İki kutu ters girilince m.5.5.2.1'in `Ds/dh ≥ 40` kontrolü **hükümden sessizce düşüyordu** ( D2 = 240 · dh = 8'de kalması gereken *Ds/dh = 30* satırı, Ds = 600 yazılınca kayboluyor ve bölüm o kontrolü geçmiş sayılıyordu — emniyetsiz yön ).  ② **Ray sayısı 1:**  kabul ediliyordu;  hesap çalışıyor ( n bölendir, ray kuvvetleri iki katına çıkar ) ama standarda aykırı bir düzen paftaya olağan seçenek gibi yazılıyordu.  ③ **Tampon babası kuyu dibinden yüksek:**  `a_dip = baba + ( boyu − ezilme )` kuyu dibi derinliğini aşınca kabinin en alt noktası **alt durak döşemesinin üstünde** kalır;  dip açıklıklarının hepsi *"büyükse iyidir"* diye bakıldığı için böyle bir düzen sığınma bölümünü **GEÇİYORDU** ( KY = 800 · baba = 1.000 → a_dip = 1.010, hüküm UYGUN ) | `dogrula`'ya üç kontrol.  ② TS EN 81-20 **m.5.7.1.1**'e dayanır ( *"shall each be guided by at least two rigid steel guide rails"* ) ve hem kabin hem karşı ağırlık için işler;  hata maddeyi yazar.  ① ve ③ tanım/geometri gereğidir, sınırlar kabul edilir ( Ds = D2 geçerli ).  Kontroller **testlerin kendi senaryolarında da iki çelişki buldu**:  TEST 9 ve altın senaryo 16, D2 = 295'e Ds = 320 veriyordu.  İkisi de geçerli yöne çevrildi ( D2 = 320 · Ds = 295 ) ve özellik artık **daha güçlü** denetleniyor:  ortalama sınırı geçerken en küçük çap geçmiyorsa bölüm düşmelidir.  Altın çıktıda **62 fark oluştu, hepsi yalnız o senaryoda** |
| **Paten arası h:  kabin 3.400 → 3.300 · karşı ağırlık 3.400 → 3.000** | h ray kuvvetinin **paydasıdır** ( `Fx = … / ( n · h )` ) ve kuyudaki yığına da girer ( halat boyu, Ç.2 üst açıklığı );  varsayılan gerçeğe yakın olmalıdır.  Kabin 3.400, diskteki dört gerçek projenin hepsinden büyüktü ( ofis Excel'i makine daireli **3.000** · MRL **3.300** · referans proje **3.300** · *new block* **3.200** ).  Karşı ağırlık kabinle aynı 3.400'dü;  oysa çerçeve boyu **dolgu malzemesine** bağlıdır:  referans proje 1.300 kg → **1.500 mm** ( pik döküm ile tutarlı ) · *new block* 1.838 kg → **3.200 mm**.  Programın varsayılan malzemesi **barit**:  Türk piyasasındaki blok 960 × 155 × 120 mm, 50 – 70 kg — 1.200 kg için yalnız dolgu 2.160 – 2.880 mm | Kabin **3.300**, karşı ağırlık **3.000** ( barit;  pik döküm kullanılan projede ~1.500 elle girilir ).  Örnek projede halat boyu 48,38 → **49,38 m** ( yığın 500 mm kısaldı, 2:1'de +1,0 m ), Ç.2 açıklığı 350 → **750 mm** — ikisi de elle doğrulandı.  155 senaryoda **hiçbir hüküm dönmedi**.  Altın çıktıda 1.275 kg'lık iki proje kabin rayında kıl payı düştü:  δx 4,94 → 5,09 mm, sınır 5 ( tam 3.400 / 3.300 oranı ).  İki test h'yi 3.400 olarak çivilemişti;  artık varsayılandan okuyor |
| **L2 makine besleme uzunluğu → Sabitler, 3 m** | Asansör formunda her projede soruluyordu ve varsayılanı kaynaksız **12 m**'ydi;  avan motoru ve ofisin üç şablonu ( Makina Daireli · Makina Dairesiz · avan Excel'i, "Asansör panosu → motor" ) **3 m** kullanıyor — aynı asansöre avanla uygulama farklı sayı veriyordu.  Pano makineye yakın durur ( makine dairesinde yanında, MRL'de üst katta ) | Asansör formundan kaldırıldı;  uygulamanın **Sabitler** sekmesinde ( ⑤ Kurulu güç ve gerilim düşümü ) **kendi değeri 3 m** olarak durur — avandan okunmaz, köprü onu avan motoruna her zaman açıkça geçirir.  Paftada kaynağı **KABUL**.  Etkisi yalnız gerilim düşümündedir ve küçüktür:  varsayılan projede ε %0,38 → %0,25, sınır %3;  **hiçbir hüküm dönmedi**.  Eski projelerde asansöre girilmiş L2 artık okunmaz, Sabitler'deki değer kullanılır |
| **L1 → Sabitler'de yatay güzergâh payı · S1 16 → 6 mm²** | L1 ( kolon hattı uzunluğu ) asansör formunda sorulan bir kutuydu;  boşsa "Hk + ofis payı ( 3,50 m )" kullanılıyor ve paftaya da böyle basılıyordu — okuyan 3,5 m'yi keyfi sanıyordu, payın uygulama projesinde değiştirilebileceği bir yer de yoktu.  S1'in uygulama varsayılanı kaynaksız **16 mm²**'ydi;  avan motoru ve ofisin avan Excel'i **6 mm²** kullanıyor | **L1 kutusu kaldırıldı:**  L1 = kuyu yüksekliği + **yatay güzergâh payı**, pay uygulamanın **Sabitler** sekmesinde ( ⑤ ) kendi değeri 3,5 m olarak durur ve köprü onu avan motoruna her zaman açıkça geçirir.  Pafta artık payın ne olduğunu yazar:  *"Hk + yatay güzergâh ( ana pano → kuyu → asansör panosu ) 3,50 m"* — avan paftası da aynı metni basar ( metin tek yerde, avan motorunda ).  Pano kuyudan uzaksa o projenin Sabitler'inde pay büyütülür.  **S1 = 6 mm²**:  4,9 – 15 kW'lık motorlarda ε ≤ %1,6 ve akım yeter;  daha büyük motorda yetmezse gerilim düşümü bölümü "kesiti büyütün" der ( 22 kW'ta S2 = 6 de yetmez, o da ayrıca uyarılır ).  S1 ve S2 Gelişmiş'te kalır:  kesit motora bağlıdır, çok asansörlü projede her asansöre ayrı verilebilmelidir.  Tesisteki en büyük koruma iletkeni ( SPE ) S1'i izler.  Altın çıktıda **hiçbir hüküm dönmedi** |
| **Topraklama şeridi boyu:  formdan kalktı, paftaya hesabıyla basılıyor** | Uygulama ve avan formunda "Topraklama şeridi boyu" kutusu vardı ve hep boş bırakılıyordu;  boşken motor boyu temel ölçülerinden türetiyor ama paftaya **"GİRİŞ"** diye basıyordu — sayının nereden geldiği görünmüyordu.  Elle yazılabildiği için aynı binaya avan ile uygulama farklı L ( dolayısıyla farklı topraklama direnci ) verebiliyordu | Kutu **iki formdan da** kaldırıldı;  şerit boyu her zaman temelden kurulur:  `L = 2·(a + b) + na·b + nb·a` — temelin çevresi kapalı halka, gözler Sabitler'deki **karelaj gözünü** ( 20 m ) geçmeyecek biçimde enine / boyuna bağ ( DIN 18014;  Topraklamalar Yönetmeliği yeni binada temel topraklayıcıyı zorunlu tutar ).  Pafta bunu işlemiyle basar ( *"şerit:  temel çevresi + karelaj bağları ( göz ≤ 20 m )"* );  avan ekranı kullanılan boyu açılımıyla gösterir.  Direnç bağıntısı `Ry = ρ/(2D) + ρ/L` ( IEEE Std 80 ) yönetmeliğin gözlü topraklayıcı yaklaşımından ( ρ/2D ) her zaman büyüktür — emniyetli taraf.  Motor elle verilen boyu hâlâ kabul eder ( API ve motor testleri ), ama kullanıcının bunu girebileceği bir kutu yoktur;  eski projelerdeki şerit değeri okunmaz.  Hiçbir hüküm dönmedi |
| **Regülatör gergi ağırlığı:  eşdeğer ağırlık** | Kutu "gergi ağırlığının kütlesi"ni soruyordu.  Güncel gergiler ise **kollu** ( 15 – 35 kg ağırlık, kol oranıyla büyütülür ) ya da **yaylı** ( ör. Dynatech COMPACT ) — hesaba giren, kasnak merkezindeki kuvvettir.  Kollu gergide ağırlığın kendi kütlesi girilirse halat gerilimi düşük, halat güvenlik katsayısı **iyimser** çıkıyordu:  referans projenin gerçek projesinde 35 kg kolda 1.030 N;  35 girilince S = 11,77, doğrusu 8,04 | Etiket "Regülatör gergi ağırlığı — **eşdeğer**";  ⓘ kasnak merkezindeki kuvvet / 9,81'in girilmesini, kollu ya da yaylı gergide kütlenin DEĞİL eşdeğerin yazılmasını söyler;  pafta satırı da buna göre adlandırıldı.  Hesap değişmedi:  eşdeğer 105 kg ile referans proje birebir ( e^(fα) 6,278 / 6,28 · S 8,10 / 8,04 ).  Kol ölçüleri için ayrı alan açılmadı — yaylı gergiyi kapsamazdı, eşdeğer ağırlık ikisini de kapsar |
| **k3 ( yardımcı donanım darbe katsayısı ):  1,2 → 2** | TS EN 81-20 Çizelge 14 k3'e sayı vermez ( *"imalatçı tarafından, gerçek tesise göre belirlenir"* ).  Ofis varsayılanı 1,2'ydi — bu, aynı çizelgedeki **k2**'nin ( Running ) değeridir;  Sabitler dosyasının başındaki not da yanlışlıkla *"k3 = 1,2 ( Çiz.14 )"* yazıyordu.  İki dış referans paftası ( referans proje örneği ve *new block* — *"karşı ağırlık zıplaması k3 = 2"* ) **2** kullanır | Varsayılan **k3 = 2**, gerekçesi koda yazıldı;  Sabitler'den değiştirilebilir.  k3 yalnız raya bağlı yardımcı donanım ağırlığını ( MY ) çarpar, etkisi küçüktür:  örnek projede karşı ağırlık rayı σv 2,16 → **2,24 N/mm²** ( ( 965,5 + 2 × 50 ) / 475, elle doğrulandı ), kuyu tabanı FKR +120 N, FAR +40 N.  155 referans senaryoda yalnız bu k3'e bağlı 13 ara değer değişti, **hiçbir hüküm dönmedi**;  avan ve trafik çıktıları birebir aynı |
| **Girdilerin ⓘ açıklaması** | Kutunun ne istediği yalnız etiketinden anlaşılıyordu.  Üç kaçıklık — *kabin merkezi* ( ağırlık nerede durur ), *askı noktası* ( yük nereden alınır ) ve *boş kabin ağırlık merkezi* — aynı sözcükle anılıyor, hepsi mm istiyor ve hiçbiri ölçüm orijinini söylemiyordu | **101 girdinin tamamında ( i ) dairesi**:  üzerine gelince alanın tanımı açılır.  Metinler motorda durur ( `MG.ACIKLAMA` · `UG.EK_ACIKLAMA` ), arayüz onları okur — JS'de kopya tutulsaydı ayrışırdı.  Sonuçlardaki **( ! )** yöntem anlatır, girdilerdeki **( i )** tanım verir.  TEST 8 sözleşmeye bağladı:  her alanın açıklaması olacak, 320 karakteri geçmeyecek, beş kaçıklık metni birbirinden farklı olacak ve her biri *ray ekseni*ni söyleyecek — açıklamasız yeni alan eklenemez |
| **Askı oranı gösterimi** | Etiket **`( 1 : n )`** yazıyordu — sektör gösteriminin tersi.  Oran halat hızının kabin hızına oranıdır:  paydadaki 1 KABİNDİR, baştaki sayı halat tarafına aittir.  Açılır listede de çıplak `1` / `2` görünüyordu;  okuyan 2:1 mi 1:2 mi ayırt edemiyordu.  Palangalı sistem uyarısı da `( 1:2 )` diye basıyordu | Etiket **`( n : 1 )`**, açılır liste **`1:1` / `2:1`** ( değer sayı kalır — hesap, kayıt ve geri yükleme ona bakar ), pafta satırı **`2 : 1`**, uyarı metni **`( 2:1 )`**.  Avan tarafı zaten doğruydu ( `ASKI_ORANLARI = {"1:1": 1, "2:1": 2}` ) ve dokunulmadı |
| **E paftada görünür** | Kabin rayı bölümünde E satırı vardı ama kaynağı **KABUL** yazıyordu — oysa çeliğin elastisite modülü bir ofis kabulü değildir, ofis sabitlerinden de değiştirilemez.  **Karşı ağırlık rayı bölümünde ise E hiç yazmıyordu**;  sehim satırı `48 × E × Ix` diye basıp E'nin sayısını hiçbir yerde göstermiyordu | İki bölümde de **E = 210.000 N/mm²** satırı, kaynağı *EN 81-50 m.5.13 · EN 1993-1-1 m.3.2.6*.  Altın çıktıda E satırları dışında tek bir fark yok ( 24 yeni satır · 24 kaynak güncellemesi · "E dışı fark: 0" ) |
| **Sığınma hacmi tipleri** | *Kabin üstü* ve *kuyu dibi sığınma hacmi tipi* Gelişmiş'teydi.  İkisi de her projede verilen bir yerleşim kararıdır ve kuyu üst / alt boşluğunu doğrudan belirler ( m.5.2.5.7 · m.5.2.5.8 ) | *Durak ve kuyu* grubunda **görünür**.  Gelişmiş 57'den 55'e indi;  hesapta hiçbir sayı değişmedi |
| **Karşı ağırlık yeri** | *Kabin ve kapı* grubunda ve **Gelişmiş**'teydi.  Oysa yerleşimin en temel kararıdır ve her projede seçilir;  üstelik hesabı da etkiler:  ağırlık yanda ( Sağ / Sol ) olduğunda rayları 90° dönük monte edilir, binanın δstr-x sehimi ağırlık rayının Y eksenine, δstr-y ise X eksenine gelir.  Gelişmiş'e alınırken yapılan beş projelik tarama "hiçbir sayıyı değiştirmiyor" demişti — yanıltıcıydı, o projelerde δstr boştu.  Ayrıca *karşı ağırlık rayları* ve *kuyu tabanı* bölümlerinin girdisi olduğu hâlde revizyon ekranı onu o bölümlerin grupları arasında göstermiyordu | **Karşı ağırlık** grubunun ilk alanı ve **görünür**.  Gelişmiş 58'den 57'ye indi;  hesapta hiçbir sayı değişmedi |
| **Hiçbir şeye girmeyen girdiler** | *Kuyu derinliği* ve *ağırlık ray merkezi – duvar* yalnız artık türetilmeyen halat arasının denetiminde okunuyordu;  *ağırlık ray arası* paftada yalnız "hesaba girmez" notlu bir bilgi satırıydı ( CAD çizimi de kullanmıyordu );  *dikine kiriş profili* ve *yan yatak profili* kutularının tek seçeneği vardı ( NPU ) | Beşi de **kaldırıldı**.  Beş projelik taramada hesabın hiçbir sayısını değiştirmiyorlardı;  pafta profili "NPU <ölçü>" diye yazmaya devam eder |
| **Nps ( tek yönde bükülmeli kasnak sayısı )** | Varsayılan 1'di;  2:1 askıda programın kendi uyarısına ( "en az iki kabin kasnağı" ) takılıyor, Nequiv ve gereken Sf olduğundan küçük çıkıyordu | Boş bırakılırsa **askı oranından** gelir ( TS EN 81-50 Ek E ):  **1:1 → 1** ( Şekil E.2, saptırma kasnağı ) · **2:1 → 2** ( Şekil E.1, iki kabin kasnağı;  ofis düzeninde saptırma karşı ağırlık tarafındadır, o kesit de 2 kasnaktır ).  Saptırma kabin tarafındaysa değer elle girilir ( 3 ).  Paftada kaynağı "askı oranından · TS EN 81-50 Ek E" yazar.  175 senaryoda hüküm dönmedi;  2:1 senaryolarda Sf büyüdü ( varsayılan projede 23,61 → 24,28 ) |
| **MRL makine yükü dört raya** | "Kılavuz raylara" seçilince makinenin yükü ( Gm + Tst ) yalnız KABİN raylarına bölünüyordu;  karşı ağırlık rayları makineyi hiç görmüyordu ( 50 N ofis kabulü ) | Yük **kabin ve karşı ağırlık raylarının toplam sayısına** ( 2 + 2 = 4 ) eşit bölünür;  iki ray da paftada "( Gm + Tst ) / 4 ray" yazar.  Karşı ağırlık rayı bu payı σv · σc'de, kuyu tabanı da FAR'da görür.  Referans proje de yükü dört raya verir.  Yalnız makine raylarda olan dört senaryo değişti, hüküm dönmedi ( örnek:  kabin rayı payı 7.974 → 3.987 N · FAR 1.026 → 5.750 N ) |
| **Boş kabinin ağırlık merkezi ( xp · yp )** | Yalnız türetiliyordu ( gövde kabin merkezinde, kapı kapı tarafında, yp = yc );  imalatçının ağırlık merkezi girilemiyordu — referans proje örneğinde xp = +250 mm iken kabin merkezi −140 mm | Kabin ve kapı · **Gelişmiş**'e iki isteğe bağlı kutu:  boşsa türetilir ( sonuç değişmez ), girilirse standardın P'sine ( kapı, gezici kablo, zincir dahil ) uygulanır ve paftada kaynağı GİRİŞ yazar.  Referans projenin kabin rayı kuvvetleri böylece birebir çıkar ( TEST 12 ) |
| **Ray çeliği Rm = 450** | Seçenekler 370 · 440 · 520'ydi | **450 eklendi.**  ISO 7465:2007 m.5 çekme dayanımını 370 – 520 N/mm² arasında ister ( işlenmiş ray için E 275 B ).  ω EN 81-50 m.5.10.3'ün doğrusal ara değerinden, σperm = Rm / St'den gelir — yeni tablo gerekmez.  Referans proje ile birebir:  σperm 250 · 200 N/mm², λ = 128,45'te ω = 3,53 |
| **Tabliye beton yüksekliği** | Adı "Kaide yüksekliği"ydi ( 750 mm, Gelişmiş ) ve MRL projede de kılavuz ray ile regülatör halatı boyuna 750 − 200 mm ekleniyordu — olmayan bir tabliye | Adı **Tabliye beton yüksekliği**, varsayılanı **1.200 mm** ( ofisin makine daireli şablonu ).  **Yalnız makine daireli projede sorulur** ( Durak ve kuyu, görünür );  MRL'de gizlidir ve hesaba **0** girer.  Pafta ray boyunda "MRL:  tabliye yok" yazar  ·  **5 Eki:**  anlamı düzeltildi — **makine dairesi zemininden kuyunun üstündeki beton tabliyenin üstüne yükseklik** ( LiftDesigner'ın makine daireli üç projesinde 1.200;  betonun kalınlığı ayrıca 120 ).  Ofisin Excel'i bunu "Kaide Yüksekliği" diye alır ve son katı "en üst durak + kaide − 200" girdirir;  programda son kat kuyu tavanına ölçüldüğünden **ray ve regülatör halatı boyuna artık eklenmez** ( eskiden iki kez sayılıyordu:  makine daireli 148 senaryoda ray boyu 1 m kısaldı, hiçbir hüküm dönmedi ) |
| **MRL'de makine kirişi ( bölüm 2 )** | MRL'de bölüm 2 "UYGULANMAZ" diyordu;  makinenin oturduğu kuyu üstü kiriş hiçbir yerde denetlenmiyordu | Bölüm 2 MRL'de **makine kirişlerini** hesaplar:  kaidenin yatay kirişiyle aynı statik ( F = k1·gn·( Q+P+Gh+Ga+Gm ), iki kiriş, σe ≤ σem ).  Tabliye ve kolon olmadığı için burkulma kontrolü yapılmaz;  şase yüksekliği ve dikine kiriş MRL'de gizlidir, **yan yatak ( makine kirişi ) ve boyu iki yerleşimde de sorulur**.  Kiriş varsayılanı **NPU 140** ( sahada genelde;  örnek projede 120 ).  176 senaryoda hüküm yalnız bölüm 2'de değişti:  NPU 140 ile 10 daireli senaryo "uygun değil"den "uygun"a, 6 MRL senaryosu "uygulanmaz"dan "uygun"a geçti |
| **Proje dosyası açılınca ekran ( uygulama )** | `.uygulama` dosyası verisi eksiksiz geri geliyordu ve hesap aynıydı;  ama asansör formu açıkken dosya yüklenince makine dairesi düğmesi ve yerleşime göre gizlenen alanlar YENİLENMİYORDU:  makine daireli projede düğme "Yok ( MRL )" gösteriyor, tabliye ve makine dairesi ölçüleri gizli kalıyordu.  TEST 6 bunu göremiyordu — onay kutularını iki asansör için iki kez çevirip makine dairesiz ( varsayılan ) bir dosya kaydediyordu | Yükleme sonrası düğme, gizlenen alanlar, kanal uyumu ve Gelişmiş sayaçları değerlere uydurulur.  TEST 6 artık makine daireli bir dosyayı gidiş-dönüş yapar ve ekranın yüklenen değeri gösterdiğini de denetler ( düzeltme kaldırılınca iki kontrol kalır ) |
| **Makine verimi projeye özel** | Motor gücündeki toplam sistem verimi η yalnız makine tipinden, Sabitler'deki ofis değerinden geliyordu ( dişlisiz · dişli ).  Her projenin makinesi başka ve imalatçının verimi ofis değerinden ayrılabiliyor;  tek projenin verimini değiştirmenin yolu ofis değerini, yani BÜTÜN projeleri değiştirmekti | Makine ve motor · **Gelişmiş**'e isteğe bağlı **Toplam sistem verimi η ( imalatçı )** kutusu ( 0,1 – 1 ):  boşsa ofis değeri kullanılır ( sonuç değişmez — 176 senaryonun hiçbirinde bir sayı değişmedi ),  girilirse motor gücü onunla hesaplanır, paftada kaynağı KATALOG yazar ve elektrik hesaplarına aynı değer geçer.  Anlamı ofis değeriyle aynıdır:  askı ( palanga ) kaybı dâhil |
| **Hız regülatörü imalatçı değerleri** | Devreye sokma kuvveti girilmezse regülatör bölümü *HESAP EKSİK* sayılıyor, proje uygun çıkmıyordu;  bu yüzden her projede bir sayı yazılıyordu ( çoğu zaman 300 — oysa 300 N regülatörün üretmesi gereken en küçük kuvvettir, fren bloğunun kuvveti değil;  300 yazınca sınır 600 N oluyordu ).  Kuvvet fren bloğunun belgesindedir ve proje aşamasında çoğu zaman bilinmez:  yerli bir üreticinin kullanma kılavuzunda bile yazmıyor, referans proje yalnız 300 N'a bakıyor.  Devreye girme hızı sınırları iki haneyle yazılıyordu ( 2,156 → "< 2,16" ):  reddedilen 2,158 paftada sınırın içinde görünüyordu | Hız regülatörü grubunun **bütün alanları Gelişmiş'te**, iki imalatçı değeri boş gelir.  **Kuvvet boşsa** 300 N denetlenir ve paftaya *"Şart:  Fgt ≤ Fçekme / 2"* yazılır ( tip inceleme belgesinden doğrulanır );  girilirse `max( 300 ; 2 × kuvvet )` aranır.  **Hız boşsa** aralık ve standardın önerisi yazılır ( v > 1 m/s'de üst, düşük hızda alt sınıra olabildiğince yakın );  hesaplanan bir varsayılan konmadı — gerçek değer siparişte belirlenir ve regülatörün etiketinde yazar ( m.5.6.2.2.1.8 ), formülden üretilen sayı aynı formülle denetlenince hep geçerdi.  Sınırlar üç haneyle yazılır.  176 senaryoda yalnız regülatör bölümü değişti ( HESAP EKSİK → UYGUN;  ikisi ani frenlemeli tertibatın hız sınırından kalıyor ve artık sebebini yazıyor );  hiçbir projenin genel sonucu değişmedi |
| **Regülatör sürtünme faktörü µ** | Asansör bazında soruluyordu ve 0,2'nin altı kabul ediliyordu.  Oysa TS EN 81-20 m.5.6.2.2.1.3 b) halatın emniyet katsayısının **µmax = 0,2 ile** hesaplanmasını istiyor;  küçük µ katsayıyı olduğundan iyi gösteriyordu ( 0,2'de 16,77 iken 0,1'de 42,02 ) | Kutu kalktı, **ofis sabiti** oldu ( Sabitler · ②d HIZ REGÜLATÖRÜ, varsayılan 0,2, üst sınır standardın sayısı ).  Paftada kaynağı *OFİS STANDARDI · m.5.6.2.2.1.3 b) µmax* yazar.  176 senaryoda **tek bir sayı değişmedi**;  yalnız bu satırın kaynak yazısı değişti |
| **Paftadaki kaynak sütunu** | Aynı sınıftaki değerler beş ayrı biçimde yazılıyordu:  *OFİS STANDARDI · Ofis kabulü · OFİS KABULÜ · OFİS TABLOSU · SABİTLER A / B · TABLOLAR T2 · ofis sabiti*.  Hem dağınıktı hem de paftayı okuyan için "ofis" sözü bir anlam taşımıyordu;  ayrıca katalogdan girilen değerler de "GİRİŞ — imalatçı kataloğu" gibi ayrı ayrı yazılıyordu | Kaynak sütununda **üç söz** kalır:  **GİRİŞ** ( projeyi yapanın beyanı ), **KATALOG** ( imalatçının kataloğundan / tip inceleme belgesinden girilen değer ), **KABUL** ( ofisin kabulü;  gerektiğinde gerekçesiyle — *KABUL · EN 81-20 Çiz.14 sayı vermez, imalatçı belirler* ).  Standardın kendi sayıları eskisi gibi madde numarasıyla yazılır ( *EN 81-50 m.5.11.3* ), türetilenler türetmeyi yazar.  Paftada "ofis" sözü hiç geçmez.  Avan ve uygulama paftalarının ikisinde de aynı düzen.  **Hiçbir sayı ve hiçbir hüküm değişmedi** — sayıları tutan iki referans dosyası bire bir aynı kaldı |
| **Girilen değer kullanılamıyorsa hesap durur** | Aralık dışı bir değer ( asansör kartında S1 = 0,5 mm², Nsç = 600 kW, i = 9 · ofis sekmesinde β = 0,5 ) **varsayılanla değiştiriliyor** ve hesap sürüyordu:  pafta kullanıcının yazmadığı bir sayıyla hesaplanıp "UYGUN" diyebiliyordu.  Avan bunu bir uyarıyla söylüyordu;  ortak paneldeki β / Is ile uygulamanın bütün ofis sabitleri ise **hiçbir iz bırakmadan** varsayılana dönüyordu ( β = 0,5 yazılan projenin topraklaması 150 Ω·m ile hesaplanıyordu ).  Avanda ηm'nin hiç aralığı yoktu | Tek kural:  **yazılan sayı ya kullanılır ya da hesap durur**, boş bırakılan alan varsayılanı kullanır.  Asansör kartındaki hata o asansörü durdurur ( ötekiler hesaplanır ) ve **bütün hatalı alanlar tek seferde** adı ve aralığıyla söylenir;  ofis sekmesi ile ortak paneldeki hata projeyi durdurur.  Ekran, PDF ve paket aynı kararı verir.  ηm'ye 0,10 - 1 aralığı verildi ( uygulamadakiyle aynı ).  Uygulamada kolon ve makine besleme kesitleri avanın S1 / S2 aralığıyla girişte denetlenir |
| **Okunamayan yazım boş sayılıyordu** | Anma yüküne `1000 kg` yazılınca değer sessizce boşa düşüyor, motor **Tablo-7'deki yükle** hesap yapıyordu;  aynısı asansör kartının, trafik formunun ve uygulama formunun bütün sayı alanlarında vardı ( ofis sekmesi bunu zaten reddediyordu ).  Kişi sayısı okunamayan asansör trafik hesabından sessizce düşüyordu | Sayı alanlarının hepsi tek kapıdan okunur ( `uclar/uc_ortak._sayi_oku` ):  boş → varsayılan, belirsiz → *Belirsiz sayı*, okunamayan → *Girdi kabul edilmedi*.  Red metni alanı iç adıyla ( `Q_elle` ) değil ekrandaki adıyla söyler.  Tanımsız kolonda kalmış değer projeyi durdurmaz |
| **Proje geneli alan asansör girdisiyle eziliyordu ( uygulama )** | Çoklu hesapta asansörün kendi değeri proje genelinin önüne geçiyordu:  eski bir `.uygulama` dosyasından asansörün içinde kalmış `temel_a = 10`, Proje sekmesinde 20 yazılıyken binanın topraklamasını 10 ile hesaplatıyordu | Temel ölçüleri ve makine dairesi alanlarında **proje geneli kazanır**;  API asansörün içindeki kopyayı hiç okumaz |
| **Onay kutusu iki kuralla okunuyordu** | API'nin kendi kopyası `Var`ı HAYIR, motor EVET okuyordu:  ekranda gizlenen alanlar bir kurala, hesap öbürüne göre seçiliyordu | Tek okuma kuralı ( `steps.evet_mi` ) |
| **Yuvarlama:  pafta, ekran, Tablolar sekmesi ve hesap ayrı kurallar** | Paftadaki sayı Python'un biçimlendirmesiyle, ekrandaki JavaScript'inkiyle, hesap içi yuvarlama ( `steps.yuvarla` ) elle yazılmış `floor( x + 0,5 )` ile yuvarlanıyordu.  Üçü de sayının İKİLİ değerine bakıyordu:  9,325 ikilide 9,32499… diye saklandığı için paftada **9,32**, 1,005 hesapta **1,00** oluyordu.  Pafta tam yarımda bankacı kuralı uyguluyordu ( 2,5 → **2**, 0,125 → **0,12** ), ekran uygulamıyordu:  20.125 değerlik taramada ekran ile pafta **168 değerde farklı** yazıyordu | Üçü de aynı kuralla yuvarlar:  sayı 12 anlamlı haneye indirilip gürültüden arındırılır, yarımı sıfırdan uzağa yuvarlanır ( ondalık aritmetik ).  Ekran ile pafta artık hiçbir değerde ayrışmıyor ( TEST 5 tarayıcıda 3.125 değerle denetler ).  Altın senaryolarda **55 basılı sayı** son hanesinde bir arttı ( ör. trafik 9,32 → 9,33 · uygulama Pm 347,83 → 347,84 · T2 4.978,57 → 4.978,58 );  hiçbir hüküm değişmedi.  Tablolar sekmesi de aynı kurala bağlandı ( ω tablosunda λ = 150 · Rm = 520:  5,6992 → 5,6993 ) |
| **Paftada boş imza kutusu ve gereksiz açıklama** | Avan, mukavemet ve uygulama paftalarının sonuç özeti altında boş bir *Hesabı yapan · Kontrol eden · Onay* kutusu duruyordu;  proje geneli hesaplar şeridi *"bütün asansörler için bir kez"* yazıyor ve altında *"BİNAYA aittir … bir kez basılır"* kutusu basılıyordu ( tek asansörlü projede de ) | İkisi de paftadan çıkarıldı ( imza bilgisi kapak sayfasındadır, trafik paftasında olduğu gibi ).  Avan paftası bir sayfa kısaldı |
| **Askı halatı 8 mm sınırı denetlenmiyordu** | TS EN 81-20 m.5.5.1.2 a) askı halatının anma çapının **en az 8 mm** olmasını ister;  formun ⓘ açıklaması da bunu yazıyordu, ama motor denetlemiyordu:  400 mm kasnakta 6 mm halat, belgesiz, **"UYGUNDUR"** çıkıyordu.  D/d yetersizken pafta "halat çapını küçültün" diyor, 240 mm kasnakta 6,5 mm halatı 8 mm'nin daha da altına itiyordu.  Regülatörde de aynı öğüt en ince halatta bile basılıyordu | 8 mm altı halat **UYGUN DEĞİL**, mevcut tek belge seçimi **Var** ise **BELGEYLE UYGUN** ( ince halat ile küçük kasnak sahada aynı onaylanmış kuruluş belgesiyle kullanılır — yeni kutu açılmadı;  seçimin adı *"Dt/dh < 40 ya da halat çapı < 8 mm için onaylanmış kuruluş belgesi"* oldu ).  Belge satırı hangi maddeden sapıldığını yazar.  Hüküm, standarda uyan en yakın çifti söyler ( 240 / 6,5:  *"en az 8 mm halat ve en az 320 mm kasnak kullanın ya da onaylanmış kuruluş belgesini beyan edin"* );  incelmeyi yalnız 8 mm'nin altına inmeden oranı tutturuyorsa önerir.  Taramada tek hüküm döndü ( 240 mm kasnakta 6 mm halat, oran tam 40 );  240 / 6,5 zaten belge istiyordu, kullanımda değişiklik yok.  Regülatör halatı için "en az 6 mm" açıklaması düzeltildi:  EN 81-20 bu halata çap sınırı vermez ( yalnız Dreg/dreg ≥ 30, m.5.6.2.2.1.3 c) ) |
| **Kabin rayı Fx · Fy ve σc elle doğrulanamıyordu** | Güvenlik tertibatı ( C.2.1 ) ve normal işletme ( C.2.2 ) durumlarında Fx ile Fy'nin işlem satırı sayıları değil formülün kendisini tekrar ediyordu ( *"k1 × gn × ( Q·xQ + P·xp ) / ( n × h )  → 965,07"* );  yükleme durumunda ( C.2.3 ) σc *"σv + σm"* yazıyordu.  Aynı bölümün öbür satırları ve karşı ağırlık rayı sayılarla basılıyordu — paftayı denetleyen bu satırlarda sonuca hesap makinesiyle ulaşamıyordu | Sayılar yerine konarak basılır ( *"2,00 × 9,81 × ( 800 × 323,75 + 713 × 92,00 ) / ( 2 × 3.300 )"* ).  Hiçbir değer değişmedi ( değer aynı ifadeyle hesaplanıyor );  TEST 14'ün yeniden hesapladığı satır 27.691 → **29.275** ( eklenen 1.584 satırın hepsi tutarlı ).  Satır sütuna sığmadığında çarpımlar ve payda **bölünmez boşlukla** bağlanır:  kırılma paydanın ortasına değil, *"/ ( 2 × 3.300 )"* grubunun önüne düşer |
| **Avanda karşı ağırlık rayı ( PK ) kitaptan sapıyordu** | PK her zaman `k1 · gn · Ga / n + Mg · gn` ile, yani karşı ağırlıkta güvenlik tertibatı varmış gibi hesaplanıyordu.  MMO/697 ( s.20 ) *"kılavuz rayı üzerinde güvenlik tertibatı etki etmemesinde k1 = 0"* der;  kitabın iki çözümlü örneği ( s.55 · s.56 ) Pk'yı *"karşı ağırlıkta güvenlik tertibatı olmadığından"* hesaplamaz.  Aynı asansörde uygulamanın karşı ağırlık rayı kuvvetinin 10 katına varıyordu | Asansör kartında *Karşı ağırlıkta güvenlik tertibatı:  Yok / Var* ( varsayılan **Yok**, kitabın örnekleri gibi ).  Yok → `PK = Mg · gn` ( k1 = 0 );  Var → eski bağıntı.  Altın ve referans senaryolarında değişen tek hesap değeri PK.  k1'e dokunulmadı:  kitabın Çizelge-1'i hıza göre verir ( 0,63-1 m/s'de 3 ) — EN 81-20 bu aralıkta kabinde yalnız kaymalı tertibata izin verdiği için 2 olmalıydı, ama kitabın değeri emniyetli tarafta ve avan kitaba göre denetlenir |
| **Avanda denge zinciri yoktu** | Kitabın ( s.20 ) ve EN 81-20'nin ( m.5.2.1.8.5 ) P tanımı *"dengeleme halatları/zincirleri ( varsa )"* içerir;  avan motorunda zincir kavramı hiç yoktu.  Zincirli yüksek binada ( 1.600 kg · 2,5 m/s · 80 m ) tampon altı kuvvetleri uygulama projesinden **%17-23 düşük** — emniyetsiz yönde — çıkıyordu | Asansör kartında *Denge zinciri:  Yok / Var* ( varsayılan Yok ).  Var → `P = Gk + Gf + Gz`, `Gz = mz · Hk`.  Kitap da standart da mz için sayı vermez;  EN 81-20 m.5.5.6.1 zincirin halat ağırlığını dengelediğini söyler.  Ofis kabulü ( Sabitler ) = ofisin halat düzeni 7 × Ø6,5 · 2:1 → **2,13 kg/m** ( λ = %100, uygulamayla aynı );  ağır asansörde kartın "farklı değerler" bölümünden girilir, SORULMAZ.  Aynı senaryoda avan artık uygulamadan %2-3 FAZLA ( kuyu yüksekliği ≥ seyir ) buluyor.  2,128 değeri "belirsiz sayı" kuralına takılıp örnek projenin bütün avan hesabını durdurduğu için iki haneye yuvarlandı;  artık hiçbir varsayılanın bu biçime düşmediğini TEST 3 denetliyor |
| **"Q elle" girilmiş avan kartı bir hesap boyunca kayboluyordu** | Trafik bir kartın kapasitesini bir kez yazınca kart "otomatik" sayılıyordu;  kullanıcı o karta Q elle girmiş olsa bile trafik grubu küçülünce kart kapanıyor, kapasite / hız siliniyor, Q elle kalıyordu.  Bir sonraki eşitlemede kart yeniden açılıyor;  arada ekranda ve indirilen paftada o asansör hesap dışıydı.  Ağ gecikmesine bağlı, TEST 13'ün rastgele dizisi buldu | Q elle trafik tarafından hiç yazılmaz, o hâlde her zaman kullanıcı verisidir:  dolu kart sayımı ( `avanDoluUst` ) onu otomatik işaretten bağımsız sayar.  TEST 5'e gecikmeye bağlı olmayan deneme eklendi ( kart kapanmıyor · eşitleme ikinci kez çalışınca hiçbir şey değişmiyor );  eski kodda ikisi de düşüyor |
| **Avan motor gücü kitaptan emniyetsiz yöne sapıyordu** | MMO/697 §2.4 *"palangalı sistemlerde verim %10 az alınacaktır"* der, çözümlü örneği ( §4.4, s.56 ) η = 0,5 − 0,1 = 0,4 ile 22 kW bulur.  Program bu düşüşü 2026-09-08'de avandan da kaldırmış, paftaya *"Δη = 0,10 palanga düşüşü artık uygulanmaz … cezalandırıyordu"* yazıyordu.  800 kg · 1,6 m/s · 2:1 · η 0,85'te 7,5 kW seçiyordu;  kitaba göre inceleyen 8,37 kW bulur ve motoru reddeder | Avanda palangalı ( 2:1 ve üstü ) sistemde `η′ = η − 0,10` paftada ayrı satır, kaynağı MMO/697 §2.4;  η etiketi *makine verimi ( askı kaybı hariç )*;  "artık uygulanmaz" notu kalktı.  η′ ≤ 0 ise ( η ≤ 0,10 · 2:1 ) asansör durur.  **Uygulama projesi değişmedi:**  orada η toplam sistem verimidir;  elektrik hesabını avan motorunda koştuğu için köprü `eta_toplam` bayrağı geçirir ( altın ve referans çıktıları birebir aynı ).  Avan altın çıktısında 74 palangalı asansörde η′ ve N, 27'sinde motor kademesi ve elektrik bölümleri değişti;  kuvvet ve aydınlatma bölümleri aynı.  Büyüyen motorun 6 mm² kabloyu aştığı 6 senaryoda ( 18,5 → 22 kW ) akım kontrolü artık doğru olarak UYGUN DEĞİL diyor.  TEST 2'ye kitabın örneği birebir eklendi ( N1 = 22 kW · N2 = 7,05 kW ) |
| **Taahhütname ile tek asansör** | Öneri tablosu ve hesap notu "şartlı kabulle 1 adet yeterli olurdu ( taahhütname )" diyordu ama bu adedi seçmenin yolu yoktu:  tek asansör tanımında program adedi hep Standart / Yükseltilmiş sınırıyla buluyordu ( elle adet kutusu v2.0'da trafik gövdeleri birleşirken düşmüştü ) | Trafik formunda **Taahhütname:  Yok / Var** seçimi.  **Var** iken bekleme ölçütü MMO/697 Tablo-10 **şartlı kabul** sınırıdır ( konutta 120 sn ):  o sınırda yeten adet uygulanır, pafta "Şartlı Kabul ( taahhütname ile )" der ve Standart için gereken adedi de yazar;  avan sekmesi bu adedi alır.  Taşıma kapasitesi yine aranır.  Şartlı sınırı olmayan bina tipinde ( kamu, hastane ) **Var** hesabı durdurur;  gerekmiyorsa bilgi notu düşülür.  Yalnız tek asansör tanımında görünür — 2–4 asansörde adedi kullanıcı verir |
| **Makine dairesi aydınlatmasının tablosu ( çok asansörlü proje )** | Devre her zaman 1. asansörün tablosuna ( TAS1 ) bağlanıyordu.  1. asansörün hesabı düşünce o tablo çizilmiyor, öbür asansörlerin şeması "Aydınlatma devresi:  TAS1" diyordu — devre ve yükü pakette hiçbir tabloda yoktu | Elektriği hesaplanan ilk asansörün tablosundan beslenir ( avan ve uygulama );  bütün asansörler hesaplanınca yine TAS1 |
| **Grup sigortası ↔ makine besleme kablosu** | Yalnız motor akımı kabloyla karşılaştırılıyordu ( `I2 ≤ Iz2` );  seçilen sigortanın kabloyu koruyup korumadığına bakılmıyordu:  15 kW motor + S2 = 4 mm² → 4 x 40 A sigorta, 11 kW + 2,5 mm² → 4 x 32 A — bölüm 6 "uygundur" diyordu.  Aynı kural ( EK-5 1.31.13 ) son devrelerin kablosunda uygulanıyordu | Bölüm 6'da `In ≤ Inmax2`:  grup sigortası kablonun önündeki en büyük değeri aşamaz — 6 mm²'ye kadar Asansör Periyodik Kontrol Yönetmeliği EK-5 1.31.13 ( 1,5 → 10 · 2,5 → 20 · 4 → 32 · 6 → 50 A ), üstünde Iz.  Aşınca bölüm uygun değil ve engelleyici uyarı;  uyarı iki koşulu ( akım ve sigorta ) birlikte sağlayan en küçük kesiti söyler |

**Canlı hesap artık kalıcı olarak denetleniyor ( TEST 13 ).**  Tarayıcıda iki proje
modunun her girdisi tek tek değiştirilir ve tohumlu rastgele değişiklik dizileri
yapay ağ gecikmesiyle art arda uygulanır;  her seferinde **ekrandaki sonuç = formun
sunucudaki taze hesabı = indirilen çıktının girdisi** olmalıdır.  Yukarıdaki üç
ekran hatası bu testle bulundu;  her biri geri alındığında test onu yakalıyor.
Sıra hatası ise TEST 11'de her sıralama denenerek sabitlendi;  aynı tarama avan
ve trafik motorlarında da yapıldı, orada sıraya bağlı bir hesap farkı yok.

**Paftadaki işlem satırları da artık kalıcı olarak denetleniyor ( TEST 14 ).**  Bütün
senaryolarda her hesap satırının işlemi, basıldığı hanelerin yuvarlama belirsizliği
hesaba katılarak ( aralık aritmetiği ) yeniden hesaplanır;  basılan sonuç o sayılarla
bulunamıyorsa test durur.  Yukarıdaki düzeltmelerden biri geri alındığında test onu
yakalıyor;  tek istisna 10 N yuvarlamasıdır — fark çoğu satırda yazılı sayıların
kendi yuvarlama payı içinde kalır, yalnız aştığı senaryoda görünür.

**Sürüm 3.1** — **Excel tamamen kaldırıldı.  Her şey programdan yapılır.**

| | Önce | Sonra |
|---|---|---|
| **Çıktılar** | PDF · CAD · XLSX ( ofisin Excel şablonları doldurularak ) | **PDF · CAD** — hesabın tek kaynağı motordur, çıktılar ondan üretilir |
| **Revizyon** | Proje dosyası ya da programın ürettiği Excel'den geri yükleme | Yalnız **proje dosyası** ( `.avan` · `.uygulama` ) — girdileri taşır, hesap bilgisi taşımaz |
| **Şablonlar** | `templates/` altında üç Excel şablonu, şablon denetimi, `araclar/` altında şablon betikleri | Kaldırıldı;  `templates/` yalnız CAD proje formatını ( `proje_formati.dxf` ) tutar |
| **Kitaplık** | `openpyxl` | Gerekmiyor |
| **Doğrulama** | TEST 1 ve 10 girdileri Excel'e yazıp LibreOffice ile hesaplatıyordu | Aynı senaryoların Excel ile doğrulanmış sonuçları **donduruldu** ( `dogrulama/referans_*.json.gz` );  TEST 1 ve 10 motoru bu referansa karşı denetler, LibreOffice gerekmez |

Neden:  aynı hesabı iki kez ( motorda ve Excel formüllerinde ) tutmak iki belgenin
ayrışmasına yol açıyordu;  canlı formüllü bir çalışma kitabı teslim etmek de
hesap aracının kendisini teslim etmek demekti.  PDF ve CAD sonucu gösterir,
aracı vermez.

Motorun ara değerleri artık Excel hücre adresiyle değil adıyla tutulur
( `sonuc["ara"]["kabin_ray.c21.d1.sf"]` gibi );  standart gereği verilen hesap
kararları 6. bölümdeki tabloda ve TEST 9'un kural denetimlerindedir.

> Aşağıdaki eski sürüm notlarında ve 6. bölümün denetim kayıtlarında geçen
> **XLSX · şablon · kitap · Excel'den geri yükleme** maddeleri Sürüm 3.1'den
> öncesine aittir;  tarihçe olarak bırakılmıştır.

**Sürüm 3.0** — **uygulama projesi eklendi.**

Program artık iki proje türü hazırlıyor. Açılışta hangisi olduğu seçiliyor;
sekme şeridi, girdiler ve çıktılar ona göre değişiyor.

| | Ne geldi |
|---|---|
| **Mukavemet** | 10 bölüm: motor gücü · makine konstrüksiyonu · kabin alanı · askı halatları · regülatör halatı · tahrik yeteneği ( 4 yük durumu ) · kabin kılavuz rayları ( C.2.1 / C.2.2 / C.2.3 ) · karşı ağırlık rayları · kuyu tabanı yükleri · sığınma alanları |
| **Elektrik ve topraklama** | Kabin ve kuyu aydınlatması, kurulu güç cetveli, gerilim düşümü, makine dairesi aydınlatması, temel topraklama. **Avan motoru çağrılıyor** — kopyalanmadı |
| **Ortak girdi köprüsü** | Kabin ölçüleri, beyan yükü, hız, kuyu boyu, motor gücü, askı oranı, ray profili **bir kez** giriliyor; elektrik tarafına kendiliğinden geçiyor |
| **Çıktılar** | Uygulama projesi PDF ( bütün bölümler tek paftada ) · Excel ( kaynak çalışma kitabı ) · CAD · revizyon akışı |

**Kaynak Excel'de yedi hata bulundu ve TS EN 81-20 / TS EN 81-50'ye göre
düzeltildi** — dördü hesabı olduğundan **iyi** gösteriyordu. Ayrıntısı 6.
bölümdeki tabloda; hepsi kodda `EXCEL_FARKLARI` altında standart maddesiyle
kayıtlı ve her biri için "gerçekten uygulanıyor mu" testi var.

**Teslim edilen Excel de düzeltiliyor.** Program kitaptan ayrıldığı için, kitap
olduğu gibi verilseydi aynı projenin iki belgesi birbirini yalanlardı. Teslim
kopyasında ilgili **formüller** düzeltiliyor ( değerler değil ), kitap kendi
kendini hesaplamaya devam ediyor. Doğrulama paketi ikisinin **hücre hücre aynı**
olduğunu denetliyor. Şablon dosyasına dokunulmuyor.

**Kod avan ve uygulama diye ayrıldı** — hesap motorları ( `engine/avan` ·
`engine/uygulama` ), HTTP uçları ( `uclar/avan_uclari.py` · `uclar/uygulama_uclari.py` ) ve arayüz
betikleri ( `avan.js` · `uygulama.js` ) ayrı dosyalarda. Ortak olan yalnız
gerçekten ortak olanlar ( bkz. 9. bölüm ). Ayrıştırmadan önce ve sonra doğrulama
paketi **aynı sayıyı** verdi — o gün 24.592 kontrol, tek bir hesap sonucu
değişmedi. ( Paket sonradan büyüdü;  bugünkü sayı 6. bölümdedir. )

**Doğrulama paketi 7 testten 11'e çıktı.** Yenileri: mukavemet tabloları ·
mukavemet motoru · mukavemet ↔ Excel ( girdi uzayı taraması ) · uygulama
projesi ( ortak girdi köprüsü ).

---

**Sürüm 2.0** — **tekli / çoklu ayrımı kalktı.  Yöntemi artık veri belirliyor.**

Trafik sekmesinde iki ayrı gövde ( tek hesap · grup hesabı ) ve aralarında seçim
yapan bir düğme vardı. Kullanıcının, hangi MMO yönteminin uygulanacağına karar
vermesi gerekiyordu — oysa bu karar **girdiden çıkarılabilir**. Artık öyle:

| | Önce | Sonra |
|---|---|---|
| **Ekran** | İki gövde; "asansör adedi 1" tek hesabı, "2-4" grup hesabını açıyordu | **Tek gövde.** Adet seçicisi duruyor ama anlamı değişti: *"Kaç asansör tanımlıyorsunuz"* — yöntem değil, veri |
| **Yöntem** | Kullanıcı seçiyordu | **Program çıkarıyor:** asansörlerin hepsi aynı tipse MMO/697 s.11-12 yolu ( `PAFTA` ), farklı tip varsa grup formülü ( `PAFTA-COKLU` ) |
| **1 asansör tanımı** | "kaç gerekir" hesabı | **Aynı** — eski davranışın birebir kopyası ( 87 senaryonun 87'sinde özet **bit bit aynı** çıktı ) |
| **2-4 aynı tip** | Yalnız "grup yeterli mi" derdi | Grup denetlenir **ve gerekli adet ayrıca yazılır** — 3 koyduysan "gerekli 2" görürsün. Bu bilgi eskiden hiç verilmiyordu |
| **Görünürlük** | — | Sonucun başında: *"Asansörlerin hepsi aynı tip — MMO/697 s.11-12 yolu. Üretilecek pafta: **PAFTA**"* Hangi yolun ve hangi Excel sayfasının kullanıldığı sessiz kalmıyor |

**Neden güvenli:** iki yolun özdeş asansörlerde aynı sonucu verdiği ölçüldü —
`ΣRi = n·R` ve `1/TReş = Σ(1/TRi) = n/TR` → `TReş = TR/n`, **fark 0,00e+00**.
Yani seçim hesabın doğruluğunu değil, yalnız **belgenin biçimini** belirliyor:
PAFTA türetmeyi adım adım yazar, PAFTA-COKLU asansör bazında tablo verir.
Motorun iki yolu da, Excel'in iki pafta sayfası da yerinde duruyor.

**Yol boyunca düzelen iki şey:** Excel'den geri yükleme artık tek forma doğru
oturuyor ( TEK sayfasının bina alanları ortak alanlara, asansör alanları 1.
kolona ); ve adet 2 → 1 → 2 gidip gelirken gizlenen kolonun değeri **silinmiyor**
( 10 + 16 kişilik grup korunuyor ) — hesaba yalnız görünen kolonlar girer.

**Sürüm 1.9** — dış denetimden gelen **dört bulgu** ölçülerek doğrulandı ve giderildi.

| Bulgu | Ölçülen davranış | Ne yapıldı |
|---|---|---|
| **S2 ( makine besleme ) akım bakımından hiç denetlenmiyordu** | 37 kW motor + **S2 = 1,5 mm²** : motor akımı **62,5 A**, kablonun taşıma kapasitesi **17,5 A** — program yine **"uygundur"** diyordu. Gerilim düşümü yakalamıyor: kısa hatta ε2 = %0,31. Bu kontrol **ofis Excel'inde de yok**. | Motor akımı I2 ve kablo kapasitesi Iz2 hesaplanıyor; yetersizse **⚠ uyarı** çıkıyor. Paftadaki `I ≤ Iz` satırı **kolon hattına ( S1 ) ait ve öyle kalmalı** — o hat asansörün toplam kurulu gücünü taşır. Sonuç satırı değiştirilmedi ki **XLSX ile pafta ayrışmasın**. |
| **Motor sigortası her güçte "4 x 25"** | Şablonda `G102` hücresinde **sabit metin**. 37 kW motorda akım ≈ 62 A, 110 kW'ta ≈ 186 A — üçünde de "4 x 25" yazıyordu. | **Motor akımından seçiliyor**: `In = P2 / ( √3 · U · cosφ )`, sigorta = kalkış katsayısı × In üstündeki ilk standart kademe ( IEC 60269 gG ). Katsayı **Sabitler → ③** altında, varsayılan **1,25** — bu katsayı ofisin 11 kW örneğinde yine **"4 x 25"** verir. Değer hem paftaya hem **XLSX'e** yazılıyor; şablon hücresi metin olduğu için Excel'e formül eklenmedi. |
| **Ekran reddediyor, indirme üretiyor** | `1.200` gibi belirsiz yazım ekranda reddediliyordu ama **trafik-XLSX, avan-XLSX ve avan-PDF** aynı girdiyle dosya üretiyordu; sayı boşa çevrildiği için hücre **boş** kalıyor, eksik girdili pafta teslim edilebilir hâlde çıkıyordu. | Beş indirme ucunun **hepsi** artık ekranla aynı kapıdan geçiyor. |
| **Kabin kuyuya sığıyor mu diye bakılmıyordu** | Kuyu 1500 mm + kabin 2100 mm sessizce hesaplanıyordu. | `kabin genişliği ≥ kuyu genişliği` ise **⚠ uyarı**. Asgari boşluk **dayatılmıyor** — kapı tipine, ray ve karşı ağırlık konumuna göre değişir. |

**Sürüm 1.8** — **şerit boyu artık girdi değil, temel ölçülerinden türetiliyor.**

Ofiste temel topraklama hesabı için **yalnız uzunluk ve genişlik** giriliyor;
elektrik projesinin topraklama planına avan aşamasında bakılamıyor. Program
artık aynı şekilde çalışıyor.

| Konu | Ne değişti |
|---|---|
| **L — şerit boyu boş bırakılır** | Alan boş kalırsa band boyu temel ölçülerinden hesaplanır: band temelin çevresini **kapalı ring** olarak dolaşır, 20 m'yi aşan kenarlarda gözler **20 × 20 m**'yi geçmeyecek şekilde **enine bağ** atılır — <b>L = 2·( a + b ) + enine bağlar</b>. Kullanılan sayı ve açılımı alanın altında görünür ( ör. `ring 99,90 m + enine bağ 1 × 18,90 = 118,80 m` ). |
| **Girilen boy türetileni ezer** | Topraklama planı çizildiğinde plandaki gerçek boy yazılır; program o değeri kullanır. **Pafta değişmez** — boyun elle mi girildiği yoksa türetildiği mi teslim edilen hesaba yazılmaz, L her zaman sıradan bir girdi satırıdır. Kaynak bilgisi yalnız ekranda, alanın altında görünür. |
| **Karelaj gözü ofis sabiti oldu** | **Sabitler → ④ Temel Topraklama** grubuna `Karelaj gözü (m)` eklendi ( varsayılan **20** ). Ofis başka bir aralık kullanıyorsa bir kez değiştirilir. |
| **"Tahmin et" düğmesi kalktı** | Düğmeye basmayı unutma ihtimali ortadan kalktı; türetme kendiliğinden ve **motorun içinde** yapılıyor — arayüzde ikinci bir formül kopyası yok. |
| **XLSX yine kendi başına doğru** | Türetilen boy indirilen dosyanın **GİRİŞ!C13** hücresine yazılır; Excel'i tek başınıza açsanız da aynı Ry / Rç / Re çıkar. Şablonda değişiklik yok. |

Ofisin kendi paftasıyla ( 31,05 × 18,90 m · β = 150 Ω·m · L = 140 m · Is = 4 )
karşılaştırıldı: **Ry = 3,82 Ω · Rç = 25,00 Ω · Re = 3,310 Ω · Re max = 166,67 Ω**
— birebir aynı. Aynı temel için türetilen boy **118,80 m** ve Re **3,45 Ω**;
sınır 166,67 Ω olduğundan **sonucu değiştirmiyor** — boydaki tahmin payı bu
kontrolü etkilemeyecek kadar küçük kalıyor.

**Sürüm 1.7** — bu sürümde giderilen **geçersiz girdi** açıkları:

Dış bir denetimde, hesabın "normal" girdilerde Excel ile birebir tuttuğu ama
**geçersiz girdi yollarında** programın yanlışlıkla "uygun" sonucu verebildiği
altı nokta bulundu. Altısı da doğrulandı ve giderildi; her biri için pakete
kalıcı test eklendi.

| Bulgu | Ne oluyordu | Ne yapıldı |
|---|---|---|
| **Manuel ta / tk / tg / tp sıfır veya negatif girilebiliyordu** | Dördü de `0` iken 44 daireli örnekte program 2 yerine **1 asansör yeterli** dedi ( TR = 24,5 sn ). Hesabın içinde fiziksel olarak imkânsız **ts = −1,88 sn** oluşuyordu. | Süreler için fiziksel aralık denetimi ( ta/tk 0,1-30 sn · tg 0,1-60 sn · tp 0,1-20 sn ). Tek ve çoklu hesapta, çokluda ayrıca asansör bazında. |
| **Çoklu hesap bina girdilerini doğrulamıyordu** | `h = −3 m` ile hata vermeden **"Yükseltilmiş kriteri karşılanıyor"** çıkıyordu; bina/yapı yüksekliği boşken sessizce "Standart" sınıfına düşüyordu. Tek asansör hesabı aynı girdileri reddediyordu. | Bina girdileri denetimi **tek yapılıp iki yolda da** kullanılıyor: N, h, bina ve yapı yüksekliği. |
| **Belirsiz sayı yazımı** | Türkçede `1.200` = bin iki yüz, `1,200` = bir virgül iki. Program ikisini de **1,2** okuyordu: 1.200 daireli bir binada gerekli asansör adedi **41 yerine 2** çıkıyordu. | Bu yazım artık **reddediliyor** ve ne yazılması gerektiği söyleniyor. `0,075` gibi sıfırla başlayan ondalıklar etkilenmez — binlik ayracı sıfırdan sonra gelmez. |
| **Avanda elle girilen yük / ağırlık / verim sınırsızdı** | `Q elle = 0` ile motor gücü **0 kW**, otomatik motor **2,2 kW** ve sonuç "uygun" oluyordu. `Gk elle` negatif olabiliyor, `η = 10` girilince motor gereksiz küçülüyordu. | Q elle ve Gk elle 50-20.000 kg, η 0,05-1,00 aralığında olmalı; dışı hesabı durdurur. |
| **Tablo-11 dışı yükte boş kabin kütlesi sessizce sabitleniyordu** | `Q = 5.000 kg` için de `Gk = 1.900 kg` kullanılıyordu ( tablonun üst ucu ). Kuvvet hesapları olduğundan küçük çıkıyordu. | Tablo-11 kapsamı ( 450-2.500 kg ) dışında **`Gk elle` zorunlu**; verilmezse hesap durur ve sebebi yazılır. |
| **Denge faktörü q = 1 kabul ediliyordu** | `q = 1` iken N = (1−q)·… = **0 kW** çıkıyor, 2,2 kW motor "uygun" görünüyordu. | Sert sınır **0,20 - 0,80**; dışı reddedilip varsayılana dönülür ve **uyarı** çıkar. Uygulama bandı 0,40 - 0,55; dışı hesabı durdurmaz ama paftaya gerekçe yazılmasını ister. |

Ayrıca: aralık dışı bırakıldığı için **varsayılana dönülen her alan** ( gr, Fmk,
Fsh, S1, S2, L2, Nsç, L1, i, q ) artık **uyarı üretir** — kullanıcı bir sayı
yazıp programın başka bir sayı kullandığını fark etmeden kalamaz.

**Sürüm 1.6** — önceki sürümde eklenenler:

| Konu | Ne değişti |
|---|---|
| **C ) Ofis Varsayılanları** | Asansörden asansöre, projeden projeye **değişmeyen** 15 değer tek bir kartta toplandı ( Sabitler sekmesi ): U · κ · εmax · ray birim kütlesi · makine ve sehpa ağırlığı · kolon ve besleme kesiti · besleme uzunluğu · kablo tipi · L1 payı · toprak özgül direnci · çubuk adedi · kat yüksekliği · kapı tipi. **Bir kez ayarlanır**, her yeni asansör ve her yeni proje bunları kullanır. |
| **Asansör kartı sadeleşti** | Ray, makine, sehpa, kesitler, kablo ve L1 kartta doğrudan durmuyor; **"Ofis standardından farklı değerler"** katlanır bölümüne indi. Boş bırakıldıklarında ofis standardı kullanılır; yalnız o asansörde farklı bir değer gerekiyorsa doldurulur ve başlıkta **"n özel"** rozeti çıkar. Paftada değerin kaynağı ( GİRİŞ — asansör bazında / OFİS VARSAYILANI ) yazılır. |
| **U, κ, εmax avan panelinden kalktı** | Projeden projeye değişmedikleri için ofis varsayılanına taşındı. **β ve çubuk adedi** yerinde bırakıldı ( zemin ölçümü arsadan arsaya değişir ) ama artık boş bırakılabiliyor — yer tutucu ofis değerini gösteriyor. |
| **Nsç motor gücü otomatik** | Boş bırakılırsa hesaplanan güçten büyük **ilk standart anma gücü** seçilir ( IEC 60072 / TS EN 60034: 2,2 · 3 · 4 · 5,5 · 7,5 · 11 · 15 · 18,5 · 22 · 30 · 37 · 45 kW ). ⚠ Excel'inizdeki örnekte 16 kişilik asansör **N = 13,33 kW** hesaplanıyor ama **Nsç = 11 kW** yazılıydı — pafta "UYGUN DEĞİL" veriyordu. Program artık **15 kW** seçiyor. |
| **L1 kolon hattı uzunluğu** | Boş bırakılırsa **L1 = kuyu yüksekliği + ofis payı** ( varsayılan 3,5 m ). Plandan ölçülen değer farklıysa elle yazılır. |
| **Çubuk adedi uyuşmazlığı** | Program **0**, Excel'iniz **4** diyordu. Ofis varsayılanı **4** oldu. |
| **Q ve Gk artık girdi değil** | Kapasiteyi seçince anma yükü **Tablo-7**'den, boş kabin kütlesi de **Tablo-11**'den kendiliğinden geliyor ve kartta **gri, salt okunur** olarak görünüyor — sarı ( elle doldurulan ) alan değiller. Tablo dışı bir yük gerekirse **Q elle** / **Gk elle** katlanır bölümde duruyor; girildiğinde üstteki satır girilen değeri gösterir, yani hep hesapta kullanılan değer görünür. |
| **Sabitler hesap bazında gruplandı** | "B) Ofis Standardı" ve "C) Ofis Varsayılanları" **tek panelde** birleşti ve alanlar **hangi hesaba girdiklerine göre** ayrıldı: ① Motor gücü ve kuvvetler · ② Aydınlatma · ③ Kurulu güç ve gerilim düşümü · ④ Temel topraklama. Her grubun başlığında hangi hesap ve hangi kaynak olduğu yazılı. Bir sabit gruba yazılmayı unutulursa **DİĞER** başlığı altında görünür — sessizce kaybolmaz. |
| **Kat yüksekliği ve kapı tipi ait olduğu yere döndü** | v1.6'da ofis varsayılanı yapılmışlardı; **her projede değiştiği için** geri alındı. İkisi de yalnız **Trafik Hesabı** sekmesinde. Sabitler panelindeki "askı oranı buradan kaldırıldı" bilgi bandı da kalktı — bu bilgi artık kart başlığındaki ( ! ) balonunda. |
| **β ve çubuk adedi ofis standardına taşındı** | Avan panelindeki **β — toprak özgül direnci** ve **Is — çubuk topraklayıcı adedi** kaldırıldı; ④ Temel Topraklama grubundalar. Zemin etüdü varsa oradan değiştirilir ve değer o projenin dosyasıyla saklanır. **L — şerit boyu** avan panelinde kaldı ( v1.8'de temel ölçülerinden türetilir oldu ). |
| **İki farklı L ayrıştırıldı** | Topraklamadaki **L ( şerit boyu )** ile asansördeki **L1 ( kolon hattı )** karışıyordu. L'nin etiketine "topraklama" eklendi ve ( ! ) balonunda farkı yazıldı; balonda temel çevresi de karşılaştırma olarak veriliyor. **L1'in yer tutucusu artık hesaplanan sayıyı gösteriyor** — `42,00 ( Hk + 3,50 )` — kuyu yüksekliğini değiştirince o da değişiyor. |
| **Manuel k ve manuel V ana akıştan kalktı** | Çoklu asansör gövdesinde ortada duruyorlardı; artık katlanır **"Manuel değerler"** bölümünde. Elle bir değer girilirse başlıkta **"n elle"** rozeti çıkar — gizlenen bir ezme sessiz kalmaz. Tek asansör gövdesinde zaten "İleri seçenekler" altındaydılar, oraya da rozet eklendi. |
| **Çokluda manuel k sessizce yok sayılıyordu** | Tablo-9'da değeri olan bir bina tipinde çoklu hesap, girilen manuel k'yı **görmezden geliyor ve hiçbir şey söylemiyordu**. Artık tek asansör hesabındaki gibi açıkça reddediliyor. Kamu binası ve Tablo-9'da olmayan bina tipleri ( karma, poliklinik, katlı otopark ) için manuel k yine geçerli. |
| **Şablon denetimi** | Yanlış ya da eski bir Excel `templates/` klasörüne konursa program yine dosya üretiyordu — hesap doğru olduğu için ekranda belirti çıkmıyor, hata yalnız teslim edilen paftada görünüyordu. Artık üç katmanlı denetim var ( sayfalar · girdi hücreleri · şablonun içindeki tablo değerleri ) ve **denetimden geçmeyen şablonla XLSX ÜRETİLMEZ**. Sabitler sekmesinde **Şablon durumu** kartı, komut satırında `python3 araclar/sablon_denetle.py`. |
| **XLSX kendi başına doğru** | İndirilen dosyanın **GİRİŞ hücrelerine, motorun gerçekten kullandığı değer yazılır** — boş bırakılan ofis alanları, otomatik seçilen Nsç / L1 ve aralık dışı olduğu için reddedilenler dâhil. Excel'i tek başına açsanız da ekrandakiyle aynı sonucu verir. Şablonda hiçbir değişiklik yapılmadı. |

**Sürüm 1.5** — daha önce eklenenler:

| Konu | Ne değişti |
|---|---|
| **Asansör adedi tek yerde** | Avan sekmesindeki asansör adedi artık **trafik hesabından gelir** ve kendiliğinden eşitlenir — tek tek "kullan" kutusu işaretlemek yok. **1 asansör** seçiliyken trafik hesabının *bulduğu* adet ( "yetmiyor, 3 gerekir" derse avanda 3 kart açılır ), **2–4** seçiliyken grupta tanımlanan adet. Trafik adedinin **altına inilemez**: gruptaki her asansörün elektrik hesabı da yapılmalıdır. |
| **Trafik grubu dışı asansör** | Binada trafik hesabına girmeyen ayrı bir yük ya da sedye asansörü varsa avandaki adet **elle artırılır**. Fazlalar **trafik grubu dışı** diye etiketlenir: kurulu güce ve gerilim düşümüne girer, trafik kontrolüne girmez — pafta bunu **not** olarak yazar ( uyarı olarak değil ). |
| **Kapasite ve hız trafiği izler** | Avandaki kapasite ve hız, trafik hesabındaki değer **değiştiğinde kendiliğinden güncellenir** — düğmeye basmayı unutma diye bir şey kalmadı. Elle başka bir değer girerseniz o değer **korunur** ( trafik yeniden değişene kadar ) ve program farkı uyarı olarak yazar; **↧ Trafikten güncelle** istediğiniz an trafiğe döndürür. |
| **Askı oranı Sabitler'den kalktı** | "B) Ofis Standardı" panelinde hâlâ **i — Palanga ( askı ) katsayısı** duruyordu; oysa v1.4'te asansörün kendi girdisi olmuştu. Panelden kaldırıldı, yerine nereye taşındığını söyleyen bir not kondu. Excel'deki `SABİTLER!C22` yalnız boş bırakılan kolon için **yedek** olarak duruyor. |
| **Kabin hızında sessiz varsayım kalktı** | Avan hız listesi artık boş başlar; değer trafikten gelir ya da elle seçilir. Önceden hiç dokunulmayan alan sessizce **1,60 m/s** kabul ediliyordu. |
| **Grup tanımı korunuyor** | Adet 2 → 1 → 2 gidip gelindiğinde gruptaki farklı kapasiteler ( ör. 10 + 16 kişilik ) artık silinmiyor; yalnız 1. kolon tek hesaptaki tanımı alır. |

**Sürüm 1.4** — daha önce eklenenler:

| Konu | Ne değişti |
|---|---|
| **Tek trafik sekmesi** | "Trafik Hesabı" ve "Çoklu Asansör Trafik" birleşti. Üstteki **asansör adedi** seçicisinden 1–4 arası seçiyorsunuz: **1** → program tek asansörün yetip yetmediğini söyler ve **yetmiyorsa kaç adet gerektiğini hesaplar**; **2–4** → her asansör ayrı tanımlanır, grup kontrolü ( Reş ≥ B·k, TReş ≤ Izul ) yapılır. Adet değişince ortak bina girdileri korunur. Tek hesap "n adet gerekir" dediğinde tek tıkla o gruba geçilir. |
| **Makine tipi ve askı oranı** | Asansörün normal girdisi oldu. **Makine tipi** ( dişlisiz / dişli ) seçilince η, MMO/697 s.21 değeriyle ( 0,85 / 0,50 ) kendiliğinden dolar. **Askı oranı** ( 1:1 / 2:1 ) Sabitler'den kalktı; artık kapasite ve hız gibi asansöre ait. |
| **Toplam sistem verimi** | İmalatçı kataloğundan gelen ( dişli 1:1 ≈ 0,60 · dişlisiz 2:1 ≈ 0,82 gibi ) **toplam** verim değerleri kullanılabiliyor: asansörün altındaki kutu işaretlenince MMO/697 §2.4'teki palanga düşüşü ikinci kez uygulanmaz ve paftada hangi esasın kullanıldığı yazılır. |
| **Makine dairesi yok ( MRL )** | Ölçülere 0 yazmak yerine açık işaret kutusu. İşaretliyken ölçü alanları kapanır ve pafta "makine dairesiz sistem" der; işaretli değilken ölçü boşsa program uyarır. |

**Sürüm 1.3** — daha önce eklenenler:

| Konu | Ne değişti |
|---|---|
| **Bodrum durağı** | Ana giriş altındaki duraklar artık girilebiliyor. Tablo-2 asgari hızı `N + 1 + Nb` durak adedinden seçilir; H, S ve TR (MMO tanımı gereği) değişmez. Tek ve çoklu sayfada, çokluda asansör bazında. |
| **Kapı genişliği boşlukları** | 1000 ve 1200 mm (Tablo-4) ile 700 mm (Tablo-8) artık hesaplanıyor — komşu satırlardan enterpolasyon / dış değerleme, kaynağı paftada belirtiliyor. Listedeki yedi genişliğin tamamı çalışıyor. |
| **Askı ve denge asansör bazında** | Palanga katsayısı (i) ve denge faktörü (q) artık η gibi asansöre özel; dişlili + dişlisiz karışık projeler doğru hesaplanıyor. |
| **Çokluda imalatçı süreleri** | ta / tk / tg / tp asansör bazında elle girilebiliyor (tek sayfadaki imkânın karşılığı). |
| **Erişilebilirlik uyarısı** | 630 kg altı kabin ve 800 mm altı kapı TS EN 81-70 / TS 9111 ölçütüyle uyarılıyor; öneri sıralamasındaki kural da buna bağlandı. |
| **Kamu binası** | Hem %k hem hız varsayımı paftaya yazılıyor. |
| **15 kişi / 1125 kg** | Tablo-7'ye açık istisna olarak yazıldı, kaynağı paftada ayrı gösteriliyor. |
| **Trafik ↔ avan bağı** | Kapasite, hız ve kuyu yüksekliği trafik hesabıyla karşılaştırılıyor; tutarsızlık uyarı olarak çıkıyor. |
| **Arayüz** | Sekme başlığında uyarı sayısı rozeti; avan uyarıları artık ekranda da görünüyor (önceden yalnız PDF'te vardı). |
| **( ! ) açıklama simgeleri** | Yöntemi anlatan uzun metinler — Tablo kuralları, bodrumun H ve S'ye neden girmediği, ara değerlerin nasıl türetildiği — ekranda başlık ve alan adlarının yanındaki **( ! )** dairesine toplandı; üzerine gelince (dokunmatikte tıklayınca) açılıyor. **⚠ uyarılar buraya girmez**, karar gerektirdikleri için açıkta durur. Paftaya ve PDF'e bu metinler yine tam basılır. |
| **Excel biçimi** | Yeni ve güncellenen uzun açıklama notları Excel'de kırpılıyordu — satır kaydırma açıldı, satır yükseklikleri verildi; ÇOKLU sayfasındaki gizli yardımcı alan gizlendi. |
| **Pafta biçimi** | İki satıra düşen bölüm başlığı mavi bandın dışına taşıyordu; band artık başlıkla birlikte büyüyor. Uyarı kutusunda çift ⚠ görünmesi giderildi. |

---

## 1. Kurulum ve çalıştırma

### macOS
`baslat.command` dosyasına **çift tıklayın.**

İlk açılışta kendi kurulumunu yapar (yaklaşık 1 dakika, internet gerekir);
sonraki açılışlarda doğrudan başlar. Tarayıcı kendiliğinden açılır.

> macOS "geliştirici doğrulanamadı" uyarısı verirse: dosyaya **sağ tık → Aç**
> deyip bir kez onaylayın. Bundan sonra çift tıklama yeterlidir.

### Windows
`baslat.bat` dosyasına **çift tıklayın.** (Python kurulu değilse uyarır.)

### Kapatmak
Açılan siyah pencerede **Ctrl + C**, ya da pencereyi kapatın.

**Program tümüyle sizin bilgisayarınızda çalışır.** İlk kurulumdan sonra
internet gerekmez; hiçbir veri dışarı gitmez.

---

## 2. Program nasıl çalışır

| Sekme | Ne yapar |
|---|---|
| **Proje Bilgileri** | Pafta antedi, proje kaydet/aç |
| **1 · Trafik Hesabı** | **Adet 1** — tek tip asansör: kaç adet, kaç kişilik, hangi hız |
| **1 · Trafik Hesabı** | **Adet 2–4** — farklı kapasitede asansör grubunun kontrolü |
| **2 · Avan Hesapları** | 1–4 asansör: motor, kuvvetler, aydınlatma, kurulu güç, gerilim düşümü + makine dairesi + topraklama |
| **Sabitler / Ofis Standardı** | Palanga, denge faktörü, armatür, priz, cosφ… |
| **Tablolar** | Kullanılan tüm tablolar ve kaynakları |

**Uygulama projesi** modunda tek adım vardır:

| Sekme | Ne yapar |
|---|---|
| **1 · Uygulama Hesapları** | 82 girdi → 14–18 hesap bölümü. **Mukavemet ( 1–10 ):** motor gücü · makine konstrüksiyonu · kabin alanı · askı halatları · regülatör halatı · tahrik yeteneği · kabin kılavuz rayları · karşı ağırlık rayları · kuyu tabanı yükleri · sığınma alanları. **Elektrik ( 11– ):** kabin ve kuyu aydınlatması · kurulu güç cetveli · gerilim düşümü ve kesit kontrolü · makine dairesi aydınlatması · temel topraklama |
| **Sabitler / Ofis Standardı** | Armatürler, priz, cosφ, U, κ, εmax, β, çubuk sayısı — elektrik ve topraklama hesapları buradan beslenir |

Sonuçlar **yazdıkça** hesaplanır; kaydet düğmesi yoktur.
**Sarı zeminli** alanlar sizin doldurduğunuz girdilerdir; boş bırakılan
opsiyonel alanlar tablo değerini kullanır.

### Tipik akış

1. **Proje Bilgileri** — proje adı, işveren, pafta no.
2. **1 · Trafik Hesabı** — üstteki **asansör adedi** seçicisiyle başlayın.
   **1** seçiliyken bina tipi, yükseklikler, kat sayısı, daire sayısı, kabin
   kapasitesi ve kapı bilgilerini girin; program kaç asansör gerektiğini bulur.
   *Otomatik öneri tablosu* hangi kabin–hız birleşiminin kaç asansör
   gerektirdiğini yan yana gösterir.
   → Farklı kapasitede bir grup kuracaksanız adedi **2–4** yapın; her asansör
   ayrı tanımlanır ve grup kontrolü yapılır.
3. **2 · Avan Hesapları** — asansör adedi, kapasite ve hız buraya
   **kendiliğinden** gelir ve trafikte bir şey değişirse **kendiliğinden
   güncellenir**. Kuyu/kabin ölçüleri, ağırlıklar ve kablo bilgilerini girin.
   Trafik hesabına girmeyen ayrı bir yük ya da sedye asansörü varsa adedi
   elle artırın.
4. **PDF indir** ya da **Projeyi paketle** ( CAD + PDF + proje dosyası ).

### Uygulama projesi akışı

1. Açılış ekranından **UYGULAMA PROJESİ**'ni seçin.
2. **Proje kimliği** — proje adı, işveren, pafta no. ( Dosya adında
   kullanılır; uygulama projesi kapağı MMO'nun **ayrı**
   kitabına aittir, avan kapağı buraya basılmaz. )
3. **Uygulama projesi girdileri** — gruplar hâlinde. En üstte makine yerleşimi,
   sonra mukavemet grupları, en altta yalnız elektrik hesaplarına ait olanlar
   ( kuyu genişliği, kablo kesit ve uzunlukları, temel ölçüleri, makine
   dairesi ).
   **Her grubun altında kapalı bir *Gelişmiş* bölümü vardır:** ofisin ya da
   ürünün hep aynı girilen değerleri ( pervaz, kapı mekanizma payı, regülatör
   kasnağı, tampon ölçüleri, ray sayıları, kesitler … ). Hesaba aynen girerler;
   yalnız ilk bakışta görünmezler. Varsayılandan farklı bir değer varsa
   başlıkta *"n değiştirildi"* yazar ve alan işaretlenir; hesabı durduran hata
   gizli bir alandaysa bölüm kendiliğinden açılır. Arama kutusu bu alanları da
   bulur.
   **Katlar tek tek girilmez:** *seyir mesafesi* ( en alt durak → en üst durak,
   m ) ile *son kat yüksekliği* ( en üst durak → kuyu tavanı, mm ) yeter.
   Kuyu boyu, kılavuz ray boyu ve regülatör halatı boyu bu ikisinden hesaplanır.
   **Kabin ağırlığı da beyan yükünü izler:** yükü değiştirdiğinizde ofis
   tablosundan dolar ( 1275 kg → 1100 kg ). Elle yazdığınız değer, beyan yükünü
   yeniden değiştirene kadar korunur — avan tarafındaki *trafik → kapasite*
   izlemesinin aynısıdır. Tablo **tahmindir**, standardın sayısı değildir;
   kesin tasarımda imalatçı verisiyle değiştirin ( bkz. §7 ).
   **Regülatörün iki imalatçı değeri boş bırakılabilir** ( Hız regülatörü ·
   Gelişmiş ): devreye sokma kuvveti boşsa pafta fren bloğuna
   *"en çok Fçekme / 2"* şartını, devreye girme hızı boşsa izin verilen
   aralığı yazar ( bkz. §7 ).
4. Sağ panelde bütün bölümler, hangisinin takıldığı, **kuyu tabanına gelen
   yükler** ( inşaat projesine bildirilecek FKR · FAR · Fkt · Fat ), asansörün
   kurulu gücü, gerilim düşümü ve topraklama direnci görünür.
5. **PDF** ( bütün hesaplar tek paftada ) ya da **Projeyi paketle** ( CAD + PDF +
   `.uygulama` proje dosyası ) indirin.

> Topraklama hesabı için temel ölçüleri, gerilim düşümü için kolon hattı
> uzunluğu girilmelidir; boş bırakılırsa o bölümler paftaya girmez ve program
> bunu söyler. Makine dairesiz ( MRL ) sistemde kutuyu işaretli bırakın.

---

## 3. Çıktılar

**Hesabın tek kaynağı programdır.** MMO/697, TS EN 81-20, TS EN 81-50,
ISO 8100-32 ve IEC tablolarının tamamı ile her formül `engine/` klasöründe
Python olarak yazılıdır;  ekran, PDF ve CAD aynı hesap sonucundan üretilir ve
bu yüzden ayrışamaz.  Program Excel üretmez, okumaz ve Excel'e ihtiyaç duymaz.

| Çıktı | Ne verir |
|---|---|
| **PDF** | Baskıya hazır pafta:  başlık → girdi satırları → denklem → sayıların yerine konmuş hâli → sonuç → kontrol → notlar.  Antet, kaynak referansları, sayfa numarası ve imza kutusu içerir. |
| **CAD ( ZIP )** | Paftaların ofisin tip proje formatına yerleştirilmiş DXF / DWG çizimi, kaynak PDF'ler ve proje dosyası |

---

## 4. Revizyon — proje dosyasından aç

Aylar sonra projede bir şey değiştiğinde ( kat eklendi, kuyu genişledi,
kapasite değişti ) hiçbir şeyi baştan girmezsiniz:

1. **Proje aç** ( avan projesinde Proje Kapağı → Proje araçları, uygulama
   projesinde Proje sekmesi ) ile `.avan` ya da `.uygulama` dosyasını seçin.
2. Bütün girdiler — ofis sabitleri ve çoklu asansörler dâhil —
   yerine oturur, hesaplar anında yeniden yapılır.
3. Değişen değeri düzeltin.
4. Güncel PDF'i ya da paketi yeniden indirin, **projeyi yeniden kaydedin**.

Dosyada bulunmayan bir alan varsa ( eski bir sürümün dosyası ) program kaç
alanın varsayılana döndüğünü **söyler** — sessiz kalmaz.

Dosyadaki bir **seçim değerini bu sürüm tanımıyorsa** ( program güncellenmiş,
bir seçenek kalkmış ya da adı değişmiştir ) alan listenin varsayılanına döner
ve program bunu **pencereyle** söyler:  hangi alan, hangi asansör, eski değer
ve yerine geçen değer.  Hesap artık o değerle yapıldığı için doğru değeri
seçip projeyi yeniden kaydedin.  Aynı kural tarayıcıda saklı proje için de
geçerlidir.

Doğrulama paketinin TEST 6'sı formdaki bütün alanların dosyaya yazılıp aynen
geri geldiğini, geri yüklenen projenin aynı hesap sonucunu verdiğini,
dosyanın gerçek **Proje aç** düğmesiyle ve **başka bir proje açıkken**
açılabildiğini, tanınmayan değerin söylendiğini denetler.

---

## 5. Proje dosyası ve paketleme

### Proje dosyası — girdilerin geri dönüş noktası

**Projeyi kaydet** tüm girdileri tek dosyaya yazar. Ne PDF ne CAD —
yalnız programın okuyup yazdığı veri. Aylar sonra revizyon gerektiğinde dosyayı
yükler, değişeni düzeltir, çıktıları yeniden alırsınız.

**İki ayrı uzantı**, çünkü avan ve uygulama ayrı projelerdir:

| Proje | Uzantı | Nerede |
|---|---|---|
| Avan | **`.avan`** | Proje Kapağı → Proje araçları |
| Uygulama | **`.uygulama`** | Uygulama Hesapları → Proje dosyası |

Dosya adı **proje adından** üretilir (`Jan Mühendislik.uygulama`). Her dosya
**yalnız kendi projesinin** alanlarını taşır; avan dosyasını uygulamaya
yüklemeye çalışırsanız program *"Bu dosya AVAN projesine ait"* deyip reddeder.

Dosyanın içinde ayrıca **`surum`** alanı vardır. Girdi sözleşmesi zamanla
değişir; sürüm yazılı olmasaydı eski bir dosyadaki eksik alan **sessizce**
varsayılana düşerdi. Yazılı olduğu için program kaç alanın döndüğünü sayıp
söyler. **Ofis sabitleri de dosyaya girer** — proje o günkü kabullerle
hesaplandı, üç yıl sonra açıldığında aynı sonucu vermelidir.

### Projeyi paketle — tek ZIP

**Projeyi paketle (ZIP)** düğmesi teslim edilecek her şeyi ve geri dönüş
noktasını **aynı arşive** koyar:

```
Jan Mühendislik - Uygulama Projesi.dxf     ← CAD çizimi ( + DWG üretilebildiyse )
pafta pdf/1 - Kapak.pdf
pafta pdf/2 - Uygulama Projesi.pdf
Jan Mühendislik.uygulama                   ← GERİ DÖNÜŞ NOKTASI
OKUBENI.txt
```

Çıktılar projeyi **anlatır**, proje dosyası onu **geri getirir**. İkisi ayrı
yerlerde durursa arşivden dönmek imkânsızlaşır — bu yüzden birlikte inerler.

> **Bilinen sınırlama — uygulama paketinin kapağı.**  Uygulama paketindeki
> `Kapak.pdf`, tarayıcıda o an açık olan **avan projesinin** kapak
> alanlarından alınır;  `.uygulama` dosyasında saklanmaz.  Aynı `.uygulama`
> dosyası, avan tarafında başka bir proje açıkken başka bir projenin kapağıyla,
> tarayıcı belleği boşken kapaksız paketlenir.  Uygulama paketini
> hazırlamadan önce avan tarafında **aynı projenin** `.avan` dosyasını açın.

### Kalıcılık

Girdiler tarayıcıda da kendiliğinden saklanır; programı kapatıp açtığınızda
kaldığınız yerden devam edersiniz. **Avan ve uygulama ayrı kovalarda durur**:
biri diğerini görmez, **"Tümünü temizle" yalnız içinde bulunduğunuz projeyi
siler**, ve aynı anda bir avan ile bir uygulama projesi tutabilirsiniz.

**Örnek proje yükle** düğmesi ofisin örnek avan projesini yükler.

---

## 6. Hesabın doğruluğu

Program bir **doğrulama paketiyle** birlikte gelir ve son çalıştırmada
( 2026-09-16 ) **40.965 kontrolün tamamı geçmiştir.**

| Test | Kapsam | Sonuç |
|---|---|---|
| **1 · Avan referans taraması** | 123 senaryo ( 87 tek · 12 grup · 24 avan ) × bütün sonuç değerleri, dondurulmuş referansa karşı | **5.599 / 5.599** |
| **2 · Kenar durumlar** | tablo sınırları, yuvarlama, ofis varsayılanları, motor kademesi, manuel k, **geçersiz girdi yolları**, **kolon hattı akımının ηm ile, kurulu gücün etiket gücüyle hesaplandığı**, **boş kabin kütlesi tablosu**, **Iz tablosunun B.52.4 Yöntem C değerleri**, **makine dairesi aydınlatmasında döşeme düzlemi** | **849 / 849** |
| **3 · Girdi dayanıklılığı** | ~1.900 bozuk girdi birleşimi + tüm API uçları ( kaldırılan Excel uçlarının gerçekten yok olduğu dâhil ) + **ofis standardında belirsiz / okunamayan sayının sessizce varsayılana dönmediği** + **gizli alanın projeyi durdurmadığı** | **138 / 138** |
| **4 · Çıktı bütünlüğü** | PDF açılabilirliği ve içeriği, uygulama paftası, paketlerin içeriği ve **CAD çizimini AutoCAD'in açtığı** ( şapka · `%%` · sınırlar · açılış görünümü ) | **282 / 282** |
| **5 · Arayüz** | tarayıcıda iki modun tüm sekmeleri, canlı hesap, indirme, **ayrı veri kovaları**, **proje dosyası**, revizyon, yerleşim taşması, **kabin ağırlığının beyan yükünü izlemesi**, **Gelişmiş bölümleri** ( kapalı açılış · sayaç ve işaret · gizli alandaki hatada açılma · arama ) | **487 / 487** |
| **6 · Proje dosyası geri yükleme** | avan ve iki asansörlü uygulama projesinde formun **her alanı** değiştirilir → "Projeyi kaydet" → program sıfırlanır → dosya yüklenir → her alan, **hesap sonucu** ve **makine daireli projede ekranın yerleşimi** aynı;  gerçek **Proje aç** düğmesi, **başka proje açıkken** açma, kaydet → aç → kaydet aynılığı, tek hesap + ek asansörün kart sayısı, `.uygulama`'nın avana dokunmaması, **tanınmayan değer uyarısı** | **1.735 / 1.735** |
| **7 · Altın çıktı** | 432 senaryonun tüm sonucu satır satır kilitli — refactor kalkanı | **867 / 867** |
| **8 · Mukavemet tabloları** | 9 tablo + ω + kanal tablosu, **ofisin kaynak tablolarının dondurulmuş kopyasına** karşı hücre hücre;  standarda göre genişletilen satırlar ayrıca;  Nequiv(t) **Çizelge 2'den türetilir**;  girdi sözleşmesinin varsayılanları ve seçenekleri;  **hangi girdinin Gelişmiş'te, hangisinin görünür kaldığı** | **1.016 / 1.016** |
| **9 · Mukavemet motoru** | örnek projenin ara değerleri + **standart gereği verilen kararların her birinin uygulandığının kanıtı** + **standardın metnine karşı bağımsız doğrulama** + **denetimlerin her bulgusu yeniden üretilerek** + girdi reddi | **534 / 534** |
| **10 · Mukavemet referans taraması** | 155 senaryo ( girdi uzayı taraması · proje senaryoları · kanal / tahrik birleşimleri · geçersiz girdiler ) × **170 ara değer + bölüm hükümleri**, dondurulmuş referansa karşı | **29.098 / 29.098** |
| **11 · Uygulama projesi** | ortak girdi köprüsü, bölüm birleştirme, makine dairesi ve topraklama yolları, **kendi ofis standardı ve tabloları**, **denetimlerde bulunan hataların her biri**, **boş kabin kütlesinin iki projede aynı tablodan geldiği**, **asansörlerin sırasının sonucu değiştirmediği**, **hesap → PDF → DXF zinciri** | **402 / 402** |
| **12 · Dış referans paftaları** | referans proje ve "new block" paftalarının yayımlanmış sayıları;  referans proje kabin rayı kendi ağırlık merkezi ve Rm 450 ile, bilinen iki fark ( yükün yönü · normal işletmede P ) kendi sayılarından yeniden üretilerek | **53 / 53** |
| **13 · Canlı hesap tutarlılığı** | tarayıcıda avan ve uygulama formunun **her girdisi** değiştirilir + tohumlu rastgele hızlı değişiklik dizileri **yapay ağ gecikmesiyle**;  her seferinde ekrandaki sonuç = formun taze hesabı = indirilen çıktının girdisi, kabin ağırlığı son olayı izler | **797 / 797** |
| **14 · Pafta işlem satırları** | bütün senaryolarda ( ~34.000 hesap satırı ) işlem metni, basıldığı hanelerin yuvarlama payıyla **yeniden hesaplanır** ve basılan sonucu vermesi aranır;  bilinen bağıntıların gerçekten denetlendiği ayrıca doğrulanır | **19 / 19** |

### Referans taraması neden güçlü bir kanıt?

TEST 1 ve TEST 10'un senaryoları, program Excel kullanırken **ofisin kendi
çalışma kitaplarına** yazılıp **LibreOffice ile yeniden hesaplatılıyor**du — yani
sonucu Excel'in kendi formülleri üretiyor, program değil — ve çıkan her değer
motorla karşılaştırılıyordu ( son koşu 2026-09-14:  5.548 ve 4.707 kontrol,
hepsi geçti ).  Excel kaldırılırken bu doğrulanmış sonuçlar **donduruldu**;
testler motoru artık o referansa karşı denetler.  Kapsam:  10 bina tipinin
tamamı ( küçük ve büyük nüfusla ), bütün kabin kapasiteleri ve hızlar, **yedi
kapı genişliğinin tamamı × kapı tipleri**, N = 1…30 kat sınırları, **bodrum
durakları**, Standart / Yükseltilmiş eşiği, elle süre ve adet girişleri, 1–4
asansörlü gruplar;  mukavemette bütün ray profilleri, halat çapları, kanal
şekli × işleme × ofis açıları, güvenlik tertibatları, askı oranları, karşı
ağırlık yeri, durak sayıları, kaçıklıklar, ofis sabitleri ve referans proje.

Kasıtlı bir hesap değişikliği referansı bozar;  farklar tek tek incelenip
onaylandıktan sonra `python3 dogrulama/tarama_uret.py` ile yeniden üretilir.

### Bağımsız denetimde bulunan ve düzeltilen hatalar

Testlerin geçmesi hataları dışlamaz. Aşağıdakiler **testlerin yakalamadığı**,
ayrı denetimlerde bulunup yeniden üretilen hatalardır; her biri artık kendi
regresyon kontrolüyle korunuyor. Altı tur yapıldı: birincisi programın
**davranışını** ( girdi–çıktı, dosya akışı, uyarılar ), ikincisi doğrudan
**hesap motorlarını** standardın metnine karşı, üçüncüsü **sayısal fiziği**,
dördüncüsü **sınır durumlarını**, beşincisi **teslim edilen çizimin
AutoCAD'de açıldığını**, altıncısı da yeniden **hesabın eksik kalan
kontrollerini** denetledi.

#### Birinci denetim — davranış ve dosya akışı

| Bulgu | Etkisi |
|---|---|
| **Negatif gerilme "uygun" sayılıyordu.** Yan yatak boyu mesnet payından küçükse `X ≤ 0` çıkıyor, σe = −5.350 N/mm² oluyor ve `σe ≤ σem` bunu sessizce geçiriyordu | fiziksel olmayan bir kaide **"UYGUNDUR"** raporlanabiliyordu — artık geometri baştan reddediliyor, ayrıca negatif gerilme hiçbir koşulda uygun sayılmıyor |
| **Genel sonuç engelleyici uyarıları saymıyordu.** 37 kW motora 1,5 mm² kablo ( 62,5 A / 17,5 A ) yalnız ⚠ uyarı üretiyor, bölüm ve proje "uygundur" diyordu | akım kontrolü artık **bölüm sonucuna** girer;  uyarılar **engelleyici / bilgilendirici** diye ayrıldı;  yapılamayan zorunlu hesap ( topraklama · makine dairesi ) projeyi uygun bırakmıyor |
| **Excel'den dönünce sonuç değişiyordu.** Ofis sabitleri dosyaya yazılmıyordu: σem = 100 ile "UYGUN DEĞİL" olan proje, aktarılıp geri okununca varsayılan 130'a dönüp "UYGUN" oluyordu | proje sabitleri artık dosyada saklanıp geri okunuyor — **aynı projenin sonucu dosyadan geçince değişmiyor** |
| **Reddedilen ofis sabiti Excel'e ham gidiyordu.** `cosφ = 2` motor tarafından reddedilip 0,9 kullanılırken dosyaya 2 yazılıyordu | ekran ve indirilen kitap **farklı hesap yapıyordu**;  artık motorun kullandığı değer yazılıyor |
| **Metin ofis alanı sayıya çevriliyordu.** Kablo tipine "NYY" yazınca `None`'a düşüp sessizce varsayılan kullanılıyordu | metin alanları korunuyor;  belirsiz sayı yazımı ( `1.200` ) artık **bildiriliyor** |
| **Fiziksel girdi doğrulaması eksikti.** 6,5 halat ile hesap yapılıp "UYGUN" veriliyor;  konsol aralığı 0 `TypeError`, regülatör açısı 360° `OverflowError` ile çöküyordu | adet alanları tam sayı, uzunluklar pozitif, açılar aralıkta olmalı — hepsi **alan adıyla** reddediliyor |
| **Proje kimliği geri gelmiyordu.** Dosya özelliklerinde yazılı olan proje adı · işveren · pafta no yükleme yanıtına alınmıyordu | önceki projenin kimliği ekranda kalıp sonraki çıktı yanlış adla iniyordu;  artık geri okunuyor ( programın kendi imzası **mühendis sanılmıyor** ) |
| **Motor akımı %18 düşüktü.** Şebekeden çekilen akım `P2/(√3·U·cosφ·ηm)`'dir;  program `ηm`'ye bölmüyordu | **kablo ve sigorta olduğundan küçük seçiliyordu.** Kitabın kendi elektrik sayfası ( `12-Elk.Hesapları!W35` ) 0,85 ile bölerek doğrusunu yapıyordu — kaynak **kendi içinde tutarsızdı**. `motor_elektrik_verimi` ofis sabiti eklendi;  **sigorta kademeleri değişti** ( 11 kW'ta 4 x 25 → 4 x 32 ) |
| **Excel'in elektrik sayfası girdilerden kopuktu.** `12-Elk.Hesapları` kendi sabitleriyle çalışıyordu:  L2 = 5 m · U = 400 V · S1 = 6 · S2 = 4 mm² · cosφ = 0,8 ve kablo kapasiteleri 43 / 34 A hücreye yazılı | teslim edilen kitap ekrandan **başka** hesap yapıyordu;  artık programın girdileri yazılıyor ve kapasiteler kesitten geliyor |

#### İkinci denetim — hesap motorunun standarda karşı denetimi

Birincisi programın **davranışını** ( girdi–çıktı, dosya akışı, uyarılar )
denetlemişti. İkincisi doğrudan **hesap motorlarını** TS EN 81-20 / 81-50'nin
metnine karşı okudu ve on bulgu çıkardı. Hepsi yeniden üretildi; her biri
artık kendi regresyon kontrolüyle korunuyor
( `dogrulama/test_mukavemet.py` · `_denetim_bulgulari` ).

| Bulgu | Yön | Etkisi ve düzeltme |
|---|---|---|
| **`Sf ≥ Smin` yanlış bir geçme ölçütü olarak kullanılıyordu** ( böl. 4 ) | yanlış ret | EN 81-20 m.5.5.2.2 tek şey ister: *gerçekleşen* S, 12/16 ile EN 81-50 m.5.12'nin Sf'sinin **büyüğünden** az olmayacak. `Sf < 12` bir uygunsuzluk değil, "asgariyi Smin belirliyor" demektir. Kitabın koşulu standarda uyan tasarımları reddediyordu ( Sf = 7,89 · **S = 32,5** → "UYGUN DEĞİLDİR" ) ve verdiği öğüt sonuca ulaşmıyordu: halat çapını artırmak Dt/dh'yi düşürür, Sf'yi **büyütür**. Ölçüt kaldırıldı; satır artık hangi asgarinin belirleyici olduğunu yazar |
| **Sonuç başlığı `Dt/dh ≥ 30` diyor, kontrol 40 ile yapılıyordu** ( böl. 4 ) | paftada yanlış sınır | Kontrol doğruydu ( m.5.5.2.1 = 40 ), paftaya basılan sayı yanlıştı. Başlık artık kontrolün kullandığı eşiği ve `S ≥ max( Sf ; Smin )` ifadesini yazar |
| **ω tanım aralığı dışında program çöküyordu** ( böl. 7 ) | çökme | `λ = konsol arası / ix`;  ω tablosu yalnız 20 ≤ λ ≤ 250'de tanımlı. Bölüm 2 λ'yı kırpıp `None`'a karşı korunuyor, bölüm 7 ikisini de yapmıyordu — 50 × 50 × 5 rayda 3.900 mm konsol aralığı ( gerçekçi bir girdi ) ham `TypeError` veriyordu. Artık girdi doğrulaması **izin verilen en büyük aralığı söyleyerek** reddediyor;  doğrulama atlansa bile motor çökmüyor |
| **Halat kütlesinin taraf dağılımı kendi içinde çelişikti** ( böl. 6 ) | **emniyetsiz** | `MSR = ( 0,5·H ± y )·ns·gh` bağıntısının ± işareti dört yük durumunun **üçünde** ters yazılmıştı: kabin en alt duraktayken halat kütlesinin tamamı karşı ağırlık tarafına konuyordu. Kitabın bölüm 1 açıklaması bunun **tersini** söylüyordu. Yön emniyetsizdi — tahrik yeteneği olduğundan iyi çıkıyordu ( 20 duraklı örnekte yükleme oranı 1,23 yerine **1,79**, e^(f·α) = 1,71 sınırını **aşar** ) |
| **Kolon hattı akımı motorun elektrik verimini içermiyordu** ( avan böl. 6 ) | **emniyetsiz** | ηm düzeltmesi makine besleme hattı için yapılmış, **kolon hattı için yapılmamıştı**. `I ≤ Iz` kararı kolon hattına aittir ve o hatta Pşeb = Nsç/ηm akar. Kaynak kitap bunu zaten doğru yapıyor ( `12-Elk.Hesapları!AT7 = W36×1000` ). Kesit olduğundan küçük seçilebiliyordu: **22 kW + 6 mm² · 30 kW + 10 mm² · 55 kW + 25 mm²** birleşimleri "uygun"dan "uygun değil"e döndü. Aynı düzeltme **ε1 ve ε2**'ye de girer ( ε ∝ P ) ve avan çalışma kitabının şablonu da güncellendi ( `SABİTLER!C39 = ηm`;  `E102` ve `E126` ona böler ) — ekran ile indirilen dosya ayrışmasın diye |
| **Sarılma açısı α 180°'yi aşabiliyordu** ( böl. 6 ) | **emniyetsiz** | `Ra < 2·R1` girildiğinde pay negatife düşüyor ve α tek sarımlı kasnakta imkânsız bir değere çıkıyordu ( Ra = 100 mm → 187,65° ). e^(f·α) sınırı α ile büyür. Halat arası artık kasnak çapından küçük olamaz;  bölüm ayrıca `0° < α ≤ 180°` denetler |
| **Ofis sabiti γ / β bölüm 6'yı değiştiriyor, bölüm 4'ü değiştirmiyordu** | pafta ile hesap ayrışıyor | `Nequiv(t)` kanalın **adına** bağlı sabit bir tablodan okunuyordu; γ = 45° seçilse bile 12 kalıyor, pafta 38° yazmayı sürdürüyordu. Artık EN 81-50 **Çizelge 2**'den, ofis açılarından, doğrusal ara değerle hesaplanıyor. Pafta hesabın gerçekten kullandığı γ ve β'yı yazar |
| **Moment ve mil kuvveti askı oranına göre indirgenmiyordu** ( böl. 1 ) | paftada 2 katı değer | 2:1 palangada tahrik kasnağının gördüğü kuvvet `Gmax` değil `Gmax/i`'dir. Motor gücünü etkilemez ( N askı oranından bağımsızdır ve doğru kurulmuştur ), ama paftadan moment okuyup makine seçen bir okuyucuya **iki katı** bir sayı yazılıyordu |
| **Uygulama projesinde "toplam sistem verimi" kutusu yoktu** | verim cezası iki kez inebilir | Avan motorundaki kutunun karşılığı yoktu; imalatçının toplam verimini kullanmak isteyen mühendis ancak ofis sabitini değiştirebiliyordu ve o değişiklik **projedeki bütün asansörleri** etkiliyordu. Kutu eklendi |
| **Kabin alanına pervaz katkısı yarım alınıyordu** ( böl. 3 ) | **emniyetsiz** | EN 81-20 m.5.4.2.1.3: girinti ≤ 100 mm ise hariç, **> 100 mm ise tamamı** alana katılır. Kitap kapı genişliğinin yarısını alıyordu ( 900 mm kapı + 300 mm pervaz → 0,1350 m², tamı **0,2700 m²** ). Kullanılabilir alanı küçük göstermek Çizelge 6'nın izin verdiğinden büyük kabine izin verir |

**Kolon hattı düzeltmesinin ofise pratik sonucu.** `I` ve `ε` motorun payı
kadar ( 1 / ηm = **%17,6** ) yükseldi. Aydınlatma + priz yükü ≈ 1,24 kW olan
tipik bir tesiste kolon hattı kesiti şu güçlerde bir kademe büyür:

| Motor | Eski I | Yeni I | S1 |
|---|---|---|---|
| 22 kW | 39,2 A | **45,8 A** | 6 → **10 mm²** |
| 30 kW | 52,7 A | **61,7 A** | 10 → **16 mm²** |
| 55 kW | 94,9 A | **111,3 A** | 25 → **35 mm²** |
| 75 kW | 128,7 A | **151,0 A** | 50 → **70 mm²** |

**Motor sigortası değişmez** — o zaten motor akımından, ηm dahil
hesaplanıyordu. Değişen kolon hattının kendisidir. Eldeki paftalarda bu güç
sınıflarındaki **S1 kesitleri gözden geçirilmelidir.**

Denetimin *"teyide muhtaç"* listesindeki noktalar da standardın metnine karşı
okundu:

| Nokta | Sonuç |
|---|---|
| `Nequiv(t) = 12` ( V kanal, γ = 38° ) doğru mu | **Doğru.** EN 81-50 Çizelge 2: γ = 35 · 36 · 38 · 40 · 42 · 45 · 50° → 18,5 · 16 · **12** · 10 · 8 · 6,5 · 5. Çizelgenin tamamı programa girdi |
| Regülatör kuvvet ölçütü | **Bulgu doğruydu — ve bir katman daha derindi.** Standardın iki ayrı maddesi iki ayrı kuvvetten söz ediyor: m.5.6.2.2.1.1 d) regülatörün **ürettiği** kuvveti sınırlar ( *"produced **by the governor**"* ) — bu, kasnağın iki yanındaki gerginlik **farkıdır**: `Fçekme = F′reg − Freg`. Güvenlik tertibatı mekanizmasını çeken odur; halatın statik gergisi Freg zaten oradadır ve hiçbir şeyi çekmez. m.5.6.2.2.1.3 b) ise **halattaki** en büyük gerginliği ( `F′reg` ) emniyet katsayısına sokar ( *"produced **in the rope**"* ). Kitap ikisini de F′reg ile yapıyor, üstelik sınıra `2 × Freg` koyuyordu. Devreye sokma kuvveti **imalatçı verisidir**; girilmezse madde denetlenemez ve bölüm **"HESAP EKSİK"** der — proje *uygundur* çıkmaz |
| Karşı ağırlıkta güvenlik tertibatı modellenmiyor | **Bulgu doğruydu.** Bölüm 8 yalnız C.2.2'yi ( normal işletme, k3 = 1,2 ) kuruyordu. Tertibat varsa belirleyici durum **C.2.1**'dir ve orada k1 = 2 · 3 · 5 geçer. Karşı ağırlık güvenlik tertibatı girdi oldu; seçilirse C.2.1 de hesaplanır |
| Bölüm 7 C.2.2'de burkulma ω'sız | **Bulgu yersizdi — program doğru.** EN 81-50 Ek **C.2.2.2** `σv = ( Fv + k3·Maux ) / A` der; ω yalnız **C.2.1.2**'de geçer. İki durumun ayrıldığı artık ayrıca denetleniyor |
| `reg_surtunme` μ üst sınırsız | **Bulgu doğruydu.** m.5.6.2.2.1.3 b) hesaba katılacak değeri kendisi verir: **µmax = 0,2**. Üstü reddediliyordu; artık asansör bazında hiç sorulmuyor, **ofis sabitidir** ( `reg_mu` ) — altına inmek de halatın emniyet katsayısını şişiriyordu |
| `Nsç = 0` girilirse paftada iki motor gücü | **Yeniden üretilemedi.** Aralık dışı Nsç uyarı ile bildiriliyor, standart kademeden seçiliyor ve bölüm 1, kurulu güç cetveli ve ε2 **aynı** değeri kullanıyor. Yine de kalıcı bir kontrol eklendi |
| Ölü ve yanıltıcı kod | `KANAL_ISLEME` gerçekten yanlış adlandırılmıştı — içindeki sayılar μ değil **f**'dir ( 0,1 / sin 19° = 0,30716 ). Başlık düzeltildi ve tablonun **çivili** olduğu ( γ = 38° · β = 90° ) açıkça yazıldı; motor onu hiç kullanmaz, ekrandaki tablo da artık f'yi ofis açılarından üretir |
| `DURAK_AZAMI = 20` — trafik 30 katı destekliyor | Sınır kaynak kitabın **kendi düzeninden** gelir ( `Veri Girişi`!G12:G34 ). Kapsam farkı bilinçlidir ve arayüz bunu söyler; 20 duraktan fazlası uygulama projesinde hesaplanamaz |
| Sigorta ↔ kablo koordinasyonu | `I2 ≤ Iz2` kontrolü ( ve artık `I ≤ Iz` de doğru güçle ) çoğu durumu yakalıyordu;  seçilen sigortanın kendisi denetlenmiyordu.  **Artık denetlenir** ( Sürüm 3.2, `In ≤ Inmax2` ):  grup sigortası makine besleme kablosunun sınırını aşamaz — EK-5 1.31.13, 6 mm² üstünde Iz;  bkz. §7 |

#### Üçüncü denetim — sayısal fizik kontrolleri

Kuvvet dengesi ve sınır kontrollerini sınayan hesaplarla üç sorun daha
bulundu. Olumlu kontrol olarak kuvvet iki katına çıkarılınca eğilme momenti
**2 kat**, açıklık iki katına çıkarılınca sehim **8 kat** çıkıyor — temel
bağıntılar tutarlı.

| Bulgu | Yön | Etkisi ve düzeltme |
|---|---|---|
| **Negatif sehim ve gerilme, sınırı aşsa da "uygun" sayılıyordu** ( böl. 7 ) | **emniyetsiz** | Kabin merkezi ray ekseninin öbür yanına düşünce ( `xc < 0` ) Fx negatife iner. `δ = −5,59 mm` iken sınır 5 mm olmasına rağmen `δ ≤ 5` **sessizce geçiyordu**. Aynı hata bir yerde daha vardı: `σm = σx + σy` işaretli toplanınca ters işaretli iki eğilme **birbirini götürüyor**, `σc = σv + σm` de küçülüyordu ( örnekte σm = −19,87 yerine **71,44 N/mm²** ). Fx ve moment işaretini korur — yön bilgisidir; **σ ve δ büyüklük olarak** yazılır ve karşılaştırılır |
| **Karşı ağırlık güvenlik tertibatının tepkisi kuyu tabanına aktarılmıyordu** ( böl. 9 ) | **emniyetsiz** | Kabin rayında bu kalem sayılıyor, karşı ağırlıkta sayılmıyordu: tertibat *"Kaymalı"* seçilse bile **FAR değişmiyordu** ( 1.015,50 N ). Eksik tepki `k1·gn·Mcwt/n = 2 × 9,81 × 1.100 / 2 = 10.791 N/ray`; taban **11.806,50 N/ray** görmeliydi. Bu sayı **inşaat projesine** bildirilir ve olduğundan düşük gidiyordu. Ray kütlesinin payı burada da bir kez sayılır ( `Fk − Mg·gn` ) |
| **Denge oranı değişince aynı projede iki farklı karşı ağırlık** | tutarsızlık | Kitabın `C80` formülü *"kabin ağırlığı + beyan yükü / 2"* diye çivili; bölüm 1 ise `Ga = P + q·Q` kuruyordu. `q = 0,60`'ta motor ve ağırlık tamponu **1.180 kg**, tahrik ve ağırlık rayı **1.100 kg** kullanıyordu. Kütle artık **tek yerden** türer ve bölüm 1 de onu okur; teslim edilen kitabın `C80` formülü de projenin q'suyla yazılır |

#### Dördüncü denetim — sınır durumları

Fiziksel olarak geçersiz girdilerin **güvenilir görünen sonuç üretmesi**. Bu
iki bulgu normal girdilerde hesabı etkilemez; kalkanların eksikliğidir.

| Bulgu | Etkisi ve düzeltme |
|---|---|
| **Sıfır ya da negatif sistem verimi kabul ediliyordu.** Verim ile palanga kaybı ayrı ayrı geçerli sayılıyor, **aralarındaki ilişki** denetlenmiyordu | η = 0,10 · Δη = 0,10 → η′ = 0 → **sıfıra bölme**. Δη = 0,20 → η′ = **−0,10** ve gereken güç **−44,26 kW**; `Nsç ≥ N` her motoru geçiriyor, temiz bir projede genel sonuç **"UYGUN"** çıkıyordu. Artık hesaptan önce `0 < η′ ≤ 1` denetleniyor ve hata **iki sabiti de adıyla** söylüyor. *( Avan motorunda bu kalkan zaten vardı — eksik olan uygulama tarafıydı. )* |
| **İmkânsız geometri negatif halat ağırlığı üretiyordu.** Kabin paten arası 30.000 mm verildiğinde halat boyu **−4,82 m**, ağırlığı **−5,13 kg** | Negatif ağırlık yükten **düşülüyor**: motor gücünü azaltıyor, halat güvenlik katsayısını **yükseltiyor** — imkânsız geometri hesabı *iyileştiriyordu*. Artık tampon/paten yığınının kuyuya sığması denetleniyor; hata toplama giren beş ölçüyü tek tek yazıyor |

Her ikisinde de **ikinci kalkan** var: girdi doğrulaması atlansa bile motor
çökmüyor, bölüm 1 *"HESAP YAPILAMADI"* diyor ve proje *uygundur* çıkmıyor.

#### Beşinci denetim — teslim edilen çizim AutoCAD'de açılmıyordu

Teslim edilmiş bir uygulama projesinin DXF'i **AutoCAD 2027 for Mac'te
açılmıyor**, program *"A software problem has caused application to close
unexpectedly"* verip kapanıyordu. Dosya bozuk değildi: yapısal denetimden
sıfır hatayla geçiyor, etiket akışı kusursuz, sınıflar ve karolar eksiksiz.

Sebep AutoCAD'in kendi başsız motoruyla ( `AcCoreConsole` ) yığın izi alınarak
bulundu — çökme yeniden çizim sırasında, bir yazının TrueType genişliği
ölçülürken:

```
regenall → fullregen → AcDbImpText::textDraw → TextEditor::get_extents
  → AcGiContextImp::getTrueTypeTextExtents → WhipImp::GetTextExtents
    → FontCacheHashImp::calTotalWidths → FontCacheOSX::getCharData   ← ÇÖKME
```

Suçlu, ikili aramayla 2 943 varlıktan tek bir yazıya, oradan **iki karaktere**
indirildi. Her adım gerçek AutoCAD çekirdeğinde ölçüldü.

| Bulgu | Etkisi ve düzeltme |
|---|---|
| **Şapka ( `^` ) AutoCAD'i çökertiyordu.** AutoCAD metinde `^` + karakteri **denetim karakteri** diye yorumlar ( `^8` → 0x18, `^(` → 0x08 ); yazı tipinde o kodun glifi yoktur ve macOS'ta arama çöker | En kısa çökerten parça **`^8`** ( `8` tek başına açılıyor ). İkinci suçlu `e^(f·α)`. Şapka paftada **üs işareti** olarak geçiyor — `10^[…]` · `(Dt/dh)^8,567` · `e^(f·α)` — yani kaçınılmaz. Çizimde artık **U+02C6** yazılır: görünüşü şapkanın aynısı, CP1252'de 0x88'de durduğu için her ANSI yazı tipinde var, hiçbir CAD onu denetim karakteri saymaz. `**` ve `%%94` de çökertmiyordu ama biri gösterimi bozar, öteki yalnız AutoCAD'in anladığı bir kaçıştır |
| **`$EXTMIN` / `$EXTMAX` atamaları dosyaya hiç geçmiyordu** | ezdxf bu başlıkları dosyayı **yazarken** model sekmesinin kendi değerlerinden yeniden üretir ( `Drawing.update_extents` ); başlığa yazmak boşunaydı. Şablondan gelen `1e+20 / -1e+20` ( *"hiç hesaplanmadı"* ) dosyaya olduğu gibi geçiyor, ZOOM EXTENTS'in dayanağı kalmıyordu. Değer artık sekmenin üstüne yazılıyor |
| **Kayıtlı görünüm orijinde duruyordu** | Şablonun `*Active` görünümü ( 0, 0 ), 1 000 birim yüksekliğinde; oysa ofisin pafta formatı **x ≈ −4 000**'de. Çökme olmasaydı bile çizim **bomboş ekranla** açılırdı. Görünüm artık çizimin üstüne oturtulur |

Şapka **yalnız uygulama paftasında** geçiyordu; avan paftalarını ölçen TEST 4
bu yüzden hatayı göremedi. Uygulama paftasının CAD çıktısı artık **TEST 11'de**
ayrıca ölçülüyor: hiçbir yazıda `^` ya da `%%` kalmadığı, üs işaretinin
paftada gerçekten geçtiği ( ölçüt boş kalmasın ), sınırların hesaplandığı ve
görünümün çizimin üstünde olduğu. Düzeltilmiş çizim, aynı kaynak paftalardan
yeniden üretilip **AutoCAD 2027'de açılarak** doğrulandı.

#### Altıncı denetim — saptırma kasnağı denetlenmiyordu

| Bulgu | Etkisi ve düzeltme |
|---|---|
| **Saptırma kasnağının halata göre çapı hiç sınanmıyordu.** Program yalnız tahrik kasnağını denetliyordu | Halat Ø8 · tahrik kasnağı Ø400 · saptırma kasnağı Ø240 girildiğinde `Dt/dh = 50` geçiyor, ama `Dp/dh = **30**` olmasına rağmen halat bölümü **UYGUN** çıkıyordu. TS EN 81-20 **m.5.5.2.1** oranı *"kasnak, makara ve tamburlar"* için ister — tahrik kasnağına özel değildir. Saptırma kasnağı bulunan projelerde artık `Dp / dh ≥ 40` da denetleniyor; kasnak yoksa ( `Nps = Npr = 0` ) pafta bunu ayrıca yazıyor. `Dp` girdisi kasnakların **ortalama** çapı olduğu için denetim ortalamaya uygulanır — çapları farklı bir düzende **en küçük kasnak ayrıca gözden geçirilmelidir**, pafta bunu da söyler |

Bulguyla birlikte gelen "üreticinin TÜV belgesi küçük oranları özel şartlarla
gerekçelendiriyor" savı **uygulanmadı**: EN 81-20 m.5.5.2.1'in metninde böyle
bir istisna yoktur, program da standardın düz metnini uygular. Bir imalatçı
belgesine dayanarak oranı düşürmek proje müellifinin kendi kararıdır ve
gerekçesi projede ayrıca belgelenmelidir.

#### Yedinci denetim — el hesabıyla karşılaştırma

Piyasada en yaygın kurulumlardan biri girilip **bütün bölümler elle yeniden
hesaplandı**: 8 kişi / 630 kg · 1,0 m/s · 2:1 dişlisiz · 6 durak · 15 m ·
kabin 1100 × 1400 ( ISO 4190-1'in 630 kg kabini ) · 5 × Ø8 halat · Ø320
kasnak · T89/B ray. Motor gücü ayrıca **tork × açısal hız** yolundan bağımsız
doğrulandı ( iki yol da 4,667 kW ). `Gh · F1 · Ga · Gmax · N · M`, `Sf · S`,
`α · f · T1 · T2 · e^(fα)`, `Fk · λ · ω · σk · Fx · My · σc · σ · δ`,
`FKR · FAR · Fkt · Fat` — **hepsi birebir tuttu**. Bir tek yer ayrıldı:

| Bulgu | Etkisi ve düzeltme |
|---|---|
| **`xp` ile `xQ` farklı eksenlerden ölçülüyordu.** `xQ = xc + D/8` ray ekseninden, `xp = mkapı·(D/2+pay)/P` ise **kabin merkezinden**; ikisi aynı toplamda moment kolu olarak toplanıyordu | `xc` ray–kapı arasıyla kayar, `xp` **hiç kımıldamıyordu** — kabin gövdesinin ray eksenine göre kaçıklığı sayılmıyordu. Ray ekseni kabin merkezinden geçtiğinde ( `xc = 0` ) iki okuma çakışır ve **kitabın örneği tam oradadır**; ray kaydıkça ayrışır ve **emniyetsiz tarafa da düşer**: 1400 mm derinlikte ray–kapı arası 500 mm iken devirici moment gerçeğin **%79'u**, 1000 mm iken **%36'sı** çıkıyordu. Artık `xp = xc − mkapı·(D/2+pay)/P`;  33 hücre kayıyor, 16'sı sapma kaydına eklendi |

Aynı turda **iki yorum notu** kaydedildi, kod değiştirilmedi:

- **`Nequiv(t)` altı kesik V kanalda β satırından okunuyor** ( Çizelge 2 ). γ = 38° V satırı seçilseydi `Nequiv` 6 → 13 ve gereken `Sf` 15,51 → 20,55 çıkardı ( **%32,5** ), örnek projede asgari halat sayısı 4 → 5 olurdu. Seçim savunulabilir — m.5.11.2.3.1.2 sertleştirilmemiş V kanalda alt kesmeyi zorunlu kılar ve sürtünmeyi de β ile hesaplar — ve varsayılan açılarda ofis kitabıyla birebir tutar; ama **denetim kuruluşları arasında yorum farkı doğabilir**, pafta β'yı ve γ'yı ayrı ayrı yazar.
- **Yük kaçıklığı yalnız `+D/8` yönünde alınıyor** ( `xQ = xc + D/8` ). `xc` negatifken `−D/8` daha olumsuz olabilir. Ek C'nin şekli elde olmadan yön kabulü doğrulanamadı.

#### Sekizinci denetim — standardın metnine karşı satır satır

Yedinci turun sonunda **TS EN 81-20 ve TS EN 81-50'nin tam metinleri
bulunup okundu** ( BS sürümleri ). Ek C'nin bütün bağıntıları, Çizelge 2,
Çizelge 14, m.5.10.5 ve m.5.11.2.3.1 programdakiyle **satır satır**
karşılaştırıldı.

**Doğrulananlar:** C.2.1.1'in `Fx · Fy · My · Mx · σy · σx`, C.2.1.2'nin
`σk`, C.2.1.3'ün üç birleşik ölçütü, C.2.1.5'in `0,7·F·l³/(48·E·I)`,
Çizelge 2'nin bütün değerleri, m.5.11.2.3.1'in sürtünme bağıntıları,
`xQ = xC + Dx/8` yön kabulü — hepsi aynı. **Sapma ④ da doğrulandı:**
m.5.10.5'in sembol listesi `l` için *"length of the guide shoe lining"*
diyor. **Yedinci turun `xp` düzeltmesi de doğrulandı:** Ek C.1.2 `xp`'yi
*"in relation to the guide rail cross coordinates"* diye tanımlar — `xC` ve
`xQ` ile aynı orijin.

**Standardın kendi çözümlü örnekleri de koşturuldu.** EN 81-50 **Ek E** üç
sayısal örnek verir ( 2:1 V kanal · 1:1 altı kesik U kanal · 1:1 çift sarım );
üçü de programda **birebir** çıkar ve artık kalıcı testtedir. E.1'de standart
`Kp`'yi 2,07'ye yuvarlayıp çarpar ( 2,07 × 2 = 4,14 ); tam değer 2,0736 →
4,1472'dir, program yuvarlamaz. Ayrıca **ω'nın tamamı** maddenin kendi parçalı
formülleriyle üretilip karşılaştırıldı: `Rm` = 370 · 440 · 520 için `λ` = 20…250
aralığında **693 nokta**, en büyük fark **1,8·10⁻¹⁵**. Ara `Rm` için standardın
verdiği formül ( `ωR = (ω520−ω370)/150·(Rm−370) + ω370` ) programın yaptığı
doğrusal ara değerin ta kendisidir.

**Ayrıldığı sekiz nokta** yukarıdaki tabloda ㉕ – ㉜'dir. Dördü sayıyı
değiştirir ve **dördü de emniyetsiz yöndeydi**: altı kesik V kanalda
`Nequiv(t)` 5,0 yerine 12 ( gereken `Sf` %32,5 artar ), ve normal işletme ·
yükleme · karşı ağırlıkta `Fy` iki kat ( payda `n·h` değil `( n/2 )·h` ).
Üçüncüsü, yükün **yalnız + yönde** kaydırılmasıydı: m.5.7.2.3.4 normatif
olarak *"en olumsuz konum"* der, Ek C'nin Şekil C.2'si ise **bilgilendirici
bir örnek** olarak tek yön gösterir. Kabin merkezi ray ekseninin öbür
yanındayken ( `xc < 0` ) + yön, boş kabinin momentini **dengeliyor** ve
gerilmeyi olduğundan küçük gösteriyordu. 1400 mm derinlikte ray–kapı arası
1.200 mm iken `Fx` **192 N yerine 2.114 N** ( 11 kat ) çıkıyor ve sehim 5 mm
sınırını aşıyor. Kalan dördü eksik terim ya da eksik seçenektir;
varsayılanları sonucu değiştirmez ama tesis bir değer verdiğinde hesaba
girer.

Dördüncüsü **㉔'ün kaçırdığı yarısıydı**: `xp` ray eksenine taşınmış ama aynı
toplamdaki **`xi` ( kapı konumu ) ham mesafe olarak** bırakılmıştı. Ek C.1.2
`xi`'yi `xC · xp · xQ · xS` ile aynı Kartezyen sistemde tanımlar; kapı, ray
ekseninin kabin merkezine göre **ters** tarafındadır. Ray ekseni kabin
merkezini geçtiğinde eşik kuvveti `Fs` ile boş kabinin momenti birbirini
**dengeliyordu**: 1400 mm derinlikte ray–kapı arası 1.200 mm iken yükleme
durumunun `Fx`'i **8,2 N** çıkıyor, doğrusu **864,4 N** — 105 kat.

Bu bulguyla birlikte teslim edilen kitabın **σ ve δ hücreleri de büyüklüğe
çevrildi**. Üçüncü denetim bu kuralı motorda kurmuştu, Excel tarafı işaretli
hesaplamaya devam ediyordu: kuvvet negatife düştüğünde kitap negatif sehim
gösterip *"δ ≤ 5 mm"* karşılaştırmasını sessizce geçiriyordu. Doğrulama
senaryolarına `xc = 0` ve `xc < 0` geometrileri eklendi — bu bölge kapsam
dışıydı ve iki hatayı birlikte gizliyordu.

### Test yazılırken bulunan ve düzeltilen hatalar

| Bulgu | Etkisi |
|---|---|
| Python'un `round()` bankacı yuvarlaması yapıyor (865 → 860), Excel'in `ROUND`'u yarımı yukarı yuvarlıyor (865 → 870) | Tablo-11 boş kabin kütlesinde bazı ara yüklerde **10 kg sapma** |
| Çoklu asansör sonuç metni Excel'den bir boşluk farklıydı | paftada metin uyuşmazlığı |
| `1,234.56` gibi İngilizce ondalık yazımı `1,23456` olarak okunuyordu | **yanlış hesap** |
| `NaN`, `Infinity`, aşırı büyük sayı girilirse | **program çöküyordu** |
| Avan tarafında zorunlu bir alan boş bırakılırsa | **program çöküyordu** |
| Ofis standardına `0` yazılırsa (armatür ışık akısı, ray sayısı) | **sıfıra bölme hatası** |
| XLSX indirmesinde kullanılmayan hesap yolu şablonun örnek verisiyle geliyordu | projeyle **ilgisiz bir pafta** çıktı alınabiliyordu |
| Bozuk istek gövdesi API uçlarında | **HTTP 500** |
| Hesap tamamlanamadığında PDF üretimi | **çöküyordu** |
| Şablon dosyası eksikse XLSX indirmesi | sessizce **bozuk bir dosya** iniyordu |
| Test paketi geçici dosyaları proje klasörüne yazıyordu | silme izni kısıtlı makinede test takılıyordu |
| Excel'den geri yüklemede ondalıklı açılır liste değeri (hız 1,6 / kesit 1,5) eşleşmiyordu | kabin hızı **sessizce boş kalıyor**, avan paneli tamamen boşalıyordu |
| Dar ekranda 331 px yatay taşma | telefonda düzen bozuluyordu |
| Avan sekmesinin uyarıları yalnız PDF'e basılıyor, ekranda hiç görünmüyordu | eksik girdi / geçersiz ofis standardı uyarısı **fark edilmiyordu** |
| Trafikte kapasite veya hız değişince avan sekmesi sessizce eski değerde kalıyordu | revizyonda **tutarsız pafta** çıkabiliyordu |
| Açılır listede seçilebilen 1000 / 1200 / 700 mm kapı genişlikleri tabloda yoktu | seçilebilen bir değer **hesabı durduruyordu** |
| Palanga ve denge faktörü proje geneli sabitti | dişlili + dişlisiz karışık projede **yanlış motor gücü ve karşı ağırlık** |
| Bodrum durağı hiçbir yerde hesaba girmiyordu | Tablo-2 asgari hızı **düşük seçilebiliyordu** |
| Uygulama projesinin **12 girdisi** ( kesitler · hat uzunlukları · temel ölçüleri · makine dairesi · paten balatası ) Excel'e hiç yazılmıyordu | revizyonda **sessizce kayboluyor**, kesitler varsayılana dönüyordu — ekran *"41 girdi geri yüklendi"* deyip eksiği söylemiyordu |
| Aralık dışı Nsç / L1 motor tarafından reddedilip varsayılan kullanılırken, **XLSX'e reddedilen değer yazılıyordu** ( Nsç = 900 kW → ekran 7,5 kW, dosya 900 kW ) | indirilen kitap **paftadan farklı hesaplıyordu**;  yazıcı motorun kabul koşulunu kendi süzgeciyle ikinci kez uyguluyordu |

Bunların hepsi düzeltildi; her biri için pakete kalıcı bir test eklendi.

### Kullanıcı gibi denemede bulunan ve düzeltilen hatalar

Program baştan sona bir kullanıcı gibi kullanılıp ( konut · yüksek konut ·
iş merkezi · hastane · otel ) her sonuç bağımsız hesapla karşılaştırıldı.
Hesaplarda sapma bulunmadı;  aşağıdakiler ekranda ya da paftada **yanlış
ya da yanıltıcı görünen** şeylerdi.

| Bulgu | Etkisi |
|---|---|
| **Tablolar sekmesinde beş tablonun başlıkları kaymıştı** ( ray profilleri · ray geometrisi · NPU · gezici kablo · karşı ağırlık malzemesi ) | T 50 rayının 3,7 kg/m'si *"b"*, 14,3 mm'lik *e*'si *"gr"* başlığı altında görünüyordu.  Başlıklar artık motorun **sütun tanımından** kuruluyor, kayamaz.  NPU tablosundaki üç yazım hatası da ( 30x15 Ix · 280 ve 300 A ) DIN 1026-1'e göre düzeltildi — hesaba girmiyorlardı |
| **Hız seçilmeyince "tg'yi elle girin" deniyordu** | Hastane · poliklinik · karma bina · katlı otopark MMO/697 Tablo-2'de yoktur; eksik olan **hızdı**, tg değil.  Mesaj artık sebebi ve çareyi söylüyor;  kat sayısı boşken de eksik olanın **③ kat sayısı** olduğunu |
| **Trafik hata metni iç adları gösteriyordu** ( *"hizli1 = 1.200"* ) | Ekranda öyle bir kutu yok.  Metin artık kutunun **ekrandaki adını** söylüyor ( *"⑤ Daire sayısı = 1.200"* );  ⑤ / ⑥ adları bina tipine göre değiştiği için etiket ile hata metni **aynı tanımdan** okunuyor |
| **Kapağın asansör bilgileri dolu görünüp boş basılıyordu** | Gri yazılar ( *"10 kişi"*, *"7,5 kW"* ) sabit örneklerdi.  Artık boş kutu **projenin hesabından** dolar ( kapasite · hız · durak · seyir · kabin · askı · adet · tahrik · motor gücü · kullanım amacı ) ve gri yazı kapağa basılacak değerin kendisidir.  Birden çok asansörün değeri dar hücreye sığmazsa yandaki hücreye taşmak yerine iki satıra bölünür |
| **Paftada hızın kaynağı hep "MMO/697 Tablo-2" yazıyordu** | Hastane paftasında ( Tablo-2'de hastane yok ) ve hızı kullanıcı seçtiğinde bile.  Artık hız Tablo-2 asgarisiyse *Tablo-2*, değilse *Proje kararı ( Tablo-2 min. … )* basılıyor |
| **Uygulama paftası ray kuvvetini "kabin raylarına gelen kuvvet" diye yazıyordu** | FKR ve FAR **tek bir rayın** kuvvetidir ( bir rayın kütlesi + güvenlik tertibatı payı ( P + Q ) / n ).  İnşaat mühendisi sayıyı toplam sanıp raylara bölseydi yükün yarısını kullanırdı.  Bölüm 9 başlıkları, sonuç satırı ( *N / ray* ), PDF özeti ve ekran kutusu artık *"bir kabin rayına"* diyor — avan bunu zaten böyle yazıyordu.  Sayı değişmedi;  anlamı TEST 11 ray sayısıyla sınıyor |
| **Halat boyundaki "tampon/paten yığını" yalnız toplam olarak görünüyordu** ( ör. 6.660 mm ) | Bölüm 1'e yığının beş ölçüsünü tek tek yazan satır eklendi ( ağırlık tamponu baba + çarpma arası − ezilme + ağırlık paten arası + kabin paten arası );  elle yeniden hesaplayan artık paftadan bulabiliyor |
| **Tek hesap + ek asansörlü avan projesi her açılışta bir asansör fazla açılıyordu** | Adedi trafik bulan ( ör. 2 ) projeye bir yük asansörü eklenince proje 3 asansörle kaydediliyor, ama sayfa yenilenince de, dosya boş sayfada ya da başka bir proje açıkken açılınca da **4 kartla** açılıyordu.  Açılış anında trafik sonucu henüz yoktu ( ya da önceki projeninkiydi );  grup 1 sanılıyor, "dolu kart kapanmaz" kuralı ek asansör sayısını şişiriyordu.  Hesap ve PDF'ler değişmiyordu ( 4. kart boştu ) ama yeniden kaydedilen dosya 4 asansör diyordu.  Artık önceki projenin sonucu atılır ve grup adedi dosyadaki açık kart sayısından kurulur;  tek hesapta trafik geçici olarak hatalıyken de son bilinen adet kullanılır |
| **`.uygulama` açmak avan projesinin bellekteki durumunu bozuyordu** | Yükleme avan durumunu ( trafik adedi · ek asansör · otomatik alan izleri ) her dosyada yeniden kuruyordu;  uygulama dosyası açılınca avanın izleri siliniyor, ek asansör sayısı yanlış türetiliyordu.  Avan durumu artık yalnız avan verisinden kurulur |
| **Tanınmayan seçim değeri sessizce değişiyordu** | Dosyadaki değer bu sürümün listesinde yoksa açık asansörde uyarısız varsayılana — dolu formda **önceki projenin ya da önceki asansörün değerine** — dönüyor, öbür asansörlerde ham kalıp hesabı "geçersiz seçim" diye durduruyordu;  ekranda yalnız "Proje açıldı" yazıyordu.  Artık bütün asansörlerde aynı kuralla listenin varsayılanına döner ve pencere hangi alanın hangi değerinin neye döndüğünü sayar |
| **Sarılma açısı girilmeyince sayfa 1 aynı eksikliği iki kez yazıyordu** | Ne yapılacağını anlatan uyarı kaldı, altındaki *"HESAP EKSİK — α girilmedi"* tekrarı kalktı.  Eksik listesi ve genel hüküm değişmedi;  α dışındaki eksikler uyarılarda aynen duruyor |

### Standarda göre verilen hesap kararları ( uygulama projesi )

Motor ofisin eski mukavemet çalışma kitabından yola çıkarak yazıldı ve kitapta
bir dizi sorun çıktı. **Uyulması gereken standart TS EN 81-20 / TS EN 81-50'dir**;
aşağıdaki noktalarda kitap standarttan ( yalnız verim, moment ve denge oranı
maddelerinde ofisin kendi kabulünden ) sapıyordu — program standardı uygular.
Her kuralın gerçekten uygulandığını TEST 9 ayrı ayrı denetler.  ( Program
Sürüm 3.1'den beri Excel kullanmaz;  "kitabın yaptığı" sütunu kararın
gerekçesi olarak tarihçede bırakılmıştır. )

| # | Konu | Standart | Kitabın yaptığı | Programın yaptığı |
|---|---|---|---|---|
| ① | Tahrik kasnağı / halat oranı | **EN 81-20 m.5.5.2.1** — en az **40** | Başlığı "≥ 40" yazar, kontrolü **30** ile yapar | 40 uygulanır |
| ㉜ | **Kapı konumu xi** | **EN 81-50 Ek C.1.2 / C.2.3.1** — `xi` *"position of the car door"*, `xp` ile **aynı** ray-ekseni sisteminde | Ray–kapı arasını **ham mesafe** ( hep artı ) yazar | `xi = −RK`; ayrıca kitabın σ/δ hücreleri **büyüklüğe** çevrildi |
| ㉛ | **Yük en olumsuz konumda** | **EN 81-20 m.5.7.2.3.4** — beyan yükü, kabin alanının **en olumsuz** konumdaki 3/4'üne dağıtılır | `xQ`'yu her zaman `xc + Dx/8` alır | ± iki konum denenir, momenti **büyüten** seçilir |
| ㉕ | **Altı kesik V kanalda Nequiv(t)** | **EN 81-50 Çizelge 2** — iki satır var: `V-grooves (γ)` ve `U-Undercut grooves (β)` | Altı kesik V'yi **β** satırından okur ( β = 90° → 5,0 ) | **V satırı** ( γ = 38° → 12 ). m.5.11.2.3.1.2 altı kesik V'yi *V kanal* sayar |
| ㉖ | **Fy'nin paydası** | **EN 81-50 Ek C.2.1.1 b) · C.2.2.1 b) · C.2.3.1 b)** — üçünde de `( n/2 )·h` | Yalnız C.2.1'de doğru; C.2.2 · C.2.3 · karşı ağırlıkta `n·h` → **Fy yarısı kadar** | Üç durumda da `( n/2 )·h` |
| ㉗ | **Normal işletme katsayısı** | **EN 81-20 Çiz. 14** — `k2` (Running) = 1,2; `k3` için sayı **vermez** | İkisini tek bir "k3 = 1,2" ile karıştırır | `k2` çizelgeden; `k3` ofis sabiti oldu |
| ㉘ | **Fp — klips itme kuvveti** | **EN 81-50 Ek C.2.1.2 · C.2.2.2 · C.2.3.2** — `Fv = … + Fp` | Terim hiç yok | Girdi olarak eklendi ( varsayılan 0 ) |
| ㉙ | **δstr — bina sehimi** | **EN 81-50 Ek C.2.1.5 · C.2.2.5 · C.2.3.5** — `δ = … + δstr` | Terim hiç yok | δstr-x · δstr-y girdi oldu ( varsayılan 0 ) |
| ㉚ | **Makaralı paten flanşı** | **EN 81-50 m.5.10.5** — makaralıda `1,85·Fx/c²` | Yalnız kaymalı formülü tanır | Paten tipi **ray başına** girdi oldu ( kabin · karşı ağırlık ); makaralıda σF **%24 büyük** |
| ㉔ | **Boş kabinin ağırlık merkezi xp** | **EN 81-50 Ek C.2.1.1** — `Fx = k1·gn·(Q·xQ + P·xp)/(n·h)` payı **ray eksenine** göre devirici momenttir | `xp`'yi **kabin merkezinden** ölçer ( yalnız kapı kütlesi ); ray–kapı arası değişse de kımıldamaz | `xp = xc − mkapı·(D/2+pay)/P` — iki moment kolu da ray ekseninden |
| ㉓ | **Saptırma kasnağı / halat oranı** | **EN 81-20 m.5.5.2.1** — oran *kasnak, makara ve tamburlar* için en az **40** | Yalnız **tahrik** kasnağını sınar; D2 hesaba sadece `Kp = (Dt/Dp)⁴` olarak girer | Saptırma kasnağı varsa `Dp / dh ≥ 40` de denetlenir |
| ② | Karşı ağırlık rayı σ(My) | **EN 81-50 Ek C.2.1.1** — Fy → Mx → **Wx** | Wy'ye böler | Wx'e bölünür |
| ③ | Durum 2'de xQ | **EN 81-50 Ek C.2.1.1** | Sabit **0** yazar ( başlığı "xQ = xc" dese de ) | xQ = xc |
| ④ | Flanş eğilmesinde ℓ | **EN 81-50 m.5.10.5** — ℓ = paten balatası **uzunluğu** | Paydaya **1** yazar ( ℓ harfi 1 rakamı okunmuş ) | ℓ girdi; boşsa 2·b'den türetilir |
| ⑤ | ω burkulma katsayısı | **EN 81-50 m.5.10.3** — ω, λ **ve Rm**'e bağlıdır | Tek tablo kullanır; o tablo yalnız **Rm = 370** eğrisidir ve ray çeliğinden bağımsız uygulanır | Rm 370 ve 520 eğrileri, arada doğrusal ara değer |
| ⑥ | Acil frenlemede μ | **EN 81-50 m.5.11.2.3.2** — μ = 0,1/(1+v/10), v **halat** hızı | Bağıntıya **kabin** hızını koyar | v = kabin hızı × askı oranı |
| ⑦ | Nps · Npr | **EN 81-50 m.5.12.2** — tesisin askı düzenine bağlı | Hesap sayfasına **sabit** 1 ve 0 yazar | Girdi;  Nps boşsa askı oranından ( **Ek E**:  1:1 → 1 · 2:1 → 2 ), 2:1'de 2'den az girilirse uyarı verilir |
| ⑬ | **Kuyu tabanı yükünde ray ağırlığı** | **EN 81-20 m.5.2.1.8.4** — ray kütlesi ve güvenlik tertibatı tepkisi **ayrı kalemler** | `FKR = gn·Gr·LR + MY + Fk`;  `Fk` zaten `Mg·gn` içerir → ray ağırlığı **iki kez** | Ray kütlesi bir kez;  tepki `Fk − Mg·gn` |
| ⑫ | **Sürtünme çarpanı f** | **EN 81-50 m.5.11.2.3.1.1** ( yarım daire ) ve **m.5.11.2.3.1.2** ( V ) — **iki ayrı bağıntı** | Kanal şeklinden **bağımsız** olarak hep V kanal bağıntısı;  alt kesilmesi olmayan kanalda da β = 90° | Şekle göre doğru madde;  alt kesilme yoksa β = 0 |
| ⑪ | Acil frenleme yavaşlamasının **alt** sınırı | **EN 81-50 m.5.11.2.2.2** — *"in no case … less than 0,5 m/s²"* | Yalnız üst sınırı ( 1 gn ) denetler | 0,5 m/s² altı **reddedilir** |
| ⑩ | **Kabin alanı tablosu** | **EN 81-20 Çizelge 6** — 28 beyan yükü | 7'si tabloda ve açılır listede **yok** ( 100 · 1050 · **1250** · 1350 · 1425 · **1500** · 2500 kg );  320 kg için 0,97 m² | Tablo Çizelge 6'ya tamamlandı;  320 kg standardın ara değeriyle **0,953** |
| ⑨ | Motor verimi η | **Ofisin kendi tablosu** ( avan ): dişlisiz 0,85 · dişli 0,50 · palangalı sistemde −0,10 ( MMO/697 §2.4 ) | Makine tipinden **bağımsız** sabit 0,92; `B130`'daki makine tipini hiç okumaz | η makine tipinden gelir, palanga düşüşü uygulanır |
| ⑧ | İki sığınma açıklığı | **EN 81-20 m.5.2.5.7.3** ve **m.5.2.5.8.2 a) 2)** | Kabin üstü **1200 mm**, ray dibi **150 mm** — ikisi de standartta yok | Kabin üstü = sığınma hacminin yüksekliği ( **1000 mm** ), ray dibi = Şekil 7 ( **100 mm** ) |
| ⑭ | **Kabin önü girintisi** | **EN 81-20 m.5.4.2.1.3** — ≤ 100 mm hariç, **> 100 mm ise tamamı** | Kapı genişliğinin **yarısını** katar;  eşiği "≥ 100" tutar | Girintinin tamamı;  100 mm'nin kendisi hariç |
| ⑮ | **`Sf ≥ Smin` geçme ölçütü** | **EN 81-20 m.5.5.2.2** — ölçüt `S ≥ max( Sf ; Smin )` | Sf'yi Smin ile karşılaştırıp **UYGUN / UYGUN DEĞİL** yazar | Ölçüt kaldırıldı;  satır hangi asgarinin belirleyici olduğunu yazar |
| ⑯ | **Nequiv(t)** | **EN 81-50 m.5.12.2.2 Çizelge 2** — γ ve β'nın fonksiyonu | Kanalın **adına** bağlı sabit tablo;  ofis açısı değişse kımıldamaz | Çizelge 2'den, ofis açılarından, doğrusal ara değerle |
| ⑰ | **Halat kütlesinin taraf dağılımı** | **EN 81-50 m.5.11.2.2** — ± işareti kabinin konumundan | Dört yük durumunun **üçünde** ters;  kabin en altta iken halat karşı ağırlıkta | Kabin en altta → halat kabin tarafında ( en olumsuz durum ) |
| ⑱ | **Mil kuvveti ve moment** | Ofis kabulü ( MMO 208/7 - 2.4 ) | `Pm = F1 − Ga` · `M = Gmax·Dt/2` — askı oranı hiç girmez | 2:1'de kasnak tarafındaki büyüklükler **yarıya** iner |
| ⑳ | **Ray σ ve δ'sinin işareti** | **EN 81-50 Ek C.2.1** · **m.5.10.6** | σ ve δ'yı işaretli karşılaştırır;  σm = σx + σy'yi işaretli toplar | σ ve δ **büyüklüktür**;  en olumsuz lif iki eğilmeyi de toplayarak görür |
| ㉑ | **Karşı ağırlık tertibatının taban tepkisi** | **EN 81-20 m.5.2.1.8.4** — tepki ayrı kalem | Karşı ağırlıkta güvenlik tertibatı girdisi yok;  FAR tepkiyi hiç saymaz | Tertibat varsa `k1·gn·Mcwt/n` FAR'a girer |
| ㉒ | **Karşı ağırlık denge oranı q** | Ofis kabulü ( MMO 208/7 - 2.4 ) | `C80 = C75 + C59/2` **çivili** — ofis q'yu değiştirse bile 0,50 | Kütle tek yerden, projenin q'suyla türer |
| ⑲ | **Regülatör çekme kuvveti ve ikinci sınır** | **EN 81-20 m.5.6.2.2.1.1 d)** ve **m.5.6.2.2.1.3 b)** — biri regülatörün **ürettiği** kuvveti, öteki **halattaki** gerginliği sınırlar | İkisini de F′reg ile yapar;  sınıra da **2 × Freg** koyar | `Fçekme = F′reg − Freg` maddeye, `F′reg` emniyet katsayısına girer;  imalatçı kuvveti yoksa **HESAP EKSİK** |

**①'in pratik sonucu:** kitabın kendi örneğinde tahrik kasnağı 240 mm, halat
6,5 mm → oran **36,9**. Kitap 30 eşiğiyle "uygun" der; **standardın 40 eşiğine
göre uygun değildir** ve program bunu kırmızı gösterir. 40'ı sağlamak için
kasnak en az **260 mm** olmalıdır. 30 sayısı aynı standardın *dengeleme halatı
gergi kasnağı* ( m.5.5.6.2 ) ve *regülatör* ( m.5.6.2.2.1.3 ) eşiğidir — askı
halatının değil.

**③ ve ④'ün etkisi** ( kitabın örnek projesinde ):

| | Kitap | Program |
|---|---|---|
| Durum 2 σm | 40,3 N/mm² | **57,4** — Durum 2 belirleyici hâle gelir |
| Flanş σF ( Durum 1 ) | 19,8 N/mm² | **15,0** ( ℓ = 2·b = 34 mm ) |

**⑤'in etkisi.** Standart Rm = 370 ve 520 için iki ω eğrisi verir ve arada
doğrusal ara değer ister; kendi notu, işlenmiş raylarda 440 N/mm² yaygın
olduğu için bunun *"her zaman yapılması"* gerektiğini söyler. Kitabın tek
tablosu yalnız 370 eğrisidir ( 231 değerinin 231'i standardın 370 formülüyle
birebir çıkıyor ) ve ray çeliğinden bağımsız kullanılır:

| λ | Rm 370 | Rm 440 | Rm 520 |
|---|---|---|---|
| 100 | 1,898 | 2,194 **(+16 %)** | 2,533 **(+34 %)** |
| 155 | 4,057 | 5,004 **(+23 %)** | 6,086 **(+50 %)** |
| 250 | 10,554 | 13,017 **(+23 %)** | 15,831 **(+50 %)** |

Burkulma gerilmesi σk doğrudan ω ile çarpıldığı için, 440 ya da 520 çelik
seçildiğinde kitap σk'yı **%19-33 düşük** gösterir.

**⑥'nın etkisi.** EN 81-50'nin çözümlü örneği bunu kanıtlıyor: 1 m/s kabin
hızı ve 2:1 askı için standart μ = 0,083 verir — bu ancak v = 2 m/s ( halat
hızı ) ile çıkar. Kabin hızı kullanmak μ'yü, dolayısıyla e^(f·α) sınırını
büyütür ve tahrik yeteneğini olduğundan iyi gösterir.

**⑬'ün etkisi.** Örnek projede kitap 21.326 N der, doğrusu 18.096 N — ray
başına **3,23 kN ( %18 )**. Bu kalem **fazla hesaplanıyor**. Hatanın yönü
emniyetli olsa da, listede bulunması gereken başka yüklerin ( ör. klips itme
kuvveti Fp ) eksikliğini telafi etmez.

**⑫'nin etkisi.** Kanal şekli açılır listede **seçilebiliyor** ama `f`'yi hiç
değiştirmiyordu — beş şekil de aynı sürtünme çarpanını veriyordu. Standardın
yarım daire kanallar için ayrı bir maddesi vardır:

| Kanal | Doğrusu | Kitabın verdiği | |
|---|---|---|---|
| Altı kesik yarım daire ( β=90° · γ=25° ) | 0,1933 | 0,2053 | **+%6** |
| Düz yarım daire ( β=0 · γ=25° ) | 0,1248 | 0,2053 | **+%65** |
| V kanal | 0,2053 | 0,2053 | fark yok |

İkisi de **emniyetsiz** taraftaydı — tahrik yeteneğini olduğundan iyi
gösteriyordu. Kanal açıları ( V için γ ≥ 35° · yarım daire için γ ≥ 25° ·
β ≤ 105° ) proje bazında bilinemediği için **ofis standardına** konmuştur.

Ayrıca m.5.11.2.3.1.2, sertleştirilmemiş kanalda **alt kesilmenin gerekli**
olduğunu söyler; alt kesilmesiz + sertleştirilmemiş birleşimi seçilirse pafta
uyarı basar.

**⑪'in etkisi.** `a = 0,05 m/s²` girip tahrik hesabını "UYGUN" almak
mümkündü. Küçük bir yavaşlama atalet kuvvetini küçültür, T1/T2 oranını
iyileştirir — emniyetsiz taraf.

**⑩'un etkisi.** Liste **kapalıdır** — içinde olmayan bir yük seçilemez. Yani
1250 ve 1500 kg gibi yaygın asansörlerde program hiç hesap yapamıyordu;
yanlış cevap vermiyordu ama o projeyi çıkaramıyordunuz. Seçenekler artık
tablodan **türetilir** ( iki listenin bir daha ayrışmaması için ) ve teslim
edilen kitabın açılır listesi de genişletilir. 320 kg Çizelge 6'da yoktur;
standardın kendi dipnotu ara yükler için doğrusal ara değer ister ve
300/375 arası **0,953 m²** verir — kitabın 0,97'si **emniyetsiz** taraftaydı,
o yük için standardın izin verdiğinden büyük kabine izin veriyordu.

**⑭'ün etkisi.** 900 mm kapı + 300 mm pervazda kitap girintiye **0,1350 m²**
katıyor, standart ise **0,2700 m²**'nin tamamını ister. Kullanılabilir alanı
küçük göstermek **emniyetsiz** yöndür: Çizelge 6'nın izin verdiğinden büyük bir
kabine izin verilir. Standardın metni ikiye ayırır — girinti derinliği
≤ 100 mm ise **hariç**, > 100 mm ise *"the **total** available area shall be
included"*.

**⑮'in etkisi.** Kitabın koşulu standarda uyan tasarımları reddediyordu ve
**verdiği öğüt sonuca ulaşmıyordu**: `Sf` gereken güvenlik katsayısıdır ve
halat çapını artırmak `Dt/dh`'yi düşürerek onu **büyütür**. Örnek: Dt = 400 mm ·
dh = 8 mm · 8 halat · yarım daire kanal → `Sf = 7,89`, gerçekleşen `S = 32,54`
— hem 7,89'un hem 12'nin çok üstünde, ama pafta "UYGUN DEĞİLDİR" yazıyordu.
`Sf < 12` yaygındır:

| Kanal | Dt/dh = 40 | 50 | 60 |
|---|---|---|---|
| V Kanal | 20,55 | 14,64 | **11,59** |
| Altı Kesik V Kanal | 15,51 | **11,34** | **9,14** |
| Yarım Daire Kanal | **10,40** | **7,89** | **6,53** |

**⑯'nın etkisi.** Ofis sabiti γ = 45° yapıldığında `Nequiv(t)` 12'den **6,5**'e
iner ve gereken `Sf` düşer; kitapta hiçbir şey değişmiyordu. Ters yönde
β = 100° seçildiğinde 5 → **10** çıkar ve `Sf` **büyür**. Üstelik pafta γ = 38°
yazmayı sürdürüyordu — yani teslim edilen belge, hesabın gerçekten kullandığı
sayıyı göstermiyordu. Altı kesik kanallarda kitap bu sütuna γ değil **β**
yazıyor ( 90 ), pafta da onu "γ" diye basıyordu.

**⑰'nin etkisi.** Halat kütlesinin taraf dağılımı dört yük durumunun üçünde
tersti. 20 duraklı · 76 m seyirli · 8 × Ø13 halatlı 1:1 bir tesiste:

| | Kitap | Doğrusu |
|---|---|---|
| Yükleme T1/T2 | 1,23 | **1,79** |
| Sınır e^(f·α) | 1,71 | 1,71 |
| Sonuç | UYGUN | **UYGUN DEĞİL** |

Kısa kuyularda fark ihmal edilebilir; **yüksek binada belirleyici** olur.

**⑱'in etkisi.** 1275 kg · 1,0 m/s · **2:1** · Dt = 240 mm örneğinde kitap
`M = 85,74 kg·m` yazar, tahrik kasnağının gördüğü moment **42,87 kg·m**'dir.
Motor gücünü etkilemez — `N = Gmax·v/(η′·102)` askı oranından bağımsızdır ve
kitapta doğru kurulmuştur. Ama paftadan moment okuyup makine seçen bir okuyucu
iki katı bir sayı görüyordu.

**⑧'in etkisi.** Kitabın 150 mm'si, m.5.2.5.8.2 a) 1)'deki **yatay**
0,15 m sınırının düşey sınır sanılmasından geliyor görünüyor; standardın
Şekil 7'si raya yatay Xₕ ≤ 0,15 m uzaklıktaki karkas parçaları, paten ve
güvenlik tertibatı için **0,10 m** verir ( Xₕ = 0,30 m'de 0,30 m,
Xₕ ≥ 0,50 m'de 0,50 m ). Kabin üstündeki 1200 mm'nin ise standartta
karşılığı yok: m.5.2.5.7.3, ayakta durulabilen alanın üzerindeki serbest
yüksekliği **seçilen sığınma hacminin yüksekliğine** bağlar — çömelmiş
duruşta ( Çizelge 3 ) **1,00 m**. Program bu sınırı artık ayrı bir sabit
olarak değil, doğrudan sığınma hacminden okur.

Ayrıca kitap ölçüleri `>` ile karşılaştırıyordu; standart **"en az"** dediği
için sınıra **eşit** ölçü de uygundur — program `≥` kullanır.

**⑨'un etkisi.** Kitap η'yı makine tipinden bağımsız 0,92 alıyordu; ofisin
**kendi avan tablosu** ise dişlisiz için 0,85, dişli için 0,50 diyor. Aynı
asansör, aynı ofis, iki pafta:

| | mukavemet ( eski ) | avan | mukavemet ( şimdi ) |
|---|---|---|---|
| Dişlisiz 2:1 | 4,81 kW | 5,23 kW | **5,90 kW** |
| Dişli 2:1 | 4,81 kW | 9,80 kW | **11,07 kW** |

Dişli makinede kitap gerekli gücün **yarısından azını** söylüyordu — emniyetsiz.
Örnek projede seçilen motor 4,9 kW: kitap "uygun" diyordu, program artık
**UYGUN DEĞİL** diyor. Mukavemetin avandan bir tık yüksek çıkması normaldir:
mukavemet halat ağırlığını ( Gh ) da dengesiz yüke katar, avan katmaz.

Tablo artık **iki projede tek kaynaktan** okunur ( `motor/ortak/ofis.py` ) —
ayrışmanın sebebi iki yerde iki kopya olmasıydı.

② · ④ · ⑧'de kitap **emniyetli tarafta** ama yanlış — ⑧ standarda uygun bir
projeyi haksız yere reddeder, kuyu boyunu gereksiz büyütür. **③ · ⑤ · ⑥ · ⑦ ·
⑨'da emniyetsiz tarafta** — hesabı olduğundan iyi gösteriyor.

#### Eski kitapta ayrıca bulunanlar

| Bulgu | Ne yapıldı |
|---|---|
| Karşı ağırlık malzemesi açılır listesi **"Döküm"** yazıyor, arama tablosunun anahtarı **"Pik Döküm"** — Excel'de seçilirse **#YOK** | Tablo anahtarı esas alındı |
| NPU **240 · 280 · 300** satırlarında atalet yarıçapı boş — seçilirse **#SAYI/0!** | Program bu seçimi **açık mesajla reddediyor** |
| Seyir mesafesi ve son kat yüksekliği elle giriliyor, durak listesiyle **sessizce çelişebiliyor** | Durak listesi **kaldırıldı**:  iki değer doğrudan girilir, çelişecek ikinci bir kaynak yok |
| `TABLOLAR!U63/U64` ve `X61:Z62` satırları hiçbir hesaba girmiyor | **Ölü artık** — tabloya alınmadı |
| *"Ana Giriş Üstü Durak"* ve *"Makine Tipi"* girdileri hiçbir hesaba girmiyor | Girdi sözleşmesine **alınmadı** |
| `AB38` hücresi "Imin — eylemsizlik momenti" der ama NPU tablosunun **atalet yarıçapı** sütununu okur | Matematiğe göre adlandırıldı — **EN 81-50 m.5.10.3** de λ = Lk/imin, imin = √(I/A) der |

#### Standarda karşı doğrulananlar

Motor yalnız kitaba değil, standardın kendisine karşı da denetlendi — bunların
hepsi **birebir tutuyor**:

- **σperm = Rm / St**, St = 2,25 normal · 1,8 güvenlik tertibatı ( EN 81-20
  Çizelge 15, A5 > %12 ) → 165/205 · 195/244 · 230/288
- **δperm** 5 mm ( güvenlik tertibatlı ray ) · 10 mm ( karşı ağırlık ) — m.5.7.4.6
- **k1** = 2 kaymalı · 3 makaralı ani · 5 ani ( Çizelge 14 ) · **k2** = 1,2
- **ω yöntemi** — EN 81-50 m.5.10.3'ün dört bantlı formülleri; Rm = 370 eğrisi
  kitabın tablosundaki **231 değerin 231'ini** birebir üretiyor ( bu, tablonun
  hangi eğri olduğunu kanıtlar )
- **Fv** = k1·gn·(P+Q)/n + Mg·gn + Fp — EN 81-20 m.5.7.2.3.5
- **σk** = ( Fv + k3·Maux )·ω / A — yardımcı donanım çarpanı **k3** güvenlik
  tertibatı durumunda da k3'tür ( k1 değil );  Çizelge 14 k3'e sayı vermez,
  ofis sabitidir ( varsayılan **2** )
- **Fy** paydası h·n/2, **Fx** paydası h·n — EN 81-50 Ek C.2.1.1
- **Tahrik eşitsizlikleri** — EN 81-50 m.5.11.2: yükleme ve acil frenlemede
  T1/T2 ≤ e^(f·α), kabin/karşı ağırlık bloke olduğunda T1/T2 ≥ e^(f·α)
- **Sf formülü** — EN 81-50 m.5.12.3; standardın çözümlü örneğini
  ( Dt/dr = 40, Nequiv = 7 → Sf ≈ 16 ) üretiyor
- **Nequiv(p)** = ( Dt/Dp )⁴ · ( Nps + 4·Npr ) — EN 81-50 m.5.12.2
- Birleşik gerilmeler σm + (Fv+k3·Maux)/A ve σk + 0,9·σm
- **Halat emniyet katsayısı** 12 ( ≥ 3 halat ) / 16 ( 2 halat ) — m.5.5.2.2
- **Sehim** 0,7·F·L³/(48·E·I), Fy ↔ Ix eşleşmesi
- **Motor gücü** N = Gmax·v/(η′·102);  102 = 1000/gn ( kgf·m/s → kW ),
  Gmax = F1 − Ga cebirsel olarak **Q/2 + Gh** — güç askı oranından
  bağımsızdır, askı yalnız halat boyu ve verim üzerinden girer
- **Makine kaidesi** basit kiriş statiği:  FA = F1(L−X)/L · FB = F1·X/L ·
  Mmax = F1·X(L−X)/L — ΣF ve ΣM dengede;  σe = M/Wx;  burkulmada
  σb = FB·ω/A ( omega yöntemi ), λ = L1/imin yukarı yuvarlanır
- **Sığınma hacimleri** Çizelge 3 / Çizelge 4 tip 2 ( çömelmiş )
  0,50 × 0,70 × 1,00 m · **açıklıklar** m.5.2.5.7.2 ( 0,50 m ) ·
  m.5.2.5.8.2 ( 0,50 · 0,10 · 0,30 m ) · Şekil 7 ( Xₕ ≤ 0,15 m → 0,10 m )
- **0,035·v²** — TS EN 81-20'de açıklığın değil, kabinin **en üst konumunun**
  tanımındadır ( Çizelge 2 ). Program kuyu ölçülerini anma konumundan aldığı
  için terimi sınıra ekler; eşitsizlik cebirsel olarak aynıdır.

#### Standardın METNİNE karşı bağımsız doğrulama

Kaynak Excel'e karşı karşılaştırma *"kitapla aynı mıyız"* der. Ayrı bir soru
daha vardır: *"standartla aynı mıyız"*. Program bunu da her koşuda denetler —
aşağıdaki sayılar **BS EN 81-20:2014** ve **BS EN 81-50:2014**'ün kendi
metninden çıkarılmıştır ve motorun koduna bakılmadan yazılmıştır:

| Standart | Doğrulanan |
|---|---|
| EN 81-20 Çiz.6 · Çiz.8 · m.5.4.2.3.1 | 28 beyan yükünün azami alanı · kişi sayısı = Q/75 · asgari alan ( 20 kişi üstü +0,115 m² kuralı dâhil ) |
| EN 81-20 Çiz.14 | k1 = 2 · 3 · 5 · k2 = 1,2 |
| EN 81-20 Çiz.15 | σperm = Rm/2,25 ve Rm/1,8 |
| EN 81-20 m.5.5.2.1 · m.5.6.2.2.1 · m.5.7.4.6 | Dt/dh ≥ 40 · Dreg/dreg ≥ 30 · Sf ≥ 8 · 300 N · μmax = 0,2 · δperm 5/10 mm |
| EN 81-20 m.5.2.5.7 · m.5.2.5.8 | altı asgari açıklık · sığınma hacimleri |
| EN 81-50 m.5.10.2 · 5.10.3 · 5.10.4 · 5.10.6 | Mm = 3·Fh·l/16 · ω polinomlarının **katsayıları** · σ = σk + 0,9·σm · δ = 0,7·F·l³/(48·E·I) |
| EN 81-50 m.5.10.5 | σF = Fx·(h₁−b−f)·6 / [ c²·( ℓ + 2·(h₁−f) ) ] |
| EN 81-50 Ek C.2.1 | Fx = k1·gn·(Q·xQ+P·xP)/(n·h) → My → σy = My/Wy · Fv = k1·gn·(P+Q)/n + Mg·gn |
| EN 81-50 m.5.12.3 | Sf bağıntısı, standardın çözümlü örneğini üretiyor |

**Eksen adlandırması standardın kendisidir:** Fx → My → Wy ve Fy → Mx → Wx —
yani x yönündeki kuvvet rayı **y ekseni** etrafında eğer. Kaynak kitap bu
ikisini ters adlandırıyordu ( sayı doğru, ad yanlıştı ) ve kendi sehim
satırlarıyla çelişiyordu; paftayı Ek C ile karşılaştıran bir denetçi olmayan
bir hata görüyordu.

#### Hangi baskıya karşı doğrulandı

Hesaplar **EN 81-20:2020 / EN 81-50:2020**'ye uygundur. Doğrulama metin
olarak **2014** baskısından okundu; bu bir eksiklik değildir, çünkü 2020
baskısının **kendi Avrupa önsözü** şunu yazar:

> *"This document supersedes EN 81-20:2014. This document is a revision of
> EN 81-20:2014. Significant changes made are as follows: — All externally
> referenced standards have now been dated. — A new Annex ZA has been
> developed … **No technical changes have been made during this revision.**"*

Aynı cümle EN 81-50:2020'nin önsözünde de vardır. İki ayrı ulusal
uyarlamadan ( İrlanda **I.S. EN 81-20:2020** · Slovenya **SIST EN 81-50:2020**
ve **SIST EN 81-20:2020** ) birebir aynı metinle teyit edildi. Madde
numaraları da değişmemiştir — programın kullandıklarının hepsi iki baskıda
aynı yerdedir:

| Program | 2014 | 2020 |
|---|---|---|
| Kasnak / halat oranı | 5.5.2 | 5.5.2 ✔ |
| Emniyet gerilmeleri · darbe katsayıları | 5.7.2 · 5.7.4 | 5.7.2 · 5.7.4 ✔ |
| Ray hesabı · burkulma · flanş | 5.10 · 5.10.3 · 5.10.5 | aynı ✔ |
| Tahrik · Nequiv · Sf | 5.11.2 · 5.12.2 · 5.12.3 | aynı ✔ |
| Ray / tahrik / Nequiv örnekleri | Ek C · D · E | aynı ✔ |

**Geçerlilik takvimi:** EN 81-20/50:2020 Şubat 2020'de yayımlandı, Temmuz
2021'de AB Resmî Gazetesi'ne girdi; **2014 baskısı 27 Temmuz 2022'de** uygunluk
varsayımını yitirdi. Bugün geçerli olan 2020 baskısıdır — teknik içeriği 2014
ile aynı olduğu için programda değişiklik gerekmedi.

#### ISO 8100 ve 2026 revizyonu

Hesaplar **TS EN 81-20 / EN 81-50**'ye göre yapılır. Aynı kurallar
**ISO 8100-1 / ISO 8100-2:2019** olarak da yayımlanmıştır — bu iki parça
EN 81-20/50:2014'ün **birebir aynısıdır** ( "identical adoption" ), yani
oradan bakmak aynı sayıları verir. ISO 8100-**32** ise trafik planlamasıdır,
mukavemetle ilgisi yoktur.

**EN ISO 8100-1/-2:2026** yayımlandı; **36 aylık** geçiş süresi işliyor, yani
TS EN 81-20/50:2020 bugün hâlâ geçerli. Avrupa Asansör Birliği'nin ( ELA ) 144
sayfalık karşılaştırma belgesine göre programın yaptığı hesaplarda değişen:

| Konu | 2026 revizyonunda |
|---|---|
| **D/d ≥ 40** ( ① ) | **Değişmedi** — ISO 4344 halatlarında yorulma deneyi yapılmadan eski kural aynen geçerli |
| **Halat emniyet katsayısı** | ISO 4344 halatları için **"gereklilikler değişmedi"** ( m.4.5.2.2.2 ) |
| **Ray hesabı** ( Ek C → **Ek B** ) | Bazı burkulma bağıntılarına **ω eklendi**; birleşik gerilme hesabı tamamlandı; **k3·Maux yerine Faux** yazıldı |
| **Tahrik** | ISO 8100-2 m.4.11 + Çizelge 1'e taşındı; klasik çelik halatta *"küçük değişiklikler"* |
| **Sığınma hacimleri** | Çizelge 3'e **diz çökmüş** duruş eklendi; kuyu-eşik boşluğu 0,15 → **0,12 m** |
| **Makine dairesi çalışma yüksekliği** | 2,10 → **2,00 m** |

Yani ⑤ ( ω ) ve ⑧ ( ray hesabındaki k3 ) için yaptığımız düzeltmelerin yönü
2026 revizyonunda da doğrulanıyor; ① ve Sf ise hiç değişmiyor. Yeni sürüm
esas olarak **yeni askı türlerini** ( elastomer kaplı halat, karbon elyaf
kayış ) ve SIL devrelerini getiriyor — programın kapsamı dışında.

### Doğrulama paketi — kendiniz çalıştırabilirsiniz

Program bir **test paketiyle** birlikte gelir. Programa dokunulduğunda hesabın
değişmediğini ( ya da yalnız bilerek değiştiğini ) doğrulamak için:

```bash
python3 dogrulama/calistir.py          # tümü
python3 dogrulama/calistir.py 1 10     # yalnız seçilen testler
```

macOS'ta programın kendi Python'unu kullanmak için `./.venv/bin/python3 dogrulama/calistir.py`.

| Test | Ne yapar |
|---|---|
| **1 · Avan referans taraması** | Trafik ve avan motorunun sonuçlarını, Excel ile doğrulanıp dondurulmuş referansa karşı karşılaştırır. |
| **2 · Kenar durumlar** | Tablo sınırları, yuvarlama kuralları, kapsam dışı girdiler, hata mesajları. |
| **3 · Girdi dayanıklılığı** | Bozuk / boş / uç girdilerin binlerce birleşimi ve tüm API uçları — program çökmemeli. |
| **4 · Çıktı bütünlüğü** | Üretilen PDF'ler açılabiliyor mu, Türkçe karakterler yerinde mi, paketler ve CAD çizimi doğru mu? |
| **5 · Arayüz** | Tarayıcıda tüm sekmeler, canlı hesap, aktarım, indirme düğmeleri, kalıcılık, dar ekran, proje dosyasından geri yükleme. |
| **6 · Proje dosyası geri yükleme** | Formun her alanını değiştirir, projeyi kaydeder, programı sıfırlar, dosyayı yükler;  her alanın ve hesap sonucunun aynen döndüğünü doğrular. |
| **7 · Altın çıktı** | Önceki sürümün tüm çıktısı sıkıştırılmış olarak saklanır; her koşuda satır satır karşılaştırılır. Refactor sırasında **hiçbir sayı sessizce değişemez**. |
| **8 · Mukavemet tabloları** | `motor/uygulama/mukavemet_tablolari.py` içindeki her değeri ofisin kaynak tablolarının dondurulmuş kopyasına karşı doğrular. Tablolar makineyle aktarıldı; bir sütun kayması hiçbir hesap testinde görünmezdi — bu test **aktarmanın kendisini** denetler. |
| **9 · Mukavemet motoru** | Örnek projenin ara değerleri, standart gereği verilen her kararın uygulandığı, standardın metnine karşı bağımsız sayılar, geçersiz girdi yolları ve profil / hız / kanal varyantları. |
| **10 · Mukavemet referans taraması** | **Girdi uzayını** tarar:  152 senaryoda motorun 170 ara değeri ve bölüm hükümleri dondurulmuş referansla karşılaştırılır. |
| **11 · Uygulama projesi** | **Ortak girdi köprüsünü** denetler: her ortak alan tek tek oynatılır ve elektrik sonucunun gerçekten değiştiği doğrulanır. Ayrıca mukavemet sonucunun birlikte koşarken **kirlenmediği** ve hesap → PDF → DXF zincirinin birebir olduğu kanıtlanır. |
| **12 · Dış referans paftaları** | Motoru bizden bağımsız iki programın yayımlanmış paftalarına karşı denetler. |

Test 3, 5 ve 6 **programın açık olmasını**, Test 5 ve 6 ayrıca **Playwright**,
Test 4 ise **pypdf** ister. Eksik olan test **atlanır** — diğerleri yine
çalışır, paket hata vermez. Bunlar programın çalışması için gerekli değildir;
`requirements.txt` içinde isteğe bağlı olarak listelenmiştir:

```
pip install playwright pypdf  &&  playwright install chromium
```

Atlanan bir test "geçti" sayılmaz; özet tablosunda **atlandı** olarak görünür.
Yani eksik bir bağımlılık, doğrulanmamış bir alanı doğrulanmış gibi göstermez.

Tablo-3 (H) ve Tablo-5 (S) için MMO/697'nin kapalı formülleri kullanılır:

```
H = N − Σ(i/N)^P        (i = 1…N−1)
S = N · ( 1 − ((N−1)/N)^P )
```

Bu formüllerin MMO/697'nin basılı tablo değerleriyle farkı en fazla **5×10⁻¹⁴**'tür.
Kapsam tablo sınırlarıyla aynıdır: **P = 6…34 kişi, N = 1…30 kat.**

---

## 7. Hesabın sınırları — dikkat edilecekler

- **N > 30 kat**: MMO/697 Tablo-3/5 en fazla 30 katı kapsar. Program hesabı
  durdurur ve **bölgeli (zoned) trafik hesabı** gerektiğini bildirir.
- **Kapı genişliği**: listedeki yedi genişliğin (700 – 1300 mm) **tamamı
  hesaplanır**. MMO Tablo-4'te 1000 ve 1200 mm, ISO 8100-32 Tablo 6'da 700 mm
  basılı değildir; bu üç değer komşu tablo satırlarından **enterpolasyon /
  dış değerleme** ile türetilir ve paftada kaynağı *"ara değer"* olarak yazılır
  (Tablo-6'daki 1,75 ve 3,00 m/s ile aynı yöntem). Tek istisna: *"Kabin İçi Oto.
  Kat K.Ç."* kapı tipi 1200 ve 1300 mm'de tabloda hiç yoktur — bu ikisinde
  program imalatçı ta/tk değerinin elle girilmesini ister.
- **1,75 ve 3,00 m/s**: Tablo-6'da satır başlığı değildir; tg doğrusal
  enterpolasyonla bulunur ve paftada *"ara değer"* olarak yazılır.
- **15 kişi / 1125 kg**: Tablo-7'de yoktur; MMO/697 s.53-54 örneğinde geçtiği
  için *örnek istisnası* olarak desteklenir.
- **Kamu binaları**: Tablo-2'de hız, Tablo-9'da %k verilmemiştir. Program
  Büro/İş Merkezi değerlerini varsayar ve **her iki varsayımı da paftaya yazar**;
  %k elle değiştirilebilir.
- **Karma binalar, poliklinik, katlı otopark**: Tablo-2 ve/veya Tablo-9'da
  değer yoktur — hız ve/veya k **elle girilmelidir**, gerekçesi paftaya yazılır.
- **Topraklama**: TT sistem, UL = 50 V, IΔn = 300 mA kabulüyle hesaplanır.
  Şebeke TN sistemse bu kontrol ölçütü geçerli değildir. Hesaplanan değer
  **tahminîdir — tesis tamamlandıktan sonra ölçümle doğrulanmalıdır.**
- **L1 (kolon hattı uzunluğu)**: gerçek kablo güzergâhıdır — ana panodan asansör
  panosuna yatay + düşey toplam. **Kuyu yüksekliğine eşit kabul etmeyin,
  plandan ölçün.**
- **Kılavuz ray > 40 m**: konsol klipslerinin itme kuvveti Fp (MMO/697 s.20)
  avan hesabına girmez; uygulama projesinde ray hesabına **girdi** olarak verilir
  (gelişmiş alan, bilinmiyorsa 0).
- **Bodrum durağı (⑪)**: ana giriş altında hizmet verilen durak adedidir.
  MMO/697 s.14 ve s.16, H (Tablo-3) ve S (Tablo-5) büyüklüklerini **ana giriş
  üstündeki** kat adedi N üzerinden tanımlar; yukarı yoğun trafikte tur ana
  giriş katından başlar. Bu yüzden bodrum durağı **H, S ve TR'yi değiştirmez**;
  yalnız (a) Tablo-2 asgari hız seçimindeki durak adedine (N + 1 + Nb) ve
  (b) toplam seyahat mesafesine ((N + Nb) · h) girer. Program bu notu paftaya
  basar. Hem tek hem çoklu sayfada, çokluda ayrıca asansör bazında girilir.
- **Erişilebilirlik**: 630 kg (8 kişi) altındaki kabin ve 800 mm altındaki net
  kapı, TS EN 81-70 / TS 9111 ölçütünü karşılamaz. Program bunu **uyarır** ve
  otomatik öneri sıralamasına almaz; hesabı durdurmaz — karar projecinindir.
- **Trafik ↔ avan tutarlılığı**: avan sekmesi, trafik hesabındaki kapasite,
  hız ve toplam seyahat mesafesiyle karşılaştırılır. Trafikte
  bir şey değişirse avan sekmesi sessizce eski değerde kalmaz — uyarı çıkar.
  Kuyu yüksekliği Hk ile seyahat mesafesi arasındaki pay (kuyu dibi + üst
  boşluk) da makul aralıkta mı diye kontrol edilir.

### Uygulama projesi — mukavemet

- **Standart gereği verilen hesap kararları** 6. bölümdeki tabloda sayılıdır;
  gerekçeleri ekranda bölüm başlığının yanındaki **( ! )** simgesinden
  okunabilir.
- **Ek C'nin şekilleri ( C.1 – C.4 ) okunamadı** — PDF'te görsel olarak
  gömülüler. Geometrik işaret kabulleri madde metninden ve mekanikten
  çıkarıldı. Bunun sonuca etkisi ÖLÇÜLDÜ: eksen yönü kabulü σ ve δ'yı
  **değiştirmiyor** ( ikisi de `|Fx|` ile kurulur ve yük konumu ± ikisinden
  en olumsuzu seçilerek bulunur ). Yöne bağlı tek gerçek nokta konumların
  **birbirine göre** işaretiydi ve o da bulunup düzeltildi ( ㉔ ve ㉜ ).
- **Boş kabinin ağırlık merkezi ( xp ) bir MODELLEME KABULÜDÜR.** TS EN 81-20
  m.5.7.2.3.2 `xp` için *"the mass centre of gravity"* der — yani kabinin
  GERÇEK ağırlık merkezi. Program bunu ölçemez; kabin gövdesini kabin
  merkezinde simetrik, tek kaçıklığı da **kapı + mekanizma kütlesi** kabul
  eder:  `xp = xc − mkapı·( D/2 + pay ) / P`. Pafta bu kabulü satırın
  kaynağında yazar. Kabinde başka büyük bir asimetri varsa ( yan konsollu
  makine, tek yana yığılmış donanım, panoramik cam cephe ) `xp` gerçekten
  sapar ve ray kuvvetleri değişir — böyle bir kabinde ağırlık merkezi
  imalatçıdan alınıp **kapı ağırlığı ve mekanizma payı** o merkezi verecek
  şekilde girilmelidir.
- **Yardımcı donanım darbe katsayısı k3 bir OFİS SABİTİDİR.** EN 81-20
  Çizelge 14 k1 ve k2'nin değerini verir ama k3 için *"the value has to be
  determined by the manufacturer due to the actual installation"* der. Ofisin
  varsayılanı **2**'dir; paftada değeri ve
  "standart sayı vermez" notu birlikte basılır. Tesise özgü bir değer varsa
  ofis sabitlerinden değiştirilmelidir.
- **Paten balatası uzunluğu ( ℓ )** flanş eğilmesine girer ( EN 81-50 m.5.10.5 ).
  Boş bırakılırsa ray tablosundaki balata yarı genişliğinden **2·b** olarak
  türetilir — kare balata kabulüdür, gerilmeyi emniyetli tarafta ( büyük )
  bırakır. **Kesin değer paten imalatçısından alınmalıdır.** Girilen ℓ kabin
  pateninindir;  karşı ağırlığın kaymalı pateninde ℓ her zaman kendi rayından
  2·b olarak türetilir ( kabinin daha uzun balatası ona verilmez ).
- **Sığınma açıklıkları kuyunun çiziminden ölçülür** ( bölüm 11 ile çizimin
  sorunları aynı sayıdır ). Kabinin düşey ölçüleri ( kuyu tavanı kiriş payı 150,
  şase altı 320, kabin tabanı 50 / tavanı 60, paten 100, fren bloğu 270, kabin
  kasnağı 425, revizyon kutusu 500 mm ) **ofis kabulüdür — TS EN 81-20 sayısı
  değildir.** Farklı kabin imalatında Sabitler sekmesinden güncellenmelidir.
  Buna karşılık **asgari açıklıklar** ( kuyu dibinde 0,50 · 0,10 · 0,10 · 0,30 m,
  kuyu üstünde 0,10 · 0,50 · 0,30 m ve sığınma hacimleri ) doğrudan **TS EN 81-20
  m.5.2.5.7 / m.5.2.5.8**'dendir ( `cizim/dusey.py` ) — her satırın karşısında
  madde numarası yazılıdır ve ofis kabulü olarak değiştirilmemelidir. Ray dibi açıklığı, parçanın raya
  **yatay Xₕ ≤ 0,15 m** uzaklıkta olduğu kabulüyle Şekil 7'den 0,10 m alınır;
  daha uzaktaki parçalar için sınır 0,30 m ( Xₕ = 0,30 ) ve 0,50 m
  ( Xₕ ≥ 0,50 ) olur.
- **Sürtünme yükü Gs = 0**, **ST 37 emniyet gerilmesi σem = 130 N/mm²**,
  **yan yatak mesnet payı 335 mm** ofis kabulleridir ( Sabitler sekmesi ). ( **Motor verimi η**
  artık sabit değildir — makine tipinden gelir, bkz. sapma ⑨. )
- **Motor gücü N kararlı rejim gücüdür.** Beyan hızındaki dengesiz yükü
  karşılar; **kalkış ( ivmelenme ) momenti** — kabin, karşı ağırlık, halat,
  kasnak ve rotor ataletleri — hesaba girmez. Motor seçiminde üretici kalkış
  verisi ayrıca kontrol edilmelidir.
- **Karşı ağırlık denge oranı q bir ofis sabitidir, varsayılanı 0,50'dir**
  ( Ga = P + q·Q ;  Sabitler sekmesinden 0,20 – 0,80 arası değiştirilebilir ).
  Karşı ağırlık kütlesi motor, tahrik ve ray hesaplarına aynı yerden girer.
  **Ağırlık tamponu kuvveti bilerek bu kütleyle yazılmaz:** TS EN 81-20
  m.5.2.1.8.6'nın kendi bağıntısı F = 4·gn·( P + q·Q ) kullanılır ve oradaki P,
  standardın sembol listesindeki tanımıyla **gezici kablo payı ve varsa denge
  zinciri dâhil** kabin kütlesidir. Bu yüzden paftada kuyu tabanındaki kütle
  ray bölümündeki karşı ağırlık kütlesinden gezici kablo payı kadar büyüktür
  ( 630 kg'lık örnekte 13,5 kg, %1,4 ) — standardın yazdığı büyük olandır,
  inşaat projesine bildirilen yük emniyetli taraftadır. Paftada iki satır da
  kaynağını yazar;  ekranda ( ! ) altında gerekçesi okunur.
- **Makine kaidesinde ( bölüm 2 ) darbe katsayısı k1 ve σem ofis kabulüdür.**
  TS EN 81-20 makine kaidesi için yük modeli **vermez** — Çizelge 14
  ( k1·k2·k3 ) o standartta açıkça **kılavuz ray** hesabına aittir. Buradaki
  kullanım ödünçtür ve **emniyetli** taraftadır: k1 makinenin kendi ağırlığına
  da uygulanır ve σem = 130, aynı standardın ST 37 için verdiği
  Rm/1,8 = 205,6 N/mm²'nin yaklaşık yarısıdır. Güvenlik tertibatı tipi bu
  bölümü doğrudan büyütür ( k1 = 2 · 3 · 5 → kaide yükü 2,5 kata kadar ).
- **Ray tablosunda bir tutarsızlık işaretlidir.** Atalet yarıçapı tanım
  gereği i = √(I/A)'dır. `125 x 82 x 16` profilinde `iy = 25,20` yazılı, ama aynı
  satırdaki I ve A `26,15` veriyor — %3,6. O satırda A, Ix ve ix birbiriyle
  tutarlıdır; tutmayan tek sayı `iy`'dir. **Değer değiştirilmedi**: küçük iy
  narinliği büyük gösterir, yani burkulma emniyetli tarafta hesaplanır.
  Doğrusu **ISO 7465'ten ya da ray imalatçısının veri sayfasından** teyit
  edilmelidir; o profil seçilince pafta uyarı basar.
- **Burkulma boyu Lk = L1 alınır** ( β = 1,0 — iki ucu mafsallı ). Kolon tek
  ucundan ankastre, öbür ucu serbestse bu kabul narinliği **olduğundan küçük**
  gösterir; öyle bir konstrüksiyonda λ elle iki katına çıkarılmalıdır.
- **Acil frenleme yavaşlaması a**, TS EN 81-20 gereği **en çok 1 gn**'dir; program
  bunu denetler. Tam **a = 1 gn** sınırında kabin tarafındaki halat kuvveti
  sıfırlanır — program tahrik yeteneğini *UYGUN DEĞİL* sayar.
- **Kabin alanı tablosu** EN 81-20 Çizelge 6'nın tablosudur ve avandakinden
  **bilerek ayrıdır** — 320 kg satırı burada vardır, avanın Tablo-11'inde yoktur.
- **Boş kabin ağırlığı ( P ) bir TAHMİNDİR — standardın sayısı değildir.**
  TS EN 81-20 ve TS EN 81-50 P'yi geçtiği dokuz yerin hiçbirinde tablolamaz;
  hep *"the mass of the empty car and components supported by the car"* diye
  **girdi** olarak tanımlar. ISO 4190-1 aynı yük serisi için kabin
  **ölçülerini** verir, kütle vermez. Program boş bırakılan alanı ofisin
  kendi tablosundan doldurur ( `motor/ortak/ofis.py` ) ve paftaya kaynağını
  *"KABUL  ·  ortalama boş kabin kütlesi"* diye basar. **Uygulama projesinde imalatçı verisiyle
  değiştirilmelidir**:  P hatası iki yönde birden emniyetsizdir — 100 kg fark
  ray kuvvetini, kuyu tabanı yükünü ve tampon kuvvetini %5–7 **artırır**
  ( yani küçük almak emniyetsiz ), buna karşılık tahrik oranı T1/T2'yi %3
  **düşürür** ( yani büyük almak tahriki olduğundan iyi gösterir ). Motor
  gücü etkilenmez:  P, Gmax = F1 + Gs − Ga bağıntısında sadeleşir.
- Uygulama projesi **en çok 4 asansör** alır; her asansör kendi kuyusunda,
  kendi girdisiyle hesaplanır ( proje geneli alanlar ortaktır ). Aynı kuyuda
  yan yana asansör ( ortak kuyu ) modellenmez.
- **Elektrik hesapları avan motorunun aynısıdır** ( `motor/avan/avan_hesabi.py` ) — avan
  projesindeki bütün sınırlar burada da geçerlidir: topraklama TT sistem,
  UL = 50 V, IΔn = 300 mA kabulüyle hesaplanır ve **tesis tamamlandıktan sonra
  ölçümle doğrulanmalıdır**; L1 gerçek kablo güzergâhıdır, kuyu yüksekliğine
  eşit kabul edilmemelidir.
- **Motor gücü:** uygulama projesinde paftaya mukavemetin **MMO 208/7** hesabı
  basılır. Avan projesindeki MMO/697 hesabı farklı bir formüldür ( halat
  ağırlığını almaz, palanga verim düşüşü uygular ) ve küçük bir fark verir —
  aynı asansörün iki projesinde iki değer görülmesi normaldir. Kurulu güç
  cetveli her iki tarafta da **seçilen** motor gücünü ( Nsç ) kullanır ve
  cetvele **etiket gücünü** yazar:  kurulu güç tanım gereği tüketicilerin anma
  ( etiket ) güçlerinin toplamıdır ( Elektrik İç Tesisleri Proje Hazırlama
  Yönetmeliği m.5-19 ) ve motorun anma gücü mil gücüdür ( TS EN 60034-1
  m.5.5.3 ).  Kolon hattının akımı ve gerilim düşümü ise motorun **şebekeden
  çektiği** güçle hesaplanır ( Pşeb = Nsç / ηm );  bölüm 6'da ayrı satırdır
  ( P1 = Pşeb + aydınlatma + priz ) ve kesitler ondan seçilir.
- **Çift sarımda sarılma açısı α elle girilir.** Tek sarımda α boş bırakılırsa
  çizimden ( saptırma kasnağının yerinden ) bulunur ve en çok 180°'dir; çift sarımı çizim
  çizmez ( tek geçiş ), halat kasnaktan iki kez geçer ve **iki geçişin toplam
  açısı** ( 180° < α ≤ 360° ) girilmelidir — 180° ve altı bir değer tek sarıma
  ait sayılıp reddedilir. `Nequiv(t)` çift geçişle hesaplanır.
- **Tahrik yeteneğinde dört yük durumu hesaplanır**: yükleme, en altta ve en
  üstte acil frenleme, karşı ağırlığın asılı kalması. TS EN 81-50 m.5.11.2.2.3
  bloke durumunu *"empty car at the **highest and lowest** position"* der;
  program üsttekini kurar. **Kabinin tampona oturduğu** karşı durum ( kaynak
  kitabın da hesaplamadığı ) modellenmez — kuyu dibine girilebiliyorsa bu
  durum ayrıca değerlendirilmelidir.
- **Konsol itme kuvveti Fp girdidir, varsayılanı 0'dır.** TS EN 81-50 Ek C.1.3
  `Fp`'yi *"push through forces of all brackets at one guide rail ( due to normal
  settling of the building or shrinkage of concrete )"* diye tanımlar ve
  C.2.1.2 / C.2.2.2'de Fv'ye ekler; program da öyle ekler. Değeri tesise
  bağlıdır:  betonarme kuyuda oturma / rötre bekleniyorsa konsol imalatçısından
  alınıp girilmelidir.
- **Ray narinliği λ = konsol arası / imin, 250'yi aşamaz** ( imin rayın en
  küçük atalet yarıçapıdır;  paftada ix ve iy birlikte yazılır ). ω tablosu
  ( m.5.10.3 ) o aralıkta tanımlıdır; program aşan girdiyi **izin verilen en
  büyük konsol aralığını söyleyerek** reddeder. `λ < 20` burkulmanın belirleyici
  olmadığı bölgedir, tablonun ilk satırı kullanılır.
- **Grup sigortası makine besleme kablosunu korumalıdır.** `sigorta_sec` kademeyi
  `1,25 × In`'den seçer;  seçilen kademe kablonun önündeki en büyük sigortayı
  aşamaz ( `In ≤ Inmax2` ):  6 mm²'ye kadar Asansör Periyodik Kontrol
  Yönetmeliği EK-5 1.31.13 ( 1,5 → 10 · 2,5 → 20 · 4 → 32 · 6 → 50 A ), üstünde
  kablonun taşıma kapasitesi Iz ( `tablolar.sigorta_siniri` ).  İki tablo 6 mm²'de
  ayrışır ( 50 A · 41 A ):  EK-5 muayenenin ölçütüdür, IEC 60364-4-43'ün daha sıkı
  `In ≤ Iz`'si 6 mm²'ye kadar uygulanmaz.  Kolon hattının önündeki sigorta binanın
  ana panosundadır, program onu seçmez:  kolon hattında yalnız `I ≤ Iz` denetlenir.
- **Regülatörün ikinci kuvvet sınırı imalatçı verisi ister.** TS EN 81-20
  m.5.6.2.2.1.1 d) *"güvenlik tertibatını devreye sokmak için gerekenin iki
  katı"* der; bu kuvvet fren bloğunun **tip inceleme belgesinden** gelir ve
  proje aşamasında çoğu zaman bilinmez. Girilmezse **300 N denetlenir** ve
  ikinci koşul tersinden **şart olarak yazılır**: fren bloğunun devreye girme
  kuvveti en çok `Fçekme / 2` olabilir; takılacak fren bloğunun belgesiyle
  doğrulanır. Girilirse `max( 300 N ; 2 × kuvvet )` aranır. Sınır, regülatörün ÜRETTİĞİ kuvvete uygulanır
  ( `Fçekme = F′reg − Freg` ) — halattaki toplam gerginliğe değil; halatın
  emniyet katsayısı ( ≥ 8 ) ise `F′reg`'e karşı hesaplanır ( m.5.6.2.2.1.3 b ).

---

## 8. Ofis standardını değiştirmek

> **İKİ PROJENİN OFİS STANDARDI AYRIDIR.** Sabitler sekmesi her iki projede de
> vardır ama **içerikleri farklıdır** — avan yaparken uygulamanın kabullerini,
> uygulama yaparken avanınkini görmezsiniz.
>
> Avan **ön tasarımdır**: genel, emniyetli kabullerle çalışır. Uygulama **kesin
> tasarımdır**: elinizde imalatçı verisi vardır. Dişlisiz makine için avanda
> 0,85 kabulü yeterliyken uygulamada makinenin kataloğundaki değer kullanılabilir.
> **İkisinin aynı sayıyı tutma zorunluluğu yoktur.**
>
> Fabrika ayarı ortaktır (`motor/ortak/ofis.py`): ikisi de oradan başlar,
> sonrası her projenin kendi kararıdır. Her değer paftaya **kaynağıyla**
> basıldığı için ayrışırlarsa bilerek ayrışırlar.

### Uygulama projesinin ofis standardı

**45 alan, 6 grup** — `motor/uygulama/uygulama_sabitleri.py`:

| Grup | İçindekiler |
|---|---|
| ① Makine ve motor | dişlisiz / dişli verimi, palanga düşüşü, Gs, q, halat payı, **kanal açıları γ ve β** |
| — | Boş kabin kütlesi tablosu **ekrandan değiştirilmez** ( `motor/ortak/ofis.py` · `GK_TABLOSU` ) — iki proje de aynı tablodan okur |
| ② **Mukavemet kabulleri** | **σem**, **k1** (kaymalı · makaralı · ani), k3, **kabin kapısı ağırlığı** ( katalog: 62 kg ), yan yatak mesnet payı |
| ③ Sığınma payları | kabin gövde yüksekliği, kabin üstü kotu, tavan / etek / ray altı payları |
| ④ Aydınlatma | kabin · kuyu armatürleri, azami aralık, tablo sütunu |
| ⑤ Kurulu güç ve gerilim düşümü | U · κ · εmax · cosφ · priz · kablo tipi · sigorta katsayısı |
| ⑥ Temel topraklama | β · çubuk adedi · karelaj gözü · çubuk boyu · UL · IΔn |

**② özellikle gözden geçirilmelidir.** σem = 130 ve k1 = 2/3/5 bugüne kadar
**kodda gömülüydü**, artık ekranda. TS EN 81-20 makine kaidesi için yük modeli
**vermez** ve Çizelge 14 (k1) o standartta açıkça **kılavuz ray** hesabına
aittir — buradaki kullanım ödünçtür ve emniyetli taraftadır (σem = 130,
standardın ST 37 için verdiği Rm/1,8 = 205,6 N/mm²'nin yaklaşık yarısı).
Kiriş gereğinden kalın çıkıyorsa bakılacak yer burasıdır.

Buradan değiştirdiğinizde **ekrandaki hesap ve PDF paftası birlikte** değişir;
değerler proje dosyasına da yazılır.

**Tablolar sekmesi de ayrıdır.** Uygulamanın 14 tablosu (ray profilleri, NPU
kesitleri, halat ağırlıkları, ω burkulma, kabin alanları, kanal katsayıları …)
bugüne kadar **yalnız motorun içindeydi** — hesaba giriyorlardı ama ekranda
görünmüyorlardı. Tablolar kopyalanmaz; motorun kendi sözlüklerinden okunur, o
yüzden ekrandaki tablo ile hesaba giren tablo ayrışamaz.

### Avan projesinin ofis standardı

**Sabitler / Ofis Standardı** sekmesindeki değerler proje geneli için ortaktır
(palanga, denge faktörü, ray sayısı, flexbil, montör, armatürler, priz, cosφ,
UL, IΔn, çubuk boyu, aydınlatma verimi sütunu). Buradan değiştirdiğinizde hem
ekrandaki hesap hem PDF paftası birlikte değişir.

**Askı oranı (i) artık burada değil, asansörün kendi girdisidir** — avan
sekmesinde makine tipiyle yan yana durur. Bir projede
dişlili ve dişlisiz makine ya da 1:1 ve 2:1 askı birlikte kullanılabildiği için
bu değer, makine verimi η gibi, asansöre özeldir.

**Denge faktörü (q)** ofis standardında kalır (uygulamada hep 0,50); gerekirse
asansör bazında **"Denge faktörü"** bölümünden ezilebilir.

### Verim (η) nasıl kullanılıyor?

| Makine tipi | Askı | η (MMO/697 s.21) | η′ (hesapta kullanılan) |
|---|---|---|---|
| Dişli | 1:1 | 0,50 | **0,50** |
| Dişli | 2:1 | 0,50 | **0,40** |
| Dişlisiz | 1:1 | 0,85 | **0,85** |
| Dişlisiz | 2:1 | 0,85 | **0,75** |

Askı oranı motor gücüne **yalnız verim üzerinden** girer: N = (1−q)·Q·V / (102·η′)
bir *güç* bağıntısıdır ve güç askı oranından bağımsızdır — 2:1 askıda halat hızı
iki katına çıkar, kuvvet yarıya iner, çarpımları değişmez. Askı oranının etkisi
MMO/697 §2.4'teki **Δη = 0,10** verim düşüşüdür ( "palangalı sistemlerde verim %10
az alınacaktır";  kitabın örneği §4.4:  η = 0,5 − 0,1 = 0,4 ).  Paftada ayrı bir
satır olarak görünür:  η′ = η − 0,10.

Avanda girilen η **makine** verimidir ( askı / palanga kaybı hariç ) — kitabın
η'sı.  Palangalı sistemde 0,10'u program kendisi düşer;  kutuya düşülmemiş
değeri girin.  Avan kitaba göre denetlendiği için bu kural kitaptaki gibi
uygulanır.

**Uygulama projesi farklıdır:** orada η imalatçı kataloğunun **toplam sistem
verimi**dir ( askı kaybı içinde ) ve 0,10 düşülmez.  Bu yüzden aynı asansörde
avan, uygulamadan bir kademe büyük motor bulabilir — avan kitabın emniyetli
ön boyutlandırmasıdır, uygulama gerçek makineyle hesaplanır.

Yönetmelik / standart sabitleri (A bölümü) programda **kilitlidir** ve
değiştirilemez.

---

## 9. Klasör yapısı

**Avan projesi ile uygulama projesi her katmanda ayrıdır** — hesap motoru, API
uçları ve arayüz betikleri ayrı dosyalarda. Ortak olan yalnız gerçekten ortak
olan şeyler: adım yapısı, sayı biçimi, çizim yardımcıları ve indirme.

```
AVAN HESAPLAMA PROGRAMI/
├── baslat.command          ← macOS: çift tıklayın
├── baslat.bat              ← Windows: çift tıklayın
├── main.py                 ← sunucu kabuğu:  uygulamayı kurar, uç paketlerini
│                              bağlar, ana sayfa · sağlık
├── requirements.txt
├── OKUBENI.md              ← bu dosya
│
├── engine/                 ← HESAP MOTORLARI  ( arayüzden ve sunucudan bağımsız )
│   ├── ortak/
│   │   ├── steps.py        ← işlem adımı yapısı, Türkçe sayı biçimi
│   │   └── ofis.py         ← FABRİKA AYARI:  iki projenin ofis standardı da
│   │                          buradan başlar ( makine verimleri, palanga düşüşü )
│   ├── avan/               ─────────────────────────────── AVAN PROJESİ
│   │   ├── tablolar.py     ← MMO/697 + ISO + IEC tabloları
│   │   ├── trafik.py       ← trafik hesabı ( tek + çoklu )
│   │   ├── hesap.py        ← avan hesapları
│   │   └── kapak.py        ← kapağın hesaptan dolan asansör bilgileri
│   └── uygulama/           ─────────────────────────── UYGULAMA PROJESİ
│       ├── mukavemet_tablolari.py ← ISO 7465 · TS 12385-5 · EN 81-50
│       ├── mukavemet_girdi.py     ← 71 girdinin sözleşmesi ( TEK KAYNAK )
│       ├── mukavemet.py           ← 10 bölümlük mukavemet hesabı
│       ├── sabitler.py            ← UYGULAMANIN KENDİ OFİS STANDARDI
│       │                             ( 45 alan · avanınkinden ayrı )
│       ├── tablolar_gorunum.py    ← 14 tablonun EKRAN GÖRÜNÜMÜ
│       │                             ( kopya değil — motorun sözlüğünden okur )
│       ├── girdi.py               ← ek girdiler + ORTAK GİRDİ KÖPRÜSÜ
│       └── hesap.py               ← mukavemet + elektrik orkestratörü
│
├── api/                    ← HTTP UÇLARI
│   ├── ortak.py            ← sayı çevirme · belirsiz yazım denetimi ·
│   │                          proje kimliği · dosya adı · indirme yanıtı
│   ├── avan.py             ← trafik · avan · kapak ve çıktıları  (  7 uç )
│   └── uygulama.py         ← mukavemet + elektrik ve çıktıları  (  4 uç )
│
├── exports/                ← BELGE ÜRETİMİ
│   ├── pdf_export.py       ← baskıya hazır PDF  ( trafik · avan · uygulama )
│   ├── dxf_export.py       ← CAD çıktısı  ( ortak )
│   └── kapak_export.py     ← avan proje kapağı
│
│   ( ARAYÜZ depo kökündeki on-yuz/'dadır — React;  program kökte sunar.
│     Eski arayüz static/ 19 Eki'de kaldırıldı. )
│
├── dogrulama/                ← doğrulama paketi
│   ├── calistir.py         ← hepsini çalıştırır
│   ├── test_avan_tarama.py · test_kenar_durum.py · test_dayaniklilik.py
│   ├── test_ciktilar.py
│   ├── test_altin.py       ← altın çıktı kalkanı
│   ├── altin_uret.py       ← altın çıktıyı yeniden üretir
│   ├── test_mukavemet_tablolari.py · test_mukavemet.py
│   ├── test_mukavemet_tarama.py · test_uygulama.py · test_referans_paftalar.py
│   ├── tarama_uret.py      ← TEST 1 / 10 referansını yeniden üretir
│   └── referans_*.json(.gz) ← dondurulmuş referans sonuçlar ve kaynak tablolar
│
├── templates/
│   └── proje_formati.dxf   ← ofisin tip proje formatı ( CAD çıktısı )
└── fonts/                  ← PDF için Türkçe karakter destekli yazı tipi
```

### İki proje neyi paylaşır, neyi paylaşmaz

| Paylaşılan | Niçin |
|---|---|
| `motor/ortak/adimlar.py` | Hesap adımlarının yapısı ve sayı biçimi — iki pafta da aynı dilde konuşsun |
| `pdf_export.py` çizim yardımcıları | İki paftanın aynı programdan çıktığı belli olsun |
| `uclar/uc_ortak.py` | Sayı okuma ve belirsiz yazım denetimi tek yerde kalsın |
| `dxf_export.py` | CAD yerleşimi hesaptan bağımsız |
| **Avanın elektrik motoru** | Uygulama projesindeki aydınlatma · kurulu güç · gerilim düşümü · topraklama, avanın `motor/avan/avan_hesabi.py`'sini **çağırır**. Kopyalanmaz — iki kopya zamanla ayrışır |

| `motor/ortak/ofis.py` | **Fabrika ayarı** — iki projenin ofis standardı da buradan başlar. Ayrı ayrı değiştirilebilirler, ama sıfır noktaları ortaktır |
| **Boş kabin kütlesi tablosu** ( `ofis.py` · `GK_TABLOSU` ) | Aynı asansör iki projede aynı kabin kütlesiyle hesaplansın. İki kopya tutulsaydı biri güncellenir, öteki unutulurdu |

| Paylaşılmayan | Niçin |
|---|---|
| **Ofis standardı** | Avan ön tasarım, uygulama kesin tasarım — kabulleri aynı olmak zorunda değil. Her projenin kendi Sabitler ekranı var |
| **Tablolar** | Mukavemet kendi kaynağından gelir; kabin alanı tablosu bile bilerek ayrıdır. Her projenin kendi Tablolar sekmesi var |
| **Veri kovası** | `avan_program_v1` · `uygulama_program_v1` — biri diğerini görmez, "Tümünü temizle" yalnız kendi projesini siler |
| **Proje dosyası** | `.avan` · `.uygulama` — her biri yalnız kendi alanlarını taşır, yanlış moda yüklenmez |
| Sekme şeridi ve girdi formları | Moda göre ayrılır. Sabitler ve Tablolar sekmeleri ikisinde de vardır ama **içerikleri ayrıdır** |

### Tabloyu ya da formülü değiştirmek
Tablo değerleri `motor/avan/tablolar.py` ve `motor/uygulama/mukavemet_tablolari.py`,
formüller `motor/avan/trafik.py` · `motor/avan/avan_hesabi.py` ·
`motor/uygulama/mukavemet.py` içindedir.  Ekran, PDF ve CAD aynı motordan
beslendiği için tek yerde değişiklik yeterlidir.  Değişiklikten sonra
`python3 dogrulama/calistir.py` hangi sonucun neden değiştiğini söyler;  kasıtlı
bir değişiklikse altın çıktı ( `dogrulama/altin_uret.py` ) ve referans taraması
( `dogrulama/tarama_uret.py` ) farklar gözle incelendikten sonra yeniden üretilir.

---

## 10. Ekibe dağıtım

Klasörün tamamını kopyalayın (ağ sürücüsü, USB veya paylaşılan klasör).
Her bilgisayarda ilk çalıştırmada kendi kurulumunu yapar.

Tek dosyalık `.app` / `.exe` isterseniz PyInstaller ile paketlenebilir:

```bash
./.venv/bin/pip install pyinstaller
./.venv/bin/pyinstaller --onefile --add-data "../on-yuz/dist:on-yuz/dist" \
    --add-data "templates:templates" --add-data "fonts:fonts" \
    --name "Asansor Avan" main.py
```

---

## 11. Sorun giderme

| Belirti | Çözüm |
|---|---|
| Tarayıcı açılmıyor | Adres çubuğuna `http://127.0.0.1:8760` yazın |
| "Port kullanımda" | Program kendiliğinden boş bir porta geçer; adresi açılan pencerede yazar |
| Program iki kez açıldı | İkinci kopya yeni pencere açmaz, var olan sekmeyi öne getirir |
| PDF'de Türkçe karakter bozuk | `fonts/` klasöründeki iki `.ttf` dosyasının yerinde olduğundan emin olun |
| Sonuç "HESAP HATASI" diyor | Kırmızı kutudaki mesaj hangi girdinin eksik/kapsam dışı olduğunu söyler |
| Hesabın doğruluğundan kuşkulandınız | `python3 dogrulama/calistir.py` — doğrulama paketi koşar ( bkz. 6. bölüm ) |

---

*MMO/697, 2. Baskı, Ocak 2020 · TS EN 81-20 · ISO 8100-32:2020 ·
IEEE Std 80 · IEC 60364-5-52 · BYKHY md.4*
