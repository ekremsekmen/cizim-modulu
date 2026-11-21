# -*- coding: utf-8 -*-
"""
PAFTA  —  çizimlerin ofisin TİP PROJE FORMATINA yerleştirilmesi

Şablon `sablon/proje_formati.dxf`:  ofisin kendi çiziminden ( TİP PROJE
FORMATI.dwg ) alınmış, hesap programının kullandığıyla AYNI dosya.  3.242 ×
600 mm'lik bir şerit:  solda notlar ve antet ( A4 hücresi ), sağda serbest
alan.  Şablonun birimi PAFTA milimetresidir;  çizimler gerçek ölçüde
( mm ) blok olarak tanımlanır ve paftaya 1/ölçek ile yerleştirilir —
CAD'de blok açılınca ölçüler gerçek boyundadır.

YERLEŞİM ( ofisin 477-8 uygulama projesindeki düzen ):  önce düşey
kesitler ( 1/50 ), sonra planlar ( 1/20 ) konu sırasıyla
sütunlara dizilir;  sıra bozulmaz, sütunlara bölme kâğıdı en kısa tutanıdır
( _sutunlar ).  Düşey kesitler paftanın yüksekliğine sığmazsa ara katlar
kırılır ( referans proje ve LiftDesigner gibi ).  Çerçevenin sağı içeriğin
sağıdır:  içerik uzunsa SAĞA uzar, kısaysa kısalır — aşağı taşmaz.

KÂĞIT ENİ ( 19 Kas, kullanıcı:  "projeyi indirirken 60 cm ya da 90 cm
seçebilmeliyim … kağıttan da tasarruf edelim ama hiç bir şey bozulmasın" ):
çizicinin rulosunun ENİ paftanın YÜKSEKLİĞİDİR — şerit rulo boyunca uzar,
kâğıdın masrafı şeridin boyudur.  Ofisin şablonu 60 cm'lik rulonundur ( 600
mm );  90 cm'de çerçeve yukarı uzar ( sablonu_uzat ), hesap sayfaları üç
satır olur, kesitler 880 mm'ye dek kırılmaz.  Çizimlerin ölçeği iki kâğıtta
da aynıdır ( 1/50, 1/20 ):  kâğıda sığdırmak için küçültülmez.

ANTET:  bilinen değerler çizim girdisinden yazılır;  çizimin bilmediği
değerler ( taşıma kapasitesi, asansör sınıfı, motor gücü ) BOŞ bırakılır —
şablondaki örnek değerler ( "300 KG", "2,67 KW" … ) projeyi yanlış tanıtırdı.
"""

import io
import os
import tempfile

import ezdxf
from ezdxf import bbox
from ezdxf import zoom

from cizim import asamalar
from cizim import cizimler
from cizim import dxf
from cizim import dusey
from cizim import eleman
from cizim import geometri
from cizim import grup
from cizim import hesap_isareti
import math

SABLON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sablon", "proje_formati.dxf"
)
#  Şablonun kendi koordinatları ( pafta mm ) — hesap programının dxf_export.py
#  sabitleriyle aynı;  şablon değişirse _sablon_dogrula yakalar.
BANT = (-4215.8, 1159.4, -973.8, 1759.4)
KAPAK_HUCRESI = (-4215.8, 1159.4, -4012.5, 1448.3)
SERBEST = (-4012.5, 1159.4, -973.8, 1759.4)
KENAR = 10.0  # serbest alanın kenarından ilk çizime
#  Çizimler arası ( her çizimin kendi çerçevesi var ):  19 Kas'a dek 12 mm — kullanıcı
#  "birbirlerine yakın olsun" dedi;  6 mm'de çerçeveler yine ayrı okunur ( ÇİZİM KABULÜ )
ARA = 6.0

#  Rulonun eni ( mm ) = çerçevenin yüksekliği.  Şablon 600 mm'dir ( BANT );  KAGIT varsayılan
KAGIT_ENLERI = (600, 900)
KAGIT = 600

#  Antetteki DEĞER hücreleri:  ( şablondaki örnek yazı, yeri ) — örnek yazı
#  yerinde değilse şablon değişmiş demektir, pafta üretilmez.
ANTET = {
    "yuk": ("300 KG (4 KİŞİ)", (-4188.7, 1400.7)),
    "hiz": ("1,00 m/sn", (-4162.0, 1400.7)),
    "durak": ("0,1/2 DURAK", (-4143.2, 1400.7)),
    "seyir": ("3500", (-4112.1, 1400.7)),
    "kabin_g": ("950", (-4092.8, 1400.3)),
    "kabin_d": ("950", (-4078.3, 1400.5)),
    "standart": ("TS EN 81-20", (-4063.5, 1400.4)),
    "sinif": ("Sınıf I", (-4187.5, 1392.0)),
    "aski": ("2:1", (-4162.3, 1392.0)),
    "adet": ("1", (-4134.6, 1392.3)),
    "tahrik": ("Elektrikli", (-4115.1, 1392.4)),
    "ray": ("70*70*9", (-4091.8, 1392.6)),
    "motor": ("2,67 KW", (-4185.6, 1385.2)),
    "olcek": ("1/20 1/30 1/50  ", (-4169.4, 1384.9)),
}

