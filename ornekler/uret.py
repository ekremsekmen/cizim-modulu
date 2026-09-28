# -*- coding: utf-8 -*-
"""ÖRNEK TAM PROJELER — ELEport PROJE 5 · Elevator 3  ( gerçek, yayımlanmış bir proje )

İki çıktı üretir, ikisi de hesap + bütün çizimler tek paftada:

  ELEport PROJE 5 - Makine Dairesiz         ELEport'un kendisi ( dişlisiz, MRL )
  ELEport PROJE 5 - Makine Daireli Dişli    aynı asansör, makine kuyunun üstündeki
                                            odada ve dişli ( hesap_girdi.ASANSOR_MD;
                                            ELEport'ta yok — değişen girdiler ve
                                            kaynakları orada )

Hesap programı DEĞİŞTİRİLMEDEN, motoru çağrılarak hesaplar;  kapak ve hesap
paftaları hesap programının kendi dışa aktarımıyla TİP PROJE FORMATINA dizilir;
çizim modülü çizimleri son hesap sayfasının sağına ekler ( pafta.birlestir ).

    "…/AVAN HESAPLAMA PROGRAMI/.venv/bin/python" ornekler/uret.py

Her proje için bu klasöre ( git'e girmez ):  .dwg ( AutoCAD'in AUDIT'inden
geçirilip kaydedilir;  AutoCAD yoksa .dxf kalır ) ve .pdf ( paftanın görüntüsü;
rsvg-convert yoksa .svg kalır ).  Köprü ( cizim/kopru.py ) gelince girdiler iki
yerde ayrı yazılmayacak;  şimdilik ikisi de ELEport'tan elle.
"""
import copy, os, re, shutil, subprocess, sys, tempfile
HESAP = "/Users/ekremsekmen/mycodes/AVAN HESAPLAMA PROGRAMI"
CIZIM = "/Users/ekremsekmen/mycodes/cizim-modulu"
CIKTI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HESAP); sys.path.insert(0, CIZIM); sys.path.insert(0, CIKTI)
ACC = ("/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/Helpers/"
       "AcCoreConsole.app/Contents/MacOS/AcCoreConsole")

from hesap_girdi import ASANSOR, ORTAK, ASANSOR_MD, ORTAK_MD
from engine.uygulama import hesap as E_UYG
from exports import pdf_export as X_PDF, dxf_export as X_DXF, kapak_export as X_KAPAK
from cizim import girdi as CG, pafta as CPF, kuyu_kesiti as CKK


def _en_buyuk(a, kimlik, sembol):
    b = next(b for b in a["bolumler"] if b.get("kimlik") == kimlik)
    d = [abs(x["deger"]) for x in b["adimlar"]
         if str(x.get("formul") or "").startswith(sembol + " =") and isinstance(x.get("deger"), (int, float))]
    assert d, (kimlik, sembol)
    return max(d)


def _dwg(dxf, dwg):
    """AutoCAD'in çekirdeğiyle açar, AUDIT eder, DWG kaydeder;  denetimin satırını döner."""
    with tempfile.TemporaryDirectory() as t:
        src, hedef, scr = (os.path.join(t, a) for a in ("p.dxf", "p.dwg", "k.scr"))
        shutil.copy(dxf, src)
        open(scr, "w").write(f"REGENALL\nZOOM\nE\nAUDIT\nN\nSAVEAS\n2018\n{hedef}\nQUIT\nY\n")
        try:
            cikti = subprocess.run([ACC, "-i", src, "-s", scr, "-l", "en-US"], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, timeout=240).stdout
        except subprocess.TimeoutExpired as z:          # QUIT'te kalırsa:  DWG çoktan yazıldı
            cikti = z.output or b""
        denetim = re.findall(r"Total errors found \d+ fixed \d+", cikti.replace(b"\x00", b"").decode("utf-8", "ignore"))
        if not os.path.exists(hedef):
            return None
        shutil.move(hedef, dwg)
        return denetim[-1] if denetim else "AUDIT satırı okunamadı"


