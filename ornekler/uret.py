# -*- coding: utf-8 -*-
"""ÖRNEK TAM PROJELER — yayımlanmış gerçek bir referans projenin girdileriyle

İki çıktı üretir, ikisi de hesap + bütün çizimler tek paftada:

  ÖRNEK PROJE - Makine Dairesiz             referans projenin kendisi ( dişlisiz, MRL )
  ÖRNEK PROJE - Makine Daireli Dişli        aynı asansör, makine kuyunun üstündeki
                                            odada ve dişli ( hesap_girdi.ASANSOR_MD;
                                            referans projede yok — değişen girdiler ve
                                            kaynakları orada )

PROGRAMIN KENDİ YOLUNDAN geçer:  girdi formun girdisidir ( hesap_girdi ), hesap
ve çizim girdisi "Projeyi paketle" düğmesinin kullandığı fonksiyonlarla kurulur
( hesap/api/uygulama · hesap/api/cizim · cizim/kopru ).  Kapak ve hesap paftaları
hesap programının dışa aktarımıyla TİP PROJE FORMATINA dizilir;  çizimler son
hesap sayfasının sağına eklenir ( pafta.birlestir ).

    .venv/bin/python ornekler/uret.py

Her proje için bu klasöre ( git'e girmez ):  .dwg ( AutoCAD'in AUDIT'inden
geçirilip kaydedilir;  AutoCAD yoksa .dxf kalır ) ve .pdf ( paftanın PDF'i —
ciktilar/pafta_pdf:  "Projeyi paketle"nin verdiğinin aynısı;  hesap sayfaları
ve çizimler vektörel, yazılar aranır ).
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KOK)
import yollar

yollar.kur()
ACC = (
    "/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/Helpers/"
    "AcCoreConsole.app/Contents/MacOS/AcCoreConsole"
)

from hesap_girdi import ASANSOR, ORTAK, ASANSOR_MD, ORTAK_MD, SABITLER
from uclar import cizim_uclari
from motor.uygulama import uygulama_hesabi
from ciktilar import pdf_cikti, dxf_cikti, kapak_cikti, pafta_pdf
from cizim import pafta
from cizim import kopru
from uclar import uygulama_istegi


def _dwg(dxf, dwg):
    """AutoCAD'in çekirdeğiyle açar, AUDIT eder, DWG kaydeder;  denetimin satırını döner."""
    with tempfile.TemporaryDirectory() as t:
        src, hedef, scr = (os.path.join(t, a) for a in ("p.dxf", "p.dwg", "k.scr"))
        shutil.copy(dxf, src)
        Path(scr).write_text(
            f"REGENALL\nZOOM\nE\nAUDIT\nN\nSAVEAS\n2018\n{hedef}\nQUIT\nY\n", encoding="utf-8"
        )
        try:
            cikti = subprocess.run(
                [ACC, "-i", src, "-s", scr, "-l", "en-US"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=240,
            ).stdout
        except subprocess.TimeoutExpired as z:  # QUIT'te kalırsa:  DWG çoktan yazıldı
            cikti = z.output or b""
        denetim = re.findall(
            r"Total errors found \d+ fixed \d+", cikti.replace(b"\x00", b"").decode("utf-8", "ignore")
        )
        if not os.path.exists(hedef):
            return None
        shutil.move(hedef, dwg)
        return denetim[-1] if denetim else "AUDIT satırı okunamadı"


def uret(md):
    ad = "ÖRNEK PROJE - Makine Daireli Dişli" if md else "ÖRNEK PROJE - Makine Dairesiz"
    #  ── HESAP:  formun isteğiyle ( proje geneli ayrı, ofis standardı ayrı ) ──
    veri = {
        "asansorler": [dict(ASANSOR_MD if md else ASANSOR, siginma_tipi_dip="Yatarak")],
        "proje_geneli": dict(ORTAK_MD if md else ORTAK),
        "sabitler": dict(SABITLER),
    }
    asansorler, ortak = uygulama_istegi.asansor_girdileri(veri)
    s = uygulama_hesabi.hesapla_coklu(asansorler, ortak)
    assert s.get("aktif"), s.get("hata")
    A = asansorler[0]
    kapak = {
        "project_title": "ASANSÖR UYGULAMA PROJESİ",
        #  BLOK:  bina bloğu — referans proje projesinde yok, boş
        "capacity": "800 KG ( 10 KİŞİ )",
        "speed": "1,60 m/sn",
        "stops": "11 DURAK",
        "travel": "29000",
        "cabin_width": "1350",
        "cabin_depth": "1400",
        "standard": "TS EN 81-20",
        "elevator_class": "Sınıf I",
        "suspension": "2:1",
        "elevator_count": "1",
        "drive_type": "Elektrikli",
        "rail_size": "89*62 / 70*65",
        "motor_power": f"{A['motor_gucu']:g} KW".replace(".", ","),
        "scale": "1/20 1/50",
    }
    kapak_pdf = kapak_cikti.pdf_baytlari(kapak)
    hesap_pdf = pdf_cikti.uygulama_pdf(s)
    hesap_dxf = dxf_cikti.proje_dxf([("Kapak", kapak_pdf), ("Uygulama Projesi", hesap_pdf)])

    #  ── ÇİZİM GİRDİSİ:  köprüden ( "Projeyi paketle" ile aynı ) ─────────
    #  Hesabın girdisi + çizim alanları;  binaya gelen yükler hesabın
    #  sonucundan;  hesapla çizimin tutarlılığı ( sarılma açısı, kasnaklar,
    #  kiriş aralığı, kuyu dibi zinciri ) orada denetlenir.
    ((g, hata),) = cizim_uclari.girdiler(veri, asansorler, ortak, s, "ÖRNEK PROJE")
    assert not hata, hata
    a = s["asansorler"][0]
    print(f"── {ad}")
    print(
        "   çizimden gelen hesap girdileri:",
        {k: a["girdi"][k] for k in kopru.CIZIMDEN if veri["asansorler"][0].get(k) is None},
    )
    #  Yerleşimin ölçüleri ( cizim/olculer ):  hesabın eskiden tahmin ettiği geometri
    print(
        "   yerleşimden ölçülenler:",
        {
            k: a["girdi"][k]
            for k in (a["girdi"].get("_cizimden") or {})
            if a["girdi"]["_cizimden"][k] == "yerleşim"
        },
    )

    #  ── PAFTA ─────────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as t:
        yol_hesap = os.path.join(t, "hesap.dxf")
        Path(yol_hesap).write_bytes(hesap_dxf)
        d, bilgi = pafta.birlestir(yol_hesap, g)
        dxf = os.path.join(t, "pafta.dxf")
        d.saveas(dxf)
        yol = os.path.join(CIKTI, ad)
        denetim = _dwg(dxf, yol + ".dwg") if os.path.exists(ACC) else None
        if denetim is None:
            shutil.copy(dxf, yol + ".dxf")
        paftalar = [("Kapak", kapak_pdf), ("Uygulama Projesi", hesap_pdf)]
        Path(yol + ".pdf").write_bytes(pafta_pdf.serit(Path(dxf).read_bytes(), paftalar, pafta.bloklar(g)))

    print("   binaya gelen yükler ( N ):", {k: round(v) for k, v in g["kuyu_dibi"]["kuvvetler"].items()})
    print("   AutoCAD:", denetim or "yok — .dxf bırakıldı")
    for c in bilgi["cizimler"]:
        x0, y0, x1, y1 = c["kutu"]
        print(f"   1/{c['olcek']:<3g} {x1 - x0:6.1f} × {y1 - y0:5.1f}  {c['baslik']}")
    for b in a["bolumler"]:
        print("     ", b["baslik"][:58], (b.get("sonuc") or {}).get("uygun"))


if __name__ == "__main__":
    for md in (False, True):
        uret(md)
