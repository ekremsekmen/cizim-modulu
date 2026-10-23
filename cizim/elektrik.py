# -*- coding: utf-8 -*-
"""
ELEKTRİK PROJESİ — asansörün tek hat şeması ( TAS ), kuyu tesisatı, topraklama
tesisatı, ana tablo yerleşimi ve sembol listesi;  paftada kapağın yanında, alt
satırın solunda ( kullanıcı isteği 23 Eki — ofisin elle hazırladığı projenin
düzeni:  referans 4815-6 AVAN paftası ).

DEĞERLER HESAPTAN ( motor/avan/avan_hesabi._elektrik_projesi ):  kuyu ve kabin
armatürlerinin adedi ve gücü ( kuyuya hesabın bulduğu kadar armatür çizilir ),
motor gücü, akımı ve sigortası, devre sigortaları ( kurulu güç cetveli ), kolon
hattı ( kesit / koruma iletkeni / kablo tipi ), makine besleme hattının koruma
iletkeni, güç devresinin kaçak akım rölesinin IΔn'ı ( topraklama hesabının ofis
standardı ).  Hesabın seçmediği cihazların değerleri hesabın sigortalarından
KURALLA çıkar ( anma_akimlari, devre_kesiti — kurallar ve kaynakları aşağıda ):
şalterlerin ve kaçak akım rölelerinin anma akımı, aydınlatma ve priz devrelerinin
30 mA'i, son devrelerin kabloları.  Kontrol panosunun içi ( termiğin aralığı,
kumanda sigortası ) imalatçınındır, yazılmaz — referans paftadaki "17-22A" başka
bir motorun değeriydi;  termiğin ayarlanacağı motor akımı yazılır.

ÖLÇEKSİZ ŞEMADIR:  kâğıt mm'siyle kurulur, eleman 1/20 biriminde ( × 20 —
yazı ve kalem boyları öbür çizimlerle aynı;  uslup ).  A3 yatay sayfa
( 420 × 297 ):  paftada iki A4 hücresi ( ciktilar/dxf_cikti ).
"""

import math

from cizim import dxf
from cizim import eleman
from cizim import pafta
from cizim import uslup

BASLIK = "ELEKTRİK PROJESİ"
#  Sayfanın boyu ( kâğıt mm ) — paftada A4 hücresinin iki katı eninde, bir katı boyunda
EN, BOY = 420.0, 297.0
K = 20.0  # kâğıt mm'si → çizim birimi ( 1/20 )
SERIT = 11.0  # alttaki künye şeridi ( geometri.cerceveli'nin 220 birimi )

N, H, B = uslup.NORMAL, uslup.HARF, uslup.BASLIK  # yazı:  2,5 · 3,5 · 5 mm

HAT, CIHAZ, TOPRAK, YAPI = "ELK-HAT", "ELK-CIHAZ", "ELK-TOPRAK", "KUYU-IC"


# ══════════════════════════════════════════════════════════════════════
#  ELEMANLAR ( kâğıt mm'siyle )
# ══════════════════════════════════════════════════════════════════════
def _ad(el, ad):
    if ad:
        el["ad"] = ad
    return el


def _cizgi(kat, x1, y1, x2, y2, ad=""):
    return _ad(eleman.cizgi(kat, x1 * K, y1 * K, x2 * K, y2 * K), ad)


def _daire(kat, x, y, r, ad=""):
    return _ad(eleman.daire(kat, x * K, y * K, r * K), ad)


def _kutu(kat, x, y, g, d, ad=""):
    return eleman.dikdortgen(kat, x * K, y * K, g * K, d * K, ad=ad)


def _cokgen(kat, noktalar, kapali=True, dolu=False, ad=""):
    """Çokgen ya da açık çoklu çizgi ( parcalar'ın "bicim"i );  zarf kutusu
    noktaların kapsayanı ( geometri.sinir zarfa bakar )."""
    xs, ys = [p[0] for p in noktalar], [p[1] for p in noktalar]
    el = eleman.dikdortgen(
        kat, min(xs) * K, min(ys) * K, (max(xs) - min(xs)) * K, (max(ys) - min(ys)) * K, ad=ad
    )
    el["bicim"] = [{"noktalar": [(x * K, y * K) for x, y in noktalar], "kapali": kapali, "dolu": dolu}]
    return el


def _yay_noktalari(cx, cy, r, a0, a1, adim=12):
    """a0 → a1 ( derece, saat yönünün tersi ) arasındaki yayın noktaları."""
    n = max(2, int(abs(a1 - a0) / adim) + 1)
    return [
        (
            cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
            cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))),
        )
        for i in range(n)
    ]


def _yazi(x, y, metin, h=N, hiza="sol", aci=0, kat="YAZI"):
    return eleman.yazi(x * K, y * K, metin, h, hiza=hiza, katman=kat, aci=aci)


def _en(metin, h=N):
    """Yazının kâğıttaki eni ( mm )."""
    return eleman.yazi_eni(metin, h) / K


def _sayi(x):
    """Türkçe ondalık:  4.9 → "4,9", 6.0 → "6"."""
    return f"{x:g}".replace(".", ",")


def _nokta(x, y, kat=HAT):
    """Bağlantı noktası ( dolu küçük daire )."""
    return _cokgen(kat, _yay_noktalari(x, y, 0.5, 0, 360, 45), dolu=True)


# ══════════════════════════════════════════════════════════════════════
#  SEMBOLLER — her biri ( x , y ) merkezli, hat yatayken
# ══════════════════════════════════════════════════════════════════════
def otomatik_sigorta(x, y, kutup=1):
    """Otomatik sigorta:  kutu, kutuda bölme ve eğik çizgi ( referans paftanın
    sembolü );  3F+N grup sigortasında iki bölme."""
    ad = "otomatik_sigorta" if kutup == 1 else "grup_sigorta"
    g, d = 8.0, 3.2
    e = [
        _kutu(CIHAZ, x - g / 2, y - d / 2, g, d, ad=ad),
        _cizgi(CIHAZ, x - 2.2, y - 3.0, x + 2.2, y + 3.0, ad),
    ]
    for bx in (x - 1.8,) if kutup == 1 else (x - 1.8, x + 1.8):
        e.append(_cizgi(CIHAZ, bx, y - d / 2, bx, y + d / 2, ad))
    return e


def _salter_bicagi(x, y, ad, cizik=0):
    """Açık kontaklı şalter:  sol kontak, bıçak, sağ kontak ( x-3 … x+3 );
    cizik:  bıçağı kesen kısa çizgiler ( kutup işareti )."""
    r = 0.6
    e = [
        _daire(CIHAZ, x - 3, y, r, ad),
        _daire(CIHAZ, x + 3, y, r, ad),
        _cizgi(CIHAZ, x - 3 + r, y + 0.3, x + 2.6, y + 2.8, ad),
    ]
    for i in range(cizik):
        cx, cy = x - 1.3 + i * 0.9, y + 1.1 + i * 0.62
        e.append(_cizgi(CIHAZ, cx - 0.5, cy + 0.9, cx + 0.5, cy - 0.9, ad))
    return e


