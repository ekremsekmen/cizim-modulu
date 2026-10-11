"""ÖLÇÜNÜN KAYNAĞI TÜREVLE — denetçi ( cizim/izli.py, olcu_kaynagi.turevden ).

Ekranda tıklanan ölçünün kaynakları çizim BİR KEZ, girdileri izli sayıya
sarılarak kurulup bulunur.  Eski yöntem ( her girdi ±1 mm oynatılıp çizim
yeniden kurulur — olcu_kaynagi.cozumle ) burada denetçidir:

  · izli kurulumun çizimi düz kurulumunkiyle birebir aynıdır ( akış, yazı,
    sayı — int ile float aynı sayılır );
  · oynatmanın DOĞRUSAL bulduğu her kaynak türevde aynı eğimle vardır;
  · türev, oynatmanın hiç görmediği bir kaynak söylemez.  Ölçü kırık bir
    noktadaysa ( iki parça çakışır, bir yöne oynatınca değişir öbürüne
    değişmez — oynatma "doğrusal değil" der ) türev tek yanlıdır:  orada
    yalnız doğrusal kaynaklar aranır.
  · Zincirde iki parçanın noktası çakışıyorsa ( delik planında iki delik
    aynı eksende ) kümede biri kalır;  türev onun yanından, oynatma öbür
    yanından bakabilir — ikisi de tek yanlı doğrudur.  Ayrılan kaynak
    oynatılınca zincirin YAPISI değişiyorsa ( nokta ayrılır, yeni ölçü
    çıkar ) çakışmadır, fark sayılmaz;  yapı değişmiyorsa hatadır.
    Değiştirme her durumda çizim yeniden kurularak doğrulanır.
Kategori seçimleri ( ray profili, askı düzeni … ) türevle bulunmaz;
karşılaştırılmaz."""

import json
import unittest

from cizim import cizimler
from cizim import izli
from cizim import olcu_kaynagi
from cizim import sabitler
from testler.test_olcu_kaynagi import DUZENLER
from testler.yavas import yavas
from uclar import cizim_uclari

UZUNLUK = ("mm", "m", "cm")


