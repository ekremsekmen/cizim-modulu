# -*- coding: utf-8 -*-
"""
TEST 8  —  MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ  ( uygulama projesi )

motor/uygulama/mukavemet_tablolari.py içindeki her tabloyu KAYNAĞINA karşı
birebir doğrular:  dogrulama/referans_tablolar.json

NİÇİN AYRI TEST:  bu tablolar ofisin mukavemet hesabından makineyle
aktarıldı.  Aktarma sırasında bir sütun kayması ya da satır atlaması olsa
hiçbir hesap testi bunu göremezdi — motor kendi ( yanlış ) tablosuyla tutarlı
çalışırdı.  Kaynak tablolar bir kez okunup JSON olarak donduruldu;  bu test
aktarımın kendisini ve standarda göre yapılan genişletmeleri denetler.
"""

import json
import os
import sys

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import yollar

yollar.kur()

from motor.uygulama import mukavemet_girdi
from motor.uygulama import mukavemet_tablolari
from dogrulama.rapor import Rapor

REFERANS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referans_tablolar.json")

#  Kaynaktan aktarılan tablolar  ( modüldeki ad )
TABLOLAR = (
    "RAY_PROFILI",
    "RAY_GEOMETRI",
    "HALAT",
    "NPU_PROFIL",
    "KABIN_ALANI",
    "DARBE_TIPLERI",
    "AGIRLIK_MALZEMESI",
    "RAY_CELIGI",
    "BUKULGEN_KABLO",
)


#  KAYNAKTAN GENİŞLETİLEN TABLOLAR.  Kaynağın satırlarına dokunulmaz;
#  yalnız standardın gerektirdiği satırlar EKLENİR.  Burada hem "kaynağın
#  hiçbir satırı değişmedi" hem de "eklenenler beklenenlerdir" denetlenir —
#  yoksa genişletme, sessizce kaynak veriyi değiştirmenin kapısı olurdu.
GENISLETILEN = {
    #  T75/B ( 75 x 62 x 10 ) kaynak listede yoktu.  Orta kapasiteli
    #  asansörlerin en yaygın rayıdır.  Kesit değerleri ISO 7465'ten;
    #  iki bağımsız kaynak doğruluyor ( bkz. mukavemet_tablolari ).
    #  ISO 8100-33:2022'ye göre ( kullanıcı onayı 6 Eki 2026 ):  70'lik ve 90'lık
    #  Tablo 5'in T70/A · T90/A kesiti;  89'luğun boynu c = 10 ( bkz. modül ).
    "RAY_PROFILI": {
        "eklenen": ("75 x 62 x 10",),
        "degisen": {
            "70 x 65 x 9": (7.379, 940, 409500, 188600, 9169, 5389, 20.87, 14.17, 6, 20.34),
            "89 x 62 x 15,88": (12.38, 1577, 598300, 524100, 14350, 11780, 19.48, 18.23, 10, 20.32),
            "90 x 75 x 16": (13.54, 1725, 1020000, 524800, 20860, 11660, 24.31, 17.44, 10, 26.12),
        },
    },
    #  T50/A ( 50 x 50 x 5 ) paralel tabanlıdır:  taban kalınlığı her yerde
    #  p = 5 ( ISO 7465 Tablo 3 = ISO 8100-33 Tablo 4 ).  Kaynak f = 8 yazıyordu;
    #  kesitin alanı ( 475 mm² ) ancak 5 ile tutar.  Kullanıcı onayı 6 Eki 2026.
    "RAY_GEOMETRI": {"eklenen": ("75 x 62 x 10",), "degisen": {"50 x 50 x 5": (5, 13.5, 50, 31.5, 45)}},
    #  EN 81-20 Çizelge 6'da olup kaynakta olmayan beyan yükleri.
    "KABIN_ALANI": {
        "eklenen": (100, 1050, 1250, 1350, 1425, 1500, 2500),
        #  320 kg Çizelge 6'da YOKTUR;  standardın ara değer notu 300/375
        #  arası 0,953 m² verir, kaynak 0,97 yazar ( emniyetsiz taraf ).
        "degisen": {320: (4, 0.953, 0.79)},
    },
    #  EN 81-20 m.5.7.4.5:  σperm = Rm / St.  Kaynak oranları tam sayıya
    #  yuvarlıyordu;  Rm 370'te normal işletme 165 ( kesin 164,44 ) emniyetsiz
    #  yöndeydi.  Satırlar değişti.  450 EKLENDİ:  ISO 7465 m.5 aralığında
    #  ( 370 – 520 ) referans proje örneğinin işlenmiş ray çeliği;  ω EN 81-50
    #  m.5.10.3 ara değerinden, σperm aynı bağıntıdan.
    "RAY_CELIGI": {
        "eklenen": (450,),
        "degisen": {rm: (rm / 2.25, rm / 1.8) for rm in (370, 440, 520)},
    },
    #  BARİT:  kaynak 150 · 101;  standart blok 960 × 155 × 120 mm, 50 kg
    #  ( Tiraslift · Egeser katalogları ) — kullanıcı kararı ( karar 11 ):
    #  dolgunun sığma denetimi bu bloğun yoğunluğuyla, derinliğin başlangıç
    #  değeri bloğunki.
    "AGIRLIK_MALZEMESI": {"eklenen": (), "degisen": {"Barit": (155, 120)}},
    #  NPU:  üç değer DIN 1026-1'e göre düzeltildi ( bkz. mukavemet_tablolari ).
    #  Düzeltmeyi satırın KENDİ öteki sütunları doğrular ( aşağıda
    #  _profil_tutarliligi ):  30x15'in ix'i ancak Ix = 2,53 ile, 280 · 300'ün
    #  G'si ancak A = 53,3 · 58,8 ile tutar.
    "NPU_PROFIL": {
        "eklenen": (),
        "degisen": {
            "30x15": (2.21, 1.74, 2.53, 1.69, 1.07, 0.38, 0.39, 0.42),
            280: (53.3, 41.8, 6280, 448, None, 399, 57.2, None),
            300: (58.8, 46.2, 8030, 535, None, 495, 67.8, None),
        },
    },
}


