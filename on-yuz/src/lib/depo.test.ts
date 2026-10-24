import { afterEach, describe, expect, it, vi } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

/**  Sahte tarayıcı deposu:  açık · dolu ( yazma QuotaExceededError ) · engelli ( her erişim SecurityError )  */
function sahteDepo(kip: "acik" | "dolu" | "engelli" = "acik") {
  const m = new Map<string, string>();
  const engel = () => {
    if (d.kip === "engelli") throw new DOMException("Access is denied for this document.", "SecurityError");
  };
  const d = {
    kip,
    m,
    getItem: (k: string) => (engel(), m.get(k) ?? null),
    setItem: (k: string, v: string) => {
      engel();
      if (d.kip === "dolu") throw new DOMException("Depo dolu", "QuotaExceededError");
      m.set(k, v);
    },
    removeItem: (k: string) => (engel(), m.delete(k)),
  };
  return d;
}

/**  Depo modülü bellek durumunu tutar:  her test temiz kopyayla  */
async function modul<T>(d: ReturnType<typeof sahteDepo>, ad: string): Promise<T> {
  vi.resetModules();
  vi.stubGlobal("localStorage", d);
  return import(/* @vite-ignore */ ad) as Promise<T>;
}
afterEach(() => vi.unstubAllGlobals());

describe("tarayıcı deposu yazılamazsa sekmenin belleğinde tutulur ( 24 Eki )", () => {
  it("engelli depo:  yazılan okunur, silinen gider;  depo yazılamıyor der", async () => {
    const depo = await modul<typeof import("./depo")>(sahteDepo("engelli"), "./depo");
    expect(depo.depoYazilamiyor()).toBe(true);
    depo.depoYaz("asansor:proje:a", "bir");
    expect(depo.depoOku("asansor:proje:a")).toBe("bir");
    depo.depoSil("asansor:proje:a");
    expect(depo.depoOku("asansor:proje:a")).toBeNull();
  });

  it("dolu depo:  yazılamayan yeni değer eskisini gölgeler;  yer açılınca depoya yazılır, uyarı kalkar", async () => {
    const d = sahteDepo();
    const depo = await modul<typeof import("./depo")>(d, "./depo");
    depo.depoYaz("asansor:proje:a", "eski");
    depo.depoYaz("asansor:proje:b", "silinecek");
    expect(depo.depoYazilamiyor()).toBe(false);
    d.kip = "dolu";
    depo.depoYaz("asansor:proje:a", "yeni");
    expect(depo.depoYazilamiyor()).toBe(true);
    expect([d.m.get("asansor:proje:a"), depo.depoOku("asansor:proje:a")]).toEqual(["eski", "yeni"]);
    //  Başka proje silindi:  yer açıldı, bekleyen yazılır
    d.kip = "acik";
    depo.depoSil("asansor:proje:b");
    expect(d.m.get("asansor:proje:a")).toBe("yeni");
    expect(depo.depoYazilamiyor()).toBe(false);
  });

  it("uygulama projesi:  engelli depoda yeni ve örnek proje okunur, listede görünür ( açılışa atıyordu )", async () => {
    const proje = await modul<typeof import("./proje")>(sahteDepo("engelli"), "./proje");
    const yeni = proje.yeniUygulama();
    const ornek = proje.ornekProjesi();
    expect([proje.projeOku(yeni.id)?.id, proje.projeOku(ornek.id)?.id]).toEqual([yeni.id, ornek.id]);
    expect(proje.projeListesi().map((x) => x.id)).toEqual(expect.arrayContaining([yeni.id, ornek.id]));
    proje.projeSil(yeni.id);
    expect(proje.projeOku(yeni.id)).toBeNull();
  });

  it("avan projesi ve açılış bildirimi de", async () => {
    const avan = await modul<typeof import("./avan")>(sahteDepo("engelli"), "./avan");
    const p = { ...avan.BOS_AVAN, kapak: { project_title: "Deneme" } };
    avan.avanProjesiniYaz(p);
    expect(avan.avanProjesiniOku().kapak.project_title).toBe("Deneme");
    avan.acilisiYaz({ proje: p, bildirim: "açıldı", dosyaAvani: [] });
    expect(avan.acilisiOku()?.bildirim).toBe("açıldı");
    avan.acilisiYaz(null);
    expect(avan.acilisiOku()).toBeNull();
  });
});

describe("ön yüzde tarayıcı deposuna yalnız lib/depo dokunur", () => {
  it("başka dosyada localStorage / sessionStorage erişimi yok ( yazma hatası sessizce düşmesin )", () => {
    const kok = path.resolve(import.meta.dirname, "..");
    const dosyalar = (readdirSync(kok, { recursive: true }) as string[]).filter(
      (f) => /\.tsx?$/.test(f) && !f.includes(".test.") && path.basename(f) !== "depo.ts",
    );
    expect(dosyalar.length).toBeGreaterThan(20);
    const erisen = dosyalar.filter((f) => /\b(?:local|session)Storage\s*[.[]/.test(readFileSync(path.join(kok, f), "utf8")));
    expect(erisen).toEqual([]);
  });
});
