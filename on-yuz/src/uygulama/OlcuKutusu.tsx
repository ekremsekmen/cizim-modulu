/*  ÖLÇÜ KUTUSU — çizimdeki bir ölçüye tıklanınca.
    /api/uygulama/olcu:  ölçüyü belirleyen girdiler ( eğimiyle:  girdi 1 mm
    değişince ölçü kaç mm değişir ).  /api/uygulama/olcu_degistir:  hedef
    ölçüye götüren girdi değişikliği — sunucu çizimi yeniden kurup doğrular,
    biz yalnız kutulara yazarız;  hesap ve çizim kendi akışıyla yenilenir.     */
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Check, Loader2, X } from "lucide-react";
import { api, type UygulamaIstegi } from "@/lib/api";
import { kutuyaYaz } from "@/lib/proje";
import { cn, sayiYaz } from "@/lib/utils";
import { Dugme, Girdi, Rozet } from "@/components/ui";
import { kutuYeri, type OlcuKonumu, type OlcuSecimi } from "./Tuval";

const YER: Record<string, string> = { asansor: "asansör", proje: "bina", ofis: "ofis standardı" };

export function OlcuKutusu({
  istek,
  asansor,
  olcu,
  konum,
  kapat,
  yaz,
  kaynaklarGeldi,
}: {
  istek: UygulamaIstegi;
  asansor: number;
  olcu: OlcuSecimi;
  konum: OlcuKonumu;
  /**  Kaynak girdiler gelince:  solda gruplarını aç, alanları vurgula  */
  kaynaklarGeldi?: (anahtarlar: string[]) => void;
  kapat: () => void;
  yaz: (degisiklikler: { anahtar: string; deger: number }[]) => void;
}) {
  //  Kutu açıldığı andaki girdilerle konuşur:  değişiklik uygulanınca çizim
  //  yenilenir ama kutu kendi ölçüsünün sonucunu göstermeye devam eder
  const [sabit] = useState(istek);
  const sorgu = useQuery({
    queryKey: ["olcu", sabit, asansor, olcu.cizim, olcu.index],
    queryFn: () => api.olcu(sabit, asansor, olcu.cizim, olcu.index, olcu.metin),
  });
  const y = sorgu.data;
  const degisebilen = (y?.kaynaklar ?? []).filter((k) => k.degistirilir);
  //  Kullanıcı seçmedikçe ilk değiştirilebilen girdi;  yazmadıkça ölçünün kendisi
  //  ( binlik ayırıcısız:  "1.600" sunucuda belirsizdir, reddedilir )
  const [anahtarSecimi, setAnahtar] = useState<string | null>(null);
  const [hedefYazi, setHedef] = useState<string | null>(null);
  const anahtar = anahtarSecimi ?? degisebilen[0]?.anahtar ?? null;
  const hedef = hedefYazi ?? (y?.deger !== undefined ? kutuyaYaz(y.deger) : "");

  const degistir = useMutation({
    mutationFn: () => api.olcuDegistir(sabit, asansor, olcu.cizim, olcu.index, olcu.metin, anahtar!, hedef),
    onSuccess: (r) => {
      if (r.aktif && r.degisiklikler) yaz(r.degisiklikler.map((d) => ({ anahtar: d.anahtar, deger: d.deger })));
    },
  });
  const sonuc = degistir.data;

  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && kapat();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [kapat]);

  //  Kutu ölçünün sağında;  tuvalin kenarına taşmaz
  useEffect(() => {
    if (y?.kaynaklar) kaynaklarGeldi?.(y.kaynaklar.filter((k) => k.yer !== "ofis").map((k) => k.anahtar));
  }, [y]); // eslint-disable-line react-hooks/exhaustive-deps

  const { sol, ust, en } = kutuYeri(konum, 344, 420);
  return (
    <div
      data-olcu-kutu
      role="dialog"
      aria-label={`Ölçü ${olcu.metin}`}
      className="absolute z-30 overflow-hidden rounded-buyuk border border-cizgi bg-yuzey text-metin shadow-kalkik select-text"
      style={{ left: sol, top: ust, width: en }}
    >
      <div className="flex items-start justify-between gap-3 border-b border-cizgi px-4 py-3">
        <div>
          <p className="text-[12px] text-metin-3">{olcu.aciklama || olcu.metin.replace(/\s*[\d.,]+$/, "") || "Ölçü"}</p>
          <p className="mt-0.5 flex items-baseline gap-2">
            <span className="sayi text-[20px] font-semibold">{y?.deger !== undefined ? sayiYaz(y.deger) : "…"}</span>
            <span className="text-[12px] text-metin-3">mm</span>
            {olcu.aciklama && <span className="font-mono text-[11.5px] text-metin-3">{olcu.metin.replace(/[\d.,]+$/, "")}</span>}
          </p>
        </div>
        <Dugme tur="hayalet" boy="simge-kucuk" aria-label="Kapat" onClick={kapat}>
          <X />
        </Dugme>
      </div>

      {sorgu.isLoading ? (
        <p className="flex items-center gap-2 px-4 py-4 text-[12.5px] text-metin-3">
          <Loader2 className="size-3.5 animate-spin" /> Kaynağı bulunuyor
        </p>
      ) : y && !y.aktif ? (
        <p className="px-4 py-3 text-[12.5px] text-red">{y.hata?.join(" ")}</p>
      ) : (
        <>
          <div className="px-4 pt-3 pb-1">
            <p className="text-[11.5px] font-medium tracking-wide text-metin-3 uppercase">Bu ölçüyü belirleyen</p>
            {y?.kural && <p className="mt-1 text-[12px] text-metin-2">{y.kural}</p>}
          </div>
          <ul className="px-2 pb-2" role="radiogroup" aria-label="Değiştirilecek girdi">
            {y?.kaynaklar?.map((k) => {
              const sec = anahtar === k.anahtar;
              return (
                <li key={k.anahtar}>
                  <button
                    type="button"
                    role="radio"
                    aria-checked={sec}
                    disabled={!k.degistirilir}
                    onClick={() => setAnahtar(k.anahtar)}
                    className={cn(
                      "flex w-full items-center gap-2.5 rounded-orta px-2 py-2 text-left",
                      k.degistirilir ? "hover:bg-black/[0.035]" : "cursor-default",
                      sec && "bg-vurgu-acik hover:bg-vurgu-acik",
                    )}
                  >
                    <span
                      className={cn(
                        "flex size-3.5 shrink-0 items-center justify-center rounded-full border",
                        !k.degistirilir ? "border-dashed border-cizgi-2" : sec ? "border-vurgu" : "border-cizgi-2",
                      )}
                    >
                      {sec && <span className="size-1.5 rounded-full bg-vurgu" />}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[12.5px]">{k.etiket.replace(/\s*\(mm\)$/, "")}</span>
                      <span className="text-[11px] text-metin-3">
                        {YER[k.yer] ?? k.yer}
                        {k.egim !== 1 && <> · ölçüye etkisi ×{sayiYaz(k.egim)}</>}
                      </span>
                    </span>
                    <span className="sayi text-[12.5px]">
                      {sayiYaz(k.deger)} <span className="text-metin-3">{k.birim}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {degisebilen.length > 0 && (
            <form
              className="border-t border-cizgi bg-yuzey-2 px-4 py-3"
              onSubmit={(e) => {
                e.preventDefault();
                degistir.mutate();
              }}
            >
              <label htmlFor="olcu-hedef" className="text-[12px] font-medium text-metin-2">
                Yeni ölçü
              </label>
              <div className="mt-1.5 flex gap-2">
                <Girdi id="olcu-hedef" value={hedef} onChange={(e) => setHedef(e.target.value)} birim="mm" className="flex-1" />
                <Dugme tur="birincil" type="submit" disabled={degistir.isPending || !anahtar}>
                  {degistir.isPending ? <Loader2 className="animate-spin" /> : <ArrowRight />}
                  Uygula
                </Dugme>
              </div>
              {sonuc &&
                (sonuc.aktif ? (
                  <div className="mt-2.5 space-y-1">
                    {sonuc.degisiklikler?.map((d) => (
                      <p key={d.anahtar} className="flex items-center gap-1.5 text-[12px] text-uygun">
                        <Check className="size-3.5" />
                        {d.etiket}:{" "}
                        <span className="sayi">
                          {sayiYaz(d.eski)} → {sayiYaz(d.deger)}
                        </span>
                      </p>
                    ))}
                    {sonuc.dogrulandi && (
                      <Rozet tur="uygun">Çizim yeniden kuruldu — ölçü {sayiYaz(sonuc.olcu)} mm</Rozet>
                    )}
                  </div>
                ) : (
                  <p className="mt-2 text-[12px] text-red">{sonuc.hata?.join(" ")}</p>
                ))}
            </form>
          )}
        </>
      )}
    </div>
  );
}
