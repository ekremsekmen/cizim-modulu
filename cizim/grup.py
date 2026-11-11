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
#  Tek kuyunun ortak çizimleri ( asansörün kendi listesinde yoklar — pafta.sira ):
#  kuyu planı ( plan ) ve öbür yatay kesitler ( birlesik );  ekrandaki ve paftadaki adları
BIRLESIK = (
    "kuyu_plani",
    "kabin_ustu",
    "kuyu_dibi",
    "kuyu_ustu",
    "makine_dairesi",
    "delik_plani",
    "kuyu_kesiti_on",
)
ADLAR = {"kuyu_plani": AD, **{a: f"{AD}_{a}" for a in BIRLESIK[1:]}}
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


def _isaretle(e, n):
    """Asansörün ölçüleri kimin ( "asansor":  gruptaki sırası, 0 soldaki — ekranda
    tıklanınca o asansörün girdisi:  olcu_kaynagi.asansorun_esi ) ;  kuyunun kendi
    ölçüleri ( dış zincir, kiriş ) işaretsiz."""
    for x in e:
        if x["tip"] == "olcu":
            x["asansor"] = n
    return e


def gruptakiler(gler):
    """Projenin ( çizim girdileri ) tek kuyudaki asansörleri soldan sağa;  tek kuyu
    değilse ( ya da asansörlerden biri kurulamadıysa — None ) boş."""
    if any(g is None for g in gler):
        return []
    gg = sorted((g for g in gler if g["proje"].get("grup_sirasi")), key=lambda g: g["proje"]["grup_sirasi"])
    if len(gg) != AZAMI:
        return []
    perdeyi_isle(gg)
    return gg


def kirisi(gler):
    """Tek kuyunun ayırma kirişinin NPU ölçüsü;  seçilmemişse None."""
    return gler[0]["proje"].get("ayirma_kirisi")


def _korkuluk_parca_araliklari(gler):
    """Her korkuluk kenarı ( kabin_ustu.korkuluklar ) ile komşu asansörün her
    hareketli parçası ( kabin, karşı ağırlık — planda ) arasındaki yatay uzaklıklar:
    [ ( mm, korkuluğun asansörü, parçanın asansörü, parça, parçanın kutusu ) ];
    kabin üstü kurulamayan asansörde None."""
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

    return [(uzaklik(s, k), a, b, p, k) for s, a in korkuluklar for k, b, p in parcalar if a != b]


def korkuluk_mesafesi(gler):
    """m.5.2.5.5.2.2:  bir asansörün kabin üstü korkuluğunun iç kenarı ile komşu
    asansörün hareketli parçası arasındaki en kısa yatay uzaklık:  ( mm, korkuluğun
    asansörü, parçanın asansörü, parça ) ;  korkuluk yoksa ya da kabin üstü
    kurulamıyorsa None."""
    adaylar = _korkuluk_parca_araliklari(gler)
    return min(adaylar)[:4] if adaylar else None


def tam_boy_perde(gler):
    """m.5.2.5.5.2.2:  bir korkuluğun iç kenarı komşunun hareketli parçasına
    0,50 m'den yakınsa asansörler arası perde KUYU BOYUNCA uzanır;  eni parçanın eni
    ve iki yanda 0,10 m ( kullanıcı kararı 11 Kas:  kendiliğinden, standardın en az
    eni, tavana kadar;  kuyu dibi perdesi aynı kalır ).  →  perdenin kuyu derinliği
    boyunca aralığı ( y0 , y1 ) — kuyunun içine kırpılmış;  gerekmiyorsa None."""
    if len(gler) != AZAMI or kirisi(gler) is None:
        return None
    yakin = [
        k for d, _a, _b, _p, k in _korkuluk_parca_araliklari(gler) or [] if d < standart.PERDE_KORKULUK_ASGARI
    ]
    if not yakin:
        return None
    D = gler[0]["kuyu"]["derinlik"]
    return (
        max(0.0, min(k[1] for k in yakin) - standart.PERDE_YAN_PAYI),
        min(D, max(k[3] for k in yakin) + standart.PERDE_YAN_PAYI),
    )


