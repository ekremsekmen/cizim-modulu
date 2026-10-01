# -*- coding: utf-8 -*-
"""
KUYU PLANI GEOMETRİSİ

Girdiden ( cizim/girdi.py ) + ofis çizim sabitlerinden ( cizim/sabitler.py )
çizim elemanları üretir.  Elemanlar saf veridir;  SVG ve DXF yazıcıları aynı
listeyi okur — iki ayrı çizici yazılmaz.

EKSEN DÜZENİ:  x kuyu genişliği boyunca, y derinlik;  ( 0 , 0 ) kuyu iç
boşluğunun sol-ön ( kapı ) köşesidir.

DBG / DBGW:  rayların BİRBİRİNE BAKAN YÜZLERİ arasındaki açıklıktır, eksenden
eksene değil.  ( referans projenin paftasında da böyle ölçülüyor:  sağ ray 1955'te
başlıyor, sol rayın yüzü 405'te bitiyor → 1550 = DBG. )  Ray, bu yüzden
DUVARA DOĞRU kendi yüksekliği ( h ) kadar uzanır.
"""
import contextlib
import threading

from cizim import girdi as CG
from cizim import sabitler as CS

_KIP = threading.local()


@contextlib.contextmanager
def yalniz_olculer():
    """Blok içinde çizimler yalnız ÖLÇÜLERİ için kurulur:  ölçülerden sonra
    konan, onlara bağlı olmayan pahalı yerleştirmeler ( kuyu dibindeki yük
    kutuları ve perde yazısı ) atlanır.  Ölçü çözümlemesi bir çizimi yüzlerce
    kez kurar ( hesap/api/cizim.py );  ekrandaki ve paftadaki çizim tamdır."""
    eski = getattr(_KIP, "olcu", False)
    _KIP.olcu = True
    try:
        yield
    finally:
        _KIP.olcu = eski


def olcu_kipi():
    return getattr(_KIP, "olcu", False)


KATMANLAR = ("KUYU-DUVAR", "TARAMA", "BINA", "KUYU-IC", "KABIN", "KABIN-IC",
             "SASE", "KAPI", "AGIRLIK", "RAY", "KONSOL", "CIVATA", "PATEN",
             "KASNAK", "PANO", "OLCU", "EKSEN", "YAZI", "CERCEVE", "KORKULUK", "SIGINMA",
             "TAMPON", "PERDE", "MERDIVEN", "GIZLI", "YUK", "MAKINE", "BAGLANTI", "DELIK", "HALAT", "KESIT", "SEVIYE")

#  T profilinde flanş / gövde et kalınlığı;  1/20 planda ayrıntı okunmaz,
#  flanş + gövde yeterlidir.
_ET = 0.18


def _ad(el, ad):
    """Elemana kimlik verir;  ikinci bir çizim ( kabin üstü ) planın
    elemanlarından kendi ihtiyacı olanları bu adla seçer."""
    el["ad"] = ad
    return el


def _dik(katman, x, y, g, d, tip="dikdortgen", ad=""):
    el = {"tip": tip, "katman": katman, "x": float(x), "y": float(y),
          "g": float(g), "d": float(d)}
    if ad:
        el["ad"] = ad
    return el


def yer_adaylari(bolge, w, h, engeller, kenar=False, adim=25.0):
    """Bölgede ( x0, y0, x1, y1 ) engellere basmayan w × h kutular.

    Konumlar bölgenin köşesinden adım ızgarasıyla aranır;  kenar=True ise
    ızgaraya engellerin kenarlarına yaslanan konumlar da eklenir — ızgara dar
    ama yeterli bir boşluğu kaçırmasın ( 507 mm'lik banda 500'lük alan
    ızgarada ya şeride 1 mm değiyor ya bölgeden taşıyordu ).  Ekleme yalnız
    ızgara yer bulamayınca istenir:  bulunan yerler değişmesin."""
    x0, y0, x1, y1 = bolge

    def konumlar(a0, a1, boy, yasla):
        s = {a0 + i * adim for i in range(int((a1 - boy - a0) / adim + 1e-9) + 1)}
        if kenar:
            s |= {a1 - boy} | set(yasla)
        return sorted(a for a in s if a0 - 1e-9 <= a and a + boy <= a1 + 1e-9)

    xs = konumlar(x0, x1, w, [p[2] for p in engeller] + [p[0] - w for p in engeller])
    ys = konumlar(y0, y1, h, [p[3] for p in engeller] + [p[1] - h for p in engeller])
    return [(x, y, x + w, y + h) for y in ys for x in xs
            if not any(x < p[2] and p[0] < x + w and y < p[3] and p[1] < y + h for p in engeller)]


