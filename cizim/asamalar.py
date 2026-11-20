# -*- coding: utf-8 -*-
"""
UZUN İŞİN AŞAMALARI  —  ekran beklerken işin GERÇEKTEN hangi adımda olduğunu gösterir

17 Kas avan aramasında başladı ( kullanıcı:  "beklerken ne yapıldığını görelim" );  20 Kas
genellendi:  uygulama ve avan paketi, düzeltme önerisi ( yayın öncesi arayüz taslağı B1 · B2 ·
B5 ).  Süreye göre değişen hazır yazı ya da yüzde YOKTUR:  bütçeler sınama sayısıdır, iş çoğu
kez sınırdan çok önce biter — yüzde yanıltırdı.

İşi yapan kod bir adımın başında asama( kod ) der;  İLERLEME BAĞLAMI YOKSA ( testler, akışsız
istek ) HİÇBİR ŞEY OLMAZ:  bildirim işin sonucunu etkilemez.  Bağlamı uç kurar ( bagla —
uclar/uc_ortak.akisli_yanit ), iş parçacığında okunur;  metinler uç başına sözlüktür
{ kod:  ( sürerken , bitince ) }.

İPTAL:  Ilerleme( iptal ) — istek bırakıldıysa ( bağlantı kapandı ) bir sonraki asama() ya da
say() Birakildi fırlatır;  Python'da iş yarıda kesilemediği için iş en geç bir adım sonra durur.
Bu katmanda durur ki çizim ( pafta ) ve çıktılar da bildirebilsin ( katman kuralı — test_mimari ).
"""

import contextlib
import contextvars
import threading
import time


class Birakildi(BaseException):
    """İstek bırakıldı:  iş bir aşama sınırında durdu.  BaseException:  yol üstündeki genel
    except'ler ( uçların son savunması, PDF'siz paket yedeği ) onu hata sanıp yutmasın ya da
    kayda ERROR yazmasın — iptal bir hata değildir ( asyncio.CancelledError gibi )."""


class Ilerleme:
    """Bir işin aşamaları ve sınama sayısı.  İş parçacığında yazılır, uç başka yerden okur
    ( durum ) — kilitli.  plan:  adımları baştan belli işte ( paket ) sıradaki adımlar;  ekran
    başlamamış olanları soluk gösterir.  onek:  aşama metninin önüne ( avan paketi:  asansörün
    adı — "B · Kuyuya yerleşim deneniyor" ).  Alt işin ( doğrulama, askı ) içindeki aşamalar
    listeye eklenmez ( bastir ), sınamaları sayılır."""

    def __init__(self, metinler, plan=(), iptal=None):
        self.metinler = metinler
        self.iptal = iptal
        self.onek = ""
        self._kilit = threading.Lock()
        self._t0 = time.monotonic()
        self.plan = []
        self.asamalar = []
        self.sinama = 0
        self.bastir = 0
        self.surum = 0
        self.planla(plan)

    def planla(self, kodlar):
        with self._kilit:
            self.plan = [
                {"kod": k, "surer": self.metinler[k][0], "bitti": self.metinler[k][1]} for k in kodlar
            ]
            self.surum += 1

    def birakildi_mi(self):
        return self.iptal is not None and self.iptal()

    def asama(self, kod, ayrinti=""):
        with self._kilit:
            if self.bastir:
                return
            son = self.asamalar[-1] if self.asamalar else None
            if son and son["kod"] == kod and son["onek"] == self.onek:
                son["ayrinti"] = ayrinti
            else:
                surer, bitti = self.metinler[kod]
                self.asamalar.append(
                    {
                        "kod": kod,
                        "onek": self.onek,
                        "surer": self.onek + surer,
                        "bitti": self.onek + bitti,
                        "ayrinti": ayrinti,
                        "t": round(time.monotonic() - self._t0, 2),
                    }
                )
            self.surum += 1

    def ayrinti(self, metin, kod=None):
        """Süren aşamanın ayrıntısı ( yeni aşama açmaz );  kod verilirse yalnız o aşama sürerken."""
        with self._kilit:
            son = self.asamalar[-1] if self.asamalar else None
            if self.bastir or son is None or (kod is not None and son["kod"] != kod):
                return
            son["ayrinti"] = metin
            self.surum += 1

    def say(self):
        with self._kilit:
            self.sinama += 1
            self.surum += 1

    def durum(self):
        """( sürüm , { asamalar , sinama , gecen [ , plan ] } ) — sürüm değişmediyse yeni bir şey yok."""
        with self._kilit:
            d = {
                "asamalar": [{k: v for k, v in a.items() if k != "onek"} for a in self.asamalar],
                "sinama": self.sinama,
                "gecen": round(time.monotonic() - self._t0, 2),
            }
            if self.plan:
                d["plan"] = [dict(p) for p in self.plan]
            return self.surum, d


_ILERLEME = contextvars.ContextVar("asamalar_ilerleme", default=None)


@contextlib.contextmanager
def bagla(i):
    """Bu bağlamdaki işin aşamaları i'ye ( Ilerleme ) bildirilir."""
    token = _ILERLEME.set(i)
    try:
        yield i
    finally:
        _ILERLEME.reset(token)


@contextlib.contextmanager
def sessiz():
    """İçteki iş başka bir işin parçasıdır:  aşamaları ve sınamaları bildirilmez ( avan seçicisinin
    uyarlamada çağırdığı düzeltme araması — care_uclari.coz:  aşamaları seçicinin sözlüğünde yok,
    sınamaları seçicinin "yerleşim sınandı" sayısına girmemeli;  iptali seçicinin kendi koruması )."""
    token = _ILERLEME.set(None)
    try:
        yield
    finally:
        _ILERLEME.reset(token)


def _bagli():
    """Bağlamın ilerlemesi ( yoksa None );  istek bırakıldıysa Birakildi."""
    i = _ILERLEME.get()
    if i is not None and i.birakildi_mi():
        raise Birakildi()
    return i


def asama(kod, ayrinti=""):
    """İşin şimdiki aşaması ( metni bağlamın sözlüğünde ) — bağlam yoksa hiçbir şey yapmaz."""
    i = _bagli()
    if i is not None:
        i.asama(kod, ayrinti)


def ayrinti(metin, kod=None):
    """Süren aşamanın ayrıntısı ( "Asansör 2 / 4" ) — bağlam yoksa hiçbir şey yapmaz."""
    i = _ILERLEME.get()
    if i is not None:
        i.ayrinti(metin, kod)


def say():
    """Bir sınama daha ( hesap ve çizimin bir kurulumu ) — bağlam yoksa hiçbir şey yapmaz."""
    i = _bagli()
    if i is not None:
        i.say()


def planla(kodlar):
    """Adımları baştan belli olan işin sıradaki adımları ( işin girdisi okununca belli olur )."""
    i = _ILERLEME.get()
    if i is not None:
        i.planla(kodlar)


@contextlib.contextmanager
def alt_is(kod):
    """Alt işin aşaması:  içindeki işin aşamaları listeye girmez ( sınamaları sayılır )."""
    asama(kod)
    i = _ILERLEME.get()
    if i is None:
        yield
        return
    with i._kilit:
        i.bastir += 1
    try:
        yield
    finally:
        with i._kilit:
            i.bastir -= 1


@contextlib.contextmanager
def onekle(metin):
    """Bu bağlamda bildirilen aşamaların metni metin'le başlar ( avan paketi:  asansörün adı )."""
    i = _ILERLEME.get()
    if i is None:
        yield
        return
    eski, i.onek = i.onek, metin
    try:
        yield
    finally:
        i.onek = eski
