# -*- coding: utf-8 -*-
"""
AVAN SEÇİCİSİ — mimarın kuyusuna doğrulanmış asansör  ( 12 Kas 2026 )

Avan projesinde elde yalnız MİMARİ vardır:  kuyunun genişliği ve derinliği,
kotlar, makine dairesi var mı.  Kapasite ve hız trafik hesabından gelir.
Uygulama projesinin çizimi ise ürünü de ister ( motor, halat, ray, kaçıklıklar ).
Seçici aradaki boşluğu doldurur:  taslak projelerden ( on-yuz/src/lib/
taslaklar.json — her biri hesabı ve çizimi temiz, testler/test_taslaklar ) aynı
yükün paketini alır, mimarın kuyusuna UYARLAR, her adayı uygulamanın hesabı ve
çizimiyle sınar.

SÖZLEŞME ( kullanıcı, 12 Kas ):
  · Kabin trafik hesabının kapasitesinde kalır:  seçici kabini değiştirmez, kuyu
    büyükse fazlası boşluktur.  Kabin avan kartınınkidir ( 24 Kas — KABIN ):  standarda
    uyuyorsa paketinkinin yerine geçer, kartta boşsa paketinki;  uymuyorsa aranmaz
    ( "beyan" — kartta paketin kabini, kabin_nedenleri ).
  · Dönen asansör DOĞRULANMIŞTIR:  çizim sorunsuz, hesabın MİMARİYİ ilgilendiren
    bölümleri ( AVAN_BOLUMLERI — sığınma alanları, kabin alanı, tamponlar ) uygun.
    Mimarın kuyusuna sığan yoksa asansör dönmez;  mimardan istenecek ölçüler
    döner ( "gereken" ) — yanlış çizim hiç kurulmaz.
  · ÜRÜN bölümleri ( tahrik, motor, halat, ray, makine taşıyıcısı, elektrik ) avan
    projesinin işi değildir ( kullanıcı, 12 Kas:  "tahrikle alakalı bir işimiz yok
    ki, avan projesi bu" ) — avanın kendi motor / kuvvet / elektrik hesabı vardır.
    Seçici onları da geçirmeye çalışır ( en küçük motor, en hafif ray );
    geçiremediği asansörü engellemez, "acik_bolumler"de söylenir.
  · Avanın BEYANI ( kartın askı oranı ve makine tipi — avan motor hesabının
    girdileri ) çizimde AYNEN durur:  hesap sayfası ile pafta çelişmez ( 12 Kas ).
    Beyanla asansör kurulamıyor, paketin kendi askısıyla kurulabiliyorsa çizim
    çıkmaz;  kartta neyin seçileceği döner ( "beyan" ).
  · Karşı ağırlık önce paketteki yerinde ( yanda ) denenir;  mimarın kuyusuna öyle
    sığmıyorsa arkaya alınır ( kullanıcı, 14 Kas:  "önce yan, sığmazsa arka" ).
    Makine daireli 1:1 askıda tersi:  önce arka, sığmazsa yan ( kullanıcı, 13 Kas:  "makine
    dairesiz 2:1'de ilk yanda ağırlık, makine daireli 1:1'de ilk arkada ağırlık" ).
  · Sayı uydurulmaz:  denenen değerler formun seçenekleri, IEC 60072 motor
    kademeleri ( avan/tablolar ) ve paketin kendi değerleridir.

UYARLAMA ( 12 Kas ölçümü — cikti/araclar/avan_cizim_olcum.py ):  paket yalnız
kendi kuyu genişliğinde temizdi.  Kuyu genişleyince karşı ağırlık duvarla
birlikte uzaklaşır:  makine dairesizde halat sapar ( tek sarılma açısı kalmaz ),
makine dairelide kaide deliklere basar.  Kabin karşı ağırlığın yanına kaydırılır
( kabin – ağırlık duvarı aralığı paketteki gibi kalır );  boşluk öbür yanda kalır.
"""

import collections
import contextlib
import contextvars
import copy
import hashlib
import importlib.metadata
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import time

from cizim import asamalar
from cizim import katlar
from motor.avan import tablolar
from motor.ortak.adimlar import tr, trn
from motor.uygulama import mukavemet_tablolari
from tasarim import alanlar
from uclar import care_uclari, uygulama_istegi
from yollar import KOK

log = logging.getLogger(__name__)

with open(os.path.join(KOK, "on-yuz", "src", "lib", "taslaklar.json"), encoding="utf-8") as _f:
    _TASLAKLAR = json.load(_f)
#  YALNIZ AVANIN HAZIR ASANSÖRLERİ ( 14 Kas — 450 · 1600 · 2000 · 2500 kg;  açılışın taslağı
#  değiller ):  aynı biçim.  Kabin ve kapı ISO 4190 / TS EN 81-20 Çizelge 6, kuyu formun kuralı;
#  çizimleri temiz, avanı bağlayan bölümleri uygun ( testler/test_avan_paketleri ).  450 kg'ın
#  her bölümü uygun;  1600 kg ve üstünde ÜRÜN bölümleri ( tahrik, halat … — "acik_bolumler" )
#  açık kalır:  avanı engellemez ( kullanıcı, 14 Kas:  "çıksın" ), uygulama projesinde çözülür.
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "avan_paketleri.json"), encoding="utf-8"
) as _f:
    _AVAN_PAKETLERI = json.load(_f)

#  Mimarın verdikleri:  pakette ne yazarsa yazsın bunlar mimardan gelir
KOTLAR = (alanlar.DURAK_KOTLARI, "kuyu_dibi_kotu", "kuyu_tavani_kotu", "md_zemini_kotu")
#  Kat adları ve giriş katı ( kot tablosu — 13 Kas ):  kotlarla birlikte mimardan
ADLAR = (alanlar.DURAK_ADLARI, alanlar.GIRIS_DURAGI)
#  Tavan döşemesinin kalınlığı ( mimarın kesitinden — boşsa uygulamanın kuralı )
MIMARI = ("kuyu_genisligi", "kuyu_derinligi", *KOTLAR, *ADLAR, "tavan_dosemesi")
#  16 Kas:  makine dairesinin iç yüksekliği de mimarın ( boşsa uygulamanın varsayılanı 3500 —
#  paketlerde yok );  plan ölçüsü değildir:  küçük oda kuralı ( _kucuk_oda ) ona bakmaz
MIMARI_GENEL = ("mk_uzunluk", "mk_genislik", "md_yukseklik")
#  Avanın BEYANI ( kartın askı oranı ve makine tipi — avan motor hesabının girdileri ):
#  verilmişse paketinkinin yerine geçer, seçici değiştirmez
#  ( 14 Kas ) kapı genişliği ve tipi de:  trafik hesabının kapısı ( kullanıcı kararı )
BEYAN = ("aski_orani", "makine_tipi", "kapi_genisligi", "kat_kapisi_tipi")
#  KARTIN KABİNİ ( 24 Kas — kullanıcı:  "Evet, kullanılsın" ):  avan hesabı kabini karttan okur
#  ( alan, aydınlatma );  kartınki standarda uyuyorsa ( kabin_nedenleri ) çizim de onunla kurulur,
#  boş kutu paketinkini alır.  Seçici kabini değiştirmez ( SABIT ).  Eskiden çizimin kabini hep
#  paketinkiydi ( 13 Kas ):  kart başka kabin söyleyince çizim çıkmıyor, kart paketinkine
#  getiriliyordu.  24 Kas ölçümü ( 800 kg, makine dairesiz, kuyu 1800 × 2700, son kat 4050 ):
#  paketin 1350 × 1400 kabiniyle mimardan 1980, kartın 1300 × 1400 kabiniyle 1920 genişlik istenir.
KABIN = ("kabin_genisligi", "kabin_derinligi")
ZORUNLU = ("beyan_yuku", "beyan_hizi", "kuyu_genisligi", "kuyu_derinligi", *KOTLAR[:3])

#  Avan projesini bağlayan bölümler:  kuyunun ölçülerine ( kuyu üstü, kuyu dibi ) ve
#  kabine bakanlar.  Kalanı ürün hesabıdır — uygulama projesinde çözülür.
AVAN_BOLUMLERI = frozenset(("siginma_alanlari", "kabin_alani", "tamponlar"))

#  Bir seçimde en çok bu kadar hesap + çizim sınaması ( biri ~0,1 sn )
AZAMI_SINAMA = 120
#  Uyarlamada ( yerleşim çaresi, mimardan istenecek ölçü ) en çok bu kadar adım
AZAMI_ADIM = 6
#  MİMARDAN İSTENECEK ÖLÇÜNÜN KÜÇÜLTÜLMESİ ( 13 Kas ):  çare bulucunun adım adım topladığı
#  kuyu ölçüsü gereğinden büyük çıkabiliyordu ( 630 kg 1800 genişliğe sığarken 2110 isteniyordu ).
#  Bulunan ölçü ile mimarınki arasında, bu adımın katlarında ( mm ) ikili arama;  her deneme
#  hesap + çizimle sınanır;  genişlikte ayrıca en çok bu kadar yerleşim adımlı deneme ( _kucult ).
KUCULEN = ("kuyu_genisligi", "kuyu_derinligi")
KUCULTME_ADIMI = 10
KUCULTME_YERLESIM = 3
#  KOTLARDA YERLEŞİM ADIMLI DENEME SAYISI ( _kucult — her biri bir çare bulucu turu;  26 Kas ölçümü ):
#  üçer denemeyle uçtan uca testin vakası ( 630 kg, 1,6 m/s, 11 durak, son kat 3400 ) 21 → 28 sn uzadı,
#  CI'da 60 sn'yi aştı ( PR #171 ).  Kuyu tavanında TEK deneme üçüyle aynı kotu buluyor ( 2,5 m/s
#  hazır asansörlerin 5 taramasında 15–21 cm, vakada +34,11 → +33,92 ), süre +2 sn;  hiç denemesiz
#  1250 kg'ı ve 500 mm kısa kuyu üstünü kaçırıyor.  Kuyu dibinde küçültme üç deneme ister ( 630 MRL
#  800 sığ:  −1,29 → −1,16;  tek denemeyle hiç inmiyor ) — yalnız kuyu dibi yetmeyen aramada çalışır.
KUCULTME_YERLESIM_KOT = {"kuyu_tavani_kotu": 1, "kuyu_dibi_kotu": 3, "md_zemini_kotu": 1}
#  KOTLAR DA KÜÇÜLTÜLÜR ( 24 Kas — T630, kuyu 2350, kuyu tavanı +19,00:  +19,37 isteniyordu, +19,18
#  yetiyor ):  çare bulucu kotu türevle önerir, sorunu O AN bağlayan parçaya göre — regülatör 1,10 m
#  korkuluğun içinde, küpeştenin 65 mm altında:  0,30 m düşey ( m.5.2.5.7.2 c ).  Regülatör öbür yana
#  alınınca bağlayan kabin halat bağlantısı olur ( korkuluğun 7,5 mm dışında:  0,10 m ) ve +19,18
#  yeter;  ama iki adımlı bu çözümü çare bulucu görmez ( her adayın sorunu tek başına gidermesi
#  gerekir ).  Kot da genişlik gibi küçültülür:  ikili arama, sonra yerleşim adımlı deneme ( _kucult ).
#  Kotlar metreyle yazılır;  arama mm'de, mimarınkinden önerilene doğru ( kuyu dibi aşağı iner ).
KUCULEN_KOT = ("kuyu_tavani_kotu", "kuyu_dibi_kotu", "md_zemini_kotu")
#  BÜTÇE SINAMA SAYISIDIR, SAAT DEĞİL ( 16 Kas — uygulamanın "düzeltme öner"i gibi, care_uclari ):
#  arama yalnız AZAMI_SINAMA / AZAMI_ADIM / AZAMI_YENIDEN ile sınırlıdır;  aynı girdi her makinede
#  aynı sonucu verir ( araclar/avan_tarama kaydıyla birebir ).  Eskiden yerel saat sınırları vardı
#  ( 4 · 12 · 24 sn ):  yavaş ya da yüklü makinede süre dolunca arama yarıda kalıyor, yanıt
#  "sığmaz" diyordu ( 630 kg 1650 × 2300:  hızlı makinede 22 sn'de uygun, CI'da sığmaz ).
#
#  GÜVENLİK SÜRESİ ( sn ):  yalnız bir isteğin sunucuyu kilitlememesi için;  normal istekte
#  ulaşılmaz ( saatsiz taramada en uzun 125 sn — CI, 4 işçi aynı anda ).  Ulaşılırsa yanıt
#  "tamamlanmadi" der — sığmaz DEMEZ ( sonuç bilinmiyor ).
GUVENLIK_SURESI = 240.0
#  SAATSİZ KİP ( araclar/avan_tarama, testler ):  güvenlik süresi de uygulanmaz.
SAATSIZ = False


