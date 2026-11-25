"""AVAN ÇİZİMLERİNİN UCU ( /api/avan/cizimler — uclar/avan_cizim_uclari;  12 Kas ).
Gövde avan hesabınınki ( /api/avan );  asansörün mimarisi kartta.  Yanıt seçicinin
sonucu;  "uygun"da uygulamanın çizim yanıtı.  Çizim bulunamadıysa çizim YOKTUR."""

import asyncio
import io
import json
import re
import time
import unittest
import zipfile
import zlib

import ezdxf
from pypdf import PdfReader

from cizim import asamalar, avan_kipi, kasnak_duzeni, katlar, pafta
from motor.uygulama import uygulama_hesabi
from uclar import (
    avan_cizim_uclari,
    avan_cizimi,
    avan_secici,
    avan_uclari,
    cizim_uclari,
    uc_ortak,
    uygulama_istegi,
)

T630 = avan_secici.paketler()[(630, True)]["asansor"]
#  Kuyu üstü yetmeyen geniş kuyu:  2350, son kat 3.700 ( 24 Kas:  korkuluğun dışındaki parçaya
#  0,10 m açıklık — kartın 4.200'ü artık yetiyor;  eskiden yetmiyordu, kuyu tavanı +19,38 istenirdi.
#  Aynı gün küpeşte tavana asılı parçalardan da içeri alınınca 3.800 de yetiyor;  4.000 artık uygun )
GENIS_YETMEZ = {"kuyu_genisligi": "2350", "kuyu_tavani_kotu": "+18,70"}
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
    """Çizim yanıtının bütün SVG'lerindeki yazılar.  İki satıra bölünmüş çizim başlığı ( 20 Kas —
    geometri.cerceveli:  "AD   1/20" + "( açıklama )" ) tek satırlık hâliyle tek yazıdır:  avanın ve
    uygulamanın aynı çizimi farklı enlerde, başlık birinde bölünüp öbüründe bölünmeyebilir."""
    out = set()
    for x in c["cizimler"]:
        t = [
            re.sub(r"<[^>]+>", "", m).strip()
            for m in re.findall(r"<text[^>]*>(.*?)</text>", x["svg"], flags=re.S)
        ]
        i = 0
        while i < len(t):
            m = re.fullmatch(r"(.*\S)(   1/\d+)", t[i])
            if m and i + 1 < len(t) and t[i + 1].startswith("( ") and t[i + 1].endswith(" )"):
                out.add(f"{m.group(1)}  {t[i + 1]}{m.group(2)}")
                i += 2
            else:
                out.add(t[i])
                i += 1
    return out


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
        ( motor, halat, ray profili ) yazmaz.  Kasnak düzenlemesi avanda DA vardır ( 17 Kas,
        kullanıcı:  "makine daireli dairesiz fark etmez, geri açalım" ) — altında kasnak
        çaplarının hazır asansörün olduğu yazar.  Aynı istek uygulamadan sorulunca hepsi
        yerindedir ( avan kipi sızmaz )."""
        r = yanit(govde(kart(T630)))
        avan = yazilar(r["cizim"])
        uygulama = yazilar(json.loads(cizim_uclari.api_cizimler(r["istek"]).body))
        urun = re.compile(r"kW|konsol arası|kasnak ø|halat ø|\d × ø|70 × 65 × 9|50 × 50 × 5")
        self.assertEqual(sorted(t for t in avan if urun.search(t)), [])
        self.assertGreaterEqual(len({t for t in uygulama if urun.search(t)}), 5)
        self.assertIn(avan_kipi.NOT, avan)
        self.assertNotIn(avan_kipi.NOT, uygulama)
        #  Kalan satırlar aynı:  avan yalnız eksiltir ( + notu ve onun sıra numarası ).  Kuyu tabanının
        #  kuvvetleri avanın hesabından ( 17 Kas — test_avan_ray_yuku ):  bu kartta avan hesabı yok
        #  ( kabin, verim girilmedi ) — yalnız adları;  yük kutuları kısalınca perde yazısının
        #  kısa / uzun biçimi başka seçilebilir
        fark = {t for t in avan - uygulama if "Dişlisiz" not in t} - {"FKR", "FAR", "Fkt", "Fat"}
        self.assertEqual(
            {t for t in fark if not t.endswith("PERDESİ")},
            {avan_kipi.NOT, "3.", *kasnak_duzeni.AVAN_NOTU},
        )
        #  Kasnak düzenlemesi ikisinde de;  açısı aynı ( geometri aynı )
        for c in (r["cizim"], json.loads(cizim_uclari.api_cizimler(r["istek"]).body)):
            self.assertIn("kasnak_duzeni", [x["ad"] for x in c["cizimler"]])
        self.assertEqual(
            {t for t in avan if t.startswith("SARIM AÇISI")},
            {t for t in uygulama if t.startswith("SARIM AÇISI")},
        )
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
        """Paftanın girdisi avan kipinde kurulunca:  antette ray boş, hesap notu yok, kasnak
        düzenlemesi sırada ( 17 Kas );  kip kapanınca aynı istek uygulamanın paftasıdır."""
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
        self.assertIn("kasnak_duzeni", pafta.sira(g))
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
        """24 Kas ( kullanıcı:  "Evet, kullanılsın" ):  çizimin kabini kartınkidir — standarda
        uyuyorsa ( avan_secici.kabin_nedenleri ).  13 Kas'tan beri hep hazır asansörünküydü, kartınki
        farklıysa çizim çıkmıyordu.  Uymayan kabinle çizim ÇIKMAZ ( hesap sayfası ile pafta ayrı kabin
        göstermesin;  seçici aramaz ):  sebep ve karta yazılacak hazır asansör kabini döner,
        uygulanınca çizim çıkar.  Kartta kabin yoksa ( hesap henüz eksik ) hazır asansörünki."""
        #  630 kg, 8 kişi:  1000 × 1550 = 1,55 m² ( Çizelge 6 en çok 1,66;  Çizelge 8 8 kişi en az 1,45 ),
        #  kuyu da kabin farkı kadar:  100 mm dar, 150 mm derin
        g = govde(
            {
                **kart(T630, kuyu_genisligi="1950", kuyu_derinligi="2000"),
                **AvanPaketi.HESAP,
                "kabin_boyu": "1550",
                "kabin_genisligi": "1000",
            }
        )
        r = yanit(g)
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kabin_derinligi"], a["kabin_genisligi"]), ("1550", "1000"))
        #  Ekranın kabin kutularına:  avan yanıtında çizimin kabini ( kartınki — düğme görünmez )
        kot = json.loads(avan_uclari.api_avan(g).body)["kotlar"][0]
        self.assertEqual(kot["kabin"], {"kabin_boyu": 1550, "kabin_genisligi": 1000})
        #  Büyük kabin:  1100 × 1600 = 1,76 m² > 1,66 — çizim yok, kart hazır asansörün kabinine
        g = govde({**kart(T630), **AvanPaketi.HESAP, "kabin_boyu": "1600"})
        r = yanit(g)
        self.assertEqual((r["durum"], r["beyan_turu"], r["sinama"]), ("beyan", "kabin", 0), r)
        self.assertNotIn("cizim", r)
        self.assertEqual(
            [(b["kart"], b["etiket"], b["eski_yazi"], b["yeni_yazi"], b["yeni"]) for b in r["beyan"]],
            [("kabin_boyu", "Kabin boyu a", "1600 mm", "1400 mm", "1400")],
        )
        (neden,) = r["nedenler"]
        self.assertIn("Çizelge 6", neden)
        self.assertIn("1,76 m²", neden)
        self.assertIn("standarda uymuyor", avan_cizimi.cizimsiz_sebebi(r))
        kot = json.loads(avan_uclari.api_avan(g).body)["kotlar"][0]
        self.assertEqual(kot["kabin"], {"kabin_boyu": 1400, "kabin_genisligi": 1100})
        duzeltilmis = g["girdiler"]["asansorler"][0] | {b["kart"]: b["yeni"] for b in r["beyan"]}
        r = yanit(govde(duzeltilmis))
        self.assertEqual(r["durum"], "uygun", r)
        a = r["istek"]["asansorler"][0]
        self.assertEqual((a["kabin_derinligi"], a["kabin_genisligi"]), ("1400", "1100"))
        #  Küçük kabin trafiğin 8 kişisini taşımaz:  1000 × 1400 = 1,40 m² < 1,45 ( Çizelge 8 )
        r = yanit(govde({**kart(T630), "kabin_boyu": "1400", "kabin_genisligi": "1000"}))
        self.assertEqual((r["durum"], r["beyan_turu"]), ("beyan", "kabin"), r)
        self.assertEqual([b["kart"] for b in r["beyan"]], ["kabin_genisligi"])
        self.assertIn("Çizelge 8", r["nedenler"][0])
        self.assertEqual(yanit(govde(kart(T630)))["durum"], "uygun")
        #  Hazır asansörü olmayan kapasite:  kabin bilinmez, sonuç eskisi gibi
        self.assertEqual(yanit(govde(kart(T630, kapasite="15", kabin_boyu="1500")))["durum"], "paket_yok")

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
        r = yanit(govde(kart(T630, **GENIS_YETMEZ)))
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
        #  15 kişi ( 1125 kg ) MMO/697 Tablo-7'de basılı değildir:  kabini standartta yok
        r = yanit(govde(kart(T630, kapasite="15")))
        self.assertEqual(r["durum"], "paket_yok")
        self.assertNotIn("hiz", r)

    def test_makine_dairesi_kapisi_suruklenir(self):
        """17 Kas:  makine dairesi kapısı ekranda dört duvar arasında sürüklenir.  Kapının
        çizildiği planlar kapının duvarını, yerini, enini ve odanın iç ölçülerini taşır
        ( "kapi" — ekran gölgeyi bundan çizer );  kartın ayarı ( md_kapi_duvar / md_kapi_konum )
        çizime yansır;  uygun olmayan yerde çizim eski kapısıyla gelir, sebep kapi_reddi'nde."""
        a, pg = T800MD["asansor"], T800MD["proje_geneli"]
        ortak = {"mk_yok": False, "mk_uzunluk": pg["mk_uzunluk"], "mk_genislik": pg["mk_genislik"]}

        def kapilar(r):
            return {c["ad"]: c["kapi"] for c in r["cizim"]["cizimler"] if "kapi" in c}

        r = yanit(govde(kart(a, i_palanga="1"), ortak))
        self.assertEqual(r["durum"], "uygun", r)
        ilk = kapilar(r)
        self.assertEqual(set(ilk), {"makine_dairesi", "delik_plani"})
        k = ilk["makine_dairesi"]
        self.assertEqual(k, ilk["delik_plani"])
        self.assertEqual((k["duvar"], k["konum"], k["en"]), ("Arka", 300, 800))
        self.assertEqual((k["genislik"], k["derinlik"]), (float(pg["mk_genislik"]), float(pg["mk_uzunluk"])))
        #  Aynı duvarda kaydırma:  çizim yeni yerle
        r = yanit(govde(kart(a, i_palanga="1", cizim_ayarlari="md_kapi_konum=700"), ortak))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertNotIn("kapi_reddi", r)
        self.assertEqual(kapilar(r)["makine_dairesi"], {**k, "konum": 700})
        self.assertEqual([(x["anahtar"], x["deger"]) for x in r["ayarlar"]], [("md_kapi_konum", "700")])
        #  Duvarın dışı:  çizim kaybolmaz, kapı eski yerinde, sebep söylenir
        r = yanit(govde(kart(a, i_palanga="1", cizim_ayarlari="md_kapi_duvar=Ön;md_kapi_konum=9000"), ortak))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertTrue(r["cizim"]["aktif"])
        self.assertEqual(kapilar(r), ilk)
        self.assertIn("duvarın dışına taşıyor", " ".join(r["kapi_reddi"]))
        #  Makine dairesiz projede kapı bilgisi yok
        self.assertEqual(kapilar(yanit(govde(kart(T630)))), {})

    def test_kot_tablosunun_dosemesi_cizimin_dosemesi(self):
        """16 Kas ( kullanıcının A BLOK 800 KG projesi ):  duvar kalınlığı elle 250'ye ayarlı
        kartta makine dairesi zemini kot tablosunun "döşemenin üstü"ne eşit girilince çizimde
        kot farkı OLMAMALI.  Eskiden tablo döşemeyi 150, çizim 250 alıyordu:  planda
        "TABLİYE +100"."""
        a, pg = T800MD["asansor"], T800MD["proje_geneli"]
        ortak = {"mk_yok": False, "mk_uzunluk": pg["mk_uzunluk"], "mk_genislik": pg["mk_genislik"]}
        k = kart(a, i_palanga="1", cizim_ayarlari="kuyu_duvar_kalinligi=250")
        doseme = avan_cizimi.doseme_kurali(k)
        self.assertEqual(doseme, 250)
        tavan, _hata = katlar.kot_oku(k["kuyu_tavani_kotu"])
        r = yanit(govde({**k, "md_zemini_kotu": katlar.kot_metni(tavan + doseme)}, ortak))
        self.assertEqual(r["durum"], "uygun", r)
        self.assertNotIn("TABLİYE", " ".join(yazilar(r["cizim"])))

    def test_kartin_elle_ayari(self):
        """Çizimde tıklanıp değiştirilen ölçü kartta durur ( cizim_ayarlari:  "girdi=değer;…" );
        seçici aynen kullanır, yanıt ayarları ekrandaki adlarıyla verir."""
        r = yanit(govde(kart(T630, cizim_ayarlari="ray_kapi_arasi=700; kuyu_genisligi=9999;bozuk")))
        self.assertEqual(r["durum"], "uygun", r.get("nedenler") or r.get("gereken"))
        a = r["istek"]["asansorler"][0]
        self.assertEqual(a["ray_kapi_arasi"], "700")
        self.assertEqual(a["kuyu_genisligi"], T630["kuyu_genisligi"])
        self.assertEqual(
            [(x["anahtar"], x["deger"], x["birim"]) for x in r["ayarlar"]], [("ray_kapi_arasi", "700", "mm")]
        )
        self.assertIn("Ray", r["ayarlar"][0]["etiket"])
        #  Ayar yoksa liste boş
        self.assertEqual(yanit(govde(kart(T630)))["ayarlar"], [])
        #  17 Kas:  çizim çıkmasa da ( kartın kabini standarda uymuyor ) adlarıyla — ekranda ad
        #  yerine "kuyu_duvar_kalinligi" yazıyordu
        r = yanit(govde(kart(T630, kabin_boyu="1700", cizim_ayarlari="kuyu_duvar_kalinligi=250")))
        self.assertEqual((r["durum"], r["beyan_turu"]), ("beyan", "kabin"), r)
        self.assertEqual(
            [(x["anahtar"], x["deger"]) for x in r["ayarlar"]], [("kuyu_duvar_kalinligi", "250")]
        )
        self.assertNotIn("_", r["ayarlar"][0]["etiket"])

    def test_uygulamada_olmayan_hiz(self):
        """Avanın 1,75 ve 3,5 m/s hızları uygulamanın hız listesinde yoktur:  çizim çıkmaz
        ( kullanıcı kararı, 14 Kas ) — "geçersiz seçim" hatası değil, açık ileti."""
        for hiz in ("1,75", "3,5"):
            r = yanit(govde(kart(T630, V=hiz)))
            self.assertEqual(r["durum"], "paket_yok", r)
            self.assertTrue(r["hiz"])
            self.assertIn(1.6, r["hizlar"])
            self.assertNotIn(1.75, r["hizlar"])

    def test_yeni_kapasiteler(self):
        """14 Kas:  6 · 20 · 25 · 30 kişi ( 450 · 1600 · 2000 · 2500 kg ) avan çizimi verir —
        yalnız avanın hazır asansörleri ( uclar/avan_paketleri.json ).  1600 kg ve üstünde
        ürün bölümleri açık kalabilir;  çizimi engellemez.  KİŞİ avanınkidir ( 18 Kas — yayın öncesi
        denetim ):  trafik, hesap belgesi ve kapak 1600 kg'a 20 kişi ( MMO/697 Tablo-7 ) derken pafta
        hazır asansörün kabininden ( TS EN 81-20 ) 21 yazıyordu."""
        for kisi, yuk in (("6", 450), ("20", 1600)):
            a = avan_secici.paketler()[(yuk, True)]["asansor"]
            k = {"kapasite": kisi, "V": "1", **{x: a[x] for x in avan_cizimi.KART if x in a}}
            r = yanit(govde(k))
            self.assertEqual(r["durum"], "uygun", r.get("nedenler") or r.get("gereken"))
            self.assertEqual(r["istek"]["asansorler"][0]["beyan_yuku"], str(yuk))
            #  Makine dairesizin bütün paftası ( kasnak düzenlemesi dahil — 17 Kas )
            self.assertEqual([c["ad"] for c in r["cizim"]["cizimler"]], list(pafta.SIRA_MRL))
            self.assertEqual(bool(r["acik_bolumler"]), yuk >= 1600)
            self.assertIn(f"{yuk} kg  ·  {kisi} kişi", yazilar(r["cizim"]))
        #  Uygulamada ( avan kipi kapalı ) aynı istek kabinin kişisini yazar:  1600 kg'ın kabini 21 kişi
        self.assertIn("1600 kg  ·  21 kişi", yazilar(json.loads(cizim_uclari.api_cizimler(r["istek"]).body)))


