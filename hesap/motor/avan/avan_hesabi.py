# -*- coding: utf-8 -*-
"""
ASANSÖR AVAN PROJE HESAPLARI
  MMO/697 (2. Baskı, Ocak 2020) s.18-21  ·  TS EN 81-20  ·  IEEE Std 80

  · 1-4 nolu asansör   ( 6 hesap bölümü )
  · makine dairesi aydınlatması
  · temel topraklama
  · özet
"""

import math
from motor.avan import tablolar
from temel import sayi_mi
from motor.ortak.adimlar import (
    Bolum,
    veri,
    hesap,
    metin,
    tr,
    trn,
    yuvarla,
    yukari_yuvarla,
    tavana_yuvarla,
    evet_mi,
    aralik_disi,
)


# ---------------------------------------------------------------- SABİTLER
#  A) Yönetmelik / standart sabitleri — değiştirilmez
SABIT_A = {
    "gn": 9.81,  # Yerçekimi ivmesi          MMO/697 s.18 — TS EN 81-20
    "tampon_katsayi": 4,  # F = 4·gn·(P+Q)            MMO/697 §2.3.3.1-2
    "k1_hizli": 2,  # V > 1,00 m/s              MMO/697 Çizelge-1
    "k1_orta": 3,  # 0,63 < V ≤ 1,00 m/s
    "k1_yavas": 5,  # 0,15 < V ≤ 0,63 m/s
    "motor_sabiti": 102,  # N = (1/η)·[(Q/2·V)/102]   MMO/697 §2.4
    "kirlenme_faktoru": 1.25,  # Aydınlatmada bakım faktörü d
    "E_makine_dairesi": 200,  # lüx     TS EN 81-20
    "E_kabin": 100,  # lüx     TS EN 81-20
    "E_kuyu": 50,  # lüx     TS EN 81-20
    "kuyu_ek_armatur": 2,  # Kuyu dibi + kuyu üstü
    "h_armatur": 1.0,  # Armatür–çalışma düzlemi arası yükseklik, m  ( kabin · kuyu )
    #  MAKİNE DAİRESİNDE ÇALIŞMA DÜZLEMİ DÖŞEMEDİR:  TS EN 81-20 m.5.2.1.4.2
    #  200 lüksü "döşeme seviyesinde" ister, armatür tavandadır ve net
    #  yükseklik en az 2,10 m'dir ( m.5.2.6.3.2.1 ).  Kabindeki 1,0 m'lik
    #  düzlem ( m.5.4.10.1:  döşemeden 1 m yukarıda 100 lüks ) buraya da
    #  uygulanıyordu:  k iki katına çıkıyor, η büyüyor, armatür sayısı
    #  %20-30 AZ çıkıyordu.
    "h_makine_dairesi": 2.10,  # Armatür–döşeme arası yükseklik, m
    "ray_dusumu": 0.20,  # I = Hk − 0,20, m
    "flexbil_sabiti": 3.0,  # Flexbil boyu = Hk/2 + 3, m
}

#  B) Ofis standardı — varsayılan; gerekirse değiştirilebilir.
#  ASKI ORANI (i) asansörün KENDİ ÖZELLİĞİDİR — kapasite ve hız gibi GİRİŞ
#  sayfasından asansör bazında girilir; buradaki değer yalnız boş bırakılan
#  kolon için yedektir.  Denge faktörü q uygulamada hep 0,50 olduğundan ofis
#  standardında durur, gerekirse asansör bazında ezilir.
SABIT_B_VARSAYILAN = {
    "i_palanga": 2,  # yedek — asıl giriş asansör bazındadır
    "q_denge": 0.50,  # Denge faktörü
    "n_ray": 2,  # Kabin kılavuz ray sayısı
    "gf": 1.5,  # Gezici kablo (flexbil) birim kütlesi, kg/m
    "Fmt": 150,  # Montör ağırlığı, kg
    "kabin_armatur_W": 5,  # LED spot
    "kabin_armatur_lm": 300,
    "kabin_ustu_armatur": 1,
    "kuyu_armatur_W": 40,  # Flüoresan
    #  Ofis armatür tablosu ( bkz. tables.ARMATUR_ISIK_AKISI ):  Flüoresan 40 W = 2100 lm.
    #  Bu değer MMO/697'de YOKTUR — kitapta aydınlatma bölümü yoktur.
    #  Burada eskiden kaynağı belirsiz bir "ofis teamülü" olarak 2600 lm duruyordu;
    #  pafta ØL satırına kaynak olarak yalnız "KABUL" yazdığı için tablodan
    #  sapıldığı GÖRÜNMÜYORDU.  2600 daha az armatür verir — yani emniyetsiz
    #  taraftır: saha ölçümünde TS EN 81-20'nin 50 lüksü tutmayabilir.  Varsayılan
    #  tabloya çekildi;  farklı bir armatür kullanılacaksa alan doldurulur ve pafta
    #  kaynağı "GİRİŞ — imalatçı verisi" olarak yazar ( bkz. _armatur_kaynagi ).
    "kuyu_armatur_lm": 2100,  # Flüoresan 40 W — ofis armatür tablosu
    "kuyu_Dmax": 7,  # Armatürler arası azami aralık, m (0 = kontrol kapalı)
    "priz_adedi": 3,
    "priz_gucu": 300,  # W
    "cosfi": 0.90,
    #  Motorun ELEKTRİK verimi — şebekeden çekilen güç = mil gücü / ηm.
    #  Mekanik sistem verimi η ( makine tipine bağlı, 0,85 / 0,50 ) ile
    #  KARIŞTIRILMAMALIDIR:  o motor GÜCÜNÜ belirler, bu ise o gücü çekmek
    #  için şebekeden akan AKIMI.  Kablo ve sigorta bu akıma göre seçilir.
    "motor_elektrik_verimi": 0.85,
    "UL": 50,  # İzin verilen temas gerilimi, V (TT sistem)
    "IDn": 0.30,  # Kaçak akım rölesi anma akımı, A
    "lc": 1.5,  # Çubuk topraklayıcı boyu, m
    "ayd_sutun": 2,  # TABLOLAR Tablo-2 sütunu (tavan .80 / duvar .50 / zemin .10)
}


#  Ofis standardı değerlerinin geçerlilik aralıkları.
#  Aralık dışında bir değer girilirse HESAP DURUR ve hangi alanın neden
#  kabul edilmediği söylenir ( bkz. girdi_hatalari ).  Varsayılana dönmek
#  kullanıcının yazmadığı bir sayıyla hesap yapmak demekti.
#  ARTIK OFİS SABİTİ DEĞİL — asansörün kendi girdisi olan, burada yalnız
#  YEDEK olarak duran alanlar.  Askı ( palanga ) oranı asansöre özeldir
#  ( GİRİŞ 53. satır ); SABİTLER'deki değer yalnız boş bırakılan kolon için
#  kullanılır, bu yüzden arayüzde "ofis standardı" diye gösterilmez.
SABIT_B_YEDEK = ("i_palanga",)

SABIT_B_ARALIK = {
    #  q = 1 iken N = ( 1 − q )·Q·V/… = 0 çıkıyor ve 2,2 kW motor "uygun"
    #  görünüyordu; q = 0 ise karşı ağırlık hiç dengelemiyor demektir.  İkisi de
    #  fiziksel değil.  Uygulama bandı 0,40 - 0,55; bu aralığın dışı UYARI,
    #  aşağıdaki sert sınırların dışı ise REDDEDİLİR.
    "i_palanga": (1, 4),
    "q_denge": (0.2, 0.8),
    "n_ray": (1, 8),
    "gf": (0, 50),
    "Fmt": (0, 1000),
    "kabin_armatur_W": (0.1, 1000),
    "kabin_armatur_lm": (1, 100000),
    "kabin_ustu_armatur": (0, 20),
    "kuyu_armatur_W": (0.1, 1000),
    "kuyu_armatur_lm": (1, 100000),
    "kuyu_Dmax": (0, 100),
    "priz_adedi": (0, 50),
    "priz_gucu": (0, 10000),
    "cosfi": (0.1, 1),
    "UL": (1, 1000),
    "IDn": (0.001, 10),
    "lc": (0.1, 50),
    "ayd_sutun": (1, 10),
    #  Aralığı yoktu:  ηm = 5 kabul ediliyor, motor akımı beşte birine
    #  iniyor, kablo ve sigorta küçük seçiliyordu.  Uygulamanın aynı sabitiyle
    #  aynı aralık ( motor/uygulama/uygulama_sabitleri.ARALIK ).
    "motor_elektrik_verimi": (0.1, 1),
}


# =====================================================================
#  C )  OFİS VARSAYILANLARI
#  Asansörden asansöre, projeden projeye DEĞİŞMEYEN değerler.  Program
#  bunları burada bir kez tutar;  asansör alanı boş bırakılırsa buradan gelir.
#
#  Bir asansörde farklı bir değer gerekiyorsa ( ör. daha ağır bir makine )
#  o asansörün kartından girilir; girilen değer buradakini ezer.
# =====================================================================
OFIS_VARSAYILAN = {
    # kesin sabitler — yönetmelik / malzeme fiziği
    "U": 380,  # Şebeke gerilimi (fazlar arası), V
    #  ------------------------------------------------------------------
    #  κ  —  BAKIRIN İLETKENLİĞİ  ( m/Ω·mm² )        2026-09-12
    #  ------------------------------------------------------------------
    #  56, bakırın 20 °C'DEKİ değeridir.  Kablo yük altında ısınır, direnci
    #  artar, iletkenliği düşer;  ε = 100·P·L/(κ·S·U²) bağıntısında κ paydada
    #  olduğu için 56 ile hesaplanan gerilim düşümü GERÇEKTEN KÜÇÜK çıkar —
    #  proje kâğıtta geçer, sahada sınırı aşabilir.  Yön EMNİYETSİZDİ.
    #
    #  TS HD 60364-5-52 EK-G  ( TSE'nin tercüme edip yayımladığı Türk
    #  standardı ) hesabın tabanını açıkça tanımlar:
    #      ρ1 = "20 °C'deki özdirencin 1,25 katı olarak alınan NORMAL ÇALIŞMA
    #            KOŞULLARINDAKİ iletkenin özdirenci"   —  bakır için
    #            0,0225 Ω·mm²/m   →   κ = 1 / 0,0225 = 44,4
    #
    #  Elektrik İç Tesisleri Yönetmeliği m.57 klasik formülü verir ve Türk
    #  pratiği 56 kullanır;  ikisi de savunulabilir, SIKI OLANI seçildi.
    #  EMO'nun kendi yayını ( EMO İzmir, Mayıs 2017, "Alçak Gerilim Elektrik
    #  Tesislerinde Gerilim Düşümü Hesapları" ) yönetmelik hükümlerinin
    #  standarda göre yeniden düzenlenmesini önerir.
    #
    #  ÖLÇÜLDÜ:  86 etkin avan senaryosunda 56 → 44,4 ε'yi ×1,26 büyütür ve
    #  İKİ projede karar döner ( ε 2,385 → 3,008 % ve 2,441 → 3,079 % ).
    #  Risk bandı:  56'da ε'si %2,38–3,00 arasında çıkanlar.
    #
    #  Ofis sabitidir — ekrandan 56'ya döndürülebilir ve paftada hangi
    #  değerin kullanıldığı kaynak sütununda yazar.
    "kappa": 44.4,  # Bakır, normal çalışma koşulları  ( ρ1 = 1,25·ρ20 )
    "eps_max": 3,  # İzin verilen gerilim düşümü, %
    # ofis malzeme standardı — asansör bazında
    "gr": 17.91,  # Kılavuz ray birim kütlesi, kg/m
    "Fmk": 350,  # Makine ağırlığı, kg
    "Fsh": 100,  # Makine sehpası ağırlığı, kg
    #  DENGE ZİNCİRİ BİRİM KÜTLESİ  ( kabinin 1 m hareketine düşen zincir )
    #  MMO/697 ( s.20 ) ve TS EN 81-20 ( m.5.2.1.8.5 ) P'ye "dengeleme
    #  halatları/zincirleri ( varsa )" katar ama İKİSİ DE SAYI VERMEZ.
    #  EN 81-20 m.5.5.6.1 zincirin amacını söyler:  askı halatlarının
    #  ağırlığını dengelemek.  Zincir halat ağırlığı kadar alınır ( λ = %100,
    #  uygulama projesinin kabulüyle aynı ) ve avan halatları bilmediği için
    #  ofisin varsayılan halat düzeni kullanılır:  7 × Ø6,5 mm ( 0,152 kg/m )
    #  × 2:1 askı  =  2,128  →  2,13 kg/m.  İKİ HANEYE YUVARLANIR:  arayüz
    #  varsayılanı kutuya yazar ve "2,128" belirsiz sayı kuralına takılıp
    #  bütün avan hesabını durduruyordu ( binlik ayraçlı 2128 ile karışır ).
    #  Ağır asansörde ( ör. 9 × Ø10 · 2:1 ≈ 6,1 kg/m ) asansör kartındaki
    #  "farklı değerler" bölümünden girilir.
    "zincir_birim_kutle": 2.13,
    "S1": 6,  # Kolon hattı kesiti, mm²
    "S2": 6,  # Makine besleme kesiti, mm²
    "L2": 3,  # Makine besleme uzunluğu, m
    "kablo_tipi": "NHXMH FE180",
    "L1_pay": 3.5,  # L1 = Hk + bu pay  ( pano ile kuyu arası )
    # ofis varsayılanı — projeye göre değişebilir
    "beta": 150,  # Toprak özgül direnci, Ω·m
    "cubuk_sayisi": 4,  # Çubuk topraklayıcı adedi
    "goz_araligi": 20,  # Temel topraklama karelaj gözü, m ( 20 × 20 )
    #  Motor koruma cihazı ( sigorta / şalter ) anma akımı = bu katsayı × In,
    #  sonra standart kademeye yuvarlanır.  1,25 ofisin kendi paftasını birebir
    #  verir:  11 kW → In 18,6 A → 23,2 A → "4 x 25".
    "sigorta_katsayisi": 1.25,
}

#  KAT YÜKSEKLİĞİ ve KAPI TİPİ burada DEĞİLDİR:  her projede değişirler,
#  bu yüzden ait oldukları yerde — trafik hesabı sekmesinde — girilirler.
#  ( v1.6'da ofis varsayılanı yapılmışlardı; v1.7'de geri alındı. )

#  Metin alanları — sayı denetimine girmez
OFIS_METIN = ("kablo_tipi",)

OFIS_ARALIK = {
    "U": (100, 1000),
    "kappa": (10, 100),
    "eps_max": (0.1, 20),
    "gr": (1, 200),
    "Fmk": (1, 5000),
    "Fsh": (0, 3000),
    "S1": (1, 400),
    "S2": (1, 400),
    "L2": (0.1, 500),
    "L1_pay": (0, 100),
    "zincir_birim_kutle": (0.1, 50),
    "beta": (1, 100000),
    "cubuk_sayisi": (0, 100),
    "goz_araligi": (1, 200),
    "sigorta_katsayisi": (1, 4),
}

#  Asansör kartından ezilebilen ofis varsayılanları ( "özel değer" bölümü )
OFIS_ASANSOR_ALANLARI = ("gr", "Fmk", "Fsh", "S1", "S2", "L2", "kablo_tipi", "zincir_birim_kutle")
#  Avan ortak panelinden gelen, boş bırakılırsa ofis varsayılanına düşenler
OFIS_ORTAK_ALANLARI = ("U", "kappa", "eps_max", "beta", "cubuk_sayisi")


def sabitler(ozel=None):
    """
    Yönetmelik sabitleri (A) + ofis standardı (B).
    `ozel` içindeki geçersiz değerler sözlüğe YAZILMAZ;  anahtarları
    "_reddedilen" listesinde döner ( uygulamanın sabitler()'i gibi ).
    hesapla() reddedilen bir değer varken hesap YAPMAZ ( bkz. girdi_hatalari ).

    KABUL EDİLEN ezmeler ayrıca "_ozel" listesinde tutulur:  paftada bir
    değerin tablodan mı yoksa kullanıcıdan mı geldiğini yazabilmek için
    ( bkz. _armatur_kaynagi ).  Aksi hâlde ØL satırı, değer ne olursa olsun
    "KABUL" diyordu ve tablodan sapıldığı paftada görünmüyordu.
    """
    s = dict(SABIT_A)
    s.update(SABIT_B_VARSAYILAN)
    s.update(OFIS_VARSAYILAN)
    reddedilen, kabul = [], []
    for k, v in (ozel or {}).items():
        if v is None or (k not in SABIT_B_VARSAYILAN and k not in OFIS_VARSAYILAN):
            continue
        if k in OFIS_METIN:  # metin alanı — boş değilse geçerli
            metin = str(v).strip()
            if metin:
                s[k] = metin
                kabul.append(k)
            continue
        alt, ust = SABIT_B_ARALIK.get(k) or OFIS_ARALIK.get(k) or (None, None)
        if not sayi_mi(v) or (alt is not None and not (alt <= v <= ust)):
            reddedilen.append(k)
            continue
        s[k] = v
        kabul.append(k)
    if "ayd_sutun" in s:
        s["ayd_sutun"] = int(round(s["ayd_sutun"]))
    s["_reddedilen"] = reddedilen
    s["_ozel"] = sorted(kabul)
    return s


