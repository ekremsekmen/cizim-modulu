# -*- coding: utf-8 -*-
"""
HESAP → ÇİZİM KÖPRÜSÜ

Hesap programının bir asansör için topladığı girdiden ( ve hesabın
sonucundan ) çizim girdisini ( cizim/girdi.py sözleşmesi ) kurar.

TEK DOĞRULUK KAYNAĞI.  Hesapta olan bir ölçü çizimde ikinci kez sorulmaz:
kabin ve kuyu ölçüleri, ray profilleri, paten araları, tamponlar, askı oranı,
halatlar, makine ve kaidesi hesabın girdisinden gelir.  Kuyu tabanına ve ray
konsollarına gelen kuvvetler hesabın SONUCUNDAN gelir.  Yalnız çizimin
ihtiyaç duyup hesabın bilmediği ölçüler ( kuyu derinliği, durak adedi, kapının
ve kabinin kuyudaki yeri … ) ayrıca sorulur:  ALANLAR.

İKİSİNİN AYNI ŞEYİ SÖYLEMESİ DENETLENİR.  Aynı fiziksel büyüklük iki yerde
modelleniyorsa ( halat sarılma açısı, askı noktası, kasnak çapları, makine
kirişlerinin mesnet aralığı ) çizimin geometrisi hesabın girdisiyle
karşılaştırılır;  uyuşmazsa çizim durur ve DOĞRU DEĞERİ söyler.  Pafta kendi
içinde çelişmez.

Eksen dönüşümleri ( hesap:  TS EN 81-50 Ek C.1.2 — orijin kabin ray ekseni,
x kabin derinliği boyunca kapıdan arkaya, y rayları birleştiren doğrultu;
çizim:  orijin kuyunun sol-ön iç köşesi, x genişlik, y derinlik ):

    kapı hattı ( kat eşiğinin kabine bakan kenarı )  y = hat
    kabin ray ekseni                                 y = hat + RK
    askı noktası                                     y = hat + RK + xs
"""
import math

from cizim import girdi as CG
from cizim import sabitler as CS


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


GRUP = "Çizim  ( kuyu yerleşimi )"

