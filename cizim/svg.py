# -*- coding: utf-8 -*-
"""
ÇİZİM  →  SVG   ( ekranda görmek ve gözle denetlemek için )

DXF ile AYNI eleman listesini okur.  Ölçü birimi mm'dir;  SVG'nin y ekseni
aşağı baktığı için çizim bir kez ters çevrilir, metinler kendi içinde geri
çevrilir ki okunaklı kalsın.
"""

import html
import math

#  TEKNİK RESİM ÜSLUBU ( ISO 128 ):  siyah çizgi, kalınlık sırası anlam taşır;
#  renkli dolgu yok ( 6 Eki — kullanıcı:  çizimler "oyuncak gibi" duruyordu;
#  parçalar açık yeşil, turuncu, pembe dolguluydu ).  Kâğıtta ( mm ):
#      0,50  kesilen duvar, kesit işareti, çerçeve
#      0,35  görünen ana kenar ( kabin, kapı, ray, ağırlık, şase, makine … )
#      0,25  ikincil parça ( konsol, paten, pano, merdiven, kabin içi … )
#      0,18  ince parça ( cıvata, delik, halat ), gizli çizgi
#      0,13  ölçü, eksen, tarama, seviye, alan sınırı, etiket oku
#  Kalınlıklar 1/20'ye göre birim:  1/20'de 0,50 mm = 10.  Ölçü ve eksen ekranda
#  ayırt edilsin diye koyu mavi / koyu kırmızı;  geri kalan siyah.  DXF'teki
#  katman renkleri AutoCAD'in koyu zemini içindir, ayrıdır ( dxf.KATMAN ).
SIYAH = "#111111"
_K = {0.50: 10, 0.35: 7, 0.25: 5, 0.18: 3.6, 0.13: 2.6}
KALEM = {
    "KUYU-DUVAR": (SIYAH, _K[0.50]),
    "KESIT": (SIYAH, _K[0.50]),
    "CERCEVE": (SIYAH, _K[0.50]),
    "KUYU-IC": (SIYAH, _K[0.35]),
    "KABIN": (SIYAH, _K[0.35]),
    "KAPI": (SIYAH, _K[0.35]),
    "AGIRLIK": (SIYAH, _K[0.35]),
    "RAY": (SIYAH, _K[0.35]),
    "SASE": (SIYAH, _K[0.35]),
    "MAKINE": (SIYAH, _K[0.35]),
    "KASNAK": (SIYAH, _K[0.35]),
    "TAMPON": (SIYAH, _K[0.35]),
    "PERDE": (SIYAH, _K[0.35]),
    "KORKULUK": (SIYAH, _K[0.35]),
    "KABIN-IC": (SIYAH, _K[0.25]),
    "KONSOL": (SIYAH, _K[0.25]),
    "PATEN": (SIYAH, _K[0.25]),
    "PANO": (SIYAH, _K[0.25]),
    "BAGLANTI": (SIYAH, _K[0.25]),
    "MERDIVEN": (SIYAH, _K[0.25]),
    "BINA": (SIYAH, _K[0.25]),
    "YUK": (SIYAH, _K[0.25]),
    "CIVATA": (SIYAH, _K[0.18]),
    "DELIK": (SIYAH, _K[0.18]),
    "HALAT": (SIYAH, _K[0.18]),
    "GIZLI": (SIYAH, _K[0.18]),
    "ACILIS": (SIYAH, _K[0.18]),
    "OLCU": ("#0b4a8f", _K[0.13]),
    "EKSEN": ("#a51d1d", _K[0.13]),
    "TARAMA": (SIYAH, _K[0.13]),
    "SEVIYE": (SIYAH, _K[0.13]),
    "SIGINMA": (SIYAH, _K[0.13]),
    "YAZI": (SIYAH, _K[0.13]),
}
#  Kesik çizilen katmanlar  ( sığınma alanı gerçek bir parça değil, alandır )
KESIK = {"SIGINMA": "80 40", "GIZLI": "40 30", "DELIK": "50 25"}
#  Dolgu yalnız örtmek için ( zemin rengi ):  kesitte kabin ve kapı arkasındakini,
#  yük kutusu oku örter.  Renkli dolgu yok.
DOLGU = {"KAPI": "#ffffff", "KABIN": "#ffffff", "YUK": "#ffffff"}


def _dikdortgen(el, renk, kalinlik, k=1.0):
    dolgu = DOLGU.get(el["katman"], "none")
    kesik = _kesik_ozniteligi(el, k)
    return (
        f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
        f'height="{el["d"]:.1f}" fill="{dolgu}" stroke="{renk}" '
        f'stroke-width="{kalinlik}"{kesik}/>'
    )