def _cizgi(katman, x1, y1, x2, y2, tip="cizgi"):
    return {"tip": tip, "katman": katman, "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2)}


def _olcu(yon, a, b, kot, metin=None, yazi=None, kural=None):
    """Ölçü.  `yazi` verilmezse yazının yeri _yazilari_yerlestir'de bulunur;
    verilirse { x, y ( yazının MERKEZİ ), aci, h } olduğu gibi kullanılır.
    `kural`:  ölçü bir girdiden değil standarttan ya da programın yerleşiminden
    geliyorsa onu söyleyen metin — ekranda ölçüye tıklanınca gösterilir
    ( olcu_kaynagi;  girdiye bağlı ölçülerin kaynağı ölçülerek bulunur )."""
    uzunluk = abs(b[0] - a[0]) if yon == "yatay" else abs(b[1] - a[1])
    el = {"tip": "olcu", "katman": "OLCU", "yon": yon, "a": tuple(map(float, a)),
          "b": tuple(map(float, b)), "kot": float(kot),
          "metin": metin if metin is not None else f"{uzunluk:g}",
          "uzunluk": uzunluk}
    if yazi:
        el["yazi"] = {"x": float(yazi["x"]), "y": float(yazi["y"]),
                      "aci": float(yazi.get("aci", 0)), "h": float(yazi.get("h", OLCU_YAZI))}
    if kural:
        el["kural"] = kural
    return el


#  Ölçü yazısının yüksekliği ( mm, 1/20'de 2,6 mm ) ve yazı eni tahmini:
#  harf başına yüksekliğin 0,6'sı  ( Arial / DejaVu ortalaması ).
OLCU_YAZI = 52.0


def _yazi_eni(metin, h=OLCU_YAZI):
    return len(metin) * h * 0.6


#  Ölçü yazısının üstüne düşmemesi gereken parçalar
PARCA_KATMANLARI = ("RAY", "KONSOL", "SASE", "TAMPON", "KASNAK", "MERDIVEN", "PERDE",
                    "MAKINE", "PANO", "PATEN")


def _yazilari_yerlestir(elemanlar, h=OLCU_YAZI):
    """Yeri verilmemiş ölçü yazılarını yerleştirir — SVG ve DXF AYNI yeri kullanır.

    Yazı önce kendi parçasının ortasına, ölçü çizgisinin dışına konur.  Aynı
    sıradaki bir yazıyla çakışırsa sıranın ucundaysa ucun dışına, değilse
    bir kat dışarı alınır.  Eskiden sığmayan yazı 130 – 280 mm öteye, BAŞKA
    BİR SIRANIN üstüne itiliyordu;  okuyan onu o sıranın ölçüsü sanıyordu.

    Parçasına sığmayan bir ARA ölçünün yazısı ortada bir parçanın ( şase,
    ray, konsol … ) üstüne düşüyorsa uzatma çizgisinin hemen dışına, geniş
    komşu tarafa yazılır ( AutoCAD'in sığmayan yazısı gibi ):  kuyu planında
    kabin duvarının "75"i şase dikmesinin üstündeydi.
    """
    k = h / OLCU_YAZI                                 # 1/50'de yazı ve aralıklar büyür
    parcalar = None

    def _biner(yon, kot, kat, orta, w):
        c = kot + (-1.0 if kot < 0 else 1.0) * (50.0 + 60.0 * kat) * k
        kutu = ((orta - w / 2.0, c - h / 2.0, orta + w / 2.0, c + h / 2.0) if yon == "yatay"
                else (c - h / 2.0, orta - w / 2.0, c + h / 2.0, orta + w / 2.0))
        return any(kutu[0] < p[2] and p[0] < kutu[2] and kutu[1] < p[3] and p[1] < kutu[3]
                   for p in parcalar)

    siralar = {}
    for el in elemanlar:
        if el["tip"] == "olcu" and "yazi" not in el:
            siralar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    for (yon, kot), liste in siralar.items():
        i = 0 if yon == "yatay" else 1
        liste.sort(key=lambda q: min(q["a"][i], q["b"][i]))
        dis = -1.0 if kot < 0 else 1.0
        yerlesen = []                                  # ( kat, bas, son )
        for n, q in enumerate(liste):
            bas, son = sorted((q["a"][i], q["b"][i]))
            w = _yazi_eni(q["metin"], h)
            aday = [(0, (bas + son) / 2.0)]
            uclar = ([(0, bas - w / 2.0 - 30 * k)] if n == 0 else []) + \
                    ([(0, son + w / 2.0 + 30 * k)] if n == len(liste) - 1 else [])
            #  Yazı parçasına sığmıyorsa ve sıranın ucundaysa ucun dışına yazılır
            #  ( referans projenin "62 83"ü gibi );  sığıyorsa parçanın ortasında durur.
            sigmaz = w > son - bas - 20 * k
            aday = uclar + aday if sigmaz else aday + uclar
            if sigmaz and not uclar:
                if parcalar is None:
                    parcalar = [sinir([x]) for x in elemanlar
                                if x.get("katman") in PARCA_KATMANLARI and x["tip"] != "yazi"]
                if _biner(yon, kot, 0, (bas + son) / 2.0, w):
                    boy = [abs(liste[m]["b"][i] - liste[m]["a"][i]) for m in (n - 1, n + 1)]
                    yanlar = [(0, son + w / 2.0 + 30 * k), (0, bas - w / 2.0 - 30 * k)]
                    if boy[0] > boy[1]:
                        yanlar.reverse()
                    aday = [a for a in yanlar if not _biner(yon, kot, a[0], a[1], w)] + aday
            aday += [(1, (bas + son) / 2.0), (2, (bas + son) / 2.0)]
            secilen = aday[-1]
            for kat, orta in aday:
                if not any(kt == kat and orta - w / 2.0 < s + 25 * k and b < orta + w / 2.0 + 25 * k
                           for kt, b, s in yerlesen):
                    secilen = (kat, orta)
                    break
            kat, orta = secilen
            yerlesen.append((kat, orta - w / 2.0, orta + w / 2.0))
            capraz = kot + dis * (50.0 + 60.0 * kat) * k
            q["yazi"] = ({"x": orta, "y": capraz, "aci": 0.0, "h": h} if yon == "yatay"
                         else {"x": capraz, "y": orta, "aci": 90.0, "h": h})


def _daire(katman, x, y, r):
    return {"tip": "daire", "katman": katman, "x": float(x), "y": float(y), "r": float(r)}


def _ok(katman, x1, y1, x2, y2):
    """Yön oku  ( kapı açılış yönü gibi )."""
    return {"tip": "ok", "katman": katman, "x1": float(x1), "y1": float(y1),
            "x2": float(x2), "y2": float(y2)}


def _yazi(x, y, metin, yukseklik=55, hiza="orta", katman="YAZI", aci=0):
    return {"tip": "yazi", "katman": katman, "x": float(x), "y": float(y),
            "metin": metin, "yukseklik": yukseklik, "hiza": hiza, "aci": float(aci)}


def _ray_yatay(yuz_x, eksen_y, b, h, yon):
    """Kabin rayı:  yüzü kabine bakar, gövdesi `yon` yönünde duvara uzanır."""
    t = b * _ET
    dis = yuz_x + h * yon                      # flanşın dış yüzü  ( duvar tarafı )
    flans_x = dis if yon > 0 else dis          # dikdörtgen sol köşesi
    flans_x = dis - t if yon > 0 else dis
    govde_x = yuz_x if yon > 0 else dis + t    # gövde YÜZDEN flanşa uzanır
    return [
        _dik("RAY", flans_x, eksen_y - b / 2.0, t, b),                      # flanş
        _dik("RAY", govde_x, eksen_y - t / 2.0, h - t, t),                  # gövde
    ]


def _ray_dusey(yuz_y, eksen_x, b, h, yon):
    """Ağırlık rayı:  yüzü ağırlığa bakar, gövdesi `yon` yönünde uzanır."""
    t = b * _ET
    dis = yuz_y + h * yon
    flans_y = dis - t if yon > 0 else dis
    govde_y = yuz_y if yon > 0 else dis + t
    return [
        _dik("RAY", eksen_x - b / 2.0, flans_y, b, t),
        _dik("RAY", eksen_x - t / 2.0, govde_y, t, h - t),
    ]


def halat_konumlari(g, S=None):
    """2:1 askıda halatların kuyudan geçtiği noktalar ( planda ).

    Halat kabinin iki kasnağının DIŞ teğetinden yukarı çıkar:
    x = kabin ekseni ± ( kasnaklar arası / 2 + çap / 2 ).  Kasnaklar kabinin
    altındaysa halat kabinin yanından, üstündeyse kabinin üstünden kuyu
    tepesine yükselir — ikisinde de kuyudaki parçaların arasından geçer.
    Doğrudan ( 1:1 ) askıda halat kabinin tepesindeki bağlantıdan çıkar.
    """
    S = S or CS.sabitler(g.get("_cizim_sabitleri"))
    a = g.get("aski") or {}
    if a.get("duzen") not in ("Kabin altı", "Kabin üstü"):
        return []
    from cizim import arka_aski as CAA
    if CAA.arkada_iki_bir(g):
        #  Arkadaki ağırlıkla 2:1:  tahrik kasnağının kabin inişi ve kabin
        #  bağlantısı ( çapraz düzlemin iki ucu — arka_aski )
        A = CAA.geometri(g, S)
        return [A["P"], A["H"]] if "P" in A else []
    k, kb = g["kuyu"], g["kabin"]
    kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
    y = kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0 + a.get("kasnak_kaciklik", 0)
    yari = a["kasnak_arasi"] / 2.0 + a["kasnak_capi"] / 2.0
    return [(kx - yari, y), (kx + yari, y)]


def kabin_kasnak_kutulari(g, S, taban):
    """Kabin kasnaklarının plandaki kutuları:  çapraz düzende ( arkadaki
    ağırlıkla 2:1 — arka_aski ) döndürülmüş kasnakların çevreleyen kutusu
    ( açıklık ve engel denetimleri için emniyetli taraf ), öbür düzenlerde
    plandaki dikdörtgen."""
    from cizim import arka_aski as CAA
    if CAA.arkada_iki_bir(g):
        A = CAA.geometri(g, S)
        return list(A.get("kutular") or [])
    return [(el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])
            for el in taban if el.get("ad") == "kabin_kasnak"]


