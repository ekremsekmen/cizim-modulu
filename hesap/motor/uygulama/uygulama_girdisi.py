# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ — GİRDİ SÖZLEŞMESİ

Uygulama projesi iki hesap ailesini birlikte kullanır:

    MUKAVEMET      motor/mukavemet.py        ( 10 bölüm )
    ELEKTRİK       motor/avan.py'nin 3-6.    ( kabin ve kuyu aydınlatması,
                   bölümleri + topraklama +     kurulu güç cetveli, gerilim
                   makine dairesi aydınlatması  düşümü ve kesit kontrolü )

BU MODÜLÜN VARLIK SEBEBİ:  iki aile ORTAK GİRDİLERİ paylaşır — kabin
ölçüleri, beyan yükü, hız, kuyu boyu, motor gücü, askı oranı, ray profili.
Aynı değeri iki kere sormak yalnız zahmet değil, HATA KAYNAĞIDIR:  biri
düzeltilip öteki unutulduğunda iki hesap sessizce ayrışır ve pafta kendi
içinde çelişir.

Bu yüzden:
  · Ortak girdiler YALNIZ mukavemet sözleşmesinde tanımlıdır
    ( motor/uygulama/mukavemet_girdi.ALANLAR ) — tek doğruluk kaynağı odur.
  · Elektrik hesaplarının mukavemette KARŞILIĞI OLMAYAN girdileri burada,
    ayrı bir grupta tanımlanır.
  · Ortak olanlar `avan_girdisi()` ile mukavemet girdisinden TÜRETİLİR, kullanıcıya
    ikinci kez sorulmaz.

