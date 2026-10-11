# -*- coding: utf-8 -*-
"""
ÇİZİM SABİTLERİ  —  ofisin hep aynı kullandığı ÜRÜN ölçüleri  ( mm )

TEK KATALOG ( karar 12 ):  hepsi hesabın Sabitler sekmesinden değiştirilir
( ofis standardı;  bölümleri BOLUMLER ) ve çizim, yerleşimin ölçü listesi
( olculer ) ile bölüm 11 aynı sayıyı kullanır.  Buradaki değerler fabrika
ayarıdır.  Paftada kaynakları KABUL sayılır.

NEREDEN GELDİLER:  Yayımlanmış bir referans projenin
paftasındaki çizimin VEKTÖR GEOMETRİSİNDEN ölçüldüler;  ölçek 1/20 üzerinden
kalibre edildi ve kalibrasyon ray profilleriyle doğrulandı ( T89/B 89 × 62 ve
T70/A 70 × 65 tam çıktı ).  Yani tek bir projenin donanımıdır;  tedarikçinin
kendi ölçüleri gelince buradan değiştirilir.
"""

import contextlib
import threading

from cizim import izli

SABIT = {
    #  ── RAY KONSOLU ──────────────────────────────────────────────────
    "konsol_kabin_en": 55,  # duvara dik  ( ray arkasından duvara )
    "konsol_kabin_boy": 300,  # ray ekseni boyunca
    "konsol_agirlik_en": 160,
    "konsol_agirlik_boy": 100,
    "konsol_civata_araligi": 65,  # konsol plakasındaki cıvata deliklerinin arası
    "konsol_civata_capi": 14,
    #  KARŞI AĞIRLIK YANDAYSA o taraftaki kabin rayı, iki ağırlık rayı
    #  konsoluna bağlı dikine bir ara kirişe tutturulur;  kirişin plandaki
    #  eni  ( referans proje paftası:  50 mm ).
    "ara_kiris_en": 50,
    #  ── PATEN  ( kaymalı gövde;  makaralıda da aynı iz kullanılır ) ──
    "paten_en": 50,  # ray yüzüne dik
    "paten_boy": 100,  # ray ekseni boyunca
    #  ── KABİN ────────────────────────────────────────────────────────
    #  Kabin panoları ( ofisin kabini:  LiftDesigner PLW = CW + 30, arka 20 —
    #  referans projede 45 · 33 )
    "kabin_pano_yan": 15,  # kabin yan panosu kalınlığı
    "kabin_pano_arka": 20,
    #  Şase dikmesi raya açılan U'dur;  sırtı patenin arkasında ( parcalar.
    #  dikme_bicimi ).  Dil ucundan sırtın arkasına:  paten_en / 2 + sac 5
    #  ( referans projenin yatay kesitinde levha dilin ucundan ~30 geride ).
    #  Kabin dikmenin sırtına değmemeli:  kabin dışı + 2 × bu < DBG ( girdi ).
    "sase_dikme": 30,
    "kabin_kasnak_genislik": 75,  # 2:1 askıda kabin kasnağının genişliği ( ofisin kabini, 1250 KG )
    #  ── KAPI ─────────────────────────────────────────────────────────
    #  referans projenin kuyu planı vektörlerinden ( 1/20 ) ve "Door Detail 1/35"
    #  paftasından:  kat kapısı ünitesi = kasa 60 + eşik 90 = 150;  kanatlar
    #  40 kalın, EŞİĞİN ÜSTÜNDE — teleskopikte iki düzlemde ( eşiğin 5 mm
    #  içinden başlar, düzlemler 45 arayla:  65 – 105 · 110 – 150 ).  Kabin
    #  eşiği de 90;  kabin kapısı kanatları onun üstünde, aynı düzende.
    #  ( Eski 60 / 40 / 30 / 50 değerleri kanatları eşiğin ARKASINA, kabin
    #  eşiğinin ve kabinin içine düşürüyordu. )
    "kasa_yan": 120,  # kat kapısı kasasının yan genişliği
    "kasa_derinlik": 60,
    "kanat_kalinlik": 40,
    "kanat_araligi": 45,  # teleskopik kanat düzlemleri arası
    "kanat_esik_payi": 5,  # ilk kanat düzlemi eşiğin kenarından içeride
    #  KANAT CEBİ:  otomatik kapının kanatları açılınca kapı boşluğunun yanında
    #  durur;  kat ve kabin kapısı ünitesi o yanda kapının yarısı + bu kadar
    #  uzanır ( LiftDesigner, altı projenin hepsinde:  DW 800 → 430, 900 → 480,
    #  1.100 → 580;  kat kapısı ünitesi kasa 120 + DW + cep, kabin kapısınınki
    #  DW + cep ).
    "kanat_cebi_payi": 30,
    "kabin_kapisi_kutu_en": 270,  # kabin kapısı mekanizma kutusu
    "kabin_kapisi_kutu_boy": 140,
    "esik_derinlik": 90,  # kat kapısı eşiği
    "kabin_esik_derinlik": 90,
    #  Kapı yanlarındaki bina duvarı ÇİZİLMEZ ( 0 ):  kuyu paftasında işe
    #  yaramıyor, ölçü yazılarının altına giriyordu.  Gerekirse >0 yapılır.
    "bina_duvari": 0,
    #  ── KARŞI AĞIRLIK ────────────────────────────────────────────────
    "agirlik_cerceve": 40,  # çerçeve profilinin kalınlığı
    #  ── KUYU DİBİ ────────────────────────────────────────────────────
    #  Tampon gövdesi ve taban plakası ( planda ):  referans proje kuyu dibi
    #  paftasından ölçüldü ( ~100 mm gövde, ~150 mm kare taban ).
    "tampon_capi": 100,
    "tampon_taban": 150,
    #  Regülatör gergi kasnağının planda görünen eni ( referans proje:  ~67 mm ).
    "gergi_kasnak_eni": 65,
    #  Kuyu dibi merdiveni  ( TS EN 81-20 Ek F ):  basamak net eni en az
    #  280 mm ( F.3.2 a ) + iki dikme en çok 35'er mm ( F.3.1 a ) = 350;
    #  dikme derinliği en çok 100 mm ( F.3.1 a ).  Duvara yaslı saklanır.
    "merdiven_eni": 350,
    "merdiven_derinlik": 100,
    #  ── KUYU ÜSTÜ  ( makine dairesiz ) ───────────────────────────────
    #  referans projenin MRL paftasındaki "Machine Room" çiziminin vektör
    #  geometrisinden ölçüldü ( 1/20 ).  Tek bir makinenin ölçüleridir —
    #  kullanılan makinenin kataloğu gelince buradan değiştirilir.
    "tahrik_kasnak_kalinlik": 105,  # tahrik kasnağının planda görünen eni
    "makine_en": 298,  # makine gövdesi ( kasnak ekseni boyunca )
    "makine_boy": 279,
    "makine_kasnak_boslugu": 15,  # kasnak ile gövde arası
    #  Halat bağlantıları ( 2:1 askıda halatın kuyu tepesine bağlandığı yer )
    "agirlik_baglanti_en": 264,
    "agirlik_baglanti_boy": 120,
    "agirlik_baglanti_x": 12,  # halattan plakanın duvar tarafı kenarına
    "agirlik_baglanti_y": 39,  # halattan plakanın kasnak tarafı kenarına
    "kabin_baglanti_en": 127,
    "kabin_baglanti_boy": 200,
    "kabin_baglanti_x": 100,  # halattan plakanın kabin tarafı kenarına
    #  Hız regülatörü:  kasnak eni ve gövde
    "regulator_eni": 80,
    "regulator_govde_en": 130,
    "regulator_govde_boy": 180,
    #  ── MAKİNE DAİRESİ ───────────────────────────────────────────────
    #  Kumanda panosu:  LiftDesigner makine dairesi planındaki pano 600 × 400.
    "kumanda_pano_en": 600,
    "kumanda_pano_derinlik": 400,
    #  Kumanda panosunun yüksekliği:  LiftDesigner "477-8" projesinin
    #  "Dikey 1:50" kesitinde yere oturan pano 2.000 mm.
    "kumanda_pano_yukseklik": 2000,
    #  Askı halatı deliğinde halat demetinin çevresine bırakılan pay ( mm ).
    #  STANDARDIN SAYISI DEĞİLDİR:  m.5.2.6.3.3 yalnız "amacı için en küçük"
    #  der;  çizim kabulüdür, proje ölçüsüyle değiştirilir.
    "halat_delik_payi": 30,
    #  Acil kurtarma ve test panosu ( TS EN 81-20 m.5.2.6.6 ) — referans proje: 400 × 300
    "acil_pano_en": 400,
    "acil_pano_derinlik": 300,
    #  ── KABİNİN DÜŞEY ÖLÇÜLERİ ( döşemeden, mm ) ──────────────────────
    #  OFİSİN KABİNİ ( kullanıcı kararı 30 Eyl — 5. adım ):  ofisin altı
    #  LiftDesigner projesinin hepsinde aynı kabin ( 1022 · 12495-18 · 1250 KG ·
    #  1275 · 4815-6 · 800 KG;  kuyu dibi ve tepe kesitleri 1/20, en alt ve en
    #  üst durakta ):  kabin 2.000 ( CH ), platformun altı −50, en alt parça
    #  ( fren bloğu, tamponun çarptığı yer ) −320, tampon tepesi −465 ( çarpma
    #  arası ~150 );  kabin altı kasnak ( 1250 KG, Ø 320 ) −265 / −585, genişliği
    #  75.  ŞASE ( 8 Eki'de ön kesitlerin bloklarından yeniden ölçüldü — K431 ·
    #  4815-6 · 1022 aynı ):  alt paten −320 / −220 ( 100 ), alt kiriş −220 /
    #  −80 ( 140 ), üst kiriş 2.200 / 2.340 ( 140 — iki C 140 × 40 × 5 ), üst
    #  paten 2.340 / 2.440:  PATENLER KİRİŞLERİN DIŞINDA, merkezleri arası
    #  2.660.  30 Eyl'de kirişler paten sanılmıştı ( paten 140, merkezler −150
    #  ve 2.270, paten arası 2.420 ) — üst paten 100 mm aşağıda kalıyordu.
    #  Referans proje de böyle ( üst kiriş 200, patenler kirişin üstünde ).
    #  Tavan kalınlığı 60 ÇİZİM KABULÜ:  LiftDesigner kabini 2.000'de tek
    #  çizgiyle bitirir.  Referans projenin kabini:  REFERANS_PROJE_KABINI.
    "kabin_tavan_kalinlik": 60,
    "kabin_taban_kalinlik": 50,
    "sase_alt_derinlik": 320,  # döşemeden şasenin en alt parçasına ( tampon buraya çarpar )
    "alt_paten_payi": 50,  # şasenin altından alt patenin merkezine ( + yukarı )
    "paten_yukseklik": 100,
    "sase_ust_kiris": 140,  # üst kirişin yüksekliği ( üst paten kirişin üstünde )
    "sase_alt_kiris": 140,  # alt kirişin yüksekliği ( alt patenin üstünde )
    "fren_blogu_yukseklik": 270,
    "kabin_kasnak_derinlik": 425,  # döşemeden kabin kasnağının merkezine
    #  KABİN ÜSTÜ ASKI ( 2:1, ağırlık yanda ):  kasnaklar şasenin üst kirişinin
    #  üstünde;  alt uçları kirişin bu kadar üstünde.  ÇİZİM KABULÜ — referans
    #  projede ve LiftDesigner örneklerinde yandaki ağırlıkla kabin üstü askı
    #  yok;  tedarikçi ölçüsü gelince değiştirilir.
    "kabin_ustu_kasnak_boslugu": 30,
    #  ARKADAKİ AĞIRLIKLA 2:1 ( çapraz kasnaklar, arka_aski ):  kasnaklar kabin
    #  tavanına oturur;  alt uçları tavanın bu kadar üstünde.  LiftDesigner
    #  12495-18 ( makine dairesiz ):  kabin tepesi 2.000, Ø 240 kasnaklar
    #  2.080 – 2.320;  1275 ( makine daireli ):  kasnak merkezi tavanın ~210
    #  üstünde.  Kasnakların arasındaki halat şasenin üst kirişinin altından geçer.
    "kabin_tavani_kasnak_boslugu": 80,
    "sase_dikme_derinlik": 300,  # şase dikmesinin kesitteki eni ( ray ekseninde )
    "etek_tahtasi": 100,  # TS EN 81-20 m.5.4.7.2 a — en az 0,10 m
    #  Kuyu tavanının en alt kısmı ( kiriş vb. ) döşeme altından — hesap
    #  programının "kuyu tavanı payı" ( 150 ) ile aynı kabul.
    "tavan_kirisi": 150,
    #  ── KUYU ÜSTÜ DONANIMININ DÜŞEY ÖLÇÜLERİ ( makine dairesiz ) ──────
    #  referans projenin "Cabin at Bottom Floor", "Cabin at Top Floor" ve "Cabin
    #  Sits on Buffer" kesitlerinin vektörlerinden ( 1/30 );  kuyu tavanından
    #  AŞAĞI ölçülür.  Plandaki yerleri kuyu_ustu.yerlesim'dekiyle birebir
    #  tuttu ( makine gövdesi 101 – 399, kasnak ekseni 250, bağlantılar ).
    #  Makine kapağının üstü tavanın 250 altında;  gövde Ø 298 ( makine_en ) +
    #  kapak 47 = 345;  şase ( yan yatak, referans projede UPN 200 ) → şase üstü
    #  tavandan 595, altı 795;
    #  tahrik kasnağının merkezi gövdenin ortası ( tavandan 446 ).
    "makine_tepe_boslugu": 250,
    #  DUVARDAN DUVARA KİRİŞTE ( arkada ağırlık, makine dairesiz ) makine
    #  kirişlerin üstündedir;  tepesi tavanın bu kadar altında.  LiftDesigner
    #  12495-18:  tavan 4.200, makine 3.750 – 4.150, kirişler ( UPN 100 )
    #  3.650 – 3.750.  Yukarıdaki 250 raylara oturan makinenin projesinden.
    "duvar_kirisi_tepe_boslugu": 50,
    "makine_kapak_yukseklik": 47,
    "makine_kapak_en": 160,  # kasnak ekseni boyunca  ( ön kesitte )
    "makine_kapak_boy": 212,  # yan kesitte
    #  Şase ağırlık raylarının ve o taraftaki kabin rayının başına oturur:
    #  duvardan 20 mm açıkta başlar, kabin rayının arkasında biter;  derinlik
    #  boyunca ağırlık raylarının dış yüzlerinden 8'er mm taşar.
    "makine_sase_duvar": 20,
    "makine_sase_ray_payi": 8,
    #  MAKİNE DAİRESİNDE KAİDE:  yüksekliği ve profilleri hesap programının
    #  girdileridir ( makine_dairesi.sase_yuksekligi · dikine_kiris,
    #  makine.yan_yatak );  boyu çizimden ( halatlara ortalı, makineyi sarar ).
    #  Buradakiler LiftDesigner 12744-3 "kasnak düzenlemesi" ve makine odası
    #  planından ( A 160 makine ):  ayak plakaları 150 × 150 × 20;  kaide
    #  makinenin ve saptırma kasnağının izinden her yana 100 taşar ( LiftDesigner'da
    #  enine;  kaide makineyi sardığından beri uzun eksende de ).  Saptırma kasnağının merkezi döşemenin 400
    #  üstünde ( LiftDesigner:  tahrik kasnağının 842 altı;  ofisin makine daireli
    #  şablonu da "saptırma kasnağı merkezi yerden 40 cm" ).  Çatı döşemesi 150
    #  ( LiftDesigner 477-8 ve 12744-3 );  oda döşemesi hesabın tabliyesidir.
    "md_cerceve_pay": 100,
    "md_cerceve_ayak_plakasi": 150,
    "md_cerceve_ayak_plakasi_kalinlik": 20,
    "md_cati_kalinlik": 150,
    "md_saptirma_yukseklik": 400,
    #  Şasenin altındaki raylar şase üstünün 55 altında biter ( tavandan 650 );
    #  öbür kabin rayı tavanın 50 altına çıkar ( çizimde tavanın en alt kısmının —
    #  tavan_kirisi payının — 50 altına;  makine dairelide bütün raylar ), kabin halat bağlantısı onun
    #  başındadır ( tavandan 280 – 645 ).  Ağırlık halat bağlantısı şasenin
    #  üstündedir ( 298 ).
    "ray_sase_icinde": 55,
    "kabin_rayi_tepe": 50,
    "kabin_baglanti_ust": 280,
    "kabin_baglanti_alt": 645,
    "agirlik_baglanti_yukseklik": 298,
    #  Hız regülatörü:  kasnak merkezi tavandan 462, gövde 433 – 645.
    "regulator_kasnak_merkez": 462,
    "regulator_govde_ust": 433,
    "regulator_govde_alt": 645,
    #  Kuyu dibindeki gergi düzeni ( referans proje "Cabin at Top Floor" ):  kasnak
    #  merkezi tabandan 520;  kol tabandan 500 – 540, kabin ray ekseninin 80
    #  önünden kasnağın 360 ötesine;  ağırlık 160 × 175, tabandan 390.
    #  Ağırlığın merkezi kasnak merkezinden 300 ( referans proje regülatör hesabı:
    #  "Distance from the center of the suspended weight to the center of the
    #  tension pulley A : 300 mm" ) → kasnağın 220 – 380 ötesinde.  Kesitteki
    #  sembolden 260 – 420 ( merkez 340 ) ölçülmüştü:  referans projenin 280'lik
    #  regülatör kaçıklığında ağırlık kuyudan taşıyordu.
    "gergi_kasnak_merkez": 520,
    "gergi_kol_alt": 500,
    "gergi_kol_yukseklik": 40,
    "gergi_kol_ray": 80,
    "gergi_kol_uc": 360,
    "gergi_agirlik_alt": 390,
    "gergi_agirlik_yukseklik": 175,
    "gergi_agirlik_yakin": 220,
    "gergi_agirlik_uzak": 380,
    #  Ağırlığın planda duvara dik ENİ ( kasnak düzlemine ortalı ):  referans
    #  proje vermiyor ( yalnız 35 kg, A 300, B 150 ve yan kesit ).  Eskiden
    #  boyuyla aynı 160 sayılıyordu — hiçbir gerçek gergi o kalınlıkta değil;
    #  ray duvara 35 – 45 mm olan kuyularda ağırlık duvarı aşıyordu ( 1022 ).
    #  ASPAR / Akşöz OSG-A/B kılavuzu:  gergiler kabin rayına tırnakla bağlanır,
    #  tabandan ~450;  25 kg ağırlık 296 × 150 × 82 kasnak düzleminde asılı
    #  ( s. 13 ), gövde 103;  12 kg 2 × 53;  yaylı 108 – 133 ( s. 10 – 12 ).
    "gergi_agirlik_eni": 82,
    #  ── KARŞI AĞIRLIK ( düşey ) ──────────────────────────────────────
    #  referans proje "Counterweight Sits on Buffer" ( 1/30 ):  çerçeve alt kirişin
    #  altından üst kirişin üstüne 2.920, patenler çerçevenin üstünde ve altında;
    #  kasnak merkezi üst kirişin 110 altında;  140'lık patenlerin merkezleri arası
    #  3.060 ( vektörlerden, 8 Eki ).  Girdi hesap programının AĞIRLIK PATEN
    #  ARASIDIR ( patenlerin merkezleri arası );  çerçeve ondan bir paten boyu kısa
    #  ( parca_kotlari.agirlik_kotlari — 8 Eki'ye dek patenler çerçevenin uçlarına ortalıydı ).
    "agirlik_kasnak_ust": 110,
    "agirlik_kiris": 10,
    #  ── RAY KONSOLU VE EK ( düşey ) ───────────────────────────────────
    #  referans proje "Rail Bracket 1/42":  ilk konsolun üstü kuyu tabanından 500,
    #  konsol 60 yüksek;  ray ekleri 5.000'de bir ( ray boyu ), ek laması 305.
    "konsol_ilk": 500,
    "konsol_yukseklik": 60,
    "ray_boyu": 5000,
    "ek_lama_boyu": 305,
    #  ── KATLAR ───────────────────────────────────────────────────────
    #  Kat döşemesi 150 ( LiftDesigner "Dikey 1:50" ve referans proje kesitleri ).
    #  KAT KAPISI ( kullanıcı kararı 1 Eki:  LiftDesigner gibi — "Giriş"
    #  görünüşü, 800 KG · 1022 · 1275 · 4815-6 · 12495-18'de aynı ):  duvardaki
    #  kaba boşluk kapıdan 240 yüksek ( "Kapı giriş açıklığı 2240" ), kapının
    #  iki yanında 140 geniş ( DW 900 → 1.180, DW 1.100 → 1.380 );  kasa
    #  dikmeleri 120 ( kasa_yan ), üstü kapının 220 üstünde ( 2.220 );  eşik
    #  plakası 50.  Referans projenin kendi boşluğu 2.100 / 2.300 ( 200 —
    #  REFERANS_PROJE_KABINI );  eskiden eşik 30 ( kaynaksız ).
    "kat_doseme_kalinlik": 150,
    "kapi_ust_payi": 240,
    "kaba_bosluk_yan_payi": 140,
    "kasa_ust": 220,
    "esik_kalinlik": 50,
    #  Kat göstergesi ( kasa başlığında, kapının ortasında ) ve kat butonu kutusu
    #  ( kapının yanındaki duvarda ):  LiftDesigner "Giriş" — gösterge 500 × 124,
    #  ortası kapının 100 üstünde;  buton kutusu 90 × 240, ortası döşemeden
    #  1.200, kapının kenarından 240;  duvardaki yuvası 160 × 290 ( altı 1.055 ).
    "gosterge_en": 500,
    "gosterge_boy": 124,
    "gosterge_yukseklik": 100,
    "buton_kutu_en": 90,
    "buton_kutu_boy": 240,
    "buton_yukseklik": 1200,
    "buton_kapi_payi": 240,
    "buton_yuva_en": 160,
    "buton_yuva_boy": 290,
}