def plan(g, cizim_sabitleri=None, kapi_duzeyi=True):
    """Kuyu planının elemanları  ( liste ).

    kapi_duzeyi:  plan kat kapısı hizasından kesilir ( C-C ) — ön duvar kapı
    boşluğunun iki yanında iki parçadır, tarama boşluktan geçmez.  Kapının
    üstünden / altından kesilen planlar ( kabin üstü, kuyu dibi, kuyu üstü,
    delik planı ) duvarı kesintisiz alır:  False."""
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    k, kb, kp = g["kuyu"], g["kabin"], g["kapi"]
    kr, ag = g["kabin_ray"], g["agirlik"]
    G, D = k["genislik"], k["derinlik"]
    ds, dg, don, dar = k["duvar_sol"], k["duvar_sag"], k["duvar_on"], k["duvar_arka"]
    e = []

    #  ── DUVARLAR  ( tarama yalnız duvar kesitinde ) ───────────────────
    #  Ön duvar kat kapısının kaba boşluğunun iki yanındadır ( CG.kaba_bosluk —
    #  giriş görünüşüyle aynı;  duvar boşluğuna monte kapıda kasa da boşluktadır ).
    b0, b1, _ = CG.kaba_bosluk(g, S)
    on = [(-ds, -don, b0 + ds, don), (b1, -don, G + dg - b1, don)] if kapi_duzeyi else \
        [(-ds, -don, G + ds + dg, don)]
    for x, y, g_, d_ in on + [(-ds, D, G + ds + dg, dar), (-ds, 0, ds, D), (G, 0, dg, D)]:
        if g_ <= 1e-6:
            continue
        e.append(_dik("TARAMA", x, y, g_, d_, tip="tarama"))
        e.append(_dik("KUYU-DUVAR", x, y, g_, d_))
    e.append(_dik("KUYU-IC", 0, 0, G, D))

    #  ── KAPI:  boşluk · kasa · eşik · kanatlar ───────────────────────
    #  Kat kapısı ünitesi ( kasa + eşik ) montaja göre ya duvar boşluğunda
    #  ( kasa duvarda, eşik kuyuya taşar ) ya da duvarın iç yüzünde durur
    #  ( ünitenin tamamı kuyunun içinde ).  KANATLAR EŞİĞİN ÜSTÜNDEDİR:
    #  kapalı konumda, teleskopikte iki düzlemde ( referans proje kapı detayı ).
    KB = CG.kapi_bolgesi(g, S)
    x0 = kp["sol_pay"]
    kg = kp["genislik"]
    e.append(_ad(_dik("KAPI", b0, -don, b1 - b0, don), "kapi_boslugu"))
    for kx0 in (x0 - S["kasa_yan"], x0 + kg):                       # kasa yanları
        e.append(_ad(_dik("KAPI", kx0, KB["kasa"][0], S["kasa_yan"], S["kasa_derinlik"]),
                     "kapi_kasasi"))
    e.append(_ad(_dik("KAPI", x0, KB["esik"][0], kg, S["esik_derinlik"]), "kat_esigi"))
    kanat = kg / 2.0
    tel = str(kp.get("tip", "")).startswith("Teleskopik")

    def kanatlar(esik0, esik1, ad):
        #  Teleskopik:  iki düzlem, eşiğin kenarından kanat_esik_payi içeride;
        #  merkezi:  iki kanat eşiğin ortasında aynı düzlemde.
        orta = (esik0 + esik1) / 2.0 - S["kanat_kalinlik"] / 2.0
        yer = []
        for i in range(2):
            ky0 = (esik0 + S["kanat_esik_payi"] + i * S["kanat_araligi"]) if tel else orta
            e.append(_ad(_dik("KAPI", x0 + i * kanat, ky0, kanat, S["kanat_kalinlik"]), ad))
            yer.append(ky0)
        return yer

    kat_kanat = kanatlar(KB["esik"][0], KB["esik"][1], "kat_kanadi")
    #  Açılış yönü oku:  teleskopik kapı hangi yana açılıyorsa o yöne bakar.
    ok_y = kat_kanat[0] + S["kanat_kalinlik"] / 2.0
    if tel:
        sag = str(kp.get("tip", "")).endswith("Sağ")
        e.append(_ok("KAPI", x0 + (kg * 0.65 if sag else kg * 0.35), ok_y,
                     x0 + (kg if sag else 0), ok_y))
    else:
        e.append(_ok("KAPI", x0 + kg / 2.0, ok_y, x0, ok_y))
        e.append(_ok("KAPI", x0 + kg / 2.0, ok_y, x0 + kg, ok_y))
    #  Kapının iki yanındaki bina duvarı yalnız istenirse çizilir.
    if S["bina_duvari"] > 0:
        for bx0, bg in ((-ds, x0 + ds), (x0 + kg, G - (x0 + kg) + dg)):
            if bg > 0:
                e.append(_dik("BINA", bx0, -don - S["bina_duvari"], bg, S["bina_duvari"],
                              tip="tarama_tugla"))

    #  ── KABİN:  pano · şase · kapı mekanizması ───────────────────────
    kx = G / 2.0 + kb["kaciklik_y"]
    ic_on = kb["on_pay"]                                   # kabin iç ön yüzü
    ky = ic_on + kb["derinlik"] / 2.0
    dis_g = kb["genislik"] + 2 * S["kabin_pano_yan"]
    dis_d = kb["derinlik"] + S["kabin_pano_arka"]
    e.append(_ad(_dik("KABIN", kx - dis_g / 2.0, ic_on, dis_g, dis_d), "kabin_dis"))          # kabin dışı
    e.append(_dik("KABIN-IC", kx - kb["genislik"] / 2.0, ic_on,
                  kb["genislik"], kb["derinlik"]))                          # kabin içi
    #  Şase dikmeleri ray ekseninde; plan ve kesit aynı derinliği kullanır.
    sd = S["sase_dikme_derinlik"]
    sy0 = kr["kapi_arasi"] - sd / 2.0
    for sx in (kx - dis_g / 2.0 - S["sase_dikme"], kx + dis_g / 2.0):
        e.append(_ad(_dik("SASE", sx, sy0, S["sase_dikme"], sd), "sase_dikme"))
    #  Şase kirişlerinin plan zarfı, ray eksenindeki iki dikmeyi bağlar.
    for sy in (sy0, sy0 + sd - S["sase_dikme"]):
        e.append(_ad(_dik("SASE", kx - dis_g / 2.0 - S["sase_dikme"], sy,
                      dis_g + 2 * S["sase_dikme"], S["sase_dikme"]), "sase_kiris"))
    #  Kabin kapısı mekanizma kutusu KABİN ÖN YÜZÜNDE durur  ( kapı ile kabin
    #  arasında;  kullanıcı kararı — referans projenin paftasındaki yerleşimin aynısı ).
    e.append(_dik("KABIN", x0 + kg / 2.0 - S["kabin_kapisi_kutu_en"] / 2.0,
                  ic_on - S["kabin_kapisi_kutu_boy"] + 20,
                  S["kabin_kapisi_kutu_en"], S["kabin_kapisi_kutu_boy"]))
    e.append(_cizgi("EKSEN", kx, -don - 150, kx, D + dar + 150, tip="eksen"))
    e.append(_cizgi("EKSEN", -ds - 150, ky, G + dg + 150, ky, tip="eksen"))

    #  ── KABİN RAYLARI · KONSOL · PATEN ───────────────────────────────
    ry = kr["kapi_arasi"]
    sol_yuz, sag_yuz = kx - kr["arasi"] / 2.0, kx + kr["arasi"] / 2.0
    #  KARŞI AĞIRLIK YANDAYSA o taraftaki kabin rayının duvara giden konsolu
    #  ağırlığın İÇİNDEN geçerdi:  ray ekseni ağırlığın boyu içinde kalır.
    #  O ray, iki ağırlık rayı konsolunun taşıdığı dikine bir ARA KİRİŞE
    #  bağlanır  ( referans projenin paftasındaki çözüm ).
    ag_yan = ag["yeri"] if ag["yeri"] in ("Sağ", "Sol") else None
    #  KARŞI AĞIRLIĞIN EKSENİ ( yandaki ağırlıkta ):  kabin ray ekseninden
    #  eksen_kaciklik kadar kayık — referans projede 50 mm önde.  Ağırlığın halatı
    #  tahrik kasnağının altına düşsün diye kabinin ray ekseninden ayrı durur.
    ag_y = ry + ag["eksen_kaciklik"]
    ag_alt = ag_y - ag["ray_arasi"] / 2.0 - ag["h"]        # ağırlık rayı arkaları
    ag_ust = ag_y + ag["ray_arasi"] / 2.0 + ag["h"]
    for yon, yuz in ((-1, sol_yuz), (+1, sag_yuz)):
        e += [_ad(r, "kabin_ray") for r in _ray_yatay(yuz, ry, kr["b"], kr["h"], yon)]
        arka = yuz + kr["h"] * yon          # rayın duvara bakan yüzü
        if ag_yan == ("Sol" if yon < 0 else "Sağ"):
            kiris_x = arka - S["ara_kiris_en"] if yon < 0 else arka
            e.append(_dik("KONSOL", kiris_x, ag_alt - S["konsol_agirlik_boy"] / 2.0,
                          S["ara_kiris_en"],
                          ag_ust - ag_alt + S["konsol_agirlik_boy"], ad="ara_kiris"))
        else:
            #  konsol:  duvara dayanan plaka  ( boşluğu doldurmaz )
            duvar_x = 0 if yon < 0 else G
            kx0 = duvar_x - S["konsol_kabin_en"] if yon > 0 else duvar_x
            e.append(_dik("KONSOL", kx0, ry - S["konsol_kabin_boy"] / 2.0,
                          S["konsol_kabin_en"], S["konsol_kabin_boy"], ad="plaka"))
            for cy in (ry - S["konsol_civata_araligi"], ry + S["konsol_civata_araligi"]):
                e.append(_daire("CIVATA", kx0 + S["konsol_kabin_en"] / 2.0, cy,
                                S["konsol_civata_capi"] / 2.0))
            #  KONSOL KOLU:  plakayı rayın arkasına bağlar.
            kol_bas = min(arka, kx0 + S["konsol_kabin_en"]) if yon < 0 else min(arka, kx0)
            kol_son = max(arka, kx0 + S["konsol_kabin_en"]) if yon < 0 else max(arka, kx0)
            if kol_son - kol_bas > 1:
                e.append(_dik("KONSOL", kol_bas, ry - S["konsol_kabin_boy"] / 6.0,
                              kol_son - kol_bas, S["konsol_kabin_boy"] / 3.0, ad="kol"))
        #  paten:  ray yüzünü kavrar
        e.append(_dik("PATEN", yuz - S["paten_en"] / 2.0, ry - S["paten_boy"] / 2.0,
                      S["paten_en"], S["paten_boy"]))
    e.append(_cizgi("EKSEN", -ds - 150, ry, G + dg + 150, ry, tip="eksen"))

    #  ── ASKI DÜZENİ  ( kullanıcı seçer:  kabin altı · kabin üstü · doğrudan )
    #  Kasnakların ve askı noktalarının yeri GİRDİDEN gelir;  koda gömülmez.
    aski = g.get("aski") or {}
    duzen = aski.get("duzen")
    aski_y = ic_on + dis_d / 2.0 + aski.get(
        "kasnak_kaciklik" if duzen in ("Kabin altı", "Kabin üstü") else "nokta_kaciklik", 0)
    aski_yari = 0.0                      # askı elemanının derinlikteki yarı boyu
    from cizim import arka_aski as CAA
    capraz = CAA.geometri(g, S) if CAA.arkada_iki_bir(g) else None
    if capraz is not None and "P" in capraz:
        #  ARKADAKİ AĞIRLIKLA 2:1 ( kabin üstü, çapraz — arka_aski ):  kasnaklar
        #  P–H düzleminde;  planda döndürülmüş dikdörtgen ( kenarları çizgi ),
        #  düzlem kesik eksen, iki düşey halat noktası.
        dc = aski["kasnak_capi"]
        for merkez, iz in zip(capraz["kasnaklar"], capraz["izler"]):
            for p0, p1 in zip(iz, iz[1:] + iz[:1]):
                e.append(_ad(_cizgi("KASNAK", p0[0], p0[1], p1[0], p1[1]), "kabin_kasnak_capraz"))
            e.append(_ad(_yazi(merkez[0] + capraz["n"][0] * 110, merkez[1] + capraz["n"][1] * 110,
                               f"ø {dc:g}", 45), "kabin_kasnak_yazi"))
        (px, py), (hx, hy) = capraz["P"], capraz["H"]
        e.append(_ad(_cizgi("EKSEN", px, py, hx, hy, tip="eksen"), "aski_duzlemi"))
        e.append(_ad(_yazi(capraz["cx"], capraz["cy"] - 230,
                           f"ASKI:  {duzen.upper()}  ·  2:1  ·  ÇAPRAZ {capraz['aci']:.0f}°", 44),
                     "aski_yazi"))
    elif duzen in ("Kabin altı", "Kabin üstü"):
        dc, aralik = aski["kasnak_capi"], aski["kasnak_arasi"]
        aski_yari = S["kabin_kasnak_genislik"] / 2.0
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(_ad(_dik("KASNAK", merkez - dc / 2.0, aski_y - aski_yari, dc, 2 * aski_yari), "kabin_kasnak"))
            e.append(_ad(_yazi(merkez, aski_y + aski_yari + 45, f"ø {dc:g}", 45), "kabin_kasnak_yazi"))
        e.append(_ad(_yazi(kx, aski_y - aski_yari - 230,
                       f"ASKI:  {duzen.upper()}  ·  2:1", 44), "aski_yazi"))
    elif duzen == "Doğrudan":
        #  1:1:  halatlar kabin şasesinin üst kirişinin ortasındaki TEK
        #  bağlantıda biter ( tek tahrik kasnağı — LiftDesigner 12744-3 );  kiriş
        #  ray ekseni üstündedir, kaçıklık hesabın xs'idir.
        aski_yari = 45.0
        e.append(_ad(_daire("KASNAK", kx, aski_y, 45), "aski_nokta"))
        e.append(_ad(_cizgi("KASNAK", kx - 70, aski_y, kx + 70, aski_y), "aski_nokta"))
        e.append(_ad(_cizgi("KASNAK", kx, aski_y - 70, kx, aski_y + 70), "aski_nokta"))
        e.append(_ad(_yazi(kx, aski_y - aski_yari - 230, "ASKI:  DOĞRUDAN  ·  1:1", 44), "aski_yazi"))

    from cizim import baglantilar as CB, makine as CMK
    e += CMK.plan(CB.kasnak_tasiyicilari(g, S, -S["kabin_kasnak_derinlik"]),
                  _dik, _daire, _cizgi)

    #  ── KARŞI AĞIRLIK:  çerçeve · dolgu · kasnak · raylar ────────────
    cer = S["agirlik_cerceve"]
    if ag_yan:
        sol = ag_yan == "Sol"
        ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]         # ağırlık ekseni
        ax, ay = ex - ag["derinlik"] / 2.0, ag_y - ag["genislik"] / 2.0
        e.append(_ad(_dik("AGIRLIK", ax, ay, ag["derinlik"], ag["genislik"]), "agirlik_blok"))
        e.append(_dik("AGIRLIK", ax + cer, ay + cer,
                      ag["derinlik"] - 2 * cer, ag["genislik"] - 2 * cer))
        #  Kabin rayının ara kirişi bu konsollara bağlanır:  kol plakadan
        #  kirişe uzanır  ( ağırlığın boyunun DIŞINDAN geçer ).
        kiris_ic = (sol_yuz - kr["h"] - S["ara_kiris_en"]) if sol else (sag_yuz + kr["h"]
                                                                        + S["ara_kiris_en"])
        for yuz, y_yon in ((ag_y + ag["ray_arasi"] / 2.0, +1), (ag_y - ag["ray_arasi"] / 2.0, -1)):
            e += [_ad(r, "agirlik_ray") for r in _ray_dusey(yuz, ex, ag["b"], ag["h"], y_yon)]
            duvar_x = 0 if sol else G
            plaka_x = duvar_x if sol else duvar_x - S["konsol_agirlik_en"]
            ray_arkasi = yuz + ag["h"] * y_yon
            e.append(_dik("KONSOL", plaka_x, ray_arkasi - S["konsol_agirlik_boy"] / 2.0,
                          S["konsol_agirlik_en"], S["konsol_agirlik_boy"], ad="plaka"))
            for cx in (plaka_x + S["konsol_agirlik_en"] / 2.0 - S["konsol_civata_araligi"],
                       plaka_x + S["konsol_agirlik_en"] / 2.0 + S["konsol_civata_araligi"]):
                e.append(_daire("CIVATA", cx, ray_arkasi, S["konsol_civata_capi"] / 2.0))
            kol_bas = plaka_x + S["konsol_agirlik_en"] if sol else kiris_ic
            kol_son = kiris_ic if sol else plaka_x
            if kol_son - kol_bas > 1:
                e.append(_dik("KONSOL", kol_bas, ray_arkasi - S["konsol_agirlik_boy"] / 6.0,
                              kol_son - kol_bas, S["konsol_agirlik_boy"] / 3.0, ad="kol"))
        if ag.get("kasnak_capi"):
            dc = ag["kasnak_capi"]
            e.append(_ad(_dik("KASNAK", ex - ag["derinlik"] / 2.0 + cer, ag_y - dc / 2.0,
                          ag["derinlik"] - 2 * cer, dc), "agirlik_kasnak"))
            e.append(_ad(_yazi(ex, ag_y, f"ø {dc:g}", 40, aci=90), "agirlik_kasnak_yazi"))
    else:
        ey = D - ag["ray_duvar"]
        ex = G / 2.0
        ax, ay = G / 2.0 - ag["genislik"] / 2.0, ey - ag["derinlik"] / 2.0
        e.append(_ad(_dik("AGIRLIK", ax, ay, ag["genislik"], ag["derinlik"]), "agirlik_blok"))
        e.append(_dik("AGIRLIK", ax + cer, ay + cer,
                      ag["genislik"] - 2 * cer, ag["derinlik"] - 2 * cer))
        for yuz, x_yon in ((G / 2.0 + ag["ray_arasi"] / 2.0, +1),
                           (G / 2.0 - ag["ray_arasi"] / 2.0, -1)):
            e += [_ad(r, "agirlik_ray") for r in _ray_yatay(yuz, ey, ag["b"], ag["h"], x_yon)]
            #  AĞIRLIK RAYI KONSOLU  ( arka duvar ):  yan yerleşimdeki konsolun
            #  aynısı, 90° dönük — rayın arkasında, duvara dayanır.
            ray_arkasi = yuz + ag["h"] * x_yon
            plaka_y = D - S["konsol_agirlik_en"]
            e.append(_dik("KONSOL", ray_arkasi - S["konsol_agirlik_boy"] / 2.0, plaka_y,
                          S["konsol_agirlik_boy"], S["konsol_agirlik_en"], ad="plaka"))
            for cy in (plaka_y + S["konsol_agirlik_en"] / 2.0 - S["konsol_civata_araligi"],
                       plaka_y + S["konsol_agirlik_en"] / 2.0 + S["konsol_civata_araligi"]):
                e.append(_daire("CIVATA", ray_arkasi, cy, S["konsol_civata_capi"] / 2.0))
        if ag.get("kasnak_capi"):
            dc = ag["kasnak_capi"]
            e.append(_ad(_dik("KASNAK", ex - dc / 2.0, ey - ag["derinlik"] / 2.0 + cer,
                          dc, ag["derinlik"] - 2 * cer), "agirlik_kasnak"))
            e.append(_ad(_yazi(ex, ey, f"ø {dc:g}", 40), "agirlik_kasnak_yazi"))

    #  KUMANDA PANOSU KUYU PLANINDA YOK:  makine dairesiz tesiste en üst katta
    #  kuyunun dışındaki acil kurtarma panosundadır ( kuyu üstü planı ), makine
    #  daireli tesiste makine dairesindedir.  Eskiden kuyunun içinde, yan
    #  duvarda kaynağı belirsiz 400 × 90'lık bir "PANO" çiziliyordu:  kesitlerde
    #  karşılığı yoktu, makine dairelide makine dairesindekiyle çift oluyordu.

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    #  Uzatma çizgisi yoktur:  ölçü, ölçtüğü noktaların hizasında durur.
    #  PLANIN DIŞINDAKİ SIRALAR yalnız kuyu sınırı boyunca okunabilen
    #  ölçüleri taşır;  bir iç parçayı ( askı, eşik ) ölçen ölçü parçanın
    #  yanına, planın İÇİNE konur — dışarıda neyi ölçtüğü görünmüyordu.
    #  Her sıra ( aynı kot ) bir zincirdir ve toplama kapanır.
    ic_sol = kx - dis_g / 2.0 - S["sase_dikme"]
    ic_sag = kx + dis_g / 2.0 + S["sase_dikme"]
    ARA = 200.0                                     # sıralar arası

    #  ÜST — kuyu genişliği boyunca
    u = [D + dar + 120 + i * ARA for i in range(5)]
    e += [
        _olcu("yatay", (-ds, 0), (0, 0), u[0], f"DUVAR {ds:g}"),
        _olcu("yatay", (0, 0), (G, 0), u[0], f"KUYU GENİŞLİĞİ {G:g}"),
        _olcu("yatay", (G, 0), (G + dg, 0), u[0], f"DUVAR {dg:g}"),
        _olcu("yatay", (-ds, 0), (G + dg, 0), u[1], f"DIŞ ÖLÇÜ {G + ds + dg:g}"),
        _olcu("yatay", (0, 0), (sol_yuz - kr["h"], 0), u[2]),
        _olcu("yatay", (sol_yuz - kr["h"], 0), (sol_yuz, 0), u[2], f"RAY {kr['h']:g}"),
        _olcu("yatay", (sol_yuz, 0), (sag_yuz, 0), u[2], f"DBG {kr['arasi']:g}"),
        _olcu("yatay", (sag_yuz, 0), (sag_yuz + kr["h"], 0), u[2], f"RAY {kr['h']:g}"),
        _olcu("yatay", (sag_yuz + kr["h"], 0), (G, 0), u[2]),
        _olcu("yatay", (0, 0), (ic_sol, 0), u[3]),
        _olcu("yatay", (ic_sol, 0), (ic_sag, 0), u[3], f"ŞASE DIŞI {ic_sag - ic_sol:g}"),
        _olcu("yatay", (ic_sag, 0), (G, 0), u[3]),
    ]
    if not ag_yan:
        #  Arkadaki ağırlığın rayları kuyu genişliği boyunca ölçülür
        e += [
            _olcu("yatay", (0, 0), (ex - ag["ray_arasi"] / 2.0, 0), u[4]),
            _olcu("yatay", (ex - ag["ray_arasi"] / 2.0, 0), (ex + ag["ray_arasi"] / 2.0, 0),
                  u[4], f"DBGW {ag['ray_arasi']:g}"),
            _olcu("yatay", (ex + ag["ray_arasi"] / 2.0, 0), (G, 0), u[4]),
        ]

    #  ALT — kapı zinciri, kuyu genişliği, kabin ve ağırlık eksenleri
    a1, a2, a3 = (-don - S["bina_duvari"] - 120, -don - S["bina_duvari"] - 320,
                  -don - S["bina_duvari"] - 520)
    kasa = S["kasa_yan"]
    e += [
        _olcu("yatay", (0, 0), (x0 - kasa, 0), a1),
        _olcu("yatay", (x0 - kasa, 0), (x0, 0), a1, f"KASA {kasa:g}"),
        _olcu("yatay", (x0, 0), (x0 + kg, 0), a1,
              f"KAPI {kg:g} x {kp.get('yukseklik', 2100):g}"),
        _olcu("yatay", (x0 + kg, 0), (x0 + kg + kasa, 0), a1, f"KASA {kasa:g}"),
        _olcu("yatay", (x0 + kg + kasa, 0), (G, 0), a1),
        _olcu("yatay", (0, 0), (G, 0), a2, f"KUYU GENİŞLİĞİ {G:g}"),
    ]
    noktalar = sorted(set([0.0, kx, G] + ([ex] if ag_yan else [])))
    for sol_n, sag_n in zip(noktalar, noktalar[1:]):
        metin = None
        if ((ag_yan == "Sol" and sol_n == 0 and sag_n == ex)
                or (ag_yan == "Sağ" and sol_n == ex and sag_n == G)):
            metin = f"AĞIRLIK RAYI {sag_n - sol_n:g}"
        e.append(_olcu("yatay", (sol_n, 0), (sag_n, 0), a3, metin))

    #  YANLAR — kuyu derinliği boyunca.  Sıra listesi duvardan dışarı
    #  doğrudur;  ağırlık yandaysa kendi zinciri O YANDA, duvara en yakın
    #  sırada durur  ( konsol kotları ağırlığın yanında okunur ).
    def _agirlik_zinciri(kot):
        return [
            _olcu("dusey", (0, 0), (0, ag_alt), kot),
            _olcu("dusey", (0, ag_alt), (0, ag_alt + ag["h"]), kot, f"{ag['h']:g}"),
            _olcu("dusey", (0, ag_alt + ag["h"]), (0, ag_ust - ag["h"]), kot,
                  f"DBGW {ag['ray_arasi']:g}"),
            _olcu("dusey", (0, ag_ust - ag["h"]), (0, ag_ust), kot, f"{ag['h']:g}"),
            _olcu("dusey", (0, ag_ust), (0, D), kot),
        ]

    def _civata(kot):
        #  Kabin rayı konsolunun cıvata aralığı — duvara dayanan konsolda
        c = S["konsol_civata_araligi"]
        return [_olcu("dusey", (0, ry - c), (0, ry), kot, f"CIVATA {c:g}"),
                _olcu("dusey", (0, ry), (0, ry + c), kot, f"{c:g}")]

    sol_siralar = []
    sag_siralar = []
    if ag_yan == "Sol":
        sol_siralar.append(_agirlik_zinciri)
    elif ag_yan == "Sağ":
        sag_siralar.append(_agirlik_zinciri)
    (sol_siralar if ag_yan == "Sağ" else sag_siralar).insert(0, _civata)
    sol_siralar += [
        lambda kot: [_olcu("dusey", (0, 0), (0, ry), kot, f"RAY EKSENİ {ry:g}"),
                     _olcu("dusey", (0, ry), (0, D), kot)],
        lambda kot: [_olcu("dusey", (0, -don), (0, D + dar), kot,
                           f"DIŞ ÖLÇÜ {D + don + dar:g}")],
    ]
    sag_siralar += [
        lambda kot: [_olcu("dusey", (0, 0), (0, D), kot, f"KUYU DERİNLİĞİ {D:g}")],
        lambda kot: [_olcu("dusey", (0, ic_on), (0, ic_on + kb["derinlik"]), kot,
                           f"KABİN {kb['derinlik']:g}")],
        lambda kot: [_olcu("dusey", (0, 0), (0, ic_on), kot, f"KAPI ARASI {ic_on:g}"),
                     _olcu("dusey", (0, ic_on), (0, ic_on + dis_d), kot,
                           f"KABİN + ŞASE {dis_d:g}"),
                     _olcu("dusey", (0, ic_on + dis_d), (0, D), kot)],
    ]
    for i, sira in enumerate(sol_siralar):
        e += sira(-ds - 120 - i * ARA)
    for i, sira in enumerate(sag_siralar):
        e += sira(G + dg + 120 + i * ARA)

    #  İÇ — kabin iç genişliği ve kabin – ray boşlukları  ( kabinin arkasında;
    #  ağırlık arkadaysa o şerit dolu olduğu için kabinin içinde, önde ).
    #  Arkadaki şerit yazıya yetmiyorsa ( referans proje:  147 mm ) kabinin içinde,
    #  arka panelin önünde durur — yazı arka duvara taşıyordu.
    arka_serit = D - (ic_on + dis_d)
    if not ag_yan:
        kab_kot = ic_on + 150
    elif arka_serit >= 90 + 50 + OLCU_YAZI / 2.0 + 40:
        kab_kot = ic_on + dis_d + 90
    else:
        kab_kot = ic_on + dis_d - 200
    e += [
        _olcu("yatay", (0, 0), (ic_sol, 0), kab_kot),
        _olcu("yatay", (ic_sol, 0), (kx - kb["genislik"] / 2.0, 0), kab_kot),
        _olcu("yatay", (kx - kb["genislik"] / 2.0, 0), (kx + kb["genislik"] / 2.0, 0), kab_kot,
              f"KABİN İÇİ {kb['genislik']:g}"),
        _olcu("yatay", (kx + kb["genislik"] / 2.0, 0), (ic_sag, 0), kab_kot),
        _olcu("yatay", (ic_sag, 0), (G, 0), kab_kot),
    ]

    #  İÇ — EŞİKLER  ( kat eşiği · aradaki açıklık · kabin eşiği ).  Kapının
    #  yanındaki boş şeritte, kuyu ön duvarı ile kabin arasında durur;  yazılar
    #  yatay ve ölçünün dışındadır ( parçalar 30 – 60 mm, yazı sığmaz ).
    #  İç yüzden kapı hattına:  duvar boşluğuna montajda kat eşiğinin taşan
    #  kısmı, kuyu içine montajda kat kapısı ünitesinin tamamı.
    hat_metni = (f"KAT EŞİĞİ {KB['hat']:g}" if kp["montaj"] == "Duvar boşluğuna"
                 else f"KAT KAPISI {KB['hat']:g}")
    esik = [(0.0, KB["hat"], hat_metni),
            (KB["hat"], KB["kabin_esik"][0], None),
            (KB["kabin_esik"][0], KB["kabin_esik"][1],
             f"KABİN EŞİĞİ {S['kabin_esik_derinlik']:g}")]
    h_esik = 40.0
    sol_bos = min(ic_sol, x0)                  # kapının solundaki boş şerit
    sag_bos = G - max(ic_sag, x0 + kg)
    if sol_bos >= sag_bos:
        esik_x, yan = sol_bos - 40.0, -1
    else:
        esik_x, yan = G - sag_bos + 40.0, +1
    onceki = -1e9
    for bas, son, metin in esik:
        metin = metin or f"{son - bas:g}"
        cy = max((bas + son) / 2.0, onceki + h_esik + 6)
        onceki = cy
        w = _yazi_eni(metin, h_esik)
        e.append(_olcu("dusey", (0, bas), (0, son), esik_x, metin,
                       yazi={"x": esik_x + yan * (30 + w / 2.0), "y": cy, "aci": 0,
                             "h": h_esik}))

    #  İÇ — ASKI:  kasnak / nokta aralığı askı elemanlarının hemen yanında,
    #  kaçıklık ise kabin merkezi ile askı ekseni arasında
    if duzen in ("Kabin altı", "Kabin üstü", "Doğrudan") and capraz is None:
        if duzen != "Doğrudan":                   # 1:1'de tek bağlantı:  aralık yok
            aralik = aski.get("kasnak_arasi")
            e.append(_olcu("yatay", (kx - aralik / 2.0, 0), (kx + aralik / 2.0, 0),
                           aski_y - aski_yari - 70, f"ASKI ARASI {aralik:g}",
                           yazi={"x": kx, "y": aski_y - aski_yari - 70 + 50, "aci": 0}))
        kac = aski_y - (ic_on + dis_d / 2.0)
        if abs(kac) > 1e-9:
            kac_x = kx - kb["genislik"] / 2.0 + 150
            metin = f"ASKI KAÇIKLIĞI {abs(kac):g}"
            e.append(_olcu("dusey", (0, aski_y), (0, ic_on + dis_d / 2.0), kac_x, metin,
                           yazi={"x": kac_x + 30 + _yazi_eni(metin) / 2.0,
                                 "y": (aski_y + ic_on + dis_d / 2.0) / 2.0, "aci": 0}))

    #  ── YAZILAR ──────────────────────────────────────────────────────
    e.append(_ad(_dik("KABIN", x0, KB["kabin_esik"][0], kg, S["kabin_esik_derinlik"]),
                 "kabin_esigi"))
    kanatlar(KB["kabin_esik"][0], KB["kabin_esik"][1], "kabin_kanadi")
    #  Askı noktaları kabin ortasına yakınsa kabin yazısı arkaya kayar.
    kabin_yazi_y = ky if abs(aski_y - ky) >= 150 else ky + 200
    e.append(_yazi(kx, kabin_yazi_y, f"KABİN  {kb['genislik']:g} x {kb['derinlik']:g}", 55))
    #  Ölçü zincirlerinin sıfır noktaları  ( referans projede de "0" yazar )
    for zx in (0, G):
        e.append(_yazi(zx, -don - S["bina_duvari"] - 420, "0", 45))
    if ag_yan:
        #  Blok dar ve uzun:  yazı DİK yazılır.  Kasnak bloğun ortasında
        #  durduğu için yazı blok ile kabin rayı arasındaki boşluğa konur;
        #  boşluk dar ise bloğun içine.
        blok_ic = ex + ag["derinlik"] / 2.0 if ag_yan == "Sol" else ex - ag["derinlik"] / 2.0
        bos = abs(kiris_ic - blok_ic)
        yx = (blok_ic + kiris_ic) / 2.0 if bos >= 60 else ex
        e.append(_ad(_yazi(yx, ag_y, "KARŞI AĞIRLIK", 40, aci=90), "agirlik_yazi"))
    else:
        e.append(_ad(_yazi(ex, ey - ag["derinlik"] / 2.0 - 45, "KARŞI AĞIRLIK", 40), "agirlik_yazi"))
    _yazilari_yerlestir(e)
    e += kesit_isaretleri(g, e)
    return e


