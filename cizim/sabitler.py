# -*- coding: utf-8 -*-
"""
ÇİZİM SABİTLERİ  —  ofisin hep aynı kullandığı ÜRÜN ölçüleri  ( mm )

Bunlar hesabın ofis sabitleri DEĞİLDİR;  yalnız çizimin ayrıntısını belirler
ve hiçbir hesaba girmez.  Paftada kaynakları KABUL sayılır.

NEREDEN GELDİLER:  ELEport'un yayımlanmış örnek projesinin ( PROJE 5 )
paftasındaki çizimin VEKTÖR GEOMETRİSİNDEN ölçüldüler;  ölçek 1/20 üzerinden
kalibre edildi ve kalibrasyon ray profilleriyle doğrulandı ( T89/B 89 × 62 ve
T70/A 70 × 65 tam çıktı ).  Yani tek bir projenin donanımıdır;  tedarikçinin
kendi ölçüleri gelince buradan değiştirilir.
"""

SABIT = {
    #  ── RAY KONSOLU ──────────────────────────────────────────────────
    "konsol_kabin_en": 55,        # duvara dik  ( ray arkasından duvara )
    "konsol_kabin_boy": 300,      # ray ekseni boyunca
    "konsol_agirlik_en": 160,
    "konsol_agirlik_boy": 100,
    "konsol_civata_araligi": 65,   # konsol plakasındaki cıvata deliklerinin arası
    "konsol_civata_capi": 14,
    #  KARŞI AĞIRLIK YANDAYSA o taraftaki kabin rayı, iki ağırlık rayı
    #  konsoluna bağlı dikine bir ara kirişe tutturulur;  kirişin plandaki
    #  eni  ( ELEport paftası:  50 mm ).
    "ara_kiris_en": 50,

    #  ── PATEN  ( kaymalı gövde;  makaralıda da aynı iz kullanılır ) ──
    "paten_en": 50,               # ray yüzüne dik
    "paten_boy": 100,             # ray ekseni boyunca

    #  ── KABİN ────────────────────────────────────────────────────────
    "kabin_pano_yan": 45,         # kabin yan panosu kalınlığı
    "kabin_pano_arka": 33,
    "sase_dikme": 30,             # şase dikmesinin plandaki kalınlığı
    "kabin_kasnak_genislik": 92,  # 2:1 askıda kabin kasnağının genişliği

    #  ── KAPI ─────────────────────────────────────────────────────────
    "kasa_yan": 120,              # kat kapısı kasasının yan genişliği
    "kasa_derinlik": 60,
    "kanat_kalinlik": 30,
    "kanat_araligi": 50,          # teleskopik kanatlar arası
    "kabin_kapisi_kutu_en": 270,  # kabin kapısı mekanizma kutusu
    "kabin_kapisi_kutu_boy": 140,
    "esik_derinlik": 60,          # kat kapısı eşiği  ( kuyu içine taşan )
    "kabin_esik_derinlik": 40,
    #  Kapı yanlarındaki bina duvarı ÇİZİLMEZ ( 0 ):  kuyu paftasında işe
    #  yaramıyor, ölçü yazılarının altına giriyordu.  Gerekirse >0 yapılır.
    "bina_duvari": 0,

    #  ── KARŞI AĞIRLIK ────────────────────────────────────────────────
    "agirlik_cerceve": 40,        # çerçeve profilinin kalınlığı

    #  ── KUYU DİBİ ────────────────────────────────────────────────────
    #  Tampon gövdesi ve taban plakası ( planda ):  ELEport kuyu dibi
    #  paftasından ölçüldü ( ~100 mm gövde, ~150 mm kare taban ).
    "tampon_capi": 100,
    "tampon_taban": 150,
    #  Regülatör gergi kasnağının planda görünen eni ( ELEport:  ~67 mm ).
    "gergi_kasnak_eni": 65,
    #  Kuyu dibi merdiveni  ( TS EN 81-20 Ek F ):  basamak net eni en az
    #  280 mm ( F.3.2 a ) + iki dikme en çok 35'er mm ( F.3.1 a ) = 350;
    #  dikme derinliği en çok 100 mm ( F.3.1 a ).  Duvara yaslı saklanır.
    "merdiven_eni": 350,
    "merdiven_derinlik": 100,

    #  ── KUYU ÜSTÜ  ( makine dairesiz ) ───────────────────────────────
    #  ELEport'un MRL paftasındaki "Machine Room" çiziminin vektör
    #  geometrisinden ölçüldü ( 1/20 ).  Tek bir makinenin ölçüleridir —
    #  kullanılan makinenin kataloğu gelince buradan değiştirilir.
    "tahrik_kasnak_kalinlik": 105,   # tahrik kasnağının planda görünen eni
    "makine_en": 298,                # makine gövdesi ( kasnak ekseni boyunca )
    "makine_boy": 279,
    "makine_kasnak_boslugu": 15,     # kasnak ile gövde arası
    #  Halat bağlantıları ( 2:1 askıda halatın kuyu tepesine bağlandığı yer )
    "agirlik_baglanti_en": 264, "agirlik_baglanti_boy": 120,
    "agirlik_baglanti_x": 12,        # halattan plakanın duvar tarafı kenarına
    "agirlik_baglanti_y": 39,        # halattan plakanın kasnak tarafı kenarına
    "kabin_baglanti_en": 127, "kabin_baglanti_boy": 200,
    "kabin_baglanti_x": 100,         # halattan plakanın kabin tarafı kenarına
    #  Hız regülatörü:  kasnak eni ve gövde
    "regulator_eni": 80, "regulator_govde_en": 130, "regulator_govde_boy": 180,
    #  ── MAKİNE DAİRESİ ───────────────────────────────────────────────
    #  Kumanda panosu:  LiftDesigner makine dairesi planındaki pano 600 × 400.
    "kumanda_pano_en": 600, "kumanda_pano_derinlik": 400,
    #  Regülatör halatı deliği:  LiftDesigner planında 200 × 200.
    "regulator_delik": 200,
    #  Askı halatı deliğinde halat demetinin çevresine bırakılan pay ( mm ).
    #  STANDARDIN SAYISI DEĞİLDİR:  m.5.2.6.3.3 yalnız "amacı için en küçük"
    #  der;  çizim kabulüdür, proje ölçüsüyle değiştirilir.
    "halat_delik_payi": 30,
    #  Acil kurtarma ve test panosu ( TS EN 81-20 m.5.2.6.6 ) — ELEport: 400 × 300
    "acil_pano_en": 400, "acil_pano_derinlik": 300,

    #  ── KUMANDA PANOSU ───────────────────────────────────────────────
    "pano_en": 400,
    "pano_derinlik": 90,
    "pano_duvar": "Sağ",
}


def sabitler(ozel=None):
    """Ofis çizim sabitleri + projeye özel ezmeler."""
    s = dict(SABIT)
    for k, v in (ozel or {}).items():
        if k in SABIT and v is not None:
            s[k] = v
    return s
