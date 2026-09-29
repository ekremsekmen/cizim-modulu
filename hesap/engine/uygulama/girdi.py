# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ — GİRDİ SÖZLEŞMESİ

Uygulama projesi iki hesap ailesini birlikte kullanır:

    MUKAVEMET      engine/mukavemet.py        ( 10 bölüm )
    ELEKTRİK       engine/avan.py'nin 3-6.    ( kabin ve kuyu aydınlatması,
                   bölümleri + topraklama +     kurulu güç cetveli, gerilim
                   makine dairesi aydınlatması  düşümü ve kesit kontrolü )

BU MODÜLÜN VARLIK SEBEBİ:  iki aile ORTAK GİRDİLERİ paylaşır — kabin
ölçüleri, beyan yükü, hız, kuyu boyu, motor gücü, askı oranı, ray profili.
Aynı değeri iki kere sormak yalnız zahmet değil, HATA KAYNAĞIDIR:  biri
düzeltilip öteki unutulduğunda iki hesap sessizce ayrışır ve pafta kendi
içinde çelişir.

Bu yüzden:
  · Ortak girdiler YALNIZ mukavemet sözleşmesinde tanımlıdır
    ( engine/uygulama/mukavemet_girdi.ALANLAR ) — tek doğruluk kaynağı odur.
  · Elektrik hesaplarının mukavemette KARŞILIĞI OLMAYAN girdileri burada,
    ayrı bir grupta tanımlanır.
  · Ortak olanlar `kopru()` ile mukavemet girdisinden TÜRETİLİR, kullanıcıya
    ikinci kez sorulmaz.

