# -*- coding: utf-8 -*-
"""
ÇİZİM GİRDİSİ SÖZLEŞMESİ  ( bütün ölçüler mm )

Sözlük, çizimin ihtiyaç duyduğu GEOMETRİDİR;  hesabın girdi setiyle aynı
değildir.  Bir kısmı hesaptan gelir ( kabin ölçüleri, ray–kapı arası … ),
bir kısmı yalnız çizime aittir ( duvar kalınlığı, kapı yeri … ).

EKSEN DÜZENİ  ( plan )
    x  →  kuyu genişliği boyunca, SOLDAN SAĞA  ( kapıya bakan için )
    y  →  derinlik;  0 = kapı duvarının İÇ yüzü, artı yön kuyunun arkası
    Kuyu iç boşluğunun sol-ön köşesi orijindir.
"""

import math

from cizim import parcalar, sabitler
from cizim import arka_aski
from cizim import sorun


def _sonlu_sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


#  Hiçbir değer "varsayılan" değildir:  çizim uydurma ölçüyle çizilmez.
#  Eksik anahtar dogrula() tarafından reddedilir.
#  ASKI DÜZENİ:  kasnakların ve askı noktalarının yeri buradan gelir.
#  Koda gömülmez — projeden projeye değişir ve kullanıcı seçer.
ASKI_DUZENLERI = ("Kabin altı", "Kabin üstü", "Doğrudan")

ZORUNLU = {
    "kuyu": ("genislik", "derinlik", "duvar_on", "duvar_arka", "duvar_sol", "duvar_sag"),
    "kabin": ("genislik", "derinlik", "kaciklik_y", "on_pay"),
    "kapi": ("genislik", "sol_pay", "montaj"),
    "kabin_ray": ("arasi", "kapi_arasi", "b", "h"),
    "agirlik": ("yeri", "genislik", "derinlik", "ray_arasi", "ray_duvar", "eksen_kaciklik", "b", "h"),
    #  2:1 askıda kasnak ölçüleri, 1:1'de askı noktası aralığı kullanılır.
    "aski": ("duzen",),
}

#  Zorunlu alanların ekrandaki adı ( iletiler için ).  Çoğu formun bir kutusudur
#  ve kopru.py onları kutunun adıyla zaten denetler;  buraya ancak TÜRETİLEN
#  değerler düşer ( kapının sol duvara uzaklığı gibi ) — iç ad ( "kapi.sol_pay" )
#  mühendise neyin yanlış olduğunu söylemiyordu ( 19 Eki denetimi ).
ADLAR = {
    "kuyu.genislik": "Kuyu genişliği",
    "kuyu.derinlik": "Kuyu derinliği",
    "kuyu.duvar_on": "Kuyu ön duvarı kalınlığı",
    "kuyu.duvar_arka": "Kuyu arka duvarı kalınlığı",
    "kuyu.duvar_sol": "Kuyu sol duvarı kalınlığı",
    "kuyu.duvar_sag": "Kuyu sağ duvarı kalınlığı",
    "kabin.genislik": "Kabin genişliği",
    "kabin.derinlik": "Kabin derinliği",
    "kabin.on_pay": "Kabinin kuyu ön duvarına uzaklığı",
    "kapi.genislik": "Kapı genişliği",
    "kapi.sol_pay": "Kapı kuyuya sığmıyor:  kapı boşluğunun sol duvara uzaklığı",
    "kabin_ray.arasi": "Kabin ray arası",
    "kabin_ray.kapi_arasi": "Kabin ray ekseninin kapıya uzaklığı",
    "kabin_ray.b": "Kabin rayının taban genişliği",
    "kabin_ray.h": "Kabin rayının yüksekliği",
    "agirlik.genislik": "Karşı ağırlık genişliği",
    "agirlik.derinlik": "Karşı ağırlık derinliği",
    "agirlik.ray_arasi": "Karşı ağırlık ray arası",
    "agirlik.ray_duvar": "Ağırlık rayının duvara uzaklığı",
    "agirlik.b": "Ağırlık rayının taban genişliği",
    "agirlik.h": "Ağırlık rayının yüksekliği",
}
#  Türetilen değerlerin kaynağı:  mühendis hangi kutuyu değiştireceğini bilsin
TURETILEN = {
    "kabin.on_pay": "kapı tipinden ve eşik arasından",
    "kapi.sol_pay": "kuyu genişliğinden, kabinin yerinden ve kapı genişliğinden",
    "kabin_ray.kapi_arasi": "kabin derinliğinden",
}

AGIRLIK_YERLERI = ("Sağ", "Sol", "Arka")
#  KAT KAPISININ MONTAJI:  kapı ünitesi ( kasa + eşik ) ya kuyu ön duvarının
#  boşluğuna oturur ( kasa duvarda, eşik kuyuya taşar ) ya da duvarın İÇ
#  YÜZÜNE monte edilir ( ünitenin tamamı kuyunun içinde — referans proje ).  İkisi de
#  aynı üründür;  yalnız kuyu içindeki yeri değişir.
KAPI_MONTAJLARI = ("Duvar boşluğuna", "Kuyu içine")

#  TS EN 81-20 m.5.2.5.3.1:  kuyunun iç yüzü ile kabin eşiği / kapı kasası
#  arası 0,15 m'yi aşamaz  ( kısa yükseklikte 0,20 m'ye çıkabilir ).
KAPI_ARASI_AZAMI = 150.0
#  TS EN 81-20 m.5.3.4.1:  kabin eşiği ile kat kapısı eşiği arası 35 mm.
ESIK_ARASI_AZAMI = 35.0

#  Kuyudaki iki sabit parça ( ara kiriş ile karşı ağırlık ) arasında aranan
#  en küçük açıklık ( mm ).  Standardın sayısı DEĞİLDİR;  çizimin kendi
#  tutarlılık kalkanıdır — iki parçanın üst üste binmesini yakalar.
ASGARI_ACIKLIK = 20.0
#  TS EN 81-20 m.5.2.5.5.1 h:  kabin ve ona bağlı parçalar karşı ağırlıktan
#  ve ona bağlı parçalardan en az 50 mm uzakta olmalıdır.
KABIN_AGIRLIK_ACIKLIGI = 50.0
#  HALAT PAYI:  halatın kuyudaki ve kabindeki parçalardan uzaklığı ( kullanıcı
#  kararı 15 Eki — standartta sayı yok );  kabin_ustu ve kuyu_ustu kullanır.
HALAT_PAYI = 20.0

