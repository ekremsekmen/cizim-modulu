# -*- coding: utf-8 -*-
"""
KABİN ÜSTÜ PLANI  ( kabin tavanı hizasından yatay kesit )

Kuyu planının duvarlarını, raylarını, konsollarını ve karşı ağırlığını AYNEN
kullanır:  yerleşim ikinci kez hesaplanmaz, plan() elemanlarından okunur —
iki çizim ayrışamaz.  Üstüne kabin tavanında olanlar gelir:

  · kabin tavanı, şase dikmeleri ve üst kirişi
  · kapı operatörü YALNIZ YERLEŞİMDE ( engel ), çizilmez — LiftDesigner
    1022'nin kabin üstü kesiti ( X-X ) de çizmez ( kullanıcı kararı 5 Eki )
  · askı:  kabin üstü askıda kasnaklar tavanda;  kabin altı askıda halatlar
    tavanın dışından geçer;  doğrudan askıda askı noktaları tavandadır
  · KORKULUK            TS EN 81-20 m.5.4.7.2 b ve m.5.4.7.4
  · SIĞINMA ALANI       TS EN 81-20 m.5.2.5.7.1 · Çizelge 3

Kapı ( kapi_gorunusu ):  kesit kabin tavanından geçer ( kabin iç + tavan,
2.060 ) — kaba boşluğun üstü kapı + kapi_ust_payi ( 2.240 ), kasanın üstü
kapı + kasa_ust ( 2.220 ).  Kesit boşluğun içindeyse ön duvar boşlukludur,
kasa kesilir;  kanatların üstü ( kapı yüksekliği ) her zaman kesitin altında
kalır:  kat ve kabin kapısı yukarıdan görünür ( LiftDesigner 1022 X-X gibi ).
Eskiden ön duvar hep dolu çiziliyor, kapı bölgesi boş
kalıyordu ( kullanıcı 5 Eki:  "kapının görünmemesi saçma" ).
"""

from dataclasses import dataclass

from temel import eleman_kutusu, ortusur
from cizim import istek_onbellegi
from cizim import eleman
from cizim import kisaltmalar
from cizim import uslup
from cizim import geometri
from cizim import girdi
from cizim import sabitler
from cizim import standart
from cizim import parca_kotlari
from cizim import arka_aski
from cizim import hareketli
from cizim import parca_adlari

#  TS EN 81-20 Çizelge 3 — kabin üstü sığınma alanının yatay ölçüleri ( mm ).
#  Adlar hesap programının "Kabin üstü sığınma hacmi tipi" seçenekleriyle
#  aynıdır;  köprü değeri olduğu gibi taşır.
SIGINMA = {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0)}
#  ve yüksekliği ( mm ) — dusey açıklığı bununla ölçer
SIGINMA_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0}

_ICERI = (
    "Korkuluğun kenardan içeri alınması:  küpeşte kuyudaki parçalardan en az "
    "0,10 m uzak durur ( TS EN 81-20 m.5.4.7.4 d ), kenardan en çok 0,15 m "
    "içeride ( m.5.4.7.4 c )."
)
#  Kuyuda duran ( kabinle birlikte gitmeyen ) parçaların katmanları
_KUYU_PARCALARI = ("RAY", "KONSOL", "AGIRLIK")
#  Kuyu planından alınan katmanlar ve adlar
_PLANDAN_KATMAN = ("TARAMA", "KUYU-DUVAR", "KUYU-IC", "RAY", "KONSOL", "CIVATA", "PATEN", "AGIRLIK", "EKSEN")
_PLANDAN_AD = ("agirlik_kasnak", "agirlik_kasnak_yazi", "agirlik_yazi", "sase_dikme")


#  Planın kabinle ve askıyla gelen elemanları — kabin üstünde kendi
#  biçimleriyle yeniden çizilir ya da askıya göre seçilir.  AÇIK LİSTE:
#  ad önekine bakılsaydı "kabin_ray" gibi yeni bir ad sessizce düşerdi.
_PLANDAN_DISLA = frozenset(
    (
        "kabin_dis",
        "sase_dikme",
        "sase_kiris",
        "kabin_kasnak",
        "kabin_kasnak_capraz",
        "aski_duzlemi",
        "kabin_kasnak_yazi",
        "aski_nokta",
    )
)
#  Kuyu planının kapı elemanları ( kasa ayrıca, tek parça çizilir )
_KAPI_AD = frozenset(
    (
        "kapi_boslugu",
        "kat_esigi",
        "kat_kanadi",
        "kanat_cebi",
        "kanat_durdurucu",
        "kabin_esigi",
        "kabin_kanadi",
        "kabin_kanat_cebi",
    )
)


def kapi_gorunusu(g, S):
    """Kabin üstü kesitinin kapıya göre yeri ( döşemeden, mm ):

      kesit   kesit kotu:  kabin iç yüksekliği + tavan kalınlığı
      acik    kesit kaba boşluğun içinde ( < kapı + kapi_ust_payi ):  ön duvar
              boşluklu;  değilse dolu, boşluk lentonun altında ( kesikli )
      kasa    kasa kesilir ( < kapı + kasa_ust )
    Kanatlar kapı yüksekliğindedir;  kabin iç yüksekliği kapıdan alçak
    olamaz ( geometri.dogrula ) — kanatlar her zaman kesitin altındadır."""
    kesit = g["dusey"]["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"]
    kapi_h = g["kapi"].get("yukseklik") or 0
    return {
        "kesit": kesit,
        "acik": kesit < girdi.kaba_bosluk(g, S)[2],
        "kasa": kesit < kapi_h + S["kasa_ust"],
    }