#  Paftadaki çizimler, sırasıyla ( makine dairesizde kuyu üstü planı,
#  makine dairelide makine dairesi ve delik planı )
#  Sonda LiftDesigner'ın görünüşleri:  kasnak düzenlemesi, giriş ve kapı yan kesiti;
#  en sonda asansörün veri tablosu ( veri_tablosu ).
SIRA_MRL = (
    "kuyu_kesiti_yan",
    "kuyu_kesiti_on",
    "kuyu_plani",
    "kabin_ustu",
    "kuyu_dibi",
    "kuyu_ustu",
    "kasnak_duzeni",
    "giris",
    "kapi_kesiti",
    "veriler",
)
SIRA_MD = (
    "kuyu_kesiti_yan",
    "kuyu_kesiti_on",
    "kuyu_plani",
    "kabin_ustu",
    "kuyu_dibi",
    "makine_dairesi",
    "delik_plani",
    "kasnak_duzeni",
    "giris",
    "kapi_kesiti",
    "veriler",
)


def _nokta(e):
    t = e.dxftype()
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "LWPOLYLINE":
        return [(q[0], q[1]) for q in e.get_points("xy")]
    return []


def _a4_mu(e, tol=0.5):
    """Hesap programının A4 çerçevesi mi:  kapalı, dört köşeli, 210 × 297 mm."""
    p = _nokta(e)
    if not (e.dxftype() == "LWPOLYLINE" and e.closed and len(p) == 4):
        return False
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return abs(max(xs) - min(xs) - 210.0) <= tol and abs(max(ys) - min(ys) - 297.0) <= tol


def _sablon_dogrula(d):
    """Dış çerçevenin köşeleri, kapak hücresi ve antetin değer hücreleri yerinde mi."""
    msp = d.modelspace()
    hata = []
    kutular = []
    for e in msp.query("LWPOLYLINE"):
        p = _nokta(e)
        kutular.append(
            (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))
        )
    if not any(all(abs(a - b) <= 0.5 for a, b in zip(k, KAPAK_HUCRESI)) for k in kutular):
        hata.append(f"kapak hücresi {KAPAK_HUCRESI} yok")
    kose = {(round(p[0], 1), round(p[1], 1)) for e in msp.query("LINE") for p in _nokta(e)}
    for x, y in ((BANT[0], BANT[1]), (BANT[2], BANT[1]), (BANT[0], BANT[3]), (BANT[2], BANT[3])):
        if not any(abs(kx - x) <= 0.5 and abs(ky - y) <= 0.5 for kx, ky in kose):
            hata.append(f"dış çerçeve köşesi ({x}, {y}) yok")
    for ad, (ornek, yer) in ANTET.items():
        if _antet_yazisi(d, yer, ornek) is None:
            hata.append(f"antette {ad} hücresi ( '{ornek.strip()}' ) yok")
    if hata:
        raise ValueError("PROJE FORMATI ŞABLONU UYUŞMUYOR — " + " · ".join(hata))


def _antet_yazisi(d, yer, ornek=None):
    for e in d.modelspace().query("TEXT"):
        p = e.dxf.insert
        if abs(p.x - yer[0]) <= 0.2 and abs(p.y - yer[1]) <= 0.2 and (ornek is None or e.dxf.text == ornek):
            return e
    return None


def kagit_eni(deger=None):
    """İstekteki kâğıt eni ( mm ):  boşsa ofisin şablonununki ( KAGIT );  600 ya da 900
    değilse ValueError ( girilen değer ya kullanılır ya iş durur )."""
    if deger is None or deger == "":
        return KAGIT
    try:
        k = float(str(deger).replace(",", "."))
    except ValueError:
        k = None
    if isinstance(deger, bool) or k not in KAGIT_ENLERI:
        raise ValueError(f"Kâğıt eni 60 ya da 90 cm olabilir ( gelen:  {deger!r} ).")
    return int(k)


def ust_kenar(kagit=KAGIT):
    """Çerçevenin üst kenarının y'si ( pafta mm ):  alt kenar yerinde, kâğıt eni kadar yukarısı."""
    return BANT[1] + kagit


def cizim_yuksekligi(kagit=KAGIT):
    """Çizimlerin sütununun yüksekliği:  çerçeve, üstte ve altta KENAR payıyla ( 60 cm'de 580 mm ) —
    düşey kesit bundan uzunsa ara katları kırılır ( cizim_listesi )."""
    return kagit - 2 * KENAR


def sablonu_uzat(d, kagit=KAGIT):
    """Şablonu kâğıdın enine uzatır ( 600 mm'de dokunmaz ):  çerçevenin üst kenarı ve notlar
    YUKARI kayar, sol / sağ kenar ve notların sınır çizgisi uzar;  kapak hücresi ve antet
    ( sol altta ) yerinde kalır.  Kayan:  ucu üst kenarda olan çizgi uçları ve notlar
    bölgesinin ( kapak hücresinin üstü, soldaki blok ) içinde duran yazılar.  Şablon önce
    doğrulanır ( _sablon_dogrula — 600 mm'lik hâliyle )."""
    fark = kagit - (BANT[3] - BANT[1])
    if abs(fark) < 1e-6:
        return
    msp = d.modelspace()
    for e in msp.query("LINE"):
        for uc in ("start", "end"):
            p = e.dxf.get(uc)
            if abs(p.y - BANT[3]) <= 0.5 and BANT[0] - 0.5 <= p.x <= BANT[2] + 0.5:
                e.dxf.set(uc, (p.x, p.y + fark, p.z))
    for e in msp.query("TEXT MTEXT"):
        p = e.dxf.insert
        if BANT[0] - 0.5 <= p.x < SERBEST[0] and KAPAK_HUCRESI[3] + 0.5 < p.y < BANT[3] + 0.5:
            e.translate(0, fark, 0)


