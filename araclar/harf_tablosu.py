"""HARF ENLERİ — cizim/harf_eni.py'yi yazı tipinin kendisinden üretir.

Çizimin yazı tipi Arial ( DXF );  ekranda Arial'le harf enleri birebir aynı
Liberation Sans gömülür ( cizim/yazi — OFL, değiştirilmeden ).
Yerleşim yazının enini buradaki tablodan hesaplar ( eskiden harf × 0,6 em:
gerçek Arial'den −%6 … +%20 sapıyordu;  "W" 0,94 em ).  Tablo yazı tipiyle
aynı mı:  testler/test_uslup.py.

    .venv/bin/python -m araclar.harf_tablosu      → cizim/harf_eni.py'yi yeniden yazar
"""

import os
import subprocess
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAZI_TIPI = os.path.join(KOK, "cizim", "yazi", "LiberationSans-Regular.ttf")  # uslup.YAZI_DOSYASI
HEDEF = os.path.join(KOK, "cizim", "harf_eni.py")
#  Tabloya girenler:  ASCII, Latin-1, Türkçe harfler ve çizimlerin işaretleri
KUME = (
    [chr(c) for c in range(32, 127)]
    + [chr(c) for c in range(160, 256)]
    + list("ĞğİıŞşŒœ–—‘’“”•…‰′″←↑→↓≈≠≤≥∅⌀√∞")
)


def enler():
    """{ harf : en ( em ) } — yazı tipinde olan harfler."""
    from fontTools.ttLib import TTFont

    f = TTFont(YAZI_TIPI)
    cmap, hmtx, em = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return {c: hmtx[cmap[ord(c)]][0] / em for c in KUME if ord(c) in cmap}


def yaz():
    en = enler()
    satirlar = "".join(f"    {c!r}: {v!r},\n" for c, v in en.items())
    with open(HEDEF, "w", encoding="utf-8") as f:
        f.write(
            '"""HARF ENLERİ ( em ) — araclar/harf_tablosu.py ÜRETİR, elle değiştirilmez.\n\n'
            "Liberation Sans 2.1.5 ( Arial'le harf enleri aynı );  kerning yok — AutoCAD\n"
            'de uygulamaz, ekran da uygulamaz ( svg:  font-kerning none )."""\n\n'
            f"EN = {{\n{satirlar}}}\n"
        )
    #  Deponun biçimiyle ( ruff format ) — biçim denetimi takılmasın
    subprocess.run([sys.executable, "-m", "ruff", "format", "-q", HEDEF], check=True)


if __name__ == "__main__":
    yaz()