#  SORUNLARIN PARÇALARI ( sorun.Sorun — ekran çizimde kırmızı işaretler ).
#  Aynı parçanın planda ve kesitte adı ayrıdır ( "kabin_dis" · "kabin",
#  "kabin_ray" · "kabin_rayi" ):  ikisi de verilir, hangisi çizimdeyse yanar.
P_KABIN = ("kabin_dis", "kabin", "sase_dikme", "sase")
P_KABIN_RAYI = ("kabin_ray", "kabin_rayi")
P_AGIRLIK = ("agirlik_blok", "agirlik", "agirlik_pateni", "agirlik_paten")
P_AGIRLIK_RAYI = ("agirlik_ray", "agirlik_rayi")
P_KANAT = ("kanat_cebi", "kabin_kanat_cebi", "kat_kanadi", "kabin_kanadi")
P_KAPI = ("kapi_boslugu", "kat_kanadi", "kat_kapisi")
P_ASKI = ("kabin_kasnak", "kabin_kasnak_ucu", "kabin_kasnagi", "aski_nokta")
P_ESIK = ("kabin_esigi", "kat_esigi")


def kapi_onerisi(tip):
    """Kanat cebi / operatör sığmayınca kapı için öğüt — tipine göre ( 15 Eki:
    merkezi kapıya da "öbür yana açın" deniyordu;  merkezinin öbür yanı yoktur ).
    4 kanatlı merkezide kanatlar daralır, cepler küçülür."""
    t = kapi_tipi(tip)
    if t["tur"] == "teleskopik":
        return "kapıyı öbür yana açın, kanat sayısını artırın ya da kapının yerini değiştirin"
    if t["tur"] == "merkezi" and t["kanat"] < 4:
        return "4 kanatlı merkezi kapı seçin, kapıyı daraltın ya da kapının yerini değiştirin"
    return "kapıyı daraltın ya da kapının yerini değiştirin"


