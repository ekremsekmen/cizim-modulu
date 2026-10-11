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
import math
import re
import threading

from cizim import eleman
from cizim import girdi
from cizim import parcalar
from cizim import sabitler
from cizim import arka_aski
from cizim import baglantilar, makine

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


#  T profilinde flanş / gövde et kalınlığı;  1/20 planda ayrıntı okunmaz,
#  flanş + gövde yeterlidir.
_ET = 0.18


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
    return [
        (x, y, x + w, y + h)
        for y in ys
        for x in xs
        if not any(x < p[2] and p[0] < x + w and y < p[3] and p[1] < y + h for p in engeller)
    ]


#  Ölçü yazısının üstüne düşmemesi gereken parçalar
PARCA_KATMANLARI = (
    "RAY",
    "KONSOL",
    "SASE",
    "TAMPON",
    "KASNAK",
    "MERDIVEN",
    "PERDE",
    "MAKINE",
    "PANO",
    "PATEN",
)


def _yazilari_yerlestir(elemanlar, h=eleman.OLCU_YAZI, kaydir=False):
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
    k = h / eleman.OLCU_YAZI  # 1/50'de yazı ve aralıklar büyür
    parca_kutulari = None
    #  Parça kenarları ( parca_kenarlari ):  yazı maskelidir, bir kenarın üstüne
    #  düşerse kenarı siler — kuyu planında kabin duvarının "75"i kabinin iki
    #  çizgisinin üstündeydi ( 5 Eki ).
    kenarlar = KenarIzgarasi(parca_kenarlari(elemanlar))

    def _biner(yon, kot, kat, orta, w):
        c = kot + (-1.0 if kot < 0 else 1.0) * (50.0 + eleman.KAT_ARALIGI * kat) * k
        kutu = (
            (orta - w / 2.0, c - h / 2.0, orta + w / 2.0, c + h / 2.0)
            if yon == "yatay"
            else (c - h / 2.0, orta - w / 2.0, c + h / 2.0, orta + w / 2.0)
        )
        return any(
            kutu[0] < p[2] and p[0] < kutu[2] and kutu[1] < p[3] and p[1] < kutu[3] for p in parca_kutulari
        ) or kenarlar.kesisir(kutu, 2.0 * k)

    #  Ölçü yazısının üstüne düşmemesi gereken parçaların kutuları
    parca_kutulari = [
        sinir([x]) for x in elemanlar if x.get("katman") in PARCA_KATMANLARI and x["tip"] != "yazi"
    ]

    def _kenara_biner(kutu):
        return kenarlar.kesisir(kutu, 2.0 * k) or any(
            kutu[0] < p[2] - 2 and p[0] < kutu[2] - 2 and kutu[1] < p[3] - 2 and p[1] < kutu[3] - 2
            for p in parca_kutulari
        )

    siralar = {}
    for el in elemanlar:
        if el["tip"] == "olcu" and "yazi" not in el:
            siralar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    #  BAŞKA SIRALARIN YAZILARI da sayılır ( yeri verilmiş ölçü yazıları ve bu
    #  çağrıda yerleşenler ):  sığmayan yazı ucun dışına çıkınca köşede öbür
    #  yöndeki sıranın yazısına biniyordu ( kuyu planının sağ üst köşesinde iki
    #  "DUVAR 150" — yazılar büyüyünce, 5 Eki ).
    dolu = [_yazi_kutusu_(el) for el in elemanlar if el["tip"] == "olcu" and "yazi" in el]

    def _kutu(yon, kot, kat, orta, w):
        c = kot + (-1.0 if kot < 0 else 1.0) * (50.0 + eleman.KAT_ARALIGI * kat) * k
        return (
            (orta - w / 2.0, c - h / 2.0, orta + w / 2.0, c + h / 2.0)
            if yon == "yatay"
            else (c - h / 2.0, orta - w / 2.0, c + h / 2.0, orta + w / 2.0)
        )

    for (yon, kot), liste in siralar.items():
        i = 0 if yon == "yatay" else 1
        liste.sort(key=lambda q: min(q["a"][i], q["b"][i]))
        dis = -1.0 if kot < 0 else 1.0
        yerlesen = []  # ( kat, bas, son )
        for n, q in enumerate(liste):
            bas, son = sorted((q["a"][i], q["b"][i]))
            w = eleman.yazi_eni(q["metin"], h)
            aday = [(0, (bas + son) / 2.0)]
            uclar = ([(0, bas - w / 2.0 - 30 * k)] if n == 0 else []) + (
                [(0, son + w / 2.0 + 30 * k)] if n == len(liste) - 1 else []
            )
            #  Yazı parçasına sığmıyorsa ve sıranın ucundaysa ucun dışına yazılır
            #  ( referans projenin "62 83"ü gibi );  sığıyorsa parçanın ortasında durur.
            sigmaz = w > son - bas - 20 * k
            aday = uclar + aday if sigmaz else aday + uclar
            if sigmaz and not uclar:
                if parca_kutulari is None:
                    parca_kutulari = [
                        sinir([x])
                        for x in elemanlar
                        if x.get("katman") in PARCA_KATMANLARI + (("KAPI",) if kaydir else ())
                        and x["tip"] != "yazi"
                    ]
                if _biner(yon, kot, 0, (bas + son) / 2.0, w):
                    boy = [abs(liste[m]["b"][i] - liste[m]["a"][i]) for m in (n - 1, n + 1)]
                    yanlar = [(0, son + w / 2.0 + 30 * k), (0, bas - w / 2.0 - 30 * k)]
                    if boy[0] > boy[1]:
                        yanlar.reverse()
                    aday = [a for a in yanlar if not _biner(yon, kot, a[0], a[1], w)] + aday
            elif kaydir and not sigmaz:
                #  kaydir:  sığan yazı ortada bir parçanın üstüne düşüyorsa kendi
                #  ölçüsünün içinde, ortaya en yakın boş yere kayar ( kabin üstü
                #  planında sığınma alanının yer ölçüsü şasenin üst kirişinin
                #  üstündeydi ).  Öbür çizimlerde yazıların yeri değişmez:  kuyu
                #  dibinde yük kutuları onlara göre yerleşir.
                if parca_kutulari is None:
                    parca_kutulari = [
                        sinir([x])
                        for x in elemanlar
                        if x.get("katman") in PARCA_KATMANLARI + ("KAPI",) and x["tip"] != "yazi"
                    ]
                orta = (bas + son) / 2.0
                if _biner(yon, kot, 0, orta, w):
                    pay = (son - bas - w) / 2.0 - 10 * k
                    adim = [orta + s * d for d in range(10, int(pay) + 1, 10) for s in (-1, 1)]
                    bos = [x for x in adim if not _biner(yon, kot, 0, x, w)]
                    #  Ölçünün içinde boş yer yoksa ve sıranın ucundaysa ucun dışı
                    #  ( operatörün derinliğindeki parça:  operatör tavanın
                    #  genişliğince uzanır )
                    bos += [a[1] for a in uclar if not _biner(yon, kot, 0, a[1], w)]
                    if bos:
                        aday = [(0, bos[0])] + aday
            aday += [(1, (bas + son) / 2.0), (2, (bas + son) / 2.0)]
            #  Seçim:  sırasındaki yazılara binmeyen ( şart ), öbür yazılara
            #  binmeyen, parça kenarına binmeyen ilk aday;  hepsini sağlayan
            #  yoksa ilk ikisini, o da yoksa yalnız ilkini sağlayan.
            ilk = yazisiz = temiz = None
            for kat, orta in aday:
                if any(
                    kt == kat and orta - w / 2.0 < s + 25 * k and b < orta + w / 2.0 + 25 * k
                    for kt, b, s in yerlesen
                ):
                    continue
                ilk = ilk or (kat, orta)
                kb_ = _kutu(yon, kot, kat, orta, w)
                if any(kb_[0] < d[2] and d[0] < kb_[2] and kb_[1] < d[3] and d[1] < kb_[3] for d in dolu):
                    continue
                yazisiz = yazisiz or (kat, orta)
                if not _kenara_biner(kb_):
                    temiz = (kat, orta)
                    break
            if temiz is None:
                #  Adayların hepsi bir parçaya biniyor ( kuyunun içinden geçen
                #  sıralar ):  yazı kendi ölçüsü boyunca kayar — uçların hemen
                #  dışına kadar, önce az kayan, sonra dış katlar.
                orta0 = (bas + son) / 2.0
                yari = (son - bas + w) / 2.0 + 30 * k
                kaymalar = sorted(
                    {
                        (kat_, d * 20 * k * sgn)
                        for kat_ in (0, 1, 2)
                        for d in range(1, int(yari / (20 * k)) + 1)
                        for sgn in (-1, 1)
                    },
                    key=lambda a: (abs(a[1]), a[0]),
                )
                for kat_, kay in kaymalar:
                    orta = orta0 + kay
                    if any(
                        kt == kat_ and orta - w / 2.0 < s + 25 * k and b < orta + w / 2.0 + 25 * k
                        for kt, b, s in yerlesen
                    ):
                        continue
                    kb_ = _kutu(yon, kot, kat_, orta, w)
                    if any(kb_[0] < d[2] and d[0] < kb_[2] and kb_[1] < d[3] and d[1] < kb_[3] for d in dolu):
                        continue
                    if not _kenara_biner(kb_):
                        temiz = (kat_, orta)
                        break
            kat, orta = temiz or yazisiz or ilk or aday[-1]
            yerlesen.append((kat, orta - w / 2.0, orta + w / 2.0))
            dolu.append(_kutu(yon, kot, kat, orta, w))
            capraz = kot + dis * (50.0 + eleman.KAT_ARALIGI * kat) * k
            q["yazi"] = (
                {"x": orta, "y": capraz, "aci": 0.0, "h": h}
                if yon == "yatay"
                else {"x": capraz, "y": orta, "aci": 90.0, "h": h}
            )


def _yazi_kutusu_(el):
    """Yeri verilmiş ölçü yazısının kutusu."""
    y = el["yazi"]
    w, h = (
        eleman.yazi_eni(el["metin"], y.get("h", eleman.OLCU_YAZI)) / 2.0,
        y.get("h", eleman.OLCU_YAZI) / 2.0,
    )
    if y.get("aci"):
        w, h = h, w
    return (y["x"] - w, y["y"] - h, y["x"] + w, y["y"] + h)


def _ray_bicimli(zarf, bicim):
    """Rayın iki zarf dikdörtgeni ( flanş + gövde ) mantık içindir;  çizilen
    biçim ISO 7465 kesitidir ( parcalar.ray_bicimi ) — flanşın zarfı biçimi
    taşır, gövdeninki çizilmez.  Profil tabloda yoksa zarflar çizilir."""
    if bicim is not None:
        zarf[0]["bicim"], zarf[1]["bicim"] = bicim, []
    return zarf


def _ray_yatay(yuz_x, eksen_y, b, h, yon):
    """Kabin rayı:  yüzü kabine bakar, gövdesi `yon` yönünde duvara uzanır."""
    t = b * _ET
    dis = yuz_x + h * yon  # flanşın dış yüzü  ( duvar tarafı )
    flans_x = dis if yon > 0 else dis  # dikdörtgen sol köşesi
    flans_x = dis - t if yon > 0 else dis
    govde_x = yuz_x if yon > 0 else dis + t  # gövde YÜZDEN flanşa uzanır
    return _ray_bicimli(
        [
            eleman.dikdortgen("RAY", flans_x, eksen_y - b / 2.0, t, b),  # flanş
            eleman.dikdortgen("RAY", govde_x, eksen_y - t / 2.0, h - t, t),  # gövde
        ],
        parcalar.ray_bicimi(b, h, yuz_x, eksen_y, yon, yatay=True),
    )


