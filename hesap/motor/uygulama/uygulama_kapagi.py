# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ KAPAĞI  —  HER ASANSÖRÜN TABLOSU PROJEDEN

Kapağın asansör tablosu ( kapasite, hız, durak, seyir, kabin, standart,
sınıf, askı, adet, tahrik, ray, motor gücü, ölçek ) uygulama projesinde
zaten vardır:  hesabın girdisinde ve sonucunda, durak ile ölçek de paketin
çizimlerinde.  Avan kapağının kuralı ( motor/avan/kapak.py ) burada da
geçerlidir:

    kutuya yazılan değer   →  o basılır ( kullanıcı her zaman ezebilir )
    kutu boş               →  projeden türetilen basılır
    türetilemeyen alan     →  boş kalır ( blok )
    hesabı kurulamayan     →  o asansörden HİÇBİR ŞEY türetilmez:  yarım bir
    asansör                   hesabın değeri kapağa "doğru" gibi basılmaz

FARKI:  avan kapağı bütün asansörleri tek tabloda " / " ile yan yana yazar;
burada HER ASANSÖRÜN KENDİ TABLOSU vardır ( ciktilar/kapak_cikti — alt alta ).
Üç asansörde kabin ölçüsü tek hücreye sığmıyor, hangi değerin hangi
asansörün olduğu okunmuyordu.

Kullanıcının yazdığı değer iki biçimde gelir ( kapak_sayfasi ):
    "capacity"      bütün asansörlerin tablosuna
    "capacity.2"    yalnız 2 nolu asansörün tablosuna ( öbürünü ezer )
