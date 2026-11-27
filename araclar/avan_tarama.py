# -*- coding: utf-8 -*-
"""AVAN SEÇİCİSİ TARAMASI — mimarın kuyuları seçiciden ( hesap/uclar/avan_secici ) geçer.

Seçici avan projesine "bu kuyuya en uygun asansör"ü bulur;  testleri ( testler/
test_avan_secici ) birkaç kuyuya bakar.  Tarama eksenleri geniş tutar:

    kuyu   her hazır asansör × kuyu genişliği / derinliği ( paketinkinden küçük ve
           büyük ) × kat düzeni ( durak, hız, kuyu dibi, kuyu üstü );  yalnız avanın hazır
           asansörleri ( 450 · 1600 · 2000 · 2500 kg ) seyrek taranır ( SEYREK_* )
    kapi   trafik hesabının kapısı ( aile × genişlik )
    hiz    avanın hızları ( paketin kendi kuyusu )
    aski   kartın askı oranı ( 1:1 · 2:1 )
    oda    makine daireli:  mimarın makine dairesi ( paketinkinden küçük )
    kabin  kartın kabini ( 24 Kas ):  hazır asansörünkinden KABIN_DARALMA dar, alanını koruyacak
           kadar derin ( standarda uyan — avan_secici.kabin_nedenleri ), kuyu da kabin farkı kadar

Her senaryoda iki tür denetim:

  DEĞİŞMEZLER ( bozulursa tarama BAŞARISIZ ):
    · seçici çökmez, bilinen bir durum döner;
    · "uygun" / "gereken" isteği uygulamanın KENDİ uçlarından ( seçicinin sınamasına
      güvenilmez ) temiz çıkar:  hesap çalışır, düşen bölümler seçicinin söyledikleridir
      ve avanı bağlayan bölüm düşmez, çizim sorunsuzdur;
    · kabin kartınkidir ( verilmişse ), değilse hazır asansörünki;  hız ve avanın beyanı ( askı,
      kapı ) istekte aynen durur;  "uygun"da mimarın ölçüleri de aynen durur.

  HÜKÜMLER ( testler/avan_tarama_hukumleri.json — değişirse tarama BAŞARISIZ ):
    durum, karşı ağırlığın yeri, mimardan istenen ölçüler, kartta istenen seçimler ve
    istenen ölçülerle yeniden seçimin durumu.  Kayıt yoksa karşılaştırma atlanır,
    sonuç cikti/avan_tarama/hukumler.json'a yazılır ( ilk kayıt oradan alınır ).

Seçicinin bütçesi sınama sayısıdır, saat değil ( 16 Kas ):  hüküm makinenin hızına bağlı
kalmaz, program da aynı hükmü verir.  Tarama seçiciyi korumasız çağırır ( avan_secici.sec —
güvenlik süresi, iptal ve önbellek yalnız sunucunun korumali bağlamında );  SAATSIZ ayrıca
güvenlik süresini kapatır.

    .venv/bin/python -m araclar.avan_tarama              hepsi ( KONTROL_IS işçi, varsayılan 2 )
    .venv/bin/python -m araclar.avan_tarama --dilim 40   her 40 senaryodan biri ( deneme )
    .venv/bin/python -m araclar.avan_tarama --parca 1/2  senaryoların birinci yarısı ( biri atlanarak —
                                                         CI iki işte yan yana koşar )
    .venv/bin/python -m araclar.avan_tarama --yenile     hüküm kaydını yeniden yazar

DAR EKSEN ( --eksen dar;  27 Kas — seçici doğruluk planı, cikti/devir/SECICI_DOGRULUK_PLANI.md ):
hazır asansörün kuyusundan çok dar ve derin kuyular ( karşı ağırlık arkaya zorlanır ) ve kullanıcının
gerçek vakası;  kendi hüküm kaydı ( testler/avan_tarama_dar_hukumleri.json ).  Bu eksende ayrıca
GÜVENCELER ölçülür ( şimdilik RAPOR — taramayı başarısız saymaz ):

    G2  bir adım eksiği kurulmaz:  "gereken"de istenen her ölçü bir adım ( 10 mm, kot 0,01 m )
        mimarınkine doğru geri alınınca seçici "uygun" demez;
    G3  fazla yer zarar vermez:  "uygun"da kuyu 100 mm geniş / derin olunca yine "uygun";
    G4  sığmaz yalnız gerçek imkânsızlıkta:  G3'ün büyütmesi "sığmaz" çıkmaz.

    .venv/bin/python -m araclar.avan_tarama --eksen dar

--yenile DAVRANIŞI DEĞİŞTİRME İZNİDİR ( altın çıktılar gibi ):  hüküm değişiklikleri tek
tek incelenip onaylandıktan sonra.  AĞIR İŞTİR:  yerelde koşulmaz, PR'ın CI'ında koşar.
"""