def _ray_dusey(yuz_y, eksen_x, b, h, yon):
    """Ağırlık rayı:  yüzü ağırlığa bakar, gövdesi `yon` yönünde uzanır."""
    t = b * _ET
    dis = yuz_y + h * yon
    flans_y = dis - t if yon > 0 else dis
    govde_y = yuz_y if yon > 0 else dis + t
    return _ray_bicimli(
        [
            eleman.dikdortgen("RAY", eksen_x - b / 2.0, flans_y, b, t),
            eleman.dikdortgen("RAY", eksen_x - t / 2.0, govde_y, t, h - t),
        ],
        parcalar.ray_bicimi(b, h, yuz_y, eksen_x, yon, yatay=False),
    )


def _tirnaklar(arka, eksen, b, h, yon, J=None, yatay=True):
    """Rayın iki tırnağı ve cıvataları ( parcalar.tirnak_bicimi ) — CIVATA
    katmanında, zarfı biçimin kapsayanı.  Profil tabloda yoksa çizilmez."""
    g, k = parcalar.ray_taban_ucu(b, h), parcalar.ray_dil_kalinligi(b, h)
    if g is None or k is None:
        return []
    bicim = parcalar.tirnak_bicimi(arka, eksen, b, g, k, yon, J, yatay)
    if not bicim:
        return []
    xs = [p[0] for q in bicim for p in q["noktalar"]]
    ys = [p[1] for q in bicim for p in q["noktalar"]]
    el = eleman.dikdortgen("CIVATA", min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys), ad="ray_tirnagi")
    el["bicim"] = bicim
    return [el]


def _agirlik_pateni(S, ag, uc, eksen, yon, yatay):
    """Karşı ağırlığın pateni ( planda ):  rayın dil ucunda, kabin patenleriyle
    aynı zarf — kesitlerin kutusu da bu ( baglantilar.agirlik_patenleri;
    kullanıcı kararı 30 Eyl:  makaralıda da aynı iz ).  Çizilen biçim paten
    tipine göre:  kaymalı ( parcalar.paten_bicimi ) ya da üç makara
    ( parcalar.makarali_paten_bicimi — makaralar zarfın dışına taşar:  ağırlığın
    çerçevesinin üstünde / altındadır ).  uc:  dil ucu;  yon:  dilden tabana."""
    en, boy = S["paten_en"], S["paten_boy"]
    if yatay:  # ray x yönünde ( arkadaki ağırlık )
        el = eleman.dikdortgen("PATEN", uc - en / 2.0, eksen - boy / 2.0, en, boy, ad="agirlik_pateni")
    else:
        el = eleman.dikdortgen("PATEN", eksen - boy / 2.0, uc - en / 2.0, boy, en, ad="agirlik_pateni")
    k = parcalar.ray_dil_kalinligi(ag["b"], ag["h"])
    if k is None:
        return el
    if ag.get("paten_tipi") == "Makaralı":
        el["bicim"] = parcalar.makarali_paten_bicimi(uc, eksen, k, yon, yatay)
    else:
        el["bicim"] = parcalar.paten_bicimi(el["x"], el["y"], el["g"], el["d"], uc, k, yon, yatay)
    return el


def halat_konumlari(g, S=None):
    """2:1 askıda halatların kuyudan geçtiği noktalar ( planda ).

    Halat kabinin iki kasnağının DIŞ teğetinden yukarı çıkar:
    x = kabin ekseni ± ( kasnaklar arası / 2 + çap / 2 ).  Kasnaklar kabinin
    altındaysa halat kabinin yanından, üstündeyse kabinin üstünden kuyu
    tepesine yükselir — ikisinde de kuyudaki parçaların arasından geçer.
    Doğrudan ( 1:1 ) askıda halat kabinin tepesindeki bağlantıdan çıkar.
    """
    S = S or sabitler.sabitler(g.get("_cizim_sabitleri"))
    a = g.get("aski") or {}
    if a.get("duzen") not in ("Kabin altı", "Kabin üstü"):
        return []

    if arka_aski.arkada_iki_bir(g):
        #  Arkadaki ağırlıkla 2:1:  tahrik kasnağının kabin inişi ve kabin
        #  bağlantısı ( çapraz düzlemin iki ucu — arka_aski )
        A = arka_aski.geometri(g, S)
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

    if arka_aski.arkada_iki_bir(g):
        A = arka_aski.geometri(g, S)
        return list(A.get("kutular") or [])
    return [
        (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])
        for el in taban
        if el.get("ad") == "kabin_kasnak"
    ]


#  Kanat cebinin çarpabileceği parçalar ( planın adıyla ) ve iletideki adları
_CEP_ENGELLERI = {
    "plaka": "ray konsoluna",
    "kol": "ray konsolunun koluna",
    "ara_kiris": "kabin rayının ara kirişine",
    "kabin_ray": "kabin rayına",
    "agirlik_ray": "karşı ağırlık rayına",
    "agirlik_blok": "karşı ağırlığa",
}


def kanat_cebi_carpismalari(g, cizim_sabitleri=None):
    """Kat ve kabin kapısının kanat cebi ( açılan kanatların durduğu yer —
    girdi.kanat_cepleri ) kuyudaki konsollara, raylara ve karşı ağırlığa
    çarpmamalı.  Kabin kapısının cebi kabinle yürür:  bütün katlarda aynı
    yerde bulunan bu parçaların hepsini geçmelidir.  İletiler ( liste )."""
    e = plan(g, cizim_sabitleri)
    cepler = [x for x in e if x.get("ad") in ("kanat_cebi", "kabin_kanat_cebi")]
    engeller = [x for x in e if x["tip"] == "dikdortgen" and x.get("ad") in _CEP_ENGELLERI]
    hata = []
    for c in cepler:
        for o in engeller:
            if (
                c["x"] < o["x"] + o["g"] - 1e-6
                and o["x"] < c["x"] + c["g"] - 1e-6
                and c["y"] < o["y"] + o["d"] - 1e-6
                and o["y"] < c["y"] + c["d"] - 1e-6
            ):
                kim = "Kabin kapısının" if c["ad"] == "kabin_kanat_cebi" else "Kat kapısının"
                metin = (
                    f"{kim} kanat cebi {_CEP_ENGELLERI[o['ad']]} çarpıyor:  açılan kanatlar "
                    "kuyuda yer bulamıyor — kapıyı öbür yana açın, kanat sayısını artırın "
                    "ya da kapının yerini değiştirin."
                )
                if metin not in hata:
                    hata.append(metin)
    return hata


def dogrula(g):
    """Kuyu planının tam denetimi:  girdinin kendisi ( girdi.dogrula ) ve
    planın parçalarıyla — kanat cepleri kuyudaki sabit parçalara ( konsollar,
    raylar ) ve karşı ağırlığa çarpmamalı ( yalnız girdi temizse:  plan geçersiz
    girdiyle kurulmaz ).  Eskiden ikincisi girdi.dogrula'nın içindeydi ve
    girdi geometriyi fonksiyon içinden import ediyordu ( iki modül birbirine
    dolanmıştı )."""
    hata = girdi.dogrula(g)
    if not hata:
        hata += kanat_cebi_carpismalari(g, sabitler.sabitler(g.get("_cizim_sabitleri")))
    return hata


#  Kuyu planında ( C-C ) kesitin üstünde ya da kabin döşemesinin altında kalan
#  askı parçaları ( plan(), kapi_duzeyi )
_KESITTE_GIZLI = frozenset(
    ("sase_kiris", "kabin_kasnak", "kabin_kasnak_capraz", "aski_nokta", "kasnak_tasiyici_sematik")
)


