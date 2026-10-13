# -*- coding: utf-8 -*-
"""
MUKAVEMET HESABI — GİRDİ SÖZLEŞMESİ        ( uygulama projesi )

Tüketen:  motor/uygulama/mukavemet.py

Bu modül hesap YAPMAZ.  Yalnızca mukavemet motorunun hangi girdileri
beklediğini, her birinin birimini, seçenek listesini ve varsayılanını
tanımlar.  Arayüz, API ve doğrulama testleri hep buradan okur — tek
doğruluk kaynağı.

AVANDAN AYRIDIR.  Avan tarafındaki tablolar ( motor/avan/tablolar.py )
MMO/697 avan kitabından gelir;  uygulama projesinin tabloları bilerek ayrı
tutulmuştur ( bkz. motor/uygulama/mukavemet_tablolari.py ).
"""

from temel import bos_mu, sayi_mi
from motor.ortak import ofis
from motor.ortak.adimlar import evet_mi
from motor.uygulama import mukavemet_tablolari
from tasarim import alanlar, gorunum
from cizim import kopru
from motor.uygulama import uygulama_sabitleri


def _s(*d):
    return tuple(d)


#  ( anahtar, etiket, birim, tür, seçenekler, varsayılan )
#    tür:  "sayi" · "secim" · "hesap"
#    "hesap" alanları kullanıcıdan alınmaz — tamamla() üretir.
#  TS EN 81-50 m.5.11.2.2.2 — hesaba girecek en küçük yavaşlama.
ACIL_FRENLEME_ASGARI = alanlar.ACIL_FRENLEME_ASGARI

#  ALAN SÖZLEŞMESİ:  ( anahtar, etiket, birim, tür, seçenekler, varsayılan )
#    tür:  "sayi" · "secim" · "hesap" — "hesap" alanlarını kullanıcı girmez,
#    tamamla() üretir.
#  TANIMLAR VE GEREKÇELERİ TASARIM ŞEMASINDA DURUR ( tasarim/alanlar.py ):
#  formun, çizimin ve elektrik hesaplarının alanlarıyla birlikte, tasarım
#  sırasıyla, bir kez.  Burası mukavemet motorunun payını oradan okur.
ALANLAR = gorunum.sozlesme(alanlar.MUK)

#  İŞARETLİ ( NEGATİF OLABİLEN ) ALANLAR
#  TS EN 81-50 Ek C.1.2 ray eksenini ORİJİN alan bir Kartezyen sistem kurar:
#  kabin merkezi, boş kabin kütlesi, beyan yükü, askı ve kapı konumları bu
#  eksene göre İŞARETLİ koordinatlardır.  Ray ekseninin bir yanı artı, öbür
#  yanı eksidir ve işaret momentin YÖNÜNÜ belirler — C.2.2.1'in ( yp − ys )
#  kolu, iki nokta ray ekseninin ayrı yanlarındaysa büyür, aynı yanındaysa
#  küçülür.  Bu alanları "negatif olamaz" saymak, kaçıklığı yalnız tek yöne
#  izin vermek demekti;  referans projenin örnek projesinde de Yp = −15,0 cm'dir.
#
#  ÖTEKİ ALANLAR NEGATİF OLAMAZ:  uzunluk, kütle, çap, sehim ve adet
#  büyüklüktür, işareti yoktur.
ISARETLI_ALANLAR = gorunum.anahtarlar(alanlar.MUK, isaretli=True)

#  Hızlı erişim
ALAN = {a[0]: a for a in ALANLAR}

#  UYGULAMA FORMUNUN mukavemet dışı ( elektrik … ) alanları — tanımları
#  tasarım şemasında ( tasarim/alanlar.py, sözleşmesi ELK ).  Uygulama
#  girdisi ( uygulama_girdisi ) ikisini birleştirir;  burada durur ki
#  mukavemet ve bu modül uygulama_girdisi'ni geri çağırmasın ( döngü ).
EK_ALANLAR = gorunum.sozlesme(alanlar.ELK)
EK_ALAN = {a[0]: a for a in EK_ALANLAR}
HESAPLANAN = tuple(a[0] for a in ALANLAR if a[3] == "hesap")


#  BOŞ BIRAKILABİLEN alanlar.  Boşsa motor değeri kendisi türetir ve
#  paftada kaynağını "türetilen" diye yazar;  zorunlu tutmak kullanıcıyı
#  bilmediği bir sayıyı uydurmaya iter.
#  ---------------------------------------------------------------------
#  FİZİKSEL GİRDİ SINIRLARI
#  ---------------------------------------------------------------------
#  ADET alanları TAM SAYI olmalıdır:  6,5 halat ya da 2,5 ray diye bir şey
#  yoktur, ama hesap böyle bir girdiyle sorunsuz koşup "UYGUN" veriyordu.
TAM_SAYI_ALANLARI = gorunum.anahtarlar(alanlar.MUK, tam_sayi=True)
#  SIFIR OLAMAYAN alanlar:  bölen ya da uzunluk oldukları için 0 girildiğinde
#  hesap teknik bir hatayla ( TypeError · ZeroDivisionError ) çöküyordu;
#  kullanıcı hangi alanın sorunlu olduğunu göremiyordu.
POZITIF_ALANLAR = gorunum.anahtarlar(alanlar.MUK, pozitif=True)
#  MAKİNE YERLEŞİMİNE GÖRE HESABA GİRMEYEN ALANLAR.  Ekranda gizlenirler;
#  gizli bir alandaki değer projeyi DURDURMAMALI ( bkz. uygulanmayan ).
#    · Makine dairesi olmadan var olmayanlar:  tabliye ve kaidenin kolonları
#      ( şase yüksekliği · dikine kiriş ).  Makinenin altındaki kiriş
#      ( yan yatak ) MRL'de de vardır ve sorulur.
#    · Makine yükünün yolu yalnız MRL'de sorulur — makine daireli tesiste
#      makine kendi kaidesindedir, yükü raya binmez.
MAKINE_DAIRESI_ALANLARI = gorunum.anahtarlar(alanlar.MUK, yerlesim="daireli")
RAYA_BINEN_ALANLARI = gorunum.anahtarlar(alanlar.MUK, yerlesim="mrl")


def uygulanmayan(g):
    """Bu makine yerleşiminde hesaba girmeyen mukavemet alanları."""
    return set(MAKINE_DAIRESI_ALANLARI) if evet_mi(g.get("mk_yok")) else set(RAYA_BINEN_ALANLARI)


#  AÇI alanları:  0 < açı < 180.  360° girildiğinde sin(180°) = 0 çıkıyor ve
#  hesap OverflowError ile çöküyordu.
#  α — sarılma açısı:  tek sarımda en çok yarım tur, çift sarımda bir tam
#  tur.  Üst sınır 360'tır;  seçilen kanal şekline göre DARALTMAYI motor
#  yapar ( bkz. mukavemet._tahrik · alfa_ust ), çünkü burada kanal şekli
#  ile açı alanı birbirini görmez.
ACI_ALANLARI = {a.anahtar: a.aci for a in alanlar.ALANLAR if a.sozlesme == alanlar.MUK and a.aci}

#  kabin_agirligi BURADA DEĞİLDİR:  tamamla() onu ofis tablosundan doldurur
#  ve doldurma bir tek beyan yükü geçersizken başarısız olur — o durumda
#  "boş bırakılamaz" hatası çıkmalı, hesap None ile devam etmemelidir.
OPSIYONEL_ALANLAR = gorunum.anahtarlar(alanlar.MUK, opsiyonel=True)

#  µ artık OFİS SABİTİDİR ( sabitler.reg_mu );  üst sınırı standartla
#  birlikte MT.REG_MU_AZAMI'da durur.

#  Hesapta BÖLEN olarak geçen alanlar — sıfır kabul edilmez.
BOLEN_ALANLAR = gorunum.anahtarlar(alanlar.MUK, bolen=True)

