"""MAKİNE DAİRESİNDE YANDAKİ AĞIRLIK KABİNE GÖRE ( 22 Kas — "fazla yer zarar vermez" taraması ).

Rayı – duvar boşken ağırlık duvara yaslanıyordu:  kuyu genişleyince kabinden uzaklaşıyor,
sarım açısı düşüyordu ( 630-md +400:  156,3 → 146,7°;  1275-md +400:  180 → 173,3° ).  Artık
kabin rayının ara kirişinden en çok kopru.YAN_AGIRLIK_ARA_KIRIS_AZAMI uzakta;  dar kuyuda
eski yer kalır, halat geometrisi izin vermiyorsa ( 1:1 halat aralığı < D1, 2:1 düşey halat
çarpıyor ) kaymaz.
"""

import json
import unittest

from cizim import girdi, kopru, sabitler
from testler import altin_cizim
from uclar import cizim_uclari, uygulama_istegi

TASLAK = {t["kimlik"]: t for t in json.load(open("on-yuz/src/lib/taslaklar.json", encoding="utf-8"))}


def _istek(kimlik, asansor_ek=None, proje_ek=None, sil=()):
    t = TASLAK[kimlik]
    a = {**t["asansor"], **{k: str(v) for k, v in (asansor_ek or {}).items()}}
    for k in sil:
        a.pop(k, None)
    return {
        "asansorler": [a],
        "proje_geneli": {**t["proje_geneli"], **{k: str(v) for k, v in (proje_ek or {}).items()}},
    }


def _girdi(v):
    asansorler, ortak = uygulama_istegi.asansor_girdileri(v)
    g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, None, "", 0)
    return g, hata


def _ara_kiris_boslugu(g):
    S = sabitler.sabitler(g.get("_cizim_sabitleri"))
    K = girdi.kabin_ve_agirlik_kutulari(g, S)
    kr = g["kabin_ray"]
    if g["agirlik"]["yeri"] == "Sağ":
        return K["agirlik"][0] - (K["kx"] + kr["arasi"] / 2.0 + kr["h"] + S["ara_kiris_en"])
    return (K["kx"] - kr["arasi"] / 2.0 - kr["h"] - S["ara_kiris_en"]) - K["agirlik"][2]


def _genis(kimlik, ek, **diger):
    t = TASLAK[kimlik]
    return _istek(
        kimlik,
        {"kuyu_genisligi": int(t["asansor"]["kuyu_genisligi"]) + ek, **diger},
        {"mk_genislik": int(t["proje_geneli"]["mk_genislik"]) + 400}
        if "mk_genislik" in t["proje_geneli"]
        else None,
    )


class YanAgirlikKabineGore(unittest.TestCase):
    def test_aci_zaten_180_ise_kaydirilmaz(self):
        """1275-md:  dar kuyuda açı 180° — 33 mm kaydırmak makine konstrüksiyonunu düşürüyordu."""
        g, hata = _girdi(_istek("1275-md"))
        self.assertEqual(hata, [])
        self.assertEqual(kopru.sarim_acisi(g), 180.0)
        self.assertAlmostEqual(g["agirlik"]["ray_duvar"], 100.0, places=6)

    def test_dar_kuyuda_eski_yer(self):
        """Hazır 1:1 asansörlerde açıklık zaten sınırın altında:  ağırlık yerinde."""
        for kimlik in ("630-md", "800-md", "1000-md"):
            with self.subTest(kimlik=kimlik):
                g, hata = _girdi(_istek(kimlik))
                self.assertEqual(hata, [])
                self.assertAlmostEqual(g["agirlik"]["ray_duvar"], 127.5, places=6)

    def test_genis_kuyuda_aci_korunur(self):
        for kimlik in ("630-md", "800-md", "1000-md", "1275-md"):
            taban, _ = _girdi(_istek(kimlik))
            a0 = kopru.sarim_acisi(taban)
            for ek in (200, 400):
                with self.subTest(kimlik=kimlik, ek=ek):
                    g, hata = _girdi(_genis(kimlik, ek))
                    self.assertEqual(hata, [])
                    aci = kopru.sarim_acisi(g)
                    self.assertGreaterEqual(aci, a0 - 0.5)
                    #  Açı zaten 180° ise kaydırılmaz ( makine kirişinin yükü değişirdi )
                    if aci < 180.0:
                        self.assertLessEqual(_ara_kiris_boslugu(g), kopru.YAN_AGIRLIK_ARA_KIRIS_AZAMI + 0.5)

    def test_iki_bir_kabin_altinda_halat_duseyde(self):
        """1250-md'nin rayı – duvarı boşaltılınca kural:  her genişlikte 180°."""
        for ek in (0, 200, 400):
            with self.subTest(ek=ek):
                v = _genis("1250-md", ek)
                v["asansorler"][0].pop("agirlik_ray_duvar")
                g, hata = _girdi(v)
                self.assertEqual(hata, [])
                self.assertEqual(kopru.sarim_acisi(g), 180.0)

    def test_girilen_ray_duvar_kullanilir(self):
        """Taslağın girdiği 165 ( ofisin gerçek projesi ) kurala bırakılmaz."""
        g, _ = _girdi(_genis("1250-md", 400))
        self.assertAlmostEqual(g["agirlik"]["ray_duvar"], 165.0, places=6)

    def test_makine_dairesizde_uygulanmaz(self):
        taban, _ = _girdi(_istek("630"))
        g, _ = _girdi(
            _istek("630", {"kuyu_genisligi": int(TASLAK["630"]["asansor"]["kuyu_genisligi"]) + 400})
        )
        self.assertAlmostEqual(g["agirlik"]["ray_duvar"], taban["agirlik"]["ray_duvar"], places=6)

    def test_halat_carpiyorsa_kaymaz(self):
        """Örnek proje ( 2:1 kabin altı, ø240, kabin 130 kaçık ):  yaklaşınca düşey halat kabin
        rayına biniyordu ( eski aralığa dönüş "öbür teğetinden içeride" reddi verirdi ) — yer aynı."""
        asansorler, ortak = uygulama_istegi.asansor_girdileri(altin_cizim.duzenler()["örnek makine daireli"])
        g, hata = cizim_uclari.asansor_girdisi(asansorler, ortak, None, "", 0)
        self.assertFalse([h for h in hata if "teğetinden" in str(getattr(h, "metin", h))])
        self.assertGreater(_ara_kiris_boslugu(g), kopru.YAN_AGIRLIK_ARA_KIRIS_AZAMI)


if __name__ == "__main__":
    unittest.main()
