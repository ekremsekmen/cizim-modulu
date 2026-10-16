# -*- coding: utf-8 -*-
"""
KUYU DÜŞEY KESİTLERİ  ( tam boy, 1/50 )

  A-A  YAN KESİT   kuyu derinliği boyunca;  ön duvar ( kat kapıları ) solda.
                   Kabin EN ALT durakta, karşı ağırlık yukarıda
                   ( referans proje "Cabin at Bottom Floor" ).
  B-B  ÖN KESİT    kuyu genişliği boyunca, kuyunun arkasından kat kapılarına
                   bakış ( plandaki sol duvar sağda görünür ).  Kabin EN ÜST
                   durakta, karşı ağırlık aşağıda ( referans proje "Cabin at Top
                   Floor", LiftDesigner "Dikey 1:50" ).

İkisi de gerçek ölçekte, bütün duraklarla ( LiftDesigner gibi;  referans proje ara
katları kırar ).  Çizilenler:

  · kuyu duvarları, kuyu dibi ve tavan döşemesi, kat döşemeleri, kat kapıları
    ( yanda kesit, önde görünüş ), kotlar ve durak adları
  · kabin ve karşı ağırlık raylarının tamamı:  üst uçları, konsolları
    ( konsollar arası:  hesap programının girdisi ), ek yerleri
  · kabin ( şase, patenler, fren blokları, 2:1 kasnakları ) ve karşı ağırlık
    ( çerçeve, kasnak, patenler )
  · makine dairesizde kuyu tepesi:  makine şasesi, makine, tahrik kasnağı,
    halat bağlantıları, hız regülatörü;  kuyu dibinde tamponlar ve gergi düzeni
  · askı halatları ( 2:1 ) ve regülatör halatı

Kotlar donanim.py'de, planla aynı yerlerden;  açıklık denetimleri dusey.py'de
( bu kesitler de aynı yerleşimle durur ).
"""

from cizim import eleman
from cizim import kisaltmalar
from cizim import uslup
from cizim import arka_aski
from cizim import donanim
from cizim import dusey
from cizim import geometri
from cizim import girdi
from cizim import kesit_parcalari
from cizim import makine_dairesi
from cizim import parca_kotlari

OLCEK = 50

#  Planların düşey kesitlerdeki seviye işaretleri ( LiftDesigner'ın X-X · Y-Y ·
#  Z-Z'si gibi ):  A ve B düşey kesitlerindir, planlar C'den başlar.  Plan
#  başlıkları aynı harfi taşır ( calistir.py ).  Hangi yükseklikten:
#    C  kuyu planı       en alt durakta kapının orta yüksekliği ( kabin ve kapı kesilir )
#    D  kabin üstü       kabinin tavanı ( kesitteki kabinin )
#    E  kuyu dibi        kuyu dibinin ortası ( tamponlar kesilir )
#    F  kuyu üstü        tahrik kasnağının ekseni ( makine kesilir );
#       makine dairesi   makine daireli projede aynı kural, odada
#    G  delik planı      makine dairesi döşemesinin ortası
PLAN_HARFLERI = {
    "kuyu_plani": "C",
    "kabin_ustu": "D",
    "kuyu_dibi": "E",
    "kuyu_ustu": "F",
    "makine_dairesi": "F",
    "delik_plani": "G",
}


def yerlesim(g, cizim_sabitleri=None):
    return dusey.yerlesim(g, cizim_sabitleri)


def dogrula(g):
    hata = dusey.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def _duvar(e, u, z, w, h, ad=None):
    e.append(eleman.dikdortgen("TARAMA", u, z, w, h, tip="tarama"))
    el = eleman.dikdortgen("KUYU-DUVAR", u, z, w, h)
    if ad:
        eleman.ad(el, ad)
    e.append(el)


def _zincir(e, kot, noktalar, metinler=None):
    """Düşey zincir.  metinler:  { sıra:  yazı ya da ( yazı , kimlik ) }."""
    metinler = metinler or {}
    for i, (a, b) in enumerate(zip(noktalar, noktalar[1:])):
        if b - a > 1e-6:
            m = metinler.get(i)
            metin, ad = m if isinstance(m, tuple) else (m, None)
            e.append(eleman.olcu("dusey", (0, a), (0, b), kot, metin, ad=ad))


