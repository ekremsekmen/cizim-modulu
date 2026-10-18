"""ÖN YÜZ DENETİMİ — SUNUCUYLA UYUM

Ön yüz ( on-yuz/src/lib/proje.ts alanHatasi ) kutuyu yazılırken denetler, kural
dışı değeri sunucuya göndermez.  Kurallar sunucudan gelir
( mukavemet_girdi.form_kurallari ).  Uyum:

  -  ÖN YÜZ SUNUCUDAN SIKI OLAMAZ:  ön yüzün reddettiği her değeri sunucu da
     reddeder — yoksa geçerli bir girdi ekranda engellenirdi.  Her sayı alanı
     hesaba girdiği yerleşimde ( gizli alan denetlenmez ) sınırın hemen
     dışındaki değerlerle denenir.
  -  İMKÂNSIZ DEĞER ÖN YÜZDE DURUR:  10¹² her alanda, −1 işaretli olmayan
     alanda sunucuya gitmeden reddedilir;  sınırın kendisi geçer.
  -  OKUNAMAYAN YAZIMIN KARARI SUNUCUNUNDUR:  "12abc", belirsiz "1.200", "1e3"
     ön yüzde reddedilmez, sebebiyle sunucu reddeder.

Ön yüzün kendi kodu koşar:  Node TypeScript'i doğrudan çalıştırır ( 22+ ).
"""

import json
import os
import shutil
import subprocess
import unittest

from testler import test_yerlesim_saglamligi
from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJE_TS = os.path.join(KOK, "on-yuz", "src", "lib", "proje.ts")
NODE_MODULES = os.path.join(KOK, "on-yuz", "node_modules")

#  Durumlar stdin'den:  [ [ anahtar , kural , ham ] ] → [ ileti | null ]
_NODE = r"""
const { pathToFileURL } = require('url');
const { alanHatasi } = await import(pathToFileURL(process.argv[1]).href);
const durumlar = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(durumlar.map(([a, k, h]) => alanHatasi({ kurallar: { [a]: k } }, a, h))));
"""


def on_yuz(durumlar):
    r = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            "--input-type=commonjs",
            "-e",
            f"(async () => {{ {_NODE} }})()",
            PROJE_TS,
        ],
        input=json.dumps(durumlar),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(r.stdout)


def _tr(x):
    return f"{x:g}".replace(".", ",")


def _dis_degerler(k):
    """Kuralın hemen dışındaki ( ön yüzün reddedebileceği ) değerler."""
    d = ["12abc", "1.200"]
    if k["en_cok"] is not None:
        d.append(_tr(k["en_cok"] + 1))
    if k["en_az"] is not None:
        d.append(
            _tr(k["en_az"]) if not k["en_az_dahil"] else _tr(k["en_az"] - (1 if k["en_az"] == 0 else 0.01))
        )
    if k["tam_sayi"]:
        d.append("2,5")
    return d


@unittest.skipUnless(
    shutil.which("node") and os.path.isdir(NODE_MODULES), "node ya da ön yüz bağımlılıkları yok ( npm ci )"
)
class OnYuzDenetimi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = uygulama_istegi.alanlar()
        cls.kurallar = cls.v["kurallar"]
        cls.alanlar = {
            f["anahtar"]: f for gr in cls.v["gruplar"] for f in gr["alanlar"] if f["tur"] == "sayi"
        }
        cls.pg = set(cls.v["proje_geneli"])
        gizli = cls.v["yerlesime_gore_gizli"]
        cls.mrl_gizli, cls.daireli_gizli = set(gizli["mrl"]), set(gizli["daireli"])

    def _istek(self, anahtar, ham):
        #  Alan hesaba girdiği yerleşimde denenir:  MRL'de gizliyse makine daireli
        v = test_yerlesim_saglamligi.standart_istek(1000, anahtar not in self.mrl_gizli, "Sağ")
        (v["proje_geneli"] if anahtar in self.pg else v["asansorler"][0])[anahtar] = ham
        return v

    def test_her_sayi_alaninin_kurali_var(self):
        self.assertEqual(sorted(set(self.alanlar) - set(self.kurallar)), [])

    def test_on_yuz_sunucudan_siki_degil(self):
        durumlar = [
            (a, ham)
            for a, k in self.kurallar.items()
            if a in self.alanlar and not (a in self.mrl_gizli and a in self.daireli_gizli)
            for ham in _dis_degerler(k)
        ]
        iletiler = on_yuz([[a, self.kurallar[a], ham] for a, ham in durumlar])
        self.assertTrue(any(iletiler), "ön yüz hiçbir değeri reddetmedi — test bir şey denemiyor")
        siki = []
        for (a, ham), ileti in zip(durumlar, iletiler):
            if not ileti:
                continue  # ön yüz geçirdi:  karar sunucunun
            #  Form her değişiklikte iki uca da gider:  çizim alanını hesap
            #  okumaz, çizim ucu reddeder
            v = self._istek(a, ham)
            if json.loads(uygulama_uclari.api_uygulama_coklu(v).body).get("aktif") is False:
                continue
            if json.loads(cizim_uclari.api_cizimler(v).body).get("aktif") is False:
                continue
            siki.append(f"{a} = {ham!r}:  ön yüz '{ileti}' diyor, sunucu kabul ediyor")
        self.assertEqual(siki, [], "\n".join(siki))

    def test_imkansiz_deger_on_yuzde_durur_sinir_gecer(self):
        durumlar, beklenen = [], []
        for a, k in self.kurallar.items():
            durumlar += [[a, k, "1000000000000"], [a, k, _tr(k["en_cok"])]]
            beklenen += [(a, "1e12", True), (a, "tavan", False)]
            if k["en_az"] is not None and k["en_az"] == 0 and k["en_az_dahil"]:
                durumlar.append([a, k, "-1"])
                beklenen.append((a, "-1", True))
            if k["en_az"] is None:
                #  alt sınırı olmayan alan ( kaçıklık ):  eksi değer geçer
                durumlar.append([a, k, "-150"])
                beklenen.append((a, "-150", False))
        iletiler = on_yuz(durumlar)
        yanlis = [
            f"{a} {ne}:  {ileti!r}" for (a, ne, red), ileti in zip(beklenen, iletiler) if bool(ileti) != red
        ]
        self.assertEqual(yanlis, [], "\n".join(yanlis))

    def test_okunamayan_yazimin_karari_sunucunun(self):
        k = {"en_az": 0, "en_az_dahil": True, "en_cok": 20000, "tam_sayi": False}
        hamlar = ["12abc", "1.200", "1,200", "inf", "nan", "1.234,5", "1e3", " 7 ", "0,001"]
        iletiler = on_yuz([["x", k, h] for h in hamlar])
        self.assertEqual(iletiler, [None] * len(hamlar), list(zip(hamlar, iletiler)))


if __name__ == "__main__":
    unittest.main()
