# -*- coding: utf-8 -*-
"""
ÇİZİMLERİN LİSTESİ  —  adı, doğrulaması, çizicisi, başlığı ve ölçeği

calistir.py ( tek tek çizim ) ve pafta.py ( TİP PROJE FORMATI ) buradan okur;
başlıklar ve ölçekler iki yerde ayrı yazılıp zamanla ayrışmasın.
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kabin_ustu as CKU
from cizim import kuyu_dibi as CKD
from cizim import kuyu_kesiti as CKK
from cizim import kuyu_ustu as CKT
from cizim import makine_dairesi as CMD


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
    "kuyu_kesiti_yan": (CKK.dogrula, CKK.yan_kesit,
                        "A-A KUYU DÜŞEY KESİTİ  ( yan — kabin en alt durakta )"),
    "kuyu_kesiti_on": (CKK.dogrula, CKK.on_kesit,
                       "B-B KUYU DÜŞEY KESİTİ  ( arkadan kat kapılarına — kabin en üst durakta )"),
}
#  1/20 dışındaki çizimler
OLCEKLER = {"kuyu_kesiti_yan": CKK.OLCEK, "kuyu_kesiti_on": CKK.OLCEK}


def plan_basligi(g, cizim, baslik):
    """Plan başlığına düşey kesitlerdeki seviye harfi:  "KUYU PLANI  C-C  ( … )".
    Düşey kesitler çizilemeyen düzende harf de yazılmaz."""
    harf = CKK.PLAN_HARFLERI.get(cizim)
    #  Makine dairesiz projede makine dairesi ve delik planının, makine daireli
    #  projede kuyu üstü planının kesitlerde seviyesi yok
    oda = (g.get("makine") or {}).get("yeri") == "Makine dairesi"
    gecerli = oda if cizim in ("makine_dairesi", "delik_plani") else (not oda if cizim == "kuyu_ustu" else True)
    if not harf or not gecerli or CKK.dogrula(g):
        return baslik
    ad, _, ek = baslik.partition("  (")
    return f"{ad}  {harf}-{harf}" + (f"  ({ek}" if ek else "")
