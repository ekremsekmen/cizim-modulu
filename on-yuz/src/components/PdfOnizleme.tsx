/*  PDF ÖNİZLEMESİ — sunucunun ürettiği PDF'in ilk sayfası, pdf.js ile tuvale.
    Tarayıcının PDF eklentisine bağlı değil:  araç çubuğu yok, her yerde aynı.  */
import { useEffect, useRef, useState } from "react";
import * as pdfjs from "pdfjs-dist";
import isci from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { Loader2 } from "lucide-react";

pdfjs.GlobalWorkerOptions.workerSrc = isci;

export function PdfOnizleme({ veri }: { veri: ArrayBuffer | undefined }) {
  const kap = useRef<HTMLDivElement>(null);
  const tuval = useRef<HTMLCanvasElement>(null);
  const [hazir, setHazir] = useState(false);
  //  pdf.js okuyamazsa ( yanıt PDF değil, bozuk ) söylenir:  reddi yutuluyor,
  //  önizleme sonsuza dek dönüyordu ( 24 Eki )
  const [hata, setHata] = useState(false);

  useEffect(() => {
    if (!veri) return;
    let iptal = false;
    //  BELGE İŞÇİSİYLE KAPATILIR ( 24 Eki ):  getDocument her çağrıda yeni bir pdf.js
    //  işçisi ( Web Worker ) açar, onu yalnız destroy kapatır.  Kapatılmıyordu:  her
    //  önizleme güncellemesi bir işçi bırakıyor, kapaktan çıkınca da kapanmıyordu.
    //  Sayfa tuvale çizilince belge gerekmez;  yarıda kalan da ( yeni veri, çıkış ) kapanır.
    const gorev = pdfjs.getDocument({ data: veri.slice(0) });
    let kapandi = false;
    const kapat = () => {
      if (kapandi) return;
      kapandi = true;
      gorev.destroy().catch(() => {});
    };
    (async () => {
      const belge = await gorev.promise;
      const sayfa = await belge.getPage(1);
      const el = tuval.current;
      const alan = kap.current;
      if (iptal || !el || !alan) return;
      const v1 = sayfa.getViewport({ scale: 1 });
      const sigdir = Math.min((alan.clientWidth - 48) / v1.width, (alan.clientHeight - 48) / v1.height);
      const dpr = window.devicePixelRatio || 1;
      const v = sayfa.getViewport({ scale: sigdir * dpr });
      el.width = v.width;
      el.height = v.height;
      el.style.width = `${v.width / dpr}px`;
      el.style.height = `${v.height / dpr}px`;
      await sayfa.render({ canvas: el, canvasContext: el.getContext("2d")!, viewport: v }).promise;
      if (!iptal) {
        setHazir(true);
        setHata(false);
      }
    })()
      .catch(() => {
        if (!iptal) setHata(true);
      })
      .finally(kapat);
    return () => {
      iptal = true;
      kapat();
    };
  }, [veri]);

  return (
    <div ref={kap} className="relative flex h-full w-full items-center justify-center bg-black/[0.04]">
      <canvas ref={tuval} hidden={hata} className="bg-white shadow-kalkik" />
      {hata ? (
        <p role="alert" className="absolute px-8 text-center text-[13px] text-red">
          Önizleme açılamadı — sunucunun yanıtı okunabilir bir PDF değil.
        </p>
      ) : (
        !hazir && <Loader2 className="absolute size-5 animate-spin text-metin-3" />
      )}
    </div>
  );
}