#  ARMATÜR IŞIK AKISININ KAYNAĞI  —  paftada GÖRÜNMELİDİR.
#  Varsayılan ( W, lm ) çiftleri OFİS ARMATÜR TABLOSUNDAN gelir ( MMO/697'de
#  aydınlatma bölümü yoktur ).  Kullanıcı
#  gücü ya da ışık akısını elle girdiyse artık tablo değeri değildir; paftaya
#  bunu yazmak, imalatçı referansının belgeye girmesini de sağlar.
def _armatur_kaynagi(S, w_anahtar, lm_anahtar):
    ozel = set(S.get("_ozel") or ())
    if ozel & {w_anahtar, lm_anahtar}:
        return "KATALOG  ( marka-model paftada belirtilmelidir )"
    return "KABUL  ·  armatür tablosu"


#  ASANSÖR KARTINDA ELLE GİRİLEN DEĞERLERİN SINIRLARI
#  Denetimsizken  Q elle = 0  →  N = 0 kW  →  2,2 kW motor "uygun" çıkıyor;
#  Gk elle negatif olabiliyor; η = 10 girilince motor gereksiz küçülüyordu.
#  Sınır dışı bir değer hesabı DURDURUR — sessizce yanlış bir motor
#  seçilmesindense kullanıcıya hangi alanın imkânsız olduğu söylenir.
#
#  Ofis varsayılanı olan alanlar ( gr · S1 · q … ) da buradadır:  eskiden
#  aralık dışı değer varsayılanla DEĞİŞTİRİLİYOR ve hesap sürüyordu;  S1 = 0,5
#  yazılan projede 6 mm² ile hesaplanan pafta "UYGUN" diyebiliyordu.  Boş
#  bırakılan alan varsayılanı kullanır — yazılan sayı ya kullanılır ya da
#  hesap durur, üçüncü yol yoktur.
#
#  Sınırlar ofis alanlarında aralık tablolarından OKUNUR ( tek kaynak ):
#  ofis sekmesindeki S1 ile asansör kartındaki S1 aynı aralığa bağlıdır.
#  L1 ve Nsç'nin alt sınırı fiziksel değildir, yalnız sıfırı ve negatifi
#  dışarıda bırakır.
ASANSOR_SINIRLARI = (
    ("Q_elle", "Q elle — anma yükü", (50, 20000), "kg"),
    ("Gk_elle", "Gk elle — boş kabin kütlesi", (50, 20000), "kg"),
    ("eta", "η — makine verimi", (0.05, 1.0), "—"),
    ("i_palanga", "i — askı oranı", SABIT_B_ARALIK["i_palanga"], "—"),
    ("q_denge", "q — denge faktörü", SABIT_B_ARALIK["q_denge"], "—"),
    ("gr", "gr — ray birim kütlesi", OFIS_ARALIK["gr"], "kg/m"),
    ("Fmk", "Fmk — makine ağırlığı", OFIS_ARALIK["Fmk"], "kg"),
    ("Fsh", "Fsh — sehpa ağırlığı", OFIS_ARALIK["Fsh"], "kg"),
    ("zincir_birim_kutle", "mz — denge zinciri birim kütlesi", OFIS_ARALIK["zincir_birim_kutle"], "kg/m"),
    ("S1", "S1 — kolon hattı kesiti", OFIS_ARALIK["S1"], "mm²"),
    ("S2", "S2 — makine besleme kesiti", OFIS_ARALIK["S2"], "mm²"),
    ("L2", "L2 — makine besleme uzunluğu", OFIS_ARALIK["L2"], "m"),
    ("L1", "L1 — kolon hattı uzunluğu", (0.1, 500), "m"),
    ("Nsc", "Nsç — seçilen motor gücü", (0.1, 500), "kW"),
)

#  HESABA GİRMESİ ZORUNLU ALANLAR.  Üçüncü sütun: sıfır ya da negatif OLAMAZ mı?
#  ( Eskiden "eksik" ve "pozitif" listeleri AYRI tutuluyordu ve ikisi elle
#    eşlenmek zorundaydı;  tek tabloya alındı, ayrışamazlar. )
ZORUNLU_ALANLAR = (
    ("V", "Kabin hızı", True),
    ("eta", "Makine verimi", True),
    ("Hk", "Kuyu yüksekliği", True),
    ("kuyu_genisligi", "Kuyu genişliği", True),
    ("kabin_boyu", "Kabin boyu", True),
    ("kabin_genisligi", "Kabin genişliği", True),
    ("gr", "Kılavuz ray birim kütlesi", False),
    ("Fmk", "Makine ağırlığı", False),
    ("Fsh", "Makine sehpası ağırlığı", False),
    ("S1", "Kolon hattı kesiti", True),
    ("L1", "Kolon hattı uzunluğu", False),
    ("S2", "Makine besleme kesiti", True),
    ("L2", "Makine besleme uzunluğu", False),
    ("U", "Şebeke gerilimi", True),
    ("kappa", "İletken iletkenliği", True),
    ("eps_max", "İzin verilen gerilim düşümü", False),
)


def _girildi_mi(x):
    """Alan doldurulmuş mu?  Boş alan varsayılanı kullanır, dolu alan denetlenir."""
    return x not in (None, "")


def _gecersiz(deger, aralik):
    """Girilmiş değer kullanılamaz mı?  ( sayı değil ya da aralık dışı )"""
    alt, ust = aralik if aralik else (None, None)
    return not sayi_mi(deger) or (alt is not None and not (alt <= deger <= ust))


def _asansor_hatasi(no, a):
    """Asansör kartındaki sınır dışı değerler  —  hata metni ya da None.

    İLK hatada durmaz, HEPSİNİ söyler:  kullanıcı bir alanı düzeltip
    yeniden hesaplatınca sıradakiyle karşılaşmasın.
    """
    hatalar = [
        aralik_disi(ad, a.get(anahtar), *aralik, birim)
        for anahtar, ad, aralik, birim in ASANSOR_SINIRLARI
        if _girildi_mi(a.get(anahtar)) and _gecersiz(a.get(anahtar), aralik)
    ]
    if not hatalar:
        return None
    return (
        f"!!!   {no} NOLU ASANSÖR — girilen değer kullanılamıyor   ·   "
        + "   ·   ".join(hatalar)
        + "   ·   Değeri düzeltin ya da alanı boşaltın ( boş alan tablo / "
        "ofis değerini kullanır ).   !!!"
    )


def _zorunlu_hatasi(no, d):
    """Eksik ya da sıfır/negatif zorunlu alan var mı?  Hata metni ya da None."""
    eksik = [ad for anahtar, ad, _ in ZORUNLU_ALANLAR if not sayi_mi(d.get(anahtar))]
    gecersiz = [
        ad for anahtar, ad, poz in ZORUNLU_ALANLAR if poz and sayi_mi(d.get(anahtar)) and d.get(anahtar) <= 0
    ]
    if not (eksik or gecersiz):
        return None
    parcalar = []
    if eksik:
        parcalar.append("eksik : " + ", ".join(eksik))
    if gecersiz:
        parcalar.append("sıfır veya negatif olamaz : " + ", ".join(gecersiz))
    return f"!!!   {no} NOLU ASANSÖR — girdi tamamlanmadı   ·   " + "   ·   ".join(parcalar) + "   !!!"


#  LÜMEN YÖNTEMİ  —  kabin, kuyu ve makine dairesi aydınlatması AYNI hesaptır.
#  Üç yerde birebir yazılıydı;  biri değişse diğerleri sessizce eskide kalırdı.
#      k = a·b / ( h·( a + b ) )      bölge indeksi
#      T = E·a·b·d / η                gerekli toplam ışık akısı   ( η: TABLOLAR T2 )
#      Z = T / ØL                     hesaplanan armatür sayısı
def _aydinlatma(a_m, b_m, E, OL, S, hh=None):
    """
    a_m, b_m : METRE cinsinden ölçüler        E : asgari aydınlatma şiddeti, lüks
    OL       : bir armatürün ışık akısı, lm   hh : armatür–çalışma düzlemi, m
                                                   ( verilmezse h_armatur )

    Dönen:  (k, eta, T, Z)  —  η okunamazsa T ve Z None döner.
    """
    if hh is None:
        hh = S["h_armatur"]
    k = a_m * b_m / (hh * (a_m + b_m))
    eta = tablolar.ayd_verim(k, S["ayd_sutun"])
    isik = E * a_m * b_m * S["kirlenme_faktoru"] / eta if eta else None
    Z = isik / OL if sayi_mi(isik) else None
    return k, eta, isik, Z


#  PROJE GENELİ DEĞERLERİN ADLARI  —  reddedilen değerin metninde görünür.
#  Ofis sekmesi ile ortak paneldeki her sayısal alanın burada karşılığı
#  olmalıdır ( TEST 2 denetler );  yoksa kullanıcı "goz_araligi" gibi bir iç
#  adla karşılaşır.  Ekrandaki uzun etiketler motor/avan/avan_sabitleri.py ETIKET'te.
OFIS_ETIKET = {
    "i_palanga": ("i — askı oranı", "—"),
    "q_denge": ("q — denge faktörü", "—"),
    "n_ray": ("n — kabin kılavuz ray sayısı", "—"),
    "gf": ("gf — gezici kablo birim kütlesi", "kg/m"),
    "Fmt": ("Fmt — montör ağırlığı", "kg"),
    "kabin_armatur_W": ("kabin armatürü gücü", "W"),
    "kabin_armatur_lm": ("kabin armatürü ışık akısı", "lm"),
    "kabin_ustu_armatur": ("kabin üstü armatür adedi", "—"),
    "kuyu_armatur_W": ("kuyu armatürü gücü", "W"),
    "kuyu_armatur_lm": ("kuyu armatürü ışık akısı", "lm"),
    "kuyu_Dmax": ("kuyu armatürü azami aralığı", "m"),
    "priz_adedi": ("priz adedi", "—"),
    "priz_gucu": ("priz başına güç", "W"),
    "cosfi": ("cosφ — güç katsayısı", "—"),
    "motor_elektrik_verimi": ("ηm — motorun elektrik verimi", "—"),
    "UL": ("UL — izin verilen temas gerilimi", "V"),
    "IDn": ("IΔn — kaçak akım rölesi", "A"),
    "lc": ("lç — çubuk topraklayıcı boyu", "m"),
    "ayd_sutun": ("aydınlatma verimi sütunu", "—"),
    "U": ("U — şebeke gerilimi", "V"),
    "kappa": ("κ — iletkenlik", "m/Ω·mm²"),
    "eps_max": ("εmax — gerilim düşümü sınırı", "%"),
    "gr": ("gr — ray birim kütlesi", "kg/m"),
    "Fmk": ("Fmk — makine ağırlığı", "kg"),
    "Fsh": ("Fsh — sehpa ağırlığı", "kg"),
    "zincir_birim_kutle": ("mz — denge zinciri birim kütlesi", "kg/m"),
    "S1": ("S1 — kolon hattı kesiti", "mm²"),
    "S2": ("S2 — makine besleme kesiti", "mm²"),
    "L2": ("L2 — makine besleme uzunluğu", "m"),
    "L1_pay": ("L1 yatay güzergâh payı", "m"),
    "beta": ("β — toprak özgül direnci", "Ω·m"),
    "cubuk_sayisi": ("Is — çubuk topraklayıcı adedi", "—"),
    "goz_araligi": ("karelaj gözü — temel topraklama", "m"),
    "sigorta_katsayisi": ("motor sigortası kalkış katsayısı", "—"),
}


def _ofis_metni(anahtar, deger):
    """Proje geneli bir değerin red metni."""
    ad, birim = OFIS_ETIKET.get(anahtar, (anahtar, ""))
    alt, ust = SABIT_B_ARALIK.get(anahtar) or OFIS_ARALIK.get(anahtar) or (None, None)
    return aralik_disi(ad, deger, alt, ust, birim)


def girdi_hatalari(veriler, S=None):
    """PROJE GENELİ girdilerden KULLANILAMAYANLAR  —  metin listesi.

    Ofis standardı ( Sabitler sekmesi ) ve ortak panel ( U · κ · εmax · β ·
    Is · şerit boyu ).  Boş liste hesabın yapılabileceği anlamına gelir.
    Asansöre ait alanlar burada DEĞİL, asansörün kendi hesabında denetlenir
    ( bkz. _asansor_hatasi ):  bir asansörün hatası ötekileri durdurmaz.
    """
    ozel = veriler.get("sabitler") or {}
    S = S if S is not None else sabitler(ozel)
    hatalar = [_ofis_metni(k, ozel.get(k)) for k in S["_reddedilen"]]

    ortak = veriler.get("ortak") or {}
    for k in OFIS_ORTAK_ALANLARI:
        if _girildi_mi(ortak.get(k)) and _gecersiz(ortak.get(k), OFIS_ARALIK.get(k)):
            hatalar.append(_ofis_metni(k, ortak.get(k)))
    #  Şerit boyu boş bırakılırsa temel ölçülerinden TÜRETİLİR;  girilmişse
    #  pozitif olmalıdır ( sıfır ya da negatif boy türetmeye düşüyordu ).
    L = ortak.get("serit_L")
    if _girildi_mi(L) and not (sayi_mi(L) and L > 0):
        hatalar.append(
            f"L — topraklama şeridi boyu = {trn(L)} m  ( sıfırdan büyük olmalı "
            "ya da boş bırakılmalı — boşsa temel ölçülerinden türetilir )"
        )
    return hatalar


def _ofis_degeri(a, S, anahtar):
    """Asansör kartındaki değer, boşsa ofis varsayılanı  —  ( değer , kaynak ).

    Dolu alanın aralığı burada DENETLENMEZ:  hesapla_asansor girdiyi önce
    _asansor_hatasi'ndan geçirir, geçersiz bir değerle buraya gelinmez.
    """
    deger = (a or {}).get(anahtar)
    if anahtar in OFIS_METIN:
        deger = str(deger or "").strip()
    if _girildi_mi(deger):
        return deger, "GİRİŞ — asansör bazında"
    return S[anahtar], "KABUL"


def _ortak_degeri(ortak, S, anahtar):
    """Ortak paneldeki değer, boşsa ofis varsayılanı.

    Aralık hesapla()'da, hesaptan ÖNCE denetlenir ( bkz. girdi_hatalari ).
    """
    deger = (ortak or {}).get(anahtar)
    return deger if _girildi_mi(deger) else S[anahtar]


# =====================================================================
#  TEK ASANSÖRÜN AVAN HESABI  —  "n NOLU ASANSÖR" sayfası
# =====================================================================
def hesapla_asansor(a: dict, ortak: dict, S: dict, no: int = 1, md: dict | None = None) -> dict:
    """
    a     : asansör girdileri (GİRİŞ sayfası C..F kolonu)
    ortak : ortak girdiler (GİRİŞ sayfası 1. bölüm)
    S     : sabitler
    md    : makine dairesi aydınlatması bu asansörün tablosundansa { adet , W }
            ( hesapla() verir — adet hesaplanamamışsa None )

    Bölümler sırayla hesaplanır;  ara değerler ( h ) bir bölümden ötekine
    geçer ve sonunda özete girer.  Kullanılamayan girdi hesabı en başta
    durdurur:  { no, aktif: False, uyari }.
    """
    # ---------- elle girilen değerlerin sınırları  ( önce — hepsi birden )
    hata = _asansor_hatasi(no, a)
    if hata:
        return {"no": no, "aktif": False, "uyari": hata}
    h = _girdiler(a, ortak, S)
    h["md_ayd"] = md
    hata = _yuk_ve_kutle(h, no) or _motor_gucu(h, a, S, no)
    if hata:
        return {"no": no, "aktif": False, "uyari": hata}

    #  UYARILAR İKİYE AYRILIR:
    #    ikaz        bilgilendirici — uygunluğu ENGELLEMEZ
    #    engelleyici projeyi durduran — genel sonuca girer
    ikaz = []
    engelleyici = []
    bolumler = [_motor_bolumu(h, ikaz)]
    _kuvvetler(h, a, S)
    bolumler.append(_kuvvet_bolumu(h, S))
    bolumler.append(_kabin_aydinlatma_bolumu(h, S))
    bolumler.append(_kuyu_aydinlatma_bolumu(h, S))
    bolumler.append(_kurulu_guc_bolumu(h, S, no))
    _gerilim_dusumu(h, S)
    bolumler.append(_gerilim_dusumu_bolumu(h, S))
    _ek_denetimler(h, ikaz, engelleyici)
    return {
        "no": no,
        "aktif": True,
        "tanim": h["tanim"],
        "baslik": f"{no} NOLU ASANSÖR",
        #  Fiziksel tutarsızlıklar sessiz kalmamalı.  UYARILAR İKİYE AYRILIR:
        #    ikaz        bilgilendirici — uygunluğu engellemez
        #    engelleyici projeyi durdurur — genel sonuca ( tumu_uygun ) girer
        #  Kullanılamayan girdi burada YOKTUR:  o, hesabı en başta durdurur
        #  ( bkz. _asansor_hatasi ).
        "uyarilar": [f"⚠ {no} NOLU ASANSÖR: {x}" for x in (ikaz + engelleyici)],
        "engelleyici": [f"⚠ {no} NOLU ASANSÖR: {x}" for x in engelleyici],
        "bolumler": bolumler,
        "ozet": _ozet(h),
        "elektrik": _elektrik_projesi(h, S, no),
    }


