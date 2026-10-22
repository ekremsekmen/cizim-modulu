import { describe, expect, it } from "vitest";
import type { AvanKoprusu, Secenekler } from "./api";
import { avanDosyaGovdesi, avanDosyasiMi, avanOku, BOS_AVAN, manuelKMetni, trafikFarki, yeniAvanAcilisi, type AvanProjesi } from "./avan";

/*  Seçenekler /api/secenekler'in bu testin kullandığı alt kümesidir;  listeler
    sunucununkiyle aynı ( 18 Eki ), sabit şeması birkaç sabite kısaltıldı.  */
const SEC = {
  bina_tipleri: ["Konut", "Kamu Binaları", "Katlı Otopark"],
  hizlar: [0.63, 1, 1.6, 1.75, 2, 2.5, 3, 3.5, 5, 6],
  kapasiteler: [6, 8, 10, 13, 15, 16, 20, 25, 30],
  kapi_genislikleri: [700, 800, 900, 1000, 1100, 1200, 1300],
  kapi_tipleri: ["Teleskopik Otomatik", "Merkezden Açılan Oto.", "Kabin İçi Oto. Kat K.Ç."],
  makine_tipleri: { Dişlisiz: 0.85, Dişli: 0.5 },
  aski_oranlari: { "1:1": 1, "2:1": 2 },
  kesitler: [1.5, 2.5, 4, 6, 10, 16],
  nufus_kalemleri: ["KONUT — İlk yatak odası", "KONUT — Diğer oda"],
  ofis_varsayilan: { U: 380, S1: 6, kablo_tipi: "NHXMH FE180" },
  sabit_b: { q_denge: 0.5 },
  sabit_sema: {
    gruplar: [{ baslik: "①", aciklama: "", alanlar: ["q_denge", "U", "S1", "kablo_tipi"] }],
    etiket: {
      q_denge: ["q — Denge faktörü", ""],
      U: ["U — Şebeke gerilimi (V)", ""],
      S1: ["S1 — Kolon hattı kesiti (mm²)", ""],
      kablo_tipi: ["Kablo tipi", ""],
    },
    varsayilan: { q_denge: 0.5, U: 380, S1: 6, kablo_tipi: "NHXMH FE180" },
    metin: ["kablo_tipi"],
  },
} as unknown as Secenekler;

const KOPRU: AvanKoprusu = {
  tip: "Konut",
  N: 11,
  bodrum: 0,
  h: 3,
  adet: 2,
  asansorler: [
    { P: 10, V: 1.6, toplam_seyahat: 33 },
    { P: 16, V: 1.6, toplam_seyahat: 33 },
  ],
};

const PROJE: AvanProjesi = {
  trafik: { bina_tipi: "Konut", bina_yuksekligi: "39,98", N: "11", h: "3", hizli1: "44", manuel_k: "0,4" },
  ekNufus: [{ kalem: "KONUT — Diğer oda", miktar: "4", aciklama: "çatı katı" }],
  trafikAsansorleri: [
    { P: "10", kapi_genisligi: "900", kapi_tipi: "Teleskopik Otomatik" },
    { P: "16", kapi_genisligi: "900", kapi_tipi: "Teleskopik Otomatik", V: "1.6", manuel_ta: "2,1" },
  ],
  ortak: { mk_yok: "false", temel_a: "26,55", temel_b: "16,4", mk_uzunluk: "4000" },
  avanAsansorleri: [{ tanim: "İnsan", Hk: "38,50", kuyu_genisligi: "1800" }, { makine_tipi: "Dişli", S1: "10" }, {}, {}],
  kapak: { project_title: "A Blok", city: "Konya" },
};

/**  Eski arayüzün kaydettiği dosya:  kutular hep dolu ( seçimler, verim, ofis )  */
const ESKI = {
  __mod: "avan",
  __surum: 1,
  alanlar: {
    __mod: "avan",
    c_bina_tipi: "Konut",
    c_bina_yuksekligi: "39,98",
    c_N: "11",
    c_h: "3",
    c_hizli1: "44",
    c_manuel_V: "",
    c_taahhut: "Yok",
    c_P1: "10",
    c_kg1: "900",
    c_kt1: "Teleskopik Otomatik",
    c_V1: "",
    c_P2: "",
    c_kg2: "900",
    __trafik_adet: 1,
    __eknufus_c: [],
    a_aktif1: true,
    a_kapasite1: "10",
    a_V1: "1.6",
    a_tanim1: "İnsan",
    a_makine_tipi1: "Dişlisiz",
    a_eta1: "0,85",
    a_i_palanga1: "2",
    a_denge_zinciri1: "Yok",
    a_agirlik_guvenlik_tertibati1: "Yok",
    a_S11: "",
    a_aktif2: false,
    a_mk_yok: true,
    a_temel_a: "26,55",
    k_project_title: "Örnek",
    of_U: "380",
    of_S1: "6",
    of_kablo_tipi: "NHXMH FE180",
    sb_q_denge: "0,5",
  },
};