#  ( girdi anahtarı , [ ( tablo sütunu , okuyucu ) … ] , ne olduğu )
TABLO_GEREKLI = (
    (
        "kabin_ray_profili",
        [
            (k, (lambda p, k=k: mukavemet_tablolari.ray(p, k)))
            for k in ("A", "Ix", "Iy", "Wx", "Wy", "ix", "c")
        ]
        + [(k, (lambda p, k=k: mukavemet_tablolari.ray_geo(p, k))) for k in ("h1_b_f", "h1_f")],
        "kesit değerleri",
    ),
    (
        "agirlik_ray_profili",
        [
            (k, (lambda p, k=k: mukavemet_tablolari.ray(p, k)))
            for k in ("A", "Gr", "Ix", "Iy", "Wx", "Wy", "c")
        ]
        + [(k, (lambda p, k=k: mukavemet_tablolari.ray_geo(p, k))) for k in ("h1_b_f", "h1_f")],
        "kesit değerleri",
    ),
    #  iy DE ARANIR:  burkulma en küçük atalet yarıçapından hesaplanır
    #  ( bkz. mukavemet._makine ), eksik profil sessizce geçmemelidir.
    (
        "dikine_kiris",
        [
            ("A", lambda x: mukavemet_tablolari.npu(x, "A")),
            ("ix", lambda x: mukavemet_tablolari.npu(x, "ix")),
            ("iy", lambda x: mukavemet_tablolari.npu(x, "iy")),
        ],
        "kesit değerleri",
    ),
    ("yan_yatak", [("Wx", lambda x: mukavemet_tablolari.npu(x, "Wx"))], "kesit değerleri"),
    (
        "halat_capi",
        [
            ("1 m ağırlığı", mukavemet_tablolari.halat_agirlik),
            ("kopma yükü", mukavemet_tablolari.halat_kopma),
        ],
        "halat verisi",
    ),
    (
        "reg_halat_capi",
        [
            ("1 m ağırlığı", mukavemet_tablolari.halat_agirlik),
            ("kopma yükü", mukavemet_tablolari.halat_kopma),
        ],
        "halat verisi",
    ),
    #  Nequiv(t) artık şeklin adından değil, ofis açılarından hesaplanır
    #  ( EN 81-50 Çizelge 2 );  burada yalnız şeklin TANINDIĞI denetlenir.
    ("kanal_sekli", [("kanal türü", mukavemet_tablolari.kanal_turu)], "kasnak verisi"),
    ("guvenlik_tertibati", [("k1", mukavemet_tablolari.darbe_k1)], "darbe katsayısı"),
    (
        "ray_celigi_rm",
        [
            ("σperm normal", mukavemet_tablolari.sigma_perm_normal),
            ("σperm güv.tert.", mukavemet_tablolari.sigma_perm_guvenlik),
        ],
        "izin verilen gerilmeler",
    ),
    ("kablo_tipi_1", [("ağırlık", mukavemet_tablolari.kablo_agirligi)], "kablo verisi"),
    ("kablo_tipi_2", [("ağırlık", mukavemet_tablolari.kablo_agirligi)], "kablo verisi"),
    (
        "beyan_yuku",
        [
            ("kişi sayısı", mukavemet_tablolari.kabin_kisi),
            ("en büyük alan", mukavemet_tablolari.kabin_azami_alan),
            ("en küçük alan", mukavemet_tablolari.kabin_asgari_alan),
        ],
        "kabin alanı verisi",
    ),
)


#  ARAYÜZ GRUPLARI.  Form kendini bu listeden üretir;  sıralama ve başlıklar
#  hesabın akışını izler.
GRUPLAR = tuple(
    (g["ad"], tuple(f["anahtar"] for f in g["alanlar"])) for g in gorunum.form_gruplari(alanlar.MUK)
)


#  GELİŞMİŞ ALANLAR.  Her grubun altında kapalı duran "Gelişmiş" bölümünde
#  gösterilirler;  hesaba AYNEN girerler ve paftaya aynen basılırlar — yalnız
#  formda ilk bakışta görünmezler.
#
#  Ölçüt:  değer binadan ya da projeden gelmiyorsa ( ürünün ya da ofisin
#  sabiti ), zaten tablodan / başka bir girdiden dolduruluyorsa ya da yanlış
#  kaldığında sonuç bunu hata / uyarı olarak söylüyorsa buradadır.  GÖRÜNÜR
#  KALANLAR her projede değişenler ve yanlış kalınca sonucu çok değiştiren
#  beyanlardır:  askı oranı · ray-kapı arası · güvenlik tertibatı tipi ·
#  karşı ağırlıkta güvenlik tertibatı · sarılma açısı · regülatörün iki
#  imalatçı değeri ( girilmezse bölüm HESAP EKSİK kalır ).
#
#  ÜÇ KAÇIKLIK GÖRÜNÜR KALIR ( kabin merkezi y · askı xs · ys ).  Ürün
#  sabiti değil, çizime bağlı ölçülerdir;  varsayılan 0 standart yerleşimdir
#  ( kabin raylar arasında ortada, askı ray ekseninde ).  100 mm kaçıklık beş
#  projenin dördünde kabin rayı hükmünü çevirdi:  kaçık bir yerleşimde gizli
#  bir 0 unutulursa ray hesabı emniyetsiz tarafta kalır ve "değiştirildi"
#  sayacı unutulan değeri yakalayamaz.
#
#  Seçim 5 proje üzerinde her girdi gerçekçi değerlere çekilerek yapıldı;
#  karşı ağırlık malzemesi ve kabin tamponu - çarpma plakası arası
#  hesabın hiçbir sayısını değiştirmedi, kaide yüksekliği en çok %1,3
#  etkiledi.  KARŞI AĞIRLIK YERİ O TARAMADA DA "değiştirmedi" çıkmıştı,
#  ama yanıltıcıydı:  etkisi yalnız δstr girilmiş projelerde görünür ve
#  tarama projelerinde δstr boştu.  Yerleşim kararı olduğu için artık
#  Gelişmiş'te değil, "Karşı ağırlık" grubunda normal alandır.
GELISMIS_ALANLAR = frozenset(gorunum.anahtarlar(alanlar.MUK, gelismis=True, formda=True))


#  ---------------------------------------------------------------------
#  ALAN AÇIKLAMALARI  —  formdaki ⓘ dairesinin içeriği
#  ---------------------------------------------------------------------
#  Her girdinin NE OLDUĞUNU bir iki cümlede söyler.  Amaç öğretmek değil,
#  KARIŞTIRMAYI ÖNLEMEK:  aynı sözcükle anılan ama farklı şeyler olan
#  alanlar ( üç kaçıklık, iki kasnak çapı, tamponun dört ölçüsü ) burada
#  birbirinden ayrılır.
#
#  EKSEN TAKIMI TEK YERDE ANLATILIR.  TS EN 81-50 Ek C.1.2 bütün konumları
#  KILAVUZ RAY SİSTEMİNİN EKSENİNDEN ölçer:  orijin iki rayı birleştiren
#  doğrunun ortasıdır, y bu doğru boyunca ( kabin genişliği ), x ona dik
#  ( kabin derinliği · kapı–arka ) yöndedir.  Kaçıklık soran her kutu bu
#  orijine göredir ve açıklaması bunu tekrar eder — kullanıcı kutuya
#  bakarken Ek C'yi açmak zorunda kalmasın.
#  AÇILIR LİSTEDE DEĞERİN YERİNE BASILACAK METİN.  Kutunun DEĞERİ sayı
#  kalır ( hesap, kayıt ve geri yükleme ona bakar );  yalnız GÖRÜNEN yazı
#  değişir.  Askı oranında çıplak "2" okuyan, 2:1 mi 1:2 mi olduğunu
#  ayırt edemiyordu — avan formu zaten "1:1 / 2:1" gösteriyor.
SECENEK_METNI = {
    a.anahtar: a.secenek_metni for a in alanlar.ALANLAR if a.sozlesme == alanlar.MUK and a.secenek_metni
}


#  Metinler şemadadır;  boşsa çizimden gelen alanın kuralı sona eklenir.
ACIKLAMA = {
    a.anahtar: gorunum.bilgi(a) for a in alanlar.ALANLAR if a.sozlesme == alanlar.MUK and gorunum.bilgi(a)
}
#  ÇİZİMDEN GELEN ALANLAR ( cizim/kopru.CIZIMDEN ):  boşsa değerin nereden
#  geldiği açıklamanın sonunda yazar — metin köprünün yanında tek yerde durur.


#  HESAP BÖLÜMÜ  →  onu besleyen GİRDİ GRUPLARI.
#  Revizyonda mühendis "halat bölümü kaldı, neyi değiştireceğim" diye
#  düşünür — girdi grubunun adıyla değil, HESAP BÖLÜMÜYLE.  Arayüz, sonuç
#  tablosundaki bir bölüme tıklandığında doğrudan onun girdilerini açar.
#  Eşleme burada durur çünkü hangi girdinin hangi hesaba girdiği MOTORUN
#  bilgisidir;  arayüzde tutulursa motor değişince sessizce bayatlar.
#
#  ANAHTAR BÖLÜMÜN KİMLİĞİDİR, NUMARASI DEĞİL.  Bir süre numara ( "4" )
#  kullanılıyordu ve bu iki yerden birden bozuktu:  numara projeye göre
#  kayıyor ( makine dairesi yoksa topraklama bir sıra öne geliyor ), bu
#  yüzden proje geneli bölümler hiç eşlenemiyordu;  ayrıca elektrik
#  bölümlerini eşlemek için "mukavemet 10 bölümdür, elektrik 11'den başlar"
#  varsayımını ikinci bir dosyaya gömmek gerekiyordu.  Kimlik bölümün
#  doğduğu yerde verilir ve hiç değişmez ( bkz. ortak/steps.Bolum ).
#
#  Sıra ÖNEM SIRASIDIR:  ilk grup bölümün ana girdilerini taşır, ikincisi o
#  bölümün kontrollerinden en az birini tek başına belirleyen ikinci gruptur.
#  İkiyle sınırlıdır — üç grup açmak akordeonu listeye çevirir ve aranan alan
#  yine kaybolur.  Listeler, motor kodundaki g[...] okumaları taranarak
#  çıkarılmıştır ve test_uygulama bunu her koşuda yeniden denetler.
BOLUM_GRUBU = {
    #  bölüm kimliği             asıl grup              ikinci grup
    "motor_gucu": ("Makine", "Asansör ve düzen"),
    "makine_konstruksiyonu": ("Makine", "Makine dairesi"),
    "kabin_alani": ("Kabin ve kapı", "Asansör ve düzen"),
    "aski_halatlari": ("Askı ve halatlar", "Makine"),
    "regulator_halati": ("Hız regülatörü",),
    "tahrik_yetenegi": ("Askı ve halatlar", "Makine"),
    "kabin_raylari": ("Raylar ve patenler", "Kabin ve kapı"),
    "agirlik_raylari": ("Raylar ve patenler", "Karşı ağırlık"),
    #  TAMPONLAR DEĞİL.  Bölüm tampon KUVVETLERİNİ ( Fkt · Fat ) verir ama
    #  bunlar kütle × g'dir;  tampon geometrisi ( baba yüksekliği · ezilme ·
    #  uzunluk ) kuvvete girmez.
    "kuyu_tabani": ("Raylar ve patenler", "Karşı ağırlık"),
    "tamponlar": ("Tamponlar", "Asansör ve düzen"),
    "siginma_alanlari": ("Kuyu ve katlar", "Tamponlar"),
}


