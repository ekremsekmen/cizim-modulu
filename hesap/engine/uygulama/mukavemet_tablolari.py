# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ  —  MUKAVEMET HESABI TABLOLARI

Tablolar ofisin mukavemet hesabından makine ile aktarıldı ( elle
yazılmadı ) ve standarda göre tamamlandı;  testler/test_mukavemet_tablolari.py
aktarılan değerleri dondurulmuş kaynağa ( testler/referans_tablolar.json )
karşı birebir doğrular.

AVAN MODÜLÜNDEN AYRIDIR.  Avan tarafı MMO/697'yi uygular ( engine/tables.py );
burası uygulama projesinin kendi kaynağını uygular.  İki tarafın ortak konuları
( ör. kabin alanı ) BİLEREK ayrı tutulur — dayanakları farklıdır ve paftalarda
kaynakları da ayrı yazılır.
"""


def _sayi(x):
    """Sayı mı  ( bool tuzağı dâhil )."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _ara(tablo, anahtar, sutun=1):
    """Birebir anahtar eşleşmesi;  yoksa None."""
    for satir in tablo:
        if satir[0] == anahtar:
            return satir[sutun]
    return None


# =====================================================================
#  KILAVUZ RAY PROFİLLERİ  ( ISO 7465 )
#  Hesabın EN ÇOK okuduğu tablo — 49 atıf.
#      Gr kg/m · A mm² · Ix mm⁴ · Iy mm⁴ · Wx mm³ · Wy mm³ · ix mm · iy mm
#      c mm ( flanş ) · e mm
# =====================================================================
#
#  T75/B EKLENDİ  ( 2026-09-11 ).  Orta kapasiteli asansörlerin en yaygın
#  rayıdır ve listede yoktu:  T75/B ile çizilmiş bir proje programla HİÇ
#  hesaplanamıyordu.  Değerlerin kaynağı satır satır:
#      Gr · A · Ix · Iy · Wx · Wy   ISO 7465 T75 kesit verisi.  İKİ BAĞIMSIZ
#                                   kaynak aynı sayıları veriyor:  referans projenin
#                                   örnek paftası ( 8,56 kg/m · 10,91 cm² ·
#                                   40,29 · 26,47 cm⁴ · 9,29 · 7,06 cm³ ) ve
#                                   ISO 7465 tablosu.
#      ix · iy                      √( I / A ).  Bu türetme mevcut altı
#                                   satırın hepsinde tabloyu yeniden üretir
#                                   ( yalnız 125x82x16'nın iy'si ayrışır —
#                                   ayrı bir konu ) ;  iy = 15,58 mm,
#                                   referans projenin paftasındaki 1,56 cm ile aynı.
#      c                            ISO 7465:2011 B-grubu ölçü tablosu.
#      e                            h1 − Ix/Wx.  Altı satırın hepsinde
#                                   tabloyu birebir yeniden üretir;  zaten
#                                   hesapta HİÇ okunmuyor.
#
#  ISO 8100-33:2022'YE GÖRE GÜNCELLENDİ  ( 2026-10-06, kullanıcı onayıyla ):
#      70 x 65 x 9      eski katalog değerleri ( "T70-1/A":  A 951 · Ix 41,30 ·
#                       Iy 18,65 cm⁴ … ) yerine ISO 8100-33 Tablo 5 = ISO
#                       7465:2007 Tablo 4, T70/A:  9,400 cm² · 7,379 kg/m ·
#                       e 2,034 · Ix 40,95 · Wx 9,169 · ix 2,087 · Iy 18,86 ·
#                       Wy 5,389 · iy 1,417.  Fark ~%1, iki yönde.
#      89 x 62 x 15,88  c 9,5 → 10:  ISO'nun T89/A ( Tablo 6 ) ve T89/B ( B
#                       grubu ölçü tablosu ) boyun kalınlığı.  Eski değer σF'yi
#                       %11 büyük veriyordu ( emniyetli yön ).
#      90 x 75 x 16     ISO 8100-33 Tablo 5, T90/A:  17,25 cm² · 13,54 kg/m ·
#                       e 2,612 · Ix 102,00 · Wx 20,86 · ix 2,431 · Iy 52,48 ·
#                       Wy 11,66 · iy 1,744.  Eski Iy / Wy ( 53,0 / 11,80 )
#                       ~%1 büyüktü — emniyetsiz yön.
#  İŞLENMİŞ ( /B ) RAYLARIN KESİT DEĞERLERİ ( ISO 8100-33 Tablo 7 ) ELİMİZDE
#  DEĞİL:  bu iki satır soğuk çekilmiş ( /A ) kesitin değerleridir;  T75'te
#  referans projenin /B paftası /A'nın değerlerini kullanır.  Bir Türk ray
#  üreticisinin TS EN 81-20 belgesi de T70 A ve T90 A için aynı sayıları verir.
RAY_PROFILI = (
    ('50 x 50 x 5', 3.7, 475, 112400, 52500, 3150, 2100, 15.38, 10.51, 5, 14.3),
    ('70 x 65 x 9', 7.379, 940, 409500, 188600, 9169, 5389, 20.87, 14.17, 6, 20.34),
    ('75 x 62 x 10', 8.564, 1091, 402900, 264700, 9290, 7060, 19.22, 15.58, 8, 18.63),
    ('89 x 62 x 15,88', 12.38, 1577, 598300, 524100, 14350, 11780, 19.48, 18.23, 10, 20.32),
    ('90 x 75 x 16', 13.54, 1725, 1020000, 524800, 20860, 11660, 24.31, 17.44, 10, 26.12),
    ('125 x 82 x 16', 18, 2290, 1511000, 1566000, 26200, 25100, 25.7, 25.2, 10, 24.3),
    ('127 x 89 x 16', 22.48, 2863, 1984000, 2300000, 30900, 36200, 26.3, 28.3, 10, 24.7),
)

RAY_PROFILLERI = tuple(s[0] for s in RAY_PROFILI)
_RAY_SUTUN = {"Gr": 1, "A": 2, "Ix": 3, "Iy": 4, "Wx": 5, "Wy": 6,
              "ix": 7, "iy": 8, "c": 9, "e": 10}


def ray(profil, ozellik):
    """Ray profilinin bir özelliği.  ozellik: Gr/A/Ix/Iy/Wx/Wy/ix/iy/c/e"""
    return _ara(RAY_PROFILI, profil, _RAY_SUTUN[ozellik])


