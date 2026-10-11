"""İZLİ SAYI — otomatik türevin kuralları ( cizim/izli.py ).

Değer düz float işlemiyle birebir aynı kalmalı ( çizim değişmez );  türev
zincir kuralıyla taşınmalı;  izleme kapalıyken hiçbir şey sarılmamalı."""

import copy
import json
import math
import pickle
import random
import threading
import unittest

from cizim import izli
from cizim.izli import Izli

A, B = ("girdi", "a"), ("girdi", "b")


def _x(v=3.0):
    return Izli(v, {A: 1.0})


def _y(v=5.0):
    return Izli(v, {B: 1.0})


class Turev(unittest.TestCase):
    def assertTurev(self, x, beklenen):
        t = izli.turev(x)
        self.assertEqual(set(t), set(beklenen), t)
        for k, v in beklenen.items():
            self.assertAlmostEqual(t[k], v, places=12, msg=k)

    def test_toplama_cikarma(self):
        x, y = _x(), _y()
        self.assertTurev(x + y, {A: 1, B: 1})
        self.assertTurev(x - y, {A: 1, B: -1})
        self.assertTurev(10 - x, {A: -1})
        self.assertTurev(x + 2, {A: 1})
        self.assertTurev(2 + x, {A: 1})
        self.assertTurev(sum([x, y, 4]), {A: 1, B: 1})
        #  Birbirini götüren terim tutulmaz:  ( x + y ) − x yalnız y'ye bağlı
        self.assertTurev((x + y) - x, {B: 1})

    def test_carpma_bolme(self):
        x, y = _x(3.0), _y(5.0)
        self.assertTurev(x * y, {A: 5, B: 3})
        self.assertTurev(0.5 * x, {A: 0.5})
        self.assertTurev(x / 2, {A: 0.5})
        self.assertTurev(x / y, {A: 1 / 5, B: -3 / 25})
        self.assertTurev(6 / x, {A: -6 / 9})

    def test_us_isaret_mutlak(self):
        x = _x(3.0)
        self.assertTurev(x**2, {A: 6})
        self.assertTurev(-x, {A: -1})
        self.assertTurev(abs(-x), {A: 1})
        self.assertTurev(abs(x - 10), {A: -1})
        self.assertIs(+x, x)

    def test_mod_ve_yuvarlama(self):
        x = _x(37.0)
        self.assertTurev(x % 25, {A: 1})
        self.assertTurev(x - x % 25, {})  # 25'lik adım:  eğim 0
        self.assertTurev(round(x / 3, 2), {A: 1 / 3})
        self.assertIsInstance(round(x), int)  # int:  iz düşer
        self.assertNotIsInstance(x // 2, Izli)

    def test_en_buyuk_secilenin_turevi(self):
        x, y = _x(3.0), _y(5.0)
        self.assertTurev(max(x, y), {B: 1})
        self.assertTurev(min(x, y), {A: 1})

    def test_math_izi_dusurur(self):
        self.assertNotIsInstance(math.sqrt(_x(4.0)), Izli)


class Deger(unittest.TestCase):
    """Değer düz float işlemiyle BİREBİR aynı ( işlem sırası dahil )."""

    def test_rastgele_islemler_birebir(self):
        rnd = random.Random(7)
        islemler = (
            lambda a, b: a + b,
            lambda a, b: a - b,
            lambda a, b: a * b,
            lambda a, b: a / b if b else a,
            lambda a, b: b - a,
            lambda a, b: 0.5 * a + b / 3.0,
            lambda a, b: abs(a - b),
            lambda a, b: max(a, b) - min(a, b),
            lambda a, b: round(a / 7.0, 3),
            lambda a, b: a % 25.0,
        )
        for _ in range(2000):
            a, b = rnd.uniform(-3000, 3000), rnd.uniform(-3000, 3000)
            ia, ib = Izli(a, {A: 1.0}), Izli(b, {B: 1.0})
            for f in islemler:
                duz, iz = f(a, b), f(ia, ib)
                self.assertEqual(float(iz), duz)
                self.assertEqual(repr(float(iz)), repr(duz))

    def test_float_gibi_davranir(self):
        x = Izli(2100.0, {A: 1.0})
        self.assertIsInstance(x, float)
        self.assertEqual(json.dumps({"v": x}), json.dumps({"v": 2100.0}))
        self.assertEqual(f"{x:g}", "2100")
        self.assertEqual(str(x), "2100.0")
        self.assertEqual({2100.0: 1}[x], 1)
        self.assertEqual(hash(x), hash(2100.0))
        self.assertTrue(x == 2100 and x < 2101 and x)
        self.assertFalse(Izli(0.0, {A: 1.0}))

    def test_kopyalanir(self):
        x = Izli(12.5, {A: 2.0})
        for k in (copy.copy(x), copy.deepcopy(x), pickle.loads(pickle.dumps(x))):
            self.assertEqual((float(k), izli.turev(k)), (12.5, {A: 2.0}))


class Izleme(unittest.TestCase):
    def test_kapaliyken_hicbir_sey_sarilmaz(self):
        self.assertFalse(izli.izlemede())
        self.assertIs(izli.girdi(5, A), 5)
        self.assertEqual(izli.oz(7.0, A), 7.0)
        self.assertNotIsInstance(izli.oz(7.0, A), Izli)

    def test_acikken_girdi_ve_oz(self):
        with izli.izleme():
            x = izli.girdi(1200, A)
            self.assertEqual(izli.turev(x), {A: 1.0})
            #  Kuralla dolan alan:  kuralın girdisine eğimi korunur, kendisine 1 eklenir
            dbgw = izli.oz(x + 60, B)
            self.assertEqual(izli.turev(dbgw), {A: 1.0, B: 1.0})
            self.assertIs(izli.girdi(True, A), True)
            self.assertIsNone(izli.oz(None, A))
            self.assertEqual(izli.oz("Sağ", A), "Sağ")
        self.assertFalse(izli.izlemede())

    def test_ic_ice_ve_hatada_kapanir(self):
        with izli.izleme():
            with izli.izleme():
                pass
            self.assertTrue(izli.izlemede())
        with self.assertRaises(ValueError), izli.izleme():
            raise ValueError
        self.assertFalse(izli.izlemede())

    def test_is_parcacigina_ozel(self):
        gorulen = []
        with izli.izleme():
            t = threading.Thread(target=lambda: gorulen.append(izli.izlemede()))
            t.start()
            t.join()
        self.assertEqual(gorulen, [False])

    def test_sayi_izi_korur(self):
        x = Izli(3.0, {A: 1.0})
        self.assertIs(izli.sayi(x), x)
        self.assertEqual(izli.sayi(3), 3.0)
        self.assertIs(type(izli.sayi(3)), float)
        self.assertEqual(izli.sayi("2.5"), 2.5)


if __name__ == "__main__":
    unittest.main()
