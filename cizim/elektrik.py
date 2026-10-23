# -*- coding: utf-8 -*-
"""
ELEKTRİK PROJESİ — asansörün tek hat şeması ( TAS ), kuyu tesisatı, topraklama
tesisatı, ana tablo yerleşimi ve sembol listesi;  paftada kapağın yanında, alt
satırın solunda ( kullanıcı isteği 23 Eki — ofisin elle hazırladığı projenin
düzeni:  referans 4815-6 AVAN paftası ).

DEĞERLER HESAPTAN ( motor/avan/avan_hesabi._elektrik_projesi ):  kuyu ve kabin
armatürlerinin adedi ve gücü ( kuyuya hesabın bulduğu kadar armatür çizilir ),
motor gücü ve sigortası, devre sigortaları ( kurulu güç cetveli ), kolon hattı
( kesit / koruma iletkeni / kablo tipi ), makine besleme hattının koruma
iletkeni, kaçak akım rölesinin IΔn'ı ( topraklama hesabının ofis standardı ).
Çizim kendisi hesaplamaz;  hesabın vermediği değer ( kontrol panosunun içi,
şalterlerin anma akımı, son devrelerin kabloları ) yazılmaz — referans
paftadaki "17-22A", "5x32A" gibi sayılar başka bir motorun değerleriydi.

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
#  TEK HAT ŞEMASI ( TAS )
# ══════════════════════════════════════════════════════════════════════
#  Bara ve devreler ( kâğıt mm )
_BARA_X = 60.0
_MOTOR_Y, _KABIN_Y, _PRIZ_Y, _KUYU_Y = 280.0, 268.0, 257.0, 246.0
_BESLEME_Y = 262.0
_FAZ_X, _PE_X = 16.0, 26.0
_SIGORTA_X = 71.0
_TOPRAK_BARASI_Y = 233.0
_MOTOR_PE_X = 194.0  # motorun koruma iletkeni devre yazılarının sağından iner
_PANO_X = 118.0  # kontrol panosunun ortası
#  Sigortanın anma akımı sigortanın üstünde:  yazının maskesi ( PDF'te alt uzantılı
#  harflerle 2,4 mm ) sigortanın eğik çizgisinin ucunu örtmesin
_AMPER_YUKSEKLIGI = 5.6


def _devre_metni(ad, adet, w):
    return f"{ad}  ( {adet}x{_sayi(w)} W )"


def tek_hat(v):
    """TAS:  besleme ( sayaç → kolon hattı → kaçak akım rölesi → pako şalter ),
    bara, motor devresi ( grup sigorta → kesici şalter → kontrol panosu → motor ),
    aydınlatma ve priz devreleri, topraklama barası.  Devrelerin hatları sağa,
    kuyu tesisatına uzar ( kuyu_tesisati )."""
    e = []
    bx = _BARA_X
    # ── bara
    e.append(
        _cokgen(
            CIHAZ,
            [(bx - 1.2, 242), (bx + 1.2, 242), (bx + 1.2, 285), (bx - 1.2, 285)],
            dolu=True,
            ad="tablo_barasi",
        )
    )
    e.append(_yazi(bx - 3.5, 274.0, v["tablo"], H, "sag"))
    # ── besleme:  sayaç ( altta ) → kolon hattı → kaçak akım rölesi → pako şalter → bara
    y0 = _BESLEME_Y
    fx = _FAZ_X
    e += sayac(fx, 141.0)
    e.append(_cizgi(HAT, fx, 136.0, fx, 128.0))
    e += [_yazi(fx, 124.5, "Şebeke", N, "orta"), _yazi(fx, 120.0, "( 3F+N )", N, "orta")]
    e.append(_cizgi(HAT, fx, 146.0, fx, 172.0))
    e += kirik(fx, 175.0)
    e += kirik(_PE_X, 175.0)
    e.append(_cizgi(HAT, fx, 178.0, fx, y0))
    e.append(_cizgi(HAT, fx, y0, 25.0, y0))
    e += kacak_akim_rolesi(29.5, y0)
    e.append(_cizgi(HAT, 34.0, y0, 39.0, y0))
    e += pako_salter(42.0, y0)
    e.append(_cizgi(HAT, 45.0, y0, bx - 1.2, y0))
    kar = f"IΔn {_sayi(v['kacak_akim_A'] * 1000)} mA" if v.get("kacak_akim_A") else ""
    e.append(_yazi(29.5, y0 + 10.5, "K.A.R", N, "orta"))
    if kar:
        e.append(_yazi(29.5, y0 + 6.5, kar, N, "orta"))
    e.append(_yazi(42.0, y0 - 5.0, "Pako", N, "orta"))
    e.append(_yazi(42.0, y0 - 9.0, "şalter", N, "orta"))
    # kolon hattının kablosu
    k = v["kolon"]
    kablo = f"4x{_sayi(k['S'])}" + (f"/{_sayi(k['SPE'])}" if k.get("SPE") else "") + f" {k['kablo']}".rstrip()
    e.append(_cizgi(HAT, fx - 1.4, 199.0, fx + 1.4, 201.6))
    e.append(_yazi(fx + 13.0, 205.0, "Kolon hattı", N))
    e.append(_yazi(fx + 13.0, 200.3, kablo, N))
    # ── koruma iletkeni:  temel topraklaması → topraklama barası
    px = _PE_X
    e += topraklama(px, 118.0)
    e.append(_yazi(px + 5.0, 113.5, "TEMEL TOPRAKLAMASINA BAĞLANACAK", N))
    e.append(_cizgi(TOPRAK, px, 118.0, px, 172.0))
    e.append(_cizgi(TOPRAK, px, 178.0, px, _TOPRAK_BARASI_Y + 0.8))
    e.append(_cizgi(TOPRAK, px, _TOPRAK_BARASI_Y + 0.8, bx - 6.0, _TOPRAK_BARASI_Y + 0.8))
    e += topraklama_barasi(bx - 6.0, _TOPRAK_BARASI_Y, 14.0)
    e.append(_yazi(bx + 1.0, _TOPRAK_BARASI_Y - 3.6, "Topraklama barası", N, "orta"))
    if k.get("SPE"):
        e.append(_yazi(px + 2.6, 148.0, f"PE {_sayi(k['SPE'])} mm² Cu", N, "orta", aci=90))
    # ── motor devresi
    e += _motor_devresi(v, bx)
    # ── aydınlatma ve priz devreleri
    kb, ku, pr, kuyu = v["kabin"], v["kabin_ustu"], v["priz"], v["kuyu"]
    devreler = (
        (
            _KABIN_Y,
            kb["sigorta_A"],
            f"Kabin + kabin üstü aydınlatması  ( {kb['adet']}x{_sayi(kb['W'])} W + {ku['adet']}x{_sayi(ku['W'])} W )",
        ),
        (_PRIZ_Y, pr["sigorta_A"], _devre_metni("Priz", pr["adet"], pr["W"])),
        (_KUYU_Y, kuyu["sigorta_A"], _devre_metni("Kuyu aydınlatması", kuyu["adet"], kuyu["W"])),
    )
    for y, amper, metin in devreler:
        e.append(_cizgi(HAT, bx + 1.2, y, _SIGORTA_X - 4.0, y))
        e += otomatik_sigorta(_SIGORTA_X, y)
        e.append(_yazi(_SIGORTA_X, y + _AMPER_YUKSEKLIGI, f"{amper} A", N, "orta"))
        e.append(_yazi(_SIGORTA_X + 9.0, y - 2.6, metin, N))
    return e


def _motor_devresi(v, bx):
    """Bara → grup sigorta → kesici şalter → kontrol panosu → motor;  motorun
    koruma iletkeni topraklama barasına."""
    e = []
    y = _MOTOR_Y
    e.append(_cizgi(HAT, bx + 1.2, y, _SIGORTA_X - 4.0, y))
    e += otomatik_sigorta(_SIGORTA_X, y, kutup=4)
    a = v.get("motor_sigorta_A")
    e.append(_yazi(_SIGORTA_X, y + _AMPER_YUKSEKLIGI, f"4x{a}A" if a else "3F+N", N, "orta"))
    e.append(_cizgi(HAT, _SIGORTA_X + 4.0, y, 82.5, y))
    e += kesici_salter(88.0, y)
    e.append(_yazi(88.0, y + 6.5, "Kesici şalter", N, "orta"))
    e.append(_cizgi(HAT, 93.5, y, 100.0, y))
    #  Kontrol panosu:  içi imalatçının ( faz sırası rölesi, motor koruması, kumanda )
    e.append(_kutu(CIHAZ, 100.0, 271.5, 36.0, 16.0, "kontrol_panosu"))
    e.append(_yazi(_PANO_X, 282.0, "KONTROL PANOSU", N, "orta"))
    e.append(_yazi(_PANO_X, 276.0, "Sıralı faz rölesi", N, "orta"))
    e.append(_cizgi(HAT, 136.0, y, 142.0, y))
    mx = 148.0
    e += motor(mx, y)
    e.append(_yazi(mx + 8.5, y + 2.6, "ASANSÖR MOTORU", N))
    e.append(_yazi(mx + 8.5, y - 2.6, f"{_sayi(v['motor_kW'])} kW", N))
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
    e.append(_cizgi(HAT, _SIGORTA_X + 4.0, _KUYU_Y, ix, _KUYU_Y))
    kotlar, kirik_y = armatur_kotlari(kuyu["adet"])
    alt = min(kotlar + [_KY0 + 10.0])
    if kirik_y is None:
        e.append(_cizgi(HAT, ix, _KUYU_Y, ix, alt))
    else:
        e.append(_cizgi(HAT, ix, _KUYU_Y, ix, kirik_y + 3.0))
        e += kirik(ix, kirik_y)
        e.append(_cizgi(HAT, ix, kirik_y - 3.0, ix, alt))
        e.append(_yazi(ix + 12.0, kirik_y, f"( toplam {kuyu['adet']} adet )", N))
    metin = f"U-1x{_sayi(kuyu['W'])} W"
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
    e.append(_cizgi(HAT, _SIGORTA_X + 4.0, _KABIN_Y, sx, _KABIN_Y))
    e.append(_cizgi(HAT, _SIGORTA_X + 4.0, _PRIZ_Y, sx, _PRIZ_Y))
    e.append(_nokta(sx, _PRIZ_Y))
    e += [_cizgi(HAT, _PANO_X, 287.5, _PANO_X, 291.0), _cizgi(HAT, _PANO_X, 291.0, sx, 291.0)]
    e.append(_cizgi(HAT, sx, 291.0, sx, _KY0 + 10.0))
    e.append(_nokta(sx, _KABIN_Y))
    e.append(_yazi(sx - 2.0, 288.0, "Kumanda", N, "sag"))
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
    e.append(_yazi(sx - 11.5, ys, "Kuyu dibi stop", N, "sag"))
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
    """Asansör tablosunun yerleşimi:  ana besleme → kaçak akım rölesi → pako
    şalter → bara;  dörtlü otomatik sigorta ( kesici şalter, kontrol panosu ve
    motor ) ve devre sigortaları ( TAS ile aynı değerler )."""
    e = []
    x0 = _SAG_SUTUN
    e.append(_yazi(x0, 157.0, "ANA TABLO YERLEŞİMİ", H))
    hx = x0 + 16.0  # besleme hattı

    def kutu(x, y, g, d, satirlar, ad):
        """Kutu ve ortasında satırlar ( maske altta 2,4, üstte 1,7 mm taşar:  0,34 yukarı )."""
        e.append(_kutu(CIHAZ, x, y, g, d, ad))
        for i, s in enumerate(satirlar):
            e.append(
                _yazi(x + g / 2.0, y + d / 2.0 + 0.34 + ((len(satirlar) - 1) / 2.0 - i) * 5.2, s, N, "orta")
            )

    kar = f"IΔn {_sayi(v['kacak_akim_A'] * 1000)} mA" if v.get("kacak_akim_A") else "IΔn"
    kutu(x0 + 2.0, 82.0, 28.0, 16.0, ("Kaçak akım", "rölesi", kar), "kacak_akim_rolesi")
    kutu(x0 + 2.0, 112.0, 28.0, 14.0, ("3F+N", "Pako şalter"), "pako_salter")
    a = v.get("motor_sigorta_A")
    ox = x0 + 90.0
    kutu(
        ox,
        106.0,
        26.0,
        24.0,
        ("3F+N Dörtlü", "otomatik", "sigorta") + ((f"4x{a}A",) if a else ()),
        "grup_sigorta",
    )
    # besleme:  kolon hattı → kaçak akım rölesi → pako şalter → bara
    e.append(_cizgi(HAT, hx, 46.0, hx, 82.0))
    e.append(_cizgi(HAT, hx, 98.0, hx, 112.0))
    e.append(_cizgi(HAT, hx, 126.0, hx, 144.0))
    e.append(_cizgi(HAT, hx, 144.0, ox + 13.0, 144.0))
    e.append(_cizgi(HAT, ox + 13.0, 144.0, ox + 13.0, 130.0))
    e += [
        _yazi(hx, 41.0, "3F+N", N, "orta"),
        _yazi(hx, 36.0, "Ana besleme", N, "orta"),
        _yazi(hx, 31.0, "( kolon hattı )", N, "orta"),
    ]
    # kesici şalter, kontrol panosu ve motor
    e.append(_cizgi(HAT, ox + 13.0, 106.0, ox + 13.0, 62.0))
    e += [
        _yazi(ox + 13.0, 57.0, "Kesici şalter,", N, "orta"),
        _yazi(ox + 13.0, 52.0, "kontrol panosu", N, "orta"),
        _yazi(ox + 13.0, 47.0, "ve motor devresine", N, "orta"),
    ]
    # devre sigortaları ( dikey )
    devreler = [
        ("Kabin ve kabin üstü aydınlatması", v["kabin"]["sigorta_A"]),
        ("Kuyu aydınlatması", v["kuyu"]["sigorta_A"]),
        ("Priz", v["priz"]["sigorta_A"]),
    ]
    if v.get("makine_dairesi"):
        devreler.insert(2, ("Makine dairesi aydınlatması", None))
    adim = 13.0 if len(devreler) <= 3 else 10.5
    for i, (ad, amper) in enumerate(devreler):
        x = x0 + 42.0 + i * adim
        e.append(_cizgi(HAT, x, 144.0, x, 130.0))
        e.append(_nokta(x, 144.0))
        e += _dikey_sigorta(x, 121.0)
        if amper:
            e.append(_yazi(x + 2.4, 134.0, f"{amper} A", N))
        e.append(_cizgi(HAT, x, 112.0, x, 108.0))
        e.append(_yazi(x, 106.0, ad, N, "sag", aci=90))
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
        (kesici_salter, "Kesici şalter"),
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
