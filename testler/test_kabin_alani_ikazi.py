"""KABİN ALANI UYARISI TEK KEZ ( 22 Kas ).

Uygulama projesinde kabin alanı bulgusu iki kez çıkıyordu:  mukavemetin
"Kullanılabilir kabin alanı" bölümü ( TS EN 81-20 m.5.4.2 — kapı girintisiyle )
UYGUN DEĞİL diyordu, altında avan motorunun kaba ikazı ( yalnız W × D ) sarı
uyarı kartı olarak aynı şeyi büyük harfle yineliyordu.  Uygulamada hüküm
bölümündür;  avan projesinde ikaz yerinde kalır ( orada bu bölüm yoktur ).
"""

import json
import unittest

from dogrulama.altin_uret import uygulama_senaryolar
from motor.avan import avan_hesabi
from motor.uygulama import uygulama_girdisi, uygulama_hesabi

BUYUK_KABIN = {"beyan_yuku": 800, "kabin_genisligi": 1500, "kabin_derinligi": 1350}


def _kabin_alani_bolumu(a):
    b = [x for x in a.get("bolumler") or [] if x.get("kimlik") == "kabin_alani"]
    assert len(b) == 1, [x.get("baslik") for x in a.get("bolumler") or []]
    return b[0]


def _avan_ikazi_var(girdi):
    av = avan_hesabi.hesapla(uygulama_girdisi.avan_girdisi(json.loads(json.dumps(girdi))))
    u = (av.get("asansorler") or [{}])[0].get("uyarilar") or []
    return any(avan_hesabi.KABIN_ALANI_IKAZI in x for x in u)


class KabinAlaniIkazi(unittest.TestCase):
    def test_buyuk_kabinde_bulgu_bolumde_ikaz_yok(self):
        s = uygulama_hesabi.hesapla_coklu([dict(BUYUK_KABIN)], {})
        a = s["asansorler"][0]
        self.assertTrue(a["aktif"])
        self.assertIs(_kabin_alani_bolumu(a)["sonuc"]["uygun"], False)
        self.assertFalse([u for u in a["uyarilar"] if avan_hesabi.KABIN_ALANI_IKAZI in u])
        self.assertFalse([u for u in s.get("uyarilar") or [] if avan_hesabi.KABIN_ALANI_IKAZI in u])
        #  Avan motoru aynı girdide ikazı hâlâ verir ( avan projesi için )
        self.assertTrue(_avan_ikazi_var(a["girdi"]))

    def test_ikaz_dusunce_bilgi_kaybolmaz(self):
        """Avanın ikaz verdiği her senaryoda uygulamanın bölümü de UYGUN DEĞİL:
        düşen yalnız tekrardır."""
        denenen = 0
        for g in [*uygulama_senaryolar(), {"asansorler": [dict(BUYUK_KABIN)], "ortak": {}}]:
            s = uygulama_hesabi.hesapla_coklu(g.get("asansorler"), g.get("ortak"))
            for a in s.get("asansorler") or []:
                if not a.get("aktif") or not _avan_ikazi_var(a["girdi"]):
                    continue
                denenen += 1
                with self.subTest(girdi={k: a["girdi"].get(k) for k in BUYUK_KABIN}):
                    self.assertIs(_kabin_alani_bolumu(a)["sonuc"]["uygun"], False)
        self.assertGreater(denenen, 0)


if __name__ == "__main__":
    unittest.main()