def perdeyi_isle(gler):
    """Tam boy perdenin aralığını grubun iki asansörünün girdisine yazar
    ( kuyu.tam_boy_perde — kesitler oradan okur:  A-A asansörün kendi çizimidir,
    komşuyu bilmez ).  Gerekmiyorsa anahtar None.  Yinelenebilir."""
    gg = sorted(
        (g for g in gler if g and g["proje"].get("grup_sirasi")), key=lambda g: g["proje"]["grup_sirasi"]
    )
    if len(gg) != AZAMI:
        return
    p = tam_boy_perde(gg)
    for g in gg:
        g["kuyu"]["tam_boy_perde"] = list(p) if p else None


def duzen_hatalari(gler):
    """Tek kuyunun sorunları ( gruptaki asansörlerin çizim girdileri, soldan sağa ):
    ayırma kirişi seçilmeli.  Bir asansörün korkuluğu komşunun hareketli parçasına
    0,50 m'den yakınsa perde kuyu boyunca uzanır ( m.5.2.5.5.2.2 ):  11 Kas'a kadar
    ret sebebiydi, artık çizilir ( tam_boy_perde ).  Kuyunun öbür değerleri iki
    asansörde zaten aynıdır ( tek girdi — tasarim/alanlar KUYU_ORTAK )."""
    if kirisi(gler) is None:
        return [KIRIS_YOK]
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
    return _eksenleri_kirp(g, komsu, e)


def _engeller(e, dx=0.0):
    """Çizimin yer kaplayan elemanlarının kutuları ( komşunun çizimi için engel —
    geometri.komsulu ):  parçalar, yazılar, ölçü çizgileri ve yazıları;  duvarlar,
    eksenler, kuyunun içi değil."""
    out = []
    for x in e:
        if _duvar_mi(x) or x["tip"] in ("eksen", "tarama") or x["katman"] in ("EKSEN", "KUYU-IC"):
            continue
        if x["tip"] == "olcu":
            a, b, k = x["a"], x["b"], x["kot"]
            kutular = [
                (min(a[0], b[0]), k - 15, max(a[0], b[0]), k + 15)
                if x["yon"] == "yatay"
                else (k - 15, min(a[1], b[1]), k + 15, max(a[1], b[1]))
            ]
            if x.get("yazi"):
                kutular.append(geometri.yazi_kutusu(x))
        else:
            kutular = [geometri.sinir([x])]
        out += [(k[0] + dx, k[1], k[2] + dx, k[3]) for k in kutular if k]
    return out


def _gevsekce(g, komsu, ad, cit_x, engel):
    """Asansörün parçası önce komşunun bölmesi kapalıyken ( geometri.komsulu
    siki );  yük kutusu yer bulamazsa komşunun yakın yarısı da açılır."""
    try:
        with geometri.komsulu(komsu, cit_x, engel):
            return _asansorun_cizimi(g, komsu, ad)
    except ValueError:
        with geometri.komsulu(komsu, cit_x, engel, siki=False):
            return _asansorun_cizimi(g, komsu, ad)


def _asansorun_cizimi(g, komsu, ad):
    """Asansörün kendi koordinatında, kuyunun ortak kuyu dibi / kabin üstü / kuyu
    üstü çizimindeki parçası:  çizimi komşunun yeri kapalıyken ( geometri.cit )
    kurulur;  kendi duvarları çıkar, komşu yandaki ölçü sıraları öbür yana geçer
    ( yan_olculeri_tasi ), eksenler aranın ortasında biter."""
    e = geometri.citsiz(cizimler.CIZIMLER[ad][1](g))
    bosluklu = sum(x["katman"] == "KUYU-DUVAR" and x["y"] < 0 for x in e) > 1
    e = [x for x in e if not _duvar_mi(x)]
    yan_olculeri_tasi(g, komsu, e)
    return _eksenleri_kirp(g, komsu, e), bosluklu