# =====================================================================
#  RAY PROFİLİ — FLANŞ GEOMETRİSİ
#      f mm · b mm · h1 mm · (h1−b−f) mm · (h1−f) mm
# =====================================================================
#
#  T75/B:  f = 9 ve h1 = 62 ISO 7465:2011 B-grubu ölçü tablosundandır.
#  b PATEN BALATASININ YARI GENİŞLİĞİDİR — ISO'nun ray ölçüsü değil, paten
#  tedarikçisinin değeridir ve T75/B için kaynaklayamadım.  ISO'nun n ölçüsünün
#  yarısı alındı ( n = 30 → 15 ) ;  bu kural T89 ( 34 → 17 ) , T90 ( 42 → 21 )
#  ve T125 ( 42 → 21 ) satırlarında tutuyor, T127'de tutmuyor.  Etkisi
#  SINIRLIDIR:  b yalnız kaymalı patenin flanş gerilmesine ve balata boyunun
#  TÜRETİLEN varsayılanına girer;  balata boyu zaten bir girdidir ve
#  girildiğinde türetme devre dışı kalır.  Küçük b, ( h1 − b − f )'yi
#  büyüttüğü için EMNİYETLİ yöndedir.
#
#  50 x 50 x 5 ( T50/A ) DÜZELTİLDİ  ( 2026-10-06, kullanıcı onayıyla ):  kaynak
#  f = 8 yazıyordu.  T50/A PARALEL TABANLIDIR — taban her yerde aynı kalınlıkta,
#  p = 5 mm ( ISO 7465:2007 Tablo 3 = ISO 8100-33:2022 Tablo 4 ).  Kesitin
#  kendisi doğruluyor:  50 × 5 + 45 × 5 = 475 mm² = ISO'nun S'si ve
#  RAY_PROFILI'nin A'sı;  f = 8 ile alan 610 mm² olurdu.  ( h1 − b − f ) ve
#  ( h1 − f ) de buna göre:  31,5 ve 45.  Eski değer kaymalı patenin σF'sini
#  küçük gösteriyordu ( emniyetsiz yön;  ℓ = 2b'de %4,9 ).
RAY_GEOMETRI = (
    ('50 x 50 x 5', 5, 13.5, 50, 31.5, 45),
    ('70 x 65 x 9', 8, 17, 65, 40, 57),
    ('75 x 62 x 10', 9, 15, 62, 38, 53),
    ('89 x 62 x 15,88', 11.1, 17, 62, 33.9, 50.9),
    ('90 x 75 x 16', 10, 21, 75, 44, 65),
    ('125 x 82 x 16', 12, 21, 82, 49, 70),
    ('127 x 89 x 16', 15.9, 25.5, 89, 47.6, 73.1),
)

_RAY_GEO_SUTUN = {"f": 1, "b": 2, "h1": 3, "h1_b_f": 4, "h1_f": 5}


def ray_geo(profil, ozellik):
    return _ara(RAY_GEOMETRI, profil, _RAY_GEO_SUTUN[ozellik])


# =====================================================================
#  ASKI HALATLARI  ( TS 12385-5 )
#      çap mm · 1 m ağırlık kg · en küçük kopma yükü N · tip · sınıf
# =====================================================================
HALAT = (
    (6, 0.129, 23100, '6x19 Lif Özlü', 1770),
    (6.5, 0.152, 24700, '6x19 Lif Özlü', 1770),
    (7, 0.1795, 27400, '6x19 Lif Özlü', 1770),
    (8, 0.23, 31700, '6x19 Lif Özlü', '1370/1770'),
    (9, 0.291, 40100, '6x19 Lif Özlü', '1370/1770'),
    (10, 0.34, 49500, '6x19 Lif Özlü', '1370/1770'),
    (11, 0.411, 53200, '8x19 Lif Özlü', '1370/1770'),
    (12, 0.49, 63300, '8x19 Lif Özlü', '1370/1770'),
    (13, 0.575, 74300, '8x19 Lif Özlü', '1370/1770'),
    (14, 0.666, 86100, '8x19 Lif Özlü', '1370/1770'),
    (15, 0.765, 98900, '8x19 Lif Özlü', '1370/1770'),
    (16, 0.87, 113000, '8x19 Lif Özlü', '1370/1770'),
)

HALAT_CAPLARI = tuple(s[0] for s in HALAT)


def halat_agirlik(cap):
    """Halatın 1 m'sinin ağırlığı, kg."""
    return _ara(HALAT, cap, 1)


def halat_kopma(cap):
    """Halatın en küçük kopma yükü Tmin, N."""
    return _ara(HALAT, cap, 2)


def halat_tipi(cap):
    return _ara(HALAT, cap, 3)


# =====================================================================
#  BURKULMA KATSAYISI  ω   ( λ = 20 … 250 )
# =====================================================================
OMEGA_LAMBDA_MIN, OMEGA_LAMBDA_MAX = 20, 250


# ---------------------------------------------------------------------
#  ω  —  TS EN 81-50 m.5.10.3  ( burkulma, "omega" yöntemi )
# ---------------------------------------------------------------------
#  ω YALNIZ narinliğe değil, RAY ÇELİĞİNİN ÇEKME DAYANIMINA da bağlıdır.
#  Standart iki eğri verir ( Rm = 370 ve Rm = 520 ) ve aradaki dayanımlar
#  için doğrusal ara değer ister:
#
#      ω(λ) = ω370(λ) + ( ω520(λ) − ω370(λ) ) · ( Rm − 370 ) / ( 520 − 370 )
#
#  Standardın kendi notu:  işlenmiş raylarda 440 N/mm² yaygın olduğu için
#  bu ara değerleme "her zaman yapılmalıdır".
#
#  Tek bir Rm = 370 tablosunu ray çeliğinden bağımsız kullanmak 440 ve 520
#  için ω'yı %23 ve %50 DÜŞÜK verir, yani burkulma gerilmesini olduğundan
#  küçük gösterir.
OMEGA_370 = ((60, 0.00012920, 1.89, 1.0),
             (85, 0.00004627, 2.14, 1.0),
             (115, 0.00001711, 2.35, 1.04),
             (250, 0.00016887, 2.00, 0.0))
OMEGA_520 = ((50, 0.00008240, 2.06, 1.021),
             (70, 0.00001895, 2.41, 1.05),
             (89, 0.00002447, 2.36, 1.03),
             (250, 0.00025330, 2.00, 0.0))
