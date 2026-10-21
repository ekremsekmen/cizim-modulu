# -*- coding: utf-8 -*-
"""
KUYU ÜSTÜ PLANI  ( makine dairesiz asansör — kuyu tepesinden yatay kesit )

Makine dairesi olmayan asansörde makine kuyunun tepesindedir;  bu plan
referans projenin MRL paftasındaki "Machine Room" çiziminin karşılığıdır.  Kuyu
planının duvarlarını, raylarını ve konsollarını AYNEN kullanır;  kabin ve
karşı ağırlık yalnız izleriyle ( kesik ) görünür.  Üstüne gelenler:

  · makine ve tahrik kasnağı  ( karşı ağırlığın üstünde )
  · 2:1 askıda halatların kuyu tepesine bağlandığı yerler
  · hız regülatörü  ( kuyu dibindeki gergi kasnağının tam üstünde )
  · ACİL KURTARMA VE TEST PANOSU  kuyunun dışında, en üst katta kapının
    yanında, önünde çalışma alanıyla          TS EN 81-20 m.5.2.6.6

HALATLAR DÜŞEY İNER.  Tahrik kasnağının bir teğeti kabinin yakın halatının
hizasındadır ( kabin kasnağının dış teğeti );  öbür teğetinden inen halat
karşı ağırlık kasnağının teğetine düşmelidir.  Düşmüyorsa sapma ölçüyle
gösterilir — bu referans projenin paftasında birebir tutar ( 370 − 240 = 130 ).

Çizilen düzenler ( duzen_hatalari ):  karşı ağırlık yanda 2:1 — kasnaklar
kabinin altında ( ofisin ve referans projenin düzeni ) ya da üstünde;  ağırlık
arkada 2:1 kabin üstünde ( çapraz kasnaklar — _arka );  makine dairesinde 1:1
( ağırlık yanda ya da arkada — _dogrudan ).  Makine ağırlık raylarına oturan
şasede ya da ( "Bina yapısına" ) kuyunun genişliğince duvardan duvara iki
kirişte ( LiftDesigner 1250 KG ).  Öteki düzenleri doğrulama açıkça reddeder.
"""

from temel import cumle_basi, eleman_kutusu, ortusur, sayi_mi
from cizim import sorunlu
from cizim import sorun
from cizim import istek_onbellegi
from cizim import eleman
from cizim import kisaltmalar
from cizim import uslup
from cizim import izli
from cizim import geometri
from cizim import girdi
from cizim import kuyu_dibi
from cizim import makine
from cizim import baglantilar
from cizim import sabitler
from cizim import arka_aski
from cizim import parcalar

#  TS EN 81-20 m.5.2.6.6.4 → m.5.2.6.3.2.1 a:  panonun önünde en az 0,70 m
#  derinlikte, en az 0,50 m ya da pano eni kadar genişlikte boş alan.
CALISMA_DERINLIK = 700.0
CALISMA_EN_ASGARI = 500.0
YANLAR = ("Sol", "Sağ")
_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA", "EKSEN")


class Duzlem:
    """HALAT DÜZLEMİ:  tahrik kasnağının iki halat inişi, kabin tarafının ve
    karşı ağırlık tarafının halatları aynı düşey düzlemdedir.  u düzlem boyunca,
    v düzleme dik ( planda ).  Karşı ağırlık yandaysa düzlem kuyu genişliği
    boyuncadır ( u = x ), arkadaysa derinliği boyunca ( u = y ).  Makine ve
    saptırma kasnağı u = x düzenindeki kuralla kurulur, arkadaki ağırlıkta
    x ↔ y takas edilir ( makine.takas ):  kasnak ekseni hep düzleme diktir."""

    def __init__(self, yon, v0):
        self.yon, self.v0 = yon, izli.sayi(v0)

    @property
    def eksen(self):  # kasnak ekseni ( düzleme dik )
        return "y" if self.yon == "x" else "x"

    def p(self, u, v=None):
        v = self.v0 if v is None else v
        return (u, v) if self.yon == "x" else (v, u)

    def u(self, nokta):
        return nokta[0] if self.yon == "x" else nokta[1]

    def v(self, nokta):
        return nokta[1] if self.yon == "x" else nokta[0]

    def kutu(self, u0, u1, v0, v1):
        u0, u1 = sorted((u0, u1))
        v0, v1 = sorted((v0, v1))
        return (u0, v0, u1, v1) if self.yon == "x" else (v0, u0, v1, u1)

    def kanonik(self, kutu):
        """Gerçek kutu → ( u0, v0, u1, v1 )."""
        return kutu if self.yon == "x" else (kutu[1], kutu[0], kutu[3], kutu[2])

    def parcalar(self, kutular):
        return kutular if self.yon == "x" else makine.takas(kutular)


def regulator_plani(rc, u0, u1, v0, v1):
    """Regülatörün kendi ekseninden ( u, v — parcalar.regulator_geometrisi )
    plana:  u kuyunun derinliği boyunca ( halat düzlemi ), v duvardan kuyuya —
    mekanizma ve kontak kuyunun içine bakar ( kabin üstünden bakılır ), ayağın
    kısa ucu duvara."""
    xa, xb = rc["x"] - rc["yan"] * v0, rc["x"] - rc["yan"] * v1
    return (min(xa, xb), rc["y"] + u0, max(xa, xb), rc["y"] + u1)


def _regulator(g, S, taban, kabin, G):
    """Hız regülatörü:  kuyu dibindeki gergi kasnağının tam üstü — seçilen
    yandaki kabin rayının hizasında, ray ekseninden regülatör kaçıklığı kadar.
    Kasnak ve gövde gerçek ölçüleriyle ( parcalar.regulator_geometrisi );
    ayağı ( konsol ) gövdeden duvara."""
    kd = g["kuyu_dibi"]
    ry = g["kabin_ray"]["kapi_arasi"]
    raylar = sorted((eleman_kutusu(el) for el in taban if el.get("ad") == "kabin_ray"), key=lambda r: r[0])
    sag_reg = kd["regulator_yan"] == "Sağ"
    rx = (raylar[-1][0] + raylar[-1][2]) / 2.0 if sag_reg else (raylar[0][0] + raylar[0][2]) / 2.0
    #  Rayın iki parçası ( flanş + gövde ) aynı hizada;  birleşik orta
    ray_parca = [r for r in raylar if (r[0] > kabin[2] - 1 if sag_reg else r[2] < kabin[0] + 1)]
    if ray_parca:
        rx = (min(r[0] for r in ray_parca) + max(r[2] for r in ray_parca)) / 2.0
    rgy = ry + kd["regulator_kaciklik"]
    rc = {
        "x": rx,
        "y": rgy,
        "yan": 1.0 if sag_reg else -1.0,
        "geo": parcalar.regulator_geometrisi(kd["regulator_kasnak_capi"]),
    }
    reg_kasnak = regulator_plani(rc, *rc["geo"]["kasnak"])
    reg_govde = regulator_plani(rc, *rc["geo"]["zarf"])
    reg_ayak = (
        (reg_govde[2], reg_govde[1], G, reg_govde[3])
        if sag_reg
        else (0.0, reg_govde[1], reg_govde[0], reg_govde[3])
    )
    return rx, rgy, reg_kasnak, reg_govde, reg_ayak, rc