def cerceveyi_tasi(d, sag, eski=None, kagit=KAGIT):
    """Çerçevenin sağ kenarı `eski`den `sag`a kayar — içerik çerçeveden uzunsa çerçeve UZAR,
    kısaysa KISALIR ( kâğıt boşa gitmez;  19 Kas ).  Sağ kenar çizgisi bütünüyle kayar;  alt
    ve üst kenarın çizgileri ( şablonun üst kenarı iki parça ) yeni sağa uzar ya da orada
    kesilir, bütünüyle dışta kalan silinir.  Başka varlığa dokunulmaz.  eski:  çerçevenin
    şimdiki sağı ( hesap programı taşımış olabilir )."""
    eski = BANT[2] if eski is None else eski
    alt, ust = BANT[1], ust_kenar(kagit)
    msp = d.modelspace()
    for e in list(msp.query("LINE")):
        a, b = e.dxf.start, e.dxf.end
        if abs(a.x - eski) <= 0.5 and abs(b.x - eski) <= 0.5:
            if min(a.y, b.y) >= alt - 0.5 and max(a.y, b.y) <= ust + 0.5:
                e.dxf.start, e.dxf.end = (sag, a.y, a.z), (sag, b.y, b.z)
            continue
        if abs(a.y - b.y) > 0.01 or not (abs(a.y - alt) <= 0.5 or abs(a.y - ust) <= 0.5):
            continue
        xa = sag if abs(a.x - eski) <= 0.5 else min(a.x, sag)
        xb = sag if abs(b.x - eski) <= 0.5 else min(b.x, sag)
        if abs(xb - xa) < 0.01:
            msp.delete_entity(e)
        else:
            e.dxf.start, e.dxf.end = (xa, a.y, a.z), (xb, b.y, b.z)


def cizim_olcegi(ad):
    """Çizimin paftadaki ölçeği ( 1/olcek ) — başlıkta yazmasa da ( OLCEKSIZ )."""
    return cizimler.OLCEKLER.get(ad, 20)


def olcek_yazisi(olcekler):
    """Antetin ve kapağın ölçek hücresi:  "1/20 1/50"."""
    return " ".join(f"1/{o:g}" for o in sorted(set(olcekler)))


def antet_degerleri(g, olcekler):
    """Antete yazılacaklar;  boş dize = çizimin bilmediği değer ( boş kalır )."""
    dy, kb, kr = g["dusey"], g["kabin"], g["kabin_ray"]
    kotlar = dusey.durak_kotlari(g)[0]
    return {
        "yuk": "",
        "sinif": "",
        "motor": "",
        "hiz": f"{dy['beyan_hizi']:.2f} m/sn".replace(".", ","),
        "durak": f"{dy['durak_adedi']} DURAK",
        "seyir": f"{kotlar[-1]:g}",
        "kabin_g": f"{kb['genislik']:g}",
        "kabin_d": f"{kb['derinlik']:g}",
        "standart": "TS EN 81-20",
        "aski": "1:1" if (g.get("aski") or {}).get("duzen") == "Doğrudan" else "2:1",
        "adet": "1",
        "tahrik": "Elektrikli",
        #  Avanda ray seçilmemiştir ( cizim/avan_kipi.py ):  hücre boş
        "ray": "" if g["proje"].get("avan") else f"{kr['b']:g}*{kr['h']:g}",
        "olcek": olcek_yazisi(olcekler),
    }


def _antet(d, g, olcekler):
    msp = d.modelspace()
    for ad, deger in antet_degerleri(g, olcekler).items():
        e = _antet_yazisi(d, ANTET[ad][1])
        if deger:
            e.dxf.text = deger
        else:
            msp.delete_entity(e)


def sira(g):
    """Bu asansörün paftasındaki çizimler, sırasıyla;  tek kuyuda kuyunun ortak
    çizimleri ( grup.BIRLESIK — kuyunun çizimi olarak bir kez ) yok."""
    s = SIRA_MD if (g.get("makine") or {}).get("yeri") == "Makine dairesi" else SIRA_MRL
    #  Avanda kasnak düzenlemesi DE vardır ( 17 Kas, kullanıcı:  "makine daireli dairesiz fark
    #  etmez, kasnak düzenlemesini geri açalım" ):  sarım açısı avanda da hesaplanır ve
    #  150°'nin altında uyarılır — açının çizimi paftada olmalı.  Kasnak çaplarının hazır
    #  asansörün olduğu çizimin kendisinde yazar ( kasnak_duzeni.AVAN_NOTU )
    if (g.get("proje") or {}).get("grup_sirasi"):
        s = tuple(a for a in s if a not in grup.BIRLESIK)
    return s


