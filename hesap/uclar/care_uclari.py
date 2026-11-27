# -*- coding: utf-8 -*-
"""
ÇARE — sorunun sayılı, doğrulanmış çaresi  ( 19 Eki;  çare planının 3. adımı )

Ekran sorunu ve parçasını gösteriyordu;  mühendis "ne yapmalıyım" sorusunun
cevabını arıyordu.  Çare bulucu iki yoldan aday üretir:

  TÜREV            Sorunun açığı ( sorun.Sorun.fark — fark ≥ 0 iken sorun
                   yok ) çizim izli sayıyla kurulunca her girdiye türeviyle
                   gelir ( cizim_uclari.izli_sorunlar ).  Açığı kapatan değer:
                   girdi − fark / eğim, bütün mm'ye güvenli yönde yuvarlanır.
                   Aynı kutuya bağlı birkaç sorun varsa en uzaktaki değer
                   hepsine birden aday olur ( kuyu dibi 1300 → 1415:  dört sorun ).
  SEÇİM            Türevin göremediği seçimler ( kapı tipi, sığınma tipi, askı
                   düzeni, ağırlığın yeri … ):  sorunun parçasına göre ilgili
                   seçim kutusunun öbür seçenekleri denenir ( SECIMLER — gerçek
                   projelerde düzeltmesiz kalanların çoğu buydu:  "kabin
                   tavanında çömelme tipi sığınma alanına yer yok" ).
  TARAMA           AÇIĞI BİLİNMEYEN sorun ( sayı açığı yok:  "merdivene yer yok" ) türev ve
                   seçimden sonra hâlâ çaresizse bina ölçüleri taranır ( 27 Kas — seçici
                   doğruluk planı Adım 2 ):  sorunun çizimine göre ölçüler ( TARAMA_OLCULERI )
                   büyüyen adımlarla ( TARAMA_ADIMLARI ) denenir, ilk gideren ile son
                   gidermeyen arası ikiye bölünür ( TARAMA_COZUNURLUK ).  Her aday tam
                   sınamadan geçer.  41 / 97 sorun yapımı açık taşımıyordu;  dar kuyuda seçici
                   öbür yerleşime kaçıp 130 mm fazla istiyordu ( 800 kg 1800 → 1980 ).
  SON DEĞİŞİKLİK   Sorun son değişiklikle çıktıysa ( ön yüz son temiz girdiyi
                   gönderir ) değişen kutuda ikiye bölmeyle sınır aranır:
                   "kuyu genişliği 2230'a kadar bu sorun yok".  Türevin
                   göremediği sıçramalar ( korkuluk 500 mm boşlukta 0,70 →
                   1,10 m olur ) burada yakalanır.

HİÇBİR ADAY TAHMİNLE GÖSTERİLMEZ:  her biri uygulanır, hesap ve bütün
çizimler yeniden kurulur;  sorunu gidermeyen, yeni sorun doğuran ya da
hesabı kötüleştiren ( hesap durur, "uygun değil" bölüm artar ) aday atılır.
Türevin tahmini tutmazsa ( kırık nokta, eşitlikte kalan ) adım büyütülerek
birkaç kez daha denenir.

Sıra ( kullanıcı kararı 19 Eki ):  son değişikliğin sınırı → aynı anda en çok
sorunu gideren → en küçük değişiklik;  bina ölçüleri ( kuyu, son kat, kuyu
dibi, duvarlar, makine dairesi ) en sonda ve işaretli.  Ürünün özelliği olan
ya da geometriyle ilgisi olmayan alanlar ( tampon ezilmesi, yapı sehimi … )
çare sayılmaz.

BÜTÇE SINAMA SAYISIDIR, SAAT DEĞİL ( Butce;  20 Eki ):  aynı proje her
bilgisayarda, her seferinde aynı çareleri alır.  Saat yalnız güvenlik
sınırıdır;  ona ya da sayıya takılan arama yanıtta "tamamlandi: false" der.
"""

import copy
import json
import logging
import math
import re
import threading
import time

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from temel import sayi_mi
from cizim import asamalar
from cizim import istek_onbellegi
from cizim import izli
from cizim import sorun
from motor.uygulama import uygulama_hesabi
from tasarim import gorunum
from tasarim.alanlar import KUYU_ORTAK
from uclar import cizim_uclari
from uclar import uc_ortak
from uclar import uygulama_istegi
from uclar.uc_ortak import _sayi, hata_iletisi, hata_kaydi

log = logging.getLogger(__name__)
router = APIRouter()

