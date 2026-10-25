/*  PROJENİN DURUMU ( açılış listesi ) — 24 Eki:  liste seçili asansörün hükmünü
    gösteriyordu ( ikinci asansör hesaplanamazken "Uygun" ), hesabı eksik ve proje
    geneli "uygun değil" proje de "Uygun" sayılıyordu;  durum eşitlenen proje kaydına
    yazıldığından iki sekme birbirini durmadan eziyordu;  avan listeye hiç girmiyordu.
    Uygulama projesinin hükmünü motor kurar ( kuralı testler/test_proje_hukmu.py
    denetler );  burada ekranın onu olduğu gibi okuması, avanın hükmü ve durumun
    girdisine ait olması denetlenir.                                             */
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AvanKoprusu, AvanYaniti, Bolum, CokluYanit, ProjeHukmu, TrafikYaniti } from "./api";
import { avanHukmu, izi, uygulamaHukmu } from "./durum";

/**  "sonucsuz":  hükümsüz bölümün sunucuda sonucu da yok ( null — topraklayıcılar )  */
const bolum = (uygun: boolean | null | "sonucsuz"): Bolum => ({
  baslik: "",
  kaynak: "",
  adimlar: [],
  sonuc: uygun === "sonucsuz" ? null : { baslik: "", metin: "", uygun },
  notlar: [],
  aciklamalar: [],
  kimlik: "b",
  ad: "",
  sira: 1,
});

const yanit = (proje_hukmu?: ProjeHukmu): CokluYanit => ({
  aktif: true,
  asansorler: [],
  ozet: { adet: 2, tumu_uygun: proje_hukmu?.durum === "uygun", proje_hukmu, asansorler: [] },
});

describe("uygulama projesinin hükmü motorundur:  ekran okur, kurmaz", () => {
  it("motorun hükmü olduğu gibi", () => {
    for (const durum of ["durdu", "eksik", "uygun_degil", "uygun"] as const)
      expect(uygulamaHukmu(yanit({ durum, uygun_degil: 3 }), 2)).toEqual({ hukum: durum, adet: 2, uygunDegil: 3 });
  });
  it("istek bütünüyle reddedildiyse hesap durdu ( yanıtta asansör listesi yok )", () => {
    expect(uygulamaHukmu({ aktif: false, hata: ["ofis değeri"] }, 3)).toEqual({ hukum: "durdu", adet: 3, uygunDegil: 0 });
  });
  it("hükümsüz yanıt:  bilinmiyor ( yazılmaz — 'Uygun' sanılmaz )", () => {
    expect(uygulamaHukmu(yanit(), 2)).toBeUndefined();
  });
});

