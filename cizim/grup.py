# -*- coding: utf-8 -*-
"""
TEK KUYUDA İKİ ASANSÖR  —  kuyunun ortak çizimi ve denetimleri ( 1 Kas )

Kuyu düzeni projenin seçimidir ( tasarim/alanlar:  kuyu_duzeni — iki asansörlü
projede "İki asansör tek kuyuda" ):  kuyunun girdileri ( derinlik, duvarlar,
katlar, kuyu dibi, son kat … — KUYU_ORTAK ) iki asansörde aynıdır;  araları
açıktır — ortaya bakan raylar her konsol seviyesindeki çelik ayırma kirişine
bağlanır, ara kirişin yüksekliğidir ( cizim/kopru._acik_ara ).  Her asansörün
kendi girdisi, hesabı ve çizimleri vardır ( LiftDesigner'ın grup modeli —
cikti/devir/ORTAK_KUYU_PLANI.md );  kuyudaki yeri g["proje"]["grup_sirasi"]
( 1 solda, 2 sağda — "Soldaki asansör" ).

KUYUNUN PLANI ( C-C ) tek düzlemde:  her asansörün planı kendi yerinde, komşu
yandaki ölçüleri öbür yanında ( LiftDesigner 12744-3 gibi ), yazıları komşunun
yerine kaçmaz;  duvarlar bir kez ( arka ve ön duvar boydan boya, kapıların arası
dolu — KONE );  ortada ayırma kirişi;  en dışta duvarlar, bölmeler ve kiriş
zinciri ile toplam;  bölmelerin üstünde asansörlerin adları.
"""

import math

from cizim import cizimler
from cizim import eleman
from cizim import geometri
from cizim import girdi
from cizim import hesap_isareti
from cizim import kabin_ustu
from cizim import kisaltmalar
from cizim import sabitler
from cizim import sorun
from cizim import standart
from cizim import uslup

AD = "kuyu_grubu"
BASLIK = "KUYU GRUBU PLANI  ( kabin hizasından yatay kesit )"
OLCEK = 20
#  K1 ( kullanıcı kararı 1 Kas ):  tek kuyuda iki asansör yan yana
AZAMI = 2
#  Komşu kuyunun yerini kapatan çitin payı ( mm ):  etiket 900 mm'ye kadar kaçar
#  ( geometri.etiketleri_ayir ), ölçü sıraları kuyudan ~600 mm dışarı uzanır
_CIT_PAYI = 3000.0
#  Asansörün planının en dış üst sırası ( geometri._ust_olculer ):  kuyunun
#  zinciri yerine geçer
_DUVAR_SIRASI = frozenset(("olcu_duvar_sol", "olcu_kuyu_genisligi", "olcu_duvar_sag"))
KIRIS_YOK = (
    "Tek kuyuda ayırma kirişi seçilmeli ( Kuyu ve katlar → Ayırma kirişi ):  seçilmeden ara ve kiriş "
    "çizilmez."
)
#  Hareketli parçaların iletideki adı ( korkuluk_mesafesi )
PARCA_ADI = {"kabin_dis": "kabini", "agirlik_blok": "karşı ağırlığı"}


def gruptakiler(gler):
    """Projenin ( çizim girdileri ) tek kuyudaki asansörleri soldan sağa;  tek kuyu
    değilse ( ya da asansörlerden biri kurulamadıysa — None ) boş."""
    if any(g is None for g in gler):
        return []
    gg = sorted((g for g in gler if g["proje"].get("grup_sirasi")), key=lambda g: g["proje"]["grup_sirasi"])
    return gg if len(gg) == AZAMI else []


def kirisi(gler):
    """Tek kuyunun ayırma kirişinin NPU ölçüsü;  seçilmemişse None."""
    return gler[0]["proje"].get("ayirma_kirisi")