#  Bina ölçüleri:  çare olabilir ama en sonda ve işaretli ( mevcut binada değişmez )
BINA = frozenset(
    (
        "kuyu_genisligi",
        "kuyu_derinligi",
        "son_kat_yuksekligi",
        "kuyu_dibi",
        "kuyu_duvar_kalinligi",
        "kuyu_duvar_on",
        "kuyu_duvar_arka",
        "kuyu_duvar_sol",
        "kuyu_duvar_sag",
        "mk_uzunluk",
        "mk_genislik",
        "md_yukseklik",
        "md_duvar",
        "tabliye_yuksekligi",
        "seyir_mesafesi",
        "durak_adedi",
        #  Kotla giriş:  kuyunun ve makine dairesinin kotları ve tavan döşemesi de
        #  binanındır.  Durak kotları mimariden gelir, metin alanıdır — önerilmez.
        "kuyu_dibi_kotu",
        "kuyu_tavani_kotu",
        "md_zemini_kotu",
        "tavan_dosemesi",
    )
)
#  Çare sayılmayanlar:  ürünün özelliği ( tamponun stroku ) ya da geometriyle ilgisiz
DISI = frozenset(
    (
        "kabin_tampon_ezilme",
        "agirlik_tampon_ezilme",
        "yapi_sehim_x",
        "yapi_sehim_y",
        "kabin_agirlik_merkezi_x",
        "kabin_agirlik_merkezi_y",
        "paten_balata_boyu",
        "kapi_mekanizma_payi",
    )
)
#  Düzeltici olabilen birimler ve adımları:  değer bu adıma güvenli yönde yuvarlanır
#  ( seyir mesafesi m — 1 cm;  durak adedi — tam sayı )
ADIM = {"mm": 1.0, "m": 0.01, "adet": 1.0}
#  Bir istekte en çok sınanan türev adayı
AZAMI_ADAY = 16
#  BİR İSTEĞİN BÜTÇESİ — SINAMA SAYISI ( her sınama hesap ve çizimin yeniden
#  kurulmasıdır, girdi_durumu ).  Eskiden 6 sn'lik duvar saatiydi:  arama makinenin o
#  anki yüküne göre farklı yerde kesiliyor, aynı proje farklı çareler alıyordu
#  ( ölçüldü 20 Eki:  makine daireli örnekte 6 sn'de sınır 4.310 ve tek çare —
#  kesilmeden 4.303 ve dört çare;  yük altında test_care ara sıra düşüyordu ).
#  Büyük çözücülerin iş sınırı gibi ( Gurobi WorkLimit, CPLEX DetTimeLimit ).
#  Test vakalarında en çok 29 sınama:  bütçe onun iki katı.
AZAMI_SINAMA = 60
#  GÜVENLİK SÜRESİ ( sn ):  yalnız bir isteğin sunucuyu kilitlememesi için;
#  normal istekte ulaşılmaz ( en uzun vaka 13,5 sn ).  Ulaşılırsa yanıt söyler.
GUVENLIK_SURESI = 60.0
#  Türevin tahmini tutmazsa adımın çarpanları ( 0:  1 mm daha )
YENIDEN = (0, 1.25, 1.5, 2.0)
#  Sorun başına gösterilen çare
SORUN_BASINA = 4
#  BİNA ÖLÇÜSÜ TARAMASI ( _taramayla — açığı bilinmeyen çaresiz sorunlar ):  sorunun çizimi
#  ( sorun.Sorun.cizim ) → denenen bina ölçüleri, sırayla.  Kot / uzunluk girişinin ikisi de yazılı:
#  formda görünmeyen ( gizli ) atlanır.  Çizimi burada olmayan sorun ( kasnak düzeni, kat adları,
#  giriş — ürün / girdi sorunu ) bina ölçüsüyle çözülmez:  taranmaz.
_PLAN = ("kuyu_genisligi", "kuyu_derinligi")
TARAMA_OLCULERI = {
    "kuyu_plani": _PLAN,
    "kuyu_dibi": _PLAN,
    "kuyu_kesiti_on": _PLAN,
    "kuyu_kesiti_yan": ("kuyu_dibi_kotu", "kuyu_dibi"),
    "kuyu_ustu": ("kuyu_tavani_kotu", "son_kat_yuksekligi", *_PLAN),
    "kabin_ustu": ("kuyu_tavani_kotu", "son_kat_yuksekligi", *_PLAN),
    "makine_dairesi": ("mk_uzunluk", "mk_genislik", "md_yukseklik", *_PLAN),
    "delik_plani": ("mk_uzunluk", "mk_genislik", *_PLAN),
}
#  Büyüme yönü:  kuyu dibi kotu AŞAĞI iner ( daha derin );  öbürleri artar
TARAMA_YONU = {"kuyu_dibi_kotu": -1.0}
#  Büyüyen adımlar ( mm;  metre birimli kotta / 1000 ) ve ikiye bölmenin çözünürlüğü ( seçicinin
#  küçültme adımı — avan_secici.KUCULTME_ADIMI — ile aynı:  10 mm, kotta 1 cm )
TARAMA_ADIMLARI = (50, 100, 200, 400, 800)
TARAMA_COZUNURLUK = 10
#  Bir sorunun taramasına en çok bu kadar sınama ( bütçe ayrıca:  Butce )
TARAMA_SORUN_SINAMA = 14
#  SEÇİM DÜZELTMELERİ:  sorunun parçasına göre denenen seçim kutuları ( sığınma
#  tipleri ayrıca — sorunun çizimine göre kabin üstü ya da kuyu dibi )
SECIMLER = {
    "kat_kapisi_tipi": frozenset(
        (
            "kanat_cebi",
            "kabin_kanat_cebi",
            "kat_kanadi",
            "kabin_kanadi",
            "kabin_kapisi_operatoru",
            "kapi_boslugu",
        )
    ),
    "aski_duzeni": frozenset(
        ("kabin_kasnak", "kabin_kasnak_ucu", "kabin_kasnagi", "kabin_kasnak_capraz", "aski_nokta", "halat")
    ),
    "agirlik_yeri": frozenset(("agirlik_blok", "agirlik", "ara_kiris")),
    "regulator_yani": frozenset(
        (
            "gergi",
            "gergi_kol",
            "gergi_kolu",
            "gergi_agirlik",
            "gergi_agirligi",
            "gergi_kontak",
            "gergi_kontagi",
        )
        + ("gergi_plaka", "gergi_plakasi", "regulator", "regulator_kasnak")
    ),
    "md_pano_duvar": frozenset(("kumanda_panosu", "calisma_alani")),
    "md_kapi_duvar": frozenset(("oda_kapisi",)),
    "acil_pano_yani": frozenset(("acil_pano",)),
    "kapi_montaji": frozenset(("kabin_esigi", "kat_esigi", "kapi_kasasi")),
    #  Arkadaki ağırlıkla makine dairesizde makine duvardan duvara kirişe oturur ( yük bina yapısına ):
    #  ileti söylüyordu, öneri gelmiyordu ( 27 Kas çare taraması:  6 çaresiz sorun )
    "makine_raya_biniyor": frozenset(("makine_sasesi",)),
    #  Kuyu – kabin eşiği 0,15 m'yi aşınca:  mekanik kilitli kabin kapısı ( m.5.2.5.3.1 c )
    "kabin_kapisi_kilidi": frozenset(("kabin_esigi",)),
}
#  ARAMANIN AŞAMALARI ( 20 Kas — arayüz taslağı B5:  arama 1,5 – 3,7 sn, en uzun vaka 13,5 sn;  ekranda
#  yalnız küçük "Aranıyor…" vardı ):  coz'un adımları — ölçüldü 1275 MD kuyu 2100:  sınır 0,39,
#  türev 0,37, seçim 0,92 sn;  her sınama ( hesap + çizim ) sayılır ( Butce.durum )
ASAMALAR = {
    "okuma": ("Sorunlar okunuyor", "Sorunlar okundu"),
    "sinir": ("Son değişikliğin sınırı aranıyor", "Son değişikliğin sınırı arandı"),
    "turev": ("Türevin önerdiği değerler sınanıyor", "Türevin önerdiği değerler sınandı"),
    "secim": ("Seçimler deneniyor", "Seçimler denendi"),
    "tarama": ("Bina ölçüleri taranıyor", "Bina ölçüleri tarandı"),
}
#  Sayı seçenekli seçim ( kapı genişliği ):  yalnız komşu seçenekler
KOMSU_SECIM = {"kapi_genisligi": SECIMLER["kat_kapisi_tipi"]}
#  Bir istekte en çok sınanan seçim
AZAMI_SECIM = 12


