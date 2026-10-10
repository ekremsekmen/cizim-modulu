# -*- coding: utf-8 -*-
"""
ŞEMADAN TÜRETİLENLER — motorların alan sözleşmeleri, form, sayı sözlüğü

Hiçbiri elle ikinci kez yazılmaz:  alanın etiketi, grubu, kaynağı, formdaki
yeri ve doğrulama bayrakları yalnız tasarim/alanlar.py'de durur.
"""

from tasarim.alanlar import ALANLAR, ALAN, GRUPLAR, CIZIM, HESAP


def sozlesme(ad):
    """Bir motorun alan sözleşmesi ( şema sırasıyla ):
    ( anahtar , etiket , birim , tür , seçenekler , varsayılan )."""
    return tuple(
        (a.anahtar, a.etiket, a.birim, a.tur, a.secenekler, a.varsayilan) for a in ALANLAR if a.sozlesme == ad
    )


def anahtarlar(sozlesme=None, **kosul):
    """Koşula uyan alanların anahtarları ( şema sırasıyla ).
    anahtarlar( "mukavemet" , pozitif=True )  →  pozitif olması gereken mukavemet alanları."""
    return tuple(
        a.anahtar
        for a in ALANLAR
        if (sozlesme is None or a.sozlesme == sozlesme) and all(getattr(a, k) == v for k, v in kosul.items())
    )


def bilgi(a):
    """Formdaki ⓘ metni:  alanın açıklaması, boşsa çizimden geliyorsa kuralıyla."""
    return f"{a.bilgi}  {a.cizimden}".strip() if a.cizimden else a.bilgi


def uygulanmayan(mk_yok, sozlesme=None):
    """Makine yerleşimine göre hesaba ve çizime girmeyen ( ekranda gizli ) alanlar."""
    disi = "daireli" if mk_yok else "mrl"
    return {a.anahtar for a in ALANLAR if a.yerlesim == disi and (sozlesme is None or a.sozlesme == sozlesme)}


def cizimden():
    """Boşsa çizimden gelen alanlar → kuralı ( cizim/kopru.CIZIMDEN )."""
    return {a.anahtar: a.cizimden for a in ALANLAR if a.cizimden}


def form_alani(a):
    """Formun bir kutusu ( arayüzün beklediği biçimde )."""
    return {
        "anahtar": a.anahtar,
        "hucre": "",
        "etiket": a.etiket,
        "birim": a.birim,
        "tur": a.tur,
        "secenekler": list(a.secenekler) if a.secenekler is not None else None,
        "varsayilan": a.varsayilan,
        "gelismis": a.gelismis,
        "bilgi": bilgi(a),
        "secenek_metni": a.secenek_metni,
        "kaynak": a.kaynak,
        #  Seçenek yalnız bir makine yerleşiminde seçilebilir:
        #  { seçenek : { "yerlesim" , "sebep" } } — arayüz ötekinde kapatır.
        "secenek_kosulu": (
            {str(s): {"yerlesim": y, "sebep": n} for s, (y, n) in a.secenek_kosulu.items()}
            if a.secenek_kosulu
            else None
        ),
    }


def form_gruplari(sozlesme=None):
    """Formun grupları, tasarım sırasıyla — yalnız formda kutusu olan alanlar."""
    gruplar = []
    for ad in GRUPLAR:
        alanlar = [
            form_alani(a)
            for a in ALANLAR
            if a.grup == ad and a.formda and (sozlesme is None or a.sozlesme == sozlesme)
        ]
        if alanlar:
            gruplar.append({"ad": ad, "alanlar": alanlar})
    return gruplar


def form():
    """Formun kendini kurduğu sözleşme ( şemanın payı )."""
    return {
        "gruplar": form_gruplari(),
        "proje_geneli": list(anahtarlar(proje_geneli=True, formda=True)),
        "yerlesime_gore_gizli": {"mrl": sorted(uygulanmayan(True)), "daireli": sorted(uygulanmayan(False))},
        "cizimden": list(cizimden()),
        "hesaplanan": list(anahtarlar(kaynak=HESAP)),
    }


def grubu(anahtar):
    return ALAN[anahtar].grup


def formda_olmayan():
    """Formda kutusu olmayan alanlar ( çizimden ya da hesaptan gelir )."""
    return tuple(a.anahtar for a in ALANLAR if not a.formda)


def cizimden_gelen_formda_olmayan():
    return tuple(a.anahtar for a in ALANLAR if not a.formda and a.kaynak == CIZIM)