#  Ekranda ölçünün kaynağı söylenirken kullanılan adlar ( olcu_kaynagi ):
#  bir ölçü sabit bir ürün ölçüsünden geliyorsa "kat kapısı eşiği derinliği
#  90" diye anılır.  Her sabitin adı vardır ( test ).
ETIKET = {
    "konsol_kabin_en": "Kabin rayı konsolunun duvara dik eni",
    "konsol_kabin_boy": "Kabin rayı konsolunun boyu",
    "konsol_agirlik_en": "Ağırlık rayı konsolunun duvara dik eni",
    "konsol_agirlik_boy": "Ağırlık rayı konsolunun boyu",
    "konsol_civata_araligi": "Konsol cıvata delikleri arası",
    "konsol_civata_capi": "Konsol cıvata deliği çapı",
    "ara_kiris_en": "Ray ara kirişinin eni",
    "paten_en": "Patenin ray yüzüne dik eni",
    "paten_boy": "Patenin ray boyunca boyu",
    "kabin_pano_yan": "Kabin yan panosu kalınlığı",
    "kabin_pano_arka": "Kabin arka panosu kalınlığı",
    "sase_dikme": "Kabin rayının dil ucundan şase dikmesinin sırtına",
    "kabin_kasnak_genislik": "Kabin kasnağının genişliği",
    "kasa_yan": "Kat kapısı kasasının yan genişliği",
    "kasa_derinlik": "Kat kapısı kasasının derinliği",
    "kanat_kalinlik": "Kapı kanadı kalınlığı",
    "kanat_araligi": "Teleskopik kapı kanatları arası",
    "kanat_esik_payi": "Kapı kanadının eşik kenarından payı",
    "kanat_cebi_payi": "Kanat cebinin kapının yarısından fazlası",
    "kabin_kapisi_kutu_en": "Kabin kapısı mekanizma kutusunun eni",
    "kabin_kapisi_kutu_boy": "Kabin kapısı mekanizma kutusunun boyu",
    "esik_derinlik": "Kat kapısı eşiği derinliği",
    "kabin_esik_derinlik": "Kabin eşiği derinliği",
    "bina_duvari": "Kapı yanındaki bina duvarı",
    "agirlik_cerceve": "Karşı ağırlık çerçeve profili kalınlığı",
    "tampon_capi": "Tampon gövdesi çapı",
    "tampon_taban": "Tampon taban plakası",
    "gergi_kasnak_eni": "Regülatör gergi kasnağının eni",
    "merdiven_eni": "Kuyu dibi merdiveninin eni",
    "merdiven_derinlik": "Kuyu dibi merdiveninin derinliği",
    "tahrik_kasnak_kalinlik": "Tahrik kasnağının planda görünen eni",
    "makine_en": "Makine gövdesinin eni",
    "makine_boy": "Makine gövdesinin boyu",
    "makine_kasnak_boslugu": "Tahrik kasnağı ile makine gövdesi arası",
    "agirlik_baglanti_en": "Ağırlık halat bağlantısının eni",
    "agirlik_baglanti_boy": "Ağırlık halat bağlantısının boyu",
    "agirlik_baglanti_x": "Ağırlık halat bağlantısının duvar tarafı payı",
    "agirlik_baglanti_y": "Ağırlık halat bağlantısının kasnak tarafı payı",
    "kabin_baglanti_en": "Kabin halat bağlantısının eni",
    "kabin_baglanti_boy": "Kabin halat bağlantısının boyu",
    "kabin_baglanti_x": "Kabin halat bağlantısının kabin tarafı payı",
    "regulator_eni": "Hız regülatörü kasnağının eni",
    "regulator_govde_en": "Hız regülatörü gövdesinin eni",
    "regulator_govde_boy": "Hız regülatörü gövdesinin boyu",
    "kumanda_pano_en": "Kumanda panosunun eni",
    "kumanda_pano_derinlik": "Kumanda panosunun derinliği",
    "kumanda_pano_yukseklik": "Kumanda panosunun yüksekliği",
    "halat_delik_payi": "Halat deliğinde demetin çevresine pay",
    "acil_pano_en": "Acil kurtarma panosunun eni",
    "acil_pano_derinlik": "Acil kurtarma panosunun derinliği",
    "kabin_tavan_kalinlik": "Kabin tavanı kalınlığı",
    "kabin_taban_kalinlik": "Kabin tabanı kalınlığı",
    "sase_alt_derinlik": "Kabin döşemesinden şase altına",
    "paten_yukseklik": "Kabin ve ağırlık pateninin yüksekliği",
    "sase_ust_kiris": "Kabin şasesi üst kirişinin yüksekliği",
    "sase_alt_kiris": "Kabin şasesi alt kirişinin yüksekliği",
    "fren_blogu_yukseklik": "Fren bloğunun yüksekliği",
    "kabin_kasnak_derinlik": "Kabin döşemesinden kabin kasnağı merkezine",
    "alt_paten_payi": "Şasenin altından alt patenin merkezine ( + yukarı )",
    "kabin_ustu_kasnak_boslugu": "Kabin üstü kasnağının kirişten boşluğu",
    "kabin_tavani_kasnak_boslugu": "Çapraz kabin kasnağının kabin tavanından boşluğu",
    "sase_dikme_derinlik": "Kabin şasesi dikmesinin kesitteki eni",
    "etek_tahtasi": "Kabin eteği ( etek tahtası )",
    "tavan_kirisi": "Kuyu tavanı kiriş payı",
    "makine_tepe_boslugu": "Kuyu tavanından makinenin tepesine",
    "duvar_kirisi_tepe_boslugu": "Duvardan duvara kirişte kuyu tavanından makinenin tepesine",
    "makine_kapak_yukseklik": "Makine kapağının yüksekliği",
    "makine_kapak_en": "Makine kapağının eni",
    "makine_kapak_boy": "Makine kapağının boyu",
    "makine_sase_duvar": "Makine şasesinin duvardan açıklığı",
    "makine_sase_ray_payi": "Makine şasesinin raylardan taşması",
    "md_cerceve_pay": "Makine kaidesinin makine izinden taşması",
    "md_cerceve_ayak_plakasi": "Kaide ayak plakasının ölçüsü",
    "md_cerceve_ayak_plakasi_kalinlik": "Kaide ayak plakasının kalınlığı",
    "md_cati_kalinlik": "Makine dairesi çatı döşemesi kalınlığı",
    "md_saptirma_yukseklik": "Saptırma kasnağı merkezinin döşemeden yüksekliği",
    "ray_sase_icinde": "Rayların şase üstünün altında bittiği pay",
    "kabin_rayi_tepe": "Kabin rayının tavan payının altında bittiği pay",
    "kabin_baglanti_ust": "Kuyu tavanından kabin halat bağlantısının üstüne",
    "kabin_baglanti_alt": "Kuyu tavanından kabin halat bağlantısının altına",
    "agirlik_baglanti_yukseklik": "Ağırlık halat bağlantısının yüksekliği",
    "regulator_kasnak_merkez": "Kuyu tavanından regülatör kasnağı merkezine",
    "regulator_govde_ust": "Kuyu tavanından regülatör gövdesinin üstüne",
    "regulator_govde_alt": "Kuyu tavanından regülatör gövdesinin altına",
    "gergi_kasnak_merkez": "Kuyu tabanından gergi kasnağı merkezine",
    "gergi_kol_alt": "Kuyu tabanından gergi kolunun altına",
    "gergi_kol_yukseklik": "Gergi kolunun yüksekliği",
    "gergi_kol_ray": "Gergi kolunun kabin ray ekseninden payı",
    "gergi_kol_uc": "Gergi kolunun kasnaktan ötesi",
    "gergi_agirlik_alt": "Kuyu tabanından gergi ağırlığının altına",
    "gergi_agirlik_yukseklik": "Gergi ağırlığının yüksekliği",
    "gergi_agirlik_yakin": "Gergi ağırlığının kasnağa yakın ucu",
    "gergi_agirlik_uzak": "Gergi ağırlığının kasnağa uzak ucu",
    "gergi_agirlik_eni": "Gergi ağırlığının planda duvara dik eni",
    "agirlik_kasnak_ust": "Ağırlık kasnağı merkezinin üst kirişten derinliği",
    "agirlik_kiris": "Karşı ağırlık kirişinin kalınlığı",
    "konsol_ilk": "Kuyu tabanından ilk ray konsolunun üstüne",
    "konsol_yukseklik": "Ray konsolunun yüksekliği",
    "ray_boyu": "Ray boyu ( ekler arası )",
    "ek_lama_boyu": "Ray ek lamasının boyu",
    "kat_doseme_kalinlik": "Kat döşemesi kalınlığı",
    "kapi_ust_payi": "Kaba kapı boşluğunun kapıdan yüksekliği",
    "kaba_bosluk_yan_payi": "Kaba kapı boşluğunun kapının iki yanında genişliği",
    "kasa_ust": "Kat kapısı kasasının kapının üstündeki yüksekliği",
    "gosterge_en": "Kat göstergesinin eni",
    "gosterge_boy": "Kat göstergesinin yüksekliği",
    "gosterge_yukseklik": "Kat göstergesinin ortası:  kapının üstünden",
    "buton_kutu_en": "Kat butonu kutusunun eni",
    "buton_kutu_boy": "Kat butonu kutusunun yüksekliği",
    "buton_yukseklik": "Kat butonunun ortası:  döşemeden",
    "buton_kapi_payi": "Kat butonunun ortası:  kapının kenarından",
    "buton_yuva_en": "Kat butonu yuvasının eni ( duvarda )",
    "buton_yuva_boy": "Kat butonu yuvasının yüksekliği ( duvarda )",
    "esik_kalinlik": "Eşik kalınlığı",
}