def _kisa_etiket(a):
    """Alanın ekrandaki adı, kısaltması olmadan ( "Kuyu genişliği  ( KG )" → "Kuyu genişliği" )."""
    return str(a.get("etiket") or a.get("anahtar") or "").split("  (")[0]


def kimlik(metin):
    """Sorunun kimliği:  ilk iki noktaya kadarki kısmı, sayılar atılmış.  Değer
    değişince metnin sonu değişebilir ( "üst pateni tepesi 3599,6" →
    "çerçevesi tepesi 3610" ) — aynı sorundur."""
    return re.sub(r"-?\d+(?:[.,]\d+)?", "#", str(metin).split(":", 1)[0]).strip()


def girdi_durumu(veri, i):
    """Bir girdinin hükmü:  ( çizim sorunları { kimlik:  metin } , hesap
    çalıştı mı , hesabın sorun kimlikleri , uygun olmayan bölümlerin kimlikleri ,
    hesap çizimin bütün ölçülerini aldı mı ).  Çizim kurulamayınca hesabın
    bazı denetimleri eksik kalır ( uygulama_girdisi.yerlesim_olculeri ):  o
    hâldeki "uygun değil" sayısı düzeltmeden sonrakiyle denk değildir."""
    try:
        asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
    except uygulama_istegi.GecersizGirdi as e:
        #  Aday kapıdan geçmiyor:  hesap durur, kapının iletileri yeni sorun
        hk = {kimlik(h): h for h in e.hatalar}
        return hk, False, set(hk), frozenset(), False
    with istek_onbellegi.etkin():
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
        _g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, s if s.get("aktif") else None, "", i)
    a = s["asansorler"][i]
    uygun_degil = frozenset(
        b.get("kimlik") for b in a.get("bolumler") or [] if (b.get("sonuc") or {}).get("uygun") is False
    )
    return (
        {kimlik(h): str(h) for h in hata},
        bool(a.get("aktif")),
        {kimlik(h) for h in a.get("hata") or []},
        uygun_degil,
        bool(a.get("aktif")) and not (a.get("girdi") or {}).get("_cizim_olcmedi"),
    )


