/*  UZUN İŞİN AŞAMALARI — 17 Kas avan aramasında başladı ( kullanıcı:  "beklerken ne yapıldığını
    görelim" );  20 Kas genellendi:  uygulama ve avan paketi, düzeltme önerisi ( arayüz taslağı
    B1 · B2 · B5 — paket 4 asansörde 10,4 sn, düzeltme 1,5 – 3,7 sn;  ekranda yalnız dönen işaret vardı ).

    Sunucu işin GERÇEK aşamalarını akıtır ( cizim/asamalar.py — api.ts akisla'nın ilerle'si );  burada
    yalnız onlar gösterilir:  süreye göre değişen hazır yazı ya da yüzde yok ( bütçeler sınama
    sayısıdır, iş çoğunlukla çok önce biter — yüzde yanıltırdı ).  Adımları baştan belli işte ( paket )
    sunucu planı gönderir:  başlamamış adımlar soluk.  Kısa işte ( GORUNME_ESIGI ) hiç görünmez:
    ekran yanıp sönmez.  Vazgeç isteği bırakır;  sunucu bir sonraki aşamada durur.  */

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import type { AramaIlerlemesi } from "@/lib/api";
import { cn } from "@/lib/utils";

/**  Bu kadar ms'den kısa süren işte liste görünmez  */
export const GORUNME_ESIGI = 1000;

/**  İşin ekrandaki durumu:  başladığı an ( performance.now ) ve sunucunun son bildirdiği  */
export interface IsDurumu {
  bas: number;
  d: AramaIlerlemesi | null;
}

type Asama = AramaIlerlemesi["asamalar"][number];

/**  İş sürerken geçen süre ( ms ), saniyede dört kez — durum null iken 0.  Zamanlayıcı İŞE bağlı
     ( başladığı an ), durum nesnesine değil:  her ilerleme satırı yeni bir durum nesnesidir;  satırlar
     0,2 sn'de bir gelince ( düzeltmede her sınama ) 250 ms'lik zamanlayıcı hiç dolmuyor, süre ve
     1 sn eşiği ilerlemiyordu ( 20 Kas )  */
export function useGecenSure(durum: IsDurumu | null): number {
  const [simdi, setSimdi] = useState(() => performance.now());
  const bas = durum?.bas;
  useEffect(() => {
    if (bas === undefined) return;
    const z = window.setInterval(() => setSimdi(performance.now()), 250);
    return () => window.clearInterval(z);
  }, [bas]);
  return bas === undefined ? 0 : Math.max(0, simdi - bas);
}

