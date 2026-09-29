# -*- coding: utf-8 -*-
"""
ÇİZİM UÇLARI  —  hesap programı ile çizim modülünün bağlantısı

Uygulama projesinin girdisi TEK YERDEN gelir:  ekrandaki form.  Hesap o
girdiyle yapılır;  çizim modülü aynı girdiden ( ve hesabın sonucundan )
cizim/kopru.py ile kendi girdisini kurar.  Hesapta olan bir ölçü çizimde
ikinci kez sorulmaz;  hesabın bilmediği ölçüler ( kuyu derinliği, durak
adedi, kabinin ve kapının kuyudaki yeri … ) formun "Çizim" grubundadır.

Çizim modülü bu klasörün bir üstündedir ( cizim/ ).
"""
import os
import sys
import tempfile

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

_KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _KOK not in sys.path:
    #  SONA eklenir:  hesap programının kendi paketleri ( engine · api ·
    #  testler ) önce bulunmalı — çizim modülünün de testler/ klasörü var.
    sys.path.append(_KOK)

from cizim import cizimler as CZ           # noqa: E402
from cizim import geometri as CGE          # noqa: E402
from cizim import kopru as CK              # noqa: E402
from cizim import pafta as CPF             # noqa: E402
from cizim import svg as CSV               # noqa: E402

router = APIRouter()


def girdiler(veri, asansorler, ortak, sonuc, proje_adi):
    """Her asansörün çizim girdisi:  [ ( g , hatalar ) ].

    Girdi hesap motorunun kurduğu gibi kurulur ( engine/uygulama/hesap.hesapla:
    varsayılanlar + girilenler, sonra tamamlama ):  çizim hesabın kullandığı
    sayıyı görür."""
    from engine.uygulama import girdi as E_UGR
    pg = {k: ortak[k] for k in ortak if k != "_ofis"}
    liste = []
    for i, a in enumerate(asansorler):
        A = E_UGR.tamamla({**E_UGR.varsayilanlar(), **ortak, **a, **pg})
        s = sonuc["asansorler"][i] if sonuc and i < len(sonuc.get("asansorler") or []) else None
        g, hata = CK.cizim_girdisi(A, s, proje_adi, i + 1)
        if g is not None:
            hata = [f"{CZ.CIZIMLER[ad][2].split('  (')[0]}:  {h}"
                    for ad in CPF.sira(g) for h in CZ.CIZIMLER[ad][0](g)]
            #  Aynı hata birçok çizimde tekrarlanır ( hepsi kuyu planının
            #  doğrulamasından geçer );  bir kez söylenir.
            gorulen, tek = set(), []
            for h in hata:
                metin = h.split(":  ", 1)[-1]
                if metin not in gorulen:
                    gorulen.add(metin)
                    tek.append(metin)
            hata = tek or CK.tutarlilik(g, A)
        liste.append((g if not hata else None, hata))
    return liste


def _svg(g, ad):
    _dogrula, ciz, baslik = CZ.CIZIMLER[ad]
    olcek = CZ.OLCEKLER.get(ad, 20)
    baslik = CZ.plan_basligi(g, ad, baslik)
    seritler = (f"{g['proje']['ad']}  ·  {g['proje']['asansor']}" if g["proje"]["ad"]
                else g["proje"]["asansor"],)
    e = CGE.cerceveli(ciz(g), baslik, olcek, seritler=seritler)
    return {"ad": ad, "baslik": baslik, "olcek": olcek,
            "svg": CSV.yaz(e, CGE.sinir(e, 120 * olcek / 20.0), "", olcek)}


@router.post("/api/uygulama/cizimler")
def api_cizimler(veri: dict = Body(...)):
    """Aktif asansörün çizimleri ( SVG ) — ekrandaki önizleme için.

    Asıl çıktı "Projeyi paketle" ile inen paftadır ( DXF / DWG );  SVG aynı
    eleman listesinden çıkar ( cizim/svg.py · cizim/dxf.py )."""
    from api import uygulama as UYG
    from api.ortak import _belirsiz_hata, _proje_kimligi
    from engine.uygulama import hesap as E_UYG
    try:
        asansorler, ortak = UYG._asansor_girdileri(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"aktif": False, "hata": [belirsiz]})
        try:
            i = int(veri.get("asansor") or 0)
        except (TypeError, ValueError):
            i = 0
        i = min(max(i, 0), len(asansorler) - 1)
        s = E_UYG.hesapla_coklu(asansorler, ortak)
        g, hata = girdiler(veri, asansorler, ortak, s if s.get("aktif") else None,
                           _proje_kimligi(veri)["proje_adi"])[i]
        if hata:
            return JSONResponse({"aktif": False, "hata": hata})
        return JSONResponse({"aktif": True, "hesap": bool(s.get("aktif")),
                             "cizimler": [_svg(g, ad) for ad in CPF.sira(g)]})
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"aktif": False, "hata": [f"ÇİZİM HATASI: {e}"]})


def paftaya_ekle(gler):
    """Pakete girecek DXF'e çizimleri ekleyen son işlem ( dxf_export ).
    Hesap sayfalarının sağından başlayarak asansörler sırayla dizilir."""
    def islem(dxf):
        with tempfile.TemporaryDirectory() as t:
            yol = os.path.join(t, "hesap.dxf")
            with open(yol, "wb") as f:
                f.write(dxf)
            d, _bilgi = CPF.birlestir(yol, gler)
            cikti = os.path.join(t, "pafta.dxf")
            d.saveas(cikti)
            with open(cikti, "rb") as f:
                return f.read()
    return islem