def _bicim(el, renk, kalinlik, k=1.0):
    """Parçanın gerçek biçimi ( parcalar ):  zarf dikdörtgeninin yerine kapalı
    çokgenler ( "dolu" kesit koyu boyanır ) ve açık çoklu çizgiler ( sac
    profil;  "ince" ayrıntı 0,18 kalemle )."""
    out = []
    #  ÖRTÜ:  dolgulu katmanın parçası ( kapı, kabin ) dikdörtgen çizilirken
    #  zemin rengiyle dolardı ve arkasındakini örterdi ( kabin kapısının
    #  kanatları üstteki operatör kutusunu );  açık sac profilin dolgusu yok —
    #  zarfın içi ayrıca örtülür.  Yarım kalem içeriden:  zarfın kenarına denk
    #  gelen komşu çizginin ( eşiğin arka kenarı ) yarısını silmesin.
    if el["katman"] in DOLGU and el["bicim"]:
        y = float(kalinlik) / 2.0
        if el["g"] > 2 * y and el["d"] > 2 * y:
            out.append(
                f'<rect x="{el["x"] + y:.1f}" y="{el["y"] + y:.1f}" width="{el["g"] - 2 * y:.1f}" '
                f'height="{el["d"] - 2 * y:.1f}" fill="{DOLGU[el["katman"]]}" stroke="none"/>'
            )
    for p in el["bicim"]:
        nok = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["noktalar"])
        kal = f"{_K[0.18] * k:g}" if p.get("ince") else kalinlik
        if not p.get("kapali", True):
            out.append(
                f'<polyline points="{nok}" fill="none" stroke="{renk}" '
                f'stroke-width="{kal}" stroke-linejoin="miter"/>'
            )
            continue
        dolgu = renk if p.get("dolu") else DOLGU.get(el["katman"], "none")
        out.append(
            f'<polygon points="{nok}" fill="{dolgu}" stroke="{renk}" '
            f'stroke-width="{kal}" stroke-linejoin="miter"/>'
        )
    return "".join(out)


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
        uc = "".join(
            f'<line x1="{x:.1f}" y1="{y - 45 * k:.1f}" x2="{x:.1f}" y2="{y + 45 * k:.1f}" '
            f'stroke="{renk}" stroke-width="{kalinlik}"/>'
            for x in (x1, x2)
        )
    else:
        y1, y2, x = el["a"][1], el["b"][1], el["kot"]
        cizgi = f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"'
        uc = "".join(
            f'<line x1="{x - 45 * k:.1f}" y1="{y:.1f}" x2="{x + 45 * k:.1f}" y2="{y:.1f}" '
            f'stroke="{renk}" stroke-width="{kalinlik}"/>'
            for y in (y1, y2)
        )
    yz = el["yazi"]
    #  Merkezden taban çizgisine:  yazının "yukarı" yönünün tersine 0,35·h
    a = math.radians(yz["aci"])
    bx = yz["x"] + 0.35 * yz["h"] * math.sin(a)
    by = yz["y"] - 0.35 * yz["h"] * math.cos(a)
    tut = ""
    if tutamak:
        h, w = yz["h"], len(el["metin"]) * yz["h"] * 0.6
        tut = (
            cizgi + f' class="tut" stroke="transparent" stroke-width="{60 * k:g}"/>'
            f'<g transform="translate({bx:.1f},{by:.1f}) scale(1,-1) rotate({-yz["aci"]})">'
            f'<rect class="tut" x="{-w / 2 - 0.3 * h:.1f}" y="{-1.05 * h:.1f}" '
            f'width="{w + 0.6 * h:.1f}" height="{1.4 * h:.1f}" fill="transparent"/></g>'
        )
    return (
        cizgi
        + f' stroke="{renk}" stroke-width="{kalinlik}"/>'
        + uc
        + _metin(bx, by, el["metin"], yz["h"], renk, -yz["aci"], k=k)
        + tut
    )


#  YAZI MASKESİ ( DXF'teki MTEXT arka planı / dimtfill ile aynı iş ):  harflerin
#  çevresinde zemin renginde bir hale — çizgi yazının üstünden geçmez, yazının
#  olduğu yerde kesilir ( ISO 128 ).  Halenin eni yazı boyunun oranı;  ölçü
#  yazısından büyük yazılarda ( çizimin başlığı ) ölçü yazısınınki kadar — geniş
#  hale başlığın altındaki şerit çizgisini kesiyordu.
HALE = 0.6
HALE_AZAMI = 70.0 * HALE  # 1/20'de;  başka ölçekte k ile


def _metin(x, y, metin, yukseklik, renk, aci=0, hiza="orta", k=1.0):  # noqa: D401
    #  Çizim ters çevrildiği için yazı kendi ekseninde geri çevrilir.
    hale = min(HALE * yukseklik, HALE_AZAMI * k)
    tutucu = {"orta": "middle", "sol": "start", "sag": "end"}.get(hiza, "middle")
    return (
        f'<g transform="translate({x:.1f},{y:.1f}) scale(1,-1) rotate({aci})">'
        f'<text x="0" y="0" font-family="DejaVu Sans, Arial" font-size="{yukseklik:g}" '
        f'fill="{renk}" stroke="#ffffff" stroke-width="{hale:.1f}" '
        f'stroke-linejoin="round" paint-order="stroke" '
        f'text-anchor="{tutucu}">{html.escape(metin)}</text></g>'
    )


