# -*- coding: utf-8 -*-
"""
TASARIM ŞEMASI — asansörün her girdisinin TEK tanımı

Programın bütün girdileri burada, TASARIM SIRASIYLA bir kez tanımlanır:
düzen → kuyu → kabin ve kapı → raylar → karşı ağırlık → askı → makine →
makine dairesi → tamponlar → regülatör → elektrik.  Her alanın etiketi,
birimi, türü, seçenekleri, varsayılanı, formdaki yeri, doğrulama bayrakları
ve NEREDEN GELDİĞİ ( kaynağı ) burada durur;  başka bir dosyada ikinci kez
yazılmaz.

KAYNAK — bir sayı beş yerden birinden gelir.  İki kaynağı olan sayı hatadır:
hesap bir değeri, çizim başka bir değeri kullanır, pafta kendi içinde çelişir.

    GİRDİ    kullanıcının tasarım kararı
    KURAL    boşsa yerleşim kuralından gelir;  girilirse girilen kullanılır
    KATALOG  ürün ölçüsü ya da imalatçı verisi
    ÇİZİM    yerleşimden ölçülür.  Formda kutusu yoktur — yalnız sarılma
             açısı:  çizim açıyı tek bir sayı olarak bulamıyorsa girilir
    HESAP    hesabın kendi türettiği ( karşı ağırlık kütlesi, kuyu boyu … )

SÖZLEŞME — alanın hangi motorun girdisi olduğu:  MUK mukavemet hesabı
( engine/uygulama/mukavemet ), ELK elektrik hesapları ( engine/uygulama/
girdi ), CIZ çizim ( cizim/kopru ).  Motorlar kendi sözleşmelerini buradan
okur ( tasarim.gorunum.sozlesme ):  sözleşmenin biçimi ve sırası onların
beklediğidir, şema yalnız tanımın tek yerde durmasını sağlar.

FORMDA DEĞİL ( formda=False ):  motor değeri bekler ama kullanıcı girmez —
ya çizimden gelir ( saptırma kasnaklarının çapı, kabin tamponu kaidesi ),
ya çizimin tek çizebildiği değerdir ( iki kabin ve iki ağırlık rayı, kabin
ve askı iki rayın ortasında ), ya da hesabın kendisi türetir.  Arayüzden
gelen istekte böyle bir alan olsa da okunmaz ( eski proje dosyaları ).

YERLEŞİM:  "mrl" ya da "daireli" yazan alan yalnız o makine yerleşiminde
hesaba ve çizime girer;  öbüründe ekranda gizlenir ve okunmaz.
"""

from dataclasses import dataclass, replace

from cizim import girdi as CG
from engine.ortak import ofis as OFIS
from engine.uygulama import mukavemet_tablolari as MT

GIRDI, KURAL, KATALOG, CIZIM, HESAP = "GİRDİ", "KURAL", "KATALOG", "ÇİZİM", "HESAP"

#  KARŞI AĞIRLIĞIN GENİŞLİĞİ ile RAYLARININ ARASI birbirinden türer:  iki uçta
#  paten payı ( referans proje:  790 çerçevede DBGW 850 ).  Biri girilmişse
#  öbürü ondan gelir;  ikisi de boşsa genişlik referans uygulama projesinin
#  960'ıdır.  Eskiden genişliğin varsayılanı her zaman 960'tı:  ray arası
#  1.700 girilen projede ( 1022 ) çerçeve ile ray arasında her yanda 370 mm
#  kalıyordu — paten bunu köprüleyemez ( kullanıcı kararı 1 Eki ).
AGIRLIK_PATEN_PAYI = 60.0
AGIRLIK_GENISLIGI_YEDEK = 960.0
KAYNAKLAR = (GIRDI, KURAL, KATALOG, CIZIM, HESAP)
MUK, ELK, CIZ = "mukavemet", "elektrik", "cizim"

#  TS EN 81-50 m.5.11.2.2.2 — hesaba girecek en küçük acil frenleme yavaşlaması.
ACIL_FRENLEME_ASGARI = 0.5


def _s(*d):
    return tuple(d)


@dataclass(frozen=True)
class Alan:
    anahtar: str
    etiket: str
    birim: str
    tur: str  # "sayi" · "secim" · "onay" · "metin" · "hesap"
    secenekler: tuple = None
    varsayilan: object = None
    kaynak: str = GIRDI
    sozlesme: str = MUK
    gelismis: bool = False  # grubun altındaki kapalı "Gelişmiş" bölümünde
    formda: bool = True
    proje_geneli: bool = False  # binaya ait:  bütün asansörlerde tek değer
    yerlesim: str = None  # "mrl" · "daireli":  yalnız bu makine yerleşiminde
    isaretli: bool = False  # negatif olabilir ( ray ekseninden konum )
    tam_sayi: bool = False
    pozitif: bool = False  # sıfır olamaz
    opsiyonel: bool = False  # boş bırakılabilir ( motor türetir ya da atlar )
    bolen: bool = False  # hesapta bölen:  sıfır kabul edilmez
    aci: tuple = None  # ( en az , en çok ) derece
    secenek_metni: dict = None  # açılır listede değerin yerine görünen yazı
    secenek_kosulu: dict = None  # { seçenek : ( yerleşim , sebep ) } — yalnız o yerleşimde
    cizimden: str = ""  # boşsa çizimden gelen değerin kuralı ( ⓘ metnine eklenir )
    bilgi: str = ""  # formdaki ⓘ metni
    grup: str = ""


def A(anahtar, etiket, birim, tur, secenekler, varsayilan, **k):
    return Alan(anahtar, etiket, birim, tur, secenekler, varsayilan, **k)