#  REFERANS PROJENİN KABİNİ:  programın ofis standardı ofisin kendi kabinidir
#  ( yukarıda, LiftDesigner projeleri );  referans projenin örnekleri ( cizim/
#  girdi.ORNEK, ornekler/hesap_girdi ) kendi kabinleriyle çizilir.  Onun "Cabin
#  at Bottom / Top Floor" kesitlerinden ( 1/30 ):  şase alt kirişinin altı −480,
#  taban 20 + 100, fren bloğu platformun altında 350, kabin kasnağı merkezi −295
#  ( genişliği 92 );  planda yan pano 45, arka 33.  ŞASE ( 8 Eki, "Cabin Sits on
#  Buffer" görünüşünün vektörlerinden ):  alt kiriş −470 / −120 ( 350 ), altında
#  10'luk levha ve 140'lık paten ( −620 / −480 — merkezi şase altının 70
#  altında ), üst kiriş 2.610 / 2.810 ( 200 — hesabındaki UPN 200 ), üstünde
#  levha ve paten.  Hesabındaki "h 330 cm" kirişlerin dış yüzleri arasıdır;
#  program h'yi patenlerin merkezleri arası sayar ( TS EN 81-50 kuvvet kolu ).
REFERANS_PROJE_KABINI = {
    "sase_alt_derinlik": 480,
    "alt_paten_payi": -70,
    "paten_yukseklik": 140,
    "sase_ust_kiris": 200,
    "sase_alt_kiris": 350,
    "kabin_taban_kalinlik": 120,
    "fren_blogu_yukseklik": 350,
    "kabin_kasnak_derinlik": 295,
    "kabin_kasnak_genislik": 92,
    "kabin_pano_yan": 45,
    "kabin_pano_arka": 33,
    #  kapı boşluğu kapıdan 200 yüksek ( 2.100 / 2.300 )
    "kapi_ust_payi": 200,
}


