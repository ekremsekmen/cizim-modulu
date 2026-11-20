import { afterEach, describe, expect, it, vi } from "vitest";
import { akisDosyasi, api, base64Bayt, indir, indirAkisli } from "./api";

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
    //  Düzeltme ( 20 Kas ) akışlı istekle — XHR;  akış vermeyen ret yine liste
    vi.stubGlobal("XMLHttpRequest", sahteXhr(JSON.stringify({ hata: "Bulunamadı" }), 1000, { tur: "application/json", durum: 404 }));
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

/**  Sahte XMLHttpRequest:  gövde parça parça gelir ( her parçada ilerleme olayı ), sonra yükleme
     biter ya da bağlantı kopar  */
function sahteXhr(metin: string, parca: number, secenek: { tur?: string; durum?: number; kopar?: boolean } = {}) {
  const tur = secenek.tur ?? "application/x-ndjson";
  return class {
    responseText = "";
    status = 0;
    onprogress: (() => void) | null = null;
    onload: (() => void) | null = null;
    onerror: (() => void) | null = null;
    onabort: (() => void) | null = null;
    basliklar: Record<string, string> = {};
    iptal = false;
    open() {}
    setRequestHeader(k: string, v: string) {
      this.basliklar[k] = v;
    }
    getResponseHeader(k: string) {
      return k.toLowerCase() === "content-type" ? tur : null;
    }
    abort() {
      this.iptal = true;
      this.onabort?.();
    }
    send() {
      this.status = secenek.durum ?? 200;
      void (async () => {
        for (let k = 0; k < metin.length; k += parca) {
          await Promise.resolve();
          if (this.iptal) return;
          this.responseText += metin.slice(k, k + parca);
          this.onprogress?.();
        }
        if (secenek.kopar) this.onerror?.();
        else this.onload?.();
      })();
    }
  };
}

describe("avan çiziminin akışlı yanıtı ( 17 Kas — aramanın aşamaları )", () => {
  afterEach(() => vi.unstubAllGlobals());
  const ilerleme = (kod: string, sinama: number) => ({
    ilerleme: { asamalar: [{ kod, surer: kod, bitti: kod, ayrinti: "", t: 0 }], sinama, gecen: 0.2 },
  });
  const satirla = (s: unknown[]) => s.map((x) => JSON.stringify(x)).join("\n") + "\n";

  it("aşamalar geldikçe ( satır ortasından bölünse de ) bildirilir, sonuç son satırdan", async () => {
    const metin = satirla([ilerleme("paket", 0), ilerleme("yerlesim", 3), { sonuc: { durum: "uygun", sure: 1.2 } }]);
    vi.stubGlobal("XMLHttpRequest", sahteXhr(metin, 7));
    const gelen: number[] = [];
    await expect(api.avanCizimleri({}, 0, undefined, (d) => gelen.push(d.sinama))).resolves.toEqual({ durum: "uygun", sure: 1.2 });
    expect(gelen).toEqual([0, 3]);
  });

  it("son satırın sonunda satır sonu olmasa da okunur;  hata metni ucun biçiminde", async () => {
    vi.stubGlobal("XMLHttpRequest", sahteXhr(JSON.stringify({ sonuc: { durum: "hata", hata: "ÇİZİM HATASI: x" } }), 5));
    await expect(api.avanCizimleri({}, 0)).resolves.toMatchObject({ durum: "hata" });
  });

  it("sonuç gelmeden akış koparsa ya da biterse hata ( yarıda kalan aramayı sonuç sanmaz )", async () => {
    vi.stubGlobal("XMLHttpRequest", sahteXhr(satirla([ilerleme("paket", 0)]), 9, { kopar: true }));
    await expect(api.avanCizimleri({}, 0)).rejects.toThrow();
    vi.stubGlobal("XMLHttpRequest", sahteXhr(satirla([ilerleme("paket", 0)]), 9));
    await expect(api.avanCizimleri({}, 0)).rejects.toThrow(/yarıda/);
  });

  it("istek bırakılınca ( girdi değişti ) iptal hatası:  sonuç beklenmez", async () => {
    vi.stubGlobal("XMLHttpRequest", sahteXhr(satirla([ilerleme("paket", 0), { sonuc: { durum: "uygun" } }]), 3));
    const k = new AbortController();
    const s = api.avanCizimleri({}, 0, k.signal);
    k.abort();
    await expect(s).rejects.toMatchObject({ name: "AbortError" });
  });

  it("akış vermeyen yanıt ( sunucunun ret iletisi ) tek JSON okunur", async () => {
    vi.stubGlobal(
      "XMLHttpRequest",
      sahteXhr(JSON.stringify({ hata: ["İstek çok büyük"] }), 1000, { tur: "application/json", durum: 413 }),
    );
    await expect(api.avanCizimleri({}, 0)).resolves.toEqual({ hata: "İstek çok büyük" });
    vi.stubGlobal("XMLHttpRequest", sahteXhr("kapalı", 1000, { tur: "text/plain", durum: 503 }));
    await expect(api.avanCizimleri({}, 0)).rejects.toThrow(/yanıt vermedi/);
  });
});