class AvanPaketi(unittest.TestCase):
    """ "Projeyi indir" ( /api/indir/proje-dwg ):  mimarisi girilen asansörlerin çizimleri
    avan hesap sayfalarının sağında.  Mimari girilmemişse paket eskisi gibidir;  girilip de
    çizilemeyen asansör pakete çizimsiz girer ve not ( X-Avan-Not:  CIZIM ) söyler."""

    #  Avan hesabının kendi kart alanları ( çizimden bağımsız )
    #  ( η ekrandan hep gelir:  makine tipinin verimi — eksikse asansör hesaplanmaz )
    HESAP = {"Hk": "20,8", "kabin_boyu": "1400", "kabin_genisligi": "1100", "eta": "0,85"}

    def girdi(self, *kartlar, ortak=None):
        return {
            "ortak": {"mk_yok": True, "temel_a": "20", "temel_b": "15", **(ortak or {})},
            "asansorler": [{**self.HESAP, **k} for k in kartlar],
            "sabitler": {},
        }

    def ham_paket(self, *kartlar, ortak=None):
        return avan_uclari.indir_proje_dwg(
            {
                "kapak": {"project_title": "Avan deneme"},
                "girdiler": {"avan": self.girdi(*kartlar, ortak=ortak)},
            }
        )

    def test_kagit_eni(self):
        """ "Projeyi indir"in kâğıt eni ( 19 Kas ):  900 → çerçeve 900 mm, çizimler onun içinde;
        600 / 900 dışı değer asansör aranmadan reddedilir."""
        veri = {"kapak": {"project_title": "Avan deneme"}, "girdiler": {"avan": self.girdi(kart(T630))}}
        self.assertIn("KÂĞIT ENİ", json.loads(avan_uclari.indir_proje_dwg(dict(veri, kagit=75)).body)["hata"])
        yanit = avan_uclari.indir_proje_dwg(dict(veri, kagit=900))
        self.assertEqual(yanit.media_type, "application/zip", yanit.body[:300])
        z = zipfile.ZipFile(io.BytesIO(yanit.body))
        d = ezdxf.read(
            io.StringIO(z.read(next(n for n in z.namelist() if n.endswith(".dxf"))).decode("utf-8"))
        )
        msp = d.modelspace()
        ust = pafta.ust_kenar(900)
        ustler = [p.x for e in msp.query("LINE") for p in (e.dxf.start, e.dxf.end) if abs(p.y - ust) < 0.5]
        self.assertTrue(ustler)
        cizimler = [e for e in msp.query("INSERT") if e.dxf.name.startswith("CIZIM_")]
        self.assertTrue(any(e.dxf.name == "CIZIM_KUYU_KESITI_YAN" for e in cizimler))
        for e in cizimler:
            with self.subTest(blok=e.dxf.name):
                self.assertGreaterEqual(e.dxf.insert.y, pafta.BANT[1] - 0.5)
                self.assertLess(e.dxf.insert.x, max(ustler))

    def test_kapak_her_pakette(self):
        """18 Kas ( yayın öncesi denetim — uygulama paketiyle aynı sınıf ):  istekte kapak yoksa ya
        da boşsa kapak hesaptan türetilir ( kapak.trafikten / avandan — ekranın kullandığı );
        kapaksız pakette ofis şablonunun antet hücreleri kendi örnek değerleriyle kalıyordu."""
        for kapak in (None, {}, {"project_title": ""}):
            with self.subTest(kapak=kapak):
                veri = {"girdiler": {"avan": self.girdi(kart(T630))}}
                if kapak is not None:
                    veri["kapak"] = kapak
                yanit = avan_uclari.indir_proje_dwg(veri)
                self.assertEqual(yanit.media_type, "application/zip", yanit.body[:300])
                z = zipfile.ZipFile(io.BytesIO(yanit.body))
                ad = next((n for n in z.namelist() if n.endswith("Kapak.pdf")), None)
                self.assertIsNotNone(ad, z.namelist())
                dxf = z.read(next(n for n in z.namelist() if n.endswith(".dxf"))).decode("utf-8")
                for ornek in ("300 KG (4 KİŞİ)", "0,1/2 DURAK", "2,67 KW"):
                    self.assertNotIn(ornek, dxf)
                #  Kapağın asansör satırları avan hesabından:  kartın kapasitesi, hızı
                metin = PdfReader(io.BytesIO(z.read(ad))).pages[0].extract_text()
                self.assertIn("8 kişi", metin)
                self.assertIn("1,00 m/s", metin)
        #  Ne kapak ne hesap:  paket yok ( eskisi gibi )
        bos = json.loads(avan_uclari.indir_proje_dwg({"girdiler": {}}).body)
        self.assertIn("hiç sayfa yok", bos["hata"])

    def test_eksik_avanla_paket_inmez(self):
        """18 Kas ( yayın öncesi denetim ):  avan hesabı eksikken paket inmez, sebebi söylenir — çizim,
        hesap sayfası ve elektrik projesi çelişiyordu ( makine dairesi ölçüsüz projede çizim hazır
        asansörün odasını çiziyor, hesap "ölçüler girilmedi" diyor, elektrik projesinde oda devresi
        adetsizdi;  kabini girilmemiş asansörün çizimi tam, hesabı yoktu ).  Aynı liste /api/avan
        yanıtında ( avan_hesabi.teslim_eksikleri — ekran "Projeyi indir"i kapatır).  Uygun olmayan
        bölüm paketi durdurmaz:  o paftanın kendi hükmüdür."""
        md = {k: T800MD["asansor"][k] for k in avan_cizimi.KART if k in T800MD["asansor"]}
        for ad, kart_, ortak, ileti in (
            ("kabin", kart(T630, kabin_boyu=""), {}, "Kabin boyu"),
            ("topraklama", kart(T630), {"temel_a": ""}, "Temel ölçüleri"),
            (
                "makine dairesi",
                {**md, "kapasite": "10", "V": "1"},
                {"mk_yok": False},
                "MAKİNE DAİRESİ ÖLÇÜLERİ",
            ),
        ):
            with self.subTest(ad):
                yanit = self.ham_paket(kart_, ortak=ortak)
                self.assertNotEqual(yanit.media_type, "application/zip")
                hata = json.loads(yanit.body)["hata"]
                self.assertIn("proje paketi inmez", hata)
                self.assertIn(ileti, hata)
                s = json.loads(avan_uclari.api_avan({"girdiler": self.girdi(kart_, ortak=ortak)}).body)
                self.assertTrue(any(ileti in x for x in s["teslim_eksikleri"]), s["teslim_eksikleri"])
        #  Eksiksiz:  liste boş;  uygun olmayan bölüm ( elle seçilen küçük motor ) durdurmaz
        for k in (kart(T630), kart(T630, Nsc="1,1")):
            s = json.loads(avan_uclari.api_avan({"girdiler": self.girdi(k)}).body)
            self.assertEqual(s["teslim_eksikleri"], [])
            self.assertEqual(self.ham_paket(k).media_type, "application/zip")
        self.assertEqual(s["proje_hukmu"]["durum"], "uygun_degil")

    def paket(self, *kartlar):
        yanit = self.ham_paket(*kartlar)
        self.assertEqual(yanit.media_type, "application/zip", getattr(yanit, "body", b"")[:400])
        z = self.zip = zipfile.ZipFile(io.BytesIO(yanit.body))
        ad = next(n for n in z.namelist() if n.endswith(".dxf"))
        d = ezdxf.read(io.StringIO(z.read(ad).decode("utf-8", "ignore")))
        bloklar = {b.name for b in d.blocks if b.name.startswith("CIZIM_") and "ELEKTRIK" not in b.name}
        return d, bloklar, (yanit.headers.get("X-Avan-Not") or "").split(",")

    def test_cizimler_pakette(self):
        d, bloklar, notlar = self.paket(kart(T630))
        self.assertNotIn("CIZIM", notlar)
        beklenen = (
            "kuyu_kesiti_yan",
            "kuyu_kesiti_on",
            "kuyu_plani",
            "kabin_ustu",
            "kuyu_dibi",
            "kuyu_ustu",
            "kasnak_duzeni",
        )
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
        """Mimarisi girilmiş ama çizilemeyen ( kuyu üstü yetmeyen ) asansör:  paket iner, çizimi
        yoktur, not söyler.  Çizilen asansörün çizimi yine pakettedir.  ( 18 Kas ) Kotu eksik kart
        avan hesabını da tamamlamaz ( kuyu yüksekliği kotlardan ):  paket inmez, sebebi söylenir —
        test_eksik_avanla_paket_inmez."""
        eksik = kart(T630)
        del eksik["kuyu_tavani_kotu"]
        yanit = self.ham_paket(eksik)
        self.assertNotEqual(yanit.media_type, "application/zip")
        self.assertIn("Kuyu tavanı kotu", json.loads(yanit.body)["hata"])
        d, bloklar, notlar = self.paket(kart(T630, **GENIS_YETMEZ), kart(T630, tanim="Yük"))
        self.assertIn("CIZIM_KUYU_PLANI", bloklar)
        self.assertFalse(any(b.endswith("_2") for b in bloklar), bloklar)
        self.assertIn("CIZIM", notlar)
        #  Paketin içinde de yazar ( 14 Kas ):  hangi asansör, neden
        (ad,) = [n for n in self.zip.namelist() if n.endswith("ÇİZİMİ OLMAYAN ASANSÖRLER.txt")]
        metin = self.zip.read(ad).decode("utf-8-sig")
        self.assertIn("1 NOLU ASANSÖR:  mimardan istenecek:", metin)
        self.assertNotIn("2 NOLU ASANSÖR", metin)
        #  Çizilebilen tek asansörün adı paftada yazar ( 14 Kas:  hangi asansör olduğu belli değildi )
        yazilar = {t.plain_text() for t in d.blocks.get("CIZIM_KUYU_PLANI").query("MTEXT")}
        self.assertTrue(any("2 NOLU ASANSÖR" in y and "Yük" in y for y in yazilar), yazilar)