def _operator(g, tavan, S):
    """Kapı operatörünün tavandaki izi.  Kanatlar açılınca operatörün kirişi
    boyunca kayar:  açılış yanına ( merkezide iki yana ) bir kanat eni kadar
    taşar — 2 kanatlıda yarım kapı, 3 kanatlıda üçte bir, 4 kanatlı merkezide
    çeyrek ( girdi.kanat_cepleri ).  Tavanın üstünde kabin kapısı mekanizma
    kutusunun derinliği kadar yer tutar ( sabitler );  önde kabin kapısının
    üstüne, kabin eşiğinin ön kenarına kadar uzanır — kanatlar onun ray
    taşıyıcısına asılıdır ( eskiden tavanın ön kenarında bitiyordu:  kabin
    kapısının üstü boş görünüyordu )."""
    kp = g["kapi"]
    x0, kg = kp["sol_pay"], kp["genislik"]
    #  Kanatların açılınca durduğu yer ( girdi.kanat_cepleri, payı olmadan ):
    #  2 kanatlıda yarım kapı, 3 kanatlıda üçte bir, 4 kanatlı merkezide çeyrek
    #  Elle açılan kat kapısında kabin kapısının cebi bilinmez:  eskisi gibi iki
    #  yana yarım kapı ( tavanın kenarında kırpılır ).
    cep = (
        girdi.kanat_cepleri(g, S, pay=False)
        if girdi.kapi_tipi(kp.get("tip"))["tur"] != "manuel"
        else [(x0 - 0.5 * kg, x0), (x0 + kg, x0 + 1.5 * kg)]
    )
    #  Kanatların yolu tavandan geniş olabilir ( dar kabinde cep kabinin
    #  yanına taşar — LiftDesigner 4815-6 ):  operatör onu da örter.  Eskiden
    #  tavanın kenarında kırpılıyordu.
    x1, x2 = min([x0] + [c[0] for c in cep]), max([x0 + kg] + [c[1] for c in cep])
    if girdi.kapi_tipi(kp.get("tip"))["tur"] == "manuel":
        x1, x2 = max(x1, tavan[0]), min(x2, tavan[2])  # cep bilinmez:  tavanda kırpılır
    return (x1, girdi.kapi_bolgesi(g, S)["kabin_esik"][0], x2, tavan[1] + S["kabin_kapisi_kutu_boy"])


@istek_onbellegi.sakla
def yerlesim(g, cizim_sabitleri=None):
    """Kabin üstünün yerleşimi — çizim de doğrulama da bunu kullanır.

    Dönen:  { taban ( plan elemanları ), tavan, kenarlar, operator, engeller,
              siginma ( kutu ya da None ), hata [ … ] }
    """
    S = sabitler.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    taban = geometri.plan(g, S, kapi_duzeyi=False, duvar_boslugu=kapi_gorunusu(g, S)["acik"])
    tavan = eleman_kutusu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    parcalar = [
        eleman_kutusu(el) for el in taban if el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI
    ]
    hata = []
    kenarlar = _korkuluk_kenarlari(g, tavan, parcalar, hata)
    halatlar = _halatlar(g, S, taban, hata)
    #  Sığınma alanı korkulukların içinde kalır
    ic = (
        tavan[0] + kenarlar["Sol"]["iceri"],
        tavan[1] + kenarlar["Ön"]["iceri"],
        tavan[2] - kenarlar["Sağ"]["iceri"],
        tavan[3] - kenarlar["Arka"]["iceri"],
    )
    operator, engeller = _tavan_engelleri(g, S, taban, tavan, parcalar, kenarlar, ic, hata)
    tip = (g.get("kabin_ustu") or {}).get("siginma_tipi")
    siginma = _siginma_yeri(S, tip, tavan, ic, engeller, hata)
    return {
        "taban": taban,
        "tavan": tavan,
        "kenarlar": kenarlar,
        "ic": ic,
        "operator": operator,
        "engeller": engeller,
        "siginma": siginma,
        "siginma_tipi": tip,
        "halatlar": halatlar,
        "hata": hata,
        "S": S,
    }


def _korkuluk_kenarlari(g, tavan, parcalar, hata):
    """KORKULUK:  her kenar ayrı değerlendirilir.
    bos:     tavan kenarından duvara  ( m.5.4.7.2 b )
    parca:   tavan kenarından o yandaki en yakın kuyu parçasına"""
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    kenarlar = {}
    for yan in ("Sol", "Sağ", "Arka", "Ön"):
        if yan == "Sol":
            bos = tavan[0]
            yakin = [
                tavan[0] - p[2]
                for p in parcalar
                if p[2] <= tavan[0] + 1e-9 and p[1] < tavan[3] and tavan[1] < p[3]
            ]
        elif yan == "Sağ":
            bos = G - tavan[2]
            yakin = [
                p[0] - tavan[2]
                for p in parcalar
                if p[0] >= tavan[2] - 1e-9 and p[1] < tavan[3] and tavan[1] < p[3]
            ]
        elif yan == "Arka":
            bos = D - tavan[3]
            yakin = [
                p[1] - tavan[3]
                for p in parcalar
                if p[1] >= tavan[3] - 1e-9 and p[0] < tavan[2] and tavan[0] < p[2]
            ]
        else:
            bos = tavan[1]
            yakin = [
                tavan[1] - p[3]
                for p in parcalar
                if p[3] <= tavan[1] + 1e-9 and p[0] < tavan[2] and tavan[0] < p[2]
            ]
        k = {
            "bos": bos,
            "gerekli": bos > standart.KORKULUK_BOSLUK,
            "iceri": 0.0,
            "parca": min(yakin) if yakin else None,
            "yukseklik": None,
        }
        if k["gerekli"]:
            #  Küpeşte parçalardan 0,10 m uzak durmalı:  gerekirse içeri alınır
            k["iceri"] = max(0.0, standart.KORKULUK_PARCA_ASGARI - (k["parca"] if yakin else 1e9))
            if k["iceri"] > standart.KORKULUK_KENAR_AZAMI:
                hata.append(
                    f"{yan} kenarda korkuluk kuyudaki parçalara {standart.KORKULUK_PARCA_ASGARI:g} mm "
                    f"uzak durmak için {k['iceri']:g} mm içeri alınmalı;  TS EN 81-20 "
                    f"m.5.4.7.4 c en çok {standart.KORKULUK_KENAR_AZAMI:g} mm verir."
                )
            k["yukseklik"] = (
                standart.KORKULUK_ALCAK
                if bos + k["iceri"] <= standart.KORKULUK_YUKSEKLIK_SINIRI
                else standart.KORKULUK_YUKSEK
            )
        kenarlar[yan] = k
    return kenarlar


