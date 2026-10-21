"""UYGULAMA FORMUNUN İSTEĞİ — formun alan sözleşmesi ve gelen isteğin
çözümü ( ham metinler → hesabın ve çizimin girdisi ).

Hem uygulama uçları ( uygulama_uclari ) hem çizim uçları ( cizim_uclari )
kullanır.  Eskiden uygulama_uclari'nın içindeydi;  cizim_uclari onu
fonksiyon içinden import ediyor, uygulama_uclari de cizim_uclari'nı import
ediyordu ( iki uç modülü birbirine dolanmıştı ).
"""

from cizim import kopru
from motor.ortak.adimlar import evet_mi
from motor.uygulama import mukavemet_girdi
from motor.uygulama import tablolar_gorunum
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_hesabi
from motor.uygulama import uygulama_sabitleri
from tasarim import gorunum
from uclar.uc_ortak import _BELIRSIZ, _RED, _sabitler_coz, _sayi, _sayi_oku, belirsiz_sayi_mi


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
    return veri


BOS_TABLODAN = ("kabin_agirligi",)


def mukavemet_girdisi(veri: dict):
    """Arayüzden gelen ham metinleri sözleşmenin beklediği türlere çevirir.

    Seçim alanları LİSTEDEKİ değere eşlenir:  arayüz her şeyi metin olarak
    yollar, oysa seçeneklerin çoğu sayıdır ( 800 · 1,6 · 370 ).  Eşleme
    burada yapılmazsa motorun doğrulaması "geçersiz seçim" der.
    """
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


def _secim_hami(ham):
    """Seçim / metin kutusunun ham değeri:  metin, sayı ya da boş.  Başka tür
    ( mantıksal, liste, sözlük — yalnız API'den gelir;  form göndermez ) metne
    çevrilir:  hiçbir seçeneğe uymaz, "geçersiz seçim" iletisiyle reddedilir.
    21 Eki uç tarama:  True seçenek 1 sanılıyordu ( True == 1 — askı oranı
    sessizce 1:1, beyan hızında tampon hesabı çöküyordu ), liste / sözlük
    sözlük anahtarı olunca ( makine tipi ) hesap ve çizim çöküyordu."""
    if ham is None or (isinstance(ham, (str, int, float)) and not isinstance(ham, bool)):
        return ham
    return str(ham)


def _girdi_coz(v, veri, atla=frozenset()):
    """Tek asansörün ham alanlarını türlerine çevirir.

    ``atla``:  makine yerleşimine göre hesaba girmeyen ( ekranda gizli )
    alanlar.  OKUNMAZLAR — içlerinde kalmış "4.000" ya da "-3" projeyi
    durdurmaz, çünkü kullanıcı gizli alanı göremez ve düzeltemez.

    _BELIRSIZ / _RED KASITLI OLARAK TEMİZLENMEZ:  çoklu projede her asansör
    ayrı çağrılır ve belirsiz girdiler hepsinden TOPLANMALIDIR — temizlik
    çağıranın işidir ( bkz. asansor_girdileri ).
    """
    v = v if isinstance(v, dict) else {}
    g = {}
    #  Elektrik hesaplarının ek alanları  ( kuyu genişliği · kesitler ·
    #  temel ölçüleri · makine dairesi ).  Onay kutusu mantıksal, geri kalanı
    #  serbest sayıdır;  boş bırakılabilir — hesap eksikliği kendisi bildirir.
    for anahtar, _et, _b2, tur2, _s2, _v2 in uygulama_girdisi.EK_ALANLAR:
        if anahtar not in v or anahtar not in _FORMDA:
            continue
        if anahtar in atla:
            g[anahtar] = None
            continue
        ham = v[anahtar]
        g[anahtar] = evet_mi(ham) if tur2 == "onay" else _sayi_oku(ham, _et)
    #  Çizim alanları:  sayılar okunur ( okunamayan yazım reddedilir ),
    #  seçimler olduğu gibi;  boş alan None — köprü kuralını uygular.
    for anahtar, _et, _b3, tur3, _s3, _v3, _gel, _bil in kopru.ALANLAR:
        if anahtar not in v or anahtar not in _FORMDA:
            continue
        if anahtar in atla:
            g[anahtar] = None
            continue
        ham = v[anahtar] if tur3 == "sayi" else _secim_hami(v[anahtar])
        g[anahtar] = _sayi_oku(ham, _et) if tur3 == "sayi" else (ham if str(ham).strip() != "" else None)
    for anahtar, etiket, _b, tur, secenekler, _var in mukavemet_girdi.ALANLAR:
        if tur == "hesap" or anahtar not in v or anahtar not in _FORMDA:
            continue
        if anahtar in atla:
            g[anahtar] = None
            continue
        ham = v[anahtar] if tur == "sayi" else _secim_hami(v[anahtar])
        if secenekler is None:
            #  Serbest sayı:  okunamayan yazım boş SAYILMAZ, sebebiyle
            #  reddedilir ( boş kabin kütlesi gibi tablodan doldurulan bir
            #  alanda "abc" eskiden tablo değerine dönüşürdü ).
            g[anahtar] = _sayi_oku(ham, etiket) if tur == "sayi" else ham
            continue
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{etiket} = {str(ham).strip()}")
        #  Seçenek listesi:  önce birebir, sonra sayısal eşleşme aranır
        if ham in secenekler:
            g[anahtar] = ham
            continue
        sayi = _sayi(ham)
        esles = next(
            (
                o
                for o in secenekler
                if isinstance(o, (int, float))
                and not isinstance(o, bool)
                and sayi is not None
                and abs(o - sayi) < 1e-9
            ),
            None,
        )
        g[anahtar] = esles if esles is not None else (ham if str(ham).strip() != "" else None)
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
#  FORMDA KUTUSU OLAN alanlar okunur ( tasarım şeması ).  Çizimden ya da
#  hesaptan gelen alan istekte olsa da okunmaz — eski proje dosyalarında
#  saptırma kasnağı çapı, kaide, ray sayısı yazılı olabilir.
_FORMDA = frozenset(gorunum.anahtarlar(formda=True))


def asansor_girdileri(veri):
    """Arayüzden gelen isteği ( 1 - 4 asansör ) çözer.

    Döner:  ( [ asansör girdi sözlükleri ] , ortak )

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
    atla = uygulanmayan(pg_ham)
    ortak = {
        k: v for k, v in _girdi_coz(pg_ham, veri, atla).items() if k in PROJE_GENELI_ALANLAR or k == "_ofis"
    }
    return [_girdi_coz(x, veri, atla) for x in ham], ortak