#  ( anahtar , etiket , birim , tür , seçenekler , varsayılan , gelişmiş , açıklama )
#  Varsayılanı None olan alan boş bırakılabilir:  değeri açıklamada yazan
#  kuraldan gelir ( _varsayilan ).  Gelişmiş alanlar grubun altında kapalı durur.
ALANLAR = (
    ("kuyu_derinligi", "Kuyu derinliği  ( KD )", "mm", "sayi", None, 1800, False,
     "Kuyunun plandaki iç derinliği:  kapı duvarının iç yüzünden arka duvarın iç "
     "yüzüne.  Kuyu genişliği ile birlikte kuyu planını kurar."),
    ("durak_adedi", "Durak adedi", "adet", "sayi", None, 8, False,
     "Kat kapısı sayısı.  Kat yüksekliği seyir mesafesinden çıkar:  "
     "seyir / ( durak − 1 ).  Düşey kesitlerde duraklar bu aralıkla dizilir."),
    ("kabin_yana_kaciklik", "Kabinin kuyu ortasından sağa kaçıklığı  ( sola − )", "mm", "sayi",
     None, 0, False,
     "Kapıya bakana göre kabin ekseninin kuyu genişliğinin ortasından uzaklığı. "
     "Karşı ağırlık yandaysa kabin çoğunlukla öbür yana kaçar.  Kabin rayları "
     "ve kat kapısı kabinle birlikte kayar."),
    ("aski_duzeni", "Askı kasnaklarının yeri  ( 2:1 )", "—", "secim", ("Kabin altı", "Kabin üstü"),
     "Kabin altı", False,
     "2:1 askıda kabin kasnaklarının kabinin altında mı üstünde mi olduğu. "
     "1:1 askıda halatlar kabine doğrudan bağlanır, bu seçim kullanılmaz."),
    ("kuyu_duvar_kalinligi", "Kuyu duvarı kalınlığı", "mm", "sayi", None, 150, True,
     "Kuyunun dört duvarı bu kalınlıkta çizilir ( referans proje:  150 )."),
    ("kapi_montaji", "Kat kapısının montajı", "—", "secim", tuple(CG.KAPI_MONTAJLARI),
     "Kuyu içine", True,
     "Duvar boşluğuna:  kasa duvarın boşluğunda, eşik kuyuya taşar.  Kuyu içine:  "
     "kapı ünitesi duvarın iç yüzüne monte ( referans proje ).  Kapı hattının ve "
     "kabinin kuyudaki yeri buna göre değişir."),
    ("esik_arasi", "Kabin eşiği – kat eşiği arası", "mm", "sayi", None, 30, True,
     "TS EN 81-20 m.5.3.4.1:  en çok 35 mm ( referans proje:  30 ).  Kabinin ön "
     "yüzü kapı hattından bu açıklık + kabin eşiği derinliği kadar geridedir."),
    ("kapi_kaciklik", "Kat kapısının kabin ekseninden sağa kaçıklığı", "mm", "sayi", None, 0, True,
     "Kapı boşluğunun ekseni kabinin ekseninde değilse ( sola − )."),
    ("kapi_yuksekligi", "Kat kapısı yüksekliği", "mm", "sayi", None, 2000, True,
     "Kapının net geçiş yüksekliği;  TS EN 81-20 m.5.3.1.1 en az 2.000 mm."),
    ("kabin_ic_yuksekligi", "Kabin iç yüksekliği", "mm", "sayi", None, 2200, True,
     "TS EN 81-20 m.5.4.1 en az 2.000 mm.  Düşey kesitlerde kabin bu yükseklikte "
     "çizilir."),
    ("kabin_ray_arasi", "Kabin rayları arası  ( DBG — boşsa kabin genişliği + 200 )", "mm", "sayi",
     None, None, True,
     "İki kabin rayının birbirine bakan uçları arası.  Kabin şasesi bu aralığa "
     "sığmalıdır ( referans proje:  1.350 mm kabinde 1.550 )."),
    ("agirlik_ray_arasi", "Ağırlık rayları arası  ( DBGW — boşsa Gy + 60 )", "mm", "sayi",
     None, None, True,
     "İki karşı ağırlık rayının birbirine bakan uçları arası.  Ağırlık çerçevesi "
     "( Gy ) bu aralıkta durur, iki uçta paten payı kalır ( referans proje:  790 "
     "çerçevede 850 ).  Makine dairesizde makine kirişleri bu raylara oturuyorsa "
     "kirişlerin mesnet aralığı ( yan yatak boyu ) da budur."),
    ("agirlik_ray_duvar", "Karşı ağırlık ekseni – duvar arası  ( boşsa Gx / 2 + 50 )", "mm", "sayi",
     None, None, True,
     "Karşı ağırlığın ekseninin yakın duvara uzaklığı:  yandaysa yan duvara, "
     "arkadaysa arka duvara."),
    ("agirlik_eksen_kaciklik", "Karşı ağırlık ekseninin kabin rayından kaçıklığı  ( arkaya + )",
     "mm", "sayi", None, 0, True,
     "Yandaki karşı ağırlığın ekseni kabin ray ekseninin önünde ( − ) ya da "
     "arkasında ( + ) olabilir ( referans proje:  50 mm önde, −50 )."),
    ("agirlik_kasnak_capi", "Karşı ağırlık kasnağı çapı  ( 2:1 )", "mm", "sayi",
     None, 400, True,
     "2:1 askıda karşı ağırlığın üstündeki kasnak ( referans proje:  400 ).  Hesabın "
     "D2'si ( saptırma kasnaklarının ortalaması ) ve Ds'si ( en küçüğü ) boş "
     "bırakılırsa çizilen kasnaklardan gelir."),
    ("kabin_kasnak_capi", "Kabin askı kasnakları çapı  ( 2:1 )", "mm", "sayi",
     None, 240, True,
     "Kabinin altındaki ( ya da üstündeki ) iki askı kasnağının çapı ( referans proje:  "
     "240 )."),
    ("makine_saptirma_capi", "Saptırma kasnağı çapı  ( makine dairesinde, gerekirse )", "mm", "sayi",
     None, 400, True,
     "Makine dairesinde karşı ağırlık halatı tahrik kasnağının öbür teğetinden daha "
     "dışarıda inmeliyse saptırma kasnağı çizilir;  o zaman bu çapta.  Çizildiyse "
     "hesabın D2 ortalamasına da girer."),
    ("kabin_kasnak_arasi", "Kabin askı kasnakları arası  ( 2:1 )", "mm",
     "sayi", None, None, True,
     "İki kasnağın eksenleri arası.  Kabin altında boşsa halat karşı ağırlık kasnağına "
     "DÜŞEY iner:  kabinin ağırlık tarafındaki halat tahrik kasnağının bir teğetinde, "
     "öbür teğeti ağırlığın ekseninde ( sarım açısı 180°, çizimden bulunur ).  Halat "
     "kabinin panosuna yaklaşıyorsa ya da düşey inen halat ray ara kirişine çarpıyorsa "
     "kabin genişliği + 30 ( referans proje:  1.350 mm kabinde 1.380;  halat eğik iner, "
     "α girilir ).  Kabin üstünde boşsa kasnakların dış ucu kabin kenarından 200 "
     "içeride:  korkuluğun içinde kalır ( korkuluk kenardan en çok 150 içeride — "
     "m.5.4.7.4 c )."),
    ("regulator_yani", "Regülatör halatının yanı", "—", "secim",
     ("Karşı ağırlığın karşısı", "Sağ", "Sol"), "Karşı ağırlığın karşısı", True,
     "Hız regülatörü halatının ve gergi kasnağının hangi kabin rayının yanından "
     "indiği.  Karşı ağırlık arkadaysa \"karşısı\" sağ yan sayılır."),
    ("regulator_kaciklik", "Regülatör halatı – kabin ray ekseni arası  ( arkaya + )", "mm", "sayi",
     None, None, True,
     "Regülatör halatının ray ekseninden uzaklığı ( referans proje:  280 arkada ).  Boşsa "
     "280, askı halatlarının çizgisinin öbür yanında:  kabin halat bağlantısı ile "
     "regülatör aynı rayın başında durur, üst üste binmesinler.  Gergi ağırlığı "
     "kasnağın ötesine uzanır, kuyuya sığmazsa kol öbür yöne döner;  o zaman raya ya da "
     "tampona çarpıyorsa program çarpmayan en yakın yeri seçer."),
    ("agirlik_tampon_boyu", "Ağırlık tamponu uzunluğu  ( boşsa kabin tamponununki )", "mm", "sayi",
     None, None, True,
     "Karşı ağırlık tamponunun serbest boyu ( kaideden tepesine ).  Düşey "
     "kesitlerde ağırlık tamponu bu boyda çizilir."),
    ("acil_pano_yani", "Acil kurtarma panosunun yanı  ( makine dairesiz )", "—", "secim",
     ("Sol", "Sağ"), "Sol", True,
     "Makine dairesizde acil kurtarma panosu en üst kattaki kat kapısının bu "
     "yanında durur."),
    #  ── MAKİNE DAİRESİ ( proje geneli:  oda binaya aittir ) ────────────
    ("md_duvar", "Makine dairesi duvar kalınlığı", "mm", "sayi", None, 200, True,
     "Makine dairesi duvarlarının kalınlığı."),
    ("md_x", "Makine dairesinin kuyuya göre yeri — x  ( boşsa ortalı )", "mm", "sayi", None, None,
     True,
     "Odanın sol iç yüzünün kuyunun sol iç yüzüne göre yeri ( sola − ).  Boşsa oda "
     "kuyunun dış genişliğine ortalanır."),
    ("md_y", "Makine dairesinin kuyuya göre yeri — y  ( boşsa ön duvarla hizalı )", "mm", "sayi",
     None, None, True,
     "Odanın ön iç yüzünün kuyunun ön iç yüzüne göre yeri ( öne − ).  Boşsa odanın "
     "önü kuyunun ön duvarının dış yüzüyle hizalıdır."),
    ("md_yukseklik", "Makine dairesi iç yüksekliği", "mm", "sayi", None, 3500, True,
     "Döşemeden tavana temiz yükseklik;  TS EN 81-20 m.5.2.6.3.2 çalışma alanlarında "
     "en az 2.100 mm."),
    ("md_kapi_duvar", "Makine dairesi kapısının duvarı", "—", "secim", ("Ön", "Arka", "Sol", "Sağ"),
     "Arka", True, "Kapının açıldığı duvar."),
    ("md_kapi_konum", "Makine dairesi kapısının köşeden uzaklığı", "mm", "sayi", None, 300, True,
     "Kapının bulunduğu duvarın sol ( ön ) iç köşesinden kapı boşluğuna."),
    ("md_kapi_genislik", "Makine dairesi kapısı genişliği", "mm", "sayi", None, 800, True,
     "TS EN 81-20 m.5.2.3.2 a:  en az 600 mm."),
    ("md_kapi_yukseklik", "Makine dairesi kapısı yüksekliği", "mm", "sayi", None, 2000, True,
     "TS EN 81-20 m.5.2.3.2 a:  en az 1.800 mm."),
    ("md_pano_duvar", "Kumanda panosunun duvarı", "—", "secim", ("Ön", "Arka", "Sol", "Sağ"),
     "Sağ", True, "Kumanda panosunun durduğu duvar."),
)
ALAN = {a[0]: a for a in ALANLAR}

#  Makine dairesi binaya aittir:  bütün asansörlerde tek değer.
PROJE_GENELI = tuple(a for a in ALAN if a.startswith("md_"))
#  Makine yerleşimine göre çizime girmeyen alanlar ( ekran gizler ).
YALNIZ_DAIRELI = PROJE_GENELI
YALNIZ_MRL = ("acil_pano_yani",)


