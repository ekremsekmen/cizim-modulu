"""MİMARİ DENETİMİ — programın modülleri arasındaki erişimlerin doğruluğu.

Bir modül başka bir modülden yalnız orada TANIMLI olanı alır ( fonksiyon,
sınıf, değişken );  o modülün kendi import ettiği bir modüle onun içinden
uzanmaz ( uygulama_hesabi.mukavemet_girdi yerine mukavemet_girdi import
edilir ).  Takma adlar kalkınca bu uzanmalar sessizce kırılırdı;  bu denetim
sözdizimi ağacından bulur ( testler/test_mimari.py ).
"""

import ast
import glob
import os

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOKLER = (KOK, os.path.join(KOK, "hesap"), os.path.join(KOK, "ornekler"))


def modul_dosyasi(noktali):
    yol = noktali.replace(".", os.sep)
    for k in KOKLER:
        for aday in (os.path.join(k, yol + ".py"), os.path.join(k, yol, "__init__.py")):
            if os.path.isfile(aday):
                return aday
    return None


def dosyalar():
    out = []
    for f in glob.glob(os.path.join(KOK, "**", "*.py"), recursive=True):
        g = os.path.relpath(f, KOK)
        if not g.startswith((".venv", "cikti")):
            out.append(g)
    return sorted(out)


_TANIM = {}


def tanimlar(dosya):
    """Modülün üst düzeyde TANIMLADIĞI adlar ( import ettikleri hariç ) ve
    import ettikleri ( ayrı ):  ( tanımlı, import edilen )."""
    if dosya not in _TANIM:
        with open(dosya, encoding="utf-8") as d:
            t = ast.parse(d.read())
        tanimli, importlu = set(), set()

        def gez(govde):
            for n in govde:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    tanimli.add(n.name)
                elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    hedefler = n.targets if isinstance(n, ast.Assign) else [n.target]
                    for h in hedefler:
                        for a in ast.walk(h):
                            if isinstance(a, ast.Name):
                                tanimli.add(a.id)
                elif isinstance(n, (ast.Import, ast.ImportFrom)):
                    for a in n.names:
                        importlu.add(a.asname or a.name.split(".")[0])
                elif isinstance(n, (ast.If, ast.Try, ast.With, ast.For)):
                    for alt in ("body", "orelse", "finalbody"):
                        gez(getattr(n, alt, []) or [])
                    for h in getattr(n, "handlers", []) or []:
                        gez(h.body)

        gez(t.body)
        _TANIM[dosya] = (tanimli, importlu)
    return _TANIM[dosya]


def ihlaller():
    """[ ( dosya, satır, ileti ) ] — olmayan ada ya da başka modülün importuna erişim."""
    out = []
    for f in dosyalar():
        with open(os.path.join(KOK, f), encoding="utf-8") as d:
            t = ast.parse(d.read())
        moduller = {}  # ad → modül dosyası ( bu dosyada modül bağlayan adlar )
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom) and n.module and not n.level:
                kaynak = modul_dosyasi(n.module)
                for a in n.names:
                    alt = modul_dosyasi(f"{n.module}.{a.name}")
                    if alt:
                        moduller[a.asname or a.name] = alt
                    elif kaynak and not kaynak.endswith("__init__.py"):
                        tanimli, importlu = tanimlar(kaynak)
                        if a.name not in tanimli:
                            neden = "o modülün importu" if a.name in importlu else "tanımlı değil"
                            out.append((f, n.lineno, f"from {n.module} import {a.name}:  {neden}"))
        for n in ast.walk(t):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in moduller:
                tanimli, importlu = tanimlar(moduller[n.value.id])
                if n.attr not in tanimli and not n.attr.startswith("__"):
                    neden = "o modülün importu" if n.attr in importlu else "tanımlı değil"
                    out.append((f, n.lineno, f"{n.value.id}.{n.attr}:  {neden}"))
    return out


def modul_adi(dosya):
    """hesap/motor/uygulama/mukavemet.py → motor.uygulama.mukavemet"""
    d = dosya[len("hesap/") :] if dosya.startswith("hesap/") else dosya
    return d[:-3].replace("/", ".").replace(".__init__", "")


#  Programın katmanları ( alttan üste );  bir katman yalnız altındakileri
#  import eder.  Paket adı → katman.
KATMANLAR = ("temel", "tasarim", "cizim", "motor", "ciktilar", "uclar")
#  Şema seçenek listelerini bu VERİ modüllerinden okur ( tablolar fiziksel
#  olarak üst katmanın paketinde durur;  kendileri şemayı ve üst katmanları
#  import etmez — test_mimari denetler ).
SEMANIN_VERILERI = frozenset(("motor.uygulama.mukavemet_tablolari", "motor.ortak.ofis", "cizim.girdi"))


def program_dosyalari():
    return [f for f in dosyalar() if modul_adi(f).split(".")[0] in KATMANLAR]


