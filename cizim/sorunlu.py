# -*- coding: utf-8 -*-
"""SORUNLU ÇİZİM — kurallar sağlanmasa da ekranda çizim kurulur

Bir kural bozulunca ( açıklık yetmiyor, kanat cebi çarpıyor … ) eskiden ekran
hiçbir çizim göstermiyordu:  mühendis sorunu çizimde göremiyordu ( 19 Eki
ölçümü:  örnek projede tek kutu oynatılınca 166 denemenin 97'sinde çizim yok;
doğrulama atlanınca bunların 95'inde çizim kurulabiliyordu ).  Bu kip açıkken
yerleşimler denetim hatasında DURMAZ, kurabildikleri kadar kurar;  yalnız
geometri hiç kurulamıyorsa ( girdi eksik ) durulur — donanim.yerlesim'deki
"kurma ile denetim ayrı" ilkesinin aynısı.

Kip yalnız EKRANIN çiziminde açılır ( cizim_uclari.cizimler_yaniti ).  Hesap,
paket ( pafta.cizim_listesi ) ve sorun listesi kipin dışında kurulur:  onların
davranışı hiç değişmez, uygunsuz çizim pakete giremez.  Kip açıkken
yerleşimlerin "hata" listesi kapalıdakiyle aynı olmayabilir ( durmayan yerleşim
sonraki denetimleri de yapar ) — bu yüzden sorunlar kipin dışından okunur.
İstek içi önbellek kipi anahtarına katar ( istek_onbellegi ):  iki kipin
yerleşimleri birbirine karışmaz."""

import contextlib
import contextvars

_ACIK = contextvars.ContextVar("sorunlu_cizim", default=False)


def acik():
    """Sorunlu çizim kipi açık mı?"""
    return _ACIK.get()


@contextlib.contextmanager
def kip(acilsin=True):
    """Bloğun içinde yerleşimler denetim hatasında durmaz ( acilsin False ise
    blok kipi değiştirmez — çağıran koşulu tek yerde yazsın )."""
    belirtec = _ACIK.set(bool(acilsin) or _ACIK.get())
    try:
        yield
    finally:
        _ACIK.reset(belirtec)