def _elektrik_projesi(h, S, no):
    """ELEKTRİK PROJESİNİN DEĞERLERİ  —  tek hat şeması ve kuyu tesisatı
    ( cizim/elektrik ).  Çizim bunları basar, kendisi hesaplamaz:  armatür
    adetleri ( bölüm 3 · 4 ), motor gücü ve sigortası ( bölüm 1 · 5 ), devre
    sigortaları ( bölüm 5 — kurulu güç cetvelinin satırları ), kolon ve
    makine besleme hattının kesitleri ( bölüm 6 ), kaçak akım rölesi ( ofis
    standardı — topraklama hesabının IΔn'ı ).  Makine dairesinin olup
    olmadığı proje genelidir:  hesapla() yazar;  aydınlatması bu tablodansa
    devresi burada ( kurulu güç cetvelinin satırı ), değilse hesapla() onu
    besleyen tabloyu yazar."""
    v = {
        "tablo": tas_adi(no),
        "motor_kW": h["Nsc"],
        "motor_sigorta_A": h["sigorta_A"],
        #  Motorun şebekeden çektiği akım ( bölüm 5 — sigortası bundan seçilir );
        #  termiğin ayarı buna uygun olmalı ( Asansör Periyodik Kontrol EK-5 1.37 )
        "motor_akimi_A": h["I_motor"],
        "kuyu": {"adet": h["n_kuyu"], "W": S["kuyu_armatur_W"], "sigorta_A": SIGORTA_AYDINLATMA},
        #  Kabin ve kabin üstü cetvelde TEK devredir ( 3. satır )
        "kabin": {"adet": h["n_kabin"], "W": S["kabin_armatur_W"], "sigorta_A": SIGORTA_AYDINLATMA},
        "kabin_ustu": {"adet": S["kabin_ustu_armatur"], "W": S["kabin_armatur_W"]},
        "priz": {"adet": S["priz_adedi"], "W": S["priz_gucu"], "sigorta_A": SIGORTA_PRIZ},
        "kolon": {"S": h["S1"], "SPE": h["SPE1"], "kablo": h["kablo_tipi"]},
        "makine_besleme": {"S": h["S2"], "SPE": h["SPE2"]},
        "kacak_akim_A": S["IDn"],
    }
    md = h["md_ayd"]
    if md:
        v["makine_dairesi_ayd"] = {"adet": md.get("adet"), "W": md["W"], "sigorta_A": SIGORTA_AYDINLATMA}
    return v


def _girdiler(a, ortak, S):
    """Asansör kartının ve ortak panelin değerleri;  boş alan ofis / ortak
    varsayılanını alır ( kaynağıyla )."""
    h = {
        "tanim": a.get("tanim") or "",
        "P_kap": a.get("kapasite"),
        "Q_elle": a.get("Q_elle"),
        "V": a.get("V"),
        "eta": a.get("eta"),
        "Hk": a.get("Hk"),
        "kuyu_b": a.get("kuyu_genisligi"),
        "kabin_a": a.get("kabin_boyu"),
        "kabin_b": a.get("kabin_genisligi"),
        "Gk_elle": a.get("Gk_elle"),
        "makine_tipi": a.get("makine_tipi") or "",
        #  İki seçim, varsayılanları MMO/697'nin çözümlü örnekleri gibi YOK:
        #    denge zinciri                      →  P'ye zincir kütlesi eklenir
        #    karşı ağırlıkta güvenlik tertibatı →  karşı ağırlık rayında k1
        "zincir_var": evet_mi(a.get("denge_zinciri")),
        "ag_tertibat_var": evet_mi(a.get("agirlik_guvenlik_tertibati")),
        "Nsc_giris": a.get("Nsc"),
    }
    #  OFİS VARSAYILANLARI — asansörden asansöre değişmeyen malzeme değerleri.
    #  Asansör kartında bir değer varsa o kullanılır, yoksa ofis standardı.
    for anahtar, kaynak in (
        ("gr", "gr_kaynak"),
        ("Fmk", "Fmk_kaynak"),
        ("Fsh", "Fsh_kaynak"),
        ("S1", "S1_kaynak"),
        ("S2", "S2_kaynak"),
        ("L2", "L2_kaynak"),
        ("kablo_tipi", "kablo_kaynak"),
    ):
        h[anahtar], h[kaynak] = _ofis_degeri(a, S, anahtar)

    #  L1 — kolon hattı uzunluğu.  Boş bırakılırsa kuyu yüksekliği + YATAY
    #  GÜZERGÂH payı kullanılır:  hat kuyu boyunca çıkar, ama ana panodan kuyuya
    #  ve kuyudan asansör panosuna yatay yol ile uçlardaki bağlantı payı da
    #  vardır.  Paftaya "ofis payı" yazmak sayıyı keyfi gösteriyordu;  ne
    #  olduğu yazılır.  Plandan ölçülen değer farklıysa alan doldurulur.
    L1_giris = a.get("L1")
    if _girildi_mi(L1_giris):
        h["L1"], h["L1_kaynak"] = L1_giris, "GİRİŞ"
    elif sayi_mi(h["Hk"]):
        h["L1"] = h["Hk"] + S["L1_pay"]
        h["L1_kaynak"] = f"Hk + yatay güzergâh ( ana pano → kuyu → asansör panosu ) {tr(S['L1_pay'])} m"
    else:
        h["L1"], h["L1_kaynak"] = None, "GİRİŞ"

    #  Şebeke gerilimi, iletkenlik ve izin verilen gerilim düşümü ofis
    #  varsayılanıdır; ortak panelde boş bırakılırsa oradan gelir.
    h["U_sebeke"] = _ortak_degeri(ortak, S, "U")
    h["kappa"] = _ortak_degeri(ortak, S, "kappa")
    h["eps_max"] = _ortak_degeri(ortak, S, "eps_max")
    return h


def _yuk_ve_kutle(h, no):
    """Anma yükü ( Tablo-7 → elle ), zorunlu girdiler, boş kabin kütlesi
    ( Tablo-11 → elle ).  Hata metni ya da None."""
    P_kap, Q_elle = h["P_kap"], h["Q_elle"]
    h["Q0"] = tablolar.TABLO_7.get(P_kap) if sayi_mi(P_kap) else None
    Q = h["Q"] = Q_elle if sayi_mi(Q_elle) else h["Q0"]
    if not sayi_mi(Q):
        return (
            "!!!   BU ASANSÖR TANIMLANMAMIŞ   —   hesaplar boştur   !!!"
            if not sayi_mi(P_kap)
            else "!!!   KAPASİTE TABLO-7 DIŞI   —   'Anma yükü — elle' alanını doldurun   !!!"
        )

    # ---------- zorunlu girdi denetimi
    hata = _zorunlu_hatasi(
        no,
        {
            "V": h["V"],
            "eta": h["eta"],
            "Hk": h["Hk"],
            "kuyu_genisligi": h["kuyu_b"],
            "kabin_boyu": h["kabin_a"],
            "kabin_genisligi": h["kabin_b"],
            **{k: h[k] for k in ("gr", "Fmk", "Fsh", "S1", "L1", "S2", "L2")},
            "U": h["U_sebeke"],
            "kappa": h["kappa"],
            "eps_max": h["eps_max"],
        },
    )
    if hata:
        return hata

    # ---------- Gk  (Tablo-11 → elle)
    #  Tablo-11 yalnız 450 - 2500 kg arasını kapsar.  Dışına çıkıldığında
    #  tablo SESSİZCE uç değere sabitleniyordu:  Q = 5000 kg için de
    #  Gk = 1900 kg kullanılıyor, kuvvet hesapları olduğundan küçük çıkıyordu.
    #  Artık bu durumda 'Gk elle' zorunludur.
    T11_ALT, T11_UST = tablolar.TABLO_11[0][0], tablolar.TABLO_11[-1][0]
    if not sayi_mi(h["Gk_elle"]) and not (T11_ALT <= Q <= T11_UST):
        return (
            f"!!!   {no} NOLU ASANSÖR — anma yükü {trn(Q, 0)} kg, MMO/697 "
            f"Tablo-11'in kapsamı DIŞINDA ( {trn(T11_ALT, 0)} - "
            f"{trn(T11_UST, 0)} kg )   ·   boş kabin kütlesi tablodan "
            "türetilemez, 'Gk elle' alanına imalatçı değerini girin.   !!!"
        )
    h["Gk0"] = tablolar.tablo11_Gk(Q)
    h["Gk"] = h["Gk_elle"] if sayi_mi(h["Gk_elle"]) else h["Gk0"]
    return None


# =========================================================
# 1 -  MOTOR GÜCÜ HESABI            (MMO/697 s.21)
# =========================================================
def _motor_gucu(h, a, S, no):
    """Verim, hesaplanan ve seçilen motor gücü.  Hata metni ya da None."""
    eta, Q, V = h["eta"], h["Q"], h["V"]
    #  Askı ( palanga ) oranı asansörün kendi özelliğidir; boş bırakılırsa
    #  SABİTLER B'deki yedek değer kullanılır.  Denge faktörü ofis
    #  standardındadır, gerekirse asansör bazında ezilir.
    h["i_pal"], h["i_kaynak"] = _ofis_degeri(a, S, "i_palanga")
    h["q"], h["q_kaynak"] = _ofis_degeri(a, S, "q_denge")
    q = h["q"]
    #  PALANGALI SİSTEMDE VERİM 0,10 DÜŞÜK ALINIR  ( MMO/697 §2.4, örnek §4.4 ).
    #  Girilen η kitabın η'sıdır — makine verimi, askı kaybı HARİÇ ( bkz.
    #  tablolar.PALANGA_VERIM_DUSUSU ).  Uygulama projesinin köprüsü TOPLAM
    #  sistem verimi geçirir ve bunu bayrakla söyler:  o yolda düşüş yoktur.
    h["eta_toplam"] = bool(a.get(tablolar.ETA_TOPLAM_ANAHTARI))
    palanga_dususu = h["palanga_dususu"] = (
        sayi_mi(eta) and not h["eta_toplam"] and tablolar.palangali_mi(h["i_pal"])
    )
    #  Çıkarma kayan noktada gürültü bırakır ( 0,51 − 0,10 = 0,41000000000000003 ):
    #  η en çok üç ondalıkla girilir, altı haneye yuvarlamak yalnız gürültüyü siler.
    eta_p = h["eta_p"] = yuvarla(eta - tablolar.PALANGA_VERIM_DUSUSU, 6) if palanga_dususu else eta
    #  η′ ≤ 0 FİZİKSEL DEĞİLDİR ( η = 0,08 · 2:1 → η′ = −0,02 ):  paftaya
    #  negatif verim basılır, N = …/(102·η′) eksi çıkar ve sonuç "motoru
    #  büyütün" diye yanlış teşhis koyar.  Girilen değer kullanılamıyorsa hesap
    #  durur — varsayılana dönülmez.
    if not (sayi_mi(eta_p) and eta_p > 0):
        return (
            f"!!!   {no} NOLU ASANSÖR — makine verimi η = {tr(eta)}, palangalı "
            f"sistemde MMO/697 §2.4 gereği {tr(tablolar.PALANGA_VERIM_DUSUSU)} düşük "
            f"alınınca η′ = {tr(eta_p)}   ·   verim sıfır ya da negatif olamaz.  "
            "İmalatçının makine verimini girin.   !!!"
            if palanga_dususu
            else f"!!!   {no} NOLU ASANSÖR — makine verimi η = {tr(eta)}   ·   "
            "verim sıfır ya da negatif olamaz.  İmalatçının makine "
            "verimini girin.   !!!"
        )
    #  AĞIR ÇALIŞMA YÖNÜ.  Karşı ağırlık q·Q kadarını dengeler:
    #      dolu kabin YUKARI  →  dengesiz yük = ( 1 − q )·Q
    #      boş  kabin AŞAĞI   →  dengesiz yük =        q ·Q   ( karşı ağırlık ağır )
    #  Motor İKİSİNİN BÜYÜĞÜNE göre seçilir.  MMO/697 s.21 formülü Q/2 ile
    #  çalışır, yani q = 0,50 kabulüdür ve orada iki yön EŞİTTİR — bu genelleme
    #  kitabın formülüyle birebir aynı sonucu verir.  Fark yalnız q > 0,50 girildiğinde
    #  çıkar:  program eskiden HAFİF yönü hesaplıyor ve motoru olduğundan küçük
    #  seçiyordu ( q = 0,55 · 800 kg · 1 m/s · 2:1'de 5,5 kW yerine 7,5 kW gerekir ).
    dengesiz = max(1 - q, q)
    N_hes = h["N_hes"] = dengesiz * Q * V / (S["motor_sabiti"] * eta_p)

    #  Nsç — SEÇİLEN motor gücü.  Elle girilmemişse hesaplanan güçten büyük
    #  ilk STANDART anma gücü seçilir ( IEC 60072 kademeleri ).  Böylece
    #  "hesap 13,33 kW diyor ama 11 kW yazılmış" durumu oluşmaz.
    if _girildi_mi(h["Nsc_giris"]):
        Nsc, h["Nsc_kaynak"] = h["Nsc_giris"], "GİRİŞ — elle seçildi"
    else:
        Nsc = tablolar.motor_sec(N_hes)
        h["Nsc_kaynak"] = "otomatik — standart kademe ( IEC 60072 )"
    h["Nsc"] = Nsc
    if not sayi_mi(Nsc) or Nsc <= 0:
        return (
            f"!!!   {no} NOLU ASANSÖR — motor gücü belirlenemedi   ·   "
            "hesaplanan güç bulunamadığı için standart kademe "
            "seçilemedi; 'Nsç' alanını elle doldurun   !!!"
        )
    #  Tolerans motor_sec ile ORTAKTIR ( bkz. tables.MOTOR_TOLERANS ):  seçim
    #  ile kontrol ayrı eşik kullanırsa pafta kendi seçtiği motoru reddeder.
    h["motor_uygun"] = sayi_mi(N_hes) and sayi_mi(Nsc) and Nsc >= N_hes - tablolar.MOTOR_TOLERANS
    return None