def _reg_halat_payi(g):
    """Regülatör halatının ekseninden kirişe en az uzaklık:  halat payı + yarıçap."""
    return girdi.HALAT_PAYI + (g["kuyu_dibi"].get("regulator_halat_capi") or 0.0) / 2.0


def _reg_halat_kutusu(g, reg_kasnak):
    """REGÜLATÖR HALATLARI kasnağın düzleminde ( derinlik boyunca ) iki teğetinden
    iner:  kasnak kutusunun y uçları.  Kirişler bu kutuyu payıyla içine alır
    ( 15 Eki:  yalnız gövde alınıyordu, halat kirişin yüzüne düşüyordu — r095 )."""
    p = _reg_halat_payi(g)
    return (reg_kasnak[0], reg_kasnak[1] - p, reg_kasnak[2], reg_kasnak[3] + p)


def _reg_halat_kiris_hatasi(g, reg_kasnak, kirisler):
    """Regülatör halatı ( kasnağın teğetlerinden ) duvardan duvara kirişlere halat
    payından yakın inemez — çelik kirişin içinden geçerdi.  [ ileti ]"""
    p = _reg_halat_payi(g)
    x = (reg_kasnak[0] + reg_kasnak[2]) / 2.0
    for y in (reg_kasnak[1], reg_kasnak[3]):
        if any(k[0] - p < x < k[2] + p and k[1] - p < y < k[3] + p for k in kirisler):
            return [
                sorun.Sorun(
                    f"Regülatör halatı ( x = {x:g}, y = {y:g} ) makinenin duvardan duvara kirişine "
                    f"{girdi.HALAT_PAYI:g} mm'den yakın iniyor — regülatör kaçıklığını ya da yanını "
                    "değiştirin.",
                    ("regulator_halati",) + _PARCA["regülatör"] + _KIRISLER,
                    "kuyu_ustu",
                )
            ]
    return []


def duzen_hatalari(g):
    """Askı düzeni ile karşı ağırlığın yerinin çizilebilir bir birleşim olup
    olmadığı.  Çizilenler:  yandaki ağırlıkla 2:1 ( kasnaklar kabinin altında ya
    da üstünde ), arkadaki ağırlıkla 2:1 kabin üstünde, makine dairesinde 1:1
    ( ağırlık yanda ya da arkada — ofisin 12744-3 ve 477-8 projeleri ).  Öbürleri gerçek projelerde yoktur, sebebiyle
    reddedilir ( düşey kesit de ilk bunu söyler ).  Döner:  hata listesi."""
    hata = []
    duzen = (g.get("aski") or {}).get("duzen")
    yer = (g.get("agirlik") or {}).get("yeri")
    oda_ici = (g.get("makine") or {}).get("yeri") == "Makine dairesi"
    if duzen == "Doğrudan" and not oda_ici:
        hata.append(
            "Makine dairesiz ( kuyu üstü ) tesiste 1:1 askı çizilmez:  tahrik kasnağı "
            "kabinin tam üstünde olur, kabin kuyu tepesine çıkamaz — makine dairesiz "
            "asansörler 2:1 askılıdır ( ofisin ve referans projenin MRL'leri ).  Askı "
            "oranını 2 seçin ya da makine dairesi olsun."
        )
    elif duzen not in ("Kabin altı", "Kabin üstü", "Doğrudan"):
        hata.append(f"aski.duzen:  ( 'Kabin altı', 'Kabin üstü', 'Doğrudan' ) içinden olmalı ( {duzen!r} ).")
    if yer == "Arka" and duzen == "Kabin altı":
        hata.append(
            sorun.Sorun(
                "Arkadaki karşı ağırlıkla 2:1 askı kabin üstünde çizilir ( kasnaklar çapraz — "
                "ofisin 12495-18 ve 1275 projeleri de kabin üstü ):  askı kasnaklarının yeri "
                "için 'Kabin üstü' seçin ya da ağırlığı yana alın.",
                ("kabin_kasnak", "kabin_kasnak_ucu", "agirlik_blok"),
                "kuyu_plani",
            )
        )
    elif yer not in YANLAR + ("Arka",):
        hata.append(f"agirlik.yeri:  ( 'Sol', 'Sağ', 'Arka' ) içinden olmalı ( {yer!r} ).")
    return hata


def _girdi_hatalari(g, acil_pano):
    """Yerleşimin kurulamayacağı girdi eksikleri:  [ ileti ]."""
    ku, kd, ag = g.get("kuyu_ustu") or {}, g.get("kuyu_dibi") or {}, g["agirlik"]
    mk = g.get("makine") or {}
    duzen = (g.get("aski") or {}).get("duzen")
    hata = duzen_hatalari(g)
    if duzen != "Doğrudan" and not (sayi_mi(ag.get("kasnak_capi")) and ag["kasnak_capi"] > 0):
        hata.append("agirlik.kasnak_capi:  2:1 askıda karşı ağırlık kasnağının çapı girilmeli.")
    if not (sayi_mi(mk.get("tahrik_kasnak_capi")) and mk["tahrik_kasnak_capi"] > 0):
        hata.append(f"makine.tahrik_kasnak_capi: sayı olmalı ( {mk.get('tahrik_kasnak_capi')!r} ).")
    if mk.get("tip") not in makine.TIPLER:
        hata.append(f"makine.tip: {makine.TIPLER} içinden olmalı ( {mk.get('tip')!r} ).")
    elif mk["tip"] == "Dişli" and mk.get("yeri", "Kuyu üstü") == "Kuyu üstü":
        #  LiftDesigner'ın dişli makinesi 1.316 × 590:  kuyu tepesindeki,
        #  karşı ağırlık rayları arasındaki şaseye sığmaz;  makine dairesiz
        #  asansörler dişlisizdir ( ofisin 4815-6'sı ve referans proje de öyle ).
        hata.append(
            "Makine dairesiz ( kuyu üstü ) tesiste dişli makine çizilmez — "
            "makine.tip Dişlisiz olmalı ya da makine.yeri Makine dairesi."
        )
    aski = g.get("aski") or {}
    for alan in ("halat_adedi", "halat_capi"):
        if not (sayi_mi(aski.get(alan)) and aski[alan] > 0):
            hata.append(f"aski.{alan}: şase plakasındaki halat deliği için gerekli ( {aski.get(alan)!r} ).")
    if makine.npu(mk.get("yan_yatak")) is None:
        hata.append(
            f"makine.yan_yatak: makinenin oturduğu kirişin NPU ölçüsü ( hesap programında "
            f"'F ( yan yatak )' ) — {tuple(makine.NPU)} içinden olmalı ( {mk.get('yan_yatak')!r} )."
        )
    if acil_pano and ku.get("acil_pano_yan") not in YANLAR:
        hata.append(f"kuyu_ustu.acil_pano_yan: {YANLAR} içinden olmalı ( {ku.get('acil_pano_yan')!r} ).")
    for alan in ("regulator_kaciklik", "regulator_kasnak_capi"):
        if not sayi_mi(kd.get(alan)):
            hata.append(f"kuyu_dibi.{alan}: regülatör onun tam üstündedir, girilmeli.")
    if kd.get("regulator_yan") not in YANLAR:
        hata.append("kuyu_dibi.regulator_yan: regülatör gergi kasnağının tam üstündedir, girilmeli.")
    return hata