def cizilir(g, ad):
    """Çizim bu asansör için kurulur mu:  paftasında ya da tek kuyuda kuyunun ortak
    çiziminde ( grup.cizimleri — ekranda tıklanan ölçünün kaynağı o asansörün
    kendi çiziminden çözülür )."""
    return ad in sira(g) or (bool((g.get("proje") or {}).get("grup_sirasi")) and ad in grup.cizimleri([g]))


def cizim_listesi(g, seritler=(), kagit=KAGIT):
    """( ad, başlık, ölçek, elemanlar — çerçeveli ) ;  hata varsa ValueError.
    seritler:  çizimlerin künye şeridine yazılacaklar ( çok asansörlü
    projede asansörün adı — hangi kuyunun çizimi olduğu okunsun ).
    kagit:  rulonun eni ( mm ) — düşey kesit sütuna ( cizim_yuksekligi ) sığmazsa kırılır."""
    cikti, hata = [], []
    #  Serbest alanın yüksekliği ( kenarlar düşülünce ), çizim biriminde
    yukseklik = cizim_yuksekligi(kagit)
    for ad in sira(g):
        dogrula, ciz, baslik = cizimler.CIZIMLER[ad]
        h = dogrula(g)
        if h:
            hata += [f"{ad}: {x}" for x in h]
            continue
        olcek = cizim_olcegi(ad)
        e = ciz(g, azami=yukseklik * olcek) if ad in cizimler.OLCEKLER else ciz(g)
        cikti.append(
            (
                ad,
                cizimler.plan_basligi(g, ad, baslik),
                olcek,
                geometri.cerceveli(
                    e,
                    cizimler.plan_basligi(g, ad, baslik),
                    olcek,
                    seritler=seritler,
                    olcekli=ad not in cizimler.OLCEKSIZ,
                    uyari=hesap_isareti.not_satirlari(g["proje"].get("hesap_uygun_degil") or []),
                ),
            )
        )
    if hata:
        raise ValueError("Pafta çizilemiyor:  " + " · ".join(hata))
    return cikti


def _sira_bolmesi(boyutlar, yukseklik, gruplar):
    """SIRA BOZULMADAN sütunlara bölme:  sütun ardışık çizimlerdir;  bölme, sütun enlerinin
    ( ve aralıklarının ) toplamını EN KÜÇÜK yapandır ( dinamik programlama;  çizim sayısının
    karesi kadar adım ).  Eşit boyda bölmelerden son sütunu en kısa olan seçilir:  öndeki
    sütunlar dolu kalır."""
    n = len(boyutlar)
    en_iyi, once = [0.0] + [math.inf] * n, [0] * (n + 1)
    for j in range(1, n + 1):
        y = en = 0.0
        for i in range(j - 1, -1, -1):
            if gruplar[i] != gruplar[j - 1]:
                break
            y += boyutlar[i][1] + (ARA if i < j - 1 else 0.0)
            if i < j - 1 and y > yukseklik + 1e-6:
                break
            en = max(en, boyutlar[i][0])
            aday = en_iyi[i] + en + (ARA if i else 0.0)
            if aday < en_iyi[j] - 1e-6:
                en_iyi[j], once[j] = aday, i
    sutunlar, j = [], n
    while j:
        sutunlar.insert(0, list(range(once[j], j)))
        j = once[j]
    return sutunlar


def _bosluk_bolmesi(boyutlar, yukseklik, gruplar):
    """BOŞLUĞU DOLDURAN bölme:  çizimler sırayla, kendi grubunun altında yer kalan
    sütunlarından EN AZ GENİŞLEYENİNE girer ( eşitse soldakine ) — genişleme yeni bir
    sütundan ( eni + ARA ) pahalıysa yeni sütun açılır.  90 cm'de kesitlerin altında
    kalan ~250 mm'yi sıradaki plan değil, oraya sığan çizim doldurur."""
    sutunlar = []
    for k, (en, boy) in enumerate(boyutlar):
        aday = None
        for s in sutunlar:
            if s["grup"] != gruplar[k] or s["boy"] + ARA + boy > yukseklik + 1e-6:
                continue
            artis = max(0.0, en - s["en"])
            if aday is None or artis < aday[0] - 1e-6:
                aday = (artis, s)
        if aday is not None and aday[0] < en + ARA - 1e-6:
            s = aday[1]
            s["en"], s["boy"] = max(s["en"], en), s["boy"] + ARA + boy
            s["sira"].append(k)
        else:
            sutunlar.append({"grup": gruplar[k], "en": en, "boy": boy, "sira": [k]})
    return [s["sira"] for s in sutunlar]


def sutunlar_boyu(boyutlar, sutunlar):
    """Sütunların kapladığı boy ( mm ):  enlerinin toplamı ve aralıkları."""
    return sum(max(boyutlar[i][0] for i in s) for s in sutunlar) + ARA * max(0, len(sutunlar) - 1)


