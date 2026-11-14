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
from tasarim import alanlar
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
BEYAN = {
    "aski_orani": ("i_palanga", "Askı oranı"),
    "makine_tipi": ("makine_tipi", "Makine tipi"),
    #  Kapı trafik hesabındadır ( kullanıcı kararı 14 Kas ):  öneri trafiğin sütununa yazılır
    "kapi_genisligi": ("kapi_genisligi", "Kapı genişliği"),
    "kat_kapisi_tipi": ("kapi_tipi", "Kapı tipi"),
}
TRAFIKTE = ("kapi_genisligi", "kat_kapisi_tipi")
#  Trafik hesabının kapı tipi ( MMO/697 Tablo-4 ) → kat kapısının ailesi ( avan_secici.kapi_ailesi ).
#  Trafik yalnız aileyi seçer;  kanat sayısı ve açılış yönü hazır asansörden / seçiciden.
KAPI_AILESI = {
    "Teleskopik Otomatik": "Teleskopik",
    "Merkezden Açılan Oto.": "Otomatik Merkezi",
    "Kabin İçi Oto. Kat K.Ç.": "Manuel",
}


def _kapi_beyani(a, taslak):
    """Trafik hesabının kapısı ( kartta kapi_genisligi / kapi_tipi — ekran trafikten koyar ) →
    seçicinin beyanı.  Tip hazır asansörünkiyle aynı ailedense hazır asansörün tipi aynen
    ( yönü ve kanat sayısıyla );  değilse o ailenin tipi, hazır asansörün açılış yönüyle."""
    b = {}
    if sayi_mi(a.get("kapi_genisligi")) and a["kapi_genisligi"] > 0:
        b["kapi_genisligi"] = a["kapi_genisligi"]
    aile = KAPI_AILESI.get(a.get("kapi_tipi"))
    if aile and taslak:
        tip = taslak["asansor"].get("kat_kapisi_tipi") or alanlar.ALAN["kat_kapisi_tipi"].varsayilan
        if avan_secici.kapi_ailesi(tip) != aile:
            yon = "Sağ" if tip.endswith("Sağ") else "Sol"
            tip = aile if aile == "Otomatik Merkezi" else f"{aile} {yon}"
        b["kat_kapisi_tipi"] = tip
    return b


#  KABİN ( 13 Kas ):  çizimin kabini trafik hesabının kapasitesinin kabinidir ( hazır asansörünki —
#  kullanıcı kararı 12 Kas:  kabin büyümez ).  Avan hesabı kabini karttan okur ( aydınlatma,
#  alan denetimi ):  kartınki farklıysa hesap sayfası ile pafta ayrı kabin gösterir.
#  Kartın alanı → ( hazır asansörün alanı , ekrandaki adı ).  Boy a = derinlik, genişlik b = genişlik.
KABIN = {
    "kabin_boyu": ("kabin_derinligi", "Kabin boyu a"),
    "kabin_genisligi": ("kabin_genisligi", "Kabin genişliği b"),
}


def paket_kabini(a, ortak):
    """Bu asansörün çizimde kullanılacak kabini ( mm ) — { kabin_boyu , kabin_genisligi } ya da
    None:  bu yük / düzen için hazır asansör yok."""
    yuk = a.get("Q_elle") if sayi_mi(a.get("Q_elle")) else tablolar.tablo7_yuk(a.get("kapasite"))
    if not sayi_mi(yuk):
        return None
    t = avan_secici.paketler().get((int(yuk), evet_mi(ortak.get("mk_yok"))))
    return t and {k: float(t["asansor"][p]) for k, (p, _ad) in KABIN.items()}


def _kabin_celiskisi(a, ortak):
    """Kartın kabini hazır asansörünkinden farklıysa karta yazılacaklar ( beyan biçiminde )."""
    kabin = paket_kabini(a, ortak)
    if not kabin:
        return []
    return [
        {
            "anahtar": k,
            "kart": k,
            "etiket": ad,
            "eski": f"{a[k]:g}",
            "yeni": f"{kabin[k]:g}",
            "eski_yazi": f"{a[k]:g} mm",
            "yeni_yazi": f"{kabin[k]:g} mm",
        }
        for k, (_p, ad) in KABIN.items()
        if sayi_mi(a.get(k)) and a[k] != kabin[k]
    ]


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
    if anahtar == "kapi_genisligi":
        return f"{deger} mm"
    return tablolar.aski_orani_metni(int(deger)) if anahtar == "aski_orani" else deger


def mimari(a, ortak, sabitler=None):
    """Avan asansörü ( okunmuş kart ) + ortak panel ( + ofis standardı ) → seçicinin girdisi."""
    yuk = a.get("Q_elle") if sayi_mi(a.get("Q_elle")) else tablolar.tablo7_yuk(a.get("kapasite"))
    m = {"beyan_yuku": yuk, "beyan_hizi": a.get("V"), "mk_yok": evet_mi(ortak.get("mk_yok"))}
    m.update({k: a.get(k) for k in KART})
    if not m["mk_yok"]:
        m.update({k: ortak.get(k) for k in avan_secici.MIMARI_GENEL})
    m.update(_beyan(a, sabitler))
    m["ayar"] = kart_ayarlari(a)
    m.update(_kapi_beyani(a, sayi_mi(yuk) and avan_secici.paketler().get((int(yuk), m["mk_yok"]))))
    return m