def _oda(e, B, g, Y, K, uzak_duvar, kesilen, u_kot):
    """Makine dairesi:  tabliye ( kuyunun üstündeki beton;  makine onun
    üstünde ), oda zemini ( tabliyenin "tabliye beton yüksekliği" altında,
    kuyunun dışında ), çatı, kesilen iki duvar ( kesit kapıdan geçiyorsa
    boşluklu ), karşıdaki duvarda kapı görünüşü, tabliyedeki delikler
    ( kesik ), zeminin ve tabliyenin kotu ( merdiven notu planda —
    makine_dairesi.ciz ).  Eskiden kuyu tavanının üstüne
    1.200 kalınlığında beton çiziliyordu ( kullanıcı 5 Eki )."""
    M, md = Y["M"], g["makine_dairesi"]
    MD = M["MD"]
    x0, y0, x1, y1 = MD["oda"]
    w = md["duvar"]
    TB = M["tabliye"]
    tv, zt, zd, ztv = M["tavan"], M["tabliye_ustu"], M["oda_doseme"], M["oda_tavan"]
    dis = (x0 - w, y0 - w, x1 + w, y1 + w)
    #  Tabliye kuyu duvarlarının üstünde ( kuyu tavanı döşemesi:  kesitin kendi
    #  çizdiği );  oda zemini yalnız kuyunun DIŞINDA — kuyunun içinden bakınca
    #  yan duvarın ardında kalır.  Zemin döşemesi tabliyeninkiyle aynı kalınlıkta.
    du0, du1 = B.aralik(dis)
    tu0, tu1 = B.aralik(TB["izi"])
    for a, b in ((du0, tu0), (tu1, du1)):
        if b - a > 1e-6:
            e.append(eleman.dikdortgen("TARAMA", a, zd - TB["doseme"], b - a, TB["doseme"], tip="tarama"))
            e.append(
                eleman.ad(
                    eleman.dikdortgen("KUYU-DUVAR", a, zd - TB["doseme"], b - a, TB["doseme"]), "oda_dosemesi"
                )
            )
    B.kutu(e, "TARAMA", dis, ztv, ztv + M["cati"], tip="tarama")
    B.kutu(e, "KUYU-DUVAR", dis, ztv, ztv + M["cati"], "oda_catisi")

    def zemin(k):
        """Kutunun durduğu zeminin kotu:  tabliyenin üstü ya da oda zemini."""
        return zt if makine_dairesi.icinde(k, TB["izi"]) else zd

    duvarlar = {
        "Ön": (x0 - w, y0 - w, x1 + w, y0),
        "Arka": (x0 - w, y1, x1 + w, y1 + w),
        "Sol": (x0 - w, y0 - w, x0, y1 + w),
        "Sağ": (x1, y0 - w, x1 + w, y1 + w),
    }
    kp, kh = MD["kapi"], md["kapi_yukseklik"]
    kx, yb = geometri.kesit_duzlemleri(g)
    for ad in kesilen:
        kutu = duvarlar[ad]
        kapidan = md["kapi_duvar"] == ad and (
            kp[0] < kx < kp[2] if ad in ("Ön", "Arka") else kp[1] < yb < kp[3]
        )
        #  Duvar kuyunun üstündeyse tabliyede ( kuyu duvarı onu taşır ), değilse
        #  oda zemininde başlar.  Kesitte görünen, duvarın kesit düzlemindeki
        #  dilimidir:  ona bakılır.  Eskiden duvarın bütün boyuna bakılıyordu —
        #  bir ucu kuyunun dışına taşan duvar, kuyunun üstündeki diliminde de
        #  oda zeminine iniyor, tabliyenin altında kuyunun içinden geçiyordu.
        dilim = (kx, kutu[1], kx, kutu[3]) if ad in ("Ön", "Arka") else (kutu[0], yb, kutu[2], yb)
        za = zemin(dilim)
        zk = zemin(kp)
        zb = zk + kh if kapidan else za
        B.kutu(e, "TARAMA", kutu, zb, ztv, tip="tarama")
        B.kutu(e, "KUYU-DUVAR", kutu, zb, ztv, "oda_duvari")
        if kapidan:
            if za < zk - 1e-6:
                B.kutu(e, "TARAMA", kutu, za, zk, tip="tarama")
                B.kutu(e, "KUYU-DUVAR", kutu, za, zk, "oda_duvari")
            B.kutu(e, "KAPI", kutu, zk, zb, "oda_kapisi")
    if md["kapi_duvar"] == uzak_duvar:
        B.kutu_ardinda(e, "KAPI", kp, zemin(kp), zemin(kp) + kh, "oda_kapisi", TB["izi"], zt)
    for _, d in MD["delikler"]:
        B.kutu(e, "GIZLI", d, tv, zt, "doseme_deligi")
    u0, u1 = B.aralik(dis)
    e.append(
        eleman.ad(eleman.yazi((u0 + u1) / 2.0, ztv - 250 * K, "MAKİNE DAİRESİ", uslup.NORMAL * K), "oda_adi")
    )
    #  Kot işaretleri odanın dışında:  oda kuyudan genişse duvarının ötesinde
    #  ( eskiden kuyunun yanında, odanın duvarının üstüne düşüyordu )
    u_kot = min(u_kot, u0 - 200 * K)
    kesit_parcalari.kot_isareti(e, u_kot, zd, dusey.kot_yazisi(zd), K, -1.0)
    if zt - zd >= 300.0:
        kesit_parcalari.kot_isareti(e, u_kot, zt, dusey.kot_yazisi(zt), K, -1.0)
    return u1


