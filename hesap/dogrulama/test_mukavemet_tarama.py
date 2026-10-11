# -*- coding: utf-8 -*-
"""
TEST 10  —  MUKAVEMET REFERANS TARAMASI        ( uygulama projesi )

TEST 9 motorun kurallarını tek tek sınar.  Bu test GİRDİ UZAYINI tarar:
ray profili, halat çapı, kanal şekli / işlemesi, güvenlik tertibatı, askı
oranı, karşı ağırlık yeri, durak sayısı, hız, yük, kaçıklıklar, ofis
sabitleri …  Her senaryoda motorun bütün ara değerleri ( sonuc["ara"] ) ve
bölüm hükümleri DONDURULMUŞ referansla karşılaştırılır.

Referansın dayanağı:  bu senaryolar mukavemet çalışma kitabında LibreOffice
ile yeniden hesaplanmış ve her değer motorla aynı çıkmıştı ( standardın
gerektirdiği bilinçli sapmalar hariç;  onlar da teslim edilen düzeltilmiş
kitapla hücre hücre aynıydı ).  Program artık Excel kullanmaz;  o doğrulanmış
sonuçlar dogrulama/referans_mukavemet.json.gz'dedir.

    python3 dogrulama/tarama_uret.py        →  referansı YENİDEN ÜRETİR

Yeniden üretmek DAVRANIŞI DEĞİŞTİRME İZNİDİR ( bkz. altin_uret ).
"""

import json
import os
import sys

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import yollar

yollar.kur()

from motor.uygulama import mukavemet
from motor.uygulama import mukavemet_girdi
from motor.uygulama import mukavemet_tablolari
from dogrulama.rapor import Rapor
from dogrulama.test_avan_tarama import karsilastir

DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referans_mukavemet.json.gz")


