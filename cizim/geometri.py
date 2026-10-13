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
from dataclasses import dataclass

from cizim import izli
from cizim import kisaltmalar
from cizim import eleman
from cizim import uslup
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


def yazilari_yerlestir(elemanlar, h=eleman.OLCU_YAZI, kaydir=False):
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
    Y = _YaziYerleri(elemanlar, h, kaydir)
    siralar = {}
    for el in elemanlar:
        if el["tip"] == "olcu" and "yazi" not in el:
            siralar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    #  BAŞKA SIRALARIN YAZILARI da sayılır ( yeri verilmiş ölçü yazıları ve bu
    #  çağrıda yerleşenler ):  sığmayan yazı ucun dışına çıkınca köşede öbür
    #  yöndeki sıranın yazısına biniyordu ( kuyu planının sağ üst köşesinde iki
    #  "DUVAR 150" — yazılar büyüyünce, 5 Eki ).
    Y.dolu = [yazi_kutusu(el) for el in elemanlar if el["tip"] == "olcu" and "yazi" in el]
    for (yon, kot), liste in siralar.items():
        i = 0 if yon == "yatay" else 1
        liste.sort(key=lambda q: min(q["a"][i], q["b"][i]))
        dis = -1.0 if kot < 0 else 1.0
        yerlesen = []  # ( kat, bas, son )
        for n, q in enumerate(liste):
            bas, son = sorted((q["a"][i], q["b"][i]))
            w = eleman.yazi_eni(q["metin"], h)
            aday = Y.adaylar(yon, kot, liste, n, i, bas, son, w)
            kat, orta = Y.sec(yon, kot, aday, yerlesen, bas, son, w)
            yerlesen.append((kat, orta - w / 2.0, orta + w / 2.0))
            Y.dolu.append(Y.kutu(yon, kot, kat, orta, w))
            capraz = kot + dis * (50.0 + eleman.KAT_ARALIGI * kat) * Y.k
            q["yazi"] = (
                {"x": orta, "y": capraz, "aci": 0.0, "h": h}
                if yon == "yatay"
                else {"x": capraz, "y": orta, "aci": 90.0, "h": h}
            )


def _sirada_biner(yerlesen, kat, orta, w, k):
    """Yazı sırasında aynı kattaki bir yazıya biner mi ( 25 mm payla )."""
    return any(
        kt == kat and orta - w / 2.0 < s + 25 * k and b < orta + w / 2.0 + 25 * k for kt, b, s in yerlesen
    )


class _YaziYerleri:
    """yazilari_yerlestir'in ortak durumu:  yazı boyu ( h ) ve ölçeği ( k —
    1/50'de yazı ve aralıklar büyür ), kaydir, parça kutuları ve kenarları,
    yazının kaçtığı engeller, dolu yazı kutuları."""

    def __init__(self, elemanlar, h, kaydir):
        self.h = h
        self.k = h / eleman.OLCU_YAZI
        self.kaydir = kaydir
        #  Parça kenarları ( parca_kenarlari ):  yazı maskelidir, bir kenarın
        #  üstüne düşerse kenarı siler — kuyu planında kabin duvarının "75"i
        #  kabinin iki çizgisinin üstündeydi ( 5 Eki ).
        self.kenarlar = KenarIzgarasi(parca_kenarlari(elemanlar))
        #  Ölçü yazısının üstüne düşmemesi gereken parçaların kutuları
        self.parca_kutulari = [
            sinir([x]) for x in elemanlar if x.get("katman") in PARCA_KATMANLARI and x["tip"] != "yazi"
        ]
        #  Yazının yer ararken kaçtığı engeller ( biner ):  parçalar, kaydir'da
        #  kapı da ( kanatlar, kasa, cepler — kabin üstünde ve kuyu planında
        #  yazı kapının içine düşmesin;  kenar denetimi yalnız kenarını görür ).
        self.engeller = self.parca_kutulari + (
            [sinir([x]) for x in elemanlar if x.get("katman") == "KAPI" and x["tip"] != "yazi"]
            if kaydir
            else []
        )
        self.dolu = []

    def kutu(self, yon, kot, kat, orta, w):
        h = self.h
        c = kot + (-1.0 if kot < 0 else 1.0) * (50.0 + eleman.KAT_ARALIGI * kat) * self.k
        return (
            (orta - w / 2.0, c - h / 2.0, orta + w / 2.0, c + h / 2.0)
            if yon == "yatay"
            else (c - h / 2.0, orta - w / 2.0, c + h / 2.0, orta + w / 2.0)
        )

    def biner(self, yon, kot, kat, orta, w):
        """Yazı bir engele ya da parça kenarına biner mi."""
        kutu = self.kutu(yon, kot, kat, orta, w)
        return any(
            kutu[0] < p[2] and p[0] < kutu[2] and kutu[1] < p[3] and p[1] < kutu[3] for p in self.engeller
        ) or self.kenarlar.kesisir(kutu, 2.0 * self.k)

    def kenara_biner(self, kutu):
        return self.kenarlar.kesisir(kutu, 2.0 * self.k) or any(
            kutu[0] < p[2] - 2 and p[0] < kutu[2] - 2 and kutu[1] < p[3] - 2 and p[1] < kutu[3] - 2
            for p in self.parca_kutulari
        )

    def yaziya_biner(self, kutu):
        return any(kutu[0] < d[2] and d[0] < kutu[2] and kutu[1] < d[3] and d[1] < kutu[3] for d in self.dolu)

    def adaylar(self, yon, kot, liste, n, i, bas, son, w):
        """Sıranın n. yazısının adayları ( kat, orta ), sırayla."""
        k = self.k
        aday = [(0, (bas + son) / 2.0)]
        uclar = ([(0, bas - w / 2.0 - 30 * k)] if n == 0 else []) + (
            [(0, son + w / 2.0 + 30 * k)] if n == len(liste) - 1 else []
        )
        #  Yazı parçasına sığmıyorsa ve sıranın ucundaysa ucun dışına yazılır
        #  ( referans projenin "62 83"ü gibi );  sığıyorsa parçanın ortasında durur.
        sigmaz = w > son - bas - 20 * k
        aday = uclar + aday if sigmaz else aday + uclar
        if sigmaz and not uclar:
            if self.biner(yon, kot, 0, (bas + son) / 2.0, w):
                boy = [abs(liste[m]["b"][i] - liste[m]["a"][i]) for m in (n - 1, n + 1)]
                yanlar = [(0, son + w / 2.0 + 30 * k), (0, bas - w / 2.0 - 30 * k)]
                if boy[0] > boy[1]:
                    yanlar.reverse()
                aday = [a for a in yanlar if not self.biner(yon, kot, a[0], a[1], w)] + aday
        elif self.kaydir and not sigmaz:
            #  kaydir:  sığan yazı ortada bir parçanın üstüne düşüyorsa kendi
            #  ölçüsünün içinde, ortaya en yakın boş yere kayar ( kabin üstü
            #  planında sığınma alanının yer ölçüsü şasenin üst kirişinin
            #  üstündeydi ).  Öbür çizimlerde yazıların yeri değişmez:  kuyu
            #  dibinde yük kutuları onlara göre yerleşir.
            orta = (bas + son) / 2.0
            if self.biner(yon, kot, 0, orta, w):
                pay = (son - bas - w) / 2.0 - 10 * k
                adim = [orta + s * d for d in range(10, int(pay) + 1, 10) for s in (-1, 1)]
                bos = [x for x in adim if not self.biner(yon, kot, 0, x, w)]
                #  Ölçünün içinde boş yer yoksa ve sıranın ucundaysa ucun dışı
                #  ( operatörün derinliğindeki parça:  operatör tavanın
                #  genişliğince uzanır )
                bos += [a[1] for a in uclar if not self.biner(yon, kot, 0, a[1], w)]
                if bos:
                    aday = [(0, bos[0])] + aday
        return aday + [(1, (bas + son) / 2.0), (2, (bas + son) / 2.0)]

    def sec(self, yon, kot, aday, yerlesen, bas, son, w):
        """Seçim:  sırasındaki yazılara binmeyen ( şart ), öbür yazılara
        binmeyen, parça kenarına binmeyen ilk aday;  hepsini sağlayan yoksa
        yazı kendi ölçüsü boyunca kayar ( _kaydir );  o da olmazsa ilk ikisini,
        o da yoksa yalnız ilkini sağlayan.  ( kat, orta )"""
        ilk = yazisiz = temiz = None
        for kat, orta in aday:
            if _sirada_biner(yerlesen, kat, orta, w, self.k):
                continue
            ilk = ilk or (kat, orta)
            kb_ = self.kutu(yon, kot, kat, orta, w)
            if self.yaziya_biner(kb_):
                continue
            yazisiz = yazisiz or (kat, orta)
            if not self.kenara_biner(kb_):
                temiz = (kat, orta)
                break
        if temiz is None:
            temiz = self._kaydir(yon, kot, yerlesen, bas, son, w)
        return temiz or yazisiz or ilk or aday[-1]

    def _kaydir(self, yon, kot, yerlesen, bas, son, w):
        """Adayların hepsi bir parçaya biniyor ( kuyunun içinden geçen sıralar ):
        yazı kendi ölçüsü boyunca kayar — uçların hemen dışına kadar, önce az
        kayan, sonra dış katlar.  ( kat, orta ) ya da None"""
        k = self.k
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
            if _sirada_biner(yerlesen, kat_, orta, w, k):
                continue
            kb_ = self.kutu(yon, kot, kat_, orta, w)
            if self.yaziya_biner(kb_):
                continue
            if not self.kenara_biner(kb_):
                return (kat_, orta)
        return None


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


