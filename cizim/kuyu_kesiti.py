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

from cizim import sorunlu
from cizim import istek_onbellegi
from cizim import eleman
from cizim import kisaltmalar
from cizim import uslup
from cizim import arka_aski
from cizim import dusey
from cizim import katlar
from cizim import geometri
from cizim import girdi
from cizim import kesit_parcalari
from cizim import makine
from cizim import makine_dairesi
from cizim import parca_kotlari
from cizim import standart

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


@istek_onbellegi.sakla
def yerlesim(g, cizim_sabitleri=None):
    return dusey.yerlesim(g, cizim_sabitleri)


def dogrula(g):
    hata = dusey.dogrula(g)
    #  Sorunlu kipte ( cizim/sorunlu.py ) ilk hatada durulmaz:  çare bulucu gizli
    #  kalan sorunları da görür ( uclar/care_uclari.py ).  Kip kapalıyken aynı.
    if hata and not sorunlu.acik():
        return hata
    #  Kat adlarının sorunları kesitindir ( katlar.ad_sorunlari — hesabı durdurmaz )
    return hata + yerlesim(g)["hata"] + katlar.ad_sorunlari(g)


def _duvar(e, u, z, w, h, ad=None):
    e.append(eleman.dikdortgen("TARAMA", u, z, w, h, tip="tarama"))
    el = eleman.dikdortgen("KUYU-DUVAR", u, z, w, h)
    if ad:
        eleman.ad(el, ad)
    e.append(el)


def _delikten_gecer(B, d):
    """Kesit düzlemi plandaki deliği ( kutu ) kesiyor mu."""
    eksen, c, _yon = B.kesit
    lo, hi = (d[0], d[2]) if eksen == "x" else (d[1], d[3])
    return lo < c < hi


def ayirma_kirisi_kotlari(g, M):
    """Kuyu grubunun açık arasındaki ayırma kirişlerinin ÜST kotları:  ortaya
    bakan rayların bütün konsol seviyeleri ( kullanıcı kararı 1 Kas ) — o yandaki
    kabin rayı, karşı ağırlık o yandaysa rayları da ( arkadaki ağırlığın rayları
    arka duvara bağlıdır ).  Açık ara yoksa boş."""
    yan = g["kuyu"].get("acik_yan")
    if not yan:
        return []
    kx = g["kuyu"]["genislik"] / 2.0 + g["kabin"]["kaciklik_y"]
    kotlar = set()
    for r in M["raylar"]:
        x = (r["kutu"][0] + r["kutu"][2]) / 2.0
        ortada = (x > kx if yan == "Sağ" else x < kx) if r["tur"] == "kabin" else g["agirlik"]["yeri"] == yan
        if ortada:
            kotlar.update(round(z, 3) for z in r["konsollar"])
    return sorted(kotlar)


def _ayirma_kirisi_kesiti(e, g, u0, kotlar):
    """B-B'de ayırma kirişlerinin kesiti:  NPU gövdesi yatay, üstte ( ağzı aşağı —
    S. Tavaslıoğlu, ara bölmeler yatay konur ), gövde aranın tamamı ( u0'dan h ),
    üstü konsolun üst kotunda;  kesilen çelik dolu ( DIN 1026-1:  h, b, s, t )."""
    P = makine.npu(g["proje"]["ayirma_kirisi"])
    h, b, s, t = P["h"], P["b"], P["s"], P["t"]
    for zt in kotlar:
        a, c = u0, u0 + h
        el = eleman.dikdortgen("KONSOL", a, zt - b, h, b, ad="ayirma_kirisi")
        el["bicim"] = [
            {
                "noktalar": [
                    (a, zt),
                    (c, zt),
                    (c, zt - b),
                    (c - t, zt - b),
                    (c - t, zt - s),
                    (a + t, zt - s),
                    (a + t, zt - b),
                    (a, zt - b),
                ],
                "kapali": True,
                "dolu": True,
            }
        ]
        e.append(el)


def _acik_ara_yanda(e, B, g, M, taban, alt_durak, tavan):
    """A-A:  kuyu grubunun açık arası bakılan yandaysa ayırma kirişleri görünüşte —
    konsol seviyelerinde ön duvardan arka duvara, flanşın dış yüzü — ve iki kuyu
    dibinin arasındaki perde ( m.5.2.5.5.2.1 );  kabinin ardında kalanı kabin örter
    ( _derin )."""
    k = g["kuyu"]
    if not k.get("acik_yan"):
        return
    D = k["derinlik"]
    x0 = -k["duvar_sol"] if k["acik_yan"] == "Sol" else k["genislik"]
    kutu = (x0, 0.0, x0 + (k["duvar_sol"] if k["acik_yan"] == "Sol" else k["duvar_sag"]), D)
    if not B.gorunur(kutu):
        return
    b = makine.npu(g["proje"]["ayirma_kirisi"])["b"]
    for zt in ayirma_kirisi_kotlari(g, M):
        e.append(B.derin_kutu(eleman.dikdortgen("KONSOL", 0, zt - b, D, b, ad="ayirma_kirisi"), kutu))
    z0, z1 = taban + standart.PERDE_TABANDAN, alt_durak + standart.PERDE_DURAK_USTU
    e.append(B.derin_kutu(eleman.ad(eleman.dikdortgen("PERDE", 0, z0, D, z1 - z0), "grup_perdesi"), kutu))
    #  Tam boy perde ( m.5.2.5.5.2.2 — grup.tam_boy_perde ):  kuyu dibi perdesinin
    #  üstünden tavana, eni kadar
    tam = k.get("tam_boy_perde")
    if tam and tavan > z1:
        e.append(
            B.derin_kutu(
                eleman.ad(
                    eleman.dikdortgen("PERDE", tam[0], z1, tam[1] - tam[0], tavan - z1), "grup_perdesi"
                ),
                kutu,
            )
        )