def korkuluk_mesafesi(gler):
    """m.5.2.5.5.2.2:  bir asansörün kabin üstü korkuluğunun iç kenarı
    ( kabin_ustu.korkuluklar ) ile komşu asansörün hareketli parçası ( kabin,
    karşı ağırlık — planda ) arasındaki en kısa yatay uzaklık:  ( mm, korkuluğun
    asansörü, parçanın asansörü, parça ) ;  korkuluk yoksa None.  Kabin üstü
    kurulamayan asansörde denetlenmez ( None )."""
    X = _x0lar(gler)
    korkuluklar, parcalar = [], []
    try:
        for x0, g in zip(X, gler):
            ad = g["proje"]["asansor"]
            for (a, b, c, d), _h in kabin_ustu.korkuluklar(kabin_ustu.yerlesim(g)):
                korkuluklar.append(((a + x0, b, c + x0, d), ad))
            for el in geometri.plan(g):
                if el.get("ad") in ("kabin_dis", "agirlik_blok"):
                    k = geometri.sinir([el])
                    parcalar.append(((k[0] + x0, k[1], k[2] + x0, k[3]), ad, PARCA_ADI[el["ad"]]))
    except sorun.BILINEN:
        return None

    def uzaklik(s, k):
        dx = max(0.0, k[0] - max(s[0], s[2]), min(s[0], s[2]) - k[2])
        dy = max(0.0, k[1] - max(s[1], s[3]), min(s[1], s[3]) - k[3])
        return math.hypot(dx, dy)

    adaylar = [(uzaklik(s, k), a, b, p) for s, a in korkuluklar for k, b, p in parcalar if a != b]
    return min(adaylar) if adaylar else None


def duzen_hatalari(gler):
    """Tek kuyunun sorunları ( gruptaki asansörlerin çizim girdileri, soldan sağa ):
    ayırma kirişi seçilmeli;  bir asansörün korkuluğu komşunun hareketli parçasına
    0,50 m'den yakınsa perde kuyu boyunca uzanmalı ( m.5.2.5.5.2.2 — program yalnız
    kuyu dibi perdesini çizer:  söylenir ).  Kuyunun öbür değerleri iki asansörde
    zaten aynıdır ( tek girdi — tasarim/alanlar KUYU_ORTAK )."""
    if kirisi(gler) is None:
        return [KIRIS_YOK]
    m = korkuluk_mesafesi(gler)
    if m and m[0] < standart.PERDE_KORKULUK_ASGARI:
        return [
            f"Tek kuyuda {m[1]} kabin üstü korkuluğu ile {m[2]} {m[3]} arası {m[0]:.0f} mm < "
            f"{standart.PERDE_KORKULUK_ASGARI:g}:  perde kuyu boyunca uzanmalı ( m.5.2.5.5.2.2 ) — "
            "program yalnız kuyu dibi perdesini çizer;  ayırma kirişi ya da yerleşim değişmeli."
        ]
    return []


def sorunlar(gler):
    """Projenin tek kuyusunun sorunları ( paket ):  gler — projenin bütün
    asansörlerinin çizim girdileri sırayla ( kurulamayan None:  denetlenmez )."""
    gg = gruptakiler(gler)
    return duzen_hatalari(gg) if gg else []


# ══════════════════════════════════════════════════════════════════════
#  GRUBUN KUYU PLANI
# ══════════════════════════════════════════════════════════════════════


def _x0lar(gler):
    """Kuyuların iç sol yüzlerinin grup koordinatı ( ilk kuyununki 0 )."""
    X = [0.0]
    for g in gler[:-1]:
        X.append(X[-1] + g["kuyu"]["genislik"] + g["kuyu"]["duvar_sag"])
    return X


def _cit(g, komsu, komsu_g):
    """Komşu kuyunun yerini kapatan taramalı alan ( geometri.plan'ın cit'i ):
    asansörün yazıları ve etiketleri ortak duvarın öbür yanına kaçmaz."""
    k = g["kuyu"]
    en = komsu_g["kuyu"]["genislik"] + _CIT_PAYI
    x0 = k["genislik"] + k["duvar_sag"] if komsu == "Sağ" else -k["duvar_sol"] - en
    y0 = -k["duvar_on"] - _CIT_PAYI
    boy = k["duvar_on"] + k["derinlik"] + k["duvar_arka"] + 2 * _CIT_PAYI
    return [eleman.dikdortgen("TARAMA", x0, y0, en, boy, tip="tarama")]


