# -*- coding: utf-8 -*-
"""
MAKİNE DAİRESİ PLANI  ve  KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI

Makine daireli asansörde makine kuyunun üstündeki odadadır.  Makinenin,
halatların, bağlantıların ve regülatörün yeri kuyu üstü planıyla AYNIDIR
( kuyu_ustu.yerlesim ):  halatlar aynı noktalardan iner, yalnız bu kez
döşemedeki deliklerden geçer.  İki çizim üretilir:

  MAKİNE DAİRESİ PLANI
    · oda duvarları ve kapısı                      m.5.2.3.2 a ( kapı ≥ 0,60 m )
    · tabliye ( kuyunun üstündeki beton ) ve kot farkı  m.5.2.6.3.2.4
    · makine, halat bağlantıları, regülatör
    · kumanda panosu ve önündeki çalışma alanı     m.5.2.6.3.2.1 a
    · makinenin başında bakım alanı 0,50 × 0,60    m.5.2.6.3.2.1 b
    · döşeme delikleri ve kuyunun izi ( kesik )

  KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI  ( MMO yönetmeliği m.6/b/3 )
    · kuyunun üstündeki döşeme, delikler ve yerlerinin ölçüleri

TABLİYE ( tabliye ):  kuyunun üstünü kuyu döşemesi kalınlığında beton
kapatır;  makine, halat bağlantıları ve regülatör onun üstündedir.  Oda zemini
tabliyenin üstünden "tabliye beton yüksekliği" kadar aşağıdadır ( LiftDesigner'ın
makine dairesi kesiti:  1.200 ).  Kumanda panosu ile önündeki çalışma alanı tek
kotta kalır;  makinenin başındaki bakım alanı tabliyenin üstündedir.  Kot farkı
0,50 m'yi aşarsa merdiven ( ya da basamak ) ve korkuluk gerekir ( m.5.2.6.3.2.4 —
çizimde not;  merdivenin yeri projeciye kalır ).

DELİKLER ( m.5.2.6.3.3:  "amacı için en küçük" ):  askı halatı demeti
( n halat, kanal aralığı 1,6 · dh — hesap programının kasnak genişliği
bağıntısı ) çevresine halat_delik_payi bırakılır;  demet tahrik ve kabin
tarafında kasnak ekseni ( y ) boyunca, karşı ağırlık bağlantısında ağırlık
kasnağının ekseni ( x ) boyunca dizilir.  Regülatör halatının deliği de aynı
kuralla ( tek halat:  çap + 2 × pay ).
"""

from temel import ortusur, sayi_mi
from cizim import eleman
from cizim import izli
from cizim import geometri
from cizim import kuyu_ustu
from cizim import makine
from cizim import sabitler

#  TS EN 81-20 m.5.2.3.2 a:  makine dairesi kapısı en az 0,60 m genişlikte.
KAPI_ASGARI = 600.0
#  m.5.2.6.3.2.1 b:  hareketli parçaların başında en az 0,50 × 0,60 m.
BAKIM_ALANI = (500.0, 600.0)
#  m.5.2.6.3.2.1 a:  panonun önünde 0,70 m derin, en az 0,50 m ya da pano eni.
CALISMA_DERINLIK = kuyu_ustu.CALISMA_DERINLIK
CALISMA_EN_ASGARI = kuyu_ustu.CALISMA_EN_ASGARI
DUVARLAR = ("Ön", "Arka", "Sol", "Sağ")
#  m.5.2.6.3.2.4:  zemin kotları 0,50 m'den fazla farklıysa merdiven ve korkuluk.
KOT_FARKI_MERDIVEN = 500.0
#  m.5.2.6.3.2.5:  0,05 m'den derin, 0,05 – 0,50 m geniş girinti örtülür.
GIRINTI = (50.0, 500.0)


def icinde(p, oda):
    return oda[0] - 1e-9 <= p[0] and p[2] <= oda[2] + 1e-9 and oda[1] - 1e-9 <= p[1] and p[3] <= oda[3] + 1e-9


def tabliye(g):
    """Kuyunun üstündeki beton ( TABLİYE ):

    izi        planda kuyunun dış yüzleri ( duvarlarıyla )
    doseme     betonun kalınlığı:  kuyu döşemesi ( kuyu dibi ile aynı;  yoksa ön duvar )
    yukseklik  oda zemininden tabliyenin üstüne ( hesap programının "Tabliye
               beton yüksekliği";  LiftDesigner'ın makine dairesi kesitinde 1.200 )
    """
    k, md = g["kuyu"], g.get("makine_dairesi") or {}
    dos = k.get("doseme") if sayi_mi(k.get("doseme")) else k["duvar_on"]
    t = md.get("tabliye_yuksekligi")
    return {
        "izi": (
            -k["duvar_sol"],
            -k["duvar_on"],
            k["genislik"] + k["duvar_sag"],
            k["derinlik"] + k["duvar_arka"],
        ),
        "doseme": izli.sayi(dos),
        "yukseklik": izli.sayi(t) if sayi_mi(t) and t > 0 else 0.0,
    }


def tek_kotta(k, TB):
    """Kutu tek bir zeminde mi:  tabliyenin üstünde ya da oda zemininde ( kot
    farkı yoksa her yer )."""
    return TB["yukseklik"] <= 1e-9 or icinde(k, TB["izi"]) or not ortusur(k, TB["izi"])