def kapi_tipi(tip):
    """Kat kapısı tipinin çizime girenleri:  { tur , kanat , yon , duzlem }.

      tur     teleskopik ( yandan açılır ) · merkezi ( ortadan ) · manuel
              ( menteşeli, tek kanat )
      kanat   kanat sayısı ( toplam )
      yon     teleskopikte açıldığı yan ( Sol / Sağ ), öbürlerinde None
      duzlem  kanatların kaydığı düzlem sayısı:  teleskopikte her kanat ayrı
              düzlemde, merkezide her yanın kanatları ( 2 kanatta tek düzlem )

    Adlar hesabın kat kapısı tipi listesidir ( mukavemet_tablolari.KAPI_KABLO );
    "Teleskopik Sol / Sağ" ve "Otomatik Merkezi" 2 kanatlıdır ( eski projeler
    bu adları taşır ).  3 kanatlı teleskopik ve 4 kanatlı merkezi büyük
    kapılar içindir ( kullanıcı kararı 2 Eki — Fermator 40/10:  T2 · T3 · C2 · C4 ).
    Tanınmayan tip eskisi gibi 2 kanatlı merkezi çizilir."""
    t = str(tip or "")
    yon = "Sağ" if t.endswith("Sağ") else "Sol" if t.endswith("Sol") else None
    if t.startswith("Manuel"):
        return {"tur": "manuel", "kanat": 1, "yon": yon, "duzlem": 1}
    if t.startswith("Teleskopik"):
        n = 3 if "3 Kanat" in t else 2
        return {"tur": "teleskopik", "kanat": n, "yon": yon or "Sol", "duzlem": n}
    n = 4 if "4 Kanat" in t else 2
    return {"tur": "merkezi", "kanat": n, "yon": None, "duzlem": n // 2}


def esik_derinligi(S, tip, kabin=False):
    """Kat ( kabin ) eşiğinin derinliği:  Sabitler'in eşiği ( 90 — iki kanat
    düzlemi sığar:  5 + 45 + 40 );  iki düzlemi aşan her kanat düzlemi eşiği
    kanat_araligi kadar derinleştirir:  3 kanatlı teleskopikte 135 — Fermator
    40/10'un T3 eşiği."""
    taban = S["kabin_esik_derinlik"] if kabin else S["esik_derinlik"]
    return taban + max(0, kapi_tipi(tip)["duzlem"] - 2) * S["kanat_araligi"]


def kapi_bolgesi(g, S):
    """Kapı bölgesinin derinlik kotları ( y, kuyu ön iç yüzünden ):

    kasa        kat kapısı kasası
    esik        kat kapısı eşiği ( kanatlar üstünde )
    hat         kapı hattı:  kat eşiğinin kabine bakan kenarı
    kabin_esik  kabin eşiği ( kabin kapısı kanatları üstünde ) — ön ucu
                kabin ön yüzünden kabin_esik_derinlik kadar önde
    yuzey       m.5.2.5.3.1'in "kuyunun iç yüzü":  duvar boşluğuna montajda
                duvarın kendisi;  kuyu içine montajda kapı hattı — kapıların
                altında ve üstünde yüzey hat boyunca sac kaplamayla sürer
                ( referans projenin düzeni ).
    """
    bas = -S["kasa_derinlik"] if g["kapi"]["montaj"] == "Duvar boşluğuna" else 0.0
    tip = g["kapi"].get("tip")
    kasa = (bas, bas + S["kasa_derinlik"])
    esik = (kasa[1], kasa[1] + esik_derinligi(S, tip))
    on = g["kabin"]["on_pay"]
    kabin_esik = (on - esik_derinligi(S, tip, kabin=True), on)
    return {
        "kasa": kasa,
        "esik": esik,
        "hat": esik[1],
        "kabin_esik": kabin_esik,
        "yuzey": 0.0 if g["kapi"]["montaj"] == "Duvar boşluğuna" else esik[1],
    }


def kanat_cepleri(g, S, pay=True):
    """Otomatik kapının kanat cepleri ( x0 , x1 ):  kanatlar açılınca kapı
    boşluğunun yanında üst üste durur;  kat ve kabin kapısı ünitesi o yanda
    bir kanat eni ( kapı ÷ kanat sayısı;  merkezide her yanda ) + kanat_cebi_payi
    uzanır.  2 kanatlı teleskopikte kapının yarısı + 30:  LiftDesigner'ın altı
    projesinde birebir ( DW 800 → 430, 900 → 480, 1.100 → 580 );  Fermator
    40/10 da aynı kuralı verir ( eşik T2 1,5·PL + 40 · T3 1,35·PL + 40 ·
    C2 2·PL + 40 · C4 1,5·PL + 40 ).  Elle açılan ( menteşeli ) kapıda cep
    yoktur.  pay=False:  yalnız kanatların eni ( kapı operatörünün izi )."""
    kp = g["kapi"]
    k = kapi_tipi(kp.get("tip"))
    x0, x1 = kp["sol_pay"], kp["sol_pay"] + kp["genislik"]
    if k["tur"] == "manuel":
        return []
    #  Her kanat kapının kanat sayısı kadarda biri genişliktedir;  açılınca o
    #  yandaki kanatlar üst üste durur ( teleskopikte hepsi bir yanda,
    #  merkezide her yanda yarısı ):  cep bir kanat eni.
    cep = kp["genislik"] / k["kanat"] + (S["kanat_cebi_payi"] if pay else 0.0)
    if k["tur"] == "teleskopik":
        return [(x1, x1 + cep)] if k["yon"] == "Sağ" else [(x0 - cep, x0)]
    return [(x0 - cep, x0), (x1, x1 + cep)]


#  Kanat cebi sığmayınca önerilen kapı tipleri ( sırayla:  aynı kapı öbür yana,
#  sonra daha çok kanat — büyük kapılar 3 ya da 4 kanatlı yapılır ).
KAPI_CEP_ONERILERI = (
    "Teleskopik Sol",
    "Teleskopik Sağ",
    "Teleskopik 3 Kanat Sol",
    "Teleskopik 3 Kanat Sağ",
    "Otomatik Merkezi 4 Kanat",
)


def _cep_sigar(g, S, tip):
    g2 = {**g, "kapi": {**g["kapi"], "tip": tip}}
    return all(c0 >= -1e-6 and c1 <= g["kuyu"]["genislik"] + 1e-6 for c0, c1 in kanat_cepleri(g2, S))


def kaba_bosluk(g, S):
    """Kat kapısının duvardaki kaba boşluğu ( x0 , x1 , yükseklik ):  kapıdan
    iki yanda kaba_bosluk_yan_payi geniş, döşemeden kapi_ust_payi yüksek
    ( LiftDesigner 800 KG ve 1022:  planda ve giriş görünüşünde 1.180,
    yükseklik 2.240 ) — kuyunun iç yüzlerini aşmaz.  Kuyu planı, düşey
    kesitler ve giriş görünüşü bunu kullanır ( eskiden planda boşluk kapı
    genişliği kadardı, giriş görünüşünde 1.180 ).  Kasa ( yanda kasa_yan,
    kapının kasa_ust üstüne ) bu boşluğun içindedir."""
    kp, G = g["kapi"], g["kuyu"]["genislik"]
    yan = S["kaba_bosluk_yan_payi"]
    return (
        max(0.0, kp["sol_pay"] - yan),
        min(G, kp["sol_pay"] + kp["genislik"] + yan),
        (kp.get("yukseklik") or 0) + S["kapi_ust_payi"],
    )


def _aski_olculeri(g):
    """Askı düzeninin çizime giren ölçüleri  ( eksikse boş döner )."""
    a = g.get("aski") or {}
    duzen = a.get("duzen")
    if duzen in ("Kabin altı", "Kabin üstü"):
        return ("kasnak", a.get("kasnak_capi"), a.get("kasnak_arasi"), a.get("kasnak_kaciklik", 0))
    if duzen == "Doğrudan":
        #  1:1:  tek bağlantı ( şasenin üst kirişinin ortası ) — aralığı yok
        return ("nokta", None, 0.0, a.get("nokta_kaciklik", 0))
    return (None, None, None, None)


#  Kabinin iç yüksekliği ( TS EN 81-20 m.5.4.1 ) ve kapının net geçiş
#  yüksekliği ( m.5.3.1.1 ) en az bu kadardır  ( mm )
ASGARI_YUKSEKLIK = 2000.0


def dogrula(g):
    """Girdinin kendisinin denetimi:  eksik / geçersiz alanlar ( metin listesi;
    boşsa temiz ).  Planın parçalarıyla yapılan denetim ( kanat cepleri )
    geometri.dogrula'dadır — çizimler ve hesap onu çağırır.  Denetimler
    sırayla çalışır ( iletiler bu sırayla çıkar )."""
    hata = _zorunlu_alanlar(g)
    if hata:
        return hata
    #  GEOMETRİ TUTARLILIĞI — çizim kâğıda sığsın, parçalar çakışmasın.
    S = sabitler.sabitler(g.get("_cizim_sabitleri"))
    hata += _yukseklikler(g)
    hata += _ana_olculer(g)
    K = _kabin_ve_agirlik_kutulari(g, S)
    hata += _kabin_ve_agirlik(g, K)
    hata += _kanat_cebi_hatalari(g, S)
    hata += _agirlik_raylari(g, S, K)
    hata += _sase_ve_kapi(g, K)
    hata += _ara_kiris(g, S, K)
    hata += _aski_hatalari(g, S)
    hata += _kapi_acikliklari(g, S)
    return hata


def _zorunlu_alanlar(g):
    hata = []
    for bolum, alanlar in ZORUNLU.items():
        d = g.get(bolum)
        if not isinstance(d, dict):
            hata.append(f"'{bolum}' bölümü eksik.")
            continue
        for a in alanlar:
            v = d.get(a)
            if a == "yeri":
                if v not in AGIRLIK_YERLERI:
                    hata.append(f"agirlik.yeri: {AGIRLIK_YERLERI} içinden olmalı ( {v!r} ).")
                continue
            if a == "duzen":
                continue  # aşağıda ayrıca denetlenir
            if a == "montaj":
                if v not in KAPI_MONTAJLARI:
                    hata.append(f"kapi.montaj: {KAPI_MONTAJLARI} içinden olmalı ( {v!r} ).")
                continue
            ad = ADLAR.get(f"{bolum}.{a}", f"{bolum}.{a}")
            if not _sonlu_sayi(v):
                hata.append(f"{ad}:  sayı olmalı ( {v!r} ).")
            elif a in ("kaciklik_y", "eksen_kaciklik"):
                continue  # işaretli olabilir
            elif v <= 0:
                kaynak = TURETILEN.get(f"{bolum}.{a}")
                hata.append(
                    f"{ad} {f'{v:g}'.replace('.', ',')} mm çıktı;  sıfırdan büyük olmalı"
                    + (f" ( {kaynak} türetilir )." if kaynak else ".")
                )
    return hata


def _yukseklikler(g):
    """YÜKSEKLİKLER ( kullanıcı kararı 4 Eki ):  kabinin iç yüksekliği ve kapının
    net geçiş yüksekliği en az 2.000 mm;  kapı kabinin girişidir, kabinden
    yüksek olamaz.  Eskiden 1.500'lük kabin, 1.800'lük ya da kabinden yüksek
    kapı sessizce çiziliyor ve hesaplanıyordu."""
    hata = []
    kabin_h = (g.get("dusey") or {}).get("kabin_ic_yukseklik")
    kapi_h = g["kapi"].get("yukseklik")
    if _sonlu_sayi(kabin_h) and kabin_h < ASGARI_YUKSEKLIK:
        hata.append(
            sorun.Sorun(
                f"Kabin iç yüksekliği {kabin_h:g} mm:  TS EN 81-20 m.5.4.1 en az {ASGARI_YUKSEKLIK:g} mm ister.",
                ("kabin",),
                "kuyu_kesiti_yan",
            )
        )
    if _sonlu_sayi(kapi_h) and kapi_h < ASGARI_YUKSEKLIK:
        hata.append(
            sorun.Sorun(
                f"Kat kapısı yüksekliği {kapi_h:g} mm:  TS EN 81-20 m.5.3.1.1 en az {ASGARI_YUKSEKLIK:g} mm ister.",
                P_KAPI,
                "kapi_kesiti",
            )
        )
    if _sonlu_sayi(kabin_h) and _sonlu_sayi(kapi_h) and kapi_h > kabin_h:
        hata.append(
            sorun.Sorun(
                f"Kat kapısı yüksekliği ( {kapi_h:g} mm ) kabin iç yüksekliğinden "
                f"( {kabin_h:g} mm ) büyük olamaz:  kapı kabinin girişidir.",
                P_KAPI + ("kabin",),
                "kuyu_kesiti_yan",
            )
        )
    return hata


def _ana_olculer(g):
    """Kabin, kapı ve raylar kuyuya sığar;  kabin rayları kabinin derinliği
    içinden geçer."""
    hata = []
    k, kb, kp, kr = g["kuyu"], g["kabin"], g["kapi"], g["kabin_ray"]
    if kb["genislik"] >= k["genislik"]:
        hata.append(
            sorun.Sorun(
                f"Kabin genişliği ({kb['genislik']}) kuyu genişliğinden ({k['genislik']}) küçük olmalı.",
                P_KABIN,
                "kuyu_plani",
            )
        )
    if kb["derinlik"] >= k["derinlik"]:
        hata.append(
            sorun.Sorun(
                f"Kabin derinliği ({kb['derinlik']}) kuyu derinliğinden ({k['derinlik']}) küçük olmalı.",
                P_KABIN,
                "kuyu_plani",
            )
        )
    if kp["sol_pay"] + kp["genislik"] > k["genislik"]:
        hata.append(sorun.Sorun("Kapı boşluğu kuyu genişliğine sığmıyor.", P_KAPI, "kuyu_plani"))
    if kr["kapi_arasi"] >= k["derinlik"]:
        hata.append(
            sorun.Sorun("Ray – kapı arası kuyu derinliğinden büyük olamaz.", P_KABIN_RAYI, "kuyu_plani")
        )
    if kr["arasi"] > k["genislik"]:
        hata.append(sorun.Sorun("Kabin rayları arası kuyu genişliğine sığmıyor.", P_KABIN_RAYI, "kuyu_plani"))
    #  KABİN RAYI DUVARA GİREMEZ ( 15 Eki — senaryo taraması:  K111, r270 ):  ray
    #  arası sığsa da kabin kaçıklığı ve rayın yüksekliği rayı duvara sokabiliyor.
    #  Eşik 0 ( kullanıcı kararı ):  EN 81-20'de ray – duvar için sayı yok;  dar
    #  boşlukta ray tek sacla duvara bağlanır ( parcalar.konsol_cifti_bicimi ),
    #  gerçek projede 15 mm görüldü.  Ağırlık tarafında ray ara kirişe bağlıdır
    #  ( _ara_kiris denetler ).
    for yan, bosluk in kabin_rayi_duvar_bosluklari(g).items():
        if bosluk < 0 and g["agirlik"]["yeri"] != yan:
            hata.append(
                sorun.Sorun(
                    f"Kabin rayı {yan.lower()} duvara {-bosluk:g} mm giriyor ( rayın arkası ile duvar "
                    "arası ≥ 0 olmalı ):  kabin rayları arasını ( DBG ), kabinin yana kaçıklığını "
                    "ya da kuyu genişliğini gözden geçirin.",
                    P_KABIN_RAYI,
                    "kuyu_plani",
                )
            )
    #  KABİN RAYLARININ ARASINDA GİDER:  ray ekseni kabinin derinliği içinden
    #  geçmeli;  geçmezse patenler kabine değil boşluğa bağlanır.
    if not (kb["on_pay"] <= kr["kapi_arasi"] <= kb["on_pay"] + kb["derinlik"]):
        hata.append(
            sorun.Sorun(
                f"Kabin rayı ekseni ( kapıdan {kr['kapi_arasi']:g} ) kabinin "
                f"derinliği içinden geçmiyor ( kabin {kb['on_pay']:g} – "
                f"{kb['on_pay'] + kb['derinlik']:g} ).",
                P_KABIN_RAYI + P_KABIN,
                "kuyu_plani",
            )
        )
    return hata


def kabin_rayi_duvar_bosluklari(g):
    """{ "Sol" | "Sağ" :  kabin rayının arka yüzü ile o yandaki duvar arası ( mm ) }
    — geometri._kabin_raylari ile aynı bağıntı:  ray yüzleri kabin ekseninin
    ± DBG / 2'sinde, arka yüzleri rayın yüksekliği kadar dışarıda."""
    k, kb, kr = g["kuyu"], g["kabin"], g["kabin_ray"]
    kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
    return {
        "Sol": kx - kr["arasi"] / 2.0 - kr["h"],
        "Sağ": k["genislik"] - (kx + kr["arasi"] / 2.0 + kr["h"]),
    }


def _kabin_ve_agirlik_kutulari(g, S):
    """Kabinin ( pano ve şasenin dış zarfı ) ve karşı ağırlığın ( patenleriyle )
    plan kutuları ve eksenleri:  { kx, kabin, agirlik, ex | ey, ag_y }."""
    k, kb, ag = g["kuyu"], g["kabin"], g["agirlik"]
    kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
    # İç ölçü yerine çizilen pano ve şasenin dış zarfını denetle.
    yari_en = kb["genislik"] / 2.0 + S["kabin_pano_yan"] + S["sase_dikme"]
    K = {
        "kx": kx,
        "kabin": (
            kx - yari_en,
            kb["on_pay"],
            kx + yari_en,
            kb["on_pay"] + kb["derinlik"] + S["kabin_pano_arka"],
        ),
    }
    #  KABİN İLE KARŞI AĞIRLIK ÇAKIŞAMAZ.  Blok, ağırlık rayı eksenine
    #  ortalanır;  kabinin yanından en az ASGARI_ACIKLIK kadar uzak durmalı.
    if ag["yeri"] in ("Sağ", "Sol"):
        ex = ag["ray_duvar"] if ag["yeri"] == "Sol" else k["genislik"] - ag["ray_duvar"]
        ag_y = g["kabin_ray"]["kapi_arasi"] + ag["eksen_kaciklik"]
        K.update(ex=ex, ag_y=ag_y)
        ag_kutu = (
            ex - ag["derinlik"] / 2.0,
            ag_y - ag["genislik"] / 2.0,
            ex + ag["derinlik"] / 2.0,
            ag_y + ag["genislik"] / 2.0,
        )
    else:
        ey = k["derinlik"] - ag["ray_duvar"]
        K["ey"] = ey
        ag_kutu = (
            k["genislik"] / 2.0 - ag["genislik"] / 2.0,
            ey - ag["derinlik"] / 2.0,
            k["genislik"] / 2.0 + ag["genislik"] / 2.0,
            ey + ag["derinlik"] / 2.0,
        )
    #  Ağırlığa bağlı patenler ( m.5.2.5.5.1 h:  "ve ona bağlı parçalar" ) rayın
    #  ucunda;  derinlik boyunca bloğun dışına taşabilir ( makaralının yan
    #  makaraları — geometri._agirlik_pateni ).  Denetimler taşan kısmı da sayar.
    yari = parcalar.agirlik_pateni_yari_eni(
        ag.get("paten_tipi"), parcalar.ray_dil_kalinligi(ag["b"], ag["h"]), S["paten_boy"]
    )
    if yari > ag["derinlik"] / 2.0:
        t = yari - ag["derinlik"] / 2.0
        ag_kutu = (
            (ag_kutu[0] - t, ag_kutu[1], ag_kutu[2] + t, ag_kutu[3])
            if ag["yeri"] in ("Sağ", "Sol")
            else (ag_kutu[0], ag_kutu[1] - t, ag_kutu[2], ag_kutu[3] + t)
        )
    K["agirlik"] = ag_kutu
    return K


def _kabin_ve_agirlik(g, K):
    """Kabin ve ağırlık kuyunun içinde, aralarında m.5.2.5.5.1 h açıklığı."""
    hata = []
    k = g["kuyu"]
    kabin_kutu, ag_kutu = K["kabin"], K["agirlik"]
    if (
        kabin_kutu[0] < 0
        or kabin_kutu[2] > k["genislik"]
        or kabin_kutu[1] < 0
        or kabin_kutu[3] > k["derinlik"]
    ):
        hata.append(sorun.Sorun("Kabin veya şasesi kuyunun dışına taşıyor.", P_KABIN, "kuyu_plani"))
    A = KABIN_AGIRLIK_ACIKLIGI
    if (
        ag_kutu[0] < kabin_kutu[2] + A
        and kabin_kutu[0] < ag_kutu[2] + A
        and ag_kutu[1] < kabin_kutu[3] + A
        and kabin_kutu[1] < ag_kutu[3] + A
    ):
        hata.append(
            sorun.Sorun(
                f"Karşı ağırlık ile kabin arasında {A:g} mm açıklık yok ( TS EN 81-20 "
                "m.5.2.5.5.1 h ) — ağırlık rayı – duvar ölçüsünü ya da kabin ölçülerini "
                "gözden geçirin.",
                P_AGIRLIK + P_KABIN,
                "kuyu_plani",
            )
        )
    if ag_kutu[0] < 0 or ag_kutu[2] > k["genislik"] or ag_kutu[1] < 0 or ag_kutu[3] > k["derinlik"]:
        hata.append(sorun.Sorun("Karşı ağırlık kuyunun dışına taşıyor.", P_AGIRLIK, "kuyu_plani"))
    return hata


def _kanat_cebi_hatalari(g, S):
    """KANAT CEBİ:  otomatik kapının kanatları açılınca kapının yanında, kuyunun
    içinde durur ( kanat_cepleri ) — yan duvara ya da karşı ağırlığa girmemeli."""
    hata = []
    k, kp = g["kuyu"], g["kapi"]
    for c0, c1 in kanat_cepleri(g, S):
        if c0 < -1e-6 or c1 > k["genislik"] + 1e-6:
            yan = kp["sol_pay"] if c0 < 0 else k["genislik"] - kp["sol_pay"] - kp["genislik"]
            n = kapi_tipi(kp.get("tip"))["kanat"]
            oneri = [t for t in KAPI_CEP_ONERILERI if t != kp.get("tip") and _cep_sigar(g, S, t)]
            hata.append(
                sorun.Sorun(
                    f"Kapının kanat cebi kuyuya sığmıyor:  kapı açıldığı yanda duvara {yan:g} mm, "
                    f"açılan {n} kanat için {c1 - c0:g} mm gerekir ( bir kanat eni "
                    f"{kp['genislik'] / n:g} + {S['kanat_cebi_payi']:g} )"
                    + (f";  sığan kapı tipi:  {' · '.join(oneri)}." if oneri else "."),
                    P_KANAT,
                    "kuyu_plani",
                )
            )
    return hata


def _agirlik_raylari(g, S, K):
    """PARÇALAR KENDİ RAYLARININ ARASINA SIĞMALI.  Çerçeve / şase, iki rayın
    birbirine bakan yüzleri arasında kalır;  patenler bu aralıkta kayar.
    Rayların arkasındaki konsol plakaları da kuyu içinde kalmalı:  yan
    yerleşimde bu zarf derinlikte, arka yerleşimde genişliktedir."""
    hata = []
    k, ag = g["kuyu"], g["agirlik"]
    if ag["genislik"] >= ag["ray_arasi"]:
        hata.append(
            sorun.Sorun(
                f"Karşı ağırlık genişliği ({ag['genislik']:g}) ağırlık rayları arasından "
                f"( DBGW {ag['ray_arasi']:g} ) küçük olmalı — çerçeve iki rayın arasında durur.",
                P_AGIRLIK + P_AGIRLIK_RAYI,
                "kuyu_plani",
            )
        )
    #  ÇERÇEVENİN İÇİ:  dolgu ve kasnak iki çerçeve profilinin arasında durur
    #  ( geometri._agirlik_blogu:  iç ölçü = dış − 2 × agirlik_cerceve ).  İç
    #  ölçü sıfır ya da eksiyken plan ve kesit eksi enli dolgu ve kasnak çizip
    #  paketi üretiyordu ( Gx 60, çerçeve 40 → −20 ).
    cer = S["agirlik_cerceve"]
    for ad, olcu in (("derinliği ( Gx )", ag["derinlik"]), ("genişliği", ag["genislik"])):
        if olcu <= 2 * cer:
            hata.append(
                sorun.Sorun(
                    f"Karşı ağırlık {ad} {olcu:g} mm:  çerçeve profilinin iki kalınlığından "
                    f"( 2 × {cer:g} = {2 * cer:g} ) büyük olmalı — dolguya ve kasnağa yer kalmıyor.",
                    P_AGIRLIK + ("agirlik_dolgu",),
                    "kuyu_plani",
                )
            )
    ray_yari = ag["ray_arasi"] / 2.0 + ag["h"] + S["konsol_agirlik_boy"] / 2.0
    if ag["yeri"] in ("Sağ", "Sol"):
        ex, ag_y = K["ex"], K["ag_y"]
        tasiyor = (
            ag_y - ray_yari < 0
            or ag_y + ray_yari > k["derinlik"]
            or ex - ag["b"] / 2.0 < 0
            or ex + ag["b"] / 2.0 > k["genislik"]
            or S["konsol_agirlik_en"] > k["genislik"]
        )
    else:
        ey = K["ey"]
        tasiyor = (
            k["genislik"] / 2.0 - ray_yari < 0
            or k["genislik"] / 2.0 + ray_yari > k["genislik"]
            or ey - ag["b"] / 2.0 < 0
            or ey + ag["b"] / 2.0 > k["derinlik"]
            or S["konsol_agirlik_en"] > k["derinlik"]
        )
    if tasiyor:
        hata.append(
            sorun.Sorun(
                "Karşı ağırlık rayları veya konsolları kuyunun dışına taşıyor.",
                P_AGIRLIK_RAYI + ("agirlik_konsolu",),
                "kuyu_plani",
            )
        )
    return hata


def _sase_ve_kapi(g, K):
    """Şase kabin rayları arasına sığar;  kat kapısı kabinin önüne düşer."""
    hata = []
    kb, kp = g["kabin"], g["kapi"]
    sase_dis = K["kabin"][2] - K["kabin"][0]
    if sase_dis >= g["kabin_ray"]["arasi"]:
        hata.append(
            sorun.Sorun(
                f"Kabin şasesinin dış genişliği ({sase_dis:g}) kabin rayları arasından "
                f"( DBG {g['kabin_ray']['arasi']:g} ) küçük olmalı.",
                ("sase_dikme", "sase") + P_KABIN_RAYI,
                "kuyu_plani",
            )
        )
    #  KAPI KABİNİN ÖNÜNE DÜŞMELİ:  kat kapısının net boşluğu kabin iç
    #  genişliğinin dışına taşarsa kabin kapısıyla karşılaşmaz.
    kx = K["kx"]
    if (
        kp["sol_pay"] < kx - kb["genislik"] / 2.0
        or kp["sol_pay"] + kp["genislik"] > kx + kb["genislik"] / 2.0
    ):
        hata.append(
            sorun.Sorun(
                "Kat kapısı boşluğu kabinin önüne düşmüyor — kapının soldan uzaklığını "
                "ya da kabinin yana kaçıklığını gözden geçirin.",
                P_KAPI + ("kabin_dis",),
                "kuyu_plani",
            )
        )
    return hata


def _ara_kiris(g, S, K):
    """AĞIRLIK YANDAYSA o taraftaki kabin rayı ağırlık konsollarına bağlı
    bir ara kirişte durur;  kiriş ağırlıkla kabin rayı arasına sığmalı."""
    ag = g["agirlik"]
    if ag["yeri"] not in ("Sağ", "Sol"):
        return []
    kr_, kx, ag_kutu = g["kabin_ray"], K["kx"], K["agirlik"]
    if ag["yeri"] == "Sol":
        ray_arkasi = kx - kr_["arasi"] / 2.0 - kr_["h"]
        bosluk = ray_arkasi - S["ara_kiris_en"] - ag_kutu[2]
    else:
        ray_arkasi = kx + kr_["arasi"] / 2.0 + kr_["h"]
        bosluk = ag_kutu[0] - (ray_arkasi + S["ara_kiris_en"])
    if bosluk < ASGARI_ACIKLIK:
        return [
            sorun.Sorun(
                f"Karşı ağırlık ile kabin rayının ara kirişi arasında {bosluk:g} mm kalıyor "
                f"( en az {ASGARI_ACIKLIK:g} ) — ağırlık rayı – duvar ölçüsünü ya da "
                "kabinin yana kaçıklığını gözden geçirin.",
                ("ara_kiris",) + P_AGIRLIK,
                "kuyu_plani",
            )
        ]
    return []


def _aski_hatalari(g, S):
    """ASKI DÜZENİ:  ölçüleri ve kuyuya sığması."""
    a = g.get("aski") or {}
    if a.get("duzen") not in ASKI_DUZENLERI:
        return [f"aski.duzen: {ASKI_DUZENLERI} içinden olmalı ( {a.get('duzen')!r} )."]
    hata = []
    k, kb = g["kuyu"], g["kabin"]
    tur, cap, aralik, kaciklik = _aski_olculeri(g)
    gerekli = [("aralık", aralik), ("kasnak çapı", cap)] if tur == "kasnak" else []
    for ad, v in gerekli:
        if not _sonlu_sayi(v) or v <= 0:
            hata.append(f"aski: {ad} sıfırdan büyük bir sayı olmalı ( {v!r} ).")
    if not _sonlu_sayi(kaciklik):
        hata.append(f"aski: kaçıklık sonlu bir sayı olmalı ( {kaciklik!r} ).")

    if arka_aski.arkada_iki_bir(g) and _sonlu_sayi(kaciklik):
        #  Arkadaki ağırlıkla 2:1:  kasnaklar çapraz düzlemde, aralığı
        #  geometriden ( arka_aski ) — sınırlarını o denetler.
        hata += [h for h in arka_aski.geometri(g, S)["hata"] if "kuyunun dışına" in h]
    elif all(_sonlu_sayi(v) and v > 0 for _, v in gerekli) and _sonlu_sayi(kaciklik):
        yari = aralik / 2.0 + (cap / 2.0 if tur == "kasnak" else 45.0)
        kx = k["genislik"] / 2.0 + kb["kaciklik_y"]
        aski_y = kb["on_pay"] + (kb["derinlik"] + S["kabin_pano_arka"]) / 2.0 + kaciklik
        yari_y = S["kabin_kasnak_genislik"] / 2.0 if tur == "kasnak" else 45.0
        if (
            kx - yari < 0
            or kx + yari > k["genislik"]
            or aski_y - yari_y < 0
            or aski_y + yari_y > k["derinlik"]
        ):
            hata.append(
                sorun.Sorun("Askı kasnakları / noktaları kuyunun dışına taşıyor.", P_ASKI, "kuyu_plani")
            )
    return hata


def _kapi_acikliklari(g, S):
    """KAPI AÇIKLIKLARI — standardın kendi sınırları, kabin EŞİĞİNİN ön
    kenarından ölçülür ( kabin gövdesinden değil )."""
    hata = []
    kb, kp = g["kabin"], g["kapi"]
    KB = kapi_bolgesi(g, S)
    kabin_esigi = KB["kabin_esik"][0]
    esik_arasi = kabin_esigi - KB["hat"]
    if esik_arasi <= 0:
        hata.append(
            sorun.Sorun(
                f"Kabin eşiği kat kapısı eşiğine biniyor ( {esik_arasi:g} mm ):  kabin "
                f"ön yüzü ( on_pay {kb['on_pay']:g} ) en az "
                f"{KB['hat'] + S['kabin_esik_derinlik']:g} olmalı.",
                P_ESIK,
                "kapi_kesiti",
            )
        )
    elif esik_arasi > ESIK_ARASI_AZAMI:
        hata.append(
            sorun.Sorun(
                f"Kabin eşiği ile kat kapısı eşiği arası {esik_arasi:g} mm — "
                f"TS EN 81-20 m.5.3.4.1 en çok {ESIK_ARASI_AZAMI:g} mm verir.",
                P_ESIK,
                "kapi_kesiti",
            )
        )
    if kp["montaj"] == "Duvar boşluğuna" and (
        S["kasa_yan"] > S["kaba_bosluk_yan_payi"] or S["kasa_ust"] > S["kapi_ust_payi"]
    ):
        hata.append(
            sorun.Sorun(
                f"Kat kapısının kasası duvardaki kaba boşluğa sığmıyor:  kasa yanda "
                f"{S['kasa_yan']:g}, kapının üstünde {S['kasa_ust']:g} mm;  boşluğun payları "
                f"{S['kaba_bosluk_yan_payi']:g} ve {S['kapi_ust_payi']:g} mm ( Sabitler ).",
                ("kapi_kasasi",),
                "giris",
            )
        )
    if kabin_esigi - KB["yuzey"] > KAPI_ARASI_AZAMI:
        hata.append(
            sorun.Sorun(
                f"Kuyu iç yüzü ile kabin eşiği arası {kabin_esigi - KB['yuzey']:g} mm — "
                f"TS EN 81-20 m.5.2.5.3.1 en çok {KAPI_ARASI_AZAMI:g} mm verir.",
                ("kabin_esigi",),
                "kapi_kesiti",
            )
        )
    return hata


#  ── DENEME GİRDİSİ  ─────────────────────────────────────────────────
#  Yayımlanmış bir referans projenin ölçüleri.  Kendi
#  çizimimizi onun paftasıyla ölçü ölçü karşılaştırabilmek için duruyor;
#  çizim mantığı ORADAN KOPYALANMAZ, yalnız sayılar denemede kullanılır.
ORNEK = {
    "proje": {"ad": "ÖRNEK PROJE", "asansor": "ASANSÖR 1", "olcek": 20},
    "kuyu": {
        "genislik": 2100,
        "derinlik": 1850,
        "duvar_on": 150,
        "duvar_arka": 150,
        "duvar_sol": 150,
        "duvar_sag": 150,
        "doseme": 150,
    },
    #  KAPI BÖLGESİ ( referans proje kuyu planı vektörleri, iç yüzden ):  kat kapısı
    #  ünitesi duvarın İÇ YÜZÜNE monte — kasa 0 – 60, eşik 60 – 150, kapı hattı
    #  150;  eşik aralığı 30;  kabin eşiği 180 – 270 → kabin ön yüzü 270.
    "kabin": {"genislik": 1350, "derinlik": 1400, "kaciklik_y": 130, "on_pay": 270},
    #  sol_pay:  kuyunun sol iç yüzünden kapının NET BOŞLUĞUNA ( kasa içi ).
    #  Referans projenin yazdığı 610, kasaya kadardır:  610 + kasa 120 = 730;  kapı
    #  ekseni böylece kabin ekseniyle aynı ( 1.180 ) olur.
    "kapi": {
        "genislik": 900,
        "sol_pay": 730,
        "yukseklik": 2100,
        "tip": "Teleskopik Sol",
        "montaj": "Kuyu içine",
    },
    #  kapi_arasi:  ray ekseni kuyunun ön İÇ YÜZÜNDEN.  Referans projenin "1017"si
    #  KAPI HATTINDAN ölçülür ( zincir 150 + 1017 + 682 = 1850 ):  iç yüzden
    #  1.167.  ( Eskiden 1.017 iç yüzden alınmıştı — arka duvar 150 geride kalıyordu. )
    "kabin_ray": {"arasi": 1550, "kapi_arasi": 1167, "b": 89, "h": 62},
    #  Karşı ağırlık çerçevesi referans proje paftasının vektör geometrisinden
    #  ölçüldü:  790 ( raylar boyunca ) × 160 mm — DBGW 850'nin içinde,
    #  iki uçta 30 mm paten payı.  ( Eski 1.250 × 250, makine dairesi
    #  çiziminden yanlış okunmuştu;  blok kendi raylarının dışına taşıyordu. )
    #  eksen_kaciklik:  yandaki ağırlığın ekseni kabin ray ekseninin 50 mm
    #  önünde ( referans proje paftasındaki "50" ölçüsü;  − = kapıya doğru ).
    "agirlik": {
        "yeri": "Sol",
        "genislik": 790,
        "derinlik": 160,
        "ray_arasi": 850,
        "ray_duvar": 130,
        "eksen_kaciklik": -50,
        "b": 70,
        "h": 65,
        #  referans projenin hesabı:  "Guide Shoe Type : Roller Type"
        "kasnak_capi": 400,
        "paten_tipi": "Makaralı",
    },
    #  2:1 askı, kasnaklar kabinin altında.  Kasnaklar arası referans proje
    #  paftasında 690 + 690 = 1.380 ( eski 1.470 yanlış okunmuştu;  halat
    #  kabin rayının ara kirişinin içinden geçiyordu ).
    #  KAÇIKLIK HALATLARI DÜŞEY İNDİRİR:  referans projede kabin kasnaklarının
    #  çizgisi = tahrik kasnağının çizgisi = ağırlık kasnağının ön teğeti
    #  ( ağırlık ekseni − 200 ).  Bu örnekte ağırlık ekseni 1.167 − 50 = 1.117,
    #  teğet 917;  kabin merkezi 270 + 1.433 / 2 = 986,5 → kaçıklık −69,5.
    "aski": {
        "duzen": "Kabin altı",
        "kasnak_capi": 240,
        "kasnak_arasi": 1380,
        "kasnak_kaciklik": -69.5,
        "halat_adedi": 7,
        "halat_capi": 6.5,
    },
    #  Kabin üstü planı:  sığınma alanı tipi  ( TS EN 81-20 Çizelge 3 ).
    #  Hesap programındaki "Kabin üstü sığınma hacmi tipi" ile aynı seçim.
    "kabin_ustu": {"siginma_tipi": "Çömelme"},
    #  Kuyu dibi planı.  derinlik, sığınma tipi ve tampon adetleri hesap
    #  programında zaten vardır ( kuyu dibi yüksekliği KY, "Kuyu dibi sığınma
    #  hacmi tipi", kabin / ağırlık tamponu adedi );  köprü onları taşır.
    #  Regülatör gergi kasnağı referans proje paftasındaki gibi karşı ağırlığın
    #  karşısındaki kabin rayının hizasında, ray ekseninin 280 mm arkasında;
    #  gergi ağırlığı kasnağın 380 ötesine uzanır ( referans proje hesabı A = 300 ):
    #  1167 + 280 + 380 = 1827, arka duvara 23.  Üst regülatör de aynı ekseni
    #  kullanır.
    "kuyu_dibi": {
        "derinlik": 1500,
        "siginma_tipi": "Çömelme",
        "kabin_tampon_adedi": 1,
        "agirlik_tampon_adedi": 1,
        "regulator_yan": "Sağ",
        "regulator_kaciklik": 280,
        #  Regülatör halatının çapı ( hesap programında "Regülatör
        #  halatı çapı";  referans proje regülatör hesabı 6,0 ):  makine
        #  dairesinde döşeme deliği bundan çıkar.
        "regulator_halat_capi": 6,
        "regulator_kasnak_capi": 300,
    },
    #  DÜŞEY:  kabinin iç yüksekliği ve paten arası, son kat yüksekliği,
    #  beyan hızı, duraklar ve tamponlar — hepsi hesap programında var
    #  ( paten arası 3.300, beyan hızı, tampon kaideleri / boyları / ezilme /
    #  çarpma arası ).  Kuyu dibi referans projeninki:  1.500 = kaide 764 + tampon
    #  160 + çarpma arası 96 + kabinin şase altı 480.  Son kat referans proje 5.000.
    #  Duraklar:  8 × 3.000 → seyir 21 m ( hesap programının varsayılanı ).
    #  Ağırlık paten arası = patenlerin merkezleri arası:  referans proje çiziminde
    #  3.060 — 2.920'lik çerçeve + 140'lık patenler üstünde ve altında ( hesabı 1.500
    #  alır — kendi çizimiyle çelişir;  örnek çizimi izler ).  8 Eki'ye dek 2.920
    #  ( patenler çerçevenin uçlarına ortalı sayılıyordu ).
    "dusey": {
        "kabin_ic_yukseklik": 2250,
        "kabin_paten_arasi": 3300,
        "agirlik_paten_arasi": 3060,
        "son_kat": 5000,
        "beyan_hizi": 1.0,
        "durak_adedi": 8,
        "kat_yuksekligi": 3000,
        "kabin_tampon_baba": 764,
        "kabin_tampon_boyu": 160,
        "kabin_carpma_arasi": 96,
        "kabin_tampon_ezilme": 90,
        "agirlik_tampon_baba": 300,
        "agirlik_tampon_boyu": 160,
        "agirlik_carpma_arasi": 150,
        "agirlik_tampon_ezilme": 90,
        #  Konsollar arası ( hesap programının "kabin / ağırlık rayı
        #  konsollar arası en uzun mesafe" girdileri ) — referans proje 1.500.
        "kabin_konsol_arasi": 1500,
        "agirlik_konsol_arasi": 1500,
    },
    #  Makine:  tahrik kasnağı çapı hesap programında var ( D1 ).  Kuyu üstü
    #  ( MRL ) ve makine dairesi planları ortak okur.
    #  Makinenin yeri:  "Kuyu üstü" ( makine dairesiz — referans proje ) ya da
    #  "Makine dairesi";  hesap programındaki "Makine dairesiz ( MRL )" seçimi.
    #  Makine tipi:  hesap programının "Makine tipi" ( Dişlisiz / Dişli );  çizim
    #  makineyi buna göre çizer ( makine.py:  LiftDesigner makineleri ).
    #  Yan yatak:  hesap programının "F ( yan yatak — makine kirişi )" NPU'su —
    #  makinenin oturduğu iki kiriş ( kuyu üstünde raylara, makine dairesinde
    #  kaidenin dikine kirişlerine oturur ).  Referans proje:  UPN 200 ( şase hesabında
    #  Wx 191 cm³ ).
    "makine": {"tahrik_kasnak_capi": 240, "yeri": "Kuyu üstü", "tip": "Dişlisiz", "yan_yatak": 200},
    #  Kuyu üstü planı ( makine dairesiz ):  acil kurtarma panosu en üst
    #  kattaki kapının hangi yanında.
    "kuyu_ustu": {"acil_pano_yan": "Sol"},
    #  Makine dairesi ( makine daireli asansör ).  İç ölçüler hesap
    #  programında var ( makine dairesi uzunluğu / genişliği;  örnek:  o
    #  programın kendi test verisi 3.800 × 2.600 ).  x, y:  odanın iç sol-ön
    #  köşesinin kuyunun iç sol-ön köşesine göre yeri — oda kuyunun üstünde,
    #  iki yana 100 mm taşar, önü kuyunun ön duvarıyla aynı hizada.
    #  Kapı ve pano duvarı:  "Ön" · "Arka" · "Sol" · "Sağ";  kapı konumu
    #  duvarın sol ( ön ) iç köşesinden kapı boşluğuna.
    "makine_dairesi": {
        "genislik": 2600,
        "derinlik": 3800,
        "duvar": 200,
        "x": -250,
        "y": -150,
        "kapi_duvar": "Arka",
        "kapi_konum": 300,
        "kapi_genislik": 800,
        "pano_duvar": "Sağ",
        #  Düşey kesit için:  iç ( temiz ) yükseklik ( LiftDesigner
        #  "477-8":  3.500 ).  Kapı yüksekliği:  TS EN 81-20 m.5.2.3.2 a'nın
        #  en azı 2.000.
        "yukseklik": 3500,
        "kapi_yukseklik": 2000,
        #  Hesap programının makine dairesi girdileri ( adları aynı;
        #  değerler o programın varsayılanları ):  tabliye beton
        #  yüksekliği = oda döşemesinin ( kuyunun üstündeki betonun )
        #  kalınlığı;  makine kaidesi:  şase yüksekliği ( dikine kirişin
        #  boyu, döşemeden kaidenin üstüne ) ve dikine kiriş NPU'su.
        #  Yan yatakların mesnet aralığı çizimden ( kaide makineyi sarar ).
        "tabliye_yuksekligi": 1200,
        "sase_yuksekligi": 1100,
        "dikine_kiris": 120,
    },
    #  Referans projenin kabini ( programın ofis standardı ofisin kendi kabini )
    "_cizim_sabitleri": dict(sabitler.REFERANS_PROJE_KABINI),
}
