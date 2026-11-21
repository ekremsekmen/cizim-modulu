"""UZUN İŞİN AŞAMALARI VE AKIŞLI UÇLAR ( 20 Kas — yayın öncesi arayüz taslağı B1 · B2 · B5 · B10 ).

Ölçüm:  uygulama paketi 1 asansörde 2,7, 4 asansörde 10,4 sn;  avan paketi aranmamış asansörü
paketin içinde arar ( 6,8 sn — 17 Kas'ta 48 sn );  düzeltme önerisi 1,5 – 3,7 sn.  Ekranda yalnız
dönen işaret vardı;  "Seçimleri de bul" 42 kutuyu 2,3 – 3,2 sn dener, ekranda "birkaç saniye".  Artık bu uçlar avan aramasının sözleşmesiyle ( uc_ortak.akisli_yanit ) işin
GERÇEK aşamalarını akıtır;  istemeyen istemci eskisi gibi tek yanıt alır.  Aşama bildirimi işin
sonucunu etkilemez;  bırakılan istek bir sonraki aşamada durur ( asamalar.Birakildi ).
"""

import asyncio
import base64
import copy
import io
import json
import os
import re
import unittest
import zipfile
import zlib

from fastapi.responses import JSONResponse

from cizim import asamalar
from testler.test_olcu_kaynagi import _veri
from uclar import avan_cizimi, avan_secici, avan_uclari, care_uclari, cizim_uclari, parca_uclari, uc_ortak
from uclar import uygulama_uclari

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(KOK, "on-yuz", "src", "lib", "taslaklar.json"), encoding="utf-8") as _d:
    TASLAKLAR = {t["kimlik"]: t for t in json.load(_d)}

METIN = {
    "a": ("A yapılıyor", "A yapıldı"),
    "b": ("B yapılıyor", "B yapıldı"),
    "c": ("C yapılıyor", "C yapıldı"),
}


def uygulama_istegi(kimlik="1275-md", adet=1, **degisen):
    """Taslaktan ön yüzün gönderdiği istek ( lib/proje.istekKur ) — çok asansör "Asansör ekle" gibi."""
    t = TASLAKLAR[kimlik]
    a = {**t["asansor"], **degisen}
    return {
        "asansorler": [copy.deepcopy(a) for _ in range(adet)],
        "proje_geneli": dict(t["proje_geneli"]),
        "sabitler": {},
        "kapak": {"project_title": "Akış deneme", "owner": "", "sheet_no": ""},
    }


def akisli_istek(yol, govde, akis=True, kodlama="gzip"):
    """Bütün uygulama üzerinden ( main.app — sıkıştırma ara katmanı dahil ) POST:  ( başlıklar ,
    gövde baytları ).  akis:  Accept'te uc_ortak.AKIS_TURU."""
    import main

    v = json.dumps(govde).encode()
    basliklar = [(b"content-type", b"application/json"), (b"accept-encoding", kodlama.encode())]
    if akis:
        basliklar.append((b"accept", uc_ortak.AKIS_TURU.encode()))
    kapsam = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": yol,
        "raw_path": yol.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": basliklar + [(b"content-length", str(len(v)).encode())],
        "client": ("test", 1),
        "server": ("test", 80),
    }
    gelen, parcalar = {}, []

    async def calistir():
        bitti = asyncio.Event()
        okundu = False

        async def al():
            nonlocal okundu
            if not okundu:
                okundu = True
                return {"type": "http.request", "body": v, "more_body": False}
            await bitti.wait()
            return {"type": "http.disconnect"}

        async def gonder(m):
            if m["type"] == "http.response.start":
                gelen.update({k.decode(): x.decode() for k, x in m["headers"]})
            elif m["type"] == "http.response.body":
                if m.get("body"):
                    parcalar.append(m["body"])
                if not m.get("more_body"):
                    bitti.set()

        await main.app(kapsam, al, gonder)

    asyncio.run(calistir())
    return gelen, b"".join(parcalar)


