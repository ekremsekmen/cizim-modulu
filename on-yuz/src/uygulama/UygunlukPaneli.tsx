/*  UYGUNLUK — bölümlerin hükmü, kalanlar başta.
    Bir bölüme tıklamak:  bağlı girdi gruplarını solda açar ( bolum_grubu ),
    hesap görünümündeyse bölüme gider.  Hüküm metni sunucunundur — çare de.  */
import { useState } from "react";
import { AlertTriangle, ChevronRight, CircleAlert } from "lucide-react";
import type { Bolum } from "@/lib/api";
import { bolumAdi, cn } from "@/lib/utils";
import { HukumNoktasi } from "@/components/ui";

export function UygunlukPaneli({
  bolumler,
  uyarilar,
  bolumGrubu,
  secili,
  sec,
  durdu,
}: {
  bolumler: Bolum[];
  uyarilar: string[];
  bolumGrubu: Record<string, string[]>;
  secili: string | null;
  sec: (b: Bolum) => void;
  durdu: boolean;
}) {
  const [uygunlarAcik, setUygunlarAcik] = useState(false);
  const kalan = bolumler.filter((b) => b.sonuc?.uygun === false);
  const uygun = bolumler.filter((b) => b.sonuc?.uygun === true);
  const bilgi = bolumler.filter((b) => b.sonuc?.uygun == null);

  return (
    <aside aria-label="Uygunluk" className="flex w-[324px] shrink-0 flex-col border-l border-cizgi bg-yuzey">
      <div className="border-b border-cizgi px-4 pt-3 pb-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-[13px] font-semibold">Uygunluk</h2>
          <span className="text-[12px] text-metin-3">{bolumler.length} bölüm</span>
        </div>
        {/*  Üç sayı:  bir bakışta proje nerede  */}
        <div className="mt-2.5 grid grid-cols-3 overflow-hidden rounded-orta border border-cizgi text-center">
          <Sayac sayi={kalan.length} ad="uygun değil" renk={kalan.length ? "text-red" : "text-metin-3"} />
          <Sayac sayi={uygun.length} ad="uygun" renk="text-uygun" ayrac />
          <Sayac sayi={bilgi.length} ad="bilgi" renk="text-metin-2" ayrac />
        </div>
        {durdu && (
          <p className="mt-2.5 flex items-start gap-1.5 text-[12px] leading-snug text-uyari">
            <CircleAlert className="mt-px size-3.5 shrink-0" />
            Hükümler son geçerli girdilerin;  güncel girdiyle hesap yapılamadı.
          </p>
        )}
      </div>

      <div className={cn("min-h-0 flex-1 space-y-2 overflow-y-auto p-3", durdu && "opacity-60")}>
        {kalan.map((b) => {
          const [no, ad] = bolumAdi(b.baslik);
          const metin = b.sonuc.metin.replace(/^UYGUN DEĞİLDİR\s*[—:-]?\s*/i, "");
          return (
            <button
              key={b.kimlik}
              type="button"
              onClick={() => sec(b)}
              aria-pressed={secili === b.kimlik}
              className={cn(
                "w-full rounded-buyuk border p-3 text-left transition-colors",
                secili === b.kimlik
                  ? "border-vurgu bg-vurgu-acik/40 ring-3 ring-vurgu/10"
                  : "border-red-cizgi bg-yuzey hover:border-red/50",
              )}
            >
              <span className="flex items-start gap-2">
                <HukumNoktasi uygun={false} className="mt-[5px]" />
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] font-medium">
                    <span className="sayi mr-1 text-metin-3">{no}</span>
                    {ad}
                  </span>
                  <span className="mt-1 line-clamp-4 block text-[12.5px] leading-snug text-metin-2">
                    {metin || "Uygun değil"}
                  </span>
                  <span className="mt-2 flex flex-wrap gap-1">
                    {(bolumGrubu[b.kimlik] ?? []).map((g) => (
                      <span key={g} className="rounded-[4px] bg-black/[0.05] px-1.5 py-px text-[11px] text-metin-2">
                        {g}
                      </span>
                    ))}
                  </span>
                </span>
              </span>
            </button>
          );
        })}

        {!bolumler.length && (
          <p className="px-2 py-6 text-center text-[12.5px] leading-relaxed text-metin-3">
            Henüz hüküm yok.  Hesap kurulunca bölümler burada, kalanlar en üstte listelenir.
          </p>
        )}

        {uyarilar.map((u) => (
          <Uyari key={u} metin={u.replace(/^[⚠ℹ]\s*/, "")} />
        ))}

        {bilgi.length > 0 && (
          <ListeBasligi>Hükümsüz bölümler</ListeBasligi>
        )}
        {bilgi.map((b) => (
          <SatirBolum key={b.kimlik} b={b} secili={secili === b.kimlik} sec={sec} sonucuGoster />
        ))}

        {uygun.length > 0 && (
          <button
            type="button"
            onClick={() => setUygunlarAcik(!uygunlarAcik)}
            aria-expanded={uygunlarAcik}
            className="mt-1 flex w-full items-center gap-1 px-1 py-1 text-[12px] font-medium text-metin-2 hover:text-metin"
          >
            <ChevronRight className={cn("size-3 transition-transform", uygunlarAcik && "rotate-90")} />
            Uygun bölümler · {uygun.length}
          </button>
        )}
        {uygunlarAcik && uygun.map((b) => <SatirBolum key={b.kimlik} b={b} secili={secili === b.kimlik} sec={sec} />)}
      </div>
    </aside>
  );
}