def _oda(g, yeri_sart=True):
    """Makine dairesinin odası ( kutu ) ya da None.  yeri_sart:  makine
    "Makine dairesi"nde olmalı ( 1:1 zaten yalnız makine dairesinde çizilir )."""
    md = g.get("makine_dairesi") or {}
    if yeri_sart and (g.get("makine") or {}).get("yeri") != "Makine dairesi":
        return None
    if not all(sayi_mi(md.get(a)) for a in ("x", "y", "genislik", "derinlik")):
        return None
    return (md["x"], md["y"], md["x"] + md["genislik"], md["y"] + md["derinlik"])


def _makine(mk, S, merkez, D1, kt, s, m_yon, engeller, oda_, sira, kutu, plana):
    """Makinenin parçaları ve gövdesi ( dişlide zarfı ):  ( parçalar, gövde |
    None ( dişlisiz:  çağıranınki ), s, m_yon ).

    Planda kot yalnız çizim sırası için:  kasnak merkezi 0.  Dişli makine
    ( yalnız makine dairesinde ):  dişli kutusu kasnağın iki yanından
    birinde, motor kasnak eksenine dik iki yöndan birinde — engellere
    binmeyen, odaya sığan ilk düzen ( sira:  denenecek ( s, m ) çarpanları ).
    kutu / plana:  makinenin kendi ekseninden plana ( halat düzlemi )."""
    if mk["tip"] != "Dişli":
        return (
            plana(
                makine.dislisiz(
                    merkez, D1, 2 * kt, s, S["makine_en"], S["makine_kasnak_boslugu"] + S["makine_boy"]
                )
            ),
            None,
            s,
            m_yon,
        )
    for s_, m_ in sira(s, m_yon):
        z = kutu(makine.disli_zarfi(merkez, s_, m_))
        if not any(ortusur(z, p) for p in engeller) and (
            oda_ is None or (oda_[0] <= z[0] and oda_[1] <= z[1] and z[2] <= oda_[2] and z[3] <= oda_[3])
        ):
            s, m_yon = s_, m_
            break
    return (
        plana(makine.disli(merkez, D1, 2 * kt, s, m_yon)),
        kutu(makine.disli_zarfi(merkez, s, m_yon)),
        s,
        m_yon,
    )


def _sira_once_govde(s, m):
    return ((s, m), (-s, m), (s, -m), (-s, -m))


def _sira_once_motor(s, m):
    return ((s, m), (s, -m), (-s, m), (-s, -m))


def _acil_pano(g, S):
    """ACİL KURTARMA VE TEST PANOSU:  en üst kattaki kapının yanında, kuyunun
    dışında;  önündeki çalışma alanıyla.  ( pano, çalışma alanı )"""
    kp, don = g["kapi"], g["kuyu"]["duvar_on"]
    x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
    kasa, pe, pd = S["kasa_yan"], S["acil_pano_en"], S["acil_pano_derinlik"]
    if (g.get("kuyu_ustu") or {}).get("acil_pano_yan") == "Sol":
        pano = (x0 - kasa - pe, -don - pd, x0 - kasa, -don)
    else:
        pano = (x1 + kasa, -don - pd, x1 + kasa + pe, -don)
    ce = max(CALISMA_EN_ASGARI, pe)
    pm = (pano[0] + pano[2]) / 2.0
    return pano, (pm - ce / 2.0, pano[1] - CALISMA_DERINLIK, pm + ce / 2.0, pano[1])


#  Sorunların parçaları ( sorun.Sorun — ekran kuyu üstü planında işaretler )
_PARCA = {
    "makine": ("makine", "makine_sasesi"),
    "tahrik kasnağı": ("tahrik_kasnagi",),
    "ağırlık halat bağlantısı": ("agirlik_baglanti",),
    "kabin halat bağlantısı": ("kabin_baglanti",),
    "regülatör": ("regulator", "regulator_kasnak"),
}
_KIRISLER = ("makine_sasesi",)


def _cakismalar(kutular, oda_, G, D):
    """ÇAKIŞMALAR:  kuyu üstündeki parçalar kuyunun içinde ( makine dairesinde
    makine odanın içindedir — makine_dairesi denetler ) ve birbirine binmeden."""
    hata = []
    for ad, p in kutular.items():
        #  Makine dairesinde makine, kasnak ve regülatör odanın döşemesindedir:
        #  kuyunun izi değil oda ve tabliye sınırlar ( makine_dairesi._oda_hatalari )
        if oda_ is not None and ad in ("makine", "tahrik kasnağı", "regülatör"):
            continue
        if p[0] < 0 or p[1] < 0 or p[2] > G or p[3] > D:
            hata.append(
                sorun.Sorun(
                    f"{cumle_basi(ad)} kuyunun dışına taşıyor.",
                    _PARCA.get(ad, ()),
                    "kuyu_ustu",
                    fark=sorun.icinde(p, G, D),
                )
            )
    adlar = list(kutular)
    for i, a in enumerate(adlar):
        for b in adlar[i + 1 :]:
            if {a, b} == {"makine", "tahrik kasnağı"}:
                continue
            if ortusur(kutular[a], kutular[b]):
                hata.append(
                    sorun.Sorun(
                        f"Kuyu üstünde {a} ile {b} üst üste biniyor.",
                        _PARCA.get(a, ()) + _PARCA.get(b, ()),
                        "kuyu_ustu",
                        fark=sorun.ayrik(kutular[a], kutular[b]),
                    )
                )
    return hata


def _taban(g, S):
    """Kuyunun planı ( kapı düzeyi olmadan ) ve içindeki kabinle karşı ağırlığın kutuları."""
    taban = geometri.plan(g, S, kapi_duzeyi=False)
    kabin = eleman_kutusu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    blok = eleman_kutusu(next(el for el in taban if el.get("ad") == "agirlik_blok"))
    return taban, kabin, blok


def _iki_bir_cakismalari(govde, kasnak, agirlik_baglanti, kabin_baglanti, reg_govde, oda_, G, D):
    """2:1 askıda kuyu üstündeki parçaların çakışmaları ( _cakismalar )."""
    return _cakismalar(
        {
            "makine": govde,
            "tahrik kasnağı": kasnak,
            "ağırlık halat bağlantısı": agirlik_baglanti,
            "kabin halat bağlantısı": kabin_baglanti,
            "regülatör": reg_govde,
        },
        oda_,
        G,
        D,
    )


def _aynen(x):
    return x


@istek_onbellegi.sakla
def yerlesim(g, cizim_sabitleri=None, acil_pano=True):
    """Makinenin, halatların, bağlantıların ve regülatörün yeri.

    Makine daireli projede de AYNEN kullanılır ( makine_dairesi.py ):  makine
    kuyunun üstündeyse halatlar aynı noktalardan iner, yalnız bu kez döşeme
    deliklerinden geçer.  acil_pano = False iken acil kurtarma panosu
    aranmaz — makine dairesinde bütün düzenekler odanın içindedir.
    """
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    hata = _girdi_hatalari(g, acil_pano)
    if hata:
        return {"hata": hata}
    ag, mk = g["agirlik"], g.get("makine") or {}
    if (g.get("aski") or {}).get("duzen") == "Doğrudan":
        return _dogrudan(g, S, mk, ag)
    if ag.get("yeri") == "Arka":
        return _arka(g, S, mk, ag, acil_pano)
    return _yandaki_agirlik(g, S, mk, ag, acil_pano)