def _motor_bolumu(h, ikaz):
    Q, V, q, eta, eta_p = h["Q"], h["V"], h["q"], h["eta"], h["eta_p"]
    makine_tipi, i_pal = h["makine_tipi"], h["i_pal"]
    b1 = Bolum("1 -  MOTOR GÜCÜ HESABI", "MMO / 697  —  s.21", kimlik="avan_motor_gucu")
    b1["adimlar"] = [
        veri("Q", "Anma yükü", Q, "kg", "GİRİŞ", 0),
        veri("V", "Kabin hızı", V, "m/s", "GİRİŞ"),
        veri("q", "Denge faktörü ( karşı ağırlığın dengelediği oran )", q, "—", h["q_kaynak"]),
        veri("", "Makine tipi", makine_tipi or "—", "", "GİRİŞ" if makine_tipi else "belirtilmedi"),
        veri(
            "i",
            f"Askı ( palanga ) oranı   —   {tablolar.aski_orani_metni(i_pal)}",
            i_pal,
            "—",
            h["i_kaynak"],
            0,
        ),
        veri(
            "η",
            (
                "Toplam sistem verimi  ( askı / palanga kaybı DÂHİL )"
                if h["eta_toplam"]
                else "Makine verimi  ( askı / palanga kaybı HARİÇ )"
            ),
            eta,
            "—",
            f"GİRİŞ  ( {makine_tipi} )" if makine_tipi else "GİRİŞ",
        ),
    ]
    _e = "η′" if h["palanga_dususu"] else "η"
    if h["palanga_dususu"]:
        b1["adimlar"].append(
            hesap(
                f"η′   =   η − {tr(tablolar.PALANGA_VERIM_DUSUSU)}",
                f"=   {tr(eta)} − {tr(tablolar.PALANGA_VERIM_DUSUSU)}",
                eta_p,
                "—",
                "palangalı sistem  ·  MMO/697 §2.4",
            )
        )
    b1["adimlar"] += [
        hesap(
            (
                f"N   =   ( 1 − q ) · Q · V   /   ( 102 · {_e} )"
                if (1 - q) >= q
                else f"N   =   q · Q · V   /   ( 102 · {_e} )        ( boş kabin aşağı — ağır yön )"
            ),
            (
                f"=   ( 1 − {tr(q)} ) · {trn(Q, 0)} · {tr(V)}   /   ( 102 · {tr(eta_p)} )"
                if (1 - q) >= q
                else f"=   {tr(q)} · {trn(Q, 0)} · {tr(V)}   /   ( 102 · {tr(eta_p)} )"
            ),
            h["N_hes"],
            "kW",
            "hesaplanan",
        ),
        veri("Nsç", "SEÇİLEN motor gücü", h["Nsc"], "kW", h["Nsc_kaynak"]),
    ]
    #  q uygulama bandı — sert sınırlar SABIT_B_ARALIK'ta ( 0,20 - 0,80 );
    #  burası pratikteki bandın dışını "bilerek mi" diye sorar.
    Q_BANT_ALT, Q_BANT_UST = 0.40, 0.55
    if sayi_mi(q) and not (Q_BANT_ALT <= q <= Q_BANT_UST):
        ikaz.append(
            f"q — denge faktörü {tr(q)} olarak kullanıldı; uygulamada "
            f"{tr(Q_BANT_ALT)} - {tr(Q_BANT_UST)} bandındadır. "
            "Karşı ağırlık dengelemesi bu değerde ise gerekçesi paftaya yazılmalıdır"
        )
    b1["aciklamalar"] = [tablolar.VERIM_NOTU]
    b1["notlar"] = [] if h["eta_toplam"] else [tablolar.MAKINE_VERIM_NOTU]
    mmo_eta = tablolar.makine_verimi(makine_tipi)
    if mmo_eta is not None and sayi_mi(eta) and abs(eta - mmo_eta) > 1e-9:
        b1["notlar"] = b1["notlar"] + [
            f"η, {makine_tipi} makine için ofis kabulü olan {tr(mmo_eta)} "
            f"değerinden farklı girilmiştir ( {tr(eta)} ). Kaynağı paftada "
            "belirtilmelidir."
        ]
    b1["sonuc"] = {
        "baslik": "KONTROL      Nsç  ≥  N",
        "metin": "UYGUN" if h["motor_uygun"] else "UYGUN DEĞİL — motoru büyütün",
        "uygun": bool(h["motor_uygun"]),
    }
    return b1


# =========================================================
# 2 -  KUVVET HESAPLARI             (MMO/697 s.18-20 / TS EN 81-20)
# =========================================================
#  Kuvvetler 10 N'un üst katına yuvarlanır.  Satırın işlemi yuvarlanmamış
#  sonucu verir;  aradaki farkın nereden geldiği kaynak kolonunda yazılı
#  olmazsa paftayı yeniden hesaplayan okur sonucu bulamaz.
_ON_N = "10 N'a yukarı yuvarlanır"

#  Fp — MMO/697 s.20 tanımı:  "bir kılavuz rayda bulunan tüm konsolların
#  kuvvetiyle itme ( betonun çekilmesinin veya binanın normal oturması
#  nedeniyle )".  Halat ya da kompanzasyon kuvveti DEĞİLDİR — not eskiden
#  öyle yazıyordu.  Kitap "seyir yüksekliği 40 m'yi geçmeyen durumlar için
#  Fp ihmal edilebilir" der;  burada SEYİR yerine kılavuz ray uzunluğu
#  ( Lr = Hk − 0,20 ) karşılaştırılır — Lr seyirden büyük olduğu için not
#  daha ERKEN çıkar, yani emniyetli taraftadır.  Karşılaştırılan büyüklük
#  notun içinde açıkça yazılır.
_FP_NOT = (
    "Fp — kılavuz ray konsollarının, betonun çekilmesi ya da binanın "
    "oturması nedeniyle uyguladığı itme kuvveti ( MMO/697 s.20 ). "
    "Kitap, SEYİR YÜKSEKLİĞİ 40 m'yi geçmiyorsa Fp'nin ihmal "
    "edilebileceğini söyler; program ölçüt olarak kılavuz ray "
    "uzunluğunu ( Lr = Hk − 0,20 ) kullanır — seyirden büyük olduğu "
    "için emniyetli taraftadır."
)


def _kuvvetler(h, a, S):
    Gk, Q, q, V, Hk = h["Gk"], h["Q"], h["q"], h["V"], h["Hk"]
    gn = S["gn"]
    Gf = S["gf"] * (Hk / 2 + S["flexbil_sabiti"])  # gezici kablo kütlesi
    #  DENGE ZİNCİRİ P'YE GİRER  ( MMO/697 s.20 · TS EN 81-20 m.5.2.1.8.5 ).
    #  Eskiden avanda zincir hiç yoktu:  zincirli yüksek binada tampon altı
    #  kuvvetleri uygulama projesinden %17-23 DÜŞÜK çıkıyordu.  Kabin en üstteyken
    #  altında asılı en uzun zincir kuyu yüksekliğiyle sınırlıdır ( emniyetli ).
    mz, mz_kaynak = _ofis_degeri(a, S, "zincir_birim_kutle")
    if mz_kaynak == "KABUL" and "zincir_birim_kutle" not in (S.get("_ozel") or ()):
        mz_kaynak = "KABUL  ·  zincir = halat ağırlığı ( λ = %100 ) · 7 × Ø6,5 · 2:1"
    Gz = mz * Hk if h["zincir_var"] else 0.0  # denge zinciri kütlesi
    P_kut = Gk + Gf + Gz  # kabin tarafı toplam kütle
    Ga = P_kut + q * Q  # karşı ağırlık kütlesi
    k1 = S["k1_hizli"] if V > 1 else (S["k1_orta"] if V > 0.63 else S["k1_yavas"])
    n_ray = S["n_ray"]
    Lr = Hk - S["ray_dusumu"]  # kılavuz ray uzunluğu
    Mg = Lr * h["gr"]  # bir ray hattının kütlesi
    #  KARŞI AĞIRLIK RAYI  —  MMO/697 s.20:  "kılavuz rayı üzerinde güvenlik
    #  tertibatı etki etmemesinde k1 = 0";  kitabın iki çözümlü örneği ( s.55 ·
    #  s.56 ) Pk'yı "karşı ağırlıkta güvenlik tertibatı olmadığından" hesaplamaz.
    #  Eskiden tertibat HER ZAMAN varmış gibi k1 kullanılıyordu ( 10 kata varan
    #  fazla kuvvet ).  Tertibat yoksa rayın kendi ağırlığı kalır.
    k1_ag = k1 if h["ag_tertibat_var"] else 0
    h.update(
        gn=gn,
        Gf=Gf,
        mz=mz,
        mz_kaynak=mz_kaynak,
        Gz=Gz,
        P_kut=P_kut,
        Ga=Ga,
        k1=k1,
        n_ray=n_ray,
        Lr=Lr,
        Mg=Mg,
        P1=tavana_yuvarla(S["tampon_katsayi"] * gn * (P_kut + Q), 10),
        P2=tavana_yuvarla(S["tampon_katsayi"] * gn * Ga, 10),
        PR=tavana_yuvarla(k1 * gn * (P_kut + Q) / n_ray + Mg * gn, 10),
        PK=tavana_yuvarla(k1_ag * gn * Ga / n_ray + Mg * gn, 10),
        Fs=tavana_yuvarla(gn * (h["Fmk"] + h["Fsh"] + S["Fmt"] + P_kut + Q + Ga), 10),
    )


def _kuvvet_bolumu(h, S):
    b2 = Bolum("2 -  KUVVET HESAPLARI", "MMO / 697  s.18-20   /   TS EN 81-20", kimlik="avan_kuvvetler")
    b2["adimlar"] = _kutle_adimlari(h, S) + _kuvvet_adimlari(h, S)
    b2["aciklamalar"] = [
        "PR ve PK, MMO/697 §2.3.3 formülündeki  Mg · gn  ray kütlesi terimini içerir "
        "( kitabın §4.3 örnek hesabı bu terimi ihmal etmiştir ).",
        "Karşı ağırlıkta paraşüt ( fren ) bulunması hâlinde PK dikkate alınır.",
    ]
    Lr = h["Lr"]
    if sayi_mi(Lr) and Lr > 40:
        b2["notlar"] = [
            f"Kılavuz ray uzunluğu 40 m'yi aşıyor ( Lr = {tr(Lr)} m ) — "
            "PR ve PK'ya Fp terimi EKLENMEMİŞTİR; uygulama projesinde "
            "konsol adedi ve klips kuvvetiyle ayrıca hesaplanmalıdır. " + _FP_NOT
        ]
    else:
        b2["aciklamalar"].append(_FP_NOT)
    return b2


def _kutle_adimlari(h, S):
    """Bölüm 2'nin ORTAK BÜYÜKLÜKLER satırları."""
    gn, Gk, Gf, Gz, P_kut, Q, q, Hk = h["gn"], h["Gk"], h["Gf"], h["Gz"], h["P_kut"], h["Q"], h["q"], h["Hk"]
    mz, Lr, gr = h["mz"], h["Lr"], h["gr"]
    if h["zincir_var"]:
        kabin_tarafi = [
            veri("mz", "Denge zinciri birim kütlesi", mz, "kg/m", h["mz_kaynak"]),
            hesap(
                "Gz   =   mz · Hk",
                f"=   {tr(mz)}  ·  {tr(Hk)}",
                Gz,
                "kg",
                "zincir kütlesi  ·  MMO/697 s.20 · EN 81-20 m.5.2.1.8.5",
            ),
            hesap(
                "P    =   Gk  +  Gf  +  Gz",
                f"=   {trn(Gk, 0)}  +  {tr(Gf)}  +  {tr(Gz)}",
                P_kut,
                "kg",
                "kabin tarafı toplam kütle",
            ),
        ]
    else:
        kabin_tarafi = [
            hesap(
                "P    =   Gk  +  Gf",
                f"=   {trn(Gk, 0)}  +  {tr(Gf)}",
                P_kut,
                "kg",
                "kabin tarafı toplam kütle",
            )
        ]
    return [
        metin("ORTAK BÜYÜKLÜKLER"),
        veri("gn", "Yerçekimi ivmesi", gn, "m/s²", "fiziksel sabit"),
        veri(
            "Gk", "Boş kabin kütlesi", Gk, "kg", "GİRİŞ" if sayi_mi(h["Gk_elle"]) else tablolar.GK_KAYNAGI, 0
        ),
        veri("gf", "Gezici kablo ( flexbil ) birim kütlesi", S["gf"], "kg/m", "KABUL"),
        hesap(
            "Gf   =   gf · ( Hk / 2  +  3 )",
            f"=   {tr(S['gf'])}  ·  ( {tr(Hk)} / 2  +  3 )",
            Gf,
            "kg",
            "gezici kablo kütlesi",
        ),
        veri("", "Denge zinciri", "Var" if h["zincir_var"] else "Yok", "", "GİRİŞ"),
        *kabin_tarafi,
        veri("Q", "Anma yükü", Q, "kg", "GİRİŞ", 0),
        veri("q", "Denge faktörü", q, "—", h["q_kaynak"]),
        hesap(
            "Ga  =   P  +  q · Q",
            f"=   {tr(P_kut)}  +  {tr(q)} · {trn(Q, 0)}",
            h["Ga"],
            "kg",
            "karşı ağırlık kütlesi",
        ),
        veri(
            "k1",
            "Darbe faktörü ( V > 1 → 2 / V > 0,63 → 3 / V ≤ 0,63 → 5 )",
            h["k1"],
            "—",
            "KABUL  ·  MMO/697 Çiz-1",
            0,
        ),
        veri("n", "Kabin kılavuz ray sayısı", h["n_ray"], "adet", "KABUL", 0),
        veri("gr", "1 m kılavuz rayın kütlesi", gr, "kg/m", h["gr_kaynak"]),
        veri("Lr", "Kılavuz ray uzunluğu ( Hk − 0,20 )", Lr, "m", "KABUL  ·  ray payı"),
        hesap("Mg  =   Lr · gr", f"=   {tr(Lr)}  ·  {tr(gr)}", h["Mg"], "kg", "bir ray hattının kütlesi"),
    ]


def _kuvvet_adimlari(h, S):
    """Bölüm 2'nin A - E kuvvet satırları."""
    gn, P_kut, Q, Ga, k1, n_ray, Mg = h["gn"], h["P_kut"], h["Q"], h["Ga"], h["k1"], h["n_ray"], h["Mg"]
    if h["ag_tertibat_var"]:
        pk = hesap(
            "PK  =   k1 · gn · Ga / n   +   Mg · gn",
            f"=   {trn(k1, 0)} · {tr(gn)} · {tr(Ga)} / {trn(n_ray, 0)}   +   {tr(Mg)} · {tr(gn)}",
            h["PK"],
            "N",
            _ON_N,
            0,
        )
    else:
        pk = hesap(
            "PK  =   Mg · gn        ( k1 = 0 )",
            f"=   {tr(Mg)} · {tr(gn)}",
            h["PK"],
            "N",
            "güvenlik tertibatı etki etmiyor  ·  MMO/697 s.20  ·  " + _ON_N,
            0,
        )
    return [
        metin("A -  KUYU ALT BOŞLUĞU TABANINA GELEN KUVVET  ( kabin tamponu altı )"),
        hesap(
            "P1  =   4 · gn · ( P  +  Q )",
            f"=   4  ·  {tr(gn)}  ·  ( {tr(P_kut)}  +  {trn(Q, 0)} )",
            h["P1"],
            "N",
            _ON_N,
            0,
        ),
        metin("B -  KARŞI AĞIRLIK TAMPONU ALTINDAKİ ZEMİNE GELEN KUVVET"),
        hesap(
            "P2  =   4 · gn · ( P  +  q · Q )   =   4 · gn · Ga",
            f"=   4  ·  {tr(gn)}  ·  {tr(Ga)}",
            h["P2"],
            "N",
            _ON_N,
            0,
        ),
        metin("C -  KABİN KILAVUZ RAYLARINA GELEN DÜŞEY KUVVET"),
        hesap(
            "PR  =   k1 · gn · ( P  +  Q ) / n   +   Mg · gn",
            f"=   {trn(k1, 0)} · {tr(gn)} · ( {tr(P_kut)} + {trn(Q, 0)} ) / {trn(n_ray, 0)}"
            f"   +   {tr(Mg)} · {tr(gn)}",
            h["PR"],
            "N",
            _ON_N,
            0,
        ),
        metin("D -  KARŞI AĞIRLIK KILAVUZ RAYLARINA GELEN DÜŞEY KUVVET"),
        veri("", "Karşı ağırlıkta güvenlik tertibatı", "Var" if h["ag_tertibat_var"] else "Yok", "", "GİRİŞ"),
        pk,
        metin("E -  KUYU ÜSTÜ BETONUNA ETKİ EDEN KUVVET"),
        hesap(
            "Fs  =   gn · ( Fmk  +  Fsh  +  Fmt  +  P  +  Q  +  Ga )",
            f"=   {tr(gn)} · ( {trn(h['Fmk'], 0)} + {trn(h['Fsh'], 0)} + {trn(S['Fmt'], 0)} + "
            f"{tr(P_kut)} + {trn(Q, 0)} + {tr(Ga)} )",
            h["Fs"],
            "N",
            _ON_N,
            0,
        ),
    ]


# =========================================================
# 3 -  KABİN AYDINLATMA HESABI      (TS EN 81-20)
# 4 -  KUYU AYDINLATMA HESABI       (TS EN 81-20)
# =========================================================
def _aydinlatma_adimlari(a_m, b_m, E, OL, k, eta, T, Z, S, armatur_kaynagi):
    """Lümen yönteminin satırları ( kabin ve kuyu aynı ):  ölçüler satırları
    çağıran yazar;  burası h'den Z'ye."""
    hh, d = S["h_armatur"], S["kirlenme_faktoru"]
    return [
        veri("h", "Armatür ile çalışma düzlemi arasındaki yükseklik", hh, "m", "KABUL"),
        hesap(
            "k   =   a · b   /   ( h · ( a + b ) )",
            f"=   {tr(a_m)} · {tr(b_m)}   /   ( {tr(hh)} · ( {tr(a_m)} + {tr(b_m)} ) )",
            k,
            "—",
            "bölge indeksi",
            4,
        ),
        veri("η", "Oda aydınlatma verimi", eta, "—", "KABUL  ·  aydınlatma verimi tablosu"),
        veri("E", "Asgari aydınlatma şiddeti", E, "lüx", "KABUL", 0),
        veri("d", "Kirlenme ( bakım ) faktörü", d, "—", "KABUL"),
        hesap(
            "T   =   E · a · b · d   /   η",
            f"=   {trn(E, 0)} · {tr(a_m)} · {tr(b_m)} · {tr(d)}   /   {tr(eta)}",
            T,
            "lm",
            "gerekli toplam ışık akısı",
        ),
        veri("ØL", "Bir armatürün ışık akısı", OL, "lm", armatur_kaynagi, 0),
        hesap(
            "Z   =   T   /   ØL", f"=   {tr(T)}   /   {trn(OL, 0)}", Z, "adet", "hesaplanan armatür sayısı"
        ),
    ]