HALAT_PAYI = girdi.HALAT_PAYI
#  Kabin altı askıda halat kasnağın teğetinden kabinin YANINDAN yukarı çıkar:
#  kasnağın üstündeki kabin parçaları ( kabin, şase, patenler ) ona değemez.
_KABINLE_GIDEN = ("kabin_dis", "sase_dikme", "sase_kiris")


def _gercek_kutu(el):
    """Elemanın planda kapladığı kutu.  Konsolun mantık zarfı ( "kol" ) dar
    tutulur ( geometri._kabin_rayi_konsolu );  çizilen biçimi duvardan ray
    arkasına, konsolun bütün boyuncadır — halat ona göre denetlenir."""
    k = eleman_kutusu(el)
    for b in el.get("bicim") or []:
        for x, y in b["noktalar"]:
            k = (min(k[0], x), min(k[1], y), max(k[2], x), max(k[3], y))
    return k


def _parca_adi(el):
    """İletideki adı:  "ara kiriş", "kabin rayı" … ( parca_adlari )."""
    return parca_adlari.ad(el["ad"]).lower() if el.get("ad") else el["katman"].lower()


def _halatlar(g, S, taban, hata):
    """Halatların planda yeri ve engelleri ( 15 Eki — senaryo taraması r467 ).
    HALAT kuyuya sabit bir düşey çizgidir:  kuyudaki parçaların ( konsol GERÇEK
    zarfıyla ) içinden geçemez;  kabin altı askıda kasnağın üstündeki kabin
    parçalarına da değemez ( kabin halat boyunca iner )."""
    G = g["kuyu"]["genislik"]
    halatlar = geometri.halat_konumlari(g, S)
    duzen = (g.get("aski") or {}).get("duzen")
    engel = [el for el in taban if el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI]
    if duzen == "Kabin altı":
        engel += [
            el
            for el in taban
            if el["tip"] == "dikdortgen"
            and (
                el.get("ad") in _KABINLE_GIDEN
                or (el["katman"] == "PATEN" and el.get("ad") != "agirlik_pateni")
            )
        ]
    for hx, hy in halatlar:
        if not (0 < hx < G):
            hata.append(f"Halat kuyunun dışına düşüyor ( x = {hx:g} ) — kasnak aralığını gözden geçirin.")
            continue
        for el in engel:
            p = _gercek_kutu(el)
            if p[0] - HALAT_PAYI < hx < p[2] + HALAT_PAYI and p[1] - HALAT_PAYI < hy < p[3] + HALAT_PAYI:
                kabinle = el["katman"] not in _KUYU_PARCALARI
                hata.append(
                    f"Halat ( x = {hx:g}, y = {hy:g} ) {_parca_adi(el)} parçasının içinden ya da ona "
                    f"{HALAT_PAYI:g} mm'den yakın geçiyor — "
                    + (
                        "kabin halat boyunca indiğinden sürtünür:  askı noktasının derinlikteki yerini "
                        "( xs ) ya da kasnak aralığını gözden geçirin."
                        if kabinle
                        else "kasnak aralığını gözden geçirin."
                    )
                )
                break
    _kasnak_engelleri(g, S, taban, hata)
    return halatlar


def _kasnak_engelleri(g, S, taban, hata):
    """KABİN KASNAĞI KABİNLE BİRLİKTE BÜTÜN KUYU BOYUNCA GİDER ( 15 Eki — senaryo
    taraması r016, r715:  kabin altı kasnağın ucu ara kirişin içindeydi ):
    kuyu boyunca uzanan sabit parçalarla ( ray, konsol, ara kiriş ) planda
    örtüşmesi çarpışmadır ( kot önemsiz );  karşı ağırlıktan da m.5.2.5.5.1 h
    açıklığı kadar uzak durur.  Kabinin kendi parçalarıyla ( şase dikmesi )
    plan örtüşmesi çarpışma DEĞİLDİR:  kabin altı kasnaklar alt kirişin
    altındadır ( parca_kotlari ).  Kenarda değmek sayılmaz ( 1 mm )."""
    duzen = (g.get("aski") or {}).get("duzen")
    if duzen not in ("Kabin altı", "Kabin üstü"):
        return
    sabit = [el for el in taban if el["tip"] == "dikdortgen" and el["katman"] in ("RAY", "KONSOL")]
    agirlik = [
        el
        for el in taban
        if el["tip"] == "dikdortgen"
        and (el["katman"] == "AGIRLIK" or el.get("ad") in ("agirlik_kasnak", "agirlik_pateni"))
    ]
    A = girdi.KABIN_AGIRLIK_ACIKLIGI
    for k in geometri.kabin_kasnak_kutulari(g, S, taban):
        yer = f"x {k[0]:g} – {k[2]:g}"
        p = next((el for el in sabit if ortusur(k, _gercek_kutu(el), -1.0)), None)
        if p is not None:
            hata.append(
                f"Kabin kasnağı ( {yer} ) {_parca_adi(p)} ile üst üste biniyor — kabin kuyu boyunca "
                "indiğinden çarpar:  kasnak aralığını ( ya da çapını ) gözden geçirin."
            )
            continue
        p = next((el for el in agirlik if ortusur(k, eleman_kutusu(el), A)), None)
        if p is not None:
            hata.append(
                f"Kabin kasnağı ( {yer} ) karşı ağırlığa {A:g} mm'den yakın ( TS EN 81-20 m.5.2.5.5.1 h ) "
                "— kasnak aralığını gözden geçirin."
            )