describe("akışlı indirme ( 20 Kas — paketin adımları, sonda dosya )", () => {
  afterEach(() => vi.unstubAllGlobals());
  const satirla = (s: unknown[]) => s.map((x) => JSON.stringify(x)).join("\n") + "\n";
  const dosya = { ad: "Proje - Uygulama Projesi.zip", tur: "application/zip", veri: btoa("PK\u0003\u0004zip") };

  it("son satırın dosyası base64'ten çözülür, notlar gelir", async () => {
    const d = akisDosyasi({ dosya, notlar: ["DXF"] }, "uygulama-dwg");
    expect(d.blob).toBeDefined();
    if (!d.blob) return;
    expect(d.ad).toBe("Proje - Uygulama Projesi.zip");
    expect(d.notlar).toEqual(["DXF"]);
    expect(new Uint8Array(await d.blob.arrayBuffer())).toEqual(base64Bayt(dosya.veri));
    expect(new TextDecoder().decode(base64Bayt(dosya.veri))).toBe("PK\u0003\u0004zip");
  });

  it("dosyasız sonuç ucun hatasıdır ( liste ya da metin — tek metin )", () => {
    expect(akisDosyasi({ aktif: false, hata: ["ÇİZİMLER KURULAMADI", "x"] }, "u")).toEqual({ hata: "ÇİZİMLER KURULAMADI\nx" });
    expect(akisDosyasi({ hata: "KÂĞIT ENİ:  75" }, "u")).toEqual({ hata: "KÂĞIT ENİ:  75" });
    expect(akisDosyasi(null, "u")).toEqual({ hata: "Üretilemedi" });
    expect(akisDosyasi({ dosya: { ...dosya, veri: "%%%" } }, "u")).toEqual({ hata: expect.stringMatching(/okunamadı/) });
  });

  it("hiç fırlatmaz:  vazgeç iptal, kopan bağlantı ve yarım akış ileti", async () => {
    const ilerleme = { ilerleme: { asamalar: [{ kod: "hesap", surer: "h", bitti: "h", ayrinti: "", t: 0 }], sinama: 0, gecen: 0.2 } };
    vi.stubGlobal("XMLHttpRequest", sahteXhr(satirla([ilerleme, { sonuc: { dosya } }]), 3));
    const k = new AbortController();
    const s = indirAkisli("uygulama-dwg", {}, k.signal);
    k.abort();
    await expect(s).resolves.toEqual({ iptal: true });
    vi.stubGlobal("XMLHttpRequest", sahteXhr(satirla([ilerleme]), 9, { kopar: true }));
    await expect(indirAkisli("uygulama-dwg", {})).resolves.toEqual({ hata: expect.stringMatching(/ulaşılamadı/) });
    vi.stubGlobal("XMLHttpRequest", sahteXhr(satirla([ilerleme]), 9));
    await expect(indirAkisli("uygulama-dwg", {})).resolves.toEqual({ hata: expect.stringMatching(/koptu/) });
    vi.stubGlobal("XMLHttpRequest", sahteXhr("<html>bozuk</html>", 1000, { tur: "application/json" }));
    await expect(indirAkisli("uygulama-dwg", {})).resolves.toEqual({ hata: expect.stringMatching(/okunamadı/) });
    vi.stubGlobal("XMLHttpRequest", sahteXhr("kapalı", 1000, { tur: "text/html", durum: 502 }));
    await expect(indirAkisli("proje-dwg", {})).resolves.toEqual({ hata: expect.stringMatching(/yanıt vermedi/) });
  });
});
