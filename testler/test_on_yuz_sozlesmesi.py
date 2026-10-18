"""YENİ ÖN YÜZÜN SUNUCU SÖZLEŞMESİ — on-yuz/ ( React ).

Yeni ön yüz yalnız KULLANICININ YAZDIĞI değerleri gönderir;  yazılmamış alan
istekte yoktur ve ekranda sunucunun kullandığı değer soluk görünür.  Eski
arayüz ise her kutuyu varsayılanıyla doldurup gönderir.  İkisinin aynı
hesabı vermesi bu sözleşmeye dayanır:

    gönderilmeyen alan  ≡  varsayılanı ( metin olarak ) gönderilmiş alan

Sözleşme bozulursa ( bir alanın "yok" hâli varsayılanından farklı hesaplanırsa )
yeni ön yüz sessizce başka bir proje hesaplar — bu test onu yakalar.  Yeni ön
yüzün yazımları da denenir:  onay alanı "true" / "false", seçim değeri
String( seçenek ) ( 1.6 → "1.6" ).
"""

import json
import unittest

from cizim import istek_onbellegi
from motor.ortak import ofis
from motor.uygulama import uygulama_hesabi
from uclar import uygulama_istegi
from uclar import uc_ortak

ALANLAR = uygulama_istegi.alanlar()
PROJE_GENELI = set(ALANLAR["proje_geneli"])
SEMA_ALANLARI = [a for g in ALANLAR["gruplar"] for a in g["alanlar"]]


def _hesap(asansor, proje_geneli):
    asansorler, ortak = uygulama_istegi.asansor_girdileri(
        {"asansorler": [asansor], "proje_geneli": proje_geneli, "sabitler": {}}
    )
    with istek_onbellegi.etkin():
        s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    return json.loads(json.dumps(s, default=str))


def _ozet(s):
    """Hesabın karşılaştırılan yüzü:  her bölümün hükmü ve bütün adımların yazısı."""
    if not s.get("aktif"):
        return ("HATA", s.get("hata"))
    ozet = [
        (b["kimlik"], b["sonuc"]["metin"], [(a["sembol"], a["metin"]) for a in b["adimlar"]])
        for x in s["asansorler"]
        for b in x["bolumler"]
    ]
    ozet += [(b["kimlik"], b["sonuc"]["metin"]) for b in s.get("proje_geneli") or []]
    return ozet


def _eski_arayuz_yazimi(v):
    """Eski arayüzün kutuya yazdığı metin ( ondalık virgül;  onay kutusu boolean )."""
    if isinstance(v, bool):
        return v
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).replace(".", ",") if isinstance(v, float) else str(v)


def _yeni_on_yuz_yazimi(v):
    """Yeni ön yüzün yazımı ( onay "true" / "false";  seçim String( seçenek ) )."""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _istek(alanlar):
    asansor = {k: v for k, v in alanlar.items() if k not in PROJE_GENELI}
    geneli = {k: v for k, v in alanlar.items() if k in PROJE_GENELI}
    return asansor, geneli