def _tavan_engelleri(g, S, taban, tavan, parcalar, kenarlar, ic, hata):
    """TAVANDAKİ ENGELLER:  kapı operatörü, askı elemanları ve kabinin tavanın
    üstündeki parçaları.  ( operatör, [ engel ] — ilki operatör )"""
    operator = _operator(g, tavan, S)
    #  Operatör kabinle gider:  tavandan taşan ucu kuyudaki bir parçaya değemez
    for p in parcalar:
        if ortusur(operator, p):
            hata.append(
                f"Kabin kapısı operatörü ( kanatların yolu, x {operator[0]:g} – "
                f"{operator[2]:g} ) kuyudaki bir parçaya değiyor ( x {p[0]:g} – {p[2]:g}, "
                f"y {p[1]:g} – {p[3]:g} ):  "
                + (
                    "kapıyı öbür yana açın ya da kabini kaydırın."
                    if girdi.kapi_tipi(g["kapi"].get("tip"))["tur"] == "teleskopik"
                    else "kabini kaydırın."
                )
            )
            break
    engeller = [operator]
    duzen = (g.get("aski") or {}).get("duzen")
    if duzen == "Kabin üstü":
        engeller += geometri.kabin_kasnak_kutulari(g, S, taban)
    elif duzen == "Doğrudan":
        for el in taban:
            if el.get("ad") == "aski_nokta" and el["tip"] == "daire":
                engeller.append((el["x"] - 70, el["y"] - 70, el["x"] + 70, el["y"] + 70))

    #  Kabin üstü kasnağı korkuluğun yolunu kesemez
    for yan, k in kenarlar.items():
        if not k["gerekli"] or duzen != "Kabin üstü":
            continue
        for p in engeller[1:]:
            if yan in ("Sol", "Sağ"):
                x = ic[0] if yan == "Sol" else ic[2]
                kesiyor = p[0] < x < p[2] and p[1] < ic[3] and ic[1] < p[3]
            else:
                y = ic[3] if yan == "Arka" else ic[1]
                kesiyor = p[1] < y < p[3] and p[0] < ic[2] and ic[0] < p[2]
            if kesiyor:
                hata.append(
                    f"Kabin üstü kasnağı {yan.lower()} kenardaki korkuluğun yolunu kesiyor — kasnak aralığını daraltın."
                )
                break

    #  KABİNİN TAVANIN ÜSTÜNDEKİ PARÇALARI ( hareketli.kabin_parcalari ):
    #  sığınma hacmi ( çömelmede 1,0 m yüksek ) onların altına giremez —
    #  şasenin üst kirişi ( ray ekseninde, dikmeden dikmeye;  kullanıcı kararı
    #  4 Eki ), kasnaklar ve aralarındaki halat ( çapraz düzende çapraz şerit ),
    #  1:1 halat bağlantısı.  Eskiden kiriş yalnız kabin altı ve doğrudan
    #  askıda sayılıyor, kasnaklar arasındaki halat hiç sayılmıyordu:  arkadaki
    #  ağırlıkla 2:1'de halat tavanın 80 mm üstünden alanın içinden geçiyordu
    #  ( denetim 9 Eki ).  Korkuluk denetimi ( yukarıda ) bunları saymaz:
    #  küpeşte kirişin ve halatın üstünden geçer.
    tip = (g.get("kabin_ustu") or {}).get("siginma_tipi")
    kt = parca_kotlari.kabin_kotlari(g["dusey"], S, 0.0, g.get("aski"), arka_aski.arkada_iki_bir(g))
    sinir = kt["tavan"] + SIGINMA_YUKSEKLIK.get(tip, max(SIGINMA_YUKSEKLIK.values()))
    engeller += [
        k
        for ad, k, alt, ust in hareketli.kabin_parcalari(g, S, taban, kt)
        if ad != hareketli.KABIN and ust > kt["tavan"] + 1e-9 and alt < sinir - 1e-9
    ]
    return operator, engeller


def _siginma_yeri(S, tip, tavan, ic, engeller, hata):
    """SIĞINMA ALANI  ( Çizelge 3 ):  kapıya en yakın, sonra kabin eksenine en
    yakın boş yer aranır — bakımcı tavana kapıdan çıkar.  Kutu ya da None."""
    if tip not in SIGINMA:
        hata.append(f"kabin_ustu.siginma_tipi: {tuple(SIGINMA)} içinden olmalı ( {tip!r} ).")
        return None
    kx = (tavan[0] + tavan[2]) / 2.0
    adaylar = []
    for kenar in (False, True):
        adaylar = [
            (round(k[1], 3), abs((k[0] + k[2]) / 2.0 - kx), k)
            for w, h in {SIGINMA[tip], SIGINMA[tip][::-1]}
            for k in geometri.yer_adaylari(ic, w, h, engeller, kenar)
        ]
        if adaylar:
            break
    if adaylar:
        return min(adaylar)[2]
    a, b = SIGINMA[tip]
    hata.append(
        f"Kabin tavanında {tip.lower()} tipi sığınma alanına ( {a:g} × {b:g} mm, "
        "TS EN 81-20 Çizelge 3 ) yer yok — korkulukların içinde;  kapı "
        "operatörü, şasenin üst kirişi ( ray ekseninde "
        f"{S['sase_dikme_derinlik']:g} mm — Sabitler:  kabin şasesi dikmesinin "
        "kesitteki eni ), kasnaklar ve aralarındaki halat dışında kalmalı."
    )
    return None


def _yazi_kutusu(el):
    """Ölçü yazısının kutusu ( geometri.yazi_kutusu ) — yazı yoksa boş."""
    return geometri.yazi_kutusu(el) or (0.0, 0.0, 0.0, 0.0)


def dogrula(g):
    """Kuyu planının doğrulaması + kabin üstünün kendi kuralları."""
    hata = geometri.dogrula(g)
    if hata:
        return hata
    return yerlesim(g)["hata"]


