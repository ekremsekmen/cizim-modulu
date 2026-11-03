import { afterEach, describe, expect, it, vi } from "vitest";
import liste from "./taslaklar.json";

function depo() {
  const m = new Map<string, string>();
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) };
}

async function modul() {
  vi.resetModules();
  vi.stubGlobal("localStorage", depo());
  return import("./taslak");
}

afterEach(() => vi.unstubAllGlobals());

describe("taslak projeler ( açılış — uygunluğu testler/test_taslaklar.py )", () => {
  it("her yük makine dairesiz ve daireli:  iki küme, sırayla", async () => {
    const { TASLAKLAR, taslakKumeleri } = await modul();
    const yukler = ["630", "800", "1000", "1250", "1275"];
    expect(TASLAKLAR.map((t) => t.kimlik)).toEqual([...yukler, ...yukler.map((q) => `${q}-md`)]);
    expect(TASLAKLAR).toHaveLength(liste.length);
    expect(taslakKumeleri().map(([d, l]) => [d, l.length])).toEqual([
      ["Makine dairesiz", 5],
      ["Makine daireli", 5],
    ]);
  });

  it("taslak YENİ proje olarak açılır:  değerleri aynen, ikinci açılış ayrı proje, taslak değişmez", async () => {
    const { TASLAKLAR, taslaktanProje } = await modul();
    const { projeOku } = await import("./proje");
    const once = JSON.stringify(TASLAKLAR[0]);
    const p = taslaktanProje("630")!;
    expect(p.asansorler).toEqual([TASLAKLAR[0].asansor]);
    expect(p.proje_geneli).toEqual(TASLAKLAR[0].proje_geneli);
    expect(p.ornek).toBe(false);
    expect(projeOku(p.id)?.asansorler[0].beyan_yuku).toBe("630");
    p.asansorler[0].beyan_yuku = "999";
    expect(JSON.stringify(TASLAKLAR[0])).toBe(once);
    const q = taslaktanProje("630")!;
    expect(q.id).not.toBe(p.id);
    expect(taslaktanProje("yok")).toBeNull();
  });
});