class Butce:
    """Bir isteğin sınama bütçesi ( AZAMI_SINAMA ) ve güvenlik süresi.  Biten
    bütçe sebebini tutar:  "sinama" ( belirlenimli ) ya da "sure" ( güvenlik )."""

    def __init__(self, sinama=AZAMI_SINAMA, sure=GUVENLIK_SURESI):
        self.kalan = sinama
        self.bitis = time.monotonic() + sure
        self.neden = None

    def var(self):
        """Bir sınama daha yapılabilir mi."""
        if self.neden is None and self.kalan <= 0:
            self.neden = "sinama"
        elif self.neden is None and time.monotonic() > self.bitis:
            self.neden = "sure"
        return self.neden is None

    def durum(self, veri, i):
        """girdi_durumu — bütçeden bir sınama düşerek ( akışlı istekte ekranda sayılır )."""
        self.kalan -= 1
        asamalar.say()
        return girdi_durumu(veri, i)


def girdi_yaz(veri, i, anahtar, deger):
    """Girdinin bir kutusu değişmiş kopyası ( proje geneli alan proje genelinde;
    tek kuyuda kuyunun ortak girdisi iki asansörde — ön yüzün "Uygula"sı gibi ).
    9 Kas:  ortak girdi seçili asansöre yazılıyordu;  kapı onu 1. asansörden okuduğu
    için 2. asansörde aday hiç etki etmiyor, "düzeltme bulunamadı" deniyordu."""
    y = copy.deepcopy(veri)
    metin = deger if isinstance(deger, str) else f"{deger:g}"
    if anahtar in uygulama_istegi.PROJE_GENELI_ALANLAR:
        y.setdefault("proje_geneli", {})[anahtar] = metin
    elif anahtar in KUYU_ORTAK and gorunum.tek_kuyu_mu(y.get("proje_geneli"), len(y["asansorler"])):
        for a in y["asansorler"]:
            a[anahtar] = metin
    else:
        y["asansorler"][i][anahtar] = metin
    return y


def _sonucu(once, sonra, ortulu=frozenset()):
    """Bir değişikliğin hükmü:  { gider ( kimlikler ) , yeni , ortaya ( gizliyken
    görünür olan — yeni sayılmaz ) , kotu }.  ortulu:  bugün de var olan ama
    denetim ilk hatada durduğu için görünmeyen sorunların kimlikleri
    ( cizim_uclari.genis_sorunlar ).

    HESAP:  düzeltmeden sonra uygun olmayan çıkacak bölümler ( bugün uygun
    görünen ) SÖYLENİR ( hesapta ):  30 Eki taraması — "askı kabin altı → kabin
    üstü" ağırlık raylarını "uygun değil" gösteriyordu, kullanıcıya
    söylenmiyordu.  Çoğu kez düzeltme bozmaz, ORTAYA ÇIKARIR:  çizim
    kurulamayınca hesabın bazı denetimleri eksik kalır ( dolgu — 1 Kas ).  Bu
    yüzden uygun olmayan bölüm sayısının artması öneriyi ancak bugünkü hesap
    çizimin bütün ölçülerini almışsa kötü yapar;  almamışsa öneri kalır,
    çıkanlar söylenir ( atmak çizimi kurmanın tek yolunu saklardı )."""
    s0, h0, hk0, u0, tam0 = once
    s1, h1, hk1, u1, _tam1 = sonra
    kotu = (
        (h0 and not h1)
        or (not h0 and not h1 and not hk1 <= hk0 | ortulu)
        or (h0 and h1 and tam0 and len(u1) > len(u0))
    )
    return {
        "gider": [k for k in s0 if k not in s1],
        "yeni": [s1[k] for k in s1 if k not in s0 and k not in ortulu],
        "ortaya": [s1[k] for k in s1 if k not in s0 and k in ortulu],
        #  Yalnız bugün UYGUN GÖRÜNEN bölümler:  hesap bugün durmuşsa ( çizimin plan
        #  denetimi ) uygun görünen bölüm yoktur — düzeltmeden sonra hesap ekranda
        #  zaten görünür;  hepsini saymak her öneriye aynı uzun listeyi yazardı
        "hesapta": sorted(u1 - u0) if h0 and h1 else [],
        "kotu": bool(kotu),
    }


def _turev_adaylari(sorunlar, degerler, gizli, alan):
    """{ ( anahtar , adım ) : { sorun kimlikleri } } — açığı kapatan adım
    ( yeni değer − bugünkü ), türevden;  aynı kutuya bağlı sorunların en
    uzaktaki adımı da ( hepsine birden ) aday."""
    out, yonlu = {}, {}
    for s in sorunlar:
        f = getattr(s, "fark", None)
        if f is None or float(f) >= 0:
            continue
        for (yer, k), c in izli.turev(f).items():
            a = alan.get(k)
            if (
                yer != "girdi"
                or abs(c) < 1e-9
                or k in gizli
                or k in DISI
                or k not in degerler
                or not a
                or a["tur"] != "sayi"
                or a["birim"] not in ADIM
            ):
                continue
            adim = -float(f) / c
            out.setdefault((k, adim), set()).add(kimlik(s))
            yonlu.setdefault((k, adim > 0), []).append((adim, kimlik(s)))
    for (k, _arti), liste in yonlu.items():
        if len(liste) > 1:
            en = max(liste, key=lambda x: abs(x[0]))[0]
            out.setdefault((k, en), set()).update(x[1] for x in liste)
    return out


