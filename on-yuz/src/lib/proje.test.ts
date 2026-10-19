import { describe, expect, it } from "vitest";
import { alanHatasi, alanOku, alanYaz, asansorAdedi, asansorEkle, asansorKaldir, formHatalari, gizliAlanlar, istekKur, kutuyaYaz, sayiOku, type UygulamaProjesi } from "./proje";
import { SEMA } from "./test-semasi";

const proje = (p: Partial<UygulamaProjesi> = {}): UygulamaProjesi => ({
  id: "t",
  tur: "uygulama",
  kimlik: { project_title: "", owner: "", sheet_no: "" },
  asansorler: [{}],
  proje_geneli: {},
  guncellendi: 0,
  ...p,
});

describe("sayıyı okuma — ön yüz sunucudan sıkı olamaz", () => {
  it("tartışmasız sayılar okunur ( virgül ve nokta ondalık )", () => {
    expect(sayiOku("2400")).toBe(2400);
    expect(sayiOku("1,6")).toBe(1.6);
    expect(sayiOku("1.6")).toBe(1.6);
    expect(sayiOku("-3")).toBe(-3);
    expect(sayiOku("0,075")).toBe(0.075);
  });
  it("belirsiz ve tuhaf yazımlar sunucuya bırakılır", () => {
    for (const m of ["1.200", "1,200", "abc", "1 200", "1e3", "", "  "]) expect(sayiOku(m)).toBeNull();
  });
});

describe("alanın kuralı ( sunucunun kurallar sözlüğünden )", () => {
  it("aralık ve tam sayı", () => {
    expect(alanHatasi(SEMA, "durak_adedi", "250")).toBe("En çok 100");
    expect(alanHatasi(SEMA, "durak_adedi", "7,5")).toBe("Tam sayı olmalı");
    expect(alanHatasi(SEMA, "durak_adedi", "12")).toBeNull();
    expect(alanHatasi(SEMA, "mk_uzunluk", "0")).toBe("0 üstünde olmalı");
  });
  it("null sınır yok demektir:  eksi kaçıklık geçerli ( gerçek projeler açılınca ekran çöküyordu )", () => {
    expect(alanHatasi(SEMA, "kabin_yana_kaciklik", "-150")).toBeNull();
    expect(alanHatasi(SEMA, "kabin_yana_kaciklik", "25000")).toBe("En çok 20.000");
  });
  it("okunamayan yazım ön yüzde reddedilmez:  sebebi sunucunundur", () => {
    expect(alanHatasi(SEMA, "durak_adedi", "abc")).toBeNull();
    expect(alanHatasi(SEMA, "durak_adedi", "1.200")).toBeNull();
  });
});

describe("gizli alanlar denetlenmez", () => {
  it("makine dairesizde makine dairesi ölçüsü kural dışı olsa da projeyi durdurmaz", () => {
    const p = proje({ proje_geneli: { mk_uzunluk: "-5" } });
    expect(gizliAlanlar(SEMA, p).has("mk_uzunluk")).toBe(true);
    expect(formHatalari(SEMA, p)).toEqual([]);
  });
  it("makine daireliyse aynı değer kural dışıdır", () => {
    const p = proje({ proje_geneli: { mk_yok: "false", mk_uzunluk: "-5" } });
    expect(formHatalari(SEMA, p)).toEqual([{ anahtar: "mk_uzunluk", hata: "0 üstünde olmalı", asansor: null }]);
  });
  it("hatanın asansörü bildirilir", () => {
    const p = proje({ asansorler: [{}, { durak_adedi: "250" }] });
    expect(formHatalari(SEMA, p)).toEqual([{ anahtar: "durak_adedi", hata: "En çok 100", asansor: 1 }]);
  });
});