def yan_olculeri_tasi(g, komsu, e, yanlar=None, k=1.0, engel=None):
    """Komşu yandaki düşey ölçü sıraları öbür yanın sıralarının dışına geçer
    ( duvardan uzaklıkları ve aralarındaki boşluk korunur — geometri._yan_olculer'in
    komsu'su gibi );  yazıları yeniden yerleşir.  yanlar:  ( sol , sağ ) dış yüzler
    ( verilmezse planınki — kesit arkadan bakar, yanları ters );  k:  ölçeğin
    1/20'ye oranı ( kesitte sıra arası ve duvardan uzaklık büyür );  engel:  o yanda
    sıraların da dışındaki elemanların en dış x'i ( kesitte seviye harfleri )."""
    ku = g["kuyu"] if g else None
    sol, sag = yanlar or (-ku["duvar_sol"], ku["genislik"] + ku["duvar_sag"])
    ara, pay = geometri.SIRA_ARASI * k, 120.0 * k
    dusey = [x for x in e if x["tip"] == "olcu" and x["yon"] == "dusey"]
    if komsu == "Sağ":
        tasan = [x for x in dusey if x["kot"] > sag]
        kalan = [x["kot"] for x in dusey if x["kot"] < sol]
        dis = min(kalan + [sol - pay + ara] + ([engel - pay + ara] if engel is not None else [])) - ara
        for x in tasan:
            x["kot"] = dis - (x["kot"] - sag - pay)
            x.pop("yazi", None)
    else:
        tasan = [x for x in dusey if x["kot"] < sol]
        kalan = [x["kot"] for x in dusey if x["kot"] > sag]
        dis = max(kalan + [sag + pay - ara]) + ara
        for x in tasan:
            x["kot"] = dis + (sol - pay - x["kot"])
            x.pop("yazi", None)


def _eksenleri_kirp(g, komsu, e):
    k = g["kuyu"]
    orta = k["genislik"] + k["duvar_sag"] / 2.0 if komsu == "Sağ" else -k["duvar_sol"] / 2.0
    for x in e:
        if x["tip"] == "eksen" and abs(x["y1"] - x["y2"]) < 1e-6:
            if komsu == "Sağ":
                x["x1"], x["x2"] = min(x["x1"], orta), min(x["x2"], orta)
            else:
                x["x1"], x["x2"] = max(x["x1"], orta), max(x["x2"], orta)
    return e


def _duvarlar(gler, X, bosluklu=(True, True)):
    """Kuyunun duvarları ( geometri._duvarlar'ın sırasıyla ):  ön duvar kapıların
    kaba boşlukları arasında parça parça ( kapıların arası dolu — KONE "trimmer
    beams" kuyusu ), arka duvar boydan boya, sol ve sağ duvar ( arada duvar yok:
    ayırma kirişi );  tek kuyunun içi.  Bina duvarı ( Sabitler'de bina_duvari > 0 )
    kapıların arasında."""
    ilk, son = gler[0]["kuyu"], gler[-1]["kuyu"]
    D, don, dar = ilk["derinlik"], ilk["duvar_on"], ilk["duvar_arka"]
    sol, sag = -ilk["duvar_sol"], X[-1] + son["genislik"] + son["duvar_sag"]
    S = [sabitler.sabitler(g.get("_cizim_sabitleri")) for g in gler]
    bosluk = [u + x0 for x0, g, s, b in zip(X, gler, S, bosluklu) if b for u in girdi.kaba_bosluk(g, s)[:2]]
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
    if bina > 0 and any(bosluklu):
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