class Kesildi(Exception):
    """Arama yarıda kesildi:  neden "sure" ( güvenlik süresi ) ya da "iptal" ( istek bırakıldı )."""

    def __init__(self, neden):
        super().__init__(neden)
        self.neden = neden


class _CareButcesi(care_uclari.Butce):
    """Seçicinin içindeki çare bulucunun bütçesi:  sınama sayısı aynı ( care_uclari.AZAMI_SINAMA ),
    saati yok — güvenlik süresi ve iptal seçicinin ( _koruma_bak ).  Eskiden çare bulucu kendi
    60 sn'lik saatiyle koşuyordu ( seçicinin sonucu yine makinenin hızına bağlı kalabilirdi ) ve
    iptal ona ulaşmıyordu:  bırakılan arama çare bulucuda 20 – 30 sınama daha sürüyordu."""

    def __init__(self):
        super().__init__(sure=float("inf"))

    def var(self):
        _koruma_bak()
        return super().var()


#  Bu aramanın koruması ( _korumali_sec kurar;  her sınamadan önce bakılır — _koruma_bak )
_KORUMA = contextvars.ContextVar("avan_secici_koruma", default=None)


#  ARAMANIN AŞAMALARI ( 17 Kas — kullanıcı:  "beklerken ne yapıldığını görelim" ):  ekran uzun
#  aramada aramanın GERÇEKTEN hangi adımda olduğunu gösterir;  süreye göre değişen hazır yazı ya
#  da yüzde yoktur ( bütçe sınama sayısıdır, arama çoğunlukla çok önce biter ).  kod:  ( sürerken ,
#  bitince ).  Aşama seçimi ETKİLEMEZ:  yalnız bildirilir ( ilerleme bağlamı yoksa hiçbir şey ).
ASAMALAR = {
    "paket": ("Hazır asansör seçiliyor", "Hazır asansör seçildi"),
    "yerlesim": ("Kuyuya yerleşim deneniyor", "Kuyuya yerleşim denendi"),
    "uyarlama": ("Yerleşim kuyuya uyarlanıyor", "Yerleşim kuyuya uyarlandı"),
    "olcu": ("Kuyu ölçüsü değiştirilerek yerleşim aranıyor", "Kuyu ölçüsü değiştirilerek yerleşim arandı"),
    "kucultme": ("Mimardan istenecek en küçük ölçü aranıyor", "Mimardan istenecek en küçük ölçü bulundu"),
    "dogrulama": ("İstenen ölçü yeniden doğrulanıyor", "İstenen ölçü yeniden doğrulandı"),
    "aski": ("Hazır asansörün askısı deneniyor", "Hazır asansörün askısı denendi"),
    "oda": ("Makine dairesine yerleşim deneniyor", "Makine dairesine yerleşim denendi"),
    "kapi": ("Makine dairesi kapısı yerleştiriliyor", "Makine dairesi kapısı yerleştirildi"),
    "cizim": ("Paftalar çiziliyor", "Paftalar çizildi"),
}


def _koruma_bak():
    k = _KORUMA.get()
    if k is None:
        return
    bitis, iptal = k
    if iptal is not None and iptal():
        raise Kesildi("iptal")
    if time.monotonic() > bitis:
        raise Kesildi("sure")


#  Seçicinin değiştirmediği:  trafik hesabının kapasitesi ( kabin ), kapı, yük, hız
SABIT = frozenset(
    ("beyan_yuku", "beyan_hizi", "kabin_genisligi", "kabin_derinligi", "kabin_ic_yuksekligi")
    + ("kapi_genisligi", "kapi_yuksekligi", "durak_adedi", "seyir_mesafesi")
    + ("aski_orani", "makine_tipi")
)

#  Elle ayarlanamayanlar ( ayarlar ):  mimari, kartın beyanı, trafiğin kabini / kapısı / hızı
AYAR_DISI = frozenset((*MIMARI, *MIMARI_GENEL, *BEYAN)) | SABIT
PROJE_GENELI = frozenset(uygulama_istegi.PROJE_GENELI_ALANLAR)
#  Proje geneli girdilerden elle ayarlanabilenler ( 17 Kas — makine dairesi kapısı avanda da
#  sürüklenir, dört duvar arasında ):  yalnız çizimin kozmetiği;  isteğin proje_geneli'sine yazılır ( _Sinayici )
AYAR_GENEL = frozenset(("md_kapi_duvar", "md_kapi_konum"))

#  ÜRÜN ARAMASI — düşen bölüm → sırayla denenecek ( girdi , değerler ).  Değerler
#  küçükten büyüğe:  bölümü geçiren İLK değer alınır ( en küçük motor, en hafif ray ).
_PROFIL = alanlar.ALAN["kabin_ray_profili"].secenekler
_YATAK = tuple(x for x in alanlar.ALAN["yan_yatak"].secenekler if isinstance(x, int) and x >= 140)
URUN = {
    "motor_gucu": (("motor_gucu", tablolar.MOTOR_KADEMELERI),),
    "kabin_raylari": (("kabin_ray_profili", _PROFIL),),
    "agirlik_raylari": (("agirlik_ray_profili", _PROFIL),),
    "aski_halatlari": (("halat_adedi", tuple(range(4, 13))),),
    "makine_konstruksiyonu": (("yan_yatak", _YATAK),),
    #  Tahrik:  sertleştirilmiş kanal, denge zinciri ( BAR 2515 gibi ), en son V kanal
    "tahrik_yetenegi": (
        ("kanal_isleme", ("Sertleştirilmiş",)),
        ("denge_zinciri", ("Var",)),
        ("kanal_sekli", ("V Kanal",)),
    ),
    #  Büyük motorun akımı:  kolon hattı ve makine beslemesi birlikte büyür
    "gerilim_dusumu": (
        (("kolon_kesit", "makine_kesit"), tuple(k for k in tablolar.STANDART_KESITLER if k >= 6)),
    ),
    #  1,0 m/s üstünde enerji biriktirmeli tampon olmaz ( TS EN 81-20 m.5.8.1.5 )
    #  Paketin kendi tampon boyu / stroku ( 1250 · 1275:  1,0 m/s'nin tamponu ) hıza yetmiyorsa
    #  boş bırakılır:  program tamponu hıza göre kendi seçer ( "" — kuraldan )
    "tamponlar": (
        ("tampon_tipi", (alanlar.ALAN["tampon_tipi"].secenekler[2],)),
        (("kabin_tampon_boyu", "kabin_tampon_ezilme", "agirlik_tampon_ezilme"), ("",)),
    ),
}


def paketler():
    """{ ( yük kg , makine dairesiz mi ):  taslak }"""
    return {
        (int(t["asansor"]["beyan_yuku"]), t["proje_geneli"].get("mk_yok") == "true"): t
        for t in (*_TASLAKLAR, *_AVAN_PAKETLERI)
    }