def _sutunlar(boyutlar, yukseklik, gruplar=None):
    """Çizimleri sütunlara böler:  [ [ sıra no, … ], … ] — sütunun çizimleri üstten aşağı,
    aralarında ARA, `yukseklik`e sığar;  eni en geniş çiziminin eni.  İki bölmeden şeridi
    ( kâğıdı ) kısa tutanı:  sırayı bozmayan ( _sira_bolmesi ) — boşluğu dolduran
    ( _bosluk_bolmesi ) ancak 1 mm'den çok kısaltırsa seçilir.  gruplar:  her çizimin grubu
    ( kuyu grubunun ortak çizimleri, her asansörün kendi çizimleri ) — bir sütunda iki
    grubun çizimi olmaz, grupların sütunları sırayla.  Sütuna tek başına sığmayan çizim
    ( kırılamayan kesit ) kendi sütununa girer.  19 Kas'a dek sıradaki çizim sığmayınca yeni
    sütun açılıyordu ( geniş bir planın yanına dar bir tablo düşünce sütun boşuna genişliyor,
    90 cm'de kesitin altı boş kalıyordu )."""
    gruplar = list(gruplar) if gruplar is not None else [0] * len(boyutlar)
    sira = _sira_bolmesi(boyutlar, yukseklik, gruplar)
    bosluk = _bosluk_bolmesi(boyutlar, yukseklik, gruplar)
    return bosluk if sutunlar_boyu(boyutlar, bosluk) < sutunlar_boyu(boyutlar, sira) - 1.0 else sira


def yerlesim(boyutlar, x0=None, kagit=KAGIT, gruplar=None):
    """Pafta mm'sinde çizim boyutlarından ( g, y ) sol-alt köşeler ve çerçevenin
    gereken sağ kenarı:  sütun sütun ( _sutunlar ), üstten aşağı, soldan sağa;  sütunun
    çizimleri sola yaslı.  x0:  ilk sütundan önceki içeriğin sağı ( hesap sayfaları;  yoksa
    serbest alanın solu ).  Sağ kenar son sütunun KENAR sağıdır:  çerçeve içerik kadar.
    gruplar:  çizimlerin grubu ( _sutunlar ).

    Sütuna sığmayan tek çizim ( en kısa kırık hâli bile uzun kesit — gerçek 800 KG:  10 durak,
    giriş katı arada kalır, 60 cm'de 583,9 mm ) çerçevenin dikey ORTASINA konur:  üstte ve
    altta eşit pay ( ~8 mm ).  19 Kas'a dek üstten diziliyordu, alt payın 4 mm'sine giriyordu."""
    x0 = SERBEST[0] if x0 is None else x0
    ust = ust_kenar(kagit) - KENAR
    x = x0 + KENAR
    yerler = [None] * len(boyutlar)
    for sutun in _sutunlar(boyutlar, cizim_yuksekligi(kagit), gruplar):
        y = ust
        if len(sutun) == 1 and boyutlar[sutun[0]][1] > cizim_yuksekligi(kagit):
            y = BANT[1] + (kagit + boyutlar[sutun[0]][1]) / 2
        for i in sutun:
            yerler[i] = (x, y - boyutlar[i][1])
            y -= boyutlar[i][1] + ARA
        x += max(boyutlar[i][0] for i in sutun) + ARA
    return yerler, (x - ARA if boyutlar else x) + KENAR


def _copleri_sil(msp):
    """Şablondaki görünmez çöp çizgileri siler ( hesap programının
    dxf_export._copleri_sil'i gibi ):  boyu 0,01 mm'den kısa ya da düzlemin
    milyonlarca mm altında — YAZı1 katmanında iki çizgi z = −150 milyon mm'de,
    dosyanın sınırlarını ( EXTMIN ) bozuyordu."""
    for e in list(msp.query("LINE")):
        a, b = e.dxf.start, e.dxf.end
        if (a - b).magnitude < 0.01 or max(abs(a.z), abs(b.z)) > 1e6:
            msp.delete_entity(e)


def katmanlari_onar(d):
    """Şablonun kendi katmanlarından dördü ( ÇERÇ, YAZı, t-çap, YAZı1 ) dosyada
    olmayan malzeme ve çizim stili kayıtlarını gösteriyor;  AutoCAD'in AUDIT'i
    bunları 16 hata sayıyordu ( AcCoreConsole ile ölçüldü ).  Geçerli
    kayıtlara ( "Global" malzeme, "Normal" çizim stili ) bağlanır.  Avan
    paketinin paftası da ( ciktilar/dxf_cikti — çizimsiz, birlestir'den
    geçmez;  23 Eki'ye dek 16 hatayla iniyordu )."""
    db = d.entitydb
    malzeme = d.materials.get("Global").dxf.handle
    stil = d.rootdict.get("ACAD_PLOTSTYLENAME").get("Normal").dxf.handle

    def tur(h):
        e = db.get(h) if h else None
        return e.dxftype() if e is not None else None

    #  "EE" ve "F" dosyada VAR ama malzeme / çizim stili değil — türüne bakılır
    for k in d.layers:
        if tur(k.dxf.get("material_handle")) != "MATERIAL":
            k.dxf.material_handle = malzeme
        if tur(k.dxf.get("plotstyle_handle")) != "ACDBPLACEHOLDER":
            k.dxf.plotstyle_handle = stil


def bloklar(g, kagit=KAGIT):
    """Paftanın çizimleri, sırasıyla:  [ ( ad, başlık, ölçek, elemanlar ) ] —
    blok adı "CIZIM_" + ad.upper().  g:  tek asansörün girdisi ya da çok
    asansörlü projede girdilerin listesi ( asansörler sırayla, her çizimin
    şeridinde asansörün adı;  kuyu grubu varsa önce grubun planı — "kuyu_grubu" ).
    DXF ( _yerlestir ) ve PDF ( ciktilar/pafta_pdf ) aynı listeyi AYNI kâğıt eniyle
    kullanır ( kesitin kırığı kâğıda bağlı )."""
    return [c for _grup, c in _gruplu_bloklar(g, kagit)]