#  SABİTLER SEKMESİNDEKİ BÖLÜMLER:  ( başlık , açıklama , anahtarlar ).  Her
#  sabit tam bir bölümdedir ( test ).  Makine ölçüleri TEK BİR makinenindir
#  ( referans projenin dişlisiz makinesi ):  başka makine kullanılıyorsa o
#  bölüm değiştirilir.
BOLUMLER = (
    (
        "RAY VE KONSOL",
        "kuyu planındaki konsollar, düşey kesitlerdeki ray ekleri ve uçları",
        (
            "konsol_kabin_en",
            "konsol_kabin_boy",
            "konsol_agirlik_en",
            "konsol_agirlik_boy",
            "konsol_civata_araligi",
            "konsol_civata_capi",
            "ara_kiris_en",
            "konsol_ilk",
            "konsol_yukseklik",
            "ray_boyu",
            "ek_lama_boyu",
            "ray_sase_icinde",
            "kabin_rayi_tepe",
        ),
    ),
    (
        "PATEN",
        "kabinde kaymalı paten ( makaralı kabin pateninin ölçüsü yok — seçilince çizim "
        "durur, karar 2 );  karşı ağırlıkta referans projenin makaralı pateni, aynı iz",
        ("paten_en", "paten_boy", "paten_yukseklik"),
    ),
    (
        "KABİN",
        "kabinin planı ve düşey ölçüleri — kabin imalatına bağlı, TS EN 81-20 sayısı değildir",
        (
            "kabin_pano_yan",
            "kabin_pano_arka",
            "sase_dikme",
            "sase_dikme_derinlik",
            "alt_paten_payi",
            "sase_ust_kiris",
            "sase_alt_kiris",
            "kabin_taban_kalinlik",
            "kabin_tavan_kalinlik",
            "sase_alt_derinlik",
            "fren_blogu_yukseklik",
            "etek_tahtasi",
        ),
    ),
    (
        "KABİN KASNAKLARI ( 2:1 )",
        "kabin altında döşemenin altında;  kabin üstünde şasenin üst "
        "kirişinin üstünde, arkadaki ağırlıkta kabin tavanında",
        (
            "kabin_kasnak_genislik",
            "kabin_kasnak_derinlik",
            "kabin_ustu_kasnak_boslugu",
            "kabin_tavani_kasnak_boslugu",
        ),
    ),
    (
        "KAPI VE KATLAR",
        "kat ve kabin kapısı, eşikler, kat döşemesi",
        (
            "kasa_yan",
            "kasa_derinlik",
            "kanat_kalinlik",
            "kanat_araligi",
            "kanat_esik_payi",
            "kanat_cebi_payi",
            "kabin_kapisi_kutu_en",
            "kabin_kapisi_kutu_boy",
            "esik_derinlik",
            "kabin_esik_derinlik",
            "esik_kalinlik",
            "kapi_ust_payi",
            "kaba_bosluk_yan_payi",
            "kasa_ust",
            "kat_doseme_kalinlik",
            "bina_duvari",
            "gosterge_en",
            "gosterge_boy",
            "gosterge_yukseklik",
            "buton_kutu_en",
            "buton_kutu_boy",
            "buton_yukseklik",
            "buton_kapi_payi",
            "buton_yuva_en",
            "buton_yuva_boy",
        ),
    ),
    ("KARŞI AĞIRLIK", "çerçeve ve kasnağı", ("agirlik_cerceve", "agirlik_kiris", "agirlik_kasnak_ust")),
    (
        "KUYU DİBİ",
        "tamponlar, merdiven, regülatör gergisi",
        (
            "tampon_capi",
            "tampon_taban",
            "merdiven_eni",
            "merdiven_derinlik",
            "gergi_kasnak_eni",
            "gergi_kasnak_merkez",
            "gergi_kol_alt",
            "gergi_kol_yukseklik",
            "gergi_kol_ray",
            "gergi_kol_uc",
            "gergi_agirlik_alt",
            "gergi_agirlik_yukseklik",
            "gergi_agirlik_yakin",
            "gergi_agirlik_uzak",
            "gergi_agirlik_eni",
        ),
    ),
    (
        "MAKİNE",
        "tek bir makinenin ölçüleri ( referans projenin dişlisiz makinesi ) — başka "
        "makinede buradan değiştirilir",
        (
            "makine_en",
            "makine_boy",
            "tahrik_kasnak_kalinlik",
            "makine_kasnak_boslugu",
            "makine_kapak_yukseklik",
            "makine_kapak_en",
            "makine_kapak_boy",
        ),
    ),
    (
        "KUYU ÜSTÜ ( makine dairesiz )",
        "makine şasesi, halat bağlantıları, regülatör, acil "
        "kurtarma panosu — düşey ölçüler kuyu tavanından aşağı",
        (
            "tavan_kirisi",
            "makine_tepe_boslugu",
            "duvar_kirisi_tepe_boslugu",
            "makine_sase_duvar",
            "makine_sase_ray_payi",
            "agirlik_baglanti_en",
            "agirlik_baglanti_boy",
            "agirlik_baglanti_x",
            "agirlik_baglanti_y",
            "agirlik_baglanti_yukseklik",
            "kabin_baglanti_en",
            "kabin_baglanti_boy",
            "kabin_baglanti_x",
            "kabin_baglanti_ust",
            "kabin_baglanti_alt",
            "regulator_eni",
            "regulator_govde_en",
            "regulator_govde_boy",
            "regulator_kasnak_merkez",
            "regulator_govde_ust",
            "regulator_govde_alt",
            "acil_pano_en",
            "acil_pano_derinlik",
        ),
    ),
    (
        "MAKİNE DAİRESİ",
        "kaide, halat delikleri, kumanda panosu, saptırma kasnağı",
        (
            "md_cerceve_pay",
            "md_cerceve_ayak_plakasi",
            "md_cerceve_ayak_plakasi_kalinlik",
            "md_cati_kalinlik",
            "md_saptirma_yukseklik",
            "halat_delik_payi",
            "kumanda_pano_en",
            "kumanda_pano_derinlik",
            "kumanda_pano_yukseklik",
        ),
    ),
)