def kacak_akim_rolesi(x, y):
    """Kaçak akım rölesi:  üç kutuplu şalter ve hattın altında algılayıcı kutusu."""
    ad = "kacak_akim_rolesi"
    e = _salter_bicagi(x - 2, y, ad, cizik=3)
    e += [_kutu(CIHAZ, x + 2.2, y - 1.0, 3.6, 2.0, ad), _cizgi(CIHAZ, x + 1.6, y, x + 2.2, y, ad)]
    return e


def pako_salter(x, y):
    """Pako şalter:  üç kutuplu açık şalter."""
    return _salter_bicagi(x, y, "pako_salter", cizik=3)


def kesici_salter(x, y):
    """Kesici şalter ( asansörün ana şalteri ):  kutunun içinde açık şalter."""
    ad = "kesici_salter"
    return [_kutu(CIHAZ, x - 5.5, y - 3.5, 11, 7, ad)] + _salter_bicagi(x, y - 1.0, ad)


def motor(x, y, r=6.0):
    ad = "motor"
    return [
        _daire(CIHAZ, x, y, r, ad),
        _yazi(x, y + 1.6, "M", N, "orta"),
        _yazi(x, y - 2.0, "3~", N, "orta"),
    ]


def sayac(x, y, r=5.0):
    return [_daire(CIHAZ, x, y, r, "sayac"), _yazi(x, y, "kWh", N, "orta")]


def etanj_armatur(x, y):
    """Etanj armatür ( kuyu ):  hattan çıkan kısa kol, gövde, ışık yayan yarısı dolu
    ( referans paftanın kuyu armatürü ) — sol uç ( x , y )."""
    ad = "etanj_armatur"
    return [
        _cizgi(CIHAZ, x, y, x + 2.0, y, ad),
        _kutu(CIHAZ, x + 2.0, y - 0.9, 8.0, 1.8, ad),
        _cokgen(
            CIHAZ,
            [(x + 6.0, y - 0.9), (x + 10.0, y - 0.9), (x + 10.0, y + 0.9), (x + 6.0, y + 0.9)],
            dolu=True,
            ad=ad,
        ),
    ]


def led_spot(x, y, r=2.0):
    """Armatür ( IEC 60617:  çarpılı daire ) — kabin ve kabin üstü LED spot."""
    ad = "led_spot"
    d = r * math.sqrt(0.5)
    return [
        _daire(CIHAZ, x, y, r, ad),
        _cizgi(CIHAZ, x - d, y - d, x + d, y + d, ad),
        _cizgi(CIHAZ, x - d, y + d, x + d, y - d, ad),
    ]


def anahtar(x, y, vavien=True, yon=1):
    """Aydınlatma anahtarı:  bağlantı dairesi ( x , y ), eğik kol, ucunda çizik
    ( vavien:  iki );  yon −1 ise kol sola."""
    ad = "vavien_anahtar" if vavien else "anahtar"
    r = 0.7
    ux, uy = x + yon * (r * 0.7 + 3.0), y + r * 0.7 + 3.0
    e = [_daire(CIHAZ, x, y, r, ad), _cizgi(CIHAZ, x + yon * r * 0.7, y + r * 0.7, ux, uy, ad)]
    for i in range(2 if vavien else 1):
        px, py = ux - yon * i * 1.0, uy - i * 1.0
        e.append(_cizgi(CIHAZ, px, py, px + yon * 0.9, py - 0.9, ad))
    return e


def stop_butonu(x, y, r=1.8):
    """Stop ( durdurma ) butonu:  alt yarısı dolu daire."""
    ad = "stop_butonu"
    return [
        _daire(CIHAZ, x, y, r, ad),
        _cokgen(CIHAZ, _yay_noktalari(x, y, r, 180, 360, 15), dolu=True, ad=ad),
    ]


def buton(x, y, r=1.3):
    return [_daire(CIHAZ, x, y, r, "buton")]


def priz(x, y, yon=1):
    """Topraklı priz:  düz yüzü hatta bakan yarım daire ve koruma kontağı;  sol
    uç ( x , y ), yon −1 ise sola bakar."""
    ad = "toprakli_priz"
    r = 2.0
    yay = _yay_noktalari(x, y, r, -90, 90, 15) if yon > 0 else _yay_noktalari(x, y, r, 90, 270, 15)
    return [
        _cizgi(CIHAZ, x, y - r, x, y + r, ad),
        _cokgen(CIHAZ, yay, kapali=False, ad=ad),
        _cizgi(CIHAZ, x, y + r + 0.9, x + yon * (r + 0.6), y + r + 0.9, ad),
    ]


def buat(x, y, a=3.0):
    return [_kutu(CIHAZ, x - a / 2, y - a / 2, a, a, "buat")]


def topraklama(x, y):
    """Toprak ( IEC 60617-02-15-01 ):  üstte bağlantı ( x , y ), altta üç çizgi."""
    ad = "topraklama"
    e = [_cizgi(TOPRAK, x, y, x, y - 3.0, ad)]
    for i, w in enumerate((4.0, 2.6, 1.2)):
        e.append(_cizgi(TOPRAK, x - w, y - 3.0 - i * 1.3, x + w, y - 3.0 - i * 1.3, ad))
    return e


def topraklama_barasi(x, y, g=12.0, d=1.6):
    return [
        _cokgen(TOPRAK, [(x, y), (x + g, y), (x + g, y + d), (x, y + d)], dolu=True, ad="topraklama_barasi")
    ]


def kirik(x, y, yatay=False):
    """Hattın kırığı ( boyu çizilmeyen uzun hat ):  iki dalgalı çizgi."""
    e = []
    for d in (-0.9, 0.9):
        nok = [(x - 3.0 + 1.5 * i, y + d + (0.6 if i % 2 else -0.6)) for i in range(5)]
        if yatay:
            nok = [(x + (py - y), y + (px - x)) for px, py in nok]
        e.append(_cokgen(HAT, nok, kapali=False))
    return e


