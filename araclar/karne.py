# -*- coding: utf-8 -*-
"""KALİTE KARNESİ — çizimlerin ölçülen kusurları, SAYI olarak ( 26 Eki, kalite
denetimi:  cikti/arastirma/KALITE_DENETIMI_26EKI.md ).

Kalite kapısının ( testler/test_kalite.py ) kuralları sıfır ister;  buradakiler
bugün her düzende vardır ve sınıf sınıf giderilecek.  Bu yüzden CIRCIR gibi
işler:  her düzenin her çiziminde her kuralın sayısı kayıttadır ( altın
düzenler:  testler/kalite_karnesi.json — test_kalite;  girdi taraması:
testler/tarama_karnesi.json — araclar/tarama ).  Sayı kayıttan BÜYÜKSE kapı
kırılır ( kötüleşme );  KÜÇÜKSE de kırılır ve kaydın yenilenmesini ister
( iyileşme kilitlenir, geri gelemez ).  Sıfıra inen kural kesin kural olur.

Ölçüm çizildiği gibidir ( pdf.ciz · svg · dxf aynı sıra ):  önce parçalar, sonra
ölçüler ÖĞE SIRASIYLA ( her biri çizgisi, uçları, maskesi ve yazısıyla ), en
son etiketler;  her yazının önce maskesi ( uslup.maske_kutusu ).  Ölçünün
yazısına binen ölçü çizgisi sıradan bağımsız sayılır ( geometri.
cizgiye_binen_yazilar ):  sonra çizilen yazının üstünden geçer, önce çizileni
yazının maskesi keser.

  maske_kenar_siliyor      yazının maskesi bir parça / duvar kenarını kâğıtta
                           MASKE_ESIGI'nden çok siliyor ( makine dairesinde
                           kumanda panosunun ön yüzü, kabin üstünde kabin duvarı )
  olcu_yaziyi_kesiyor      başka bir ölçünün çizgisi / ucu bir ölçü yazısının
                           harflerinden KESME_ESIGI'nden çok geçiyor ( kabin
                           üstünde "500"ün çizgisi kabin duvarının "15"inden;
                           kuyu dibinde "162,5" "615"in çizgisinde — maske onu
                           kesiyordu )
  olcu_ucu_yaziya_degiyor  aynısı, KESME_ESIGI'ne kadar:  üst sıranın kısa uzatma
                           çizgisi alttaki ölçü yazısının harflerine değiyor
  ok_yaziyi_kesiyor        etiket oku başka bir yazının harflerinden geçiyor
  yazi_cizgisinden_kopuk   ölçü yazısı kendi çizgisinden KOPUK yazı boyundan
                           uzak ( dar aralıkta yana kaçmış, başka zincirin
                           yanında okunuyor )
  halat_betonda            halat çizgisi kesilen betonun ( tarama ) içinden
                           kâğıtta HALAT_ESIGI'nden çok geçiyor ( delik yok )

    .venv/bin/python -m araclar.karne            altın düzenlerin karnesi ( özet )
    .venv/bin/python -m araclar.karne --yenile   altının kaydını yeniden yazar

--yenile DAVRANIŞI KABUL İZNİDİR ( altın çizim gibi ):  yalnız sayılar incelenip
iyileşme ( ya da onaylı bir değişiklik ) görüldükten sonra.
"""

import collections
import json
import os
import sys

from cizim import geometri
from testler import altin_cizim

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALTIN_KAYDI = os.path.join(KOK, "testler", "kalite_karnesi.json")
TARAMA_KAYDI = os.path.join(KOK, "testler", "tarama_karnesi.json")

#  Eşikler kâğıtta mm ( ölçekle çizim birimine çevrilir );  KOPUK yazı boyu
MASKE_ESIGI = 0.3
KESME_ESIGI = 0.5
HALAT_ESIGI = 0.5
KOPUK = 1.5
#  Okun ucu kendi yazısının bu kadar yakınındaysa o yazının okudur
OK_PAYI = 3.0
#  Harf gövdesi bu kadar içeriden denenir:  kenarına sürtünme sayılmaz
GOVDE_PAYI = 0.1