#  HESABIN OFİS STANDARDINDAN ÇİZİME GEÇEN KABİN VE KUYU ÖLÇÜLERİ:  hesabın
#  Sabitler sekmesinde değiştirilir;  çizim ve hesabın bölüm 11'i aynı sayıyı
#  kullanır.  hesap anahtarı → çizim sabiti ( cizim/sabitler.py )
OFIS_SABITLERI = {
    "tavan_payi": "tavan_kirisi",
    "sase_alt_derinlik": "sase_alt_derinlik",
    "kabin_taban_kalinlik": "kabin_taban_kalinlik",
    "kabin_tavan_kalinlik": "kabin_tavan_kalinlik",
    "paten_yukseklik": "paten_yukseklik",
    "fren_blogu_yukseklik": "fren_blogu_yukseklik",
    "kabin_kasnak_derinlik": "kabin_kasnak_derinlik",
}


def cizim_sabitleri(A):
    """Hesabın ofis standardındaki ( A["_ofis"] ) çizim sabitleri — ezme sözlüğü.
    A["_urun_ezme"] ( { cizim/sabitler anahtarı : değer } ) ürün ölçülerini
    ezer:  ölçü kaynağı çözümlemesi ( olcu_kaynagi ) bir ürün ölçüsünü
    oynatıp hangi ölçülerin ona bağlı olduğunu böyle bulur."""
    ofis = A.get("_ofis") if isinstance(A.get("_ofis"), dict) else {}
    d = {c: float(ofis[o]) for o, c in OFIS_SABITLERI.items() if _sayi(ofis.get(o)) and ofis[o] > 0}
    ez = A.get("_urun_ezme")
    if isinstance(ez, dict):
        d.update({k: float(v) for k, v in ez.items() if k in CS.SABIT and _sayi(v)})
    return d


#  BOŞSA KURALLA DOLAN ÇİZİM ALANLARI ( varsayılanı None ):  kutu boşken
#  değer bir kuraldan gelir ( "boşsa Gy + 60" … ).  Ölçü kaynağı çözümlemesi
#  kutunun ETKİN değerini çizimin girdisinden okur — okumasaydı DBGW ölçüsü
#  "karşı ağırlık genişliğinden geliyor" görünür, ölçüyü değiştirmek Gy'yi
#  değiştirirdi.  Yol:  çizim girdisinde ( g ) değerin durduğu yer.
KURALLI = {
    "kabin_ray_arasi": ("kabin_ray", "arasi"),
    "agirlik_ray_arasi": ("agirlik", "ray_arasi"),
    "agirlik_ray_duvar": ("agirlik", "ray_duvar"),
    "kabin_kasnak_arasi": ("aski", "kasnak_arasi"),
    "regulator_kaciklik": ("kuyu_dibi", "regulator_kaciklik"),
    "agirlik_tampon_boyu": ("dusey", "agirlik_tampon_boyu"),
    "md_x": ("makine_dairesi", "x"),
    "md_y": ("makine_dairesi", "y"),
}


def etkin_deger(g, anahtar):
    """Kuralla dolan bir çizim alanının çizimde kullanılan değeri ( yoksa None:
    ör. 1:1 askıda kasnak arası, makine dairesizde odanın yeri )."""
    b, a = KURALLI[anahtar]
    v = (g.get(b) or {}).get(a)
    return float(v) if _sayi(v) else None


def _mrl(A):
    """Makine dairesiz mi?  Girdide yoksa hesap programının varsayılanı ( MRL )."""
    return bool(A.get("mk_yok", True))


def uygulanmayan(mk_yok):
    return set(YALNIZ_DAIRELI) if mk_yok else set(YALNIZ_MRL)


def arayuz_grubu():
    """Hesap formunun bir grubu olarak çizim alanları ( hesap programının
    alan sözlüğü biçiminde )."""
    return {"ad": GRUP, "alanlar": [
        {"anahtar": a, "hucre": "", "etiket": et, "birim": b, "tur": t,
         "secenekler": list(s) if s is not None else None, "varsayilan": v,
         "gelismis": gel, "bilgi": bilgi}
        for a, et, b, t, s, v, gel, bilgi in ALANLAR]}


def _profil(p):
    """Ray profili "89 x 62 x 15,88"  →  ( b, h )."""
    try:
        b, h = (float(x.strip().replace(",", ".")) for x in str(p).split("x")[:2])
        return b, h
    except (TypeError, ValueError):
        return None


def _en_buyuk(a, kimlik, sembol):
    """Hesap bölümündeki bütün yük durumlarının en büyük |Fx| ya da |Fy|'si."""
    b = next((b for b in a.get("bolumler") or [] if b.get("kimlik") == kimlik), None)
    d = [abs(x["deger"]) for x in (b or {}).get("adimlar") or []
         if str(x.get("formul") or "").startswith(sembol + " =") and _sayi(x.get("deger"))]
    return max(d) if d else None


def kuvvetler(a):
    """Binaya gelen yükler ( N ):  kuyu tabanı 9. bölümden, ray konsollarına
    gelen yatay kuvvetler 7. ve 8. bölümlerin bütün yük durumlarının en
    büyüğünden.  Hesap yapılamadıysa boş ( kutularda yalnız ad yazar )."""
    if not (isinstance(a, dict) and a.get("aktif")):
        return {}
    oz = a.get("ozet") or {}
    k = {s: oz[s] for s in ("FKR", "FAR", "Fkt", "Fat") if _sayi(oz.get(s))}
    for ad, kimlik in (("kabin", "kabin_raylari"), ("agirlik", "agirlik_raylari")):
        for s in ("Fx", "Fy"):
            v = _en_buyuk(a, kimlik, s)
            if v is not None:
                k[f"{s}_{ad}"] = v
    return k


def _deger(A, anahtar):
    """Girilmiş çizim alanı;  boş / girilmemiş ise None."""
    v = A.get(anahtar)
    return None if v is None or (isinstance(v, str) and not v.strip()) else v


def _varsayilan(A, anahtar):
    v = _deger(A, anahtar)
    return ALAN[anahtar][5] if v is None else v


def _bos(v):
    """Kutu boş mu ( girilmemiş, None ya da boşluk )."""
    return v is None or (isinstance(v, str) and not v.strip())


def _dusey_kasnak_arasi(kx, kb_g, Dk, D1, G, ray_duvar, yer, S):
    """Kabin altı 2:1, ağırlık yanda, kasnaklar arası boş:  halat karşı ağırlık
    kasnağına DÜŞEY insin.  Tahrik kasnağının bir teğeti kabinin ağırlık
    tarafındaki halatın üstünde, öbür teğeti ağırlığın ekseninde olmalı:
    halat = ağırlık ekseni − D1 ( ağırlık solda:  + D1 ).  Eski kural ( kabin
    genişliği + 30 ) halatı kabin rayının ara kirişinin 20 mm dibine koyuyor
    ( kasnak 20 mm büyüyünce çizim reddediliyordu ) ve ağırlığa 25 mm eğik
    indiriyordu ( sarım açısı çizimden bulunamıyor, makine dairesinde "halat
    içeride inmeli" hatası ).  Halat kabinin panosuna 20 mm'den yaklaşırsa
    None ( eski kural ).  Ara kirişe ya da konsola çarpıyorsa çizim söyler."""
    y_ = 1.0 if yer == "Sağ" else -1.0
    ex = G - ray_duvar if yer == "Sağ" else ray_duvar
    halat = ex - y_ * D1
    yari = y_ * (halat - kx)                       # kabin ekseninden halata
    if yari < kb_g / 2.0 + S["kabin_pano_yan"] + 20.0:
        return None
    return round(2.0 * yari - Dk, 3)


