# -*- coding: utf-8 -*-
"""
ÇİZİM GİRDİSİ SÖZLEŞMESİ  ( bütün ölçüler mm )

Sözlük, çizimin ihtiyaç duyduğu GEOMETRİDİR;  hesabın girdi setiyle aynı
değildir.  Bir kısmı hesaptan gelir ( kabin ölçüleri, ray–kapı arası … ),
bir kısmı yalnız çizime aittir ( duvar kalınlığı, kapı yeri … ).

EKSEN DÜZENİ  ( plan )
    x  →  kuyu genişliği boyunca, SOLDAN SAĞA  ( kapıya bakan için )
    y  →  derinlik;  0 = kapı duvarının İÇ yüzü, artı yön kuyunun arkası
    Kuyu iç boşluğunun sol-ön köşesi orijindir.
"""

import math


def _sonlu_sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


#  Hiçbir değer "varsayılan" değildir:  çizim uydurma ölçüyle çizilmez.
#  Eksik anahtar dogrula() tarafından reddedilir.
#  ASKI DÜZENİ:  kasnakların ve askı noktalarının yeri buradan gelir.
#  Koda gömülmez — projeden projeye değişir ve kullanıcı seçer.
ASKI_DUZENLERI = ("Kabin altı", "Kabin üstü", "Doğrudan")

ZORUNLU = {
    "kuyu": ("genislik", "derinlik", "duvar_on", "duvar_arka", "duvar_sol", "duvar_sag"),
    "kabin": ("genislik", "derinlik", "kaciklik_y", "on_pay"),
    "kapi": ("genislik", "sol_pay", "montaj"),
    "kabin_ray": ("arasi", "kapi_arasi", "b", "h"),
    "agirlik": ("yeri", "genislik", "derinlik", "ray_arasi", "ray_duvar", "eksen_kaciklik",
                "b", "h"),
    #  2:1 askıda kasnak ölçüleri, 1:1'de askı noktası aralığı kullanılır.
    "aski": ("duzen",),
}

AGIRLIK_YERLERI = ("Sağ", "Sol", "Arka")
#  KAT KAPISININ MONTAJI:  kapı ünitesi ( kasa + eşik ) ya kuyu ön duvarının
#  boşluğuna oturur ( kasa duvarda, eşik kuyuya taşar ) ya da duvarın İÇ
#  YÜZÜNE monte edilir ( ünitenin tamamı kuyunun içinde — referans proje ).  İkisi de
#  aynı üründür;  yalnız kuyu içindeki yeri değişir.
KAPI_MONTAJLARI = ("Duvar boşluğuna", "Kuyu içine")

#  TS EN 81-20 m.5.2.5.3.1:  kuyunun iç yüzü ile kabin eşiği / kapı kasası
#  arası 0,15 m'yi aşamaz  ( kısa yükseklikte 0,20 m'ye çıkabilir ).
KAPI_ARASI_AZAMI = 150.0
#  TS EN 81-20 m.5.3.4.1:  kabin eşiği ile kat kapısı eşiği arası 35 mm.
ESIK_ARASI_AZAMI = 35.0

#  Kuyudaki iki sabit parça ( ara kiriş ile karşı ağırlık ) arasında aranan
#  en küçük açıklık ( mm ).  Standardın sayısı DEĞİLDİR;  çizimin kendi
#  tutarlılık kalkanıdır — iki parçanın üst üste binmesini yakalar.
ASGARI_ACIKLIK = 20.0
#  TS EN 81-20 m.5.2.5.5.1 h:  kabin ve ona bağlı parçalar karşı ağırlıktan
#  ve ona bağlı parçalardan en az 50 mm uzakta olmalıdır.
KABIN_AGIRLIK_ACIKLIGI = 50.0


