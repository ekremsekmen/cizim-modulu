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
MIMARI = ("kuyu_genisligi", "kuyu_derinligi", *KOTLAR)
MIMARI_GENEL = ("mk_uzunluk", "mk_genislik")
#  Avanın BEYANI ( kartın askı oranı ve makine tipi — avan motor hesabının girdileri ):
#  verilmişse paketinkinin yerine geçer, seçici değiştirmez
BEYAN = ("aski_orani", "makine_tipi")
ZORUNLU = ("beyan_yuku", "beyan_hizi", "kuyu_genisligi", "kuyu_derinligi", *KOTLAR[:3])

#  Avan projesini bağlayan bölümler:  kuyunun ölçülerine ( kuyu üstü, kuyu dibi ) ve
#  kabine bakanlar.  Kalanı ürün hesabıdır — uygulama projesinde çözülür.
AVAN_BOLUMLERI = frozenset(("siginma_alanlari", "kabin_alani", "tamponlar"))

#  Bir seçimde en çok bu kadar hesap + çizim sınaması ( biri ~0,1 sn )
AZAMI_SINAMA = 120
#  Uyarlamada ( yerleşim çaresi, mimardan istenecek ölçü ) en çok bu kadar adım ve süre ( sn )
AZAMI_ADIM = 6
AZAMI_SURE = 12.0
#  Beyan çelişkisinde "yalnız şunu değiştirin" denemelerinin süresi ( sn )
TEK_SURE = 4.0
#  Seçicinin değiştirmediği:  trafik hesabının kapasitesi ( kabin ), kapı, yük, hız
SABIT = frozenset(
    ("beyan_yuku", "beyan_hizi", "kabin_genisligi", "kabin_derinligi", "kabin_ic_yuksekligi")
    + ("kapi_genisligi", "kapi_yuksekligi", "durak_adedi", "seyir_mesafesi")
    + BEYAN
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
    "tamponlar": (("tampon_tipi", (alanlar.ALAN["tampon_tipi"].secenekler[2],)),),
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
                if bugun in (None, ""):
                    bugun = alanlar.ALAN[anahtarlar[0]].varsayilan
                for x in degerler:
                    if not sina.var():
                        return v, d, secilen
                    if _metin(x) == (bugun if isinstance(bugun, str) else _metin(bugun)):
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


def _oneri_sec(v):
    """Çare bulucunun ( care_uclari.coz ) önerilerinden sıradaki adım:  önce YERLEŞİM
    ( kaçıklıklar, kapı tipi — seçicinin kendi kararı ), sonra BİNA ( mimardan istenir );
    ikisinde de başka sorun açmayan önce.  Kabin, kapı genişliği, yük, hız değişmez;
    otomatik kapı elle açılan kapıya çevrilmez."""
    oneriler = [
        o
        for c in care_uclari.coz(v, 0)["careler"]
        for o in c["oneriler"]
        if o["anahtar"] not in SABIT and not str(o["yeni"]).startswith("Manuel")
    ]
    oneriler.sort(key=lambda o: (bool(o["ortaya_cikan"] or o["hesapta_ortaya_cikan"]), o["bina"]))
    return oneriler[0] if oneriler else None


def _uyarla(v, d, sina, bitis):
    """Sorunlu adayı adım adım temize çeker:  ürün ( gevşek ) → çare bulucunun önerisi.
    Döner ( istek , durum , seçilenler , gereken listesi )."""
    secilen, gereken, ilk = {}, {}, v
    for _adim in range(AZAMI_ADIM):
        if not d["temiz"] and d["engel"]:
            v, d, s = _urun_ara(v, d, sina, gevsek=True)
            secilen.update(s)
        if d["temiz"] or not d["cizim"] or not sina.var() or time.monotonic() > bitis:
            break
        oneri = _oneri_sec(v)
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
            secilen[oneri["anahtar"]] = v["asansorler"][0].get(oneri["anahtar"])
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

    #  YERLEŞİM ADAYLARI:  kabin ağırlığın yanında ( ölçülen çare ), sonra pakette olduğu gibi
    kay = _kaydirma(taslak, m)
    adaylar = ([{"kabin_yana_kaciklik": round(kay)}] if kay is not None else []) + [{}]
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
            return son("uygun", istek=v, secimler=secilen, acik_bolumler=d["bolum"], paket=taslak["kimlik"])
        kalan.append((v, d, secilen))

    #  Hiçbiri olduğu gibi temiz değil:  adaylar sırayla uyarlanır
    bitis = t0 + azami_sure
    for v, d, secilen in kalan:
        v2, d2, s, gereken = _uyarla(v, d, sina, bitis)
        if d2["temiz"]:
            secilen.update(s)
            #  Uyarlama yerleşimi değiştirdi:  ürün bölümleri bir kez daha aranır ( sıkı )
            if d2["bolum"]:
                v2, d2, s = _urun_ara(v2, d2, sina)
                secilen.update(s)
            ortak = dict(istek=v2, secimler=secilen, acik_bolumler=d2["bolum"], paket=taslak["kimlik"])
            return son("gereken", gereken=gereken, **ortak) if gereken else son("uygun", **ortak)
    _v, d, _s = kalan[0]
    nedenler = list(d["cizim"].values()) + d["hesap"] + [f"bölüm:{b}" for b in d["engel"]]
    return son("sigmaz", nedenler=nedenler, paket=taslak["kimlik"])