describe("alan yazma", () => {
  it("boş değer alanı siler ( sunucu varsayılanını uygular )", () => {
    const p = alanYaz(proje({ asansorler: [{ kuyu_genisligi: "2400" }] }), SEMA, 0, "kuyu_genisligi", " ");
    expect(p.asansorler[0]).toEqual({});
  });
  it("binaya ait alan bütün asansörlerde ortak", () => {
    const p = alanYaz(proje({ asansorler: [{}, {}] }), SEMA, 1, "mk_yok", "false");
    expect(p.proje_geneli).toEqual({ mk_yok: "false" });
    expect(p.asansorler).toEqual([{}, {}]);
  });
  it("yük değişince kabin ağırlığı tabloya döner ( eski arayüzün kuralı )", () => {
    const p0 = proje({ asansorler: [{ beyan_yuku: "800", kabin_agirligi: "700" }, { kabin_agirligi: "650" }] });
    const p = alanYaz(p0, SEMA, 0, "beyan_yuku", "1000");
    //  boş metin = tablodan;  alan silinseydi sunucu varsayılanı ( 700 ) kullanırdı
    expect(p.asansorler[0]).toEqual({ beyan_yuku: "1000", kabin_agirligi: "" });
    expect(p.asansorler[1]).toEqual({ kabin_agirligi: "650" });
    expect(alanOku(p, SEMA, 0, "kabin_agirligi")).toBeUndefined();
  });
  it("tablodan alanı silinince boş kalır, öbür alan silinir", () => {
    const p0 = proje({ asansorler: [{ kabin_agirligi: "900", kuyu_genisligi: "2400" }] });
    const p = alanYaz(alanYaz(p0, SEMA, 0, "kabin_agirligi", " "), SEMA, 0, "kuyu_genisligi", "");
    expect(p.asansorler[0]).toEqual({ kabin_agirligi: "" });
  });
  it("aynı yük yeniden seçilince kabin ağırlığı kalır", () => {
    const p = alanYaz(proje({ asansorler: [{ beyan_yuku: "800", kabin_agirligi: "700" }] }), SEMA, 0, "beyan_yuku", "800");
    expect(p.asansorler[0].kabin_agirligi).toBe("700");
  });
});

describe("istek", () => {
  it("ofis standardının boş kutuları gönderilmez", () => {
    const i = istekKur(proje(), { sigma_em: "", kablo_tipi: "NYY", x: "  " });
    expect(i.sabitler).toEqual({ kablo_tipi: "NYY" });
  });
});

describe("sunucudan gelen sayıyı kutuya yazma", () => {
  it("ondalık virgülle", () => {
    expect(kutuyaYaz(1470)).toBe("1470");
    expect(kutuyaYaz(1072.5)).toBe("1072,5");
  });
  it("üç ondalıklı yazım belirsiz sayılmasın diye sıfır eklenir", () => {
    expect(kutuyaYaz(123.456)).toBe("123,4560");
    expect(sayiOku(kutuyaYaz(123.456))).toBe(123.456);
  });
});

describe("asansör ekleme / kaldırma", () => {
  const p0 = proje({ asansorler: [{ asansor_adi: "A", kuyu_genisligi: "2400" }, { asansor_adi: "B" }, { asansor_adi: "C" }] });
  it("yeni asansör 1 nolunun kopyası, adı hariç", () => {
    const p = asansorEkle(p0, 4);
    expect(p.asansorler[3]).toEqual({ kuyu_genisligi: "2400" });
    expect(asansorEkle(p, 4)).toBe(p);
  });
  it("ortadaki asansör kaldırılır, sırası korunur;  son asansör kalır", () => {
    expect(asansorKaldir(p0, 1).asansorler.map((h) => h.asansor_adi)).toEqual(["A", "C"]);
    const tek = proje({ asansorler: [{ asansor_adi: "A" }] });
    expect(asansorKaldir(tek, 0)).toBe(tek);
  });
  it("adet artınca kopyalar, azalınca sondakiler gider", () => {
    expect(asansorAdedi(p0, 1, 4).asansorler).toEqual([{ asansor_adi: "A", kuyu_genisligi: "2400" }]);
    expect(asansorAdedi(p0, 4, 4).asansorler).toHaveLength(4);
    expect(asansorAdedi(p0, 9, 4).asansorler).toHaveLength(4);
  });
});