def cizim_girdisi(A, sonuc=None, proje_adi="", sira=1):
    """Tek asansörün çizim girdisi.

    A:      hesap girdisi ( tamamlanmış — boş alanlar hesabın varsayılanıyla
            dolu ) + çizim alanları ( ALANLAR ) + proje geneli alanlar.
    sonuc:  hesabın o asansör için sonucu ( kuvvetler buradan );  None olabilir.
    Döner:  ( g , hatalar ) — hata varsa g None."""
    ozel = cizim_sabitleri(A)
    S = CS.sabitler(ozel)
    hata = []

    def sayi(anahtar, etiket=None, bos=False, isaretli=False):
        v = A.get(anahtar) if anahtar not in ALAN else _varsayilan(A, anahtar)
        et = etiket or (ALAN[anahtar][1] if anahtar in ALAN else anahtar)
        if v is None and bos:
            return None
        if not _sayi(v):
            hata.append(f"{et}:  girilmemiş." if _bos(v) else f"{et}:  sayı olmalı ( {v!r} ).")
            return None
        if not isaretli and v <= 0:
            hata.append(f"{et}:  sıfırdan büyük olmalı ( {v:g} ).")
            return None
        return float(v)

    def secim(anahtar, etiket=None, secenekler=None):
        """Çizim alanı ya da ( etiket ve seçeneklerle ) hesabın bir seçim alanı."""
        v = _varsayilan(A, anahtar) if anahtar in ALAN else A.get(anahtar)
        et = etiket or ALAN[anahtar][1]
        sec = tuple(secenekler if secenekler is not None else ALAN[anahtar][4])
        if v not in sec:
            liste = " · ".join(str(x) for x in sec)
            hata.append(f"{et}:  seçilmemiş ( {liste} )." if _bos(v)
                        else f"{et}:  {liste} içinden olmalı ( {v!r} ).")
        return v

    mk_yok = _mrl(A)
    #  ── HESAPTAN ──────────────────────────────────────────────────────
    G = sayi("kuyu_genisligi", "Kuyu genişliği")
    kb_g, kb_d = sayi("kabin_genisligi", "Kabin genişliği"), sayi("kabin_derinligi", "Kabin derinliği")
    RK = sayi("ray_kapi_arasi", "Ray – kapı arası ( RK )")
    kapi_g = sayi("kapi_genisligi", "Kat kapısı genişliği")
    Gy, Gx = sayi("agirlik_genisligi", "Karşı ağırlık genişliği ( Gy )"), \
        sayi("agirlik_derinligi", "Karşı ağırlık derinliği ( Gx )")
    kr, ar = _profil(A.get("kabin_ray_profili")), _profil(A.get("agirlik_ray_profili"))
    for p, et, a in ((kr, "Kabin rayı profili", "kabin_ray_profili"),
                     (ar, "Ağırlık rayı profili", "agirlik_ray_profili")):
        if p is None:
            hata.append(f"{et}:  seçilmemiş." if _bos(A.get(a))
                        else f"{et}:  okunamadı ( {A.get(a)!r} ).")
    oran = secim("aski_orani", "Askı oranı", (1, 2))
    #  Hesabın seçimleri çizim modülünün kendi doğrulamasına boş gitmesin:
    #  ileti formdaki adla söylensin ( "agirlik.yeri" değil ).
    from cizim import kabin_ustu as CKU, kuyu_dibi as CKD, makine as CMK
    ag_yeri = secim("agirlik_yeri", "Karşı ağırlık yeri", CG.AGIRLIK_YERLERI)
    sig_ust = secim("siginma_tipi_ust", "Kabin üstü sığınma hacmi tipi", CKU.SIGINMA)
    sig_dip = secim("siginma_tipi_dip", "Kuyu dibi sığınma hacmi tipi", CKD.SIGINMA)
    mk_tip = secim("makine_tipi", "Makine tipi", CMK.TIPLER)
    yan_yatak = secim("yan_yatak", "F  ( yan yatak — makine kirişi ölçüsü )", CMK.NPU)
    halat_n = sayi("halat_adedi", "Askı halatı adedi")
    halat_d = sayi("halat_capi", "Askı halatı çapı")
    D1 = sayi("tahrik_kasnak_capi", "D1 ( tahrik kasnağı çapı )")
    #  Hesabın kaçıklıkları ( ray ekseninden ):  kabin merkezi yc, askı xs · ys
    yc = sayi("kabin_kaciklik", "Kabin merkezinin y kaçıklığı ( yc )", isaretli=True)
    xs = sayi("aski_kaciklik_x", "Askı noktasının x kaçıklığı ( xs )", bos=True, isaretli=True)
    ys = sayi("aski_kaciklik_y", "Askı noktasının y kaçıklığı ( ys )", isaretli=True)
    #  ── ÇİZİMİN KENDİ ALANLARI ───────────────────────────────────────
    KD = sayi("kuyu_derinligi")
    durak = sayi("durak_adedi")
    kacik = sayi("kabin_yana_kaciklik", isaretli=True)
    duvar = sayi("kuyu_duvar_kalinligi")
    montaj = secim("kapi_montaji")
    esik_arasi = sayi("esik_arasi")
    kapi_kacik = sayi("kapi_kaciklik", isaretli=True)
    ag_kacik = sayi("agirlik_eksen_kaciklik", isaretli=True)
    reg_kacik = sayi("regulator_kaciklik", bos=True, isaretli=True)
    reg_yan = secim("regulator_yani")
    if hata:
        return None, hata

    #  ÇİZİMİN MODELLEYEMEDİĞİ KAÇIKLIKLAR.  Çizim kabini raylarının ortasına,
    #  askıyı kabin ekseninin üstüne koyar;  hesap başka bir yer söylüyorsa
    #  pafta hesapla çelişir.
    if abs(yc) > 1e-9:
        hata.append(f"Kabin merkezinin y kaçıklığı ( yc ) {yc:g} mm:  çizim kabini iki rayın "
                    "tam ortasında çizer — kabin raylara göre kaçıksa bu henüz çizilemiyor.")
    if abs(ys) > 1e-9:
        hata.append(f"Askı noktasının y kaçıklığı ( ys ) {ys:g} mm:  çizim askıyı raylar "
                    "arasının ortasında çizer — yana kaçık askı henüz çizilemiyor.")
    if xs is None:
        hata.append("Askı noktasının x kaçıklığı ( xs ) boş — değerini girin.")
    if durak < 2 or durak != int(durak):
        hata.append(f"Durak adedi en az 2 olan bir tam sayı olmalı ( {durak:g} ).")
    seyir = sayi("seyir_mesafesi", "Seyir mesafesi")
    #  KUYU DİBİ ZİNCİRİ:  kabin en alt durakta dururken kaide + tampon +
    #  çarpma arası + kabinin şase altı kuyu dibine eşittir.  Hesap kaideyi
    #  boşsa buradan alır ( cizimden );  girilmişse zincir kapanmalı.
    KY, baba = sayi("kuyu_dibi", "Kuyu dibi yüksekliği ( KY )"), \
        sayi("kabin_tampon_baba", "Kabin tamponu baba yüksekliği")
    boy, carpma = sayi("kabin_tampon_boyu", "Kabin tamponu uzunluğu"), \
        sayi("kabin_carpma_arasi", "Kabin tamponu – çarpma plakası arası")
    if not hata and abs(baba + boy + carpma + S["sase_alt_derinlik"] - KY) > 0.5:
        dogru = KY - boy - carpma - S["sase_alt_derinlik"]
        hata.append(f"Kuyu dibi zinciri kapanmıyor:  kaide {baba:g} + tampon {boy:g} + çarpma arası "
                    f"{carpma:g} + kabinin şase altı {S['sase_alt_derinlik']:g} = "
                    f"{baba + boy + carpma + S['sase_alt_derinlik']:g}, kuyu dibi {KY:g} — kabin "
                    f"tamponu kaidesine {dogru:g} girin ya da kutuyu boş bırakın ( çizimden gelir ).")
    if hata:
        return None, hata

    #  ── KAPI BÖLGESİ ─────────────────────────────────────────────────
    #  Kapı hattı ( kat eşiğinin kabine bakan kenarı ):  kuyu içine montajda
    #  kasa + eşik, duvar boşluğunda yalnız eşik kuyuya taşar.
    hat = CG.kapi_bolgesi({"kapi": {"montaj": montaj}, "kabin": {"on_pay": 0}}, S)["hat"]
    on_pay = hat + esik_arasi + S["kabin_esik_derinlik"]
    kapi_arasi = hat + RK
    kx = G / 2.0 + kacik

    #  ── ASKI ─────────────────────────────────────────────────────────
    #  Askı noktasının derinlikteki yeri hesabın xs'inden:  çizimde askı
    #  merkezi kabin ( pano dahil ) merkezine göre kaydırılarak verilir.
    aski_y = kapi_arasi + xs
    kabin_merkez = on_pay + (kb_d + S["kabin_pano_arka"]) / 2.0
    aralik = sayi("kabin_kasnak_arasi", bos=True)
    D1_, dusey_ara, eski_kural = D1 or 0.0, None, None
    if oran == 1:
        #  1:1:  tek bağlantı, kabin şasesinin üst kirişinin ortasında
        aski = {"duzen": "Doğrudan", "nokta_kaciklik": aski_y - kabin_merkez}
    else:
        duzen, Dk = secim("aski_duzeni"), sayi("kabin_kasnak_capi")
        eski_kural = kb_g + 30.0 if duzen == "Kabin altı" else kb_g - 2 * 200.0 - (Dk or 0)
        if not aralik and duzen == "Kabin altı" and ag_yeri in ("Sağ", "Sol") and Dk:
            ray_duvar = sayi("agirlik_ray_duvar", bos=True) or Gx / 2.0 + 50.0
            dusey_ara = _dusey_kasnak_arasi(kx, kb_g, Dk, D1_, G, ray_duvar, ag_yeri, S)
        aski = {"duzen": duzen, "kasnak_capi": Dk,
                "kasnak_arasi": aralik or dusey_ara or eski_kural,
                "kasnak_kaciklik": aski_y - kabin_merkez}
    aski.update(halat_adedi=halat_n, halat_capi=halat_d)

    if reg_yan == "Karşı ağırlığın karşısı":
        reg_yan = "Sol" if ag_yeri == "Sağ" else "Sağ"
    #  Regülatör ile kabin halat bağlantısı aynı rayın başındadır:  boşsa
    #  regülatör askı halatlarının çizgisinin öbür yanına ( referans proje:  halatlar
    #  ray ekseninin 250 önünde, regülatör 280 arkasında ).
    reg_bos = reg_kacik is None
    if reg_bos:
        reg_kacik = -280.0 if xs > 0 else 280.0
    agirlik_tampon_boyu = sayi("agirlik_tampon_boyu", bos=True) or sayi("kabin_tampon_boyu",
                                                                          "Kabin tamponu uzunluğu")
    Da = sayi("agirlik_kasnak_capi") if oran == 2 else None
    if hata:
        return None, hata

    g = {
        #  Hesabın Sabitler sekmesindeki kabin ölçüleri:  bütün çizimler okur
        "_cizim_sabitleri": ozel,
        "proje": {"ad": proje_adi or "", "asansor": str(A.get("asansor_adi") or "").strip()
                  or f"ASANSÖR {sira}", "olcek": 20},
        "kuyu": {"genislik": G, "derinlik": KD, "duvar_on": duvar, "duvar_arka": duvar,
                 "duvar_sol": duvar, "duvar_sag": duvar},
        "kabin": {"genislik": kb_g, "derinlik": kb_d, "kaciklik_y": kacik, "on_pay": on_pay},
        "kapi": {"genislik": kapi_g, "sol_pay": kx + kapi_kacik - kapi_g / 2.0,
                 "yukseklik": sayi("kapi_yuksekligi"), "tip": A.get("kat_kapisi_tipi"),
                 "montaj": montaj},
        "kabin_ray": {"arasi": sayi("kabin_ray_arasi", bos=True) or kb_g + 200.0,
                      "kapi_arasi": kapi_arasi, "b": kr[0], "h": kr[1]},
        "agirlik": {"yeri": ag_yeri, "genislik": Gy, "derinlik": Gx,
                    "ray_arasi": sayi("agirlik_ray_arasi", bos=True) or Gy + 60.0,
                    "ray_duvar": sayi("agirlik_ray_duvar", bos=True) or Gx / 2.0 + 50.0,
                    "eksen_kaciklik": ag_kacik, "b": ar[0], "h": ar[1], "kasnak_capi": Da},
        "aski": aski,
        "kabin_ustu": {"siginma_tipi": sig_ust},
        "kuyu_dibi": {"derinlik": sayi("kuyu_dibi", "Kuyu dibi yüksekliği ( KY )"),
                      "siginma_tipi": sig_dip,
                      "kabin_tampon_adedi": int(A.get("kabin_tampon_adedi") or 1),
                      "agirlik_tampon_adedi": int(A.get("agirlik_tampon_adedi") or 1),
                      "regulator_yan": reg_yan, "regulator_kaciklik": reg_kacik,
                      "regulator_halat_capi": sayi("reg_halat_capi", "Regülatör halatı çapı"),
                      "regulator_kasnak_capi": sayi("reg_kasnak_capi", "Regülatör kasnak çapı"),
                      #  Hesap yapılamadıysa yok ( kutularda yalnız ad yazar )
                      "kuvvetler": kuvvetler(sonuc) or None},
        "dusey": {"kabin_ic_yukseklik": sayi("kabin_ic_yuksekligi"),
                  "kabin_paten_arasi": sayi("kabin_paten_arasi", "Kabin paten arası"),
                  "agirlik_paten_arasi": sayi("agirlik_paten_arasi", "Ağırlık paten arası"),
                  "son_kat": sayi("son_kat_yuksekligi", "Son kat yüksekliği"),
                  "beyan_hizi": sayi("beyan_hizi", "Beyan hızı"),
                  "durak_adedi": int(durak),
                  "kat_yuksekligi": seyir * 1000.0 / (durak - 1),
                  "kabin_tampon_baba": sayi("kabin_tampon_baba", "Kabin tamponu baba yüksekliği"),
                  "kabin_tampon_boyu": sayi("kabin_tampon_boyu", "Kabin tamponu uzunluğu"),
                  "kabin_carpma_arasi": sayi("kabin_carpma_arasi", "Kabin tamponu – çarpma plakası arası"),
                  "kabin_tampon_ezilme": sayi("kabin_tampon_ezilme", "Kabin tamponu ezilme miktarı"),
                  "agirlik_tampon_baba": sayi("agirlik_tampon_baba", "Ağırlık tamponu baba yüksekliği"),
                  "agirlik_tampon_boyu": agirlik_tampon_boyu,
                  "agirlik_carpma_arasi": sayi("agirlik_carpma_arasi",
                                               "Ağırlık tamponu – çarpma plakası arası"),
                  "agirlik_tampon_ezilme": sayi("agirlik_tampon_ezilme", "Ağırlık tamponu ezilme miktarı"),
                  "kabin_konsol_arasi": sayi("kabin_konsol_arasi", "Kabin rayı konsollar arası"),
                  "agirlik_konsol_arasi": sayi("agirlik_konsol_arasi", "Ağırlık rayı konsollar arası")},
        "makine": {"tahrik_kasnak_capi": D1, "yeri": "Kuyu üstü" if mk_yok else "Makine dairesi",
                   "tip": mk_tip, "yan_yatak": yan_yatak,
                   "saptirma_kasnak_capi": sayi("makine_saptirma_capi")},
        "kuyu_ustu": {"acil_pano_yan": secim("acil_pano_yani")},
    }
    if not mk_yok:
        genislik, derinlik = sayi("mk_genislik", "Makine dairesi genişliği"), \
            sayi("mk_uzunluk", "Makine dairesi uzunluğu")
        md_duvar = sayi("md_duvar")
        mx, my = sayi("md_x", bos=True, isaretli=True), sayi("md_y", bos=True, isaretli=True)
        if genislik is not None:
            g["makine_dairesi"] = {
                "genislik": genislik, "derinlik": derinlik, "duvar": md_duvar,
                #  Boşsa oda kuyunun dış genişliğine ortalı, önü kuyunun ön
                #  duvarının dış yüzüyle hizalı ( çizim örneğinin düzeni ).
                "x": mx if mx is not None else -duvar - (genislik - (G + 2 * duvar)) / 2.0,
                "y": my if my is not None else -duvar,
                "kapi_duvar": secim("md_kapi_duvar"), "kapi_konum": sayi("md_kapi_konum"),
                "kapi_genislik": sayi("md_kapi_genislik"), "pano_duvar": secim("md_pano_duvar"),
                "yukseklik": sayi("md_yukseklik"), "kapi_yukseklik": sayi("md_kapi_yukseklik"),
                "tabliye_yuksekligi": sayi("tabliye_yuksekligi", "Tabliye beton yüksekliği"),
                "sase_yuksekligi": sayi("sase_yuksekligi", "Şase yüksekliği"),
                "dikine_kiris": secim("dikine_kiris", "E  ( dikine kiriş ölçüsü )", CMK.NPU),
                "yan_yatak_boyu": sayi("yan_yatak_boyu", "Yan yatak boyu")}
    if hata:
        return None, hata
    if dusey_ara:
        _kasnak_arasi_sec(g, eski_kural)
    if reg_bos:
        _regulator_yeri(g)
    return g, []


