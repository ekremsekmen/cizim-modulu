"""AVAN ÇİZİMLERİNİN UCU ( /api/avan/cizimler — uclar/avan_cizim_uclari;  12 Kas ).
Gövde avan hesabınınki ( /api/avan );  asansörün mimarisi kartta.  Yanıt seçicinin
sonucu;  "uygun"da uygulamanın çizim yanıtı.  Çizim bulunamadıysa çizim YOKTUR."""

import io
import json
import re
import unittest
import zipfile

import ezdxf

from cizim import avan_kipi, katlar, pafta
from motor.uygulama import uygulama_hesabi
from uclar import avan_cizim_uclari, avan_cizimi, avan_secici, avan_uclari, cizim_uclari, uygulama_istegi

T630 = avan_secici.paketler()[(630, True)]["asansor"]
T800MD = avan_secici.paketler()[(800, False)]


def govde(kart, ortak=None, asansor=0):
    return {
        "girdiler": {"ortak": {"mk_yok": True, **(ortak or {})}, "asansorler": [kart], "sabitler": {}},
        "asansor": asansor,
    }


def kart(t, **degisen):
    """Avan kartı:  kapasite kişi ( Tablo-7 ), ölçüler ekranda yazıldığı gibi metin."""
    kisi = {"630": "8", "800": "10"}[t["beyan_yuku"]]
    k = {"kapasite": kisi, "V": "1", **{a: t[a] for a in avan_cizimi.KART if a in t}}
    k.update(degisen)
    return k


def yanit(g):
    return json.loads(avan_cizim_uclari.api_avan_cizimler(g).body)


def yazilar(c):
    """Çizim yanıtının bütün SVG'lerindeki yazılar."""
    return {
        re.sub(r"<[^>]+>", "", t).strip()
        for x in c["cizimler"]
        for t in re.findall(r"<text[^>]*>(.*?)</text>", x["svg"], flags=re.S)
    }


