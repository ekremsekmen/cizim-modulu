# -*- coding: utf-8 -*-
"""AVAN SEÇİCİSİ TARAMASI — mimarın kuyuları seçiciden ( hesap/uclar/avan_secici ) geçer.

Seçici avan projesine "bu kuyuya en uygun asansör"ü bulur;  testleri ( testler/
test_avan_secici ) birkaç kuyuya bakar.  Tarama eksenleri geniş tutar:

    kuyu   her hazır asansör × kuyu genişliği / derinliği ( paketinkinden küçük ve
           büyük ) × kat düzeni ( durak, hız, kuyu dibi, kuyu üstü )
    kapi   trafik hesabının kapısı ( aile × genişlik )
    hiz    avanın hızları ( paketin kendi kuyusu )
    aski   kartın askı oranı ( 1:1 · 2:1 )
    oda    makine daireli:  mimarın makine dairesi ( paketinkinden küçük )

Her senaryoda iki tür denetim:

  DEĞİŞMEZLER ( bozulursa tarama BAŞARISIZ ):
    · seçici çökmez, bilinen bir durum döner;
    · "uygun" / "gereken" isteği uygulamanın KENDİ uçlarından ( seçicinin sınamasına
      güvenilmez ) temiz çıkar:  hesap çalışır, düşen bölümler seçicinin söyledikleridir
      ve avanı bağlayan bölüm düşmez, çizim sorunsuzdur;
    · kabin hazır asansörünkidir;  hız ve avanın beyanı ( askı, kapı ) istekte aynen durur;
      "uygun"da mimarın ölçüleri de aynen durur.

  HÜKÜMLER ( testler/avan_tarama_hukumleri.json — değişirse tarama BAŞARISIZ ):
    durum, karşı ağırlığın yeri, mimardan istenen ölçüler, kartta istenen seçimler ve
    istenen ölçülerle yeniden seçimin durumu.  Kayıt yoksa karşılaştırma atlanır,
    sonuç cikti/avan_tarama/hukumler.json'a yazılır ( ilk kayıt oradan alınır ).

Seçici SAATSİZ kipte koşar ( avan_secici.SAATSIZ ):  süre sınırı uygulanmaz, hüküm
makinenin hızına bağlı kalmaz.

    .venv/bin/python -m araclar.avan_tarama              hepsi ( KONTROL_IS işçi, varsayılan 2 )
    .venv/bin/python -m araclar.avan_tarama --dilim 40   her 40 senaryodan biri ( deneme )
    .venv/bin/python -m araclar.avan_tarama --yenile     hüküm kaydını yeniden yazar

--yenile DAVRANIŞI DEĞİŞTİRME İZNİDİR ( altın çıktılar gibi ):  hüküm değişiklikleri tek
tek incelenip onaylandıktan sonra.  AĞIR İŞTİR:  yerelde koşulmaz, PR'ın CI'ında koşar.
"""

import collections
import copy
import json
import multiprocessing
import os
import sys
import time
import traceback

import yollar

yollar.kur()

from cizim import katlar
from uclar import avan_secici
from uclar import cizim_uclari
from uclar import uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "cikti", "avan_tarama")
HUKUMLER = os.path.join(KOK, "testler", "avan_tarama_hukumleri.json")
DURUMLAR = ("uygun", "gereken", "sigmaz", "beyan")

#  Kuyu ekseni:  paketin kuyusuna göre fark ( mm )
GENISLIK = (-200, 0, 100, 300, 600)
DERINLIK = (-100, 0, 300)
#  ( durak , kat yüksekliği mm , hız , kuyu dibi mm , kuyu üstü mm — son durak → tavan )
KATLAR = ((6, 3000, 1.0, 1600, 4200), (10, 2900, 1.6, 1800, 4600))
KAPILAR = tuple(
    (tip, gen) for tip in ("Otomatik Merkezi", "Teleskopik Sol") for gen in (800, 900, 1000, 1100)
)
HIZLAR = (0.63, 1.6, 2, 2.5)
ASKILAR = (1, 2)
#  Makine dairesi ( uzunluk , genişlik ):  yeten, yetmeyen, kuyudan küçük
ODALAR = ((3000, 2500), (2200, 2200), (1000, 1000))
KABIN = ("beyan_yuku", "kabin_genisligi", "kabin_derinligi")