@dataclass(frozen=True)
class _Plan:
    """Kuyu planının bölümlerinin ( duvar, kapı, kabin, ray, askı, ağırlık,
    ölçü, yazı ) ortak ölçüleri — plan() bir kez hesaplar, bölümler okur."""

    g: dict
    S: dict
    G: float  # kuyu genişliği
    D: float  # kuyu derinliği
    ds: float  # duvarlar:  sol · sağ · ön · arka
    dg: float
    don: float
    dar: float
    b0: float  # ön duvardaki kaba boşluğun iki yanı ( girdi.kaba_bosluk )
    b1: float
    KB: dict  # kapı bölgesi ( girdi.kapi_bolgesi )
    KT: dict  # kapı tipi ( girdi.kapi_tipi )
    x0: float  # kapının sol yanı
    kg: float  # kapı genişliği
    kx: float  # kabin merkezi
    ky: float
    ic_on: float  # kabin iç ön yüzü
    dis_g: float  # kabin dışı ( panolarla )
    dis_d: float
    ry: float  # kabin raylarının ekseni ( derinlikte )
    sol_yuz: float  # kabin raylarının dil yüzleri ( DBG bunların arası )
    sag_yuz: float
    ag_yan: str | None  # karşı ağırlık "Sol" · "Sağ" yanda;  None:  arkada
    ag_y: float  # yandaki ağırlığın ekseni ( derinlikte )
    ag_alt: float  # yandaki ağırlığın ray arkaları
    ag_ust: float
    ex: float  # ağırlık ekseni ( genişlikte )
    ey: float  # arkadaki ağırlığın ekseni ( derinlikte )
    kiris_ic: float  # yandaki ağırlıkta ara kirişin kabin tarafındaki yüzü
    aski: dict
    duzen: str | None  # askı düzeni:  "Kabin altı" · "Kabin üstü" · "Doğrudan"
    aski_y: float  # askı ekseni ( derinlikte )
    aski_yari: float  # askı elemanının derinlikteki yarı boyu
    capraz: dict | None  # arkadaki ağırlıkla 2:1 çapraz askı ( arka_aski )


def _plan_olculeri(g, S):
    k, kb, kp = g["kuyu"], g["kabin"], g["kapi"]
    kr, ag = g["kabin_ray"], g["agirlik"]
    G = k["genislik"]
    b0, b1, _ = girdi.kaba_bosluk(g, S)
    kx = G / 2.0 + kb["kaciklik_y"]
    ic_on = kb["on_pay"]
    dis_d = kb["derinlik"] + S["kabin_pano_arka"]
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
    if ag_yan is None:
        ex = G / 2.0
    else:
        ex = ag["ray_duvar"] if ag_yan == "Sol" else G - ag["ray_duvar"]
    #  Kabin rayının ara kirişi ağırlık rayı konsollarına bağlanır:  kol plakadan
    #  kirişe uzanır  ( ağırlığın boyunun DIŞINDAN geçer ).
    if ag_yan == "Sol":
        kiris_ic = sol_yuz - kr["h"] - S["ara_kiris_en"]
    else:
        kiris_ic = sag_yuz + kr["h"] + S["ara_kiris_en"]
    #  ASKI DÜZENİ  ( kullanıcı seçer:  kabin altı · kabin üstü · doğrudan ):
    #  kasnakların ve askı noktalarının yeri GİRDİDEN gelir;  koda gömülmez.
    aski = g.get("aski") or {}
    duzen = aski.get("duzen")
    aski_y = (
        ic_on
        + dis_d / 2.0
        + aski.get("kasnak_kaciklik" if duzen in ("Kabin altı", "Kabin üstü") else "nokta_kaciklik", 0)
    )
    capraz = arka_aski.geometri(g, S) if arka_aski.arkada_iki_bir(g) else None
    if capraz is not None and "P" in capraz:
        aski_yari = 0.0
    elif duzen in ("Kabin altı", "Kabin üstü"):
        aski_yari = S["kabin_kasnak_genislik"] / 2.0
    elif duzen == "Doğrudan":
        aski_yari = 45.0
    else:
        aski_yari = 0.0
    return _Plan(
        g=g,
        S=S,
        G=G,
        D=k["derinlik"],
        ds=k["duvar_sol"],
        dg=k["duvar_sag"],
        don=k["duvar_on"],
        dar=k["duvar_arka"],
        b0=b0,
        b1=b1,
        KB=girdi.kapi_bolgesi(g, S),
        KT=girdi.kapi_tipi(kp.get("tip")),
        x0=kp["sol_pay"],
        kg=kp["genislik"],
        kx=kx,
        ky=ic_on + kb["derinlik"] / 2.0,
        ic_on=ic_on,
        dis_g=kb["genislik"] + 2 * S["kabin_pano_yan"],
        dis_d=dis_d,
        ry=ry,
        sol_yuz=sol_yuz,
        sag_yuz=sag_yuz,
        ag_yan=ag_yan,
        ag_y=ag_y,
        ag_alt=ag_y - ag["ray_arasi"] / 2.0 - ag["h"],
        ag_ust=ag_y + ag["ray_arasi"] / 2.0 + ag["h"],
        ex=ex,
        ey=k["derinlik"] - ag["ray_duvar"],
        kiris_ic=kiris_ic,
        aski=aski,
        duzen=duzen,
        aski_y=aski_y,
        aski_yari=aski_yari,
        capraz=capraz,
    )


def plan(g, cizim_sabitleri=None, kapi_duzeyi=True, duvar_boslugu=None):
    """Kuyu planının elemanları  ( liste ).

    kapi_duzeyi:  plan kat kapısı hizasından kesilir ( C-C ) — ön duvar kapı
    boşluğunun iki yanında iki parçadır, tarama boşluktan geçmez.  Kapının
    üstünden / altından kesilen planlar ( kuyu dibi, kuyu üstü, delik planı )
    duvarı kesintisiz alır:  False.
    duvar_boslugu:  ön duvarın boşluklu olup olmadığı ( verilmezse
    kapi_duzeyi ) — kabin üstü planı kesit kotu kaba boşluğun içinde kalırsa
    boşluklu ister ( kabin_ustu.kapi_gorunusu ).

    Eleman SIRASI çizimin parçasıdır ( sonraki öncekinin üstüne çizilir;
    altın kayıtlar sırayı da tutar ):  bölümler aşağıdaki sırayla eklenir."""
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    P = _plan_olculeri(g, S)
    e = _duvarlar(P, kapi_duzeyi if duvar_boslugu is None else duvar_boslugu)
    e += _kat_kapisi(P, kapi_duzeyi)
    e += _kabin(P)
    e += _kabin_raylari(P)
    e += _aski(P)
    e += _agirlik_yanda(P) if P.ag_yan else _agirlik_arkada(P)
    if kapi_duzeyi:
        _kesitte_gizle(P, e)
    #  KUMANDA PANOSU KUYU PLANINDA YOK:  makine dairesiz tesiste en üst katta
    #  kuyunun dışındaki acil kurtarma panosundadır ( kuyu üstü planı ), makine
    #  daireli tesiste makine dairesindedir.  Eskiden kuyunun içinde, yan
    #  duvarda kaynağı belirsiz 400 × 90'lık bir "PANO" çiziliyordu:  kesitlerde
    #  karşılığı yoktu, makine dairelide makine dairesindekiyle çift oluyordu.

    #  Alttaki ölçü sıraları menteşeli kapının açılma yayının da altında
    alt = min([-P.don - S["bina_duvari"]] + [el["y"] for el in e if el.get("ad") == "kapi_acilisi"])
    e += _ust_olculer(P)
    e += _alt_olculer(P, alt)
    e += _yan_olculer(P)
    e += _kabin_ici_olculeri(P)
    e += _aski_olculeri(P)
    e += _kabin_kapisi(P)
    _yazilar(P, e)
    yazilari_yerlestir(e, kaydir=True)
    adaylar = _kabin_ici_yazi_adaylari(P, e)
    if adaylar:
        yazilari_coz(e, adaylar)
    parcadan_kaydir(e, ek_katman=("AGIRLIK",))
    e += kesit_isaretleri(g, e)
    return e


def _duvarlar(P, bosluklu):
    """Duvarlar ( tarama yalnız duvar kesitinde ).  Boşluklu ön duvar kat
    kapısının kaba boşluğunun iki yanındadır ( girdi.kaba_bosluk — giriş
    görünüşüyle aynı;  duvar boşluğuna monte kapıda kasa da boşluktadır )."""
    G, D, ds, dg, don, dar = P.G, P.D, P.ds, P.dg, P.don, P.dar
    if bosluklu:
        on = [(-ds, -don, P.b0 + ds, don), (P.b1, -don, G + dg - P.b1, don)]
    else:
        on = [(-ds, -don, G + ds + dg, don)]
    e = []
    for x, y, g_, d_ in on + [(-ds, D, G + ds + dg, dar), (-ds, 0, ds, D), (G, 0, dg, D)]:
        if g_ <= 1e-6:
            continue
        e.append(eleman.dikdortgen("TARAMA", x, y, g_, d_, tip="tarama"))
        e.append(eleman.dikdortgen("KUYU-DUVAR", x, y, g_, d_))
    e.append(eleman.dikdortgen("KUYU-IC", 0, 0, G, D))
    return e


def _kat_kapisi(P, kapi_duzeyi):
    """Kat kapısı:  boşluk · kasa · eşik · kanatlar · açılış işareti.

    Kat kapısı ünitesi ( kasa + eşik ) montaja göre ya duvar boşluğunda
    ( kasa duvarda, eşik kuyuya taşar ) ya da duvarın iç yüzünde durur
    ( ünitenin tamamı kuyunun içinde ).  KANATLAR EŞİĞİN ÜSTÜNDEDİR:
    kapalı konumda, teleskopikte iki düzlemde ( referans proje kapı detayı )."""
    S, KB, x0, kg = P.S, P.KB, P.x0, P.kg
    e = [eleman.ad(eleman.dikdortgen("KAPI", P.b0, -P.don, P.b1 - P.b0, P.don), "kapi_boslugu")]
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
    kanatlar, kat_kanat = _kanatlar_ve_cepler(P, kat_esigi, *KB["esik"], "kat_kanadi", "kanat_cebi")
    e += kanatlar
    e += _acilis_isareti(P, kat_kanat[0], kapi_duzeyi)
    #  Kapının iki yanındaki bina duvarı yalnız istenirse çizilir.
    if S["bina_duvari"] > 0:
        for bx0, bg in ((-P.ds, x0 + P.ds), (x0 + kg, P.G - (x0 + kg) + P.dg)):
            if bg > 0:
                e.append(
                    eleman.dikdortgen(
                        "BINA", bx0, -P.don - S["bina_duvari"], bg, S["bina_duvari"], tip="tarama_tugla"
                    )
                )
    return e


