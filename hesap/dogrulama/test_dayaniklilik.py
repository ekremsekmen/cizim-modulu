# -*- coding: utf-8 -*-
"""
TEST 3  —  GİRDİ DAYANIKLILIĞI VE API SÖZLEŞMESİ

Program hiçbir girdide çökmemeli; anlamsız girdide anlaşılır hata döndürmeli.
Sunucu ayakta değilse HTTP bölümü atlanır, motor bölümü yine çalışır.
"""

import json
import os
import sys
import urllib.error
import urllib.request

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import yollar

yollar.kur()

from motor.avan import avan_hesabi
from motor.avan import trafik
from dogrulama.rapor import Rapor


#  Uçlar iki pakete ayrıldı ( uclar/avan_uclari.py · uclar/uygulama_uclari.py ), ortak
#  yardımcılar uclar/uc_ortak.py'ye taşındı.  Test onları oradan alır.
from uclar import avan_uclari
from uclar import uc_ortak
from uclar import uygulama_uclari
from motor.uygulama import uygulama_girdisi
from motor.avan import tablolar
from uclar import uygulama_istegi

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8780")

# Kasten bozuk / uç girdiler
KOTU_DEGERLER = [
    "",
    "   ",
    None,
    "abc",
    "1,2,3",
    "-5",
    "0",
    "1e400",
    "NaN",
    "Infinity",
    "٣",
    "１０",
    "3٫5",
    "<script>alert(1)</script>",
    "'; DROP TABLE x;--",
    "=1+1",
    "9" * 60,
    "1.234.567,89",
    "1,234,567.89",
    "1 234,5",
    "٫",
    "—",
    "\n\t",
    "3,,5",
    ",5",
    "5,",
    "+3",
    "%50",
    "3 m",
    True,
    False,
    [],
    {},
    0,
    -1,
]


