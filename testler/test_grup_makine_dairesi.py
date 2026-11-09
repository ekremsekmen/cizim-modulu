"""TEK KUYUDA MAKİNE DAİRESİ ( cizim/grup.makine_dairesi — 2 Kas;  plan
cikti/devir/ORTAK_KUYU_PLANI.md § 9 ).

·  oda iki asansörün:  yeri kuyunun sol iç köşesine göre ( boşsa bütün kuyuya
   ortalı );  köprü sağdaki asansörde soldaki bölme + kiriş kadar kaydırır —
   iki asansörün odası aynı yerde
·  her asansörün panosu ve çalışma alanı odanın kendi yarısında ( sınır kirişin
   ortası );  pano duvarı yan duvarsa her asansör kendi dış yan duvarını
   kullanır;  pano asansörün adıyla
·  makine dairesi ve delik planı tek düzlemde:  oda, kapı, oda ölçüleri bir kez,
   tabliye kirişin üstünden kesintisiz, zincir 250 · SW · kiriş · SW · 250;
   makine daireli projede kuyu üstü planı yok
"""

import unittest

from cizim import cizimler, geometri, grup
from tasarim.alanlar import ALAN
from testler.test_grup import cakisan_yazilar, girdiler, ikili
from testler.test_yerlesim_saglamligi import standart_istek


def md_ikili(Q1=1000, Q2=800, soldaki=1, **pg):
    """İki asansörlü, makine daireli tek kuyu ( arkadaki ağırlık, kabin üstü askı );
    oda iki kuyuyu örter."""
    v = ikili(Q1=Q1, Q2=Q2, soldaki=soldaki)
    ortak = {
        k: v["asansorler"][0][k] for k in ("kuyu_derinligi", "kuyu_duvar_kalinligi", "son_kat_yuksekligi")
    }
    a = [standart_istek(Q, False, "Arka", aski_duzeni="Kabin üstü")["asansorler"][0] for Q in (Q1, Q2)]
    a[0].update(ortak)
    v["asansorler"] = a
    W = a[0]["kuyu_genisligi"] + a[1]["kuyu_genisligi"] + 140 + 500
    v["proje_geneli"].update(mk_yok=False, mk_genislik=W, mk_uzunluk=4950, **pg)
    return v


def kuyudakiler(v):
    c = girdiler(v)
    assert not any(h for _g, h in c), [h for _g, h in c]
    return grup.gruptakiler([g for g, _h in c])


class Oda(unittest.TestCase):
    def test_iki_asansorun_odasi_ayni_yerde(self):
        for soldaki in (1, 2):
            A, B = kuyudakiler(md_ikili(soldaki=soldaki))
            X1 = grup._x0lar([A, B])[1]
            a, b = A["makine_dairesi"], B["makine_dairesi"]
            self.assertAlmostEqual(a["x"], b["x"] + X1)
            self.assertEqual((a["y"], a["genislik"], a["derinlik"]), (b["y"], b["genislik"], b["derinlik"]))
            #  Boşsa bütün kuyuya ortalı ( dış duvarlar dahil )
            dis = A["kuyu"]["duvar_sol"] + X1 + B["kuyu"]["genislik"] + B["kuyu"]["duvar_sag"]
            self.assertAlmostEqual(a["x"], -A["kuyu"]["duvar_sol"] - (a["genislik"] - dis) / 2.0)

    def test_panolar_kendi_yarisinda_kendi_adiyla(self):
        for duvar, beklenen in (("Sağ", ("Sol", "Sağ")), ("Arka", ("Arka", "Arka"))):
            A, B = kuyudakiler(md_ikili(md_pano_duvar=duvar))
            self.assertEqual((A["makine_dairesi"]["pano_duvar"], B["makine_dairesi"]["pano_duvar"]), beklenen)
            X1 = grup._x0lar([A, B])[1]
            orta = A["kuyu"]["genislik"] + A["kuyu"]["duvar_sag"] / 2.0
            e = grup.makine_dairesi([A, B])
            pano = sorted(
                geometri.sinir([x]) for x in e if x.get("ad") in ("kumanda_panosu", "calisma_alani")
            )
            self.assertEqual(len(pano), 4)
            self.assertEqual(sum(k[2] <= orta + 1e-6 for k in pano), 2, duvar)
            self.assertEqual(sum(k[0] >= orta - 1e-6 for k in pano), 2, duvar)
            #  Pano adı panonun içinde;  tek satıra sığmazsa iki satır ( makine_dairesi._pano_adi —
            #  7 Kas çizim denetimi ):  satırlar okuma sırasıyla birleşir
            adlar = []
            for k in (geometri.sinir([x]) for x in e if x.get("ad") == "kumanda_panosu"):
                satirlar = [
                    x
                    for x in e
                    if x.get("ad") == "pano_adi" and k[0] < x["x"] < k[2] and k[1] < x["y"] < k[3]
                ]
                satirlar.sort(key=lambda x: x["x"] if x.get("aci") else -x["y"])
                adlar.append(" ".join(x["metin"] for x in satirlar))
            self.assertEqual(sorted(adlar), ["ASANSÖR 1 PANOSU", "ASANSÖR 2 PANOSU"])
            self.assertTrue(X1 > orta)


