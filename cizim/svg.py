# -*- coding: utf-8 -*-
"""
ÇİZİM  →  SVG   ( ekranda görmek ve gözle denetlemek için )

DXF ile AYNI eleman listesini okur.  Ölçü birimi mm'dir;  SVG'nin y ekseni
aşağı baktığı için çizim bir kez ters çevrilir, metinler kendi içinde geri
çevrilir ki okunaklı kalsın.
"""
import html
import math

#  Katman → ( renk, çizgi kalınlığı mm )
KALEM = {
    "KUYU-DUVAR": ("#1a1a1a", 12), "TARAMA": ("#9a9a9a", 3),
    "KUYU-IC": ("#1a1a1a", 6), "KABIN": ("#1a1a1a", 7),
    "KABIN-IC": ("#c026a0", 5), "SASE": ("#c026a0", 7),
    "KAPI": ("#b4531b", 7), "AGIRLIK": ("#e2680c", 7),
    "RAY": ("#1f7a1f", 6), "KONSOL": ("#2f6f2f", 4),
    "PATEN": ("#7a3ea8", 5), "KASNAK": ("#0f8f4f", 5),
    "PANO": ("#2f6fb5", 5), "BINA": ("#a06a4a", 3),
    "CIVATA": ("#2f6f2f", 3), "CERCEVE": ("#1a1a1a", 8),
    "OLCU": ("#0a6ebd", 3), "EKSEN": ("#c01c1c", 3), "YAZI": ("#1a1a1a", 0),
    "KORKULUK": ("#d11a6a", 12), "SIGINMA": ("#1d8a3a", 6),
    "TAMPON": ("#8a2be2", 6), "PERDE": ("#d11a6a", 14), "MERDIVEN": ("#6b4f2a", 6),
    "GIZLI": ("#7a7a7a", 4), "YUK": ("#c01c1c", 5),
    "MAKINE": ("#1f4fbf", 7), "BAGLANTI": ("#444444", 5), "DELIK": ("#1f4fbf", 6),
    "HALAT": ("#c2185b", 4), "KESIT": ("#1a1a1a", 14), "SEVIYE": ("#c79a00", 4),
}
#  Kesik çizilen katmanlar  ( sığınma alanı gerçek bir parça değil, alandır )
KESIK = {"SIGINMA": "80 40", "GIZLI": "40 30", "DELIK": "50 25"}
DOLGU = {"KABIN-IC": "none", "AGIRLIK": "#fde9d7", "RAY": "#dff0df",
         "KAPI": "#ffffff", "KABIN": "#ffffff", "SASE": "#fbe6f6",
         "KONSOL": "#eef7ee", "PATEN": "#efe4f8", "KASNAK": "#d8f0e2",
         "PANO": "#dbe8f7", "SIGINMA": "#e6f6ea", "TAMPON": "#efe4f8",
         "MERDIVEN": "#f3ead9", "MAKINE": "#dbe4fa", "BAGLANTI": "#e6e6e6",
         "YUK": "#ffffff"}


def _dikdortgen(el, renk, kalinlik, k=1.0):
    dolgu = DOLGU.get(el["katman"], "none")
    kesik = _kesik_ozniteligi(el, k)
    return (f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
            f'height="{el["d"]:.1f}" fill="{dolgu}" stroke="{renk}" '
            f'stroke-width="{kalinlik}"{kesik}/>')