function oku(d: unknown, ofis = {}) {
  const o = avanOku(JSON.stringify(d), SEC, ofis);
  if (!o.tamam) throw new Error(o.hata);
  return o;
}

describe("avan dosyası — eski arayüzün biçimi", () => {
  it("eski arayüzün kutu kimlikleriyle yazılır", () => {
    const d = avanDosyaGovdesi(PROJE, SEC, { U: "400" }, KOPRU);
    expect(d.__mod).toBe("avan");
    expect(d.alanlar).toMatchObject({
      c_bina_tipi: "Konut",
      c_manuel_k: "0,4",
      c_taahhut: "Yok",
      c_P2: "16",
      c_kg2: "900",
      c_mta2: "2,1",
      c_P4: "",
      __trafik_adet: 2,
      //  avan kartları trafikten;  eski arayüz bunu __avan_trf'ten bilir
      a_aktif1: true,
      a_aktif2: true,
      a_aktif3: false,
      a_kapasite2: "16",
      a_V2: "1.6",
      __avan_trf: { 1: { P: 10, V: 1.6 }, 2: { P: 16, V: 1.6 } },
      //  seçim ve verim eski formda hep doludur:  etkin değer
      a_makine_tipi1: "Dişlisiz",
      a_eta1: "0,85",
      a_makine_tipi2: "Dişli",
      a_eta2: "0,5",
      a_i_palanga1: "2",
      a_S12: "10",
      a_mk_yok: false,
      a_mk_uzunluk: "4000",
      k_project_title: "A Blok",
      k_city: "Konya",
      //  ofis standardı:  of_ ( ofis varsayılanı ) / sb_ ( motor sabiti ) ayrımı korunur
      of_U: "400",
      of_S1: "6",
      sb_q_denge: "0,5",
    });
    expect(d.alanlar.__eknufus_c).toEqual([{ kalem: "KONUT — Diğer oda", miktar: "4", aciklama: "çatı katı" }]);
  });

  it("yazılan dosya aynı projeyle geri okunur", () => {
    const o = oku(avanDosyaGovdesi(PROJE, SEC, {}, KOPRU));
    expect(o.proje).toEqual(PROJE);
    expect(o.ofisFarki).toEqual([]);
    expect(o.taninmayan).toEqual([]);
    expect(trafikFarki(o.dosyaAvani, KOPRU)).toBeNull();
  });

  it("eski dosyanın dolu varsayılanları yazılmamış sayılır", () => {
    const o = oku(ESKI);
    expect(o.proje.avanAsansorleri[0]).toEqual({ tanim: "İnsan" });
    expect(o.proje.trafik).toEqual({ bina_tipi: "Konut", bina_yuksekligi: "39,98", N: "11", h: "3", hizli1: "44" });
    expect(o.proje.trafikAsansorleri).toEqual([{ P: "10", kapi_genisligi: "900", kapi_tipi: "Teleskopik Otomatik" }]);
    expect(o.proje.ortak).toEqual({ temel_a: "26,55", mk_yok: "true" });
    expect(o.ofisFarki).toEqual([]);
  });

  it("sütun adedi yazılmamışsa dolu kapasitelerden", () => {
    const { __trafik_adet: _, ...alanlar } = { ...ESKI.alanlar, c_P2: "16" };
    expect(oku({ alanlar }).proje.trafikAsansorleri).toHaveLength(2);
  });

  it("ondalık virgüllü seçim tanınır, listede olmayan alınmaz ve söylenir", () => {
    const o = oku({ alanlar: { ...ESKI.alanlar, c_V1: "1,6", c_kt1: "Kaldırılmış Kapı", a_S11: "7" } });
    expect(o.proje.trafikAsansorleri[0].V).toBe("1.6");
    expect(o.proje.trafikAsansorleri[0].kapi_tipi).toBeUndefined();
    expect(o.proje.avanAsansorleri[0].S1).toBeUndefined();
    expect(o.taninmayan).toEqual(["Kapı tipi = Kaldırılmış Kapı", "S1 ( 1. avan asansörü ) = 7"]);
  });

  it("dosyadaki farklı ofis standardı uygulanmaz, etiketiyle söylenir", () => {
    const o = oku({ alanlar: { ...ESKI.alanlar, of_U: "400", sb_q_denge: "0.5" } });
    expect(o.ofisFarki).toEqual(["U — Şebeke gerilimi (V)"]);
    //  bu tarayıcının değeri de karşılaştırılır
    expect(oku(ESKI, { U: "400" }).ofisFarki).toEqual(["U — Şebeke gerilimi (V)"]);
  });

  it("dosyadaki avan trafikten farklıysa söylenir", () => {
    const o = oku({ alanlar: { ...ESKI.alanlar, a_kapasite1: "13" } });
    const k = { ...KOPRU, asansorler: KOPRU.asansorler.slice(0, 1) };
    expect(trafikFarki(o.dosyaAvani, k)).toContain("13 kişi · 1,6 m/s idi;  trafik hesabı 10 kişi · 1,6 m/s");
    expect(trafikFarki(oku(ESKI).dosyaAvani, k)).toBeNull();
  });

  it("uygulama dosyası ve bozuk dosya reddedilir", () => {
    expect(avanOku(JSON.stringify({ __mod: "uygulama", alanlar: {} }), SEC, {})).toEqual({
      tamam: false,
      hata: expect.stringMatching(/uygulama projesi dosyası — açılış sayfasındaki/),
    });
    expect(avanOku("{", SEC, {}).tamam).toBe(false);
    expect(avanOku(JSON.stringify({ x: 1 }), SEC, {}).tamam).toBe(false);
  });

  it("başlıksız eski biçim de avan dosyasıdır", () => {
    expect(avanDosyasiMi(ESKI.alanlar)).toBe(true);
    expect(avanDosyasiMi({ c_N: "5" })).toBe(true);
    expect(avanDosyasiMi({ __mod: "uygulama", m_adet: "1" })).toBe(false);
    expect(avanDosyasiMi(BOS_AVAN)).toBe(false);
  });
});

