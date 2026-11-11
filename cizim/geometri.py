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

import collections
import contextlib
import contextvars
import math
import re
import threading
from dataclasses import dataclass

from cizim import sorunlu
from cizim import izli
from cizim import kisaltmalar
from cizim import eleman
from cizim import uslup
from cizim import girdi
from cizim import parcalar
from cizim import sabitler
from cizim import arka_aski
from cizim import sorun
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


#  Yerinde sabit etiketler:  ayırıcı ( etiketleri_ayir ) kıpırdatmaz — kuyu grubunun
#  ayırma kirişinin adı kirişin içindedir ( kiriş yazılara duvar sayılır — duvar_gibi );
#  kuyu dibinin yük yazısı çerçevesinin içindedir ( kayınca çerçevesi boş kalıyordu:
#  tek kuyunun kuyu dibinde, 2 Kas )
SABIT_ETIKETLER = frozenset(("ayirma_kirisi_adi", "yuk"))

#  Kuyunun İÇİNDE kalması gereken etiketler:  karşı ağırlığın ve kasnakların yazısı.
#  Ayırıcı ( etiketleri_ayir ) bunları kuyunun dışına taşımaz;  dar ağırlığa
#  maskesiz sığmazlarsa kuyunun içinde en yakın boş yere kısa okla taşır.  7 Kas
#  çizim denetimi 5. adımı:  B-B'de dar ağırlığın "KARŞI AĞIRLIK"ı duvarın ötesine
#  ( kot yazılarının yanına ) itiliyordu — taramada 210 / 283 kesit;  BAR 2515
#  planında "ø 400" duvarın dışındaydı.  araclar/karne de bunları sayar
#  ( etiket_kuyu_disinda ).
KUYU_ICI_ETIKETLERI = frozenset(("agirlik_yazi", "agirlik_kasnak_yazi", "kabin_kasnak_yazi"))
#  Parçasına sığmayınca küçük boyda yazılan karşı ağırlık etiketleri ( _dar_agirlik_yazilari )
DAR_AGIRLIK_ETIKETLERI = frozenset(("agirlik_yazi", "agirlik_kasnak_yazi"))
#  Uzağa oklu taşınacaksa önce kuyunun İÇİNDE oklu yer arayan etiketler ( etiketleri_ayir —
#  8 Kas çizim denetimi 8. adımı ):  kuyu üstünde makinenin yanındaki HALAT BAĞLANTISI
#  kuyunun dışına, ölçü zincirlerinin üstüne ya da ön duvarın altına atılıyordu ( oku
#  duvarı ve makineyi boydan kesiyordu;  arkadaki ağırlıkta duvarın ötesine oksuz );
#  kuyunun dışına düşecekse önce içeride oklu yer, yoksa eskisi gibi dışarıda
ICERDE_OKLU_ETIKETLER = frozenset(("halat_baglanti_yazi", "perde_yazi"))


def kuyunun_ici(e):
    """Kuyunun iç yüzleri SW / SD ölçülerinden:  ( yatay aralık , düşey aralık ) —
    kesitte yalnız yatay ( A-A'da SD, B-B'de SW );  ölçü yoksa None."""
    ar = [None, None]
    for o in e:
        if o["tip"] == "olcu" and str(o.get("metin", "")).startswith(("SW", "SD")):
            j = 0 if o["yon"] == "yatay" else 1
            lo, hi = sorted((o["a"][j], o["b"][j]))
            ar[j] = (lo, hi) if ar[j] is None else (min(ar[j][0], lo), max(ar[j][1], hi))
    return None if ar == [None, None] else tuple(ar)


def kuyuda(kutu, kuyu):
    """Kutunun ortası kuyunun içinde mi ( kuyunun_ici;  None:  bilinmiyor — evet )."""
    if kuyu is None:
        return True
    cx, cy = (kutu[0] + kutu[2]) / 2.0, (kutu[1] + kutu[3]) / 2.0
    x, y = kuyu
    return (x is None or x[0] <= cx <= x[1]) and (y is None or y[0] <= cy <= y[1])


def duvar_gibi(x):
    """Yazının içine giremediği kesit:  duvar ( tarama, KUYU-DUVAR ) ve kuyu grubunun
    açık arasındaki ayırma kirişi — duvarın yerindedir;  yazılar oraya, komşu kuyunun
    yerine kaçmasın ( cizim/grup.py )."""
    return x["tip"] in ("tarama", "tarama_tugla") or (
        x["tip"] == "dikdortgen" and (x.get("katman") == "KUYU-DUVAR" or x.get("ad") == "ayirma_kirisi")
    )


def yazilari_yerlestir(elemanlar, h=eleman.OLCU_YAZI, kaydir=False, kopuk=True):
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
    Y = _YaziYerleri(elemanlar, h, kaydir, kopuk)
    siralar = {}
    for el in elemanlar:
        if el["tip"] == "olcu" and "yazi" not in el:
            siralar.setdefault((el["yon"], round(el["kot"], 3)), []).append(el)
    #  BAŞKA SIRALARIN YAZILARI da sayılır ( yeri verilmiş ölçü yazıları ve bu
    #  çağrıda yerleşenler ):  sığmayan yazı ucun dışına çıkınca köşede öbür
    #  yöndeki sıranın yazısına biniyordu ( kuyu planının sağ üst köşesinde iki
    #  "DUVAR 150" — yazılar büyüyünce, 5 Eki ).
    Y.dolu = [yazi_kutusu(el) for el in elemanlar if el["tip"] == "olcu" and "yazi" in el]
    Y.dolu_yon = [el["yon"] for el in elemanlar if el["tip"] == "olcu" and "yazi" in el]
    for (yon, kot), liste in siralar.items():
        i = 0 if yon == "yatay" else 1
        liste.sort(key=lambda q: min(q["a"][i], q["b"][i]))
        yerlesen = []  # ( kat, bas, son )
        for n, q in enumerate(liste):
            bas, son = sorted((q["a"][i], q["b"][i]))
            w = eleman.yazi_eni(q["metin"], h)
            Y.kendi = {id(s) for s in Y.cizgiler.get(id(q), ())}
            Y.simdiki = q
            aday = Y.adaylar(yon, kot, liste, n, i, bas, son, w)
            kat, orta = Y.sec(yon, kot, aday, yerlesen, bas, son, w)
            yerlesen.append((kat, orta - w / 2.0, orta + w / 2.0))
            Y.dolu.append(Y.kutu(yon, kot, kat, orta, w))
            Y.dolu_yon.append(yon)
            capraz = Y.capraz(kot, kat)
            q["yazi"] = (
                {"x": orta, "y": capraz, "aci": 0.0, "h": h}
                if yon == "yatay"
                else {"x": capraz, "y": orta, "aci": 90.0, "h": h}
            )


#  Ölçü yazısının harfleriyle başka bir ölçünün çizgisi arasındaki en az pay
#  ( 1/20'de çizim birimi — kâğıtta 0,1 mm;  ölçekle büyür ).  Dış sıranın ucu
#  iç sıranın yazısının 0,22 mm üstünde biter ( uslup.SAPLAMA ):  pay bundan
#  küçük kalmalı, yoksa iç sıranın her yazısı dış sıranın ucuna "biner".
CIZGI_PAYI = 2.0


def _sirada_biner(yerlesen, kat, orta, w, k):
    """Yazı sırasında aynı kattaki bir yazıya biner mi ( 25 mm payla )."""
    return any(
        kt == kat and orta - w / 2.0 < s + 25 * k and b < orta + w / 2.0 + 25 * k for kt, b, s in yerlesen
    )


