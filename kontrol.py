# -*- coding: utf-8 -*-
"""PROGRAMIN BÜTÜN DENETİMLERİ — tek komut.

    .venv/bin/python kontrol.py            hızlı:  lint + biçim, hesap ( arayüz
                                           hariç ), çizim ( yavaş test hariç,
                                           altın çıktı dahil ), node  ( ~3 dk )
    .venv/bin/python kontrol.py tam        hızlı + yavaş test ( ~9 dk — o tek test 7 dk )
    .venv/bin/python kontrol.py arayuz     arayüz testleri:  programı 8790'da
                                           açar, testleri koşar, kapatır ( ~20 dk )
    .venv/bin/python kontrol.py tarama     girdi taraması ( 510 düzen;  ~5 dk )
    .venv/bin/python kontrol.py bicim      ruff format + ruff check --fix ( düzeltir )

Çizim testleri pytest ile paralel koşar:  KONTROL_IS işçi ( varsayılan 4 —
bilgisayarın hepsini doldurmasın;  CI'da "auto" ).

Her değişiklikte en az hızlı denetim koşulur;  commit'ten önce tam + arayüz.
Adımlar SIRAYLA koşar ( ağır işler aynı anda koşturulmaz ).  Çıkış kodu:  bir
adım başarısızsa 1 — CI ( .github/workflows ) bunu okur.
"""

import glob
import os
import subprocess
import sys
import time
import urllib.request

KOK = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
HESAP = os.path.join(KOK, "hesap")

#  Hesap programının arayüz istemeyen testleri ( hesap/dogrulama/calistir.py
#  numaraları ) ve arayüz testleri ( 8790'da açık program ister )
HESAP_TESTLERI = ["1", "2", "3", "4", "6", "7", "8", "9", "10", "11", "12", "14"]
ARAYUZ_TESTLERI = ["3", "5", "13", "6"]
ARAYUZ_PORTU = 8790
#  Hızlı / tam denetimde hesabın HTTP bölümleri ( TEST 3 · 6 ) sunucu aramaz:
#  yoksa 8780'de o an açık olan programa ( kullanıcınınkine, belki eski koda )
#  bağlanıyor, sonuç makinede neyin açık olduğuna göre değişiyordu.  O
#  bölümler arayüz denetiminde kendi açtığı programa karşı koşar.
SUNUCUSUZ = {"AVAN_TEST_URL": "http://127.0.0.1:1"}


#  Çizim testlerinin işçi sayısı ( pytest-xdist )
IS = os.environ.get("KONTROL_IS", "4")


def _kos(ad, komut, cwd=KOK, ortam=None):
    print(f"\n━━ {ad}", flush=True)
    t = time.time()
    r = subprocess.run(komut, cwd=cwd, env=dict(os.environ, **(ortam or {})), check=False)
    print(
        f"━━ {ad}:  {'GEÇTİ' if r.returncode == 0 else 'BAŞARISIZ'}  ·  {time.time() - t:.0f} sn", flush=True
    )
    return r.returncode == 0


def hesap(numaralar, ortam=None):
    return _kos(
        "hesap testleri " + " ".join(numaralar),
        [PY, os.path.join("dogrulama", "calistir.py")] + numaralar,
        cwd=HESAP,
        ortam=ortam,
    )


def lint():
    """ruff:  hata kuralları ( pyproject.toml ) ve biçim."""
    return _kos("lint", [PY, "-m", "ruff", "check", "."]) and _kos(
        "biçim", [PY, "-m", "ruff", "format", "--check", "."]
    )


def bicim():
    return _kos("biçim ( düzeltir )", [PY, "-m", "ruff", "format", "."]) and _kos(
        "lint ( düzeltir )", [PY, "-m", "ruff", "check", "--fix", "."]
    )


def cizim(tam):
    """Hızlıda bir dakikayı aşan testler ( testler/yavas.py ile işaretli ) atlanır."""
    return _kos(
        f"çizim testleri{'' if tam else ' ( yavaşlar hariç )'}",
        [PY, "-m", "pytest", "-q", "-n", IS],
        ortam={"KONTROL_HIZLI": "0" if tam else "1"},
    )


def node():
    dosyalar = glob.glob(os.path.join(KOK, "testler", "*.test.cjs"))
    if not dosyalar:
        return True
    return _kos("arayüz yardımcıları ( node )", ["node", "--test"] + dosyalar)


def arayuz():
    """Programı test portunda açar ( kullanıcının açık programına dokunmaz ),
    arayüz testlerini koşar, programı kapatır."""
    sunucu = subprocess.Popen(
        [
            PY,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(ARAYUZ_PORTU),
            "--log-level",
            "warning",
        ],
        cwd=HESAP,
    )
    try:
        url = f"http://127.0.0.1:{ARAYUZ_PORTU}/api/saglik"
        for _ in range(60):
            try:
                with urllib.request.urlopen(url, timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        else:
            print("program açılamadı")
            return False
        return hesap(ARAYUZ_TESTLERI, {"AVAN_TEST_URL": f"http://127.0.0.1:{ARAYUZ_PORTU}"})
    finally:
        sunucu.terminate()
        sunucu.wait(timeout=30)


def tarama():
    """Hükümler depodaki kayıtla karşılaştırılır ( araclar/tarama.py )."""
    return _kos("girdi taraması", [PY, "-m", "araclar.tarama"])


def main(argv):
    kip = argv[0] if argv else "hizli"
    adimlar = {
        "hizli": lambda: [lint(), hesap(HESAP_TESTLERI, SUNUCUSUZ), cizim(False), node()],
        "tam": lambda: [lint(), hesap(HESAP_TESTLERI, SUNUCUSUZ), cizim(True), node()],
        "bicim": lambda: [bicim()],
        "arayuz": lambda: [arayuz()],
        "tarama": lambda: [tarama()],
    }
    if kip not in adimlar:
        print(__doc__)
        return 2
    t = time.time()
    sonuc = adimlar[kip]()
    print(
        f"\n{'HEPSİ GEÇTİ' if all(sonuc) else 'BAŞARISIZ ADIM VAR'}  ·  {kip}  ·  "
        f"{(time.time() - t) / 60:.1f} dk"
    )
    return 0 if all(sonuc) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
