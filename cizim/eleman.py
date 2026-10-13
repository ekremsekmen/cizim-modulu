"""ÇİZİM ELEMANLARI — programın bütün çizimlerinin yapı taşları.

Eleman saf veridir ( sözlük ):  { tip, katman, … }.  SVG ( cizim/svg.py ) ve
DXF ( cizim/dxf.py ) yazıcıları aynı listeyi okur — iki ayrı çizici yazılmaz.
Tipler:  dikdortgen ( x, y, g, d ) · cizgi ( x1, y1, x2, y2 ) · daire ( x, y,
r ) · ok · yazi ( x, y, metin, yukseklik, hiza, aci ) · olcu ( yon, a, b, kot,
metin, yazi? ).  Çizimler geometrisini cizim modüllerinde kurar, elemanını
buradan alır.  Eskiden bunlar geometri.py'nin "özel" ( _dik, _yazi … )
fonksiyonlarıydı ve 300'e yakın yerden dışarıdan çağrılıyordu.
"""

from cizim import harf_eni
from cizim import izli
from cizim import uslup

KATMANLAR = (
    "KUYU-DUVAR",
    "TARAMA",
    "BINA",
    "KUYU-IC",
    "KABIN",
    "KABIN-IC",
    "SASE",
    "KAPI",
    "AGIRLIK",
    "RAY",
    "KONSOL",
    "CIVATA",
    "PATEN",
    "KASNAK",
    "PANO",
    "OLCU",
    "EKSEN",
    "YAZI",
    "CERCEVE",
    "KORKULUK",
    "SIGINMA",
    "TAMPON",
    "PERDE",
    "MERDIVEN",
    "GIZLI",
    "YUK",
    "MAKINE",
    "BAGLANTI",
    "DELIK",
    "HALAT",
    "KESIT",
    "SEVIYE",
    "ACILIS",
)


#  Ölçü yazısının yüksekliği ( em, 1/20'de — kâğıtta 2,5 mm büyük harf;
#  uslup.NORMAL ).  Yazı boyları ISO 3098 dizisinde ( uslup:  2,5 · 3,5 · 5 mm ).
OLCU_YAZI = uslup.NORMAL
#  Çakışan ölçü yazısının bir kat dışarısı:  yazı boyu + 10 ( eskiden 60 —
#  52'lik yazıya göreydi;  70'lik yazı alttakine biniyordu )
KAT_ARALIGI = OLCU_YAZI + 10.0
#  Tabloda olmayan harfin eni ( em ) — eski tahmin
_BILINMEYEN_HARF = 0.6


def buyuk(metin):
    """Türkçe büyük harf:  str.upper() "i"yi "I" yapar ( "Kabin altı" →
    "KABIN ALTI", "Dik duruş" → "DIK DURUŞ" — çizimlerde böyle yazıyordu )."""
    return metin.replace("i", "İ").replace("ı", "I").upper()


def yazi_eni(metin, h=OLCU_YAZI):
    """Yazının eni:  harflerin GERÇEK enleri ( Arial — harf_eni.EN ) × h.
    Eskiden harf × 0,6 h sayılıyordu:  gerçeğinden −%6 … +%20 ( 12 Eki )."""
    return h * sum(harf_eni.EN.get(c, _BILINMEYEN_HARF) for c in metin)


def ad(el, ad):
    """Elemana kimlik verir;  ikinci bir çizim ( kabin üstü ) planın
    elemanlarından kendi ihtiyacı olanları bu adla seçer."""
    el["ad"] = ad
    return el


def dikdortgen(katman, x, y, g, d, tip="dikdortgen", ad=""):
    el = {
        "tip": tip,
        "katman": katman,
        "x": izli.sayi(x),
        "y": izli.sayi(y),
        "g": izli.sayi(g),
        "d": izli.sayi(d),
    }
    if ad:
        el["ad"] = ad
    return el


def cizgi(katman, x1, y1, x2, y2, tip="cizgi"):
    return {
        "tip": tip,
        "katman": katman,
        "x1": izli.sayi(x1),
        "y1": izli.sayi(y1),
        "x2": izli.sayi(x2),
        "y2": izli.sayi(y2),
    }


def daire(katman, x, y, r):
    return {"tip": "daire", "katman": katman, "x": izli.sayi(x), "y": izli.sayi(y), "r": izli.sayi(r)}


def ok(katman, x1, y1, x2, y2):
    """Yön oku  ( kapı açılış yönü gibi )."""
    return {
        "tip": "ok",
        "katman": katman,
        "x1": izli.sayi(x1),
        "y1": izli.sayi(y1),
        "x2": izli.sayi(x2),
        "y2": izli.sayi(y2),
    }


def yazi(x, y, metin, yukseklik=uslup.NORMAL, hiza="orta", katman="YAZI", aci=0):
    """Etiket.  yukseklik:  em ( 1/20'de;  uslup.NORMAL · HARF · BASLIK — başka
    ölçekte çizim k ile çarpar )."""
    return {
        "tip": "yazi",
        "katman": katman,
        "x": izli.sayi(x),
        "y": izli.sayi(y),
        "metin": metin,
        "yukseklik": yukseklik,
        "hiza": hiza,
        "aci": izli.sayi(aci),
    }


def olcu(yon, a, b, kot, metin=None, yazi=None, kural=None, ad=None):
    """Ölçü.  `yazi` verilmezse yazının yeri geometri.yazilari_yerlestir'de bulunur;
    verilirse { x, y ( yazının MERKEZİ ), aci, h } olduğu gibi kullanılır.
    `kural`:  ölçü bir girdiden değil standarttan ya da programın yerleşiminden
    geliyorsa onu söyleyen metin — ekranda ölçüye tıklanınca gösterilir
    ( olcu_kaynagi;  girdiye bağlı ölçülerin kaynağı ölçülerek bulunur ).
    `ad`:  ölçünün yazıdan bağımsız KİMLİĞİ ( "olcu_" önekiyle saklanır ) —
    yazısı koda ya da yalnız sayıya inen ölçüyü ölçüye tıklama ve testler
    onunla tanır ( olcu_kaynagi._imza;  13 Eki )."""
    uzunluk = abs(b[0] - a[0]) if yon == "yatay" else abs(b[1] - a[1])
    el = {
        "tip": "olcu",
        "katman": "OLCU",
        "yon": yon,
        "a": tuple(map(izli.sayi, a)),
        "b": tuple(map(izli.sayi, b)),
        "kot": izli.sayi(kot),
        "metin": metin if metin is not None else f"{uzunluk:g}",
        "uzunluk": uzunluk,
    }
    if yazi:
        el["yazi"] = {
            "x": izli.sayi(yazi["x"]),
            "y": izli.sayi(yazi["y"]),
            "aci": izli.sayi(yazi.get("aci", 0)),
            "h": izli.sayi(yazi.get("h", OLCU_YAZI)),
        }
    if kural:
        el["kural"] = kural
    if ad:
        el["ad"] = "olcu_" + ad
    return el