def _paket_mimarisi(t, **degisen):
    """Hazır asansörün kendi kuyusu ve kotları, mimarın vereceği biçimde.  Makine dairesinin
    ölçüsü verilmez ( hazır asansörünki kullanılır ) — "oda" ekseni dışında."""
    a = t["asansor"]
    m = {k: a[k] for k in ("beyan_yuku", "beyan_hizi", *avan_secici.MIMARI) if k in a}
    m["mk_yok"] = t["proje_geneli"].get("mk_yok") == "true"
    m.update(degisen)
    return m


def _katli(t, dg, dd, kat):
    """Paketin kuyusundan dg / dd farklı kuyu, verilen kat düzeniyle."""
    n, h, hiz, dip, ust = kat
    a = t["asansor"]
    son = (n - 1) * h
    m = {
        "beyan_yuku": a["beyan_yuku"],
        "beyan_hizi": hiz,
        "kuyu_genisligi": int(a["kuyu_genisligi"]) + dg,
        "kuyu_derinligi": int(a["kuyu_derinligi"]) + dd,
        "durak_kotlari": "; ".join(katlar.kot_metni(j * h) for j in range(n)),
        "kuyu_dibi_kotu": katlar.kot_metni(-dip),
        "kuyu_tavani_kotu": katlar.kot_metni(son + ust),
        "mk_yok": t["proje_geneli"].get("mk_yok") == "true",
    }
    if not m["mk_yok"]:
        #  hazır asansördeki gibi:  makine dairesi zemini tavanın 1050 altında ( tabliye )
        m["md_zemini_kotu"] = katlar.kot_metni(son + ust - 1050)
    return m


def senaryolar():
    """[ ( kimlik , paketin anahtarı , mimari ) ] — sırası sabittir."""
    liste = []
    for anahtar, t in avan_secici.paketler().items():
        ad = t["kimlik"]
        for dg in GENISLIK:
            for dd in DERINLIK:
                for i, kat in enumerate(KATLAR):
                    liste.append((f"kuyu|{ad}|g{dg:+d}|d{dd:+d}|k{i}", anahtar, _katli(t, dg, dd, kat)))
        for tip, gen in KAPILAR:
            m = _paket_mimarisi(t, kat_kapisi_tipi=tip, kapi_genisligi=gen)
            liste.append((f"kapi|{ad}|{tip}|{gen}", anahtar, m))
        for hiz in HIZLAR:
            liste.append((f"hiz|{ad}|{hiz:g}", anahtar, _paket_mimarisi(t, beyan_hizi=hiz)))
        for aski in ASKILAR:
            liste.append((f"aski|{ad}|{aski}", anahtar, _paket_mimarisi(t, aski_orani=aski)))
        if not anahtar[1]:
            for uzunluk, genislik in ODALAR:
                m = _paket_mimarisi(t, mk_uzunluk=uzunluk, mk_genislik=genislik)
                liste.append((f"oda|{ad}|{uzunluk}x{genislik}", anahtar, m))
    return liste


def _metin(x):
    """Mimarın değeri, isteğe yazıldığı gibi ( avan_secici'nin yazımı )."""
    if isinstance(x, bool):
        return "true" if x else "false"
    return x if isinstance(x, str) else f"{x:g}"


