import { describe, expect, it } from "vitest";
import yazimlar from "./kot-yazimlari.json";
import {
  araligiYaz,
  hizliDoldur,
  kaydir,
  kotOku,
  kotYaz,
  kotlaGecis,
  kotlaMi,
  kotlariOku,
  olcuyleGecis,
  yapistir,
} from "./kotlar";
import { formHatalari, kipGizlileri, type UygulamaProjesi } from "./proje";
import { SEMA } from "./test-semasi";

describe("kot yazımı — sunucuyla aynı liste ( testler/test_kotlar.py da okur )", () => {
  it.each(yazimlar.yazimlar as [string, number | null][])("%s → %s", (m, mm) => {
    expect(kotOku(m)).toBe(mm);
  });
  it("yazılan kot sunucunun kot_metni'si gibi ve geri okunur", () => {
    for (const mm of [0, 3200, -7000, 57600, -8805, 62300]) expect(kotOku(kotYaz(mm))).toBe(mm);
    expect([kotYaz(0), kotYaz(3200), kotYaz(-7000), kotYaz(-8805)]).toEqual(["±0,00", "+3,20", "-7,00", "-8,805"]);
  });
});

describe("durak kotları", () => {
  it("noktalı virgül ya da satır;  okunamayan null kalır", () => {
    expect(kotlariOku("−7,00; −3,50; ±0,00; +3,20;")).toEqual([-7000, -3500, 0, 3200]);
    expect(kotlariOku("0\n3,2\nx")).toEqual([0, 3200, null]);
    expect(kotlaMi({ durak_kotlari: "  " })).toBe(false);
    expect(kotlaMi({ durak_kotlari: "0; 3" })).toBe(true);
  });
  it("yapıştırma:  sekme ve satır ayırır, yukarıdan aşağı yazılmışsa çevrilir", () => {
    expect(yapistir("+57,60\n+54,40\n±0,00\n-7,00")).toBe("-7,00; ±0,00; +54,40; +57,60");
    expect(yapistir("-7,00\t-3,50\t±0,00")).toBe("-7,00; -3,50; ±0,00");
    //  Okunamayan varsa sıra korunur:  sebebi sunucu söyler
    expect(yapistir("3,20\nx\n0")).toBe("3,20; x; 0");
  });
  it("hızlı doldur", () => {
    expect(hizliDoldur(4, -3500, 3000)).toBe("-3,50; -0,50; +2,50; +5,50");
  });
});

describe("fark yazılınca üstteki satırlar kayar ( kat-kat arası )", () => {
  const h = {
    durak_kotlari: "-7,00; -3,50; ±0,00; +3,20",
    kuyu_dibi_kotu: "-8,80",
    kuyu_tavani_kotu: "+7,80",
    md_zemini_kotu: "+6,40",
  };
  it("2. – 3. durak arası 3.500 → 4.000:  3. durak ve üstü 500 yukarı, kuyu dibi yerinde", () => {
    expect(araligiYaz(h, 2, 4000)).toEqual({
      durak_kotlari: "-7,00; -3,50; +0,50; +3,70",
      kuyu_tavani_kotu: "+8,30",
      md_zemini_kotu: "+6,90",
    });
  });
  it("bütün kotlar kayar ( mimarın ±0,00'ına )", () => {
    expect(kaydir(h, 7000)).toEqual({
      durak_kotlari: "±0,00; +3,50; +7,00; +10,20",
      kuyu_dibi_kotu: "-1,80",
      kuyu_tavani_kotu: "+14,80",
      md_zemini_kotu: "+13,40",
    });
  });
  it("okunamayan kot varsa fark uygulanmaz", () => {
    expect(araligiYaz({ durak_kotlari: "0; x; 6" }, 2, 3000)).toBeNull();
  });
});

describe("kipler arasında kayıpsız geçiş", () => {
  const varsayilan: Record<string, number> = {
    durak_adedi: 8,
    seyir_mesafesi: 21,
    son_kat_yuksekligi: 4200,
    kuyu_dibi: 1600,
    tabliye_yuksekligi: 1200,
    kuyu_duvar_kalinligi: 150,
  };
  const d = (k: string) => varsayilan[k];
  it("ölçüyle → kotla:  en alt durak ±0,00, ölçü kutuları silinir", () => {
    const y = kotlaGecis(d, undefined, true);
    expect(y.durak_kotlari).toBe("±0,00; +3,00; +6,00; +9,00; +12,00; +15,00; +18,00; +21,00");
    expect([y.kuyu_dibi_kotu, y.kuyu_tavani_kotu, y.md_zemini_kotu]).toEqual(["-1,60", "+25,20", "+24,15"]);
    expect([y.seyir_mesafesi, y.durak_adedi, y.kat_yukseklikleri, y.tabliye_yuksekligi]).toEqual(["", "", "", ""]);
  });
  it("kat yükseklikleri yazılmışsa onlardan;  eşit olmayan bölme mm'ye, seyir aynı", () => {
    expect(kotlaGecis(d, "3400; 3000; 3000; 3000; 3000; 3000; 2600", false).durak_kotlari).toBe(
      "±0,00; +3,40; +6,40; +9,40; +12,40; +15,40; +18,40; +21,00",
    );
    const e = (k: string) => ({ ...varsayilan, durak_adedi: 12, seyir_mesafesi: 35.25 })[k];
    const kotlar = kotlariOku(kotlaGecis(e, undefined, false).durak_kotlari);
    expect(kotlar[kotlar.length - 1]).toBe(35250);
  });
  it("kotla → ölçüyle:  sunucunun türettikleri kutulara, kotlar silinir", () => {
    const y = olcuyleGecis(
      { durak_adedi: 21, seyir_mesafesi: 64.6, kat_yukseklikleri: [3500, 3500, 3200], kuyu_dibi: 1800, son_kat_yuksekligi: 4600, tabliye_yuksekligi: 1500 },
      true,
    );
    expect(y).toMatchObject({
      durak_adedi: "21",
      seyir_mesafesi: "64,6",
      kat_yukseklikleri: "3500; 3500; 3200",
      kuyu_dibi: "1800",
      son_kat_yuksekligi: "4600",
      tabliye_yuksekligi: "1500",
      durak_kotlari: "",
      kuyu_dibi_kotu: "",
    });
    //  Makine dairesizde tabliyeye dokunulmaz
    expect("tabliye_yuksekligi" in olcuyleGecis({ tabliye_yuksekligi: 1500 }, false)).toBe(false);
  });
});

describe("ön yüzün denetimi öbür kipin alanına bakmaz", () => {
  const proje = (h: Record<string, string>): UygulamaProjesi => ({
    id: "t",
    tur: "uygulama",
    kimlik: { project_title: "", owner: "", sheet_no: "" },
    asansorler: [h],
    proje_geneli: {},
    guncellendi: 0,
  });
  it("kotla girişte durak adedi okunmaz:  kural dışı değeri projeyi durdurmaz", () => {
    expect(kipGizlileri(SEMA, { durak_kotlari: "0; 3" }).has("durak_adedi")).toBe(true);
    expect(formHatalari(SEMA, proje({ durak_kotlari: "0; 3", durak_adedi: "250" }))).toEqual([]);
    expect(formHatalari(SEMA, proje({ durak_adedi: "250" }))).toHaveLength(1);
  });
});