def arayuz_alanlari():
    """Formun mukavemet payı ( JSON'a hazır ) — gruplar tasarım şemasından."""
    return {
        "gruplar": gorunum.form_gruplari(alanlar.MUK),
        "bolum_grubu": {no: list(gr) for no, gr in BOLUM_GRUBU.items()},
        #  MALZEME → ALIŞILMIŞ DERİNLİK.  Bir HESAP tablosu DEĞİL, formun
        #  başlangıç değeridir:  malzeme seçilince derinlik kutusu bu sayıyla
        #  dolar, mühendis üzerine yazabilir, hesap KUTUDAKİ sayıyı okur.
        "malzeme_derinligi": {
            r[0]: r[mukavemet_tablolari.MALZEME_SUTUN["derinlik"]]
            for r in mukavemet_tablolari.AGIRLIK_MALZEMESI
        },
        "hesaplanan": list(HESAPLANAN),
    }


def varsayilanlar():
    """Örnek projenin girdileri — arayüzün açılış değerleri."""
    g = {}
    for anahtar, _e, _b, tur, _s2, var in ALANLAR:
        if tur == "hesap":
            continue
        g[anahtar] = var
    g = tamamla(g)
    #  ÇİZİMDEN TÜRETİLENLER VARSAYILANDA BOŞ KALIR:  hesap varsayılanların
    #  üstüne girdiyi yazıp yeniden tamamlar;  burada doldurulsalardı
    #  varsayılan projenin kuyu dibinden, kasnaklarından türeyen sayı asıl
    #  girdide de kalırdı ( kuyu dibi değişse de kaide 870 ).
    for _k in gorunum.cizimden():
        g[_k] = None
    #  Karşı ağırlığın genişliği de:  boşsa ray arasından türer ( tamamla );
    #  varsayılanda dolu kalsaydı girilen ray arası onu hiç değiştirmezdi.
    g["agirlik_genisligi"] = None
    #  Kaynak işaretleri de gider:  kalsaydı kullanıcının girdiği α raporda
    #  "ÇİZİMDEN" yazardı ( işaret varsayılandan girdiye taşınırdı ).
    g.pop("_cizimden", None)
    g.pop("_kural", None)
    return g


def uygulama_varsayilanlari():
    """Uygulama formunun bütün varsayılanları:  mukavemet alanları ve ek
    ( elektrik … ) alanlar — uygulama_girdisi.varsayilanlar() bunu döner."""
    g = varsayilanlar()
    for a, _et, _b, _t, _s, v in EK_ALANLAR:
        g[a] = v
    return g


def _kural_isareti(g, anahtar, kural):
    """Boş alan kuralla dolduruldu:  rapor kaynağını "KURAL · …" yazar ( girilmiş
    sanılmasın — 13 Eki:  Gy ve h boşken raporda "GİRİŞ" yazıyordu ).  Çizimden
    gelenlerin işareti _cizimden gibi."""
    g["_kural"] = {**(g.get("_kural") or {}), anahtar: kural}


def tamamla(g):
    """Girdilerden türetilen alanları doldurur.

    kabin ağırlığı  boşsa ofis tablosundan
    karşı ağırlık   = kabin ağırlığı + q × beyan yükü
    kuyu boyu       = seyir × 1000 + son kat yüksekliği + kuyu dibi
    2. kablo tipi   kat kapısı tipinden
    """
    g = dict(g)
    if isinstance(g.get("sarilma_acisi"), str) and not g["sarilma_acisi"].strip():
        g["sarilma_acisi"] = None
    #  BOŞ KABİN KÜTLESİ:  girilmemişse ofis tablosundan doldurulur.
    #  Program aynı tabloyu avan tarafında da kullandığı için iki proje aynı asansöre aynı kütleyi
    #  verir.  Elle girilen değer HER ZAMAN önceliklidir.
    by = g.get("beyan_yuku")
    if g.get("kabin_agirligi") is None or (
        isinstance(g.get("kabin_agirligi"), str) and not g["kabin_agirligi"].strip()
    ):
        g["kabin_agirligi"] = ofis.bos_kabin_kutlesi(by)
        g["kabin_agirligi_kaynak"] = ofis.GK_KAYNAGI
    else:
        #  KAYNAK DEĞERDEN OKUNUR, GEÇMİŞTEN DEĞİL.  Ekran tablo değerini
        #  kutuya yazar;  sonraki her istek o sayıyı taşır.  Kaynak "boş mu
        #  geldi" diye belirlenince aynı girdi ilk hesapta "OFİS TABLOSU",
        #  sonrakilerde ( ve indirilen paftada ) "GİRİŞ" yazıyordu.  Değer bu
        #  beyan yükünün tablo değeriyse kaynak tablodur;  değilse girilmiştir.
        g["kabin_agirligi_kaynak"] = (
            ofis.GK_KAYNAGI if g.get("kabin_agirligi") == ofis.bos_kabin_kutlesi(by) else "GİRİŞ"
        )
    ka = g.get("kabin_agirligi")
    #  KARŞI AĞIRLIK DENGE ORANI OFİS SABİTİDİR.
    #  Bölüm 1 Ga'yı  P + q·Q  ile kurar;  karşı ağırlık da buradan aynı q
    #  ile kurulur.  "Beyan yükü / 2" diye çivilenseydi q = 0,60'ta aynı
    #  projede iki farklı karşı ağırlık oluşurdu — aynı fiziksel parçanın
    #  kütlesi her hesapta aynı olmalıdır.

    # Motor, tahrik ve tampon aynı doğrulanmış denge oranını kullanmalı.
    # Ham sözlüğü koru: reddedilen girdiler uyarılarda gösterilmeye devam eder.
    q = uygulama_sabitleri.sabitler(g.get("_ofis"))["q_denge"]
    if sayi_mi(ka) and sayi_mi(by):
        g["karsi_agirlik"] = ka + q * by
    _tavan, kd = alt_duraktan_tavana(g), g.get("kuyu_dibi")
    if _tavan is not None and sayi_mi(kd):
        g["kuyu_boyu"] = _tavan + kd
    #  KARŞI AĞIRLIĞIN GENİŞLİĞİ ( Gy ):  boşsa ağırlık rayları arasından
    #  ( DBGW − paten payı ), o da boşsa referans uygulama projesinin 960'ı
    #  ( tasarim/alanlar.AGIRLIK_PATEN_PAYI ).  Çizim DBGW'yi tersinden kurar
    #  ( boşsa Gy + pay ):  ikisi aynı çerçeveyi anlatır.  Yalnız BOŞ alan
    #  türer:  bozuk girdi ( "x" ) doğrulamaya kalır — eskiden sessizce
    #  kurala çevriliyor, hesap kuruluyordu ( 12 Eki ).
    if bos_mu(g.get("agirlik_genisligi")):
        dbgw = g.get("agirlik_ray_arasi")
        rayli = sayi_mi(dbgw) and dbgw > alanlar.AGIRLIK_PATEN_PAYI
        g["agirlik_genisligi"] = (
            dbgw - alanlar.AGIRLIK_PATEN_PAYI if rayli else alanlar.AGIRLIK_GENISLIGI_YEDEK
        )
        _kural_isareti(
            g,
            "agirlik_genisligi",
            f"DBGW − {alanlar.AGIRLIK_PATEN_PAYI:g}" if rayli else "DBGW boş — referans projenin ölçüsü",
        )
    #  2. bükülgen kablo kat kapısı tipinden türetilir
    g["kablo_tipi_2"] = mukavemet_tablolari.kapi_kablosu(g.get("kat_kapisi_tipi"))
    #  ÇİZİMDEN GELEN GİRDİLER ( cizim/kopru.CIZIMDEN ):  boş bırakılmışsa
    #  ( None ) değer çizimin geometrisinden türetilir — askı kaçıklığı xs,
    #  D2 · Ds, kabin tamponu kaidesi, sarılma açısı α.  Hesap ile çizim aynı
    #  sayıyı kullanır;  türetilemezse boş kalır ( doğrulama "boş bırakılamaz"
    #  der, α'da tahrik kontrolleri HESAP EKSİK ).  Çizim uygulama alanlarını
    #  da ister ( kuyu genişliği, makine dairesi … ):  motor doğrudan
    #  çağrıldığında girdide yoksa uygulama sözleşmesinin varsayılanları —
    #  sabit tablo;  girdi.varsayilanlar() buraya döner, döngü olurdu.

    #  KABİN PATEN ARASI ( h ):  boşsa kabin iç yüksekliğinden — şase kabini
    #  sarar ( tasarim/alanlar.KABIN_PATEN_PAYI ).  Çizimden türetilenlerden
    #  önce:  kabinin düşey kotları ona dayanır.  Girilen değer olduğu gibi
    #  kalır ( kiriş tavana giriyorsa çizim gereken paten arasını söyler ),
    #  bozuk girdi doğrulamaya kalır.
    if bos_mu(g.get("kabin_paten_arasi")):
        kh = kopru.varsayilan_deger(g, "kabin_ic_yuksekligi")
        if sayi_mi(kh):
            g["kabin_paten_arasi"] = kh + alanlar.KABIN_PATEN_PAYI
            _kural_isareti(g, "kabin_paten_arasi", f"kabin iç yüksekliği + {alanlar.KABIN_PATEN_PAYI:g}")
    _cd = kopru.cizimden({**{a[0]: a[5] for a in EK_ALANLAR}, **g})
    g.update(_cd)
    #  KAYNAK İŞARETİ:  çizimden gelen değer raporda "ÇİZİMDEN" yazar ( girilmiş
    #  sanılmasın ).  Anahtar → kuralı.
    if _cd:
        g["_cizimden"] = {**(g.get("_cizimden") or {}), **{k: kopru.CIZIMDEN[k] for k in _cd}}
    #  ESKİ BİÇİM:  makine yükünün yolu bir zamanlar ONAY KUTUSUYDU ve
    #  True / "EVET" olarak kaydediliyordu.  Eski .uygulama dosyaları bu
    #  değeri taşır;  seçime çevrilmezse
    #  doğrulama "geçersiz seçim — True" deyip projeyi hiç açmaz.
    _yy = g.get("makine_raya_biniyor")
    if _yy is not None and _yy not in mukavemet_tablolari.MAKINE_YUK_YOLU:
        g["makine_raya_biniyor"] = (
            mukavemet_tablolari.MAKINE_YUK_YOLU[1]
            if mukavemet_tablolari.makine_raya_mi(_yy)
            else mukavemet_tablolari.MAKINE_YUK_YOLU[0]
        )
    return g