def _ihlaller(r, m, t):
    """Değişmezlerin bozulanları ( metin listesi ) — "uygun" / "gereken" sonucu için."""
    s = []
    v = r["istek"]
    a = {**v["proje_geneli"], **v["asansorler"][0]}
    for k in KABIN:
        if a.get(k) != t["asansor"].get(k):
            s.append(f"kabin {k}:  {a.get(k)} ≠ {t['asansor'].get(k)}")
    for k in ("beyan_hizi", *avan_secici.BEYAN):
        if m.get(k) not in (None, "") and a.get(k) != _metin(m[k]):
            s.append(f"beyan {k}:  {a.get(k)} ≠ {m[k]}")
    if r["durum"] == "uygun":
        for k in (*avan_secici.MIMARI, *avan_secici.MIMARI_GENEL):
            if m.get(k) not in (None, "") and a.get(k) != _metin(m[k]):
                s.append(f"mimari {k}:  {a.get(k)} ≠ {m[k]}")
    h = json.loads(uygulama_uclari.api_uygulama_coklu(copy.deepcopy(v)).body)
    if not h.get("aktif"):
        s.append(f"hesap çalışmadı:  {h.get('hata')}")
    else:
        dusen = sorted(
            b["kimlik"]
            for b in h["asansorler"][0]["bolumler"]
            if (b.get("sonuc") or {}).get("uygun") is False
        )
        if dusen != r["acik_bolumler"]:
            s.append(f"düşen bölümler {dusen} ≠ seçicinin söylediği {r['acik_bolumler']}")
        if set(dusen) & avan_secici.AVAN_BOLUMLERI:
            s.append(f"avanı bağlayan bölüm düştü:  {dusen}")
    c = json.loads(cizim_uclari.api_cizimler(copy.deepcopy(v)).body)
    if not c.get("aktif") or c.get("hata"):
        s.append(f"çizim:  {c.get('hata')}")
    return s


def _yeniden(m, gereken):
    """Mimardan istenen ölçüler verilince seçicinin durumu ( "uygun" beklenir )."""
    m2 = dict(m)
    for g in gereken:
        yeni = g["yeni"]
        m2[g["anahtar"]] = yeni if isinstance(yeni, str) else int(round(yeni))
    return avan_secici.sec(m2)["durum"]


def _kur():
    avan_secici.SAATSIZ = True


def dene(senaryo):
    """Bir senaryo → { kimlik , hukum , ihlal , sure } ( işçi süreçte koşar )."""
    kimlik, anahtar, m = senaryo
    t0 = time.monotonic()
    t = avan_secici.paketler()[anahtar]
    try:
        r = avan_secici.sec(m)
        durum = r["durum"]
        ihlal = [] if durum in DURUMLAR else [f"beklenmeyen durum:  {durum}"]
        hukum = {"durum": durum}
        if durum in ("uygun", "gereken"):
            ihlal += _ihlaller(r, m, t)
            hukum["agirlik"] = r["istek"]["asansorler"][0].get("agirlik_yeri")
        if durum == "gereken":
            hukum["gereken"] = [[g["anahtar"], g["yeni"]] for g in r["gereken"]]
            hukum["yeniden"] = _yeniden(m, r["gereken"])
        if durum == "beyan":
            hukum["beyan"] = [[b["anahtar"], b["yeni"]] for b in r["beyan"]]
        if durum == "sigmaz" and not r.get("nedenler"):
            ihlal.append("sığmaz ama sebep yok")
    except Exception:  # noqa: BLE001 — çökme de bulgudur
        hukum, ihlal = {"durum": "ÇÖKME"}, [traceback.format_exc(limit=4).strip().splitlines()[-1]]
    return {"kimlik": kimlik, "hukum": hukum, "ihlal": ihlal, "sure": round(time.monotonic() - t0, 1)}


def _isci_sayisi():
    """KONTROL_IS ( kontrol.py'ninki ):  "auto" işlemci sayısı, sayı o kadar;  yoksa 2
    ( bilgisayarı doldurmasın — ağır iş yerelde koşulmaz )."""
    x = os.environ.get("KONTROL_IS", "2")
    return (os.cpu_count() or 2) if x == "auto" else max(1, int(x))