def _oda_olculeri(e, M, md, D1, kot_makine, kot_oda):
    """Makine dairesinde:  şase · kasnak · kasnak üstü ( m.5.2.6.3.2.3 );  oda
    zemininden tabliye · tabliyenin üstünde temiz yükseklik ( m.5.2.6.3.2.1 ) ·
    çatı;  dışta odanın temiz yüksekliği."""
    zt, zd, ztv, c = M["tabliye_ustu"], M["oda_doseme"], M["oda_tavan"], M["cati"]
    sa = M["sase"]
    ku = M["kasnak"][4] + D1 / 2.0
    _zincir(
        e,
        kot_makine,
        [zt, sa[5], ku, ztv],
        {0: f"ŞASE {sa[5] - zt:g}", 2: f"KASNAK ÜSTÜ {ztv - ku:g} ≥ {donanim.DONEN_PARCA_USTU:g}"},
    )
    _zincir(
        e,
        kot_oda,
        [zd, zt, ztv, ztv + c],
        {0: f"TABLİYE {zt - zd:g}", 1: f"{ztv - zt:g} ≥ {donanim.ODA_YUKSEKLIK:g}", 2: f"{c:g}"},
    )
    if zt - zd > 1e-6:
        e.append(
            eleman.olcu(
                "dusey",
                (0, zd),
                (0, ztv),
                kot_oda + (kot_oda - kot_makine),
                f"MAKİNE DAİRESİ {md['yukseklik']:g} ≥ {donanim.ODA_YUKSEKLIK:g}",
            )
        )


def kuyu_dibi_seviyesi(g, Y):
    """Kuyu dibi planının ( E-E ) kesit kotu.  Kabin bu planda YOKTUR:  kesit,
    en alt duraktaki kabinin en alt noktasının ( etek, alt paten, fren bloğu,
    kabin kasnağı ) altından geçer;  ilk konsolların üstünde kalır ki konsollar,
    gergi ve tamponlar planda görünsün — ikisinin ortası.  Konsol kabinin
    altına sığmıyorsa kuyu tabanıyla kabinin ortası."""
    kt = parca_kotlari.kabin_kotlari(
        g["dusey"], Y["S"], Y["kotlar"][0], g.get("aski"), arka_aski.arkada_iki_bir(g)
    )
    kabin_alti = min(kt["etek_alti"], kt["sase_alt"], kt["alt_paten"], kt["fren_alti"])
    if Y["kasnaklar"]:
        kabin_alti = min(kabin_alti, kt["kasnak_merkez"] - Y["kasnak_capi"] / 2.0)
    konsol = max((r["konsollar"][0] for r in Y["M"]["raylar"] if r["konsollar"]), default=Y["taban"])
    return ((konsol if konsol < kabin_alti else Y["taban"]) + kabin_alti) / 2.0


def plan_seviyeleri(g, Y, kt):
    """( harf, kot, plan ) — kt:  kesitteki kabinin kotları."""
    M = Y["M"]
    oda = "MD" in M
    sev = [
        (PLAN_HARFLERI["kuyu_plani"], Y["kotlar"][0] + g["kapi"]["yukseklik"] / 2.0, "kuyu_plani"),
        (PLAN_HARFLERI["kabin_ustu"], kt["tavan"], "kabin_ustu"),
        (PLAN_HARFLERI["kuyu_dibi"], kuyu_dibi_seviyesi(g, Y), "kuyu_dibi"),
        (PLAN_HARFLERI["kuyu_ustu"], M["kasnak"][4], "makine_dairesi" if oda else "kuyu_ustu"),
    ]
    if oda:
        sev.append((PLAN_HARFLERI["delik_plani"], M["tavan"] + M["tabliye"]["doseme"] / 2.0, "delik_plani"))
    return sev


def _seviye_isaretleri(e, sev, K):
    """Çizimin iki yanına uzanan kesik çizgi, uçlarında ▽ ve harf ( bakış aşağı )."""
    u0, _, u1, _ = geometri.sinir(e)
    u0, u1 = u0 - 150 * K, u1 + 150 * K
    w, h = 45 * K, 60 * K
    #  İşaretin boyu ( ▽ + harf ):  daha yakın iki seviyeden ALTTAKİNİN işareti
    #  dışarı kayar — üstteki çizgi onun harfinin üstünden geçmesin.
    boy, kay = h + 120 * K, 2 * w + 60 * K
    sira, onceki = 0, None
    for harf, z, ad in sorted(sev, key=lambda s_: -s_[1]):
        sira = sira + 1 if onceki is not None and onceki - z < boy else 0
        onceki = z
        a0, a1 = u0 - sira * kay, u1 + sira * kay
        e.append(eleman.ad(eleman.cizgi("SEVIYE", a0, z, a1, z, tip="eksen"), "plan_seviyesi_" + ad))
        for u in (a0 + w, a1 - w):
            for a, b in (
                ((u - w, z + h), (u + w, z + h)),
                ((u - w, z + h), (u, z)),
                ((u, z), (u + w, z + h)),
            ):
                e.append(eleman.cizgi("SEVIYE", a[0], a[1], b[0], b[1]))
            e.append(eleman.ad(eleman.yazi(u, z + h + 70 * K, harf, uslup.HARF * K), "plan_harfi"))


