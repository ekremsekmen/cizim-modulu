# -*- coding: utf-8 -*-
"""KALİTE KARNESİ — çizimlerin ölçülen kusurları, SAYI olarak ( 26 Eki, kalite
denetimi:  cikti/arastirma/KALITE_DENETIMI_26EKI.md ).

Kalite kapısının ( testler/test_kalite.py ) kuralları sıfır ister;  buradakiler
bugün her düzende vardır ve sınıf sınıf giderilecek.  Bu yüzden CIRCIR gibi
işler:  her düzenin her çiziminde her kuralın sayısı kayıttadır ( altın
düzenler:  testler/kalite_karnesi.json — test_kalite;  girdi taraması:
testler/tarama_karnesi.json — araclar/tarama ).  Sayı kayıttan BÜYÜKSE kapı
kırılır ( kötüleşme );  KÜÇÜKSE de kırılır ve kaydın yenilenmesini ister
( iyileşme kilitlenir, geri gelemez ).  Sıfıra inen kural kesin kural olur.

Ölçüm çizildiği gibidir ( pdf.ciz · svg · dxf aynı sıra ):  önce parçalar, sonra
ölçüler ÖĞE SIRASIYLA ( her biri çizgisi, uçları, maskesi ve yazısıyla ), en
son etiketler;  her yazının önce maskesi ( uslup.maske_kutusu ).  Ölçünün
yazısına binen ölçü çizgisi sıradan bağımsız sayılır ( geometri.
cizgiye_binen_yazilar ):  sonra çizilen yazının üstünden geçer, önce çizileni
yazının maskesi keser.

  maske_kenar_siliyor      yazının maskesi bir parça / duvar kenarını kâğıtta
                           MASKE_ESIGI'nden çok siliyor ( makine dairesinde
                           kumanda panosunun ön yüzü, kabin üstünde kabin duvarı )
  maske_olcu_siliyor       yazının maskesi kendinden ÖNCE çizilen bir ölçünün
                           çizgisini MASKE_ESIGI'nden çok siliyor ya da ucunu
                           ( ölçünün sınırı ) örtüyor ( geometri.OlcuIzgarasi;
                           kabin üstünde HALAT 500 ile 650'nin arasındaki ucu,
                           kuyu dibinde "270" "640"ın çizgisini siliyordu )
  olcu_yaziyi_kesiyor      başka bir ölçünün çizgisi / ucu bir ölçü yazısının
                           harflerinden KESME_ESIGI'nden çok geçiyor ( kabin
                           üstünde "500"ün çizgisi kabin duvarının "15"inden;
                           kuyu dibinde "162,5" "615"in çizgisinde — maske onu
                           kesiyordu )
  olcu_ucu_yaziya_degiyor  aynısı, KESME_ESIGI'ne kadar:  üst sıranın kısa uzatma
                           çizgisi alttaki ölçü yazısının harflerine değiyor
  ok_yaziyi_kesiyor        etiket oku başka bir yazının harflerinden geçiyor
  yazi_cizgisinden_kopuk   ölçü yazısı kendi çizgisinden KOPUK yazı boyundan
                           uzak ( dar aralıkta yana kaçmış, başka zincirin
                           yanında okunuyor )
  halat_betonda            halat çizgisi kesilen betonun ( tarama ) içinden
                           kâğıtta HALAT_ESIGI'nden çok geçiyor ( delik yok )
  olcu_kot_isaretine_degiyor
                           bir ölçünün çizgisi ( uçlarıyla ) kot işaretinin
                           üçgenine DEGME_PAYI'ndan yakın ya da içinden geçiyor
                           ( 27 Eki:  makine dairesi kuyudan çok taşınca A-A'da
                           MD'nin kotu sol zincirlerin arasına düşüyordu )

6 Kas çizim denetimi ( cikti/devir/CIZIM_DENETIMI_PLANI.md ):

  yazi_yanlis_aralikta     ölçü yazısı kendi aralığının dışında, aynı zincirin
                           başka bir aralığının hizasında ( geometri.
                           yanlis_aralikta — kuyu planında "30" 90'ın yanında )
  yazi_bitisik             aynı doğrultudaki iki ölçü yazısı arası BITISIK_ESIGI
                           mm'den az:  tek söz gibi okunur ( "ŞASE 140 MAKİNE 345" )
  yazi_cizimden_tasiyor    açıklamalı ölçü yazısı ( iki harf yan yana — yalnız
                           sayı uçta dışarı yazılabilir, ISO 129-1 ) çizimin
                           parçalarından kendi doğrultusunda TASMA mm'den çok
                           dışarı taşıyor ( "İLK KONSOL 500" kuyu dibinin altında )
  uzak_olcu                giriş görünüşünde ve kapı yan kesitinde ölçünün bir
                           ucu ölçtüğü özellikten ( aynı koordinattaki parça
                           kenarı / köşesi ) UZAK_OLCU mm'den uzak ya da o
                           koordinatta çizili özellik yok ( buton "240" havada ) —
                           planlarda ve kesitlerde dış sıralar bilerek uzaktır
  etiket_kuyu_disinda      kuyunun içindeki parçanın oksuz etiketi ( karşı ağırlık,
                           kasnaklar ) kuyunun iç yüzlerinin ( SW / SD ölçüsü )
                           dışında ( BAR 2515'te "ø 400", B-B'de "KARŞI AĞIRLIK" )
  kapi_no_kat_adi          B-B'de kat kapısının yazısı o katın adından farklı
                           ( kapıda durak sırası "1", solda kat adı "0" )
  isaret_birligi           çap "Ø" ya da çarpı "x" ( çizimlerin işareti ø ve × )

    .venv/bin/python -m araclar.karne            altın düzenlerin karnesi ( özet )
    .venv/bin/python -m araclar.karne --yenile   altının kaydını yeniden yazar

--yenile DAVRANIŞI KABUL İZNİDİR ( altın çizim gibi ):  yalnız sayılar incelenip
iyileşme ( ya da onaylı bir değişiklik ) görüldükten sonra.
"""

