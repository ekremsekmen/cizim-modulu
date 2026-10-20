# -*- coding: utf-8 -*-
"""
ÇİZİMLERİN LİSTESİ  —  adı, doğrulaması, çizicisi, başlığı ve ölçeği

calistir.py ( tek tek çizim ) ve pafta.py ( TİP PROJE FORMATI ) buradan okur;
başlıklar ve ölçekler iki yerde ayrı yazılıp zamanla ayrışmasın.
"""

from cizim import geometri
from cizim import kabin_ustu
from cizim import giris
from cizim import kapi_kesiti
from cizim import kasnak_duzeni
from cizim import kuyu_dibi
from cizim import kuyu_kesiti
from cizim import kuyu_ustu
from cizim import makine_dairesi
from cizim import sorunlu
from cizim import veri_tablosu


CIZIMLER = {
    "kuyu_plani": (geometri.dogrula, geometri.plan, "KUYU PLANI  ( kabin hizasından yatay kesit )"),
    "kabin_ustu": (
        kabin_ustu.dogrula,
        kabin_ustu.ciz,
        "KABİN ÜSTÜ PLANI  ( kabin tavanı hizasından yatay kesit )",
    ),
    "kuyu_dibi": (kuyu_dibi.dogrula, kuyu_dibi.ciz, "KUYU DİBİ PLANI  ( kuyu tabanından yatay kesit )"),
    "kuyu_ustu": (
        kuyu_ustu.dogrula,
        kuyu_ustu.ciz,
        "KUYU ÜSTÜ PLANI  ( makine dairesiz — kuyu tepesinden yatay kesit )",
    ),
    "makine_dairesi": (makine_dairesi.dogrula, makine_dairesi.ciz, "MAKİNE DAİRESİ PLANI"),
    "delik_plani": (makine_dairesi.dogrula, makine_dairesi.delik_plani, "KUYU ÜSTÜ DÖŞEME HALAT DELİK PLANI"),
    "kuyu_kesiti_yan": (
        kuyu_kesiti.dogrula,
        kuyu_kesiti.yan_kesit,
        "A-A KUYU DÜŞEY KESİTİ  ( yan — kabin en alt durakta )",
    ),
    "kuyu_kesiti_on": (
        kuyu_kesiti.dogrula,
        kuyu_kesiti.on_kesit,
        "B-B KUYU DÜŞEY KESİTİ  ( arkadan kat kapılarına — kabin en üst durakta )",
    ),
    #  LiftDesigner paftalarındaki iki görünüş ( kullanıcı isteği 1 Eki )
    "kasnak_duzeni": (
        kasnak_duzeni.dogrula,
        kasnak_duzeni.ciz,
        "KASNAK DÜZENLEMESİ  ( tahrik kasnağının ekseninden — halatlar ve sarım açısı )",
    ),
    "giris": (giris.dogrula, giris.ciz, "GİRİŞ GÖRÜNÜŞÜ  ( en alt durağın kapısı, durak tarafından )"),
    #  LiftDesigner'ın "Front Entrance Side View"ü gibi ( 7 Eki )
    "kapi_kesiti": (
        kapi_kesiti.dogrula,
        kapi_kesiti.ciz,
        "KAPI YAN KESİTİ  ( en alt durağın kapısı, ortasından — kat tarafı solda )",
    ),
    #  Asansörün veri tablosu, kısaltmalar ve notlar ( 13 Eki — eskiden kuyu planında )
    "veriler": (veri_tablosu.dogrula, veri_tablosu.ciz, veri_tablosu.BASLIK),
}


#  Son adım:  aynı aralığın ikinci kimliksiz ölçüsü atılır ( geometri.tekrarlari_at ),
#  birbirine binen etiketler ayrılır ( geometri.etiketleri_ayir ), ondalık ayırıcı
#  virgül olur ( geometri.ondalik_virgul )
def _ayir(ciz, olcek=20):
    def ayrilmis(*a, **k):
        e = geometri.tekrarlari_at(ciz(*a, **k))
        return geometri.ondalik_virgul(geometri.etiketleri_ayir(e, olcek))

    ayrilmis.__name__ = ciz.__name__
    return ayrilmis


#  1/20 dışındaki çizimler
OLCEKLER = {"kuyu_kesiti_yan": kuyu_kesiti.OLCEK, "kuyu_kesiti_on": kuyu_kesiti.OLCEK}
#  Başlığında ölçek yazmayanlar ( tablo — yazıları 1/20'deki boyda )
OLCEKSIZ = {"veriler"}
CIZIMLER = {
    ad: (dog, _ayir(ciz, OLCEKLER.get(ad, 20)), baslik) for ad, (dog, ciz, baslik) in CIZIMLER.items()
}


def _kesit_sorunlu(g):
    """Düşey kesitlerin sorunu var mı.  Sorunlu kipte ( yalnız ekran —
    cizim/sorunlu.py ) kesitlerin yerleşimi kurulamazsa da "var":  harf
    yazılmaz, plan çizimi yine kurulur.  Eskiden kesitin hatası her planın
    başlığından taşıyor, ekranın bütün çizimleri kayboluyordu ( 20 Eki ).
    Kip kapalıyken hata bugünkü gibi yükselir."""
    if not sorunlu.acik():
        return kuyu_kesiti.dogrula(g)
    try:
        return kuyu_kesiti.dogrula(g)
    except Exception:  # noqa: BLE001 — kesit kendi çiziminde kurulamayan diye söylenir
        return True


def plan_basligi(g, cizim, baslik):
    """Plan başlığına düşey kesitlerdeki seviye harfi:  "KUYU PLANI  C-C  ( … )".
    Düşey kesitler çizilemeyen düzende harf de yazılmaz."""
    harf = kuyu_kesiti.PLAN_HARFLERI.get(cizim)
    #  Makine dairesiz projede makine dairesi ve delik planının, makine daireli
    #  projede kuyu üstü planının kesitlerde seviyesi yok
    oda = (g.get("makine") or {}).get("yeri") == "Makine dairesi"
    gecerli = (
        oda if cizim in ("makine_dairesi", "delik_plani") else (not oda if cizim == "kuyu_ustu" else True)
    )
    if not harf or not gecerli or _kesit_sorunlu(g):
        return baslik
    ad, _, ek = baslik.partition("  (")
    return f"{ad}  {harf}-{harf}" + (f"  ({ek}" if ek else "")
