"""ÖN YÜZ DENETİMİ — SUNUCUYLA UYUM ( 17 Eki )

Arayüz kutuyu yazılırken denetler ( hesap/static/uygulama.js mKuralHatasi ),
kural dışı değeri sunucuya göndermez.  Kurallar sunucudan gelir
( mukavemet_girdi.form_kurallari ).  İki yönlü uyum:

  -  ÖN YÜZ SUNUCUDAN SIKI OLAMAZ:  ön yüzün reddettiği her değeri sunucu da
     reddeder — yoksa geçerli bir girdi ekranda engellenirdi.  Her sayı alanı
     hesaba girdiği yerleşimde ( gizli alan denetlenmez ) sınırın hemen
     dışındaki değerlerle denenir.
  -  İMKÂNSIZ DEĞER ÖN YÜZDE DURUR:  10¹² her alanda, −1 işaretli olmayan
     alanda sunucuya gitmeden reddedilir;  sınırın kendisi geçer."""

import json
import os
import shutil
import subprocess
import unittest

from testler import test_yerlesim_saglamligi
from uclar import cizim_uclari, uygulama_istegi, uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#  uygulama.js'i küçük bir bağlamla yükler ( olcu_arayuz.test.cjs gibi ),
#  durumları stdin'den alır:  [ [ kural , ham , birim ] ] → [ ileti ]
_NODE = r"""
const fs = require('fs'), vm = require('vm'), path = require('path');
const ctx = vm.createContext({ISTEK: {mukavemet: 0}, MUK: {asansor_azami: 4},
  localStorage: {getItem: () => null}, addEventListener() {}, kur() {},
  Event: class {}, kacis: x => String(x), trn: x => String(x)});
vm.runInContext(fs.readFileSync(path.join(process.argv[1], 'hesap/static/uygulama.js'), 'utf8'), ctx);
const f = vm.runInContext('mKuralHatasi', ctx);
const durumlar = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(durumlar.map(([k, h, b]) => f(k, h, b))));
"""


def on_yuz(durumlar):
    r = subprocess.run(
        ["node", "-e", _NODE, KOK], input=json.dumps(durumlar), capture_output=True, text=True, check=True
    )
    return json.loads(r.stdout)


def _tr(x):
    return f"{x:g}".replace(".", ",")


def _dis_degerler(k):
    """Kuralın hemen dışındaki ( ön yüzün reddettiği ) değerler."""
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


@unittest.skipUnless(shutil.which("node"), "node yok")
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
        iletiler = on_yuz([[self.kurallar[a], ham, self.alanlar[a]["birim"]] for a, ham in durumlar])
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
            b = self.alanlar.get(a, {}).get("birim", "")
            durumlar += [[k, "1000000000000", b], [k, _tr(k["en_cok"]), b]]
            beklenen += [(a, "1e12", True), (a, "tavan", False)]
            if k["en_az"] is not None and k["en_az"] == 0 and k["en_az_dahil"]:
                durumlar.append([k, "-1", b])
                beklenen.append((a, "-1", True))
        iletiler = on_yuz(durumlar)
        yanlis = [
            f"{a} {ne}:  {ileti!r}" for (a, ne, red), ileti in zip(beklenen, iletiler) if bool(ileti) != red
        ]
        self.assertEqual(yanlis, [], "\n".join(yanlis))

    def test_okuma_sunucuyla_ayni(self):
        """Gevşek okuma ( "12abc" → 12 ) ve belirsiz yazım ( "1.200" ) sunucuda
        reddedilir;  ön yüz de reddeder.  Türkçe ve İngilizce ondalık geçer."""
        k = {"en_az": None, "en_az_dahil": True, "en_cok": None, "tam_sayi": False}
        hamlar = ["12abc", "1.200", "1,200", "inf", "nan", "1.234,5", "1,234.5", "0,001", "-3", " 7 ", "1e3"]
        iletiler = on_yuz([[k, h, "mm"] for h in hamlar])
        self.assertEqual([bool(x) for x in iletiler], [True] * 5 + [False] * 6, list(zip(hamlar, iletiler)))


if __name__ == "__main__":
    unittest.main()