OMEGA_RM_ALT, OMEGA_RM_UST = 370, 520


def _omega_egri(egri, lam):
    for ust, kat, us, ek in egri:
        if lam <= ust:
            return kat * lam ** us + ek
    return None


def omega_en8150(lam, rm=OMEGA_RM_ALT):
    """ω  ( TS EN 81-50 m.5.10.3 )  —  narinlik ve ray çeliğine göre."""
    if not (_sayi(lam) and _sayi(rm)):
        return None
    if not (OMEGA_LAMBDA_MIN <= lam <= OMEGA_LAMBDA_MAX):
        return None
    a = _omega_egri(OMEGA_370, lam)
    if rm <= OMEGA_RM_ALT:
        return a
    b = _omega_egri(OMEGA_520, lam)
    if rm >= OMEGA_RM_UST:
        return b
    return a + (b - a) * (rm - OMEGA_RM_ALT) / (OMEGA_RM_UST - OMEGA_RM_ALT)


# =====================================================================
#  NPU / NPI PROFİLLERİ  ( makine kaidesi kirişleri )
#      A cm² · G kg/m · Ix cm⁴ · Wx cm³ · ix cm · Iy cm⁴ · Wy cm³ · iy cm
#  ix / iy atalet YARIÇAPIDIR ( λ = L1 / imin'de öyle kullanılır ).
#
#  ÜÇ DEĞER KAYNAKTAN DÜZELTİLDİ  ( DIN 1026-1 · UPN ) :
#      30x15  Ix  2,21 → 2,53 cm⁴   kaynak A'yı ( 2,21 ) Ix sütununa da
#                                   yazmış;  satırın kendi ix'i ( 1,07 )
#                                   ancak √( 2,53 / 2,21 ) ile tutar.
#      280    A  47,5 → 53,3 cm²    kaynağın kendi G'si ( 41,8 kg/m ) çelik
#      300    A  50   → 58,8 cm²    yoğunluğuyla A = G / 0,785 verir.
#  Üçü de şu an hesaba girmez ( 30x15'in Ix'i hiç okunmaz;  280 · 300'ün ix'i
#  boş olduğundan dikine kiriş seçimi reddedilir ) — ama Tablolar sekmesinde
#  görünürler ve yanlış görünmemelidirler.
# =====================================================================
NPU_PROFIL = (
    ('30x15', 2.21, 1.74, 2.53, 1.69, 1.07, 0.38, 0.39, 0.42),
    (30, 5.44, 4.27, 6.39, 4.26, 1.08, 5.33, 2.68, 0.99),
    ('40x20', 3.66, 2.87, 7.58, 3.79, 1.44, 1.14, 0.86, 0.56),
    (40, 6.21, 4.87, 14.1, 7.05, 1.5, 6.68, 3.08, 1.04),
    ('50x25', 4.92, 3.86, 16.8, 6.73, 1.85, 2.49, 1.48, 0.71),
    (50, 7.12, 5.59, 26.4, 10.6, 1.92, 9.12, 3.75, 1.13),
    (60, 6.46, 5.07, 31.6, 10.5, 2.21, 4.51, 2.16, 0.84),
    (65, 9.03, 7.09, 57.5, 17.7, 2.52, 14.1, 5.07, 1.25),
    (80, 11, 8.64, 106, 26.5, 3.1, 19.4, 6.36, 1.33),
    (100, 13.5, 10.6, 206, 41.2, 3.91, 29.3, 8.49, 1.47),
    (120, 17, 13.4, 364, 60.7, 4.62, 43.2, 11.1, 1.59),
    (140, 20.4, 16, 605, 86.4, 5.45, 62.7, 14.8, 1.75),
    (160, 24, 18.8, 925, 116, 6.21, 85.3, 18.3, 1.89),
    (180, 28, 22, 1350, 150, 6.95, 114, 22.4, 2.02),
    (200, 32.2, 25.3, 1910, 191, 7.7, 148, 27, 2.14),
    (240, 42.3, 33.2, 3600, 300, None, 248, 39.6, None),
    (280, 53.3, 41.8, 6280, 448, None, 399, 57.2, None),
    (300, 58.8, 46.2, 8030, 535, None, 495, 67.8, None),
)

NPU_OLCULERI = tuple(r[0] for r in NPU_PROFIL)

_NPU_SUTUN = {"A": 1, "G": 2, "Ix": 3, "Wx": 4, "ix": 5,
              "Iy": 6, "Wy": 7, "iy": 8}


def npu(olcu, ozellik):
    """NPU/NPI profil özelliği.  olcu sayı ( 120 ) ya da metin ( '30x15' )."""
    return _ara(NPU_PROFIL, olcu, _NPU_SUTUN[ozellik])


# =====================================================================
#  KABİN ALANI  ( beyan yükü → kişi · en büyük · en küçük alan )
#
#  DİKKAT:  Avan modülünün MMO/697 Tablo-11'i ile ortak satırları AYNIDIR;
#  ama iki tablo bilerek ayrı tutulur — biri MMO/697'yi, diğeri EN 81-20
#  Çizelge 6'yı uygular.
# =====================================================================
#  EN 81-20 Çizelge 6'nın 28 beyan yükünün tamamı;  ofisin eski listesinde
#  olmayan satırlar ★ ile işaretlidir ( 1250 ve 1500 kg yaygın asansörlerdir ).
#
#  Sütunlar:  beyan yükü · kişi · azami alan ( Çiz.6 ) · asgari alan ( Çiz.8 )
#  Kişi sayısı m.5.4.2.3.1 a):  Q/75, aşağı yuvarlanır.
#  Çizelge 8'de 20 kişiden sonrası:  3,13 + 0,115 × ( kişi − 20 ).
KABIN_ALANI = (
    (100, 1, 0.37, 0.28),          # ★ Çiz.6 — tek kişilik asansör asgarisi
    (180, 2, 0.58, 0.49),
    (225, 3, 0.7, 0.6),
    (300, 4, 0.9, 0.79),
    (320, 4, 0.953, 0.79),   # Çiz.6'da YOK — 300/375 arası doğrusal ara değer
    (375, 5, 1.1, 0.98),
    (400, 5, 1.17, 0.98),
    (450, 6, 1.3, 1.17),
    (525, 7, 1.45, 1.31),
    (600, 8, 1.6, 1.45),
    (630, 8, 1.66, 1.45),
    (675, 9, 1.75, 1.59),
    (750, 10, 1.9, 1.73),
    (800, 10, 2, 1.73),
    (825, 11, 2.05, 1.87),
    (900, 12, 2.2, 2.01),
    (975, 13, 2.35, 2.15),
    (1000, 13, 2.4, 2.15),
    (1050, 14, 2.5, 2.29),      # ★
    (1125, 15, 2.65, 2.43),
    (1200, 16, 2.8, 2.57),
    (1250, 16, 2.9, 2.57),      # ★
    (1275, 17, 2.95, 2.71),
    (1350, 18, 3.1, 2.85),      # ★
    (1425, 19, 3.25, 2.99),     # ★
    (1500, 20, 3.4, 3.13),      # ★
    (1600, 21, 3.56, 3.245),
    (2000, 26, 4.2, 3.82),
    (2500, 33, 5.0, 4.625),     # ★  Çiz.6'nın son satırı
)