def _kasnak_arasi_sec(g, eski_kural):
    """Düşey iniş için bulunan kasnaklar arası halatı kuyudaki bir parçaya
    ( kabin rayının ara kirişi, konsol ) çarptırıyorsa eski kural:  kuyu
    kabinden geniş, ağırlık duvarla birlikte uzaklaşmışsa halat kabine yakın
    kalır, ağırlığa eğik iner ( sapma ölçüsü;  sarım açısı girilmeli )."""
    from cizim import kabin_ustu as CKUS
    try:
        carpar = any(h.startswith("Halat (") for h in CKUS.yerlesim(g)["hata"])
    except Exception:                                      # noqa: BLE001
        carpar = True
    if carpar:
        g["aski"]["kasnak_arasi"] = eski_kural


def _regulator_yeri(g):
    """Regülatör kaçıklığı boşsa:  varsayılan yer ( 280, askı halatlarının
    öbür yanında ) gergiyi bir raya ya da tampona çarptırıyorsa ( sığ kuyuda
    kol döner, ağırlık raya iner — 320 kg kabinlerde ) çarpmayan en yakın yer
    seçilir:  öbür yan, sonra 200 · 360 · 440.  Hiçbiri çarpmaktan
    kurtulmuyorsa varsayılan kalır ( çizim hatayı söyler )."""
    from cizim import kuyu_dibi as CKD
    from cizim import kuyu_ustu as CKT
    from cizim import makine_dairesi as CMD
    kd = g["kuyu_dibi"]
    ilk = kd["regulator_kaciklik"]

    def carpisma(c):
        #  Gergi kuyu dibinde, regülatörün kendisi kuyu tepesinde ( ya da
        #  makine dairesinde ):  ikisi de çarpmamalı.
        kd["regulator_kaciklik"] = c
        try:
            h = list(CKD.yerlesim(g)["hata"])
            h += (CKT.yerlesim(g) if g["makine"]["yeri"] == "Kuyu üstü"
                  else CMD.yerlesim(g)).get("hata") or []
        except Exception:                                  # noqa: BLE001
            return ["?"]
        return [x for x in h if "egülatör" in x]

    if not carpisma(ilk):
        return
    for c in (-ilk, 200.0 * (1 if ilk > 0 else -1), -200.0 * (1 if ilk > 0 else -1),
              360.0 * (1 if ilk > 0 else -1), -360.0 * (1 if ilk > 0 else -1),
              440.0 * (1 if ilk > 0 else -1), -440.0 * (1 if ilk > 0 else -1)):
        if not carpisma(c):
            return
    kd["regulator_kaciklik"] = ilk