def _yandaki_agirlik(g, S, mk, ag, acil_pano):
    """YANDAKİ AĞIRLIKLA 2:1:  halatlar kuyu genişliği boyunca ( y0 çizgisi )."""
    hata = []
    taban, kabin, blok = _taban(g, S)
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    sol = ag["yeri"] == "Sol"
    ry = g["kabin_ray"]["kapi_arasi"]
    ag_y = ry + ag["eksen_kaciklik"]
    ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]

    #  ── HALATLAR ─────────────────────────────────────────────────────
    (xl, y0), (xr, _) = geometri.halat_konumlari(g, S)
    yakin, uzak = (xl, xr) if sol else (xr, xl)
    D1 = mk["tahrik_kasnak_capi"]
    y_ = -1.0 if sol else 1.0  # kabinden ağırlığa doğru
    ag_dusus_x = yakin + y_ * D1  # tahrik kasnağının öbür teğeti
    R = ag["kasnak_capi"] / 2.0
    teget1, teget2 = sorted((ag_y - R, ag_y + R), key=lambda t: abs(t - y0))

    #  ── MAKİNE:  tahrik kasnağı + gövde ───────────────────────────────
    #  Kasnak halat çizgisinde;  gövde kasnağın ağırlık eksenine bakan
    #  tarafında ( referans proje:  kasnak 865–970, gövde 985–1.264 ).
    kx0, kx1 = sorted((yakin, ag_dusus_x))
    kt = S["tahrik_kasnak_kalinlik"] / 2.0
    kasnak = (kx0, y0 - kt, kx1, y0 + kt)
    s = 1.0 if ag_y >= y0 else -1.0
    kmx = (kx0 + kx1) / 2.0
    g0 = y0 + s * (kt + S["makine_kasnak_boslugu"])
    g1 = g0 + s * S["makine_boy"]
    govde = (kmx - S["makine_en"] / 2.0, min(g0, g1), kmx + S["makine_en"] / 2.0, max(g0, g1))

    kab_r, sase = _yandaki_sase(S, taban, sol, G)
    agirlik_baglanti, kabin_baglanti = _yandaki_baglantilar(S, y0, teget2, s, ex, uzak, y_)

    #  ── REGÜLATÖR:  gergi kasnağının tam üstü ─────────────────────────
    rx, rgy, reg_kasnak, reg_govde, reg_ayak, reg_cizim = _regulator(g, S, taban, kabin, G)
    pano, calisma = _acil_pano(g, S) if acil_pano else (None, None)

    #  ── MAKİNENİN PARÇALARI ( makine.py ):  önce ağırlık tarafı ve kuyunun ortası
    m_yon = 1.0 if kmx < G / 2.0 else -1.0
    oda_ = _oda(g)
    makine_parcalari, zarf, s, m_yon = _makine(
        mk,
        S,
        (kmx, y0, 0.0),
        D1,
        kt,
        s,
        m_yon,
        (agirlik_baglanti, kabin_baglanti, reg_govde),
        oda_,
        _sira_once_govde,
        _aynen,
        _aynen,
    )
    govde = zarf or govde
    hata += _iki_bir_cakismalari(govde, kasnak, agirlik_baglanti, kabin_baglanti, reg_govde, oda_, G, D)
    duvar = mk.get("kiris") == "duvar" and oda_ is None
    if duvar:
        kutular = (kasnak, govde, agirlik_baglanti, kabin_baglanti, reg_govde)
        sase = _yandaki_kiris_sasesi(g, mk, kutular, reg_kasnak, hata)
    aski = g["aski"]
    return {
        "taban": taban,
        "kabin": kabin,
        "blok": blok,
        "halatlar": [(xl, y0), (xr, y0)],
        "ag_dusus": (ag_dusus_x, y0),
        "ag_teget": (ex, teget1),
        "ag_teget2": (ex, teget2),
        "sapma": (ag_dusus_x - ex, y0 - teget1),
        "kasnak": kasnak,
        "govde": govde,
        "agirlik_baglanti": agirlik_baglanti,
        "makine": makine_parcalari,
        "m_yon": m_yon,
        "s": s,
        "sase": sase,
        "duvardan_duvara": duvar,
        "kiris_yonu": "x" if duvar else "y",
        "tip": mk["tip"],
        "yan_yatak": makine.npu(mk["yan_yatak"]),
        #  Şaseden aşağı inen halatların delikleri ( plakaya düşenler açılır ):
        #  tahrik kasnağının iki yanı ve karşı ağırlık bağlantısı
        "sase_delikleri": [
            makine.halat_deligi(x_, y0, aski["halat_adedi"], aski["halat_capi"], S["halat_delik_payi"])
            for x_ in (yakin, ag_dusus_x)
        ]
        + [
            makine.halat_deligi(
                ex, teget2, aski["halat_adedi"], aski["halat_capi"], S["halat_delik_payi"], "x"
            )
        ],
        "kabin_baglanti": kabin_baglanti,
        "halat_konsolu": baglantilar.halat_konsolu(kabin_baglanti, kab_r[-1] if sol else kab_r[0], 0),
        "reg_kasnak": reg_kasnak,
        "reg_govde": reg_govde,
        "reg_ayak": reg_ayak,
        "reg_cizim": reg_cizim,
        "pano": pano,
        "calisma": calisma,
        "D1": D1,
        "rgx": rx,
        "rgy": rgy,
        "yakin": yakin,
        "uzak": uzak,
        "ag_y": ag_y,
        "ry": ry,
        "ex": ex,
        "ag_eksen_x": ex,
        "hata": hata,
        "S": S,
    }


def _yandaki_sase(S, taban, sol, G):
    """MAKİNE ŞASESİ ( makine dairesizde ):  karşı ağırlık rayları boyunca,
    duvardan ağırlık tarafındaki kabin rayına ( referans proje:  şase kabin
    rayına ve ağırlık raylarına oturur ).  ( sıralı kabin rayları, şase )"""
    kab_r = sorted(kuyu_dibi.raylari_topla(taban, "kabin_ray"), key=lambda r: r[0])
    ag_r = kuyu_dibi.raylari_topla(taban, "agirlik_ray")
    yakin_ray = kab_r[0] if sol else kab_r[-1]
    sase_y = (
        min(r[1] for r in ag_r) - S["makine_sase_ray_payi"],
        max(r[3] for r in ag_r) + S["makine_sase_ray_payi"],
    )
    if sol:
        return kab_r, (S["makine_sase_duvar"], sase_y[0], yakin_ray[0], sase_y[1])
    return kab_r, (yakin_ray[2], sase_y[0], G - S["makine_sase_duvar"], sase_y[1])


def _yandaki_kiris_sasesi(g, mk, kutular, reg_kasnak, hata):
    """Yandaki ağırlıkta duvardan duvara kirişler:  parçaları ve regülatörün
    halatlarını ( payıyla ) içine alır;  kuyunun derinliğine sığmalı."""
    k = g["kuyu"]
    sase = _yandaki_duvar_kirisleri(mk, k["genislik"], *kutular, _reg_halat_kutusu(g, reg_kasnak))
    if sase[1] < 0.0 or sase[3] > k["derinlik"]:
        hata.append(
            sorun.Sorun(
                "Makinenin duvardan duvara kirişleri kuyunun derinliğine sığmıyor.", _KIRISLER, "kuyu_ustu"
            )
        )
    b = makine.npu(mk["yan_yatak"])["b"]
    hata += _reg_halat_kiris_hatasi(
        g, reg_kasnak, [(sase[0], sase[1], sase[2], sase[1] + b), (sase[0], sase[3] - b, sase[2], sase[3])]
    )
    return sase