def kanal_acilari(g, O):
    """( γ , β , γ_girildi , β_girildi )  —  proje değeri varsa o, yoksa ofis.

    BÖLÜM 4 ( Nequiv ) İLE BÖLÜM 6 ( tahrik ) AYNI KAYNAKTAN OKUR.  İki yerde
    ayrı ayrı okunsaydı projeye girilen açı yalnız birine işler, pafta kendi
    içinde çelişirdi.
    """
    sekil = g.get("kanal_sekli")
    pg, pb = g.get("kasnak_gama"), g.get("kasnak_beta")
    g_var, b_var = sayi_mi(pg), sayi_mi(pb)
    gv = float(pg) if g_var else O["kanal_gama_v"]
    gyd = float(pg) if g_var else O["kanal_gama_yd"]
    bt = float(pb) if b_var else O["kanal_beta"]
    return (
        mukavemet_tablolari.kanal_acisi(sekil, gv, gyd),
        mukavemet_tablolari.kanal_beta(sekil, bt),
        g_var,
        b_var,
    )


def sistem_verimi(g):
    """η ve girilip girilmediği:  projeye girilen verim, yoksa makine tipinden
    ofis değeri.  Mukavemet ve elektrik köprüsü AYNI değeri buradan okur."""
    e = g.get("makine_verimi")
    if sayi_mi(e):
        return e, True

    return uygulama_sabitleri.verim(uygulama_sabitleri.sabitler(g.get("_ofis")), g.get("makine_tipi")), False


def dogrula(g):
    """Girdi sözlüğünü denetler; hata metinleri listesi döner ( boşsa temiz ).
    Denetimler sırayla çalışır ( _DENETIMLER );  her biri ( g, atla ) alır —
    atla:  bu projede uygulanmayan alanlar."""
    #  Hesaba girmeyen, ekranda da görünmeyen bir alan projeyi durdurmamalı.
    atla = uygulanmayan(g)
    hata = []
    for denetim in _DENETIMLER:
        hata += denetim(g, atla)
    #  OFİS STANDARDI  ( Sabitler sekmesi ).  Aralık dışı değer varsayılanla
    #  değiştiriliyor ve bunu hiçbir yer söylemiyordu;  artık hesap durur.
    return hata + uygulama_sabitleri.ofis_hatalari(g.get("_ofis"))


def _alan_turleri(g, atla):
    """Boş, geçersiz seçim, sayı değil, negatif."""
    hata = []
    for anahtar, etiket, birim, tur, secenekler, _v in ALANLAR:
        if tur == "hesap" or anahtar in atla:
            continue
        d = g.get(anahtar)
        ad = f"{etiket} ({birim})" if birim not in ("—", "") else etiket
        if d is None or d == "":
            if anahtar not in OPSIYONEL_ALANLAR:
                hata.append(f"{ad}: boş bırakılamaz.")
            continue
        if secenekler is not None and d not in secenekler:
            hata.append(f"{ad}: geçersiz seçim — {d!r}. Seçenekler: {', '.join(str(x) for x in secenekler)}.")
            continue
        if tur == "sayi" and not sayi_mi(d):
            hata.append(f"{ad}: sayı olmalı ( {d!r} girildi ).")
        elif tur == "sayi" and d < 0 and anahtar not in ISARETLI_ALANLAR:
            hata.append(f"{ad}: negatif olmayan bir sayı olmalı ( {d!r} girildi ).")
    return hata


def _bolenler(g, atla):
    """SIFIR OLAMAYACAK ALANLAR.  Bunlar hesapta BÖLEN olarak geçer;  sıfır
    girilirse motor ZeroDivisionError ile çöker.  Kullanıcıya çökme değil
    neyi düzelteceği söylenmeli."""
    return [
        f"{ALAN[anahtar][1]}: sıfır olamaz — bu değer hesapta bölen olarak kullanılır."
        for anahtar in BOLEN_ALANLAR
        if anahtar not in atla and sayi_mi(g.get(anahtar)) and g.get(anahtar) == 0
    ]


def _tablo_butunlugu(g, atla):
    """TABLO BÜTÜNLÜĞÜ.  Bir seçenek listede var ama tablosunda karşılığı
    eksikse hesap sessizce yanlış sonuç vermemeli  ( ör. NPU tablosunda
    240 · 280 · 300 için atalet yarıçapı yoktur )."""
    hata = []
    for anahtar, oku, ne in TABLO_GEREKLI:
        d = g.get(anahtar)
        if anahtar in atla or d is None or d == "":
            continue
        eksik = [a for a, f in oku if f(d) is None]
        if eksik:
            hata.append(
                f"{ALAN[anahtar][1]}: seçilen '{d}' için tabloda "
                f"{ne} eksik ( {', '.join(eksik)} ). Başka bir değer seçin."
            )
    return hata


def _acil_frenleme(g, atla):
    """ACİL FRENLEME YAVAŞLAMASININ İKİ SINIRI DA VARDIR.
    Üst sınır TS EN 81-20'den:  en çok 1 gn.
    ALT sınır TS EN 81-50 m.5.11.2.2.2'den:  "In no case shall the rate of
    retardation to consider be less than … 0,5 m/s²".  Bu sınır önce
    denetlenmiyordu;  küçük bir a atalet kuvvetini küçültür, T1/T2 oranını
    iyileştirir ve tahrik yeteneğini olduğundan İYİ gösterir — emniyetsiz."""
    hata = []
    ivme = g.get("acil_frenleme_a")
    if sayi_mi(ivme) and ivme > 9.81:
        hata.append(
            f"Acil frenleme yavaşlaması ({ivme} m/s²) TS EN 81-20 gereği 1 gn = 9,81 m/s² değerini aşamaz."
        )
    if sayi_mi(ivme) and ivme < ACIL_FRENLEME_ASGARI:
        hata.append(
            f"Acil frenleme yavaşlaması ({ivme} m/s²) TS EN 81-50 "
            f"m.5.11.2.2.2 gereği {ACIL_FRENLEME_ASGARI} m/s²'nin "
            "altına inemez. ( Tampon kursu kısıtlıysa daha küçük bir "
            "değer ancak tamponun tasarım yavaşlamasıyla birlikte "
            "gerekçelendirilebilir. )"
        )
    return hata