def _kanatlar_ve_cepler(P, esik_el, esik0, esik1, kanat_adi, cep_adi):
    """Bir eşiğin ( kat ya da kabin ) kanatları ve kanat cepleri;  eşiğin
    biçimi de bunlara göre kurulur.  ( elemanlar, kanat düzlemlerinin y'leri )"""
    kanatlar, duzlemler = _kanatlar(P, esik0, esik1, kanat_adi)
    yeni = kanatlar + _cepler(P, esik0, esik1, duzlemler, cep_adi)
    _esik_bicimi(P, esik_el, yeni)
    return yeni, duzlemler


def _kanatlar(P, esik0, esik1, ad):
    """Kapalı kanatlar, her biri kapının kanat sayısı kadarda biri.
    Teleskopik:  her kanat ayrı düzlemde ( eşiğin kenarından kanat_esik_payi
    içeride, kanat_araligi arayla );  cebe en yakın kanat duvara en yakın
    düzlemde ( LiftDesigner 1022 ).  Merkezi:  her yanda yarısı, dıştaki
    duvara yakın düzlemde;  2 kanatta tek düzlem eşiğin ortasında.  Elle
    açılan kapıda tek kanat.  ( elemanlar, her kanadın düzleminin y'si )"""
    S, KT = P.S, P.KT
    n_kanat = KT["kanat"]
    kanat = P.kg / n_kanat
    orta = (esik0 + esik1) / 2.0 - S["kanat_kalinlik"] / 2.0
    e, yer = [], []
    for i in range(n_kanat):
        if KT["tur"] == "teleskopik":
            sira = i if KT["yon"] == "Sol" else n_kanat - 1 - i
        elif KT["duzlem"] > 1:
            sira = i if i < n_kanat // 2 else n_kanat - 1 - i
        else:
            sira = None
        ky0 = orta if sira is None else esik0 + S["kanat_esik_payi"] + sira * S["kanat_araligi"]
        el = eleman.ad(eleman.dikdortgen("KAPI", P.x0 + i * kanat, ky0, kanat, S["kanat_kalinlik"]), ad)
        #  sac tepsi:  kat kapısının yüzü kata, kabin kapısınınki kabine bakar
        el["bicim"] = parcalar.kanat_bicimi(el["x"], el["y"], el["g"], el["d"], ad == "kat_kanadi")
        e.append(el)
        yer.append(ky0)
    return e, yer


def _cepler(P, esik0, esik1, duzlemler, ad):
    """KANAT CEBİ ( LiftDesigner gibi ):  açılan kanatların durduğu yer —
    eşiğin bandında kapının yanında, uçta her kanat düzlemine durdurucu."""
    S = P.S
    pay = S["kanat_cebi_payi"]
    e = []
    for c0, c1 in girdi.kanat_cepleri(P.g, S):
        e.append(eleman.ad(eleman.dikdortgen("KAPI", c0, esik0, c1 - c0, esik1 - esik0), ad))
        uc = c0 if c1 <= P.x0 + 1e-6 else c1 - pay
        for ky0 in sorted(set(duzlemler)):
            if pay > 0:
                e.append(
                    eleman.ad(eleman.dikdortgen("KAPI", uc, ky0, pay, S["kanat_kalinlik"]), "kanat_durdurucu")
                )
    return e