#  ---------------------------------------------------------------------
#  RAY TABLOSUNUN KENDİ TUTARLILIĞI
#  ---------------------------------------------------------------------
#  Atalet yarıçapı tanımı gereği  i = √( I / A )  olmalıdır;  ama bir satırda
#  tablonun değerleri tutmuyor ( 70 x 65 x 9'daki %0,3'lük fark ISO 8100-33'ün
#  değerleriyle kalktı — 6 Eki 2026 ):
#
#      125 x 82 x 16    iy  25,20   √(Iy/A) = 26,15   %3,6
#
#  125'lik satırda A, Ix ve ix birbiriyle tutarlıdır ( √(1511000/2290) =
#  25,69 ≈ 25,7 );  tutmayan TEK sayı iy'dir.  Hangisinin doğru olduğu ISO
#  7465'in kendi tablosundan teyit edilmelidir — elimizde o yok.
#
#  DEĞER DEĞİŞTİRİLMEDİ:  tabloda duran küçük iy, narinliği ( λ = l/i ) BÜYÜK
#  gösterir, dolayısıyla ω ve burkulma gerilmesi de büyük çıkar — yani
#  emniyetli taraftadır.  Doğrulanmamış bir sayıyı emniyetsiz yönde
#  değiştirmek yerine tutarsızlık burada AÇIKÇA işaretlenir.
RAY_TUTARSIZ = ("125 x 82 x 16",)


def ray_tutarsizliklari(tolerans=0.005):
    """i ≠ √(I/A) olan satırlar  →  [ ( profil, eksen, tablo, hesap ) ]."""
    import math as _m
    bulunan = []
    for satir in RAY_PROFILI:
        ad = satir[0]
        A = ray(ad, "A")
        for eksen, atalet in (("ix", "Ix"), ("iy", "Iy")):
            tablo = ray(ad, eksen)
            hesap = _m.sqrt(ray(ad, atalet) / A)
            if abs(tablo - hesap) > tolerans * hesap:
                bulunan.append((ad, eksen, tablo, round(hesap, 3)))
    return bulunan


#  ---------------------------------------------------------------------
#  ASANSÖR TİPİ  →  kapı eşiği kuvvetinin katsayısı   ( EN 81-20 m.5.7.2.3.6 )
#      Fs = 0,4 · gn · Q   insan asansörü
#      Fs = 0,6 · gn · Q   yük-insan asansörü
#  ( Taşıma aracının ağırlığı beyan yüküne katılmayan ağır taşıma araçlı
#    yük-insan asansörü için madde 0,85 verir;  o tip bu programın kapsamı
#    dışında bırakıldı. )
#  ---------------------------------------------------------------------
ASANSOR_TIPLERI = ("İnsan asansörü", "Yük-insan asansörü")
ESIK_KUVVETI_KATSAYISI = {"İnsan asansörü": 0.4, "Yük-insan asansörü": 0.6}


def esik_katsayisi(tip):
    """m.5.7.2.3.6 katsayısı;  tanınmayan / boş tip insan asansörü sayılır."""
    return ESIK_KUVVETI_KATSAYISI.get(tip, ESIK_KUVVETI_KATSAYISI[ASANSOR_TIPLERI[0]])


#  ---------------------------------------------------------------------
#  EN 81-20 ÇİZELGE 8  —  yolcu sayısı → kullanılabilir EN KÜÇÜK alan  ( m² )
#  20 kişiden sonra her kişi için + 0,115 m².
#  m.5.4.2.3.1:  yolcu sayısı "Q / 75 ( aşağı yuvarlanır ) ile Çizelge 8'in
#  KÜÇÜĞÜDÜR".  Çizelge 8 bir ret ölçütü değildir:  alanı küçük bir kabin
#  uygunsuz olmaz, üzerine daha az kişi yazılır.
#  ---------------------------------------------------------------------
CIZELGE_8 = (0.28, 0.49, 0.60, 0.79, 0.98, 1.17, 1.31, 1.45, 1.59, 1.73,
             1.87, 2.01, 2.15, 2.29, 2.43, 2.57, 2.71, 2.85, 2.99, 3.13)
CIZELGE_8_KISI_BASI = 0.115


def cizelge8_alan(kisi):
    """Çizelge 8:  bu kadar yolcu için kullanılabilir en küçük alan  ( m² )."""
    if kisi is None or kisi < 1:
        return None
    kisi = int(kisi)
    if kisi <= len(CIZELGE_8):
        return CIZELGE_8[kisi - 1]
    return CIZELGE_8[-1] + CIZELGE_8_KISI_BASI * (kisi - len(CIZELGE_8))


def cizelge8_kisi(alan):
    """Çizelge 8'in tersi:  bu alanın taşıyabileceği EN ÇOK yolcu  ( 0 olabilir )."""
    import math as _m
    if alan is None:
        return None
    if alan + 1e-9 >= CIZELGE_8[-1]:
        return len(CIZELGE_8) + int(_m.floor((alan - CIZELGE_8[-1]) / CIZELGE_8_KISI_BASI
                                              + 1e-9))
    return sum(1 for a in CIZELGE_8 if a <= alan + 1e-9)


def kabin_kisi(beyan_yuku):
    return _ara(KABIN_ALANI, beyan_yuku, 1)


def kabin_azami_alan(beyan_yuku):
    """Kullanılabilir EN BÜYÜK kabin alanı, m²."""
    return _ara(KABIN_ALANI, beyan_yuku, 2)