def satirlar(basliklar, govde):
    """Akışın satırları ( gzip çözülmüş )."""
    if basliklar.get("content-encoding") == "gzip":
        govde = zlib.decompressobj(31).decompress(govde)
    return [json.loads(s) for s in govde.decode("utf-8").splitlines() if s.strip()]


def kodlar(durum):
    return [a["kod"] for a in durum["asamalar"]]


class Asamalar(unittest.TestCase):
    """cizim/asamalar:  bağlamsız hiçbir şey yapmaz, aynı aşama tek satır, alt iş görünmez, iptal."""

    def test_baglam_yokken_hicbir_sey_olmaz(self):
        asamalar.asama("a")
        asamalar.say()
        asamalar.ayrinti("x")
        asamalar.planla(["a"])
        with asamalar.alt_is("a"), asamalar.onekle("A · "):
            asamalar.asama("b")

    def test_asamalar_onek_ve_ayrinti(self):
        i = asamalar.Ilerleme(METIN, plan=["a", "b"])
        with asamalar.bagla(i):
            asamalar.asama("a", "1")
            asamalar.asama("a", "2")
            with asamalar.onekle("B · "):
                asamalar.asama("a")
            asamalar.asama("b")
            asamalar.ayrinti("Asansör 1 / 2", kod="b")
            asamalar.ayrinti("başka aşamanınki", kod="a")
            asamalar.say()
            asamalar.say()
        d = i.durum()[1]
        self.assertEqual(kodlar(d), ["a", "a", "b"])
        self.assertEqual(
            [a["surer"] for a in d["asamalar"]], ["A yapılıyor", "B · A yapılıyor", "B yapılıyor"]
        )
        self.assertEqual([a["ayrinti"] for a in d["asamalar"]], ["2", "", "Asansör 1 / 2"])
        self.assertEqual(d["sinama"], 2)
        self.assertEqual([p["kod"] for p in d["plan"]], ["a", "b"])
        self.assertNotIn("onek", d["asamalar"][0])

    def test_alt_isin_asamalari_listeye_girmez(self):
        i = asamalar.Ilerleme(METIN)
        with asamalar.bagla(i):
            with asamalar.alt_is("a"):
                asamalar.asama("b")
                asamalar.say()
            asamalar.asama("c")
        d = i.durum()[1]
        self.assertEqual(kodlar(d), ["a", "c"])
        self.assertEqual(d["sinama"], 1)

    def test_birakilan_iste_asama_ve_sinama_durdurur(self):
        birakildi = [False]
        i = asamalar.Ilerleme(METIN, iptal=lambda: birakildi[0])
        with asamalar.bagla(i):
            asamalar.asama("a")
            birakildi[0] = True
            with self.assertRaises(asamalar.Birakildi):
                asamalar.asama("b")
            with self.assertRaises(asamalar.Birakildi):
                asamalar.say()
        #  Genel except ( uçların son savunması ) iptali hata sanıp yutmaz
        self.assertFalse(issubclass(asamalar.Birakildi, Exception))

    def test_ic_ice_isin_bildirimi_susturulur(self):
        """Avan seçicisi uyarlamada düzeltme aramasını ( care_uclari.coz ) çağırır:  onun aşamaları
        seçicinin sözlüğünde yok ( KeyError ), sınamaları "yerleşim sınandı" sayısına girmemeli."""
        i = asamalar.Ilerleme(METIN)
        with asamalar.bagla(i):
            asamalar.asama("a")
            with asamalar.sessiz():
                asamalar.asama("sozlukte-yok")
                asamalar.say()
            asamalar.asama("b")
        d = i.durum()[1]
        self.assertEqual(kodlar(d), ["a", "b"])
        self.assertEqual(d["sinama"], 0)

    def test_surum_yalniz_degisince_artar(self):
        i = asamalar.Ilerleme(METIN)
        s0 = i.durum()[0]
        self.assertEqual(i.durum()[0], s0)
        with asamalar.bagla(i):
            asamalar.asama("a")
        self.assertGreater(i.durum()[0], s0)


