# -*- coding: utf-8 -*-
"""
AVAN ÇİZİMİ — avan kartından seçiciye, seçiciden çizim girdisine  ( 12 Kas 2026 )

İki yerden kullanılır ve ikisi aynı asansörü çizer:

    ekran   /api/avan/cizimler      ( uclar/avan_cizim_uclari.py )
    paket   /api/indir/proje-dwg    ( uclar/avan_uclari.py — "Projeyi indir" )

Asansörün MİMARİSİ avan kartındadır ( kuyu genişliği / derinliği, kotlar ),
makine dairesi ortak panelde;  yük Tablo-7'den ( ya da Q elle ), hız trafikten.
Seçici ( uclar/avan_secici.py ) bu kuyuya doğrulanmış asansörü bulur.
"""

import copy

from cizim import avan_kipi, istek_onbellegi
from motor.avan import tablolar
from motor.ortak.adimlar import evet_mi
from motor.uygulama import uygulama_hesabi
from temel import sayi_mi
from uclar import avan_secici, cizim_uclari, uygulama_istegi

#  Avan kartındaki mimari alanlar ( kotlar metindir — uygulamanın kot kutuları gibi okunur )
KART = ("kuyu_genisligi", "kuyu_derinligi", *avan_secici.KOTLAR)
#  Çizim İSTENDİ sayılan alanlar:  kuyu genişliği avan hesabının da girdisidir, tek başına
#  çizim isteği değildir ( eski projelerde de doludur )
ISTEK = tuple(k for k in KART if k != "kuyu_genisligi")


def mimari(a, ortak):
    """Avan asansörü ( okunmuş kart ) + ortak panel → seçicinin girdisi."""
    yuk = a.get("Q_elle") if sayi_mi(a.get("Q_elle")) else tablolar.tablo7_yuk(a.get("kapasite"))
    m = {"beyan_yuku": yuk, "beyan_hizi": a.get("V"), "mk_yok": evet_mi(ortak.get("mk_yok"))}
    m.update({k: a.get(k) for k in KART})
    if not m["mk_yok"]:
        m.update({k: ortak.get(k) for k in avan_secici.MIMARI_GENEL})
    return m


def secim(g, i):
    """Okunmuş avan girdisinin ( avan_uclari.avan_girdisi ) i. asansörü için seçicinin
    sonucu ( avan_secici.sec ) ya da { durum:  "hata" , hata } — asansör yoksa."""
    asansorler = g["asansorler"]
    if not 0 <= i < len(asansorler) or asansorler[i] is None:
        return {
            "durum": "hata",
            "hata": "Avan hesabında bu asansör yok — kapasite ve hız trafik hesabından gelir.",
        }
    return avan_secici.sec(mimari(asansorler[i], g["ortak"]))


def istendi(a):
    """Bu kartta çizim için bir şey girilmiş mi ( ISTEK )."""
    return any(a.get(k) not in (None, "") for k in ISTEK)


def paket_cizimleri(g, proje_adi, adlar):
    """Paketin çizimleri:  ( [ çizim girdisi — avan kipinde ] , [ çizimi olmayan
    asansörlerin adları ] ).  adlar:  asansörlerin paftadaki adları ( sırayla ).

    Yalnız çizimi İSTENEN asansörler ( mimarisi girilmiş kartlar ):  hiçbir kartta
    mimari yoksa paket bugünkü gibidir ( çizimsiz, notsuz ).  İstenip de çizilemeyen
    asansör ( eksik mimari, mimardan istenecek ölçü, sığmayan kuyu ) pakete çizimsiz
    girer ve adı döner — çağıran kullanıcıya SÖYLER."""
    gler, eksik = [], []
    for i, a in enumerate(g["asansorler"]):
        if a is None or not istendi(a):
            continue
        r = secim(g, i)
        cg = None
        if r["durum"] == "uygun":
            v = copy.deepcopy(r["istek"])
            v["asansorler"][0]["asansor_adi"] = adlar[i]
            #  Avan kipi ( cizim/avan_kipi.py ):  ürün yazıları ve hesap işareti yok
            with avan_kipi.etkin(), istek_onbellegi.etkin():
                A, o = uygulama_istegi.asansor_girdileri(copy.deepcopy(v))
                s = uygulama_hesabi.hesapla_coklu(A, o)
                ((cg, hata),) = cizim_uclari.girdiler(v, A, o, s, proje_adi)
            if hata:
                cg = None
        if cg is None:
            eksik.append(adlar[i])
        else:
            gler.append(cg)
    return gler, eksik