def bagimliliklar():
    """{ modül : { import ettiği program modülleri } } ve fonksiyon içi
    importlar [ ( dosya, satır, import ) ] — program katmanları için."""
    tum = {modul_adi(f) for f in program_dosyalari()}
    graf, fonksiyon_ici = {}, []
    for f in program_dosyalari():
        with open(os.path.join(KOK, f), encoding="utf-8") as d:
            t = ast.parse(d.read())
        hedefler = set()
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom) and n.module and not n.level:
                bulunan = {
                    f"{n.module}.{a.name}" if f"{n.module}.{a.name}" in tum else n.module for a in n.names
                }
            elif isinstance(n, ast.Import):
                bulunan = {a.name for a in n.names}
            else:
                continue
            bulunan &= tum
            hedefler |= bulunan
        for fn in ast.walk(t):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for n in ast.walk(fn):
                    if isinstance(n, (ast.Import, ast.ImportFrom)):
                        fonksiyon_ici.append((f, n.lineno, ast.unparse(n)))
        graf[modul_adi(f)] = hedefler - {modul_adi(f)}
    return graf, fonksiyon_ici


def donguler(graf):
    """Birbirine dolanmış modül grupları ( Tarjan ) — boş olmalı."""
    sira, alt, yigin, yiginda, gruplar, sayac = {}, {}, [], set(), [], [0]

    def gez(v):
        sira[v] = alt[v] = sayac[0]
        sayac[0] += 1
        yigin.append(v)
        yiginda.add(v)
        for w in graf.get(v, ()):
            if w not in sira:
                gez(w)
                alt[v] = min(alt[v], alt[w])
            elif w in yiginda:
                alt[v] = min(alt[v], sira[w])
        if alt[v] == sira[v]:
            grup = []
            while True:
                w = yigin.pop()
                yiginda.discard(w)
                grup.append(w)
                if w == v:
                    break
            if len(grup) > 1:
                gruplar.append(sorted(grup))

    for v in sorted(graf):
        if v not in sira:
            gez(v)
    return gruplar


def katman_ihlalleri(graf):
    """[ ( modül, import ettiği ) ] — üst katmana ya da kuralsız yana bağımlılık."""
    out = []
    for m, hedefler in graf.items():
        km = KATMANLAR.index(m.split(".")[0])
        for h in hedefler:
            kh = KATMANLAR.index(h.split(".")[0])
            if kh <= km:
                continue
            if m.startswith("tasarim.") and h in SEMANIN_VERILERI:
                continue
            out.append((m, h))
    #  Şemanın okuduğu veri modülleri, dolaylı yoldan bile şemaya bağlanmaz
    for v in SEMANIN_VERILERI:
        gorulen, yigin = set(), [v]
        while yigin:
            x = yigin.pop()
            for h in graf.get(x, ()):
                if h.startswith("tasarim."):
                    out.append((v, h))
                elif h not in gorulen:
                    gorulen.add(h)
                    yigin.append(h)
    return sorted(set(out))


def golgeler():
    """[ ( dosya, satır, ileti ) ] — modül adını gölgeleyen yerel ad:  dosyada
    import edilmiş bir modülün adı bir fonksiyonda değişken / parametre olunca
    o fonksiyonda modül görünmez olur;  `geometri = []` sonra
    `geometri.dogrula( … )` listeyi çağırır ve hata çoğu kez bir except'te
    sessizce yutulur ( 11 Eki:  hesap çizimden ölçü almadan sürdü — altın
    çıktı yakaladı )."""
    out = []
    for f in dosyalar():
        with open(os.path.join(KOK, f), encoding="utf-8") as d:
            t = ast.parse(d.read())
        moduller = set()
        for n in t.body:
            if isinstance(n, ast.ImportFrom) and n.module and not n.level:
                for a in n.names:
                    if modul_dosyasi(f"{n.module}.{a.name}"):
                        moduller.add(a.asname or a.name)
        if not moduller:
            continue
        for fn in ast.walk(t):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            argumanlar = fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs
            for a in argumanlar + [x for x in (fn.args.vararg, fn.args.kwarg) if x]:
                if a.arg in moduller:
                    out.append((f, fn.lineno, f"parametre {a.arg} modülü gölgeliyor"))
            for n in ast.walk(fn):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in moduller:
                    out.append((f, n.lineno, f"yerel ad {n.id} modülü gölgeliyor"))
    return sorted(set(out))


def _agac(dosya, _onbellek={}):  # noqa: B006 — bilerek paylaşılan önbellek
    if dosya not in _onbellek:
        with open(os.path.join(KOK, dosya), encoding="utf-8") as d:
            _onbellek[dosya] = ast.parse(d.read())
    return _onbellek[dosya]