def kapi_bolgesi(g, S):
    """Kapı bölgesinin derinlik kotları ( y, kuyu ön iç yüzünden ):

      kasa        kat kapısı kasası
      esik        kat kapısı eşiği ( kanatlar üstünde )
      hat         kapı hattı:  kat eşiğinin kabine bakan kenarı
      kabin_esik  kabin eşiği ( kabin kapısı kanatları üstünde ) — ön ucu
                  kabin ön yüzünden kabin_esik_derinlik kadar önde
      yuzey       m.5.2.5.3.1'in "kuyunun iç yüzü":  duvar boşluğuna montajda
                  duvarın kendisi;  kuyu içine montajda kapı hattı — kapıların
                  altında ve üstünde yüzey hat boyunca sac kaplamayla sürer
                  ( referans projenin düzeni ).
    """
    bas = -S["kasa_derinlik"] if g["kapi"]["montaj"] == "Duvar boşluğuna" else 0.0
    kasa = (bas, bas + S["kasa_derinlik"])
    esik = (kasa[1], kasa[1] + S["esik_derinlik"])
    on = g["kabin"]["on_pay"]
    kabin_esik = (on - S["kabin_esik_derinlik"], on)
    return {"kasa": kasa, "esik": esik, "hat": esik[1], "kabin_esik": kabin_esik,
            "yuzey": 0.0 if g["kapi"]["montaj"] == "Duvar boşluğuna" else esik[1]}


def _aski_olculeri(g):
    """Askı düzeninin çizime giren ölçüleri  ( eksikse boş döner )."""
    a = g.get("aski") or {}
    duzen = a.get("duzen")
    if duzen in ("Kabin altı", "Kabin üstü"):
        return ("kasnak", a.get("kasnak_capi"), a.get("kasnak_arasi"),
                a.get("kasnak_kaciklik", 0))
    if duzen == "Doğrudan":
        #  1:1:  tek bağlantı ( şasenin üst kirişinin ortası ) — aralığı yok
        return ("nokta", None, 0.0, a.get("nokta_kaciklik", 0))
    return (None, None, None, None)