import collections
import json
import math
import os
import re
import sys

from cizim import geometri
from cizim import kesit_parcalari
from testler import altin_cizim

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALTIN_KAYDI = os.path.join(KOK, "testler", "kalite_karnesi.json")
TARAMA_KAYDI = os.path.join(KOK, "testler", "tarama_karnesi.json")

#  Eşikler kâğıtta mm ( ölçekle çizim birimine çevrilir );  KOPUK yazı boyu.
#  Maskeninki yerleşimle aynı ( yazı ondan çok silen yerden kaçar ).
MASKE_ESIGI = geometri.MASKE_ESIGI
KESME_ESIGI = 0.5
HALAT_ESIGI = 0.5
KOPUK = 1.5
#  Okun ucu kendi yazısının bu kadar yakınındaysa o yazının okudur
OK_PAYI = 3.0
#  Ölçü çizgisi kot işaretinin üçgenine bu kadar yaklaşırsa değer
DEGME_PAYI = 0.3
#  Harf gövdesi bu kadar içeriden denenir:  kenarına sürtünme sayılmaz
GOVDE_PAYI = 0.1
#  Açıklamalı ölçü yazısı çizimin parçalarından bu kadar taşarsa ( kâğıtta mm )
TASMA = 3.0
#  Ölçünün ucu ölçtüğü özellikten bu kadar uzaksa ( kâğıtta mm ) havada kalır;
#  yalnız bu çizimlerde ( planda ve kesitte dış sıralar bilerek uzaktır )
UZAK_OLCU = 30.0
UZAK_CIZIMLER = ("giris", "kapi_kesiti")
#  Çizime bağlı kurallar:  karne( e , olcek , cizim ) çizimin adıyla sayar
CIZIME_BAGLI = {"uzak_olcu": UZAK_CIZIMLER}
#  Kuyunun içindeki parçaların etiketleri:  kuyunun dışına düşmez ( ayırıcıyla aynı küme )
PARCA_ETIKETLERI = geometri.KUYU_ICI_ETIKETLERI
#  Çizimin sınırına ( yazının taşması ) sayılmayan katmanlar — yerleştiriciyle aynı
PARCA_DISI = geometri.CIZIM_DISI_KATMANLAR
#  Ölçünün ucunun özelliği:  yazı / ölçü / çerçeve / kesit işareti dışında her çizgi
OZELLIK_DISI = frozenset(("OLCU", "YAZI", "CERCEVE", "KESIT"))
_ACIKLAMA = geometri.ACIKLAMALI
_ISARET = re.compile(r"Ø|\d\s*x\s*\d")
#  B-B'de kat adı durağın 1.100 üstünde, kapının yazısı kapı yüksekliğinin 0,6'sında
#  ( kuyu_kesiti._kat_seviyeleri · _on_katlar ):  kapının yazısının altındaki en
#  yakın ad o katındır ( kısa kapıya pay )
KAT_ADI_PAYI = 300.0

