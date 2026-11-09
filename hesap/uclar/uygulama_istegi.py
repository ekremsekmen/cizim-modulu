"""UYGULAMA FORMUNUN İSTEĞİ — formun alan sözleşmesi ve gelen isteğin
çözümü ( ham metinler → hesabın ve çizimin girdisi ).

Hem uygulama uçları ( uygulama_uclari ) hem çizim uçları ( cizim_uclari )
kullanır.  Eskiden uygulama_uclari'nın içindeydi;  cizim_uclari onu
fonksiyon içinden import ediyor, uygulama_uclari de cizim_uclari'nı import
ediyordu ( iki uç modülü birbirine dolanmıştı ).

TEK KAPI:  isteğin değerleri yalnız burada denetlenir ( asansor_girdileri ) —
tür, okunuş, seçenek, tam sayı, alt sınır, tavan.  Geçersiz girdide uç
GecersizGirdi'nin iletilerini döndürür, hesap da çizim de başlamaz.
"""

from cizim import katlar
from cizim import kopru
from motor.ortak.adimlar import evet_mi
from motor.uygulama import mukavemet_girdi
from motor.uygulama import mukavemet_tablolari
from motor.uygulama import tablolar_gorunum
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from motor.uygulama import uygulama_sabitleri
from tasarim import gorunum
from tasarim.alanlar import ALAN, ALANLAR, CIZ, DURAK_KOTLARI, ELK, KOT, KUYU_ORTAK, MUK
from uclar.uc_ortak import (
    _BELIRSIZ,
    _RED,
    _belirsiz_hata,
    _bos_mu,
    _sabitler_coz,
    _sayi,
    _sayi_oku,
    belirsiz_sayi_mi,
)


def alanlar():
    """Formun kendini üretmesi için girdi sözleşmesi.

    Mukavemet alanları + elektrik hesaplarının mukavemette KARŞILIĞI OLMAYAN
    alanları.  Ortak girdiler burada BİR KEZ geçer ( bkz. uygulama_girdi ).
    """
    veri = uygulama_girdisi.arayuz_alanlari()
    veri["ortak_kopru"] = [
        {"mukavemet": ad, "anahtar": a, "avan": av} for ad, a, av in uygulama_girdisi.ORTAK_KOPRU
    ]
    #  UYGULAMANIN KENDİ OFİS STANDARDI  —  avanınkinden ayrıdır.
    #  Ekran bu listeden kurulur;  avanın MMO/697 kuvvet sabitleri burada
    #  YOKTUR, uygulamanın mukavemet kabulleri ( σem · k1 · paylar ) ise
    #  yalnız burada vardır.
    veri["sabitler"] = {
        "varsayilan": uygulama_sabitleri.VARSAYILAN,
        "metin": list(uygulama_sabitleri.METIN),
        "gruplar": [
            {"baslik": b, "aciklama": a, "alanlar": list(al)} for b, a, al in uygulama_sabitleri.GRUPLAR
        ],
        "etiket": {k: list(v) for k, v in uygulama_sabitleri.ETIKET.items()},
    }
    #  Tablolar sekmesi:  uygulamanın kendi tabloları  ( ray · NPU · halat ·
    #  ω · kabin alanı … ).  Bunlar bugüne kadar yalnız motorun içindeydi,
    #  ekranda görünmüyordu — uygulama yapan mühendis kullandığı ray
    #  tablosuna bakamıyordu.
    veri["tablolar"] = tablolar_gorunum.arayuz_tablolari()
    veri["asansor_azami"] = uygulama_hesabi.ASANSOR_AZAMI
    #  BOŞ METNİN ANLAMI OLAN ALANLAR.  Gönderilmeyen alan varsayılandır
    #  ( boş kabin kütlesinde 700 );  BOŞ METİN ise "tablodan al" demektir
    #  ( mukavemet_girdi.tamamla:  beyan yükünün ofis tablosu değeri ).  Ön yüz
    #  bu alanlarda boşu boş olarak gönderir — beyan yükü değişince de, eski
    #  dosyadaki boş kutu da tablo değerini verir.  Liste
    #  testler/test_on_yuz_sozlesmesi.py taramasıyla eşit tutulur.
    veri["bos_tablodan"] = list(BOS_TABLODAN)
    veri["eski_onay"] = {k: list(v) for k, v in ESKI_ONAY.items()}
    return veri


BOS_TABLODAN = ("kabin_agirligi",)

