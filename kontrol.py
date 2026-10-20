# -*- coding: utf-8 -*-
"""PROGRAMIN BÜTÜN DENETİMLERİ — tek komut.

    .venv/bin/python kontrol.py            hızlı:  lint + biçim, hesap ( arayüz
                                           hariç ), çizim ( yavaş test hariç,
                                           altın çıktı dahil ), ön yüz ( tip,
                                           lint, test, derleme )  ( ~4 dk )
    .venv/bin/python kontrol.py tam        hızlı + yavaş test + sunucu + uçtan uca ( ~12 dk — yavaş test 7 dk )
    .venv/bin/python kontrol.py sunucu     programı 8790'da açar, uçlarını ve kök
                                           sayfayı dener ( TEST 3 ), kapatır ( ~1 dk )
    .venv/bin/python kontrol.py uctan_uca  ön yüz gerçek tarayıcıda:  örnek proje, canlı
                                           hesap, proje dosyası, ölçü, teslim ( ~1 dk )
    .venv/bin/python kontrol.py tarama     girdi taraması ( 510 düzen;  ~5 dk )
    .venv/bin/python kontrol.py bicim      ruff format + ruff check --fix ( düzeltir )

Çizim testleri pytest ile paralel koşar:  KONTROL_IS işçi ( varsayılan 4 —
bilgisayarın hepsini doldurmasın;  CI'da "auto" ).

Her değişiklikte en az hızlı denetim koşulur;  commit'ten önce tam.
Adımlar SIRAYLA koşar ( ağır işler aynı anda koşturulmaz ).  Çıkış kodu:  bir
adım başarısızsa 1 — CI ( .github/workflows ) bunu okur.
"""

import os
import shutil
import subprocess
import sys
import time
import urllib.request

KOK = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
HESAP = os.path.join(KOK, "hesap")
ON_YUZ = os.path.join(KOK, "on-yuz")

#  Hesap programının testleri ( hesap/dogrulama/calistir.py numaraları ) ve
#  açık program isteyen bölümleri ( 8790'da kendi açtığı program )
HESAP_TESTLERI = ["1", "2", "3", "4", "7", "8", "9", "10", "11", "12", "14"]
SUNUCU_TESTLERI = ["3"]
SUNUCU_PORTU = 8790
#  Hesap testlerinde HTTP bölümü ( TEST 3 ) sunucu aramaz:  yoksa 8780'de o an
#  açık olan programa ( kullanıcınınkine, belki eski koda ) bağlanıyor, sonuç
#  makinede neyin açık olduğuna göre değişiyordu.  O bölüm sunucu denetiminde
#  kendi açtığı programa karşı koşar.
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


def on_yuz():
    """Ön yüz ( on-yuz/, React ):  tip, lint, birim testleri ve derleme.  Derleme
    hesap/main.py'nin kökte sunduğu dist'i de tazeler.  Bağımlılıklar
    yoksa önce kilit dosyasından kurulur ( npm ci )."""
    npm = shutil.which("npm") or "npm"
    if not os.path.isdir(os.path.join(ON_YUZ, "node_modules")) and not _kos(
        "ön yüz bağımlılıkları ( npm ci )", [npm, "ci", "--no-audit", "--no-fund"], cwd=ON_YUZ
    ):
        return False
    return _kos("ön yüz ( tip, lint, test, derleme )", [npm, "run", "denetim"], cwd=ON_YUZ)


def sunucu():
    """Programı test portunda açar ( kullanıcının açık programına dokunmaz ),
    uçlarını ve kök sayfayı dener, programı kapatır.  Tam denetimde ön yüz
    derlendikten sonra koşar:  kök sayfa derlenmiş React'tir."""
    url = f"http://127.0.0.1:{SUNUCU_PORTU}/api/saglik"
    #  Port doluysa ( açık bir program ya da önizleme ) denenen o olurdu —
    #  belki eski kod.  Yanıltmasın:  açıkça söylenir.
    try:
        with urllib.request.urlopen(url, timeout=1):
            print(f"{SUNUCU_PORTU} portunda açık bir program var — kapatıp yeniden deneyin")
            return False
    except OSError:
        pass
    sunucu = subprocess.Popen(
        [
            PY,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(SUNUCU_PORTU),
            "--log-level",
            "warning",
        ],
        cwd=HESAP,
    )
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen(url, timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        else:
            print("program açılamadı")
            return False
        return hesap(SUNUCU_TESTLERI, {"AVAN_TEST_URL": f"http://127.0.0.1:{SUNUCU_PORTU}"})
    finally:
        sunucu.terminate()
        sunucu.wait(timeout=30)


def uctan_uca(derlendi=True):
    """Ön yüz gerçek tarayıcıda ( testler/test_on_yuz_uctan_uca.py ):  test kendi
    programını boş bir portta açar.  Derlenmiş ön yüzü dener — ön yüz
    derlendikten sonra koşar.  Derleme başarısızsa koşmaz:  dist'te kalan ESKİ
    derlemeyi dener ve yanıltıcı biçimde geçerdi."""
    if not derlendi:
        print("\n━━ ön yüz uçtan uca ( tarayıcı ):  ATLANDI — ön yüz derlenemedi", flush=True)
        return False
    return _kos(
        "ön yüz uçtan uca ( tarayıcı )",
        [PY, "-m", "pytest", "-q", "testler/test_on_yuz_uctan_uca.py"],
        ortam={"KONTROL_UCTAN_UCA": "1"},
    )


def tarama():
    """Hükümler depodaki kayıtla karşılaştırılır ( araclar/tarama.py )."""
    return _kos("girdi taraması", [PY, "-m", "araclar.tarama"])


def main(argv):
    kip = argv[0] if argv else "hizli"
    adimlar = {
        #  Ön yüz çizim testlerinden ÖNCE derlenir:  test_sunucu kök sayfayı
        #  ( on-yuz/dist ) ister;  temiz kopyada ( CI ) derleme yoksa 503 alırdı.
        "hizli": lambda: [lint(), hesap(HESAP_TESTLERI, SUNUCUSUZ), on_yuz(), cizim(False)],
        "tam": lambda: [
            lint(),
            hesap(HESAP_TESTLERI, SUNUCUSUZ),
            (derlendi := on_yuz()),
            cizim(True),
            sunucu(),
            uctan_uca(derlendi),
        ],
        "bicim": lambda: [bicim()],
        "sunucu": lambda: [sunucu()],
        "uctan_uca": lambda: [uctan_uca(on_yuz())],
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