describe("avan projesinin hükmü", () => {
  const KOPRU: AvanKoprusu = { tip: "tek", N: 10, bodrum: 0, h: 3, adet: 2, asansorler: [{ P: 8, V: 1.6, toplam_seyahat: 30 }, { P: 8, V: 1.6, toplam_seyahat: 30 }] };
  const trafik = (o: Partial<TrafikYaniti> = {}): TrafikYaniti => ({
    hata: null,
    bolumler: [bolum(null)],
    ozet: {
      bina_tipi: "Konut",
      standart: "",
      B: 0,
      TR: 0,
      R: 0,
      Ieer: 0,
      Izul: 0,
      adet: 2,
      sonuc_cumlesi: "",
      karar_olcutleri: [{ ad: "Taşıma", metin: "", uygun: true }],
    },
    avan_koprusu: KOPRU,
    ...o,
  });
  const avan = (o: Partial<AvanYaniti> = {}): AvanYaniti => ({
    asansorler: [
      { no: 1, aktif: true, bolumler: [bolum(true)] },
      { no: 2, aktif: true, bolumler: [bolum(true)] },
    ],
    topraklama: { aktif: true, bolumler: [bolum(true)] },
    engelleyici: [],
    ...o,
  });

  it("trafik hesabı yapılamadıysa hesap durdu", () => {
    expect(avanHukmu(trafik({ hata: "Bina tipi listeden seçilmelidir." }), null)).toEqual({ hukum: "durdu", adet: 0, uygunDegil: 0 });
  });
  it("girdisi tamamlanmamış avan asansörü:  hesap durdu ( avan ekranı da 'eksik' der )", () => {
    const a = avan({ asansorler: [{ no: 1, aktif: true, bolumler: [] }, { no: 2, aktif: false, uyari: "girdi tamamlanmadı" }] });
    expect(avanHukmu(trafik(), KOPRU, a).hukum).toBe("durdu");
  });
  it("trafik ölçütü, bölüm ve engelleyici 'uygun değil'e girer", () => {
    expect(avanHukmu(trafik(), KOPRU, avan({ topraklama: { aktif: true, bolumler: [bolum(false)] } }))).toEqual({
      hukum: "uygun_degil",
      adet: 2,
      uygunDegil: 1,
    });
    const olcut = trafik({ ozet: { ...trafik().ozet!, karar_olcutleri: [{ ad: "Bekleme", metin: "", uygun: false }] } });
    expect(avanHukmu(olcut, KOPRU, avan()).hukum).toBe("uygun_degil");
    expect(avanHukmu(trafik(), KOPRU, avan({ engelleyici: ["kabin alanı"] })).hukum).toBe("uygun_degil");
  });
  it("hepsi uygunsa uygun;  asansör sayısı trafikten", () => {
    expect(avanHukmu(trafik(), KOPRU, avan())).toEqual({ hukum: "uygun", adet: 2, uygunDegil: 0 });
  });
});

describe("girdinin izi", () => {
  it("anahtar sırasından bağımsız, değer değişince değişir", () => {
    expect(izi({ a: "1", b: ["x", { c: 2, d: 3 }] })).toBe(izi({ b: ["x", { d: 3, c: 2 }], a: "1" }));
    expect(izi({ a: "1" })).not.toBe(izi({ a: "2" }));
    expect(izi({ a: ["1", "2"] })).not.toBe(izi({ a: ["2", "1"] }));
    //  JSON'a girmeyen tanımsız değer izi değiştirmez ( kayıttan okunan hâl aynı izi verir )
    expect(izi({ a: "1", b: undefined })).toBe(izi({ a: "1" }));
  });
});

/* ───────────────────────────── tarayıcı deposuyla:  durum girdisinindir */
function sahteDepo() {
  const m = new Map<string, string>();
  const yazilan: string[] = [];
  return {
    m,
    yazilan,
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => {
      yazilan.push(k);
      m.set(k, v);
    },
    removeItem: (k: string) => m.delete(k),
  };
}
async function moduller(d: ReturnType<typeof sahteDepo>) {
  vi.resetModules();
  vi.stubGlobal("localStorage", d);
  const [proje, avan, durum] = await Promise.all([import("./proje"), import("./avan"), import("./durum")]);
  return { proje, avan, durum };
}
afterEach(() => vi.unstubAllGlobals());