def _arka_kiris_hatalari(g, sase, b, reg_kasnak):
    """Arkadaki ağırlıkta duvardan duvara kirişler ( derinlik boyunca ):  kuyunun
    genişliğine sığmalı, regülatör halatı onlara değmemeli."""
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    hata = []
    if not (0.0 <= sase[0] and sase[2] <= G):
        hata.append(
            sorun.Sorun(
                "Makinenin duvardan duvara kirişleri kuyunun genişliğine sığmıyor.", _KIRISLER, "kuyu_ustu"
            )
        )
    return hata + _reg_halat_kiris_hatasi(
        g, reg_kasnak, [(sase[0], 0.0, sase[0] + b, D), (sase[2] - b, 0.0, sase[2], D)]
    )


def _yandaki_duvar_kirisleri(mk, G, *kutular):
    """YANDAKİ AĞIRLIKTA BİNA YAPISINA ( "Makine yükünün yolu" — LiftDesigner 1250 KG ):
    iki kiriş kuyunun GENİŞLİĞİNCE, uçları yan duvarlarda.  Kuyu tepesindeki
    parçaları — tahrik kasnağı, makine gövdesi, iki halat bağlantısı, regülatör —
    İÇİNE ALIR:  halatlar kirişlerin arasından iner, parçalar aradaki plakalara
    oturur.  Arkadaki ağırlıktaki gibi kasnağın iki yanına simetrik konamaz:
    ağırlık kasnağı 90° dönüktür ( referans proje ), bağlantısının halatı kasnağın
    halatlarından ağırlık kasnağı çapı kadar uzaktadır ve simetrik kirişin
    gövdesine düşerdi;  kabin bağlantısı ve regülatör de kirişlerin kotundadır.
    ( x0 , y0 , x1 , y1 ) — kirişlerin dış yüzleri."""
    b = makine.npu(mk["yan_yatak"])["b"]
    ic0 = min(k[1] for k in kutular if k)
    ic1 = max(k[3] for k in kutular if k)
    return (0.0, ic0 - b, G, ic1 + b)


def _yandaki_baglantilar(S, y0, teget2, s, ex, uzak, y_):
    """HALAT BAĞLANTILARI ( yandaki ağırlık ):  ağırlık tarafı ağırlık
    kasnağının öbür teğetinin üstünde;  plaka halattan kabine doğru uzanır.
    Kabin tarafı kabinin uzak halatının üstünde, kabin rayının başına bağlı;
    plaka halattan kabine doğru.  ( ağırlık bağlantısı, kabin bağlantısı )"""
    ab_y0 = teget2 - s * S["agirlik_baglanti_y"]
    ab_y1 = ab_y0 + s * S["agirlik_baglanti_boy"]
    ab_x0 = ex + y_ * S["agirlik_baglanti_x"]
    ab_x1 = ab_x0 - y_ * S["agirlik_baglanti_en"]
    kb_x0 = uzak + y_ * S["kabin_baglanti_x"]
    kb_x1 = kb_x0 - y_ * S["kabin_baglanti_en"]
    return (min(ab_x0, ab_x1), min(ab_y0, ab_y1), max(ab_x0, ab_x1), max(ab_y0, ab_y1)), (
        min(kb_x0, kb_x1),
        y0 - S["kabin_baglanti_boy"] / 2.0,
        max(kb_x0, kb_x1),
        y0 + S["kabin_baglanti_boy"] / 2.0,
    )


def _dogrudan(g, S, mk, ag):
    """1:1 ASKI ( makine dairesinde ):  halatlar kabin şasesinin üst kirişinin
    ortasındaki bağlantıdan tahrik kasnağına çıkar, öbür teğetten — halat aralığı
    kasnak çapından büyükse saptırma kasnağından ( makine_dairesi ) — karşı
    ağırlığın ortasındaki bağlantıya iner ( LiftDesigner 12744-3 "kasnak
    düzenlemesi":  kabin halatı tahrik kasnağının teğetinden, ağırlık halatı
    saptırma kasnağının dış teğetinden düşey iner ).  Kuyu tepesinde halat
    bağlantısı yoktur:  halatlar kabinde ve ağırlıkta biter.

    Halat düzlemi ( Duzlem ) ağırlık yandaysa kuyu genişliği, arkadaysa
    derinliği boyuncadır ( ofisin 12744-3'ü ve 477-8'in sağdaki asansörü:
    ağırlık arkada ).  Kabin bağlantısı düzlemin üstündedir;  karşı ağırlığın
    bağlantısı düzlemin dışında kalırsa halat sapması ölçüyle gösterilir."""
    hata = []
    taban, kabin, blok = _taban(g, S)
    k, kb, a = g["kuyu"], g["kabin"], g["aski"]
    G, D = k["genislik"], k["derinlik"]
    ry = g["kabin_ray"]["kapi_arasi"]
    #  Kabin bağlantısı:  kuyu planındaki askı noktası ( geometri.plan )
    hx = G / 2.0 + kb["kaciklik_y"]
    hy = kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0 + a.get("nokta_kaciklik", 0)
    #  Karşı ağırlığın bağlantısı:  çerçevenin ortası
    ax, ay = (blok[0] + blok[2]) / 2.0, (blok[1] + blok[3]) / 2.0
    if ag["yeri"] in YANLAR:
        d = Duzlem("x", hy)
    else:
        d = Duzlem("y", hx)
    uk, ua = d.u((hx, hy)), d.u((ax, ay))
    y_ = 1.0 if ua >= uk else -1.0  # kabinden ağırlığa doğru
    D1 = mk["tahrik_kasnak_capi"]
    ud = uk + y_ * D1  # tahrik kasnağının öbür teğeti

    #  ── MAKİNE:  tahrik kasnağı + gövde ( 2:1'deki kural, düzlemin içinde ) ──
    kt = S["tahrik_kasnak_kalinlik"] / 2.0
    kasnak = d.kutu(uk, ud, d.v0 - kt, d.v0 + kt)
    s = 1.0 if d.v((ax, ay)) >= d.v0 else -1.0  # gövde ağırlığın yanına
    kmu = (uk + ud) / 2.0
    g0 = d.v0 + s * (kt + S["makine_kasnak_boslugu"])
    govde = d.kutu(kmu - S["makine_en"] / 2.0, kmu + S["makine_en"] / 2.0, g0, g0 + s * S["makine_boy"])
    rx, rgy, reg_kasnak, reg_govde, reg_ayak, reg_cizim = _regulator(g, S, taban, kabin, G)
    m_yon = 1.0 if kmu < (G if d.yon == "x" else D) / 2.0 else -1.0
    makine_parcalari, zarf, s, m_yon = _makine(
        mk,
        S,
        (kmu, d.v0, 0.0),
        D1,
        kt,
        s,
        m_yon,
        (reg_govde,),
        _oda(g, yeri_sart=False),
        _sira_once_govde,
        lambda zk: d.kutu(zk[0], zk[2], zk[1], zk[3]),
        d.parcalar,
    )
    govde = zarf or govde
    if ortusur(kasnak, reg_govde) or ortusur(govde, reg_govde):
        hata.append(
            sorun.Sorun(
                "Makine dairesinde makine ile regülatör üst üste biniyor.",
                _PARCA["makine"] + _PARCA["regülatör"],
                "makine_dairesi",
            )
        )
    return {
        "dogrudan": True,
        "duzlem": d,
        "y_": y_,
        "taban": taban,
        "kabin": kabin,
        "blok": blok,
        "halatlar": [(hx, hy)],
        "kabin_nokta": (hx, hy),
        "ag_nokta": (ax, ay),
        "ag_dusus": d.p(ud),
        "sapma": (ud - ua, d.v0 - d.v((ax, ay))),
        "kasnak": kasnak,
        "govde": govde,
        "agirlik_baglanti": None,
        "kabin_baglanti": None,
        "makine": makine_parcalari,
        "m_yon": m_yon,
        "s": s,
        "sase": None,
        "tip": mk["tip"],
        "yan_yatak": makine.npu(mk["yan_yatak"]),
        "sase_delikleri": [],
        "reg_kasnak": reg_kasnak,
        "reg_govde": reg_govde,
        "reg_ayak": reg_ayak,
        "reg_cizim": reg_cizim,
        "pano": None,
        "calisma": None,
        "D1": D1,
        "rgx": rx,
        "rgy": rgy,
        "ry": ry,
        "hata": hata,
        "S": S,
    }


