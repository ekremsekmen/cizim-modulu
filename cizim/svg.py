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
}
#  Kesik çizilen katmanlar  ( sığınma alanı gerçek bir parça değil, alandır )
KESIK = {"SIGINMA": "80 40"}
DOLGU = {"KABIN-IC": "none", "AGIRLIK": "#fde9d7", "RAY": "#dff0df",
         "KAPI": "#ffffff", "KABIN": "#ffffff", "SASE": "#fbe6f6",
         "KONSOL": "#eef7ee", "PATEN": "#efe4f8", "KASNAK": "#d8f0e2",
         "PANO": "#dbe8f7", "SIGINMA": "#e6f6ea"}


def _dikdortgen(el, renk, kalinlik):
    dolgu = DOLGU.get(el["katman"], "none")
    kesik = (f' stroke-dasharray="{KESIK[el["katman"]]}"' if el["katman"] in KESIK else "")
    return (f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
            f'height="{el["d"]:.1f}" fill="{dolgu}" stroke="{renk}" '
            f'stroke-width="{kalinlik}"{kesik}/>')


def _olcu(el, renk, kalinlik):
    """Ölçü çizgisi + iki uçtaki kısa çizgi + yazı.

    Yazının yeri geometride bulunur ( el["yazi"] = yazının MERKEZİ );  DXF de
    aynı yeri kullanır.  UZATMA ÇİZGİSİ YOK:  ölçülen noktadan ölçü çizgisine
    uzanan kesik çizgiler bütün planı boydan boya kesiyor, çizimi okunmaz
    yapıyordu ( kullanıcı kararı ).
    """
    if el["yon"] == "yatay":
        x1, x2, y = el["a"][0], el["b"][0], el["kot"]
        cizgi = f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"'
        uc = "".join(f'<line x1="{x:.1f}" y1="{y - 45:.1f}" x2="{x:.1f}" y2="{y + 45:.1f}" '
                     f'stroke="{renk}" stroke-width="{kalinlik}"/>' for x in (x1, x2))
    else:
        y1, y2, x = el["a"][1], el["b"][1], el["kot"]
        cizgi = f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"'
        uc = "".join(f'<line x1="{x - 45:.1f}" y1="{y:.1f}" x2="{x + 45:.1f}" y2="{y:.1f}" '
                     f'stroke="{renk}" stroke-width="{kalinlik}"/>' for y in (y1, y2))
    yz = el["yazi"]
    #  Merkezden taban çizgisine:  yazının "yukarı" yönünün tersine 0,35·h
    a = math.radians(yz["aci"])
    bx = yz["x"] + 0.35 * yz["h"] * math.sin(a)
    by = yz["y"] - 0.35 * yz["h"] * math.cos(a)
    return (cizgi + f' stroke="{renk}" stroke-width="{kalinlik}"/>' + uc
            + _metin(bx, by, el["metin"], yz["h"], renk, -yz["aci"]))


def _metin(x, y, metin, yukseklik, renk, aci=0, hiza="orta"):  # noqa: D401
    #  Çizim ters çevrildiği için yazı kendi ekseninde geri çevrilir.
    tutucu = {"orta": "middle", "sol": "start", "sag": "end"}.get(hiza, "middle")
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale(1,-1) rotate({aci})">'
            f'<text x="0" y="0" font-family="DejaVu Sans, Arial" font-size="{yukseklik}" '
            f'fill="{renk}" text-anchor="{tutucu}">{html.escape(metin)}</text></g>')


def yaz(elemanlar, sinir, baslik="", olcek=20):
    """Eleman listesini SVG metnine çevirir."""
    x1, y1, x2, y2 = sinir
    g, d = x2 - x1, y2 - y1
    parcalar = []
    for el in elemanlar:
        renk, kal = KALEM.get(el["katman"], ("#000", 4))
        if el["tip"] == "tarama_tugla":
            parcalar.append(f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
                            f'height="{el["d"]:.1f}" fill="url(#tugla)" stroke="{renk}" '
                            f'stroke-width="{kal}"/>')
        elif el["tip"] == "tarama":
            parcalar.append(f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
                            f'height="{el["d"]:.1f}" fill="url(#tarama)" stroke="none"/>')
        elif el["tip"] == "dikdortgen":
            parcalar.append(_dikdortgen(el, renk, kal))
        elif el["tip"] in ("cizgi", "eksen"):
            kesik = ' stroke-dasharray="120 40 20 40"' if el["tip"] == "eksen" else ""
            parcalar.append(f'<line x1="{el["x1"]:.1f}" y1="{el["y1"]:.1f}" x2="{el["x2"]:.1f}" '
                            f'y2="{el["y2"]:.1f}" stroke="{renk}" stroke-width="{kal}"{kesik}/>')
        elif el["tip"] == "daire":
            parcalar.append(f'<circle cx="{el["x"]:.1f}" cy="{el["y"]:.1f}" r="{el["r"]:.1f}" '
                            f'fill="none" stroke="{renk}" stroke-width="{kal}"/>')
        elif el["tip"] == "ok":
            #  Uç üçgeni yönü gösterir.
            dx, dy = el["x2"] - el["x1"], el["y2"] - el["y1"]
            boy = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            ux, uy = dx / boy, dy / boy
            ux2, uy2 = -uy, ux
            u = 55
            parcalar.append(
                f'<line x1="{el["x1"]:.1f}" y1="{el["y1"]:.1f}" x2="{el["x2"]:.1f}" '
                f'y2="{el["y2"]:.1f}" stroke="{renk}" stroke-width="{kal}"/>'
                f'<polygon points="{el["x2"]:.1f},{el["y2"]:.1f} '
                f'{el["x2"] - ux * u + ux2 * u * 0.4:.1f},{el["y2"] - uy * u + uy2 * u * 0.4:.1f} '
                f'{el["x2"] - ux * u - ux2 * u * 0.4:.1f},{el["y2"] - uy * u - uy2 * u * 0.4:.1f}" '
                f'fill="{renk}"/>')
        elif el["tip"] == "olcu":
            parcalar.append(_olcu(el, renk, kal))
        elif el["tip"] == "yazi":
            parcalar.append(_metin(el["x"], el["y"], el["metin"], el["yukseklik"], renk,
                                   -el.get("aci", 0), el.get("hiza", "orta")))
    bas = (_metin(x1 + g / 2.0, y1 - 180, f"{baslik}   1/{olcek:g}", 90, "#1a1a1a")
           if baslik else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x1:.0f} {-y2 - 300:.0f} '
            f'{g:.0f} {d + 600:.0f}" width="{g / olcek:.0f}mm" height="{(d + 600) / olcek:.0f}mm">'
            '<defs><pattern id="tarama" width="120" height="120" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="120" '
            'stroke="#9a9a9a" stroke-width="6"/></pattern>'
            '<pattern id="tugla" width="240" height="120" patternUnits="userSpaceOnUse">'
            '<rect width="240" height="120" fill="#fdf3ee"/>'
            '<path d="M0 0 H240 M0 60 H240 M120 0 V60 M0 60 V120 M240 60 V120" '
            'stroke="#c08a6a" stroke-width="5" fill="none"/></pattern></defs>'
            '<rect x="-100000" y="-100000" width="200000" height="200000" fill="#ffffff"/>'
            f'<g transform="scale(1,-1)">{"".join(parcalar)}{bas}</g></svg>')