Not:  ofis standardı ( U · κ · εmax · armatürler · priz · cosφ · β · çubuk )
zaten "Sabitler / Ofis Standardı" sekmesinden gelir;  o da ikinci kez
sorulmaz.
"""
from engine.avan import hesap as E_AVAN
from engine.ortak.steps import aralik_disi, evet_mi
from engine.uygulama import mukavemet as MK
from engine.uygulama import sabitler as US
from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import mukavemet_tablolari as MT

#  Tanınmayan makine tipinde geri düşülecek verim.  Gerçek verim makine
#  tipinden ve projenin kendi ofis sabitlerinden gelir ( US.verim ).
MK_VERIM = US.OFIS.VARSAYILAN_VERIM

#  ( anahtar , etiket , birim , tür , seçenekler , varsayılan )
#  Mukavemette KARŞILIĞI OLMAYAN girdiler.  Hepsi elektrik hesaplarına girer.
#  PROJE GENELİ GİRDİLER.  Temel topraklama ve makine dairesi BİNAYA aittir,
#  asansöre değil:  bir binada dört asansör varsa topraklama tektir ve makine
#  dairesi ortaktır.  Çoklu projede bunlar asansör formunun DIŞINDA bir kez
#  girilir ve her asansörün girdi setine karıştırılır — elektrik köprüsü
#  onları orada bekler.  Liste burada durur ki API ve arayüz aynı yerden
#  okusun;  iki yerde tutulsaydı ayrışırlardı.
PROJE_GENELI_ALANLAR = ("temel_a", "temel_b",
                        "mk_yok", "mk_uzunluk", "mk_genislik")

EK_ALANLAR = (
    ("kuyu_genisligi",  "Kuyu genişliği  ( KG )",            "mm",   "sayi", None, 2400),
    #  S1 = 6 mm²:  avan motoru ve ofisin avan Excel'i de 6 kullanır;  eskiden
    #  burada kaynaksız 16 vardı ve aynı asansöre iki proje farklı kesit
    #  veriyordu.  4,9 – 15 kW'lık motorlarda ε ≤ %1,6 ve akım yeter;  daha
    #  büyük motorda yetmezse gerilim düşümü bölümü "kesiti büyütün" der.
    ("kolon_kesit",     "S1 — Kolon hattı kesiti",           "mm²",  "sayi", None, 6),
    ("makine_kesit",    "S2 — Makine besleme kesiti",        "mm²",  "sayi", None, 6),
    ("temel_a",         "Temel uzunluğu",                    "m",    "sayi", None, None),
    ("temel_b",         "Temel genişliği",                   "m",    "sayi", None, None),
    ("mk_yok",          "Makine dairesiz  ( MRL )",          "—",    "onay", None, True),
    ("mk_uzunluk",      "Makine dairesi uzunluğu",           "mm",   "sayi", None, None),
    ("mk_genislik",     "Makine dairesi genişliği",          "mm",   "sayi", None, None),
)

EK_ALAN = {a[0]: a for a in EK_ALANLAR}

#  KÖPRÜDEN AVAN MOTORUNA GEÇEN ve orada SINIRLANAN alanlar  →  avandaki adı.
#  Avan motoru bunları kendi sınırlarıyla denetler ve sınır dışındaysa
#  asansörü durdurur;  burada denetlenmezse kullanıcı yalnız "elektrik
#  hesapları yapılamadı" görür, hangi alanı düzelteceğini göremezdi.
#  Sınırlar avan motorundan OKUNUR ( tek kaynak:  ASANSOR_SINIRLARI ).
AVAN_SINIRLI = {"kolon_kesit": "S1", "makine_kesit": "S2",
                "motor_gucu": "Nsc", "kabin_agirligi": "Gk_elle"}


#  Elektrik / topraklama alanlarının ⓘ metinleri  ( bkz. MG.ACIKLAMA ).
EK_ACIKLAMA = {
    "kuyu_genisligi": "KG — kuyunun plandaki genişliği. Yalnız kuyu "
              "aydınlatmasının bölge indeksine girer; mukavemet hesabına "
              "girmez.",
    "kolon_kesit": "S1 — panodan asansör tablosuna gelen kolon hattının "
              "iletken kesiti. Gerilim düşümü ve koruma iletkeni bundan çıkar.",
    "makine_kesit": "S2 — tablodan makineye giden besleme hattının kesiti.",
    "temel_a": "Binanın temelinin uzunluğu. Temel topraklamasının eşdeğer "
              "direnci temel ALANINDAN hesaplanır.",
    "temel_b": "Binanın temelinin genişliği.",
    "mk_yok": "Makine dairesi var mı yok mu. Dairesiz ( MRL ) seçilirse "
              "tabliye betonu ve makine kaidesi kolonu yoktur: kiriş burkulma "
              "kontrolü yapılmaz, ray boyuna tabliye eklenmez.",
    "mk_uzunluk": "Makine dairesinin plandaki uzunluğu. Makine dairesi "
              "aydınlatmasına girer.",
    "mk_genislik": "Makine dairesinin plandaki genişliği.",
}

#  "Gelişmiş" bölümündeki elektrik alanları  ( bkz. MG.GELISMIS_ALANLAR ).
#  Kesitler ofisin alışılmış kesitleridir;  yetmezlerse gerilim düşümü ve
#  koruma iletkeni bölümleri bunu hüküm olarak söyler.  Uzunluklar binaya
#  bağlıdır, görünür kalır.
EK_GELISMIS = frozenset(("kolon_kesit", "makine_kesit"))

EK_GRUP = ("Elektrik ve topraklama  ( uygulama projesi )",
           tuple(a[0] for a in EK_ALANLAR))

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
YERLESIM_GRUBU_ADI = "Makine yerleşimi"

EK_BOLUM_GRUBU = {
    "kabin_aydinlatma":          ("Kabin ve kapı",),        # ← kabin ölçüleri
    "kuyu_aydinlatma":           (EK_GRUP[0], "Durak ve kuyu"),   # ← KG · kuyu boyu
    #  ELEKTRİK GRUBU DEĞİL.  Cetvelde kuyu aydınlatması var, ama armatür
    #  ADEDİ kuyu YÜKSEKLİĞİNDEN gelir;  kuyu genişliği yalnız lux kontrolüne
    #  girer ve kurulu gücü değiştirmez.  Gücü belirleyenler motor ( Nsç ) ve
    #  kabin ölçüsü ( kabin armatür adedi ).
    "kurulu_guc":                ("Makine ve motor", "Kabin ve kapı"),
    "gerilim_dusumu":            (EK_GRUP[0], "Makine ve motor"),  # ← S1 · L1 · S2 · L2
    #  MAKİNE DAİRESİ ÖLÇÜLERİ ARTIK "Makine yerleşimi" GRUBUNDA  ( en üstte ):
    #  seçim 11 bölümden üçünü belirlediği için elektrik grubunun dibinden
    #  alındı  ( bkz. YERLESIM_GRUBU ).
    #  Ölçüler elektrik grubunda, MRL kutusu yerleşim grubunda:  ikisi de
    #  bu bölümü besler, sonuçtan tıklanınca ikisi de açılmalı.
    "makine_dairesi_aydinlatma": (EK_GRUP[0], YERLESIM_GRUBU_ADI),
    "topraklama_yatay":          (EK_GRUP[0],),             # ← temel a · b · şerit L
    "topraklama_dikey":          (EK_GRUP[0],),
    "topraklama_toplam":         (EK_GRUP[0],),
    #  KESİTLER TESİSİN EN BÜYÜK KORUMA İLETKENİNDEN TÜRER;  o da yalnız
    #  S1 · S2'den — gerilim düşümünün aksine motor gücü buraya girmez, bu
    #  yüzden "Makine ve motor" grubu bu bölümü etkilemez.
    "topraklama_iletkenleri":    (EK_GRUP[0],),
}



#  MAKİNE YERLEŞİMİ EN BAŞTA SORULUR.  Bu iki soru birlikte 11 bölümden
#  üçünü belirler:
#     · makine dairesi var mı        →  bölüm 2 ( kaide ) uygulanır mı ·
#                                       aydınlatma ve elektrik hesapları
#     · makine yükü raylara biniyor mu →  bölüm 7 · 8 ( kabin ve karşı
#                                       ağırlık rayları ) Maux ·
#                                       bölüm 9 ( kuyu tabanı ) FKR · FAR
#  Bu kadar şey belirleyen bir seçim formun dibinde duramaz;  eskiden
#  "Elektrik ve topraklama" grubunun içinde, en altta duruyordu — çünkü o
#  zamanlar YALNIZ aydınlatma hesabını etkiliyordu.
#  ÖLÇÜLER BURADA DEĞİL.  mk_uzunluk / mk_genislik YALNIZ makine dairesi
#  aydınlatma hesabına girer ( engine/avan/hesap.hesapla_makine_dairesi );
#  mukavemetin 11 bölümünün hiçbirini etkilemezler.  Formun en üstünde,
#  üç bölüm belirleyen mk_yok ile yan yana durmaları önem sırasını
#  bozuyordu — ölçüler kendi hesabının yanında, "Elektrik ve topraklama"
#  grubunda durur.
YERLESIM_GRUBU = (YERLESIM_GRUBU_ADI,
                  ("mk_yok", "makine_raya_biniyor"))


def arayuz_alanlari():
    """Formun kendini üretmesi için tüm gruplar  ( mukavemet + elektrik )."""
    veri = MG.arayuz_alanlari()
    _ek = {a: {"anahtar": a, "hucre": "", "etiket": et, "birim": b,
               "tur": t, "secenekler": list(s) if s is not None else None,
               "varsayilan": v, "gelismis": a in EK_GELISMIS,
               "bilgi": EK_ACIKLAMA.get(a, "")}
           for a, et, b, t, s, v in EK_ALANLAR}
    veri["gruplar"].append({
        "ad": EK_GRUP[0],
        "alanlar": [_ek[a] for a, *_x in EK_ALANLAR
                    if a not in YERLESIM_GRUBU[1]],
    })
    #  Yerleşim grubu İKİ KAYNAKTAN toplanır:  makine dairesi alanları proje
    #  geneli ( burada ), makine yükünün yolu asansör başına ( mukavemet ).
    _muk = {f["anahtar"]: f for gr in veri["gruplar"] for f in gr["alanlar"]}
    _yer = [(_ek.get(a) or _muk.get(a)) for a in YERLESIM_GRUBU[1]]
    for gr in veri["gruplar"]:
        gr["alanlar"] = [f for f in gr["alanlar"]
                         if f["anahtar"] not in YERLESIM_GRUBU[1]]
    veri["gruplar"].insert(0, {"ad": YERLESIM_GRUBU[0],
                               "alanlar": [f for f in _yer if f]})
    veri["bolum_grubu"].update({no: list(gr)
                                for no, gr in EK_BOLUM_GRUBU.items()})
    #  Arayüz gizleyeceği alanları buradan okur — motorun atladığıyla aynı liste.
    veri["yerlesime_gore_gizli"] = {"mrl": sorted(uygulanmayan_alanlar(True)),
                                    "daireli": sorted(uygulanmayan_alanlar(False))}
    return veri


def varsayilanlar():
    g = MG.varsayilanlar()
    for a, _et, _b, _t, _s, v in EK_ALANLAR:
        g[a] = v
    return g


def tamamla(g):
    g = MG.tamamla(g)
    for a, _et, _b, _t, _s, v in EK_ALANLAR:
        g.setdefault(a, v)
    return g


def uygulanmayan_alanlar(mk_yok):
    """Makine yerleşimine göre HESABA GİRMEYEN alanlar  —  ekranda gizlenirler.

    Gizli bir alanda kalmış değer ( makine dairesizde "4.000" yazılı makine
    dairesi ölçüsü, makine dairelide geçersiz bir makine yükü yolu ) projeyi
    durduruyordu:  kullanıcı hatayı göremiyor, düzeltemiyordu.  API bu
    alanları okumaz, motor da doğrulamaz.
    """
    mrl = evet_mi(mk_yok)
    #  Formun "Çizim" grubundaki yerleşime bağlı alanlar da ( makine dairesinin
    #  ölçüleri · acil pano ) — ekran ve API bu tek listeyi kullanır.
    from cizim import kopru as _CK
    alanlar = MG.uygulanmayan({"mk_yok": mrl}) | _CK.uygulanmayan(mrl)
    return alanlar | {"mk_uzunluk", "mk_genislik"} if mrl else alanlar


def dogrula(g):
    """Mukavemet doğrulaması + elektrik girdilerinin denetimi."""
    hata = list(MG.dogrula(g))
    atla = uygulanmayan_alanlar(g.get("mk_yok"))
    for a, et, birim, tur, _s, _v in EK_ALANLAR:
        d = g.get(a)
        ad = f"{et} ({birim})" if birim not in ("—", "") else et
        if tur == "onay" or a in atla:
            continue
        if d is None or d == "":
            continue                       # boş bırakılabilir — hesap uyarır
        if not isinstance(d, (int, float)) or isinstance(d, bool) or d < 0:
            hata.append(f"{ad}: negatif olmayan bir sayı olmalı ( {d!r} girildi ).")
    hata += _avan_siniri_hatalari(g, atla)
    #  Makine dairesi işaretli DEĞİLSE ölçüsü istenir;  yoksa aydınlatma
    #  hesabı sessizce yapılamaz hâle gelirdi.
    if not evet_mi(g.get("mk_yok")):
        for a in ("mk_uzunluk", "mk_genislik"):
            if not (isinstance(g.get(a), (int, float)) and g[a] > 0):
                hata.append(f"{EK_ALAN[a][1]}: makine dairesi varsa ölçüsü girilmelidir "
                            "( ya da 'Makine dairesiz ( MRL )' kutusunu işaretleyin ).")
    return hata


def _avan_siniri_hatalari(g, atla):
    """Avan motorunun kabul etmeyeceği köprü değerleri  —  hata metinleri.

    Negatif değer ve bölen alandaki sıfır zaten kendi denetiminde söylenir;
    burada ikinci kez yazılmaz.
    """
    sinir = {k: (aralik, birim) for k, _ad, aralik, birim in E_AVAN.ASANSOR_SINIRLARI}
    hata = []
    for a, avan_adi in AVAN_SINIRLI.items():
        d = g.get(a)
        if (a in atla or not isinstance(d, (int, float)) or isinstance(d, bool)
                or d < 0 or (d == 0 and a in MG.BOLEN_ALANLAR)):
            continue
        (alt, ust), birim = sinir[avan_adi]
        if not alt <= d <= ust:
            et = (EK_ALAN.get(a) or MG.ALAN[a])[1]
            hata.append(aralik_disi(et, d, alt, ust, birim)
                        + "  —  elektrik hesapları bu değerle yapılamaz.")
    return hata


def kopru(g):
    """ORTAK GİRDİ KÖPRÜSÜ  —  mukavemet girdisi  →  avan asansör girdisi.

    Buradaki her satır, kullanıcıya İKİNCİ KEZ SORULMAYAN bir alandır.
    Sağ taraf mukavemet sözleşmesinden gelir;  sol taraf engine/avan.py'nin
    beklediği addır.
    """
    ray = MT.ray(g.get("kabin_ray_profili"), "Gr")
    asansor = {
        "aktif": True,
        "tanim": "Uygulama projesi",
        #  ── ortak ── ( mukavemetten )
        "Q_elle": g.get("beyan_yuku"),            # beyan yükü          [kg]
        "V": g.get("beyan_hizi"),                 # kabin hızı          [m/s]
        "Gk_elle": g.get("kabin_agirligi"),       # boş kabin kütlesi   [kg]
        "kabin_boyu": g.get("kabin_derinligi"),   # avanda "boy" = derinlik
        "kabin_genisligi": g.get("kabin_genisligi"),
        "Hk": (g.get("kuyu_boyu") or 0) / 1000.0,  # kuyu yüksekliği    [m]
        "Nsc": g.get("motor_gucu"),               # seçilen motor gücü  [kW]
        "i_palanga": g.get("aski_orani"),
        "gr": ray,                                # ray metre ağırlığı  [kg/m]
        #  Motor verimi:  MAKİNE TİPİNDEN gelir ( ofis standardı, tek kaynak
        #  engine/ortak/ofis.py ) ve uygulamada TOPLAM SİSTEM VERİMİDİR — askı
        #  kaybı içindedir.  Avan motoru ise kitaba göre MAKİNE verimi bekler ve
        #  palangalı sistemde 0,10 düşer ( MMO/697 §2.4 );  bayrak o düşüşü bu
        #  yolda kapatır, iki proje aynı η ile aynı elektrik hesabını yapar.
        #  ( Eskiden buradan sabit 0,92 geçiyordu:  aynı asansör için avan ve
        #  uygulama paftaları farklı motor gücü veriyordu. )
        "makine_tipi": g.get("makine_tipi"),
        #  Projeye imalatçının verimi girilmişse mukavemetle aynı değer geçer.
        "eta": MG.sistem_verimi(g)[0],
        E_AVAN.T.ETA_TOPLAM_ANAHTARI: True,
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
        "temel_a": g.get("temel_a"), "temel_b": g.get("temel_b"),
        #  ŞERİT BOYU GİRDİ DEĞİLDİR:  avan motoru temel ölçülerinden kurar
        #  ( temel çevresi + karelaj bağları, göz Sabitler'de ) ve paftaya
        #  hesabıyla basar.  Formda hep boş bırakılan bir kutuydu.
        "serit_L": None,
        "mk_yok": bool(g.get("mk_yok")),
        "mk_uzunluk": g.get("mk_uzunluk"), "mk_genislik": g.get("mk_genislik"),
    }
    #  OFİS STANDARDI  ( Sabitler sekmesi ):  armatür ışık akısı, priz, cosφ,
    #  εmax, κ, U, β, çubuk sayısı …  Elektrik ve topraklama hesapları bunları
    #  kullanır;  köprüden geçmezse kullanıcının sekmedeki değişikliği hiçbir
    #  şeyi değiştirmezdi.
    return {"ortak": ortak, "asansorler": [asansor],
            "sabitler": _avan_sabitleri(g.get("_ofis")), "trafik": {}}


#  Uygulamanın ofis sabiti  →  avan motorunun beklediği anahtar.  Elektrik ve
#  topraklama hesapları avan motorunda koştuğu için ( ELEKTRIK_BOLUMLERI )
#  uygulamanın kendi setinden karşılığı olanlar oraya çevrilir.  Adı aynı
#  olanlar zaten eşleşir;  liste yalnız ADI FARKLI olanlar içindir.
AVAN_KARSILIGI = {}
#  Avan motoruna GEÇMEYECEKLER:  yalnız mukavemeti ilgilendirirler ve avan
#  tarafında aynı adla başka bir anlam taşıyabilirler.
AVAN_DISI = ("q_denge", "sigma_em", "k1_kaymali", "k1_makarali", "k1_ani",
             "yan_yatak_L_X", "halat_pay_m", "Gs", "verim_dislisiz",
             "verim_disli") + MK.SIGINMA_PAYLARI


def _avan_sabitleri(ofis):
    """Uygulamanın ofis setinden, avan motorunun kullanabileceği alt küme."""
    if not isinstance(ofis, dict):
        ofis = {}
    d = {}
    for k, v in ofis.items():
        if k in AVAN_DISI:
            continue
        d[AVAN_KARSILIGI.get(k, k)] = v
    #  L2 uygulamanın KENDİ sabitidir:  boş bırakılsa da avan motorunun
    #  varsayılanına düşmesin diye her zaman açıkça geçirilir.
    _us = US.sabitler(ofis)
    d["L2"] = _us["L2"]
    d["L1_pay"] = _us["L1_pay"]
    return d


#  ORTAK ALANLARIN LİSTESİ  —  arayüz bunu "bu değer mukavemetten geliyor"
#  diye gösterir;  belgeleme ve test de buradan okur.
ORTAK_KOPRU = (
    ("Beyan yükü",           "beyan_yuku",        "Q"),
    ("Beyan hızı",           "beyan_hizi",        "V"),
    ("Boş kabin ağırlığı",   "kabin_agirligi",    "Gk"),
    ("Kabin derinliği",      "kabin_derinligi",   "a  ( kabin boyu )"),
    ("Kabin genişliği",      "kabin_genisligi",   "b"),
    ("Kuyu boyu",            "kuyu_boyu",         "Hk"),
    ("Motor gücü",           "motor_gucu",        "Nsç"),
    ("Askı oranı",           "aski_orani",        "i"),
    ("Kabin rayı profili",   "kabin_ray_profili", "gr  ( ray metre ağırlığı )"),
)