def _arka(g, S, mk, ag, acil_pano):
    """ARKADAKİ AĞIRLIKLA 2:1 ( kabin üstü, çapraz — arka_aski ):  tahrik
    kasnağının düzlemi derinlik boyunca ( Duzlem "y", x = xk ):  inişleri
    ağırlık kasnağının teğetinde ( W ) ve D1 önünde ( P ).  Makinenin gövdesi
    ağırlık kasnağının merkezinden uzağa uzanır.  Bağlantılar:  ağırlığınki
    ağırlık kasnağının öbür teğetinde ( Hw ), kabininki çapraz düzlemin ön
    ucunda ( H ).

    Makine dairesizde makine DUVARDAN DUVARA iki kirişe oturur ( kullanıcı
    kararı — 12495-18;  karar 3'ün platformu ):  kirişler derinlik boyunca ön
    duvarın iç yüzünden arka duvarınkine, tahrik kasnağının İKİ YANINDA
    SİMETRİK — makinenin yükü ( kasnaktaki halat kuvvetleri ) iki kirişe eşit
    biner ( hesabın F / 2'si ).  Referans projede kasnak kirişlerin dışında,
    150 mm taşkındı:  yakın kiriş yükün 1,6 katını taşır, uzak kiriş kalkardı."""
    A = arka_aski.geometri(g, S)
    if "P" not in A:
        return {"hata": A["hata"]}
    hata = list(A["hata"])
    taban, kabin, blok = _taban(g, S)
    k, a = g["kuyu"], g["aski"]
    G, D = k["genislik"], k["derinlik"]
    ry = g["kabin_ray"]["kapi_arasi"]
    D1, xk, yon = A["D1"], A["xk"], A["yon"]
    d = Duzlem("y", xk)
    (px, py), (hx, hy) = A["P"], A["H"]
    wy = A["W"][1]

    #  ── MAKİNE:  tahrik kasnağı + gövde ( düzlemin içinde, _dogrudan'daki kural ) ──
    kt = S["tahrik_kasnak_kalinlik"] / 2.0
    kasnak = d.kutu(py, wy, xk - kt, xk + kt)
    kmu = (py + wy) / 2.0
    s = yon  # gövde ağırlık kasnağından uzağa
    g0 = xk + s * (kt + S["makine_kasnak_boslugu"])
    govde = d.kutu(kmu - S["makine_en"] / 2.0, kmu + S["makine_en"] / 2.0, g0, g0 + s * S["makine_boy"])
    rx, rgy, reg_kasnak, reg_govde, reg_ayak, reg_cizim = _regulator(g, S, taban, kabin, G)
    oda_ = _oda(g)
    makine_parcalari, zarf, s, m_yon = _makine(
        mk,
        S,
        (kmu, xk, 0.0),
        D1,
        kt,
        s,
        1.0 if kmu < D / 2.0 else -1.0,
        (reg_govde,),
        oda_,
        _sira_once_motor,
        lambda zk: d.kutu(zk[0], zk[2], zk[1], zk[3]),
        d.parcalar,
    )
    govde = zarf or govde

    wx = A["Hw"][0]
    agirlik_baglanti, kabin_baglanti = _arka_baglantilar(S, wx, wy, yon, hx, hy)
    kab_r = sorted(kuyu_dibi.raylari_topla(taban, "kabin_ray"), key=lambda r: r[0])
    yakin_ray = kab_r[0] if hx < (kabin[0] + kabin[2]) / 2.0 else kab_r[-1]

    #  ── MAKİNE ŞASESİ ( makine dairesizde ):  duvardan duvara iki kiriş ──
    yy = makine.npu(mk["yan_yatak"])
    ic = kt + S["makine_kasnak_boslugu"] + S["makine_boy"]  # kirişlerin iç yüzü
    sase = (xk - ic - yy["b"], 0.0, xk + ic + yy["b"], D)
    n_, dh_, pay_ = a["halat_adedi"], a["halat_capi"], S["halat_delik_payi"]
    pano, calisma = _acil_pano(g, S) if acil_pano else (None, None)
    hata += _iki_bir_cakismalari(govde, kasnak, agirlik_baglanti, kabin_baglanti, reg_govde, oda_, G, D)
    if oda_ is None:
        hata += _arka_kiris_hatalari(g, sase, yy["b"], reg_kasnak)
    return {
        "taban": taban,
        "kabin": kabin,
        "blok": blok,
        "capraz": A,
        "duzlem": d,
        "y_": 1.0,
        "halatlar": [A["P"], A["H"]],
        "kabin_inis": A["P"],
        "kabin_baglanti_nokta": A["H"],
        "ag_dusus": A["W"],
        "ag_teget": A["W"],
        "ag_teget2": A["Hw"],
        "ag_baglanti_eksen": "y",
        "kabin_baglanti_eksen": "x",
        "sapma": (0.0, 0.0),
        "kasnak": kasnak,
        "govde": govde,
        "agirlik_baglanti": agirlik_baglanti,
        "makine": makine_parcalari,
        "m_yon": m_yon,
        "s": s,
        "sase": sase,
        "duvardan_duvara": True,
        "kiris_yonu": "y",
        "tip": mk["tip"],
        "yan_yatak": yy,
        "sase_delikleri": [
            makine.halat_deligi(px, py, n_, dh_, pay_, "x"),
            makine.halat_deligi(xk, wy, n_, dh_, pay_, "x"),
            makine.halat_deligi(wx, wy, n_, dh_, pay_, "y"),
        ],
        "kabin_baglanti": kabin_baglanti,
        "halat_konsolu": baglantilar.halat_konsolu(kabin_baglanti, yakin_ray, 0),
        "reg_kasnak": reg_kasnak,
        "reg_govde": reg_govde,
        "reg_ayak": reg_ayak,
        "reg_cizim": reg_cizim,
        "pano": pano,
        "calisma": calisma,
        "D1": D1,
        "rgx": rx,
        "rgy": rgy,
        #  Halat düzlemi boyunca ( u = y ) koordinatlar:  kabin inişi, ağırlık inişi
        "yakin": py,
        "uzak": hy,
        "ag_y": wy,
        "ry": ry,
        #  ex düzlem boyunca ( u = y );  plandaki x ag_eksen_x ( _olculer — 15 Eki )
        "ex": wy,
        "ag_eksen_x": (blok[0] + blok[2]) / 2.0,
        "hata": hata,
        "S": S,
    }