def _deger(bugun, adim, carpan, birim="mm"):
    """Yeni değer:  birimin adımına ( ADIM ) güvenli yönde ( açığı kapatan
    yana ) yuvarlanır;  çarpan 0:  türevin değeri + bir adım ( eşitlikte kalan
    sınır )."""
    a = ADIM[birim]
    v = (bugun + (adim + math.copysign(a, adim) if carpan == 0 else adim * carpan)) / a
    return round((math.ceil(v - 1e-9) if adim > 0 else math.floor(v + 1e-9)) * a, 6)


def _form_kurali_uyar(anahtar, deger, alan):
    return not cizim_uclari.kural_disi(
        [{"anahtar": anahtar, "deger": deger, "etiket": alan[anahtar]["etiket"]}]
    )


def _turevle(veri, i, once, sorunlar, degerler, gizli, alan, butce, ortulu):
    """Türev adaylarını sınar:  [ { anahtar , yeni , gider , yontem } ] ( kabul edilenler )."""
    adaylar = _turev_adaylari(sorunlar, degerler, gizli, alan)

    def sira(ka):
        k, adim = ka
        return (k in BINA, -len(adaylar[ka]), abs(adim) / max(abs(degerler[k]), 100.0))

    secilen = sorted(adaylar, key=sira)[:AZAMI_ADAY]
    if secilen:
        asamalar.asama("turev")
    kabul, denenen = [], set()
    for k, adim in secilen:
        for carpan in (1.0,) + YENIDEN:
            v = _deger(degerler[k], adim, carpan, alan[k]["birim"])
            if (k, v) in denenen or not _form_kurali_uyar(k, v, alan):
                continue
            if not butce.var():
                return kabul
            denenen.add((k, v))
            r = _sonucu(once, butce.durum(girdi_yaz(veri, i, k, v), i), ortulu)
            if not r["yeni"] and not r["kotu"] and r["gider"]:
                kabul.append(
                    {
                        "anahtar": k,
                        "yeni": v,
                        "gider": r["gider"],
                        "ortaya": r["ortaya"],
                        "hesapta": r["hesapta"],
                        "yontem": "türev",
                    }
                )
            #  Hedeflerinden biri gittiyse büyütmek gerekmez
            if adaylar[(k, adim)] & set(r["gider"]) or r["yeni"] or r["kotu"]:
                break
    return kabul


def _degisenler(veri, i, onceki, alan, gizli):
    """Son temiz girdiden bu yana değişen sayı kutuları:  [ ( anahtar , eski , yeni ) ]."""
    simdi = dict(veri.get("proje_geneli") or {}, **veri["asansorler"][i])
    eski = dict((onceki or {}).get("proje_geneli") or {}, **((onceki or {}).get("asansor") or {}))
    out = []
    for k, a in alan.items():
        if a["tur"] != "sayi" or a["birim"] not in ADIM or k in gizli or k in DISI:
            continue
        v0, v1 = _sayi(eski.get(k)), _sayi(simdi.get(k))
        if v0 is not None and v1 is not None and abs(v0 - v1) >= ADIM[a["birim"]]:
            out.append((k, float(v0), float(v1)))
    return out[:3]


def _son_degisiklikle(veri, i, once, onceki, alan, gizli, butce, ortulu):
    """Son değişiklikle çıkan sorunların sınırı ( ikiye bölme ):  değişen kutuda
    eski değerdeki kadar temiz olan ( orada olmayan hiçbir sorun yok ),
    bugünküne en yakın değer — doğrulanmış.  "Eski değerde olmayan" ölçüt:
    girdi çizime hiç çevrilemiyorsa ( tampon kaidesi ≤ 0 ) bugünkü sorun
    listesi kısadır;  kaideyi düzelten değer kesitin sorunlarını ortaya
    çıkarabilir — sınır onları da geçen değerdir ( kuyu dibi 1000 → 1415 )."""
    kabul = []
    degisenler = _degisenler(veri, i, onceki, alan, gizli)
    if degisenler:
        asamalar.asama("sinir", "  ·  ".join(_kisa_etiket(alan[k]) for k, _v0, _v1 in degisenler))
    for k, v0, v1 in degisenler:
        if not butce.var():
            break
        eski = butce.durum(girdi_yaz(veri, i, k, v0), i)
        if not [x for x in once[0] if x not in eski[0]]:
            continue
        iyi, kotu_ = (v0, eski), v1
        a = ADIM[alan[k]["birim"]]
        while abs(kotu_ - iyi[0]) > a + 1e-9:
            orta = round(round((iyi[0] + kotu_) / 2.0 / a) * a, 6)
            if orta in (iyi[0], kotu_) or not butce.var():
                break
            d = butce.durum(girdi_yaz(veri, i, k, orta), i)
            if any(x not in eski[0] for x in d[0]):
                kotu_ = orta
            else:
                iyi = (orta, d)
        r = _sonucu(once, iyi[1], ortulu)
        if r["gider"] and not r["yeni"] and not r["kotu"] and _form_kurali_uyar(k, iyi[0], alan):
            kabul.append(
                {
                    "anahtar": k,
                    "yeni": iyi[0],
                    "gider": r["gider"],
                    "ortaya": r["ortaya"],
                    "hesapta": r["hesapta"],
                    "yontem": "son değişiklik",
                }
            )
    return kabul


