# -*- coding: utf-8 -*-
"""
MUKAVEMET HESAP MOTORU              ( UYGULAMA PROJESİ  —  avandan ayrıdır )

Standartlar:  TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465
              MMO 208/7 m.2.4  ( motor gücü )
              MMO 208/4 m.3.4.6 ( makine konstrüksiyonu )

Bölümler
  1  Asansör motor gücü                       MMO 208/7 - 2.4
  2  Makine konstrüksiyonu                    MMO 208/4 - m.3.4.6
  3  Kullanılabilir kabin alanı               EN 81-20 m.5.4.2
  4  Askı halatları                           EN 81-50 m.5.12
  5  Hız regülatörü halatı                    EN 81-20 m.5.6.2.2.1
  6  Tahrik yeteneği                          EN 81-50 m.5.11.2 / m.5.11.3
  7  Kabin kılavuz rayları                    EN 81-50 m.C.2.1 / C.2.2 / C.2.3
  8  Karşı ağırlık kılavuz rayları            EN 81-50 m.5.10
  9  Kuyu tabanına gelen yükler               EN 81-20 m.5.2.1.8
 10  Sığınma alanları ve açıklıklar           EN 81-20 m.5.2.5.7 / 5.2.5.8

Çıktı biçimi avan motoruyla aynıdır ( engine.steps.Bolum / veri / hesap /
kontrol ), böylece ekran, PDF ve CAD katmanları ortak kalır.
"""
import math

from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import sabitler as US
from engine.uygulama import mukavemet_tablolari as MT
from engine.ortak.steps import Bolum, hesap, kontrol, numarala, veri
from engine.ortak.steps import bagla, metin, tr, trn, evet_mi

# =====================================================================
#  SABİTLER
# =====================================================================
#  Hesabın sabit sayıları ( girdi değildir ).  Kaynakları yanlarında;
#  değiştirmek gerekirse tek yer burasıdır.
SABIT = {
    "gn":              9.81,      # yerçekimi ivmesi              [m/s²]
    "motor_sabiti":    102,       # kW ↔ kg·m/s dönüşümü
    "hp_carpani":      1.34,      # kW → HP
    "Dt_dh_asgari":    40,        # tahrik kasnağı / halat oranı   EN 81-20 m.5.5.2.1
    "halat_capi_asgari": 8,       # askı halatı anma çapı [mm]     EN 81-20 m.5.5.1.2 a)
    "Dreg_dreg_asgari": 30,       # regülatör kasnağı / halat oranı
    "reg_kat_asgari":  8,         # regülatör halatı emniyet katsayısı
    "reg_kuvvet_asgari": 300,     # F'reg alt sınırı              [N]
    #  TS EN 81-20 m.5.6.2.2.1.1 a) — devreye girme hızı penceresi
    "reg_hiz_alt_carpan": 1.15,   # "at least 115 % of the rated speed"
    "reg_hiz_ust_ani":    0.80,   # ani frenlemeli ( makaralı hariç )
    "reg_hiz_ust_makara": 1.00,   # ani frenlemeli makaralı
    "reg_hiz_ust_kaymali": 1.50,  # kaymalı, v ≤ 1,0 m/s
    #  m.5.6.2.1.2.1 b) — ani frenlemeli kabin tertibatı üst hız sınırı
    "ani_tertibat_azami_v": 0.63,
    #  m.5.6.2.1.2.3 — karşı ağırlık tertibatı bu hızın üstünde KAYMALI olmalı
    "agirlik_kaymali_esigi": 1.0,
    "reg_sarilma_aci": 180,       # α'  regülatör kasnağı sarılma [°]
    "mu_yukleme":      0.1,       # μ  yükleme
    "mu_bloke":        0.2,       # μ  kabin bloke
    "kanal_acisi":     38,        # γ  sertleştirilmiş kanal      [°]
    "alt_kesilme":     90,        # β  alt kesilme açısı          [°]
    #  ÇELİĞİN ELASTİSİTE MODÜLÜ.  EN 81-50 m.5.10.4 ve Ek C'nin sembol
    #  listeleri E'yi yalnız "modulus of elasticity" diye tanımlar, sayı
    #  vermez;  standardın KENDİ verdiği tek çelik değeri m.5.13'tedir:
    #  "for steel: E = 2,1 × 10⁵ N/mm²".  Yapı çeliğinin Avrupa'daki bağlayıcı
    #  değeri de budur ( EN 1993-1-1 m.3.2.6 ).  Referans proje, ofisin Excel'i ve
    #  "new block" paftası da 210.000 kullanır — aynı sayı, paftamızı elden
    #  doğrulanabilir kılar.
    #
    #  ESKİDEN 206.010'du ve gerekçesi yazılı değildi:  21.000 kgf/mm² × 9,81,
    #  yani kgf'den çevrilmiş eski teknik değer.  Sehimleri %1,94 BÜYÜK
    #  gösteriyordu.  Yön emniyetliydi ama iki zararı vardı:  δ/δperm oranı
    #  0,981 – 1,000 bandına düşen bir tasarımı standarda göre geçerken
    #  reddediyorduk, ve paftada E'nin sayısı görünmediği için hesabı elden
    #  denetleyen 210.000 ile %1,94 farklı bir sonuç bulup bizde aritmetik
    #  hata arıyordu.
    "E":               210000,    # elastisite modülü           [N/mm²]
    #  TS EN 81-20 Çizelge 14.  k2 ÇİZELGEDE YAZILIDIR ( Running = 1,2 );
    #  k3 için çizelge sayı vermez — "imalatçı tarafından, gerçek tesise göre
    #  belirlenir" — o yüzden k3 OFİS SABİTİDİR ( sabitler.k3_yardimci ).
    "k2":              1.2,       # normal kullanma darbe katsayısı  ( Çiz.14 )
    "MY_kabin":        150,       # kabin rayına bağlı donanım    [N]
    "MY_agirlik":      50,        # ağırlık rayına bağlı donanım  [N]
    "dperm_kabin":     5,         # kabin rayı azami sehim        [mm]
    "dperm_agirlik":   10,        # ağırlık rayı azami sehim      [mm]
    "sehim_katsayi":   0.7,       # sehim formülü katsayısı
    "sehim_bolen":     48,        # 48·E·I
    "moment_pay":      3,         # M = 3·F·l/16
    "moment_bolen":    16,
    "birlesik_katsayi": 0.9,      # σk + 0,9·σm
    "kabin_merkez_payi": 130,     # xc = ( derinlik/2 + 130 ) − RK  [mm]
    "Dx_bolen":        8,         # Dx = derinlik / 8
    "Dy_bolen":        8,         # Dy = genişlik  / 8
    "Dxa_katsayi":     0.1,       # Dxa = 0,1 × ağırlık derinliği
    "Dya_katsayi":     0.05,      # Dya = 0,05 × ağırlık genişliği
    "tampon_katsayi":  4,         # F = 4·gn·(P+Q)
    #  ( Kuyu sürtünmesi yüzdeleri buradan OFİS SABİTLERİNE taşındı —
    #    kuyu_surtunme_kabin · kuyu_surtunme_agirlik;  bkz. _tahrik. )
    "ray_kaide_payi":  200,       # ray boyu:  tabliye beton yüksekliği − 200 mm
    "ray_kuyu_payi":   300,       # ray boyu:  kuyu dibi − 300 mm
}

#  SIĞINMA AÇIKLIKLARI kuyunun ÇİZİMİNDEN ölçülür ( bölüm 11, cizim/dusey.py ).
#  Kabinin düşey ölçüleri OFİS STANDARDINDADIR ( ekrandan değiştirilir, çizim
#  de aynı sayıyı kullanır — cizim/kopru.OFIS_SABITLERI );  sığınma hacimleri
#  duruş tipinden ( mukavemet_tablolari.SIGINMA_HACMI ).  Standardın asgari
#  açıklıkları çizim modülündedir ( cizim/dusey.py );  aşağıdaki ikisi çizimin
#  ölçmediği iki satırındır.
SIGINMA_PAYLARI = ("tavan_payi", "sase_alt_derinlik", "kabin_taban_kalinlik",
                   "kabin_tavan_kalinlik", "paten_yukseklik", "fren_blogu_yukseklik",
                   "kabin_kasnak_derinlik", "revizyon_payi")
SIGINMA = {
    "min_revizyon":          500,   # m.5.2.5.7.2 a) kabin üstü donanım  0,50 m
    "min_regulator":         300,   # m.5.2.5.8.2 b) kuyuya sabit parça  0,30 m
    #  m.5.2.5.7.2 b):  paten / makara ve halat bağlantısı ile kuyu tavanı
    #  arası 0,10 m ( çizimde dusey.UST_PATEN ile aynı sayı ).
    "min_paten_tavan":       100,
}


def _trh(x, hane=4):
    """Hesap satırındaki ARA DEĞER — okuyan satırı yeniden hesaplayabilsin.

    tr() iki haneye yuvarlar;  büyük sayıda sorun değildir ama birin altındaki
    bir çarpanda anlamı değiştirir:  0,179 kg/m halat "0,18", f = 0,2327
    "0,23", tampon katsayısı 0,0674 "0,07" yazılıyordu ve satırdaki sayılarla
    yeniden hesaplayan denetçi paftanın sonucunu bulamıyordu.  Sondaki
    sıfırlar atılır ( 0,1350 → 0,135 ).
    """
    s = tr(x, hane)
    return s.rstrip("0").rstrip(",") if "," in s else s


def _pozitif(x):
    """Pozitif bir sayı mı  ( bool tuzağı dâhil )."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def _sayi_mi(x):
    """Sayı mı  ( bool tuzağı dâhil;  işaretli olabilir )."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


#  BİRLEŞİK PROGRAM:  geometri çizimden.  Program hesabı yaparken çizimin
#  kurduğu yerleşimden ölçülen değerleri girdiye yazar ( engine/uygulama/
#  girdi.yerlesim_olculeri ) ve kaynağını işaretler ( g["_cizimden"] ).  Değer
#  yoksa ( motor doğrudan çağrıldı ya da çizim kurulamadı ) hesabın eski
#  yaklaşığı kullanılır;  rapor hangisinin kullanıldığını yazar.
CIZIMDEN = "ÇİZİMDEN"


def _kaynak(g, anahtar, girildi="GİRİŞ"):
    """Rapordaki kaynak yazısı:  çizimden geldiyse ÇİZİMDEN ve kuralı."""
    kural = (g.get("_cizimden") or {}).get(anahtar)
    if kural is None:
        return girildi
    if kural == "yerleşim":
        return CIZIMDEN
    kural = kural.replace("Boşsa çizimden:", "").replace("Boşsa çizimden", "").strip(" ,.:")
    if kural.startswith("(") and kural.endswith(")"):
        kural = kural[1:-1].strip()
    return f"{CIZIMDEN}  ·  {kural}" if kural else CIZIMDEN


def _cizim_olcusu(g, anahtar):
    """Çizimden ölçülmüş değer ya da None."""
    v = g.get(anahtar)
    return v if (_sayi_mi(v) and anahtar in (g.get("_cizimden") or {})) else None


#  MAKİNE YÜKÜ DÖRT RAYA EŞİT DAĞILIR  ( MRL · "Kılavuz raylara" ).
#  MRL makinesinin şasesi kabin raylarıyla birlikte karşı ağırlık raylarına da
#  oturur;  referans projenin örnek projesi de yükü dört raya birden verir ( bina
#  yükleri M1 … M4 ).  Eskiden yalnız kabin raylarına bölünüyordu:  kabin rayı
#  payı iki katı çıkıyor, karşı ağırlık rayları ise makineyi hiç görmüyordu
#  ( 50 N ofis kabulü ) — o rayların σv · σc'si ve kuyu tabanı yükü FAR
#  EMNİYETSİZ taraftaydı.  Ofisin MRL makineleri dört raya oturur ( kullanıcı
#  kararı ).  Toplam:  makine ağırlığı + kasnağın statik yükü ( Tst ).
def _makine_ray_payi(g, o):
    """Makine raylara biniyorsa ( BİR RAYA düşen yük N , kaynak );  binmiyorsa None."""
    if not (evet_mi(g.get("mk_yok"))
            and MT.makine_raya_mi(g.get("makine_raya_biniyor"))):
        return None
    nk, na = g["kabin_ray_sayisi"] or 0, g["agirlik_ray_sayisi"] or 0
    n_top = nk + na
    toplam = (g["makine_agirligi"] or 0.0) + (o.get("Tst_hesap") or 0.0)
    kutle = toplam / n_top if n_top else toplam
    return (kutle * SABIT["gn"],
            f"( Gm + Tst ) / {trn(n_top, 0)} ray  ( {trn(nk, 0)} kabin + {trn(na, 0)} "
            "karşı ağırlık rayı · makine raylara biniyor — m.5.7.2.3.7 )")


def _gezici_kablo(g):
    """Gezici kabloların toplam 1 m ağırlığı  —  İMALATÇI DEĞERİ TABLOYU EZER.

    Döner:  ( mt kg/m , kaynak )
    Tablo iki kablo tanır ( 1. tip + kat kapısından türeyen 2. tip ) ve dört
    kesit bilir;  tek kablolu ya da başka kesitli bir tesis girilemiyordu.
    Motor gücü, P ( ray · kuyu tabanı ) ve tahrik AYNI sayıyı kullanır.
    """
    elle = g.get("kablo_birim_kutle")
    if _pozitif(elle):
        return float(elle), "KATALOG"
    return (sum(MT.kablo_agirligi(g.get(k)) or 0.0
                for k in ("kablo_tipi_1", "kablo_tipi_2")),
            f"tablo  ( {g.get('kablo_tipi_1')} + {g.get('kablo_tipi_2')} )")


def _halat_verisi(g, cap="halat_capi", kutle="halat_birim_kutle",
                  kopma="halat_kopma_kN"):
    """Halat birim kütlesi ve kopma yükü  —  KATALOG GİRDİSİ TABLOYU EZER.

    Döner:  ( gh kg/m , Tmin N , gh_kaynak , Tmin_kaynak )

    TS 12385-5 tablosu yalnız 6x19 / 8x19 LİF ÖZLÜ halatları kapsar;  küçük
    kasnaklı dişlisiz makinelerin çelik özlü / özel halatları orada yoktur.
    Elle girilen değer tabloyu ezer ve paftaya kaynağı 'imalatçı kataloğu'
    olarak yazılır — hangi verinin kullanıldığı GÖRÜNÜR olmalıdır.
    """
    dh = g.get(cap)
    gh_t, Tmin_t = MT.halat_agirlik(dh), MT.halat_kopma(dh)
    gh_e, Tmin_e = g.get(kutle), g.get(kopma)
    tablo = f"TS 12385-5  ·  {MT.halat_tipi(dh)}"
    if _pozitif(gh_e):
        gh, gh_k = float(gh_e), "KATALOG"
    else:
        gh, gh_k = gh_t, tablo
    if _pozitif(Tmin_e):
        Tmin, Tmin_k = float(Tmin_e) * 1000.0, "KATALOG"
    else:
        Tmin, Tmin_k = Tmin_t, tablo
    return gh, Tmin, gh_k, Tmin_k


def _bosluk(v):
    """0,10 m ilave kılavuzlu yol + 0,035·v² sıçrama payı  →  mm.

    TS EN 81-20'de 0,035·v² açıklığın değil, kabinin en üst konumunun
    tanımındadır ( Çizelge 2 );  0,10 m ise m.5.2.5.6.2'nin ilave kılavuzlu
    yoludur.  Kuyu ölçüleri anma konumundan alındığı için ikisi burada
    tek sınırda toplanır — eşitsizlik cebirsel olarak aynıdır.
    """
    return (0.1 + 0.035 * v * v) * 1000


def _oran(a, b):
    return max(a / b, b / a) if (a and b) else None


def _kay(o, bolum, **degerler):
    """Ara değerleri  o["ara"]  altında  "bölüm.ad"  anahtarıyla saklar.

    Pafta satırlarından bağımsız, ADIYLA okunabilen sayılar:  testler bir
    ara büyüklüğü ( ör. "kabin_ray.c21.d1.sf" ) hesabı tekrar etmeden
    doğrudan denetleyebilir.  Arayüze gönderilmez.
    """
    o.setdefault("ara", {}).update(
        {f"{bolum}.{ad}": deger for ad, deger in degerler.items()})


# =====================================================================
#  1 -  ASANSÖR MOTOR GÜCÜ                        ( MMO 208/7 - 2.4 )
# =====================================================================
def _motor(g, o):
    S, O = SABIT, o["ofis"]
    Q, P, v = g["beyan_yuku"], g["kabin_agirligi"], g["beyan_hizi"]
    Dt, dh, nh, r = (g["tahrik_kasnak_capi"], g["halat_capi"],
                     g["halat_adedi"], g["aski_orani"])
    gh, _Tmin_h, gh_kaynak, _Tmin_kaynak = _halat_verisi(g)

    #  Halat boyu:  kabin tarafındaki halat, kabin en alt durakta.  Program
    #  çizimden ölçer ( tahrik kasnağından kabine, 2:1'de kabin kasnaklarının
    #  altından kuyu tavanındaki bağlantıya ).  Yoksa eski yaklaşık:  kuyu
    #  boyundan tampon/paten yığını düşülür, 5 m pay eklenir;  2:1'de iki kat.
    yigin = (g["agirlik_tampon_baba"] + g["agirlik_carpma_arasi"]
             - g["agirlik_tampon_ezilme"] + g["agirlik_paten_arasi"]
             + g["kabin_paten_arasi"])
    lh_ciz = _cizim_olcusu(g, "aski_halat_boyu")
    if lh_ciz:
        lh = float(lh_ciz)
    else:
        lh = (g["kuyu_boyu"] - yigin) / 1000.0 + O["halat_pay_m"]
        if r != 1:
            lh *= 2
    Gh = gh * lh * nh
    F1 = Q + P + Gh                       # kabin ve aksesuarlarının yükü
    #  KARŞI AĞIRLIK TEK YERDEN GELİR  ( MG.tamamla → 'karsi_agirlik' ).
    #  Burada ikinci kez  P + q·Q  hesaplansaydı, q değiştiğinde bu bölüm ile
    #  tahrik / ray / tampon bölümleri ayrışırdı — nitekim ayrışıyordu.
    Ga = g["karsi_agirlik"]               # karşı ağırlık yükü

    #  ------------------------------------------------------------------
    #  DENGESİZ ( ARTAN ) YÜK  Gmax  —  motor gücünü belirleyen büyüklük
    #  ------------------------------------------------------------------
    #  ESKİDEN:  Gmax = F1 + Gs − Ga,  yani ( 1−q )·Q + Gh.  Buradaki Gh
    #  KABİN TARAFINDAKİ TOPLAM halat kütlesidir ve dengesizlik DEĞİLDİR:
    #  kabin en alttayken karşı ağırlık tarafında da halat vardır, motoru
    #  zorlayan iki tarafın FARKIDIR.  Üç eksik vardı:
    #
    #    1) Halat dengesizliği kuyu boyu + 5 m payla hesaplanıyordu;  doğrusu
    #       SEYAHAT MESAFESİDİR ( MSR = i·H·gh·ns ).  Kısa kuyuda fazla, uzun
    #       kuyuda — hafif tablo halatıyla birleşince — EKSİK çıkıyordu.
    #    2) DENGE ZİNCİRİ hiç yoktu.  Zincir halat dengesizliğini karşılar;
    #       zincirli bir tesiste program motoru gereğinden büyük seçiyordu.
    #    3) GEZİCİ KABLO ( flexbil ) hiç girmiyordu.  Küçük ama her zaman
    #       eksi yönde:  kablo kuyu ortasından asılıdır, kabin en alttayken
    #       yarısı kabin tarafındadır.
    #
    #  Gh ve F1 OLDUĞU GİBİ KALIR:  onlar kabin tarafındaki GERÇEK yüktür ve
    #  kaide ( bölüm 2 ), halat güvenlik katsayısı ( bölüm 4 ), tahrik
    #  ( bölüm 6 ) ve Tst bunlara dayanır — dengesizlikle karıştırılmamalıdır.
    H = g["seyir_mesafesi"]                          # seyahat mesafesi, m
    MSR = r * H * gh * nh                            # dengesiz halat kütlesi
    #  DENGE ZİNCİRİ VAR / YOK.  Zincir halatı dengelemek için takılır ve
    #  halat ağırlığına göre seçilir;  bu yüzden "var" TAM DENGELEME kabulüdür
    #  ( λ = 1 ).  Zincirin metre ağırlığı sahada ölçülemediği için ofis
    #  kabulü olarak alınır — bilerek hafif seçilmiş bir zincir gerçek güç
    #  ihtiyacını bu hesabın üstüne çıkarır.  Kabul, paftada λ satırında
    #  görünür.
    lam = ((O["denge_zinciri_orani"] or 0) / 100.0
           if str(g.get("denge_zinciri") or "").strip() == "Var" else 0.0)
    MCR = lam * MSR                                  # zincirin dengelediği
    mt, mt_kaynak = _gezici_kablo(g)
    MTrav = 0.5 * H * mt                             # gezici kablo dengesizliği
    #  İKİ HAREKET YÖNÜ DE HESAPLANIR.  Motoru zorlayan yalnız "dolu kabin
    #  yukarı" değildir;  BOŞ KABİN AŞAĞI inerken motor karşı ağırlığı
    #  KALDIRIR ve o taraftaki dengesizlik  Ga − P = q·Q  kadardır.
    #
    #      dolu kabin yukarı :  ( Q + P ) − Ga  =  ( 1 − q )·Q
    #      boş  kabin aşağı  :  Ga − P          =  q·Q
    #
    #  q = 0,50'de ikisi eşittir.  Ama q ofis sabitidir ve
    #  0,2 – 0,8 arasında değiştirilebilir:  q > 0,50'de BELİRLEYİCİ OLAN
    #  İKİNCİ DURUMDUR ve program onu hiç hesaplamıyordu.  Sonuç emniyetsiz
    #  ve yönü terstir — q büyüdükçe gereken güç düşüyor görünüyordu
    #  ( q = 0,60'ta 4,36 kW;  aynadaki q = 0,40'ta 6,21 kW ).
    Gden_dolu = (Q + P) - Ga              # dolu kabin yukarı
    Gden_bos = Ga - P                     # boş kabin aşağı  ( ağırlık yukarı )
    Gden = max(Gden_dolu, Gden_bos)
    Gden_yon = "dolu kabin yukarı" if Gden_dolu >= Gden_bos else "boş kabin aşağı"
    Gmax = Gden + O["Gs"] + MSR - MCR + MTrav
    #  MİL KUVVETİ VE MOMENT ASKI ORANINA GÖRE İNDİRGENİR.
    #  2:1 palangalı bir sistemde tahrik kasnağının gördüğü kuvvet Gmax değil Gmax/i'dir —
    #  kasnak tarafındaki büyüklükler yarıya iner, halat hızı iki katına
    #  çıkar.  ( Gücü etkilemez:  N = Gmax·v / (η·102) askı oranından
    #  bağımsızdır ve doğrudur.  Ama paftadan MOMENT okuyup makine seçen bir
    #  okuyucuya iki katı bir sayı yazılıyordu. )
    #
    #  Pm, GÜCÜ VE MOMENTİ BELİRLEYEN YÜKTEN TÜRER — Pm ve M aynı çalışma
    #  durumunu anlatmalı.  F1 halatın TAMAMINI kabin tarafına koyar, yön seçmez, denge zincirini
    #  ve gezici kabloyu bilmez.  Gmax ise iki hareket yönünün büyüğünü,
    #  dengesiz halatı, zinciri ve kabloyu taşır.  Sonuç:  q = 0,60'ta paftaya
    #  "en büyük döndürme kuvveti" diye 185,7 kg basılıyor, momenti ve gücü
    #  belirleyen yük ise 269,1 kg oluyordu ( %31 az );  zincir seçimi M'yi
    #  değiştiriyor, Pm'yi değiştirmiyordu.  Pm hiçbir kontrole girmez ama
    #  paftadan okunup makine seçilir.  Artık  M = Pm × Dt/2  birebir tutar.
    Pm = Gmax / r                         # tahrik kasnağına gelen döndürme kuvveti
    M = Pm * (Dt / 2000.0)                # tahrik kasnağı momenti
    #  TAHRİK KASNAĞINA GELEN STATİK YÜK.  Kasnak iki halat kolunu birden
    #  taşır;  Pm bunların FARKI ( döndüren kuvvet ), Tst ise TOPLAMIDIR.
    #  Palangalı sistemde her kol yükün yarısını çeker, bu yüzden askı
    #  oranına bölünür:  1:1'de F1 + Ga,  2:1'de ( F1 + Ga ) / 2.
    #  İmalatçının kasnak için verdiği azami statik yük aşılmamalıdır;
    #  program bunu HİÇ denetlemiyordu — motor gücü "UYGUN" çıkan bir seçim
    #  kasnak yükünü aşmış olabilirdi.
    #
    #  DENGE ZİNCİRİ DE KASNAĞA BİNER.  Zincir kabin ile karşı ağırlık
    #  arasında asılıdır;  ağırlığı ikisine paylaşılır ve halatlar üzerinden
    #  kasnağa ulaşır.  Gmax'ta zincir dengesizliği AZALTIR ( eksi işaretli ),
    #  statik yükte ise ARTIRIR — ikisi ayrı büyüklüktür.  Zincir hesaba
    #  girmezse Tst olduğundan küçük çıkar ve kasnak yükü aşılmış bir makine
    #  "UYGUN" görünebilir;  bu EMNİYETSİZ taraftır.  Karşı ağırlık koluna
    #  eklenir ( EN 81-50 m.5.11.2'nin T2 = gn·( Mcwt + MCR )/r bağıntısı
    #  ile aynı kabul ).
    Tst_h = (F1 + Ga + MCR) / r
    Tst = g.get("makine_tst")
    Tst_verildi = isinstance(Tst, (int, float)) and not isinstance(Tst, bool) and Tst > 0
    tst_uygun = (Tst >= Tst_h) if Tst_verildi else None
    #  VERİM — makine tipine bağlı TOPLAM SİSTEM VERİMİ  ( ofis standardı ).
    #  Ofisin avan tablosuyla aynı:  dişlisiz 0,85 · dişli 0,50.  Makine
    #  tipinden bağımsız sabit bir verim dişli makinede gerekli gücü YARIYA
    #  yakın gösterirdi — emniyetsiz taraf.
    #  ASKI ORANINA BAĞLI Δη = 0,10 DÜŞÜŞÜ KALDIRILDI ( bkz. ortak/ofis.py ):
    #  askı ( palanga ) kaybı artık η'nın İÇİNDEDİR, ikinci kez inmez.  Bu
    #  yüzden "Ofis verimi η toplam sistem verimidir" anahtarı da kalktı —
    #  η her zaman toplam sistem verimidir.
    #  Projeye imalatçının verimi girilmişse o kullanılır ( MG.sistem_verimi ).
    eta, eta_girildi = MG.sistem_verimi(g)
    #  İKİNCİ KALKAN.  Girdi doğrulaması η ≤ 0'ı ve negatif halat boyunu
    #  zaten reddediyor;  motor doğrudan çağrılırsa ( testler ) sıfıra
    #  bölünmesin ve fiziksel olmayan bir güç "uygun" sayılmasın.
    hesaplanabilir = eta > 0 and lh > 0
    N = (Gmax * v / (eta * S["motor_sabiti"])) if hesaplanabilir else None
    HP = N * S["hp_carpani"] if N is not None else None
    uygun = bool(N is not None and N > 0 and g["motor_gucu"] >= N
                 and tst_uygun is not False)

    #  λ ve zincir kütlesi TEK YERDE hesaplanır ( burada ) ve tahrik bölümü
    #  buradan okur — iki yerde ayrı türetilirse ayrışırlar.
    o.update(lam=lam, MCR=MCR, MSR_dengesiz=MSR, MTrav=MTrav)
    #  ------------------------------------------------------------------
    #  P'NİN STANDARTTAKİ TANIMI  —  ray · tampon · kuyu tabanı için
    #  ------------------------------------------------------------------
    #  TS EN 81-20 P'yi HER YERDE şöyle tanımlar  ( m.5.2.1.8.5 · m.5.2.1.8.6
    #  · m.5.2.1.9 · m.5.7.2.3.2 ):
    #
    #      "P is the mass of the empty car and components supported by the
    #       car, i.e. part of the travelling cable, compensating
    #       ropes/chains (if any), etc."
    #
    #  Yani BOŞ KABİN KÜTLESİ DEĞİL:  gezici kablonun kabin tarafındaki payı
    #  ve varsa denge zinciri de P'ye dâhildir.  m.5.7.2.3.1 a) 1) yatay
    #  kuvvetlerin kaynağını sayarken bunu tekrar eder ( "compensation means,
    #  travelling cables" ), m.5.7.2.3.2 de "such as ram, part of travelling
    #  cable, compensating ropes/chains (if any) P" der.
    #
    #  Program ray, tampon ve kuyu tabanı hesaplarında düz boş kabin
    #  kütlesini kullanıyordu.  Zincirsiz kısa kuyuda eksik %2, zincirli uzun
    #  kuyuda %30'a çıkar — hep EMNİYETSİZ yönde.
    #
    #  NİÇİN AYRI BİR DEĞİŞKEN:  bölüm 1 ( motor ) ve bölüm 2 ( kaide ) P'yi
    #  BAŞKA amaçla kullanır — F1 = P+Q+Gh kabin tarafındaki gerçek yüktür,
    #  kaide yük modeli ise ofis kabulüdür ( MMO 208/4 ).  Onlara dokunulmaz.
    #
    #  ZİNCİRİN TAMAMI SAYILIR:  zincir kabin ile karşı ağırlık arasında U
    #  yapar ve payı konuma göre değişir.  Kabin en üstteyken neredeyse
    #  tamamı kabin tarafındadır — ray ve tampon en olumsuz konuma göre
    #  denetlendiği için tamamı alınır.  Karşı ağırlık rayı da KENDİ en
    #  olumsuz konumunda ( ağırlık en üstte ) aynı zinciri görür;  iki
    #  kontrol AYNI ANDA olmadığı için bu çift sayma değildir
    #  ( m.5.7.2.3.3:  "forces due to compensating ropes/chains (if any),
    #  tensioned or not" ).
    o["P_std"] = P + MCR + MTrav
    o.update(Q=Q, P=P, v=v, gh=gh, lh=lh, Gh=Gh, F1=F1, Ga=Ga, Gmax=Gmax,
             N_hesap=N, motor_uygun=uygun, r=r, nh=nh, dh=dh, Dt=Dt,
             Tst_hesap=Tst_h, Tst=Tst if Tst_verildi else None,
             tst_uygun=tst_uygun)
    o.update(eta=eta)
    _kay(o, "motor", gh=gh, lh=lh, Gh=Gh, F1=F1, Ga=Ga, Gmax=Gmax, Pm=Pm,
         M=M, eta=eta, N=N, HP=HP)

    b = Bolum("ASANSÖR MOTOR GÜCÜNÜN HESAPLANMASI", kimlik="motor_gucu", kaynak="MMO 208/7 - 2.4")
    b["adimlar"] = [
        veri("v", "Kabin hızı", v, "m/s", "GİRİŞ"),
        veri("Q", "Beyan yükü", Q, "kg", "GİRİŞ"),
        veri("P", "Boş kabin ağırlığı", P, "kg",
             g.get("kabin_agirligi_kaynak") or "GİRİŞ"),
        veri("dh", "Halat çapı", dh, "mm", "GİRİŞ"),
        veri("nh", "Halat sayısı", nh, "adet", "GİRİŞ"),
        veri("gh", "Halatın 1 m'deki ağırlığı", gh, "kg/m", gh_kaynak, 4),
    ] + ([
        #  ÇİZİMDEN:  halatın gerçek yolu ( cizim/olculer ).
        veri("lh", "Kabin tarafındaki halat boyu  ( kabin en alt durakta )", lh, "m",
             CIZIMDEN + ("  ·  tahrik kasnağından kabin kasnaklarının altından kuyu "
                         "tavanındaki bağlantıya" if r != 1 else
                         "  ·  tahrik kasnağından kabin şasesindeki bağlantıya"), 3),
    ] if lh_ciz else [
        #  YIĞIN PAFTADA AÇIK YAZILIR:  eskiden halat boyu satırında yalnız
        #  toplamı ( ör. 6.660 mm ) görünüyordu;  elle yeniden hesaplayan
        #  hangi beş ölçünün toplandığını paftadan okuyamıyordu.
        hesap("Yığın = ağırlık tamponu baba + çarpma arası − ezilme"
              " + ağırlık paten arası + kabin paten arası",
              f"{trn(g['agirlik_tampon_baba'])} + {trn(g['agirlik_carpma_arasi'])}"
              f" − {trn(g['agirlik_tampon_ezilme'])} + {trn(g['agirlik_paten_arasi'])}"
              f" + {trn(g['kabin_paten_arasi'])}",
              yigin, "mm", "KABUL  ·  halat boyu"),
        #  2:1 askıda PAY DA iki kat gider:  köşeli parantez yazılmazsa satır
        #  "… + 5 × 2" okunur ve yeniden hesaplayan sonucu bulamaz.
        hesap(("lh = [ ( Kuyu boyu − tampon/paten yığını ) / 1000 + halat payı ] × 2"
               "  ( 2:1 askı )") if r != 1 else
              "lh = ( Kuyu boyu − tampon/paten yığını ) / 1000 + halat payı",
              (f"[ ( {trn(g['kuyu_boyu'], 0)} − {trn(yigin, 0)} ) / 1000 + "
               f"{trn(O['halat_pay_m'])} ] × 2") if r != 1 else
              (f"( {trn(g['kuyu_boyu'], 0)} − {trn(yigin, 0)} ) / 1000 + "
               f"{trn(O['halat_pay_m'])}"),
              lh, "m", "KABUL  ·  halat payı"),
    ]) + [
        hesap("Gh = gh × lh × nh", f"{_trh(gh)} × {tr(lh)} × {trn(nh, 0)}",
              Gh, "kg"),
        hesap("F1 = P + Q + Gh", f"{trn(P, 0)} + {trn(Q, 0)} + {tr(Gh)}", F1, "kg"),
        hesap(f"Ga = P + {tr(O['q_denge'])} × Q",
              f"{trn(P, 0)} + {tr(O['q_denge'])} × {trn(Q, 0)}", Ga, "kg"),
        veri("Gs", "Sürtünme yükü", O["Gs"], "kg", "KABUL"),
        metin("Dengesiz  ( artan )  yükün bileşenleri :"),
        hesap("Gden₁ = ( Q + P ) − Ga        ( dolu kabin yukarı )",
              f"( {trn(Q, 0)} + {trn(P, 0)} ) − {tr(Ga)}", Gden_dolu, "kg"),
        hesap("Gden₂ = Ga − P        ( boş kabin aşağı — ağırlık kalkar )",
              f"{tr(Ga)} − {trn(P, 0)}", Gden_bos, "kg"),
        hesap("Gden = MAX ( Gden₁ ; Gden₂ )",
              f"MAX ( {tr(Gden_dolu)} ; {tr(Gden_bos)} )", Gden, "kg",
              f"belirleyici :  {Gden_yon}"),
        veri("H", "Seyir mesafesi", H, "m", "GİRİŞ"),
        hesap("MSR = i × H × gh × ns" if r != 1 else "MSR = H × gh × ns",
              (f"{trn(r, 0)} × {tr(H)} × {_trh(gh)} × {trn(nh, 0)}" if r != 1
               else f"{tr(H)} × {_trh(gh)} × {trn(nh, 0)}"), MSR, "kg",
              "dengesiz halat kütlesi  ( kabin en altta )"),
        veri("", "Denge ( kompanzasyon ) zinciri",
             "Var" if lam else "Yok", "", "GİRİŞ"),
        veri("λ", "Dengeleme oranı", lam, "—",
             f"KABUL  ·  %{trn(O['denge_zinciri_orani'], 0)}"
             if lam else "zincir yok", 2),
        hesap("MCR = λ × MSR", f"{tr(lam)} × {tr(MSR)}", MCR, "kg",
              "zincirin dengelediği kütle"),
        veri("mt", "Gezici kabloların 1 m ağırlığı", mt, "kg/m", mt_kaynak, 3),
        hesap("MTrav = 0,5 × H × mt",
              f"0,5 × {tr(H)} × {tr(mt)}", MTrav, "kg",
              "gezici kablo dengesizliği"),
        hesap("Gmax = Gden + Gs + MSR − MCR + MTrav",
              f"{tr(Gden)} + {tr(O['Gs'])} + {tr(MSR)} − {tr(MCR)} + {tr(MTrav)}",
              Gmax, "kg"),
        hesap("Pm = Gmax / i" if r != 1 else "Pm = Gmax",
              (f"{tr(Gmax)} / {trn(r, 0)}" if r != 1 else f"{tr(Gmax)}"), Pm, "kg",
              "tahrik kasnağına gelen en büyük döndürme kuvveti"),
        veri("Dt", "Tahrik kasnağı çapı", Dt, "mm", "GİRİŞ"),
        hesap("M = Pm × ( Dt / 2 )",
              f"{tr(Pm)} × {tr(Dt / 2000.0)}", M, "kg·m",
              "tahrik kasnağı momenti"),
        veri("", "Makine tipi", g.get("makine_tipi") or "—", "", "GİRİŞ"),
        veri("η", "Toplam sistem verimi  ( askı / palanga kaybı DÂHİL )", eta, "",
             "KATALOG" if eta_girildi else
             f"KABUL  ·  {g.get('makine_tipi') or 'tanınmayan tip'}"),
        hesap("N = Gmax × v / ( η × 102 )",
              f"{tr(Gmax)} × {tr(v)} / ( {tr(eta)} × 102 )",
              N, "kW", "MMO 208/7 - 2.4"),
        hesap("HP = N × 1,34", f"{tr(N)} × 1,34", HP, "HP"),
        veri("Nsç", "Kullanılan motor gücü", g["motor_gucu"], "kW", "GİRİŞ"),
        metin("Tahrik kasnağına gelen statik yük :"),
        hesap("Tst-h = ( F1 + Ga + MCR ) / i" if r != 1
              else "Tst-h = F1 + Ga + MCR",
              (f"( {tr(F1)} + {tr(Ga)} + {tr(MCR)} ) / {trn(r, 0)}" if r != 1
               else f"{tr(F1)} + {tr(Ga)} + {tr(MCR)}"), Tst_h, "kg",
              "kasnağın taşıdığı toplam yük  ( halatlar + denge zinciri )"),
    ] + ([
        veri("Tst", "Makinenin azami kasnak statik yükü", Tst, "kg",
             "KATALOG", 0),
        kontrol(f"Tst-h = {trn(Tst_h, 0)} kg  ≤  Tst = {trn(Tst, 0)} kg", bool(tst_uygun)),
    ] if Tst_verildi else [
        metin("Tst girilmediği için kasnak statik yükü DENETLENMEDİ — "
              "imalatçı kataloğundaki sınırla karşılaştırın."),
    ])
    b["aciklamalar"] = [
        "N bir GÜÇ bağıntısıdır ve güç askı oranından bağımsızdır — 2:1'de "
        "kuvvet yarıya iner, halat hızı iki katına çıkar. Askı oranı buraya "
        "yalnız TEK yoldan girer:  halat boyu ( dolayısıyla Gh ) iki katına "
        "çıkar. Verime AYRICA girmez — askı ( palanga ) kaybı η'nın "
        "içindedir ve eski Δη = 0,10 düşüşü kaldırılmıştır.",
        "Gmax, motorun yenmesi gereken EN BÜYÜK dengesiz kütledir ve İKİ "
        "HAREKET YÖNÜ karşılaştırılarak bulunur: dolu kabin yukarı çıkarken "
        "Gden₁ = ( Q + P ) − Ga = ( 1 − q )·Q, boş kabin aşağı inerken motor "
        "karşı ağırlığı kaldırır ve Gden₂ = Ga − P = q·Q olur. q = 0,50'de "
        "ikisi eşittir; q > 0,50'de BELİRLEYİCİ OLAN İKİNCİSİDİR. Seçilenin "
        "üstüne halatın iki taraf arasındaki FARKI ( MSR ) ve gezici kablonun "
        "yarısı eklenir, denge zincirinin karşıladığı kısım ( MCR ) düşülür.",
        "MSR = i·H·gh·ns:  askı oranı çarpan olarak girer çünkü 2:1'de kabin "
        "1 m indiğinde kabin tarafındaki halat 2 m uzar. Denge zinciri 1:1 "
        "asıldığı için tam dengeleme ( λ = %100 ) tam bu kütleyi ister."]
    #  PAFTAYA GİDEN TEK NOT:  ne alınacağı.  Ötekiler YÖNTEM ANLATIMIDIR ve
    #  aciklamalar'a taşındı — Bolum'ün kendi tanımı böyle ayırıyor ve ekranda
    #  ⓘ altında zaten görünüyorlar.  Dördü birden basılınca tek bir bölüm
    #  paftada yarım sayfa yöntem metni ediyordu.
    b["notlar"] = [f"Binada en az {tr(N)} kW ( {tr(HP)} HP ) gücünde makine "
                   "motor kullanılacaktır."]
    b["aciklamalar"] += [
        "Tst, kasnağın taşıdığı TOPLAM yüktür ( iki halat kolu "
        "artı denge zinciri ) ve makinenin katalog sınırıyla "
        "karşılaştırılır. Denge zinciri Gmax'ta dengesizliği "
        "AZALTIR ama statik yükte ARTIRIR — iki ayrı büyüklüktür. "
        "Makinenin kendi ağırlığı buna girmez — o, kaide "
        "hesabındadır ( bölüm 2 ).",
        "Bu güç KARARLI REJİM gücüdür:  beyan hızındaki dengesiz "
        "yükü karşılar. Kalkış ( ivmelenme ) momenti — kabin, karşı "
        "ağırlık, halat, kasnak ve rotor ataletleri — hesaba "
        "girmez; motor seçiminde üretici kalkış verisi ayrıca "
        "kontrol edilmelidir.",
        "Karşı ağırlık denge oranı q bir OFİS SABİTİDİR ( Sabitler "
        "sekmesi · varsayılan 0,50 · 0,20 – 0,80 arası ). Ga = P + q·Q "
        "TEK YERDEN kurulur; tahrik, ray ve tampon hesapları karşı "
        "ağırlığı aynı yerden okur, böylece q değiştiğinde bölümler "
        "ayrışmaz."]
    _ne = []
    if hesaplanabilir and not (N is not None and N > 0 and g["motor_gucu"] >= N):
        _ne.append("motoru büyütün")
    if tst_uygun is False:
        _ne.append("kasnak statik yükü aşıldı — makineyi büyütün")
    b["sonuc"] = {"baslik": "KONTROL      Nsç ≥ N"
                            + ("   ·   Tst-h ≤ Tst" if Tst_verildi else ""),
                  "metin": "UYGUNDUR." if uygun else
                           ("HESAP YAPILAMADI — sistem verimi ya da halat boyu "
                            "fiziksel değil" if not hesaplanabilir
                            else "UYGUN DEĞİLDİR — " + " ve ".join(_ne)),
                  "uygun": bool(uygun)}
    if not hesaplanabilir:
        b["eksik_hesap"] = b["sonuc"]["metin"]
    return b