def korkuluklar(Y):
    """Plan, kesit ve açıklık denetiminin ortak küpeşte konumları.

    Kapı operatörü tavanın önünde durur;  küpeşte onun içinden geçemez:  yan
    kenardaki korkuluk operatörün arka yüzünden başlar ( operatör o kenara
    uzanıyorsa ), ön kenarda korkuluk gerekirse operatörün arkasına geçer.
    Eskiden yan korkuluk tavanın bütün derinliğince çiziliyor, ön dikmesi
    operatörün içinde duruyordu."""
    x0, y0, x1, y1 = Y["ic"]
    op = Y["operator"]

    def on(x):
        return op[3] if op[0] - 1e-9 <= x <= op[2] + 1e-9 and op[1] - 1e-9 <= y0 < op[3] else y0

    kenarlar = {
        "Sol": (x0, on(x0), x0, y1),
        "Sağ": (x1, on(x1), x1, y1),
        "Ön": (x0, max(y0, op[3]), x1, max(y0, op[3])),
        "Arka": (x0, y1, x1, y1),
    }
    return [(kenarlar[ad], k["yukseklik"]) for ad, k in Y["kenarlar"].items() if k["gerekli"]]


def ciz(g, cizim_sabitleri=None):
    """Kabin üstü planının elemanları."""
    Y = yerlesim(g, cizim_sabitleri)
    S, tavan = Y["S"], Y["tavan"]
    duzen = (g.get("aski") or {}).get("duzen")
    #  Tavandaki askı elemanları ( kabin üstü kasnakları, 1:1 bağlantısı )
    #  TAVANDAN SONRA çizilir:  tavanın dolgusu onları örtüyordu.
    aski_ad = (
        ("kabin_kasnak", "kabin_kasnak_capraz", "aski_duzlemi", "kabin_kasnak_yazi")
        if duzen == "Kabin üstü"
        else ("aski_nokta",)
        if duzen == "Doğrudan"
        else ()
    )
    e = [
        el
        for el in Y["taban"]
        if el.get("ad") in _PLANDAN_AD
        or (el["katman"] in _PLANDAN_KATMAN and el["tip"] != "yazi" and el.get("ad") not in _PLANDAN_DISLA)
    ]
    aski_el = [el for el in Y["taban"] if el.get("ad") in aski_ad]

    #  ── KABİN TAVANI ─────────────────────────────────────────────────
    e.append(
        eleman.ad(
            eleman.dikdortgen("KABIN", tavan[0], tavan[1], tavan[2] - tavan[0], tavan[3] - tavan[1]), "tavan"
        )
    )
    #  Şasenin üst kirişi tavanın üstünde, ray ekseninde dikmeden dikmeye
    #  ( kuyu planındaki zarfı;  kabin üstü kasnaklar onun da üstünde ).
    #  Eskiden bu planda yalnız dikmeler vardı:  askı görünmüyordu ( 3 Eki ).
    e += [el for el in Y["taban"] if el.get("ad") == "sase_kiris"]
    e += _kapi_elemanlari(g, S, Y)

    #  Kabin altı askıda halatlar tavanın DIŞINDAN, kasnakların dış
    #  teğetinden yukarı çıkar ( kabin üstü askıda halat tavandaki kasnaktan
    #  çıkar — kasnak zaten çizili )
    for hx, hy in Y["halatlar"] if duzen == "Kabin altı" else ():
        e.append(eleman.ad(eleman.daire("KASNAK", hx, hy, 20), "halat"))
        e.append(eleman.yazi(hx, hy - 70, "HALAT", uslup.NORMAL))

    #  ── KORKULUK ─────────────────────────────────────────────────────
    #  Küpeşte çizgisi, gerekli olan her kenarda iceri kadar içeride durur.
    for kutu, _ in korkuluklar(Y):
        e.append(eleman.ad(eleman.cizgi("KORKULUK", *kutu), "korkuluk"))

    #  ── SIĞINMA ALANI ────────────────────────────────────────────────
    sg = Y["siginma"]
    if sg:
        e.append(
            eleman.ad(eleman.dikdortgen("SIGINMA", sg[0], sg[1], sg[2] - sg[0], sg[3] - sg[1]), "siginma")
        )
        a, b = SIGINMA[Y["siginma_tipi"]]
        e += geometri.alan_yazisi(sg, ["SIĞINMA ALANI", f"{eleman.buyuk(Y['siginma_tipi'])}  {a:g} x {b:g}"])
    e += aski_el

    e += _ana_olculer(g, tavan)
    e += _iceri_olculeri(Y)
    if sg:
        e += _siginma_olculeri(g, Y, e)
    #  KORKULUK YAZISI:  küpeşte boyunca, operatöre ve sığınma ölçüsüne
    #  denk gelmeyen en uzun boş parçanın ortasına.  Ölçü yazıları önce
    #  yerleşir:  yazının şeridine düşen ölçü yazısı da o parçayı doldurur.
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e, kaydir=True)
    _korkuluk_yazilari(Y, e)

    #  Sıfır boylu ölçü çizilmez  ( sığınma alanı kenara dayanmışsa )
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    geometri.yazilari_yerlestir(e, kaydir=True)
    geometri.parcadan_kaydir(e, ek_katman=("KAPI",))
    return e


def _kapi_elemanlari(g, S, Y):
    """KAPI ( kapi_gorunusu ):  kat kapısı kesitin altında, yukarıdan görünür:
    eşik, kanatlar, cep.  Kasa kesilir ya da üstü görünür:  her iki halde
    kapının üstünü boydan boya geçen tek parça ( dikmeler + üst kasa );  duvar
    boşluğuna monte kasa dolu lentonun altında kalır ( kesikli ).  Kabin kapısı
    da görünür:  operatör çizilmez ( LiftDesigner 1022 X-X )."""
    KG = kapi_gorunusu(g, S)
    KB = girdi.kapi_bolgesi(g, S)
    kp = g["kapi"]
    e = []
    for el in Y["taban"]:
        ad = el.get("ad")
        if el["katman"] not in ("KAPI", "KABIN") or ad not in _KAPI_AD:
            continue
        el = dict(el)
        if ad == "kapi_boslugu" and not KG["acik"]:
            el["katman"] = "GIZLI"
        e.append(el)
    kasa = eleman.dikdortgen(
        "KAPI",
        kp["sol_pay"] - S["kasa_yan"],
        KB["kasa"][0],
        kp["genislik"] + 2 * S["kasa_yan"],
        KB["kasa"][1] - KB["kasa"][0],
    )
    if not KG["acik"] and kp["montaj"] == "Duvar boşluğuna":
        kasa["katman"] = "GIZLI"
    e.append(eleman.ad(kasa, "kapi_kasasi"))
    return e