def _arka_baglantilar(S, wx, wy, yon, hx, hy):
    """HALAT BAĞLANTILARI ( arkadaki ağırlık ):  ağırlığınki ağırlık kasnağının
    öbür teğetinin üstünde ( halat demeti ağırlık kasnağının ekseni — derinlik
    — boyunca );  kabininki çapraz düzlemin ön ucunda, o yandaki kabin rayının
    başına bağlı.  Plakalar yandaki ağırlıktakinin 90° dönüğü ( referans
    projeden ölçülmüş paylar ):  ağırlığınki halat demeti ( derinlik ) boyunca
    en, duvar tarafında halattan agirlik_baglanti_x, kasnak tarafında _y payla;
    kabininki halat demeti ( genişlik ) boyunca boy, düzlem boyunca en."""
    ay0 = wy + S["agirlik_baglanti_x"]
    ax0 = wx + yon * S["agirlik_baglanti_y"]
    ax1 = ax0 - yon * S["agirlik_baglanti_boy"]
    ke, kb_ = S["kabin_baglanti_en"] / 2.0, S["kabin_baglanti_boy"] / 2.0
    return (min(ax0, ax1), ay0 - S["agirlik_baglanti_en"], max(ax0, ax1), ay0), (
        hx - kb_,
        hy - ke,
        hx + kb_,
        hy + ke,
    )


def dogrula(g):
    hata = geometri.dogrula(g)
    #  Sorunlu kipte ( cizim/sorunlu.py ) ilk hatada durulmaz:  çare bulucu gizli
    #  kalan sorunları da görür ( uclar/care_uclari.py ).  Kip kapalıyken aynı.
    if hata and not sorunlu.acik():
        return hata
    return hata + yerlesim(g)["hata"]


def ciz(g, cizim_sabitleri=None):
    Y = yerlesim(g, cizim_sabitleri)
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    e = [el for el in Y["taban"] if el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi"]
    e += _parcalar(g, Y)
    e += _olculer(g, Y)
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e)
    tasinir = _sapma_yazisi_adaylari(e, G, D)
    if tasinir:
        geometri.yazilari_coz(e, tasinir, ek_katman=("KUYU-DUVAR", "MAKINE", "KONSOL"))
    return e


def _kutu(katman, p, ad):
    return eleman.ad(eleman.dikdortgen(katman, p[0], p[1], p[2] - p[0], p[3] - p[1]), ad)


def regulator_cizimi(e, Y):
    """Regülatör planda ( tepeden — parcalar.regulator_geometrisi ):  iki ayak ve
    Ø16 delikleri, bacakların üstündeki büküm ( kasnağın ortasını örter ), güvenlik
    kontağı;  kasnağın bükümden taşan iki ucu.  Zarflar denetimin kutularıdır
    ( reg_govde · reg_kasnak );  makine dairesi de bunu çizer."""
    rc = Y["reg_cizim"]
    geo = rc["geo"]

    def dortgen(u0, u1, v0, v1):
        x0, y0, x1, y1 = regulator_plani(rc, u0, u1, v0, v1)
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    w0, w1 = geo["bacak"]
    (b0, _), (_, b1) = geo["bacaklar"]
    ku0, ku1, kv0, kv1, _kz0, _kz1 = geo["kontak"]
    govde = _kutu("MAKINE", Y["reg_govde"], "regulator")
    govde["bicim"] = [{"noktalar": dortgen(*a)} for a in geo["ayaklar"]] + [
        {"noktalar": dortgen(w0, w1, b0, b1)},
        {"noktalar": dortgen(ku0, ku1, kv0, kv1)},
    ]
    e.append(govde)
    for u, v in geo["delikler"]:
        x, _y, _x, y = regulator_plani(rc, u, u, v, v)
        e.append(eleman.ad(eleman.daire("CIVATA", x, y, parcalar.REGULATOR_DELIK / 2.0), "regulator"))
    kasnak = _kutu("KASNAK", Y["reg_kasnak"], "regulator_kasnak")
    R, (_, _, sv0, sv1) = geo["R"], geo["kasnak"]
    if R > w1:
        kasnak["bicim"] = [{"noktalar": dortgen(-R, w0, sv0, sv1)}, {"noktalar": dortgen(w1, R, sv0, sv1)}]
    e.append(kasnak)
    #  Regülatör halatı kasnağın iki ucundan kuyu dibindeki gergiye iner ( kuyu
    #  dibi planında aynı noktalar )
    for u in (-R, R):
        x, _y, _x, y = regulator_plani(rc, u, u, 0.0, 0.0)
        e.append(eleman.ad(eleman.daire("HALAT", x, y, parcalar.REGULATOR_HALAT_SEMBOLU), "regulator_halati"))


def _parcalar(g, Y):
    """İzler, makine ve şasesi, halat bağlantıları ve halatlar, regülatör,
    acil pano ve çalışma alanı."""
    G, don = g["kuyu"]["genislik"], g["kuyu"]["duvar_on"]
    kp = g["kapi"]
    #  İzler:  kabin, karşı ağırlık, kat kapısı ( kesik )
    e = [
        _kutu("GIZLI", Y["kabin"], "kabin_izi"),
        _kutu("GIZLI", Y["blok"], "agirlik_izi"),
        _kutu("GIZLI", (kp["sol_pay"], -don, kp["sol_pay"] + kp["genislik"], 0), "kapi_izi"),
    ]
    #  Makine şasesi ( 2 yan yatak ) ve makine — parça parça ( makine.py )
    e += makine.plan(makine.plan_parcalari(Y, Y["S"]), eleman.dikdortgen, eleman.daire, eleman.cizgi)
    ks = Y["kasnak"]
    e.append(eleman.yazi((ks[0] + ks[2]) / 2.0, (ks[1] + ks[3]) / 2.0, f"ø {Y['D1']:g}", uslup.NORMAL))

    #  Halat bağlantıları, sonra halatlar ( işaret plakanın üstünde görünsün )
    e.append(_kutu("BAGLANTI", Y["agirlik_baglanti"], "agirlik_baglanti"))
    e.append(_kutu("BAGLANTI", Y["kabin_baglanti"], "kabin_baglanti"))
    if g["makine"]["yeri"] == "Kuyu üstü":
        e += makine.plan(Y["halat_konsolu"], eleman.dikdortgen, eleman.daire, eleman.cizgi)
    for p in (Y["agirlik_baglanti"], Y["kabin_baglanti"]):
        e.append(eleman.yazi((p[0] + p[2]) / 2.0, p[3] + 40, "HALAT BAĞLANTISI", uslup.NORMAL))
    for hx, hy in Y["halatlar"] + [Y["ag_dusus"], Y["ag_teget2"]]:
        e.append(eleman.ad(eleman.daire("KASNAK", hx, hy, 20), "halat"))

    #  Regülatör
    e.append(_kutu("KONSOL", Y["reg_ayak"], "regulator_ayak"))
    regulator_cizimi(e, Y)
    rg = Y["reg_govde"]
    e.append(
        eleman.yazi(
            rg[0] - 60 if rg[0] > G / 2 else rg[2] + 60,
            (rg[1] + rg[3]) / 2.0,
            "REGÜLATÖR",
            uslup.NORMAL,
            aci=90,
        )
    )

    #  Acil kurtarma ve test panosu + çalışma alanı
    pn, ca = Y["pano"], Y["calisma"]
    e.append(_kutu("PANO", pn, "acil_pano"))
    e.append(_kutu("SIGINMA", ca, "calisma_alani"))
    e.append(eleman.yazi((pn[0] + pn[2]) / 2.0, (pn[1] + pn[3]) / 2.0, "ACİL PANO", uslup.NORMAL))
    e += geometri.alan_yazisi(ca, ["ÇALIŞMA ALANI"])
    return e


