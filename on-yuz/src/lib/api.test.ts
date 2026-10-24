import { afterEach, describe, expect, it, vi } from "vitest";
import { api, indir } from "./api";

/**  Başlığı gelmiş, gövdesi yarıda kesilen yanıt:  bağlantı dosya inerken koptu  */
function yaridaKesilen(tur: string) {
  return new Response(
    new ReadableStream({
      start(c) {
        c.enqueue(new TextEncoder().encode(tur.includes("json") ? '{"hata": "Kapak üre' : "%PDF-1.7"));
        c.error(new TypeError("network error"));
      },
    }),
    { status: 200, headers: { "Content-Type": tur } },
  );
}

describe("indirme fırlatmaz:  düğmeler yalnız dönen hatayı gösterir ( 24 Eki )", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("dosya inerken bağlantı koparsa hata döner ( sessizce düşüyordu:  dosya yok, ileti yok )", async () => {
    vi.stubGlobal("fetch", async () => yaridaKesilen("application/pdf"));
    await expect(indir("kapak-pdf", {})).resolves.toEqual({ hata: expect.stringMatching(/bağlantı koptu/) });
  });

  it("sunucunun ret iletisi yarıda kesilirse de", async () => {
    vi.stubGlobal("fetch", async () => yaridaKesilen("application/json"));
    await expect(indir("uygulama-pdf", {})).resolves.toEqual({ hata: expect.stringMatching(/okunamadı/) });
  });

  it("bağlantı hiç kurulamazsa ( eskisi gibi )", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("Failed to fetch");
    });
    await expect(indir("proje-dwg", {})).resolves.toEqual({ hata: expect.stringMatching(/Sunucuya ulaşılamadı/) });
  });
});

describe("ret iletisi ucun biçiminde gelir ( 24 Eki )", () => {
  afterEach(() => vi.unstubAllGlobals());
  const yanit = (govde: unknown, durum: number) => async () =>
    new Response(JSON.stringify(govde), { status: durum, headers: { "Content-Type": "application/json" } });

  it("boyut sınırının listesi avan ucunda metin olur ( avan ekranı .trim()'de çöküyordu )", async () => {
    vi.stubGlobal("fetch", yanit({ aktif: false, hata: ["İstek çok büyük", "ikinci"] }, 413));
    await expect(api.avan({})).resolves.toMatchObject({ hata: "İstek çok büyük\nikinci" });
    await expect(api.trafik({})).resolves.toMatchObject({ hata: "İstek çok büyük\nikinci" });
  });

  it("bilinmeyen adresin metni uygulama ucunda liste olur ( ekran .map() ile okur )", async () => {
    vi.stubGlobal("fetch", yanit({ hata: "Bulunamadı" }, 404));
    const istek = { asansorler: [{}], proje_geneli: {}, sabitler: {} };
    await expect(api.hesap(istek)).resolves.toEqual({ hata: ["Bulunamadı"] });
    await expect(api.cizimler(istek, 0)).resolves.toEqual({ hata: ["Bulunamadı"] });
    await expect(api.care(istek, 0, null)).resolves.toEqual({ hata: ["Bulunamadı"] });
  });

  it("ucun kendi biçimi ve hatasız yanıt olduğu gibi kalır", async () => {
    vi.stubGlobal("fetch", yanit({ hata: null, ozet: { adet: 1 } }, 200));
    await expect(api.trafik({})).resolves.toEqual({ hata: null, ozet: { adet: 1 } });
    vi.stubGlobal("fetch", yanit({ aktif: false, hata: ["Kuyu dar."] }, 200));
    await expect(api.olcu({ asansorler: [{}], proje_geneli: {}, sabitler: {} }, 0, "plan", 1, "100")).resolves.toEqual({
      aktif: false,
      hata: ["Kuyu dar."],
    });
    vi.stubGlobal("fetch", yanit({ aktif: true, cizimler: [] }, 200));
    await expect(api.cizimler({ asansorler: [{}], proje_geneli: {}, sabitler: {} }, 0)).resolves.toEqual({ aktif: true, cizimler: [] });
  });
});