#  HESABIN ÇİZİMDEN TÜRETİLEN GİRDİLERİ:  hesapta BOŞ bırakılırsa değeri
#  çizimin geometrisinden gelir ve hesaba o değer girer ( ekranda kutunun
#  içinde gri yazar ).  Girilmişse girilen kullanılır ve çizimle
#  karşılaştırılır ( tutarlilik ).
CIZIMDEN = {
    "aski_kaciklik_x": "Boşsa çizimden ( 2:1 halat çizgisi;  1:1 ve arkada 0 ).",
    "saptirma_kasnak_capi": "Boşsa çizimden:  çizilen kasnakların ortalaması ( çapları "
                            "formun Çizim grubunda ).",
    "saptirma_kasnak_min_capi": "Boşsa çizimden:  çizilen kasnakların en küçüğü.",
    "kabin_tampon_baba": "Boşsa çizimden:  kuyu dibi − tampon − çarpma arası − kabinin "
                         "şase altı.",
    "sarilma_acisi": "Boşsa çizimden, açı sabitse:  iki iniş düşey ( 180° ) ya da saptırma "
                     "kasnağı.  Halat eğik iniyorsa ( HALAT SAPMASI:  açı ağırlığın konumuyla "
                     "değişir ), çift sarımda ya da çizim kurulamıyorsa girilmeli.",
}