KURALLAR = {
    "maske_kenar_siliyor": "yazının maskesi parça / duvar kenarını siliyor",
    "olcu_yaziyi_kesiyor": "başka ölçünün çizgisi ölçü yazısını kesiyor",
    "olcu_ucu_yaziya_degiyor": "başka ölçünün ucu ölçü yazısına değiyor",
    "ok_yaziyi_kesiyor": "etiket oku başka bir yazıyı kesiyor",
    "yazi_cizgisinden_kopuk": "ölçü yazısı kendi çizgisinden kopuk",
    "halat_betonda": "halat betonun içinden geçiyor",
}


def _yazilar(e):
    """Etiketler ( çerçevenin başlığı hariç ) ve ölçü yazıları."""
    return [
        x
        for x in e
        if (x["tip"] == "yazi" and x.get("katman") != "CERCEVE") or (x["tip"] == "olcu" and x.get("yazi"))
    ]


def _icerden(kutu, pay):
    return (kutu[0] + pay, kutu[1] + pay, kutu[2] - pay, kutu[3] - pay)


def _maskeler(e, yazilar, olcek):
    """maske_kenar_siliyor:  [ ( metin , silinen boy — kâğıtta mm ) ]."""
    kenarlar = geometri.KenarIzgarasi(geometri.parca_kenarlari(e))
    out = []
    for x in yazilar:
        m = geometri.maske_kutusu(x)
        boy = sum(geometri.kutudaki_boy(s, m) for s in kenarlar.adaylar(m))
        if boy > MASKE_ESIGI * olcek:
            out.append((x["metin"], round(boy / olcek, 1)))
    return out


def _olcu_ustunde(e, olcek):
    """Başka bir ölçünün çizgisi ölçü yazısının harflerinde ( geometri.
    cizgiye_binen_yazilar — harf gövdesi GOVDE_PAYI içeriden ):  ( kesen ,
    değen ) — [ ( yazı , çizginin ölçüsünün yazısı ) ]."""
    kesen, degen = [], []
    for o, q, boy in geometri.cizgiye_binen_yazilar(e, olcek / 20.0, -GOVDE_PAYI * olcek):
        (kesen if boy > KESME_ESIGI * olcek else degen).append((o["metin"], q.get("metin")))
    return kesen, degen


def _oklar(e, yazilar, olcek):
    """ok_yaziyi_kesiyor:  [ metin ] — okun ucu ( iki ucundan biri ) kendi
    yazısına yakındır, o yazı sayılmaz."""
    oklar = [
        (x["x1"], x["y1"], x["x2"], x["y2"])
        for x in e
        if (x["tip"] == "ok" or (x["tip"] == "cizgi" and x.get("katman") == "YAZI"))
        and x.get("katman") in ("YAZI", "YUK")
        and x.get("ad") != "kuvvet_semasi"
    ]
    pay = OK_PAYI * olcek
    out = []
    for s in oklar:
        for x in yazilar:
            g = geometri.govde_kutusu(x)
            kendi = any(
                g[0] - pay <= px <= g[2] + pay and g[1] - pay <= py <= g[3] + pay
                for px, py in ((s[0], s[1]), (s[2], s[3]))
            )
            if not kendi and geometri.kutudaki_boy(s, _icerden(g, GOVDE_PAYI * olcek)) > 0.0:
                out.append(x["metin"])
    return out


def _kopuklar(e, olcek):
    """yazi_cizgisinden_kopuk:  [ ( metin , uzaklık — kâğıtta mm ) ]."""
    out = []
    for o in e:
        y = o.get("yazi") if o["tip"] == "olcu" else None
        if not y:
            continue
        dik = abs(y["y"] - o["kot"]) if o["yon"] == "yatay" else abs(y["x"] - o["kot"])
        if dik > KOPUK * y["h"]:
            out.append((o["metin"], round(dik / olcek, 1)))
    return out


