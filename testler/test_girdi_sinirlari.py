"""Kuyu dışına taşan donanım ve örnek üreticinin sağ yerleşimi."""
import copy
import unittest
from unittest.mock import patch

import calistir
from cizim import girdi as CG, geometri as CGE, sabitler as CS
from testler.test_cizim import _ornek, _sag_ayna, _arka


class GirdiSinirlari(unittest.TestCase):
    def test_aski_kacikligi_gecersizse_reddedilir(self):
        for duzen in CG.ASKI_DUZENLERI:
            alan = 'nokta_kaciklik' if duzen == 'Doğrudan' else 'kasnak_kaciklik'
            for deger in ('abc', None, True, float('nan'), float('inf'), -float('inf'), -2000, 2000):
                g = copy.deepcopy(CG.ORNEK)
                g['aski'].update(duzen=duzen, nokta_arasi=450)
                g['aski'][alan] = deger
                with self.subTest(duzen=duzen, deger=deger):
                    self.assertTrue(any('aski' in h or 'Askı' in h for h in CG.dogrula(g)))

    def test_aski_derinlik_siniri(self):
        for duzen in CG.ASKI_DUZENLERI:
            g = copy.deepcopy(CG.ORNEK)
            g['aski'].update(duzen=duzen, nokta_arasi=450)
            S = CS.sabitler()
            alan = 'nokta_kaciklik' if duzen == 'Doğrudan' else 'kasnak_kaciklik'
            yari = 45 if duzen == 'Doğrudan' else S['kabin_kasnak_genislik'] / 2
            merkez = g['kabin']['on_pay'] + (g['kabin']['derinlik'] + S['kabin_pano_arka']) / 2
            for y, uygun in ((yari, True), (yari - 1, False),
                             (g['kuyu']['derinlik'] - yari, True),
                             (g['kuyu']['derinlik'] - yari + 1, False)):
                g['aski'][alan] = y - merkez
                with self.subTest(duzen=duzen, y=y):
                    self.assertEqual(CG.dogrula(g) == [], uygun)

    def test_agirlik_ray_ve_konsol_siniri(self):
        S = CS.sabitler()
        for factory in (_ornek, _sag_ayna, _arka):
            g = factory()
            ag = g['agirlik']
            if ag['yeri'] == 'Arka':
                bosluk = g['kuyu']['genislik'] / 2
            else:
                merkez = g['kabin_ray']['kapi_arasi'] + ag['eksen_kaciklik']
                bosluk = min(merkez, g['kuyu']['derinlik'] - merkez)
            sinir = 2 * (bosluk - ag['h'] - S['konsol_agirlik_boy'] / 2)
            for aralik, uygun in ((sinir, True), (sinir + 2, False), (2200, False)):
                ag['ray_arasi'] = aralik
                with self.subTest(yer=ag['yeri'], aralik=aralik):
                    self.assertEqual(CG.dogrula(g) == [], uygun)
                    if uygun:
                        for e in CGE.plan(g):
                            if e['tip'] == 'dikdortgen' and e['katman'] in ('RAY', 'KONSOL'):
                                self.assertGreaterEqual(e['x'], 0)
                                self.assertGreaterEqual(e['y'], 0)
                                self.assertLessEqual(e['x'] + e['g'], g['kuyu']['genislik'])
                                self.assertLessEqual(e['y'] + e['d'], g['kuyu']['derinlik'])

    def test_sag_secimi_gecerli_plan_uretir(self):
        with patch.object(calistir, 'uret', return_value=0) as uret:
            self.assertEqual(calistir.main(['--agirlik', 'Sağ']), 0)
        g = uret.call_args.args[0]
        self.assertEqual(CG.dogrula(g), [])
        self.assertEqual(CGE.plan(g), CGE.plan(_sag_ayna()))

    def test_sonlu_olmayan_olculer_reddedilir(self):
        for deger in (float('nan'), float('inf'), -float('inf')):
            self.assertTrue(CG.dogrula(_ornek(kuyu={'genislik': deger})))


if __name__ == '__main__':
    unittest.main()
