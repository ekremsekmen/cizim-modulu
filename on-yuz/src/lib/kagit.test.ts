import { afterEach, describe, expect, it, vi } from "vitest";

/**  Kâğıt eni ( 19 Kas ):  seçim tarayıcıda hatırlanır;  yoksa ya da tanınmayan değerse 60 cm  */
function sahteDepo() {
  const m = new Map<string, string>();
  return {
    m,
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => void m.set(k, v),
    removeItem: (k: string) => void m.delete(k),
  };
}

async function modul(d: ReturnType<typeof sahteDepo>) {
  vi.resetModules();
  vi.stubGlobal("localStorage", d);
  return import("./kagit");
}
afterEach(() => vi.unstubAllGlobals());

describe("kâğıt eni", () => {
  it("ilk açılışta 60 cm ( ofisin şablonu )", async () => {
    const k = await modul(sahteDepo());
    expect(k.kagitOku()).toBe(600);
  });

  it("seçilen hatırlanır;  sunucuya mm gider", async () => {
    const d = sahteDepo();
    const k = await modul(d);
    k.kagitYaz(900);
    expect(k.kagitOku()).toBe(900);
    expect([...d.m.values()]).toEqual(["900"]);
    k.kagitYaz(600);
    expect(k.kagitOku()).toBe(600);
  });

  it("depoda tanınmayan değer 60 cm sayılır", async () => {
    const d = sahteDepo();
    d.m.set("asansor:kagit_eni", "750");
    const k = await modul(d);
    expect(k.kagitOku()).toBe(600);
  });

  it("seçenekler 60 ve 90 cm", async () => {
    const k = await modul(sahteDepo());
    expect(k.KAGIT_ENLERI.map((s) => [s.deger, s.cm])).toEqual([
      ["600", 60],
      ["900", 90],
    ]);
  });
});
