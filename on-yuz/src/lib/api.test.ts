import { afterEach, describe, expect, it, vi } from "vitest";
import { indir } from "./api";

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