#  SIFIR OLABİLENLER:  boşluklar ve paylar.  Öbürleri parçanın kendi ölçüsüdür;
#  sıfırı çizimi bozar ( ray boyu sıfırsa ray eklerinin kotları biter ).
SIFIR_OLABILIR = frozenset(
    (
        "ray_sase_icinde",
        "kabin_rayi_tepe",
        "kabin_ustu_kasnak_boslugu",
        "kabin_tavani_kasnak_boslugu",
        "kanat_esik_payi",
        "kanat_cebi_payi",
        "kapi_ust_payi",
        "esik_kalinlik",
        "bina_duvari",
        "gergi_kol_ray",
        "makine_kasnak_boslugu",
        "tavan_kirisi",
        "alt_paten_payi",
        "makine_tepe_boslugu",
        "duvar_kirisi_tepe_boslugu",
        "makine_sase_duvar",
        "makine_sase_ray_payi",
        "agirlik_baglanti_x",
        "agirlik_baglanti_y",
        "kabin_baglanti_x",
        "md_cerceve_pay",
        "halat_delik_payi",
    )
)

#  GEÇERLİ ARALIK ( hesabın Sabitler sekmesi ve köprü aynısını kullanır:
#  hesabın reddettiği değer çizime de geçmez ).  Kabinin düşey ölçülerinin
#  sınırları hesabın eski sınırlarıdır.
_ARALIK_OZEL = {
    "tavan_kirisi": (0, 5000),
    "sase_alt_derinlik": (1, 5000),
    "kabin_taban_kalinlik": (1, 1000),
    "kabin_tavan_kalinlik": (1, 1000),
    "paten_yukseklik": (1, 1000),
    "fren_blogu_yukseklik": (1, 2000),
    #  alt paten şasenin altından aşağıda da olabilir ( referans proje −70 )
    "alt_paten_payi": (-2000, 5000),
    "kabin_kasnak_derinlik": (1, 2000),
}