def _metin(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    return x if isinstance(x, str) else f"{x:g}"


def _sayi(x):
    return float(str(x).replace(",", "."))


def _sayili(x):
    try:
        _sayi(x)
        return x is not None and not isinstance(x, bool)
    except ValueError:
        return False


def _olcu(x):
    """Girilmiş, sıfırdan büyük ölçü mü ( boş / okunamayan / 0:  girilmemiş sayılır )."""
    return _sayili(x) and _sayi(x) > 0


def kabin(taslak, m):
    """Çizimin kabini ( mm ):  { kabin_genisligi , kabin_derinligi } — kartınki ( m, KABIN ), boş
    olan paketinki.  Standarda uygunluğu ayrıca:  kabin_nedenleri."""
    a = taslak["asansor"]
    return {k: _sayi(m[k]) if _olcu(m.get(k)) else _sayi(a[k]) for k in KABIN}


def kabin_nedenleri(taslak, m):
    """KARTIN KABİNİ STANDARDA UYUYOR MU ( 24 Kas ) — uymuyorsa nedenleri ( metin listesi;  boş:
    uygun ).  TS EN 81-20 m.5.4.2, uygulamanın kabin alanı bölümünün tablolarıyla
    ( motor/uygulama/mukavemet — çizimin hesabı aynı tabloyla denetler ):
      · alan, beyan yükünün Çizelge 6'daki en büyük alanını aşmaz ( büyük kabin beyan yükünün
        üstünde yüklenebilir;  uygulamanın hesabında da UYGUN DEĞİL — avanı bağlayan bölüm );
      · alan trafik hesabının kişisini ( m["kisi"] — verilmişse ) taşır, Çizelge 8:  pafta kartın
        kişisini yazar ( 18 Kas ), kabin o kadar yolcuyu taşımalı ( m.5.4.2.3.1 ).
    Paketin kabini denetlenmez:  hazır asansör o yükte doğrulanmıştır ( test_avan_paketleri ) —
    kart paketin kabinini söylüyorsa ( ya da boşsa ) davranış 24 Kas'tan önceki gibidir.  Alana
    kapı girintisi katılmaz:  paketlerin uzun pervazı varsayılan ( 90 mm ≤ 100 — m.5.4.2.1.3 )."""
    k = kabin(taslak, m)
    if all(k[x] == _sayi(taslak["asansor"][x]) for x in KABIN):
        return []
    q = _sayi(m["beyan_yuku"])
    alan = k["kabin_genisligi"] * k["kabin_derinligi"] / 1e6
    nedenler = []
    azami = mukavemet_tablolari.kabin_azami_alan(q)
    if azami is not None and alan > azami + 1e-9:
        nedenler.append(
            f"Kabin alanı {tr(alan)} m²:  {trn(q, 0)} kg için en çok {tr(azami)} m² "
            "( TS EN 81-20 Çizelge 6 ) — büyük kabin beyan yükünün üstünde yüklenebilir."
        )
    kisi = m.get("kisi")
    if _olcu(kisi) and mukavemet_tablolari.cizelge8_kisi(alan) < _sayi(kisi):
        nedenler.append(
            f"Kabin alanı {tr(alan)} m²:  {trn(kisi, 0)} kişi için en az "
            f"{tr(mukavemet_tablolari.cizelge8_alan(int(_sayi(kisi))))} m² ( TS EN 81-20 Çizelge 8 ) — "
            "kabin trafik hesabının kapasitesini taşımaz."
        )
    return nedenler


def _istek(taslak, m, ek=None):
    """Paket + mimarın kuyusu ( + denenen değerler ) → uygulamanın isteği."""
    a = {k: v for k, v in taslak["asansor"].items() if k not in MIMARI}
    pg = {k: v for k, v in taslak["proje_geneli"].items() if k not in MIMARI_GENEL}
    for k in ("beyan_hizi", *MIMARI, *BEYAN):
        if m.get(k) not in (None, ""):
            a[k] = _metin(m[k])
    for k in KABIN:
        if _olcu(m.get(k)):
            a[k] = _metin(_sayi(m[k]))
    for k in MIMARI_GENEL:
        if m.get(k) not in (None, "") and pg.get("mk_yok") != "true":
            pg[k] = _metin(m[k])
    #  Makine dairesinin ölçüsü verilmediyse paketinki ( formun kuralı )
    for k in MIMARI_GENEL:
        if k not in pg and k in taslak["proje_geneli"]:
            pg[k] = taslak["proje_geneli"][k]
    a.update({k: _metin(v) for k, v in (ek or {}).items()})
    #  RAY – KAPI ARASI ( RK ) seçicide 650'den başlar, gerekirse seçici büyütür ( çare bulucunun
    #  yerleşim adımı ).  23 Kas ( PR #167 ):  RK boşken köprü onu kendiliğinden büyütüyordu
    #  ( yerleşim kurtarması — cizim/kopru ).  Bu kurtarma, kuyu büyüyünce çıkan yeni sorunu
    #  ( korkuluk – kuyu tavanı ) ilk adımda gösteriyordu.  Çare bulucu yeni sorun açan adımı
    #  önermediği için iki adımlı çözüm ( kuyu genişliği + tavan kotu ) kayboluyordu:
    #  630 / 1000 kg 1100 merkezi kapıda seçici "sığmaz" deyip kapıyı daraltmayı öneriyordu.
    #  Elle ayar ( ayarlar ) bunun üstüne yazılır ( _Sinayici ).
    a.setdefault("ray_kapi_arasi", _metin(alanlar.RK_VARSAYILAN))
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def ayarlar(m):
    """ELLE AYARLANAN ÖLÇÜLER ( 14 Kas, kullanıcı:  "ölçüye tıklayınca değiştirebilmem lazım —
    ray – kapı, karşı ağırlık – duvar … hesaplamayla ilgisi yok" ).  m["ayar"]:  { uygulamanın
    asansör girdisi:  değer } — çizimde tıklanan ölçünün kaynağı ( + AYAR_GENEL:  sürüklenen
    makine dairesi kapısının yeri ).  Seçici bunları AYNEN kullanır
    ( her adayda, uyarlamada, küçültmede — _Sinayici );  kalanını yine kendi seçer ve sonucu
    yine doğrular:  ayarla asansör kurulamıyorsa çizim çıkmaz.  Mimarinin, trafiğin ve kartın
    ölçüleri ( kuyu, kotlar, kabin, kapı genişliği, yük, hız, askı ) burada değişmez — onların
    kendi kutuları vardır.  Döner { alan:  metin } ( tanınmayan / izinsiz alanlar atılır )."""
    ham = m.get("ayar") or {}
    return {
        k: _metin(v)
        for k, v in ham.items()
        if k in alanlar.ALAN
        and k not in AYAR_DISI
        and v not in (None, "")
        and (k not in PROJE_GENELI or k in AYAR_GENEL)
    }


def _kaydirma(taslak, m):
    """Kabinin yana kaçıklığı:  kabin – karşı ağırlık duvarı aralığı paketteki
    gibi kalsın.  Ağırlık arkadaysa kabin ortada kalır ( None:  dokunma ).
    Kartın kabini ( KABIN ) paketinkinden darsa ağırlık yanındaki kenarı yine paketteki yerinde
    kalır:  kabin ağırlığa doğru farkın yarısı kadar daha kayar ( geniş kabinde tersi )."""
    a = taslak["asansor"]
    yon = {"Sağ": 1, "Sol": -1}.get(a.get("agirlik_yeri", alanlar.ALAN["agirlik_yeri"].varsayilan))
    if yon is None:
        return None
    fark = _sayi(m["kuyu_genisligi"]) - _sayi(a["kuyu_genisligi"])
    fark -= kabin(taslak, m)["kabin_genisligi"] - _sayi(a["kabin_genisligi"])
    return _sayi(a.get("kabin_yana_kaciklik") or 0) + yon * fark / 2.0


class _Sinayici:
    """Hesap + çizim sınaması, sayarak ( care_uclari.girdi_durumu )."""

    def __init__(self):
        self.kalan = AZAMI_SINAMA
        self.sayi = 0
        #  Mimarın vermediği makine dairesi ölçüleri ( _oda_kurali ):  kuyuyla birlikte büyür
        self.oda = {}
        #  Kullanıcının çizimde elle ayarladığı ölçüler ( ayarlar ):  her adayda aynen durur
        self.ayar = {}

    def __call__(self, v):
        _koruma_bak()
        self.kalan -= 1
        self.sayi += 1
        asamalar.say()
        #  İsteğin kendisine yazılır ( kopya değil ):  dönen istek sınananla aynıdır
        for k, d in self.ayar.items():
            (v["proje_geneli"] if k in AYAR_GENEL else v["asansorler"][0])[k] = d
        for k, (kuyu, oda, paket) in self.oda.items():
            fark = max(0.0, _sayi(v["asansorler"][0][kuyu]) - paket)
            v["proje_geneli"][k] = _metin(oda + fark)
        cizim, aktif, hesap, uygun_degil, olctu = care_uclari.girdi_durumu(v, 0)
        bolum = sorted(x for x in uygun_degil if x)
        engel = [b for b in bolum if b in AVAN_BOLUMLERI]
        return {
            "cizim": cizim,
            "hesap": sorted(hesap),
            "bolum": bolum,
            #  avanı bağlayanlar ( AVAN_BOLUMLERI ) — "temiz" bunlara bakar
            "engel": engel,
            "temiz": not cizim and aktif and not hesap and not engel and olctu,
        }

    def var(self):
        return self.kalan > 0


#  Makine dairesinin ölçüsü → kuyunun aynı yöndeki ölçüsü ( formun kuralı:  uzunluk kabin
#  derinliğinden, genişlik kabin genişliğinden türer )
ODA_KUYU = {"mk_uzunluk": "kuyu_derinligi", "mk_genislik": "kuyu_genisligi"}


def _oda_kurali(taslak, m):
    """MİMARIN VERMEDİĞİ MAKİNE DAİRESİ ( 14 Kas — tarama:  630 ve 1000 kg makine dairelide
    paketinkinden 600 mm geniş kuyu "sığmaz" çıkıyordu ).  Oda verilmediyse hazır asansörünki
    kullanılır;  kuyu hazır asansörünkinden büyükse oda da o kadar büyür ( makine dairesi kuyunun
    üstüne kurulur — sabit kalan odanın duvarı geniş kuyunun boşluğuna basıyordu ).
    Döner { oda alanı:  ( kuyu alanı , paketin odası , paketin kuyusu ) } — mimarın verdiği
    ölçü için kayıt yoktur ( o aynen kullanılır )."""
    pg = taslak["proje_geneli"]
    if m.get("mk_yok") in (True, "true"):
        return {}
    return {
        k: (kuyu, _sayi(pg[k]), _sayi(taslak["asansor"][kuyu]))
        for k, kuyu in ODA_KUYU.items()
        if m.get(k) in (None, "") and k in pg
    }


def _urun_ara(v, d, sina, gevsek=False):
    """Düşen bölümleri ürün değerleriyle geçirmeyi dener ( URUN ).  Bir bölüm
    başka bir seçimle düşebilir ( ağır ray → motor ):  üç tur.  Döner ( istek ,
    durum , seçilenler ).

    gevsek:  yalnız avanı bağlayan bölümler aranır ve seçim yeni bir çizim sorunu ya da
    düşen bölüm çıkarabilir ( hidrolik tampon uzundur:  kuyu üstü yetmez ) — uyarlamada;
    sonuç yine baştan sona sınanır."""
    secilen = {}
    for _tur in range(3):
        degisti = False
        for bolum in [b for b in (d["engel"] if gevsek else d["bolum"]) if b in URUN]:
            for anahtar, degerler in URUN[bolum]:
                if bolum not in d["bolum"]:
                    break
                #  Birlikte değişen girdiler ( iki kablo kesiti ):  ilki bugünkü değeri verir
                anahtarlar = anahtar if isinstance(anahtar, tuple) else (anahtar,)
                bugun = v["asansorler"][0].get(anahtarlar[0])
                girilmis = bugun not in (None, "")
                if not girilmis:
                    bugun = alanlar.ALAN[anahtarlar[0]].varsayilan
                for x in degerler:
                    if not sina.var():
                        return v, d, secilen
                    #  "" = kuraldan:  yalnız pakette girilmiş değeri boşaltmak bir denemedir
                    if x == "":
                        if not girilmis:
                            continue
                        bugun = None
                    if bugun is not None and _metin(x) == (
                        bugun if isinstance(bugun, str) else _metin(bugun)
                    ):
                        continue
                    #  Sayılı kademede ( motor, halat adedi, yan yatak ) bugünkünden küçüğü denenmez
                    if _sayili(x) and _sayili(bugun) and _sayi(x) <= _sayi(bugun):
                        continue
                    y = copy.deepcopy(v)
                    for k in anahtarlar:
                        y["asansorler"][0][k] = _metin(x)
                    dy = sina(y)
                    #  Bölüm geçti ve başka hiçbir şey bozulmadı ( yeni çizim sorunu,
                    #  yeni düşen bölüm )
                    #  ( yeni düşen bölümün de düğmesi varsa sıradaki turda aranır:  büyük
                    #  motor makine taşıyıcısını düşürür, o da yan yatakla geçer )
                    if (
                        bolum not in dy["bolum"]
                        and (gevsek or set(dy["cizim"]) <= set(d["cizim"]))
                        and (gevsek or set(dy["bolum"]) - set(d["bolum"]) <= set(URUN))
                        and set(dy["hesap"]) <= set(d["hesap"])
                    ):
                        v, d, degisti = y, dy, True
                        secilen.update({k: _metin(x) for k in anahtarlar})
                        break
        if not degisti or not d["bolum"]:
            break
    return v, d, secilen


def kapi_ailesi(tip):
    """Kat kapısı tipinin ailesi:  "Teleskopik" · "Otomatik Merkezi" · "Manuel" ( kanat sayısı
    ve açılış yönü aile içi ayrıntıdır — trafik hesabı yalnız aileyi seçer )."""
    return next((a for a in ("Teleskopik", "Otomatik Merkezi", "Manuel") if str(tip).startswith(a)), None)


def _oneri_sec(v, kapi_kilidi=False, bina_once=False, yalniz_yerlesim=False, kilit=frozenset()):
    """Çare bulucunun ( care_uclari.coz ) önerilerinden sıradaki adım:  önce YERLEŞİM
    ( kaçıklıklar, kapı tipi — seçicinin kendi kararı ), sonra BİNA ( mimardan istenir );
    ikisinde de başka sorun açmayan önce.  Kabin, kapı genişliği, yük, hız değişmez;
    otomatik kapı elle açılan kapıya çevrilmez.

    bina_once:  sıra tersine — önce mimardan istenecek ölçü.  Yerleşim adımı ( kaçıklık ) bazen
    sorunu yalnız kabini küçülterek çözülür hâle getirir ( kabin değişmez → çıkmaz );  aynı
    aday bu sırayla bir kez daha denenir ( _sec.yerlesim )."""
    #  Çare araması seçicinin uyarlama aşamasının parçası:  kendi aşamaları ve sınamaları ekrana gitmez
    with asamalar.sessiz():
        careler = care_uclari.coz(v, 0, None, _CareButcesi())["careler"]
    oneriler = [
        o
        for c in careler
        for o in c["oneriler"]
        if o["anahtar"] not in SABIT
        #  Kullanıcının elle ayarladığı ölçü ( ayarlar ):  çare onu değiştirmez
        and o["anahtar"] not in kilit
        #  yalniz_yerlesim:  mimardan ölçü istenmez ( dar kuyuda önce kaçıklıklarla sığdırma )
        and not (yalniz_yerlesim and o["bina"])
        and not str(o["yeni"]).startswith("Manuel")
        #  Trafik hesabının kapısı ( beyan ):  çare kapının ailesini değiştirmez ( 3 kanat olur )
        and not (
            kapi_kilidi
            and o["anahtar"] == "kat_kapisi_tipi"
            and kapi_ailesi(o["yeni"])
            != kapi_ailesi(
                v["asansorler"][0].get("kat_kapisi_tipi") or alanlar.ALAN["kat_kapisi_tipi"].varsayilan
            )
        )
    ]
    oneriler.sort(
        key=lambda o: (bool(o["ortaya_cikan"] or o["hesapta_ortaya_cikan"]), o["bina"] != bina_once)
    )
    return oneriler[0] if oneriler else None


def _uyarla(v, d, sina, kapi_kilidi=False, bina_once=False, yalniz_yerlesim=False, adim=AZAMI_ADIM):
    """Sorunlu adayı adım adım temize çeker:  ürün ( gevşek ) → çare bulucunun önerisi.
    Döner ( istek , durum , seçilenler , gereken listesi )."""
    secilen, gereken, ilk = {}, {}, v
    for _adim in range(adim):
        if not d["temiz"] and d["engel"]:
            v, d, s = _urun_ara(v, d, sina, gevsek=True)
            secilen.update(s)
        if d["temiz"] or not d["cizim"] or not sina.var():
            break
        oneri = _oneri_sec(v, kapi_kilidi, bina_once, yalniz_yerlesim, frozenset(sina.ayar))
        if oneri is None:
            break
        v = care_uclari.girdi_yaz(v, 0, oneri["anahtar"], oneri["yeni"])
        if oneri["bina"]:
            gereken[oneri["anahtar"]] = {
                "anahtar": oneri["anahtar"],
                "etiket": oneri["etiket"],
                "yeni": oneri["yeni"],
                "sebep": oneri["gider"][0] if oneri["gider"] else "",
            }
        else:
            secilen[oneri["anahtar"]] = {**v.get("proje_geneli", {}), **v["asansorler"][0]}.get(
                oneri["anahtar"]
            )
        d = sina(v)
    if not d["temiz"] and d["engel"]:
        v, d, s = _urun_ara(v, d, sina, gevsek=True)
        secilen.update(s)
    a = {**ilk.get("proje_geneli", {}), **ilk["asansorler"][0]}
    for g in gereken.values():
        g["eski"] = a.get(g["anahtar"])
        if g["anahtar"] in KOTLAR:
            g["yeni"] = _kot_metni(g["yeni"])
    return v, d, secilen, list(gereken.values())


#  Kuyu ölçüsü → kabinin aynı yöndeki ölçüsü ( kabin çevresindeki aralık paketteki gibi kalsın )
KUYU_KABIN = {"kuyu_genisligi": "kabin_genisligi", "kuyu_derinligi": "kabin_derinligi"}


def _paket_kuyusu(taslak, m):
    """Paketin kuyusu, kabin farkı kadar ( mm ):  kartın kabini ( KABIN ) paketinkinden 50 mm darsa
    kuyu da 50 mm dar — kabin çevresindeki aralıklar paketteki gibi.  Kabin paketinkiyse paketin
    kuyusu."""
    a, k = taslak["asansor"], kabin(taslak, m)
    return {x: _sayi(a[x]) + k[y] - _sayi(a[y]) for x, y in KUYU_KABIN.items()}


def _paket_olcusunde(taslak, m, ek, sina):
    """Mimarın kuyusu paketinkinden ( _paket_kuyusu ) dar / sığ ise aynı aday paketin kuyu
    ölçüsüyle ( kabin yine ağırlığın yanında ).  Döner ( istek , durum , seçilenler , gereken )
    ya da None:  kuyu paketinkinden küçük değil."""
    paketin = _paket_kuyusu(taslak, m)
    buyuyen = {k: paketin[k] for k in KUCULEN if _sayi(m[k]) < paketin[k]}
    if not buyuyen:
        return None
    m2 = {**m, **buyuyen}
    ek2 = dict(ek)
    if "kabin_yana_kaciklik" in ek2:
        ek2["kabin_yana_kaciklik"] = round(_kaydirma(taslak, m2))
    v = _istek(taslak, m2, ek2)
    d = sina(v)
    secilen = dict(ek2)
    if d["bolum"]:
        v, d, s = _urun_ara(v, d, sina)
        secilen.update(s)
    gereken = [
        {
            "anahtar": k,
            "etiket": alanlar.ALAN[k].etiket,
            "eski": _metin(m[k]),
            "yeni": _sayi(x),
            "sebep": "Bu kabin ve karşı ağırlığı daha küçük kuyuya sığmıyor.",
        }
        for k, x in buyuyen.items()
    ]
    return v, d, secilen, gereken


def _kucult(v, d, gereken, sina, taslak, kapi_kilidi=False, anahtarlar=(*KUCULEN, *KUCULEN_KOT)):
    """Mimardan istenecek kuyu ölçülerini ( KUCULEN ) ve kotları ( KUCULEN_KOT ) temiz kalan en
    küçük değere indirir.  Döner ( istek , durum , gereken ).  Genişlik denenirken kabin de ağırlığın
    yanına yeniden kaydırılır ( _kaydirma — uyarlamanın başındaki kaydırma mimarın ilk genişliği
    içindi ).  Mimarın kendi ölçüsü de temizse o ölçü istenmez ( listeden düşer ).

    İki aşama, ikisi de saate bakmaz ( sonuç makinenin hızına göre değişmez ):
      1  ikili arama, yalnız sınama ( hızlı );
      2  genişlikte ve kotlarda, bulunanın altında en çok KUCULTME_YERLESIM deneme daha — her
         birinde bir yerleşim adımı ( çare bulucu:  kapı kaçıklığı dar kuyuda kapıyı yerinde tutar;
         regülatörün yanı korkuluğun yanındaki parçayı değiştirir, kuyu tavanı alçalır ).
    Kot metreyle yazılır:  adımlar mm'de, mimarınkinden ( eski ) önerilene ( yeni ) doğru."""
    yanda = v["asansorler"][0].get("agirlik_yeri", taslak["asansor"].get("agirlik_yeri")) == taslak[
        "asansor"
    ].get("agirlik_yeri")

    def dene(anahtar, x, yerlesim, taban=None):
        """( istek , durum ) ya da None.  taban:  ( istek , durum ) — deneme bundan türer ( yoksa
        bulunan son temiz istekten )."""
        tv, td = taban or (v, d)
        y = care_uclari.girdi_yaz(tv, 0, anahtar, x)
        adaylar = [y]
        if anahtar == "kuyu_genisligi" and yanda:
            kay = _kaydirma(taslak, {**{k: v["asansorler"][0].get(k) for k in KABIN}, "kuyu_genisligi": x})
            if kay is not None:
                adaylar.insert(0, care_uclari.girdi_yaz(y, 0, "kabin_yana_kaciklik", round(kay)))
        for i, y in enumerate(adaylar):
            if not sina.var():
                return None
            dy = sina(y)
            #  Kotta avanı bağlayan bölüm düşse de yerleşim denenir:  kuyu üstünün açıklıkları hesabın
            #  sığınma bölümünde de denetlenir ( korkuluk – tavan sorunu "siginma_alanlari"nı düşürür )
            if (
                yerlesim
                and i == 0
                and not dy["temiz"]
                and dy["cizim"]
                and (anahtar in KUCULEN_KOT or not dy["engel"])
            ):
                y, dy, _s, _g = _uyarla(y, dy, sina, kapi_kilidi, yalniz_yerlesim=True, adim=1)
            #  Temiz ve yeni bir ürün bölümü de düşürmüyor
            if dy["temiz"] and set(dy["bolum"]) <= set(td["bolum"]):
                return y, dy
        return None

    #  Önce derinlik, sonra genişlik, en son kotlar ( planın ölçüsü korkuluğun yüksekliğini belirler )
    for g in sorted(
        (g for g in gereken if g["anahtar"] in anahtarlar and _sayili(g["eski"])),
        key=lambda g: (g["anahtar"] != "kuyu_derinligi", g["anahtar"] in KUCULEN_KOT),
    ):
        kot = g["anahtar"] in KUCULEN_KOT
        if kot:
            alt, ust = round(_sayi(g["eski"]) * 1000), round(_sayi(g["yeni"]) * 1000)
        else:
            alt, ust = _sayi(g["eski"]), _sayi(g["yeni"])
        #  Kuyu dibi kotu aşağı iner:  adımlar mimarınkinden önerilene doğru
        yon = -1 if kot and ust < alt else 1
        n = int(-(-(yon * (ust - alt)) // KUCULTME_ADIMI))
        if n < 1:
            continue
        #  alt + k · adım:  k = n bulunan ölçü ( temiz ), k = 0 mimarınki.  En küçük temiz k aranır
        dusuk, yuksek = -1, n
        while yuksek - dusuk > 1:
            k = 0 if dusuk < 0 and yuksek == n else (dusuk + yuksek) // 2
            sonuc = dene(g["anahtar"], _adimdaki(alt, yon, k, kot), False)
            if sonuc is None:
                dusuk = k
            else:
                yuksek, (v, d) = k, sonuc
        if g["anahtar"] == "kuyu_genisligi" or kot:
            #  k = 0 ( mimarın ölçüsü ) yerleşimle zaten denendi ( _sec.yerlesim ) — sığmıyor
            dusuk = 0
            #  KOTTA DENEMELER ÜST ÜSTE BİNMEZ:  her biri aynı düzenden ( yerleşimsiz bulunan ) tek
            #  yerleşim adımıyla — mimar o kotu girince seçici aynı düzeni uyarlamada yeniden bulur
            #  ( _tek_seferde ).  Birikince ( karşı ağırlık çarpma arası + regülatörün yanı ) iki adımlı,
            #  yeniden bulunamayan düzen çıkıyor, doğrulama turları kotu adım adım geri büyütüyordu.
            taban = (v, d) if kot else None
            for _deneme in range(KUCULTME_YERLESIM_KOT[g["anahtar"]] if kot else KUCULTME_YERLESIM):
                if yuksek - dusuk <= 1:
                    break
                k = (dusuk + yuksek) // 2
                sonuc = dene(g["anahtar"], _adimdaki(alt, yon, k, kot), True, taban)
                if sonuc is None:
                    dusuk = k
                else:
                    yuksek, (v, d) = k, sonuc
        if yuksek < n:
            g["yeni"] = _adimdaki(alt, yon, yuksek, kot)

    def istenmez(g):
        """Mimarın kendi ölçüsü yetiyor ( kot:  önerilen mimarınkine indi )."""
        if g["anahtar"] not in anahtarlar:
            return False
        if g["anahtar"] in KUCULEN_KOT:
            return _sayi(g["yeni"]) == _sayi(g["eski"])
        return _sayi(g["yeni"]) <= _sayi(g["eski"])

    return v, d, [g for g in gereken if not istenmez(g)]


def _adimdaki(alt, yon, k, kot):
    """Küçültmenin k. adımındaki değer:  alt + yon · k · KUCULTME_ADIMI;  kot ( mm ) formun yazımıyla."""
    x = alt + yon * k * KUCULTME_ADIMI
    return katlar.kot_metni(round(x)) if kot else x


def _kot_metni(deger):
    """Çare bulucunun kot önerisi ( m, sayı ) → formun yazımı ( "+19,37" )."""
    return katlar.kot_metni(round(float(deger) * 1000)) if not isinstance(deger, str) else deger


def sec(m):
    """Mimarın kuyusuna asansör.

    m:  beyan_yuku ( kg ), beyan_hizi, kuyu_genisligi, kuyu_derinligi, durak_kotlari,
        kuyu_dibi_kotu, kuyu_tavani_kotu, mk_yok;  makine dairesi varsa md_zemini_kotu,
        isteğe bağlı mk_uzunluk / mk_genislik / md_yukseklik;  isteğe bağlı avanın beyanı ( BEYAN:
        aski_orani, makine_tipi ) — verilmişse istekte aynen durur;  isteğe bağlı kartın kabini
        ( KABIN — boşsa paketinki ) ve kişi ( kisi — trafik hesabının kapasitesi:  kabin bunu
        taşımalı, kabin_nedenleri );  isteğe bağlı ayar ( { girdi:  değer } — çizimde elle
        ayarlanan ölçüler, ayarlar ).

    Döner { durum , … }:
      "uygun"      istek ( uygulamanın isteği — çizimi ve avanı bağlayan bölümleri temiz ),
                   secimler, acik_bolumler ( geçirilemeyen ürün bölümleri — çoğunlukla boş )
      "gereken"    gereken [ { anahtar , etiket , eski , yeni , sebep } ] — mimarın
                   ölçüleri böyle olursa temiz;  istek o ölçülerle
      "sigmaz"     nedenler [ metin ] — mimardan istenecek ölçü de bulunamadı
      "paket_yok"  bu yük / düzen için paket yok;  hiz ( True ) + hizlar:  bu hızda çizim
                   çıkmaz ( uygulamanın hız listesinde yok — 1,75 · 3,5 m/s )
      "eksik"      eksik [ anahtar ] — mimari girdi eksik
      "beyan"      beyan [ { anahtar , etiket , eski , yeni } ] — avanın beyanıyla asansör
                   kurulamadı;  kartta bunlar seçilirse kurulur ( doğrulanmış, en az değişiklik ).
                   beyan_turu "kabin":  kartın kabini standarda uymuyor ( aranmadı ) — nedenler
                   [ metin ], kartta paketin kabini
    Hepsinde sinama ( sayı ) ve sure ( sn ).

    MAKİNE DAİRESİ KAPISI ( AYAR_GENEL — ekranda sürüklenir ):  asansörün seçimini etkilemez;
    seçim kapısız yapılır, kapı bulunan isteğe SONRA taşınır ( _kapiyi_tasi ).  Eskiden kapı da
    aramaya giriyordu:  uygun olmayan yerde seçici saniyelerce arayıp ilgisiz bir gerekçeyle
    "sığmaz" diyor, çizim kayboluyordu.

    SUNUCUDA ( korumali bağlamı — avan çizim ucu, paket ):  güvenlik süresi, iptal ve önbellek
    ( _korumali_sec );  yarıda kalırsa "tamamlanmadi" ( neden , hata ).  Bağlam yoksa ( testler,
    tarama ) ham arama."""
    iptal = _SUNUCU.get()
    if iptal is not None:
        return _korumali_sec(m, iptal)
    return _sec_ham(m)


def _sec_ham(m):
    """sec — koruma ve önbellek olmadan."""
    kapisiz, kapi = _kapisi_ayri(m)
    r = _sec_kapisiz(kapisiz)
    return _kapiyi_tasi(r, kapi) if kapi else r


def _kapisi_ayri(m):
    """( kapısız girdi , kapı ) — makine dairesi kapısının elle ayarı ( AYAR_GENEL ) seçimden
    ayrılır:  kapı asansörün seçimini etkilemez, bulunan isteğe sonra taşınır ( _kapiyi_tasi ).
    Kapı ayarı yoksa ( m , {} )."""
    kapi = {k: v for k, v in ayarlar(m).items() if k in AYAR_GENEL}
    if not kapi:
        return m, {}
    ayar = m.get("ayar") or {}
    return {**m, "ayar": {k: v for k, v in ayar.items() if k not in AYAR_GENEL}}, kapi


def _anahtar(m):
    """Seçicinin önbellek anahtarı:  girdinin kendisi ( sıralı JSON );  ayarsız girdi boş ayarla aynı
    ( ayarlar ikisini de boş okur — kapısı ayrılan girdi boş ayarla kalır, _kapisi_ayri )."""
    return json.dumps({**m, "ayar": m.get("ayar") or {}}, sort_keys=True, ensure_ascii=False, default=str)


#  Sunucu bağlamı ( korumali ):  None değilse seçici korumalı çalışır;  değer iptal sorgusu
_SUNUCU = contextvars.ContextVar("avan_secici_sunucu", default=None)


@contextlib.contextmanager
def korumali(iptal=None):
    """Bu bağlamdaki seçimler korumalı ve önbellekli ( sunucu uçları ).  iptal:  çağrılınca True
    dönerse arama durur ( ekran isteği bıraktı ) — yoksa yalnız güvenlik süresi."""
    token = _SUNUCU.set(iptal or (lambda: False))
    try:
        yield
    finally:
        _SUNUCU.reset(token)


def _korumali_sec(m, iptal):
    """SUNUCUNUN SEÇİCİSİ:  arama + güvenlik süresi + iptal + önbellek.

      · Güvenlik süresi ( GUVENLIK_SURESI ) ya da iptal ( iptal() True — ekran isteği bıraktı )
        aramayı keser:  yanıt { durum:  "tamamlanmadi" , neden , hata } — sığmaz demez.
      · ÖNBELLEK:  bütçe saat değil sınama sayısı olduğu için aynı girdinin sonucu hep aynıdır;
        son ONBELLEK_BOYU sonuç saklanır ( geri al, aynı kuyuya dönüş, paketi indirme anında ).
        Yarıda kalan sonuç saklanmaz.  Dönen sonuç kopyadır ( çağıran değiştirebilir ).  Bellekte
        yoksa İŞÇİLER ARASI disk önbelleğine bakılır ( _Onbellek ).
      · MAKİNE DAİRESİ KAPISI ( AYAR_GENEL ) seçimi etkilemez:  kapısız seçim önbellekten alınır
        ( yoksa aranır, kapısız anahtarla saklanır ), kapı ona taşınır — tek sınama.  18 Kas ( yayın
        öncesi denetim ):  önbellek yalnız kapılı anahtara bakıyordu, kapı her sürüklenişte bütün
        arama baştan yapılıyordu ( 800 kg makine daireli örnek:  kapısız önbellekten 0,26 sn, her
        kapı yeri 9,7 sn;  dar kuyuda dakikalar ).

    Saatsiz kipte ( SAATSIZ ) güvenlik süresi yok;  iptal ve önbellek yine çalışır."""
    anahtar = _anahtar(m)
    r = _ONBELLEK.al(anahtar)
    if r is not None:
        return r
    kapisiz, kapi = _kapisi_ayri(m)
    if kapi:
        r = _korumali_sec(kapisiz, iptal)
        if r["durum"] == "tamamlanmadi":
            return r
        r = _kapiyi_tasi(r, kapi)
        _ONBELLEK.koy(anahtar, r)
        return r
    t0 = time.monotonic()
    token = _KORUMA.set((float("inf") if SAATSIZ else t0 + GUVENLIK_SURESI, iptal))
    try:
        r = _sec_ham(m)
    except Kesildi as e:
        return {
            "durum": "tamamlanmadi",
            "neden": e.neden,
            "hata": TAMAMLANMADI[e.neden],
            "sinama": 0,
            "sure": round(time.monotonic() - t0, 2),
        }
    finally:
        _KORUMA.reset(token)
    _ONBELLEK.koy(anahtar, r)
    return r


#  Yarıda kalan aramanın ekrandaki / paketteki sebebi
TAMAMLANMADI = {
    "sure": "asansör araması güvenlik süresinde bitmedi ( sunucu yoğun olabilir ) — yeniden deneyin",
    "iptal": "asansör araması bırakıldı ( girdi değişti )",
}
ONBELLEK_BOYU = 64
#  Disk önbelleğinde en çok bu kadar sonuç ( eskiler silinir;  bir sonuç ~10 – 60 KB )
DISK_ONBELLEK_AZAMI = 2000


class _Onbellek:
    """SEÇİCİNİN ÖNBELLEĞİ:  bellek ( işçinin kendi, son ONBELLEK_BOYU ) + DİSK ( İŞÇİLER ARASI ).

    17 Kas ( yayın öncesi denetim ):  sunucu dört işçiyle çalışır, bellek önbelleği işçi
    başınadır.  "Projeyi indir" Çizimler adımında bulunan asansörü başka bir işçide
    bulamayınca aramayı baştan yapıyordu — kullanıcının 2 asansörlü projesinde paket 48 sn
    ( 23,7 + 24,1 ), dar kuyuda asansör başına dakikalar;  vekil sunucunun zaman aşımı ( 30 –
    60 sn ) indirmeyi düşürürdü.  Sonuç diske de yazılır, öbür işçiler oradan okur.

      · Klasör:  AVAN_SECICI_ONBELLEK ( "kapali":  disk yok ) ya da geçici klasörde
        kullanıcıya özel bir klasör ( yalnız sahibi okur / yazar — 0700 ).
      · PROGRAM DEĞİŞİNCE geçersiz:  alt klasörün adı programın kod imzasıdır ( _kod_imzasi —
        hesap / çizim / tasarım kodu ve hazır asansörler );  eski imzaların klasörleri silinir.
        Aynı imzada sonuç aynıdır ( bütçe deterministik ).
      · Yalnız JSON'a birebir dönüşen sonuç yazılır ( okunan bellektekiyle aynı olsun );  yazım
        atomiktir ( geçici dosya + yeniden adlandırma:  yarım dosya okunmaz );  okunamayan dosya
        yok sayılır ( arama yapılır ).  Disk hatası aramayı durdurmaz:  önbelleksiz devam."""

    def __init__(self):
        self._bellek = collections.OrderedDict()
        self._kilit = threading.Lock()
        self._klasor = None  # None:  henüz kurulmadı;  False:  disk kapalı / kurulamadı

    def __len__(self):
        return len(self._bellek)

    def clear(self):
        """Bellek ve disk ( testler:  yeni arama yapılsın )."""
        with self._kilit:
            self._bellek.clear()
            k = self._disk()
        if k:
            with contextlib.suppress(OSError):
                for ad in os.listdir(k):
                    with contextlib.suppress(OSError):
                        os.remove(os.path.join(k, ad))

    def al(self, anahtar):
        """Saklanan sonucun kopyası ya da None."""
        with self._kilit:
            r = self._bellek.get(anahtar)
            if r is not None:
                self._bellek.move_to_end(anahtar)
                return copy.deepcopy(r)
        r = self._diskten(anahtar)
        if r is not None:
            self._bellege(anahtar, r)
            return copy.deepcopy(r)
        return None

    def koy(self, anahtar, r):
        self._bellege(anahtar, copy.deepcopy(r))
        self._diske(anahtar, r)

    def _bellege(self, anahtar, r):
        with self._kilit:
            self._bellek[anahtar] = r
            while len(self._bellek) > ONBELLEK_BOYU:
                self._bellek.popitem(last=False)

    def _disk(self):
        """Disk klasörü ya da False ( kapalı / kurulamadı ) — ilk kullanımda kurulur.  Klasör
        sonradan silinmişse ( geçici klasör temizliği ) yeniden kurulur:  yoksa işçi yeniden
        başlayana kadar önbelleksiz kalırdı."""
        if self._klasor is None or (self._klasor and not os.path.isdir(self._klasor)):
            self._klasor = _disk_klasoru()
        return self._klasor

    def _yol(self, anahtar):
        k = self._disk()
        return k and os.path.join(k, hashlib.sha256(anahtar.encode("utf-8")).hexdigest() + ".json")

    def _diskten(self, anahtar):
        yol = self._yol(anahtar)
        if not yol:
            return None
        try:
            with open(yol, encoding="utf-8") as f:
                kayit = json.load(f)
        except (OSError, ValueError):
            return None
        #  Özet çakışmasına karşı:  kayıt kendi anahtarını taşır
        if not isinstance(kayit, dict) or kayit.get("anahtar") != anahtar:
            return None
        return kayit.get("sonuc")

    def _diske(self, anahtar, r):
        yol = self._yol(anahtar)
        if not yol:
            return
        try:
            metin = json.dumps({"anahtar": anahtar, "sonuc": r}, ensure_ascii=False)
            if json.loads(metin)["sonuc"] != r:
                return  # JSON'a birebir dönmüyor:  diskten okunan farklı olurdu
            gecici = f"{yol}.{os.getpid()}.{threading.get_ident()}.tmp"
            with open(gecici, "w", encoding="utf-8") as f:
                f.write(metin)
            os.replace(gecici, yol)
            self._buda(os.path.dirname(yol))
        except (OSError, TypeError, ValueError):
            log.warning("seçicinin disk önbelleğine yazılamadı", exc_info=True)
            with contextlib.suppress(OSError, UnboundLocalError):
                os.remove(gecici)

    @staticmethod
    def _buda(k):
        """En çok DISK_ONBELLEK_AZAMI sonuç:  fazlası, en eskiden başlayarak silinir."""
        with os.scandir(k) as it:
            dosyalar = [e for e in it if e.name.endswith(".json")]
        if len(dosyalar) <= DISK_ONBELLEK_AZAMI:
            return
        dosyalar.sort(key=lambda e: e.stat().st_mtime)
        for e in dosyalar[: len(dosyalar) - DISK_ONBELLEK_AZAMI]:
            with contextlib.suppress(OSError):
                os.remove(e.path)


#  İMZANIN KAPSADIĞI:  kod ve veri dosyaları ( KOK'a göre klasörler, türler ) — YAZI TİPLERİ DE:
#  çizimdeki yazının eni yazı tipinden ölçülür ( cizim/pdf — stringWidth );  yazıların yerleşimi ve
#  seçicinin "çizim temiz" kararı ona bağlıdır.  Yazının ölçüsünü ve çizimi kuran kütüphanelerin
#  sürümü de ( _IMZA_KUTUPHANELERI ).
_IMZA_KLASORLERI = ("cizim", "hesap", "tasarim")
_IMZA_TURLERI = (".py", ".json", ".ttf", ".otf")
_IMZA_KUTUPHANELERI = ("reportlab", "ezdxf")


def _imza_hesapla(kok=KOK, veri=None):
    """Programın seçiciyi etkileyen her şeyinin özeti:
      · kod ve veri dosyalarının adları ve içerikleri ( _IMZA_KLASORLERI, _IMZA_TURLERI —
        dogrulama / __pycache__ hariç ) + temel.py;
      · seçicinin YÜKLEDİĞİ hazır asansörler ( veri;  boşsa bu sürecinkiler — _TASLAKLAR,
        _AVAN_PAKETLERI ):  taslakların dosyası kod klasörlerinin DIŞINDA ( on-yuz/src/lib/
        taslaklar.json ) — dosyanın kendisi değil, bu sürecin kullandığı veri özetlenir;
      · kütüphane sürümleri ( _IMZA_KUTUPHANELERI ) ve Python'un ana sürümü.
    Aynı program her işçide aynı imzayı verir.  YENİ BİR VERİ KAYNAĞI ( dosyadan okunan, kod
    klasörlerinin dışında ya da başka türde ) seçiciyi etkiliyorsa buraya eklenmelidir."""
    h = hashlib.sha256()
    yollar_ = [os.path.join(kok, "temel.py")]
    for kl in _IMZA_KLASORLERI:
        for k, dizinler, dosyalar in os.walk(os.path.join(kok, kl)):
            dizinler[:] = sorted(x for x in dizinler if x not in ("__pycache__", "dogrulama"))
            yollar_ += [os.path.join(k, x) for x in sorted(dosyalar) if x.endswith(_IMZA_TURLERI)]
    for yol in yollar_:
        h.update(os.path.relpath(yol, kok).encode("utf-8") + b"\0")
        with open(yol, "rb") as f:
            h.update(f.read())
        h.update(b"\0")
    veri = [_TASLAKLAR, _AVAN_PAKETLERI] if veri is None else veri
    h.update(json.dumps(veri, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\0")
    for ad in _IMZA_KUTUPHANELERI:
        try:
            surum = importlib.metadata.version(ad)
        except importlib.metadata.PackageNotFoundError:
            surum = "-"
        h.update(f"{ad}={surum}\0".encode())
    h.update(f"python={sys.version_info[0]}.{sys.version_info[1]}".encode())
    return h.hexdigest()[:20]


#  İŞÇİ AÇILIRKEN hesaplanır ( modül yüklenince:  kod ve veri o an yüklenmiştir ).  17 Kas denetimi:
#  eskiden ilk disk kullanımında hesaplanıyor ve taslak verisini, yazı tiplerini, kütüphane
#  sürümlerini KAPSAMIYORDU — yalnız taslaklar.json değişen bir güncellemeden sonra eski hazır
#  asansörle bulunmuş sonuç kullanılırdı ( yanlış pafta, hatasız );  güncelleme dosyaları yerinde
#  değiştirirken eski bir işçi de eski koduyla bulduğu sonucu YENİ imzayla yazabilirdi.
_KOD_IMZASI = _imza_hesapla()


def _kod_imzasi():
    """Bu sürecin kod imzası ( _KOD_IMZASI )."""
    return _KOD_IMZASI


def _disk_klasoru():
    """Disk önbelleğinin bu programa ait klasörü ( kurulur ) ya da False."""
    ayar = os.environ.get("AVAN_SECICI_ONBELLEK", "")
    if ayar.strip().lower() == "kapali":
        return False
    kok = ayar or os.path.join(tempfile.gettempdir(), f"asansor-secici-onbellegi-{_kullanici()}")
    try:
        imza = _kod_imzasi()
        os.makedirs(kok, mode=0o700, exist_ok=True)
        #  Başkasının klasörü ya da herkese açık:  güvenilmez ( içine sonuç konabilir )
        st = os.stat(kok)
        if hasattr(os, "getuid") and (st.st_uid != os.getuid() or st.st_mode & 0o077):
            log.warning("seçicinin disk önbelleği kullanılmıyor:  %s güvenli değil", kok)
            return False
        k = os.path.join(kok, imza)
        os.makedirs(k, mode=0o700, exist_ok=True)
        for ad in os.listdir(kok):
            if ad != imza:
                shutil.rmtree(os.path.join(kok, ad), ignore_errors=True)
        return k
    except OSError:
        log.warning("seçicinin disk önbelleği kurulamadı", exc_info=True)
        return False


def _kullanici():
    return os.getuid() if hasattr(os, "getuid") else (os.environ.get("USERNAME") or "x")


_ONBELLEK = _Onbellek()


def _kapiyi_tasi(r, kapi):
    """Seçilen asansörün makine dairesi kapısı kullanıcının bıraktığı yere ( kapi:  { md_kapi_duvar ,
    md_kapi_konum } ).  Çizim orada da temizse istek o kapıyla döner;  değilse istek ( ve çizim )
    eski kapısıyla kalır, sebep "kapi_reddi"nde ( [ metin ] ) — ekran söyler, ayarı kaldırır."""
    if r.get("durum") != "uygun":
        return r
    v = copy.deepcopy(r["istek"])
    v["proje_geneli"].update(kapi)
    asamalar.asama("kapi")
    cizim, aktif, _hesap, _uygun_degil, _olctu = care_uclari.girdi_durumu(v, 0)
    r["sinama"] = r.get("sinama", 0) + 1
    if aktif and not cizim:
        r["istek"] = v
    else:
        r["kapi_reddi"] = list(cizim.values()) or ["Makine dairesi kapısı oraya konamıyor."]
    return r


def _sec_kapisiz(m):
    """sec — makine dairesi kapısının elle ayarı dışında."""
    t0 = time.monotonic()
    r = _sec(m)
    if r["durum"] == "gereken":
        r = _tek_seferde(m, r, t0)
    beyan = {k: _metin(m[k]) for k in BEYAN if m.get(k) not in (None, "")}
    if r["durum"] != "sigmaz" or not beyan:
        return r
    taslak = paketler()[(int(_sayi(m["beyan_yuku"])), m.get("mk_yok") in (True, "true"))]
    kendi = {k: taslak["asansor"].get(k) or _metin(alanlar.ALAN[k].varsayilan) for k in beyan}
    farkli = [k for k in beyan if kendi[k] != beyan[k]]
    if not farkli:
        return r
    #  Paketin kendi askısı ( hızlı — çoğunlukla tek sınama ):  o da kurulamıyorsa sebep beyan değil
    denemeler = [farkli] + ([[k] for k in farkli] if len(farkli) > 1 else [])
    bulunan, sinama = None, r["sinama"]
    for i, degisen in enumerate(denemeler):
        #  Tek değişiklik denemeleri:  bulunamazsa hepsini değiştiren öneri kalır
        with asamalar.alt_is("aski"):
            r2 = _sec({**m, **{k: kendi[k] for k in degisen}})
        sinama += r2["sinama"]
        if r2["durum"] in ("uygun", "gereken"):
            bulunan = degisen
            if i > 0:
                break
        elif i == 0:
            break
    r["sinama"], r["sure"] = sinama, round(time.monotonic() - t0, 2)
    if bulunan is None:
        return r
    return {
        "durum": "beyan",
        "beyan": [
            {"anahtar": k, "etiket": alanlar.ALAN[k].etiket, "eski": beyan[k], "yeni": kendi[k]}
            for k in bulunan
        ],
        "paket": taslak["kimlik"],
        "sinama": sinama,
        "sure": r["sure"],
    }


#  İstenen ölçüyle yeniden seçim en çok bu kadar kez ( _tek_seferde )
AZAMI_YENIDEN = 2


def _tek_seferde(m, r, t0):
    """MİMARA SÖYLENEN ÖLÇÜ TEK SEFERDE YETER ( 14 Kas — tarama:  1250 kg makine dairelide
    "kuyu genişliği 2020" isteniyor, 2020 girilince bu kez 2030 isteniyordu ).  Küçültme
    ( _kucult ) temiz bir yerleşim bulur;  ama mimar o ölçüyü girince seçim baştan yapılır ve
    aynı yerleşime varmayabilir.  İstenen ölçülerle seçim burada bir kez daha yapılır:  yine
    ölçü isteniyorsa o ölçü de listeye girer ( mimarın ilk değerinden ), en çok AZAMI_YENIDEN
    kez.  Yeniden seçim "sığmaz" derse ilk sonuç kalır."""
    ilk = {g["anahtar"]: g["eski"] for g in r["gereken"]}
    for _tur in range(AZAMI_YENIDEN):
        m2 = dict(m)
        for g in r["gereken"]:
            m2[g["anahtar"]] = g["yeni"] if isinstance(g["yeni"], str) else int(round(g["yeni"]))
        with asamalar.alt_is("dogrulama"):
            r2 = _sec(m2)
        r["sinama"] += r2["sinama"]
        if r2["durum"] != "gereken":
            break
        #  Yine ölçü isteniyor:  önceki istekler geçerli kalır, yenileri eklenir / büyür
        yeni = {g["anahtar"]: g for g in r["gereken"]}
        for g in r2["gereken"]:
            ilk.setdefault(g["anahtar"], g["eski"])
            yeni[g["anahtar"]] = {**g, "eski": ilk[g["anahtar"]]}
        r = {**r2, "gereken": list(yeni.values()), "sinama": r["sinama"]}
    r["sure"] = round(time.monotonic() - t0, 2)
    return r


def _on_denetim(m):
    """Aramasız sonuç:  ( durum , alanlar ) — mimari eksik, bu hızda / yükte hazır asansör yok,
    kartın kabini standarda uymuyor — ya da None ( seçici arar ).  _sec ve aranacak_mi aynı
    kuralı kullanır."""
    eksik = [k for k in ZORUNLU if m.get(k) in (None, "")]
    mk_yok = m.get("mk_yok") in (True, "true")
    if not mk_yok and m.get("md_zemini_kotu") in (None, ""):
        eksik.append("md_zemini_kotu")
    if eksik:
        return "eksik", {"eksik": eksik}
    #  Avanın hız listesinde olup uygulamanın listesinde olmayan hızlar ( 1,75 · 3,5 m/s ):
    #  çizim çıkmaz ( kullanıcı kararı, 14 Kas ) — eskiden "geçersiz seçim" hatası görünüyordu
    hizlar = alanlar.ALAN["beyan_hizi"].secenekler
    if not any(_sayili(x) and _sayi(x) == _sayi(m["beyan_hizi"]) for x in hizlar):
        return "paket_yok", {"hiz": True, "hizlar": [x for x in hizlar if _sayili(x)]}
    if (int(_sayi(m["beyan_yuku"])), mk_yok) not in paketler():
        return "paket_yok", {}
    #  Kartın kabini standarda uymuyor ( kabin_nedenleri ):  aranmaz — o kabinle uygulamanın hesabı
    #  ( kabin alanı ) ya da pafta ( kişi ) çelişir.  Kartta paketin kabini seçilince aranır.
    taslak = paketler()[(int(_sayi(m["beyan_yuku"])), mk_yok)]
    nedenler = kabin_nedenleri(taslak, m)
    if nedenler:
        k = kabin(taslak, m)
        beyan = [
            {
                "anahtar": x,
                "etiket": alanlar.ALAN[x].etiket,
                "eski": _metin(k[x]),
                "yeni": taslak["asansor"][x],
            }
            for x in KABIN
            if k[x] != _sayi(taslak["asansor"][x])
        ]
        return "beyan", {
            "beyan_turu": "kabin",
            "beyan": beyan,
            "nedenler": nedenler,
            "paket": taslak["kimlik"],
        }
    return None


def aranacak_mi(m):
    """Sunucunun seçicisi ( korumali ) bu girdi için ŞİMDİ arama yapacak mı:  önbellekte ( bellek
    ya da disk ) sonucu yok ve aramasız bir sonucu da yok ( _on_denetim ).  Arama yapmaz — paketin
    "henüz aranmadı" sorusu için ( 17 Kas )."""
    if _on_denetim(m) is not None or _ONBELLEK.al(_anahtar(m)) is not None:
        return False
    #  Kapısız seçimi hazırsa kapı yalnız taşınır ( tek sınama — _korumali_sec ):  arama değildir
    kapisiz, kapi = _kapisi_ayri(m)
    return not kapi or _ONBELLEK.al(_anahtar(kapisiz)) is None


def _sec(m):
    """sec'in bir denemesi:  m'nin beyanı ( varsa ) değiştirilmeden."""
    t0 = time.monotonic()
    sina = _Sinayici()

    def son(durum, **ek):
        return {"durum": durum, "sinama": sina.sayi, "sure": round(time.monotonic() - t0, 2), **ek}

    on = _on_denetim(m)
    if on is not None:
        durum, ek = on
        return son(durum, **ek)
    mk_yok = m.get("mk_yok") in (True, "true")
    taslak = paketler()[(int(_sayi(m["beyan_yuku"])), mk_yok)]
    asamalar.asama(
        "paket",
        f"{int(_sayi(m['beyan_yuku']))} kg · {'makine dairesiz' if mk_yok else 'makine daireli'} · "
        f"{_etkin_aski(taslak, m)}:1",
    )
    kucuk = _kucuk_oda(taslak, m)
    if kucuk:
        return _kucuk_odada(taslak, m, kucuk)
    sina.oda = _oda_kurali(taslak, m)
    sina.ayar = ayarlar(m)

    def yerlesim(adaylar, kucult=True):
        """Adayları sırayla dener:  olduğu gibi temiz olan → uyarlananlar.  Döner
        ( "uygun" | "gereken" | "sigmaz" , sonucun alanları ).  kucult:  mimardan istenecek ölçüler
        en küçüğe indirilir ( _kucult ) — "gereken"i kullanılmayacak yerleşimde gereksiz."""
        kalan = []
        for ek in adaylar:
            if not sina.var():
                break
            v = _istek(taslak, m, ek)
            d = sina(v)
            secilen = dict(ek)
            if d["bolum"]:
                v, d, s = _urun_ara(v, d, sina)
                secilen.update(s)
            if d["temiz"]:
                return "uygun", dict(istek=v, secimler=secilen, acik_bolumler=d["bolum"])
            kalan.append((v, d, secilen, ek))
        #  Hiçbiri olduğu gibi temiz değil:  adaylar sırayla uyarlanır
        kilit = m.get("kat_kapisi_tipi") not in (None, "")
        buyutuldu = []
        #  Önce yerleşim adımları, olmadıysa aynı aday önce mimardan istenecek ölçüyle ( _oneri_sec )
        for bina_once in (False, True):
            asamalar.asama("olcu" if bina_once else "uyarlama")
            for v, d, secilen, ek in kalan:
                #  Kuyu paketinkinden küçükse çare aranmaz:  paketin ölçüsünden başlanır ( o ölçüde
                #  doğrulanmıştır ), aşağıda en küçüğe indirilir.  Bir kez:  ilk yan adayında
                once = []
                if not bina_once and not buyutuldu and ek.get("agirlik_yeri") != "Arka":
                    buyutuldu.append(True)
                    buyuk = _paket_olcusunde(taslak, m, ek, sina)
                    if buyuk:
                        #  Önce mimarın kuyusunda, yalnız yerleşimle ( kaçıklıklar ):  sığıyorsa ölçü istenmez
                        v1, d1, s1, _g = _uyarla(v, d, sina, kilit, yalniz_yerlesim=True)
                        if d1["temiz"]:
                            v, d, secilen = v1, d1, {**secilen, **s1}
                        else:
                            v, d, secilen, once = buyuk
                v2, d2, s, gereken = _uyarla(v, d, sina, kilit, bina_once)
                #  Uyarlama aynı ölçüyü bir daha büyüttüyse tek satır:  mimarın değeri → son değer
                for g in gereken:
                    ilk = next((x for x in once if x["anahtar"] == g["anahtar"]), None)
                    if ilk:
                        g["eski"] = ilk["eski"]
                gereken = [x for x in once if x["anahtar"] not in {g["anahtar"] for g in gereken}] + gereken
                if d2["temiz"]:
                    secilen = {**secilen, **s}
                    if gereken and kucult:
                        asamalar.asama("kucultme")
                        v2, d2, gereken = _kucult(v2, d2, gereken, sina, taslak, kilit)
                        secilen = {
                            k: x if v2["asansorler"][0].get(k) is None else v2["asansorler"][0][k]
                            for k, x in secilen.items()
                        }
                    #  Uyarlama yerleşimi değiştirdi:  ürün bölümleri bir kez daha aranır ( sıkı )
                    if d2["bolum"]:
                        v2, d2, s = _urun_ara(v2, d2, sina)
                        secilen.update(s)
                    ortak = dict(istek=v2, secimler=secilen, acik_bolumler=d2["bolum"])
                    return ("gereken", dict(gereken=gereken, **ortak)) if gereken else ("uygun", ortak)
        _v, d, _s, _ek = kalan[0]
        nedenler = list(d["cizim"].values()) + d["hesap"] + [f"bölüm:{b}" for b in d["engel"]]
        return "sigmaz", dict(nedenler=nedenler)

    #  YERLEŞİM ADAYLARI.  Yan:  kabin ağırlığın yanında ( ölçülen çare ), sonra pakette olduğu
    #  gibi.  Arka ( kullanıcı kararı 14 Kas ):  dar ve derin kuyu.  Hangisi önce ( _once_arka ):
    #  makine daireli 1:1 askıda arka, öbürlerinde yan ( kullanıcı, 13 Kas ).  Sıra:  ilki uygun →
    #  ikincisi uygun → ilki ( mimardan istenecek ) → ikincisi ( mimardan istenecek ) → sığmaz;
    #  mimarın bugünkü kuyusuna sığan yerleşim, mimardan ölçü istemekten önce gelir ( benim yorumum ).
    kay = _kaydirma(taslak, m)
    yan = ([{"kabin_yana_kaciklik": round(kay)}] if kay is not None else []) + [{}]
    arka = _arka_adayi(taslak, m)
    sira = [yan] if arka is None else ([[arka], yan] if _once_arka(taslak, m) else [yan, [arka]])

    def yer(adaylar):
        return "ağırlık arkada" if adaylar[0] is arka else "ağırlık yanda"

    asamalar.asama("yerlesim", yer(sira[0]))
    durum, alanlar_ = yerlesim(sira[0])
    if durum != "uygun" and len(sira) > 1:
        sina.kalan = AZAMI_SINAMA
        asamalar.asama("yerlesim", yer(sira[1]))
        #  İlki mimardan ölçü istiyorsa ikincisinin yalnız "uygun"u kullanılır:  onun istediği ölçüler
        #  küçültülmez ( 24 Kas — kot da küçültülünce boşa giden arama seçimin süresini ikiye katlıyordu )
        durum_2, alanlar_2 = yerlesim(sira[1], kucult=durum == "sigmaz")
        if durum_2 == "uygun" or (durum_2 == "gereken" and durum == "sigmaz"):
            durum, alanlar_ = durum_2, alanlar_2
    return son(durum, paket=taslak["kimlik"], **alanlar_)


def _kucuk_oda(taslak, m):
    """Mimarın makine dairesinin hazır asansörünkinden küçük ölçüleri → { alan:  hazır asansörünki }."""
    pg = taslak["proje_geneli"]
    if m.get("mk_yok") in (True, "true"):
        return {}
    return {
        k: pg[k] for k in ODA_KUYU if m.get(k) not in (None, "") and k in pg and _sayi(m[k]) < _sayi(pg[k])
    }


def _kucuk_odada(taslak, m, kucuk):
    """MAKİNE DAİRESİ ( 13 Kas ):  mimarın odası hazır asansörünkinden küçük.  Çare bulucu oda
    ölçüsü önermez;  küçük odada asansör "sığmaz" çıkıyor, sebep olarak da kuyu gösteriliyordu.
    Asansör önce hazır asansörün odasıyla seçilir ( o ölçüde doğrulanmıştır ), sonra mimarın
    odasına konur:  olduğu gibi ya da bir – iki yerleşim adımıyla ( pano / kapı duvarı ) temizse
    oda yetiyordur;  değilse odanın ölçüsü de mimardan istenir, en küçüğe indirilerek
    ( _kucult — yalnız sınama ).  Döner _sec'in sonucu."""
    t0 = time.monotonic()
    r = _sec({**m, **kucuk})
    if r["durum"] not in ("uygun", "gereken"):
        return r
    asamalar.asama("oda")
    sina = _Sinayici()
    sina.ayar = ayarlar(m)
    buyuk = r["istek"]
    v = buyuk
    for k in kucuk:
        v = care_uclari.girdi_yaz(v, 0, k, _metin(m[k]))
    d = sina(v)
    secilen = {}
    if not d["temiz"] and d["cizim"]:
        v, d, secilen, _g = _uyarla(v, d, sina, yalniz_yerlesim=True, adim=2)
    gereken = []
    if not d["temiz"]:
        d = sina(buyuk)
        gereken = [
            {
                "anahtar": k,
                "etiket": alanlar.ALAN[k].etiket,
                "eski": _metin(m[k]),
                "yeni": _sayi(x),
                "sebep": "Makine ve kumanda panosu daha küçük makine dairesine sığmıyor.",
            }
            for k, x in kucuk.items()
        ]
        v, d, gereken = _kucult(buyuk, d, gereken, sina, taslak, anahtarlar=tuple(ODA_KUYU))
        secilen = {}
    gereken = r.get("gereken", []) + gereken
    return {
        **r,
        "durum": "gereken" if gereken else "uygun",
        **({"gereken": gereken} if gereken else {}),
        "istek": v,
        "secimler": {**r["secimler"], **secilen},
        "acik_bolumler": d["bolum"],
        "sinama": r["sinama"] + sina.sayi,
        "sure": round(time.monotonic() - t0, 2),
    }


def _etkin_aski(taslak, m):
    """Asansörün askı oranı ( "1" | "2" ):  avanın beyanı, yoksa paketinki, yoksa formun varsayılanı."""
    aski = (
        m.get("aski_orani") if m.get("aski_orani") not in (None, "") else taslak["asansor"].get("aski_orani")
    )
    return _metin(aski if aski not in (None, "") else alanlar.ALAN["aski_orani"].varsayilan)


def _once_arka(taslak, m):
    """Karşı ağırlık önce arkada mı denenir:  makine daireli 1:1 askıda ( kullanıcı, 13 Kas ).
    Makine dairesiz 2:1'de ve öbür birleşimlerde önce yan."""
    return m.get("mk_yok") not in (True, "true") and _etkin_aski(taslak, m) == "1"


def _arka_adayi(taslak, m):
    """Paketin yandaki karşı ağırlığını arkaya alan aday ( ek girdiler ) ya da None:  paketin
    ağırlığı zaten arkada.  Programın arka yerleşim kuralları ( cizim/kopru ):  2:1 askıda
    kasnaklar kabin üstünde ( çapraz ), makine dairesizde makine duvardan duvara kirişe oturur
    ( yük bina yapısına ).  Kabin ortalanır;  kalanı uyarlama bulur ( kapı kaçıklığı … )."""
    a = taslak["asansor"]
    if a.get("agirlik_yeri", alanlar.ALAN["agirlik_yeri"].varsayilan) == "Arka":
        return None
    ek = {"agirlik_yeri": "Arka", "kabin_yana_kaciklik": 0}
    if _etkin_aski(taslak, m) == "2":
        ek["aski_duzeni"] = "Kabin üstü"
    if m.get("mk_yok") in (True, "true"):
        ek["makine_raya_biniyor"] = "Bina yapısına"
    return ek
