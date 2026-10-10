# -*- coding: utf-8 -*-
"""GİRDİ TARAMASI — 378 standart düzen programın yolundan geçer.

Her düzen formun isteği gibi api_cizimler'e gider;  çizilirse paftanın bütün
çizimleri kurulur ve denetlenir:  ölçü zincirleri kapanıyor mu, yazılar
birbirine, parçalara, parça kenarlarına binmiyor mu, NaN var mı.  Hükümler
( çizildi / ret ve ret sebebi ) depodaki kayıtla ( testler/tarama_hukumleri.json )
karşılaştırılır:  beklenmeyen bir hüküm değişikliği ya da sorunlu bir düzen
taramayı BAŞARISIZ yapar.

    .venv/bin/python -m araclar.tarama                 üç grup ( ana · kapi · diger )
    .venv/bin/python -m araclar.tarama kapi            tek grup
    .venv/bin/python -m araclar.tarama --yenile        hüküm kaydını yeniden yazar

--yenile DAVRANIŞI DEĞİŞTİRME İZNİDİR ( altın çıktılar gibi ):  yalnız hüküm
değişiklikleri tek tek incelenip onaylandıktan sonra.  Ayrıntılı sonuçlar
cikti/tarama/<grup>.json'a yazılır ( git'e girmez ).
"""

import collections
import itertools
import json
import os
import sys
import time
import traceback

import yollar

yollar.kur()

from araclar import kesisme as K
from cizim import eleman as CEL
from cizim import cizimler as CZ
from cizim import geometri as CGE
from cizim import pafta as CPF
from testler import test_yerlesim_saglamligi as Y

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "cikti", "tarama")
HUKUMLER = os.path.join(KOK, "testler", "tarama_hukumleri.json")
GRUPLAR = ("ana", "kapi", "diger")

PARCA = set(CGE.PARCA_KATMANLARI) | {"KAPI", "AGIRLIK", "KASNAK"}
#  Yazının üstünden geçebilecek ( maskeyle kesilecek ) çizgiler:  eksen, ölçü
#  çizgisi, gizli / alan çizgisi, seviye, kesit işareti, duvar taramasının içi —
#  programın kendi kuralı:  geometri.MASKELI_KATMANLAR + duvar taraması
SERBEST = set(CGE.MASKELI_KATMANLAR) | {"TARAMA-İÇİ", "TARAMA"}
#  Kutuların birbirine bu kadar girmesi çakışma sayılmaz ( çizim birimi )
PAY = 2


def _olcu_yazilari(e):
    """Ölçü yazılarının kutuları ( yeri geometri._yazilari_yerlestir'den ):
    ( metin, x0, y0, x1, y1 )."""
    out = []
    for el in e:
        if el["tip"] == "olcu" and el.get("yazi"):
            y = el["yazi"]
            w, h = CEL.yazi_eni(el["metin"], y["h"]) / 2.0, y["h"] / 2.0
            if y["aci"]:
                w, h = h, w
            out.append((el["metin"], y["x"] - w, y["y"] - h, y["x"] + w, y["y"] + h))
    return out


def _binisir(a, b):
    """İki ( metin, x0, y0, x1, y1 ) kutusu PAY'dan fazla iç içe mi."""
    return a[1] < b[3] - PAY and b[1] < a[3] - PAY and a[2] < b[4] - PAY and b[2] < a[4] - PAY