class BosAlanVarsayilandir(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bos = _ozet(_hesap({}, {}))

    def test_bos_istek_hesaplanir(self):
        self.assertIsInstance(self.bos, list, self.bos)

    def test_eski_arayuz_gibi_hepsi_varsayilanla(self):
        alanlar = {
            a["anahtar"]: _eski_arayuz_yazimi(a["varsayilan"])
            for a in SEMA_ALANLARI
            if a["varsayilan"] is not None
        }
        self.assertEqual(_ozet(_hesap(*_istek(alanlar))), self.bos)

    def test_yeni_on_yuz_yazimiyla_hepsi_varsayilanla(self):
        alanlar = {
            a["anahtar"]: _yeni_on_yuz_yazimi(a["varsayilan"])
            for a in SEMA_ALANLARI
            if a["varsayilan"] is not None
        }
        self.assertEqual(_ozet(_hesap(*_istek(alanlar))), self.bos)

    def test_varsayilani_olmayan_alanin_bos_metni_yok_sayilir(self):
        alanlar = {a["anahtar"]: "" for a in SEMA_ALANLARI if a["varsayilan"] is None}
        self.assertEqual(_ozet(_hesap(*_istek(alanlar))), self.bos)

    def test_her_alan_tek_basina(self):
        """Bir alanın varsayılanı tek başına gönderilince de hesap değişmez:  sapan
        alan adıyla görünür."""
        sapan = []
        for a in SEMA_ALANLARI:
            if a["varsayilan"] is None:
                continue
            for yazim in (_eski_arayuz_yazimi, _yeni_on_yuz_yazimi):
                if _ozet(_hesap(*_istek({a["anahtar"]: yazim(a["varsayilan"])}))) != self.bos:
                    sapan.append((a["anahtar"], yazim.__name__))
        self.assertEqual(sapan, [])


class BosMetinTablodan(unittest.TestCase):
    """Boş metin ile gönderilmeyen alan bir tek bos_tablodan alanlarında ayrışır:
    gönderilmeyen varsayılandır, boş metin tablonun değeridir.  Yeni ön yüz bu
    alanlarda boşu boş gönderir ( 18 Eki:  boş kabin kütlesi gönderilmiyordu,
    beyan yükü 1275 kg iken hesap tablonun 1100'ü yerine 700 ile yapılıyordu ).
    """

    def test_liste_taramayla_esit(self):
        """Boş metnin HESAP EKSİK demeden başka bir hesap verdiği alanlar listede
        olmalı — yenisi eklenirse ön yüz onu da boş göndermeyi öğrenir."""
        bos = _ozet(_hesap({}, {}))
        ayrisan = []
        for a in SEMA_ALANLARI:
            if a["varsayilan"] is None:
                continue
            o = _ozet(_hesap(*_istek({a["anahtar"]: ""})))
            if not isinstance(o, list) or o == bos:
                continue
            if any(str(b[1]).startswith("HESAP EKSİK") for b in o):
                continue  # boş = eksik girdi ( kuyu genişliği gibi ):  sunucu söyler
            ayrisan.append(a["anahtar"])
        self.assertEqual(sorted(ayrisan), sorted(ALANLAR["bos_tablodan"]))

    def test_bos_kabin_kutlesi_tablonun_degeri(self):
        tablo = ofis.bos_kabin_kutlesi(1275)
        bos = _ozet(_hesap({"beyan_yuku": "1275", "kabin_agirligi": ""}, {}))
        yazili = _ozet(_hesap({"beyan_yuku": "1275", "kabin_agirligi": _eski_arayuz_yazimi(tablo)}, {}))
        self.assertEqual(bos, yazili)
        self.assertNotEqual(bos, _ozet(_hesap({"beyan_yuku": "1275"}, {})))


class SecimYazimi(unittest.TestCase):
    def test_her_secenek_yeni_on_yuzun_yazimiyla_taninir(self):
        """Yeni ön yüz seçimi String( seçenek ) olarak gönderir ( 1.6 → "1.6" ):
        sunucu her birini listedeki değere eşlemeli, "belirsiz sayı" saymamalı."""
        taninmayan = []
        gizli_mrl = set(ALANLAR["yerlesime_gore_gizli"]["mrl"])
        for a in SEMA_ALANLARI:
            #  Alan göründüğü yerleşimde denenir ( gizli alanı sunucu okumaz )
            yerlesim = {"mk_yok": "false"} if a["anahtar"] in gizli_mrl else {}
            for s in a["secenekler"] or []:
                self.assertFalse(uc_ortak.belirsiz_sayi_mi(_yeni_on_yuz_yazimi(s)), (a["anahtar"], s))
                girdi = {**yerlesim, a["anahtar"]: _yeni_on_yuz_yazimi(s)}
                g = uygulama_istegi.mukavemet_girdisi({"girdiler": girdi})
                if a["anahtar"] in g and g[a["anahtar"]] != s:
                    taninmayan.append((a["anahtar"], s, g[a["anahtar"]]))
        self.assertEqual(taninmayan, [])


if __name__ == "__main__":
    unittest.main()
