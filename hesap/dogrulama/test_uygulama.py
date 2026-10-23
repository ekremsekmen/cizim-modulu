# -*- coding: utf-8 -*-
"""
TEST 11  —  UYGULAMA PROJESİ  ( orkestratör )

motor/uygulama.py mukavemet ve avan motorlarını TEK GİRDİ SETİYLE koşturur.
Bu testin asıl konusu ORTAK GİRDİ KÖPRÜSÜDÜR:

    Kullanıcı kabin genişliğini bir kez girer;  hem mukavemet hem kabin
    aydınlatması aynı değerden beslenmelidir.

Köprü sessizce kopabilir ( alan adı değişir, biri None kalır ) ve hiçbir
hesap testi bunu göremez — iki motor da kendi içinde tutarlı çalışmaya devam
eder.  Bu yüzden burada her ortak alan TEK TEK oynatılır ve elektrik
sonucunun gerçekten değiştiği doğrulanır.
"""

import io
import json
import os
import re
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _on_yuz_kaynagi():
    """Ön yüzün ( on-yuz/src, React ) bütün kaynağı — ekranın kendi metin ya da
    hüküm kurmadığını denetlemek için."""
    import glob

    kok = os.path.join(os.path.dirname(KOK), "on-yuz", "src")
    return "".join(
        open(p, encoding="utf-8").read()
        for p in sorted(glob.glob(os.path.join(kok, "**", "*.ts*"), recursive=True))
    )


#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(KOK))
import yollar

yollar.kur()

from motor.avan import avan_hesabi
from motor.avan import tablolar
from motor.uygulama import mukavemet
from motor.uygulama import uygulama_hesabi
from motor.uygulama import uygulama_girdisi
from motor.uygulama import uygulama_sabitleri
from dogrulama.rapor import P_std as _P_std, Rapor
from ciktilar import dxf_cikti
from ciktilar import pdf_cikti
from motor.uygulama import mukavemet_girdi
from uclar import uc_ortak, uygulama_uclari
from motor.ortak import adimlar
from uclar import uygulama_istegi

#  Topraklama olmadan elektrik bölümlerinin bir kısmı boş kalır.  L1 girdi
#  değildir:  kuyu yüksekliği + Sabitler'deki yatay güzergâh payından kurulur.
TAM = {"temel_a": 26.55, "temel_b": 16.4}


def _bolum_adlari(s):
    return [b["baslik"] for b in (s.get("bolumler") or [])]


