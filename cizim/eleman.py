"""ÇİZİM ELEMANLARI — programın bütün çizimlerinin yapı taşları.

Eleman saf veridir ( sözlük ):  { tip, katman, … }.  SVG ( cizim/svg.py ) ve
DXF ( cizim/dxf.py ) yazıcıları aynı listeyi okur — iki ayrı çizici yazılmaz.
Tipler:  dikdortgen ( x, y, g, d ) · cizgi ( x1, y1, x2, y2 ) · daire ( x, y,
r ) · ok · yazi ( x, y, metin, yukseklik, hiza, aci ) · olcu ( yon, a, b, kot,
metin, yazi? ).  Çizimler geometrisini cizim modüllerinde kurar, elemanını
buradan alır.  Eskiden bunlar geometri.py'nin "özel" ( _dik, _yazi … )
fonksiyonlarıydı ve 300'e yakın yerden dışarıdan çağrılıyordu.
"""

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


#  Ölçü yazısının yüksekliği ( mm, 1/20'de 2,6 mm ) ve yazı eni tahmini:
#  harf başına yüksekliğin 0,6'sı  ( Arial / DejaVu ortalaması ).
#  YAZI BOYLARI ( kullanıcı 5 Eki:  "AutoCAD'de yazılar belli olmuyor" ):
#  LiftDesigner'ın paftalarında ölçü yazısı ve genel yazılar kâğıtta 2,5 mm
#  ( büyük harf ), başlıklar 5 mm.  Bizim ölçü yazımız 1,86 mm'ydi ( 52 em ·
#  0,716 / 20 ), etiketler 1,1 – 1,6 mm.  Bütün yazılar aynı oranda büyür:
#  ölçü yazısı 70 em → 70 · 0,716 / 20 = 2,5 mm;  etiketlerin elle verilen
#  boyları ( yazi ) bu çarpanla çarpılır — boylar arasındaki sıra korunur.
#  Genişlik hesaplayan yerler GERÇEK boyu kullanır ( yb ).
YAZI_CARPANI = 70.0 / 52.0
OLCU_YAZI = 70.0
#  Çakışan ölçü yazısının bir kat dışarısı:  yazı boyu + 10 ( eskiden 60 —
#  52'lik yazıya göreydi;  70'lik yazı alttakine biniyordu )
KAT_ARALIGI = OLCU_YAZI + 10.0


def buyuk(metin):
    """Türkçe büyük harf:  str.upper() "i"yi "I" yapar ( "Kabin altı" →
    "KABIN ALTI", "Dik duruş" → "DIK DURUŞ" — çizimlerde böyle yazıyordu )."""
    return metin.replace("i", "İ").replace("ı", "I").upper()


def yb(h):
    """Etiketin elle verilen ( eski ) boyundan çizilen boyu."""
    return h * YAZI_CARPANI


def yazi_eni(metin, h=OLCU_YAZI):
    return len(metin) * h * 0.6


def ad(el, ad):
    """Elemana kimlik verir;  ikinci bir çizim ( kabin üstü ) planın
    elemanlarından kendi ihtiyacı olanları bu adla seçer."""
    el["ad"] = ad
    return el


def dikdortgen(katman, x, y, g, d, tip="dikdortgen", ad=""):
    el = {"tip": tip, "katman": katman, "x": float(x), "y": float(y), "g": float(g), "d": float(d)}
    if ad:
        el["ad"] = ad
    return el


def cizgi(katman, x1, y1, x2, y2, tip="cizgi"):
    return {"tip": tip, "katman": katman, "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def daire(katman, x, y, r):
    return {"tip": "daire", "katman": katman, "x": float(x), "y": float(y), "r": float(r)}


def ok(katman, x1, y1, x2, y2):
    """Yön oku  ( kapı açılış yönü gibi )."""
    return {"tip": "ok", "katman": katman, "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def yazi(x, y, metin, yukseklik=55, hiza="orta", katman="YAZI", aci=0):
    """Etiket.  yukseklik:  eski ( 1,86 mm'lik ölçü yazısına göre ) boy —
    çizilen boy yb ile büyür."""
    return {
        "tip": "yazi",
        "katman": katman,
        "x": float(x),
        "y": float(y),
        "metin": metin,
        "yukseklik": yb(yukseklik),
        "hiza": hiza,
        "aci": float(aci),
    }


def olcu(yon, a, b, kot, metin=None, yazi=None, kural=None):
    """Ölçü.  `yazi` verilmezse yazının yeri geometri._yazilari_yerlestir'de bulunur;
    verilirse { x, y ( yazının MERKEZİ ), aci, h } olduğu gibi kullanılır.
    `kural`:  ölçü bir girdiden değil standarttan ya da programın yerleşiminden
    geliyorsa onu söyleyen metin — ekranda ölçüye tıklanınca gösterilir
    ( olcu_kaynagi;  girdiye bağlı ölçülerin kaynağı ölçülerek bulunur )."""
    uzunluk = abs(b[0] - a[0]) if yon == "yatay" else abs(b[1] - a[1])
    el = {
        "tip": "olcu",
        "katman": "OLCU",
        "yon": yon,
        "a": tuple(map(float, a)),
        "b": tuple(map(float, b)),
        "kot": float(kot),
        "metin": metin if metin is not None else f"{uzunluk:g}",
        "uzunluk": uzunluk,
    }
    if yazi:
        el["yazi"] = {
            "x": float(yazi["x"]),
            "y": float(yazi["y"]),
            "aci": float(yazi.get("aci", 0)),
            "h": float(yazi.get("h", OLCU_YAZI)),
        }
    if kural:
        el["kural"] = kural
    return el
