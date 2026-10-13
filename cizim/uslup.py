# -*- coding: utf-8 -*-
"""
ÜSLUP — çizimlerin GÖRÜNÜŞÜ tek yerde:  kalem kalınlığı, çizgi tipi, renk,
tarama, yazı boyu, ölçü ucu.

Ekran ( svg.py ) ve AutoCAD ( dxf.py ) bu tablodan okur;  ikisi ayrı ayrı
tutulurken ayrışmışlardı ( 12 Eki ölçüldü:  33 katmanın 22'sinde kalınlık
farklı — delik ekranda 0,18, DXF'te 0,30;  ölçü ucu ekranda dik çizgi,
AutoCAD'de eğik tik;  duvar taraması ekranda 6 mm, AutoCAD'de 3,2 mm aralıklı,
tuğla taraması AutoCAD'de çelik deseni ( ANSI32 ) ).

Bütün boylar KÂĞITTA milimetredir;  çizim gerçek ölçüde ( mm ) kurulduğu
için çizici ölçekle çarpar ( 1/20'de 1 mm kâğıt = 20 mm çizim ).
"""

import os
from typing import NamedTuple

#  YAZI TİPİ DOSYALARI ( OFL — hesap/static/yazi/OFL.txt;  değiştirilmeden ):
#  ekran ve PDF gömer, DXF aynı enlerdeki Arial / Times'ı adıyla ister.
YAZI_KLASORU = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hesap", "static", "yazi"
)
YAZI_DOSYASI = os.path.join(YAZI_KLASORU, "LiberationSans-Regular.ttf")  # Arial'in enleri
SERIF_DOSYASI = os.path.join(YAZI_KLASORU, "LiberationSerif-Regular.ttf")  # Times'ın enleri

#  ── KALEM ( ISO 128-2:  0,13 · 0,18 · 0,25 · 0,35 · 0,5 · 0,7 — her adım √2 ) ──
#      0,50  kesilen duvar, kesit işareti, çerçeve
#      0,35  görünen ana kenar ( kabin, kapı, ray, ağırlık, şase, makine … )
#      0,25  ikincil parça ( konsol, paten, pano, merdiven, kabin içi … )
#      0,18  ince parça ( cıvata, delik, halat ), gizli çizgi
#      0,13  ölçü, eksen, tarama, seviye, alan sınırı
#  ( 6 Eki — kullanıcı:  çizimler "oyuncak gibi" duruyordu;  bu sıra o gün
#  ekranda kuruldu, DXF eski değerlerinde kalmıştı. )
KALEMLER = (0.13, 0.18, 0.25, 0.35, 0.50, 0.70)


#  ── ÇİZGİ TİPLERİ ( AutoCAD'in ISO tipleri — acadiso.lin;  LiftDesigner de
#  bunları kullanır ) ──  desen W100 tanımıdır ( 1 mm kalem için:  çizgi,
#  −boşluk, 0 = nokta );  "olcek" kâğıttaki desen çarpanı.  Ekran aynı deseni
#  çizer ( nokta ekranda 0,25 mm'lik çizgi — SVG'de boyu 0 olan çizgi görünmez ).
class Desen(NamedTuple):
    dxf: str
    tanim: tuple
    olcek: float


SUREKLI = None
DESENLER = {
    #  eksen:  ISO çizgi – nokta;  kâğıtta 6 · 1,5 · nokta · 1,5
    "EKSEN": Desen("ACAD_ISO10W100", (12.0, -3.0, 0.0, -3.0), 0.5),
    #  gizli kenar:  ISO kesik;  kâğıtta 3 · 0,75
    "GIZLI": Desen("ACAD_ISO02W100", (12.0, -3.0), 0.25),
    #  alan sınırı ( sığınma — parça değil, alan ):  seyrek kesik;  3 · 4,5
    "ALAN": Desen("ACAD_ISO03W100", (12.0, -18.0), 0.25),
}
NOKTA = 0.25  # ekranda noktanın boyu ( mm )


class Kalem(NamedTuple):
    kalinlik: float  # kâğıtta mm ( KALEMLER'den )
    desen: str | None  # DESENLER'in anahtarı;  None sürekli
    ekran: str  # ekrandaki renk
    aci: int  # AutoCAD rengi ( ACI;  koyu zemin için — ölçü camgöbeği 5 Eki )


SIYAH = "#111111"
MAVI = "#0b4a8f"  # ölçü ( ekranda ayırt edilsin )
KIRMIZI = "#a51d1d"  # eksen

