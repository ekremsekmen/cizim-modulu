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
  · Kabin trafik hesabının kapasitesinde kalır:  paketin kabini değişmez, kuyu
    büyükse fazlası boşluktur.
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

import copy
import json
import os
import time

from cizim import katlar
from motor.avan import tablolar
from tasarim import alanlar
from uclar import care_uclari
from yollar import KOK

with open(os.path.join(KOK, "on-yuz", "src", "lib", "taslaklar.json"), encoding="utf-8") as _f:
    _TASLAKLAR = json.load(_f)

#  Mimarın verdikleri:  pakette ne yazarsa yazsın bunlar mimardan gelir
KOTLAR = (alanlar.DURAK_KOTLARI, "kuyu_dibi_kotu", "kuyu_tavani_kotu", "md_zemini_kotu")
#  Kat adları ve giriş katı ( kot tablosu — 13 Kas ):  kotlarla birlikte mimardan
ADLAR = (alanlar.DURAK_ADLARI, alanlar.GIRIS_DURAGI)
#  Tavan döşemesinin kalınlığı ( mimarın kesitinden — boşsa uygulamanın kuralı )
MIMARI = ("kuyu_genisligi", "kuyu_derinligi", *KOTLAR, *ADLAR, "tavan_dosemesi")
MIMARI_GENEL = ("mk_uzunluk", "mk_genislik")
#  Avanın BEYANI ( kartın askı oranı ve makine tipi — avan motor hesabının girdileri ):
#  verilmişse paketinkinin yerine geçer, seçici değiştirmez
#  ( 14 Kas ) kapı genişliği ve tipi de:  trafik hesabının kapısı ( kullanıcı kararı )
BEYAN = ("aski_orani", "makine_tipi", "kapi_genisligi", "kat_kapisi_tipi")
ZORUNLU = ("beyan_yuku", "beyan_hizi", "kuyu_genisligi", "kuyu_derinligi", *KOTLAR[:3])

#  Avan projesini bağlayan bölümler:  kuyunun ölçülerine ( kuyu üstü, kuyu dibi ) ve
#  kabine bakanlar.  Kalanı ürün hesabıdır — uygulama projesinde çözülür.
AVAN_BOLUMLERI = frozenset(("siginma_alanlari", "kabin_alani", "tamponlar"))

#  Bir seçimde en çok bu kadar hesap + çizim sınaması ( biri ~0,1 sn )
AZAMI_SINAMA = 120
#  Uyarlamada ( yerleşim çaresi, mimardan istenecek ölçü ) en çok bu kadar adım ve süre ( sn )
AZAMI_ADIM = 6
AZAMI_SURE = 12.0
#  İkinci yerleşim denemesinin ( önce yan denendiyse arka, önce arka denendiyse yan )
#  uyarlama süresi:  asıl sürenin bu kadarı ( ölçülen arka uyarlamaları 1 – 3 sn;  ilki zaten
#  "mimardan istenecek" bulduysa uzun beklenmez )
IKINCI_SURE_PAYI = 0.5
#  Beyan çelişkisinde "yalnız şunu değiştirin" denemelerinin süresi ( sn )
TEK_SURE = 4.0
#  MİMARDAN İSTENECEK ÖLÇÜNÜN KÜÇÜLTÜLMESİ ( 13 Kas ):  çare bulucunun adım adım topladığı
#  kuyu ölçüsü gereğinden büyük çıkabiliyordu ( 630 kg 1800 genişliğe sığarken 2110 isteniyordu ).
#  Bulunan ölçü ile mimarınki arasında, bu adımın katlarında ( mm ) ikili arama;  her deneme
#  hesap + çizimle sınanır;  genişlikte ayrıca en çok bu kadar yerleşim adımlı deneme ( _kucult ).
KUCULEN = ("kuyu_genisligi", "kuyu_derinligi")
KUCULTME_ADIMI = 10
KUCULTME_YERLESIM = 3
#  Paketinkinden küçük kuyuda, ölçü istemeden önce yalnız yerleşimle sığdırma denemesinin süresi ( sn )
YERLESIM_SURESI = 4.0
#  Seçicinin değiştirmediği:  trafik hesabının kapasitesi ( kabin ), kapı, yük, hız
SABIT = frozenset(
    ("beyan_yuku", "beyan_hizi", "kabin_genisligi", "kabin_derinligi", "kabin_ic_yuksekligi")
    + ("kapi_genisligi", "kapi_yuksekligi", "durak_adedi", "seyir_mesafesi")
    + ("aski_orani", "makine_tipi")
)

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
        (int(t["asansor"]["beyan_yuku"]), t["proje_geneli"].get("mk_yok") == "true"): t for t in _TASLAKLAR
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