def _kat_seviyeleri(e, g, S, kotlar, u_duvar, K, yon):
    """Kot işaretleri ve durak adları ( duvarın dışında )."""
    for i, z in enumerate(kotlar):
        kesit_parcalari.kot_isareti(e, u_duvar + yon * 200 * K, z, dusey.kot_yazisi(z), K, yon)
        e.append(
            eleman.ad(
                eleman.yazi(
                    u_duvar + yon * 120 * K,
                    z + 1100,
                    f"{i + 1}. DURAK",
                    uslup.NORMAL * K,
                    hiza="sol" if yon > 0 else "sag",
                ),
                "durak_adi",
            )
        )


def _olculer_sol(e, Y, u0, K, kotlar, tavan, g):
    """Kuyu dibi + kat yükseklikleri + son kat · seyir · kuyu yüksekliği."""
    H = kotlar[-1]
    s0, s1, s2 = (u0 - (geometri.SIRA_ARASI * i) * K for i in range(3))
    zincir = [Y["taban"]] + kotlar + [tavan]
    #  Son kat ( kuyu üst boşluğu ) LiftDesigner'ın OH'si;  kuyu dibi, seyir ve
    #  kuyu yüksekliği LD'de de Türkçe yazılır ( "Kuyu dibi1700", "Seyir15000" )
    _zincir(
        e,
        s0,
        zincir,
        {
            0: f"KUYU DİBİ {-Y['taban']:g}",
            len(zincir) - 2: (kisaltmalar.kodlu("OH", tavan - H), "kuyu_ust_boslugu"),
        },
    )
    e.append(eleman.olcu("dusey", (0, 0.0), (0, H), s1, f"SEYİR {H:g}"))
    e.append(eleman.olcu("dusey", (0, Y["taban"]), (0, tavan), s2, f"KUYU YÜKSEKLİĞİ {tavan - Y['taban']:g}"))


def _konsol_zinciri(e, kot, r, tavan, ad, aralik):
    noktalar = [r["alt"]] + r["konsollar"] + [r["ust"], tavan]
    #  Etiket ikinci aralıkta:  kırık gösterimde de görünür kalır
    _zincir(
        e,
        kot,
        noktalar,
        {0: f"İLK KONSOL {r['konsollar'][0] - r['alt']:g}", 1: f"{ad} KONSOL ARASI {aralik:g}"},
    )


KIRIK_BOSLUK = 1200.0  # kırık gösterimde atlanan katların yerine kalan yükseklik
KIRIK_PAY = 300.0  # kırık çizgisi ile en yakın parça arası


def _sayisal(m):
    return m.replace(".", "").isdigit()


def _birlesik_metin(parcalar, uzunluk):
    """Kırığın üstünden geçen ölçünün yazısı:  eşit aralıklar "n × a",
    değilse gerçek toplam."""
    metinler = [p[2]["metin"] for p in parcalar]
    if all(_sayisal(m) for m in metinler) and len(set(metinler)) == 1 and len(metinler) > 1:
        return f"{len(metinler)} × {metinler[0]}"
    return f"{uzunluk:g}"


def _kir(e, za, zu, bosluk):
    """( za, zu ) aralığını çizimden çıkarır, yerine `bosluk` bırakır.

    Aralığın içindeki parçalar ( ara katların kapıları, konsollar, kotlar )
    düşer;  aralığı geçen dikdörtgen ve düşey çizgiler ( duvar, ray, halat )
    ikiye bölünür;  düşey ölçü zincirleri yeniden kurulur — aralığı geçen
    ölçü gerçek değerini yazar.  Dönen:  ( elemanlar, kot eşlemesi, içinde mi ).
    """
    kay = (zu - za) - bosluk

    def ic(z):
        return za + 1e-9 < z < zu - 1e-9

    def m(z):
        return z if z <= za + 1e-9 else z - kay

    def bol(y0, y1):
        lo, hi = sorted((y0, y1))
        return [(a, b) for a, b in ((lo, min(hi, za)), (max(lo, zu), hi)) if b - a > 1e-6]

    out, olculer = [], {}
    for el in e:
        t = el["tip"]
        if t == "olcu":
            if el["yon"] == "dusey":
                olculer.setdefault(round(el["kot"], 3), []).append(el)
            elif not (ic(el["a"][1]) or ic(el["kot"])):
                n = dict(el)
                n["a"], n["b"], n["kot"] = (
                    (el["a"][0], m(el["a"][1])),
                    (el["b"][0], m(el["b"][1])),
                    m(el["kot"]),
                )
                out.append(n)
        elif t in ("dikdortgen", "tarama"):
            for a, b in bol(el["y"], el["y"] + el["d"]):
                n = dict(el)
                n["y"], n["d"] = m(a), b - a
                out.append(n)
        elif t in ("cizgi", "eksen", "ok"):
            y1, y2 = el["y1"], el["y2"]
            if abs(y1 - y2) < 1e-9:
                if not ic(y1):
                    n = dict(el)
                    n["y1"] = n["y2"] = m(y1)
                    out.append(n)
                continue
            for a, b in bol(y1, y2):
                n = dict(el)
                ta, tb = ((a - y1) / (y2 - y1), (b - y1) / (y2 - y1))
                n["x1"], n["x2"] = (
                    el["x1"] + (el["x2"] - el["x1"]) * ta,
                    el["x1"] + (el["x2"] - el["x1"]) * tb,
                )
                n["y1"], n["y2"] = m(a), m(b)
                out.append(n)
        elif t in ("daire", "yazi"):
            if not ic(el["y"]):
                n = dict(el)
                n["y"] = m(el["y"])
                out.append(n)
        else:
            out.append(el)
    for kot, liste in olculer.items():
        parcalar = sorted((min(el["a"][1], el["b"][1]), max(el["a"][1], el["b"][1]), el) for el in liste)
        noktalar = sorted({p for q in parcalar for p in q[:2]})
        tut = [p for p in noktalar if not ic(p)]
        for p, q in zip(tut, tut[1:]):
            icinde = [r for r in parcalar if r[0] >= p - 1e-9 and r[1] <= q + 1e-9]
            if not icinde:
                continue
            tek = len(icinde) == 1 and abs(icinde[0][0] - p) < 1e-9 and abs(icinde[0][1] - q) < 1e-9
            metin = icinde[0][2]["metin"] if tek else _birlesik_metin(icinde, q - p)
            x = icinde[0][2]["a"][0]
            yeni = eleman.olcu("dusey", (x, m(p)), (x, m(q)), kot, metin)
            #  Kırıktan geçmeyen tek ölçü kimliğini korur ( OH — ölçüye tıklama )
            if tek and "ad" in icinde[0][2]:
                yeni["ad"] = icinde[0][2]["ad"]
            out.append(yeni)
    return out, m, ic


