"""TEMEL YARDIMCILAR — programın her katmanının kullandığı küçük, bağımsız
fonksiyonlar ( hiçbir proje modülünü import etmez ).

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


def kutu_merkezi(k):
    return ((k[0] + k[2]) / 2.0, (k[1] + k[3]) / 2.0)
