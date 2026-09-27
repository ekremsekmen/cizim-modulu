# -*- coding: utf-8 -*-
"""
ÖRNEK ÇİZİM ÜRETİCİ

    python3 calistir.py                 → ornekler/ klasörüne SVG + DXF yazar
    python3 calistir.py --aski Doğrudan → 1:1 askı düzeniyle
    python3 calistir.py --cizim kabin_ustu → kabin üstü planı
    python3 calistir.py --cizim kuyu_dibi  → kuyu dibi planı
    python3 calistir.py --cizim kuyu_ustu  → kuyu üstü planı ( MRL )
    python3 calistir.py --cizim makine_dairesi / delik_plani
    python3 calistir.py --cizim kuyu_dibi_kesiti / kuyu_ustu_kesiti
    python3 calistir.py --cizim kuyu_kesiti_yan / kuyu_kesiti_on → tam boy A-A / B-B ( 1/50 )
    python3 calistir.py --cizim kuyu_kesiti_on --makine "Makine dairesi" → makine daireli

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
from cizim import kabin_ustu as CKU
from cizim import kuyu_dibi as CKD
from cizim import kuyu_ustu as CKT
from cizim import makine_dairesi as CMD
from cizim import donanim as CDN
from cizim import dusey as CDU
from cizim import kuyu_kesiti as CKK
from cizim import svg as CSV

KOK = os.path.dirname(os.path.abspath(__file__))


CIZIMLER = {
    "kuyu_plani": (CG.dogrula, CGE.plan, "KUYU PLANI  ( kabin hizasından yatay kesit )"),
    "kabin_ustu": (CKU.dogrula, CKU.ciz,
                   "KABİN ÜSTÜ PLANI  ( kabin tavanı hizasından yatay kesit )"),
    "kuyu_dibi": (CKD.dogrula, CKD.ciz,
                  "KUYU DİBİ PLANI  ( kuyu tabanından yatay kesit )"),
    "kuyu_ustu": (CKT.dogrula, CKT.ciz,
                  "KUYU ÜSTÜ PLANI  ( makine dairesiz — kuyu tepesinden yatay kesit )"),
    "makine_dairesi": (CMD.dogrula, CMD.ciz, "MAKİNE DAİRESİ PLANI"),
    "delik_plani": (CMD.dogrula, CMD.delik_plani, "KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI"),
    "kuyu_dibi_kesiti": (CDU.dogrula, CDU.kuyu_dibi_kesiti,
                         "KUYU DİBİ DÜŞEY KESİTİ  ( kabin tam ezilmiş tamponunda )"),
    "kuyu_ustu_kesiti": (CDU.dogrula, CDU.kuyu_ustu_kesiti,
                         "KUYU ÜSTÜ DÜŞEY KESİTİ  ( kabin en üst konumunda )"),
    "kuyu_kesiti_yan": (CKK.dogrula, CKK.yan_kesit,
                        "A-A KUYU DÜŞEY KESİTİ  ( yan — kabin en alt durakta )"),
    "kuyu_kesiti_on": (CKK.dogrula, CKK.on_kesit,
                       "B-B KUYU DÜŞEY KESİTİ  ( arkadan kat kapılarına — kabin en üst durakta )"),
}
#  1/20 dışındaki çizimler
OLCEKLER = {"kuyu_kesiti_yan": CKK.OLCEK, "kuyu_kesiti_on": CKK.OLCEK}


def uret(g, ad, baslik, olcek=20, cizim="kuyu_plani"):
    dogrula, ciz, _ = CIZIMLER[cizim]
    hata = dogrula(g)
    if hata:
        print("GİRDİ REDDEDİLDİ:")
        for h in hata:
            print("   ·", h)
        return 1
    elemanlar = CGE.cerceveli(ciz(g), baslik, olcek,
                              seritler=(f"{g['proje']['ad']}  ·  {g['proje']['asansor']}",))
    klasor = os.path.join(KOK, "ornekler")
    os.makedirs(klasor, exist_ok=True)
    svg = CSV.yaz(elemanlar, CGE.sinir(elemanlar, 120 * olcek / 20.0), "", olcek)
    open(os.path.join(klasor, ad + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(klasor, ad + ".dxf"), "wb").write(CDX.yaz(elemanlar, "", olcek))
    olcu = sum(1 for x in elemanlar if x["tip"] == "olcu")
    print(f"{ad}:  {len(elemanlar)} eleman · {olcu} ölçü  →  ornekler/{ad}.svg + .dxf")
    return 0


def main(argv):
    ayrıştırıcı = argparse.ArgumentParser(description="Kuyu planı çizer")
    ayrıştırıcı.add_argument("--aski", choices=CG.ASKI_DUZENLERI, default="Kabin altı")
    ayrıştırıcı.add_argument("--agirlik", choices=CG.AGIRLIK_YERLERI, default=None)
    ayrıştırıcı.add_argument("--cizim", choices=tuple(CIZIMLER), default="kuyu_plani")
    ayrıştırıcı.add_argument("--siginma", choices=tuple(CKU.SIGINMA), default=None)
    ayrıştırıcı.add_argument("--makine", choices=CDN.MAKINE_YERLERI, default=None)
    ayrıştırıcı.add_argument("--ad", default=None)
    a = ayrıştırıcı.parse_args(argv)

    g = copy.deepcopy(CG.ORNEK)
    if a.aski == "Doğrudan":
        g["aski"] = {"duzen": "Doğrudan", "nokta_arasi": 450}
    else:
        g["aski"]["duzen"] = a.aski
    if a.agirlik:
        g["agirlik"]["yeri"] = a.agirlik
    if a.siginma:
        g["kabin_ustu"]["siginma_tipi"] = a.siginma
    if a.makine:
        g["makine"]["yeri"] = a.makine
    return uret(g, a.ad or a.cizim, CIZIMLER[a.cizim][2], OLCEKLER.get(a.cizim, 20), cizim=a.cizim)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