def _profil_tutarliligi(r):
    """Profil tablolarının KENDİ İÇİNDEKİ bağıntıları  ( %2 ).

    Kaynağa karşı birebir karşılaştırma, kaynağın kendi yazım hatasını
    göremez:  NPU 30x15'te A değeri Ix sütununa da yazılmıştı, 280 · 300'ün
    A'sı G'leriyle çelişiyordu — üçü de yıllarca "kaynakla aynı" diye geçti.
    Kesit değerleri birbirinden bağımsız değildir:
        atalet yarıçapı  i = √( I / A )
        birim ağırlık    G = ρ · A     ( çelik 7.850 kg/m³ )
    """
    #  Sütun sayısı bozuk satırı tablo karşılaştırması zaten yazar — burada atlanır.
    for olcu, A, G, Ix, _Wx, ix, Iy, _Wy, iy in (x for x in mukavemet_tablolari.NPU_PROFIL if len(x) == 9):
        r.kontrol(
            f"NPU {olcu}: G = 0,785 × A",
            abs(G - 0.785 * A) <= 0.02 * G,
            f"→ G {G} · 0,785 × A {0.785 * A:.3f}",
        )
        for ad, i, I in (("ix", ix, Ix), ("iy", iy, Iy)):
            if i is not None:
                r.kontrol(
                    f"NPU {olcu}: {ad} = √( I / A )",
                    abs(i - (I / A) ** 0.5) <= 0.02 * i,
                    f"→ {ad} {i} · √( I / A ) {(I / A) ** 0.5:.3f}",
                )
    #  Flanş geometrisinin türetilen iki sütunu kendi satırından çıkar:
    #  ( h1 − b − f ) ve ( h1 − f ).  Biri düzeltilip öbürü unutulursa σF
    #  sessizce yanlış hesaplanırdı.
    for p, f, b, h1, h1_b_f, h1_f in (x for x in mukavemet_tablolari.RAY_GEOMETRI if len(x) == 6):
        r.kontrol(
            f"ray {p}: h1 − b − f",
            abs(h1_b_f - (h1 - b - f)) < 1e-6,
            f"→ {h1_b_f} · {h1} − {b} − {f} = {h1 - b - f}",
        )
        r.kontrol(f"ray {p}: h1 − f", abs(h1_f - (h1 - f)) < 1e-6, f"→ {h1_f} · {h1} − {f} = {h1 - f}")
    for p, Gr, A, Ix, Iy, _Wx, _Wy, ix, iy, _c, _e in (
        x for x in mukavemet_tablolari.RAY_PROFILI if len(x) == 11
    ):
        r.kontrol(
            f"ray {p}: Gr = 0,00785 × A",
            abs(Gr - 0.00785 * A) <= 0.02 * Gr,
            f"→ Gr {Gr} · 0,00785 × A {0.00785 * A:.3f}",
        )
        r.kontrol(
            f"ray {p}: ix = √( Ix / A )",
            abs(ix - (Ix / A) ** 0.5) <= 0.02 * ix,
            f"→ ix {ix} · √( Ix / A ) {(Ix / A) ** 0.5:.3f}",
        )
        #  125x82x16'nın iy'si kaynakta tutarsızdır ve bilerek öyle kalır:
        #  küçük iy burkulmayı emniyetli tarafta hesaplar;  paftaya not düşülür.
        if p not in mukavemet_tablolari.RAY_TUTARSIZ:
            r.kontrol(
                f"ray {p}: iy = √( Iy / A )",
                abs(iy - (Iy / A) ** 0.5) <= 0.02 * iy,
                f"→ iy {iy} · √( Iy / A ) {(Iy / A) ** 0.5:.3f}",
            )


