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

#  Hiçbir değer "varsayılan" değildir:  çizim uydurma ölçüyle çizilmez.
#  Eksik anahtar dogrula() tarafından reddedilir.
#  ASKI DÜZENİ:  kasnakların ve askı noktalarının yeri buradan gelir.
#  Koda gömülmez — projeden projeye değişir ve kullanıcı seçer.
ASKI_DUZENLERI = ("Kabin altı", "Kabin üstü", "Doğrudan")

ZORUNLU = {
    "kuyu": ("genislik", "derinlik", "duvar_on", "duvar_arka", "duvar_sol", "duvar_sag"),
    "kabin": ("genislik", "derinlik", "kaciklik_y", "on_pay"),
    "kapi": ("genislik", "sol_pay"),
    "kabin_ray": ("arasi", "kapi_arasi", "b", "h"),
    "agirlik": ("yeri", "genislik", "derinlik", "ray_arasi", "ray_duvar", "b", "h"),
    #  2:1 askıda kasnak ölçüleri, 1:1'de askı noktası aralığı kullanılır.
    "aski": ("duzen",),
}

AGIRLIK_YERLERI = ("Sağ", "Sol", "Arka")

#  TS EN 81-20 m.5.2.5.3.1:  kuyunun iç yüzü ile kabin eşiği / kapı kasası
#  arası 0,15 m'yi aşamaz  ( kısa yükseklikte 0,20 m'ye çıkabilir ).
KAPI_ARASI_AZAMI = 150.0
#  TS EN 81-20 m.5.3.4.1:  kabin eşiği ile kat kapısı eşiği arası 35 mm.
ESIK_ARASI_AZAMI = 35.0

#  Çizimde kabin ile karşı ağırlık arasında aranan en küçük açıklık ( mm ).
#  Standardın sayısı DEĞİLDİR;  çizimin kendi tutarlılık kalkanıdır — iki
#  parçanın üst üste binmesini yakalar.
ASGARI_ACIKLIK = 20.0


