# -*- coding: utf-8 -*-
"""
ÇİZİM  →  SVG   ( ekranda görmek ve gözle denetlemek için )

DXF ile AYNI eleman listesini okur.  Ölçü birimi mm'dir;  SVG'nin y ekseni
aşağı baktığı için çizim bir kez ters çevrilir, metinler kendi içinde geri
çevrilir ki okunaklı kalsın.
"""

import html
import math
from typing import NamedTuple

from cizim import eleman
from cizim import geometri
from cizim import kisaltmalar
from cizim import parca_adlari
from cizim import uslup

#  TEKNİK RESİM ÜSLUBU ( ISO 128 ):  kalem kalınlığı, çizgi tipi ve renk
#  cizim/uslup.py'de — DXF ile aynı tablo ( 12 Eki:  ikisi ayrı tutulurken 33
#  katmanın 22'sinde kalınlık farklıydı ).  Kalınlıklar 1/20'ye göre birim:
#  1/20'de 0,50 mm = 10;  başka ölçekte k ile büyür.
SIYAH = uslup.SIYAH
#  Dolgu yalnız örtmek için ( zemin rengiyle — Renkler.zemin ):  kesitte kabin ve
#  kapı arkasındakini, yük kutusu oku örter.  Renkli dolgu yok.
DOLGU = ("KAPI", "KABIN", "YUK")


class Renkler(NamedTuple):
    """Renk takımı:  KAGIT ( beyaz zemin, ekran rengi — PDF ile aynı ) ya da CAD
    ( AutoCAD'in koyu model alanı, DXF'in katman renkleri — ekranın tuvali )."""

    zemin: str  # arka plan;  örtü ( DOLGU ) ve yazı halesi de bu renkte
    cad: bool  # katman rengi DXF'inki ( uslup.cad_rengi ) mi
    baslik: str  # çizimin başlığının rengi


KAGIT = Renkler("#ffffff", False, "#1a1a1a")
CAD = Renkler(uslup.CAD_ZEMIN, True, uslup.ACI_RGB[7])


def kalem(katman, r=KAGIT):
    """( renk , 1/20'de kalınlık birimi )"""
    k = uslup.KATMAN[katman]
    return (uslup.cad_rengi(katman) if r.cad else k.ekran), round(k.kalinlik * 20, 3)


def _dolgu(katman, r):
    """Örtü:  dolgulu katmanın ( DOLGU ) parçası zemin renginde dolar."""
    return r.zemin if katman in DOLGU else "none"


def _dikdortgen(el, renk, kalinlik, k=1.0, r=KAGIT):
    dolgu = _dolgu(el["katman"], r)
    kesik = _kesik_ozniteligi(el, k)
    return (
        f'<rect x="{el["x"]:.1f}" y="{el["y"]:.1f}" width="{el["g"]:.1f}" '
        f'height="{el["d"]:.1f}" fill="{dolgu}" stroke="{renk}" '
        f'stroke-width="{kalinlik}"{kesik}/>'
    )


def _bicim(el, renk, kalinlik, k=1.0, r=KAGIT):
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
                f'height="{el["d"] - 2 * y:.1f}" fill="{r.zemin}" stroke="none"/>'
            )
    for p in el["bicim"]:
        nok = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["noktalar"])
        kal = f"{uslup.INCE * 20 * k:g}" if p.get("ince") else kalinlik
        if not p.get("kapali", True):
            out.append(
                f'<polyline points="{nok}" fill="none" stroke="{renk}" '
                f'stroke-width="{kal}" stroke-linejoin="miter"/>'
            )
            continue
        dolgu = renk if p.get("dolu") else _dolgu(el["katman"], r)
        out.append(
            f'<polygon points="{nok}" fill="{dolgu}" stroke="{renk}" '
            f'stroke-width="{kal}" stroke-linejoin="miter"/>'
        )
    return "".join(out)


