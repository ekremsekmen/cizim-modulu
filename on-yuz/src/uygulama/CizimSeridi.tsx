/*  ÇİZİM ŞERİDİ ( K2 ) — tuvalin altında;  20 Kas'tan ( arayüz taslağı B7 ) düğme adı kadar geniş,
    sığmayanlar sırayla "Diğer" kutusunda ( lib/serit ).  Rozet çizimde sorunlu ( kırmızı ) ya da
    hesabın uygun bulmadığı ( turuncu ) parça olduğunu söyler;  Diğer'e inen çizimin rozeti
    Diğer'in üstünde de görünür.  Düğmenin erişilebilir adı başlığın kendisi ( baslikAdi ),
    tam başlık üstüne gelince.  */

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { ChevronDown, LayoutGrid } from "lucide-react";
import type { Cizim } from "@/lib/api";
import { baslikAdi, seritAdi, seritYerlesimi, seviyeHarfi } from "@/lib/serit";
import { cn } from "@/lib/utils";
import { Acilir, AcilirIcerik, AcilirTetik } from "@/components/ui";

export type Rozet = "sorunlu" | "hesap" | null;

/**  Düğmelerin aralığı ( gap-0.5 ):  yerleşim hesabında her düğmeye eklenir  */
const ARA = 2;
const DIGER = "__diger";