def _gruplu_bloklar(g, kagit=KAGIT):
    """bloklar ve her çizimin grubu:  [ ( grup, çizim ) ] — 0 kuyu grubunun ortak çizimleri,
    i. asansörün çizimleri i ( yerleşimde bir sütuna iki grubun çizimi girmez )."""
    gler = g if isinstance(g, (list, tuple)) else [g]
    #  Kuyu grubunun planı önde ( asansörlerin kendi çizimleri ardından — cizim/grup.py )
    liste = [(0, c) for c in grup.pafta_cizimleri(gler, cizim_yuksekligi(kagit))]
    for i, g_ in enumerate(gler):
        coklu = len(gler) > 1
        #  Paket çizimleri paftaya dizerken ekran hangi asansörde olduğunu görür ( uç akışlı
        #  istekte — cizim/asamalar;  aşama kodu uclar/uc_ortak.PAKET_ASAMALARI'nın )
        if coklu:
            asamalar.ayrinti(f"Asansör {i + 1} / {len(gler)}", kod="cizimler")
        #  Çok asansörlü projeden yalnız biri çizilebildiyse ( avan paketi — uclar/avan_cizimi )
        #  şeritte adı yine yazar:  hangi asansörün çizimi olduğu belli olsun
        adli = coklu or g_["proje"].get("cok_asansorlu")
        for ad, baslik, olcek, e in cizim_listesi(g_, (g_["proje"]["asansor"],) if adli else (), kagit):
            #  Blok adı asansörle birlikte:  iki kuyunun kesiti aynı bloğu ezmesin
            liste.append((i + 1, (f"{ad}_{i + 1}" if coklu else ad, baslik, olcek, e)))
    return liste


def kunyeler(g):
    """bloklar( g ) ile aynı sırada her çizimin projesi ve asansörü:
    [ { proje, asansor } ] — ayrı sayfalı PDF'in anteti ( pdf.sayfalar )."""
    gler = g if isinstance(g, (list, tuple)) else [g]
    return grup.kunyeler(gler) + [
        {"proje": g_["proje"]["ad"], "asansor": g_["proje"]["asansor"]} for g_ in gler for _ad in sira(g_)
    ]


def blok_adi(ad):
    return f"CIZIM_{ad.upper()}"


def _yerlestir(d, g, x0=None, sag_eski=None, kagit=KAGIT):
    """Çizimleri belgeye blok olarak yerleştirir;  çerçevenin sağı son sütuna gelir."""
    gruplu = _gruplu_bloklar(g, kagit)
    liste = [c for _grup, c in gruplu]
    dxf.hazirla(d)
    boyutlar, kutular = [], []
    for _ad, _baslik, olcek, e in liste:
        bx0, by0, bx1, by1 = geometri.sinir(e)
        kutular.append((bx0, by0))
        boyutlar.append(((bx1 - bx0) / olcek, (by1 - by0) / olcek))
    yerler, sag = yerlesim(boyutlar, x0, kagit, [grup_ for grup_, _c in gruplu])
    cerceveyi_tasi(d, sag, sag_eski, kagit)
    msp = d.modelspace()
    yerlesen = []
    for (ad, baslik, olcek, e), (bx, by), (px, py), (w, h) in zip(liste, kutular, yerler, boyutlar):
        blok = d.blocks.new(name=blok_adi(ad), base_point=(bx, by))
        dxf.ciz(blok, e, olcek, blokta=True)
        msp.add_blockref(
            blok.name, (px, py), dxfattribs={"xscale": 1.0 / olcek, "yscale": 1.0 / olcek, "layer": "0"}
        )
        yerlesen.append({"ad": ad, "baslik": baslik, "olcek": olcek, "kutu": (px, py, px + w, py + h)})
    x0_, y0_, x1_, y1_ = BANT[0], BANT[1], sag, ust_kenar(kagit)
    msp.dxf.extmin, msp.dxf.extmax = (x0_, y0_, 0), (x1_, y1_, 0)
    msp.dxf.limmin, msp.dxf.limmax = (x0_, y0_), (x1_, y1_)
    zoom.window(msp, (x0_ - 10, y0_ - 10), (x1_ + 10, y1_ + 10))
    return {"cizimler": yerlesen, "sag": sag, "olcekler": [c[2] for c in liste]}


def belge(g, kagit=KAGIT):
    """Doldurulmuş pafta ( ezdxf belgesi ) ve yerleşim bilgisi;  kagit:  rulonun eni ( mm )."""
    d = ezdxf.readfile(SABLON)
    _sablon_dogrula(d)
    katmanlari_onar(d)
    _copleri_sil(d.modelspace())
    sablonu_uzat(d, kagit)
    bilgi = _yerlestir(d, g, kagit=kagit)
    _antet(d, g, bilgi["olcekler"])
    _kullanilmayanlari_sil(d)
    return d, bilgi