# =====================================================================
#  SENARYOLAR
# =====================================================================
def tarama_senaryolari():
    """Varsayılan projeden TEK girdiyi değiştiren senaryolar  ( ad , girdi )."""
    v = mukavemet_girdi.varsayilanlar()
    s = []

    def E(ad, **kw):
        g = dict(v)
        g.update(kw)
        s.append((ad, g))

    def durak(n, h=3000, son=3750):
        #  n durak, katlar arası h:  seyir ( n − 1 ) · h.  Adlar referans
        #  dosyasının anahtarıdır — "12 durak" olarak kalırlar.
        return {"son_kat_yuksekligi": son, "seyir_mesafesi": (n - 1) * h / 1000.0}

    E("varsayılan")
    #  Sarılma açısı zorunlu girdidir ve varsayılanı yoktur:  öteki
    #  senaryolarda tahrik sınırları hesaplanmaz ( HESAP EKSİK ).
    E("sarılma açısı 180°", sarilma_acisi=180)
    E("sarılma açısı 150°", sarilma_acisi=150)
    #  Denge zinciri P'ye giren MCR yolunu açar  ( m.5.2.1.8.5 · m.5.7.2.3.2 ).
    E("denge zinciri var", denge_zinciri="Var")
    #  Makine raylara biniyor  ( MRL — m.5.7.2.3.7 ).
    E("makine raylara biniyor", mk_yok=True, makine_raya_biniyor=mukavemet_tablolari.MAKINE_YUK_YOLU_RAY)
    E(
        "zincir + ağırlık güvenlik tertibatı",
        denge_zinciri="Var",
        agirlik_guvenlik_tertibati=mukavemet_tablolari.DARBE_TIPLERI_ADLARI[0],
    )
    E("regülatör katalog halatı", reg_halat_kopma_kN=28, reg_halat_birim_kutle=0.30)

    for p in mukavemet_tablolari.RAY_PROFILLERI:
        E(f"kabin rayı {p}", kabin_ray_profili=p)
        E(f"ağırlık rayı {p}", agirlik_ray_profili=p)
    for c in mukavemet_tablolari.HALAT_CAPLARI:
        E(f"halat Ø{c}", halat_capi=c)
    for c in (6, 6.5, 8):
        E(f"regülatör halatı Ø{c}", reg_halat_capi=c)
    for k in mukavemet_tablolari.KANAL_SEKILLERI:
        #  Düz V kanal sertleştirilmemiş olamaz ( m.5.11.2.3.1.2 ).
        if mukavemet_tablolari.kanal_turu(k) == "V":
            E(f"kanal {k}", kanal_sekli=k, kanal_isleme="Sertleştirilmiş")
        else:
            E(f"kanal {k}", kanal_sekli=k)
    for k in mukavemet_tablolari.KANAL_ISLEME_SEKILLERI:
        E(f"kanal işleme {k}", kanal_isleme=k)
    for t in mukavemet_tablolari.DARBE_TIPLERI_ADLARI:
        E(f"güv. tertibatı {t}", guvenlik_tertibati=t)
    _derinlik = {r[0]: r[1] for r in mukavemet_tablolari.AGIRLIK_MALZEMESI}
    for m in mukavemet_tablolari.AGIRLIK_MALZEMELERI:
        E(f"ağırlık malzemesi {m}", agirlik_malzemesi=m, agirlik_derinligi=_derinlik[m])
    for rm in mukavemet_tablolari.RAY_CELIKLERI:
        E(f"ray çeliği Rm {rm}", ray_celigi_rm=rm)
    E("askı 1:1", aski_orani=1)
    #  Kapı ağırlığın tersine açılır:  sola açılan kabin kapısının cebi soldaki
    #  ağırlığın ara kirişine çarpar ( çizim reddeder;  kabin üstü planı 5 Eki )
    E("ağırlık solda", agirlik_yeri="Sol", kat_kapisi_tipi="Teleskopik Sağ")
    E("ağırlık arkada", agirlik_yeri="Arka")
    for h in (0.63, 1.6, 2.5, 4):
        E(f"hız {h} m/s", beyan_hizi=h)
    E("630 kg küçük kabin", beyan_yuku=630, kabin_genisligi=1100, kabin_derinligi=1400, kabin_agirligi=600)
    E(
        "1600 kg büyük kabin",
        beyan_yuku=1600,
        kabin_genisligi=1900,
        kabin_derinligi=2000,
        kabin_agirligi=1200,
        kabin_ray_profili="125 x 82 x 16",
    )
    E(
        "2000 kg",
        beyan_yuku=2000,
        kabin_genisligi=2000,
        kabin_derinligi=2200,
        kabin_agirligi=1400,
        kabin_ray_profili="127 x 89 x 16",
    )
    E("320 kg", beyan_yuku=320, kabin_genisligi=900, kabin_derinligi=1000, kabin_agirligi=450)
    for n in (2, 5, 12, 20):
        E(f"{n} durak", **durak(n))
    E("yüksek son kat", **durak(8, son=5000))
    for npu in (80, 160, 200):
        E(f"NPU {npu}", dikine_kiris=npu, yan_yatak=npu)
    #  0,5 m/s² m.5.11.2.2.2'nin alt sınırıdır;  altı reddedilir.
    for a in (0.5, 1.5, 5.0):
        E(f"a = {a} m/s²", acil_frenleme_a=a)
    for k in mukavemet_tablolari.KABLO_TIPLERI:
        E(f"kablo {k}", kablo_tipi_2=k)
    E("uzun pervaz 150", uzun_pervaz=150)
    E("ray-kapı arası 500", ray_kapi_arasi=500)
    #  Ray ekseni kabin merkezini geçiyor  →  xc ≤ 0, kuvvetler negatife düşer.
    E("ray-kapı arası 830  ( xc = 0 )", ray_kapi_arasi=830)
    E("ray-kapı arası 1200 ( xc < 0 )", ray_kapi_arasi=1200)
    E("kabin kaçıklığı 60", kabin_kaciklik=60)
    E("ağır kabin kapısı", _ofis={"kabin_kapisi_agirligi": 180}, kapi_mekanizma_payi=90)
    E("dar konsol aralığı", kabin_konsol_arasi=2000, agirlik_konsol_arasi=2000)
    E(
        "küçük kabin  ( Çizelge 8 )",
        beyan_yuku=1000,
        kabin_agirligi=900,
        kabin_genisligi=1300,
        kabin_derinligi=1500,
    )
    E("yük-insan asansörü", asansor_tipi="Yük-insan asansörü")
    E("geniş paten arası", kabin_paten_arasi=4200, agirlik_paten_arasi=4200)
    return s


