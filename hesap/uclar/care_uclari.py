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

BÜTÇE SINAMA SAYISIDIR, SAAT DEĞİL ( _Butce;  20 Eki ):  aynı proje her
bilgisayarda, her seferinde aynı çareleri alır.  Saat yalnız güvenlik
sınırıdır;  ona ya da sayıya takılan arama yanıtta "tamamlandi: false" der.
"""

import copy
import logging
import math
import re
import time

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from cizim import istek_onbellegi
from cizim import izli
from cizim import sorun
from motor.uygulama import uygulama_hesabi
from uclar import cizim_uclari
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
#  kurulmasıdır, _durum ).  Eskiden 6 sn'lik duvar saatiydi:  arama makinenin o
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
}
#  Sayı seçenekli seçim ( kapı genişliği ):  yalnız komşu seçenekler
KOMSU_SECIM = {"kapi_genisligi": SECIMLER["kat_kapisi_tipi"]}
#  Bir istekte en çok sınanan seçim
AZAMI_SECIM = 12


def kimlik(metin):
    """Sorunun kimliği:  ilk iki noktaya kadarki kısmı, sayılar atılmış.  Değer
    değişince metnin sonu değişebilir ( "üst pateni tepesi 3599,6" →
    "çerçevesi tepesi 3610" ) — aynı sorundur."""
    return re.sub(r"-?\d+(?:[.,]\d+)?", "#", str(metin).split(":", 1)[0]).strip()


def _durum(veri, i):
    """Bir girdinin hükmü:  ( çizim sorunları { kimlik:  metin } , hesap
    çalıştı mı , hesabın sorun kimlikleri , uygun olmayan bölüm sayısı )."""
    with istek_onbellegi.etkin():
        asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
        _g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, s if s.get("aktif") else None, "", i)
    a = s["asansorler"][i]
    uygun_degil = sum(1 for b in a.get("bolumler") or [] if (b.get("sonuc") or {}).get("uygun") is False)
    return (
        {kimlik(h): str(h) for h in hata},
        bool(a.get("aktif")),
        {kimlik(h) for h in a.get("hata") or []},
        uygun_degil,
    )


class _Butce:
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
        """_durum — bütçeden bir sınama düşerek."""
        self.kalan -= 1
        return _durum(veri, i)


def _yaz(veri, i, anahtar, deger):
    """Girdinin bir kutusu değişmiş kopyası ( proje geneli alan proje genelinde )."""
    y = copy.deepcopy(veri)
    yer = (
        y.setdefault("proje_geneli", {})
        if anahtar in uygulama_istegi.PROJE_GENELI_ALANLAR
        else y["asansorler"][i]
    )
    yer[anahtar] = deger if isinstance(deger, str) else f"{deger:g}"
    return y


def _sonucu(once, sonra, ortulu=frozenset()):
    """Bir değişikliğin hükmü:  { gider ( kimlikler ) , yeni , ortaya ( gizliyken
    görünür olan — yeni sayılmaz ) , kotu }.  ortulu:  bugün de var olan ama
    denetim ilk hatada durduğu için görünmeyen sorunların kimlikleri
    ( cizim_uclari.genis_sorunlar )."""
    s0, h0, hk0, u0 = once
    s1, h1, hk1, u1 = sonra
    kotu = (h0 and not h1) or (not h0 and not h1 and not hk1 <= hk0 | ortulu) or (h0 and h1 and u1 > u0)
    return {
        "gider": [k for k in s0 if k not in s1],
        "yeni": [s1[k] for k in s1 if k not in s0 and k not in ortulu],
        "ortaya": [s1[k] for k in s1 if k not in s0 and k in ortulu],
        "kotu": bool(kotu),
    }


def _kabul(r, hedef):
    return hedef in r["gider"] and not r["yeni"] and not r["kotu"]


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
    kabul, denenen = [], set()
    for k, adim in secilen:
        for carpan in (1.0,) + YENIDEN:
            v = _deger(degerler[k], adim, carpan, alan[k]["birim"])
            if (k, v) in denenen or not _form_kurali_uyar(k, v, alan):
                continue
            if not butce.var():
                return kabul
            denenen.add((k, v))
            r = _sonucu(once, butce.durum(_yaz(veri, i, k, v), i), ortulu)
            if not r["yeni"] and not r["kotu"] and r["gider"]:
                kabul.append(
                    {"anahtar": k, "yeni": v, "gider": r["gider"], "ortaya": r["ortaya"], "yontem": "türev"}
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
    for k, v0, v1 in _degisenler(veri, i, onceki, alan, gizli):
        if not butce.var():
            break
        eski = butce.durum(_yaz(veri, i, k, v0), i)
        if not [x for x in once[0] if x not in eski[0]]:
            continue
        iyi, kotu_ = (v0, eski), v1
        a = ADIM[alan[k]["birim"]]
        while abs(kotu_ - iyi[0]) > a + 1e-9:
            orta = round(round((iyi[0] + kotu_) / 2.0 / a) * a, 6)
            if orta in (iyi[0], kotu_) or not butce.var():
                break
            d = butce.durum(_yaz(veri, i, k, orta), i)
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
        simdi = girilen.get(k)
        simdi = alan[k]["varsayilan"] if simdi in (None, "") else simdi
        for v in _secenekler(k, alan[k], simdi):
            if sayac >= AZAMI_SECIM or not butce.var():
                return kabul
            sayac += 1
            r = _sonucu(once, butce.durum(_yaz(veri, i, k, v), i), ortulu)
            if r["gider"] and not r["yeni"] and not r["kotu"]:
                kabul.append(
                    {
                        "anahtar": k,
                        "eski": simdi,
                        "yeni": v,
                        "gider": r["gider"],
                        "ortaya": r["ortaya"],
                        "yontem": "seçim",
                    }
                )
    return kabul


def coz(veri, i=0, onceki=None, butce=None):
    """Aktif asansörün her sorununun doğrulanmış çareleri:
    { careler:  [ { metin , oneriler:  [ … ] } ] , sinama , tamamlandi , neden , sure }.
    tamamlandi:  arama bütçeye ( neden "sinama" ) ya da güvenlik süresine
    ( "sure" ) takılmadan bitti mi — takıldıysa çareler eksik olabilir."""
    t0 = time.monotonic()
    butce = butce or _Butce()
    ilk = butce.kalan
    once = _durum(veri, i)
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
                        "bina": c["anahtar"] in BINA,
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


def _sirala(liste, degerler):
    """Son değişikliğin sınırı → sayı ( bina olmayan ) → seçim → bina ölçüsü;
    sonra en çok sorunu gideren → en küçük değişiklik;  aynı kutudan tek
    öneri ( en iyisi )."""

    def anahtar(c):
        if c["yontem"] == "seçim":
            return (True, 1, -len(c["gider"]), 0.0)
        eski = degerler.get(c["anahtar"]) or 0.0
        return (
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
def api_care(veri: dict = Body(...)):
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
        i = min(max(i, 0), len(asansorler) - 1)
        onceki = veri.get("onceki") if isinstance(veri.get("onceki"), dict) else None
        return JSONResponse({"aktif": True, **coz(veri, i, onceki)})
    except Exception as e:  # noqa: BLE001
        hata_kaydi(log, e)
        return JSONResponse({"aktif": False, "hata": [hata_iletisi("DÜZELTME HATASI", e, ": ")]})