def ascii_disi_adlar():
    """[ ( dosya, satır, ad ) ] — Türkçe harfli ad.  Adlar Türkçedir ama
    Türkçe harfsiz yazılır ( aski, boslugun ):  arama ve araçlar tek
    biçimi bulsun, "askı" ile "aski" iki ayrı ad olmasın."""
    out = []
    for f in dosyalar():
        for n in ast.walk(_agac(f)):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                adlar = [n.name]
            elif isinstance(n, ast.Name):
                adlar = [n.id]
            elif isinstance(n, ast.arg):
                adlar = [n.arg]
            elif isinstance(n, ast.Attribute):
                adlar = [n.attr]
            elif isinstance(n, ast.keyword) and n.arg:
                adlar = [n.arg]
            else:
                continue
            out += [(f, n.lineno, a) for a in adlar if not a.isascii()]
    return sorted(set(out))


def uzun_fonksiyonlar(sinir):
    """[ ( dosya, satır, ad, uzunluk ) ] — programın ( katmanlar ve araçlar )
    sinir satırdan uzun fonksiyonları;  yorumlar ve belge metni dahil."""
    out = []
    for f in dosyalar():
        if not (f in program_dosyalari() or f.startswith("araclar")):
            continue
        for n in ast.walk(_agac(f)):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                uzunluk = n.end_lineno - n.lineno + 1
                if uzunluk > sinir:
                    out.append((f, n.lineno, n.name, uzunluk))
    return sorted(out)


def ozel_erisimler():
    """[ ( dosya, satır, ileti ) ] — başka bir modülün özel ( alt çizgili ) adına
    erişim:  geometri.yazilari_yerlestir( … ).  Başka modülün kullandığı ad
    o modülün arayüzüdür, özel değildir;  alt çizgi "dışarıdan çağrılmaz"
    der ve değiştiren kişi çağıranları aramaz.  Testler hariç ( iç işleyişi
    sınayabilirler )."""
    out = []
    for f in dosyalar():
        if f.startswith("testler") or "/dogrulama/" in f:
            continue
        t = _agac(f)
        moduller = set()
        for n in t.body:
            if isinstance(n, ast.ImportFrom) and n.module and not n.level:
                for a in n.names:
                    if modul_dosyasi(f"{n.module}.{a.name}"):
                        moduller.add(a.asname or a.name)
        for n in ast.walk(t):
            if (
                isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id in moduller
                and n.attr.startswith("_")
                and not n.attr.startswith("__")
            ):
                out.append((f, n.lineno, f"{n.value.id}.{n.attr}"))
    return sorted(set(out))


#  Hatayı ERROR düzeyinde kaydeden çağrılar ( uc_ortak.hata_kaydi programın
#  hatasını ERROR yazar )
_ERROR_KAYDI = frozenset(("error", "exception", "critical", "hata_kaydi"))


def yutan_exceptler(kaynak):
    """[ satır ] — kaynağın genel except'leri ( except Exception / BaseException
    / çıplak ) içinden hatayı ERROR yazmadan, yeniden fırlatmadan ve noqa'sız
    ( sebebi yazılı ) karşılayanlar.  ruff'ın BLE001'i exc_info'lu HER kaydı
    yeterli sayar:  log.debug( … , exc_info=True ) ile yutulan programlama
    hatası ancak istisnaları izleyen ayrı bir araçla görülüyordu ( 21 Eki son
    denetimi ).  Bilinen sınır kendi türüyle yakalanır ( cizim/sorun.py
    BILINEN )."""
    satirlar = kaynak.splitlines()
    out = []
    for n in ast.walk(ast.parse(kaynak)):
        if not (isinstance(n, ast.ExceptHandler) and _genel_mi(n.type)):
            continue
        if "noqa: BLE001" in satirlar[n.lineno - 1]:
            continue
        if not any(_error_kaydi_mi(m) or isinstance(m, ast.Raise) for b in n.body for m in ast.walk(b)):
            out.append(n.lineno)
    return sorted(out)


def _genel_mi(tur):
    if tur is None:
        return True
    adlar = tur.elts if isinstance(tur, ast.Tuple) else [tur]
    return any(isinstance(a, ast.Name) and a.id in ("Exception", "BaseException") for a in adlar)


def _error_kaydi_mi(n):
    if not isinstance(n, ast.Call):
        return False
    f = n.func
    ad = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
    return ad in _ERROR_KAYDI


def yutan_genel_exceptler():
    """[ ( dosya, satır ) ] — programın ( katmanlar ) hatayı yutan genel
    except'leri ( yutan_exceptler )."""
    out = []
    for f in program_dosyalari():
        with open(os.path.join(KOK, f), encoding="utf-8") as d:
            out += [(f, s) for s in yutan_exceptler(d.read())]
    return sorted(out)


if __name__ == "__main__":
    for f, s, i in ihlaller() + golgeler() + ozel_erisimler():
        print(f"{f}:{s}:  {i}")