#  Açısı girilmiş projede TEK şeyi değiştiren senaryolar;  sonda hepsi bir
#  arada ve referans örnek proje.
_B = {"sarilma_acisi": 180}
PROJE_SENARYOLARI = (
    ("kabin kaçıklığı +200", dict(_B, kabin_kaciklik=200)),
    ("kabin kaçıklığı −150", dict(_B, kabin_kaciklik=-150)),
    ("askı noktası xs", dict(_B, aski_kaciklik_x=250)),
    ("askı noktası ys", dict(_B, aski_kaciklik_y=50)),
    ("askı ve kabin ters işaretli", dict(_B, aski_kaciklik_x=-300, aski_kaciklik_y=-80, kabin_kaciklik=120)),
    ("makaralı paten", dict(_B, paten_tipi="Makaralı", agirlik_paten_tipi="Makaralı")),
    (
        "makaralı paten + ℓ",
        dict(_B, paten_tipi="Makaralı", agirlik_paten_tipi="Makaralı", paten_balata_boyu=120),
    ),
    #  Paten tipi ray başınadır;  girilen ℓ yalnız kabin pateninindir.
    ("kabin kaymalı · ağırlık makaralı", dict(_B, agirlik_paten_tipi="Makaralı")),
    ("kabin makaralı · ağırlık kaymalı", dict(_B, paten_tipi="Makaralı")),
    ("kabin ℓ girilmiş · ağırlıkta ℓ türetilir", dict(_B, paten_balata_boyu=140)),
    ("Fp ve bina sehimi", dict(_B, klips_itme_kuvveti=500, yapi_sehim_x=1, yapi_sehim_y=1.5)),
    ("sehim · ağırlık arkada", dict(_B, yapi_sehim_x=0.7, yapi_sehim_y=1.3, agirlik_yeri="Arka")),
    (
        "sehim · ağırlık solda",
        dict(_B, yapi_sehim_x=0.7, yapi_sehim_y=1.3, agirlik_yeri="Sol", kat_kapisi_tipi="Teleskopik Sağ"),
    ),
    ("Fp tek başına", dict(_B, klips_itme_kuvveti=750)),
    (
        "makine daireli + eski 'raylara' seçimi",
        dict(_B, makine_raya_biniyor=mukavemet_tablolari.MAKINE_YUK_YOLU_RAY),
    ),
    (
        "MRL makine raylarda",
        dict(_B, mk_yok=True, makine_raya_biniyor=mukavemet_tablolari.MAKINE_YUK_YOLU_RAY),
    ),
    ("zincir + ağırlıkta tertibat", dict(_B, denge_zinciri="Var", agirlik_guvenlik_tertibati="Kaymalı")),
    (
        "zincir + ağırlıkta ani tertibat + Fp",
        dict(
            _B,
            denge_zinciri="Var",
            agirlik_guvenlik_tertibati="Ani Frenlemeli",
            beyan_hizi=0.63,
            klips_itme_kuvveti=400,
        ),
    ),
    ("ofis k3", dict(_B, _ofis={"k3_yardimci": 1.2})),
    ("ofis k1 kaymalı", dict(_B, _ofis={"k1_kaymali": 3})),
    (
        "ofis k1 makaralı",
        dict(_B, guvenlik_tertibati="Ani Frenlemeli Makaralı", beyan_hizi=0.63, _ofis={"k1_makarali": 4}),
    ),
    ("ofis k1 ani", dict(_B, guvenlik_tertibati="Ani Frenlemeli", beyan_hizi=0.63, _ofis={"k1_ani": 6})),
    ("ofis sürtünme yükü Gs", dict(_B, _ofis={"Gs": 30})),
    ("ofis halat payı", dict(_B, _ofis={"halat_pay_m": 3})),
    ("ofis halat payı · 1:1", dict(_B, aski_orani=1, sarilma_acisi=160, _ofis={"halat_pay_m": 7.5})),
    ("ofis kaide mesnet payı", dict(_B, _ofis={"yan_yatak_L_X": 300})),
    ("ofis σem", dict(_B, _ofis={"sigma_em": 100})),
    (
        "ofis sığınma payları",
        dict(
            _B,
            _ofis={
                "kabin_yuksekligi": 2600,
                "kabin_ust_donanim": 2300,
                "paten_payi": 350,
                "tavan_payi": 200,
                "revizyon_payi": 600,
                "etek_payi": 500,
                "etek_kotu": 1000,
                "ray_alt_payi": 300,
                "regulator_payi": 350,
            },
        ),
    ),
    #  m.5.4.2.3.1 yolcu = MIN( Q/75 ; Çizelge 8 ) · m.5.7.4.5 σperm = Rm/St ·
    #  m.5.7.2.3.6 eşik kuvveti asansör tipinden.
    (
        "küçük kabin · Çizelge 8 kişiyi düşürür",
        dict(_B, beyan_yuku=1000, kabin_agirligi=900, kabin_genisligi=1300, kabin_derinligi=1500),
    ),
    (
        "21+ kişi · Çizelge 8'in ötesi",
        dict(
            _B,
            beyan_yuku=2000,
            kabin_agirligi=1400,
            kabin_genisligi=1700,
            kabin_derinligi=2300,
            kabin_ray_profili="125 x 82 x 16",
        ),
    ),
    ("1250 kg", dict(_B, beyan_yuku=1250, kabin_agirligi=1000, kabin_genisligi=1600, kabin_derinligi=1800)),
    ("yük-insan asansörü", dict(_B, asansor_tipi="Yük-insan asansörü")),
    ("ray çeliği Rm 440", dict(_B, ray_celigi_rm=440)),
    ("ray çeliği Rm 520", dict(_B, ray_celigi_rm=520)),
    (
        "hepsi bir arada",
        dict(
            _B,
            kabin_kaciklik=-90,
            aski_kaciklik_x=180,
            aski_kaciklik_y=-40,
            paten_tipi="Makaralı",
            agirlik_paten_tipi="Makaralı",
            klips_itme_kuvveti=250,
            yapi_sehim_x=0.5,
            yapi_sehim_y=0.8,
            agirlik_yeri="Sol",
            denge_zinciri="Var",
            kablo_birim_kutle=0.6,
            mk_yok=True,
            makine_raya_biniyor=mukavemet_tablolari.MAKINE_YUK_YOLU_RAY,
            _ofis={
                "k3_yardimci": 1.6,
                "k1_kaymali": 2.5,
                "Gs": 15,
                "halat_pay_m": 4,
                "yan_yatak_L_X": 320,
                "sigma_em": 120,
                "q_denge": 0.45,
                "tavan_payi": 180,
            },
        ),
    ),
    #  Referans örnek proje, arayüzden girildiği gibi  ( bkz. TEST 12 ).
    (
        "referans proje",
        dict(
            beyan_yuku=800,
            kabin_agirligi=900,
            beyan_hizi=1.6,
            aski_orani=2,
            son_kat_yuksekligi=5000,
            seyir_mesafesi=29.0,
            kaide_yuksekligi=500,
            kuyu_dibi=1500,
            kabin_genisligi=1350,
            kabin_derinligi=1400,
            ray_kapi_arasi=970,
            aski_kaciklik_x=250,
            aski_kaciklik_y=50,
            motor_gucu=11.3,
            makine_tst=3400,
            tahrik_kasnak_capi=240,
            saptirma_kasnak_capi=294,
            saptirma_kasnak_min_capi=240,
            halat_capi=6.5,
            halat_adedi=7,
            halat_birim_kutle=0.179,
            halat_kopma_kN=31.5,
            kasnak_belgesi="Var",
            kanal_sekli="V Kanal",
            kanal_isleme="Sertleştirilmiş",
            sarilma_acisi=180,
            kasnak_tek_yon=2,
            kasnak_ters_yon=0,
            acil_frenleme_a=0.5,
            denge_zinciri="Var",
            kablo_birim_kutle=0.44,
            mk_yok=True,
            makine_raya_biniyor=mukavemet_tablolari.MAKINE_YUK_YOLU_RAY,
            kabin_ray_profili="75 x 62 x 10",
            agirlik_ray_profili="70 x 65 x 9",
            kabin_konsol_arasi=2000,
            agirlik_konsol_arasi=1200,
            ray_celigi_rm=440,
            kabin_paten_arasi=3300,
            agirlik_paten_arasi=1500,
            paten_balata_boyu=140,
            agirlik_paten_tipi="Makaralı",
            agirlik_genisligi=850,
            agirlik_derinligi=160,
            tampon_tipi="Hidrolik  ( enerji yutmalı )",
            _ofis={"k3_yardimci": 2},
        ),
    ),
)