def kesit_duzlemleri(g):
    """A-A düzleminin x'i ( kabin ekseni ) ve B-B düzleminin y'si ( kabinin
    arkası ile arka duvarın ortası )."""
    k, kb = g["kuyu"], g["kabin"]
    arka = kb["on_pay"] + kb["derinlik"] + CS.sabitler(g.get("_cizim_sabitleri"))["kabin_pano_arka"]
    return k["genislik"] / 2.0 + kb["kaciklik_y"], (arka + k["derinlik"]) / 2.0


def kesit_isaretleri(g, e):
    """A-A ve B-B düşey kesitlerinin plandaki işaretleri ( kuyu_kesiti.py ).

    Standart çizim kuralı:  kesit düzlemi yalnız uçlarında kalın kısa bir
    çizgiyle, bakış yönü okla ve harfle gösterilir;  planın ölçülerinin
    dışında durur.  A-A kabin ekseninden karşı ağırlığa bakar;  B-B kabinin
    arkasından kat kapılarına.  Kesitler çizilebiliyorsa konur:  yandaki
    karşı ağırlık, kabin altı 2:1, makine kuyu üstünde.
    """
    ag = g["agirlik"]
    #  Kesitler kuyu üstü düzeni çizilebiliyorsa konur ( kuyu_ustu.yerlesim )
    duzen = (g.get("aski") or {}).get("duzen")
    md_ = (g.get("makine") or {}).get("yeri") == "Makine dairesi"
    if not ((ag.get("yeri") in ("Sol", "Sağ") and (duzen in ("Kabin altı", "Kabin üstü")
                                                     or (duzen == "Doğrudan" and md_)))
            or (ag.get("yeri") == "Arka" and duzen == "Doğrudan" and md_)) or \
            (g.get("makine") or {}).get("yeri") not in ("Kuyu üstü", "Makine dairesi"):
        return []
    x1, y1, x2, y2 = sinir(e)
    kx, yb = kesit_duzlemleri(g)
    yon_a = -1.0 if ag["yeri"] == "Sol" else 1.0
    L, O, P = 300.0, 260.0, 150.0
    cikti = []
    for harf, (px, py), (dx, dy), (ox, oy) in (
            ("A", (kx, y2 + P), (0, 1), (yon_a, 0)), ("A", (kx, y1 - P), (0, -1), (yon_a, 0)),
            ("B", (x1 - P, yb), (-1, 0), (0, -1)), ("B", (x2 + P, yb), (1, 0), (0, -1))):
        cikti.append(_ad(_cizgi("KESIT", px, py, px + dx * L, py + dy * L), "kesit_isareti"))
        tx, ty = px + dx * L / 2.0, py + dy * L / 2.0
        cikti.append(_ok("KESIT", tx, ty, tx + ox * O, ty + oy * O))
        cikti.append(_ad(_yazi(tx + ox * (O + 90), ty + oy * (O + 90), harf, 90), "kesit_harfi"))
    return cikti