def _on_duvarlar(e, B, g, M, z, dos_t, oda, alt_durak):
    """B-B:  yan duvarlar ( görünüşte plandaki sağ duvar solda ), kuyu dibi döşemesi ve
    tavan.  z:  ( döşemenin altı , kuyu tabanı , tavan , tavan döşemesinin üstü ).
    Kuyu grubunun açık arasında o yanda duvar yok:  konsol seviyelerinde ayırma
    kirişlerinin kesiti, aranın ortasında kesilen perde ( m.5.2.5.5.2.1:  kuyu
    tabanının en çok 0,30 m üstünden en alt durağın 2,50 m üstüne );  kuyu dibi ve
    tavan aranın üstünden geçer ( tek kuyu )."""
    k = g["kuyu"]
    G, ds, dg, acik = k["genislik"], k["duvar_sol"], k["duvar_sag"], k.get("acik_yan")
    alt, taban, tavan, ust = z
    if acik != "Sağ":
        _duvar(e, -dg, alt, dg, ust - alt)
    if acik != "Sol":
        _duvar(e, G, alt, ds, ust - alt)
    a0, a1 = (-dg if acik == "Sağ" else 0.0), (G + ds if acik == "Sol" else G)
    _duvar(e, a0, alt, a1 - a0, taban - alt)
    _tabliye(e, B, M, a0, tavan, a1 - a0, dos_t, oda)
    if acik:
        _ayirma_kirisi_kesiti(e, g, -dg if acik == "Sağ" else G, ayirma_kirisi_kotlari(g, M))
        um = -dg / 2.0 if acik == "Sağ" else G + ds / 2.0
        z0, z1 = taban + standart.PERDE_TABANDAN, alt_durak + standart.PERDE_DURAK_USTU
        if k.get("tam_boy_perde"):
            z1 = max(z1, tavan)  # m.5.2.5.5.2.2:  kuyu boyunca
        e.append(eleman.ad(eleman.cizgi("PERDE", um, z0, um, z1), "grup_perdesi"))