def aralik(anahtar):
    """( en az , en çok ) — sıfır yalnız boşluk ve paylarda."""
    return _ARALIK_OZEL.get(anahtar, (0 if anahtar in SIFIR_OLABILIR else 1, 20000))


#  Sabitler sekmesinde adı farklı olan ( hesabın eski adı, kayıtlı projeler
#  onu taşır ):  çizim adı → ofis adı.  Öbürlerinin adı aynıdır.
OFIS_ADI = {"tavan_kirisi": "tavan_payi"}


def ofis_adi(anahtar):
    return OFIS_ADI.get(anahtar, anahtar)


def sabitler(ozel=None):
    """Ofis çizim sabitleri + projeye özel ezmeler."""
    s = dict(SABIT)
    for k, v in (ozel or {}).items():
        if k in SABIT and v is not None:
            s[k] = v
    if izli.izlemede():
        #  Ölçü kaynağı çözümlenirken her sabit ofis standardındaki adıyla izlenir
        s = {k: izli.oz(v, ("ofis", ofis_adi(k))) for k, v in s.items()}
    kume = getattr(_KAYIT, "kume", None)
    return _Okunan(s, kume) if kume is not None else s


#  OKUNAN SABİTLER:  ölçü kaynağı çözümlemesi ( olcu_kaynagi ) bir çizimin
#  hangi ürün ölçülerini okuduğunu bilirse yalnız onları oynatır ( doksan
#  küsur sabitin hepsini değil ).  Kayıt iş parçacığına özeldir:  aynı anda
#  kurulan başka çizimlere dokunmaz.  Sabitlere yalnız sabitler() ile
#  erişilir ( SABIT'i doğrudan okuyan çizim kodu yok — test ).
_KAYIT = threading.local()


class _Okunan(dict):
    def __init__(self, d, kume):
        super().__init__(d)
        self._kume = kume

    def __getitem__(self, k):
        self._kume.add(k)
        return super().__getitem__(k)

    def get(self, k, v=None):
        self._kume.add(k)
        return super().get(k, v)


@contextlib.contextmanager
def okunanlar():
    """Blok içinde okunan sabitlerin kümesi."""
    eski, kume = getattr(_KAYIT, "kume", None), set()
    _KAYIT.kume = kume
    try:
        yield kume
    finally:
        _KAYIT.kume = eski
