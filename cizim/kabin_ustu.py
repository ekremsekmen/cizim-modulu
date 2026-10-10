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

from cizim import geometri as CGE
from cizim import girdi as CG
from cizim import sabitler as CS

#  TS EN 81-20 Çizelge 3 — kabin üstü sığınma alanının yatay ölçüleri ( mm ).
#  Adlar hesap programının "Kabin üstü sığınma hacmi tipi" seçenekleriyle
#  aynıdır;  köprü değeri olduğu gibi taşır.
SIGINMA = {"Dik duruş": (400.0, 500.0), "Çömelme": (500.0, 700.0)}
#  ve yüksekliği ( mm ) — dusey açıklığı bununla ölçer
SIGINMA_YUKSEKLIK = {"Dik duruş": 2000.0, "Çömelme": 1000.0}

#  TS EN 81-20 m.5.4.7.2 b:  tavan kenarından kuyu duvarına yatay boşluk
#  0,30 m'yi AŞARSA korkuluk gerekir.
KORKULUK_BOSLUK = 300.0
#  m.5.4.7.4 c:  korkuluk tavan kenarından en çok 0,15 m içeride durur.
KORKULUK_KENAR_AZAMI = 150.0
_ICERI = (
    "Korkuluğun kenardan içeri alınması:  küpeşte kuyudaki parçalardan en az "
    "0,10 m uzak durur ( TS EN 81-20 m.5.4.7.4 d ), kenardan en çok 0,15 m "
    "içeride ( m.5.4.7.4 c )."
)
#  m.5.4.7.4 d:  küpeştenin dış kenarı kuyudaki parçalardan ( karşı ağırlık,
#  raylar, konsollar … ) en az 0,10 m uzakta olmalıdır.
KORKULUK_PARCA_ASGARI = 100.0
#  m.5.4.7.4 b:  küpeştenin iç kenarından duvara boşluk 0,50 m'ye kadar ise
#  yükseklik en az 0,70 m, aşarsa en az 1,10 m.
KORKULUK_YUKSEKLIK_SINIRI = 500.0
KORKULUK_ALCAK, KORKULUK_YUKSEK = 700.0, 1100.0

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
        "aski_yazi",
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


def _kutu(el):
    return (el["x"], el["y"], el["x"] + el["g"], el["y"] + el["d"])


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def kapi_gorunusu(g, S):
    """Kabin üstü kesitinin kapıya göre yeri ( döşemeden, mm ):

      kesit   kesit kotu:  kabin iç yüksekliği + tavan kalınlığı
      acik    kesit kaba boşluğun içinde ( < kapı + kapi_ust_payi ):  ön duvar
              boşluklu;  değilse dolu, boşluk lentonun altında ( kesikli )
      kasa    kasa kesilir ( < kapı + kasa_ust )
    Kanatlar kapı yüksekliğindedir;  kabin iç yüksekliği kapıdan alçak
    olamaz ( girdi.dogrula ) — kanatlar her zaman kesitin altındadır."""
    kesit = g["dusey"]["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"]
    kapi_h = g["kapi"].get("yukseklik") or 0
    return {"kesit": kesit, "acik": kesit < CG.kaba_bosluk(g, S)[2], "kasa": kesit < kapi_h + S["kasa_ust"]}


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
        CG.kanat_cepleri(g, S, pay=False)
        if CG.kapi_tipi(kp.get("tip"))["tur"] != "manuel"
        else [(x0 - 0.5 * kg, x0), (x0 + kg, x0 + 1.5 * kg)]
    )
    #  Kanatların yolu tavandan geniş olabilir ( dar kabinde cep kabinin
    #  yanına taşar — LiftDesigner 4815-6 ):  operatör onu da örter.  Eskiden
    #  tavanın kenarında kırpılıyordu.
    x1, x2 = min([x0] + [c[0] for c in cep]), max([x0 + kg] + [c[1] for c in cep])
    if CG.kapi_tipi(kp.get("tip"))["tur"] == "manuel":
        x1, x2 = max(x1, tavan[0]), min(x2, tavan[2])  # cep bilinmez:  tavanda kırpılır
    return (x1, CG.kapi_bolgesi(g, S)["kabin_esik"][0], x2, tavan[1] + S["kabin_kapisi_kutu_boy"])


