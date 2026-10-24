"""TEMEL YARDIMCILAR — programın her katmanının kullandığı küçük, bağımsız
fonksiyonlar ve iki katmanın birlikte okuduğu kural tabloları ( hiçbir proje
modülünü import etmez ).

Eskiden her modül kendi kopyasını tutuyordu:  "sayı mı" 13 yerde tanımlıydı
ve üçü sonsuzu / NaN'ı reddederken öbürleri kabul ediyordu — aynı değer bir
modülde geçersiz, ötekinde sayı sayılıyordu.  Tek tanım:  burası.

Plan kutusu:  ( x0, y0, x1, y1 ) — x0 < x1, y0 < y1;  mm.
"""

import math


def sayi_mi(v):
    """Hesaba girebilecek bir sayı mı:  int ya da float, bool DEĞİL ( True bir
    int'tir — tuzak ), sonlu ( NaN ve sonsuz sayı değildir )."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def bos_mu(v):
    """Kutu boş mu:  girilmemiş ( None ) ya da yalnız boşluk."""
    return v is None or (isinstance(v, str) and not v.strip())


def eleman_kutusu(el):
    """Dikdörtgen çizim elemanının ( x, y, g, d ) plan kutusu."""
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def ortusur(a, b, pay=0.0):
    """İki plan kutusu iç içe geçiyor mu.  Kenarda değmek sayılmaz;  pay > 0
    ise kutular pay kadar büyütülmüş gibi ( yakınlık ), < 0 ise küçültülmüş."""
    return a[0] < b[2] + pay and b[0] < a[2] + pay and a[1] < b[3] + pay and b[1] < a[3] + pay


def kucuk(metin):
    """Türkçe küçük harf:  str.lower() "I"yı "i", "İ"yi noktalı "i̇" yapar
    ( "AĞIRLIK" → "ağirlik" — iletilerde böyle yazıyordu, 19 Eki )."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


#  AutoCAD'in TEXT ve MTEXT'te ortak kodları:  "%%" + harf özel karakterdir
#  ( %%c → Ø, %%d → °, %%p → ± ), "^" + harf denetim karakteri ( ^I sekme,
#  ^J satır başı ).  Kullanıcının yazdığı adlar ( asansör, proje ) çizime ve
#  paftaya girer:  "%%c" Ø olur, şapka macOS'ta AutoCAD'i çökertir
#  ( hesap/ciktilar/dxf_cikti.CAD_SIMGE — orada ölçüldü ).  Şapka aynı
#  görünüşteki U+02C6'ya çevrilir;  "%%" geçen yazıda her "%" AutoCAD'in
#  tek yüzde kodu "%%%" olur ( tek "%" kod değildir, olduğu gibi kalır ).
def cad_yazisi(metin):
    """Yazıyı AutoCAD'in kod saymayacağı biçime çevirir ( TEXT ve MTEXT )."""
    metin = metin.replace("^", "ˆ")
    return metin.replace("%", "%%%") if "%%" in metin else metin


def cumle_basi(metin):
    """Türkçe ilk harf büyük, gerisi küçük — str.capitalize'ın Türkçesi
    ( "KABİN BAĞLANTISI" → "Kabin bağlantısı";  capitalize "Kabi̇n bağlantisi" yazıyordu )."""
    k = kucuk(metin)
    return k[:1].replace("i", "İ").replace("ı", "I").upper() + k[1:]


def kutu_merkezi(k):
    return ((k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0)


#  KABLO KESİTİ → ÖNÜNDEKİ SİGORTANIN EN BÜYÜK ANMA AKIMI  ( mm² , A ) —
#  Asansör Periyodik Kontrol Yönetmeliği EK-5 1.31.13:  sigorta kablonun bu
#  sınırını aşmaz.  Hesap ( makine besleme hattının grup sigortası — avan
#  tablolar.sigorta_siniri ) ve elektrik projesi ( son devrelerin kablosu —
#  cizim/elektrik.devre_kesiti ) aynı tablodan okur:  hesap çizim modülünü
#  ( ezdxf ), çizim hesabı import edemez.
KESIT_SIGORTA = ((1.0, 6), (1.5, 10), (2.5, 20), (4.0, 32), (6.0, 50))