"""

from cizim import pafta
from motor.avan import tablolar
from motor.avan.kapak import SINIF_I, STANDART, TAHRIK, sade, tam
from motor.ortak.adimlar import tr
from temel import sayi_mi

#  Kapağın asansör tablosundaki alanlar ( kapak_cikti._asansor_degerleri ).
ALANLAR = (
    "block",
    "capacity",
    "speed",
    "stops",
    "travel",
    "standard",
    "cabin_width",
    "cabin_depth",
    "elevator_class",
    "suspension",
    "elevator_count",
    "drive_type",
    "rail_size",
    "motor_power",
    "scale",
)

#  Projeden türetilemeyen:  bloğun adı yapının bilgisidir, hesapta yoktur.
TURETILMEYEN = ("block",)

#  ASANSÖR SINIFI ( ISO 4190-1 ) formun asansör tipinden:  insan asansörü
#  Sınıf I'dir.  "Yük-insan asansörü" Sınıf II ( yük de taşıyan insan
#  asansörü ) ile Sınıf IV ( insanın eşlik ettiği yük asansörü ) arasında
#  ikirciklidir — türetilmez, kullanıcı yazar.
SINIF = {"İnsan asansörü": SINIF_I}

#  RAY ÖLÇÜSÜ:  formun profilleri ( mukavemet_tablolari.RAY_PROFILI ) ISO 7465 /
#  ISO 8100-33 adlarıyla — ad tabanın genişliğidir ( T89:  89 x 62 x 15,88 ).
#  /A ( soğuk çekilmiş ) ya da /B ( işlenmiş ) ayrımı girdide yok:  yazılmaz.
RAY_ADI = {
    "50 x 50 x 5": "T50",
    "70 x 65 x 9": "T70",
    "75 x 62 x 10": "T75",
    "89 x 62 x 15,88": "T89",
    "90 x 75 x 16": "T90",
    "125 x 82 x 16": "T125",
    "127 x 89 x 16": "T127",
}


def _pozitif(x):
    return sayi_mi(x) and x > 0


def ray_adi(profil):
    """Formun ray profili "89 x 62 x 15,88" → "T89".  Tabloda olmayan profil
    ölçüsüyle yazılır ( "89×62", çizimin anteti gibi:  taban × yükseklik )."""
    metin = str(profil or "").strip()
    if metin in RAY_ADI:
        return RAY_ADI[metin]
    parca = [p.strip() for p in metin.split(" x ")]
    return "×".join(parca[:2]) if len(parca) >= 2 else metin


def _asansorden(a, cizim_girdisi, adet):
    """Hesabı kurulan bir asansörün kapak alanları ( boş olan yazılmaz )."""
    g, o = a.get("girdi") or {}, a.get("ozet") or {}
    cg = cizim_girdisi or {}
    Q, kisi = g.get("beyan_yuku"), o.get("kabin_kisi")
    kapasite = " / ".join(
        x for x in (f"{tam(Q)} kg" if _pozitif(Q) else "", f"{tam(kisi)} kişi" if _pozitif(kisi) else "") if x
    )
    durak = (cg.get("dusey") or {}).get("durak_adedi", g.get("durak_adedi"))
    #  Ray ölçüsü:  kabin rayı / ağırlık rayı ( aynıysa bir kez )
    raylar = []
    for p in (g.get("kabin_ray_profili"), g.get("agirlik_ray_profili")):
        if str(p or "").strip() and ray_adi(p) not in raylar:
            raylar.append(ray_adi(p))
    i = g.get("aski_orani")
    return {
        k: v
        for k, v in {
            "capacity": kapasite,
            "speed": f"{tr(g['beyan_hizi'])} m/s" if _pozitif(g.get("beyan_hizi")) else "",
            "stops": tam(durak) if sayi_mi(durak) and durak >= 2 and durak == int(durak) else "",
            "travel": f"{tr(g['seyir_mesafesi'])} m" if _pozitif(g.get("seyir_mesafesi")) else "",
            "standard": STANDART,
            "cabin_width": tam(g["kabin_genisligi"]) if _pozitif(g.get("kabin_genisligi")) else "",
            "cabin_depth": tam(g["kabin_derinligi"]) if _pozitif(g.get("kabin_derinligi")) else "",
            "elevator_class": SINIF.get(str(g.get("asansor_tipi") or "").strip(), ""),
            "suspension": tablolar.aski_orani_metni(i) if _pozitif(i) else "",
            "elevator_count": str(adet),
            "drive_type": TAHRIK,
            "rail_size": " / ".join(raylar),
            "motor_power": f"{sade(g['motor_gucu'])} kW" if _pozitif(g.get("motor_gucu")) else "",
            #  Paftadaki çizimlerin ölçekleri ( antetin yazdığı )
            "scale": (
                pafta.olcek_yazisi(pafta.cizim_olcegi(ad) for ad in pafta.sira(cg)) if cizim_girdisi else ""
            ),
        }.items()
        if v
    }


def uygulamadan(sonuc, cizim_girdileri=()) -> list:
    """Her asansörün kapak alanları, asansör sırasıyla:  [ { … } ].

    sonuc:  uygulama_hesabi.hesapla_coklu;  cizim_girdileri:  aynı sırayla
    çizim girdileri ( durak ve ölçek oradan — paketin çizimleriyle aynı ).
    Hesabı kurulamayan asansörün yeri boş sözlüktür ( tablosu yine çizilir,
    asansörün sırası kaymaz )."""
    if not isinstance(sonuc, dict) or not sonuc.get("aktif"):
        return []
    liste = [a for a in (sonuc.get("asansorler") or []) if isinstance(a, dict)]
    cg = list(cizim_girdileri or [])
    return [
        _asansorden(a, cg[i] if i < len(cg) else None, len(liste)) if a.get("aktif") else {}
        for i, a in enumerate(liste)
    ]


def _yazilan(kapak, anahtar):
    v = kapak.get(anahtar)
    return " ".join(str(v).split()) if v is not None else ""


def kapak_tablolari(kapak, turetilen) -> list:
    """Kapağa basılacak asansör tabloları:  türetilen + kullanıcının yazdığı.

    Asansöre özgü değer ( "capacity.2" ) bütün asansörlerinkini
    ( "capacity" ), o da türetileni ezer."""
    k = kapak if isinstance(kapak, dict) else {}
    cikti = []
    for no, t in enumerate(turetilen, 1):
        d = dict(t)
        for alan in ALANLAR:
            v = _yazilan(k, f"{alan}.{no}") or _yazilan(k, alan)
            if v:
                d[alan] = v
        cikti.append(d)
    return cikti