if __name__ == "__main__":
    unittest.main()


def akisli_istek(g, kodlama="gzip", kes=None):
    """/api/avan/cizimler'e akışlı istek, bütün uygulama üzerinden ( main.app — sıkıştırma ara
    katmanı dahil ).  Döner ( başlıklar , [ gövde parçaları ] ).  kes:  bu kadar parça gelince
    bağlantı kapanır ( ekran isteği bıraktı )."""
    import main

    govde = json.dumps(g).encode()
    kapsam = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/avan/cizimler",
        "raw_path": b"/api/avan/cizimler",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"content-type", b"application/json"),
            (b"accept", uc_ortak.AKIS_TURU.encode()),
            (b"accept-encoding", kodlama.encode()),
            (b"content-length", str(len(govde)).encode()),
        ],
        "client": ("test", 1),
        "server": ("test", 80),
    }
    basliklar, parcalar = {}, []

    async def calistir():
        bitti = asyncio.Event()
        okundu = False

        async def al():
            nonlocal okundu
            if not okundu:
                okundu = True
                return {"type": "http.request", "body": govde, "more_body": False}
            await bitti.wait()
            return {"type": "http.disconnect"}

        async def gonder(m):
            if m["type"] == "http.response.start":
                basliklar.update({k.decode(): v.decode() for k, v in m["headers"]})
            elif m["type"] == "http.response.body":
                if m.get("body"):
                    parcalar.append(m["body"])
                if not m.get("more_body") or (kes and len(parcalar) >= kes):
                    bitti.set()

        await main.app(kapsam, al, gonder)

    asyncio.run(calistir())
    return basliklar, parcalar