def _ana_olculer(g, tavan):
    """Kabin tavanı ve kuyu ölçüleri ( üstte ve sağda )."""
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    dg, dar = g["kuyu"]["duvar_sag"], g["kuyu"]["duvar_arka"]
    tg = tavan[2] - tavan[0]
    u0, u1 = D + dar + 120, D + dar + 120 + geometri.SIRA_ARASI
    s0, s1 = G + dg + 120, G + dg + 120 + geometri.SIRA_ARASI
    return [
        eleman.olcu("yatay", (0, 0), (tavan[0], 0), u0),
        eleman.olcu(
            "yatay", (tavan[0], 0), (tavan[2], 0), u0, kisaltmalar.kodlu("PLW", tg), ad="kabin_dis_genisligi"
        ),
        eleman.olcu("yatay", (tavan[2], 0), (G, 0), u0),
        eleman.olcu("yatay", (0, 0), (G, 0), u1, kisaltmalar.kodlu("SW", G), ad="kuyu_genisligi"),
        eleman.olcu("dusey", (0, 0), (0, tavan[1]), s0),
        eleman.olcu("dusey", (0, tavan[1]), (0, tavan[3]), s0, ad="kabin_tavani_derinligi"),
        eleman.olcu("dusey", (0, tavan[3]), (0, D), s0),
        eleman.olcu("dusey", (0, 0), (0, D), s1, kisaltmalar.kodlu("SD", D), ad="kuyu_derinligi"),
    ]


#  Ölçü yazısının parça kenarına uzaklığı ( yazının halesi — svg.HALE — kenarı
#  silmesin:  0,6 em'in yarısı 21 mm )
KENAR_PAYI = 25.0


def _iceri_olculeri(Y):
    """Korkuluğun kenardan içeri alınması  ( 0'dan büyükse )."""
    tavan, ic = Y["tavan"], Y["ic"]
    e = []
    for yan, k in Y["kenarlar"].items():
        if not (k["gerekli"] and k["iceri"] > 1e-9):
            continue
        metin = f"{k['iceri']:g}"
        yari = eleman.yazi_eni(metin, uslup.NORMAL) / 2.0
        if yan in ("Sol", "Sağ"):
            x1, x2 = (tavan[0], ic[0]) if yan == "Sol" else (ic[2], tavan[2])
            #  Her kenarın ölçüsü kendi sırasında  ( iki kenar aynı sırada
            #  kopuk bir zincir oluştururdu )
            kot = tavan[3] - (120 if yan == "Sol" else 200)
            yazi = {"x": (x2 + 30 + yari) if yan == "Sol" else (x1 - 30 - yari), "y": kot, "h": uslup.NORMAL}
            e.append(eleman.olcu("yatay", (x1, 0), (x2, 0), kot, metin, kural=_ICERI, yazi=yazi))
        else:
            y1, y2 = (ic[3], tavan[3]) if yan == "Arka" else (tavan[1], ic[1])
            kot = tavan[0] + (120 if yan == "Arka" else 200)
            #  Yazı aralığa sığıyorsa ortasına;  sığmıyorsa ucun yanına, tavanın
            #  içine ( korkuluğun içi — korkuluk yazısı sonra konur, ölçü
            #  yazılarından kaçar ).  12 Eki:  yazı 2,5 mm'ye büyüyünce 37,5'lik
            #  aralıkta tavanın ve korkuluğun kenarına biniyordu ( 35 düzen ).
            yy = (y1 + y2) / 2.0
            yari_h = uslup.BUYUK_HARF * uslup.NORMAL / 2.0
            if y2 - y1 < 2 * (yari_h + KENAR_PAYI):
                yy = y1 - yari_h - KENAR_PAYI if yan == "Arka" else y2 + yari_h + KENAR_PAYI
            yazi = {"x": kot + 30 + yari, "y": yy, "h": uslup.NORMAL}
            e.append(eleman.olcu("dusey", (0, y1), (0, y2), kot, metin, kural=_ICERI, yazi=yazi))
    #  İçerideki yazı köşede yan kenarın yazısına değiyorsa sağa kayar ( 13
    #  Eki:  arkadaki ağırlıkta "40" soldaki "45"in ucuna biniyordu )
    yanlar = [geometri.yazi_kutusu(o) for o in e if o["yon"] == "yatay"]
    for o in e:
        if o["yon"] != "dusey":
            continue
        while any(ortusur(geometri.yazi_kutusu(o), b, 10.0) for b in yanlar):
            o["yazi"]["x"] += 20.0
    return e