def plan(g, cizim_sabitleri=None, kapi_duzeyi=True, duvar_boslugu=None):
    """Kuyu planının elemanları  ( liste ).

    kapi_duzeyi:  plan kat kapısı hizasından kesilir ( C-C ) — ön duvar kapı
    boşluğunun iki yanında iki parçadır, tarama boşluktan geçmez.  Kapının
    üstünden / altından kesilen planlar ( kuyu dibi, kuyu üstü, delik planı )
    duvarı kesintisiz alır:  False.
    duvar_boslugu:  ön duvarın boşluklu olup olmadığı ( verilmezse
    kapi_duzeyi ) — kabin üstü planı kesit kotu kaba boşluğun içinde kalırsa
    boşluklu ister ( kabin_ustu.kapi_gorunusu )."""
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    k, kb, kp = g["kuyu"], g["kabin"], g["kapi"]
    kr, ag = g["kabin_ray"], g["agirlik"]
    G, D = k["genislik"], k["derinlik"]
    ds, dg, don, dar = k["duvar_sol"], k["duvar_sag"], k["duvar_on"], k["duvar_arka"]
    e = []

    #  ── DUVARLAR  ( tarama yalnız duvar kesitinde ) ───────────────────
    #  Ön duvar kat kapısının kaba boşluğunun iki yanındadır ( CG.kaba_bosluk —
    #  giriş görünüşüyle aynı;  duvar boşluğuna monte kapıda kasa da boşluktadır ).
    b0, b1, _ = girdi.kaba_bosluk(g, S)
    bosluklu = kapi_duzeyi if duvar_boslugu is None else duvar_boslugu
    on = (
        [(-ds, -don, b0 + ds, don), (b1, -don, G + dg - b1, don)]
        if bosluklu
        else [(-ds, -don, G + ds + dg, don)]
    )
    for x, y, g_, d_ in on + [(-ds, D, G + ds + dg, dar), (-ds, 0, ds, D), (G, 0, dg, D)]:
        if g_ <= 1e-6:
            continue
        e.append(eleman.dikdortgen("TARAMA", x, y, g_, d_, tip="tarama"))
        e.append(eleman.dikdortgen("KUYU-DUVAR", x, y, g_, d_))
    e.append(eleman.dikdortgen("KUYU-IC", 0, 0, G, D))

    #  ── KAPI:  boşluk · kasa · eşik · kanatlar ───────────────────────
    #  Kat kapısı ünitesi ( kasa + eşik ) montaja göre ya duvar boşluğunda
    #  ( kasa duvarda, eşik kuyuya taşar ) ya da duvarın iç yüzünde durur
    #  ( ünitenin tamamı kuyunun içinde ).  KANATLAR EŞİĞİN ÜSTÜNDEDİR:
    #  kapalı konumda, teleskopikte iki düzlemde ( referans proje kapı detayı ).
    KB = girdi.kapi_bolgesi(g, S)
    x0 = kp["sol_pay"]
    kg = kp["genislik"]
    e.append(eleman.ad(eleman.dikdortgen("KAPI", b0, -don, b1 - b0, don), "kapi_boslugu"))
    for kx0 in (x0 - S["kasa_yan"], x0 + kg):  # kasa yanları
        kasa = eleman.ad(
            eleman.dikdortgen("KAPI", kx0, KB["kasa"][0], S["kasa_yan"], S["kasa_derinlik"]), "kapi_kasasi"
        )
        kasa["bicim"] = parcalar.kasa_bicimi(kasa["x"], kasa["y"], kasa["g"], kasa["d"], kx0 < x0)
        e.append(kasa)
    kat_esigi = eleman.ad(
        eleman.dikdortgen("KAPI", x0, KB["esik"][0], kg, KB["esik"][1] - KB["esik"][0]), "kat_esigi"
    )
    e.append(kat_esigi)
    KT = girdi.kapi_tipi(kp.get("tip"))
    tel = KT["tur"] == "teleskopik"
    n_kanat = KT["kanat"]
    kanat = kg / n_kanat

    def kanatlar(esik0, esik1, ad):
        #  Kapalı kanatlar, her biri kapının kanat sayısı kadarda biri.
        #  Teleskopik:  her kanat ayrı düzlemde ( eşiğin kenarından kanat_esik_payi
        #  içeride, kanat_araligi arayla );  cebe en yakın kanat duvara en yakın
        #  düzlemde ( LiftDesigner 1022 ).  Merkezi:  her yanda yarısı, dıştaki
        #  duvara yakın düzlemde;  2 kanatta tek düzlem eşiğin ortasında.  Elle
        #  açılan kapıda tek kanat.
        orta = (esik0 + esik1) / 2.0 - S["kanat_kalinlik"] / 2.0
        yer = []
        for i in range(n_kanat):
            if tel:
                sira = i if KT["yon"] == "Sol" else n_kanat - 1 - i
            elif KT["duzlem"] > 1:
                sira = i if i < n_kanat // 2 else n_kanat - 1 - i
            else:
                sira = None
            ky0 = orta if sira is None else esik0 + S["kanat_esik_payi"] + sira * S["kanat_araligi"]
            el = eleman.ad(eleman.dikdortgen("KAPI", x0 + i * kanat, ky0, kanat, S["kanat_kalinlik"]), ad)
            #  sac tepsi:  kat kapısının yüzü kata, kabin kapısınınki kabine bakar
            el["bicim"] = parcalar.kanat_bicimi(el["x"], el["y"], el["g"], el["d"], ad == "kat_kanadi")
            e.append(el)
            yer.append(ky0)
        return yer

    def cepler(esik0, esik1, duzlemler, ad):
        #  KANAT CEBİ ( LiftDesigner gibi ):  açılan kanatların durduğu yer —
        #  eşiğin bandında kapının yanında, uçta her kanat düzlemine durdurucu.
        pay = S["kanat_cebi_payi"]
        for c0, c1 in girdi.kanat_cepleri(g, S):
            e.append(eleman.ad(eleman.dikdortgen("KAPI", c0, esik0, c1 - c0, esik1 - esik0), ad))
            uc = c0 if c1 <= x0 + 1e-6 else c1 - pay
            for ky0 in sorted(set(duzlemler)):
                if pay > 0:
                    e.append(
                        eleman.ad(
                            eleman.dikdortgen("KAPI", uc, ky0, pay, S["kanat_kalinlik"]), "kanat_durdurucu"
                        )
                    )

    def esik_bicimi(esik_el, yeni):
        #  EŞİK ( parcalar ):  cebin altından da süren tek parça — eşikle cep
        #  arasında çizgi yok;  her kanat düzleminin kılavuz oluğu, üstündeki
        #  kanadın ve durdurucunun örtmediği yerde görünür.
        kanat_el = [x for x in yeni if x.get("ad") in ("kat_kanadi", "kabin_kanadi")]
        cep_el = [x for x in yeni if x.get("ad") in ("kanat_cebi", "kabin_kanat_cebi")]
        ortu = [
            (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
            for x in yeni
            if x.get("ad") in ("kat_kanadi", "kabin_kanadi", "kanat_durdurucu")
        ]
        merkez = [] if KT["tur"] == "manuel" else [x["y"] + x["d"] / 2.0 for x in kanat_el]
        ex0 = esik_el["x"]
        solda = [c for c in cep_el if abs(c["x"] + c["g"] - ex0) < 1e-6]
        for el, sol_acik, sag_acik in [(esik_el, bool(solda), len(cep_el) > len(solda))] + [
            (c, c not in solda, c in solda) for c in cep_el
        ]:
            el["bicim"] = parcalar.esik_cizgileri(
                el["x"], el["y"], el["g"], el["d"], sol_acik, sag_acik
            ) + parcalar.oluk_cizgileri(el["x"], el["x"] + el["g"], merkez, ortu)

    n0 = len(e)
    kat_kanat = kanatlar(KB["esik"][0], KB["esik"][1], "kat_kanadi")
    cepler(KB["esik"][0], KB["esik"][1], kat_kanat, "kanat_cebi")
    esik_bicimi(kat_esigi, e[n0:])
    #  Açılış yönü oku:  teleskopik kapı hangi yana açılıyorsa o yöne bakar.
    ok_y = kat_kanat[0] + S["kanat_kalinlik"] / 2.0
    if tel:
        sag = KT["yon"] == "Sağ"
        e.append(
            eleman.ok("KAPI", x0 + (kg * 0.65 if sag else kg * 0.35), ok_y, x0 + (kg if sag else 0), ok_y)
        )
    elif KT["tur"] == "manuel" and kapi_duzeyi:
        #  MENTEŞELİ KAPI:  ok yerine açılma simgesi ( ISO 128 / yapı resmi:
        #  açık konum ve çeyrek yay, ince sürekli çizgi ).  Kat kapısı kata
        #  açılır;  menteşe kanadın kat yüzünde, kasanın yanında.  Yan
        #  ( kullanıcı 8 Eki:  "Manuel Sağ sağa açılıyor" ):  kattan bakınca
        #  kanat sağa açılır, menteşe sağda ( DIN 107'nin "sağ"ı da bu );
        #  kattan bakan için sağ, planın +x'idir ( teleskopik "Sağ" da +x'e açılır ).

        sag = KT["yon"] == "Sağ"
        hx, hy = (x0 + kg if sag else x0), kat_kanat[0]
        s = -1.0 if sag else 1.0  # menteşeden kanadın serbest ucuna
        yay = [
            (hx + s * kg * math.cos(math.radians(a)), hy - kg * math.sin(math.radians(a)))
            for a in range(0, 91, 5)
        ]
        acilis = eleman.ad(eleman.dikdortgen("ACILIS", min(hx, hx + s * kg), hy - kg, kg, kg), "kapi_acilisi")
        acilis["bicim"] = [
            {"noktalar": [(hx, hy), (hx, hy - kg)], "kapali": False},
            {"noktalar": yay, "kapali": False},
        ]
        e.append(acilis)
    else:
        e.append(eleman.ok("KAPI", x0 + kg / 2.0, ok_y, x0, ok_y))
        e.append(eleman.ok("KAPI", x0 + kg / 2.0, ok_y, x0 + kg, ok_y))
    #  Kapının iki yanındaki bina duvarı yalnız istenirse çizilir.
    if S["bina_duvari"] > 0:
        for bx0, bg in ((-ds, x0 + ds), (x0 + kg, G - (x0 + kg) + dg)):
            if bg > 0:
                e.append(
                    eleman.dikdortgen(
                        "BINA", bx0, -don - S["bina_duvari"], bg, S["bina_duvari"], tip="tarama_tugla"
                    )
                )

    #  ── KABİN:  pano · şase · kapı mekanizması ───────────────────────
    kx = G / 2.0 + kb["kaciklik_y"]
    ic_on = kb["on_pay"]  # kabin iç ön yüzü
    ky = ic_on + kb["derinlik"] / 2.0
    dis_g = kb["genislik"] + 2 * S["kabin_pano_yan"]
    dis_d = kb["derinlik"] + S["kabin_pano_arka"]
    e.append(
        eleman.ad(eleman.dikdortgen("KABIN", kx - dis_g / 2.0, ic_on, dis_g, dis_d), "kabin_dis")
    )  # kabin dışı
    e.append(
        eleman.dikdortgen("KABIN-IC", kx - kb["genislik"] / 2.0, ic_on, kb["genislik"], kb["derinlik"])
    )  # kabin içi
    #  ŞASE DİKMELERİ her kabin rayında raya açılan U ( parcalar.dikme_bicimi ):
    #  kanatları patenin iki yanından dilin ucunu geçer, sırtı patenin arkasında
    #  ( paten sırta bağlı ).  Zarf kanat ucundan sırtın arkasına;  kabin sırta
    #  değmez ( girdi:  kabin dışı + 2 × sase_dikme < DBG ).  Eskiden kabinin dış
    #  yüzüne yapışık 30'luk bir kutuydu:  patenle arasında 30 mm boşluk kalıyor,
    #  paten havada duruyordu.  Plan ve kesit aynı derinliği kullanır.
    sd = S["sase_dikme_derinlik"]
    sy0 = kr["kapi_arasi"] - sd / 2.0
    yp = S["paten_en"] / 2.0
    for yon, uc in ((-1, kx - kr["arasi"] / 2.0), (+1, kx + kr["arasi"] / 2.0)):
        dikme = eleman.ad(
            eleman.dikdortgen(
                "SASE", uc - yp if yon < 0 else uc - S["sase_dikme"], sy0, yp + S["sase_dikme"], sd
            ),
            "sase_dikme",
        )
        if S["sase_dikme"] > yp:
            dikme["bicim"] = parcalar.dikme_bicimi(uc, kr["kapi_arasi"], sd, yp, S["sase_dikme"] - yp, yon)
        e.append(dikme)
    #  Şase kirişleri:  iki C profil ( parcalar.SASE_PROFIL_ENI — referans proje
    #  50;  8 Eki'ye dek kaynaksız 30 ), iki dikmenin sırtını bağlar.
    k0, k1 = kx - kr["arasi"] / 2.0 + S["sase_dikme"], kx + kr["arasi"] / 2.0 - S["sase_dikme"]
    pe = min(parcalar.SASE_PROFIL_ENI, sd / 2.0)
    for sy in (sy0, sy0 + sd - pe):
        e.append(eleman.ad(eleman.dikdortgen("SASE", k0, sy, k1 - k0, pe), "sase_kiris"))
    e.append(eleman.cizgi("EKSEN", kx, -don - 150, kx, D + dar + 150, tip="eksen"))
    e.append(eleman.cizgi("EKSEN", -ds - 150, ky, G + dg + 150, ky, tip="eksen"))

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
    ag_alt = ag_y - ag["ray_arasi"] / 2.0 - ag["h"]  # ağırlık rayı arkaları
    ag_ust = ag_y + ag["ray_arasi"] / 2.0 + ag["h"]
    for yon, yuz in ((-1, sol_yuz), (+1, sag_yuz)):
        e += [eleman.ad(r, "kabin_ray") for r in _ray_yatay(yuz, ry, kr["b"], kr["h"], yon)]
        arka = yuz + kr["h"] * yon  # rayın duvara bakan yüzü
        if ag_yan == ("Sol" if yon < 0 else "Sağ"):
            kiris_x = arka - S["ara_kiris_en"] if yon < 0 else arka
            e.append(
                eleman.dikdortgen(
                    "KONSOL",
                    kiris_x,
                    ag_alt - S["konsol_agirlik_boy"] / 2.0,
                    S["ara_kiris_en"],
                    ag_ust - ag_alt + S["konsol_agirlik_boy"],
                    ad="ara_kiris",
                )
            )
            #  ara kiriş = ağırlık çerçevesinin kabin tarafındaki boyuna profili
            #  ( LiftDesigner K431 );  kabin rayı ona tırnakla bağlı
            e += _tirnaklar(arka, ry, kr["b"], kr["h"], -yon, yatay=True)
        else:
            #  konsol:  duvara dayanan plaka  ( boşluğu doldurmaz )
            duvar_x = 0 if yon < 0 else G
            kx0 = duvar_x - S["konsol_kabin_en"] if yon > 0 else duvar_x
            plaka = eleman.dikdortgen(
                "KONSOL",
                kx0,
                ry - S["konsol_kabin_boy"] / 2.0,
                S["konsol_kabin_en"],
                S["konsol_kabin_boy"],
                ad="plaka",
            )
            e.append(plaka)
            for cy in (ry - S["konsol_civata_araligi"], ry + S["konsol_civata_araligi"]):
                e.append(
                    eleman.daire(
                        "CIVATA", kx0 + S["konsol_kabin_en"] / 2.0, cy, S["konsol_civata_capi"] / 2.0
                    )
                )
            #  KONSOL KOLU:  plakayı rayın arkasına bağlar ( zarf — mantık ).
            #  ÇİZİLEN:  duvar konsolu + ray konsolu ( parcalar.konsol_cifti_bicimi ),
            #  plakanın ve kolun kapsadığı dikdörtgende ( duvardan ray arkasına,
            #  plakanın boyunca ).  Kolun zarfı dar kalır:  geniş zarfta kuyu dibi
            #  gergi kasnağı ( ray ortasına hizalı, ray arkasından 1,5 mm taşar )
            #  konsolla "çakışıyor" sayılıyordu — gergi raya bağlıdır, arkasına geçmez.
            kol_bas = min(arka, kx0 + S["konsol_kabin_en"]) if yon < 0 else min(arka, kx0)
            kol_son = max(arka, kx0 + S["konsol_kabin_en"]) if yon < 0 else max(arka, kx0)
            cift = parcalar.konsol_cifti_bicimi(duvar_x, arka, ry, S["konsol_kabin_boy"], kr["b"])
            if kol_son - kol_bas > 1:
                kol = eleman.dikdortgen(
                    "KONSOL",
                    kol_bas,
                    ry - S["konsol_kabin_boy"] / 6.0,
                    kol_son - kol_bas,
                    S["konsol_kabin_boy"] / 3.0,
                    ad="kol",
                )
                #  biçim kolda, plaka çizilmez
                kol["bicim"], plaka["bicim"] = cift, []
                e.append(kol)
            else:
                plaka["bicim"] = cift
            #  TIRNAKLAR:  rayın tabanını ray konsolunun dik ayağına bastırır
            e += _tirnaklar(arka, ry, kr["b"], kr["h"], -yon, parcalar.konsol_tipi(kr["b"])[3], yatay=True)
        #  paten:  ray yüzünü kavrar ( U kesiti dilin üstünde — parcalar.paten_bicimi )
        paten = eleman.dikdortgen(
            "PATEN", yuz - S["paten_en"] / 2.0, ry - S["paten_boy"] / 2.0, S["paten_en"], S["paten_boy"]
        )
        k_dil = parcalar.ray_dil_kalinligi(kr["b"], kr["h"])
        if k_dil is not None:
            paten["bicim"] = parcalar.paten_bicimi(
                paten["x"], paten["y"], paten["g"], paten["d"], yuz, k_dil, yon, yatay=True
            )
        e.append(paten)
    e.append(eleman.cizgi("EKSEN", -ds - 150, ry, G + dg + 150, ry, tip="eksen"))

    #  ── ASKI DÜZENİ  ( kullanıcı seçer:  kabin altı · kabin üstü · doğrudan )
    #  Kasnakların ve askı noktalarının yeri GİRDİDEN gelir;  koda gömülmez.
    aski = g.get("aski") or {}
    duzen = aski.get("duzen")
    aski_y = (
        ic_on
        + dis_d / 2.0
        + aski.get("kasnak_kaciklik" if duzen in ("Kabin altı", "Kabin üstü") else "nokta_kaciklik", 0)
    )
    aski_yari = 0.0  # askı elemanının derinlikteki yarı boyu

    capraz = arka_aski.geometri(g, S) if arka_aski.arkada_iki_bir(g) else None
    if capraz is not None and "P" in capraz:
        #  ARKADAKİ AĞIRLIKLA 2:1 ( kabin üstü, çapraz — arka_aski ):  kasnaklar
        #  P–H düzleminde;  planda döndürülmüş dikdörtgen ( kenarları çizgi ),
        #  düzlem kesik eksen, iki düşey halat noktası.
        dc = aski["kasnak_capi"]
        for merkez, iz in zip(capraz["kasnaklar"], capraz["izler"]):
            for p0, p1 in zip(iz, iz[1:] + iz[:1]):
                e.append(eleman.ad(eleman.cizgi("KASNAK", p0[0], p0[1], p1[0], p1[1]), "kabin_kasnak_capraz"))
            e.append(
                eleman.ad(
                    eleman.yazi(
                        merkez[0] + capraz["n"][0] * 110, merkez[1] + capraz["n"][1] * 110, f"ø {dc:g}", 45
                    ),
                    "kabin_kasnak_yazi",
                )
            )
        (px, py), (hx, hy) = capraz["P"], capraz["H"]
        e.append(eleman.ad(eleman.cizgi("EKSEN", px, py, hx, hy, tip="eksen"), "aski_duzlemi"))
        #  İki satır:  tek satırda kabinden genişti, iki ucu kabin duvarlarının
        #  üstüne düşüyordu ( 450 kg arka ağırlık — 5 Eki )
        e.append(
            eleman.ad(
                eleman.yazi(capraz["cx"], capraz["cy"] - 230, f"ASKI:  {eleman.buyuk(duzen)}  ·  2:1", 44),
                "aski_yazi",
            )
        )
        e.append(
            eleman.ad(
                eleman.yazi(
                    capraz["cx"], capraz["cy"] - 230 - 1.4 * eleman.yb(44), f"ÇAPRAZ {capraz['aci']:.0f}°", 44
                ),
                "aski_yazi",
            )
        )
    elif duzen in ("Kabin altı", "Kabin üstü"):
        dc, aralik = aski["kasnak_capi"], aski["kasnak_arasi"]
        aski_yari = S["kabin_kasnak_genislik"] / 2.0
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(
                eleman.ad(
                    eleman.dikdortgen("KASNAK", merkez - dc / 2.0, aski_y - aski_yari, dc, 2 * aski_yari),
                    "kabin_kasnak",
                )
            )
            e.append(
                eleman.ad(eleman.yazi(merkez, aski_y + aski_yari + 45, f"ø {dc:g}", 45), "kabin_kasnak_yazi")
            )
        e.append(
            eleman.ad(
                eleman.yazi(kx, aski_y - aski_yari - 230, f"ASKI:  {eleman.buyuk(duzen)}  ·  2:1", 44),
                "aski_yazi",
            )
        )
    elif duzen == "Doğrudan":
        #  1:1:  halatlar kabin şasesinin üst kirişinin ortasındaki TEK
        #  bağlantıda biter ( tek tahrik kasnağı — LiftDesigner 12744-3 );  kiriş
        #  ray ekseni üstündedir, kaçıklık hesabın xs'idir.
        aski_yari = 45.0
        e.append(eleman.ad(eleman.daire("KASNAK", kx, aski_y, 45), "aski_nokta"))
        e.append(eleman.ad(eleman.cizgi("KASNAK", kx - 70, aski_y, kx + 70, aski_y), "aski_nokta"))
        e.append(eleman.ad(eleman.cizgi("KASNAK", kx, aski_y - 70, kx, aski_y + 70), "aski_nokta"))
        e.append(
            eleman.ad(eleman.yazi(kx, aski_y - aski_yari - 230, "ASKI:  DOĞRUDAN  ·  1:1", 44), "aski_yazi")
        )

    e += makine.plan(
        baglantilar.kasnak_tasiyicilari(g, S, -S["kabin_kasnak_derinlik"]),
        eleman.dikdortgen,
        eleman.daire,
        eleman.cizgi,
    )

    #  ── KARŞI AĞIRLIK:  çerçeve · dolgu · kasnak · raylar ────────────
    cer = S["agirlik_cerceve"]
    if ag_yan:
        sol = ag_yan == "Sol"
        ex = ag["ray_duvar"] if sol else G - ag["ray_duvar"]  # ağırlık ekseni
        ax, ay = ex - ag["derinlik"] / 2.0, ag_y - ag["genislik"] / 2.0
        e.append(
            eleman.ad(eleman.dikdortgen("AGIRLIK", ax, ay, ag["derinlik"], ag["genislik"]), "agirlik_blok")
        )
        e.append(
            eleman.dikdortgen(
                "AGIRLIK", ax + cer, ay + cer, ag["derinlik"] - 2 * cer, ag["genislik"] - 2 * cer
            )
        )
        #  Kabin rayının ara kirişi bu konsollara bağlanır:  kol plakadan
        #  kirişe uzanır  ( ağırlığın boyunun DIŞINDAN geçer ).
        kiris_ic = (sol_yuz - kr["h"] - S["ara_kiris_en"]) if sol else (sag_yuz + kr["h"] + S["ara_kiris_en"])
        #  KONSOL ÇERÇEVESİ ( LiftDesigner gibi — parcalar.CERCEVE_PROFILI ):  her
        #  ağırlık rayı, tabanının dış yanındaki ray profiline dayanır;  profil
        #  duvardan ara kirişe uzanır.  Zarflar ( plaka, kol ) mantık içindir,
        #  değişmedi;  çizilen profil ikisinin kapsadığı dikdörtgende.  Plakanın
        #  eski cıvata daireleri kalktı:  bağlantıyı tırnaklar gösterir.
        pr = parcalar.CERCEVE_PROFILI
        duvar_x = 0 if sol else G
        dis_uclar = []
        for yuz, y_yon in ((ag_y + ag["ray_arasi"] / 2.0, +1), (ag_y - ag["ray_arasi"] / 2.0, -1)):
            e += [eleman.ad(r, "agirlik_ray") for r in _ray_dusey(yuz, ex, ag["b"], ag["h"], y_yon)]
            e.append(_agirlik_pateni(S, ag, yuz, ex, y_yon, yatay=False))
            plaka_x = duvar_x if sol else duvar_x - S["konsol_agirlik_en"]
            ray_arkasi = yuz + ag["h"] * y_yon
            plaka = eleman.dikdortgen(
                "KONSOL",
                plaka_x,
                ray_arkasi - S["konsol_agirlik_boy"] / 2.0,
                S["konsol_agirlik_en"],
                S["konsol_agirlik_boy"],
                ad="plaka",
            )
            e.append(plaka)
            kol_bas = plaka_x + S["konsol_agirlik_en"] if sol else kiris_ic
            kol_son = kiris_ic if sol else plaka_x
            profil = parcalar.profil_bicimi(duvar_x, kiris_ic, ray_arkasi, ray_arkasi + y_yon * pr)
            if kol_son - kol_bas > 1:
                kol = eleman.dikdortgen(
                    "KONSOL",
                    kol_bas,
                    ray_arkasi - S["konsol_agirlik_boy"] / 6.0,
                    kol_son - kol_bas,
                    S["konsol_agirlik_boy"] / 3.0,
                    ad="kol",
                )
                kol["bicim"], plaka["bicim"] = profil, []
                e.append(kol)
            else:
                plaka["bicim"] = profil
            e += _tirnaklar(ray_arkasi, ex, ag["b"], ag["h"], -y_yon, yatay=False)
            dis_uclar.append(ray_arkasi + y_yon * pr)
        #  Duvar profili ( K431 ):  ağırlık ile duvar arasında profil ve çakışma
        #  payı kadar yer varsa;  yoksa yalnız ray profilleri ( 4815-6 ).
        bosluk = ax if sol else G - (ax + ag["derinlik"])
        if bosluk >= pr + girdi.ASGARI_ACIKLIK:
            plaka["bicim"] = plaka["bicim"] + parcalar.profil_bicimi(
                duvar_x, duvar_x + (pr if sol else -pr), min(dis_uclar), max(dis_uclar)
            )
        if ag.get("kasnak_capi"):
            dc = ag["kasnak_capi"]
            e.append(
                eleman.ad(
                    eleman.dikdortgen(
                        "KASNAK",
                        ex - ag["derinlik"] / 2.0 + cer,
                        ag_y - dc / 2.0,
                        ag["derinlik"] - 2 * cer,
                        dc,
                    ),
                    "agirlik_kasnak",
                )
            )
            e.append(eleman.ad(eleman.yazi(ex, ag_y, f"ø {dc:g}", 40, aci=90), "agirlik_kasnak_yazi"))
    else:
        ey = D - ag["ray_duvar"]
        ex = G / 2.0
        ax, ay = G / 2.0 - ag["genislik"] / 2.0, ey - ag["derinlik"] / 2.0
        e.append(
            eleman.ad(eleman.dikdortgen("AGIRLIK", ax, ay, ag["genislik"], ag["derinlik"]), "agirlik_blok")
        )
        e.append(
            eleman.dikdortgen(
                "AGIRLIK", ax + cer, ay + cer, ag["genislik"] - 2 * cer, ag["derinlik"] - 2 * cer
            )
        )
        for yuz, x_yon in ((G / 2.0 + ag["ray_arasi"] / 2.0, +1), (G / 2.0 - ag["ray_arasi"] / 2.0, -1)):
            e += [eleman.ad(r, "agirlik_ray") for r in _ray_yatay(yuz, ey, ag["b"], ag["h"], x_yon)]
            e.append(_agirlik_pateni(S, ag, yuz, ey, x_yon, yatay=True))
            #  AĞIRLIK RAYI KONSOLU  ( arka duvar ):  yan yerleşimdeki konsolun
            #  aynısı, 90° dönük — rayın arkasında, duvara dayanır.
            #  ÇİZİLEN ( LiftDesigner K111 ):  rayın tabanının dış yanında çerçevenin
            #  ray profili — duvardan rayın tırnaklarının ötesine ( plakanın zarfı
            #  mantık içindir, değişmedi );  eski cıvata daireleri yerine tırnaklar.
            ray_arkasi = yuz + ag["h"] * x_yon
            plaka_y = D - S["konsol_agirlik_en"]
            plaka = eleman.dikdortgen(
                "KONSOL",
                ray_arkasi - S["konsol_agirlik_boy"] / 2.0,
                plaka_y,
                S["konsol_agirlik_boy"],
                S["konsol_agirlik_en"],
                ad="plaka",
            )
            boy = max(
                S["konsol_agirlik_en"], ag["ray_duvar"] + parcalar.tirnak_uzanimi(ag["b"], ag["h"]) + 10
            )
            plaka["bicim"] = parcalar.profil_bicimi(
                D, D - boy, ray_arkasi, ray_arkasi + x_yon * parcalar.CERCEVE_PROFILI, yatay=False
            )
            e.append(plaka)
            e += _tirnaklar(ray_arkasi, ey, ag["b"], ag["h"], -x_yon, yatay=True)
        #  Duvar profili ( K111 ):  ağırlık ile arka duvar arasında yer varsa
        if ag["ray_duvar"] - ag["derinlik"] / 2.0 >= parcalar.CERCEVE_PROFILI + girdi.ASGARI_ACIKLIK:
            dis = G / 2.0 + ag["ray_arasi"] / 2.0 + ag["h"] + parcalar.CERCEVE_PROFILI
            plaka["bicim"] = plaka["bicim"] + parcalar.profil_bicimi(
                D, D - parcalar.CERCEVE_PROFILI, G - dis, dis, yatay=False
            )
        if ag.get("kasnak_capi"):
            dc = ag["kasnak_capi"]
            e.append(
                eleman.ad(
                    eleman.dikdortgen(
                        "KASNAK", ex - dc / 2.0, ey - ag["derinlik"] / 2.0 + cer, dc, ag["derinlik"] - 2 * cer
                    ),
                    "agirlik_kasnak",
                )
            )
            e.append(eleman.ad(eleman.yazi(ex, ey, f"ø {dc:g}", 40), "agirlik_kasnak_yazi"))

    #  ── KESİTTE GÖRÜNMEYEN ASKI  ( yalnız C-C ) ───────────────────────
    #  Kuyu planı kabinin ortasından kesilir ( kapı yüksekliğinin yarısı ) ve
    #  yukarıdan bakılır:  şasenin dikmeleri kesilir ( düz kalır );  üst kiriş,
    #  kabin üstü kasnaklar ve 1:1 bağlantısı kesitin ÜSTÜNDE ( kaldırılmış ),
    #  alt kiriş, kabin altı kasnaklar ve taşıyıcıları kabin döşemesinin ALTINDA
    #  ( örtülü ):  kesik çizgiyle ( GIZLI ) çizilir, ölçüleri yerinde kalır.
    #  Kabin altı kasnağın kabinin izinin dışına taşan ucu yukarıdan açıktır,
    #  düz çizilir ( halat oradan çıkar ) — LiftDesigner 4815-6'nın kuyu planı ve
    #  referans projenin yatay kesiti de böyle.  Eskiden hepsi düz çiziliyordu:
    #  şase kirişleri ve kasnaklar kabinin içinden geçiyor görünüyordu ( 3 Eki ).
    #  Öbür planlar ( kapi_duzeyi=False ) elemanları adlarıyla kendileri seçer.
    if kapi_duzeyi:
        k0, k1 = kx - dis_g / 2.0, kx + dis_g / 2.0
        for el in list(e):
            if el.get("ad") not in _KESITTE_GIZLI:
                continue
            if el.get("ad") == "kabin_kasnak" and duzen == "Kabin altı":
                for a, b in ((el["x"], min(el["x"] + el["g"], k0)), (max(el["x"], k1), el["x"] + el["g"])):
                    if b - a > 1e-6:
                        e.append(
                            eleman.ad(
                                eleman.dikdortgen("KASNAK", a, el["y"], b - a, el["d"]), "kabin_kasnak_ucu"
                            )
                        )
            el["katman"] = "GIZLI"

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
    #  Kabinin dış yüzleri ( LiftDesigner'ın PLW'si ):  şasenin dikmeleri rayın
    #  ucunda, kabinle ray arasındadır — eskiden "ŞASE DIŞI" kabin + 2 × 30'du,
    #  çizimde karşılığı yoktu.
    ic_sol = kx - dis_g / 2.0
    ic_sag = kx + dis_g / 2.0
    ARA = 200.0  # sıralar arası

    #  ÜST — kuyu genişliği boyunca
    u = [D + dar + 120 + i * ARA for i in range(5)]
    e += [
        eleman.olcu("yatay", (-ds, 0), (0, 0), u[0], f"DUVAR {ds:g}"),
        eleman.olcu("yatay", (0, 0), (G, 0), u[0], f"KUYU GENİŞLİĞİ {G:g}"),
        eleman.olcu("yatay", (G, 0), (G + dg, 0), u[0], f"DUVAR {dg:g}"),
        eleman.olcu("yatay", (-ds, 0), (G + dg, 0), u[1], f"DIŞ ÖLÇÜ {G + ds + dg:g}"),
        eleman.olcu("yatay", (0, 0), (sol_yuz - kr["h"], 0), u[2]),
        eleman.olcu("yatay", (sol_yuz - kr["h"], 0), (sol_yuz, 0), u[2], f"RAY {kr['h']:g}"),
        eleman.olcu("yatay", (sol_yuz, 0), (sag_yuz, 0), u[2], f"DBG {kr['arasi']:g}"),
        eleman.olcu("yatay", (sag_yuz, 0), (sag_yuz + kr["h"], 0), u[2], f"RAY {kr['h']:g}"),
        eleman.olcu("yatay", (sag_yuz + kr["h"], 0), (G, 0), u[2]),
        eleman.olcu("yatay", (ic_sol, 0), (ic_sag, 0), u[3], f"KABİN DIŞI {ic_sag - ic_sol:g}"),
    ]
    #  KABİN İLE KARŞI AĞIRLIK ARASI ( m.5.2.5.5.1 h:  en az 50 — girdi.dogrula ):
    #  yandaki ağırlıkta zincir duvardan ağırlığın çerçevesine, çerçeveye ve
    #  kabinin dış yüzüne ( LiftDesigner 4815-6:  100 · 150 · 225 · PLW ).
    #  Eskiden yalnız duvar – şase ölçülüyordu;  kabin ile ağırlık arası hiçbir
    #  planda yoktu.
    #  Ağırlık kabinle bu yönde ayrık değilse ( ağırlık kabinin önünde ya da
    #  arkasında kalıyor — aralarındaki açıklık derinliktedir ) bölünmez.
    sol_uc, sag_uc = [0.0, ic_sol], [ic_sag, G]
    if ag_yan:
        bx0, bx1 = ex - ag["derinlik"] / 2.0, ex + ag["derinlik"] / 2.0
        if ag_yan == "Sol" and bx1 <= ic_sol:
            sol_uc = [0.0, bx0, bx1, ic_sol]
        elif ag_yan == "Sağ" and bx0 >= ic_sag:
            sag_uc = [ic_sag, bx0, bx1, G]
    for uc in (sol_uc, sag_uc):
        e += [eleman.olcu("yatay", (a, 0), (b, 0), u[3]) for a, b in zip(uc, uc[1:]) if b - a > 1e-6]
    if not ag_yan:
        #  Arkadaki ağırlığın rayları kuyu genişliği boyunca ölçülür
        e += [
            eleman.olcu("yatay", (0, 0), (ex - ag["ray_arasi"] / 2.0, 0), u[4]),
            eleman.olcu(
                "yatay",
                (ex - ag["ray_arasi"] / 2.0, 0),
                (ex + ag["ray_arasi"] / 2.0, 0),
                u[4],
                f"DBGW {ag['ray_arasi']:g}",
            ),
            eleman.olcu("yatay", (ex + ag["ray_arasi"] / 2.0, 0), (G, 0), u[4]),
        ]

    #  ALT — kapı zinciri, kuyu genişliği, kabin ve ağırlık eksenleri
    #  ( menteşeli kapının açılma yayının da altında )
    alt = min([-don - S["bina_duvari"]] + [el["y"] for el in e if el.get("ad") == "kapi_acilisi"])
    a1, a2, a3 = alt - 120, alt - 320, alt - 520
    kasa = S["kasa_yan"]
    e += [
        eleman.olcu("yatay", (0, 0), (x0 - kasa, 0), a1),
        eleman.olcu("yatay", (x0 - kasa, 0), (x0, 0), a1, f"KASA {kasa:g}"),
        eleman.olcu("yatay", (x0, 0), (x0 + kg, 0), a1, f"KAPI {kg:g} x {kp.get('yukseklik', 2100):g}"),
        eleman.olcu("yatay", (x0 + kg, 0), (x0 + kg + kasa, 0), a1, f"KASA {kasa:g}"),
        eleman.olcu("yatay", (x0 + kg + kasa, 0), (G, 0), a1),
        eleman.olcu("yatay", (0, 0), (G, 0), a2, f"KUYU GENİŞLİĞİ {G:g}"),
    ]
    noktalar = sorted(set([0.0, kx, G] + ([ex] if ag_yan else [])))
    for sol_n, sag_n in zip(noktalar, noktalar[1:]):
        metin = None
        if (ag_yan == "Sol" and sol_n == 0 and sag_n == ex) or (
            ag_yan == "Sağ" and sol_n == ex and sag_n == G
        ):
            metin = f"AĞIRLIK RAYI {sag_n - sol_n:g}"
        e.append(eleman.olcu("yatay", (sol_n, 0), (sag_n, 0), a3, metin))

    #  YANLAR — kuyu derinliği boyunca.  Sıra listesi duvardan dışarı
    #  doğrudur;  ağırlık yandaysa kendi zinciri O YANDA, duvara en yakın
    #  sırada durur  ( konsol kotları ağırlığın yanında okunur ).
    def _agirlik_zinciri(kot):
        return [
            eleman.olcu("dusey", (0, 0), (0, ag_alt), kot),
            eleman.olcu("dusey", (0, ag_alt), (0, ag_alt + ag["h"]), kot, f"{ag['h']:g}"),
            eleman.olcu(
                "dusey", (0, ag_alt + ag["h"]), (0, ag_ust - ag["h"]), kot, f"DBGW {ag['ray_arasi']:g}"
            ),
            eleman.olcu("dusey", (0, ag_ust - ag["h"]), (0, ag_ust), kot, f"{ag['h']:g}"),
            eleman.olcu("dusey", (0, ag_ust), (0, D), kot),
        ]

    def _civata(kot):
        #  Kabin rayı konsolunun cıvata aralığı — duvara dayanan konsolda
        c = S["konsol_civata_araligi"]
        return [
            eleman.olcu("dusey", (0, ry - c), (0, ry), kot, f"CIVATA {c:g}"),
            eleman.olcu("dusey", (0, ry), (0, ry + c), kot, f"{c:g}"),
        ]

    sol_siralar = []
    sag_siralar = []
    if ag_yan == "Sol":
        sol_siralar.append(_agirlik_zinciri)
    elif ag_yan == "Sağ":
        sag_siralar.append(_agirlik_zinciri)
    (sol_siralar if ag_yan == "Sağ" else sag_siralar).insert(0, _civata)
    #  Arkadaki ağırlıkta derinlik zincirleri ağırlığa bölünür ( LiftDesigner
    #  800 KG:  ray ekseni 850 · kabin rayı – ağırlık rayı 970 · 180 ve
    #  kabin – ağırlık 100 · 150 · 105 ):  kabin rayı ile ağırlık rayı arası ve
    #  kabin ile ağırlık arası ( m.5.2.5.5.1 h ) hiçbir planda ölçülmüyordu.
    ray_uc, kabin_uc = [ry, D], [ic_on + dis_d, D]
    if not ag_yan:
        ey = D - ag["ray_duvar"]
        if ey > ry:
            ray_uc = [ry, ey, D]
        if ey - ag["derinlik"] / 2.0 >= ic_on + dis_d:
            kabin_uc = [ic_on + dis_d, ey - ag["derinlik"] / 2.0, ey + ag["derinlik"] / 2.0, D]

    def _parcalar(uc, kot, ilk_metin=None):
        #  Kısa parçalar yazısız ( yalnız sayı ):  uzun ad parçaya sığmayıp
        #  dışarı taşıyor, duvarın ölçüsüne biniyordu.
        out = [eleman.olcu("dusey", (0, a), (0, b), kot) for a, b in zip(uc, uc[1:])]
        if ilk_metin and len(uc) > 2:
            out[0] = eleman.olcu("dusey", (0, uc[0]), (0, uc[1]), kot, ilk_metin)
        return out

    sol_siralar += [
        lambda kot: (
            [eleman.olcu("dusey", (0, 0), (0, ry), kot, f"RAY EKSENİ {ry:g}")]
            + _parcalar(ray_uc, kot, f"KABİN RAYI – AĞIRLIK RAYI {ray_uc[1] - ry:g}")
        ),
        lambda kot: [eleman.olcu("dusey", (0, -don), (0, D + dar), kot, f"DIŞ ÖLÇÜ {D + don + dar:g}")],
    ]
    sag_siralar += [
        #  Ön ve arka duvar da ölçülür ( üstteki sol · sağ duvar gibi ):  ölçüye
        #  tıklanınca yalnız o duvarın kalınlığı değişir ( 2 Eki ).
        lambda kot: [
            eleman.olcu("dusey", (0, -don), (0, 0), kot, f"DUVAR {don:g}"),
            eleman.olcu("dusey", (0, 0), (0, D), kot, f"KUYU DERİNLİĞİ {D:g}"),
            eleman.olcu("dusey", (0, D), (0, D + dar), kot, f"DUVAR {dar:g}"),
        ],
        lambda kot: [
            eleman.olcu("dusey", (0, ic_on), (0, ic_on + kb["derinlik"]), kot, f"KABİN {kb['derinlik']:g}")
        ],
        lambda kot: (
            [
                eleman.olcu("dusey", (0, 0), (0, ic_on), kot, f"KAPI ARASI {ic_on:g}"),
                eleman.olcu("dusey", (0, ic_on), (0, ic_on + dis_d), kot, f"KABİN + ŞASE {dis_d:g}"),
            ]
            + _parcalar(kabin_uc, kot)
        ),
    ]
    #  EŞİKLER  ( kat eşiği · aradaki açıklık · kabin eşiği ):  sağdaki dış
    #  sıralarda, "KAPI ARASI"nın hemen içinde ( o aralığı böler — LiftDesigner'ın
    #  kuyu planı da eşikleri "190 · 10 · 90 · 30" diye dışarıda ölçer ).
    #  Eskiden kapının yanındaki şeritteydi:  kanat cepleri, kasa ve ara kiriş o
    #  şeridi doldurunca yazılar onların üstüne düşüyordu ( girdi taraması, 4 Eki );
    #  şerit varsa içeride, yoksa dışarıda koymak da olmadı — girdi oynayınca yer
    #  değiştiriyor, ölçüye tıklayınca kaynağı bulunamıyordu.
    #  İç yüzden kapı hattına:  duvar boşluğuna montajda kat eşiğinin taşan
    #  kısmı, kuyu içine montajda kat kapısı ünitesinin tamamı.
    hat_metni = (
        f"KAT EŞİĞİ {KB['hat']:g}" if kp["montaj"] == "Duvar boşluğuna" else f"KAT KAPISI {KB['hat']:g}"
    )
    esik = [
        (0.0, KB["hat"], hat_metni),
        (KB["hat"], KB["kabin_esik"][0], None),
        (
            KB["kabin_esik"][0],
            KB["kabin_esik"][1],
            f"KABİN EŞİĞİ {KB['kabin_esik'][1] - KB['kabin_esik'][0]:g}",
        ),
    ]
    sag_siralar.insert(
        len(sag_siralar) - 1,
        lambda kot: [
            eleman.olcu("dusey", (0, bas), (0, son), kot, metin or f"{son - bas:g}")
            for bas, son, metin in esik
        ],
    )

    for i, sira in enumerate(sol_siralar):
        e += sira(-ds - 120 - i * ARA)
    for i, sira in enumerate(sag_siralar):
        e += sira(G + dg + 120 + i * ARA)

    #  İÇ — kabin iç genişliği ve panoları  ( kabinin arkasında;  ağırlık
    #  arkadaysa o şerit dolu olduğu için kabinin içinde, önde ).  Duvar – kabin
    #  dışı parçaları yok:  üstteki sırada ( KABİN DIŞI zinciri ) zaten ölçülü —
    #  ISO 129-1, her ölçü bir kez.  8 Eki'ye dek buradaydılar;  ağırlık patenleri
    #  planda çizilince duvar – kabin yazısı yandaki ağırlıkta sığacak yer
    #  bulamıyor, iki kat dışarı itiliyordu.
    #  Arkadaki şerit yazıya yetmiyorsa ( referans proje:  147 mm ) kabinin içinde,
    #  arka panelin önünde durur — yazı arka duvara taşıyordu.
    arka_serit = D - (ic_on + dis_d)
    if not ag_yan:
        kab_kot = ic_on + 150
    elif arka_serit >= 90 + 50 + eleman.OLCU_YAZI / 2.0 + 40:
        kab_kot = ic_on + dis_d + 90
    else:
        kab_kot = ic_on + dis_d - 200
    e += [
        eleman.olcu("yatay", (ic_sol, 0), (kx - kb["genislik"] / 2.0, 0), kab_kot),
        eleman.olcu(
            "yatay",
            (kx - kb["genislik"] / 2.0, 0),
            (kx + kb["genislik"] / 2.0, 0),
            kab_kot,
            f"KABİN İÇİ {kb['genislik']:g}",
        ),
        eleman.olcu("yatay", (kx + kb["genislik"] / 2.0, 0), (ic_sag, 0), kab_kot),
    ]

    #  İÇ — ASKI:  kasnak / nokta aralığı askı elemanlarının hemen yanında,
    #  kaçıklık ise kabin merkezi ile askı ekseni arasında
    if duzen in ("Kabin altı", "Kabin üstü", "Doğrudan") and capraz is None:
        arasi = None
        if duzen != "Doğrudan":  # 1:1'de tek bağlantı:  aralık yok
            aralik = aski.get("kasnak_arasi")
            arasi = eleman.olcu(
                "yatay",
                (kx - aralik / 2.0, 0),
                (kx + aralik / 2.0, 0),
                aski_y - aski_yari - 70,
                f"ASKI ARASI {aralik:g}",
                yazi={"x": kx, "y": aski_y - aski_yari - 70 + 50, "aci": 0},
            )
            e.append(arasi)
        kac = aski_y - (ic_on + dis_d / 2.0)
        if abs(kac) > 1e-9:
            kac_x = kx - kb["genislik"] / 2.0 + 150
            metin = f"ASKI KAÇIKLIĞI {abs(kac):g}"
            w_kac, h_ = eleman.yazi_eni(metin), eleman.OLCU_YAZI
            yazi = {"x": kac_x + 30 + w_kac / 2.0, "y": (aski_y + ic_on + dis_d / 2.0) / 2.0, "aci": 0}
            #  Kaçıklık küçükken iki yazı aynı yüksekliğe düşüyordu ( girdi
            #  taraması, 4 Eki ):  önce ASKI ARASI kendi ölçüsünün içinde sağa
            #  kayar, sığmazsa kaçıklığın yazısı ölçünün üst ucunun üstüne çıkar.
            if arasi is not None:
                ay = arasi["yazi"]
                w_ar = eleman.yazi_eni(arasi["metin"])
                ust_uste = abs(ay["y"] - yazi["y"]) < h_ and abs(ay["x"] - yazi["x"]) < (w_ar + w_kac) / 2.0
                if ust_uste:
                    c = yazi["x"] + w_kac / 2.0 + 20 + w_ar / 2.0
                    if c + w_ar / 2.0 <= kx + aralik / 2.0:
                        ay["x"] = c
                    else:
                        yazi["y"] = max(aski_y, ic_on + dis_d / 2.0) + 25 + h_ / 2.0
            e.append(eleman.olcu("dusey", (0, aski_y), (0, ic_on + dis_d / 2.0), kac_x, metin, yazi=yazi))

    #  ── YAZILAR ──────────────────────────────────────────────────────
    kabin_esigi = eleman.ad(
        eleman.dikdortgen("KABIN", x0, KB["kabin_esik"][0], kg, KB["kabin_esik"][1] - KB["kabin_esik"][0]),
        "kabin_esigi",
    )
    e.append(kabin_esigi)
    n0 = len(e)
    cepler(
        KB["kabin_esik"][0],
        KB["kabin_esik"][1],
        kanatlar(KB["kabin_esik"][0], KB["kabin_esik"][1], "kabin_kanadi"),
        "kabin_kanat_cebi",
    )
    esik_bicimi(kabin_esigi, e[n0:])
    #  Kabin kapısı mekanizma kutusu KABİN ÖN YÜZÜNDE durur  ( kapı ile kabin
    #  arasında;  kullanıcı kararı — referans projenin paftasındaki yerleşimin aynısı ).
    #  Kapı elemanlarından SONRA:  kanatların örtüsü onu silmesin.
    #  KESİK:  kutu kabin kapısının üstündedir, planın kesit düzleminin ( kapı
    #  hizası ) üstünde kalır — kesitin üstündeki parça kesik çizilir ( ISO 128;
    #  kullanıcı onayı 6 Eki ).  Eskiden düz çiziliyordu, eşiklerin ve kanatların
    #  üstünden geçen bir kutu gibi duruyordu.
    e.append(
        eleman.ad(
            eleman.dikdortgen(
                "GIZLI",
                x0 + kg / 2.0 - S["kabin_kapisi_kutu_en"] / 2.0,
                ic_on - S["kabin_kapisi_kutu_boy"] + 20,
                S["kabin_kapisi_kutu_en"],
                S["kabin_kapisi_kutu_boy"],
            ),
            "kabin_kapisi_operatoru",
        )
    )
    #  Askı noktaları kabin ortasına yakınsa kabin yazısı arkaya kayar.
    kabin_yazi_y = ky if abs(aski_y - ky) >= 150 else ky + 200
    e.append(
        eleman.ad(
            eleman.yazi(kx, kabin_yazi_y, f"KABİN  {kb['genislik']:g} x {kb['derinlik']:g}", 55), "kabin_yazi"
        )
    )
    #  Ölçü zincirlerinin sıfır noktaları  ( referans projede de "0" yazar )
    for zx in (0, G):
        e.append(eleman.yazi(zx, alt - 420, "0", 45))
    if ag_yan:
        #  Blok dar ve uzun:  yazı DİK yazılır.  Kasnak bloğun ortasında
        #  durduğu için yazı blok ile kabin rayı arasındaki boşluğa konur;
        #  boşluk dar ise bloğun içine.
        blok_ic = ex + ag["derinlik"] / 2.0 if ag_yan == "Sol" else ex - ag["derinlik"] / 2.0
        bos = abs(kiris_ic - blok_ic)
        yx = (blok_ic + kiris_ic) / 2.0 if bos >= 60 else ex
        metin = "KARŞI AĞIRLIK"
        if bos < 60:
            #  Yazı bloğun içinde, kasnağın çap yazısıyla aynı yerde:  ikisi tek
            #  yazı olur ( eskiden üst üste biniyordu )
            cap = [x for x in e if x.get("ad") == "agirlik_kasnak_yazi"]
            if cap:
                metin += "  " + cap[0]["metin"]
                e.remove(cap[0])
        e.append(eleman.ad(eleman.yazi(yx, ag_y, metin, 40, aci=90), "agirlik_yazi"))
    else:
        e.append(
            eleman.ad(eleman.yazi(ex, ey - ag["derinlik"] / 2.0 - 45, "KARŞI AĞIRLIK", 40), "agirlik_yazi")
        )
    _yazilari_yerlestir(e, kaydir=True)
    #  Kabinin içindeki yazılar dar yerde yarışır ( kasnak çapı, askı yazısı,
    #  kabin yazısı, askı kaçıklığı ):  çakışan, sıradaki boş adaya taşınır
    #  ( girdi taraması, 4 Eki — kaçıklık küçükken ve kabin darken üst üste
    #  biniyorlardı ).
    adaylar = {}
    for el in e:
        ad = el.get("ad")
        if ad == "kabin_kasnak_yazi":
            m = el["x"]
            w = eleman.yazi_eni(el["metin"], el["yukseklik"]) / 2.0
            dc_ = (aski.get("kasnak_capi") or 0) / 2.0
            adaylar[id(el)] = (
                el,
                [
                    (m, el["y"]),
                    (m, aski_y - aski_yari - 45),
                    (m - dc_ - w - 20, aski_y),
                    (m + dc_ + w + 20, aski_y),
                ],
            )
        elif ad == "aski_yazi":
            adaylar[id(el)] = (
                el,
                [
                    (el["x"], el["y"]),
                    (el["x"], aski_y + aski_yari + 230),
                    (el["x"], aski_y - aski_yari - 330),
                ],
            )
        elif ad == "kabin_yazi":
            adaylar[id(el)] = (el, [(kx, el["y"])] + [(kx, ky + d) for d in (200, -200, 350, -350, 500)])
        elif el["tip"] == "olcu" and el["metin"].startswith("ASKI KAÇIKLIĞI"):
            y_ = el["yazi"]
            w = eleman.yazi_eni(el["metin"]) / 2.0
            z0, z1 = sorted((el["a"][1], el["b"][1]))
            k_ = el["kot"]
            #  Bunlar da doluysa çevresinde adım adım ( en yakın önce ):  küçük
            #  kabinde dört yer de şase dikmesine ya da kasnak yazısına düşüyordu
            #  ( yazılar büyüyünce, 5 Eki )
            ek = sorted(
                (
                    (y_["x"] + dx, y_["y"] + dy)
                    for dx in (0, -1, 1, -2, 2, -3, 3)
                    for dy in range(-600, 601, 50)
                    for dx in [dx * (eleman.OLCU_YAZI / 2.0 + 40)]
                ),
                key=lambda a: (a[0] - y_["x"]) ** 2 + (a[1] - y_["y"]) ** 2,
            )
            adaylar[id(el)] = (
                el,
                [
                    (y_["x"], y_["y"]),
                    (k_ - 30 - w, (z0 + z1) / 2.0),
                    (k_ + 30 + w, z1 + 25 + eleman.OLCU_YAZI / 2.0),
                    (k_ + 30 + w, z0 - 25 - eleman.OLCU_YAZI / 2.0),
                ]
                + ek,
            )
    if adaylar:
        _yazilari_coz(e, list(adaylar.values()))
    _parcadan_kaydir(e, ek_katman=("AGIRLIK",))
    e += kesit_isaretleri(g, e)
    return e


def _yazi_kutusu(el):
    """Yazının ( ya da ölçü yazısının ) kutusu."""
    if el["tip"] == "olcu":
        y = el.get("yazi")
        if not y:
            return None
        w, h = (
            eleman.yazi_eni(el["metin"], y.get("h", eleman.OLCU_YAZI)) / 2.0,
            y.get("h", eleman.OLCU_YAZI) / 2.0,
        )
        if y.get("aci"):
            w, h = h, w
        return (y["x"] - w, y["y"] - h, y["x"] + w, y["y"] + h)
    return sinir([el])


#  Yazının üstünden geçebilen çizgiler:  DXF'te ve SVG'de yazı MASKELİDİR
#  ( dxf.MASKE_PAYI · svg.HALE ) — eksen, ölçü, gizli çizgi, alan sınırı,
#  seviye, kesit işareti ve halat ( ince akış çizgisi:  B-B'de kapının önünden
#  geçer, dar kanatlı kapıda durak numarasının konacağı çizgisiz kanat
#  kalmıyordu ) yazının olduğu yerde kesilir ( ISO 128 ).  Öbür katmanlar
#  PARÇA KENARIDIR:  yazı onların üstüne düşerse maske parçanın kenarını
#  siler, düşmemelidir.
MASKELI_KATMANLAR = ("EKSEN", "OLCU", "GIZLI", "SIGINMA", "SEVIYE", "KESIT", "HALAT", "YAZI", "CERCEVE")


def parca_kenarlari(e):
    """Yazının üstünden geçemeyen çizgiler:  [ ( x1, y1, x2, y2 ) ]."""
    out = []
    for el in e:
        t = el["tip"]
        if el.get("katman") in MASKELI_KATMANLAR or t in ("yazi", "olcu", "eksen"):
            continue
        if "bicim" in el:  # gerçek biçim ( parcalar )
            for p in el["bicim"]:
                n = p["noktalar"]
                bas = 0 if p.get("kapali", True) else 1  # açık çizgide kapanış kenarı yok
                out += [(n[i][0], n[i][1], n[i - 1][0], n[i - 1][1]) for i in range(bas, len(n))]
        elif t in ("dikdortgen", "tarama", "tarama_tugla"):
            x, y, g, d = el["x"], el["y"], el["g"], el["d"]
            out += [(x, y, x + g, y), (x + g, y, x + g, y + d), (x, y + d, x + g, y + d), (x, y, x, y + d)]
        elif t in ("cizgi", "ok"):
            out.append((el["x1"], el["y1"], el["x2"], el["y2"]))
        elif t == "daire":
            n, r = 16, el["r"]
            out += [
                (
                    el["x"] + r * math.cos(2 * math.pi * i / n),
                    el["y"] + r * math.sin(2 * math.pi * i / n),
                    el["x"] + r * math.cos(2 * math.pi * (i + 1) / n),
                    el["y"] + r * math.sin(2 * math.pi * (i + 1) / n),
                )
                for i in range(n)
            ]
    return out


def kenar_kesisir(s, kutu, pay=0.0):
    """Doğru parçası kutunun ( pay kadar küçültülmüş ) içinden geçiyor mu."""
    x0, y0, x1, y1 = kutu[0] + pay, kutu[1] + pay, kutu[2] - pay, kutu[3] - pay
    ax, ay, bx, by = s
    if max(ax, bx) <= x0 or min(ax, bx) >= x1 or max(ay, by) <= y0 or min(ay, by) >= y1:
        return False
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True


class KenarIzgarasi:
    """Parça kenarlarının ızgara dizini:  bir kutuya değebilecek kenarlar yalnız
    kutunun düştüğü hücrelerden denenir.  Hesap kuyu planını bir projede
    binlerce kez kurar;  her aday yazı yeri için BÜTÜN kenarları denemek hesap
    testini 163 sn'den 5.486 sn'ye çıkarmıştı ( 5 Eki )."""

    def __init__(self, kenarlar, hucre=200.0):
        self.h, self.d = hucre, {}
        for s_ in kenarlar:
            for i in range(int(min(s_[0], s_[2]) // hucre), int(max(s_[0], s_[2]) // hucre) + 1):
                for j in range(int(min(s_[1], s_[3]) // hucre), int(max(s_[1], s_[3]) // hucre) + 1):
                    self.d.setdefault((i, j), []).append(s_)

    def kesisir(self, kutu, pay=0.0):
        h = self.h
        for i in range(int(kutu[0] // h), int(kutu[2] // h) + 1):
            for j in range(int(kutu[1] // h), int(kutu[3] // h) + 1):
                for s_ in self.d.get((i, j), ()):
                    if kenar_kesisir(s_, kutu, pay):
                        return True
        return False


#  Türkçe ondalık ayırıcı virgüldür:  yalnız tek noktalı sayılar ( "1022.5" ,
#  "+21.00" );  madde numaraları ( "m.5.2.6.3.2.4" ) değişmez.
_ONDALIK = re.compile(r"(?<![\d.,])(\d+)\.(\d+)(?![\d.])")


def ondalik_virgul(e):
    """SON ADIM ( cizimler.CIZIMLER ):  yazılardaki ve ölçülerdeki ondalık nokta
    virgül olur ( "AĞIRLIK RAYI 127,5", "+21,00" — kullanıcı 5 Eki ).  Ölçü
    kaynağı ( olcu_kaynagi ) sayıyı ikisinde de tanır."""
    for el in e:
        if el.get("metin"):
            el["metin"] = _ONDALIK.sub(r"\1,\2", el["metin"])
    return e


def etiketleri_ayir(e, olcek=20):
    """SON ADIM ( bütün çizimler — cizimler.CIZIMLER ):  başka bir yazıya ( etiket
    ya da ölçü yazısı ) ya da bir PARÇANIN KENARINA ( parca_kenarlari ) binen ya
    da bir DUVARIN ( taramalı kesit ) içinde duran ETİKET, en az kayarak hiçbirine
    binmediği yere taşınır;  yeni yeri eskisinden daha çok parçanın içine
    girmez ( kabinin içinden karşı ağırlığa, karşı ağırlıktan duvara geçmez ).
    300 mm'de ( 1/20;  başka ölçekte oranında ) yer yoksa 900 mm'ye kadar HİÇBİR
    parçanın içinde olmayan en yakın yere konur ve parçasına OKLU ÇİZGİYLE
    bağlanır ( teknik resmin etiket oku );  orada da yoksa yerinde kalır.  Ölçü
    yazıları kıpırdamaz ( ölçüye tıklama onların yerini bilir ).  Yazılar
    büyüyünce ( 5 Eki ) kasnak çapı, gergi, askı etiketleri yer yer bir ölçü
    yazısına biniyordu;  yazılar maskelenince ( 5 Eki ) parçanın üstündeki etiket
    parçanın kenarını siliyordu ( kuyu üstünde HALAT BAĞLANTISI makine
    şasesinin, kabin üstünde HALAT şase kirişinin, dar karşı ağırlığın içinde
    KARŞI AĞIRLIK  ø 400 kasnağın üstünde )."""
    k = olcek / 20.0

    def ust(a, b, pay=4.0):
        return a[0] < b[2] + pay and b[0] < a[2] + pay and a[1] < b[3] + pay and b[1] < a[3] + pay

    #  Parçalar ( etiket içlerine yeniden girmez ) ve duvarlar ( içinde durmaz )
    parca_kutulari = [
        sinir([x])
        for x in e
        if (x["tip"] == "dikdortgen" and x.get("katman") not in MASKELI_KATMANLAR)
        or x["tip"] in ("tarama", "tarama_tugla")
    ]
    duvarlar = [
        sinir([x])
        for x in e
        if x["tip"] in ("tarama", "tarama_tugla")
        or (x["tip"] == "dikdortgen" and x.get("katman") == "KUYU-DUVAR")
    ]
    kenarlar = KenarIzgarasi(parca_kenarlari(e))
    yazilar = [
        x
        for x in e
        if (x["tip"] == "yazi" and x.get("katman") not in ("CERCEVE",))
        or (x["tip"] == "olcu" and x.get("yazi"))
    ]
    kutular = {id(x): _yazi_kutusu(x) for x in yazilar}

    def adimlar_(menzil, adim, ic=0):
        return sorted(
            {
                (dx, dy)
                for dx in range(-menzil, menzil + 1, adim)
                for dy in range(-menzil, menzil + 1, adim)
                if max(abs(dx), abs(dy)) > ic
            },
            key=lambda d: (d[0] ** 2 + d[1] ** 2, abs(d[1])),
        )

    yakin_m, uzak_m = int(300 * k), int(900 * k)
    yakin_adim = adimlar_(yakin_m, max(int(20 * k), 1))
    uzak_adim = adimlar_(uzak_m, max(int(40 * k), 1), yakin_m)
    oklar = []
    for el in yazilar:
        if el["tip"] != "yazi":
            continue
        kb = kutular[id(el)]
        obur = [kutular[id(x)] for x in yazilar if x is not el and kutular[id(x)]]

        def sorunlu(kt, obur=obur):
            return (
                any(ust(kt, b) for b in obur)
                or any(ust(kt, d, -2.0 * k) for d in duvarlar)
                or kenarlar.kesisir(kt, 2.0 * k)
            )

        if not sorunlu(kb):
            continue
        eski_parca = sum(1 for q in parca_kutulari if ust(kb, q, 0.0))
        yer = next(
            (
                (dx, dy)
                for dx, dy in yakin_adim[1:]
                if not sorunlu((kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy))
                and sum(
                    1 for q in parca_kutulari if ust((kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy), q, 0.0)
                )
                <= eski_parca
            ),
            None,
        )
        ok = False
        if yer is None:
            yer = next(
                (
                    (dx, dy)
                    for dx, dy in uzak_adim
                    if not sorunlu((kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy))
                    and not any(
                        ust((kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy), q, 0.0) for q in parca_kutulari
                    )
                ),
                None,
            )
            ok = yer is not None
        if yer is None:
            continue
        dx, dy = yer
        k2 = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
        if ok:
            #  Ok:  etiketin parçaya en yakın noktasından eski yerinin ortasına
            ax, ay = (kb[0] + kb[2]) / 2.0, (kb[1] + kb[3]) / 2.0
            px, py = min(max(ax, k2[0]), k2[2]), min(max(ay, k2[1]), k2[3])
            oklar.append(eleman.ad(eleman.ok("YAZI", px, py, ax, ay), "etiket_oku"))
        el["x"] += dx
        el["y"] += dy
        kutular[id(el)] = k2
    return e + oklar


def _yazilari_coz(e, tasinir, ek_katman=()):
    """tasinir:  [ ( eleman , [ ( x , y ) adayları — ilki şimdiki yer ] ) ].
    Her yazı öbür bütün yazılara ( ölçü yazıları dahil ) binmeyen ilk adaya
    taşınır;  hiçbiri boş değilse yerinde kalır."""

    def kutu_yerde(el, x, y):
        if el["tip"] == "olcu":
            eski = dict(el["yazi"])
            el["yazi"].update(x=x, y=y)
            k = _yazi_kutusu(el)
            el["yazi"].clear()
            el["yazi"].update(eski)
            return k
        eski = (el["x"], el["y"])
        el["x"], el["y"] = x, y
        k = sinir([el])
        el["x"], el["y"] = eski
        return k

    def ortusur(a, b):
        return a[0] < b[2] - 2 and b[0] < a[2] - 2 and a[1] < b[3] - 2 and b[1] < a[3] - 2

    parca_kutulari = [
        sinir([x])
        for x in e
        if x["tip"] == "dikdortgen" and x.get("katman") in PARCA_KATMANLARI + tuple(ek_katman)
    ]
    #  Parça kenarına ( parca_kenarlari ) binmeyen aday önce;  yoksa eskisi gibi
    #  yalnız yazılara ve parçalara binmeyen ilk aday ( yazılar maskeli, 5 Eki )
    kenarlar = KenarIzgarasi(parca_kenarlari(e))
    for el, adaylar in tasinir:
        digerleri = [_yazi_kutusu(x) for x in e if x is not el and x["tip"] in ("yazi", "olcu")]
        digerleri = [k for k in digerleri if k] + parca_kutulari
        secilen = None
        for x, y in adaylar:
            k = kutu_yerde(el, x, y)
            if not any(ortusur(k, d) for d in digerleri):
                secilen = secilen or (x, y)
                if not kenarlar.kesisir(k, 2.0):
                    secilen = (x, y)
                    break
        if secilen:
            if el["tip"] == "olcu":
                el["yazi"].update(x=secilen[0], y=secilen[1])
            else:
                el["x"], el["y"] = secilen


def kesit_duzlemleri(g):
    """A-A düzleminin x'i ( kabin ekseni ) ve B-B düzleminin y'si ( kabinin
    arkası ile arka duvarın ortası )."""
    k, kb = g["kuyu"], g["kabin"]
    arka = kb["on_pay"] + kb["derinlik"] + sabitler.sabitler(g.get("_cizim_sabitleri"))["kabin_pano_arka"]
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
    if not (
        (
            ag.get("yeri") in ("Sol", "Sağ")
            and (duzen in ("Kabin altı", "Kabin üstü") or (duzen == "Doğrudan" and md_))
        )
        or (ag.get("yeri") == "Arka" and duzen == "Doğrudan" and md_)
    ) or (g.get("makine") or {}).get("yeri") not in ("Kuyu üstü", "Makine dairesi"):
        return []
    x1, y1, x2, y2 = sinir(e)
    kx, yb = kesit_duzlemleri(g)
    yon_a = -1.0 if ag["yeri"] == "Sol" else 1.0
    L, O, P = 300.0, 260.0, 150.0
    cikti = []
    for harf, (px, py), (dx, dy), (ox, oy) in (
        ("A", (kx, y2 + P), (0, 1), (yon_a, 0)),
        ("A", (kx, y1 - P), (0, -1), (yon_a, 0)),
        ("B", (x1 - P, yb), (-1, 0), (0, -1)),
        ("B", (x2 + P, yb), (1, 0), (0, -1)),
    ):
        cikti.append(eleman.ad(eleman.cizgi("KESIT", px, py, px + dx * L, py + dy * L), "kesit_isareti"))
        tx, ty = px + dx * L / 2.0, py + dy * L / 2.0
        cikti.append(eleman.ok("KESIT", tx, ty, tx + ox * O, ty + oy * O))
        cikti.append(eleman.ad(eleman.yazi(tx + ox * (O + 90), ty + oy * (O + 90), harf, 90), "kesit_harfi"))
    return cikti


def sinir(elemanlar, pay=0.0):
    """Elemanların kapsayan dikdörtgeni  ( x1, y1, x2, y2 )."""
    xs, ys = [], []
    for el in elemanlar:
        if el["tip"] in ("dikdortgen", "tarama"):
            xs += [el["x"], el["x"] + el["g"]]
            ys += [el["y"], el["y"] + el["d"]]
        elif el["tip"] in ("cizgi", "eksen", "ok"):
            xs += [el["x1"], el["x2"]]
            ys += [el["y1"], el["y2"]]
        elif el["tip"] == "daire":
            xs += [el["x"] - el["r"], el["x"] + el["r"]]
            ys += [el["y"] - el["r"], el["y"] + el["r"]]
        elif el["tip"] == "olcu":
            if el["yon"] == "yatay":
                xs += [el["a"][0], el["b"][0]]
                ys += [el["kot"]]
            else:
                ys += [el["a"][1], el["b"][1]]
                xs += [el["kot"]]
            y_ = el.get("yazi")
            if y_:
                #  Yazı da çerçevenin içinde kalmalı  ( "ASKI KAÇIKLIĞI"
                #  çerçeveye taşıp kesiliyordu ).
                w, h = eleman.yazi_eni(el["metin"], y_["h"]) / 2.0, y_["h"] / 2.0
                if y_["aci"]:
                    w, h = h, w
                xs += [y_["x"] - w, y_["x"] + w]
                ys += [y_["y"] - h, y_["y"] + h]
        elif el["tip"] == "yazi":
            #  Yazının eni de:  sola hizalı bir tablo satırı çerçeveden taşıyordu
            w, h = eleman.yazi_eni(el["metin"], el["yukseklik"]), el["yukseklik"] / 2.0
            a, b = {"sol": (0.0, w), "sag": (-w, 0.0)}.get(el.get("hiza"), (-w / 2.0, w / 2.0))
            if abs(abs(el.get("aci", 0)) - 90) < 1e-6:
                xs += [el["x"] - h, el["x"] + h]
                ys += [el["y"] + a, el["y"] + b] if el["aci"] > 0 else [el["y"] - b, el["y"] - a]
            else:
                xs += [el["x"] + a, el["x"] + b]
                ys += [el["y"] - h, el["y"] + h]
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
        cikti.append(
            {
                "yon": yon,
                "kot": kot,
                "bas": min(min(el["a"][i], el["b"][i]) for el in liste),
                "son": max(max(el["a"][i], el["b"][i]) for el in liste),
                "toplam": sum(el["uzunluk"] for el in liste),
                "adet": len(liste),
            }
        )
    return cikti


def cerceveli(elemanlar, baslik, olcek=20, pay=300, seritler=()):
    """Çizimi kendi çerçevesine alır ve altına başlık şeridi ekler.

    Referans projede de her çizim ayrı bir çerçevededir ve altında adı ile ölçeği
    yazar.  Çerçeve ölçüleri de kapsar;  yazılar dışarıda kalmaz.
    """
    k = olcek / 20.0  # yazılar paftada 1/20'deki boyda kalır
    x1, y1, x2, y2 = sinir(elemanlar, pay * k)
    serit = 220.0 * k
    #  Künye şeridi başlığı ve sağdaki yazıları taşımalı:  sığmıyorsa
    #  çerçeve iki yana eşit genişler  ( başlık proje adının üstüne biniyordu ).
    #  Başlık kâğıtta 5 mm ( LiftDesigner ):  104 → 140 em · 0,716 / 20
    gerek = (
        (120 + 200 + 120) * k
        + eleman.yazi_eni(f"{baslik}   1/{olcek:g}", eleman.yb(104 * k))
        + max([eleman.yazi_eni(m, eleman.yb(70 * k)) for m in seritler] or [0])
    )
    if x2 - x1 < gerek:
        fark = (gerek - (x2 - x1)) / 2.0
        x1, x2 = x1 - fark, x2 + fark
    e = list(elemanlar)
    e.append(eleman.dikdortgen("CERCEVE", x1, y1 - serit, x2 - x1, (y2 - y1) + serit))
    e.append(eleman.cizgi("CERCEVE", x1, y1, x2, y1))
    e.append(
        eleman.yazi(
            x1 + 120 * k, y1 - serit / 2.0, f"{baslik}   1/{olcek:g}", 104 * k, hiza="sol", katman="CERCEVE"
        )
    )
    for i, metin in enumerate(seritler):
        e.append(
            eleman.yazi(
                x2 - 120 * k, y1 - serit / 2.0 - i * 120 * k, metin, 70 * k, hiza="sag", katman="CERCEVE"
            )
        )
    return e


def _parcadan_kaydir(e, ek_katman=()):
    """Yazısı bir parçanın üstüne düşen ölçünün yazısı, kendi ölçüsü boyunca
    ( ya da ucunun dışına ) parçaya ve öbür yazılara binmeyen en yakın yere
    taşınır — _yazilari_yerlestir'in kaydir'ı gibi, ama yerleşimi bitmiş bir
    çizimde ( kuyu dibinde yük kutuları ölçü yazılarına göre konduktan sonra:
    kutuları da engel sayar ).  ek_katman:  engel sayılan öbür katmanlar."""
    katman = PARCA_KATMANLARI + tuple(ek_katman)
    parca_kutulari = [sinir([x]) for x in e if x["tip"] == "dikdortgen" and x.get("katman") in katman]

    def ortusur(a, b):
        return a[0] < b[2] - 2 and b[0] < a[2] - 2 and a[1] < b[3] - 2 and b[1] < a[3] - 2

    tasinir = []
    for el in e:
        if el["tip"] != "olcu" or not el.get("yazi"):
            continue
        k = _yazi_kutusu(el)
        if not any(ortusur(k, p) for p in parca_kutulari):
            continue
        y_ = el["yazi"]
        i = 0 if el["yon"] == "yatay" else 1
        a, b = sorted((el["a"][i], el["b"][i]))
        w = (k[2] - k[0]) / 2.0 if i == 0 else (k[3] - k[1]) / 2.0
        simdi = y_["x"] if i == 0 else y_["y"]
        yerler = [a + w + 10 + 10 * n for n in range(int(max(0.0, b - a - 2 * w - 20) / 10) + 1)]
        yerler = sorted(yerler, key=lambda u: abs(u - simdi)) + [a - 30 - w, b + 30 + w]
        tasinir.append((el, [(u, y_["y"]) if i == 0 else (y_["x"], u) for u in yerler]))
    if tasinir:
        _yazilari_coz(e, tasinir, ek_katman=ek_katman)