def _kanal_tablosu(r, kaynak):
    """Nequiv(t) OFİS AÇILARINDAN türetilir;  varsayılan açılarda kaynakla birebir.

    Kaynak tablo her kanal şeklinin karşısına tek bir açı ve tek bir
    Nequiv(t) yazar.  Modül TS EN 81-50 Çizelge 2'yi kullanıp değeri γ / β'dan
    hesaplar;  ofisin varsayılan açılarında türetilen değer kaynakla AYNI
    olmalıdır.
    """
    from motor.uygulama import uygulama_sabitleri

    O = uygulama_sabitleri.sabitler(None)
    satir = {ad: tuple(v) for ad, v in kaynak.items()}
    r.esit("kaynak kanal tablosu satır sayısı", len(satir), len(mukavemet_tablolari.KANAL_SEKLI))
    for ad, _tur, _gecis in mukavemet_tablolari.KANAL_SEKLI:
        aci_x, neq_x = satir.get(ad, (None, None))
        #  Kaynağın "açı" sütunu iki büyüklüğü karıştırır:  V kanalda γ,
        #  altı kesik kanalda β.  Karşılaştırma buna göre yapılır.
        _tur = mukavemet_tablolari.kanal_turu(ad)
        bizim = mukavemet_tablolari.kanal_nequiv_t(ad, O["kanal_gama_v"], O["kanal_beta"])
        if _tur == "VK":
            #  ALTI KESİK V'DE BİLEREK AYRILIYORUZ:  kaynak onu Çizelge 2'nin
            #  β satırından okur ( 5,0 ), standart ise V satırındadır.
            #  Beklenen değer OFİS γ'SINI İZLER — sabitlendiğinde varsayılan
            #  değişince test kırılıyor ve kaynağı kendisi söylemiyordu.
            r.esit(f"kanal '{ad}' kaynakta β satırından okunuyor", neq_x, 5)
            r.esit(
                f"kanal '{ad}' bizde V satırından  ( standart )",
                bizim,
                mukavemet_tablolari.kanal_nequiv_t("V Kanal", O["kanal_gama_v"], O["kanal_beta"]),
            )
            continue
        #  KAYNAK TABLOSU KENDİ AÇISIYLA ÜRETİLMİŞTİR ( γ = 38° ).  Ofis
        #  varsayılanı Akış'ın yayımlanmış 45°'sine çekilince bu karşılaştırma
        #  "modül 45, kaynak 38" diye kırılıyordu — oysa denetlenmek istenen
        #  şey BAĞINTININ aynılığı, ofis kabulünün aynılığı değil.  Kaynağın
        #  kendi açısı verilerek karşılaştırılır.
        r.kontrol(
            f"kanal '{ad}' Nequiv(t) kaynağın kendi açısıyla aynı",
            _esit(mukavemet_tablolari.kanal_nequiv_t(ad, aci_x, aci_x), neq_x),
            f"→ modül {mukavemet_tablolari.kanal_nequiv_t(ad, aci_x, aci_x)!r}, kaynak {neq_x!r}",
        )
    #  ÇİZELGE 2'NİN KENDİSİ  —  TS EN 81-50 m.5.12.2.2
    for aci, bek in mukavemet_tablolari.NEQUIV_V:
        r.esit(f"Çizelge 2  V kanal γ = {aci}°", mukavemet_tablolari.kanal_nequiv_t("V Kanal", aci, 90), bek)
    #  β SATIRI "U-Undercut grooves" SATIRIDIR:  altı kesik YARIM DAİRE.
    #  Altı kesik V, Çizelge 2'nin V satırındadır.
    for aci, bek in mukavemet_tablolari.NEQUIV_U_ALTI_KESIK:
        r.esit(
            f"Çizelge 2  altı kesik yarım daire β = {aci}°",
            mukavemet_tablolari.kanal_nequiv_t("Altı Kesik Yarım Daire Kanal", 38, aci),
            bek,
        )
    for aci, bek in mukavemet_tablolari.NEQUIV_V:
        r.esit(
            f"Çizelge 2  altı kesik V γ = {aci}°  ( V satırı )",
            mukavemet_tablolari.kanal_nequiv_t("Altı Kesik V Kanal", aci, 90),
            bek,
        )
    r.esit(
        "altı kesik V'de β Nequiv'i değiştirmez",
        mukavemet_tablolari.kanal_nequiv_t("Altı Kesik V Kanal", 38, 105),
        12.0,
    )
    # ------------------------------------------------------------------
    #  TS EN 81-50 Ek E  —  STANDARDIN KENDİ ÇÖZÜMLÜ ÖRNEKLERİ
    #  Ek E üç sayısal örnek verir;  üçü de burada yeniden üretilir.
    #  E.1'de standart Kp'yi 2,07'ye YUVARLAYIP çarpar ( 2,07 × 2 = 4,14 );
    #  tam değer 2,0736 → 4,1472'dir.  Program yuvarlamaz, bu yüzden
    #  karşılaştırma standardın kendi yuvarlamasına tolerans tanır.
    # ------------------------------------------------------------------
    for _ad, _kanal, _g, _b, _Dt, _Dp, _nps, _npr, _nt, _neq in (
        ("E.1  2:1 · V kanal", "V Kanal", 40, 90, 600, 500, 2, 0, 10.0, 14.14),
        ("E.2  1:1 · altı kesik U", "Altı Kesik Yarım Daire Kanal", 38, 90, 600, 400, 1, 0, 5.0, 10.06),
        ("E.3  1:1 çift sarım · U", "Yarım Daire Kanal (Çift Sarım)", 38, 90, 600, 600, 2, 0, 2.0, 4.0),
    ):
        _t = mukavemet_tablolari.kanal_nequiv_t(_kanal, _g, _b)
        r.esit(f"Ek E {_ad}: Nequiv(t)", _t, _nt)
        _kp = (_Dt / _Dp) ** 4
        _n = _t + _kp * (_nps + 4 * _npr)
        r.kontrol(
            f"Ek E {_ad}: Nequiv = {_neq}", abs(_n - _neq) <= 0.01, f"→ program {_n:.4f}, standart {_neq}"
        )
        r.esit(
            "Çizelge 2  alt kesilmesiz yarım daire",
            mukavemet_tablolari.kanal_nequiv_t("Yarım Daire Kanal", 38, 90),
            1.0,
        )
    r.esit(
        "çift sarımda iki geçiş",
        mukavemet_tablolari.kanal_nequiv_t("Yarım Daire Kanal (Çift Sarım)", 38, 90),
        2.0,
    )
    #  Ara değer:  çizelgenin kendi notu doğrusal ara değere izin verir
    r.esit(
        "Çizelge 2  ara değer β = 87,5°  ( altı kesik yarım daire )",
        mukavemet_tablolari.kanal_nequiv_t("Altı Kesik Yarım Daire Kanal", 38, 87.5),
        4.4,
    )
    r.esit("Çizelge 2  ara değer γ = 39°", mukavemet_tablolari.kanal_nequiv_t("V Kanal", 39, 90), 11.0)
    r.esit(
        "Çizelge 2  ara değer γ = 43,5°  ( altı kesik V, V satırı )",
        mukavemet_tablolari.kanal_nequiv_t("Altı Kesik V Kanal", 43.5, 90),
        7.25,
    )