def kabin_asgari_alan(beyan_yuku):
    """Kullanılabilir EN KÜÇÜK kabin alanı, m²."""
    return _ara(KABIN_ALANI, beyan_yuku, 3)


# =====================================================================
#  TAHRİK KASNAĞI KANAL ŞEKLİ
# =====================================================================
#  KANAL AÇISI ARTIK TABLODA DEĞİL, OFİS SABİTİDİR.
#
#  Kanal şeklinin karşısına TEK bir açı ve TEK bir Nequiv(t) yazan bir
#  tablo ( V → 38° / 12 ,  altı kesik → 90° / 5 ) iki ayrı büyüklüğü
#  karıştırır:  V kanalda γ ( kanal açısı ), altı kesik kanalda β ( alt
#  kesilme açısı ).  Üstelik ofis sabitlerinden γ = 45° seçilse bile 38 ve
#  12 kalır — pafta hesabın kullandığı sayıyı yazmaz.
#
#  TS EN 81-50 m.5.12.2.2 Çizelge 2 Nequiv(t)'yi doğrudan bu açıların
#  fonksiyonu verir ve "çizelgede olmayan açılar için doğrusal ara değer"
#  ister.  Tablo artık şeklin YALNIZ TÜRÜNÜ tutar;  açılar ofis
#  sabitlerinden gelir ve Nequiv(t) onlardan hesaplanır.
#
#     tür    anlamı                             f bağıntısı ( m.5.11.2.3.1 )
#     'V'    V kanal, alt kesilmesiz            m.5.11.2.3.1.2   ( β = 0 )
#     'VK'   V kanal, altı kesik                m.5.11.2.3.1.2   ( β )
#     'U'    yarım daire, alt kesilmesiz        m.5.11.2.3.1.1   ( β = 0 )
#     'UK'   yarım daire, altı kesik            m.5.11.2.3.1.1   ( β )
#
#  ( ad , tür , tahrik kasnağı üzerinden geçiş sayısı )
KANAL_SEKLI = (
    ('V Kanal',                       'V',  1),
    ('Altı Kesik V Kanal',            'VK', 1),
    ('Yarım Daire Kanal',             'U',  1),
    ('Altı Kesik Yarım Daire Kanal',  'UK', 1),
    #  Çift sarımda halat tahrik kasnağının üzerinden İKİ kez geçer;  her
    #  geçiş bir basit eğilmedir, bu yüzden Nequiv(t) iki katıdır.
    ('Yarım Daire Kanal (Çift Sarım)', 'U', 2),
)

KANAL_SEKILLERI = tuple(s[0] for s in KANAL_SEKLI)


def kanal_turu(sekil):
    """Kanalın türü:  'V' · 'VK' · 'U' · 'UK'  ( bilinmeyen şekilde None )."""
    return _ara(KANAL_SEKLI, sekil, 1)


def kanal_gecis_sayisi(sekil):
    """Halatın tahrik kasnağı üzerinden geçiş sayısı  ( çift sarımda 2 )."""
    return _ara(KANAL_SEKLI, sekil, 2)


# ---------------------------------------------------------------------
#  TS EN 81-50 m.5.12.2.2  Çizelge 2  —  Nequiv(t)
# ---------------------------------------------------------------------
#      V kanal          γ  35°   36°   38°   40°   42°   45°   50°
#                  Nequiv(t) 18,5   16    12    10     8   6,5     5
#      Altı kesik U     β  75°   80°   85°   90°   95°  100°  105°
#                  Nequiv(t)  2,5   3,0   3,8   5,0   6,7  10,0  15,2
#      Alt kesilmesiz U         Nequiv(t) = 1
#  "Values for angles not in the table may be determined by linear
#   interpolation."  —  çizelgenin kendi notu.
NEQUIV_V = ((35, 18.5), (36, 16.0), (38, 12.0), (40, 10.0),
            (42, 8.0), (45, 6.5), (50, 5.0))
NEQUIV_U_ALTI_KESIK = ((75, 2.5), (80, 3.0), (85, 3.8), (90, 5.0),
                       (95, 6.7), (100, 10.0), (105, 15.2))

#  m.5.11.2.3.1.1 / m.5.11.2.3.1.2'nin kendi sınırları
BETA_AZAMI = 105.0        # "shall not exceed 105° (1,83 rad)"
GAMA_ASGARI_U = 25.0      # yarım daire:  "in no case … less than 25°"
GAMA_ASGARI_V = 35.0      # V kanal:  "in no case, angle γ shall be less than 35°"
GAMA_AZAMI = 90.0         # γ bir kanal açısıdır;  90°'yi aşamaz

#  m.5.6.2.2.1.3 b):  regülatör halatının emniyet katsayısı hesaplanırken
#  "taking into account a friction factor µmax equal to 0,2".  Sayıyı
#  standart verir;  ofis daha KÜÇÜK bir değer yazarsa katsayı olduğundan
#  iyi çıkar — üst sınır bu yüzden burada durur.
REG_MU_AZAMI = 0.2