class AkisSonucu(unittest.TestCase):
    def test_dosya_ve_json(self):
        y = uc_ortak._indir(b"PK\x03\x04", "Ölçüm - Uygulama Projesi.zip", "application/zip")
        y.headers["X-Avan-Not"] = "DXF,TASMA"
        s = uc_ortak.akis_sonucu(y)
        self.assertEqual(s["dosya"]["ad"], "Ölçüm - Uygulama Projesi.zip")
        self.assertEqual(s["dosya"]["tur"], "application/zip")
        self.assertEqual(base64.b64decode(s["dosya"]["veri"]), b"PK\x03\x04")
        self.assertEqual(s["notlar"], ["DXF", "TASMA"])
        hata = JSONResponse({"aktif": False, "hata": ["x"]})
        self.assertEqual(uc_ortak.akis_sonucu(hata), {"aktif": False, "hata": ["x"]})


class UygulamaPaketi(unittest.TestCase):
    """B1:  /api/indir/uygulama-dwg — akışta paketin adımları, sonda dosya;  akışsız eskisi gibi."""

    def test_asamalar_sirayla_ve_asansor_sayaci(self):
        veri = {**uygulama_istegi(adet=2), "kapak_sayfasi": {}, "kagit": 600}
        i = asamalar.Ilerleme(uygulama_uclari.PAKET_ASAMALARI)
        with asamalar.bagla(i):
            y = uygulama_uclari.indir_uygulama_dwg(veri)
        self.assertEqual(y.media_type, "application/zip", y.body[:300])
        d = i.durum()[1]
        beklenen = [
            k for k in ("hesap", "sayfalar", "cizimler", "dwg", "pdf") if k in [p["kod"] for p in d["plan"]]
        ]
        self.assertEqual(kodlar(d), beklenen)
        self.assertEqual(d["asamalar"][0]["ayrinti"], "2 asansör")
        self.assertEqual(next(a for a in d["asamalar"] if a["kod"] == "cizimler")["ayrinti"], "Asansör 2 / 2")

    def test_akisli_yanitin_dosyasi_akissizinkiyle_ayni(self):
        veri = {**uygulama_istegi(), "kapak_sayfasi": {}, "kagit": 600}
        b, govde = akisli_istek("/api/indir/uygulama-dwg", veri, akis=False, kodlama="identity")
        self.assertEqual(b["content-type"], "application/zip")
        tek = zipfile.ZipFile(io.BytesIO(govde))
        b, govde = akisli_istek("/api/indir/uygulama-dwg", veri)
        self.assertEqual(b["content-type"], uc_ortak.AKIS_TURU)
        s = satirlar(b, govde)
        self.assertIn("sonuc", s[-1])
        for x in s[:-1]:
            self.assertTrue(set(kodlar(x["ilerleme"])) <= set(uygulama_uclari.PAKET_ASAMALARI))
        dosya = s[-1]["sonuc"]["dosya"]
        self.assertTrue(dosya["ad"].endswith("Uygulama Projesi.zip"), dosya["ad"])
        akisli = zipfile.ZipFile(io.BytesIO(base64.b64decode(dosya["veri"])))
        self.assertEqual(sorted(akisli.namelist()), sorted(tek.namelist()))

    def test_reddedilen_istek_akista_json(self):
        veri = {**uygulama_istegi(), "kagit": 75}
        b, govde = akisli_istek("/api/indir/uygulama-dwg", veri)
        self.assertIn("KÂĞIT ENİ", satirlar(b, govde)[-1]["sonuc"]["hata"])

    def test_birakilan_paket_kurulmaz(self):
        veri = {**uygulama_istegi(), "kapak_sayfasi": {}}
        i = asamalar.Ilerleme(uygulama_uclari.PAKET_ASAMALARI, iptal=lambda: True)
        with asamalar.bagla(i), self.assertRaises(asamalar.Birakildi):
            uygulama_uclari.indir_uygulama_dwg(veri)