#  Kartta çizimin elle ayarlanan ölçüleri ( ekran yazar — "girdi=değer;girdi=değer" ):  çizimde
#  tıklanan ölçünün kaynağı olan uygulama girdileri ( avan_secici.ayarlar )
AYAR_ALANI = "cizim_ayarlari"


def kart_ayarlari(a):
    """Kartın elle ayarlanan ölçüleri → { uygulamanın girdisi:  değer metni }."""
    d = {}
    for parca in str(a.get(AYAR_ALANI) or "").split(";"):
        k, _es, v = parca.partition("=")
        if k.strip() and v.strip():
            d[k.strip()] = v.strip()
    return d


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
                #  Çizimin kabini ( hazır asansörünki ) — kartın kabin kutularına
                "kabin": paket_kabini(a, g["ortak"]),
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
    #  Kartın kabini çizimin kabini değilse çizim çıkmaz ( seçici koşmadan ):  karta yazılacak
    kabin = _kabin_celiskisi(asansorler[i], g["ortak"])
    if kabin:
        return {"durum": "beyan", "beyan_turu": "kabin", "beyan": kabin, "sinama": 0, "sure": 0.0}
    m = mimari(asansorler[i], g["ortak"], g.get("sabitler"))
    r = avan_secici.sec(m)
    #  Elle ayarlanan ölçüler, ekrandaki adlarıyla ( soldaki liste — kaldırılabilir )
    r["ayarlar"] = [
        {"anahtar": k, "etiket": alanlar.ALAN[k].etiket, "deger": v, "birim": alanlar.ALAN[k].birim or ""}
        for k, v in avan_secici.ayarlar(m).items()
    ]
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
        #  Kapı trafik hesabının girdisidir:  öneri trafiğin diliyle ( tip adı ), trafiğe yazılır
        if b["anahtar"] in TRAFIKTE:
            b["yer"] = "trafik"
            if b["anahtar"] == "kat_kapisi_tipi":
                aile = avan_secici.kapi_ailesi(b["yeni"])
                b["yeni"] = b["yeni_yazi"] = next(t for t, x in KAPI_AILESI.items() if x == aile)
                b["eski_yazi"] = asansorler[i].get("kapi_tipi") or b["eski"]
    if any(b.get("yer") == "trafik" for b in r.get("beyan") or []):
        r["beyan_turu"] = "kapi"
    return r


def _sayi_yazi(x):
    """Ölçü, okunduğu gibi:  2030.0 → "2030";  kot metni aynen."""
    return x if isinstance(x, str) else f"{x:g}"


def cizimsiz_sebebi(r):
    """Çizimi çıkmayan asansörün sebebi, tek satır ( paketteki nota — 14 Kas:  not hangi
    asansörün neden çizilmediğini söylemiyordu ).  r:  secim( g , i ) sonucu."""
    durum = r["durum"]
    if durum == "eksik":
        adlar = [alanlar.ALAN[k].etiket if k in alanlar.ALAN else k for k in r.get("eksik") or []]
        return "mimari ölçü eksik:  " + ", ".join(adlar)
    if durum == "gereken":
        return "mimardan istenecek:  " + ";  ".join(
            f"{g['etiket']} {_sayi_yazi(g['eski']) if g.get('eski') not in (None, '') else '—'} → {_sayi_yazi(g['yeni'])}"
            for g in r["gereken"]
        )
    if durum == "beyan":
        yer = "trafik hesabında" if r.get("beyan_turu") == "kapi" else "avan kartında"
        return f"{yer} seçilecek:  " + ";  ".join(
            f"{b['etiket']} {b.get('eski_yazi', b['eski'])} → {b.get('yeni_yazi', b['yeni'])}"
            for b in r["beyan"]
        )
    if durum == "sigmaz":
        return "bu kuyuya asansör sığmıyor:  " + (str((r.get("nedenler") or ["sebep bulunamadı"])[0]))
    if durum == "paket_yok":
        if r.get("hiz"):
            return "bu hızda avan çizimi çıkmaz ( uygulama projesinin hız listesinde yok )"
        return "bu kapasite için hazır asansör yok"
    if durum == "uygun":
        return "çizim kurulamadı"
    return str(r.get("hata") or "çizim kurulamadı")


def istendi(a):
    """Bu kartta çizim için bir şey girilmiş mi ( ISTEK )."""
    return any(a.get(k) not in (None, "") for k in ISTEK)


def paket_cizimleri(g, proje_adi, adlar):
    """Paketin çizimleri:  ( [ çizim girdisi — avan kipinde ] , [ çizimi olmayan
    asansörler:  ( ad , sebep ) ] ).  adlar:  asansörlerin paftadaki adları ( sırayla ).

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
            elif sum(1 for x in g["asansorler"] if x is not None) > 1:
                #  Öbür asansörler çizilemese de paftada bu asansörün adı yazar ( cizim/pafta.bloklar )
                cg["proje"]["cok_asansorlu"] = True
        if cg is None:
            eksik.append((adlar[i], cizimsiz_sebebi(r)))
        else:
            gler.append(cg)
    return gler, eksik
