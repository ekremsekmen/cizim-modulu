# -*- coding: utf-8 -*-
"""SORUN — çizimin bir sorunu:  metni, ilgili parçaları ve görüldüğü çizim

Sorunlar eskiden düz metindi:  ekran hangi parçanın sorunlu olduğunu
bilemiyor, mühendis sorunu çizimde arıyordu ( 19 Eki ).  Sorun bir METİNDİR
( str'nin alt sınıfı — denetimlerin, hesabın, paketin ve testlerin onu düz
metin gibi kullanması değişmez:  eşitlik, sözlük anahtarı, JSON aynı );
yanında taşıdıkları:

  parcalar  ilgili parçaların elemandaki adları ( "kabin_rayi" — parca_adlari );
            ekran onları çizimde kırmızı işaretler.  Parçayı sorunu üreten
            denetim söyler ( kendi bildiği geometriyle ), metinden tahmin
            edilmez.
  cizim     sorunun en iyi görüldüğü çizim ( cizimler.CIZIMLER adı:  açıklık
            sorunları kesitte, yerleşim sorunları kuyu planında ) — ekran
            sorunu seçince oraya gider.  None:  parçanın göründüğü ilk çizim.

Metne bir şey eklemek ( + , f-metin ) düz metin verir:  yapı yalnız sorunun
kendisinde taşınır.  Aynı metin iki denetimden gelirse birlestir parçaları
birleştirir."""

from cizim import parca_adlari


class Sorun(str):
    """Metin + parcalar + cizim ( yukarıda )."""

    def __new__(cls, metin, parcalar=(), cizim=None):
        o = str.__new__(cls, metin)
        #  Boş ad ( adsız eleman ) atılır
        o.parcalar = tuple(dict.fromkeys(p for p in parcalar if p))
        o.cizim = cizim
        return o

    def __reduce__(self):
        #  İstek içi önbellek yerleşimleri pickle'la kopyalar ( istek_onbellegi )
        return (Sorun, (str(self), self.parcalar, self.cizim))


def parcalari(h):
    """Bir sorunun parçaları ( düz metinse boş )."""
    return getattr(h, "parcalar", ())


def birlestir(liste):
    """Aynı metinli sorunlar bir kez, ilk geldiği sırada;  parçaları birleşir,
    çizimi ilk söyleyenin.  ( Eskiden metinler tekilleştiriliyordu:  sıra ve
    metinler aynı kalır. )"""
    sira = {}
    for h in liste:
        if h not in sira:
            sira[h] = h
            continue
        o = sira[h]
        parca = parcalari(o) + parcalari(h)
        if parca != parcalari(o):
            sira[h] = Sorun(o, parca, getattr(o, "cizim", None) or getattr(h, "cizim", None))
    return list(sira.values())


def yapili(h):
    """Ekrana giden biçim:  { metin , parcalar ( ekrandaki adlarıyla — SVG'nin
    data-ad'ı ) , cizim }."""
    return {
        "metin": str(h),
        "parcalar": list(dict.fromkeys(parca_adlari.ad(p) for p in parcalari(h))),
        "cizim": getattr(h, "cizim", None),
    }