# ══════════════════════════════════════════════════════════════════════
#  ŞALTERLERİN, KAÇAK AKIM RÖLELERİNİN VE DEVRE KABLOLARININ DEĞERLERİ
# ══════════════════════════════════════════════════════════════════════
#  Hesap bu cihazları seçmez;  değerleri hesabın sigortalarından kuralla çıkar
#  ( 23 Eki — kullanıcının onayıyla;  araştırma:  Asansör Periyodik Kontrol
#  Yönetmeliği EK-5 kontrol listesi ):
#  · Şalterin ve kaçak akım rölesinin anma akımı birlikte çalıştığı sigortadan
#    küçük olmaz ( kontakları sigortanın geçirdiği akımı taşımalı ), sonra
#    piyasanın standart kademesi.  Referans paftadaki 4x25A sigorta → 5x32A
#    kesici → 4x40A K.A.R sırası da bu kurala uyar.
#  · Kaçak akım iki yerde ( EK-5 1.33.11 · 12 · 14 ):  güç devresininki
#    topraklama direncine göre ( hesabın IΔn'ı — Re ≤ UL / IΔn ), aydınlatma
#    ve priz devrelerininki 30 mA.
#  · Son devrenin kablosu:  sigorta kablonun sınırını aşmaz ( EK-5 1.31.13 ),
#    aydınlatma linyesi en az 1,5, priz linyesi en az 2,5 mm² ( Elektrik İç
#    Tesisleri Yönetmeliği );  üç damar ( faz, nötr, koruma ), kablo kolon
#    hattının ailesinden ( ofisin NHXMH'si — halojensiz ).
SALTER_KADEMELERI = (16, 20, 25, 32, 40, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630)  # yük ayırıcı
KAR_KADEMELERI = (25, 40, 63, 80, 100, 125)  # kaçak akım rölesi ( üstü röleli kesici:  şalter kademesi )
KAYNAK_KAR_MA = 30  # aydınlatma ve priz devrelerinin kaçak akım rölesi ( EK-5 1.33.11 · 12 )
#  EK-5 1.31.13:  ( kesit mm² , en büyük sigorta A )
KESIT_SIGORTA = ((1.0, 6), (1.5, 10), (2.5, 20), (4.0, 32), (6.0, 50))
AYDINLATMA_KESIT_EN_AZ, PRIZ_KESIT_EN_AZ = 1.5, 2.5


def _kademe(akim, kademeler):
    """akim'dan küçük olmayan ilk standart kademe ( yoksa None )."""
    if not akim:
        return None
    return next((k for k in kademeler if k >= akim - 1e-9), None)


def anma_akimlari(v):
    """Kuraldan anma akımları ( A;  None:  hesabın sigortası yok ):  güç
    devresinin kaçak akım rölesi, kesici ( ana ) şalter, aydınlatma ve priz
    devrelerinin kaçak akım rölesi, tablonun pako şalteri."""
    grup = v.get("motor_sigorta_A")
    devre = max(v[k]["sigorta_A"] for k in ("kabin", "priz", "kuyu"))
    guc = _kademe(grup, KAR_KADEMELERI) or _kademe(grup, SALTER_KADEMELERI)
    ayd = _kademe(devre, KAR_KADEMELERI)
    return {
        "guc_kar": guc,
        "kesici": _kademe(grup, SALTER_KADEMELERI),
        "ayd_kar": ayd,
        #  Pako bütün tablonun girişi:  motorun sigortası bilinmiyorsa onunki de
        "pako": _kademe(max(guc, ayd), SALTER_KADEMELERI) if guc else None,
    }


def devre_kesiti(amper, en_az):
    """Son devrenin kesiti ( mm² ):  sigortayı taşıyan, en az `en_az` olan ilk kesit."""
    return next((s for s, a in KESIT_SIGORTA if s >= en_az and a >= amper), None)


def devre_kablosu(v, amper, en_az):
    kesit = devre_kesiti(amper, en_az)
    if kesit is None:
        return ""
    aile = (v["kolon"].get("kablo") or "").split()
    return f"3x{_sayi(kesit)} mm²" + (f" {aile[0]}" if aile else "")


def _ma(akim_A):
    return f"{_sayi(round(akim_A * 1000, 3))} mA"


# ══════════════════════════════════════════════════════════════════════
#  TEK HAT ŞEMASI ( TAS )
# ══════════════════════════════════════════════════════════════════════
#  Bara ve devreler ( kâğıt mm )
_BARA_X, _BARA_Y0, _BARA_Y1 = 40.0, 250.0, 282.0
_MOTOR_Y, _KABIN_Y, _PRIZ_Y, _KUYU_Y = 280.0, 266.0, 256.0, 246.0
_BESLEME_Y = 266.0
_FAZ_X, _PE_X = 16.0, 26.0
_PAKO_X = 28.0
_KAR_X = 52.0  # güç ve aydınlatma devrelerinin kaçak akım röleleri
_ALT_BARA_X = 62.0  # aydınlatma ve priz devrelerinin barası ( 30 mA'in arkası )
_SIGORTA_X = 71.0
_KESICI_X = 89.0
_PANO = (101.0, 271.5, 36.0, 16.0)  # x, y, g, d
_PANO_X = _PANO[0] + _PANO[2] / 2.0  # kontrol panosunun ortası
_MOTOR_X = 149.0
_TOPRAK_BARASI_Y = 233.0
_MOTOR_PE_X = 198.0  # motorun koruma iletkeni devre yazılarının sağından iner
_KUMANDA_Y = 293.5
#  Sigortanın anma akımı sigortanın üstünde:  yazının maskesi ( PDF'te alt uzantılı
#  harflerle 2,4 mm ) sigortanın eğik çizgisinin ucunu örtmesin
_AMPER_YUKSEKLIGI = 6.2
_CIHAZ_ADI = 10.2  # cihazın adı amper yazısının üstünde
#  Aydınlatma ve priz devrelerinin sigortaları;  amper yazısı sigortanın sol üstünde
#  ( üstte olunca bir üstteki devrenin sigortasına daha yakın düşüyordu ), devrenin
#  kablosu hattın üstünde, adı altında
_DEVRE_SIGORTA_X = 78.0
_DEVRE_AMPER = (68.5, 3.4)  # x , hattan yukarı
_DEVRE_YAZISI_X = 86.0


def _devre_metni(ad, adet, w):
    return f"{ad}  ( {adet}x{_sayi(w)} W )"


def tek_hat(v):
    """TAS:  besleme ( sayaç → kolon hattı → pako şalter ) ve bara;  motor
    devresi ( güç kaçak akım rölesi → grup sigorta → kesici şalter → kontrol
    panosu → motor );  aydınlatma ve priz devreleri ( 30 mA kaçak akım rölesi →
    alt bara → devre sigortaları ), topraklama barası.  Devrelerin hatları sağa,
    kuyu tesisatına uzar ( kuyu_tesisati )."""
    e = []
    bx = _BARA_X
    anma = anma_akimlari(v)
    e.append(
        _cokgen(
            CIHAZ,
            [(bx - 1.2, _BARA_Y0), (bx + 1.2, _BARA_Y0), (bx + 1.2, _BARA_Y1), (bx - 1.2, _BARA_Y1)],
            dolu=True,
            ad="tablo_barasi",
        )
    )
    e.append(_yazi(bx - 4.0, 276.0, v["tablo"], H, "sag"))
    e += _besleme(v, anma)
    e += _motor_devresi(v, anma)
    e += _aydinlatma_devreleri(v, anma)
    return e