def _istek(taslak, m, ek=None):
    """Paket + mimarın kuyusu ( + denenen değerler ) → uygulamanın isteği."""
    a = {k: v for k, v in taslak["asansor"].items() if k not in MIMARI}
    pg = {k: v for k, v in taslak["proje_geneli"].items() if k not in MIMARI_GENEL}
    for k in ("beyan_hizi", *MIMARI, *BEYAN):
        if m.get(k) not in (None, ""):
            a[k] = _metin(m[k])
    for k in MIMARI_GENEL:
        if m.get(k) not in (None, "") and pg.get("mk_yok") != "true":
            pg[k] = _metin(m[k])
    #  Makine dairesinin ölçüsü verilmediyse paketinki ( formun kuralı )
    for k in MIMARI_GENEL:
        if k not in pg and k in taslak["proje_geneli"]:
            pg[k] = taslak["proje_geneli"][k]
    a.update({k: _metin(v) for k, v in (ek or {}).items()})
    return {"asansorler": [a], "proje_geneli": pg, "sabitler": {}, "asansor": 0}


def _kaydirma(taslak, m):
    """Kabinin yana kaçıklığı:  kabin – karşı ağırlık duvarı aralığı paketteki
    gibi kalsın.  Ağırlık arkadaysa kabin ortada kalır ( None:  dokunma )."""
    a = taslak["asansor"]
    yon = {"Sağ": 1, "Sol": -1}.get(a.get("agirlik_yeri", alanlar.ALAN["agirlik_yeri"].varsayilan))
    if yon is None:
        return None
    fark = _sayi(m["kuyu_genisligi"]) - _sayi(a["kuyu_genisligi"])
    return _sayi(a.get("kabin_yana_kaciklik") or 0) + yon * fark / 2.0


class _Sinayici:
    """Hesap + çizim sınaması, sayarak ( care_uclari.girdi_durumu )."""

    def __init__(self):
        self.kalan = AZAMI_SINAMA
        self.sayi = 0

    def __call__(self, v):
        self.kalan -= 1
        self.sayi += 1
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


def _oneri_sec(v, kapi_kilidi=False, bina_once=False, yalniz_yerlesim=False):
    """Çare bulucunun ( care_uclari.coz ) önerilerinden sıradaki adım:  önce YERLEŞİM
    ( kaçıklıklar, kapı tipi — seçicinin kendi kararı ), sonra BİNA ( mimardan istenir );
    ikisinde de başka sorun açmayan önce.  Kabin, kapı genişliği, yük, hız değişmez;
    otomatik kapı elle açılan kapıya çevrilmez.

    bina_once:  sıra tersine — önce mimardan istenecek ölçü.  Yerleşim adımı ( kaçıklık ) bazen
    sorunu yalnız kabini küçülterek çözülür hâle getirir ( kabin değişmez → çıkmaz );  aynı
    aday bu sırayla bir kez daha denenir ( _sec.yerlesim )."""
    oneriler = [
        o
        for c in care_uclari.coz(v, 0)["careler"]
        for o in c["oneriler"]
        if o["anahtar"] not in SABIT
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


def _uyarla(v, d, sina, bitis, kapi_kilidi=False, bina_once=False, yalniz_yerlesim=False, adim=AZAMI_ADIM):
    """Sorunlu adayı adım adım temize çeker:  ürün ( gevşek ) → çare bulucunun önerisi.
    Döner ( istek , durum , seçilenler , gereken listesi )."""
    secilen, gereken, ilk = {}, {}, v
    for _adim in range(adim):
        if not d["temiz"] and d["engel"]:
            v, d, s = _urun_ara(v, d, sina, gevsek=True)
            secilen.update(s)
        if d["temiz"] or not d["cizim"] or not sina.var() or time.monotonic() > bitis:
            break
        oneri = _oneri_sec(v, kapi_kilidi, bina_once, yalniz_yerlesim)
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


def _paket_olcusunde(taslak, m, ek, sina):
    """Mimarın kuyusu paketinkinden dar / sığ ise aynı aday paketin kuyu ölçüsüyle ( kabin
    yine ağırlığın yanında ).  Döner ( istek , durum , seçilenler , gereken ) ya da None:
    kuyu paketinkinden küçük değil."""
    a = taslak["asansor"]
    buyuyen = {k: a[k] for k in KUCULEN if _sayi(m[k]) < _sayi(a[k])}
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
            "sebep": "Bu kapasitenin kabini ve karşı ağırlığı daha küçük kuyuya sığmıyor.",
        }
        for k, x in buyuyen.items()
    ]
    return v, d, secilen, gereken