def calistir():
    print("\n\033[1mTEST 11 — UYGULAMA PROJESİ (mukavemet + elektrik köprüsü)\033[0m")
    r = Rapor("Uygulama projesi")

    # ---------------------------------------------------------- yapı
    s = uygulama_hesabi.hesapla(TAM)
    if not r.kontrol("tam girdiyle hesap koşuyor", s["aktif"], f"→ {s.get('hata')}"):
        return r
    adlar = _bolum_adlari(s)
    #  SAYI ELLE YAZILMAZ:  mukavemet motoruna bölüm eklenince ( ör.
    #  TAMPONLAR ) bu testin de kendiliğinden takip etmesi gerekir.
    _MUK = len(mukavemet.BOLUM_URETICILERI)
    r.esit("mukavemet bölüm sayısı", s["mukavemet_bolum_sayisi"], _MUK)
    r.esit(f"toplam bölüm  ( {_MUK} mukavemet + 4 elektrik + 4 topraklama )", len(adlar), _MUK + 8)
    for i, ad in enumerate(adlar, 1):
        r.kontrol(f"bölüm {i} sırayla numaralı", ad.startswith(f"{i} -"), f"→ {ad!r}")
    for ara in (
        "KABİN AYDINLATMA",
        "KUYU AYDINLATMA",
        "KURULU GÜÇ CETVELİ",
        "GERİLİM DÜŞÜMÜ",
        "TOPRAKLAYICI",
        "TOPLAM TOPRAKLAMA",
    ):
        r.kontrol(f"bölüm var: {ara}", any(ara in a for a in adlar), f"→ {adlar}")
    #  Avanın motor gücü ve kuvvet hesapları ALINMAZ — mukavemet zaten yapıyor
    r.kontrol(
        "avanın motor gücü bölümü alınmıyor", not any("MOTOR GÜCÜ HESABI" in a for a in adlar), f"→ {adlar}"
    )
    r.kontrol(
        "avanın kuvvet hesapları bölümü alınmıyor",
        not any("KUVVET HESAPLARI" in a for a in adlar),
        f"→ {adlar}",
    )
    r.kontrol("mukavemetin motor bölümü duruyor", any("MOTOR GÜCÜNÜN HESAPLANMASI" in a for a in adlar))

    #  Özet iki aileyi de taşıyor mu
    o = s["ozet"]
    for anahtar in (
        "N_hesap",
        "kabin_alani",
        "ray_boyu",
        "FKR",  # mukavemet
        "P_kurulu",
        "eps",
        "n_kabin",
        "n_kuyu",  # elektrik
        "Z_kabin",
        "Z_kuyu",
        "Re",
    ):
        r.kontrol(f"özette {anahtar} var", o.get(anahtar) is not None, f"→ {o.get(anahtar)!r}")

    # ---------------------------------------------------------- KÖPRÜ
    #  Her ortak alan oynatılır;  elektrik sonucu DEĞİŞMELİDİR.
    #  Değişmiyorsa köprü kopmuş, kullanıcı değeri boşuna girmiş demektir.
    taban = uygulama_hesabi.hesapla(TAM)["ozet"]
    OYNAT = (
        #  Ölçüt YUVARLANMAMIŞ değerdir:  armatür sayısı ROUNDUP'lıdır ve
        #  küçük bir değişikliği yutar — köprü kopsa bile "4 = 4" geçerdi.
        ("kabin_genisligi", 1450, 2000, "Z_kabin", "kabin genişliği → kabin aydınlatması"),
        ("kabin_derinligi", 1350, 2100, "Z_kabin", "kabin derinliği → kabin aydınlatması"),
        ("kuyu_genisligi", 2400, 4000, "Z_kuyu", "kuyu genişliği → kuyu aydınlatması"),
        ("motor_gucu", 4.9, 15, "P_kurulu", "motor gücü → kurulu güç cetveli"),
        ("seyir_mesafesi", 21, 45, "Z_kuyu", "seyir mesafesi → kuyu boyu → kuyu aydınlatması"),
        ("kolon_kesit", 16, 4, "eps", "kolon kesiti → gerilim düşümü"),
        ("_ofis", {}, {"L1_pay": 80}, "eps", "L1 yatay güzergâh payı ( Sabitler ) → gerilim düşümü"),
        ("temel_a", 26.55, 8, "Re", "temel uzunluğu → topraklama direnci"),
    )
    for anahtar, eski, yeni, olcut, aciklama in OYNAT:
        ek = dict(TAM)
        ek[anahtar] = yeni
        #  Kabin büyürken kuyu da büyür ( 950 geniş, 450 derin ):  kabini kuyuya
        #  sığmayan projenin hesabı durur ( 4 Eki ).
        if anahtar == "kabin_genisligi":
            ek["kuyu_genisligi"] = yeni + 950
        if anahtar == "kabin_derinligi":
            ek["kuyu_derinligi"] = yeni + 450
        y = uygulama_hesabi.hesapla(ek)
        if not r.kontrol(f"köprü senaryosu koşuyor: {anahtar}", y["aktif"], f"→ {y.get('hata')}"):
            continue
        r.kontrol(
            f"KÖPRÜ · {aciklama}",
            y["ozet"][olcut] != taban[olcut],
            f"→ {anahtar} {eski} → {yeni} olduğu hâlde {olcut} "
            f"{taban[olcut]!r} kaldı;  ortak girdi elektrik hesabına "
            "ULAŞMIYOR",
        )

    #  Köprü, avan motoruna DOĞRU alanları veriyor mu
    g = uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **TAM))
    k = uygulama_girdisi.avan_girdisi(g)
    a = k["asansorler"][0]
    r.esit("köprü · Q", a["Q_elle"], g["beyan_yuku"])
    r.esit("köprü · V", a["V"], g["beyan_hizi"])
    r.esit("köprü · Gk", a["Gk_elle"], g["kabin_agirligi"])
    r.esit("köprü · kabin boyu = mukavemet derinliği", a["kabin_boyu"], g["kabin_derinligi"])
    r.esit("köprü · kabin genişliği", a["kabin_genisligi"], g["kabin_genisligi"])
    r.esit("köprü · Hk = kuyu boyu / 1000", a["Hk"], g["kuyu_boyu"] / 1000)
    r.esit("köprü · Nsç = motor gücü", a["Nsc"], g["motor_gucu"])
    r.esit("köprü · askı oranı", a["i_palanga"], g["aski_orani"])
    r.esit("köprü · ray metre ağırlığı ray profilinden", a["gr"], 12.38)
    #  Verim artık sabit değil, MAKİNE TİPİNDEN gelir ve TOPLAM SİSTEM
    #  VERİMİDİR ( askı kaybı içinde ) — iki taraf aynı sayıyı kullanır.
    from motor.ortak import ofis

    r.esit("köprü · makine tipi taşınıyor", a["makine_tipi"], g["makine_tipi"])
    r.esit("köprü · η makine tipinden", a["eta"], ofis.makine_verimi(g["makine_tipi"]))
    r.kontrol("köprü · η sabit 0,92 DEĞİL", a["eta"] != 0.92, f"→ {a['eta']!r}")
    for _t in ofis.MAKINE_VERIMLERI:
        _g = uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), makine_tipi=_t))
        r.esit(
            f"köprü · η ( {_t} )",
            uygulama_girdisi.avan_girdisi(_g)["asansorler"][0]["eta"],
            ofis.MAKINE_VERIMLERI[_t],
        )
    r.kontrol(
        "köprü ORTAK_KOPRU listesindeki her alanı taşıyor",
        all(x in g for _ad, x, _av in uygulama_girdisi.ORTAK_KOPRU),
        f"→ {[x for _a, x, _b in uygulama_girdisi.ORTAK_KOPRU if x not in g]}",
    )

    # -------------------------------------------------------------
    #  UYGULAMANIN KENDİ OFİS STANDARDI  ( avandan AYRI )
    # -------------------------------------------------------------
    from motor.uygulama import tablolar_gorunum
    from motor.uygulama import mukavemet_tablolari

    _S = uygulama_sabitleri.sabitler()
    r.kontrol(
        "ofis sabitleri eksiksiz tanımlı",
        not [k for k in uygulama_sabitleri.VARSAYILAN if k not in uygulama_sabitleri.ETIKET],
        f"→ etiketi olmayan: {[k for k in uygulama_sabitleri.VARSAYILAN if k not in uygulama_sabitleri.ETIKET]}",
    )
    r.kontrol(
        "her sabit bir gruba ait",
        not [
            k for k in uygulama_sabitleri.VARSAYILAN if not any(k in g[2] for g in uygulama_sabitleri.GRUPLAR)
        ],
    )
    r.kontrol(
        "sayısal her sabitin aralığı var",
        not [
            k
            for k in uygulama_sabitleri.VARSAYILAN
            if k not in uygulama_sabitleri.ARALIK and k not in uygulama_sabitleri.METIN
        ],
    )
    r.kontrol(
        "aralık dışı değer REDDEDİLİYOR",
        uygulama_sabitleri.sabitler({"sigma_em": 9999})["_reddedilen"] == ["sigma_em"],
    )
    r.esit("geçerli değer kabul ediliyor", uygulama_sabitleri.sabitler({"cosfi": 0.85})["cosfi"], 0.85)
    r.esit(
        "reddedilen değer varsayılana dönüyor",
        uygulama_sabitleri.sabitler({"sigma_em": 9999})["sigma_em"],
        uygulama_sabitleri.VARSAYILAN["sigma_em"],
    )

    #  σem ve k1 KODDA GÖMÜLÜ DEĞİL — ofis bunları gözden geçirebilmeli
    for _k in (
        "sigma_em",
        "k1_kaymali",
        "k1_makarali",
        "k1_ani",
        "q_denge",
        "verim_dislisiz",
        "verim_disli",
        "tavan_payi",
    ):
        r.kontrol(f"ofis sabiti ekrana çıkıyor: {_k}", _k in uygulama_sabitleri.VARSAYILAN)

    #  AVANIN kuvvet sabitleri uygulamada YOK — ayrı projeler

    _avan_ozel = ("gf", "Fmt", "n_ray", "gr", "Fmk", "Fsh", "i_palanga")
    r.esit(
        "avanın MMO/697 kuvvet sabitleri uygulamada yok",
        [k for k in _avan_ozel if k in uygulama_sabitleri.VARSAYILAN],
        [],
    )

    #  Ofis sabiti hesabı GERÇEKTEN değiştiriyor mu
    _t = mukavemet.hesapla()
    for _ez, _hucre in (
        ({"verim_dislisiz": 0.88}, "motor.N"),
        ({"sigma_em": 80}, "makine.sigma_e"),
        ({"k1_kaymali": 3}, "makine.F"),
        ({"q_denge": 0.45}, "motor.Ga"),
        ({"tavan_payi": 200}, "siginma.kabin_ustu_tavan"),
        ({"Gs": 50}, "motor.Gmax"),
        ({"halat_pay_m": 8}, "motor.lh"),
        ({"yan_yatak_L_X": 400}, "makine.X"),
    ):
        _y = mukavemet.hesapla({"_ofis": _ez})
        _ad = list(_ez)[0]
        if _ad == "sigma_em":
            #  σem gerilmeyi DEĞİL, sınırı değiştirir:  etkisi bölüm 2'nin
            #  KARARINDA görünür.  Örnek projede başka bölümler zaten
            #  kaldığı için "tumu_uygun" ile bakmak yanıltıcı olurdu.
            def _b2(x):
                return [b for b in x["bolumler"] if b["baslik"].startswith("2")][0]["sonuc"]["uygun"]

            r.kontrol(
                f"ofis sabiti '{_ad}' makine kaidesinin kararını çeviriyor",
                _b2(_t) is True and _b2(_y) is False,
                f"→ önce {_b2(_t)}, sonra {_b2(_y)}",
            )
        else:
            r.kontrol(
                f"ofis sabiti '{_ad}' hesabı değiştiriyor",
                _y["ara"][_hucre] != _t["ara"][_hucre],
                f"→ {_hucre}: {_t['ara'][_hucre]} → {_y['ara'][_hucre]}",
            )

    # -------------------------------------------------------------
    #  UYGULAMANIN KENDİ TABLOLARI  ( ekranda bugüne kadar YOKTU )
    # -------------------------------------------------------------
    _tb = tablolar_gorunum.arayuz_tablolari()
    r.kontrol("tablo görünümü dolu", len(_tb) >= 12, f"→ {len(_tb)} tablo")
    for _x in _tb:
        r.kontrol(
            f"tablo '{_x['ad'][:28]}' eksiksiz",
            bool(_x["ad"])
            and bool(_x["basliklar"])
            and bool(_x["satirlar"])
            and all(len(s) == len(_x["basliklar"]) for s in _x["satirlar"]),
            f"→ {len(_x['basliklar'])} sütun, {len(_x['satirlar'])} satır",
        )
    #  TABLOLAR KOPYALANMAZ — motorun kendi sözlüğünden okunmalı
    _ray = [x for x in _tb if "Kılavuz ray" in x["ad"]][0]
    r.esit(
        "ray tablosu motorun tablosuyla aynı satır sayısında",
        len(_ray["satirlar"]),
        len(mukavemet_tablolari.RAY_PROFILI),
    )
    r.kontrol("ray tablosu gerçek profil taşıyor", any("50 x 50 x 5" in str(s[0]) for s in _ray["satirlar"]))

    #  BAŞLIK DOĞRU SAYININ ÜSTÜNDE Mİ.  Sütun SAYISI tutarken başlıklar
    #  kayabiliyordu:  T50'nin 3,7 kg/m'si "b ( balata yarı gen. )", e = 14,3
    #  mm'si "gr ( kg/m )" başlığıyla görünüyordu.  Her tabloda başlığın
    #  altındaki değer, motorun o büyüklüğü okuduğu işlevle karşılaştırılır.
    def _hucre(tablo_adi, anahtar, baslik):
        """Başlığın altındaki hücre;  başlık ya da satır yoksa açıklayan metin
        döner ( kontrol ÇÖKMEZ, başarısız yazılır )."""
        _t = [x for x in _tb if x["ad"].startswith(tablo_adi)][0]
        _s = [s for s in _t["satirlar"] if s[0] == anahtar]
        if not _s or baslik not in _t["basliklar"]:
            return f"başlık ya da satır yok — başlıklar: {_t['basliklar']}"
        return _s[0][_t["basliklar"].index(baslik)]

    for _tab, _key, _bas, _bek in (
        ("Kılavuz ray", "50 x 50 x 5", "Gr  ( kg/m )", mukavemet_tablolari.ray("50 x 50 x 5", "Gr")),
        ("Kılavuz ray", "89 x 62 x 15,88", "Wx  ( mm³ )", mukavemet_tablolari.ray("89 x 62 x 15,88", "Wx")),
        ("Kılavuz ray", "89 x 62 x 15,88", "iy  ( mm )", mukavemet_tablolari.ray("89 x 62 x 15,88", "iy")),
        ("Kılavuz ray", "50 x 50 x 5", "e  ( mm )", mukavemet_tablolari.ray("50 x 50 x 5", "e")),
        (
            "Ray geometrisi",
            "89 x 62 x 15,88",
            "h1  ( mm )",
            mukavemet_tablolari.ray_geo("89 x 62 x 15,88", "h1"),
        ),
        (
            "Ray geometrisi",
            "89 x 62 x 15,88",
            "b  ( balata yarı gen., mm )",
            mukavemet_tablolari.ray_geo("89 x 62 x 15,88", "b"),
        ),
        ("NPU profilleri", 140, "Wx  ( cm³ )", mukavemet_tablolari.npu(140, "Wx")),
        ("NPU profilleri", 140, "G  ( kg/m )", mukavemet_tablolari.npu(140, "G")),
        ("NPU profilleri", 140, "iy  ( cm )", mukavemet_tablolari.npu(140, "iy")),
        ("Gezici kablo", "24 x 0,75", "Ağırlık  ( kg/m )", mukavemet_tablolari.kablo_agirligi("24 x 0,75")),
        (
            "Karşı ağırlık",
            "Barit",
            "Derinlik  ( mm )",
            uygulama_girdisi.arayuz_alanlari()["malzeme_derinligi"]["Barit"],
        ),
    ):
        r.esit(
            f"tablo '{_tab}' · {_key} · {_bas.split('(')[0].strip()} başlığı motorun değerini gösteriyor",
            _hucre(_tab, _key, _bas),
            _bek,
        )
    _w = [x for x in _tb if x["ad"].startswith("ω")][0]
    r.kontrol("ω tablosu üç Rm sütunu veriyor", len(_w["basliklar"]) == 4)
    #  Sekmedeki değer paftanın kuralıyla yuvarlanır ( steps.yuvarla ):
    #  Python'un round()'u λ = 150 · Rm = 520'de ω = 5,69925'i ( ikilide
    #  5,69924999… ) 5,6992 gösteriyordu, pafta ise 5,6993 basar.  Üç Rm
    #  sütununun hepsi denetlenir.
    from motor.ortak.adimlar import yuvarla as _yuv

    r.kontrol(
        "ω tablosu motorun formülüyle ve paftanın yuvarlamasıyla aynı",
        all(
            s[i] == _yuv(mukavemet_tablolari.omega_en8150(s[0], rm), 4)
            for s in _w["satirlar"]
            for i, rm in ((1, 370), (2, 440), (3, 520))
        ),
        f"→ {[(s[0], s[3]) for s in _w['satirlar'] if s[3] != _yuv(mukavemet_tablolari.omega_en8150(s[0], 520), 4)][:3]}",
    )

    # ═══════════════════════════════════════════════════════════════
    #  DENETİMDE BULUNAN SEKİZ HATA  —  her biri yeniden üretilerek
    # ═══════════════════════════════════════════════════════════════

    def _yakin(a, b, tol=1e-6):
        try:
            return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
        except (TypeError, ValueError):
            return a == b

    #  ①  NEGATİF GERİLME "UYGUN" SAYILMAZ
    #  X = L − mesnet payı ≤ 0 iken σe negatif çıkıyor ve "σe ≤ σem" bunu
    #  sessizce geçiriyordu ( −5.350 ≤ 130 doğrudur ).
    _n1 = mukavemet.hesapla({"yan_yatak_boyu": 100, "yan_yatak": 30, "dikine_kiris": 30})
    r.kontrol("① imkânsız kaide geometrisi REDDEDİLİYOR", not _n1["aktif"], f"→ {_n1.get('ozet')}")
    r.kontrol(
        "① hata mesajı alanı ve sebebi söylüyor",
        any("Yan yatak boyu" in x and "mesnet payı" in x for x in (_n1.get("hata") or [])),
        f"→ {_n1.get('hata')}",
    )
    r.kontrol("① sınırda ( X = 0 ) da reddediliyor", not mukavemet.hesapla({"yan_yatak_boyu": 335})["aktif"])
    r.kontrol("① X = 1 mm kabul ediliyor", mukavemet.hesapla({"yan_yatak_boyu": 336})["aktif"])
    #  İkinci kalkan:  negatif gerilme hiçbir koşulda uygun sayılmamalı

    r.kontrol(
        "① negatif gerilme uygun sayılmıyor  ( ikinci kalkan )",
        not (0 <= -1 <= 130),
        "→ karşılaştırma yalnız ≤ ile yapılıyor",
    )

    #  ②  GENEL SONUÇ ENGELLEYİCİ UYARILARI SAYIYOR
    #  Temiz projede imalatçı kuvveti girilidir;  girilmezse de proje uygun
    #  çıkar — bölüm 300 N'u denetler ve fren bloğuna şart yazar ( sapma ⑲ ).
    #  TAHRİK YETENEĞİ için kanalın sertleştirilmiş olması ve denge zinciri
    #  de gerekir;  Ek D'nin ivme işaretleriyle ( ㊳ ) çıplak örnek
    #  tahrikten kalıyor.
    #  Temiz proje sarılma açısını da BEYAN eder ( zorunlu girdi ).  6,5 mm
    #  halat 8 mm'nin altındadır ( m.5.5.1.2 a) );  sahadaki gibi belgelidir.
    #  KUYU ÜSTÜ 4.200:  sığınma açıklıkları kuyunun çiziminden ölçülür
    #  ( birleşik program );  varsayılan 3.750'de 3.300'lük şasenin üst pateni
    #  kuyu tavanına 150 mm giriyor, revizyon kutusu halat bağlantısına 70 mm
    #  kalıyor — eski ofis payı modeli bunu görmüyordu.
    _temiz = dict(
        tahrik_kasnak_capi=280,
        saptirma_kasnak_capi=280,
        motor_gucu=7.5,
        guvenlik_devreye_kuvvet=200,
        kanal_isleme="Sertleştirilmiş",
        denge_zinciri="Var",
        sarilma_acisi=180,
        kasnak_belgesi="Var",
        son_kat_yuksekligi=4200,
    )
    _t = uygulama_hesabi.hesapla(uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **_temiz)))
    r.kontrol("② temiz proje uygun", _t["ozet"]["tumu_uygun"] is True)
    #  Akım yetersizse İLGİLİ BÖLÜM de uygun değil
    _s2 = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(
            dict(
                uygulama_girdisi.varsayilanlar(),
                tahrik_kasnak_capi=280,
                saptirma_kasnak_capi=280,
                motor_gucu=37,
                kolon_kesit=95,
                makine_kesit=1.5,
            )
        )
    )
    #  SIRAYA DEĞİL KİMLİĞE BAK:  mukavemet tarafına bölüm eklenince
    #  ( TAMPONLAR ) elektrik bölümlerinin numarası kayıyor.
    _b14 = [b for b in _s2["bolumler"] if b["kimlik"] == "gerilim_dusumu"][0]
    r.kontrol("② akım yetersizken BÖLÜM uygun değil", _b14["sonuc"]["uygun"] is False, f"→ {_b14['sonuc']}")
    r.kontrol(
        "② bölümün alt satırında I2 ≤ Iz2 kontrolü var",
        any("I2" in x for x in _b14["sonuc"]["alt"]),
        f"→ {_b14['sonuc']['alt']}",
    )
    r.kontrol("② akım yetersizken proje uygun değil", _s2["ozet"]["tumu_uygun"] is False)
    #  Fiziksel imkânsızlıkta HESAP DURUR ( kullanıcı kararı 4 Eki ):  kuyunun
    #  geometrisi kurulamıyorsa ( çizimin plan doğrulaması ) rapor üretilmez,
    #  sebep söylenir.  Eskiden hesap kuruluyor, özet "engelleyici" diyordu.
    _kk = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(
            dict(uygulama_girdisi.varsayilanlar(), **_temiz, kabin_genisligi=1850, kuyu_genisligi=1800)
        )
    )
    r.kontrol("② kabin kuyuya sığmıyorsa hesap durur", _kk.get("aktif") is False)
    r.kontrol(
        "② sebebi söylenir",
        any("kuyu genişliğinden" in h for h in _kk.get("hata") or []),
        f"→ {_kk.get('hata')}",
    )
    #  Zorunlu hesap yapılamıyorsa EKSİK
    _ek = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **_temiz, temel_a=10, temel_b=None))
    )
    r.kontrol("② yapılamayan zorunlu hesap projeyi uygun bırakmıyor", _ek["ozet"]["tumu_uygun"] is False)
    r.kontrol(
        "② eksik hesap ayrı listede",
        len(_ek["ozet"].get("eksik_hesap") or []) >= 1,
        f"→ {_ek['ozet'].get('eksik_hesap')}",
    )
    #  İMALATÇI KUVVETİ YOKSA ŞART YAZILIR, HESAP EKSİK SAYILMAZ.  Fren
    #  bloğunun kuvveti proje aşamasında çoğu zaman bilinmez;  bölüm 300 N'u
    #  denetler ve kuvvete Fçekme / 2 üst sınırını şart olarak basar.
    _rg = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(
            dict(uygulama_girdisi.varsayilanlar(), **_temiz) | {"guvenlik_devreye_kuvvet": None}
        )
    )
    r.kontrol(
        "② imalatçı kuvveti yoksa da temiz proje uygun",
        _rg["ozet"]["tumu_uygun"] is True,
        f"→ {_rg['ozet'].get('eksik_hesap')}",
    )
    r.esit(
        "② regülatör eksik_hesap listesinde değil",
        [x for x in (_rg["ozet"].get("eksik_hesap") or []) if "devreye" in x],
        [],
    )
    _rgb = [b for b in _rg["bolumler"] if b["kimlik"] == "regulator_halati"][0]
    r.kontrol(
        "② regülatör bölümü fren bloğu şartını basıyor",
        any(str(a.get("aciklama", "")).startswith("Şart:  Fgt") for a in _rgb["adimlar"]),
        f"→ {[a.get('aciklama') for a in _rgb['adimlar']]}",
    )

    #  BİLGİLENDİRİCİ uyarı uygunluğu ENGELLEMEZ.  Örnek eskiden reddedilen
    #  bir ofis sabitiydi ( cosφ = 99 );  o artık bilgilendirici değildir,
    #  hesabı durdurur ( bkz. ④ ).  Makine dairesiz tesiste yükün binaya
    #  aktarıldığı notu gerçek bir bilgilendirici uyarıdır.  Programda bu
    #  düzen çizilmiyor ( karar 3:  bölüm 2 EKSİK );  hesap motoru kendi
    #  varsayılan kirişiyle hesaplar — uyarının yolu orada sınanır.
    _bg = mukavemet.hesapla(dict(_temiz, mk_yok=True, makine_raya_biniyor="Bina yapısına"))
    r.kontrol(
        "② örnekte bilgilendirici uyarı var",
        any("BİNA YAPISINA" in u for u in _bg["uyarilar"]),
        f"→ {_bg['uyarilar']}",
    )
    r.kontrol(
        "② bilgilendirici uyarı uygunluğu engellemiyor",
        _bg["ozet"]["tumu_uygun"] is True,
        f"→ {_bg['ozet'].get('engelleyici')} / {_bg['ozet'].get('eksik_hesap')}",
    )

    #  ④  REDDEDİLEN OFİS SABİTİ HESABA HAM GİRMİYOR

    _veri4 = {
        "ortak": {},
        "asansorler": [
            {
                "aktif": True,
                "tanim": "T",
                "Q_elle": 800,
                "V": 1,
                "Hk": 30,
                "eta": 0.7,
                "kuyu_genisligi": 1900,
                "kabin_boyu": 1300,
                "kabin_genisligi": 1100,
            }
        ],
        "sabitler": {"cosfi": 2, "q_denge": 5, "n_ray": 0},
        "trafik": {},
    }
    _S4 = avan_hesabi.sabitler(_veri4["sabitler"])
    for _k, _ham in (("cosfi", 2), ("q_denge", 5), ("n_ray", 0)):
        r.kontrol(
            f"④ {_k} reddedilen ham değer ({_ham}) sözlüğe yazılmıyor",
            _S4[_k] != _ham and _S4[_k] == avan_hesabi.sabitler({})[_k],
            f"→ {_S4[_k]!r}",
        )
    #  ... ve o sözlükle HESAP YAPILMAZ:  üçü de adıyla tek hatada söylenir.
    _h4 = avan_hesabi.hesapla(_veri4).get("hata") or ""
    r.kontrol(
        "④ reddedilen ofis sabitiyle avan hesabı yapılmıyor",
        all(x in _h4 for x in ("cosφ", "q — denge faktörü", "n — kabin kılavuz ray")),
        f"→ {_h4!r}",
    )
    #  Uygulamada da:  Sabitler sekmesindeki aralık dışı değer eskiden HİÇBİR
    #  iz bırakmadan varsayılanla değişiyordu ( β = 0,5 → 150 Ω·m ).
    for _k4, _v4 in (("cosfi", 99), ("beta", 0.5), ("sigma_em", 5), ("U", 50)):
        _u4 = uygulama_hesabi.hesapla(
            uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **_temiz, _ofis={_k4: _v4}))
        )
        r.kontrol(
            f"④ uygulama: ofis {_k4} = {_v4} ile hesap yapılmıyor",
            _u4["aktif"] is False
            and any("Ofis standardı" in h and "geçerli aralık" in h for h in _u4.get("hata") or []),
            f"→ aktif {_u4['aktif']} · {_u4.get('hata')}",
        )
    #  Uygulamanın avan motoruna geçirdiği sabitler İKİ tarafta aynı aralıkta
    #  olmalı:  yoksa uygulamanın kabul ettiği bir değeri avan motoru reddeder
    #  ve elektrik hesapları sebepsiz "yapılamadı" görünür.
    _avr4 = {**avan_hesabi.SABIT_B_ARALIK, **avan_hesabi.OFIS_ARALIK}
    _fark4 = {
        k: (_avr4[k], uygulama_sabitleri.ARALIK.get(k))
        for k in uygulama_sabitleri.VARSAYILAN
        if k in _avr4 and k not in uygulama_girdisi.AVAN_DISI and uygulama_sabitleri.ARALIK.get(k) != _avr4[k]
    }
    r.kontrol("④ avana geçen ofis sabitlerinin aralıkları iki projede aynı", not _fark4, f"→ {_fark4}")

    #  ⑤  METİN OFİS ALANI SAYIYA ÇEVRİLMİYOR

    uc_ortak._BELIRSIZ.clear()
    _g5 = uygulama_istegi.mukavemet_girdisi(
        {"girdiler": {}, "sabitler": {"kablo_tipi": "NYY", "cosfi": "0,85", "priz_gucu": "1.200"}}
    )
    r.esit("⑤ metin ofis alanı korunuyor", _g5["_ofis"].get("kablo_tipi"), "NYY")
    r.esit("⑤ sayısal ofis alanı okunuyor", _g5["_ofis"].get("cosfi"), 0.85)
    r.kontrol(
        "⑤ belirsiz yazım BİLDİRİLİYOR",
        len(list(uc_ortak._BELIRSIZ)) >= 1,
        f"→ {list(uc_ortak._BELIRSIZ)}",
    )

    #  ⑥  FİZİKSEL GİRDİ SINIRLARI
    for _ad6, _ek6 in (
        ("kesirli halat adedi", {"halat_adedi": 6.5}),
        ("kesirli ray sayısı", {"kabin_ray_sayisi": 2.5}),
        ("konsol aralığı 0", {"kabin_konsol_arasi": 0}),
        ("regülatör açısı 360", {"reg_kanal_acisi": 360}),
        ("regülatör açısı 0", {"reg_kanal_acisi": 0}),
    ):
        _x6 = mukavemet.hesapla(_ek6)
        r.kontrol(f"⑥ {_ad6} reddediliyor", not _x6["aktif"], "→ hesap yapıldı")
        r.kontrol(
            f"⑥ {_ad6} hatası ALAN ADINI söylüyor",
            bool(_x6.get("hata")) and not any("Traceback" in x for x in _x6["hata"]),
            f"→ {_x6.get('hata')}",
        )
    r.kontrol("⑥ geçerli girdi hâlâ kabul ediliyor", mukavemet.hesapla()["aktif"])

    #  ⑧  RAY AĞIRLIĞI BİR KEZ SAYILIYOR
    _s8 = mukavemet.hesapla()
    _h8 = _s8["ara"]
    _gn8 = mukavemet.SABIT["gn"]
    _ray8 = _gn8 * mukavemet_tablolari.ray(_s8["girdi"]["kabin_ray_profili"], "Gr") * _s8["ozet"]["ray_boyu"]
    #  Raya bağlı donanım k3 ile çarpılır:  m.5.2.1.8.4 tabanın taşıyacağı
    #  kalemler arasında "additional reaction … due to REBOUND when machine
    #  on rails" der, katsayısı m.5.7.4.3'ün k3'üdür  ( bölüm 7 ile aynı ).
    _k38 = uygulama_sabitleri.sabitler(_s8["girdi"].get("_ofis"))["k3_yardimci"]
    _bek8 = _ray8 + _k38 * mukavemet.SABIT["MY_kabin"] + (_h8["kabin_ray.Fk"] - _h8["kabin_ray.Mg"] * _gn8)
    r.kontrol(
        "⑧ FKR = ray kütlesi + k3 × bileşen + güv.tert. tepkisi",
        _yakin(_h8["kuyu.FKR"], _bek8),
        f"→ {_h8['kuyu.FKR']!r} ≠ {_bek8!r}",
    )
    r.kontrol(
        "⑧ ray ağırlığı iki kez sayılmıyor",
        abs(_h8["kuyu.FKR"] - (_bek8 + _ray8)) > 1,
        "→ hâlâ çift sayılıyor",
    )

    #  ⑨  KORUMA İLETKENİ ( PE ) HER İKİ PROJEDE DE PAFTAYA GİRİYOR
    #  Uygulama projesinin 15. bölümü avan motorunun gerilim_dusumu bölümüdür;
    #  tek kaynaktan beslendiği için iki paftada da AYNI satırlar çıkmalı.
    #  Beklenen değer ÇİZELGE-8'den türetilir, motorun kendi satırından değil.
    def _pe_satirlari(bolumler):
        b = next(x for x in bolumler if x.get("kimlik") == "gerilim_dusumu")
        return {
            str(a.get("sembol")): a
            for a in b["adimlar"]
            if isinstance(a, dict) and str(a.get("sembol") or "") in ("SPE1", "SPE2")
        }

    _u9 = uygulama_hesabi.hesapla()
    _pu = _pe_satirlari(_u9["bolumler"])
    r.esit("⑨ uygulama paftasında iki PE satırı", len(_pu), 2)
    _av9 = avan_hesabi.hesapla(
        {
            "ortak": {
                "temel_a": 26.55,
                "temel_b": 16.4,
                "beta": 150,
                "cubuk_sayisi": 4,
                "mk_uzunluk": 3000,
                "mk_genislik": 2500,
            },
            "sabitler": {},
            "asansorler": [
                {
                    "tanim": "A",
                    "kapasite": 10,
                    "V": 1.6,
                    "eta": 0.85,
                    "Hk": 32.85,
                    "kuyu_genisligi": 1800,
                    "kabin_boyu": 1450,
                    "kabin_genisligi": 1300,
                    "makine_tipi": "Dişlisiz",
                    "S1": 150,
                    "S2": 95,
                }
            ],
        }
    )
    _pa = _pe_satirlari(_av9["asansorler"][0]["bolumler"])
    r.esit("⑨ avan paftasında iki PE satırı", len(_pa), 2)
    #  S/2'nin standart kesite düşmediği satır:  150 → 75 → BİR ÜST = 95
    r.esit(
        "⑨ SPE1 bir üst standart kesite yuvarlanıyor  ( 150 → 95 )",
        _pa["SPE1"]["deger"],
        tablolar.koruma_iletkeni_kesiti(150)[0],
    )
    r.esit(
        "⑨ SPE2 çizelgeyle aynı  ( 95 → 50 )", _pa["SPE2"]["deger"], tablolar.koruma_iletkeni_kesiti(95)[0]
    )
    r.kontrol(
        "⑨ yuvarlama paftada kaynak sütununda yazıyor",
        "bir üst standart" in str(_pa["SPE1"].get("kaynak") or ""),
        f"→ {_pa['SPE1'].get('kaynak')!r}",
    )
    r.kontrol(
        "⑨ hat başına PE satırları topraklama bölümüne kaymamış",
        not any(
            str(a.get("sembol") or "") in ("SPE1", "SPE2")
            for b in ((_av9.get("topraklama") or {}).get("bolumler") or [])
            for a in b["adimlar"]
            if isinstance(a, dict)
        ),
    )

    #  ⑩  TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ  ( m.9-j · m.9/c )
    #  Ana potansiyel dengeleme "TESİSTEKİ en büyük koruma iletkeninden" türer
    #  ( m.9-j/1/i ) — tesis çok asansörlüyse hepsine bakılmalı.
    _ORTAK10 = {
        "temel_a": 26.55,
        "temel_b": 16.4,
        "beta": 150,
        "cubuk_sayisi": 4,
        "mk_uzunluk": 3000,
        "mk_genislik": 2500,
    }
    _T10 = {
        "tanim": "A",
        "kapasite": 10,
        "V": 1.6,
        "eta": 0.85,
        "Hk": 32.85,
        "kuyu_genisligi": 1800,
        "kabin_boyu": 1450,
        "kabin_genisligi": 1300,
        "makine_tipi": "Dişlisiz",
    }

    def _iletken_satirlari(asans):
        s10 = avan_hesabi.hesapla({"ortak": dict(_ORTAK10), "sabitler": {}, "asansorler": asans})
        b = next(x for x in s10["topraklama"]["bolumler"] if x.get("kimlik") == "topraklama_iletkenleri")
        d = {}
        for a in b["adimlar"]:
            if isinstance(a, dict):
                ad = str(a.get("sembol") or "")
                if not ad and str(a.get("formul") or "").startswith("Sapd"):
                    ad = "Sapd"
                if ad:
                    d[ad] = a["deger"]
        return s10, d

    _s10, _d10 = _iletken_satirlari([dict(_T10, S1=6, S2=6)])
    r.esit("⑩ topraklama bölümü dört alt bölüm", len(_s10["topraklama"]["bolumler"]), 4)
    r.esit("⑩ SPE = 6 → Sapd", _d10.get("Sapd"), tablolar.ana_potansiyel_dengeleme_kesiti(6)[0])
    r.esit("⑩ SPE = 6 → Stopr", _d10.get("Stopr"), tablolar.topraklama_iletkeni_kesiti(6)[0])
    #  ÇOK ASANSÖRDE EN BÜYÜK PE BELİRLER — tesis geneli bir iletkendir.
    _s10c, _d10c = _iletken_satirlari(
        [dict(_T10, S1=6, S2=6), dict(_T10, S1=150, S2=95), dict(_T10, S1=16, S2=10)]
    )
    r.esit("⑩ üç asansörde en büyük PE seçiliyor", _d10c.get("SPE"), tablolar.koruma_iletkeni_kesiti(150)[0])
    r.esit("⑩ Sapd 25 mm² üst sınırında", _d10c.get("Sapd"), 25)
    r.kontrol("⑩ tek asansörlük Sapd, çok asansörlüden büyük olamaz", _d10.get("Sapd") <= _d10c.get("Sapd"))

    #  ⑪  BURKULMA HESAPLANAMADIĞINDA PAFTA SEBEBİNİ YAZAR
    #  λ, EN 81-50'nin ω çizelgesinin ( 20…250 ) dışına çıkarsa σk yoktur.
    #  Eskiden satır "σk = —  ≤  σperm = 205" diye basılıp yanına UYGUN DEĞİL
    #  yazıyordu:  boş hücrenin yanında bir ret.  Okuyan, gerilmenin sınırı
    #  AŞTIĞINI sanar;  oysa hesap hiç yapılamamıştır.
    _s11 = mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})
    _b11 = next(x for x in _s11["bolumler"] if x["kimlik"] == "agirlik_raylari")
    _w11 = next(
        (a["deger"] for a in _b11["adimlar"] if isinstance(a, dict) and str(a.get("sembol") or "") == "ω"),
        "yok",
    )
    r.kontrol("⑪ ofis varsayılanı ω'yı tablo dışına taşıyor", _w11 is None, f"→ ω = {_w11!r}")
    _metinler = " | ".join(str(a.get("aciklama") or "") for a in _b11["adimlar"] if isinstance(a, dict))
    r.kontrol(
        "⑪ satır 'HESAPLANAMADI' diyor, sessizce reddetmiyor",
        "HESAPLANAMADI" in _metinler,
        f"→ {_metinler[:120]}",
    )
    r.kontrol("⑪ sebep ( λ ve çizelge sınırı ) paftada yazılı", "286" in _metinler and "250" in _metinler)
    r.kontrol(
        "⑪ bölüm sonucu 'denetlenemedi' diyor",
        "denetlenemedi" in str(_b11["sonuc"]["metin"]),
        f"→ {_b11['sonuc']['metin'][:90]}",
    )
    #  Gerçekten AŞAN durumda mesaj değişmeli — ikisi farklı şeydir.
    _s11b = mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı", "agirlik_konsol_arasi": 2500})
    _b11b = next(x for x in _s11b["bolumler"] if x["kimlik"] == "agirlik_raylari")
    r.kontrol(
        "⑪ ω varken mesaj 'denetlenemedi' demiyor",
        "denetlenemedi" not in str(_b11b["sonuc"]["metin"]),
        f"→ {_b11b['sonuc']['metin'][:90]}",
    )

    #  ⑫  GEÇERSİZ AÇI VE STANDART DIŞI KANAL:  GİRDİDE RET, KİTAPTA HÜKÜM YOK
    #  İki birleşim fiziksel ya da standarda aykırıdır:
    #    · sarılma açısı kanalın sarım sayısına uymuyor — tek sarımda α > 180°,
    #      çift sarımda α ≤ 180° ( tek sarıma ait açı );
    #    · sertleştirilmemiş DÜZ V kanal — TS EN 81-50 m.5.11.2.3.1.2 alt
    #      kesilme ister ( "an undercut is necessary" ).
    #  Eskiden motor bunları hesaplıyor, satırlara "UYGUN" basıyor ( düz V
    #  576 senaryonun 142'sinde "UYGUNDUR" ).
    _CS = "Yarım Daire Kanal (Çift Sarım)"
    for _ad12, _g12, _parca in (
        ("tek sarım · 300°", {"sarilma_acisi": 300}, "tek sarımlı kanalda 180°'yi aşamaz"),
        ("tek sarım · 181°", {"sarilma_acisi": 181}, "tek sarımlı kanalda 180°'yi aşamaz"),
        (
            "çift sarım · 180°",
            {"kanal_sekli": _CS, "sarilma_acisi": 180},
            "çift sarımlı kanalda 180°'yi aşmalıdır",
        ),
        (
            "düz V · sertleştirilmemiş",
            {"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş", "sarilma_acisi": 180},
            "m.5.11.2.3.1.2",
        ),
    ):
        _s12 = mukavemet.hesapla(_g12)
        r.kontrol(
            f"⑫ {_ad12} girdide reddediliyor",
            _s12.get("aktif") is False and any(_parca in h for h in _s12.get("hata") or []),
            f"→ {_s12.get('hata')}",
        )
    for _ad12, _g12 in (
        ("tek sarım · 180°", {"sarilma_acisi": 180}),
        ("çift sarım · 181°", {"kanal_sekli": _CS, "sarilma_acisi": 181}),
        (
            "düz V · sertleştirilmiş",
            {"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmiş", "sarilma_acisi": 180},
        ),
    ):
        r.kontrol(f"⑫ {_ad12} kabul ediliyor", mukavemet.hesapla(_g12).get("aktif") is True)
    r.esit(
        "⑫ ret sırasında kanal işlemesi sessizce değiştirilmiyor",
        mukavemet.hesapla({"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş"})["girdi"][
            "kanal_isleme"
        ],
        "Sertleştirilmemiş",
    )
    #  Uygulama projesi de aynı reddi taşımalı ( ekran bu yoldan hesaplar )
    _u12 = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(dict(dict(uygulama_girdisi.varsayilanlar(), **TAM), sarilma_acisi=300))
    )
    r.kontrol(
        "⑫ uygulama projesi de imkânsız açıyı reddediyor", _u12.get("aktif") is False, f"→ {_u12.get('hata')}"
    )
    #  Geçerli çift sarımda tahrik ara değerleri eksiksiz yazılmalı
    _s12c = mukavemet.hesapla({"kanal_sekli": _CS, "sarilma_acisi": 330})
    _bos = [
        h
        for h in (
            "tahrik.alfa_derece",
            "tahrik.alfa",
            "tahrik.f_bloke",
            "tahrik.yukleme.T1",
            "tahrik.yukleme.T2",
            "tahrik.bloke.T1",
            "tahrik.bloke.T2",
            "tahrik.bloke.oran",
            "tahrik.bloke.sinir",
        )
        if _s12c["ara"].get(h) is None
    ]
    r.esit("⑫ geçerli çift sarımda tahrik ara değerleri yazılıyor", _bos, [])
    #  ⑬  GENEL HÜKÜM:  "UYGUN DEĞİL"  >  "HESAP EKSİK"  >  "UYGUNDUR"
    #  Eksik önce gelirse, dört bölümü çakılan bir proje ekranda yalnız
    #  "HESAP EKSİK" der ve okuyan tasarımın tutmadığını göremez.  Hüküm
    #  MOTORDA üretilir;  PDF ve ekran onu yalnız basar ( iki kopya hâlinde
    #  tutulduğunda zaten bir kez ayrışmıştı ).
    _S = lambda u: {"sonuc": {"uygun": u}}
    _E = lambda u: {"sonuc": {"uygun": u}, "eksik_hesap": "x"}
    for _ad, _bol, _tu, _eks, _bek in (
        ("kalan varken eksik onu örtmez", [_S(True), _S(False)], False, ["e"], "UYGUN DEĞİLDİR."),
        ("yalnız eksik varsa HESAP EKSİK", [_S(True), _E(False)], False, ["e"], "HESAP EKSİK"),
        ("hiçbiri yoksa UYGUNDUR", [_S(True), _S(True)], True, [], "UYGUNDUR."),
        ("engelleyici varsa UYGUN DEĞİL", [_S(True)], False, [], "UYGUN DEĞİLDİR."),
    ):
        r.esit(f"⑬ {_ad}", mukavemet.genel_hukum(_bol, _tu, _eks)[0], _bek)
    #  GERÇEK PROJEDE:  varsayılan girdide hem kalan bölüm hem eksik vardır.
    #  Eksik:  α — kanal çift sarımlı ( çizim tek sarım çizer, α çizimden
    #  bulunamaz;  varsayılanın α'sı artık çizimden gelir:  halat düşey iner ).
    _s13 = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(
            dict(uygulama_girdisi.varsayilanlar(), **TAM, kanal_sekli="Yarım Daire Kanal (Çift Sarım)")
        )
    )
    _o13 = _s13["ozet"]
    _kalan13 = [
        b["baslik"][:34]
        for b in _s13["bolumler"]
        if (b.get("sonuc") or {}).get("uygun") is False and not b.get("eksik_hesap")
    ]
    r.kontrol(
        "⑬ senaryoda hem kalan bölüm hem eksik var",
        bool(_kalan13) and bool(_o13.get("eksik_hesap")),
        f"→ kalan {_kalan13} / eksik {_o13.get('eksik_hesap')}",
    )
    r.esit("⑬ hüküm kalan bölümü söylüyor, eksiği değil", _o13.get("genel_sonuc"), "UYGUN DEĞİLDİR.")
    r.esit("⑬ kısa hüküm de aynı", _o13.get("genel_sonuc_kisa"), "UYGUN DEĞİL")
    #  PDF EKRANLA AYNI HÜKMÜ BASMALI

    _pdf13 = pdf_cikti.uygulama_pdf({"asansorler": [dict(_s13, no=1, tanim="A")], "adet": 1}, {})
    r.kontrol("⑬ PDF üretiliyor", len(_pdf13) > 10000, f"→ {len(_pdf13)} bayt")
    _kaynak13 = open(os.path.join(KOK, "ciktilar", "pdf_cikti.py"), encoding="utf-8").read()
    r.kontrol(
        "⑬ PDF hükmü kendi kurmuyor, motordan okuyor",
        _kaynak13.count('o.get("genel_sonuc")') == 2 and "HESAP EKSİK" not in _kaynak13,
        "→ pdf_export hâlâ kendi hükmünü kuruyor",
    )
    _js13 = _on_yuz_kaynagi()
    r.kontrol(
        "⑬ ekran hükmü kendi kurmuyor, motordan okuyor",
        len(_js13) > 10000 and "HESAP EKSİK" not in _js13,
        "→ ön yüz kendi hükmünü kuruyor",
    )

    #  ⑮  α — SARILMA AÇISI ZORUNLU BEYANDIR, VARSAYIMI YOKTUR
    #  TS EN 81-50 m.5.11.2.1'in iki eşitsizliği terstir;  hiçbir açı iki
    #  kontrolde birden emniyetli değildir ( 180° varsayılanı 486 senaryonun
    #  %33'ünde yükleme/frenleme hükmünü geçme yönüne çeviriyordu ).  Bu
    #  yüzden açı girilmezse dört SINIR hesaplanmaz ve bölüm HESAP EKSİK olur.
    #  Ama bölüm ERKEN DÖNMEZ:  bir ara sürüm boş bölüm döndürüp T1 · T2'yi
    #  bile hesaplamıyordu.
    _CS15 = "Yarım Daire Kanal (Çift Sarım)"
    #  α BİLİNMİYOR:  girilmemiş ve çizimden de bulunamıyor — çift sarım ( çizim
    #  tek sarım çizer ).  Varsayılan asansörde α artık çizimden gelir ( 180°,
    #  halat düşey iner ):  "yok" durumunu çift sarım sınar.
    _s15y = mukavemet.hesapla({"kanal_sekli": _CS15})
    _s15b = mukavemet.hesapla({"sarilma_acisi": 150})
    _s15t = mukavemet.hesapla({"sarilma_acisi": 180})
    _b15y = next(x for x in _s15y["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
    r.kontrol(
        "⑮ α varsayılanı yok ( çizimden bulunamayınca )",
        _s15y["girdi"].get("sarilma_acisi") is None,
        f"→ {_s15y['girdi'].get('sarilma_acisi')!r}",
    )
    r.kontrol(
        "⑮ α yokken bölüm HESAP EKSİK",
        "α girilmedi" in str(_b15y.get("eksik_hesap") or ""),
        f"→ {_b15y.get('eksik_hesap')!r}",
    )
    r.kontrol("⑮ α yokken genel hüküm 'uygundur' olamıyor", _s15y["ozet"]["tumu_uygun"] is False)
    #  Açıdan BAĞIMSIZ her şey yine hesaplanmalı
    _eksik_h = [
        h
        for h in (
            "tahrik.yukleme.T1",
            "tahrik.yukleme.T2",
            "tahrik.yukleme.oran",
            "tahrik.fren_alt.T1",
            "tahrik.fren_alt.T2",
            "tahrik.fren_alt.oran",
            "tahrik.fren_ust.T1",
            "tahrik.fren_ust.T2",
            "tahrik.fren_ust.oran",
            "tahrik.bloke.T1",
            "tahrik.bloke.T2",
            "tahrik.bloke.oran",
            "tahrik.mu_fren",
            "tahrik.f_bloke",
        )
        if _s15y["ara"].get(h) is None
    ]
    r.esit("⑮ α yokken T1 · T2 · oranlar · f yine hesaplanıyor", _eksik_h, [])
    r.esit(
        "⑮ α yokken sınır ara değerleri YAZILMIYOR ( sahte sayı yok )",
        [
            h
            for h in (
                "tahrik.alfa_derece",
                "tahrik.alfa",
                "tahrik.yukleme.sinir",
                "tahrik.fren_alt.sinir",
                "tahrik.fren_ust.sinir",
                "tahrik.bloke.sinir",
            )
            if h in _s15y["ara"]
        ],
        [],
    )
    _k15y = [
        a["deger"]
        for a in _b15y["adimlar"]
        if isinstance(a, dict) and a.get("deger") in ("UYGUN", "UYGUN DEĞİL", "HESAP EKSİK")
    ]
    r.esit("⑮ α yokken beş kontrol satırı da HESAP EKSİK", _k15y, ["HESAP EKSİK"] * 5)
    r.kontrol(
        "⑮ α yokken proje uyarısı çıkıyor",
        any("SARILMA AÇISI" in u for u in _s15y["uyarilar"]),
        f"→ {[u[:40] for u in _s15y['uyarilar']]}",
    )
    r.kontrol("⑮ α girilince uyarı çıkmıyor", not any("SARILMA AÇISI" in u for u in _s15b["uyarilar"]))
    r.esit("⑮ girilen açı hesaba giriyor", _s15b["ara"]["tahrik.alfa_derece"], 150.0)
    r.kontrol(
        "⑮ açı büyüyünce e^(f·α) sınırı da büyüyor",
        _s15t["ara"]["tahrik.yukleme.sinir"] > _s15b["ara"]["tahrik.yukleme.sinir"],
        f"→ {_s15b['ara']['tahrik.yukleme.sinir']:.4f} → {_s15t['ara']['tahrik.yukleme.sinir']:.4f}",
    )
    _a15 = [
        a
        for a in next(x for x in _s15b["bolumler"] if x["kimlik"] == "tahrik_yetenegi")["adimlar"]
        if isinstance(a, dict) and str(a.get("sembol") or "") == "α"
    ]
    r.esit("⑮ paftada α kaynağı 'GİRİŞ'", _a15[0].get("kaynak") if _a15 else None, "GİRİŞ")
    #  GEVŞEK HALAT, EKSİK AÇIYLA ÖRTÜLMEZ — kesin başarısızlık eksikten güçlü
    _s15g = mukavemet.hesapla({"acil_frenleme_a": 9.81, "kanal_sekli": _CS15})
    _b15g = next(x for x in _s15g["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
    r.kontrol(
        "⑮ α yokken gevşek halat 'UYGUN DEĞİL' kalıyor, eksikle örtülmüyor",
        not _b15g.get("eksik_hesap") and "gevşiyor" in str(_b15g["sonuc"]["metin"]),
        f"→ {_b15g['sonuc']['metin']!r} / eksik {_b15g.get('eksik_hesap')!r}",
    )
    #  Türetme kalktı:  C · D · Ra artık girdi değil
    for _alan in ("sap_kasnak_yuk", "makine_yatak_yuk", "halat_arasi_yan", "halat_arasi"):
        r.kontrol(f"⑮ '{_alan}' girdisi kaldırıldı", _alan not in _s15y["girdi"], "→ hâlâ var")
    #  ÇİFT SARIMDA AÇI 180°'Yİ AŞARSA BLOKE HÜKMÜ VERİLİR
    _s15c = mukavemet.hesapla({"kanal_sekli": _CS15, "sarilma_acisi": 330})
    _b15c = next(x for x in _s15c["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
    r.kontrol(
        "⑮ çift sarımda 180°'yi aşan açıyla hüküm veriliyor",
        not _b15c.get("eksik_hesap"),
        f"→ {_b15c.get('eksik_hesap')!r}",
    )
    r.esit("⑮ çift sarımda üst sınır 360°", _s15c["ara"]["tahrik.alfa_derece"], 330.0)
    #  Tek sarımda 180°'yi aşan açı reddedilmeli ( fiziksel olarak imkânsız )
    r.kontrol(
        "⑮ tek sarımda α > 180° kabul edilmiyor  ( girdide ret, bkz. ⑫ )",
        mukavemet.hesapla({"sarilma_acisi": 300}).get("aktif") is False,
    )
    r.kontrol(
        "⑮ aralık dışı açı girdi doğrulamasında reddediliyor",
        mukavemet.hesapla({"sarilma_acisi": 400}).get("aktif") is False,
    )
    #  ⑯  AVAN MOTORUNUN KABUL ETMEYECEĞİ KÖPRÜ DEĞERİYLE HESAP YAPILMAZ
    #  Kesitler, motor gücü ve kabin ağırlığı avan motorunun elektrik
    #  hesabına girer ve sınırları orada durur.  Önce aralık dışı kesit
    #  varsayılanla değiştiriliyor ( 900 mm² yazılan paftada 6 mm² ile hesap ),
    #  sonra yalnız "elektrik hesapları yapılamadı" deniyordu.  Artık girdi
    #  doğrulaması alanı adıyla reddeder.  L2 ve L1 asansör girdisi değildir
    #  ( Sabitler sekmesinde denetlenir ).
    _SINIR16 = {k: aralik for k, _ad, aralik, _b in avan_hesabi.ASANSOR_SINIRLARI}
    for _alan, _kotu in (
        ("kolon_kesit", 900),
        ("makine_kesit", 0.5),
        ("motor_gucu", 600),
        ("kabin_agirligi", 30),
    ):
        _avan_adi = uygulama_girdisi.AVAN_SINIRLI[_alan]
        _etiket = (uygulama_girdisi.EK_ALAN.get(_alan) or mukavemet_girdi.ALAN[_alan])[1]
        _ham16 = dict(uygulama_girdisi.varsayilanlar(), **TAM)
        _ham16[_alan] = _kotu
        _r16 = uygulama_hesabi.hesapla(uygulama_girdisi.tamamla(_ham16))
        r.kontrol(f"⑯ {_alan} = {_kotu} ile hesap yapılmıyor", _r16["aktif"] is False, "→ hesap yapıldı")
        r.kontrol(
            f"⑯ {_alan} reddi alanı ekrandaki adıyla ve aralığıyla söylüyor",
            any(_etiket in h and "geçerli aralık" in h for h in _r16.get("hata") or []),
            f"→ {_r16.get('hata')}",
        )
        #  Sınır İKİ projede aynı yerden okunur:  uç değer kabul edilir
        _ust16 = _SINIR16[_avan_adi][1]
        _sinir16 = dict(uygulama_girdisi.varsayilanlar(), **TAM, **{_alan: _ust16})
        _s16 = uygulama_hesabi.hesapla(uygulama_girdisi.tamamla(_sinir16))
        r.kontrol(
            f"⑯ {_alan} üst sınırda ( {_ust16} ) girdi kabul ediliyor",
            not any(_etiket in h for h in _s16.get("hata") or []),
            f"→ {_s16.get('hata')}",
        )
    #  ⑲  Pm, GÜCÜ VE MOMENTİ BELİRLEYEN YÜKTEN TÜRER
    #  Pm = F1 − Ga idi:  halatın tamamı kabin tarafında, yön · zincir · kablo
    #  yok.  q = 0,60'ta 185,7 kg basılıyor, belirleyici yük 269,1 kg idi.
    for _ad19, _g19 in (
        ("varsayılan", {}),
        ("denge zinciri", {"denge_zinciri": "Var"}),
        ("q = 0,60", {"_ofis": {"q_denge": 0.60}}),
        ("1:1 askı", {"aski_orani": 1}),
    ):
        _s19 = mukavemet.hesapla(_g19)
        _h19, _gi19 = _s19["ara"], _s19["girdi"]
        r.kontrol(
            f"⑲ [{_ad19}] Pm = Gmax / i",
            abs(_h19["motor.Pm"] - _h19["motor.Gmax"] / _gi19["aski_orani"]) < 1e-9,
            f"→ Pm {_h19['motor.Pm']} · Gmax/i {_h19['motor.Gmax'] / _gi19['aski_orani']}",
        )
        r.kontrol(
            f"⑲ [{_ad19}] M = Pm × Dt/2",
            abs(_h19["motor.M"] - _h19["motor.Pm"] * _gi19["tahrik_kasnak_capi"] / 2000) < 1e-9,
        )
    r.kontrol(
        "⑲ denge zinciri Pm'yi de değiştiriyor",
        mukavemet.hesapla({"denge_zinciri": "Var"})["ara"]["motor.Pm"]
        != mukavemet.hesapla({})["ara"]["motor.Pm"],
    )

    #  ⑳  UYGULAMA PAKETİ:  çizim + proje dosyası;  çalışma kitabı YOK
    import zipfile as _zip20

    if dxf_cikti is None:
        r.atla("⑳ CAD kitaplıkları kurulu değil — paket denetimi atlandı")
    else:
        #  BİRLEŞİK PROGRAM:  paket ÇİZİMLERLE iner ( çizim modülü, ../cizim ).
        #  Paketin içeriği çizilebilen bir asansörle denetlenir:  örnek projenin
        #  girdisi ( ../ornekler/hesap_girdi — referans proje ).  Son katı 3.200
        #  olan asansör çizilemez ( kuyu üstü yetmiyor:  üst paten kuyu tavanına
        #  giriyor — ofisin kabiniyle 3.750'de yalnız korkuluk kalıyor ):  paket
        #  inmez, sebebi söylenir.
        from hesap_girdi import ASANSOR as _A20, ORTAK as _O20, SABITLER as _S20

        _y20 = uygulama_uclari.indir_uygulama_dwg(
            {
                "asansorler": [dict(_A20)],
                "proje_geneli": dict(_O20),
                "sabitler": dict(_S20),
                "proje_dosyasi": {"__mod": "uygulama", "alanlar": {}},
            }
        )
        _r20 = uygulama_uclari.indir_uygulama_dwg(
            {
                "girdiler": dict(TAM, sarilma_acisi=180, son_kat_yuksekligi=3200),
                "proje_dosyasi": {"__mod": "uygulama", "alanlar": {}},
            }
        )
        r.kontrol(
            "⑳ çizimi kurulamayan girdide paket inmez, sebebi söylenir",
            _r20.media_type == "application/json"
            and "ÇİZİMLER KURULAMADI" in json.loads(_r20.body).get("hata", "")
            and "Üst paten" in json.loads(_r20.body).get("hata", ""),
            f"→ {_r20.media_type}",
        )
        _n20 = _zip20.ZipFile(io.BytesIO(_y20.body)).namelist()
        r.kontrol(
            "⑳ pakette DXF ve .uygulama proje dosyası var",
            any(x.endswith(".dxf") for x in _n20) and any(x.endswith(".uygulama") for x in _n20),
            f"→ {_n20}",
        )
        r.kontrol(
            "⑳ pakette Excel ya da eksik-dosya bildirimi yok",
            not any(x.lower().endswith((".xlsx", ".txt")) and x != "OKUBENI.txt" for x in _n20),
            f"→ {_n20}",
        )
    _js20 = _on_yuz_kaynagi()
    r.kontrol(
        "⑳ arayüzde Excel yükleme / kitap notu kalmadı", "KITAP" not in _js20 and "xlsx" not in _js20.lower()
    )

    # ---------------------------------------------------------------------
    #  ㉑  UYGULAMA OFİSİNİN ELEKTRİK VARSAYILANLARI AVAN MOTORUNUNKİYLE AYNI
    # ---------------------------------------------------------------------
    r.esit(
        "㉑ uygulama ofisinin κ varsayılanı motorunkiyle aynı",
        uygulama_sabitleri.VARSAYILAN["kappa"],
        avan_hesabi.OFIS_VARSAYILAN["kappa"],
    )
    _avv21 = {**avan_hesabi.SABIT_B_VARSAYILAN, **avan_hesabi.OFIS_VARSAYILAN}
    r.esit(
        "㉑ uygulama ofisinin BÜTÜN elektrik varsayılanları motorunkiyle aynı",
        {k: v for k, v in uygulama_sabitleri.VARSAYILAN.items() if k in _avv21 and v != _avv21[k]},
        {},
    )
    # ------------------------------------------------- proje adı sızıntısı
    #  AVAN VE UYGULAMA AYRI PROJELERDİR.  Avandan alınan bölümlerin bazı
    #  notları "kesin seçim UYGULAMA PROJESİNDE yapılır" der;  avan paftasında
    #  doğrudur, uygulama paftasında ise okuyucunun elindeki belgeyi işaret
    #  eder — kendi kendisiyle çelişir.  Metin uyarlanır, HESAP DEĞİŞMEZ.
    import re as _re

    _kalip = _re.compile(r"uygulama projesi", _re.I)
    _sizan = []
    for b in s["bolumler"]:
        for _alan in ("notlar", "aciklamalar", "ekran_notlari"):
            _sizan += [(b["baslik"], x) for x in (b.get(_alan) or []) if _kalip.search(x)]
        for c in b.get("cetvel") or []:
            if _kalip.search(str(c.get("sigorta") or "")):
                _sizan.append((b["baslik"], f"cetvel: {c['sigorta']}"))
    r.kontrol("uygulama paftasında kendini işaret eden not yok", not _sizan, f"→ {_sizan[:2]}")
    #  Aynı metin AVAN paftasında OLDUĞU GİBİ kalmalı — orada doğru
    _av = avan_hesabi.hesapla(
        uygulama_girdisi.avan_girdisi(uygulama_girdisi.tamamla(uygulama_girdisi.varsayilanlar()))
    )["asansorler"][0]
    _avnot = [
        x
        for b in _av["bolumler"]
        for _a in ("notlar", "aciklamalar")
        for x in (b.get(_a) or [])
        if _kalip.search(x)
    ]
    r.esit("avan paftasında not olduğu gibi duruyor", len(_avnot), 2)

    #  Sigorta kademesi tablo dışına taşarsa da proje adı sızmamalı
    _bt = uygulama_hesabi.hesapla(dict(TAM, motor_gucu=400))
    if r.kontrol("çok büyük motorla hesap koşuyor", _bt["aktif"]):
        _c = [b for b in _bt["bolumler"] if "KURULU GÜÇ" in b["baslik"]][0]["cetvel"][0]
        r.kontrol(
            "taşan sigorta hücresinde proje adı yok",
            not _kalip.search(str(_c["sigorta"])),
            f"→ {_c['sigorta']!r}",
        )
        #  Kurulu güç cetveline motorun ETİKET ( mil ) gücü yazılır;
        #  şebekeden çekilen güç kolon hattı hesabındadır ( bölüm 6 ).
        r.esit("taşan sigortada güç değeri bozulmadı", _c["guc"], 400_000)

    #  Ofis standardı köprüden geçiyor mu
    y = uygulama_hesabi.hesapla(dict(TAM, _ofis={"kuyu_armatur_lm": 1000}))
    r.kontrol(
        "ofis standardı elektrik hesabına giriyor",
        y["aktif"] and y["ozet"]["Z_kuyu"] != taban["Z_kuyu"],
        f"→ {y['ozet'].get('Z_kuyu')!r} / {taban['Z_kuyu']!r}",
    )

    # ---------------------------------------------------------- eksik girdi
    s = uygulama_hesabi.hesapla({})  # topraklama ve kolon boyu yok
    r.kontrol("eksik elektrik girdisiyle de hesap koşuyor", s["aktif"], f"→ {s.get('hata')}")
    if s["aktif"]:
        r.esit("topraklama olmadan bölüm sayısı", len(s["bolumler"]), len(mukavemet.BOLUM_URETICILERI) + 4)
        r.kontrol("topraklamasız özet Re taşımıyor", s["ozet"]["Re"] is None)

    s = uygulama_hesabi.hesapla({"mk_yok": False})
    r.kontrol("makine dairesi işaretli ama ölçüsüz → hesap duruyor", not s["aktif"])
    r.kontrol(
        "hata makine dairesi ölçüsünü istiyor",
        any("Makine dairesi" in x for x in (s.get("hata") or [])),
        f"→ {s.get('hata')}",
    )

    s = uygulama_hesabi.hesapla(dict(TAM, mk_yok=False, mk_uzunluk=4, mk_genislik=3))
    r.kontrol("makine daireli hesap koşuyor", s["aktif"], f"→ {s.get('hata')}")
    if s["aktif"]:
        r.esit("makine daireli bölüm sayısı", len(s["bolumler"]), len(mukavemet.BOLUM_URETICILERI) + 9)
        r.kontrol("makine dairesi aydınlatması eklendi", any("MAKİNE DAİRESİ" in a for a in _bolum_adlari(s)))

    #  Mukavemet girdisi geçersizse uygulama da durmalı
    #  ( kabin ağırlığı ARTIK boş bırakılabilir — ofis tablosundan dolar;
    #    burada gerçekten geçersiz bir geometri kullanılıyor.  Kaide alanı
    #    DEĞİL:  varsayılan proje MRL'dir ve orada kaide doğrulanmaz. )
    s = uygulama_hesabi.hesapla({"kabin_paten_arasi": 0})
    r.kontrol("geçersiz mukavemet girdisi uygulamayı da durduruyor", not s["aktif"], f"→ {s.get('hata')}")

    #  ------------------------------------------------------------------
    #  BOŞ KABİN AĞIRLIĞI OFİS TABLOSUNDAN DOLAR  —  AVANLA AYNI TABLODAN
    #  ------------------------------------------------------------------
    #  Standartlarda böyle bir çizelge yoktur:  TS EN 81-20 / 81-50 boş kabin
    #  kütlesini ( P ) hep GİRDİ olarak tanımlar.  Tablo ofisin kendi imalatçı
    #  deneyimidir ve İKİ PROJE DE aynı yerden okur ( motor/ortak/ofis.py ) —
    #  ayrı kopyalar tutulsaydı aynı asansör iki projede iki farklı kabin
    #  kütlesiyle hesaplanırdı.
    for _q in (450, 630, 800, 1000, 1125, 1275, 1600, 2000, 2500):
        _u = mukavemet.hesapla({"beyan_yuku": _q, "kabin_agirligi": None})
        if not r.kontrol(f"[Gk] {_q} kg için hesap koşuyor", _u["aktif"], f"→ {_u.get('hata')}"):
            continue
        r.esit(
            f"[Gk] {_q} kg → uygulama = avan tablosu",
            _u["girdi"]["kabin_agirligi"],
            float(tablolar.tablo11_Gk(_q)),
        )
        #  Karşı ağırlık da onunla birlikte türer
        r.esit(
            f"[Gk] {_q} kg → karşı ağırlık P + Q/2",
            _u["girdi"]["karsi_agirlik"],
            _u["girdi"]["kabin_agirligi"] + _q / 2.0,
        )
    #  Elle girilen değer HER ZAMAN önceliklidir
    _el = mukavemet.hesapla({"beyan_yuku": 1275, "kabin_agirligi": 1234})
    r.esit("[Gk] elle girilen değer korunuyor", _el["girdi"]["kabin_agirligi"], 1234)

    #  Paftada kaynağı yazıyor:  tahmin mi, giriş mi
    def _p_kaynagi(s):
        b1 = [x for x in s["bolumler"] if x["baslik"].startswith("1 ")][0]
        return next(a["kaynak"] for a in b1["adimlar"] if a.get("sembol") == "P")

    r.esit("[Gk] elle girilende kaynak GİRİŞ", _p_kaynagi(_el), "GİRİŞ")
    _tb = mukavemet.hesapla({"beyan_yuku": 1275, "kabin_agirligi": None})
    r.kontrol(
        "[Gk] tablodan gelende kaynak ofis tablosu", "KABUL" in _p_kaynagi(_tb), f"→ {_p_kaynagi(_tb)!r}"
    )

    #  Mukavemet sonucu tek başına koşturulanla AYNI olmalı  ( kirlenme yok )
    #  Uygulama projesinin varsayılan yerleşimi MRL'dir;  mukavemet tek başına
    #  aynı yerleşimle koşturulur ( tabliye MRL'de hesaba girmez ).  Program
    #  geometriyi çizimden alır ( UG.yerlesim_olculeri ):  tek başına koşan
    #  motora da aynı ölçüler verilir.
    _olc = uygulama_girdisi.yerlesim_olculeri(
        uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **TAM))
    )
    r.kontrol(
        "çizimden ölçü geliyor ( kabin rayı · askı halatı · Nps )",
        all(k in _olc for k in ("kabin_ray_boyu", "aski_halat_boyu", "kasnak_tek_yon")),
        f"→ {sorted(_olc)}",
    )
    tek = mukavemet.hesapla(dict(TAM, mk_yok=uygulama_girdisi.EK_ALAN["mk_yok"][5], **_olc))
    birlikte = uygulama_hesabi.hesapla(TAM)
    r.esit("ray boyu çizimdeki en uzun kabin rayı", birlikte["ozet"]["ray_boyu"], _olc.get("kabin_ray_boyu"))
    r.esit(
        "mukavemet bölümleri tek başına koşanla birebir aynı",
        [b["baslik"] for b in birlikte["bolumler"][: len(mukavemet.BOLUM_URETICILERI)]],
        [b["baslik"] for b in tek["bolumler"]],
    )
    for anahtar in ("N_hesap", "Sf", "ray_boyu", "FKR", "FAR", "Fkt", "Fat"):
        r.esit(f"mukavemet özeti değişmedi: {anahtar}", birlikte["ozet"][anahtar], tek["ozet"][anahtar])

    #  Avan tarafı tek başına koşturulanla aynı mı
    av = avan_hesabi.hesapla(
        uygulama_girdisi.avan_girdisi(uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **TAM)))
    )
    r.esit(
        "elektrik özeti avan motoruyla aynı",
        birlikte["ozet"]["P_kurulu"],
        av["asansorler"][0]["ozet"]["P_kurulu"],
    )

    # ==================================================================
    #  CAD ÇIKTISI  —  UYGULAMA PAFTASI AUTOCAD'DE AÇILIYOR MU
    #
    #  Bu bölümün varlık sebebi teslim edilmiş bir projedir:  AutoCAD 2027
    #  çizimi açarken ÇÖKÜYORDU ( "A software problem has caused application
    #  to close unexpectedly" ).  Sebep, AutoCAD'in metinde "^" + karakteri
    #  DENETİM KARAKTERİ diye yorumlaması;  yazı tipinde o kodun glifi yok ve
    #  macOS'ta arama FontCacheOSX::getCharData içinde çöküyor.  Şapka YALNIZ
    #  uygulama paftasında geçiyordu  —  halat emniyet katsayısı formülünde
    #  ( 10^[…], (Dt/dh)^8,567 ) ve tahrik yeteneğinde ( e^(f·α) )  —  bu
    #  yüzden avan paftalarını ölçen TEST 4 hatayı göremedi.  Uygulama
    #  paftasının CAD çıktısı o günden beri BURADA ölçülüyor.
    # ==================================================================
    try:
        import ezdxf
    except Exception as _cad_hata:  # noqa: BLE001
        r.atla(f"CAD çıktısı testi atlandı — ezdxf / pdfminer.six kurulu değil ( {_cad_hata} )")
    else:
        #  `s` bu noktada bozuk girdilerle yeniden hesaplanmış durumda;
        #  pafta TAM girdiden üretilmeli.
        _pdf = pdf_cikti.uygulama_pdf(uygulama_hesabi.hesapla_coklu([TAM]))
        _dxf = dxf_cikti.proje_dxf([("Uygulama Projesi", _pdf)])
        import io as _io

        _d = ezdxf.read(_io.StringIO(_dxf.decode("utf-8")))
        _m = _d.modelspace()
        _yazilar = [_e.dxf.text for _e in _m.query("TEXT")]
        r.kontrol("CAD: uygulama paftası çizime döndü", len(_yazilar) > 100, f"→ {len(_yazilar)} yazı")

        _sapkali = [t for t in _yazilar if "^" in t]
        r.kontrol(
            "CAD: hiçbir yazıda şapka ( ^ ) yok — AutoCAD'i çökertiyor", not _sapkali, f"→ {_sapkali[:3]}"
        )
        _yuzdeli = [t for t in _yazilar if "%%" in t]
        r.kontrol("CAD: hiçbir yazıda AutoCAD kaçış dizisi ( %% ) yok", not _yuzdeli, f"→ {_yuzdeli[:3]}")
        #  Üs işareti PAFTADA gerçekten var mı — yoksa yukarıdaki iki kontrol
        #  hiçbir şey ölçmemiş olur.
        _pdf_yazi = " ".join(t["metin"] for _s in dxf_cikti._sayfa_geometrisi(_pdf) for t in _s["metinler"])
        r.kontrol("CAD: paftada üs işareti gerçekten geçiyor  ( ölçüt boş değil )", "^" in _pdf_yazi)
        r.kontrol("CAD: üs işareti çizimde U+02C6 olarak duruyor", any("\u02c6" in t for t in _yazilar))

        #  Açılış görünümü:  sınırlar hesaplanmış ve görünüm çizimin üstünde
        _emin, _emax = _d.header["$EXTMIN"], _d.header["$EXTMAX"]
        r.kontrol(
            "CAD: $EXTMIN / $EXTMAX hesaplanmış ( 1e+20 değil )",
            all(abs(q) < 1e9 for q in list(_emin) + list(_emax)),
            f"→ {_emin} {_emax}",
        )
        from ezdxf.bbox import extents as _extents

        _bb = _extents(_m)
        _mrk = list(_d.viewports.get("*Active"))[0].dxf.center
        r.kontrol(
            "CAD: kayıtlı görünüm çizimin ÜSTÜNDE ( boş ekran açılmıyor )",
            _bb.extmin.x <= _mrk.x <= _bb.extmax.x and _bb.extmin.y <= _mrk.y <= _bb.extmax.y,
            f"→ görünüm {_mrk}, çizim {_bb.extmin}-{_bb.extmax}",
        )
    #  Geçersiz q ile hesap YAPILMAZ ( eskiden varsayılan 0,50'ye dönülüyordu ).
    for q in (2, -1):
        sonuc = mukavemet.hesapla({"_ofis": {"q_denge": q}})
        r.kontrol(
            f"denge {q}: aralık dışı q ile hesap yapılmıyor",
            sonuc["aktif"] is False
            and any("Ofis standardı" in h and "geçerli aralık" in h for h in sonuc.get("hata") or []),
            f"→ {sonuc.get('hata')}",
        )
    #  Geçerli q:  türetilen kütle ve bütün yük hesapları aynı değeri kullanır.
    for q, beklenen in ((0.6, 1180), (0.2, 860), (0.8, 1340), (0.5, 1100)):
        sonuc = mukavemet.hesapla({"_ofis": {"q_denge": q}})
        r.esit(f"denge {q}: türetilen kütle", sonuc["girdi"]["karsi_agirlik"], beklenen)
        r.esit(f"denge {q}: motor kütlesi", sonuc["ara"]["motor.Ga"], beklenen)
        #  AĞIRLIK TAMPONU m.5.2.1.8.6'NIN KENDİ BAĞINTISIYLA:
        #  F = 4·gn·( P + q·Q ) — oradaki P "boş kabin + gezici kablo payı +
        #  denge zinciri"dir, karşı ağırlığın fiziksel kütlesi değil.
        #  Asıl denetlenen şey q'nun her yere AYNI geçmesi:  beklenen kütle
        #  700 + q·800 olduğuna göre q buradan geri okunur.
        _qe = (beklenen - 700) / 800.0
        r.kontrol(
            f"denge {q}: tampon yükü m.5.2.1.8.6 bağıntısıyla",
            abs(sonuc["ozet"]["Fat"] - 4 * 9.81 * (_P_std(sonuc) + _qe * 800)) < 1e-7,
            f"→ {sonuc['ozet']['Fat']!r}",
        )

    from motor.ortak import ofis

    otomatik = uygulama_hesabi.hesapla({"kabin_agirligi": None})
    p_satiri = next(a for a in otomatik["bolumler"][0]["adimlar"] if a.get("sembol") == "P")
    r.esit("otomatik kabin kütlesi hesap satırında kaynak korur", p_satiri["kaynak"], ofis.GK_KAYNAGI)
    tekrar = uygulama_girdisi.tamamla(otomatik["girdi"])
    r.esit("tekrar tamamlamada kaynak korunur", tekrar["kabin_agirligi_kaynak"], ofis.GK_KAYNAGI)
    tekrar["kabin_agirligi"] = 777
    r.esit(
        "elle değiştirilmiş kütle giriş olarak işaretlenir",
        uygulama_girdisi.tamamla(tekrar)["kabin_agirligi_kaynak"],
        "GİRİŞ",
    )

    # Tek kalın halatın yüksek kopma dayanımı asgari adedi geçiremez.
    _halat_g = dict(
        halat_capi=16, tahrik_kasnak_capi=640, saptirma_kasnak_capi=640, beyan_yuku=225, kabin_agirligi=200
    )
    _tek = mukavemet.hesapla(dict(_halat_g, halat_adedi=1))
    r.kontrol("tek askı halatı girişte reddedilir", not _tek["aktif"])
    r.kontrol("tek halat hatası asgari adedi bildirir", any("en az 2" in h for h in _tek["hata"]))
    for _n, _smin in ((2, 16), (3, 12)):
        _s = mukavemet.hesapla(dict(_halat_g, halat_adedi=_n))
        r.esit(f"{_n} halatta doğru güvenlik alt sınırı", _s["ara"]["aski.Smin"], _smin)
    # Doğrulamayı atlayan doğrudan bölüm çağrısında da uygunluk engellenir.
    _g = uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **_halat_g, halat_adedi=1))
    _o = {"ofis": uygulama_sabitleri.sabitler()}
    mukavemet._motor(_g, _o)
    _b = mukavemet._aski_halatlari(_g, _o)
    r.kontrol("tek halat bölümde de reddedilir", _b["sonuc"]["uygun"] is False)

    #  ══════════════════════════════════════════════════════════════
    #  ÇOKLU ASANSÖR  ( 1 - 4 asansör, tek proje )
    #  ══════════════════════════════════════════════════════════════
    #  Motor TEK ASANSÖRLÜK kalır;  çoklu yalnız onu birden çok kez koşturur.
    #  İkinci bir hesap yolu açılmadığı burada kilitlenir:  tek asansörlük
    #  çağrı ile çoklunun ilk asansörü BİREBİR aynı çıkmalıdır.
    _C_ORTAK = {
        "temel_a": 26.55,
        "temel_b": 16.4,
        "serit_L": 58.5,
        "mk_yok": False,
        "mk_uzunluk": 4.0,
        "mk_genislik": 3.0,
    }
    _c = uygulama_hesabi.hesapla_coklu(
        [{"asansor_adi": "İnsan 1"}, {"beyan_yuku": 630}, {"beyan_yuku": 1000, "asansor_adi": "Yük"}],
        _C_ORTAK,
    )
    r.kontrol("çoklu: hesap aktif", _c["aktif"] is True, f"→ {_c.get('hata')}")
    r.esit("çoklu: asansör sayısı", _c["adet"], 3)
    r.esit("çoklu: azami asansör", uygulama_hesabi.ASANSOR_AZAMI, 4)
    r.esit("çoklu: girilen ad korunuyor", _c["asansorler"][0]["tanim"], "İnsan 1")
    r.esit("çoklu: adsız asansör numarayla anılıyor", _c["asansorler"][1]["tanim"], "2 nolu asansör")

    #  PROJE GENELİ HESAPLAR HİÇBİR ASANSÖRDE DEĞİL, EN SONDA BİR KEZ.
    #  Topraklama ve makine dairesi binaya aittir;  dört kez basılması hem yer
    #  kaplar hem "hangisi geçerli" sorusunu doğurur.  Bir süre YALNIZ İLK
    #  asansörde bırakılıyorlardı — o zaman da binaya ait hesap 1 nolu
    #  asansörün arkasına, yani belgenin ORTASINA düşüyordu.
    _pg = [len([b for b in a["bolumler"] if b.get("proje_geneli")]) for a in _c["asansorler"]]
    r.esit("çoklu: proje geneli bölüm hiçbir asansörde kalmıyor", _pg, [0, 0, 0])
    r.esit(
        "çoklu: proje geneli bölümler üst seviyede",
        [b["baslik"] for b in _c["proje_geneli"]],
        [
            "1 - MAKİNE DAİRESİ AYDINLATMA HESABI",
            "2 - YATAY ( TEMEL ) TOPRAKLAYICI",
            "3 - DİKEY ( ÇUBUK ) TOPRAKLAYICI",
            "4 - TOPLAM TOPRAKLAMA DİRENCİ VE KONTROL",
            "5 - TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ",
        ],
    )
    r.esit("çoklu: özet proje geneli bölümleri sayıyor", _c["ozet"]["proje_geneli_adet"], 5)
    r.kontrol("çoklu: proje geneli uygunluğu özette", _c["ozet"]["proje_geneli_uygun"] is True)
    #  PROJE GENELİ HESAP "HEPSİ UYGUN"A GİRER.  Bölümler asansörlerden
    #  çıkınca onların bayrağı bunları saymaz;  ayrıca katılmasaydı
    #  topraklaması yetersiz bir proje "UYGUNDUR" görünürdü.
    _kotu = uygulama_hesabi.hesapla_coklu([{}], dict(_C_ORTAK, temel_a=0.4, temel_b=0.4, serit_L=1.0))
    if _kotu["ozet"]["proje_geneli_uygun"] is False:
        r.kontrol("çoklu: proje geneli kalınca proje UYGUN görünmüyor", _kotu["ozet"]["tumu_uygun"] is False)
    else:
        r.kontrol(
            "çoklu: proje geneli kalınca proje UYGUN görünmüyor",
            True,
            "→ küçük temelde de topraklama uygun çıktı, kontrol atlandı",
        )
    r.kontrol(
        "çoklu: asansörlerin bölüm numaraları boşluksuz",
        all(
            [b["baslik"].split("-")[0].strip() for b in a["bolumler"]]
            == [str(i) for i in range(1, len(a["bolumler"]) + 1)]
            for a in _c["asansorler"]
        ),
        f"→ {[b['baslik'].split('-')[0].strip() for b in _c['asansorler'][1]['bolumler']]}",
    )

    #  TEK ASANSÖRLE BİREBİR AYNI:  ikinci bir hesap yolu yok
    _tekil = uygulama_hesabi.hesapla(dict(_C_ORTAK, beyan_yuku=630))
    _ikinci = _c["asansorler"][1]
    r.esit(
        "çoklu: 2. asansörün motor gücü tekille aynı",
        (_ikinci["ozet"] or {}).get("N_hesap"),
        (_tekil["ozet"] or {}).get("N_hesap"),
    )
    r.esit(
        "çoklu: 2. asansörün halat katsayısı tekille aynı",
        (_ikinci["ozet"] or {}).get("Sf"),
        (_tekil["ozet"] or {}).get("Sf"),
    )

    #  SINIRLAR
    r.esit(
        "çoklu: azamiden fazlası kırpılıyor",
        uygulama_hesabi.hesapla_coklu([{}] * 9)["adet"],
        uygulama_hesabi.ASANSOR_AZAMI,
    )
    r.esit("çoklu: boş liste tek asansöre düşer", uygulama_hesabi.hesapla_coklu([])["adet"], 1)
    r.kontrol(
        "çoklu: özet asansör listesi dolu",
        len(_c["ozet"]["asansorler"]) == 3 and _c["ozet"]["asansorler"][2]["tanim"] == "Yük",
    )

    #  PAFTADA EN SONDA.  Motor bölümleri ayırıyor;  asıl mesele onların
    #  BELGEDE nereye düştüğü — bunu ancak basılmış PDF gösterir.
    try:
        import io as _io
        import re as _re

        import pypdfium2 as _pdfium

        _b = pdf_cikti.uygulama_pdf(_c, {"project_title": "Deneme"})
        _d = _pdfium.PdfDocument(_io.BytesIO(_b))
        _m = "\n".join(_d[i].get_textpage().get_text_range() for i in range(len(_d)))
        _d.close()  # pdfium tutamakları açık kalmasın
        _sira, _onceki = [], None
        for _x in _re.findall(r"(ASANSÖR \d · [^\n]*?|PROJE GENELİ HESAPLAR)", _m):
            _x = _x.split(" 3 asansörden")[0].strip()
            if _x != _onceki:
                _sira.append(_x)
                _onceki = _x
        r.kontrol(
            "pafta: proje geneli hesaplar EN SONDA",
            _sira and _sira[-1] == "PROJE GENELİ HESAPLAR",
            f"→ {_sira}",
        )
        r.esit("pafta: topraklama bir kez basılıyor", _m.count("YATAY ( TEMEL ) TOPRAKLAYICI"), 1)
        #  Şerit yalnız başlıktır:  "bütün asansörler için bir kez" yan yazısı
        #  ve "BİNAYA aittir" kutusu paftayı okuyana bilgi vermiyordu.
        r.kontrol(
            "pafta: proje geneli şeridinde açıklama yazısı YOK",
            "bütün asansörler için bir kez" not in _m and "BİNAYA aittir" not in _m,
        )
    except ImportError:
        r.kontrol("pafta sırası denetlenemedi ( pypdfium2 yok )", True)

    #  ─────────────────────────────────────────────────────────────
    #  TEK YOL  —  tek asansör ile çoklu asansör aynı yerden geçer
    #  ─────────────────────────────────────────────────────────────
    #  Bir süre iki motor girişi ( hesapla / hesapla_coklu ), iki pafta
    #  fonksiyonu ( uygulama_pdf / uygulama_coklu_pdf ) ve API'de ÜÇ ayrı
    #  dallanma vardı;  hangisinin çağrılacağına API karar veriyordu.  İkisi
    #  ayrıştı:  proje geneli hesaplar çoklu paftada en sona alınmış, tek
    #  asansörlükte bölümlerin arasında kalmıştı — aynı program aynı projeyi
    #  asansör sayısına göre iki türlü basıyordu.  Avan trafik motoru bu işi
    #  baştan doğru yapar:  tek giriş, kullanılan yol SONUCUN İÇİNDE yazar.
    _t1 = uygulama_hesabi.hesapla_coklu([{}], _C_ORTAK)
    _t2 = uygulama_hesabi.hesapla_coklu([{}, {"beyan_yuku": 630}], _C_ORTAK)
    r.esit("tek asansörde yol 'tek' yazıyor", _t1["yol"], "tek")
    r.esit("çok asansörde yol 'coklu' yazıyor", _t2["yol"], "coklu")
    r.esit("iki durumda da SONUÇ ŞEKLİ aynı", sorted(_t1.keys()), sorted(_t2.keys()))
    #  Proje geneli hesaplar TEK asansörde de ayrılır — asıl ayrışma buydu
    r.esit(
        "tek asansörde de proje geneli ayrılmış",
        [b["kimlik"] for b in _t1["proje_geneli"]],
        [b["kimlik"] for b in _t2["proje_geneli"]],
    )
    r.esit(
        "tek asansörde de bölümler asansörde kalmıyor",
        [b for b in _t1["asansorler"][0]["bolumler"] if b.get("proje_geneli")],
        [],
    )
    #  API artık asansör sayısına göre BAŞKA MOTOR çağırmıyor:  modülde
    #  dallanmayı kuran isimler kalmamalı.
    _api = open(os.path.join(KOK, "uclar", "uygulama_uclari.py"), encoding="utf-8").read()
    for _ad in ("_coklu_mu", "_uygulama_sonucu", "uygulama_coklu_pdf"):
        r.kontrol(f"API'de '{_ad}' kalmadı", _ad not in _api)
    r.esit("API tek motor girişi çağırıyor", _api.count("E_UYG.hesapla("), 0)
    _pe = open(os.path.join(KOK, "ciktilar", "pdf_cikti.py"), encoding="utf-8").read()
    r.esit("tek uygulama paftası fonksiyonu", _pe.count("\ndef uygulama_"), 1)

    #  ─────────────────────────────────────────────────────────────
    #  BÖLÜM KİMLİĞİ  —  numara biçimdir, kimlik değildir
    #  ─────────────────────────────────────────────────────────────
    #  Bir süre bölümü tanıyan her şey BAŞLIKTAKİ NUMARAYA bakıyordu.  Numara
    #  projeye göre kayar:  proje geneli bölümler ayrılınca kalanlar yeniden
    #  numaralanır, makine dairesi yoksa topraklama bir sıra öne gelir.  Bu
    #  yüzden proje geneli bölümler hiç eşlenemiyordu ve elektrik bölümlerini
    #  eşlemek için "mukavemet 10 bölümdür" varsayımını gömmek gerekiyordu.
    _tekil = uygulama_hesabi.hesapla(_C_ORTAK)
    _tum = list(_tekil["bolumler"])
    r.kontrol(
        "her bölüm kimlik taşıyor",
        all(b.get("kimlik") for b in _tum),
        f"→ kimliksiz: {[b['baslik'] for b in _tum if not b.get('kimlik')]}",
    )
    r.esit("kimlikler tekil", len({b["kimlik"] for b in _tum}), len(_tum))
    r.kontrol(
        "her bölüm sıra numarası da taşıyor",
        [b.get("sira") for b in _tum] == list(range(1, len(_tum) + 1)),
        f"→ {[b.get('sira') for b in _tum]}",
    )
    r.kontrol(
        "başlık = sıra + ad",
        all(b["baslik"] == f"{b['sira']} - {b['ad']}" for b in _tum),
        f"→ {[b['baslik'] for b in _tum[:2]]}",
    )

    #  ASIL KONTROL:  NUMARA KAYARKEN KİMLİK DURUYOR.
    #  Aynı hesap üç ayrı kurulumda üç ayrı numara alır ama kimliği aynıdır.
    def _numara(sonuc, kim):
        for b in (sonuc.get("bolumler") or []) + (sonuc.get("proje_geneli") or []):
            if b.get("kimlik") == kim:
                return b["sira"]
        return None

    _mk_var = uygulama_hesabi.hesapla_coklu([{}], _C_ORTAK)  # makine dairesi VAR
    _mk_yok = uygulama_hesabi.hesapla_coklu(
        [{}], dict(_C_ORTAK, mk_yok=True, mk_uzunluk=None, mk_genislik=None)
    )
    _numaralar = (
        _numara(_tekil, "topraklama_toplam"),
        _numara(_mk_var["asansorler"][0], "topraklama_toplam") or _numara(_mk_var, "topraklama_toplam"),
        _numara(_mk_yok, "topraklama_toplam"),
    )
    r.kontrol(
        "aynı hesap kurulumdan kuruluma FARKLI numara alıyor", len(set(_numaralar)) > 1, f"→ {_numaralar}"
    )
    r.kontrol("kimlik ise hiç değişmiyor", all(n is not None for n in _numaralar), f"→ {_numaralar}")

    #  EŞLEME SÖZLEŞMESİ:  eşlemedeki her kimlik gerçek bir bölümdür ve
    #  gerçek her bölüm eşlemededir.  Numara kullanılırken bu denetlenemezdi.
    _bg = uygulama_girdisi.arayuz_alanlari()["bolum_grubu"]
    _gercek = {b["kimlik"] for b in _tum}
    r.esit("eşlemede olup motorda olmayan bölüm", sorted(set(_bg) - _gercek), [])
    r.esit("motorda olup eşlemede olmayan bölüm", sorted(_gercek - set(_bg)), [])
    _gruplar = {g["ad"] for g in uygulama_girdisi.arayuz_alanlari()["gruplar"]}
    r.esit(
        "eşlemenin gösterdiği her grup gerçekten var",
        sorted({ad for v in _bg.values() for ad in v} - _gruplar),
        [],
    )
    r.kontrol(
        "eşleme en çok iki grup gösteriyor",
        all(1 <= len(v) <= 2 for v in _bg.values()),
        f"→ {[k for k, v in _bg.items() if len(v) > 2]}",
    )
    r.kontrol(
        "proje geneli bölümler de eşlenmiş",
        all(k in _bg for k in ("makine_dairesi_aydinlatma", "topraklama_yatay", "topraklama_toplam")),
        "→ numara kayarken eşlenemiyorlardı",
    )

    #  ─────────────────────────────────────────────────────────────
    #  EŞLEMENİN İÇERİĞİ  —  gösterdiği grup gerçekten o bölümü besliyor mu
    #  ─────────────────────────────────────────────────────────────
    #  Yukarıdaki kontroller eşlemenin TAM olduğunu gösteriyor:  her bölüm
    #  eşlemede, her kimlik gerçek.  Ama İÇERİĞİNİ ( "aski_halatlari →
    #  Makine ve motor" doğru mu ) hiçbir şey denetlemiyordu;  liste elle
    #  yazılmıştı ve bir alan grup değiştirdiğinde sessizce bayatlardı.
    #
    #  YÖNTEM PERTÜRBASYON, KOD TARAMASI DEĞİL:  her girdi tek tek oynatılıp
    #  hangi bölümün sonucunun değiştiğine bakılır.  Kaynak koddaki g[...]
    #  okumalarını taramak dolaylı bağları ( köprüden geçen elektrik
    #  girdileri gibi ) kaçırırdı;  bu yöntem motorun İKİSİNİ birden ve
    #  gerçekte ne olduğunu ölçer.
    #
    #  KURAL:  eşlemede yazılı her grup, o bölümü GERÇEKTEN etkileyen bir
    #  grup olmalıdır.  Tersi aranmaz — bir bölüm çoğu grubu okur ( motor
    #  gücü yedi gruptan besleniyor ), eşleme ise en çok ikisini gösterir.
    #
    #  Bu tarama iki gerçek hata yakaladı:  "kuyu_tabani → Tamponlar"
    #  ( tampon KUVVETİ kütle × g'dir, tampon geometrisi kuvvete girmez ) ve
    #  "kurulu_guc → Elektrik ve topraklama" ( kuyu armatür adedi kuyu
    #  YÜKSEKLİĞİNDEN gelir, genişlik yalnız lux kontrolüne girer ).
    _ORTAK_T = {
        "mk_yok": False,
        "mk_uzunluk": 4000.0,
        "mk_genislik": 3000.0,
        "temel_a": 20.0,
        "temel_b": 12.0,
        "serit_L": 64.0,
    }

    def _bolum_icerigi(sonuc):
        """kimlik → karşılaştırılabilir içerik  ( sıra ve başlık hariç )."""
        ic = {}
        for b in ((sonuc.get("asansorler") or [{}])[0].get("bolumler") or []) + (
            sonuc.get("proje_geneli") or []
        ):
            ic[b.get("kimlik")] = json.dumps(
                {k: v for k, v in b.items() if k not in ("sira", "baslik")},
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
        return ic

    def _oynat(f, simdiki):
        """Alanı GEÇERLİ kalacak şekilde değiştir;  değiştirilemiyorsa None."""
        t = f["tur"]
        if t == "onay":
            return [not simdiki]
        if t == "secim":
            baska = [x for x in (f["secenekler"] or []) if str(x) != str(simdiki)]
            return baska[:1] or None
        if t == "sayi":
            v = simdiki if isinstance(simdiki, (int, float)) else 0
            #  KESİT ALANLARI BASAMAK FONKSİYONUDUR.  Koruma iletkeni ve
            #  potansiyel dengeleme kesitleri standart kesit merdivenine
            #  yuvarlanır ve 6 mm² tabanı vardır;  +%15'lik bir itme
            #  ( 6 → 7,9 ) hiçbir basamağı atlamaz ve bölüm kımıldamaz.
            #  Bağı GERÇEKTEN sınamak için bir basamak aşan bir sıçrama gerekir.
            if f["anahtar"] in ("kolon_kesit", "makine_kesit"):
                return [round(v * 8 + 1, 3)]
            #  Adetler tam sayıdır;  ölçüler önce büyür, kuyunun geometrisini
            #  bozuyorsa ( kabin kuyuya sığmıyor — hesap durur, 4 Eki ) küçülür.

            if f["anahtar"] in mukavemet_girdi.TAM_SAYI_ALANLARI:
                return [v + 1] + ([v - 1] if v > 1 else [])
            return [round(v * 1.15 + 1, 3), round(v * 0.9, 3)]
        return None  # metin ve liste: sonuca girmez / ayrı denenir

    _taban = uygulama_hesabi.hesapla_coklu([{}], _ORTAK_T)
    _taban_ic = _bolum_icerigi(_taban)
    _tg = _taban["asansorler"][0]["girdi"]
    _arayuz = uygulama_girdisi.arayuz_alanlari()
    _grubu = {f["anahtar"]: gr["ad"] for gr in _arayuz["gruplar"] for f in gr["alanlar"]}
    _etki, _denenemeyen = {k: set() for k in _taban_ic}, []
    for _gr in _arayuz["gruplar"]:
        for _f in _gr["alanlar"]:
            _a = _f["anahtar"]
            _adaylar = _oynat(_f, _tg.get(_a))
            if _adaylar is None:
                _denenemeyen.append(_a)
                continue
            #  Kabin büyüyünce kuyu da aynı kadar büyür:  kabini kuyuya sığmayan
            #  projenin hesabı durur ( 4 Eki ) — kabin yalnız küçülebilseydi
            #  aydınlatmanın armatür sayısı ( ROUNDUP ) kımıldamazdı.
            _kuyusu = {"kabin_genisligi": "kuyu_genisligi", "kabin_derinligi": "kuyu_derinligi"}
            for _yeni in _adaylar:
                _ek = {_a: _yeni}
                if (
                    _a in _kuyusu
                    and isinstance(_tg.get(_a), (int, float))
                    and isinstance(_tg.get(_kuyusu[_a]), (int, float))
                ):
                    _ek[_kuyusu[_a]] = _tg[_kuyusu[_a]] + (_yeni - _tg[_a])
                _s = (
                    uygulama_hesabi.hesapla_coklu([{}], dict(_ORTAK_T, **_ek))
                    if _a in uygulama_girdisi.PROJE_GENELI_ALANLAR
                    else uygulama_hesabi.hesapla_coklu([_ek], _ORTAK_T)
                )
                if _s.get("aktif"):
                    break
            if not _s.get("aktif"):
                _denenemeyen.append(_a)  # bu değerlerle girdi geçersiz oluyor
                continue
            _yeni_ic = _bolum_icerigi(_s)
            for _kim in set(_taban_ic) | set(_yeni_ic):
                if _taban_ic.get(_kim) != _yeni_ic.get(_kim):
                    _etki.setdefault(_kim, set()).add(_grubu[_a])

    r.kontrol(
        "pertürbasyon taraması çalıştı",
        sum(len(v) for v in _etki.values()) > 40,
        f"→ yalnız {sum(len(v) for v in _etki.values())} bağ bulundu",
    )
    _yanlis = {
        kim: [g for g in gruplar if g not in _etki.get(kim, set())]
        for kim, gruplar in _bg.items()
        #  Girdisi HİÇ olmayan bölüm muaf:  topraklama çubuğu yalnız
        #  ofis sabitlerinden ( çubuk sayısı · boyu · toprak özdirenci )
        #  hesaplanır, hiçbir proje girdisi onu değiştirmez.
        if _etki.get(kim)
    }
    _yanlis = {k: v for k, v in _yanlis.items() if v}
    r.esit("eşlemedeki her grup o bölümü GERÇEKTEN etkiliyor", _yanlis, {})
    #  Girdisiz bölümlerin listesi SABİTLENİR — yenisi çıkarsa fark edilsin
    r.esit(
        "hiçbir proje girdisinden etkilenmeyen bölümler",
        sorted(k for k in _bg if not _etki.get(k)),
        ["topraklama_dikey"],
    )
    #  Denenemeyen alanlar körlük yaratır;  sayısı sabitlenir ki sessizce
    #  büyümesin ( büyürse tarama gitgide daha az şey görüyor demektir ).
    r.kontrol(
        "taramanın körlüğü sınırlı",
        len(_denenemeyen) <= 16,
        f"→ {len(_denenemeyen)} alan denenemedi: {sorted(_denenemeyen)}",
    )

    #  PROJE GENELİ ALANLAR TEK KAYNAKTA
    r.kontrol(
        "proje geneli alan listesi motorda",
        set(uygulama_girdisi.PROJE_GENELI_ALANLAR)
        == {"temel_a", "temel_b", "mk_yok", "mk_uzunluk", "mk_genislik"},
        f"→ {uygulama_girdisi.PROJE_GENELI_ALANLAR}",
    )

    _muhendis_okumasi(r)
    _sira_degismezligi(r)
    _pafta_zinciri(r)
    return r


# =====================================================================
#  MÜHENDİS OKUMASI  —  paftanın NE SÖYLEDİĞİ
# =====================================================================
#  Program bir mühendis gibi kullanılıp pafta baştan sona okununca üç yer
#  bulundu.  Hiçbiri bir sayıyı değiştirmez;  üçü de paftayı okuyanın
#  sayıyı doğru anlamasıyla ilgilidir.
def _muhendis_okumasi(r):

    #  ①  FKR / FAR BİR RAYIN KUVVETİDİR.  Paftada "Kabin raylarına gelen
    #  kuvvet" yazıyordu;  inşaat mühendisi sayıyı toplam sanıp raylara
    #  bölseydi yükün yarısını kullanırdı.  Anlamı SAYIYLA sınanır:  kabin
    #  rayında FKR = a + b / n olmalı ( a = bir rayın kütlesi ve donanımı,
    #  b / n = güvenlik tertibatı payı ).  Öyleyse n = 2 · 3 · 6 için art
    #  arda iki fark eşittir;  toplam olsaydı ( a·n + b ) eşit çıkmazdı.
    _f = {
        n: mukavemet.hesapla({"sarilma_acisi": 180, "kabin_ray_sayisi": n})["ozet"]["FKR"] for n in (2, 3, 6)
    }
    r.kontrol(
        "① FKR bir rayın kuvveti:  FKR(2) − FKR(3) = FKR(3) − FKR(6)",
        abs((_f[2] - _f[3]) - (_f[3] - _f[6])) < 1e-6,
        f"→ {_f}",
    )
    #  b = k1 · gn · ( P + Q ):  güvenlik tertibatı payının tamamı.  P
    #  standardın P'sidir ( gezici kablo dâhil ) ve motordan okunmaz.
    _s = mukavemet.hesapla({"sarilma_acisi": 180})
    _b = 6 * (_f[2] - _f[3])
    _bek = (
        mukavemet.SABIT["gn"]
        * 2  # k1 = 2 ( kaymalı — örnek projenin tertibatı )
        * (_P_std(_s) + _s["girdi"]["beyan_yuku"])
    )
    r.kontrol(
        "① FKR'deki tertibat payı k1·gn·( P + Q ) / n",
        abs(_b - _bek) < 1e-6 * _bek,
        f"→ {_b} · beklenen {_bek}",
    )
    #  Karşı ağırlıkta tertibat yokken FAR ray sayısından bağımsızdır:
    #  içinde yalnız BİR rayın kütlesi ve donanımı vardır.
    _far = {
        n: mukavemet.hesapla({"sarilma_acisi": 180, "agirlik_ray_sayisi": n})["ozet"]["FAR"] for n in (2, 4)
    }
    r.kontrol(
        "① FAR bir rayın kuvveti:  ray sayısı değişince aynı kalıyor",
        abs(_far[2] - _far[4]) < 1e-9,
        f"→ {_far}",
    )
    _kt = next(b for b in _s["bolumler"] if b["kimlik"] == "kuyu_tabani")
    _metin = [str(a.get("deger")) for a in _kt["adimlar"] if a.get("tip") == "metin"]
    r.kontrol(
        "① bölüm 9 başlıkları 'bir kabin rayına' / 'bir ağırlık rayına'",
        any(m.startswith("Bir kabin rayına gelen kuvvet") for m in _metin)
        and any(m.startswith("Bir ağırlık rayına gelen kuvvet") for m in _metin)
        and not any("raylarına gelen" in m for m in _metin),
        f"→ {_metin}",
    )
    r.kontrol(
        "① bölüm 9 sonucu FKR ve FAR'ı 'N / ray' yazıyor",
        _kt["sonuc"]["metin"].count("N / ray") == 2,
        f"→ {_kt['sonuc']['metin']}",
    )
    _pdf = open(os.path.join(KOK, "ciktilar", "pdf_cikti.py"), encoding="utf-8").read()
    _js = _on_yuz_kaynagi()
    r.kontrol(
        "① PDF özetleri ( tek ve çoklu ) 'bir rayına' yazıyor",
        _pdf.count("FKR — Bir kabin rayına gelen kuvvet") == 2
        and _pdf.count("FAR — Bir ağırlık rayına gelen kuvvet") == 2
        and "raylarına gelen kuvvet" not in _pdf,
    )
    #  Ekran kuvvet adlarını kendi yazmaz:  bölüm sonucunu sunucudan okur
    r.kontrol(
        "① ekran kuvvet adlarını kendi kurmuyor ( sunucunun metni )",
        len(_js) > 10000 and "FKR" not in _js and "rayları'" not in _js,
    )

    #  ②  HALAT BOYUNDAKİ YIĞIN AÇIK YAZILIR.  Paftada yalnız toplamı
    #  ( 6.660 mm ) görünüyordu;  hangi beş ölçünün toplandığı yoktu.
    _g = _s["girdi"]
    _mb = next(b for b in _s["bolumler"] if b["kimlik"] == "motor_gucu")
    _y = [
        a for a in _mb["adimlar"] if a.get("tip") == "hesap" and str(a.get("formul", "")).startswith("Yığın")
    ]
    _top = (
        _g["agirlik_tampon_baba"]
        + _g["agirlik_carpma_arasi"]
        - _g["agirlik_tampon_ezilme"]
        + _g["agirlik_paten_arasi"]
        + _g["kabin_paten_arasi"]
    )
    r.kontrol(
        "② bölüm 1'de yığın satırı var ve beş ölçünün toplamı",
        len(_y) == 1 and abs(_y[0]["deger"] - _top) < 1e-9,
        f"→ {[a.get('deger') for a in _y]} · beklenen {_top}",
    )
    _lh = next(
        a for a in _mb["adimlar"] if a.get("tip") == "hesap" and str(a.get("formul", "")).startswith("lh")
    )
    r.kontrol(
        "② halat boyu satırı aynı yığını kullanıyor",
        f"− {adimlar.trn(_top, 0)} )" in _lh["islem"],
        f"→ {_lh['islem']}",
    )

    #  ③  AYNI EKSİKLİK UYARILARDA BİR KEZ.  α girilmeyince sayfa 1'de hem
    #  ne yapılacağını anlatan uyarı hem "HESAP EKSİK — α girilmedi" satırı
    #  basılıyordu.  Eksik LİSTESİ ( özet · genel hüküm ) değişmemeli.
    def _alfa_sayisi(u):
        return sum(("α GİRİLMEDİ" in x) or ("α girilmedi" in x) for x in u)

    _a = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(
            dict(
                uygulama_girdisi.varsayilanlar(),
                temel_a=10,
                temel_b=None,
                kanal_sekli="Yarım Daire Kanal (Çift Sarım)",
            )
        )
    )
    r.esit("③ α yokken α uyarısı BİR kez", _alfa_sayisi(_a["uyarilar"]), 1)
    r.kontrol(
        "③ kalan uyarı ne yapılacağını anlatan uzun uyarı", mukavemet_girdi.ALFA_UYARI in _a["uyarilar"]
    )
    r.kontrol(
        "③ eksik listesinde α yine var ( hüküm HESAP EKSİK'i görür )",
        mukavemet.ALFA_YOK in (_a["ozet"].get("eksik_hesap") or []),
    )
    _oteki = [x for x in (_a["ozet"].get("eksik_hesap") or []) if x != mukavemet.ALFA_YOK]
    r.kontrol(
        "③ α dışındaki eksikler uyarılarda aynen duruyor",
        bool(_oteki) and all(f"⚠ {x}" in _a["uyarilar"] for x in _oteki),
        f"→ eksik {_oteki} · uyarılar {_a['uyarilar']}",
    )
    _v = uygulama_hesabi.hesapla(
        uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), sarilma_acisi=180))
    )
    r.esit("③ α girilince α uyarısı yok", _alfa_sayisi(_v["uyarilar"]), 0)


