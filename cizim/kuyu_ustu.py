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

Bugün çizilen düzen:  karşı ağırlık yanda, kabin altı 2:1 askı ( ofisin ve
referans projenin düzeni ).  Öteki düzenler için doğrulama açıkça reddeder.
"""
from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import kuyu_dibi as CKD
from cizim import makine as CMK
from cizim import baglantilar as CB
from cizim import sabitler as CS

#  TS EN 81-20 m.5.2.6.6.4 → m.5.2.6.3.2.1 a:  panonun önünde en az 0,70 m
#  derinlikte, en az 0,50 m ya da pano eni kadar genişlikte boş alan.
CALISMA_DERINLIK = 700.0
CALISMA_EN_ASGARI = 500.0
YANLAR = ("Sol", "Sağ")
_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA", "EKSEN")


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Duzlem:
    """HALAT DÜZLEMİ:  tahrik kasnağının iki halat inişi, kabin tarafının ve
    karşı ağırlık tarafının halatları aynı düşey düzlemdedir.  u düzlem boyunca,
    v düzleme dik ( planda ).  Karşı ağırlık yandaysa düzlem kuyu genişliği
    boyuncadır ( u = x ), arkadaysa derinliği boyunca ( u = y ).  Makine ve
    saptırma kasnağı u = x düzenindeki kuralla kurulur, arkadaki ağırlıkta
    x ↔ y takas edilir ( makine.takas ):  kasnak ekseni hep düzleme diktir."""

    def __init__(self, yon, v0):
        self.yon, self.v0 = yon, float(v0)

    @property
    def eksen(self):                        # kasnak ekseni ( düzleme dik )
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

    def parcalar(self, parcalar):
        return parcalar if self.yon == "x" else CMK.takas(parcalar)


def _regulator(g, S, taban, kabin, G):
    """Hız regülatörü:  kuyu dibindeki gergi kasnağının tam üstü — seçilen
    yandaki kabin rayının hizasında, ray ekseninden regülatör kaçıklığı kadar."""
    kd = g["kuyu_dibi"]
    ry = g["kabin_ray"]["kapi_arasi"]
    raylar = sorted((_kutu(el) for el in taban if el.get("ad") == "kabin_ray"),
                    key=lambda r: r[0])
    sag_reg = kd["regulator_yan"] == "Sağ"
    rx = ((raylar[-1][0] + raylar[-1][2]) / 2.0 if sag_reg
          else (raylar[0][0] + raylar[0][2]) / 2.0)
    #  Rayın iki parçası ( flanş + gövde ) aynı hizada;  birleşik orta
    ray_parca = [r for r in raylar if (r[0] > kabin[2] - 1 if sag_reg else r[2] < kabin[0] + 1)]
    if ray_parca:
        rx = (min(r[0] for r in ray_parca) + max(r[2] for r in ray_parca)) / 2.0
    rgy = ry + kd["regulator_kaciklik"]
    re_, rd = S["regulator_eni"] / 2.0, kd["regulator_kasnak_capi"] / 2.0
    reg_kasnak = (rx - re_, rgy - rd, rx + re_, rgy + rd)
    ge, gb = S["regulator_govde_en"] / 2.0, S["regulator_govde_boy"] / 2.0
    reg_govde = (rx - ge, rgy - gb, rx + ge, rgy + gb)
    reg_ayak = ((reg_govde[2], rgy - gb, G, rgy + gb) if sag_reg
                else (0.0, rgy - gb, reg_govde[0], rgy + gb))
    return rx, rgy, reg_kasnak, reg_govde, reg_ayak


def duzen_hatalari(g):
    """Askı düzeni ile karşı ağırlığın yerinin çizilebilir bir birleşim olup
    olmadığı.  Çizilenler:  yandaki ağırlıkla 2:1 ( kasnaklar kabinin altında ya
    da üstünde ), makine dairesinde 1:1 ( ağırlık yanda ya da arkada — ofisin
    12744-3 ve 477-8 projeleri ).  Öbürleri gerçek projelerde yoktur, sebebiyle
    reddedilir ( düşey kesit de ilk bunu söyler ).  Döner:  hata listesi."""
    hata = []
    duzen = (g.get("aski") or {}).get("duzen")
    yer = (g.get("agirlik") or {}).get("yeri")
    oda_ici = (g.get("makine") or {}).get("yeri") == "Makine dairesi"
    if duzen == "Doğrudan" and not oda_ici:
        hata.append("Makine dairesiz ( kuyu üstü ) tesiste 1:1 askı çizilmez:  tahrik kasnağı "
                    "kabinin tam üstünde olur, kabin kuyu tepesine çıkamaz — makine dairesiz "
                    "asansörler 2:1 askılıdır ( ofisin ve referans projenin MRL'leri ).  Askı "
                    "oranını 2 seçin ya da makine dairesi olsun.")
    elif duzen not in ("Kabin altı", "Kabin üstü", "Doğrudan"):
        hata.append(f"aski.duzen:  ( 'Kabin altı', 'Kabin üstü', 'Doğrudan' ) içinden olmalı ( {duzen!r} ).")
    if yer == "Arka" and duzen != "Doğrudan":
        hata.append("Arkadaki karşı ağırlık yalnız 1:1 askıda çizilir ( ofisin 12744-3 ve 477-8 "
                    "projeleri ):  2:1 askıda halatlar kabinin iki yanından çıkar, arkadaki "
                    "ağırlığa ancak ek saptırma kasnaklarıyla ulaşır — bu düzen çizilmez;  "
                    "ağırlığı yana alın ya da 1:1 askı seçin.")
    elif yer not in YANLAR + ("Arka",):
        hata.append(f"agirlik.yeri:  ( 'Sol', 'Sağ', 'Arka' ) içinden olmalı ( {yer!r} ).")
    return hata


def yerlesim(g, cizim_sabitleri=None, acil_pano=True):
    """Makinenin, halatların, bağlantıların ve regülatörün yeri.

    Makine daireli projede de AYNEN kullanılır ( makine_dairesi.py ):  makine
    kuyunun üstündeyse halatlar aynı noktalardan iner, yalnız bu kez döşeme
    deliklerinden geçer.  acil_pano = False iken acil kurtarma panosu
    aranmaz — makine dairesinde bütün düzenekler odanın içindedir.
    """
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    ku, kd, ag = g.get("kuyu_ustu") or {}, g.get("kuyu_dibi") or {}, g["agirlik"]
    mk = g.get("makine") or {}
    hata = []
    duzen = (g.get("aski") or {}).get("duzen")
    hata += duzen_hatalari(g)
    if duzen != "Doğrudan" and not (_sayi(ag.get("kasnak_capi")) and ag["kasnak_capi"] > 0):
        hata.append("agirlik.kasnak_capi:  2:1 askıda karşı ağırlık kasnağının çapı girilmeli.")
    if not (_sayi(mk.get("tahrik_kasnak_capi")) and mk["tahrik_kasnak_capi"] > 0):
        hata.append(f"makine.tahrik_kasnak_capi: sayı olmalı ( {mk.get('tahrik_kasnak_capi')!r} ).")
    if mk.get("tip") not in CMK.TIPLER:
        hata.append(f"makine.tip: {CMK.TIPLER} içinden olmalı ( {mk.get('tip')!r} ).")
    elif mk["tip"] == "Dişli" and mk.get("yeri", "Kuyu üstü") == "Kuyu üstü":
        #  LiftDesigner'ın dişli makinesi 1.316 × 590:  kuyu tepesindeki,
        #  karşı ağırlık rayları arasındaki şaseye sığmaz;  makine dairesiz
        #  asansörler dişlisizdir ( ofisin 4815-6'sı ve referans proje de öyle ).
        hata.append("Makine dairesiz ( kuyu üstü ) tesiste dişli makine çizilmez — "
                    "makine.tip Dişlisiz olmalı ya da makine.yeri Makine dairesi.")
    aski = g.get("aski") or {}
    for alan in ("halat_adedi", "halat_capi"):
        if not (_sayi(aski.get(alan)) and aski[alan] > 0):
            hata.append(f"aski.{alan}: şase plakasındaki halat deliği için gerekli ( {aski.get(alan)!r} ).")
    if CMK.npu(mk.get("yan_yatak")) is None:
        hata.append(f"makine.yan_yatak: makinenin oturduğu kirişin NPU ölçüsü ( hesap programında "
                    f"'F ( yan yatak )' ) — {tuple(CMK.NPU)} içinden olmalı ( {mk.get('yan_yatak')!r} ).")
    if acil_pano and ku.get("acil_pano_yan") not in YANLAR:
        hata.append(f"kuyu_ustu.acil_pano_yan: {YANLAR} içinden olmalı ( {ku.get('acil_pano_yan')!r} ).")
    for alan in ("regulator_kaciklik", "regulator_kasnak_capi"):
        if not _sayi(kd.get(alan)):
            hata.append(f"kuyu_dibi.{alan}: regülatör onun tam üstündedir, girilmeli.")
    if kd.get("regulator_yan") not in YANLAR:
        hata.append("kuyu_dibi.regulator_yan: regülatör gergi kasnağının tam üstündedir, girilmeli.")
    if hata:
        return {"hata": hata}
    if duzen == "Doğrudan":
        return _dogrudan(g, S, mk, ag)

    taban = CGE.plan(g, S, kapi_duzeyi=False)
    k = g["kuyu"]
    G, D = k["genislik"], k["derinlik"]
    kabin = _kutu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    blok = _kutu(next(el for el in taban if el.get("ad") == "agirlik_blok"))
    sol = ag["yeri"] == "Sol"
    ry = g["kabin_ray"]["kapi_arasi"]
    ag_y = ry + ag["eksen_kaciklik"]
    ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]

    #  ── HALATLAR ─────────────────────────────────────────────────────
    (xl, y0), (xr, _) = CGE.halat_konumlari(g, S)
    yakin, uzak = (xl, xr) if sol else (xr, xl)
    D1 = mk["tahrik_kasnak_capi"]
    y_ = -1.0 if sol else 1.0                       # kabinden ağırlığa doğru
    ag_dusus_x = yakin + y_ * D1                    # tahrik kasnağının öbür teğeti
    R = ag["kasnak_capi"] / 2.0
    teget1, teget2 = sorted((ag_y - R, ag_y + R), key=lambda t: abs(t - y0))
    sapma = (ag_dusus_x - ex, y0 - teget1)

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

    #  ── MAKİNE ŞASESİ ( makine dairesizde ) ───────────────────────────
    #  Karşı ağırlık rayları boyunca, duvardan ağırlık tarafındaki kabin
    #  rayına ( referans proje:  şase kabin rayına ve ağırlık raylarına oturur ).
    kab_r = sorted(CKD._raylar(taban, "kabin_ray"), key=lambda r: r[0])
    ag_r = CKD._raylar(taban, "agirlik_ray")
    yakin_ray = kab_r[0] if sol else kab_r[-1]
    sase = ((S["makine_sase_duvar"], min(r[1] for r in ag_r) - S["makine_sase_ray_payi"],
             yakin_ray[0], max(r[3] for r in ag_r) + S["makine_sase_ray_payi"]) if sol else
            (yakin_ray[2], min(r[1] for r in ag_r) - S["makine_sase_ray_payi"],
             G - S["makine_sase_duvar"], max(r[3] for r in ag_r) + S["makine_sase_ray_payi"]))

    #  ── HALAT BAĞLANTILARI ───────────────────────────────────────────
    #  Ağırlık tarafı:  ağırlık kasnağının öbür teğetinin üstünde;  plaka
    #  halattan kabine doğru uzanır.  Kabin tarafı:  kabinin uzak halatının
    #  üstünde, kabin rayının başına bağlı;  plaka halattan kabine doğru.
    ab_y0 = teget2 - s * S["agirlik_baglanti_y"]
    ab_y1 = ab_y0 + s * S["agirlik_baglanti_boy"]
    ab_x0 = ex + y_ * S["agirlik_baglanti_x"]
    ab_x1 = ab_x0 - y_ * S["agirlik_baglanti_en"]
    agirlik_baglanti = (min(ab_x0, ab_x1), min(ab_y0, ab_y1), max(ab_x0, ab_x1), max(ab_y0, ab_y1))
    kb_x0 = uzak + y_ * S["kabin_baglanti_x"]
    kb_x1 = kb_x0 - y_ * S["kabin_baglanti_en"]
    kabin_baglanti = (min(kb_x0, kb_x1), y0 - S["kabin_baglanti_boy"] / 2.0,
                      max(kb_x0, kb_x1), y0 + S["kabin_baglanti_boy"] / 2.0)

    #  ── REGÜLATÖR:  gergi kasnağının tam üstü ─────────────────────────
    rx, rgy, reg_kasnak, reg_govde, reg_ayak = _regulator(g, S, taban, kabin, G)

    #  ── ACİL KURTARMA VE TEST PANOSU ─────────────────────────────────
    kp, don = g["kapi"], k["duvar_on"]
    pano = calisma = None
    x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
    kasa, pe, pd = S["kasa_yan"], S["acil_pano_en"], S["acil_pano_derinlik"]
    if acil_pano:
        if ku["acil_pano_yan"] == "Sol":
            pano = (x0 - kasa - pe, -don - pd, x0 - kasa, -don)
        else:
            pano = (x1 + kasa, -don - pd, x1 + kasa + pe, -don)
        ce = max(CALISMA_EN_ASGARI, pe)
        pm = (pano[0] + pano[2]) / 2.0
        calisma = (pm - ce / 2.0, pano[1] - CALISMA_DERINLIK, pm + ce / 2.0, pano[1])

    #  ── MAKİNENİN PARÇALARI ( makine.py ) ────────────────────────────
    #  Planda kot yalnız çizim sırası için:  kasnak merkezi 0.  Dişli makine
    #  ( yalnız makine dairesinde ):  dişli kutusu kasnağın iki yanından
    #  birinde, motor kasnak eksenine dik iki yöndan birinde — bağlantılara ve
    #  regülatöre binmeyen, odaya sığan ilk düzen ( önce ağırlık tarafı ve
    #  kuyunun ortası ).
    m_yon = 1.0 if kmx < G / 2.0 else -1.0
    oda_ = None
    if mk.get("yeri") == "Makine dairesi" and all(
            _sayi((g.get("makine_dairesi") or {}).get(a)) for a in ("x", "y", "genislik", "derinlik")):
        md = g["makine_dairesi"]
        oda_ = (md["x"], md["y"], md["x"] + md["genislik"], md["y"] + md["derinlik"])
    if mk["tip"] == "Dişli":
        engel = (agirlik_baglanti, kabin_baglanti, reg_govde)
        for s_, m_ in ((s, m_yon), (-s, m_yon), (s, -m_yon), (-s, -m_yon)):
            z = CMK.disli_zarfi((kmx, y0, 0.0), s_, m_)
            if not any(_ortusur(z, p) for p in engel) and (
                    oda_ is None or (oda_[0] <= z[0] and oda_[1] <= z[1] and z[2] <= oda_[2] and z[3] <= oda_[3])):
                s, m_yon = s_, m_
                break
        makine = CMK.disli((kmx, y0, 0.0), D1, 2 * kt, s, m_yon)
        govde = CMK.disli_zarfi((kmx, y0, 0.0), s, m_yon)
    else:
        makine = CMK.dislisiz((kmx, y0, 0.0), D1, 2 * kt, s, S["makine_en"],
                              S["makine_kasnak_boslugu"] + S["makine_boy"])

    #  ── ÇAKIŞMALAR ───────────────────────────────────────────────────
    parcalar = {"makine": govde, "tahrik kasnağı": kasnak, "ağırlık halat bağlantısı": agirlik_baglanti,
                "kabin halat bağlantısı": kabin_baglanti, "regülatör": reg_govde}
    for ad, p in parcalar.items():
        #  Makine dairesinde makine odanın içindedir ( makine_dairesi denetler )
        if oda_ is not None and ad in ("makine", "tahrik kasnağı"):
            continue
        if p[0] < 0 or p[1] < 0 or p[2] > G or p[3] > D:
            hata.append(f"{ad.capitalize()} kuyunun dışına taşıyor.")
    adlar = list(parcalar)
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            if {a, b} == {"makine", "tahrik kasnağı"}:
                continue
            if _ortusur(parcalar[a], parcalar[b]):
                hata.append(f"Kuyu üstünde {a} ile {b} üst üste biniyor.")

    return {"taban": taban, "kabin": kabin, "blok": blok, "halatlar": [(xl, y0), (xr, y0)],
            "ag_dusus": (ag_dusus_x, y0), "ag_teget": (ex, teget1), "ag_teget2": (ex, teget2),
            "sapma": sapma, "kasnak": kasnak, "govde": govde, "agirlik_baglanti": agirlik_baglanti,
            "makine": makine, "m_yon": m_yon, "s": s, "sase": sase, "tip": mk["tip"],
            "yan_yatak": CMK.npu(mk["yan_yatak"]),
            #  Şaseden aşağı inen halatların delikleri ( plakaya düşenler açılır ):
            #  tahrik kasnağının iki yanı ve karşı ağırlık bağlantısı
            "sase_delikleri": [CMK.halat_deligi(x_, y0, aski["halat_adedi"], aski["halat_capi"],
                                                S["halat_delik_payi"]) for x_ in (yakin, ag_dusus_x)] +
                              [CMK.halat_deligi(ex, teget2, aski["halat_adedi"], aski["halat_capi"],
                                                S["halat_delik_payi"], "x")],
            "kabin_baglanti": kabin_baglanti,
            "halat_konsolu": CB.halat_konsolu(kabin_baglanti, kab_r[-1] if sol else kab_r[0], 0),
            "reg_kasnak": reg_kasnak, "reg_govde": reg_govde,
            "reg_ayak": reg_ayak, "pano": pano, "calisma": calisma, "D1": D1,
            "rgx": rx, "rgy": rgy, "yakin": yakin, "uzak": uzak,
            "ag_y": ag_y, "ry": ry, "ex": ex, "hata": hata, "S": S}


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
    taban = CGE.plan(g, S, kapi_duzeyi=False)
    k, kb, a = g["kuyu"], g["kabin"], g["aski"]
    G, D = k["genislik"], k["derinlik"]
    kabin = _kutu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    blok = _kutu(next(el for el in taban if el.get("ad") == "agirlik_blok"))
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
    y_ = 1.0 if ua >= uk else -1.0                  # kabinden ağırlığa doğru
    D1 = mk["tahrik_kasnak_capi"]
    ud = uk + y_ * D1                               # tahrik kasnağının öbür teğeti
    sapma = (ud - ua, d.v0 - d.v((ax, ay)))

    #  ── MAKİNE:  tahrik kasnağı + gövde ( 2:1'deki kural, düzlemin içinde ) ──
    kt = S["tahrik_kasnak_kalinlik"] / 2.0
    kasnak = d.kutu(uk, ud, d.v0 - kt, d.v0 + kt)
    va = d.v((ax, ay))
    s = 1.0 if va >= d.v0 else -1.0                 # gövde ağırlığın yanına
    kmu = (uk + ud) / 2.0
    g0 = d.v0 + s * (kt + S["makine_kasnak_boslugu"])
    govde = d.kutu(kmu - S["makine_en"] / 2.0, kmu + S["makine_en"] / 2.0, g0, g0 + s * S["makine_boy"])
    rx, rgy, reg_kasnak, reg_govde, reg_ayak = _regulator(g, S, taban, kabin, G)
    md = g.get("makine_dairesi") or {}
    oda_ = None
    if all(_sayi(md.get(k_)) for k_ in ("x", "y", "genislik", "derinlik")):
        oda_ = (md["x"], md["y"], md["x"] + md["genislik"], md["y"] + md["derinlik"])
    m_yon = 1.0 if kmu < (G if d.yon == "x" else D) / 2.0 else -1.0
    if mk["tip"] == "Dişli":
        for s_, m_ in ((s, m_yon), (-s, m_yon), (s, -m_yon), (-s, -m_yon)):
            zk = CMK.disli_zarfi((kmu, d.v0, 0.0), s_, m_)
            z = d.kutu(zk[0], zk[2], zk[1], zk[3])
            if not _ortusur(z, reg_govde) and (
                    oda_ is None or (oda_[0] <= z[0] and oda_[1] <= z[1] and z[2] <= oda_[2] and z[3] <= oda_[3])):
                s, m_yon = s_, m_
                break
        makine = d.parcalar(CMK.disli((kmu, d.v0, 0.0), D1, 2 * kt, s, m_yon))
        zk = CMK.disli_zarfi((kmu, d.v0, 0.0), s, m_yon)
        govde = d.kutu(zk[0], zk[2], zk[1], zk[3])
    else:
        makine = d.parcalar(CMK.dislisiz((kmu, d.v0, 0.0), D1, 2 * kt, s, S["makine_en"],
                                         S["makine_kasnak_boslugu"] + S["makine_boy"]))
    if _ortusur(kasnak, reg_govde) or _ortusur(govde, reg_govde):
        hata.append("Makine dairesinde makine ile regülatör üst üste biniyor.")
    for ad_, p_ in (("regülatör", reg_govde),):
        if p_[0] < 0 or p_[1] < 0 or p_[2] > G or p_[3] > D:
            hata.append(f"{ad_.capitalize()} kuyunun dışına taşıyor.")
    return {"dogrudan": True, "duzlem": d, "y_": y_, "taban": taban, "kabin": kabin, "blok": blok,
            "halatlar": [(hx, hy)], "kabin_nokta": (hx, hy), "ag_nokta": (ax, ay),
            "ag_dusus": d.p(ud), "sapma": sapma, "kasnak": kasnak, "govde": govde,
            "agirlik_baglanti": None, "kabin_baglanti": None,
            "makine": makine, "m_yon": m_yon, "s": s, "sase": None, "tip": mk["tip"],
            "yan_yatak": CMK.npu(mk["yan_yatak"]), "sase_delikleri": [],
            "reg_kasnak": reg_kasnak, "reg_govde": reg_govde, "reg_ayak": reg_ayak,
            "pano": None, "calisma": None, "D1": D1, "rgx": rx, "rgy": rgy,
            "ry": ry, "hata": hata, "S": S}


def dogrula(g):
    hata = CG.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def ciz(g, cizim_sabitleri=None):
    Y = yerlesim(g, cizim_sabitleri)
    k = g["kuyu"]
    G, D, don, dg, dar, ds = (k["genislik"], k["derinlik"], k["duvar_on"], k["duvar_sag"],
                              k["duvar_arka"], k["duvar_sol"])
    e = [el for el in Y["taban"] if el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi"]

    def kutu(katman, p, ad):
        e.append(CGE._ad(CGE._dik(katman, p[0], p[1], p[2] - p[0], p[3] - p[1]), ad))

    #  İzler:  kabin, karşı ağırlık, kat kapısı ( kesik )
    kutu("GIZLI", Y["kabin"], "kabin_izi")
    kutu("GIZLI", Y["blok"], "agirlik_izi")
    kp = g["kapi"]
    kutu("GIZLI", (kp["sol_pay"], -don, kp["sol_pay"] + kp["genislik"], 0), "kapi_izi")

    #  Makine şasesi ( 2 yan yatak ) ve makine — parça parça ( makine.py )
    e += CMK.plan(CMK.plan_parcalari(Y, Y["S"]), CGE._dik, CGE._daire, CGE._cizgi)
    ks = Y["kasnak"]
    e.append(CGE._yazi((ks[0] + ks[2]) / 2.0, (ks[1] + ks[3]) / 2.0, f"ø {Y['D1']:g}", 38))

    #  Halat bağlantıları, sonra halatlar ( işaret plakanın üstünde görünsün )
    kutu("BAGLANTI", Y["agirlik_baglanti"], "agirlik_baglanti")
    kutu("BAGLANTI", Y["kabin_baglanti"], "kabin_baglanti")
    if g["makine"]["yeri"] == "Kuyu üstü":
        e += CMK.plan(Y["halat_konsolu"], CGE._dik, CGE._daire, CGE._cizgi)
    for p in (Y["agirlik_baglanti"], Y["kabin_baglanti"]):
        e.append(CGE._yazi((p[0] + p[2]) / 2.0, p[3] + 40, "HALAT BAĞLANTISI", 30))
    for hx, hy in Y["halatlar"] + [Y["ag_dusus"], Y["ag_teget2"]]:
        e.append(CGE._ad(CGE._daire("KASNAK", hx, hy, 20), "halat"))

    #  Regülatör
    kutu("KONSOL", Y["reg_ayak"], "regulator_ayak")
    kutu("MAKINE", Y["reg_govde"], "regulator")
    kutu("KASNAK", Y["reg_kasnak"], "regulator_kasnak")
    rg = Y["reg_govde"]
    e.append(CGE._yazi(rg[0] - 60 if rg[0] > G / 2 else rg[2] + 60, (rg[1] + rg[3]) / 2.0,
                       "REGÜLATÖR", 34, aci=90))

    #  Acil kurtarma ve test panosu + çalışma alanı
    kutu("PANO", Y["pano"], "acil_pano")
    kutu("SIGINMA", Y["calisma"], "calisma_alani")
    pn, ca = Y["pano"], Y["calisma"]
    e.append(CGE._yazi((pn[0] + pn[2]) / 2.0, (pn[1] + pn[3]) / 2.0, "ACİL PANO", 34))
    e.append(CGE._yazi((ca[0] + ca[2]) / 2.0, (ca[1] + ca[3]) / 2.0, "ÇALIŞMA ALANI", 34))

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    O = CGE._olcu
    xl, xr = Y["halatlar"][0][0], Y["halatlar"][1][0]
    kx = (Y["kabin"][0] + Y["kabin"][2]) / 2.0
    u0, u1 = D + dar + 120, D + dar + 320
    xs = sorted({0.0, G, Y["ex"], Y["ag_dusus"][0], xl, xr, kx})
    e += [O("yatay", (a, 0), (b, 0), u0,
            f"ø {Y['D1']:g}" if (a, b) == (Y["kasnak"][0], Y["kasnak"][2]) else None)
          for a, b in zip(xs, xs[1:])]
    e.append(O("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"))
    #  Sağ:  halat çizgisi, kabin ray ekseni, regülatör
    s0, s1 = G + dg + 120, G + dg + 320
    ys = sorted({0.0, D, Y["halatlar"][0][1], Y["ry"], (Y["reg_kasnak"][1] + Y["reg_kasnak"][3]) / 2.0})
    e += [O("dusey", (0, a), (0, b), s0) for a, b in zip(ys, ys[1:])]
    e.append(O("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"))
    #  Sol:  ağırlık kasnağının teğetleri ve ekseni ( halat düşüşü )
    t1, t2 = Y["ag_teget"][1], Y["ag_teget2"][1]
    ys = sorted({0.0, D, t1, t2, Y["ag_y"], Y["ry"]})
    e += [O("dusey", (0, a), (0, b), -ds - 120) for a, b in zip(ys, ys[1:])]
    #  Acil pano çalışma alanı  ( m.5.2.6.3.2.1 a )
    e.append(O("yatay", (ca[0], 0), (ca[2], 0), ca[1] - 90, f"{ca[2] - ca[0]:g}"))
    e.append(O("dusey", (0, ca[1]), (0, ca[3]), ca[0] - 90 if ca[0] > G / 2 else ca[2] + 90,
               f"{ca[3] - ca[1]:g}"))
    #  Halat sapması — varsa
    dx, dy = Y["sapma"]
    if abs(dx) > 0.5:
        a, b = sorted((Y["ag_dusus"][0], Y["ex"]))
        e.append(O("yatay", (a, 0), (b, 0), Y["ag_dusus"][1] - 150, f"HALAT SAPMASI {abs(dx):g}"))
    if abs(dy) > 0.5:
        a, b = sorted((Y["ag_dusus"][1], t1))
        e.append(O("dusey", (0, a), (0, b), Y["ex"] + 150, f"HALAT SAPMASI {abs(dy):g}"))
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e)
    return e
