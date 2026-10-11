"""ÇİZİMLERİN ALTIN ÇIKTISI ( testler/altin_cizim.py ) — her düzenin paftası
dondurulmuş olanla AYNI olmalı.

Fark çıkarsa ileti hangi düzende, hangi çizimde, kaçıncı elemanda ve neyin
değiştiğini söyler.  Değişiklik kasıtlıysa ( çizim davranışı bilerek
değiştiyse ) farklar incelenip dosya yeniden üretilir:

    .venv/bin/python -m testler.altin_cizim
"""

import json
import os
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from testler import altin_cizim

#  İletide gösterilen en çok fark ( düzen başına )
AZAMI_FARK = 5


def _kisa(x, boy=160):
    s = json.dumps(x, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= boy else s[:boy] + " …"


def farklar(eski, yeni):
    """Bir düzenin iki kaydı arasındaki farklar:  [ ileti ]."""
    if ("hata" in eski) != ("hata" in yeni):
        ne = lambda k: "reddediliyor:  " + k["hata"][0] if "hata" in k else "çiziliyor"
        return [f"hüküm değişti — önce {ne(eski)}, şimdi {ne(yeni)}"]
    if "hata" in eski:
        return (
            []
            if eski["hata"] == yeni["hata"]
            else [f"ret sebebi değişti:  {_kisa(eski['hata'])}  →  {_kisa(yeni['hata'])}"]
        )
    out = []
    ec, yc = eski["cizimler"], yeni["cizimler"]
    if eski["sira"] != yeni["sira"]:
        out.append(f"paftanın çizimleri değişti:  {eski['sira']}  →  {yeni['sira']}")
    for ad in (a for a in eski["sira"] if a in yc):
        e, y = ec[ad], yc[ad]
        for alan in ("baslik", "olcek"):
            if e[alan] != y[alan]:
                out.append(f"{ad}:  {alan}  {e[alan]!r}  →  {y[alan]!r}")
        ee, ye = e["elemanlar"], y["elemanlar"]
        if len(ee) != len(ye):
            out.append(f"{ad}:  eleman sayısı {len(ee)} → {len(ye)}")
        for i, (a, b) in enumerate(zip(ee, ye)):
            if a != b:
                anahtar = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                out.append(
                    f"{ad}:  {i}. eleman ( {a.get('tip')} · {a.get('katman')} · "
                    f"{a.get('ad', '')} ) değişti — {anahtar}:  "
                    f"{_kisa({k: a.get(k) for k in anahtar})}  →  "
                    f"{_kisa({k: b.get(k) for k in anahtar})}"
                )
                break
        if ee == ye and e["svg"] != y["svg"]:
            out.append(f"{ad}:  elemanlar aynı, SVG çıktısı değişti ( cizim/svg.py )")
    return out


class AltinCizim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eski = altin_cizim.oku()
        cls.yeni = altin_cizim.uret()

    def test_duzenler_ayni(self):
        self.assertEqual(
            sorted(self.yeni), sorted(self.eski), "düzen listesi değişti — altin_cizim.duzenler()"
        )

    def test_her_duzenin_paftasi_ayni(self):
        for ad in self.eski:
            if ad not in self.yeni:
                continue
            with self.subTest(duzen=ad):
                f = farklar(self.eski[ad], self.yeni[ad])
                self.assertEqual(
                    f,
                    [],
                    "\n  "
                    + "\n  ".join(f[:AZAMI_FARK])
                    + (f"\n  ( + {len(f) - AZAMI_FARK} fark )" if len(f) > AZAMI_FARK else ""),
                )

    def test_kapsam(self):
        #  Altın düzenler programın bütün yollarını kapsamalı:  makine dairesiz ve
        #  daireli, ağırlık sağda / solda / arkada, kabin altı / kabin üstü / 1:1
        #  askı, reddedilen düzenler.
        cizilen = [k for k in self.eski.values() if "cizimler" in k]
        self.assertGreaterEqual(len(cizilen), 25)
        self.assertGreaterEqual(sum(1 for k in self.eski.values() if "hata" in k), 3)
        cizimler = set().union(*(k["cizimler"] for k in cizilen))
        self.assertTrue(
            {
                "makine_dairesi",
                "delik_plani",
                "kuyu_ustu",
                "kabin_ustu",
                "kuyu_dibi",
                "kuyu_kesiti_yan",
                "kuyu_kesiti_on",
                "kasnak_duzeni",
                "giris",
                "kapi_kesiti",
                "kuyu_plani",
            }
            <= cizimler,
            cizimler,
        )


class FarkIletisi(unittest.TestCase):
    """Fark iletisinin kendisi:  yanlış bir şeyi söylerse düzenleme yanıltır."""

    def test_eleman_farki_yeri_ve_anahtariyla(self):
        e = {
            "sira": ["kuyu_plani"],
            "cizimler": {
                "kuyu_plani": {
                    "baslik": "B",
                    "olcek": 20,
                    "svg": "1",
                    "elemanlar": [
                        {"tip": "cizgi", "katman": "RAY", "x1": 0.0},
                        {"tip": "cizgi", "katman": "RAY", "x1": 5.0},
                    ],
                }
            },
        }
        y = json.loads(json.dumps(e))
        y["cizimler"]["kuyu_plani"]["elemanlar"][1]["x1"] = 6.0
        f = farklar(e, y)
        self.assertEqual(len(f), 1)
        self.assertIn("kuyu_plani:  1. eleman ( cizgi · RAY", f[0])
        self.assertIn("['x1']", f[0])
        self.assertIn('{"x1": 5.0}  →  {"x1": 6.0}', f[0])

    def test_hukum_degisimi(self):
        f = farklar({"hata": ["X yok"]}, {"sira": [], "cizimler": {}})
        self.assertEqual(f, ["hüküm değişti — önce reddediliyor:  X yok, şimdi çiziliyor"])

    def test_yalniz_svg(self):
        e = {
            "sira": ["giris"],
            "cizimler": {"giris": {"baslik": "B", "olcek": 20, "svg": "1", "elemanlar": []}},
        }
        y = json.loads(json.dumps(e))
        y["cizimler"]["giris"]["svg"] = "2"
        self.assertEqual(farklar(e, y), ["giris:  elemanlar aynı, SVG çıktısı değişti ( cizim/svg.py )"])


if __name__ == "__main__":
    unittest.main()
