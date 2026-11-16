import { describe, expect, it } from "vitest";
import { azamiKonum, DUVARLAR, kapiKutusu, kapiYeri, odayiBul, type KapiBilgisi, type Oda } from "./kapiTasima";

//  630 kg makine daireli taslağın odası:  2600 × 3800, duvar 200, kapı 800
const ODA: Oda = { x0: -400, y0: -900, x1: 2200, y1: 2900, t: 200 };
const kapi = (duvar: KapiBilgisi["duvar"], konum = 300): KapiBilgisi => ({ duvar, konum, en: 800, genislik: 2600, derinlik: 3800 });

describe("makine dairesi kapısını sürükleme", () => {
  it("oda, kapının çizimdeki kutusundan bulunur — dört duvarda da ( gidiş – dönüş )", () => {
    for (const d of DUVARLAR) {
      const k = kapi(d, 470);
      expect(odayiBul(k, kapiKutusu(ODA, k, k.en))).toEqual(ODA);
    }
  });

  it("kapı boşluğu duvarın kalınlığı içindedir", () => {
    expect(kapiKutusu(ODA, { duvar: "Arka", konum: 300 }, 800)).toEqual({ x: -100, y: 2900, w: 800, h: 200 });
    expect(kapiKutusu(ODA, { duvar: "Ön", konum: 300 }, 800)).toEqual({ x: -100, y: -1100, w: 800, h: 200 });
    expect(kapiKutusu(ODA, { duvar: "Sol", konum: 300 }, 800)).toEqual({ x: -600, y: -600, w: 200, h: 800 });
    expect(kapiKutusu(ODA, { duvar: "Sağ", konum: 300 }, 800)).toEqual({ x: 2200, y: -600, w: 200, h: 800 });
  });

  it("kendi duvarında kayar:  tutuş noktası korunur, 10 mm adım, iki uçta durur", () => {
    const k = kapi("Arka");
    //  Kapının başı x = −100;  işaretçi başından 250 ötede tutmuş
    expect(kapiYeri(ODA, k, { x: 150 + 123, y: 3000 }, 250)).toEqual({ duvar: "Arka", konum: 420 });
    expect(kapiYeri(ODA, k, { x: 9000, y: 3000 }, 250)).toEqual({ duvar: "Arka", konum: 1800 });
    expect(kapiYeri(ODA, k, { x: -9000, y: 3000 }, 250)).toEqual({ duvar: "Arka", konum: 10 });
  });

  it("işaretçi başka duvara yaklaşınca kapı o duvara geçer, işaretçiye ortalanır", () => {
    const k = kapi("Arka");
    expect(kapiYeri(ODA, k, { x: 2250, y: 1000 }, 250)).toEqual({ duvar: "Sağ", konum: 1500 });
    expect(kapiYeri(ODA, k, { x: -450, y: 1000 }, 250)).toEqual({ duvar: "Sol", konum: 1500 });
    expect(kapiYeri(ODA, k, { x: 900, y: -1000 }, 250)).toEqual({ duvar: "Ön", konum: 900 });
    //  Yan duvarda "köşeden uzaklık" ön köşeden ( y0 ) ölçülür;  uçta durur
    expect(kapiYeri(ODA, k, { x: 2300, y: 2890 }, 250, "Sağ")).toEqual({ duvar: "Sağ", konum: 3000 });
  });

  it("köşede titremez:  öteki duvar belirgin biçimde yakın olmadıkça geçilmez", () => {
    const k = kapi("Arka");
    //  Sağ arka köşenin içinde, sağ duvara 20 mm daha yakın — arka duvarda kalır
    expect(kapiYeri(ODA, k, { x: 2100, y: 2780 }, 250).duvar).toBe("Arka");
    expect(kapiYeri(ODA, k, { x: 2100, y: 2600 }, 250).duvar).toBe("Sağ");
    //  Sağdayken aynı noktada sağda kalır
    expect(kapiYeri(ODA, k, { x: 2090, y: 2810 }, 250, "Sağ").duvar).toBe("Sağ");
  });

  it("kapının sığmadığı duvara geçilmez", () => {
    const dar: KapiBilgisi = { duvar: "Sol", konum: 300, en: 800, genislik: 700, derinlik: 3800 };
    expect(azamiKonum(dar, "Arka")).toBeNull();
    expect(azamiKonum(dar, "Sol")).toBe(3000);
    const o: Oda = { x0: 0, y0: 0, x1: 700, y1: 3800, t: 200 };
    expect(kapiYeri(o, dar, { x: 350, y: 3900 }, 100).duvar).not.toBe("Arka");
    //  Ondalıklı oda ( avan seçicisi ):  uç adıma iner
    expect(azamiKonum({ en: 800, genislik: 1792.2, derinlik: 3704.4 }, "Arka")).toBe(990);
  });
});
