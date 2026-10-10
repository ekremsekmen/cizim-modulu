# -*- coding: utf-8 -*-
"""
ÖRNEK ÇİZİM ÜRETİCİ

    python3 calistir.py                 → cikti/ klasörüne SVG + DXF yazar ( git'e girmez )
    python3 calistir.py --aski Doğrudan → 1:1 askı düzeniyle
    python3 calistir.py --cizim kabin_ustu → kabin üstü planı
    python3 calistir.py --cizim kuyu_dibi  → kuyu dibi planı
    python3 calistir.py --cizim kuyu_ustu  → kuyu üstü planı ( MRL )
    python3 calistir.py --cizim makine_dairesi / delik_plani
    python3 calistir.py --cizim kuyu_kesiti_yan / kuyu_kesiti_on → tam boy A-A / B-B ( 1/50 )
    python3 calistir.py --cizim kuyu_kesiti_on --makine "Makine dairesi" → makine daireli
    python3 calistir.py --cizim makine_dairesi --makine "Makine dairesi" --makine_tipi Dişli
    python3 calistir.py --pafta          → bütün çizimler TİP PROJE FORMATINDA ( cikti/pafta.dxf )

Hesap programından BAĞIMSIZDIR;  girdiyi cizim/girdi.py içindeki ÖRNEK
sözlüğünden alır.  Birleşik programda ( hesap/main.py ) çizim girdisini
köprü ( cizim/kopru.py ) formun girdisinden ve hesabın sonucundan kurar.
"""

import argparse
import copy
import os
import sys

from cizim import cizimler as CZ
from cizim import dxf as CDX
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kabin_ustu as CKU
from cizim import donanim as CDN
from cizim import makine as CMK
from cizim import pafta as CPF
from cizim import svg as CSV

KOK = os.path.dirname(os.path.abspath(__file__))


#  Çizimlerin listesi, başlıkları ve ölçekleri tek yerde ( pafta da okur )
CIZIMLER, OLCEKLER, plan_basligi = CZ.CIZIMLER, CZ.OLCEKLER, CZ.plan_basligi


def uret(g, ad, baslik, olcek=20, cizim="kuyu_plani"):
    dogrula, ciz, _ = CIZIMLER[cizim]
    hata = dogrula(g)
    if hata:
        print("GİRDİ REDDEDİLDİ:")
        for h in hata:
            print("   ·", h)
        return 1
    elemanlar = CGE.cerceveli(
        ciz(g), baslik, olcek, seritler=(f"{g['proje']['ad']}  ·  {g['proje']['asansor']}",)
    )
    klasor = os.path.join(KOK, "cikti")
    os.makedirs(klasor, exist_ok=True)
    svg = CSV.yaz(elemanlar, CGE.sinir(elemanlar, 120 * olcek / 20.0), "", olcek)
    open(os.path.join(klasor, ad + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(klasor, ad + ".dxf"), "wb").write(CDX.yaz(elemanlar, "", olcek))
    olcu = sum(1 for x in elemanlar if x["tip"] == "olcu")
    print(f"{ad}:  {len(elemanlar)} eleman · {olcu} ölçü  →  cikti/{ad}.svg + .dxf")
    return 0


def pafta_uret(g, ad):
    try:
        d, bilgi = CPF.belge(g)
    except ValueError as h:
        print(h)
        return 1
    klasor = os.path.join(KOK, "cikti")
    os.makedirs(klasor, exist_ok=True)
    d.saveas(os.path.join(klasor, ad + ".dxf"))
    open(os.path.join(klasor, ad + ".svg"), "w", encoding="utf-8").write(CPF.onizleme(d))
    print(f"{ad}:  {len(bilgi['cizimler'])} çizim → cikti/{ad}.dxf + .svg ( önizleme )")
    for c in bilgi["cizimler"]:
        x0, y0, x1, y1 = c["kutu"]
        print(f"   1/{c['olcek']:<3g} {x1 - x0:6.1f} × {y1 - y0:5.1f} mm   {c['baslik']}")
    return 0


def main(argv):
    ayrıştırıcı = argparse.ArgumentParser(description="Kuyu planı çizer")
    ayrıştırıcı.add_argument("--aski", choices=CG.ASKI_DUZENLERI, default="Kabin altı")
    ayrıştırıcı.add_argument("--agirlik", choices=CG.AGIRLIK_YERLERI, default=None)
    ayrıştırıcı.add_argument("--cizim", choices=tuple(CIZIMLER), default="kuyu_plani")
    ayrıştırıcı.add_argument("--siginma", choices=tuple(CKU.SIGINMA), default=None)
    ayrıştırıcı.add_argument("--makine", choices=CDN.MAKINE_YERLERI, default=None)
    ayrıştırıcı.add_argument("--makine_tipi", choices=CMK.TIPLER, default=None)
    ayrıştırıcı.add_argument(
        "--pafta", action="store_true", help="bütün çizimleri TİP PROJE FORMATINA yerleştir"
    )
    ayrıştırıcı.add_argument("--ad", default=None)
    a = ayrıştırıcı.parse_args(argv)

    g = copy.deepcopy(CG.ORNEK)
    if a.aski == "Doğrudan":
        #  1:1:  kasnak yok, halatlar ( adet · çap ) aynı
        g["aski"] = {
            "duzen": "Doğrudan",
            "halat_adedi": g["aski"]["halat_adedi"],
            "halat_capi": g["aski"]["halat_capi"],
        }
    else:
        g["aski"]["duzen"] = a.aski
    if a.agirlik:
        g["agirlik"]["yeri"] = a.agirlik
        if a.agirlik == "Sağ":
            g["kabin"]["kaciklik_y"] = -g["kabin"]["kaciklik_y"]
            g["kapi"]["sol_pay"] = g["kuyu"]["genislik"] - g["kapi"]["sol_pay"] - g["kapi"]["genislik"]
            #  Kapı da aynadır:  sağa açılır ( kanat cebi sol duvara sığmaz )
            g["kapi"]["tip"] = "Teleskopik Sağ"
        if a.agirlik == "Arka":
            #  Arkadaki ağırlık kabinin arkasına sığmalı ( m.5.2.5.5.1 h, 50 mm ):
            #  örnek kuyu 2.100 derinlikte, kabin ortada, kapı ona göre
            #  ( testlerdeki _arka düzeni ).
            g["kuyu"]["derinlik"] = 2100
            g["kabin"]["kaciklik_y"] = 0
            g["kapi"]["sol_pay"] = 600
    if a.siginma:
        g["kabin_ustu"]["siginma_tipi"] = a.siginma
    if a.makine:
        g["makine"]["yeri"] = a.makine
    if a.makine_tipi:
        g["makine"]["tip"] = a.makine_tipi
    if a.pafta:
        return pafta_uret(g, a.ad or "pafta")
    return uret(
        g,
        a.ad or a.cizim,
        plan_basligi(g, a.cizim, CIZIMLER[a.cizim][2]),
        OLCEKLER.get(a.cizim, 20),
        cizim=a.cizim,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