def _besleme(v, anma):
    """Sayaç ( altta ) → kolon hattı → pako şalter → bara;  koruma iletkeni
    temel topraklamasından topraklama barasına."""
    e = []
    bx, y0, fx = _BARA_X, _BESLEME_Y, _FAZ_X
    e += sayac(fx, 141.0)
    e.append(_cizgi(HAT, fx, 136.0, fx, 128.0))
    e += [_yazi(fx, 124.5, "Şebeke", N, "orta"), _yazi(fx, 120.0, "( 3F+N )", N, "orta")]
    e.append(_cizgi(HAT, fx, 146.0, fx, 172.0))
    e += kirik(fx, 175.0)
    e += kirik(_PE_X, 175.0)
    e.append(_cizgi(HAT, fx, 178.0, fx, y0))
    e.append(_cizgi(HAT, fx, y0, _PAKO_X - 3.6, y0))
    e += pako_salter(_PAKO_X, y0)
    e.append(_cizgi(HAT, _PAKO_X + 3.6, y0, bx - 1.2, y0))
    e += [_yazi(_PAKO_X, y0 - 5.0, "Pako", N, "orta"), _yazi(_PAKO_X, y0 - 9.0, "şalter", N, "orta")]
    if anma["pako"]:
        e.append(_yazi(_PAKO_X, y0 - 13.0, f"4x{anma['pako']}A", N, "orta"))
    # kolon hattının kablosu
    k = v["kolon"]
    kablo = f"4x{_sayi(k['S'])}" + (f"/{_sayi(k['SPE'])}" if k.get("SPE") else "") + f" {k['kablo']}".rstrip()
    e.append(_cizgi(HAT, fx - 1.4, 199.0, fx + 1.4, 201.6))
    e.append(_yazi(fx + 13.0, 205.0, "Kolon hattı", N))
    e.append(_yazi(fx + 13.0, 200.3, kablo, N))
    # koruma iletkeni:  temel topraklaması → topraklama barası
    px = _PE_X
    e += topraklama(px, 118.0)
    e.append(_yazi(px + 5.0, 113.5, "TEMEL TOPRAKLAMASINA BAĞLANACAK", N))
    e.append(_cizgi(TOPRAK, px, 118.0, px, 172.0))
    e.append(_cizgi(TOPRAK, px, 178.0, px, _TOPRAK_BARASI_Y + 0.8))
    e.append(_cizgi(TOPRAK, px, _TOPRAK_BARASI_Y + 0.8, bx - 6.0, _TOPRAK_BARASI_Y + 0.8))
    e += topraklama_barasi(bx - 6.0, _TOPRAK_BARASI_Y, 14.0)
    #  Sola yaslı, baranın ucundan:  ortalanınca solundaki koruma iletkenine biniyordu
    e.append(_yazi(bx - 6.0, _TOPRAK_BARASI_Y - 3.6, "Topraklama barası", N))
    if k.get("SPE"):
        e.append(_yazi(px + 2.6, 148.0, f"PE {_sayi(k['SPE'])} mm² Cu", N, "orta", aci=90))
    return e


def _motor_devresi(v, anma):
    """Bara → güç kaçak akım rölesi ( IΔn hesaptan — topraklama direncine göre )
    → grup sigorta → kesici ( ana ) şalter → kontrol panosu → motor;  motorun
    koruma iletkeni topraklama barasına."""
    e = []
    y, bx = _MOTOR_Y, _BARA_X
    e.append(_cizgi(HAT, bx + 1.2, y, _KAR_X - 5.6, y))
    e += kacak_akim_rolesi(_KAR_X, y)
    e.append(_yazi(_KAR_X, y + _CIHAZ_ADI, "K.A.R", N, "orta"))
    if anma["guc_kar"]:
        e.append(_yazi(_KAR_X, y + _AMPER_YUKSEKLIGI, f"4x{anma['guc_kar']}A", N, "orta"))
    if v.get("kacak_akim_A"):
        e.append(_yazi(_KAR_X, y - 5.0, f"IΔn {_ma(v['kacak_akim_A'])}", N, "orta"))
    e.append(_cizgi(HAT, _KAR_X + 5.8, y, _SIGORTA_X - 4.0, y))
    e += otomatik_sigorta(_SIGORTA_X, y, kutup=4)
    a = v.get("motor_sigorta_A")
    e.append(_yazi(_SIGORTA_X, y + _AMPER_YUKSEKLIGI, f"4x{a}A" if a else "3F+N", N, "orta"))
    e.append(_cizgi(HAT, _SIGORTA_X + 4.0, y, _KESICI_X - 5.5, y))
    e += kesici_salter(_KESICI_X, y)
    e.append(_yazi(_KESICI_X, y + _CIHAZ_ADI, "Kesici şalter", N, "orta"))
    if anma["kesici"]:
        e.append(_yazi(_KESICI_X, y + _AMPER_YUKSEKLIGI, f"4x{anma['kesici']}A", N, "orta"))
    px0, py0, pg, pd = _PANO
    e.append(_cizgi(HAT, _KESICI_X + 5.5, y, px0, y))
    #  Kontrol panosu:  içi imalatçının ( faz sırası rölesi, motor koruması, kumanda )
    e.append(_kutu(CIHAZ, px0, py0, pg, pd, "kontrol_panosu"))
    e.append(_yazi(_PANO_X, 282.0, "KONTROL PANOSU", N, "orta"))
    e.append(_yazi(_PANO_X, 276.0, "Sıralı faz rölesi", N, "orta"))
    mx = _MOTOR_X
    e.append(_cizgi(HAT, px0 + pg, y, mx - 6.0, y))
    e += motor(mx, y)
    e.append(_yazi(mx + 8.5, y + 2.6, "ASANSÖR MOTORU", N))
    guc = f"{_sayi(v['motor_kW'])} kW"
    if v.get("motor_akimi_A"):
        #  Termiğin ayarı motorun çektiği akıma uygun olmalı ( EK-5 1.37 )
        guc += f"  ·  I = {_sayi(round(v['motor_akimi_A'], 2))} A"
    e.append(_yazi(mx + 8.5, y - 2.6, guc, N))
    # motorun koruma iletkeni ( makine besleme hattı ):  devrelerin yazılarının
    # sağından topraklama barasına
    py = y - 8.0
    px = _MOTOR_PE_X
    e += [
        _cizgi(TOPRAK, mx, y - 6.0, mx, py),
        _cizgi(TOPRAK, mx, py, px, py),
        _cizgi(TOPRAK, px, py, px, _TOPRAK_BARASI_Y + 0.8),
        _cizgi(TOPRAK, px, _TOPRAK_BARASI_Y + 0.8, bx + 8.0, _TOPRAK_BARASI_Y + 0.8),
    ]
    spe = (v.get("makine_besleme") or {}).get("SPE")
    if spe:
        e.append(_yazi(px - 2.0, _TOPRAK_BARASI_Y + 3.4, f"PE {_sayi(spe)} mm² Cu", N, "sag"))
    return e


