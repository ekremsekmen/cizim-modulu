/*  KAT GİRİŞİ — "Ölçüyle | Kotla" ve kot tablosu ( KOT_PLANI 6. adım )
    Kotla girişte satırlar yukarıdan aşağı, kesit gibi:  tavan döşemesinin üstü
    ( türetilen — mimarın plan kotuyla karşılaştırılır ) · kuyu tavanı ( döşemenin
    ALTI ) · makine dairesinin zemini · duraklar · kuyu dibi.  Her satıra kot ya da
    fark yazılır;  saklanan hep kottur ( tek kaynak ).  Fark yazılınca üstteki
    satırlar birlikte kayar.  Türetilenler ( durak adedi, seyir, KY, son kat,
    tabliye ) sunucudan gelir — ön yüz hesaplamaz, girişi kolaylaştırır.        */
import { useState } from "react";
import { Plus, X } from "lucide-react";
import type { Deger } from "@/lib/api";
import {
  DURAK_KOTLARI,
  KUYU_DIBI_KOTU,
  KUYU_TAVANI_KOTU,
  MD_ZEMINI_KOTU,
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
  type Degisiklik,
} from "@/lib/kotlar";
import { sayiOku } from "@/lib/denetim";
import { cn, sayiYaz } from "@/lib/utils";
import { Bolumlu, Girdi } from "@/components/ui";

type Ham = Record<string, string>;

function parcalar(metin: string | undefined): string[] {
  return (metin ?? "")
    .split(/[;\n]/)
    .map((x) => x.trim())
    .filter((x) => x !== "");
}

/**  Yazarken yerel, Enter ya da odaktan çıkınca uygulanan kutu — fark yazılınca
     üstteki satırlar her tuşta kaymasın.  */
function YerelKutu({
  deger,
  uygula,
  etiket,
  birim,
}: {
  deger: string;
  uygula: (yazi: string) => void;
  etiket: string;
  birim?: string;
}) {
  const [yazi, setYazi] = useState<string | null>(null);
  const bitir = () => {
    if (yazi !== null && yazi.trim() !== "" && yazi !== deger) uygula(yazi);
    setYazi(null);
  };
  return (
    <Girdi
      aria-label={etiket}
      className="h-7"
      inputMode="decimal"
      birim={birim}
      value={yazi ?? deger}
      placeholder="—"
      onChange={(e) => setYazi(e.target.value)}
      onBlur={bitir}
      onKeyDown={(e) => e.key === "Enter" && (e.currentTarget as HTMLInputElement).blur()}
    />
  );
}

/**  Fark ( mm ):  iki kotun farkı;  yazılınca uygula( mm )  */
function FarkKutusu({ deger, uygula, etiket }: { deger: number | null; uygula: (mm: number) => void; etiket: string }) {
  return (
    <YerelKutu
      etiket={etiket}
      deger={deger === null ? "" : String(deger)}
      uygula={(y) => {
        const n = sayiOku(y);
        if (n !== null && n > 0) uygula(Math.round(n));
      }}
    />
  );
}