class AvanCizimUcu(unittest.TestCase):
    def test_uygun_kuyuda_cizimler(self):
        r = yanit(govde(kart(T630)))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["paket"], "630")
        self.assertTrue(r["cizim"]["aktif"], r["cizim"].get("hata"))
        self.assertGreaterEqual(len(r["cizim"]["cizimler"]), 5)
        self.assertTrue(all("<svg" in c["svg"] for c in r["cizim"]["cizimler"]))
        #  Ürün bölümlerinin turuncu işareti avana gitmez
        self.assertEqual(r["cizim"]["hesap_parcalari"], {})
        #  Mimarın verdikleri isteğe aynen geçti;  kabin Tablo-7 yükünün paketi
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["beyan_yuku"], a["kuyu_genisligi"], a["kuyu_derinligi"]), ("630", "2050", "1850"))
        self.assertEqual(a["kuyu_tavani_kotu"], T630["kuyu_tavani_kotu"])

    def test_urun_yazilari_avanda_yok(self):
        """Kullanıcı kararı ( 12 Kas ):  paftanın bilgi tablosunda seçicinin iç seçimleri
        ( motor, halat, ray profili ) yazmaz;  tahrikin çizimi ( kasnak düzenlemesi ) yok.
        Aynı istek uygulamadan sorulunca hepsi yerindedir ( avan kipi sızmaz )."""
        r = yanit(govde(kart(T630)))
        avan = yazilar(r["cizim"])
        uygulama = yazilar(json.loads(cizim_uclari.api_cizimler(r["istek"]).body))
        urun = re.compile(
            r"kW|konsol arası|kasnak ø|halat ø|\d × ø|KASNAK DÜZENLEMESİ|70 × 65 × 9|50 × 50 × 5"
        )
        self.assertEqual(sorted(t for t in avan if urun.search(t)), [])
        self.assertGreaterEqual(len({t for t in uygulama if urun.search(t)}), 5)
        self.assertIn(avan_kipi.NOT, avan)
        self.assertNotIn(avan_kipi.NOT, uygulama)
        #  Kalan satırlar aynı:  avan yalnız eksiltir ( + notu ve onun sıra numarası )
        self.assertEqual({t for t in avan - uygulama if "Dişlisiz" not in t}, {avan_kipi.NOT, "3."})
        self.assertFalse(avan_kipi.acik())

    def test_acik_urun_bolumu_isaretlenmez(self):
        """1250 kg ( Q elle ) 1,6 m/s:  tahrik yeteneği geçmiyor ( acik_bolumler );  avanın
        çiziminde hesap notu da turuncu işaret de yok."""
        t = avan_secici.paketler()[(1250, True)]["asansor"]
        n, h = 10, 2900
        k = {a: t[a] for a in avan_cizimi.KART if a in t}
        k.update(
            Q_elle="1250",
            kapasite="16",
            V="1,6",
            durak_kotlari="; ".join(katlar.kot_metni(j * h) for j in range(n)),
            kuyu_dibi_kotu=katlar.kot_metni(-1800),
            kuyu_tavani_kotu=katlar.kot_metni((n - 1) * h + 4600),
        )
        r = yanit(govde(k))
        self.assertEqual((r["durum"], r["acik_bolumler"]), ("uygun", ["tahrik_yetenegi"]), r)
        self.assertEqual(r["cizim"]["hesap_parcalari"], {})
        self.assertEqual([t for t in yazilar(r["cizim"]) if "HESAP" in t or "UYGUN DEĞİL" in t], [])
        #  Uygulamada aynı istek notunu taşır
        u = json.loads(cizim_uclari.api_cizimler(r["istek"]).body)
        self.assertTrue([t for t in yazilar(u) if t.startswith("HESAP:")])

    def test_pafta_avan_kipinde(self):
        """Paftanın girdisi avan kipinde kurulunca:  kasnak düzenlemesi sırada yok, antette
        ray boş, hesap notu yok;  kip kapanınca aynı istek uygulamanın paftasıdır."""
        v = yanit(govde(kart(T630)))["istek"]

        def girdi():
            A, o = uygulama_istegi.asansor_girdileri(json.loads(json.dumps(v)))
            s = uygulama_hesabi.hesapla_coklu(A, o)
            ((g, hata),) = cizim_uclari.girdiler(v, A, o, s, "AVAN")
            self.assertEqual(hata, [])
            return g

        with avan_kipi.etkin():
            g = girdi()
        self.assertTrue(g["proje"]["avan"])
        self.assertNotIn("kasnak_duzeni", pafta.sira(g))
        self.assertEqual(pafta.antet_degerleri(g, [20])["ray"], "")
        self.assertEqual([ad for ad, *_ in pafta.cizim_listesi(g)], list(pafta.sira(g)))
        u = girdi()
        self.assertFalse(u["proje"]["avan"])
        self.assertIn("kasnak_duzeni", pafta.sira(u))
        self.assertTrue(pafta.antet_degerleri(u, [20])["ray"])

    def test_makine_daireli(self):
        a, pg = T800MD["asansor"], T800MD["proje_geneli"]
        ortak = {"mk_yok": False, "mk_uzunluk": pg["mk_uzunluk"], "mk_genislik": pg["mk_genislik"]}
        #  Paketin askısı 1:1;  kart boşken avan hesabı ofis standardını ( 2:1 ) kullanır
        r = yanit(govde(kart(a, i_palanga="1"), ortak))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["paket"], "800-md")
        self.assertEqual(r["istek"]["proje_geneli"]["mk_yok"], "false")
        self.assertTrue(r["cizim"]["aktif"])

    def test_kartin_askisi_cizimde(self):
        """12 Kas:  avan kartının askı oranı ve makine tipi çizimde AYNEN durur ( hesap sayfası
        ile pafta çelişmez ).  1275 kg makine daireli paket 2:1 dişli;  kart 1:1 dişlisiz."""
        t = avan_secici.paketler()[(1275, False)]
        a, pg = t["asansor"], t["proje_geneli"]
        ortak = {"mk_yok": False, "mk_uzunluk": pg["mk_uzunluk"], "mk_genislik": pg["mk_genislik"]}
        k = {"kapasite": "16", "V": a["beyan_hizi"], **{x: a[x] for x in avan_cizimi.KART if x in a}}
        self.assertEqual((a["aski_orani"], a["makine_tipi"]), ("2", "Dişli"))
        r = yanit(govde({**k, "i_palanga": "1", "makine_tipi": "Dişlisiz"}, ortak))
        self.assertEqual(r["durum"], "uygun", r)
        i = r["istek"]["asansorler"][0]
        self.assertEqual((i["aski_orani"], i["makine_tipi"]), ("1", "Dişlisiz"))
        tablo = [y for y in yazilar(r["cizim"]) if "1:1" in y or "Dişlisiz" in y]
        self.assertTrue(any("1:1" in y for y in tablo) and any("Dişlisiz" in y for y in tablo), tablo)

    def test_kartin_askisiyla_kurulamayan(self):
        """Kartın askısıyla asansör kurulamıyorsa çizim ÇIKMAZ ( paketin askısıyla çizip hesap
        sayfasıyla çelişmek yerine );  kartta seçilecek değer döner, uygulanınca çizim çıkar.
        Makine dairesizde 1:1 askı ve dişli makine çizilmez ( programın kuralı )."""
        k = kart(T630, i_palanga="1")
        r = yanit(govde(k))
        self.assertEqual(r["durum"], "beyan", r)
        self.assertNotIn("cizim", r)
        self.assertNotIn("istek", r)
        self.assertEqual(
            [(b["kart"], b["etiket"], b["eski_yazi"], b["yeni_yazi"], b["yeni"]) for b in r["beyan"]],
            [("i_palanga", "Askı oranı", "1:1", "2:1", "2")],
        )
        r = yanit(govde({**k, **{b["kart"]: b["yeni"] for b in r["beyan"]}}))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertEqual(r["istek"]["asansorler"][0]["aski_orani"], "2")
        #  1:1 dişli:  ikisi de değişmeli
        r = yanit(govde(kart(T630, i_palanga="1", makine_tipi="Dişli")))
        self.assertEqual(r["durum"], "beyan", r)
        self.assertEqual(
            {b["kart"]: b["yeni"] for b in r["beyan"]}, {"i_palanga": "2", "makine_tipi": "Dişlisiz"}
        )

    def test_makine_dairelide_iki_bir_aski(self):
        """Makine daireli 800 kg paketi 1:1;  avanın ofis standardı 2:1.  14 Kas'tan beri 2:1 de
        kurulur ( askı kasnakları kabin üstünde ):  kartın askısı çizimde aynen durur."""
        a, pg = T800MD["asansor"], T800MD["proje_geneli"]
        ortak = {"mk_yok": False, "mk_uzunluk": pg["mk_uzunluk"], "mk_genislik": pg["mk_genislik"]}
        r = yanit(govde(kart(a, makine_tipi="Dişlisiz"), ortak))
        self.assertEqual(r["durum"], "uygun", r)
        i = r["istek"]["asansorler"][0]
        self.assertEqual(
            (i["aski_orani"], i["makine_tipi"], i["aski_duzeni"]), ("2", "Dişlisiz", "Kabin üstü")
        )

    def test_kartin_kabini_cizimin_kabini(self):
        """13 Kas:  çizimin kabini hazır asansörünkidir ( kapasitenin kabini — büyümez );  avan
        hesabı kabini karttan okur.  Kartınki farklıysa çizim ÇIKMAZ ( hesap sayfası ile pafta
        ayrı kabin göstermesin ), karta yazılacak ölçü döner;  uygulanınca çizim çıkar.  Kartta
        kabin yoksa ( hesap henüz eksik ) çelişki yoktur."""
        g = govde({**kart(T630), **AvanPaketi.HESAP, "kabin_boyu": "1500"})
        r = yanit(g)
        self.assertEqual((r["durum"], r["beyan_turu"], r["sinama"]), ("beyan", "kabin", 0), r)
        self.assertNotIn("cizim", r)
        self.assertEqual(
            [(b["kart"], b["etiket"], b["eski_yazi"], b["yeni_yazi"], b["yeni"]) for b in r["beyan"]],
            [("kabin_boyu", "Kabin boyu a", "1500 mm", "1400 mm", "1400")],
        )
        duzeltilmis = g["girdiler"]["asansorler"][0] | {b["kart"]: b["yeni"] for b in r["beyan"]}
        r = yanit(govde(duzeltilmis))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kabin_derinligi"], a["kabin_genisligi"]), ("1400", "1100"))
        #  Ekranın kabin kutularına:  avan yanıtında çizimin kabini
        kot = json.loads(avan_uclari.api_avan(g).body)["kotlar"][0]
        self.assertEqual(kot["kabin"], {"kabin_boyu": 1400, "kabin_genisligi": 1100})
        self.assertEqual(yanit(govde(kart(T630)))["durum"], "uygun")
        #  Hazır asansörü olmayan kapasite:  kabin bilinmez, sonuç eskisi gibi
        self.assertEqual(yanit(govde(kart(T630, kapasite="6", kabin_boyu="1500")))["durum"], "paket_yok")

    def test_kapi_trafik_hesabindan(self):
        """Kullanıcı kararı ( 14 Kas ):  çizimin kapısı trafik hesabınınkidir.  Ekran köprüdeki
        kapıyı karta koyar ( kapi_genisligi, kapi_tipi — trafiğin adlarıyla );  aynı ailede
        hazır asansörün tipi kalır ( yönüyle ), başka ailede o ailenin tipi çizilir."""
        r = yanit(govde(kart(T630, kapi_genisligi="800", kapi_tipi="Teleskopik Otomatik")))
        a = r["istek"]["asansorler"][0]
        self.assertEqual(
            (r["durum"], a["kapi_genisligi"], a["kat_kapisi_tipi"]), ("uygun", "800", "Teleskopik Sol")
        )
        r = yanit(govde(kart(T630, kapi_genisligi="900", kapi_tipi="Merkezden Açılan Oto.")))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kapi_genisligi"], a["kat_kapisi_tipi"]), ("900", "Otomatik Merkezi"))
        self.assertTrue(any("Otomatik Merkezi" in y for y in yazilar(r["cizim"])))
        #  Köprü:  trafiğin kapısı ve sütunu asansörlere ( tek tipte bütün sütunlar )
        k = avan_uclari._kopruye_kapi(
            {"tip": "tek", "asansorler": [{"P": 8}, {"P": 8}]},
            {"ozet": {"kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}},
        )
        self.assertEqual(
            k["asansorler"][1],
            {"P": 8, "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik", "sutun": None},
        )
        k = avan_uclari._kopruye_kapi(
            {"tip": "coklu", "asansorler": [{"P": 8}, {"P": 13}]},
            {
                "asansorler": [
                    {"no": 1, "kapi_genisligi": 800, "kapi_tipi": "x"},
                    {"no": 3, "kapi_genisligi": 900, "kapi_tipi": "y"},
                ]
            },
        )
        self.assertEqual([(a["kapi_genisligi"], a["sutun"]) for a in k["asansorler"]], [(800, 0), (900, 2)])

    def test_avanin_motor_gucu_tabloda(self):
        """Bilgi tablosunda motor gücü AVANIN KENDİ hesabınınkidir ( Nsç ), seçicinin motoru
        değil.  Avan hesabı tamamlanmamışsa ( kart eksik ) güç yazmaz."""
        g = govde({**kart(T630), **AvanPaketi.HESAP})
        ozet = json.loads(avan_uclari.api_avan(g).body)["ozet"]["asansorler"][0]
        r = yanit(g)
        self.assertEqual(r["durum"], "uygun", r)
        tahrik = [y for y in yazilar(r["cizim"]) if "kW" in y]
        self.assertEqual(len(tahrik), 1, tahrik)
        nsc = f"{ozet['Nsc']:g}".replace(".", ",")
        self.assertTrue(tahrik[0].endswith(f"  {nsc} kW"), (tahrik, ozet["Nsc"]))
        #  Elle seçilen motor da ( Nsç girişi ):  seçicinin paketinde böyle bir motor yok
        r = yanit(govde({**kart(T630), **AvanPaketi.HESAP, "Nsc": "18,5"}))
        self.assertEqual([y[-7:] for y in yazilar(r["cizim"]) if "kW" in y], ["18,5 kW"])
        self.assertNotEqual(r["istek"]["asansorler"][0]["motor_gucu"], "18.5")
        self.assertEqual([y for y in yazilar(yanit(govde(kart(T630)))["cizim"]) if "kW" in y], [])

    def test_gereken_cizim_dondurmez(self):
        """Geniş kuyuda kuyu üstü yetmez:  çizim de istek de dönmez, mimardan istenen döner."""
        r = yanit(govde(kart(T630, kuyu_genisligi="2350")))
        self.assertEqual(r["durum"], "gereken", r)
        self.assertEqual([g["anahtar"] for g in r["gereken"]], ["kuyu_tavani_kotu"])
        self.assertNotIn("cizim", r)
        self.assertNotIn("istek", r)

    def test_eksik_mimari(self):
        k = kart(T630)
        del k["kuyu_derinligi"], k["kuyu_dibi_kotu"]
        r = yanit(govde(k))
        self.assertEqual((r["durum"], r["eksik"]), ("eksik", ["kuyu_derinligi", "kuyu_dibi_kotu"]))

    def test_okunamayan_ve_olmayan_asansor(self):
        #  Belirsiz yazım ( "1.850" ) avan hesabındaki gibi durdurur
        r = yanit(govde(kart(T630, kuyu_derinligi="1.850")))
        self.assertEqual(r["durum"], "hata", r)
        self.assertIn("Kuyu derinliği", r["hata"])
        #  Kapasitesi yazılmamış kart ve olmayan sıra
        self.assertEqual(yanit(govde(kart(T630, kapasite="")))["durum"], "hata")
        self.assertEqual(yanit(govde(kart(T630), asansor=3))["durum"], "hata")

    def test_paketi_olmayan_kapasite(self):
        self.assertEqual(yanit(govde(kart(T630, kapasite="6")))["durum"], "paket_yok")


class AvanPaketi(unittest.TestCase):
    """ "Projeyi indir" ( /api/indir/proje-dwg ):  mimarisi girilen asansörlerin çizimleri
    avan hesap sayfalarının sağında.  Mimari girilmemişse paket eskisi gibidir;  girilip de
    çizilemeyen asansör pakete çizimsiz girer ve not ( X-Avan-Not:  CIZIM ) söyler."""

    #  Avan hesabının kendi kart alanları ( çizimden bağımsız )
    #  ( η ekrandan hep gelir:  makine tipinin verimi — eksikse asansör hesaplanmaz )
    HESAP = {"Hk": "20,8", "kabin_boyu": "1400", "kabin_genisligi": "1100", "eta": "0,85"}

    def paket(self, *kartlar):
        yanit = avan_uclari.indir_proje_dwg(
            {
                "kapak": {"project_title": "Avan deneme"},
                "girdiler": {
                    "avan": {
                        "ortak": {"mk_yok": True, "temel_a": "20", "temel_b": "15"},
                        "asansorler": [{**self.HESAP, **k} for k in kartlar],
                        "sabitler": {},
                    }
                },
            }
        )
        self.assertEqual(yanit.media_type, "application/zip", getattr(yanit, "body", b"")[:400])
        z = zipfile.ZipFile(io.BytesIO(yanit.body))
        ad = next(n for n in z.namelist() if n.endswith(".dxf"))
        d = ezdxf.read(io.StringIO(z.read(ad).decode("utf-8", "ignore")))
        bloklar = {b.name for b in d.blocks if b.name.startswith("CIZIM_") and "ELEKTRIK" not in b.name}
        return d, bloklar, (yanit.headers.get("X-Avan-Not") or "").split(",")

    def test_cizimler_pakette(self):
        d, bloklar, notlar = self.paket(kart(T630))
        self.assertNotIn("CIZIM", notlar)
        beklenen = ("kuyu_kesiti_yan", "kuyu_kesiti_on", "kuyu_plani", "kabin_ustu", "kuyu_dibi", "kuyu_ustu")
        self.assertEqual(
            bloklar, {"CIZIM_" + a.upper() for a in (*beklenen, "giris", "kapi_kesiti", "veriler")}
        )
        #  Avan kipi paftada da:  veri tablosunda ürün satırı yok, not var
        veriler = " ".join(t.plain_text() for t in d.blocks.get("CIZIM_VERILER").query("MTEXT TEXT"))
        self.assertIn("uygulama projesinde kesinleşir", veriler)
        self.assertNotIn("konsol arası", veriler)
        #  Motor gücü avanın kendi hesabından ( Nsç ) — hesap sayfasındakiyle aynı
        self.assertEqual(len(re.findall(r"[\d.,]+ kW", veriler)), 1, veriler)

    def test_iki_asansor_adlariyla(self):
        d, bloklar, notlar = self.paket(kart(T630, tanim="İnsan"), kart(T630, tanim="Yük"))
        self.assertNotIn("CIZIM", notlar)
        self.assertTrue({"CIZIM_KUYU_PLANI_1", "CIZIM_KUYU_PLANI_2"} <= bloklar, bloklar)
        yazilar = {
            t.plain_text()
            for b in d.blocks
            if b.name.startswith("CIZIM_KUYU_PLANI_")
            for t in b.query("MTEXT")
        }
        self.assertTrue(any("İnsan" in y for y in yazilar) and any("Yük" in y for y in yazilar), yazilar)

    def test_mimarisiz_paket_eskisi_gibi(self):
        """Kuyu genişliği avan hesabının da girdisidir:  tek başına çizim isteği değildir."""
        _d, bloklar, notlar = self.paket({"kapasite": "8", "V": "1", "kuyu_genisligi": "2050"})
        self.assertEqual(bloklar, set())
        self.assertNotIn("CIZIM", notlar)

    def test_cizilemeyen_asansor_soylenir(self):
        """Mimarisi girilmiş ama çizilemeyen ( eksik kot;  kuyu üstü yetmeyen ) asansör:  paket
        iner, çizimi yoktur, not söyler.  Çizilen asansörün çizimi yine pakettedir."""
        eksik = kart(T630)
        del eksik["kuyu_tavani_kotu"]
        _d, bloklar, notlar = self.paket(eksik)
        self.assertEqual(bloklar, set())
        self.assertIn("CIZIM", notlar)
        d, bloklar, notlar = self.paket(kart(T630, kuyu_genisligi="2350"), kart(T630, tanim="Yük"))
        self.assertIn("CIZIM_KUYU_PLANI", bloklar)
        self.assertFalse(any(b.endswith("_2") for b in bloklar), bloklar)
        self.assertIn("CIZIM", notlar)
        #  Çizilebilen tek asansörün adı paftada yazar ( 14 Kas:  hangi asansör olduğu belli değildi )
        yazilar = {t.plain_text() for t in d.blocks.get("CIZIM_KUYU_PLANI").query("MTEXT")}
        self.assertTrue(any("2 NOLU ASANSÖR" in y and "Yük" in y for y in yazilar), yazilar)


if __name__ == "__main__":
    unittest.main()