KATMAN = {
    "KUYU-DUVAR": Kalem(0.50, None, SIYAH, 7),
    "KESIT": Kalem(0.50, None, SIYAH, 7),
    "CERCEVE": Kalem(0.50, None, SIYAH, 7),
    "KUYU-IC": Kalem(0.35, None, SIYAH, 7),
    "KABIN": Kalem(0.35, None, SIYAH, 7),
    "KAPI": Kalem(0.35, None, SIYAH, 30),
    "AGIRLIK": Kalem(0.35, None, SIYAH, 30),
    "RAY": Kalem(0.35, None, SIYAH, 3),
    "SASE": Kalem(0.35, None, SIYAH, 6),
    "MAKINE": Kalem(0.35, None, SIYAH, 5),
    "KASNAK": Kalem(0.35, None, SIYAH, 90),
    "TAMPON": Kalem(0.35, None, SIYAH, 200),
    "PERDE": Kalem(0.35, None, SIYAH, 6),
    "KORKULUK": Kalem(0.35, None, SIYAH, 6),
    "KABIN-IC": Kalem(0.25, None, SIYAH, 6),
    "KONSOL": Kalem(0.25, None, SIYAH, 3),
    "PATEN": Kalem(0.25, None, SIYAH, 200),
    "PANO": Kalem(0.25, None, SIYAH, 150),
    "BAGLANTI": Kalem(0.25, None, SIYAH, 8),
    "MERDIVEN": Kalem(0.25, None, SIYAH, 32),
    "BINA": Kalem(0.25, None, SIYAH, 33),
    "YUK": Kalem(0.25, None, SIYAH, 1),
    "CIVATA": Kalem(0.18, None, SIYAH, 3),
    "DELIK": Kalem(0.18, "GIZLI", SIYAH, 5),
    "HALAT": Kalem(0.18, None, SIYAH, 6),
    "GIZLI": Kalem(0.18, "GIZLI", SIYAH, 8),
    #  menteşeli kapının açılma yayı ve açık konumu ( ISO 128:  ince sürekli )
    "ACILIS": Kalem(0.18, None, SIYAH, 30),
    "OLCU": Kalem(0.13, None, MAVI, 4),
    "EKSEN": Kalem(0.13, "EKSEN", KIRMIZI, 1),
    "TARAMA": Kalem(0.13, None, SIYAH, 8),
    "SEVIYE": Kalem(0.13, None, SIYAH, 2),
    "SIGINMA": Kalem(0.13, "ALAN", SIYAH, 3),
    "YAZI": Kalem(0.13, None, SIYAH, 7),
}
#  Parçanın "ince" ayrıntısı ( sac profil kıvrımı, oluk ) katmanından bağımsız
INCE = 0.18


#  ── TARAMA ( kesilen duvar ) ──  aralık kâğıtta mm.  AutoCAD desenleri:
#  ANSI31 45° tek çizgi ( temel aralığı 3,175 ), BRICK tuğla ( sıra 6,35 ·
#  derz 12,7 ).  Ekran aynı aralığı çizer.
class Tarama(NamedTuple):
    dxf: str
    temel: float  # desenin kendi sıra aralığı ( çizim birimi )
    aralik: float  # kâğıtta istenen sıra aralığı ( mm )


TARAMALAR = {
    "tarama": Tarama("ANSI31", 3.175, 3.0),
    "tarama_tugla": Tarama("BRICK", 6.35, 3.0),
}


def tarama_olcegi(tur, olcek):
    """AutoCAD desen ölçeği:  gerçek ölçüde ( mm ) çizilen tarama 1/ölçek
    küçültülünce sıra aralığı kâğıtta TARAMALAR'daki olsun."""
    t = TARAMALAR[tur]
    return t.aralik * olcek / t.temel


#  ── YAZI ( ISO 3098:  büyük harf yüksekliği 2,5 · 3,5 · 5 mm ) ──  Çizim
#  yazının boyunu em ( font-size ) olarak taşır;  Arial'de büyük harf =
#  0,716 em ( 1467 / 2048 ).  Değerler 1/20'de em:  70 → 70 · 0,716 / 20 =
#  2,5 mm.  Başka ölçekte çizim k = ölçek / 20 ile çarpar.  ( 12 Eki:  13 ayrı
#  boy vardı — 1,45 … 4,34 mm;  üçü ISO'nun en küçüğü 1,8'in altında. )
BUYUK_HARF = 0.716
NORMAL = 70.0  # ölçü yazısı, etiket, not — 2,5 mm
HARF = 98.0  # kesit / görünüş harfi, durak numarası — 3,5 mm
BASLIK = 140.0  # çizimin başlığı — 5 mm
YAZI_SINIFLARI = (NORMAL, HARF, BASLIK)


#  YAZI MASKESİ:  etiketin arkasındaki örtü yazının kutusundan her yanda
#  ( MASKE_PAYI − 1 ) / 2 · yazı boyu taşar ( DXF:  MTEXT arka planı — AutoCAD
#  "Border offset factor";  PDF:  dikdörtgen ).  Ölçü yazısınınki OLCU_BOSLUGU
#  ( DXF dimgap ).  Yerleşim yazıyı maskesiyle denetler ( geometri ):  maske
#  bir parçanın kenarına değerse kâğıtta kenar kopuk çıkar ( 13 Eki:  delik
#  planında "66 x 66" duvar çizgisini kesiyordu — kutusu duvara değmiyordu ).
MASKE_PAYI = 1.25


def maske_payi(h):
    """Etiket maskesinin yazının kutusundan taşması ( h:  yazı boyu, em )."""
    return (MASKE_PAYI - 1.0) / 2.0 * h


def kagitta(em, olcek):
    """em yüksekliğinin kâğıttaki büyük harf boyu ( mm )."""
    return em * BUYUK_HARF / olcek


#  ── ÖLÇÜ ( ISO 129-1 ) ──  Uç:  45° EĞİK ÇİZGİ ( yapı çizimlerinin ucu ) ve
#  ölçü çizgisini dik kesen KISA UZATMA ÇİZGİSİ ( LiftDesigner gibi ).  Uzun
#  uzatma çizgileri planı boydan boya kesiyordu;  kısa ve sabit boylu olanı
#  kullanıcı seçti ( 12 Eki ).  Eskiden ekranda yalnız dik çizgi, AutoCAD'de
#  ezdxf'in stilinden kalın eğik tik vardı.
TIK = 1.0  # eğik çizginin iki eksendeki yarı boyu ( mm )
SAPLAMA = 1.5  # kısa uzatma çizgisinin ölçü çizgisinin iki yanındaki boyu ( mm )
TIK_KALEM = 0.25
OLCU_BOSLUGU = 0.75  # yazının maskesi yazıdan bu kadar taşar ( mm )
