# -*- coding: utf-8 -*-
"""PROGRAMIN BÜTÜN DENETİMLERİ — tek komut.

    .venv/bin/python kontrol.py            hızlı:  hesap ( arayüz hariç ) + çizim
                                           ( yavaş modüller hariç ) + çizimlerin
                                           altın çıktısı  ( ~3 dk )
    .venv/bin/python kontrol.py tam        hızlı + yavaş çizim modülleri ( ~12 dk )
    .venv/bin/python kontrol.py arayuz     arayüz testleri:  programı 8790'da
                                           açar, testleri koşar, kapatır ( ~20 dk )
    .venv/bin/python kontrol.py tarama     girdi taraması ( 378 düzen;  ~15 dk )

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

#  Hesap programının arayüz istemeyen testleri ( hesap/testler/calistir.py
#  numaraları ) ve arayüz testleri ( 8790'da açık program ister )
HESAP_TESTLERI = ["1", "2", "3", "4", "6", "7", "8", "9", "10", "11", "12", "14"]
ARAYUZ_TESTLERI = ["3", "5", "13", "6"]
ARAYUZ_PORTU = 8790


def _cizim_modulleri():
    return sorted(
        "testler." + os.path.basename(f)[:-3] for f in glob.glob(os.path.join(KOK, "testler", "test_*.py"))
    )


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
        [PY, os.path.join("testler", "calistir.py")] + numaralar,
        cwd=HESAP,
        ortam=ortam,
    )


def cizim(tam):
    """Hızlıda bir dakikayı aşan testler ( testler/yavas.py ile işaretli ) atlanır."""
    return _kos(
        f"çizim testleri{'' if tam else ' ( yavaşlar hariç )'}",
        [PY, "-m", "unittest"] + _cizim_modulleri(),
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
        "hizli": lambda: [hesap(HESAP_TESTLERI), cizim(False), node()],
        "tam": lambda: [hesap(HESAP_TESTLERI), cizim(True), node()],
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