KURALLAR = {
    "maske_kenar_siliyor": "yazının maskesi parça / duvar kenarını siliyor",
    "maske_olcu_siliyor": "yazının maskesi önce çizilen ölçü çizgisini siliyor",
    "olcu_yaziyi_kesiyor": "başka ölçünün çizgisi ölçü yazısını kesiyor",
    "olcu_ucu_yaziya_degiyor": "başka ölçünün ucu ölçü yazısına değiyor",
    "ok_yaziyi_kesiyor": "etiket oku başka bir yazıyı kesiyor",
    "yazi_cizgisinden_kopuk": "ölçü yazısı kendi çizgisinden kopuk",
    "halat_betonda": "halat betonun içinden geçiyor",
    "olcu_kot_isaretine_degiyor": "ölçü çizgisi kot işaretine değiyor",
    "yazi_yanlis_aralikta": "ölçü yazısı zincirin başka aralığının hizasında",
    "yazi_bitisik": "iki ölçü yazısı bitişik ( tek söz gibi )",
    "yazi_cizimden_tasiyor": "açıklamalı ölçü yazısı çizimin dışına taşıyor",
    "uzak_olcu": "ölçü ölçtüğü özellikten uzak ( giriş, kapı kesiti )",
    "etiket_kuyu_disinda": "parçanın etiketi kuyunun dışında",
    "kapi_no_kat_adi": "B-B'de kapının yazısı kat adından farklı",
    "isaret_birligi": "çap Ø / çarpı x ( ø ve × yerine )",
}
#  Karnenin kendisinin saymadığı, yalnız girdi taramasının yazdığı sayılar
#  ( araclar/tarama.denetle_tek_kuyu ):  tek asansörlü çizimlerde bu bulgu taramayı
#  durduran bir sorundur;  tek kuyunun ortak çizimlerinde kayıtla karşılaştırılır.
TARAMA_KURALLARI = {
    "yazi_parca_kenarinda": "tek kuyunun ortak çiziminde yazı parçaya, duvara ya da başka yazıya biniyor",
}


def _yazilar(e):
    """Etiketler ( çerçevenin başlığı hariç ) ve ölçü yazıları."""
    return [
        x
        for x in e
        if (x["tip"] == "yazi" and x.get("katman") != "CERCEVE") or (x["tip"] == "olcu" and x.get("yazi"))
    ]


def _icerden(kutu, pay):
    return (kutu[0] + pay, kutu[1] + pay, kutu[2] - pay, kutu[3] - pay)


def _maskeler(e, yazilar, olcek):
    """maske_kenar_siliyor:  [ ( metin , silinen boy — kâğıtta mm ) ]."""
    kenarlar = geometri.KenarIzgarasi(geometri.parca_kenarlari(e))
    out = []
    for x in yazilar:
        m = geometri.maske_kutusu(x)
        boy = sum(geometri.kutudaki_boy(s, m) for s in kenarlar.adaylar(m))
        if boy > MASKE_ESIGI * olcek:
            out.append((x["metin"], round(boy / olcek, 1)))
    return out


def _maske_olculer(e, yazilar, olcek):
    """maske_olcu_siliyor:  [ ( metin , silinen çizgi boyu — mm , örtülen uç ) ]."""
    olculer = geometri.OlcuIzgarasi(e)
    out = []
    for x in yazilar:
        boy, uc = olculer.silinen(geometri.maske_kutusu(x), x)
        if boy > MASKE_ESIGI * olcek or uc:
            out.append((x["metin"], round(boy / olcek, 1), uc))
    return out


