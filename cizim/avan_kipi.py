# -*- coding: utf-8 -*-
"""
AVAN KİPİ — çizim avan projesi için kuruluyor  ( 12 Kas 2026 )

Avan projesinin çizimleri uygulamanın çizim yolundan çıkar ( uclar/
avan_cizim_uclari.py ):  geometri aynıdır.  Fark YAZIDADIR — avanda ürün
seçilmemiştir;  makineyi, halatı, rayı seçici ( uclar/avan_secici.py ) çizimi
kurabilmek için seçti, mimarın ya da avanın beyanı değildir:

  · veri tablosunda ürün satırları yazılmaz ( motor gücü, tahrik kasnağı, halat,
    ray profili, konsol arası, regülatör ) — cizim/veri_tablosu.py
  · antette ray hücresi boş kalır, kasnak düzenlemesi çizilmez ( tahrikin çizimi ) —
    cizim/pafta.py
  · hesabın ürün bölümleri için "uygun değil" işareti ve notu yoktur
    ( cizim/kopru.py · _proje )
  · notlara ürünün uygulama projesinde kesinleşeceği yazılır

Kip isteğe bağlıdır ( ContextVar — istek_onbellegi gibi ):  çizim girdisi
( g["proje"]["avan"] ) kurulurken okunur, sonrası girdiden.  Aynı önbellek
bloğunda iki kip karışmaz:  blok kipin İÇİNDE açılır.
"""

import contextlib
import contextvars

_ACIK = contextvars.ContextVar("avan_kipi", default=False)

#  Notlar tablosuna eklenen satır ( veri_tablosu )
NOT = "Avan projesi:  makine, halat ve ray seçimi uygulama projesinde kesinleşir."


def acik():
    return _ACIK.get()


@contextlib.contextmanager
def etkin():
    belirtec = _ACIK.set(True)
    try:
        yield
    finally:
        _ACIK.reset(belirtec)