def kasnaklar(g):
    """Çizilen saptırma kasnaklarının çapları ( tahrik kasnağı hariç ):  2:1
    askıda iki kabin kasnağı ve karşı ağırlık kasnağı, makine dairesinde
    çizildiyse saptırma kasnağı."""
    a, c = g["aski"], []
    if a["duzen"] != "Doğrudan":
        c += [a["kasnak_capi"], a["kasnak_capi"], g["agirlik"]["kasnak_capi"]]
    if g["makine"]["yeri"] == "Makine dairesi":
        from cizim import makine_dairesi as CMD
        try:
            sap = CMD.yerlesim(g).get("saptirma")
        except Exception:                              # noqa: BLE001 — çizim zaten reddeder
            sap = None
        if sap:
            c.append(sap["D"])
    return c


def _aski_x(A):
    """Askının ray ekseninden kaçıklığı ( xs ).
      2:1   ağırlık yandayken:  tahrik kasnağının iki halat inişi aynı düşey
            düzlemdedir;  kabin kasnaklarının çizgisi karşı ağırlık kasnağının
            kabine yakın teğetindedir ( referans proje:  kasnaklar ağırlık ekseninin
            200, ray ekseninin 250 önünde ).
      1:1   halatlar kabin şasesinin üst kirişinin ortasındaki bağlantıda biter;
            kiriş ray ekseni üstündedir:  0 ( LiftDesigner 12744-3 ).
    Arkadaki ağırlıkla 2:1'de ya da ölçüsü eksikse None.

    YALNIZ KENDİ ÖLÇÜLERİNDEN hesaplanır:  başka bir girdideki hata ( kuyu
    dibi zinciri, kuyu derinliği … ) türetmeyi durdurmaz — o hata kendi
    iletisiyle söylenir, "xs boş" diye değil."""
    oran = A.get("aski_orani")
    if oran == 1:
        return 0.0
    if (oran != 2 or A.get("agirlik_yeri") not in ("Sağ", "Sol")
            or _varsayilan(A, "kapi_montaji") not in CG.KAPI_MONTAJLARI):
        return None
    v = [A.get("ray_kapi_arasi"), A.get("kabin_derinligi")] + [
        _varsayilan(A, k) for k in ("esik_arasi", "agirlik_eksen_kaciklik")]
    Da = _varsayilan(A, "agirlik_kasnak_capi")
    if not all(_sayi(x) for x in v + [Da]):
        return None
    RK, kb_d, esik, ag_kacik = v
    S = CS.sabitler(cizim_sabitleri(A))
    hat = CG.kapi_bolgesi({"kapi": {"montaj": _varsayilan(A, "kapi_montaji")},
                           "kabin": {"on_pay": 0}}, S)["hat"]
    ray_y = hat + RK
    kabin = hat + esik + S["kabin_esik_derinlik"] + (kb_d + S["kabin_pano_arka"]) / 2.0
    ag_y = ray_y + ag_kacik
    return min((ag_y - Da / 2.0, ag_y + Da / 2.0), key=lambda t: abs(t - kabin)) - ray_y


def _saptirma(g):
    """Makine dairesindeki saptırma kasnağı ( yoksa, makine dairesizde ya da
    çizim kurulamıyorsa None ).  Gerekip gerekmediği ve çapı halat aralığı ile
    tahrik kasnağından çıkar — odanın öbür hatalarından bağımsız."""
    if g is None or g["makine"]["yeri"] != "Makine dairesi":
        return None
    from cizim import makine_dairesi as CMD
    try:
        return CMD.yerlesim(g).get("saptirma")
    except Exception:                                  # noqa: BLE001 — çizim kendi hatasını söyler
        return None


def _kasnak_caplari(A, sap):
    """Hesabın D2 / Ds'si için çizilecek saptırma kasnakları — girdilerden
    doğrudan:  2:1 askıda iki kabin kasnağı ve karşı ağırlık kasnağı;  makine
    dairesinde çiziliyorsa saptırma kasnağı ( sap )."""
    c = []
    if A.get("aski_orani") == 2:
        Dk, Da = _varsayilan(A, "kabin_kasnak_capi"), _varsayilan(A, "agirlik_kasnak_capi")
        if not (_sayi(Dk) and _sayi(Da) and Dk > 0 and Da > 0):
            return None
        c = [float(Dk), float(Dk), float(Da)]
    if sap:
        c.append(sap["D"])
    return c


def _cift_sarim(A):
    """Kanal çift sarımlı mı:  halat tahrik kasnağının üzerinden iki kez geçer."""
    return "çift sarım" in str(A.get("kanal_sekli") or "").lower()




def cizimden(A):
    """Boş bırakılmış ( None ) hesap girdilerinin çizimden gelen değerleri.
    Sıra:  kaide ve askı kaçıklığı önce ( makine dairesindeki saptırma
    kasnağının yeri onlarla kurulan çizime bağlı ), sarılma açısı ve
    kasnaklar sonra."""
    d, B = {}, dict(A)
    bos = [k for k in CIZIMDEN if k in A and A[k] is None]
    if not bos:
        return d
    if "kabin_tampon_baba" in bos:
        v = [B.get(k) for k in ("kuyu_dibi", "kabin_tampon_boyu", "kabin_carpma_arasi")]
        if all(_sayi(x) for x in v):
            d["kabin_tampon_baba"] = v[0] - v[1] - v[2] - \
                CS.sabitler(cizim_sabitleri(B))["sase_alt_derinlik"]
    if "aski_kaciklik_x" in bos:
        #  Çizimden bulunamıyorsa ( arkadaki karşı ağırlık ) hesabın eski
        #  varsayılanı:  askı ray ekseninde ( 0 ).
        xs = _aski_x(B)
        d["aski_kaciklik_x"] = 0.0 if xs is None else xs
    B.update(d)
    kasnak = {"saptirma_kasnak_capi", "saptirma_kasnak_min_capi"} & set(bos)
    if kasnak or "sarilma_acisi" in bos:
        gc, _hata = cizim_girdisi(B)
    if "sarilma_acisi" in bos and not _cift_sarim(B):
        #  Çift sarımı çizim çizmez ( tek geçiş );  açısı girilmeli.
        alfa = sarim_acisi(gc) if gc is not None else None
        if alfa is not None:
            d["sarilma_acisi"] = alfa
    if kasnak:
        c = _kasnak_caplari(B, _saptirma(gc))
        if c == [] and _sayi(B.get("tahrik_kasnak_capi")):
            #  Saptırma kasnağı yok ( 1:1, makine dairesinde saptırmasız ):  D2 ve
            #  Ds hesapta etkisizdir — tahrik kasnağının çapı verilir ( Kp = 1,
            #  D/d denetimi tahrik kasnağınınkiyle aynı ).
            c = [float(B["tahrik_kasnak_capi"])]
        if c:
            if "saptirma_kasnak_capi" in bos:
                d["saptirma_kasnak_capi"] = round(sum(c) / len(c), 1)
            #  Ds boşsa D2 girilmiş olsa da çizimden:  hesabın kendi kuralı ( Ds
            #  boşsa D2 ) en küçük kasnağı ortalamayla ölçerdi — 2:1'de 240'lık
            #  kabin kasnaklarının D/d denetimi 294 ile yapılırdı.  Girilen D2
            #  çizimin en küçük kasnağından da küçükse türetilmez:  hesap Ds'yi
            #  D2'ye düşürür ( güvenli yön ), çizim D2'nin uyuşmadığını söyler —
            #  yoksa hesap dokunulmamış Ds'yi "ters girilmiş" diye reddederdi.
            D2 = d.get("saptirma_kasnak_capi", B.get("saptirma_kasnak_capi"))
            if "saptirma_kasnak_min_capi" in bos and not (_sayi(D2) and min(c) > D2):
                d["saptirma_kasnak_min_capi"] = min(c)
    return d