def _kabin_aydinlatma_bolumu(h, S):
    ka, kb = h["kabin_a"] / 1000, h["kabin_b"] / 1000
    E, OL = S["E_kabin"], S["kabin_armatur_lm"]
    k, eta, T, Z = _aydinlatma(ka, kb, E, OL, S)
    n_kabin = int(yukari_yuvarla(Z, 0)) if sayi_mi(Z) else None
    h.update(ka=ka, kb=kb, k_kabin=k, eta_kabin=eta, T_kabin=T, Z_kabin=Z, n_kabin=n_kabin)

    b3 = Bolum("3 -  KABİN AYDINLATMA HESABI", "TS EN 81-20", kimlik="kabin_aydinlatma")
    b3["adimlar"] = [
        veri("a", "Kabin boyu", ka, "m", "GİRİŞ"),
        veri("b", "Kabin genişliği", kb, "m", "GİRİŞ"),
        *_aydinlatma_adimlari(
            ka, kb, E, OL, k, eta, T, Z, S, _armatur_kaynagi(S, "kabin_armatur_W", "kabin_armatur_lm")
        ),
        veri("n", "SEÇİLEN armatür sayısı  ( Z yukarı yuvarlanır )", n_kabin, "adet", "", 0),
    ]
    b3["sonuc"] = {
        "baslik": "SONUÇ",
        "metin": f"{n_kabin} adet {trn(S['kabin_armatur_W'], 0)} W armatür kullanılacaktır.",
        "uygun": True,
    }
    return b3


def _kuyu_aydinlatma_bolumu(h, S):
    Hk = h["Hk"]
    qa, qb = Hk, h["kuyu_b"] / 1000
    E, OL = S["E_kuyu"], S["kuyu_armatur_lm"]
    k, eta, T, Z = _aydinlatma(qa, qb, E, OL, S)
    n1 = int(yukari_yuvarla(Z, 0)) + S["kuyu_ek_armatur"] if sayi_mi(Z) else None
    Dmax = S["kuyu_Dmax"]
    aralikli = sayi_mi(Dmax) and Dmax > 0
    n2 = int(yukari_yuvarla((Hk - 1) / Dmax, 0)) + 1 if aralikli else 0
    n_kuyu = int(max(n1 or 0, n2 or 0)) if sayi_mi(n1) else None
    h.update(qa=qa, qb=qb, k_kuyu=k, eta_kuyu=eta, T_kuyu=T, Z_kuyu=Z, n1_kuyu=n1, n2_kuyu=n2, n_kuyu=n_kuyu)

    b4 = Bolum("4 -  KUYU AYDINLATMA HESABI", "TS EN 81-20", kimlik="kuyu_aydinlatma")
    b4["adimlar"] = [
        veri("a", "Kuyu yüksekliği ( kuyu boyu )", qa, "m", "GİRİŞ"),
        veri("b", "Kuyu genişliği", qb, "m", "GİRİŞ"),
        *_aydinlatma_adimlari(
            qa, qb, E, OL, k, eta, T, Z, S, _armatur_kaynagi(S, "kuyu_armatur_W", "kuyu_armatur_lm")
        ),
        veri("n1", "Işık akısından  =  ROUNDUP( Z ) + 2   ( kuyu dibi + üstü )", n1, "adet", "KABUL", 0),
        veri("Dmax", "Armatürler arası azami aralık", Dmax, "m", "KABUL", 0),
        hesap(
            "n2  =   ROUNDUP( ( Hk − 1 ) / Dmax )  +  1",
            f"=   ROUNDUP( ( {tr(Hk)} − 1 ) / {tr(Dmax)} )  +  1"
            if aralikli
            else "—   ( aralık kontrolü kapalı )",
            n2,
            "adet",
            "geometrik asgari adet",
            0,
        ),
        veri("n", "SEÇİLEN armatür sayısı  =  MAX ( n1 ; n2 )", n_kuyu, "adet", "", 0),
    ]
    b4["sonuc"] = {
        "baslik": "SONUÇ",
        "metin": f"{n_kuyu} adet {trn(S['kuyu_armatur_W'], 0)} W armatür kullanılacaktır.",
        "uygun": True,
    }
    return b4


# =========================================================
# 5 -  KURULU GÜÇ CETVELİ                        ( TAS )
# =========================================================
#  İKİ AYRI GÜÇ VARDIR VE KARIŞTIRILMAMALIDIR.
#
#  KURULU GÜÇ — cetvel.  Tanım gereği tüketicilerin ANMA ( ETİKET )
#  güçlerinin toplamıdır ( Elektrik İç Tesisleri Proje Hazırlama
#  Yönetmeliği m.5-19 ).  Motorun anma gücü MİL gücüdür ( TS EN 60034-1
#  m.5.5.3 ):  11 kW'lık motor cetvele 11 kW yazılır.
#
#  HATTAN ÇEKİLEN GÜÇ — bölüm 6.  Motor şebekeden mil gücünden fazlasını
#  çeker:  Pşeb = Nsç / ηm.  Kolon hattının akımı ve gerilim düşümü bu
#  güçle hesaplanır;  mil gücüyle hesaplanınca akım %18 düşük çıkıyor,
#  kesit olduğundan küçük seçilebiliyordu.
#
#  Bir süre ikisi tek sayıydı:  akım doğru çıksın diye cetvele Pşeb
#  yazılıyor, asansörün kurulu gücü de %18 büyük bildiriliyordu.
#
#  AYDINLATMA VE PRİZ DEVRELERİNİN SİGORTALARI ( A ) — cetvelin sigorta
#  sütununda sabit yazan değerler.  Elektrik projesinin tek hat şeması da
#  aynılarını basar ( _elektrik_projesi ):  cetvel ile şema ayrışmasın.
SIGORTA_AYDINLATMA = 10
SIGORTA_PRIZ = 16


def tas_adi(no):
    """Asansörün tablosunun adı ( kurulu güç cetveli ve tek hat şeması )."""
    return f"TAS{no}"


def tablo_adi_metni(no):
    """Kurulu güç cetvelinin kaynak satırı."""
    return f"tablo adı :  {tas_adi(no)}"


def _kurulu_guc_bolumu(h, S, no):
    Nsc, n_kuyu, n_kabin, U_sebeke = h["Nsc"], h["n_kuyu"], h["n_kabin"], h["U_sebeke"]
    eta_m = S["motor_elektrik_verimi"]
    g_motor = Nsc * 1000  # anma ( etiket · mil ) gücü
    g_motor_seb = (g_motor / eta_m) if (sayi_mi(eta_m) and 0 < eta_m <= 1) else g_motor
    g_kuyu = n_kuyu * S["kuyu_armatur_W"]
    g_kabin = (n_kabin + S["kabin_ustu_armatur"]) * S["kabin_armatur_W"]
    g_priz = S["priz_adedi"] * S["priz_gucu"]
    #  Makine dairesi aydınlatması yalnız onu besleyen tablonun cetvelinde
    #  ( bkz. hesapla );  armatür adedi makine dairesi aydınlatma hesabından
    md = h["md_ayd"] or {}
    n_md = md.get("adet")
    g_md = n_md * md["W"] if sayi_mi(n_md) else 0
    P_kurulu = g_motor + g_kuyu + g_kabin + g_md + g_priz

    #  MOTOR KORUMA CİHAZI  —  her güçte aynı sabit metin ( "4 x 25" ) değil,
    #  motor anma akımından seçilir:
    #  In = P2 / ( √3 · U · cosφ ),  kademe = katsayı · In üstündeki ilk
    #  standart değer.  Ofisin 11 kW örneğinde sonuç yine "4 x 25" çıkar.
    #  ŞEBEKEDEN ÇEKİLEN AKIM.  Motorun MİL gücü değil, şebekeden çektiği
    #  güç akar:  Pşeb = P2 / ηm.  Program bir süre ηm'yi atlıyordu ve akımı
    #  %18 DÜŞÜK gösteriyordu — kablo ve sigorta olduğundan küçük seçiliyordu.
    I_motor = (
        g_motor_seb / (math.sqrt(3) * U_sebeke * S["cosfi"])
        if all(sayi_mi(x) and x > 0 for x in (U_sebeke, S["cosfi"]))
        else None
    )
    sigorta_A = tablolar.sigorta_sec(I_motor, S["sigorta_katsayisi"])
    motor_sigorta = f"4 x {trn(sigorta_A, 0)}" if sigorta_A else "uygulama projesinde"
    h.update(
        eta_m=eta_m,
        g_motor=g_motor,
        g_motor_seb=g_motor_seb,
        g_kuyu=g_kuyu,
        g_kabin=g_kabin,
        g_priz=g_priz,
        g_md=g_md,
        P_kurulu=P_kurulu,
        #  Kolon hattı motoru, aydınlatmayı ve prizi birlikte besler.
        P_hat=g_motor_seb + g_kuyu + g_kabin + g_md + g_priz,
        I_motor=I_motor,
        sigorta_A=sigorta_A,
        motor_sigorta=motor_sigorta,
    )

    b5 = Bolum("5 -  KURULU GÜÇ CETVELİ", tablo_adi_metni(no), kimlik="kurulu_guc")
    b5["aciklamalar"] = [
        "Kurulu güç, tüketicilerin anma ( etiket ) güçlerinin toplamıdır "
        "( Elektrik İç Tesisleri Proje Hazırlama Yönetmeliği m.5-19 ).  Motorun "
        "anma gücü mil gücüdür ( TS EN 60034-1 m.5.5.3 ).  Kolon hattının akımı "
        "ve gerilim düşümü motorun şebekeden çektiği güçle hesaplanır ( bölüm 6 ).",
        tablolar.SIGORTA_NOTU,
    ]
    b5["cetvel"] = [
        {
            "lin": 1,
            "sorti": f"MOTOR          ( Nsç = {tr(Nsc)} kW )",
            "guc": g_motor,
            "birim": "W",
            "sigorta": motor_sigorta,
        },
        {
            "lin": 2,
            "sorti": f"KUYU AYDINLATMASI          ( {n_kuyu} X {trn(S['kuyu_armatur_W'], 0)} W )",
            "guc": g_kuyu,
            "birim": "W",
            "sigorta": str(SIGORTA_AYDINLATMA),
        },
        {
            "lin": 3,
            "sorti": (
                f"KABİN + KABİN ÜSTÜ AYD.     ( {n_kabin} X {trn(S['kabin_armatur_W'], 0)} W"
                f"  +  {trn(S['kabin_ustu_armatur'], 0)} X {trn(S['kabin_armatur_W'], 0)} W )"
            ),
            "guc": g_kabin,
            "birim": "W",
            "sigorta": str(SIGORTA_AYDINLATMA),
        },
    ]
    if sayi_mi(n_md):
        b5["cetvel"].append(
            {
                "lin": 4,
                "sorti": f"MAKİNE DAİRESİ AYD.          ( {n_md} X {trn(md['W'], 0)} W )",
                "guc": g_md,
                "birim": "W",
                "sigorta": str(SIGORTA_AYDINLATMA),
            }
        )
    b5["cetvel"].append(
        {
            "lin": len(b5["cetvel"]) + 1,
            "sorti": f"TOPLAM PRİZ          ( {trn(S['priz_adedi'], 0)} X {trn(S['priz_gucu'], 0)} W )",
            "guc": g_priz,
            "birim": "W",
            "sigorta": str(SIGORTA_PRIZ),
        }
    )
    b5["sonuc"] = {"baslik": "ASANSÖRÜN KURULU GÜCÜ", "metin": f"{trn(P_kurulu, 0)} W", "uygun": True}
    return b5


# =========================================================
# 6 -  GERİLİM DÜŞÜMÜ VE KESİT KONTROLÜ
# =========================================================
def _gerilim_dusumu(h, S):
    P_hat, U_sebeke, kappa, S1, S2 = h["P_hat"], h["U_sebeke"], h["kappa"], h["S1"], h["S2"]
    cosfi = S["cosfi"]
    #  ε BAĞINTISI ( 100·P·L / (κ·S·U²) ) HATTAN AKAN AKTİF GÜÇTEN türetilir:
    #  iki hatta da motorun şebekeden çektiği güç akar, kurulu güç değil.
    eps1 = (
        (100 * P_hat * h["L1"] / (kappa * S1 * U_sebeke**2))
        if all(sayi_mi(x) and x > 0 for x in (kappa, S1, U_sebeke))
        else None
    )
    P_motor_W = h["g_motor_seb"]
    eps2 = (
        (100 * P_motor_W * h["L2"] / (kappa * S2 * U_sebeke**2))
        if all(sayi_mi(x) and x > 0 for x in (kappa, S2, U_sebeke))
        else None
    )
    eps = (eps1 + eps2) if all(sayi_mi(x) for x in (eps1, eps2)) else None
    I_hat = (
        (P_hat / (math.sqrt(3) * U_sebeke * cosfi))
        if all(sayi_mi(x) and x > 0 for x in (U_sebeke, cosfi))
        else None
    )
    #  KESİT TABLODA YOKSA:  Iz kesitle birlikte arttığı için, kesitten küçük
    #  en büyük tablo satırı GÜVENLİ ALT SINIRDIR.  Eskiden Iz = None dönüyor,
    #  pafta 150 mm² gibi standart bir kesitte bile "UYGUN DEĞİLDİR — kesiti
    #  büyütün" diyordu;  kesiti büyütmek sonucu iyileştirmiyordu.
    Iz, Iz_kesin = tablolar.kablo_iz_sinir(S1)

    #  MAKİNE BESLEME HATTININ ( S2 ) AKIM KONTROLÜ
    #  Paftadaki "I ≤ Iz" kontrolü KOLON HATTINA ( S1 ) aittir ve öyle
    #  olmalıdır: o hat motoru, aydınlatmayı ve prizi birlikte taşır.  Ama makine
    #  besleme hattı hiç denetlenmiyordu — yalnız gerilim düşümüne ( ε2 )
    #  giriyordu ve ε2 kısa bir hatta çok ince kesitte bile küçük çıkar.
    #  Sonuç: 37 kW motor + S2 = 1,5 mm² ( I2 = 62 A, kablo 17,5 A )
    #  birleşimi "uygundur" görünüyordu.  Artık bölüm sonucuna girer
    #  ( bkz. aşağıda "MAKİNE BESLEME HATTI" ).
    Iz2, Iz2_kesin = tablolar.kablo_iz_sinir(S2)
    I2 = h["I_motor"]
    #  GRUP SİGORTASI MAKİNE BESLEME KABLOSUNU KORUMALI.  I2 ≤ Iz2 kablonun
    #  motor akımını taşıdığını söyler;  aşırı akımda kabloyu önündeki sigorta
    #  korur ve sigorta kablonun sınırını aşamaz ( tablolar.sigorta_siniri:
    #  EK-5 1.31.13, 6 mm² üstünde Iz ).  Kural son devrelerin kablosunda vardı
    #  ( cizim/elektrik.devre_kesiti ), motor devresinde yoktu:  4 mm² kabloya
    #  4 x 40 A, 2,5 mm²'ye 4 x 32 A sigorta "uygundur" çıkıyordu ( 23 Eki
    #  bağımsız denetim ).
    In_max2, In_max2_kaynak = tablolar.sigorta_siniri(S2)
    sigorta2_kontrol = sayi_mi(h["sigorta_A"]) and sayi_mi(In_max2)

    #  ------------------------------------------------------------------
    #  KORUMA İLETKENİ ( PE ) KESİTİ
    #  ------------------------------------------------------------------
    #  Elektrik Tesislerinde Topraklamalar Yönetmeliği m.9-e1/ii · Çizelge-8.
    #  KORUMA İLETKENİ, TOPRAKLAMA İLETKENİ DEĞİLDİR:  birincisi besleme
    #  kablosunun içindeki damardır ve kesiti faz kesitinden türer;  ikincisi
    #  ana baradan toprak elektroduna gider ve kendi kuralı vardır ( bakırda
    #  16 mm² ).  Program topraklama bölümünde elektrodun DİRENCİNİ hesaplar,
    #  iletkenin kesitini değil.  Bu satırlar bölüm 6'dadır çünkü hesaplanan
    #  şey bir KABLO DAMARININ KESİTİDİR ve S1 · S2 · kablo tipi buradadır.
    #
    #  m.9-e1/iv ( ortak PE, en büyük ana iletkene göre ) UYGULANMAZ:  o kural
    #  TEK bir PE'nin birçok devreye ORTAK hizmet ettiği durum içindir.  Kolon
    #  hattı ile makine beslemesi ayrı kablolardır, her birinin kendi PE damarı
    #  vardır;  ardışıktırlar, ortak değil.
    SPE1, SPE1_ham, SPE1_yuv = tablolar.koruma_iletkeni_kesiti(S1)
    SPE2, SPE2_ham, SPE2_yuv = tablolar.koruma_iletkeni_kesiti(S2)
    h.update(
        cosfi=cosfi,
        P_motor_W=P_motor_W,
        eps1=eps1,
        eps2=eps2,
        eps=eps,
        eps_uygun=sayi_mi(eps) and sayi_mi(h["eps_max"]) and eps <= h["eps_max"],
        I_hat=I_hat,
        Iz=Iz,
        Iz_kesin=Iz_kesin,
        akim_uygun=sayi_mi(I_hat) and sayi_mi(Iz) and I_hat <= Iz,
        I2=I2,
        Iz2=Iz2,
        Iz2_kesin=Iz2_kesin,
        akim2_uygun=sayi_mi(I2) and sayi_mi(Iz2) and I2 <= Iz2,
        In_max2=In_max2,
        In_max2_kaynak=In_max2_kaynak,
        sigorta2_kontrol=sigorta2_kontrol,
        sigorta2_uygun=sigorta2_kontrol and h["sigorta_A"] <= In_max2 + 1e-9,
        SPE1=SPE1,
        SPE1_kaynak=_pe_kaynagi(S1, SPE1_ham, SPE1_yuv),
        SPE2=SPE2,
        SPE2_kaynak=_pe_kaynagi(S2, SPE2_ham, SPE2_yuv),
    )