def _aydinlatma_devreleri(v, anma):
    """Bara → 30 mA kaçak akım rölesi → alt bara → kabin ( + kabin üstü ), priz ve
    kuyu aydınlatması sigortaları;  her devrenin üstünde kablosu, altında adı ve
    yükü ( kurulu güç cetvelinin satırı )."""
    e = []
    bx, ax, yk = _BARA_X, _ALT_BARA_X, _PRIZ_Y
    e.append(_cizgi(HAT, bx + 1.2, yk, _KAR_X - 5.6, yk))
    e += kacak_akim_rolesi(_KAR_X, yk)
    e.append(_cizgi(HAT, _KAR_X + 5.8, yk, ax, yk))
    e += [_cizgi(HAT, ax, _KUYU_Y, ax, _KABIN_Y), _nokta(ax, yk)]
    e += [
        _yazi(_KAR_X, yk - 5.6, "K.A.R", N, "orta"),
        _yazi(_KAR_X, yk - 9.6, f"{KAYNAK_KAR_MA} mA", N, "orta"),
    ]
    if anma["ayd_kar"]:
        e.append(_yazi(_KAR_X, yk - 13.6, f"2x{anma['ayd_kar']}A", N, "orta"))
    kb, ku, pr, kuyu = v["kabin"], v["kabin_ustu"], v["priz"], v["kuyu"]
    devreler = (
        (
            _KABIN_Y,
            kb["sigorta_A"],
            AYDINLATMA_KESIT_EN_AZ,
            f"Kabin + kabin üstü aydınlatması  ( {kb['adet']}x{_sayi(kb['W'])} W + {ku['adet']}x{_sayi(ku['W'])} W )",
        ),
        (_PRIZ_Y, pr["sigorta_A"], PRIZ_KESIT_EN_AZ, _devre_metni("Priz", pr["adet"], pr["W"])),
        (
            _KUYU_Y,
            kuyu["sigorta_A"],
            AYDINLATMA_KESIT_EN_AZ,
            _devre_metni("Kuyu aydınlatması", kuyu["adet"], kuyu["W"]),
        ),
    )
    for y, amper, en_az, metin in devreler:
        e.append(_cizgi(HAT, ax, y, _DEVRE_SIGORTA_X - 4.0, y))
        if y != yk:
            e.append(_nokta(ax, y))
        e += otomatik_sigorta(_DEVRE_SIGORTA_X, y)
        e.append(_yazi(_DEVRE_AMPER[0], y + _DEVRE_AMPER[1], f"{amper} A", N, "orta"))
        kablo = devre_kablosu(v, amper, en_az)
        if kablo:
            e.append(_yazi(_DEVRE_YAZISI_X, y + 2.6, kablo, N))
        e.append(_yazi(_DEVRE_YAZISI_X, y - 2.6, metin, N))
    return e


# ══════════════════════════════════════════════════════════════════════
#  KUYU TESİSATI
# ══════════════════════════════════════════════════════════════════════
#  Kuyu ( iç duvarlar ), üstte makine kutusu, aydınlatma hattı solda, kabin /
#  priz / kumanda hattı sağda ( kâğıt mm )
_KX0, _KX1, _KY0 = 206.0, 286.0, 22.0
_DUVAR = 2.5
_UST_Y0, _UST_Y1 = 213.0, 239.0  # makine kutusu ( dış )
_ISIK_X, _SAG_X = 214.0, 280.0
_KABIN = (226.0, 150.0, 36.0, 42.0)  # iç:  x, y, g, d
_BUAT_Y = 128.0
#  Kuyu armatürleri:  en üstteki makine kutusunun altında, öbürleri kabinin
#  altından kuyu dibine eşit aralıkla ( en alttaki kuyu dibinde )
_ARMATUR_UST, _ARA_UST, _ARMATUR_ALT = 207.0, 140.0, 30.0
_ARA_ADIM_EN_AZ = 5.5


def _cift_cizgi_kutu(x0, y0, x1, y1, ust=True):
    """Duvar:  iç ve dış çizgi ( ust False:  üst kenar açık — kutu oturur )."""
    e = []
    for d in (0.0, _DUVAR):
        a0, b0, a1, b1 = x0 - d, y0 - d, x1 + d, y1 + (d if ust else 0.0)
        e += [_cizgi(YAPI, a0, b0, a1, b0), _cizgi(YAPI, a0, b0, a0, b1), _cizgi(YAPI, a1, b0, a1, b1)]
        if ust:
            e.append(_cizgi(YAPI, a0, b1, a1, b1))
    return e


def armatur_kotlari(adet):
    """Kuyu armatürlerinin kâğıttaki y'leri ( üstten aşağı ) ve kırık:  çok
    armatürde aradakilerin bir kısmı çizilmez — ( kotlar , kırığın y'si ya da
    None ).  Hesabın bulduğu adet kadar armatür kuyuya konur;  sığmayanlar
    kırıkla gösterilir, kırığın yazısı toplamı söyler."""
    if adet <= 0:
        return [], None
    if adet == 1:
        return [_ARMATUR_UST], None
    alt = adet - 1  # kabinin altındakiler
    if alt == 1:
        return [_ARMATUR_UST, _ARMATUR_ALT], None
    sigan = int((_ARA_UST - _ARMATUR_ALT) / _ARA_ADIM_EN_AZ) + 1
    if alt <= sigan:
        adim = (_ARA_UST - _ARMATUR_ALT) / (alt - 1)
        return [_ARMATUR_UST] + [_ARA_UST - i * adim for i in range(alt)], None
    #  Sığmayan:  üstten ve alttan birer kısım, ortada kırık
    yari = (sigan - 1) // 2
    ust = [_ARA_UST - i * _ARA_ADIM_EN_AZ for i in range(yari)]
    dip = [_ARMATUR_ALT + i * _ARA_ADIM_EN_AZ for i in reversed(range(yari))]
    return [_ARMATUR_UST] + ust + dip, (ust[-1] + dip[0]) / 2.0


def kuyu_tesisati(v):
    """Kuyu:  armatürler ( hesabın adedi ), kabin ve kabin üstü aydınlatması,
    prizler, stop butonları, vavien anahtarlar, gezici kablo ve buat.  TAS'ın
    devreleri üstten girer ( tek_hat )."""
    e = []
    x0, x1 = _KX0, _KX1
    e += _cift_cizgi_kutu(x0, _KY0, x1, _UST_Y0, ust=False)
    e += _cift_cizgi_kutu(x0, _UST_Y0 + _DUVAR, x1, _UST_Y1 - _DUVAR)
    ust_adi = "MAKİNE DAİRESİ" if v.get("makine_dairesi") else "KUYU ÜSTÜ"
    e.append(_yazi(x0 + 9.0, _UST_Y1 - 5.5, ust_adi, N))
    e.append(_yazi((x0 + x1) / 2.0, _KY0 - _DUVAR - 4.0, "KUYU", H, "orta"))
    e += _kuyu_aydinlatmasi(v)
    e += _sag_hat(v)
    e += _kabin(v)
    # kuyu dibinde kabin tamponu
    tx = _KABIN[0] + _KABIN[2] / 2.0
    e.append(
        _cokgen(
            YAPI,
            [(tx - 4, _KY0), (tx + 4, _KY0), (tx + 4, _KY0 + 5), (tx - 4, _KY0 + 5)],
            dolu=True,
            ad="tampon",
        )
    )
    return e