def _duz(x):
    """int → float ( 50 ile 50.0 aynı çizgi ), izli sayı → float."""
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, dict):
        return {k: _duz(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_duz(v) for v in x]
    return x


def _hazirla(v, ad):
    ham, i, proje = cizim_uclari._istek(v)
    kur, bilgi = cizim_uclari._kurucu(ham, ad, proje, i + 1)
    with sabitler.okunanlar() as okunan:
        taban = kur({})
    if taban is None:
        return None
    adaylar = cizim_uclari._adaylar(ham, bilgi["A"], bilgi["g"], okunan)
    return ham, i, proje, kur, bilgi, taban, adaylar


def izli_cizim(ham, ad, proje, sira, g_taban, adaylar):
    """Bütün çizim ( yalnız ölçüler değil ), izli girdiyle."""
    with izli.izleme():
        g = cizim_uclari.izli_cizim_girdisi(ham, proje, sira, g_taban, adaylar)
        return cizimler.CIZIMLER[ad][1](g)


def farklar(fd_kaynak, tr_kaynak, taban):
    """[ ( sıra, ölçü, eksik, fazla, eğim farkı ) ] — üstteki kurallara göre;
    kaynaklar kimlikleriyle ( ( "girdi" | "ofis", ad ) )."""
    alan = cizim_uclari._sozlesme()[0]

    def gecerli(k):
        return k["tur"] in ("sayi", "ofis") or (
            k["tur"] == "secim" and k["egim"] is not None and alan[k["kimlik"][1]]["birim"] in UZUNLUK
        )

    out = []
    for j, (o, fd_k, tr_k) in enumerate(zip(taban, fd_kaynak, tr_kaynak)):
        fd = {k["kimlik"]: k["egim"] for k in fd_k if gecerli(k) and k["dogrusal"]}
        tr = {k["kimlik"]: k["egim"] for k in tr_k if gecerli(k)}
        kirik = any(gecerli(k) and not k["dogrusal"] for k in fd_k)
        eksik = sorted(k for k in fd if k not in tr)
        fazla = [] if kirik else sorted(k for k in tr if k not in {x["kimlik"] for x in fd_k})
        egim = sorted(
            (k, fd[k], tr[k]) for k in fd if k in tr and abs(fd[k] - tr[k]) > 1e-6 * max(1.0, abs(fd[k]))
        )
        if eksik or fazla or egim:
            out.append((j, o["metin"], eksik, fazla, egim))
    return out


def cakismalar_disinda(fark, kur, taban, adaylar):
    """Farklardan çakışma olanlar çıkar:  ayrılan her kaynak 1 mm oynatılınca
    ( bir yöne ya da öbürüne ) ölçü zincirinin yapısı değişiyorsa
    ( olcu_kaynagi.eslestir — aynı sıra, aynı sözlü ölçüler değil )."""
    aday = {a["kimlik"]: a for a in adaylar}

    def yapi_degisir(k):
        #  Çakışma bir yönde ayrılır, öbür yönde ayrılmaz:  iki yön denenir
        a = aday[k]
        for y in (1.0, -1.0):
            e = kur({k: a["deger"] + y * a.get("adim", 1.0)})
            if e is not None and olcu_kaynagi.eslestir(taban, e) != list(range(len(taban))):
                return True
        return False

    return [f for f in fark if not all(yapi_degisir(k) for k in [*f[2], *f[3], *(x[0] for x in f[4])])]


class TurevOynatmaylaAyni(unittest.TestCase):
    @yavas("6 dk")
    def test_butun_duzenler(self):
        sayi = 0
        for ad_d, v in DUZENLER.items():
            v = v()
            for ad in cizimler.CIZIMLER:
                h = _hazirla(v, ad)
                if h is None:
                    continue
                ham, i, proje, kur, bilgi, taban, adaylar = h
                with self.subTest(duzen=ad_d, cizim=ad):
                    duz = _duz(cizimler.CIZIMLER[ad][1](bilgi["g"]))
                    iz = _duz(izli_cizim(ham, ad, proje, i + 1, bilgi["g"], adaylar))
                    self.assertEqual(json.dumps(iz, sort_keys=True), json.dumps(duz, sort_keys=True))
                    e = cizim_uclari._izli_olculer(ham, ad, proje, i + 1, bilgi["g"], adaylar)
                    self.assertEqual([o["metin"] for o in e], [o["metin"] for o in taban])
                    _t, fd = olcu_kaynagi.cozumle(kur, adaylar)
                    fark = farklar(fd, olcu_kaynagi.turevden(e, adaylar), taban)
                    self.assertEqual(cakismalar_disinda(fark, kur, taban, adaylar), [])
                    sayi += len(taban)
        self.assertGreater(sayi, 1000)


class Kurallar(unittest.TestCase):
    """Denetçinin kendisi:  yanlışı geçirmez."""

    def _k(self, kimlik, egim, dogrusal=True, tur="sayi"):
        return {"kimlik": ("girdi", kimlik), "tur": tur, "egim": egim, "dogrusal": dogrusal, "bagli": False}

    def test_eksik_fazla_egim_yakalanir(self):
        taban = [{"metin": "100"}]
        fd = [[self._k("kuyu_genisligi", 1.0)]]
        kg, kb = ("girdi", "kuyu_genisligi"), ("girdi", "kabin_genisligi")
        self.assertEqual(farklar(fd, [[]], taban), [(0, "100", [kg], [], [])])
        self.assertEqual(
            farklar(fd, [[self._k("kuyu_genisligi", 1.0), self._k("kabin_genisligi", 0.5)]], taban),
            [(0, "100", [], [kb], [])],
        )
        self.assertEqual(
            farklar(fd, [[self._k("kuyu_genisligi", 0.5)]], taban), [(0, "100", [], [], [(kg, 1.0, 0.5)])]
        )

    def test_cakisma_yalniz_yapi_degisince(self):
        taban = [{"metin": "240", "yon": "yatay"}, {"metin": "100", "yon": "yatay"}]
        fark = [(0, "240", [], [("girdi", "a")], [])]
        aday = [{"kimlik": ("girdi", "a"), "deger": 1.0, "adim": 1.0}]
        self.assertEqual(cakismalar_disinda(fark, lambda d: taban, taban, aday), fark)  # yapı aynı:  hata
        yeni = [{"metin": "1", "yon": "yatay"}, *taban]
        self.assertEqual(cakismalar_disinda(fark, lambda d: yeni, taban, aday), [])  # nokta ayrıldı

    def test_kirik_noktada_yalniz_dogrusallar(self):
        taban = [{"metin": "100"}]
        fd = [[self._k("kuyu_genisligi", 1.0), self._k("kabin_genisligi", 0.5, dogrusal=False)]]
        tr = [[self._k("kuyu_genisligi", 1.0), self._k("esik_arasi", 1.0)]]
        self.assertEqual(farklar(fd, tr, taban), [])


if __name__ == "__main__":
    unittest.main()
