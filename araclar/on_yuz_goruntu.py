"""YENİ ÖN YÜZÜN EKRAN GÖRÜNTÜLERİ — her ekran, gerçek sunucuyla, 1440 × 900 ( 2x ).

Ekran ekran geçişte görsel denetim:  bir değişiklikten sonra bütün ekranlar
aynı durumlarla yeniden çekilir, gözle karşılaştırılır.  Program açık olmalı
( 8790 — .claude/launch.json "program" ) ve ön yüz derlenmiş ( /yeni ) ya da
geliştirme sunucusunda ( 5174/yeni ) olmalı.

    .venv/bin/python -m araclar.on_yuz_goruntu                 # bütün ekranlar
    .venv/bin/python -m araclar.on_yuz_goruntu olcu teslim     # adında geçenler
    ON_YUZ_URL=http://localhost:5174/yeni .venv/bin/python -m araclar.on_yuz_goruntu

Çıktı:  cikti/on-yuz-goruntuleri/ ( git'e girmez ).
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

KOK = os.environ.get("ON_YUZ_URL", "http://127.0.0.1:8790/yeni").rstrip("/")
CIKTI = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cikti", "on-yuz-goruntuleri"
)


def bekle(s, ms=900):
    s.wait_for_load_state("networkidle")
    time.sleep(ms / 1000)


def proje(s, degerler=None, sorgu="", ornek=False, ad=""):
    """Tarayıcı belleğine bir uygulama projesi yazar ve çalışma alanını açar."""
    s.goto(KOK + "/")
    pid = s.evaluate(
        """([d, o, a]) => {
            const id = Math.random().toString(36).slice(2, 10);
            const p = {id, tur: 'uygulama', ornek: o,
                       kimlik: {project_title: o ? 'Örnek proje' : a, owner: '', sheet_no: ''},
                       asansorler: [d || {}], proje_geneli: {}, guncellendi: Date.now()};
            localStorage.setItem('asansor:proje:' + id, JSON.stringify(p));
            const l = JSON.parse(localStorage.getItem('asansor:projeler') || '[]');
            l.push({id, tur: 'uygulama', ad: p.kimlik.project_title || 'Adsız uygulama projesi',
                    ornek: o, guncellendi: Date.now()});
            localStorage.setItem('asansor:projeler', JSON.stringify(l));
            return id;
        }""",
        [degerler or {}, ornek, ad],
    )
    s.goto(f"{KOK}/uygulama/{pid}{sorgu}")
    bekle(s, 1500)
    return pid


def alana_yaz(s, grup, anahtar, deger):
    s.get_by_role("button", name=grup, exact=True).first.click()
    s.locator(f"#alan-{anahtar}").fill(deger)
    bekle(s, 1500)


def acilis(s):
    proje(s, {}, ornek=True)
    proje(s, {"kuyu_genisligi": "1200"}, ad="Hastane — Servis asansörü")
    proje(s, {"halat_capi": "8", "motor_gucu": "7,5"}, ad="Konut — A Blok")
    s.goto(KOK + "/")
    bekle(s)


def calisma(s):
    proje(s, {"asansor_adi": "A Blok"})
    s.get_by_role("button", name="Askı halatlarının hesaplanması").first.click()
    time.sleep(0.6)


def olcu(s):
    proje(s, {}, "?cizim=kuyu_plani")
    s.evaluate(
        """() => [...document.querySelectorAll('[data-cizim="kuyu_plani"] .olcu')]
            .find(x => (x.getAttribute('aria-label') || '').includes('Kabin dış genişliği'))
            .dispatchEvent(new MouseEvent('click', {bubbles: true}))"""
    )
    bekle(s, 800)


def hesap(s):
    proje(s, {}, "?gorunum=hesap")
    s.get_by_role("button", name="Askı halatlarının hesaplanması").first.click()
    time.sleep(1.0)


def hesap_durdu(s):
    proje(s, {"asansor_adi": "A Blok"})
    alana_yaz(s, "Kuyu ve katlar", "kuyu_genisligi", "1200")


def kural_disi(s):
    proje(s, {"asansor_adi": "A Blok"})
    alana_yaz(s, "Kuyu ve katlar", "durak_adedi", "250")


def teslim(s):
    proje(s, {}, "?teslim=1")
    s.get_by_text("değeri programın varsayılanıyla yaptı").click()
    time.sleep(0.5)


def ofis(s):
    s.goto(KOK + "/ofis-standardi")
    bekle(s)


def tablolar(s):
    s.goto(KOK + "/tablolar")
    bekle(s)


def avan_projesi(s):
    s.goto(KOK + "/")
    s.evaluate(
        """() => localStorage.setItem('asansor:avan', JSON.stringify({
            kimlik: '',
            trafik: {bina_tipi: 'Konut', bina_yuksekligi: '30', yapi_yuksekligi: '31', N: '10', h: '3',
                     hizli1: '20', hizli2: '2'},
            trafikAsansorleri: [{P: '8', V: '1', kapi_genisligi: '800', kapi_tipi: 'Teleskopik Otomatik',
                                 durak: '11'}],
            ortak: {mk_yok: 'true', temel_a: '20', temel_b: '15'},
            avanAsansorleri: [
              {makine_tipi: 'Dişlisiz', Hk: '34', kuyu_genisligi: '1,8', kabin_boyu: '1,4',
               kabin_genisligi: '1,1', L1: '40'},
              {makine_tipi: 'Dişlisiz', Hk: '34', kuyu_genisligi: '1,8', kabin_boyu: '1,4',
               kabin_genisligi: '1,1', L1: '40'}, {}, {}],
            kapak: {project_title: 'Konut — A Blok', owner: '[İŞVEREN]', city: '[İL]', district: '[İLÇE]'}
        }))"""
    )


def avan(adim, ms):
    def ac(s):
        avan_projesi(s)
        s.goto(f"{KOK}/avan/{adim}")
        bekle(s, ms)

    return ac


EKRANLAR = [
    ("01-acilis", acilis),
    ("02-calisma-cizim", calisma),
    ("03-olcu-kutusu", olcu),
    ("04-calisma-hesap", hesap),
    ("05-hesap-durdu", hesap_durdu),
    ("06-kural-disi-girdi", kural_disi),
    ("07-teslim", teslim),
    ("08-ofis-standardi", ofis),
    ("09-tablolar", tablolar),
    ("10-avan-trafik", avan("trafik", 1200)),
    ("11-avan-hesaplar", avan("hesaplar", 1500)),
    ("12-avan-kapak", avan("kapak", 2500)),
]


def main(secilen):
    os.makedirs(CIKTI, exist_ok=True)
    basarisiz = 0
    with sync_playwright() as p:
        tarayici = p.chromium.launch()
        for ad, kur in EKRANLAR:
            if secilen and not any(x in ad for x in secilen):
                continue
            baglam = tarayici.new_context(
                viewport={"width": 1440, "height": 900}, device_scale_factor=2, locale="tr-TR"
            )
            s = baglam.new_page()
            hatalar = []
            s.on("pageerror", lambda e, h=hatalar: h.append(str(e)))
            try:
                kur(s)
                print("tamam ", ad, *(["  SAYFA HATASI:", *hatalar] if hatalar else []))
                basarisiz += bool(hatalar)
            except Exception as e:  # noqa: BLE001 — bir ekranın hatası ötekileri durdurmasın
                print("OLMADI", ad, e)
                basarisiz += 1
            s.screenshot(path=os.path.join(CIKTI, ad + ".png"))
            baglam.close()
        tarayici.close()
    print(f"\n{CIKTI}")
    return 1 if basarisiz else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