def birlestir(hesap_dxf, g, kagit=KAGIT):
    """TAM PROJE:  hesap programının TİP PROJE FORMATINA dizdiği DXF'e
    ( kapak + hesap sayfaları ) çizimleri ekler — son hesap sayfasının
    sağından başlayarak;  çerçevenin sağı son çizim sütununa gelir.  Antete
    dokunulmaz:  hesap programının kapağı onun yerindedir.

    hesap_dxf:  dosya yolu.  g:  tek girdi ya da asansörlerin girdileri
    ( listede sırayla dizilir ).  kagit:  rulonun eni ( mm ) — hesap DXF'i aynı
    kâğıda dizilmiş olmalı ( çerçevenin üst kenarı orada aranır ).  Dönen:  ( belge, bilgi )."""
    d = ezdxf.readfile(hesap_dxf)
    msp = d.modelspace()
    #  Çerçevenin şimdiki sağ kenarı:  üst kenar çizgisinin en sağ ucu
    ust = [
        p.x for e in msp.query("LINE") for p in (e.dxf.start, e.dxf.end) if abs(p.y - ust_kenar(kagit)) <= 0.5
    ]
    if not ust or min(ust) > BANT[0] + 0.5:
        raise ValueError(f"Hesap DXF'inde {kagit / 10:g} cm'lik TİP PROJE FORMATI çerçevesi bulunamadı.")
    sag_eski = max(ust)
    #  Hesap sayfalarının sağı:  A4 çerçevelerinin en sağ ucu.  Hesap programı
    #  çerçeveleri 0 katmanına çizer ( orada şablonun kendi çizgileri de var ),
    #  bu yüzden çerçeve ŞEKLİYLE tanınır:  kapalı, dört köşeli, 210 × 297.
    sayfalar = [q[0] for e in msp.query("LWPOLYLINE") if _a4_mu(e) for q in _nokta(e)]
    #  Hesap programının koyduğu çizim blokları da ( elektrik projesi — alt satırın
    #  başında, cizim/elektrik ):  çizimler onların da sağından başlar
    sayfalar += [
        bbox.extents([e]).extmax.x for e in msp.query("INSERT") if e.dxf.name.startswith(blok_adi(""))
    ]
    x0 = max(sayfalar) if sayfalar else SERBEST[0]
    katmanlari_onar(d)
    bilgi = _yerlestir(d, g, x0, sag_eski, kagit)
    bilgi["hesap_sagi"] = x0
    _kullanilmayanlari_sil(d)
    return d, bilgi


AILELER = {"times.ttf": "Times New Roman", "arialuni.ttf": "Arial Unicode MS", "arial.ttf": "Arial"}


def _kullanilmayanlari_sil(d):
    """Hiçbir yazının ve ölçü stilinin kullanmadığı yazı stillerini, hiçbir
    ölçünün kullanmadığı ölçü stillerini siler ( AutoCAD'in PURGE'ü gibi ).
    Şablon ve hesap programının DXF'i 30'a yakın stil taşıyordu ( "dddddddddd",
    "STYLE1", "ODA" … — 12 Eki );  AutoCAD açılışta bulamadığı yazı tiplerini
    simplex.shx'e düşürüp tek tek bildiriyordu.  Kalanlar şablonun kendi antet
    yazılarınındır.  Dosyanın varsayılan stilleri ( AutoCAD'de yeni yazı ve
    ölçü bunlarla çizilir ) çizimin stilleri olur — şablonunki ezdxf'in
    "EZDXF" ölçü stiliydi ( OpenSans yazı tipi, DIMLFAC 100 )."""
    if dxf.YAZI_TIPI in d.styles:
        d.header["$TEXTSTYLE"] = dxf.YAZI_TIPI
    #  Şablonun stillerine yazı tipinin AİLE adı da:  AutoCAD TrueType'ı önce
    #  aileden bulur — Mac'te dosya adları farklı ( times.ttf, ARIALUNI.TTF
    #  bulunamayıp simplex.shx'e düşüyordu;  dxf.hazirla'daki Arial gibi )
    for st in d.styles:
        aile = AILELER.get(st.dxf.get("font", "").lower())
        if aile and not st.has_extended_font_data:
            st.set_extended_font_data(aile, bold=False, italic=False)
    varsayilan = dxf.olcu_stili(d, 20)
    d.header["$DIMSTYLE"] = varsayilan
    yazilar, olculer = set(), set()
    for yer in [d.modelspace(), *d.blocks]:
        for e in yer:
            if e.dxftype() in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF"):
                yazilar.add(e.dxf.get("style", "Standard").upper())
            elif e.dxftype() == "INSERT":
                yazilar.update(a.dxf.get("style", "Standard").upper() for a in e.attribs)
            elif e.dxftype() == "DIMENSION":
                olculer.add(e.dxf.get("dimstyle", "Standard").upper())
    olculer.add(str(d.header.get("$DIMSTYLE", "Standard")).upper())
    for s in list(d.dimstyles):
        if s.dxf.name.upper() not in olculer | {"STANDARD"}:
            d.dimstyles.remove(s.dxf.name)
    yazilar.update(s.dxf.get("dimtxsty", "Standard").upper() for s in d.dimstyles)
    yazilar.add(str(d.header.get("$TEXTSTYLE", "Standard")).upper())
    for s in list(d.styles):
        #  Biçim ( shape ) dosyaları adsızdır ve çizgi tiplerinden kullanılır
        if s.dxf.name and not s.dxf.flags & 1 and s.dxf.name.upper() not in yazilar | {"STANDARD"}:
            d.styles.remove(s.dxf.name)


