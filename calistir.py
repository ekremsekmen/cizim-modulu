# -*- coding: utf-8 -*-
"""
ÖRNEK ÇİZİM ÜRETİCİ

    python3 calistir.py                 → ornekler/ klasörüne SVG + DXF yazar
    python3 calistir.py --aski Doğrudan → 1:1 askı düzeniyle

Hesap programından BAĞIMSIZDIR;  girdiyi cizim/girdi.py içindeki ÖRNEK
sözlüğünden alır.  İleride köprü ( cizim/kopru.py ) bu sözlüğü hesabın
sonuçlarından dolduracaktır.
"""
import argparse
import copy
import os
import sys

from cizim import dxf as CDX
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import svg as CSV

KOK = os.path.dirname(os.path.abspath(__file__))


def uret(g, ad, baslik, olcek=20):
    hata = CG.dogrula(g)
    if hata:
        print("GİRDİ REDDEDİLDİ:")
        for h in hata:
            print("   ·", h)
        return 1
    elemanlar = CGE.cerceveli(CGE.plan(g), baslik, olcek,
                              seritler=(f"{g['proje']['ad']}  ·  {g['proje']['asansor']}",))
    klasor = os.path.join(KOK, "ornekler")
    os.makedirs(klasor, exist_ok=True)
    svg = CSV.yaz(elemanlar, CGE.sinir(elemanlar, 120), "", olcek)
    open(os.path.join(klasor, ad + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(klasor, ad + ".dxf"), "wb").write(CDX.yaz(elemanlar, "", olcek))
    olcu = sum(1 for x in elemanlar if x["tip"] == "olcu")
    print(f"{ad}:  {len(elemanlar)} eleman · {olcu} ölçü  →  ornekler/{ad}.svg + .dxf")
    return 0


def main(argv):
    ayrıştırıcı = argparse.ArgumentParser(description="Kuyu planı çizer")
    ayrıştırıcı.add_argument("--aski", choices=CG.ASKI_DUZENLERI, default="Kabin altı")
    ayrıştırıcı.add_argument("--agirlik", choices=CG.AGIRLIK_YERLERI, default=None)
    ayrıştırıcı.add_argument("--ad", default="kuyu_plani")
    a = ayrıştırıcı.parse_args(argv)

    g = copy.deepcopy(CG.ORNEK)
    if a.aski == "Doğrudan":
        g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 450}
    else:
        g["aski"]["duzen"] = a.aski
    if a.agirlik:
        g["agirlik"]["yeri"] = a.agirlik
    return uret(g, a.ad, "KUYU PLANI  ( kabin hizasından yatay kesit )")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
