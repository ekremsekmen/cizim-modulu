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
    #  Kumanda panosunun yüksekliği:  LiftDesigner "477-8" projesinin
    #  "Dikey 1:50" kesitinde yere oturan pano 2.000 mm.
    "kumanda_pano_yukseklik": 2000,
    #  Askı halatı deliğinde halat demetinin çevresine bırakılan pay ( mm ).
    #  STANDARDIN SAYISI DEĞİLDİR:  m.5.2.6.3.3 yalnız "amacı için en küçük"
    #  der;  çizim kabulüdür, proje ölçüsüyle değiştirilir.
    "halat_delik_payi": 30,
    #  Acil kurtarma ve test panosu ( TS EN 81-20 m.5.2.6.6 ) — ELEport: 400 × 300
    "acil_pano_en": 400, "acil_pano_derinlik": 300,

    #  ── KABİNİN DÜŞEY ÖLÇÜLERİ ( döşemeden, mm ) ──────────────────────
    #  ELEport'un "Cabin at Bottom / Top Floor" kesitlerinin vektör
    #  geometrisinden ölçüldü ( 1/30 ):  iç yükseklik 2.250, tavan 60 →
    #  tavan üstü 2.310;  taban 20 + 100;  şase alt kirişinin altı −480,
    #  üst kirişin üstü −480 + paten arası ( 3.300 ) = 2.820;  paten 140;
    #  fren bloğu platformun altında 350;  kabin kasnağı merkezi −295.
    "kabin_tavan_kalinlik": 60,
    "kabin_taban_kalinlik": 120,
    "sase_alt_derinlik": 480,       # döşemeden şase alt kirişinin altına
    "paten_yukseklik": 140,
    "fren_blogu_yukseklik": 350,
    "kabin_kasnak_derinlik": 295,   # döşemeden kabin kasnağının merkezine
    "sase_dikme_derinlik": 300,     # şase dikmesinin kesitteki eni ( ray ekseninde )
    "etek_tahtasi": 100,            # TS EN 81-20 m.5.4.7.2 a — en az 0,10 m
    #  Kuyu tavanının en alt kısmı ( kiriş vb. ) döşeme altından — hesap
    #  programının "kuyu tavanı payı" ( 150 ) ile aynı kabul.
    "tavan_kirisi": 150,

    #  ── KUYU ÜSTÜ DONANIMININ DÜŞEY ÖLÇÜLERİ ( makine dairesiz ) ──────
    #  ELEport'un "Cabin at Bottom Floor", "Cabin at Top Floor" ve "Cabin
    #  Sits on Buffer" kesitlerinin vektörlerinden ( 1/30 );  kuyu tavanından
    #  AŞAĞI ölçülür.  Plandaki yerleri kuyu_ustu.yerlesim'dekiyle birebir
    #  tuttu ( makine gövdesi 101 – 399, kasnak ekseni 250, bağlantılar ).
    #  Makine kapağının üstü tavanın 250 altında;  gövde Ø 298 ( makine_en ) +
    #  kapak 47 = 345;  şase 200 → şase üstü tavandan 595, altı 795;
    #  tahrik kasnağının merkezi gövdenin ortası ( tavandan 446 ).
    "makine_tepe_boslugu": 250,
    "makine_kapak_yukseklik": 47,
    "makine_kapak_en": 160,          # kasnak ekseni boyunca  ( ön kesitte )
    "makine_kapak_boy": 212,         # yan kesitte
    "makine_sase_yukseklik": 200,
    #  Şase ağırlık raylarının ve o taraftaki kabin rayının başına oturur:
    #  duvardan 20 mm açıkta başlar, kabin rayının arkasında biter;  derinlik
    #  boyunca ağırlık raylarının dış yüzlerinden 8'er mm taşar.
    "makine_sase_duvar": 20,
    "makine_sase_ray_payi": 8,
    #  Şasenin altındaki raylar şase üstünün 55 altında biter ( tavandan 650 );
    #  öbür kabin rayı tavanın 50 altına çıkar, kabin halat bağlantısı onun
    #  başındadır ( tavandan 280 – 645 ).  Ağırlık halat bağlantısı şasenin
    #  üstündedir ( 298 ).
    "ray_sase_icinde": 55,
    "kabin_rayi_tepe": 50,
    "kabin_baglanti_ust": 280, "kabin_baglanti_alt": 645,
    "agirlik_baglanti_yukseklik": 298,
    #  Hız regülatörü:  kasnak merkezi tavandan 462, gövde 433 – 645.
    "regulator_kasnak_merkez": 462,
    "regulator_govde_ust": 433, "regulator_govde_alt": 645,
    #  Kuyu dibindeki gergi düzeni ( ELEport "Cabin at Top Floor" ):  kasnak
    #  merkezi tabandan 520;  kol tabandan 500 – 540, kabin ray ekseninin 80
    #  önünden kasnağın 360 ötesine;  ağırlık 160 × 175, tabandan 390,
    #  kasnağın 260 – 420 ötesinde.
    "gergi_kasnak_merkez": 520,
    "gergi_kol_alt": 500, "gergi_kol_yukseklik": 40, "gergi_kol_ray": 80, "gergi_kol_uc": 360,
    "gergi_agirlik_alt": 390, "gergi_agirlik_yukseklik": 175,
    "gergi_agirlik_yakin": 260, "gergi_agirlik_uzak": 420,

    #  ── KARŞI AĞIRLIK ( düşey ) ──────────────────────────────────────
    #  ELEport "Counterweight Sits on Buffer" ( 1/30 ):  çerçeve alt kirişin
    #  altından üst kirişin üstüne 2.920;  kasnak merkezi üst kirişin 110
    #  altında;  patenler çerçevenin üstünde ve altında 140 ( paten_yukseklik ).
    "agirlik_yukseklik": 2920,
    "agirlik_kasnak_ust": 110,
    "agirlik_kiris": 10,

    #  ── RAY KONSOLU VE EK ( düşey ) ───────────────────────────────────
    #  ELEport "Rail Bracket 1/42":  ilk konsolun üstü kuyu tabanından 500,
    #  konsol 60 yüksek;  ray ekleri 5.000'de bir ( ray boyu ), ek laması 305.
    "konsol_ilk": 500,
    "konsol_yukseklik": 60,
    "ray_boyu": 5000,
    "ek_lama_boyu": 305,

    #  ── KATLAR ───────────────────────────────────────────────────────
    #  Kat döşemesi 150 ( LiftDesigner "Dikey 1:50" ve ELEport kesitleri );
    #  duvardaki kapı boşluğu kapıdan 200 yüksek ( ELEport:  2.100 / 2.300 ).
    "kat_doseme_kalinlik": 150,
    "kapi_ust_payi": 200,
    "esik_kalinlik": 30,

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