def _kasnak_caplari(g, atla):
    """EN KÜÇÜK ÇAP, ORTALAMADAN BÜYÜK OLAMAZ.
    Ds "saptırma kasnaklarının EN KÜÇÜK çapı", D2 ise ORTALAMASIDIR;
    tanım gereği Ds ≤ D2.  İki kutu karıştırılınca ( ya da "en küçük"
    "en büyük" diye okununca ) m.5.5.2.1'in Ds/dh ≥ 40 kontrolü
    HÜKÜMDEN SESSİZCE DÜŞÜYORDU:  D2 = 240 · dh = 8 ile Ds/dh = 30
    kalması gerekirken, Ds = 600 girilince satır kayboluyor ve bölüm o
    kontrolü geçmiş sayılıyordu — emniyetsiz yön."""
    _d2, _ds = g.get("saptirma_kasnak_capi"), g.get("saptirma_kasnak_min_capi")
    if sayi_mi(_d2) and sayi_mi(_ds) and float(_ds) > float(_d2):
        return [
            f"{ALAN['saptirma_kasnak_min_capi'][1]} ({_ds} mm), "
            f"saptırma kasnaklarının ORTALAMA çapından ({_d2} mm) "
            "büyük olamaz — Ds en küçük çaptır.  İki değer ters "
            "girilmiş olabilir."
        ]
    return []


def _ray_sayilari(g, atla):
    """KABİN VE KARŞI AĞIRLIK EN AZ İKİ RAYLA KILAVUZLANIR.
    TS EN 81-20 m.5.7.1.1:  "The car, counterweight or balancing weight
    shall each be guided by AT LEAST TWO rigid steel guide rails."
    Tek ray kabul ediliyordu;  hesap çalışıyor ( n bölen olarak geçer ve
    ray kuvvetleri iki katına çıkar ) ama standarda aykırı bir düzen
    paftaya olağan bir seçenek gibi yazılıyordu."""
    hata = []
    for _ra in ("kabin_ray_sayisi", "agirlik_ray_sayisi"):
        _n = g.get(_ra)
        if sayi_mi(_n) and 0 < float(_n) < 2:
            hata.append(
                f"{ALAN[_ra][1]}: en az 2 olmalıdır "
                f"( {_n} girildi ).  TS EN 81-20 m.5.7.1.1 kabin ve "
                "karşı ağırlığın en az iki rijit çelik kılavuz rayla "
                "kılavuzlanmasını ister."
            )
    return hata


def _kabin_alt_konumu(g, atla):
    """KABİNİN EN ALT KONUMU KUYU DİBİNİN İÇİNDE KALMALIDIR.
    a_dip = baba + ( tampon boyu − ezilme ) , kabinin TAM EZİLMİŞ tamponun
    üstünde durduğu kot.  Bu kot kuyu dibi derinliğini aşarsa kabinin en
    alt noktası ALT DURAK DÖŞEMESİNİN ÜSTÜNDE kalır — geometrik olarak
    olanaksızdır.  Dip açıklıklarının hepsi "büyükse iyidir" diye
    bakıldığı için böyle bir düzen sığınma bölümünü GEÇİYORDU
    ( KY = 800 mm · baba = 1.000 mm → a_dip = 1.010 mm , hüküm UYGUN )."""
    _ky, _bb = g.get("kuyu_dibi"), g.get("kabin_tampon_baba")
    _tb2, _te2 = g.get("kabin_tampon_boyu"), g.get("kabin_tampon_ezilme")
    if all(sayi_mi(x) for x in (_ky, _bb, _tb2, _te2)):
        _adip = float(_bb) + (float(_tb2) - float(_te2))
        if _adip >= float(_ky):
            return [
                f"Kabinin tampona oturduğu kot ({_adip:.0f} mm = baba "
                f"{_bb} + tampon boyu {_tb2} − ezilme {_te2}), kuyu dibi "
                f"yüksekliğinden ({_ky} mm) küçük olmalıdır — aksi hâlde "
                "kabinin en alt noktası alt durak döşemesinin üstünde kalır."
            ]
    return []


def _tampon_ezilmesi(g, atla):
    """TAMPON KENDİ BOYUNDAN FAZLA EZİLEMEZ.
    Kuyu dibindeki bütün açıklıklar tek bir sayıdan türer:
        a_dip = baba + ( tampon boyu − ezilme )
    yani kabinin, TAM EZİLMİŞ tamponun üstünde durduğu kot.  Ezilme boyu
    aşarsa parantez negatife döner ve a_dip fiziksel anlamını yitirir;
    ondan türeyen a · a.1 · a.2 · b açıklıkları ile Ç.4 sığınma hacmi de
    sessizce bozulur.  Denetimde 100 mm'lik tampona 5.000 mm ezilme
    girilebiliyor ve a_dip = −3.900 mm çıkıyordu — hiçbir uyarı yoktu."""
    hata = []
    _tb, _te = g.get("kabin_tampon_boyu"), g.get("kabin_tampon_ezilme")
    if sayi_mi(_tb) and sayi_mi(_te) and float(_te) > float(_tb):
        hata.append(
            f"{ALAN['kabin_tampon_ezilme'][1]} ({_te} mm), tamponun "
            f"kendi boyunu ({_tb} mm) aşamaz — tampon en çok kendi "
            "boyu kadar kısalabilir.  Kuyu dibi açıklıkları ve Ç.4 "
            "sığınma hacmi bu farktan türer."
        )
    _ab = g.get("agirlik_tampon_boyu")
    if _ab is None or (isinstance(_ab, str) and not _ab.strip()):
        _ab = _tb
    _ae = g.get("agirlik_tampon_ezilme")
    if sayi_mi(_ab) and sayi_mi(_ae) and float(_ae) > float(_ab):
        hata.append(
            f"{ALAN['agirlik_tampon_ezilme'][1]} ({_ae} mm), tamponun "
            f"kendi boyunu ({_ab} mm) aşamaz — tampon en çok kendi boyu kadar kısalabilir."
        )
    return hata


def _fiziksel_sinirlar(g, atla):
    """ADET · POZİTİFLİK · AÇI  —  fiziksel sınırlar."""
    hata = []
    for anahtar in TAM_SAYI_ALANLARI:
        d = g.get(anahtar)
        if sayi_mi(d) and float(d) != int(d):
            hata.append(f"{ALAN[anahtar][1]}: adet tam sayı olmalıdır ( {d} girildi ).")
    nh = g.get("halat_adedi")
    if sayi_mi(nh) and nh < 2:
        hata.append("Askı halatı adedi en az 2 olmalıdır (TS EN 81-20 m.5.5.1.3).")
    for anahtar in POZITIF_ALANLAR:
        d = g.get(anahtar)
        if anahtar in atla:
            continue
        if anahtar in ALAN and d is not None and (not sayi_mi(d) or d <= 0):
            hata.append(f"{ALAN[anahtar][1]}: sıfırdan büyük olmalıdır ( {d} girildi ).")
    for anahtar, (alt, ust) in ACI_ALANLARI.items():
        d = g.get(anahtar)
        if d is not None and (not sayi_mi(d) or not (alt <= d <= ust)):
            hata.append(f"{ALAN[anahtar][1]}: {alt}° ile {ust}° arasında olmalıdır ( {d} girildi ).")
    return hata


def _sarilma_acisi(g, atla):
    """SARILMA AÇISI KANALIN SARIM SAYISINA GÖRE FİZİKSEL OLMALI.

    Tek sarımda halat tahrik kasnağını en çok yarım tur sarar ( ≤ 180° ).
    Çift sarımda iki kez geçer ve toplam açı yarım turu AŞAR ( > 180° );
    180° ve altı bir değer tek sarıma aittir — büyük ihtimalle tek geçişin
    açısı girilmiştir.  Bu kontrol eskiden yalnız motorun içindeydi:  motor
    bölümü "uygun değil" sayıyor ama altındaki üç yük durumuna imkânsız
    açıyla "UYGUN" basıyordu ( tek sarım · 300° ).  Açı kanal şekline
    bağlı olduğundan alanın kendi aralığıyla ( 1–360° ) denetlenemez;
    burada, iki alan birlikte görülürken reddedilir."""
    _aci, _kanal = g.get("sarilma_acisi"), g.get("kanal_sekli")
    if not (sayi_mi(_aci) and 1 <= _aci <= 360 and mukavemet_tablolari.kanal_turu(_kanal) is not None):
        return []
    if (mukavemet_tablolari.kanal_gecis_sayisi(_kanal) or 1) > 1:
        if _aci <= 180:
            return [
                f"Sarılma açısı α ({_aci:g}°) çift sarımlı kanalda 180°'yi "
                "aşmalıdır. Çift sarımda halat tahrik kasnağının üzerinden "
                "iki kez geçer; 180° ve altı bir açı tek sarıma aittir. "
                "İki geçişin TOPLAM sarılma açısını girin."
            ]
    elif _aci > 180:
        return [
            f"Sarılma açısı α ({_aci:g}°) tek sarımlı kanalda 180°'yi "
            "aşamaz — halat tahrik kasnağını en çok yarım tur sarar. "
            "Çift sarım kullanılıyorsa kanal şeklini ona göre seçin."
        ]
    return []