def _secim_alanlari(s):
    """Sorunun parçalarına göre denenecek seçim kutuları."""
    p = set(sorun.parcalari(s))
    out = [k for k, parcalar in list(SECIMLER.items()) + list(KOMSU_SECIM.items()) if p & parcalar]
    if "siginma" in p or "sığınma" in str(s).lower():
        ust = getattr(s, "cizim", None) in ("kabin_ustu", "kuyu_kesiti_on")
        out.append("siginma_tipi_ust" if ust else "siginma_tipi_dip")
    #  Makine dairesizde 1:1 çizilmez ( kuyu_ustu.dogrula ):  çaresi askı oranı.
    #  İleti söylüyordu, öneri gelmiyordu ( 30 Eki taraması:  27 çaresiz sorun )
    if "1:1 askı çizilmez" in str(s):
        out.append("aski_orani")
    return out


def _secenekler(k, a, simdi):
    """Seçim kutusunun bugünkü dışındaki seçenekleri ( sayı seçeneklide komşular )."""
    secenek = list(a.get("secenekler") or [])
    sayi = _sayi(simdi)
    ayni = [
        j for j, v in enumerate(secenek) if str(v) == str(simdi) or (sayi is not None and _sayi(v) == sayi)
    ]
    if k in KOMSU_SECIM:
        if not ayni:
            return []
        j = ayni[0]
        return [secenek[x] for x in (j - 1, j + 1, j - 2, j + 2) if 0 <= x < len(secenek)]
    return [v for j, v in enumerate(secenek) if j not in ayni]


def _secimle(veri, i, once, sorunlar, alan, gizli, girilen, butce, oncelikli, ortulu):
    """Seçim düzeltmeleri:  sorunun parçasına göre ilgili seçimin öbür
    seçenekleri uygulanıp sınanır.  Düzeltmesi olmayan sorunların seçimleri önce."""
    alanlar = []
    for s in sorted(sorunlar, key=lambda x: kimlik(x) not in oncelikli):
        for k in _secim_alanlari(s):
            if k not in alanlar and k in alan and k not in gizli:
                alanlar.append(k)
    kabul, sayac = [], 0
    for k in alanlar:
        asamalar.asama("secim", _kisa_etiket(alan[k]))
        simdi = girilen.get(k)
        simdi = alan[k]["varsayilan"] if simdi in (None, "") else simdi
        for v in _secenekler(k, alan[k], simdi):
            if sayac >= AZAMI_SECIM or not butce.var():
                return kabul
            sayac += 1
            r = _sonucu(once, butce.durum(girdi_yaz(veri, i, k, v), i), ortulu)
            if r["gider"] and not r["yeni"] and not r["kotu"]:
                kabul.append(
                    {
                        "anahtar": k,
                        "eski": simdi,
                        "yeni": v,
                        "gider": r["gider"],
                        "ortaya": r["ortaya"],
                        "hesapta": r["hesapta"],
                        "yontem": "seçim",
                    }
                )
    return kabul


class _Tarama:
    """Bir isteğin bina ölçüsü taraması ( _taramayla ):  sınama ve tek ölçünün araması."""

    def __init__(self, veri, i, once, alan, butce, ortulu):
        self.veri, self.i, self.once, self.alan, self.butce, self.ortulu = veri, i, once, alan, butce, ortulu

    def sina(self, kim, k, v, sayac):
        """( sorun gitti mi — yeni sorun yok, hesap kötüleşmedi , hüküm ) ya da None:  bütçe ya da
        sorunun payı ( TARAMA_SORUN_SINAMA ) bitti, değer formun kuralı dışında."""
        if not self.butce.var() or sayac[0] >= TARAMA_SORUN_SINAMA or not _form_kurali_uyar(k, v, self.alan):
            return None
        sayac[0] += 1
        r = _sonucu(self.once, self.butce.durum(girdi_yaz(self.veri, self.i, k, v), self.i), self.ortulu)
        return kim in r["gider"] and not r["yeni"] and not r["kotu"], r

    def olcu(self, kim, k, bugun, sayac):
        """k ölçüsünde sorunu gideren en küçük büyüme:  ( yeni değer , hüküm ) ya da None.  Büyüyen
        adımlar ( TARAMA_ADIMLARI ), sonra son gidermeyenle ilk gideren arası ikiye bölme."""
        bolen = 1000.0 if self.alan[k]["birim"] == "m" else 1.0
        yon = TARAMA_YONU.get(k, 1.0)

        def deger(n):
            return round(bugun + yon * n * TARAMA_COZUNURLUK / bolen, 6)

        alt, ust, hukum = 0, None, None
        for adim in TARAMA_ADIMLARI:
            n = adim // TARAMA_COZUNURLUK
            x = self.sina(kim, k, deger(n), sayac)
            if x is None:
                break
            if x[0]:
                ust, hukum = n, x[1]
                break
            alt = n
        if ust is None:
            return None
        while ust - alt > 1:
            orta = (alt + ust) // 2
            x = self.sina(kim, k, deger(orta), sayac)
            if x is None:
                break
            if x[0]:
                ust, hukum = orta, x[1]
            else:
                alt = orta
        return deger(ust), hukum


