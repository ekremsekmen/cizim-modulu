# -*- coding: utf-8 -*-
"""
TEST 9  —  MUKAVEMET MOTORU  ( uygulama projesi )

Motorun kurallarını tek tek sınar:

  · ÖRNEK PROJE:  ofisin eski mukavemet hesabının örnek projesinde bulduğu
    ara değerler.  Motor bu değerleri hem ara değer olarak ( sonuc["ara"] )
    hem de o bölümün pafta satırlarında aynen üretmelidir.  Standarda göre
    değişen büyüklükler bu listede YOKTUR — onları aşağıdaki kurallar ve
    TEST 10'un referans taraması denetler.
  · Standardın kuralları ( ① … ㊽ ):  her birinin gerçekten uygulandığı.
  · Standardın metnine karşı bağımsız sayılar, girdi doğrulama, hata yolu.
"""

import json
import math
import os
import sys

#  Giriş noktası:  programın kökleri ( depo kökü, hesap/ ) — yollar.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import yollar

yollar.kur()

from motor.uygulama import mukavemet
from cizim import sabitler
from motor.uygulama import mukavemet_tablolari
from motor.uygulama import uygulama_sabitleri
from dogrulama.rapor import P_std as _P_std, Rapor
from motor.uygulama import mukavemet_girdi
from motor.avan import tablolar
from motor.avan import avan_hesabi

#  Ofisin kaynak tablolarından bir kez okunup dondurulan değerler ( ω … )
REFERANS_TABLOLAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referans_tablolar.json")

#  ÖRNEK PROJENİN ARA DEĞERLERİ  —  bölüm kimliği → ( ara değer adı , değer , ne )
#  BÖLÜM İNDEKSİ DEĞİL KİMLİK:  araya yeni bir bölüm girse de değerler doğru
#  bölümde aranır.
ORNEK_PROJE = {
    "motor_gucu": (
        ("motor.Gh", 52.54032, "Gh toplam halat ağırlığı"),
        ("motor.lh", 49.38, "lh halat uzunluğu"),
        ("motor.F1", 1552.54032, "F1 kabin ve aksesuar yükü"),
        ("motor.Ga", 1100, "Ga karşı ağırlık yükü"),
    ),
    "makine_konstruksiyonu": (
        ("makine.F", 57928.8410784, "F kaide üzerindeki en büyük kuvvet"),
        ("makine.F1", 28964.4205392, "F1 yan yatak putreli"),
        ("makine.FB", 22033.648481605716, "FB"),
        ("makine.FA", 6930.772057594284, "FA"),
        ("makine.Mmax", 7381272.241337912, "Mmax"),
        ("makine.sigma_e", 121.60250809452903, "σe eğilme gerilmesi"),
    ),
    "aski_halatlari": (
        ("aski.oran", 36.92307692307692, "Dt / dh"),
        #  D2 boş — ÇİZİMDEN ( birleşik program ):  iki kabin kasnağı ø240 ve
        #  karşı ağırlık kasnağı ø400 ( referans proje );  ( 240 + 240 + 400 ) / 3
        #  = 293,3  →  Kp = ( 240 / 293,3 )⁴ = 0,44833
        ("aski.Kp", (240 / 293.3) ** 4, "Kp"),
        #  Nps boş — askı oranından gelir:  2:1 → 2 ( TS EN 81-50 Ek E Şekil E.1 ).
        #  Örnek projenin kendi dosyasında 1 yazılıydı;  Nequiv(p) = Kp · Nps.
        ("aski.Nequiv_p", 2 * (240 / 293.3) ** 4, "Nequiv(p)"),
        ("aski.S", 22.704560199764753, "S gerçek güvenlik katsayısı"),
    ),
    "regulator_halati": (
        ("regulator.oran", 50, "Dreg / dreg"),
        ("regulator.f", 0.5847608800326175, "f sürtünme değeri"),
        ("regulator.efa", 6.278182230367683, "e^(f·α')"),
    ),
    "tahrik_yetenegi": (("tahrik.bloke.T2", 219.19464000000002, "T2 bloke"),),
    #  RAY BOYU ( ve ona bağlı Mg, Fv, σv ):  ofisin kitabı LR'yi kat
    #  yükseklikleri toplamı ( makine dairesi zeminine ) + ( kaide − 200 ) +
    #  ( kuyu dibi − 300 ) diye alır ve son katı "en üst durak + kaide − 200"
    #  girdirir;  örnek iki yere de 3.750 yazmıştı → kitapta 26.600.  Programda
    #  son kat kuyu tavanına ölçülür, tabliye ( kitabın kaidesi ) bir kez daha
    #  eklenmez:  21.000 + 3.750 − 200 + 1.300 = 25.850 ( 5 Eki;  LiftDesigner'ın
    #  makine daireli üç projesi:  tabliye 1.200 oda zemininden ölçülür ).
    "kabin_raylari": (
        ("kabin_ray.Mg", 320.023, "Mg kabin rayı kütlesi"),
        ("kabin_ray.xc", 155, "xc"),
        ("kabin_ray.Fv", 3139.42563, "Fv"),
    ),
    "agirlik_raylari": (
        ("agirlik_ray.derinlik", 150, "ağırlık derinliği"),
        ("agirlik_ray.genislik", 960, "ağırlık genişliği"),
        ("agirlik_ray.Dxa", 15, "Dxa"),
        ("agirlik_ray.Dya", 48, "Dya"),
        ("agirlik_ray.Mg", 95.64500000000001, "Mg ağırlık rayı kütlesi"),
        ("agirlik_ray.Fv", 938.2774500000002, "Fv"),
        #  ( Fv + k3·MY ) / A = ( 938,3 + 2 × 50 ) / 475  —  k3 = 2 ( ofis )
        ("agirlik_ray.sv", 2.185847263157895, "σv"),
    ),
    "kuyu_tabani": (("kuyu.LR", 25850, "LR ray boyu"),),
    #  BİRLEŞİK PROGRAM:  açıklıklar kuyunun çiziminden ( cizim/dusey.py ) —
    #  elden, çizim sabitleriyle ( cizim/sabitler.py;  referans projenin kabini ):
    #  KUYU DİBİ  kabin tam ezilmiş tamponunda:  döşeme −( 150 + 90 ) = −240,
    #  kuyu tabanı −1.600 ( kaide çizimden 1.600 − 100 − 150 − 480 = 870 )
    #    en alt kısım  alt şase kirişinin altı ( şasenin altı ) −240 − 480 = −720
    #                  ( kabin kasnağı altı −240 − 295 − 240 / 2 = −655'ten
    #                  alçak;  10 Eki'ye dek kiriş sayılmıyordu:  945 )    →  880
    #    etek          −240 − 750 − 35 = −1.025 ( önlüğün pahı — m.5.4.5 ) →  575
    #    şase / paten  şase altı −240 − 480 = −720;  alt patenin merkezi
    #                  −720 − 70 = −790, altı − 140 / 2 = −860         →  740
    #                  ( patenler kirişlerin dışında — cizim/donanim.py )
    #    sığınma       sığınma alanının üstünde taban altı −240 − 120    → 1.240
    #  KUYU ÜSTÜ  ( son kattan )  kabin en üst konumda:  150 + 90 + 35·1² = 275
    #    makine şasesi üstü 3.750 − 250 − 47 − 298 = 3.155, altı − 120 = 3.035
    #    ( yan yatak NPU 120 — ORNEK_GIRDI );
    #    yakın kabin rayı ve ağırlık rayları şasenin 55 altında:  3.100
    #    kabin üst pateni:  alt paten merkezi 275 − 480 − 70 = −275,  üst paten
    #        merkezi −275 + 3.300 = 3.025,  üstü + 70 = 3.095
    #        rayın ucuna 3.100 − 3.095 = 5 ;  şaseye 3.035 − 3.095 = −60
    #    ağırlık en üst konumunda:  tamponu −1.600 + 300 + 100 = −1.200 ( alttan ),
    #        alt kirişi −1.200 + 150 + 150 + 90 + 35 = −775 ( üstten );  patenler
    #        çerçevenin dışında ( paten arası h:  merkezler ):  üst kirişin üstü
    #        −775 + 3.000 − 140 = 2.085,  üst pateni + 140 = 2.225  →  875
    #  Regülatör gergisi kabinin izdüşümünde değil:  satır yok.
    "siginma_alanlari": (
        ("siginma.agirlik_paten_ray", 875, "ağırlık üst pateni / ray ucu"),
        ("siginma.ust_paten_ray", 5, "kabin üst pateni / ray ucu"),
        ("siginma.paten_tavan", -60, "üst paten / makine şasesi"),
        ("siginma.kuyu_tabani_kabin", 880, "kuyu tabanı / alt şase kirişi"),
        ("siginma.etek", 575, "kuyu tabanı / etek"),
        ("siginma.ray_kabin_alt", 740, "kuyu tabanı / şase, paten"),
        ("siginma.dip_siginma", 1240, "kuyu dibi sığınma yüksekliği"),
    ),
}
ORNEK_OZET = (("S_gercek", 22.704560199764753), ("Mg_kabin", 320.023), ("Mg_agirlik", 95.64500000000001))


def _yakin(a, b, tol=1e-7):
    if a is None or b is None:
        return False
    try:
        buyuk = max(abs(float(a)), abs(float(b)), 1.0)
        return abs(float(a) - float(b)) <= tol * buyuk
    except (TypeError, ValueError):
        return False


#  ÖRNEK PROJENİN KENDİ İKİ DEĞERİ.  Varsayılanlar sonradan değişti:  tabliye
#  1.200 mm ( ofisin makine daireli şablonu ) ve makine kirişi NPU 140.  Örnek
#  projenin ara değerleri kendi girdileriyle denetlenir.
#  Son kat 3.750:  ofisin örnek hesabı ( programın varsayılanı artık 4.200 ).
#  Karşı ağırlık derinliği 150 ve paten arası 3.000:  örneğin kendi değerleri
#  ( varsayılanlar karar 11'le 155 ve 3.400 — barit dolgusu sığsın diye;
#  patenler çerçevenin dışında, çerçeve 3.300 ).
ORNEK_GIRDI = {
    "tabliye_yuksekligi": 750,
    "yan_yatak": 120,
    "son_kat_yuksekligi": 3750,
    "agirlik_derinligi": 150,
    "agirlik_paten_arasi": 3000,
    #  5. adım:  ofisin kabini varsayılan oldu ( paten arası 2.660, kabin
    #  2.000, şase altı 320 … );  örnek referans projenin kabiniyle
    "kabin_paten_arasi": 3300,
    "kabin_ic_yuksekligi": 2200,
    "_ofis": dict(sabitler.REFERANS_PROJE_KABINI),
}


def calistir():
    print("\n\033[1mTEST 9 — MUKAVEMET MOTORU\033[0m")
    r = Rapor("Mukavemet motoru")

    s = mukavemet.hesapla(dict(ORNEK_GIRDI))
    if not r.kontrol("varsayılan girdilerle hesap koşuyor", s["aktif"], f"→ {s.get('hata')}"):
        return r
    b = s["bolumler"]
    r.esit("bölüm sayısı", len(b), 11)
    for i, bl in enumerate(b):
        r.kontrol(f"bölüm {i + 1} başlığı dolu", bool(bl.get("baslik")))
        r.kontrol(f"bölüm {i + 1} adım üretti", len(bl.get("adimlar") or []) > 0)
        r.kontrol(f"bölüm {i + 1} sonucu var", bool(bl.get("sonuc")))

    #  ÖRNEK PROJE ÜÇ BÖLÜMDEN KALIYOR — üçü de gerçek yetersizliktir:
    #    · ASKI HALATLARI — TS EN 81-20 m.5.5.2.1 tahrik kasnağı / halat
    #      oranını EN AZ 40 ister;  örnekte 240 / 6,5 = 36,9  ( ① ).
    #    · MOTOR GÜCÜ — verim makine tipine bağlı;  dişlisiz + 2:1 askıda
    #      gereken güç örnekte seçilen 4,9 kW'ı aşar  ( ⑨ ).
    #  HIZ REGÜLATÖRÜ artık kalmıyor:  m.5.6.2.2.1.1 d)'nin ikinci sınırındaki
    #  devreye sokma kuvveti örnekte yoktur;  bölüm 300 N'u denetler ve
    #  fren bloğunun kuvvetine Fçekme / 2 şartını yazar  ( ⑲ ).
    #    · TAHRİK YETENEĞİ — acil frenlemede Ek D'nin ivme işaretleriyle
    #      sarılma açısı 139° · sertleştirilmemiş kanal sınırı aşıyor  ( ㊳ ).
    #  Beklenen davranış budur — geri dönerse test bağırır.
    #    · SIĞINMA AÇIKLIKLARI — kuyunun çiziminden ( birleşik program ):  son
    #      kat 3.750'de 3.300'lük şasenin üst pateni makine şasesine 150 mm giriyor.
    _kalan = [x["baslik"] for x in b if (x.get("sonuc") or {}).get("uygun") is False]
    r.esit("örnek proje dört bölümden kalıyor", len(_kalan), 4)
    r.kontrol(
        "kalanlar motor gücü, askı halatları, tahrik ve sığınma açıklıkları",
        sorted(x.split(" ")[0] for x in _kalan) == ["1", "11", "4", "6"],
        f"→ {_kalan}",
    )
    r.kontrol(
        "regülatör bölümü kuvvet girilmeden UYGUN, HESAP EKSİK değil",
        any(
            (x.get("sonuc") or {}).get("uygun") is True and not x.get("eksik_hesap")
            for x in b
            if x["baslik"].startswith("5 ")
        ),
    )
    r.esit("Dt/dh eşiği standarda göre 40", mukavemet.SABIT["Dt_dh_asgari"], 40)
    _oran = 240 / 6.5
    r.kontrol("örnek proje 40 eşiğini sağlamıyor", _oran < 40, f"→ {_oran}")
    #  İkisi de giderilince bütün bölümler uygun olmalı
    #  TAHRİK için iki bileşen bilgisi daha gerekir:  kanalın SERTLEŞTİRİLMİŞ
    #  olması ( f = μ / sin(γ/2) — EN 81-50 m.5.11.2.3.1.2 ) ve DENGE ZİNCİRİ
    #  ( boş kabin en üstteyken dengesiz halat kütlesini götürür ).  İkisi de
    #  örnekte beyan edilmemiştir;  gerçek projede imalatçıdan gelir.
    #  SARILMA AÇISI da beyan edilmeli ( zorunlu girdi, varsayılanı yok ).
    #  Senaryo 137,89° ile 180° arasındaki her açıda tam geçiyor;  180°
    #  alındı ( halat kasnaktan dikey iniyor — referans projenin örneğiyle aynı ).
    #  6,5 mm HALAT 8 mm'NİN ALTINDADIR ( m.5.5.1.2 a) ):  sahadaki gibi
    #  onaylanmış kuruluş belgesiyle kullanılır.
    #  KUYU ÜSTÜ 4.200:  sığınma açıklıkları kuyunun çiziminden ( 3.750'de üst
    #  paten makine şasesine giriyor ).
    _d = mukavemet.hesapla(
        {
            "tahrik_kasnak_capi": 280,
            "saptirma_kasnak_capi": 280,
            "motor_gucu": 7.5,
            "guvenlik_devreye_kuvvet": 200,
            "kanal_isleme": "Sertleştirilmiş",
            "denge_zinciri": "Var",
            "sarilma_acisi": 180,
            "kasnak_belgesi": "Var",
            "son_kat_yuksekligi": 4200,
        }
    )
    r.kontrol(
        "kasnak 280 mm · motor 7,5 kW · imalatçı kuvveti · sertleştirilmiş "
        "kanal · denge zinciri · halat belgesi girilince bütün bölümler uygun",
        _d["aktif"] and _d["ozet"]["tumu_uygun"],
        "→ "
        + ", ".join(
            x["baslik"] for x in (_d.get("bolumler") or []) if (x.get("sonuc") or {}).get("uygun") is False
        ),
    )
    r.esit("ray boyu (m)", s["ozet"]["ray_boyu"], 25.85)
    r.esit("kabin kişi sayısı", s["ozet"]["kabin_kisi"], 10)

    _kimlikler = {x["kimlik"]: x for x in b}
    for kimlik, liste in ORNEK_PROJE.items():
        _bl = _kimlikler.get(kimlik)
        if _bl is None:
            r.kontrol(f"bölüm {kimlik} üretildi", False)
            continue
        havuz = [
            a["deger"]
            for a in _bl["adimlar"]
            if isinstance(a["deger"], (int, float)) and not isinstance(a["deger"], bool)
        ]
        for ad, bek, ne in liste:
            r.kontrol(
                f"böl.{_bl['sira']}  {ad}  {ne}",
                _yakin(s["ara"].get(ad), bek) and any(_yakin(x, bek) for x in havuz),
                f"→ beklenen {bek!r} · ara değer {s['ara'].get(ad)!r}",
            )
    for anahtar, bek in ORNEK_OZET:
        r.kontrol(
            f"özet {anahtar}",
            _yakin(s["ozet"][anahtar], bek),
            f"→ motor {s['ozet'][anahtar]!r}, beklenen {bek!r}",
        )

    p = mukavemet_tablolari.ray("50 x 50 x 5", "Wx")
    #  Karşı ağırlık Fy:  k2 · gn · Mcwt · Dya / ( ( n / 2 ) · h )
    #  ( Ek C.2.2.1 b) — payda n·h DEĞİL, (n/2)·h )
    r.kontrol(
        "motor σ(My) için Wx kullanıyor",
        any(
            _yakin(
                a["deger"],
                mukavemet._moment(
                    1.2 * 9.81 * 1100 * 48 / ((2 / 2) * s["girdi"]["agirlik_paten_arasi"]), 3000
                )
                / p,
            )
            for a in b[7]["adimlar"]
            if isinstance(a["deger"], (int, float))
        ),
    )
    return _girdi_yollari(_denetim_bulgulari(_sapmalar(r)))


