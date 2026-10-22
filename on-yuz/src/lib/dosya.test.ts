import { describe, expect, it } from "vitest";
import { AVAN_DOSYASI_UYGULAMADA, dosyaGovdesi, dosyaOku } from "./dosya";
import type { UygulamaProjesi } from "./proje";
import { SEMA } from "./test-semasi";

const proje: UygulamaProjesi = {
  id: "t",
  tur: "uygulama",
  kimlik: { project_title: "A Blok", owner: "İşveren", sheet_no: "12" },
  asansorler: [{ kuyu_genisligi: "2500", aski_orani: "1" }, { durak_adedi: "12" }],
  proje_geneli: { mk_yok: "false", mk_uzunluk: "3000" },
  kapak: { city: "Konya" },
  guncellendi: 0,
};

describe("proje dosyası — eski arayüzün biçimi", () => {
  it("eski arayüzün okuduğu anahtarlarla yazılır", () => {
    const d = dosyaGovdesi(proje, SEMA, { sigma_em: "140" });
    expect(d.__mod).toBe("uygulama");
    expect(d.alanlar).toMatchObject({
      mk_proje_adi: "A Blok",
      mk_isveren: "İşveren",
      mk_pafta_no: "12",
      m_adet: "2",
      //  onay alanı eski arayüzde onay kutusudur
      m_mk_yok: false,
      m_mk_uzunluk: "3000",
      uof_sigma_em: "140",
      __muk_adet: 2,
      __muk_asansorler: [{ kuyu_genisligi: "2500", aski_orani: "1" }, { durak_adedi: "12" }],
    });
  });

  it("yazılan dosya aynı projeyi geri verir", () => {
    const o = dosyaOku(JSON.stringify(dosyaGovdesi(proje, SEMA, {})), SEMA, {});
    expect(o.tamam).toBe(true);
    if (!o.tamam) return;
    expect(o.icerik).toEqual({
      kimlik: proje.kimlik,
      asansorler: proje.asansorler,
      proje_geneli: proje.proje_geneli,
      kapak: proje.kapak,
    });
    expect(o.ofisFarki).toEqual([]);
  });

  it("eski arayüzün dosyası:  varsayılana eşit değerler yazılmamış sayılır", () => {
    //  Eski arayüz her kutuyu doldurur ( varsayılanlar dahil, metin olarak )
    const eski = {
      __mod: "uygulama",
      __surum: 1,
      alanlar: {
        mk_proje_adi: "Eski",
        m_mk_yok: true,
        uof_sigma_em: "130",
        __muk_adet: 1,
        __muk_asansorler: [{ beyan_yuku: "800", kuyu_genisligi: "2.400", durak_adedi: "10", aski_orani: "2", asansor_adi: "" }],
      },
    };
    const o = dosyaOku(JSON.stringify(eski), SEMA, {});
    expect(o.tamam).toBe(true);
    if (!o.tamam) return;
    //  800 ve 2:1 varsayılan;  "2.400" belirsiz:  sunucuya olduğu gibi gider
    expect(o.icerik.asansorler).toEqual([{ kuyu_genisligi: "2.400", durak_adedi: "10" }]);
    expect(o.icerik.proje_geneli).toEqual({});
    //  ofis değeri varsayılana eşit:  fark yok
    expect(o.ofisFarki).toEqual([]);
  });

  it("listede olmayan seçim varsayılana döner ve söylenir", () => {
    const c = dosyaOku(JSON.stringify({ alanlar: { __muk_asansorler: [{ beyan_yuku: "1000,0" }] } }), SEMA, {});
    //  seçim listedeki yazımıyla:  kutu onu tanır
    expect(c.tamam && c.icerik.asansorler).toEqual([{ beyan_yuku: "1000" }]);
    const b = dosyaOku(JSON.stringify({ alanlar: { __muk_asansorler: [{ kabin_agirligi: "", kuyu_genisligi: "" }] } }), SEMA, {});
    //  boş kabin kutusu "tablodan" demektir:  boş olarak taşınır
    expect(b.tamam && b.icerik.asansorler).toEqual([{ kabin_agirligi: "" }]);
    const o = dosyaOku(JSON.stringify({ alanlar: { __muk_asansorler: [{ beyan_yuku: "999" }] } }), SEMA, {});
    expect(o.tamam && o.taninmayan).toEqual(["beyan_yuku = 999"]);
  });

  it("ofis standardı farkı sayılır, uygulanmaz", () => {
    const o = dosyaOku(JSON.stringify({ alanlar: { uof_sigma_em: "150", __muk_asansorler: [{}] } }), SEMA, {});
    expect(o.tamam && o.ofisFarki).toEqual(["sigma_em"]);
  });

  it("avan dosyası ve bozuk dosya anlaşılır biçimde reddedilir", () => {
    expect(dosyaOku(JSON.stringify({ __mod: "avan", alanlar: {} }), SEMA, {}).tamam).toBe(false);
    expect(dosyaOku("{bozuk", SEMA, {}).tamam).toBe(false);
  });

  it("uygulama kısmı avan dosyasını açmaz, nereden açılacağını söyler ( başlıksız eski avan dosyası da )", () => {
    for (const d of [{ __mod: "avan", alanlar: {} }, { alanlar: { c_bina_tipi: "Konut" } }, { a_Hk: "34" }]) {
      const o = dosyaOku(JSON.stringify(d), SEMA, {});
      expect(o).toEqual({ tamam: false, hata: AVAN_DOSYASI_UYGULAMADA });
    }
    expect(AVAN_DOSYASI_UYGULAMADA).toMatch(/avan ekranından ya da açılış sayfasından/);
  });

  it("asansör adedi dört ile sınırlı", () => {
    const o = dosyaOku(JSON.stringify({ alanlar: { __muk_adet: 9, __muk_asansorler: Array(9).fill({}) } }), SEMA, {});
    expect(o.tamam && o.icerik.asansorler.length).toBe(4);
  });
});