def _kuyu_aydinlatmasi(v):
    """TAS'tan gelen kuyu aydınlatması hattı, armatürler ve iki vavien anahtar
    ( makine kutusunda ve kuyu dibinde )."""
    e = []
    ix = _ISIK_X
    kuyu = v["kuyu"]
    e.append(_cizgi(HAT, _DEVRE_SIGORTA_X + 4.0, _KUYU_Y, ix, _KUYU_Y))
    kotlar, kirik_y = armatur_kotlari(kuyu["adet"])
    alt = min(kotlar + [_KY0 + 10.0])
    if kirik_y is None:
        e.append(_cizgi(HAT, ix, _KUYU_Y, ix, alt))
    else:
        e.append(_cizgi(HAT, ix, _KUYU_Y, ix, kirik_y + 3.0))
        e += kirik(ix, kirik_y)
        e.append(_cizgi(HAT, ix, kirik_y - 3.0, ix, alt))
        e.append(_yazi(ix + 12.0, kirik_y, f"( toplam {kuyu['adet']} adet )", N))
    #  Etanj ( korumalı ) armatür:  EN 81-20 5.2.1.4.1 aydınlatma elemanları mekanik
    #  hasara karşı korunur.  Referans paftadaki "U-" önekinin bir tanımı yoktu.
    metin = f"Etanj 1x{_sayi(kuyu['W'])} W"
    for y in kotlar:
        e.append(_nokta(ix, y))
        e += etanj_armatur(ix, y)
        e.append(_yazi(ix + 12.0, y, metin, N))
    # vavien anahtarlar:  makine kutusunda ve kuyu dibinde ( kuyunun iki ucundan yakılır )
    for y in (_UST_Y0 + 11.0, _KY0 + 14.0):
        e.append(_nokta(ix, y))
        e.append(_cizgi(HAT, ix, y, ix - 2.0, y))
        e += anahtar(ix - 2.7, y, vavien=True, yon=-1)
    return e


def _sag_hat(v):
    """Sağdaki hat:  kabin aydınlatması, priz ve kumanda TAS'tan üstten girer;
    makine kutusunda stop butonu ve priz, ortada buat ( gezici kablo kabine ),
    kuyu dibinde priz ve stop butonu."""
    e = []
    sx = _SAG_X
    # TAS'ın kabin ve priz devreleri, kontrol panosunun kumandası
    e.append(_cizgi(HAT, _DEVRE_SIGORTA_X + 4.0, _KABIN_Y, sx, _KABIN_Y))
    e.append(_cizgi(HAT, _DEVRE_SIGORTA_X + 4.0, _PRIZ_Y, sx, _PRIZ_Y))
    e.append(_nokta(sx, _PRIZ_Y))
    pano_ust = _PANO[1] + _PANO[3]
    e += [
        _cizgi(HAT, _PANO_X, pano_ust, _PANO_X, _KUMANDA_Y),
        _cizgi(HAT, _PANO_X, _KUMANDA_Y, sx, _KUMANDA_Y),
    ]
    e.append(_cizgi(HAT, sx, _KUMANDA_Y, sx, _KY0 + 10.0))
    e.append(_nokta(sx, _KABIN_Y))
    e.append(_yazi(sx - 2.0, _KUMANDA_Y - 3.0, "Kumanda", N, "sag"))
    # makine kutusunda:  stop butonu ve priz
    ys = _UST_Y1 - 12.0
    e += [_nokta(sx, ys), _cizgi(HAT, sx, ys, sx - 6.2, ys)]
    e += stop_butonu(sx - 8.0, ys)
    e.append(_yazi(sx - 11.5, ys, "Makine stop", N, "sag"))
    prizler = v["priz"]["adet"]
    yp = _UST_Y0 + 6.0
    if prizler >= 3:
        e += [_nokta(sx, yp), _cizgi(HAT, sx, yp, sx - 2.0, yp)]
        e += priz(sx - 2.0, yp, yon=-1)
        e.append(_yazi(sx - 6.5, yp, "Priz", N, "sag"))
    # buat ve gezici kablo
    e.append(_nokta(sx, _BUAT_Y))
    e += buat(sx - 4.0, _BUAT_Y)
    e.append(_cizgi(HAT, sx, _BUAT_Y, sx - 2.5, _BUAT_Y))
    kx = _KABIN[0] + _KABIN[2] - 4.0
    sol, sag_, dip = kx, sx - 5.5, _BUAT_Y - 14.0
    r = (sag_ - sol) / 2.0
    e.append(_cizgi(HAT, sol, _KABIN[1], sol, dip + r))
    e.append(_cokgen(HAT, _yay_noktalari(sol + r, dip + r, r, 180, 360, 12), kapali=False))
    e.append(_cizgi(HAT, sag_, dip + r, sag_, _BUAT_Y - 1.5))
    e.append(_yazi(sol + r, dip - 3.5, "Gezici kablo", N, "orta"))
    # kuyu dibi:  priz ve stop butonu
    if prizler >= 1:
        yp = _KY0 + 22.0
        e += [_nokta(sx, yp), _cizgi(HAT, sx, yp, sx - 2.0, yp)]
        e += priz(sx - 2.0, yp, yon=-1)
        e.append(_yazi(sx - 6.5, yp, "Priz", N, "sag"))
    ys = _KY0 + 10.0
    e += [_cizgi(HAT, sx, ys, sx - 6.2, ys)]
    e += stop_butonu(sx - 8.0, ys)
    #  İki satır:  kuyu dibinin armatür yazısı ( "Etanj 1x40 W" ) aynı yükseklikte olabilir
    e += [_yazi(sx - 11.5, ys + 2.0, "Kuyu dibi", N, "sag"), _yazi(sx - 11.5, ys - 2.0, "stop", N, "sag")]
    return e


def _kabin(v):
    """Kabin:  içinde LED spotlar ( hesabın adedi ) ve kapı açma butonu;  üstünde
    kabin üstü aydınlatması ve priz.  Gezici kablo sağ alttan girer."""
    e = []
    x, y, g, d = _KABIN
    e.append(_kutu(YAPI, x, y, g, d, "kabin"))
    kb, ku = v["kabin"], v["kabin_ustu"]
    giris = x + g - 4.0  # gezici kablonun girdiği yer;  kabinin iç hattı
    cx, ly = x + g / 2.0 - 2.0, y + d - 7.0
    # kabin aydınlatması
    e += led_spot(cx, ly)
    e.append(_yazi(cx, ly - 5.5, f"{kb['adet']}x{_sayi(kb['W'])}W Led Spot", N, "orta"))
    e.append(_yazi(cx, y + d / 2.0 - 4.0, "KABİN", H, "orta"))
    e += [_cizgi(HAT, giris, y, giris, ly), _cizgi(HAT, giris, ly, cx + 2.0, ly)]
    # kapı açma butonu
    bx, by = x + 5.0, y + 9.0
    e += buton(bx, by)
    e += [
        _cizgi(HAT, bx, by - 1.3, bx, y + 4.0),
        _cizgi(HAT, bx, y + 4.0, giris, y + 4.0),
        _nokta(giris, y + 4.0),
    ]
    e.append(_yazi(bx + 3.0, by + 2.0, "Kapı açma", N))
    e.append(_yazi(bx + 3.0, by - 2.0, "butonu", N))
    # kabin üstü:  armatür ve priz ( kabinin tavanından )
    if ku["adet"]:
        lx, uy = x + 9.0, y + d + 5.0
        e += led_spot(lx, uy)
        e.append(_cizgi(HAT, lx, y + d, lx, uy - 2.0))
        e.append(_yazi(lx, uy + 5.0, f"{ku['adet']}x{_sayi(ku['W'])}W Led Spot", N, "orta"))
    if v["priz"]["adet"] >= 2:
        px = x + g - 6.0
        e.append(_cizgi(HAT, px, y + d, px, y + d + 3.0))
        e += priz(px, y + d + 5.0, yon=1)
        e.append(_yazi(px, y + d + 11.0, "Priz", N, "orta"))
    return e