def dogrula(g):
    """Eksik / geçersiz alanları metin listesi olarak döner ( boşsa temiz )."""
    hata = []
    for bolum, alanlar in ZORUNLU.items():
        d = g.get(bolum)
        if not isinstance(d, dict):
            hata.append(f"'{bolum}' bölümü eksik.")
            continue
        for a in alanlar:
            v = d.get(a)
            if a == "yeri":
                if v not in AGIRLIK_YERLERI:
                    hata.append(f"agirlik.yeri: {AGIRLIK_YERLERI} içinden olmalı ( {v!r} ).")
                continue
            if a == "duzen":
                continue                       # aşağıda ayrıca denetlenir
            if a == "montaj":
                if v not in KAPI_MONTAJLARI:
                    hata.append(f"kapi.montaj: {KAPI_MONTAJLARI} içinden olmalı ( {v!r} ).")
                continue
            if not _sonlu_sayi(v):
                hata.append(f"{bolum}.{a}: sayı olmalı ( {v!r} ).")
            elif a in ("kaciklik_y", "eksen_kaciklik"):
                continue                      # işaretli olabilir
            elif v <= 0:
                hata.append(f"{bolum}.{a}: sıfırdan büyük olmalı ( {v!r} ).")
    if hata:
        return hata
    #  GEOMETRİ TUTARLILIĞI — çizim kâğıda sığsın, parçalar çakışmasın.
    from cizim import sabitler as _CS
    S = _CS.sabitler(g.get("_cizim_sabitleri"))
    k, kb, kp = g["kuyu"], g["kabin"], g["kapi"]
    if kb["genislik"] >= k["genislik"]:
        hata.append(f"Kabin genişliği ({kb['genislik']}) kuyu genişliğinden ({k['genislik']}) küçük olmalı.")
    if kb["derinlik"] >= k["derinlik"]:
        hata.append(f"Kabin derinliği ({kb['derinlik']}) kuyu derinliğinden ({k['derinlik']}) küçük olmalı.")
    if kp["sol_pay"] + kp["genislik"] > k["genislik"]:
        hata.append("Kapı boşluğu kuyu genişliğine sığmıyor.")
    if g["kabin_ray"]["kapi_arasi"] >= k["derinlik"]:
        hata.append("Ray – kapı arası kuyu derinliğinden büyük olamaz.")
    if g["kabin_ray"]["arasi"] > k["genislik"]:
        hata.append("Kabin rayları arası kuyu genişliğine sığmıyor.")
    #  KABİN RAYLARININ ARASINDA GİDER:  ray ekseni kabinin derinliği içinden
    #  geçmeli;  geçmezse patenler kabine değil boşluğa bağlanır.
    if not (kb["on_pay"] <= g["kabin_ray"]["kapi_arasi"] <= kb["on_pay"] + kb["derinlik"]):
        hata.append(f"Kabin rayı ekseni ( kapıdan {g['kabin_ray']['kapi_arasi']:g} ) kabinin "
                    f"derinliği içinden geçmiyor ( kabin {kb['on_pay']:g} – "
                    f"{kb['on_pay'] + kb['derinlik']:g} ).")
    #  KABİN İLE KARŞI AĞIRLIK ÇAKIŞAMAZ.  Blok, ağırlık rayı eksenine
    #  ortalanır;  kabinin yanından en az ASGARI_ACIKLIK kadar uzak durmalı.
    ag = g["agirlik"]
    kx, ky = k["genislik"] / 2.0 + kb["kaciklik_y"], kb["on_pay"] + kb["derinlik"] / 2.0
    # İç ölçü yerine çizilen pano ve şasenin dış zarfını denetle.
    yari_en = kb["genislik"] / 2.0 + S["kabin_pano_yan"] + S["sase_dikme"]
    kabin_kutu = (kx - yari_en, kb["on_pay"], kx + yari_en,
                  kb["on_pay"] + kb["derinlik"] + S["kabin_pano_arka"])
    if (kabin_kutu[0] < 0 or kabin_kutu[2] > k["genislik"]
            or kabin_kutu[1] < 0 or kabin_kutu[3] > k["derinlik"]):
        hata.append("Kabin veya şasesi kuyunun dışına taşıyor.")
    if ag["yeri"] in ("Sağ", "Sol"):
        ex = ag["ray_duvar"] if ag["yeri"] == "Sol" else k["genislik"] - ag["ray_duvar"]
        ag_y = g["kabin_ray"]["kapi_arasi"] + ag["eksen_kaciklik"]
        ag_kutu = (ex - ag["derinlik"] / 2.0, ag_y - ag["genislik"] / 2.0,
                   ex + ag["derinlik"] / 2.0, ag_y + ag["genislik"] / 2.0)
    else:
        ey = k["derinlik"] - ag["ray_duvar"]
        ag_kutu = (k["genislik"] / 2.0 - ag["genislik"] / 2.0, ey - ag["derinlik"] / 2.0,
                   k["genislik"] / 2.0 + ag["genislik"] / 2.0, ey + ag["derinlik"] / 2.0)
    A = KABIN_AGIRLIK_ACIKLIGI
    if (ag_kutu[0] < kabin_kutu[2] + A and kabin_kutu[0] < ag_kutu[2] + A
            and ag_kutu[1] < kabin_kutu[3] + A and kabin_kutu[1] < ag_kutu[3] + A):
        hata.append(f"Karşı ağırlık ile kabin arasında {A:g} mm açıklık yok ( TS EN 81-20 "
                    "m.5.2.5.5.1 h ) — ağırlık rayı – duvar ölçüsünü ya da kabin ölçülerini "
                    "gözden geçirin.")
    if ag_kutu[0] < 0 or ag_kutu[2] > k["genislik"] or ag_kutu[1] < 0 or ag_kutu[3] > k["derinlik"]:
        hata.append("Karşı ağırlık kuyunun dışına taşıyor.")
    #  PARÇALAR KENDİ RAYLARININ ARASINA SIĞMALI.  Çerçeve / şase, iki rayın
    #  birbirine bakan yüzleri arasında kalır;  patenler bu aralıkta kayar.
    if ag["genislik"] >= ag["ray_arasi"]:
        hata.append(f"Karşı ağırlık genişliği ({ag['genislik']:g}) ağırlık rayları arasından "
                    f"( DBGW {ag['ray_arasi']:g} ) küçük olmalı — çerçeve iki rayın arasında durur.")
    # Rayların arkasındaki konsol plakaları da kuyu içinde kalmalı.
    # Yan yerleşimde bu zarf derinlikte, arka yerleşimde genişliktedir.
    ray_yari = ag["ray_arasi"] / 2.0 + ag["h"] + S["konsol_agirlik_boy"] / 2.0
    if ag["yeri"] in ("Sağ", "Sol"):
        tasiyor = (ag_y - ray_yari < 0 or ag_y + ray_yari > k["derinlik"]
                   or ex - ag["b"] / 2.0 < 0 or ex + ag["b"] / 2.0 > k["genislik"]
                   or S["konsol_agirlik_en"] > k["genislik"])
    else:
        tasiyor = (k["genislik"] / 2.0 - ray_yari < 0
                   or k["genislik"] / 2.0 + ray_yari > k["genislik"]
                   or ey - ag["b"] / 2.0 < 0 or ey + ag["b"] / 2.0 > k["derinlik"]
                   or S["konsol_agirlik_en"] > k["derinlik"])
    if tasiyor:
        hata.append("Karşı ağırlık rayları veya konsolları kuyunun dışına taşıyor.")
    sase_dis = kabin_kutu[2] - kabin_kutu[0]
    if sase_dis >= g["kabin_ray"]["arasi"]:
        hata.append(f"Kabin şasesinin dış genişliği ({sase_dis:g}) kabin rayları arasından "
                    f"( DBG {g['kabin_ray']['arasi']:g} ) küçük olmalı.")
    #  KAPI KABİNİN ÖNÜNE DÜŞMELİ:  kat kapısının net boşluğu kabin iç
    #  genişliğinin dışına taşarsa kabin kapısıyla karşılaşmaz.
    if kp["sol_pay"] < kx - kb["genislik"] / 2.0 or \
            kp["sol_pay"] + kp["genislik"] > kx + kb["genislik"] / 2.0:
        hata.append("Kat kapısı boşluğu kabinin önüne düşmüyor — kapının soldan uzaklığını "
                    "ya da kabinin yana kaçıklığını gözden geçirin.")
    #  AĞIRLIK YANDAYSA o taraftaki kabin rayı ağırlık konsollarına bağlı
    #  bir ara kirişte durur;  kiriş ağırlıkla kabin rayı arasına sığmalı.
    if ag["yeri"] in ("Sağ", "Sol"):
        kr_ = g["kabin_ray"]
        if ag["yeri"] == "Sol":
            ray_arkasi = kx - kr_["arasi"] / 2.0 - kr_["h"]
            bosluk = ray_arkasi - S["ara_kiris_en"] - ag_kutu[2]
        else:
            ray_arkasi = kx + kr_["arasi"] / 2.0 + kr_["h"]
            bosluk = ag_kutu[0] - (ray_arkasi + S["ara_kiris_en"])
        if bosluk < ASGARI_ACIKLIK:
            hata.append(f"Karşı ağırlık ile kabin rayının ara kirişi arasında {bosluk:g} mm kalıyor "
                        f"( en az {ASGARI_ACIKLIK:g} ) — ağırlık rayı – duvar ölçüsünü ya da "
                        "kabinin yana kaçıklığını gözden geçirin.")
    #  ASKI DÜZENİ
    a = g.get("aski") or {}
    if a.get("duzen") not in ASKI_DUZENLERI:
        hata.append(f"aski.duzen: {ASKI_DUZENLERI} içinden olmalı ( {a.get('duzen')!r} ).")
    else:
        tur, cap, aralik, kaciklik = _aski_olculeri(g)
        gerekli = ([("aralık", aralik), ("kasnak çapı", cap)] if tur == "kasnak" else [])
        for ad, v in gerekli:
            if not _sonlu_sayi(v) or v <= 0:
                hata.append(f"aski: {ad} sıfırdan büyük bir sayı olmalı ( {v!r} ).")
        if not _sonlu_sayi(kaciklik):
            hata.append(f"aski: kaçıklık sonlu bir sayı olmalı ( {kaciklik!r} ).")
        from cizim import arka_aski as CAA
        if CAA.arkada_iki_bir(g) and _sonlu_sayi(kaciklik):
            #  Arkadaki ağırlıkla 2:1:  kasnaklar çapraz düzlemde, aralığı
            #  geometriden ( arka_aski ) — sınırlarını o denetler.
            A = CAA.geometri(g, S)
            hata += [h for h in A["hata"] if "kuyunun dışına" in h]
        elif (all(_sonlu_sayi(v) and v > 0 for _, v in gerekli)
                and _sonlu_sayi(kaciklik)):
            yari = aralik / 2.0 + (cap / 2.0 if tur == "kasnak" else 45.0)
            kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
            aski_y = kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0 + kaciklik
            yari_y = S["kabin_kasnak_genislik"] / 2.0 if tur == "kasnak" else 45.0
            if (kx - yari < 0 or kx + yari > k["genislik"]
                    or aski_y - yari_y < 0 or aski_y + yari_y > k["derinlik"]):
                hata.append("Askı kasnakları / noktaları kuyunun dışına taşıyor.")

    #  KAPI AÇIKLIKLARI — standardın kendi sınırları, kabin EŞİĞİNİN ön
    #  kenarından ölçülür ( kabin gövdesinden değil )
    KB = kapi_bolgesi(g, S)
    kabin_esigi = KB["kabin_esik"][0]
    esik_arasi = kabin_esigi - KB["hat"]
    if esik_arasi <= 0:
        hata.append(f"Kabin eşiği kat kapısı eşiğine biniyor ( {esik_arasi:g} mm ):  kabin "
                    f"ön yüzü ( on_pay {kb['on_pay']:g} ) en az "
                    f"{KB['hat'] + S['kabin_esik_derinlik']:g} olmalı.")
    elif esik_arasi > ESIK_ARASI_AZAMI:
        hata.append(f"Kabin eşiği ile kat kapısı eşiği arası {esik_arasi:g} mm — "
                    f"TS EN 81-20 m.5.3.4.1 en çok {ESIK_ARASI_AZAMI:g} mm verir.")
    if kabin_esigi - KB["yuzey"] > KAPI_ARASI_AZAMI:
        hata.append(f"Kuyu iç yüzü ile kabin eşiği arası {kabin_esigi - KB['yuzey']:g} mm — "
                    f"TS EN 81-20 m.5.2.5.3.1 en çok {KAPI_ARASI_AZAMI:g} mm verir.")
    return hata