def _pe_kaynagi(kesit, ham, yuvarlandi):
    """Koruma iletkeni kesitinin Çizelge-8 kuralı ( kaynak kolonu )."""
    if ham is None:
        return "kesit okunamadı"
    kural = "S ≤ 16 → S" if kesit <= 16 else ("16 < S ≤ 35 → 16" if kesit <= 35 else "S > 35 → S/2")
    return kural + (f"  ·  {tr(ham)} bir üst standart kesite yuvarlandı" if yuvarlandi else "")


def _gerilim_dusumu_bolumu(h, S):
    b6 = Bolum(
        "6 -  GERİLİM DÜŞÜMÜ VE KESİT KONTROLÜ", "Elektrik İç Tesisleri Yönetmeliği", kimlik="gerilim_dusumu"
    )
    b6["aciklamalar"] = [
        "ε %  =  100 · P · L  /  ( κ · S · U² )          I  =  P  /  ( √3 · U · cosφ )",
        "Kolon hattı motoru, aydınlatmayı ve prizi birlikte besler; makine besleme "
        "hattı yalnız motoru besler.",
        "Her iki hatta da motorun ŞEBEKEDEN ÇEKTİĞİ güç ( Pşeb = Pm / ηm ) akar; "
        "Nsç motorun mil gücüdür ve hattı o değil, ondan büyük olan Pşeb yükler.  "
        "Bu yüzden P1 kurulu güçten ( bölüm 5 ) büyüktür — kurulu güç tanım gereği "
        "etiket güçlerinin toplamıdır.",
        "SPE  —  koruma iletkeni, besleme kablosunun bakır damarı kabul edilmiştir "
        "( Çizelge-8 ancak PE ile ana iletken aynı malzemedense geçerlidir ). "
        "Kablo dışında çekilen bir PE hiçbir şekilde 2,5 mm²'den ( mekanik korumalı ) "
        "ya da 4 mm²'den ( korumasız ) küçük olamaz  —  m.9-e1/iii.",
    ]
    b6["notlar"] = [
        "Aydınlatma ve priz devrelerinde izin verilen gerilim düşümü %1,5'tir; bu devrelerin "
        "uç noktalara kadar düşümü uygulama projesinde kontrol edilecektir.",
    ]
    b6["adimlar"] = _gerilim_dusumu_adimlari(h) + _akim_adimlari(h)
    b6["sonuc"] = _gerilim_dusumu_sonucu(h)
    return b6


def _gerilim_dusumu_adimlari(h):
    """Bölüm 6:  güçler ve iki hattın gerilim düşümü."""
    U, kappa, g_motor, g_motor_seb = h["U_sebeke"], h["kappa"], h["g_motor"], h["g_motor_seb"]
    P_hat, P_motor_W, L1, S1, L2, S2 = h["P_hat"], h["P_motor_W"], h["L1"], h["S1"], h["L2"], h["S2"]
    if abs(kappa - 44.4) < 0.05:
        kappa_kaynagi = "TS HD 60364-5-52 EK-G  ·  ρ1 = 1,25 × ρ20  ( normal çalışma )"
    elif abs(kappa - 56) < 0.05:
        kappa_kaynagi = "20 °C değeri  —  işletme sıcaklığında ε daha büyüktür"
    else:
        kappa_kaynagi = "GİRİŞ"
    return [
        veri("U", "Şebeke gerilimi ( fazlar arası )", U, "V", "GİRİŞ", 0),
        veri("cosφ", "Güç katsayısı", h["cosfi"], "—", "KABUL"),
        veri("κ", "İletken iletkenliği", kappa, "m/Ω·mm²", kappa_kaynagi, 1),
        veri("Pm", "Makine ( motor ) anma gücü  —  mil gücü", g_motor, "W", "GİRİŞ  ( Nsç )", 0),
        veri("ηm", "Motorun elektrik verimi", h["eta_m"], "—", "KABUL"),
        hesap(
            "Pşeb  =   Pm  /  ηm",
            f"=   {trn(g_motor, 0)}  /  {tr(h['eta_m'])}",
            g_motor_seb,
            "W",
            "motorun şebekeden çektiği güç",
            0,
        ),
        hesap(
            "P1  =   Pşeb  +  aydınlatma  +  priz",
            f"=   {trn(g_motor_seb, 0)}  +  {trn(h['g_kuyu'] + h['g_kabin'] + h['g_md'], 0)}  +  {trn(h['g_priz'], 0)}",
            P_hat,
            "W",
            "kolon hattından çekilen güç",
            0,
        ),
        veri("L1", "Kolon hattı uzunluğu", L1, "m", h["L1_kaynak"]),
        veri("S1", "Kolon hattı kesiti", S1, "mm²", h["S1_kaynak"]),
        hesap(
            "ε1  =   100 · P1 · L1   /   ( κ · S1 · U² )",
            f"=   100 · {trn(P_hat, 0)} · {tr(L1)}   /   ( {trn(kappa, 1)} · {tr(S1)} · {trn(U, 0)}² )",
            h["eps1"],
            "%",
            "kolon hattı",
            3,
        ),
        veri("P2", "Makine besleme hattının gücü  ( = Pşeb )", P_motor_W, "W", "yukarıdan", 0),
        veri("L2", "Makine besleme uzunluğu", L2, "m", h["L2_kaynak"]),
        veri("S2", "Makine besleme kesiti", S2, "mm²", h["S2_kaynak"]),
        hesap(
            "ε2  =   100 · P2 · L2   /   ( κ · S2 · U² )",
            f"=   100 · {trn(P_motor_W, 0)} · {tr(L2)}   /   ( {trn(kappa, 1)} · {tr(S2)} · {trn(U, 0)}² )",
            h["eps2"],
            "%",
            "makine besleme",
            3,
        ),
        hesap(
            "ε   =   ε1  +  ε2", f"=   {tr(h['eps1'], 3)}  +  {tr(h['eps2'], 3)}", h["eps"], "%", "toplam", 3
        ),
        veri("εmax", "İzin verilen gerilim düşümü", h["eps_max"], "%", "GİRİŞ", 1),
    ]


def _iz_satiri(ad, aciklama, iz, kesin):
    return veri(
        ad,
        aciklama,
        (trn(iz, 1) if kesin else f"≥ {trn(iz, 1)}") if sayi_mi(iz) else "tablo dışı — kontrol edilemedi",
        "A",
        "IEC 60364-5-52" if kesin else "tablo dışı kesit — alt sınır ( bir küçük tablo satırı )",
        1,
    )


def _spe_satiri(ad, aciklama, spe, kaynak):
    return veri(
        ad,
        aciklama,
        spe if spe is not None else "kontrol edilemedi — kesit tablo dışı",
        "mm²" if spe is not None else "",
        kaynak,
        1,
    )


def _sigorta_satirlari(h):
    """Bölüm 6:  grup sigortası ve makine besleme kablosunun önündeki en büyük sigorta."""
    In, In_max2 = h["sigorta_A"], h["In_max2"]
    return [
        veri(
            "In",
            "Grup sigortası  ( motor koruma cihazı )",
            In if sayi_mi(In) else "seçilemedi",
            "A" if sayi_mi(In) else "",
            "bölüm 5",
            0,
        ),
        veri(
            "Inmax2",
            "Makine besleme kablosunun önündeki en büyük sigorta",
            In_max2 if sayi_mi(In_max2) else "kontrol edilemedi — kesit tablonun altında",
            "A" if sayi_mi(In_max2) else "",
            h["In_max2_kaynak"],
            0,
        ),
    ]


def _akim_adimlari(h):
    """Bölüm 6:  iki hattın akımı, taşıma kapasiteleri, koruma iletkenleri."""
    U, cosfi, P_hat, P_motor_W = h["U_sebeke"], h["cosfi"], h["P_hat"], h["P_motor_W"]
    return [
        hesap(
            "I   =   P1   /   ( √3 · U · cosφ )",
            f"=   {trn(P_hat, 0)}   /   ( 1,73 · {trn(U, 0)} · {tr(cosfi)} )",
            h["I_hat"],
            "A",
            "kolon hattı akımı  —  şebekeden çekilen",
        ),
        hesap(
            "I2  =   P2   /   ( √3 · U · cosφ )",
            f"=   {trn(P_motor_W, 0)}   /   ( 1,73 · {trn(U, 0)} · {tr(cosfi)} )",
            h["I2"],
            "A",
            "makine besleme akımı  —  şebekeden çekilen",
        ),
        _iz_satiri("Iz2", "Makine besleme kablosunun taşıma kapasitesi", h["Iz2"], h["Iz2_kesin"]),
        *_sigorta_satirlari(h),
        _iz_satiri("Iz", "Kablonun akım taşıma kapasitesi", h["Iz"], h["Iz_kesin"]),
        metin("Koruma iletkeni ( PE ) kesitleri  —  Çizelge-8 :"),
        _spe_satiri("SPE1", "Kolon hattı koruma iletkeni  ( asgari )", h["SPE1"], h["SPE1_kaynak"]),
        _spe_satiri("SPE2", "Makine besleme koruma iletkeni  ( asgari )", h["SPE2"], h["SPE2_kaynak"]),
    ]


def _gerilim_dusumu_sonucu(h):
    """MAKİNE BESLEME HATTI ( S2 ) DA SONUCA GİRER.
    Program bir süre yalnız ⚠ uyarı veriyordu:  37 kW motora 1,5 mm²
    kabloyla bölüm "uygundur" diyordu."""
    eps_uygun, akim_uygun, akim2_uygun = h["eps_uygun"], h["akim_uygun"], h["akim2_uygun"]
    s2_kontrol = sayi_mi(h["I2"])
    sigorta2_uygun = h["sigorta2_uygun"] or not h["sigorta2_kontrol"]
    tumu = eps_uygun and akim_uygun and (akim2_uygun or not s2_kontrol) and sigorta2_uygun
    if akim_uygun:
        akim = "UYGUN"
    elif sayi_mi(h["Iz"]):
        akim = "UYGUN DEĞİL — kesiti büyütün"
    else:
        akim = "KONTROL EDİLEMEDİ — kesit akım tablosunun dışında"
    if akim2_uygun:
        akim2 = "UYGUN"
    else:
        akim2 = "UYGUN DEĞİL — makine besleme kesitini büyütün" if s2_kontrol else "KONTROL EDİLEMEDİ"
    if not h["sigorta2_kontrol"]:
        sigorta2 = "KONTROL EDİLEMEDİ"
    elif h["sigorta2_uygun"]:
        sigorta2 = "UYGUN"
    else:
        sigorta2 = "UYGUN DEĞİL — sigorta kabloyu korumuyor, makine besleme kesitini büyütün"
    return {
        "baslik": "KONTROL      ε ≤ εmax    ·    I ≤ Iz    ·    I2 ≤ Iz2    ·    In ≤ Inmax2",
        "metin": (
            f"Seçilen kablo :   {tr(h['S1'])} mm²  {h['kablo_tipi']}   —   "
            + ("uygundur." if tumu else "UYGUN DEĞİLDİR.")
        ),
        "uygun": bool(tumu),
        "alt": [
            "ε  ≤  εmax  :  " + ("UYGUN" if eps_uygun else "UYGUN DEĞİL — kesiti büyütün"),
            "I  ≤  Iz    :  " + akim,
            "I2 ≤  Iz2   :  " + akim2,
            "In ≤  Inmax2:  " + sigorta2,
        ],
    }


# =========================================================
#  PAFTAYA GİRMEYEN EK DENETİMLER  —  ⚠ uyarı olarak bildirilir
# =========================================================
def _ek_denetimler(h, ikaz, engelleyici):
    for _ad, _kesit, _iz, _kesin in (
        ("S1 — kolon hattı", h["S1"], h["Iz"], h["Iz_kesin"]),
        ("S2 — makine besleme", h["S2"], h["Iz2"], h["Iz2_kesin"]),
    ):
        if _kesin:
            continue
        if sayi_mi(_iz):
            ikaz.append(
                f"{_ad} kesiti {tr(_kesit)} mm² akım tablosunda BULUNMUYOR : kontrol, bir "
                f"küçük tablo satırının değeriyle ( Iz ≥ {trn(_iz, 0)} A ) emniyetli tarafta "
                "yapıldı. Kesin taşıma kapasitesi IEC 60364-5-52 / imalatçı verisinden "
                "alınmalı ve paftaya yazılmalıdır."
            )
        else:
            ikaz.append(
                f"{_ad} kesiti {tr(_kesit)} mm² akım tablosunun EN KÜÇÜK kesitinin altında : "
                "akım taşıma kontrolü yapılamadı."
            )
    I2, Iz2 = h["I2"], h["Iz2"]
    if sayi_mi(I2) and not h["akim2_uygun"]:
        engelleyici.append(
            f"MAKİNE BESLEME KESİTİ AKIM BAKIMINDAN YETERSİZ : S2 = {tr(h['S2'])} mm² "
            f"kablo {(tr(Iz2) + ' A') if sayi_mi(Iz2) else 'tablo dışı'} taşır, "
            f"motor akımı I2 = {tr(I2)} A. Kesiti büyütün."
        )
    #  Grup sigortası kabloyu korumuyor ( bkz. _gerilim_dusumu ):  önerilen kesit
    #  iki koşulu birlikte sağlar — akım uyarısıyla yan yana çıktığında da aynı sayı
    if h["sigorta2_kontrol"] and not h["sigorta2_uygun"]:
        en_az = tablolar.gerekli_kesit(I2, h["sigorta_A"])
        engelleyici.append(
            f"MAKİNE BESLEME KABLOSU SİGORTAYLA KORUNMUYOR : grup sigortası 4 x "
            f"{trn(h['sigorta_A'], 0)} A, S2 = {trn(h['S2'], 1)} mm² kablonun önünde en çok "
            f"{trn(h['In_max2'], 0)} A olabilir ( {h['In_max2_kaynak']} ). Kesiti büyütün"
            + (f" — en az {trn(en_az, 1)} mm²." if en_az else ".")
        )
    #  Kabin kuyunun içine girer — genişlik karşılaştırması fizikseldir.
    #  Aradaki boşluk kapı tipine, karşı ağırlık ve ray konumuna göre değişir,
    #  bu yüzden asgari boşluk dayatılmaz; yalnız "kabin ≥ kuyu" reddedilir.
    #  KABİN ALANI BEYAN YÜKÜNE UYGUN OLMALIDIR  ( MMO/697 Tablo-11 = TS EN 81-20 ).
    #  Aşırı büyük kabin, beyan yükünün üstünde yüklenmeye izin verir; tablo bunu
    #  sınırlar ( ör. 450 kg → en fazla 1,84 m² ).  Hesabı DURDURMAZ:  avan
    #  aşamasında kabin ölçüleri yaklaşıktır, karar projecinindir.
    Q, kabin_a, kabin_b, kuyu_b = h["Q"], h["kabin_a"], h["kabin_b"], h["kuyu_b"]
    _azami = tablolar.kabin_azami_alan(Q)
    if all(sayi_mi(x) and x > 0 for x in (kabin_a, kabin_b)) and sayi_mi(_azami):
        _alan = (kabin_a / 1000) * (kabin_b / 1000)
        if _alan > _azami + 1e-9:
            ikaz.append(
                f"KABİN ALANI BEYAN YÜKÜNE GÖRE BÜYÜK : {trn(Q, 0)} kg için MMO/697 "
                f"Tablo-11 ( TS EN 81-20 ) en fazla {tr(_azami)} m² verir; girilen "
                f"kabin {trn(kabin_a, 0)} × {trn(kabin_b, 0)} mm = {tr(_alan)} m². "
                "Beyan yükünü büyütün ya da kabini küçültün — aksi hâlde kabin, "
                "beyan yükünün üstünde yüklenebilir."
            )

    #  Kabin kuyuya sığmıyorsa proje FİZİKSEL olarak kurulamaz — bilgilendirici
    #  değil, engelleyicidir.
    if all(sayi_mi(x) and x > 0 for x in (kuyu_b, kabin_b)) and kabin_b >= kuyu_b:
        engelleyici.append(
            f"KABİN KUYUYA SIĞMIYOR : kabin genişliği {trn(kabin_b, 0)} mm, kuyu "
            f"genişliği {trn(kuyu_b, 0)} mm. Kabin genişliği kuyudan KÜÇÜK olmalıdır "
            "( aradaki boşluk kapı tipine, ray ve karşı ağırlık konumuna göre belirlenir )."
        )


