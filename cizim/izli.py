# -*- coding: utf-8 -*-
"""İZLİ SAYI — ölçünün kaynağını çizimi bir kez kurarak bulmak ( otomatik türev )

Ekranda bir ölçüye tıklanınca program onun hangi girdilerden geldiğini ve
nasıl değiştiğini ( eğim:  girdi 1 artınca ölçü kaç artar ) söyler.  Bunun
için girdiler İZLİ SAYIYA sarılır:  değeri düz sayıyla aynıdır, yanında
{ girdi kimliği:  ∂değer / ∂girdi } taşır.  Toplama, çarpma, bölme türevi
zincir kuralıyla taşır;  çizim bir kez kurulur ve her ölçünün uzunluğu
kaynaklarını bilir ( ileri yönlü otomatik türev ).  Önceki yöntem her girdiyi
±1 mm oynatıp çizimi 200 – 280 kez yeniden kuruyordu ( 3 – 9 sn );  o yöntem
şimdi testte türevin denetçisidir ( testler/test_olcu_turevi.py ).

İzli sayı bir float'tır:  karşılaştırma, biçimleme, sözlük anahtarı aynı
çalışır;  değer düz float işlemiyle aynı sırada hesaplanır — çizim birebir
aynı kalır.  Türev yalnız float döndüren işlemlerden geçer:  int döndürenler
( round( x ), math.floor, // ) izi düşürür.  math'in fonksiyonları da düşürür:
geometride bu modülün karşılıkları kullanılır ( atan2, hypot, sin … — izleme
kapalıyken math'in kendisi ).  İzi düşen yoldan gelen bağlılık görünmez;  bir
ölçünün bir ucu izli, öbürü değilse eğim YANLIŞ olur — denetçi test bunu yakalar.

İzleme yalnız çözümleme sırasında açıktır ( izleme() ).  Kapalıyken izli sayı
hiç oluşmaz:  sayi() float() ile, oz() değerin kendisiyle aynıdır.
"""

import contextlib
import math
import threading

_float = float
#  İzleme iş parçacığına özeldir:  aynı anda kurulan başka çizimlere dokunmaz
_DURUM = threading.local()


def _birlesim(ta, ka, tb, kb):
    """ta · ka + tb · kb  ( seyrek türevler;  sıfır terim tutulmaz )."""
    out = {}
    if ta:
        for k, v in ta.items():
            out[k] = v * ka
    if tb:
        for k, v in tb.items():
            out[k] = out.get(k, 0.0) + v * kb
    return {k: v for k, v in out.items() if v != 0.0}


def _sonuc(v, t):
    return Izli(v, t) if t else v


def _t(x):
    return x.t if isinstance(x, Izli) else None


class Izli(float):
    """Değer + türev ( t:  { kimlik:  ∂değer / ∂kimlik } )."""

    __slots__ = ("t",)

    def __new__(cls, deger, t):
        o = _float.__new__(cls, deger)
        o.t = t
        return o

    def __reduce__(self):
        return (Izli, (_float(self), dict(self.t)))

    def __add__(self, o):
        r = _float.__add__(self, o)
        return r if r is NotImplemented else _sonuc(r, _birlesim(self.t, 1.0, _t(o), 1.0))

    def __radd__(self, o):
        r = _float.__radd__(self, o)
        return r if r is NotImplemented else _sonuc(r, _birlesim(self.t, 1.0, _t(o), 1.0))

    def __sub__(self, o):
        r = _float.__sub__(self, o)
        return r if r is NotImplemented else _sonuc(r, _birlesim(self.t, 1.0, _t(o), -1.0))

    def __rsub__(self, o):
        r = _float.__rsub__(self, o)
        return r if r is NotImplemented else _sonuc(r, _birlesim(self.t, -1.0, _t(o), 1.0))

    def __mul__(self, o):
        r = _float.__mul__(self, o)
        if r is NotImplemented:
            return r
        return _sonuc(r, _birlesim(self.t, _float(o), _t(o), _float(self)))

    def __rmul__(self, o):
        r = _float.__rmul__(self, o)
        if r is NotImplemented:
            return r
        return _sonuc(r, _birlesim(self.t, _float(o), _t(o), _float(self)))

    def __truediv__(self, o):
        r = _float.__truediv__(self, o)
        if r is NotImplemented:
            return r
        b = _float(o)
        return _sonuc(r, _birlesim(self.t, 1.0 / b, _t(o), -_float(self) / (b * b)))

    def __rtruediv__(self, o):
        r = _float.__rtruediv__(self, o)
        if r is NotImplemented:
            return r
        a = _float(self)
        return _sonuc(r, _birlesim(self.t, -_float(o) / (a * a), _t(o), 1.0 / a))

    def __mod__(self, o):
        #  x % c, c sabitken:  eğim 1 ( sıçrama noktaları dışında )
        r = _float.__mod__(self, o)
        if r is NotImplemented or _t(o):
            return r
        return _sonuc(r, self.t)

    def __pow__(self, n, mod=None):
        r = _float.__pow__(self, n, mod)
        if r is NotImplemented or _t(n) or mod is not None:
            return r
        return _sonuc(r, _birlesim(self.t, n * _float.__pow__(self, n - 1), None, 0.0))

    def __neg__(self):
        return _sonuc(-_float(self), _birlesim(self.t, -1.0, None, 0.0))

    def __pos__(self):
        return self

    def __abs__(self):
        return self if _float(self) >= 0.0 else -self

    def __round__(self, n=None):
        #  round( x ) int döndürür ( iz düşer );  round( x , n ) kırıntı
        #  temizliğidir — eğim korunur
        if n is None:
            return _float.__round__(self)
        return _sonuc(_float.__round__(self, n), self.t)


