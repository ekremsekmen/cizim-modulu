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
  fark      sorunun AÇIĞI ( mm ):  fark ≥ 0 iken sorun yoktur ( açıklık −
            asgari, kutunun kuyu duvarına payı, iki parçanın arası … ).
            Çizim izli sayıyla kurulunca ( cizim/izli.py ) farkın her girdiye
            türevi çıkar:  çare bulucu ( uclar/care.py ) hangi kutunun ne kadar
            değişmesi gerektiğini buradan tahmin eder, sonra yeniden kurarak
            doğrular.  None:  sayısı olmayan sorun ( seçim, eksik alan ).

Metne bir şey eklemek ( + , f-metin ) düz metin verir:  yapı yalnız sorunun
kendisinde taşınır.  Aynı metin iki denetimden gelirse birlestir parçaları
birleştirir."""

from cizim import parca_adlari


class Sorun(str):
    """Metin + parcalar + cizim ( yukarıda )."""

    def __new__(cls, metin, parcalar=(), cizim=None, fark=None):
        o = str.__new__(cls, metin)
        #  Boş ad ( adsız eleman ) atılır
        o.parcalar = tuple(dict.fromkeys(p for p in parcalar if p))
        o.cizim = cizim
        o.fark = fark
        return o

    def __reduce__(self):
        #  İstek içi önbellek yerleşimleri pickle'la kopyalar ( istek_onbellegi )
        return (Sorun, (str(self), self.parcalar, self.cizim, self.fark))


def ayrik(a, b, pay=0.0):
    """İki plan kutusunun arası ( temel.ortusur'un payıyla ):  ≥ 0 iken
    örtüşmezler.  En geniş açılan yanın aralığı ( max — izi korur )."""
    return max(a[0] - b[2] - pay, b[0] - a[2] - pay, a[1] - b[3] - pay, b[1] - a[3] - pay)


def icinde(k, G, D):
    """Kutunun kuyu iç yüzlerine en dar payı:  ≥ 0 iken kuyunun içindedir."""
    return min(k[0], k[1], G - k[2], D - k[3])


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
        fark = getattr(o, "fark", None)
        if parca != parcalari(o) or (fark is None and getattr(h, "fark", None) is not None):
            sira[h] = Sorun(
                o,
                parca,
                getattr(o, "cizim", None) or getattr(h, "cizim", None),
                fark if fark is not None else getattr(h, "fark", None),
            )
    return list(sira.values())


def yapili(h):
    """Ekrana giden biçim:  { metin , parcalar ( ekrandaki adlarıyla — SVG'nin
    data-ad'ı ) , cizim }."""
    return {
        "metin": str(h),
        "parcalar": list(dict.fromkeys(parca_adlari.ad(p) for p in parcalari(h))),
        "cizim": getattr(h, "cizim", None),
    }