def uret(md):
    ad = "ELEport PROJE 5 - Makine Daireli Dişli" if md else "ELEport PROJE 5 - Makine Dairesiz"
    ort = ORTAK_MD if md else ORTAK
    #  ── HESAP ─────────────────────────────────────────────────────────
    A = dict(ASANSOR_MD if md else ASANSOR, siginma_tipi_dip="Yatarak")
    s = E_UYG.hesapla_coklu([A], dict(ort))
    assert s.get("aktif"), s.get("hata")
    kapak = {
        "project_title": "ASANSÖR UYGULAMA PROJESİ",
        #  BLOK:  bina bloğu — ELEport projesinde yok, boş
        "capacity": "800 KG ( 10 KİŞİ )", "speed": "1,60 m/sn", "stops": "11 DURAK",
        "travel": "29000", "cabin_width": "1350", "cabin_depth": "1400",
        "standard": "TS EN 81-20", "elevator_class": "Sınıf I", "suspension": "2:1",
        "elevator_count": "1", "drive_type": "Elektrikli", "rail_size": "89*62 / 70*65",
        "motor_power": f"{A['motor_gucu']:g} KW".replace(".", ","), "scale": "1/20 1/50",
    }
    kapak_pdf = X_KAPAK.pdf_bytes(kapak)
    hesap_pdf = X_PDF.uygulama_pdf(s)
    hesap_dxf = X_DXF.proje_dxf([("Kapak", kapak_pdf), ("Uygulama Projesi", hesap_pdf)])

    #  ── ÇİZİM GİRDİSİ:  ELEport'un gerçek ölçüleri ─────────────────────
    g = copy.deepcopy(CG.ORNEK)
    g["proje"] = {"ad": "PROJE 5", "asansor": "Elevator 3", "olcek": 20}
    g["dusey"].update({
        "kabin_paten_arasi": A["kabin_paten_arasi"],
        "agirlik_paten_arasi": A["agirlik_paten_arasi"],
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
    #  Binaya gelen yükler ( N ):  kuyu tabanı hesabın 9. bölümünden;  ray
    #  konsoluna gelen yatay kuvvetler 7. ve 8. bölümlerin bütün yük durumlarındaki
    #  paten kuvvetlerinin en büyüğü.  Tampon adetleri iki girdide aynı olmalı ki
    #  "her tampona düşen" doğru bölünsün.
    a = s["asansorler"][0]
    g["kuyu_dibi"]["kuvvetler"] = dict(
        {k: a["ozet"][k] for k in ("FKR", "FAR", "Fkt", "Fat")},
        Fx_kabin=_en_buyuk(a, "kabin_raylari", "Fx"), Fy_kabin=_en_buyuk(a, "kabin_raylari", "Fy"),
        Fx_agirlik=_en_buyuk(a, "agirlik_raylari", "Fx"), Fy_agirlik=_en_buyuk(a, "agirlik_raylari", "Fy"))
    for k in ("kabin_tampon_adedi", "agirlik_tampon_adedi"):
        assert int(A.get(k) or 1) == g["kuyu_dibi"][k], (k, A.get(k), g["kuyu_dibi"][k])
    g["kabin_ustu"]["siginma_tipi"] = "Çömelme"
    #  Makine ve oturduğu kirişler hesabın girdileriyle AYNI:  tip, yer, tahrik
    #  kasnağı, yan yatak;  makine dairesinde tabliye ( oda döşemesi ), kaide ve oda
    #  ölçüleri.  Kuyu üstünde kirişler karşı ağırlık raylarına oturur:  mesnet
    #  aralığı ( hesabın L'si ) raylar arasıdır.
    g["makine"].update(tip=A["makine_tipi"], yeri="Kuyu üstü" if ort["mk_yok"] else "Makine dairesi",
                       tahrik_kasnak_capi=A["tahrik_kasnak_capi"], yan_yatak=A["yan_yatak"])
    if ort["mk_yok"]:
        assert A["yan_yatak_boyu"] == g["agirlik"]["ray_arasi"], (A["yan_yatak_boyu"], g["agirlik"]["ray_arasi"])
    else:
        g["makine_dairesi"].update({k: A[k] for k in ("tabliye_yuksekligi", "sase_yuksekligi", "dikine_kiris",
                                                       "yan_yatak_boyu")},
                                   genislik=ort["mk_genislik"], derinlik=ort["mk_uzunluk"])
    h = CKK.dogrula(g)
    assert not h, h
    #  Sarım açısı:  çizimin halat geometrisi hesabın beyan ettiği α'yı vermeli
    sarim = CKK.yerlesim(g)["M"].get("sarim_acisi", 180.0)
    assert abs(sarim - A["sarilma_acisi"]) < 0.5, (sarim, A["sarilma_acisi"])

    #  ── PAFTA ─────────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as t:
        yol_hesap = os.path.join(t, "hesap.dxf")
        open(yol_hesap, "wb").write(hesap_dxf)
        d, bilgi = CPF.birlestir(yol_hesap, g)
        dxf, svg = os.path.join(t, "pafta.dxf"), os.path.join(t, "pafta.svg")
        d.saveas(dxf)
        open(svg, "w", encoding="utf-8").write(CPF.onizleme(d))
        yol = os.path.join(CIKTI, ad)
        denetim = _dwg(dxf, yol + ".dwg") if os.path.exists(ACC) else None
        if denetim is None:
            shutil.copy(dxf, yol + ".dxf")
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", yol + ".pdf", svg], check=True)
        else:
            shutil.copy(svg, yol + ".svg")

    print(f"── {ad}")
    print("   binaya gelen yükler ( N ):", {k: round(v) for k, v in g["kuyu_dibi"]["kuvvetler"].items()})
    print("   AutoCAD:", denetim or "yok — .dxf bırakıldı")
    for c in bilgi["cizimler"]:
        x0, y0, x1, y1 = c["kutu"]
        print(f"   1/{c['olcek']:<3g} {x1-x0:6.1f} × {y1-y0:5.1f}  {c['baslik']}")
    for b in a["bolumler"]:
        print("     ", b["baslik"][:58], (b.get("sonuc") or {}).get("uygun"))


if __name__ == "__main__":
    for md in (False, True):
        uret(md)
