# -*- coding: utf-8 -*-
"""
AYIRMA KİRİŞİ  —  tek kuyuda iki asansörün arasındaki çelik kiriş ( 2 Kas )

Tek kuyuda ( tasarim/alanlar KUYU DÜZENİ ) iki asansörün arası açıktır:  ortaya
bakan raylar her konsol seviyesinde kuyunun önünden arkasına uzanan ayırma
kirişine ( NPU, gövdesi yatay — cizim/grup.py ) bağlanır.  Araştırma ve kararlar:
cikti/devir/AYIRMA_KIRISI_HESABI.md.

·  TS EN 81-20 m.5.7.4.6:  sehim sınırı rayın bağlantılarını açıkça sayar —
   "guide rails and their fixings ( brackets, separation beams )":  δperm 5 mm
   ( güvenlik tertibatlı ray ), 10 mm ( tertibatsız karşı ağırlık rayı ).
·  TS EN 81-20 Ek E.2 · EN 81-50 m.5.10.6:  kirişin sehimi rayın yer
   değiştirmesine katılır — δray + δkiriş ≤ δperm.

MODEL ( kullanıcı kararı 2 Kas — önerilenler ):
·  Basit mesnet, açıklık kuyu derinliği ( cıvatalı uç levhası moment aktarmaz —
   emniyetli ).
·  Yük:  iki asansörün ortaya bakan raylarının konsol kuvvetleri, hesabın bütün
   yük durumlarının en büyüğü ( kopru.kuvvetler );  aynı anda ve aynı yönde
   ( toplanır — emniyetli );  konsol kotları ayrı olsa da aynı kirişte sayılır.
   Kabin rayının ağzı kabine bakar:  Fy kirişe diktir.  Ortadaki karşı ağırlığın
   raylarının ağzı kuyu boyuncadır:  Fx kirişe diktir.  Kiriş boyunca kalan
   bileşen eksenel kuvvettir, duvara gider ( eğilmeye girmez ).
·  Gerilme:  σ = Mx / Wx + My / Wy ≤ σem ( ofisin ST 37 değeri — makine
   kirişleriyle aynı );  My kirişin kendi ağırlığından ( gövde yatay:  zayıf eksen ).
·  Kirişin duvara ankrajı binanın hesabıdır ( raporda not ).
"""

from temel import sayi_mi
from motor.ortak.adimlar import Bolum, hesap, kontrol, madde, metin, tr, trn, veri
from motor.uygulama import mukavemet
from motor.uygulama import mukavemet_tablolari
from motor.uygulama import uygulama_sabitleri
from cizim import geometri
from cizim import kopru

KIMLIK = "ayirma_kirisi"
AD = "AYIRMA KİRİŞİNİN HESAPLANMASI"
KAYNAK = "TS EN 81-20 m.5.7.4.6 · Ek E.2  ·  EN 81-50 m.5.10.6"


def _en_buyuk_sehim(sonuc, onek, eksen):
    """Rayın bölümündeki bütün yük durumlarının en büyük sehimi ( ara değerler )."""
    d = [
        abs(v) for k, v in (sonuc.get("ara") or {}).items() if k.startswith(onek) and k.endswith("." + eksen)
    ]
    d = [v for v in d if sayi_mi(v)]
    return max(d) if d else None


