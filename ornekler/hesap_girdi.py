# -*- coding: utf-8 -*-
"""Örnek projelerin girdisi ( yayımlanmış bir referans proje ) — programın
formunun girdisiyle AYNI:  hesabın alanları + çizim alanları ( cizim/kopru.ALANLAR ).
Kaynak:  ~/asansör projeleri/sample-project.pdf ( referans proje, 3 Eylül 2025 ) ve hesap
programının TEST 12'si.  Tampon referans projede belirsiz:  OLEO LB 16 ( oleoelevator.com ).

İKİ DEĞER referans projenin HESABINDAN değil ÇİZİMİNDEN alındı — birleşik programda
hesap ile çizim aynı sayıyı kullanır, referans projenin ikisi ise çelişiyordu:
  agirlik_genisligi   790   karşı ağırlık çerçevesi ( çizimden ölçüldü );  referans
                            hesabı 850 alır — o raylar arasıdır ( DBGW ).
  aski_kaciklik_x     boş   çizimden:  halatlar ağırlık kasnağının kabine yakın
                            teğetinden iner, askı ray ekseninin 250 önünde ( −250 );
                            referans hesabı 0 alır ( askı ray ekseninde )."""
from cizim import sabitler as _CS   # noqa: E402

ASANSOR = {
    "asansor_adi": "ASANSÖR 1",
    "asansor_tipi": "İnsan asansörü",
    "beyan_yuku": 800, "kabin_agirligi": 900, "beyan_hizi": 1.6,
    "aski_orani": 2, "seyir_mesafesi": 29.0, "son_kat_yuksekligi": 5000, "kuyu_dibi": 1500,
    "kabin_genisligi": 1350, "kabin_derinligi": 1400,
    "kat_kapisi_tipi": "Teleskopik Sol", "kapi_genisligi": 900,
    "ray_kapi_arasi": 1017,
    "tahrik_kasnak_capi": 240,
    "halat_capi": 6.5, "halat_adedi": 7, "halat_birim_kutle": 0.179, "halat_kopma_kN": 31.5,
    "sarilma_acisi": 180, "kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmiş",
    #  Nps · Npr formda yok:  çizilen kasnaklardan ( 2:1 → 2 · 0, referans projeyle aynı )
    "acil_frenleme_a": 0.5,
    "denge_zinciri": "Var", "kasnak_belgesi": "Var",
    "motor_gucu": 11.3, "makine_tst": 3400, "makine_verimi": 0.8415, "makine_tipi": "Dişlisiz",
    #  MRL:  makine şasesi raylara oturur ( referans proje "Motor Bedplate Calculation":
    #  şase kabin ve ağırlık raylarına dayanır;  motor 250 kg ).  Hesap programı
    #  bir raya ( Gm + Tst ) / 4 yükler ( m.5.7.2.3.7 );  referans proje kendi paftasında
    #  raya 800 kg ( ray hesabında 1.000 kg ) KABUL eder.
    "makine_raya_biniyor": "Kılavuz raylara", "makine_agirligi": 250,
    #  Makinenin oturduğu kirişler ( bölüm 2 ):  referans proje "Motor Bedplate
    #  Calculation" — Wa 191.000 mm³ ( UPN 200 ), L 850 ( karşı ağırlık rayları
    #  arası;  kirişler o raylara oturur ).  L girdi değildir:  çizimden ( DBGW ).
    "yan_yatak": 200,
    "kablo_birim_kutle": 0.44,
    "kabin_ray_profili": "89 x 62 x 15,88", "agirlik_ray_profili": "70 x 65 x 9",
    "kabin_konsol_arasi": 1500, "agirlik_konsol_arasi": 1500, "ray_celigi_rm": 450,
    #  Ağırlık paten arası:  referans proje hesabında 1.500, çiziminde 140'lık patenler
    #  2.920'lik çerçevenin üstünde ve altında — merkezleri arası 3.060.  Çizim
    #  çerçeveyi bundan kurar ( paten arası − paten );  hesap ile pafta aynı şeyi
    #  söylesin diye referans projenin çizimindeki 3.060 ( 8 Eki'ye dek 2.920 ).
    "kabin_paten_arasi": 3300, "agirlik_paten_arasi": 3060,
    "paten_tipi": "Kaymalı", "agirlik_paten_tipi": "Makaralı", "guvenlik_tertibati": "Kaymalı",
    "agirlik_yeri": "Sol", "agirlik_genisligi": 790, "agirlik_derinligi": 160,
    #  Regülatör:  referans proje "Speed Governor Calculation" — kasnak ø240, halat ø6,0
    "reg_kasnak_capi": 240, "reg_halat_capi": 6,
    "tampon_tipi": "Hidrolik  ( enerji yutmalı )",
    "kabin_tampon_adedi": 1, "agirlik_tampon_adedi": 1,
    "kabin_tampon_boyu": 618, "kabin_tampon_ezilme": 203,
    "kabin_carpma_arasi": 96,
    "agirlik_tampon_baba": 300, "agirlik_tampon_ezilme": 203, "agirlik_carpma_arasi": 150,
    "siginma_tipi_ust": "Çömelme", "siginma_tipi_dip": "Çömelme",
    "kuyu_genisligi": 2100,
    #  Boş:  çizimden ( cizim/kopru.CIZIMDEN ).  Formda sorulmayanlar ( tasarım
    #  şeması ) burada da yok:  saptırma kasnaklarının çapı çizilen kasnaklardan
    #  ( 240 · 240 · 400 → D2 293,3 — referans projenin hesabı yuvarlayıp 294
    #  alır ), kabin tamponu kaidesi kuyu dibi zincirinden ( 306 ), kabin iki
    #  rayın ortasında ( yc 0 ).
    "aski_kaciklik_x": None,
    #  ── ÇİZİM ALANLARI ( referans projenin kuyu planı ve kesitlerinden ) ─────
    #  Kuyu 2.100 × 1.850;  kabin kuyu ortasının 130 sağında ( ağırlık solda );
    #  11 durak, seyir 29 m → kat 2.900;  kapı 2.100, kabin içi 2.250;  ağırlık
    #  ekseni ray ekseninin 50 önünde, kasnağı ø400;  kabin kasnakları ø240,
    #  1.380 arayla;  ağırlık tamponu da OLEO LB 16 ( 618 );  regülatör ray
    #  ekseninin 280 arkasında.  Öbür çizim alanları formun varsayılanıyla aynı:
    #  duvar 150, kapı kuyu içine, eşik arası 30, DBG 1.350 + 200, DBGW 790 + 60,
    #  ağırlık ekseni – duvar 160 / 2 + 50.
    "kuyu_derinligi": 1850, "durak_adedi": 11, "kabin_yana_kaciklik": 130,
    "kapi_yuksekligi": 2100, "kabin_ic_yuksekligi": 2250,
    "agirlik_eksen_kaciklik": -50, "agirlik_kasnak_capi": 400,
    "kabin_kasnak_capi": 240, "kabin_kasnak_arasi": 1380,
    "agirlik_tampon_boyu": 618, "regulator_kaciklik": 280,
}
#  Ofis standardı ( Sabitler sekmesi ):  referans projenin kabulleri ve KABİNİ.
#  Programın ofis standardı ofisin kendi ( LiftDesigner ) kabinidir ( 5. adım,
#  cizim/sabitler.py );  referans projenin kabini onun "Cabin at Bottom / Top
#  Floor" kesitlerinden ölçülmüştü ( 1/30 ):  şase alt kirişinin altı −480,
#  paten onun ortasında, taban 120, fren bloğu platformun altında 350, kabin
#  kasnağı merkezi −295 ( genişliği 92 ), yan pano 45, arka 33.
SABITLER = {"q_denge": 0.50, "kanal_gama_v": 38, **_CS.REFERANS_PROJE_KABINI}
ORTAK = {"mk_yok": True}