def _dogrusal_ara(tablo, x):
    """Çizelge 2 için doğrusal ara değer;  aralık dışında uç değere sabitler."""
    if not _sayi(x):
        return None
    if x <= tablo[0][0]:
        return tablo[0][1]
    if x >= tablo[-1][0]:
        return tablo[-1][1]
    for (x0, y0), (x1, y1) in zip(tablo, tablo[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def kanal_acisi(sekil, gama_v=None, gama_yd=None):
    """Hesapta KULLANILAN γ  ( kanal açısı ).  Alt kesilme açısı β değildir.

    Altı kesik kanallarda β'yı γ diye basmak paftada "γ = 90°" yazıp hesapta
    38° kullanmak olurdu.
    """
    tur = kanal_turu(sekil)
    if tur is None:
        return None
    return gama_yd if tur in ("U", "UK") else gama_v


def kanal_beta(sekil, beta=None):
    """Alt kesilme açısı β.  Alt kesilmesi olmayan kanalda 0'dır."""
    return beta if kanal_alti_kesik_mi(sekil) else 0.0


#  ---------------------------------------------------------------------
#  KANAL ŞEKLİNİN SÜRTÜNME BAĞINTISI
#  ---------------------------------------------------------------------
#  TS EN 81-50 sürtünme çarpanı f için İKİ AYRI madde verir:
#
#    m.5.11.2.3.1.1  YARIM DAİRE ( ve altı kesik yarım daire ) kanal
#        f = μ · 4( cos(γ/2) − sin(β/2) ) / ( π − β − γ − sin β + sin γ )
#        γ imalatçıdan gelir, hiçbir durumda 25°'den küçük olamaz.
#
#    m.5.11.2.3.1.2  V KANAL
#        sertleştirilmemiş, yükleme / acil frenleme :
#            f = μ · 4( 1 − sin(β/2) ) / ( π − β − sin β )        ( γ girmez )
#        sertleştirilmiş                            :  f = μ / sin(γ/2)
#        ağırlık bloke ( ikisinde de )              :  f = μ / sin(γ/2)
#        γ asansörlerde 35°'den küçük olamaz.
#
#  Kanal şeklinden bağımsız hep V kanal bağıntısı kullanılamaz:  yarım
#  dairenin kendi maddesi vardır.
KANAL_YARIM_DAIRE = tuple(a for a, t, _g in KANAL_SEKLI if t in ("U", "UK"))
#  Altı kesik olanlar:  β = alt kesilme açısı;  ötekilerde β = 0.
KANAL_ALTI_KESIK = tuple(a for a, t, _g in KANAL_SEKLI if t in ("VK", "UK"))


def kanal_yarim_daire_mi(sekil):
    return sekil in KANAL_YARIM_DAIRE


def kanal_alti_kesik_mi(sekil):
    return sekil in KANAL_ALTI_KESIK


def kanal_nequiv_t(sekil, gama_v=None, beta=None):
    """Kasnakların eşdeğer sayısı Nequiv(t)  ( TS EN 81-50 Çizelge 2 ).

    Kanalın ADINA bağlı sabit bir değer değildir:  Çizelge 2 Nequiv(t)'yi
    doğrudan γ ve β'nın fonksiyonu verir;  ofis sabiti değişince o da değişir.
    """
    tur = kanal_turu(sekil)
    if tur is None:
        return None
    gecis = kanal_gecis_sayisi(sekil) or 1
    if tur in ("V", "VK"):
        #  ÇİZELGE 2'NİN İKİ SATIRI VARDIR:  "V-grooves" ( V açısı γ ile ) ve
        #  "U-Undercut grooves" ( alt kesme açısı β ile ).  ALTI KESİK V DE
        #  BİR V KANALDIR:  m.5.11.2.3.1.1 "yarım daire ve altı kesik yarım
        #  daire" kanalları, m.5.11.2.3.1.2 ise "V kanallar"ı ele alır ve
        #  altı kesik V açıkça ikincisinin içindedir ( "sertleştirilmemişse
        #  alt kesme gereklidir" ).  m.5.12.2'nin girişi de kanalları "U- ya
        #  da V-" diye ikiye ayırır.  Altı kesik V'yi β satırından okumak
        #  γ = 38° için 12 yerine β = 90° için 5,0 verir — Nequiv küçük,
        #  gereken güvenlik katsayısı da küçük çıkar ( emniyetsiz ).
        taban = _dogrusal_ara(NEQUIV_V, gama_v)
    elif tur == "UK":
        taban = _dogrusal_ara(NEQUIV_U_ALTI_KESIK, beta)
    else:                                   # 'U' — alt kesilmesiz yarım daire
        taban = 1.0
    return None if taban is None else taban * gecis


# =====================================================================
#  DARBE KATSAYISI  k1   ( TS EN 81-20 Çizelge 14 )
#  Bu tablo GÜVENLİK TERTİBATI TİPİNE bakar.  Avan modülü aynı çizelgeyi
#  HIZA göre okur ( MMO/697 Çizelge-1 iki sütunu yan yana verir ).  Normal
#  kurulumda ikisi aynı değeri üretir;  düşük hızlı bir asansöre kademeli
#  tertibat konursa ayrışırlar — o durumda tertibat tipi daha doğrudur.
# =====================================================================
DARBE_TIPLERI = (
    ('Kaymalı', 2),
    ('Ani Frenlemeli Makaralı', 3),
    ('Ani Frenlemeli', 5),
)



DARBE_TIPLERI_ADLARI = tuple(r[0] for r in DARBE_TIPLERI)


def darbe_k1(tertibat_tipi):
    return _ara(DARBE_TIPLERI, tertibat_tipi, 1)


#  Normal kullanma hareketi  ( TS EN 81-20 Çizelge 14 · MMO/697 Çizelge-1 )
K2_NORMAL_KULLANMA = 1.2


# =====================================================================
#  BÜKÜLGEN ( GEZİCİ ) KABLO
# =====================================================================
#  Kabin ile kuyu arasındaki asma kablo.  MTrav ( gezici kablo indirgenmiş
#  kütlesi ) hesabına girer.
#      tip · genişlik mm · kalınlık mm · ağırlık kg/m   ( yassı kablo )
#  Hesaba yalnız ağırlık girer.
BUKULGEN_KABLO = (
    ('12 x 0,75', 33.8, 4.2, 0.284),
    ('24 x 0,75', 70.4, 4.2, 0.642),
    ('12 x 1,00', 36.2, 4.2, 0.33),
    ('24 x 1,00', 70.4, 4.2, 0.62),
)

KABLO_TIPLERI = tuple(r[0] for r in BUKULGEN_KABLO)
_KABLO_SUTUN = {"genislik": 1, "kalinlik": 2, "agirlik": 3}


# =====================================================================
#  KAT KAPISI TİPİ  →  2. BÜKÜLGEN KABLO
# =====================================================================
#  2. kablo tipi GİRDİ DEĞİLDİR:  kat kapısı tipinden türetilir ( manuel
#  kapıda daha ince kablo ).  3 kanatlı teleskopik ve 4 kanatlı merkezi
#  ( büyük kapılar — çizimin kanat cebi, kullanıcı kararı 2 Eki ) otomatik
#  kapıdır:  öbür otomatik kapılar gibi 24'lü.  "Teleskopik Sol / Sağ" ve
#  "Otomatik Merkezi" 2 kanatlıdır ( kayıtlı projeler bu adları taşır ).
KAPI_KABLO = (
    ('Manuel Sağ', '12 x 0,75'),
    ('Manuel Sol', '12 x 0,75'),
    ('Otomatik Merkezi', '24 x 0,75'),
    ('Otomatik Merkezi 4 Kanat', '24 x 0,75'),
    ('Teleskopik Sağ', '24 x 0,75'),
    ('Teleskopik Sol', '24 x 0,75'),
    ('Teleskopik 3 Kanat Sağ', '24 x 0,75'),
    ('Teleskopik 3 Kanat Sol', '24 x 0,75'),
)

KAPI_TIPLERI = tuple(r[0] for r in KAPI_KABLO)


def kapi_kablosu(kapi_tipi):
    """Kat kapısı tipine karşılık gelen 2. bükülgen kablo tipi."""
    return _ara(KAPI_KABLO, kapi_tipi, 1)


def kablo_agirligi(tip):
    """Bükülgen kablonun metre ağırlığı ( kg/m )."""
    return _ara(BUKULGEN_KABLO, tip, _KABLO_SUTUN["agirlik"])


def kablo_en(tip):
    return _ara(BUKULGEN_KABLO, tip, 1)


def kablo_yukseklik(tip):
    return _ara(BUKULGEN_KABLO, tip, 2)


# =====================================================================
#  KARŞI AĞIRLIK MALZEMESİ  ( derinlik · yükseklik mm )
# =====================================================================
#  KARŞI AĞIRLIK MALZEMESİ  ( Barit 155 · Pik döküm 100 mm derinlik ).
#  Derinlik GİRDİDİR ( bkz. aşağıdaki "KALDIRILDI" notu ):  ölçü
#  malzemenin değil, imal edilen çerçevenin özelliğidir ve TS EN 81-50
#  Ek C.2.2 onu veri olarak ister.  Sayı sütunları BAŞLANGIÇ DEĞERİ olarak
#  kaldı — form açılırken derinliğe barit çerçevenin alışılmış ölçüsü gelir;
#  hesap yalnız girilen değeri okur.  BARİT:  standart blok 960 × 155 × 120 mm,
#  50 kg ( Tiraslift · Egeser katalogları;  kullanıcı kararı 30 Eyl — karar 11:
#  dolgunun sığma denetimi bu bloğun yoğunluğuyla, derinliği bloğunki ).
AGIRLIK_MALZEMESI = (
    ('Barit', 155, 120),
    ('Pik Döküm', 100, 100),
)

AGIRLIK_MALZEMELERI = tuple(r[0] for r in AGIRLIK_MALZEMESI)
_MALZEME_SUTUN = {"derinlik": 1, "yukseklik": 2}


#  KARŞI AĞIRLIĞIN GENİŞLİĞİ DE GİRDİDİR.  Ray arasından türetilemez:  TS EN
#  81-50 Ek C.2.2 ölçüleri veri olarak ister ( ray hesabı kılavuzu:  "Gx =
#  130 mm, Gy = 960 mm Counterweight dimensions", XG = %10 × Gx, YG = %5 ×
#  Gy ) ve referans proje de karşı ağırlığın Dx · Dy'sini doğrudan sorar.  Program
#  kabin tarafında da böyle yapar ( kabin_genisligi · kabin_derinligi ).

# =====================================================================
#  KILAVUZ RAY ÇELİĞİ  Rm → izin verilen gerilmeler
#      σperm normal kullanma · σperm güvenlik tertibatı çalışması  ( N/mm² )
# =====================================================================
#  STANDARDIN BAĞINTISI:  σperm = Rm / St  ( EN 81-20 m.5.7.4.5 ).
#  St Çizelge 15'ten, A5 > %12 çelik için:  normal işletme ve yükleme 2,25 ·
#  güvenlik tertibatı çalışması 1,8.  Tam sayıya yuvarlanmış bir tablo
#  ( 165 · 205 · … ) Rm 370'te normal işletmede 164,44 yerine 165 alır —
#  EMNİYETSİZ yönde %0,3.  Tablo bağıntının kendisidir.
RAY_EMNIYET_NORMAL = 2.25
RAY_EMNIYET_GUVENLIK = 1.8
#  SEÇENEKLER:  ISO 7465:2007 m.5 ray çeliğinin çekme dayanımını "en az 370,
#  en çok 520 N/mm²" diye sınırlar ve işlenmiş raylar için E 275 B çeliğini
#  önerir.  Aradaki her Rm için ω EN 81-50 m.5.10.3'ün doğrusal ara
#  değeriyle bulunur ( omega_en8150 ), σperm de bu bağıntıdan — yeni bir
#  seçenek için ayrı tablo gerekmez.  450:  referans projenin örnek projesindeki
#  işlenmiş ray değeri.
RAY_CELIGI = tuple((rm, rm / RAY_EMNIYET_NORMAL, rm / RAY_EMNIYET_GUVENLIK)
                   for rm in (370, 440, 450, 520))

RAY_CELIKLERI = tuple(s[0] for s in RAY_CELIGI)


def sigma_perm_normal(rm):
    return _ara(RAY_CELIGI, rm, 1)


def sigma_perm_guvenlik(rm):
    return _ara(RAY_CELIGI, rm, 2)


# =====================================================================
#  KANAL İŞLEME ŞEKLİ
# =====================================================================
#  Sürtünme çarpanı f tabloda DEĞİLDİR:  kanal şekline ve ofis açılarına
#  bağlıdır, motor onu her seferinde m.5.11.2.3.1'den hesaplar
#  ( mukavemet._tahrik ).  Ekrandaki tablo da ofis sabitlerinden üretilir
#  ( engine/uygulama/tablolar_gorunum.py ).
KANAL_ISLEME_SEKILLERI = ("Sertleştirilmemiş", "Sertleştirilmiş")


# =====================================================================
#  TAMPON TİPLERİ            TS EN 81-20 m.5.8.1 / m.5.8.2
# =====================================================================
#  Standart tamponları ÜÇE ayırır ve her birine BAŞKA kural bağlar:
#
#    lineer  ( yaylı )          m.5.8.2.1.1  strok ≥ 0,135·v² , en az 65 mm
#    lineer olmayan             m.5.8.2.1.2  strok formülü YOK — tip deneyiyle
#      ( poliüretan )                        doğrulanır ( yavaşlama ölçütleri )
#    enerji yutmalı             m.5.8.2.2.1  strok ≥ 0,0674·v²
#      ( hidrolik )
#
#  Ayrıca m.5.8.1.5:  enerji biriktirmeli tamponlar ( lineer VE lineer
#  olmayan ) YALNIZ v ≤ 1 m/s'de kullanılabilir;  enerji yutmalıda hız
#  sınırı yoktur ( m.5.8.1.6 ).
#
#      ad · enerji biriktirmeli mi · strok katsayısı ( None = tip deneyi )
#  AD KISA TUTULUR:  pafta değer sütunu 40 mm'dir, uzun ad üç satıra
#  bölünüyordu.  Tipin standarttaki tam karşılığı bölümün KAYNAK sütununda
#  ( m.5.8.2.1.1 · m.5.8.2.1.2 · m.5.8.2.2 ) zaten yazılı.
TAMPON_TIPLERI = (
    ("Yaylı  ( lineer )", True, 0.135),
    ("Poliüretan  ( lineer olmayan )", True, None),
    ("Hidrolik  ( enerji yutmalı )", False, 0.0674),
)
TAMPON_TIPLERI_ADLARI = tuple(t[0] for t in TAMPON_TIPLERI)
#  m.5.8.2.1.1.1'in alt sınırı:  hesap ne verirse versin 65 mm'nin altına
#  inilemez.  m.5.8.2.2.1'de böyle bir alt sınır yoktur.
TAMPON_ASGARI_STROK = 65.0
#  m.5.8.1.5:  enerji biriktirmeli tamponun kullanılabildiği en yüksek hız
TAMPON_BIRIKTIRMELI_AZAMI_HIZ = 1.0
#  m.5.8.2.1.2.2:  "tam ezilmiş" = kurulu tampon yüksekliğinin %90'ı
TAMPON_TAM_EZILME_ORANI = 0.90


def tampon(ad):
    """Tampon tipi satırı  ->  ( ad , biriktirmeli_mi , strok_katsayisi )."""
    for t in TAMPON_TIPLERI:
        if t[0] == ad:
            return t
    return TAMPON_TIPLERI[1]        # tanınmayan ad: poliüretan sayılır


# =====================================================================
#  SIĞINMA HACMİ TİPLERİ   ( TS EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 )
# =====================================================================
#  Standart, kabin üstünde ve kuyu dibinde bir sığınma hacmi ARAR ama TİPİNİ
#  tasarımcıya bırakır:  aşağıdaki duruşlardan BİRİ sağlanmalıdır.  Kuyu
#  dibinde üç, kabin üstünde iki seçenek vardır — YATARAK duruş yalnız kuyu
#  dibi içindir.
#
#      duruş        yatay a × b      yükseklik c
#      dik           0,40 × 0,50        2,00 m
#      çömelme       0,50 × 0,70        1,00 m
#      yatarak       0,70 × 1,00        0,50 m      ( yalnız kuyu dibi )
#
#  NİÇİN SEÇİM:  program bu tabloyu bilmiyor, ÇÖMELME tipini koda çivilemişti
#  ( eski SIGINMA["dip_hacim"] = (0,50 · 0,70 · 1,00) ).  Kuyu dibinde 0,88 m
#  serbest yüksekliği olan bir tesis çömelmeyi geçmez ama YATARAK tipini
#  rahatça geçer;  program buna bakmadığı için "UYGUN DEĞİL" diyor ve
#  projeciyi kuyu dibini derinleştirmeye ya da tamponu revize etmeye
#  yönlendiriyordu — çoğu zaman gereksiz, mevcut binada çoğu zaman imkânsız.
#
#  Seçilen tip PAFTAYA YAZILIR:  hangi duruşun beyan edildiği belgelenmeli ve
#  standardın istediği biçimde kuyu dibinde işaretlenmelidir.
SIGINMA_HACMI = (
    #  ad,         a (m),  b (m),  c (m) — yükseklik
    ("Dik duruş",   0.40,   0.50,   2.00),
    ("Çömelme",     0.50,   0.70,   1.00),
    ("Yatarak",     0.70,   1.00,   0.50),
)

#  Kabin üstünde YATARAK duruş yoktur  ( m.5.2.5.7.1 ).
SIGINMA_TIPLERI_UST = ("Dik duruş", "Çömelme")
SIGINMA_TIPLERI_DIP = ("Dik duruş", "Çömelme", "Yatarak")


def siginma_hacmi(tip, konum="dip"):
    """Sığınma hacmi ölçüleri  ( a , b , c )  —  metre.

    konum "dip" ise ( a , b ) = ( kısa , uzun ) ,  "ust" ise ( uzun , kısa ).
    Bu SIRALAMA standardın bir kuralı değildir;  kabin üstü ve kuyu dibi
    kontrollerinde dikdörtgenin hangi eksene oturtulduğunu belirler
    ( bkz. mukavemet._siginma ).
    Tanınmayan tip için None döner.
    """
    for ad, a, b, c in SIGINMA_HACMI:
        if ad == tip:
            return (b, a, c) if konum == "ust" else (a, b, c)
    return None


# =====================================================================
#  MAKİNE YÜKÜNÜN YOLU   ( TS EN 81-20 m.5.7.2.3.7 · m.5.2.1.8.1 )
# =====================================================================
#  Standart makinenin NEREYE oturabileceğine dair kapalı bir liste vermez:
#  m.5.2.1.8.1 "yapı taşıyacak, ayrıntısı ulusal yapı yönetmeliğinde" der.
#  Mukavemet hesabını değiştiren TEK ayrım, yükün asansörün KENDİ parçasına
#  ( kılavuz raya ) değip değmediğidir:
#
#    · raylara      →  m.5.7.2.3.7 ek yük durumları ister, Maux hesaba girer
#    · bina yapısına →  kapsam DIŞI;  m.5.2.1.8.1 ve Ek E uyarınca inşaat
#                       projesine BİLDİRİLİR  ( sayı paftada verilir )
#
#  Kuyu üstü kiriş · duvar · konsol ayrımı hesabı değiştirmez — üçü de
#  "bina yapısına"dır.  Kirişin UÇLARI raylara cıvatalıysa yük yine raya
#  iner ve "raylara" seçilir.
MAKINE_YUK_YOLU = ("Bina yapısına", "Kılavuz raylara")
MAKINE_YUK_YOLU_RAY = MAKINE_YUK_YOLU[1]


def makine_raya_mi(deger):
    """Seçim 'raylara' mı  —  eski onay kutusu ( True/'Evet' ) da anlaşılır."""
    if isinstance(deger, bool):
        return deger
    m = str(deger or "").strip().lower()
    return m in ("evet", "e", "var", "true", "1", "yes",
                 MAKINE_YUK_YOLU_RAY.lower())
