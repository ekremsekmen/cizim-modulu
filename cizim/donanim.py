# -*- coding: utf-8 -*-
"""
KUYU DONANIMININ DÜŞEY YERLERİ

Planlar donanımın YATAY yerini verir ( kuyu_plani, kuyu_dibi, kuyu_ustu );
bu modül aynı parçaların KOTLARINI ekler ki düşey kesitler çizebilsin ve
açıklıkları denetleyebilsin:

  · makine, şasesi, tahrik kasnağı                ( makine dairesizde kuyu tepesinde )
  · kabin ve ağırlık halat bağlantıları           ( 2:1 askıda kuyu tepesinde )
  · hız regülatörü ( tepede ) ve gergi düzeni ( kuyu dibinde )
  · rayların üst uçları, konsolları, ek yerleri
  · karşı ağırlığın çerçevesi, kasnağı, patenleri

Kotlar sabitler.py'deki ELEport ölçüleridir.  Düşey eksen döşeme kotudur
( 0 = en alt durak );  kuyu tavanı = en üst durak + son kat.

Makine daireli projede makine, bağlantılar ve regülatör odadadır;  kuyuda
yalnız raylar ve karşı ağırlık kalır.  Rayların üst ucu o zaman kuyu
tavanının en alt kısmıdır ( tavan_kirisi ) — makine dairesinin düşey kesiti
henüz çizilmiyor.
"""
from cizim import kuyu_dibi as CKD
from cizim import kuyu_ustu as CKT