def main(argv):
    yenile = "--yenile" in argv
    dilim = int(argv[argv.index("--dilim") + 1]) if "--dilim" in argv else 1
    hepsi = senaryolar()
    secilen = hepsi[::dilim]
    n = _isci_sayisi()
    print(f"avan seçicisi taraması:  {len(secilen)} / {len(hepsi)} senaryo, {n} işçi", flush=True)
    t0 = time.monotonic()
    sonuclar = []
    with multiprocessing.Pool(n, initializer=_kur) as havuz:
        for i, s in enumerate(havuz.imap(dene, secilen), 1):
            sonuclar.append(s)
            if s["ihlal"]:
                print(f"  İHLAL  {s['kimlik']}:  {' · '.join(s['ihlal'])}", flush=True)
            if i % 25 == 0:
                print(f"  {i} / {len(secilen)}  ·  {(time.monotonic() - t0) / 60:.1f} dk", flush=True)

    hukumler = {s["kimlik"]: s["hukum"] for s in sonuclar}
    os.makedirs(CIKTI, exist_ok=True)
    with open(os.path.join(CIKTI, "sonuc.json"), "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, ensure_ascii=False, indent=1)
    with open(os.path.join(CIKTI, "hukumler.json"), "w", encoding="utf-8") as f:
        json.dump(hukumler, f, ensure_ascii=False, indent=1, sort_keys=True)

    sayim = collections.Counter(s["hukum"]["durum"] for s in sonuclar)
    sureler = sorted(s["sure"] for s in sonuclar)
    print("\ndurumlar:  " + "  ·  ".join(f"{k} {v}" for k, v in sorted(sayim.items())))
    tutmayan = [s["kimlik"] for s in sonuclar if s["hukum"].get("yeniden") not in (None, "uygun")]
    print(f'istenen ölçüyle yeniden seçim "uygun" değil:  {len(tutmayan)}')
    print(
        f"süre:  toplam {sum(sureler) / 60:.1f} dk işlemci, ortanca {sureler[len(sureler) // 2]} sn, "
        f"en uzun {sureler[-1]} sn  ·  duvar saati {(time.monotonic() - t0) / 60:.1f} dk"
    )

    ihlalli = [s for s in sonuclar if s["ihlal"]]
    tamam = not ihlalli
    if ihlalli:
        print(f"\nDEĞİŞMEZ BOZULDU:  {len(ihlalli)} senaryo ( yukarıda )")

    if yenile:
        if dilim != 1:
            print("\n--yenile yalnız tam taramayla ( --dilim olmadan ).")
            return 2
        with open(HUKUMLER, "w", encoding="utf-8") as f:
            json.dump(hukumler, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        print(f"\nhüküm kaydı yenilendi:  {os.path.relpath(HUKUMLER, KOK)}")
    elif not os.path.exists(HUKUMLER):
        print("\nhüküm kaydı yok — karşılaştırma atlandı;  sonuç cikti/avan_tarama/hukumler.json'da.")
    else:
        with open(HUKUMLER, encoding="utf-8") as f:
            kayit = json.load(f)
        farklar = [
            f"  {k}:  {json.dumps(kayit.get(k), ensure_ascii=False)}  →  {json.dumps(h, ensure_ascii=False)}"
            for k, h in hukumler.items()
            if kayit.get(k) != h
        ]
        if dilim == 1:
            farklar += [f"  {k}:  kayıtta var, taramada yok" for k in kayit if k not in hukumler]
        if farklar:
            tamam = False
            print(f"\nHÜKÜM DEĞİŞTİ:  {len(farklar)} senaryo ( kayıt → şimdi )")
            print("\n".join(farklar[:60]))
            if len(farklar) > 60:
                print(f"  … {len(farklar) - 60} tane daha ( cikti/avan_tarama/hukumler.json )")
            print("Değişiklik bilerek yapıldıysa incelenip --yenile ile kayıt yenilenir.")
        else:
            print("\nhükümler kayıtla aynı.")
    print("\nTARAMA " + ("GEÇTİ" if tamam else "BAŞARISIZ"))
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