def _kanal_bicimi(g, atla):
    """SERTLEŞTİRİLMEMİŞ V KANALIN ALT KESİLMESİ OLMALIDIR.

    TS EN 81-50 m.5.11.2.3.1.2:  "Where the groove has not been submitted
    to an additional hardening process, in order to limit the
    deterioration of traction due to wear, an undercut is necessary."
    Normatif gövdededir, not değildir.  Bu birleşim eskiden yalnız bir not
    alıyor ve sayısal kontroller geçerse tahrik bölümü "UYGUNDUR" diyordu
    ( 576 senaryonun 142'sinde ).  Seçim SESSİZCE "sertleştirilmiş"e
    çevrilmez — o, gerçek kasnağın özelliğini değiştirmek olurdu.

    γ ve β STANDARDIN SINIRLARI İÇİNDE OLMALIDIR.  Aynı sınırlar ofis
    sabitleri için sabitler.ARALIK'ta duruyor;  proje girdisi onları
    atlayamaz.  γ'nın ALT sınırı kanal türüne göre değişir ( V 35° ·
    yarım daire 25° ), üst sınır bir kanal açısı olarak 90°'dir."""
    hata = []
    _kanal = g.get("kanal_sekli")
    if mukavemet_tablolari.kanal_turu(_kanal) == "V" and g.get("kanal_isleme") == "Sertleştirilmemiş":
        hata.append(
            "Alt kesilmesiz V kanal sertleştirilmemiş olamaz — TS EN 81-50 "
            "m.5.11.2.3.1.2 sertleştirilmemiş V kanalda aşınmadan doğan tahrik "
            "kaybını sınırlamak için ALT KESİLME ister. Kanal ya "
            "sertleştirilmiş olmalı ya da 'Altı Kesik V Kanal' seçilmelidir."
        )
    _pg, _pb = g.get("kasnak_gama"), g.get("kasnak_beta")
    if sayi_mi(_pg):
        _alt = (
            mukavemet_tablolari.GAMA_ASGARI_U
            if mukavemet_tablolari.kanal_yarim_daire_mi(_kanal)
            else mukavemet_tablolari.GAMA_ASGARI_V
        )
        if not (_alt <= _pg <= mukavemet_tablolari.GAMA_AZAMI):
            hata.append(
                f"Kasnak kanal açısı γ = {_pg}° sınırların dışında — seçilen "
                f"kanalda {_alt:.0f}° ≤ γ ≤ {mukavemet_tablolari.GAMA_AZAMI:.0f}° olmalıdır "
                "( TS EN 81-50 m.5.11.2.3.1 )."
            )
    if sayi_mi(_pb):
        if not (0 < _pb <= mukavemet_tablolari.BETA_AZAMI):
            hata.append(
                f"Kanal alt kesme açısı β = {_pb}° sınırların dışında — "
                f"0° < β ≤ {mukavemet_tablolari.BETA_AZAMI:.0f}° olmalıdır "
                "( TS EN 81-50 m.5.11.2.3.1 )."
            )
        elif not mukavemet_tablolari.kanal_alti_kesik_mi(_kanal):
            hata.append(
                f"Alt kesme açısı β girildi ama seçilen kanalın ( {_kanal} ) "
                "alt kesilmesi yoktur — ya kutuyu boş bırakın ya da altı "
                "kesik bir kanal seçin."
            )
    return hata


def _opsiyonel_alanlar(g, atla):
    """OPSİYONEL ALANLARIN POZİTİFLİK VE FİZİKSEL SINIRLARI
    Boş bırakılabilirler;  ama girilmişse pozitif ve fiziksel olmalıdır.
    paten_balata_boyu = 0 girildiğinde motor bunu sessizce türetilene
    çeviriyor, 0,001 mm girildiğinde ise formül paydası pozitif kaldığı
    için mikroskobik balatayla "UYGUN" çıkıyordu.
    ( 20 mm alt sınırı standart maddesi değil;  yazılımsal koruma, sınır
    değer kontrolü / sanitization ve fiziksel tutarlılık kalkanıdır. )"""
    hata = []
    pbb = g.get("paten_balata_boyu")
    if pbb is not None and pbb != "":
        if not sayi_mi(pbb) or pbb <= 0:
            hata.append(f"{ALAN['paten_balata_boyu'][1]}: sıfırdan büyük olmalıdır ( {pbb!r} girildi ).")
        elif pbb < 20:
            hata.append(
                f"Paten balatası uzunluğu ({pbb:g} mm) fiziksel değil — balata boyu en az 20 mm olmalıdır."
            )
        else:
            kpa = g.get("kabin_paten_arasi")
            if sayi_mi(kpa) and pbb >= kpa:
                hata.append(
                    f"Paten balatası uzunluğu ({pbb:g} mm) kabin patenler arası mesafeden ({kpa:g} mm) küçük olmalıdır."
                )
    gdk = g.get("guvenlik_devreye_kuvvet")
    if gdk is not None and gdk != "" and (not sayi_mi(gdk) or gdk <= 0):
        hata.append(f"{ALAN['guvenlik_devreye_kuvvet'][1]}: sıfırdan büyük olmalıdır ( {gdk!r} girildi ).")
    return hata


def _katalog_verileri(g, atla):
    """KATALOG HALAT VERİSİ ve Tst — hepsi opsiyoneldir, girilirse MAKUL olmalı.
    Kopma yükü alanı kN'dir:  katalog "31,5 kN" der, projeci 31500 yazarsa
    güvenlik katsayısı 1000 kat büyür ve HER tasarım "UYGUN" görünürdü.
    Üst sınır o hatayı yakalar."""
    hata = []
    for _ad, _alt, _ust in (
        ("halat_birim_kutle", 0.02, 5.0),
        ("kablo_birim_kutle", 0.05, 20.0),
        ("halat_kopma_kN", 5.0, 2000.0),
        ("reg_halat_birim_kutle", 0.02, 5.0),
        ("reg_halat_kopma_kN", 5.0, 2000.0),
        ("makine_tst", 100.0, 100000.0),
        #  Sabitler'deki ofis verimiyle aynı aralık.
        ("makine_verimi", 0.1, 1.0),
    ):
        _v = g.get(_ad)
        if _v is None or _v == "":
            continue
        if not sayi_mi(_v) or not (_alt <= _v <= _ust):
            hata.append(f"{ALAN[_ad][1]}: {_alt} - {_ust} aralığında olmalıdır ( {_v!r} girildi ).")
    return hata


def _kaide_geometrisi(g, atla):
    """MAKİNE KAİDESİ GEOMETRİSİ.  Bölüm 2 basit kiriş modelidir:  açıklığı L
    olan kirişte tekil yük, A mesnedinden X = L − mesnet payı uzaklıktadır.
    Model 0 < X < L gerektirir.  L mesnet payından küçükse X NEGATİF çıkar;
    o zaman moment ve gerilme de negatif olur ve "σe ≤ σem" karşılaştırması
    bunu SESSİZCE "uygun" sayar ( −5.350 N/mm² ≤ 130 doğrudur ).  Sayı
    fiziksel değildir;  geometri baştan reddedilmelidir."""
    L = g.get("yan_yatak_boyu")
    pay = (g.get("_ofis") or {}).get("yan_yatak_L_X")
    if not sayi_mi(pay):
        pay = uygulama_sabitleri.VARSAYILAN["yan_yatak_L_X"]
    #  Yükün yeri çizimden geldiyse ( program hesabı ) mesnet payı kullanılmaz.
    _x_ciz = "makine_yuku_x" in (g.get("_cizimden") or {}) and sayi_mi(g.get("makine_yuku_x"))
    if "yan_yatak_boyu" not in atla and not _x_ciz and sayi_mi(L) and sayi_mi(pay) and L - pay <= 0:
        return [
            f"Yan yatak boyu ({L} mm) mesnet payından ({pay} mm) büyük "
            "olmalıdır. Makine kaidesi hesabı, açıklığı L olan basit "
            f"kirişte yükün mesnetten X = L − {pay} uzaklıkta olduğunu "
            "kabul eder; X ≤ 0 fiziksel değildir."
        ]
    #  ( RAY NARİNLİĞİ hata değil uyarıdır — bkz. uyarilar.  "Halat arası
    #    tahrik kasnağı çapından küçük olamaz" doğrulaması KALDIRILDI.  O
    #    kural, α'yı Ra'dan türeten geometrik modelin kendisini korumak
    #    içindi:  Ra < 2·R1'de pay negatife düşüyor ve α 180°'yi aşıyordu.
    #    α artık doğrudan beyan ediliyor ve kendi aralığında ( 1° – 360° )
    #    denetleniyor;  Ra diye bir girdi kalmadı. )
    return []