def sarim_acisi(g):
    """Çizimdeki halatın tahrik kasnağını sardığı açı ( ° ) — yalnız çizim onu
    TEK BİR SAYI olarak biliyorsa:
      · iki iniş düşey:  180°
      · makine dairesinde saptırma kasnağı halatın yönünü sabitler:  tahrik
        kasnağı ile saptırma kasnağının ortak teğetlerinden
    Makine dairesizde ağırlık tarafındaki iniş kasnağın düzleminde eğikse
    ( HALAT SAPMASI ) açı ağırlığın konumuyla değişir ( ağırlık tepedeyken
    halat kısa, sapma birkaç derece ):  None — hesabın tek açısı buradan
    seçilemez ( çekiş ve kayma denetimleri açıya ters yönde bağlıdır ).
    Çizim kurulamıyorsa da None."""
    try:
        if g["makine"]["yeri"] == "Kuyu üstü":
            from cizim import kuyu_ustu as CKU
            Y = CKU.yerlesim(g)
            if Y.get("hata"):
                return None
            return 180.0 if abs(Y["sapma"][0]) <= 0.5 else None
        from cizim import makine_dairesi as CMD
        Y = CMD.yerlesim(g)
        if Y.get("hata"):
            return None
        sp = Y.get("saptirma")
        if not sp:
            return 180.0
        return round(sp["sarim"], 1) if "sarim" in sp else None
    except Exception:                                  # noqa: BLE001 — çizim zaten reddetti
        return None


def _uyusmazliklar(g, A):
    """[ ( ileti , düzeltme ) ] — hesabın girdisi ile çizimin geometrisinin
    ayrı söylediği büyüklükler.  Düzeltme { girdi : çizimdeki değer } ( ya
    da çizilemeyen bir durumda None ):  ölçüden değiştirmede bağlı büyüklükler
    birlikte güncellenir ( kuyu genişliği değişince L = DBGW … ).  İleti ile
    düzeltme aynı yerde kurulur:  biri değişip öteki eskimesin."""
    liste = []
    #  HALAT SARILMA AÇISI:  tahrik kasnağı ile karşı ağırlığa inen halatın
    #  geometrisinden çıkar;  hesabın tahrik ( kayma ) kontrolüne girer.  Boşsa
    #  çizimden gelir ( cizimden );  girilmişse çizimle aynı olmalı.
    #  ÇİFT SARIM:  çizim halatı kasnağın üzerinden bir kez geçirir;  paftadaki
    #  sarım açısı hesabınkiyle çelişirdi.  Kuyunun geometrisi ( bölüm 11 ) sarım
    #  sayısından bağımsızdır — yalnız çizim durur.
    alfa, sarim = A.get("sarilma_acisi"), sarim_acisi(g)
    if _cift_sarim(A):
        liste.append(("Çift sarımlı kanal:  çizim halatı tahrik kasnağının üzerinden bir kez "
                      "geçirir — çift sarım ( ikinci kasnak, iki geçiş ) henüz çizilemiyor.", None))
        sarim = None
    if sarim is not None and _sayi(alfa) and abs(alfa - sarim) >= 0.5:
        liste.append((f"Halat sarılma açısı:  çizimdeki halat geometrisi α = {sarim:.1f}° veriyor, "
                      f"hesapta {alfa:g}° — α'yı boş bırakın ( çizimden gelir ).",
                      {"sarilma_acisi": round(sarim, 1)}))
    #  SAPTIRMA KASNAKLARI:  hesabın D2'si çizilen kasnakların ortalaması,
    #  Ds'si en küçüğü ( TS EN 81-50 m.5.12:  Dp ortalama çap ).
    cap = kasnaklar(g)
    if cap:
        ort, en_kucuk = sum(cap) / len(cap), min(cap)
        D2, Ds = A.get("saptirma_kasnak_capi"), A.get("saptirma_kasnak_min_capi")
        Ds = Ds if _sayi(Ds) else D2
        yazi = " · ".join(f"{c:g}" for c in cap)
        if _sayi(D2) and abs(D2 - ort) >= 1.0:
            liste.append((f"Saptırma kasnakları:  çizimdeki kasnaklar ( {yazi} ) ortalaması "
                          f"{ort:.1f} mm, hesaptaki D2 {D2:g} — D2'yi boş bırakın ( çizimden gelir ) "
                          "ya da kasnak çaplarını düzeltin.",
                          {"saptirma_kasnak_capi": round(ort, 1)}))
        if _sayi(Ds) and abs(Ds - en_kucuk) >= 0.5:
            liste.append((f"Saptırma kasnakları:  çizimdeki en küçük kasnak {en_kucuk:g} mm, hesaptaki "
                          f"Ds {Ds:g} — Ds'yi boş bırakın ( çizimden gelir ).",
                          {"saptirma_kasnak_min_capi": en_kucuk}))
    #  MAKİNE KİRİŞLERİ RAYLARA OTURUYORSA mesnet aralıkları raylar arasıdır.
    if (g["makine"]["yeri"] == "Kuyu üstü" and A.get("makine_raya_biniyor") == "Kılavuz raylara"
            and _sayi(A.get("yan_yatak_boyu"))
            and abs(A["yan_yatak_boyu"] - g["agirlik"]["ray_arasi"]) >= 0.5):
        liste.append((f"Makine kirişleri karşı ağırlık raylarına oturuyor:  mesnet aralığı raylar "
                      f"arasıdır ( DBGW {g['agirlik']['ray_arasi']:g} ), hesaptaki yan yatak boyu "
                      f"{A['yan_yatak_boyu']:g} — yan yatak boyuna {g['agirlik']['ray_arasi']:g} girin.",
                      {"yan_yatak_boyu": g["agirlik"]["ray_arasi"]}))
    return liste


def tutarlilik(g, A):
    """Hesabın girdisi ile çizimin geometrisi aynı şeyi söylüyor mu?  Aynı
    fiziksel büyüklük iki yerde modelleniyorsa ikisi eşit olmalıdır;
    uyuşmazlık metin listesi olarak döner ( doğru değeriyle ).  g geçerli
    olmalı ( çizimlerin doğrulamasından geçmiş )."""
    return [m for m, _d in _uyusmazliklar(g, A)]


def tutarlilik_duzeltmeleri(g, A):
    """Uyuşmazlıkları gideren girdi değerleri ( { girdi : değer } )."""
    d = {}
    for _m, duz in _uyusmazliklar(g, A):
        d.update(duz or {})
    return d