def _olcu(el, renk, kalinlik, k=1.0, tutamak=False):
    """Ölçü çizgisi + iki uçtaki kısa çizgi + yazı.

    tutamak:  ekranda tıklanacak ölçü için çizginin ve yazının üstüne
    görünmez, geniş bir tutma yüzeyi ( ince çizgiye ve harflere tam
    denk getirmek gerekmesin ).

    Yazının yeri geometride bulunur ( el["yazi"] = yazının MERKEZİ );  DXF de
    aynı yeri kullanır.  UZATMA ÇİZGİSİ YOK:  ölçülen noktadan ölçü çizgisine
    uzanan kesik çizgiler bütün planı boydan boya kesiyor, çizimi okunmaz
    yapıyordu ( kullanıcı kararı ).
    """
    if el["yon"] == "yatay":
        x1, x2, y = el["a"][0], el["b"][0], el["kot"]
        cizgi = f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"'
        uc = "".join(f'<line x1="{x:.1f}" y1="{y - 45 * k:.1f}" x2="{x:.1f}" y2="{y + 45 * k:.1f}" '
                     f'stroke="{renk}" stroke-width="{kalinlik}"/>' for x in (x1, x2))
    else:
        y1, y2, x = el["a"][1], el["b"][1], el["kot"]
        cizgi = f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"'
        uc = "".join(f'<line x1="{x - 45 * k:.1f}" y1="{y:.1f}" x2="{x + 45 * k:.1f}" y2="{y:.1f}" '
                     f'stroke="{renk}" stroke-width="{kalinlik}"/>' for y in (y1, y2))
    yz = el["yazi"]
    #  Merkezden taban çizgisine:  yazının "yukarı" yönünün tersine 0,35·h
    a = math.radians(yz["aci"])
    bx = yz["x"] + 0.35 * yz["h"] * math.sin(a)
    by = yz["y"] - 0.35 * yz["h"] * math.cos(a)
    tut = ""
    if tutamak:
        h, w = yz["h"], len(el["metin"]) * yz["h"] * 0.6
        tut = (cizgi + f' class="tut" stroke="transparent" stroke-width="{60 * k:g}"/>'
               f'<g transform="translate({bx:.1f},{by:.1f}) scale(1,-1) rotate({-yz["aci"]})">'
               f'<rect class="tut" x="{-w / 2 - 0.3 * h:.1f}" y="{-1.05 * h:.1f}" '
               f'width="{w + 0.6 * h:.1f}" height="{1.4 * h:.1f}" fill="transparent"/></g>')
    return (cizgi + f' stroke="{renk}" stroke-width="{kalinlik}"/>' + uc
            + _metin(bx, by, el["metin"], yz["h"], renk, -yz["aci"]) + tut)


def _metin(x, y, metin, yukseklik, renk, aci=0, hiza="orta"):  # noqa: D401
    #  Çizim ters çevrildiği için yazı kendi ekseninde geri çevrilir.
    tutucu = {"orta": "middle", "sol": "start", "sag": "end"}.get(hiza, "middle")
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale(1,-1) rotate({aci})">'
            f'<text x="0" y="0" font-family="DejaVu Sans, Arial" font-size="{yukseklik:g}" '
            f'fill="{renk}" text-anchor="{tutucu}">{html.escape(metin)}</text></g>')


def _kesik(desen, k):
    return desen if k == 1 else " ".join(f"{float(v) * k:g}" for v in desen.split())


def _kesik_ozniteligi(el, k):
    desen = ("120 40 20 40" if el["tip"] == "eksen" or el["katman"] == "EKSEN"
             else KESIK.get(el["katman"]))
    return f' stroke-dasharray="{_kesik(desen, k)}"' if desen else ""


def _olcekle(k):
    return "" if k == 1 else f" scale({k:g})"


def _desen(k):
    return "" if k == 1 else f' patternTransform="scale({k:g})"'


