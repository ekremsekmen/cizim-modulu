# -*- coding: utf-8 -*-
"""
TEST 12  —  DIŞ REFERANS PAFTALARI  ( başka programların çıktıları )

Motorun sayılarını, aynı asansörü hesaplayan BAŞKA İKİ PROGRAMIN yayımlanmış
paftalarına karşı doğrular:

    referans proje        ~/asansör projeleri/sample-project.pdf   ( PROJE 5 · Elevator 3 )
    "new block"    ~/asansör projeleri/new block-Model.pdf

NİÇİN AYRI TEST:  öteki bütün testler ya motoru KENDİ dondurulmuş referansımıza
ya da kendi altın çıktımıza karşı denetler.  İkisi de bizim yorumumuzdur — ikisinde
birden aynı yanlışı yapıyorsak hiçbiri bunu göremez.  Burada karşılaştırma
noktası dışarıdadır:  aynı standardı uygulayan, bizden bağımsız yazılmış iki
program.

BEKLENEN DEĞERLER PAFTALARIN KENDİ BASILI SAYILARIDIR.  Elle kopyalandılar;
kaynak satırları aşağıda tek tek yazılıdır ki doğrulanabilsinler.

TOLERANSLAR GEVŞEKTİR VE SEBEPLERİ YAZILIDIR.  İki program aynı standardı
uygular ama ara kabulleri ( kasnak ataleti modeli, yuvarlama, katalog
toleransı ) aynı değildir;  amaç birebir eşitlik değil, BİR YERDE SESSİZCE
AYRIŞMADIĞIMIZI görmektir.  Sapma büyürse buradan görünür.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet as MK  # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT  # noqa: E402
from testler.ortak import Rapor  # noqa: E402


# =====================================================================
#  REFERANS PROJE  —  sample-project.pdf  ·  "PROJE 5 / Elevator 3"
# =====================================================================
#  Girdiler paftanın "CALCULATION OF STEEL ROPES IN ROPE-TRACTION ELEVATORS"
#  başlıklı sayfasındaki girdi bloğundan alındı.  Son kat yüksekliği orada
#  yoktur;  2.900 mm alındı ( referans projenin kuyu boyu hesabına girmez ).
REFERANS_PROJE = {
    "beyan_yuku": 800,  # Actual Load Q : 800 kg
    "kabin_agirligi": 900,  # Empty Cabin Mass P : 900 kg
    "beyan_hizi": 1.6,  # Cabin Speed V : 1.6 m/s
    "aski_orani": 2,  # Roping Type 2/1 · r : 2
    "seyir_mesafesi": 29.0,  # Travel Distance Htravel : 29.0 m
    "son_kat_yuksekligi": 2900,
    "tahrik_kasnak_capi": 240,  # Traction Sheave Diameter Dt : 240 mm
    "saptirma_kasnak_capi": 294,  # Average diameter Dp : 294 mm
    "saptirma_kasnak_min_capi": 240,  # Minimum diameter Ds : 240 mm
    "halat_capi": 6.5,  # Rope Diameter dr : 6.5 mm
    "halat_adedi": 7,  # Number of Rope ns : 7 piece
    "halat_birim_kutle": 0.179,  # Rope Unit Mass ms : 0.179 kg/m
    "halat_kopma_kN": 31.5,  # Rope Breaking Force Sh : 31.5 kN
    "sarilma_acisi": 180,  # Rope Winding Angle α : 180°
    "kanal_sekli": "V Kanal",  # (V) Groove - Hardened
    "kanal_isleme": "Sertleştirilmiş",
    "kasnak_tek_yon": 2,  # Nps : 2 piece
    "kasnak_ters_yon": 0,  # Npr : 0 piece
    "acil_frenleme_a": 0.5,  # Emergency Braking Deceleration a : 0.5
    "denge_zinciri": "Var",  # Compensation Chain Ratio λ : 100 %
    "_ofis": {
        "q_denge": 0.50,  # Counterweight Balance Factor q : 50 %
        "kanal_gama_v": 38,
    },  # Traction Sheave Groove Angle γ : 38°
}

#  ( ad , hücre , referans projenin bastığı değer , izin verilen sapma % , gerekçe )
REFERANS_BEKLENEN = (
    #  Bunlar TANIM GEREĞİ aynı çıkmalı:  α doğrudan girdi, f ise
    #  m.5.11.2.3.1.2'nin kapalı bağıntısı ( μ / sin(γ/2) ).
    ("α  ( derece )", "tahrik.alfa_derece", 180.0, 0.01, "doğrudan girdi"),
    ("f  yükleme", "tahrik.f_yukleme", 0.307, 0.5, "referans proje 3 haneye yuvarlıyor"),
    ("f  bloke", "tahrik.f_bloke", 0.614, 0.5, "referans proje 3 haneye yuvarlıyor"),
    #  Yükleme durumu STATİKTİR:  kasnak ataleti ve sürtünme girmez, iki
    #  program da aynı kütleleri aynı bağıntıya koyar → birebir tutmalı.
    ("yükleme  T1", "tahrik.yukleme.T1", 9676.0, 0.05, "statik — ara kabul yok"),
    ("yükleme  T2", "tahrik.yukleme.T2", 6733.0, 0.05, "statik — ara kabul yok"),
    ("yükleme  T1/T2", "tahrik.yukleme.oran", 1.44, 0.5, "referans proje 2 haneye yuvarlıyor"),
    ("yükleme  e^(fα)", "tahrik.yukleme.sinir", 2.62, 0.5, "referans proje 2 haneye yuvarlıyor"),
    ("fren  e^(fα)", "tahrik.fren_ust.sinir", 2.08, 0.5, "referans proje 2 haneye yuvarlıyor"),
    ("bloke  e^(fα)", "tahrik.bloke.sinir", 6.89, 0.5, "referans proje 2 haneye yuvarlıyor"),
    #  FRENLEME:  sürtünme referans proje ile aynı yapıda ( kuyudaki kuvvet, / r );
    #  kalan küçük fark ağırlık tarafı oranıdır ( bizde %1,5, referans proje %2 ) —
    #  aşağıda referans projenin kendi oranı ve kablosuyla birebir denetlenir.
    ("fren alt  T1", "tahrik.fren_alt.T1", 8987.82, 0.01, "sürtünme yapısı referans proje ile aynı"),
    ("fren alt  T2", "tahrik.fren_alt.T2", 6514.24, 0.6, "ağırlık sürtünmesi %1,5 ↔ %2"),
    ("bloke  T1/T2", "tahrik.bloke.oran", 13.47, 2.0, "halat kütlesi dağılımı kabulü"),
)


def _referans_proje(r):
    s = MK.hesapla(dict(REFERANS_PROJE))
    r.kontrol("referans proje girdileri motorda geçerli", s.get("aktif"), f"→ {s.get('hata')}")
    if not s.get("aktif"):
        return
    h = s["ara"]
    for ad, anahtar, bek, tol, neden in REFERANS_BEKLENEN:
        v = h.get(anahtar)
        if v is None:
            r.kontrol(f"referans proje · {ad}", False, f"→ {anahtar} hesaplanmadı")
            continue
        sapma = abs(v - bek) / abs(bek) * 100
        r.kontrol(
            f"referans proje · {ad}  ( ≤ %{tol} )",
            sapma <= tol,
            f"→ bizim {v:.4f} · referans proje {bek} · sapma %{sapma:.2f}  ( {neden} )",
        )

    #  HALAT GÜVENLİK KATSAYISI  —  EN 81-50 m.5.12'nin kapalı bağıntısı.
    #  Ara kabul yoktur;  birebir tutmalıdır.
    r.kontrol(
        "referans proje · Sf ( gereken güvenlik katsayısı )",
        abs(s["ozet"]["Sf"] - 23.54) / 23.54 * 100 <= 0.5,
        f"→ bizim {s['ozet']['Sf']:.2f} · referans proje 23,54",
    )
    #  S ( gerçekleşen ):  bir halata düşen en büyük kuvvetten çıkar.  Referans proje
    #  MSR'yi kabin en alttayken alır, biz de;  kalan fark yuvarlamadır.
    r.kontrol(
        "referans proje · S ( gerçekleşen güvenlik katsayısı )",
        abs(s["ozet"]["S_gercek"] - 25.36) / 25.36 * 100 <= 1.0,
        f"→ bizim {s['ozet']['S_gercek']:.2f} · referans proje 25,36",
    )

    #  ── Dt/dh = 36,92 < 40  —  BELGE YOLU ────────────────────────────
    #  referans proje bu kontrolü "halat sertifikalı" diye atlar ve Sf'yi 12'ye
    #  indirir.  Biz belgesiz projede reddederiz;  belge beyan edilince
    #  oran kabul edilir ama Sf = 23,54 aynen aranır ( 7 halat S = 25,1 ).
    _hb = lambda x: next(b for b in x["bolumler"] if b["kimlik"] == "aski_halatlari")
    r.kontrol(
        "referans proje · belgesiz 240 / 6,5 halat bölümü UYGUN DEĞİL",
        _hb(s)["sonuc"]["uygun"] is False,
        f"→ {_hb(s)['sonuc']['metin']}",
    )
    s_b = MK.hesapla(dict(REFERANS_PROJE, kasnak_belgesi="Var"))
    r.kontrol(
        "referans proje · belgeyle halat bölümü UYGUN, Sf yine 23,54",
        _hb(s_b)["sonuc"]["uygun"] is True and abs(s_b["ozet"]["Sf"] - 23.54) / 23.54 * 100 <= 0.5,
        f"→ {_hb(s_b)['sonuc']['metin']} · Sf {s_b['ozet']['Sf']:.2f}",
    )

    #  ── REFERANS PROJENİN KENDİ İKİ KABULÜYLE BİREBİR ────────────────────────
    #  Kalan iki fark GİRDİDİR, bağıntı değil:  referans proje tek gezici kablo
    #  ( 0,44 kg/m ) ve ağırlık tarafında %2 sürtünme kullanır.  İkisi
    #  verilince frenleme ve bloke kuvvetlerinin altısı da yuvarlama içinde
    #  tutmalı — kasnak ataleti, halat dağılımı, zincir ve sürtünme dâhil.
    s_e = MK.hesapla(
        dict(
            REFERANS_PROJE,
            kablo_birim_kutle=0.44,
            _ofis=dict(REFERANS_PROJE["_ofis"], kuyu_surtunme_agirlik=2),
        )
    )
    for _ad, _h, _bek in (
        ("fren alt T1", "tahrik.fren_alt.T1", 8987.82),
        ("fren alt T2", "tahrik.fren_alt.T2", 6514.24),
        ("fren üst kabin", "tahrik.fren_ust.T1", 4641.92),
        ("fren üst ağırlık", "tahrik.fren_ust.T2", 6963.68),
        ("bloke T1", "tahrik.bloke.T1", 4802.29),
        ("bloke T2", "tahrik.bloke.T2", 356.5),
    ):
        _v = s_e["ara"][_h]
        r.kontrol(
            f"referans proje · kendi kablosu ve %2 ile {_ad} birebir  ( ≤ 0,05 N )",
            abs(_v - _bek) <= 0.05,
            f"→ bizim {_v:.3f} · referans proje {_bek}",
        )

    #  ── KARŞI AĞIRLIK RAYI:  PATEN TİPİ RAY BAŞINA ─────────────────────
    #  referans proje kabinde kaymalı, karşı ağırlıkta MAKARALI paten kullanır
    #  ( "Guide Shoe Type : Roller Type" ) ve flanş gerilmesini 1,85·Fx/c²
    #  ile hesaplar.  Karşı ağırlık rayında zinciri saymadığı için ( Mcwt =
    #  1.300 kg ) karşılaştırma zincirsiz yapılır.  Birim:  N/cm² → N/mm².
    s_a = MK.hesapla(
        dict(
            REFERANS_PROJE,
            denge_zinciri="Yok",
            agirlik_ray_profili="70 x 65 x 9",
            agirlik_konsol_arasi=1200,
            agirlik_paten_arasi=1500,
            agirlik_genisligi=850,
            agirlik_derinligi=160,
            paten_tipi="Kaymalı",
            agirlik_paten_tipi="Makaralı",
        )
    )
    for _ad, _h, _bek in (
        ("Fx", "agirlik_ray.Fx", 81.62),
        ("Fy", "agirlik_ray.Fy", 433.6),
        ("σF  makaralı paten", "agirlik_ray.sf", 4.1943),
    ):
        _v = s_a["ara"][_h]
        r.kontrol(
            f"referans proje · ağırlık rayı {_ad} birebir  ( ≤ %0,05 )",
            abs(_v - _bek) / _bek * 100 <= 0.05,
            f"→ bizim {_v:.4f} · referans proje {_bek}",
        )

    #  ── KABİN RAYI:  REFERANS PROJENİN KENDİ AĞIRLIK MERKEZİYLE ───────────────
    #  referans proje P'nin ağırlık merkezini doğrudan sorar:  Xp = +25 cm,
    #  Yp = −15 cm ( kabin merkezi Xc = −14 cm ).  Program bunu türetemezdi;
    #  "Boş kabinin ağırlık merkezi" girdileri ( Gelişmiş ) ile aynı proje
    #  girilebilir.  Ray T75/B, l = 200 cm, h = 330 cm, Rm = 450, kaymalı paten
    #  lp = 14 cm, tek gezici kablo 0,44 kg/m.  Birim:  N/cm² → N/mm², cm → mm.
    s_k = MK.hesapla(
        dict(
            REFERANS_PROJE,
            kabin_derinligi=1400,
            kabin_genisligi=1350,
            ray_kapi_arasi=970,
            aski_kaciklik_x=250,
            aski_kaciklik_y=50,
            kabin_agirlik_merkezi_x=250,
            kabin_agirlik_merkezi_y=-150,
            kabin_ray_profili="75 x 62 x 10",
            kabin_konsol_arasi=2000,
            kabin_paten_arasi=3300,
            ray_celigi_rm=450,
            guvenlik_tertibati="Kaymalı",
            paten_tipi="Kaymalı",
            paten_balata_boyu=140,
            kablo_birim_kutle=0.44,
        )
    )
    r.kontrol(
        "referans proje · kabin rayı girdileri ( Rm 450 · xp · yp ) geçerli",
        s_k.get("aktif"),
        f"→ {s_k.get('hata')}",
    )
    if s_k.get("aktif"):
        k = lambda ad: s_k["ara"]["kabin_ray." + ad]
        for _ad, _v, _bek, _tol in (
            ("güv. tert. yük önde  Fx", k("c21.d1.Fx"), 810.85, 0.01),
            ("güv. tert. yük önde  |Fy|", abs(k("c21.d1.Fy")), 873.14, 0.01),
            ("güv. tert. yük yanda  Fx", k("c21.d2.Fx"), 394.67, 0.01),
            ("güv. tert. flanş σF  ( N/mm² )", k("c21.d1.sf"), 11.7425, 0.01),
            ("normal işletme yük yanda  |Fx|", abs(k("c22.d2.Fx")), 556.49, 0.01),
            ("σperm güvenlik  ( Rm 450 / 1,8 )", k("sperm_g"), 250.0, 0.001),
            ("σperm normal  ( Rm 450 / 2,25 )", k("sperm_n"), 200.0, 0.001),
            ("eşik kuvveti Fs", k("Fs"), 3139.2, 0.01),
        ):
            r.kontrol(
                f"referans proje · kabin rayı {_ad} birebir  ( ≤ %{_tol} )",
                abs(_v - _bek) / _bek * 100 <= _tol,
                f"→ bizim {_v:.3f} · referans proje {_bek}",
            )
        #  Sehim cm'de 2 haneye yuvarlı basılır ( 0,17 · 0,12 cm ).
        for _ad, _v, _bek in (("δx", k("c21.d1.dx"), 1.7), ("δy", k("c21.d1.dy"), 1.2)):
            r.kontrol(
                f"referans proje · kabin rayı güv. tert. {_ad} ( ±0,05 mm )",
                abs(_v - _bek) <= 0.05,
                f"→ bizim {_v:.3f} mm · referans proje {_bek} mm",
            )
        #  ω:  λ = l / iy = 128,45.  Aynı λ ile ω referans projenin 3,53'ü;  program
        #  λ'yı yukarı tam sayıya ( 129 ) yuvarladığı için biraz büyük alır.
        r.kontrol(
            "referans proje · ω ( Rm 450 ara değeri, λ = 128,45 ) = 3,53",
            abs(MT.omega_en8150(128.45, 450) - 3.53) <= 0.005,
            f"→ {MT.omega_en8150(128.45, 450):.4f}",
        )
        #  BİLİNEN FARK 1 — YÜKÜN YÖNÜ.  m.5.7.2.3.4 yükü "en olumsuz" konuma
        #  koyar;  program ±Dy/8'i dener, referans proje yalnız +Dy/8'i alır.  İki
        #  değer de referans projenin kendi kütle ve konumlarıyla yeniden üretilir.
        _gn, _Q, _P, _h = 9.81, 800, 900 + 72.67 + 6.38, 3300
        _arti = 2 * _gn * (_Q * 168.75 + _P * -150) / _h
        _eksi = 2 * _gn * (_Q * -168.75 + _P * -150) / _h
        r.kontrol(
            "referans proje · güv. tert. yük yanda Fy:  referans proje +Dy/8 ( 70,50 N )",
            abs(abs(_arti) - 70.50) <= 0.05,
            f"→ {_arti:.2f}",
        )
        r.kontrol(
            "referans proje · güv. tert. yük yanda Fy:  bizde en olumsuz yön ( −Dy/8 )",
            abs(abs(k("c21.d2.Fy")) - max(abs(_arti), abs(_eksi))) <= 0.05,
            f"→ bizim {k('c21.d2.Fy'):.2f} · +Dy/8 {_arti:.2f} · −Dy/8 {_eksi:.2f}",
        )
        #  BİLİNEN FARK 2 — NORMAL İŞLETMEDE P.  Referans proje güvenlik tertibatında
        #  P'ye zinciri ve kabloyu katar ( 979 kg ), normal işletmede katmaz
        #  ( 900 kg → Fy 784,8 N ).  Standardın P tanımı ikisinde de katar.
        _fy900 = 1.2 * _gn * (_Q * -50 + 900 * -200) / _h
        _fyP = 1.2 * _gn * (_Q * -50 + _P * -200) / _h
        r.kontrol(
            "referans proje · normal işletme Fy:  referans proje P = 900 kg ile 784,8 N",
            abs(abs(_fy900) - 784.8) <= 0.05,
            f"→ {_fy900:.2f}",
        )
        r.kontrol(
            "referans proje · normal işletme Fy:  bizde standardın P'si ( 979 kg )",
            abs(abs(k("c22.d1.Fy")) - abs(_fyP)) <= 0.05,
            f"→ bizim {k('c22.d1.Fy'):.2f} · P = 979 kg ile {_fyP:.2f}",
        )

    #  ── T1/T2 ETİKETİ:  AYNI SAYI, BAŞKA AD ───────────────────────────
    #  EN 81-50 m.5.11.2.1 T1 ve T2'yi "kasnağın İKİ YANINDAKİ kuvvetler"
    #  diye tanımlar, hangisinin T1 olduğunu söylemez.  Referans proje BÜYÜK olana
    #  T1 der ve yük durumuna göre taraf değiştirir;  biz T1'i HER ZAMAN
    #  KABİN tarafı sayarız ve paftaya "T1 ( kabin tarafı )" diye yazarız.
    #  "Boş kabin en üstte frenleme"de karşı ağırlık tarafı büyüktür, bu
    #  yüzden iki paftada T1 ve T2 yer değişmiş GÖRÜNÜR.  Oran max(a/b, b/a)
    #  alındığı için hüküm ikisinde de aynıdır.  Aşağısı bunu KANITLAR:
    #  taraflar eşleştirilince sayılar tutar.
    for ad, anahtar, bek in (
        ("kabin tarafı", "tahrik.fren_ust.T1", 4641.92),
        ("karşı ağırlık tarafı", "tahrik.fren_ust.T2", 6963.68),
    ):
        v = h.get(anahtar)
        sapma = abs(v - bek) / bek * 100 if v else 100
        r.kontrol(
            f"referans proje · fren üst {ad} ( taraf eşleşmesi )",
            sapma <= 2.0,
            f"→ bizim {v:.2f} · referans proje {bek}  ( referans proje büyüğe T1 der, biz kabin tarafına )",
        )


# =====================================================================
#  "NEW BLOCK"  —  new block-Model.pdf  ·  kabin rayı, yük arkada
# =====================================================================
#  Paftanın "2.2 Yuk dagilimi arkada iken sonuclar" bölümü.  Ray kesiti
#  kataloğumuzda birebir yoktur;  bu yüzden ray verileri ( Wx · Wy · Jx · Jy
#  · c ) paftanın KENDİ yazdığı sayılardır ve doğrudan bağıntıya konur.
#  Denetlenen şey KESİT VERİSİ DEĞİL, BAĞINTININ KENDİSİDİR.
BLOCK_RAY = {
    "k": 1.2,
    "Q": 1275,
    "P": 1200,
    "xQ": 175,
    "xP": -65,
    "yQ": -263,
    "n": 2,
    "h": 3200,
    "l": 1700,
    "Wy": 11400,
    "Wx": 20800,
    "Jy": 515000,
    "Jx": 1012000,
    "c": 9,
    "sigma_perm": 165,
}

#  ( ad , paftanın bastığı değer , tolerans )   —  kaynak satırlar yorumda
BLOCK_BEKLENEN = (
    ("Fx  ( yük arkada )", 266.0, 1.0),  # "Fx = 266 N"
    ("My  ( yük arkada )", 84794.0, 1.0),  # "My = 84794 Nm"
    ("σy  ( yük arkada )", 7.4, 2.0),  # "Sigm(y) = 7,4 N/mm^2"
    ("σF  ( flanş, arkada )", 6.1, 2.0),  # "Sigm(F) = 6,1 N/mm^2"
    ("δx  ( yük arkada )", 0.18, 5.0),  # "d(x) = 0,18 mm"
    ("Fy  ( yük solda )", -1231.0, 1.0),  # "Fy = -1231 N"
    ("σx  ( yük solda )", 18.9, 2.0),  # "Sigm(x) = 18,9 N/mm^2"
)


def _block(r):
    """Paftanın ray bağıntılarını KENDİ verisiyle yeniden kurar.

    Motorun aynı bağıntıları kullandığı TEST 9 ve 11'de denetleniyor;  burada
    denetlenen, BAĞINTILARIN dış bir paftayla aynı sonucu verdiğidir.
    """
    b = BLOCK_RAY
    gn = 9.81
    # C.2.1.1 a)  Fx = k1·gn·( Q·xQ + P·xP ) / ( n·h )
    Fx = b["k"] * gn * (b["Q"] * b["xQ"] + b["P"] * b["xP"]) / (b["n"] * b["h"])
    #  m.5.10.2:  My = 3·Fx·l / 16   ( iki açıklıklı sürekli kiriş )
    My = 3 * Fx * b["l"] / 16
    sy = My / b["Wy"]
    #  C.2.1.4:  σF = 1,85·Fx / c²
    sF = 1.85 * Fx / b["c"] ** 2
    #  C.2.1.5:  δ = 0,7·F·l³ / ( 48·E·J )
    dx = 0.7 * (Fx * b["l"] ** 3) / (48 * 210000 * b["Jy"])
    # "Yuk dagilimi solda":  xQ = 0, yQ = −263
    #  Paftanın Fy paydası  h'dir;  C.2.1.1 b) ( n/2 )·h ister — n = 2'de
    #  ikisi AYNIDIR.  Bu yüzden bu pafta o farkı gösteremez;  fark bizim
    #  kendi testimizde ( test_tsen_bagimsiz ) denetleniyor.
    Fy = b["k"] * gn * (b["Q"] * b["yQ"] + b["P"] * 0) / ((b["n"] / 2) * b["h"])
    Mx = 3 * Fy * b["l"] / 16
    sx = abs(Mx / b["Wx"])
    bulunan = {
        "Fx  ( yük arkada )": Fx,
        "My  ( yük arkada )": My,
        "σy  ( yük arkada )": sy,
        "σF  ( flanş, arkada )": sF,
        "δx  ( yük arkada )": dx,
        "Fy  ( yük solda )": Fy,
        "σx  ( yük solda )": sx,
    }
    for ad, bek, tol in BLOCK_BEKLENEN:
        v = bulunan[ad]
        sapma = abs(v - bek) / abs(bek) * 100
        r.kontrol(
            f"block · {ad}  ( ≤ %{tol} )",
            sapma <= tol,
            f"→ bağıntı {v:.4f} · pafta {bek} · sapma %{sapma:.2f}",
        )

    #  ── PAFTANIN KENDİ KUSURLARI  ( bizde OLMAMALI ) ──────────────────
    #  Bu pafta bizim değil;  ondan KOPYALAMAMAMIZ gereken şeyler de var.
    #  Aşağısı, aynı hatayı yapmadığımızı sabitler.
    s = MK.hesapla({})
    kb = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
    #  Bölünmez boşluk ( U+00A0 ) okuyan için boşluktur.
    metinler = " | ".join(str(a.get("formul") or "") for a in kb["adimlar"] if isinstance(a, dict)).replace(
        "\u00a0", " "
    )
    #  ① Paftanın Fy bağıntısı paydaya yalnız h yazar;  C.2.1.1 b) ( n/2 )·h
    #    ister.  n = 2'de ikisi aynıdır, n = 4'te pafta Fy'yi İKİ KAT
    #    büyük gösterir.  Bizde payda her zaman ( n/2 )·h olmalı.
    r.kontrol(
        "block · Fy paydası bizde ( n/2 )·h  ( paftada yalnız h )",
        "( n / 2 )" in metinler,
        f"→ {metinler[:150]}",
    )
    #  ② Pafta P'yi bölümden bölüme değiştiriyor ( ray 1.200 · tahrik 1.270 ·
    #    başka yerde 1.100 ).  Bizde P TEK KAYNAKTAN gelir.
    p_satir = [
        a
        for a in kb["adimlar"]
        if isinstance(a, dict) and str(a.get("formul") or "").startswith("P = boş kabin")
    ]
    r.kontrol(
        "block · P tek kaynaktan türüyor  ( paftada bölüme göre değişiyor )",
        len(p_satir) >= 1,
        f"→ {len(p_satir)} satır",
    )


def calistir():
    r = Rapor("TEST 12 — DIŞ REFERANS PAFTALARI (referans proje · new block)")
    _referans_proje(r)
    _block(r)
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
