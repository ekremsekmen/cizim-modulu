# -*- coding: utf-8 -*-
"""
PROJE KAPAĞI  —  HESAPTAN TÜREYEN ASANSÖR BİLGİLERİ

Kapağın "Asansör bilgileri" bölümü projenin kendi hesabında zaten vardır:
kapasite, hız, durak, seyir mesafesi, kabin ölçüleri, askı, adet, tahrik ve
motor gücü.  Kullanıcı bunları kapak formuna ikinci kez yazmak zorunda
kalmamalı;  yazmazsa da kapak BOŞ basılmamalı.  Eskiden formdaki gri
örnek değerler ( "10 kişi", "7,5 kW" … ) dolu gibi görünüyor, çıktıya ise
hiçbiri girmiyordu.

Kural:
    kutuya yazılan değer   →  o basılır ( kullanıcı her zaman ezebilir )
    kutu boş               →  buradaki türetilmiş değer basılır;  arayüz
                              bunu kutunun gri yer tutucusunda gösterir
                              ( ekranda görünen = kâğıda basılan )
    türetilemeyen alan     →  ( blok, asansör sınıfı, ray ölçüsü, ölçek )
                              boş kalır;  yer tutucusu da boştur

İki kaynak ayrı ayrı okunur — her biri kendi yanıtında döner:
    trafikten()  →  yapı kullanım amacı · durak sayısı · seyir mesafesi
    avandan()    →  kapasite · hız · kabin · askı · adet · tahrik · motor · standart
Hesabı hatalı ya da eksik olan kaynaktan HİÇBİR ŞEY türetilmez:  yarım bir
hesabın değeri kapağa "doğru" gibi basılmamalıdır.

Asansörler farklıysa değerler asansör sırasıyla " / " ile yan yana yazılır
( "10 / 16 kişi" );  aynıysa bir kez.
"""
from engine.ortak.steps import sayi_mi, tr

#  Program TS EN 81-20 / 50'ye göre hesap yapar ( bkz. Sabitler A ).
STANDART = "TS EN 81-20"

#  Hesaptan türeyen kapak alanları ( anahtarlar kapak formunun / kapak
#  PDF'inin adlarıdır ).  Arayüz bu listeyi /api/secenekler'den okur.
ALANLAR = ("usage", "stops", "travel",                      # trafikten
           "capacity", "speed", "cabin_width", "cabin_depth", "suspension",
           "elevator_count", "drive_type", "motor_power", "standard")   # avandan

#  Projeden türetilemeyen kapak alanları — yer tutucuları boş kalır.
TURETILMEYEN = ("block", "elevator_class", "rail_size", "scale")


def _birlestir(degerler, birim="", ayrac=" / "):
    """Asansör sırasıyla, tekrarsız;  birim sona bir kez eklenir."""
    goruldu = []
    for d in degerler:
        if d and d not in goruldu:
            goruldu.append(d)
    if not goruldu:
        return ""
    return ayrac.join(goruldu) + (f" {birim}" if birim else "")


def _tam(x):
    """Ölçü ve yük binlik ayracısız yazılır ( çizim teamülü ):  1100 · 1275."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else _sade(x)


def _mm(metre):
    """Özetteki kabin ölçüsü metre cinsindendir ( 1,1 m → "1100" )."""
    return _tam(metre * 1000) if sayi_mi(metre) and metre > 0 else ""


def _sade(x):
    """En çok iki ondalık, sondaki sıfırsız:  5,5 · 11 · 0,75."""
    return tr(x, 2).rstrip("0").rstrip(",") if "," in tr(x, 2) else tr(x, 2)


def trafikten(sonuc) -> dict:
    """Trafik hesabından kapak alanları.  Hesap hatalıysa boş sözlük."""
    if not isinstance(sonuc, dict) or sonuc.get("hata"):
        return {}
    o = sonuc.get("ozet") or {}
    if sonuc.get("tip") == "coklu":
        liste = [a for a in (sonuc.get("asansorler") or []) if isinstance(a, dict)]
    else:
        liste = [o]
    return {k: v for k, v in {
        "usage": o.get("bina_tipi") or "",
        "stops": _birlestir(_tam(a.get("durak")) for a in liste if sayi_mi(a.get("durak"))),
        "travel": _birlestir((tr(a.get("toplam_seyahat")) for a in liste
                              if sayi_mi(a.get("toplam_seyahat"))), "m"),
    }.items() if v}


def avandan(sonuc) -> dict:
    """Avan hesabından kapak alanları.

    Tanımlanan asansörlerden biri bile hesaplanamadıysa ( eksik / hatalı
    girdi ) boş sözlük döner:  adet ve değerler eksik asansörle yazılmaz.
    """
    if not isinstance(sonuc, dict) or sonuc.get("hata"):
        return {}
    tanimli = [a for a in (sonuc.get("asansorler") or []) if isinstance(a, dict)]
    if not tanimli or not all(a.get("aktif") for a in tanimli):
        return {}
    liste = [a.get("ozet") or {} for a in tanimli]

    #  Kapasite kişi ile tanımlanır;  yalnız anma yükü girilmişse kg.
    #  Birim hepsinde aynıysa sona bir kez, değilse her değerin yanına yazılır.
    kap = [(_tam(a["kapasite"]), "kişi") if sayi_mi(a.get("kapasite"))
           else (_tam(a["Q"]), "kg") for a in liste
           if sayi_mi(a.get("kapasite")) or sayi_mi(a.get("Q"))]
    birimler = {b for _s, b in kap}
    kapasite = (_birlestir((s for s, _b in kap), birimler.pop()) if len(birimler) == 1
                else _birlestir(f"{s} {b}" for s, b in kap))

    #  Makine dairesi yok ( MRL ) işareti bütün proje içindir.
    mrl = bool((sonuc.get("makine_dairesi") or {}).get("mk_yok"))
    tahrik = _birlestir(a.get("makine_tipi") or "" for a in liste)
    #  KABİN ÖLÇÜLERİ mm, BİRİMSİZ yazılır:  kapaktaki "D:" hücresi 17 pt'dir,
    #  "1400 mm" en küçük puntoda bile sığmaz ( 4 hane sığar ).  İki farklı
    #  kabin iki satıra basılır ( "1450/1350" ); daha fazlası o hücrede
    #  okunmaz — türetilmez, kutu boş kalır, kullanıcı gerekirse yazar.
    gen = _birlestir((_mm(a.get("kabin_b")) for a in liste), ayrac="/")
    der = _birlestir((_mm(a.get("kabin_a")) for a in liste), ayrac="/")
    if max(gen.count("/"), der.count("/")) > 1:
        gen = der = ""
    return {k: v for k, v in {
        "capacity": kapasite,
        "speed": _birlestir((tr(a.get("V")) for a in liste if sayi_mi(a.get("V"))), "m/s"),
        "cabin_width": gen,
        "cabin_depth": der,
        "suspension": _birlestir(a.get("aski") or "" for a in liste),
        "elevator_count": str(len(liste)),
        "drive_type": (f"{tahrik} (MRL)" if tahrik else "MRL") if mrl else tahrik,
        "motor_power": _birlestir((_sade(a.get("Nsc")) for a in liste
                                   if sayi_mi(a.get("Nsc"))), "kW"),
        "standard": STANDART,
    }.items() if v}