export function CizimSeridi({
  cizimler,
  tumu,
  aktif,
  tumuSec,
  goster,
  rozet,
  boy,
}: {
  cizimler: Cizim[];
  /**  Tümü görünümü açık  */
  tumu: boolean;
  /**  Açık çizim ( tek kipte ) — hep şeritte görünür  */
  aktif: string | null;
  tumuSec: () => void;
  goster: (ad: string) => void;
  rozet: (ad: string) => Rozet;
  boy: number;
}) {
  const ogeler = cizimler.map((c) => ({ c, ad: seritAdi(c), harf: seviyeHarfi(c.baslik), rozet: rozet(c.ad) }));
  const alanRef = useRef<HTMLDivElement>(null);
  const olcuRef = useRef<HTMLDivElement>(null);
  const [alan, setAlan] = useState<number | null>(null);
  const [enler, setEnler] = useState<Record<string, number>>({});
  //  Yazı tipi gelince yeniden ölçülür ( ilk ölçü yedek yazı tipiyle olabilir )
  const [yaziTipi, setYaziTipi] = useState(0);
  useEffect(() => {
    let sur = true;
    document.fonts?.ready.then(() => sur && setYaziTipi((n) => n + 1));
    return () => {
      sur = false;
    };
  }, []);
  useLayoutEffect(() => {
    const el = alanRef.current;
    if (!el) return;
    //  Kesirli ölçü ( aşağı ):  yuvarlanan genişlikler toplanınca son düğme taşıp kesilebilirdi
    const olc = () => setAlan(Math.floor(el.getBoundingClientRect().width));
    olc();
    const ro = new ResizeObserver(olc);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  //  Düğmelerin doğal genişliği:  görünmez kopyalarından ( adı, harfi, rozeti değişince yeniden )
  const imza = ogeler.map((o) => `${o.c.ad}|${o.ad}|${o.harf ?? ""}|${o.rozet ?? ""}`).join(";");
  useLayoutEffect(() => {
    const el = olcuRef.current;
    if (!el) return;
    const y: Record<string, number> = {};
    for (const x of el.querySelectorAll<HTMLElement>("[data-olc]"))
      y[x.dataset.olc!] = Math.ceil(x.getBoundingClientRect().width) + ARA;
    setEnler((e) => (JSON.stringify(e) === JSON.stringify(y) ? e : y));
  }, [imza, yaziTipi]);

  const acikAd = tumu ? null : aktif;
  const olculdu = alan !== null && ogeler.every((o) => enler[o.c.ad] !== undefined) && enler[DIGER] !== undefined;
  const { gorunen, gizli } = olculdu
    ? seritYerlesimi(
        ogeler.map((o) => enler[o.c.ad]),
        enler[DIGER],
        alan,
        ogeler.findIndex((o) => o.c.ad === acikAd),
      )
    : { gorunen: ogeler.map((_o, i) => i), gizli: [] as number[] };
  const gizliRozet: Rozet = gizli.some((i) => ogeler[i].rozet === "sorunlu")
    ? "sorunlu"
    : gizli.some((i) => ogeler[i].rozet === "hesap")
      ? "hesap"
      : null;
  const [acik, setAcik] = useState(false);

  return (
    <nav
      data-tuval-arac
      aria-label="Çizimler"
      className="absolute inset-x-0 bottom-0 flex items-center gap-0.5 border-t border-white/[0.08] bg-tuval-2/95 px-2 backdrop-blur"
      style={{ height: boy }}
    >
      <SeritDugmesi secili={tumu} onClick={tumuSec} className="shrink-0">
        <LayoutGrid className="size-3.5" /> Tümü
      </SeritDugmesi>
      <span className="mx-1 h-5 w-px shrink-0 bg-white/10" />
      <div ref={alanRef} className="flex min-w-0 flex-1 items-center gap-0.5">
        {gorunen.map((i) => {
          const o = ogeler[i];
          return (
            <SeritDugmesi
              key={o.c.ad}
              secili={o.c.ad === acikAd}
              onClick={() => goster(o.c.ad)}
              baslik={o.c.baslik}
              ad={baslikAdi(o.c.baslik)}
              className="min-w-0"
            >
              <Icerik o={o} />
            </SeritDugmesi>
          );
        })}
        {gizli.length > 0 && (
          <Acilir open={acik} onOpenChange={setAcik}>
            <AcilirTetik asChild>
              <SeritDugmesi ad={`Diğer çizimler ( ${gizli.length} )`} className="shrink-0">
                <DigerIcerik n={gizli.length} rozet={gizliRozet} />
              </SeritDugmesi>
            </AcilirTetik>
            <AcilirIcerik side="top" align="end" aria-label="Öteki çizimler" className="w-64 p-1.5" data-tuval-arac>
              {gizli.map((i) => {
                const o = ogeler[i];
                return (
                  <button
                    key={o.c.ad}
                    type="button"
                    aria-label={baslikAdi(o.c.baslik)}
                    title={o.c.baslik}
                    onClick={() => {
                      setAcik(false);
                      goster(o.c.ad);
                    }}
                    className="flex w-full items-center gap-2 rounded-kucuk px-2 py-1.5 text-left text-[12.5px] hover:bg-black/[0.04]"
                  >
                    <RozetIsareti rozet={o.rozet} />
                    {o.harf && <span className="sayi text-[11px] text-metin-3">{o.harf}</span>}
                    <span className="min-w-0 flex-1 truncate">{o.ad}</span>
                  </button>
                );
              })}
            </AcilirIcerik>
          </Acilir>
        )}
      </div>
      {/*  Ölçü:  düğmelerin görünmez kopyaları ( doğal genişlikleri — yerleşim bunlarla )  */}
      <div aria-hidden className="pointer-events-none invisible absolute top-0 left-0 h-0 overflow-hidden">
        <div ref={olcuRef} className="flex w-max">
          {ogeler.map((o) => (
            <span key={o.c.ad} data-olc={o.c.ad} className={cn(DUGME, "shrink-0")}>
              <Icerik o={o} />
            </span>
          ))}
          <span data-olc={DIGER} className={cn(DUGME, "shrink-0")}>
            <DigerIcerik n={88} rozet="sorunlu" />
          </span>
        </div>
      </div>
    </nav>
  );
}

type Oge = { c: Cizim; ad: string; harf: string | null; rozet: Rozet };

function Icerik({ o }: { o: Oge }) {
  return (
    <>
      <RozetIsareti rozet={o.rozet} />
      {o.harf && <span className="sayi shrink-0 text-[10.5px] opacity-60">{o.harf}</span>}
      <span className="truncate">{o.ad}</span>
    </>
  );
}

function DigerIcerik({ n, rozet }: { n: number; rozet: Rozet }) {
  return (
    <>
      <RozetIsareti rozet={rozet} />
      Diğer <span className="sayi opacity-60">· {n}</span>
      <ChevronDown className="size-3.5 shrink-0" />
    </>
  );
}

function RozetIsareti({ rozet }: { rozet: Rozet }) {
  if (rozet === "sorunlu")
    return <span aria-hidden title="Sorunlu parça var" className="size-1.5 shrink-0 rounded-full bg-[#f97066]" />;
  if (rozet === "hesap")
    return (
      <span aria-hidden title="Hesabın uygun bulmadığı parça var" className="size-1.5 shrink-0 rounded-full bg-[#ff9f1a]" />
    );
  return null;
}

const DUGME = "inline-flex h-8 items-center gap-1.5 rounded-orta px-2 text-[12px] font-medium whitespace-nowrap";

function SeritDugmesi({
  secili,
  baslik,
  ad,
  className,
  children,
  ...p
}: {
  /**  Basılı mı ( çizim düğmesi );  yoksa aria-pressed yok ( Diğer — açılır kutunun tetiği )  */
  secili?: boolean;
  baslik?: string;
  /**  Erişilebilir ad ( görünen kısa ad olabilir )  */
  ad?: string;
} & React.ComponentProps<"button">) {
  return (
    <button
      type="button"
      aria-pressed={secili}
      aria-label={ad}
      title={baslik}
      className={cn(
        DUGME,
        secili ? "bg-white/[0.12] text-white" : "text-tuval-metin-2 hover:bg-white/[0.06] hover:text-tuval-metin",
        className,
      )}
      {...p}
    >
      {children}
    </button>
  );
}