def sinir(elemanlar, pay=0.0):
    """Elemanların kapsayan dikdörtgeni  ( x1, y1, x2, y2 )."""
    xs, ys = [], []
    for el in elemanlar:
        if el["tip"] in ("dikdortgen", "tarama"):
            xs += [el["x"], el["x"] + el["g"]]; ys += [el["y"], el["y"] + el["d"]]
        elif el["tip"] in ("cizgi", "eksen", "ok"):
            xs += [el["x1"], el["x2"]]; ys += [el["y1"], el["y2"]]
        elif el["tip"] == "daire":
            xs += [el["x"] - el["r"], el["x"] + el["r"]]; ys += [el["y"] - el["r"], el["y"] + el["r"]]
        elif el["tip"] == "olcu":
            if el["yon"] == "yatay":
                xs += [el["a"][0], el["b"][0]]; ys += [el["kot"]]
            else:
                ys += [el["a"][1], el["b"][1]]; xs += [el["kot"]]
            y_ = el.get("yazi")
            if y_:
                #  Yazı da çerçevenin içinde kalmalı  ( "ASKI KAÇIKLIĞI"
                #  çerçeveye taşıp kesiliyordu ).
                w, h = _yazi_eni(el["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                if y_["aci"]:
                    w, h = h, w
                xs += [y_["x"] - w, y_["x"] + w]; ys += [y_["y"] - h, y_["y"] + h]
        elif el["tip"] == "yazi":
            #  Yazının eni de:  sola hizalı bir tablo satırı çerçeveden taşıyordu
            w, h = _yazi_eni(el["metin"], el["yukseklik"]), el["yukseklik"] / 2.0
            a, b = {"sol": (0.0, w), "sag": (-w, 0.0)}.get(el.get("hiza"), (-w / 2.0, w / 2.0))
            if abs(abs(el.get("aci", 0)) - 90) < 1e-6:
                xs += [el["x"] - h, el["x"] + h]
                ys += [el["y"] + a, el["y"] + b] if el["aci"] > 0 else [el["y"] - b, el["y"] - a]
            else:
                xs += [el["x"] + a, el["x"] + b]; ys += [el["y"] - h, el["y"] + h]
    return (min(xs) - pay, min(ys) - pay, max(xs) + pay, max(ys) + pay)


def zincirler(elemanlar):
    """Aynı kota düşen ölçüleri zincir hâlinde toplar  ( kapanma denetimi )."""
    gruplar = {}
    for el in elemanlar:
        if el["tip"] == "olcu":
            gruplar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    cikti = []
    for (yon, kot), liste in sorted(gruplar.items()):
        i = 0 if yon == "yatay" else 1
        cikti.append({"yon": yon, "kot": kot,
                      "bas": min(min(el["a"][i], el["b"][i]) for el in liste),
                      "son": max(max(el["a"][i], el["b"][i]) for el in liste),
                      "toplam": sum(el["uzunluk"] for el in liste),
                      "adet": len(liste)})
    return cikti


def cerceveli(elemanlar, baslik, olcek=20, pay=300, seritler=()):
    """Çizimi kendi çerçevesine alır ve altına başlık şeridi ekler.

    Referans projede de her çizim ayrı bir çerçevededir ve altında adı ile ölçeği
    yazar.  Çerçeve ölçüleri de kapsar;  yazılar dışarıda kalmaz.
    """
    k = olcek / 20.0                     # yazılar paftada 1/20'deki boyda kalır
    x1, y1, x2, y2 = sinir(elemanlar, pay * k)
    serit = 220.0 * k
    #  Künye şeridi başlığı ve sağdaki yazıları taşımalı:  sığmıyorsa
    #  çerçeve iki yana eşit genişler  ( başlık proje adının üstüne biniyordu ).
    gerek = (120 + 200 + 120) * k + _yazi_eni(f"{baslik}   1/{olcek:g}", 95 * k) + \
        max([_yazi_eni(m, 70 * k) for m in seritler] or [0])
    if x2 - x1 < gerek:
        fark = (gerek - (x2 - x1)) / 2.0
        x1, x2 = x1 - fark, x2 + fark
    e = list(elemanlar)
    e.append(_dik("CERCEVE", x1, y1 - serit, x2 - x1, (y2 - y1) + serit))
    e.append(_cizgi("CERCEVE", x1, y1, x2, y1))
    e.append(_yazi(x1 + 120 * k, y1 - serit / 2.0, f"{baslik}   1/{olcek:g}", 95 * k, hiza="sol",
                   katman="CERCEVE"))
    for i, metin in enumerate(seritler):
        e.append(_yazi(x2 - 120 * k, y1 - serit / 2.0 - i * 120 * k, metin, 70 * k, hiza="sag",
                       katman="CERCEVE"))
    return e
