# -*- coding: utf-8 -*-
"""DÜZENLEME EŞDEĞERLİĞİ — bir düzenlemenin ( refactor ) davranışı değiştirmediğini
altın kayıtlardan GENİŞ bir girdi kümesinde gösterir.

İki kısım:

  cizim   Altın kayıt ( testler/altin_cizim.py ) 37 düzeni tam kilitler;  girdi
          taraması ( araclar.tarama ) 510 düzenin yalnız hükmünü tutar.  İkisinin
          bütün düzenlerinin paftası kurulur, her çizimin parmak izi ( elemanlar
          + SVG ) karşılaştırılır.
  hesap   Hesabın altın senaryoları ( dogrulama/altin_uret.py:  trafik · avan ·
          uygulama ) ve her birinin BOZULMUŞ kopyaları:  her alana sırayla
          eksik, boş, sıfır, negatif, aşırı, yazı ... değerler konur.  Altın
          kayıt geçerli yolları kilitler;  bu, hata dallarını da tarar.

    .venv/bin/python -m araclar.esdegerlik                 HEAD ile çalışma ağacı
    .venv/bin/python -m araclar.esdegerlik <commit>        o sürümle çalışma ağacı
    .venv/bin/python -m araclar.esdegerlik HEAD hesap      yalnız bir kısım

Karşılaştırılan sürüm cikti/esdegerlik/<commit> altına git worktree olarak
açılır;  parmak izleri cikti/esdegerlik/<commit>.<kısım>.json'da saklanır ( aynı
sürüm ikinci kez kurulmaz ).  Uzun sürer ( çizim:  iki sürüm × ~410 düzen,
~8 dk ):  yerelde, büyük bir düzenlemeden sonra koşulur.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import yollar

yollar.kur()

from araclar import tarama
from testler import altin_cizim
from dogrulama import altin_uret
from motor.avan import avan_hesabi
from motor.avan import trafik

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "cikti", "esdegerlik")
KISIMLAR = ("cizim", "hesap")

#  Hesap senaryolarının alanlarına sırayla konan değerler
BOZUK = (None, "", 0, -1, 0.5, 2, 7, 1e6, "x", True, "Var", "Yok")


def _iz(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


def parmak_izleri(kisim):
    return {"cizim": cizim_izleri, "hesap": hesap_izleri}[kisim]()


def cizim_izleri():
    """{ düzen adı:  { çizim adı:  sha256 } ya da { "hata": … } } — bu sürecin
    import ettiği kodla."""
    duzenler = dict(altin_cizim.duzenler())
    for grup in tarama.GRUPLAR:
        duzenler.update(tarama.duzenler(grup))
    izler = {}
    for ad, veri in duzenler.items():
        try:
            k = altin_cizim.pafta_kaydi(veri)
        except Exception as x:  # noqa: BLE001 — çöküş de bir sonuç
            izler[ad] = {"çöktü": f"{type(x).__name__}: {x}"}
            continue
        if "hata" in k:
            izler[ad] = {"hata": k["hata"]}
            continue
        izler[ad] = {c: _iz(v) for c, v in k["cizimler"].items()}
        izler[ad]["sira"] = k["sira"]
    return izler


def _alanlar(x, yol=()):
    """Senaryonun içindeki sözlüklerin yolları:  [ yol ] ( liste sırası dahil )."""
    if isinstance(x, dict):
        yield yol
        for k, v in x.items():
            yield from _alanlar(v, yol + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _alanlar(v, yol + (i,))


def _bul(x, yol):
    for k in yol:
        x = x[k]
    return x


def bozulmuslar(senaryolar):
    """Her senaryo ve bozulmuş kopyaları:  ( ad, girdi ).  Bir sözlüğün her
    alanına ( o türden senaryolarda görülen bütün anahtarlar ) BOZUK değerler;
    sayı alanlarına yarısı, iki katı ve bir fazlası da."""
    senaryolar = [json.loads(json.dumps(g)) for g in senaryolar]
    anahtarlar = {}
    for g in senaryolar:
        for yol in _alanlar(g):
            desen = tuple("*" if isinstance(k, int) else k for k in yol)
            anahtarlar.setdefault(desen, set()).update(_bul(g, yol))
    for i, g in enumerate(senaryolar):
        yield f"{i}", g
        for yol in _alanlar(g):
            desen = tuple("*" if isinstance(k, int) else k for k in yol)
            kap = _bul(g, yol)
            for k in sorted(anahtarlar[desen]):
                eski = kap.get(k)
                if isinstance(eski, (dict, list)):
                    continue
                degerler = list(BOZUK)
                if isinstance(eski, (int, float)) and not isinstance(eski, bool):
                    degerler += [eski / 2, eski * 2, eski + 1]
                for d in degerler:
                    kopya = json.loads(json.dumps(g))
                    _bul(kopya, yol)[k] = d
                    yield f"{i} {'/'.join(map(str, yol))}/{k}={d!r}", kopya


def hesap_izleri():
    """{ "motor senaryo [ bozma ]":  sha256 ( çıktı ya da çöküş ) }."""
    izler = {}
    for motor, fonk, senaryolar in (
        ("trafik", trafik.hesapla, altin_uret.senaryolar),
        ("avan", avan_hesabi.hesapla, altin_uret.avan_senaryolar),
        ("uygulama", altin_uret.uygulama_motoru, altin_uret.uygulama_senaryolar),
    ):
        for ad, g in bozulmuslar(senaryolar()):
            try:
                cikti = fonk(g)
            except Exception as x:  # noqa: BLE001 — çöküş de bir sonuç
                cikti = f"çöktü {type(x).__name__}: {x}"
            izler[f"{motor} {ad}"] = {"cikti": _iz(cikti)}
    return izler


def _surum(kaynak):
    return subprocess.run(
        ["git", "rev-parse", "--short", kaynak], cwd=KOK, capture_output=True, text=True, check=True
    ).stdout.strip()


def _yaz(izler, dosya):
    os.makedirs(os.path.dirname(dosya), exist_ok=True)
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(izler, f, ensure_ascii=False, sort_keys=True)


def referans(surum, kisim):
    """Sürümün parmak izleri ( kayıtlıysa kayıttan, yoksa worktree'de kurup )."""
    dosya = os.path.join(CIKTI, f"{surum}.{kisim}.json")
    if os.path.exists(dosya):
        with open(dosya, encoding="utf-8") as f:
            return json.load(f)
    agac = os.path.join(CIKTI, surum)
    if not os.path.isdir(agac):
        subprocess.run(["git", "worktree", "add", "--detach", agac, surum], cwd=KOK, check=True)
    try:
        #  Araç o sürümde olmayabilir:  bu kopyası ağaca konur, ağacın
        #  modülleriyle koşar
        shutil.copy(os.path.abspath(__file__), os.path.join(agac, "araclar", "esdegerlik.py"))
        subprocess.run(
            [sys.executable, "-m", "araclar.esdegerlik", "--yaz", kisim, dosya], cwd=agac, check=True
        )
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", agac], cwd=KOK, check=True)
    with open(dosya, encoding="utf-8") as f:
        return json.load(f)


def farklar(eski, yeni):
    """[ ileti ] — düzen düzen, çizim çizim."""
    out = []
    for ad in sorted(set(eski) | set(yeni)):
        a, b = eski.get(ad), yeni.get(ad)
        if a == b:
            continue
        if a is None or b is None:
            out.append(f"{ad}:  yalnız {'yeni' if a is None else 'eski'} sürümde")
            continue
        for c in sorted(set(a) | set(b)):
            if a.get(c) != b.get(c):
                out.append(f"{ad}:  {c}  {str(a.get(c))[:60]}  →  {str(b.get(c))[:60]}")
    return out


def main(argv):
    if argv[:1] == ["--yaz"]:  # worktree'deki alt süreç:  o sürümün izleri
        _yaz(parmak_izleri(argv[1]), argv[2])
        return 0
    kisimlar = [a for a in argv if a in KISIMLAR] or list(KISIMLAR)
    surum = _surum(next((a for a in argv if a not in KISIMLAR), "HEAD"))
    sonuc = 0
    for kisim in kisimlar:
        t = time.time()
        eski = referans(surum, kisim)
        print(f"  {kisim}  {surum}:  {len(eski)} girdi  ·  {time.time() - t:.0f} sn")
        t = time.time()
        yeni = parmak_izleri(kisim)
        print(f"  {kisim}  çalışma ağacı:  {len(yeni)} girdi  ·  {time.time() - t:.0f} sn")
        f = farklar(eski, yeni)
        for satir in f[:60]:
            print("  " + satir)
        print(f"{kisim}:  EŞDEĞER  ·  {len(yeni)} girdi" if not f else f"{kisim}:  FARKLI  ·  {len(f)} fark")
        sonuc = sonuc or (1 if f else 0)
    return sonuc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