class _YaziYerleri:
    """yazilari_yerlestir'in ortak durumu:  yazı boyu ( h ) ve ölçeği ( k —
    1/50'de yazı ve aralıklar büyür ), kaydir, parça kutuları ve kenarları,
    öbür ölçülerin çizgileri, yazının kaçtığı engeller, dolu yazı kutuları."""

    def __init__(self, elemanlar, h, kaydir, kopuk=True):
        self.h = h
        self.k = h / eleman.OLCU_YAZI
        self.kaydir = kaydir
        #  kopuk:  dışarı itilmiş yazı çizgisine yaklaştırılır ( _iyilestir ) —
        #  yazıları başka yerleşimlerin dayanağı olan çizimde kapalı ( kuyu
        #  dibinin yük kutuları ve perde yazısı;  kabin üstünde sığınma
        #  ölçüsünün yerini seçen denemeler )
        self.kopuk = kopuk
        #  Parça kenarları ( parca_kenarlari ):  yazı maskelidir, bir kenarın
        #  üstüne düşerse kenarı siler — kuyu planında kabin duvarının "75"i
        #  kabinin iki çizgisinin üstündeydi ( 5 Eki ).
        self.kenarlar = KenarIzgarasi(parca_kenarlari(elemanlar))
        #  Ölçülerin çizgileri ve uçları ( olcu_cizgileri;  sıfır boylu ölçü
        #  çizilmez ):  yazı başka bir ölçünün çizgisine konmaz — kendininkiler
        #  ( kendi ) sayılmaz.  26 Eki:  sonra çizilen çizgi yazının üstünden
        #  geçiyordu ( kabin üstünde sığınma alanının düşey ölçüsü "215"in
        #  içinden ), önce çizileni yazının maskesi kesiyordu ( kuyu dibinde
        #  "162,5" "615"in çizgisinde ) — araclar/karne:  olcu_yaziyi_kesiyor.
        self.cizgiler = {
            id(o): olcu_cizgileri(o, self.k)
            for o in elemanlar
            if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6
        }
        self.olcu_izgarasi = KenarIzgarasi([s for c in self.cizgiler.values() for s in c])
        self.kendi = set()
        #  Yazının MASKESİ kendinden önce çizilen ölçülerin çizgisini siler
        #  ( OlcuIzgarasi;  simdiki:  yerleşen ölçü — sırası onunkinden küçük
        #  olanlar önce çizilir )
        self.olculer = OlcuIzgarasi(elemanlar)
        self.tum_olculer = [o for o in elemanlar if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6]
        self.simdiki = None
        self.esik = MASKE_ESIGI * 20.0 * self.k
        #  Duvarlar ( taramalı kesit ):  yazı çizgiden kaçarken içlerine girmez
        self.duvarlar = [sinir([x]) for x in elemanlar if duvar_gibi(x)]
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
        self.dolu_yon = []
        #  Çizimin parçalarının sınırı:  açıklamalı yazı onun dışına taşmasın
        #  ( yazi_cizimden_tasiyor — _yumusak_iyilestir yazıyı daha çok taşırmaz )
        cizim_parcalari = [
            x
            for x in elemanlar
            if x["tip"] not in ("olcu", "yazi", "ok") and x.get("katman") not in CIZIM_DISI_KATMANLAR
        ]
        self.cizim_siniri = sinir(cizim_parcalari) if cizim_parcalari else None
        #  Zincirler ( aynı yön ve kot ):  yazının ortası başka bir aralığın
        #  hizasına düşmesin ( yanlis_aralikta — 6 Kas çizim denetimi )
        self.hatlar = collections.defaultdict(list)
        for o in self.tum_olculer:
            j = 0 if o["yon"] == "yatay" else 1
            self.hatlar[(o["yon"], round(o["kot"], 1))].append(
                (min(o["a"][j], o["b"][j]), max(o["a"][j], o["b"][j]), id(o))
            )

    def capraz(self, kot, kat):
        """Yazının ortasının ölçü çizgisine dik konumu:  çizginin dışında, kat
        kat;  kat -1:  çizginin İÇ yanında, bitişik ( TERS — _ters_serbest )."""
        dis = -1.0 if kot < 0 else 1.0
        if kat < 0:
            return kot - dis * 50.0 * self.k
        return kot + dis * (50.0 + eleman.KAT_ARALIGI * kat) * self.k

    def _ters_serbest(self, yon, kot, bas, son, pay=100.0):
        """Çizginin iç yanı yazıya açık mı:  o yanda aynı yönde başka bir ölçü
        sırası yok ( iç yandaki yazı öbür sıranın yazılarının şeridine düşer,
        okuyan onu o sıranın ölçüsü sanar — 5 Eki ).  bas – son:  ölçünün
        aralığı ya da ( yanlış aralık / bitişik yazıda ) yalnız yazının kendisi:
        iç sıra o hizada yoksa yazı onun ölçüsü sanılmaz ( kuyu planının eşik
        zincirinde "30" — iç yandaki CD sırası 90'ın üstünden başlıyor )."""
        dis = -1.0 if kot < 0 else 1.0
        i = 0 if yon == "yatay" else 1
        pay = pay * self.k
        return not any(
            o is not self.simdiki
            and o["yon"] == yon
            and 1e-6 < dis * (kot - o["kot"]) < 1.6 * SIRA_ARASI * self.k
            and min(o["a"][i], o["b"][i]) < son + pay
            and bas - pay < max(o["a"][i], o["b"][i])
            for o in self.tum_olculer
        )

    def kutu(self, yon, kot, kat, orta, w):
        h = self.h
        c = self.capraz(kot, kat)
        return (
            (orta - w / 2.0, c - h / 2.0, orta + w / 2.0, c + h / 2.0)
            if yon == "yatay"
            else (c - h / 2.0, orta - w / 2.0, c + h / 2.0, orta + w / 2.0)
        )

    def _yazi_yeri(self, yon, kot, kat, orta, w):
        """( x, y, en, h, aci ) — uslup kutularının girdisi."""
        c = self.capraz(kot, kat)
        return (orta, c, w, self.h, 0.0) if yon == "yatay" else (c, orta, w, self.h, 90.0)

    def cizgiye_biner(self, yon, kot, kat, orta, w):
        """Yazının harfleri ( gövdesi, CIZGI_PAYI büyütülerek ) başka bir
        ölçünün çizgisine ya da ucuna biner mi."""
        g = uslup.govde_kutusu(*self._yazi_yeri(yon, kot, kat, orta, w))
        p = CIZGI_PAYI * self.k
        g = (g[0] - p, g[1] - p, g[2] + p, g[3] + p)
        return any(id(s) not in self.kendi and kenar_kesisir(s, g) for s in self.olcu_izgarasi.adaylar(g))

    def silinen(self, yon, kot, kat, orta, w):
        """Yazının maskesinin sildiği parça kenarı boyu ( uslup.maske_kutusu )."""
        m = uslup.maske_kutusu(*self._yazi_yeri(yon, kot, kat, orta, w))
        return sum(kutudaki_boy(s, m) for s in self.kenarlar.adaylar(m))

    def duvarda(self, yon, kot, kat, orta, w):
        """Yazı bir duvarın içine giriyor mu ( 2 mm kıl payıyla )."""
        kb_ = self.kutu(yon, kot, kat, orta, w)
        p = 2.0 * self.k
        return any(
            kb_[0] < d[2] - p and d[0] < kb_[2] - p and kb_[1] < d[3] - p and d[1] < kb_[3] - p
            for d in self.duvarlar
        )

    def engelde(self, kutu):
        """Yazı bir engelin ( parça;  kaydir'da kapı ) içine düşüyor mu."""
        return any(
            kutu[0] < p[2] and p[0] < kutu[2] and kutu[1] < p[3] and p[1] < kutu[3] for p in self.engeller
        )

    def biner(self, yon, kot, kat, orta, w):
        """Yazı bir engele ya da parça kenarına biner mi."""
        kutu = self.kutu(yon, kot, kat, orta, w)
        return self.engelde(kutu) or self.kenarlar.kesisir(kutu, 2.0 * self.k)

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
        o da yoksa yalnız ilkini sağlayan.  Seçilen yerin kusuru varsa daha
        iyisi aranır ( _iyilestir ).  ( kat, orta )"""
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
        secilen = temiz or yazisiz or ilk or aday[-1]
        return self._iyilestir(yon, kot, aday, yerlesen, bas, son, w, secilen)

    def yanlis_aralik(self, yon, kot, orta):
        """Yazının ortası kendi aralığının dışında, aynı zincirin başka bir
        aralığının hizasında mı ( yanlis_aralikta — araclar/karne:  okuyan onu
        o aralığın ölçüsü sanar )."""
        j = 0 if yon == "yatay" else 1
        o = self.simdiki
        if min(o["a"][j], o["b"][j]) - 1e-6 <= orta <= max(o["a"][j], o["b"][j]) + 1e-6:
            return False
        pay = ARALIK_PAYI * 20.0 * self.k
        return any(
            kim != id(o) and lo + pay < orta < hi - pay for lo, hi, kim in self.hatlar[(yon, round(kot, 1))]
        )

    def bitisik(self, yon, kot, kat, orta, w):
        """Aynı doğrultudaki bir ölçü yazısına BITISIK_ESIGI'nden yakın mı
        ( bitisik_yazilar — araclar/karne:  iki yazı tek söz gibi okunur )."""
        kb_ = self.kutu(yon, kot, kat, orta, w)
        i = 0 if yon == "yatay" else 1
        d = 1 - i
        c = (kb_[d] + kb_[d + 2]) / 2.0
        esik = BITISIK_ESIGI * 20.0 * self.k
        for y, b in zip(self.dolu_yon, self.dolu):
            if y != yon or abs((b[d] + b[d + 2]) / 2.0 - c) > 0.25 * self.h:
                continue
            if -0.5 * self.h < max(b[i] - kb_[i + 2], kb_[i] - b[i + 2]) < esik:
                return True
        return False

    def kusurlar(self, yon, kot, kat, orta, w):
        """Yerin kusurları ( araclar/karne'nin ölçü yazısına bakan kuralları ):
        ( harflerine başka ölçünün çizgisi biniyor , maskesinin sildiği parça
        kenarı , maskesinin sildiği önceki ölçü çizgisi , örttüğü uç , başka
        aralığın hizasında , bitişik )."""
        m = uslup.maske_kutusu(*self._yazi_yeri(yon, kot, kat, orta, w))
        boy, uc = self.olculer.silinen(m, self.simdiki)
        return (
            self.cizgiye_biner(yon, kot, kat, orta, w),
            self.silinen(yon, kot, kat, orta, w),
            boy,
            uc,
            self.yanlis_aralik(yon, kot, orta),
            self.bitisik(yon, kot, kat, orta, w),
        )

    def _kusurlu(self, d, kat):
        """Giderilecek kusurlar ( karnenin eşiğini aşan ):  ( çizgi , kenar ,
        ölçü , kopuk — yazı bir kat ya da daha dışarıda:  araclar/karne
        yazi_cizgisinden_kopuk , yanlış aralık , bitişik — 6 Kas ).  Maskeninkiler yalnız kaydir'da:  öbür çizimlerde yazıların yeri
        başka yerleşimlerin dayanağıdır — kuyu dibinde yük kutuları ölçü
        yazılarına göre konur, maskesi için kayan "565" onları kuyunun dışına
        itiyordu ( 26 Eki )."""
        cizgi, kenar, boy, uc, aralik, bitisik = d
        if not self.kaydir:
            return (cizgi, False, False, self.kopuk and kat >= 1, aralik, bitisik)
        return (cizgi, kenar > self.esik, boy > self.esik or uc > 0, self.kopuk and kat >= 1, aralik, bitisik)

    def _iyilestir(self, yon, kot, aday, yerlesen, bas, son, w, secilen):
        """Seçilen yerin kusurları giderilir:  önce SERT kusurlar ( çizgi, maske,
        kopuk — _sert_iyilestir, 26 – 27 Eki ), sonra yazının hangi aralığa ait
        olduğu ( yanlış aralık, bitişik — _yumusak_iyilestir, 6 Kas ).  İkinci
        aşama birincinin giderdiği hiçbir kusuru geri getirmez:  komşu aralığa
        kaymış bir yazı ( kabin üstünde "70", kuyu dibinde "162,5" ) maskesinden
        kaçmak için oradaysa yerinde kalır."""
        secilen = self._sert_iyilestir(yon, kot, aday, yerlesen, bas, son, w, secilen)
        return self._yumusak_iyilestir(yon, kot, aday, yerlesen, bas, son, w, secilen)

    def _sert_iyilestir(self, yon, kot, aday, yerlesen, bas, son, w, secilen):
        """Seçilen yerin kusuru varsa ( 26 Eki:  harflerine başka ölçünün
        çizgisi biniyor, maskesi parça kenarını ya da önce çizilen ölçünün
        çizgisini siliyor ) seçimin şartlarını sağlayan ve HİÇBİR ölçüde kötü
        olmayan, kusuru daha az yer:  çizgisinden daha uzak değil ( kat —
        araclar/karne:  kopuk ), duvarın ve engelin içine girmiyor, maskesinin
        sildikleri kötüleşmiyor ( _maske_kotulesmez ).  Önce bütün kusurlardan kurtulan yer,
        yoksa kusuru azalan;  kendi ölçüsünün içinde kalan kaymalar, sonra
        adaylar sırasıyla ( sıranın ucunun dışı ), sonra öbür kaymalar.  Yoksa
        seçilen ( kusursuz yazının yeri hiç değişmez ).  Yalnız çizgi şartıyla
        aransaydı yazı kuyu dibinde duvarın içine, kabin üstünde iki kat
        dışarı kaçıyordu.  Yalnız SERT kusurlar ( _kusurlu'nun ilk dördü )."""
        d0 = self.kusurlar(yon, kot, *secilen, w)
        k0 = self._kusurlu(d0, secilen[0])[:4]
        if not any(k0):
            return secilen
        kat0, duvarda0 = secilen[0], self.duvarda(yon, kot, *secilen, w)
        engelde0 = self.engelde(self.kutu(yon, kot, *secilen, w))
        #  Yalnız maskenin kusuru varsa 20 mm'lik adım yeter ( kabin üstünde
        #  sığınma ölçüsünün yeri 16 kez denenerek seçilir — süre )
        kaymalar = self._kaymalar(bas, son, w, (20.0, 5.0) if k0[0] else (20.0,))
        icinde = [a for a in kaymalar if bas <= a[1] - w / 2.0 and a[1] + w / 2.0 <= son]
        #  KOPUK ( 27 Eki, kalite 4. adımı ):  dışarı itilmiş yazıya önce çizgisine
        #  bitişik yerler — kendi ölçüsünün üstünde, iç yan açıksa onun da ( kapı
        #  kesitinde eşik zincirinin "60"ı ve "EŞİK ARASI 30"u zincirin altında
        #  havada kalıyordu )
        bitisik = []
        if k0[3]:
            orta0 = (bas + son) / 2.0
            yerler = [orta0] + [o for _k, o in self._kaymalar(bas, son, w) if _k == 0]
            yerler = [o for o in yerler if bas - 1e-6 <= o <= son + 1e-6]
            katlar = (0, -1) if self._ters_serbest(yon, kot, bas, son) else (0,)
            bitisik = [(kat, o) for kat in katlar for o in yerler]
        uygun = []
        for kat, orta in bitisik + icinde + list(aday) + kaymalar:
            if kat > kat0 or _sirada_biner(yerlesen, kat, orta, w, self.k):
                continue
            kb_ = self.kutu(yon, kot, kat, orta, w)
            if (
                self.yaziya_biner(kb_)
                or self.kenara_biner(kb_)
                or (self.duvarda(yon, kot, kat, orta, w) and not duvarda0)
                or (self.engelde(kb_) and not engelde0)
            ):
                continue
            #  Kusurlar sırayla, yenisi çıkan aday erkenden elenir ( süre )
            cizgi = self.cizgiye_biner(yon, kot, kat, orta, w)
            if cizgi and not k0[0]:
                continue
            kenar = self.silinen(yon, kot, kat, orta, w)
            if not k0[1] and kenar > d0[1] + 1e-6:
                continue
            m = uslup.maske_kutusu(*self._yazi_yeri(yon, kot, kat, orta, w))
            d = (cizgi, kenar) + self.olculer.silinen(m, self.simdiki) + (False, False)
            k = self._kusurlu(d, kat)[:4]
            if any(a > b for a, b in zip(k, k0)) or sum(k) >= sum(k0):
                continue
            if not _maske_kotulesmez(d0[1:], d[1:], k0[1:3], k[1:3], self.esik):
                continue
            if not any(k):
                return (kat, orta)
            uygun.append((kat, orta))
        return uygun[0] if uygun else secilen

    def tasma(self, yon, kot, kat, orta, w):
        """Yazının çizimin parçalarından ( CIZIM_DISI_KATMANLAR dışındakiler ) kendi
        doğrultusunda dışarı taşan boyu ( araclar/karne:  yazi_cizimden_tasiyor )."""
        P = self.cizim_siniri
        if P is None:
            return 0.0
        k = self.kutu(yon, kot, kat, orta, w)
        j = 0 if yon == "yatay" else 1
        return max(P[j] - k[j], k[j + 2] - P[j + 2], 0.0)

    def _yumusak_iyilestir(self, yon, kot, aday, yerlesen, bas, son, w, secilen):
        """YANLIŞ ARALIK / BİTİŞİK ( 6 Kas ):  sığmayan ara ölçünün yazısı komşu
        aralığın hizasındaydı ( kuyu planının eşik zincirinde "30" 90'ın yanında,
        "150"ye bitişik ).  Daha az yanlış aralık / bitişik kusurlu yer:  önce
        kendi aralığının ortası — iç yan yazının hizasında açıksa çizginin iç
        yanı ( kat −1;  iç sıra yalnız yazının hizasında aranır ), sonra çizginin
        dışı —, sonra kendi aralığı boyunca, sonra adaylar ve öbür kaymalar.  Yeni
        yer hiçbir SERT kusuru ( çizgi, maske, kopuk ) artırmaz, maskesinin
        sildikleri kötüleşmez, çizimden daha çok taşmaz, duvara / engele girmez;
        yoksa yazı yerinde kalır."""
        #  Yalnız sayı yazıları:  açıklamalı uzun yazılar ( "İLK KONSOL 500", "MAKİNE
        #  345" ) 3. adımda yeniden yazılır — burada kaydırılınca B-B'de karşı
        #  ağırlığın etiketi yerinden oluyordu
        if ACIKLAMALI.search(self.simdiki.get("metin", "")):
            return secilen
        d0 = self.kusurlar(yon, kot, *secilen, w)
        k0 = self._kusurlu(d0, secilen[0])
        if not any(k0[4:]):
            return secilen
        kat0, duvarda0 = secilen[0], self.duvarda(yon, kot, *secilen, w)
        engelde0 = self.engelde(self.kutu(yon, kot, *secilen, w))
        tasma0 = self.tasma(yon, kot, *secilen, w)
        #  Yanlış aralıktan çıkmak:  yazının ortası kendi aralığında ya da zincirin
        #  bütün aralıklarının dışında ( sınırın payını kıl payı aşmak sayılmaz —
        #  A-A'da "MAKİNE 345" 0,26 mm kayıp kuralın payının altına düşüyordu )
        pay = ARALIK_PAYI * 20.0 * self.k
        hat = [(lo, hi) for lo, hi, kim in self.hatlar[(yon, round(kot, 1))] if kim != id(self.simdiki)]

        def aralikta(orta):
            return bas - 1e-6 <= orta <= son + 1e-6 or not any(lo - pay < orta < hi + pay for lo, hi in hat)

        orta0 = (bas + son) / 2.0
        ters = self._ters_serbest(yon, kot, orta0 - w / 2.0, orta0 + w / 2.0, pay=25.0)
        kaymalar = self._kaymalar(bas, son, w, (20.0, 5.0))
        kendi = [(kat, orta0) for kat in ((-1, 0) if ters else (0,))] + [
            (kat_, o) for kat_, o in kaymalar if kat_ == 0 and bas - 1e-6 <= o <= son + 1e-6
        ]
        for kat, orta in kendi + list(aday) + kaymalar:
            if kat > kat0 or _sirada_biner(yerlesen, kat, orta, w, self.k):
                continue
            kb_ = self.kutu(yon, kot, kat, orta, w)
            if (
                self.yaziya_biner(kb_)
                or self.kenara_biner(kb_)
                or (self.duvarda(yon, kot, kat, orta, w) and not duvarda0)
                or (self.engelde(kb_) and not engelde0)
                or self.tasma(yon, kot, kat, orta, w) > tasma0 + 1e-6
            ):
                continue
            if k0[4] and not aralikta(orta):
                continue
            d = self.kusurlar(yon, kot, kat, orta, w)
            k = self._kusurlu(d, kat)
            if any(a > b for a, b in zip(k[:4], k0[:4])) or sum(k[4:]) >= sum(k0[4:]):
                continue
            if not _maske_kotulesmez(d0[1:], d[1:], k0[1:3], k[1:3], self.esik):
                continue
            return (kat, orta)
        return secilen

    def _kaymalar(self, bas, son, w, adimlar=(20.0, 5.0)):
        """Yazının kendi ölçüsü boyunca yerleri ( kat, orta ):  uçların hemen
        dışına kadar, önce az kayan, sonra dış katlar;  önce 20 mm, sonra 5 mm adım."""
        k = self.k
        orta0 = (bas + son) / 2.0
        yari = (son - bas + w) / 2.0 + 30 * k
        out = []
        for adim in (a * k for a in adimlar):
            kaymalar = sorted(
                {
                    (kat_, d * adim * sgn)
                    for kat_ in (0, 1, 2)
                    for d in range(1, int(yari / adim) + 1)
                    for sgn in (-1, 1)
                },
                key=lambda a: (abs(a[1]), a[0]),
            )
            out += [(kat_, orta0 + kay) for kat_, kay in kaymalar]
        return out

    def _kaydir(self, yon, kot, yerlesen, bas, son, w):
        """Adayların hepsi bir parçaya biniyor ( kuyunun içinden geçen sıralar ):
        yazı kendi ölçüsü boyunca kayar ( _kaymalar ).  Adım önce 20 mm, sonra
        5 mm:  iki kenar arasındaki boşluk yazıya ancak yetiyorsa kaba adım onu
        atlayabilir ( kabin üstünde sığınma alanının arkadaki 70 mm'lik yerinin
        yazısı tavanın kenarı ile konsol plakası arasındaki 5 mm'lik pencereyi
        kaçırıyordu — şase 240, 20 Eki;  300'de adım tesadüfen pencereye
        düşüyordu ).  ( kat, orta ) ya da None"""
        for kat_, orta in self._kaymalar(bas, son, w):
            if _sirada_biner(yerlesen, kat_, orta, w, self.k):
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
                metin = sorun.Sorun(
                    f"{kim} kanat cebi {_CEP_ENGELLERI[o['ad']]} çarpıyor:  açılan kanatlar "
                    f"kuyuda yer bulamıyor — {girdi.RK_ONERISI}, {girdi.kapi_onerisi(g['kapi'].get('tip'))}.",
                    (c["ad"], o["ad"]),
                    "kuyu_plani",
                    fark=sorun.ayrik(
                        (c["x"], c["y"], c["x"] + c["g"], c["y"] + c["d"]),
                        (o["x"], o["y"], o["x"] + o["g"], o["y"] + o["d"]),
                        -1e-6,
                    ),
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
    #  Sorunlu kipte ( cizim/sorunlu.py ) ilk hatada durulmaz:  çare bulucu gizli
    #  kalan sorunları da görür ( uclar/care_uclari.py ).  Kip kapalıyken aynı.
    if not hata or sorunlu.acik():
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


def agirlik_rayi_eksenleri(g, S=None):
    """Yandaki karşı ağırlığın iki rayının eksenleri ( y — ön duvardan ):  ayırma
    kirişinin hesabı ( hesap/motor/uygulama/ayirma_kirisi ) kuvvetin yerini okur."""
    P = _plan_olculeri(g, S or sabitler.sabitler(g.get("_cizim_sabitleri")))
    h = g["agirlik"]["h"]
    return P.ag_alt + h / 2.0, P.ag_ust - h / 2.0


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


def plan(g, cizim_sabitleri=None, kapi_duzeyi=True, duvar_boslugu=None, komsu=None, cit=(), olcu_alti=None):
    """Kuyu planının elemanları  ( liste ).

    kapi_duzeyi:  plan kat kapısı hizasından kesilir ( C-C ) — ön duvar kapı
    boşluğunun iki yanında iki parçadır, tarama boşluktan geçmez.  Kapının
    üstünden / altından kesilen planlar ( kuyu dibi, kuyu üstü, delik planı )
    duvarı kesintisiz alır:  False.
    duvar_boslugu:  ön duvarın boşluklu olup olmadığı ( verilmezse
    kapi_duzeyi ) — kabin üstü planı kesit kotu kaba boşluğun içinde kalırsa
    boşluklu ister ( kabin_ustu.kapi_gorunusu ).

    KUYU GRUBU ( cizim/grup.py — grubun planında asansörün kendi parçası ):
    komsu:  komşu kuyunun yanı ( "Sol" · "Sağ" ) — o yandaki ölçü sıraları
    öbür yana geçer, kesit işaretleri yazılmaz ( grubun planında iki asansörün
    A-A'sı olurdu ).  cit:  komşu kuyunun yerini kapatan elemanlar — yazılar
    oraya kaçmasın diye en baştan listededir ( çağıran sonra atar ).
    olcu_alti:  alttaki ölçü sıralarının en üstü ( grubun kuyuları aynı
    sıralarda ölçülür — menteşeli kapının yayı birininkini aşağı iter ).

    Eleman SIRASI çizimin parçasıdır ( sonraki öncekinin üstüne çizilir;
    altın kayıtlar sırayı da tutar ):  bölümler aşağıdaki sırayla eklenir."""
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    P = _plan_olculeri(g, S)
    e = list(cit) + _duvarlar(P, kapi_duzeyi if duvar_boslugu is None else duvar_boslugu)
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

    alt = _olcu_alti(P, e)
    if olcu_alti is not None:
        alt = min(alt, olcu_alti)
    e += _ust_olculer(P)
    e += _alt_olculer(P, alt)
    e += _yan_olculer(P, komsu)
    e += _kabin_ici_olculeri(P)
    e += _aski_olculeri(P)
    e += _kabin_kapisi(P)
    _yazilar(P, e)
    yazilari_yerlestir(e, kaydir=True)
    adaylar = _kabin_ici_yazi_adaylari(P, e)
    if adaylar:
        yazilari_coz(e, adaylar)
    parcadan_kaydir(e, ek_katman=("AGIRLIK",))
    if komsu is None:
        e += kesit_isaretleri(g, e)
    return e


def _olcu_alti(P, e):
    """Alttaki ölçü sıralarının en üstü:  ön duvarın ( ve bina duvarının )
    dışı, menteşeli kapıda açılma yayının da altı."""
    return min([-P.don - P.S["bina_duvari"]] + [el["y"] for el in e if el.get("ad") == "kapi_acilisi"])


def olcu_alti(g):
    """Kuyu planının alttaki ölçü sıralarının en üstü ( plan() ile aynı ) —
    grubun planı kuyuların sıralarını aynı yere koyar ( cizim/grup.py )."""
    P = _plan_olculeri(g, sabitler.sabitler(g.get("_cizim_sabitleri")))
    return _olcu_alti(P, _kat_kapisi(P, True))


def _duvarlar(P, bosluklu):
    """Duvarlar ( tarama yalnız duvar kesitinde ).  Boşluklu ön duvar kat
    kapısının kaba boşluğunun iki yanındadır ( girdi.kaba_bosluk — giriş
    görünüşüyle aynı;  duvar boşluğuna monte kapıda kasa da boşluktadır ).
    Kuyu grubunun açık arasında ( kuyu.acik_yan — kopru._acik_ara ) o yanda
    duvar yoktur:  yerinde ayırma kirişi."""
    G, D, ds, dg, don, dar = P.G, P.D, P.ds, P.dg, P.don, P.dar
    acik = P.g["kuyu"].get("acik_yan")
    if bosluklu:
        on = [(-ds, -don, P.b0 + ds, don), (P.b1, -don, G + dg - P.b1, don)]
    else:
        on = [(-ds, -don, G + ds + dg, don)]
    yanlar = [y for y, ad in (((-ds, 0, ds, D), "Sol"), ((G, 0, dg, D), "Sağ")) if ad != acik]
    e = []
    for x, y, g_, d_ in on + [(-ds, D, G + ds + dg, dar)] + yanlar:
        if g_ <= 1e-6:
            continue
        e.append(eleman.dikdortgen("TARAMA", x, y, g_, d_, tip="tarama"))
        e.append(eleman.dikdortgen("KUYU-DUVAR", x, y, g_, d_))
    e.append(eleman.dikdortgen("KUYU-IC", 0, 0, G, D))
    if acik:
        e += ayirma_kirisi(P.g, -ds if acik == "Sol" else G, ds if acik == "Sol" else dg, D)
    return e


#  TEK KUYUNUN ORTAK ÇİZİMİ ( cizim/grup.py ):  asansörün kuyu dibi, kabin üstü,
#  kuyu üstü planı kuyunun ortak çizimine giriyorsa ( komsulu bloğunda ) komşu
#  asansör bellidir:  yanı ( "Sol" · "Sağ" ), çizimde yer kaplayan elemanlarının
#  kutuları ( asansörün koordinatında ) ve çitin başladığı x ( komşunun bölmesinin
#  ortası ).  Çizim kurulurken bunlar engeldir ( cit ):  yük kutuları, etiketler
#  komşunun parçasına, yazısına konmaz, onun öbür yarısına kaçmaz;  engeller
#  çizimden en sonda atılır ( citsiz ).  Komşu yandaki ölçü sıraları öbür yana
#  grupta geçer ( grup.yan_olculeri_tasi ).
CIT = "CIT"
_CIT_ENI = 20000.0
_KOMSU = contextvars.ContextVar("komsu", default=None)


@contextlib.contextmanager
def komsulu(yan, cit_x, engel=(), siki=True):
    """siki:  komşunun bölmesi ( kuyunun içi ve ön / arka duvarı, kirişin öbür
    yüzünden ) de kapalı — asansörün yazısı komşunun bölmesine düşmesin;  yalnız
    kuyunun önü ve arkası komşunun ortasına kadar açık."""
    j = _KOMSU.set({"yan": yan, "cit_x": cit_x, "engel": tuple(engel), "siki": siki})
    try:
        yield
    finally:
        _KOMSU.reset(j)


def komsu_yani(g=None):
    """Asansörün çizimi kuyunun ortak çizimine giriyorsa komşunun yanı;  yoksa None."""
    k = _KOMSU.get()
    return k and k["yan"]


def cit(g):
    """Komşu asansörün yerini kapatan engeller ( komsulu ) — [ eleman ] ya da boş."""
    k = _KOMSU.get()
    if not k:
        return []
    ku = g["kuyu"]
    x0 = k["cit_x"] if k["yan"] == "Sağ" else k["cit_x"] - _CIT_ENI
    y0 = -ku["duvar_on"] - _CIT_ENI
    e = [eleman.dikdortgen(CIT, x0, y0, _CIT_ENI, ku["derinlik"] + 2 * _CIT_ENI)]
    if k["siki"]:
        x0 = ku["genislik"] + ku["duvar_sag"] if k["yan"] == "Sağ" else -ku["duvar_sol"] - _CIT_ENI
        e.append(
            eleman.dikdortgen(
                CIT, x0, -ku["duvar_on"], _CIT_ENI, ku["duvar_on"] + ku["derinlik"] + ku["duvar_arka"]
            )
        )
    e += [eleman.dikdortgen(CIT, a, b, c - a, d - b) for a, b, c, d in k["engel"]]
    return [eleman.ad(x, "cit") for x in e]


def sag_sira(g, i):
    """Kuyunun sağındaki i. düşey ölçü sırasının kotu ( duvardan dışarı );  tek
    kuyunun ortak çiziminde sağ komşuysa sıra solda ( komşunun yerine düşmesin,
    yük kutuları ve tablo yerini bilsin )."""
    k = g["kuyu"]
    if komsu_yani(g) == "Sağ":
        return -k["duvar_sol"] - 120 - i * SIRA_ARASI
    return k["genislik"] + k["duvar_sag"] + 120 + i * SIRA_ARASI


def citsiz(e):
    return [x for x in e if x.get("katman") != CIT]


def grup_perdesi(g):
    """Kuyu grubunun açık arasında iki kuyu dibinin arasındaki perde
    ( m.5.2.5.5.2.1 ) planda:  aranın ortasında, ön duvardan arka duvara — bir
    kuyu dibinden ötekine geçilemesin;  adı perdenin boyunca.  Açık ara yoksa boş."""
    k = g["kuyu"]
    yan = k.get("acik_yan")
    if not yan:
        return []
    x = -k["duvar_sol"] / 2.0 if yan == "Sol" else k["genislik"] + k["duvar_sag"] / 2.0
    return [eleman.ad(eleman.cizgi("PERDE", x, 0, x, k["derinlik"]), "grup_perdesi")]


def grup_perdesi_adi(e, h=uslup.NORMAL, metinler=("ASANSÖRLER ARASI PERDE", "PERDE")):
    """Perdenin ( grup_perdesi ) adı boyunca, öbür yazılar ( etiket, ölçü yazısı,
    yük kutusu ) ve oklar yerleştikten sonra ( kuyu dibinde yük kutuları en sonda —
    ad önce konunca kutulara yer kalmıyordu ):  ortaya en yakın boş yer;  uzun ad
    sığmazsa kısası, o da sığmazsa ad yazılmaz.  [ yazı ] ya da boş."""
    perde = next((p for p in e if p.get("ad") == "grup_perdesi"), None)
    if perde is None:
        return []
    x, y0, y1 = perde["x1"], min(perde["y1"], perde["y2"]), max(perde["y1"], perde["y2"])
    dolu = [sinir([o]) for o in e if o["tip"] == "yazi" or o.get("ad") in ("yuk_oku", "yuk_kutusu", "yuk")]
    dolu += [yazi_kutusu(o) for o in e if o["tip"] == "olcu" and o.get("yazi")]
    for metin in metinler:
        L = eleman.yazi_eni(metin, h)
        orta = (y0 + y1) / 2.0
        for c in sorted(range(int(y0 + L / 2.0), int(y1 - L / 2.0) + 1, 20), key=lambda c: abs(c - orta)):
            k = (x - h / 2.0 - 10, c - L / 2.0 - 10, x + h / 2.0 + 10, c + L / 2.0 + 10)
            if not any(k[0] < d[2] and d[0] < k[2] and k[1] < d[3] and d[1] < k[3] for d in dolu if d):
                return [eleman.ad(eleman.yazi(x, c, metin, h, aci=90), "grup_perdesi_adi")]
    return []


def ayirma_kirisi(g, x, h, D):
    """Kuyu grubunun açık arasındaki AYIRMA KİRİŞİ planda ( cizim/grup.py ):  NPU
    gövdesi yatay — üstten görünen gövdesi ara boyunca ( h:  kirişin yüksekliği ),
    ön duvardan arka duvara;  adı ve ölçüsü kiriş boyunca ( sığmazsa yalnız
    ölçüsü ).  Konsollar gibi kesitin altındadır, görünür çizilir."""
    npu = g["proje"]["ayirma_kirisi"]
    metin = next(
        (m for m in (f"AYIRMA KİRİŞİ  NPU {npu}", f"NPU {npu}") if eleman.yazi_eni(m) <= D - 200),
        f"NPU {npu}",
    )
    return [
        eleman.dikdortgen("KONSOL", x, 0, h, D, ad="ayirma_kirisi"),
        eleman.ad(eleman.yazi(x + h / 2.0, D / 2.0, metin, aci=90), "ayirma_kirisi_adi"),
    ]


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
    #  PLAKA DUVAR İLE RAY ARASINDA:  boşluk konsol eninden darsa plaka boşluk
    #  kadardır ( 15 Eki:  hep 55 çiziliyor, dar boşlukta raya ve patene biniyordu );
    #  ray duvara dayalıysa ( < 1 mm ) plaka yok, tek sac biçimi aşağıda.
    en = min(S["konsol_kabin_en"], abs(arka - duvar_x))
    kx0 = duvar_x - en if yon > 0 else duvar_x
    plaka = eleman.dikdortgen(
        "KONSOL",
        kx0,
        ry - S["konsol_kabin_boy"] / 2.0,
        max(en, 1.0),
        S["konsol_kabin_boy"],
        ad="plaka",
    )
    e = [plaka]
    if en >= S["konsol_civata_capi"]:
        for cy in (ry - S["konsol_civata_araligi"], ry + S["konsol_civata_araligi"]):
            e.append(eleman.daire("CIVATA", kx0 + en / 2.0, cy, S["konsol_civata_capi"] / 2.0))
    #  KONSOL KOLU:  plakayı rayın arkasına bağlar ( zarf — mantık ).
    #  ÇİZİLEN:  duvar konsolu + ray konsolu ( parcalar.konsol_cifti_bicimi ),
    #  plakanın ve kolun kapsadığı dikdörtgende ( duvardan ray arkasına,
    #  plakanın boyunca ).  Kolun zarfı dar kalır:  geniş zarfta kuyu dibi
    #  gergi kasnağı ( ray ortasına hizalı, ray arkasından 1,5 mm taşar )
    #  konsolla "çakışıyor" sayılıyordu — gergi raya bağlıdır, arkasına geçmez.
    kol_bas = min(arka, kx0 + en) if yon < 0 else min(arka, kx0)
    kol_son = max(arka, kx0 + en) if yon < 0 else max(arka, kx0)
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
    #  TIRNAKLAR:  rayın tabanını ray konsolunun dik ayağına bastırır;  somun
    #  sacın arkasında.  Boşluk somuna yetmiyorsa ( dar boşlukta tek sac —
    #  eşik 0, 15 Eki ) cıvata sacın saplamasıdır, somun çizilmez:  29 Eki
    #  rastgele taramada ray arkası duvardan 13 mm, somun duvara 5 mm giriyordu.
    tirnak = _tirnaklar(arka, ry, kr["b"], kr["h"], -yon, parcalar.konsol_tipi(kr["b"])[3], yatay=True)
    if tirnak and (
        tirnak[0]["x"] < duvar_x - 1e-6 if yon < 0 else tirnak[0]["x"] + tirnak[0]["g"] > duvar_x + 1e-6
    ):
        tirnak = _tirnaklar(arka, ry, kr["b"], kr["h"], -yon, None, yatay=True)
    return e + tirnak


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


def _yan_olculer(P, komsu=None):
    """YANLAR — kuyu derinliği boyunca.  Sıra listesi duvardan dışarı
    doğrudur;  ağırlık yandaysa kendi zinciri O YANDA, duvara en yakın
    sırada durur  ( konsol kotları ağırlığın yanında okunur );  kabin rayı
    konsolunun cıvata aralığı duvara dayanan konsolun yanında.
    komsu:  kuyu grubunda komşu kuyunun yanı — o yanın sıraları öbür yanın
    sıralarının dışına geçer ( LiftDesigner'ın grup planı gibi )."""
    if P.ag_yan == "Sol":
        sol, sag = [_agirlik_rayi_sirasi], [_civata_sirasi]
    elif P.ag_yan == "Sağ":
        sol, sag = [_civata_sirasi], [_agirlik_rayi_sirasi]
    else:
        sol, sag = [], [_civata_sirasi]
    sol += [_ray_ekseni_sirasi]
    sag += [_kabin_derinligi_sirasi, _esik_sirasi, _kapi_arasi_sirasi, _on_arka_duvar_sirasi]
    if komsu == "Sağ":
        sol, sag = sol + sag, []
    elif komsu == "Sol":
        sol, sag = [], sag + sol
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
    return adaylar


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


def _yazi_yeri(el):
    """( x , y , en , h , aci , hiza ) — yazının ya da ölçü yazısının;  ölçünün
    yazısı yoksa None."""
    if el["tip"] == "olcu":
        y = el.get("yazi")
        if not y:
            return None
        h = y.get("h", eleman.OLCU_YAZI)
        return y["x"], y["y"], eleman.yazi_eni(el["metin"], h), h, y.get("aci") or 0.0, "orta"
    h = el["yukseklik"]
    return el["x"], el["y"], eleman.yazi_eni(el["metin"], h), h, el.get("aci") or 0.0, el.get("hiza", "orta")


def maske_kutusu(el):
    """Yazının ( ya da ölçü yazısının ) MASKESİNİN kutusu:  PDF'in zemin rengiyle
    örttüğü dikdörtgen ( uslup.maske_kutusu ).  yazi_kutusu'ndan geniştir —
    her yanda 0,125 em, alt uzantılı harflerin yanında 0,19 em daha;  maskenin
    altında kalan parça kenarı kâğıtta kopuk çıkar."""
    yer = _yazi_yeri(el)
    return None if yer is None else uslup.maske_kutusu(*yer)


def govde_kutusu(el):
    """Yazının büyük harf gövdesinin kutusu ( uslup.govde_kutusu ) — maskesiz."""
    yer = _yazi_yeri(el)
    return None if yer is None else uslup.govde_kutusu(*yer)


def olcu_cizgileri(o, k=1.0):
    """Ölçünün çizilen doğru parçaları:  ölçü çizgisi, iki uçta kısa uzatma
    çizgisi ve eğik çizgi ( uslup.olcu_uclari — ekran ve PDF'in çizdiği;
    yazı yerleşimi ve kalite karnesi aynı parçalara bakar )."""
    if o["yon"] == "yatay":
        bas, son, kot = o["a"][0], o["b"][0], o["kot"]
        out = [(bas, kot, son, kot)]
    else:
        bas, son, kot = o["a"][1], o["b"][1], o["kot"]
        out = [(kot, bas, kot, son)]
    for (a, b), (c, d) in uslup.olcu_uclari(o["yon"], bas, son, kot, k):
        out += [(*a, *b), (*c, *d)]
    return out


def cizgiye_binen_yazilar(e, k=1.0, pay=None):
    """Harflerinden ( gövdesi pay kadar büyütülmüş — verilmezse CIZGI_PAYI )
    başka bir ölçünün çizgisi ya da ucu geçen ölçü yazıları:  [ ( yazının
    ölçüsü , o yazıda en uzun parçası olan ölçü , boyu ) ].  Sonra çizilen
    çizgi yazının üstünden geçer, önce çizileni yazının maskesi keser:  ikisi
    de kusurdur ( yazilari_yerlestir kaçınır;  araclar/karne sayar )."""
    p = CIZGI_PAYI * k if pay is None else pay
    olculer = [o for o in e if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6]
    sahip = {}
    for o in olculer:
        for s in olcu_cizgileri(o, k):
            sahip[id(s)] = (s, o)
    izgara = KenarIzgarasi([s for s, _ in sahip.values()])
    out = []
    for o in olculer:
        g = govde_kutusu(o)
        if g is None:
            continue
        g = (g[0] - p, g[1] - p, g[2] + p, g[3] + p)
        boy = {}
        for s in izgara.adaylar(g):
            q = sahip[id(s)][1]
            if q is not o and (b := kutudaki_boy(s, g)) > 0.0:
                boy[id(q)] = max(boy.get(id(q), 0.0), b)
        if boy:
            q = max(olculer, key=lambda q: boy.get(id(q), 0.0))
            out.append((o, q, boy[id(q)]))
    return out


#  Maskenin sildiği çizginin kusur sayıldığı boy ( kâğıtta mm — araclar/karne
#  aynı eşikle sayar ):  daha kısası yazının kenarına sürtünmedir
MASKE_ESIGI = 0.3


class OlcuIzgarasi:
    """Ölçü çizgilerinin ( yalnız ölçü çizgisi — uçları değil ) ızgarası,
    çizim sırasıyla:  bir yazının MASKESİNİN kendinden ÖNCE çizilen ölçülerde
    sildiği ( silinen ).  Ölçüler öğe sırasıyla, etiketler hepsinden sonra
    çizilir ( pdf.ciz · svg · dxf ):  ölçü yazısı yalnız önceki ölçüleri,
    etiket bütün ölçüleri siler.  Sıfır boylu ölçü çizilmez."""

    def __init__(self, e):
        olculer = [o for o in e if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6]
        self.sira = {id(o): i for i, o in enumerate(olculer)}
        self.cizgiler = [
            (o["a"][0], o["kot"], o["b"][0], o["kot"])
            if o["yon"] == "yatay"
            else (o["kot"], o["a"][1], o["kot"], o["b"][1])
            for o in olculer
        ]
        self.sahip = {id(s): i for i, s in enumerate(self.cizgiler)}
        self.izgara = KenarIzgarasi(self.cizgiler)

    def silinen(self, m, yazi=None):
        """Maskenin ( m ) sildiği:  ( bir ölçünün çizgisinden en uzun silinen boy ,
        örtülen uç — ölçünün sınırı — sayısı );  yazi:  maskenin sahibi ( ölçü
        ise yalnız ondan önce çizilenler sayılır )."""
        once = self.sira.get(id(yazi), len(self.cizgiler))
        boy, uc = 0.0, 0
        for s in self.izgara.adaylar(m):
            if self.sahip[id(s)] >= once:
                continue
            boy = max(boy, kutudaki_boy(s, m))
            uc += sum(1 for px, py in ((s[0], s[1]), (s[2], s[3])) if m[0] < px < m[2] and m[1] < py < m[3])
        return boy, uc


def olcu_yazisi_olcutleri(e, k=1.0):
    """Ölçü yazılarının yerleşimini karşılaştırmak için:  ( harflerine başka
    ölçünün çizgisi binen yazı sayısı , yazıların kendi çizgilerine dik
    uzaklıkları toplamı , maskelerin sildiği parça kenarı boyu toplamı ) —
    araclar/karne'nin ölçü yazısına bakan kuralları ( çizgi, kopuk, maske )."""
    kenarlar = KenarIzgarasi(parca_kenarlari(e))
    uzak = silinen = 0.0
    for o in e:
        y = o.get("yazi") if o["tip"] == "olcu" else None
        if not y:
            continue
        uzak += abs(y["y"] - o["kot"]) if o["yon"] == "yatay" else abs(y["x"] - o["kot"])
        m = maske_kutusu(o)
        silinen += sum(kutudaki_boy(s, m) for s in kenarlar.adaylar(m))
    return len(cizgiye_binen_yazilar(e, k)), uzak, silinen


#  ÖLÇÜ YAZISININ HANGİ ARALIĞA AİT OLDUĞU ( 6 Kas çizim denetimi — araclar/karne:
#  yazi_yanlis_aralikta, yazi_bitisik;  cikti/devir/CIZIM_DENETIMI_PLANI.md ).
#  Aynı zincirin ( aynı yön ve kot ) başka bir aralığının hizasındaki yazı okuyana
#  o aralığın ölçüsü gibi görünür:  kuyu planının ön duvar zincirinde "30" 90'ın
#  yanındaydı, A-A'nın tepesinde "MAKİNE 345" 250'nin.  Kendi aralığına sığmayan
#  yazı ucun ötesine ya da çizginin öbür yanına konur ( ISO 129-1 ).  Pay kâğıtta mm.
ARALIK_PAYI = 0.3
#  Açıklamalı yazı:  iki harf yan yana ( "İLK KONSOL 500", "SW2200" — yalnız sayı
#  değil );  araclar/karne'nin taşma kuralı da bunu kullanır
ACIKLAMALI = re.compile(r"[^\W\d_]{2}")
#  Çizimin sınırına ( yazının taşması ) sayılmayan katmanlar:  yazılar, ölçüler,
#  eksen, kesit işareti, çerçeve, seviye, uyarı, yük, açılış yayı
CIZIM_DISI_KATMANLAR = frozenset(
    ("OLCU", "YAZI", "EKSEN", "KESIT", "CERCEVE", "SEVIYE", "UYARI", "YUK", "ACILIS")
)
#  Aynı doğrultudaki iki ölçü yazısı arası bundan azsa ( kâğıtta mm ) tek söz gibi
#  okunur:  "ŞASE 140 MAKİNE 345", "60 EŞİK ARASI 30" ( 2,5 mm yazıda sözcük arası
#  0,7, harf eni 1,5 mm ).
BITISIK_ESIGI = 2.0


def adli_olcu_metni(adlar, deger, boy, k=1.0):
    """Ölçünün yazısı:  adıyla ( "ŞASE 1100" ) — ad kendi aralığına sığıyorsa
    ( yerleştiricinin ölçütü:  yazı eni ≤ aralık − 20k;  k = ölçek / 20 ), sığmıyorsa
    yalnız değer ( 6 Kas çizim denetimi 3. adımı:  28 mm'lik "İLK KONSOL 500" 10 mm'lik
    aralığından taşıp çizimin altına sarkıyordu, "ŞASE 140 MAKİNE 345" tek söz gibiydi ).
    adlar:  sırayla denenir ( uzundan kısaya ).  deger:  sayı ( :g )."""
    for ad in adlar:
        metin = f"{ad} {deger:g}"
        if eleman.yazi_eni(metin, eleman.OLCU_YAZI * k) <= boy - 20.0 * k:
            return metin
    return f"{deger:g}"


def _yazili_olculer(e):
    return [o for o in e if o["tip"] == "olcu" and o.get("yazi") and o.get("uzunluk", 1.0) >= 1e-6]


def yanlis_aralikta(e, olcek=20.0):
    """Yazısı kendi aralığının dışında, aynı zincirin başka bir aralığının
    hizasında olan ölçüler:  [ ( ölçü , hizasındaki ölçü ) ]."""
    hatlar = collections.defaultdict(list)
    for o in e:
        if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6:
            hatlar[(o["yon"], round(o["kot"], 1))].append(o)
    pay = ARALIK_PAYI * olcek
    out = []
    for o in _yazili_olculer(e):
        j = 0 if o["yon"] == "yatay" else 1
        c = o["yazi"]["x" if j == 0 else "y"]
        if min(o["a"][j], o["b"][j]) - 1e-6 <= c <= max(o["a"][j], o["b"][j]) + 1e-6:
            continue
        for p in hatlar[(o["yon"], round(o["kot"], 1))]:
            if p is not o and min(p["a"][j], p["b"][j]) + pay < c < max(p["a"][j], p["b"][j]) - pay:
                out.append((o, p))
                break
    return out


def bitisik_yazilar(e, olcek=20.0):
    """Aynı doğrultuda ( yön, açı, dik konum ) arası BITISIK_ESIGI'nden az iki
    ölçü yazısı:  [ ( ölçü , ölçü , boşluk — kâğıtta mm ) ].  Üst üste binenler
    ( yazı yazıya — kalite kapısı ) sayılmaz."""
    kutular = [(o, yazi_kutusu(o)) for o in _yazili_olculer(e)]
    out = []
    for i, (o, a) in enumerate(kutular):
        j = 0 if o["yon"] == "yatay" else 1
        d = 1 - j
        for p, b in kutular[i + 1 :]:
            if p["yon"] != o["yon"] or abs(o["yazi"]["aci"] - p["yazi"]["aci"]) > 1e-6:
                continue
            h = min(o["yazi"]["h"], p["yazi"]["h"])
            if abs((a[d] + a[d + 2]) - (b[d] + b[d + 2])) / 2.0 > 0.25 * h:
                continue
            bosluk = max(b[j] - a[j + 2], a[j] - b[j + 2])
            if -0.5 * h < bosluk < BITISIK_ESIGI * olcek:
                out.append((o, p, bosluk / olcek))
    return out


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


def kutudaki_aralik(s, kutu):
    """Doğru parçasının ( ax, ay, bx, by ) kutunun içinde kalan kısmı:  parametre
    aralığı ( t0 , t1 ), 0 ≤ t0 < t1 ≤ 1 — kutuya girmiyorsa None."""
    x0, y0, x1, y1 = kutu
    ax, ay, bx, by = s
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
    return (t0, t1) if t1 > t0 else None


def kutudaki_boy(s, kutu):
    """Doğru parçasının kutunun içinde kalan boyu ( maskenin sildiği çizgi )."""
    a = kutudaki_aralik(s, kutu)
    return 0.0 if a is None else (a[1] - a[0]) * math.hypot(s[2] - s[0], s[3] - s[1])


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

    def adaylar(self, kutu):
        """Kutunun düştüğü hücrelerin kenarları, her biri bir kez."""
        h, gorulen = self.h, set()
        for i in range(int(kutu[0] // h), int(kutu[2] // h) + 1):
            for j in range(int(kutu[1] // h), int(kutu[3] // h) + 1):
                for s_ in self.d.get((i, j), ()):
                    if id(s_) not in gorulen:
                        gorulen.add(id(s_))
                        yield s_


#  Türkçe ondalık ayırıcı virgüldür:  yalnız tek noktalı sayılar ( "1022.5" ,
#  "+21.00" );  madde numaraları ( "m.5.2.6.3.2.4" ) değişmez.
_ONDALIK = re.compile(r"(?<![\d.,])(\d+)\.(\d+)(?![\d.])")


def olcu_araligi(o):
    """Ölçünün ölçtüğü aralık:  ( yön , baş , son ) — 0,1 mm'ye yuvarlı."""
    j = 0 if o["yon"] == "yatay" else 1
    return (o["yon"], round(min(o["a"][j], o["b"][j]), 1), round(max(o["a"][j], o["b"][j]), 1))


#  Rastlantısal küçük aralık ( gerçek mm ):  kimliksiz zincir ölçüsü bundan kısaysa
#  komşusuyla birleşir ( kalite 4. adımı, 27 Eki ) — ÇİZİM KABULÜ.  CAKISIK'tan
#  kısası çakışan iki noktadır, birleşmez:  ölçü kaynağı girdiyi 1 mm oynatır;
#  çakışık nokta ayrılınca doğan 1 mm'lik parça komşusuna sessizce katılırsa
#  kaynağın kırığı gizlenir, türev ile oynatma ayrışır ( kuyu üstünde "200" —
#  test_olcu_turevi;  ayrılan parça ayrı ölçü olarak zincirin yapısını değiştirir,
#  çakışma diye tanınır ).
KUCUK_ARALIK = 20.0
CAKISIK = 1.5


def _kendi_yazisi(o):
    """Ölçünün yazısı ölçülen değerin kendisi mi ( kodsuz, sözsüz )."""
    return o.get("metin") == f"{o['uzunluk']:g}"


def kucukleri_birlestir(e):
    """SON ADIM ( cizimler.CIZIMLER ):  zincirde iki nokta rastlantıyla birbirine
    çok yakın düşünce kâğıtta milimetrelik, anlamsız bir ölçü çıkıyordu ( delik
    planında "4", gerçek 1022'nin kuyu dibinde "5" ).  Kimliksiz, kuralsız,
    yazısı yalnız değeri olan ve KUCUK_ARALIK'tan kısa bir ölçü, aynı sırada
    ucunu paylaşan böyle bir komşusuyla birleşir ( komşusu uzar, yazısı kendi
    ölçüsünün yeni ortasına kayar ).  Anlamlı küçük ölçüler ( kabin duvarı
    "15", korkuluğun içeri alınması ) kimlikli ya da kurallıdır, dokunulmaz."""

    def serbest(o):
        return o["tip"] == "olcu" and not o.get("ad") and not o.get("kural") and _kendi_yazisi(o)

    at = set()
    for o in e:
        if not (serbest(o) and CAKISIK < o["uzunluk"] < KUCUK_ARALIK) or id(o) in at:
            continue
        i = 0 if o["yon"] == "yatay" else 1
        bas, son = sorted((o["a"][i], o["b"][i]))
        komsular = [
            q
            for q in e
            if q is not o
            and id(q) not in at
            and serbest(q)
            and q["yon"] == o["yon"]
            and abs(q["kot"] - o["kot"]) < 1e-6
            and q["uzunluk"] >= KUCUK_ARALIK
            and (abs(max(q["a"][i], q["b"][i]) - bas) < 1e-6 or abs(min(q["a"][i], q["b"][i]) - son) < 1e-6)
        ]
        if not komsular:
            continue
        q = max(komsular, key=lambda q: q["uzunluk"])
        qb, qs = sorted((q["a"][i], q["b"][i]))
        yb, ys = min(qb, bas), max(qs, son)
        kayma = (yb + ys - qb - qs) / 2.0
        a, b = list(q["a"]), list(q["b"])
        a[i], b[i] = yb, ys
        q["a"], q["b"] = tuple(a), tuple(b)
        q["uzunluk"] = ys - yb
        q["metin"] = f"{q['uzunluk']:g}"
        if q.get("yazi"):
            q["yazi"] = dict(q["yazi"], **{"x" if i == 0 else "y": q["yazi"]["x" if i == 0 else "y"] + kayma})
        at.add(id(o))
    return [el for el in e if id(el) not in at]


def tekrarlari_at(e):
    """SON ADIM ( cizimler.CIZIMLER ):  kimliksiz ( `ad`sız ) bir ölçü, aynı
    aralığı ölçen başka bir ölçü varsa yazılmaz — ISO 129-1:  her ölçü bir kez
    ( 13 Eki:  gerçek 800 KG kuyu planında üst iki sırada iki "400" ).  Kimlikli
    ölçü kalır:  ölçüye tıklama onu tanır;  iki ayrı parçanın ölçüsü rastlantıyla
    çakışabilir ( ray civatası ile askı kaçıklığı ).  Aynı aralıkta yalnız
    kimliksizler varsa ilki kalır.  Kendi zincirinin ORTASINDAKİ ölçü atılmaz:
    iki yanında aynı sıradan ölçü varken atılınca zincir kopuyordu ( 29 Eki
    rastgele tarama — kuyu üstü:  0 · 490 · 690 · 740 | 890 · 2400 );  ucundaki
    tekrar eskisi gibi atılır."""
    gruplar, uclar = {}, collections.Counter()
    for el in e:
        if el["tip"] == "olcu":
            gruplar.setdefault(olcu_araligi(el), []).append(el)
            yon, a, b = olcu_araligi(el)
            for u in (a, b):
                uclar[(yon, round(el["kot"], 3), u)] += 1

    def ortada(o):
        yon, a, b = olcu_araligi(o)
        return all(uclar[(yon, round(o["kot"], 3), u)] >= 2 for u in (a, b))

    at = set()
    for liste in gruplar.values():
        kimlikli = [o for o in liste if o.get("ad")]
        kalan = kimlikli or liste[:1]
        at |= {id(o) for o in liste if not o.get("ad") and all(o is not k for k in kalan) and not ortada(o)}
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


def _etiket_yeri(kb, maske, k, cakisir, parca_kutulari, adimlar, olcu_siler=lambda dx, dy: False):
    """Sorunlu etiketin kayması:  ( dx, dy, oklu mu ) ya da None ( yerinde kalır ).

    Maskesi ( uslup.maske_payi ) ya da kutusu kıl payı ( 2 mm'den az ) bir
    kenara değen etiket kâğıtta o kenarı koparır ( 13 Eki ):  az kaydırılır
    ( 100 mm — kâğıtta 5 mm ) — önce maskesi, yoksa kutusu temiz yere;
    bulunamazsa yerinde kalır, uzağa oklu sıçramaz ( kuyu dibinin perde
    yazısı kuyunun dışına itiliyordu ).  Gerçekten binen etiket önce de az
    kaydırılır, olmazsa eskisi gibi en yakın yere ( 300 mm ), o da yoksa oklu
    uzak yere.  Daha uzaktaki temiz yer seçilmez:  etiket adlandırdığı
    parçadan kopuyordu ( kabin üstünde KARŞI AĞIRLIK kabinin içine, ön kesitte
    kuyu duvarının dışına geçiyordu ).  Oklu uzak yerde maskesi bir ölçünün
    çizgisini ya da ucunu da silmez ( olcu_siler ( dx , dy ) — 8 Kas çizim
    denetimi 8. adımı:  kuyu üstünde makinenin yanındaki HALAT BAĞLANTISI
    kuyunun dışında sağdaki ölçü zincirlerinin üstüne düşüyordu ).  Yakın yerde
    aranmaz:  orada etiket parçasının yanında kalır, maskesi sonra
    _maskeden_kacir'la temizlenir."""
    itme, yakin, uzak = adimlar
    eski_parca = sum(1 for q in parca_kutulari if _ust(kb, q, 0.0))

    def kayik(dx, dy):
        return (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)

    def yakinda(pay, liste):
        return next(
            (
                (dx, dy)
                for dx, dy in liste[1:]
                if not cakisir(kayik(dx, dy), pay=pay)
                and sum(1 for q in parca_kutulari if _ust(kayik(dx, dy), q, 0.0)) <= eski_parca
            ),
            None,
        )

    yer = yakinda(maske, itme) or yakinda(0.0, itme)
    if yer is None and not cakisir(kb, pay=2.0 * k):
        return None
    yer = yer or yakinda(2.0 * k, yakin)
    if yer is not None:
        return yer + (False,)
    yer = next(
        (
            (dx, dy)
            for dx, dy in uzak
            if not cakisir(kayik(dx, dy))
            and not any(_ust(kayik(dx, dy), q, 0.0) for q in parca_kutulari)
            and not olcu_siler(dx, dy)
        ),
        None,
    )
    if yer is None:
        #  Uzakta hiçbir parçanın içinde olmayan yer de yoksa ( kuyunun iç kutusu
        #  da parça sayılır:  kuyu üstünde makinenin yanındaki HALAT BAĞLANTISI
        #  kuyunun dışına, duvarın ötesine atılıyordu;  duvar 370 mm'yi geçince
        #  orası da duvara değdi, yazı makinenin üstünde kaldı — 21 Eki, BAR
        #  2515 ):  yakın aramanın kuralıyla ( eskisinden daha çok parçanın içine
        #  girmeyen ) en yakın temiz yer — yerinde kalıp çizgilere binmektense.
        yer = next(
            (
                (dx, dy)
                for dx, dy in uzak
                if not cakisir(kayik(dx, dy))
                and sum(1 for q in parca_kutulari if _ust(kayik(dx, dy), q, 0.0)) <= eski_parca
                and not olcu_siler(dx, dy)
            ),
            None,
        )
    return None if yer is None else yer + (True,)


def _dar_agirlik_yazilari(e, k):
    """Karşı ağırlığın kısa etiketleri ( DAR_AGIRLIK_ETIKETLERI ) normal boyda maskesi parçanın
    kenarını siliyor, küçük boyda ( uslup.KUCUK — 1,8 mm ) silmiyorsa küçük yazılır;  küçük boyda
    da siliyorsa normal kalır, ayırıcı taşır ( hepsini birlikte küçültünce "KARŞI AĞIRLIK"
    tavanın kenarında kalıyordu ) — 9 Kas çizim denetimi 8. adımı, kullanıcı
    kararı:  dik yazının maskesi 82, kasnak 75–80, "KARŞI AĞIRLIK"ın yeri 60–86 mm."""
    yazilar = [x for x in e if x["tip"] == "yazi" and x.get("ad") in DAR_AGIRLIK_ETIKETLERI]
    if not yazilar:
        return
    kenarlar = KenarIzgarasi(parca_kenarlari(e))
    esik = MASKE_ESIGI * 20.0 * k
    oran = uslup.KUCUK / uslup.NORMAL

    def siler(x):
        m = maske_kutusu(x)
        return sum(kutudaki_boy(s, m) for s in kenarlar.adaylar(m)) > esik

    def kucuk_temiz(x):
        y = dict(x, yukseklik=x["yukseklik"] * oran)
        return not siler(y)

    for x in [x for x in yazilar if siler(x) and kucuk_temiz(x)]:
        x["yukseklik"] *= oran


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
    _dar_agirlik_yazilari(e, k)
    #  Parçalar ( etiket içlerine yeniden girmez ) ve duvarlar ( içinde durmaz )
    parca_kutulari = [
        sinir([x])
        for x in e
        if (x["tip"] == "dikdortgen" and x.get("katman") not in MASKELI_KATMANLAR)
        or x["tip"] in ("tarama", "tarama_tugla")
    ]
    duvarlar = [sinir([x]) for x in e if duvar_gibi(x)]
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
    oklar, oklu = [], set()
    kuyu = kuyunun_ici(e)
    olculer = OlcuIzgarasi(e)
    olcu_esigi = MASKE_ESIGI * 20.0 * k
    for el in yazilar:
        if el["tip"] != "yazi" or el.get("ad") in SABIT_ETIKETLER:
            continue
        kb = kutular[id(el)]
        obur = [kutular[id(x)] for x in yazilar if x is not el and kutular[id(x)]]

        def cakisir(kt, obur=obur, pay=2.0 * k):
            #  pay:  kenar denetiminde kutunun küçültülmesi ( eksi:  büyütülmesi )
            return (
                any(_ust(kt, b) for b in obur)
                or any(_ust(kt, d, -2.0 * k) for d in duvarlar)
                or kenarlar.kesisir(kt, pay)
            )

        maske = -uslup.maske_payi(el["yukseklik"])
        if not cakisir(kb, pay=maske):
            continue
        m0 = maske_kutusu(el)

        def olcu_siler(dx, dy, m0=m0):
            boy, uc = olculer.silinen((m0[0] + dx, m0[1] + dy, m0[2] + dx, m0[3] + dy))
            return boy > olcu_esigi or uc > 0

        yer = _etiket_yeri(kb, maske, k, cakisir, parca_kutulari, adimlar, olcu_siler)
        if yer is None:
            continue
        dx, dy, ok = yer
        disarida = ok or not kuyuda((kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy), kuyu)
        if disarida and el.get("ad") in ICERDE_OKLU_ETIKETLER:
            E = _Etiketler(e, yazilar, kutular, oklu, duvarlar, parca_kutulari, kenarlar, k, kuyu)
            icerde = _oklu_yer(
                E, kb, m0, obur, adimlar[1] + adimlar[2], lambda m, E=E: _maske_kusurlu(E, olculer, m), True
            )
            if icerde:
                (dx, dy), ok_ = icerde
                el["x"] += dx
                el["y"] += dy
                kutular[id(el)] = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
                oklar.append(ok_)
                oklu.add(id(el))
                continue
        k2 = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
        #  Kuyunun içindeki parçanın etiketi kuyunun dışına düştüyse oku parçasını
        #  gösterir ( 7 Kas çizim denetimi 5. adımı:  B-B'de dar ağırlığın "KARŞI
        #  AĞIRLIK"ı duvarın ötesinde, kot yazılarının yanında oksuz kalıyordu —
        #  duvarın ya da katın adı gibi okunuyordu;  ağırlığın yanında boş yer yok )
        ok = ok or (el.get("ad") in KUYU_ICI_ETIKETLERI and not kuyuda(k2, kuyu))
        if ok:
            #  Ok:  etiketin parçaya en yakın noktasından eski yerinin ortasına
            ax, ay = (kb[0] + kb[2]) / 2.0, (kb[1] + kb[3]) / 2.0
            px, py = min(max(ax, k2[0]), k2[2]), min(max(ay, k2[1]), k2[3])
            oklar.append(eleman.ad(eleman.ok("YAZI", px, py, ax, ay), "etiket_oku"))
            oklu.add(id(el))
        el["x"] += dx
        el["y"] += dy
        kutular[id(el)] = k2
    oklar += _maskeden_kacir(
        _Etiketler(e, yazilar, kutular, oklu, duvarlar, parca_kutulari, kenarlar, k, kuyu), adimlar
    )
    return e + oklar


def _maske_kusurlu(E, olculer, m):
    """Maske ( m ) bir parçanın kenarını ya da bir ölçünün çizgisini / ucunu siliyor mu
    ( araclar/karne:  maske_kenar_siliyor, maske_olcu_siliyor )."""
    esik = MASKE_ESIGI * 20.0 * E.k
    boy, uc = olculer.silinen(m)
    return boy > esik or uc > 0 or sum(kutudaki_boy(s, m) for s in E.kenarlar.adaylar(m)) > esik


def _maske_kotulesmez(d0, d, k0, kk, esik):
    """Maskenin sildiklerinden ( kenar , ölçü çizgisi boyu , örtülen uç — d0
    eski, d yeni;  k0 / kk:  ( kenar kusurlu , ölçü kusurlu ) ) hiçbiri
    kötüleşmez:  giden kusura bakılmaz, süren kusur ancak biraz büyüyebilir
    ( eşik ya da dörtte bir — zaten kesik çizgi biraz daha kesilebilir:  kumanda
    panosunun adı panonun kenarından ancak böyle kurtuluyordu, altından geçen
    ölçü çizgisi 3,7 mm yerine 4,1 mm kesik ), kusur olmayanın ölçüsü hiç büyümez."""

    def surer(eski, yeni):
        return yeni <= max(eski + esik, 1.25 * eski)

    kenar = (not kk[0] or surer(d0[0], d[0])) if k0[0] else d[0] <= d0[0] + 1e-6
    olcu = (
        (not kk[1] or (surer(d0[1], d[1]) and d[2] <= d0[2]))
        if k0[1]
        else (d[1] <= d0[1] + 1e-6 and d[2] <= d0[2])
    )
    return kenar and olcu


@dataclass
class _Etiketler:
    """etiketleri_ayir'ın durumu:  elemanlar, yazılar ve kutuları ( kayınca
    güncellenir ), oklu etiketler, duvarlar, parça kutuları ve kenarları, ölçek."""

    e: list
    yazilar: list
    kutular: dict
    oklu: set
    duvarlar: list
    parca_kutulari: list
    kenarlar: KenarIzgarasi
    k: float
    kuyu: tuple = None


def _satirli(el, yazilar):
    """Etiket alt alta ( ya da yan yana — dikine yazıda ) yazılmış bir bloğun
    satırı mı:  aynı adla, açıyla, hizayla ve boyda, satır doğrultusunda aynı
    yerde, bir buçuk satır içinde başka bir etiket var ( kuyu dibinin yük
    tablosu ) — satır tek başına kayarsa blok bozulur.  "KARŞI AĞIRLIK" ile
    altındaki "ø 400" ayrı adlı iki etikettir, blok değil."""
    h, aci = el["yukseklik"], el.get("aci", 0)
    i, j = ("x", "y") if aci == 0 else ("y", "x")
    return any(
        x is not el
        and x["tip"] == "yazi"
        and x.get("ad") == el.get("ad")
        and x.get("aci", 0) == aci
        and x.get("hiza", "orta") == el.get("hiza", "orta")
        and x["yukseklik"] == h
        and abs(x[i] - el[i]) <= 1.0
        and 0.0 < abs(x[j] - el[j]) <= 1.6 * h
        for x in yazilar
    )


def _boyunca(el, k):
    """Etiketin kendi doğrultusunda ( yazının yönünde ) uzak kaymaları:
    1/20'de 110 – 300 mm, 20 mm adımla, yakından uzağa — uzun etiket, altından
    geçen ölçü çizgisinden ancak böyle kurtulur ( kuyu dibinde perdenin yanındaki
    "KARŞI AĞIRLIK PERDESİ" "665"in çizgisinin üstündeydi );  yanından geçtiği
    parçanın boyunca kaldığı için adlandırdığı şeyden kopmaz."""
    adim = max(int(20 * k), 1)
    out = []
    for d in range(int(110 * k), int(300 * k) + 1, adim):
        out += [(d, 0), (-d, 0)] if el.get("aci", 0) == 0 else [(0, d), (0, -d)]
    return out


def _maskeden_kacir(E, adimlar):
    """MASKE ( 26 Eki, kalite 3. adımı ):  etiketin GERÇEK maskesi
    ( uslup.maske_kutusu — ayırıcının denetimi çıplak kutuya bakıyordu ) bir
    parçanın kenarını ya da önce çizilen bir ölçünün çizgisini / ucunu
    siliyorsa ( MASKE_ESIGI;  araclar/karne:  maske_kenar_siliyor,
    maske_olcu_siliyor ) etiket en az kayarak ( 1/20'de 100 mm;  kendi
    doğrultusunda 300 mm'ye kadar — _boyunca ) HİÇBİR ölçüde kötüleşmediği,
    kusuru azaldığı yere taşınır:  başka yazıya
    binmez, duvara girmez, eskisinden çok parçanın içine girmez, maskesi
    eskisinden çok kenar ve ölçü silmez;  önce kusursuz yer.  Kumanda panosunun
    adı panonun ön yüzünü, kabin üstünde HALAT kabin duvarını, "KARŞI AĞIRLIK"
    çerçevenin üst kenarını siliyordu.  Oklu ( uzağa taşınmış ) etiket, alan
    adı ( alanının içinde, satırlı ), kot ( işaretinin yanında ) ve bloğun
    satırı ( _satirli ) kıpırdamaz.

    Kuyunun içindeki etiket ( KUYU_ICI_ETIKETLERI ) kuyunun dışına kaymaz;
    yakında kusursuz yer yoksa kuyunun içinde, hiçbir parçanın üstünde olmayan
    en yakın kusursuz yere KISA OKLA taşınır ( _oklu_yer — 7 Kas çizim denetimi
    5. adımı:  dar karşı ağırlığın "ø 400"ü çerçeveyi siliyordu ).  Dönen:  oklar."""
    itme = adimlar[0]
    esik = MASKE_ESIGI * 20.0 * E.k
    olculer = OlcuIzgarasi(E.e)

    def olcut(m):
        boy, uc = olculer.silinen(m)
        return sum(kutudaki_boy(s, m) for s in E.kenarlar.adaylar(m)), boy, uc

    def kusurlu(d):
        return (d[0] > esik, d[1] > esik or d[2] > 0)

    oklar = []
    for el in E.yazilar:
        if (
            el["tip"] != "yazi"
            or id(el) in E.oklu
            or el.get("ad") in ("alan_adi", "kot", *SABIT_ETIKETLER)
            or _satirli(el, E.yazilar)
        ):
            continue
        m0 = maske_kutusu(el)
        d0 = olcut(m0)
        k0 = kusurlu(d0)
        kb = E.kutular[id(el)]
        obur = [E.kutular[id(x)] for x in E.yazilar if x is not el and E.kutular[id(x)]]
        if not any(k0):
            continue
        ok = None
        secilen = _maskesiz_kayma(E, el, kb, m0, obur, itme, olcut, kusurlu, d0, k0, esik)
        kalan = (
            k0 if secilen is None else kusurlu(olcut(tuple(v + (secilen[i % 2]) for i, v in enumerate(m0))))
        )
        if el.get("ad") in KUYU_ICI_ETIKETLERI and any(kalan):
            yer = _kuyudaki_yer(E, kb, m0, obur, adimlar, lambda m: any(kusurlu(olcut(m))))
            if yer:
                secilen, ok = yer
        if secilen:
            dx, dy = secilen
            el["x"] += dx
            el["y"] += dy
            E.kutular[id(el)] = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
        if ok:
            oklar.append(ok)
            E.oklu.add(id(el))
    return oklar


def _maskesiz_kayma(E, el, kb, m0, obur, itme, olcut, kusurlu, d0, k0, esik):
    """_maskeden_kacir'ın kayması ( kuyunun içindekiler dışındaki etiketler ):
    ( dx , dy ) ya da None — önce kusursuz, yoksa kusuru azalan ilk yer."""
    parca0 = sum(1 for q in E.parca_kutulari if _ust(kb, q, 0.0))
    secilen = None
    for dx, dy in itme + _boyunca(el, E.k):
        kt = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
        if (
            any(_ust(kt, b) for b in obur)
            or any(_ust(kt, d, -2.0 * E.k) for d in E.duvarlar)
            or E.kenarlar.kesisir(kt, 2.0 * E.k)
            or sum(1 for q in E.parca_kutulari if _ust(kt, q, 0.0)) > parca0
        ):
            continue
        d = olcut((m0[0] + dx, m0[1] + dy, m0[2] + dx, m0[3] + dy))
        kk = kusurlu(d)
        if any(a > b for a, b in zip(kk, k0)) or sum(kk) >= sum(k0):
            continue
        if not _maske_kotulesmez(d0, d, k0, kk, esik):
            continue
        secilen = secilen or (dx, dy)
        if not any(kk):
            return (dx, dy)
    return secilen


def _kuyudaki_yer(E, kb, m0, obur, adimlar, kusurlu_mu):
    """Maskesi kayınca da parçanın kenarını ya da ölçüyü silen kuyu içi etiketinin
    ( KUYU_ICI_ETIKETLERI — dar karşı ağırlığın "ø 400"ü çerçevenin içinde ) oklu
    yeri:  ( ( dx , dy ) , ok ) ya da None ( yerinde kalır ) — kuyunun içinde kısa
    okla ( 1/20'de 300 mm ), maskesi kusursuz yer ( _oklu_yer ).  Dışarı taşınmaz:
    örnek düzende "KARŞI AĞIRLIK" ile "ø 400" duvarın dışında alt alta tek yazı
    gibi okunuyor, ölçü yazısının dibine düşüyordu."""
    return _oklu_yer(E, kb, m0, obur, adimlar[1], kusurlu_mu, True)


def _oklu_yer(E, kb, m0, obur, kaymalar, kusurlu_mu, icerde):
    """Kuyunun içindeki etiketin oklu yeri:  ( ( dx , dy ) , ok ) ya da None —
    kaymalar sırasıyla ( yakından uzağa ), icerde:  kuyunun içinde, değilse dışında;
    hiçbir parçanın ( kuyunun kendisi hariç ) ve yazının üstünde olmayan, duvara
    girmeyen, kenara değmeyen, maskesi kusursuz ilk yer;  ok etiketin eski yerine
    ( adlandırdığı parçaya ) gider ve hiçbir yazının üstünden geçmez.  İçeride
    uzak yer seçilmez:  B-B'de kapı görünüşünü boydan kesen uzun ok gerekiyordu."""
    x, y = E.kuyu if E.kuyu else (None, None)

    def kuyunun_kendisi(q):
        return (x is None or (q[0] <= x[0] + 1.0 and q[2] >= x[1] - 1.0)) and (
            y is None or (q[1] <= y[0] + 1.0 and q[3] >= y[1] - 1.0)
        )

    parcalar_ = [q for q in E.parca_kutulari if not kuyunun_kendisi(q)]
    ax, ay = (kb[0] + kb[2]) / 2.0, (kb[1] + kb[3]) / 2.0
    for dx, dy in kaymalar:
        kt = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
        if (
            kuyuda(kt, E.kuyu) != icerde
            or any(_ust(kt, b) for b in obur)
            or any(_ust(kt, d, -2.0 * E.k) for d in E.duvarlar)
            or any(_ust(kt, q, 0.0) for q in parcalar_)
            or E.kenarlar.kesisir(kt, -2.0 * E.k)
            or kusurlu_mu((m0[0] + dx, m0[1] + dy, m0[2] + dx, m0[3] + dy))
        ):
            continue
        px, py = min(max(ax, kt[0]), kt[2]), min(max(ay, kt[1]), kt[3])
        cizgi = (px, py, ax, ay)
        if any(kenar_kesisir(cizgi, b) for b in obur):
            continue
        return (dx, dy), eleman.ad(eleman.ok("YAZI", px, py, ax, ay), "etiket_oku")
    return None


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
        #  Tuğla tarama da ( bina duvarı — Sabitler'de bina_duvari > 0 ):
        #  yoksa etiketleri_ayir boş kutuda min() hatası veriyor, ekrana
        #  hiçbir çizim gelmiyordu ( 20 Eki ).
        if el["tip"] in ("dikdortgen", "tarama", "tarama_tugla"):
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


_UYARI_AYRAC = ("  —  ", "  ·  ")


def _uyari_parcalari(metin):
    """Notun bölünmez parçaları ( ayraçlar önceki parçada kalır )."""
    parcalar_ = [metin]
    for a in _UYARI_AYRAC:
        parcalar_ = [
            x + (a if i < len(p.split(a)) - 1 else "") for p in parcalar_ for i, x in enumerate(p.split(a))
        ]
    return parcalar_


def _sar(metin, en, h):
    """Satırı en'e sığan satırlara sarar ( ayraçlardan;  sondaki ayraç düşer )."""
    satirlar, s = [], ""
    for p in _uyari_parcalari(metin):
        if s and eleman.yazi_eni((s + p).rstrip(" ·—"), h) > en:
            satirlar.append(s.rstrip(" ·—"))
            s = ""
        s += p
    return satirlar + [s.rstrip(" ·—")] if s else satirlar


def cerceveli(elemanlar, baslik, olcek=20, pay=300, seritler=(), olcekli=True, uyari=()):
    """Çizimi kendi çerçevesine alır ve altına başlık şeridi ekler.

    Referans projede de her çizim ayrı bir çerçevededir ve altında adı ile ölçeği
    yazar.  Çerçeve ölçüleri de kapsar;  yazılar dışarıda kalmaz.  olcekli:
    başlıkta ölçek yazar mı ( tabloda yazmaz — cizimler.OLCEKSIZ ).  uyari:
    künye şeridinin altında, çerçevenin içinde ayrı bir bantta satırlar —
    hesabın uygun bulmadığı bölümler ( cizim/hesap_isareti.py ).
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
    #  Not çerçeveyi genişletmez ( çizimlerin yerleşimi değişmesin ):  satırlar
    #  "  ·  " ve "  —  " yerlerinden sarılır;  yalnız tek parçası sığmazsa genişler
    parcalar_ = [p for m in uyari for p in _uyari_parcalari(m)]
    gerek = max([gerek] + [240 * k + eleman.yazi_eni(p, uslup.HARF * k) for p in parcalar_])
    if x2 - x1 < gerek:
        fark = (gerek - (x2 - x1)) / 2.0
        x1, x2 = x1 - fark, x2 + fark
    uyari = [s for m in uyari for s in _sar(m, x2 - x1 - 240 * k, uslup.HARF * k)]
    satir = 150.0 * k
    bant = (len(uyari) + 0.6) * satir if uyari else 0.0
    e = list(elemanlar)
    e.append(eleman.dikdortgen("CERCEVE", x1, y1 - serit - bant, x2 - x1, (y2 - y1) + serit + bant))
    e.append(eleman.cizgi("CERCEVE", x1, y1, x2, y1))
    if uyari:
        ust = y1 - serit
        e.append(eleman.cizgi("UYARI", x1, ust, x2, ust))
        e += [
            eleman.yazi(x1 + 120 * k, ust - (i + 0.8) * satir, m, uslup.HARF * k, hiza="sol", katman="UYARI")
            for i, m in enumerate(uyari)
        ]
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