def yukler(sonuc):
    """Asansörün kirişe bağlanan raylarının kuvvetleri ( kiriş boyunca yeri ile ):
    ( D , [ { y , F , ray , dray , dperm } ] ) ;  asansör tek kuyuda değilse ya da
    çizimi kurulamıyorsa ( None , [] ).  Kuvvetin bulunamadığı rayda F None."""
    g = sonuc.get("girdi") or {}
    gc, _h = kopru.cizim_girdisi(g)
    if gc is None or not gc["kuyu"].get("acik_yan"):
        return None, []
    k, yan = gc["kuyu"], gc["kuyu"]["acik_yan"]
    kv = kopru.kuvvetler(sonuc)
    ad = sonuc.get("tanim") or ""
    S = sonuc.get("sabitler") or mukavemet.SABIT
    out = [
        {
            "y": gc["kabin_ray"]["kapi_arasi"],
            "F": kv.get("Fy_kabin"),
            "ray": f"{ad} kabin rayı  ( Fy )",
            "dray": _en_buyuk_sehim(sonuc, "kabin_ray.", "dy"),
            "dperm": S["dperm_kabin"],
        }
    ]
    ag = gc["agirlik"]
    if ag["yeri"] == yan:
        gt = (g.get("agirlik_guvenlik_tertibati") or "Yok") != "Yok"
        dperm = S["dperm_kabin"] if gt else S["dperm_agirlik"]
        for n, y in enumerate(geometri.agirlik_rayi_eksenleri(gc), 1):
            out.append(
                {
                    "y": y,
                    "F": kv.get("Fx_agirlik"),
                    "ray": f"{ad} karşı ağırlık rayı {n}  ( Fx )",
                    "dray": _en_buyuk_sehim(sonuc, "agirlik_ray", "dx"),
                    "dperm": dperm,
                }
            )
    return k["derinlik"], out


def _moment(L, yukler_, x):
    """Basit mesnetli kirişte x'teki eğilme momenti ( tekil yükler )."""
    return sum(F * (L - a) * x / L if x <= a else F * a * (L - x) / L for a, F in yukler_)


def _sehim(L, yukler_, x, EI):
    """Basit mesnetli kirişte x'teki sehim ( tekil yükler — üst üste binme )."""
    d = 0.0
    for a, F in yukler_:
        b = L - a
        if x <= a:
            d += F * b * x * (L * L - b * b - x * x) / (6 * EI * L)
        else:
            u = L - x
            d += F * a * u * (L * L - a * a - u * u) / (6 * EI * L)
    return d