describe("liste yalnız kayıttaki girdinin durumunu gösterir", () => {
  it("uygulama:  girdi ya da ofis standardı değişince 'Hesaplanmadı';  aynı girdiye dönünce yine görünür", async () => {
    const d = sahteDepo();
    const { proje, durum } = await moduller(d);
    const p = proje.yeniUygulama(false, { kimlik: { project_title: "A", owner: "", sheet_no: "" }, asansorler: [{ kuyu_genisligi: "2200" }], proje_geneli: {}, kapak: {} });
    const iz = proje.uygulamaIzi(p, {});
    durum.durumYaz(p.id, { iz, hukum: "uygun", adet: 1, uygunDegil: 0 });
    expect(proje.uygulamaListeDurumu(p.id)?.hukum).toBe("uygun");
    //  Girdi değişti ( sonuç gelmeden sekme kapandı ):  eski hüküm yeni girdinin sanılmaz
    const k = `asansor:proje:${p.id}`;
    d.m.set(k, JSON.stringify({ ...p, asansorler: [{ kuyu_genisligi: "1000" }] }));
    expect(proje.uygulamaListeDurumu(p.id)).toBeUndefined();
    d.m.set(k, JSON.stringify(p));
    expect(proje.uygulamaListeDurumu(p.id)?.hukum).toBe("uygun");
    //  Ofis standardı değişti:  hesap onunla yapılmadı
    d.m.set("asansor:ofis", JSON.stringify({ beta: "5000" }));
    expect(proje.uygulamaListeDurumu(p.id)).toBeUndefined();
    //  Proje adı ve kapak hesaba girmez
    d.m.delete("asansor:ofis");
    d.m.set(k, JSON.stringify({ ...p, kimlik: { ...p.kimlik, project_title: "B" }, kapak: { city: "Konya" } }));
    expect(proje.uygulamaListeDurumu(p.id)?.hukum).toBe("uygun");
  });

  it("durum proje kaydına yazılmaz, aynı durum yeniden yazılmaz;  proje silinince durumu da gider", async () => {
    const d = sahteDepo();
    const { proje, durum } = await moduller(d);
    const p = proje.yeniUygulama();
    const once = d.m.get(`asansor:proje:${p.id}`);
    const x = { iz: proje.uygulamaIzi(p, {}), hukum: "durdu" as const, adet: 1, uygunDegil: 0 };
    durum.durumYaz(p.id, x);
    durum.durumYaz(p.id, { ...x });
    expect(d.yazilan.filter((k) => k === `asansor:durum:${p.id}`)).toHaveLength(1);
    expect(d.m.get(`asansor:proje:${p.id}`)).toBe(once);
    proje.projeSil(p.id);
    expect(d.m.has(`asansor:durum:${p.id}`)).toBe(false);
  });

  it("avan:  listede kendi kaydından;  boşsa yok;  zamanı yalnız içerik değişince", async () => {
    const d = sahteDepo();
    const { avan } = await moduller(d);
    expect(avan.avanOzeti()).toBeNull();
    avan.avanProjesiniYaz(avan.BOS_AVAN);
    expect(avan.avanOzeti()).toBeNull();
    const p = { ...avan.BOS_AVAN, trafik: { N: "10" } };
    avan.avanProjesiniYaz(p);
    expect(avan.avanOzeti()).toMatchObject({ id: "avan", tur: "avan", ad: "Adsız avan projesi" });
    const zaman = d.m.get("asansor:avan-zaman");
    expect(Number(zaman)).toBeGreaterThan(0);
    //  Aynı hâl ( ekran açıldı, başka sekmeden geldi ):  yazılmaz, zaman değişmez
    const yazma = d.yazilan.length;
    avan.avanProjesiniYaz(JSON.parse(JSON.stringify(p)));
    expect(d.yazilan.length).toBe(yazma);
    avan.avanProjesiniYaz({ ...p, kapak: { project_title: "A Blok" } });
    expect(avan.avanOzeti()?.ad).toBe("A Blok");
  });

  it("avan:  kapak hesaba girmez;  girdi ve avan ofis standardı değişince 'Hesaplanmadı'", async () => {
    const d = sahteDepo();
    const { avan, durum } = await moduller(d);
    const p = { ...avan.BOS_AVAN, trafik: { N: "10" } };
    avan.avanProjesiniYaz(p);
    durum.durumYaz("avan", { iz: avan.avanIzi(p, {}), hukum: "durdu", adet: 0, uygunDegil: 0 });
    expect(avan.avanListeDurumu()?.hukum).toBe("durdu");
    avan.avanProjesiniYaz({ ...p, kapak: { project_title: "A Blok" } });
    expect(avan.avanListeDurumu()?.hukum).toBe("durdu");
    d.m.set("asansor:avan-ofis", JSON.stringify({ kuyu_armatur_W: "40" }));
    expect(avan.avanListeDurumu()).toBeUndefined();
    d.m.delete("asansor:avan-ofis");
    avan.avanProjesiniYaz({ ...p, trafik: { N: "11" } });
    expect(avan.avanListeDurumu()).toBeUndefined();
  });
});