class AvanPaketi(unittest.TestCase):
    """B2:  /api/indir/proje-dwg — her asansörün araması adıyla, önbellektekinin "çizimi hazır"."""

    T630 = avan_secici.paketler()[(630, True)]["asansor"]

    def veri(self):
        k = {"kapasite": "8", "V": "1", **{a: self.T630[a] for a in avan_cizimi.KART if a in self.T630}}
        k.update({"tanim": "A", "Hk": "20,8", "kabin_boyu": "1400", "kabin_genisligi": "1100", "eta": "0,85"})
        ortak = {"mk_yok": True, "temel_a": "20", "temel_b": "15"}
        return {
            "kapak": {"project_title": "Avan akış"},
            "girdiler": {"avan": {"ortak": ortak, "asansorler": [k], "sabitler": {}}},
        }

    def test_arama_adiyla_sonra_onbellekten(self):
        avan_secici._ONBELLEK.clear()
        for aranir in (True, False):
            with self.subTest(aranir=aranir):
                i = asamalar.Ilerleme(avan_uclari.PAKET_ASAMALARI)
                with asamalar.bagla(i):
                    y = avan_uclari.indir_proje_dwg(self.veri())
                self.assertEqual(y.media_type, "application/zip", y.body[:300])
                d = i.durum()[1]
                k = kodlar(d)
                self.assertEqual(k[0], "hesaplar")
                self.assertEqual(k[-1], "pdf")
                self.assertIn("cizimler", [p["kod"] for p in d["plan"]])
                asansorun = [a for a in d["asamalar"] if a["surer"].startswith("A · ")]
                if aranir:
                    self.assertEqual(asansorun[0]["kod"], "paket")
                    self.assertTrue({a["kod"] for a in asansorun} <= set(avan_secici.ASAMALAR))
                else:
                    self.assertEqual([a["kod"] for a in asansorun], ["hazir"])

    def test_akista_dosya_iner(self):
        b, govde = akisli_istek("/api/indir/proje-dwg", self.veri())
        s = satirlar(b, govde)
        z = zipfile.ZipFile(io.BytesIO(base64.b64decode(s[-1]["sonuc"]["dosya"]["veri"])))
        self.assertTrue(any(n.endswith(".dxf") for n in z.namelist()))


class Duzeltme(unittest.TestCase):
    """B5:  /api/uygulama/care — aramanın aşamaları ve sınama sayısı;  sonuç akışsızla aynı."""

    def veri(self):
        v = uygulama_istegi(kuyu_genisligi="2100")
        temiz = uygulama_istegi()
        return {
            **v,
            "asansor": 0,
            "onceki": {"asansor": temiz["asansorler"][0], "proje_geneli": temiz["proje_geneli"]},
        }

    def test_asamalar_ve_sinama(self):
        v = self.veri()
        i = asamalar.Ilerleme(care_uclari.ASAMALAR)
        with asamalar.bagla(i):
            r = care_uclari.coz(v, 0, v["onceki"])
        d = i.durum()[1]
        self.assertEqual(kodlar(d), ["okuma", "sinir", "turev", "secim"])
        self.assertEqual(d["asamalar"][1]["ayrinti"], "Kuyu genişliği")
        self.assertEqual(d["sinama"], r["sinama"])
        self.assertTrue(r["careler"] and r["careler"][0]["oneriler"])

    def test_akisli_sonuc_akissizla_ayni(self):
        v = self.veri()
        b, govde = akisli_istek("/api/uygulama/care", v, akis=False, kodlama="identity")
        tek = json.loads(govde)
        b, govde = akisli_istek("/api/uygulama/care", v)
        s = satirlar(b, govde)
        akisli = s[-1]["sonuc"]
        for r in (akisli, tek):
            r.pop("sure")
        self.assertEqual(akisli, tek)
        sayilar = [x["ilerleme"]["sinama"] for x in s[:-1]]
        self.assertEqual(sayilar, sorted(sayilar))
        self.assertTrue(all(n <= tek["sinama"] for n in sayilar))