def _esik_bicimi(P, esik_el, yeni):
    """EŞİK ( parcalar ):  cebin altından da süren tek parça — eşikle cep
    arasında çizgi yok;  her kanat düzleminin kılavuz oluğu, üstündeki
    kanadın ve durdurucunun örtmediği yerde görünür."""
    kanat_el = [x for x in yeni if x.get("ad") in ("kat_kanadi", "kabin_kanadi")]
    cep_el = [x for x in yeni if x.get("ad") in ("kanat_cebi", "kabin_kanat_cebi")]
    ortu = [
        (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
        for x in yeni
        if x.get("ad") in ("kat_kanadi", "kabin_kanadi", "kanat_durdurucu")
    ]
    merkez = [] if P.KT["tur"] == "manuel" else [x["y"] + x["d"] / 2.0 for x in kanat_el]
    ex0 = esik_el["x"]
    solda = [c for c in cep_el if abs(c["x"] + c["g"] - ex0) < 1e-6]
    for el, sol_acik, sag_acik in [(esik_el, bool(solda), len(cep_el) > len(solda))] + [
        (c, c not in solda, c in solda) for c in cep_el
    ]:
        el["bicim"] = parcalar.esik_cizgileri(
            el["x"], el["y"], el["g"], el["d"], sol_acik, sag_acik
        ) + parcalar.oluk_cizgileri(el["x"], el["x"] + el["g"], merkez, ortu)


def _acilis_isareti(P, kanat_y, kapi_duzeyi):
    """Açılış yönü oku:  teleskopik kapı hangi yana açılıyorsa o yöne bakar;
    merkezi kapıda iki yana.  Menteşeli kapıda açılma simgesi."""
    KT, x0, kg = P.KT, P.x0, P.kg
    ok_y = kanat_y + P.S["kanat_kalinlik"] / 2.0
    if KT["tur"] == "teleskopik":
        sag = KT["yon"] == "Sağ"
        return [
            eleman.ok("KAPI", x0 + (kg * 0.65 if sag else kg * 0.35), ok_y, x0 + (kg if sag else 0), ok_y)
        ]
    if KT["tur"] == "manuel" and kapi_duzeyi:
        #  MENTEŞELİ KAPI:  ok yerine açılma simgesi ( ISO 128 / yapı resmi:
        #  açık konum ve çeyrek yay, ince sürekli çizgi ).  Kat kapısı kata
        #  açılır;  menteşe kanadın kat yüzünde, kasanın yanında.  Yan
        #  ( kullanıcı 8 Eki:  "Manuel Sağ sağa açılıyor" ):  kattan bakınca
        #  kanat sağa açılır, menteşe sağda ( DIN 107'nin "sağ"ı da bu );
        #  kattan bakan için sağ, planın +x'idir ( teleskopik "Sağ" da +x'e açılır ).
        sag = KT["yon"] == "Sağ"
        hx, hy = (x0 + kg if sag else x0), kanat_y
        s = -1.0 if sag else 1.0  # menteşeden kanadın serbest ucuna
        yay = [
            (hx + s * kg * izli.cos(izli.radians(a)), hy - kg * izli.sin(izli.radians(a)))
            for a in range(0, 91, 5)
        ]
        acilis = eleman.ad(eleman.dikdortgen("ACILIS", min(hx, hx + s * kg), hy - kg, kg, kg), "kapi_acilisi")
        acilis["bicim"] = [
            {"noktalar": [(hx, hy), (hx, hy - kg)], "kapali": False},
            {"noktalar": yay, "kapali": False},
        ]
        return [acilis]
    return [
        eleman.ok("KAPI", x0 + kg / 2.0, ok_y, x0, ok_y),
        eleman.ok("KAPI", x0 + kg / 2.0, ok_y, x0 + kg, ok_y),
    ]


def _kabin(P):
    """Kabin:  pano · şase · eksenler."""
    S, kb, kr = P.S, P.g["kabin"], P.g["kabin_ray"]
    kx = P.kx
    e = [
        eleman.ad(eleman.dikdortgen("KABIN", kx - P.dis_g / 2.0, P.ic_on, P.dis_g, P.dis_d), "kabin_dis"),
        eleman.dikdortgen("KABIN-IC", kx - kb["genislik"] / 2.0, P.ic_on, kb["genislik"], kb["derinlik"]),
    ]
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
    e.append(eleman.cizgi("EKSEN", kx, -P.don - 150, kx, P.D + P.dar + 150, tip="eksen"))
    e.append(eleman.cizgi("EKSEN", -P.ds - 150, P.ky, P.G + P.dg + 150, P.ky, tip="eksen"))
    return e


def _kabin_raylari(P):
    """Kabin rayları · bağlantıları ( konsol ya da ara kiriş ) · patenler."""
    S, kr, ry = P.S, P.g["kabin_ray"], P.ry
    e = []
    for yon, yuz in ((-1, P.sol_yuz), (+1, P.sag_yuz)):
        e += [eleman.ad(r, "kabin_ray") for r in _ray_yatay(yuz, ry, kr["b"], kr["h"], yon)]
        arka = yuz + kr["h"] * yon  # rayın duvara bakan yüzü
        if P.ag_yan == ("Sol" if yon < 0 else "Sağ"):
            e += _ara_kiris(P, yon, arka)
        else:
            e += _kabin_rayi_konsolu(P, yon, arka)
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
    e.append(eleman.cizgi("EKSEN", -P.ds - 150, ry, P.G + P.dg + 150, ry, tip="eksen"))
    return e


def _ara_kiris(P, yon, arka):
    """Yandaki ağırlığın tarafındaki kabin rayı:  ara kiriş = ağırlık
    çerçevesinin kabin tarafındaki boyuna profili ( LiftDesigner K431 );
    kabin rayı ona tırnakla bağlı."""
    S, kr = P.S, P.g["kabin_ray"]
    kiris = eleman.dikdortgen(
        "KONSOL",
        arka - S["ara_kiris_en"] if yon < 0 else arka,
        P.ag_alt - S["konsol_agirlik_boy"] / 2.0,
        S["ara_kiris_en"],
        P.ag_ust - P.ag_alt + S["konsol_agirlik_boy"],
        ad="ara_kiris",
    )
    return [kiris] + _tirnaklar(arka, P.ry, kr["b"], kr["h"], -yon, yatay=True)


def _kabin_rayi_konsolu(P, yon, arka):
    """Kabin rayının duvar konsolu:  duvara dayanan plaka ( boşluğu doldurmaz ),
    cıvatalar, kol ve tırnaklar."""
    S, kr, ry = P.S, P.g["kabin_ray"], P.ry
    duvar_x = 0 if yon < 0 else P.G
    kx0 = duvar_x - S["konsol_kabin_en"] if yon > 0 else duvar_x
    plaka = eleman.dikdortgen(
        "KONSOL",
        kx0,
        ry - S["konsol_kabin_boy"] / 2.0,
        S["konsol_kabin_en"],
        S["konsol_kabin_boy"],
        ad="plaka",
    )
    e = [plaka]
    for cy in (ry - S["konsol_civata_araligi"], ry + S["konsol_civata_araligi"]):
        e.append(eleman.daire("CIVATA", kx0 + S["konsol_kabin_en"] / 2.0, cy, S["konsol_civata_capi"] / 2.0))
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
    return e + _tirnaklar(arka, ry, kr["b"], kr["h"], -yon, parcalar.konsol_tipi(kr["b"])[3], yatay=True)


def _aski(P):
    """Askı:  kabin kasnakları ya da askı noktası, makine taşıyıcıları."""
    S, aski, duzen, kx, aski_y = P.S, P.aski, P.duzen, P.kx, P.aski_y
    if P.capraz is not None and "P" in P.capraz:
        e = _capraz_aski(P)
    elif duzen in ("Kabin altı", "Kabin üstü"):
        dc, aralik = aski["kasnak_capi"], aski["kasnak_arasi"]
        e = []
        for merkez in (kx - aralik / 2.0, kx + aralik / 2.0):
            e.append(
                eleman.ad(
                    eleman.dikdortgen("KASNAK", merkez - dc / 2.0, aski_y - P.aski_yari, dc, 2 * P.aski_yari),
                    "kabin_kasnak",
                )
            )
            e.append(
                eleman.ad(
                    eleman.yazi(merkez, aski_y + P.aski_yari + 45, f"ø {dc:g}", uslup.NORMAL),
                    "kabin_kasnak_yazi",
                )
            )
    elif duzen == "Doğrudan":
        #  1:1:  halatlar kabin şasesinin üst kirişinin ortasındaki TEK
        #  bağlantıda biter ( tek tahrik kasnağı — LiftDesigner 12744-3 );  kiriş
        #  ray ekseni üstündedir, kaçıklık hesabın xs'idir.
        e = [
            eleman.ad(eleman.daire("KASNAK", kx, aski_y, 45), "aski_nokta"),
            eleman.ad(eleman.cizgi("KASNAK", kx - 70, aski_y, kx + 70, aski_y), "aski_nokta"),
            eleman.ad(eleman.cizgi("KASNAK", kx, aski_y - 70, kx, aski_y + 70), "aski_nokta"),
        ]
    else:
        e = []
    return e + makine.plan(
        baglantilar.kasnak_tasiyicilari(P.g, S, -S["kabin_kasnak_derinlik"]),
        eleman.dikdortgen,
        eleman.daire,
        eleman.cizgi,
    )


def _capraz_aski(P):
    """ARKADAKİ AĞIRLIKLA 2:1 ( kabin üstü, çapraz — arka_aski ):  kasnaklar
    P–H düzleminde;  planda döndürülmüş dikdörtgen ( kenarları çizgi ),
    düzlem kesik eksen, iki düşey halat noktası."""
    capraz = P.capraz
    dc = P.aski["kasnak_capi"]
    e = []
    for merkez, iz in zip(capraz["kasnaklar"], capraz["izler"]):
        for p0, p1 in zip(iz, iz[1:] + iz[:1]):
            e.append(eleman.ad(eleman.cizgi("KASNAK", p0[0], p0[1], p1[0], p1[1]), "kabin_kasnak_capraz"))
        e.append(
            eleman.ad(
                eleman.yazi(
                    merkez[0] + capraz["n"][0] * 110,
                    merkez[1] + capraz["n"][1] * 110,
                    f"ø {dc:g}",
                    uslup.NORMAL,
                ),
                "kabin_kasnak_yazi",
            )
        )
    (px, py), (hx, hy) = capraz["P"], capraz["H"]
    e.append(eleman.ad(eleman.cizgi("EKSEN", px, py, hx, hy, tip="eksen"), "aski_duzlemi"))
    return e


def _agirlik_blogu(P, ax, ay, en, boy):
    """Karşı ağırlığın çerçevesi ve dolgusu."""
    cer = P.S["agirlik_cerceve"]
    return [
        eleman.ad(eleman.dikdortgen("AGIRLIK", ax, ay, en, boy), "agirlik_blok"),
        eleman.dikdortgen("AGIRLIK", ax + cer, ay + cer, en - 2 * cer, boy - 2 * cer),
    ]


def _agirlik_yanda(P):
    """Yandaki karşı ağırlık:  çerçeve · dolgu · raylar · konsol çerçevesi · kasnak."""
    S, ag, G = P.S, P.g["agirlik"], P.G
    sol = P.ag_yan == "Sol"
    ex, ag_y, kiris_ic = P.ex, P.ag_y, P.kiris_ic
    ax = ex - ag["derinlik"] / 2.0
    e = _agirlik_blogu(P, ax, ag_y - ag["genislik"] / 2.0, ag["derinlik"], ag["genislik"])
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
        cer = S["agirlik_cerceve"]
        e.append(
            eleman.ad(
                eleman.dikdortgen("KASNAK", ax + cer, ag_y - dc / 2.0, ag["derinlik"] - 2 * cer, dc),
                "agirlik_kasnak",
            )
        )
        e.append(eleman.ad(eleman.yazi(ex, ag_y, f"ø {dc:g}", uslup.NORMAL, aci=90), "agirlik_kasnak_yazi"))
    return e


def _agirlik_arkada(P):
    """Arkadaki karşı ağırlık:  çerçeve · dolgu · raylar · konsol profilleri · kasnak."""
    S, ag, G, D = P.S, P.g["agirlik"], P.G, P.D
    ex, ey = P.ex, P.ey
    e = _agirlik_blogu(
        P, G / 2.0 - ag["genislik"] / 2.0, ey - ag["derinlik"] / 2.0, ag["genislik"], ag["derinlik"]
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
        plaka = eleman.dikdortgen(
            "KONSOL",
            ray_arkasi - S["konsol_agirlik_boy"] / 2.0,
            D - S["konsol_agirlik_en"],
            S["konsol_agirlik_boy"],
            S["konsol_agirlik_en"],
            ad="plaka",
        )
        boy = max(S["konsol_agirlik_en"], ag["ray_duvar"] + parcalar.tirnak_uzanimi(ag["b"], ag["h"]) + 10)
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
        cer = S["agirlik_cerceve"]
        e.append(
            eleman.ad(
                eleman.dikdortgen(
                    "KASNAK", ex - dc / 2.0, ey - ag["derinlik"] / 2.0 + cer, dc, ag["derinlik"] - 2 * cer
                ),
                "agirlik_kasnak",
            )
        )
        e.append(eleman.ad(eleman.yazi(ex, ey, f"ø {dc:g}", uslup.NORMAL), "agirlik_kasnak_yazi"))
    return e


def _kesitte_gizle(P, e):
    """KESİTTE GÖRÜNMEYEN ASKI  ( yalnız C-C ).

    Kuyu planı kabinin ortasından kesilir ( kapı yüksekliğinin yarısı ) ve
    yukarıdan bakılır:  şasenin dikmeleri kesilir ( düz kalır );  üst kiriş,
    kabin üstü kasnaklar ve 1:1 bağlantısı kesitin ÜSTÜNDE ( kaldırılmış ),
    alt kiriş, kabin altı kasnaklar ve taşıyıcıları kabin döşemesinin ALTINDA
    ( örtülü ):  kesik çizgiyle ( GIZLI ) çizilir, ölçüleri yerinde kalır.
    Kabin altı kasnağın kabinin izinin dışına taşan ucu yukarıdan açıktır,
    düz çizilir ( halat oradan çıkar ) — LiftDesigner 4815-6'nın kuyu planı ve
    referans projenin yatay kesiti de böyle.  Eskiden hepsi düz çiziliyordu:
    şase kirişleri ve kasnaklar kabinin içinden geçiyor görünüyordu ( 3 Eki ).
    Öbür planlar ( kapi_duzeyi=False ) elemanları adlarıyla kendileri seçer."""
    k0, k1 = P.kx - P.dis_g / 2.0, P.kx + P.dis_g / 2.0
    for el in list(e):
        if el.get("ad") not in _KESITTE_GIZLI:
            continue
        if el.get("ad") == "kabin_kasnak" and P.duzen == "Kabin altı":
            for a, b in ((el["x"], min(el["x"] + el["g"], k0)), (max(el["x"], k1), el["x"] + el["g"])):
                if b - a > 1e-6:
                    e.append(
                        eleman.ad(eleman.dikdortgen("KASNAK", a, el["y"], b - a, el["d"]), "kabin_kasnak_ucu")
                    )
        el["katman"] = "GIZLI"


#  ── ÖLÇÜLER ──────────────────────────────────────────────────────────
#  ÖLÇÜ DİLİ ( kisaltmalar — 13 Eki, kullanıcı "LD gibi kısa kod + tablo" ):
#  asıl ölçüler kodla ( SW · SD · CW · CD · PLW · DW · DBG · DBGW ), neyi
#  ölçtüğü çizimden belli olanlar ( duvar, kasa, ray yüksekliği, eşikler,
#  eksenlerin yeri, askı ) yalnız sayıyla.  Her ölçünün yazıdan bağımsız
#  KİMLİĞİ ( ad, "olcu_…" ):  yazı sayıya inince ölçüye tıklama ölçüyü onunla
#  tanır ( olcu_kaynagi._imza ).
#  SIRALAR ( ISO 129-1 ):  ara zincirler içte, duvarlarla kuyu genişliği /
#  derinliği en dışta;  her ölçü bir kez — kuyunun dış ölçüsü ( duvar + SW +
#  duvar ) yazılmaz ( kullanıcı kararı 13 Eki ), SW altta tekrarlanmaz.
#  Uzatma çizgisi yoktur:  ölçü, ölçtüğü noktaların hizasında durur.
#  PLANIN DIŞINDAKİ SIRALAR yalnız kuyu sınırı boyunca okunabilen
#  ölçüleri taşır;  bir iç parçayı ( askı, eşik ) ölçen ölçü parçanın
#  yanına, planın İÇİNE konur — dışarıda neyi ölçtüğü görünmüyordu.
#  Her sıra ( aynı kot ) bir zincirdir ve toplama kapanır.
#  Kabinin dış yüzleri ( LiftDesigner'ın PLW'si ):  şasenin dikmeleri rayın
#  ucunda, kabinle ray arasındadır — eskiden "ŞASE DIŞI" kabin + 2 × 30'du,
#  çizimde karşılığı yoktu.
#  Dış ölçü sıraları arası:  1/20'de 100 ( kâğıtta 5 mm — LiftDesigner );
#  bütün planlar bunu kullanır ( eskiden 200 — 10 mm )
SIRA_ARASI = 100.0


def _o(yon, a, b, kot, ad=None, metin=None, **ek):
    """Planın ölçüsü ( kimliği önce — okunsun diye )."""
    return eleman.olcu(yon, a, b, kot, metin, ad=ad, **ek)


def _ust_olculer(P):
    """ÜST — kuyu genişliği boyunca.  Sıralar duvardan dışarı:  kabinin dış
    yüzleri ( PLW ), kabin rayları ( DBG ), arkadaki ağırlığın rayları
    ( DBGW ), en dışta duvarlar ve kuyu genişliği ( SW )."""
    G, ds, dg, kr = P.G, P.ds, P.dg, P.g["kabin_ray"]
    sol_yuz, sag_yuz = P.sol_yuz, P.sag_yuz
    ic_sol, ic_sag = P.kx - P.dis_g / 2.0, P.kx + P.dis_g / 2.0
    u = [P.D + P.dar + 120 + i * SIRA_ARASI for i in range(4)]
    e = [
        _o(
            "yatay",
            (ic_sol, 0),
            (ic_sag, 0),
            u[0],
            "kabin_dis_genisligi",
            kisaltmalar.kodlu("PLW", ic_sag - ic_sol),
        ),
    ]
    #  KABİN İLE KARŞI AĞIRLIK ARASI ( m.5.2.5.5.1 h:  en az 50 — girdi.dogrula ):
    #  yandaki ağırlıkta zincir duvardan ağırlığın çerçevesine, çerçeveye ve
    #  kabinin dış yüzüne ( LiftDesigner 4815-6:  100 · 150 · 225 · PLW ).
    #  Eskiden yalnız duvar – şase ölçülüyordu;  kabin ile ağırlık arası hiçbir
    #  planda yoktu.
    #  Ağırlık kabinle bu yönde ayrık değilse ( ağırlık kabinin önünde ya da
    #  arkasında kalıyor — aralarındaki açıklık derinliktedir ) bölünmez.
    ag, ex = P.g["agirlik"], P.ex
    sol_uc, sag_uc = [0.0, ic_sol], [ic_sag, G]
    if P.ag_yan:
        bx0, bx1 = ex - ag["derinlik"] / 2.0, ex + ag["derinlik"] / 2.0
        if P.ag_yan == "Sol" and bx1 <= ic_sol:
            sol_uc = [0.0, bx0, bx1, ic_sol]
        elif P.ag_yan == "Sağ" and bx0 >= ic_sag:
            sag_uc = [ic_sag, bx0, bx1, G]
    for uc in (sol_uc, sag_uc):
        e += [_o("yatay", (a, 0), (b, 0), u[0]) for a, b in zip(uc, uc[1:]) if b - a > 1e-6]
    e += [
        _o("yatay", (0, 0), (sol_yuz - kr["h"], 0), u[1]),
        _o("yatay", (sol_yuz - kr["h"], 0), (sol_yuz, 0), u[1], "kabin_rayi_sol"),
        _o(
            "yatay",
            (sol_yuz, 0),
            (sag_yuz, 0),
            u[1],
            "kabin_ray_arasi",
            kisaltmalar.kodlu("DBG", kr["arasi"]),
        ),
        _o("yatay", (sag_yuz, 0), (sag_yuz + kr["h"], 0), u[1], "kabin_rayi_sag"),
        _o("yatay", (sag_yuz + kr["h"], 0), (G, 0), u[1]),
    ]
    dis = 2
    if not P.ag_yan:
        #  Arkadaki ağırlığın rayları kuyu genişliği boyunca ölçülür
        r0, r1 = ex - ag["ray_arasi"] / 2.0, ex + ag["ray_arasi"] / 2.0
        e += [
            _o("yatay", (0, 0), (r0, 0), u[2]),
            _o(
                "yatay",
                (r0, 0),
                (r1, 0),
                u[2],
                "agirlik_ray_arasi",
                kisaltmalar.kodlu("DBGW", ag["ray_arasi"]),
            ),
            _o("yatay", (r1, 0), (G, 0), u[2]),
        ]
        dis = 3
    e += [
        _o("yatay", (-ds, 0), (0, 0), u[dis], "duvar_sol"),
        _o("yatay", (0, 0), (G, 0), u[dis], "kuyu_genisligi", kisaltmalar.kodlu("SW", G)),
        _o("yatay", (G, 0), (G + dg, 0), u[dis], "duvar_sag"),
    ]
    return e


def _alt_olculer(P, alt):
    """ALT — kapı zinciri, kuyu genişliği, kabin ve ağırlık eksenleri
    ( alt:  kapının ve açılma yayının altı )."""
    G, x0, kg, kasa = P.G, P.x0, P.kg, P.S["kasa_yan"]
    a1, a3 = alt - 120, alt - 120 - SIRA_ARASI
    e = [
        _o("yatay", (0, 0), (x0 - kasa, 0), a1),
        _o("yatay", (x0 - kasa, 0), (x0, 0), a1, "kasa_sol"),
        _o("yatay", (x0, 0), (x0 + kg, 0), a1, "kapi_genisligi", kisaltmalar.kodlu("DW", kg)),
        _o("yatay", (x0 + kg, 0), (x0 + kg + kasa, 0), a1, "kasa_sag"),
        _o("yatay", (x0 + kg + kasa, 0), (G, 0), a1),
    ]
    ex = P.ex
    noktalar = sorted(set([0.0, P.kx, G] + ([ex] if P.ag_yan else [])))
    for sol_n, sag_n in zip(noktalar, noktalar[1:]):
        ad = None
        if (P.ag_yan == "Sol" and sol_n == 0 and sag_n == ex) or (
            P.ag_yan == "Sağ" and sol_n == ex and sag_n == G
        ):
            ad = "agirlik_ekseni"
        e.append(_o("yatay", (sol_n, 0), (sag_n, 0), a3, ad))
    return e


def _yan_olculer(P):
    """YANLAR — kuyu derinliği boyunca.  Sıra listesi duvardan dışarı
    doğrudur;  ağırlık yandaysa kendi zinciri O YANDA, duvara en yakın
    sırada durur  ( konsol kotları ağırlığın yanında okunur );  kabin rayı
    konsolunun cıvata aralığı duvara dayanan konsolun yanında."""
    if P.ag_yan == "Sol":
        sol, sag = [_agirlik_rayi_sirasi], [_civata_sirasi]
    elif P.ag_yan == "Sağ":
        sol, sag = [_civata_sirasi], [_agirlik_rayi_sirasi]
    else:
        sol, sag = [], [_civata_sirasi]
    sol += [_ray_ekseni_sirasi]
    sag += [_kabin_derinligi_sirasi, _esik_sirasi, _kapi_arasi_sirasi, _on_arka_duvar_sirasi]
    e = []
    for i, sira in enumerate(sol):
        e += sira(P, -P.ds - 120 - i * SIRA_ARASI)
    for i, sira in enumerate(sag):
        e += sira(P, P.G + P.dg + 120 + i * SIRA_ARASI)
    return e


def _zincir(uc, kot, ilk_ad=None):
    """Düşey ölçü zinciri ( uc:  sıralı noktalar ).  Kısa parçalar yazısız
    ( yalnız sayı ):  uzun ad parçaya sığmayıp dışarı taşıyor, duvarın
    ölçüsüne biniyordu."""
    out = [_o("dusey", (0, a), (0, b), kot) for a, b in zip(uc, uc[1:])]
    if ilk_ad and len(uc) > 2:
        out[0] = _o("dusey", (0, uc[0]), (0, uc[1]), kot, ilk_ad)
    return out


def _agirlik_rayi_sirasi(P, kot):
    ag, ag_alt, ag_ust = P.g["agirlik"], P.ag_alt, P.ag_ust
    return [
        _o("dusey", (0, 0), (0, ag_alt), kot),
        _o("dusey", (0, ag_alt), (0, ag_alt + ag["h"]), kot, "agirlik_rayi_on"),
        _o(
            "dusey",
            (0, ag_alt + ag["h"]),
            (0, ag_ust - ag["h"]),
            kot,
            "agirlik_ray_arasi",
            kisaltmalar.kodlu("DBGW", ag["ray_arasi"]),
        ),
        _o("dusey", (0, ag_ust - ag["h"]), (0, ag_ust), kot, "agirlik_rayi_arka"),
        _o("dusey", (0, ag_ust), (0, P.D), kot),
    ]


def _civata_sirasi(P, kot):
    """Kabin rayı konsolunun cıvata aralığı — duvara dayanan konsolda."""
    c, ry = P.S["konsol_civata_araligi"], P.ry
    return [
        _o("dusey", (0, ry - c), (0, ry), kot, "civata_on"),
        _o("dusey", (0, ry), (0, ry + c), kot, "civata_arka"),
    ]


def _ray_ekseni_sirasi(P, kot):
    """Kabin ray ekseni ve ardından arka duvara.  Arkadaki ağırlıkta zincir
    ağırlığın rayına bölünür ( LiftDesigner 800 KG:  ray ekseni 850 · kabin
    rayı – ağırlık rayı 970 · 180 ):  kabin rayı ile ağırlık rayı arası
    hiçbir planda ölçülmüyordu."""
    ry = P.ry
    ray_uc = [ry, P.D]
    if not P.ag_yan and P.ey > ry:
        ray_uc = [ry, P.ey, P.D]
    return [_o("dusey", (0, 0), (0, ry), kot, "ray_ekseni")] + _zincir(ray_uc, kot, "kabin_rayi_agirlik_rayi")


def _on_arka_duvar_sirasi(P, kot):
    """Ön ve arka duvar da ölçülür ( üstteki sol · sağ duvar gibi ):  ölçüye
    tıklanınca yalnız o duvarın kalınlığı değişir ( 2 Eki )."""
    D, don, dar = P.D, P.don, P.dar
    return [
        _o("dusey", (0, -don), (0, 0), kot, "duvar_on"),
        _o("dusey", (0, 0), (0, D), kot, "kuyu_derinligi", kisaltmalar.kodlu("SD", D)),
        _o("dusey", (0, D), (0, D + dar), kot, "duvar_arka"),
    ]


def _kabin_derinligi_sirasi(P, kot):
    kd = P.g["kabin"]["derinlik"]
    return [_o("dusey", (0, P.ic_on), (0, P.ic_on + kd), kot, "kabin_derinligi", kisaltmalar.kodlu("CD", kd))]


def _esik_sirasi(P, kot):
    """EŞİKLER  ( kat eşiği · aradaki açıklık · kabin eşiği ):  sağdaki dış
    sıralarda, "KAPI ARASI"nın hemen içinde ( o aralığı böler — LiftDesigner'ın
    kuyu planı da eşikleri "190 · 10 · 90 · 30" diye dışarıda ölçer ).
    Eskiden kapının yanındaki şeritteydi:  kanat cepleri, kasa ve ara kiriş o
    şeridi doldurunca yazılar onların üstüne düşüyordu ( girdi taraması, 4 Eki );
    şerit varsa içeride, yoksa dışarıda koymak da olmadı — girdi oynayınca yer
    değiştiriyor, ölçüye tıklayınca kaynağı bulunamıyordu.
    İç yüzden kapı hattına:  duvar boşluğuna montajda kat eşiğinin taşan
    kısmı, kuyu içine montajda kat kapısı ünitesinin tamamı."""
    KB = P.KB
    hat = "kat_esigi" if P.g["kapi"]["montaj"] == "Duvar boşluğuna" else "kat_kapisi"
    esik = [
        (0.0, KB["hat"], hat),
        (KB["hat"], KB["kabin_esik"][0], "esik_arasi"),
        (KB["kabin_esik"][0], KB["kabin_esik"][1], "kabin_esigi"),
    ]
    return [_o("dusey", (0, bas), (0, son), kot, ad) for bas, son, ad in esik]


def _kapi_arasi_sirasi(P, kot):
    """Kapı arası, kabin ve şase, ardından arka duvara.  Arkadaki ağırlıkta
    zincir ağırlığa bölünür ( LiftDesigner 800 KG:  kabin – ağırlık
    100 · 150 · 105 ):  kabin ile ağırlık arası ( m.5.2.5.5.1 h ) hiçbir
    planda ölçülmüyordu."""
    ic_on, dis_d, D = P.ic_on, P.dis_d, P.D
    kabin_uc = [ic_on + dis_d, D]
    ag_d = P.g["agirlik"]["derinlik"]
    if not P.ag_yan and P.ey - ag_d / 2.0 >= ic_on + dis_d:
        kabin_uc = [ic_on + dis_d, P.ey - ag_d / 2.0, P.ey + ag_d / 2.0, D]
    return [
        _o("dusey", (0, 0), (0, ic_on), kot, "kapi_arasi"),
        _o("dusey", (0, ic_on), (0, ic_on + dis_d), kot, "kabin_ve_sase"),
    ] + _zincir(kabin_uc, kot)


def _kabin_ici_olculeri(P):
    """İÇ — kabin iç genişliği ve panoları  ( kabinin arkasında;  ağırlık
    arkadaysa o şerit dolu olduğu için kabinin içinde, önde ).  Duvar – kabin
    dışı parçaları yok:  üstteki sırada ( KABİN DIŞI zinciri ) zaten ölçülü —
    ISO 129-1, her ölçü bir kez.  8 Eki'ye dek buradaydılar;  ağırlık patenleri
    planda çizilince duvar – kabin yazısı yandaki ağırlıkta sığacak yer
    bulamıyor, iki kat dışarı itiliyordu.
    Arkadaki şerit yazıya yetmiyorsa ( referans proje:  147 mm ) kabinin içinde,
    arka panelin önünde durur — yazı arka duvara taşıyordu."""
    ic_on, dis_d, kx = P.ic_on, P.dis_d, P.kx
    kg = P.g["kabin"]["genislik"]
    arka_serit = P.D - (ic_on + dis_d)
    if not P.ag_yan:
        kab_kot = ic_on + 150
    elif arka_serit >= 90 + 50 + eleman.OLCU_YAZI / 2.0 + 40:
        kab_kot = ic_on + dis_d + 90
    else:
        kab_kot = ic_on + dis_d - 200
    ic_sol, ic_sag = kx - P.dis_g / 2.0, kx + P.dis_g / 2.0
    return [
        _o("yatay", (ic_sol, 0), (kx - kg / 2.0, 0), kab_kot, "kabin_duvari_sol"),
        _o(
            "yatay",
            (kx - kg / 2.0, 0),
            (kx + kg / 2.0, 0),
            kab_kot,
            "kabin_genisligi",
            kisaltmalar.kodlu("CW", kg),
        ),
        _o("yatay", (kx + kg / 2.0, 0), (ic_sag, 0), kab_kot, "kabin_duvari_sag"),
    ]


def _aski_olculeri(P):
    """İÇ — ASKI:  kasnak / nokta aralığı askı elemanlarının hemen yanında,
    kaçıklık ise kabin merkezi ile askı ekseni arasında."""
    if P.duzen not in ("Kabin altı", "Kabin üstü", "Doğrudan") or P.capraz is not None:
        return []
    kx, aski_y, aski_yari = P.kx, P.aski_y, P.aski_yari
    merkez_y = P.ic_on + P.dis_d / 2.0
    e = []
    arasi = None
    if P.duzen != "Doğrudan":  # 1:1'de tek bağlantı:  aralık yok
        aralik = P.aski.get("kasnak_arasi")
        arasi = _o(
            "yatay",
            (kx - aralik / 2.0, 0),
            (kx + aralik / 2.0, 0),
            aski_y - aski_yari - 70,
            "aski_arasi",
            yazi={"x": kx, "y": aski_y - aski_yari - 70 + 50, "aci": 0},
        )
        e.append(arasi)
    kac = aski_y - merkez_y
    if abs(kac) <= 1e-9:
        return e
    kac_x = kx - P.g["kabin"]["genislik"] / 2.0 + 150
    metin = f"{abs(kac):g}"
    w_kac, h_ = eleman.yazi_eni(metin), eleman.OLCU_YAZI
    yazi = {"x": kac_x + 30 + w_kac / 2.0, "y": (aski_y + merkez_y) / 2.0, "aci": 0}
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
                yazi["y"] = max(aski_y, merkez_y) + 25 + h_ / 2.0
    e.append(_o("dusey", (0, aski_y), (0, merkez_y), kac_x, "aski_kacikligi", metin, yazi=yazi))
    return e


def _kabin_kapisi(P):
    """Kabin eşiği, kanatları, cepleri ve kapı mekanizması.

    Kabin kapısı mekanizma kutusu KABİN ÖN YÜZÜNDE durur  ( kapı ile kabin
    arasında;  kullanıcı kararı — referans projenin paftasındaki yerleşimin aynısı ).
    Kapı elemanlarından SONRA:  kanatların örtüsü onu silmesin.
    KESİK:  kutu kabin kapısının üstündedir, planın kesit düzleminin ( kapı
    hizası ) üstünde kalır — kesitin üstündeki parça kesik çizilir ( ISO 128;
    kullanıcı onayı 6 Eki ).  Eskiden düz çiziliyordu, eşiklerin ve kanatların
    üstünden geçen bir kutu gibi duruyordu."""
    S, KB, x0, kg = P.S, P.KB, P.x0, P.kg
    kabin_esigi = eleman.ad(
        eleman.dikdortgen("KABIN", x0, KB["kabin_esik"][0], kg, KB["kabin_esik"][1] - KB["kabin_esik"][0]),
        "kabin_esigi",
    )
    kanatlar, _ = _kanatlar_ve_cepler(P, kabin_esigi, *KB["kabin_esik"], "kabin_kanadi", "kabin_kanat_cebi")
    operator = eleman.ad(
        eleman.dikdortgen(
            "GIZLI",
            x0 + kg / 2.0 - S["kabin_kapisi_kutu_en"] / 2.0,
            P.ic_on - S["kabin_kapisi_kutu_boy"] + 20,
            S["kabin_kapisi_kutu_en"],
            S["kabin_kapisi_kutu_boy"],
        ),
        "kabin_kapisi_operatoru",
    )
    return [kabin_esigi] + kanatlar + [operator]


def _yazilar(P, e):
    """Karşı ağırlığın yazısı.  KABİN ölçüleri ve askı düzeni VERİLER
    tablosunda ( kuyu_plani;  13 Eki — eskiden kabinin içinde "KABİN 1350 x
    1400", "ASKI:  KABİN ALTI · 2:1" yazıyordu );  ölçü zincirlerinin "0"
    sıfır noktaları kalktı ( zincirler duvardan başlar, sıfır okunuyordu )."""
    ag, ex, ag_y = P.g["agirlik"], P.ex, P.ag_y
    if not P.ag_yan:
        e.append(
            eleman.ad(
                eleman.yazi(ex, P.ey - ag["derinlik"] / 2.0 - 45, "KARŞI AĞIRLIK", uslup.NORMAL),
                "agirlik_yazi",
            )
        )
        return
    #  Blok dar ve uzun:  yazı DİK yazılır.  Kasnak bloğun ortasında
    #  durduğu için yazı blok ile kabin rayı arasındaki boşluğa konur;
    #  boşluk dar ise bloğun içine.
    blok_ic = ex + ag["derinlik"] / 2.0 if P.ag_yan == "Sol" else ex - ag["derinlik"] / 2.0
    bos = abs(P.kiris_ic - blok_ic)
    yx = (blok_ic + P.kiris_ic) / 2.0 if bos >= 60 else ex
    metin = "KARŞI AĞIRLIK"
    if bos < 60:
        #  Yazı bloğun içinde, kasnağın çap yazısıyla aynı yerde:  ikisi tek
        #  yazı olur ( eskiden üst üste biniyordu )
        cap = [x for x in e if x.get("ad") == "agirlik_kasnak_yazi"]
        if cap:
            metin += "  " + cap[0]["metin"]
            e.remove(cap[0])
    e.append(eleman.ad(eleman.yazi(yx, ag_y, metin, uslup.NORMAL, aci=90), "agirlik_yazi"))


def _kabin_ici_yazi_adaylari(P, e):
    """Kabinin içindeki yazılar dar yerde yarışır ( kasnak çapı, askı yazısı,
    kabin yazısı, askı kaçıklığı ):  çakışan, sıradaki boş adaya taşınır
    ( girdi taraması, 4 Eki — kaçıklık küçükken ve kabin darken üst üste
    biniyorlardı ).  [ ( yazı, adaylar ) ]"""
    aski_y, aski_yari, kx, ky = P.aski_y, P.aski_yari, P.kx, P.ky
    adaylar = []
    for el in e:
        ad = el.get("ad")
        if ad == "kabin_kasnak_yazi":
            m = el["x"]
            w = eleman.yazi_eni(el["metin"], el["yukseklik"]) / 2.0
            dc_ = (P.aski.get("kasnak_capi") or 0) / 2.0
            adaylar.append(
                (
                    el,
                    [
                        (m, el["y"]),
                        (m, aski_y - aski_yari - 45),
                        (m - dc_ - w - 20, aski_y),
                        (m + dc_ + w + 20, aski_y),
                    ],
                )
            )
        elif ad == "aski_yazi":
            adaylar.append(
                (
                    el,
                    [
                        (el["x"], el["y"]),
                        (el["x"], aski_y + aski_yari + 230),
                        (el["x"], aski_y - aski_yari - 330),
                    ],
                )
            )
        elif ad == "kabin_yazi":
            adaylar.append((el, [(kx, el["y"])] + [(kx, ky + d) for d in (200, -200, 350, -350, 500)]))
        elif el["tip"] == "olcu" and el["metin"].startswith("ASKI KAÇIKLIĞI"):
            adaylar.append((el, _kaciklik_adaylari(el)))
    return adaylar


def _kaciklik_adaylari(el):
    """Askı kaçıklığı ölçüsünün yazısının yerleri:  yerinde, ölçünün iki
    yanında;  bunlar da doluysa çevresinde adım adım ( en yakın önce ):  küçük
    kabinde dört yer de şase dikmesine ya da kasnak yazısına düşüyordu
    ( yazılar büyüyünce, 5 Eki )."""
    y_ = el["yazi"]
    w = eleman.yazi_eni(el["metin"]) / 2.0
    z0, z1 = sorted((el["a"][1], el["b"][1]))
    k_ = el["kot"]
    adim = eleman.OLCU_YAZI / 2.0 + 40
    ek = sorted(
        (
            (y_["x"] + dx * adim, y_["y"] + dy)
            for dx in (0, -1, 1, -2, 2, -3, 3)
            for dy in range(-600, 601, 50)
        ),
        key=lambda a: (a[0] - y_["x"]) ** 2 + (a[1] - y_["y"]) ** 2,
    )
    return [
        (y_["x"], y_["y"]),
        (k_ - 30 - w, (z0 + z1) / 2.0),
        (k_ + 30 + w, z1 + 25 + eleman.OLCU_YAZI / 2.0),
        (k_ + 30 + w, z0 - 25 - eleman.OLCU_YAZI / 2.0),
    ] + ek


def yazi_kutusu(el):
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
                    el["x"] + r * izli.cos(2 * math.pi * i / n),
                    el["y"] + r * izli.sin(2 * math.pi * i / n),
                    el["x"] + r * izli.cos(2 * math.pi * (i + 1) / n),
                    el["y"] + r * izli.sin(2 * math.pi * (i + 1) / n),
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


def olcu_araligi(o):
    """Ölçünün ölçtüğü aralık:  ( yön , baş , son ) — 0,1 mm'ye yuvarlı."""
    j = 0 if o["yon"] == "yatay" else 1
    return (o["yon"], round(min(o["a"][j], o["b"][j]), 1), round(max(o["a"][j], o["b"][j]), 1))


def tekrarlari_at(e):
    """SON ADIM ( cizimler.CIZIMLER ):  kimliksiz ( `ad`sız ) bir ölçü, aynı
    aralığı ölçen başka bir ölçü varsa yazılmaz — ISO 129-1:  her ölçü bir kez
    ( 13 Eki:  gerçek 800 KG kuyu planında üst iki sırada iki "400" ).  Kimlikli
    ölçü kalır:  ölçüye tıklama onu tanır;  iki ayrı parçanın ölçüsü rastlantıyla
    çakışabilir ( ray civatası ile askı kaçıklığı ).  Aynı aralıkta yalnız
    kimliksizler varsa ilki kalır."""
    gruplar = {}
    for el in e:
        if el["tip"] == "olcu":
            gruplar.setdefault(olcu_araligi(el), []).append(el)
    at = set()
    for liste in gruplar.values():
        kimlikli = [o for o in liste if o.get("ad")]
        kalan = kimlikli or liste[:1]
        at |= {id(o) for o in liste if not o.get("ad") and all(o is not k for k in kalan)}
    return [el for el in e if id(el) not in at]


def ondalik_virgul(e):
    """SON ADIM ( cizimler.CIZIMLER ):  yazılardaki ve ölçülerdeki ondalık nokta
    virgül olur ( "AĞIRLIK RAYI 127,5", "+21,00" — kullanıcı 5 Eki ).  Ölçü
    kaynağı ( olcu_kaynagi ) sayıyı ikisinde de tanır."""
    for el in e:
        if el.get("metin"):
            el["metin"] = _ONDALIK.sub(r"\1,\2", el["metin"])
    return e


def alan_yazisi(kutu, satirlar, h=uslup.NORMAL):
    """Bir alanın ( sığınma, çalışma alanı ) adı, alanın İÇİNDE ve ortasında:
    yazı ( maskesiyle — uslup.maske_payi ) kutuya sığmıyorsa satırları bölünür
    ( önce iki boşluktan:  "ÇÖMELME  500 x 700" → "ÇÖMELME", "500 x 700";  sonra
    yalnız harflerden oluşan satır sözcüklerine:  "SIĞINMA ALANI" → "SIĞINMA",
    "ALANI" ), o da sığmazsa kutu uzunsa dikine yazılır;  hiçbiri sığmıyorsa
    ilk biçim kalır.  Satır adımı yazı boyu ve iki maske payı:  satırların
    maskeleri birbirine değmez ( adım h iken etiket ayırıcı alt alta satırları
    birbirine binmiş sayıp dağıtıyordu ).  13 Eki:
    yazı kendi alanının kesikli sınırının üstüne taşıyordu ( kabin üstünde
    "ÇÖMELME  500 x 700" 700'lük kutuda, kuyu üstünde "ÇALIŞMA ALANI" 500'lük
    kutuda ).  [ yazı elemanı ]"""
    pay = uslup.maske_payi(h)
    adim = h + 2 * pay
    bolunmus = [p for s in satirlar for p in s.split("  ")]
    sozcuk = [w for s in bolunmus for w in (s.split(" ") if not re.search(r"\d", s) else [s])]
    eni, boyu = kutu[2] - kutu[0], kutu[3] - kutu[1]
    adaylar = [(s, 0) for s in (list(satirlar), bolunmus, sozcuk)]
    if boyu > eni:
        adaylar += [(s, 90) for s in (list(satirlar), bolunmus, sozcuk)]

    def sigar(sat, aci):
        en, yuk = (eni, boyu) if aci == 0 else (boyu, eni)
        return max(eleman.yazi_eni(s, h) for s in sat) + 2 * pay <= en and len(sat) * adim <= yuk

    sat, aci = next((a for a in adaylar if sigar(*a)), adaylar[0])
    cx, cy = (kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0
    n = len(sat)
    return [
        eleman.ad(
            eleman.yazi(cx, cy + ((n - 1) / 2.0 - j) * adim, s, h)
            if aci == 0
            else eleman.yazi(cx - ((n - 1) / 2.0 - j) * adim, cy, s, h, aci=90),
            "alan_adi",
        )
        for j, s in enumerate(sat)
    ]


def _ust(a, b, pay=4.0):
    """İki kutu ( pay kadar büyütülmüş ) üst üste mi."""
    return a[0] < b[2] + pay and b[0] < a[2] + pay and a[1] < b[3] + pay and b[1] < a[3] + pay


def _kayma_adimlari(menzil, adim, ic=0):
    """Etiketin denenecek kaymaları:  kareli, yakından uzağa ( önce yatay )."""
    return sorted(
        {
            (dx, dy)
            for dx in range(-menzil, menzil + 1, adim)
            for dy in range(-menzil, menzil + 1, adim)
            if max(abs(dx), abs(dy)) > ic
        },
        key=lambda d: (d[0] ** 2 + d[1] ** 2, abs(d[1])),
    )


def _etiket_yeri(kb, maske, k, sorunlu, parca_kutulari, adimlar):
    """Sorunlu etiketin kayması:  ( dx, dy, oklu mu ) ya da None ( yerinde kalır ).

    Maskesi ( uslup.maske_payi ) ya da kutusu kıl payı ( 2 mm'den az ) bir
    kenara değen etiket kâğıtta o kenarı koparır ( 13 Eki ):  az kaydırılır
    ( 100 mm — kâğıtta 5 mm ) — önce maskesi, yoksa kutusu temiz yere;
    bulunamazsa yerinde kalır, uzağa oklu sıçramaz ( kuyu dibinin perde
    yazısı kuyunun dışına itiliyordu ).  Gerçekten binen etiket önce de az
    kaydırılır, olmazsa eskisi gibi en yakın yere ( 300 mm ), o da yoksa oklu
    uzak yere.  Daha uzaktaki temiz yer seçilmez:  etiket adlandırdığı
    parçadan kopuyordu ( kabin üstünde KARŞI AĞIRLIK kabinin içine, ön kesitte
    kuyu duvarının dışına geçiyordu )."""
    itme, yakin, uzak = adimlar
    eski_parca = sum(1 for q in parca_kutulari if _ust(kb, q, 0.0))

    def kayik(dx, dy):
        return (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)

    def yakinda(pay, liste):
        return next(
            (
                (dx, dy)
                for dx, dy in liste[1:]
                if not sorunlu(kayik(dx, dy), pay=pay)
                and sum(1 for q in parca_kutulari if _ust(kayik(dx, dy), q, 0.0)) <= eski_parca
            ),
            None,
        )

    yer = yakinda(maske, itme) or yakinda(0.0, itme)
    if yer is None and not sorunlu(kb, pay=2.0 * k):
        return None
    yer = yer or yakinda(2.0 * k, yakin)
    if yer is not None:
        return yer + (False,)
    yer = next(
        (
            (dx, dy)
            for dx, dy in uzak
            if not sorunlu(kayik(dx, dy)) and not any(_ust(kayik(dx, dy), q, 0.0) for q in parca_kutulari)
        ),
        None,
    )
    return None if yer is None else yer + (True,)


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
    kutular = {id(x): yazi_kutusu(x) for x in yazilar}
    adimlar = (
        _kayma_adimlari(int(100 * k), max(int(10 * k), 1)),
        _kayma_adimlari(int(300 * k), max(int(20 * k), 1)),
        _kayma_adimlari(int(900 * k), max(int(40 * k), 1), int(300 * k)),
    )
    oklar = []
    for el in yazilar:
        if el["tip"] != "yazi":
            continue
        kb = kutular[id(el)]
        obur = [kutular[id(x)] for x in yazilar if x is not el and kutular[id(x)]]

        def sorunlu(kt, obur=obur, pay=2.0 * k):
            #  pay:  kenar denetiminde kutunun küçültülmesi ( eksi:  büyütülmesi )
            return (
                any(_ust(kt, b) for b in obur)
                or any(_ust(kt, d, -2.0 * k) for d in duvarlar)
                or kenarlar.kesisir(kt, pay)
            )

        maske = -uslup.maske_payi(el["yukseklik"])
        if not sorunlu(kb, pay=maske):
            continue
        yer = _etiket_yeri(kb, maske, k, sorunlu, parca_kutulari, adimlar)
        if yer is None:
            continue
        dx, dy, ok = yer
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


def yazilari_coz(e, tasinir, ek_katman=()):
    """tasinir:  [ ( eleman , [ ( x , y ) adayları — ilki şimdiki yer ] ) ].
    Her yazı öbür bütün yazılara ( ölçü yazıları dahil ) binmeyen ilk adaya
    taşınır;  hiçbiri boş değilse yerinde kalır."""

    def kutu_yerde(el, x, y):
        if el["tip"] == "olcu":
            eski = dict(el["yazi"])
            el["yazi"].update(x=x, y=y)
            k = yazi_kutusu(el)
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
        digerleri = [yazi_kutusu(x) for x in e if x is not el and x["tip"] in ("yazi", "olcu")]
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
        cikti.append(
            eleman.ad(eleman.yazi(tx + ox * (O + 90), ty + oy * (O + 90), harf, uslup.HARF), "kesit_harfi")
        )
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
            k = yazi_kutusu(el)
            if k:
                #  Yazı da çerçevenin içinde kalmalı  ( "ASKI KAÇIKLIĞI"
                #  çerçeveye taşıp kesiliyordu ).
                xs += [k[0], k[2]]
                ys += [k[1], k[3]]
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


#  PARÇA ÖRNEKLERİ ( 13 Eki — çizim kalitesi 6. adımı;  DXF'in parça blokları ve
#  ekranın parça vurgusu ):  adı olan parçanın
#  ( elemanın `ad`ı:  kabin_ray, makine_sasesi, kat_kapisi … ) her örneği kendi
#  adlı bloğundadır — AutoCAD'de tıklanınca bütün parça seçilir, adı
#  özelliklerde görünür ( LiftDesigner'ın paftalarında her parça bloktur ).
#  Aynı adlı elemanlar birbirine değiyorsa bir örnektir ( rayın flanşı ve
#  gövdesi );  değmiyorsa ayrı örnek ( iki kabin rayı ).  Blok olmaz:  duvar,
#  tarama, ölçü, yazı, maskelenen çizgiler ( eksen, gizli, halat, alan sınırı … )
#  ve işaretler ( yük kutusu, etiket oku ).  Çizgiler yerinde kalır:  bloğun
#  taban noktası örneğin köşesi, eklendiği yer de orası.
BLOKSUZ_KATMANLAR = set(MASKELI_KATMANLAR) | {"KUYU-DUVAR", "KUYU-IC", "TARAMA", "YUK", "BINA"}
_BLOK_TIPLERI = ("dikdortgen", "cizgi", "daire")
_ORNEK_PAYI = 1.0  # mm:  aynı adlı iki eleman bundan yakınsa aynı örnek


def parca_ornekleri(elemanlar):
    """Blok olacak parça örnekleri:  [ ( ad , [ eleman ] ) ], çizim sırasıyla."""
    gruplar = {}
    for el in elemanlar:
        if el.get("ad") and el["tip"] in _BLOK_TIPLERI and el["katman"] not in BLOKSUZ_KATMANLAR:
            gruplar.setdefault(el["ad"], []).append(el)
    ornekler = []
    for ad, liste in gruplar.items():
        kutular = [sinir([el], _ORNEK_PAYI) for el in liste]
        ornekler += [(ad, [liste[i] for i in kume]) for kume in _degenler(kutular)]
    return ornekler


def _degenler(kutular):
    """Birbirine ( zincirleme ) değen kutuların kümeleri:  [ [ sıra no ] ]."""
    kok = list(range(len(kutular)))

    def bul(i):
        while kok[i] != i:
            kok[i] = kok[kok[i]]
            i = kok[i]
        return i

    for i, a in enumerate(kutular):
        for j in range(i + 1, len(kutular)):
            b = kutular[j]
            if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                kok[bul(i)] = bul(j)
    kume = {}
    for i in range(len(kutular)):
        kume.setdefault(bul(i), []).append(i)
    return list(kume.values())


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


def cerceveli(elemanlar, baslik, olcek=20, pay=300, seritler=(), olcekli=True):
    """Çizimi kendi çerçevesine alır ve altına başlık şeridi ekler.

    Referans projede de her çizim ayrı bir çerçevededir ve altında adı ile ölçeği
    yazar.  Çerçeve ölçüleri de kapsar;  yazılar dışarıda kalmaz.  olcekli:
    başlıkta ölçek yazar mı ( tabloda yazmaz — cizimler.OLCEKSIZ ).
    """
    k = olcek / 20.0  # yazılar paftada 1/20'deki boyda kalır
    etiket = f"{baslik}   1/{olcek:g}" if olcekli else baslik
    x1, y1, x2, y2 = sinir(elemanlar, pay * k)
    serit = 220.0 * k
    #  Künye şeridi başlığı ve sağdaki yazıları taşımalı:  sığmıyorsa
    #  çerçeve iki yana eşit genişler  ( başlık proje adının üstüne biniyordu ).
    #  Başlık kâğıtta 5 mm ( LiftDesigner ):  104 → 140 em · 0,716 / 20
    gerek = (
        (120 + 200 + 120) * k
        + eleman.yazi_eni(etiket, uslup.BASLIK * k)
        + max([eleman.yazi_eni(m, uslup.HARF * k) for m in seritler] or [0])
    )
    if x2 - x1 < gerek:
        fark = (gerek - (x2 - x1)) / 2.0
        x1, x2 = x1 - fark, x2 + fark
    e = list(elemanlar)
    e.append(eleman.dikdortgen("CERCEVE", x1, y1 - serit, x2 - x1, (y2 - y1) + serit))
    e.append(eleman.cizgi("CERCEVE", x1, y1, x2, y1))
    e.append(
        eleman.yazi(
            x1 + 120 * k,
            y1 - serit / 2.0,
            etiket,
            uslup.BASLIK * k,
            hiza="sol",
            katman="CERCEVE",
        )
    )
    for i, metin in enumerate(seritler):
        e.append(
            eleman.yazi(
                x2 - 120 * k,
                y1 - serit / 2.0 - i * 120 * k,
                metin,
                uslup.HARF * k,
                hiza="sag",
                katman="CERCEVE",
            )
        )
    return e


def parcadan_kaydir(e, ek_katman=()):
    """Yazısı bir parçanın üstüne düşen ölçünün yazısı, kendi ölçüsü boyunca
    ( ya da ucunun dışına ) parçaya ve öbür yazılara binmeyen en yakın yere
    taşınır — yazilari_yerlestir'in kaydir'ı gibi, ama yerleşimi bitmiş bir
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
        k = yazi_kutusu(el)
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
        yazilari_coz(e, tasinir, ek_katman=ek_katman)