def _olcu(el, renk, kalinlik, k=1.0, tutamak=False, r=KAGIT):
    """Ölçü çizgisi + iki uçta ölçü ucu + yazı.

    tutamak:  ekranda tıklanacak ölçü için çizginin ve yazının üstüne
    görünmez, geniş bir tutma yüzeyi ( ince çizgiye ve harflere tam
    denk getirmek gerekmesin ).

    Yazının yeri geometride bulunur ( el["yazi"] = yazının MERKEZİ );  DXF de
    aynı yeri kullanır.  UÇ ( uslup.TIK · SAPLAMA ):  45° eğik çizgi ve dik
    KISA uzatma çizgisi — DXF'teki ucun bloğuyla aynı ( dxf.UC_BLOGU ).  Uzun
    uzatma çizgileri bütün planı boydan boya kesiyordu ( kullanıcı kararı ).
    """
    t, sp = uslup.TIK * 20 * k, uslup.SAPLAMA * 20 * k
    tik = f"{uslup.TIK_KALEM * 20 * k:g}"
    if el["yon"] == "yatay":
        x1, x2, y = el["a"][0], el["b"][0], el["kot"]
        cizgi = f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"'
        uclar = [((x, y - sp), (x, y + sp), (x - t, y - t), (x + t, y + t)) for x in (x1, x2)]
    else:
        y1, y2, x = el["a"][1], el["b"][1], el["kot"]
        cizgi = f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"'
        #  Uç ölçü çizgisiyle döner ( 90° ):  eğik çizgi öbür yöne yatar
        uclar = [((x - sp, y), (x + sp, y), (x + t, y - t), (x - t, y + t)) for y in (y1, y2)]
    uc = "".join(
        f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
        f'stroke="{renk}" stroke-width="{kalinlik}"/>'
        f'<line x1="{c[0]:.1f}" y1="{c[1]:.1f}" x2="{d[0]:.1f}" y2="{d[1]:.1f}" '
        f'stroke="{renk}" stroke-width="{tik}"/>'
        for a, b, c, d in uclar
    )
    yz = el["yazi"]
    #  Merkezden taban çizgisine:  yazının "yukarı" yönünün tersine 0,35·h
    a = math.radians(yz["aci"])
    bx = yz["x"] + 0.35 * yz["h"] * math.sin(a)
    by = yz["y"] - 0.35 * yz["h"] * math.cos(a)
    tut = ""
    if tutamak:
        h, w = yz["h"], eleman.yazi_eni(el["metin"], yz["h"])
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
        + _metin(bx, by, el["metin"], yz["h"], renk, -yz["aci"], k=k, zemin=r.zemin)
        + tut
    )


#  YAZI MASKESİ ( DXF'teki MTEXT arka planı / dimtfill ile aynı iş ):  harflerin
#  çevresinde zemin renginde bir hale — çizgi yazının üstünden geçmez, yazının
#  olduğu yerde kesilir ( ISO 128 ).  Halenin eni yazı boyunun oranı;  ölçü
#  yazısından büyük yazılarda ( çizimin başlığı ) ölçü yazısınınki kadar — geniş
#  hale başlığın altındaki şerit çizgisini kesiyordu.
HALE = 0.6
HALE_AZAMI = uslup.NORMAL * HALE  # 1/20'de;  başka ölçekte k ile
#  Yazı tipi:  ekranda gömülü Liberation Sans ( style.css · CizimYazi ), yoksa
#  Arial — ikisinin harf enleri aynı ( harf_eni ).  Kerning kapalı:  yazının
#  eni harflerin toplamı olsun ( AutoCAD de kerning yapmaz ).
YAZI_TIPI = "CizimYazi, Arial, 'Liberation Sans', sans-serif"


def _metin(x, y, metin, yukseklik, renk, aci=0, hiza="orta", k=1.0, zemin="#ffffff"):
    #  Çizim ters çevrildiği için yazı kendi ekseninde geri çevrilir.
    hale = min(HALE * yukseklik, HALE_AZAMI * k)
    tutucu = {"orta": "middle", "sol": "start", "sag": "end"}.get(hiza, "middle")
    return (
        f'<g transform="translate({x:.1f},{y:.1f}) scale(1,-1) rotate({aci})">'
        f'<text x="0" y="0" font-family="{YAZI_TIPI}" font-size="{yukseklik:g}" style="font-kerning:none" '
        f'fill="{renk}" stroke="{zemin}" stroke-width="{hale:.1f}" '
        f'stroke-linejoin="round" paint-order="stroke" '
        f'text-anchor="{tutucu}">{html.escape(metin)}</text></g>'
    )


def kesik(desen, k=1.0):
    """Çizgi tipinin SVG deseni ( 1/20 birimi, k ile ölçekli ) — DXF'teki ISO
    tipiyle aynı ( uslup.DESENLER );  nokta ekranda uslup.NOKTA boyunda çizgi."""
    d = uslup.DESENLER[desen]
    return " ".join(f"{(abs(v) * d.olcek or uslup.NOKTA) * 20 * k:g}" for v in d.tanim)


def _kesik_ozniteligi(el, k):
    desen = "EKSEN" if el["tip"] == "eksen" else uslup.KATMAN[el["katman"]].desen
    return f' stroke-dasharray="{kesik(desen, k)}"' if desen else ""