def _genisletilen_tablo(r, ad, tablo, kaynak):
    ex = {satir[0]: tuple(satir[1:]) for satir in kaynak}
    mo = {satir[0]: tuple(satir[1:]) for satir in tablo}
    kural = GENISLETILEN[ad]
    r.esit(f"{ad}: kaynağın satırlarının hepsi duruyor", sorted(set(ex) - set(mo), key=str), [])
    r.esit(
        f"{ad}: eklenenler beklenenlerle aynı",
        sorted(set(mo) - set(ex), key=str),
        sorted(kural["eklenen"], key=str),
    )
    #  Anahtarlar karışık türde olabilir ( NPU:  '30x15' ve 30 ) — metin olarak sıralanır.
    #  HÜCRE HÜCRE ve sütun sayısıyla:  toplu karşılaştırma ( zip ) eksik bir
    #  sütunu göremezdi;  değişmeyen tabloların denetimiyle aynı incelikte.
    for anahtar, deger in sorted(ex.items(), key=lambda kv: str(kv[0])):
        beklenen = kural["degisen"].get(anahtar, deger)
        if anahtar not in mo or not r.esit(f"{ad}[{anahtar}]: sütun sayısı", len(mo[anahtar]), len(beklenen)):
            continue
        for j, (mv, bv) in enumerate(zip(mo[anahtar], beklenen), 1):
            r.kontrol(
                f"{ad}[{anahtar}][{j}]",
                _esit(mv, bv),
                f"→ modül {mv!r}, beklenen {bv!r}  ( satır {mo[anahtar]!r} )",
            )
    #  Satır SIRASI da korunur ( seçim listeleri tablodan bu sırayla kurulur ).
    r.esit(f"{ad}: kaynağın satırları aynı sırada", [a for a in mo if a in ex], [a for a in ex if a in mo])