# ══════════════════════════════════════════════════════════════════════
#  TOPRAKLAMA TESİSATI · ANA TABLO YERLEŞİMİ · SEMBOL LİSTESİ
# ══════════════════════════════════════════════════════════════════════
_SAG_SUTUN = 298.0  # sağdaki iki şemanın solu


def topraklama_tesisati(v):
    """Topraklama barası ve paralel topraklama hatları ( referans paftanın
    şeması );  kesitler hesaptan:  kolon hattının koruma iletkeni ve faz
    kesitleri ( kolon · makine besleme — büyüğü )."""
    e = []
    x0 = _SAG_SUTUN
    e.append(_yazi(x0, 289.0, "TOPRAKLAMA TESİSATI", H))
    bx0, bx1, by0, by1 = x0 + 20.0, x0 + 26.0, 206.0, 276.0
    e.append(_kutu(TOPRAK, bx0, by0, bx1 - bx0, by1 - by0, "topraklama_barasi"))
    for i in range(int((by1 - by0) / 3.0)):
        ya = by0 + i * 3.0
        e.append(_cizgi(TOPRAK, bx0, ya, bx1, min(ya + 6.0, by1)))
    e += [
        _cizgi(YAPI, bx1 - 1.0, by1, bx1 + 5.0, by1 + 6.0),
        _cizgi(YAPI, bx1 + 5.0, by1 + 6.0, bx1 + 9.0, by1 + 6.0),
    ]
    e.append(_yazi(bx1 + 10.0, by1 + 6.0, "Topraklama barası", N))
    hedefler = (
        "Ana panoya",
        "Kontrol panosuna",
        "Kesici şalter ve regülatöre",
        "Makine - motor grubuna",
        "Diğer elektrikli cihazlara",
    )
    for i, metin in enumerate(hedefler):
        y = 268.0 - i * 12.0
        e.append(_cizgi(TOPRAK, bx1, y, bx1 + 20.0, y))
        e.append(_yazi(bx1 + 22.0, y, metin, N))
    # topraklama kolon hattı ( kolon hattının koruma iletkeni )
    k = v["kolon"]
    lx = x0 + 11.0
    e += [_cizgi(TOPRAK, lx, 196.0, lx, 240.0), _cizgi(TOPRAK, lx, 240.0, bx0, 240.0)]
    e.append(_yazi(lx - 7.0, 218.0, "Topraklama kolon hattı", N, "orta", aci=90))
    if k.get("SPE"):
        e.append(_yazi(lx - 3.2, 218.0, f"{_sayi(k['SPE'])} mm² Cu kablo", N, "orta", aci=90))
    faz = max(x for x in (k.get("S"), (v.get("makine_besleme") or {}).get("S")) if x)
    notlar = (
        "Paralel topraklama hatları faz kesitinden",
        f"az olmamak kaydıyla {_sayi(faz)} mm² Cu korumalı",
        "kablo olmalıdır.",
        "Bağlantılar pabuçla yapılacaktır.",
    )
    for i, n in enumerate(notlar):
        e.append(_yazi(bx0, 196.0 - i * 5.0, n, N))
    return e


def ana_tablo(v):
    """Asansör tablosunun ( TAS ) yerleşimi — tek hat şemasının aynısı:  ana
    besleme → pako şalter → bara;  bir yanda güç kaçak akım rölesi → dörtlü
    otomatik sigorta ( kesici şalter, kontrol panosu ve motor ), öbür yanda
    30 mA kaçak akım rölesi → aydınlatma ve priz sigortaları."""
    e = []
    x0 = _SAG_SUTUN
    anma = anma_akimlari(v)
    e.append(_yazi(x0, 157.0, "ANA TABLO YERLEŞİMİ", H))
    hx, by = x0 + 16.0, 144.0  # besleme hattı, bara

    def kutu(x, y, g, d, satirlar, ad):
        """Kutu ve ortasında satırlar ( maske altta 2,4, üstte 1,7 mm taşar:  0,34 yukarı )."""
        e.append(_kutu(CIHAZ, x, y, g, d, ad))
        for i, s in enumerate(satirlar):
            e.append(
                _yazi(x + g / 2.0, y + d / 2.0 + 0.34 + ((len(satirlar) - 1) / 2.0 - i) * 5.2, s, N, "orta")
            )

    # besleme:  kolon hattı → pako şalter → bara
    pako = ("3F+N", "Pako şalter") + ((f"4x{anma['pako']}A",) if anma["pako"] else ())
    kutu(x0 + 2.0, 100.0, 28.0, 16.0, pako, "pako_salter")
    e += [_cizgi(HAT, hx, 46.0, hx, 100.0), _cizgi(HAT, hx, 116.0, hx, by)]
    e += [
        _yazi(hx, 41.0, "3F+N", N, "orta"),
        _yazi(hx, 36.0, "Ana besleme", N, "orta"),
        _yazi(hx, 31.0, "( kolon hattı )", N, "orta"),
    ]
    # güç devresi:  kaçak akım rölesi → dörtlü otomatik sigorta → kesici şalter, pano, motor
    ox = x0 + 92.0
    ix = ox + 13.0
    kar = ("K.A.R",) + ((f"4x{anma['guc_kar']}A",) if anma["guc_kar"] else ())
    kar += (f"IΔn {_ma(v['kacak_akim_A'])}",) if v.get("kacak_akim_A") else ()
    kutu(ox, 114.0, 26.0, 18.0, kar, "kacak_akim_rolesi")
    a = v.get("motor_sigorta_A")
    kutu(
        ox,
        82.0,
        26.0,
        24.0,
        ("3F+N Dörtlü", "otomatik", "sigorta") + ((f"4x{a}A",) if a else ()),
        "grup_sigorta",
    )
    e += [_cizgi(HAT, hx, by, ix, by), _cizgi(HAT, ix, by, ix, 132.0), _cizgi(HAT, ix, 114.0, ix, 106.0)]
    e.append(_cizgi(HAT, ix, 82.0, ix, 62.0))
    e += [
        _yazi(ix, 57.0, "Kesici şalter,", N, "orta"),
        _yazi(ix, 52.0, "kontrol panosu", N, "orta"),
        _yazi(ix, 47.0, "ve motor devresine", N, "orta"),
    ]
    # aydınlatma ve priz:  30 mA kaçak akım rölesi → alt bara → devre sigortaları
    devreler = [
        ("Kabin ve kabin üstü aydınlatması", v["kabin"]["sigorta_A"]),
        ("Kuyu aydınlatması", v["kuyu"]["sigorta_A"]),
        ("Priz", v["priz"]["sigorta_A"]),
    ]
    if v.get("makine_dairesi"):
        devreler.insert(2, ("Makine dairesi aydınlatması", None))
    adim = 13.0 if len(devreler) <= 3 else 10.5
    xs = [x0 + 42.0 + i * adim for i in range(len(devreler))]
    kx = (xs[0] + xs[-1]) / 2.0
    ayd = ("K.A.R",) + ((f"2x{anma['ayd_kar']}A",) if anma["ayd_kar"] else ()) + (f"{KAYNAK_KAR_MA} mA",)
    kutu(kx - 12.0, 122.0, 24.0, 16.0, ayd, "kacak_akim_rolesi")
    e += [_cizgi(HAT, kx, by, kx, 138.0), _nokta(kx, by), _cizgi(HAT, kx, 122.0, kx, 116.0)]
    e += [_cizgi(HAT, xs[0], 116.0, xs[-1], 116.0), _nokta(kx, 116.0)]
    for x, (ad, amper) in zip(xs, devreler):
        e.append(_cizgi(HAT, x, 116.0, x, 109.0))
        e += _dikey_sigorta(x, 100.0)
        if amper:
            e.append(_yazi(x + 2.4, 112.5, f"{amper} A", N))
        e.append(_cizgi(HAT, x, 91.0, x, 89.0))
        e.append(_yazi(x, 87.0, ad, N, "sag", aci=90))
    return e