class SecimAramasi(unittest.TestCase):
    """B10:  "Seçimleri de bul" ( /api/uygulama/parca, secimler ) — denenen kutunun adı ve sırası;
    bırakılan arama önbelleğe yarım sonuç yazmaz;  akışın sonucu akışsızla aynı."""

    AYRINTI = r"^[^(]+ · (\d+) / (\d+)$"

    def cozumleme(self, **ek):
        """Önbelleksiz çözümleme ( arama baştan ) ve kuyu planındaki ilk kabin rayının kimliği."""
        v = _veri(**ek)
        ham, i, proje = cizim_uclari.istek(v)
        r = parca_uclari._cozumle(ham, i, proje, "kuyu_plani")
        return v, r, f"kabin_ray-{[a for a, _k in r['ornekler']].index('kabin_ray')}"

    def test_kutu_kutu_ve_sirasi(self):
        _v, r, _pid = self.cozumleme()
        i = asamalar.Ilerleme(parca_uclari.ASAMALAR)
        with asamalar.bagla(i):
            bagli = parca_uclari._secim_kaynaklari(r)
        d = i.durum()[1]
        self.assertEqual(kodlar(d), ["secim"])
        m = re.match(self.AYRINTI, d["asamalar"][0]["ayrinti"])
        self.assertTrue(m, d)
        #  Son bildirim son kutu:  "… · 42 / 42"
        self.assertEqual(m.group(1), m.group(2))
        self.assertGreater(int(m.group(2)), 10)
        self.assertTrue(bagli)

    def test_birakilan_arama_onbellege_yazmaz(self):
        _v, r, _pid = self.cozumleme()
        with asamalar.bagla(asamalar.Ilerleme(parca_uclari.ASAMALAR, iptal=lambda: True)):
            with self.assertRaises(asamalar.Birakildi):
                parca_uclari._secim_kaynaklari(r)
        self.assertIsNone(r["secim"])
        self.assertTrue(parca_uclari._secim_kaynaklari(r))

    def test_akisli_sonuc_akissizla_ayni(self):
        v, _r, pid = self.cozumleme(kuyu_genisligi=2160)
        govde = {**v, "cizim": "kuyu_plani", "parca": pid, "secimler": True}
        b, g = akisli_istek("/api/uygulama/parca", govde)
        self.assertEqual(b["content-type"], uc_ortak.AKIS_TURU)
        s = satirlar(b, g)
        self.assertGreater(len(s), 1, s)
        _b, tek = akisli_istek("/api/uygulama/parca", govde, akis=False, kodlama="identity")
        self.assertEqual(s[-1]["sonuc"], json.loads(tek))
        self.assertIn("kabin_ray_profili", [x["anahtar"] for x in s[-1]["sonuc"]["girdiler"]])
        #  İlk satırlar aşamasız olabilir:  satır 0,2 sn'de gider, çizimin çözümlemesi o anda sürebilir
        #  ( 21 Kas — CI'ın yavaş makinesinde ilk satırın aşama listesi boştu;  ekran onu "Seçimler
        #  deneniyor" diye gösterir ).  Arama saniyeler sürer:  aşamalı satır mutlaka gelir.
        asamali = [x["ilerleme"]["asamalar"] for x in s[:-1] if x["ilerleme"]["asamalar"]]
        self.assertTrue(asamali, s[:-1])
        for a in asamali:
            self.assertEqual([x["kod"] for x in a], ["secim"])
            self.assertRegex(a[0]["ayrinti"], self.AYRINTI)
        #  Seçimsiz istek akış istese de tek JSON ( anında — aranacak bir şey yok )
        b, g = akisli_istek("/api/uygulama/parca", {**govde, "secimler": False}, kodlama="identity")
        self.assertTrue(b["content-type"].startswith("application/json"))
        self.assertTrue(json.loads(g)["aktif"])


if __name__ == "__main__":
    unittest.main()