#  ── MAKİNE DAİRELİ, DİŞLİ MAKİNELİ ÇEŞİT ─────────────────────────────────
#  referans projede böyle bir proje yok:  AYNI asansör ( kuyu, kabin, raylar, halatlar,
#  tamponlar referans projenin ), makine kuyunun üstündeki odada, dişli.
#  Yalnız makineye ve odaya ait girdiler değişir;  kaynakları:
#    makine_tipi        Dişli — çizim LiftDesigner 12744-3'ün A 160'ını çizer
#    makine_verimi      boş:  ofisin dişli makine verimi ( hesap programı sabiti 0,50 )
#    makine_agirligi    350 kg — ofisin 12744-3 hesabı ( A 160 ), "Gm:mak-motor ağırlığı"
#    motor_gucu         15 kW — dişli verimiyle gereken 12,75 kW;  bir üstteki IEC
#                       motor gücü ( 11 · 15 · 18,5 ).  Referans projenin 11,3'ü dişlisizindi.
#    tabliye, kaide     hesap programının makine daireli varsayılanları ( ofis
#                       şablonu ):  tabliye 1.200, şase 1.100, dikine kiriş NPU 120,
#                       yan yatak NPU 140, boyu 1.400
#    makine dairesi     3.800 × 2.600 ( çizim örneğinin odası );  odanın yeri ve
#                       kapısı formun varsayılanı ( kuyuya ortalı, önü hizalı )
#    makine_tst         3.400 kg — referans proje makinesinin değeri AYNEN kaldı ( A 160'ın
#                       katalog değeri elde yok );  hesapta kasnağa gelen 1.581 kg
ASANSOR_MD = {k: v for k, v in ASANSOR.items() if k not in ("makine_verimi", "makine_raya_biniyor")}
ASANSOR_MD.update({
    "makine_tipi": "Dişli", "makine_agirligi": 350, "motor_gucu": 15,
    "tabliye_yuksekligi": 1200, "sase_yuksekligi": 1100, "dikine_kiris": 120,
    "yan_yatak": 140,             # kaidenin açıklığı çizimden ( halatlara ortalı, makineyi sarar )
})
ORTAK_MD = {"mk_yok": False, "mk_uzunluk": 3800, "mk_genislik": 2600}
