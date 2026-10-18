"""ÖN YÜZÜ GEREKİRSE DERLER — başlatıcılar ( baslat.command · baslat.bat ) çağırır.

Program ön yüzü derlenmiş dosyalardan sunar ( on-yuz/dist;  depoda değil ).
Derleme yoksa ya da kaynak derlemeden yeniyse ( program güncellenmiş ) bir kez
derlenir;  güncelse hiçbir şey yapılmaz, bekletmez.  Bağımlılıklar yoksa ya da
kilit dosyası değişmişse önce kurulur ( npm ci ).  Node yoksa ne yapılacağı
söylenir;  program yine açılır ( kök adres derleme talimatını gösterir ).

    .venv/bin/python -m araclar.on_yuz_derle
"""

import os
import shutil
import subprocess
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ON_YUZ = os.path.join(KOK, "on-yuz")
GIRIS = os.path.join(ON_YUZ, "dist", "index.html")
KILIT = os.path.join(ON_YUZ, "package-lock.json")
KURULU = os.path.join(ON_YUZ, "node_modules", ".package-lock.json")

#  Derlemeyi etkileyen kaynaklar:  bunlardan biri derlemeden yeniyse derlenir
KAYNAKLAR = ("src", "index.html", "package.json", "package-lock.json", "vite.config.ts", "tsconfig.json")


def _en_yeni(yol):
    if os.path.isfile(yol):
        return os.path.getmtime(yol)
    zaman = 0.0
    for kok, _klasorler, dosyalar in os.walk(yol):
        for d in dosyalar:
            zaman = max(zaman, os.path.getmtime(os.path.join(kok, d)))
    return zaman


def derleme_gerekli():
    if not os.path.isfile(GIRIS):
        return True
    derleme = os.path.getmtime(GIRIS)
    return any(
        _en_yeni(os.path.join(ON_YUZ, k)) > derleme
        for k in KAYNAKLAR
        if os.path.exists(os.path.join(ON_YUZ, k))
    )


def kurulum_gerekli():
    #  npm ci node_modules/.package-lock.json yazar:  yoksa ya da kilitten eskiyse kurulum eski
    return not os.path.isfile(KURULU) or os.path.getmtime(KILIT) > os.path.getmtime(KURULU)


def main():
    if not derleme_gerekli():
        return 0
    npm = shutil.which("npm")
    if not npm:
        print("  Ön yüz derlenmemiş ve Node.js bulunamadı.")
        print("  https://nodejs.org adresinden Node.js 22 ( LTS ) kurup başlatıcıyı yeniden açın.")
        print("  Program yine açılıyor;  sayfa derleme talimatını gösterecek.\n")
        return 1
    if kurulum_gerekli():
        print("  Ön yüz bağımlılıkları kuruluyor ( yalnız güncellemeden sonra, ~1 dakika )…")
        if subprocess.run([npm, "ci", "--no-audit", "--no-fund"], cwd=ON_YUZ, check=False).returncode:
            print("  Kurulum yapılamadı — internet bağlantınızı kontrol edin.\n")
            return 1
    print("  Ön yüz derleniyor ( yalnız güncellemeden sonra, birkaç saniye )…")
    if subprocess.run([npm, "run", "build"], cwd=ON_YUZ, check=False).returncode:
        print("  Ön yüz derlenemedi.\n")
        return 1
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
