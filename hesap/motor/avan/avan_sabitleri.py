# -*- coding: utf-8 -*-
"""
AVAN PROJESİNİN OFİS STANDARDI — ekrandaki adları ve hesap grupları

Değerler iki sözlükte durur ve öyle kalır ( avan_hesabi ):

    SABIT_B_VARSAYILAN  →  motorun "sabitler" sözlüğü
    OFIS_VARSAYILAN     →  asansör alanı boşsa kullanılan ofis değeri

Kullanıcı için bu ayrımın anlamı yoktur;  onun sorusu "bu sabit hangi hesaba
giriyor".  Bu yüzden ekranda tek liste vardır ve alanlar HESABA göre gruplanır.
İkisi de istekte aynı "sabitler" sözlüğüyle gider.

Etiketler eskiden yalnız eski arayüzdeydi ( hesap/static/ortak.js SABIT_ETIKET );
yeni ön yüz etiket uydurmasın diye sunucu söyler ( /api/secenekler ).
"""

from motor.avan import avan_hesabi

#  ( başlık, açıklama, alanlar )
GRUPLAR = (
    (
        "① Motor gücü ve kuvvetler",
        "MMO/697 s.18-21 — motor gücü, karşı ağırlık, ray ve kuyu dibi kuvvetleri",
        ("q_denge", "gr", "n_ray", "gf", "zincir_birim_kutle", "Fmk", "Fsh", "Fmt"),
    ),
    (
        "② Aydınlatma",
        "kabin · kuyu · makine dairesi aydınlatma hesapları",
        (
            "kabin_armatur_W",
            "kabin_armatur_lm",
            "kabin_ustu_armatur",
            "kuyu_armatur_W",
            "kuyu_armatur_lm",
            "kuyu_Dmax",
            "ayd_sutun",
        ),
    ),
    (
        "③ Kurulu güç ve gerilim düşümü",
        "IEC 60364-5-52 — kurulu güç, hat akımı, kablo ve gerilim düşümü",
        (
            "U",
            "kappa",
            "eps_max",
            "cosfi",
            "motor_elektrik_verimi",
            "priz_adedi",
            "priz_gucu",
            "S1",
            "S2",
            "L2",
            "L1_pay",
            "kablo_tipi",
            "sigorta_katsayisi",
        ),
    ),
    (
        "④ Temel topraklama",
        "IEEE Std 80 · BYKHY — temel ve çubuk topraklayıcı",
        ("beta", "cubuk_sayisi", "goz_araligi", "lc", "UL", "IDn"),
    ),
)

#  anahtar → ( etiket, açıklama )
ETIKET = {
    #  SABIT_B_VARSAYILAN
    "q_denge": ("q — Denge faktörü", "karşı ağırlığın dengelediği yük oranı"),
    "n_ray": ("n — Kabin kılavuz ray sayısı", "kabin daima iki raya oturur"),
    "gf": ("gf — Gezici kablo ( flexbil ) birim kütlesi (kg/m)", ""),
    "Fmt": ("Fmt — Montör ağırlığı (kg)", "kuyu üstü yükünde"),
    "kabin_armatur_W": ("Kabin armatürü gücü (W)", "LED spot"),
    "kabin_armatur_lm": ("Kabin armatürü ışık akısı (lm)", ""),
    "kabin_ustu_armatur": ("Kabin üstü armatür adedi", "kurulu güce eklenir"),
    "kuyu_armatur_W": ("Kuyu armatürü gücü (W)", ""),
    "kuyu_armatur_lm": ("Kuyu armatürü ışık akısı (lm)", ""),
    "kuyu_Dmax": ("Kuyu armatürü azami aralığı (m)", "0 = kontrol kapalı"),
    "priz_adedi": ("Priz adedi", ""),
    "priz_gucu": ("Priz başına güç (W)", ""),
    "cosfi": ("cosφ — Güç katsayısı", "hat akımı hesabında"),
    "motor_elektrik_verimi": (
        "Motorun elektrik verimi ηm",
        "şebekeden çekilen güç = mil gücü / ηm;  kablo ve sigorta bu akıma göre seçilir",
    ),
    "UL": ("UL — İzin verilen temas gerilimi (V)", "TT sistem"),
    "IDn": ("IΔn — Kaçak akım rölesi (A)", "300 mA = 0,30 A"),
    "lc": ("lç — Çubuk topraklayıcı boyu (m)", ""),
    "ayd_sutun": ("Aydınlatma verimi sütunu (1-10)", "Tablo-2 yansıma çifti"),
    #  OFIS_VARSAYILAN
    "U": ("U — Şebeke gerilimi (V)", "fazlar arası"),
    "kappa": ("κ — İletken iletkenliği (m/Ω·mm²)", ""),
    "eps_max": ("εmax — İzin verilen gerilim düşümü (%)", "yönetmelik sınırı"),
    "gr": ("gr — Kılavuz ray birim kütlesi (kg/m)", "ofis ray profili"),
    "Fmk": ("Fmk — Makine ağırlığı (kg)", ""),
    "Fsh": ("Fsh — Makine sehpası ağırlığı (kg)", ""),
    "zincir_birim_kutle": (
        "mz — Denge zinciri birim kütlesi (kg/m)",
        "yalnız zincir Var seçilen asansörde",
    ),
    "S1": ("S1 — Kolon hattı kesiti (mm²)", ""),
    "S2": ("S2 — Makine besleme kesiti (mm²)", ""),
    "L2": ("L2 — Makine besleme uzunluğu (m)", "pano – makine arası"),
    "kablo_tipi": ("Kablo tipi", "paftaya metin olarak yazılır"),
    "L1_pay": (
        "L1 yatay güzergâh payı (m)",
        "ana pano → kuyu → asansör panosu yatay kablo yolu;  L1 = Hk + bu pay",
    ),
    "beta": ("β — Toprak özgül direnci (Ω·m)", "zemin etüdü varsa o değeri yazın"),
    "cubuk_sayisi": ("Is — Çubuk topraklayıcı adedi", "paralel bağlı çubuk sayısı"),
    "goz_araligi": ("Karelaj gözü (m)", "şerit boyu temel ölçülerinden türetilirken kullanılır"),
    "sigorta_katsayisi": (
        "Motor sigortası kalkış katsayısı",
        "sigorta = bu katsayı × motor akımı, standart kademeye yuvarlanır",
    ),
}


def sema():
    """Ekranın ofis standardı formu:  gruplar, etiketler, varsayılanlar.

    Panelde görünmeyen yedek sabitler ( SABIT_B_YEDEK — askı oranı, asıl
    girişi asansör bazındadır ) listeye girmez."""
    yedek = set(avan_hesabi.SABIT_B_YEDEK)
    varsayilan = {
        k: v
        for k, v in {**avan_hesabi.SABIT_B_VARSAYILAN, **avan_hesabi.OFIS_VARSAYILAN}.items()
        if k not in yedek
    }
    return {
        "gruplar": [{"baslik": b, "aciklama": a, "alanlar": list(al)} for b, a, al in GRUPLAR],
        "etiket": {k: list(v) for k, v in ETIKET.items()},
        "varsayilan": varsayilan,
        #  Sayı olmayanlar ( kablo tipi ):  ekran sayı diye okumaz
        "metin": [k for k, v in varsayilan.items() if isinstance(v, str)],
    }