def _duvar_mi(el):
    """Asansörün kendi kuyusunun duvarları ve açık aradaki ayırma kirişi
    ( geometri._duvarlar ), bina duvarı:  grubun duvarları ve kirişi yerlerine
    bir kez çizilir."""
    return (
        el["katman"] in ("KUYU-DUVAR", "KUYU-IC", "BINA")
        or (el["katman"] == "TARAMA" and el["tip"] == "tarama")
        or el.get("ad") in ("ayirma_kirisi", "ayirma_kirisi_adi")
    )


def _asansorun_plani(g, komsu, komsu_g, alt):
    """Asansörün kendi koordinatında, grubun planındaki parçası:  planı ( çizim
    listesinin son adımlarıyla — cizimler.bitir ) komşu yanı çitle kapalıyken
    kurulur;  kendi duvarları çıkar.  Duvarın dışına uzanan eksenler komşu yanda
    ortak duvarın ortasında biter ( aynı derinlikteki iki eksen birleşir )."""
    cit = _cit(g, komsu, komsu_g)
    e = cizimler.bitir(geometri.plan(g, komsu=komsu, cit=cit, olcu_alti=alt), OLCEK)
    e = [x for x in e if all(x is not c for c in cit) and not _duvar_mi(x)]
    k = g["kuyu"]
    orta = k["genislik"] + k["duvar_sag"] / 2.0 if komsu == "Sağ" else -k["duvar_sol"] / 2.0
    for x in e:
        if x["tip"] == "eksen" and abs(x["y1"] - x["y2"]) < 1e-6:
            if komsu == "Sağ":
                x["x1"], x["x2"] = min(x["x1"], orta), min(x["x2"], orta)
            else:
                x["x1"], x["x2"] = max(x["x1"], orta), max(x["x2"], orta)
    return e


def _duvarlar(gler, X):
    """Kuyunun duvarları ( geometri._duvarlar'ın sırasıyla ):  ön duvar kapıların
    kaba boşlukları arasında parça parça ( kapıların arası dolu — KONE "trimmer
    beams" kuyusu ), arka duvar boydan boya, sol ve sağ duvar ( arada duvar yok:
    ayırma kirişi );  tek kuyunun içi.  Bina duvarı ( Sabitler'de bina_duvari > 0 )
    kapıların arasında."""
    ilk, son = gler[0]["kuyu"], gler[-1]["kuyu"]
    D, don, dar = ilk["derinlik"], ilk["duvar_on"], ilk["duvar_arka"]
    sol, sag = -ilk["duvar_sol"], X[-1] + son["genislik"] + son["duvar_sag"]
    S = [sabitler.sabitler(g.get("_cizim_sabitleri")) for g in gler]
    bosluk = [u + x0 for x0, g, s in zip(X, gler, S) for u in girdi.kaba_bosluk(g, s)[:2]]
    parca = [(a, -don, b - a, don) for a, b in zip([sol] + bosluk[1::2], bosluk[::2] + [sag])]
    parca += [(sol, D, sag - sol, dar), (sol, 0, ilk["duvar_sol"], D)]
    parca.append((X[-1] + son["genislik"], 0, son["duvar_sag"], D))
    e = []
    for x, y, g_, d_ in parca:
        if g_ <= 1e-6:
            continue
        e.append(eleman.dikdortgen("TARAMA", x, y, g_, d_, tip="tarama"))
        e.append(eleman.dikdortgen("KUYU-DUVAR", x, y, g_, d_))
    e.append(eleman.dikdortgen("KUYU-IC", 0, 0, X[-1] + son["genislik"], D))
    #  Bina duvarı ofis standardıdır ( bütün asansörlerde aynı )
    bina = S[0]["bina_duvari"]
    if bina > 0:
        kapi = [
            x0 + g["kapi"]["sol_pay"] + u * g["kapi"]["genislik"] for x0, g in zip(X, gler) for u in (0, 1)
        ]
        for a, b in zip([sol] + kapi[1::2], kapi[::2] + [sag]):
            if b - a > 0:
                e.append(eleman.dikdortgen("BINA", a, -don - bina, b - a, bina, tip="tarama_tugla"))
    return e


