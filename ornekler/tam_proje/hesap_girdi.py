# -*- coding: utf-8 -*-
"""ELEport PROJE 5 · Elevator 3 — hesap motoru girdisi.
Kaynak:  ~/asansör projeleri/sample-project.pdf ( ELEport, 3 Eylül 2025 ) ve hesap
programının TEST 12'si.  Tampon ELEport'ta belirsiz:  OLEO LB 16 ( oleoelevator.com )."""
ASANSOR = {
    "asansor_adi": "Elevator 3",
    "asansor_tipi": "İnsan asansörü",
    "beyan_yuku": 800, "kabin_agirligi": 900, "beyan_hizi": 1.6,
    "aski_orani": 2, "seyir_mesafesi": 29.0, "son_kat_yuksekligi": 5000, "kuyu_dibi": 1500,
    "kabin_genisligi": 1350, "kabin_derinligi": 1400, "kabin_kaciklik": 0,
    "kat_kapisi_tipi": "Teleskopik Sol", "kapi_genisligi": 900,
    "ray_kapi_arasi": 1017,
    "tahrik_kasnak_capi": 240, "saptirma_kasnak_capi": 294, "saptirma_kasnak_min_capi": 240,
    "halat_capi": 6.5, "halat_adedi": 7, "halat_birim_kutle": 0.179, "halat_kopma_kN": 31.5,
    "sarilma_acisi": 180, "kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmiş",
    "kasnak_tek_yon": 2, "kasnak_ters_yon": 0, "acil_frenleme_a": 0.5,
    "denge_zinciri": "Var", "kasnak_belgesi": "Var",
    "motor_gucu": 11.3, "makine_tst": 3400, "makine_verimi": 0.8415, "makine_tipi": "Dişlisiz",
    #  MRL:  makine şasesi raylara oturur ( ELEport "Motor Bedplate Calculation":
    #  şase kabin ve ağırlık raylarına dayanır;  motor 250 kg ).  Hesap programı
    #  bir raya ( Gm + Tst ) / 4 yükler ( m.5.7.2.3.7 );  ELEport kendi paftasında
    #  raya 800 kg ( ray hesabında 1.000 kg ) KABUL eder.
    "makine_raya_biniyor": "Kılavuz raylara", "makine_agirligi": 250,
    "kablo_birim_kutle": 0.44,
    "kabin_ray_profili": "89 x 62 x 15,88", "agirlik_ray_profili": "70 x 65 x 9",
    "kabin_konsol_arasi": 1500, "agirlik_konsol_arasi": 1500, "ray_celigi_rm": 450,
    "kabin_paten_arasi": 3300, "agirlik_paten_arasi": 1500,
    "paten_tipi": "Kaymalı", "agirlik_paten_tipi": "Makaralı", "guvenlik_tertibati": "Kaymalı",
    "agirlik_yeri": "Sol", "agirlik_genisligi": 850, "agirlik_derinligi": 160,
    "reg_kasnak_capi": 240,
    "tampon_tipi": "Hidrolik  ( enerji yutmalı )",
    "kabin_tampon_adedi": 1, "agirlik_tampon_adedi": 1,
    "kabin_tampon_baba": 306, "kabin_tampon_boyu": 618, "kabin_tampon_ezilme": 203,
    "kabin_carpma_arasi": 96,
    "agirlik_tampon_baba": 300, "agirlik_tampon_ezilme": 203, "agirlik_carpma_arasi": 150,
    "siginma_tipi_ust": "Çömelme", "siginma_tipi_dip": "Çömelme",
    "_ofis": {"q_denge": 0.50, "kanal_gama_v": 38},
    "kuyu_genisligi": 2100,
}
ORTAK = {"mk_yok": True}