def _kucult(v, d, gereken, sina, taslak, kapi_kilidi=False, anahtarlar=KUCULEN):
    """Mimardan istenecek kuyu ölçülerini ( KUCULEN ) temiz kalan en küçük değere indirir.
    Döner ( istek , durum , gereken ).  Genişlik denenirken kabin de ağırlığın yanına yeniden
    kaydırılır ( _kaydirma — uyarlamanın başındaki kaydırma mimarın ilk genişliği içindi ).
    Mimarın kendi ölçüsü de temizse o ölçü istenmez ( listeden düşer ).

    İki aşama, ikisi de saate bakmaz ( sonuç makinenin hızına göre değişmez ):
      1  ikili arama, yalnız sınama ( hızlı );
      2  genişlikte, bulunanın altında en çok KUCULTME_YERLESIM deneme daha — her birinde bir
         yerleşim adımı ( çare bulucu:  kapı kaçıklığı dar kuyuda kapıyı yerinde tutar )."""
    yanda = v["asansorler"][0].get("agirlik_yeri", taslak["asansor"].get("agirlik_yeri")) == taslak[
        "asansor"
    ].get("agirlik_yeri")
    sonsuz = float("inf")

    def dene(anahtar, x, yerlesim):
        y = care_uclari.girdi_yaz(v, 0, anahtar, x)
        adaylar = [y]
        if anahtar == "kuyu_genisligi" and yanda:
            kay = _kaydirma(taslak, {"kuyu_genisligi": x})
            if kay is not None:
                adaylar.insert(0, care_uclari.girdi_yaz(y, 0, "kabin_yana_kaciklik", round(kay)))
        for i, y in enumerate(adaylar):
            if not sina.var():
                return None
            dy = sina(y)
            if yerlesim and i == 0 and not dy["temiz"] and dy["cizim"] and not dy["engel"]:
                y, dy, _s, _g = _uyarla(y, dy, sina, sonsuz, kapi_kilidi, yalniz_yerlesim=True, adim=1)
            #  Temiz ve yeni bir ürün bölümü de düşürmüyor
            if dy["temiz"] and set(dy["bolum"]) <= set(d["bolum"]):
                return y, dy
        return None

    #  Önce derinlik, sonra genişlik
    for g in sorted(
        (g for g in gereken if g["anahtar"] in anahtarlar and _sayili(g["eski"])),
        key=lambda g: g["anahtar"] != "kuyu_derinligi",
    ):
        alt, ust = _sayi(g["eski"]), _sayi(g["yeni"])
        n = int(-(-(ust - alt) // KUCULTME_ADIMI))
        if n < 1:
            continue
        #  alt + k · adım:  k = n bulunan ölçü ( temiz ), k = 0 mimarınki.  En küçük temiz k aranır
        dusuk, yuksek = -1, n
        while yuksek - dusuk > 1:
            k = 0 if dusuk < 0 and yuksek == n else (dusuk + yuksek) // 2
            sonuc = dene(g["anahtar"], alt + k * KUCULTME_ADIMI, False)
            if sonuc is None:
                dusuk = k
            else:
                yuksek, (v, d) = k, sonuc
        if g["anahtar"] == "kuyu_genisligi":
            #  k = 0 ( mimarın genişliği ) yerleşimle zaten denendi ( _sec.yerlesim ) — sığmıyor
            dusuk = 0
            for _deneme in range(KUCULTME_YERLESIM):
                if yuksek - dusuk <= 1:
                    break
                k = (dusuk + yuksek) // 2
                sonuc = dene(g["anahtar"], alt + k * KUCULTME_ADIMI, True)
                if sonuc is None:
                    dusuk = k
                else:
                    yuksek, (v, d) = k, sonuc
        if yuksek < n:
            g["yeni"] = alt + yuksek * KUCULTME_ADIMI
    return (
        v,
        d,
        [g for g in gereken if not (g["anahtar"] in anahtarlar and _sayi(g["yeni"]) <= _sayi(g["eski"]))],
    )


def _kot_metni(deger):
    """Çare bulucunun kot önerisi ( m, sayı ) → formun yazımı ( "+19,37" )."""
    return katlar.kot_metni(round(float(deger) * 1000)) if not isinstance(deger, str) else deger


def sec(m):
    """Mimarın kuyusuna asansör.

    m:  beyan_yuku ( kg ), beyan_hizi, kuyu_genisligi, kuyu_derinligi, durak_kotlari,
        kuyu_dibi_kotu, kuyu_tavani_kotu, mk_yok;  makine dairesi varsa md_zemini_kotu,
        isteğe bağlı mk_uzunluk / mk_genislik;  isteğe bağlı avanın beyanı ( BEYAN:
        aski_orani, makine_tipi ) — verilmişse istekte aynen durur.

    Döner { durum , … }:
      "uygun"      istek ( uygulamanın isteği — çizimi ve avanı bağlayan bölümleri temiz ),
                   secimler, acik_bolumler ( geçirilemeyen ürün bölümleri — çoğunlukla boş )
      "gereken"    gereken [ { anahtar , etiket , eski , yeni , sebep } ] — mimarın
                   ölçüleri böyle olursa temiz;  istek o ölçülerle
      "sigmaz"     nedenler [ metin ] — mimardan istenecek ölçü de bulunamadı
      "paket_yok"  bu yük / düzen için paket yok
      "eksik"      eksik [ anahtar ] — mimari girdi eksik
      "beyan"      beyan [ { anahtar , etiket , eski , yeni } ] — avanın beyanıyla asansör
                   kurulamadı;  kartta bunlar seçilirse kurulur ( doğrulanmış, en az değişiklik )
    Hepsinde sinama ( sayı ) ve sure ( sn )."""
    t0 = time.monotonic()
    r = _sec(m)
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
        #  Dört beyan da farklıysa tek tek denemek uzar:  toplam süre dolunca kalınır
        if i > 0 and time.monotonic() - t0 > 2 * AZAMI_SURE:
            break
        #  Tek değişiklik denemeleri kısa sürelidir:  bulunamazsa hepsini değiştiren öneri kalır
        r2 = _sec({**m, **{k: kendi[k] for k in degisen}}, AZAMI_SURE if i == 0 else TEK_SURE)
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


def _sec(m, azami_sure=AZAMI_SURE):
    """sec'in bir denemesi:  m'nin beyanı ( varsa ) değiştirilmeden."""
    t0 = time.monotonic()
    sina = _Sinayici()

    def son(durum, **ek):
        return {"durum": durum, "sinama": sina.sayi, "sure": round(time.monotonic() - t0, 2), **ek}

    eksik = [k for k in ZORUNLU if m.get(k) in (None, "")]
    mk_yok = m.get("mk_yok") in (True, "true")
    if not mk_yok and m.get("md_zemini_kotu") in (None, ""):
        eksik.append("md_zemini_kotu")
    if eksik:
        return son("eksik", eksik=eksik)
    taslak = paketler().get((int(_sayi(m["beyan_yuku"])), mk_yok))
    if taslak is None:
        return son("paket_yok")
    kucuk = _kucuk_oda(taslak, m)
    if kucuk:
        return _kucuk_odada(taslak, m, kucuk, azami_sure)

    def yerlesim(adaylar, sure=azami_sure):
        """Adayları sırayla dener:  olduğu gibi temiz olan → uyarlananlar.  Döner
        ( "uygun" | "gereken" | "sigmaz" , sonucun alanları )."""
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
        bitis = time.monotonic() + sure
        kilit = m.get("kat_kapisi_tipi") not in (None, "")
        buyutuldu = []
        #  Önce yerleşim adımları, olmadıysa aynı aday önce mimardan istenecek ölçüyle ( _oneri_sec )
        for bina_once in (False, True):
            for v, d, secilen, ek in kalan:
                if bina_once and time.monotonic() > bitis:
                    break
                #  Kuyu paketinkinden küçükse çare aranmaz:  paketin ölçüsünden başlanır ( o ölçüde
                #  doğrulanmıştır ), aşağıda en küçüğe indirilir.  Bir kez:  ilk yan adayında
                once = []
                if not bina_once and not buyutuldu and ek.get("agirlik_yeri") != "Arka":
                    buyutuldu.append(True)
                    buyuk = _paket_olcusunde(taslak, m, ek, sina)
                    if buyuk:
                        #  Önce mimarın kuyusunda, yalnız yerleşimle ( kaçıklıklar ):  sığıyorsa ölçü istenmez
                        v1, d1, s1, _g = _uyarla(
                            v,
                            d,
                            sina,
                            min(bitis, time.monotonic() + YERLESIM_SURESI),
                            kilit,
                            yalniz_yerlesim=True,
                        )
                        if d1["temiz"]:
                            v, d, secilen = v1, d1, {**secilen, **s1}
                        else:
                            v, d, secilen, once = buyuk
                v2, d2, s, gereken = _uyarla(v, d, sina, bitis, kilit, bina_once)
                #  Uyarlama aynı ölçüyü bir daha büyüttüyse tek satır:  mimarın değeri → son değer
                for g in gereken:
                    ilk = next((x for x in once if x["anahtar"] == g["anahtar"]), None)
                    if ilk:
                        g["eski"] = ilk["eski"]
                gereken = [x for x in once if x["anahtar"] not in {g["anahtar"] for g in gereken}] + gereken
                if d2["temiz"]:
                    secilen = {**secilen, **s}
                    if gereken:
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
    durum, alanlar_ = yerlesim(sira[0])
    if durum != "uygun" and len(sira) > 1:
        sina.kalan = AZAMI_SINAMA
        durum_2, alanlar_2 = yerlesim(sira[1], azami_sure * IKINCI_SURE_PAYI)
        if durum_2 == "uygun" or (durum_2 == "gereken" and durum == "sigmaz"):
            durum, alanlar_ = durum_2, alanlar_2
    return son(durum, paket=taslak["kimlik"], **alanlar_)


def _kucuk_oda(taslak, m):
    """Mimarın makine dairesinin hazır asansörünkinden küçük ölçüleri → { alan:  hazır asansörünki }."""
    pg = taslak["proje_geneli"]
    if m.get("mk_yok") in (True, "true"):
        return {}
    return {
        k: pg[k]
        for k in MIMARI_GENEL
        if m.get(k) not in (None, "") and k in pg and _sayi(m[k]) < _sayi(pg[k])
    }


def _kucuk_odada(taslak, m, kucuk, azami_sure):
    """MAKİNE DAİRESİ ( 13 Kas ):  mimarın odası hazır asansörünkinden küçük.  Çare bulucu oda
    ölçüsü önermez;  küçük odada asansör "sığmaz" çıkıyor, sebep olarak da kuyu gösteriliyordu.
    Asansör önce hazır asansörün odasıyla seçilir ( o ölçüde doğrulanmıştır ), sonra mimarın
    odasına konur:  olduğu gibi ya da bir – iki yerleşim adımıyla ( pano / kapı duvarı ) temizse
    oda yetiyordur;  değilse odanın ölçüsü de mimardan istenir, en küçüğe indirilerek
    ( _kucult — yalnız sınama ).  Döner _sec'in sonucu."""
    t0 = time.monotonic()
    r = _sec({**m, **kucuk}, azami_sure)
    if r["durum"] not in ("uygun", "gereken"):
        return r
    sina = _Sinayici()
    buyuk = r["istek"]
    v = buyuk
    for k in kucuk:
        v = care_uclari.girdi_yaz(v, 0, k, _metin(m[k]))
    d = sina(v)
    secilen = {}
    if not d["temiz"] and d["cizim"]:
        bitis = time.monotonic() + YERLESIM_SURESI
        v, d, secilen, _g = _uyarla(v, d, sina, bitis, yalniz_yerlesim=True, adim=2)
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
        v, d, gereken = _kucult(buyuk, d, gereken, sina, taslak, anahtarlar=MIMARI_GENEL)
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