def _ozet(h):
    """Asansörün özeti:  öteki hesapların ( trafik, topraklama, uygulama
    projesi, çıktılar ) okuduğu değerler."""
    zincir_var = h["zincir_var"]
    return {
        "tanim": h["tanim"],
        "kapasite": h["P_kap"],
        "Q": h["Q"],
        "Q0": h["Q0"],
        "V": h["V"],
        "eta": h["eta"],
        #  eta_p = motor gücünde kullanılan verim:  palangalı sistemde
        #  η − 0,10 ( MMO/697 §2.4 ),  öteki durumlarda η.
        "eta_p": h["eta_p"],
        "Gk": h["Gk"],
        "Gk0": h["Gk0"],
        "Gf": h["Gf"],
        "P": h["P_kut"],
        "Ga": h["Ga"],
        "i_palanga": h["i_pal"],
        "q_denge": h["q"],
        "i_kaynak": h["i_kaynak"],
        "q_kaynak": h["q_kaynak"],
        "makine_tipi": h["makine_tipi"],
        "aski": tablolar.aski_orani_metni(h["i_pal"]),
        "k1": h["k1"],
        "Lr": h["Lr"],
        "Mg": h["Mg"],
        "denge_zinciri": zincir_var,
        "mz": h["mz"] if zincir_var else None,
        "Gz": h["Gz"],
        "agirlik_guvenlik_tertibati": h["ag_tertibat_var"],
        "N_hes": h["N_hes"],
        "Nsc": h["Nsc"],
        "motor_uygun": h["motor_uygun"],
        **{k: h[k] for k in ("P1", "P2", "PR", "PK", "Fs", "n_kabin", "n_kuyu", "k_kabin", "k_kuyu")},
        **{k: h[k] for k in ("eta_kabin", "T_kabin", "Z_kabin", "eta_kuyu", "T_kuyu", "Z_kuyu")},
        "n1_kuyu": h["n1_kuyu"],
        "n2_kuyu": h["n2_kuyu"],
        **{k: h[k] for k in ("g_motor", "g_motor_seb", "eta_m", "g_kuyu", "g_kabin", "g_priz", "g_md")},
        "kabin_a": h["ka"],
        "kabin_b": h["kb"],
        "kuyu_a": h["qa"],
        "kuyu_b": h["qb"],
        **{k: h[k] for k in ("P_kurulu", "P_hat", "eps1", "eps2", "eps", "eps_uygun")},
        "I": h["I_hat"],
        **{k: h[k] for k in ("Iz", "akim_uygun", "I2", "Iz2", "akim2_uygun", "I_motor", "sigorta_A")},
        **{k: h[k] for k in ("motor_sigorta", "Hk", "kablo_tipi", "S1", "L1", "S2", "L2")},
        #  Koruma iletkeni kesitleri özete girer:  ana potansiyel dengeleme
        #  iletkeni TESİSİN EN BÜYÜK koruma iletkeninden türer ve tesis
        #  birden çok asansör olabilir  ( m.9-j/1/i ).
        "SPE1": h["SPE1"],
        "SPE2": h["SPE2"],
    }


# =====================================================================
#  MAKİNE DAİRESİ AYDINLATMASI      —  MK.DAİRESİ AYD. sayfası
# =====================================================================
def hesapla_makine_dairesi(ortak: dict, S: dict) -> dict:
    A = ortak.get("mk_uzunluk")
    B = ortak.get("mk_genislik")
    #  "Makine dairesi yok ( MRL )" işaret kutusu açık bir tercihtir; ölçü
    #  alanlarına 0 yazmayı beklemek yerine kullanıcı bunu doğrudan söyler.
    #  Kutu hiç gönderilmemişse ( eski proje dosyaları ) eski davranışa
    #  dönülür: ölçü yoksa MRL kabul edilir.
    isaretli = "mk_yok" in (ortak or {})
    mk_yok = evet_mi(ortak.get("mk_yok"))
    olcu_var = sayi_mi(A) and sayi_mi(B) and A > 0 and B > 0
    if mk_yok:
        return {
            "aktif": False,
            "mk_yok": True,
            "uyari": "Makine dairesi yok ( MRL ) olarak işaretlendi  —  bu hesap uygulanmaz.",
        }
    if not olcu_var:
        if isaretli:
            return {
                "aktif": False,
                "mk_yok": False,
                "uyari": "!!!   MAKİNE DAİRESİ ÖLÇÜLERİ GİRİLMEDİ   —   A ve B "
                "ölçüsünü girin ya da 'Makine dairesi yok ( MRL )' "
                "kutusunu işaretleyin   !!!",
            }
        return {
            "aktif": False,
            "mk_yok": True,
            "uyari": "Makine dairesiz ( MRL ) sistem  —  bu hesap uygulanmaz.",
        }
    a, b = A / 1000, B / 1000
    hh, d = S["h_makine_dairesi"], S["kirlenme_faktoru"]
    E, OL = S["E_makine_dairesi"], S["kuyu_armatur_lm"]
    k, eta, Tt, Z = _aydinlatma(a, b, E, OL, S, hh)
    n = int(yukari_yuvarla(Z, 0)) if sayi_mi(Z) else None

    bl = Bolum("MAKİNE DAİRESİ AYDINLATMA HESABI", "TS EN 81-20", kimlik="makine_dairesi_aydinlatma")
    bl["adimlar"] = [
        veri("a", "Makine dairesi uzunluğu", a, "m", "GİRİŞ"),
        veri("b", "Makine dairesi genişliği", b, "m", "GİRİŞ"),
        veri(
            "h",
            "Armatür ile döşeme ( çalışma düzlemi ) arasındaki yükseklik",
            hh,
            "m",
            "TS EN 81-20 m.5.2.1.4.2 · m.5.2.6.3.2.1",
        ),
        hesap(
            "k   =   a · b   /   ( h · ( a + b ) )",
            f"=   {tr(a)} · {tr(b)}   /   ( {tr(hh)} · ( {tr(a)} + {tr(b)} ) )",
            k,
            "—",
            "bölge indeksi",
            4,
        ),
        veri("η", "Oda aydınlatma verimi", eta, "—", "KABUL  ·  aydınlatma verimi tablosu"),
        veri("E", "Asgari aydınlatma şiddeti", E, "lüx", "KABUL", 0),
        veri("d", "Kirlenme ( bakım ) faktörü", d, "—", "KABUL"),
        hesap(
            "T   =   E · a · b · d   /   η",
            f"=   {trn(E, 0)} · {tr(a)} · {tr(b)} · {tr(d)}   /   {tr(eta)}",
            Tt,
            "lm",
            "",
        ),
        veri(
            "ØL",
            "Bir armatürün ışık akısı",
            OL,
            "lm",
            _armatur_kaynagi(S, "kuyu_armatur_W", "kuyu_armatur_lm"),
            0,
        ),
        hesap("Z   =   T   /   ØL", f"=   {tr(Tt)}   /   {trn(OL, 0)}", Z, "adet", ""),
        veri("n", "SEÇİLEN armatür sayısı  ( Z yukarı yuvarlanır )", n, "adet", "", 0),
    ]
    bl["sonuc"] = {
        "baslik": "SONUÇ",
        "metin": f"{n} adet {trn(S['kuyu_armatur_W'], 0)} W armatür kullanılacaktır.",
        "uygun": True,
    }
    return {"aktif": True, "bolum": bl, "n": n, "k": k, "eta": eta, "T": Tt, "Z": Z}


# =====================================================================
#  TEMEL TOPRAKLAMA HESABI          —  TOPRAKLAMA sayfası
# =====================================================================
def serit_boyu_tahmin(a, b, goz=20.0):
    """
    ŞERİT ( BAND ) BOYU  —  temel ölçülerinden türetme.

    Avan aşamasında elektrik projesinin topraklama planı henüz çizilmemiş
    olur; ofiste de yalnız temelin UZUNLUĞU ve GENİŞLİĞİ girilir.  Uygulama
    kuralı:  band temelin çevresini KAPALI RİNG olarak dolaşır, gözler
    `goz` × `goz` m'yi geçmeyecek şekilde enine / boyuna bağ atılır.

        L   =   2 · ( a + b )   +   na · b   +   nb · a
        na  =   tavan( a / goz ) − 1        ( b boyunda enine bağ )
        nb  =   tavan( b / goz ) − 1        ( a boyunda boyuna bağ )

    Döner:  ( L, ring, na, nb ).  a ya da b geçersizse L = None.
    """
    if not (sayi_mi(a) and sayi_mi(b) and a > 0 and b > 0):
        return None, None, 0, 0
    if not (sayi_mi(goz) and goz > 0):
        goz = 20.0
    ring = 2 * (a + b)
    na = max(0, math.ceil(a / goz - 1e-9) - 1)
    nb = max(0, math.ceil(b / goz - 1e-9) - 1)
    return ring + na * b + nb * a, ring, na, nb


def hesapla_topraklama(ortak: dict, S: dict, en_buyuk_pe=None) -> dict:
    a = ortak.get("temel_a")
    b = ortak.get("temel_b")
    beta = _ortak_degeri(ortak, S, "beta")
    L = ortak.get("serit_L")
    Is = _ortak_degeri(ortak, S, "cubuk_sayisi")
    goz = S.get("goz_araligi", 20)

    #  ŞERİT BOYU GİRDİ DEĞİL, TÜRETİLEN DEĞERDİR.  Ofiste temel için yalnız
    #  uzunluk ve genişlik giriliyor; band boyu bunlardan çıkarılır.  Kullanıcı
    #  topraklama planından gerçek boyu okuyabiliyorsa yazar, yazdığı değer
    #  türetileni ezer.
    L_kaynak, L_ring, L_na, L_nb = "GİRİŞ", None, 0, 0
    if not (sayi_mi(L) and L > 0):
        L, L_ring, L_na, L_nb = serit_boyu_tahmin(a, b, goz)
        L_kaynak = "türetilen"

    if not all(sayi_mi(x) and x > 0 for x in (a, b, beta, L)):
        return {
            "aktif": False,
            "uyari": (
                "!!!   Temel ölçüleri ( uzunluk × genişlik ) ya da toprak "
                "özgül direnci eksik veya sıfır   !!!"
            ),
        }

    A = a * b
    r = math.sqrt(A / math.pi)
    D = 2 * r
    Ry = beta / (2 * D) + beta / L
    lc = S["lc"]
    Rc = (beta / (Is * lc)) if (sayi_mi(Is) and Is > 0 and lc > 0) else None
    Re = (Ry * Rc / (Ry + Rc)) if sayi_mi(Rc) else Ry
    UL = S["UL"]
    IDn = S["IDn"]
    Re_max = UL / IDn if IDn > 0 else None
    uygun = sayi_mi(Re) and sayi_mi(Re_max) and Re <= Re_max
    t = {
        "a": a,
        "b": b,
        "beta": beta,
        "Is": Is,
        "goz": goz,
        "A": A,
        "r": r,
        "D": D,
        "Ry": Ry,
        "lc": lc,
        "Rc": Rc,
        "Re": Re,
        "UL": UL,
        "IDn": IDn,
        "Re_max": Re_max,
        "uygun": uygun,
        "L": L,
        "L_kaynak": L_kaynak,
        "L_na": L_na,
        "L_nb": L_nb,
    }
    #  4 -  TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ ( bkz. _iletken_bolumu )
    Sapd, apd_ham, apd_sinir = tablolar.ana_potansiyel_dengeleme_kesiti(en_buyuk_pe)
    Stopr, topr_dayanak = tablolar.topraklama_iletkeni_kesiti(en_buyuk_pe)
    return {
        "aktif": True,
        "bolumler": [
            _yatay_topraklayici_bolumu(t),
            _dikey_topraklayici_bolumu(t),
            _topraklama_direnci_bolumu(t, S),
            _iletken_bolumu(en_buyuk_pe, Sapd, apd_ham, apd_sinir, Stopr, topr_dayanak),
        ],
        "Sapd": Sapd,
        "Stopr": Stopr,
        "en_buyuk_pe": en_buyuk_pe,
        "A": A,
        "r": r,
        "D": D,
        "Ry": Ry,
        "Rc": Rc,
        "Re": Re,
        "Re_max": Re_max,
        "uygun": uygun,
        "L": L,
        "L_kaynak": L_kaynak,
        "L_ring": L_ring,
        "L_na": L_na,
        "L_nb": L_nb,
        "goz_araligi": goz,
    }


def _yatay_topraklayici_bolumu(t):
    a, b, A, r, D, beta, L = t["a"], t["b"], t["A"], t["r"], t["D"], t["beta"], t["L"]
    b1 = Bolum("1 -  YATAY ( TEMEL ) TOPRAKLAYICI", "IEEE Std 80", kimlik="topraklama_yatay")
    b1["adimlar"] = [
        hesap("A   =   a · b", f"=   {tr(a)}  ·  {tr(b)}", A, "m²", "temel alanı"),
        hesap("r   =   √ ( A / π )", f"=   √ ( {tr(A)} / 3,1416 )", r, "m", "eşdeğer yarıçap"),
        hesap("D   =   2 · r", f"=   2  ·  {tr(r)}", D, "m", "eşdeğer daire çapı"),
        veri("β", "Toprak özgül direnci", beta, "Ω·m", "GİRİŞ", 0),
        #  L TÜRETİLDİYSE PAFTAYA HESABIYLA BASILIR.  Eskiden her durumda
        #  "GİRİŞ" diye basılıyordu:  okuyan sayının nereden geldiğini
        #  göremiyordu.  Şerit temelin çevresini kapalı halka olarak dolaşır,
        #  gözler karelaj aralığını ( Sabitler ) geçmeyecek biçimde enine ve
        #  boyuna bağ atılır — bkz. serit_boyu_tahmin.  Elle girildiyse
        #  sıradan bir girdi satırıdır.
        (
            hesap(
                "L   =   2 · ( a + b )   +   na · b   +   nb · a",
                f"=   2 · ( {tr(a)} + {tr(b)} )   +   {t['L_na']} · {tr(b)}   +   {t['L_nb']} · {tr(a)}",
                L,
                "m",
                f"şerit:  temel çevresi + karelaj bağları  ( göz ≤ {trn(t['goz'], 0)} m )",
            )
            if t["L_kaynak"] == "türetilen"
            else veri("L", "Temel / şerit iletken uzunluğu", L, "m", "GİRİŞ")
        ),
        hesap(
            "Ry  =   β / ( 2 · D )   +   β / L",
            f"=   {trn(beta, 0)} / ( 2 · {tr(D)} )   +   {trn(beta, 0)} / {tr(L)}",
            t["Ry"],
            "Ω",
            "IEEE Std 80",
            3,
        ),
    ]
    return b1


def _dikey_topraklayici_bolumu(t):
    b2 = Bolum("2 -  DİKEY ( ÇUBUK ) TOPRAKLAYICI", kimlik="topraklama_dikey")
    b2["adimlar"] = [
        veri("lç", "Bir çubuğun boyu", t["lc"], "m", "KABUL"),
        veri("Is", "Paralel bağlı çubuk sayısı", t["Is"], "adet", "GİRİŞ", 0),
        hesap(
            "Rç  =   β / ( Is · lç )",
            (
                f"=   {trn(t['beta'], 0)} / ( {trn(t['Is'], 0)}  ·  {tr(t['lc'])} )"
                if sayi_mi(t["Rc"])
                else "—   ( çubuk topraklayıcı yok )"
            ),
            t["Rc"],
            "Ω",
            "tek çubuk β/lç — Is adet paralel",
            3,
        ),
    ]
    return b2