# =====================================================================
#  2 -  MAKİNE KONSTRÜKSİYONU                   ( MMO 208/4 - m.3.4.6 )
# =====================================================================
def _makine(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    k1 = US.darbe_k1(O, g["guvenlik_tertibati"])
    #  Kabin rayları ( bölüm 7 ) aynı k1'i okur — makine dairesi olsun olmasın.
    o.update(k1=k1)
    b = Bolum("MAKİNE KONSTRÜKSİYONUNUN HESAPLANMASI", kimlik="makine_konstruksiyonu", kaynak="MMO 208/4 - m.3.4.6")
    #  MAKİNE DAİRESİZ ( MRL ) TESİSTE YALNIZ KİRİŞ HESAPLANIR.
    #  Makine dairesinde makine, tabliyeye basan bir ÇELİK KAİDEYE oturur:
    #  yatay kirişler ( yan yatak ) ve onları taşıyan kolonlar ( dikine
    #  kiriş, boyu şase yüksekliği ).  MRL'de tabliye de kolon da yoktur —
    #  makine kuyu üstündeki NPU kirişlere doğrudan oturur ( sahada genelde
    #  NPU 140 ).  Bu kirişler aynı yükü aynı statikle taşır;  kolonların
    #  burkulma kontrolü MRL'de UYGULANMAZ.  Eskiden bölüm MRL'de hiç
    #  hesaplanmıyor, makinenin altındaki kiriş hiçbir yerde denetlenmiyordu.
    #  Kirişin yükü nereye aktardığı ( raylar / bina ) bölüm 7 · 8'dedir.
    _mrl = evet_mi(g.get("mk_yok"))
    Gm, L = g["makine_agirligi"], g["yan_yatak_boyu"]
    Wx = MT.npu(g["yan_yatak"], "Wx") * 1000            # cm³ → mm³
    F = k1 * gn * (o["Q"] + o["P"] + o["Gh"] + o["Ga"] + Gm)
    F1 = F / 2.0                                        # yan yatak putreli
    #  YÜKÜN KİRİŞTEKİ YERİ çizimden ( tahrik kasnağı:  makine dairesizde
    #  ağırlık raylarına oturan kirişte, makine dairelide kaidede );  yoksa
    #  ofis kabulü:  mesnetten L − 335.
    X_ciz = _cizim_olcusu(g, "makine_yuku_x")
    X_ciz = X_ciz if (X_ciz is not None and 0 < X_ciz < L) else None
    X = float(X_ciz) if X_ciz is not None else L - O["yan_yatak_L_X"]
    FB = F1 * X / L
    FA = F1 - FB
    Mmax = FA * X
    sigma_e = Mmax / Wx
    #  σem "en çok" değeridir:  sınıra eşit gerilme de uygundur.
    #  NEGATİF GERİLME "UYGUN" SAYILMAZ:  gerilme büyüklüktür, işareti
    #  geometrinin ters dönmesinden gelir ( X < 0 ).  Yalnız "≤ σem" bakmak,
    #  −5.350 N/mm² gibi anlamsız bir değeri sessizce geçirirdi.  Girdi
    #  doğrulaması bu geometriyi zaten reddediyor;  bu ikinci kalkandır.
    egilme_uygun = 0 <= sigma_e <= O["sigma_em"]
    if not _mrl:
        L1 = g["sase_yuksekligi"]
        A = MT.npu(g["dikine_kiris"], "A") * 100            # cm² → mm²
        #  NPU tablosunun atalet YARIÇAPI ( cm ):  λ = L1 / imin bağıntısında
        #  eylemsizlik momenti değil yarıçap kullanılır.
        #
        #  BURKULMA ZAYIF EKSENDE OLUR.  Program uzun süre yalnız ix'i okuyordu;
        #  oysa bir çubuk EN KÜÇÜK atalet yarıçapına sahip
        #  eksende burkulur.  U profilinde iki eksen çok ayrışır — NPU 120'de
        #  ix = 46,2 mm ama iy = 15,9 mm'dir ( λ 23,8 yerine 69,2 ).  ix ile
        #  hesaplanan ω burkulma etkisini KÜÇÜK gösterir;  NPU 40x20 ve 50x25'te
        #  varsayılan yüklerde bile karar "UYGUN"dan "UYGUN DEĞİL"e döner.
        #
        #  ix DOĞRU OLABİLİR — ama ancak kiriş zayıf eksende MESNETLİYSE.  Bu bir
        #  KABULDÜR ve sessizce yapılamaz:  şase yanal bağlıysa ofis bunu
        #  "kaide_zayif_eksen_mesnetli" anahtarıyla AÇIKÇA beyan eder ve ω yine
        #  ix'ten hesaplanır.  Beyan yoksa emniyetli taraf olan min( ix ; iy )
        #  kullanılır.
        _ix = MT.npu(g["dikine_kiris"], "ix") * 10          # cm → mm
        _iy = MT.npu(g["dikine_kiris"], "iy") * 10          # cm → mm
        _mesnetli = bool(O["kaide_zayif_eksen_mesnetli"])
        imin = _ix if _mesnetli else min(_ix, _iy)
        _eksen = "ix  ( zayıf eksen mesnetli )" if _mesnetli else (
            "ix" if _ix <= _iy else "iy  ( zayıf eksen )")
        lam_ham = L1 / imin
        lam = max(20, math.ceil(lam_ham - 1e-9))
        #  Kaide kirişi ST 37'dir ( σem = 130 ) — ω'nın Rm = 370 eğrisi geçerli.
        omega = MT.omega_en8150(lam, MT.OMEGA_RM_ALT)
        sigma_b = FB * omega / A if omega else None
        burkulma_uygun = (sigma_b is not None and 0 <= sigma_b <= O["sigma_em"])
        #  σem de kaydedilir:  hükmün sınırıdır ve ofis sabitidir.
        _kay(o, "makine", k1=k1, A=A, imin=imin, Wx=Wx, omega=omega,
             sigma_em=O["sigma_em"], F=F, F1=F1, X=X, FB=FB, FA=FA, Mmax=Mmax,
             sigma_e=sigma_e, lam_ham=lam_ham, lam=lam, sigma_b=sigma_b)
    else:
        burkulma_uygun = True
        _kay(o, "makine", k1=k1, Wx=Wx, sigma_em=O["sigma_em"], F=F, F1=F1, X=X,
             FB=FB, FA=FA, Mmax=Mmax, sigma_e=sigma_e)
    b["adimlar"] = ([
        metin("MAKİNE DAİRESİZ ( MRL ) — makine kuyu üstündeki NPU kirişlere "
              "oturur;  tabliye ve kolon ( dikine kiriş ) yoktur, burkulma "
              "kontrolü uygulanmaz.", vurgu=True),
    ] if _mrl else []) + [
        veri("k1", "Darbe katsayısı", k1, "",
             f"KABUL  ·  {g['guvenlik_tertibati']}"),
        veri("Gm", "Makine motor ağırlığı", Gm, "kg", "KATALOG"),
        veri("L", "Yan yatak ( makine kirişi ) boyu", L, "mm", "GİRİŞ"),
    ] + ([] if _mrl else [
        veri("L1", "Dikine kirişin boyu", L1, "mm", "GİRİŞ"),
        veri("A", "Dikine kirişin kesit alanı", A, "mm²",
             f"NPU {g['dikine_kiris']}", 0),
        veri("imin", "Dikine kirişin en küçük atalet yarıçapı", imin, "mm",
             f"NPU {g['dikine_kiris']}  ·  {_eksen}"),
    ]) + [
        veri("Wx", "Yan yatağın mukavemet momenti", Wx, "mm³",
             f"NPU {g['yan_yatak']}", 0),
        veri("σem", "Emniyet gerilmesi ( ST 37 )", O["sigma_em"], "N/mm²", "KABUL"),
        metin("Makine kirişlerine gelen en büyük kuvvet :" if _mrl
              else "Kaide üzerindeki en büyük kuvvet :"),
        hesap("F = k1 × gn × ( Q + P + Gh + Ga + Gm )",
              f"{tr(k1)} × {tr(gn)} × ( {trn(o['Q'], 0)} + {trn(o['P'], 0)} + "
              f"{tr(o['Gh'])} + {tr(o['Ga'])} + {trn(Gm, 0)} )", F, "N"),
        metin("Yan yatak putreline gelen kuvvet :"),
        hesap("F1 = F / 2", f"{tr(F)} / 2", F1, "N"),
        (veri("X", "Makine yükünün ( tahrik kasnağının ) mesnetten uzaklığı", X, "mm",
              CIZIMDEN + ("  ·  kirişler karşı ağırlık raylarına oturur" if _mrl
                          else "  ·  kaidenin yan yatağında"), 0)
         if X_ciz is not None else
         hesap("X = L − 335", f"{trn(L, 0)} − {O['yan_yatak_L_X']}", X, "mm")),
        hesap("FB = F1 × X / L", f"{tr(F1)} × {trn(X, 0)} / {trn(L, 0)}", FB, "N"),
        hesap("FA = F1 − FB", f"{tr(F1)} − {tr(FB)}", FA, "N"),
        metin("Makine kirişlerinde eğilme momenti ve gerilmesi :" if _mrl
              else "Kaide yatay kirişlerinde eğilme momenti ve gerilmesi :"),
        hesap("Mmax = FA × X", f"{tr(FA)} × {trn(X, 0)}", Mmax, "N·mm", ondalik=0),
        hesap("σe = Mmax / Wx", f"{trn(Mmax, 0)} / {trn(Wx, 0)}", sigma_e, "N/mm²"),
        kontrol(f"σe = {tr(sigma_e)}  ≤  σem = {tr(O['sigma_em'])} N/mm²  →  "
                f"NPU {g['yan_yatak']}", egilme_uygun),
    ] + ([] if _mrl else [
        metin("Dikine kirişlerin bükülme kontrolü :"),
        hesap("λ = L1 / imin", f"{trn(L1, 0)} / {tr(imin)}", lam_ham, ""),
        veri("λ", "Yuvarlanmış burkulma narinliği ( en az 20 )", lam, "",
             "ω çizelgesi tam sayı λ ile okunur", 0),
        veri("ω", "Omega değeri", omega, "", f"Burkulma tablosu  λ = {lam}", 4),
        hesap("σb = FB × ω / A",
              f"{tr(FB)} × {tr(omega)} / {trn(A, 0)}", sigma_b, "N/mm²"),
        kontrol(f"σb = {tr(sigma_b)}  ≤  σem = {tr(O['sigma_em'])} N/mm²  →  "
                f"NPU {g['dikine_kiris']}", burkulma_uygun),
    ])
    b["sonuc"] = {"baslik": ("KONTROL      σe ≤ σem  ( makine kirişleri )" if _mrl
                             else "KONTROL      σe ≤ σem   ve   σb ≤ σem"),
                  #  HANGİ KİRİŞİN DÜŞTÜĞÜ YAZILIR.  "Kiriş kesitini
                  #  büyütün" iki ayrı eleman için aynı cümleydi:  yan
                  #  yatak eğilmeden ( σe ), dikine kiriş burkulmadan
                  #  ( σb ) düşer ve büyütülecek profil farklıdır.
                  "metin": ("UYGUNDUR." if (egilme_uygun and burkulma_uygun)
                            else "UYGUN DEĞİLDİR — " + "  ·  ".join(
                                ([f"yan yatak ( NPU {g['yan_yatak']} ) eğilmeden "
                                  f"düşüyor:  σe = {tr(sigma_e)} > σem = "
                                  f"{tr(O['sigma_em'])} N/mm²"]
                                 if not egilme_uygun else [])
                                + ([f"dikine kiriş ( NPU {g['dikine_kiris']} ) "
                                    + (f"burkulmadan düşüyor:  σb = "
                                       f"{tr(sigma_b)} > σem = "
                                       f"{tr(O['sigma_em'])} N/mm²"
                                       if sigma_b is not None else
                                       #  σb yoksa "aşıyor" DENMEZ:  ω
                                       #  çizelgesi λ aralığı dışında kalmış,
                                       #  hesap hiç yapılamamıştır.
                                       f"için burkulma denetlenemedi:  λ = "
                                       f"{trn(lam, 0)} , ω çizelgesi "
                                       f"{MT.OMEGA_LAMBDA_MIN} … "
                                       f"{MT.OMEGA_LAMBDA_MAX} arasını kapsar")]
                                   if not burkulma_uygun else []))),
                  "uygun": bool(egilme_uygun and burkulma_uygun)}
    b["aciklamalar"] = [
        "Kiriş statiği:  açıklığı L olan basit kirişte, A mesnedinden X "
        "uzaktaki tekil yük için  FA = F1·(L−X)/L,  FB = F1·X/L,  "
        "Mmax = FA·X."
        + ("  Makine dairesiz tesiste makine kirişleri kuyu üstünde doğrudan "
           "mesnetlenir;  kolon olmadığı için burkulma kontrolü yapılmaz."
           if _mrl else
           "  Burkulmada σb = FB·ω/A ( omega yöntemi ) ve "
           "λ = L1/imin — yani burkulma boyu Lk = L1 alınır, iki ucu mafsallı "
           "kabulüdür ( β = 1,0 ).  Kolon tek ucundan ankastre, öbür ucu "
           "serbestse bu kabul narinliği OLDUĞUNDAN KÜÇÜK gösterir.")]
    if not _mrl:
        b["aciklamalar"] += [
            "imin, profilin İKİ EKSENİNİN EN KÜÇÜĞÜDÜR:  çubuk zayıf eksende "
            "burkulur.  U profilinde iki eksen çok ayrışır ( NPU 120: ix = 46,2 "
            "mm · iy = 15,9 mm ).  Yalnız ix ile hesaplamak ω'yı ve dolayısıyla "
            "σb'yi OLDUĞUNDAN KÜÇÜK gösterir.  Şase kirişi zayıf eksende yanal "
            "mesnetliyse ix geçerlidir;  bu bir KABULDÜR ve Sabitler sekmesindeki "
            "'Kaide zayıf ekseni mesnetli' anahtarıyla açıkça beyan edilir."]
    #  İKİSİ DE YÖNTEM ANLATIMI — paftaya değil, ekrandaki ⓘ'ye.
    b["aciklamalar"] += [
        "Darbe katsayısı k1 ve emniyet gerilmesi σem OFİS KABULLERİDİR "
        "( Sabitler sekmesinden değiştirilir ). TS EN 81-20 makine kaidesi için yük "
        "modeli vermez — Çizelge 14 (k1·k2·k3) o standartta açıkça KILAVUZ "
        "RAY hesabına aittir. Buradaki kullanım ödünçtür ve emniyetli "
        "taraftadır:  k1 makinenin kendi ağırlığına da uygulanır ve σem, "
        "aynı standardın ST 37 için verdiği Rm/1,8 = 205,6 N/mm²'nin "
        "yaklaşık yarısıdır. Sonuç, kirişin gereğinden kalın çıkmasıdır.",
        "Güvenlik tertibatı tipi bu bölümü doğrudan büyütür ( k1 = 2 · 3 · 5 ): "
        "ani frenlemeli tertibatta kaide yükü kaymalıya göre 2,5 kat çıkar. "
        "Kesit bu yüzden UYGUN DEĞİL çıkıyorsa, ofis kabulü gözden "
        "geçirilmeli — standart bu katsayıyı burada zorunlu kılmaz."]
    return b


# =====================================================================
#  3 -  KULLANILABİLİR KABİN ALANI              ( TS EN 81-20 m.5.4.2 )
# =====================================================================
def _kabin_alani(g, o):
    Q = g["beyan_yuku"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]
    azami = MT.kabin_azami_alan(Q)
    kisi_yuk = MT.kabin_kisi(Q)
    alan = (W * D) / 1e6
    pervaz = g["uzun_pervaz"]
    #  TS EN 81-20 m.5.4.2.1.3'ün son fıkrası, kapı kasası dikmeleri arasındaki
    #  girinti için İKİ KURAL verir:
    #      a)  derinlik ≤ 100 mm  →  alana HİÇ katılmaz;
    #      b)  derinlik > 100 mm  →  "the TOTAL available area shall be
    #          included in the floor area" — girintinin TAMAMI katılır.
    #  Yalnız kapı genişliğinin yarısını katmak ( 900 mm kapı + 300 mm
    #  pervazda 0,1350 m²;  tamı 0,2700 m² ) alanı küçük gösterir — EMNİYETSİZ
    #  yöndür, Çizelge 6'nın izin verdiğinden büyük bir kabine izin verilir.
    #  Eşik de standardındır:  "≤ 100 mm hariç", 100 mm'nin kendisi dahil değil.
    girinti_var = pervaz > 100
    if girinti_var:
        alan += (g["kapi_genisligi"] * pervaz) / 1e6
    ust_uygun = azami is not None and azami >= alan
    #  YOLCU SAYISI İKİ SINIRIN KÜÇÜĞÜDÜR  ( TS EN 81-20 m.5.4.2.3.1 ):
    #      a)  Q / 75, aşağı yuvarlanır;   b)  Çizelge 8.
    #  Çizelge 8 bir RET ölçütü DEĞİLDİR.  Program eskiden onu "kabin alanı ≥
    #  en küçük alan" diye denetliyor ve alanı küçük kabine UYGUN DEĞİL
    #  diyordu;  standart ise o kabini uygun sayar ve üzerine daha az kişi
    #  yazdırır ( m.5.4.2.3.2 e ).  Örnek:  1000 kg · 1,95 m² → Q/75 = 13,
    #  Çizelge 8 = 11 → kabine 11 kişi yazılır.  Tek gerçek alt sınır tek
    #  kişiliktir:  0,28 m²'nin altındaki kabin hiç yolcu taşıyamaz.
    kisi_alan = MT.cizelge8_kisi(alan)
    kisi = min(kisi_yuk, kisi_alan) if kisi_yuk is not None else None
    yolcu_var = kisi is not None and kisi >= 1
    asgari = MT.cizelge8_alan(kisi if yolcu_var else 1)
    o.update(kabin_alani=alan, kabin_kisi=kisi)
    _kay(o, "kabin_alani", alan=alan, azami=azami, kisi=kisi, asgari=asgari)

    b = Bolum("KULLANILABİLİR KABİN ALANI", kimlik="kabin_alani", kaynak="TS EN 81-20 m.5.4.2")
    b["adimlar"] = [
        veri("Q", "Beyan yükü", Q, "kg", "GİRİŞ"),
        veri("", "Kabin genişliği × derinliği", f"{trn(W, 0)} × {trn(D, 0)} mm"),
        hesap("Kabin alanı = ( genişlik × derinlik ) / 10⁶"
              + ("  +  ( kapı genişliği × uzun pervaz ) / 10⁶"
                 if girinti_var else ""),
              f"( {trn(W, 0)} × {trn(D, 0)} ) / 10⁶"
              + (f" + ( {trn(g['kapi_genisligi'], 0)} × {trn(pervaz, 0)} ) / 10⁶"
                 if girinti_var else
                 f"   ( pervaz {trn(pervaz, 0)} mm ≤ 100 mm — girinti alana katılmaz )"),
              alan, "m²", "TS EN 81-20 m.5.4.2.1.3", 4),
        veri("", f"{trn(Q, 0)} kg için kullanılabilir EN BÜYÜK kabin alanı",
             azami, "m²", "EN 81-20 Çizelge 6"),
        kontrol(f"Kabin alanı {tr(alan)} m²  ≤  {tr(azami)} m²", ust_uygun),
        metin("Kabindeki yolcu sayısı  ( TS EN 81-20 m.5.4.2.3.1 ) :", vurgu=True),
        hesap("a)  Q / 75  ( aşağı yuvarlanır )", f"{trn(Q, 0)} / 75", kisi_yuk, "kişi",
              "m.5.4.2.3.1 a)", 0),
        hesap("b)  Kabin alanının taşıyabileceği yolcu",
              f"{tr(alan)} m²  ≥  {tr(MT.cizelge8_alan(kisi_alan)) if kisi_alan else '0,28'} m²",
              kisi_alan, "kişi", "EN 81-20 Çizelge 8  ·  20 kişiden sonra + 0,115 m² / kişi", 0),
        hesap("Yolcu sayısı = MIN ( a ; b )", f"MIN ( {trn(kisi_yuk, 0)} ; {trn(kisi_alan, 0)} )",
              kisi, "kişi", "kabine yazılacak sayı  ( m.5.4.2.3.2 e )", 0),
        kontrol(f"Kabin alanı {tr(alan)} m²  ≥  {tr(asgari)} m²  ( tek kişilik en küçük alan )",
                yolcu_var) if not yolcu_var else
        veri("", f"{trn(kisi, 0)} kişi için kullanılabilir en küçük alan", asgari, "m²",
             "EN 81-20 Çizelge 8"),
    ]
    b["sonuc"] = {"baslik": "KONTROL      Akabin  ≤  Amax   ·   yolcu = MIN ( Q/75 ; Çizelge 8 )",
                  "metin": ((f"UYGUNDUR  —  kabine {trn(kisi, 0)} kişi yazılır."
                             if yolcu_var else
                             "UYGUN DEĞİLDİR — kabin tek kişilik en küçük alanın "
                             "( 0,28 m² ) altında")
                            if ust_uygun else
                            "UYGUN DEĞİLDİR — kabin alanı beyan yüküne göre büyük"),
                  "uygun": bool(ust_uygun and yolcu_var)}
    return b


# =====================================================================
#  4 -  ASKI HALATLARI                           ( TS EN 81-50 m.5.12 )
# =====================================================================
#  BELGEYLE KABUL EDİLEN SINIRIN hükmü ( halat çapı < 8 mm · D/d < 40 ).
#  "UYGUN" ile başlar ki okuyan bunu ret sanmasın.
BELGEYLE_UYGUN = "BELGEYLE UYGUN"


def _aski_halatlari(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    Dt, dh, nh, r = o["Dt"], o["dh"], o["nh"], o["r"]
    Dp = g["saptirma_kasnak_capi"]                       # ORTALAMA — Kp için
    #  Ds — EN KÜÇÜK kasnak çapı.  m.5.5.2.1'in D/dr ≥ 40 sınırı HER kasnak
    #  için geçerlidir;  Kp = (Dt/Dp)⁴ ise ortalama bükülme şiddetidir.
    #  Boşsa çizimden gelir ( en küçük çizilen kasnak — MG.tamamla );  çizim
    #  de veremiyorsa ortalamaya düşülür.
    Ds = g.get("saptirma_kasnak_min_capi")
    Ds_verildi = _pozitif(Ds)
    Ds = float(Ds) if Ds_verildi else Dp
    oran = Dt / dh
    #  40 SINIRI BELGEYLE AŞILABİLİR  ( bkz. MG.ALANLAR · kasnak_belgesi ).
    #  Standart oranı ayrı tutulur ki pafta sınırın mı sağlandığını yoksa
    #  belgeye mi dayanıldığını ayırt edebilsin.  Sf'ye dokunulmaz.
    belge = g.get("kasnak_belgesi") == "Var"
    oran_std = oran >= S["Dt_dh_asgari"]
    oran_uygun = oran_std or belge
    #  HALAT ÇAPI ≥ 8 mm  ( m.5.5.1.2 a) ) — AYNI BELGEYLE AŞILIR.  6,5 mm gibi
    #  ince halatlar sahada yaygındır ama standardın dışındadır;  küçük
    #  kasnakla birlikte tek bir onaylanmış kuruluş belgesiyle kullanılır.
    #  Şart hiç denetlenmiyordu:  400 mm kasnakta 6 mm halat, belgesiz,
    #  "UYGUNDUR" çıkıyordu ( ⓘ açıklaması 8 mm diyordu ).
    cap_std = dh >= S["halat_capi_asgari"]
    cap_uygun = cap_std or belge

    #  Nps boşsa ASKI ORANINDAN gelir ( TS EN 81-50 Ek E — bkz. MG ).
    Nps, Nps_girildi = MG.kasnak_tek_yon(g)
    Npr = g["kasnak_ters_yon"]
    #  SAPTIRMA KASNAĞI DA m.5.5.2.1 KAPSAMINDADIR.
    #  Madde oranı "kasnak, makara ve tamburlar" için ister;  tahrik kasnağına
    #  özel değildir.  Yalnız Dt sınanırsa Dp hesaba SADECE Kp = (Dt/Dp)⁴
    #  olarak girer ve Dt/dh = 50 ama Dp/dh = 30 olan bir tesis "UYGUN" çıkar.
    #  Kasnak yoksa ( Nps = Npr = 0 ) ortada denetlenecek kasnak da yoktur.
    kasnak_var = (Nps or 0) + (Npr or 0) > 0
    oran_p = Ds / dh
    oran_p_std = oran_p >= S["Dt_dh_asgari"]
    oran_p_uygun = (not kasnak_var) or oran_p_std or belge

    def _sinir_kontrol(ifade, std, esik):
        """Standart sınırı:  sağlanıyorsa UYGUN, sağlanmıyorsa belgeyle kabul
        ya da UYGUN DEĞİL."""
        if std or not belge:
            return kontrol(f"{ifade}  ≥  {esik}", std)
        return kontrol(f"{ifade}  <  {esik}  —  onaylanmış kuruluş belgesiyle",
                       True, BELGEYLE_UYGUN)

    def _dd_kontrol(ad, deger, std):
        return _sinir_kontrol(f"{ad} = {tr(deger)}", std, S["Dt_dh_asgari"])

    _cap_esik = f"{trn(S['halat_capi_asgari'], 0)} mm"
    #  Belge satırı HANGİ maddeden sapıldığını yazar;  belge beyan edilmiş ama
    #  hiçbir sınır aşılmamışsa bunu da söyler.
    _sapmalar = ([] if cap_std else ["m.5.5.1.2"]) + (
        [] if (oran_std and (oran_p_std or not kasnak_var)) else ["m.5.5.2.1"])
    _belge_kaynagi = "GİRİŞ  ·  " + (
        f"{' ve '.join(_sapmalar)}'den sapma  ·  2014/33/AB Ek-I 1.3"
        if _sapmalar else "standart sınırları zaten sağlanıyor")

    def _belgeli_sinirlar_metni():
        """Belgeyle aşılabilen sınırlar ( çap · D/d ) TEK cümlede:  ne eksik,
        standarda nasıl uyulur, ya da belge.  Eskiden her sınır kendi
        cümlesini kuruyor ve 240 mm kasnakta 6,5 mm halata "halat çapını
        küçültün" diyordu — standardın öbür şartını çiğneten bir öğüt."""
        sorun = ([f"dh = {trn(dh, 1)} mm < {_cap_esik}"] if not cap_uygun else []) + (
            [f"Dt/dh = {tr(oran)} < {trn(S['Dt_dh_asgari'], 0)}"] if not oran_uygun else []) + (
            [f"Ds/dh = {tr(oran_p)} < {trn(S['Dt_dh_asgari'], 0)}"] if not oran_p_uygun else [])
        if not sorun:
            return None
        #  STANDARDA UYAN EN YAKIN ÇİFT:  halat en az 8 mm, her kasnak 40 × halat.
        d_std = max(dh, S["halat_capi_asgari"])
        D_std = S["Dt_dh_asgari"] * d_std
        kasnaklar = [ad for ad, D, denetle in (("tahrik kasnağı", Dt, True),
                                               ("saptırma kasnağı", Ds, kasnak_var))
                     if denetle and D < D_std - 1e-9]
        parca = ([f"en az {_cap_esik} halat"] if not cap_std else []) + (
            [f"en az {trn(D_std, 0)} mm "
             + ("kasnak" if len(kasnaklar) > 1 else kasnaklar[0])] if kasnaklar else [])
        #  Halat 8 mm'nin üstündeyse İNCELTMEK de bir yoldur — yeter ki 8 mm'nin
        #  altına inmeden oranı tuttursun.
        D_kucuk = min([Dt] + ([Ds] if kasnak_var else []))
        d_ince = D_kucuk / S["Dt_dh_asgari"]
        incelt = cap_std and d_ince >= S["halat_capi_asgari"] and d_ince < dh
        return (" · ".join(sorun) + ":  " + " ve ".join(parca) + " kullanın"
                + (f", halatı en çok {trn(d_ince, 1)} mm'ye inceltin" if incelt else "")
                + " ya da onaylanmış kuruluş belgesini beyan edin")
    #  Nequiv(t) OFİS AÇILARINDAN HESAPLANIR  ( EN 81-50 Çizelge 2 ).
    #  Kanalın ADINA bağlı sabit bir tablo kullanılsaydı ofis sabiti γ = 45°
    #  yapılsa bile Nequiv(t) 12 kalır, pafta γ = 38° yazmayı sürdürürdü — hesabın bölüm 6'da kullandığı sayı ile paftaya basılan
    #  sayı ayrışıyordu.
    sekil = g["kanal_sekli"]
    #  γ ve β TEK KAYNAKTAN:  projeye girilmişse o, yoksa ofis ( MG ).
    #  Nequiv(t) de AYNI açılardan okunur — eskiden doğrudan ofis sabitinden
    #  okunuyordu;  projeye girilen γ yalnız tahrike işleseydi pafta kendi
    #  içinde çelişirdi ( bölüm 4'te 38°, bölüm 6'da 50° ).
    gama, beta, gama_girildi, beta_girildi = MG.kanal_acilari(g, O)
    _g_ofis = O["kanal_gama_yd"] if MT.kanal_yarim_daire_mi(sekil) else O["kanal_gama_v"]
    Nequiv_t = MT.kanal_nequiv_t(sekil, gama if gama_girildi else _g_ofis,
                                 beta if beta_girildi else O["kanal_beta"])
    _gh4, Tmin, _gh4_kaynak, Tmin_kaynak = _halat_verisi(g)
    nh_uygun = nh >= 2 and float(nh).is_integer()
    Smin = 16 if nh == 2 else 12
    Kp = (Dt / Dp) ** 4
    Nequiv_p = Kp * (Nps + 4 * Npr)
    Nequiv = Nequiv_t + Nequiv_p
    #  EN 81-50 m.5.12 halat güvenlik katsayısı
    Sf = 10 ** (2.6834 - (math.log10(695.85e6 * Nequiv / oran ** 8.567)
                          / math.log10(77.09 * oran ** -2.894)))
    Fmax = gn * o["F1"] / r
    Sger = nh * Tmin / Fmax
    sinir = max(Sf, Smin)
    #  "Sf ≥ Smin" BİR GEÇME ÖLÇÜTÜ DEĞİLDİR  ( m.5.5.2.2:  ölçüt
    #  S ≥ max( Sf ; Smin ) ).  Belirleyici olanın hangisi olduğunu söyler.
    belirleyici = "Sf  ( EN 81-50 m.5.12 )" if Sf >= Smin else \
                  f"Smin = {trn(Smin, 0)}  ( EN 81-20 m.5.5.2.2 )"
    s_uygun = Sger >= sinir
    o.update(Sf=Sf, S_gercek=Sger)
    _kay(o, "aski", oran=oran, Nequiv_t=Nequiv_t, Tmin=Tmin, Smin=Smin, Kp=Kp,
         Nequiv_p=Nequiv_p, Nequiv=Nequiv, Sf=Sf, S=Sger)

    b = Bolum("ASKI HALATLARININ HESAPLANMASI", kimlik="aski_halatlari", kaynak="TS EN 81-50 m.5.12")
    b["adimlar"] = [
        #  PAFTADA KONTROL SATIRI YALNIZ KARARINI BASAR ( "UYGUN" ).  Neyin
        #  kontrolü olduğunu ÖNÜNDEKİ değer satırı söyler;  o olmadan pafta
        #  bölümün başında bağlamsız bir "UYGUN" gösteriyordu.
        metin("Askı halatı sayısı  ( TS EN 81-20 m.5.5.1.3 ) :"),
        veri("nh", "Askı halatı adedi", nh, "adet", "GİRİŞ", 0),
        kontrol(f"Askı halatı adedi nh = {tr(nh)} ≥ 2  ( TS EN 81-20 m.5.5.1.3 )", nh_uygun),
    ] + ([
        veri("", MG.ALAN["kasnak_belgesi"][1], "Var", "", _belge_kaynagi),
    ] if belge else []) + [
        metin("Askı halatı çapı  ( TS EN 81-20 m.5.5.1.2 a) ) :"),
        veri("dh", "Askı halatı anma çapı", dh, "mm", "GİRİŞ", 1),
        _sinir_kontrol(f"dh = {trn(dh, 1)} mm", cap_std, _cap_esik),
        metin("Tahrik kasnağı & askı halatı oranı  ( TS EN 81-20 m.5.5.2.1 ) :"),
        hesap("Dt / dh", f"{trn(Dt, 0)} / {tr(dh)}", oran, ""),
        _dd_kontrol("Dt / dh", oran, oran_std),
    ] + ([
        veri("Ds", "Kasnakların EN KÜÇÜK çapı", Ds, "mm",
             _kaynak(g, "saptirma_kasnak_min_capi") if Ds_verildi else "ortalama çap kullanıldı", 0),
        hesap("Ds / dh", f"{trn(Ds, 0)} / {tr(dh)}", oran_p, ""),
        _dd_kontrol("Ds / dh", oran_p, oran_p_std),
    ] if kasnak_var else [
        metin("Tahrik kasnağı dışında kasnak yok  ( Nps = Npr = 0 ) — "
              "saptırma kasnağı oranı denetlenmedi."),
    ]) + [
        metin("Halat güvenlik katsayısının hesaplanması :"),
        veri("", "Kanal tipi", sekil),
        veri("γ", "Kanal açısı  ( hesapta kullanılan )", gama, "°",
             "KATALOG  ·  kasnak föyü" if gama_girildi else
             ("KABUL  ·  " + ("yarım daire" if MT.kanal_yarim_daire_mi(sekil)
                              else "V kanal")), 0),
        veri("β", "Alt kesilme açısı", beta, "°",
             ("KATALOG  ·  kasnak föyü" if beta_girildi else "KABUL")
             if MT.kanal_alti_kesik_mi(sekil) else "alt kesilme yok", 0),
        veri("Nequiv(t)", "Kasnakların eşdeğer sayısı", Nequiv_t, "",
             "EN 81-50 Çizelge 2  ·  "
             + (f"β = {trn(beta, 0)}°" if MT.kanal_alti_kesik_mi(sekil)
                else (f"γ = {trn(gama, 0)}°" if not MT.kanal_yarim_daire_mi(sekil)
                      else "alt kesilmesiz yarım daire"))
             + (f"  ×  {trn(MT.kanal_gecis_sayisi(sekil), 0)} geçiş"
                if (MT.kanal_gecis_sayisi(sekil) or 1) > 1 else ""), 2),
        veri("Nps", "Tek yönde bükülmeli kasnak sayısı", Nps, "adet",
             (CIZIMDEN + "  ·  çizilen kasnaklar  ·  TS EN 81-50 Ek E"
              if "kasnak_tek_yon" in (g.get("_cizimden") or {}) else "GİRİŞ") if Nps_girildi else
             f"askı oranından  ·  TS EN 81-50 Ek E Şekil E.{2 if r == 1 else 1}", 0),
        veri("Npr", "Ters yönde bükülmeli kasnak sayısı", Npr, "adet",
             _kaynak(g, "kasnak_ters_yon"), 0),
        veri("Dp", "Tahrik kasnağı hariç kasnakların ortalama çapı", Dp, "mm",
             _kaynak(g, "saptirma_kasnak_capi")),
        #  ORAN GÖSTERİMİYLE BASILIR.  Çıplak "2" okuyan, 2:1 mi 1:2 mi
        #  olduğunu ayırt edemiyordu;  n : 1 sektör gösterimidir ve avan
        #  paftası zaten böyle basıyor ( tablolar.aski_orani_metni ).
        veri("r", "Halat askı oranı", f"{trn(r, 0)} : 1", "", "GİRİŞ"),
        veri("Tmin", "Halatın en küçük kopma değeri", Tmin, "N", Tmin_kaynak, 0),
        veri("Smin", "Asgari halat güvenlik katsayısı", Smin, "",
             "EN 81-20 m.5.5.2.2  ( nh = 2 ise 16 )", 0),
        hesap("Kp = ( Dt / Dp )⁴", f"( {trn(Dt, 0)} / {trn(Dp, 0)} )⁴", Kp, "", ondalik=4),
        hesap("Nequiv(p) = Kp × ( Nps + 4 × Npr )",
              f"{tr(Kp)} × ( {trn(Nps, 0)} + 4 × {trn(Npr, 0)} )", Nequiv_p, "",
              "EN 81-50 m.5.12.2"),
        hesap("Nequiv = Nequiv(t) + Nequiv(p)",
              f"{tr(Nequiv_t)} + {tr(Nequiv_p)}", Nequiv, ""),
        hesap("Sf = 10^[ 2,6834 − log( 695,85·10⁶ · Nequiv / (Dt/dh)^8,567 ) "
              "/ log( 77,09 · (Dt/dh)^−2,894 ) ]",
              f"Nequiv = {tr(Nequiv)} ,  Dt/dh = {tr(oran)}", Sf, "",
              "EN 81-50 m.5.12"),
        veri("", "Belirleyici asgari güvenlik katsayısı", belirleyici, "",
             f"max( Sf = {tr(Sf)} ; Smin = {trn(Smin, 0)} ) = {tr(sinir)}"),
        hesap("S = nh × Tmin / Fmax        ( Fmax = gn × F1 / r )",
              f"{trn(nh, 0)} × {trn(Tmin, 0)} / ( {tr(gn)} × {tr(o['F1'])} / {trn(r, 0)} )",
              Sger, ""),
        kontrol(f"S = {tr(Sger)}  ≥  max( Sf ; Smin ) = {tr(sinir)}", s_uygun),
    ]
    #  Belgeyle aşılabilen sınırlar GRUP olarak yazılır ve "( ya da belge )"
    #  bir kez eklenir:  her sınıra ayrı eklenince başlık iki satıra taşıyor,
    #  "S ≥ max( Sf ; Smin )" ortadan bölünüyordu.
    _dd_esik = trn(S["Dt_dh_asgari"], 0)
    _belgeli = " · ".join([f"dh ≥ {_cap_esik}", f"Dt/dh ≥ {_dd_esik}"]
                          + ([f"Ds/dh ≥ {_dd_esik}"] if kasnak_var else []))
    _uygun = nh_uygun and cap_uygun and oran_uygun and oran_p_uygun and s_uygun
    b["sonuc"] = {"baslik": (f"KONTROL      {_belgeli}"
                             + ("  ( ya da belge )" if belge else "")
                             + "   ·   S ≥ max( Sf ; Smin )"),
                  "metin": "UYGUNDUR." if _uygun
                           else ("UYGUN DEĞİLDİR — "
                                 + " ve ".join(
                                     [m for m in [_belgeli_sinirlar_metni()] if m]
                                     + (["en az iki bağımsız askı halatı kullanın"] if not nh_uygun else [])
                                     + (["halat çapını / adedini artırın"]
                                        if not s_uygun else []))),
                  "uygun": bool(_uygun)}
    b["notlar"] = []
    _iki_cap = []
    if kasnak_var:
        #  YÖNTEM ANLATIMI — paftaya değil ekrandaki ⓘ'ye.  Uygulanabilir
        #  öğüdü ( "Ds'yi girin" ) zaten Ds satırının kaynak kolonunda yazılı.
        _iki_cap.append(
            "İKİ AYRI ÇAP KULLANILIR:  Kp = (Dt/Dp)⁴ ORTALAMA çapı ister "
            "( ortalama bükülme şiddeti ), m.5.5.2.1'in D/dr ≥ "
            f"{trn(S['Dt_dh_asgari'], 0)} sınırı ise HER kasnak için geçerli "
            "olduğundan EN KÜÇÜK çapa ( Ds ) uygulanır. Ds girilmezse "
            "ortalamaya düşülür;  çapları farklı bir askı düzeninde Ds'yi "
            "mutlaka girin — ortalama sınırı geçse de tek bir küçük kasnak "
            "geçemiyor olabilir.")
    if r > 1 and Nps < 2:
        b["notlar"] += [
            "⚠ Palangalı ( " + trn(r, 0) + ":1 ) sistemde halatın en olumsuz "
            "kesiti genelde tahrik kasnağı + EN AZ İKİ kabin kasnağı üzerinden "
            "geçer ( EN 81-50 Ek E ). Tek yönde bükülmeli kasnak sayısı "
            f"{trn(Nps, 0)} girilmiş; tesisin gerçek askı düzenine göre "
            "denetleyin — düşük girilirse Nequiv, dolayısıyla gereken "
            "asgari güvenlik katsayısı olduğundan küçük çıkar."]
    b["aciklamalar"] = _iki_cap + [
        "TS EN 81-20 m.5.5.2.2:  'Askı elemanlarının güvenlik katsayısı … 12'den "
        "( iki halatta 16'dan ) az olamaz.  BUNA EK OLARAK askı halatlarının "
        "güvenlik katsayısı EN 81-50 m.5.12'ye göre hesaplanandan az olamaz.'  "
        "Yani ölçüt tektir:  GERÇEKLEŞEN S, ikisinin BÜYÜĞÜNDEN küçük olmayacak. "
        "Sf'nin kendisinin 12'yi geçmesi ŞART DEĞİLDİR — Sf < 12 yalnız "
        "'asgariyi Smin belirliyor' demektir;  'Sf ≥ Smin' diye ayrı bir geçme "
        "koşulu yoktur.",
        "TS EN 81-20 m.5.5.2.1: tahrik kasnağı / saptırma kasnağı bölüm dairesi "
        "çapının askı halatı anma çapına oranı, halatın kol sayısından bağımsız "
        "olarak EN AZ 40 olmalıdır. 30, aynı standardın dengeleme halatı gergi "
        "kasnağı ( m.5.5.6.2 ) ve regülatör ( m.5.6.2.2.1.3 ) eşiğidir, askı "
        "halatının değil.",
        "40 sınırı uyumlaştırılmış standart şartıdır; Asansör Yönetmeliği "
        "( 2014/33/AB ) Ek-I 1.3 sayısal oran vermez. Küçük kasnaklı makineler "
        "sapmayı onaylanmış kuruluş belgesiyle kanıtlar — belge beyan edilirse "
        "40'ın altı hata sayılmaz. Halat güvenlik katsayısı Sf yine EN 81-50 "
        "m.5.12'ye göre aranır; küçük kasnak Sf'yi zaten büyütür."]
    return b


# =====================================================================
#  5 -  HIZ REGÜLATÖRÜ HALATI               ( TS EN 81-20 m.5.6.2.2.1 )
# =====================================================================
def _reg_metni(tip_uygun, hiz_uygun, oran_uygun, kuvvet_uygun, kat_uygun,
               tertibat, S, oran, Fcekme, sinir_metni, kat, Dreg, dreg):
    """Regülatör bölümünün hükmü — GEREKÇE DÜŞEN KONTROLDEN YAZILIR.

    Bölümde beş kontrol var;  metin yalnız ikisini ( tip · hız ) açıklıyordu.
    Dreg/dreg oranı, çekme kuvveti ya da emniyet katsayısı düştüğünde pafta
    çıplak "UYGUN DEĞİLDİR" yazıyor, mühendise neyi değiştireceğini
    SÖYLEMİYORDU — ör. Dreg 150 mm'de hüküm tamamen gerekçesizdi.
    """
    if tip_uygun and hiz_uygun and oran_uygun and kuvvet_uygun and kat_uygun:
        return "UYGUNDUR."
    n = []
    if not tip_uygun:
        n.append(f"{tertibat} tertibat en çok "
                 f"{tr(S['ani_tertibat_azami_v'])} m/s'de kullanılır "
                 f"( m.5.6.2.1.2.1 b) )")
    if not hiz_uygun:
        n.append("regülatör devreye girme hızı izin verilen sınırların dışındadır")
    if not oran_uygun:
        #  Halatı inceltmek ancak listede oranı tutturan daha ince bir halat
        #  varsa önerilir;  en ince halattayken "küçültün" demek boş öğüttü.
        incelt = any(d < dreg and Dreg / d >= S["Dreg_dreg_asgari"]
                     for d in MG.ALAN["reg_halat_capi"][4])
        n.append(f"Dreg / dreg = {tr(oran)} < {S['Dreg_dreg_asgari']} — "
                 "regülatör kasnağını büyütün"
                 + (" ya da halat çapını küçültün" if incelt else ""))
    if not kuvvet_uygun:
        n.append(f"Fçekme = {tr(Fcekme)} N, {sinir_metni} değerinin altında — "
                 "gergi ağırlığını ya da kanal sürtünmesini artırın")
    if not kat_uygun:
        n.append(f"T'min / F'reg = {tr(kat)} < {S['reg_kat_asgari']} — "
                 "regülatör halatını güçlendirin ya da gergi ağırlığını azaltın")
    return "UYGUN DEĞİLDİR — " + "  ·  ".join(n)


def _regulator(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    Dreg, dreg = g["reg_kasnak_capi"], g["reg_halat_capi"]
    #  µ OFİS SABİTİDİR ( m.5.6.2.2.1.3 b)'nin µmax'ı );  asansör bazında
    #  sorulmaz — küçültülürse halat emniyet katsayısı olduğundan iyi çıkar.
    mu, gama = O["reg_mu"], g["reg_kanal_acisi"]
    alfa = S["reg_sarilma_aci"]
    #  Regülatör halatı:  program çizimden ölçer ( regülatör kasnağı ile gergi
    #  kasnağı arası iki kez + iki yarım sarım ).  Yoksa eski yaklaşık:  kuyu
    #  boyunca iki kat ( tabliye makine dairesiz tesiste 0 — MG.tabliye ).
    boy_ciz = _cizim_olcusu(g, "reg_halat_boyu")
    boy = float(boy_ciz) if boy_ciz else ((MG.alt_duraktan_tavana(g) + MG.tabliye(g)
                                            - S["ray_kaide_payi"]) * 2) / 1000.0
    #  REGÜLATÖR HALATINDA DA KATALOG VERİSİ GEÇERLİDİR.  Askı halatında
    #  imalatçı alanları vardı, regülatörde yoktu ve değerler HER ZAMAN
    #  TS 12385-5'in lif özlü tablosundan okunuyordu.  O tablo küçük çaplı
    #  çelik özlü regülatör halatlarını kapsamaz:  6 mm için 23,1 kN verir,
    #  piyasadaki çelik özlü halat 28 kN'dir.  Program bu yüzden UYGUN
    #  tasarımları reddedebiliyordu  ( 6,59 < 8 yerine 8,04 ≥ 8 ).
    gh_m, Tmin, gh_kaynak, Tmin_kaynak = _halat_verisi(
        g, "reg_halat_capi", "reg_halat_birim_kutle", "reg_halat_kopma_kN")
    gh = gh_m * boy
    Gra = g["reg_gergi_agirligi"]

    oran = Dreg / dreg
    oran_uygun = oran >= S["Dreg_dreg_asgari"]
    f = mu / math.sin(math.radians(gama) / 2.0)
    efa = math.exp(f * math.radians(alfa))
    Freg = gn * (gh + Gra) / 2.0
    Freg2 = Freg * efa
    #  TS EN 81-20 m.5.6.2.2.1.1 d):  regülatörün ürettiği çekme kuvveti,
    #  şu İKİ değerin BÜYÜĞÜNDEN az olamaz —
    #      · güvenlik tertibatını devreye sokmak için GEREKENİN İKİ KATI,
    #      · 300 N.
    #  İkinci sınır "2 × Freg" DEĞİLDİR:  Freg halatın kendi statik gergisidir,
    #  güvenlik tertibatını devreye sokan kuvvet değil.  O kuvvet imalatçıdan
    #  / tip inceleme belgesinden gelir;  2 × Freg, standardın istemediği
    #  e^(f·α') ≥ 2 koşuluna denk düşerdi.
    F_devreye = g.get("guvenlik_devreye_kuvvet")
    devreye_var = isinstance(F_devreye, (int, float)) and not isinstance(
        F_devreye, bool) and F_devreye > 0
    sinir = max(S["reg_kuvvet_asgari"], 2 * F_devreye) if devreye_var \
        else S["reg_kuvvet_asgari"]
    sinir_metni = (f"max( {trn(S['reg_kuvvet_asgari'], 0)} N ; 2 × "
                   f"{tr(F_devreye)} N )" if devreye_var
                   else f"{trn(S['reg_kuvvet_asgari'], 0)} N")
    Fcekme = Freg2 - Freg
    kuvvet_uygun = Fcekme >= sinir
    #  KUVVET GİRİLMEMİŞSE İKİNCİ KOŞUL ŞART OLARAK YAZILIR.  Devreye sokma
    #  kuvveti fren bloğunun belgesindedir ve proje aşamasında çoğu zaman
    #  bilinmez ( fren bloğu ayrı bir parçadır, montajda seçilir;  yerli
    #  üreticinin kullanma kılavuzunda bile yazmaz ).  Bölüm bu yüzden
    #  HESAP EKSİK sayılıyordu ve her projede bir sayı yazdırıyordu.  Koşul
    #  tersinden de aynıdır:  Fçekme ≥ 2 × F  ⇔  F ≤ Fçekme / 2.  300 N
    #  yine denetlenir;  fren bloğunun kuvveti en çok Fçekme / 2 olabilir.
    Fgt_azami = Fcekme / 2.0

    #  ── TS EN 81-20 m.5.6.2.1.2.1 b)  ve  m.5.6.2.2.1.1 a) ────────────
    #  İkisi denetlenmezse 2,5 m/s'lik bir asansöre ani frenlemeli tertibat
    #  konsa da, regülatör hangi hızda devreye girerse girsin bölüm
    #  "UYGUNDUR" derdi.
    v = g["beyan_hizi"]
    tertibat = g["guvenlik_tertibati"]
    ani = tertibat.startswith("Ani Frenlemeli")
    makarali = tertibat == "Ani Frenlemeli Makaralı"
    #  m.5.6.2.1.2.1 b):  ani frenlemeli KABİN tertibatı yalnız v ≤ 0,63 m/s
    tip_uygun = (not ani) or v <= S["ani_tertibat_azami_v"]
    #  m.5.6.2.2.1.1 a):  alt sınır 1,15·v ;  üst sınır tertibat tipine bağlı
    v_alt = S["reg_hiz_alt_carpan"] * v
    if ani:
        v_ust = S["reg_hiz_ust_makara"] if makarali else S["reg_hiz_ust_ani"]
        ust_dayanak = ("m.5.6.2.2.1.1 a) 2)  ani frenlemeli makaralı" if makarali
                       else "m.5.6.2.2.1.1 a) 1)  ani frenlemeli")
    elif v <= 1.0:
        v_ust = S["reg_hiz_ust_kaymali"]
        ust_dayanak = "m.5.6.2.2.1.1 a) 3)  kaymalı, v ≤ 1,0 m/s"
    else:
        v_ust = 1.25 * v + 0.25 / v
        ust_dayanak = "m.5.6.2.2.1.1 a) 4)  1,25·v + 0,25/v"
    v_dev = g.get("reg_devreye_hizi")
    hiz_var = isinstance(v_dev, (int, float)) and not isinstance(v_dev, bool) \
        and v_dev > 0
    hiz_uygun = (v_alt <= v_dev < v_ust) if hiz_var else True
    kat = Tmin / Freg2
    kat_uygun = kat >= S["reg_kat_asgari"]

    _kay(o, "regulator", gh=gh, Tmin=Tmin, oran=oran, f=f, efa=efa, Freg=Freg,
         Freg2=Freg2, F_cekme=Fcekme, F_sinir=sinir, S=kat,
         Fgt_azami=None if devreye_var else Fgt_azami)

    b = Bolum("HIZ REGÜLATÖRÜ HALATININ HESAPLANMASI", kimlik="regulator_halati",
              kaynak="TS EN 81-20 m.5.6.2.2.1  /  TS EN 81-50 m.5.11.2.3")
    b["adimlar"] = [
        veri("Dreg", "Regülatör kasnak çapı", Dreg, "mm", "GİRİŞ"),
        veri("dreg", "Regülatör halat çapı", dreg, "mm", "GİRİŞ"),
        veri("μ", "Sürtünme faktörü", mu, "",
             "KABUL  ·  TS EN 81-20 m.5.6.2.2.1.3 b) µmax"),
        veri("γ", "Kanal açısı", gama, "°", "GİRİŞ", 0),
        veri("α'", "Regülatör kasnağı sarılma açısı", alfa, "°", "KABUL", 0),
        veri("", "Regülatör halatı 1 m ağırlığı", gh_m, "kg/m", gh_kaynak),
        *([veri("", "Regülatör halatı boyu", boy, "m",
                 CIZIMDEN + "  ·  regülatör kasnağından gergi kasnağına iki kez + iki yarım sarım", 3),
           hesap("gh = ( 1 m ağırlık ) × halat boyu", f"{_trh(gh_m)} × {tr(boy)}", gh, "kg")]
          if boy_ciz else
          [hesap("gh = ( 1 m ağırlık ) × ( H × 1000 + son kat + tabliye − 200 ) × 2 / 1000",
                 f"{_trh(gh_m)} × {tr(boy)}", gh, "kg")]),
        veri("Gra", "Regülatör gergi ağırlığı — kasnak merkezindeki kuvvetin eşdeğeri",
             Gra, "kg", "GİRİŞ"),
        veri("Fgt", "Güvenlik tertibatını devreye sokma kuvveti",
             F_devreye if devreye_var else "girilmedi", "N" if devreye_var else "",
             "KATALOG  ·  tip inceleme belgesi" if devreye_var
             else "fren bloğunun belgesinden  ·  şartı aşağıda"),
        veri("T'min", "Halatın en küçük kopma yükü", Tmin, "N", Tmin_kaynak, 0),
        metin("Güvenlik tertibatı tipi & beyan hızı  ( m.5.6.2.1.2.1 ) :"),
        veri("", "Kabin güvenlik tertibatı tipi", tertibat, "", "GİRİŞ"),
        kontrol(f"{tertibat} tertibat, v = {tr(v)} m/s"
                + (f"  ≤  {tr(S['ani_tertibat_azami_v'])} m/s"
                   if ani else "  ( kaymalı — hız sınırı yok )"), tip_uygun),
        metin("Regülatör devreye girme hızı  ( m.5.6.2.2.1.1 a) ) :"),
        hesap("v_alt = 1,15 × v", f"1,15 × {tr(v)}", v_alt, "m/s",
              "en az beyan hızının %115'i", 3),
        hesap("v_üst", ust_dayanak, v_ust, "m/s", "tertibat tipine bağlı", 3),
        veri("v_dev", "Regülatör devreye girme hızı",
             v_dev if hiz_var else "seçilecek", "m/s" if hiz_var else "",
             "KATALOG  ·  tip inceleme belgesi" if hiz_var
             else f"İMALATÇI ŞARTI — [{trn(v_alt, 3)}, {trn(v_ust, 3)}) m/s aralığında olmalıdır", 3 if hiz_var else None),
        #  Sınırlar üç haneyle yazılır:  iki hane 2,156'yı 2,16 gösteriyordu
        #  ve reddedilen 2,158 paftada sınırın içinde görünüyordu.
        kontrol(f"{trn(v_alt, 3)} ≤ v_dev = {trn(v_dev, 3)} < {trn(v_ust, 3)} m/s", hiz_uygun)
        if hiz_var else
        kontrol(f"Şart:  {trn(v_alt, 3)} m/s  ≤  v_dev  <  {trn(v_ust, 3)} m/s", True,
                #  m.5.6.2.2.1.1 a)'nın kendi önerisi:  v > 1 m/s'de üst
                #  sınıra, düşük hızda alt sınıra olabildiğince yakın.
                "Bu aralıkta seçilir  ·  "
                + ("üst" if v > 1.0 else "alt")
                + " sınıra olabildiğince yakın önerilir"),
        metin("Regülatör kasnağı & halat oranı :"),
        hesap("Dreg / dreg", f"{trn(Dreg, 0)} / {tr(dreg)}", oran, ""),
        kontrol(f"Dreg / dreg = {tr(oran)}  ≥  {S['Dreg_dreg_asgari']}", oran_uygun),
        metin("Regülatör halatında oluşan gergi kuvveti :"),
        hesap("f = μ / sin( γ / 2 )",
              f"{tr(mu)} / sin( {trn(gama, 0)}° / 2 )", f, "", ondalik=4),
        hesap("e^(f·α')", f"exp( {_trh(f)} × {trn(alfa, 0)}° )", efa, "", ondalik=4),
        hesap("Freg = gn × ( gh + Gra ) / 2",
              f"{tr(gn)} × ( {tr(gh)} + {trn(Gra, 0)} ) / 2", Freg, "N"),
        hesap("F'reg = Freg × e^(f·α')", f"{tr(Freg)} × {_trh(efa)}", Freg2, "N"),
        hesap("Fçekme = F'reg − Freg",
              f"{tr(Freg2)} − {tr(Freg)}", Fcekme, "N",
              "regülatörün ÜRETTİĞİ çekme kuvveti  —  m.5.6.2.2.1.1 d)"),
        kontrol(f"Fçekme = {tr(Fcekme)} N  ≥  {sinir_metni} = {tr(sinir)} N",
                kuvvet_uygun) if devreye_var else
        kontrol(f"Fçekme = {tr(Fcekme)} N  ≥  {sinir_metni}", kuvvet_uygun),
    ] + ([] if devreye_var else [
        hesap("Fgt,azami = Fçekme / 2", f"{tr(Fcekme)} / 2", Fgt_azami, "N",
              "fren bloğunun devreye girme kuvveti en çok bu değer olabilir"),
        kontrol(f"Şart:  Fgt  ≤  {tr(Fgt_azami)} N", True,
                "Fren bloğunun tip inceleme belgesinden doğrulanır"),
    ]) + [
        metin("Regülatör halatı emniyet katsayısı :"),
        hesap("T'min / F'reg", f"{trn(Tmin, 0)} / {tr(Freg2)}", kat, ""),
        kontrol(f"T'min / F'reg = {tr(kat)}  ≥  {S['reg_kat_asgari']}", kat_uygun),
    ]
    _baslik_sinir = sinir_metni if devreye_var else (
        f"{sinir_metni}   ·   Fgt ≤ Fçekme / 2")
    b["sonuc"] = {"baslik": (f"KONTROL      Dreg/dreg ≥ {trn(S['Dreg_dreg_asgari'], 0)}"
                             f"   ·   Fçekme ≥ {_baslik_sinir}"
                             f"   ·   T'min/F'reg ≥ {trn(S['reg_kat_asgari'], 0)}"),
                  "metin": _reg_metni(tip_uygun, hiz_uygun, oran_uygun,
                                      kuvvet_uygun, kat_uygun, tertibat, S,
                                      oran, Fcekme, sinir_metni, kat, Dreg, dreg),
                  "uygun": bool(tip_uygun and hiz_uygun and oran_uygun
                                and kuvvet_uygun and kat_uygun)}
    b["aciklamalar"] = [
        "TS EN 81-20 m.5.6.2.2.1.1 d):  'the tensile force in the overspeed "
        "governor rope produced by the governor, when tripped, shall be at "
        "least the greater of … twice that necessary to engage the safety "
        "gear, or 300 N.'  İkinci sınırdaki kuvvet GÜVENLİK TERTİBATINI "
        "DEVREYE SOKAN kuvvettir ve imalatçıdan gelir — halatın statik "
        "gergisi Freg değildir.",
        "μ, TS EN 81-20 m.5.6.2.2.1.3 b)'nin verdiği µmax = 0,2 ile "
        "sınırlıdır:  emniyet katsayısı hesabında bundan büyük bir sürtünme "
        "varsayılamaz."]
    return b


# =====================================================================
#  6 -  TAHRİK YETENEĞİ                  ( TS EN 81-50 m.5.11.2 / 5.11.3 )
# =====================================================================
#  Yük durumları.  Her durum, EN 81-50 m.5.11.2 terimlerini kendi işaretleriyle üretir.
YUK_DURUMLARI = (
    ("yukleme", "Kabinin yüklenmesi  ( %125 yüklü kabin en alt durakta dururken )"),
    ("fren_alt", "Acil frenleme  ( %100 yüklü kabin en alt durakta )"),
    ("fren_ust", "Acil frenleme  ( boş kabin en üst durakta )"),
    ("bloke", "Karşı ağırlığın asılı kalması  ( boş kabin en üstte )"),
)


def _terimler(g, o, durum):
    """Bir yük durumunun EN 81-50 m.5.11.2 terimleri."""
    S = SABIT
    Q, P, r = o["Q"], o["P"], o["r"]
    nh, gh, H = o["nh"], o["gh"], g["seyir_mesafesi"]
    Mcwt = g["karsi_agirlik"]
    a_in = g["acil_frenleme_a"]
    w_kablo, _ = _gezici_kablo(g)
    ycar = ycwt = H / 2.0

    #  ASKI KASNAKLARININ ATALETİ  —  yalnız askı oranı > 1 iken  ( koşul III )
    mP, _J, _A = _kasnak_atalet(g, o["ofis"])
    _cok = r > 1
    iPcar, iPcwt, mDPcwt = _kasnak_adetleri(g, o["ofis"], r)
    t = {"P": P, "Q": 0.0, "Mcwt": Mcwt, "MCRcar": 0.0, "MCRcwt": 0.0,
         "MComp": 0.0, "MTrav": 0.0, "mPTD": 0.0, "iPDT": 0.0,
         #  Saptırma kasnağının ataleti TARAFINA göre ( koşul I:  kabin, II:
         #  karşı ağırlık tarafı ).  Çizilen düzenlerde saptırma kasnağı
         #  yalnız makine dairesinde, ağırlık tarafındadır.
         "mDPcar": 0.0, "mDPcwt": mDPcwt,
         "mPcar": mP if _cok else 0.0, "mPcwt": mP if _cok else 0.0,
         "iPcar": iPcar, "iPcwt": iPcwt,
         "r": r, "gn": S["gn"], "a": 0.0,
         "MSRcar": 0.0, "MSRcwt": 0.0, "FRcar": 0.0, "FRcwt": 0.0}
    #  MSR:  askı halatlarının kabin / karşı ağırlık tarafındaki indirgenmiş
    #  kütlesi.  Kabin ve karşı ağırlık tarafı AYRI büyüklüklerdir
    #  ( ycar · ycwt );  ikisi sayısal olarak eşit olsa da ayrım korunur.
    #  ------------------------------------------------------------------
    #  HALAT KÜTLESİNİN TARAF DAĞILIMI      EN 81-50 m.5.11.2.2
    #  ------------------------------------------------------------------
    #  MSR = ( 0,5·H ± y ) · ns · ( halatın 1 m kütlesi ).  ± işareti kabinin
    #  KUYUDAKİ KONUMUNDAN çıkar.  Üstte makineli bir tesiste halat, tahrik
    #  kasnağından kabine ve karşı ağırlığa iner:
    #      kabin EN ALTTA  →  kabin tarafındaki halat UZUN   ( 0,5·H + y = H )
    #                          ağırlık üsttedir, o taraf KISA ( 0,5·H − y = 0 )
    #      kabin EN ÜSTTE  →  tam tersi.
    #
    #  "Kabin en alt durakta" durumu tam da halat kütlesi kabin tarafında
    #  olduğu için EN OLUMSUZ durumdur — standart T1/T2'yi "for the worst case
    #  depending on the position of the car in the well" değerlendirmeyi ister.
    #  Halatı karşı ağırlık tarafına koymak EMNİYETSİZ olurdu:  T1 küçük
    #  çıkar, tahrik yeteneği olduğundan iyi görünür ( 20 duraklı bir tesiste
    #  1,79 yerine 1,23 ).
    uzun_car = (0.5 * H + ycar) * nh * gh     # kabin EN ALTTA  →  halat kabinde
    kisa_car = (0.5 * H - ycar) * nh * gh     # kabin EN ÜSTTE  ( ycar = H/2 → 0 )
    uzun_cwt = (0.5 * H + ycwt) * nh * gh     # ağırlık EN ALTTA ( kabin üstte )
    kisa_cwt = (0.5 * H - ycwt) * nh * gh
    #  ------------------------------------------------------------------
    #  DENGE ZİNCİRİ  MCRcar / MCRcwt        EN 81-50 m.5.11.2
    #  ------------------------------------------------------------------
    #  Terimler _T1 / _T2'de ZATEN vardı ama hiçbir yerde atanmıyordu:  tahrik
    #  hesabı zincirden habersizdi.  Zincir kabin altından kuyu dibine sarkıp
    #  karşı ağırlığa çıkar;  dağılımı HALATIN TAM TERSİDİR:
    #      kabin EN ALTTA  →  zincir kabin tarafında KISA ( kabin kuyu dibinde ),
    #                          karşı ağırlık tarafında UZUN
    #      kabin EN ÜSTTE  →  tam tersi
    #  Toplamı her konumda sabittir ve motor bölümündeki MCR'ye eşittir.
    #  ( λ ve MCR bölüm 1'den okunur — tek kaynak.  Bölüm 1 her zaman önce
    #    çalışır;  motor tek başına çağrılırsa zincirsiz duruma düşülür. )
    mu_zincir = (o.get("lam") or 0.0) * r * gh * nh    # zincirin metre kütlesi
    zincir_uzun = (0.5 * H + ycar) * mu_zincir         # = H · mu  = MCR
    zincir_kisa = (0.5 * H - ycar) * mu_zincir         # = 0
    #  MTrav:  gezici kablonun indirgenmiş kütlesi
    trav = (0.25 * H + 0.5 * ycar) * w_kablo

    if durum == "yukleme":                    # sütun M — %125 yüklü kabin EN ALTTA
        t["Q"] = 1.25 * Q
        t["MSRcar"], t["MSRcwt"] = uzun_car, kisa_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_kisa, zincir_uzun
    elif durum == "fren_alt":                 # sütun P — %100 yüklü kabin EN ALTTA
        t["Q"] = Q
        t["a"] = a_in
        t["MSRcar"], t["MSRcwt"] = uzun_car, kisa_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_kisa, zincir_uzun
    elif durum == "fren_ust":                 # sütun Q — boş kabin EN ÜSTTE
        t["a"] = a_in
        t["MSRcar"], t["MSRcwt"] = kisa_car, uzun_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_uzun, zincir_kisa
        t["MTrav"] = trav
    elif durum == "bloke":                    # sütun O — boş kabin EN ÜSTTE
        t["Mcwt"] = 0.0
        #  Kabin üstte, halat kütlesi karşı ağırlık tarafında:
        #  ( 0,5·H + H/2 )·ns·gh  =  ns × H × gh.
        t["MSRcar"], t["MSRcwt"] = kisa_car, uzun_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_uzun, zincir_kisa
        t["MTrav"] = trav
    return t


def _kasnak_adetleri(g, O, r):
    """( iPcar , iPcwt , mDPcwt ) — atalete giren kasnaklar.

    Program çizilen kasnakları sayar ( cizim/olculer ):  kabinle ve karşı
    ağırlıkla hareket eden kasnaklar ve makine dairesinde ağırlık tarafındaki
    sabit saptırma kasnağı.  Saptırma kasnağının indirgenmiş kütlesi
    ( EN 81-50 m.5.11.2.2 ):  mDP = J · ( v_kasnak / v )² / R²;  sabit
    kasnakta halat hızı r·v olduğundan ( v_kasnak / v )² = r².  Çizimden
    değer yoksa ofis kabulü ( askı oranı > 1 iken kabin 2, ağırlık 1 ) ve
    saptırma ataleti 0."""
    ik, ia = _cizim_olcusu(g, "kasnak_kabin_adedi"), _cizim_olcusu(g, "kasnak_agirlik_adedi")
    if ik is not None and ia is not None:
        iPcar, iPcwt = int(ik), int(ia)
    else:
        iPcar = O["kasnak_adet_kabin"] if r > 1 else 0
        iPcwt = O["kasnak_adet_agirlik"] if r > 1 else 0
    Ds = _cizim_olcusu(g, "saptirma_agirlik_capi")
    mDP = 0.0
    if Ds:
        mP_s, _J, _A = _kasnak_atalet(g, O, Ds)
        mDP = mP_s * r * r
    return iPcar, iPcwt, mDP


def _kasnak_atalet(g, O, Dp=None):
    """Saptırma kasnaklarının indirgenmiş kütlesi  mP = J / R²   [ kg ].

    TS EN 81-50 m.5.11.2.2 a) tahrik kuvvetlerine kasnak ataletini de katar:

        Σ( mPcar · iPcar · a ) / r          mPcar = J · ( v_kasnak / v )² / R²

    J bir BİLEŞEN ÖZELLİĞİDİR ve standart onu imalatçıdan bekler.  Sahada
    kimse kasnağın atalet momentini veri sayfasından okuyup girmez;  bu
    yüzden kasnak, ÇAPI VE HALAT DÜZENİ BİLİNEN bir döküm disk olarak
    modellenir  ( dört sayı da ofis kabulüdür, bkz. sabitler.py ):

        J  = ½·π·ρ·A·( R⁴ − R₁⁴ )  +  ½·π·ρ·A₁·R₁⁴
        R  = Dp / 2                          Dp : ortalama saptırma çapı
        R₁ = ( Dp − göbek payı ) / 2
        A  = ( ns − 1 )·1,6·dr + kanal payı  ns · dr : halat sayısı ve çapı
        A₁ = A × göbek oranı

    2:1 askıda kasnağın çevresel hızı kabin hızına eşittir, yani
    ( v_kasnak / v ) = 1 ve mP = J / R² olur.

    DOĞRULAMA:  referans projenin yayımlanmış örnek paftasında Dp = 294 mm ve
    7 × 6,5 mm halat için J = 0,29 kg·m² yazar;  bu bağıntı 0,2920 verir.
    """
    Dp = g.get("saptirma_kasnak_capi") if Dp is None else Dp
    ns, dr = g.get("halat_adedi"), g.get("halat_capi")
    if not (Dp and ns and dr) or Dp <= O["kasnak_gobek_pay"]:
        return 0.0, 0.0, 0.0
    R = (Dp / 2.0) / 1000.0
    R1 = ((Dp - O["kasnak_gobek_pay"]) / 2.0) / 1000.0
    A = ((ns - 1) * 1.6 * dr + O["kasnak_kanal_payi"]) / 1000.0
    A1 = A * O["kasnak_gobek_orani"]
    rho = O["kasnak_yogunluk"]
    J = (0.5 * math.pi * rho * A * (R ** 4 - R1 ** 4)
         + 0.5 * math.pi * rho * A1 * R1 ** 4)
    return (J / (R ** 2)) if R else 0.0, J, A


def _T1(t, FRcar, s):
    """Kabin tarafındaki halat kuvveti  T1  ( EN 81-50 m.5.11.2.2 a ).

        T1 = ( P + Q + MCRcar + MTrav ) / r · ( gn ± a )
             + MComp / ( 2·r ) · gn
             + MSRcar · ( gn ± a · ( r² + 2 ) / 3 )
             ± ( iPTD · mPTD / ( 2·r ) ) · a
             ± ( mDP · a ) / r
             ∓ FRcar / r

    ``s`` İŞLEMİ seçer:  +1 ÜST işlem  ( beyan yüklü kabin AŞAĞI yönde
    yavaşlıyor ), −1 ALT işlem  ( boş kabin YUKARI yönde yavaşlıyor ).
    Yükleme ve bloke durumlarında a = 0'dır, işlem fark etmez.
    """
    r, gn, a = t["r"], t["gn"], t["a"]
    return ((t["P"] + t["Q"] + t["MCRcar"] + t["MTrav"]) * (gn + s * a) / r
            + t["MComp"] / (2.0 * r) * gn
            + t["MSRcar"] * (gn + s * a * (r * r + 2) / 3.0)
            + s * (t["iPDT"] * t["mPTD"] * a) / (2.0 * r)
            + s * t["mDPcar"] * a / r
            #  Σ( mPcar · iPcar · a ) / r   —  askı kasnaklarının ataleti
            #  ( m.5.11.2.2, koşul III:  yalnız askı oranı > 1 iken )
            + s * (t["mPcar"] * t["iPcar"] * a) / r
            - s * FRcar / r)


def _T2(t, FRcwt, s):
    """Karşı ağırlık tarafındaki halat kuvveti  T2  —  işaretler T1'in TERSİ.

        T2 = ( Mcwt + MCRcwt ) / r · ( gn ∓ a )  +  MComp / ( 2·r ) · gn
             + MSRcwt · ( gn ∓ a · ( r² + 2 ) / 3 )
             ∓ ( iPTD · mPTD / ( 2·r ) ) · a  ∓ ( mDP · a ) / r  ± FRcwt / r
    """
    r, gn, a = t["r"], t["gn"], t["a"]
    return ((t["Mcwt"] + t["MCRcwt"]) * (gn - s * a) / r
            + t["MComp"] * gn / (2.0 * r)
            + t["MSRcwt"] * (gn - s * a * (r * r + 2) / 3.0)
            - s * (t["iPDT"] * t["mPTD"] * a) / (2.0 * r)
            - s * t["mDPcwt"] * a / r
            - s * (t["mPcwt"] * t["iPcwt"] * a) / r
            + s * FRcwt / r)


#  YÜK DURUMU  →  m.5.11.2.2'nin HANGİ İŞLEMİ
#
#  Maddenin kendi cümlesi:  "the upper operation is applicable in case the
#  car with its rated load is retarding in the DOWN direction and the lower
#  operation in case the empty car is retarding in the UP direction.  For
#  the cases car loading and stalled condition a = 0."
#
#  Ek D'nin çözümlü örneği ( 2:1, dengeleme yok ) bunu sayıya döker:
#      a) yüklü kabin en alt durakta :  T1 = (P+Q)/2·( gn + a ) …  − FRcar/2
#                                       T2 = Mcwt/2·( gn − a ) …  + FRcwt/2
#      b) boş kabin  en üst durakta  :  işaretlerin tamamı ters.
#
#  İŞARETLER TERS ALINIRSA ( yüklü kabin aşağı yavaşlarken kabin tarafına
#  gn − a, ağırlık tarafına gn + a ) T1/T2 oranı %36 KÜÇÜK çıkar ve tahrik
#  yeteneği kontrolü olduğundan kolay geçilir — EMNİYETSİZ taraf.
#  ( referans projenin paftası da Ek D ile aynı işaretleri yazar. )
ISLEM = {"yukleme": +1, "fren_alt": +1, "fren_ust": -1, "bloke": +1}


#  SARILMA AÇISI α ZORUNLU BEYANDIR — VARSAYIMI YOKTUR.
#  TS EN 81-50 m.5.11.2.1 İKİ EŞİTSİZLİK verir ve YÖNLERİ TERSTİR:
#
#      yükleme · acil frenleme :   T1 / T2  ≤  e^(f·α)
#      bloke ( kabin/ağırlık )  :   T1 / T2  ≥  e^(f·α)
#
#  Küçük α ilk ikisinde sınırı DARALTIR ( emniyetli ), blokede GEVŞETİR
#  ( emniyetsiz );  büyük α tersini yapar.  Hiçbir açı iki kontrolde birden
#  "emniyetli varsayılan" değildir.  180° varsayılanı denendi:  486
#  senaryonun %33'ünde yükleme/frenleme hükmü geçme yönünde dönüyordu.
#  Bu yüzden açı GİRİLMEDİKÇE dört sınır hesaplanmaz ve bölüm HESAP EKSİK
#  sayılır.  Açıdan bağımsız olan her şey ( T1 · T2 · oranlar · f ) yine
#  hesaplanır ve paftada durur — mühendis açıyı girince eksik yalnız sınır
#  satırlarıdır.
ALFA_YOK = "HESAP EKSİK — sarılma açısı α girilmedi"

#  AÇI KANALIN SARIM SAYISINA GÖRE FİZİKSEL DEĞİLSE HÜKÜM YOKTUR.
#  Tek sarımda α en çok 180°, çift sarımda 180°'den büyüktür.  Bu, GİRDİ
#  DOĞRULAMASINDA reddedilir ( bkz. MG.dogrula );  aşağısı motor doğrudan
#  çağrıldığında devreye giren İKİNCİ KALKANDIR.  Eskiden çift sarımda 180°
#  ve altı için ayrı bir "yarım hesap" yolu vardı ( üç kontrol hesaplanır,
#  bloke eksik sayılır );  açı artık girdide reddedildiği için o yol hiçbir
#  yoldan ulaşılamaz hâle geldi ve kaldırıldı.  İmkânsız bir açıyla hiçbir
#  yük durumuna "UYGUN" basılmaz.
ALFA_ARALIK_DISI = "sarılma açısı α kanalın sarım sayısına göre fiziksel değil"

#  SERTLEŞTİRİLMEMİŞ DÜZ V KANAL STANDART DIŞIDIR ( m.5.11.2.3.1.2 ).  O da
#  girdide reddedilir;  aşağısı ikinci kalkandır.
KANAL_STANDART_DISI = ("alt kesilmesiz V kanal sertleştirilmemiş olamaz  "
                       "( TS EN 81-50 m.5.11.2.3.1.2 )")


def _tahrik(g, o):
    S, O = SABIT, o["ofis"]
    R1 = g["tahrik_kasnak_capi"] / 2.0
    v = o["v"]
    sekil = g["kanal_sekli"]
    cift_sarim = (MT.kanal_gecis_sayisi(sekil) or 1) > 1

    #  ------------------------------------------------------------------
    #  SARILMA AÇISI  α          BEYAN EDİLİR, TÜRETİLMEZ
    #  ------------------------------------------------------------------
    #  α makine şasesinin ölçülerinden de türetilebilir:
    #      A = Ra − 2·R1 ,  B = H − C + D ,  α = 180° − arctan( A / B )
    #  Bağıntı DOĞRUDUR ( tahrik kasnağı ile saptırma kasnağı arasındaki
    #  ortak teğetten çıkar ) ama üç ölçüye bağlıdır ve o üç ölçü BAŞKA
    #  HİÇBİR HESABA girmez:  C · D · Ra yalnız bunun için sorulurdu.
    #  Üstelik model iki kasnağın yarıçapını EŞİT varsayar;  Dp ≠ Dt olan
    #  her tesiste yaklaşıktır.
    #
    #  α artık doğrudan sorulur.  Dış referansların ikisi de böyle yapar:
    #  referans proje "Rope Winding Angle α" diye ayrı girdi alır ( ve C · D · Ra
    #  diye bir girdisi hiç yoktur ), "new block" paftası formüle sabit
    #  3,1416 yazar.
    #
    #  AÇI GİRİLMEMİŞSE BÖLÜM ERKEN DÖNMEZ ( bkz. ALFA_YOK ).  T1 ve T2 yine
    #  hesaplanır;  açıya bağlı olan yalnız DÖRT SINIR ve HÜKÜMLERİDİR.
    _a = g.get("sarilma_acisi")
    alfa_var = (isinstance(_a, (int, float)) and not isinstance(_a, bool)
                and _a > 0)
    alfa_derece = float(_a) if alfa_var else None
    alfa = math.radians(alfa_derece) if alfa_var else None
    #  Tek sarımda halat kasnağı en çok yarım tur dolanır.  Çift sarımda
    #  halat kasnaktan İKİ kez geçer;  toplam sarım her zaman yarım turdan
    #  büyüktür ve bir tam turu aşamaz.
    alt, ust = (180.0, 360.0) if cift_sarim else (0.0, 180.0)
    alfa_uygun = alfa_var and alt < alfa_derece <= ust

    #  Sürtünme katsayısı kabulleri  ( EN 81-50 m.5.11.2.3.2 )
    #  Acil frenlemedeki μ HALAT hızına bağlıdır;  palangalı sistemde halat
    #  kabinden askı oranı katı hızlı gider.
    v_halat = v * o["r"]
    mu_yuk = S["mu_yukleme"]
    mu_fren = S["mu_yukleme"] / (1 + v_halat / 10.0)
    mu_bloke = S["mu_bloke"]
    #  SÜRTÜNME ÇARPANI f  —  KANAL ŞEKLİNE GÖRE AYRI MADDE.
    #  Yarım daire kanalın maddesi m.5.11.2.3.1.1, V kanalınki
    #  m.5.11.2.3.1.2'dir.  Şekilden bağımsız hep V bağıntısı kullanmak
    #  yarım dairede f'yi BÜYÜK, yani tahrik yeteneğini olduğundan iyi verir.
    yarim_daire = MT.kanal_yarim_daire_mi(sekil)
    #  Alt kesilme yoksa β = 0;  düz yarım daire kanalın alt kesilmesi yoktur.
    #  Açılar bölüm 4 ile AYNI kaynaktan okunur ( MT.kanal_acisi / kanal_beta ) —
    #  pafta ile hesap ayrışmasın diye.
    gama_derece, beta_derece, gama_girildi, beta_girildi = MG.kanal_acilari(g, O)
    beta = math.radians(beta_derece)
    gama = math.radians(gama_derece)
    sert = g["kanal_isleme"] == "Sertleştirilmiş"

    def _f(mu):
        """TS EN 81-50 m.5.11.2.3.1.1 ( yarım daire ) / m.5.11.2.3.1.2 ( V )."""
        if yarim_daire:
            pay = 4 * (math.cos(gama / 2.0) - math.sin(beta / 2.0))
            payda = (math.pi - beta - gama - math.sin(beta) + math.sin(gama))
            return mu * pay / payda
        if sert:
            return mu / math.sin(gama / 2.0)
        return mu * 4 * (1 - math.sin(beta / 2.0)) / (math.pi - beta - math.sin(beta))

    f_yuk, f_fren = _f(mu_yuk), _f(mu_fren)
    #  Ağırlık bloke durumu:  V kanalda m.5.11.2.3.1.2 sertleştirilmiş olsun
    #  olmasın μ/sin(γ/2) der;  yarım dairede ayrı bir kural yoktur, aynı
    #  bağıntı μ = 0,2 ile kullanılır.
    f_bloke = (_f(mu_bloke) if yarim_daire else mu_bloke / math.sin(gama / 2.0))

    _kay(o, "tahrik", mu_fren=mu_fren, f_bloke=f_bloke)
    if alfa_var:
        _kay(o, "tahrik", alfa_derece=alfa_derece, alfa=alfa)
    _kay(o, "tahrik", f_yukleme=f_yuk, f_frenleme=f_fren)

    b = Bolum("TAHRİK YETENEĞİNİN HESAPLANMASI", kimlik="tahrik_yetenegi",
              kaynak="TS EN 81-50 m.5.11.2  /  m.5.11.3")
    #  m.5.11.2.3.1.2:  "Where the groove has not been submitted to an
    #  additional hardening process, in order to limit the deterioration of
    #  traction due to wear, an undercut is necessary."  Yani sertleştirilmemiş
    #  V kanalın ALT KESİLMESİ OLMALIDIR;  bu birleşim standardın dışındadır.
    #  Bu birleşim girdide reddedilir ( MG.dogrula );  buraya ancak motor
    #  doğrudan çağrılırsa gelinir.  Eskiden yalnız not düşülüyor ve sayısal
    #  kontroller geçerse bölüm "UYGUNDUR" diyordu — artık hüküm de düşer.
    kanal_standart_disi = ((not yarim_daire) and (not sert)
                           and not MT.kanal_alti_kesik_mi(sekil))
    b["adimlar"] = [
        veri("R1", "Tahrik kasnağı yarıçapı", R1, "mm"),
        veri("α", "Halat sarılma açısı", alfa_derece, "°",
             _kaynak(g, "sarilma_acisi") if alfa_var else "GİRİLMEDİ"),
        (kontrol(f"α = {tr(alfa_derece)}°  —  "
                 f"{'çift' if cift_sarim else 'tek'} sarımlı kasnakta "
                 f"{trn(alt, 0)}° < α ≤ {trn(ust, 0)}°", alfa_uygun)
         if alfa_var else
         kontrol("α girilmedi  —  gerçek sarılma açısı proje yerleşiminden "
                 "belirlenip girilmelidir", False, "HESAP EKSİK")),
        metin("Sürtünme katsayısı μ kabulleri  ( TS EN 81-50 Şekil 8 ) :"),
        veri("μ", "Yükleme için", mu_yuk, "", "EN 81-50 Şekil 8"),
        veri("v halat", "Halat hızı  ( kabin hızı × askı oranı )", v_halat, "m/s"),
        hesap("μ = 0,1 / ( 1 + v_halat / 10 )",
              f"0,1 / ( 1 + {tr(v_halat)} / 10 )", mu_fren, "",
              "EN 81-50 m.5.11.2.3.2"),
        veri("μ", "Kabinin bloke edildiği durumlar için", mu_bloke, "",
             "EN 81-50 Şekil 8"),
        metin(f"Sürtünme faktörü f  —  kanal işleme : {g['kanal_isleme']} :"),
        veri("γ", "Kanal açısı", gama_derece, "°",
             "KATALOG  ·  kasnak föyü" if gama_girildi else "KABUL", 0),
        veri("β", "Alt kesilme açısı", beta_derece, "°",
             ("KATALOG  ·  kasnak föyü" if beta_girildi else "KABUL")
             if MT.kanal_alti_kesik_mi(sekil) else "alt kesilme yok", 0),
        veri("f", "Kabinin yüklenmesi", f_yuk, "", "EN 81-50 m.5.11.2.3", 4),
        veri("f", "Durdurma tertibatının çalışması", f_fren, "",
             "EN 81-50 m.5.11.2.3", 4),
        veri("f", "Kabinin bloke edilmesi", f_bloke, "", "EN 81-50 m.5.11.2.3", 4),
    ]

    #  ── ASKI KASNAKLARININ ATALETİ  ( m.5.11.2.2, koşul III ) ────────
    #  Paftada GÖRÜNÜR:  terim ofis kabulleriyle modellenen bir kasnaktan
    #  çıkıyor, okuyan mühendis nereden geldiğini görebilmeli.
    _mP, _J, _A = _kasnak_atalet(g, O)
    _iPcar, _iPcwt, _mDPcwt = _kasnak_adetleri(g, O, o["r"])
    _adet_kaynak = (CIZIMDEN + "  ·  çizilen kasnaklar"
                    if _cizim_olcusu(g, "kasnak_kabin_adedi") is not None else "KABUL")
    if o["r"] > 1 and _mP:
        b["adimlar"] += [
            metin("Askı kasnaklarının ataleti  ( m.5.11.2.2 · koşul III ) :",
                  vurgu=True),
            veri("Dp", "Saptırma kasnaklarının ortalama çapı",
                 g["saptirma_kasnak_capi"], "mm", _kaynak(g, "saptirma_kasnak_capi"), 0),
            hesap("A = ( ns − 1 ) × 1,6 × dr + pay",
                  f"( {trn(g['halat_adedi'], 0)} − 1 ) × 1,6 × {tr(g['halat_capi'])}"
                  f" + {trn(O['kasnak_kanal_payi'], 0)}", _A * 1000, "mm",
                  "KABUL  ·  kasnak genişliği", 0),
            hesap("J = ½·π·ρ·A·( R⁴ − R₁⁴ ) + ½·π·ρ·A₁·R₁⁴",
                  f"ρ = {trn(O['kasnak_yogunluk'], 0)} kg/m³  ·  "
                  f"göbek payı {trn(O['kasnak_gobek_pay'], 0)} mm",
                  _J, "kg·m²", "KABUL  ·  döküm disk modeli", 4),
            hesap("mP = J / R²", f"{_trh(_J)} / ( {_trh(g['saptirma_kasnak_capi'] / 2000)} )²",
                  _mP, "kg"),
            veri("iPcar", "Kabin tarafındaki kasnak sayısı",
                 _iPcar, "adet", _adet_kaynak, 0),
            veri("iPcwt", "Ağırlık tarafındaki kasnak sayısı",
                 _iPcwt, "adet", _adet_kaynak, 0),
        ]
    if _mDPcwt:
        _Dsap = g["saptirma_agirlik_capi"]
        b["adimlar"] += [
            metin("Saptırma kasnağının ataleti  ( m.5.11.2.2 · koşul II — ağırlık tarafı ) :",
                  vurgu=True),
            veri("Dsap", "Makine dairesindeki saptırma kasnağının çapı", _Dsap, "mm",
                 CIZIMDEN, 0),
            hesap("mDP = J / R² × r²   ( sabit kasnakta halat hızı r·v )",
                  f"J / ( {_trh(_Dsap / 2000)} )² × {trn(o['r'], 0)}²", _mDPcwt, "kg"),
        ]

    #  ── KUYU SÜRTÜNMESİ  ( m.5.11.2.2 · yalnız acil frenlemede ) ──────
    #  Paftada GÖRÜNÜR:  frenleme hükmü bu kabule bağlıdır ( 5.760
    #  senaryonun 399'unda sürtünme 0 alınınca hüküm döner ) ve standart onu
    #  "asgari sürtünme sağlanamıyorsa silinmelidir" koşuluna bağlar.
    _fr_kaynak = ("KABUL  ·  EN 81-50 m.5.11.2.2 — asgari sürtünme "
                  "sağlanamıyorsa 0 alınır")
    b["adimlar"] += [
        metin("Kuyudaki sürtünme  ( m.5.11.2.2 · yalnız acil frenlemede ) :",
              vurgu=True),
        veri("FRcar", "Kabin tarafı sürtünmesi  ( P + Q + MCR + MTrav kuvvetinin )",
             O["kuyu_surtunme_kabin"], "%", _fr_kaynak, 1),
        veri("FRcwt", "Ağırlık tarafı sürtünmesi  ( Mcwt + MCR kuvvetinin )",
             O["kuyu_surtunme_agirlik"], "%", _fr_kaynak, 1),
    ]

    tumu_uygun = alfa_uygun
    gevsek_var = False
    #  m.5.5.3 c) 2 BEYAN EDİLDİYSE "bloke" SATIRI HÜKÜM VERMEZ.
    #  Satır yine hesaplanır ve paftada durur — T1 · T2 · oran gerçek bilgidir
    #  ve m.6.3.3 saha deneyinde karşılaştırılır;  yalnız bölümün kararını
    #  belirlemez, çünkü kabini tavana çekilmekten koruyan şey halatın kayması
    #  değil, makineyi durduran elektrikli tertibattır.
    _elektrikli = (str(g.get("yukari_kacma_korumasi") or "").strip()
                   == "Elektrikli güvenlik tertibatı")
    #  HANGİ YÜK DURUMUNUN KALDIĞI SÖYLENİR.  Bölüm yalnız "UYGUN DEĞİLDİR"
    #  diyordu;  dört durumdan hangisinin kaldığı ve ne yapılacağı yazmıyordu.
    #  Öteki bütün bölümler uygulanabilir bir öğüt veriyor.
    _kalan = []
    for durum, baslik in YUK_DURUMLARI:
        t = _terimler(g, o, durum)
        isl = ISLEM[durum]
        kont_mesaj = ""          # kontrol satırının "UYGUN / UYGUN DEĞİL"i
        sinir_kaynak = "EN 81-50 m.5.11.3"
        #  SÜRTÜNME, KUYUDAKİ KUVVETTİR  ( m.5.11.2.2:  "FRcar is the
        #  frictional force IN THE WELL" ).  Formül onu FR / r olarak halata
        #  çevirir;  bu yüzden yüzde, o taraftaki GÖVDENİN kuyudaki ağırlık
        #  kuvvetine uygulanır — halat kuvvetine değil:
        #      FRcar = %k · ( P + Q + MCRcar + MTrav ) · ( gn ± a )
        #      FRcwt = %k · ( Mcwt + MCRcwt )          · ( gn ∓ a )
        #  referans proje ( FRcar = (Q+P)·(gn+a)·%2 ) ve new block ( FR_car =
        #  F_car·FL_p ) böyle kurar.  Eskiden yüzde, ZATEN /r ile halata
        #  çevrilmiş sürtünmesiz T1 / T2'den alınıyor ve formülde BİR KEZ DAHA
        #  /r'ye bölünüyordu:  2:1 askıda sürtünme yarıya iniyordu.  Referans proje
        #  örneğinde fren alt T1 9.071 N yerine şimdi 8.987,79 N ( referans proje
        #  8.987,82 ).
        #  a = 0 olan durumlarda ( yükleme · bloke ) sürtünme alınmaz — Ek D
        #  de o iki durumu "no friction considered" diye kurar.
        if durum in ("fren_alt", "fren_ust"):
            FRcar = (O["kuyu_surtunme_kabin"] / 100.0
                     * (t["P"] + t["Q"] + t["MCRcar"] + t["MTrav"])
                     * (t["gn"] + isl * t["a"]))
            FRcwt = (O["kuyu_surtunme_agirlik"] / 100.0
                     * (t["Mcwt"] + t["MCRcwt"])
                     * (t["gn"] - isl * t["a"]))
        else:
            FRcar = FRcwt = 0.0
        T1 = _T1(t, FRcar, isl)
        T2 = _T2(t, FRcwt, isl)
        #  HALAT KUVVETİ SIFIRIN ALTINA İNEMEZ.  T ≤ 0, halatın gevşemesi
        #  demektir;  o noktada tahrik modeli ( T1/T2 ≤ e^(f·α) ) geçersizdir,
        #  çünkü sürtünme bağıntısı GERGİN halat varsayar.
        #  Oran max(a/b, b/a) olduğu için negatif bir kuvvet oranı da NEGATİF
        #  yapıyor ve "oran ≤ sınır" karşılaştırması sessizce GEÇİYORDU:
        #  a = 1 gn'de T2 = −48,8 N çıkıp bölüm "UYGUNDUR" diyordu.
        #  Eskiden T tam sıfıra denk geldiği için _oran None döner ve durum
        #  tesadüfen yakalanırdı;  kasnak atalet terimi eklenince sıfırı
        #  geçip negatife düştü ve tesadüf bozuldu.
        gergin = T1 > 0 and T2 > 0
        GEVSEK = ("HALAT GEVŞİYOR — T1 ya da T2 sıfırın altına iniyor, "
                  "tahrik bağıntısı bu noktada geçerli değildir")
        if durum == "bloke":
            oran = T1 / T2 if T2 else None
            f_kul = f_bloke
            sinir = math.exp(f_kul * alfa) if alfa_var else None
            #  T1 · T2 · oran GERÇEKTİR ve paftada durur;  açı yoksa ya da
            #  çift sarıma ait değilse karara bağlanamayan yalnız SINIRDIR.
            uygun = (gergin and oran is not None and sinir is not None
                     and sinir <= oran)
            metni = (f"e^(f·α) = {tr(sinir)}  ≤  T1/T2 = {tr(oran)}"
                     if gergin and sinir is not None else GEVSEK)
        else:
            oran = _oran(T1, T2)
            f_kul = f_yuk if durum == "yukleme" else f_fren
            sinir = math.exp(f_kul * alfa) if alfa_var else None
            uygun = (gergin and oran is not None and sinir is not None
                     and sinir >= oran)
            metni = (f"T1/T2 = {tr(oran)}  ≤  e^(f·α) = {tr(sinir)}"
                     if gergin and sinir is not None else GEVSEK)
        if not gergin:
            #  GEVŞEK HALAT AÇIDAN BAĞIMSIZ, KESİN BİR BAŞARISIZLIKTIR.  Açı
            #  girilmemiş olsa bile "eksik" ile örtülmez — genel hükümde
            #  "uygun değil"in "hesap eksik"ten önce gelmesinin sebebi budur.
            gevsek_var = True
            uygun, metni, kont_mesaj = False, GEVSEK, ""
        elif not alfa_var:
            #  Açı yoksa sınır yok;  hüküm verilmez, sebep satırda yazar.
            uygun, metni, kont_mesaj = False, ALFA_YOK, "HESAP EKSİK"
        elif not alfa_uygun or kanal_standart_disi:
            #  İKİNCİ KALKAN — imkânsız açı ya da standart dışı kanalla
            #  hesaplanan sınır bir ölçüt değildir;  satır "UYGUN" basmaz.
            uygun = False
            metni = (f"{ALFA_ARALIK_DISI} — hüküm verilemez" if not alfa_uygun
                     else f"{KANAL_STANDART_DISI} — hüküm verilemez")
            sinir_kaynak = "ölçüt DEĞİLDİR  ( girdi geçersiz )"
        if durum == "bloke" and _elektrikli:
            #  Hüküm dışıdır:  satır UYGUN / UYGUN DEĞİL basmaz, dayanağını yazar.
            kont_mesaj = "m.5.5.3 c) 2"
            metni = ("Koruma HALATIN KAYMASIYLA sağlanmıyor — makineyi "
                     "durduran elektrikli güvenlik tertibatı beyan edildi;  "
                     "bu satır hüküm vermez, tertibat projede gösterilmelidir")
            uygun = True
        elif not uygun and (alfa_var and alfa_uygun and not kanal_standart_disi
                            and not gevsek_var):
            _kalan.append(durum)
        tumu_uygun = tumu_uygun and uygun
        #  ORAN SATIRI KENDİ SAYILARINI VERMELİ.
        #  T1 ve T2 satırları TARAFA göre yazılır ( T1 = kabin tarafı ) —
        #  TS EN 81-50 m.5.11.2.1 hangisinin T1 olduğunu söylemez, yalnız
        #  "kasnağın iki yanındaki kuvvetler" der.  Ama ORAN büyük/küçüktür
        #  ( _oran ) ve "boş kabin en üstte frenleme"de büyük olan KARŞI
        #  AĞIRLIK tarafıdır:  paftada T1 = 4.653, T2 = 7.044 yazarken oran
        #  1,5137 çıkıyordu.  Okuyan 4.653/7.044 = 0,66 bulur ve satırı
        #  doğrulayamaz.  Bölmeyi YAPAN çifti yazıyoruz.
        #  ( referans proje bunun yerine BÜYÜK olana T1 der ve tarafı yük durumuna
        #    göre değiştirir;  bizim taraf etiketimiz sabittir — bkz. TEST 12. )
        if T1 and T2 and (T1 / T2) < (T2 / T1):
            o_pay, o_payda = T2, T1
        else:
            o_pay, o_payda = T1, T2
        #  Sınır yalnız açı varken kaydedilir.
        _kay(o, f"tahrik.{durum}", T1=T1, T2=T2, oran=oran)
        if sinir is not None:
            _kay(o, f"tahrik.{durum}", sinir=sinir)
        _fren = durum in ("fren_alt", "fren_ust")
        _car_isr, _cwt_isr = ("+", "−") if isl > 0 else ("−", "+")
        b["adimlar"] += [
            metin(baslik + " :", vurgu=True),
        ] + ([
            hesap(f"FRcar = %FRcar × ( P + Q + MCR + MTrav ) × ( gn {_car_isr} a )",
                  f"{tr(O['kuyu_surtunme_kabin'])} % × "
                  f"{tr(t['P'] + t['Q'] + t['MCRcar'] + t['MTrav'])} × "
                  f"( {tr(t['gn'])} {_car_isr} {tr(t['a'])} )", FRcar, "N",
                  "kuyudaki sürtünme  ·  formüle FRcar / r girer"),
            hesap(f"FRcwt = %FRcwt × ( Mcwt + MCR ) × ( gn {_cwt_isr} a )",
                  f"{tr(O['kuyu_surtunme_agirlik'])} % × "
                  f"{tr(t['Mcwt'] + t['MCRcwt'])} × "
                  f"( {tr(t['gn'])} {_cwt_isr} {tr(t['a'])} )", FRcwt, "N",
                  "kuyudaki sürtünme  ·  formüle FRcwt / r girer"),
        ] if _fren else []) + [
            hesap("T1  ( kabin tarafı )", "EN 81-50 m.5.11.2", T1, "N"),
            hesap("T2  ( karşı ağırlık tarafı )", "EN 81-50 m.5.11.2", T2, "N"),
            hesap("T1 / T2" if durum == "bloke" else "T1 / T2   ( büyük / küçük )",
                  f"{tr(o_pay)} / {tr(o_payda)}", oran, "", ondalik=4),
            hesap("e^(f·α)",
                  f"exp( {_trh(f_kul)} × {tr(alfa_derece)}° )" if alfa_var
                  else "α girilmedi", sinir, "", sinir_kaynak, 4),
            kontrol(metni, uygun, kont_mesaj),
        ]

    #  KALAN DURUMUN ADI VE ÖĞÜDÜ.  "bloke" ötekilerin TERSİ yöndedir
    #  ( orada kayma İSTENİR ), o yüzden öğüdü de terstir:  ötekiler sarılma
    #  açısını / sürtünmeyi BÜYÜTMEK ister, bloke KÜÇÜLTMEK ya da m.5.5.3 c) 2
    #  yoluna geçmek ister.  Tek bir "UYGUN DEĞİLDİR" ikisini ayırt ettirmiyordu.
    #  İKİ FRENLEME DURUMU AYIRT EDİLİR.  Başlıkların ikisi de "Acil
    #  frenleme" ile başlıyor;  parantezi atınca mühendis hangisinin kaldığını
    #  göremiyordu.
    KALAN_ADI = {"yukleme": "kabinin yüklenmesi",
                 "fren_alt": "acil frenleme ( dolu kabin altta )",
                 "fren_ust": "acil frenleme ( boş kabin üstte )",
                 "bloke": "karşı ağırlığın asılı kalması"}
    _ogut = ""
    if _kalan:
        _bloke_kaldi = "bloke" in _kalan
        _oteki = [KALAN_ADI[k] for k in _kalan if k != "bloke"]
        _kalan = [KALAN_ADI[k] for k in _kalan]
        _parca = []
        if _oteki:
            _parca.append("sarılma açısını ya da kanal sürtünmesini artırın "
                          "( denge zinciri de oranı düşürür )")
        if _bloke_kaldi:
            _parca.append("halat kaymıyor — kabin tavana çekilebilir;  "
                          "TS EN 81-20 m.5.5.3 c) 2 uyarınca makineyi durduran "
                          "elektrikli güvenlik tertibatı kullanılıyorsa "
                          "\"Yukarı kaçmaya karşı koruma\" alanından beyan edin")
        _ogut = "  —  kalan:  " + " · ".join(_kalan) + "  →  " + ";  ".join(_parca)
    b["sonuc"] = {"baslik": "KONTROL      dört yük durumunda tahrik yeteneği",
                  "metin": "UYGUNDUR." if tumu_uygun else
                           (f"UYGUN DEĞİLDİR — {ALFA_ARALIK_DISI}"
                            if alfa_var and not alfa_uygun else
                            f"UYGUN DEĞİLDİR — {KANAL_STANDART_DISI}"
                            if kanal_standart_disi else
                            "UYGUN DEĞİLDİR" + _ogut),
                  "uygun": bool(tumu_uygun)}
    if not alfa_var and gevsek_var:
        #  Kesin başarısızlık eksikten güçlüdür:  bölüm "uygun değil" kalır,
        #  açının eksikliği ayrıca söylenir ( proje uyarısı da çıkar ).
        b["sonuc"]["metin"] = ("UYGUN DEĞİLDİR — halat gevşiyor  ( ayrıca "
                               "sarılma açısı α girilmedi )")
    elif not alfa_var:
        b["sonuc"]["metin"] = ALFA_YOK
        b["eksik_hesap"] = ALFA_YOK
    return b


# =====================================================================
#  RAY HESABI ORTAK YARDIMCILARI
# =====================================================================
def _ray_tutarsizlik_notu(profil):
    """Seçilen ray profilinin tablo değerleri kendi içinde tutarlı mı.

    i = √(I/A) tanım gereğidir.  Tutmayan bir satır seçildiğinde projeci bunu
    BİLMELİDİR — sayı emniyetli tarafta olsa bile.
    """
    if profil not in MT.RAY_TUTARSIZ:
        return None
    for ad, eksen, tablo, hesap in MT.ray_tutarsizliklari():
        if ad == profil:
            return (f"RAY TABLOSU TUTARSIZ:  {profil} profilinde {eksen} = "
                    f"{tr(tablo)} yazılı, ama aynı satırdaki I ve A "
                    f"{eksen} = {tr(hesap)} veriyor ( √(I/A) ).  Tablodaki "
                    "küçük değer narinliği büyük gösterir, yani burkulma "
                    "EMNİYETLİ tarafta hesaplanır;  yine de doğrusu ISO 7465 "
                    "ya da ray imalatçısının veri sayfasından teyit "
                    "edilmelidir.")
    return None


def _ray_ozellik(profil):
    """Bir ray profilinin hesaba giren bütün kesit değerleri."""
    d = {k: MT.ray(profil, k)
         for k in ("A", "Ix", "Iy", "Wx", "Wy", "ix", "iy", "c")}
    #  BURKULMA NARİNLİĞİ EN KÜÇÜK ATALET YARIÇAPINDAN ÇIKAR.
    #  m.5.10.3 sembol listesi:  "i is the MINIMUM radius of gyration".
    #  Kolon hangi eksende zayıfsa orada burkulur;  ray konsolları iki yönde
    #  de aynı aralıkta bağladığı için seçici olan kesitin kendisidir.
    d["imin"] = min(d["ix"], d["iy"])
    d["h1_b_f"] = MT.ray_geo(profil, "h1_b_f")
    d["h1_f"] = MT.ray_geo(profil, "h1_f")
    d["b"] = MT.ray_geo(profil, "b")        # paten balatası yarı genişliği
    return d


def _moment(F, l):
    """Eğilme momenti  M = 3 · F · l / 16   ( iki açıklıklı sürekli kiriş )."""
    return SABIT["moment_pay"] * F * l / SABIT["moment_bolen"]


def _flans(F, p, balata, makarali=False):
    """Flanş eğilme gerilmesi  —  TS EN 81-50 m.5.10.5 / Ek C.2.1.4.

    Madde İKİ formül verir ve hangisinin geçerli olduğunu PATEN TİPİ söyler:

        makaralı paten :  σF = 1,85 · Fx / c²
        kaymalı  paten :  σF = 6 · Fx · ( h1 − b − f ) / ( c² · ( ℓ + 2·( h1 − f ) ) )

    ℓ, maddenin kendi sembol listesinde "the length of the guide shoe
    lining" — paten balatasının UZUNLUĞUDUR ( 1 rakamı değil ).  Makaralı
    patende madde ayrı bir bağıntı verir.
    """
    if makarali:
        return 1.85 * F / p["c"] ** 2
    return F * (p["h1_b_f"] * 6) / (p["c"] ** 2 * (balata + 2 * p["h1_f"]))


def _balata_boyu(g, p, kabin=True):
    """Paten balata uzunluğu ℓ  ( mm ).

    Girilmemişse ray tablosundaki balata YARI genişliğinden türetilir:
    ℓ = 2·b, yani kare balata kabulü.  Balatalar genelde genişliğinden
    uzundur;  kare kabulü ℓ'yi küçük tutar ve σF'yi EMNİYETLİ tarafta
    ( büyük ) bırakır.  Kesin değer paten imalatçısından alınmalıdır.

    GİRİLEN ℓ KABİN PATENİNİNDİR.  Karşı ağırlığın pateni başka bir parçadır
    ve genelde daha kısa balatalıdır;  kabinin ℓ'sini ona vermek σF'yi
    emniyetsiz tarafa çekerdi.  Karşı ağırlıkta ℓ her zaman kendi rayından
    türetilir ( kabin=False ).
    """
    d = g.get("paten_balata_boyu")
    if kabin and isinstance(d, (int, float)) and not isinstance(d, bool) and d > 0:
        return d, "GİRİŞ"
    return 2 * p["b"], "türetilen  ( 2 × balata yarı genişliği )"


def _sehim(F, l, I):
    """Sehim  δ = 0,7 · l³ · F / ( 48 · E · I )."""
    S = SABIT
    return S["sehim_katsayi"] * l ** 3 * F / (S["sehim_bolen"] * S["E"] * I)


RAY_CARE = (
    ("gerilme",  "eğilme / birleşik gerilme ( σm · σc )",
     "ray profilini büyütün ya da konsol aralığını küçültün"),
    ("burkulma", "burkulma ( σk )",
     "ray profilini büyütün ya da konsol aralığını küçültün"),
    ("sehim",    "sehim ( δ )",
     "ray profilini büyütün ya da konsol aralığını küçültün"),
    ("flans",    "flanş eğilmesi ( σF )",
     "ray profilini büyütün ya da paten balatasını uzatın  —  "
     "konsol aralığı bu kontrole GİRMEZ"),
    ("basma",    "normal işletme basma gerilmesi ( σv )",
     "ray profilini büyütün  —  konsol aralığı bu kontrole GİRMEZ"),
)


def _ray_metni(uygunlar, turler, ad_ray="ray"):
    """Ray bölümünün hükmü — ÇÖZÜM DÜŞEN KONTROLÜN TÜRÜNDEN YAZILIR.

    Aynı çözümü paylaşan kontroller TEK KEZ yazılır:  üç tür de "profili
    büyütün ya da konsol aralığını küçültün" diyorsa cümle üç kez
    tekrarlanmaz, adlar toplanır ve çözüm bir kere söylenir.
    """
    dusen = {t for t, u in zip(turler, uygunlar) if not u}
    gruplar = []                       # [ ( çare , [ ad … ] ) ]  —  sıra korunur
    for anahtar, ad, care in RAY_CARE:
        if anahtar not in dusen:
            continue
        for g in gruplar:
            if g[0] == care:
                g[1].append(ad)
                break
        else:
            gruplar.append((care, [ad]))
    if not gruplar:
        return "UYGUN DEĞİLDİR."
    return "UYGUN DEĞİLDİR — " + "  ;  ".join(
        "  ·  ".join(adlar) + "  →  " + care.replace("ray profilini", ad_ray + " profilini")
        for care, adlar in gruplar)


def _burkulma_mesaji(lam, deger, sperm):
    """Burkulma kontrolünün satır metni.

    ω çizelgesi 20 ≤ λ ≤ 250 arasında tanımlıdır.  λ bunun ÜSTÜNDEYSE σk
    hesaplanamaz ve satır eskiden  "σk = —  ≤  σperm = 205"  diye basılıp
    yanına UYGUN DEĞİL yazıyordu:  boş bir hücrenin yanında bir RET.  Paftayı
    okuyan, gerilmenin sınırı AŞTIĞINI sanır;  oysa hesap hiç yapılamamıştır.
    Sebep yazılır ve iki çözümün ikisi de söylenir  ( λ = l / imin ).
    """
    if deger is None:
        return (f"σk HESAPLANAMADI — λ = {trn(lam, 0)} , EN 81-50'nin ω "
                f"çizelgesi {MT.OMEGA_LAMBDA_MIN} … {MT.OMEGA_LAMBDA_MAX} "
                "arasını kapsar;  ray profilini büyütün ya da konsol "
                "aralığını küçültün")
    return f"σk = {tr(deger)}  ≤  σperm = {tr(sperm)} N/mm²"


def _burkulma_omega(l, imin, rm):
    """Narinlik ve ω  —  TS EN 81-50 m.5.10.3.

    ``imin`` EN KÜÇÜK atalet yarıçapıdır.  Madde sembol listesinde
    "i is the MINIMUM radius of gyration" der.  Kataloğun altı profilinden
    beşinde iy < ix olduğu için ix ile λ KÜÇÜK, ω da küçük çıkar — burkulma
    gerilmesi olduğundan düşük görünür ( 70 x 65 x 9'da ω %123 eksik ).

    ω RAY ÇELİĞİNİN çekme dayanımına da bağlıdır;  Rm = 370 ve 520 eğrileri
    arasında doğrusal ara değer alınır.

    λ ALT SINIRDA KIRPILIR.  ω tablosu 20 ≤ λ ≤ 250 arasında tanımlıdır;
    λ < 20 burkulmanın belirleyici olmadığı bölgedir ve tablonun ilk satırı
    kullanılır ( makine kaidesi hesabı da öyle yapar ).  ÜST sınırın
    dışında ω yoktur:  bu durumda None döner ve bölüm "burkulma hesabı
    yapılamadı" der — girdi doğrulaması bu geometriyi zaten reddeder,
    burası ikinci kalkandır.  Eskiden None doğrudan çarpıma giriyor ve
    motor ham bir TypeError ile çöküyordu.
    """
    lam = max(MT.OMEGA_LAMBDA_MIN, math.ceil(l / imin - 1e-9))
    return lam, MT.omega_en8150(lam, rm)


def _yuk_merkezi(merkez, sapma, Q, P, p_kolu, askı=0.0):
    """Yükün EN OLUMSUZ konumu  —  TS EN 81-20 m.5.7.2.3.4.

    Madde normatiftir:  "the rated load Q of the car shall be evenly
    distributed over those three quarters of the car area being in the MOST
    UNFAVOURABLE POSITION".  Kabin alanının 3/4'ü yüklenince yükün ağırlık
    merkezi kabin merkezinden  Dx/2 − 3·Dx/8 = Dx/8  kadar kayar;  Ek C'nin
    "xQ = xC + Dx/8" satırı bunun bir ÖRNEĞİDİR ( Ek C bilgilendiricidir ) ve
    kaymayı tek yönde gösterir.

    Yön SEÇİLMELİDİR.  Ek C.2.1.1'in payı  Q·xQ + P·xp  bir moment
    toplamıdır;  kabin merkezi ray ekseninin öbür yanındaysa ( xc < 0 ) boş
    kabinin momenti negatiftir ve yükü inatla + yönde kaydırmak onu
    DENGELER:  toplam moment küçülür, ray gerilmesi olduğundan küçük çıkar,
    program "UYGUNDUR" der.  Oysa yolcular öbür yana yığılırsa ray
    hesaplanandan büyük yük görür — emniyetsiz taraf.

    Bu yüzden ± iki konum da denenir ve momentin BÜYÜKLÜĞÜNÜ büyüteni
    seçilir.  Simetrik yerleşimde ( xc = 0 ) iki yön aynı sonucu verir.
    """
    sabit = P * (p_kolu - askı)
    arti, eksi = merkez + sapma, merkez - sapma
    return (arti if abs(Q * (arti - askı) + sabit) >= abs(Q * (eksi - askı) + sabit)
            else eksi)


def _ray_satirlari(eksen, kuvvet, F, l, W, I, adimlar, dstr=0.0):
    """Bir kuvvet için moment · gerilme satırlarını yazar, ( σ , δ ) döndürür.

    ADLANDIRMA TS EN 81-50 Ek C.2.1.1'İN KENDİSİDİR:

        Fx  →  My = 3·Fx·l/16  →  σy = My/Wy
        Fy  →  Mx = 3·Fy·l/16  →  σx = Mx/Wx

    Yani x yönündeki kuvvet rayı Y EKSENİ etrafında eğer.  Paftayı standartla karşılaştıran bir denetçi için
    bu, olmayan bir hata gibi görünüyordu.
    """
    M = _moment(F, l)
    #  GERİLME VE SEHİM BİRER BÜYÜKLÜKTÜR.
    #  Fx / Fy işaretlidir ve işaret YÖNÜ gösterir:  kabin merkezi ray
    #  ekseninin öbür yanındaysa ( xc < 0 ) kuvvet de moment de negatife
    #  düşer.  Ama rayın gördüğü gerilme ile yaptığı sehim, yönden bağımsız
    #  büyüklüklerdir;  "δ ≤ 5 mm" karşılaştırması işaretli yapılırsa
    #  −5,59 mm SESSİZCE geçer ( sınır 5 mm olmasına rağmen ).
    #  Kuvvet ve moment satırları işaretini korur — yön bilgisi paftada
    #  kalsın diye;  σ ve δ büyüklük olarak yazılır ve karşılaştırılır.
    sigma = abs(M) / W
    #  Ek C.2.1.5 / C.2.2.5 / C.2.3.5:  δ = 0,7·F·l³/(48·E·I) + δstr.
    #  δstr BİNANIN kendi sehimidir ve rayın sehimine EKLENİR.
    #  Varsayılan 0 — değeri yapı hesabından gelir.
    d = abs(_sehim(F, l, I)) + (dstr or 0.0)
    adimlar.extend([
        hesap(f"M{eksen} = 3 × F{kuvvet} × l / 16",
              f"3 × {tr(F)} × {trn(l, 0)} / 16", M, "N·mm", ondalik=0),
        hesap(f"σ{eksen} = | M{eksen} | / W{eksen}",
              f"| {trn(M, 0)} | / {trn(W, 0)}", sigma, "N/mm²"),
    ])
    return sigma, d


# =====================================================================
#  7 -  KABİN KILAVUZ RAYLARI     ( TS EN 81-50 m.C.2.1 / C.2.2 / C.2.3 )
# =====================================================================
def _kabin_raylari(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    #  P STANDARTTAKİ TANIMIYLA:  boş kabin + gezici kablo payı + denge
    #  zinciri  ( m.5.7.2.3.2 · bkz. _motor'daki P_std ).
    Q, P = o["Q"], o["P_std"]
    k1, k2, k3 = o["k1"], S["k2"], O["k3_yardimci"]
    Fp = g["klips_itme_kuvveti"] or 0.0
    dstr_x, dstr_y = g["yapi_sehim_x"] or 0.0, g["yapi_sehim_y"] or 0.0
    makarali = g["paten_tipi"] == "Makaralı"
    prof = g["kabin_ray_profili"]
    p = _ray_ozellik(prof)
    n, h, l = g["kabin_ray_sayisi"], g["kabin_paten_arasi"], g["kabin_konsol_arasi"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]

    #  RAY BOYU çizimden ( en uzun kabin rayı:  kuyu tabanından üst ucuna );
    #  yoksa eski yaklaşık ( seyir + son kat + tabliye − 200 + kuyu dibi − 300 ).
    ray_ciz = _cizim_olcusu(g, "kabin_ray_boyu")
    ray_boyu = float(ray_ciz) if ray_ciz else MG.toplam_ray_boyu(g)
    Mg = ray_boyu * MT.ray(prof, "Gr")
    #  ── RAYA BAĞLI YARDIMCI DONANIM  Maux  ( m.5.7.2.3.1 b) 2) ) ──────
    #  Ofisin 150 N'u ≈ 15 kg'dır:  raya cıvatalanan şalter, kam, kanal.  MAKİNE DAİRESİ OLAN bir asansörde doğrudur —
    #  makine yukarıda kendi kaidesinde durur.
    #
    #  MAKİNE DAİRESİZ ( MRL ) TESİSTE MAKİNE RAYIN ÜSTÜNE BİNER.  m.5.7.2.3.7
    #  bunu adıyla anar:  "If the machine or rope suspensions are fixed to the
    #  guide rails, additional load cases ... shall be considered."  Program
    #  bu durumda da 150 N kullanıyordu — referans proje aynı alana 1.000 kg yazar,
    #  yani 65 kat.
    #
    #  YENİ GİRDİ İSTENMEZ, ELDEKİ İKİ SAYI YÖNLENDİRİLİR:
    #      makinenin kendi ağırlığı            Gm   ( girdi )
    #    + tahrik kasnağına gelen statik yük   Tst  ( bölüm 1'de hesaplanıyor )
    #  referans projenin kendi notu da bunu tarif eder:  "the weight of the motor,
    #  the loads on the traction sheave from the cabin and counterweight, and
    #  the motor bedplate weight should all be summed".
    #
    #  Maux RAY BAŞINA BİR BÜYÜKLÜKTÜR.  m.5.7.2.3.7 açıkça böyle yazar:
    #  "Forces and torques PER GUIDE RAIL due to auxiliary equipment fixed to
    #   the guide rail Maux shall be considered".  150 N da ray başınadır ( şalter · kam · kanal ), o yüzden bölünmez.
    #
    #  TÜRETİLEN DEĞER İSE TOPLAMDIR:  Gm + Tst makinenin tamamının yüküdür.
    #  KABİN VE KARŞI AĞIRLIK RAYLARININ TOPLAM SAYISINA EŞİT bölünür — makine
    #  şasesi dört raya oturur ve yük simetrik paylaşılır kabul edilir
    #  ( bkz. _makine_ray_payi;  karşı ağırlık rayı aynı payı bölüm 8'de
    #  görür ).  Bir raya düşen yük ayrıca SORULMAZ ( kullanıcı kararı:
    #  imalatçının asimetrik değeri için duran kutu kaldırıldı ).
    #  SEÇİM YALNIZ MAKİNE DAİRESİZ TESİSTE GEÇERLİDİR.  Makine dairesi
    #  varsa makine kendi kaidesinde durur ve yükü bölüm 2'de hesaplanır;
    #  aynı yükü bir de raya bindirmek onu İKİ KEZ saymaktır ve paftaya
    #  çelişkili iki cümle yazar ( "kaide uygundur" + "makine raylarda" ).
    #  Kutu işaretli kalsa bile burada YOK SAYILIR — motor kararı verir,
    #  ekranın gizlemesi tek başına yetmez  ( eski proje dosyaları ekranı
    #  atlar ).
    #
    #  KAPSAM DIŞI BIRAKILAN DURUM:  m.5.7.2.3.7 "machine OR ROPE SUSPENSIONS
    #  are fixed to the guide rails" der.  Makine dairesi olan bir tesiste
    #  saptırma kasnakları raya bağlanabilir;  o zaman raya binen yük makine
    #  değil KASNAK TEPKİSİDİR ve Gm + Tst ile hesaplanamaz.  Bu durum bilerek
    #  kapsam dışıdır — türetme yanlış sonuç verirdi.
    _mrl = evet_mi(g.get("mk_yok"))
    _raya = MT.makine_raya_mi(g.get("makine_raya_biniyor"))
    MY = S["MY_kabin"]
    MY_kaynak = "KABUL"
    _pay = _makine_ray_payi(g, o)
    if _pay:
        MY, MY_kaynak = _pay
    #  KUYU TABANI DA AYNI SAYIYI GÖRÜR.  m.5.2.1.8.4 kalemleri sayarken bunu
    #  ADIYLA anar:  "...any additional reaction (N) occurring during
    #  emergency stopping (e.g. LOAD ON TRACTION SHEAVE DUE TO REBOUND WHEN
    #  MACHINE ON RAILS)".  Eskiden bölüm 9 sabiti doğrudan okuyordu ve
    #  makine raya binse bile 150 N kalıyordu.
    o["MY_kabin"] = MY
    o["MY_kaynak"] = MY_kaynak
    #  BİNAYA AKTARILAN YÜK.  Makine raya binmiyorsa yükü bina yapısına
    #  gider;  m.5.2.1.8.1 "yapı ... makine tarafından uygulanan yükleri
    #  taşıyabilecek" der ve Ek E bunu inşaat projesine devreder.  Program o
    #  yapıyı HESAPLAMAZ ama SAYIYI VERİR — inşaat mühendisine gidecek
    #  değeri kullanıcının ayrıca hesaplaması gerekmesin.
    o["makine_binaya"] = (((g["makine_agirligi"] or 0.0)
                           + (o.get("Tst_hesap") or 0.0)) * gn
                          if (_mrl and not _raya) else None)
    sperm_g = MT.sigma_perm_guvenlik(g["ray_celigi_rm"])
    sperm_n = MT.sigma_perm_normal(g["ray_celigi_rm"])
    dperm = S["dperm_kabin"]

    #  KABİN MERKEZİ çizimden ( kabinin iç tabanının ortası:  eşik arası +
    #  kabin eşiği + derinlik / 2 − RK );  yoksa eski yaklaşık D/2 + 130 − RK.
    xc_ciz = _cizim_olcusu(g, "kabin_merkezi_x")
    xc = float(xc_ciz) if xc_ciz is not None else (D / 2.0 + S["kabin_merkez_payi"]) - g["ray_kapi_arasi"]
    #  KABİN MERKEZİNİN y KAÇIKLIĞI HESABA GİRER.
    #  Ek C.1.2 yc'yi "kabin merkezinin ray koordinatlarına göre konumu",
    #  yp'yi "boş kabin kütlesinin (P) konumu" diye tanımlar;  ikisi de
    #  C.2.1.1 b), C.2.2.1 b) ve C.2.3.1 b)'de Fy'nin payına girer.
    #  Burada ikisi de SABİT SIFIR yazılıydı:  girdi listesinde "Kabin
    #  merkezinin y ekseninde kaçıklığı" diye bir kutu vardı, kullanıcı
    #  değer giriyordu ve Fy hiç değişmiyordu — kutu yalnız kapı eşiğinin
    #  konumunu ( yi, m.C.2.3 ) besliyordu.  200 mm kaçıklıkta Fy 836,7 N
    #  kalıyordu, doğrusu 2.567,9 N — EMNİYETSİZ taraf.
    #  ( referans projenin paftası da Yp'yi gerçek bir girdi olarak taşır:
    #    "Fy = k2·gn·( Q·(yQ−Ys) + P·(Yp−Ys) ) / ((n/2)·h)" )
    yc = g["kabin_kaciklik"]
    #  BOŞ KABİNİN AĞIRLIK MERKEZİ DE RAY EKSENİNDEN ÖLÇÜLÜR.
    #  Ek C.2.1.1'in  Fx = k1·gn·( Q·xQ + P·xp ) / ( n·h )  bağıntısındaki pay,
    #  sistemin RAY EKSENİNE göre devirici momentidir;  xQ ile xp aynı toplama
    #  giriyorsa ikisinin de orijini ray merkez çizgisi olmak ZORUNDADIR.
    #  xp kabin merkezinden ölçülürse yalnız kapı + mekanizma kütlesinin
    #  kaçıklığı sayılır, kabin gövdesinin ray eksenine göre kaçıklığı ( xc )
    #  düşer.  Ray ekseni kabin merkezinden geçtiğinde ( xc = 0 ) iki okuma
    #  çakışır ama ray kaydıkça ayrışır ve EMNİYETSİZ tarafa düşer:  ray–kapı
    #  arası 500 mm'de moment toplamı gerçeğin %79'u, 1000 mm'de %36'sı olur.
    #      gövde  ( P − mkapı )  →  xc
    #      kapı   ( mkapı )      →  xc − ( D/2 + mekanizma payı )
    #      xp = [ (P−mkapı)·xc + mkapı·( xc − (D/2+pay) ) ] / P = xc − xp_kapı
    #  KAPI DÜZELTMESİ BOŞ KABİN KÜTLESİNE GÖRE YAPILIR.  Kapı, kabinin
    #  KENDİ kütlesinin bir parçasıdır;  momenti boş kabin kütlesine bölünür.
    P_bos = o["P"]
    #  Kapı ağırlığı OFİS STANDARDIDIR ( asansör bazında sorulmaz ).
    m_kapi = O["kabin_kapisi_agirligi"]
    xp_kapi = (m_kapi * (D / 2.0 + g["kapi_mekanizma_payi"])) / P_bos
    #  AĞIRLIK MERKEZİ GİRİLMİŞSE TÜRETME YAPILMAZ  ( Ek C.1.2 ).
    #  Girilen değer standardın xp · yp'sidir:  ray ekseninden ölçülen, P'nin
    #  ( boş kabin + kapı + kabine asılı gezici kablo ve denge zinciri )
    #  ağırlık merkezi — m.5.7.2.3.2 "the mass centre of gravity of them".
    #  Kapı düzeltmesi de eklenen kütleler de onun içindedir;  referans proje de
    #  Xp · Yp'yi P'nin tamamına uygular.
    xp_giris = g.get("kabin_agirlik_merkezi_x")
    yp_giris = g.get("kabin_agirlik_merkezi_y")
    xp_verildi, yp_verildi = _sayi_mi(xp_giris), _sayi_mi(yp_giris)
    xp_bos = xc - xp_kapi
    #  m.5.7.2.3.2:  "The acting point of the masses of the empty car and
    #  components supported by the car such as ram, part of travelling cable,
    #  compensating ropes/chains (if any) P shall be the mass centre of
    #  gravity OF THEM."  —  yani P'ye eklenen kütlelerin de bir konumu
    #  vardır ve ortak ağırlık merkezi aranır.  Gezici kablonun ve zincirin
    #  yatay konumu bilinmez;  kabin merkezinde ( xc ) kabul edilir — kapının
    #  momentini seyreltmezler, kendi momentlerini xc'den katarlar:
    #
    #      xp = [ P_boş·xp_boş  +  ( MTrav + MCR )·xc ]  /  P
    #
    #  P = P_boş olduğunda ( zincirsiz, kablosuz ) eski davranışa döner.
    _ek = P - P_bos
    xp = float(xp_giris) if xp_verildi else (
        ((P_bos * xp_bos + _ek * xc) / P) if P else xp_bos)
    #  TÜRETİLİRKEN yp = yc:  kapı x yüzündedir, kabinin y merkezini
    #  kaydırmaz — x'teki gibi ayrı bir kapı düzeltmesi yoktur;  eklenen
    #  kütleler de kabin merkezinde olduğu için yp değişmez.
    yp = float(yp_giris) if yp_verildi else yc
    #  ASKI NOKTASI ( S ) GİRDİDİR.  Ek C.1.2'nin tanımı:  "xs, ys is the
    #  position of the suspension (S) in relation to the guide rail cross
    #  coordinates".  C.2.1.1'de geçmez ( güvenlik tertibatı rayı kavrar,
    #  tepki ray ekseninden ölçülür );  C.2.2.1 ve C.2.3.1 taşır.
    #  Eskiden sabit sıfırdı:  askısı eksantrik bir kabinde normal çalışma
    #  kuvvetleri yanlış çıkıyordu ( ±%100'ü aşan sapmalar ).
    xs, ys = g["aski_kaciklik_x"], g["aski_kaciklik_y"]
    #  KAPI KONUMU DA RAY EKSENİNDEN ÖLÇÜLÜR  ( Ek C.1.2 ).
    #  C.2.3'ün payı  gn·P·(xp − xs) + Fs·(xi − xs)  bir moment toplamıdır;
    #  xp ray ekseninden ölçülen İŞARETLİ bir konumdur, xi de öyle olmalıdır.
    #  Kapı, ray ekseninin kabin merkezinin TERS tarafındadır:  kabin merkezi
    #  +xc'de ise kapı düzlemi −RK'dedir.  Ray ekseni kabin merkezini geçince
    #  ( xc < 0 ) iki terim yanlış yönde toplanıyor ve eşik kuvveti boş
    #  kabinin momentini DENGELİYORDU:  1400 mm derinlikte RK = 1.200 mm iken
    #  Fx 8,2 N çıkıyor, doğrusu 864,4 N — 105 kat, EMNİYETSİZ taraf.
    #  Program eşik kuvvetinin noktasını çizimden alır:  m.5.7.2.3.6 onu kabin
    #  girişinin EŞİĞİNİN ORTASINA koyar ( kat eşiğinin kenarı değil ).
    xi_ciz = _cizim_olcusu(g, "esik_x")
    xi = float(xi_ciz) if xi_ciz is not None else -g["ray_kapi_arasi"]
    yi = g["kabin_kaciklik"]
    balata, balata_kaynak = _balata_boyu(g, p)
    #  KATSAYI ASANSÖRÜN TİPİNDEN GELİR  ( m.5.7.2.3.6 ) — beyan yükünden değil.
    tip = g.get("asansor_tipi") or MT.ASANSOR_TIPLERI[0]
    k_esik = MT.esik_katsayisi(tip)
    Fs = k_esik * gn * Q

    #  Durum 1  ( x ekseni ) ve Durum 2  ( y ekseni ) yük merkezleri.
    #  TS EN 81-50 Ek C.2.1.1:  yük yalnız ilgili eksende Dx/8 ya da Dy/8
    #  kadar kaydırılır;  ÖTEKİ eksendeki moment kolu kabin merkezidir.
    #  Yük ± kaydırılır, momenti büyüten yön seçilir  ( m.5.7.2.3.4 ).
    #
    #  YÖN HER YÜK DURUMU İÇİN AYRI SEÇİLİR.  C.2.1'in momenti
    #  ( Q·yQ + P·yp ) askı noktasını TAŞIMAZ;  C.2.2 ve C.2.3'ünki
    #  ( Q·(yQ−ys) + P·(yp−ys) ) taşır.  Askı ray ekseninde değilken en
    #  olumsuz yön ikisinde FARKLI olabilir — tek bir yön seçip ikisine
    #  birden vermek, güvenlik tertibatı durumunda yanlış yönü seçtiriyordu.
    #  ( xs = ys = 0 iken iki seçim çakışır;  eski davranış aynen korunur. )
    xQ1_g = _yuk_merkezi(xc, D / S["Dx_bolen"], Q, P, xp)          # C.2.1
    yQ2_g = _yuk_merkezi(yc, W / S["Dy_bolen"], Q, P, yp)
    xQ1_n = _yuk_merkezi(xc, D / S["Dx_bolen"], Q, P, xp, xs)      # C.2.2 · C.2.3
    yQ2_n = _yuk_merkezi(yc, W / S["Dy_bolen"], Q, P, yp, ys)
    #  Paftada gösterilen "Durum 1 / Durum 2" satırları güvenlik tertibatı
    #  durumunundur — bölümün hükmünü genelde o verir.
    xQ1, yQ1, xQ2, yQ2 = xQ1_g, yc, xc, yQ2_g

    b = Bolum("KABİN KILAVUZ RAYLARININ HESAPLANMASI", kimlik="kabin_raylari",
              kaynak="TS EN 81-50 m.C.2.1 / C.2.2 / C.2.3")
    ad = [
        hesap("P = boş kabin + gezici kablo payı + denge zinciri",
              f"{trn(o['P'], 0)} + {tr(o.get('MTrav') or 0)} + {tr(o.get('MCR') or 0)}",
              o["P_std"], "kg",
              "TS EN 81-20 m.5.7.2.3.2  ·  P'nin standarttaki tanımı"),
        veri("h", "Patenler arası düşey mesafe", h, "mm", "GİRİŞ"),
        veri("l", "Ray konsolları arasındaki en uzun mesafe", l, "mm", "GİRİŞ"),
        veri("n", "Ray sayısı", n, "adet", "GİRİŞ", 0),
        veri("", "Ray profili", prof, "", "ISO 7465"),
        hesap("Mg = ray boyu × Gr", f"{tr(ray_boyu)} m × {tr(MT.ray(prof, 'Gr'))} kg/m",
              Mg, "kg", CIZIMDEN + "  ·  en uzun kabin rayı" if ray_ciz else ""),
        *( [veri("", "Makine yükünün yolu",
                 MT.MAKINE_YUK_YOLU[1] if _raya else MT.MAKINE_YUK_YOLU[0], "",
                 "GİRİŞ  ·  TS EN 81-20 m.5.7.2.3.7")]
            + ([veri("", "Bina yapısına aktarılan makine yükü",
                     o["makine_binaya"], "N",
                     "m.5.2.1.8.1 · Ek E  —  inşaat projesine bildirilir", 0)]
               if o.get("makine_binaya") else [])
            if _mrl else [] ),
        veri("MY", "Raylara bağlı yardımcı donanım ağırlığı", MY, "N", MY_kaynak, 0),
        #  DARBE KATSAYILARI PAFTADA GÖRÜNSÜN.  k1 ve k2'nin değeri EN 81-20
        #  Çizelge 14'te YAZILIDIR;  k3 için çizelge sayı vermez ( "imalatçı
        #  tarafından, gerçek tesise göre belirlenir" ) — hangi sayının
        #  kullanıldığı denetçiye görünmelidir.
        veri("k1", "Güvenlik tertibatı darbe katsayısı", k1, "",
             f"EN 81-20 Çizelge 14  ·  {g['guvenlik_tertibati']}", 0),
        veri("k2", "Normal işletme darbe katsayısı", k2, "",
             "EN 81-20 Çizelge 14  ·  Running", 1),
        veri("k3", "Yardımcı donanım darbe katsayısı", k3, "",
             "KABUL  ·  EN 81-20 Çiz.14 sayı vermez, imalatçı belirler", 1),
        veri("xc", "Kabin merkezinin x mesafesi", xc, "mm",
             CIZIMDEN + "  ·  kabinin iç tabanının ortası" if xc_ciz is not None else ""),
        veri("yc", "Kabin merkezinin y mesafesi", yc, "mm"),
        *( [] if xp_verildi else
           [veri("", "Kabin kapısı ağırlığı  ( panel + mekanizma )", m_kapi, "kg",
                 "KABUL  ·  kapı kataloğu", 0)] ),
        veri("xp", "Boş kabin ağırlık merkezinin x mesafesi", xp, "mm",
             "GİRİŞ  ·  P'nin ağırlık merkezi  ( kapı, gezici kablo, zincir dahil )"
             if xp_verildi else
             f"xc − kapı katkısı  ( {trn(m_kapi, 0)} kg × "
             f"{trn(D / 2 + g['kapi_mekanizma_payi'], 0)} mm / {trn(P, 0)} kg )  ·  "
             "gövde kabin merkezinde kabul edilir"),
        veri("yp", "Boş kabin ağırlık merkezinin y mesafesi", yp, "mm",
             "GİRİŞ  ·  P'nin ağırlık merkezi" if yp_verildi else ""),
        veri("xs", "Askı noktasının x mesafesi", xs, "mm", _kaynak(g, "aski_kaciklik_x", "")),
        veri("ys", "Askı noktasının y mesafesi", ys, "mm"),
        veri("xi", "Kabin eşiğinin ortasının x mesafesi" if xi_ciz is not None
             else "Kabin kapısının x mesafesi", xi, "mm",
             CIZIMDEN + "  ·  m.5.7.2.3.6" if xi_ciz is not None else ""),
        veri("yi", "Kabin kapısının y mesafesi", yi, "mm"),
        #  E BİR OFİS KABULÜ DEĞİLDİR — kaynağı "KABUL" yazıyordu.  Çeliğin
        #  elastisite modülü standardın kendi verdiği sayıdır ve ofis
        #  sabitlerinden değiştirilmez;  kaynak kolonu artık onu gösterir.
        veri("E", "Çeliğin elastisite modülü", S["E"], "N/mm²",
             "EN 81-50 m.5.13  ·  EN 1993-1-1 m.3.2.6", 0),
        hesap(f"Fs = {tr(k_esik, 1)} × gn × Q      ( {tip} )",
              f"{tr(k_esik, 1)} × {tr(gn)} × {trn(Q, 0)}", Fs, "N",
              "TS EN 81-20 m.5.7.2.3.6  ·  asansör tipi GİRİŞ"),
        #  σperm = Rm / St  ( m.5.7.4.5 · Çizelge 15, A5 > %12 ) — yuvarlanmaz.
        hesap("σperm = Rm / 1,8      ( güvenlik tertibatı çalışması )",
              f"{trn(g['ray_celigi_rm'], 0)} / 1,8", sperm_g, "N/mm²",
              "EN 81-20 m.5.7.4.5  ·  Çizelge 15"),
        hesap("σperm = Rm / 2,25      ( normal işletme ve yükleme )",
              f"{trn(g['ray_celigi_rm'], 0)} / 2,25", sperm_n, "N/mm²",
              "EN 81-20 m.5.7.4.5  ·  Çizelge 15"),
        veri("δperm", "İzin verilen en büyük eğilme miktarı", dperm, "mm",
             "EN 81-20 m.5.7.4.6", 0),
        veri("ℓ", "Paten balatasının uzunluğu",
             "—" if makarali else balata,
             "" if makarali else "mm",
             "Makaralı paten  ( EN 81-50 m.5.10.5 makara formülü geçerlidir )"
             if makarali else balata_kaynak, 0),
        hesap(f"Durum 1 :  xQ = xc {'+' if xQ1 >= xc else '−'} D / 8",
              f"{tr(xc)} {'+' if xQ1 >= xc else '−'} {trn(D, 0)} / 8", xQ1, "mm",
              "EN 81-20 m.5.7.2.3.4  ·  yük en olumsuz konumda"),
        hesap(f"Durum 2 :  yQ = yc {'+' if yQ2 >= yc else '−'} W / 8",
              f"{tr(yc)} {'+' if yQ2 >= yc else '−'} {trn(W, 0)} / 8", yQ2, "mm",
              "EN 81-20 m.5.7.2.3.4  ·  yük en olumsuz konumda"),
    ]

    uygunlar = []
    #  KONTROLÜN TÜRÜ DE BİRİKTİRİLİR.  Hüküm bütün ret hâllerine
    #  "ray profilini büyütün ya da konsol aralığını küçültün" yazıyordu.
    #  İki kontrolde bu tavsiye FİZİKEN YANLIŞTIR:  flanş eğilmesi ( σF )
    #  yerel bir kuvvetten doğar, konsol aralığı l bağıntıya hiç girmez;
    #  normal işletme basma gerilmesi ( σv = ( Fv + k3·MY ) / A ) da yalnız
    #  kesit alanına bağlıdır.  Mühendis konsolları sıklaştırıp aynı sonucu
    #  alıyordu.
    turler = []

    def _kuvvet(eksen, k_ad, k, Qk, Pk, ref=0.0, ref_ad=""):
        """C.2.1 · C.2.2 eğilme kuvveti  —  ( formül , işlem , değer ).

            Fx = k × gn × ( Q·(xQ − xs) + P·(xp − xs) ) / ( n × h )
            Fy = k × gn × ( Q·(yQ − ys) + P·(yp − ys) ) / ( ( n / 2 ) × h )

        C.2.1'de moment askı noktasına göre değil alınır ( ref = 0 ).
        İŞLEM SAYILARLA BASILIR:  satırda formülün kendisi tekrar ediyordu,
        paftayı denetleyen sonuca hesap makinesiyle ulaşamıyordu — C.2.3 ve
        karşı ağırlık rayı zaten sayılarla basılıyordu.  Değer eski ifadenin
        AYNISIDIR ( x − 0 = x );  hiçbir sonuç değişmez.
        """
        #  Satır sütuna sığmayabilir ( işlem ≈ 74 mm ):  çarpımlar ve payda
        #  BAĞLANIR ki kırılma yalnız "+" ile "/" sınırına düşsün.
        yarim = eksen == "y"
        q_ad, p_ad = f"{eksen}Q", f"{eksen}p"
        if ref_ad:
            terim = f"Q·({q_ad}−{ref_ad}) + P·({p_ad}−{ref_ad})"
            sayi = (bagla(f"{trn(Q, 0)} × {tr(Qk - ref)}") + " + "
                    + bagla(f"{trn(P, 0)} × {tr(Pk - ref)}"))
        else:
            terim = f"Q·{q_ad} + P·{p_ad}"
            sayi = bagla(f"{trn(Q, 0)} × {tr(Qk)}") + " + " + bagla(f"{trn(P, 0)} × {tr(Pk)}")
        payda = (n / 2.0) * h if yarim else n * h
        return (f"F{eksen} = {k_ad} × gn × ( {terim} ) "
                + bagla("/ ( ( n / 2 ) × h )" if yarim else "/ ( n × h )"),
                f"{tr(k)} × {tr(gn)} × ( {sayi} ) "
                + bagla(f"/ ( {tr(n / 2.0)} × {trn(h, 0)} )" if yarim
                        else f"/ ( {trn(n, 0)} × {trn(h, 0)} )"),
                k * gn * (Q * (Qk - ref) + P * (Pk - ref)) / payda)

    def _kesim(baslik, kuvvetler, kk, sperm, omega=None, kayit=None):
        """Bir yükleme durumu için gerilme · burkulma · flanş · sehim satırları.

        kuvvetler  ( ( Fx , Fy ) durum 1 , ( Fx , Fy ) durum 2 );  her biri
                   _kuvvet()'in ( formül , işlem , değer ) üçlüsü.
        kayit  ara değerlerin ön eki ( ör. "kabin_ray.c21" );  her durum
               "<ön ek>.d1" / ".d2" altında  Fx · sy · Fy · sx · sm · sc ·
               sf · dx · dy  ( burkulmalı durumda ayrıca st )  olarak saklanır.
               TS EN 81-50 adlandırması:  Fx → My → Wy  ( σy ),
               Fy → Mx → Wx  ( σx ).
        """
        ad.append(metin(baslik, vurgu=True))
        sonuc = []
        tur = []
        for sira, (etiket, (fx, fy)) in enumerate(
                zip(("Durum 1  x-ekseni", "Durum 2  y-ekseni"), kuvvetler)):
            ad.append(metin(etiket + " :"))
            #  Fy'nin KENDİ bağıntısı yazılır.  İkisine de Fx'in formülü
            #  basılıyordu:  y ekseni kuvvetinin yanında x ekseni bağıntısı
            #  duruyor, üstelik paydası ( n·h ) görünüyordu — oysa C.2.1.1 b),
            #  C.2.2.1 b) ve C.2.3.1 b) Fy'yi ( n/2 )·h'ye böler ve hesap da
            #  öyle yapıyor.  Sayı doğruydu, PAFTA yanlış anlatıyordu.
            Fx, Fy = fx[2], fy[2]
            ad.append(hesap(fx[0], fx[1], Fx, "N"))
            ad.append(hesap(fy[0], fy[1], Fy, "N"))
            #  m.C.2.1.1:  Fx → My → Wy   ·   Fy → Mx → Wx
            sy, dx = _ray_satirlari("y", "x", Fx, l, p["Wy"], p["Iy"], ad, dstr_x)
            sx, dy = _ray_satirlari("x", "y", Fy, l, p["Wx"], p["Ix"], ad, dstr_y)
            sm = sx + sy
            sc = (kk["Fv"] + kk["k"] * MY) / p["A"] + sm
            ad.append(hesap("σm = σx + σy", f"{tr(sx)} + {tr(sy)}", sm, "N/mm²"))
            ad.append(kontrol(f"σm = {tr(sm)}  ≤  σperm = {tr(sperm)} N/mm²",
                              sm <= sperm))
            ad.append(hesap("σc = ( Fv + k × MY ) / A + σm",
                            f"( {tr(kk['Fv'])} + {tr(kk['k'])} × {trn(MY, 0)} ) / "
                            f"{trn(p['A'], 0)} + {tr(sm)}", sc, "N/mm²"))
            ad.append(kontrol(f"σc = {tr(sc)}  ≤  σperm = {tr(sperm)} N/mm²",
                              sc <= sperm))
            sonuc += [sm <= sperm, sc <= sperm]
            tur += ["gerilme", "gerilme"]
            if omega is not None:
                st = kk["sigma_k"] + S["birlesik_katsayi"] * sm
                ad.append(hesap("σ = σk + 0,9 × σm",
                                f"{tr(kk['sigma_k'])} + 0,9 × {tr(sm)}", st, "N/mm²"))
                ad.append(kontrol(f"σ = {tr(st)}  ≤  σperm = {tr(sperm)} N/mm²",
                                  st <= sperm))
                sonuc.append(st <= sperm)
                tur.append("gerilme")
            sf = abs(_flans(Fx, p, balata, makarali))
            ad.append(hesap(
                "σF = 1,85 × | Fx | / c²" if makarali else
                "σF = | Fx | × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
                (f"1,85 × {tr(abs(Fx))} / {tr(p['c'] ** 2)}" if makarali else
                 f"{tr(abs(Fx))} × {tr(p['h1_b_f'] * 6)} / "
                 f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}"),
                sf, "N/mm²", f"EN 81-50 m.5.10.5  ·  {g['paten_tipi'].lower()} paten"))
            ad.append(kontrol(f"σF = {tr(sf)}  ≤  σperm = {tr(sperm)} N/mm²",
                              sf <= sperm))
            ad.append(hesap("δx = | 0,7 × l³ × Fx / ( 48 × E × Iy ) | + δstr-x",
                            f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴"
                            + (f" ,  δstr-x = {tr(dstr_x)} mm" if dstr_x else ""),
                            dx, "mm"))
            ad.append(kontrol(f"δx = {tr(dx)}  ≤  δperm = {trn(dperm, 0)} mm",
                              dx <= dperm))
            ad.append(hesap("δy = | 0,7 × l³ × Fy / ( 48 × E × Ix ) | + δstr-y",
                            f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴"
                            + (f" ,  δstr-y = {tr(dstr_y)} mm" if dstr_y else ""),
                            dy, "mm"))
            ad.append(kontrol(f"δy = {tr(dy)}  ≤  δperm = {trn(dperm, 0)} mm",
                              dy <= dperm))
            sonuc += [sf <= sperm, dx <= dperm, dy <= dperm]
            tur += ["flans", "sehim", "sehim"]
            if kayit:
                degerler = dict(Fx=Fx, sy=sy, Fy=Fy, sx=sx, sm=sm, sc=sc,
                                sf=sf, dx=dx, dy=dy)
                if "sigma_k" in kk:          # burkulmayla birleşik gerilme
                    degerler["st"] = (kk["sigma_k"] + S["birlesik_katsayi"] * sm
                                      if omega else None)
                _kay(o, f"{kayit}.d{sira + 1}", **degerler)
        uygunlar.extend(sonuc)
        turler.extend(tur)

    # ── C.2.1  Güvenlik tertibatının çalışması ────────────────────────
    #  Ek C.2.1.2:  Fv = k1·gn·(P+Q)/n + Mg·gn + Fp.  Fp bir raydaki bütün
    #  konsol klipslerinin itme kuvvetidir.
    Fk = k1 * gn * (P + Q) / n + Mg * gn + Fp
    lam, omega = _burkulma_omega(l, p["imin"], g["ray_celigi_rm"])
    #  MY çarpanı burada da k3'tür — güvenlik tertibatı
    #  durumunda bile yardımcı donanım normal kullanma katsayısıyla alınır.
    sigma_k = ((Fk + k3 * MY) * omega / p["A"]) if omega else None
    burkulma_uygun = sigma_k is not None and 0 <= sigma_k <= sperm_g
    ad += [
        metin("Güvenlik Tertibatının Çalışması  ( TS EN 81-50 m.C.2.1 ) :", vurgu=True),
        hesap("Fk = k1 × gn × ( P + Q ) / n + Mg × gn + Fp",
              f"{tr(k1)} × {tr(gn)} × ( {trn(P, 0)} + {trn(Q, 0)} ) / {trn(n, 0)} "
              f"+ {tr(Mg)} × {tr(gn)}" + (f" + {tr(Fp)}" if Fp else ""), Fk, "N"),
        hesap("λ = l / imin", f"{trn(l, 0)} / {tr(p['imin'])}"
              f"   ( ix = {tr(p['ix'])} · iy = {tr(p['iy'])} )",
              l / p["imin"], ""),
        veri("λ", "Yuvarlanmış burkulma narinliği  ( en az 20 )", lam, "",
             "ω çizelgesi tam sayı λ ile okunur", 0),
        veri("ω", "Omega değeri", omega, "",
             (f"EN 81-50 m.5.10.3  ·  λ = {lam}  ·  Rm = {trn(g['ray_celigi_rm'], 0)}"
              if omega else
              f"TABLO DIŞI — λ = {lam} > {MT.OMEGA_LAMBDA_MAX};  konsol aralığını "
              "küçültün ya da daha büyük kesitli ray seçin"), 6),
        hesap("σk = ( Fk + k3 × MY ) × ω / A",
              f"( {tr(Fk)} + {tr(k3)} × {trn(MY, 0)} ) × {tr(omega)} / {trn(p['A'], 0)}",
              sigma_k, "N/mm²"),
        kontrol(_burkulma_mesaji(lam, sigma_k, sperm_g), burkulma_uygun),
    ]
    uygunlar.append(burkulma_uygun)
    turler.append("burkulma")
    _kesim("Eğilme gerilmesi  ( C.2.1 ) :",
           ((_kuvvet("x", "k1", k1, xQ1_g, xp), _kuvvet("y", "k1", k1, yc, yp)),
            (_kuvvet("x", "k1", k1, xc, xp), _kuvvet("y", "k1", k1, yQ2_g, yp))),
           {"Fv": Fk, "k": k3, "sigma_k": sigma_k}, sperm_g, omega,
           "kabin_ray.c21")

    # ── C.2.2  Normal çalışma, işletme ────────────────────────────────
    #  Ek C.2.2.2 / C.2.3.2:  Fv = Mg·gn + Fp   ( burada ω yoktur )
    Fv = Mg * gn + Fp
    sigma_v = (Fv + k3 * MY) / p["A"]
    ad += [
        metin("Normal Çalışma, İşletme  ( TS EN 81-50 m.C.2.2 ) :", vurgu=True),
        hesap("Fv = Mg × gn + Fp", f"{tr(Mg)} × {tr(gn)}"
              + (f" + {tr(Fp)}" if Fp else ""), Fv, "N"),
        hesap("σv = ( Fv + k3 × MY ) / A",
              f"( {tr(Fv)} + {tr(k3)} × {trn(MY, 0)} ) / {trn(p['A'], 0)}",
              sigma_v, "N/mm²"),
        kontrol(f"σv = {tr(sigma_v)}  ≤  σperm = {tr(sperm_n)} N/mm²",
                sigma_v <= sperm_n),
    ]
    uygunlar.append(sigma_v <= sperm_n)
    turler.append("basma")
    #  Ek C.2.2.1 katsayıyı k2 der ( EN 81-20 Çizelge 14:  Running = 1,2 ).
    #  Fy'nin paydası da C.2.1.1 b) ile aynıdır:  ( n / 2 ) · h  —  n·h
    #  Fy'yi YARISI kadar gösterirdi, emniyetsiz.
    _kesim("Eğilme gerilmesi  ( C.2.2 ) :",
           ((_kuvvet("x", "k2", k2, xQ1_n, xp, xs, "xs"),
             _kuvvet("y", "k2", k2, yc, yp, ys, "ys")),
            (_kuvvet("x", "k2", k2, xc, xp, xs, "xs"),
             _kuvvet("y", "k2", k2, yQ2_n, yp, ys, "ys"))),
           {"Fv": Fv, "k": k3}, sperm_n, None, "kabin_ray.c22")

    # ── C.2.3  Normal çalışma, yükleme ────────────────────────────────
    Fx3 = (gn * P * (xp - xs) + Fs * (xi - xs)) / (n * h)
    #  Ek C.2.3.1 b) paydası da ( n / 2 ) · h'dir.
    Fy3 = (gn * P * (yp - ys) + Fs * (yi - ys)) / ((n / 2.0) * h)
    ad.append(metin("Normal Çalışma, Yükleme  ( TS EN 81-50 m.C.2.3 ) :", vurgu=True))
    #  Çarpımlar ve payda bağlanır ( bkz. _kuvvet ).
    ad.append(hesap("Fx = ( gn × P × (xp−xs) + Fs × (xi−xs) ) " + bagla("/ ( n × h )"),
                    "( " + bagla(f"{tr(gn)} × {trn(P, 0)} × {tr(xp - xs)}") + " + "
                    + bagla(f"{tr(Fs)} × {tr(xi - xs)}") + " ) "
                    + bagla(f"/ ( {trn(n, 0)} × {trn(h, 0)} )"), Fx3, "N"))
    ad.append(hesap("Fy = ( gn × P × (yp−ys) + Fs × (yi−ys) ) " + bagla("/ ( ( n / 2 ) × h )"),
                    "( " + bagla(f"{tr(gn)} × {trn(P, 0)} × {tr(yp - ys)}") + " + "
                    + bagla(f"{tr(Fs)} × {tr(yi - ys)}") + " ) "
                    + bagla(f"/ ( {tr(n / 2.0)} × {trn(h, 0)} )"), Fy3, "N"))
    #  m.C.2.3:  Fx → My → Wy   ·   Fy → Mx → Wx
    sy3, dx3 = _ray_satirlari("y", "x", Fx3, l, p["Wy"], p["Iy"], ad, dstr_x)
    sx3, dy3 = _ray_satirlari("x", "y", Fy3, l, p["Wx"], p["Ix"], ad, dstr_y)
    sm3 = sx3 + sy3
    sc3 = (Fv + k3 * MY) / p["A"] + sm3
    sf3 = abs(_flans(Fx3, p, balata, makarali))
    ad += [
        hesap("σm = σx + σy", f"{tr(sx3)} + {tr(sy3)}", sm3, "N/mm²"),
        kontrol(f"σm = {tr(sm3)}  ≤  σperm = {tr(sperm_n)} N/mm²", sm3 <= sperm_n),
        #  σv yukarıda ( C.2.2 ) sayılarıyla basıldı;  burada o değer kullanılır.
        hesap("σc = σv + σm", f"{tr(sigma_v)} + {tr(sm3)}", sc3, "N/mm²"),
        kontrol(f"σc = {tr(sc3)}  ≤  σperm = {tr(sperm_n)} N/mm²", sc3 <= sperm_n),
        hesap("σF  ( flanş eğilmesi )", f"Fx = {tr(Fx3)} N", sf3, "N/mm²"),
        kontrol(f"σF = {tr(sf3)}  ≤  σperm = {tr(sperm_n)} N/mm²", sf3 <= sperm_n),
        hesap("δx", f"Iy = {trn(p['Iy'], 0)} mm⁴", dx3, "mm"),
        kontrol(f"δx = {tr(dx3)}  ≤  δperm = {trn(dperm, 0)} mm", dx3 <= dperm),
        hesap("δy", f"Ix = {trn(p['Ix'], 0)} mm⁴", dy3, "mm"),
        kontrol(f"δy = {tr(dy3)}  ≤  δperm = {trn(dperm, 0)} mm", dy3 <= dperm),
    ]
    uygunlar += [sm3 <= sperm_n, sc3 <= sperm_n, sf3 <= sperm_n,
                 dx3 <= dperm, dy3 <= dperm]
    turler += ["gerilme", "gerilme", "flans", "sehim", "sehim"]

    #  MY ( Maux ) makine raya biniyorsa türetilir — o yüzden o da kaydedilir.
    _kay(o, "kabin_ray", MY=MY, Mg=Mg, xc=xc, xp=xp, xi=xi, yi=yi, Fs=Fs,
         sperm_g=sperm_g, sperm_n=sperm_n, xQ1=xQ1, yQ2=yQ2, Fk=Fk,
         lam_ham=l / p["imin"], lam=lam, omega=omega, sigma_k=sigma_k,
         Fv=Fv, sigma_v=sigma_v)
    _kay(o, "kabin_ray.c23", Fx=Fx3, sy=sy3, Fy=Fy3, sx=sx3, sm=sm3, sc=sc3,
         sf=sf3, dx=dx3, dy=dy3)
    o.update(Fk_kabin=Fk, Mg_kabin=Mg, ray_boyu=ray_boyu)
    b["adimlar"] = ad
    hepsi = all(uygunlar)
    b["sonuc"] = {"baslik": "KONTROL      σm · σc · σF ≤ σperm   ve   δ ≤ δperm",
                  "metin": ("UYGUNDUR." if hepsi
                            else _ray_metni(uygunlar, turler)),
                  "uygun": bool(hepsi)}
    _not = _ray_tutarsizlik_notu(prof)
    if _not:
        b["notlar"] = [_not]
    b["aciklamalar"] = [
        "Adlandırma TS EN 81-50 Ek C.2.1.1'in kendisidir:  Fx → My → Wy ve "
        "Fy → Mx → Wx.  Yani x yönündeki kuvvet rayı Y ekseni etrafında eğer.",
        "Durum 1 yükü x ekseninde Dx/8, Durum 2 y ekseninde Dy/8 kadar "
        "kaydırır ( TS EN 81-50 Ek C.2.1.1 ); öteki eksendeki moment kolu her "
        "iki durumda da kabin merkezidir.",
        "Flanş eğilmesinde ℓ paten balatasının uzunluğudur ( EN 81-50 "
        "m.5.10.5 ). Girilmezse ray tablosundaki balata yarı genişliğinden "
        "2·b olarak türetilir; kesin değer paten imalatçısından alınmalıdır."]
    return b


# =====================================================================
#  8 -  KARŞI AĞIRLIK KILAVUZ RAYLARI              ( TS EN 81-50 m.5.10 )
# =====================================================================
def _agirlik_raylari(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    #  k2  normal işletme darbe katsayısı  ( EN 81-20 Çizelge 14 = 1,2 ),
    #  k3  yardımcı donanım katsayısı  —  çizelge ona sayı vermez, ofis verir.
    k2, k3 = S["k2"], O["k3_yardimci"]
    Fp = g["klips_itme_kuvveti"] or 0.0
    dstr_x, dstr_y = g["yapi_sehim_x"] or 0.0, g["yapi_sehim_y"] or 0.0
    #  YAN AĞIRLIKTA BİNA SEHİM EKSENLERİ RAYA GÖRE DÖNER.
    #  Kabin rayları kuyu yan duvarındadır ( ray x'i genişlik, y'si derinlik ).
    #  Karşı ağırlık yanda ( Sağ / Sol ) olduğunda raylar 90° dönük monte edilir:
    #  binanın X sehimi ağırlık rayının Y eksenine ( sırtına ), Y sehimi ise
    #  rayın X eksenine ( flanşına ) etki eder.  Arka ağırlıkta eksenler paraleldir.
    if g.get("agirlik_yeri") in ("Sağ", "Sol"):
        dstr_ray_x, dstr_ray_y = dstr_y, dstr_x
    else:
        dstr_ray_x, dstr_ray_y = dstr_x, dstr_y
    #  Karşı ağırlığın KENDİ paten tipi  ( kabininkinden ayrı seçilir ).
    paten = g["agirlik_paten_tipi"]
    makarali = paten == "Makaralı"
    prof = g["agirlik_ray_profili"]
    p = _ray_ozellik(prof)
    n = g["agirlik_ray_sayisi"]
    h, l = g["agirlik_paten_arasi"], g["agirlik_konsol_arasi"]
    #  m.5.7.2.3.3:  karşı ağırlığın kılavuzlama kuvvetleri "denge
    #  halatlarından/zincirlerinden ( varsa ) gelen kuvvetler" hesaba
    #  katılarak değerlendirilir.  Ağırlık EN ÜST konumdayken zincirin
    #  tamamı o taraftadır;  kabin rayıyla aynı anda olmadığı için çift
    #  sayma değildir  ( bkz. _motor'daki P_std açıklaması ).
    Mcwt = g["karsi_agirlik"] + (o.get("MCR") or 0.0)
    MY, MY_kaynak = S["MY_agirlik"], "KABUL"
    _pay = _makine_ray_payi(g, o)
    if _pay:
        MY, MY_kaynak = _pay
    o["MY_agirlik"] = MY
    o["MY_agirlik_kaynak"] = MY_kaynak
    sperm = MT.sigma_perm_normal(g["ray_celigi_rm"])

    gt = g.get("agirlik_guvenlik_tertibati") or "Yok"
    gt_var = gt != "Yok"
    #  TS EN 81-20 m.5.6.2.1.2.3:  karşı ağırlık ( ya da dengeleme ağırlığı )
    #  güvenlik tertibatı, BEYAN HIZI 1 m/s'yi AŞIYORSA kaymalı olmak
    #  zorundadır;  altında ani frenlemeli de olabilir.
    gt_tip_uygun = (not gt_var or not gt.startswith("Ani Frenlemeli")
                    or g["beyan_hizi"] <= S["agirlik_kaymali_esigi"])
    #  TS EN 81-20 m.5.7.4.6:  İzin verilen azami sehim ( δperm )
    #  a) Güv. tertibatlı kabin ve GÜV. TERTİBATLI KARŞI AĞIRLIK raylarında: 5 mm
    #  b) Güv. tertibatsız karşı ağırlık raylarında: 10 mm
    dperm = S["dperm_kabin"] if gt_var else S["dperm_agirlik"]

    #  KARŞI AĞIRLIĞIN KENDİ ÖLÇÜLERİ  —  Ek C.2.2'nin Gx ( derinlik ) ve
    #  Gy ( genişlik )'si.  İKİSİ DE GİRDİDİR;  eskiden derinlik malzemeden,
    #  genişlik ray arasından türetiliyordu ve ikisi de yanlıştı — ölçü imal
    #  edilen çerçevenin özelliğidir ( bkz. mukavemet_tablolari'ndeki
    #  "AĞIRLIK RAY ARASI → GENİŞLİK TABLOSU · KALDIRILDI" notu ).
    derinlik = g["agirlik_derinligi"]
    genislik = g["agirlik_genisligi"]
    Dxa = S["Dxa_katsayi"] * derinlik
    Dya = S["Dya_katsayi"] * genislik
    xsa = ysa = 0.0

    ray_a = _cizim_olcusu(g, "agirlik_ray_boyu")
    ray_boyu_a = float(ray_a) if ray_a else MG.toplam_ray_boyu(g)
    o["ray_boyu_agirlik"] = ray_boyu_a
    Mg = ray_boyu_a * MT.ray(prof, "Gr")
    #  Ek C.2.2.1:  katsayı k2'dir ve Fy'nin paydası ( n / 2 ) · h'dir.
    Fx = (k2 * gn * Mcwt * (Dxa - xsa)) / (n * h)
    Fy = (k2 * gn * Mcwt * (Dya - ysa)) / ((n / 2.0) * h)
    Mx, My = _moment(Fx, l), _moment(Fy, l)
    #  σ ve δ BÜYÜKLÜKTÜR  ( bkz. _ray_satirlari ).  Karşı ağırlıkta Dxa/Dya
    #  ve Mcwt pozitif olduğu için bugün işaret dönmüyor;  kural yine de
    #  kabin rayıyla AYNI tutulur — geometri kabulü değişirse iki bölüm
    #  sessizce ayrışmasın.
    sx, sy = abs(Mx) / p["Wy"], abs(My) / p["Wx"]
    sm = sx + sy
    Fv = Mg * gn + Fp
    sv = (Fv + k3 * MY) / p["A"]
    sc = sv + sm
    balata, balata_kaynak = _balata_boyu(g, p, kabin=False)
    sf = abs(_flans(Fx, p, balata, makarali))
    dx = abs(_sehim(Fx, l, p["Iy"])) + dstr_ray_x
    dy = abs(_sehim(Fy, l, p["Ix"])) + dstr_ray_y
    kontroller = [sm <= sperm, sc <= sperm, sf <= sperm, dx <= dperm, dy <= dperm,
                  gt_tip_uygun]
    #  kontroller ile AYNI SIRADA tür listesi  —  bkz. _ray_metni / RAY_CARE
    turler = ["gerilme", "gerilme", "flans", "sehim", "sehim", "tip"]

    #  ------------------------------------------------------------------
    #  KARŞI AĞIRLIKTA GÜVENLİK TERTİBATI      TS EN 81-50 Ek C.2.1
    #  ------------------------------------------------------------------
    #  TS EN 81-20 m.5.6.1:  kuyunun altındaki hacme girilebiliyorsa karşı
    #  ağırlıkta güvenlik tertibatı ZORUNLUDUR.  Tertibat varsa rayın asıl belirleyici yük durumu odur:  k1 = 2 … 5,
    #  yani ray kuvvetleri iki ila dört kat büyür.
    kg = None
    if gt_var:
        k1a = US.darbe_k1(o["ofis"], gt)
        sperm_g = MT.sigma_perm_guvenlik(g["ray_celigi_rm"])
        lam_a, omega_a = _burkulma_omega(l, p["imin"], g["ray_celigi_rm"])
        Fxg = (k1a * gn * Mcwt * (Dxa - xsa)) / (n * h)
        Fyg = (k1a * gn * Mcwt * (Dya - ysa)) / ((n / 2.0) * h)
        sxg = abs(_moment(Fxg, l)) / p["Wy"]
        syg = abs(_moment(Fyg, l)) / p["Wx"]
        smg = sxg + syg
        Fkg = (k1a * gn * Mcwt) / n + Mg * gn + Fp
        skg = ((Fkg + k3 * MY) * omega_a / p["A"]) if omega_a else None
        scg = (skg + S["birlesik_katsayi"] * smg) if skg is not None else None
        sfg = abs(_flans(Fxg, p, balata, makarali))
        dxg = abs(_sehim(Fxg, l, p["Iy"])) + dstr_ray_x
        dyg = abs(_sehim(Fyg, l, p["Ix"])) + dstr_ray_y
        #  Bölüm 9 bunu okur:  kuyu tabanına bildirilen yükte güvenlik
        #  tertibatı tepkisi AYRI bir kalemdir ( EN 81-20 m.5.2.1.8.4 ).
        o["Fk_agirlik"] = Fkg
        kg = {"k1": k1a, "sperm": sperm_g, "lam": lam_a, "omega": omega_a,
              "Fx": Fxg, "Fy": Fyg, "sx": sxg, "sy": syg, "sm": smg,
              "Fk": Fkg, "sk": skg, "sc": scg, "sF": sfg, "dx": dxg, "dy": dyg}
        kontroller += [
            smg <= sperm_g,
            skg is not None and 0 <= skg <= sperm_g,
            scg is not None and scg <= sperm_g,
            sfg <= sperm_g, dxg <= dperm, dyg <= dperm]
        turler += ["gerilme", "burkulma", "gerilme", "flans", "sehim", "sehim"]

    b = Bolum("KARŞI AĞIRLIK KILAVUZ RAYLARININ HESAPLANMASI", kimlik="agirlik_raylari",
              kaynak="TS EN 81-50 m.5.10  /  m.C.2.2" + ("  /  m.C.2.1" if gt_var else ""))
    b["adimlar"] = [
        veri("", "Ray profili", prof, "", "ISO 7465"),
        veri("n", "Ağırlık rayı sayısı", n, "adet", "GİRİŞ", 0),
        veri("h", "Ağırlık paten arası", h, "mm", "GİRİŞ"),
        veri("l", "Ağırlık rayı konsollar arası en uzun mesafe", l, "mm", "GİRİŞ"),
        #  KÜTLENİN NASIL KURULDUĞU YAZILIR:  bölüm 9'daki ağırlık tamponu
        #  kuvveti standardın P'siyle kurulur ve bu sayıdan biraz büyüktür;
        #  okuyan iki sayının kaynağını paftada görebilmelidir.
        veri("Mcwt", "Karşı ağırlık kütlesi", Mcwt, "kg",
             f"boş kabin + {tr(o['ofis']['q_denge'])} × Q"
             + ("  +  denge zinciri" if o.get("MCR") else "")),
        veri("", "Karşı ağırlıkta güvenlik tertibatı", gt, "", "GİRİŞ"),
        kontrol(f"{gt} tertibat, beyan hızı {tr(g['beyan_hizi'])} m/s"
                + ("  ( m.5.6.2.1.2.3:  v > 1 m/s ise KAYMALI olmalı )"
                   if gt_var else "  ( tertibat yok )"), gt_tip_uygun),
        veri("", "Karşı ağırlık malzemesi", g["agirlik_malzemesi"]),
        veri("Gx", "Karşı ağırlık derinliği", derinlik, "mm", "GİRİŞ", 0),
        veri("Gy", "Karşı ağırlık genişliği", genislik, "mm", "GİRİŞ", 0),
        hesap("Dxa = 0,1 × ağırlık derinliği",
              f"0,1 × {trn(derinlik, 0)}", Dxa, "mm"),
        hesap("Dya = 0,05 × ağırlık genişliği",
              f"0,05 × {trn(genislik, 0)}", Dya, "mm"),
        veri("xsa", "Askı noktasının x mesafesi", xsa, "mm"),
        veri("ysa", "Askı noktasının y mesafesi", ysa, "mm"),
        veri("MY", "Raylara bağlı yardımcı donanım", MY, "N", MY_kaynak, 0),
        veri("E", "Çeliğin elastisite modülü", S["E"], "N/mm²",
             "EN 81-50 m.5.13  ·  EN 1993-1-1 m.3.2.6", 0),
        veri("ℓ", "Paten balatasının uzunluğu",
             "—" if makarali else balata,
             "" if makarali else "mm",
             "Makaralı paten  ( EN 81-50 m.5.10.5 makara formülü geçerlidir )"
             if makarali else balata_kaynak, 0),
        hesap("Mg = ray boyu × Gr",
              f"{tr(ray_boyu_a)} m × {tr(MT.ray(prof, 'Gr'))} kg/m", Mg, "kg",
              CIZIMDEN + "  ·  en uzun ağırlık rayı" if ray_a else ""),
        metin("Eğilme gerilmesi  ( TS EN 81-50 m.C.2.2 ) :", vurgu=True),
        hesap("Fx = k2 × gn × Mcwt × ( Dxa − xsa ) / ( n × h )",
              f"{tr(k2)} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dxa)} / "
              f"( {trn(n, 0)} × {trn(h, 0)} )", Fx, "N"),
        hesap("Fy = k2 × gn × Mcwt × ( Dya − ysa ) / ( ( n / 2 ) × h )",
              f"{tr(k2)} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dya)} / "
              f"( {tr(n / 2.0)} × {trn(h, 0)} )", Fy, "N"),
        #  m.C.2.2.1:  Fx → My → Wy   ·   Fy → Mx → Wx
        hesap("My = 3 × Fx × l / 16", f"3 × {tr(Fx)} × {trn(l, 0)} / 16", Mx,
              "N·mm", ondalik=0),
        hesap("σy = My / Wy", f"{trn(Mx, 0)} / {trn(p['Wy'], 0)}", sx, "N/mm²"),
        hesap("Mx = 3 × Fy × l / 16", f"3 × {tr(Fy)} × {trn(l, 0)} / 16", My,
              "N·mm", ondalik=0),
        hesap("σx = Mx / Wx", f"{trn(My, 0)} / {trn(p['Wx'], 0)}", sy, "N/mm²"),
        metin("Burkulma :"),
        hesap("Fv = Mg × gn + Fp" if Fp else "Fv = Mg × gn",
              f"{tr(Mg)} × {tr(gn)}" + (f" + {tr(Fp)}" if Fp else ""), Fv, "N"),
        hesap("σv = ( Fv + k3 × MY ) / A",
              f"( {tr(Fv)} + {tr(k3)} × {trn(MY, 0)} ) / {trn(p['A'], 0)}", sv, "N/mm²"),
        metin("Birleşik gerilme :"),
        hesap("σm = σx + σy", f"{tr(sy)} + {tr(sx)}", sm, "N/mm²"),
        kontrol(f"σm = {tr(sm)}  ≤  σperm = {tr(sperm)} N/mm²", sm <= sperm),
        hesap("σc = σv + σm", f"{tr(sv)} + {tr(sm)}", sc, "N/mm²"),
        kontrol(f"σc = {tr(sc)}  ≤  σperm = {tr(sperm)} N/mm²", sc <= sperm),
        metin("Flanş eğilmesi :"),
        hesap("σF = 1,85 × | Fx | / c²" if makarali else
              "σF = | Fx | × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
              (f"1,85 × {tr(abs(Fx))} / {tr(p['c'] ** 2)}" if makarali else
               f"{tr(abs(Fx))} × {tr(p['h1_b_f'] * 6)} / "
               f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}"),
              sf, "N/mm²",
              f"EN 81-50 m.5.10.5  ·  {paten.lower()} paten"),
        kontrol(f"σF = {tr(sf)}  ≤  σperm = {tr(sperm)} N/mm²", sf <= sperm),
        metin("Sehim miktarları :"),
        hesap("δx = | 0,7 × l³ × Fx / ( 48 × E × Iy ) |" + (" + δstr-x" if dstr_ray_x else ""),
              f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴"
              + (f" ,  δstr = {tr(dstr_ray_x)} mm" if dstr_ray_x else ""), dx, "mm"),
        kontrol(f"δx = {tr(dx)}  ≤  δperm = {trn(dperm, 0)} mm", dx <= dperm),
        hesap("δy = | 0,7 × l³ × Fy / ( 48 × E × Ix ) |" + (" + δstr-y" if dstr_ray_y else ""),
              f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴"
              + (f" ,  δstr = {tr(dstr_ray_y)} mm" if dstr_ray_y else ""), dy, "mm"),
        kontrol(f"δy = {tr(dy)}  ≤  δperm = {trn(dperm, 0)} mm", dy <= dperm),
    ]
    if kg:
        sg = kg["sperm"]
        b["adimlar"] += [
            metin("Güvenlik Tertibatının Çalışması  ( TS EN 81-50 m.C.2.1 ) :",
                  vurgu=True),
            veri("k1", "Darbe katsayısı", kg["k1"], "",
                 f"KABUL  ·  {gt}"),
            veri("σperm", "Güvenlik tertibatı durumunda izin verilen gerilme",
                 sg, "N/mm²", f"Rm = {trn(g['ray_celigi_rm'], 0)}  ·  Rm / 1,8  ( m.5.7.4.5 )"),
            hesap("Fx = k1 × gn × Mcwt × ( Dxa − xsa ) / ( n × h )",
                  f"{tr(kg['k1'])} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dxa)} / "
                  f"( {trn(n, 0)} × {trn(h, 0)} )", kg["Fx"], "N"),
            hesap("σy = My / Wy        ( My = 3 × Fx × l / 16 )",
                  f"Wy = {trn(p['Wy'], 0)} mm³", kg["sx"], "N/mm²"),
            hesap("Fy = k1 × gn × Mcwt × ( Dya − ysa ) / ( ( n / 2 ) × h )",
                  f"{tr(kg['k1'])} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dya)} / "
                  f"( {tr(n / 2.0)} × {trn(h, 0)} )", kg["Fy"], "N"),
            hesap("σx = Mx / Wx        ( Mx = 3 × Fy × l / 16 )",
                  f"Wx = {trn(p['Wx'], 0)} mm³", kg["sy"], "N/mm²"),
            hesap("σm = σx + σy", f"{tr(kg['sy'])} + {tr(kg['sx'])}",
                  kg["sm"], "N/mm²"),
            kontrol(f"σm = {tr(kg['sm'])}  ≤  σperm = {tr(sg)} N/mm²",
                    kg["sm"] <= sg),
            hesap("Fk = k1 × gn × Mcwt / n + Mg × gn + Fp" if Fp else
                  "Fk = k1 × gn × Mcwt / n + Mg × gn",
                  f"{tr(kg['k1'])} × {tr(gn)} × {trn(Mcwt, 0)} / {trn(n, 0)} "
                  f"+ {tr(Mg)} × {tr(gn)}" + (f" + {tr(Fp)}" if Fp else ""), kg["Fk"], "N"),
            veri("λ", "Yuvarlanmış burkulma narinliği  ( en az 20 )",
                 kg["lam"], "", "", 0),
            veri("ω", "Omega değeri", kg["omega"], "",
                 (f"EN 81-50 m.5.10.3  ·  λ = {kg['lam']}" if kg["omega"] else
                  f"TABLO DIŞI — λ = {kg['lam']} > {MT.OMEGA_LAMBDA_MAX};  ray "
                  "profilini büyütün ya da konsol aralığını küçültün"), 6),
            hesap("σk = ( Fk + k3 × MY ) × ω / A",
                  f"( {tr(kg['Fk'])} + {tr(k3)} × {trn(MY, 0)} ) × "
                  f"{tr(kg['omega'])} / {trn(p['A'], 0)}", kg["sk"], "N/mm²"),
            kontrol(_burkulma_mesaji(kg["lam"], kg["sk"], sg),
                    kg["sk"] is not None and 0 <= kg["sk"] <= sg),
            hesap("σ = σk + 0,9 × σm",
                  f"{tr(kg['sk'])} + 0,9 × {tr(kg['sm'])}", kg["sc"], "N/mm²",
                  "EN 81-50 m.5.10.4"),
            kontrol(f"σ = {tr(kg['sc'])}  ≤  σperm = {tr(sg)} N/mm²",
                    kg["sc"] is not None and kg["sc"] <= sg),
            hesap("σF = 1,85 × | Fx | / c²" if makarali else
                  "σF = | Fx | × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
                  (f"1,85 × {tr(abs(kg['Fx']))} / {tr(p['c'] ** 2)}" if makarali else
                   f"{tr(abs(kg['Fx']))} × {tr(p['h1_b_f'] * 6)} / "
                   f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}"),
                  kg["sF"], "N/mm²",
                  f"EN 81-50 m.5.10.5  ·  {paten.lower()} paten"),
            kontrol(f"σF = {tr(kg['sF'])}  ≤  σperm = {tr(sg)} N/mm²",
                    kg["sF"] <= sg),
            hesap("δx = | 0,7 × l³ × Fx / ( 48 × E × Iy ) |" + (" + δstr-x" if dstr_ray_x else ""),
                  f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴"
                  + (f" ,  δstr = {tr(dstr_ray_x)} mm" if dstr_ray_x else ""), kg["dx"], "mm"),
            kontrol(f"δx = {tr(kg['dx'])}  ≤  δperm = {trn(dperm, 0)} mm",
                    kg["dx"] <= dperm),
            hesap("δy = | 0,7 × l³ × Fy / ( 48 × E × Ix ) |" + (" + δstr-y" if dstr_ray_y else ""),
                  f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴"
                  + (f" ,  δstr = {tr(dstr_ray_y)} mm" if dstr_ray_y else ""), kg["dy"], "mm"),
            kontrol(f"δy = {tr(kg['dy'])}  ≤  δperm = {trn(dperm, 0)} mm",
                    kg["dy"] <= dperm),
        ]
    b["sonuc"] = {"baslik": ("KONTROL      σm · σc · σF ≤ σperm   ve   δ ≤ δperm"
                             + ("   ( C.2.2 ve C.2.1 )" if gt_var else "")),
                  "metin": "UYGUNDUR." if all(kontroller)
                           else ("UYGUN DEĞİLDİR — karşı ağırlık güvenlik tertibatı v > 1,0 m/s "
                                 "için kaymalı tip olmalıdır ( TS EN 81-20 m.5.6.2.1.2.3 )"
                                 if not gt_tip_uygun else
                                 #  ω yoksa RET'in sebebi gerilmenin sınırı aşması
                                 #  değil, hesabın YAPILAMAMASIDIR;  ikisi farklı
                                 #  şeylerdir ve çözümleri de farklıdır.
                                 (f"UYGUN DEĞİLDİR — burkulma denetlenemedi:  λ = "
                                  f"{trn(kg['lam'], 0)} , ω çizelgesi en çok "
                                  f"{MT.OMEGA_LAMBDA_MAX}'ye kadar tanımlı.  Ağırlık "
                                  "rayı profilini büyütün ya da konsol aralığını "
                                  "küçültün"
                                  if (kg and kg.get("omega") is None) else
                                  _ray_metni(kontroller, turler, "ağırlık rayı"))),
                  "uygun": bool(all(kontroller))}
    _not8 = _ray_tutarsizlik_notu(prof)
    if _not8:
        b["notlar"] = [_not8]
    b["aciklamalar"] = [
        "TS EN 81-50 Ek C.2.2.1:  Fy → Mx → Wx;  y yönündeki kuvvet rayı X "
        "ekseni etrafında eğer.  Fy'den gelen gerilme Wx ile, sehim Ix ile "
        "hesaplanır.",
        "TS EN 81-20 m.5.6.1:  karşı ağırlıkta güvenlik tertibatı, kuyunun "
        "altındaki hacme girilebiliyorsa ZORUNLUDUR.  Tertibat varsa "
        "belirleyici yük durumu yalnız normal işletme ( m.C.2.2 ) değil "
        "m.C.2.1'dir ve orada k1 ( 2 · 3 · 5 ) geçer. "
        + ("Bu projede tertibat '" + gt + "' seçilmiştir ve m.C.2.1 de "
           "hesaplanmıştır." if gt_var else
           "Bu projede 'Yok' seçilmiştir;  kuyu dibindeki hacme "
           "girilebiliyorsa seçim gözden geçirilmelidir.")]
    #  MY de kaydedilir:  makine raylara biniyorsa türetilen bir değerdir.
    _kay(o, "agirlik_ray", derinlik=derinlik, genislik=genislik, Dxa=Dxa, Dya=Dya,
         Mg=Mg, MY=MY, Fx=Fx, sx=sx, Fy=Fy, sy=sy, Fv=Fv, sv=sv, sm=sm, sc=sc, sf=sf,
         dx=dx, dy=dy)
    o.update(Mg_agirlik=Mg)
    return b


# =====================================================================
#  9 -  KUYU TABANINA GELEN YÜKLER            ( TS EN 81-20 m.5.2.1.8 )
# =====================================================================
def _kuyu_tabani(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    #  P STANDARTTAKİ TANIMIYLA  ( m.5.2.1.8.5 / m.5.2.1.8.6 ).
    Q, P = o["Q"], o["P_std"]
    LR = o["ray_boyu"] * 1000.0                      # mm — kabin rayı
    LRa = (o.get("ray_boyu_agirlik") or o["ray_boyu"]) * 1000.0   # ağırlık rayı
    _lr_ciz = bool(_cizim_olcusu(g, "kabin_ray_boyu"))
    Gr_k = MT.ray(g["kabin_ray_profili"], "Gr")
    Gr_a = MT.ray(g["agirlik_ray_profili"], "Gr")
    #  RAY AĞIRLIĞI BİR KEZ SAYILIR.  TS EN 81-20 m.5.2.1.8.4 kalemleri tek
    #  tek sayar:  "the force due to the MASS OF THE GUIDE RAILS plus any load
    #  due to components fixed or linked to the guide(s) … plus the REACTION
    #  at the moment of operation of the safety gear".  Yani ray kütlesi ayrı
    #  bir kalem, güvenlik tertibatı tepkisi ayrı bir kalemdir.
    #
    #  Fk ( bölüm 7'nin Fv'si, EN 81-50 Ek C.2.1.2 ) zaten Mg·gn içerir;
    #  üstüne bir de gn·Gr·LR eklemek ray ağırlığını iki kez sayardı.
    ray_agirlik = gn * Gr_k * LR / 1000.0
    #  KLİPS İTME KUVVETİ HER RAYDA AYRI KALEMDİR.  m.5.2.1.8.4 son kalemi
    #  "any push through force exerted by the guide rails clips" diye sayar;
    #  güvenlik tertibatına bağlı değildir.  Eskiden kabin rayında Fk'nin
    #  içinde görünmeden geliyordu, karşı ağırlık rayında ise yalnız
    #  ağırlıkta tertibat varken sayılıyordu — tertibatsız karşı ağırlıkta
    #  kuyu tabanı yükü Fp kadar DÜŞÜK bildiriliyordu.
    Fp = g["klips_itme_kuvveti"] or 0.0
    #  Fk'den ray kütlesinin payı ve Fp düşülür;  geriye yalnız güvenlik
    #  tertibatının tepkisi ( k1·gn·(P+Q)/n ) kalır.
    guvenlik_tepkisi = o["Fk_kabin"] - o["Mg_kabin"] * gn - Fp
    #  ------------------------------------------------------------------
    #  RAYA BAĞLI DONANIM KUYU TABANINA k3 İLE İNER      m.5.2.1.8.4
    #  ------------------------------------------------------------------
    #  Madde kalemleri sayarken "any load due to components fixed or linked
    #  to the guide(s) AND/OR any additional reaction (N) occurring during
    #  EMERGENCY STOPPING ( e.g. load on traction sheave due to REBOUND when
    #  machine on rails )" der.  Geri tepmenin katsayısı m.5.7.4.3'ün
    #  k3'üdür:  "shall be multiplied with the impact factor k3 … to take
    #  into account the possible car … BOUNCE when the car … is stopped by a
    #  safety device".
    #
    #  Bölüm 7 ve 8 bunu zaten doğru yapıyordu ( σk · σv · σc hep k3·MY ile
    #  kurulur );  bölüm 9'da MY çarpansız ekleniyordu.  Aynı donanım aynı
    #  geri tepmeyi rayın gövdesinde yaşayıp tabanına yaşamıyor olamaz.
    #  Yön EMNİYETSİZDİ:  inşaat projesine bildirilen kuyu tabanı yükü
    #  olduğundan küçük çıkıyordu — makine raylara biniyorken MY birkaç kN
    #  olduğu için fark küçük değildir.
    k3 = O["k3_yardimci"]
    MY_k = (o.get("MY_kabin") or S["MY_kabin"])
    MY_a = (o.get("MY_agirlik") or S["MY_agirlik"])
    FKR = ray_agirlik + k3 * MY_k + guvenlik_tepkisi + Fp
    #  KARŞI AĞIRLIKTA GÜVENLİK TERTİBATI VARSA TEPKİSİ DE TABANA GELİR.
    #  Kabin tarafında bu kalem sayılıyordu, karşı ağırlıkta sayılmıyordu:
    #  tertibat "Kaymalı" seçilse bile FAR değişmiyordu.  Kuyu tabanı yükü
    #  OLDUĞUNDAN DÜŞÜK bildiriliyordu — inşaat projesine giden sayı budur.
    #  Ray kütlesinin payı burada da bir kez sayılır ( Fk − Mg·gn − Fp ).
    agirlik_tepkisi = (o["Fk_agirlik"] - o["Mg_agirlik"] * gn - Fp
                       if o.get("Fk_agirlik") is not None else 0.0)
    FAR = (gn * Gr_a * LRa / 1000.0) + k3 * MY_a + agirlik_tepkisi + Fp
    #  m.5.2.1.8.5 ve m.5.2.1.8.6 iki bağıntıyı da AÇIKÇA bu P ile yazar
    #  ( sembol listesinde "i.e. part of the travelling cable, compensating
    #  ropes/chains (if any)" ).  Ağırlık tamponunda da standardın kendi
    #  formülü 4·gn·( P + q·Q )'dur — karşı ağırlığın fiziksel kütlesi
    #  değil, standardın tanımladığı yük yazılır.
    Fkt = S["tampon_katsayi"] * gn * (P + Q)
    Fat = S["tampon_katsayi"] * gn * (P + o["ofis"]["q_denge"] * Q)
    #  ADET SIFIR YA DA BOŞ GİRİLİRSE 1 SAYILIR:  bölme çökmesin ve
    #  "tek tampon" en olumsuz ( en büyük ) tekil kuvveti versin.
    n_kt = max(1, int(g["kabin_tampon_adedi"] or 1))
    n_at = max(1, int(g["agirlik_tampon_adedi"] or 1))
    Fkt1, Fat1 = Fkt / n_kt, Fat / n_at

    b = Bolum("KUYU TABANINA GELEN YÜKLERİN HESAPLANMASI", kimlik="kuyu_tabani",
              kaynak="TS EN 81-20 m.5.2.1.8")
    b["adimlar"] = [
        hesap("P = boş kabin + gezici kablo payı + denge zinciri",
              f"{trn(o['P'], 0)} + {tr(o.get('MTrav') or 0)} + {tr(o.get('MCR') or 0)}",
              o["P_std"], "kg",
              "TS EN 81-20 m.5.2.1.8.5  ·  P'nin standarttaki tanımı"),
        *([veri("LR", "Kabin rayı boyu", LR, "mm", CIZIMDEN + "  ·  en uzun kabin rayı", 0),
           veri("Lar", "Ağırlık rayı boyu", LRa, "mm", CIZIMDEN + "  ·  en uzun ağırlık rayı", 0)]
          if _lr_ciz else
          [veri("LR", "Kılavuz ray boyu", LR, "mm",
                "H × 1000 + son kat + tabliye − 200 + kuyu dibi − 300"
                + ( "  ·  MRL:  tabliye yok ( 0 )" if evet_mi(g.get("mk_yok")) else ""), 0)]),
        #  FKR / FAR TEK BİR RAYIN KUVVETİDİR:  ray kütlesi bir rayındır,
        #  güvenlik tertibatı tepkisi ( P + Q ) / n'dir ( bölüm 7, Fk ).
        #  Başlık eskiden "raylarına" diyordu;  inşaat mühendisi sayıyı toplam
        #  sanıp raylara bölseydi yükün yarısını kullanırdı.  Avan aynı
        #  büyüklüğü zaten "bir kabin kılavuz rayına" diye yazıyor.
        metin("Bir kabin rayına gelen kuvvet  ( her ray altına ayrı ayrı ) :"),
        hesap("FKR = gn × Gr × LR / 1000 + k3 × MY + Fgt" + ("  +  Fp" if Fp else ""),
              f"{tr(gn)} × {tr(Gr_k)} × {trn(LR, 0)} / 1000 + "
              f"{tr(k3)} × {trn(MY_k, 0)} + {tr(guvenlik_tepkisi)}"
              + (f" + {tr(Fp)}" if Fp else ""), FKR, "N",
              "EN 81-20 m.5.2.1.8.4  ·  k3 : m.5.7.4.3 geri tepme"),
        veri("MY", "Kabin rayına bağlı donanım yükü", MY_k, "N",
             o.get("MY_kaynak") or "ofis kabulü", 0),
        veri("k3", "Yardımcı donanım darbe katsayısı", k3, "",
             "KABUL  ·  m.5.7.4.3  ( bölüm 7 ile aynı )"),
        veri("Fgt", "Güvenlik tertibatı çalışma tepkisi  ( Fk − Mg·gn"
             + ( " − Fp )" if Fp else " )"),
             guvenlik_tepkisi, "N",
             "ray kütlesi ayrı kalemdir, iki kez sayılmaz"),
        *( [veri("Fp", "Klips itme kuvveti  ( her rayda )", Fp, "N",
                 "GİRİŞ  ·  m.5.2.1.8.4 · m.5.7.2.3.5", 0)] if Fp else [] ),
        metin("Bir ağırlık rayına gelen kuvvet  ( her ray altına ayrı ayrı ) :"),
        hesap("FAR = gn × Gar × Lar / 1000 + k3 × Ma"
              + ("  +  Fgt" if agirlik_tepkisi else "") + ("  +  Fp" if Fp else ""),
              f"{tr(gn)} × {tr(Gr_a)} × {trn(LRa, 0)} / 1000 + "
              f"{tr(k3)} × {trn(MY_a, 0)}"
              + (f" + {tr(agirlik_tepkisi)}" if agirlik_tepkisi else "")
              + (f" + {tr(Fp)}" if Fp else ""),
              FAR, "N", "EN 81-20 m.5.2.1.8.4  ·  k3 : m.5.7.4.3 geri tepme"),
        veri("Fgt", "Karşı ağırlık güvenlik tertibatı çalışma tepkisi",
             agirlik_tepkisi if agirlik_tepkisi else "tertibat yok",
             "N" if agirlik_tepkisi else "",
             (f"{g['agirlik_guvenlik_tertibati']}  ·  Fk − Mg·gn"
              if agirlik_tepkisi else "karşı ağırlıkta güvenlik tertibatı seçilmedi")),
        metin("Kabin tamponlarına gelen kuvvetler :"),
        hesap("Fkt = 4 × gn × ( P + Q )",
              f"4 × {tr(gn)} × ( {trn(P, 0)} + {trn(Q, 0)} )", Fkt, "N"),
        veri("ncar", "Kabin tamponu adedi", n_kt, "adet", "GİRİŞ", 0),
        #  m.5.2.1.8.5:  kuvvet "evenly distributed between the total number
        #  of car buffers".  Döşemenin YEREL olarak taşıyacağı sayı budur;
        #  toplam kuvvet bütün tamponlara dağılır.
        hesap("Fkt1 = Fkt / ncar", f"{trn(Fkt, 0)} / {trn(n_kt, 0)}",
              Fkt1, "N", "m.5.2.1.8.5  ·  bir tampon altına"),
        metin("Ağırlık tamponlarına gelen kuvvetler :"),
        hesap("Fat = 4 × gn × ( P + q × Q )",
              f"4 × {tr(gn)} × ( {trn(P, 0)} + {tr(O['q_denge'])} × {trn(Q, 0)} )",
              Fat, "N", "m.5.2.1.8.6  ·  standardın P'si"),
        veri("ncwt", "Ağırlık tamponu adedi", n_at, "adet", "GİRİŞ", 0),
        hesap("Fat1 = Fat / ncwt", f"{trn(Fat, 0)} / {trn(n_at, 0)}",
              Fat1, "N", "m.5.2.1.8.6  ·  bir tampon altına"),
    ]
    b["notlar"] = [
        "Bu kuvvetler kuyu alt boşluğu tabanının ( temel / döşeme ) statik "
        "hesabına girer; inşaat projesine bildirilmelidir."]
    #  EKRANDA ⓘ:  ağırlık tamponu kuvvetindeki kütle ile bölüm 8'deki
    #  karşı ağırlık kütlesi AYNI SAYI DEĞİLDİR ve bu bilerek böyledir.
    #  Paftayı elden denetleyen biri farkı hata sanabiliyordu.
    b["aciklamalar"] = [
        "AĞIRLIK TAMPONU KUVVETİ STANDARDIN BAĞINTISIYLA YAZILIR.  TS EN 81-20 "
        "m.5.2.1.8.6:  F = 4·gn·( P + q·Q );  buradaki P, sembol listesinin "
        "tanımıyla boş kabin + kabinin taşıdığı parçalardır — gezici kablo payı "
        "ve varsa denge zinciri DÂHİL.  Bölüm 8'deki karşı ağırlık kütlesi "
        f"( Mcwt = boş kabin + q·Q{' + denge zinciri' if o.get('MCR') else ''} ) "
        "ise karşı ağırlığın fiziksel kütlesidir;  tahrik ve ray hesapları onu "
        "kullanır.  Aradaki fark gezici kablo payı kadardır;  standardın "
        "yazdığı büyük olandır, yani inşaat projesine bildirilen yük emniyetli "
        "taraftadır.",
    ]
    b["sonuc"] = {"baslik": "KUYU TABANI YÜKLERİ",
                  "metin": f"FKR = {tr(FKR)} N / ray  ·  FAR = {tr(FAR)} N / ray  ·  "
                           f"Fkt = {tr(Fkt)} N  ·  Fat = {tr(Fat)} N",
                  "uygun": None}
    _kay(o, "kuyu", LR=LR, FKR=FKR, FAR=FAR, Fkt=Fkt, Fat=Fat)
    o.update(FKR=FKR, FAR=FAR, Fkt=Fkt, Fat=Fat)
    return b


# =====================================================================
# 11 -  SIĞINMA ALANLARI VE AÇIKLIKLAR  ( EN 81-20 m.5.2.5.6 – 5.2.5.8 )
# =====================================================================
#  BİRLEŞİK PROGRAM:  açıklıklar kuyunun ÇİZİMİNDEN ölçülür ( cizim/dusey.py ).
#  Kabin ve karşı ağırlık uç konumlarındayken parçaların gerçek kotları ve
#  plandaki yerleri kullanılır:  kuyu tavanının en alt parçası sığınma
#  alanının, patenlerin ve korkuluğun TAM ÜSTÜNDEKİ parçadır ( makine şasesi,
#  halat bağlantısı, regülatör … ) ve kabinin üst kotu kabin iç yüksekliğinden
#  ve paten arasından çıkar.  Paftadaki tablo ile kesitteki ölçü aynı sayıdır.
#
#  ESKİDEN ofis paylarıyla ayrı bir model kuruluyordu:  kabin gövdesi 2.400,
#  kabin üstü 2.100, üst paten bir satırda 2.700, bir başkasında 2.900 kotta;
#  girilen paten arası hiç kullanılmıyordu.  Varsayılan asansörde çizim üst
#  patenin kuyu tavanına 150 mm girdiğini bulurken hesap "UYGUNDUR" diyordu.
def _siginma(g, o):
    from cizim import donanim as CDN
    from cizim import dusey as CDU
    from cizim import kopru as CK
    O, v = o["ofis"], o["v"]
    tip_ust = g.get("siginma_tipi_ust") or "Çömelme"
    tip_dip = g.get("siginma_tipi_dip") or "Çömelme"
    b = Bolum("SIĞINMA ALANLARI VE AÇIKLIKLARIN UYGUNLUĞU", kimlik="siginma_alanlari",
              kaynak="TS EN 81-20 m.5.2.5.6.2  /  m.5.2.5.7  /  m.5.2.5.8")
    b["notlar"] = [
        f"Beyan edilen sığınma duruşu — kabin üstü : {tip_ust}   ·   "
        f"kuyu dibi : {tip_dip}."]
    b["aciklamalar"] = [
        "AÇIKLIKLAR KUYUNUN ÇİZİMİNDEN ÖLÇÜLÜR:  kabin ve karşı ağırlık uç "
        "konumlarındayken parçaların gerçek kotları ve plandaki yerleri kullanılır "
        "( düşey kesitlerdeki ölçülerle aynı sayılar ).  Kuyu tavanının en alt kısmı, "
        "sığınma alanının, patenlerin ve korkuluğun tam üstündeki parçadır — tavan "
        "kirişi ya da makine şasesi, halat bağlantısı, regülatör ( m.5.2.5.7.2 ).",
        "Kabinin düşey ölçüleri ( şase altı, taban ve tavan kalınlığı, paten, fren "
        "bloğu, kabin kasnağı ) ve revizyon kutusunun yüksekliği ofis kabulüdür; "
        "TS EN 81-20 sayısı değildir.  Sabitler sekmesinden değiştirilir;  çizim de "
        "aynı sayıları kullanır.  Asgari açıklıklar doğrudan TS EN 81-20 m.5.2.5.7 ve "
        "m.5.2.5.8'dendir.",
        "KABİN EN ÜST KONUMU:  karşı ağırlık tam ezilmiş tamponunda + 0,035·v² "
        "( Çizelge 2 ).  Kabin EN ALT KONUMU:  kabin tam ezilmiş tamponunda. "
        "m.5.2.5.6.1.2 ve m.5.2.5.6.1.3'ün izin verdiği indirimler ( yavaşlama "
        "denetimi, denge halatı kilitleme tertibatı ) UYGULANMAZ — emniyetli taraftır.",
        "Raya yakın parçaların ( şase, paten, fren bloğu ) kuyu tabanına açıklığı, "
        "parçanın raya yatay XH ≤ 0,15 m uzaklıkta olduğu kabulüyle Şekil 7'den "
        "0,10 m alınır.",
        "SIĞINMA HACMİ TİPİ BİR BEYANDIR ( m.5.2.5.7.1 · m.5.2.5.8.1 ):  dik "
        "( 0,40 × 0,50 × 2,00 m ), çömelme ( 0,50 × 0,70 × 1,00 m ) ve — yalnız kuyu "
        "dibinde — yatarak ( 0,70 × 1,00 × 0,50 m ).  Alan kabin üstünde ve kuyu "
        "dibinde çizime yerleştirilir;  seçilen duruş kuyu dibinde işaretlenmeli ve "
        "projede belgelenmelidir."]
    _kay(o, "siginma", paten_tavan_asgari=SIGINMA["min_paten_tavan"])

    #  ÇİZİM:  hesabın girdisinden;  kabin ölçüleri bu hesabın ofis standardından.
    #  Motor tek başına çağrıldığında uygulama projesinin alanları ( kuyu
    #  genişliği, makine yerleşimi ) girdide olmayabilir:  varsayılanlarıyla.
    from engine.uygulama import girdi as UG
    G, hata = CK.cizim_girdisi({**UG.varsayilanlar(), **g,
                                "_ofis": {k: O[k] for k in CK.OFIS_SABITLERI}})
    Y = CDU.yerlesim(G) if G is not None else {"hata": hata}
    if "dip_aciklik" not in Y:
        #  Çizim kurulamadıysa açıklıklar ölçülemez:  hesap EKSİKTİR, sebebi yazılır.
        metin_ = "HESAP EKSİK — kuyunun çizimi kurulamadı:  " + "  ·  ".join(Y["hata"][:3]) + (
            f"  ( + {len(Y['hata']) - 3} )" if len(Y["hata"]) > 3 else "")
        b["adimlar"] = ([metin("Açıklıklar kuyunun çiziminden ölçülür;  çizim kurulamadı :",
                               vurgu=True)]
                        + [metin("·  " + h) for h in Y["hata"]])
        b["sonuc"] = {"baslik": "KONTROL      bütün sığınma ölçüleri", "metin": metin_,
                      "uygun": False}
        b["eksik_hesap"] = metin_
        return b

    dy, H = G["dusey"], Y["kotlar"][-1]
    b35 = 35.0 * v * v
    ad = [veri("", "En üst durak ( son kat ) yüksekliği", dy["son_kat"], "mm", "GİRİŞ", 0),
          hesap("Kabinin en üst konuma yükselmesi  =  ağırlık çarpma arası "
                "+ tampon ezilmesi + 0,035 × v² × 1000",
                f"{trn(dy['agirlik_carpma_arasi'], 0)} + {trn(dy['agirlik_tampon_ezilme'], 0)} + "
                f"0,035 × {tr(v)}² × 1000",
                Y["yukselme"], "mm", "TS EN 81-20 Çiz.2  ·  kabin açıklıkları bu konumda ölçülür", 0)]
    uygunlar, dusen = [], []

    def satir(etiket, deger, asgari, madde, ara):
        _kay(o, "siginma", **{ara: deger})
        uygun = deger >= asgari - 1e-9            # standart "en az" der
        uygunlar.append(uygun)
        if not uygun:
            dusen.append(f"{etiket}  ( {trn(deger, 0)} < {trn(asgari, 0)} mm )")
        ad.append(veri("", f"{etiket}  ( en az {trn(asgari, 0)} mm · {madde} )", deger, "mm",
                       "ÇİZİM", 0))
        ad.append(kontrol(f"{trn(deger, 0)} mm  ≥  {trn(asgari, 0)} mm", uygun))

    #  ── KABİN ÜSTÜ:  kabin en üst konumunda ─────────────────────────────
    ust, ua, ue = Y["ust"], Y["ust_aciklik"], Y["ust_engel"]
    ad.append(metin("Kabin tavanı üzerindeki sığınma alanı ve açıklıklar  ( m.5.2.5.7 · kabin "
                    "en üst konumunda ) :", vurgu=True))
    def alan(k):                              # standardın yazışıyla:  kısa × uzun
        a_, b_ = sorted(((k[2] - k[0]) / 1000.0, (k[3] - k[1]) / 1000.0))
        return f"{tr(a_)} × {tr(b_)} m"

    def parca(e):
        return CDN.TAVAN_PARCASI.get(e[1], e[1])
    ad.append(veri("", f"Kabin üstünde sığınma alanı — beyan edilen duruş :  {tip_ust}",
                   alan(Y["KU"]["siginma"]), "", "ÇİZİM  ·  korkulukların içinde, kapıya en yakın yer"))
    deger, asgari, madde = ua["siginma"]
    satir(f"Sığınma alanı / üstündeki en alt kısım ( {parca(ue['siginma'])} )", deger, asgari, madde,
          "kabin_ustu_tavan")
    #  m.5.2.5.7.2 a:  kabin üstündeki en yüksek donanım ( revizyon kutusu ) ile
    #  kabinin izdüşümündeki en alt tavan parçası
    z, ad_ = CDN.tavan_engeli(Y["M"], Y["KU"]["tavan"])
    satir(f"Revizyon kutusu / kuyu tavanının en alt kısmı ( {parca((z, ad_))} )",
          (z - H) - (ust["tavan"] + O["revizyon_payi"]), SIGINMA["min_revizyon"],
          "m.5.2.5.7.2 a", "revizyon_tavan")
    deger, asgari, madde = ua["paten"]
    satir(f"Üst paten / kuyu tavanının en alt kısmı ( {parca(ue['paten'])} )", deger, asgari, madde,
          "paten_tavan")
    if "kasnak" in ua:                        # kabin üstü askı:  kasnaklar kabin tavanında
        deger, asgari, madde = ua["kasnak"]
        satir(f"Kabin üstü kasnağı / kuyu tavanının en alt kısmı ( {parca(ue['kasnak'])} )", deger,
              asgari, madde, "kasnak_tavan")
    if "baglanti" in ua:                      # 1:1:  halat soketleri kabin şasesinin üstünde
        deger, asgari, madde = ua["baglanti"]
        satir(f"Kabindeki halat bağlantısı / kuyu tavanının en alt kısmı ( {parca(ue['baglanti'])} )",
              deger, asgari, madde, "baglanti_tavan")
    if "korkuluk" in ua:
        deger, asgari, madde = ua["korkuluk"]
        satir(f"Korkuluk / kuyu tavanının en alt kısmı ( {parca(ue['korkuluk'])} )", deger, asgari,
              madde, "korkuluk_tavan")
    deger, asgari, madde = ua["ray"]
    satir("Üst paten / kabin rayının üst ucu", deger, asgari, madde, "ust_paten_ray")
    deger, asgari, madde = ua["agirlik_ray"]
    satir("Karşı ağırlık üst pateni / rayın üst ucu  ( ağırlık en üst konumunda )", deger, asgari,
          madde, "agirlik_paten_ray")

    #  ── KUYU DİBİ:  kabin tam ezilmiş tamponunda ────────────────────────
    da, dip = Y["dip_aciklik"], Y["dip"]
    ad.append(metin("Kuyu dibindeki sığınma alanı ve açıklıklar  ( m.5.2.5.8 · kabin tam ezilmiş "
                    "tamponunda ) :", vurgu=True))
    ad.append(veri("", f"Kuyu dibinde sığınma alanı — beyan edilen duruş :  {tip_dip}",
                   alan(Y["KD"]["siginma"]), "",
                   "ÇİZİM  ·  kabinin izinin altında, tampon / gergi / merdiven dışında"))
    for ad_ara, et in (("siginma", "Kuyu tabanı / sığınma alanının üstündeki kabin"),
                       ("en_alt", "Kuyu tabanı / kabinin en alt kısmı"),
                       ("etek", "Kuyu tabanı / kabin eteği"),
                       ("sase", "Kuyu tabanı / şase, paten, fren bloğu ( raya yakın )")):
        deger, asgari, madde = da[ad_ara]
        satir(et, deger, asgari, madde, {"siginma": "dip_siginma", "en_alt": "kuyu_tabani_kabin",
                                         "etek": "etek", "sase": "ray_kabin_alt"}[ad_ara])
    #  m.5.2.5.8.2 b:  kuyuya sabit parça ( regülatör gergisi ) kabinin
    #  izdüşümündeyse kabinin en alt kısmıyla arası en az 0,30 m
    gr = Y["M"]["gergi"]
    kabin_izi = Y["KU"]["tavan"]
    if CDN._ortusur(gr["plan"], kabin_izi):
        satir("Regülatör gergi kasnağı / kabinin en alt kısmı",
              dip["taban_alti"] - (gr["merkez"] + gr["cap"] / 2.0), SIGINMA["min_regulator"],
              "m.5.2.5.8.2 b", "regulator_kabin")
    else:
        ad.append(metin("Regülatör gergi kasnağı kabinin izdüşümünde değil — m.5.2.5.8.2 b'nin "
                        "0,30 m'si aranmaz ( kuyu dibi planı ).", vurgu=False))
    #  Açıklık dışındaki fiziksel çakışmalar ( ağırlığın makine şasesine çarpması … )
    for h in Y.get("diger") or []:
        uygunlar.append(False)
        dusen.append(h)
        ad.append(kontrol(h, False))

    b["adimlar"] = ad
    b["sonuc"] = {"baslik": "KONTROL      bütün sığınma ölçüleri",
                  "metin": ("UYGUNDUR." if all(uygunlar)
                            else "UYGUN DEĞİLDİR — " + "  ·  ".join(dusen)),
                  "uygun": bool(all(uygunlar))}
    return b


# =====================================================================
#  GİRİŞ NOKTASI
# =====================================================================
# =====================================================================
#  TAMPONLARIN KONTROLÜ            ( TS EN 81-20 m.5.8.1 / m.5.8.2 )
# =====================================================================
def _tamponlar(g, o):
    """Tampon tipinin hıza ve strokun beyan hızına uygunluğu.

    BU BÖLÜM ÖNCEDEN HİÇ YOKTU.  Program tampon geometrisini yalnız
    YERLEŞİM için okuyordu:  ezilme miktarı sığınma açıklıklarına ve halat
    boyuna giriyordu, ama tamponun o hız için YETERLİ olup olmadığı hiç
    sorulmuyordu.  2,5 m/s beyan hızında 90 mm'lik bir tampon sessizce
    "uygun" geçiyordu — lineer tamponda gereken strok 844 mm'dir.

    Standart üç ayrı kural koyar ve hangisinin geçerli olduğunu TAMPON TİPİ
    belirler ( bkz. mukavemet_tablolari.TAMPON_TIPLERI ):

        m.5.8.1.5    enerji biriktirmeli tampon  →  v ≤ 1 m/s
        m.5.8.2.1.1  lineer                      →  strok ≥ 0,135·v² , ≥ 65 mm
        m.5.8.2.2.1  enerji yutmalı              →  strok ≥ 0,0674·v²
        m.5.8.2.1.2  lineer olmayan              →  formül yok, TİP DENEYİ

    Lineer olmayan ( poliüretan ) tamponda strok bir bağıntıdan çıkmaz;
    m.5.8.2.1.2.1 yavaşlama ölçütlerini tip deneyine bırakır.  Orada
    denetlenebilen tek sayısal kural hız sınırıdır — bölüm bunu söyler ve
    strok için tip inceleme belgesine yollar.
    """
    v = g["beyan_hizi"]
    ad_t, biriktirmeli, katsayi = MT.tampon(g["tampon_tipi"])
    e_kabin = g["kabin_tampon_ezilme"]
    e_agirlik = g["agirlik_tampon_ezilme"]

    b = Bolum("TAMPONLARIN KONTROLÜ", kimlik="tamponlar",
              kaynak="TS EN 81-20 m.5.8.1 / m.5.8.2")
    ad = [
        veri("", "Tampon tipi", ad_t, "", "GİRİŞ"),
        veri("v", "Beyan hızı", v, "m/s", "GİRİŞ"),
        veri("", "Kabin tamponu strok ( ezilme ) miktarı", e_kabin, "mm", "GİRİŞ", 0),
        veri("", "Ağırlık tamponu strok ( ezilme ) miktarı", e_agirlik, "mm", "GİRİŞ", 0),
    ]
    uygunlar = []

    #  ── m.5.8.1.5  TİP / HIZ UYUMU ────────────────────────────────────
    hiz_uygun = (not biriktirmeli) or v <= MT.TAMPON_BIRIKTIRMELI_AZAMI_HIZ
    ad += [
        metin("Tip ve beyan hızı  ( m.5.8.1.5 / m.5.8.1.6 ) :", vurgu=True),
        kontrol(
            (f"Enerji biriktirmeli tampon:  v = {tr(v)} m/s  ≤  "
             f"{tr(MT.TAMPON_BIRIKTIRMELI_AZAMI_HIZ)} m/s" if biriktirmeli else
             f"Enerji yutmalı tamponda hız sınırı yoktur  ( v = {tr(v)} m/s )"),
            hiz_uygun),
    ]
    uygunlar.append(hiz_uygun)

    #  ── STROK ────────────────────────────────────────────────────────
    if katsayi is None:
        #  Lineer olmayan:  strok bağıntısı yok, tip deneyi belirler.
        #  PAFTAYA TEK SATIR.  Uzun anlatım ekranda ⓘ altında durur
        #  ( aciklamalar );  pafta hesap belgesidir, ders anlatmaz.
        ad += [
            metin("Strok  ( m.5.8.2.1.2 ) :", vurgu=True),
            veri("", "Strok bağıntısı", "TİP DENEYİ", "",
                 "m.5.8.2.1.2.1 — yavaşlama ölçütleri, AT tip inceleme belgesi"),
        ]
        gereken = None
    else:
        gereken = katsayi * v * v * 1000.0            # m  →  mm
        alt = MT.TAMPON_ASGARI_STROK if biriktirmeli else 0.0
        gereken = max(gereken, alt)
        madde = "m.5.8.2.1.1.1" if biriktirmeli else "m.5.8.2.2.1"
        #  KATSAYI STANDARTTAKİ HANESİYLE YAZILIR.  tr() iki haneye yuvarlar:
        #  paftada "0,07 × 1,60² × 1000 = 173" duruyordu ( 0,07 ile 179 çıkar,
        #  hesap 0,0674 ile yapılıyordu );  lineer tamponda 0,135 → "0,14".
        _k = _trh(katsayi)
        ad.append(metin(f"Gereken strok  ( {madde} ) :", vurgu=True))
        ad.append(hesap(
            f"s = {_k} × v² × 1000",
            f"{_k} × {tr(v)}² × 1000", katsayi * v * v * 1000.0, "mm",
            madde, 0))
        if biriktirmeli:
            ad.append(veri("", "En küçük strok  ( madde alt sınırı )",
                           MT.TAMPON_ASGARI_STROK, "mm", madde, 0))
            ad.append(hesap("s = max( hesap ; alt sınır )",
                            f"max( {trn(katsayi * v * v * 1000.0, 0)} ; "
                            f"{trn(MT.TAMPON_ASGARI_STROK, 0)} )",
                            gereken, "mm", ondalik=0))
        for etiket, e in (("Kabin", e_kabin), ("Ağırlık", e_agirlik)):
            iyi = isinstance(e, (int, float)) and e >= gereken - 1e-9
            ad.append(kontrol(
                f"{etiket} tamponu:  strok = {trn(e, 0)} mm  ≥  "
                f"{trn(gereken, 0)} mm", iyi))
            uygunlar.append(iyi)

    b["adimlar"] = ad
    b["aciklamalar"] = [
        "LİNEER OLMAYAN TAMPONDA STROK BİR BAĞINTIDAN ÇIKMAZ.  "
        "m.5.8.2.1.2.1 ortalama yavaşlamanın 1 gn'yi, 2,5 gn üstü sürenin "
        "0,04 s'yi, tepe yavaşlamanın 6 gn'yi aşmamasını ister ve bunları "
        "TİP DENEYİNE bırakır;  tamponun beyan yükü ( P + Q ) ve çarpma hızı "
        "için belgeli olduğu AT tip inceleme belgesinden doğrulanmalıdır.",
        "Tampon strokları YERLEŞİME de girer:  aynı sayı sığınma "
        "açıklıklarında ( m.5.2.5.7 / m.5.2.5.8 ) ve halat boyunda "
        "kullanılır — bkz. bölüm 'SIĞINMA ALANLARI'.",
        "TS EN 81-20 m.5.8.1.7:  lineer olmayan ve enerji yutmalı tamponlar "
        "GÜVENLİK BİLEŞENİDİR;  TS EN 81-50 m.5.5'e göre doğrulanır ve "
        "üzerinde tip inceleme belge numarası bulunur ( m.5.8.1.8 ).",
    ]
    tumu = all(uygunlar)
    if tumu:
        metni = ("Tip uygun — strok tip inceleme belgesinden doğrulanır."
                 if gereken is None else "UYGUNDUR.")
    else:
        #  GEREKÇE GERÇEKTEN DÜŞEN KONTROLDEN YAZILIR.
        #  Tip/hız düşüp strok geçtiğinde ( ör. 1,6 m/s'de 400 mm stroklu
        #  YAYLI tampon:  346 mm gerekiyor, 400 mm var ) hüküm yine de
        #  "en az 346 mm strok gerekir" diyordu.  Strok zaten yeterliydi;
        #  asıl engel m.5.8.1.5'ti — enerji biriktirmeli tampon 1 m/s
        #  üstünde HİÇBİR strokla kullanılamaz.  Mühendis paftadaki
        #  gerekçeye bakıp daha uzun yay arar, aynı yere çıkardı.
        _neden = []
        if not hiz_uygun:
            _neden.append("tampon tipi bu hıza uygun değil")
        if gereken is not None and not all(uygunlar[1:]):
            _neden.append(f"en az {trn(gereken, 0)} mm strok gerekir")
        metni = "UYGUN DEĞİLDİR — " + "  ·  ".join(_neden) + "."
    b["sonuc"] = {"baslik": "KONTROL TİP · HIZ · STROK", "metin": metni,
                  "uygun": tumu}
    o.update(tampon_gereken_strok=gereken, tampon_biriktirmeli=biriktirmeli)
    return b


BOLUM_URETICILERI = (_motor, _makine, _kabin_alani, _aski_halatlari, _regulator,
                     _tahrik, _kabin_raylari, _agirlik_raylari, _kuyu_tabani,
                     _tamponlar, _siginma)


# =====================================================================
#  GENEL HÜKÜM  —  TEK YERDE ÜRETİLİR
# =====================================================================
#  Üç hüküm vardır ve SIRALARI ÖNEMLİDİR:
#
#      UYGUN DEĞİLDİR  —  en az bir bölüm GERÇEKTEN kaldı
#      HESAP EKSİK     —  kalan yok, ama yapılamayan zorunlu hesap var
#      UYGUNDUR        —  ikisi de yok
#
#  SIRA TERS KURULAMAZ.  Eksik önce gelirse, dört bölümü çakılan bir proje
#  ekranda yalnız "HESAP EKSİK" der;  okuyan "bir alanı doldurayım geçer"
#  anlar ve tasarımın tutmadığını göremez.  Kesin olumsuzluk, eksiklikten
#  DAHA GÜÇLÜ bilgidir ve onu örtemez.
#
#  Eksik bir bölümün KENDİ sonucu da "uygun değil" işaretlidir ( regülatör ·
#  tahrik yeteneği ).  Bu yüzden "kaldı" sayılırken eksik bölümler DIŞARIDA
#  bırakılır — yoksa her eksik aynı zamanda "kaldı" görünür ve üstteki sıra
#  hiçbir zaman ikinci basamağa inemezdi.
#
#  HÜKÜM MOTORDAN ÇIKAR, ekran ve PDF onu YALNIZ BASAR.  İki kopya hâlinde
#  tutulduğu için ayrışmıştı:  PDF "HESAP EKSİK" derken ekranın rengi hâlâ
#  "uygun değil"i gösteriyordu.
def genel_hukum(bolumler, tumu_uygun, eksik=()):
    """( uzun hüküm , kısa hüküm )  —  ör. ( "UYGUNDUR." , "UYGUN" )."""
    kaldi = any((b.get("sonuc") or {}).get("uygun") is False
                for b in (bolumler or []) if not b.get("eksik_hesap"))
    if kaldi:
        return "UYGUN DEĞİLDİR.", "UYGUN DEĞİL"
    if eksik:
        return "HESAP EKSİK", "HESAP EKSİK"
    if tumu_uygun:
        return "UYGUNDUR.", "UYGUN"
    #  Bölüm kalmadı, eksik de yok:  geriye ENGELLEYİCİ uyarı kalır.
    return "UYGUN DEĞİLDİR.", "UYGUN DEĞİL"


def hesapla(veriler=None):
    """Mukavemet hesabının tamamı.

    veriler   girdi sözlüğü ( engine.mukavemet_girdi.ALANLAR anahtarları ).
              Eksik alanlar örnek projenin varsayılanlarıyla tamamlanır.
    """
    g = MG.varsayilanlar()
    g.update(veriler or {})
    g = MG.tamamla(g)
    hata = MG.dogrula(g)
    if hata:
        return {"aktif": False, "hata": hata, "girdi": g}

    #  OFİS STANDARDI — uygulama projesinin KENDİ sabitleri ( avandan ayrı,
    #  bkz. engine/uygulama/sabitler.py ).  Bölümler bunu o["ofis"]'ten okur;
    #  ekrandaki Sabitler sekmesinde değiştirilen her değer buradan geçer.
    o = {"ofis": US.sabitler(g.get("_ofis"))}
    #  NUMARA BURADA VERİLİR, BÖLÜMÜN İÇİNDE DEĞİL.  Bölüm kendi adını ve
    #  değişmez kimliğini taşır;  kaçıncı sırada basılacağı onu kullanan
    #  projeye aittir — uygulama projesi bu on bölümün arkasına elektrik ve
    #  topraklama hesaplarını ekleyip hepsini yeniden numaralar.
    bolumler = [numarala(uret(g, o), i)
                for i, uret in enumerate(BOLUM_URETICILERI, 1)]
    uygunlar = [b["sonuc"]["uygun"] for b in bolumler
                if b.get("sonuc") and b["sonuc"].get("uygun") is not None]
    _eksikler = [b["eksik_hesap"] for b in bolumler if b.get("eksik_hesap")]
    _hukum = genel_hukum(bolumler, all(uygunlar), _eksikler)
    return {
        "aktif": True,
        "baslik": "ASANSÖR MUKAVEMET HESAPLARI",
        "girdi": g,
        "bolumler": bolumler,
        "sabitler": dict(SABIT),
        "ozet": {
            "N_hesap": o.get("N_hesap"), "motor_uygun": o.get("motor_uygun"),
            "Tst_hesap": o.get("Tst_hesap"), "Tst": o.get("Tst"),
            "tst_uygun": o.get("tst_uygun"),
            "kabin_alani": o.get("kabin_alani"), "kabin_kisi": o.get("kabin_kisi"),
            "Sf": o.get("Sf"), "S_gercek": o.get("S_gercek"),
            "ray_boyu": o.get("ray_boyu"), "Mg_kabin": o.get("Mg_kabin"),
            "Mg_agirlik": o.get("Mg_agirlik"), "Fk_kabin": o.get("Fk_kabin"),
            "FKR": o.get("FKR"), "FAR": o.get("FAR"),
            "Fkt": o.get("Fkt"), "Fat": o.get("Fat"),
            "tumu_uygun": all(uygunlar),
            "eksik_hesap": _eksikler,
            "genel_sonuc": _hukum[0], "genel_sonuc_kisa": _hukum[1],
        },
        #  HESABI DURDURMAYAN UYARILAR  ( bkz. MG.uyarilar ).  λ > 250 gibi
        #  durumlar hesabı imkânsız kılmaz, yalnız bir kontrolü düşürür;
        #  sebebi paftada ve ekranda görünsün diye buradan taşınır.
        "uyarilar": MG.uyarilar(g),
        #  Adıyla okunabilen ara değerler  { "bölüm.ad" : değer }  ( bkz. _kay )
        "ara": o.get("ara", {}),
    }