def _siginma_olculeri(g, Y, e):
    """Sığınma alanının yeri — tavan kenarlarından.

    İki sıranın yeri DENENEREK seçilir:  her aday için yazılar gerçekten
    yerleştirilir ( yazilari_yerlestir ), yazıların öbür yazılara, kapı
    operatörüne, şasenin üst kirişine ve askı elemanlarına binmesi
    sayılır;  en az binen aday ( eşitse sıradaki ).  Korkuluk yazısı sonra
    konur ve bu yazılardan kendisi kaçar.
    Adaylar:  alanın arkası / önü ( sağı / solu ), içeride ön ( sol ) ve
    arka ( sağ ) kenarına yakın.  Eskiden tek kurallı seçim yazıları
    operatöre, korkuluk yazısına ve korkuluğun içeri alınma ölçüsüne
    bindiriyordu ( girdi taraması, 4 Eki )."""
    tavan, sg = Y["tavan"], Y["siginma"]
    yer = (
        "Sığınma alanının yeri:  program alanı kapıya en yakın, sonra kabin "
        "eksenine en yakın boş yere koyar ( 25 mm adımla;  dar boşlukta engelin "
        "kenarına yaslanarak )."
    )
    buyukluk = (
        f"Sığınma alanının ölçüsü:  TS EN 81-20 Çizelge 3 ( {str(g['kabin_ustu']['siginma_tipi']).lower()} )."
    )

    def olculer(kot_y, kot_x):
        return [
            eleman.olcu("yatay", (tavan[0], 0), (sg[0], 0), kot_y, kural=yer),
            eleman.olcu("yatay", (sg[0], 0), (sg[2], 0), kot_y, kural=buyukluk),
            eleman.olcu("yatay", (sg[2], 0), (tavan[2], 0), kot_y, kural=yer),
            eleman.olcu("dusey", (0, tavan[1]), (0, sg[1]), kot_x, kural=yer),
            eleman.olcu("dusey", (0, sg[1]), (0, sg[3]), kot_x, kural=buyukluk),
            eleman.olcu("dusey", (0, sg[3]), (0, tavan[3]), kot_x, kural=yer),
        ]

    engel = [geometri.sinir([el]) for el in e if el.get("ad") == "sase_kiris"] + list(Y["engeller"])
    yazilar = [geometri.sinir([el]) for el in e if el["tip"] == "yazi"]

    def puan(kot_y, kot_x):
        if not (
            tavan[1] < kot_y - 20
            and kot_y + 100 < tavan[3]
            and tavan[0] < kot_x - 20
            and kot_x + 100 < tavan[2]
        ):
            return 1e9
        yeni = olculer(kot_y, kot_x)
        dene = [dict(el) for el in e if el["tip"] == "olcu"] + yeni
        geometri.yazilari_yerlestir([el for el in e if el["tip"] != "olcu"] + dene, kaydir=True)
        diger = [_yazi_kutusu(el) for el in dene[: -len(yeni)]] + yazilar
        n = 0
        kutular_ = [_yazi_kutusu(el) for el in yeni if el["uzunluk"] >= 1e-6]
        for i_, k_ in enumerate(kutular_):
            n += sum(1 for b in diger + engel + kutular_[i_ + 1 :] if ortusur(k_, b))
        return n

    adaylar = [
        (ky, kx)
        for ky in (sg[3] + 90, sg[1] - 90, sg[1] + 60, sg[3] - 110)
        for kx in (sg[2] + 90, sg[0] - 90, sg[2] - 110, sg[0] + 60)
    ]
    kot_y, kot_x = min(adaylar, key=lambda a: (puan(*a), adaylar.index(a)))
    return olculer(kot_y, kot_x)


def _korkuluk_yazilari(Y, e):
    """Her gerekli kenarın korkuluk yazısı ( e'ye eklenir ).  Yazı çizilen
    küpeştenin çizgisine göre konur ( korkuluklar — ön kenarda operatörün
    arkasındadır, yanlarda operatörün arka yüzünden başlar ):  eskiden tavanın
    kenarına göre konuyor, ön korkuluğun yazısı operatöre ve yan korkuluğun
    yazısına biniyordu."""
    ken, op = Y["kenarlar"], Y["operator"]
    olcu_yazilari = [_yazi_kutusu(el) for el in e if el["tip"] == "olcu"] + [
        geometri.sinir([el]) for el in e if el["tip"] == "yazi"
    ]
    cizgiler = dict(zip([yan for yan, k in ken.items() if k["gerekli"]], korkuluklar(Y)))
    for yan, k in ken.items():
        if not k["gerekli"]:
            continue
        dikey = yan in ("Sol", "Sağ")
        (cx0, cy0, cx1, cy1), _h = cizgiler[yan]
        serit = _Serit(
            dikey=dikey,
            cizgi=cx0 if dikey else cy0,
            bas=min(cy0, cy1) if dikey else min(cx0, cx1),
            son=max(cy0, cy1) if dikey else max(cx0, cx1),
            ic_yon=1.0 if yan in ("Sol", "Ön") else -1.0,
        )
        metin, yon_, orta = _korkuluk_yazisi_yeri(serit, e, op, olcu_yazilari, k["yukseklik"])
        if dikey:
            e.append(eleman.yazi(serit.cizgi + yon_ * 60, orta, metin, uslup.NORMAL, aci=90))
        else:
            e.append(eleman.yazi(orta, serit.cizgi + yon_ * 60, metin, uslup.NORMAL))
        olcu_yazilari.append(geometri.sinir([e[-1]]))  # sonraki korkuluğun yazısı kaçsın


@dataclass(frozen=True)
class _Serit:
    """Bir küpeşte çizgisi ve boyunca yazı şeridi:  dikey ( yan kenar ) ise
    çizgi x'tedir ve şerit y boyuncadır ( bas … son );  ic_yon kabinin içine."""

    dikey: bool
    cizgi: float
    bas: float
    son: float
    ic_yon: float

    def kutu(self, yon_, a, b):
        """Çizginin yon_ tarafında 40 – 80 mm'lik bant ( boyunca a … b )."""
        s = sorted((self.cizgi + yon_ * 40, self.cizgi + yon_ * 80))
        return (s[0], a, s[1], b) if self.dikey else (a, s[0], b, s[1])

    def boyunca(self, k):
        """Kutunun şerit boyunca aralığı."""
        return (k[1], k[3]) if self.dikey else (k[0], k[2])

    def enine(self, k):
        """Kutunun şeride dik aralığı."""
        return (k[0], k[2]) if self.dikey else (k[1], k[3])


def _dolu_araliklar(serit, e, op):
    """Küpeşte boyunca yazının giremeyeceği aralıklar:  operatör, şasenin üst
    kirişi ve küpeşteyi kesen ölçüler."""
    cizgi, dikey = serit.cizgi, serit.dikey
    dolu = []
    if dikey and op[0] <= cizgi <= op[2]:
        dolu.append((op[1], op[3]))
    if not dikey and op[1] <= cizgi <= op[3]:
        dolu.append((op[0], op[2]))
    #  Şasenin üst kirişi de küpeştenin üstünden geçer
    for el in e:
        if el.get("ad") == "sase_kiris":
            k_ = geometri.sinir([el])
            if dikey and k_[0] <= cizgi <= k_[2]:
                dolu.append((k_[1] - 40, k_[3] + 40))
            if not dikey and k_[1] <= cizgi <= k_[3]:
                dolu.append((k_[0] - 40, k_[2] + 40))
    for el in e:
        if el["tip"] == "olcu" and el["yon"] == ("yatay" if dikey else "dusey"):
            i = 0 if dikey else 1
            if min(el["a"][i], el["b"][i]) <= cizgi + 60 and cizgi - 60 <= max(el["a"][i], el["b"][i]):
                dolu.append((el["kot"] - 70, el["kot"] + 110))
    return dolu