def yaz(elemanlar, sinir, baslik="", olcek=20, onek="", etkilesimli=False):
    """Eleman listesini SVG metnine çevirir.

    onek:  desen kimliklerinin öneki — aynı sayfada birden çok SVG satır içi
    durunca kimlikler çakışmasın ( ölçekleri farklı, desenleri de farklı ).
    etkilesimli:  her ölçü  <g class="olcu" data-olcu="sıra">  içinde ve
    tutamaklı ( ekranda tıklanır;  sıra eleman listesindeki ölçülerin sırası —
    olcu_kaynagi.olculer ile aynı )."""
    x1, y1, x2, y2 = sinir
    g, d = x2 - x1, y2 - y1
    #  Kalem kalınlıkları, tarama ve oklar 1/20'ye göre;  başka ölçekte
    #  paftadaki boyları aynı kalsın diye k ile büyür.
    k = olcek / 20.0
    parcalar, n_olcu = [], 0
    for el in elemanlar:
        renk, kal = KALEM.get(el["katman"], ("#000", 4))
        kal = f"{kal * k:g}"
        if el["tip"] == "tarama_tugla":
            parcalar.append(f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
                            f'height="{el["d"]:.1f}" fill="url(#{onek}tugla)" stroke="{renk}" '
                            f'stroke-width="{kal}"/>')
        elif el["tip"] == "tarama":
            parcalar.append(f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
                            f'height="{el["d"]:.1f}" fill="url(#{onek}tarama)" stroke="none"/>')
        elif el["tip"] == "dikdortgen":
            parcalar.append(_dikdortgen(el, renk, kal, k))
        elif el["tip"] in ("cizgi", "eksen"):
            kesik = _kesik_ozniteligi(el, k)
            parcalar.append(f'<line x1="{el["x1"]:.1f}" y1="{el["y1"]:.1f}" x2="{el["x2"]:.1f}" '
                            f'y2="{el["y2"]:.1f}" stroke="{renk}" stroke-width="{kal}"{kesik}/>')
        elif el["tip"] == "daire":
            kesik = _kesik_ozniteligi(el, k)
            parcalar.append(f'<circle cx="{el["x"]:.1f}" cy="{el["y"]:.1f}" r="{el["r"]:.1f}" '
                            f'fill="none" stroke="{renk}" stroke-width="{kal}"{kesik}/>')
        elif el["tip"] == "ok":
            #  Uç üçgeni yönü gösterir.
            dx, dy = el["x2"] - el["x1"], el["y2"] - el["y1"]
            boy = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            ux, uy = dx / boy, dy / boy
            ux2, uy2 = -uy, ux
            u = 55 * k
            parcalar.append(
                f'<line x1="{el["x1"]:.1f}" y1="{el["y1"]:.1f}" x2="{el["x2"]:.1f}" '
                f'y2="{el["y2"]:.1f}" stroke="{renk}" stroke-width="{kal}"/>'
                f'<polygon points="{el["x2"]:.1f},{el["y2"]:.1f} '
                f'{el["x2"] - ux * u + ux2 * u * 0.4:.1f},{el["y2"] - uy * u + uy2 * u * 0.4:.1f} '
                f'{el["x2"] - ux * u - ux2 * u * 0.4:.1f},{el["y2"] - uy * u - uy2 * u * 0.4:.1f}" '
                f'fill="{renk}"/>')
        elif el["tip"] == "olcu":
            if etkilesimli:
                parcalar.append(f'<g class="olcu" data-olcu="{n_olcu}" tabindex="0" role="button" '
                                f'aria-label="Ölçü {html.escape(el["metin"])}">'
                                + _olcu(el, renk, kal, k, tutamak=True) + '</g>')
            else:
                parcalar.append(_olcu(el, renk, kal, k))
            n_olcu += 1
        elif el["tip"] == "yazi":
            parcalar.append(_metin(el["x"], el["y"], el["metin"], el["yukseklik"], renk,
                                   -el.get("aci", 0), el.get("hiza", "orta")))
    bas = (_metin(x1 + g / 2.0, y1 - 180, f"{baslik}   1/{olcek:g}", 90, "#1a1a1a")
           if baslik else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x1:.0f} {-y2 - 300:.0f} '
            f'{g:.0f} {d + 600:.0f}" width="{g / olcek:.0f}mm" height="{(d + 600) / olcek:.0f}mm">'
            f'<defs><pattern id="{onek}tarama" width="120" height="120" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45){_olcekle(k)}"><line x1="0" y1="0" x2="0" y2="120" '
            'stroke="#9a9a9a" stroke-width="6"/></pattern>'
            f'<pattern id="{onek}tugla" width="240" height="120" patternUnits="userSpaceOnUse"'
            f'{_desen(k)}>'
            '<rect width="240" height="120" fill="#fdf3ee"/>'
            '<path d="M0 0 H240 M0 60 H240 M120 0 V60 M0 60 V120 M240 60 V120" '
            'stroke="#c08a6a" stroke-width="5" fill="none"/></pattern></defs>'
            '<rect x="-100000" y="-100000" width="200000" height="200000" fill="#ffffff"/>'
            f'<g transform="scale(1,-1)">{"".join(parcalar)}{bas}</g></svg>')