def yerlesim(g, cizim_sabitleri=None):
    """Kabin üstünün yerleşimi — çizim de doğrulama da bunu kullanır.

    Dönen:  { taban ( plan elemanları ), tavan, kenarlar, operator, engeller,
              siginma ( kutu ya da None ), hata [ … ] }
    """
    S = CS.sabitler(g.get("_cizim_sabitleri") if cizim_sabitleri is None else cizim_sabitleri)
    taban = CGE.plan(g, S, kapi_duzeyi=False, duvar_boslugu=kapi_gorunusu(g, S)["acik"])
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    tavan = _kutu(next(el for el in taban if el.get("ad") == "kabin_dis"))
    parcalar = [_kutu(el) for el in taban if el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI]
    hata = []

    #  ── KORKULUK:  her kenar ayrı değerlendirilir ─────────────────────
    #  bos:     tavan kenarından duvara  ( m.5.4.7.2 b )
    #  parca:   tavan kenarından o yandaki en yakın kuyu parçasına
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
            "gerekli": bos > KORKULUK_BOSLUK,
            "iceri": 0.0,
            "parca": min(yakin) if yakin else None,
            "yukseklik": None,
        }
        if k["gerekli"]:
            #  Küpeşte parçalardan 0,10 m uzak durmalı:  gerekirse içeri alınır
            k["iceri"] = max(0.0, KORKULUK_PARCA_ASGARI - (k["parca"] if yakin else 1e9))
            if k["iceri"] > KORKULUK_KENAR_AZAMI:
                hata.append(
                    f"{yan} kenarda korkuluk kuyudaki parçalara {KORKULUK_PARCA_ASGARI:g} mm "
                    f"uzak durmak için {k['iceri']:g} mm içeri alınmalı;  TS EN 81-20 "
                    f"m.5.4.7.4 c en çok {KORKULUK_KENAR_AZAMI:g} mm verir."
                )
            k["yukseklik"] = (
                KORKULUK_ALCAK if bos + k["iceri"] <= KORKULUK_YUKSEKLIK_SINIRI else KORKULUK_YUKSEK
            )
        kenarlar[yan] = k

    #  HALAT KUYUDAKİ BİR PARÇANIN İÇİNDEN GEÇEMEZ  ( kabin altı askı )
    halatlar = CGE.halat_konumlari(g, S)
    for hx, hy in halatlar:
        if not (0 < hx < G):
            hata.append(f"Halat kuyunun dışına düşüyor ( x = {hx:g} ) — kasnak aralığını gözden geçirin.")
            continue
        for el in taban:
            if el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI:
                p = _kutu(el)
                if p[0] - 20 < hx < p[2] + 20 and p[1] - 20 < hy < p[3] + 20:
                    hata.append(
                        f"Halat ( x = {hx:g}, y = {hy:g} ) kuyudaki bir parçanın "
                        f"( {el['katman'].lower()} ) içinden geçiyor."
                    )
                    break

    #  Sığınma alanı korkulukların içinde kalır
    ic = (
        tavan[0] + kenarlar["Sol"]["iceri"],
        tavan[1] + kenarlar["Ön"]["iceri"],
        tavan[2] - kenarlar["Sağ"]["iceri"],
        tavan[3] - kenarlar["Arka"]["iceri"],
    )

    #  ── TAVANDAKİ ENGELLER ───────────────────────────────────────────
    operator = _operator(g, tavan, S)
    #  Operatör kabinle gider:  tavandan taşan ucu kuyudaki bir parçaya değemez
    for p in parcalar:
        if _ortusur(operator, p):
            hata.append(
                f"Kabin kapısı operatörü ( kanatların yolu, x {operator[0]:g} – "
                f"{operator[2]:g} ) kuyudaki bir parçaya değiyor ( x {p[0]:g} – {p[2]:g}, "
                f"y {p[1]:g} – {p[3]:g} ):  kapıyı öbür yana açın ya da kabini kaydırın."
            )
            break
    engeller = [operator]
    duzen = (g.get("aski") or {}).get("duzen")
    if duzen == "Kabin üstü":
        engeller += CGE.kabin_kasnak_kutulari(g, S, taban)
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
                    f"Kabin üstü kasnağı {yan.lower()} kenardaki korkuluğun yolunu "
                    "kesiyor — kasnak aralığını daraltın."
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
    from cizim import arka_aski as CAA
    from cizim import donanim as CDN
    from cizim import hareketli as CH

    tip = (g.get("kabin_ustu") or {}).get("siginma_tipi")
    kt = CDN.kabin_kotlari(g["dusey"], S, 0.0, g.get("aski"), CAA.arkada_iki_bir(g))
    sinir = kt["tavan"] + SIGINMA_YUKSEKLIK.get(tip, max(SIGINMA_YUKSEKLIK.values()))
    engeller += [
        k
        for ad, k, alt, ust in CH.kabin_parcalari(g, S, taban, kt)
        if ad != CH.KABIN and ust > kt["tavan"] + 1e-9 and alt < sinir - 1e-9
    ]

    #  ── SIĞINMA ALANI  ( Çizelge 3 ) ──────────────────────────────────
    #  Kapıya en yakın, sonra kabin eksenine en yakın boş yer aranır:  bakımcı
    #  tavana kapıdan çıkar.
    siginma = None
    if tip not in SIGINMA:
        hata.append(f"kabin_ustu.siginma_tipi: {tuple(SIGINMA)} içinden olmalı ( {tip!r} ).")
    else:
        kx = (tavan[0] + tavan[2]) / 2.0
        adaylar = []
        for kenar in (False, True):
            adaylar = [
                (round(k[1], 3), abs((k[0] + k[2]) / 2.0 - kx), k)
                for w, h in {SIGINMA[tip], SIGINMA[tip][::-1]}
                for k in CGE.yer_adaylari(ic, w, h, engeller, kenar)
            ]
            if adaylar:
                break
        if adaylar:
            siginma = min(adaylar)[2]
        else:
            a, b = SIGINMA[tip]
            hata.append(
                f"Kabin tavanında {tip.lower()} tipi sığınma alanına ( {a:g} × {b:g} mm, "
                "TS EN 81-20 Çizelge 3 ) yer yok — korkulukların içinde;  kapı "
                "operatörü, şasenin üst kirişi ( ray ekseninde "
                f"{S['sase_dikme_derinlik']:g} mm — Sabitler:  kabin şasesi dikmesinin "
                "kesitteki eni ), kasnaklar ve aralarındaki halat dışında kalmalı."
            )
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


