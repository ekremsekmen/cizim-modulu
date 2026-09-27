# -*- coding: utf-8 -*-
"""TAM PROJE — ELEport PROJE 5 · Elevator 3  ( gerçek, yayımlanmış bir proje )

Hesap programı DEĞİŞTİRİLMEDEN, motoru çağrılarak hesaplar;  kapak ve hesap
paftaları hesap programının kendi dışa aktarımıyla TİP PROJE FORMATINA dizilir;
çizim modülü çizimleri son hesap sayfasının sağına ekler ( pafta.birlestir ).

    ../../.venv  yoksa hesap programının .venv'i ile:
    "…/AVAN HESAPLAMA PROGRAMI/.venv/bin/python" ornekler/tam_proje/uret.py

Çıktılar bu klasöre ( git'e girmez ):  Tam Proje .dxf / .dwg ( AutoCAD varsa ) /
pafta .pdf, önizleme .svg, Hesaplar .pdf.  Köprü ( cizim/kopru.py ) gelince
girdiler iki yerde ayrı yazılmayacak;  şimdilik ikisi de ELEport'tan elle.
"""
import copy, io, os, sys
HESAP = "/Users/ekremsekmen/mycodes/AVAN HESAPLAMA PROGRAMI"
CIZIM = "/Users/ekremsekmen/mycodes/cizim-modulu"
CIKTI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HESAP); sys.path.insert(0, CIZIM); sys.path.insert(0, CIKTI)
os.makedirs(CIKTI, exist_ok=True)

from hesap_girdi import ASANSOR, ORTAK
from engine.uygulama import hesap as E_UYG
from exports import pdf_export as X_PDF, dxf_export as X_DXF, kapak_export as X_KAPAK
from cizim import girdi as CG, pafta as CPF, kuyu_kesiti as CKK

#  ── HESAP ─────────────────────────────────────────────────────────────
A = dict(ASANSOR, siginma_tipi_dip="Yatarak")
s = E_UYG.hesapla_coklu([A], dict(ORTAK))
assert s.get("aktif"), s.get("hata")
KAPAK = {
    "project_title": "ASANSÖR UYGULAMA PROJESİ",
    #  BLOK:  bina bloğu — ELEport projesinde yok, boş
    "capacity": "800 KG ( 10 KİŞİ )", "speed": "1,60 m/sn", "stops": "11 DURAK",
    "travel": "29000", "cabin_width": "1350", "cabin_depth": "1400",
    "standard": "TS EN 81-20", "elevator_class": "Sınıf I", "suspension": "2:1",
    "elevator_count": "1", "drive_type": "Elektrikli", "rail_size": "89*62 / 70*65",
    "motor_power": "11,3 KW", "scale": "1/20 1/50",
}
kapak_pdf = X_KAPAK.pdf_bytes(KAPAK)
hesap_pdf = X_PDF.uygulama_pdf(s)
from pypdf import PdfReader, PdfWriter
w = PdfWriter()
for b in (kapak_pdf, hesap_pdf):
    for p in PdfReader(io.BytesIO(b)).pages:
        w.add_page(p)
with open(os.path.join(CIKTI, "ELEport PROJE 5 - Hesaplar.pdf"), "wb") as f:
    w.write(f)
hesap_dxf = X_DXF.proje_dxf([("Kapak", kapak_pdf), ("Uygulama Projesi", hesap_pdf)])
yol_hesap = os.path.join(CIKTI, "_hesap_yalniz.dxf")
open(yol_hesap, "wb").write(hesap_dxf)

#  ── ÇİZİM GİRDİSİ:  ELEport'un gerçek ölçüleri ─────────────────────────
g = copy.deepcopy(CG.ORNEK)
g["proje"] = {"ad": "PROJE 5", "asansor": "Elevator 3", "olcek": 20}
g["dusey"].update({
    "beyan_hizi": 1.6, "durak_adedi": 11, "kat_yuksekligi": 2900, "son_kat": 5000,
    #  OLEO LB 16 hidrolik tampon ( strok 203, serbest boy 618 ):  kaide
    #  1.500 − 618 − 96 − 480 = 306
    "kabin_tampon_baba": 306, "kabin_tampon_boyu": 618, "kabin_carpma_arasi": 96,
    "kabin_tampon_ezilme": 203,
    "agirlik_tampon_baba": 300, "agirlik_tampon_boyu": 618, "agirlik_carpma_arasi": 150,
    "agirlik_tampon_ezilme": 203,
    "kabin_konsol_arasi": 1500, "agirlik_konsol_arasi": 1500,
})
g["kuyu_dibi"].update({"siginma_tipi": "Yatarak", "regulator_kasnak_capi": 240})
g["kabin_ustu"]["siginma_tipi"] = "Çömelme"
h = CKK.dogrula(g)
assert not h, h
d, bilgi = CPF.birlestir(yol_hesap, g)
yol = os.path.join(CIKTI, "ELEport PROJE 5 - Tam Proje.dxf")
d.saveas(yol)
open(os.path.join(CIKTI, "ELEport PROJE 5 - Tam Proje (onizleme).svg"), "w", encoding="utf-8").write(CPF.onizleme(d))
os.remove(yol_hesap)
print("hesap sayfalarının sağı", round(bilgi["hesap_sagi"], 1), "· çerçeve sağı", round(bilgi["sag"], 1))
for c in bilgi["cizimler"]:
    x0, y0, x1, y1 = c["kutu"]
    print(f"  1/{c['olcek']:<3g} {x1-x0:6.1f} × {y1-y0:5.1f}  {c['baslik']}")
for a in s["asansorler"]:
    for b in a["bolumler"]:
        print("   ", b["baslik"][:58], (b.get("sonuc") or {}).get("uygun"))