TAM_BOY_PERDE_ADI = ("TAM BOY PERDE", "PERDE")
#  Perdenin adı ile aynı hizadaki ayırma kirişi adı arasında en az açıklık ( mm )
_PERDE_ADI_BOSLUGU = 150.0


def _tam_boy_perdesi(gler, X):
    """Tam boy perde ( tam_boy_perde ) planda:  aranın ortasında, eni kadar — bir kez."""
    p = tam_boy_perde(gler)
    if p is None:
        return []
    x = X[1] - gler[0]["kuyu"]["duvar_sag"] / 2.0
    return [eleman.ad(eleman.cizgi("PERDE", x, p[0], x, p[1]), "grup_perdesi")]


def _tam_boy_perde_adi(gler, e):
    """Tam boy perdenin adı:  aranın boyunca herhangi bir yerde ( perdenin kendi
    boyu kısa olabilir ), ayırma kirişinin adından ayrık."""
    return geometri.grup_perdesi_adi(
        e,
        metinler=TAM_BOY_PERDE_ADI,
        aralik=(0.0, gler[0]["kuyu"]["derinlik"]),
        bosluk=_PERDE_ADI_BOSLUGU,
        parcadan_kac=True,
    )


def perde_notu(gler):
    """Tam boy perdenin sebebi — kuyunun planının altındaki not ( paftada ve ekranda ):
    hangi korkuluk hangi parçaya ne kadar yakın, hangi madde.  Perde gerekmiyorsa boş."""
    if tam_boy_perde(gler) is None:
        return []
    d, korkuluk, parca_asansoru, parca = korkuluk_mesafesi(gler)
    return [
        f"ASANSÖRLER ARASI PERDE KUYU BOYUNCA  —  {korkuluk} kabin üstü korkuluğu ile "
        f"{parca_asansoru} {parca} arası {d:.0f} mm < {standart.PERDE_KORKULUK_ASGARI:g} mm"
        "  ·  TS EN 81-20 m.5.2.5.5.2.2"
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


def _adlar(gler, X, e, k=1.0):
    """Kuyuların üstünde asansörlerin adları ( 12744-3'te kabinin içinde;  bizde
    kabinin içi ölçülü, ad en üstte boşta ).  Kuyuya sığmayan ad küçülür,
    komşusuna binen ad bir satır yukarı çıkar.  k:  ölçeğin 1/20'ye oranı
    ( kesit 1/50 — yazı kağıtta aynı boyda )."""
    ust = geometri.sinir(e)[3] + 60.0 * k
    out, sag_uc = [], None
    for x0, g in zip(X, gler):
        ad, G = g["proje"]["asansor"], g["kuyu"]["genislik"]
        h = (uslup.HARF if eleman.yazi_eni(ad, uslup.HARF) * k <= G else uslup.NORMAL) * k
        w, cx = eleman.yazi_eni(ad, h), x0 + G / 2.0
        y = ust + h / 2.0
        if sag_uc is not None and cx - w / 2.0 < sag_uc[0] + 60.0 * k:
            y = sag_uc[1] + (uslup.HARF + 40.0) * k
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
        e = _isaretle(_asansorun_plani(g, komsu, komsu_g, alt), n)
        kotlar += [x["kot"] for x in e if x.get("ad") in _DUVAR_SIRASI]
        parcalar += [eleman.tasi(x, X[n]) for x in e if x.get("ad") not in _DUVAR_SIRASI]
    e = _duvarlar(gler, X) + _ayirma_kirisleri(gler, X) + parcalar + _ust_zincir(gler, X, max(kotlar))
    e += _tam_boy_perdesi(gler, X)
    _sira_yazilari(e, gler[0]["kuyu"])
    e = geometri.ondalik_virgul(e)
    e += _tam_boy_perde_adi(gler, e)
    return e + _adlar(gler, X, e)


def birlesik(gler, ad):
    """Tek kuyunun ortak kuyu dibi / kabin üstü / kuyu üstü çizimi ( BIRLESIK ) —
    elemanlar, çerçevesiz:  asansörlerin çizimleri kendi yerlerinde, duvarlar ve
    ayırma kirişi bir kez, iki kuyu dibinin perdesi bir kez, en dışta kuyunun
    zinciri ( planınki gibi ), adlar en üstte."""
    if len(gler) != AZAMI or kirisi(gler) is None:
        raise ValueError("Tek kuyunun çizimi iki asansör ve ayırma kirişiyle çizilir.")
    X = _x0lar(gler)
    A, B = gler
    X1, GA, GB = X[1], A["kuyu"]["genislik"], B["kuyu"]["genislik"]
    #  Soldaki önce, sağdakinin PARÇALARI engelken ( yazılarını sağdaki sonra
    #  soldakininkilerden kaçarak koyar );  çitler komşunun bölmesinin ortasında
    #  Kuyunun en dıştaki zinciri ( _ust_zincir ) ve toplamı sonra eklenir:  yeri
    #  baştan engeldir ( kuyunun dışına konan yük kutusu ona biniyordu )
    ciz = cizimler.CIZIMLER[ad][1]
    eB0 = ciz(B)
    parca = [x for x in eB0 if x["katman"] in geometri.PARCA_KATMANLARI]
    zincir = [x["kot"] for x in eB0 if x.get("ad") in _DUVAR_SIRASI]
    serit = (
        [(-_CIT_PAYI - X1, max(zincir) - 15, X1 + GB + _CIT_PAYI, max(zincir) + geometri.SIRA_ARASI + 150)]
        if zincir
        else []
    )
    eA, bA = _gevsekce(A, "Sağ", ad, X1 + GB / 2.0, _engeller(parca, X1) + serit)
    serit = [(a - X1, b, c - X1, d) for a, b, c, d in serit]
    eB, bB = _gevsekce(B, "Sol", ad, GA / 2.0 - X1, _engeller(eA, -X1) + serit)
    _isaretle(eA, 0)
    _isaretle(eB, 1)
    parcalar, kotlar, bosluklu = [], [], [bA, bB]
    for n, e in enumerate((eA, eB)):
        #  Perde ve adı bir kez ( soldakininki — ikisi aynı yerde )
        e = [x for x in e if n == 0 or x.get("ad") not in ("grup_perdesi", "grup_perdesi_adi")]
        kotlar += [x["kot"] for x in e if x.get("ad") in _DUVAR_SIRASI]
        parcalar += [eleman.tasi(x, X[n]) for x in e if x.get("ad") not in _DUVAR_SIRASI]
    e = _duvarlar(gler, X, bosluklu) + _ayirma_kirisleri(gler, X) + parcalar
    if kotlar:
        e += _ust_zincir(gler, X, max(kotlar))
    #  Yalnız yeri boşalan ( öbür yana geçen ) ölçülerin ve zincirin yazıları
    geometri.yazilari_yerlestir(e)
    e = geometri.ondalik_virgul(e)
    #  Kuyu dibinde perde zaten boydan boya ( m.5.2.5.5.2.1 );  öbür planlarda tam boy perde
    if ad != "kuyu_dibi":
        e += _tam_boy_perdesi(gler, X)
        e += _tam_boy_perde_adi(gler, e)
    else:
        #  Perdenin adı iki asansör birleştikten sonra:  soldakinin çizimi sağdakinin
        #  araya uzanan konsol kollarını bilmez, ad kolların üstüne düşüyordu
        e = [x for x in e if x.get("ad") != "grup_perdesi_adi"]
        e += geometri.grup_perdesi_adi(e, bosluk=_PERDE_ADI_BOSLUGU, parcadan_kac=True)
    return e + _adlar(gler, X, e)


def on_kesit(gler, azami=None):
    """Tek kuyunun B-B kesiti ( arkadan kat kapılarına bakış ) — iki asansörün
    kesiti yan yana, elemanlar çerçevesiz.  Arkadan bakıldığı için planın sağındaki
    asansör solda.  Katlar ve kotlar ortaktır ( KUYU_ORTAK ):  soldakinin sol
    yanındaki kot zincirleri, durak adları, kotlar ikisinindir — sağdakininkiler
    atılır;  soldakinin aradaki konsol ölçüleri onun dış yanına geçer
    ( yan_olculeri_tasi );  döşemeler boydan boya bir kez;  ayırma kirişinin
    kesitleri iki asansörün konsol kotlarında ( aynı kotta bir kez );  plan
    seviyeleri ( C-C, D-D … — kabin yüksekliği asansörden asansöre değişir ) her
    asansörün kendi yarısında, harfi dış yanında."""
    if len(gler) != AZAMI or kirisi(gler) is None:
        raise ValueError("Tek kuyunun kesiti iki asansör ve ayırma kirişiyle çizilir.")
    R, L = gler  # planın solundaki kesitte sağda
    ciz = cizimler.CIZIMLER["kuyu_kesiti_on"][1]
    eL, eR = (ciz(g, azami=azami) if azami else ciz(g) for g in (L, R))
    _isaretle(eL, 1)
    _isaretle(eR, 0)
    GL, h = L["kuyu"]["genislik"], L["kuyu"]["duvar_sol"]
    X1, orta = GL + h, GL + h / 2.0
    #  Soldaki:  aradaki konsol ölçüleri dışa, aradaki seviye harfleri gider
    sol, sag = -L["kuyu"]["duvar_sag"], GL + h
    k = olcegi("kuyu_kesiti_on") / 20.0
    harf = [
        _sinir(x)[0] for x in eL if x["tip"] != "olcu" and _sinir(x)[2] < sol and x["katman"] != "KUYU-IC"
    ]
    yan_olculeri_tasi(None, "Sağ", eL, (sol, sag), k, min(harf, default=None))
    eL = [x for x in eL if not (x["tip"] != "olcu" and x.get("ad") != "grup_perdesi" and _sinir(x)[0] > orta)]
    #  Sağdaki:  sol yanı ( ortak kotlar, aradaki perde ) gider
    eR = [x for x in eR if x.get("ad") != "grup_perdesi" and not _sinir(x)[2] < -h / 2.0]
    for x in eL:
        if x["tip"] == "eksen":
            x["x1"], x["x2"] = min(x["x1"], orta), min(x["x2"], orta)
    for x in eR:
        if x["tip"] == "eksen":
            x["x1"], x["x2"] = max(x["x1"], -h / 2.0), max(x["x2"], -h / 2.0)
    #  Döşemeler ( geniş duvar parçaları ) soldakinin, sağdakinin sağ ucuna kadar
    doseme = {round(x["y"], 3): x for x in eR if _doseme_mi(x)}
    for x in eL:
        if _doseme_mi(x) and round(x["y"], 3) in doseme:
            d = doseme[round(x["y"], 3)]
            x["g"] = X1 + d["x"] + d["g"] - x["x"]
    eR = [eleman.tasi(x, X1) for x in eR if not _doseme_mi(x)]
    #  Ayırma kirişinin kesiti aynı kotta bir kez
    kiris = {(round(x["x"], 1), round(x["y"], 1)) for x in eL if x.get("ad") == "ayirma_kirisi"}
    eR = [
        x
        for x in eR
        if not (x.get("ad") == "ayirma_kirisi" and (round(x["x"], 1), round(x["y"], 1)) in kiris)
    ]
    e = eL + eR
    geometri.yazilari_yerlestir(e, h=eleman.OLCU_YAZI * k)
    return e + _adlar([L, R], [0.0, X1], e, k)


def makine_dairesi(gler):
    """Tek kuyunun makine dairesi planı:  oda iki asansörün ( kopru._tek_kuyu_odasi —
    yeri kuyunun sol iç köşesine göre, panolar kendi yarısında ).  Soldakinin çizimi
    odasıyla ( duvarlar, kapı, oda ölçüleri ) aynen;  sağdakinden yalnız kendi
    parçaları — oda bir kez.  Tabliye kirişin üstünden kesintisiz:  aradaki
    kenarları gider.  Kuyu zinciri:  odanın iç yüzünden soldaki bölme · kiriş ·
    sağdaki bölme · odanın iç yüzü;  aynı ölçü ( kuyu derinliği, oda derinliği ) bir kez."""
    if len(gler) != AZAMI or kirisi(gler) is None:
        raise ValueError("Tek kuyunun makine dairesi iki asansör ve ayırma kirişiyle çizilir.")
    A, B = gler
    X1 = _x0lar(gler)[1]
    GA = A["kuyu"]["genislik"]
    ciz = cizimler.CIZIMLER["makine_dairesi"][1]
    eA, eB = _isaretle(ciz(A), 0), [eleman.tasi(x, X1) for x in _isaretle(ciz(B), 1)]
    zincir = next((x["kot"] for x in eA if x.get("ad") == "olcu_kuyu_genisligi"), None)

    def oda_mi(x):
        return (
            x["katman"] in ("KUYU-DUVAR", "KUYU-IC")
            or x["tip"] == "tarama"
            or x.get("ad")
            in (
                "oda_kapisi",
                "olcu_oda_genisligi",
                "olcu_oda_derinligi",
                "merdiven_notu",
                "tabliye_yazi",
            )
        )

    def ara_kenari(x):
        return x.get("ad") == "tabliye_kenari" and all(GA - 1 < x[k] < X1 + 1 for k in ("x1", "x2"))

    def zincirde(x):
        return (
            x["tip"] == "olcu"
            and x["yon"] == "yatay"
            and zincir is not None
            and abs(x["kot"] - zincir) < 1e-6
        )

    eA = [
        x for x in eA if not ara_kenari(x) and not (zincirde(x) and x["a"][0] > GA - 1 and x["b"][0] > GA + 1)
    ]
    eB = [
        x
        for x in eB
        if not (oda_mi(x) and x.get("ad") != "tabliye_kenari")
        and not ara_kenari(x)
        and not (zincirde(x) and min(x["a"][0], x["b"][0]) < X1 - 1)
    ]
    yazilar = {(x["metin"], round(x["x"], 1), round(x["y"], 1)) for x in eA if x["tip"] == "yazi"}
    eB = [
        x
        for x in eB
        if not (x["tip"] == "yazi" and (x["metin"], round(x["x"], 1), round(x["y"], 1)) in yazilar)
    ]
    olculen = {(x["yon"], round(x["kot"], 1), geometri.olcu_araligi(x)) for x in eA if x["tip"] == "olcu"}
    eB = [
        x
        for x in eB
        if not (x["tip"] == "olcu" and (x["yon"], round(x["kot"], 1), geometri.olcu_araligi(x)) in olculen)
    ]
    e = eA + eB
    if zincir is not None:
        e.append(eleman.olcu("yatay", (GA, 0), (X1, 0), zincir, ad="grup_ayirma_kirisi_1"))
    for x in e:
        if zincirde(x):
            x.pop("yazi", None)
    geometri.yazilari_yerlestir(e)
    return e + _adlar(gler, [0.0, X1], e)


def _sinir(x):
    return geometri.sinir([x]) or (0.0, 0.0, 0.0, 0.0)


def _doseme_mi(x):
    """Kesitte kuyu dibi ve tavan döşemesi:  enine uzun duvar parçası ( ve taraması )."""
    return (x["katman"] == "KUYU-DUVAR" or x["tip"] == "tarama") and x.get("g", 0) > x.get("d", 0)


def baslik(gler, ad="kuyu_plani"):
    """Başlık;  bütün asansörlerin düşey kesitleri çiziliyorsa seviye harfiyle
    ( "KUYU GRUBU PLANI  C-C" — asansörlerin kesitlerindeki C-C ile aynı seviye )."""
    ana = BASLIK if ad == "kuyu_plani" else cizimler.CIZIMLER[ad][2]
    b = {cizimler.plan_basligi(g, ad, ana) for g in gler}
    return b.pop() if len(b) == 1 else ana


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


def cizimleri(gler):
    """Tek kuyunun ortak çizimleri sırayla:  kuyu üstü planı yalnız makine dairesizde
    ( pafta.sira gibi — makine yeri proje genelidir, iki asansörde aynı )."""
    oda = (gler[0].get("makine") or {}).get("yeri") == "Makine dairesi"
    odali = ("makine_dairesi", "delik_plani")
    return [a for a in BIRLESIK if (a in odali) == oda or a not in odali + ("kuyu_ustu",)]


def kurulamayanlar(gler, ad):
    """Asansörlerin o çizimdeki denetim hataları ( cizimler.CIZIMLER'in dogrula'sı )."""
    if ad == "kuyu_plani":
        return []
    dogrula = cizimler.CIZIMLER[ad][0]
    return [f"{g['proje']['asansor']} — {ad}: {h}" for g in gler for h in dogrula(g)]


def elemanlari(gler, ad, yukseklik=None):
    """Tek kuyunun ad'lı ortak çizimi — elemanlar, çerçevesiz ( cerceveli ve girdi
    taraması — araclar/tarama )."""
    if ad == "kuyu_plani":
        return plan(gler)
    if ad == "makine_dairesi":
        return makine_dairesi(gler)
    if ad == "kuyu_kesiti_on":
        return on_kesit(gler, yukseklik * olcegi(ad) if yukseklik else None)
    return birlesik(gler, ad)


def cerceveli(gler, seritler=(), ad="kuyu_plani", yukseklik=None):
    """Tek kuyunun çizimi çerçevesiyle ( ekran ve pafta ):  ( başlık , elemanlar ).
    yukseklik:  paftanın serbest alanının yüksekliği ( kesit sığmazsa kırılır —
    pafta.cizim_listesi gibi )."""
    b = baslik(gler, ad)
    e = elemanlari(gler, ad, yukseklik)
    bilgi = perde_notu(gler) if ad == "kuyu_plani" else []
    return b, geometri.cerceveli(e, b, olcegi(ad), seritler=seritler, uyari=uyari(gler), bilgi=bilgi)


def olcegi(ad):
    return cizimler.OLCEKLER.get(ad, OLCEK)


def pafta_cizimleri(gler, yukseklik=None):
    """Paftanın tek kuyu çizimleri:  [ ( ad , başlık , ölçek , elemanlar — çerçeveli ) ],
    tek kuyu değilse boş;  kuyunun ya da bir çizimin sorunu varsa ValueError
    ( pafta.cizim_listesi gibi )."""
    gg = gruptakiler(gler)
    if not gg:
        return []
    h = duzen_hatalari(gg) + [x for ad in cizimleri(gg) for x in kurulamayanlar(gg, ad)]
    if h:
        raise ValueError("Pafta çizilemiyor:  " + " · ".join(h))
    out = []
    for ad in cizimleri(gg):
        b, e = cerceveli(gg, (adlari(gg),), ad, yukseklik)
        out.append((ADLAR[ad], b, olcegi(ad), e))
    return out


def kunyeler(gler):
    """pafta_cizimleri ile aynı sırada çizimlerin projesi ve asansörleri
    ( ayrı sayfalı PDF'in anteti — pafta.kunyeler )."""
    gg = gruptakiler(gler)
    return [{"proje": gg[0]["proje"]["ad"], "asansor": adlari(gg)} for _ad in cizimleri(gg)] if gg else []