def _sapmalar(r):
    """Standardın gerektirdiği kurallar gerçekten uygulanıyor mu."""
    #  ① Dt/dh eşiği
    r.esit("① Dt/dh asgari oranı", mukavemet.SABIT["Dt_dh_asgari"], 40)

    #  ② karşı ağırlık rayı σ(My)  →  Wx

    s = mukavemet.hesapla()
    p = mukavemet_tablolari.ray("50 x 50 x 5", "Wx")
    _M = mukavemet._moment(s["ara"]["agirlik_ray.Fy"], 3000)
    r.kontrol(
        "② σ(My) Wx ile bölünüyor",
        _yakin(s["ara"]["agirlik_ray.sy"], _M / p),
        f"→ {s['ara']['agirlik_ray.sy']!r} ≠ {_M / p!r}",
    )

    #  ③ Durum 2'de xQ = xc
    _xc = s["ara"]["kabin_ray.xc"]
    #  h VARSAYILANDAN okunur, sayı olarak yazılmaz ( 3400 çivilenmişti ).
    _bek = (
        2 * 9.81 * (800 * _xc + _P_std(s) * s["ara"]["kabin_ray.xp"]) / (2 * s["girdi"]["kabin_paten_arasi"])
    )
    r.kontrol(
        "③ Durum 2 Fx, xQ = xc ile hesaplanıyor",
        _yakin(s["ara"]["kabin_ray.c21.d2.Fx"], _bek),
        f"→ {s['ara']['kabin_ray.c21.d2.Fx']!r} ≠ {_bek!r}",
    )

    #  ⑤ ω ray çeliğine bağlı  ( EN 81-50 m.5.10.3 )

    with open(REFERANS_TABLOLAR, encoding="utf-8") as _f:
        _omega_tablo = dict(json.load(_f)["omega"])
    r.kontrol(
        "⑤ Rm = 370 eğrisi kaynak ω tablosunun tamamını üretiyor",
        all(
            abs(mukavemet_tablolari.omega_en8150(x, 370) - _omega_tablo[x]) <= 0.006
            for x in range(mukavemet_tablolari.OMEGA_LAMBDA_MIN, mukavemet_tablolari.OMEGA_LAMBDA_MAX + 1)
        ),
    )
    _w = {rm: mukavemet.hesapla({"ray_celigi_rm": rm})["ara"]["kabin_ray.omega"] for rm in (370, 440, 520)}
    r.kontrol("⑤ ω ray çeliğiyle birlikte büyüyor", _w[370] < _w[440] < _w[520], f"→ {_w}")
    r.kontrol(
        "⑤ Rm 440 ara değerlemesi doğru",
        _yakin(_w[440], _w[370] + (_w[520] - _w[370]) * (440 - 370) / 150),
        f"→ {_w}",
    )
    #  λ EN KÜÇÜK atalet yarıçapından ölçülür ( sapma ㊴ ):  varsayılan
    #  89 x 62 x 15,88 rayda imin = iy = 18,23 mm, konsol 3.000 mm →  λ = 165.
    #  ( ix = 19,48 ile 155 çıkıyordu. )
    _lam = mukavemet_tablolari.OMEGA_LAMBDA_MIN
    import math as _m

    _lam = max(
        _lam,
        _m.ceil(
            3000
            / min(
                mukavemet_tablolari.ray("89 x 62 x 15,88", "ix"),
                mukavemet_tablolari.ray("89 x 62 x 15,88", "iy"),
            )
        ),
    )
    r.esit("⑤ λ en küçük atalet yarıçapından", _lam, 165)
    r.kontrol(
        "⑤ Rm 370'te kaynak ω tablosuyla aynı", abs(_w[370] - _omega_tablo[_lam]) <= 0.006, f"→ {_w[370]!r}"
    )

    #  ⑥ acil frenlemede μ HALAT hızına bağlı  ( EN 81-50 m.5.11.2.3.2 )
    #  EN 81-50'nin çözümlü örneği:  kabin 1 m/s, askı 2:1 → μ = 0,083
    _m = mukavemet.hesapla({"beyan_hizi": 1, "aski_orani": 2})["ara"]["tahrik.mu_fren"]
    r.kontrol(
        "⑥ μ, EN 81-50 örneğiyle aynı  ( 1 m/s · 2:1 → 0,0833 )", _yakin(_m, 0.1 / (1 + 2 / 10)), f"→ {_m!r}"
    )
    _m1 = mukavemet.hesapla({"beyan_hizi": 1, "aski_orani": 1})["ara"]["tahrik.mu_fren"]
    r.kontrol("⑥ 1:1 askıda μ kabin hızıyla aynı", _yakin(_m1, 0.1 / 1.1), f"→ {_m1!r}")
    r.kontrol("⑥ askı oranı μ'yü değiştiriyor", _m < _m1, f"→ {_m!r} / {_m1!r}")

    #  ⑦ Nps / Npr girdi
    #  D2 = D1 = 240:  Kp = 1, Nequiv(p) doğrudan Nps ( D2 boşsa çizimden gelirdi )
    _n = {
        x: mukavemet.hesapla({"kasnak_tek_yon": x, "saptirma_kasnak_capi": 240})["ara"]["aski.Nequiv"]
        for x in (1, 2, 3)
    }
    #  Nequiv(t) = 6,5  ( altı kesik V, ofis γ = 45°, Çizelge 2'nin V satırı ) + Nps
    r.esit("⑦ Nps Nequiv'i belirliyor", [_n[1], _n[2], _n[3]], [7.5, 8.5, 9.5])
    _sf = mukavemet.hesapla({"kasnak_tek_yon": 2})["ara"]["aski.Sf"]
    r.kontrol(
        "⑦ Nps büyüyünce gereken Sf de büyüyor",
        _sf > mukavemet.hesapla({"kasnak_tek_yon": 1})["ara"]["aski.Sf"],
        f"→ {_sf!r}",
    )
    _b4 = [b for b in mukavemet.hesapla({"kasnak_tek_yon": 1})["bolumler"] if "ASKI HALAT" in b["baslik"]][0]
    r.kontrol(
        "⑦ palangalı sistemde Nps 1 GİRİLİRSE uyarı çıkıyor",
        any("EN AZ İKİ kabin kasnağı" in x for x in (_b4.get("notlar") or [])),
        f"→ {_b4.get('notlar')}",
    )

    #  ⑦b Nps BOŞSA ASKI ORANINDAN  ( TS EN 81-50 Ek E ):  1:1 → 1 ( Şekil E.2,
    #  saptırma kasnağı ) · 2:1 → 2 ( Şekil E.1, iki kabin kasnağı ).  Girilen
    #  değer — 0 dâhil — her zaman kazanır.
    def _nps(**k):
        _h = mukavemet.hesapla(k)
        _bl = [b for b in _h["bolumler"] if b.get("kimlik") == "aski_halatlari"][0]
        _sat = [a for a in _bl["adimlar"] if a.get("sembol") == "Nps"][0]
        return _sat["deger"], _sat["kaynak"], _bl.get("notlar") or []

    for _r, _bek, _sekil in ((1, 1, "E.2"), (2, 2, "E.1")):
        _d, _k, _nt = _nps(aski_orani=_r)
        r.kontrol(
            f"⑦b Nps boş · {_r}:1 askı → {_bek}  ( Ek E Şekil {_sekil} )",
            _d == _bek and f"Şekil {_sekil}" in _k,
            f"→ {_d!r} · {_k!r}",
        )
        r.kontrol(
            f"⑦b Nps boş · {_r}:1 askı → uyarı yok",
            not any("EN AZ İKİ kabin kasnağı" in x for x in _nt),
            f"→ {_nt}",
        )
    for _giris in (0, 3):
        _d, _k, _nt = _nps(aski_orani=2, kasnak_tek_yon=_giris)
        r.kontrol(
            f"⑦b Nps = {_giris} girilince türetilen ezilmiyor",
            _d == _giris and _k == "GİRİŞ",
            f"→ {_d!r} · {_k!r}",
        )
    r.kontrol("⑦b boş metin de boş sayılır", _nps(aski_orani=2, kasnak_tek_yon="")[0] == 2)

    #  Sf formülü EN 81-50 m.5.12.3'ün çözümlü örneğini üretiyor mu
    #  ( LEIA örneği:  Dt/dr = 40 , Nequiv = 7  →  Sf ≈ 16 )
    import math as _m2

    _sfx = 10 ** (2.6834 - _m2.log10(695.85e6 * 7 / 40**8.567) / _m2.log10(77.09 * 40**-2.894))
    r.kontrol("Sf formülü EN 81-50 örneğini üretiyor  ( ≈ 16 )", 15.5 <= _sfx <= 16.9, f"→ {_sfx!r}")

    #  ④ flanş eğilmesinde ℓ
    _a = mukavemet.hesapla({"paten_balata_boyu": 60})
    _b = mukavemet.hesapla({"paten_balata_boyu": 120})
    r.kontrol(
        "④ balata boyu σF'yi değiştiriyor",
        _a["ara"]["kabin_ray.c21.d1.sf"] > _b["ara"]["kabin_ray.c21.d1.sf"] > 0,
        f"→ ℓ=60 {_a['ara']['kabin_ray.c21.d1.sf']!r} · ℓ=120 {_b['ara']['kabin_ray.c21.d1.sf']!r}",
    )
    r.kontrol(
        "④ balata boyu boşsa türetiliyor  ( 2·b )",
        _yakin(
            s["ara"]["kabin_ray.c21.d1.sf"],
            mukavemet._flans(
                s["ara"]["kabin_ray.c21.d1.Fx"], mukavemet._ray_ozellik("89 x 62 x 15,88"), 2 * 17
            ),
        ),
    )

    #  ═══════════════════════════════════════════════════════════════
    #  STANDARDIN METNİNE KARŞI BAĞIMSIZ DOĞRULAMA
    #  ═══════════════════════════════════════════════════════════════
    #  Aşağıdaki sayılar BS EN 81-20:2014 ve BS EN 81-50:2014'ün kendi
    #  metninden alınmıştır — motorun koduna bakılmadan.

    #  EN 81-20 Çizelge 14  —  darbe katsayıları
    for _tip, _bek in (("Kaymalı", 2), ("Ani Frenlemeli Makaralı", 3), ("Ani Frenlemeli", 5)):
        r.esit(f"EN 81-20 Çiz.14  k1 {_tip}", mukavemet_tablolari.darbe_k1(_tip), _bek)
    r.esit("EN 81-20 Çiz.14  k2 = 1,2  ( hareket )", mukavemet.SABIT["k2"], 1.2)

    #  EN 81-20 Çizelge 15  —  σperm = Rm / St
    #  Yuvarlanmadan:  tam sayıya yuvarlanmış bir tablo Rm 370'te normal
    #  işletmede 165 ( kesin 164,44 ) ile emniyetsiz yönde olurdu.
    for _rm in mukavemet_tablolari.RAY_CELIKLERI:
        r.kontrol(
            f"EN 81-20 Çiz.15  Rm={_rm} normal = Rm/2,25  ( yuvarlanmadan )",
            _yakin(mukavemet_tablolari.sigma_perm_normal(_rm), _rm / 2.25),
            f"→ {mukavemet_tablolari.sigma_perm_normal(_rm)} · kesin {_rm / 2.25!r}",
        )
        r.kontrol(
            f"EN 81-20 Çiz.15  Rm={_rm} güv.tert. = Rm/1,8  ( yuvarlanmadan )",
            _yakin(mukavemet_tablolari.sigma_perm_guvenlik(_rm), _rm / 1.8),
            f"→ {mukavemet_tablolari.sigma_perm_guvenlik(_rm)} · kesin {_rm / 1.8!r}",
        )
    _s370 = mukavemet.hesapla({"ray_celigi_rm": 370})
    r.kontrol(
        "EN 81-20 m.5.7.4.5  hesapta da 164,44  ( 165 değil )",
        _yakin(_s370["ara"]["kabin_ray.sperm_n"], 370 / 2.25)
        and _yakin(_s370["ara"]["kabin_ray.sperm_g"], 370 / 1.8),
        f"→ {_s370['ara']['kabin_ray.sperm_n']!r} · {_s370['ara']['kabin_ray.sperm_g']!r}",
    )

    #  EN 81-20 m.5.7.2.3.6  —  kapı eşiği kuvveti ASANSÖR TİPİNDEN
    #  ( Q < 2500 kg diye bir eşik standartta yoktur )
    for _tip, _k in (("İnsan asansörü", 0.4), ("Yük-insan asansörü", 0.6)):
        for _q, _gk, _w, _d in ((800, 700, 1450, 1350), (2500, 1600, 2200, 2250)):
            _sf = mukavemet.hesapla(
                {
                    "asansor_tipi": _tip,
                    "beyan_yuku": _q,
                    "kabin_agirligi": _gk,
                    "kabin_genisligi": _w,
                    "kabin_derinligi": _d,
                    "kabin_ray_profili": "127 x 89 x 16",
                }
            )
            r.kontrol(
                f"EN 81-20 m.5.7.2.3.6  {_tip} · Q={_q} → Fs = {_k}·gn·Q",
                _sf["aktif"] and _yakin(_sf["ara"]["kabin_ray.Fs"], _k * 9.81 * _q),
                f"→ {_sf.get('hata') or _sf['ara'].get('kabin_ray.Fs')!r}",
            )
    r.esit(
        "asansör tipi varsayılanı insan asansörü",
        mukavemet.hesapla({})["girdi"]["asansor_tipi"],
        "İnsan asansörü",
    )
    r.kontrol(
        "tanınmayan asansör tipi reddediliyor",
        not mukavemet.hesapla({"asansor_tipi": "Araba asansörü"})["aktif"],
    )

    #  EN 81-20 m.5.4.2.3.1  —  yolcu = MIN( Q/75 ; Çizelge 8 ), Çizelge 8 ret değil
    def _ka(**kw):
        _s = mukavemet.hesapla(dict({"sarilma_acisi": 180}, **kw))
        return _s, next(b for b in _s["bolumler"] if b["kimlik"] == "kabin_alani")

    _s1, _b1 = _ka(beyan_yuku=1000, kabin_agirligi=900, kabin_genisligi=1300, kabin_derinligi=1500)
    r.kontrol(
        "m.5.4.2.3.1  1000 kg · 1,95 m² → 11 kişi ve UYGUN  ( Çizelge 8 ret değil )",
        _s1["ozet"]["kabin_kisi"] == 11 and _b1["sonuc"]["uygun"] is True,
        f"→ {_s1['ozet']['kabin_kisi']!r} · {_b1['sonuc']['metin']!r}",
    )
    _s2, _b2 = _ka(beyan_yuku=800, kabin_genisligi=1450, kabin_derinligi=1350)
    r.kontrol(
        "m.5.4.2.3.1  alan yeterliyse Q/75 belirler  ( 800 kg → 10 kişi )",
        _s2["ozet"]["kabin_kisi"] == 10 and _b2["sonuc"]["uygun"] is True,
    )
    _s3, _b3 = _ka(beyan_yuku=800, kabin_genisligi=1600, kabin_derinligi=1400)
    r.kontrol(
        "Çizelge 6  en büyük alan hâlâ ret ölçütü  ( 800 kg · 2,24 m² )", _b3["sonuc"]["uygun"] is False
    )
    r.kontrol(
        "Çizelge 8'in tersi  20 kişiden sonrası + 0,115 m²",
        mukavemet_tablolari.cizelge8_kisi(3.245) == 21
        and mukavemet_tablolari.cizelge8_kisi(3.2449) == 20
        and mukavemet_tablolari.cizelge8_kisi(0.2799) == 0
        and mukavemet_tablolari.cizelge8_kisi(1.87) == 11,
    )

    #  EN 81-20 m.5.5.2  ·  m.5.6.2.2.1  ·  m.5.7.4.6
    r.esit("EN 81-20 m.5.5.2.1  Dt/dh ≥ 40", mukavemet.SABIT["Dt_dh_asgari"], 40)
    r.esit("EN 81-20 m.5.6.2.2.1.3 c)  Dreg/dreg ≥ 30", mukavemet.SABIT["Dreg_dreg_asgari"], 30)
    r.esit("EN 81-20 m.5.6.2.2.1.3 b)  emniyet katsayısı ≥ 8", mukavemet.SABIT["reg_kat_asgari"], 8)
    r.esit("EN 81-20 m.5.6.2.2.1.1 d)  çekme kuvveti ≥ 300 N", mukavemet.SABIT["reg_kuvvet_asgari"], 300)
    r.esit("EN 81-20 m.5.6.2.2.1.3 b)  μmax = 0,20", mukavemet.SABIT["mu_bloke"], 0.2)
    r.esit("EN 81-20 m.5.7.4.6 a)  δperm = 5 mm", mukavemet.SABIT["dperm_kabin"], 5)
    r.esit("EN 81-20 m.5.7.4.6 b)  δperm = 10 mm", mukavemet.SABIT["dperm_agirlik"], 10)

    #  EN 81-20 Çizelge 6 / 8 / m.5.4.2.3.1  —  kabin alanı
    _CIZ6 = {
        100: 0.37,
        180: 0.58,
        225: 0.70,
        300: 0.90,
        375: 1.10,
        400: 1.17,
        450: 1.30,
        525: 1.45,
        600: 1.60,
        630: 1.66,
        675: 1.75,
        750: 1.90,
        800: 2.00,
        825: 2.05,
        900: 2.20,
        975: 2.35,
        1000: 2.40,
        1050: 2.50,
        1125: 2.65,
        1200: 2.80,
        1250: 2.90,
        1275: 2.95,
        1350: 3.10,
        1425: 3.25,
        1500: 3.40,
        1600: 3.56,
        2000: 4.20,
        2500: 5.00,
    }
    _CIZ8 = {
        1: 0.28,
        2: 0.49,
        3: 0.60,
        4: 0.79,
        5: 0.98,
        6: 1.17,
        7: 1.31,
        8: 1.45,
        9: 1.59,
        10: 1.73,
        11: 1.87,
        12: 2.01,
        13: 2.15,
        14: 2.29,
        15: 2.43,
        16: 2.57,
        17: 2.71,
        18: 2.85,
        19: 2.99,
        20: 3.13,
    }
    r.esit(
        "EN 81-20 Çiz.6'nın hiçbir yükü eksik değil",
        [q for q in sorted(_CIZ6) if mukavemet_tablolari.kabin_azami_alan(q) is None],
        [],
    )
    for _q, _a in sorted(_CIZ6.items()):
        r.kontrol(
            f"EN 81-20 Çiz.6  Q={_q} → {_a} m²",
            _yakin(mukavemet_tablolari.kabin_azami_alan(_q), _a),
            f"→ {mukavemet_tablolari.kabin_azami_alan(_q)}",
        )
    for _q, _k, _az, _as in mukavemet_tablolari.KABIN_ALANI:
        r.esit(f"EN 81-20 m.5.4.2.3.1  Q={_q} → kişi", _k, _q // 75)
        _bek = _CIZ8.get(_k) if _k <= 20 else round(3.13 + 0.115 * (_k - 20), 4)
        r.kontrol(f"EN 81-20 Çiz.8  {_k} kişi → {_bek} m²", _yakin(_as, _bek), f"→ {_as}")
    #  320 kg Çizelge 6'da yoktur:  ara değer kuralı ( m.Çiz.6 dipnotu )
    r.kontrol(
        "EN 81-20 Çiz.6 dipnotu  320 kg ara değeri",
        _yakin(mukavemet_tablolari.kabin_azami_alan(320), 0.90 + 0.20 * 20 / 75, 1e-3),
        f"→ {mukavemet_tablolari.kabin_azami_alan(320)}",
    )

    #  EN 81-50 m.5.10.2 / 5.10.3 / 5.10.4 / 5.10.6  —  ray hesabı
    r.esit(
        "EN 81-50 m.5.10.2.1  Mm = 3·Fh·l/16",
        (mukavemet.SABIT["moment_pay"], mukavemet.SABIT["moment_bolen"]),
        (3, 16),
    )
    r.esit("EN 81-50 m.5.10.4  σ = σk + 0,9·σm", mukavemet.SABIT["birlesik_katsayi"], 0.9)
    r.esit(
        "EN 81-50 m.5.10.6  δ = 0,7·F·l³/(48·E·I)",
        (mukavemet.SABIT["sehim_katsayi"], mukavemet.SABIT["sehim_bolen"]),
        (0.7, 48),
    )
    #  ω polinomları — standardın kendi katsayıları
    r.esit(
        "EN 81-50 m.5.10.3  Rm=370 eğrisi",
        [(a, round(b, 8), c, d) for a, b, c, d in mukavemet_tablolari.OMEGA_370],
        [
            (60, 0.0001292, 1.89, 1.0),
            (85, 0.00004627, 2.14, 1.0),
            (115, 0.00001711, 2.35, 1.04),
            (250, 0.00016887, 2.0, 0.0),
        ],
    )
    r.esit(
        "EN 81-50 m.5.10.3  Rm=520 eğrisi",
        [(a, round(b, 8), c, d) for a, b, c, d in mukavemet_tablolari.OMEGA_520],
        [
            (50, 0.0000824, 2.06, 1.021),
            (70, 0.00001895, 2.41, 1.05),
            (89, 0.00002447, 2.36, 1.03),
            (250, 0.0002533, 2.0, 0.0),
        ],
    )

    #  EN 81-50 Ek C.2.1.1 — kuvvet · moment · gerilme zinciri
    _sc = mukavemet.hesapla()
    _gc, _hc = _sc["girdi"], _sc["ara"]
    _k1 = mukavemet_tablolari.darbe_k1(_gc["guvenlik_tertibati"])
    _n, _hh = _gc["kabin_ray_sayisi"], _gc["kabin_paten_arasi"]
    _l = _gc["kabin_konsol_arasi"]
    _p = mukavemet_tablolari.RAY_PROFILI
    _Wy = mukavemet_tablolari.ray(_gc["kabin_ray_profili"], "Wy")
    _xc, _xp = _hc["kabin_ray.xc"], _hc["kabin_ray.xp"]
    _xQ = _xc + _gc["kabin_derinligi"] / 8.0
    _Fx = _k1 * 9.81 * (_gc["beyan_yuku"] * _xQ + _P_std(_sc) * _xp) / (_n * _hh)
    r.kontrol(
        "EN 81-50 C.2.1.1 a)  Fx = k1·gn·(Q·xQ+P·xP)/(n·h)",
        _yakin(_hc["kabin_ray.c21.d1.Fx"], _Fx),
        f"→ motor {_hc['kabin_ray.c21.d1.Fx']!r}, standart {_Fx!r}",
    )
    r.kontrol(
        "EN 81-50 C.2.1.1 a)  σy = (3·Fx·l/16)/Wy",
        _yakin(_hc["kabin_ray.c21.d1.sy"], 3 * _Fx * _l / 16 / _Wy),
        f"→ motor {_hc['kabin_ray.c21.d1.sy']!r}",
    )
    #  C.2.1.2 burkulma
    _Fv = _k1 * 9.81 * (_P_std(_sc) + _gc["beyan_yuku"]) / _n + _hc["kabin_ray.Mg"] * 9.81
    r.kontrol(
        "EN 81-50 C.2.1.2  Fv = k1·gn·(P+Q)/n + Mg·gn",
        _yakin(_hc["kabin_ray.Fk"], _Fv),
        f"→ motor {_hc['kabin_ray.Fk']!r}, standart {_Fv!r}",
    )

    #  ⑪  acil frenleme yavaşlamasının ALT sınırı  ( m.5.11.2.2.2 )

    r.esit("EN 81-50 m.5.11.2.2.2  asgari yavaşlama 0,5 m/s²", mukavemet_girdi.ACIL_FRENLEME_ASGARI, 0.5)
    for _a, _bek in ((0.05, False), (0.2, False), (0.5, True), (0.8, True), (9.81, True), (10, False)):
        _sa = mukavemet.hesapla({"acil_frenleme_a": _a})
        r.esit(f"a = {_a} m/s² {'kabul' if _bek else 'RED'}", _sa["aktif"], _bek)
    r.kontrol(
        "alt sınır hatası maddeyi yazıyor",
        any("5.11.2.2.2" in x for x in (mukavemet.hesapla({"acil_frenleme_a": 0.2}).get("hata") or [])),
    )

    #  ⑪.b  TAMPON KENDİ BOYUNDAN FAZLA EZİLEMEZ
    #  Kuyu dibindeki bütün açıklıklar  a_dip = baba + ( boyu − ezilme )
    #  üzerinden türer.  Ezilme boyu aşınca a_dip negatife dönüyor ve
    #  a · a.1 · a.2 · b ile Ç.4 sığınma hacmi sessizce bozuluyordu:
    #  100 mm'lik tampona 5.000 mm ezilme kabul ediliyordu.
    for _b, _e, _bek in (
        (100, 90, True),
        (100, 100, True),
        (200, 150, True),
        (100, 120, False),
        (120, 200, False),
        (100, 5000, False),
    ):
        _st = mukavemet.hesapla({"kabin_tampon_boyu": _b, "kabin_tampon_ezilme": _e})
        r.esit(f"tampon boyu {_b} · ezilme {_e} {'kabul' if _bek else 'RED'}", _st["aktif"], _bek)
    #  ⑪.c  BİRBİRİNE BAĞLI GİRDİLERDE TUTARLILIK
    #  Üçü de aynı sınıftandı:  tek tek geçerli ama BİRLİKTE olanaksız
    #  değerler sessizce kabul edilip hesabı bozuyordu.
    #     Ds > D2   →  m.5.5.2.1'in Ds/dh kontrolü hükümden düşüyordu
    #     ray = 1   →  m.5.7.1.1 en az iki ray ister
    #     a_dip ≥ KY →  kabinin en alt noktası alt durak döşemesinin üstünde
    for _ad, _gir, _bek in (
        ("Ds > D2", {"saptirma_kasnak_capi": 240, "saptirma_kasnak_min_capi": 600}, False),
        ("Ds = D2", {"saptirma_kasnak_capi": 240, "saptirma_kasnak_min_capi": 240}, True),
        ("Ds < D2", {"saptirma_kasnak_capi": 240, "saptirma_kasnak_min_capi": 200}, True),
        ("kabin rayı 1", {"kabin_ray_sayisi": 1}, False),
        ("ağırlık rayı 1", {"agirlik_ray_sayisi": 1}, False),
        ("kabin rayı 2", {"kabin_ray_sayisi": 2}, True),
        ("kabin rayı 4", {"kabin_ray_sayisi": 4}, True),
        ("baba kuyu dibinden yüksek", {"kuyu_dibi": 800, "kabin_tampon_baba": 1000}, False),
        ("baba kuyu dibinin içinde", {"kuyu_dibi": 1600, "kabin_tampon_baba": 1000}, True),
    ):
        r.esit(f"tutarlılık: {_ad} {'kabul' if _bek else 'RED'}", mukavemet.hesapla(_gir)["aktif"], _bek)
    r.kontrol(
        "ray sayısı hatası maddeyi yazıyor",
        any("5.7.1.1" in x for x in (mukavemet.hesapla({"kabin_ray_sayisi": 1}).get("hata") or [])),
    )

    r.kontrol(
        "tampon ezilme hatası iki sayıyı da yazıyor",
        any(
            "100" in x and "5000" in x
            for x in (
                mukavemet.hesapla({"kabin_tampon_boyu": 100, "kabin_tampon_ezilme": 5000}).get("hata") or []
            )
        ),
    )

    #  ⑫  sürtünme çarpanı f  —  kanal şekline göre AYRI madde
    import math as _mf

    _O = mukavemet.hesapla()["ozet"] and None

    _Sf = uygulama_sabitleri.sabitler()
    r.esit("EN 81-50  V kanal γ ≥ 35°", _Sf["kanal_gama_v"] >= 35, True)
    r.esit("EN 81-50  yarım daire γ ≥ 25°", _Sf["kanal_gama_yd"] >= 25, True)
    r.esit("EN 81-50  β ≤ 105°", _Sf["kanal_beta"] <= 105, True)

    def _f_std(sekil, isleme, mu):
        """Standardın kendi bağıntısı — motorun koduna bakılmadan."""
        yd = sekil in mukavemet_tablolari.KANAL_YARIM_DAIRE
        b = _mf.radians(_Sf["kanal_beta"] if sekil in mukavemet_tablolari.KANAL_ALTI_KESIK else 0)
        gm = _mf.radians(_Sf["kanal_gama_yd"] if yd else _Sf["kanal_gama_v"])
        if yd:
            return mu * 4 * (_mf.cos(gm / 2) - _mf.sin(b / 2)) / (_mf.pi - b - gm - _mf.sin(b) + _mf.sin(gm))
        if isleme == "Sertleştirilmiş":
            return mu / _mf.sin(gm / 2)
        return mu * 4 * (1 - _mf.sin(b / 2)) / (_mf.pi - b - _mf.sin(b))

    for _sk in mukavemet_tablolari.KANAL_SEKILLERI:
        for _is in ("Sertleştirilmemiş", "Sertleştirilmiş"):
            _x = mukavemet.hesapla({"kanal_sekli": _sk, "kanal_isleme": _is})
            #  Sertleştirilmemiş DÜZ V kanal girdide reddedilir
            #  ( TS EN 81-50 m.5.11.2.3.1.2 ) — onun f'i sınanmaz, reddi sınanır.
            if mukavemet_tablolari.kanal_turu(_sk) == "V" and _is == "Sertleştirilmemiş":
                r.kontrol(
                    f"f yükleme  {_sk[:26]} · {_is[:14]}  girdide reddediliyor",
                    not _x.get("aktif") and any("m.5.11.2.3.1.2" in h for h in _x.get("hata") or []),
                    f"→ {_x.get('hata')}",
                )
                continue
            _h2 = _x["ara"]
            _fm = (
                _h2.get("tahrik.f_yukleme")
                if _h2.get("tahrik.f_yukleme") is not None
                else _h2.get("tahrik.f_yukleme")
            )
            r.kontrol(
                f"f yükleme  {_sk[:26]} · {_is[:14]}",
                _yakin(_fm, _f_std(_sk, _is, 0.1)),
                f"→ motor {_fm!r}, standart {_f_std(_sk, _is, 0.1)!r}",
            )
    #  Kanal şekli f'yi GERÇEKTEN değiştirmeli  ( eskiden değiştirmiyordu )
    _fset = set()
    for _sk in mukavemet_tablolari.KANAL_SEKILLERI:
        _h2 = mukavemet.hesapla({"kanal_sekli": _sk, "kanal_isleme": "Sertleştirilmiş"})["ara"]
        _fset.add(round(_h2.get("tahrik.f_yukleme") or _h2.get("tahrik.f_yukleme"), 6))
    r.kontrol("kanal şekli sürtünme çarpanını değiştiriyor", len(_fset) > 1, f"→ {_fset}")
    #  Sertleştirilmemiş + alt kesilmesiz V kanal:  standart dışı.  Eskiden
    #  yalnız not düşülüyor ve sayısal kontroller geçerse bölüm "UYGUNDUR"
    #  diyordu;  artık girdide reddedilir ve seçim sessizce değiştirilmez.
    _v6 = mukavemet.hesapla({"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş"})
    r.kontrol(
        "alt kesilmesiz sertleştirilmemiş kanal girdide REDDEDİLİYOR",
        not _v6.get("aktif") and any("m.5.11.2.3.1.2" in h for h in _v6.get("hata") or []),
        f"→ {_v6.get('hata')}",
    )
    r.esit("ret sırasında işleme seçimi değiştirilmiyor", _v6["girdi"]["kanal_isleme"], "Sertleştirilmemiş")

    #  ⑨  motor verimi makine tipine bağlı  ( ofis standardı, TEK KAYNAK )
    from motor.ortak import ofis

    r.kontrol(
        "⑨ verim tablosu avan ile UYGULAMA'da tek kaynak",
        tablolar.MAKINE_TIPLERI is ofis.MAKINE_VERIMLERI,
        "→ tablo ikiye ayrılmış;  yeniden ayrışabilir",
    )
    r.esit("⑨ ofis verim tablosu", dict(ofis.MAKINE_VERIMLERI), {"Dişlisiz": 0.85, "Dişli": 0.50})
    #  Δη = 0,10 YALNIZ AVANDA ( kitaba göre, motor/avan/tablolar ):  ortak
    #  tabloya taşınırsa uygulamanın toplam verimine de uygulanabilir hâle gelir.
    r.kontrol(
        "⑨ uygulamada palanga verim düşüşü Δη YOK  ( ortak tabloda değil )",
        not hasattr(ofis, "PALANGA_VERIM_DUSUSU"),
        "→ Δη ortak tabloya taşınmış;  uygulamada η toplam verimdir, makara kaybı çarpımsaldır",
    )
    r.kontrol(
        "⑨ makine tipi girdi",
        "makine_tipi" in mukavemet_girdi.ALAN and mukavemet_girdi.ALAN["makine_tipi"][3] == "secim",
        f"→ {mukavemet_girdi.ALAN.get('makine_tipi')}",
    )
    #  η TOPLAM SİSTEM VERİMİDİR:  askı oranı onu DEĞİŞTİRMEZ.
    _bek9 = {("Dişlisiz", 1): 0.85, ("Dişlisiz", 2): 0.85, ("Dişli", 1): 0.50, ("Dişli", 2): 0.50}
    for (_t, _r2), _e in sorted(_bek9.items()):
        _v = mukavemet.hesapla({"makine_tipi": _t, "aski_orani": _r2})["ara"]["motor.eta"]
        r.kontrol(f"⑨ η  {_t} {_r2}:1  = {_e}", _yakin(_v, _e), f"→ {_v!r}")
    _s9 = mukavemet.hesapla({"makine_tipi": "Dişli", "aski_orani": 1})
    _bekN = _s9["ara"]["motor.Gmax"] * _s9["girdi"]["beyan_hizi"] / (0.50 * 102)
    r.kontrol(
        "⑨ N = Gmax·v/(η·102)",
        _yakin(_s9["ara"]["motor.N"], _bekN),
        f"→ {_s9['ara']['motor.N']!r} ≠ {_bekN!r}",
    )
    r.kontrol(
        "⑨ dişli makine dişlisizden BÜYÜK güç istiyor",
        mukavemet.hesapla({"makine_tipi": "Dişli"})["ara"]["motor.N"]
        > mukavemet.hesapla({"makine_tipi": "Dişlisiz"})["ara"]["motor.N"],
    )
    r.kontrol(
        "⑨ sabit 0,92 hiçbir makine tipinde kullanılmıyor",
        all(
            not _yakin(mukavemet.hesapla({"makine_tipi": _t, "aski_orani": _r2})["ara"]["motor.eta"], 0.92)
            for _t in ("Dişlisiz", "Dişli")
            for _r2 in (1, 2)
        ),
    )
    from motor.uygulama import uygulama_girdisi

    for _t in ("Dişlisiz", "Dişli"):
        for _r2 in (1, 2):
            _g9 = uygulama_girdisi.tamamla(
                dict(uygulama_girdisi.varsayilanlar(), makine_tipi=_t, aski_orani=_r2)
            )
            _oz9 = avan_hesabi.hesapla(uygulama_girdisi.avan_girdisi(_g9))["asansorler"][0]["ozet"]
            r.kontrol(
                f"⑨ köprü η aynı, avanın palanga düşüşü uygulanmıyor  ( {_t} {_r2}:1 )",
                _yakin(_oz9["eta_p"], _bek9[(_t, _r2)]),
                f"→ avan {_oz9['eta_p']!r}, beklenen {_bek9[(_t, _r2)]}",
            )

    #  ⑧ sığınma açıklıklarının alt sınırları  ( EN 81-20 m.5.2.5.7 / 5.2.5.8 )
    #  Açıklıkların çoğu kuyunun çiziminden ölçülür;  sınırları orada
    from cizim import dusey

    _S = mukavemet.SIGINMA
    r.esit("⑧ ray dibi açıklığı  ( m.5.2.5.8.2 a) 2) · Şekil 7 )", dusey.DIP_RAYA_YAKIN, 100)
    r.esit("⑧ kuyu dibi - kabin  ( m.5.2.5.8.2 a) )", dusey.DIP_EN_ALT, 500)
    r.esit("⑧ etek açıklığı  ( m.5.2.5.8.2 a) 1) )", dusey.DIP_ETEK, 100)
    r.esit("⑧ kuyuya sabit parça  ( m.5.2.5.8.2 b) )", _S["min_regulator"], 300)
    r.esit("⑧ kabin üstü donanım  ( m.5.2.5.7.2 a) )", _S["min_revizyon"], 500)
    r.esit("⑧ ilave kılavuzlu yol  ( m.5.2.5.6.2 )", dusey.RAY_UZANTISI, 100)
    r.esit("⑧ üst paten – tavan  ( m.5.2.5.7.2 b) )", dusey.UST_PATEN, _S["min_paten_tavan"])
    #  Sığınma hacimleri SIGINMA sözlüğünden çıkarıldı:  duruş tipi artık
    #  tesise özel bir BEYAN ( girdi ), ölçüler MT.SIGINMA_HACMI tablosundan.
    r.kontrol(
        "⑧ sığınma hacimleri artık ofis sabiti DEĞİL",
        "ust_hacim" not in _S and "dip_hacim" not in _S,
        f"→ {sorted(_S)}",
    )
    r.esit(
        "⑧ sığınma duruşları  ( EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 )",
        {ad: (a, b, c) for ad, a, b, c in mukavemet_tablolari.SIGINMA_HACMI},
        {"Dik duruş": (0.40, 0.50, 2.00), "Çömelme": (0.50, 0.70, 1.00), "Yatarak": (0.70, 1.00, 0.50)},
    )
    r.kontrol(
        "⑧ yatarak duruş YALNIZ kuyu dibinde",
        "Yatarak" in mukavemet_tablolari.SIGINMA_TIPLERI_DIP
        and "Yatarak" not in mukavemet_tablolari.SIGINMA_TIPLERI_UST,
        f"→ üst {mukavemet_tablolari.SIGINMA_TIPLERI_UST} · dip {mukavemet_tablolari.SIGINMA_TIPLERI_DIP}",
    )
    r.esit(
        "⑧ varsayılan duruş çömelme  ( eski davranış korunuyor )",
        [
            mukavemet_tablolari.siginma_hacmi("Çömelme", "ust"),
            mukavemet_tablolari.siginma_hacmi("Çömelme", "dip"),
        ],
        [(0.7, 0.5, 1.0), (0.5, 0.7, 1.0)],
    )
    r.kontrol("⑧ artık ayrı bir min_kabin_ustu sabiti yok", "min_kabin_ustu" not in _S, f"→ {sorted(_S)}")

    #  SIRAYA DEĞİL KİMLİĞE BAK:  araya bölüm girince numara kayıyor.
    _b10 = [b for b in s["bolumler"] if b["kimlik"] == "siginma_alanlari"][0]
    _sinir = {}
    for a in _b10["adimlar"]:
        _ac = str(a.get("aciklama") or "")
        if "( en az" in _ac and " mm" in _ac:
            _sinir[_ac.split("  ( en az")[0]] = float(
                _ac.split("en az")[1].split("mm")[0].strip().replace(".", "")
            )

    def _bas(on):
        return next((v for k, v in _sinir.items() if k.startswith(on)), None)

    r.esit(
        "⑧ kabin üstü sınırı sığınma yüksekliğinden okunuyor",
        _bas("Sığınma alanı / üstündeki en alt kısım"),
        mukavemet_tablolari.siginma_hacmi("Çömelme", "ust")[2] * 1000,
    )
    r.esit(
        "⑧ ray dibi sınırı pafta metnine de yansıyor", _bas("Kuyu tabanı / şase, paten, fren bloğu"), 100.0
    )
    r.kontrol(
        "⑧ sınıra eşit ölçü UYGUN sayılıyor  ( 'en az' )",
        all(
            ("≥" in str(a.get("aciklama") or "")) or ("mm  >  " not in str(a.get("aciklama") or ""))
            for a in _b10["adimlar"]
        ),
        "→ '>' karşılaştırması kalmış",
    )
    r.kontrol(
        "⑧ bölüm notu payların ofis kabulü olduğunu söylüyor",
        any("ofis kabulüdür" in x for x in _b10["aciklamalar"]),
    )
    r.kontrol(
        "⑧ bölüm notu açıklıkların standarttan geldiğini söylüyor",
        any("m.5.2.5.7 ve m.5.2.5.8" in x for x in _b10["aciklamalar"]),
        f"→ {_b10['aciklamalar']}",
    )
    return r


def _denetim_bulgulari(r):
    """BAĞIMSIZ DENETİMDE BULUNAN HATALARIN HER BİRİ YENİDEN ÜRETİLİR.

    Testlerin geçmesi hataların yokluğunu göstermez;  aşağıdaki on bulgunun
    hiçbirini paketin geri kalanı yakalamıyordu.  Her kontrol, hatanın ESKİ
    hâlini üreten girdiyle çalışır ve düzeltmenin yerinde durduğunu gösterir.
    """

    #  ── B1  "Sf ≥ Smin" bir geçme ölçütü değildir  ( EN 81-20 m.5.5.2.2 )
    #  Dt 400 · dh 8 · yarım daire kanal:  Sf = 7,89 ( < 12 ) ama gerçekleşen
    #  S = 32,5 — hem Sf'nin hem Smin'in çok üstünde;  reddedilmemeli.
    _b1 = mukavemet.hesapla(
        {
            "tahrik_kasnak_capi": 400,
            "saptirma_kasnak_capi": 400,
            "saptirma_kasnak_min_capi": 400,
            "halat_capi": 8,
            "halat_adedi": 8,
            "kanal_sekli": "Yarım Daire Kanal",
        }
    )
    _s4 = [x for x in _b1["bolumler"] if x["baslik"].startswith("4 ")][0]
    r.kontrol(
        "B1  Sf < Smin ama S ikisinin de üstünde → bölüm 4 UYGUN",
        _s4["sonuc"]["uygun"] is True,
        f"→ Sf={_b1['ozet']['Sf']!r} S={_b1['ozet']['S_gercek']!r} {_s4['sonuc']['metin']!r}",
    )
    r.kontrol(
        "B1  Sf gerçekten Smin'in altında  ( ölçütün eskiden kestiği yer )",
        _b1["ozet"]["Sf"] < 12 < _b1["ozet"]["S_gercek"],
        f"→ {_b1['ozet']['Sf']!r} / {_b1['ozet']['S_gercek']!r}",
    )
    #  S gerçekten yetersizse bölüm yine kalmalı
    _b1k = mukavemet.hesapla(
        {"tahrik_kasnak_capi": 400, "saptirma_kasnak_capi": 400, "halat_capi": 8, "halat_adedi": 2}
    )
    _s4k = [x for x in _b1k["bolumler"] if x["baslik"].startswith("4 ")][0]
    r.kontrol(
        "B1  S yetersizse bölüm 4 yine UYGUN DEĞİL",
        _s4k["sonuc"]["uygun"] is False,
        f"→ S={_b1k['ozet']['S_gercek']!r}",
    )

    #  ── B2  Sonuç başlığı kontrolün gerçekten kullandığı eşiği yazar
    r.kontrol(
        "B2  bölüm 4 başlığı 40 eşiğini yazıyor",
        "40" in _s4["sonuc"]["baslik"] and "30" not in _s4["sonuc"]["baslik"],
        f"→ {_s4['sonuc']['baslik']!r}",
    )
    r.kontrol(
        "B2  bölüm 4 başlığı S ≥ max( Sf ; Smin ) diyor",
        "max( Sf ; Smin )" in _s4["sonuc"]["baslik"],
        f"→ {_s4['sonuc']['baslik']!r}",
    )

    #  ── B3  ω tanım aralığı dışında ÇÖKME yok, alan adını söyleyen hata var
    _g3 = mukavemet_girdi.tamamla(
        dict(mukavemet_girdi.varsayilanlar(), kabin_ray_profili="50 x 50 x 5", kabin_konsol_arasi=3900)
    )
    _h3 = mukavemet_girdi.dogrula(_g3)
    #  λ > 250 GİRDİYİ REDDETMEZ, UYARIR.  ω tanımsız kalır ve yalnız
    #  BURKULMA kontrolü düşer;  eğilme, birleşik gerilme, flanş ve sehim
    #  hesapları geçerlidir.  Hesabı büsbütün durdurmak öteki bölümlerin
    #  sonucunu da gizliyordu ( referans proje de "σk cannot be calculated" der ).
    r.esit("B3  λ > 250 girdi doğrulamasında REDDEDİLMİYOR", _h3, [])
    _u3 = mukavemet_girdi.uyarilar(_g3)
    r.kontrol(
        "B3  uyarı listesinde bildiriliyor",
        any("narin" in x and "konsollar arası" in x for x in _u3),
        f"→ {_u3}",
    )
    #  Senaryonun rayı 50 x 50 x 5:  imin = iy = 10,51 mm  →  250 × 10,51
    #  = 2.628 mm.  ( ix = 15,38 ile 3.845 çıkıyordu — bkz. sapma ㊴. )
    r.kontrol(
        "B3  uyarı, izin verilen en büyük aralığı söylüyor",
        any("2628" in x or "2.628" in x for x in _u3),
        f"→ {_u3}",
    )
    r.kontrol(
        "B3  burkulma kontrolü DÜŞÜYOR", mukavemet.hesapla(_g3)["bolumler"][6]["sonuc"]["uygun"] is False
    )
    #  İKİNCİ KALKAN:  doğrulama atlansa bile motor çökmemeli
    _dog = mukavemet_girdi.dogrula
    try:
        mukavemet_girdi.dogrula = lambda g: []
        _s3 = mukavemet.hesapla(_g3)
        _b7 = [x for x in _s3["bolumler"] if x["baslik"].startswith("7 ")][0]
        r.kontrol("B3  doğrulama atlansa bile motor çökmüyor", _s3["aktif"] is True)
        r.kontrol("B3  ω yoksa bölüm 7 UYGUN DEĞİL diyor", _b7["sonuc"]["uygun"] is False)
    except Exception as _e:  # noqa: BLE001
        r.kontrol("B3  doğrulama atlansa bile motor çökmüyor", False, f"→ {_e!r}")
    finally:
        mukavemet_girdi.dogrula = _dog
    #  λ alt sınırda kırpılıyor  ( bölüm 2 zaten öyle yapıyordu )
    _lam, _om = mukavemet._burkulma_omega(200, 19.48, 370)
    r.esit("B3  λ en az 20'ye kırpılıyor", _lam, 20)
    r.kontrol("B3  kırpılan λ'da ω var", _om is not None)

    #  ── B4  Halat kütlesinin taraf dağılımı  ( EN 81-50 m.5.11.2.2 )
    _o4 = {
        "ofis": uygulama_sabitleri.sabitler(None),
        "Q": 800.0,
        "P": 700.0,
        "r": 2,
        "nh": 7,
        "gh": 0.152,
        "F1": 0.0,
    }
    _g4 = mukavemet_girdi.varsayilanlar()
    _tam = _g4["seyir_mesafesi"] * 7 * 0.152
    for _durum, _alt in (("yukleme", True), ("fren_alt", True), ("fren_ust", False), ("bloke", False)):
        _t = mukavemet._terimler(_g4, _o4, _durum)
        _kabinde = _t["MSRcar"] > _t["MSRcwt"]
        r.kontrol(
            f"B4  '{_durum}' — kabin "
            + ("EN ALTTA → halat kabin tarafında" if _alt else "EN ÜSTTE → halat ağırlık tarafında"),
            _kabinde is _alt,
            f"→ MSRcar={_t['MSRcar']:.2f} MSRcwt={_t['MSRcwt']:.2f}",
        )
        r.kontrol(
            f"B4  '{_durum}' toplam halat kütlesi korunuyor",
            _yakin(_t["MSRcar"] + _t["MSRcwt"], _tam, 1e-6),
            f"→ {_t['MSRcar'] + _t['MSRcwt']:.3f} ≠ {_tam:.3f}",
        )
    #  Yüksek binada karar değişiyor — düzeltmenin emniyet etkisi
    _y = {
        "seyir_mesafesi": 76.0,
        "son_kat_yuksekligi": 3000,
        "halat_capi": 13,
        "halat_adedi": 8,
        "aski_orani": 1,
        "tahrik_kasnak_capi": 640,
        "saptirma_kasnak_capi": 640,
        "motor_gucu": 30,
    }
    _sy = mukavemet.hesapla(_y)
    r.kontrol("B4  76 m seyirde hesap yapılabiliyor", _sy["aktif"] is True, f"→ {_sy.get('hata')}")
    if _sy["aktif"]:
        _t1 = mukavemet._terimler(
            _sy["girdi"],
            {
                "ofis": uygulama_sabitleri.sabitler(None),
                "Q": 800.0,
                "P": 700.0,
                "r": 1,
                "nh": 8,
                "gh": 0.64,
                "F1": 0.0,
            },
            "yukleme",
        )
        r.kontrol(
            "B4  uzun kuyuda halat kütlesi kabin tarafında  ( yükleme )",
            _t1["MSRcar"] > 300 and _t1["MSRcwt"] == 0,
            f"→ {_t1['MSRcar']!r} / {_t1['MSRcwt']!r}",
        )

    #  ── B6  Sarılma açısı α tek sarımda 180°'yi aşamaz
    #  α artık türetilmiyor, BEYAN EDİLİYOR;  aralığı kendi girdisinde
    #  ( 1° – 360° ) ve bölüm 6'da kanal şekline göre ( tek sarım ≤ 180° )
    #  denetlenir.  Eski "Ra < Dt" kuralı geometrik modeli koruyordu, o
    #  model kalktı.
    r.kontrol(
        "B6  aralık dışı α girdi doğrulamasında reddediliyor",
        bool(
            mukavemet_girdi.dogrula(
                mukavemet_girdi.tamamla(dict(mukavemet_girdi.varsayilanlar(), sarilma_acisi=400))
            )
        ),
        "→ 400° kabul edildi",
    )
    #  Tek sarımda 180°'yi aşan açı artık GİRDİDE reddedilir ( kanal şekli
    #  ile birlikte ):  eskiden motor bölümü "uygun değil" sayıp üç yük
    #  durumuna "UYGUN" basıyordu.
    _v6b = mukavemet.hesapla({"sarilma_acisi": 200})
    r.kontrol(
        "B6  tek sarımda α > 180° girdide reddediliyor",
        not _v6b.get("aktif")
        and any("tek sarımlı kanalda 180°'yi aşamaz" in h for h in _v6b.get("hata") or []),
        f"→ {_v6b.get('hata')}",
    )
    _b6 = [x for x in mukavemet.hesapla({"sarilma_acisi": 180})["bolumler"] if x["baslik"].startswith("6 ")][
        0
    ]
    r.kontrol(
        "B6  bölüm 6'da α aralık kontrolü var",
        any("tek sarımlı" in str(a.get("aciklama", "")) for a in _b6["adimlar"]),
        "→ α kontrol satırı yok",
    )

    #  ── B7  Nequiv(t) ve pafta γ'sı ofis sabitini izliyor
    #  OFİS VARSAYILANI γ = 45°  ( Akış Asansör kullanım kılavuzu — bkz.
    #  sabitler.kanal_gama_v ).  Test sabiti değil, sabitin KENDİSİNİ izler.
    _n45 = mukavemet.hesapla()["ara"]["aski.Nequiv_t"]
    _n38 = mukavemet.hesapla({"_ofis": {"kanal_gama_v": 38}})["ara"]["aski.Nequiv_t"]
    #  ALTI KESİK V DE BİR V KANALDIR  ( Çizelge 2'nin V satırı, γ ile ).
    #  β satırından okumak 5,0 verirdi.
    r.esit("B7  altı kesik V, ofis γ = 45° → Nequiv(t) = 6,5", _n45, 6.5)
    r.esit("B7  altı kesik V γ = 38° → 12  ( V satırını izliyor )", _n38, 12.0)
    r.esit(
        "B7  altı kesik V'de β Nequiv'i DEĞİŞTİRMEZ",
        mukavemet.hesapla({"_ofis": {"kanal_beta": 100}})["ara"]["aski.Nequiv_t"],
        6.5,
    )
    #  ( Düz V kanal sertleştirilmemiş olamaz — m.5.11.2.3.1.2;  Nequiv(t)
    #    kanal işlemesinden bağımsızdır, sertleştirilmiş seçilir. )
    _sb = mukavemet.hesapla({"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmiş"})["ara"][
        "aski.Nequiv_t"
    ]
    _sb38 = mukavemet.hesapla(
        {"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmiş", "_ofis": {"kanal_gama_v": 38}}
    )["ara"]["aski.Nequiv_t"]
    r.esit("B7  V kanal ofis γ = 45° → 6,5", _sb, 6.5)
    r.esit("B7  V kanal γ = 38° → 12  ( ofis sabiti izleniyor )", _sb38, 12.0)
    #  β satırı ALTI KESİK YARIM DAİRE kanalda geçerlidir
    _uk = {
        b: mukavemet.hesapla({"kanal_sekli": "Altı Kesik Yarım Daire Kanal", "_ofis": {"kanal_beta": b}})[
            "ara"
        ]["aski.Nequiv_t"]
        for b in (90, 100)
    }
    r.esit("B7  altı kesik yarım daire β = 90° → 5", _uk[90], 5.0)
    r.esit("B7  altı kesik yarım daire β = 100° → 10", _uk[100], 10.0)
    #  Paftaya basılan γ, hesabın kullandığı γ ile aynı mı.
    #  BEKLENEN DEĞER OFİS SABİTİNİ İZLER — sayı olarak sabitlenirse
    #  varsayılan değişince test kırılır ve denetlediği şey ( pafta ile
    #  hesabın aynı γ'yı kullanması ) gözden kaybolur.
    _O7 = uygulama_sabitleri.sabitler(None)
    for _sekil, _bek in (
        ("V Kanal", _O7["kanal_gama_v"]),
        ("Yarım Daire Kanal", _O7["kanal_gama_yd"]),
        ("Altı Kesik V Kanal", _O7["kanal_gama_v"]),
    ):
        _s7 = mukavemet.hesapla({"kanal_sekli": _sekil, "kanal_isleme": "Sertleştirilmiş"})
        _b4x = [x for x in _s7["bolumler"] if x["baslik"].startswith("4 ")][0]
        _gam = [a["deger"] for a in _b4x["adimlar"] if a.get("sembol") == "γ"]
        r.esit(f"B7  '{_sekil}' paftada γ = hesabın γ'sı", _gam, [_bek])
    r.kontrol(
        "B7  V kanalın açısı β sütunundan okunmuyor",
        mukavemet_tablolari.kanal_acisi("Altı Kesik V Kanal", 38, 25) == 38,
        "→ altı kesik V kanalda γ hâlâ 90 okunuyor",
    )

    #  ── B8  Mil kuvveti ve moment askı oranına göre iniyor
    _m1 = mukavemet.hesapla({"aski_orani": 1})["ara"]["motor.M"]
    _m2 = mukavemet.hesapla({"aski_orani": 2})["ara"]["motor.M"]
    _p1 = mukavemet.hesapla({"aski_orani": 1})["ara"]["motor.Pm"]
    _p2 = mukavemet.hesapla({"aski_orani": 2})["ara"]["motor.Pm"]
    _gmax2 = mukavemet.hesapla({"aski_orani": 2})["ara"]["motor.Gmax"]
    r.kontrol(
        "B8  2:1'de moment = ( Gmax / 2 ) × Dt/2",
        _yakin(_m2, _gmax2 / 2 * 240 / 2000),
        f"→ {_m2!r} / {_gmax2!r}",
    )
    r.kontrol(
        "B8  askı oranı momenti değiştiriyor",
        _m1 != _m2 and _p1 != _p2,
        f"→ M {_m1!r}/{_m2!r} · Pm {_p1!r}/{_p2!r}",
    )

    #  ── B9  η TOPLAM SİSTEM VERİMİDİR:  askı oranı verimi değiştirmez
    _v0 = mukavemet.hesapla({"aski_orani": 2})["ara"]["motor.eta"]
    _v1 = mukavemet.hesapla({"aski_orani": 1})["ara"]["motor.eta"]
    r.kontrol(
        "B9  askı oranı η'yı DEĞİŞTİRMİYOR  ( uygulamada Δη yok )",
        _yakin(_v0, _v1),
        f"→ 2:1 {_v0!r} · 1:1 {_v1!r}",
    )
    r.kontrol(
        "B9  η ofis tablosundan birebir geliyor",
        _yakin(_v0, uygulama_sabitleri.VARSAYILAN["verim_dislisiz"]),
        f"→ {_v0!r} ≠ {uygulama_sabitleri.VARSAYILAN['verim_dislisiz']!r}",
    )
    r.kontrol(
        "B9  'toplam_verim' anahtarı artık girdi listesinde yok",
        "toplam_verim" not in [a[0] for a in mukavemet_girdi.ALANLAR],
    )

    #  ── B9b  Tst  —  kasnak statik yükü, denge zinciri DÂHİL
    #  Zincir Gmax'ta dengesizliği AZALTIR ama kasnak statik yükünde ARTIRIR;
    #  ikisi ayrı büyüklüktür.  Zincir Tst'ye girmezse yük olduğundan küçük
    #  çıkar ve kasnak yükü aşılmış bir makine "UYGUN" görünür — EMNİYETSİZ.
    _t0 = mukavemet.hesapla({"aski_orani": 2, "denge_zinciri": "Yok"})["ozet"]
    _t1 = mukavemet.hesapla({"aski_orani": 2, "denge_zinciri": "Var"})["ozet"]
    r.kontrol(
        "B9b denge zinciri Tst'yi ARTIRIYOR",
        _t1["Tst_hesap"] > _t0["Tst_hesap"],
        f"→ λ=0 {_t0['Tst_hesap']!r} · λ=100 {_t1['Tst_hesap']!r}",
    )
    r.kontrol(
        "B9b aynı zincir Gmax'ı AZALTIYOR  ( ters yönde )",
        _t1["N_hesap"] < _t0["N_hesap"],
        f"→ λ=0 {_t0['N_hesap']!r} · λ=100 {_t1['N_hesap']!r}",
    )
    #  Artış tam olarak MCR/i kadar olmalı
    _g9 = mukavemet.hesapla({"aski_orani": 2, "denge_zinciri": "Var"})["girdi"]
    _MCR = (
        2 * _g9["seyir_mesafesi"] * mukavemet_tablolari.halat_agirlik(_g9["halat_capi"]) * _g9["halat_adedi"]
    )
    r.kontrol(
        "B9b artış tam olarak MCR / i kadar",
        _yakin(_t1["Tst_hesap"] - _t0["Tst_hesap"], _MCR / 2),
        f"→ {_t1['Tst_hesap'] - _t0['Tst_hesap']!r} ≠ {_MCR / 2!r}",
    )
    #  ── B9c  Ds ( EN KÜÇÜK kasnak )  ile  Dp ( ORTALAMA )  AYRI kullanılır
    #  Kp = (Dt/Dp)⁴ ortalama bükülme şiddetidir;  m.5.5.2.1'in D/dr ≥ 40
    #  sınırı ise HER kasnak için geçerlidir — en küçüğe uygulanmalı.
    #  Ds ≤ D2'dir ( en küçük çap, ortalamayı aşamaz ) — senaryolar bu
    #  yönde kurulur.  Eski hâli D2 = 295'e Ds = 320 veriyordu:  geçerli
    #  bir tesis değil, artık dogrula da reddediyor.  Özellik AYNI yönde
    #  ama GEÇERLİ sayılarla, üstelik daha güçlü denetleniyor:  ortalama
    #  sınırı geçerken EN KÜÇÜK çap geçmiyorsa bölüm DÜŞMELİDİR.
    _dsz = {"tahrik_kasnak_capi": 320, "halat_capi": 8, "kasnak_tek_yon": 2, "motor_gucu": 11}
    _d_bos = mukavemet.hesapla(dict(_dsz, saptirma_kasnak_capi=295))
    _d_min = mukavemet.hesapla(dict(_dsz, saptirma_kasnak_capi=320, saptirma_kasnak_min_capi=295))
    _d_esit = mukavemet.hesapla(dict(_dsz, saptirma_kasnak_capi=320, saptirma_kasnak_min_capi=320))
    _d_200 = mukavemet.hesapla(dict(_dsz, saptirma_kasnak_capi=320, saptirma_kasnak_min_capi=200))
    _b4 = lambda x: [b for b in x["bolumler"] if b["baslik"].startswith("4")][0]
    #  Birleşik programda boş Ds çizimden gelir:  varsayılan çizimin en
    #  küçük kasnağı ( kabin kasnağı 240 );  ortalamayla ölçülmez.
    r.esit("B9c Ds boşken çizimdeki en küçük kasnak", _d_bos["girdi"].get("saptirma_kasnak_min_capi"), 240)
    r.kontrol(
        "B9c Ds boşken bölüm en küçük kasnakla düşüyor",
        _b4(_d_bos)["sonuc"]["uygun"] is False,
        "→ 240/8 = 30 < 40 olmalıydı",
    )
    #  D2 çizimin en küçük kasnağından küçük girilmişse Ds türetilmez
    #  ( yoksa dokunulmamış Ds "D2'den büyük — ters girilmiş" diye reddedilirdi ):
    #  hesap Ds'yi D2'ye düşürür, güvenli yön.
    _d_kucuk = mukavemet.hesapla(dict(_dsz, saptirma_kasnak_capi=200))
    r.kontrol(
        "B9c D2 < çizimin en küçüğü:  Ds türetilmiyor, hesap duruyor değil",
        _d_kucuk.get("aktif") and _d_kucuk["girdi"].get("saptirma_kasnak_min_capi") is None,
        f"→ {_d_kucuk.get('hata')}",
    )
    r.kontrol(
        "B9c ortalama 320 geçse de EN KÜÇÜK 295 düşürüyor",
        _b4(_d_min)["sonuc"]["uygun"] is False,
        f"→ {_b4(_d_min)['sonuc']['metin']}",
    )
    r.kontrol(
        "B9c Ds = D2 = 320 girilince geçiyor",
        _b4(_d_esit)["sonuc"]["uygun"] is True,
        f"→ {_b4(_d_esit)['sonuc']['metin']}",
    )
    r.kontrol("B9c Ds = 200 girilince reddediliyor", _b4(_d_200)["sonuc"]["uygun"] is False)
    #  Sf, Kp = (Dt/Dp)⁴ üzerinden ORTALAMA çapa bakar;  Ds yalnız
    #  m.5.5.2.1'in oran kontrolüne girer.  Karşılaştırma aynı D2 = 320
    #  üzerinde yapılır — D2 değişirse Sf'nin değişmesi zaten DOĞRUDUR.
    _d_d2 = mukavemet.hesapla(dict(_dsz, saptirma_kasnak_capi=320))
    r.kontrol(
        "B9c Ds, Sf'yi DEĞİŞTİRMİYOR  ( Kp hâlâ ortalamadan )",
        _yakin(_d_d2["ozet"]["Sf"], _d_esit["ozet"]["Sf"])
        and _yakin(_d_d2["ozet"]["Sf"], _d_min["ozet"]["Sf"])
        and _yakin(_d_d2["ozet"]["Sf"], _d_200["ozet"]["Sf"]),
        f"→ {_d_d2['ozet']['Sf']!r} · {_d_esit['ozet']['Sf']!r} · "
        f"{_d_min['ozet']['Sf']!r} · {_d_200['ozet']['Sf']!r}",
    )
    r.kontrol(
        "B9c D2 değişince Sf DEĞİŞİR  ( Kp ortalamadan )",
        not _yakin(_d_bos["ozet"]["Sf"], _d_d2["ozet"]["Sf"]),
        f"→ D2=295 {_d_bos['ozet']['Sf']!r} · D2=320 {_d_d2['ozet']['Sf']!r}",
    )

    #  ── B9c2  D/d < 40 ONAYLANMIŞ KURULUŞ BELGESİYLE kabul edilir
    #  m.5.5.2.1'in 40'ı uyumlaştırılmış standart şartıdır;  2014/33/AB Ek-I
    #  1.3 sayısal oran vermez.  Belge oran sınırını kaldırır, Sf'yi DEĞİL.
    _kc = {"tahrik_kasnak_capi": 240, "halat_capi": 6.5, "saptirma_kasnak_capi": 240, "kasnak_tek_yon": 2}
    _dd = lambda s, ad: [a for a in _b4(s)["adimlar"] if str(a.get("aciklama") or "").startswith(ad + " =")][
        0
    ]
    _k_yok = mukavemet.hesapla(dict(_kc))
    _k_var = mukavemet.hesapla(dict(_kc, kasnak_belgesi="Var"))
    r.esit("B9c2 belge varsayılanı Yok", _k_yok["girdi"]["kasnak_belgesi"], "Yok")
    r.kontrol(
        "B9c2 belgesiz 240 / 6,5 oranı reddediliyor",
        _dd(_k_yok, "Dt / dh")["metin"] == "UYGUN DEĞİL" and "Dt/dh = 36,92" in _b4(_k_yok)["sonuc"]["metin"],
        f"→ {_b4(_k_yok)['sonuc']['metin']}",
    )
    for _ad in ("Dt / dh", "Ds / dh"):
        r.esit(f"B9c2 belgeyle {_ad} kabul ediliyor", _dd(_k_var, _ad)["metin"], mukavemet.BELGEYLE_UYGUN)
    #  Belge satırı HANGİ maddeden sapıldığını yazar:  240 / 6,5'te ikisinden.
    r.kontrol(
        "B9c2 belgeli pafta belgeye dayandığını yazıyor",
        any(
            a.get("aciklama") == mukavemet_girdi.ALAN["kasnak_belgesi"][1]
            and "m.5.5.2.1" in str(a.get("kaynak"))
            and "m.5.5.1.2" in str(a.get("kaynak"))
            for a in _b4(_k_var)["adimlar"]
        )
        and "belge" in _b4(_k_var)["sonuc"]["baslik"],
    )

    #  ── B9c2b  HALAT ÇAPI ≥ 8 mm  ( m.5.5.1.2 a) ) — AYNI BELGEYLE AŞILIR
    #  Şart hiç denetlenmiyordu:  400 mm kasnakta ( oran 66 ) 6 mm halat,
    #  belgesiz, "UYGUNDUR" çıkıyordu.
    _c6 = {
        "halat_capi": 6,
        "tahrik_kasnak_capi": 400,
        "saptirma_kasnak_capi": 400,
        "halat_adedi": 8,
        "sarilma_acisi": 180,
    }
    _c6_yok, _c6_var = mukavemet.hesapla(dict(_c6)), mukavemet.hesapla(dict(_c6, kasnak_belgesi="Var"))
    r.kontrol(
        "B9c2b oran 66 olsa da 6 mm halat belgesiz reddediliyor",
        _b4(_c6_yok)["sonuc"]["uygun"] is False and "dh = 6 mm < 8 mm" in _b4(_c6_yok)["sonuc"]["metin"],
        f"→ {_b4(_c6_yok)['sonuc']['metin']}",
    )
    r.esit("B9c2b belgeyle 6 mm halat kabul ediliyor", _dd(_c6_var, "dh")["metin"], mukavemet.BELGEYLE_UYGUN)
    r.kontrol(
        "B9c2b belge satırı yalnız m.5.5.1.2'den sapmayı yazıyor ( oran tutuyor )",
        any(
            a.get("aciklama") == mukavemet_girdi.ALAN["kasnak_belgesi"][1]
            and "m.5.5.1.2" in str(a.get("kaynak"))
            and "m.5.5.2.1" not in str(a.get("kaynak"))
            for a in _b4(_c6_var)["adimlar"]
        ),
    )
    r.esit(
        "B9c2b 8 mm halat sınırı karşılıyor",
        _dd(
            mukavemet.hesapla({"halat_capi": 8, "tahrik_kasnak_capi": 320, "saptirma_kasnak_capi": 320}), "dh"
        )["metin"],
        "UYGUN",
    )
    #  Öğüt standardın ÖBÜR şartını çiğnetmemeli:  240 mm kasnakta 6,5 mm
    #  halata "halat çapını küçültün" demek 8 mm'nin daha da altına iterdi.
    _m65 = _b4(_k_yok)["sonuc"]["metin"]
    r.kontrol(
        "B9c2b 240 / 6,5'te öğüt standarda uyan çifti söylüyor",
        "en az 8 mm halat ve en az 320 mm kasnak" in _m65
        and "küçültün" not in _m65
        and "inceltin" not in _m65,
        f"→ {_m65}",
    )
    r.kontrol(
        "B9c2 belge Sf'yi DEĞİŞTİRMİYOR",
        _yakin(_k_yok["ozet"]["Sf"], _k_var["ozet"]["Sf"]),
        f"→ {_k_yok['ozet']['Sf']!r} · {_k_var['ozet']['Sf']!r}",
    )
    #  Belge Sf kontrolünü ezmemeli:  halat yetmiyorsa bölüm yine düşer.
    _k_az = mukavemet.hesapla(dict(_kc, kasnak_belgesi="Var", halat_adedi=2))
    r.kontrol(
        "B9c2 belgeli ama S < Sf ise bölüm yine UYGUN DEĞİL",
        _b4(_k_az)["sonuc"]["uygun"] is False
        and "halat çapını / adedini artırın" in _b4(_k_az)["sonuc"]["metin"]
        and "kasnağı çapını" not in _b4(_k_az)["sonuc"]["metin"],
        f"→ {_b4(_k_az)['sonuc']['metin']}",
    )
    _k_40 = mukavemet.hesapla({"tahrik_kasnak_capi": 320, "halat_capi": 8, "kasnak_belgesi": "Var"})
    r.esit("B9c2 oran ≥ 40 iken belge hükmü değiştirmiyor", _dd(_k_40, "Dt / dh")["metin"], "UYGUN")
    r.kontrol(
        "B9c2 geçersiz belge seçimi reddediliyor", not mukavemet.hesapla({"kasnak_belgesi": "Belki"})["aktif"]
    )

    #  ── B9c3  KUYU SÜRTÜNMESİ KUYUDAKİ KUVVETTİR  ( m.5.11.2.2 )
    #  Yüzde o taraftaki gövdenin ağırlık kuvvetine uygulanır ve formüle bir
    #  kez / r ile girer.  Eskiden ZATEN /r'li halat kuvvetinden alınıp bir kez
    #  daha /r yapılıyordu ( 2:1'de yarıya iniyordu ).  Oran ofis sabitidir ve
    #  paftada KABUL diye görünür.
    _s3 = mukavemet.hesapla({"aski_orani": 2, "sarilma_acisi": 180})
    _b6 = next(b for b in _s3["bolumler"] if b["kimlik"] == "tahrik_yetenegi")
    _fr = [a for a in _b6["adimlar"] if a.get("sembol") in ("FRcar", "FRcwt")]
    r.kontrol(
        "B9c3 paftada kabin ve ağırlık sürtünme oranı KABUL diye yazılı",
        len(_fr) == 2
        and all("KABUL" in str(a.get("kaynak")) and "m.5.11.2.2" in str(a.get("kaynak")) for a in _fr),
        f"→ {[(a.get('sembol'), a.get('kaynak')) for a in _fr]}",
    )
    r.esit("B9c3 varsayılan oranlar  %2 · %1,5", [a.get("deger") for a in _fr], [2, 1.5])
    _frs = [a for a in _b6["adimlar"] if str(a.get("formul") or "").startswith("FRcar =")]
    _gg = _s3["girdi"]
    _bek_fr = 0.02 * (_gg["kabin_agirligi"] + _gg["beyan_yuku"]) * (9.81 + _gg["acil_frenleme_a"])
    r.kontrol(
        "B9c3 fren alt FRcar = %2 × ( P + Q ) × ( gn + a )  ( halat kuvvetinden DEĞİL )",
        bool(_frs) and _yakin(_frs[0]["deger"], _bek_fr),
        f"→ {_frs[0]['deger'] if _frs else None!r} · beklenen {_bek_fr!r}",
    )
    r.kontrol("B9c3 yükleme ve blokede sürtünme satırı yok", len(_frs) == 2, f"→ {len(_frs)} FRcar satırı")
    _s0 = mukavemet.hesapla(
        {
            "aski_orani": 2,
            "sarilma_acisi": 180,
            "_ofis": {"kuyu_surtunme_kabin": 0, "kuyu_surtunme_agirlik": 0},
        }
    )
    r.kontrol(
        "B9c3 ofis sürtünmeyi 0 yapınca frenleme oranı büyüyor, statikler değişmiyor",
        _s0["ara"]["tahrik.fren_alt.oran"] > _s3["ara"]["tahrik.fren_alt.oran"]
        and _s0["ara"]["tahrik.fren_ust.oran"] > _s3["ara"]["tahrik.fren_ust.oran"]
        and _yakin(_s0["ara"]["tahrik.yukleme.oran"], _s3["ara"]["tahrik.yukleme.oran"])
        and _yakin(_s0["ara"]["tahrik.bloke.oran"], _s3["ara"]["tahrik.bloke.oran"]),
    )

    #  ── B9c4  GEZİCİ KABLONUN İMALATÇI AĞIRLIĞI tabloyu ezer
    _kt = mukavemet.hesapla({"aski_orani": 2, "sarilma_acisi": 180})
    _ke = mukavemet.hesapla({"aski_orani": 2, "sarilma_acisi": 180, "kablo_birim_kutle": 0.44})
    _mt = lambda s: next(a for a in s["bolumler"][0]["adimlar"] if a.get("sembol") == "mt")
    r.kontrol(
        "B9c4 boşken tablo kullanılıyor ve kaynağı yazılı",
        "tablo" in str(_mt(_kt).get("kaynak")) and _mt(_kt)["deger"] > 1.0,
        f"→ {_mt(_kt).get('deger')!r} · {_mt(_kt).get('kaynak')!r}",
    )
    r.kontrol(
        "B9c4 girilince imalatçı değeri kullanılıyor",
        _mt(_ke)["deger"] == 0.44 and "KATALOG" in str(_mt(_ke).get("kaynak")),
    )
    _H = _ke["girdi"]["seyir_mesafesi"]
    r.kontrol(
        "B9c4 aynı değer motora, P'ye ve tahrike giriyor",
        _yakin(
            _ke["ozet"]["N_hesap"] - _kt["ozet"]["N_hesap"],
            0.5
            * _H
            * (0.44 - _mt(_kt)["deger"])
            * _ke["girdi"]["beyan_hizi"]
            / (
                uygulama_sabitleri.verim(uygulama_sabitleri.sabitler(None), _ke["girdi"]["makine_tipi"]) * 102
            ),
        )
        and _ke["ara"]["tahrik.fren_ust.T1"] < _kt["ara"]["tahrik.fren_ust.T1"],
    )
    r.kontrol(
        "B9c4 fiziksel olmayan kablo ağırlığı reddediliyor",
        not mukavemet.hesapla({"kablo_birim_kutle": 50})["aktif"]
        and not mukavemet.hesapla({"kablo_birim_kutle": 0.01})["aktif"],
    )

    #  ── B9c5  PAFTADAKİ İŞLEM SATIRI YENİDEN HESAPLANABİLİR OLMALI
    #  tr() iki haneye yuvarlıyordu:  tampon satırında "0,07 × 1,60² × 1000 =
    #  173" ( 0,07 ile 179 çıkar, hesap 0,0674 ile ), halat "0,18" ( 0,179 ),
    #  f "0,23" ( 0,2327 ).  Satırdaki sayılarla hesaplayan denetçi paftanın
    #  sonucunu bulamıyordu.
    _ts = lambda tip, v: next(
        a
        for b in mukavemet.hesapla(
            {
                "sarilma_acisi": 180,
                "beyan_hizi": v,
                "tampon_tipi": tip,
                "halat_birim_kutle": 0.179,
                "kabin_tampon_boyu": 600,
                "kabin_tampon_ezilme": 500,
                "agirlik_tampon_ezilme": 500,
            }
        )["bolumler"]
        if b["kimlik"] == "tamponlar"
        for a in b["adimlar"]
        if str(a.get("formul") or "").startswith("s = ")
    )
    _hid = _ts("Hidrolik  ( enerji yutmalı )", 1.6)
    r.kontrol(
        "B9c5 enerji yutmalı tampon katsayısı 0,0674 yazılıyor",
        _hid["formul"].startswith("s = 0,0674 ×") and _hid["islem"].startswith("0,0674 ×"),
        f"→ {_hid['formul']!r} · {_hid['islem']!r}",
    )
    _yay = _ts("Yaylı  ( lineer )", 0.63)
    r.kontrol(
        "B9c5 lineer tampon katsayısı 0,135 yazılıyor",
        _yay["formul"].startswith("s = 0,135 ×"),
        f"→ {_yay['formul']!r}",
    )
    _s5 = mukavemet.hesapla({"sarilma_acisi": 180, "halat_birim_kutle": 0.179, "aski_orani": 2})
    _sat = {
        str(a.get("formul")): str(a.get("islem"))
        for b in _s5["bolumler"]
        for a in b["adimlar"]
        if a.get("formul")
    }
    r.kontrol(
        "B9c5 halat metre ağırlığı işlem satırında 0,179",
        _sat["Gh = gh × lh × nh"].startswith("0,179 ×") and " 0,179 × " in _sat["MSR = i × H × gh × ns"],
        f"→ {_sat['Gh = gh × lh × nh']!r}",
    )
    _efa = [
        a["islem"]
        for b in _s5["bolumler"]
        if b["kimlik"] == "tahrik_yetenegi"
        for a in b["adimlar"]
        if a.get("formul") == "e^(f·α)"
    ]
    r.kontrol(
        "B9c5 tahrik sınırında f dört haneyle  ( exp( f × α ) yeniden hesaplanır )",
        len(_efa) == 4
        and all(
            math.isclose(
                math.exp(float(x.split("exp( ")[1].split(" ×")[0].replace(",", ".")) * math.pi),
                v,
                rel_tol=2e-4,
            )
            for x, v in zip(
                _efa,
                (
                    _s5["ara"][h]
                    for h in (
                        "tahrik.yukleme.sinir",
                        "tahrik.fren_alt.sinir",
                        "tahrik.fren_ust.sinir",
                        "tahrik.bloke.sinir",
                    )
                ),
            )
        ),
        f"→ {_efa!r}",
    )

    #  ── B9c6  KLİPS İTME KUVVETİ HER RAYIN ALTINA İNER  ( m.5.2.1.8.4 )
    #  Karşı ağırlık rayında yalnız ağırlıkta güvenlik tertibatı varken
    #  sayılıyordu.  Kabin rayında Fk'nin içindeydi, şimdi ayrı kalem.
    _f0 = mukavemet.hesapla({"sarilma_acisi": 180})
    _f5 = mukavemet.hesapla({"sarilma_acisi": 180, "klips_itme_kuvveti": 500})
    r.kontrol(
        "B9c6 tertibatsız karşı ağırlıkta FAR, Fp kadar artıyor",
        _yakin(_f5["ozet"]["FAR"] - _f0["ozet"]["FAR"], 500.0),
        f"→ {_f5['ozet']['FAR'] - _f0['ozet']['FAR']!r}",
    )
    r.kontrol(
        "B9c6 kabin rayında FKR, Fp kadar artıyor  ( bir kez )",
        _yakin(_f5["ozet"]["FKR"] - _f0["ozet"]["FKR"], 500.0),
        f"→ {_f5['ozet']['FKR'] - _f0['ozet']['FKR']!r}",
    )
    _g6 = {"sarilma_acisi": 180, "agirlik_guvenlik_tertibati": "Kaymalı"}
    r.kontrol(
        "B9c6 ağırlıkta tertibat varken de Fp bir kez sayılıyor",
        _yakin(
            mukavemet.hesapla(dict(_g6, klips_itme_kuvveti=500))["ozet"]["FAR"]
            - mukavemet.hesapla(_g6)["ozet"]["FAR"],
            500.0,
        ),
    )
    _kt6 = next(b for b in _f5["bolumler"] if b["kimlik"] == "kuyu_tabani")
    r.kontrol(
        "B9c6 paftada Fp ayrı satır, varsayılanda satır yok",
        any(a.get("sembol") == "Fp" for a in _kt6["adimlar"])
        and not any(
            a.get("sembol") == "Fp"
            for b in _f0["bolumler"]
            if b["kimlik"] == "kuyu_tabani"
            for a in b["adimlar"]
        ),
    )

    #  ── B9d  Denge zinciri TAHRİK hesabına da girer  ( EN 81-50 m.5.11.2 )
    #  MCRcar / MCRcwt terimleri _T1 / _T2'de vardı ama hiç atanmıyordu.
    #  Zincirin dağılımı HALATIN TAM TERSİDİR ve toplamı her konumda sabittir.
    def _ter(zincir, durum):
        _g = mukavemet.hesapla({"aski_orani": 2, "denge_zinciri": zincir})["girdi"]
        _o = {"ofis": uygulama_sabitleri.sabitler(None)}
        mukavemet._motor(_g, _o)
        return mukavemet._terimler(_g, _o, durum), _o

    for _d in ("yukleme", "fren_alt", "fren_ust", "bloke"):
        _t0, _ = _ter("Yok", _d)
        r.kontrol(
            f"B9d zincirsizde MCR terimleri sıfır  ( {_d} )",
            _t0["MCRcar"] == 0.0 and _t0["MCRcwt"] == 0.0,
            f"→ {_t0['MCRcar']!r} / {_t0['MCRcwt']!r}",
        )
    _talt, _o1 = _ter("Var", "yukleme")  # kabin EN ALTTA
    _tust, _ = _ter("Var", "bloke")  # kabin EN ÜSTTE
    _MCR = _o1["MCR"]
    r.kontrol(
        "B9d kabin EN ALTTA → zincir KARŞI AĞIRLIK tarafında",
        _yakin(_talt["MCRcar"], 0.0) and _yakin(_talt["MCRcwt"], _MCR),
        f"→ car {_talt['MCRcar']!r} · cwt {_talt['MCRcwt']!r} · MCR {_MCR!r}",
    )
    r.kontrol(
        "B9d kabin EN ÜSTTE → zincir KABİN tarafında",
        _yakin(_tust["MCRcar"], _MCR) and _yakin(_tust["MCRcwt"], 0.0),
        f"→ car {_tust['MCRcar']!r} · cwt {_tust['MCRcwt']!r}",
    )
    r.kontrol(
        "B9d zincir kütlesi her konumda KORUNUYOR",
        _yakin(_talt["MCRcar"] + _talt["MCRcwt"], _tust["MCRcar"] + _tust["MCRcwt"]),
    )
    r.kontrol(
        "B9d zincir dağılımı HALATIN TERSİ",
        (_talt["MSRcar"] > _talt["MSRcwt"]) != (_talt["MCRcar"] > _talt["MCRcwt"]),
        f"→ MSR {_talt['MSRcar']:.1f}/{_talt['MSRcwt']:.1f} · "
        f"MCR {_talt['MCRcar']:.1f}/{_talt['MCRcwt']:.1f}",
    )

    r.kontrol(
        "B9b Tst girilmezse kontrol yapılmıyor, karar bozulmuyor",
        mukavemet.hesapla({"motor_gucu": 11})["bolumler"][0]["sonuc"]["uygun"] is True
        and mukavemet.hesapla({"motor_gucu": 11, "makine_tst": 100000})["bolumler"][0]["sonuc"]["uygun"]
        is True,
    )

    #  ── B10  Kabin önü girintisi  ( EN 81-20 m.5.4.2.1.3 )
    _a90 = mukavemet.hesapla({"uzun_pervaz": 90})["ozet"]["kabin_alani"]
    _a100 = mukavemet.hesapla({"uzun_pervaz": 100})["ozet"]["kabin_alani"]
    _a300 = mukavemet.hesapla({"uzun_pervaz": 300})["ozet"]["kabin_alani"]
    _kuru = 1450 * 1350 / 1e6
    r.kontrol(
        "B10  pervaz ≤ 100 mm alana katılmıyor",
        _yakin(_a90, _kuru) and _yakin(_a100, _kuru),
        f"→ 90:{_a90!r} 100:{_a100!r} kuru:{_kuru!r}",
    )
    r.kontrol(
        "B10  pervaz > 100 mm ise girintinin TAMAMI katılıyor",
        _yakin(_a300, _kuru + 900 * 300 / 1e6),
        f"→ {_a300!r} ≠ {_kuru + 0.27!r}",
    )

    #  ── B12  Regülatör:  ÇEKME kuvveti ve ikinci sınır imalatçıdan gelir
    #  m.5.6.2.2.1.1 d) regülatörün ÜRETTİĞİ kuvveti sınırlar — kasnağın iki
    #  yanındaki gerginlik FARKI ( Fçekme = F'reg − Freg ).  m.5.6.2.2.1.3 b)
    #  ise halattaki EN BÜYÜK gerginliği ( F'reg ) emniyet katsayısına sokar.
    #  ( α verilir ki eksik listesinde YALNIZ regülatörün eksiği kalsın —
    #    bu blok regülatörü denetler. )
    _s5 = mukavemet.hesapla({"sarilma_acisi": 180})
    _b5 = [x for x in _s5["bolumler"] if x["baslik"].startswith("5 ")][0]
    _h5 = _s5["ara"]
    r.kontrol(
        "B12  Fçekme = F'reg − Freg",
        _yakin(_h5["regulator.F_cekme"], _h5["regulator.Freg2"] - _h5["regulator.Freg"]),
        f"→ {_h5['regulator.F_cekme']!r} ≠ {_h5['regulator.Freg2'] - _h5['regulator.Freg']!r}",
    )
    r.kontrol(
        "B12  Fçekme halattaki toplam gerginlikten KÜÇÜK",
        0 < _h5["regulator.F_cekme"] < _h5["regulator.Freg2"],
        f"→ {_h5['regulator.F_cekme']!r} / {_h5['regulator.Freg2']!r}",
    )
    r.kontrol(
        "B12  emniyet katsayısı F'reg ile hesaplanıyor  ( m.5.6.2.2.1.3 b )",
        _yakin(_h5["regulator.S"], _h5["regulator.Tmin"] / _h5["regulator.Freg2"]),
        f"→ {_h5['regulator.S']!r}",
    )
    r.esit("B12  imalatçı kuvveti yoksa sınır 300 N", _h5["regulator.F_sinir"], 300)
    #  Girilmemişse 300 N denetlenir ve ikinci koşul fren bloğuna ŞART olarak
    #  yazılır:  Fçekme ≥ 2 × F  ⇔  F ≤ Fçekme / 2.
    r.kontrol(
        "B12  imalatçı kuvveti yoksa bölüm HESAP EKSİK değil",
        _b5["sonuc"]["uygun"] is True and not _b5.get("eksik_hesap"),
        f"→ {_b5['sonuc']!r}",
    )
    r.esit("B12  eksik hesap özete girmiyor", _s5["ozet"]["eksik_hesap"], [])
    r.kontrol(
        "B12  fren bloğu şartı Fçekme / 2",
        _yakin(_h5["regulator.Fgt_azami"], _h5["regulator.F_cekme"] / 2),
        f"→ {_h5['regulator.Fgt_azami']!r}",
    )
    r.kontrol(
        "B12  imalatçı kuvveti yoksa paftada şart satırı var",
        any(
            str(x.get("aciklama", "")).startswith("Şart:  Fgt")
            and "tip inceleme belgesi" in str(x.get("deger", ""))
            for x in _b5["adimlar"]
        ),
        f"→ {[x.get('aciklama') for x in _b5['adimlar']]}",
    )
    r.esit(
        "B12  imalatçı kuvveti girilince sınır 2 katı",
        mukavemet.hesapla({"guvenlik_devreye_kuvvet": 900})["ara"]["regulator.F_sinir"],
        1800,
    )
    r.esit(
        "B12  küçük imalatçı kuvvetinde 300 N belirleyici",
        mukavemet.hesapla({"guvenlik_devreye_kuvvet": 100})["ara"]["regulator.F_sinir"],
        300,
    )
    #  Kuvvet girilince bölüm yeniden hesaplanabilir hâle gelir
    _b5v = [
        x
        for x in mukavemet.hesapla({"guvenlik_devreye_kuvvet": 200})["bolumler"]
        if x["baslik"].startswith("5 ")
    ][0]
    r.kontrol(
        "B12  kuvvet girilince bölüm hesaplanıyor",
        _b5v["sonuc"]["uygun"] is True and "EKSİK" not in _b5v["sonuc"]["metin"],
        f"→ {_b5v['sonuc']!r}",
    )
    #  Ölçüt gerçekten Fçekme ile:  çok büyük bir imalatçı kuvvetinde kalmalı
    _b5r = [
        x
        for x in mukavemet.hesapla({"guvenlik_devreye_kuvvet": 9000})["bolumler"]
        if x["baslik"].startswith("5 ")
    ][0]
    r.kontrol("B12  aşırı imalatçı kuvvetinde bölüm kalıyor", _b5r["sonuc"]["uygun"] is False)

    # Toplam gerginin geçtiği, NET çekmenin kaldığı gerçek regresyon aralığı.
    _net = mukavemet.hesapla({"guvenlik_devreye_kuvvet": 1100})
    r.kontrol(
        "B12 net çekme yetersizken toplam gerilme uygunluk vermez",
        _net["ara"]["regulator.Freg2"] > 2200 > _net["ara"]["regulator.F_cekme"]
        and _net["bolumler"][4]["sonuc"]["uygun"] is False,
    )

    #  ── B12.2  Kabin tertibatı hız sınırı  ( TS EN 81-20 m.5.6.2.1.2.1 b) )
    _b5_ani_hizli = mukavemet.hesapla(
        {"beyan_hizi": 1.0, "guvenlik_tertibati": "Ani Frenlemeli", "guvenlik_devreye_kuvvet": 400}
    )["bolumler"][4]
    r.kontrol(
        "B12.2  v > 0,63 iken ani frenlemeli kabin tertibatı reddedilir",
        _b5_ani_hizli["sonuc"]["uygun"] is False and "0,63" in _b5_ani_hizli["sonuc"]["metin"],
        f"→ {_b5_ani_hizli['sonuc']!r}",
    )

    _b5_ani_yavas = mukavemet.hesapla(
        {"beyan_hizi": 0.63, "guvenlik_tertibati": "Ani Frenlemeli", "guvenlik_devreye_kuvvet": 400}
    )["bolumler"][4]
    r.kontrol(
        "B12.2  v ≤ 0,63 iken ani frenlemeli kabin tertibatı kabul edilir",
        _b5_ani_yavas["sonuc"]["uygun"] is True,
        f"→ {_b5_ani_yavas['sonuc']!r}",
    )

    #  ── B12.3  Regülatör devreye girme hızı penceresi  ( m.5.6.2.2.1.1 a) )
    _b5_reg_dusuk = mukavemet.hesapla(
        {"beyan_hizi": 1.0, "guvenlik_devreye_kuvvet": 400, "reg_devreye_hizi": 1.05}
    )["bolumler"][4]
    r.kontrol(
        "B12.3  v_dev < 1,15·v reddedilir",
        _b5_reg_dusuk["sonuc"]["uygun"] is False,
        f"→ {_b5_reg_dusuk['sonuc']!r}",
    )

    _b5_reg_uygun = mukavemet.hesapla(
        {"beyan_hizi": 1.0, "guvenlik_devreye_kuvvet": 400, "reg_devreye_hizi": 1.25}
    )["bolumler"][4]
    r.kontrol(
        "B12.3  1,15·v ≤ v_dev < v_üst kabul edilir",
        _b5_reg_uygun["sonuc"]["uygun"] is True,
        f"→ {_b5_reg_uygun['sonuc']!r}",
    )

    #  ── B13  Karşı ağırlıkta güvenlik tertibatı  ( EN 81-50 Ek C.2.1 )
    _yok = mukavemet.hesapla()["bolumler"][7]
    _var = mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})["bolumler"][7]
    r.kontrol(
        "B13  tertibat yokken C.2.1 hesaplanmıyor",
        "C.2.1" not in _yok["baslik"] + str(_yok.get("kaynak", "")),
        f"→ {_yok['baslik']!r}",
    )
    r.kontrol(
        "B13  tertibat varken C.2.1 adımları geliyor",
        any("m.C.2.1" in str(a.get("deger", "")) for a in _var["adimlar"]),
        "→ C.2.1 başlığı yok",
    )
    r.kontrol(
        "B13  C.2.1 adım sayısını artırıyor",
        len(_var["adimlar"]) > len(_yok["adimlar"]) + 10,
        f"→ {len(_yok['adimlar'])} → {len(_var['adimlar'])}",
    )
    #  k1 büyüdükçe ray zorlanır:  ani frenlemeli tertibatta 50x50x5 kalmalı
    r.kontrol(
        "B13  ani frenlemeli tertibatta ince ray UYGUN DEĞİL",
        mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Ani Frenlemeli"})["bolumler"][7]["sonuc"]["uygun"]
        is False,
    )

    #  ── B13.2  Karşı ağırlık tertibatı hız sınırı  ( TS EN 81-20 m.5.6.2.1.2.3 )
    _b8_ani_hizli = mukavemet.hesapla(
        {
            "beyan_hizi": 1.6,
            "agirlik_guvenlik_tertibati": "Ani Frenlemeli",
            "agirlik_ray_profili": "70 x 65 x 9",
        }
    )["bolumler"][7]
    r.kontrol(
        "B13.2  v > 1,0 iken ani frenlemeli karşı ağırlık tertibatı reddedilir",
        _b8_ani_hizli["sonuc"]["uygun"] is False
        and "kaymalı tip olmalıdır" in _b8_ani_hizli["sonuc"]["metin"],
        f"→ {_b8_ani_hizli['sonuc']!r}",
    )

    _b8_kaymali_hizli = mukavemet.hesapla(
        {"beyan_hizi": 1.6, "agirlik_guvenlik_tertibati": "Kaymalı", "agirlik_ray_profili": "70 x 65 x 9"}
    )["bolumler"][7]
    r.kontrol(
        "B13.2  v > 1,0 iken kaymalı karşı ağırlık tertibatı kabul edilir",
        _b8_kaymali_hizli["sonuc"]["uygun"] is True,
        f"→ {_b8_kaymali_hizli['sonuc']!r}",
    )

    #  ── B16  Regülatör μ'sü OFİS SABİTİ  ( EN 81-20 m.5.6.2.2.1.3 b) )
    #  Asansör bazında sorulmaz:  0,2'den küçük bir değer halatın emniyet
    #  katsayısını olduğundan iyi gösterirdi.  Üst sınır standardınkidir.
    r.kontrol("B16  μ asansör girdisi değil", "reg_surtunme" not in mukavemet_girdi.ALAN)
    r.esit("B16  sınır standardın verdiği değer", mukavemet_tablolari.REG_MU_AZAMI, 0.2)

    r.esit("B16  ofis varsayılanı µmax", uygulama_sabitleri.VARSAYILAN["reg_mu"], 0.2)
    _o16 = uygulama_sabitleri.sabitler({"reg_mu": 5})
    r.kontrol(
        "B16  ofiste µmax aşılamaz, değer reddedilir",
        _o16["reg_mu"] == 0.2 and "reg_mu" in _o16["_reddedilen"],
        f"→ {_o16['reg_mu']} / {_o16['_reddedilen']}",
    )
    r.esit(
        "B16  ofis küçük µ'yü kabul eder ve hesap onu kullanır",
        round(mukavemet.hesapla({"_ofis": {"reg_mu": 0.1}})["ara"]["regulator.f"], 4),
        round(0.1 / math.sin(math.radians(40) / 2), 4),
    )
    r.kontrol(
        "B16  asansöre yazılan μ hesabı değiştirmiyor",
        mukavemet.hesapla({"reg_surtunme": 0.05})["ara"]["regulator.S"]
        == mukavemet.hesapla({})["ara"]["regulator.S"],
    )

    #  ── B14  C.2.2'de ω YOKTUR — denetimin şüphesi yersizdi
    #  EN 81-50 Ek C.2.2.2:  σv = ( Fv + k3·Maux ) / A.  ω yalnız C.2.1.2'de
    #  geçer.  Motor bunu doğru yapıyor;  burada geri dönmediği denetlenir.
    _sc = mukavemet.hesapla()
    _pc = mukavemet_tablolari.ray("89 x 62 x 15,88", "A")
    _fv = _sc["ozet"]["Mg_kabin"] * 9.81
    _bek = (_fv + uygulama_sabitleri.sabitler(None)["k3_yardimci"] * 150) / _pc  # ω YOK
    _b7c = [x for x in _sc["bolumler"] if x["baslik"].startswith("7 ")][0]
    _sv = [a["deger"] for a in _b7c["adimlar"] if str(a.get("formul", "")).startswith("σv = ")]
    r.esit("B14  C.2.2'de tek bir σv satırı var", len(_sv), 1)
    r.kontrol(
        "B14  C.2.2'de burkulma ω'sız  ( EN 81-50 Ek C.2.2.2 )",
        bool(_sv) and _yakin(_sv[0], _bek),
        f"→ σv = {_sv!r}, ω'sız beklenen {_bek!r}",
    )
    #  C.2.1'de ω VARDIR — iki durumun ayrıldığı da denetlenir
    _sk = [a["deger"] for a in _b7c["adimlar"] if str(a.get("formul", "")).startswith("σk = ")]
    r.kontrol(
        "B14  C.2.1'de ω uygulanıyor  ( iki durum ayrı )", bool(_sk) and _sk[0] > _bek, f"→ σk = {_sk!r}"
    )

    #  ══════════════════════════════════════════════════════════════
    #  ÜÇÜNCÜ TUR  —  SAYISAL FİZİK DENETİMİNDE BULUNANLAR
    #  ══════════════════════════════════════════════════════════════
    #  ── C1  σ ve δ BÜYÜKLÜKTÜR;  işaretli karşılaştırma emniyetsizdi
    #  Kabin merkezi ray ekseninin öbür yanına düşünce ( xc < 0 ) Fx negatife
    #  iner;  δ = −5,59 mm iken "δ ≤ 5" SESSİZCE geçiyordu.
    _c1 = mukavemet.hesapla({"kabin_genisligi": 900, "ray_kapi_arasi": 1200, "kabin_konsol_arasi": 3800})
    r.kontrol("C1  negatif geometrili proje hesaplanabiliyor", _c1["aktif"], f"→ {_c1.get('hata')}")
    _b7c1 = [x for x in _c1["bolumler"] if x["baslik"].startswith("7 ")][0]
    _sayilar = [
        a["deger"]
        for a in _b7c1["adimlar"]
        if isinstance(a["deger"], (int, float)) and not isinstance(a["deger"], bool)
    ]
    r.kontrol(
        "C1  Fx işaretini koruyor  ( yön bilgisi paftada kalıyor )",
        any(x < 0 for x in _sayilar),
        "→ hiç negatif kuvvet yok",
    )
    for _ad, _on in (("σ", "σ"), ("δ", "δ")):
        _deg = [
            a["deger"]
            for a in _b7c1["adimlar"]
            if str(a.get("formul", "")).startswith(_on) and isinstance(a["deger"], (int, float))
        ]
        r.kontrol(
            f"C1  hiçbir {_ad} negatif yazılmıyor",
            all(x >= 0 for x in _deg),
            f"→ {[x for x in _deg if x < 0]}",
        )
    _dx = [a for a in _b7c1["adimlar"] if str(a.get("aciklama", "")).startswith("δx")]
    r.kontrol(
        "C1  δ = 5,59 mm  >  5 mm  →  UYGUN DEĞİL",
        any(a["deger"] == "UYGUN DEĞİL" for a in _dx),
        f"→ {[(a['aciklama'][:34], a['deger']) for a in _dx]}",
    )
    r.kontrol("C1  bölüm 7 bu geometride kalıyor", _b7c1["sonuc"]["uygun"] is False, f"→ {_b7c1['sonuc']}")
    #  σm artık iki eğilmeyi TOPLUYOR  ( ters işaretliler birbirini götürmüyor )
    _sm = [a["deger"] for a in _b7c1["adimlar"] if str(a.get("formul", "")).startswith("σm = ")]
    r.kontrol("C1  σm = |σx| + |σy|  ( götürme yok )", bool(_sm) and all(x >= 0 for x in _sm), f"→ {_sm}")

    #  ── C2  Karşı ağırlık tertibatının tepkisi kuyu tabanına gelir
    _far0 = mukavemet.hesapla()["ozet"]["FAR"]
    _mc = mukavemet.hesapla()["girdi"]["karsi_agirlik"]
    _n = mukavemet.hesapla()["girdi"]["agirlik_ray_sayisi"]
    for _tip in ("Kaymalı", "Ani Frenlemeli Makaralı", "Ani Frenlemeli"):
        _k1 = mukavemet_tablolari.darbe_k1(_tip)
        _far = mukavemet.hesapla({"agirlik_guvenlik_tertibati": _tip})["ozet"]["FAR"]
        _bek2 = _far0 + _k1 * mukavemet.SABIT["gn"] * _mc / _n
        r.kontrol(
            f"C2  '{_tip}' tepkisi FAR'a giriyor  ( {_far0:.0f} → {_far:.0f} N )",
            _yakin(_far, _bek2),
            f"→ {_far!r} ≠ {_bek2!r}",
        )
    r.kontrol(
        "C2  tertibat yokken FAR değişmiyor",
        _yakin(mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Yok"})["ozet"]["FAR"], _far0),
    )
    #  RAY KÜTLESİ BURADA DA BİR KEZ SAYILIR.  Bölüm 8'in Fk'si  Mg·gn'i
    #  içerir;  tabana giden tepki  Fk − Mg·gn  olmalıdır — yoksa ray hattının
    #  ağırlığı FAR'da iki kez görünürdü ( kabin tarafında düzeltilen ⑬ ).
    _s2 = mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})
    _mg_a = _s2["ozet"]["Mg_agirlik"] * mukavemet.SABIT["gn"]
    _tepki = _s2["ozet"]["FAR"] - _far0
    r.kontrol(
        "C2  tepkide ray kütlesi yok  ( Fk − Mg·gn )",
        _yakin(_tepki, 2 * mukavemet.SABIT["gn"] * _mc / _n),
        f"→ tepki {_tepki!r},  Mg·gn = {_mg_a!r}",
    )
    r.kontrol("C2  FAR özet ile ara değer aynı", _yakin(_s2["ara"]["kuyu.FAR"], _s2["ozet"]["FAR"]))

    #  ── C3  Karşı ağırlık kütlesi TEK yerden türer  ( ofis q'su )
    for _q in (0.40, 0.45, 0.50, 0.55, 0.60):
        _s3 = mukavemet.hesapla({"kabin_agirligi": 700, "beyan_yuku": 800, "_ofis": {"q_denge": _q}})
        _ga = _s3["ara"]["motor.Ga"]  # bölüm 1  —  motor · ağırlık tamponu
        _mcwt = _s3["girdi"]["karsi_agirlik"]  # bölüm 6 tahrik · bölüm 8 ray
        r.esit(f"C3  q = {_q}  →  Ga = Mcwt", (_ga, _mcwt), (700 + _q * 800, 700 + _q * 800))
        #  AĞIRLIK TAMPONU STANDARDIN KENDİ BAĞINTISINI KULLANIR.
        #  m.5.2.1.8.6:  F = 4·gn·( P + q·Q )  ve oradaki P "boş kabin +
        #  gezici kablo payı + denge zinciri"dir — karşı ağırlığın fiziksel
        #  kütlesi değil.  Zincirsiz bir tesiste ikisi neredeyse eşittir;
        #  zincir takılınca ayrışırlar ve standardın yazdığı BÜYÜK olandır.
        r.kontrol(
            f"C3  q = {_q}  ağırlık tamponu m.5.2.1.8.6 bağıntısıyla",
            _yakin(
                _s3["ozet"]["Fat"],
                mukavemet.SABIT["tampon_katsayi"] * mukavemet.SABIT["gn"] * (_P_std(_s3) + _q * 800),
            ),
            f"→ {_s3['ozet']['Fat']!r}",
        )
        r.kontrol(
            f"C3  q = {_q}  Fat ≥ 4·gn·Mcwt  ( fiziksel kütlenin üstünde )",
            _s3["ozet"]["Fat"] >= mukavemet.SABIT["tampon_katsayi"] * mukavemet.SABIT["gn"] * _mcwt - 1e-6,
        )

    #  ── C3b  İki kütlenin KAYNAĞI paftada yazılı
    #  Bölüm 8 karşı ağırlığın fiziksel kütlesini, bölüm 9 standardın P'siyle
    #  kurulan yükü basar;  ikisi bilerek farklıdır ( C3 ).  Paftayı elden
    #  denetleyen biri farkı hata sanabiliyordu:  iki satır da nasıl
    #  kurulduğunu yazmalı ve ekrandaki açıklamanın iddiası — fark yalnız
    #  gezici kablo payıdır — sayıyla tutmalı.

    for _z in ("Yok", "Var"):
        _s4 = mukavemet.hesapla({"denge_zinciri": _z})
        _g4 = _s4["girdi"]
        _b8 = next(b for b in _s4["bolumler"] if b["kimlik"] == "agirlik_raylari")
        _b9 = next(b for b in _s4["bolumler"] if b["kimlik"] == "kuyu_tabani")
        _mc = next(a for a in _b8["adimlar"] if a.get("sembol") == "Mcwt")
        _fa = next(a for a in _b9["adimlar"] if (a.get("formul") or "").startswith("Fat ="))
        r.kontrol(
            f"C3b zincir {_z}: Mcwt satırı nasıl kurulduğunu yazıyor",
            "boş kabin" in (_mc.get("kaynak") or "") and ("denge zinciri" in _mc["kaynak"]) == (_z == "Var"),
            f"→ {_mc.get('kaynak')!r}",
        )
        r.kontrol(
            f"C3b zincir {_z}: Fat satırı standardın maddesini yazıyor",
            "m.5.2.1.8.6" in (_fa.get("kaynak") or ""),
            f"→ {_fa.get('kaynak')!r}",
        )
        r.kontrol(
            f"C3b zincir {_z}: ekranda farkın nedeni açıklanıyor",
            any("m.5.2.1.8.6" in x and "gezici kablo" in x for x in _b9.get("aciklamalar") or []),
        )
        #  Gezici kablo payı motordan okunmaz:  0,5 · H · mt  ( iki kablo )
        _mtrav = (
            0.5
            * _g4["seyir_mesafesi"]
            * sum(
                mukavemet_tablolari.kablo_agirligi(_g4.get(k)) or 0.0
                for k in ("kablo_tipi_1", "kablo_tipi_2")
            )
        )
        _fark = _fa["deger"] / (mukavemet.SABIT["tampon_katsayi"] * mukavemet.SABIT["gn"]) - _mc["deger"]
        r.kontrol(
            f"C3b zincir {_z}: fark tam gezici kablo payı ( {_mtrav:.3f} kg )",
            _yakin(_fark, _mtrav),
            f"→ fark {_fark!r}",
        )

    #  ══════════════════════════════════════════════════════════════
    #  DÖRDÜNCÜ TUR  —  SINIR DURUMLARI
    #  ══════════════════════════════════════════════════════════════
    #  ── D1  Sistem verimi η fiziksel olmalı  ( 0 < η ≤ 1 )
    #  Δη KALDIRILDIĞI için η artık kendi başına negatife düşemez;  eski
    #  senaryolar ( η = 0,10 · Δη = 0,10 → sıfıra bölme;  Δη = 0,20 →
    #  η′ = −0,10 ve N = −44,26 kW ) yapısal olarak imkânsızdır.  Kalan risk
    #  ofis sabitinin kendisidir:  aralık dışı değerle HESAP YAPILMAZ.  Önce
    #  varsayılana dönülüyordu ve bunu hiçbir yer söylemiyordu — kullanıcı
    #  0,5 yazıyor, pafta 0,85 ile hesaplanıyordu.
    for _kotu in (0, -0.5, 1.5):
        _d1 = mukavemet.hesapla({"_ofis": {"verim_dislisiz": _kotu}})
        r.kontrol(f"D1  η = {_kotu} ile hesap yapılmıyor", _d1["aktif"] is False)
        r.kontrol(
            f"D1  η = {_kotu} hatası ofis alanını ve aralığı söylüyor",
            any("Ofis standardı" in h and "geçerli aralık" in h for h in _d1.get("hata") or []),
            f"→ {_d1.get('hata')}",
        )
    r.kontrol(
        "D1  η = 1 sınırı kabul ediliyor",
        mukavemet.hesapla({"_ofis": {"verim_dislisiz": 1.0}})["aktif"] is True,
    )
    #  İKİNCİ KALKAN:  doğrulama ATLANSA ve η yine de sıfır gelse bile
    #  N sıfıra bölünmemeli  ( motor doğrudan çağrıldığında ).
    _dog1, _ver1 = mukavemet_girdi.dogrula, uygulama_sabitleri.verim
    try:
        mukavemet_girdi.dogrula = lambda g: []
        uygulama_sabitleri.verim = lambda *a, **k: 0.0
        _d1x = mukavemet.hesapla({})
        r.kontrol(
            "D1  doğrulama atlansa bile sıfıra bölünmüyor",
            _d1x["aktif"] is True and _d1x["ozet"]["tumu_uygun"] is False,
        )
        r.kontrol(
            "D1  bölüm 1 'HESAP YAPILAMADI' diyor",
            any("HESAP YAPILAMADI" in (x.get("sonuc") or {}).get("metin", "") for x in _d1x["bolumler"]),
        )
    except Exception as _e:  # noqa: BLE001
        r.kontrol("D1  doğrulama atlansa bile sıfıra bölünmüyor", False, f"→ {_e!r}")
    finally:
        mukavemet_girdi.dogrula, uygulama_sabitleri.verim = _dog1, _ver1

    #  ── D2  Tampon / paten yığını kuyuya sığmalı  ( halat boyu > 0 )
    #  30 m paten arasında lh = −4,82 m, Gh = −5,13 kg;  negatif ağırlık
    #  yükten DÜŞÜLÜYOR — motor gücünü azaltıp Sf'yi yükseltiyordu.
    _d2 = mukavemet.hesapla({"kabin_paten_arasi": 30000})
    r.kontrol("D2  yığın kuyuya sığmıyorsa reddediliyor", _d2["aktif"] is False)
    r.kontrol(
        "D2  hata yığını ve kuyu boyunu sayıyor",
        any("yığını" in x and "kuyu boyundan" in x for x in (_d2.get("hata") or [])),
        f"→ {_d2.get('hata')}",
    )
    #  SINIRDA da reddedilmeli:  yığın TAM kuyu boyuna eşitken halat boyu
    #  ( paydan önce ) sıfırdır — fiziksel değildir.
    _gv = mukavemet_girdi.tamamla(mukavemet_girdi.varsayilanlar())
    _tam = (
        _gv["kuyu_boyu"]
        - _gv["agirlik_tampon_baba"]
        - _gv["agirlik_carpma_arasi"]
        + _gv["agirlik_tampon_ezilme"]
        - _gv["agirlik_paten_arasi"]
    )
    r.kontrol(
        "D2  sınırda ( yığın = kuyu boyu ) da reddediliyor",
        mukavemet.hesapla({"kabin_paten_arasi": _tam})["aktif"] is False,
        f"→ kabin paten arası {_tam:g} mm",
    )
    r.kontrol(
        "D2  sınırın 1 mm altı kabul ediliyor",
        mukavemet.hesapla({"kabin_paten_arasi": _tam - 1})["aktif"] is True,
    )
    #  Normal geometri geçmeye devam ediyor
    r.kontrol(
        "D2  normal paten arası kabul ediliyor",
        mukavemet.hesapla({"kabin_paten_arasi": 3400})["aktif"] is True,
    )
    _dog2 = mukavemet_girdi.dogrula
    try:
        mukavemet_girdi.dogrula = lambda g: []
        _d2x = mukavemet.hesapla({"kabin_paten_arasi": 30000})
        r.kontrol(
            "D2  doğrulama atlansa bile negatif halat 'uygun' olmuyor", _d2x["ozet"]["tumu_uygun"] is False
        )
        r.kontrol(
            "D2  negatif halat boyunda güç hesaplanmıyor",
            _d2x["ara"].get("motor.N") is None,
            f"→ {_d2x['ara'].get('motor.N')!r}",
        )
    finally:
        mukavemet_girdi.dogrula = _dog2

    #  ══════════════════════════════════════════════════════════════
    #  BEŞİNCİ TUR  —  SAPTIRMA KASNAĞI
    #  ══════════════════════════════════════════════════════════════
    #  ── E1  Dp / dh ≥ 40 denetlenmiyordu  ( TS EN 81-20 m.5.5.2.1 )
    #  Madde oranı "kasnak, makara ve tamburlar" için ister;  yalnız TAHRİK
    #  kasnağı sınanırsa Dt/dh = 400/8 = 50 ama Dp/dh = 240/8 = 30 olan
    #  tesiste halat bölümü UYGUN çıkar.
    _e_g = {"halat_capi": 8, "tahrik_kasnak_capi": 400, "saptirma_kasnak_capi": 240}

    def _b4(**ek):
        _s = mukavemet.hesapla(dict(_e_g, **ek))
        if not _s["aktif"]:
            return None, _s
        return [x for x in _s["bolumler"] if x["baslik"].startswith("4 ")][0], _s

    _e1b, _e1s = _b4()
    r.kontrol("E1  denetimin girdisi hesaplanabiliyor", _e1b is not None, f"→ {_e1s.get('hata')}")
    r.kontrol("E1  Ds/dh = 30 halat bölümünü DÜŞÜRÜYOR", _e1b["sonuc"]["uygun"] is False)
    r.kontrol(
        "E1  gerekçe saptırma kasnağını adıyla söylüyor",
        "saptırma kasnağı" in _e1b["sonuc"]["metin"],
        f"→ {_e1b['sonuc']['metin']!r}",
    )
    #  Oran kontrolü artık EN KÜÇÜK kasnak çapına ( Ds ) uygulanır;  Ds
    #  girilmezse çizimden gelir ( varsayılan çizimde 240 ), sonuç değişmez.
    r.kontrol(
        "E1  bölüm başlığı Ds/dh ölçütünü duyuruyor",
        "Ds/dh" in _e1b["sonuc"]["baslik"],
        f"→ {_e1b['sonuc']['baslik']!r}",
    )
    _dpsat = [a for a in _e1b["adimlar"] if "Ds / dh" in str(a.get("aciklama") or "")]
    r.kontrol(
        "E1  paftada Ds/dh kontrol satırı var",
        bool(_dpsat),
        f"→ {[a.get('aciklama') for a in _e1b['adimlar']][:6]}",
    )
    r.kontrol(
        "E1  o satır UYGUN DEĞİL diyor",
        bool(_dpsat) and _dpsat[0]["deger"] == "UYGUN DEĞİL",
        f"→ {_dpsat[0]['deger'] if _dpsat else None!r}",
    )
    #  SINIR:  tam 40 geçer, 1 mm altı geçmez  ( dh = 8 → Dp = 320 )
    r.kontrol(
        "E1  Ds/dh = 40 tam sınırı kabul ediliyor",
        _b4(saptirma_kasnak_capi=320, saptirma_kasnak_min_capi=320)[0]["sonuc"]["uygun"] is True,
    )
    r.kontrol(
        "E1  sınırın 1 mm altı reddediliyor",
        _b4(saptirma_kasnak_capi=319, saptirma_kasnak_min_capi=319)[0]["sonuc"]["uygun"] is False,
    )
    #  Tahrik kasnağı denetimi bozulmadı
    r.kontrol(
        "E1  tahrik kasnağı denetimi yerinde duruyor",
        _b4(tahrik_kasnak_capi=240, saptirma_kasnak_capi=320)[0]["sonuc"]["uygun"] is False,
    )
    #  KASNAK YOKSA denetlenecek kasnak da yoktur
    _e1y = _b4(kasnak_tek_yon=0, kasnak_ters_yon=0)[0]
    r.kontrol(
        "E1  kasnak yokken Ds oranı aranmıyor",
        _e1y["sonuc"]["uygun"] is True and "Ds/dh" not in _e1y["sonuc"]["baslik"],
        f"→ {_e1y['sonuc']['baslik']!r}",
    )
    r.kontrol(
        "E1  kasnak yokken pafta bunu YAZIYOR",
        any("kasnak yok" in str(a.get("deger") or "") for a in _e1y["adimlar"]),
        f"→ {[a.get('deger') for a in _e1y['adimlar']][:4]}",
    )
    #  Varsayılan proje bu yüzden düşmemeli  ( Dt = Dp = 240, dh = 10 → 24 )
    _v = mukavemet.hesapla({})
    _vb4 = [x for x in _v["bolumler"] if x["baslik"].startswith("4 ")][0]
    r.kontrol(
        "E1  varsayılan projede iki oran da AYNI sonucu veriyor",
        ("Dt/dh" in _vb4["sonuc"]["baslik"]) and ("Ds/dh" in _vb4["sonuc"]["baslik"]),
    )

    #  ── E2  xp RAY EKSENİNDEN ölçülmeli  ( TS EN 81-50 Ek C.2.1.1 )
    #  Fx = k1·gn·( Q·xQ + P·xp )/( n·h ) payı ray eksenine göre devirici
    #  momenttir;  xQ ray ekseninden ( xQ = xc + D/8 ), xp ise KABİN
    #  MERKEZİNDEN ölçülüyordu ve ray–kapı arası değişince hiç kımıldamıyordu.
    def _xcxp(**ek):
        #  Askı ray ekseninde ( xs = 0 ):  bulgu yükleme / kapı kuvvetinin
        #  işaretidir;  xs boş kalsa çizimden gelir ve RK ile birlikte kayardı.
        _s = mukavemet.hesapla(
            dict({"kabin_derinligi": 1400, "kabin_agirligi": 650, "aski_kaciklik_x": 0}, **ek)
        )
        if not _s["aktif"]:
            return None, None, _s
        _b = [x for x in _s["bolumler"] if x["baslik"].startswith("7 ")][0]
        _d = {a.get("sembol"): a["deger"] for a in _b["adimlar"] if a.get("sembol")}
        return _d.get("xc"), _d.get("xp"), _s

    #  Kapının kabin merkezine göre katkısı:  mkapı·( D/2 + pay ) / P
    _gv = mukavemet_girdi.tamamla(mukavemet_girdi.varsayilanlar())

    _mkapi = uygulama_sabitleri.sabitler(None)["kabin_kapisi_agirligi"]
    _kapi = _mkapi * (1400 / 2 + _gv["kapi_mekanizma_payi"]) / 650

    #  m.5.7.2.3.2:  P'nin etki noktası, P'yi oluşturan kütlelerin ORTAK
    #  ağırlık merkezidir.  Kapı düzeltmesi boş kabin kütlesine göre yapılır;
    #  gezici kablo ve zincirin yatay konumu bilinmediği için kabin
    #  merkezinde ( xc ) kabul edilir.
    def _xp_bek(_xc, _s):
        _Pb, _Ps = 650.0, _P_std(_s)
        return (_Pb * (_xc - _kapi) + (_Ps - _Pb) * _xc) / _Ps

    #  KABİN KAPISI AĞIRLIĞI OFİS STANDARDIDIR — asansör formunda sorulmaz.
    #  Değer imalatçı kataloğundan gelir ( Fermator 40/10 PM · 2 panel
    #  teleskopik · 800 × 2.000 mm · sac panel: 62 kg );  paftada kaynağı
    #  "KATALOG" yazar.  Ofis değeri değiştirirse xp aynı bağıntıyla izler.
    r.kontrol("E2  kabin kapısı ağırlığı asansör formunda yok", "kapi_agirligi" not in mukavemet_girdi.ALAN)
    r.esit("E2  kabin kapısı ağırlığı ofis standardı = 62 kg ( katalog )", _mkapi, 62)
    _xcK, _xpK, _sK = _xcxp(ray_kapi_arasi=650)
    _bK = [x for x in _sK["bolumler"] if x["baslik"].startswith("7 ")][0]
    _satirK = next(
        (a for a in _bK["adimlar"] if str(a.get("aciklama", "")).startswith("Kabin kapısı ağırlığı")), None
    )
    r.kontrol(
        "E2  paftada kapı ağırlığı satırı: 62 kg · KABUL",
        _satirK is not None and _satirK["deger"] == 62 and _satirK["kaynak"] == "KABUL  ·  kapı kataloğu",
        f"→ {_satirK}",
    )
    _, _xp120, _s120 = _xcxp(ray_kapi_arasi=650, _ofis={"kabin_kapisi_agirligi": 120})
    _P120 = _P_std(_s120)
    r.esit(
        "E2  ofis kapı ağırlığı 120 kg → xp aynı bağıntıyla kayıyor",
        _xp120,
        _xpK - (120 - 62) * (1400 / 2 + _gv["kapi_mekanizma_payi"]) / _P120,
    )

    _degerler = []
    for _rk in (500, 650, 830, 1000):
        _xc, _xp, _s5 = _xcxp(ray_kapi_arasi=_rk)
        _degerler.append((_rk, _xc, _xp))
        _bk = _xp_bek(_xc, _s5) if _xc is not None else None
        r.kontrol(
            f"E2  RK={_rk}: xp = ortak ağırlık merkezi  ( m.5.7.2.3.2 )",
            _xp is not None and abs(_xp - _bk) < 1e-9,
            f"→ xc={_xc}, xp={_xp}, beklenen {_bk}",
        )
    #  ASIL BULGU:  xp artık ray–kapı arasını İZLİYOR  ( eskiden sabitti )
    r.kontrol(
        "E2  xp ray–kapı arasıyla değişiyor",
        len({round(x[2], 6) for x in _degerler}) == len(_degerler),
        f"→ {[(x[0], x[2]) for x in _degerler]}",
    )
    #  Ray ekseni kabin merkezinden geçerken ( xc = 0 ) xp yalnız kapıdır
    _xc0, _xp0, _s0 = _xcxp(ray_kapi_arasi=1400 / 2 + mukavemet.SABIT["kabin_merkez_payi"])
    #  xc = 0'da yalnız kapı momenti kalır;  eklenen kütleler xc'de olduğu
    #  için momente katkı vermez, sadece paydayı büyütür.
    r.kontrol(
        "E2  xc = 0 iken xp = −kapı momenti / P",
        abs(_xc0) < 1e-9 and abs(_xp0 + 650.0 * _kapi / _P_std(_s0)) < 1e-9,
        f"→ xc={_xc0}, xp={_xp0}",
    )
    #  EMNİYETSİZ YÖN:  ray kapıya yaklaştıkça devirici moment BÜYÜR
    _mom = []
    for _rk in (500, 830):
        _xc, _xp, _s2 = _xcxp(ray_kapi_arasi=_rk)
        _b2 = [x for x in _s2["bolumler"] if x["baslik"].startswith("7 ")][0]
        _mom.append(
            next(a["deger"] for a in _b2["adimlar"] if str(a.get("formul") or "").startswith("Fx = k1"))
        )
    r.kontrol(
        "E2  ray kapıya yaklaşınca Fx büyüyor",
        abs(_mom[0]) > abs(_mom[1]),
        f"→ RK=500 Fx={_mom[0]:.1f} , RK=830 Fx={_mom[1]:.1f}",
    )

    #  ── E3  Yük EN OLUMSUZ konumda  ( TS EN 81-20 m.5.7.2.3.4 )
    #  xQ'yu her zaman xc + Dx/8 almak, xc < 0 iken boş kabinin momentini
    #  DENGELER ve gerilmeyi olduğundan küçük gösterir.
    def _b7(**ek):
        #  Askı ray ekseninde ( xs = 0 ):  bulgu yükleme / kapı kuvvetinin
        #  işaretidir;  xs boş kalsa çizimden gelir ve RK ile birlikte kayardı.
        _s = mukavemet.hesapla(
            dict({"kabin_derinligi": 1400, "kabin_agirligi": 650, "aski_kaciklik_x": 0}, **ek)
        )
        _b = [x for x in _s["bolumler"] if x["baslik"].startswith("7 ")][0]
        _xq = next(a["deger"] for a in _b["adimlar"] if str(a.get("formul") or "").startswith("Durum 1"))
        _fx = next(a["deger"] for a in _b["adimlar"] if str(a.get("formul") or "").startswith("Fx = k1"))
        _xc = {a.get("sembol"): a["deger"] for a in _b["adimlar"] if a.get("sembol")}["xc"]
        return _xc, _xq, _fx, _b

    #  Yardımcının kendisi:  momenti büyüten yönü seçmeli
    r.esit(
        "E3  merkez pozitifken + yön seçiliyor",
        mukavemet._yuk_merkezi(300.0, 175.0, 630.0, 650.0, 100.0),
        475.0,
    )
    r.esit(
        "E3  merkez negatifken − yön seçiliyor",
        mukavemet._yuk_merkezi(-300.0, 175.0, 630.0, 650.0, -100.0),
        -475.0,
    )
    r.esit(
        "E3  simetrikte ( merkez = 0, kol = 0 ) + yön",
        mukavemet._yuk_merkezi(0.0, 175.0, 630.0, 650.0, 0.0),
        175.0,
    )
    #  ASIL BULGU:  xc < 0 iken artık − yön seçiliyor ve Fx BÜYÜYOR
    for _rk, _bek in ((500, +1), (1200, -1)):
        _xc, _xq, _fx, _ = _b7(ray_kapi_arasi=_rk)
        r.kontrol(
            f"E3  RK={_rk}: xQ, xc'den {'+' if _bek > 0 else '−'} yönde kaydı",
            (_xq - _xc) * _bek > 0,
            f"→ xc={_xc}, xQ={_xq}",
        )
    #  Yalnız + yönle karşılaştırma:  o seçim HER ZAMAN daha küçük
    for _rk in (500, 830, 1000, 1200):
        _xc, _xq, _fx, _ = _b7(ray_kapi_arasi=_rk)
        _gv = mukavemet_girdi.tamamla(mukavemet_girdi.varsayilanlar())
        _arti_xq = _xc + 1400 / 8
        _arti_yon = abs(630 * _arti_xq + 650 * (_xc - _mkapi * (700 + _gv["kapi_mekanizma_payi"]) / 650))
        _bizim = abs(630 * _xq + 650 * (_xc - _mkapi * (700 + _gv["kapi_mekanizma_payi"]) / 650))
        r.kontrol(
            f"E3  RK={_rk}: seçilen yön yalnız + yönünkinden küçük DEĞİL",
            _bizim >= _arti_yon - 1e-9,
            f"→ bizim {_bizim:.0f}, + yön {_arti_yon:.0f}",
        )

    #  ── E4  Kapı konumu xi RAY EKSENİNDEN  ( TS EN 81-50 Ek C.1.2 )
    #  C.2.3'ün payı  gn·P·(xp−xs) + Fs·(xi−xs)  bir moment toplamıdır;
    #  xi'ye ray–kapı arasını HAM MESAFE ( hep artı ) yazmak, xc < 0 iken eşik
    #  kuvvetinin boş kabinin momentini DENGELEMESİ demektir.
    def _yuk_fx(**ek):
        #  Askı ray ekseninde ( xs = 0 ):  bulgu yükleme / kapı kuvvetinin
        #  işaretidir;  xs boş kalsa çizimden gelir ve RK ile birlikte kayardı.
        _s = mukavemet.hesapla(
            dict({"kabin_derinligi": 1400, "kabin_agirligi": 650, "aski_kaciklik_x": 0}, **ek)
        )
        _b = [x for x in _s["bolumler"] if x["baslik"].startswith("7 ")][0]
        _d = {a.get("sembol"): a["deger"] for a in _b["adimlar"] if a.get("sembol")}
        _fx = next(a["deger"] for a in _b["adimlar"] if str(a.get("formul") or "").startswith("Fx = ( gn"))
        return _d.get("xi"), _d.get("xp"), _fx

    for _rk in (500, 830, 1200):
        _xi, _xp, _fx = _yuk_fx(ray_kapi_arasi=_rk)
        r.esit(f"E4  RK={_rk}: xi ray ekseninden ( −RK )", _xi, -_rk)
    #  ASIL BULGU:  ray ekseni kabin merkezini geçince kuvvet BÜYÜMELİ
    _, _, _f830 = _yuk_fx(ray_kapi_arasi=830)
    _, _, _f1200 = _yuk_fx(ray_kapi_arasi=1200)
    r.kontrol(
        "E4  ray ekseni kabin merkezini geçince yükleme Fx'i büyüyor",
        abs(_f1200) > abs(_f830) > 100,
        f"→ RK=830 {_f830:.1f} N , RK=1200 {_f1200:.1f} N",
    )
    #  Ham mesafeyle karşılaştırma:  xc < 0'da o KÜÇÜK kalır
    _gv = mukavemet_girdi.tamamla(mukavemet_girdi.varsayilanlar())
    for _rk in (830, 1200):
        _xi, _xp, _fx = _yuk_fx(ray_kapi_arasi=_rk)
        _Fs = 0.4 * 9.81 * _gv["beyan_yuku"]
        _arti_yon = abs(9.81 * 650 * _xp + _Fs * (+_rk)) / (2 * _gv["kabin_paten_arasi"])
        r.kontrol(
            f"E4  RK={_rk}: doğrusu ham mesafeyle bulunandan BÜYÜK",
            abs(_fx) > _arti_yon,
            f"→ bizim {abs(_fx):.1f} , ham mesafe {_arti_yon:.1f}",
        )
    return r