def _tabliye(e, B, M, u0, z, w, h, oda):
    """Kuyu tavanı döşemesi ( makine dairelide tabliye ).  Kesit düzlemi bir
    halat deliğinden geçiyorsa döşeme orada kesilmez:  delik boşluk olarak
    görünür ( kenarları dolu ).  Öbür delikler düzlemin ardındadır — _oda kesik
    çizer, içlerinden geçen halat da kesik ( betondaki_halati_gizle )."""
    if not oda:
        _duvar(e, u0, z, w, h)
        return
    acik = sorted(
        (max(u0, a), min(u0 + w, b))
        for a, b in (B.aralik(d) for _, d in M["MD"]["delikler"] if _delikten_gecer(B, d))
        if min(u0 + w, b) > max(u0, a)
    )
    a = u0
    for d0, d1 in acik + [(u0 + w, u0 + w)]:
        if d0 - a > 1e-6:
            _duvar(e, a, z, d0 - a, h, "tabliye")
        a = max(a, d1)


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
    1.200 kalınlığında beton çiziliyordu ( kullanıcı 5 Eki ).
    Döner:  ( odanın dış yüzü — öbür yanda , kot işaretlerinin u'su )."""
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
        if not _delikten_gecer(B, d):  # düzlemdeki delik tabliyede boşluk ( _tabliye )
            B.kutu(e, "GIZLI", d, tv, zt, "doseme_deligi")
    u0, u1 = B.aralik(dis)
    e.append(
        eleman.ad(eleman.yazi((u0 + u1) / 2.0, ztv - 250 * K, "MAKİNE DAİRESİ", uslup.NORMAL * K), "oda_adi")
    )
    #  Kot işaretleri odanın dışında:  oda kuyudan genişse duvarının ötesinde
    #  ( eskiden kuyunun yanında, odanın duvarının üstüne düşüyordu )
    u_kot = min(u_kot, u0 - 200 * K)
    ofset = dusey.kot_ofseti(g)
    kesit_parcalari.kot_isareti(e, u_kot, zd, dusey.kot_yazisi(zd, ofset), K, -1.0)
    if zt - zd >= 300.0:
        kesit_parcalari.kot_isareti(e, u_kot, zt, dusey.kot_yazisi(zt, ofset), K, -1.0)
    return u1, u_kot


def _sol_zincir(u0, isaretler, K):
    """Sol zincirin ilk sırası:  duvardan 700K ( u0 ) ya da sol yandaki kot
    işaretlerinin ( isaretler:  uçlarının u'su — duraklar ve kuyu dibi, makine
    dairesi ) en uzun olası yazısının ( dusey.EN_UZUN_KOT ) maskesinin kâğıtta
    MASKE_ESIGI ötesi, hangisi dışarıdaysa.  Yer kota bağlı değil:  kotlar
    kayınca zincir yerinde kalır ( KOT_PLANI B4 ).  27 Eki:  oda kuyudan
    taşınca makine dairesinin kotları odanın dışına çıkar ( _oda );  mutlak
    kotun yazısı ( "+874,75" ) zincirin çizgisini siliyor, çok taşan odada
    üçgen zincirlerin arasına düşüyordu ( ölçüyle girişte de )."""
    uclar = []
    for u in isaretler:
        gecici = []
        kesit_parcalari.kot_isareti(gecici, u, 0.0, dusey.EN_UZUN_KOT, K, -1.0)
        uclar.append(geometri.maske_kutusu(gecici[-1])[0])
    return min(u0, min(uclar) - geometri.MASKE_ESIGI * 20.0 * K)


def _adli(adlar, deger, boy):
    """Kesitte ölçünün yazısı:  adı kendi aralığına sığıyorsa adıyla, sığmıyorsa
    yalnız değer ( geometri.adli_olcu_metni — 1/50 )."""
    return geometri.adli_olcu_metni(adlar, deger, boy, OLCEK / 20.0)


def _oda_olculeri(e, g, M, kot_makine, kot_oda):
    """Makine dairesinde:  şase · kasnak · kasnak üstü ( m.5.2.6.3.2.3 );  oda
    zemininden tabliye · tabliyenin üstünde temiz yükseklik ( m.5.2.6.3.2.1 ) ·
    çatı;  dışta odanın temiz yüksekliği.  Uygunluk ( ≥ ) ölçüde değil, veri
    tablosunun "Makine dairesi" ve "Tahrik kasnağı üstü" satırlarında
    ( donanim.oda_acikliklari — aynı sayılar;  6 Kas çizim denetimi, karar D2:
    "KASNAK ÜSTÜ 931 ≥ 300" 1/50'de 41 mm, odanın çatısına taşıyordu );  ad
    aralığına sığmazsa yalnız değer."""
    zt, zd, ztv, c = M["tabliye_ustu"], M["oda_doseme"], M["oda_tavan"], M["cati"]
    sa = M["sase"]
    ku = M["kasnak"][4] + g["makine"]["tahrik_kasnak_capi"] / 2.0
    _zincir(
        e,
        kot_makine,
        [zt, sa[5], ku, ztv],
        {0: _adli(("ŞASE",), sa[5] - zt, sa[5] - zt), 2: _adli(("KASNAK ÜSTÜ",), ztv - ku, ztv - ku)},
    )
    _zincir(
        e,
        kot_oda,
        [zd, zt, ztv, ztv + c],
        {0: _adli(("TABLİYE",), zt - zd, zt - zd), 1: f"{ztv - zt:g}", 2: f"{c:g}"},
    )
    if zt - zd > 1e-6:
        e.append(
            eleman.olcu(
                "dusey",
                (0, zd),
                (0, ztv),
                kot_oda + (kot_oda - kot_makine),
                _adli(("MAKİNE DAİRESİ",), g["makine_dairesi"]["yukseklik"], ztv - zd),
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


def _kat_seviyeleri(e, g, S, kotlar, u_duvar, K, yon, taban):
    """Kot işaretleri ve durak adları ( duvarın dışında ), sonra kuyu dibinin
    kotu aynı sütunda.  Kotla girişte yazılar mimarinin kotudur ( kot_ofseti ).
    Döner:  işaretlerin u'su."""
    ofset = dusey.kot_ofseti(g)
    #  Durağın adı ( katlar.adlar_ve_giris — giriş katı 0, altı −1, üstü 1 … ya da elle
    #  yazılan;  KAT_ADLARI_PLANI 2 Kas — eskiden alttan "1. DURAK" )
    adlar, _giris = katlar.adlar_ve_giris(g)
    for i, z in enumerate(kotlar):
        kesit_parcalari.kot_isareti(e, u_duvar + yon * 200 * K, z, dusey.kot_yazisi(z, ofset), K, yon)
        e.append(
            eleman.ad(
                eleman.yazi(
                    u_duvar + yon * 120 * K,
                    z + 1100,
                    adlar[i],
                    uslup.NORMAL * K,
                    hiza="sol" if yon > 0 else "sag",
                ),
                "durak_adi",
            )
        )
    kesit_parcalari.kot_isareti(e, u_duvar + yon * 200 * K, taban, dusey.kot_yazisi(taban, ofset), K, yon)
    return u_duvar + yon * 200 * K


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


def _konsol_zinciri(e, kot, r, tavan, ad):
    """Rayın konsolları:  ilk konsol rayın altından, konsol araları, rayın üstü,
    tavan — aralıklarda yalnız sayı.  Zincirin adı ( "KABİN RAYI KONSOLLARI" ) bir
    kez, kırıktan sonra zincirin yanında boş yerde ( _zincir_adi ).  6 Kas çizim
    denetimi, karar D4:  ad aralıklara yazılıyordu — "AĞIRLIK RAYI KONSOL ARASI 1500"
    1/50'de 59 mm, aralığı 30 mm;  "İLK KONSOL 500" 28 mm, aralığı 10 mm:  yazılar
    aralıklarından taşıp çizimin altına sarkıyordu.  Rayın konsol arası veri
    tablosunda da.  Dönen:  ( kot , alt , üst , ad ) — _bitir'in zincir_adlari'na."""
    noktalar = [r["alt"]] + r["konsollar"] + [r["ust"], tavan]
    _zincir(e, kot, noktalar)
    return kot, noktalar[0], noktalar[-1], f"{ad} KONSOLLARI"


def _zincir_adi(e, kot, z0, z1, metin, K, bantlar=()):
    """Düşey zincirin adı:  zincirin dış yanında, ölçü yazılarının iki sıra
    ötesinde ( yoksa üç ), düşey;  zincirin boyunda ( z0 – z1 ) kırığın bandına
    ( bantlar — boş:  kesilen katların yeri ), kırık yoksa zincirin ortasına en
    yakın, hiçbir yazının maskesine, ölçü çizgisine ve parça kenarına binmeyen
    yer.  Orada da yoksa iç yanda ( çizgiye bitişik ).  Hiçbirinde yer yoksa
    yazılmaz.  Bir sıra öte olmaz:  maskesi sayılarınkine değer ( KAT_ARALIGI
    yazıdan 10 büyük, maske yazıdan büyük ), arada 0,5 mm kalır, sayılarla tek
    yazı gibi okunur."""
    h = eleman.OLCU_YAZI * K
    w = eleman.yazi_eni(metin, h)
    if z1 - z0 < w:
        return False
    dis = 1.0 if kot >= 0 else -1.0
    sutunlar = [kot + dis * (50.0 + eleman.KAT_ARALIGI * kat) * K for kat in (2, 3)] + [kot - dis * 50.0 * K]
    #  Yalnız adın sütunlarının şeridindekiler ( süre:  kesit kırık denenirken birkaç kez kurulur )
    x0, x1 = min(sutunlar) - h, max(sutunlar) + h

    def seritte(k):
        return k is not None and k[0] < x1 and x0 < k[2]

    maskeler = [
        k
        for x in e
        if (x["tip"] == "yazi" and x.get("katman") != "CERCEVE") or (x["tip"] == "olcu" and x.get("yazi"))
        for k in (geometri.maske_kutusu(x),)
        if seritte(k)
    ]
    parcalar_ = [x for x in e if x["tip"] not in ("yazi", "olcu") and seritte(geometri.sinir([x]))]
    cizgiler = [
        s
        for s in geometri.parca_kenarlari(parcalar_)
        + [
            s
            for o in e
            if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6
            for s in geometri.olcu_cizgileri(o, K)
        ]
        if min(s[0], s[2]) < x1 and x0 < max(s[0], s[2])
    ]
    orta = (z0 + z1) / 2.0
    tercih = min(
        ((a + b) / 2.0 for a, b in bantlar if z0 < (a + b) / 2.0 < z1),
        key=lambda z: abs(z - orta),
        default=orta,
    )
    adim = 25.0 * K
    n = int((z1 - z0) / adim) + 1
    yerler = sorted(
        {min(max(tercih + i * adim, z0 + w / 2.0), z1 - w / 2.0) for i in range(-n, n + 1)},
        key=lambda y: (abs(y - tercih), y),
    )
    for c in sutunlar:
        for y in yerler:
            m = uslup.maske_kutusu(c, y, w, h, 90.0)
            if any(m[0] < b[2] and b[0] < m[2] and m[1] < b[3] and b[1] < m[3] for b in maskeler):
                continue
            if any(geometri.kenar_kesisir(s, m) for s in cizgiler):
                continue
            e.append(eleman.ad(eleman.yazi(c, y, metin, h, katman="OLCU", aci=90), "zincir_adi"))
            return True
    return False


KIRIK_BOSLUK = 1200.0  # kırık gösterimde atlanan katların yerine kalan yükseklik
KIRIK_PAY = 300.0  # kırık çizgisi ile en yakın parça arası
#  Kırık çizgisi ile üstte kalan durağın eşik altı sacının ucu arası:  sac ince
#  bir parça, döşemenin payı gerekmez ( 300 verilince 63444-2'de bir ara kat daha
#  kırığa düşüyordu ) — ÇİZİM KABULÜ
KIRIK_SAC_PAYI = 100.0


def _sayisal(m):
    return m.replace(".", "").isdigit()


def _birlesik_metin(parcalar, uzunluk):
    """Kırığın üstünden geçen ölçünün yazısı:  eşit aralıklar "n × a",
    değilse gerçek toplam."""
    metinler = [p[2]["metin"] for p in parcalar]
    if all(_sayisal(m) for m in metinler) and len(set(metinler)) == 1 and len(metinler) > 1:
        return f"{len(metinler)} × {metinler[0]}"
    return f"{uzunluk:g}"


def _bantta(noktalar, a, b):
    """Açık çizginin a ≤ z ≤ b bandında kalan parçaları ( nokta listeleri )."""
    out, son = [], None
    for (x0, z0), (x1, z1) in zip(noktalar, noktalar[1:]):
        dz = z1 - z0
        if abs(dz) < 1e-12:
            t0, t1 = (0.0, 1.0) if a - 1e-9 <= z0 <= b + 1e-9 else (1.0, 0.0)
        else:
            ta, tb = (a - z0) / dz, (b - z0) / dz
            t0, t1 = max(0.0, min(ta, tb)), min(1.0, max(ta, tb))
        if t1 - t0 < 1e-12:
            son = None
            continue
        p = (x0 + (x1 - x0) * t0, z0 + dz * t0)
        q = (x0 + (x1 - x0) * t1, z0 + dz * t1)
        if son is not None and abs(son[-1][0] - p[0]) < 1e-9 and abs(son[-1][1] - p[1]) < 1e-9:
            son.append(q)
        else:
            son = [p, q]
            out.append(son)
    return out


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
        elif t in ("dikdortgen", "tarama", "tarama_tugla"):
            kalan = bol(el["y"], el["y"] + el["d"])
            for a, b in kalan:
                n = dict(el)
                n["y"], n["d"] = m(a), b - a
                if "bicim" in el:
                    #  GERÇEK BİÇİM DE KAYAR ( regülatör, kasnak … ):  eskiden yalnız
                    #  zarf kayıyor, biçim kırılmamış kotunda — paftanın 300 mm
                    #  dışında — çiziliyordu ( 20 Eki ).  Kırığa giren parçanın
                    #  kapalı biçimi kesilemez:  zarfı çizilir;  açık çizgi biçimi
                    #  ( eşik altı sacı ) çizgi gibi kesilir ( 3 Kas ).
                    if len(kalan) == 1 and b - a >= el["d"] - 1e-6:
                        dy = n["y"] - el["y"]
                        n["bicim"] = [
                            dict(p, noktalar=[(x, y + dy) for x, y in p["noktalar"]]) for p in el["bicim"]
                        ]
                    elif not any(p.get("kapali", True) for p in el["bicim"]):
                        kesik = [(p, q) for p in el["bicim"] for q in _bantta(p["noktalar"], a, b)]
                        if not kesik:
                            continue
                        n["bicim"] = [dict(p, noktalar=[(x, m(z)) for x, z in q]) for p, q in kesik]
                        xs = [x for _, q in kesik for x, _z in q]
                        n["x"], n["g"] = min(xs), max(xs) - min(xs)
                    else:
                        del n["bicim"]
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


def _hareketli_sinirlari(g, Y):
    """Kırığın değmeyeceği hareketli parçaların sınırları — İKİ KESİTTE ORTAK:
    altta kalanların üstü ( A-A'da en alt duraktaki kabin, B-B'de tamponundaki
    karşı ağırlık ) ve üstte kalanların altı ( A-A'da yukarıdaki karşı ağırlık,
    B-B'de en üst duraktaki kabin ).  Kesitler kırığı ayrı ayrı seçiyordu:  en
    sıkı kırıkta kendi parçasına göre, aynı kot iki kesitte ayrı yükseklikte
    kalıyordu ( 3 Kas — 63444-2, eşik altı sacının payıyla ortaya çıktı )."""
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    H = Y["kotlar"][-1]
    ag = M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"]
    alt_k, ust_k = (
        parca_kotlari.kabin_kotlari(dy, S, z, g.get("aski"), arka_aski.arkada_iki_bir(g)) for z in (0.0, H)
    )
    alt_a, ust_a = (parca_kotlari.agirlik_kotlari(M, z) for z in (ag, ag + H))
    r = (g["agirlik"].get("kasnak_capi") or 0) / 2.0
    return (
        max(
            alt_k["ust_paten"],
            alt_k["tavan"] + Y["korkuluk"],
            alt_a["ust"],
            alt_a["ust_paten"],
            alt_a["kasnak_merkez"] + r,
        ),
        min(
            ust_a["alt"],
            ust_a["alt_paten"],
            ust_k["etek_alti"],
            ust_k["sase_alt"],
            ust_k["alt_paten"],
            ust_k["fren_alti"],
        ),
    )


def _bitir(e, g, Y, kt, K, alt_ust, ust_alt, bosluk_h, duvarlar, azami, zincir_adlari=()):
    """Yazıları yerleştirir, plan seviyelerini ekler.  Çizim `azami`
    yüksekliğe ( çerçevesiyle, çizim birimi ) sığmıyorsa ara katları kırar:
    alttan ve üstten SIĞAN EN ÇOK durak kalır ( en az birer ).  Giriş katı
    ( katlar.adlar_ve_giris ) kırığa düşerse o da kalır:  iki kırık, arada giriş
    katı ( KAT_ADLARI_PLANI — 2 Kas:  63444-2'de paftada "0" yoktu ).  Kırık
    hareketli parçalara ( kabin, karşı ağırlık ) değmez.  Halatın betondaki
    parçası önce kesik olur ( kesit_parcalari.betondaki_halati_gizle ).
    zincir_adlari:  [ ( kot , alt , üst , ad ) ] — kırıktan sonra zincirin yanına
    ( _zincir_adi;  kırık varsa onun bandına en yakın )."""
    kesit_parcalari.betondaki_halati_gizle(e)
    sev = plan_seviyeleri(g, Y, kt)

    def son(e_, m=None, ic=None, bantlar=()):
        e_ = [dict(x) for x in e_]
        geometri.yazilari_yerlestir(e_, eleman.OLCU_YAZI * K)
        s_ = [(h, m(z) if m else z, ad) for h, z, ad in sev if not (ic and ic(z))]
        _seviye_isaretleri(e_, s_, K)
        for kot, z0, z1, ad in zincir_adlari:
            _zincir_adi(e_, kot, m(z0) if m else z0, m(z1) if m else z1, ad, K, bantlar)
        return e_

    tam = son(e)
    if azami is None or _yukseklik(tam, K) <= azami:
        return tam
    kotlar = Y["kotlar"]
    #  Kırık eşik altı saclarını kesmez:  üstte kalan durağın döşemesi ve sacı
    #  kırığın üstünde kalır;  kırığa düşen ilk durağın sacı bütün düşer
    sac = -girdi.esik_alti_saci(g, Y["S"])["alt"]
    ust_pay = max(Y["S"]["kat_doseme_kalinlik"] + KIRIK_PAY, sac + KIRIK_SAC_PAYI)
    _adlar, giris = katlar.adlar_ve_giris(g)

    def alt_cizgi(z0, j):
        """Kırığın alt çizgisi:  altta kalanların üstünün ( z0 ) KIRIK_PAY üstü;
        j. durağın ( kırığa düşen ilk durak ) eşik altı sacının ucu o paya
        giriyorsa sacın ucu — sacın bir parçası kırığın altında kalmaz."""
        uc = kotlar[j] - sac
        return min(z0 + KIRIK_PAY, uc) if z0 < uc else z0 + KIRIK_PAY

    for i in range(len(kotlar) // 2 - 1, -1, -1):
        za = alt_cizgi(max(alt_ust, kotlar[i] + bosluk_h), i + 1)
        zu = min(ust_alt - KIRIK_PAY, kotlar[-1 - i] - ust_pay)
        if zu - za <= KIRIK_BOSLUK:
            continue
        araliklar = [(za, zu)]
        if i < giris < len(kotlar) - 1 - i:
            araliklar = [
                (za, kotlar[giris] - ust_pay),
                (alt_cizgi(kotlar[giris] + bosluk_h, giris + 1), zu),
            ]
        k = _kirik(e, [(a, b) for a, b in araliklar if b - a > KIRIK_BOSLUK], duvarlar, K, son)
        if k is not None and (_yukseklik(k, K) <= azami or i == 0):
            return k
    return tam


def _kirik(e, araliklar, duvarlar, K, son):
    """Aralıkları ( alttan üste, ayrık ) çizimden çıkarır:  üstteki önce ( alttakinin
    kotları kaymasın ), kot eşlemesi bileşik.  Aralık yoksa None."""
    if not araliklar:
        return None
    eslemeler, icler = [], []
    for za, zu in reversed(araliklar):
        e, m, ic = _kir(e, za, zu, KIRIK_BOSLUK)
        _kirik_cizgileri(e, za, KIRIK_BOSLUK, duvarlar[0], duvarlar[1], K)
        eslemeler.append(m)
        icler.append(ic)

    def m(z):
        for f in eslemeler:
            z = f(z)
        return z

    #  Kesilen katların yeri ( çizimde ):  kırığın alt çizgisi ve KIRIK_BOSLUK
    bantlar = [(m(za), m(za) + KIRIK_BOSLUK) for za, _zu in araliklar]
    return son(e, m, lambda z: any(f(z) for f in icler), bantlar)


def yan_bakis(g):
    """A-A:  kabin ekseninden karşı ağırlık tarafına bakış."""
    return kesit_parcalari.Bakis(
        "yan",
        g["kuyu"]["genislik"],
        ("x", geometri.kesit_duzlemleri(g)[0], -1.0 if g["agirlik"]["yeri"] == "Sol" else 1.0),
    )


def _yan_katlar(e, g, S, P, kotlar, u0, L, kapi_h):
    """A-A'da katlar:  döşeme ( u0'dan L boyunca ), kat kapısı ( kasa, üst kutu,
    eşik, kanatlar, eşik altı sacı — kapı yan kesitindeki gibi, aynı kaynaktan:
    girdi.kapi_bolgesi · girdi.esik_alti_saci ).  Kısa katta sac alttaki kapının
    üst kutusuna bağlanır ( m.5.2.5.3.2 d 1 )."""
    KB = girdi.kapi_bolgesi(g, S)
    for i, zk in enumerate(kotlar):
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
        ku = (KB["kasa"][1], zk + kapi_h, KB["hat"] - KB["kasa"][1], S["kasa_ust"])
        e.append(eleman.ad(eleman.dikdortgen("KAPI", *ku), "kapi_ust_kutusu"))
        s = girdi.esik_alti_saci(g, S, zk - kotlar[i - 1] if i else None)
        if s["dik_alt"] < s["ust"] - 1e-6:
            e.append(kesit_parcalari.esik_alti_saci_kesiti(s, zk))


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
    dos = k.get("doseme", don)  # kuyu dibi döşemesi
    dos_t = makine_dairesi.tabliye(g)["doseme"]  # tavan döşemesi ( makine dairelide tabliye )
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
    ust = tavan + dos_t  # tavan döşemesinin üstü ( makine dairesinde tabliye )
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
    _tabliye(e, B, M, 0, tavan, D, dos_t, oda)
    _acik_ara_yanda(e, B, g, M, taban, kotlar[0], tavan)
    #  Kuyu tavanının en alt kısmı ( kiriş payı — hesap programının "kuyu tavanı
    #  payı" ):  bir KABULDÜR, beton değil;  kesik sınır çizgisi ( eskiden taralı
    #  150 mm bir katman gibi çiziliyor, tavan iki kat kalın görünüyordu ).
    e.append(eleman.ad(eleman.cizgi("GIZLI", 0, Y["tavan_alti"] + H, D, Y["tavan_alti"] + H), "tavan_kirisi"))
    L = 240 * K
    _yan_katlar(e, g, S, P, kotlar, -don - L, L, kapi_h)
    isaretler = [_kat_seviyeleri(e, g, S, kotlar, -don - L, K, -1.0, taban)]
    u_oda = None
    if oda:
        #  A-A kabin ekseninden karşı ağırlığa bakar:  ön ve arka duvar kesilir,
        #  karşı ağırlık tarafındaki duvar görünür
        u_oda, u_kot = _oda(e, B, g, Y, K, g["agirlik"]["yeri"], ("Ön", "Arka"), isaretler[0])
        isaretler.append(u_kot)
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
    _olculer_sol(e, Y, _sol_zincir(-don - L - 700 * K, isaretler, K), K, kotlar, tavan, g)
    #  Görünen raylar karşı ağırlık tarafındakiler:  konsol zinciri onların
    ag = min((r for r in M["raylar"] if r["tur"] == "agirlik"), key=lambda r: r["ust"])
    r0 = D + dar + 150 * K
    if oda:
        #  Oda zemini kuyu tavanının altında ( tabliye ):  oda kuyunun yanına
        #  taşıyorsa zincir onun dış duvarının ötesinde — odanın içinden geçmez
        r0 = max(r0, u_oda + 150 * K)
    zincir = _konsol_zinciri(e, r0, ag, tavan, "AĞIRLIK RAYI")
    sa = M["sase"]
    if oda:
        r1 = r0 + geometri.SIRA_ARASI * K
        _oda_olculeri(e, g, M, r1, r1 + geometri.SIRA_ARASI * K)
    else:
        _zincir(
            e,
            r0 + geometri.SIRA_ARASI * K,
            [sa[4], sa[5], M["kapak"][5], tavan],
            {
                0: _adli(("ŞASE",), sa[5] - sa[4], sa[5] - sa[4]),
                1: _adli(("MAKİNE",), M["kapak"][5] - sa[5], M["kapak"][5] - sa[5]),
            },
        )
    dh, sd = kisaltmalar.kodlu("DH", kapi_h), kisaltmalar.kodlu("SD", D)
    e.append(eleman.olcu("dusey", (0, 0.0), (0, kapi_h), -don - 120 * K, dh, ad="kapi_yuksekligi"))
    e.append(eleman.olcu("yatay", (0, taban), (D, taban), taban - dos - 250 * K, sd, ad="kuyu_derinligi"))
    #  Kırık:  hareketli parçalara değmez ( iki kesitte ortak — _hareketli_sinirlari )
    return _bitir(
        e,
        g,
        Y,
        kt,
        K,
        *_hareketli_sinirlari(g, Y),
        bosluk_h,
        (-don, D + dar),
        azami,
        [zincir],
    )


def _on_katlar(e, B, g, S, P, kotlar, kapi_h, K):
    """B-B'de kat kapıları ön duvarda ( görünüş ):  kasa, boşluk, eşik ve altında
    eşik altı sacı ( m.5.2.5.3.2 — kısa katta alttaki kapının kasasına bağlanır,
    d 1 ), kanat ayrımı, katın adı ( "durak_no" ).  Dönen:  kanatların sınırları
    ve kapının ortası ( adın yeri — _kapidaki_adlar ).

    Kapıdaki ad soldaki kot işaretinin yanındaki adın aynısıdır ( katlar.
    adlar_ve_giris — giriş katı 0, altı −1, üstü 1 … ya da elle yazılan ).  6 Kas'a
    dek kapıya durak sırası ( 1 … n ) yazılıyordu:  giriş katının kapısında "1",
    solda "0" ( KAT_ADLARI_PLANI'nın kaçan yeri — çizim denetimi M1 )."""
    kp = g["kapi"]
    bos = (kp["sol_pay"], -1, kp["sol_pay"] + kp["genislik"], 0)
    kasa_x0 = min(kk[0] for kk in P["kasa"])
    kasa_x1 = max(kk[2] for kk in P["kasa"])
    #  Kanatların ayrımları ( kapı tipinin kanat sayısında — 2 · 3 · 4 )
    ayrimlar = sorted({round(kk[2], 6) for kk in P["kanat"]})[:-1]
    #  Katın adı ortaya en yakın KANADIN ortasında:  kapının ortası iki kanatlı
    #  kapıda kanat ayrımıdır, ad ( maskeli ) ayrım çizgisini siliyordu ( 5 Eki ).
    xs = [bos[0]] + [a for a in ayrimlar if bos[0] < a < bos[2]] + [bos[2]]
    orta = (bos[0] + bos[2]) / 2.0
    k0, k1 = min(zip(xs, xs[1:]), key=lambda p: (abs((p[0] + p[1]) / 2.0 - orta), -(p[1] - p[0])))
    #  Eşik kanat ceplerinin altından da sürer ( planda cep ayrı parça )
    esik = P["esik"] + P["cep"]
    esik = [tuple(f(k[i] for k in esik) for i, f in enumerate((min, min, max, max)))] if esik else []
    adlar, _giris = katlar.adlar_ve_giris(g)
    for i, zk in enumerate(kotlar):
        B.kutu(e, "KAPI", (kasa_x0, -1, kasa_x1, 0), zk, zk + kapi_h + S["kasa_ust"], "kapi_kasasi")
        B.kutu(e, "KAPI", bos, zk, zk + kapi_h, "kat_kapisi")
        #  Eşiğin kuyuya bakan yüzü ve altında eşik altı sacı ( m.5.2.5.3.2 —
        #  kısa katta alttaki kapının kasasına bağlanır, d 1 )
        for kk in esik:
            B.kutu(e, "KAPI", kk, zk - S["esik_kalinlik"], zk, "kat_esigi")
        s = girdi.esik_alti_saci(g, S, zk - kotlar[i - 1] if i else None)
        kesit_parcalari.esik_alti_saci_gorunusu(e, B, s, zk)
        for ayrim in ayrimlar:
            u = B.u(ayrim, 0)
            e.append(B.derin(eleman.cizgi("KAPI", u, zk, u, zk + kapi_h), -1, 0))
        e.append(
            B.derin(
                eleman.ad(
                    eleman.yazi(B.u((k0 + k1) / 2.0, 0), zk + kapi_h * 0.6, adlar[i], uslup.HARF * K),
                    "durak_no",
                ),
                -1,
                0,
            )
        )
    return xs, orta


def _kapidaki_adlar(e, B, xs, orta, kapi_h, kasa_ust, K):
    """B-B'de kapıdaki kat adı ( "durak_no" — _on_katlar ) halatın ( kapının
    önünden geçer ) ya da başka bir parçanın çizgisine binmesin:  ortaya en yakın,
    çizgisiz kanat ( 2500 kg arka ağırlıkta askı halatı kanadın ortasından
    geçiyordu — 5 Eki ).  Hiçbir kanada sığmayan ad ( elle yazılmış uzun ad —
    katlar.AD_AZAMI ) kapının ortasında kasanın üstüne;  orada da yer yoksa
    yazılmaz:  ad solda kot işaretinin yanında zaten var ( 6 Kas çizim denetimi,
    karar D1 )."""
    kanatlar = sorted(zip(xs, xs[1:]), key=lambda p: (abs((p[0] + p[1]) / 2.0 - orta), -(p[1] - p[0])))
    kenarlar = geometri.parca_kenarlari([el for el in e if el.get("ad") != "durak_no"])

    def serbest(el, x, y):
        #  Çizgi ne harfe ne yazının MASKESİNE değer:  maske altındaki kenarı siler
        #  ( araclar/karne maske_kenar_siliyor )
        kutu = geometri.sinir([dict(el, x=x, y=y)])
        maske = geometri.maske_kutusu(dict(el, x=x, y=y))
        return not any(
            geometri.kenar_kesisir(s_, kutu, 2.0 * K) or geometri.kutudaki_boy(s_, maske) > 0.0
            for s_ in kenarlar
        )

    sigmayan = []
    for el in e:
        if el.get("ad") != "durak_no":
            continue
        #  Kasanın üstünde:  maskenin altı ( taban + alt uzantı + pay ) kasanın
        #  çizgisinden 2K yukarıda
        m = geometri.maske_kutusu(el)
        ust = el["y"] - kapi_h * 0.6 + kapi_h + kasa_ust + (el["y"] - m[1]) + 2.0 * K
        yerler = [(B.u((a + b) / 2.0, 0), el["y"]) for a, b in kanatlar] + [(B.u(orta, 0), ust)]
        yer = next(((x, y) for x, y in yerler if serbest(el, x, y)), None)
        if yer is None:
            sigmayan.append(el)
        else:
            el["x"], el["y"] = yer
    if sigmayan:
        e[:] = [el for el in e if not any(el is x for x in sigmayan)]


def on_kesit(g, cizim_sabitleri=None, azami=None):
    """B-B:  kabin en üst durakta;  kuyunun arkasından kat kapılarına bakış."""
    Y = yerlesim(g, cizim_sabitleri)
    S, M, dy = Y["S"], Y["M"], g["dusey"]
    k = g["kuyu"]
    G, ds, dg, don = k["genislik"], k["duvar_sol"], k["duvar_sag"], k["duvar_on"]
    dos = k.get("doseme", don)  # kuyu dibi döşemesi
    dos_t = makine_dairesi.tabliye(g)["doseme"]  # tavan döşemesi ( makine dairelide tabliye )
    K = OLCEK / 20.0
    B = kesit_parcalari.Bakis("on", G, ("y", geometri.kesit_duzlemleri(g)[1], -1.0))
    P = kesit_parcalari.plan_parcalari(Y["KD"], g)
    kotlar = Y["kotlar"]
    H = kotlar[-1]
    tavan = H + dy["son_kat"]
    taban = Y["taban"]
    kapi_h = g["kapi"]["yukseklik"]
    oda = "MD" in M
    ust = tavan + dos_t
    e = []
    #  Yan duvarlar ( görünüşte plandaki sağ duvar solda ), kuyu dibi, tavan
    _on_duvarlar(e, B, g, M, (taban - dos, taban, tavan, ust), dos_t, oda, kotlar[0])
    e.append(eleman.ad(eleman.cizgi("GIZLI", 0, Y["tavan_alti"] + H, G, Y["tavan_alti"] + H), "tavan_kirisi"))
    #  Kat kapıları ön duvarda ( görünüş )
    xs, orta = _on_katlar(e, B, g, S, P, kotlar, kapi_h, K)
    isaretler = [_kat_seviyeleri(e, g, S, kotlar, -dg, K, -1.0, taban)]
    u_oda = None
    if oda:
        #  B-B arkadan kat kapılarına bakar:  yan duvarlar kesilir, ön duvar görünür
        u_oda, u_kot = _oda(e, B, g, Y, K, "Ön", ("Sol", "Sağ"), isaretler[0])
        isaretler.append(u_kot)
    AK, kt = kesit_parcalari.donanimi_ciz(
        e, B, g, Y, P, H, M["agirlik"]["tampon_ustu"] + dy["agirlik_carpma_arasi"], K
    )
    ortuler = kesit_parcalari.kabin_on(e, B, g, Y, P, kt)
    kesit_parcalari.korkuluk(e, B, Y, kt)
    #  Kabin opak:  arkasında kalan kat kapısı ( en üst durak ) kabinin içinden,
    #  eşik altı sacı kabinin altına sarkan önlüğün içinden görünmez
    kesit_parcalari.kabin_arkasi(e, B, Y["KD"]["kabin"], kt["taban_alti"], kt["tavan"], ortuler=ortuler)
    _kapidaki_adlar(e, B, xs, orta, kapi_h, S["kasa_ust"], K)
    #  Ölçüler
    _olculer_sol(e, Y, _sol_zincir(-dg - 700 * K, isaretler, K), K, kotlar, tavan, g)
    uzak = max((r for r in M["raylar"] if r["tur"] == "kabin"), key=lambda r: r["ust"])
    r0 = G + ds + 150 * K
    if oda:
        r0 = max(r0, u_oda + 150 * K)  # oda kuyunun yanına taşıyorsa ötesinde
    zincir = _konsol_zinciri(e, r0, uzak, tavan, "KABİN RAYI")
    _zincir(
        e,
        r0 + 250 * K,
        [M["agirlik"]["tampon_ustu"], AK["alt"], AK["ust"]],
        {
            0: _adli(("ÇARPMA ARASI",), dy["agirlik_carpma_arasi"], AK["alt"] - M["agirlik"]["tampon_ustu"]),
            1: _adli(("KARŞI AĞIRLIK",), AK["ust"] - AK["alt"], AK["ust"] - AK["alt"]),
        },
    )
    if oda:
        r1 = r0 + 2 * geometri.SIRA_ARASI * K
        _oda_olculeri(e, g, M, r1, r1 + geometri.SIRA_ARASI * K)
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
    #  Kırık:  hareketli parçalara değmez ( iki kesitte ortak — _hareketli_sinirlari )
    return _bitir(
        e,
        g,
        Y,
        kt,
        K,
        *_hareketli_sinirlari(g, Y),
        kapi_h + S["kapi_ust_payi"],
        (-dg, G + ds),
        azami,
        [zincir],
    )