MAKINE_YERLERI = ("Kuyu üstü", "Makine dairesi")
ETEK_BOYU = 750.0           # m.5.4.5.1:  kabin eteğinin düşey kısmı en az 0,75 m


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _ortusur(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def kabin_kotlari(dy, S, z):
    """Döşemesi z kotundaki kabinin parça kotları ( ELEport kabini )."""
    tavan = z + dy["kabin_ic_yukseklik"] + S["kabin_tavan_kalinlik"]
    sase_alt = z - S["sase_alt_derinlik"]
    sase_ust = sase_alt + dy["kabin_paten_arasi"]
    return {"doseme": z, "taban_alti": z - S["kabin_taban_kalinlik"],
            "etek_alti": z - ETEK_BOYU, "fren_alti": z - S["kabin_taban_kalinlik"]
            - S["fren_blogu_yukseklik"], "sase_alt": sase_alt, "sase_ust": sase_ust,
            "alt_paten": sase_alt - S["paten_yukseklik"], "ust_paten": sase_ust + S["paten_yukseklik"],
            "ic_ust": z + dy["kabin_ic_yukseklik"], "tavan": tavan,
            "kasnak_merkez": z - S["kabin_kasnak_derinlik"]}


def konsol_kotlari(taban, ust, aralik, S):
    """Konsolların ÜST kotları:  tabandan konsol_ilk, sonra `aralik`;  rayın
    üst ucunu geçmez ( ELEport:  500 + 1.500 · n )."""
    z, kotlar = taban + S["konsol_ilk"], []
    while z <= ust + 1e-6:
        kotlar.append(z)
        z += aralik
    return kotlar


def ek_kotlari(taban, ust, S):
    """Ray eklerinin kotları:  kuyu tabanından her ray boyunda bir."""
    z, kotlar = taban + S["ray_boyu"], []
    while z < ust - 1e-6:
        kotlar.append(z)
        z += S["ray_boyu"]
    return kotlar


def yerlesim(g, S, H, tavan, taban):
    """H:  en üst durağın kotu ( seyir ),  tavan:  kuyu tavanı ( döşeme altı ),
    taban:  kuyu tabanı.  Dönen sözlükte her parça ( plandaki kutu, z0, z1 )."""
    mk, dy = g.get("makine") or {}, g.get("dusey") or {}
    hata = []
    yeri = mk.get("yeri")
    if yeri not in MAKINE_YERLERI:
        hata.append(f"makine.yeri: {MAKINE_YERLERI} içinden olmalı ( {yeri!r} ).")
    for alan in ("kabin_konsol_arasi", "agirlik_konsol_arasi"):
        if not (_sayi(dy.get(alan)) and dy[alan] > 0):
            hata.append(f"dusey.{alan}: sıfırdan büyük bir sayı olmalı ( {dy.get(alan)!r} ).")
    if hata:
        return {"hata": hata}
    KD = CKD.yerlesim(g, S)
    if KD["hata"]:
        return {"hata": KD["hata"]}
    mrl = yeri == "Kuyu üstü"
    ag = g["agirlik"]
    sol = ag["yeri"] == "Sol"
    kabin_raylari = sorted(KD["kabin_raylari"], key=lambda r: r[0])
    agirlik_raylari = KD["agirlik_raylari"]
    tavan_alti = tavan - S["tavan_kirisi"]
    M = {"mrl": mrl, "KD": KD, "hata": hata, "tavan": tavan, "tavan_alti": tavan_alti,
         "parcalar": []}

    if mrl:
        KU = CKT.yerlesim(g, S, acil_pano=False)
        if KU["hata"]:
            return {"hata": KU["hata"]}
        M["KU"] = KU
        G = g["kuyu"]["genislik"]
        #  ── MAKİNE ŞASESİ ve MAKİNE ────────────────────────────────────
        yakin_ray = kabin_raylari[0] if sol else kabin_raylari[-1]
        uzak_ray = kabin_raylari[-1] if sol else kabin_raylari[0]
        ya0 = min(r[1] for r in agirlik_raylari) - S["makine_sase_ray_payi"]
        ya1 = max(r[3] for r in agirlik_raylari) + S["makine_sase_ray_payi"]
        sase_x = ((S["makine_sase_duvar"], yakin_ray[0]) if sol
                  else (yakin_ray[2], G - S["makine_sase_duvar"]))
        z_ust = tavan - S["makine_tepe_boslugu"]
        zs = z_ust - S["makine_kapak_yukseklik"] - S["makine_en"]      # şase üstü
        sase = (sase_x[0], ya0, sase_x[1], ya1, zs - S["makine_sase_yukseklik"], zs)
        kx0, ky0, kx1, ky1 = KU["kasnak"]
        gx0, gy0, gx1, gy1 = KU["govde"]
        mx, my = (kx0 + kx1) / 2.0, (gy0 + gy1) / 2.0
        M.update({
            "sase": sase,
            "govde": (gx0, gy0, gx1, gy1, zs, zs + S["makine_en"]),
            "kapak": (mx - S["makine_kapak_en"] / 2.0, my - S["makine_kapak_boy"] / 2.0,
                      mx + S["makine_kapak_en"] / 2.0, my + S["makine_kapak_boy"] / 2.0,
                      zs + S["makine_en"], z_ust),
            "kasnak": KU["kasnak"] + (zs + S["makine_en"] / 2.0,),     # + merkez kotu
            "agirlik_baglanti": KU["agirlik_baglanti"] + (zs, zs + S["agirlik_baglanti_yukseklik"]),
            "kabin_baglanti": KU["kabin_baglanti"] + (tavan - S["kabin_baglanti_alt"],
                                                      tavan - S["kabin_baglanti_ust"]),
            "regulator": KU["reg_govde"] + (tavan - S["regulator_govde_alt"],
                                            tavan - S["regulator_govde_ust"]),
            "regulator_kasnak": KU["reg_kasnak"] + (tavan - S["regulator_kasnak_merkez"],),
        })
        #  Tavanın altındaki parçalar:  sığınma ve açıklıklar bunlara da ölçülür
        #  ( m.5.2.5.7.2:  "kuyu tavanının en alt kısımları — kirişler ve
        #  tavanın altına yerleştirilmiş parçalar dahil" ).
        for ad in ("sase", "kabin_baglanti", "agirlik_baglanti", "regulator"):
            p = M[ad]
            M["parcalar"].append((ad, p[:4], p[4]))
        #  Öbür kabin rayı ELEport'ta tavanın 50 altına çıkar;  kuyu tavanı payı
        #  ( tavan_kirisi ) daha büyükse onun altında kalır.
        ray_ust = {"yakin": zs - S["ray_sase_icinde"],
                   "uzak": min(tavan - S["kabin_rayi_tepe"], tavan_alti),
                   "agirlik": zs - S["ray_sase_icinde"]}
        M["raylar"] = [("kabin", yakin_ray, ray_ust["yakin"]),
                       ("kabin", uzak_ray, ray_ust["uzak"])] + \
                      [("agirlik", r, ray_ust["agirlik"]) for r in agirlik_raylari]
        M["regulator_x"], M["regulator_y"] = KU["rgx"], KU["rgy"]
    else:
        M["raylar"] = [("kabin", r, tavan_alti) for r in kabin_raylari] + \
                      [("agirlik", r, tavan_alti) for r in agirlik_raylari]
        rg = KD["gergi"]
        M["regulator_x"] = (rg[0] + rg[2]) / 2.0
        M["regulator_y"] = (rg[1] + rg[3]) / 2.0

    #  ── GERGİ DÜZENİ ( kuyu dibi ) ──────────────────────────────────────
    kd = g["kuyu_dibi"]
    ry = g["kabin_ray"]["kapi_arasi"]
    rgy = M["regulator_y"]
    s = 1.0 if rgy >= ry else -1.0                 # kol raydan kasnağa, öteye uzanır
    kol = sorted((ry - s * S["gergi_kol_ray"], rgy + s * S["gergi_kol_uc"]))
    agr = sorted((rgy + s * S["gergi_agirlik_yakin"], rgy + s * S["gergi_agirlik_uzak"]))
    M["gergi"] = {"merkez": taban + S["gergi_kasnak_merkez"], "cap": kd["regulator_kasnak_capi"],
                  "kol": (kol[0], kol[1], taban + S["gergi_kol_alt"],
                          taban + S["gergi_kol_alt"] + S["gergi_kol_yukseklik"]),
                  "agirlik": (agr[0], agr[1], taban + S["gergi_agirlik_alt"],
                              taban + S["gergi_agirlik_alt"] + S["gergi_agirlik_yukseklik"]),
                  "plan": KD["gergi"]}
    D = g["kuyu"]["derinlik"]
    if agr[0] < 0 or agr[1] > D:
        hata.append("Regülatör gergi ağırlığı kuyunun dışına taşıyor ( ELEport düzeni:  kol "
                    f"kasnağın {S['gergi_agirlik_uzak']:g} mm ötesine uzanır ).")

    #  ── RAYLAR:  konsollar ve ekler ─────────────────────────────────────
    raylar = []
    for tur, kutu, ust in M["raylar"]:
        aralik = dy["kabin_konsol_arasi"] if tur == "kabin" else dy["agirlik_konsol_arasi"]
        raylar.append({"tur": tur, "kutu": kutu, "alt": taban, "ust": ust,
                       "konsollar": konsol_kotlari(taban, ust, aralik, S),
                       "ekler": ek_kotlari(taban, ust, S)})
    M["raylar"] = raylar

    #  ── KARŞI AĞIRLIK ────────────────────────────────────────────────────
    M["agirlik"] = {"kutu": KD["blok"], "yukseklik": S["agirlik_yukseklik"],
                    "kasnak_ust": S["agirlik_kasnak_ust"], "paten": S["paten_yukseklik"],
                    "tampon_ustu": taban + dy["agirlik_tampon_baba"] + dy["agirlik_tampon_boyu"]}
    return M


def agirlik_kotlari(M, alt):
    """Alt kirişi `alt` kotundaki karşı ağırlığın parça kotları."""
    A = M["agirlik"]
    ust = alt + A["yukseklik"]
    return {"alt": alt, "ust": ust, "kasnak_merkez": ust - A["kasnak_ust"],
            "alt_paten": alt - A["paten"], "ust_paten": ust + A["paten"]}


def tavan_engeli(M, kutu):
    """`kutu`nun üstündeki en alçak tavan parçası:  ( kot, ad ).  Hiçbiri
    örtüşmüyorsa kuyu tavanının en alt kısmı ( kiriş )."""
    en = (M["tavan_alti"], "kuyu tavanı")
    for ad, p, z in M["parcalar"]:
        if _ortusur(p, kutu) and z < en[0]:
            en = (z, ad)
    return en