function Satir({ ad, kot, fark, sil }: { ad: React.ReactNode; kot: React.ReactNode; fark?: React.ReactNode; sil?: () => void }) {
  return (
    <div className="flex items-center gap-1.5 py-px">
      <span className="min-w-0 flex-1 truncate text-[12px] text-metin-2">{ad}</span>
      <div className="w-[86px]">{kot}</div>
      <div className="w-[72px]">{fark}</div>
      <div className="w-5">
        {sil && (
          <button type="button" aria-label={`${typeof ad === "string" ? ad : "durak"} — sil`} onClick={sil} className="text-metin-3 hover:text-red">
            <X className="size-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

export function KatGirisi({
  h,
  kullanilan,
  daireli,
  doseme,
  etkin,
  yaz,
}: {
  /**  Aktif asansörün yazılmış değerleri  */
  h: Ham;
  /**  Sunucunun hesapta kullandığı değerler ( türetilenler buradan )  */
  kullanilan: Record<string, Deger> | undefined;
  daireli: boolean;
  /**  Tavan döşemesinin etkin kalınlığı ( mm )  */
  doseme: number;
  /**  Alanın etkin sayısı:  yazılmış, yoksa sunucunun kullandığı, yoksa varsayılan  */
  etkin: (anahtar: string) => number | undefined;
  yaz: (anahtar: string, deger: string) => void;
}) {
  const [arac, setArac] = useState<null | "doldur" | "yapistir" | "kaydir">(null);
  const kot = kotlaMi(h);
  const uygula = (d: Degisiklik | null) => d && Object.entries(d).forEach(([k, v]) => yaz(k, v));
  const k = kotlariOku(h[DURAK_KOTLARI]);
  const ham = parcalar(h[DURAK_KOTLARI]);
  const enAlt = k[0] ?? null;
  const enUst = k.length ? k[k.length - 1] : null;
  const tavan = kotOku(h[KUYU_TAVANI_KOTU]);
  const dip = kotOku(h[KUYU_DIBI_KOTU]);
  //  Makine dairesinin zemini boşsa sunucunun kuralıyla ( tabliye 1.200 ):  soluk
  const mdKullanilan = typeof kullanilan?.[MD_ZEMINI_KOTU] === "number" ? (kullanilan[MD_ZEMINI_KOTU] as number) : null;
  const md = kotOku(h[MD_ZEMINI_KOTU]) ?? (mdKullanilan === null ? null : Math.round(mdKullanilan * 1000));
  const durakYaz = (j: number, metin: string) => {
    const y = [...ham];
    y[j] = metin;
    yaz(DURAK_KOTLARI, y.filter((x) => x.trim() !== "").join("; "));
  };
  const kotKutusu = (alan: string, etiket: string, yer?: string) => (
    <Girdi
      aria-label={etiket}
      className="h-7"
      inputMode="decimal"
      birim="m"
      value={h[alan] ?? ""}
      placeholder={yer}
      durum={h[alan] === undefined && yer ? "varsayilan" : undefined}
      onChange={(e) => yaz(alan, e.target.value)}
    />
  );

  return (
    <div className="mb-1.5 rounded-orta border border-cizgi bg-black/[0.015] px-2 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[12.5px] font-medium">Katlar</span>
        <Bolumlu
          etiket="Kat girişi"
          deger={kot ? "kot" : "olcu"}
          degisti={(d) =>
            uygula(
              d === "kot"
                ? kotlaGecis(etkin, h.kat_yukseklikleri ?? (typeof kullanilan?.kat_yukseklikleri === "string" ? kullanilan.kat_yukseklikleri : undefined), daireli)
                : olcuyleGecis(kullanilan, daireli),
            )
          }
          secenekler={[
            { deger: "olcu", ad: "Ölçüyle" },
            { deger: "kot", ad: "Kotla" },
          ]}
        />
      </div>
      {kot && (
        <div className="mt-2">
          <div className="flex items-center gap-1.5 pb-0.5 text-[11px] text-metin-3">
            <span className="flex-1" />
            <span className="w-[86px] text-right">kot</span>
            <span className="w-[72px] text-right">fark ( mm )</span>
            <span className="w-5" />
          </div>
          {/*  Mimarın planındaki kot döşemenin ÜSTÜDÜR:  buraya yazılırsa kuyu tavanı
               ( altı ) döşeme kalınlığı çıkarılarak bulunur — altı yerine üstü yazmak
               kuyu üst boşluğunu kalınlık kadar büyük gösterirdi ( güvensiz yön )  */}
          <Satir
            ad="Döşemenin üstü"
            kot={
              <YerelKutu
                etiket="Tavan döşemesinin üstü ( mimarın plan kotu )"
                birim="m"
                deger={tavan === null ? "" : kotYaz(tavan + doseme)}
                uygula={(y) => {
                  const m = kotOku(y);
                  if (m !== null) yaz(KUYU_TAVANI_KOTU, kotYaz(m - doseme));
                }}
              />
            }
            fark={<span className="block pr-1 text-right text-[11.5px] text-metin-3">{sayiYaz(doseme)}</span>}
          />
          <Satir
            ad="Kuyu tavanı ( altı )"
            kot={kotKutusu(KUYU_TAVANI_KOTU, "Kuyu tavanı kotu ( döşemenin altı )")}
            fark={
              <FarkKutusu
                etiket="Son kat yüksekliği"
                deger={tavan !== null && enUst !== null ? tavan - enUst : null}
                uygula={(mm) => enUst !== null && yaz(KUYU_TAVANI_KOTU, kotYaz(enUst + mm))}
              />
            }
          />
          {daireli && (
            <Satir
              ad="Makine dairesi zemini"
              kot={kotKutusu(MD_ZEMINI_KOTU, "Makine dairesi zemini kotu", md === null ? undefined : kotYaz(md))}
              fark={
                <FarkKutusu
                  etiket="Tabliye beton yüksekliği"
                  deger={tavan !== null && md !== null ? tavan + doseme - md : null}
                  uygula={(mm) => tavan !== null && yaz(MD_ZEMINI_KOTU, kotYaz(tavan + doseme - mm))}
                />
              }
            />
          )}
          {ham
            .map((metin, j) => ({ metin, j }))
            .reverse()
            .map(({ metin, j }) => {
              const alt = j > 0 ? k[j - 1] : null;
              const bu = k[j];
              return (
                <Satir
                  key={j}
                  ad={`${j + 1}. durak`}
                  kot={
                    <Girdi
                      aria-label={`${j + 1}. durağın kotu`}
                      className="h-7"
                      inputMode="decimal"
                      birim="m"
                      value={metin}
                      durum={bu === null ? "hata" : undefined}
                      onChange={(e) => durakYaz(j, e.target.value)}
                    />
                  }
                  fark={
                    j > 0 ? (
                      <FarkKutusu
                        etiket={`${j}. – ${j + 1}. durak arası`}
                        deger={alt !== null && bu !== null ? bu - alt : null}
                        uygula={(mm) => uygula(araligiYaz(h, j, mm))}
                      />
                    ) : undefined
                  }
                  sil={ham.length > 2 ? () => yaz(DURAK_KOTLARI, ham.filter((_, i) => i !== j).join("; ")) : undefined}
                />
              );
            })}
          <Satir
            ad="Kuyu dibi"
            kot={kotKutusu(KUYU_DIBI_KOTU, "Kuyu dibi kotu")}
            fark={
              <FarkKutusu
                etiket="Kuyu dibi yüksekliği ( KY )"
                deger={dip !== null && enAlt !== null ? enAlt - dip : null}
                uygula={(mm) => enAlt !== null && yaz(KUYU_DIBI_KOTU, kotYaz(enAlt - mm))}
              />
            }
          />
          <div className="mt-1.5 flex flex-wrap gap-1">
            <button
              type="button"
              className="inline-flex h-7 items-center gap-1 rounded-kucuk px-1.5 text-[12px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin"
              onClick={() => {
                if (enUst === null) return;
                const h1 = k.length > 1 && k[k.length - 2] !== null ? enUst - (k[k.length - 2] as number) : 3000;
                uygula({
                  [DURAK_KOTLARI]: [...ham, kotYaz(enUst + h1)].join("; "),
                  ...(tavan !== null && { [KUYU_TAVANI_KOTU]: kotYaz(tavan + h1) }),
                  ...(kotOku(h[MD_ZEMINI_KOTU]) !== null && { [MD_ZEMINI_KOTU]: kotYaz((kotOku(h[MD_ZEMINI_KOTU]) as number) + h1) }),
                });
              }}
            >
              <Plus className="size-3.5" /> Durak ekle
            </button>
            {(["doldur", "yapistir", "kaydir"] as const).map((a) => (
              <button
                key={a}
                type="button"
                aria-expanded={arac === a}
                onClick={() => setArac(arac === a ? null : a)}
                className={cn(
                  "inline-flex h-7 items-center rounded-kucuk px-1.5 text-[12px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin",
                  arac === a && "bg-black/[0.05] text-metin",
                )}
              >
                {{ doldur: "Hızlı doldur", yapistir: "Yapıştır", kaydir: "Kaydır" }[a]}
              </button>
            ))}
          </div>
          {arac && (
            <Arac
              arac={arac}
              kapat={() => setArac(null)}
              h={h}
              uygula={uygula}
              sonKat={tavan !== null && enUst !== null ? tavan - enUst : null}
              ky={dip !== null && enAlt !== null ? enAlt - dip : null}
            />
          )}
          <Ozet kullanilan={kullanilan} daireli={daireli} />
        </div>
      )}
    </div>
  );
}

/**  Hızlı doldur ( n durak × h, en alt kot — son kat ve KY korunur ) · yapıştır · bütün kotları kaydır  */
function Arac({
  arac,
  kapat,
  h,
  uygula,
  sonKat,
  ky,
}: {
  arac: "doldur" | "yapistir" | "kaydir";
  kapat: () => void;
  h: Ham;
  uygula: (d: Degisiklik | null) => void;
  sonKat: number | null;
  ky: number | null;
}) {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [c, setC] = useState("");
  const tamam = () => {
    if (arac === "doldur") {
      const n = sayiOku(a);
      const hh = sayiOku(b);
      const alt = kotOku(c || "±0,00");
      if (n === null || hh === null || alt === null || n < 2 || hh <= 0) return;
      const ust = alt + (Math.round(n) - 1) * Math.round(hh);
      uygula({
        [DURAK_KOTLARI]: hizliDoldur(Math.round(n), alt, Math.round(hh)),
        ...(sonKat !== null && { [KUYU_TAVANI_KOTU]: kotYaz(ust + sonKat) }),
        ...(ky !== null && { [KUYU_DIBI_KOTU]: kotYaz(alt - ky) }),
      });
    } else if (arac === "yapistir") {
      if (!a.trim()) return;
      uygula({ [DURAK_KOTLARI]: yapistir(a) });
    } else {
      const m = kotOku(a);
      if (m === null) return;
      uygula(kaydir(h, m));
    }
    kapat();
  };
  return (
    <div className="mt-1.5 space-y-1.5 rounded-kucuk border border-cizgi bg-yuzey p-2">
      {arac === "doldur" && (
        <div className="grid grid-cols-3 gap-1">
          <Girdi aria-label="Durak sayısı" placeholder="durak" value={a} onChange={(e) => setA(e.target.value)} className="h-7" />
          <Girdi aria-label="Kat yüksekliği ( mm )" placeholder="kat ( mm )" value={b} onChange={(e) => setB(e.target.value)} className="h-7" />
          <Girdi aria-label="En alt durağın kotu" placeholder="±0,00" value={c} onChange={(e) => setC(e.target.value)} className="h-7" birim="m" />
        </div>
      )}
      {arac === "yapistir" && (
        <textarea
          aria-label="Yapıştırılacak kotlar"
          value={a}
          onChange={(e) => setA(e.target.value)}
          rows={4}
          placeholder={"−7,00\n−3,50\n±0,00\n+3,20 …  ( yukarıdan aşağı da olur )"}
          className="w-full rounded-kucuk border border-cizgi-2 bg-yuzey px-2 py-1 text-[12.5px] outline-none focus:border-vurgu"
        />
      )}
      {arac === "kaydir" && (
        <Girdi aria-label="Bütün kotlar ne kadar kaysın ( m )" placeholder="−7,00 — mimarın ±0,00'ına" value={a} onChange={(e) => setA(e.target.value)} className="h-7" birim="m" />
      )}
      <div className="flex justify-end gap-1">
        <button type="button" onClick={kapat} className="h-7 rounded-kucuk px-2 text-[12px] text-metin-2 hover:bg-black/[0.04]">
          Vazgeç
        </button>
        <button type="button" onClick={tamam} className="h-7 rounded-kucuk bg-vurgu px-2.5 text-[12px] font-medium text-white hover:opacity-90">
          Uygula
        </button>
      </div>
    </div>
  );
}

/**  Türetilenler — sunucunun kullandığı ( yanıtın girdisi ):  ön yüz hesaplamaz  */
function Ozet({ kullanilan, daireli }: { kullanilan: Record<string, Deger> | undefined; daireli: boolean }) {
  const s = (a: string) => (typeof kullanilan?.[a] === "number" ? (kullanilan[a] as number) : null);
  const parca = [
    s("durak_adedi") !== null && `${sayiYaz(s("durak_adedi"))} durak`,
    s("seyir_mesafesi") !== null && `seyir ${sayiYaz(s("seyir_mesafesi"))} m`,
    s("kuyu_dibi") !== null && `KY ${sayiYaz(s("kuyu_dibi"))}`,
    s("son_kat_yuksekligi") !== null && `son kat ${sayiYaz(s("son_kat_yuksekligi"))}`,
    daireli && s("tabliye_yuksekligi") !== null && `tabliye ${sayiYaz(s("tabliye_yuksekligi"))}`,
  ].filter(Boolean);
  if (!parca.length) return null;
  return (
    <p className="mt-1.5 px-0.5 text-[11.5px] text-metin-3" aria-label="Kotlardan türeyenler">
      Kotlardan:  {parca.join(" · ")}
    </p>
  );
}