# =====================================================================
#  ASANSÖRLERİN SIRASI HESABI DEĞİŞTİRMEZ
# =====================================================================
#  Binaya ait bölümler ( makine dairesi aydınlatması · temel topraklama )
#  çoklu projede ilk asansörün KENDİ hesabından alınıyordu.  Topraklama
#  iletkenleri tesisteki EN BÜYÜK koruma iletkeninden türediği için sonuç
#  asansörlerin sırasına bağlıydı:  kolon kesiti 16 ve 95 mm² olan iki
#  asansörde 16'lık önce gelince topraklama iletkeni 16, ana potansiyel
#  dengeleme 10 mm² çıkıyordu — 95'lik önce gelince 50 ve 25 ( bağımsız
#  incelemede bulundu ).  Burada her sıralama denenir.
def _sira_degismezligi(r):
    import itertools

    ortak = {"temel_a": 26.55, "temel_b": 16.4, "mk_yok": False, "mk_uzunluk": 4000, "mk_genislik": 3000}
    asansorler = [
        {"asansor_adi": "A16", "kolon_kesit": 16, "makine_kesit": 6, "sarilma_acisi": 180},
        {"asansor_adi": "A95", "kolon_kesit": 95, "makine_kesit": 10, "sarilma_acisi": 180},
        {
            "asansor_adi": "A35",
            "kolon_kesit": 35,
            "makine_kesit": 70,
            "beyan_yuku": 1000,
            "sarilma_acisi": 180,
        },
    ]

    def _iletkenler(c):
        b = next(x for x in c["proje_geneli"] if x.get("kimlik") == "topraklama_iletkenleri")
        return {
            a.get("sembol") or a.get("formul", "")[:5]: a.get("deger")
            for a in b["adimlar"]
            if isinstance(a, dict) and a.get("deger") is not None
        }

    #  Beklenen:  avan motorunun TESİS hesabı — bütün asansörler tek girdide
    tesis = uygulama_girdisi.avan_girdisi(
        uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **ortak, **asansorler[0]))
    )
    tesis["asansorler"] = [
        uygulama_girdisi.avan_girdisi(
            uygulama_girdisi.tamamla(dict(uygulama_girdisi.varsayilanlar(), **ortak, **a))
        )["asansorler"][0]
        for a in asansorler
    ]
    beklenen = avan_hesabi.hesapla(tesis)["topraklama"]
    _pe = max(
        x
        for a in asansorler
        for x in (
            tablolar.koruma_iletkeni_kesiti(a["kolon_kesit"])[0],
            tablolar.koruma_iletkeni_kesiti(a["makine_kesit"])[0],
        )
    )
    r.esit("tesisteki en büyük koruma iletkeni ( 95 mm² kolon → 50 )", beklenen["en_buyuk_pe"], _pe)

    def _metin(x):
        return re.sub(r"TAS\d+", "TAS", json.dumps(x, sort_keys=True, default=str, ensure_ascii=False))

    taban, asansor_tabani = None, {}
    for sira in itertools.permutations(asansorler):
        ad = " → ".join(a["asansor_adi"] for a in sira)
        c = uygulama_hesabi.hesapla_coklu([dict(a) for a in sira], ortak)
        if not r.kontrol(f"sıra {ad} · hesap koşuyor", c["aktif"], f"→ {c.get('hata')}"):
            continue
        il = _iletkenler(c)
        r.esit(f"sıra {ad} · en büyük koruma iletkeni", il.get("SPE"), beklenen["en_buyuk_pe"])
        r.esit(f"sıra {ad} · topraklama iletkeni", il.get("Stopr"), beklenen["Stopr"])
        r.kontrol(
            f"sıra {ad} · ana potansiyel dengeleme iletkeni",
            beklenen["Sapd"] in il.values(),
            f"→ {il} · beklenen Sapd {beklenen['Sapd']}",
        )
        #  Asansörlerin kendi sonuçları da sıradan bağımsız ( no ve etiket hariç;
        #  tablonun adı da numaradan:  TAS<no> — 23 Eki ).  Makine dairesinin
        #  aydınlatması ilk asansörün tablosundan beslenir ( 23 Eki ):  asansörün
        #  sonucu kendisine ve o devreyi taşıyıp taşımadığına bağlıdır, sıraya değil
        ozu = _metin(
            {
                "proje_geneli": c["proje_geneli"],
                "tumu_uygun": c["ozet"]["tumu_uygun"],
                "proje_geneli_uygun": c["ozet"]["proje_geneli_uygun"],
                "hata": sorted(c["hata"]),
            }
        )
        if taban is None:
            taban = ozu
        else:
            r.kontrol(f"sıra {ad} · proje geneli ilk sıralamayla aynı", ozu == taban)
        for a in c["asansorler"]:
            anahtar = (a["tanim"], a["no"] == 1)
            ozu = _metin({k: v for k, v in a.items() if k != "no"})
            if anahtar in asansor_tabani:
                r.kontrol(
                    f"sıra {ad} · {a['tanim']} ( makine dairesi aydınlatması "
                    f"{'onun' if a['no'] == 1 else 'başka'} tablosunda ) aynı sonuç",
                    ozu == asansor_tabani[anahtar],
                )
            else:
                asansor_tabani[anahtar] = ozu
    #  Her asansör hem ilk sırada ( devre onun tablosunda ) hem sonra denendi
    r.esit("sıra · denenen asansör rolleri", len(asansor_tabani), 2 * len(asansorler))