#  ESKİDEN ONAY KUTUSU OLAN SEÇİMLER:  ( işaretsiz , işaretli ).  Eski .uygulama
#  dosyası bu alanda true / false ( "EVET" ) taşır;  kapı onu seçime çevirir
#  ( _secim_oku → makine_yuk_yolu ).  Ön yüz dosyayı açarken aynı seçeneği alır —
#  24 Eki:  tanımayıp varsayılana döndürüyordu, işaretsiz kutu ( bina yapısına )
#  sessizce "Kılavuz raylara" oluyordu.  Okuyuşun eşitliği:  test_on_yuz_denetimi.
ESKI_ONAY = {"makine_raya_biniyor": mukavemet_tablolari.MAKINE_YUK_YOLU}


class GecersizGirdi(ValueError):
    """İstek kapıdan geçmedi:  hatalar alan alan, Türkçe ve alanın adıyla.
    Uçlar bunları olduğu gibi döndürür;  hiçbir hesap ya da çizim işi başlamaz."""

    def __init__(self, hatalar):
        super().__init__("  ·  ".join(hatalar))
        self.hatalar = list(hatalar)


def mukavemet_girdisi(veri: dict):
    """Eski tek asansörlük isteğin ( "girdiler" ) çözümü — kapının hatalarını
    yükseltmez ( okunamayan yazım _BELIRSIZ / _RED'de kalır )."""
    _BELIRSIZ.clear()
    _RED.clear()
    girdiler = (veri or {}).get("girdiler")
    return _girdi_coz(girdiler, veri, uygulanmayan((girdiler or {}) if isinstance(girdiler, dict) else {}))


def uygulanmayan(ham):
    """Ham girdideki makine yerleşimine göre hesaba girmeyen alanlar.

    Kutu gönderilmemişse sözleşmenin varsayılanı ( makine dairesiz ) geçerlidir.
    """
    mk_yok = evet_mi(ham["mk_yok"]) if "mk_yok" in ham else uygulama_girdisi.EK_ALAN["mk_yok"][5]
    return uygulama_girdisi.uygulanmayan_alanlar(mk_yok)


class _Kisa:
    """İletide uzun liste / sözlük yerine kısaltılmış yazımı."""

    def __init__(self, x):
        self.r = repr(x)

    def __repr__(self):
        return self.r if len(self.r) <= 40 else self.r[:37] + "…"

    __str__ = __repr__