def tahrik_senaryolari():
    """Kanal şekli × işleme × ofis açıları, D/d belgesi ve tahrik yük yolları."""
    s = []
    for ofis in (None, {"kanal_gama_v": 45, "kanal_gama_yd": 30, "kanal_beta": 100}):
        for k in mukavemet_tablolari.KANAL_SEKILLERI:
            for i in mukavemet_tablolari.KANAL_ISLEME_SEKILLERI:
                if mukavemet_tablolari.kanal_turu(k) == "V" and i == "Sertleştirilmemiş":
                    continue  # standart dışı — reddedilir
                #  Açı kanalın sarım sayısına uymalı ( tek ≤ 180°, çift > 180° ).
                aci = 330 if (mukavemet_tablolari.kanal_gecis_sayisi(k) or 1) > 1 else 180
                g = {"kanal_sekli": k, "kanal_isleme": i, "sarilma_acisi": aci}
                if ofis:
                    g["_ofis"] = dict(ofis)
                s.append((f"kanal {k} · {i}" + (" · ofis açıları" if ofis else ""), g))
    kucuk = {"tahrik_kasnak_capi": 240, "halat_capi": 6.5, "saptirma_kasnak_capi": 240, "kasnak_tek_yon": 2}
    s += [
        ("D/d 240/6,5 belgesiz", dict(kucuk, kasnak_belgesi="Yok")),
        ("D/d 240/6,5 belgeli", dict(kucuk, kasnak_belgesi="Var")),
        ("D/d 40 belgeli", {"tahrik_kasnak_capi": 320, "halat_capi": 8, "kasnak_belgesi": "Var"}),
        (
            "tahrik 1:1 V kanal",
            {
                "aski_orani": 1,
                "sarilma_acisi": 150,
                "kanal_sekli": "V Kanal",
                "kanal_isleme": "Sertleştirilmiş",
            },
        ),
        ("tahrik denge zinciri", {"aski_orani": 2, "sarilma_acisi": 180, "denge_zinciri": "Var"}),
        (
            "tahrik katalog halatı",
            {
                "aski_orani": 2,
                "sarilma_acisi": 180,
                "denge_zinciri": "Var",
                "halat_birim_kutle": 0.21,
                "_ofis": {"denge_zinciri_orani": 70, "q_denge": 0.45},
            },
        ),
        ("tahrik kablo kütlesi", {"aski_orani": 2, "sarilma_acisi": 180, "kablo_birim_kutle": 0.44}),
        (
            "tahrik kablo tipi",
            {
                "aski_orani": 1,
                "sarilma_acisi": 170,
                "kablo_tipi_1": "12 x 1,00",
                "kat_kapisi_tipi": "Manuel Sağ",
            },
        ),
        (
            "kuyu sürtünmesi 0",
            {
                "aski_orani": 2,
                "sarilma_acisi": 180,
                "_ofis": {"kuyu_surtunme_kabin": 0, "kuyu_surtunme_agirlik": 0},
            },
        ),
        (
            "kuyu sürtünmesi 3 / 2,5",
            {
                "aski_orani": 2,
                "sarilma_acisi": 170,
                "_ofis": {"kuyu_surtunme_kabin": 3, "kuyu_surtunme_agirlik": 2.5},
            },
        ),
    ]
    return s