def bolum(sonuclar, npu):
    """İki asansörün hesap sonuçlarından ( aktif ) kirişin bölümü;  tek kuyu
    değilse None.  Bölüm iki asansörün raporuna aynen girer.  σem ofisin
    değeri ( makine kirişleriyle aynı — Sabitler sekmesinden değişir )."""
    sigma_em = uygulama_sabitleri.sabitler((sonuclar[0].get("girdi") or {}).get("_ofis"))["sigma_em"]
    D, raylar = None, []
    for s in sonuclar:
        d, r = yukler(s)
        if d is None:
            return None
        D, raylar = d, raylar + r
    b = Bolum(AD, kimlik=KIMLIK, kaynak=KAYNAK)
    eksik = [r["ray"] for r in raylar if not sayi_mi(r["F"]) or not sayi_mi(r["dray"])]
    if eksik:
        b["adimlar"] = [metin("Kuvveti ya da sehimi hesaplanamayan raylar:  " + " · ".join(eksik))]
        b["sonuc"] = {
            "baslik": "KONTROL      σ ≤ σem   ·   δray + δkiriş ≤ δperm",
            "metin": "HESAP EKSİK — kirişe bağlanan rayların hesabı yapılamadı",
            "uygun": False,
            "maddeler": [madde("kirişe bağlanan rayların hesabı yapılamadı:  " + " · ".join(eksik))],
        }
        b["eksik_hesap"] = True
        return b

    E = mukavemet.SABIT["E"]
    Ix, Wx = mukavemet_tablolari.npu(npu, "Ix") * 1e4, mukavemet_tablolari.npu(npu, "Wx") * 1e3
    Wy, G = mukavemet_tablolari.npu(npu, "Wy") * 1e3, mukavemet_tablolari.npu(npu, "G")
    gn = mukavemet.SABIT["gn"]
    yk = [(r["y"], r["F"]) for r in raylar]
    Mx = max(_moment(D, yk, a) for a, _F in yk)
    q = G * gn / 1000.0  # N/mm
    My = q * D * D / 8.0
    sigma = Mx / Wx + My / Wy
    gerilme_uygun = sigma <= sigma_em

    adimlar = [
        metin(
            "Ortaya bakan raylar her konsol seviyesinde kuyunun önünden arkasına uzanan ayırma kirişine "
            "bağlanır.  Kiriş basit mesnetli;  iki asansörün kuvvetleri aynı anda ve aynı yönde alınır, "
            "konsol kotları ayrı olsa da aynı kirişte sayılır ( emniyetli ).  Kirişin duvara ankrajı "
            "binanın hesabıdır."
        ),
        veri("", "Kiriş profili  ( gövde yatay )", f"NPU {npu}", "", "GİRİŞ  ·  DIN 1026-1"),
        veri("L", "Açıklık  ( kuyu derinliği )", D, "mm", "ÇİZİMDEN", 0),
        veri("Ix", "Atalet momenti  ( güçlü eksen — yatay kuvvet )", Ix, "mm⁴", f"NPU {npu}", 0),
        veri("Wx", "Mukavemet momenti  ( güçlü eksen )", Wx, "mm³", f"NPU {npu}", 0),
        veri("Wy", "Mukavemet momenti  ( zayıf eksen — kendi ağırlığı )", Wy, "mm³", f"NPU {npu}", 0),
        veri("G", "Birim ağırlık", G, "kg/m", f"NPU {npu}"),
        veri("E", "Çeliğin elastisite modülü", E, "N/mm²", "EN 81-50 m.5.13", 0),
        metin("Kirişe gelen kuvvetler  ( bütün yük durumlarının en büyüğü — bölüm 7 · 8 ) :", vurgu=True),
    ]
    adimlar += [
        veri("", f"{r['ray']}  ·  ön duvardan {trn(r['y'], 0)} mm", r["F"], "N", "", 0) for r in raylar
    ]
    adimlar += [
        hesap(
            "Mx = Σ F · a · b / L  ( en büyük, kuvvet noktalarında )",
            "  +  ".join(f"{trn(F, 0)} × {trn(a, 0)} × {trn(D - a, 0)} / {trn(D, 0)}" for a, F in yk),
            Mx,
            "N·mm",
            "basit mesnet, tekil yükler",
            0,
        ),
        hesap("My = q · L² / 8  ( kendi ağırlığı )", f"{tr(q, 4)} × {trn(D, 0)}² / 8", My, "N·mm", "", 0),
        hesap(
            "σ = Mx / Wx + My / Wy",
            f"{trn(Mx, 0)} / {trn(Wx, 0)} + {trn(My, 0)} / {trn(Wy, 0)}",
            sigma,
            "N/mm²",
        ),
        kontrol(f"σ = {tr(sigma)}  ≤  σem = {tr(sigma_em)} N/mm²", gerilme_uygun),
        metin(
            "Sehim:  rayın kendi sehimi ( bölüm 7 · 8 ) ile kirişin o noktadaki sehimi toplanır "
            "( EN 81-50 m.5.10.6 δstr ) :",
            vurgu=True,
        ),
    ]
    sehim_uygun = True
    for r in raylar:
        dk = _sehim(D, yk, r["y"], E * Ix)
        top = r["dray"] + dk
        uygun = top <= r["dperm"]
        sehim_uygun = sehim_uygun and uygun
        adimlar.append(
            hesap(
                f"δ = δray + δkiriş  —  {r['ray']}",
                f"{tr(r['dray'])} + {tr(dk)}",
                top,
                "mm",
                f"δperm = {trn(r['dperm'], 0)} mm  ( TS EN 81-20 m.5.7.4.6 )",
            )
        )
        adimlar.append(kontrol(f"{tr(top)} mm  ≤  {trn(r['dperm'], 0)} mm", uygun))
    b["adimlar"] = adimlar
    neden = [n for n, u in (("eğilme gerilmesi", gerilme_uygun), ("sehim", sehim_uygun)) if not u]
    b["sonuc"] = {
        "baslik": "KONTROL      σ ≤ σem   ·   δray + δkiriş ≤ δperm",
        "metin": (
            f"UYGUNDUR  —  NPU {npu}"
            if not neden
            else f"UYGUN DEĞİLDİR — {' ve '.join(neden)} aşılıyor:  NPU profilini büyütün"
        ),
        "uygun": not neden,
    }
    if neden:
        b["sonuc"]["maddeler"] = [madde(f"{' ve '.join(neden)} aşılıyor", "NPU profilini büyütün")]
    return b
