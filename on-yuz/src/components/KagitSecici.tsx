/*  Paketin kâğıt eni:  60 / 90 cm ( lib/kagit ) — Teslim'in paket bölümünde ve avanın
    "Projeyi indir"inin yanında aynı seçici.  kisa:  dar üst şerit — 1.440 px'ten dar ekranda
    birimsiz ( "60 · 90";  birimi ipucu söyler ), proje adına yer kalsın.  */
import { KAGIT_ENLERI, type KagitEni } from "@/lib/kagit";
import { Bolumlu } from "@/components/ui";

export function KagitSecici({
  deger,
  degisti,
  kisa,
}: {
  deger: KagitEni;
  degisti: (k: KagitEni) => void;
  kisa?: boolean;
}) {
  return (
    <Bolumlu
      etiket="Kâğıt eni"
      deger={`${deger}` as const}
      degisti={(d) => degisti(d === "900" ? 900 : 600)}
      secenekler={KAGIT_ENLERI.map((s) => ({
        deger: s.deger,
        ad: kisa ? (
          <>
            {s.cm}
            <span className="hidden min-[1440px]:inline"> cm</span>
          </>
        ) : (
          `${s.cm} cm`
        ),
      }))}
    />
  );
}
