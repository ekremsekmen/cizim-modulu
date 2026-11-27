# -*- coding: utf-8 -*-
"""ÇARE TARAMASI — çare bulucu ( hesap/uclar/care_uclari ) girdi taramasının sorunlu düzenlerinde.

27 Kas ( seçici doğruluk planı, cikti/devir/SECICI_DOGRULUK_PLANI.md — Adım 1 ):  30 Eki'deki elle
koşulan taramanın kalıcısı.  Girdi taramasının düzenleri ( araclar/tarama.duzenler — ana · kapi ·
diger · oda ) çizim sorunu verenleri için çare bulucu koşar;  her öneri BAĞIMSIZ uygulanıp
yeniden sınanır.

  GÜVENCELER ( bozulursa tarama BAŞARISIZ — çare bulucunun sözü:  "hiçbir aday tahminle
  gösterilmez" ):
    · öneri, gidereceğini söylediği sorunu gerçekten giderir;
    · öneri, söylediklerinin ( ortaya çıkan ) dışında yeni çizim sorunu doğurmaz;
    · öneri hesabı durdurmaz;
    · çare bulucu çökmez.

  ÖLÇÜLEN ( rapor ):  sorunlu düzen, sorun, ÇARESİZ sorun ( önerisi olmayan ) ve kimlikleri,
  öneri, yöntemler, bütçeye takılan arama.  30 Eki:  277 reddedilen düzende çaresiz 108 → 90 ( #80 ).

Bütçe sınama sayısıdır:  güvenlik süresi kapalı ( sonuç makinenin hızına bağlı kalmaz ).

    .venv/bin/python -m araclar.care_tarama              hepsi ( KONTROL_IS işçi, varsayılan 2 )
    .venv/bin/python -m araclar.care_tarama --dilim 20   her 20 düzenden biri ( deneme )

AĞIR İŞTİR:  yerelde dilimle denenir, tamamı PR'ın CI'ında koşar.
"""

import collections
import json
import multiprocessing
import os
import sys
import time
import traceback

import yollar

yollar.kur()

from araclar import tarama
from uclar import care_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "cikti", "care_tarama")
#  Tek kuyu grubu ( iki asansör ) dışında:  çare bulucu tek asansöre bakar
GRUPLAR = ("ana", "kapi", "diger", "oda")


def isler():
    """[ ( ad , formun isteği ) ] — sırası sabittir."""
    return [(f"{grup}|{ad}", v) for grup in GRUPLAR for ad, v in tarama.duzenler(grup)]


def _kimlikler(metinler):
    return {care_uclari.kimlik(x) for x in metinler}


def dene(is_):
    """Bir düzen → { ad , sorun , caresiz , oneri , yontem , ihlal , tamamlandi , sure }."""
    ad, v = is_
    t0 = time.monotonic()
    try:
        once = care_uclari.girdi_durumu(v, 0)
        if not once[0]:
            return {"ad": ad, "sorun": [], "sure": round(time.monotonic() - t0, 1)}
        c = care_uclari.coz(v, 0, None, care_uclari.Butce(sure=float("inf")))
        ihlal, yontem, oneri = [], collections.Counter(), 0
        for cc in c["careler"]:
            for o in cc["oneriler"]:
                oneri += 1
                yontem[o["yontem"]] += 1
                d = care_uclari.girdi_durumu(care_uclari.girdi_yaz(v, 0, o["anahtar"], o["yeni"]), 0)
                adi = f"{o['anahtar']} → {o['yeni']}"
                kalan = set(d[0])
                if _kimlikler(o["gider"]) & kalan:
                    ihlal.append(f"{adi}:  gidereceği sorun kaldı")
                yeni = kalan - set(once[0]) - _kimlikler(o["ortaya_cikan"])
                if yeni:
                    ihlal.append(f"{adi}:  yeni sorun {sorted(yeni)[:2]}")
                if once[1] and not d[1]:
                    ihlal.append(f"{adi}:  hesap durdu")
        return {
            "ad": ad,
            "sorun": sorted(once[0]),
            "caresiz": sorted(care_uclari.kimlik(cc["metin"]) for cc in c["careler"] if not cc["oneriler"]),
            "oneri": oneri,
            "yontem": dict(yontem),
            "ihlal": ihlal,
            "tamamlandi": c["tamamlandi"],
            "sinama": c["sinama"],
            "sure": round(time.monotonic() - t0, 1),
        }
    except Exception:  # noqa: BLE001 — çökme de bulgudur
        return {"ad": ad, "ihlal": ["ÇÖKME:  " + traceback.format_exc(limit=4).strip().splitlines()[-1]]}


def _isci_sayisi():
    x = os.environ.get("KONTROL_IS", "2")
    return (os.cpu_count() or 2) if x == "auto" else max(1, int(x))


def main(argv):
    dilim = int(argv[argv.index("--dilim") + 1]) if "--dilim" in argv else 1
    hepsi = isler()
    secilen = hepsi[::dilim]
    n = _isci_sayisi()
    print(f"çare taraması:  {len(secilen)} / {len(hepsi)} düzen, {n} işçi", flush=True)
    t0 = time.monotonic()
    sonuclar = []
    with multiprocessing.Pool(n) as havuz:
        for i, s in enumerate(havuz.imap(dene, secilen), 1):
            sonuclar.append(s)
            for x in s.get("ihlal") or []:
                print(f"  İHLAL  {s['ad']}:  {x}", flush=True)
            if i % 50 == 0:
                print(f"  {i} / {len(secilen)}  ·  {(time.monotonic() - t0) / 60:.1f} dk", flush=True)
    os.makedirs(CIKTI, exist_ok=True)
    with open(os.path.join(CIKTI, "sonuc.json"), "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, ensure_ascii=False, indent=1)

    sorunlu = [s for s in sonuclar if s.get("sorun")]
    caresiz = collections.Counter(k for s in sorunlu for k in s.get("caresiz") or [])
    yontem = collections.Counter()
    for s in sorunlu:
        yontem.update(s.get("yontem") or {})
    print(
        f"\nsorunlu düzen {len(sorunlu)}  ·  sorun {sum(len(s['sorun']) for s in sorunlu)}  ·  "
        f"çaresiz sorun {sum(caresiz.values())}  ·  öneri {sum(s.get('oneri', 0) for s in sorunlu)}  ·  "
        f"bütçeye takılan {sum(1 for s in sorunlu if s.get('tamamlandi') is False)}"
    )
    print("öneri yöntemleri:  " + "  ·  ".join(f"{k} {v}" for k, v in sorted(yontem.items())))
    print("en sık çaresiz sorunlar:")
    for k, v in caresiz.most_common(15):
        print(f"  {v:4d}  {k[:110]}")
    sureler = sorted(s.get("sure", 0) for s in sonuclar)
    print(
        f"süre:  toplam {sum(sureler) / 60:.1f} dk işlemci, en uzun {sureler[-1] if sureler else 0} sn  ·  "
        f"duvar saati {(time.monotonic() - t0) / 60:.1f} dk  —  ayrıntı "
        f"{os.path.relpath(os.path.join(CIKTI, 'sonuc.json'), KOK)}"
    )
    ihlalli = [s for s in sonuclar if s.get("ihlal")]
    print(
        "\nÇARE TARAMASI "
        + ("GEÇTİ" if not ihlalli else f"BAŞARISIZ:  {len(ihlalli)} düzende güvence bozuldu")
    )
    return 0 if not ihlalli else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