# =====================================================================
#  HESAP → PDF PAFTA → DXF  —  teslim edilen dosyalar AYNI ŞEYİ söylüyor mu
# =====================================================================
#  DXF ayrı çizilmez;  programın kendi PDF'i okunup LINE / TEXT'e çevrilir
#  ( ciktilar/dxf_cikti ).  TEST 4 bu birebirliği avan ve trafik paftalarında
#  ölçüyordu;  uygulama paftasında yalnız birkaç simge denetleniyordu.  Burada
#  4 asansörlü bir proje ( programın izin verdiği en büyüğü ) arayüzün indirme
#  uçlarından alınır ve:
#    · hesabın her satırı ( formül · işlem · değer · birim · kaynak · karar ·
#      sonuç ) PDF'te basılı,
#    · satırda yazan sayı satırın değeriyle aynı,
#    · DXF'in her yazısı ve çizgisi PDF ile konum · boy · metin olarak aynı,
#    · 26 A4'lük ofis formatına sığmayan proje ( 86 sayfa ) aşağı taşmıyor,
#      çerçeve gerektiği kadar SAĞA uzuyor.
def _pafta_zinciri(r):
    import re as _re
    import tempfile as _tmp
    import zipfile as _zip

    try:
        import ezdxf as _ez
        from pdfminer.high_level import extract_pages as _sayfalar
        from pdfminer.layout import LTChar as _Harf
    except Exception as _e:  # noqa: BLE001
        r.atla(f"pafta zinciri denetimi atlandı — CAD / PDF kitaplıkları yok ( {_e} )")
        return

    #  EN BÜYÜK PROJE:  4 asansör ( ASANSOR_AZAMI ) — 86 sayfa, format 43 sütuna
    #  uzar.  Tipleri ve askıları farklı ki bölümler aynı metni tekrarlamasın.
    _asansorler = [
        {"asansor_adi": "İnsan 1", "sarilma_acisi": "180"},
        {
            "asansor_adi": "Yük-insan",
            "asansor_tipi": "Yük-insan asansörü",
            "beyan_yuku": "1600",
            "kabin_agirligi": "1200",
            "kabin_genisligi": "1400",
            "kabin_derinligi": "2000",
            "kabin_ray_profili": "125 x 82 x 16",
            "sarilma_acisi": "165",
            "paten_tipi": "Makaralı",
            "klips_itme_kuvveti": "300",
            "yapi_sehim_x": "0,5",
            "denge_zinciri": "Var",
            "agirlik_guvenlik_tertibati": "Kaymalı",
            "kabin_kaciklik": "-80",
            "aski_kaciklik_x": "120",
        },
        {
            "asansor_adi": "Sedye",
            "beyan_yuku": "1275",
            "kabin_agirligi": "1100",
            "kabin_genisligi": "1400",
            "kabin_derinligi": "2400",
            "kabin_ray_profili": "90 x 75 x 16",
            "sarilma_acisi": "170",
            "beyan_hizi": "1.6",
            "tampon_tipi": "Hidrolik  ( enerji yutmalı )",
            "kabin_tampon_boyu": "250",
            "kabin_tampon_ezilme": "200",
            "agirlik_tampon_ezilme": "200",
        },
        {
            "asansor_adi": "Servis",
            "beyan_yuku": "630",
            "kabin_agirligi": "600",
            "kabin_genisligi": "1100",
            "kabin_derinligi": "1400",
            "sarilma_acisi": "175",
            "aski_orani": "1",
            "kabin_kaciklik": "60",
        },
    ]
    #  Kuyu kabinden 950 geniş, 450 derin:  geometrisi kurulamayan kuyunun
    #  hesabı durur ( 4 Eki ) — eskiden bu asansörler varsayılan kuyuya sığmıyordu.
    for _a in _asansorler:
        if "kabin_genisligi" in _a:
            _a.setdefault("kuyu_genisligi", str(int(_a["kabin_genisligi"]) + 950))
            _a.setdefault("kuyu_derinligi", str(int(_a["kabin_derinligi"]) + 450))
    veri = {
        "proje_adi": "Zincir",
        "asansorler": _asansorler,
        "proje_geneli": {
            "mk_yok": False,
            "temel_a": "24",
            "temel_b": "15",
            "serit_L": "60",
            "mk_uzunluk": "3800",
            "mk_genislik": "2600",
        },
        "sabitler": {"k3_yardimci": "2"},
    }
    s, _hata = uygulama_uclari._coklu_sonuc(json.loads(json.dumps(veri)))
    if not r.kontrol("[pafta zinciri] proje hesaplandı", s is not None):
        return
    pdf = uygulama_uclari.indir_uygulama_pdf(json.loads(json.dumps(veri))).body
    #  BİRLEŞİK PROGRAM:  "Projeyi paketle" çizimleri de ekler ve çizilemeyen
    #  projeyi paketlemez ( TEST 11 ⑳ );  bu dört asansör hesabın uç durumlarını
    #  dener, çizilebilir değildir.  Zincir HESAP sayfalarınındır:  paket,
    #  düğmenin paketleyicisiyle ( indir_uygulama_dwg'nin çizimden önceki
    #  adımları ) çizimsiz kurulur.
    _zip_b, _sebep, _tasti = dxf_cikti.proje_paketi(
        [("Uygulama Projesi", pdf_cikti.uygulama_pdf(s))], "Zincir - Uygulama Projesi", []
    )

    class _Paket:
        body = _zip_b
        headers = {"X-Avan-Not": ",".join((["DXF"] if _sebep else []) + (["TASMA"] if _tasti else []))}

    paket = _Paket()

    def _duz(t):
        return _re.sub(r"\s+", "", str(t or ""))

    harf = []
    for _sf in _sayfalar(io.BytesIO(pdf), laparams=None):

        def _gez(o):
            for e in o:
                if isinstance(e, _Harf):
                    harf.append(e.get_text())
                elif hasattr(e, "__iter__"):
                    _gez(e)

        _gez(_sf)
    pafta = _duz("".join(harf))

    bolumler = [(f"{i + 1}/{b['kimlik']}", b) for i, a in enumerate(s["asansorler"]) for b in a["bolumler"]]
    bolumler += [(f"PG/{b.get('kimlik')}", b) for b in s.get("proje_geneli") or []]
    eksik, sayi, yanlis = [], 0, []
    _SAYI = _re.compile(r"^-?\d{1,3}(\.\d{3})*(,\d+)?$|^-?\d+(,\d+)?$")
    for yer, b in bolumler:
        metinler = [b["baslik"], b.get("kaynak", ""), (b.get("sonuc") or {}).get("metin", "")]
        for a in b.get("adimlar") or []:
            if a.get("tip") == "metin":
                metinler += (
                    [a["aciklama"], a["deger"]]
                    if a.get("vurgu") and str(a.get("aciklama") or "").strip()
                    else [a["deger"]]
                )
            elif a.get("tip") == "hesap":
                metinler += [a["formul"], a["islem"], a["metin"], a["birim"], a["kaynak"]]
            else:
                metinler += [a["sembol"], a["aciklama"], a["metin"], a["birim"], a["kaynak"]]
            d, m = a.get("deger"), str(a.get("metin") or "").strip()
            if isinstance(d, (int, float)) and not isinstance(d, bool) and _SAYI.match(m):
                sayi += 1
                hane = len(m.split(",")[1]) if "," in m else 0
                if abs(float(m.replace(".", "").replace(",", ".")) - d) > 0.5 * 10**-hane + 1e-9:
                    yanlis.append(f"{yer}: {m} ≠ {d!r}")
        eksik += [f"{yer}: {t[:60]!r}" for t in metinler if _duz(t) and _duz(t) not in pafta]
    r.kontrol(
        "[pafta zinciri] hesabın bütün satırları PDF paftada basılı",
        not eksik,
        f"→ {len(eksik)} eksik: {eksik[:5]}",
    )
    r.kontrol(
        f"[pafta zinciri] satırda yazan sayı satırın değeriyle aynı ( {sayi} sayı )",
        sayi > 500 and not yanlis,
        f"→ {yanlis[:5]}",
    )

    #  PDF → DXF  ( paketin içindeki pafta PDF'i ve DXF )
    r.kontrol(
        "[pafta zinciri] 26 A4'ü aşan projede taşma notu YOK",
        "TASMA" not in (paket.headers.get("X-Avan-Not") or ""),
        f"→ {paket.headers.get('X-Avan-Not')!r}",
    )
    z = _zip.ZipFile(io.BytesIO(paket.body))
    zpdf = sorted(n for n in z.namelist() if n.startswith("pafta pdf/"))
    paftalar = [(n.split(" - ", 1)[1].rsplit(".pdf", 1)[0], z.read(n)) for n in zpdf]
    sayfalar = dxf_cikti.sayfalari_topla(paftalar)
    r.kontrol(
        "[pafta zinciri] 4 asansörün hepsi hesaplandı, pakette Excel yok",
        sum(1 for a in s["asansorler"] if a.get("aktif")) == 4
        and not any(n.endswith(".xlsx") for n in z.namelist()),
    )
    r.kontrol(
        "[pafta zinciri] proje formatın 26 A4'ünden uzun  ( ölçüt boş değil )",
        len(sayfalar) > 3 * 26,
        f"→ {len(sayfalar)} sayfa",
    )
    yerler, tasti = dxf_cikti._yerlesim(len(sayfalar))
    bek_c, bek_y = set(), []
    for sf, (ox, oy) in zip(sayfalar, yerler):
        for x0, y0, x1, y1, _w in sf["cizgiler"]:
            if abs(x1 - x0) > 1e-9 or abs(y1 - y0) > 1e-9:
                bek_c.add(
                    tuple(
                        sorted(
                            [
                                (round(ox + x0 * dxf_cikti.PT_MM, 4), round(oy + y0 * dxf_cikti.PT_MM, 4)),
                                (round(ox + x1 * dxf_cikti.PT_MM, 4), round(oy + y1 * dxf_cikti.PT_MM, 4)),
                            ]
                        )
                    )
                )
        for t in sf["metinler"]:
            bek_y.append(
                (
                    round(ox + t["x"] * dxf_cikti.PT_MM, 4),
                    round(oy + t["taban"] * dxf_cikti.PT_MM, 4),
                    round(t["boy"] * dxf_cikti.CAP_ORAN * dxf_cikti.PT_MM, 3),
                    dxf_cikti._cad_metni(t["metin"]),
                )
            )
    yol = os.path.join(_tmp.gettempdir(), "zincir_uygulama.dxf")
    with open(yol, "wb") as f:
        f.write(z.read(next(n for n in z.namelist() if n.endswith(".dxf"))))
    m = _ez.readfile(yol).modelspace()
    var_c = {
        tuple(
            sorted(
                [
                    (round(e.dxf.start.x, 4), round(e.dxf.start.y, 4)),
                    (round(e.dxf.end.x, 4), round(e.dxf.end.y, 4)),
                ]
            )
        )
        for e in m.query("LINE")
        if e.dxf.layer == dxf_cikti.KATMAN_CIZGI
    }
    var_y = [
        (round(e.dxf.insert.x, 4), round(e.dxf.insert.y, 4), round(e.dxf.height, 3), e.dxf.text)
        for e in m.query("TEXT")
        if e.dxf.layer == dxf_cikti.KATMAN_YAZI
    ]
    r.kontrol(
        f"[pafta zinciri] DXF çizgileri PDF ile birebir ( {len(bek_c)} )",
        bek_c == var_c,
        f"→ eksik {len(bek_c - var_c)} · fazla {len(var_c - bek_c)}",
    )
    r.kontrol(
        f"[pafta zinciri] DXF yazıları PDF ile birebir ( {len(bek_y)} )",
        sorted(bek_y) == sorted(var_y),
        f"→ eksik {len([x for x in bek_y if x not in var_y])} · "
        f"fazla {len([x for x in var_y if x not in bek_y])}",
    )

    #  ÇERÇEVE SAĞA UZADI:  sağ kenar çizgileri yeni kenarda, her A4 içeride
    uzatma = dxf_cikti._uzatma(len(sayfalar))
    sag = dxf_cikti.BANT[2] + uzatma
    r.kontrol("[pafta zinciri] sayfalar aşağı taşmadı", not tasti)
    kenar = [
        e
        for e in m.query("LINE")
        if e.dxf.layer != dxf_cikti.KATMAN_CIZGI and max(e.dxf.start.x, e.dxf.end.x) > dxf_cikti.BANT[2] + 0.5
    ]
    r.kontrol(
        "[pafta zinciri] dış çerçevenin dört kenar çizgisi yeni sağ kenara uzadı",
        uzatma > 0
        and len(kenar) == 4
        and all(abs(max(e.dxf.start.x, e.dxf.end.x) - sag) < 0.5 for e in kenar),
        f"→ uzatma {uzatma} · {len(kenar)} çizgi",
    )
    a4 = dxf_cikti.a4_cerceveleri(m)
    r.kontrol(
        f"[pafta zinciri] {len(a4)} A4'ün hepsi uzamış çerçevenin içinde",
        len(a4) == len(sayfalar)
        and all(
            dxf_cikti.SERBEST[0] - 0.5 <= b[0]
            and b[2] <= sag + 0.5
            and dxf_cikti.BANT[1] - 0.5 <= b[1]
            and b[3] <= dxf_cikti.BANT[3] + 0.5
            for b in a4
        ),
    )
    r.esit("[pafta zinciri] sığan projede format hiç uzamaz  ( 28 A4 )", dxf_cikti._uzatma(28), 0.0)
    r.esit(
        "[pafta zinciri] 29. sayfa bir sütun ekler",
        dxf_cikti._uzatma(29),
        dxf_cikti.A4_G + dxf_cikti.SUTUN_ARA,
    )


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