def calistir():
    print("\n\033[1mTEST 3 — GİRDİ DAYANIKLILIĞI VE API SÖZLEŞMESİ\033[0m")
    r = Rapor("Dayanıklılık")

    # ------------------------------------------------ sayı ayrıştırma
    for metin, bek in (
        ("1,60", 1.6),
        ("1.60", 1.6),
        ("1,234.56", 1234.56),
        ("1.234,56", 1234.56),
        ("  3  ", 3),
        ("", None),
        ("abc", None),
        (None, None),
        ("-2,5", -2.5),
        ("0,075", 0.075),
        (12, 12),
        (3.0, 3),
    ):
        r.esit(f"_sayi({metin!r})", uc_ortak._sayi(metin), bek)
    r.kontrol("_sayi(True) sayı sayılmaz", uc_ortak._sayi(True) in (None, 1))

    # ------------------------------------------------ motor: her kötü değer her alanda
    ALANLAR = (
        "bina_yuksekligi",
        "yapi_yuksekligi",
        "N",
        "hizli1",
        "hizli2",
        "h",
        "P",
        "kapi_genisligi",
        "manuel_k",
        "manuel_V",
        "manuel_adet",
    )
    TEMEL = dict(
        bina_tipi="Konut",
        bina_yuksekligi="39,98",
        yapi_yuksekligi="43",
        N="11",
        h="3",
        hizli1="44",
        hizli2="3",
        P="10",
        kapi_genisligi="900",
        kapi_tipi="Merkezden Açılan Oto.",
    )
    cokme = 0
    for alan in ALANLAR:
        for kotu in KOTU_DEGERLER:
            veri = dict(TEMEL)
            veri[alan] = kotu
            try:
                g = avan_uclari._trafik_girdi({"girdiler": veri})
                s = trafik.hesapla_tek(g)
                if not isinstance(s, dict):
                    cokme += 1
            except Exception as e:  # noqa: BLE001
                cokme += 1
                r.kontrol(f"tek/{alan}={kotu!r} çökme", False, f"→ {type(e).__name__}: {e}")
    r.kontrol(
        f"tek asansör: {len(ALANLAR) * len(KOTU_DEGERLER)} bozuk girdi kombinasyonu çökmedi", cokme == 0
    )

    # bina tipi ve kapı tipi metin alanları
    for kotu in ("", None, "Konut ", "konut", "<b>x</b>", "Yok", 5, ["Konut"]):
        try:
            g = avan_uclari._trafik_girdi({"girdiler": dict(TEMEL, bina_tipi=kotu)})
            s = trafik.hesapla_tek(g)
            r.kontrol(f"bina_tipi={kotu!r} anlamlı hata", isinstance(s, dict))
        except Exception as e:  # noqa: BLE001
            r.kontrol(f"bina_tipi={kotu!r} çökme", False, f"→ {e}")
    for kotu in ("", None, "Teleskopik", "yok", 7):
        try:
            g = avan_uclari._trafik_girdi({"girdiler": dict(TEMEL, kapi_tipi=kotu)})
            r.kontrol(f"kapi_tipi={kotu!r} çökmedi", isinstance(trafik.hesapla_tek(g), dict))
        except Exception as e:  # noqa: BLE001
            r.kontrol(f"kapi_tipi={kotu!r} çökme", False, f"→ {e}")

    # ------------------------------------------------ çoklu: bozuk asansör listeleri
    C = dict(
        bina_tipi="Konut",
        bina_yuksekligi="39,98",
        yapi_yuksekligi="43",
        N="11",
        h="3",
        hizli1="44",
        hizli2="3",
    )
    for asl in (
        [],
        [{}],
        [{"P": ""}],
        [{"P": "abc"}],
        [{"P": "10"}] * 8,  # 4'ten fazla
        [{"P": "10", "kapi_genisligi": "yok", "kapi_tipi": None}],
        [{"P": "10", "durak": "-3"}],
        [{"P": "10", "V": "9"}],
        [{"P": "10", "h": "0"}],
        [{"P": "99"}],
    ):
        try:
            g = avan_uclari._trafik_girdi({"girdiler": dict(C, asansorler=asl)})
            r.kontrol(f"çoklu asansorler={str(asl)[:38]} çökmedi", isinstance(trafik.hesapla_coklu(g), dict))
        except Exception as e:  # noqa: BLE001
            r.kontrol(f"çoklu asansorler={str(asl)[:38]} çökme", False, f"→ {e}")

    #  Kapasitesiz sütun atılınca iletiler ekrandaki sütun numarasıyla ( 21 Eki:
    #  boş 1. sütunda 3. sütunun hatası "ASANSÖR-2" diyordu )
    _iyi = {"P": "8", "kapi_genisligi": "800", "kapi_tipi": "Merkezden Açılan Oto."}
    _s = trafik.hesapla(
        avan_uclari._trafik_girdi(
            {"girdiler": dict(C, asansorler=[{}, _iyi, dict(_iyi, P="10", kapi_genisligi="850")])}
        )
    )
    r.kontrol(
        "boş sütundan sonra ileti ekrandaki numarayla",
        "ASANSÖR-3 —" in str(_s.get("hata")),
        f"→ {_s.get('hata')}",
    )
    r.esit(
        "boş sütundan sonra asansör adları ekrandaki numarayla",
        [a["ad"] for a in _s.get("asansorler") or []],
        ["ASANSÖR-2", "ASANSÖR-3"],
    )

    # ------------------------------------------------ avan: bozuk girdiler
    A = dict(
        aktif=True,
        tanim="A",
        kapasite="10",
        V="1.6",
        eta="0,85",
        Hk="32,85",
        kuyu_genisligi="1800",
        kabin_boyu="1450",
        kabin_genisligi="1300",
        gr="17,91",
        Fmk="350",
        Fsh="100",
        Nsc="11",
        S1="6",
        L1="32,85",
        S2="6",
        L2="3",
        kablo_tipi="NHXMH FE180",
    )
    O = dict(
        U="380",
        kappa="56",
        eps_max="3",
        temel_a="26,55",
        temel_b="16,4",
        beta="150",
        serit_L="58,5",
        cubuk_sayisi="4",
        mk_uzunluk="0",
        mk_genislik="0",
    )
    AVAN_ALAN = (
        "kapasite",
        "V",
        "eta",
        "Hk",
        "kuyu_genisligi",
        "kabin_boyu",
        "kabin_genisligi",
        "gr",
        "Fmk",
        "Fsh",
        "Nsc",
        "S1",
        "L1",
        "S2",
        "L2",
        "Q_elle",
        "Gk_elle",
    )
    cokme = 0
    for alan in AVAN_ALAN:
        for kotu in KOTU_DEGERLER:
            try:
                v = avan_uclari._avan_girdi(
                    {"girdiler": {"ortak": O, "asansorler": [dict(A, **{alan: kotu})], "sabitler": {}}}
                )
                s = avan_hesabi.hesapla(v)
                if not isinstance(s, dict):
                    cokme += 1
            except Exception as e:  # noqa: BLE001
                cokme += 1
                r.kontrol(f"avan/{alan}={kotu!r} çökme", False, f"→ {type(e).__name__}: {e}")
    r.kontrol(f"avan: {len(AVAN_ALAN) * len(KOTU_DEGERLER)} bozuk girdi kombinasyonu çökmedi", cokme == 0)

    # ortak girdiler
    cokme = 0
    for alan in O:
        for kotu in KOTU_DEGERLER:
            try:
                v = avan_uclari._avan_girdi(
                    {"girdiler": {"ortak": dict(O, **{alan: kotu}), "asansorler": [A], "sabitler": {}}}
                )
                avan_hesabi.hesapla(v)
            except Exception as e:  # noqa: BLE001
                cokme += 1
                r.kontrol(f"avan/ortak.{alan}={kotu!r} çökme", False, f"→ {e}")
    r.kontrol(f"avan ortak girdiler: {len(O) * len(KOTU_DEGERLER)} kombinasyon çökmedi", cokme == 0)

    # sabitler (ofis standardı) bozulursa
    cokme = 0
    for alan in avan_hesabi.SABIT_B_VARSAYILAN:
        for kotu in ("", "abc", "0", "-1", "999999"):
            try:
                v = avan_uclari._avan_girdi(
                    {"girdiler": {"ortak": O, "asansorler": [A], "sabitler": {alan: kotu}}}
                )
                avan_hesabi.hesapla(v)
            except Exception as e:  # noqa: BLE001
                cokme += 1
                r.kontrol(f"sabit {alan}={kotu!r} çökme", False, f"→ {e}")
    r.kontrol("bozuk ofis standardı değerleri çökmedi", cokme == 0)

    # ------------------------------------------------ ofis standardı SESSİZCE varsayılana dönmez
    #  Avan tarafı her değere _sayi() uyguluyordu:  β = "1.200" ve "abc" hata
    #  vermeden 150'ye dönüyor, kablo tipine yazılan "NYY" NHXMH FE180 oluyordu
    #  ( bağımsız incelemede bulundu:  1200 yazan kullanıcının topraklama
    #  direnci 4,83 yerine 38,61 Ω olmalıydı ).
    def _avan(sb):
        #  β ortak alanda boş:  ofis standardındaki değer kullanılsın
        return json.loads(
            avan_uclari.api_avan(
                {"girdiler": {"ortak": dict(O, beta=""), "asansorler": [A], "sabitler": sb}}
            ).body
        )

    def _uyg(sb=None, asansor=None, pg=None):
        return json.loads(
            uygulama_uclari.api_uygulama_coklu(
                {
                    "asansorler": [dict({"sarilma_acisi": "180"}, **(asansor or {}))],
                    "proje_geneli": pg if pg is not None else {"mk_yok": True},
                    "sabitler": sb or {},
                }
            ).body
        )

    _re_150, _re_1200 = _avan({})["ozet"]["Re"], _avan({"beta": "1200"})["ozet"]["Re"]
    r.kontrol("avan · β = 1200 hesaba giriyor", _re_1200 > _re_150 * 5, f"→ {_re_150} · {_re_1200}")
    for proje, kos in (("avan", _avan), ("uygulama", _uyg)):
        for ham, beklenen in (("1.200", "Belirsiz sayı"), ("abc", "kabul edilmedi")):
            h = kos({"beta": ham}).get("hata")
            h = " ".join(h) if isinstance(h, list) else str(h or "")
            r.kontrol(
                f"{proje} · ofis standardında β = {ham!r} sessizce varsayılana dönmüyor",
                beklenen in h,
                f"→ {h[:120]!r}",
            )
    r.esit(
        "avan · metin sabiti ( kablo tipi ) metin kalıyor",
        avan_uclari._avan_girdi(
            {"girdiler": {"ortak": O, "asansorler": [A], "sabitler": {"kablo_tipi": "NYY"}}}
        )["sabitler"].get("kablo_tipi"),
        "NYY",
    )
    r.esit(
        "uygulama · metin sabiti ( kablo tipi ) metin kalıyor",
        uygulama_istegi.asansor_girdileri(
            {"asansorler": [{}], "proje_geneli": {}, "sabitler": {"kablo_tipi": "NYY"}}
        )[0][0]["_ofis"].get("kablo_tipi"),
        "NYY",
    )

    # ------------------------------------------------ okunamayan yazım BOŞ SAYILMAZ
    #  _temiz yalnız belirsiz yazımı ( "1.200" ) yakalıyordu:  anma yüküne
    #  "1000 kg" yazılınca değer sessizce boşa düşüyor, motor Tablo-7'deki yükle
    #  hesap yapıyordu.  Ofis sekmesi bunu zaten reddediyordu;  artık asansör
    #  kartı, trafik formu ve uygulama formu da aynı kapıdan geçer.
    def _hata(yanit):
        h = json.loads(yanit.body).get("hata")
        return " ".join(h) if isinstance(h, list) else str(h or "")

    for alan, ham in (
        ("Q_elle", "1000 kg"),
        ("Gk_elle", "~800"),
        ("S1", "abc"),
        ("L1", "30m"),
        ("Nsc", "11kW"),
    ):
        h = _hata(
            avan_uclari.api_avan(
                {"girdiler": {"ortak": O, "asansorler": [dict(A, **{alan: ham})], "sabitler": {}}}
            )
        )
        r.kontrol(
            f"avan · {alan} = {ham!r} sessizce boş sayılmıyor",
            "kabul edilmedi" in h and avan_uclari.AVAN_AS_ETIKET[alan] in h,
            f"→ {h[:120]!r}",
        )
    #  Red metni alanı İÇ ADIYLA ( "Q_elle" ) değil kullanıcının gördüğü adla söyler
    r.kontrol(
        "avan · her asansör alanının red metninde görünen bir adı var",
        set(avan_uclari.AVAN_AS_SAYISAL) <= set(avan_uclari.AVAN_AS_ETIKET),
        f"→ adsız: {set(avan_uclari.AVAN_AS_SAYISAL) - set(avan_uclari.AVAN_AS_ETIKET)}",
    )
    r.kontrol(
        "avan · her ortak alanın red metninde görünen bir adı var",
        set(avan_uclari.AVAN_ORTAK_SAYISAL) <= set(avan_uclari.AVAN_ORTAK_ETIKET),
        f"→ adsız: {set(avan_uclari.AVAN_ORTAK_SAYISAL) - set(avan_uclari.AVAN_ORTAK_ETIKET)}",
    )
    #  Anma yükü yazılmış ama okunamıyorsa kolon TANIMSIZ sayılmaz
    h = _hata(
        avan_uclari.api_avan(
            {"girdiler": {"ortak": O, "asansorler": [dict(A, kapasite="", Q_elle="bin kg")], "sabitler": {}}}
        )
    )
    r.kontrol(
        "avan · okunamayan anma yükü kolonu sessizce düşürmüyor",
        "kabul edilmedi" in h and "Q elle — anma yükü" in h,
        f"→ {h[:120]!r}",
    )
    #  Boş kolondaki artık değer projeyi DURDURMAZ ( kolon hesaba girmiyor )
    _bos_kolon = dict(A, kapasite="", S1="abc")
    r.kontrol(
        "avan · tanımsız kolondaki artık değer projeyi durdurmuyor",
        not json.loads(
            avan_uclari.api_avan(
                {"girdiler": {"ortak": O, "asansorler": [A, _bos_kolon], "sabitler": {}}}
            ).body
        ).get("hata"),
    )
    for alan, ham in (("manuel_V", "hızlı"), ("N", "on bir")):
        h = _hata(avan_uclari.api_trafik({"girdiler": dict(TEMEL, **{alan: ham})}))
        r.kontrol(
            f"trafik · {alan} = {ham!r} sessizce boş sayılmıyor",
            "kabul edilmedi" in h and f"{trafik.GIRDI_ETIKET[alan]} = {ham}" in h,
            f"→ {h[:120]!r}",
        )
    #  Trafik red metni de kutuyu EKRANDAKİ adıyla söyler:  "hizli1 = 1.200"
    #  diye bir kutu yoktur.  ⑤ / ⑥ adı bina tipine göre değişir.
    for _bt, _h1, _h2 in (
        ("Konut", "⑤ Daire sayısı", "⑥ Daire başına DİĞER oda sayısı"),
        ("Katlı Otopark", "⑤ Özel amaçlı araç adedi", "⑥ Ticari amaçlı araç adedi"),
        ("Otel (3* ve altı)", "⑤ Toplam yatak sayısı", "⑥"),
    ):
        h = _hata(avan_uclari.api_trafik({"girdiler": dict(TEMEL, bina_tipi=_bt, hizli1="1.200")}))
        r.kontrol(
            f"trafik · {_bt[:14]} · belirsiz ⑤ ekrandaki adıyla",
            f"{_h1} = 1.200" in h and "hizli1" not in h,
            f"→ {h[:120]!r}",
        )
        h = _hata(avan_uclari.api_trafik({"girdiler": dict(TEMEL, bina_tipi=_bt, hizli2="abc")}))
        r.kontrol(
            f"trafik · {_bt[:14]} · okunamayan ⑥ ekrandaki adıyla",
            f"{_h2} = abc" in h and "hizli2" not in h,
            f"→ {h[:120]!r}",
        )
    h = _hata(
        avan_uclari.api_trafik(
            {
                "girdiler": dict(
                    TEMEL,
                    asansorler=[
                        {
                            "P": "10",
                            "kapi_genisligi": "900",
                            "kapi_tipi": "Merkezden Açılan Oto.",
                            "h": "3.000",
                            "durak": "on iki",
                            "manuel_tg": "iki",
                        }
                    ],
                )
            }
        )
    )
    r.kontrol(
        "trafik · asansör kartındaki belirsiz h ekrandaki adıyla",
        "ASANSÖR-1: h — kat yüksekliği = 3.000" in h,
        f"→ {h[:140]!r}",
    )
    h = _hata(
        avan_uclari.api_trafik(
            {
                "girdiler": dict(
                    TEMEL,
                    asansorler=[
                        {
                            "P": "10",
                            "kapi_genisligi": "900",
                            "kapi_tipi": "Merkezden Açılan Oto.",
                            "durak": "on iki",
                            "manuel_tg": "iki",
                        }
                    ],
                )
            }
        )
    )
    r.kontrol(
        "trafik · asansör kartındaki okunamayan alanlar ekrandaki adıyla",
        "ASANSÖR-1: Durak = on iki" in h and "ASANSÖR-1: tg ( imalatçı ) = iki" in h and "manuel_tg" not in h,
        f"→ {h[:160]!r}",
    )
    #  Hiçbir sayısal trafik alanı iç adıyla kalmaz — her bina tipinde
    for _bt in ("", *tablolar.BINA_TIPLERI):
        _ad = trafik.girdi_etiketleri(_bt)
        r.kontrol(
            f"trafik · {_bt[:18] or 'bina tipi boş'} · her bina alanının görünen adı var",
            set(avan_uclari.TRAFIK_SAYISAL) <= set(_ad),
            f"→ adsız: {set(avan_uclari.TRAFIK_SAYISAL) - set(_ad)}",
        )
    r.kontrol(
        "trafik · her asansör kartı alanının görünen adı var",
        set(avan_uclari.ASANSOR_SAYISAL) <= set(trafik.ASANSOR_ETIKET),
        f"→ adsız: {set(avan_uclari.ASANSOR_SAYISAL) - set(trafik.ASANSOR_ETIKET)}",
    )
    #  Arayüz ⑤ / ⑥ etiketini AYNI kaynaktan okur ( /api/secenekler )
    _he = avan_uclari.secenekler()["hizli_etiketleri"]
    r.kontrol(
        "secenekler · ⑤/⑥ etiketi her bina tipi ve boş seçim için var",
        set(_he) == {"", *tablolar.BINA_TIPLERI}
        and all(set(v) == {"hizli1", "hizli2"} for v in _he.values()),
    )
    r.esit(
        "secenekler · Konut ⑤ etiketi motorla aynı",
        tuple(_he["Konut"]["hizli1"]),
        ("⑤ Daire sayısı", "(bağımsız bölüm adedi)"),
    )
    r.kontrol(
        "bozuk bina tipi ( sayı ) etiket kurarken çökmüyor", trafik.hizli_etiketleri(5)["hizli1"][0] == "⑤"
    )
    #  Kişi sayısı okunamayan asansör listeden sessizce düşmüyor
    h = _hata(
        avan_uclari.api_trafik(
            {
                "girdiler": dict(
                    TEMEL,
                    asansorler=[
                        {"P": "10", "kapi_genisligi": "900", "kapi_tipi": "Merkezden Açılan Oto."},
                        {"P": "8 kişi", "kapi_genisligi": "900", "kapi_tipi": "Merkezden Açılan Oto."},
                    ],
                )
            }
        )
    )
    r.kontrol(
        "trafik · okunamayan kişi sayısı asansörü düşürmüyor",
        "kabul edilmedi" in h and "ASANSÖR-2" in h,
        f"→ {h[:120]!r}",
    )
    for alan, ham in (("kabin_agirligi", "abc"), ("kuyu_genisligi", "2400 mm"), ("halat_adedi", "altı")):
        h = " ".join(_uyg(asansor={alan: ham}).get("hata") or [])
        r.kontrol(
            f"uygulama · {alan} = {ham!r} sessizce boş sayılmıyor", "kabul edilmedi" in h, f"→ {h[:120]!r}"
        )

    # ------------------------------------------------ varsayılan BELİRSİZ yazılmamalı
    #  Arayüz varsayılanları kutuya virgüllü yazar ( 2.128 → "2,128" ).  Tek
    #  ayraçtan sonra tam üç rakam belirsiz sayıdır ( binlik mi ondalık mı ) ve
    #  hesabı durdurur:  denge zinciri varsayılanı 2,128 iken ÖRNEK PROJENİN
    #  avan hesabı hiç yapılamıyordu.  Varsayılanlar ve seçim listeleri bu
    #  biçime düşmemeli.
    from motor.uygulama import uygulama_sabitleri, mukavemet_girdi

    def _yaz(x):
        return repr(x).replace(".", ",")

    _vars = {
        "avan SABIT_B": avan_hesabi.SABIT_B_VARSAYILAN,
        "avan OFIS": avan_hesabi.OFIS_VARSAYILAN,
        "uygulama Sabitler": uygulama_sabitleri.VARSAYILAN,
        "uygulama form": {a[0]: a[5] for a in mukavemet_girdi.ALANLAR},
        "uygulama ek": {a[0]: a[5] for a in uygulama_girdisi.EK_ALANLAR},
    }
    _kotu = [
        (ad, k, v)
        for ad, d in _vars.items()
        for k, v in d.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool) and uc_ortak.belirsiz_sayi_mi(_yaz(v))
    ]
    _kotu += [
        ("seçim", a[0], o)
        for a in mukavemet_girdi.ALANLAR
        if a[4]
        for o in a[4]
        if isinstance(o, (int, float)) and not isinstance(o, bool) and uc_ortak.belirsiz_sayi_mi(_yaz(o))
    ]
    r.kontrol("hiçbir varsayılan ya da seçenek belirsiz sayı biçiminde değil", not _kotu, f"→ {_kotu}")

    # ------------------------------------------------ onay alanı TEK okuma kuralı
    #  API'nin kendi kopyası "Var"ı HAYIR, motorun evet_mi'si EVET okuyordu:
    #  aynı kutu ekranda gizlenen alanları bir kurala, hesabı öbür kurala göre
    #  seçiyordu.
    for x in (True, False, None, "", "Var", "Yok", "EVET", "hayır", "on", "1", "0"):
        r.esit(
            f"uygulama · mk_yok = {x!r} API'de ve motorda aynı okunuyor",
            uygulama_istegi.uygulanmayan({"mk_yok": x}),
            uygulama_girdisi.uygulanmayan_alanlar(x),
        )

    # ------------------------------------------------ PROJE GENELİ ALANDA ortak kazanır
    #  Asansörün içinde kalmış eski bir temel ölçüsü binanın topraklamasını
    #  ezmemeli;  API onu okumamalı ( gizli, düzeltilemez ), motor da ortakta
    #  yazan değeri kullanmalı.
    _asl, _ort = uygulama_istegi.asansor_girdileri(
        {
            "asansorler": [{"temel_a": "10"}, {"temel_a": "abc"}],
            "proje_geneli": {"temel_a": "20", "temel_b": "15"},
        }
    )
    r.kontrol(
        "uygulama · asansörün içindeki proje geneli kopya okunmuyor",
        all("temel_a" not in a for a in _asl) and _ort["temel_a"] == 20,
    )
    r.kontrol(
        "uygulama · asansörde kalmış bozuk proje geneli değer projeyi durdurmuyor",
        not uc_ortak._belirsiz_hata(),
    )
    from motor.uygulama import uygulama_hesabi

    _pgs = uygulama_hesabi.hesapla_coklu([{"temel_a": 10, "temel_b": 15}, {}], {"temel_a": 20, "temel_b": 15})
    r.esit(
        "uygulama · motorda da proje geneli alanda ortak kazanıyor",
        [a["girdi"]["temel_a"] for a in _pgs["asansorler"]],
        [20, 20],
    )
    r.esit(
        "uygulama · ortakta olmayan proje geneli alan asansörden alınıyor",
        uygulama_hesabi.hesapla_coklu([{"temel_a": 12, "temel_b": 9}], {})["asansorler"][0]["girdi"][
            "temel_a"
        ],
        12,
    )

    # ------------------------------------------------ gizli alan projeyi durdurmaz
    #  Makine yerleşimine göre ekranda gizlenen bir alanda kalmış değer projeyi
    #  durduruyordu;  kullanıcı gizli alanı göremez, düzeltemez.  Görünen alanda
    #  aynı değer yine reddedilmeli.
    _DAIRELI = {"mk_yok": False, "mk_uzunluk": "4000", "mk_genislik": "3000"}
    for ad, asansor, pg, gecerli in (
        ("MRL · makine dairesi ölçüsü '4.000'", {}, {"mk_yok": True, "mk_uzunluk": "4.000"}, True),
        ("MRL · makine dairesi ölçüsü '-5'", {}, {"mk_yok": True, "mk_uzunluk": "-5"}, True),
        ("MRL · dikine kiriş 'x'", {"dikine_kiris": "x"}, {"mk_yok": True}, True),
        (
            "MRL · tabliye beton yüksekliği '1.200' ( gizli )",
            {"tabliye_yuksekligi": "1.200"},
            {"mk_yok": True},
            True,
        ),
        #  Makine kirişi MRL'de de sorulur ve hesaplanır:  görünen alan.
        ("MRL · yan yatak ölçüsü 'x' ( görünür )", {"yan_yatak": "x"}, {"mk_yok": True}, False),
        (
            "daireli · tabliye beton yüksekliği '1.200' ( görünür )",
            {"tabliye_yuksekligi": "1.200"},
            _DAIRELI,
            False,
        ),
        (
            "daireli · makine yükü yolu 'Kılavuz raylara' ( gizli )",
            {"makine_raya_biniyor": "Kılavuz raylara"},
            _DAIRELI,
            True,
        ),
        (
            "daireli · makine dairesi ölçüsü '4.000' ( görünür )",
            {},
            dict(_DAIRELI, mk_uzunluk="4.000"),
            False,
        ),
        ("daireli · yan yatak ölçüsü 'x' ( görünür )", {"yan_yatak": "x"}, _DAIRELI, False),
        #  Kirişin açıklığı formda yok ( çizimden ):  eski projede yazılı olsa da okunmaz
        ("daireli · yan yatak boyu '1.400' ( formda yok )", {"yan_yatak_boyu": "1.400"}, _DAIRELI, True),
    ):
        s = _uyg(asansor=asansor, pg=pg)
        r.kontrol(
            f"uygulama · {ad} → {'hesaplanır' if gecerli else 'reddedilir'}",
            bool(s.get("aktif")) is gecerli,
            f"→ {s.get('hata')}",
        )
    _gizli = uygulama_girdisi.arayuz_alanlari()["yerlesime_gore_gizli"]
    r.esit(
        "ekranın gizlediği alanlar = motorun hesaba almadığı alanlar ( MRL )",
        set(_gizli["mrl"]),
        uygulama_girdisi.uygulanmayan_alanlar(True),
    )
    r.esit(
        "ekranın gizlediği alanlar = motorun hesaba almadığı alanlar ( daireli )",
        set(_gizli["daireli"]),
        uygulama_girdisi.uygulanmayan_alanlar(False),
    )

    # ek nüfus satırları
    for ek in (
        [],
        [{}],
        [{"kalem": "yok", "miktar": "5"}],
        [{"kalem": "KONUT — Diğer oda", "miktar": "abc"}],
        [{"kalem": "KONUT — Diğer oda", "miktar": "-5"}],
        [{"kalem": "DOĞRUDAN KİŞİ — Tablo-1 dışı", "miktar": "1000000"}],
        [{"kalem": "KONUT — Diğer oda", "miktar": "1"}] * 30,
    ):
        try:
            g = avan_uclari._trafik_girdi({"girdiler": dict(TEMEL, ek_nufus=ek)})
            r.kontrol(f"ek_nufus={str(ek)[:34]} çökmedi", isinstance(trafik.hesapla_tek(g), dict))
        except Exception as e:  # noqa: BLE001
            r.kontrol(f"ek_nufus={str(ek)[:34]} çökme", False, f"→ {e}")

    # ------------------------------------------------ HTTP uçları
    def istek(yol, govde=None, yontem="POST"):
        veri = json.dumps(govde).encode() if govde is not None else None
        req = urllib.request.Request(
            BASE + yol, data=veri, method=yontem, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as c:
            return c.status, c.read(), dict(c.headers)

    try:
        istek("/api/saglik", yontem="GET")
    except Exception:  # noqa: BLE001
        r.atla(
            f"Sunucu {BASE} adresinde çalışmıyor — HTTP bölümü atlandı "
            "(programı açıkken testi tekrar çalıştırın)."
        )
        return r

    kod, govde, _ = istek("/api/saglik", yontem="GET")
    r.kontrol("/api/saglik 200", kod == 200)
    r.kontrol("sürüm bilgisi var", "surum" in json.loads(govde))

    kod, govde, _ = istek("/api/secenekler", yontem="GET")
    sec = json.loads(govde)
    r.kontrol("/api/secenekler 200", kod == 200)
    for anahtar in (
        "bina_tipleri",
        "kapasiteler",
        "hizlar",
        "kapi_genislikleri",
        "kapi_tipleri",
        "tablo_1",
        "tablo_7",
        "tablo_9",
        "tablo_10",
        "sabit_a",
        "sabit_b",
        "kesitler",
    ):
        r.kontrol(f"secenekler.{anahtar} var", anahtar in sec and sec[anahtar])

    # ana sayfa
    #  Ön yüz derlenmişse ( on-yuz/dist ) React sayfası, değilse 503 ve derleme talimatı
    req = urllib.request.Request(BASE + "/", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as c:
            html = c.read().decode()
    except urllib.error.HTTPError as e:
        html = e.read().decode() if e.code == 503 else ""
    r.kontrol("ana sayfa yüklendi", "<title>" in html and ('id="kok"' in html or "npm run build" in html))

    # bozuk gövdeler — 500 dönmemeli
    for govde in (
        {},
        {"mod": "tek"},
        {"girdiler": {}},
        {"mod": "yok", "girdiler": {}},
        {"mod": "tek", "girdiler": {"bina_tipi": "Yok"}},
        {"mod": "coklu", "girdiler": {"asansorler": "metin"}},
        {"girdiler": {"ortak": None, "asansorler": None}},
        {"girdiler": {"asansorler": [{"aktif": True}]}},
    ):
        for yol in ("/api/trafik", "/api/avan"):
            try:
                kod, cevap, _ = istek(yol, govde)
                r.kontrol(f"{yol} {str(govde)[:30]} → 200", kod == 200)
                r.kontrol(f"{yol} {str(govde)[:30]} → JSON", isinstance(json.loads(cevap), dict))
            except urllib.error.HTTPError as e:
                r.kontrol(f"{yol} {str(govde)[:30]} sunucu hatası", False, f"→ HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                r.kontrol(f"{yol} {str(govde)[:30]} istisna", False, f"→ {e}")

    # indirme uçları bozuk gövdeyle de dosya üretmeli ya da düzgün hata dönmeli
    for yol in ("/api/indir/trafik-pdf", "/api/indir/avan-pdf"):
        for govde in (
            {"mod": "tek", "girdiler": {"bina_tipi": "Konut"}, "proje": {}},
            {"girdiler": {"ortak": {}, "asansorler": []}, "proje": {}},
        ):
            try:
                kod, icerik, basliklar = istek(yol, govde)
                r.kontrol(
                    f"{yol} boş girdide çökmedi",
                    kod == 200 and len(icerik) > 0,
                    f"→ HTTP {kod}, {len(icerik)} bayt",
                )
                #  v2.9 — İKİ KABUL EDİLEBİLİR SONUÇ VAR:
                #    (a) geçerli dosya          — hesap tamamsa
                #    (b) düzgün JSON hata       — hesap reddedildiyse
                #  Kabul EDİLMEYEN:  çökme ya da BOZUK dosya.
                _json_mu = icerik.lstrip()[:1] == b"{"
                if _json_mu:
                    import json as _j

                    r.kontrol(
                        f"{yol} hata gövdesi düzgün JSON",
                        bool(_j.loads(icerik.decode("utf-8")).get("hata")),
                        f"→ {icerik[:80]!r}",
                    )
                else:
                    r.kontrol(f"{yol} geçerli PDF", icerik[:4] == b"%PDF" and len(icerik) > 500)
            except Exception as e:  # noqa: BLE001
                r.kontrol(f"{yol} boş girdi", False, f"→ {e}")

    # ---------------------------------------------------- v1.9: EKRAN = İNDİRME
    #  Belirsiz sayı yazımı ( "1.200" ) ekranda reddediliyordu ama İNDİRME
    #  uçlarının bir kısmı aynı girdiyle dosya üretiyordu:  kullanıcı eksik
    #  girdili bir paftayı teslim edebilir hâlde alıyordu.
    #  Artık her uç aynı kapıdan geçer.
    _BT = dict(TEMEL, P="1.200")
    _BA = {
        "ortak": {"temel_a": "26,55", "temel_b": "16,4", "mk_yok": True},
        "asansorler": [
            {
                "aktif": True,
                "kapasite": "10",
                "V": "1.6",
                "eta": "0,85",
                "Hk": "1.200",
                "makine_tipi": "Dişlisiz",
                "i_palanga": "2",
                "kuyu_genisligi": "1800",
                "kabin_boyu": "1450",
                "kabin_genisligi": "1300",
            }
        ],
        "sabitler": {},
    }
    for _yol, _gov in (
        ("/api/trafik", {"mod": "tek", "girdiler": _BT}),
        ("/api/indir/trafik-pdf", {"mod": "tek", "girdiler": _BT, "proje": {}}),
        ("/api/avan", {"girdiler": _BA}),
        ("/api/indir/avan-pdf", {"girdiler": _BA, "proje": {}}),
    ):
        try:
            _k, _ic, _b = istek(_yol, _gov)
            _hata = ""
            if _ic[:4] != b"%PDF":
                try:
                    _hata = (json.loads(_ic) or {}).get("hata") or ""
                except Exception:  # noqa: BLE001
                    _hata = ""
            r.kontrol(f"{_yol} belirsiz sayıyla DOSYA ÜRETMİYOR", "Belirsiz sayı" in _hata, f"→ {_ic[:40]!r}")
        except Exception as e:  # noqa: BLE001
            r.kontrol(f"{_yol} belirsiz sayı", False, f"→ {e}")
    #  Temiz girdide indirme yine çalışmalı — denetim fazla sıkı olmamalı
    for _yol, _gov, _im in (
        ("/api/indir/trafik-pdf", {"mod": "tek", "girdiler": dict(TEMEL), "proje": {}}, b"%PDF"),
        (
            "/api/indir/avan-pdf",
            {"girdiler": dict(_BA, asansorler=[dict(_BA["asansorler"][0], Hk="38,5")]), "proje": {}},
            b"%PDF",
        ),
    ):
        _k, _ic, _b = istek(_yol, _gov)
        r.kontrol(f"{_yol} temiz girdide yine üretiyor", _ic[: len(_im)] == _im)

    #  EŞ ZAMANLI KULLANICILAR ( web sunucusu ):  reddedilen girdilerin listesi
    #  iş parçacığına özel ( uc_ortak._BELIRSIZ );  havuzun aynı iş parçacığı
    #  sıradaki isteği — başka bir kullanıcınınkini — de koşar.  Bir kullanıcının
    #  belirsiz sayısı ötekinin hesabını reddetmemeli, ötekinin temiz isteği de
    #  ilkinin hatasını silmemeli.
    from concurrent.futures import ThreadPoolExecutor

    _isler = [
        (yol, gov, bozuk)
        for _ in range(12)
        for yol, gov, bozuk in (
            ("/api/trafik", {"mod": "tek", "girdiler": _BT}, True),
            ("/api/trafik", {"mod": "tek", "girdiler": dict(TEMEL)}, False),
            ("/api/avan", {"girdiler": _BA}, True),
            ("/api/avan", {"girdiler": dict(_BA, asansorler=[dict(_BA["asansorler"][0], Hk="38,5")])}, False),
        )
    ]

    def _es_zamanli(is_):
        yol, gov, bozuk = is_
        hata = json.loads(istek(yol, gov)[1]).get("hata") or ""
        return ("Belirsiz sayı" in hata) == bozuk

    with ThreadPoolExecutor(16) as havuz:
        _tutan = sum(havuz.map(_es_zamanli, _isler))
    r.kontrol(
        f"eş zamanlı {len(_isler)} istek:  belirsiz sayı yalnız kendi isteğini reddediyor",
        _tutan == len(_isler),
        f"→ {len(_isler) - _tutan} istek başkasının girdisiyle karıştı",
    )

    # proje adı dosya adına güvenli biçimde geçmeli
    kod, icerik, basliklar = istek(
        "/api/indir/trafik-pdf",
        {
            "mod": "tek",
            "girdiler": dict(TEMEL),
            "proje": {"proje_adi": '../../kötü/ad:*?"<>|  ÇĞİÖŞÜ', "muhendis": "X"},
        },
    )
    cd = basliklar.get("Content-Disposition", "")
    r.kontrol(
        "dosya adında yol ayracı yok", "/" not in cd.split("''")[-1].replace("%2F", "/") or "%2F" not in cd
    )
    r.kontrol("proje adlı PDF üretildi", kod == 200 and icerik[:4] == b"%PDF")

    #  EXCEL UÇLARI KALDIRILDI:  program Excel üretmez ve okumaz.
    for _yol in (
        "/api/indir/trafik-xlsx",
        "/api/indir/avan-xlsx",
        "/api/indir/uygulama-xlsx",
        "/api/xlsx-yukle",
    ):
        try:
            _k, _ic, _b = istek(_yol, {"girdiler": {}})
            r.kontrol(f"{_yol} artık yok", _k in (404, 405), f"→ HTTP {_k}")
        except urllib.error.HTTPError as e:
            r.kontrol(f"{_yol} artık yok", e.code in (404, 405), f"→ HTTP {e.code}")
    try:
        urllib.request.urlopen(BASE + "/api/sablon", timeout=30).read()
        r.kontrol("/api/sablon artık yok", False, "→ uç hâlâ yanıt veriyor")
    except urllib.error.HTTPError as e:
        r.kontrol("/api/sablon artık yok", e.code == 404, f"→ HTTP {e.code}")

    # ---------------------------------------------- PROJE KİMLİĞİ  ( denetim 2.5 )
    #  Kusur:  indirilen her dosya "Asansor - Avan Hesaplari.pdf" adıyla
    #  iniyordu — aynı klasördeki iki projenin dosyaları ayırt edilemiyordu.
    #  Kapak sekmesindeki proje adı artık dosya adına geçer;  paftanın
    #  İÇERİĞİ değişmez.
    _KP = {
        "project_title": "ÇAĞDAŞ KONUTLARI B BLOK",
        "owner": "Örnek Yapı A.Ş.",
        "sheet_no": "EL-04",
        "elec_name": "Ekrem",
        "elec_surname": "Sekmen",
    }
    _pk = uc_ortak._proje_kimligi({"kapak": _KP})
    r.esit("kapak → proje adı", _pk["proje_adi"], "ÇAĞDAŞ KONUTLARI B BLOK")
    r.kontrol(
        "dosya adı proje adıyla başlıyor",
        uc_ortak._dosya_adi(_pk, "Avan Hesaplari", "pdf").startswith("ÇAĞDAŞ KONUTLARI B BLOK"),
    )
    #  kapak gönderilmezse ( eski istemci / boş kapak ) eski davranış sürer
    r.esit(
        "kapaksız istek eski adı verir",
        uc_ortak._dosya_adi(uc_ortak._proje_kimligi({}), "Avan Hesaplari", "pdf"),
        "Asansor - Avan Hesaplari.pdf",
    )
    #  dosya adına yol ayracı / üst dizin sızmamalı
    _kotu = uc_ortak._dosya_adi(
        uc_ortak._proje_kimligi({"kapak": {"project_title": "../../etc/passwd"}}), "Avan Hesaplari", "pdf"
    )
    r.kontrol("dosya adında yol ayracı yok", "/" not in _kotu and ".." not in _kotu, f"→ {_kotu}")
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