def _dikey_sigorta(x, y):
    """Ana tablodaki otomatik sigorta ( hat düşey ):  kutu ve eğik çizgi."""
    g, d = 5.0, 18.0
    ad = "otomatik_sigorta"
    return [
        _kutu(CIHAZ, x - g / 2, y - d / 2, g, d, ad),
        _cizgi(CIHAZ, x - 4.0, y - 6.0, x + 4.0, y + 6.0, ad),
    ]


#  Sembol listesi:  ( çizen , ad ) — çizimde kullanılanlar
def _semboller():
    return (
        (lambda x, y: otomatik_sigorta(x, y), "Otomatik sigorta"),
        (lambda x, y: otomatik_sigorta(x, y, kutup=4), "Grup sigorta  ( 3F+N )"),
        (kacak_akim_rolesi, "Kaçak akım rölesi  ( K.A.R )"),
        (pako_salter, "Pako şalter"),
        (kesici_salter, "Kesici şalter  ( ana şalter )"),
        (lambda x, y: etanj_armatur(x - 5.0, y), "Etanj armatür"),
        (led_spot, "Armatür  ( LED spot )"),
        (lambda x, y: anahtar(x - 1.5, y - 1.5), "Vavien anahtar"),
        (stop_butonu, "Stop butonu"),
        (buton, "Buton"),
        (lambda x, y: priz(x - 1.0, y), "Topraklı priz"),
        (buat, "Buat"),
        (lambda x, y: topraklama(x, y + 2.5), "Topraklama"),
        (lambda x, y: topraklama_barasi(x - 6.0, y - 0.8), "Topraklama barası"),
    )


def sembol_listesi():
    e = [_yazi(8.0, 96.0, "SEMBOL LİSTESİ", H)]
    liste = _semboller()
    satir = (len(liste) + 1) // 2
    for i, (ciz_, ad) in enumerate(liste):
        sutun, sira = divmod(i, satir)
        sx = 18.0 + sutun * 92.0
        y = 86.0 - sira * 9.0
        e += ciz_(sx, y)
        e.append(_yazi(sx + 12.0, y, ad, N))
    return e


# ══════════════════════════════════════════════════════════════════════
#  SAYFA
# ══════════════════════════════════════════════════════════════════════
def ciz(v, sag_yazi=""):
    """Elektrik projesinin sayfası:  sol alt köşe ( 0 , 0 ), A3 yatay, 1/20
    biriminde.  v:  hesabın elektrik verisi ( avan_hesabi._elektrik_projesi );
    sag_yazi:  künye şeridinin sağı ( asansörün adı )."""
    e = [_kutu("CERCEVE", 0.0, 0.0, EN, BOY), _cizgi("CERCEVE", 0.0, SERIT, EN, SERIT)]
    e.append(_yazi(6.0, SERIT / 2.0, BASLIK, B, kat="CERCEVE"))
    yazi = "  ·  ".join(x for x in (v.get("tablo"), sag_yazi) if x)
    if yazi:
        e.append(_yazi(EN - 6.0, SERIT / 2.0, yazi, H, "sag", kat="CERCEVE"))
    e += tek_hat(v)
    e += kuyu_tesisati(v)
    e += topraklama_tesisati(v)
    e += ana_tablo(v)
    e += sembol_listesi()
    return e


#  Paftada sayfanın kapladığı A4 hücresi ( yan yana ) ve çizim birimi ( 1/20 )
HUCRE = 2
OLCEK = 20


def pafta_sayfalari(veriler):
    """Paftaya girecek elektrik projeleri, asansörlerin sırasıyla:  [ ( ad,
    başlık, ölçek, elemanlar ) ] — pafta.bloklar gibi ( DXF'te blok
    "CIZIM_" + ad, PDF'te aynı liste ).  veriler:  [ ( hesabın elektrik
    verisi , asansörün adı ) ];  verisi olmayan ( hesabı yapılamamış )
    asansör atlanır."""
    dolu = [(v, adi) for v, adi in veriler if v]
    return [
        (f"elektrik_{i}" if len(dolu) > 1 else "elektrik", BASLIK, OLCEK, ciz(v, adi))
        for i, (v, adi) in enumerate(dolu, 1)
    ]


def paftaya_yerlestir(d, sayfalar, yerler):
    """Elektrik projelerini ( pafta_sayfalari ) paftaya blok olarak koyar:  her
    biri yerler'deki sol alt köşeye ( pafta mm ), 1/ölçek ile — çizimlerin
    blokları gibi ( pafta._yerlestir;  PDF şeridi bloğu adından bulur )."""
    dxf.hazirla(d)
    msp = d.modelspace()
    for (ad, _baslik, olcek, e), (x, y) in zip(sayfalar, yerler):
        blok = d.blocks.new(name=pafta.blok_adi(ad), base_point=(0.0, 0.0))
        dxf.ciz(blok, e, olcek, blokta=True)
        msp.add_blockref(
            blok.name, (x, y), dxfattribs={"xscale": 1.0 / olcek, "yscale": 1.0 / olcek, "layer": "0"}
        )