def _verim_siniri(g, atla):
    """SİSTEM VERİMİ  η  FİZİKSEL OLMALI             0 < η ≤ 1

    Δη kalktığı için η artık kendi başına negatife düşemez;  bu kalkan
    yine de durur, çünkü ofis sabiti ekrandan elle girilir ve ARALIK
    ( 0,1 - 1 ) atlanırsa N = Gmax·v/(η·102) sıfıra bölünür.
    Projeye verim girilmişse aralığını katalog denetimi bekler;  ofis
    değeri o projede kullanılmadığı için burada aranmaz."""
    _etap, _eta_girildi = sistem_verimi(g)
    if not _eta_girildi and not (sayi_mi(_etap) and 0 < _etap <= 1):
        return [
            f"Toplam sistem verimi η = {_etap} fiziksel değil — 0 < η ≤ 1 "
            f"olmalı ( '{g.get('makine_tipi')}' makine ). Sabitler sekmesinden düzeltin."
        ]
    return []


def _halat_boyu(g, atla):
    """HALAT BOYU POZİTİF OLMALI  —  tampon / paten yığını kuyuya sığmalı.

    lh = ( kuyu boyu − yığın ) / 1000 + pay.  Yığın kuyu boyunu aşarsa
    halat boyu NEGATİF çıkıyor ( 30 m paten arasında −4,82 m ) ve halat
    ağırlığı Gh = −5,13 kg oluyor.  Negatif ağırlık yükten DÜŞÜLÜYOR:
    motor gücünü azaltıyor, halat güvenlik katsayısını yükseltiyor —
    yani imkânsız bir geometri hesabı İYİLEŞTİRİYORDU.

    ( REGÜLATÖR SÜRTÜNME KATSAYISI artık asansör bazında sorulmaz:  ofis
    sabitidir ( sabitler.reg_mu ) ve üst sınırını ARALIK denetler. )"""
    _y = {
        a: g.get(a)
        for a in (
            "agirlik_tampon_baba",
            "agirlik_carpma_arasi",
            "agirlik_tampon_ezilme",
            "agirlik_paten_arasi",
            "kabin_paten_arasi",
        )
    }
    _kb = g.get("kuyu_boyu")
    if not (sayi_mi(_kb) and all(sayi_mi(v) for v in _y.values())):
        return []
    _yigin = (
        _y["agirlik_tampon_baba"]
        + _y["agirlik_carpma_arasi"]
        - _y["agirlik_tampon_ezilme"]
        + _y["agirlik_paten_arasi"]
        + _y["kabin_paten_arasi"]
    )
    if _kb - _yigin > 0:
        return []
    return [
        f"Tampon / paten yığını ({_yigin:g} mm) kuyu boyundan "
        f"({_kb:g} mm) büyük — halat boyu negatif çıkar. "
        "Toplama giren ölçüler:  ağırlık tampon babası "
        f"{_y['agirlik_tampon_baba']:g} + ağırlık çarpma arası "
        f"{_y['agirlik_carpma_arasi']:g} − ağırlık tampon ezilmesi "
        f"{_y['agirlik_tampon_ezilme']:g} + ağırlık paten arası "
        f"{_y['agirlik_paten_arasi']:g} + kabin paten arası "
        f"{_y['kabin_paten_arasi']:g}."
    ]


#  dogrula'nın denetimleri — iletiler bu sırayla çıkar
_DENETIMLER = (
    _alan_turleri,
    _bolenler,
    _tablo_butunlugu,
    _acil_frenleme,
    _kasnak_caplari,
    _ray_sayilari,
    _kabin_alt_konumu,
    _tampon_ezilmesi,
    _fiziksel_sinirlar,
    _sarilma_acisi,
    _kanal_bicimi,
    _opsiyonel_alanlar,
    _katalog_verileri,
    _kaide_geometrisi,
    _verim_siniri,
    _halat_boyu,
)


#  Sarılma açısı girilmediğinde paftanın başına basılan uyarı.  Sabittir,
#  çünkü uygulama projesi ( motor/uygulama/uygulama_hesabi.py ) aynı eksikliği bir de
#  kısa "HESAP EKSİK" satırıyla yazmasın diye bu metni arar.
ALFA_UYARI = (
    "SARILMA AÇISI α GİRİLMEDİ ve çizimden de bulunamadı: çizim açıyı "
    "yalnız sabitse verir (iki iniş düşey ya da saptırma kasnağı). Halat "
    "ağırlık tarafında eğik iniyorsa (kuyu üstü planında HALAT SAPMASI) "
    "açı ağırlığın konumuyla değişir — kasnak aralığını düzeltip halatı "
    "düşey indirin ya da açıyı girin. Çift sarımda (çizim tek sarım "
    "çizer) ya da çizim kurulamıyorsa açıyı girin (tek sarımda en çok "
    "180°, çift sarımda 180°–360°). Açı belli olana kadar tahrik "
    "yeteneğinin dört sınırı hesaplanmaz ve bölüm HESAP EKSİK kalır."
)


def uyarilar(g):
    """Hesabı DURDURMAYAN ama paftaya yazılması gereken uyarılar.

    ``dogrula`` hesabı imkânsız kılan girdileri reddeder;  burası hesabın
    yapılabildiği ama bir kontrolün DÜŞECEĞİ durumları bildirir.  İkisi ayrı
    kanaldır:  biri projeyi hiç hesaplatmaz, öteki sonucu "uygun değil"
    yapar ve sebebini yazar.
    """
    uyari = []
    #  ------------------------------------------------------------------
    #  SARILMA AÇISI ZORUNLU BEYANDIR ( bkz. mukavemet.ALFA_YOK ).
    #  Girilmemişse tahrik yeteneğinin dört sınırı hesaplanmaz;  proje
    #  "uygundur" çıkamaz ve sebep burada, açıkça söylenir.
    #  ------------------------------------------------------------------
    if g.get("sarilma_acisi") in (None, ""):
        uyari.append(ALFA_UYARI)
    #  ------------------------------------------------------------------
    #  MAKİNE DAİRESİZ TESİSTE MAKİNENİN YÜKÜ BİR YERE GİDER.
    #  TS EN 81-20 m.5.7.2.3.7 makine raya bağlıysa EK YÜK DURUMLARI ister.
    #  Kutu işaretsizse program yükü BİNA YAPISINA verilmiş kabul eder ve
    #  raya yalnız ofis kabulü olan ufak donanımı ( 150 N ) koyar.  Bu bir
    #  KABULDÜR ve sessiz kalmamalıdır:  makine gerçekten raylara biniyorsa
    #  ray ve kuyu tabanı yükü olduğundan küçük çıkar.
    #  ------------------------------------------------------------------
    #  Makine dairesi VARKEN seçim uygulanmaz ( makine kendi kaidesinde, yükü
    #  bölüm 2'de ):  eskiden "YOK SAYILDI" uyarısı basılırdı.  Karar 3'ten
    #  beri varsayılan "Kılavuz raylara" ve alan makine daireli formda
    #  gizlidir ( kullanıcı seçemez ):  uyarı her makine daireli projede
    #  anlamsız çıkardı.
    if evet_mi(g.get("mk_yok")) and not mukavemet_tablolari.makine_raya_mi(g.get("makine_raya_biniyor")):
        uyari.append(
            "MAKİNE YÜKÜ BİNA YAPISINA AKTARILIYOR — makine dairesiz ( MRL ) "
            "sistemde makinenin yükü kuyu üstü kirişe, duvara ya da konsola "
            "iner ve bu yapı TS EN 81-20 m.5.2.1.8.1 ile Ek E uyarınca İNŞAAT "
            "PROJESİNDE hesaplanır;  paftada verilen yük o hesabın girdisidir. "
            "Makinenin ya da altındaki kirişin uçları kılavuz raylara "
            "bağlıysa 'Makine yükünün yolu' alanından 'Kılavuz raylara' "
            "seçilmelidir — m.5.7.2.3.7 o durumda ek yük durumları ister."
        )
    return uyari + _narinlik_uyarilari(g) + _tampon_ezilmesi_uyarisi(g)


