# -*- coding: utf-8 -*-
"""Programın kendi penceresini ( static/ortak.js  pencere ) testte yakalar.

15 Eki'ye kadar program tarayıcının alert / confirm pencerelerini açıyordu;
testler onları ``pg.on("dialog", ...)`` ile okuyup kapatıyordu.  Artık
sayfa içi bir <dialog id="pencere"> açılıyor.  Buradaki kanca onun
karşılığıdır:  pencere açılır açılmaz metni okunur, ``liste``ye eklenir ve
pencere "hayır" ile kapatılır ( confirm'in dismiss'i gibi ).
"""

_YAKALA = """(() => {
  const ac = HTMLDialogElement.prototype.showModal;
  HTMLDialogElement.prototype.showModal = function () {
    ac.call(this);
    if (this.id !== 'pencere') return;
    const metin = this.innerText;
    this.close();
    if (window.__pencereAcildi) window.__pencereAcildi(metin);
  };
})()"""


def pencere_dinle(pg, liste=None):
    """``pg`` sayfasında açılan her pencerenin metnini ``liste``ye ekler ve
    pencereyi kapatır.  Kanca her yüklemede yeniden kurulur;  sayfa zaten
    açıksa ona da hemen kurulur."""
    pg.expose_function("__pencereAcildi", lambda metin: liste.append(metin) if liste is not None else None)
    pg.add_init_script(_YAKALA)
    if pg.url not in ("", "about:blank"):
        pg.evaluate(_YAKALA)