def _bos_parcalar(serit, yon_, dolu, olcu_yazilari):
    """Şeridin yon_ tarafında yazıya boş kalan parçalar ( bas … son içinde )."""
    bant = serit.kutu(yon_, serit.bas, serit.son)
    s0, s1 = serit.enine(bant)
    d_ = list(dolu)
    for k_ in olcu_yazilari:
        u0, u1 = serit.enine(k_)
        if u0 < s1 and s0 < u1:
            d_.append(serit.boyunca(k_))
    out, a = [], serit.bas
    for d1, d2 in sorted(d_):
        if d1 > a:
            out.append((a, min(d1, serit.son)))
        a = max(a, d2)
    if a < serit.son:
        out.append((a, serit.son))
    return out


def _kenar_dolu(serit, yon_, kenarlar_):
    """Şeridi kesen parça kenarları da şeridi doldurur ( yazı maskelidir —
    çapraz askının kasnağı çizgilerle çizilir, dikdörtgen sayılmıyordu;
    yazı kasnağın üstüne düşüyordu, 5 Eki )."""
    bant = serit.kutu(yon_, serit.bas, serit.son)
    return [
        (min(s_[1], s_[3]) - 10, max(s_[1], s_[3]) + 10)
        if serit.dikey
        else (min(s_[0], s_[2]) - 10, max(s_[0], s_[2]) + 10)
        for s_ in kenarlar_
        if geometri.kenar_kesisir(s_, bant)
    ]


def _korkuluk_yazisi_yeri(serit, e, op, olcu_yazilari, yukseklik):
    """( metin, yön, şerit boyunca orta ).

    Yazının şeridi küpeştenin içinde ( 40 – 80 mm );  içeride yazının
    boyunca boş parça yoksa küpeştenin DIŞINDA ( kabin ile duvar arası ),
    orada parçalardan da kaçarak.  Eskiden en uzun boş parçaya sığmasa da
    konuyordu:  sığınma ölçülerinin yazılarına biniyordu ( girdi taraması )."""
    metin = f"KORKULUK  h = {yukseklik:g}"
    kisa = f"h = {yukseklik:g}"
    ic_yon = serit.ic_yon
    dolu = _dolu_araliklar(serit, e, op)
    parcalar_ = [
        geometri.sinir([el])
        for el in e
        if (el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI + ("PATEN", "SASE"))
        or (el["tip"] == "daire" and el["katman"] == "KASNAK")
    ]  # halatlar
    kenarlar_ = geometri.parca_kenarlari([el for el in e if el.get("ad") != "korkuluk"])
    ic_parca = _bos_parcalar(serit, ic_yon, dolu + _kenar_dolu(serit, ic_yon, kenarlar_), olcu_yazilari)
    dis_engel = _kenar_dolu(serit, -ic_yon, kenarlar_)
    serit_dis = sorted((serit.cizgi - ic_yon * 40, serit.cizgi - ic_yon * 80))
    for k_ in parcalar_:
        u0, u1 = serit.enine(k_)
        if u0 < serit_dis[1] and serit_dis[0] < u1:
            dis_engel.append(serit.boyunca(k_))
    dis_parca = _bos_parcalar(serit, -ic_yon, dolu + dis_engel, olcu_yazilari)
    #  Sıra:  uzun yazı içeride, dışarıda;  ikisine de sığmıyorsa kısa yazı
    #  ( "h = 700" — çizgi korkuluk katmanında ) içeride, dışarıda.
    for m_, L_ in (
        (metin, eleman.yazi_eni(metin, uslup.NORMAL) + 20.0),
        (kisa, eleman.yazi_eni(kisa, uslup.NORMAL) + 20.0),
    ):
        for yon_, liste in ((ic_yon, ic_parca), (-ic_yon, dis_parca)):
            sigan = [p_ for p_ in liste if p_[1] - p_[0] >= L_]
            if sigan:
                p1, p2 = max(sigan, key=lambda t: t[1] - t[0])
                return m_, yon_, (p1 + p2) / 2.0
    #  Hiçbir boş parçaya sığmıyor:  çizgi boyunca her konumda çakışan
    #  yazı ve parça sayılır, en azı ( eşitse kısa yazı, içeride )
    engel_ = olcu_yazilari + [op] + list(parcalar_)
    en_iyi = None
    for m_ in (kisa, metin):
        L_ = eleman.yazi_eni(m_, uslup.NORMAL)
        for yon_ in (ic_yon, -ic_yon):
            u = serit.bas + L_ / 2.0
            while u <= serit.son - L_ / 2.0 + 1e-6:
                c_ = serit.cizgi + yon_ * 60
                k_ = (
                    (c_ - 20, u - L_ / 2.0, c_ + 20, u + L_ / 2.0)
                    if serit.dikey
                    else (u - L_ / 2.0, c_ - 20, u + L_ / 2.0, c_ + 20)
                )
                n_ = sum(1 for b_ in engel_ if ortusur(k_, b_)) + sum(
                    1 for s_ in kenarlar_ if geometri.kenar_kesisir(s_, k_)
                )
                if en_iyi is None or n_ < en_iyi[0]:
                    en_iyi = (n_, m_, yon_, u)
                u += 20.0
    if en_iyi is None:  # çizgi kısa yazıdan da kısa
        en_iyi = (0, kisa, ic_yon, (serit.bas + serit.son) / 2.0)
    _n, metin, yon_, orta = en_iyi
    return metin, yon_, orta