def _birlesik(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _duvar_seridi(oda, duvar, en, derinlik, konum):
    """Odanın iç yüzüne dayanan kutu:  duvar boyunca `en`, içeri `derinlik`,
    duvarın sol ( ön ) iç köşesinden `konum` kadar ötede.  Döner:  kutu ve
    içeri bakan yön ( çalışma alanı o yöne açılır )."""
    x0, y0, x1, y1 = oda
    if duvar == "Ön":
        return (x0 + konum, y0, x0 + konum + en, y0 + derinlik), (0, 1)
    if duvar == "Arka":
        return (x0 + konum, y1 - derinlik, x0 + konum + en, y1), (0, -1)
    if duvar == "Sol":
        return (x0, y0 + konum, x0 + derinlik, y0 + konum + en), (1, 0)
    return (x1 - derinlik, y0 + konum, x1, y0 + konum + en), (-1, 0)


def _onunde(kutu, yon, derinlik, en):
    """Kutunun iç yüzünün önünde, ona ortalı alan."""
    cx, cy = (kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0
    if yon[1]:
        y = kutu[3] if yon[1] > 0 else kutu[1] - derinlik
        return (cx - en / 2.0, y, cx + en / 2.0, y + derinlik)
    x = kutu[2] if yon[0] > 0 else kutu[0] - derinlik
    return (x, cy - en / 2.0, x + derinlik, cy + en / 2.0)


def _pano_yeri(oda, md, S, engeller, kapi, TB=None):
    """Kumanda panosu ve önündeki çalışma alanı ( m.5.2.6.3.2.1 a ):  seçilen
    duvar boyunca 25 mm adımla, engellere basmadan kapıya en yakın yer;  yoksa
    ( None, None ).  Her engelin kapattığı adımlar bir kez hesaplanır ( engel ×
    adım karşılaştırması yerine — kaide adayları için sık çağrılır )."""
    pe, pd = S["kumanda_pano_en"], S["kumanda_pano_derinlik"]
    ce = max(CALISMA_EN_ASGARI, pe)
    duvar = md["pano_duvar"]
    uzunluk = md["genislik"] if duvar in ("Ön", "Arka") else md["derinlik"]
    kc = ((kapi[0] + kapi[2]) / 2.0, (kapi[1] + kapi[3]) / 2.0)
    kay = (ce - pe) / 2.0 if ce > pe else 0.0  # panonun adımdaki yeri
    adet = int((uzunluk - max(pe, ce)) / 25.0 + 1e-9) + 1 if uzunluk >= max(pe, ce) - 1e-9 else 0
    x0, y0, x1, y1 = oda

    def _izdusum(k):
        """Kutunun duvar boyunca ( a0 , a1 ) ve duvardan içeri ( d0 , d1 ) aralığı."""
        if duvar == "Ön":
            return k[0] - x0, k[2] - x0, k[1] - y0, k[3] - y0
        if duvar == "Arka":
            return k[0] - x0, k[2] - x0, y1 - k[3], y1 - k[1]
        if duvar == "Sol":
            return k[1] - y0, k[3] - y0, k[0] - x0, k[2] - x0
        return k[1] - y0, k[3] - y0, x1 - k[2], x1 - k[0]

    kapali = [False] * adet
    for e in engeller:
        a0, a1, d0, d1 = _izdusum(e)
        araliklar = []
        if d0 < pd and 0.0 < d1:  # pano şeridi
            araliklar.append((a0 - kay - pe, a1 - kay))
        if d0 < pd + CALISMA_DERINLIK and pd < d1:  # çalışma alanı şeridi
            araliklar.append((a0 - kay - pe / 2.0 - ce / 2.0, a1 - kay - pe / 2.0 + ce / 2.0))
        for k0, k1 in araliklar:  # açık aralık:  k0 < k < k1
            i0 = max(0, int(k0 // 25.0) + 1 if k0 >= 0 else 0)
            for i in range(i0, adet):
                k = i * 25.0
                if k >= k1:
                    break
                if k > k0:
                    kapali[i] = True
    en_iyi = None
    for i in range(adet):
        if kapali[i]:
            continue
        pano, pyon = _duvar_seridi(oda, duvar, pe, pd, i * 25.0 + kay)
        calisma = _onunde(pano, pyon, CALISMA_DERINLIK, ce)
        if not (icinde(pano, oda) and icinde(calisma, oda)):
            continue
        #  Pano ile önündeki çalışma alanı tabliyenin kenarından bölünmez
        if TB and not tek_kotta(_birlesik(pano, calisma), TB):
            continue
        pc = ((pano[0] + pano[2]) / 2.0, (pano[1] + pano[3]) / 2.0)
        aday = (abs(pc[0] - kc[0]) + abs(pc[1] - kc[1]), i * 25.0, pano, calisma)
        if en_iyi is None or aday < en_iyi:
            en_iyi = aday
    if en_iyi is None:
        return None, None
    return en_iyi[2], en_iyi[3]


def _bakim_yeri(mk, engeller, oda, TB=None):
    """Makinenin başında 0,50 × 0,60 bakım alanı ( m.5.2.6.3.2.1 b ):  makinenin
    ( kaidenin ) dört yanından birine, engellere basmadan, makineye en yakın;
    yoksa None.  Kot farkı varsa tabliyenin üstünde ( makineyle aynı kotta )."""
    adaylar = []
    mc = ((mk[0] + mk[2]) / 2.0, (mk[1] + mk[3]) / 2.0)
    #  Adaylar makinenin en çok alanın uzun kenarı kadar çevresindedir
    r = max(BAKIM_ALANI)
    cevre = (mk[0] - r, mk[1] - r, mk[2] + r, mk[3] + r)
    engeller = [x for x in engeller if ortusur(x, cevre)]
    for w, h in (BAKIM_ALANI, BAKIM_ALANI[::-1]):
        for kutu in _bitisik_adaylar(mk, w, h):
            if TB and TB["yukseklik"] > 1e-9 and not icinde(kutu, TB["izi"]):
                continue
            if icinde(kutu, oda) and not any(ortusur(kutu, x) for x in engeller):
                c = ((kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0)
                adaylar.append((abs(c[0] - mc[0]) + abs(c[1] - mc[1]), kutu))
    return min(adaylar)[1] if adaylar else None


def _girdi_hatalari(g, md, a):
    """Yerleşimin kurulamayacağı girdi eksikleri:  [ ileti ]."""
    hata = []
    for alan in ("genislik", "derinlik", "duvar", "kapi_genislik"):
        if not (sayi_mi(md.get(alan)) and md[alan] > 0):
            hata.append(f"makine_dairesi.{alan}: sıfırdan büyük bir sayı olmalı ( {md.get(alan)!r} ).")
    for alan in ("x", "y", "kapi_konum"):
        if not sayi_mi(md.get(alan)):
            hata.append(f"makine_dairesi.{alan}: sayı olmalı ( {md.get(alan)!r} ).")
    for alan in ("kapi_duvar", "pano_duvar"):
        if md.get(alan) not in DUVARLAR:
            hata.append(f"makine_dairesi.{alan}: {DUVARLAR} içinden olmalı ( {md.get(alan)!r} ).")
    for alan in ("halat_adedi", "halat_capi"):
        if not (sayi_mi(a.get(alan)) and a[alan] > 0):
            hata.append(f"aski.{alan}: döşeme deliği için gerekli ( {a.get(alan)!r} ).")
    rdh = (g.get("kuyu_dibi") or {}).get("regulator_halat_capi")
    if not (sayi_mi(rdh) and rdh > 0):
        hata.append(
            f"kuyu_dibi.regulator_halat_capi: regülatör halatının döşeme deliği için gerekli "
            f"( hesap programında 'Regülatör halatı çapı' ) ( {rdh!r} )."
        )
    #  Makine kaidesi:  hesap programının girdileri ( bölüm 2 )
    if not (sayi_mi(md.get("sase_yuksekligi")) and md["sase_yuksekligi"] > 0):
        hata.append(
            f"makine_dairesi.sase_yuksekligi: sıfırdan büyük bir sayı olmalı ( {md.get('sase_yuksekligi')!r} )."
        )
    if makine.npu(md.get("dikine_kiris")) is None:
        hata.append(
            f"makine_dairesi.dikine_kiris: kaidenin kolonlarının NPU ölçüsü — "
            f"{tuple(makine.NPU)} içinden olmalı ( {md.get('dikine_kiris')!r} )."
        )
    return hata


def yerlesim(g, cizim_sabitleri=None):
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    md, a = g.get("makine_dairesi") or {}, g.get("aski") or {}
    hata = _girdi_hatalari(g, md, a)
    if hata:
        return {"hata": hata}
    if md["kapi_genislik"] < KAPI_ASGARI:
        hata.append(
            f"Makine dairesi kapısı {md['kapi_genislik']:g} mm — TS EN 81-20 m.5.2.3.2 a "
            f"en az {KAPI_ASGARI:g} mm ister."
        )
    M = kuyu_ustu.yerlesim(g, S, acil_pano=False)
    #  Kurma ile denetim ayrı ( bkz. donanim.yerlesim ):  kuyu üstünün denetim
    #  hatası odanın yerleşimini durdurmaz, yalnız girdisi eksikse dur.
    if "kasnak" not in M:
        return {"hata": hata + M["hata"]}
    hata += M["hata"]
    oda = (md["x"], md["y"], md["x"] + md["genislik"], md["y"] + md["derinlik"])
    TB = tabliye(g)

    #  1:1 askıda halat düzlemi ( kuyu_ustu.Duzlem ) ağırlık arkadaysa derinlik
    #  boyuncadır;  2:1'de hep genişlik boyunca ( y0 çizgisi ).
    dz = M.get("duzlem") or kuyu_ustu.Duzlem("x", M["halatlar"][0][1])
    if M.get("dogrudan"):
        y_ = M["y_"]
        ex, uk = dz.u(M["ag_nokta"]), dz.u(M["kabin_nokta"])
    else:
        y_ = -1.0 if g["agirlik"]["yeri"] == "Sol" else 1.0
        ex, uk = M["ex"], M["yakin"]
    fark = y_ * (ex - dz.u(M["ag_dusus"]))
    saptirma = _saptirma(g, M, dz, y_, ex, fark, hata)
    agirlik_dusus = dz.p(ex) if saptirma else M["ag_dusus"]
    makine_izi = _birlesik(M["govde"], M["kasnak"])
    #  Makine kaidesi ( hesap programının bölüm 2'si ):  makinenin ve saptırma
    #  kasnağının izini taşır;  yan yataklar izin uzun ekseni boyunca.
    iz = _birlesik(makine_izi, saptirma["kutu"]) if saptirma else makine_izi
    uzun_x = (iz[2] - iz[0]) >= (iz[3] - iz[1])
    E, F = makine.npu(md["dikine_kiris"]), M["yan_yatak"]
    kaide = {"E": E, "F": F, "uzun_x": uzun_x}

    n, dh, p = a["halat_adedi"], a["halat_capi"], S["halat_delik_payi"]
    demet = (n - 1) * 1.6 * dh + dh  # kasnak ekseni boyunca
    delikler = _doseme_delikleri(g, M, dz, agirlik_dusus, n, dh, p)
    hata += _delik_hatalari(delikler, g["kuyu"]["genislik"], g["kuyu"]["derinlik"])

    kapi, kyon = _duvar_seridi(oda, md["kapi_duvar"], md["kapi_genislik"], 0.0, md["kapi_konum"])
    kapi_onu = _onunde(kapi, kyon, CALISMA_DERINLIK, md["kapi_genislik"])
    sabit0 = _sabit_parcalar(M, delikler, saptirma)
    kx, ky = dz.p(uk)
    halat_ortasi = ((kx + agirlik_dusus[0]) / 2.0, (ky + agirlik_dusus[1]) / 2.0)
    arama = _KaideAramasi(oda, md, S, TB, iz, uzun_x, E, F, delikler, sabit0, kapi, kapi_onu, halat_ortasi)
    cerceve, alanlar = arama.ara()
    if cerceve:
        cerceve, boy, ortali = cerceve
        #  Yan yatakların mesnet aralığı:  dikine kirişlerin eksenleri arası
        kaide["L"] = boy - E["h"]
        kaide["ortali"] = ortali
    else:
        hata.append("Makine kaidesi odaya sığmıyor ya da ayakları döşeme deliklerine basıyor.")

    kaide_delikleri = _makine_plakasi(
        g, M, S, dz, kaide, cerceve, makine_izi, saptirma, uk, y_, n, dh, p, demet, hata
    )

    #  ── KUMANDA PANOSU:  seçilen duvar boyunca kapıya en yakın boş yer ─
    #  ( kapı ve önündeki geçiş payı kaideden önce kuruldu )
    sabit = sabit0 + ([cerceve] if cerceve else [])
    pano, calisma, bakim = alanlar or (None, None, None)
    if pano is None:
        pano, calisma = _pano_yeri(oda, md, S, sabit + [kapi_onu], kapi, TB)
    if pano is None:
        hata.append(
            f"Kumanda panosu önündeki {CALISMA_DERINLIK:g} mm çalışma alanıyla "
            f"{md['pano_duvar'].lower()} duvara sığmıyor ( TS EN 81-20 m.5.2.6.3.2.1 a )."
        )

    #  ── MAKİNENİN BAŞINDA BAKIM ALANI  ( 0,50 × 0,60 ) ─────────────────
    #  Makinenin ( gövde + kasnak ) dört yanından birine, deliklere, panoya
    #  ve kapının önüne basmadan;  makineye en yakın yer.
    mk = cerceve or makine_izi
    if bakim is None:
        bakim = _bakim_yeri(mk, sabit + [kapi_onu] + ([pano, calisma] if pano else []), oda, TB)
    if bakim is None:
        hata.append("Makinenin başında 0,50 × 0,60 m bakım alanı kalmıyor ( TS EN 81-20 m.5.2.6.3.2.1 b ).")
    hata += _oda_hatalari(M, mk, oda, TB, kapi_onu)

    return {
        "M": M,
        "oda": oda,
        "delikler": delikler,
        "kapi": kapi,
        "kapi_onu": kapi_onu,
        "pano": pano,
        "calisma": calisma,
        "bakim": bakim,
        "makine": mk,
        "tabliye": TB,
        "pano_kotu": TB["yukseklik"] if pano and icinde(pano, TB["izi"]) else 0.0,
        "merdiven": TB["yukseklik"] > KOT_FARKI_MERDIVEN + 1e-9,
        "girintiler": _girintiler(oda, TB),
        "makine_izi": makine_izi,
        "cerceve": cerceve,
        "kaide": kaide,
        "saptirma": saptirma,
        #  Ağırlık halatının yolu kurulamadı ( içeride inmeli ya da saptırma
        #  kasnağının çapı yok ):  saptirma None iken iniş düşey DEĞİLDİR —
        #  sarım açısı ve kasnak sayıları buradan okunmaz.
        "halat_kurulamadi": fark < -1e-6 or (fark > 1e-6 and saptirma is None),
        "kaide_delikleri": kaide_delikleri,
        "agirlik_dusus": agirlik_dusus,
        "demet": demet,
        "duzlem": dz,
        "y_": y_,
        "hata": hata,
        "S": S,
    }


def _delik_hatalari(delikler, G, D):
    """Döşemedeki halat delikleri kuyunun içinde ve birbirine binmeden."""
    hata = []
    for ad, d in delikler:
        if d[0] < 0 or d[1] < 0 or d[2] > G or d[3] > D:
            hata.append(f"{ad.capitalize()} halatı deliği kuyunun dışına düşüyor.")
    for i, (a1, d1) in enumerate(delikler):
        for a2, d2 in delikler[i + 1 :]:
            if ortusur(d1, d2):
                hata.append(f"{a1.capitalize()} ve {a2.lower()} delikleri üst üste biniyor.")
    return hata


def _sabit_parcalar(M, delikler, saptirma):
    """Odada yeri belli parçalar:  makine, bağlantılar ( 1:1'de yok ), regülatör,
    döşeme delikleri, saptırma kasnağı."""
    parcalar = (
        M["govde"],
        M["kasnak"],
        M["agirlik_baglanti"],
        M["kabin_baglanti"],
        M["reg_govde"],
        M["reg_kasnak"],
    )
    return (
        [k_ for k_ in parcalar if k_] + [d_ for _, d_ in delikler] + ([saptirma["kutu"]] if saptirma else [])
    )


def _saptirma(g, M, dz, y_, ex, fark, hata):
    """SAPTIRMA KASNAĞI:  karşı ağırlık halatı tahrik kasnağının öbür
    teğetinden daha dışarıda inmeliyse ( halat aralığı kasnak çapından büyük )
    saptırma kasnağı onu tam yerine indirir ( LiftDesigner'ın makine
    dairelerindeki gibi );  içeride inmeliyse saptırma kasnağıyla çözülmez.
    Döner:  saptırma kasnağı ya da None ( gerekmiyorsa ya da kurulamıyorsa —
    sebebi hataya )."""
    if fark < -1e-6:
        hata.append(
            f"Karşı ağırlık halatı tahrik kasnağının öbür teğetinden {-fark:g} mm içeride "
            f"inmeli:  halat aralığı kasnak çapından ( {M['D1']:g} ) küçük — saptırma "
            "kasnağıyla çözülmez, tahrik kasnağı çapını ya da ağırlığın yerini değiştirin."
        )
        return None
    if fark <= 1e-6:
        return None
    D2 = g["makine"].get("saptirma_kasnak_capi")
    if not (sayi_mi(D2) and D2 > 0):
        hata.append(
            f"makine.saptirma_kasnak_capi:  halat aralığı tahrik kasnağından {fark:g} mm "
            "büyük — saptırma kasnağı gerekir, çapı girilmeli ( hesap programında "
            "'Saptırma kasnağı çapı' )."
        )
        return None
    ks_ = dz.kanonik(M["kasnak"])
    bk = ks_[3] - ks_[1]
    xd = ex - y_ * D2 / 2.0
    x_, yy_ = dz.p(xd)
    y0 = dz.v0
    return {
        "u": xd,
        "x": x_,
        "y": yy_,
        "D": izli.sayi(D2),
        "bk": bk,
        "kutu": dz.kutu(xd - D2 / 2.0, xd + D2 / 2.0, y0 - bk / 2.0, y0 + bk / 2.0),
    }


def _doseme_delikleri(g, M, dz, agirlik_dusus, n, dh, p):
    """DÖŞEME DELİKLERİ:  [ ( ad, kutu ) ]."""
    if M.get("dogrudan"):
        #  1:1:  kabin halatı ve ağırlık halatı;  demet kasnak ekseni boyunca
        delikler = [
            ("KABİN", makine.halat_deligi(*M["kabin_nokta"], n, dh, p, dz.eksen)),
            ("AĞIRLIK", makine.halat_deligi(*agirlik_dusus, n, dh, p, dz.eksen)),
        ]
    else:
        #  2:1:  halat demetleri kasnak eksenleri boyunca ( tahrik kasnağınınki
        #  düzleme dik;  ağırlık kasnağınınki yandaki ağırlıkta x, arkadakinde y;
        #  arkadaki ağırlıkta kabin bağlantısı çapraz düzlemin ucunda — arka_aski )
        kin = M.get("kabin_inis") or dz.p(M["yakin"])
        kbn = M.get("kabin_baglanti_nokta") or dz.p(M["uzak"])
        delikler = [
            ("KABİN", makine.halat_deligi(*kin, n, dh, p, dz.eksen)),
            ("AĞIRLIK", makine.halat_deligi(*agirlik_dusus, n, dh, p, dz.eksen)),
            (
                "AĞIRLIK BAĞLANTISI",
                makine.halat_deligi(
                    M["ag_teget2"][0], M["ag_teget2"][1], n, dh, p, M.get("ag_baglanti_eksen", "x")
                ),
            ),
            (
                "KABİN BAĞLANTISI",
                makine.halat_deligi(*kbn, n, dh, p, M.get("kabin_baglanti_eksen", dz.eksen)),
            ),
        ]
    #  Regülatör halatı ( tek halat ) da aynı kuralla:  eskiden LiftDesigner'ın
    #  200 × 200'ü kullanılıyordu — ø240 regülatörde iki delik arasında 40 mm,
    #  kuyu duvarına 14 mm kalıyordu.
    rg = g["kuyu_dibi"]["regulator_kasnak_capi"] / 2.0
    rdh = g["kuyu_dibi"]["regulator_halat_capi"]
    return delikler + [
        ("REGÜLATÖR", makine.halat_deligi(M["rgx"], M["rgy"] - rg, 1, rdh, p)),
        ("REGÜLATÖR", makine.halat_deligi(M["rgx"], M["rgy"] + rg, 1, rdh, p)),
    ]


class _KaideAramasi:
    """MAKİNE KAİDESİNİN YERİ ( kullanıcı kararı, 29 Eyl ):

     · KAİDE MAKİNEYİ SARAR:  makinenin ve saptırma kasnağının izi + her yana
       payı ( LiftDesigner 800 KG:  şase makinenin boyunda ).  Yan yatakların
       mesnet aralığı ( hesabın L'si ) buradan çıkar:  boy − dikine kiriş;
       eskiden girilen yan yatak boyuydu ve 400 mm'lik dişlisiz makineye
       1.400 mm'lik kaide kuruluyordu.
     · HALATLAR KAİDEYE ORTALANIR:  tahrik kasnağından ve saptırma kasnağından
       inen halatların ortası kaidenin ortasıdır ( S. Tavaslıoğlu, "Asansörde
       karkas imalatları":  "makine kaidesi önden bakıldığında halat
       deliklerini ortalamalıdır … halatlar makine kaidesi içinden akmalıdır"
       — takozlar eşit yüklenir, kaide yatmaz;  enine eksende iki yan yatağa
       eşit yük:  hesabın F1 = F / 2'si ).  Kaide bunun için izin kısa
       tarafına doğru uzar.  Oda ya da döşeme delikleri buna yer vermiyorsa
       ortaya en yakın konum alınır ( LiftDesigner 1022:  kaide halatlara
       165 mm kaçık ) ve kaide["ortali"] yanlış olur.  Önce enine eksen
       ortalanır ( iki yan yatağa eşit yük hesabın kabulüdür ), sonra uzun
       eksen ( dişli makinede motor kasnaktan uzağa uzanır:  kaide ortalanırsa
       motorun boyu kadar öbür yana taşar — oda buna çoğu zaman yer vermez ).
    Ayak plakaları döşeme deliklerine basmaz ve kaide odaya sığar:  basıyorsa
    pay büyür ( 100 → 200 → 300 ) — önce enine, sonra uzun eksende ( uzun
    eksendeki pay açıklığı, yani momenti büyütür ).  Kaide odanın standart
    alanlarına da yer bırakır:  kumanda panosunun önündeki çalışma alanı ve
    makinenin başındaki bakım alanı ( m.5.2.6.3.2.1 ) — bırakmayan aday
    geçilir ( makine daireli 1:1'de ağırlık arkadayken dişli makinede
    halatlara tam ortalı kaide 2,8 m olup panonun önünü kapatıyordu ).
    Hiçbir aday bırakmıyorsa ilk sığan kaide alınır, alanlar hatasını söyler."""

    ORANLAR = (1.0, 0.75, 0.5, 0.25, 0.0)  # ortalama:  1 tam ortalı, 0 ortalamasız

    def __init__(self, oda, md, S, TB, iz, uzun_x, E, F, delikler, sabit, kapi, kapi_onu, halat_ortasi):
        self.oda, self.md, self.S, self.TB = oda, md, S, TB
        self.iz, self.uzun_x, self.E, self.F = iz, uzun_x, E, F
        self.delikler, self.sabit, self.kapi, self.kapi_onu = delikler, sabit, kapi, kapi_onu
        rc = halat_ortasi
        self.u = (iz[0], iz[2]) if uzun_x else (iz[1], iz[3])  # uzun eksen
        self.e = (iz[1], iz[3]) if uzun_x else (iz[0], iz[2])  # enine eksen
        self.cu, self.ce = (rc[0], rc[1]) if uzun_x else (rc[1], rc[0])
        self.a = makine.ayak_plakasi(E, S)
        self.paylar = [k * S["md_cerceve_pay"] for k in (1, 2, 3)]

    def alanlar(self, c):
        """( pano , çalışma alanı , bakım alanı ) — biri yoksa None."""
        engel = self.sabit + [c, self.kapi_onu]
        pano_, calisma_ = _pano_yeri(self.oda, self.md, self.S, engel, self.kapi, self.TB)
        bakim_ = pano_ and _bakim_yeri(c, engel + [pano_, calisma_], self.oda, self.TB)
        return (pano_, calisma_, bakim_) if bakim_ else None

    @staticmethod
    def _aralik(a0, a1, c, pay, t):
        """İz + pay;  kısa taraf, ortaya ( c ) göre simetriye t kadar uzar."""
        a0, a1 = a0 - pay, a1 + pay
        eksik = (a1 - c) - (c - a0)  # > 0:  a0 tarafı kısa
        return (a0 - t * eksik, a1) if eksik > 0 else (a0, a1 - t * eksik)

    def _kutu(self, pu, pe, tu, te):
        """Aday kaide:  ( kutu, uzun eksendeki boyu )."""
        ua, ub = self._aralik(*self.u, self.cu, pu, tu)
        ea, eb = self._aralik(*self.e, self.ce, pe, te)
        return ((ua, ea, ub, eb) if self.uzun_x else (ea, ua, eb, ub)), ub - ua

    def _deliklere_basar(self, c):
        a = self.a
        plakalar = [
            (x - a / 2.0, y - a / 2.0, x + a / 2.0, y + a / 2.0)
            for x, y in makine.ayaklar(c, self.E, self.F, self.uzun_x)
        ]
        return any(ortusur(p, d_) for p in plakalar for _, d_ in self.delikler)

    def _adaylar(self):
        for te, tu in ((te, tu) for te in self.ORANLAR for tu in self.ORANLAR):
            for pu, pe in ((pu, pe) for pu in self.paylar for pe in self.paylar):
                yield pu, pe, tu, te

    def ara(self):
        """( ( kaide, uzun eksendeki boyu, halatlara ortalı mı ) | None,
        ( pano, çalışma, bakım ) | None )."""
        TB = self.TB
        sigan = None  # ilk sığan ( alanlar kalmasa da )
        for pu, pe, tu, te in self._adaylar():
            c, boy = self._kutu(pu, pe, tu, te)
            #  Kot farkı varsa kaide tabliyenin üstündedir ( halatlar oradan iner ):
            #  taşan aday burada geçilir ( aşağıda kaydırılarak denenir )
            if TB["yukseklik"] > 1e-9 and not icinde(c, TB["izi"]):
                continue
            if not icinde(c, self.oda) or self._deliklere_basar(c):
                continue
            aday = (c, boy, (te, tu) == (1.0, 1.0))
            alanlar = self.alanlar(c)
            if alanlar:
                return aday, alanlar
            if sigan is None:
                sigan = aday
                #  En küçük kaide ( izi + en az pay, ortalamasız ) bile alanlara
                #  yer bırakmıyorsa büyükleri de bırakmaz:  aramaya gerek yok.
                if not self.alanlar(self._kutu(self.paylar[0], self.paylar[0], 0.0, 0.0)[0]):
                    return aday, alanlar
        if sigan is not None:
            return sigan, None
        if TB["yukseklik"] > 1e-9:
            return self._kaydirarak_ara()
        return None, None

    def _kaydirarak_ara(self):
        """Hiçbir aday tabliyeye sığmadı:  taşanlar tabliyenin içine kaydırılır
        ( halatlara ortalılık bozulur;  tabliyenin kenarındaki yanda pay
        daralır — makine halatların yerinde, kuyunun kenarına yakın durabilir );
        odanın alanlarına yer bırakan, enine halatlara ortalı ( iki yan yatağa
        eşit yük ) en küçük kaide, eşitse en az kayan.  Kaydırma ilk aramada
        olsaydı tabliye genişliğinde bir kaide küçük adaylardan önce
        seçilebiliyordu."""
        iz_, kaydirilan = self.TB["izi"], []
        for pu, pe, tu, te in self._adaylar():
            c, boy = self._kutu(pu, pe, tu, te)
            dx = max(0.0, iz_[0] - c[0]) - max(0.0, c[2] - iz_[2])
            dy = max(0.0, iz_[1] - c[1]) - max(0.0, c[3] - iz_[3])
            c = (c[0] + dx, c[1] + dy, c[2] + dx, c[3] + dy)
            #  Kaide makineyi ( ve saptırma kasnağını ) yine sarar;  tabliyenin
            #  kenarındaki yanda payı daralır
            if (
                not icinde(c, iz_)
                or not icinde(c, self.oda)
                or not icinde(self.iz, c)
                or self._deliklere_basar(c)
            ):
                continue
            al_ = self.alanlar(c)
            kaydirilan.append(
                (al_ is None, -te, (c[2] - c[0]) * (c[3] - c[1]), abs(dx) + abs(dy), c, boy, al_)
            )
        if not kaydirilan:
            return None, None
        _, _, _, _, c, boy, alanlar = min(kaydirilan, key=lambda k_: k_[:4])
        return (c, boy, False), alanlar


def _makine_plakasi(g, M, S, dz, kaide, cerceve, makine_izi, saptirma, uk, y_, n, dh, p, demet, hata):
    """MAKİNE PLAKASI, SAPTIRMA KASNAĞININ KOTU, PLAKADAKİ DELİKLER.

    Makine kaidenin iki yan yatağının arasındaki plakaya oturur ( hesap:  yük
    iki yan yatağa, F / 2 ):  plaka yan yatakların arasında, üstleriyle aynı
    hizada, uzun eksende makinenin izi kadar ( uçtaki kısa kirişlerin içinde ).
    Eskiden plaka yoktu:  makine iki yan yatağın arasında havada duruyordu.
    Kotlar DÖŞEMEDEN ( düşey kesit döşemenin kotunu ekler ).  kaide'ye hs, hk,
    plaka yazılır;  saptırma kasnağına kotu.  Döner:  plakadaki delikler."""
    md, F = g["makine_dairesi"], kaide["F"]
    t = makine.MOTOR_PLAKASI_KALINLIK
    hs = md["sase_yuksekligi"]
    hk = hs - makine.DISLI_ZARF["z"][0] if g["makine"]["tip"] == "Dişli" else hs + S["makine_en"] / 2.0
    kaide.update(hs=hs, hk=hk, plaka=None)
    if not cerceve:
        return []
    kb = makine.npu(makine.KAIDE_KISA)["b"]
    if kaide["uzun_x"]:
        plaka = (
            max(makine_izi[0], cerceve[0] + kb),
            cerceve[1] + F["b"],
            min(makine_izi[2], cerceve[2] - kb),
            cerceve[3] - F["b"],
        )
    else:
        plaka = (
            cerceve[0] + F["b"],
            max(makine_izi[1], cerceve[1] + kb),
            cerceve[2] - F["b"],
            min(makine_izi[3], cerceve[3] - kb),
        )
    kaide["plaka"] = plaka
    if saptirma:
        saptirma.update(saptirma_kotu(M, saptirma, dz.kanonik(M["kasnak"]), M["D1"], hs, hk, y_, S))
        if saptirma["z"] + saptirma["D"] / 2.0 > hs - t - 50.0:
            hata.append(
                f"Saptırma kasnağı ( ø {saptirma['D']:g} ) döşemedeki bağlantıların üstünde, "
                "makine plakasının altına sığmıyor — şase yüksekliğini büyütün."
            )
    #  Plakadan geçen halatlar:  tahrik kasnağının iki yanından inenler;
    #  saptırmada ağırlık tarafı eğik iner — plakayı kestiği yerde delik.
    #  Kasnak plakanın altına sarkıyorsa kasnağın kendisi için yuva açılır.
    adaylar = []
    ks = M["kasnak"]
    if hk - M["D1"] / 2.0 < hs:
        adaylar.append((ks[0] - p, ks[1] - p, ks[2] + p, ks[3] + p))
    adaylar.append(makine.halat_deligi(*dz.p(uk), n, dh, p, dz.eksen))
    if saptirma:
        (x1, z1), (x2, z2) = saptirma["P1"], saptirma["P2"]
        xs = [x1 + (z - z1) * (x2 - x1) / (z2 - z1) for z in (hs, hs - t)]
        a_, b_ = dh / 2.0 + p, demet / 2.0 + p
        y0 = dz.v0
        adaylar.append(dz.kutu(min(xs) - a_, max(xs) + a_, y0 - b_, y0 + b_))
    else:
        adaylar.append(makine.halat_deligi(*M["ag_dusus"], n, dh, p, dz.eksen))
    yuva = adaylar[0] if hk - M["D1"] / 2.0 < hs else None
    return makine.plaka_delikleri(
        plaka,
        [
            d
            for d in adaylar
            if d is yuva
            or not (
                yuva
                and yuva[0] <= (d[0] + d[2]) / 2.0 <= yuva[2]
                and yuva[1] <= (d[1] + d[3]) / 2.0 <= yuva[3]
            )
        ],
    )


def _oda_hatalari(M, mk, oda, TB, kapi_onu):
    """Odada durması gerekenler odanın içinde;  kot farkı varsa tabliyenin
    üstünde.  Kapıdan girilen yer tek kotta."""
    hata = []
    for ad, kutu in (
        ("Makine", mk),
        ("Ağırlık bağlantısı", M["agirlik_baglanti"]),
        ("Kabin bağlantısı", M["kabin_baglanti"]),
        ("Regülatör", M["reg_govde"]),
    ):
        if kutu and not icinde(kutu, oda):
            hata.append(f"{ad} makine dairesinin dışına taşıyor.")
        elif kutu and TB["yukseklik"] > 1e-9 and not icinde(kutu, TB["izi"]):
            hata.append(f"{ad} tabliyenin ( kuyunun üstündeki betonun ) dışına taşıyor.")
    #  Oda tabliyeden büyük olmalı ki zemini olsun
    if not tek_kotta(kapi_onu, TB):
        hata.append(
            "Makine dairesi kapısının önü tabliyenin kenarına denk geliyor:  kapının "
            "önündeki geçiş tek kotta olmalı — kapının yerini değiştirin."
        )
    return hata


def _girintiler(oda, TB):
    """Tabliye ile oda duvarı arasında dar şerit kalıyorsa girintidir ( zemin
    tabliyenin altında ):  üstü örtülür ( m.5.2.6.3.2.5 ) — çizimde not.
    [ ( yan, genişlik, şerit ) ]"""
    girintiler = []
    if TB["yukseklik"] <= GIRINTI[0]:
        return girintiler
    iz = TB["izi"]
    for yan, a, b, serit in (
        ("Sol", oda[0], iz[0], (oda[0], max(oda[1], iz[1]), iz[0], min(oda[3], iz[3]))),
        ("Sağ", iz[2], oda[2], (iz[2], max(oda[1], iz[1]), oda[2], min(oda[3], iz[3]))),
        ("Ön", oda[1], iz[1], (max(oda[0], iz[0]), oda[1], min(oda[2], iz[2]), iz[1])),
        ("Arka", iz[3], oda[3], (max(oda[0], iz[0]), iz[3], min(oda[2], iz[2]), oda[3])),
    ):
        if GIRINTI[0] < b - a <= GIRINTI[1]:
            girintiler.append((yan, b - a, serit))
    return girintiler


def saptirma_kotu(M, sp, kasnak, D1, hs, hk, y_, S):
    """Saptırma kasnağının merkezinin döşemeden yüksekliği ve tahrik kasnağıyla
    ortak teğeti ( kotlar döşemeden ).  LiftDesigner'ın 400'ü;  döşemedeki bir
    bağlantının / regülatörün üstüne düşerse onun 50 mm üstüne yükselir.
    Döner:  { z, P1, P2, sarim }."""
    R2 = sp["D"] / 2.0
    z = S["md_saptirma_yukseklik"]
    for kutu_, h_ in (
        (M["agirlik_baglanti"], S["agirlik_baglanti_yukseklik"]),
        (M["kabin_baglanti"], S["kabin_baglanti_alt"] - S["kabin_baglanti_ust"]),
        (M["reg_govde"], S["regulator_govde_alt"] - S["regulator_govde_ust"]),
    ):
        if kutu_ and ortusur(kutu_, sp["kutu"]):
            z = max(z, h_ + 50.0 + R2)
    #  Halat düzleminde ( u, z ):  kasnak kanonik kutu ( u0, v0, u1, v1 )
    mx = (kasnak[0] + kasnak[2]) / 2.0
    P1, P2, n = makine.teget((mx, hk), D1 / 2.0, (sp.get("u", sp["x"]), z), R2, y_)
    return {"z": z, "P1": P1, "P2": P2, "sarim": makine.sarim_acisi(y_, n)}


def _bitisik_adaylar(mk, w, h, adim=25.0):
    """Makinenin dört kenarına bitişik, kenar boyunca kayan adaylar."""
    x0, y0, x1, y1 = mk
    xs = [x0 - w + i * adim for i in range(int((x1 - x0 + w) / adim) + 1)]
    ys = [y0 - h + i * adim for i in range(int((y1 - y0 + h) / adim) + 1)]
    for x in xs:
        yield (x, y1, x + w, y1 + h)
        yield (x, y0 - h, x + w, y0)
    for y in ys:
        yield (x1, y, x1 + w, y + h)
        yield (x0 - w, y, x0, y + h)


def dogrula(g):
    hata = geometri.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _duvarlar(e, oda, t, kapi):
    """Oda duvarları;  kapının duvarı kapı boşluğunun iki yanında iki parça
    ( tarama boşluktan geçmez ).  kapi:  duvardaki boşluğun kutusu."""
    x0, y0, x1, y1 = oda
    for x, y, w, h in (
        (x0 - t, y0 - t, x1 - x0 + 2 * t, t),
        (x0 - t, y1, x1 - x0 + 2 * t, t),
        (x0 - t, y0, t, y1 - y0),
        (x1, y0, t, y1 - y0),
    ):
        parcalar = [(x, y, x + w, y + h)]
        if ortusur(parcalar[0], kapi):
            if w >= h:
                parcalar = [(x, y, kapi[0], y + h), (kapi[2], y, x + w, y + h)]
            else:
                parcalar = [(x, y, x + w, kapi[1]), (x, kapi[3], x + w, y + h)]
        for a, b, c, d in parcalar:
            if c - a > 1e-6 and d - b > 1e-6:
                e.append(eleman.dikdortgen("TARAMA", a, b, c - a, d - b, tip="tarama"))
                e.append(eleman.dikdortgen("KUYU-DUVAR", a, b, c - a, d - b))
    e.append(eleman.dikdortgen("KUYU-IC", x0, y0, x1 - x0, y1 - y0))


def _alan_yazi_yeri(alan):
    """Çalışma / bakım alanının adı:  alanın içindeki iki ölçünün ( altta yatay,
    solda düşey — yazıları kenardan 110 içeride ) dışında kalan parçanın
    ortası.  Eskiden alanın tam ortasındaydı:  yazılar büyüyünce düşey ölçünün
    yazısına biniyordu ( 5 Eki )."""
    pay = 110 + eleman.yb(34) / 2.0 + 15
    return ((alan[0] + pay + alan[2]) / 2.0, (alan[1] + pay + alan[3]) / 2.0)


def _delik_elemanlari(e, Y):
    for _ad, d in Y["delikler"]:
        e.append(eleman.ad(eleman.dikdortgen("DELIK", d[0], d[1], d[2] - d[0], d[3] - d[1]), "delik"))


def ciz(g, cizim_sabitleri=None):
    """Makine dairesi planının elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    md = g["makine_dairesi"]
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    e = []
    _oda_ve_kapi(e, Y, md)
    #  Kuyunun izi
    e.append(eleman.ad(eleman.dikdortgen("GIZLI", 0, 0, G, D), "kuyu_izi"))
    if Y["tabliye"]["yukseklik"] > 1e-9:
        e += _tabliye_kenari(Y)
    _delik_elemanlari(e, Y)
    e += _makine_ve_donanim(Y, md, G)
    e += _olculer(Y, md, G, D)
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e)
    return e


def _kutu(katman, p, ad):
    return eleman.ad(eleman.dikdortgen(katman, p[0], p[1], p[2] - p[0], p[3] - p[1]), ad)


def _oda_ve_kapi(e, Y, md):
    """Odanın duvarları ve kapı:  duvardaki boşluk ( e'ye eklenir )."""
    oda, kp, t = Y["oda"], Y["kapi"], md["duvar"]
    if kp[1] == kp[3]:  # ön / arka duvar
        y = kp[1] if kp[1] > oda[1] else kp[1] - t
        bosluk = (kp[0], y, kp[2], y + t)
        yazi = eleman.yazi((kp[0] + kp[2]) / 2.0, y + t / 2.0, f"KAPI {md['kapi_genislik']:g}", 34)
    else:
        x = kp[0] if kp[0] > oda[0] else kp[0] - t
        bosluk = (x, kp[1], x + t, kp[3])
        yazi = eleman.yazi(x + t / 2.0, (kp[1] + kp[3]) / 2.0, f"KAPI {md['kapi_genislik']:g}", 34, aci=90)
    _duvarlar(e, oda, t, bosluk)
    e.append(_kutu("KAPI", bosluk, "oda_kapisi"))
    e.append(yazi)


def _tabliye_kenari(Y):
    """Tabliye:  kot farkı varsa kenarı ( odanın içinde kalan kenarları ) görünür
    çizgi, üstünde kotu;  0,50 m'yi aşıyorsa merdiven ve korkuluk notu;
    girintilerin notu."""
    TB, oda = Y["tabliye"], Y["oda"]
    iz = (
        max(TB["izi"][0], oda[0]),
        max(TB["izi"][1], oda[1]),
        min(TB["izi"][2], oda[2]),
        min(TB["izi"][3], oda[3]),
    )
    #  ( kenar , içeri yön , kenarla oda duvarı arası )
    kenarlar = [
        ((iz[0], iz[1]), (iz[0], iz[3]), (1, 0), iz[0] - oda[0]),
        ((iz[2], iz[1]), (iz[2], iz[3]), (-1, 0), oda[2] - iz[2]),
        ((iz[0], iz[1]), (iz[2], iz[1]), (0, 1), iz[1] - oda[1]),
        ((iz[0], iz[3]), (iz[2], iz[3]), (0, -1), oda[3] - iz[3]),
    ]
    ic = [k_ for k_ in kenarlar if k_[3] > 1e-6]
    e = [eleman.ad(eleman.cizgi("KUYU-DUVAR", a[0], a[1], b[0], b[1]), "tabliye_kenari") for a, b, _, _ in ic]
    for yan, en, sr in Y["girintiler"]:
        e.append(
            eleman.ad(
                eleman.yazi(
                    (sr[0] + sr[2]) / 2.0,
                    (sr[1] + sr[3]) / 2.0,
                    f"{en:g} GİRİNTİ:  ÜSTÜ ÖRTÜLÜR ( m.5.2.6.3.2.5 )",
                    min(30, en * 0.6),
                    aci=90 if yan in ("Sol", "Sağ") else 0,
                ),
                "girinti_notu",
            )
        )
    if not ic:
        return e
    #  Yazılar odanın asıl zeminine ( en geniş aralığa ) bakan kenarda:
    #  kot yazısı tabliyede, merdiven notu zeminde — aralık dar bir
    #  girintiyse ( notu orada ) tabliyede kot yazısının altında
    a, b, yon, bos = max(ic, key=lambda k_: k_[3])
    cx, cy = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    aci = 90 if yon[0] != 0 else 0
    e.append(
        eleman.ad(
            eleman.yazi(cx + yon[0] * 70, cy + yon[1] * 70, f"TABLİYE  +{TB['yukseklik']:g}", 36, aci=aci),
            "tabliye_yazi",
        )
    )
    if Y["merdiven"]:
        d = -min(bos / 2.0, 300.0) if bos > GIRINTI[1] else 150.0
        e.append(
            eleman.ad(
                eleman.yazi(
                    cx + yon[0] * d,
                    cy + yon[1] * d,
                    f"KOT FARKI {TB['yukseklik']:g} > {KOT_FARKI_MERDIVEN:g}:  MERDİVEN VE KORKULUK ( m.5.2.6.3.2.4 )",
                    30,
                    aci=aci,
                ),
                "merdiven_notu",
            )
        )
    return e


def _makine_ve_donanim(Y, md, G):
    """Makinenin kaidesi, saptırma kasnağı ve makine — parça parça ( makine.py );
    kotlar yalnız çizim sırası için:  kaide ve saptırma kasnağı makinenin
    altında.  Bağlantılar, regülatör, halatlar, kumanda panosu, bakım alanı."""
    M = Y["M"]
    S_, K = M["S"], Y["kaide"]
    H = md["sase_yuksekligi"]
    alt = (
        makine.kaide(
            Y["cerceve"], -3000.0 - H, H, K["E"], K["F"], K["uzun_x"], S_, K["plaka"], Y["kaide_delikleri"]
        )
        if Y["cerceve"]
        else []
    )
    sp = Y["saptirma"]
    if sp:
        d = Y["duzlem"]
        alt += d.parcalar(
            makine.saptirma(
                (sp["u"], d.v0, -3000.0 - H / 2.0), sp["D"], sp["bk"], -3000.0, makine.MOTOR_PLAKASI_KALINLIK
            )
        )
    e = makine.plan(
        alt + makine.plan_parcalari(M, S_, sase=False), eleman.dikdortgen, eleman.daire, eleman.cizgi
    )
    ks = M["kasnak"]
    e.append(eleman.yazi((ks[0] + ks[2]) / 2.0, (ks[1] + ks[3]) / 2.0, f"ø {M['D1']:g}", 38))
    for ad_ in ("agirlik_baglanti", "kabin_baglanti"):  # 1:1 askıda yok
        if M[ad_]:
            e.append(_kutu("BAGLANTI", M[ad_], ad_))
    e.append(_kutu("MAKINE", M["reg_govde"], "regulator"))
    e.append(_kutu("KASNAK", M["reg_kasnak"], "regulator_kasnak"))
    rg = M["reg_govde"]
    e.append(
        eleman.yazi(
            rg[0] - 60 if rg[0] > G / 2 else rg[2] + 60, (rg[1] + rg[3]) / 2.0, "REGÜLATÖR", 34, aci=90
        )
    )
    for hx, hy in M["halatlar"] + [Y["agirlik_dusus"]] + ([M["ag_teget2"]] if M.get("ag_teget2") else []):
        e.append(eleman.ad(eleman.daire("KASNAK", hx, hy, 20), "halat"))
    if Y["pano"]:
        pn, ca = Y["pano"], Y["calisma"]
        e.append(_kutu("PANO", pn, "kumanda_panosu"))
        e.append(_kutu("SIGINMA", ca, "calisma_alani"))
        dik = (pn[2] - pn[0]) < (pn[3] - pn[1])
        e.append(
            eleman.yazi(
                (pn[0] + pn[2]) / 2.0, (pn[1] + pn[3]) / 2.0, "KUMANDA PANOSU", 32, aci=90 if dik else 0
            )
        )
        e.append(eleman.yazi(*_alan_yazi_yeri(ca), "ÇALIŞMA ALANI", 32, aci=90 if dik else 0))
    if Y["bakim"]:
        e.append(_kutu("SIGINMA", Y["bakim"], "bakim_alani"))
        e.append(eleman.yazi(*_alan_yazi_yeri(Y["bakim"]), "BAKIM ALANI", 32))
    return e


def _olculer(Y, md, G, D):
    """Oda ve odanın kuyuya göre yeri;  çalışma ve bakım alanlarının ölçüleri
    ( standardın sayıları )."""
    oda, t = Y["oda"], md["duvar"]
    u0, u1 = oda[3] + t + 120, oda[3] + t + 320
    xs = sorted({oda[0], oda[2], 0.0, G})
    e = [
        eleman.olcu("yatay", (a_, 0), (b_, 0), u0, "KUYU " + f"{G:g}" if (a_, b_) == (0.0, G) else None)
        for a_, b_ in zip(xs, xs[1:])
    ]
    e.append(eleman.olcu("yatay", (oda[0], 0), (oda[2], 0), u1, f"MAKİNE DAİRESİ {oda[2] - oda[0]:g}"))
    s0, s1 = oda[2] + t + 120, oda[2] + t + 320
    ys = sorted({oda[1], oda[3], 0.0, D})
    e += [
        eleman.olcu("dusey", (0, a_), (0, b_), s0, "KUYU " + f"{D:g}" if (a_, b_) == (0.0, D) else None)
        for a_, b_ in zip(ys, ys[1:])
    ]
    e.append(eleman.olcu("dusey", (0, oda[1]), (0, oda[3]), s1, f"MAKİNE DAİRESİ {oda[3] - oda[1]:g}"))
    for alan, kural in (
        (
            Y["calisma"],
            "Kumanda panosu önündeki çalışma alanı:  derinliği 0,70 m, eni "
            "panonun eni ya da en az 0,50 m ( TS EN 81-20 m.5.2.6.3.2.1 a ).  "
            "Yerini program kapıya en yakın uygun yere koyar.",
        ),
        (
            Y["bakim"],
            "Makinenin başındaki bakım alanı:  0,50 × 0,60 m ( TS EN 81-20 "
            "m.5.2.6.3.2.1 b ).  Yerini program makineye en yakın boş yere koyar.",
        ),
    ):
        if not alan:
            continue
        e.append(
            eleman.olcu(
                "yatay",
                (alan[0], 0),
                (alan[2], 0),
                alan[1] + 60,
                f"{alan[2] - alan[0]:g}",
                kural=kural,
                yazi={"x": (alan[0] + alan[2]) / 2.0, "y": alan[1] + 110, "h": eleman.yb(34)},
            )
        )
        e.append(
            eleman.olcu(
                "dusey",
                (0, alan[1]),
                (0, alan[3]),
                alan[0] + 60,
                f"{alan[3] - alan[1]:g}",
                kural=kural,
                yazi={"x": alan[0] + 110, "y": (alan[1] + alan[3]) / 2.0, "aci": 90, "h": eleman.yb(34)},
            )
        )
    return e


def delik_plani(g, cizim_sabitleri=None):
    """Kuyu üstü döşeme halat delik planı:  döşeme, delikler ve yerleri."""
    Y = yerlesim(g, cizim_sabitleri)
    k = g["kuyu"]
    G, D, dg, dar = k["genislik"], k["derinlik"], k["duvar_sag"], k["duvar_arka"]
    e = [
        el
        for el in geometri.plan(g, Y["S"], kapi_duzeyi=False)
        if el["katman"] in ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "EKSEN") and el["tip"] != "yazi"
    ]
    _delik_elemanlari(e, Y)
    for _ad, d in Y["delikler"]:
        w, h = d[2] - d[0], d[3] - d[1]
        dik = h > w
        e.append(
            eleman.yazi(
                (d[0] + d[2]) / 2.0 + (0 if dik else 0),
                (d[1] + d[3]) / 2.0,
                f"{round(w):g} x {round(h):g}",
                30,
                aci=90 if dik else 0,
            )
        )
    #  Deliklerin yeri EKSENLERİNDEN ölçülür ( inşaat çiziminde delik böyle
    #  verilir );  kenardan ölçülünce 31 – 66 mm'lik parçalarla dolan bir
    #  zincir çıkıyordu.  Her deliğin ekseni kısa çizgiyle işaretlenir.
    for _, d in Y["delikler"]:
        cx, cy = (d[0] + d[2]) / 2.0, (d[1] + d[3]) / 2.0
        e.append(eleman.cizgi("EKSEN", d[0] - 40, cy, d[2] + 40, cy, tip="eksen"))
        e.append(eleman.cizgi("EKSEN", cx, d[1] - 40, cx, d[3] + 40, tip="eksen"))
    xs = sorted({0.0, G} | {round((d[0] + d[2]) / 2.0, 3) for _, d in Y["delikler"]})
    ys = sorted({0.0, D} | {round((d[1] + d[3]) / 2.0, 3) for _, d in Y["delikler"]})
    u0, u1 = D + dar + 120, D + dar + 320
    s0, s1 = G + dg + 120, G + dg + 320
    e += [eleman.olcu("yatay", (a_, 0), (b_, 0), u0) for a_, b_ in zip(xs, xs[1:])]
    e.append(eleman.olcu("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"))
    e += [eleman.olcu("dusey", (0, a_), (0, b_), s0) for a_, b_ in zip(ys, ys[1:])]
    e.append(eleman.olcu("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"))
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e)
    return e
