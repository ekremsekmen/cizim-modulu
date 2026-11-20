import { describe, expect, it } from "vitest";
import { baslikAdi, seritAdi, seritYerlesimi, seviyeHarfi } from "./serit";

describe("çizim şeridinin adları", () => {
  it("başlığın adı ve seviye harfi", () => {
    expect(baslikAdi("KUYU PLANI  C-C  ( kabin hizasından yatay kesit )")).toBe("KUYU PLANI  C-C");
    expect(seviyeHarfi("KUYU PLANI  C-C  ( kabin hizasından yatay kesit )")).toBe("C-C");
    expect(seviyeHarfi("A-A KUYU DÜŞEY KESİTİ  ( yan — kabin en alt durakta )")).toBe("A-A");
    //  Sorunlu kipte harf yok;  parantezin içindeki harf sayılmaz
    expect(seviyeHarfi("KUYU DİBİ PLANI  ( kuyu tabanından yatay kesit )")).toBeNull();
    expect(seviyeHarfi("MAKİNE DAİRESİ PLANI  ( B-B hizası )")).toBeNull();
  });

  it("ad sunucudan;  yoksa başlıktan, harfsiz", () => {
    expect(seritAdi({ baslik: "KUYU PLANI  C-C", kisa: "Kuyu planı" })).toBe("Kuyu planı");
    expect(seritAdi({ baslik: "KUYU ÜSTÜ PLANI  F-F  ( makine dairesiz )" })).toBe("Kuyu üstü planı");
    expect(seritAdi({ baslik: "İÇ GÖRÜNÜŞ", kisa: null })).toBe("İç görünüş");
  });
});

describe("çizim şeridinin yerleşimi", () => {
  const enler = [100, 100, 100, 100];

  it("hepsi sığarsa hepsi ( sınırda da )", () => {
    expect(seritYerlesimi(enler, 50, 400, 2)).toEqual({ gorunen: [0, 1, 2, 3], gizli: [] });
  });

  it("sığmayanlar sırayla Diğer'e", () => {
    expect(seritYerlesimi(enler, 50, 300)).toEqual({ gorunen: [0, 1], gizli: [2, 3] });
    //  Açık çizim sığanlardansa değişen yok
    expect(seritYerlesimi(enler, 50, 300, 1)).toEqual({ gorunen: [0, 1], gizli: [2, 3] });
  });

  it("açık çizim hep şeritte:  sığanlardan birinin yerine geçer", () => {
    expect(seritYerlesimi(enler, 50, 300, 3)).toEqual({ gorunen: [0, 3], gizli: [1, 2] });
  });

  it("sıra korunur:  sığmayandan sonrakiler sığsa da atlanmaz", () => {
    expect(seritYerlesimi([100, 200, 50, 50], 50, 300)).toEqual({ gorunen: [0], gizli: [1, 2, 3] });
  });

  it("alan açık çizime de yetmezse yine o görünür", () => {
    expect(seritYerlesimi(enler, 50, 80, 2)).toEqual({ gorunen: [2], gizli: [0, 1, 3] });
    expect(seritYerlesimi(enler, 50, 80)).toEqual({ gorunen: [], gizli: [0, 1, 2, 3] });
  });
});
