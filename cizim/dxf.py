# -*- coding: utf-8 -*-
"""
ÇİZİM  →  DXF   ( CAD )

SVG ile AYNI eleman listesini okur.  Birim milimetredir;  AutoCAD dosyayı
1:1 açar, ölçek yalnız paftaya yerleştirirken kullanılır.

KATMAN DÜZENİ:  her eleman türü kendi katmanına girer ki CAD'de katman
katman kapatılabilsin.  Renkler ACI numarasıdır.
"""
import io

import ezdxf
from ezdxf.enums import TextEntityAlignment

#  Katman → ( ACI rengi , çizgi kalınlığı 1/100 mm )
KATMAN = {
    "KUYU-DUVAR": (7, 50), "TARAMA": (8, 13), "BINA": (33, 13),
    "KUYU-IC": (7, 25), "KABIN": (7, 30), "KABIN-IC": (6, 20),
    "SASE": (6, 30), "KAPI": (30, 30), "AGIRLIK": (30, 30),
    "RAY": (3, 25), "KONSOL": (3, 18), "PATEN": (200, 20),
    "KASNAK": (90, 20), "PANO": (150, 20),
    "CIVATA": (3, 13), "CERCEVE": (7, 40),
    "OLCU": (5, 13), "EKSEN": (1, 13), "YAZI": (7, 0),
    "KORKULUK": (6, 50), "SIGINMA": (3, 25),
    "TAMPON": (200, 25), "PERDE": (6, 50), "MERDIVEN": (32, 25), "GIZLI": (8, 13), "YUK": (1, 0),
    "MAKINE": (5, 30), "BAGLANTI": (8, 25), "DELIK": (5, 30),
    "HALAT": (6, 18), "KESIT": (7, 50), "SEVIYE": (2, 13),
}
YAZI_TIPI = "ASANSOR"


def _katmanlari_kur(d):
    for ad, (renk, kalinlik) in KATMAN.items():
        if ad not in d.layers:
            d.layers.add(ad, color=renk, lineweight=kalinlik)
    d.layers.get("EKSEN").dxf.linetype = "CENTER"
    d.layers.get("SIGINMA").dxf.linetype = "DASHED"
    d.layers.get("GIZLI").dxf.linetype = "DASHED"
    d.layers.get("DELIK").dxf.linetype = "DASHED"


def _dikdortgen(msp, el, lt=None):
    x, y, g, h = el["x"], el["y"], el["g"], el["d"]
    msp.add_lwpolyline([(x, y), (x + g, y), (x + g, y + h), (x, y + h)],
                       close=True, dxfattribs={"layer": el["katman"], **(lt or {})})


def _olcu(msp, el, k=1.0):
    """Gerçek DIMENSION varlığı — CAD'de ölçü olarak tanınır, metin değil."""
    a, b, kot = el["a"], el["b"], el["kot"]
    if el["yon"] == "yatay":
        p1, p2 = (a[0], a[1]), (b[0], a[1])
        taban = (a[0], kot)
        aci = 0
    else:
        p1, p2 = (a[0], a[1]), (a[0], b[1])
        taban = (kot, a[1])
        aci = 90
    yz = el["yazi"]
    #  Yazı geometrinin bulduğu yerde durur  ( SVG ile aynı merkez ).
    olcu = msp.add_linear_dim(base=taban, p1=p1, p2=p2, angle=aci,
                              location=(yz["x"], yz["y"]), text_rotation=yz["aci"],
                              text=el["metin"],
                              dxfattribs={"layer": "OLCU"},
                              #  dimse1 / dimse2:  uzatma çizgileri çizilmez —
                              #  SVG ile aynı görünüm ( kullanıcı kararı ).
                              override={"dimtxt": yz["h"], "dimasz": 35 * k, "dimexe": 30 * k,
                                        "dimexo": 25 * k, "dimgap": 15 * k, "dimclrt": 5,
                                        "dimse1": 1, "dimse2": 1})
    olcu.render()


#  Çizgi tipi ölçeği:  CENTER deseni 5,08, DASHED 1,524 birim;  çizim gerçek
#  ölçüde ( mm ) olduğu için desen paftada 1/ölçek küçülür ve kesik çizgi DÜZ
#  görünürdü.  Her varlığa ölçek × 2,5 verilir:  paftada CENTER ~12,7 mm,
#  DASHED ~3,8 mm — tek başına açılan DXF'te de, paftadaki blokta da.
CIZGI_TIPI_OLCEGI = 2.5