def yaz(g, kagit=KAGIT) -> bytes:
    d, _ = belge(g, kagit)
    with tempfile.TemporaryDirectory() as klasor:
        yol = os.path.join(klasor, "pafta.dxf")
        d.saveas(yol)
        with open(yol, "rb") as f:
            return f.read()


def _maskeleri_ac(d):
    """Yazı maskelerini ( MTEXT arka planı, ölçüde dimtfill ) ezdxf'in çizdiği
    WIPEOUT'a çevirir:  ezdxf ( 1.4 ) MTEXT'in arka planını çizmiyor, AutoCAD
    çiziyor ( CDX.MASKE_PAYI ).  Yalnız önizlemenin kopyasında;  her maskenin
    WIPEOUT'u yazısıyla birlikte bloğun sonuna alınır ( örtü kendinden önce
    çizileni örter ).  Kutu yazının kendisinden:  tek satır, ortası ( 4 · 5 · 6 )
    ya da altı ( 7 · 8 · 9 ) hizalı;  en harflerin gerçek eninden
    ( eleman.yazi_eni — ezdxf'in MTEXT kutusu bu yazılarda kayıktı )."""

    for blok in d.blocks:
        for m in list(blok.query("MTEXT")):
            if not m.dxf.get("bg_fill", 0):
                continue
            h = m.dxf.char_height
            w = eleman.yazi_eni(m.plain_text(), h / dxf.BUYUK_HARF)
            ap = m.dxf.get("attachment_point", 1)
            x0 = {0: 0.0, 1: -w / 2.0, 2: -w}[(ap - 1) % 3]
            y0 = {0: -h, 1: -h / 2.0, 2: 0.0}[(ap - 1) // 3]
            pay = (m.dxf.get("box_fill_scale", 1.5) - 1.0) * h / 2.0
            a = math.radians(m.dxf.get("rotation", 0.0))
            c, s_ = math.cos(a), math.sin(a)
            ix, iy = m.dxf.insert.x, m.dxf.insert.y
            koseler = [
                (x0 - pay, y0 - pay),
                (x0 + w + pay, y0 - pay),
                (x0 + w + pay, y0 + h + pay),
                (x0 - pay, y0 + h + pay),
            ]
            blok.add_wipeout([(ix + u * c - v * s_, iy + u * s_ + v * c) for u, v in koseler])
            yazi = m.copy()
            blok.delete_entity(m)
            blok.add_entity(yazi)


def onizleme(d) -> str:
    """Paftanın SVG önizlemesi ( ezdxf'in kendi çizicisiyle, DXF'ten ) —
    ekranda görmek için;  asıl çıktı DXF'tir.

    ezdxf ( 1.4 ) ölçekli bloğun içindeki taramanın desen çizgilerini
    ölçeklemiyor:  desen blok ölçeğinin tersi kadar seyrek çıkıyordu ( 1/50
    kesitte duvarda tek çizgi ).  AutoCAD deseni doğru ölçekler;  DXF'e
    dokunulmaz — önizleme bir KOPYADA yalnız taramaları bloklardan çıkarır
    ( öbür parçalar blokta kalır:  bütün blok açılınca ölçü yazıları da
    yanlış ölçekleniyordu ), desenlerini adından ve ( doğru ölçeklenmiş )
    desen ölçeğinden yeniden kurar."""
    #  Çizim eklentisi ( matplotlib'siz SVG ) yalnız önizlemede gerekir ve
    #  ağırdır:  program açılırken yüklenmesin diye burada import edilir.
    from ezdxf.addons.drawing import Frontend, RenderContext, config, layout, svg
    from ezdxf.entities import factory

    akis = io.StringIO()
    d.write(akis)
    akis.seek(0)
    k = ezdxf.read(akis)
    msp, bloklar = k.modelspace(), set()
    for ins in list(msp.query("INSERT")):
        for e in ins.virtual_entities():
            if e.dxftype() == "HATCH" and e.pattern and e.dxf.pattern_name in ezdxf.pattern.ISO_PATTERN:
                e.set_pattern_fill(
                    e.dxf.pattern_name,
                    color=e.dxf.color,
                    angle=e.dxf.pattern_angle,
                    scale=e.dxf.pattern_scale,
                )
                factory.bind(e, k)
                msp.add_entity(e)
                bloklar.add(ins.dxf.name)
    for ad in bloklar:
        blok = k.blocks[ad]
        for e in list(blok.query("HATCH")):
            if e.pattern and e.dxf.pattern_name in ezdxf.pattern.ISO_PATTERN:
                blok.delete_entity(e)
    _maskeleri_ac(k)
    #  Beyaz zeminde camgöbeği ölçü okunmaz:  önizlemede mavi ( CDX.KATMAN )
    if "OLCU" in k.layers:
        k.layers.get("OLCU").dxf.color = 5
    d = k
    arka = svg.SVGBackend()
    ayar = config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE, color_policy=config.ColorPolicy.COLOR
    )
    Frontend(RenderContext(d), arka, config=ayar).draw_layout(d.modelspace())
    return arka.get_string(layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(5)))