def denetle(g):
    """Paftanın bütün çizimlerinin sorunları:  [ ileti ]."""
    sorun = []
    md = g["makine"]["yeri"] == "Makine dairesi"
    for c in CPF.SIRA_MD if md else CPF.SIRA_MRL:
        dogrula, ciz, _ = CZ.CIZIMLER[c]
        try:
            h = dogrula(g)
            if h:
                sorun.append(f"{c}: doğrulama reddediyor ama uç çizdi:  {h[0][:90]}")
                continue
            e = ciz(g)
        except Exception as x:  # noqa: BLE001 — çöküş de bir bulgu
            sorun.append(f"{c}: ÇÖKTÜ {type(x).__name__}: {x}")
            continue
        for z in CGE.zincirler(e):
            if abs(z["toplam"] - (z["son"] - z["bas"])) > 0.5:
                sorun.append(f"{c}: zincir kapanmıyor {z['toplam']} vs {z['son'] - z['bas']}")
        olcu = _olcu_yazilari(e)
        yazi = [(el["metin"],) + tuple(CGE.sinir([el])) for el in e if el["tip"] == "yazi"]
        for a, b in itertools.combinations(olcu + yazi, 2):
            if _binisir(a, b):
                sorun.append(f"{c}: yazı çakışması '{a[0]}' / '{b[0]}'")
        parcalar = [
            (el.get("ad") or el["katman"], ("",) + tuple(CGE.sinir([el])))
            for el in e
            if el["tip"] == "dikdortgen" and el["katman"] in PARCA
        ]
        for a in olcu:
            ad = next((ad for ad, p in parcalar if _binisir(a, p)), None)
            if ad:
                sorun.append(f"{c}: ölçü yazısı parçada '{a[0]}' / {ad}")
        k = CZ.OLCEKLER.get(c, 20) / 20.0
        for metin, tip, kat, ad in K.kesismeler(e, k):
            if kat not in SERBEST:
                sorun.append(f"{c}: yazı parça kenarında '{metin}' / {kat} {ad}")
            elif kat == "TARAMA-İÇİ" and tip == "yazi":
                sorun.append(f"{c}: etiket duvarın içinde '{metin}'")
        for el in e:
            if any(
                isinstance(el.get(a), float) and el[a] != el[a]
                for a in ("x", "y", "g", "d", "x1", "y1", "x2", "y2", "r")
            ):
                sorun.append(f"{c}: NaN {el.get('ad')}")
    return sorun


def duzen(ad, v):
    """Bir düzenin sonucu:  { ad, durum ( çizildi · ret · çöktü ), hata | sorun }."""
    t = time.time()
    try:
        d = Y._cizim(v)
    except Exception:  # noqa: BLE001 — çöküş de bir bulgu
        return {"ad": ad, "durum": "çöktü", "ayrinti": traceback.format_exc()[-600:]}
    if not d.get("aktif"):
        return {"ad": ad, "durum": "ret", "hata": d.get("hata")}
    try:
        g, _A, _h = Y._g(v)
        s = denetle(g)
    except Exception:  # noqa: BLE001
        s = ["DENETİM ÇÖKTÜ " + traceback.format_exc()[-400:]]
    return {"ad": ad, "durum": "çizildi", "sorun": s, "sure": round(time.time() - t, 1)}


def duzenler(grup):
    """( ad , formun isteği ) — grubun düzenleri."""
    if grup == "ana":
        for Q in Y.KABIN:
            for yer in ("Sağ", "Sol", "Arka"):
                for mrl in (True, False):
                    for aski in (
                        {"aski_duzeni": "Kabin altı"},
                        {"aski_duzeni": "Kabin üstü"},
                        {"aski_orani": 1},
                    ):
                        v = Y._veri(Q, mrl, yer, **aski)
                        if yer == "Arka":
                            v["asansorler"][0]["kuyu_derinligi"] = Y.KABIN[Q][1] + 700
                        if aski.get("aski_duzeni") == "Kabin üstü":
                            v["asansorler"][0]["son_kat_yuksekligi"] = 5000
                        yield f"{Q} {yer} {'MRL' if mrl else 'MD'} {aski}", v
    elif grup == "kapi":
        from motor.uygulama import mukavemet_tablolari as MT

        for Q in (450, 800, 1000, 1600, 2500):
            for yer in ("Sağ", "Sol", "Arka"):
                for tip in MT.KAPI_TIPLERI:
                    ek = (
                        {
                            "aski_duzeni": "Kabin üstü",
                            "son_kat_yuksekligi": 5000,
                            "makine_raya_biniyor": "Bina yapısına",
                        }
                        if yer == "Arka"
                        else {}
                    )
                    v = Y._veri(Q, True, yer, kat_kapisi_tipi=tip, **ek)
                    if yer == "Arka":
                        v["asansorler"][0]["kuyu_derinligi"] = Y.KABIN[Q][1] + 700
                    yield f"{Q} {yer} {tip}", v
    elif grup == "diger":
        for Q in (320, 630, 1275, 2000):
            for su in ("Dik duruş", "Çömelme"):
                for sd in ("Dik duruş", "Çömelme", "Yatarak"):
                    for mont in ("Kuyu içine", "Duvar boşluğuna"):
                        for hiz in (1.0, 1.6):
                            v = Y._veri(
                                Q,
                                Q % 2 == 0,
                                "Sağ",
                                siginma_tipi_ust=su,
                                siginma_tipi_dip=sd,
                                kapi_montaji=mont,
                                beyan_hizi=hiz,
                            )
                            yield f"{Q} üst={su} dip={sd} {mont} v={hiz}", v
    else:
        raise ValueError(f"bilinmeyen grup:  {grup!r} — {GRUPLAR}")