describe("manuel k kutusunun metni", () => {
  //  Sunucunun Tablo-10'undan ( motor/avan/tablolar.TABLO_10 — k_tipi )
  const sec = {
    tablo_10: {
      Konut: { k_tipi: "Konut" },
      "Kamu Binaları": { k_tipi: "İş Merkezi" },
      "Karma Binalar (İşyeri ve Konut)": { k_tipi: null },
      "Poliklinik Binaları ve Yaşlı Bakım Ev.": { k_tipi: null },
    },
  };
  it("Kamu'da manuel k İş Merkezi oranının önüne geçer", () => {
    expect(manuelKMetni("Kamu Binaları", sec)).toEqual({
      ipucu: "0 – 1;  boşsa İş Merkezi oranı ( Kamu binaları Tablo-9'da yok )",
      yer: "İş Merkezi",
    });
  });
  it("Tablo-9'da olmayan tipte zorunlu", () => {
    for (const b of ["Karma Binalar (İşyeri ve Konut)", "Poliklinik Binaları ve Yaşlı Bakım Ev."])
      expect(manuelKMetni(b, sec).yer).toBe("girin");
  });
  it("Tablo-9'u olan tipte girilemez;  tip seçilmeden yalnız aralık", () => {
    expect(manuelKMetni("Konut", sec).ipucu).toContain("girilemez");
    expect(manuelKMetni("", sec)).toEqual({ ipucu: "0 – 1", yer: "" });
  });
});

describe("yeni avan projesi", () => {
  it("açık proje geri alınabilir;  boş projede bildirim yok", () => {
    const acik: AvanProjesi = { ...BOS_AVAN, kapak: { project_title: "Eski avan" } };
    const a = yeniAvanAcilisi(acik);
    expect(a?.proje).toEqual(BOS_AVAN);
    expect(a?.onceki).toEqual(acik);
    expect(a?.bildirim).toContain("Geri al");
    expect(yeniAvanAcilisi(BOS_AVAN)).toBeNull();
  });
});