def _taramayla(veri, i, once, sorunlar, degerler, gizli, alan, butce, cozulen, ortulu):
    """BİNA ÖLÇÜSÜ TARAMASI:  türev ve seçimden sonra hâlâ önerisi olmayan, açığı bilinmeyen
    ( fark yok ) her sorun için sorunun çizimine göre bina ölçüleri ( TARAMA_OLCULERI ), sırayla;
    ilk bulunan öneri olur.  Kabul türevinkiyle aynı:  sorun gider, yeni sorun yok, hesap
    kötüleşmez.  [ { anahtar , yeni , gider , … , yontem "tarama" } ]."""
    tarama = _Tarama(veri, i, once, alan, butce, ortulu)
    kabul = []
    for s in sorunlar:
        kim = kimlik(s)
        if kim not in once[0] or kim in cozulen or getattr(s, "fark", None) is not None:
            continue
        sayac = [0]
        for k in TARAMA_OLCULERI.get(getattr(s, "cizim", None), ()):
            a = alan.get(k)
            if not a or k in gizli or not sayi_mi(degerler.get(k)) or a["birim"] not in ("mm", "m"):
                continue
            asamalar.asama("tarama", _kisa_etiket(a))
            bulunan = tarama.olcu(kim, k, degerler[k], sayac)
            if bulunan is None:
                continue
            yeni, hukum = bulunan
            kabul.append(
                {
                    "anahtar": k,
                    "yeni": yeni,
                    "gider": hukum["gider"],
                    "ortaya": hukum["ortaya"],
                    "hesapta": hukum["hesapta"],
                    "yontem": "tarama",
                }
            )
            cozulen = cozulen | set(hukum["gider"])
            break
    return kabul


def coz(veri, i=0, onceki=None, butce=None):
    """Aktif asansörün her sorununun doğrulanmış çareleri:
    { careler:  [ { metin , oneriler:  [ … ] } ] , sinama , tamamlandi , neden , sure }.
    tamamlandi:  arama bütçeye ( neden "sinama" ) ya da güvenlik süresine
    ( "sure" ) takılmadan bitti mi — takıldıysa çareler eksik olabilir."""
    t0 = time.monotonic()
    butce = butce or Butce()
    ilk = butce.kalan
    asamalar.asama("okuma")
    once = girdi_durumu(veri, i)
    sorunlar, degerler, gizli = cizim_uclari.izli_sorunlar(veri, i)
    alan = {a["anahtar"]: a for gr in uygulama_istegi.alanlar()["gruplar"] for a in gr["alanlar"]}
    #  Denetim ilk hatada durduğu için bugün görünmeyen ( ama var olan ) sorunlar
    ortulu = {kimlik(h) for h in cizim_uclari.genis_sorunlar(veri, i)} - set(once[0])
    kabul = _son_degisiklikle(veri, i, once, onceki, alan, gizli, butce, ortulu)
    kabul += _turevle(veri, i, once, sorunlar, degerler, gizli, alan, butce, ortulu)
    girilen = dict(veri.get("proje_geneli") or {}, **veri["asansorler"][i])
    cozulen = {x for c in kabul for x in c["gider"]}
    oncelikli = {x for x in once[0] if x not in cozulen}
    kabul += _secimle(veri, i, once, sorunlar, alan, gizli, girilen, butce, oncelikli, ortulu)
    cozulen = {x for c in kabul for x in c["gider"]}
    kabul += _taramayla(veri, i, once, sorunlar, degerler, gizli, alan, butce, cozulen, ortulu)
    careler = []
    for kim, metin in once[0].items():
        oneriler = _sirala([c for c in kabul if kim in c["gider"]], degerler)
        careler.append(
            {
                "metin": metin,
                "oneriler": [
                    {
                        "anahtar": c["anahtar"],
                        "etiket": alan[c["anahtar"]]["etiket"],
                        "eski": c["eski"] if "eski" in c else degerler.get(c["anahtar"]),
                        "girilmis": girilen.get(c["anahtar"]) not in (None, ""),
                        "yeni": c["yeni"],
                        "gider": [once[0][x] for x in c["gider"]],
                        #  Düzeltmeden sonra görünür olacak ( bugün gizli ) sorunlar
                        "ortaya_cikan": c.get("ortaya", []),
                        #  Düzeltmeden sonra hesapta uygun olmayan çıkacak bölümler ( bugün
                        #  uygun görünen — kimlikler;  ekran adlarını hesabın bölümlerinden okur )
                        "hesapta_ortaya_cikan": c.get("hesapta", []),
                        "bina": c["anahtar"] in BINA,
                        "aciklama": _kot_aciklamasi(c, degerler),
                        "yontem": c["yontem"],
                    }
                    for c in oneriler
                ],
            }
        )
    return {
        "careler": careler,
        "sinama": ilk - butce.kalan,
        "tamamlandi": butce.neden is None,
        "neden": butce.neden,
        "sure": round(time.monotonic() - t0, 2),
    }