function Sayac({ sayi, ad, renk, ayrac }: { sayi: number; ad: string; renk: string; ayrac?: boolean }) {
  return (
    <div className={cn("py-2", ayrac && "border-l border-cizgi")}>
      <div className={cn("sayi text-[18px] leading-none font-semibold", renk)}>{sayi}</div>
      <div className="mt-1 text-[11px] text-metin-3">{ad}</div>
    </div>
  );
}

function ListeBasligi({ children }: { children: React.ReactNode }) {
  return <p className="px-1 pt-2 text-[11.5px] font-medium tracking-wide text-metin-3 uppercase">{children}</p>;
}

function SatirBolum({
  b,
  secili,
  sec,
  sonucuGoster,
}: {
  b: Bolum;
  secili: boolean;
  sec: (b: Bolum) => void;
  sonucuGoster?: boolean;
}) {
  const [no, ad] = bolumAdi(b.baslik);
  return (
    <button
      type="button"
      onClick={() => sec(b)}
      aria-pressed={secili}
      className={cn(
        "flex w-full items-start gap-2 rounded-orta px-2 py-1.5 text-left hover:bg-black/[0.035]",
        secili && "bg-vurgu-acik hover:bg-vurgu-acik",
      )}
    >
      <HukumNoktasi uygun={b.sonuc?.uygun} className="mt-[5px]" />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[12.5px]">
          <span className="sayi mr-1 text-metin-3">{no}</span>
          {ad}
        </span>
        {sonucuGoster && (
          <span className="mt-0.5 line-clamp-2 block font-mono text-[11px] leading-snug text-metin-3">
            {b.sonuc.metin}
          </span>
        )}
      </span>
    </button>
  );
}

function Uyari({ metin }: { metin: string }) {
  const [acik, setAcik] = useState(false);
  const uzun = metin.length > 160;
  return (
    <div className="rounded-buyuk border border-uyari-cizgi bg-uyari-acik p-3">
      <p className={cn("flex gap-1.5 text-[12.5px] leading-snug text-uyari", !acik && uzun && "line-clamp-4")}>
        <AlertTriangle className="mt-px size-3.5 shrink-0" />
        <span>{metin}</span>
      </p>
      {uzun && (
        <button
          type="button"
          onClick={() => setAcik(!acik)}
          className="mt-1 ml-5 text-[12px] font-medium text-uyari underline-offset-2 hover:underline"
        >
          {acik ? "Kısalt" : "Devamı"}
        </button>
      )}
    </div>
  );
}
