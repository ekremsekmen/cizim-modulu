"""OFİSİN GERÇEK PROJELERİ ( ~/Desktop/örnekliftler ) — 5. adımın test verisi.

Her proje programın formuna girildiği gibi:  hesabın ve çizimin alanları.
Ölçüler projelerin kendi çizimlerinden ( LiftDesigner:  veri bloğu ve kuyu
planının ölçüleri, AutoCAD 2027 DXF'e çevrilip ölçek çarpanıyla okundu ) —
kaynak satırları her projenin yanında.

EŞLEME ( LiftDesigner → program ):
    SW · SD           kuyu genişliği · derinliği
    CW · CD · CH      kabin genişliği · derinliği · iç yüksekliği
    DW                kapı genişliği ( Kapilar:  800 x 2000 → yükseklik 2.000 )
    BG                kabin rayları arası ( ray uçları )
    DBG               ağırlık rayları arası
    EE                kabinin DIŞ önünden kabin ray eksenine;  kabinin iç önü 140
                      geride, bizim RK ray ekseninden kabin iç önüne 120 ekler:
                      RK = EE − 20
    OH · Kuyu dibi    son kat yüksekliği · kuyu dibi
    Seyir · Durak     seyir mesafesi ( m ) · durak adedi
    RDB               halat iniş aralığı = tahrik kasnağı çapı ( makine dairesiz )
    kaçıklıklar       kuyu planının zincir ölçülerinden ( kabin ekseni, kapı
                      ekseni, ağırlık ekseni – duvar )
Karşılığı olmayanlar:  karşı ağırlık rayı 45 × 45 × 5 ( listede en küçüğü
50 × 50 × 5 );  kapı tipi ( projede yazmıyor — varsayılan teleskopik ).

BEKLENEN ( test_gercek_projeler.py ):  projenin çiziminde okunan ve programın
kendi geometrisinden çıkan ölçüler ( halat inişleri ) ile programın bugünkü
hükmü ( çizilir mi, bölüm 11 ).  Program projeden farklı hükmediyorsa sebebi
testin yanında yazılıdır.
"""

#  Ortak:  LiftDesigner projelerinde tampon hidrolik, kabin 2.000
_LD = {"beyan_hizi": 1.0, "kabin_ic_yuksekligi": 2000, "kapi_yuksekligi": 2000,
       "tampon_tipi": "Hidrolik  ( enerji yutmalı )", "agirlik_ray_profili": "50 x 50 x 5",
       "agirlik_derinligi": 150}