import collections
import copy
import json
import math
import multiprocessing
import os
import sys
import time
import traceback

import yollar

yollar.kur()

from cizim import katlar
from motor.avan import tablolar
from uclar import avan_secici
from uclar import cizim_uclari
from uclar import uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "cikti", "avan_tarama")
HUKUMLER = os.path.join(KOK, "testler", "avan_tarama_hukumleri.json")
#  Eksenin hüküm kaydı ve çıktı klasörü ( dar eksen ayrı:  temel kaydı ve CI işleri değişmez )
EKSEN_HUKUMLERI = {"temel": HUKUMLER, "dar": os.path.join(KOK, "testler", "avan_tarama_dar_hukumleri.json")}
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
#  Kartın kabini ( "kabin" ekseni ):  hazır asansörünkinden bu kadar dar ( mm ), derinliği alanı
#  koruyacak kadar ( 50 mm'ye yukarı ) — dar kuyuya standarda uyan kabin
KABIN_DARALMA = 100
#  YALNIZ AVANIN HAZIR ASANSÖRLERİ ( uclar/avan_paketleri.json — 450 · 1600 · 2000 · 2500 kg )
#  seyrek taranır:  hepsi tam eksenle 819 senaryo CI'da 80 dk sürdü ( 14 Kas, PR #134 — büyük
#  asansörlerin senaryoları yavaş ).  Küçük / geniş kuyu, iki kapı, iki hız;  askı ve oda tam.
SEYREK_GENISLIK = (-200, 0, 300)
SEYREK_DERINLIK = (-100, 300)
SEYREK_KATLAR = KATLAR[:1]
SEYREK_KAPILAR = (("Otomatik Merkezi", 900), ("Teleskopik Sol", 1000))
SEYREK_HIZLAR = (0.63, 1.6)


#  DAR EKSEN ( 27 Kas taraması, cikti/arastirma/caresiz_27kas ):  hazır asansörün kuyusuna göre fark
#  ( genişlik , derinlik , kapı genişliği farkı ) — 1. tur hafif dar, 2. tur kullanıcının kuyusu
#  kadar dar ( 800 kg:  2300 × 1850 → 1800 × 2700 )
DAR_KUYULAR = tuple((dg, 500, dk) for dg in (-150, -250) for dk in (0, 100)) + tuple(
    (dg, dd, 0) for dg in (-400, -500) for dd in (500, 850)
)
#  Makine daireli 2. turda mimarın verdiği oda ( hazır asansörünki ):  kuyu derinleşince aynı oda
#  kuyuya göre kısa kalır ( 1000-md 1650 × 3400 "sığmaz" — S3 )
DAR_ODALI = tuple((dg, 850, 0) for dg in (-400, -500))
#  KULLANICININ VAKASI ( 24 – 27 Kas ):  800 kg MRL, 1800 × 2700, durak −2,60 … +24,70 ( 10 ),
#  kuyu dibi −4,70;  ( kapı , son kat )
VAKA_KOTLARI = "; ".join(["-2,60"] + [katlar.kot_metni(700 + 3000 * i) for i in range(9)])
VAKALAR = tuple((kapi, son) for kapi in (800, 900) for son in (4050, 4300))
#  Güvencelerin adımı ( G2 ) ve büyütmesi ( G3 )
GERI_ADIM = 10
BUYUTME = 100


def _dar_kuyu(a, dg, dd):
    """Hazır asansörün ( a ) kuyusundan dg / dd farklı kuyu."""
    return {"kuyu_genisligi": int(a["kuyu_genisligi"]) + dg, "kuyu_derinligi": int(a["kuyu_derinligi"]) + dd}