def _esit(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return (a if a is not None else "") == (b if b is not None else "")


def calistir():
    print("\n\033[1mTEST 8 — MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ\033[0m")
    r = Rapor("Mukavemet tabloları")
    with open(REFERANS, encoding="utf-8") as f:
        kaynak = json.load(f)

    for ad in TABLOLAR:
        tablo = getattr(mukavemet_tablolari, ad)
        ref = [tuple(x) for x in kaynak["tablolar"][ad]]
        if ad in GENISLETILEN:
            _genisletilen_tablo(r, ad, tablo, ref)
            continue
        if not r.esit(f"{ad}: satır sayısı", len(tablo), len(ref)):
            continue
        for i, (m, e) in enumerate(zip(tablo, ref)):
            if not r.esit(f"{ad}[{i}]: sütun sayısı", len(m), len(e)):
                continue
            for j, (mv, ev) in enumerate(zip(m, e)):
                r.kontrol(f"{ad}[{i}][{j}]", _esit(mv, ev), f"→ modül {mv!r}, kaynak {ev!r}")

    #  KANAL TABLOSU:  modül Nequiv(t)'yi ofis açılarından ve TS EN 81-50
    #  Çizelge 2'den türetiyor.
    _kanal_tablosu(r, kaynak["kanal"])
    _profil_tutarliligi(r)

    #  ω:  kaynak tablo λ = 20 … 250, Rm = 370 eğrisidir.  Modül standardın
    #  iki eğrisini ( 370 · 520 ) formülle kurar;  370 eğrisi tabloyu üretmeli.
    om = [tuple(x) for x in kaynak["omega"]]
    r.esit(
        "OMEGA: satır sayısı",
        mukavemet_tablolari.OMEGA_LAMBDA_MAX - mukavemet_tablolari.OMEGA_LAMBDA_MIN + 1,
        len(om),
    )
    r.esit("OMEGA: λ alt sınırı", mukavemet_tablolari.OMEGA_LAMBDA_MIN, om[0][0])
    r.esit("OMEGA: λ üst sınırı", mukavemet_tablolari.OMEGA_LAMBDA_MAX, om[-1][0])
    for lam, w in om:
        r.kontrol(
            f"ω(λ={lam}, Rm 370)",
            abs(mukavemet_tablolari.omega_en8150(lam, 370) - w) <= 0.006,
            f"→ modül {mukavemet_tablolari.omega_en8150(lam, 370)!r}, kaynak {w!r}",
        )
    r.kontrol(
        "ω tablo dışı λ için None",
        mukavemet_tablolari.omega_en8150(19) is None and mukavemet_tablolari.omega_en8150(251) is None,
    )

    #  AĞIRLIK RAY ARASI → GENİŞLİK TABLOSU KALDIRILDI:  TS EN 81-50 Ek C.2.2
    #  karşı ağırlığın KENDİ ölçülerini ( Gx · Gy ) veri olarak ister.
    #  Türetme işlevlerinin GERİ GELMEDİĞİ denetlenir.
    for _kalkti in (
        "AGIRLIK_RAY_ARASI",
        "RAY_ARALARI",
        "agirlik_genisligi",
        "agirlik_derinlik",
        "OMEGA",
        "omega",
        "KANAL_ISLEME",
        "surtunme",
    ):
        r.kontrol(
            f"kaldırılan tablo / türetme geri gelmedi: {_kalkti}", not hasattr(mukavemet_tablolari, _kalkti)
        )
    r.kontrol(
        "karşı ağırlık ölçüleri GİRDİ",
        all(a in mukavemet_girdi.ALAN for a in ("agirlik_genisligi", "agirlik_derinligi")),
    )

    #  Erişim işlevleri gerçekten doğru sütunu okuyor mu
    p = "89 x 62 x 15,88"
    r.esit("ray() Gr", mukavemet_tablolari.ray(p, "Gr"), 12.38)
    r.esit("ray() Wx", mukavemet_tablolari.ray(p, "Wx"), 14350)
    r.esit("ray() ix", mukavemet_tablolari.ray(p, "ix"), 19.48)
    r.esit("npu() A", mukavemet_tablolari.npu(120, "A"), 17)
    r.esit("npu() Wx", mukavemet_tablolari.npu(120, "Wx"), 60.7)
    r.esit("npu() ix", mukavemet_tablolari.npu(120, "ix"), 4.62)
    r.esit("halat_kopma()", mukavemet_tablolari.halat_kopma(6.5), 24700)
    r.esit("k2 sabiti", mukavemet_tablolari.K2_NORMAL_KULLANMA, 1.2)
    r.esit("kablo_agirligi()", mukavemet_tablolari.kablo_agirligi("24 x 0,75"), 0.642)
    r.kontrol(
        "bilinmeyen anahtar None döner",
        mukavemet_tablolari.ray("yok", "Gr") is None and mukavemet_tablolari.halat_kopma(99) is None,
    )

    _girdi_sozlesmesi(r, kaynak)
    _gelismis_sozlesmesi(r)
    return r


#  SEÇENEK LİSTELERİ.  Arayüzün sunduğu listeler standardın tablolarıyla
#  aynı olmalı:  beyan yükleri EN 81-20 Çizelge 6'nın 28 yükü, ray listesi
#  T75/B dâhil yedi profil, hızlar 0,63 … 6 m/s.
SECENEKLER = {
    "beyan_hizi": [0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6],
    "agirlik_malzemesi": ["Barit", "Pik Döküm"],
    "kabin_ray_profili": [
        "50 x 50 x 5",
        "70 x 65 x 9",
        "75 x 62 x 10",
        "89 x 62 x 15,88",
        "90 x 75 x 16",
        "125 x 82 x 16",
        "127 x 89 x 16",
    ],
    "agirlik_ray_profili": [
        "50 x 50 x 5",
        "70 x 65 x 9",
        "75 x 62 x 10",
        "89 x 62 x 15,88",
        "90 x 75 x 16",
        "125 x 82 x 16",
        "127 x 89 x 16",
    ],
    "beyan_yuku": [
        100,
        180,
        225,
        300,
        320,
        375,
        400,
        450,
        525,
        600,
        630,
        675,
        750,
        800,
        825,
        900,
        975,
        1000,
        1050,
        1125,
        1200,
        1250,
        1275,
        1350,
        1425,
        1500,
        1600,
        2000,
        2500,
    ],
}


#  KAYNAK ÖRNEKTEN BİLEREK AYRILAN VARSAYILANLAR  ( anahtar → ( değer , neden ) ).
BILEREK_DEGISEN_VARSAYILAN = {
    "yan_yatak": (140, "makine kirişi — sahada genelde NPU 140 ( kullanıcı kararı )"),
    #  Kaynak örnek 0,8 taşıyor;  o sayı ofis Excel'inin b = 0,67·v² + 0,13·v
    #  bağıntısının YALNIZ v = 1 m/s değeridir ve sabitlenmişti.  EN 81-50
    #  m.5.11.2.2.2 hesaba girecek en küçük yavaşlamayı 0,5 m/s² der;  referans
    #  program ( referans proje ) da 0,5 kullanır.  Bilinmeyen makinede standardın
    #  tabanı alınır, gerçek değer imalatçıdan girilir.
    "kabin_paten_arasi": (
        2660,
        "kabin paten arası h — patenlerin merkezleri arası;  "
        "patenler şase kirişlerinin dışında ( LiftDesigner ön "
        "kesitleri:  2.660 ) ( kullanıcı kararı 30 Eyl, 8 Eki )",
    ),
    "agirlik_paten_arasi": (
        3400,
        "karşı ağırlık paten arası ( merkezler ) — patenler "
        "çerçevenin dışında, çerçeve 3.300:  800 kg'lık asansörün "
        "1.200 kg'lık barit dolgusu ( 24 blok × 120 ) 2:1 "
        "kasnağının altına sığar ( kullanıcı kararı 30 Eyl, 8 Eki )",
    ),
    #  BİRLEŞİK PROGRAM:  boşsa ÇİZİMDEN ( cizim/kopru.CIZIMDEN ) — hesap ile
    #  çizim aynı sayıyı kullanır;  kutu boş açılır.
    "saptirma_kasnak_capi": (
        None,
        "boşsa çizimden:  çizilen saptırma kasnaklarının ortalaması ( referans proje 240 · 240 · 400 )",
    ),
    "kabin_tampon_baba": (None, "boşsa çizimden:  kuyu dibi − tampon − çarpma arası − kabinin şase altı"),
    "son_kat_yuksekligi": (
        4200,
        "sığınma açıklıkları çizimden:  3.750'de 3.300'lük şasenin "
        "üst pateni kuyu tavanına giriyor ( kullanıcı kararı )",
    ),
    "acil_frenleme_a": (
        mukavemet_girdi.ACIL_FRENLEME_ASGARI,
        "EN 81-50 m.5.11.2.2.2 tabanı — referans proje de 0,5 kullanıyor ( kullanıcı kararı )",
    ),
}


def _girdi_sozlesmesi(r, kaynak):
    """motor/uygulama/mukavemet_girdi.py  —  varsayılanlar ve seçenekler."""
    for anahtar, etiket, _b, tur, secenekler, varsayilan in mukavemet_girdi.ALANLAR:
        if tur == "hesap":
            r.kontrol(
                f"girdi {anahtar}: seçenek/varsayılan taşımıyor", secenekler is None and varsayilan is None
            )
            continue
        r.kontrol(f"girdi {anahtar}: etiket dolu", bool(etiket and etiket.strip()))
        #  Örnek projenin varsayılanları kaynaktaki örnekle aynı:  TEST 9'un
        #  örnek değerleri ve TEST 10'un taraması bu girdilere dayanır.
        if anahtar in kaynak["varsayilanlar"]:
            bek = BILEREK_DEGISEN_VARSAYILAN.get(anahtar, (kaynak["varsayilanlar"][anahtar],))[0]
            r.kontrol(
                f"girdi {anahtar}: varsayılan örnek projeyle aynı",
                _esit(varsayilan, bek),
                f"→ modül {varsayilan!r}, kaynak {bek!r}",
            )
        if secenekler is not None:
            r.kontrol(
                f"girdi {anahtar}: varsayılan seçenek listesinde",
                varsayilan is None or varsayilan in secenekler,
                f"→ {varsayilan!r} ∉ {secenekler!r}",
            )
        if anahtar in SECENEKLER:
            r.esit(
                f"girdi {anahtar}: seçenekler",
                sorted(map(str, secenekler)),
                sorted(map(str, SECENEKLER[anahtar])),
            )

    #  Hesaplanan iki alan kaynaktaki örnekle aynı sonucu veriyor mu
    #  Bağıntı kaynağın örneğiyle:  son kat bilerek değişti ( 3.750 → 4.200 ),
    #  kuyu boyu kaynağın son katıyla denetlenir
    g = mukavemet_girdi.tamamla(
        dict(
            mukavemet_girdi.varsayilanlar(), son_kat_yuksekligi=kaynak["varsayilanlar"]["son_kat_yuksekligi"]
        )
    )
    for anahtar in ("karsi_agirlik", "kuyu_boyu"):
        r.kontrol(
            f"hesaplanan {anahtar} örnek projeyle aynı",
            _esit(g[anahtar], kaynak["hesaplanan"][anahtar]),
            f"→ modül {g[anahtar]!r}, kaynak {kaynak['hesaplanan'][anahtar]!r}",
        )
    #  Çizimden türeyen alanlar varsayılanda bilerek boştur ( cizim/kopru.CIZIMDEN );
    #  hesap onları girdiyle birlikte tamamlar — doğrulama tamamlanmış girdiye.
    _gt = mukavemet_girdi.tamamla(g)
    r.kontrol(
        "varsayılan girdiler doğrulamadan temiz geçiyor",
        mukavemet_girdi.dogrula(_gt) == [],
        f"→ {mukavemet_girdi.dogrula(_gt)}",
    )
    #  Tabliye ray boyuna girmez ( son kat kuyu tavanına ölçülür — 5 Eki;
    #  eskiden örnek projenin tabliyesi 750 ile 26,6 )
    r.esit(
        "toplam ray boyu (m)  ( örnek proje )",
        mukavemet_girdi.toplam_ray_boyu(dict(g, tabliye_yuksekligi=750)),
        26.6 - 0.75,
    )
    r.esit(
        "toplam ray boyu (m)  ( MRL )",
        mukavemet_girdi.toplam_ray_boyu(dict(g, mk_yok=True, tabliye_yuksekligi=750)),
        26.6 - 0.75,
    )


#  GÖRÜNÜR KALMASI GEREKEN GİRDİLER.  Her projede değişenler ( bina ve
#  asansörün kendi ölçüleri ) ve yanlış kaldığında sonucu çok değiştiren
#  beyanlar.  Gelişmiş'e taşınırlarsa bir projenin değeri öbür projeden
#  sessizce devralınırdı.
GORUNUR_KALMALI = (
    "beyan_yuku",
    "beyan_hizi",
    "seyir_mesafesi",
    "aski_orani",
    "kabin_genisligi",
    "kabin_derinligi",
    "kat_kapisi_tipi",
    "kapi_genisligi",
    #  Makine daireli projede sorulur ( MRL'de gizli ).
    "tabliye_yuksekligi",
    #  Kaçıklıklar çizime bağlıdır;  gizli bir 0 kaçık yerleşimde unutulur.
    "kabin_kaciklik",
    "aski_kaciklik_x",
    "aski_kaciklik_y",
    "son_kat_yuksekligi",
    "kuyu_dibi",
    "ray_kapi_arasi",
    "motor_gucu",
    "makine_agirligi",
    "makine_tipi",
    "tahrik_kasnak_capi",
    "saptirma_kasnak_capi",
    "makine_tst",
    "makine_raya_biniyor",
    "halat_adedi",
    "halat_capi",
    "sarilma_acisi",
    "kabin_ray_profili",
    "agirlik_ray_profili",
    "kabin_konsol_arasi",
    "agirlik_konsol_arasi",
    "guvenlik_tertibati",
    "agirlik_guvenlik_tertibati",
    "kabin_tampon_baba",
    "agirlik_tampon_baba",
)
#  BÜTÜN ALANLARI GELİŞMİŞ'TE OLAN GRUPLAR  ( kullanıcı kararı ).  Hız
#  regülatörünün hepsi ürün / imalatçı verisidir;  devreye sokma kuvveti ve
#  devreye girme hızı boşsa paftaya standardın şartı yazılır.
TAMAMI_GELISMIS_GRUPLAR = ("Hız regülatörü",)
#  Hiçbir hesaba / paftaya girmediği ya da tek seçeneği olduğu için kaldırılanlar.
#  reg_surtunme ( µ ) KALKMADI, OFİS SABİTİNE TAŞINDI ( sabitler.reg_mu ):
#  standart hesaba katılacak değeri kendisi verir ve asansör bazında
#  küçültülünce halatın emniyet katsayısı olduğundan iyi çıkıyordu.
KALDIRILAN_ALANLAR = (
    "kuyu_derinligi",
    "agirlik_ray_duvar",
    "dikine_kiris_tipi",
    "yan_yatak_tipi",
    "agirlik_ray_arasi",
    "reg_surtunme",
)


def _gelismis_sozlesmesi(r):
    """Formun "Gelişmiş" bölümleri  ( MG.GELISMIS_ALANLAR · girdi.EK_GELISMIS ·
    çizim alanlarının gelişmiş işareti — form üçünü tasarım şemasından birlikte kurar )."""
    from motor.uygulama import uygulama_girdisi
    from cizim import kopru

    _ck_gelismis = frozenset(a[0] for a in kopru.ALANLAR if a[6])
    for a in sorted(mukavemet_girdi.GELISMIS_ALANLAR):
        r.kontrol(
            f"gelişmiş {a}: sözleşmede var ve kullanıcıdan alınıyor",
            a in mukavemet_girdi.ALAN and mukavemet_girdi.ALAN[a][3] != "hesap",
        )
        #  Gizli bir alan boş ve zorunluysa proje görünmeyen bir kutu yüzünden
        #  durur:  ya varsayılanı olmalı ya da boş bırakılabilmeli.
        if a in mukavemet_girdi.ALAN:
            r.kontrol(
                f"gelişmiş {a}: varsayılanı var ya da boş bırakılabilir",
                mukavemet_girdi.ALAN[a][5] is not None or a in mukavemet_girdi.OPSIYONEL_ALANLAR,
            )
    for a in GORUNUR_KALMALI:
        r.kontrol(
            f"görünür kalır: {a}", a in mukavemet_girdi.ALAN and a not in mukavemet_girdi.GELISMIS_ALANLAR
        )
    for a in KALDIRILAN_ALANLAR:
        r.kontrol(f"kaldırıldı: {a}", a not in mukavemet_girdi.ALAN)
    for anahtar, _e, _b, _tur, secenekler, _v in mukavemet_girdi.ALANLAR:
        if secenekler is not None:
            r.kontrol(
                f"girdi {anahtar}: tek seçenekli kutu sorulmuyor", len(secenekler) > 1, f"→ {secenekler!r}"
            )
    veri = uygulama_girdisi.arayuz_alanlari()
    for gr in veri["gruplar"]:
        if gr["ad"] in TAMAMI_GELISMIS_GRUPLAR:
            r.kontrol(
                f"grup '{gr['ad']}': bütün alanlar gelişmiş",
                bool(gr["alanlar"]) and all(f["gelismis"] for f in gr["alanlar"]),
            )
            continue
        r.kontrol(f"grup '{gr['ad']}': en az bir görünür alan", any(not f["gelismis"] for f in gr["alanlar"]))
        for f in gr["alanlar"]:
            bek = f["anahtar"] in (
                mukavemet_girdi.GELISMIS_ALANLAR | uygulama_girdisi.EK_GELISMIS | _ck_gelismis
            )
            if f["gelismis"] != bek:
                r.kontrol(
                    f"arayüz {f['anahtar']}: gelişmiş işareti",
                    False,
                    f"→ {f['gelismis']!r}, beklenen {bek!r}",
                )
    _hepsi = [f for gr in veri["gruplar"] for f in gr["alanlar"]]
    r.esit(
        "arayüz: gelişmiş alan sayısı",
        sum(f["gelismis"] for f in _hepsi),
        len(mukavemet_girdi.GELISMIS_ALANLAR) + len(uygulama_girdisi.EK_GELISMIS) + len(_ck_gelismis),
    )

    #  ── ALAN AÇIKLAMALARI  ( formdaki ⓘ )  ────────────────────────────
    #  SÖZLEŞMENİN PARÇASIDIR.  Açıklamasız bir girdi, kullanıcının ne
    #  yazacağını bilemediği bir kutudur;  yeni alan eklenirken metni
    #  yazmak unutulmasın diye burada zorunlu tutulur.  Özellikle üç
    #  kaçıklık birbirine karıştırılmaya çok açıktır.
    for f in _hepsi:
        r.kontrol(f"açıklama {f['anahtar']}: var ve boş değil", bool(str(f.get("bilgi") or "").strip()))
        _b = str(f.get("bilgi") or "")
        r.kontrol(
            f"açıklama {f['anahtar']}: kısa  ( ≤ 320 karakter )", len(_b) <= 320, f"→ {len(_b)} karakter"
        )
    #  ÜÇ KAÇIKLIK AYIRT EDİLİR.  Metinleri birbirinin kopyası olmamalı ve
    #  her biri ÖLÇÜM ORİJİNİNİ ( ray ekseni ) söylemeli — asıl karışma
    #  sebebi "neye göre kaçık" sorusunun cevapsız kalmasıydı.
    _kacik = (
        "kabin_kaciklik",
        "aski_kaciklik_x",
        "aski_kaciklik_y",
        "kabin_agirlik_merkezi_x",
        "kabin_agirlik_merkezi_y",
    )
    _metin = {a: mukavemet_girdi.ACIKLAMA[a] for a in _kacik}
    r.kontrol("kaçıklık açıklamaları birbirinden farklı", len(set(_metin.values())) == len(_kacik))
    for a, m in _metin.items():
        r.kontrol(
            f"kaçıklık {a}: ölçüm orijinini söylüyor",
            "ray ekseni" in m or "ray ekseninden" in m,
            f"→ {m[:60]}",
        )


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