class AvanCizimAkisi(unittest.TestCase):
    """AKIŞLI YANIT ( 17 Kas — kullanıcı:  "beklerken ne yapıldığını görelim" ):  ekran aramanın
    gerçek aşamalarını gösterir ( asamalar.Ilerleme — avan_secici.ASAMALAR ).  Sonuç tek JSON'la AYNI;  aşamalar
    geldikleri anda açılır ( sıkıştırma biriktirmez );  aşama bildirimi seçimi etkilemez."""

    #  Kuyu üstü yetmeyen geniş kuyu:  ~8 sn, birkaç aşama ( yerleşim → uyarlama → küçültme → doğrulama )
    GENIS = GENIS_YETMEZ

    def setUp(self):
        avan_secici._ONBELLEK.clear()

    def satirlar(self, basliklar, parcalar):
        """Her parça GELDİĞİ ANDA açılır:  tam satırlar çıkmalı ( yarım satır biriktirilmez )."""
        coz = zlib.decompressobj(31) if basliklar.get("content-encoding") == "gzip" else None
        sonuc = []
        for p in parcalar:
            metin = (coz.decompress(p) if coz else p).decode("utf-8")
            self.assertTrue(metin.endswith("\n"), "parça satır ortasında bitti:  sıkıştırma biriktiriyor")
            sonuc += [json.loads(s) for s in metin.splitlines() if s.strip()]
        return sonuc

    def test_sonuc_tek_jsonla_ayni_asamalar_aninda(self):
        g = govde(kart(T630, **self.GENIS))
        basliklar, parcalar = akisli_istek(g)
        self.assertEqual(basliklar["content-type"], uc_ortak.AKIS_TURU)
        self.assertEqual(basliklar.get("content-encoding"), "gzip")
        satirlar = self.satirlar(basliklar, parcalar)
        self.assertIn("sonuc", satirlar[-1])
        ilerleme = [s["ilerleme"] for s in satirlar[:-1]]
        self.assertGreater(len(ilerleme), 1, "aşamalar sonuçtan önce gelmeli")
        kodlar = [a["kod"] for a in ilerleme[-1]["asamalar"]]
        self.assertEqual(kodlar[:2], ["paket", "yerlesim"])
        self.assertTrue(set(kodlar) <= set(avan_secici.ASAMALAR))
        #  Sınama sayısı azalmaz
        sayilar = [i["sinama"] for i in ilerleme]
        self.assertEqual(sayilar, sorted(sayilar))
        avan_secici._ONBELLEK.clear()
        akisli, tek = satirlar[-1]["sonuc"], yanit(g)
        for r in (akisli, tek):
            r.pop("sure")
        self.assertEqual(akisli, tek)

    def test_cizimli_yanit_sikisik_iner(self):
        """Uygun kuyuda çizimler ( ~800 KB ):  akışlı yanıt da sıkışık — ara katmanınki kadar."""
        g = govde(kart(T630))
        basliklar, parcalar = akisli_istek(g)
        satirlar = self.satirlar(basliklar, parcalar)
        sonuc = satirlar[-1]["sonuc"]
        self.assertEqual(sonuc["durum"], "uygun", sonuc)
        ham = len(json.dumps(sonuc, ensure_ascii=False).encode())
        self.assertGreater(ham, 300_000)
        self.assertLess(sum(map(len, parcalar)), ham / 8)
        #  Çizim aşaması da bildirildi ( önbellekten gelmediyse )
        if len(satirlar) > 1:
            self.assertIn("cizim", [a["kod"] for a in satirlar[-2]["ilerleme"]["asamalar"]])

    def test_sikistirma_istenmezse_duz(self):
        basliklar, parcalar = akisli_istek(govde(kart(T630)), kodlama="identity")
        self.assertNotIn("content-encoding", basliklar)
        self.assertEqual(self.satirlar(basliklar, parcalar)[-1]["sonuc"]["durum"], "uygun")

    def test_baglanti_kapaninca_arama_durur(self):
        """Ekran isteği bıraktı ( girdi değişti ):  arama sonuna kadar sürmez, sonuç saklanmaz."""
        t0 = time.monotonic()
        akisli_istek(govde(kart(T630, kuyu_genisligi="1500")), kes=1)
        self.assertLess(time.monotonic() - t0, 10)
        self.assertEqual(len(avan_secici._ONBELLEK), 0)

    def test_asama_bildirimi_secimi_etkilemez(self):
        m = avan_cizimi.secim(avan_uclari.avan_girdisi(govde(kart(T630, **self.GENIS)))[0], 0)
        i = asamalar.Ilerleme(avan_secici.ASAMALAR)
        with asamalar.bagla(i):
            m2 = avan_cizimi.secim(avan_uclari.avan_girdisi(govde(kart(T630, **self.GENIS)))[0], 0)
        for r in (m, m2):
            r.pop("sure", None)
        self.assertEqual(m, m2)
        durum = i.durum()[1]
        self.assertEqual(durum["sinama"], m["sinama"])
        #  Bütün aşamalar:  doğrulamanın içindeki yeniden seçim listeye girmez ( paket bir kez )
        kodlar = [a["kod"] for a in durum["asamalar"]]
        self.assertEqual(kodlar[0], "paket")
        self.assertEqual(kodlar[-1], "dogrulama")
        self.assertNotIn("paket", kodlar[1:])
        self.assertEqual(
            [a["ayrinti"] for a in durum["asamalar"] if a["kod"] == "yerlesim"],
            ["ağırlık yanda", "ağırlık arkada"],
        )