#  Duvar kalınlıkları LiftDesigner planlarından ( ön · arka · sol · sağ;  2 Eki ).
PROJELER = {
    #  12495-18 ( makine dairesiz, ağırlık arkada, 2:1 kabin üstü çapraz ) —
    #  Normal yük 800 · Hiz 1 · Seyir 3500 · Durak 2 · Surucu 2:1 · Kabin-ray
    #  90 x 75 x 16 · SW1650 · SD1950 · CW/CD 1100 · DW800 · BG 1280 · DBG 1100 ·
    #  EE610 · OH4200 · Kuyu dibi 1700 · RDB240.  Kuyu planı:  kabin ekseni sol
    #  duvardan 885 ( +60 ), kapı ekseni 1.035 ( +150 ), ağırlık ekseni arka
    #  duvardan 354.
    "12495-18": {**_LD, "kuyu_duvar_on": 200, "kuyu_duvar_arka": 200, "kuyu_duvar_sol": 250, "kuyu_duvar_sag": 250,
                 "beyan_yuku": 800, "aski_orani": 2, "seyir_mesafesi": 3.5,
                 "durak_adedi": 2, "son_kat_yuksekligi": 4200, "kuyu_dibi": 1700,
                 "kuyu_genisligi": 1650, "kuyu_derinligi": 1950, "kabin_genisligi": 1100,
                 "kabin_derinligi": 1100, "kapi_genisligi": 800, "kabin_yana_kaciklik": 60,
                 "kapi_kaciklik": 150, "kabin_ray_arasi": 1280, "agirlik_ray_arasi": 1100,
                 "agirlik_ray_duvar": 354, "ray_kapi_arasi": 590, "agirlik_yeri": "Arka",
                 "aski_duzeni": "Kabin üstü", "makine_raya_biniyor": "Bina yapısına",
                 "tahrik_kasnak_capi": 240, "kabin_ray_profili": "90 x 75 x 16",
                 "mk_yok": True},
    #  1250 KG ( makine dairesiz, ağırlık sağda, 2:1 kabin altı ) — Normal yük 1250 ·
    #  Seyir 12000 · Durak 5 · Kabin-ray 90 x 75 x 16 · SW2000 · SD2400 · CW1240 ·
    #  CD2100 · DW1100 · BG 1450 · DBG 1200 · EE1120 · OH3400 · Kuyu dibi 1450 ·
    #  RDB320.  Kuyu planı:  kabin ekseni 875 ( −125 ), kapı ekseni 855 ( −20 ),
    #  ağırlık ekseni sağ duvardan 165.
    "1250 KG": {**_LD, "kuyu_duvar_on": 100, "kuyu_duvar_arka": 100, "kuyu_duvar_sol": 100, "kuyu_duvar_sag": 100,
                "beyan_yuku": 1250, "aski_orani": 2, "seyir_mesafesi": 12.0,
                "durak_adedi": 5, "son_kat_yuksekligi": 3400, "kuyu_dibi": 1450,
                "kuyu_genisligi": 2000, "kuyu_derinligi": 2400, "kabin_genisligi": 1240,
                "kabin_derinligi": 2100, "kapi_genisligi": 1100, "kabin_yana_kaciklik": -125,
                "kapi_kaciklik": -20, "kabin_ray_arasi": 1450, "agirlik_ray_arasi": 1200,
                "agirlik_ray_duvar": 165, "ray_kapi_arasi": 1100, "agirlik_yeri": "Sağ",
                "aski_duzeni": "Kabin altı", "tahrik_kasnak_capi": 320,
                "kabin_ray_profili": "90 x 75 x 16", "mk_yok": True},
    #  4815-6 ( makine dairesiz, ağırlık solda, 2:1 kabin altı ) — Normal yük 800 ·
    #  Seyir 18150 · Durak 7 · Kabin-ray 89 x 62 x 15.88 · SW2100 · SD2000 ·
    #  CW1350 · CD1400 · DW900 · BG 1540 · DBG 1100 · EE910 · OH4650 · Kuyu dibi
    #  1700 · RDB240.  Kuyu planı:  kabin ekseni 1.165 ( +115 ), kapı ekseni
    #  1.315 ( +150 ), ağırlık ekseni sol duvardan 175, kabin halatı x 415.
    "4815-6": {**_LD, "kuyu_duvar_on": 200, "kuyu_duvar_arka": 250, "kuyu_duvar_sol": 200, "kuyu_duvar_sag": 200,
               "beyan_yuku": 800, "aski_orani": 2, "seyir_mesafesi": 18.15,
               "durak_adedi": 7, "son_kat_yuksekligi": 4650, "kuyu_dibi": 1700,
               "kuyu_genisligi": 2100, "kuyu_derinligi": 2000, "kabin_genisligi": 1350,
               "kabin_derinligi": 1400, "kapi_genisligi": 900, "kabin_yana_kaciklik": 115,
               "kapi_kaciklik": 150, "kabin_ray_arasi": 1540, "agirlik_ray_arasi": 1100,
               "agirlik_ray_duvar": 175, "ray_kapi_arasi": 890, "agirlik_yeri": "Sol",
               "aski_duzeni": "Kabin altı", "tahrik_kasnak_capi": 240,
               "kabin_ray_profili": "89 x 62 x 15,88", "mk_yok": True},
    #  1022 ( makine daireli, ağırlık arkada, 1:1, dişli A 160 ) — Normal yük 750 ·
    #  Seyir 9000 · Durak 4 · Surucu 1:1 · Kabin-ray 70 x 65 x 9 · SW2000 ·
    #  SD2250 · CW1360 · CD1330 · DW900 · BG 1790 · DBG 1700 · EE750 · OH4330 ·
    #  Kuyu dibi 1700 · MRW/MRD 4800 · HM3400 · RDA/RDB 930.  Kuyu planı:  kabin
    #  ekseni 1.005 ( +5 ), kapı ekseni 825 ( −180 ), ağırlık ekseni arka
    #  duvardan 430, kabin halatı y 890 ( ray ekseni ), ağırlığınki 1.820;
    #  regülatör halatı sol duvardan ~65 ( rayın yanı ), ray ekseninin ~280 ve
    #  580 arkasında.  Kasnak düzenlemesi:  Ø480 tahrik, Ø400 saptırma, merkezler
    #  arası 490 / 842, RDA / RDB 930, sarım açısı 152.
    "1022": {**_LD, "kuyu_duvar_on": 200, "kuyu_duvar_arka": 200, "kuyu_duvar_sol": 200, "kuyu_duvar_sag": 200,
             "beyan_yuku": 750, "aski_orani": 1, "seyir_mesafesi": 9.0,
             "durak_adedi": 4, "son_kat_yuksekligi": 4330, "kuyu_dibi": 1700,
             "kuyu_genisligi": 2000, "kuyu_derinligi": 2250, "kabin_genisligi": 1360,
             "kabin_derinligi": 1330, "kapi_genisligi": 900, "kabin_yana_kaciklik": 5,
             "kapi_kaciklik": -180, "kabin_ray_arasi": 1790, "agirlik_ray_arasi": 1700,
             "agirlik_ray_duvar": 430, "ray_kapi_arasi": 730, "agirlik_yeri": "Arka",
             "makine_tipi": "Dişli", "tahrik_kasnak_capi": 480, "kabin_ray_profili": "70 x 65 x 9",
             "mk_yok": False, "mk_genislik": 4800, "mk_uzunluk": 4800, "md_yukseklik": 3400},
    #  1275 ( makine daireli, ağırlık arkada, 2:1 kabin üstü;  LiftDesigner
    #  kasnakları derinlik boyunca düz koyar — program çapraz, kullanıcı kararı ) —
    #  Normal yük 1275 · Seyir 27000 · Durak 10 · Kabin-ray 89 x 62 x 15.88 ·
    #  Karsi agirlik-ray 50 x 50 x 5 · SW2100 · SD2700 · CW1440 · CD2000 · DW1100 ·
    #  BG 1750 · DBG 1800 · EE1077.5 · OH4080 · Kuyu dibi 1700 · MRW3500 · MRD6900 ·
    #  HM3380 · RDB240.  Kuyu planı:  kabin ekseni 1.015 ( −35 ), kapı ekseni 895
    #  ( −120 ), ağırlık 130 derin, ekseni arka duvardan 230;  halat inişleri y
    #  2.230 ( kabin ) ve 2.470 ( ağırlık ).
    "1275": {**_LD, "kuyu_duvar_on": 200, "kuyu_duvar_arka": 200, "kuyu_duvar_sol": 200, "kuyu_duvar_sag": 250,
             "beyan_yuku": 1275, "aski_orani": 2, "seyir_mesafesi": 27.0,
             "durak_adedi": 10, "son_kat_yuksekligi": 4080, "kuyu_dibi": 1700,
             "kuyu_genisligi": 2100, "kuyu_derinligi": 2700, "kabin_genisligi": 1440,
             "kabin_derinligi": 2000, "kapi_genisligi": 1100, "kabin_yana_kaciklik": -35,
             "kapi_kaciklik": -120, "kabin_ray_arasi": 1750, "agirlik_ray_arasi": 1800,
             "agirlik_ray_duvar": 230, "agirlik_derinligi": 130, "ray_kapi_arasi": 1057.5,
             "agirlik_yeri": "Arka", "aski_duzeni": "Kabin üstü", "makine_tipi": "Dişli",
             "tahrik_kasnak_capi": 240, "kabin_ray_profili": "89 x 62 x 15,88",
             "mk_yok": False, "mk_genislik": 3500, "mk_uzunluk": 6900, "md_yukseklik": 3380},
    #  800 KG ( makine daireli, ağırlık arkada, 1:1, dişli A 125 ) — Normal yük 750 ·
    #  Seyir 27500 · Durak 10 · Surucu 1:1 · Kabin-ray 89 x 62 x 15.88 · SW2000 ·
    #  SD2000 · CW1290 · CD1350 · DW900 · BG 1500 · DBG 1200 · EE710 · OH4050 ·
    #  Kuyu dibi 1700 · MRW4950 · MRD6900 · HM3420 · RDA/RDB 970.  Kuyu planı:
    #  kabin ekseni 1.060 ( +60 ), kapı kabin ekseninde, ağırlık ekseni arka
    #  duvardan 180;  halat inişleri y 850 ve 1.820.  Kasnak düzenlemesi:  Ø500
    #  tahrik, Ø400 saptırma, merkezler arası 520 / 822, RDA / RDB 970, sarım
    #  açısı 151.  Giriş:  kaba boşluk sol duvardan 470, 1.180 geniş, 2.240 yüksek.
    "800 KG": {**_LD, "kuyu_duvar_on": 200, "kuyu_duvar_arka": 200, "kuyu_duvar_sol": 250, "kuyu_duvar_sag": 250,
               "beyan_yuku": 750, "aski_orani": 1, "seyir_mesafesi": 27.5,
               "durak_adedi": 10, "son_kat_yuksekligi": 4050, "kuyu_dibi": 1700,
               "kuyu_genisligi": 2000, "kuyu_derinligi": 2000, "kabin_genisligi": 1290,
               "kabin_derinligi": 1350, "kapi_genisligi": 900, "kabin_yana_kaciklik": 60,
               "kapi_kaciklik": 0, "kabin_ray_arasi": 1500, "agirlik_ray_arasi": 1200,
               "agirlik_ray_duvar": 180, "ray_kapi_arasi": 690, "agirlik_yeri": "Arka",
               "makine_tipi": "Dişli", "tahrik_kasnak_capi": 500,
               "kabin_ray_profili": "89 x 62 x 15,88",
               "mk_yok": False, "mk_genislik": 4950, "mk_uzunluk": 6900, "md_yukseklik": 3420},
}