def dar_senaryolari():
    """Dar eksen:  [ ( kimlik , paketin anahtarı , mimari ) ] — sırası sabittir.  Yalnız
    açılışın hazır asansörleri ( yalnız-avan olanlar 27 Kas taramasında yoktu )."""
    liste = []
    for anahtar, t in avan_secici.paketler().items():
        if "acik_bolumler" in t:
            continue
        a, ad = t["asansor"], t["kimlik"]
        for dg, dd, dk in DAR_KUYULAR:
            m = _paket_mimarisi(t, **_dar_kuyu(a, dg, dd), kapi_genisligi=int(a["kapi_genisligi"]) + dk)
            liste.append((f"dar|{ad}|g{dg:+d}|d{dd:+d}|k{dk:+d}", anahtar, m))
        if not anahtar[1]:
            pg = t["proje_geneli"]
            for dg, dd, _dk in DAR_ODALI:
                m = _paket_mimarisi(
                    t, **_dar_kuyu(a, dg, dd), mk_uzunluk=pg["mk_uzunluk"], mk_genislik=pg["mk_genislik"]
                )
                liste.append((f"dar|{ad}|g{dg:+d}|d{dd:+d}|oda", anahtar, m))
    t = avan_secici.paketler()[(800, True)]
    for kapi, son in VAKALAR:
        m = _paket_mimarisi(
            t,
            kuyu_genisligi=1800,
            kuyu_derinligi=2700,
            durak_kotlari=VAKA_KOTLARI,
            kuyu_dibi_kotu="-4,70",
            kuyu_tavani_kotu=katlar.kot_metni(24700 + son),
            kisi=10,
            kapi_genisligi=kapi,
        )
        liste.append((f"vaka|800|k{kapi}|s{son}", (800, True), m))
    return liste


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
        seyrek = "acik_bolumler" in t
        for dg in SEYREK_GENISLIK if seyrek else GENISLIK:
            for dd in SEYREK_DERINLIK if seyrek else DERINLIK:
                for i, kat in enumerate(SEYREK_KATLAR if seyrek else KATLAR):
                    liste.append((f"kuyu|{ad}|g{dg:+d}|d{dd:+d}|k{i}", anahtar, _katli(t, dg, dd, kat)))
        for tip, gen in SEYREK_KAPILAR if seyrek else KAPILAR:
            m = _paket_mimarisi(t, kat_kapisi_tipi=tip, kapi_genisligi=gen)
            liste.append((f"kapi|{ad}|{tip}|{gen}", anahtar, m))
        for hiz in SEYREK_HIZLAR if seyrek else HIZLAR:
            liste.append((f"hiz|{ad}|{hiz:g}", anahtar, _paket_mimarisi(t, beyan_hizi=hiz)))
        for aski in ASKILAR:
            liste.append((f"aski|{ad}|{aski}", anahtar, _paket_mimarisi(t, aski_orani=aski)))
        if not anahtar[1]:
            for uzunluk, genislik in ODALAR:
                m = _paket_mimarisi(t, mk_uzunluk=uzunluk, mk_genislik=genislik)
                liste.append((f"oda|{ad}|{uzunluk}x{genislik}", anahtar, m))
        liste.append((f"kabin|{ad}", anahtar, _kartin_kabiniyle(t)))
    return liste


def _kartin_kabiniyle(t):
    """ "kabin" ekseni ( 24 Kas ):  kartta hazır asansörünkinden KABIN_DARALMA dar, alanını koruyacak
    kadar derin kabin;  kuyu da kabin farkı kadar ( kabin çevresindeki aralıklar paketteki gibi ) —
    seçici o kabinle arar.  Kişi trafiğinki ( Tablo-7 ) — kabin taşımalı;  kabin standarda uyar."""
    a = t["asansor"]
    gen, der = int(a["kabin_genisligi"]), int(a["kabin_derinligi"])
    g = gen - KABIN_DARALMA
    d = math.ceil(gen * der / g / 50) * 50
    yuk = int(a["beyan_yuku"])
    m = _paket_mimarisi(
        t,
        kabin_genisligi=g,
        kabin_derinligi=d,
        kuyu_genisligi=int(a["kuyu_genisligi"]) - KABIN_DARALMA,
        kuyu_derinligi=int(a["kuyu_derinligi"]) + d - der,
    )
    kisi = next((p for p, q in tablolar.TABLO_7.items() if q == yuk), None)
    if kisi is not None:
        m["kisi"] = kisi
    if avan_secici.kabin_nedenleri(t, m):
        raise ValueError(f"kabin ekseni:  {t['kimlik']} kabini standarda uymuyor — {m}")
    return m


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
    if a.get("beyan_yuku") != t["asansor"].get("beyan_yuku"):
        s.append(f"yük:  {a.get('beyan_yuku')} ≠ {t['asansor'].get('beyan_yuku')}")
    #  Kabin kartınki ( verilmişse ), değilse hazır asansörünki
    kabin = avan_secici.kabin(t, m)
    for k in avan_secici.KABIN:
        if a.get(k) != _metin(kabin[k]):
            s.append(f"kabin {k}:  {a.get(k)} ≠ {_metin(kabin[k])}")
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