Not:  ofis standardı ( U · κ · εmax · armatürler · priz · cosφ · β · çubuk )
zaten "Sabitler / Ofis Standardı" sekmesinden gelir;  o da ikinci kez
sorulmaz.
"""

from motor.avan import avan_hesabi
from motor.ortak.adimlar import aralik_disi, evet_mi
from motor.uygulama import mukavemet
from motor.uygulama import uygulama_sabitleri
from motor.uygulama import mukavemet_girdi
from motor.uygulama import mukavemet_tablolari
from tasarim import alanlar, gorunum
from motor.avan import tablolar
from motor.ortak import ofis
from cizim import geometri
from cizim import kopru
from cizim import olculer

#  Tanınmayan makine tipinde geri düşülecek verim.  Gerçek verim makine
#  tipinden ve projenin kendi ofis sabitlerinden gelir ( US.verim ).
MK_VERIM = ofis.VARSAYILAN_VERIM

#  ( anahtar , etiket , birim , tür , seçenekler , varsayılan )
#  Mukavemette KARŞILIĞI OLMAYAN girdiler.  Hepsi elektrik hesaplarına girer.
#  PROJE GENELİ GİRDİLER.  Temel topraklama ve makine dairesi BİNAYA aittir,
#  asansöre değil:  bir binada dört asansör varsa topraklama tektir ve makine
#  dairesi ortaktır.  Çoklu projede bunlar asansör formunun DIŞINDA bir kez
#  girilir ve her asansörün girdi setine karıştırılır — elektrik köprüsü
#  onları orada bekler.  Liste burada durur ki API ve arayüz aynı yerden
#  okusun;  iki yerde tutulsaydı ayrışırlardı.
PROJE_GENELI_ALANLAR = gorunum.anahtarlar(alanlar.ELK, proje_geneli=True)

#  Tanımlar tasarım şemasında ( tasarim/alanlar.py, sözleşmesi ELK ) —
#  mukavemet_girdi'de durur ( mukavemet onları da kullanır ).
EK_ALANLAR = mukavemet_girdi.EK_ALANLAR
EK_ALAN = mukavemet_girdi.EK_ALAN

#  KÖPRÜDEN AVAN MOTORUNA GEÇEN ve orada SINIRLANAN alanlar  →  avandaki adı.
#  Avan motoru bunları kendi sınırlarıyla denetler ve sınır dışındaysa
#  asansörü durdurur;  burada denetlenmezse kullanıcı yalnız "elektrik
#  hesapları yapılamadı" görür, hangi alanı düzelteceğini göremezdi.
#  Sınırlar avan motorundan OKUNUR ( tek kaynak:  ASANSOR_SINIRLARI ).
AVAN_SINIRLI = {"kolon_kesit": "S1", "makine_kesit": "S2", "motor_gucu": "Nsc", "kabin_agirligi": "Gk_elle"}


#  Elektrik / topraklama alanlarının ⓘ metinleri  ( bkz. MG.ACIKLAMA ).
EK_ACIKLAMA = {a.anahtar: a.bilgi for a in alanlar.ALANLAR if a.sozlesme == alanlar.ELK}

#  "Gelişmiş" bölümündeki elektrik alanları  ( bkz. MG.GELISMIS_ALANLAR ).
#  Kesitler ofisin alışılmış kesitleridir;  yetmezlerse gerilim düşümü ve
#  koruma iletkeni bölümleri bunu hüküm olarak söyler.  Uzunluklar binaya
#  bağlıdır, görünür kalır.
EK_GELISMIS = frozenset(gorunum.anahtarlar(alanlar.ELK, gelismis=True, formda=True))

EK_GRUP = ("Elektrik ve topraklama", gorunum.anahtarlar(alanlar.ELK))

#  ELEKTRİK VE PROJE GENELİ BÖLÜMLERİN GİRDİ GRUPLARI.
#  mukavemet_girdi.BOLUM_GRUBU'nun devamı — oradaki on bölüm mukavemetin,
#  buradakiler avan motorundan ödünç alınanlardır.  Anahtar yine bölümün
#  KİMLİĞİDİR;  numara kullanılırken bu sözlük "mukavemet 10 bölümdür,
#  elektrik 11'den başlar" varsayımını taşımak zorundaydı ve mukavemete bir
#  bölüm eklendiğinde sessizce yanlış bölümü gösterecekti.
#
#  PROJE GENELİ BÖLÜMLER DE ARTIK EŞLENİYOR.  Numara ile eşlenemiyorlardı:
#  makine dairesi varsa topraklama 16'dan, yoksa 15'ten başlıyordu.
#  Grup adı iki yerde geçtiği için tek sabitte durur.
YERLESIM_GRUBU_ADI = "Asansör ve düzen"

EK_BOLUM_GRUBU = {
    "kabin_aydinlatma": ("Kabin ve kapı",),  # ← kabin ölçüleri
    "kuyu_aydinlatma": ("Kuyu ve katlar",),  # ← KG · kuyu boyu
    #  Cetvelde kuyu aydınlatması var, ama armatür ADEDİ kuyu YÜKSEKLİĞİNDEN
    #  gelir;  gücü belirleyenler motor ( Nsç ) ve kabin ölçüsü.
    "kurulu_guc": ("Makine", "Kabin ve kapı"),
    "gerilim_dusumu": (EK_GRUP[0], "Makine"),  # ← S1 · L1 · S2 · L2
    #  Ölçüler makine dairesi grubunda, makine yeri ( MRL ) düzen grubunda.
    "makine_dairesi_aydinlatma": ("Makine dairesi", YERLESIM_GRUBU_ADI),
    "topraklama_yatay": (EK_GRUP[0],),  # ← temel a · b · şerit L
    "topraklama_dikey": (EK_GRUP[0],),
    "topraklama_toplam": (EK_GRUP[0],),
    #  KESİTLER TESİSİN EN BÜYÜK KORUMA İLETKENİNDEN TÜRER;  o da yalnız S1 · S2'den.
    "topraklama_iletkenleri": (EK_GRUP[0],),
}


#  MAKİNE YERİ FORMUN İLK GRUBUNDA ( "Asansör ve düzen" ):  makine dairesi
#  var mı sorusu 11 bölümden üçünü belirler ( bölüm 2 kaide · aydınlatma ve
#  elektrik · rayların Maux'u ) ve çizimin yarısını.  Makine dairesinin ölçüleri
#  kendi grubunda ( "Makine dairesi" ) — tasarım şeması.


def arayuz_alanlari():
    """Formun kendini kurduğu sözleşme:  bütün gruplar ( mukavemet · çizim ·
    elektrik ) tasarım şemasından, tasarım sırasıyla;  hesap bölümü → girdi
    grubu eşlemesi motorlardan."""
    veri = mukavemet_girdi.arayuz_alanlari()
    veri.update(gorunum.form())
    veri["bolum_grubu"].update({no: list(gr) for no, gr in EK_BOLUM_GRUBU.items()})
    return veri


def varsayilanlar():
    return mukavemet_girdi.uygulama_varsayilanlari()


def tamamla(g):
    g = mukavemet_girdi.tamamla(g)
    for a, _et, _b, _t, _s, v in EK_ALANLAR:
        g.setdefault(a, v)
    return g


#  ÇİZİMDEN ÖLÇÜLEN HESAP GİRDİLERİ ( tasarım şeması:  kaynağı ÇİZİM, formda
#  kutusu yok;  cizim/olculer.py ).
YERLESIM_OLCULERI = (
    "kabin_merkezi_x",
    "esik_x",
    "kabin_ray_boyu",
    "agirlik_ray_boyu",
    "aski_halat_boyu",
    "reg_halat_boyu",
    "kasnak_tek_yon",
    "kasnak_ters_yon",
    "kasnak_kabin_adedi",
    "kasnak_agirlik_adedi",
    "saptirma_agirlik_capi",
    "makine_yuku_x",
    "agirlik_baglanti_x",
    "yan_yatak_boyu",
    "agirlik_dolgu_yuksekligi",
)


def yerlesim_olculeri(g):
    """PROGRAMIN HESABI geometriyi çizimden alır:  çizim girdisi köprüden
    kurulur, yerleşimin ölçüleri okunur ( cizim/olculer ).  { girdi : değer }
    ve kaynak işareti ( _cizimden ) döner.  Çizim kurulamıyorsa boş:  hesap
    kendi yaklaşığıyla sürer ve raporda KABUL yazar.

    Makine kirişinde yükün yeri yalnız kiriş çizildiği yere oturuyorsa
    alınır:  makine dairesizde raylara ( "Kılavuz raylar" ), makine dairelide
    kaideye.  "Bina yapısına" oturan kiriş henüz çizilmiyor ( karar 3 ).

    Motor doğrudan çağrılınca ( hesap programının kendi referans testleri )
    bu adım yoktur:  motorun davranışı asıl programınkiyle aynı kalır."""

    plan_hatalari = []
    try:
        gc, _hata = kopru.cizim_girdisi(g)
        #  KUYU GEOMETRİSİ KURULAMIYORSA HESAP DURUR ( kullanıcı kararı 4 Eki ):
        #  kabin kuyuya sığmıyor, raylar / ağırlık / kapı dışarı taşıyor, kabin ya
        #  da kapı 2 m'den alçak … ( çizimin plan doğrulaması ).  Eskiden çizim
        #  reddederken hesap "hesaplandı" diyordu:  imkânsız bir kuyunun raporu
        #  çıkabiliyordu.  Çizimin yalnız çizemediği durumlarda ( makaralı kabin
        #  pateni, 3 tampon, yana kaçık askı — köprünün iletileri ) hesap sürer.
        plan_hatalari = geometri.dogrula(gc) if gc is not None else []
        o = olculer.hesap_olculeri(gc) if gc is not None and not plan_hatalari else {}
    except Exception:  # noqa: BLE001 — çizim kendi hatasını söyler
        o = {}
    if evet_mi(g.get("mk_yok")):
        #  Makine dairesizde çizilen kiriş seçilen yük yoluna uymalı:  arkadaki
        #  ağırlıkta makine yalnız duvardan duvara kirişlerdedir ( bina yapısına );
        #  "Kılavuz raylara" seçilmişse çizim durur ( köprü uyuşmazlığı ) ve
        #  kirişin ölçüsü hesaba girmez.  Yandaki ağırlıkta iki yol da çizilir
        #  ( 14 Eki'ye kadar "Bina yapısına" çizilmiyordu — karar 3 ).
        arka = g.get("agirlik_yeri") == "Arka"
        if arka and mukavemet_tablolari.makine_raya_mi(g.get("makine_raya_biniyor")):
            for k in ("makine_yuku_x", "agirlik_baglanti_x", "yan_yatak_boyu"):
                o.pop(k, None)
    d = {k: o[k] for k in YERLESIM_OLCULERI if k in o}
    isaret = {k: "yerleşim" for k in d}
    #  KİRİŞİN AÇIKLIĞI GİRDİ DEĞİLDİR:  çizimden gelmezse boş kalır ( bölüm 2
    #  HESAP EKSİK ) — şemanın 1.400'ü hesap motorunun kendi varsayılanıdır,
    #  programda sessizce kullanılmaz.
    d.setdefault("yan_yatak_boyu", None)
    if isaret:
        d["_cizimden"] = {**(g.get("_cizimden") or {}), **isaret}
    if plan_hatalari:
        d["_geometri_hatasi"] = plan_hatalari
    return d


def uygulanmayan_alanlar(mk_yok):
    """Makine yerleşimine göre HESABA GİRMEYEN alanlar  —  ekranda gizlenirler.

    Gizli bir alanda kalmış değer ( makine dairesizde "4.000" yazılı makine
    dairesi ölçüsü, makine dairelide geçersiz bir makine yükü yolu ) projeyi
    durduruyordu:  kullanıcı hatayı göremiyor, düzeltemiyordu.  API bu
    alanları okumaz, motor da doğrulamaz.  Liste tasarım şemasından
    ( alanın yerleşimi ) — mukavemet, çizim ve elektrik alanları birlikte.
    """
    return gorunum.uygulanmayan(evet_mi(mk_yok))


def dogrula(g):
    """Mukavemet doğrulaması + elektrik girdilerinin denetimi."""
    hata = list(mukavemet_girdi.dogrula(g))
    atla = uygulanmayan_alanlar(g.get("mk_yok"))
    for a, et, birim, tur, _s, _v in EK_ALANLAR:
        d = g.get(a)
        ad = f"{et} ({birim})" if birim not in ("—", "") else et
        if tur == "onay" or a in atla:
            continue
        if d is None or d == "":
            continue  # boş bırakılabilir — hesap uyarır
        if not isinstance(d, (int, float)) or isinstance(d, bool) or d < 0:
            hata.append(f"{ad}: negatif olmayan bir sayı olmalı ( {d!r} girildi ).")
    hata += _avan_siniri_hatalari(g, atla)
    #  Makine dairesi işaretli DEĞİLSE ölçüsü istenir;  yoksa aydınlatma
    #  hesabı sessizce yapılamaz hâle gelirdi.
    if not evet_mi(g.get("mk_yok")):
        for a in ("mk_uzunluk", "mk_genislik"):
            if not (isinstance(g.get(a), (int, float)) and g[a] > 0):
                hata.append(
                    f"{EK_ALAN[a][1]}: makine dairesi varsa ölçüsü girilmelidir "
                    "( ya da 'Makine dairesiz ( MRL )' kutusunu işaretleyin )."
                )
    return hata


def _avan_siniri_hatalari(g, atla):
    """Avan motorunun kabul etmeyeceği köprü değerleri  —  hata metinleri.

    Negatif değer ve bölen alandaki sıfır zaten kendi denetiminde söylenir;
    burada ikinci kez yazılmaz.
    """
    sinir = {k: (aralik, birim) for k, _ad, aralik, birim in avan_hesabi.ASANSOR_SINIRLARI}
    hata = []
    for a, avan_adi in AVAN_SINIRLI.items():
        d = g.get(a)
        if (
            a in atla
            or not isinstance(d, (int, float))
            or isinstance(d, bool)
            or d < 0
            or (d == 0 and a in mukavemet_girdi.BOLEN_ALANLAR)
        ):
            continue
        (alt, ust), birim = sinir[avan_adi]
        if not alt <= d <= ust:
            et = (EK_ALAN.get(a) or mukavemet_girdi.ALAN[a])[1]
            hata.append(aralik_disi(et, d, alt, ust, birim) + "  —  elektrik hesapları bu değerle yapılamaz.")
    return hata


def avan_girdisi(g):
    """ORTAK GİRDİ KÖPRÜSÜ  —  mukavemet girdisi  →  avan asansör girdisi.

    Buradaki her satır, kullanıcıya İKİNCİ KEZ SORULMAYAN bir alandır.
    Sağ taraf mukavemet sözleşmesinden gelir;  sol taraf motor/avan.py'nin
    beklediği addır.
    """
    ray = mukavemet_tablolari.ray(g.get("kabin_ray_profili"), "Gr")
    asansor = {
        "aktif": True,
        "tanim": "Uygulama projesi",
        #  ── ortak ── ( mukavemetten )
        "Q_elle": g.get("beyan_yuku"),  # beyan yükü          [kg]
        "V": g.get("beyan_hizi"),  # kabin hızı          [m/s]
        "Gk_elle": g.get("kabin_agirligi"),  # boş kabin kütlesi   [kg]
        "kabin_boyu": g.get("kabin_derinligi"),  # avanda "boy" = derinlik
        "kabin_genisligi": g.get("kabin_genisligi"),
        "Hk": (g.get("kuyu_boyu") or 0) / 1000.0,  # kuyu yüksekliği    [m]
        "Nsc": g.get("motor_gucu"),  # seçilen motor gücü  [kW]
        "i_palanga": g.get("aski_orani"),
        "gr": ray,  # ray metre ağırlığı  [kg/m]
        #  Motor verimi:  MAKİNE TİPİNDEN gelir ( ofis standardı, tek kaynak
        #  motor/ortak/ofis.py ) ve uygulamada TOPLAM SİSTEM VERİMİDİR — askı
        #  kaybı içindedir.  Avan motoru ise kitaba göre MAKİNE verimi bekler ve
        #  palangalı sistemde 0,10 düşer ( MMO/697 §2.4 );  bayrak o düşüşü bu
        #  yolda kapatır, iki proje aynı η ile aynı elektrik hesabını yapar.
        #  ( Eskiden buradan sabit 0,92 geçiyordu:  aynı asansör için avan ve
        #  uygulama paftaları farklı motor gücü veriyordu. )
        "makine_tipi": g.get("makine_tipi"),
        #  Projeye imalatçının verimi girilmişse mukavemetle aynı değer geçer.
        "eta": mukavemet_girdi.sistem_verimi(g)[0],
        tablolar.ETA_TOPLAM_ANAHTARI: True,
        #  ── uygulama projesine özgü ──
        "kuyu_genisligi": g.get("kuyu_genisligi"),
        #  L1 GÖNDERİLMEZ:  avan motoru kuyu yüksekliği + yatay güzergâh payıyla
        #  kurar;  pay uygulamanın Sabitler'indedir ( _avan_sabitleri geçirir ).
        "S1": g.get("kolon_kesit"),
        #  L2 GÖNDERİLMEZ:  ofis sabitidir ( Sabitler · ⑤ ) ve her projede
        #  aynıdır — asansör panosu makineye yakın durur.  Avan motoru asansör
        #  değeri yoksa ofis değerini kullanır ( _ofis_degeri ).  Eskiden asansör
        #  formunda kaynaksız 12 m varsayılanla soruluyordu;  avan ve ofisin üç
        #  şablonu 3 m kullanıyor, aynı asansöre iki proje farklı sayı veriyordu.
        "S2": g.get("makine_kesit"),
    }
    ortak = {
        "temel_a": g.get("temel_a"),
        "temel_b": g.get("temel_b"),
        #  ŞERİT BOYU GİRDİ DEĞİLDİR:  avan motoru temel ölçülerinden kurar
        #  ( temel çevresi + karelaj bağları, göz Sabitler'de ) ve paftaya
        #  hesabıyla basar.  Formda hep boş bırakılan bir kutuydu.
        "serit_L": None,
        "mk_yok": bool(g.get("mk_yok")),
        "mk_uzunluk": g.get("mk_uzunluk"),
        "mk_genislik": g.get("mk_genislik"),
    }
    #  OFİS STANDARDI  ( Sabitler sekmesi ):  armatür ışık akısı, priz, cosφ,
    #  εmax, κ, U, β, çubuk sayısı …  Elektrik ve topraklama hesapları bunları
    #  kullanır;  köprüden geçmezse kullanıcının sekmedeki değişikliği hiçbir
    #  şeyi değiştirmezdi.
    return {
        "ortak": ortak,
        "asansorler": [asansor],
        "sabitler": _avan_sabitleri(g.get("_ofis")),
        "trafik": {},
    }


#  Uygulamanın ofis sabiti  →  avan motorunun beklediği anahtar.  Elektrik ve
#  topraklama hesapları avan motorunda koştuğu için ( ELEKTRIK_BOLUMLERI )
#  uygulamanın kendi setinden karşılığı olanlar oraya çevrilir.  Adı aynı
#  olanlar zaten eşleşir;  liste yalnız ADI FARKLI olanlar içindir.
AVAN_KARSILIGI = {}
#  Avan motoruna GEÇMEYECEKLER:  yalnız mukavemeti ilgilendirirler ve avan
#  tarafında aynı adla başka bir anlam taşıyabilirler.
#  Çizimin ürün ölçüleri ( tek katalog ) ve dolgu yoğunlukları da geçmez.
AVAN_DISI = (
    (
        "q_denge",
        "sigma_em",
        "k1_kaymali",
        "k1_makarali",
        "k1_ani",
        "yan_yatak_L_X",
        "halat_pay_m",
        "Gs",
        "verim_dislisiz",
        "verim_disli",
        "dolgu_yogunlugu_barit",
        "dolgu_yogunlugu_pik",
    )
    + mukavemet.SIGINMA_PAYLARI
    + uygulama_sabitleri.CIZIM_ANAHTARLARI
)


def _avan_sabitleri(ofis_degerleri):
    """Uygulamanın ofis setinden, avan motorunun kullanabileceği alt küme."""
    if not isinstance(ofis_degerleri, dict):
        ofis_degerleri = {}
    d = {}
    for k, v in ofis_degerleri.items():
        if k in AVAN_DISI:
            continue
        d[AVAN_KARSILIGI.get(k, k)] = v
    #  L2 uygulamanın KENDİ sabitidir:  boş bırakılsa da avan motorunun
    #  varsayılanına düşmesin diye her zaman açıkça geçirilir.
    _us = uygulama_sabitleri.sabitler(ofis_degerleri)
    d["L2"] = _us["L2"]
    d["L1_pay"] = _us["L1_pay"]
    return d


#  ORTAK ALANLARIN LİSTESİ  —  arayüz bunu "bu değer mukavemetten geliyor"
#  diye gösterir;  belgeleme ve test de buradan okur.
ORTAK_KOPRU = (
    ("Beyan yükü", "beyan_yuku", "Q"),
    ("Beyan hızı", "beyan_hizi", "V"),
    ("Boş kabin ağırlığı", "kabin_agirligi", "Gk"),
    ("Kabin derinliği", "kabin_derinligi", "a  ( kabin boyu )"),
    ("Kabin genişliği", "kabin_genisligi", "b"),
    ("Kuyu boyu", "kuyu_boyu", "Hk"),
    ("Motor gücü", "motor_gucu", "Nsç"),
    ("Askı oranı", "aski_orani", "i"),
    ("Kabin rayı profili", "kabin_ray_profili", "gr  ( ray metre ağırlığı )"),
)