#  ( grup , alanlar ) — FORMUN SIRASI BUDUR.  Grupların sırası tasarımın
#  sırasıdır:  mühendis önce asansörün düzenine karar verir ( yük, hız,
#  makine yeri, askı, karşı ağırlığın yeri ), sonra kuyuyu ve kabini
#  ölçülendirir, sonra parçaları seçer.
_GRUPLAR = (
    # ═══ ASANSÖR VE DÜZEN ══════════════════════════════════════════════════
    (
        "Asansör ve düzen",
        (
            #  ASANSÖR ADI.  Bir binada dört asansör olabilir ve hepsi ayrı kuyudadır;
            #  paftaları birbirinden ayırt edilebilmeli.  Boş bırakılırsa "1 nolu
            #  asansör" gibi numarayla anılır.
            A(
                "asansor_adi",
                "Asansör adı  ( paftada görünür )",
                "—",
                "metin",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=MUK,
                opsiyonel=True,
                bilgi="Paftanın başlığında ve sekmede görünen ad. Hesaba girmez.",
            ),
            #  ASANSÖR TİPİ.  TS EN 81-20 m.5.7.2.3.6 kapı eşiğine binen kuvveti
            #  asansörün TİPİNE göre verir:  insan asansöründe Fs = 0,4·gn·Q, yük-insan
            #  asansöründe 0,6·gn·Q.  Beyan yüküne bağlı bir eşik ( Q < 2500 kg →
            #  0,4 ) standartta yoktur — 1600 kg bir yük-insan asansörü 0,4 ile
            #  emniyetsiz hesaplanırdı.
            A(
                "asansor_tipi",
                "Asansör tipi",
                "—",
                "secim",
                MT.ASANSOR_TIPLERI,
                MT.ASANSOR_TIPLERI[0],
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "İnsan mı yük-insan mı. Yükleme sırasında eşiğe gelen kuvveti değiştirir: insan "
                    "asansöründe Fs = 0,4·gn·Q, yük-insanda 0,6·gn·Q ( m.5.7.2.3.6 )."
                ),
            ),
            #  SEÇENEKLER TABLODAN TÜRETİLİR.  Elle yazılan ikinci bir liste, kabin
            #  alanı tablosuyla ayrışabilir ( EN 81-20 Çizelge 6'nın bazı yükleri
            #  listede olmaz, o yüklerde hesap yapılamaz ).  Tek kaynak KABIN_ALANI'dır.
            A(
                "beyan_yuku",
                "Beyan yükü",
                "kg",
                "secim",
                tuple(k[0] for k in MT.KABIN_ALANI),
                800,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Q — kabinin taşıyacağı anma yükü. Kullanılabilir kabin alanının üst sınırını ( "
                    "Çizelge 6 ) ve yolcu sayısını belirler."
                ),
            ),
            A(
                "beyan_hizi",
                "Beyan hızı",
                "m/s",
                "secim",
                _s(0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6),
                1,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "v — kabinin anma hızı. Motor gücüne, tampon strokuna ve regülatörün devreye girme "
                    "hızı bandına doğrudan girer."
                ),
            ),
            A(
                "mk_yok",
                "Makine dairesiz  ( MRL )",
                "—",
                "onay",
                None,
                True,
                kaynak=GIRDI,
                sozlesme=ELK,
                proje_geneli=True,
                bilgi=(
                    "Makine dairesi var mı yok mu. Dairesiz ( MRL ) seçilirse tabliye ve makine "
                    "kaidesi kolonu yoktur: kiriş burkulma kontrolü yapılmaz."
                ),
            ),
            #  GÖSTERİM  n : 1'DİR, 1 : n DEĞİL.  Oran HALAT HIZININ KABİN HIZINA
            #  oranıdır;  paydadaki 1 kabindir, baştaki sayı halat / kasnak tarafına
            #  aittir ( 2:1'de halat iki kat hızlı gider, kuvvet yarıya iner ).
            #  Etiket "( 1 : n )" yazıyordu — sektör gösteriminin tersi.  Avan tarafı
            #  zaten doğruydu ( tablolar.ASKI_ORANLARI = {"1:1": 1, "2:1": 2} ).
            A(
                "aski_orani",
                "Askı oranı  ( n : 1 )",
                "—",
                "secim",
                _s(1, 2),
                2,
                kaynak=GIRDI,
                sozlesme=MUK,
                bolen=True,
                secenek_metni={1: "1:1", 2: "2:1"},
                secenek_kosulu={
                    1: ("daireli", "Makine dairesizde 1:1 askı kullanılmaz — çizim yalnız 2:1 çizer.")
                },
                bilgi=(
                    "Halatın kabine kaç kolla bağlandığı. 1:1'de kasnak kabin hızında döner, 2:1'de halat"
                    " iki kat yol alır — kasnağa gelen kuvvet yarıya iner, halat boyu ve halat kütlesi "
                    "iki katına çıkar."
                ),
            ),
            A(
                "aski_duzeni",
                "Askı kasnaklarının yeri  ( 2:1 )",
                "—",
                "secim",
                ("Kabin altı", "Kabin üstü"),
                "Kabin altı",
                kaynak=GIRDI,
                sozlesme=CIZ,
                bilgi=(
                    "2:1 askıda kabin kasnaklarının kabinin altında mı üstünde mi olduğu. 1:1 askıda "
                    "halatlar kabine doğrudan bağlanır, bu seçim kullanılmaz."
                ),
            ),
            #  KARŞI AĞIRLIĞIN YERİ HER PROJEDE SEÇİLİR — Gelişmiş'te değildir.
            #  Yerleşimin en temel kararıdır ve hesabı da etkiler:  ağırlık YANDA
            #  ( Sağ / Sol ) olduğunda rayları kabin raylarına göre 90° dönük monte
            #  edilir, bu yüzden binanın δstr-x sehimi ağırlık rayının Y eksenine,
            #  δstr-y ise X eksenine gelir ( bkz. mukavemet._agirlik_raylari ).
            #  Arkada ise eksenler paraleldir.  Eskiden bu alan "Kabin ve kapı"
            #  grubundaydı ve Gelişmiş'teydi:  ağırlık bölümünün girdisi olduğu
            #  hâlde revizyonda o bölümün grupları arasında görünmüyordu.
            A(
                "agirlik_yeri",
                "Karşı ağırlık yeri",
                "—",
                "secim",
                _s("Sağ", "Sol", "Arka"),
                "Sağ",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Karşı ağırlığın kuyudaki yeri. Yanda ( sağ / sol ) ise rayları kabin raylarına göre "
                    "90° dönük monte edilir ve binanın iki sehim ekseni ağırlık rayında yer değiştirir."
                ),
            ),
        ),
    ),
    # ═══ KUYU VE KATLAR ════════════════════════════════════════════════════
    (
        "Kuyu ve katlar",
        (
            A(
                "kuyu_genisligi",
                "Kuyu genişliği  ( KG )",
                "mm",
                "sayi",
                None,
                2400,
                kaynak=GIRDI,
                sozlesme=ELK,
                bilgi=(
                    "KG — kuyunun plandaki genişliği. Yalnız kuyu aydınlatmasının bölge indeksine girer; "
                    "mukavemet hesabına girmez."
                ),
            ),
            A(
                "kuyu_derinligi",
                "Kuyu derinliği  ( KD )",
                "mm",
                "sayi",
                None,
                1800,
                kaynak=GIRDI,
                sozlesme=CIZ,
                bilgi=(
                    "Kuyunun plandaki iç derinliği:  kapı duvarının iç yüzünden arka duvarın iç yüzüne.  "
                    "Kuyu genişliği ile birlikte kuyu planını kurar."
                ),
            ),
            A(
                "durak_adedi",
                "Durak adedi",
                "adet",
                "sayi",
                None,
                8,
                kaynak=GIRDI,
                sozlesme=CIZ,
                bilgi=(
                    "Kat kapısı sayısı. Kat yükseklikleri boşsa duraklar "
                    "seyir / ( durak − 1 ) aralığıyla dizilir."
                ),
            ),
            A(
                "seyir_mesafesi",
                "Seyir mesafesi",
                "m",
                "sayi",
                None,
                21,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "En alt durak eşiği ile en üst durak eşiği arasındaki düşey mesafe. Kuyu boyu "
                    "değildir — dengesiz halat kütlesi bundan hesaplanır."
                ),
            ),
            A(
                "kat_yukseklikleri",
                "Kat yükseklikleri  ( isteğe bağlı )",
                "mm",
                "metin",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=CIZ,
                opsiyonel=True,
                bilgi=(
                    "En alt duraktan başlayarak ardışık durak aralıklarını noktalı virgülle ayırın "
                    "( örnek: 3400; 3000; 3200 ). Durak adedinden bir eksik sayı girin; "
                    "toplamı seyir mesafesine eşit olmalı. Boşsa katlar eşit dağıtılır."
                ),
            ),
            #  SON KAT YÜKSEKLİĞİ:  en üst durak döşemesinden kuyu tavanına.
            #  4.200 ( kullanıcı kararı, 29 Eyl 2026 ):  sığınma açıklıkları kuyunun
            #  çiziminden ölçülünce 3.750'de 3.300'lük şasenin üst pateni kuyu tavanına
            #  giriyordu — varsayılan asansör açılışta uygun olsun.
            A(
                "son_kat_yuksekligi",
                "Son kat yüksekliği",
                "mm",
                "sayi",
                None,
                4200,
                kaynak=GIRDI,
                sozlesme=MUK,
                pozitif=True,
                bilgi=(
                    "En üst durak eşiğinden kuyu tavanına ( tabliye altına ) kadar olan düşey mesafe. "
                    "Kuyu üst boşluğu ve ray boyu buradan çıkar."
                ),
            ),
            A(
                "kuyu_dibi",
                "Kuyu dibi yüksekliği  ( KY )",
                "mm",
                "sayi",
                None,
                1600,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "KY — en alt durak eşiğinden kuyu tabanına inen DÜŞEY mesafe ( kuyu dibi derinliği )."
                    " Plandaki derinlik değildir. Kuyu dibi sığınma hacmini ve ray boyunu belirler."
                ),
            ),
            #  SIĞINMA HACMİ TİPİ  ( TS EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 ).
            #  Standart üç duruştan BİRİNİ ister;  program bunu bilmiyor, ÇÖMELME
            #  tipini koda çivilemişti ve yatarak tipiyle uygun olan tesislere
            #  "UYGUN DEĞİL" diyordu.  Beyan edilen tip paftaya yazılır.
            A(
                "siginma_tipi_ust",
                "Kabin üstü sığınma hacmi tipi",
                "—",
                "secim",
                MT.SIGINMA_TIPLERI_UST,
                "Çömelme",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Bakım yapan kişinin kabin üstünde hangi duruşta korunacağı. Dik duruş daha büyük bir"
                    " kuyu üst boşluğu ister ( m.5.2.5.7 )."
                ),
            ),
            A(
                "siginma_tipi_dip",
                "Kuyu dibi sığınma hacmi tipi",
                "—",
                "secim",
                MT.SIGINMA_TIPLERI_DIP,
                "Çömelme",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Kuyu dibinde hangi duruşta korunulacağı. Yatarak, çömelme ve dik duruş için standart"
                    " farklı hacimler verir ( m.5.2.5.8 )."
                ),
            ),
            A(
                "kuyu_duvar_kalinligi",
                "Kuyu duvarı kalınlığı",
                "mm",
                "sayi",
                None,
                150,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Kuyunun duvarları ( kalınlığı ayrıca girilmeyenler ), kuyu dibinin ve kuyu "
                    "tavanının döşemesi ( makine dairelide makinenin oturduğu tabliye ) bu kalınlıkta "
                    "çizilir ( referans proje:  150 )."
                ),
            ),
            #  DUVARLAR AYRI AYRI ( kullanıcı isteği 2 Eki ):  LiftDesigner projelerinde
            #  kalınlıklar farklı ( 800 KG:  ön · arka 200, yanlar 250;  4815-6:  arka
            #  250, öbürleri 200 ).  Boş bırakılan duvar ortak kalınlığı alır;  planda
            #  duvarın ölçüsüne tıklanınca yalnız o duvar değişir.
            A(
                "kuyu_duvar_on",
                "Ön duvar kalınlığı  ( kapının duvarı — boşsa kuyu duvarı kalınlığı )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi='Kat kapılarının olduğu duvar.  Boşsa "Kuyu duvarı kalınlığı".',
            ),
            A(
                "kuyu_duvar_arka",
                "Arka duvar kalınlığı  ( boşsa kuyu duvarı kalınlığı )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi='Kapının karşısındaki duvar.  Boşsa "Kuyu duvarı kalınlığı".',
            ),
            A(
                "kuyu_duvar_sol",
                "Sol duvar kalınlığı  ( boşsa kuyu duvarı kalınlığı )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi='Durakta kapıya bakarken soldaki duvar.  Boşsa "Kuyu duvarı kalınlığı".',
            ),
            A(
                "kuyu_duvar_sag",
                "Sağ duvar kalınlığı  ( boşsa kuyu duvarı kalınlığı )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi='Durakta kapıya bakarken sağdaki duvar.  Boşsa "Kuyu duvarı kalınlığı".',
            ),
            A(
                "kuyu_boyu",
                "Kuyu boyu",
                "mm",
                "hesap",
                None,
                None,
                kaynak=HESAP,
                sozlesme=MUK,
                formda=False,
                bilgi="",
            ),
        ),
    ),
    # ═══ KABIN VE KAPI ═════════════════════════════════════════════════════
    (
        "Kabin ve kapı",
        (
            A(
                "kabin_genisligi",
                "Kabin genişliği",
                "mm",
                "sayi",
                None,
                1450,
                kaynak=GIRDI,
                sozlesme=MUK,
                pozitif=True,
                bilgi=(
                    "Kabinin duvardan duvara İÇ genişliği ( rayları birleştiren doğrultu, y ekseni ). "
                    "Kaplama hariç ölçülür."
                ),
            ),
            A(
                "kabin_derinligi",
                "Kabin derinliği",
                "mm",
                "sayi",
                None,
                1350,
                kaynak=GIRDI,
                sozlesme=MUK,
                pozitif=True,
                bilgi="Kabinin kapıdan arka duvara İÇ derinliği ( x ekseni ). Kaplama hariç ölçülür.",
            ),
            A(
                "kat_kapisi_tipi",
                "Kat kapısı tipi",
                "—",
                "secim",
                MT.KAPI_TIPLERI,
                "Teleskopik Sol",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Açılış düzeni ve kanat sayısı ( Teleskopik Sol / Sağ ve Otomatik Merkezi 2 "
                    "kanatlı ). Kanatlar, açılan kanatların durduğu cep ( bir kanat eni + 30 ) ve "
                    "eşik ( 3 kanatlıda 135 ) buradan çizilir;  cep sığmazsa çizim sığan tipi söyler. "
                    "Büyük kapılar 3 ya da 4 kanatlıdır."
                ),
            ),
            A(
                "kapi_genisligi",
                "Kat kapısı genişliği",
                "mm",
                "secim",
                _s(700, 800, 900, 1000, 1100, 1200, 1300, 1400),
                900,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi="Kapının net geçiş genişliği ( kasa iç ölçüsü ).",
            ),
            A(
                "kabin_yana_kaciklik",
                "Kabinin kuyu ortasından sağa kaçıklığı  ( sola − )",
                "mm",
                "sayi",
                None,
                0,
                kaynak=GIRDI,
                sozlesme=CIZ,
                bilgi=(
                    "Kapıya bakana göre kabin ekseninin kuyu genişliğinin ortasından uzaklığı. Karşı "
                    "ağırlık yandaysa kabin çoğunlukla öbür yana kaçar.  Kabin rayları ve kat kapısı "
                    "kabinle birlikte kayar."
                ),
            ),
            #  2.000:  ofisin kabini ( altı LiftDesigner projesinin hepsinde CH 2.000 —
            #  kullanıcı kararı 30 Eyl, 5. adım;  eskiden 2.200 ).
            A(
                "kabin_ic_yuksekligi",
                "Kabin iç yüksekliği",
                "mm",
                "sayi",
                None,
                2000,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi="TS EN 81-20 m.5.4.1 en az 2.000 mm.  Düşey kesitlerde kabin bu yükseklikte çizilir.",
            ),
            A(
                "kapi_yuksekligi",
                "Kat kapısı yüksekliği",
                "mm",
                "sayi",
                None,
                2000,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi="Kapının net geçiş yüksekliği;  TS EN 81-20 m.5.3.1.1 en az 2.000 mm.",
            ),
            A(
                "kapi_montaji",
                "Kat kapısının montajı",
                "—",
                "secim",
                tuple(CG.KAPI_MONTAJLARI),
                "Kuyu içine",
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Duvar boşluğuna:  kasa duvarın boşluğunda, eşik kuyuya taşar.  Kuyu içine:  kapı "
                    "ünitesi duvarın iç yüzüne monte ( referans proje ).  Kapı hattının ve kabinin "
                    "kuyudaki yeri buna göre değişir."
                ),
            ),
            A(
                "esik_arasi",
                "Kabin eşiği – kat eşiği arası",
                "mm",
                "sayi",
                None,
                30,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "TS EN 81-20 m.5.3.4.1:  en çok 35 mm ( referans proje:  30 ).  Kabinin ön yüzü kapı "
                    "hattından bu açıklık + kabin eşiği derinliği kadar geridedir."
                ),
            ),
            A(
                "kapi_kaciklik",
                "Kat kapısının kabin ekseninden sağa kaçıklığı",
                "mm",
                "sayi",
                None,
                0,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi="Kapı boşluğunun ekseni kabinin ekseninde değilse ( sola − ).",
            ),
            #  BOŞ BIRAKILIRSA OFİS TABLOSUNDAN DOLAR  ( engine/ortak/ofis.py ).
            #  Standartlarda böyle bir çizelge yoktur — TS EN 81-20 / 81-50 kabin
            #  kütlesini ( P ) hep GİRDİ olarak tanımlar;  tablo ofisin kendi
            #  imalatçı deneyimidir ve avan tarafında da aynı yerden okunur.
            #  VARSAYILANI 700'DÜR:  örnek projenin değeri ve doğrulama testlerinin
            #  dayanağı odur.  Beyan yükü değiştirildiğinde arayüz alanı tablodan
            #  günceller.
            A(
                "kabin_agirligi",
                "Kabin ağırlığı",
                "kg",
                "sayi",
                None,
                700,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bolen=True,
                bilgi=(
                    "P — kabinin BOŞ ağırlığı ( iskelet, döşeme, duvarlar, kapı ). Gezici kablo ve denge "
                    "zinciri buna dâhil değildir; onları program ayrıca ekler."
                ),
            ),
            A(
                "uzun_pervaz",
                "Uzun pervaz",
                "mm",
                "sayi",
                None,
                90,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Kapı kasası dikmeleri arasındaki GİRİNTİNİN derinliği. 100 mm'ye kadar kabin alanına"
                    " hiç katılmaz, 100 mm'yi aşarsa girintinin tamamı alana eklenir ( m.5.4.2.1.3 )."
                ),
            ),
            #  BOŞ KABİNİN AĞIRLIK MERKEZİ ( P )  —  Ek C.1.2'nin xp · yp'si.
            #  Boş bırakılırsa TÜRETİLİR:  gövde kabin merkezinde, kapı ( ofis
            #  standardındaki ağırlığıyla ) kapı tarafında, gezici kablo ve denge
            #  zinciri kabin merkezinde kabul edilir ve yp = yc olur ( bkz.
            #  mukavemet._kabin_raylari ).  İmalatçı ağırlık merkezini veriyorsa buraya
            #  girilir;  ray ekseninden ölçülür ve P'nin TAMAMINA uygulanır ( kapı,
            #  gezici kablo, zincir dahil — m.5.7.2.3.2 ).  Referans proje bu iki değeri
            #  doğrudan sorar ( Xp · Yp );  türetme onları temsil edemiyordu — örnek
            #  projesinde xp = +250 mm iken kabin merkezi −140 mm'dedir.
            A(
                "kabin_agirlik_merkezi_x",
                "Boş kabinin ağırlık merkezi x  ( xp — boşsa türetilir )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                isaretli=True,
                opsiyonel=True,
                bilgi=(
                    "xp — BOŞ KABİN KÜTLESİNİN ağırlık merkezi, ray ekseninden ölçülür ( kabin "
                    "merkezinden değil ). Boş bırakılırsa gövde + kapı dağılımından türetilir; imalatçı "
                    "değer veriyorsa onu girin."
                ),
            ),
            A(
                "kabin_agirlik_merkezi_y",
                "Boş kabinin ağırlık merkezi y  ( yp — boşsa türetilir )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                isaretli=True,
                opsiyonel=True,
                bilgi=(
                    "yp — boş kabin kütlesinin ağırlık merkezi, rayları birleştiren doğrultuda ve ray "
                    "ekseninden. Boşsa kabin merkezinin kaçıklığına ( yc ) eşit alınır."
                ),
            ),
            #  Kabin kapısı ağırlığı burada SORULMAZ — ofis standardıdır
            #  ( engine/uygulama/sabitler.py · kabin_kapisi_agirligi ).
            A(
                "kapi_mekanizma_payi",
                "Kapı mekanizma ağ. mrk. payı",
                "mm",
                "sayi",
                None,
                50,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Kapı ve mekanizmasının ağırlık merkezinin, kabin ön yüzünden ne kadar ileride "
                    "olduğu. Boş kabinin ağırlık merkezi türetilirken kullanılır."
                ),
            ),
            A(
                "kabin_kaciklik",
                "Kabin merkezinin y ekseninde kaçıklığı",
                "mm",
                "sayi",
                None,
                0,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                isaretli=True,
                bilgi=(
                    "yc — KABİN GÖVDESİNİN merkezi, iki rayı birleştiren doğrultuda ray ekseninden ne "
                    "kadar kaçık. Kabin rayların tam ortasındaysa 0 girin. Bu, ağırlığın NEREDE "
                    "DURDUĞUDUR."
                ),
            ),
            #  YERLEŞİMİN ÖLÇÜLERİ ( cizim/olculer.py ):  hesap bunları eskiden kendi
            #  formülüyle tahmin ediyordu;  program çizimin kurduğu yerleşimden alır.
            #  Boşsa ( motor doğrudan çağrılınca ) hesabın eski yaklaşığı kullanılır.
            A(
                "kabin_merkezi_x",
                "Kabin merkezinin ray eksenine uzaklığı  ( xc )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                isaretli=True,
                opsiyonel=True,
                bilgi=(
                    "xc — kabinin iç tabanının ortası ile kabin ray ekseni arası ( arkaya + ). Çizim "
                    "kabini eşik arası, kabin eşiği ve ray – kapı arasıyla yerleştirir;  hesap eskiden "
                    "derinlik / 2 + 130 − RK diye tahmin ediyordu."
                ),
            ),
            A(
                "esik_x",
                "Kabin eşiği ortasının ray eksenine uzaklığı  ( xi )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                isaretli=True,
                opsiyonel=True,
                bilgi=(
                    "xi — yükleme sırasında eşik kuvvetinin noktası:  kabin girişinin eşiğinin ortası "
                    "( m.5.7.2.3.6 ). Hesap eskiden kat eşiğinin kenarını ( −RK ) alıyordu."
                ),
            ),
        ),
    ),
    # ═══ RAYLAR VE PATENLER ════════════════════════════════════════════════
    (
        "Raylar ve patenler",
        (
            #  KUYU DERİNLİĞİ ( KD ) ve AĞIRLIK RAY MERKEZİ - DUVAR SORULMAZ.  İkisi
            #  yalnız arka ağırlıkta halat arasını ( KD − RK − ray-duvar ) türetmek
            #  için vardı;  o türetme α doğrudan beyan edilince kalktı ( bkz.
            #  "halat_arasi" notu ).  Sonra hiçbir hesaba ve paftaya girmediler —
            #  yalnız artık türetilmeyen o sayının pozitifliğini denetleyen bir
            #  kontrolde okunuyorlardı.
            A(
                "ray_kapi_arasi",
                "Ray - kapı arası  ( RK )",
                "mm",
                "sayi",
                None,
                650,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "RK — kılavuz ray ekseninden kat kapısı düzlemine olan yatay mesafe. Kabin merkezinin"
                    " x kaçıklığı bundan türetilir: ray kabin ortasından geçmiyorsa ray kuvveti büyür."
                ),
            ),
            A(
                "kabin_ray_profili",
                "Kabin rayı profili",
                "—",
                "secim",
                MT.RAY_PROFILLERI,
                "89 x 62 x 15,88",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Kabin kılavuz rayının T profili ( TS ISO 7465 ). Kesit değerleri ( Wx, Wy, Ix, Iy, A"
                    " ) buradan gelir."
                ),
            ),
            A(
                "agirlik_ray_profili",
                "Ağırlık rayı profili",
                "—",
                "secim",
                MT.RAY_PROFILLERI,
                "50 x 50 x 5",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Karşı ağırlık kılavuz rayının profili. Ağırlıkta güvenlik tertibatı yoksa genelde "
                    "kabininkinden küçük seçilir."
                ),
            ),
            A(
                "kabin_konsol_arasi",
                "Kabin rayı konsollar arası en uzun mesafe",
                "mm",
                "sayi",
                None,
                3000,
                kaynak=GIRDI,
                sozlesme=MUK,
                pozitif=True,
                bilgi=(
                    "İki ray konsolu arasındaki EN UZUN düşey mesafe. Gerilme bu mesafeyle doğru, sehim "
                    "ise KÜBÜYLE orantılıdır — iki katına çıkarsa sehim sekiz katına çıkar."
                ),
            ),
            A(
                "agirlik_konsol_arasi",
                "Ağırlık rayı konsollar arası en uzun mesafe",
                "mm",
                "sayi",
                None,
                3000,
                kaynak=GIRDI,
                sozlesme=MUK,
                pozitif=True,
                bilgi="Karşı ağırlık rayında iki konsol arasındaki en uzun düşey mesafe.",
            ),
            A(
                "guvenlik_tertibati",
                "Güvenlik tertibatı ( fren bloğu ) tipi",
                "—",
                "secim",
                MT.DARBE_TIPLERI_ADLARI,
                "Kaymalı",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Fren bloğunun tipi. Darbe katsayısını belirler ( kaymalı 2 · ani frenlemeli makaralı"
                    " 3 · ani frenlemeli 5 ) — ray kuvvetlerini doğrudan iki buçuk katına kadar büyütür."
                ),
            ),
            A(
                "kabin_ray_arasi",
                "Kabin rayları arası  ( DBG — boşsa kabin genişliği + 200 )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "İki kabin rayının birbirine bakan uçları arası.  Kabin şasesi bu aralığa sığmalıdır "
                    "( referans proje:  1.350 mm kabinde 1.550 )."
                ),
            ),
            #  "Ofis verimi η toplam sistem verimidir" ANAHTARI KALDIRILDI.
            #  η artık HER ZAMAN toplam sistem verimidir ( askı kaybı içinde ) —
            #  seçilecek bir şey kalmadı.  Bkz. engine/ortak/ofis.py, "PALANGA VERİM
            #  DÜŞÜŞÜ KALDIRILDI".  Eski projelerin JSON'unda kalan toplam_verim
            #  anahtarı yok sayılır, geri yükleme bozulmaz.
            #  PATEN ARASI h  —  ray kuvvetinin PAYDASIDIR ( Fx = … / ( n · h ) ) ve
            #  kuyudaki yığına da girer ( halat boyu, Ç.2 üst açıklığı ).
            #  Kabin:  2.660 — ofisin kabini ( kullanıcı kararı 30 Eyl, 5. adım;
            #  8 Eki düzeltmesi ):  LiftDesigner'ın ön kesitlerinde ( K431 · 4815-6 ·
            #  1022 ) 2.000'lik kabinin patenleri kirişlerin DIŞINDA, merkezleri −270
            #  ve 2.390.  30 Eyl'de kirişler paten sanılıp 2.420 ( −150 / 2.270 )
            #  alınmıştı.  Has Asansör'ün kabin şasesi kılavuzunda ( Şekil 1 ) üst
            #  patenler üst kirişin altında, aralık toplam kabin yüksekliğinin
            #  200 – 400 mm fazlası.  Ofis Excel'i makine daireli 3.000 · MRL 3.300,
            #  referans proje 3.300, new block 3.200 kullanıyordu:  büyük h ray
            #  kuvvetini küçültür ( emniyetsiz yön ).  Eskiden 3.400, sonra 3.300.
            #  Karşı ağırlık:  çerçeve boyu DOLGU MALZEMESİNE bağlıdır.  Gerçek
            #  projeler:  referans proje 1.300 kg → 1.500 mm ( pik döküm ile tutarlı ) ·
            #  new block 1.838 kg → 3.200 mm.  Varsayılan malzeme BARİT:  Türk
            #  piyasasındaki blok 960 × 155 × 120 mm, 50 – 70 kg;  1.200 kg için
            #  dolgu 2.160 – 2.880 mm, travers payıyla ~3.000.  Pik dökümde ~1.500
            #  elle girilir.
            A(
                "kabin_paten_arasi",
                "Kabin paten arası",
                "mm",
                "sayi",
                None,
                2660,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                pozitif=True,
                bolen=True,
                bilgi=(
                    "h — kabinin üst ve alt patenlerinin MERKEZLERİ arasındaki düşey mesafe. Devirici "
                    "momentin kolu budur: büyüdükçe raya gelen yatay kuvvet küçülür. Patenler şasenin "
                    "kirişlerinin dışındadır ( üst paten üst kirişin üstünde )."
                ),
            ),
            A(
                "ray_celigi_rm",
                "Ray çeliği Rm",
                "N/mm²",
                "secim",
                MT.RAY_CELIKLERI,
                370,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Ray çeliğinin çekme dayanımı. İzin verilen gerilme σperm = Rm / St buradan "
                    "hesaplanır ( Çizelge 15 )."
                ),
            ),
            #  TS EN 81-50 m.5.10.5 / Ek C.2.1.4 flanş eğilmesi için İKİ formül verir:
            #  makaralı patende 1,85·Fx/c² , kaymalı patende balata boyuna bağlı olan.
            #  PATEN TİPİ RAY BAŞINADIR.  Kabin ve karşı ağırlık patenleri ayrı
            #  seçilir:  kabinde kaymalı, karşı ağırlıkta makaralı paten yaygın bir
            #  düzendir ve tek seçimle girilemiyordu — karşı ağırlık rayının flanş
            #  gerilmesi yanlış formülle hesaplanıyordu.
            A(
                "paten_tipi",
                "Kabin paten tipi",
                "—",
                "secim",
                _s("Kaymalı", "Makaralı"),
                "Kaymalı",
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Kabin patenlerinin cinsi. Rayın boyun ( flanş ) eğilmesi makaralı ve kaymalı patende"
                    " FARKLI formülle hesaplanır."
                ),
            ),
            #  TS EN 81-50 m.5.10.5 flanş eğilmesindeki ℓ ( KABİN paten balatasının
            #  uzunluğu ).  Boş bırakılırsa ray tablosundaki balata yarı genişliğinden
            #  türetilir.  Karşı ağırlığın kaymalı pateni bu değeri KULLANMAZ:  iki
            #  patenin balatası aynı parça değildir;  onun ℓ'si kendi rayından
            #  türetilir ( bkz. mukavemet._balata_boyu ).
            A(
                "paten_balata_boyu",
                "Kabin paten balatası uzunluğu  ( ℓ )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "ℓ — kaymalı patenin balatasının ray boyunca uzunluğu. Boşsa kareye yakın bir balata "
                    "kabul edilir. Makaralı patende kullanılmaz."
                ),
            ),
            A(
                "agirlik_paten_tipi",
                "Karşı ağırlık paten tipi",
                "—",
                "secim",
                _s("Kaymalı", "Makaralı"),
                "Kaymalı",
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Karşı ağırlık patenlerinin cinsi. Kabinden ayrı seçilir — kabinde kaymalı, ağırlıkta"
                    " makaralı yaygın bir düzendir."
                ),
            ),
            #  Ek C.2.1.2 / C.2.2.2 / C.2.3.2:  Fv = … + Fp.  Fp, bir raydaki bütün
            #  konsol klipslerinin itme kuvvetidir ( binanın oturması, betonun
            #  büzülmesi ).  Varsayılan 0, değeri tesise bağlıdır.
            A(
                "klips_itme_kuvveti",
                "Fp ( konsol klipslerinin itme kuvveti )",
                "N",
                "sayi",
                None,
                0,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Fp — bir raydaki bütün konsol klipslerinin, betonun büzülmesi ya da binanın oturması"
                    " yüzünden uyguladığı itme kuvveti. Bilinmiyorsa 0 bırakılır."
                ),
            ),
            #  Ek C.2.1.5 / C.2.2.5 / C.2.3.5:  δ = 0,7·F·l³/(48·E·I) + δstr.
            #  δstr binanın kendi sehimidir;  varsayılan 0.
            A(
                "yapi_sehim_x",
                "δstr-x ( bina yapısının x sehimi )",
                "mm",
                "sayi",
                None,
                0,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "δstr-x — BİNA yapısının kendi sehimi ( rayın değil ). Rayın sehimine EKLENİR ve aynı"
                    " sınırla karşılaştırılır."
                ),
            ),
            A(
                "yapi_sehim_y",
                "δstr-y ( bina yapısının y sehimi )",
                "mm",
                "sayi",
                None,
                0,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "δstr-y — bina yapısının öbür eksendeki sehimi. Karşı ağırlık yanda ise rayları 90° "
                    "dönük olduğu için bu iki eksen ağırlık rayında yer değiştirir."
                ),
            ),
            A(
                "kabin_ray_sayisi",
                "Kabin rayı sayısı",
                "adet",
                "sayi",
                None,
                2,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                tam_sayi=True,
                bolen=True,
                bilgi=(
                    "Kabini kılavuzlayan ray sayısı. Kuvvet raylara eşit dağıtılır; dört rayda bir raya "
                    "düşen kuvvet yarıya iner."
                ),
            ),
            A(
                "agirlik_ray_sayisi",
                "Ağırlık rayı sayısı",
                "adet",
                "sayi",
                None,
                2,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                tam_sayi=True,
                bolen=True,
                bilgi="Karşı ağırlığı kılavuzlayan ray sayısı.",
            ),
            A(
                "kabin_ray_boyu",
                "Kabin rayı boyu",
                "m",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi=(
                    "En uzun kabin rayı:  kuyu tabanından üst ucuna ( rayın kütlesi ray ve kuyu tabanı "
                    "hesaplarına girer )."
                ),
            ),
            A(
                "agirlik_ray_boyu",
                "Ağırlık rayı boyu",
                "m",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi="En uzun karşı ağırlık rayı:  kuyu tabanından üst ucuna.",
            ),
        ),
    ),
    # ═══ KARŞI AĞIRLIK ═════════════════════════════════════════════════════
    (
        "Karşı ağırlık",
        (
            #  AĞIRLIK RAY ARASI SORULMAZ.  Mukavemet hesabına girmiyordu ( standartta
            #  ray arası → genişlik diye bir bağıntı yoktur ) ve paftada yalnız
            #  "hesaba girmez" notlu bir bilgi satırıydı;  CAD çizimi de kullanmıyordu.
            #  Ölçü kuyu yerleşim çiziminde durur.
            #  TS EN 81-20 m.5.6.1:  karşı ağırlıkta güvenlik tertibatı, kuyunun
            #  altındaki hacme girilebiliyorsa ZORUNLUDUR.  Varsa ağırlık rayı
            #  yalnız C.2.2'ye ( normal işletme ) değil TS EN 81-50 Ek C.2.1'e göre de
            #  ( k1 darbe katsayısıyla ) hesaplanmalıdır.
            A(
                "agirlik_guvenlik_tertibati",
                "Karşı ağırlıkta güvenlik tertibatı",
                "—",
                "secim",
                ("Yok",) + MT.DARBE_TIPLERI_ADLARI,
                "Yok",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Karşı ağırlıkta fren bloğu var mı. Kuyunun altındaki hacme girilebiliyorsa "
                    "ZORUNLUDUR ( m.5.6.1 ). Varsa ağırlık rayı ayrıca darbe katsayısıyla hesaplanır ve "
                    "izin verilen sehim 10 mm'den 5 mm'ye iner."
                ),
            ),
            #  KARŞI AĞIRLIĞIN KENDİ İKİ ÖLÇÜSÜ  —  TS EN 81-50 Ek C.2.2'nin Gx · Gy
            #  Eksantriklikler bunlardan çıkar:  Dxa = %10 × derinlik ( Gx ),
            #  Dya = %5 × genişlik ( Gy ).  Standardı izleyen ray hesabı kılavuzu da
            #  ikisini VERİ olarak alır ( "Gx = 130 mm, Gy = 960 mm Counterweight
            #  dimensions" ), referans uygulama projesi de doğrudan sorar.
            #
            #  ESKİDEN TÜRETİLİYORLARDI ve ikisi de yanlıştı:  genişlik ray arasından
            #  ( üç değere kilitli açılır liste ), derinlik malzemeden.  Ölçü ne ray
            #  arasının ne malzemenin özelliğidir — imal edilen ÇERÇEVENİN özelliğidir.
            #  Program kabin tarafında zaten böyle yapıyor ( kabin_genisligi ·
            #  kabin_derinligi ).
            A(
                "agirlik_genisligi",
                "Karşı ağırlık genişliği  ( Gy — boşsa DBGW − 60 )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Gy — karşı ağırlık çerçevesinin genişliği. Kütlenin kaçıklığı bunun %5'i kabul "
                    "edilir ( m.5.7.2.3.3 ).  Boşsa ağırlık rayları arasından 60 eksik ( iki uçta "
                    "paten payı );  o da boşsa 960 mm."
                ),
            ),
            #  155:  standart barit bloğunun derinliği ( 960 × 155 × 120 mm, 50 kg —
            #  karar 11;  eskiden 150 ve dolgu varsayılan asansörde sığmıyordu ).
            A(
                "agirlik_derinligi",
                "Karşı ağırlık derinliği  ( Gx )",
                "mm",
                "sayi",
                None,
                155,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Gx — karşı ağırlık çerçevesinin derinliği. Kütlenin kaçıklığı bunun %10'u kabul edilir."
                ),
            ),
            #  3.300 ( kullanıcı kararı 30 Eyl — karar 11 ):  formun varsayılan
            #  asansöründe ( 800 kg, tablodan 800 kg kabin → karşı ağırlık 1.200 kg,
            #  2:1 ) 24 standart barit bloğu × 120 = 2.880 mm dolgu;  3.000'lik
            #  çerçevede ağırlık kasnağının altına 2.680 kalıyordu.  Ağır asansörde
            #  hesap gereken paten arasını söyler.
            #  8 Eki:  patenler çerçevenin DIŞINDA ( LiftDesigner 1022:  2.000'lik
            #  çerçeve, 100'lük patenler üstte ve altta ) — çerçeve paten arasından
            #  bir paten boyu kısa.  Kullanıcının 30 Eyl'de seçtiği 3.300'lük çerçeve
            #  ( varsayılan asansörün barit dolgusu 2.880 sığsın diye ) paten arası
            #  3.400 demektir;  eskiden paten arası = çerçeve sayılıyordu.
            A(
                "agirlik_paten_arasi",
                "Ağırlık paten arası",
                "mm",
                "sayi",
                None,
                3400,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                pozitif=True,
                bolen=True,
                bilgi=(
                    "Karşı ağırlığın üst ve alt patenlerinin MERKEZLERİ arasındaki düşey mesafe. "
                    "Patenler çerçevenin üstünde ve altındadır:  çerçeve bundan bir paten boyu kısadır."
                ),
            ),
            #  DOLGUYA KALAN YÜKSEKLİK ( karar 11 ):  karşı ağırlık çerçevesinde
            #  alt kirişin üstünden üst kirişin — 2:1'de ağırlık kasnağının — altına.
            #  Çizimden gelir;  hesap dolgunun sığdığını bununla denetler.
            A(
                "agirlik_dolgu_yuksekligi",
                "Karşı ağırlık çerçevesinde dolguya kalan yükseklik",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi=(
                    "Çerçevenin ( paten arası ) alt kirişinden üst kirişine — 2:1'de ağırlık kasnağının "
                    "altına — dolgu blokları için kalan yükseklik."
                ),
            ),
            A(
                "agirlik_malzemesi",
                "Karşı ağırlık malzemesi",
                "—",
                "secim",
                MT.AGIRLIK_MALZEMELERI,
                "Barit",
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Ağırlık bloklarının malzemesi. Seçim yalnız derinlik kutusunun başlangıç değerini "
                    "doldurur; hesap kutudaki sayıyı okur."
                ),
            ),
            A(
                "agirlik_ray_arasi",
                "Ağırlık rayları arası  ( DBGW — boşsa Gy + 60 )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "İki karşı ağırlık rayının birbirine bakan uçları arası.  Ağırlık çerçevesi ( Gy ) bu"
                    " aralıkta durur, iki uçta paten payı kalır ( referans proje:  790 çerçevede 850 ).  "
                    "Makine dairesizde makine kirişleri bu raylara oturuyorsa kirişlerin mesnet aralığı ("
                    " yan yatak boyu ) da budur."
                ),
            ),
            A(
                "agirlik_ray_duvar",
                "Karşı ağırlık ekseni – duvar arası  ( boşsa Gx / 2 + 50 )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Karşı ağırlığın ekseninin yakın duvara uzaklığı:  yandaysa yan duvara, arkadaysa "
                    "arka duvara."
                ),
            ),
            A(
                "agirlik_eksen_kaciklik",
                "Karşı ağırlık ekseninin kabin rayından kaçıklığı  ( arkaya + )",
                "mm",
                "sayi",
                None,
                0,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Yandaki karşı ağırlığın ekseni kabin ray ekseninin önünde ( − ) ya da arkasında ( + "
                    ") olabilir ( referans proje:  50 mm önde, −50 )."
                ),
            ),
            A(
                "karsi_agirlik",
                "Karşı ağırlık",
                "kg",
                "hesap",
                None,
                None,
                kaynak=HESAP,
                sozlesme=MUK,
                formda=False,
                bilgi="",
            ),
        ),
    ),
    # ═══ ASKI VE HALATLAR ══════════════════════════════════════════════════
    (
        "Askı ve halatlar",
        (
            A(
                "halat_adedi",
                "Askı halatı adedi",
                "adet",
                "sayi",
                None,
                7,
                kaynak=GIRDI,
                sozlesme=MUK,
                tam_sayi=True,
                bolen=True,
                bilgi=(
                    "Kabini taşıyan bağımsız halat sayısı. En az iki olmalıdır; iki halatta aranan "
                    "güvenlik katsayısı 12 yerine 16'dır."
                ),
            ),
            A(
                "halat_capi",
                "Askı halatı çapı",
                "mm",
                "secim",
                MT.HALAT_CAPLARI,
                6.5,
                kaynak=GIRDI,
                sozlesme=MUK,
                pozitif=True,
                bolen=True,
                bilgi=(
                    "Askı halatının anma çapı. En az 8 mm olmalıdır ( m.5.5.1.2 a) ); 6,5 mm gibi ince "
                    "halatlar onaylanmış kuruluş belgesiyle kullanılır ( aşağıdaki belge seçimi )."
                ),
            ),
            #  ASKI NOKTASI ( S ) — KAÇIKLIKTAN AYRI BİR NOKTADIR.
            #  Ek C.1.2 ray eksenini orijin alıp beş nokta tanımlar:  kabin merkezi
            #  ( C ), boş kabin kütlesi ( P ), beyan yükü ( Q ), ASKI ( S ) ve kapı.
            #  Kaçıklık ağırlığın NEREDE DURDUĞU, askı ise NEREDEN ASILDIĞIDIR;  ray
            #  kuvveti ikisinin arasındaki moment kolundan doğar — C.2.2.1 ve
            #  C.2.3.1 bu yüzden ( xQ − xs ) ve ( yp − ys ) yazar.
            #  Kabin ortada olup askı kaçık olabilir ( o zaman kaçıklık 0 iken kuvvet
            #  vardır ), ya da kabin kaçık olup kendi üstünden asılı olabilir ( o
            #  zaman boş kabinin momenti sıfırlanır ).
            #  C.2.1'DE ( güvenlik tertibatı ) BU NOKTA GEÇMEZ:  tertibat RAYI
            #  kavradığı için tepki ray ekseninden ölçülür.  Bölümün hükmünü genelde
            #  o durum verdiğinden ( k1 = 2 ), varsayılan 0 çoğu projede sonucu
            #  değiştirmez — ama eksantrik askılı yerleşimde gerçek değer girilmelidir.
            #  BOŞSA ÇİZİMDEN ( cizim/kopru.CIZIMDEN — tamamla ):  halatların indiği
            #  çizgi çizimin geometrisidir;  hesap ile çizim aynı xs'i kullanır.
            A(
                "aski_kaciklik_x",
                "Askı noktasının x kaçıklığı  ( xs )  ( boşsa çizimden )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=MUK,
                isaretli=True,
                cizimden="Boşsa çizimden ( 2:1 halat çizgisi;  1:1 ve arkada 0 ).",
                bilgi=(
                    "xs — HALATLARIN kabine bağlandığı askı noktasının, kabin derinliği doğrultusunda ray"
                    " ekseninden kaçıklığı. Kaçıklık ağırlığın nerede durduğu, askı ise NEREDEN "
                    "ASILDIĞIDIR; ray kuvveti ikisinin FARKINDAN doğar. Kabin ortada olup askı kaçık "
                    "olabilir."
                ),
            ),
            # Boşsa çizimden ( halat geometrisi — cizim/kopru.CIZIMDEN );  çizim
            # bulamıyorsa varsayılan atanmaz:  tahrik kontrolleri HESAP EKSİK.
            A(
                "sarilma_acisi",
                "α — halat sarılma açısı  ( boşsa çizimden )",
                "°",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                opsiyonel=True,
                aci=(1, 360),
                cizimden=(
                    "Boşsa çizimden, açı sabitse:  iki iniş düşey ( 180° ) ya da saptırma kasnağı.  Halat"
                    " eğik iniyorsa ( HALAT SAPMASI:  açı ağırlığın konumuyla değişir ), çift sarımda ya "
                    "da çizim kurulamıyorsa girilmeli."
                ),
                bilgi="α — halatın tahrik kasnağını sardığı açı; tahrik sınırı e^(f·α) buradan çıkar.",
            ),
            A(
                "kabin_kasnak_capi",
                "Kabin askı kasnakları çapı  ( 2:1 )",
                "mm",
                "sayi",
                None,
                240,
                kaynak=KATALOG,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Kabinin altındaki ( ya da üstündeki ) iki askı kasnağının çapı ( referans proje:  240 )."
                ),
            ),
            A(
                "agirlik_kasnak_capi",
                "Karşı ağırlık kasnağı çapı  ( 2:1 )",
                "mm",
                "sayi",
                None,
                400,
                kaynak=KATALOG,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "2:1 askıda karşı ağırlığın üstündeki kasnak ( referans proje:  400 ).  Hesabın D2'si"
                    " ( saptırma kasnaklarının ortalaması ) ve Ds'si ( en küçüğü ) boş bırakılırsa "
                    "çizilen kasnaklardan gelir."
                ),
            ),
            A(
                "kabin_kasnak_arasi",
                "Kabin askı kasnakları arası  ( 2:1 )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "İki kasnağın eksenleri arası.  Boşsa kabin altında halat karşı ağırlığa DÜŞEY "
                    "iner ( sarım açısı 180°, çizimden );  panoya ya da ray ara kirişine çarpacaksa "
                    "kabin genişliği + 30 ( halat eğik iner, α girilir ).  Kabin üstünde kasnakların "
                    "dış ucu kabin kenarından 200 içeride ( korkuluğun içinde )."
                ),
            ),
            A(
                "kanal_sekli",
                "Kasnak kanal şekli",
                "—",
                "secim",
                MT.KANAL_SEKILLERI,
                "Altı Kesik V Kanal",
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Halatın oturduğu kanalın biçimi. Sürtünme katsayısını ve halatın bükülme yorulmasını"
                    " ( Nequiv ) belirler."
                ),
            ),
            A(
                "kanal_isleme",
                "Kanal işleme şekli",
                "—",
                "secim",
                MT.KANAL_ISLEME_SEKILLERI,
                "Sertleştirilmemiş",
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Kanal yüzeyi sertleştirilmiş mi. Sertleştirilmemiş V kanalın alt kesilmesi olmak "
                    "zorundadır."
                ),
            ),
            #  γ ve β KASNAĞIN KENDİ ÖZELLİĞİDİR.  TS EN 81-50 m.5.11.2.3.1.1:
            #  "The value of the groove angle γ shall be GIVEN BY THE MANUFACTURER
            #  according to the grooving design."  Gerçek projelerde değişiyor:
            #  referans projenin makinesi ( Y-2/1-01 ) γ = 38°, ofisin Excel'i γ = 45°,
            #  EN 81-50 hesaplarının yayımlanmış örneği γ = 50° · β = 105°.
            #
            #  İKİSİ DE YALNIZ OFİS SABİTİYDİ ve tek bir projeyi modellemek için genel
            #  sabiti değiştirmek gerekiyordu — o da ofisteki BÜTÜN projeleri sessizce
            #  kaydırıyor, paftada izi kalmıyordu.  ( Makine verimi η'da düzeltilen
            #  hatanın aynısı — bkz. sistem_verimi. )
            #
            #  γ İKİ YÖNLÜDÜR, bu yüzden hiçbir ofis varsayılanı "emniyetli taraf"
            #  olamaz:  büyük γ tahrikte sürtünmeyi düşürür ( emniyetli ) ama
            #  Çizelge 2'de Nequiv(t)'yi de düşürür, yani gereken halat güvenlik
            #  katsayısını GEVŞETİR ( γ = 38° → 12 ,  γ = 50° → 5 ).  Tek dürüst
            #  çözüm, föy elde varken kasnağın gerçek açısını girmektir.
            #  β ise yalnız tahriki etkiler — Nequiv(t) altı kesik V'de β'dan bağımsızdır.
            A(
                "kasnak_gama",
                "γ — kasnak kanal açısı  ( imalatçı — boşsa ofis )",
                "°",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Tahrik kasnağı kanalının açısı — kasnağın kendi özelliğidir ve makinenin teknik "
                    "föyünde yazar. Boşsa ofis değeri kullanılır. İki yönlü etkir: büyük γ tahrikte "
                    "sürtünmeyi düşürür ama gereken halat güvenlik katsayısını da düşürür."
                ),
            ),
            A(
                "kasnak_beta",
                "β — kanal alt kesme açısı  ( imalatçı — boşsa ofis )",
                "°",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Kanalın alt kesme açısı — yalnız altı kesik kanallarda vardır ve en çok 105° "
                    "olabilir. Yalnız tahriki etkiler, halat güvenlik katsayısına girmez. Boşsa ofis "
                    "değeri kullanılır."
                ),
            ),
            #  BELGEYLE AŞILABİLEN İKİ SINIR:  halat çapı ≥ 8 mm ( TS EN 81-20
            #  m.5.5.1.2 a) ) ve D/d ≥ 40 ( m.5.5.2.1 ).  İkisi de uyumlaştırılmış
            #  standart şartıdır;  Asansör Yönetmeliği ( 2014/33/AB ) Ek-I 1.3 askı
            #  elemanları için sayı vermez.  240 mm kasnak ile 6,5 mm halat gibi
            #  birleşimler İKİ sapmayı birlikte, tek bir onaylanmış kuruluş belgesiyle
            #  kanıtlar ( halat üreticisinin ömür / bükülme deneyine dayanan belgesi ) —
            #  bu yüzden ayrı seçim açılmadı.  "Var" seçilirse iki sınırın altı hata
            #  sayılmaz;  Sf ( EN 81-50 m.5.12 ) yine aynen aranır — küçük kasnağın
            #  bedelini zaten o öder.  Referans proje aynı yerde Sf'yi de 12'ye indirir;  bu
            #  bilerek alınmadı.  ANAHTAR ADI ( kasnak_belgesi ) proje dosyaları için
            #  korunur.
            A(
                "kasnak_belgesi",
                "Dt/dh < 40 ya da halat çapı < 8 mm için onaylanmış kuruluş belgesi",
                "—",
                "secim",
                ("Yok", "Var"),
                "Yok",
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Halat çapı 8 mm'den ince ya da kasnak / halat oranı 40'ın altındaysa, sapmayı "
                    "kanıtlayan onaylanmış kuruluş belgesi var mı. İnce halat ile küçük kasnak genellikle"
                    " AYNI belgeyle onaylanır. Belge beyan edilirse iki sınır da hata sayılmaz; güvenlik "
                    "katsayısı yine aranır."
                ),
            ),
            A(
                "halat_birim_kutle",
                "Askı halatı 1 m ağırlığı  ( imalatçı — boşsa tablo )",
                "kg/m",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Halatın metre ağırlığı. Boş bırakılırsa çap ve yapıya göre tablodan alınır; imalatçı"
                    " değeri varsa onu girin."
                ),
            ),
            A(
                "halat_kopma_kN",
                "Askı halatı en küçük kopma yükü  ( imalatçı — boşsa tablo )",
                "kN",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Halatın en küçük kopma yükü. Boşsa tablodan alınır. Gerçekleşen güvenlik katsayısı "
                    "bu değerle hesaplanır."
                ),
            ),
            #  KATALOG HALAT VERİSİ.  Birim kütle ve kopma yükü TS 12385-5 tablosundan
            #  ( 6x19 / 8x19 LİF ÖZLÜ ) çapa göre okunuyordu ve elle girme yolu yoktu.
            #  Küçük kasnaklı dişlisiz makinelerde kullanılan çelik özlü / özel halatlar
            #  o tabloda HİÇ YOKTUR:  6,5 mm için tablo 0,152 kg/m · 24,7 kN derken
            #  katalog 0,179 kg/m · 31,5 kN verir.  Fark iki ayrı yöne çalışıyordu —
            #  hafif halat motoru KÜÇÜK gösteriyor ( emniyetsiz ), düşük kopma yükü ise
            #  güvenlik katsayısını olduğundan KÖTÜ gösterip standarda uyan tasarımlara
            #  "UYGUN DEĞİL" dedirtiyordu.  Boş bırakılırsa tablo kullanılır.
            #  λ — DENGE ( KOMPANZASYON ) ZİNCİRİ ORANI.  Zincir, kabin ile karşı
            #  ağırlık arasında asılıdır ve halatın kabin en alttayken yarattığı
            #  dengesizliği karşılar.  Program bunu HİÇ bilmiyordu:  zincirli bir
            #  tesiste motoru gereğinden büyük hesaplıyordu ( 120 m seyirde 20,7 kW
            #  yerine 39,3 kW ).  %0 = zincir yok  ·  %100 = tam dengeleme.
            #  YUKARI KAÇMAYA KARŞI KORUMA — TS EN 81-20 m.5.5.3 c) İKİ YOL TANIR.
            #  "…it shall not be possible to raise the empty car or the counterweight
            #  to a dangerous position if either the car or the counterweight is
            #  stalled;  EITHER  1) the ropes shall slip on the traction sheave;  OR
            #  2) the machine shall be stopped by an electric safety device."
            #  EN 81-50 m.5.11.2.1 de  T1/T2 ≥ e^(f·α)  şartını açıkça
            #  "where protection … is provided by LIMITING OF TRACTION" diye koşula
            #  bağlar.  Program bu şartı KOŞULSUZ uyguluyordu;  2. yolu kullanan bir
            #  tesis haksız yere UYGUN DEĞİL alıyordu — uzun seyirde halat kütlesi
            #  yüzünden T2 küçülmez ve kayma güvenilmez olur, o yüzden elektrikli
            #  tertibata geçilir.
            #
            #  VARSAYILAN 1. YOLDUR ve öyle kalmalıdır:  bir emniyet kontrolünü
            #  gevşeten seçenek sessizce varsayılan olamaz.  Karşılaştırdığımız üç
            #  uygulama ( referans proje · new block · ofisin Excel'i ) de 1. yolu varsayar.
            #  Hangisinin geçerli olduğu sahada m.6.3.3 deneyiyle sınanır:  karşı
            #  ağırlık tampona oturtulur, makine döndürülmeye devam edilir;  ya halat
            #  kayar ya da kabin hiç yükselmez.
            A(
                "yukari_kacma_korumasi",
                "Yukarı kaçmaya karşı koruma",
                "—",
                "secim",
                _s("Halatın kayması", "Elektrikli güvenlik tertibatı"),
                "Halatın kayması",
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Karşı ağırlık tampona oturmuşken makine yukarı dönmeye devam ederse kabinin tavana "
                    "çekilmesini ne engelliyor. Standart iki yol tanır ( m.5.5.3 c ): halatın kasnakta "
                    "kayması, ya da makineyi durduran elektrikli güvenlik tertibatı. Kumanda panosunda "
                    "böyle bir tertibat yoksa varsayılanı bırakın."
                ),
            ),
            A(
                "denge_zinciri",
                "Denge ( kompanzasyon ) zinciri",
                "—",
                "secim",
                ("Yok", "Var"),
                "Yok",
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Kuyuda kabin ile karşı ağırlık arasına asılan denge ( kompanzasyon ) zinciri var mı."
                    " Varsa halat dengesizliğini karşılar ve gereken motor gücü düşer."
                ),
            ),
            #  EN 81-50 m.5.12.2 — Nequiv(p).  Sabit değil, tesisin askı düzenine bağlıdır.
            #  Program çizilen kasnakları sayar ( cizim/olculer );  motor doğrudan
            #  çağrılıp boş bırakılırsa askı oranından ( bkz. kasnak_tek_yon_askidan ).
            A(
                "kasnak_tek_yon",
                "Tek yönde bükülmeli kasnak sayısı  ( Nps )",
                "adet",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                tam_sayi=True,
                opsiyonel=True,
                bilgi=(
                    "Nps — halatın AYNI yönde büküldüğü kasnak sayısı:  halatın bir kesitinin üzerinden "
                    "geçtiği çizilen kasnaklar ( tahrik kasnağı hariç ). Halat yorulmasını ( Nequiv ) "
                    "büyütür."
                ),
            ),
            A(
                "kasnak_ters_yon",
                "Ters yönde bükülmeli kasnak sayısı  ( Npr )",
                "adet",
                "sayi",
                None,
                0,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                tam_sayi=True,
                bilgi=(
                    "Npr — halatın TERS yönde büküldüğü kasnak sayısı. Ters bükülme halatı dört kat daha "
                    "çok yorar."
                ),
            ),
            #  VARSAYILAN = STANDARDIN KENDİ TABANI ( ACIL_FRENLEME_ASGARI = 0,5 ).
            #  EN 81-50 m.5.11.2.2.2:  "Each moving element shall be considered with
            #  its proper rate of retardation …  In no case shall the rate of
            #  retardation to consider be less than …  0,5 m/s²."  Yani 0,5 bir
            #  TABANDIR;  doğrusu makinenin GERÇEK fren yavaşlamasını imalatçıdan
            #  alıp girmektir.  Bilinmiyorken standardın izin verdiği taban kullanılır.
            #
            #  Eskiden 0,8 yazıyordu ve kaynağı yazılı değildi.  Ofisin Excel'i
            #  b = 0,67·v² + 0,13·v kullanıyor;  bu bağıntı v = 1 m/s'de tam 0,80
            #  verir — 0,8 oradan gelmiş ama HIZA BAĞLI bir değer sabitlenmiş, oysa
            #  aynı bağıntı v = 1,6'da 1,92, v = 2,5'te 4,51 der.  Referans program
            #  ( referans proje ) 0,5 kullanıyor  ( bkz. testler/test_referans_paftalar.py ).
            #
            #  ETKİSİ TEK YÖNLÜ DEĞİLDİR:  a yalnız tahrik bölümüne girer ve
            #  ( gn + a ) / ( gn − a ) çarpanıyla T1/T2 oranını büyütür.  0,8 → 0,5
            #  bu çarpanı 1,178'den 1,107'ye indirir;  gerçek saha projelerinde
            #  tahrik hükmünü belirleyen TEK başat girdi budur.
            A(
                "acil_frenleme_a",
                "Acil frenleme yavaşlaması  ( a )",
                "m/s²",
                "sayi",
                None,
                ACIL_FRENLEME_ASGARI,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "a — acil duruşta kabinin yavaşlaması. Tahrik yeteneğinde halat kuvvetlerini "
                    "belirleyen başat girdidir. Varsayılan 0,5 m/s² STANDARDIN TABANIDIR ( m.5.11.2.2.2 "
                    "); makinenin gerçek fren yavaşlaması biliniyorsa imalatçı değerini girin — büyük a "
                    "tahriki zorlaştırır."
                ),
            ),
            A(
                "aski_kaciklik_y",
                "Askı noktasının y kaçıklığı  ( ys )",
                "mm",
                "sayi",
                None,
                0,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                isaretli=True,
                bilgi=(
                    "ys — askı noktasının, rayları birleştiren doğrultuda ray ekseninden kaçıklığı. Kabin"
                    " kendi askı noktasının tam altındaysa yc ile ys eşittir ve boş kabinin momenti "
                    "sıfırlanır."
                ),
            ),
            #  D2 · Ds BOŞSA ÇİZİMDEN:  çizilen kasnakların ortalaması ve en küçüğü.
            A(
                "saptirma_kasnak_capi",
                "D2 — saptırma kasnaklarının ORTALAMA çapı  ( boşsa çizimden )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                bolen=True,
                cizimden="Boşsa çizimden:  çizilen kasnakların ortalaması.",
                bilgi=(
                    "D2 — tahrik kasnağı HARİÇ bütün kasnakların ORTALAMA çapı. Halatın bükülme şiddeti "
                    "katsayısı Kp = (D1/D2)⁴ bundan çıkar."
                ),
            ),
            #  Ds — EN KÜÇÜK kasnak çapı.  Sf formülündeki Kp = (Dt/Dp)⁴ ORTALAMA
            #  bükülme şiddetini temsil eder;  EN 81-20 m.5.5.2.1'in D/dr ≥ 40 sınırı
            #  ise HER kasnak için ayrı ayrı geçerlidir — ortalama sınırı geçse bile
            #  tek bir küçük kasnak geçemiyor olabilir.  Boş bırakılırsa ortalama çap
            #  kullanılır ( eski davranış ).
            A(
                "saptirma_kasnak_min_capi",
                "Ds — saptırma kasnaklarının EN KÜÇÜK çapı  ( boşsa çizimden )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                cizimden="Boşsa çizimden:  çizilen kasnakların en küçüğü.",
                bilgi=(
                    "Ds — aynı kasnakların EN KÜÇÜĞÜNÜN çapı. D/d ≥ 40 sınırı her kasnak için ayrı "
                    "geçerlidir."
                ),
            ),
            A(
                "aski_halat_boyu",
                "Askı halatının kabin tarafındaki boyu  ( kabin en alt durakta )",
                "m",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi=(
                    "Bir halatın tahrik kasnağından kabine;  2:1'de kabin kasnaklarının altından "
                    "geçip kuyu tavanındaki bağlantıya kadar boyu. Kabin tarafındaki halat kütlesi Gh "
                    "buradan ( motor, kaide, halat güvenliği ).  Hesap eskiden kuyu boyu − yığın + 5 m "
                    "diye tahmin ediyordu."
                ),
            ),
            A(
                "kasnak_kabin_adedi",
                "Kabinle hareket eden kasnak sayısı",
                "adet",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                tam_sayi=True,
                opsiyonel=True,
                bilgi="iPcar — tahrikte ataleti sayılan kabin kasnakları ( 2:1'de iki, 1:1'de yok ).",
            ),
            A(
                "kasnak_agirlik_adedi",
                "Karşı ağırlıkla hareket eden kasnak sayısı",
                "adet",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                tam_sayi=True,
                opsiyonel=True,
                bilgi="iPcwt — tahrikte ataleti sayılan karşı ağırlık kasnakları.",
            ),
            A(
                "saptirma_agirlik_capi",
                "Karşı ağırlık tarafındaki saptırma kasnağının çapı",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi=(
                    "Makine dairesinde karşı ağırlık halatını saptıran sabit kasnak ( yoksa 0 ). "
                    "Tahrikte ataleti mDP olarak ağırlık tarafına girer ( EN 81-50 m.5.11.2.2, koşul II "
                    ")."
                ),
            ),
        ),
    ),
    # ═══ MAKINE ════════════════════════════════════════════════════════════
    (
        "Makine",
        (
            #  Makine tipi motor verimini belirler;  ofisin tablosu
            #  ( engine/ortak/ofis.py ) dişlisiz makinede 0,85, dişlide 0,50 der.
            A(
                "makine_tipi",
                "Makine tipi",
                "—",
                "secim",
                tuple(OFIS.MAKINE_VERIMLERI),
                "Dişlisiz",
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi=(
                    "Dişlisiz mi dişli mi. Verim girilmediğinde ofisin bu tipe ait varsayılan verimi "
                    "kullanılır."
                ),
            ),
            A(
                "motor_gucu",
                "Motor gücü",
                "kW",
                "sayi",
                None,
                4.9,
                kaynak=KATALOG,
                sozlesme=MUK,
                bilgi=(
                    "Seçilen makinenin katalog gücü. Program hesapladığı gücü bununla karşılaştırır; "
                    "küçükse bölüm uygun çıkmaz."
                ),
            ),
            A(
                "makine_agirligi",
                "Makine - motor ağırlığı  ( Gm )",
                "kg",
                "sayi",
                None,
                300,
                kaynak=KATALOG,
                sozlesme=MUK,
                bilgi=(
                    "Gm — makine ve motorun katalogdaki ağırlığı. Makine kaidesine ve kuyu üstüne gelen "
                    "yüke girer."
                ),
            ),
            #  C ( sap. kasnak yükü ) ve D ( makine yatak yükü ) KALDIRILDI.
            #  İkisi de YALNIZ sarılma açısını türetmek için vardı:
            #      B = H − C + D ,  α = 180° − arctan( ( Ra − 2·R1 ) / B )
            #  α artık doğrudan beyan ediliyor ( bkz. "sarilma_acisi" ), o yüzden
            #  bu iki ölçü hiçbir sonuca girmiyordu — formda durup kullanıcıyı
            #  oyalıyorlardı.  Referans proje de açıyı doğrudan sorar ve bu ölçüleri hiç
            #  istemez.
            A(
                "tahrik_kasnak_capi",
                "D1 ( tahrik kasnağı çapı )",
                "mm",
                "sayi",
                None,
                240,
                kaynak=KATALOG,
                sozlesme=MUK,
                pozitif=True,
                bolen=True,
                bilgi=(
                    "D1 — halatın üzerinden geçtiği tahrik kasnağının bölüm dairesi çapı. D1 / halat çapı"
                    " oranı en az 40 olmalıdır."
                ),
            ),
            #  BİR RAYA DÜŞEN MAKİNE YÜKÜ SORULMAZ.  "Bina yapısına" seçildiğinde
            #  hesaba hiç girmez;  "Kılavuz raylara" seçildiğinde makinenin yükü
            #  ( Gm + Tst ) kabin VE karşı ağırlık raylarına EŞİT dağıtılır ( bkz.
            #  mukavemet._makine_ray_payi ).  Eskiden imalatçının asimetrik değeri için ayrı bir
            #  kutu vardı;  yük yolu "bina yapısına" iken de görünüyordu.
            A(
                "makine_tst",
                "Tst — makinenin azami kasnak statik yükü  ( imalatçı )",
                "kg",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                opsiyonel=True,
                bilgi=(
                    "Makinenin taşıyabileceği en büyük kasnak statik yükü ( imalatçı verisi ). Program "
                    "hesapladığı statik yükü bununla karşılaştırır."
                ),
            ),
            #  Tst — SEÇİLEN makinenin tahrik kasnağına izin verdiği azami STATİK yük
            #  ( imalatçı kataloğu ).  Motor gücü "UYGUN" çıkıp kasnak yükü aşılmış bir
            #  makine seçilebiliyordu:  hiçbir şey bakmıyordu.  Boş bırakılırsa kontrol
            #  yapılmaz ve pafta bunu açıkça yazar.
            #  ── MAKİNE YÜKÜNÜN YOLU  ( TS EN 81-20 m.5.7.2.3.7 ) ──────────────
            #  "If the machine or rope suspensions are FIXED TO THE GUIDE RAILS,
            #   additional load cases according to the Table 13 shall be considered."
            #  m.5.2.1.8.4 aynı durumu kuyu tabanı için de anar:  "...load on traction
            #  sheave due to rebound WHEN MACHINE ON RAILS".
            #
            #  Makine dairesiz ( MRL ) tesiste makine kuyunun üstündedir ve yükü ya
            #  RAYLARA ya da BİNA YAPISINA iner.  Standart makinenin nereye
            #  oturabileceğine dair kapalı bir liste vermez — m.5.2.1.8.1 "yapı
            #  taşıyacak, ayrıntısı ulusal yapı yönetmeliğinde" der.  Hesabı
            #  değiştiren TEK ayrım, yükün asansörün KENDİ parçasına ( raya ) değip
            #  değmediğidir.
            #
            #  KİRİŞ TEK BAŞINA CEVAP DEĞİLDİR:  makinenin altındaki platformun
            #  uçları raylara cıvatalıysa yük yine raya iner — "Kılavuz raylara".
            #
            #  ONAY KUTUSU DEĞİL, AÇIK SEÇİM.  İşaretsiz bir kutu SESSİZ VARSAYIMDIR:
            #  kullanıcı dokunmadığında program onun adına "bina yapısına" diye karar
            #  vermiş oluyordu ve bu yalnız paftadaki uyarı satırında görünüyordu.
            #  Seçim olarak sorulunca hangi yolun kabul edildiği HESAP SATIRI olur.
            #  ( Eski projeler True/'EVET' taşır;  MT.makine_raya_mi ikisini de anlar. )
            #  KARAR 3 ( 29 Eyl ):  varsayılan raylara — çizim makine kirişlerini
            #  karşı ağırlık raylarına oturtur ( referans proje de öyle ).  "Bina
            #  yapısına" ( duvardan duvara kiriş ) henüz çizilmiyor:  çizim durur.
            A(
                "makine_raya_biniyor",
                "Makine yükünün yolu",
                "—",
                "secim",
                MT.MAKINE_YUK_YOLU,
                MT.MAKINE_YUK_YOLU[1],
                kaynak=GIRDI,
                sozlesme=MUK,
                yerlesim="mrl",
                bilgi=(
                    "Makine ağırlığı ve kasnak yükü nereye iniyor. 'Kılavuz raylara':  kirişler karşı "
                    "ağırlık raylarına oturur, yük rayların yardımcı donanım kalemine ( MY ) eklenir. "
                    "'Bina yapısına' ( duvardan duvara kiriş ) henüz çizilmiyor."
                ),
            ),
            #  PROJENİN MAKİNESİNE AİT VERİM.  Ofis değeri makine tipine göre tektir
            #  ( dişlisiz · dişli ),  ama her projenin makinesi başkadır ve
            #  imalatçının verdiği verim ondan ayrılabilir.  Tek projenin verimi için
            #  Sabitler'deki ofis değerini değiştirmek BÜTÜN projeleri değiştirirdi.
            #  Boşsa makine tipinden ofis değeri kullanılır ( bkz. sistem_verimi ).
            #  Anlamı ofis değeriyle AYNIDIR:  toplam sistem verimi, askı kaybı dâhil.
            A(
                "makine_verimi",
                "Toplam sistem verimi η  ( imalatçı — boşsa ofis değeri )",
                "—",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "η — askı ( palanga ) kaybı DÂHİL toplam sistem verimi. İmalatçının katalog değeri; "
                    "boş bırakılırsa makine tipine göre ofis değeri kullanılır."
                ),
            ),
            #  YAN YATAK = MAKİNENİN ALTINDAKİ KİRİŞ.  Makine dairesinde kaidenin
            #  yatay kirişidir;  makine dairesiz ( MRL ) tesiste makine kuyu üstünde
            #  doğrudan bu NPU kirişlere oturur ( kolon yoktur ).  İki yerleşimde de
            #  sorulur ve bölüm 2'de eğilmeye göre denetlenir.  Varsayılan NPU 140:
            #  ofisin sahada gördüğü kiriş ( kullanıcı kararı;  örnek projede 120 ).
            A(
                "yan_yatak",
                "F  ( yan yatak — makine kirişi ölçüsü )",
                "—",
                "secim",
                MT.NPU_OLCULERI,
                140,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Makinenin üzerine oturduğu yatay kirişin NPU ölçüsü. Eğilme gerilmesi kontrolüne girer."
                ),
            ),
            #  KİRİŞİN AÇIKLIĞI ÇİZİMDEN ( 29 Eyl, kullanıcı kararı ):  makine
            #  dairesinde kaide halatlara ortalı ve makineyi sarar, açıklığı buradan;
            #  makine dairesizde kirişler karşı ağırlık raylarına oturur ( DBGW ).
            #  Varsayılan 1.400 yalnız hesap motoru doğrudan çağrıldığında ( hesap
            #  programının kendi referans testleri );  programda çizimden gelmezse boş
            #  kalır ve bölüm 2 HESAP EKSİK der ( sayı uydurulmaz ).
            A(
                "yan_yatak_boyu",
                "Yan yatak ( makine kirişi ) boyu",
                "mm",
                "sayi",
                None,
                1400,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                pozitif=True,
                bolen=True,
                opsiyonel=True,
                bilgi=(
                    "L — makine kirişinin mesnetleri arasındaki açıklık:  makine dairesinde kaidenin "
                    "dikine kirişleri arası ( kaide halatlara ortalı, makineyi sarar ), makine "
                    "dairesizde karşı ağırlık rayları arası ( DBGW )."
                ),
            ),
            A(
                "makine_yuku_x",
                "Makine yükünün kiriş mesnedine uzaklığı  ( X )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi=(
                    "X — tahrik kasnağının kiriş boyunca mesnetten uzaklığı:  makine dairesizde "
                    "kirişler karşı ağırlık raylarına oturur, makine dairesinde kaidenin yan "
                    "yataklarıdır. Hesap eskiden L − 335 alıyordu."
                ),
            ),
            A(
                "makine_saptirma_capi",
                "Saptırma kasnağı çapı  ( makine dairesinde, gerekirse )",
                "mm",
                "sayi",
                None,
                400,
                kaynak=KATALOG,
                sozlesme=CIZ,
                gelismis=True,
                yerlesim="daireli",
                bilgi=(
                    "Makine dairesinde karşı ağırlık halatı tahrik kasnağının öbür teğetinden daha "
                    "dışarıda inmeliyse saptırma kasnağı çizilir;  o zaman bu çapta.  Çizildiyse hesabın "
                    "D2 ortalamasına da girer."
                ),
            ),
            A(
                "acil_pano_yani",
                "Acil kurtarma panosunun yanı  ( makine dairesiz )",
                "—",
                "secim",
                ("Sol", "Sağ"),
                "Sol",
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                yerlesim="mrl",
                bilgi=(
                    "Makine dairesizde acil kurtarma panosu en üst kattaki kat kapısının bu yanında durur."
                ),
            ),
        ),
    ),
    # ═══ MAKINE DAIRESI ════════════════════════════════════════════════════
    (
        "Makine dairesi",
        (
            A(
                "mk_uzunluk",
                "Makine dairesi uzunluğu",
                "mm",
                "sayi",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=ELK,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="Makine dairesinin plandaki uzunluğu. Makine dairesi aydınlatmasına girer.",
            ),
            A(
                "mk_genislik",
                "Makine dairesi genişliği",
                "mm",
                "sayi",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=ELK,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="Makine dairesinin plandaki genişliği.",
            ),
            #  TABLİYE BETON YÜKSEKLİĞİ  —  makine dairesinin ZEMİNİNDEN kuyunun
            #  üstündeki betonun ( makinenin oturduğu tabliyenin ) üstüne yükseklik:
            #  kuyu makine dairesine bu kadar taşar ( LiftDesigner'ın makine dairesi
            #  kesiti:  1.200;  betonun kalınlığı ayrıca 120 ).  Ofisin mukavemet
            #  Excel'inde adı "Kaide Yüksekliği" ( 750 ) ve son kat "en üst durak
            #  yüksekliği + kaide − 200" diye girilir.  Programda son kat zaten kuyu
            #  tavanına ölçülür:  tabliye ray ve regülatör halatı boyuna AYRICA
            #  EKLENMEZ ( 5 Eki'ye kadar "tabliye − 200" ekleniyordu — bir kez daha
            #  sayılıyordu;  çizim de onu kuyu tavanının üstünde 1.200 kalın beton
            #  sanıyordu ).  Yalnız makine daireli tesiste sorulur;  odanın kesitini
            #  ve makinenin başındaki temiz yüksekliği belirler ( çizim ).
            A(
                "tabliye_yuksekligi",
                "Tabliye beton yüksekliği",
                "mm",
                "sayi",
                None,
                1200,
                kaynak=GIRDI,
                sozlesme=MUK,
                yerlesim="daireli",
                bilgi=(
                    "Makine dairesinin zemininden kuyunun üstündeki beton tabliyenin ( makinenin "
                    "oturduğu yerin ) üstüne yükseklik — kuyunun makine dairesine taşan kısmı. "
                    "Betonun kalınlığı değildir. Zemin tabliyeyle aynı hizadaysa 0. Yalnız makine "
                    "daireli projede sorulur."
                ),
            ),
            A(
                "md_yukseklik",
                "Makine dairesi iç yüksekliği",
                "mm",
                "sayi",
                None,
                3500,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi=(
                    "Döşemeden tavana temiz yükseklik;  TS EN 81-20 m.5.2.6.3.2 çalışma alanlarında en az"
                    " 2.100 mm."
                ),
            ),
            #  ── MAKİNE DAİRESİ ( proje geneli:  oda binaya aittir ) ────────────
            A(
                "md_duvar",
                "Makine dairesi duvar kalınlığı",
                "mm",
                "sayi",
                None,
                200,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="Makine dairesi duvarlarının kalınlığı.",
            ),
            A(
                "md_x",
                "Makine dairesinin kuyuya göre yeri — x  ( boşsa ortalı )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi=(
                    "Odanın sol iç yüzünün kuyunun sol iç yüzüne göre yeri ( sola − ).  Boşsa oda kuyunun"
                    " dış genişliğine ortalanır."
                ),
            ),
            A(
                "md_y",
                "Makine dairesinin kuyuya göre yeri — y  ( boşsa ön duvarla hizalı )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi=(
                    "Odanın ön iç yüzünün kuyunun ön iç yüzüne göre yeri ( öne − ).  Boşsa odanın önü "
                    "kuyunun ön duvarının dış yüzüyle hizalıdır."
                ),
            ),
            A(
                "md_kapi_duvar",
                "Makine dairesi kapısının duvarı",
                "—",
                "secim",
                ("Ön", "Arka", "Sol", "Sağ"),
                "Arka",
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="Kapının açıldığı duvar.",
            ),
            A(
                "md_kapi_konum",
                "Makine dairesi kapısının köşeden uzaklığı",
                "mm",
                "sayi",
                None,
                300,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="Kapının bulunduğu duvarın sol ( ön ) iç köşesinden kapı boşluğuna.",
            ),
            A(
                "md_kapi_genislik",
                "Makine dairesi kapısı genişliği",
                "mm",
                "sayi",
                None,
                800,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="TS EN 81-20 m.5.2.3.2 a:  en az 600 mm.",
            ),
            A(
                "md_kapi_yukseklik",
                "Makine dairesi kapısı yüksekliği",
                "mm",
                "sayi",
                None,
                2000,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="TS EN 81-20 m.5.2.3.2 a:  en az 1.800 mm.",
            ),
            A(
                "md_pano_duvar",
                "Kumanda panosunun duvarı",
                "—",
                "secim",
                ("Ön", "Arka", "Sol", "Sağ"),
                "Sağ",
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                proje_geneli=True,
                yerlesim="daireli",
                bilgi="Kumanda panosunun durduğu duvar.",
            ),
            A(
                "sase_yuksekligi",
                "Şase yüksekliği",
                "mm",
                "sayi",
                None,
                1100,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                yerlesim="daireli",
                pozitif=True,
                bilgi=(
                    "Makine kaidesinin kolonlarının ( dikine kirişlerin ) boyu. Burkulma narinliği bu "
                    "boydan hesaplanır."
                ),
            ),
            #  PROFİL TİPİ SORULMAZ:  tablo yalnız NPU tanır ve seçim kutusunun tek
            #  seçeneği vardı.  Pafta profili "NPU <ölçü>" diye kendisi yazar.
            A(
                "dikine_kiris",
                "E  ( dikine kiriş ölçüsü )",
                "—",
                "secim",
                MT.NPU_OLCULERI,
                120,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                yerlesim="daireli",
                bilgi="Makine kaidesini taşıyan düşey kolonun NPU ölçüsü. Burkulma kontrolüne girer.",
            ),
        ),
    ),
    # ═══ TAMPONLAR ═════════════════════════════════════════════════════════
    (
        "Tamponlar",
        (
            #  TİP, KONTROLÜN KENDİSİNİ SEÇER.  TS EN 81-20 m.5.8.1 tamponları üçe
            #  ayırır ve her birine başka bir kural bağlar ( strok formülü, hız
            #  sınırı );  tip sorulmadan bu kuralların hiçbiri denetlenemiyordu.
            #  Ofis poliüretan kullanıyor, varsayılan odur.
            A(
                "tampon_tipi",
                "Tampon tipi",
                "—",
                "secim",
                MT.TAMPON_TIPLERI_ADLARI,
                MT.TAMPON_TIPLERI_ADLARI[1],
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Tamponun cinsi. Her tipin strok kuralı ayrıdır: lineer ( yaylı ), lineer olmayan ( "
                    "poliüretan ) ve enerji yutmalı ( hidrolik )."
                ),
            ),
            #  ADET, KUYU TABANINA DÜŞEN KUVVETİ BÖLER.  m.5.2.1.8.5 kuvveti
            #  "evenly distributed between the total number of car buffers" der:
            #  toplam 4·gn·(P+Q)'dur ama döşemenin TAŞIYACAĞI şey tampon BAŞINA
            #  düşendir.
            #  Tam sayı ve bölen:  0 ya da 1,5 eskiden sessizce 1 sayılıyordu ( 4 Eki ).
            A(
                "kabin_tampon_adedi",
                "Kabin tamponu adedi",
                "adet",
                "sayi",
                None,
                1,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                tam_sayi=True,
                bolen=True,
                bilgi=(
                    "Kabinin altındaki tampon sayısı. Kuyu tabanına gelen toplam kuvvet bu sayıya "
                    "bölünerek bir tampon altına düşen yük bulunur.  Çizim 1 ya da 2 tampon çizer."
                ),
            ),
            A(
                "kabin_tampon_arasi",
                "Kabin tamponları arası  ( iki tamponda )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "İki kabin tamponunun eksenleri arası.  Tamponlar kabin rayı ekseninde, kabinin "
                    "ortasına simetrik çizilir.  Tek tamponda boş kalır."
                ),
            ),
            A(
                "agirlik_tampon_adedi",
                "Ağırlık tamponu adedi",
                "adet",
                "sayi",
                None,
                1,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                tam_sayi=True,
                bolen=True,
                bilgi="Karşı ağırlığın altındaki tampon sayısı.  Çizim 1 ya da 2 tampon çizer.",
            ),
            A(
                "agirlik_tampon_arasi",
                "Ağırlık tamponları arası  ( iki tamponda )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "İki ağırlık tamponunun eksenleri arası.  Tamponlar ağırlığın boyunca, ortasına "
                    "simetrik çizilir.  Tek tamponda boş kalır."
                ),
            ),
            A(
                "kabin_tampon_boyu",
                "Kabin tamponu uzunluğu",
                "mm",
                "sayi",
                None,
                100,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi="Tamponun kendi boyu ( ezilmemiş hâlde ).",
            ),
            A(
                "kabin_tampon_ezilme",
                "Kabin tamponu ezilme miktarı",
                "mm",
                "sayi",
                None,
                90,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Tamponun tam ezildiğinde kısalacağı miktar ( stroku ). Kabinin tampona oturduğu en "
                    "alçak konum bununla bulunur."
                ),
            ),
            A(
                "kabin_carpma_arasi",
                "Kabin tamponu - çarpma plakası arası",
                "mm",
                "sayi",
                None,
                150,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Tamponun üst yüzü ile kabinin altındaki çarpma plakası arasındaki boşluk ( kabin en "
                    "alt durakta iken )."
                ),
            ),
            A(
                "agirlik_tampon_baba",
                "Ağırlık tamponu baba yüksekliği",
                "mm",
                "sayi",
                None,
                300,
                kaynak=GIRDI,
                sozlesme=MUK,
                bilgi="Karşı ağırlık tamponunun beton babasının yüksekliği.",
            ),
            A(
                "agirlik_tampon_boyu",
                "Ağırlık tamponu uzunluğu  ( boşsa kabin tamponununki )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Karşı ağırlık tamponunun serbest boyu ( kaideden tepesine ).  Düşey kesitlerde "
                    "ağırlık tamponu bu boyda çizilir."
                ),
            ),
            A(
                "agirlik_tampon_ezilme",
                "Ağırlık tamponu ezilme miktarı",
                "mm",
                "sayi",
                None,
                90,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi="Karşı ağırlık tamponunun ezilme miktarı.",
            ),
            A(
                "agirlik_carpma_arasi",
                "Ağırlık tamponu - çarpma plakası arası",
                "mm",
                "sayi",
                None,
                150,
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi="Karşı ağırlık tamponu ile ağırlığın çarpma plakası arasındaki boşluk.",
            ),
            #  BOŞSA ÇİZİMDEN:  kuyu dibi zinciri ( kuyu dibi − tampon − çarpma arası
            #  − kabinin şase altı ).
            A(
                "kabin_tampon_baba",
                "Kabin tamponu baba yüksekliği  ( boşsa çizimden )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                cizimden="Boşsa çizimden:  kuyu dibi − tampon − çarpma arası − kabinin şase altı.",
                bilgi=(
                    "Tamponun üzerinde durduğu beton babanın yüksekliği ( kuyu tabanından tamponun altına )."
                ),
            ),
        ),
    ),
    # ═══ HIZ REGÜLATÖRÜ ════════════════════════════════════════════════════
    (
        "Hız regülatörü",
        (
            A(
                "regulator_yani",
                "Regülatör halatının yanı",
                "—",
                "secim",
                ("Karşı ağırlığın karşısı", "Sağ", "Sol"),
                "Karşı ağırlığın karşısı",
                kaynak=GIRDI,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Hız regülatörü halatının ve gergi kasnağının hangi kabin rayının yanından indiği.  "
                    'Karşı ağırlık arkadaysa "karşısı" sağ yan sayılır.'
                ),
            ),
            A(
                "regulator_kaciklik",
                "Regülatör halatı – kabin ray ekseni arası  ( arkaya + )",
                "mm",
                "sayi",
                None,
                None,
                kaynak=KURAL,
                sozlesme=CIZ,
                gelismis=True,
                bilgi=(
                    "Regülatör halatının ray ekseninden uzaklığı ( referans proje:  280 arkada ).  Boşsa "
                    "280, askı halatlarının öbür yanında ( kabin halat bağlantısıyla üst üste binmesin );  "
                    "gergi raya ya da tampona çarpıyorsa program çarpmayan en yakın yeri seçer."
                ),
            ),
            #  "halat_arasi" ( Ra ) da KALDIRILDI — o da yalnız α'nın payındaydı
            #  ( A = Ra − 2·R1 ).  Arka ağırlıkta kuyu derinliği − ray-kapı arası −
            #  ağırlık ray-duvar'dan türetiliyordu;  o üç ölçü kendi hesaplarında
            #  duruyor, yalnız bu türetme kalktı.
            A(
                "reg_halat_capi",
                "Regülatör halatı çapı",
                "mm",
                "secim",
                _s(6, 6.5, 8),
                6,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                pozitif=True,
                bolen=True,
                bilgi=(
                    "Regülatör halatının anma çapı ( EN 12385-5 ). TS EN 81-20 çap için ayrı bir alt "
                    "sınır vermez; kasnak çapına oranı en az 30 olmalıdır ( m.5.6.2.2.1.3 c) )."
                ),
            ),
            A(
                "reg_kasnak_capi",
                "Regülatör kasnak çapı  ( Dreg )",
                "mm",
                "sayi",
                None,
                300,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                pozitif=True,
                bilgi=(
                    "Dreg — regülatör kasnağının bölüm dairesi çapı. Halat çapına oranı en az 30 "
                    "olmalıdır ( m.5.6.2.2.1.3 )."
                ),
            ),
            A(
                "reg_kanal_acisi",
                "Regülatör kanal açısı",
                "°",
                "sayi",
                None,
                40,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bolen=True,
                aci=(1, 179),
                bilgi=(
                    "Regülatör kasnağı kanalının açısı. Halatı çekme kuvvetini belirleyen sürtünme "
                    "buradan çıkar."
                ),
            ),
            #  EŞDEĞER AĞIRLIK:  güncel gergiler kollu ( 15 – 35 kg ağırlık, kol oranıyla
            #  büyütülür ) ya da yaylıdır;  hesaba giren kasnak merkezindeki kuvvettir.
            #  Kollu gergide ağırlığın kendi kütlesi girilirse halat gerilimi düşük,
            #  halat güvenlik katsayısı İYİMSER çıkar ( referans proje:  35 kg kolda 1.030 N
            #  → eşdeğer 105 kg;  35 girilince S = 11,77, doğrusu 8,04 ).
            A(
                "reg_gergi_agirligi",
                "Regülatör gergi ağırlığı — eşdeğer  ( Gra )",
                "kg",
                "sayi",
                None,
                70,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Gra — gergi kasnağının merkezinde oluşan kuvvet / 9,81. Kollu ya da yaylı gergide "
                    "ağırlığın kendi kütlesini DEĞİL bu eşdeğeri girin ( imalatçı belgesinde yazar ); "
                    "yalnız doğrudan asılı ağırlıkta ikisi aynıdır. Halattaki gerilimi belirler."
                ),
            ),
            #  KATALOG VERİSİ ASKI HALATINDA VARDI, REGÜLATÖRDE YOKTU.  TS 12385-5
            #  tablosu yalnız LİF ÖZLÜ halatları kapsar;  regülatör halatları çoğu
            #  zaman çelik özlüdür ve kopma yükleri belirgin biçimde yüksektir
            #  ( 6 mm:  tablo 23,1 kN — piyasadaki çelik özlü 28 kN ).  Program bu
            #  yüzden UYGUN tasarımları reddedebiliyordu.  Boş bırakılırsa tablo.
            A(
                "reg_halat_birim_kutle",
                "Regülatör halatı 1 m ağırlığı  ( imalatçı — boşsa tablo )",
                "kg/m",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi="Regülatör halatının metre ağırlığı. Boşsa tablodan alınır.",
            ),
            A(
                "reg_halat_kopma_kN",
                "Regülatör halatı en küçük kopma yükü  ( imalatçı — boşsa tablo )",
                "kN",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Regülatör halatının en küçük kopma yükü. Boşsa tablodan alınır; halat güvenlik "
                    "katsayısı en az 8 olmalıdır."
                ),
            ),
            #  TS EN 81-20 m.5.6.2.2.1.1 d):  regülatörün ürettiği çekme kuvveti,
            #  "güvenlik tertibatını devreye sokmak için GEREKENİN İKİ KATI" ile
            #  300 N'un BÜYÜĞÜNDEN az olamaz.  O kuvvet İMALATÇI VERİSİDİR ( halatın
            #  kendi statik gergisinin iki katı DEĞİLDİR ).  Boş bırakılırsa yalnız
            #  300 N sınırı denetlenir ve pafta eksiği açıkça yazar.
            A(
                "guvenlik_devreye_kuvvet",
                "Güv. tertibatını devreye sokma kuvveti  ( imalatçı )",
                "N",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Fren bloğunu devreye sokmak için gereken kuvvet ( fren bloğunun tip inceleme "
                    "belgesinde yazar ). Boş bırakılırsa standardın 300 N şartı denetlenir."
                ),
            ),
            #  TS EN 81-20 m.5.6.2.2.1.1 a):  devreye girme hızı beyan hızının en az
            #  %115'i ve tertibat tipine göre belirlenen üst sınırın ALTINDA olmalı.
            #  Değer regülatörün TİP İNCELEME belgesinden gelir.
            A(
                "reg_devreye_hizi",
                "Regülatör devreye girme hızı  ( imalatçı )",
                "m/s",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi=(
                    "Regülatörün fren bloğunu tetiklediği hız ( regülatörün etiketinde yazar ). Boşsa "
                    "paftaya standardın izin verdiği aralık yazılır."
                ),
            ),
            A(
                "reg_halat_boyu",
                "Regülatör halatı boyu",
                "m",
                "sayi",
                None,
                None,
                kaynak=CIZIM,
                sozlesme=MUK,
                formda=False,
                opsiyonel=True,
                bilgi=(
                    "Regülatör kasnağı ile kuyu dibindeki gergi kasnağı arası iki kez ve iki yarım "
                    "sarım. Çizim yoksa ( alt duraktan tavana − 200 ) × 2."
                ),
            ),
        ),
    ),
    # ═══ ELEKTRIK VE TOPRAKLAMA ════════════════════════════════════════════
    (
        "Elektrik ve topraklama",
        (
            #  S1 = 6 mm²:  avan motoru ve ofisin avan Excel'i de 6 kullanır;  eskiden
            #  burada kaynaksız 16 vardı ve aynı asansöre iki proje farklı kesit
            #  veriyordu.  4,9 – 15 kW'lık motorlarda ε ≤ %1,6 ve akım yeter;  daha
            #  büyük motorda yetmezse gerilim düşümü bölümü "kesiti büyütün" der.
            A(
                "kolon_kesit",
                "S1 — Kolon hattı kesiti",
                "mm²",
                "sayi",
                None,
                6,
                kaynak=GIRDI,
                sozlesme=ELK,
                gelismis=True,
                bilgi=(
                    "S1 — panodan asansör tablosuna gelen kolon hattının iletken kesiti. Gerilim düşümü "
                    "ve koruma iletkeni bundan çıkar."
                ),
            ),
            A(
                "makine_kesit",
                "S2 — Makine besleme kesiti",
                "mm²",
                "sayi",
                None,
                6,
                kaynak=GIRDI,
                sozlesme=ELK,
                gelismis=True,
                bilgi="S2 — tablodan makineye giden besleme hattının kesiti.",
            ),
            A(
                "temel_a",
                "Temel uzunluğu",
                "m",
                "sayi",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=ELK,
                proje_geneli=True,
                bilgi=(
                    "Binanın temelinin uzunluğu. Temel topraklamasının eşdeğer direnci temel ALANINDAN "
                    "hesaplanır."
                ),
            ),
            A(
                "temel_b",
                "Temel genişliği",
                "m",
                "sayi",
                None,
                None,
                kaynak=GIRDI,
                sozlesme=ELK,
                proje_geneli=True,
                bilgi="Binanın temelinin genişliği.",
            ),
            A(
                "kablo_tipi_1",
                "1. bükülgen kablo tipi",
                "—",
                "secim",
                MT.KABLO_TIPLERI,
                "24 x 0,75",
                kaynak=GIRDI,
                sozlesme=MUK,
                gelismis=True,
                bilgi=(
                    "Kabine inen bükülgen ( gezici ) kablonun tipi. Metre ağırlığı buradan tabloya bakılır."
                ),
            ),
            #  GEZİCİ KABLONUN İMALATÇI AĞIRLIĞI.  Program iki kabloyu tablodan alır
            #  ( 1. tip + kat kapısından türeyen 2. tip ) ve tablo dört kablo tanır;
            #  tek kablolu ya da farklı kesitli bir tesis girilemiyordu ( referans proje
            #  örneği:  tek kablo 0,44 kg/m — tablo 2 × 0,642 = 1,284 kg/m verir ).
            #  MTrav motor gücüne, P'ye ( ray · kuyu tabanı ) ve tahrike girer.
            #  TOPLAMDIR:  bütün gezici kabloların metre ağırlıkları toplanıp yazılır.
            #  Boş bırakılırsa tablo kullanılır.
            A(
                "kablo_birim_kutle",
                "Gezici kabloların toplam 1 m ağırlığı  ( imalatçı — boşsa tablo )",
                "kg/m",
                "sayi",
                None,
                None,
                kaynak=KATALOG,
                sozlesme=MUK,
                gelismis=True,
                opsiyonel=True,
                bilgi="Bütün gezici kabloların toplam metre ağırlığı. Boşsa kablo tipinden tabloya bakılır.",
            ),
            #  2. kablo tipi GİRDİ DEĞİLDİR:  kat kapısı tipinden türetilir.
            #  Sorulmaz, hesaplanır.
            A(
                "kablo_tipi_2",
                "2. bükülgen kablo tipi",
                "—",
                "hesap",
                None,
                None,
                kaynak=HESAP,
                sozlesme=MUK,
                formda=False,
                bilgi="",
            ),
        ),
    ),
)