def _mm(x):
    """Mimarın uzunluğu ( mm ) ya da None — "1800", 1800.0."""
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _geri(g):
    """G2:  istenen ölçünün bir adım mimarınkine doğru geri alınmışı ( yazımıyla ) ya da None —
    aradaki fark bir adımdan küçükse ( geri adım mimarın kendi ölçüsüdür, o zaten "uygun" değil )."""
    eski, yeni = g["eski"], g["yeni"]
    if isinstance(yeni, str):
        y, _h = katlar.kot_oku(yeni)
        e, _h2 = katlar.kot_oku(eski) if isinstance(eski, str) else (None, None)
        if y is None or e is None or abs(y - e) <= GERI_ADIM:
            return None
        return katlar.kot_metni(y - math.copysign(GERI_ADIM, y - e))
    e = _mm(eski)
    if e is None or abs(yeni - e) <= GERI_ADIM:
        return None
    return int(round(yeni - math.copysign(GERI_ADIM, yeni - e)))


def guvenceler(m, r):
    """G2 – G4 ölçümü ( dar eksen;  RAPOR ):  [ ( güvence , metin ) ] — bozulanlar."""
    out = []
    if r["durum"] == "gereken":
        tam = {
            g["anahtar"]: (g["yeni"] if isinstance(g["yeni"], str) else int(round(g["yeni"])))
            for g in r["gereken"]
        }
        for g in r["gereken"]:
            x = _geri(g)
            if x is None:
                continue
            r2 = avan_secici.sec({**m, **tam, g["anahtar"]: x})
            if r2["durum"] == "uygun":
                a = r2["istek"]["asansorler"][0].get("agirlik_yeri")
                out.append(("G2", f"{g['anahtar']} {g['yeni']} istendi, {x} ile uygun ( ağırlık {a} )"))
    if r["durum"] == "uygun":
        for k in ("kuyu_genisligi", "kuyu_derinligi"):
            r2 = avan_secici.sec({**m, k: int(_mm(m[k])) + BUYUTME})
            if r2["durum"] == "sigmaz":
                out.append(("G4", f"{k} +{BUYUTME}:  sığmaz — {(r2.get('nedenler') or [''])[0][:120]}"))
            elif r2["durum"] != "uygun":
                istenen = [[g["anahtar"], g["yeni"]] for g in r2.get("gereken") or []]
                out.append(("G3", f"{k} +{BUYUTME}:  {r2['durum']} {istenen}"))
    return out


def _kur():
    avan_secici.SAATSIZ = True


def dene(senaryo):
    """Bir senaryo → { kimlik , hukum , ihlal , guvence , sure } ( işçi süreçte koşar ).  guvence
    yalnız dar eksende ( kimliği "dar|" / "vaka|" ile başlar ) ölçülür."""
    kimlik, anahtar, m = senaryo
    guvence = []
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
        if kimlik.split("|", 1)[0] in ("dar", "vaka"):
            guvence = guvenceler(m, r)
    except Exception:  # noqa: BLE001 — çökme de bulgudur
        hukum, ihlal = {"durum": "ÇÖKME"}, [traceback.format_exc(limit=4).strip().splitlines()[-1]]
    return {
        "kimlik": kimlik,
        "hukum": hukum,
        "ihlal": ihlal,
        "guvence": guvence,
        "sure": round(time.monotonic() - t0, 1),
    }


def _isci_sayisi():
    """KONTROL_IS ( kontrol.py'ninki ):  "auto" işlemci sayısı, sayı o kadar;  yoksa 2
    ( bilgisayarı doldurmasın — ağır iş yerelde koşulmaz )."""
    x = os.environ.get("KONTROL_IS", "2")
    return (os.cpu_count() or 2) if x == "auto" else max(1, int(x))