#  ── DENEME GİRDİSİ  ─────────────────────────────────────────────────
#  Yayımlanmış bir referans projenin ölçüleri.  Kendi
#  çizimimizi onun paftasıyla ölçü ölçü karşılaştırabilmek için duruyor;
#  çizim mantığı ORADAN KOPYALANMAZ, yalnız sayılar denemede kullanılır.
ORNEK = {
    "proje": {"ad": "ÖRNEK PROJE", "asansor": "ASANSÖR 1", "olcek": 20},
    "kuyu": {"genislik": 2100, "derinlik": 1850,
             "duvar_on": 150, "duvar_arka": 150, "duvar_sol": 150, "duvar_sag": 150},
    #  KAPI BÖLGESİ ( referans proje kuyu planı vektörleri, iç yüzden ):  kat kapısı
    #  ünitesi duvarın İÇ YÜZÜNE monte — kasa 0 – 60, eşik 60 – 150, kapı hattı
    #  150;  eşik aralığı 30;  kabin eşiği 180 – 270 → kabin ön yüzü 270.
    "kabin": {"genislik": 1350, "derinlik": 1400, "kaciklik_y": 130, "on_pay": 270},
    #  sol_pay:  kuyunun sol iç yüzünden kapının NET BOŞLUĞUNA ( kasa içi ).
    #  Referans projenin yazdığı 610, kasaya kadardır:  610 + kasa 120 = 730;  kapı
    #  ekseni böylece kabin ekseniyle aynı ( 1.180 ) olur.
    "kapi": {"genislik": 900, "sol_pay": 730, "yukseklik": 2100, "tip": "Teleskopik Sol",
             "montaj": "Kuyu içine"},
    #  kapi_arasi:  ray ekseni kuyunun ön İÇ YÜZÜNDEN.  Referans projenin "1017"si
    #  KAPI HATTINDAN ölçülür ( zincir 150 + 1017 + 682 = 1850 ):  iç yüzden
    #  1.167.  ( Eskiden 1.017 iç yüzden alınmıştı — arka duvar 150 geride kalıyordu. )
    "kabin_ray": {"arasi": 1550, "kapi_arasi": 1167, "b": 89, "h": 62},
    #  Karşı ağırlık çerçevesi referans proje paftasının vektör geometrisinden
    #  ölçüldü:  790 ( raylar boyunca ) × 160 mm — DBGW 850'nin içinde,
    #  iki uçta 30 mm paten payı.  ( Eski 1.250 × 250, makine dairesi
    #  çiziminden yanlış okunmuştu;  blok kendi raylarının dışına taşıyordu. )
    #  eksen_kaciklik:  yandaki ağırlığın ekseni kabin ray ekseninin 50 mm
    #  önünde ( referans proje paftasındaki "50" ölçüsü;  − = kapıya doğru ).
    "agirlik": {"yeri": "Sol", "genislik": 790, "derinlik": 160,
                "ray_arasi": 850, "ray_duvar": 130, "eksen_kaciklik": -50, "b": 70, "h": 65,
                "kasnak_capi": 400},
    #  2:1 askı, kasnaklar kabinin altında.  Kasnaklar arası referans proje
    #  paftasında 690 + 690 = 1.380 ( eski 1.470 yanlış okunmuştu;  halat
    #  kabin rayının ara kirişinin içinden geçiyordu ).
    #  KAÇIKLIK HALATLARI DÜŞEY İNDİRİR:  referans projede kabin kasnaklarının
    #  çizgisi = tahrik kasnağının çizgisi = ağırlık kasnağının ön teğeti
    #  ( ağırlık ekseni − 200 ).  Bu örnekte ağırlık ekseni 1.167 − 50 = 1.117,
    #  teğet 917;  kabin merkezi 270 + 1.433 / 2 = 986,5 → kaçıklık −69,5.
    "aski": {"duzen": "Kabin altı", "kasnak_capi": 240, "kasnak_arasi": 1380,
             "kasnak_kaciklik": -69.5, "halat_adedi": 7, "halat_capi": 6.5},
    #  Kabin üstü planı:  sığınma alanı tipi  ( TS EN 81-20 Çizelge 3 ).
    #  Hesap programındaki "Kabin üstü sığınma hacmi tipi" ile aynı seçim.
    "kabin_ustu": {"siginma_tipi": "Çömelme"},
    #  Kuyu dibi planı.  derinlik, sığınma tipi ve tampon adetleri hesap
    #  programında zaten vardır ( kuyu dibi yüksekliği KY, "Kuyu dibi sığınma
    #  hacmi tipi", kabin / ağırlık tamponu adedi );  köprü onları taşır.
    #  Regülatör gergi kasnağı referans proje paftasındaki gibi karşı ağırlığın
    #  karşısındaki kabin rayının hizasında, ray ekseninin 280 mm arkasında;
    #  gergi ağırlığı kasnağın 380 ötesine uzanır ( referans proje hesabı A = 300 ):
    #  1167 + 280 + 380 = 1827, arka duvara 23.  Üst regülatör de aynı ekseni
    #  kullanır.
    "kuyu_dibi": {"derinlik": 1500, "siginma_tipi": "Çömelme",
                  "kabin_tampon_adedi": 1, "agirlik_tampon_adedi": 1,
                  "regulator_yan": "Sağ", "regulator_kaciklik": 280,
                  #  Regülatör halatının çapı ( hesap programında "Regülatör
                  #  halatı çapı";  referans proje regülatör hesabı 6,0 ):  makine
                  #  dairesinde döşeme deliği bundan çıkar.
                  "regulator_halat_capi": 6,
                  "regulator_kasnak_capi": 300},
    #  DÜŞEY:  kabinin iç yüksekliği ve paten arası, son kat yüksekliği,
    #  beyan hızı, duraklar ve tamponlar — hepsi hesap programında var
    #  ( paten arası 3.300, beyan hızı, tampon kaideleri / boyları / ezilme /
    #  çarpma arası ).  Kuyu dibi referans projeninki:  1.500 = kaide 764 + tampon
    #  160 + çarpma arası 96 + kabinin şase altı 480.  Son kat referans proje 5.000.
    #  Duraklar:  8 × 3.000 → seyir 21 m ( hesap programının varsayılanı ).
    #  Ağırlık paten arası = karşı ağırlık çerçevesinin yüksekliği ( patenler
    #  uçlarında ):  referans proje çiziminde 2.920 ( hesabı 1.500 alır — kendi çizimiyle
    #  çelişir;  örnek çizimi izler ).
    "dusey": {"kabin_ic_yukseklik": 2250, "kabin_paten_arasi": 3300, "agirlik_paten_arasi": 2920,
              "son_kat": 5000, "beyan_hizi": 1.0, "durak_adedi": 8, "kat_yuksekligi": 3000,
              "kabin_tampon_baba": 764, "kabin_tampon_boyu": 160, "kabin_carpma_arasi": 96,
              "kabin_tampon_ezilme": 90, "agirlik_tampon_baba": 300, "agirlik_tampon_boyu": 160,
              "agirlik_carpma_arasi": 150, "agirlik_tampon_ezilme": 90,
              #  Konsollar arası ( hesap programının "kabin / ağırlık rayı
              #  konsollar arası en uzun mesafe" girdileri ) — referans proje 1.500.
              "kabin_konsol_arasi": 1500, "agirlik_konsol_arasi": 1500},
    #  Makine:  tahrik kasnağı çapı hesap programında var ( D1 ).  Kuyu üstü
    #  ( MRL ) ve makine dairesi planları ortak okur.
    #  Makinenin yeri:  "Kuyu üstü" ( makine dairesiz — referans proje ) ya da
    #  "Makine dairesi";  hesap programındaki "Makine dairesiz ( MRL )" seçimi.
    #  Makine tipi:  hesap programının "Makine tipi" ( Dişlisiz / Dişli );  çizim
    #  makineyi buna göre çizer ( makine.py:  LiftDesigner makineleri ).
    #  Yan yatak:  hesap programının "F ( yan yatak — makine kirişi )" NPU'su —
    #  makinenin oturduğu iki kiriş ( kuyu üstünde raylara, makine dairesinde
    #  kaidenin dikine kirişlerine oturur ).  Referans proje:  UPN 200 ( şase hesabında
    #  Wx 191 cm³ ).
    "makine": {"tahrik_kasnak_capi": 240, "yeri": "Kuyu üstü", "tip": "Dişlisiz", "yan_yatak": 200},
    #  Kuyu üstü planı ( makine dairesiz ):  acil kurtarma panosu en üst
    #  kattaki kapının hangi yanında.
    "kuyu_ustu": {"acil_pano_yan": "Sol"},
    #  Makine dairesi ( makine daireli asansör ).  İç ölçüler hesap
    #  programında var ( makine dairesi uzunluğu / genişliği;  örnek:  o
    #  programın kendi test verisi 3.800 × 2.600 ).  x, y:  odanın iç sol-ön
    #  köşesinin kuyunun iç sol-ön köşesine göre yeri — oda kuyunun üstünde,
    #  iki yana 100 mm taşar, önü kuyunun ön duvarıyla aynı hizada.
    #  Kapı ve pano duvarı:  "Ön" · "Arka" · "Sol" · "Sağ";  kapı konumu
    #  duvarın sol ( ön ) iç köşesinden kapı boşluğuna.
    "makine_dairesi": {"genislik": 2600, "derinlik": 3800, "duvar": 200, "x": -250, "y": -150,
                       "kapi_duvar": "Arka", "kapi_konum": 300, "kapi_genislik": 800,
                       "pano_duvar": "Sağ",
                       #  Düşey kesit için:  iç ( temiz ) yükseklik ( LiftDesigner
                       #  "477-8":  3.500 ).  Kapı yüksekliği:  TS EN 81-20 m.5.2.3.2 a'nın
                       #  en azı 2.000.
                       "yukseklik": 3500, "kapi_yukseklik": 2000,
                       #  Hesap programının makine dairesi girdileri ( adları aynı;
                       #  değerler o programın varsayılanları ):  tabliye beton
                       #  yüksekliği = oda döşemesinin ( kuyunun üstündeki betonun )
                       #  kalınlığı;  makine kaidesi:  şase yüksekliği ( dikine kirişin
                       #  boyu, döşemeden kaidenin üstüne ) ve dikine kiriş NPU'su.
                       #  Yan yatakların mesnet aralığı çizimden ( kaide makineyi sarar ).
                       "tabliye_yuksekligi": 1200, "sase_yuksekligi": 1100, "dikine_kiris": 120},
}
