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

from cizim import avan_kipi, istek_onbellegi, katlar, kopru
from motor.avan import avan_hesabi, tablolar
from motor.ortak.adimlar import evet_mi
from motor.uygulama import uygulama_hesabi
from temel import sayi_mi
from uclar import avan_secici, cizim_uclari, uygulama_istegi

#  Avan kartındaki mimari alanlar ( kotlar metindir — uygulamanın kot kutuları gibi okunur )
KART = ("kuyu_genisligi", "kuyu_derinligi", *avan_secici.KOTLAR, *avan_secici.ADLAR, "tavan_dosemesi")
#  Çizim İSTENDİ sayılan alanlar:  kuyu genişliği avan hesabının da girdisidir, tek başına
#  çizim isteği değildir ( eski projelerde de doludur )
ISTEK = ("kuyu_derinligi", *avan_secici.KOTLAR)


#  AVANIN BEYANI ( 12 Kas ):  avan motor hesabının askı oranı ve makine tipi çizimde aynen
#  durur — hesap sayfası "1:1 dişli" derken pafta "2:1 dişlisiz" çizmez.  Seçicinin
#  girdisi ( uygulamanın alanı ) → kartın alanı ve ekrandaki adı
BEYAN = {"aski_orani": ("i_palanga", "Askı oranı"), "makine_tipi": ("makine_tipi", "Makine tipi")}


def avan_ozeti(g, i):
    """i. asansörün avan hesabının özeti ( motor.avan.avan_hesabi — seçilen motor gücü
    Nsç … ) ya da None:  avan hesabı reddedildi / asansör hesaplanamadı."""
    s = avan_hesabi.hesapla(g)
    return next((x for x in (s.get("ozet") or {}).get("asansorler") or [] if x.get("no") == i + 1), None)


def _beyan(a, sabitler):
    """Kartın beyanı, avan motor hesabının okuduğu gibi:  askı oranı kartta boşsa ofis
    standardı ( avan_hesabi.sabitler ), makine tipi kartta seçilmişse.  Avan hesabı
    tamamlanmamış olsa da aynıdır ( çizim hesap bitince değişmez ).  Uygulamanın seçeneği
    olmayan değer ( 4:1 askı ) beyan edilmez — seçici paketinkini kullanır."""
    i = a.get("i_palanga")
    if not sayi_mi(i):
        i = avan_hesabi.sabitler(sabitler).get("i_palanga")
    tip = a.get("makine_tipi")
    b = {}
    if i in tablolar.ASKI_ORANLARI.values():
        b["aski_orani"] = int(i)
    if tip in tablolar.MAKINE_TIPLERI:
        b["makine_tipi"] = tip
    return b


def _yazi(anahtar, deger):
    return tablolar.aski_orani_metni(int(deger)) if anahtar == "aski_orani" else deger


def mimari(a, ortak, sabitler=None):
    """Avan asansörü ( okunmuş kart ) + ortak panel ( + ofis standardı ) → seçicinin girdisi."""
    yuk = a.get("Q_elle") if sayi_mi(a.get("Q_elle")) else tablolar.tablo7_yuk(a.get("kapasite"))
    m = {"beyan_yuku": yuk, "beyan_hizi": a.get("V"), "mk_yok": evet_mi(ortak.get("mk_yok"))}
    m.update({k: a.get(k) for k in KART})
    if not m["mk_yok"]:
        m.update({k: ortak.get(k) for k in avan_secici.MIMARI_GENEL})
    m.update(_beyan(a, sabitler))
    return m


def kot_bilgisi(g):
    """Kot tablosunun sunucudan beklediği ( ekran hesaplamaz ) — asansör sırasıyla, kartı
    olmayan için None:  hesabın kotlardan türettikleri ( avan_hesabi.kot_turetilenleri —
    Hk, seyir, durak, kuyu_dibi, ust_bosluk;  m ), "hata" ( kullanılamayan kot ), "adlar"
    ( katlar.ad_tablosu — kuraldan kat adları, giriş katı ) ve "doseme" ( tavan döşemesinin
    çizimdeki kalınlığı, mm — kartta girilmişse o, boşsa kuraldan:  "doseme_kural" )."""
    kural = kopru.tavan_dosemesi({})
    liste = []
    for a in g["asansorler"]:
        if a is None:
            liste.append(None)
            continue
        t, hata = avan_hesabi.kot_turetilenleri(a)
        #  Kartta girilmişse o ( aralığını uygulamanın kapısı denetler — seçici söyler )
        d = a.get("tavan_dosemesi")
        doseme = d if sayi_mi(d) and d > 0 else kural
        liste.append(
            {
                **(t or {}),
                "hata": hata,
                "adlar": katlar.ad_tablosu(a),
                "doseme": doseme,
                "doseme_kural": kural,
            }
        )
    return liste


def secim(g, i):
    """Okunmuş avan girdisinin ( avan_uclari.avan_girdisi ) i. asansörü için seçicinin
    sonucu ( avan_secici.sec ) ya da { durum:  "hata" , hata } — asansör yoksa."""
    asansorler = g["asansorler"]
    if not 0 <= i < len(asansorler) or asansorler[i] is None:
        return {
            "durum": "hata",
            "hata": "Avan hesabında bu asansör yok — kapasite ve hız trafik hesabından gelir.",
        }
    r = avan_secici.sec(mimari(asansorler[i], g["ortak"], g.get("sabitler")))
    ozet = avan_ozeti(g, i)
    #  Avanın kendi motor gücü ( Nsç ):  paftanın bilgi tablosuna ( cizim/avan_kipi.py )
    r["avan"] = {"motor_gucu": (ozet or {}).get("Nsc")}
    #  Beyan çelişkisi kartın diliyle:  kartın alanı, ekrandaki adı, "2:1" yazımı
    for b in r.get("beyan") or []:
        kart, ad = BEYAN[b["anahtar"]]
        b.update(
            kart=kart,
            etiket=ad,
            eski_yazi=_yazi(b["anahtar"], b["eski"]),
            yeni_yazi=_yazi(b["anahtar"], b["yeni"]),
        )
    return r


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
            with avan_kipi.etkin(r["avan"]), istek_onbellegi.etkin():
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