GRUPLAR = tuple(ad for ad, _a in _GRUPLAR)
ALANLAR = tuple(replace(a, grup=ad) for ad, al in _GRUPLAR for a in al)
ALAN = {a.anahtar: a for a in ALANLAR}


def _denetle():
    """Şemanın kendi tutarlılığı — içe aktarılırken bir kez."""
    gorulen = set()
    for a in ALANLAR:
        assert a.anahtar not in gorulen, f"iki kez tanımlı: {a.anahtar}"
        gorulen.add(a.anahtar)
        assert a.kaynak in KAYNAKLAR, (a.anahtar, a.kaynak)
        assert a.sozlesme in (MUK, ELK, CIZ), (a.anahtar, a.sozlesme)
        assert a.yerlesim in (None, "mrl", "daireli"), (a.anahtar, a.yerlesim)
        assert a.formda or a.kaynak in (CIZIM, HESAP), f"formda olmayan girdi: {a.anahtar}"
        assert a.formda or not a.gelismis, f"formda olmayan alan gelişmiş olamaz: {a.anahtar}"
        assert a.bilgi.strip() or not a.formda, f"açıklaması yok: {a.anahtar}"
        if a.secenek_kosulu:
            assert set(a.secenek_kosulu) <= set(a.secenekler or ()), a.anahtar


_denetle()