@contextlib.contextmanager
def izleme():
    """Bu blokta oz() ve girdiye sarılan değerler izli sayı üretir."""
    eski = getattr(_DURUM, "acik", False)
    _DURUM.acik = True
    try:
        yield
    finally:
        _DURUM.acik = eski


def izlemede():
    return getattr(_DURUM, "acik", False)


def turev(x):
    """{ kimlik:  eğim } — izli değilse boş."""
    return dict(x.t) if isinstance(x, Izli) else {}


def sayi(x):
    """float( x ) — izli sayının izini düşürmeden ( çizim elemanları )."""
    return x if isinstance(x, Izli) else _float(x)


def girdi(v, kimlik):
    """Girdinin değeri:  izleme açıksa kendi kimliğine eğimi 1 olan izli sayı."""
    if not izlemede() or isinstance(v, bool) or not isinstance(v, (int, _float)):
        return v
    return Izli(_float(v), {kimlik: 1.0})


def oz(v, kimlik):
    """Boş bırakılıp kuralla ya da varsayılanla dolan alanın değeri:  izleme
    açıksa kendi kimliğine eğim 1 eklenir — kutuya değer yazılsa ölçü onunla
    değişir.  Kuralın girdilerine eğimi ( DBGW = Gy + 60 → Gy'ye 1 ) korunur."""
    if not izlemede() or isinstance(v, bool) or not isinstance(v, (int, _float)):
        return v
    t = turev(v)
    if kimlik in t:
        #  Zaten kendi kutusundan geliyor ( sabitler, bir çizimin tam S'sini
        #  yeniden sabitler()'den geçirince ):  ikinci kez eklenmez
        return v
    t[kimlik] = 1.0
    return Izli(_float(v), t)


#  ── math'in türev taşıyan karşılıkları ──────────────────────────────


def _tek(f, df, x):
    v = f(x)
    return _sonuc(v, _birlesim(x.t, df(_float(x)), None, 0.0)) if isinstance(x, Izli) else v


def sqrt(x):
    return _tek(math.sqrt, lambda a: 0.5 / math.sqrt(a), x)


def sin(x):
    return _tek(math.sin, math.cos, x)


def cos(x):
    return _tek(math.cos, lambda a: -math.sin(a), x)


def tan(x):
    return _tek(math.tan, lambda a: 1.0 / math.cos(a) ** 2, x)


def asin(x):
    return _tek(math.asin, lambda a: 1.0 / math.sqrt(1.0 - a * a), x)


def acos(x):
    return _tek(math.acos, lambda a: -1.0 / math.sqrt(1.0 - a * a), x)


def atan(x):
    return _tek(math.atan, lambda a: 1.0 / (1.0 + a * a), x)


def degrees(x):
    return _tek(math.degrees, lambda _a: 180.0 / math.pi, x)


def radians(x):
    return _tek(math.radians, lambda _a: math.pi / 180.0, x)


def atan2(y, x):
    v = math.atan2(y, x)
    if not (isinstance(x, Izli) or isinstance(y, Izli)):
        return v
    a, b = _float(y), _float(x)
    r2 = a * a + b * b
    return _sonuc(v, _birlesim(_t(y), b / r2, _t(x), -a / r2))


def hypot(*xs):
    v = math.hypot(*xs)
    if not any(isinstance(x, Izli) for x in xs):
        return v
    t = None
    for x in xs:
        if isinstance(x, Izli) and v:
            t = _birlesim(t, 1.0, x.t, _float(x) / v)
    return _sonuc(v, t)


def fsum(xs):
    xs = list(xs)
    v = math.fsum(xs)
    t = None
    for x in xs:
        if isinstance(x, Izli):
            t = _birlesim(t, 1.0, x.t, 1.0)
    return _sonuc(v, t)