def _kesik(desen, k):
    return desen if k == 1 else " ".join(f"{float(v) * k:g}" for v in desen.split())


def _kesik_ozniteligi(el, k):
    desen = "120 40 20 40" if el["tip"] == "eksen" or el["katman"] == "EKSEN" else KESIK.get(el["katman"])
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
    #  Önce parçalar, sonra ölçüler, en son etiketler:  yazının halesi
    #  kendinden önce çizileni örter ( DXF ile aynı sıra ).
    sira = {"olcu": 1, "yazi": 2}
    for el in sorted(elemanlar, key=lambda el: sira.get(el["tip"], 0)):
        renk, kal = KALEM.get(el["katman"], ("#000", 4))
        kal = f"{kal * k:g}"
        if el["tip"] == "tarama_tugla":
            parcalar.append(
                f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
                f'height="{el["d"]:.1f}" fill="url(#{onek}tugla)" stroke="{renk}" '
                f'stroke-width="{kal}"/>'
            )
        elif el["tip"] == "tarama":
            parcalar.append(
                f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
                f'height="{el["d"]:.1f}" fill="url(#{onek}tarama)" stroke="none"/>'
            )
        elif el["tip"] == "dikdortgen":
            parcalar.append(_bicim(el, renk, kal, k) if "bicim" in el else _dikdortgen(el, renk, kal, k))
        elif el["tip"] in ("cizgi", "eksen"):
            kesik = _kesik_ozniteligi(el, k)
            parcalar.append(
                f'<line x1="{el["x1"]:.1f}" y1="{el["y1"]:.1f}" x2="{el["x2"]:.1f}" '
                f'y2="{el["y2"]:.1f}" stroke="{renk}" stroke-width="{kal}"{kesik}/>'
            )
        elif el["tip"] == "daire":
            kesik = _kesik_ozniteligi(el, k)
            parcalar.append(
                f'<circle cx="{el["x"]:.1f}" cy="{el["y"]:.1f}" r="{el["r"]:.1f}" '
                f'fill="none" stroke="{renk}" stroke-width="{kal}"{kesik}/>'
            )
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
                f"{el['x2'] - ux * u + ux2 * u * 0.4:.1f},{el['y2'] - uy * u + uy2 * u * 0.4:.1f} "
                f'{el["x2"] - ux * u - ux2 * u * 0.4:.1f},{el["y2"] - uy * u - uy2 * u * 0.4:.1f}" '
                f'fill="{renk}"/>'
            )
        elif el["tip"] == "olcu":
            if etkilesimli:
                parcalar.append(
                    f'<g class="olcu" data-olcu="{n_olcu}" tabindex="0" role="button" '
                    f'aria-label="Ölçü {html.escape(el["metin"])}">'
                    + _olcu(el, renk, kal, k, tutamak=True)
                    + "</g>"
                )
            else:
                parcalar.append(_olcu(el, renk, kal, k))
            n_olcu += 1
        elif el["tip"] == "yazi":
            #  Geometri yazının ORTASINI verir ( DXF'te MIDDLE hizası );  SVG
            #  taban çizgisine yazar:  ölçü yazısı gibi 0,35·h aşağı ( eskiden
            #  etiketler ekranda DXF'tekinden 0,35·h yukarıdaydı — çizimin başlığı
            #  şeridin çizgisine biniyordu ).
            a, h = math.radians(el.get("aci", 0)), el["yukseklik"]
            parcalar.append(
                _metin(
                    el["x"] + 0.35 * h * math.sin(a),
                    el["y"] - 0.35 * h * math.cos(a),
                    el["metin"],
                    h,
                    renk,
                    -el.get("aci", 0),
                    el.get("hiza", "orta"),
                    k,
                )
            )
    bas = _metin(x1 + g / 2.0, y1 - 180, f"{baslik}   1/{olcek:g}", 90, "#1a1a1a") if baslik else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x1:.0f} {-y2 - 300:.0f} '
        f'{g:.0f} {d + 600:.0f}" width="{g / olcek:.0f}mm" height="{(d + 600) / olcek:.0f}mm">'
        f'<defs><pattern id="{onek}tarama" width="120" height="120" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45){_olcekle(k)}"><line x1="0" y1="0" x2="0" y2="120" '
        f'stroke="{SIYAH}" stroke-width="{_K[0.13]:g}"/></pattern>'
        f'<pattern id="{onek}tugla" width="240" height="120" patternUnits="userSpaceOnUse"'
        f"{_desen(k)}>"
        '<path d="M0 0 H240 M0 60 H240 M120 0 V60 M0 60 V120 M240 60 V120" '
        f'stroke="{SIYAH}" stroke-width="{_K[0.13]:g}" fill="none"/></pattern></defs>'
        '<rect x="-100000" y="-100000" width="200000" height="200000" fill="#ffffff"/>'
        f'<g transform="scale(1,-1)">{"".join(parcalar)}{bas}</g></svg>'
    )