def _kirik_cizgileri(e, za, bosluk, u0, u1, K):
    """Kırığın iki ucunda, kuyunun iki duvarını aşan kırık çizgisi."""
    for z in (za, za + bosluk):
        um = (u0 + u1) / 2.0
        d, t = 60 * K, 30 * K
        nok = [
            (u0 - 150 * K, z),
            (um - d, z),
            (um - t, z + d),
            (um + t, z - d),
            (um + d, z),
            (u1 + 150 * K, z),
        ]
        for a, b in zip(nok, nok[1:]):
            e.append(eleman.ad(eleman.cizgi("KUYU-IC", a[0], a[1], b[0], b[1]), "kirik_cizgisi"))


def _yukseklik(e, K):
    """Çerçeveli çizimin yüksekliği ( cerceveli:  2 · pay + künye şeridi )."""
    _, y0, _, y1 = geometri.sinir(e)
    return (y1 - y0) + 2 * 300 * K + 220 * K


def _bitir(e, g, Y, kt, K, alt_ust, ust_alt, bosluk_h, duvarlar, azami):
    """Yazıları yerleştirir, plan seviyelerini ekler.  Çizim `azami`
    yüksekliğe ( çerçevesiyle, çizim birimi ) sığmıyorsa ara katları kırar:
    alttan ve üstten SIĞAN EN ÇOK durak kalır ( en az birer ).  Kırık
    hareketli parçalara ( kabin, karşı ağırlık ) değmez."""
    sev = plan_seviyeleri(g, Y, kt)

    def son(e_, m=None, ic=None):
        e_ = [dict(x) for x in e_]
        geometri.yazilari_yerlestir(e_, eleman.OLCU_YAZI * K)
        s_ = [(h, m(z) if m else z, ad) for h, z, ad in sev if not (ic and ic(z))]
        _seviye_isaretleri(e_, s_, K)
        return e_

    tam = son(e)
    if azami is None or _yukseklik(tam, K) <= azami:
        return tam
    kotlar = Y["kotlar"]
    doseme = Y["S"]["kat_doseme_kalinlik"]
    for i in range(len(kotlar) // 2 - 1, -1, -1):
        za = max(alt_ust, kotlar[i] + bosluk_h) + KIRIK_PAY
        zu = min(ust_alt, kotlar[-1 - i] - doseme) - KIRIK_PAY
        if zu - za <= KIRIK_BOSLUK:
            continue
        k, m, ic = _kir(e, za, zu, KIRIK_BOSLUK)
        _kirik_cizgileri(k, za, KIRIK_BOSLUK, duvarlar[0], duvarlar[1], K)
        k = son(k, m, ic)
        if _yukseklik(k, K) <= azami or i == 0:
            return k
    return tam


def yan_bakis(g):
    """A-A:  kabin ekseninden karşı ağırlık tarafına bakış."""
    return kesit_parcalari.Bakis(
        "yan",
        g["kuyu"]["genislik"],
        ("x", geometri.kesit_duzlemleri(g)[0], -1.0 if g["agirlik"]["yeri"] == "Sol" else 1.0),
    )


def _yan_katlar(e, S, P, kotlar, u0, L, kapi_h):
    """A-A'da katlar:  döşeme ( u0'dan L boyunca ), kat kapısı ( kasa, eşik, kanatlar )."""
    for zk in kotlar:
        _duvar(e, u0, zk - S["kat_doseme_kalinlik"], L, S["kat_doseme_kalinlik"], "kat_dosemesi")
        for kk in P["kasa"]:
            e.append(
                eleman.ad(
                    eleman.dikdortgen(
                        "KAPI",
                        kk[1],
                        zk - S["esik_kalinlik"],
                        kk[3] - kk[1],
                        kapi_h + S["kasa_ust"] + S["esik_kalinlik"],
                    ),
                    "kapi_kasasi",
                )
            )
        for kk in P["esik"]:
            e.append(
                eleman.ad(
                    eleman.dikdortgen(
                        "KAPI", kk[1], zk - S["esik_kalinlik"], kk[3] - kk[1], S["esik_kalinlik"]
                    ),
                    "kat_esigi",
                )
            )
        for kk in P["kanat"]:
            e.append(eleman.ad(eleman.dikdortgen("KAPI", kk[1], zk, kk[3] - kk[1], kapi_h), "kat_kapisi"))


def _yan_kabin_kapisi(e, S, P, doseme, kapi_h):
    """Kabin eşiği ve kabin kapısı kanatları ( kabinin önünde, kendi döşemesinde )."""
    for kk in P["kabin_esik"]:
        e.append(
            eleman.ad(
                eleman.dikdortgen(
                    "KABIN", kk[1], doseme - S["esik_kalinlik"], kk[3] - kk[1], S["esik_kalinlik"]
                ),
                "kabin_esigi",
            )
        )
    for kk in P["kabin_kanat"]:
        e.append(eleman.ad(eleman.dikdortgen("KAPI", kk[1], doseme, kk[3] - kk[1], kapi_h), "kabin_kanadi"))


def yan_kesit(g, cizim_sabitleri=None, azami=None):
    """A-A:  kabin en alt durakta.  azami:  çerçevesiyle en çok yükseklik
    ( çizim birimi ) — aşılırsa ara katlar kırılır."""
    Y = yerlesim(g, cizim_sabitleri)
    S, M, KD, dy = Y["S"], Y["M"], Y["KD"], g["dusey"]
    k = g["kuyu"]
    D, don, dar = k["derinlik"], k["duvar_on"], k["duvar_arka"]
    dos = k.get("doseme", don)  # kuyu dibi ve tavan döşemesi
    K = OLCEK / 20.0
    B = yan_bakis(g)
    P = kesit_parcalari.plan_parcalari(Y["KD"], g)
    kotlar = Y["kotlar"]
    H = kotlar[-1]
    tavan = H + dy["son_kat"]
    taban = Y["taban"]
    kapi_h = g["kapi"]["yukseklik"]
    bosluk_h = girdi.kaba_bosluk(g, S)[2]
    oda = "MD" in M
    ust = tavan + dos  # makine dairesinde tabliye ( aynı kalınlık )
    e = []
    #  Ön duvar kapı boşluklarıyla, arka duvar, kuyu dibi ve tavan döşemesi.
    #  Kapı ünitesi duvar boşluğundaysa boşluk eşiğin altından başlar ( kasa ve
    #  eşik döşemenin esik_kalinlik altına iner;  tarama onlara binmez ).
    alt = S["esik_kalinlik"] if g["kapi"]["montaj"] == "Duvar boşluğuna" else 0.0
    z = taban - dos
    for zk in kotlar:
        _duvar(e, -don, z, don, zk - alt - z)
        z = zk + bosluk_h
    _duvar(e, -don, z, don, ust - z)
    _duvar(e, D, taban - dos, dar, ust - (taban - dos))
    _duvar(e, 0, taban - dos, D, dos)
    _duvar(e, 0, tavan, D, dos, "tabliye" if oda else None)
    #  Kuyu tavanının en alt kısmı ( kiriş payı — hesap programının "kuyu tavanı
    #  payı" ):  bir KABULDÜR, beton değil;  kesik sınır çizgisi ( eskiden taralı
    #  150 mm bir katman gibi çiziliyor, tavan iki kat kalın görünüyordu ).
    e.append(eleman.ad(eleman.cizgi("GIZLI", 0, Y["tavan_alti"] + H, D, Y["tavan_alti"] + H), "tavan_kirisi"))
    L = 240 * K
    _yan_katlar(e, S, P, kotlar, -don - L, L, kapi_h)
    _kat_seviyeleri(e, g, S, kotlar, -don - L, K, -1.0)
    kesit_parcalari.kot_isareti(e, -don - L + 200 * K * -1.0, taban, dusey.kot_yazisi(taban), K, -1.0)
    u_oda = None
    if oda:
        #  A-A kabin ekseninden karşı ağırlığa bakar:  ön ve arka duvar kesilir,
        #  karşı ağırlık tarafındaki duvar görünür
        u_oda = _oda(e, B, g, Y, K, g["agirlik"]["yeri"], ("Ön", "Arka"), -don - L - 200 * K)
    AK, kt = kesit_parcalari.donanimi_ciz(
        e, B, g, Y, P, 0.0, M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"] + H, K
    )
    kb = KD["kabin"]
    ky = [(kz[1] + kz[3]) / 2.0 for kz in P["kabin_kasnak"]]
    dusey.kabin_kesiti(
        e,
        kt,
        (kb[1], kb[3]),
        g["kabin_ray"]["kapi_arasi"],
        S,
        ky[:1],
        g["aski"].get("kasnak_capi") or 0,
        esik_on=min((kk[1] for kk in P["kabin_esik"]), default=None),
    )
    kesit_parcalari.korkuluk(e, B, Y, kt)
    _yan_kabin_kapisi(e, S, P, kt["doseme"], kapi_h)
    #  Kabin opak:  yan duvarının arkasındaki ağırlık rayları, konsollar, halatlar
    #  kabinin içinden görünmez;  kabin rayı ( ve şase — _kabin ) kabinin üstünden
    #  görünür ( referans projenin ve LiftDesigner'ın yan kesitleri gibi ).
    kesit_parcalari.kabin_arkasi(e, B, kb, kt["taban_alti"], kt["tavan"], onde={"kabin_rayi"})
    #  Ölçüler
    _olculer_sol(e, Y, -don - L - 700 * K, K, kotlar, tavan, g)
    #  Görünen raylar karşı ağırlık tarafındakiler:  konsol zinciri onların
    ag = min((r for r in M["raylar"] if r["tur"] == "agirlik"), key=lambda r: r["ust"])
    r0 = D + dar + 150 * K
    if oda:
        #  Oda zemini kuyu tavanının altında ( tabliye ):  oda kuyunun yanına
        #  taşıyorsa zincir onun dış duvarının ötesinde — odanın içinden geçmez
        r0 = max(r0, u_oda + 150 * K)
    _konsol_zinciri(e, r0, ag, tavan, "AĞIRLIK RAYI", dy["agirlik_konsol_arasi"])
    sa = M["sase"]
    if oda:
        r1 = r0 + geometri.SIRA_ARASI * K
        _oda_olculeri(
            e, M, g["makine_dairesi"], g["makine"]["tahrik_kasnak_capi"], r1, r1 + geometri.SIRA_ARASI * K
        )
    else:
        _zincir(
            e,
            r0 + geometri.SIRA_ARASI * K,
            [sa[4], sa[5], M["kapak"][5], tavan],
            {0: f"ŞASE {sa[5] - sa[4]:g}", 1: f"MAKİNE {M['kapak'][5] - sa[5]:g}"},
        )
    dh, sd = kisaltmalar.kodlu("DH", kapi_h), kisaltmalar.kodlu("SD", D)
    e.append(eleman.olcu("dusey", (0, 0.0), (0, kapi_h), -don - 120 * K, dh, ad="kapi_yuksekligi"))
    e.append(eleman.olcu("yatay", (0, taban), (D, taban), taban - dos - 250 * K, sd, ad="kuyu_derinligi"))
    #  Kırık:  altta kabin ( ve paten ), üstte karşı ağırlık kalmalı
    return _bitir(
        e,
        g,
        Y,
        kt,
        K,
        max(kt["ust_paten"], kt["tavan"] + Y["korkuluk"]),
        min(AK["alt"], AK["alt_paten"]),
        bosluk_h,
        (-don, D + dar),
        azami,
    )


def on_kesit(g, cizim_sabitleri=None, azami=None):
    """B-B:  kabin en üst durakta;  kuyunun arkasından kat kapılarına bakış."""
    Y = yerlesim(g, cizim_sabitleri)
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    k = g["kuyu"]
    G, ds, dg, don = k["genislik"], k["duvar_sol"], k["duvar_sag"], k["duvar_on"]
    dos = k.get("doseme", don)  # kuyu dibi ve tavan döşemesi
    K = OLCEK / 20.0
    B = kesit_parcalari.Bakis("on", G, ("y", geometri.kesit_duzlemleri(g)[1], -1.0))
    P = kesit_parcalari.plan_parcalari(Y["KD"], g)
    kotlar = Y["kotlar"]
    H = kotlar[-1]
    tavan = H + dy["son_kat"]
    taban = Y["taban"]
    kapi_h = g["kapi"]["yukseklik"]
    oda = "MD" in M
    ust = tavan + dos
    e = []
    #  Yan duvarlar ( görünüşte plandaki sağ duvar solda ), kuyu dibi, tavan
    _duvar(e, -dg, taban - dos, dg, ust - (taban - dos))
    _duvar(e, G, taban - dos, ds, ust - (taban - dos))
    _duvar(e, 0, taban - dos, G, dos)
    _duvar(e, 0, tavan, G, dos, "tabliye" if oda else None)
    e.append(eleman.ad(eleman.cizgi("GIZLI", 0, Y["tavan_alti"] + H, G, Y["tavan_alti"] + H), "tavan_kirisi"))
    #  Kat kapıları ön duvarda ( görünüş ):  kasa, boşluk, kanat ayrımı, durak numarası
    kp = g["kapi"]
    bos = (kp["sol_pay"], -1, kp["sol_pay"] + kp["genislik"], 0)
    kasa_x0 = min(kk[0] for kk in P["kasa"])
    kasa_x1 = max(kk[2] for kk in P["kasa"])
    #  Kanatların ayrımları ( kapı tipinin kanat sayısında — 2 · 3 · 4 )
    ayrimlar = sorted({round(kk[2], 6) for kk in P["kanat"]})[:-1]
    #  Durak numarası ortaya en yakın KANADIN ortasında:  kapının ortası iki
    #  kanatlı kapıda kanat ayrımıdır, numara ( maskeli ) ayrım çizgisini
    #  siliyordu ( 5 Eki ).
    xs = [bos[0]] + [a for a in ayrimlar if bos[0] < a < bos[2]] + [bos[2]]
    orta = (bos[0] + bos[2]) / 2.0
    k0, k1 = min(zip(xs, xs[1:]), key=lambda p: (abs((p[0] + p[1]) / 2.0 - orta), -(p[1] - p[0])))
    for i, zk in enumerate(kotlar):
        B.kutu(e, "KAPI", (kasa_x0, -1, kasa_x1, 0), zk, zk + kapi_h + S["kasa_ust"], "kapi_kasasi")
        B.kutu(e, "KAPI", bos, zk, zk + kapi_h, "kat_kapisi")
        for ayrim in ayrimlar:
            u = B.u(ayrim, 0)
            e.append(B.derin(eleman.cizgi("KAPI", u, zk, u, zk + kapi_h), -1, 0))
        e.append(
            B.derin(
                eleman.ad(
                    eleman.yazi(B.u((k0 + k1) / 2.0, 0), zk + kapi_h * 0.6, f"{i + 1}", uslup.HARF * K),
                    "durak_no",
                ),
                -1,
                0,
            )
        )
    _kat_seviyeleri(e, g, S, kotlar, -dg, K, -1.0)
    kesit_parcalari.kot_isareti(e, -dg - 200 * K, taban, dusey.kot_yazisi(taban), K, -1.0)
    u_oda = None
    if oda:
        #  B-B arkadan kat kapılarına bakar:  yan duvarlar kesilir, ön duvar görünür
        u_oda = _oda(e, B, g, Y, K, "Ön", ("Sol", "Sağ"), -dg - 200 * K)
    AK, kt = kesit_parcalari.donanimi_ciz(
        e, B, g, Y, P, H, M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"], K
    )
    kesit_parcalari.kabin_on(e, B, g, Y, P, kt)
    kesit_parcalari.korkuluk(e, B, Y, kt)
    #  Kabin opak:  arkasında kalan kat kapısı ( en üst durak ) kabinin içinden görünmez
    kesit_parcalari.kabin_arkasi(e, B, Y["KD"]["kabin"], kt["taban_alti"], kt["tavan"])
    #  Durak numarası halatın ( kapının önünden geçer ) ya da başka bir parçanın
    #  çizgisine binmesin:  ortaya en yakın, çizgisiz kanat ( 2500 kg arka
    #  ağırlıkta askı halatı kanadın ortasından geçiyordu — 5 Eki )
    kanatlar = sorted(zip(xs, xs[1:]), key=lambda p: (abs((p[0] + p[1]) / 2.0 - orta), -(p[1] - p[0])))
    kenarlar = geometri.parca_kenarlari([el for el in e if el.get("ad") != "durak_no"])
    for el in e:
        if el.get("ad") == "durak_no":
            for a, b in kanatlar:
                kutu = geometri.sinir([dict(el, x=B.u((a + b) / 2.0, 0))])
                if not any(geometri.kenar_kesisir(s_, kutu, 2.0 * K) for s_ in kenarlar):
                    el["x"] = B.u((a + b) / 2.0, 0)
                    break
    #  Ölçüler
    _olculer_sol(e, Y, -dg - 700 * K, K, kotlar, tavan, g)
    uzak = max((r for r in M["raylar"] if r["tur"] == "kabin"), key=lambda r: r["ust"])
    r0 = G + ds + 150 * K
    if oda:
        r0 = max(r0, u_oda + 150 * K)  # oda kuyunun yanına taşıyorsa ötesinde
    _konsol_zinciri(e, r0, uzak, tavan, "KABİN RAYI", dy["kabin_konsol_arasi"])
    _zincir(
        e,
        r0 + 250 * K,
        [M["agirlik"]["tampon_ustu"], AK["alt"], AK["ust"]],
        {0: f"ÇARPMA ARASI {dy['agirlik_carpma_arasi']:g}", 1: f"KARŞI AĞIRLIK {AK['ust'] - AK['alt']:g}"},
    )
    if oda:
        r1 = r0 + 2 * geometri.SIRA_ARASI * K
        _oda_olculeri(
            e, M, g["makine_dairesi"], g["makine"]["tahrik_kasnak_capi"], r1, r1 + geometri.SIRA_ARASI * K
        )
    e.append(
        eleman.olcu(
            "yatay",
            (0, taban),
            (G, taban),
            taban - dos - 250 * K,
            kisaltmalar.kodlu("SW", G),
            ad="kuyu_genisligi",
        )
    )
    #  Kırık:  altta karşı ağırlık, üstte kabin ( etek, fren bloğu, paten ) kalmalı
    return _bitir(
        e,
        g,
        Y,
        kt,
        K,
        max(AK["ust"], AK["ust_paten"], AK["kasnak_merkez"] + (g["agirlik"].get("kasnak_capi") or 0) / 2.0),
        min(kt["etek_alti"], kt["sase_alt"], kt["alt_paten"], kt["fren_alti"]),
        kapi_h + S["kapi_ust_payi"],
        (-dg, G + ds),
        azami,
    )