def hazirla(d):
    """Belgeye çizimin katmanlarını ve yazı biçimini ekler ( şablon da olabilir )."""
    _katmanlari_kur(d)
    if YAZI_TIPI not in d.styles:
        d.styles.add(YAZI_TIPI, font="arial.ttf")


def ciz(hedef, elemanlar, olcek=20):
    """Elemanları `hedef` yerleşimine ( model alanı ya da blok ) yazar."""
    k = olcek / 20.0                   # ok, tarama ve boşluklar 1/20'ye göre
    lt = {"ltscale": CIZGI_TIPI_OLCEGI * olcek}
    for el in elemanlar:
        tur, kat = el["tip"], el["katman"]
        if tur in ("dikdortgen", "tarama", "tarama_tugla"):
            _dikdortgen(hedef, el, lt)
            if tur in ("tarama", "tarama_tugla"):
                #  Duvar kesiti taraması:  CAD'in kendi HATCH varlığı
                tarama = hedef.add_hatch(color=KATMAN[kat][0], dxfattribs={"layer": kat})
                tarama.set_pattern_fill("ANSI31" if tur == "tarama" else "ANSI32", scale=20 * k)
                tarama.paths.add_polyline_path(
                    [(el["x"], el["y"]), (el["x"] + el["g"], el["y"]),
                     (el["x"] + el["g"], el["y"] + el["d"]), (el["x"], el["y"] + el["d"])],
                    is_closed=True)
        elif tur in ("cizgi", "eksen"):
            hedef.add_line((el["x1"], el["y1"]), (el["x2"], el["y2"]),
                           dxfattribs={"layer": kat, **lt,
                                       "linetype": "CENTER" if tur == "eksen" else "BYLAYER"})
        elif tur == "daire":
            hedef.add_circle((el["x"], el["y"]), el["r"], dxfattribs={"layer": kat, **lt})
        elif tur == "ok":
            hedef.add_line((el["x1"], el["y1"]), (el["x2"], el["y2"]),
                           dxfattribs={"layer": kat})
            dx, dy = el["x2"] - el["x1"], el["y2"] - el["y1"]
            boy = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            ux, uy, u = dx / boy, dy / boy, 55 * k
            hedef.add_solid([(el["x2"], el["y2"]),
                             (el["x2"] - ux * u - uy * u * 0.4, el["y2"] - uy * u + ux * u * 0.4),
                             (el["x2"] - ux * u + uy * u * 0.4, el["y2"] - uy * u - ux * u * 0.4)],
                            dxfattribs={"layer": kat})
        elif tur == "olcu":
            _olcu(hedef, el, k)
        elif tur == "yazi":
            hedef.add_text(el["metin"], height=el["yukseklik"],
                           dxfattribs={"layer": kat, "style": YAZI_TIPI,
                                       "rotation": el.get("aci", 0)}
                           ).set_placement((el["x"], el["y"]), align={
                               "sol": TextEntityAlignment.MIDDLE_LEFT,
                               "sag": TextEntityAlignment.MIDDLE_RIGHT,
                           }.get(el.get("hiza"), TextEntityAlignment.MIDDLE_CENTER))


def belge(elemanlar, baslik="", olcek=20):
    """Eleman listesinden ezdxf belgesi kurar."""
    d = ezdxf.new("R2018", setup=True)
    d.header["$INSUNITS"] = 4                    # milimetre
    hazirla(d)
    msp = d.modelspace()
    ciz(msp, elemanlar, olcek)
    if baslik:
        x1 = min(el.get("x", el.get("x1", 0)) for el in elemanlar if el["tip"] != "olcu")
        y1 = min(el.get("y", el.get("y1", 0)) for el in elemanlar if el["tip"] != "olcu")
        msp.add_text(f"{baslik}   1/{olcek:g}", height=90,
                     dxfattribs={"layer": "YAZI", "style": YAZI_TIPI}
                     ).set_placement((x1, y1 - 400), align=TextEntityAlignment.LEFT)
    return d


def yaz(elemanlar, baslik="", olcek=20) -> bytes:
    """DXF baytları  ( AutoCAD çift tıkla açar )."""
    d = belge(elemanlar, baslik, olcek)
    akis = io.StringIO()
    d.write(akis)
    return akis.getvalue().encode("utf-8")