class BosBolme(unittest.TestCase):
    def test_bos_kuyu_genisligi_varsayilanla_ayni_odayi_kurar(self):
        """Programın kuralı:  boş kutu = varsayılanı yazılmış kutu.  9 Kas:  bölme genişliği
        boşken kapı onu yazmıyordu;  oda bütün kuyuya ortalanmıyor, sağdaki asansör odayı
        kaymış görüyordu ( x:  −1.820 yerine −495 )."""
        varsayilan = ALAN["kuyu_genisligi"].varsayilan
        yazili, bos = md_ikili(Q1=800, Q2=800), md_ikili(Q1=800, Q2=800)
        for v, deger in ((yazili, varsayilan), (bos, None)):
            for a in v["asansorler"]:
                a.pop("kuyu_genisligi", None)
                if deger is not None:
                    a["kuyu_genisligi"] = deger
        for (g1, h1), (g2, h2) in zip(girdiler(yazili), girdiler(bos)):
            self.assertEqual(h1, h2)
            self.assertEqual(g1["makine_dairesi"], g2["makine_dairesi"])


class Cizimler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gler = kuyudakiler(md_ikili())

    def test_makine_daireli_projenin_ortak_cizimleri(self):
        self.assertEqual(
            grup.cizimleri(self.gler),
            ["kuyu_plani", "kabin_ustu", "kuyu_dibi", "makine_dairesi", "delik_plani", "kuyu_kesiti_on"],
        )
        for ad in grup.cizimleri(self.gler):
            self.assertEqual(grup.kurulamayanlar(self.gler, ad), [], ad)

    def test_oda_bir_kez_tabliye_kesintisiz_zincir(self):
        A, B = self.gler
        X1, GA = grup._x0lar(self.gler)[1], A["kuyu"]["genislik"]
        e = grup.makine_dairesi(self.gler)
        self.assertEqual(cakisan_yazilar(e), 0)
        tek = cizimler.CIZIMLER["makine_dairesi"][1](A)
        for ad in ("oda_kapisi", "olcu_oda_genisligi", "olcu_oda_derinligi", "tabliye_yazi"):
            self.assertEqual(sum(x.get("ad") == ad for x in e), sum(x.get("ad") == ad for x in tek), ad)
        self.assertEqual(sum(x["katman"] == "KUYU-DUVAR" and x["tip"] == "dikdortgen" for x in e), 5)
        self.assertFalse(
            [
                x
                for x in e
                if x.get("ad") == "tabliye_kenari" and all(GA - 1 < x[k] < X1 + 1 for k in ("x1", "x2"))
            ]
        )
        zincir = next(x["kot"] for x in e if x.get("ad") == "olcu_kuyu_genisligi")
        sira = sorted(
            (x["a"][0], x["metin"])
            for x in e
            if x["tip"] == "olcu" and x["yon"] == "yatay" and x["kot"] == zincir
        )
        self.assertEqual(
            [m for _a, m in sira], ["250", f"SW{GA:g}", "140", f"SW{B['kuyu']['genislik']:g}", "250"]
        )

    def test_delik_plani_yazilar_cakismaz(self):
        _b, e = grup.cerceveli(self.gler, (), "delik_plani")
        self.assertEqual(cakisan_yazilar(e), 0)
        self.assertEqual(sum(x.get("ad") == "ayirma_kirisi" for x in e), 1)


if __name__ == "__main__":
    unittest.main()
