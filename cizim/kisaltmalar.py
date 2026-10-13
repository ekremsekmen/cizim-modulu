# -*- coding: utf-8 -*-
"""
KISALTMALAR — ölçülerin kısa kodları ve çizimin VERİLER / KISALTMALAR tabloları.

Ölçü dili LiftDesigner gibidir ( kullanıcı 12 Eki:  "LD gibi kısa kod +
tablo" ):  asıl ölçüler kodla ( "SW2100" ), neyi ölçtüğü çizimden belli
olanlar yalnız sayıyla ( duvar, kasa, ray yüksekliği, eşikler ), kodların
Türkçesi çizimin yanındaki tabloda.  Kodların anlamı LiftDesigner'ın 11
projesinde ölçülerek doğrulandı ( cikti/araclar/ld_kodlari.py );  ray
aralıklarında programın kendi adları kalır ( kullanıcı kararı 13 Eki ):  LD
kabin rayları arasına BG, ağırlık rayları arasına DBG der — hesap programı ve
form DBG / DBGW kullanır.
"""

import re

from cizim import eleman
from cizim import uslup

#  Kod → Türkçesi ( tablo bu sırayla )
KODLAR = {
    "SW": "Kuyu iç genişliği",
    "SD": "Kuyu iç derinliği",
    "CW": "Kabin iç genişliği",
    "CD": "Kabin iç derinliği",
    "PLW": "Kabin dış genişliği",
    "DW": "Kapı açıklığı ( genişlik )",
    "DH": "Kapı açıklığı ( yükseklik )",
    "DBG": "Kabin rayları arası",
    "DBGW": "Karşı ağırlık rayları arası",
    "OH": "Kuyu üst boşluğu ( son kat )",
    "MRW": "Makine dairesi genişliği",
    "MRD": "Makine dairesi derinliği",
}


_KOD = re.compile(r"^([A-Z]+)\d")


def kodlu(kod, deger):
    """Ölçünün yazısı:  kod ve değer bitişik ( LiftDesigner:  "SW2010" )."""
    if kod not in KODLAR:
        raise KeyError(f"Tanımsız ölçü kodu:  {kod}")
    return f"{kod}{deger:g}"


def kodu(metin):
    """Ölçü yazısının kodu ( "DBGW850" → "DBGW" ) ya da None."""
    m = _KOD.match(metin or "")
    return m.group(1) if m and m.group(1) in KODLAR else None


def kullanilanlar(elemanlar):
    """Çizimin ölçülerinde geçen kodlar ( KODLAR sırasıyla )."""
    var = {kodu(el["metin"]) for el in elemanlar if el.get("tip") == "olcu"}
    return [k for k in KODLAR if k in var]


def projede(g, plandaki):
    """Paftanın BÜTÜN çizimlerinde geçen kodlar:  KISALTMALAR tablosu yalnız
    kuyu planındadır, paftanın tek tablosu odur.  Pafta ancak bütün çizimleri
    çizilebiliyorsa çıkar ( pafta.cizim_listesi ):  planın kodları, kesitlerin
    OH'si, giriş görünüşünün ve kapı kesitlerinin DH'si, makine daireli
    projede odanın MRW / MRD'si ( test_kisaltmalar bunu bütün çizimlerden
    sayarak denetler )."""
    var = set(plandaki) | {"DH", "OH"}
    if (g.get("makine") or {}).get("yeri") == "Makine dairesi":
        var |= {"MRW", "MRD"}
    return [k for k in KODLAR if k in var]


#  Tablonun boyları ( 1/20'de;  başka ölçekte k ile ):  satır adımı yazı
#  boyunun 1,6 katı, kod sütunu 300, iki tablo arası 2 satır
SATIR = 1.6 * uslup.NORMAL
KOD_SUTUNU = 300.0
KENAR = 60.0


def tablo(x, y, baslik, satirlar, ad, k=1.0):
    """Sola hizalı iki sütunlu tablo:  sol üst köşe ( x , y ).  satirlar:
    [ ( sol , sağ ) ].  Dönen:  ( elemanlar , alt kenarın y'si )."""
    h, adim = uslup.NORMAL * k, SATIR * k
    e = [eleman.ad(eleman.yazi(x, y - adim / 2.0, baslik, h, hiza="sol"), ad)]
    yy = y - adim
    e.append(eleman.ad(eleman.cizgi("YAZI", x, yy, x + _tablo_eni(baslik, satirlar, k), yy), ad))
    for sol, sag in satirlar:
        yy -= adim
        e.append(eleman.ad(eleman.yazi(x, yy + adim / 2.0, sol, h, hiza="sol"), ad))
        e.append(eleman.ad(eleman.yazi(x + KOD_SUTUNU * k, yy + adim / 2.0, sag, h, hiza="sol"), ad))
    return e, yy


def _tablo_eni(baslik, satirlar, k):
    h = uslup.NORMAL * k
    return max(
        [eleman.yazi_eni(baslik, h)] + [KOD_SUTUNU * k + eleman.yazi_eni(sag, h) for _sol, sag in satirlar]
    )