def _yazi_kutusu(el):
    """Ölçü yazısının kutusu ( yeri _yazilari_yerlestir'den ) — yazı yoksa boş."""
    y = el.get("yazi")
    if not y:
        return (0.0, 0.0, 0.0, 0.0)
    w, h = CGE._yazi_eni(el["metin"], y["h"]) / 2.0, y["h"] / 2.0
    if y["aci"]:
        w, h = h, w
    return (y["x"] - w, y["y"] - h, y["x"] + w, y["y"] + h)


def dogrula(g):
    """Kuyu planının doğrulaması + kabin üstünün kendi kuralları."""
    hata = CG.dogrula(g)
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
    S, tavan, ken = Y["S"], Y["tavan"], Y["kenarlar"]
    op = Y["operator"]  # çizilmez;  yazılar onun yerinden kaçar
    G, D = g["kuyu"]["genislik"], g["kuyu"]["derinlik"]
    dg, dar = g["kuyu"]["duvar_sag"], g["kuyu"]["duvar_arka"]
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
    tg, td = tavan[2] - tavan[0], tavan[3] - tavan[1]
    e.append(CGE._ad(CGE._dik("KABIN", tavan[0], tavan[1], tg, td), "tavan"))
    #  Şasenin üst kirişi tavanın üstünde, ray ekseninde dikmeden dikmeye
    #  ( kuyu planındaki zarfı;  kabin üstü kasnaklar onun da üstünde ).
    #  Eskiden bu planda yalnız dikmeler vardı:  askı görünmüyordu ( 3 Eki ).
    e += [el for el in Y["taban"] if el.get("ad") == "sase_kiris"]

    #  ── KAPI ( kapi_gorunusu ) ───────────────────────────────────────
    #  Kat kapısı kesitin altında, yukarıdan görünür:  eşik, kanatlar, cep.
    #  Kasa kesilir ya da üstü görünür:  her iki halde kapının üstünü boydan
    #  boya geçen tek parça ( dikmeler + üst kasa );  duvar boşluğuna monte
    #  kasa dolu lentonun altında kalır ( kesikli ).  Kabin kapısı da
    #  görünür:  operatör çizilmez ( LiftDesigner 1022 X-X ).
    KG = kapi_gorunusu(g, S)
    KB = CG.kapi_bolgesi(g, S)
    kp = g["kapi"]
    for el in Y["taban"]:
        ad = el.get("ad")
        if el["katman"] not in ("KAPI", "KABIN") or ad not in _KAPI_AD:
            continue
        el = dict(el)
        if ad == "kapi_boslugu" and not KG["acik"]:
            el["katman"] = "GIZLI"
        e.append(el)
    kasa = CGE._dik(
        "KAPI",
        kp["sol_pay"] - S["kasa_yan"],
        KB["kasa"][0],
        kp["genislik"] + 2 * S["kasa_yan"],
        KB["kasa"][1] - KB["kasa"][0],
    )
    if not KG["acik"] and kp["montaj"] == "Duvar boşluğuna":
        kasa["katman"] = "GIZLI"
    e.append(CGE._ad(kasa, "kapi_kasasi"))

    #  Kabin altı askıda halatlar tavanın DIŞINDAN, kasnakların dış
    #  teğetinden yukarı çıkar ( kabin üstü askıda halat tavandaki kasnaktan
    #  çıkar — kasnak zaten çizili )
    for hx, hy in Y["halatlar"] if (g.get("aski") or {}).get("duzen") == "Kabin altı" else ():
        e.append(CGE._ad(CGE._daire("KASNAK", hx, hy, 20), "halat"))
        e.append(CGE._yazi(hx, hy - 70, "HALAT", 36))

    #  ── KORKULUK ─────────────────────────────────────────────────────
    #  Küpeşte çizgisi, gerekli olan her kenarda iceri kadar içeride durur.
    ic = Y["ic"]
    for kutu, _ in korkuluklar(Y):
        e.append(CGE._ad(CGE._cizgi("KORKULUK", *kutu), "korkuluk"))

    #  ── SIĞINMA ALANI ────────────────────────────────────────────────
    sg = Y["siginma"]
    if sg:
        e.append(CGE._ad(CGE._dik("SIGINMA", sg[0], sg[1], sg[2] - sg[0], sg[3] - sg[1]), "siginma"))
        a, b = SIGINMA[Y["siginma_tipi"]]
        cx, cy = (sg[0] + sg[2]) / 2.0, (sg[1] + sg[3]) / 2.0
        e.append(CGE._yazi(cx, cy + 35, "SIĞINMA ALANI", 38))
        e.append(CGE._yazi(cx, cy - 35, f"{CGE.buyuk(Y['siginma_tipi'])}  {a:g} x {b:g}", 34))
    e += aski_el

    #  ── ÖLÇÜLER ──────────────────────────────────────────────────────
    O = CGE._olcu
    u0, u1 = D + dar + 120, D + dar + 320
    s0, s1 = G + dg + 120, G + dg + 320
    e += [
        O("yatay", (0, 0), (tavan[0], 0), u0),
        O("yatay", (tavan[0], 0), (tavan[2], 0), u0, f"KABİN TAVANI {tg:g}"),
        O("yatay", (tavan[2], 0), (G, 0), u0),
        O("yatay", (0, 0), (G, 0), u1, f"KUYU GENİŞLİĞİ {G:g}"),
        O("dusey", (0, 0), (0, tavan[1]), s0),
        O("dusey", (0, tavan[1]), (0, tavan[3]), s0, f"KABİN TAVANI {td:g}"),
        O("dusey", (0, tavan[3]), (0, D), s0),
        O("dusey", (0, 0), (0, D), s1, f"KUYU DERİNLİĞİ {D:g}"),
    ]
    #  Korkuluğun kenardan içeri alınması  ( 0'dan büyükse )
    for yan, k in ken.items():
        if not (k["gerekli"] and k["iceri"] > 1e-9):
            continue
        if yan in ("Sol", "Sağ"):
            x1, x2 = (tavan[0], ic[0]) if yan == "Sol" else (ic[2], tavan[2])
            #  Her kenarın ölçüsü kendi sırasında  ( iki kenar aynı sırada
            #  kopuk bir zincir oluştururdu )
            kot = tavan[3] - (120 if yan == "Sol" else 200)
            e.append(
                O(
                    "yatay",
                    (x1, 0),
                    (x2, 0),
                    kot,
                    f"{k['iceri']:g}",
                    kural=_ICERI,
                    yazi={
                        "x": (x2 + 30 + CGE._yazi_eni(f"{k['iceri']:g}", CGE.yb(40)) / 2.0)
                        if yan == "Sol"
                        else (x1 - 30 - CGE._yazi_eni(f"{k['iceri']:g}", CGE.yb(40)) / 2.0),
                        "y": kot,
                        "h": CGE.yb(40),
                    },
                )
            )
        else:
            y1, y2 = (ic[3], tavan[3]) if yan == "Arka" else (tavan[1], ic[1])
            kot = tavan[0] + (120 if yan == "Arka" else 200)
            e.append(
                O(
                    "dusey",
                    (0, y1),
                    (0, y2),
                    kot,
                    f"{k['iceri']:g}",
                    kural=_ICERI,
                    yazi={
                        "x": kot + 30 + CGE._yazi_eni(f"{k['iceri']:g}", CGE.yb(40)) / 2.0,
                        "y": (y1 + y2) / 2.0,
                        "h": CGE.yb(40),
                    },
                )
            )
    #  Sığınma alanının yeri — tavan kenarlarından
    if sg:
        yer = (
            "Sığınma alanının yeri:  program alanı kapıya en yakın, sonra kabin "
            "eksenine en yakın boş yere koyar ( 25 mm adımla;  dar boşlukta engelin "
            "kenarına yaslanarak )."
        )
        buyukluk = (
            f"Sığınma alanının ölçüsü:  TS EN 81-20 Çizelge 3 "
            f"( {str(g['kabin_ustu']['siginma_tipi']).lower()} )."
        )

        def olculer(kot_y, kot_x):
            return [
                O("yatay", (tavan[0], 0), (sg[0], 0), kot_y, kural=yer),
                O("yatay", (sg[0], 0), (sg[2], 0), kot_y, kural=buyukluk),
                O("yatay", (sg[2], 0), (tavan[2], 0), kot_y, kural=yer),
                O("dusey", (0, tavan[1]), (0, sg[1]), kot_x, kural=yer),
                O("dusey", (0, sg[1]), (0, sg[3]), kot_x, kural=buyukluk),
                O("dusey", (0, sg[3]), (0, tavan[3]), kot_x, kural=yer),
            ]

        #  İki sıranın yeri DENENEREK seçilir:  her aday için yazılar gerçekten
        #  yerleştirilir ( _yazilari_yerlestir ), yazıların öbür yazılara, kapı
        #  operatörüne, şasenin üst kirişine ve askı elemanlarına binmesi
        #  sayılır;  en az binen aday ( eşitse sıradaki ).  Korkuluk yazısı sonra
        #  konur ve bu yazılardan kendisi kaçar.
        #  Adaylar:  alanın arkası / önü ( sağı / solu ), içeride ön ( sol ) ve
        #  arka ( sağ ) kenarına yakın.  Eskiden tek kurallı seçim yazıları
        #  operatöre, korkuluk yazısına ve korkuluğun içeri alınma ölçüsüne
        #  bindiriyordu ( girdi taraması, 4 Eki ).
        engel = [CGE.sinir([el]) for el in e if el.get("ad") == "sase_kiris"] + list(Y["engeller"])
        yazilar = [CGE.sinir([el]) for el in e if el["tip"] == "yazi"]

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
            CGE._yazilari_yerlestir([el for el in e if el["tip"] != "olcu"] + dene, kaydir=True)
            diger = [_yazi_kutusu(el) for el in dene[: -len(yeni)]] + yazilar
            n = 0
            kutular_ = [_yazi_kutusu(el) for el in yeni if el["uzunluk"] >= 1e-6]
            for i_, k_ in enumerate(kutular_):
                n += sum(1 for b in diger + engel + kutular_[i_ + 1 :] if _ortusur(k_, b))
            return n

        adaylar = [
            (ky, kx)
            for ky in (sg[3] + 90, sg[1] - 90, sg[1] + 60, sg[3] - 110)
            for kx in (sg[2] + 90, sg[0] - 90, sg[2] - 110, sg[0] + 60)
        ]
        kot_y, kot_x = min(adaylar, key=lambda a: (puan(*a), adaylar.index(a)))
        e += olculer(kot_y, kot_x)
    #  KORKULUK YAZISI:  küpeşte boyunca, operatöre ve sığınma ölçüsüne
    #  denk gelmeyen en uzun boş parçanın ortasına.  Ölçü yazıları önce
    #  yerleşir:  yazının şeridine düşen ölçü yazısı da o parçayı doldurur.
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e, kaydir=True)
    olcu_yazilari = [_yazi_kutusu(el) for el in e if el["tip"] == "olcu"] + [
        CGE.sinir([el]) for el in e if el["tip"] == "yazi"
    ]
    #  Yazı çizilen küpeştenin çizgisine göre konur ( korkuluklar — ön kenarda
    #  operatörün arkasındadır, yanlarda operatörün arka yüzünden başlar ):
    #  eskiden tavanın kenarına göre konuyor, ön korkuluğun yazısı operatöre ve
    #  yan korkuluğun yazısına biniyordu.
    cizgiler = dict(zip([yan for yan, k in ken.items() if k["gerekli"]], korkuluklar(Y)))
    for yan, k in ken.items():
        if not k["gerekli"]:
            continue
        metin = f"KORKULUK  h = {k['yukseklik']:g}"
        dikey = yan in ("Sol", "Sağ")
        (cx0, cy0, cx1, cy1), _h = cizgiler[yan]
        bas, son = (min(cy0, cy1), max(cy0, cy1)) if dikey else (min(cx0, cx1), max(cx0, cx1))
        cizgi = cx0 if dikey else cy0
        dolu = []
        if dikey and op[0] <= cizgi <= op[2]:
            dolu.append((op[1], op[3]))
        if not dikey and op[1] <= cizgi <= op[3]:
            dolu.append((op[0], op[2]))
        #  Şasenin üst kirişi de küpeştenin üstünden geçer
        for el in e:
            if el.get("ad") == "sase_kiris":
                k_ = CGE.sinir([el])
                if dikey and k_[0] <= cizgi <= k_[2]:
                    dolu.append((k_[1] - 40, k_[3] + 40))
                if not dikey and k_[1] <= cizgi <= k_[3]:
                    dolu.append((k_[0] - 40, k_[2] + 40))
        for el in e:
            if el["tip"] == "olcu" and el["yon"] == ("yatay" if dikey else "dusey"):
                i = 0 if dikey else 1
                if min(el["a"][i], el["b"][i]) <= cizgi + 60 and cizgi - 60 <= max(el["a"][i], el["b"][i]):
                    dolu.append((el["kot"] - 70, el["kot"] + 110))
        #  Yazının şeridi küpeştenin içinde ( 40 – 80 mm );  içeride yazının
        #  boyunca boş parça yoksa küpeştenin DIŞINDA ( kabin ile duvar arası ),
        #  orada parçalardan da kaçarak.  Eskiden en uzun boş parçaya sığmasa da
        #  konuyordu:  sığınma ölçülerinin yazılarına biniyordu ( girdi taraması ).
        L = CGE._yazi_eni(metin, CGE.yb(40)) + 20.0
        ic_yon = 1.0 if yan in ("Sol", "Ön") else -1.0
        parcalar_ = [
            CGE.sinir([el])
            for el in e
            if (el["tip"] == "dikdortgen" and el["katman"] in _KUYU_PARCALARI + ("PATEN", "SASE"))
            or (el["tip"] == "daire" and el["katman"] == "KASNAK")
        ]  # halatlar

        def bos_parcalar(yon_, ek):
            serit = sorted((cizgi + yon_ * 40, cizgi + yon_ * 80))
            d_ = list(dolu) + list(ek)
            for k_ in olcu_yazilari:
                u0, u1 = (k_[0], k_[2]) if dikey else (k_[1], k_[3])
                if u0 < serit[1] and serit[0] < u1:
                    d_.append((k_[1], k_[3]) if dikey else (k_[0], k_[2]))
            out, a = [], bas
            for d1, d2 in sorted(d_):
                if d1 > a:
                    out.append((a, min(d1, son)))
                a = max(a, d2)
            if a < son:
                out.append((a, son))
            return out

        #  Şeridi kesen parça kenarları da şeridi doldurur ( yazı maskelidir —
        #  çapraz askının kasnağı çizgilerle çizilir, dikdörtgen sayılmıyordu;
        #  yazı kasnağın üstüne düşüyordu, 5 Eki )
        kenarlar_ = CGE.parca_kenarlari([el for el in e if el.get("ad") != "korkuluk"])

        def kenar_dolu(yon_):
            serit = sorted((cizgi + yon_ * 40, cizgi + yon_ * 80))
            bant = (serit[0], bas, serit[1], son) if dikey else (bas, serit[0], son, serit[1])
            return [
                (min(s_[1], s_[3]) - 10, max(s_[1], s_[3]) + 10)
                if dikey
                else (min(s_[0], s_[2]) - 10, max(s_[0], s_[2]) + 10)
                for s_ in kenarlar_
                if CGE.kenar_kesisir(s_, bant)
            ]

        ic_parca = bos_parcalar(ic_yon, kenar_dolu(ic_yon))
        dis_engel = kenar_dolu(-ic_yon)
        serit_dis = sorted((cizgi - ic_yon * 40, cizgi - ic_yon * 80))
        for k_ in parcalar_:
            u0, u1 = (k_[0], k_[2]) if dikey else (k_[1], k_[3])
            if u0 < serit_dis[1] and serit_dis[0] < u1:
                dis_engel.append((k_[1], k_[3]) if dikey else (k_[0], k_[2]))
        dis_parca = bos_parcalar(-ic_yon, dis_engel)
        #  Sıra:  uzun yazı içeride, dışarıda;  ikisine de sığmıyorsa kısa yazı
        #  ( "h = 700" — çizgi korkuluk katmanında ) içeride, dışarıda.
        kisa = f"h = {k['yukseklik']:g}"
        secim = None
        for m_, L_ in ((metin, L), (kisa, CGE._yazi_eni(kisa, CGE.yb(40)) + 20.0)):
            for yon_, liste in ((ic_yon, ic_parca), (-ic_yon, dis_parca)):
                sigan = [p_ for p_ in liste if p_[1] - p_[0] >= L_]
                if sigan:
                    secim = (m_, yon_, max(sigan, key=lambda t: t[1] - t[0]))
                    break
            if secim:
                break
        if secim:
            metin, yon_, (p1, p2) = secim
            orta = (p1 + p2) / 2.0
        else:
            #  Hiçbir boş parçaya sığmıyor:  çizgi boyunca her konumda çakışan
            #  yazı ve parça sayılır, en azı ( eşitse kısa yazı, içeride )
            engel_ = olcu_yazilari + [op] + [p_ for p_ in parcalar_]
            en_iyi = None
            for m_ in (kisa, metin):
                L_ = CGE._yazi_eni(m_, CGE.yb(40))
                for yon_ in (ic_yon, -ic_yon):
                    u = bas + L_ / 2.0
                    while u <= son - L_ / 2.0 + 1e-6:
                        c_ = cizgi + yon_ * 60
                        k_ = (
                            (c_ - 20, u - L_ / 2.0, c_ + 20, u + L_ / 2.0)
                            if dikey
                            else (u - L_ / 2.0, c_ - 20, u + L_ / 2.0, c_ + 20)
                        )
                        n_ = sum(1 for b_ in engel_ if _ortusur(k_, b_)) + sum(
                            1 for s_ in kenarlar_ if CGE.kenar_kesisir(s_, k_)
                        )
                        if en_iyi is None or n_ < en_iyi[0]:
                            en_iyi = (n_, m_, yon_, u)
                        u += 20.0
            if en_iyi is None:  # çizgi kısa yazıdan da kısa
                en_iyi = (0, kisa, ic_yon, (bas + son) / 2.0)
            _n, metin, yon_, orta = en_iyi
        if dikey:
            e.append(CGE._yazi(cizgi + yon_ * 60, orta, metin, 40, aci=90))
        else:
            e.append(CGE._yazi(orta, cizgi + yon_ * 60, metin, 40))
        olcu_yazilari.append(CGE.sinir([e[-1]]))  # sonraki korkuluğun yazısı kaçsın

    #  Sıfır boylu ölçü çizilmez  ( sığınma alanı kenara dayanmışsa )
    e = [el for el in e if not (el["tip"] == "olcu" and el["uzunluk"] < 1e-6)]
    CGE._yazilari_yerlestir(e, kaydir=True)
    CGE._parcadan_kaydir(e, ek_katman=("KAPI",))
    return e