def _ayirma_kirisleri(gler, X):
    """Aradaki ayırma kirişi ( geometri.ayirma_kirisi ) — bir kez."""
    D = gler[0]["kuyu"]["derinlik"]
    return [
        el
        for x0, g in zip(X[:-1], gler[:-1])
        for el in geometri.ayirma_kirisi(g, x0 + g["kuyu"]["genislik"], g["kuyu"]["duvar_sag"], D)
    ]


def _ust_zincir(gler, X, kot):
    """En dış üst sıra:  duvarlar, bölmeler ve ortadaki ayırma kirişi ( LiftDesigner
    12744-3:  250 · SW2100 · 100 · SW1800 · 250 );  bir dışında kuyunun toplamı —
    zincir kapalı olduğu için yardımcı ölçü, ayraç içinde ( ISO 129-1 )."""
    ilk, son = gler[0]["kuyu"], gler[-1]["kuyu"]
    sol, sag = -ilk["duvar_sol"], X[-1] + son["genislik"] + son["duvar_sag"]
    e = [eleman.olcu("yatay", (sol, 0), (0, 0), kot, ad="grup_duvar_sol")]
    for n, (x0, g) in enumerate(zip(X, gler), 1):
        G, dg = g["kuyu"]["genislik"], g["kuyu"]["duvar_sag"]
        sag_ad = "grup_duvar_sag" if n == len(gler) else f"grup_ayirma_kirisi_{n}"
        e.append(
            eleman.olcu("yatay", (x0, 0), (x0 + G, 0), kot, kisaltmalar.kodlu("SW", G), ad=f"grup_kuyu_{n}")
        )
        e.append(eleman.olcu("yatay", (x0 + G, 0), (x0 + G + dg, 0), kot, ad=sag_ad))
    toplam = eleman.olcu(
        "yatay", (sol, 0), (sag, 0), kot + geometri.SIRA_ARASI, f"({sag - sol:g})", ad="grup_genisligi"
    )
    return e + [toplam]


def _sira_yazilari(e, ilk):
    """Üst ve alt ölçü sıralarının yazıları grupça yeniden yerleşir:  asansörlerin
    sıraları yan yana durur, birinin ucundan taşan yazı komşusununkine binmesin
    ( geometri.plan'ın adımlarıyla )."""
    for x in e:
        if x["tip"] == "olcu" and x["yon"] == "yatay":
            if x["kot"] > ilk["derinlik"] + ilk["duvar_arka"] or x["kot"] < -ilk["duvar_on"]:
                x.pop("yazi", None)
    geometri.yazilari_yerlestir(e, kaydir=True)
    geometri.parcadan_kaydir(e, ek_katman=("AGIRLIK",))


def _adlar(gler, X, e):
    """Kuyuların üstünde asansörlerin adları ( 12744-3'te kabinin içinde;  bizde
    kabinin içi ölçülü, ad en üstte boşta ).  Kuyuya sığmayan ad küçülür,
    komşusuna binen ad bir satır yukarı çıkar."""
    ust = geometri.sinir(e)[3] + 60.0
    out, sag_uc = [], None
    for x0, g in zip(X, gler):
        ad, G = g["proje"]["asansor"], g["kuyu"]["genislik"]
        h = uslup.HARF if eleman.yazi_eni(ad, uslup.HARF) <= G else uslup.NORMAL
        w, cx = eleman.yazi_eni(ad, h), x0 + G / 2.0
        y = ust + h / 2.0
        if sag_uc is not None and cx - w / 2.0 < sag_uc[0] + 60.0:
            y = sag_uc[1] + uslup.HARF + 40.0
        out.append(eleman.yazi(cx, y, ad, h))
        sag_uc = (cx + w / 2.0, y)
    return out