def _sayi_turu(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _secim_oku(a, ham):
    """Seçim kutusu:  listedeki değer ( birebir ya da sayısal eşleşme — arayüz
    "1,6" yollar ) ya da hata.  Mantıksal, liste, sözlük hiçbir seçeneğe uymaz
    ( 21 Eki:  True == 1 askı oranını sessizce 1:1 yapıyordu )."""
    if a.anahtar == "makine_raya_biniyor" and isinstance(ham, (bool, str)):
        #  Eski onay kutusu ( True / "EVET" ) — eski .uygulama dosyaları
        return mukavemet_tablolari.makine_yuk_yolu(ham), None
    if not (isinstance(ham, str) or _sayi_turu(ham)):
        return None, mukavemet_girdi.secim_iletisi(a.anahtar, _Kisa(ham))
    if belirsiz_sayi_mi(ham):
        _BELIRSIZ.append(f"{a.etiket} = {ham.strip()}")
        return None, None
    sayi = _sayi(ham)
    for o in a.secenekler:
        if o == ham or (_sayi_turu(o) and sayi is not None and abs(o - sayi) < 1e-9):
            return o, None
    return None, mukavemet_girdi.secim_iletisi(a.anahtar, ham)


def _oku(a, ham):
    """Bir kutunun ham değeri → ( değer , hata ):  tür, okunuş, seçenek, tam
    sayı, alt sınır, tavan ( mukavemet_girdi.alan_hatasi — ön yüzün kural
    tablosu ).  Okunamayan / belirsiz yazım _RED / _BELIRSIZ'e gider ( bugünkü
    toplu ileti )."""
    if a.tur == "onay":
        if ham is None or isinstance(ham, (bool, str)) or _sayi_turu(ham):
            return evet_mi(ham), None
        return None, f"{a.etiket}: işaretli ya da işaretsiz olmalı ( {_Kisa(ham)!r} girildi )."
    if _bos_mu(ham):
        return None, None
    #  KOT YAZIMI ( cizim/katlar ):  metre, işaretli, mm'ye kadar, "−" ve "±";
    #  okunamayanın sebebi alanın kendi iletisinde ( sayının toplu iletisi
    #  "binlik ayracı mı" der, kotta nokta da virgül de ondalıktır )
    if a.tur == "sayi" and a.kip == KOT:
        mm, ileti = katlar.kot_oku(ham)
        return (None, f"{a.etiket}:  {ileti}") if ileti else (mm / 1000.0, None)
    if a.anahtar == DURAK_KOTLARI:
        _kotlar, iletiler = katlar.kotlari_oku(ham)
        return (None, katlar.iletiler_metni(a.etiket, iletiler)) if iletiler else (ham, None)
    if a.tur == "sayi":
        d = _sayi_oku(ham, a.etiket)
        return d, (None if d is None else mukavemet_girdi.alan_hatasi(a.anahtar, d))
    if a.tur == "secim":
        return _secim_oku(a, ham)
    #  metin
    if isinstance(ham, str) or (_sayi_turu(ham) and _sayi(ham) is not None):
        return str(ham), None
    return None, f"{a.etiket}: yazı olmalı ( {_Kisa(ham)!r} girildi )."


#  Okunan alanlar:  FORMDA KUTUSU OLANLAR ( elektrik · çizim · mukavemet ).
#  Çizimden ya da hesaptan gelen alan istekte olsa da okunmaz — eski proje
#  dosyalarında saptırma kasnağı çapı, kaide, ray sayısı yazılı olabilir.
_OKUNAN = tuple(
    a for s in (ELK, CIZ, MUK) for a in ALANLAR if a.sozlesme == s and a.formda and a.tur != "hesap"
)


def _girdi_coz(v, veri, atla=frozenset(), hatalar=None):
    """Tek asansörün ham alanlarını okur ve DENETLER ( _oku ):  değerler
    türünde, hatalar ( anahtar , ileti ) olarak ``hatalar``a.

    ``atla``:  makine yerleşimine göre hesaba girmeyen ( ekranda gizli )
    alanlar.  OKUNMAZLAR — içlerinde kalmış "4.000" ya da "-3" projeyi
    durdurmaz, çünkü kullanıcı gizli alanı göremez ve düzeltemez.  Formda
    kutusu olmayan alan da okunmaz ( eski proje dosyaları ).  Kat girişinin
    öbür kipinin alanları da böyle okunmaz ( asansörün kendi kipi — kotla
    girişte ölçüden türeyenler, ölçüyle girişte kotlar:  tek kaynak ).

    _BELIRSIZ / _RED KASITLI OLARAK TEMİZLENMEZ:  çoklu projede her asansör
    ayrı çağrılır ve belirsiz girdiler hepsinden TOPLANMALIDIR — temizlik
    çağıranın işidir ( bkz. asansor_girdileri ).
    """
    v = v if isinstance(v, dict) else {}
    atla = set(atla) | gorunum.kip_disi(katlar.kot_kipi(v))
    g = {}
    for a in _OKUNAN:
        if a.anahtar not in v:
            continue
        if a.anahtar in atla:
            g[a.anahtar] = None
            continue
        g[a.anahtar], hata = _oku(a, v[a.anahtar])
        if hata and hatalar is not None:
            hatalar.append((a.anahtar, hata))
    #  Ofis standardı ( Sabitler sekmesi ) — elektrik ve topraklama hesapları
    #  buradan besleniyor;  avan tarafındaki ile aynı biçimde alınır.
    g["_ofis"] = _sabitler_coz(
        (veri or {}).get("sabitler"),
        uygulama_sabitleri.METIN,
        #  Değer ofis standardındadır ( proje formunda aranmasın ) — avandaki gibi
        lambda k: f"Ofis standardı · {uygulama_sabitleri.ETIKET.get(k, (k,))[0]}",
    )
    return g


#  Makine dairesinin çizim ölçüleri de binaya aittir.
PROJE_GENELI_ALANLAR = uygulama_girdisi.PROJE_GENELI_ALANLAR + kopru.PROJE_GENELI


def asansor_girdileri(veri):
    """TEK KAPI:  arayüzden gelen isteği ( 1 - 4 asansör ) çözer ve denetler.
    Uygulamanın bütün uçları isteği yalnız buradan okur.

    Döner:  ( [ asansör girdi sözlükleri ] , ortak ) — her değer türünde,
    tek alanın kuralına uyar ( _oku ).  Geçersiz girdide GecersizGirdi:
    okunamayan / belirsiz yazım ( bugünkü toplu ileti ), alan alan kural
    dışı değerler ( çok asansörlüde asansörün adıyla ), Sabitler sekmesinin
    aralık dışı değerleri.  21 Eki:  hesap girdiyi denetlemeden çizimi kurup
    değer türetiyordu ( tamamla → kopru.cizimden ) — kapı genişliği 10¹²
    belleği bitirdi, True / liste / sözlük çökertti.  Alanlar arası ve
    mühendislik kuralları motorda kalır.

    GERİYE DÖNÜK:  "asansorler" yoksa eski tek asansörlük "girdiler" alanı
    kullanılır — kayıtlı eski projeler ve eski istekler çalışmaya devam eder.
    """
    _BELIRSIZ.clear()
    _RED.clear()
    veri = veri or {}
    ham = veri.get("asansorler")
    if not isinstance(ham, list) or not ham:
        ham = [veri.get("girdiler")]
    ham = [x for x in ham if isinstance(x, dict)][: uygulama_hesabi.ASANSOR_AZAMI] or [{}]

    #  Proje geneli alanlar:  ayrı gönderilmişse oradan, yoksa İLK asansörün
    #  girdisinden ( eski tek asansörlük istekler bunları orada taşıyor ).
    pg_ham = veri.get("proje_geneli")
    if isinstance(pg_ham, dict):
        #  Ayrı gönderildiyse asansörün İÇİNDEKİ kopyalar okunmaz:  eski bir
        #  proje dosyasından kalmış olabilirler, ekranda görünmezler ve motor
        #  zaten ortaktakini kullanır ( bkz. hesap.hesapla_coklu ).
        ham = [{k: v for k, v in x.items() if k not in PROJE_GENELI_ALANLAR} for x in ham]
    else:
        pg_ham = {k: ham[0][k] for k in PROJE_GENELI_ALANLAR if k in ham[0]}
    #  Makine yerleşimi proje genelidir:  gizli alanlar bütün asansörlerde aynı.
    #  KUYU DÜZENİ de ( tasarim/alanlar ):  tek kuyunun alanları yalnız iki asansörlü
    #  tek kuyuda okunur.  Tek kuyuda kuyunun ortak girdileri iki asansörde aynıdır:
    #  ön yüz ikisine birden yazar;  kapı da 1. asansörünkini öbürüne yazar ( eski
    #  dosya, elle kurulan istek — iki asansör ayrı kuyu çizilmesin ).
    atla = set(uygulanmayan(pg_ham)) | gorunum.tek_kuyu_disi(pg_ham, len(ham))
    if gorunum.tek_kuyu_mu(pg_ham, len(ham)):
        ortak_ham = {k: ham[0][k] for k in KUYU_ORTAK if k in ham[0]}
        ham[1] = {**{k: v for k, v in ham[1].items() if k not in KUYU_ORTAK}, **ortak_ham}
    hatalar = []
    ortak = {
        k: v
        for k, v in _girdi_coz(pg_ham, veri, atla, hatalar).items()
        if k in PROJE_GENELI_ALANLAR or k == "_ofis"
    }
    hatalar = [h for k, h in hatalar if k in PROJE_GENELI_ALANLAR]
    asansorler = []
    for i, x in enumerate(ham, 1):
        h = []
        asansorler.append(_girdi_coz(x, veri, atla, h))
        #  Binanın alanı ( ilk asansörde taşınıyorsa ) yukarıda bir kez söylendi
        h = [m for k, m in h if k not in PROJE_GENELI_ALANLAR]
        ad = str(x.get("asansor_adi") or "").strip() or f"{i} nolu asansör"
        hatalar += [f"{ad}:  {m}" for m in h] if len(ham) > 1 else h
    hatalar += uygulama_sabitleri.ofis_hatalari(ortak["_ofis"])
    belirsiz = _belirsiz_hata()
    if belirsiz or hatalar:
        raise GecersizGirdi(([belirsiz] if belirsiz else []) + list(dict.fromkeys(hatalar)))
    _tek_kuyu_bolmeleri(asansorler, ortak)
    return asansorler, ortak


def _tek_kuyu_bolmeleri(asansorler, ortak):
    """TEK KUYUDA iki asansör kuyunun iki bölmesinin genişliğini bilir ( soldan
    sağa — "Soldaki asansör" ):  makine dairesinin yeri kuyunun sol iç köşesine
    göredir, köprü sağdaki asansörde soldaki bölme + kiriş kadar kaydırır
    ( kopru._makine_dairesi_girdisi ).  Boş bölme varsayılan genişliğindedir ( 9 Kas:
    boşken yazılmıyordu, makine dairesi — "boş = varsayılan" kuralına aykırı — başka
    yere kuruluyordu )."""
    if not gorunum.tek_kuyu_mu(ortak, len(asansorler)):
        return
    sol = 0 if ortak.get("soldaki_asansor") in (None, 1) else 1
    varsayilan = ALAN["kuyu_genisligi"].varsayilan
    G = [
        varsayilan if a.get("kuyu_genisligi") is None else a["kuyu_genisligi"]
        for a in (asansorler[sol], asansorler[1 - sol])
    ]
    for a in asansorler:
        a["_kuyu_bolmeleri"] = G
