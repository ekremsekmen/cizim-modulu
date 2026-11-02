import { describe, expect, it, vi } from "vitest";
import { alanHatasi, alanOku, alanYaz, asansorAdedi, asansorEkle, asansorKaldir, formHatalari, gizliAlanlar, girilmeyenler, kotOzeti, kotlayaCevir, varsayilanKotlarMi, istekKur, kutuyaYaz, kuyununOrtaklari, projeOku, sayiOku, secenekKapali, siraKaydir, tekKuyuMu, type UygulamaProjesi } from "./proje";
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

describe("yerleşime bağlı seçenek ( secenek_kosulu:  yalnız o yerleşimde )", () => {
  const aski = SEMA.gruplar.flatMap((g) => g.alanlar).find((a) => a.anahtar === "aski_orani")!;
  it("1:1 makine dairelide açık, dairesizde sebebiyle kapalı ( 21 Eki:  ters okunuyordu )", () => {
    expect(secenekKapali(aski, 1, false)).toBeUndefined();
    expect(secenekKapali(aski, 1, true)).toBe("Makine dairesizde 1:1 askı kullanılmaz");
  });
  it("koşulsuz seçenek her yerleşimde açık", () => {
    expect(secenekKapali(aski, 2, true)).toBeUndefined();
    expect(secenekKapali(aski, 2, false)).toBeUndefined();
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

describe("asansöre özgü kapak değeri asansörüyle gider ( 24 Eki )", () => {
  //  "capacity.2" 2 nolu asansörün tablosudur:  sıra kayınca anahtar da kaymalı
  const p0 = proje({
    asansorler: [{ beyan_yuku: "630" }, { beyan_yuku: "1000" }, { beyan_yuku: "1600" }],
    kapak: { "capacity.1": "630 kg", "capacity.2": "1000 kg", "speed.3": "2 m/s", capacity: "hepsi", owner: "İşveren" },
  });
  it("kaldırılanınki silinir, sonrakiler bir öne kayar ( kalan 1000 kg'lık asansöre 630 basılıyordu )", () => {
    expect(asansorKaldir(p0, 0).kapak).toEqual({ "capacity.1": "1000 kg", "speed.2": "2 m/s", capacity: "hepsi", owner: "İşveren" });
    expect(asansorKaldir(p0, 1).kapak).toEqual({ "capacity.1": "630 kg", "speed.2": "2 m/s", capacity: "hepsi", owner: "İşveren" });
  });
  it("adet azalınca kaldırılanlarınki silinir", () => {
    expect(asansorAdedi(p0, 1, 4).kapak).toEqual({ "capacity.1": "630 kg", capacity: "hepsi", owner: "İşveren" });
  });
  it("yeni asansör kaldırılmış bir asansörün değerini almaz ( eski kayıtta kalmış olsa da )", () => {
    const eski = proje({ asansorler: [{}], kapak: { "capacity.2": "eski 2. asansör", "speed.1": "1 m/s" } });
    expect(asansorEkle(eski, 4).kapak).toEqual({ "speed.1": "1 m/s" });
  });
  it("asansöre ait olmayan ve sırası olmayan anahtara dokunulmaz", () => {
    const p = proje({ asansorler: [{}, {}], kapak: { "owner.1": "x", "capacity.a": "y", "capacity.2": "z" } });
    expect(asansorKaldir(p, 0).kapak).toEqual({ "owner.1": "x", "capacity.a": "y", "capacity.1": "z" });
  });
  it("kayıtlı projede olmayan asansörün değeri atılır ( eskiden kalmış:  görünmeden 'dolu alan' sayılıyordu )", () => {
    const kayit = proje({ asansorler: [{}, {}], kapak: { "capacity.2": "iki", "capacity.3": "kalıntı", city: "Konya" } });
    vi.stubGlobal("localStorage", { getItem: () => JSON.stringify(kayit) });
    try {
      expect(projeOku("t")?.kapak).toEqual({ "capacity.2": "iki", city: "Konya" });
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("sırayla tutulan veri ( son temiz girdi ) asansörüyle gider ( 24 Eki )", () => {
  //  "Düzeltme öner" asansörün son temiz girdisini gönderir;  sırayla tutuluyordu
  const p0 = proje({ asansorler: [{ asansor_adi: "A" }, { asansor_adi: "B" }, { asansor_adi: "C" }] });
  const veri = { 0: "A'nın", 1: "B'nin", 2: "C'nin" };
  const kaydir = (p: UygulamaProjesi, v: Record<number, string> = veri, once = p0) => siraKaydir(v, once.asansorler, p.asansorler);

  it("kaldırılanınki gider, sonrakiler kayar ( 1. kaldırılınca 2.'ye 1.'ninki gidiyordu )", () => {
    expect(kaydir(asansorKaldir(p0, 0))).toEqual({ 0: "B'nin", 1: "C'nin" });
    expect(kaydir(asansorKaldir(p0, 1))).toEqual({ 0: "A'nın", 1: "C'nin" });
    expect(kaydir(asansorAdedi(p0, 1, 4))).toEqual({ 0: "A'nın" });
  });
  it("girdisi yazılan asansör yerinde kalır;  eklenenin verisi yok", () => {
    expect(kaydir(alanYaz(p0, SEMA, 1, "kuyu_genisligi", "2000"))).toEqual(veri);
    expect(kaydir(asansorEkle(p0, 4))).toEqual(veri);
    expect(kaydir(asansorEkle(asansorKaldir(p0, 2), 4), { 0: "A'nın", 1: "B'nin" }, asansorKaldir(p0, 2))).toEqual({ 0: "A'nın", 1: "B'nin" });
  });
  it("geri alınınca kalanlarınki yerine döner, geri gelenin verisi unutulur", () => {
    const kaldirilmis = asansorKaldir(p0, 0);
    const geri = { ...kaldirilmis, asansorler: p0.asansorler };
    expect(kaydir(geri, kaydir(kaldirilmis), kaldirilmis)).toEqual({ 1: "B'nin", 2: "C'nin" });
  });
  it("başka sekmeden gelen liste:  boyu aynıysa yerinde, değiştiyse hepsi unutulur", () => {
    const disaridan = (p: UygulamaProjesi) => JSON.parse(JSON.stringify(p)) as UygulamaProjesi;
    expect(kaydir(disaridan(p0))).toEqual(veri);
    expect(kaydir(disaridan(asansorKaldir(p0, 0)))).toEqual({});
  });
});

describe("tek kuyuda iki asansör ( sunucu:  gorunum.tek_kuyu_mu, kapı 1.'nin ortaklarını öbürüne yazar )", () => {
  const tek = { kuyu_duzeni: "Tek kuyu" };
  it("yalnız iki asansörlü projede ve seçilince", () => {
    expect(tekKuyuMu(SEMA, proje({ asansorler: [{}, {}], proje_geneli: tek }))).toBe(true);
    expect(tekKuyuMu(SEMA, proje({ asansorler: [{}, {}], proje_geneli: { kuyu_duzeni: "Ayrı" } }))).toBe(false);
    for (const n of [1, 3]) expect(tekKuyuMu(SEMA, proje({ asansorler: Array.from({ length: n }, () => ({})), proje_geneli: tek }))).toBe(false);
  });
  it("kuyu düzeni yalnız iki asansörde, tek kuyunun alanları yalnız tek kuyuda görünür", () => {
    const g = (n: number, pg = {}) => gizliAlanlar(SEMA, proje({ asansorler: Array.from({ length: n }, () => ({})), proje_geneli: pg }));
    expect(g(1).has("kuyu_duzeni")).toBe(true);
    expect(g(2).has("kuyu_duzeni")).toBe(false);
    expect(g(2).has("ayirma_kirisi")).toBe(true);
    expect(g(2, tek).has("ayirma_kirisi")).toBe(false);
    expect(g(2, tek).has("soldaki_asansor")).toBe(false);
    expect(g(3, tek).has("ayirma_kirisi")).toBe(true);
  });
  it("tek kuyuya geçince 1.'nin ortak girdileri öbürüne yazılır, asansörünki kalır", () => {
    const p0 = proje({ asansorler: [{ kuyu_derinligi: "2800", kuyu_genisligi: "2000" }, { kuyu_derinligi: "1234", kuyu_dibi: "1500", kuyu_genisligi: "1900" }] });
    const p = alanYaz(p0, SEMA, 1, "kuyu_duzeni", "Tek kuyu");
    expect(p.asansorler[1]).toEqual({ kuyu_derinligi: "2800", kuyu_genisligi: "1900" });
    expect(p.asansorler[0]).toBe(p0.asansorler[0]);
    //  Ayrı'ya dönünce değerler kalır ( ayrı ayrı değiştirilir )
    expect(alanYaz(p, SEMA, 0, "kuyu_duzeni", "Ayrı").asansorler).toEqual(p.asansorler);
  });
  it("tek kuyuda ortak alan iki asansöre yazılır, 1.'den okunur, hatası bir kez", () => {
    const p0 = proje({ asansorler: [{}, {}], proje_geneli: tek });
    const p = alanYaz(p0, SEMA, 1, "durak_adedi", "250");
    expect(p.asansorler.map((h) => h.durak_adedi)).toEqual(["250", "250"]);
    expect(alanOku({ ...p, asansorler: [p.asansorler[0], {}] }, SEMA, 1, "durak_adedi")).toBe("250");
    expect(formHatalari(SEMA, p).filter((h) => h.anahtar === "durak_adedi").map((h) => h.asansor)).toEqual([0]);
    //  Asansörün kendi alanı yalnız ona;  ayrı kuyuda ortak alan da yalnız ona
    expect(alanYaz(p0, SEMA, 1, "kuyu_genisligi", "1900").asansorler[0]).toEqual({});
    const ayri = proje({ asansorler: [{}, {}] });
    expect(alanYaz(ayri, SEMA, 1, "durak_adedi", "5").asansorler[0]).toEqual({});
    expect(kuyununOrtaklari(SEMA, ayri).size).toBe(0);
  });
});

describe("Teslim'in 'girmediğiniz değerler'i ( girilmeyenler ) kat girişinin kipine bakar", () => {
  const adlar = (p: UygulamaProjesi) => girilmeyenler(SEMA, p, 0).map((x) => x.alan.anahtar);
  it("ölçüyle girişte durak adedi yazılmadıysa varsayılandır", () => {
    expect(adlar(proje())).toContain("durak_adedi");
  });
  it("kotla girişte durak adedi kotlardan türer:  girmediğiniz değer değildir ( 2 Kas )", () => {
    const p = proje({ asansorler: [{ durak_kotlari: "0; 3; 6" }] });
    expect(adlar(p)).not.toContain("durak_adedi");
    //  Kipin dışındaki alanlar yine sayılır
    expect(adlar(p)).toContain("kuyu_genisligi");
  });
  it("yazılan alan ve gizli alan sayılmaz", () => {
    expect(adlar(proje({ asansorler: [{ kuyu_genisligi: "2200" }] }))).not.toContain("kuyu_genisligi");
    expect(adlar(proje())).not.toContain("mk_uzunluk");
  });
});

describe("yalnız kotla giriş ( 2 Kas ):  kotsuz proje açılırken kotlara çevrilir", () => {
  it("eski dosyanın ölçüleri kotlara:  en alt durak ±0,00, türetilenler silinir", () => {
    const p = kotlayaCevir(
      SEMA,
      proje({
        asansorler: [{ durak_adedi: "3", seyir_mesafesi: "6", kuyu_dibi: "1500", son_kat_yuksekligi: "4000", kuyu_genisligi: "2200" }],
      }),
    );
    expect(p.asansorler[0]).toEqual({
      durak_kotlari: "±0,00; +3,00; +6,00",
      kuyu_dibi_kotu: "-1,50",
      kuyu_tavani_kotu: "+10,00",
      kuyu_genisligi: "2200",
    });
    expect(kotOzeti(p.asansorler[0])).toBe("3 durak · ±0,00 … +6,00");
  });
  it("kat yükseklikleri yazılıysa onlarla", () => {
    const h = kotlayaCevir(SEMA, proje({ asansorler: [{ durak_adedi: "3", seyir_mesafesi: "7", kat_yukseklikleri: "4000; 3000" }] }))
      .asansorler[0];
    expect(h.durak_kotlari).toBe("±0,00; +4,00; +7,00");
  });
  it("kotla girilmiş proje aynen döner ( aynı nesne )", () => {
    const p = proje({ asansorler: [{ durak_kotlari: "-3,00; ±0,00", kuyu_dibi_kotu: "-4,50" }] });
    expect(kotlayaCevir(SEMA, p)).toBe(p);
  });
  it("yeni projenin kotları programın varsayılanı:  Teslim 'girmediğiniz' sayar, değişince saymaz", () => {
    const p = kotlayaCevir(SEMA, proje());
    expect(varsayilanKotlarMi(SEMA, p, 0)).toBe(true);
    const q = { ...p, asansorler: [{ ...p.asansorler[0], kuyu_dibi_kotu: "-1,70" }] };
    expect(varsayilanKotlarMi(SEMA, q, 0)).toBe(false);
    //  Kotlardan türeyenler hiçbir zaman "girmediğiniz" değildir
    expect(girilmeyenler(SEMA, q, 0).map((x) => x.alan.anahtar)).not.toContain("durak_adedi");
  });
});