def _taramalar(onek, k, r=KAGIT):
    """Duvar kesiti ( 45° ) ve tuğla taramasının desenleri — DXF'teki ANSI31 ve
    BRICK ile aynı aralıkta ( uslup.TARAMALAR );  renk TARAMA katmanınki."""
    ince = f'stroke="{kalem("TARAMA", r)[0]}" stroke-width="{uslup.KATMAN["TARAMA"].kalinlik * 20:g}"'
    a = uslup.TARAMALAR["tarama"].aralik * 20
    t = uslup.TARAMALAR["tarama_tugla"].aralik * 20
    return (
        f'<pattern id="{onek}tarama" width="{a:g}" height="{a:g}" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(-45){_olcekle(k)}"><line x1="0" y1="0" x2="0" y2="{a:g}" {ince}/></pattern>'
        f'<pattern id="{onek}tugla" width="{2 * t:g}" height="{2 * t:g}" patternUnits="userSpaceOnUse"'
        f"{_desen(k)}>"
        f'<path d="M0 0 H{2 * t:g} M0 {t:g} H{2 * t:g} M{t:g} 0 V{t:g} M0 {t:g} V{2 * t:g} M{2 * t:g} {t:g} V{2 * t:g}" '
        f'{ince} fill="none"/></pattern>'
    )


def _olcekle(k):
    return "" if k == 1 else f" scale({k:g})"


def _desen(k):
    return "" if k == 1 else f' patternTransform="scale({k:g})"'


def _parca_isaretleri(elemanlar):
    """Ekranda her eleman katmanıyla ( katmanlar aç / kapa ) ve parça örneğiyle
    ( fareyle üstüne gelince adı, örneği vurgulanır — geometri.parca_ornekleri,
    DXF'in parça bloklarıyla aynı örnekler ) işaretlenir:  13 Eki.
    id(eleman) → <g> öznitelikleri."""
    ornek = {}
    for n, (ad, liste) in enumerate(geometri.parca_ornekleri(elemanlar)):
        for p in liste:
            ornek[id(p)] = f' data-parca="{ad}-{n}" data-ad="{html.escape(parca_adlari.ad(ad))}"'
    return ornek


def yaz(elemanlar, sinir, baslik="", olcek=20, onek="", etkilesimli=False, r=KAGIT):
    """Eleman listesini SVG metnine çevirir.  r:  renk takımı ( KAGIT · CAD ).

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
    ornek = _parca_isaretleri(elemanlar) if etkilesimli else {}
    #  Önce parçalar, sonra ölçüler, en son etiketler:  yazının halesi
    #  kendinden önce çizileni örter ( DXF ile aynı sıra ).
    sira = {"olcu": 1, "yazi": 2}
    for el in sorted(elemanlar, key=lambda el: sira.get(el["tip"], 0)):
        once = len(parcalar)
        renk, kal = kalem(el["katman"], r)
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
            parcalar.append(
                _bicim(el, renk, kal, k, r) if "bicim" in el else _dikdortgen(el, renk, kal, k, r)
            )
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
                #  Kodlu ölçünün Türkçesi ( kisaltmalar ):  üstüne gelince ve ölçü kutusunda
                ack = kisaltmalar.KODLAR.get(kisaltmalar.kodu(el["metin"]) or "", "")
                ek = f' data-aciklama="{html.escape(ack)}"' if ack else ""
                #  ( adı "baslik" değil:  fonksiyonun başlık parametresini eziyordu, ekranda
                #  çizimin altına son ölçünün açıklaması "başlık" diye basılıyordu — 13 Eki )
                ipucu = f"<title>{html.escape(ack)}</title>" if ack else ""
                parcalar.append(
                    f'<g class="olcu" data-olcu="{n_olcu}" tabindex="0" role="button"{ek} '
                    f'aria-label="Ölçü {html.escape(el["metin"])}{" — " + html.escape(ack) if ack else ""}">'
                    + ipucu
                    + _olcu(el, renk, kal, k, tutamak=True, r=r)
                    + "</g>"
                )
            else:
                parcalar.append(_olcu(el, renk, kal, k, r=r))
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
                    r.zemin,
                )
            )
        if etkilesimli and el["tip"] != "olcu" and len(parcalar) > once:
            parcalar[once:] = [
                f'<g data-katman="{el["katman"]}"{ornek.get(id(el), "")}>{"".join(parcalar[once:])}</g>'
            ]
    bas = (
        _metin(x1 + g / 2.0, y1 - 180, f"{baslik}   1/{olcek:g}", 90, r.baslik, zemin=r.zemin)
        if baslik
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x1:.0f} {-y2 - 300:.0f} '
        f'{g:.0f} {d + 600:.0f}" width="{g / olcek:.0f}mm" height="{(d + 600) / olcek:.0f}mm">'
        f"<defs>{_taramalar(onek, k, r)}</defs>"
        f'<rect x="-100000" y="-100000" width="200000" height="200000" fill="{r.zemin}"/>'
        f'<g transform="scale(1,-1)">{"".join(parcalar)}{bas}</g></svg>'
    )
