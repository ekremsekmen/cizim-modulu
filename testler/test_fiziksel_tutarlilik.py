"""Plan ve kesitte aynı parçaların konumu ve fiziksel bağlantıları."""
import unittest

from cizim import girdi as G, geometri as E, kuyu_dibi as D
from cizim import kuyu_kesiti as K, kabin_ustu as U, kesit_parcalari as P
from testler.test_cizim import _ornek, _sag_ayna


class FizikselTutarlilik(unittest.TestCase):
    def test_sase_plan_yan_kesit_ayni_derinlik(self):
        for factory in (_ornek, _sag_ayna):
            g = factory()
            if g['agirlik']['yeri'] == 'Sağ':
                g['kuyu_dibi']['regulator_yan'] = 'Sol'
            g['_cizim_sabitleri'] = {'sase_dikme_derinlik': 360}
            plan = [e for e in E.plan(g) if e.get('ad') == 'sase_dikme']
            yan = [e for e in K.yan_kesit(g) if e.get('ad') == 'sase']
            self.assertEqual(len(plan), 2)
            self.assertEqual(min(e['x'] for e in yan), plan[0]['y'])
            self.assertEqual(max(e['x'] + e['g'] for e in yan), plan[0]['y'] + plan[0]['d'])
            self.assertEqual(plan[0]['d'], 360)

    def test_gergi_kolu_her_yonde_ray_kasnak_agirligi_baglar(self):
        for kaciklik in (260, -600):
            g = _ornek(kuyu_dibi={'regulator_kaciklik': kaciklik})
            Y = D.yerlesim(g)
            self.assertEqual(Y['hata'], [])
            gp = Y['gergi_donanim']
            kol, ag = gp['kol'], gp['agirlik']
            gy = (Y['gergi'][1] + Y['gergi'][3]) / 2
            for y in (g['kabin_ray']['kapi_arasi'], gy, (ag[1] + ag[3]) / 2):
                self.assertLessEqual(kol[1], y)
                self.assertGreaterEqual(kol[3], y)

    def test_eski_gergi_yeri_rayla_cakistigi_icin_reddedilir(self):
        hata = D.dogrula(_ornek(kuyu_dibi={'regulator_kaciklik': 280}))
        self.assertTrue(any('gergisi agirlik' in h and 'çakışıyor' in h for h in hata), hata)

    def test_gergi_plan_kesit_ayni_kutular_ve_siginma_bos(self):
        for factory in (_ornek, _sag_ayna):
            g = factory()
            if g['agirlik']['yeri'] == 'Sağ':
                g['kuyu_dibi']['regulator_yan'] = 'Sol'
            Y = K.yerlesim(g)
            self.assertEqual(Y['hata'], [])
            gp = Y['KD']['gergi_donanim']
            e = D.ciz(g)
            for ad, kutu in gp.items():
                el = next(el for el in e if el.get('ad') == 'gergi_' + ad)
                self.assertEqual(P.kutu_(el), kutu)
                self.assertEqual(Y['M']['gergi'][ad][:2], (kutu[1], kutu[3]))
                self.assertFalse(D._ortusur(kutu, Y['KD']['siginma']))
            for kutu in gp.values():
                self.assertTrue(0 <= kutu[0] <= kutu[2] <= g['kuyu']['genislik'])
                self.assertTrue(0 <= kutu[1] <= kutu[3] <= g['kuyu']['derinlik'])

    def test_gergi_donanimi_merdiven_ve_siginmaya_engel(self):
        """Gergi kolu ve ağırlığı kuyu dibinde yer tutar:  merdiven ve sığınma
        onlara basmaz.  Gergi sağ rayda, kaçıklık −900 iken engel sayılmasa
        merdiven sağ yanda kolun ve ağırlığın üstüne düşüyordu."""
        for kac in (-900, -700, 260):
            for tip in ('Yatarak', 'Çömelme', 'Dik duruş'):
                g = _ornek(kuyu_dibi={'regulator_yan': 'Sağ', 'regulator_kaciklik': kac, 'siginma_tipi': tip})
                Y = D.yerlesim(g)
                with self.subTest(kaciklik=kac, siginma=tip):
                    self.assertEqual(Y['hata'], [])
                    for kutu in Y['gergi_donanim'].values():
                        for alan in (Y['merdiven'], Y['siginma']):
                            self.assertFalse(alan and D._ortusur(kutu, alan), (kutu, alan))

    def test_kasnak_tasiyicisi_kasnagi_saseye_baglar(self):
        """Kabin altı kasnaklar şaseye bağlıdır:  planda yol kasnağın
        merkezinden şase dikmesine ( ray eksenine ) gider;  iki kesitte de
        aynı yol kasnak merkezinin kotunda çizilir."""
        g = _ornek()
        plan = E.plan(g)
        yol = [e for e in plan if e.get('ad') == 'kasnak_tasiyici_sematik']
        kasnaklar = [e for e in plan if e.get('ad') == 'kabin_kasnak']
        dikmeler = [e for e in plan if e.get('ad') == 'sase_dikme']
        self.assertEqual((len(kasnaklar), len(dikmeler)), (2, 2))
        uclar = [(e['x1'], e['y1']) for e in yol] + [(e['x2'], e['y2']) for e in yol]

        def icinde(p, el):
            return el['x'] - 1e-6 <= p[0] <= el['x'] + el['g'] + 1e-6 and el['y'] - 1e-6 <= p[1] <= el['y'] + el['d'] + 1e-6
        for k in kasnaklar:
            self.assertIn((k['x'] + k['g'] / 2.0, k['y'] + k['d'] / 2.0), uclar)
        for d in dikmeler:
            self.assertTrue(any(icinde(p, d) for p in uclar), d)
        from cizim import donanim as CDN
        Y = K.yerlesim(g)
        #  A-A'da kabin en alt, B-B'de en üst durakta
        for ciz, z in ((K.yan_kesit, Y['kotlar'][0]), (K.on_kesit, Y['kotlar'][-1])):
            yol = [x for x in ciz(g) if x.get('ad') == 'kasnak_tasiyici_sematik']
            zk = CDN.kabin_kotlari(g['dusey'], Y['S'], z)['kasnak_merkez']
            with self.subTest(kesit=ciz.__name__):
                self.assertTrue(yol)
                self.assertEqual({x[k] for x in yol for k in ('y1', 'y2')}, {zk})

    def test_kabin_halat_baglantisi_raya_baglanir(self):
        """Kuyu tepesinde kabin halat bağlantısının plakası kabin rayının başına
        bağlıdır:  kuyu üstü planında ve B-B'de yol plakanın ortasından ray
        eksenine gider ( eskiden plaka ile ray arasında 105,5 mm boşluk vardı,
        plaka havada duruyordu ).  Makine dairesinde bağlantı döşemededir, yol yok."""
        from cizim import kuyu_ustu as CKT
        g = _ornek()
        Y = CKT.yerlesim(g)
        kb = Y['kabin_baglanti']
        rx, ry = Y['halat_konsolu'][-1]['p1'][:2]
        #  Bağlantıya en yakın kabin rayı ( öbür yandaki ray kuyunun karşı ucundadır )
        r = min((e for e in E.plan(g) if e.get('ad') == 'kabin_ray'),
                key=lambda e: abs(e['x'] + e['g'] / 2 - (kb[0] + kb[2]) / 2))
        self.assertTrue(r['x'] <= rx <= r['x'] + r['g'] and r['y'] <= ry <= r['y'] + r['d'], (rx, ry, r))
        self.assertEqual(Y['halat_konsolu'][0]['p0'][:2], ((kb[0] + kb[2]) / 2, (kb[1] + kb[3]) / 2))
        plan = CKT.ciz(g)
        self.assertEqual(len([e for e in plan if e.get('ad') == 'halat_konsolu_sematik']), len(Y['halat_konsolu']))
        M = K.yerlesim(g)['M']
        zb = (M['kabin_baglanti'][4] + M['kabin_baglanti'][5]) / 2
        yol = [e for e in K.on_kesit(g) if e.get('ad') == 'halat_konsolu_sematik']
        self.assertTrue(yol)
        self.assertEqual({e[k] for e in yol for k in ('y1', 'y2')}, {zb})
        md = _ornek(makine={'yeri': 'Makine dairesi'})
        self.assertFalse([e for e in K.on_kesit(md) + CKT.ciz(md) if e.get('ad') == 'halat_konsolu_sematik'])

    def test_korkuluk_yuksekligi_ve_kotu_iki_kesitte(self):
        g = _ornek()
        Y = K.yerlesim(g)
        h = max(h for _, h in U.korkuluklar(Y['KU']))
        for ciz, z in ((K.yan_kesit, 0), (K.on_kesit, Y['kotlar'][-1])):
            es = [e for e in ciz(g) if e.get('ad') == 'korkuluk']
            self.assertTrue(es)
            zs = [e[k] for e in es for k in ('y1', 'y2')]
            tavan = z + g['dusey']['kabin_ic_yukseklik'] + Y['S']['kabin_tavan_kalinlik']
            self.assertEqual(min(zs), tavan)
            self.assertEqual(max(zs), tavan + h)

    def test_kirik_kesit_korkulugu_kesmez(self):
        g = _ornek()
        tam = [e for e in K.yan_kesit(g) if e.get('ad') == 'korkuluk']
        kirik = [e for e in K.yan_kesit(g, azami=10000) if e.get('ad') == 'korkuluk']
        def parcalar(es):
            return sorted(tuple(sorted(((e["x1"], e["y1"]), (e["x2"], e["y2"])))) for e in es)
        self.assertEqual(parcalar(kirik), parcalar(tam))


if __name__ == '__main__':
    unittest.main()