def plan(gler):
    """Tek kuyunun planı ( C-C ) — elemanlar, çerçevesiz.  gler:  kuyudaki
    asansörlerin çizim girdileri, soldan sağa ( duzen_hatalari temiz )."""
    if len(gler) != AZAMI:
        raise ValueError(f"Tek kuyunun planı {AZAMI} asansörle çizilir ( {len(gler)} ).")
    if kirisi(gler) is None:
        raise ValueError("Tek kuyuda ayırma kirişi seçilmeden kuyunun planı çizilmez.")
    X = _x0lar(gler)
    alt = min(geometri.olcu_alti(g) for g in gler)
    parcalar, kotlar = [], []
    for n, g in enumerate(gler):
        komsu, komsu_g = ("Sağ", gler[n + 1]) if n == 0 else ("Sol", gler[n - 1])
        e = _asansorun_plani(g, komsu, komsu_g, alt)
        kotlar += [x["kot"] for x in e if x.get("ad") in _DUVAR_SIRASI]
        parcalar += [eleman.tasi(x, X[n]) for x in e if x.get("ad") not in _DUVAR_SIRASI]
    e = _duvarlar(gler, X) + _ayirma_kirisleri(gler, X) + parcalar + _ust_zincir(gler, X, max(kotlar))
    _sira_yazilari(e, gler[0]["kuyu"])
    e = geometri.ondalik_virgul(e)
    return e + _adlar(gler, X, e)


def baslik(gler):
    """Başlık;  bütün asansörlerin düşey kesitleri çiziliyorsa seviye harfiyle
    ( "KUYU GRUBU PLANI  C-C" — asansörlerin kesitlerindeki C-C ile aynı seviye )."""
    b = {cizimler.plan_basligi(g, "kuyu_plani", BASLIK) for g in gler}
    return b.pop() if len(b) == 1 else BASLIK


def uyari(gler):
    """Hesabın uygun bulmadığı bölümler ( hesap_isareti ) — asansör asansör, adıyla."""
    out = []
    for g in gler:
        s = hesap_isareti.not_satirlari(g["proje"].get("hesap_uygun_degil") or [])
        if s:
            out += [f"{g['proje']['asansor']}  —  {s[0]}"] + s[1:]
    return out


def adlari(gler):
    """Grubun asansörleri tek satırda:  "ASANSÖR 1  ·  ASANSÖR 2"."""
    return "  ·  ".join(g["proje"]["asansor"] for g in gler)


def cerceveli(gler, seritler=()):
    """Grubun planı çerçevesiyle ( ekran ve pafta ):  ( başlık , elemanlar )."""
    b = baslik(gler)
    return b, geometri.cerceveli(plan(gler), b, OLCEK, seritler=seritler, uyari=uyari(gler))


def pafta_cizimleri(gler):
    """Paftanın tek kuyu çizimi:  [ ( ad , başlık , ölçek , elemanlar — çerçeveli ) ],
    tek kuyu değilse boş;  kuyunun sorunu varsa ValueError ( pafta.cizim_listesi gibi )."""
    gg = gruptakiler(gler)
    if not gg:
        return []
    h = duzen_hatalari(gg)
    if h:
        raise ValueError("Pafta çizilemiyor:  " + " · ".join(h))
    b, e = cerceveli(gg, (adlari(gg),))
    return [(AD, b, OLCEK, e)]


def kunyeler(gler):
    """pafta_cizimleri ile aynı sırada çizimlerin projesi ve asansörleri
    ( ayrı sayfalı PDF'in anteti — pafta.kunyeler )."""
    gg = gruptakiler(gler)
    return [{"proje": gg[0]["proje"]["ad"], "asansor": adlari(gg)}] if gg else []
