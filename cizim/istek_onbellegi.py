# -*- coding: utf-8 -*-
"""İSTEK İÇİ ÖNBELLEK — bir isteğin içinde aynı yerleşim bir kez kurulur.

Çizim isteğinde yerleşimler defalarca baştan kuruluyordu:  doğrulama, başlık ve
çizim her biri kendi kurar ( 63444-2 gerçek projesinde kuyu dibi 52, kuyu üstü
45, düşey yerleşim 20 kez — isteğin yarısı;  17 Eki ).  `sakla` ile sarılan
fonksiyon, etkin bir istekte aynı girdiyle ikinci kez çağrılınca ilk sonucu
verir.

GÜVENLİK ( deneyle bulunan üç tuzak ):
  -  Anahtar girdinin İÇERİĞİDİR, kimliği değil:  regülatörün yerini arayan
     köprü aynı g'yi yerinde değiştirip yeniden kurar;  Python silinen bir
     g'nin kimliğini yenisine verir.
  -  Saklarken ve verirken KOPYA:  yazı yerleştirici yerleşimin parça
     listesindeki yazıların yerini sonradan değiştirir ( kabin üstü `taban` ).
     Her çağıran bugünkü gibi kendine ait bir sonuç alır.  Kopya pickle'la:
     deepcopy'nin üçte biri kadar sürer ( 63444-2:  360 → 285 ms ).
     Paketlenemeyen sonuç önbelleğe girmez.
  -  Ölçüye tıklamanın iz sürmesi açıkken ( izli.izlemede ) önbellek devre
     dışıdır:  izli sayı float'tır, JSON'da düz sayıya döner — anahtarı düz
     girdiyle aynı olur, türevi taşımayan sonuç dönerdi.  JSON'a çevrilemeyen
     girdi de önbelleğe girmez.
  -  Sorunlu çizim kipi ( cizim/sorunlu.py ) anahtara girer:  kip açıkken
     yerleşimler denetim hatasında durmaz, sonuçları kapalıdakinden farklıdır.
Önbellek yalnız `etkin` bloğunun içinde yaşar:  istekler ve kullanıcılar arası
hiçbir şey paylaşılmaz."""

import contextlib
import contextvars
import functools
import json
import pickle

from cizim import izli
from cizim import sorunlu

_ETKIN = contextvars.ContextVar("istek_onbellegi", default=None)


def _anahtar(ad, a, k):
    try:
        return ad + json.dumps((a, k), sort_keys=True, allow_nan=True)
    except (TypeError, ValueError):
        return None  # JSON'a çevrilemeyen girdi:  önbelleğe girmez


def sakla(f):
    """f'yi istek içi önbelleğe bağlar ( etkin istek yoksa olduğu gibi çalışır )."""
    ad = f"{f.__module__}.{f.__qualname__}:"

    @functools.wraps(f)
    def sarili(*a, **k):
        d = _ETKIN.get()
        if d is None or izli.izlemede():
            return f(*a, **k)
        anahtar = _anahtar(ad + ("sorunlu:" if sorunlu.acik() else ""), a, k)
        if anahtar is None:
            return f(*a, **k)
        if anahtar not in d:
            sonuc = f(*a, **k)
            try:
                d[anahtar] = pickle.dumps(sonuc, protocol=pickle.HIGHEST_PROTOCOL)
            except (pickle.PicklingError, TypeError, AttributeError):
                d[anahtar] = None
            return sonuc if d[anahtar] is None else pickle.loads(d[anahtar])
        if d[anahtar] is None:
            return f(*a, **k)
        return pickle.loads(d[anahtar])

    return sarili


@contextlib.contextmanager
def etkin():
    """Bloğun içindeki çağrılar önbelleği paylaşır;  iç içe bloklar dıştakini
    kullanır."""
    if _ETKIN.get() is not None:
        yield
        return
    belirtec = _ETKIN.set({})
    try:
        yield
    finally:
        _ETKIN.reset(belirtec)