def _olcu_ustunde(e, olcek):
    """Başka bir ölçünün çizgisi ölçü yazısının harflerinde ( geometri.
    cizgiye_binen_yazilar — harf gövdesi GOVDE_PAYI içeriden ):  ( kesen ,
    değen ) — [ ( yazı , çizginin ölçüsünün yazısı ) ]."""
    kesen, degen = [], []
    for o, q, boy in geometri.cizgiye_binen_yazilar(e, olcek / 20.0, -GOVDE_PAYI * olcek):
        (kesen if boy > KESME_ESIGI * olcek else degen).append((o["metin"], q.get("metin")))
    return kesen, degen


def _oklar(e, yazilar, olcek):
    """ok_yaziyi_kesiyor:  [ metin ] — okun ucu ( iki ucundan biri ) kendi
    yazısına yakındır, o yazı sayılmaz."""
    oklar = [
        (x["x1"], x["y1"], x["x2"], x["y2"])
        for x in e
        if (x["tip"] == "ok" or (x["tip"] == "cizgi" and x.get("katman") == "YAZI"))
        and x.get("katman") in ("YAZI", "YUK")
        and x.get("ad") != "kuvvet_semasi"
    ]
    pay = OK_PAYI * olcek
    out = []
    for s in oklar:
        for x in yazilar:
            g = geometri.govde_kutusu(x)
            kendi = any(
                g[0] - pay <= px <= g[2] + pay and g[1] - pay <= py <= g[3] + pay
                for px, py in ((s[0], s[1]), (s[2], s[3]))
            )
            if not kendi and geometri.kutudaki_boy(s, _icerden(g, GOVDE_PAYI * olcek)) > 0.0:
                out.append(x["metin"])
    return out


def _kopuklar(e, olcek):
    """yazi_cizgisinden_kopuk:  [ ( metin , uzaklık — kâğıtta mm ) ]."""
    out = []
    for o in e:
        y = o.get("yazi") if o["tip"] == "olcu" else None
        if not y:
            continue
        dik = abs(y["y"] - o["kot"]) if o["yon"] == "yatay" else abs(y["x"] - o["kot"])
        if dik > KOPUK * y["h"]:
            out.append((o["metin"], round(dik / olcek, 1)))
    return out


def _halatlar(e, olcek):
    """halat_betonda:  [ betondaki boy — mm ]."""
    beton = [
        (x["x"], x["y"], x["x"] + x["g"], x["y"] + x["d"])
        for x in e
        if x["tip"] == "tarama" and x.get("katman") == "TARAMA"
    ]
    out = []
    for x in e:
        if x["tip"] == "cizgi" and x.get("katman") == "HALAT":
            s = (x["x1"], x["y1"], x["x2"], x["y2"])
            boy = sum(geometri.kutudaki_boy(s, b) for b in beton)
            if boy > HALAT_ESIGI * olcek:
                out.append(round(boy))
    return out


def _kot_ucgenleri(e):
    """kesit_parcalari.kot_isareti'nin üçgenleri ( üst kenarı yatay, iki kenarı
    ucunda — döşemede — birleşir;  boyu / yarı eni KOT_UCGENI'nin oranı ):
    [ ( sol üst , sağ üst , uç ) ]."""
    oran = kesit_parcalari.KOT_UCGENI[1] / kesit_parcalari.KOT_UCGENI[0]
    cizgiler = [
        ((x["x1"], x["y1"]), (x["x2"], x["y2"]))
        for x in e
        if x["tip"] == "cizgi" and x.get("katman") == "KUYU-IC"
    ]
    bitisler = collections.defaultdict(list)  # başlangıç noktası → bitiş noktaları
    for p, q in cizgiler:
        bitisler[(round(p[0], 3), round(p[1], 3))].append(q)

    def bitis(p, hedef):
        return next(
            (
                q
                for q in bitisler[(round(p[0], 3), round(p[1], 3))]
                if abs(q[0] - hedef[0]) < 1e-3 and abs(q[1] - hedef[1]) < 1e-3
            ),
            None,
        )

    out = []
    for a, b in cizgiler:
        if abs(a[1] - b[1]) > 1e-6 or b[0] <= a[0]:
            continue
        w = (b[0] - a[0]) / 2.0
        uc = bitis(a, (a[0] + w, a[1] - oran * w))
        if uc is not None and bitis(uc, b) is not None:
            out.append((a, b, uc))
    return out