#  Kot kutusunun önerisi mimarın diliyle ( KOT_PLANI 1.2 — "kuyu dibi kotu −8,80 →
#  −8,95:  15 cm daha derin" ):  ( artınca , azalınca )
KOT_YONU = {
    "kuyu_dibi_kotu": ("daha sığ", "daha derin"),
    "kuyu_tavani_kotu": ("daha yüksek", "daha alçak"),
    "md_zemini_kotu": ("daha yüksek", "daha alçak"),
}


def _kot_aciklamasi(c, degerler):
    """Kot kutusunun önerisinde değişimin kendisi ( "15 cm daha derin" );  başka
    kutuda None."""
    yon = KOT_YONU.get(c["anahtar"])
    eski = c["eski"] if "eski" in c else degerler.get(c["anahtar"])
    if yon is None or not (sayi_mi(eski) and sayi_mi(c["yeni"])) or c["yeni"] == eski:
        return None
    fark = c["yeni"] - eski
    return f"{round(abs(fark) * 100, 1):g} cm {yon[0] if fark > 0 else yon[1]}".replace(".", ",")


def _sirala(liste, degerler):
    """Hesapta bölüm çıkarmayanlar önce ( 1 Kas );  sonra son değişikliğin sınırı →
    sayı ( bina olmayan ) → seçim → bina ölçüsü;  sonra en çok sorunu gideren →
    en küçük değişiklik;  aynı kutudan tek öneri ( en iyisi )."""

    def anahtar(c):
        cikar = bool(c.get("hesapta"))
        if c["yontem"] == "seçim":
            return (cikar, True, 1, -len(c["gider"]), 0.0)
        eski = degerler.get(c["anahtar"]) or 0.0
        return (
            cikar,
            c["yontem"] != "son değişiklik",
            2 if c["anahtar"] in BINA else 0,
            -len(c["gider"]),
            abs(c["yeni"] - eski) / max(abs(eski), 100.0),
        )

    out, gorulen = [], set()
    for c in sorted(liste, key=anahtar):
        if c["anahtar"] in gorulen:
            continue
        gorulen.add(c["anahtar"])
        out.append(c)
    return out[:SORUN_BASINA]


@router.post("/api/uygulama/care")
async def api_care_ucu(istek: Request, veri: dict = Body(...)):
    """Aktif asansörün sorunlarının çareleri ( api_care ).  AKIŞ ( 20 Kas — arayüz taslağı B5 ):
    istek uc_ortak.AKIS_TURU'nü isterse aramanın aşamaları ( ASAMALAR ) ve sınama sayısı satır
    satır, sonda bugünkü yanıt;  vazgeçilince ( bağlantı kapandı ) arama bir sonraki sınamada durur."""
    if not uc_ortak.akis_isteniyor(istek):
        return await run_in_threadpool(api_care, veri)
    birakildi = threading.Event()
    ilerleme = asamalar.Ilerleme(ASAMALAR, iptal=birakildi.is_set)
    return uc_ortak.akisli_yanit(istek, lambda: json.loads(api_care(veri).body), ilerleme, birakildi)


def api_care(veri):
    """Aktif asansörün sorunlarının çareleri.  onceki:  son temiz girdi
    ( { asansor , proje_geneli } — ön yüz gönderir;  yoksa yalnız türev )."""
    try:
        try:
            i = int(veri.get("asansor") or 0)
        except (TypeError, ValueError):
            i = 0
        asansorler = veri.get("asansorler") or []
        if not isinstance(asansorler, list) or not asansorler:
            return JSONResponse({"aktif": False, "hata": ["Asansör yok."]})
        #  BOZUK GÖVDE ( 22 Kas denetimi ):  asansör_girdileri sözlük olmayan asansörü atlar, ama
        #  arama ham listeyi okur — [ 1 , 2 ] içeride TypeError'du ( genel ileti dönüyordu ).
        #  Ön yüz böyle göndermez;  açık ileti ve proje geneli / önceki girdi yalnız sözlükse.
        if not all(isinstance(a, dict) for a in asansorler):
            return JSONResponse({"aktif": False, "hata": ["Asansör girdisi okunamadı."]})
        if "proje_geneli" in veri and not isinstance(veri["proje_geneli"], dict):
            #  Sözlük değilse yok sayılır:  istek okuyucusu da öyle sayar ( ilk asansörden )
            veri = {k: x for k, x in veri.items() if k != "proje_geneli"}
        i = min(max(i, 0), len(asansorler) - 1)
        try:
            uygulama_istegi.asansor_girdileri(veri)
        except uygulama_istegi.GecersizGirdi as e:
            return JSONResponse({"aktif": False, "hata": e.hatalar})
        onceki = veri.get("onceki") if isinstance(veri.get("onceki"), dict) else None
        if onceki is not None:
            onceki = {k: x for k, x in onceki.items() if isinstance(x, dict)}
        return JSONResponse({"aktif": True, **coz(veri, i, onceki)})
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"aktif": False, "hata": [hata_iletisi("DÜZELTME HATASI", e, ": ")]})
