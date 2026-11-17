/*  AVAN SEÇİCİSİNİN AŞAMALARI ( 17 Kas — kullanıcı:  "beklerken ne yapıldığını görelim" )

    Seçici bazen saniyeler, dar kuyuda bir – iki dakika arar.  Sunucu aramanın GERÇEK aşamalarını
    akıtır ( avan_secici.Ilerleme — api.avanCizimleri'nin ilerle'si );  burada yalnız onlar
    gösterilir:  süreye göre değişen hazır yazı ya da yüzde yok ( bütçe sınama sayısıdır, arama
    çoğunlukla çok önce biter — yüzde yanıltırdı ).  Kısa aramada ( GORUNME_ESIGI ) hiç görünmez:
    ekran yanıp sönmez.  */

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import type { AramaIlerlemesi } from "@/lib/api";
import { cn } from "@/lib/utils";

/**  Bu kadar ms'den kısa süren arama için liste görünmez  */
export const GORUNME_ESIGI = 1000;

/**  Aramanın ekrandaki durumu:  başladığı an ( performance.now ) ve sunucunun son bildirdiği  */
export interface AramaDurumu {
  bas: number;
  d: AramaIlerlemesi | null;
}

/**  Arama sürerken geçen süre ( ms ), saniyede dört kez — durum null iken 0  */
export function useGecenSure(durum: AramaDurumu | null): number {
  const [simdi, setSimdi] = useState(() => performance.now());
  useEffect(() => {
    if (!durum) return;
    const z = window.setInterval(() => setSimdi(performance.now()), 250);
    return () => window.clearInterval(z);
  }, [durum]);
  return durum ? Math.max(0, simdi - durum.bas) : 0;
}

export function sureYaz(sn: number): string {
  if (sn < 60)
    return `${sn < 10 ? sn.toFixed(1).replace(".", ",") : Math.round(sn)} sn`;
  const s = Math.floor(sn);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/**  Liste:  biten aşamalar ( süresiyle ), süren aşama ( dönen işaret ), sınanan düzen sayısı.
     kucuk:  çizimin üstünde köşedeki kart ( eski çizim görünürken yenisi aranıyor )  */
export function AramaAsamalari({
  durum,
  gecen,
  kucuk,
}: {
  durum: AramaDurumu;
  gecen: number;
  kucuk?: boolean;
}) {
  const asamalar = durum.d?.asamalar ?? [];
  const sn = gecen / 1000;
  const son = asamalar[asamalar.length - 1];
  const baslik =
    son?.kod === "cizim" ? "Çizimler kuruluyor…" : "Asansör seçiliyor…";
  const sinama = durum.d?.sinama ?? 0;
  return (
    <div
      role="status"
      aria-live="polite"
      data-arama-asamalari
      className={cn(
        "rounded-buyuk border border-cizgi bg-yuzey text-left",
        kucuk ? "w-80 px-4 py-3 shadow-sm" : "w-full max-w-md px-5 py-4",
      )}
    >
      <div className="flex items-baseline justify-between gap-3">
        <p
          className={cn("font-semibold", kucuk ? "text-[13px]" : "text-[15px]")}
        >
          {baslik}
        </p>
        <span className="sayi text-[12px] text-metin-3">{sureYaz(sn)}</span>
      </div>
      {asamalar.length > 0 && (
        <ol className="mt-3 flex flex-col gap-2 text-[12.5px]">
          {asamalar.map((a, j) => {
            const sonraki = asamalar[j + 1];
            const bitti = !!sonraki;
            const sure = bitti ? sonraki.t - a.t : Math.max(0, sn - a.t);
            return (
              <li
                key={`${j}-${a.kod}`}
                className="flex gap-2.5"
                data-asama={a.kod}
                data-bitti={bitti || undefined}
              >
                {bitti ? (
                  <Check
                    className="mt-0.5 size-3.5 shrink-0 text-[#12b76a]"
                    aria-label="bitti"
                  />
                ) : (
                  <Loader2
                    className="mt-0.5 size-3.5 shrink-0 animate-spin text-metin-3"
                    aria-label="sürüyor"
                  />
                )}
                <div className="min-w-0 flex-1">
                  <span
                    className={cn(
                      bitti ? "text-metin-2" : "font-medium text-metin",
                    )}
                  >
                    {bitti ? a.bitti : a.surer}
                  </span>
                  {a.ayrinti && (
                    <span className="block text-[11.5px] text-metin-3">
                      {a.ayrinti}
                    </span>
                  )}
                </div>
                <span className="sayi shrink-0 text-[11.5px] text-metin-3">
                  {sureYaz(sure)}
                </span>
              </li>
            );
          })}
        </ol>
      )}
      <p className="mt-3 border-t border-cizgi pt-2 text-[11.5px] text-metin-3">
        {sinama > 0 && (
          <span className="sayi">{sinama} yerleşim sınandı · </span>
        )}
        Girdiyi değiştirirseniz bu arama bırakılır, yenisi başlar.
      </p>
    </div>
  );
}