#  Motorun REDDETMESİ gereken girdiler  ( hüküm verilmez )
GECERSIZ_SENARYOLARI = (
    ("tek sarım 300°", {"sarilma_acisi": 300, "kanal_isleme": "Sertleştirilmiş"}),
    ("çift sarım 180°", {"kanal_sekli": "Yarım Daire Kanal (Çift Sarım)", "sarilma_acisi": 180}),
    (
        "sertleştirilmemiş V kanal",
        {"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş", "sarilma_acisi": 180},
    ),
)


def _kopya(g):
    return json.loads(json.dumps(g))


def mukavemet_sonucu(g):
    s = mukavemet.hesapla(_kopya(g))
    if not s.get("aktif"):
        return {"aktif": False, "hata": s.get("hata")}
    return {
        "aktif": True,
        "ara": s["ara"],
        "hukumler": [[b["kimlik"], (b.get("sonuc") or {}).get("uygun")] for b in s["bolumler"]],
    }


AILELER = (
    ("tarama", tarama_senaryolari),
    ("proje", lambda: list(PROJE_SENARYOLARI)),
    ("tahrik", tahrik_senaryolari),
    ("gecersiz", lambda: list(GECERSIZ_SENARYOLARI)),
)


def uret():
    """Referans kaydı  —  { aile : [ { ad, girdi, sonuc } ] }."""
    return {
        aile: [{"ad": ad, "girdi": _kopya(g), "sonuc": _kopya(mukavemet_sonucu(g))} for ad, g in senaryo()]
        for aile, senaryo in AILELER
    }


def calistir():
    print(
        "\n\033[1mTEST 10 — MUKAVEMET REFERANS TARAMASI\033[0m"
        "   (ara değerler ve hükümler dondurulmuş referansa karşı)"
    )
    r = Rapor("Mukavemet referans taraması")
    if not os.path.isfile(DOSYA):
        r.kontrol(
            "referans dosyası var",
            False,
            f"→ {os.path.basename(DOSYA)} yok — python3 dogrulama/tarama_uret.py",
        )
        return r
    simdi = uret()
    karsilastir(r, DOSYA, simdi, "mukavemet")
    #  Geçersiz girdiler gerçekten reddediliyor, geçerliler hesaplanıyor
    for aile, liste in simdi.items():
        for k in liste:
            r.esit(
                f"[mukavemet · {aile}] {k['ad']} · "
                + ("reddediliyor" if aile == "gecersiz" else "hesaplanıyor"),
                k["sonuc"]["aktif"],
                aile != "gecersiz",
            )
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