def _aski_olculeri(g):
    """Askı düzeninin çizime giren ölçüleri  ( eksikse boş döner )."""
    a = g.get("aski") or {}
    duzen = a.get("duzen")
    if duzen in ("Kabin altı", "Kabin üstü"):
        return ("kasnak", a.get("kasnak_capi"), a.get("kasnak_arasi"),
                a.get("kasnak_kaciklik", 0))
    if duzen == "Doğrudan":
        return ("nokta", None, a.get("nokta_arasi"), a.get("nokta_kaciklik", 0))
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
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                hata.append(f"{bolum}.{a}: sayı olmalı ( {v!r} ).")
            elif a in ("kaciklik_y",):
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
        ag_kutu = (ex - ag["derinlik"] / 2.0, g["kabin_ray"]["kapi_arasi"] - ag["genislik"] / 2.0,
                   ex + ag["derinlik"] / 2.0, g["kabin_ray"]["kapi_arasi"] + ag["genislik"] / 2.0)
    else:
        ey = k["derinlik"] - ag["ray_duvar"]
        ag_kutu = (k["genislik"] / 2.0 - ag["genislik"] / 2.0, ey - ag["derinlik"] / 2.0,
                   k["genislik"] / 2.0 + ag["genislik"] / 2.0, ey + ag["derinlik"] / 2.0)
    if (ag_kutu[0] < kabin_kutu[2] + ASGARI_ACIKLIK and kabin_kutu[0] < ag_kutu[2] + ASGARI_ACIKLIK
            and ag_kutu[1] < kabin_kutu[3] + ASGARI_ACIKLIK
            and kabin_kutu[1] < ag_kutu[3] + ASGARI_ACIKLIK):
        hata.append("Karşı ağırlık kabin/şaseyle çakışıyor veya gerekli açıklık sağlanmıyor — ağırlık rayı – duvar ölçüsünü "
                    "ya da kabin ölçülerini gözden geçirin.")
    if ag_kutu[0] < 0 or ag_kutu[2] > k["genislik"] or ag_kutu[1] < 0 or ag_kutu[3] > k["derinlik"]:
        hata.append("Karşı ağırlık kuyunun dışına taşıyor.")
    #  ASKI DÜZENİ
    a = g.get("aski") or {}
    if a.get("duzen") not in ASKI_DUZENLERI:
        hata.append(f"aski.duzen: {ASKI_DUZENLERI} içinden olmalı ( {a.get('duzen')!r} ).")
    else:
        tur, cap, aralik, kaciklik = _aski_olculeri(g)
        gerekli = [("aralık", aralik)] + ([("kasnak çapı", cap)] if tur == "kasnak" else [])
        for ad, v in gerekli:
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
                hata.append(f"aski: {ad} sıfırdan büyük bir sayı olmalı ( {v!r} ).")
        if isinstance(aralik, (int, float)) and not isinstance(aralik, bool):
            yari = aralik / 2.0 + (cap / 2.0 if tur == "kasnak" and isinstance(cap, (int, float)) else 0)
            kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
            if kx - yari < 0 or kx + yari > k["genislik"]:
                hata.append("Askı kasnakları / noktaları kuyunun dışına taşıyor.")

    #  KAPI AÇIKLIKLARI — standardın kendi sınırları
    if kb["on_pay"] > KAPI_ARASI_AZAMI:
        hata.append(f"Kuyu iç yüzü ile kabin ön yüzü arası {kb['on_pay']:g} mm — "
                    f"TS EN 81-20 m.5.2.5.3.1 en çok {KAPI_ARASI_AZAMI:g} mm verir.")
    esik_arasi = kb["on_pay"] - S["kabin_esik_derinlik"] - S["esik_derinlik"]
    if esik_arasi > ESIK_ARASI_AZAMI:
        hata.append(f"Kabin eşiği ile kat kapısı eşiği arası {esik_arasi:g} mm — "
                    f"TS EN 81-20 m.5.3.4.1 en çok {ESIK_ARASI_AZAMI:g} mm verir.")
    return hata


#  ── DENEME GİRDİSİ  ─────────────────────────────────────────────────
#  ELEport'un yayımlanmış örnek projesinin ( PROJE 5 ) ölçüleri.  Kendi
#  çizimimizi onun paftasıyla ölçü ölçü karşılaştırabilmek için duruyor;
#  çizim mantığı ORADAN KOPYALANMAZ, yalnız sayılar denemede kullanılır.
ORNEK = {
    "proje": {"ad": "PROJE 5", "asansor": "Elevator 3", "olcek": 20},
    "kuyu": {"genislik": 2100, "derinlik": 1850,
             "duvar_on": 150, "duvar_arka": 150, "duvar_sol": 150, "duvar_sag": 150},
    #  on_pay:  kuyu iç yüzü ile kabin ön yüzü arası.  Eşikler ( kat 60 +
    #  kabin 40 ) düşülünce kalan açıklık m.5.3.4.1'in 35 mm sınırını
    #  aşmamalı → en çok 135.
    "kabin": {"genislik": 1350, "derinlik": 1400, "kaciklik_y": 130, "on_pay": 130},
    "kapi": {"genislik": 900, "sol_pay": 610, "yukseklik": 2100, "tip": "Teleskopik Sol"},
    "kabin_ray": {"arasi": 1550, "kapi_arasi": 1017, "b": 89, "h": 62},
    "agirlik": {"yeri": "Sol", "genislik": 1250, "derinlik": 250,
                "ray_arasi": 850, "ray_duvar": 130, "b": 70, "h": 65,
                "kasnak_capi": 400},
    #  2:1 askı, kasnaklar kabinin altında;  eksenleri kabin merkezinden
    #  125 mm kapıya doğru kaçık  ( ELEport örneğindeki yerleşim ).
    "aski": {"duzen": "Kabin altı", "kasnak_capi": 240, "kasnak_arasi": 1470,
             "kasnak_kaciklik": -125},
}