def _halatlar(e, olcek):
    """halat_betonda:  [ betondaki boy — mm ]."""
    beton = [
        (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
        for x in e
        if x["tip"] == "tarama" and x.get("katman") == "TARAMA"
    ]
    out = []
    for x in e:
        if x["tip"] == "cizgi" and x.get("katman") == "HALAT":
            s = (x["x1"], x["y1"], x["x2"], x["y2"])
            boy = sum(geometri.kutudaki_boy(s, b) for b in beton)
            if boy > HALAT_ESIGI * olcek:
                out.append(round(boy))
    return out


def karne(e, olcek=20):
    """Çizimin ( elemanları e ) kusurları:  { kural : [ bulgu ] } — bütün kurallar."""
    yazilar = _yazilar(e)
    kesen, degen = _olcu_ustunde(e, olcek)
    return {
        "maske_kenar_siliyor": _maskeler(e, yazilar, olcek),
        "olcu_yaziyi_kesiyor": kesen,
        "olcu_ucu_yaziya_degiyor": degen,
        "ok_yaziyi_kesiyor": _oklar(e, yazilar, olcek),
        "yazi_cizgisinden_kopuk": _kopuklar(e, olcek),
        "halat_betonda": _halatlar(e, olcek),
    }


def sayilar(e, olcek=20):
    """{ kural : sayı } — yalnız sıfırdan büyükler."""
    return {k: len(v) for k, v in karne(e, olcek).items() if v}


def altin_karnesi():
    """Altın düzenlerin karnesi:  { düzen : { çizim : { kural : sayı } } } —
    çizimleri altın kayıttan ( testler/altin_cizim — bugünkü kodun çıktısı
    olduğunu test_altin_cizim denetler )."""
    out = {}
    for duzen, kayit in sorted(altin_cizim.oku().items()):
        c = {
            ad: s
            for ad, cizim in sorted((kayit.get("cizimler") or {}).items())
            if (s := sayilar(cizim["elemanlar"], cizim["olcek"]))
        }
        if c:
            out[duzen] = c
    return out


def oku(yol):
    if not os.path.exists(yol):
        return {}
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def yaz(yol, kayit):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def farklar(eski, yeni):
    """( kötüleşenler , iyileşenler ) — [ ileti ];  kayıtlar { düzen : { çizim :
    { kural : sayı } } }."""
    kotu, iyi = [], []
    for duzen in sorted(set(eski) | set(yeni)):
        e, y = eski.get(duzen, {}), yeni.get(duzen, {})
        for ad in sorted(set(e) | set(y)):
            ec, yc = e.get(ad, {}), y.get(ad, {})
            for kural in sorted(set(ec) | set(yc)):
                a, b = ec.get(kural, 0), yc.get(kural, 0)
                if a != b:
                    ileti = f"{duzen} · {ad} · {KURALLAR.get(kural, kural)}:  {a} → {b}"
                    (kotu if b > a else iyi).append(ileti)
    return kotu, iyi


def toplamlar(kayit):
    """{ kural : ( bulgu , düzen ) } — kaydın özeti."""
    bulgu, duzen = collections.Counter(), collections.Counter()
    for c in kayit.values():
        gorulen = set()
        for s in c.values():
            for kural, n in s.items():
                bulgu[kural] += n
                gorulen.add(kural)
        for kural in gorulen:
            duzen[kural] += 1
    return {k: (bulgu[k], duzen[k]) for k in KURALLAR if bulgu[k]}


def main(argv):
    yeni = altin_karnesi()
    if "--yenile" in argv:
        yaz(ALTIN_KAYDI, yeni)
        print(f"karne kaydı yazıldı:  {os.path.relpath(ALTIN_KAYDI, KOK)}")
    else:
        kotu, iyi = farklar(oku(ALTIN_KAYDI), yeni)
        for i in kotu:
            print("KÖTÜLEŞTİ  " + i)
        for i in iyi:
            print("İYİLEŞTİ   " + i)
    for kural, (n, d) in toplamlar(yeni).items():
        print(f"{KURALLAR[kural]:48s} {n:5d} bulgu  ·  {d} düzen")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
