# -*- coding: utf-8 -*-
"""GÜVENLİ KOŞTURUCU — ağır bir işi bilgisayarı kilitlemeden koşturur.

17 Eki:  6 süreçli uç değer taraması belleği bitirdi, macOS'un ekran süreci
( WindowServer ) 40 sn yanıt veremedi ve bilgisayar çöktü.  Bu araç işi kendi
süreç grubunda, düşük öncelikle ( nice 10 ) başlatır ve yarım saniyede bir
bakar;  şunlardan biri olursa bütün grubu öldürür:

  -  sistemin boş bellek oranı ( kern.memorystatus_level — sıkıştırılmış ve
     takas belleğini de sayar ) --bos'un altına düştü ( varsayılan %%35 )
  -  işin süreçlerinin toplam RSS'i --bellek MB'ı aştı ( varsayılan 4000 )
  -  süre --sure saniyeyi aştı ( varsayılan 0:  sınırsız )

    .venv/bin/python -m araclar.guvenli -- .venv/bin/python kontrol.py tam
    .venv/bin/python -m araclar.guvenli --bellek 2000 --sure 600 -- python x.py

Çıkış kodu işin kodudur;  araç öldürdüyse 137 ve sebebini yazar.
"""

import argparse
import os
import signal
import subprocess
import sys
import time

ARALIK = 0.5


def bos_oran() -> int:
    """Sistemin boş bellek yüzdesi ( Activity Monitor'deki baskının tersi )."""
    try:
        return int(
            subprocess.run(
                ["sysctl", "-n", "kern.memorystatus_level"], capture_output=True, text=True, check=False
            ).stdout
        )
    except ValueError:
        return 100  # macOS dışı:  bu denetim yok


def grup_rss_mb(pgid: int) -> float:
    """Süreç grubundaki bütün süreçlerin RSS toplamı ( MB )."""
    cikti = subprocess.run(["ps", "-axo", "pgid=,rss="], capture_output=True, text=True, check=False).stdout
    toplam = 0
    for satir in cikti.splitlines():
        p = satir.split()
        if len(p) == 2 and int(p[0]) == pgid:
            toplam += int(p[1])
    return toplam / 1024


def _oldur(is_: subprocess.Popen):
    for imza in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(is_.pid, imza)
        except (ProcessLookupError, PermissionError):  # macOS:  yalnız ölü önder kalmışsa EPERM
            return
        try:
            is_.wait(2)
        except subprocess.TimeoutExpired:
            pass


def kostur(komut, bellek_mb: float, bos_alt: int, sure: float) -> int:
    is_ = subprocess.Popen(komut, start_new_session=True, preexec_fn=lambda: os.nice(10))
    pgid = is_.pid
    t0 = time.monotonic()
    tepe = 0.0
    try:
        while is_.poll() is None:
            time.sleep(ARALIK)
            rss, bos = grup_rss_mb(pgid), bos_oran()
            tepe = max(tepe, rss)
            sebep = None
            if bos < bos_alt:
                sebep = f"sistemde boş bellek %{bos} ( alt sınır %{bos_alt} )"
            elif rss > bellek_mb:
                sebep = f"iş {rss:.0f} MB kullanıyor ( sınır {bellek_mb:.0f} MB )"
            elif sure and time.monotonic() - t0 > sure:
                sebep = f"süre {sure:.0f} sn'yi aştı"
            if sebep:
                print(f"\n[guvenli] DURDURULDU:  {sebep}", file=sys.stderr, flush=True)
                _oldur(is_)
                return 137
    except KeyboardInterrupt:
        _oldur(is_)
        return 130
    print(
        f"[guvenli] bitti:  {time.monotonic() - t0:.0f} sn, tepe {tepe:.0f} MB", file=sys.stderr, flush=True
    )
    return is_.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bellek", type=float, default=4000, help="işin toplam RSS sınırı, MB")
    ap.add_argument("--bos", type=int, default=35, help="sistemin boş bellek alt sınırı, %%")
    ap.add_argument("--sure", type=float, default=0, help="süre sınırı, sn ( 0:  yok )")
    ap.add_argument("komut", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    komut = a.komut[1:] if a.komut[:1] == ["--"] else a.komut
    if not komut:
        ap.error("komut yok")
    sys.exit(kostur(komut, a.bellek, a.bos, a.sure))


if __name__ == "__main__":
    main()