def _narinlik_uyarilari(g):
    """ω tablosu YALNIZ 20 ≤ λ ≤ 250 arasında tanımlıdır.  Üst sınırın
    dışında ω yoktur;  motor bunu ham bir Python hatasıyla ( None ile
    çarpım ) bildiriyordu ve kullanıcı hangi alanın sorunlu olduğunu
    göremiyordu.  50 x 50 x 5 rayda sınır 3.845 mm'dir — varsayılan
    3.000 mm konsol aralığına yakın, yani gerçekçi bir girdiyle
    karşılaşılıyordu.

    ALT SINIRDA HATA YOKTUR:  λ < 20 burkulmanın belirleyici olmadığı
    bölgedir, motor λ'yı 20'ye yuvarlar ( makine kaidesinde de öyle ).
    BURKULMA YALNIZ GÜVENLİK TERTİBATI ÇALIŞTIĞINDA VARDIR.
    ω, Ek C.2.1.2'de ( güvenlik tertibatının çalışması ) geçer;  C.2.2 ve
    C.2.3 normal çalışma hâlleridir ve orada Fv = Mg·gn + Fp'dir, ω yoktur.
    Kabinde tertibat her zaman vardır;  karşı ağırlıkta ise SEÇİME bağlıdır.
    Tertibat yoksa rayı sıkıştıran Fk de yoktur, λ > 250 bir şeyi
    düşürmez — orada uyarmak yanlış alarm olurdu."""
    uyari = []
    _agirlik_gt = str(g.get("agirlik_guvenlik_tertibati") or "Yok") != "Yok"
    for ray_alan, konsol_alan, ne, _gerekli in (
        ("kabin_ray_profili", "kabin_konsol_arasi", "Kabin", True),
        ("agirlik_ray_profili", "agirlik_konsol_arasi", "Karşı ağırlık", _agirlik_gt),
    ):
        if not _gerekli:
            continue
        prof, l = g.get(ray_alan), g.get(konsol_alan)
        #  NARİNLİK EN KÜÇÜK ATALET YARIÇAPINDAN ÖLÇÜLÜR  ( m.5.10.3:
        #  "i is the MINIMUM radius of gyration" ).  Burada ix okunuyordu;
        #  kataloğun altı profilinden beşinde iy < ix olduğu için tablo
        #  dışına düşen geometriler ( λ > 250 ) sessizce kabul ediliyordu.
        _ix = mukavemet_tablolari.ray(prof, "ix") if prof else None
        _iy = mukavemet_tablolari.ray(prof, "iy") if prof else None
        imin = min(_ix, _iy) if sayi_mi(_ix) and sayi_mi(_iy) else None
        if not (sayi_mi(imin) and imin > 0 and sayi_mi(l) and l > 0):
            continue
        lam = l / imin
        if lam > mukavemet_tablolari.OMEGA_LAMBDA_MAX:
            azami = mukavemet_tablolari.OMEGA_LAMBDA_MAX * imin
            #  GİRDİ REDDEDİLMEZ, UYARILIR.  Eskiden burası hata veriyor ve
            #  bütün proje hesaplanamıyordu.  Oysa λ > 250 yalnız ω'yı
            #  tanımsız bırakır:  eğilme, birleşik gerilme, flanş ve sehim
            #  hesapları geçerliliğini korur.  Motor ω = None'ı zaten
            #  karşılıyor — bölüm "TABLO DIŞI" der ve burkulma kontrolü
            #  DÜŞER, yani sonuç UYGUN DEĞİL çıkar.  Referans projenin paftası da
            #  aynı şeyi yapar:  "when λ > 250 … σk also cannot be
            #  calculated".  Hesabı büsbütün durdurmak, kullanıcıya öteki
            #  bölümlerin sonucunu da göstermiyordu.
            uyari.append(
                f"{ne} rayı fazla narin:  λ = konsol arası / imin = "
                f"{l:g} / {imin:g} = {lam:.1f}  >  {mukavemet_tablolari.OMEGA_LAMBDA_MAX}. "
                "TS EN 81-50 m.5.10.3'ün ω tablosu bu narinliğin ötesinde "
                "tanımlı değildir;  BURKULMA HESABI YAPILAMAZ ve bölüm "
                f"uygun çıkmaz. '{ALAN[konsol_alan][1]}' en çok "
                f"{azami:.0f} mm olabilir ( '{prof}' rayı için ), ya da daha "
                "büyük kesitli bir ray profili seçilmelidir."
            )
    return uyari


def _tampon_ezilmesi_uyarisi(g):
    """TAM EZİLME = KURULU YÜKSEKLİĞİN %90'I   TS EN 81-20 m.5.8.2.1.2.2

    Madde "fully compressed" terimini TANIMLAR:  Çizelge 2'nin uç
    konumlarında tampon, kurulu yüksekliğinin %90'ı kadar ezilmiş sayılır
    ( bağlantı elemanları daha azıyla sınırlıyorsa o kadar ).  Program bu
    sayıyı sığınma açıklıklarında kullanır:
        kuyu dibi açıklığı = baba + ( tampon boyu − ezilme )
    Girilen ezilme gerçeğinden KÜÇÜKSE açıklık OLDUĞUNDAN BÜYÜK çıkar ve
    m.5.2.5.8'in 500 mm'si yanlışlıkla sağlanmış görünür — emniyetsiz yön.
    Lineer olmayan tamponda uyarılır;  lineer ve hidrolikte strok zaten
    bağıntıyla denetlendiği için burada tekrarlanmaz."""
    _tip = g.get("tampon_tipi")
    if not (_tip and mukavemet_tablolari.tampon(_tip)[2] is None):
        return []
    _boy, _ez = g.get("kabin_tampon_boyu"), g.get("kabin_tampon_ezilme")
    if not (sayi_mi(_boy) and sayi_mi(_ez) and _boy > 0):
        return []
    _tam = mukavemet_tablolari.TAMPON_TAM_EZILME_ORANI * _boy
    if _ez >= _tam - 0.5:
        return []
    return [
        f"Kabin tamponu ezilmesi ({_ez:g} mm), kurulu yüksekliğin "
        f"%{mukavemet_tablolari.TAMPON_TAM_EZILME_ORANI * 100:.0f}'ından "
        f"({_tam:.0f} mm) küçük.  TS EN 81-20 m.5.8.2.1.2.2 "
        '"tam ezilmiş" durumu bu oranla tanımlar;  daha küçük bir '
        "değer kuyu dibi açıklığını olduğundan BÜYÜK gösterir. "
        "Bağlantı elemanları ezilmeyi gerçekten sınırlıyorsa değer "
        "doğrudur, yoksa tampon boyuyla uyumlu hâle getirilmelidir."
    ]


def alt_duraktan_tavana(g):
    """En alt durak döşemesinden kuyu tavanına ( mm )  =  seyir × 1000 + son kat.

    Eski durak listesinin TOPLAMIYDI;  ray boyu, regülatör halatı ve kuyu
    boyu bu tek sayıdan türer.  Girdiler sayı değilse None.
    """
    sm, sk = g.get("seyir_mesafesi"), g.get("son_kat_yuksekligi")
    if not (sayi_mi(sm) and sayi_mi(sk)):
        return None
    return sm * 1000.0 + sk


def toplam_ray_boyu(g):
    """Kılavuz ray toplam boyu ( m )  =  ( seyir + son kat − 200 + kuyu dibi − 300 ) / 1000
    — çizim yoksa ( program raydan ölçer ).

    Rayın üst ucu kuyu tavanının 200 altında:  makine daireli tesiste de ( son
    kat kuyu tavanına ölçülür ).  5 Eki'ye kadar "+ tabliye" ekleniyordu:  tabliye
    beton yüksekliği oda zemininden ölçülür, kuyu tavanının üstünde değildir —
    raylar 1.000 mm uzun çıkıyordu ( tasarim/alanlar ).
    """
    tavan = alt_duraktan_tavana(g)
    kd = g.get("kuyu_dibi")
    if tavan is None or not sayi_mi(kd):
        return None
    return (tavan - 200 + (kd - 300)) / 1000.0


#  Nps  —  TEK YÖNDE BÜKÜLMELİ KASNAK SAYISI, BOŞ BIRAKILINCA  ( TS EN 81-50 Ek E )
#  m.5.12.3 güvenlik katsayısını halatın EN OLUMSUZ KESİTİ için ister:  sayılan,
#  halatın tamamının geçtiği kasnaklar değil, tek bir kesitin çalışırken
#  üzerinden geçtiği kasnaklardır.  Standardın iki çözümlü örneği:
#     Şekil E.1 — 2:1 askı       Nps = 2   kabin kesiti iki kabin kasnağından
#                                          geçer;  hareketli kasnak ters
#                                          bükülme sayılmaz ( Npr = 0 )
#     Şekil E.2 — 1:1 askı       Nps = 1   tahrik kasnağının saptırma kasnağı
#  OFİS DÜZENİ:  2:1'de tahrik kasnağının saptırma kasnağı KARŞI AĞIRLIK
#  tarafındadır.  Ağırlık kesiti saptırma + ağırlık kasnağından geçer ( 2 ),
#  kabin kesiti iki kabin kasnağından ( 2 ) — ikisi de Şekil E.1'in sayısı.
#  Saptırma kabin tarafında olan bir düzende kabin kesiti 3 kasnaktan geçer;
#  o projede değer elle girilir.
#  ESKİ VARSAYILAN 1'Dİ ve 2:1'de programın kendi uyarısına ( "en az iki kabin
#  kasnağı" ) takılıyordu:  Nequiv küçük, gereken Sf olduğundan küçük çıkıyordu.
def kasnak_tek_yon_askidan(r):
    return 1 if r == 1 else 2


def kasnak_tek_yon(g):
    """( Nps , girildi_mi ).  Boşsa askı oranından türetilir."""
    d = g.get("kasnak_tek_yon")
    if d is None or (isinstance(d, str) and not d.strip()):
        return kasnak_tek_yon_askidan(g.get("aski_orani")), False
    return d, True