export function sureYaz(sn: number): string {
  if (sn < 60) return `${sn < 10 ? sn.toFixed(1).replace(".", ",") : Math.round(sn)} sn`;
  const s = Math.floor(sn);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/**  Aşamalı iş:  useMutation + sunucunun aşamaları ( durum ) + Vazgeç ( isteği bırakır ).
     calistir:  ( değişkenler , sinyal , ilerle ) → sonuç.  Bırakılan iş reddedilir ( AbortError )
     ya da çağıranın sözleşmesiyle döner ( indirAkisli:  { iptal } ) — çağıran ayırır.  */
export function useAsamaliIs<D, S>(
  calistir: (v: D, sinyal: AbortSignal, ilerle: (d: AramaIlerlemesi) => void) => Promise<S>,
) {
  const [durum, setDurum] = useState<IsDurumu | null>(null);
  const kontrol = useRef<AbortController | null>(null);
  const m = useMutation({
    mutationFn: async (v: D) => {
      const k = new AbortController();
      kontrol.current = k;
      const bas = performance.now();
      setDurum({ bas, d: null });
      try {
        return await calistir(v, k.signal, (d) => setDurum((x) => (x && x.bas === bas ? { ...x, d } : x)));
      } finally {
        if (kontrol.current === k) {
          kontrol.current = null;
          setDurum(null);
        }
      }
    },
  });
  return { ...m, durum, vazgec: () => kontrol.current?.abort() };
}

/**  Bırakılan isteğin reddi mi ( Vazgeç ):  hata olarak gösterilmez  */
export function birakildiMi(e: unknown): boolean {
  return e instanceof DOMException && e.name === "AbortError";
}

/**  Liste:  biten aşamalar ( süresiyle ), süren aşama ( dönen işaret ), planda sıradakiler ( soluk ),
     sayaç.  kucuk:  başka bir şeyin üstünde / içinde duran kart  */
export function IsAsamalari({
  durum,
  gecen,
  baslik,
  sayac,
  alt,
  vazgec,
  kucuk,
  className,
}: {
  durum: IsDurumu;
  gecen: number;
  /**  Kartın başlığı ( son aşamaya göre değişebilir — avan araması:  çizimler kurulurken )  */
  baslik: string | ((son: Asama | undefined) => string);
  /**  Sınama sayısının metni ( "4 yerleşim sınandı" );  yoksa sayı yazılmaz  */
  sayac?: (n: number) => string;
  /**  Alt satırın açıklaması  */
  alt?: string;
  /**  Vazgeç ( isteği bırakır );  yoksa düğme yok  */
  vazgec?: () => void;
  kucuk?: boolean;
  className?: string;
}) {
  const asamalar = durum.d?.asamalar ?? [];
  const baslayan = new Set(asamalar.map((a) => a.kod));
  const sirada = (durum.d?.plan ?? []).filter((p) => !baslayan.has(p.kod));
  const sn = gecen / 1000;
  const son = asamalar[asamalar.length - 1];
  const sinama = durum.d?.sinama ?? 0;
  return (
    <div
      role="status"
      aria-live="polite"
      data-arama-asamalari
      className={cn(
        "rounded-buyuk border border-cizgi bg-yuzey text-left text-metin",
        kucuk ? "w-80 max-w-full px-4 py-3 shadow-sm" : "w-full max-w-md px-5 py-4",
        className,
      )}
    >
      <div className="flex items-baseline justify-between gap-3">
        <p className={cn("font-semibold", kucuk ? "text-[13px]" : "text-[15px]")}>
          {typeof baslik === "function" ? baslik(son) : baslik}
        </p>
        <span className="sayi text-[12px] text-metin-3">{sureYaz(sn)}</span>
      </div>
      {asamalar.length + sirada.length > 0 && (
        <ol className="mt-3 flex flex-col gap-2 text-[12.5px]">
          {asamalar.map((a, j) => {
            const sonraki = asamalar[j + 1];
            const bitti = !!sonraki;
            const sure = bitti ? sonraki.t - a.t : Math.max(0, sn - a.t);
            return (
              <li key={`${j}-${a.kod}`} className="flex gap-2.5" data-asama={a.kod} data-bitti={bitti || undefined}>
                {bitti ? (
                  <Check className="mt-0.5 size-3.5 shrink-0 text-[#12b76a]" aria-label="bitti" />
                ) : (
                  <Loader2 className="mt-0.5 size-3.5 shrink-0 animate-spin text-metin-3" aria-label="sürüyor" />
                )}
                <div className="min-w-0 flex-1">
                  <span className={cn(bitti ? "text-metin-2" : "font-medium text-metin")}>{bitti ? a.bitti : a.surer}</span>
                  {a.ayrinti && <span className="block text-[11.5px] text-metin-3">{a.ayrinti}</span>}
                </div>
                <span className="sayi shrink-0 text-[11.5px] text-metin-3">{sureYaz(sure)}</span>
              </li>
            );
          })}
          {sirada.map((p) => (
            <li key={`plan-${p.kod}`} className="flex gap-2.5 text-metin-3" data-asama={p.kod} data-sirada>
              <span aria-label="sırada" className="mt-1 ml-0.5 size-2.5 shrink-0 rounded-full border border-cizgi-2" />
              <span className="min-w-0 flex-1">{p.surer}</span>
            </li>
          ))}
        </ol>
      )}
      {(sinama > 0 && sayac) || alt || vazgec ? (
        <div className="mt-3 flex items-center gap-3 border-t border-cizgi pt-2 text-[11.5px] text-metin-3">
          <p className="min-w-0 flex-1">
            {sinama > 0 && sayac && <span className="sayi">{sayac(sinama)}</span>}
            {sinama > 0 && sayac && alt && " · "}
            {alt}
          </p>
          {vazgec && (
            <button
              type="button"
              onClick={vazgec}
              className="shrink-0 rounded-kucuk border border-cizgi-2 px-2 py-0.5 text-[11.5px] font-medium text-metin hover:bg-black/[0.04]"
            >
              Vazgeç
            </button>
          )}
        </div>
      ) : null}
    </div>
  );
}