def _girdi_yollari(r):
    """Girdi doğrulama ve hata yolları."""
    s = mukavemet.hesapla({"beyan_yuku": 777})
    r.kontrol("geçersiz beyan yükü hesabı durduruyor", not s["aktif"])
    r.kontrol(
        "hata metni alan adını içeriyor",
        any("Beyan yükü" in x for x in (s.get("hata") or [])),
        f"→ {s.get('hata')}",
    )

    #  KATLAR TEK TEK SORULMAZ:  seyir mesafesi ile son kat yüksekliği yeter.
    #  Eskiden "her durak pozitif" kuralı son kat yüksekliğini de koruyordu.
    s = mukavemet.hesapla({"seyir_mesafesi": None})
    r.kontrol("boş seyir mesafesi hesabı durduruyor", not s["aktif"])
    for _sk in (0, -500, None):
        s = mukavemet.hesapla({"son_kat_yuksekligi": _sk})
        r.kontrol(f"son kat yüksekliği {_sk!r} hesabı durduruyor", not s["aktif"], f"→ {s.get('hata')}")
    s = mukavemet.hesapla(
        {"seyir_mesafesi": 45, "son_kat_yuksekligi": 4200, "tabliye_yuksekligi": 750, "kuyu_dibi": 1600}
    )
    r.esit("kuyu boyu = seyir · 1000 + son kat + kuyu dibi", s["girdi"]["kuyu_boyu"], 45000 + 4200 + 1600)
    r.esit(
        "ray boyu = ( seyir · 1000 + son kat − 200 + kuyu dibi − 300 ) / 1000",
        s["ozet"]["ray_boyu"],
        (45000 + 4200 - 200 + 1300) / 1000,
    )
    #  Tabliye ray ve regülatör halatı boyuna girmez ( son kat kuyu tavanına
    #  ölçülür;  tabliye oda zemininden — 5 Eki ):  MRL ile aynı, tabliye ne olursa olsun
    _m = mukavemet.hesapla(
        {
            "seyir_mesafesi": 45,
            "son_kat_yuksekligi": 4200,
            "tabliye_yuksekligi": 750,
            "kuyu_dibi": 1600,
            "mk_yok": True,
        }
    )
    _t = mukavemet.hesapla(
        {"seyir_mesafesi": 45, "son_kat_yuksekligi": 4200, "tabliye_yuksekligi": 1200, "kuyu_dibi": 1600}
    )
    r.esit(
        "MRL ray boyu = ( seyir · 1000 + son kat − 200 + kuyu dibi − 300 ) / 1000",
        _m["ozet"]["ray_boyu"],
        (45000 + 4200 - 200 + 1300) / 1000,
    )
    r.kontrol(
        "ray boyu ve regülatör halatı tabliyeden bağımsız",
        s["ozet"]["ray_boyu"] == _t["ozet"]["ray_boyu"]
        and s["ara"]["regulator.gh"] == _t["ara"]["regulator.gh"] == _m["ara"]["regulator.gh"],
        f"→ {_m['ara']['regulator.gh']!r} / {s['ara']['regulator.gh']!r} / {_t['ara']['regulator.gh']!r}",
    )
    r.kontrol(
        "form durak listesi göndermiyor",
        all(a[3] != "liste" and "durak" not in a[0] for a in mukavemet_girdi.ALANLAR),
    )

    s = mukavemet.hesapla({"acil_frenleme_a": 12})
    r.kontrol("a > 1 gn reddediliyor", not s["aktif"])

    #  Tablosunda atalet yarıçapı olmayan NPU seçimi  ( 240 · 280 · 300 )
    s = mukavemet.hesapla({"dikine_kiris": 300})
    r.kontrol("verisi eksik NPU reddediliyor", not s["aktif"])
    r.kontrol(
        "eksik NPU hatası neyin eksik olduğunu söylüyor",
        any("ix" in x for x in (s.get("hata") or [])),
        f"→ {s.get('hata')}",
    )

    #  Bölen alanlarda sıfır
    for anahtar in ("halat_adedi", "kabin_ray_sayisi", "aski_orani"):
        s = mukavemet.hesapla({anahtar: 0})
        r.kontrol(f"{anahtar} = 0 reddediliyor", not s["aktif"])

    #  Arka karşı ağırlık hâlâ hesaplanmalı.  ( "halat arası" türetmesi
    #  kalktı — o değer yalnız α'nın payındaydı ve α artık girdi. )
    s = mukavemet.hesapla({"agirlik_yeri": "Arka"})
    r.kontrol("arka ağırlıkta hesap koşuyor", s["aktif"], f"→ {s.get('hata')}")
    r.kontrol(
        "halat arası artık girdi değil",
        "halat_arasi" not in (s.get("girdi") or {}),
        f"→ {(s.get('girdi') or {}).get('halat_arasi')!r}",
    )

    #  a = 1 gn sınırında T1 sıfırlanır — motor çökmemeli, tahrik yeteneğini
    #  UYGUN DEĞİL saymalı.
    s = mukavemet.hesapla({"acil_frenleme_a": 9.81})
    r.kontrol("a = 1 gn sınırında hesap çöküyor mu", s["aktif"], f"→ {s.get('hata')}")
    if s["aktif"]:
        r.kontrol("a = 1 gn'de tahrik yeteneği uygun değil", s["bolumler"][5]["sonuc"]["uygun"] is False)

    #  1. bükülgen kablonun tablodan gerçekten arandığını kanıtla:  1. kablo tipi değişince MTrav değişmeli.
    a1 = mukavemet.hesapla({"kablo_tipi_1": "24 x 0,75"})
    a2 = mukavemet.hesapla({"kablo_tipi_1": "12 x 0,75"})
    r.kontrol(
        "1. bükülgen kablo tipi sonuca giriyor",
        a1["aktif"]
        and a2["aktif"]
        and not _yakin(a1["ara"]["tahrik.fren_ust.T1"], a2["ara"]["tahrik.fren_ust.T1"]),
        "→ MTrav 1. kabloya duyarsız; kablo tipi sabitlenmiş",
    )

    #  Farklı profil / hız ile de çökmeden koşmalı
    for ek in (
        {"kabin_ray_profili": "127 x 89 x 16"},
        {"dikine_kiris": 200, "yan_yatak": 200},
        {"beyan_hizi": 2.5},
        {"aski_orani": 1},
        {"kanal_isleme": "Sertleştirilmiş"},
        {"guvenlik_tertibati": "Ani Frenlemeli"},
        {"agirlik_malzemesi": "Pik Döküm"},
        {"beyan_yuku": 2000, "kabin_genisligi": 2000, "kabin_derinligi": 2200, "kabin_agirligi": 1400},
    ):
        s = mukavemet.hesapla(ek)
        r.kontrol(f"varyant koşuyor: {ek}", s["aktif"], f"→ {s.get('hata')}")
        if s["aktif"]:
            r.kontrol(
                f"varyant bütün bölümleri üretti: {list(ek)[0]}",
                len(s["bolumler"]) == len(mukavemet.BOLUM_URETICILERI),
                f"→ {len(s['bolumler'])}",
            )

    #  ── Fiziksel sınır kalkanları ve yeni 4 girdi testleri
    #  1. Balata boyu fiziksel sınırları: 0, 10 mm ve paten aralığını aşanlar reddedilmeli
    r.kontrol("balata boyu = 0 reddediliyor", not mukavemet.hesapla({"paten_balata_boyu": 0})["aktif"])
    r.kontrol("balata boyu < 20 mm reddediliyor", not mukavemet.hesapla({"paten_balata_boyu": 10})["aktif"])
    r.kontrol(
        "balata boyu > paten arası reddediliyor", not mukavemet.hesapla({"paten_balata_boyu": 4000})["aktif"]
    )
    r.kontrol("balata boyu 60 mm geçerli", mukavemet.hesapla({"paten_balata_boyu": 60})["aktif"])

    #  2. Güv. devreye sokma kuvveti sıfır olamaz
    r.kontrol(
        "güv. devreye sokma kuvveti = 0 reddediliyor",
        not mukavemet.hesapla({"guvenlik_devreye_kuvvet": 0})["aktif"],
    )

    #  3. Karşı ağırlıkta güvenlik tertibatı varsa dperm = 5 mm (TS EN 81-20 m.5.7.4.6)
    s_yok = mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Yok"})
    b8_yok = [x for x in s_yok["bolumler"] if x["baslik"].startswith("8 ")][0]
    r.kontrol(
        "güv. tertibatsız karşı ağırlıkta dperm = 10 mm",
        any("δperm = 10" in a.get("aciklama", "") for a in b8_yok["adimlar"]),
    )

    s_var = mukavemet.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})
    b8_var = [x for x in s_var["bolumler"] if x["baslik"].startswith("8 ")][0]
    r.kontrol(
        "güv. tertibatlı karşı ağırlıkta dperm = 5 mm (TS EN 81-20 m.5.7.4.6)",
        any("δperm = 5" in a.get("aciklama", "") for a in b8_var["adimlar"]),
    )

    #  4. Yan ağırlıkta (Sağ) bina sehimi rayın yerel eksenlerine göre döner
    s_sag = mukavemet.hesapla({"agirlik_yeri": "Sağ", "yapi_sehim_x": 3.0, "yapi_sehim_y": 1.0})
    b8_sag = [x for x in s_sag["bolumler"] if x["baslik"].startswith("8 ")][0]
    # Yan ağırlıkta ray x'i bina y'sini (1.0), ray y'si bina x'ini (3.0) almalı
    dx_sag = next(a["deger"] for a in b8_sag["adimlar"] if a.get("formul", "").startswith("δx ="))
    dy_sag = next(a["deger"] for a in b8_sag["adimlar"] if a.get("formul", "").startswith("δy ="))
    s_arka = mukavemet.hesapla({"agirlik_yeri": "Arka", "yapi_sehim_x": 3.0, "yapi_sehim_y": 1.0})
    b8_arka = [x for x in s_arka["bolumler"] if x["baslik"].startswith("8 ")][0]
    dx_arka = next(a["deger"] for a in b8_arka["adimlar"] if a.get("formul", "").startswith("δx ="))
    dy_arka = next(a["deger"] for a in b8_arka["adimlar"] if a.get("formul", "").startswith("δy ="))
    r.kontrol(
        "yan ağırlıkta bina sehimi eksen dönüşümü çalışıyor", abs((dx_arka - dx_sag) - (3.0 - 1.0)) < 1e-6
    )
    #  ve y'de tersi:  arkada ray y'si bina y'sini ( 1,0 ), yanda bina x'ini
    #  ( 3,0 ) alır.  11 Eki'ye dek δy hesaplanıyor ama denetlenmiyordu.
    r.kontrol("yan ağırlıkta bina sehimi eksen dönüşümü ( y )", abs((dy_arka - dy_sag) - (1.0 - 3.0)) < 1e-6)

    #  5. Makaralı patende balata adımı ve Bölüm 8 formül adı
    s_mak = mukavemet.hesapla({"agirlik_paten_tipi": "Makaralı", "agirlik_guvenlik_tertibati": "Kaymalı"})
    b8_mak = [x for x in s_mak["bolumler"] if x["baslik"].startswith("8 ")][0]
    r.kontrol(
        "makaralı patende B8 flanş formülü 1,85 yazıyor",
        any("1,85" in a.get("formul", "") for a in b8_mak["adimlar"]),
    )

    #  6. Paten tipi ray başınadır:  kabinin seçimi karşı ağırlığa geçmez,
    #     girilen ℓ de yalnız kabin pateninindir.
    def _flans_formulu(s, no):
        b = next(x for x in s["bolumler"] if x["baslik"].startswith(f"{no} "))
        return [a.get("formul", "") for a in b["adimlar"] if "σF" in a.get("formul", "")]

    s_kk = mukavemet.hesapla({"paten_tipi": "Makaralı"})
    _f7, _f8 = _flans_formulu(s_kk, 7), _flans_formulu(s_kk, 8)
    r.kontrol(
        "kabin makaralı: B7 flanş formülü 1,85",
        any("1,85" in f for f in _f7) and not any("ℓ" in f for f in _f7),
        f"→ {_f7}",
    )
    r.kontrol(
        "kabin makaralı, ağırlık kaymalı: B8 flanş formülü balatalı",
        any("ℓ" in f for f in _f8) and not any("1,85" in f for f in _f8),
        f"→ {_f8}",
    )
    s_varsayilan = mukavemet.hesapla({})
    s_l = mukavemet.hesapla({"paten_balata_boyu": 140})
    r.kontrol(
        "girilen ℓ kabin rayının σF'sini değiştiriyor",
        s_l["ara"]["kabin_ray.c22.d1.sf"] != s_varsayilan["ara"]["kabin_ray.c22.d1.sf"],
    )
    r.esit(
        "girilen ℓ karşı ağırlık rayına geçmiyor  ( kendi rayından türetilir )",
        s_l["ara"]["agirlik_ray.sf"],
        s_varsayilan["ara"]["agirlik_ray.sf"],
    )

    #  ──────────────────────────────────────────────────────────────
    #  HÜKÜM GEREKÇESİ DÜŞEN KONTROLDEN GELİR
    #  ──────────────────────────────────────────────────────────────
    #  Beş bölüm, hangi alt kontrolün kaldığına bakmadan SABİT bir gerekçe
    #  basıyordu.  En açık kanıtı tampondu:  1,6 m/s'de 400 mm stroklu
    #  yaylı tamponda strok satırı UYGUN ( 400 ≥ 346 ) olmasına rağmen
    #  hüküm "en az 346 mm strok gerekir" diyordu;  asıl engel m.5.8.1.5.
    #  Regülatörde beş kontrolün üçü düşünce metin TAMAMEN boştu.
    def _hukum(s, kimlik):
        b = next(x for x in s["bolumler"] if x["kimlik"] == kimlik)
        return (b.get("sonuc") or {}).get("metin") or ""

    #  1. Tampon:  tip düşer, strok GEÇER  →  gerekçe stroku suçlamamalı
    _t = mukavemet.hesapla(
        {
            "beyan_hizi": 1.6,
            "tampon_tipi": "Yaylı  ( lineer )",
            "kabin_tampon_boyu": 500,
            "kabin_tampon_ezilme": 400,
            "agirlik_tampon_ezilme": 400,
        }
    )
    _m = _hukum(_t, "tamponlar")
    r.kontrol(
        "tampon:  tip düşüp strok geçince gerekçe TİP'i söylüyor",
        "tipi bu hıza uygun değil" in _m and "strok gerekir" not in _m,
        f"→ {_m}",
    )
    #     ikisi de düşerse ikisi de yazılır
    _t2 = mukavemet.hesapla(
        {
            "beyan_hizi": 1.6,
            "tampon_tipi": "Yaylı  ( lineer )",
            "kabin_tampon_ezilme": 90,
            "agirlik_tampon_ezilme": 90,
        }
    )
    _m2 = _hukum(_t2, "tamponlar")
    r.kontrol(
        "tampon:  tip ve strok birlikte düşerse ikisi de yazılıyor",
        "tipi bu hıza uygun değil" in _m2 and "strok gerekir" in _m2,
        f"→ {_m2}",
    )

    #  2. Regülatör:  Dreg/dreg düşer  →  hüküm çıplak kalmamalı
    _g = mukavemet.hesapla({"reg_kasnak_capi": 150})
    _mg = _hukum(_g, "regulator_halati")
    r.kontrol(
        "regülatör:  oran düşünce gerekçe yazılıyor",
        _mg.strip() not in ("UYGUN DEĞİLDİR", "UYGUN DEĞİLDİR.") and "Dreg" in _mg,
        f"→ {_mg}",
    )

    #  3. Makine:  hangi KİRİŞİN düştüğü söylenmeli ( E ile F ayrı eleman )
    _k = mukavemet.hesapla({"mk_yok": "Yok", "yan_yatak": 60})
    _mk = _hukum(_k, "makine_konstruksiyonu")
    r.kontrol(
        "makine:  düşen kirişin adı ve profili yazılıyor", "yan yatak" in _mk and "60" in _mk, f"→ {_mk}"
    )

    #  4. Ray:  flanş ( σF ) düşerse "konsol aralığını küçültün" DENMEZ —
    #     konsol aralığı l flanş bağıntısına hiç girmez.
    _r = mukavemet.hesapla({"paten_balata_boyu": 20, "kabin_konsol_arasi": 1500})
    _mr = _hukum(_r, "kabin_raylari")
    if "flanş" in _mr:
        _flans_kismi = _mr.split("flanş")[1]
        r.kontrol(
            "ray:  flanş düşünce konsol aralığının girmediği yazılıyor", "GİRMEZ" in _flans_kismi, f"→ {_mr}"
        )

    #  5. Hiçbir bölüm gerekçesiz RET vermiyor  ( sınıfın tamamı )
    for _gir in (
        {"reg_kasnak_capi": 150},
        {"mk_yok": "Yok", "yan_yatak": 60},
        {
            "beyan_hizi": 1.6,
            "tampon_tipi": "Yaylı  ( lineer )",
            "kabin_tampon_boyu": 500,
            "kabin_tampon_ezilme": 400,
            "agirlik_tampon_ezilme": 400,
        },
        {"kabin_konsol_arasi": 5000},
        {"siginma_tipi_dip": "Dik duruş"},
    ):
        _s = mukavemet.hesapla(_gir)
        for _b in _s["bolumler"]:
            _so = _b.get("sonuc") or {}
            if _so.get("uygun") is False:
                r.kontrol(
                    f"{_b['kimlik']}:  RET gerekçeli  ( {list(_gir)[0]} )",
                    _so.get("metin", "").strip().rstrip(".") != "UYGUN DEĞİLDİR",
                    f"→ {_so.get('metin')}",
                )
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