def main(argv):
    yenile = "--yenile" in argv
    eksen = argv[argv.index("--eksen") + 1] if "--eksen" in argv else "temel"
    if eksen not in EKSEN_HUKUMLERI:
        print(f"--eksen {eksen}:  {' · '.join(EKSEN_HUKUMLERI)} olmalı.")
        return 2
    kayit_yolu = EKSEN_HUKUMLERI[eksen]
    cikti = CIKTI if eksen == "temel" else os.path.join(CIKTI, eksen)
    dilim = int(argv[argv.index("--dilim") + 1]) if "--dilim" in argv else 1
    #  PARÇA ( 21 Kas — CI'da tek iş 27–49 dk sürüyordu ):  "i/n" senaryoların i. parçası, n'de bir
    #  atlanarak ( ağır ve hafif senaryolar parçalara dağılır )
    parca = argv[argv.index("--parca") + 1] if "--parca" in argv else "1/1"
    p, n_parca = (int(x) for x in parca.split("/"))
    if not 1 <= p <= n_parca:
        print(f"--parca {parca}:  1/2, 2/2 gibi olmalı.")
        return 2
    hepsi = senaryolar() if eksen == "temel" else dar_senaryolari()
    secilen = hepsi[::dilim][p - 1 :: n_parca]
    n = _isci_sayisi()
    ek = f", parça {parca}" if n_parca > 1 else ""
    print(
        f"avan seçicisi taraması ( {eksen} ):  {len(secilen)} / {len(hepsi)} senaryo{ek}, {n} işçi",
        flush=True,
    )
    t0 = time.monotonic()
    sonuclar = []
    with multiprocessing.Pool(n, initializer=_kur) as havuz:
        for i, s in enumerate(havuz.imap(dene, secilen), 1):
            sonuclar.append(s)
            if s["ihlal"]:
                print(f"  İHLAL  {s['kimlik']}:  {' · '.join(s['ihlal'])}", flush=True)
            for g, metin in s["guvence"]:
                print(f"  {g}  {s['kimlik']}:  {metin}", flush=True)
            if i % 25 == 0:
                print(f"  {i} / {len(secilen)}  ·  {(time.monotonic() - t0) / 60:.1f} dk", flush=True)

    hukumler = {s["kimlik"]: s["hukum"] for s in sonuclar}
    os.makedirs(cikti, exist_ok=True)
    with open(os.path.join(cikti, "sonuc.json"), "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, ensure_ascii=False, indent=1)
    with open(os.path.join(cikti, "hukumler.json"), "w", encoding="utf-8") as f:
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

    if eksen != "temel":
        guv = collections.Counter(g for s in sonuclar for g, _m in s["guvence"])
        print(
            "güvenceler ( rapor ):  "
            + "  ·  ".join(f"{g} bozuk {guv.get(g, 0)}" for g in ("G2", "G3", "G4"))
            + f"  —  ayrıntı {os.path.relpath(os.path.join(cikti, 'sonuc.json'), KOK)}"
        )

    ihlalli = [s for s in sonuclar if s["ihlal"]]
    tamam = not ihlalli
    if ihlalli:
        print(f"\nDEĞİŞMEZ BOZULDU:  {len(ihlalli)} senaryo ( yukarıda )")

    if yenile:
        if dilim != 1 or n_parca != 1:
            print("\n--yenile yalnız tam taramayla ( --dilim ve --parca olmadan ).")
            return 2
        with open(kayit_yolu, "w", encoding="utf-8") as f:
            json.dump(hukumler, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        print(f"\nhüküm kaydı yenilendi:  {os.path.relpath(kayit_yolu, KOK)}")
    elif not os.path.exists(kayit_yolu):
        print(
            "\nhüküm kaydı yok — karşılaştırma atlandı;  sonuç "
            f"{os.path.relpath(os.path.join(cikti, 'hukumler.json'), KOK)}'da."
        )
    else:
        with open(kayit_yolu, encoding="utf-8") as f:
            kayit = json.load(f)
        farklar = [
            f"  {k}:  {json.dumps(kayit.get(k), ensure_ascii=False)}  →  {json.dumps(h, ensure_ascii=False)}"
            for k, h in hukumler.items()
            if kayit.get(k) != h
        ]
        if dilim == 1 and n_parca == 1:
            farklar += [f"  {k}:  kayıtta var, taramada yok" for k in kayit if k not in hukumler]
        elif dilim == 1 and p == 1:
            #  Parçalı koşuda kaldırılan senaryoyu birinci parça söyler ( bütün senaryoların listesinden )
            tum = {k for k, _a, _m in hepsi}
            farklar += [f"  {k}:  kayıtta var, senaryolarda yok" for k in kayit if k not in tum]
        if farklar:
            tamam = False
            print(f"\nHÜKÜM DEĞİŞTİ:  {len(farklar)} senaryo ( kayıt → şimdi )")
            print("\n".join(farklar[:60]))
            if len(farklar) > 60:
                print(
                    f"  … {len(farklar) - 60} tane daha ( {os.path.relpath(os.path.join(cikti, 'hukumler.json'), KOK)} )"
                )
            print("Değişiklik bilerek yapıldıysa incelenip --yenile ile kayıt yenilenir.")
        else:
            print("\nhükümler kayıtla aynı.")
    print("\nTARAMA " + ("GEÇTİ" if tamam else "BAŞARISIZ"))
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