def _olculer(g, Y):
    """Üst:  halatlar, kabin ve ağırlık eksenleri;  sağ:  halat çizgisi, kabin
    ray ekseni, regülatör;  sol:  ağırlık kasnağının teğetleri ve ekseni;  acil
    pano çalışma alanı;  halat sapması ( varsa )."""
    k = g["kuyu"]
    G, D, dg, dar, ds = k["genislik"], k["derinlik"], k["duvar_sag"], k["duvar_arka"], k["duvar_sol"]
    xl, xr = Y["halatlar"][0][0], Y["halatlar"][1][0]
    kx = (Y["kabin"][0] + Y["kabin"][2]) / 2.0
    u0, u1 = D + dar + 120, D + dar + 120 + geometri.SIRA_ARASI
    kasnak = (Y["kasnak"][0], Y["kasnak"][2])
    #  Kasnağın ucuyla çakışan nokta kasnağın ucu sayılır:  "ø" ölçüsü kasnağın
    #  kendisinden ölçülür ( halat ağırlığa düşey inince ucu ağırlığın ekseniyle
    #  çakışır;  kümede ilk yazılan kaldığı için ölçünün kaynağı eksenin
    #  kaynakları görünüyordu — izli.py )
    xs = sorted(
        {
            next((u for u in kasnak if u == x), x)
            for x in (0.0, G, Y["ag_eksen_x"], Y["ag_dusus"][0], xl, xr, kx)
        }
    )
    e = [
        eleman.olcu("yatay", (a, 0), (b, 0), u0, f"ø {Y['D1']:g}" if (a, b) == kasnak else None)
        for a, b in zip(xs, xs[1:])
    ]
    e.append(eleman.olcu("yatay", (0, 0), (G, 0), u1, kisaltmalar.kodlu("SW", G), ad="kuyu_genisligi"))
    s0, s1 = G + dg + 120, G + dg + 120 + geometri.SIRA_ARASI
    ys = sorted({0.0, D, Y["halatlar"][0][1], Y["ry"], (Y["reg_kasnak"][1] + Y["reg_kasnak"][3]) / 2.0})
    sag = list(zip(ys, ys[1:]))
    e += [eleman.olcu("dusey", (0, a), (0, b), s0) for a, b in sag]
    e.append(eleman.olcu("dusey", (0, 0), (0, D), s1, kisaltmalar.kodlu("SD", D), ad="kuyu_derinligi"))
    t1, t2 = Y["ag_teget"][1], Y["ag_teget2"][1]
    ys = sorted({0.0, D, t1, t2, Y["ag_y"], Y["ry"]})
    #  Sağdaki zincirin ölçtüğü aralık solda yazılmaz ( ISO 129-1:  her ölçü bir
    #  kez — 13 Eki;  iki yanda da ray ekseniyle duvar arası vardı )
    sol = [
        (a, b) for a, b in zip(ys, ys[1:]) if not any(abs(a - p) < 0.5 and abs(b - q) < 0.5 for p, q in sag)
    ]
    e += [eleman.olcu("dusey", (0, a), (0, b), -ds - 120) for a, b in sol]
    #  Acil pano çalışma alanı  ( m.5.2.6.3.2.1 a )
    ca = Y["calisma"]
    kural = (
        "Acil pano önündeki çalışma alanı:  derinliği 0,70 m, eni panonun eni ya "
        "da en az 0,50 m ( TS EN 81-20 m.5.2.6.3.2.1 a )."
    )
    e.append(eleman.olcu("yatay", (ca[0], 0), (ca[2], 0), ca[1] - 90, f"{ca[2] - ca[0]:g}", kural=kural))
    e.append(
        eleman.olcu(
            "dusey",
            (0, ca[1]),
            (0, ca[3]),
            ca[0] - 90 if ca[0] > G / 2 else ca[2] + 90,
            f"{ca[3] - ca[1]:g}",
            kural=kural,
        )
    )
    #  Halat sapması:  aynı aralığı bir zincir ölçüyorsa yazılmaz ( zincirin
    #  sürekliliği kalır — 13 Eki;  üst zincirin "335"i ile "HALAT SAPMASI 335" )
    olculen = {geometri.olcu_araligi(el) for el in e}
    dx, dy = Y["sapma"]
    if abs(dx) > 0.5:
        a, b = sorted((Y["ag_dusus"][0], Y["ag_eksen_x"]))
        if ("yatay", round(a, 1), round(b, 1)) not in olculen:
            e.append(
                eleman.olcu("yatay", (a, 0), (b, 0), Y["ag_dusus"][1] - 150, f"HALAT SAPMASI {abs(dx):g}")
            )
    if abs(dy) > 0.5:
        a, b = sorted((Y["ag_dusus"][1], t1))
        if ("dusey", round(a, 1), round(b, 1)) not in olculen:
            e.append(
                eleman.olcu("dusey", (0, a), (0, b), Y["ag_eksen_x"] + 150, f"HALAT SAPMASI {abs(dy):g}")
            )
    return e


def _sapma_yazisi_adaylari(e, G, D):
    """Halat sapmasının yazısı ölçüsünden uzundur:  uçlarından birinin dışına ya
    da ölçünün üstüne / altına — duvara, makineye, şaseye ve öbür yazılara
    binmeyen ilk yere ( eskiden sol uca, duvarın ve yan ölçülerin üstüne
    düşüyordu — girdi taraması, 4 Eki ).  [ ( ölçü, adaylar ) ]"""
    tasinir = []
    for el in e:
        if el["tip"] == "olcu" and el["metin"].startswith("HALAT SAPMASI"):
            y_, w = el["yazi"], eleman.yazi_eni(el["metin"]) / 2.0
            i = 0 if el["yon"] == "yatay" else 1
            a, b = sorted((el["a"][i], el["b"][i]))
            ic_ = (a + b) / 2.0 < (G if i == 0 else D) / 2.0  # içerisi hangi yanda
            uclar = [b + 30 + w, a - 30 - w] if ic_ else [a - 30 - w, b + 30 + w]
            #  İç yanda sıranın uzantısı boyunca ( makinenin ötesine kadar )
            uzanti = [(b + 30 + w + 50 * n) if ic_ else (a - 30 - w - 50 * n) for n in range(1, 16)]
            k_, ad = el["kot"], []
            for d in (50, -50, 110, -110, 170, -170):
                ad += [(u, k_ + d) if i == 0 else (k_ + d, u) for u in uclar + [(a + b) / 2.0]]
            for d in (50, -50):
                ad += [(u, k_ + d) if i == 0 else (k_ + d, u) for u in uzanti]
            tasinir.append((el, [(y_["x"], y_["y"])] + ad))
    return tasinir