def _yon(p, q, r):
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _nokta_parca(p, a, b):
    """Noktanın doğru parçasına ( a – b ) uzaklığı."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = 0.0 if dx == dy == 0 else ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _ucgen_uzakligi(s, ucgen):
    """Doğru parçasının ( x1, y1, x2, y2 ) üçgene uzaklığı:  içinden geçiyorsa 0."""
    p, q = (s[0], s[1]), (s[2], s[3])
    kenarlar = [(ucgen[i - 1], ucgen[i]) for i in range(3)]

    def icinde(r):
        d = [_yon(a, b, r) for a, b in kenarlar]
        return min(d) >= 0 or max(d) <= 0

    if icinde(p) or icinde(q):
        return 0.0
    if any(_yon(p, q, a) * _yon(p, q, b) < 0 and _yon(a, b, p) * _yon(a, b, q) < 0 for a, b in kenarlar):
        return 0.0
    return min(
        min(_nokta_parca(p, a, b), _nokta_parca(q, a, b), _nokta_parca(a, p, q), _nokta_parca(b, p, q))
        for a, b in kenarlar
    )


def _olcu_kot_isaretinde(e, olcek):
    """olcu_kot_isaretine_degiyor:  [ ( kot yazısı , ölçünün yazısı ) ] — işaret
    başına bir bulgu;  ölçünün çizgisi uçlarıyla ( geometri.olcu_cizgileri )."""
    ucgenler = _kot_ucgenleri(e)
    if not ucgenler:
        return []
    sahip = {}
    for o in e:
        if o["tip"] == "olcu" and o.get("uzunluk", 1.0) >= 1e-6:
            for s in geometri.olcu_cizgileri(o, olcek / 20.0):
                sahip[id(s)] = (s, o)
    izgara = geometri.KenarIzgarasi([s for s, _ in sahip.values()])
    kotlar = [x for x in e if x["tip"] == "yazi" and x.get("ad") == "kot"]
    pay = DEGME_PAYI * olcek
    out = []
    for ucgen in ucgenler:
        (a, b, uc) = ucgen
        kutu = (a[0] - pay, uc[1] - pay, b[0] + pay, a[1] + pay)
        for s in izgara.adaylar(kutu):
            if _ucgen_uzakligi(s, ucgen) <= pay:
                yazi = min(kotlar, key=lambda x: (x["x"] - uc[0]) ** 2 + (x["y"] - a[1]) ** 2, default=None)
                out.append((yazi["metin"] if yazi else "", sahip[id(s)][1].get("metin")))
                break
    return out


def _tasanlar(e, olcek):
    """yazi_cizimden_tasiyor:  [ ( metin , taşma — kâğıtta mm ) ]."""
    parcalar = [x for x in e if x["tip"] not in ("olcu", "yazi", "ok") and x.get("katman") not in PARCA_DISI]
    if not parcalar:
        return []
    P = geometri.sinir(parcalar)
    out = []
    for o in e:
        if o["tip"] != "olcu" or not o.get("yazi") or not _ACIKLAMA.search(o["metin"]):
            continue
        j = 0 if o["yon"] == "yatay" else 1
        k = geometri.yazi_kutusu(o)
        tasma = max(P[j] - k[j], k[j + 2] - P[j + 2], 0.0)
        if tasma > TASMA * olcek:
            out.append((o["metin"], round(tasma / olcek, 1)))
    return out


def _ozellik_kenarlari(e):
    """Ölçünün ölçebileceği çizgiler:  [ ( x1, y1, x2, y2 ) ] — dairenin iki çapı
    ( merkezi ölçülür )."""
    out = []
    for el in e:
        t = el["tip"]
        if el.get("katman") in OZELLIK_DISI or t in ("yazi", "olcu"):
            continue
        if t in ("dikdortgen", "tarama", "tarama_tugla"):
            x, y, g, d = el["x"], el["y"], el["g"], el["d"]
            out += [(x, y, x + g, y), (x + g, y, x + g, y + d), (x, y + d, x + g, y + d), (x, y, x, y + d)]
            for p in el.get("bicim") or ():
                n = p["noktalar"]
                out += [(n[i][0], n[i][1], n[i - 1][0], n[i - 1][1]) for i in range(1, len(n))]
        elif "x1" in el:
            out.append((el["x1"], el["y1"], el["x2"], el["y2"]))
        elif t == "daire":
            x, y, r = el["x"], el["y"], el["r"]
            out += [(x - r, y, x + r, y), (x, y - r, x, y + r)]
    return out


def _uc_uzakliklari(o, kenarlar, olcek, tol=GOVDE_PAYI * 3):
    """Ölçünün iki ucunun aynı koordinattaki özelliğe ( dik kenar ya da köşe ) dik
    uzaklığı — kâğıtta mm;  o koordinatta özellik yoksa sonsuz."""
    i = 0 if o["yon"] == "yatay" else 1
    t = tol * olcek
    out = []
    for p in (o["a"], o["b"]):
        v, en = p[i], math.inf
        for s in kenarlar:
            a, b = (s[0], s[1]), (s[2], s[3])
            if abs(a[i] - v) < t and abs(b[i] - v) < t:
                lo, hi = sorted((a[1 - i], b[1 - i]))
                en = min(en, 0.0 if lo <= o["kot"] <= hi else min(abs(lo - o["kot"]), abs(hi - o["kot"])))
            else:
                en = min([en] + [abs(q[1 - i] - o["kot"]) for q in (a, b) if abs(q[i] - v) < t])
        out.append(en / olcek)
    return out


def _uzaklar(e, olcek):
    """uzak_olcu:  [ ( metin , uzaklık — kâğıtta mm;  özellik yoksa None ) ]."""
    kenarlar = _ozellik_kenarlari(e)
    out = []
    for o in e:
        if o["tip"] != "olcu" or o.get("uzunluk", 0.0) < 1e-6:
            continue
        en = max(_uc_uzakliklari(o, kenarlar, olcek))
        if en > UZAK_OLCU:
            out.append((o["metin"], None if en == math.inf else round(en, 1)))
    return out


def _disaridakiler(e, olcek):
    """etiket_kuyu_disinda:  [ metin ] — oklu etiket ( okun ucu yazının yanında ) sayılmaz."""
    kuyu = geometri.kuyunun_ici(e)
    if kuyu is None or kuyu[0] is None:
        return []
    x, y = kuyu
    pay = OK_PAYI * olcek
    uclar = [
        (s["x1"], s["y1"], s["x2"], s["y2"])
        for s in e
        if s["tip"] in ("ok", "cizgi") and s.get("katman") == "YAZI"
    ]
    out = []
    for el in e:
        if el["tip"] != "yazi" or el.get("ad") not in PARCA_ETIKETLERI:
            continue
        k = geometri.sinir([el])
        cx, cy = (k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0
        if x[0] <= cx <= x[1] and (y is None or y[0] <= cy <= y[1]):
            continue
        oklu = any(
            k[0] - pay <= px <= k[2] + pay and k[1] - pay <= py <= k[3] + pay
            for s in uclar
            for px, py in ((s[0], s[1]), (s[2], s[3]))
        )
        if not oklu:
            out.append(el["metin"])
    return out


def _kapi_numaralari(e):
    """kapi_no_kat_adi:  [ ( katın adı , kapının yazısı ) ]."""
    adlar = sorted((x["y"], x["metin"]) for x in e if x["tip"] == "yazi" and x.get("ad") == "durak_adi")
    out = []
    for x in e:
        if x["tip"] == "yazi" and x.get("ad") == "durak_no":
            alt = [m for y, m in adlar if y <= x["y"] + KAT_ADI_PAYI]
            ad = alt[-1] if alt else None
            if ad != x["metin"]:
                out.append((ad, x["metin"]))
    return out


def _isaretler(e):
    """isaret_birligi:  [ metin ]."""
    return [
        x["metin"]
        for x in e
        if x["tip"] in ("yazi", "olcu")
        and x.get("katman") != "CERCEVE"
        and _ISARET.search(str(x.get("metin", "")))
    ]


def karne(e, olcek=20, cizim=None):
    """Çizimin ( elemanları e ) kusurları:  { kural : [ bulgu ] } — bütün kurallar.
    cizim:  çizimin adı ( cizimler.CIZIMLER ) — çizime bağlı kurallar ( CIZIME_BAGLI )
    yalnız onunla sayılır."""
    yazilar = _yazilar(e)
    kesen, degen = _olcu_ustunde(e, olcek)
    return {
        "maske_kenar_siliyor": _maskeler(e, yazilar, olcek),
        "maske_olcu_siliyor": _maske_olculer(e, yazilar, olcek),
        "olcu_yaziyi_kesiyor": kesen,
        "olcu_ucu_yaziya_degiyor": degen,
        "ok_yaziyi_kesiyor": _oklar(e, yazilar, olcek),
        "yazi_cizgisinden_kopuk": _kopuklar(e, olcek),
        "halat_betonda": _halatlar(e, olcek),
        "olcu_kot_isaretine_degiyor": _olcu_kot_isaretinde(e, olcek),
        "yazi_yanlis_aralikta": [(o["metin"], p["metin"]) for o, p in geometri.yanlis_aralikta(e, olcek)],
        "yazi_bitisik": [
            (o["metin"], p["metin"], round(b, 2)) for o, p, b in geometri.bitisik_yazilar(e, olcek)
        ],
        "yazi_cizimden_tasiyor": _tasanlar(e, olcek),
        "uzak_olcu": _uzaklar(e, olcek) if cizim in UZAK_CIZIMLER else [],
        "etiket_kuyu_disinda": _disaridakiler(e, olcek),
        "kapi_no_kat_adi": _kapi_numaralari(e),
        "isaret_birligi": _isaretler(e),
    }


def sayilar(e, olcek=20, cizim=None):
    """{ kural : sayı } — yalnız sıfırdan büyükler."""
    return {k: len(v) for k, v in karne(e, olcek, cizim).items() if v}


def altin_karnesi():
    """Altın düzenlerin karnesi:  { düzen : { çizim : { kural : sayı } } } —
    çizimleri altın kayıttan ( testler/altin_cizim — bugünkü kodun çıktısı
    olduğunu test_altin_cizim denetler )."""
    out = {}
    for duzen, kayit in sorted(altin_cizim.oku().items()):
        c = {
            ad: s
            for ad, cizim in sorted((kayit.get("cizimler") or {}).items())
            if (s := sayilar(cizim["elemanlar"], cizim["olcek"], ad))
        }
        if c:
            out[duzen] = c
    return out


def oku(yol):
    if not os.path.exists(yol):
        return {}
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def yaz(yol, kayit):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def farklar(eski, yeni):
    """( kötüleşenler , iyileşenler ) — [ ileti ];  kayıtlar { düzen : { çizim :
    { kural : sayı } } }."""
    kotu, iyi = [], []
    for duzen in sorted(set(eski) | set(yeni)):
        e, y = eski.get(duzen, {}), yeni.get(duzen, {})
        for ad in sorted(set(e) | set(y)):
            ec, yc = e.get(ad, {}), y.get(ad, {})
            for kural in sorted(set(ec) | set(yc)):
                a, b = ec.get(kural, 0), yc.get(kural, 0)
                if a != b:
                    adi = KURALLAR.get(kural) or TARAMA_KURALLARI.get(kural, kural)
                    ileti = f"{duzen} · {ad} · {adi}:  {a} → {b}"
                    (kotu if b > a else iyi).append(ileti)
    return kotu, iyi


def toplamlar(kayit):
    """{ kural : ( bulgu , düzen ) } — kaydın özeti."""
    bulgu, duzen = collections.Counter(), collections.Counter()
    for c in kayit.values():
        gorulen = set()
        for s in c.values():
            for kural, n in s.items():
                bulgu[kural] += n
                gorulen.add(kural)
        for kural in gorulen:
            duzen[kural] += 1
    return {k: (bulgu[k], duzen[k]) for k in (*KURALLAR, *TARAMA_KURALLARI) if bulgu[k]}


def main(argv):
    yeni = altin_karnesi()
    if "--yenile" in argv:
        yaz(ALTIN_KAYDI, yeni)
        print(f"karne kaydı yazıldı:  {os.path.relpath(ALTIN_KAYDI, KOK)}")
    else:
        kotu, iyi = farklar(oku(ALTIN_KAYDI), yeni)
        for i in kotu:
            print("KÖTÜLEŞTİ  " + i)
        for i in iyi:
            print("İYİLEŞTİ   " + i)
    for kural, (n, d) in toplamlar(yeni).items():
        print(f"{(KURALLAR.get(kural) or TARAMA_KURALLARI[kural]):48s} {n:5d} bulgu  ·  {d} düzen")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