def hukum(r):
    """Kayda geçen hüküm:  durum ve ( ret ise ) ilk sebep."""
    return {"durum": r["durum"], "sebep": (r.get("hata") or [""])[0] if r["durum"] == "ret" else ""}


def tara(grup):
    sonuc = [duzen(ad, v) for ad, v in duzenler(grup)]
    os.makedirs(CIKTI, exist_ok=True)
    with open(os.path.join(CIKTI, f"{grup}.json"), "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)
    return sonuc


def karsilastir(grup, sonuc, kayit):
    """Hüküm değişiklikleri ve sorunlar:  [ ileti ]."""
    out = []
    eski = kayit.get(grup, {})
    yeni = {r["ad"]: hukum(r) for r in sonuc}
    for ad in sorted(set(eski) | set(yeni)):
        if ad not in yeni:
            out.append(f"düzen artık taranmıyor:  {ad}")
        elif ad not in eski:
            out.append(f"yeni düzen ( kayıtta yok ):  {ad}  →  {yeni[ad]['durum']}")
        elif eski[ad] != yeni[ad]:
            e, y = eski[ad], yeni[ad]
            out.append(
                f"{ad}:  {e['durum']} → {y['durum']}"
                + (f"  ( {y['sebep'][:120]} )" if y["sebep"] else "")
                + (
                    f"  ·  önceki sebep:  {e['sebep'][:120]}"
                    if e["sebep"] and e["sebep"] != y["sebep"]
                    else ""
                )
            )
    for r in sonuc:
        for s in r.get("sorun") or []:
            out.append(f"SORUN  {r['ad']}:  {s}")
        if r["durum"] == "çöktü":
            out.append(f"ÇÖKTÜ  {r['ad']}:  {r['ayrinti']}")
    return out


def main(argv):
    yenile = "--yenile" in argv
    gruplar = [a for a in argv if not a.startswith("--")] or list(GRUPLAR)
    kayit = {}
    if os.path.exists(HUKUMLER):
        with open(HUKUMLER, encoding="utf-8") as f:
            kayit = json.load(f)
    basarili = True
    for grup in gruplar:
        t = time.time()
        sonuc = tara(grup)
        sayi = collections.Counter(r["durum"] for r in sonuc)
        sorunlu = sum(1 for r in sonuc if r.get("sorun"))
        print(
            f"{grup}:  {len(sonuc)} düzen  ·  {dict(sayi)}  ·  sorunlu {sorunlu}  ·  "
            f"{time.time() - t:.0f} sn",
            flush=True,
        )
        if yenile:
            kayit[grup] = {r["ad"]: hukum(r) for r in sonuc}
            continue
        farklar = karsilastir(grup, sonuc, kayit)
        for f in farklar:
            print("   " + f)
        basarili = basarili and not farklar
    if yenile:
        with open(HUKUMLER, "w", encoding="utf-8") as f:
            json.dump(kayit, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        print(f"hüküm kaydı yazıldı:  {os.path.relpath(HUKUMLER, KOK)}")
    return 0 if basarili else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