def _topraklama_direnci_bolumu(t, S):
    Ry, Rc, Re, Re_max = t["Ry"], t["Rc"], t["Re"], t["Re_max"]
    b3 = Bolum("3 -  TOPLAM TOPRAKLAMA DİRENCİ VE KONTROL", kimlik="topraklama_toplam")
    b3["adimlar"] = [
        hesap(
            "Re  =   ( Ry · Rç )  /  ( Ry  +  Rç )",
            (
                f"=   ( {tr(Ry)} · {tr(Rc)} )  /  ( {tr(Ry)} + {tr(Rc)} )"
                if sayi_mi(Rc)
                else f"=   {tr(Ry)}   ( yalnız temel topraklayıcı )"
            ),
            Re,
            "Ω",
            "paralel",
            3,
        ),
        veri("UL", "İzin verilen temas gerilimi", t["UL"], "V", "KABUL", 0),
        veri("IΔn", "Kaçak akım rölesi anma akımı", t["IDn"], "A", "KABUL"),
        hesap("Re max  =   UL   /   IΔn", f"=   {trn(t['UL'], 0)}   /   {tr(t['IDn'])}", Re_max, "Ω", "", 2),
    ]
    b3["sonuc"] = {
        "baslik": "KONTROL      Re  ≤  Re max",
        "metin": (
            f"Re = {tr(Re)} Ω   ≤   {tr(Re_max)} Ω   olduğundan temel topraklaması yeterlidir."
            if t["uygun"]
            else f"Re = {tr(Re)} Ω   >   {tr(Re_max)} Ω   —   ek topraklayıcı gereklidir."
        ),
        "uygun": bool(t["uygun"]),
    }
    #  BU NOTLAR PAFTAYA VE CAD ÇIKTISINA BASILMAZ  ( "ekran_notlari" ).
    #  Gerekçe:  söyledikleri değerler zaten hesap satırlarında yazılı
    #  ( UL, IΔn, β — kaynak kolonuyla birlikte ) ve dört satırlık blok,
    #  topraklama hesabının üç bölümünün tek sayfada kalmasını engelliyordu.
    #  Bilgi kaybolmuyor:  ekranda bölüm başlığındaki ⓘ altında duruyor.
    b3["ekran_notlari"] = [
        "HESAPLANAN TAHMİNİ DEĞERDİR — TESİS TAMAMLANDIKTAN SONRA ÖLÇÜMLE DOĞRULANACAKTIR.",
        f"KABULLER: TT şebeke, UL = {trn(S['UL'], 0)} V, IΔn = {tr(S['IDn'])} A. "
        "Şebeke TN sistem ise bu kontrol ölçütü geçerli değildir.",
        "Toprak özgül direnci β zemin etüdünden alınmalıdır; verilmemişse 150 Ω·m kabul "
        "edilir. Rç bağıntısı çubuk çapını ve çubuklar arası etkileşimi içermeyen bir ön "
        "kabuldür — kesin değer ölçümle bulunur.",
    ]
    return b3


def _iletken_bolumu(en_buyuk_pe, Sapd, apd_ham, apd_sinir, Stopr, topr_dayanak):
    """4 -  TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ

    Bölüm 1-3 toprak ELEKTRODUNUN direncini çözer;  bu bölüm ana topraklama
    barasına bağlanması zorunlu İLETKENLERİN kesitlerini verir  ( m.9/d
    baraya bağlanacakları sayar:  topraklama iletkenleri, koruma iletkenleri,
    ana potansiyel dengeleme iletkenleri ).  Koruma iletkeni kesitleri
    asansör paftasının 6. bölümündedir — hat başına ayrıdır;  buradakiler
    TESİSİN TAMAMI için tektir ve en büyük koruma iletkeninden türer."""
    b4 = Bolum(
        "4 -  TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ",
        "Elektrik Tesislerinde Topraklamalar Yönetmeliği",
        kimlik="topraklama_iletkenleri",
    )
    if en_buyuk_pe is None:
        b4["adimlar"] = [
            metin(
                "Kesitler tesisteki en büyük koruma iletkeninden türer; etkin asansör bulunmadığı için hesaplanamadı."
            ),
        ]
    else:
        #  İŞLEM SATIRI SONUCA KADAR HER ADIMI YAZAR:  "0,5 · 4 = 6" ya da
        #  "0,5 · 16 = 8" ( sonuç 10 ) diye bir satır kendi içinde yanlıştır.
        #  Yarım kesit → 6 mm² asgarisi / 25 mm² üst sınırı → standart kesit.
        islem = (
            f"=   0,5  ·  {tr(en_buyuk_pe)}   =   {tr(en_buyuk_pe / 2)}"
            + (
                f"   →   en az {trn(tablolar.APD_ASGARI, 0)} mm²"
                if en_buyuk_pe / 2 < tablolar.APD_ASGARI
                else ""
            )
            + (f"   →   {trn(tablolar.APD_UST_SINIR, 0)} mm² üst sınırı" if apd_sinir else "")
            + (
                f"   →   standart kesit {trn(Sapd, 0)} mm²"
                if sayi_mi(Sapd) and Sapd != min(apd_ham, tablolar.APD_UST_SINIR)
                else ""
            )
        )
        b4["adimlar"] = [
            veri(
                "SPE",
                "Tesisteki en büyük koruma iletkeni kesiti",
                en_buyuk_pe,
                "mm²",
                "asansör paftaları bölüm 6",
                1,
            ),
            hesap(
                "Sapd  =   0,5 · SPE        ( en az 6 mm² )",
                islem,
                Sapd,
                "mm²",
                "m.9-j/1/i  ·  Çizelge-4b",
                1,
            ),
            veri("Stopr", "Topraklama iletkeni  ( asgari )", Stopr, "mm²", f"m.9/c  ·  {topr_dayanak}", 1),
        ]
    b4["ekran_notlari"] = [
        "Ana potansiyel dengeleme iletkeni bakır için 25 mm²'den büyük olmak "
        "zorunda değildir ( m.9-j/1/i ); başka metallerde eşdeğer iletkenlik aranır.",
        "Topraklama iletkeni TOPRAĞA DÖŞENİYOR ve korozyona karşı KORUNMAMIŞSA "
        "Çizelge-4a en az 25 mm² bakır ( ya da 50 mm² daldırma galvanizli demir ) ister.",
        "Kablo içinde olmayan koruma iletkeni mekanik korumalıysa 2,5 mm²'den, "
        "korumasızsa 4 mm²'den küçük olamaz ( m.9-e1/iii ).",
    ]
    return b4


# =====================================================================
#  TÜM AVAN HESABI  ( ÖZET dâhil )
# =====================================================================
#  Kuyu yüksekliği ile seyahat mesafesi arasındaki pay ( kuyu dibi + üst boşluk ).
#  TS EN 81-20 kuyu dibi ve üst boşluk asgarilerini hıza ve tampon tipine göre
#  belirler; uygulamada bu pay tipik olarak 4,5 – 7 m arasındadır.  Aşağıdaki
#  sınırlar HESABI DURDURMAZ, yalnız "kontrol et" uyarısı üretir.
HK_PAY_ALT = 3.5  # m — bunun altı şüpheli
HK_PAY_UST = 12.0  # m — bunun üstü şüpheli


def _trafik_tutarlilik(trafik, asansorler_girdi):
    """
    Trafik sekmesindeki sonuçla avan girdilerini karşılaştırır.
    Aktarımdan sonra trafikte yapılan bir değişiklik avan sekmesine
    yansımadıysa burada görünür.  Yalnız uyarı üretir, hesabı durdurmaz.
    """
    u = []
    if not isinstance(trafik, dict):
        return u
    ham = trafik.get("asansorler")
    t_list = [t for t in ham if isinstance(t, dict)] if isinstance(ham, list) else []
    if not t_list:
        return u
    ham_a = asansorler_girdi if isinstance(asansorler_girdi, list) else []
    a_sayi = len([a for a in ham_a if isinstance(a, dict)])
    #  GERÇEK ADET  —  API köprüsü asansör listesini arayüz sınırına ( 4 ) keser
    #  ( main._trafik_koprusu ).  Adet karşılaştırması kesilmiş listeye bakınca,
    #  trafik 27 asansör gerektirdiğinde uyarı "4 adet veriyor" diyordu.
    #  Doğru sayı köprüde `adet` alanında zaten taşınıyor.
    _adet = trafik.get("adet")
    t_sayi = (
        int(_adet)
        if (isinstance(_adet, (int, float)) and not isinstance(_adet, bool) and _adet > len(t_list))
        else len(t_list)
    )

    #  ADET  —  avan adedi trafik grubundan AZ olamaz: gruptaki her asansörün
    #  elektrik hesabı da yapılmalıdır.  FAZLASI ise olağandır ( trafik
    #  hesabına girmeyen ayrı bir yük ya da sedye asansörü ); bu bir hata
    #  değil, paftaya yazılan bir nottur.
    if a_sayi < t_sayi:
        u.append(
            f"⚠ Trafik hesabı {t_sayi} adet asansör veriyor, avanda {a_sayi} adet "
            f"tanımlı — eksik {t_sayi - a_sayi} asansörün motor gücü, kurulu güç ve "
            "gerilim düşümü hesabı yapılmamış olur."
        )
    elif a_sayi > t_sayi:
        u.append(
            f"ℹ Avanda trafik grubunda olmayan {a_sayi - t_sayi} asansör var "
            "( ayrı yük / sedye asansörü ). Kurulu güce ve gerilim düşümüne girer, "
            "trafik kontrolüne girmez."
        )

    #  DEĞER  —  yalnız trafik grubundaki asansörler karşılaştırılır ve
    #  karşılaştırma SIRA NUMARASINA göredir ( 3 nolu avan asansörü 3 nolu
    #  trafik asansörüyle ), aradaki tanımsız kolonlar hizayı kaydırmaz.
    for i in range(1, min(t_sayi, 4) + 1):
        a = ham_a[i - 1] if i - 1 < len(ham_a) else None
        if not isinstance(a, dict):
            continue
        t = t_list[i - 1]
        P_a, P_t = a.get("kapasite"), t.get("P")
        if sayi_mi(P_a) and sayi_mi(P_t) and P_a != P_t:
            u.append(
                f"⚠ {i} NOLU ASANSÖR: kapasite trafik hesabında {trn(P_t, 0)} kişi, "
                f"avan girdisinde {trn(P_a, 0)} kişi — avandaki değer ELLE "
                "değiştirilmiş. Bilerek yapıldıysa gerekçesi paftaya yazılmalıdır; "
                "değilse 'Trafikten güncelle' düğmesi eşitler."
            )
        V_a, V_t = a.get("V"), t.get("V")
        if sayi_mi(V_a) and sayi_mi(V_t) and abs(V_a - V_t) > 1e-9:
            u.append(
                f"⚠ {i} NOLU ASANSÖR: kabin hızı trafik hesabında {tr(V_t)} m/s, "
                f"avan girdisinde {tr(V_a)} m/s — avandaki değer ELLE değiştirilmiş. "
                "Bilerek yapıldıysa gerekçesi paftaya yazılmalıdır; değilse "
                "'Trafikten güncelle' düğmesi eşitler."
            )
        Hk, seyahat = a.get("Hk"), t.get("toplam_seyahat")
        if sayi_mi(Hk) and sayi_mi(seyahat) and seyahat > 0:
            pay = Hk - seyahat
            if pay <= 0:
                u.append(
                    f"⚠ {i} NOLU ASANSÖR: kuyu yüksekliği {tr(Hk)} m, toplam seyahat "
                    f"mesafesinden ( {tr(seyahat)} m ) küçük ya da ona eşit — kuyu dibi ve "
                    "üst boşluk için pay kalmıyor. Hk değerini kontrol edin."
                )
            elif pay < HK_PAY_ALT:
                u.append(
                    f"⚠ {i} NOLU ASANSÖR: kuyu dibi + üst boşluk payı yalnız {tr(pay)} m "
                    f"( Hk {tr(Hk)} − seyahat {tr(seyahat)} ). TS EN 81-20 asgarileri için "
                    "kontrol edin."
                )
            elif pay > HK_PAY_UST:
                u.append(
                    f"⚠ {i} NOLU ASANSÖR: kuyu dibi + üst boşluk payı {tr(pay)} m "
                    f"( Hk {tr(Hk)} − seyahat {tr(seyahat)} ) olağandışı büyük — kat "
                    "sayısı ya da Hk girdisi güncel olmayabilir."
                )
    return u


def hesapla(veriler: dict) -> dict:
    """Avan projesinin bütün hesapları.

    Proje geneli bir girdi kullanılamıyorsa ( ofis standardı · ortak panel )
    hesap YAPILMAZ ve yalnız  { "hata": metin }  döner — bu değer her
    asansörün ve topraklamanın hesabına girer, yarım bir proje çıkmaz.
    """
    ortak = veriler.get("ortak") or {}
    S = sabitler(veriler.get("sabitler"))
    hatalar = girdi_hatalari(veriler, S)
    if hatalar:
        return {
            "hata": "HESAP HATASI: Girilen değer kullanılamıyor  —  "
            + "  ·  ".join(hatalar)
            + "   ·   Değeri düzeltin ya da alanı boşaltın ( boş alan "
            "ofis varsayılanını kullanır )."
        }
    mk = hesapla_makine_dairesi(ortak, S)
    #  Makine dairesi aydınlatmasının devresi yalnız makine dairesi varsa ( MRL'de
    #  oda yok ):  hesabı yapılmışsa ya da oda var denmiş ama ölçüsü girilmemişse
    #  ( hesap eksik — mk_yok False )
    oda = bool(mk.get("aktif")) or mk.get("mk_yok") is False
    #  MAKİNE DAİRESİ AYDINLATMASI BİR TABLODAN BESLENİR.  Kabin, kuyu ve makine
    #  dairesi aydınlatması makineyi besleyen devreden bağımsızdır:  ayrı bir
    #  hatla ya da ana şalterin giriş tarafından ayrılan bir hatla beslenir
    #  ( TS EN 81-20 m.5.10.7.1 ) — TAS'ın 30 mA'lik aydınlatma grubunda kendi
    #  sigortasıyla ( Tavaslıoğlu, Asansör Tasarımı, ana tablo örneği:  "ayrı
    #  bir hattan alınmadı ise makine dairesi aydınlatması" ).  Yükü o tablonun
    #  kurulu güç cetveline ve kolon hattına girer.  Oda tektir:  elektriği
    #  hesaplanan ilk asansörün tablosu besler ( ÇİZİM KABULÜ ), dört asansörlü
    #  binada dört kez yazılmaz.  Hesabı düşen asansörün tablosu çizilmez:  devre
    #  ona verilince pakette hiçbir tabloda kalmıyor, öbürleri olmayan bir TAS'ı
    #  gösteriyordu ( 23 Eki bağımsız denetim ) — sıradakine geçer.  Uygulama
    #  projesi asansörleri tek tek hesaplar;  besleyen bulunduktan sonra onu
    #  kendisi söyler ( makine_dairesi_tablosu ).
    besleyen = veriler.get("makine_dairesi_tablosu") if oda else None
    asansorler = []
    for i, a in enumerate(veriler.get("asansorler") or [], 1):
        if not a:
            continue
        md = {"adet": mk.get("n"), "W": S["kuyu_armatur_W"]} if oda and besleyen is None else None
        s = hesapla_asansor(a, ortak, S, i, md)
        if md and s.get("elektrik"):
            besleyen = tas_adi(i)
        asansorler.append(s)
    for a in asansorler:
        e = a.get("elektrik")
        if e:
            e["makine_dairesi"] = oda
            if oda and "makine_dairesi_ayd" not in e:
                e["makine_dairesi_ayd"] = {"besleyen": besleyen}
    #  ANA POTANSİYEL DENGELEME "TESİSTEKİ EN BÜYÜK KORUMA İLETKENİ"NDEN
    #  türer ( m.9-j/1/i ) — tesis dört asansörlü olabilir, hepsine bakılır.
    _peler = [
        x
        for a in asansorler
        if a.get("aktif")
        for x in ((a["ozet"].get("SPE1"), a["ozet"].get("SPE2")))
        if sayi_mi(x)
    ]
    tp = hesapla_topraklama(ortak, S, max(_peler) if _peler else None)

    aktifler = [a for a in asansorler if a.get("aktif")]
    tesis_kurulu = sum(a["ozet"]["P_kurulu"] for a in aktifler)

    ozet = {
        "asansorler": [{"no": a["no"], **a["ozet"]} for a in aktifler],
        "tesis_kurulu_guc": tesis_kurulu,
        "Re": tp.get("Re") if tp.get("aktif") else None,
        "topraklama_uygun": tp.get("uygun") if tp.get("aktif") else None,
        #  Şerit boyu artık türetilebilir — arayüz yer tutucusunda hangi değerin
        #  kullanıldığı ve nereden geldiği görünsün.
        "serit_L": tp.get("L"),
        "serit_L_kaynak": tp.get("L_kaynak"),
        "serit_L_ring": tp.get("L_ring"),
        "serit_L_na": tp.get("L_na"),
        "serit_L_nb": tp.get("L_nb"),
        "eps_max": ortak.get("eps_max"),
    }
    uyarilar = []
    engelleyiciler = []
    for a in asansorler:
        if not a:
            continue
        if not a.get("aktif") and a.get("uyari"):
            uyarilar.append(a["uyari"])
        uyarilar += a.get("uyarilar") or []
        engelleyiciler += a.get("engelleyici") or []
    uyarilar += _trafik_tutarlilik(veriler.get("trafik"), veriler.get("asansorler"))
    return {
        "asansorler": asansorler,
        "makine_dairesi": mk,
        "topraklama": tp,
        "ozet": ozet,
        "sabitler": S,
        "ortak": ortak,
        "uyarilar": uyarilar,
        "engelleyici": engelleyiciler,
    }
