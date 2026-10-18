/*  HESAP BELGESİ — sunucunun bölümleri, paftanın ekrandaki okuması.
    Uygulama ( /api/uygulama/coklu ), trafik ( /api/trafik ) ve avan
    ( /api/avan ) aynı biçimde döner:  bölüm → adımlar → sonuç.  Bileşen tek.  */
import { ChevronRight } from "lucide-react";
import { useState } from "react";
import type { Adim, Bolum } from "@/lib/api";
import { bolumAdi, cn } from "@/lib/utils";
import { Rozet } from "./ui";

export function HukumRozeti({ uygun }: { uygun: boolean | null | undefined }) {
  if (uygun === true) return <Rozet tur="uygun">Uygun</Rozet>;
  if (uygun === false) return <Rozet tur="red">Uygun değil</Rozet>;
  return <Rozet>Bilgi</Rozet>;
}

export function HesapBelgesi({
  bolumler,
  secili,
  bos,
}: {
  bolumler: Bolum[];
  secili?: string | null;
  bos?: React.ReactNode;
}) {
  if (!bolumler.length) return <>{bos}</>;
  return (
    <div className="space-y-4">
      {bolumler.map((b, i) => (
        <BolumKarti key={b.kimlik ?? i} b={b} secili={!!b.kimlik && secili === b.kimlik} />
      ))}
    </div>
  );
}

function BolumKarti({ b, secili }: { b: Bolum; secili: boolean }) {
  const [no, ad] = bolumAdi(b.baslik);
  const [ack, setAck] = useState(false);
  const cetvel = (b as unknown as { cetvel?: Record<string, unknown>[] }).cetvel;
  return (
    <article
      id={`bolum-${b.kimlik}`}
      className={cn(
        "scroll-mt-4 overflow-hidden rounded-buyuk border bg-yuzey shadow-panel transition-shadow",
        secili ? "border-vurgu ring-3 ring-vurgu/15" : "border-cizgi",
      )}
    >
      <header className="flex items-start justify-between gap-4 border-b border-cizgi px-5 py-3.5">
        <div className="min-w-0">
          <h3 className="text-[14px] font-semibold">
            {no && <span className="sayi mr-2 text-metin-3">{no}</span>}
            {ad}
          </h3>
          <p className="mt-0.5 font-mono text-[11.5px] text-metin-3">{b.kaynak}</p>
        </div>
        <HukumRozeti uygun={b.sonuc?.uygun} />
      </header>

      <table className="w-full table-fixed text-[12.5px]">
        <colgroup>
          <col className="w-[92px]" />
          <col />
          <col className="w-[120px]" />
          <col className="w-[64px]" />
          <col className="w-[92px]" />
        </colgroup>
        <tbody>
          {b.adimlar.map((a, i) => (
            <AdimSatiri key={i} a={a} />
          ))}
        </tbody>
      </table>

      {cetvel && Array.isArray(cetvel) && cetvel.length > 0 && (
        <div className="border-t border-cizgi px-5 py-3">
          <table className="w-full text-[12px]">
            <thead className="text-left text-metin-3">
              <tr>
                <th className="py-1 font-medium">Linye</th>
                <th className="py-1 font-medium">Sorti</th>
                <th className="py-1 text-right font-medium">Güç</th>
                <th className="py-1 text-right font-medium">Sigorta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cizgi">
              {cetvel.map((s, i) => (
                <tr key={i}>
                  <td className="sayi py-1">{String(s.lin)}</td>
                  <td className="py-1 font-mono text-[11.5px]">{String(s.sorti).replace(/\s{2,}/g, " ")}</td>
                  <td className="sayi py-1 text-right">
                    {Number(s.guc).toLocaleString("tr-TR")} {String(s.birim)}
                  </td>
                  <td className="sayi py-1 text-right">{String(s.sigorta)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {b.sonuc && (
        <div
          className={cn(
            "border-t px-5 py-3",
            b.sonuc.uygun === false
              ? "border-red-cizgi bg-red-acik"
              : b.sonuc.uygun === true
                ? "border-uygun-cizgi bg-uygun-acik"
                : "border-cizgi bg-yuzey-2",
          )}
        >
          <p className="font-mono text-[11.5px] whitespace-pre-wrap text-metin-2">
            {b.sonuc.baslik.replace(/\s{3,}/g, "   ")}
          </p>
          <p
            className={cn(
              "mt-1 text-[13px] font-medium",
              b.sonuc.uygun === false ? "text-red" : b.sonuc.uygun === true ? "text-uygun" : "text-metin",
            )}
          >
            {b.sonuc.metin}
          </p>
          {b.sonuc.alt && (
            <ul className="mt-1 space-y-0.5 font-mono text-[11.5px] text-metin-2">
              {b.sonuc.alt.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {(b.notlar?.length > 0 || b.aciklamalar?.length > 0) && (
        <div className="border-t border-cizgi px-5 py-2.5">
          {b.notlar?.map((n) => (
            <p key={n} className="py-0.5 text-[12.5px] text-metin">
              {n}
            </p>
          ))}
          {b.aciklamalar?.length > 0 && (
            <>
              <button
                type="button"
                onClick={() => setAck(!ack)}
                aria-expanded={ack}
                className="inline-flex items-center gap-1 py-1 text-[12px] font-medium text-metin-2 hover:text-metin"
              >
                <ChevronRight className={cn("size-3 transition-transform", ack && "rotate-90")} />
                Açıklamalar · {b.aciklamalar.length}
              </button>
              {ack && (
                <div className="space-y-2 pb-1.5 text-[12.5px] leading-relaxed text-metin-2">
                  {b.aciklamalar.map((x) => (
                    <p key={x}>{x}</p>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </article>
  );
}

const ARA_HUKUM = /^UYGUN( DEĞİL)?(DUR|DİR)?\.?$/;

function AdimSatiri({ a }: { a: Adim }) {
  //  Bölüm içindeki ara hüküm ( "UYGUN" / "UYGUN DEĞİL" ) başlık değil, rozettir
  if (a.tip === "metin" && ARA_HUKUM.test(a.metin.trim())) {
    return (
      <tr>
        <td />
        <td colSpan={4} className="pt-0.5 pb-1.5">
          <HukumRozeti uygun={!/DEĞİL/i.test(a.metin)} />
        </td>
      </tr>
    );
  }
  if (a.tip === "metin") {
    return (
      <tr>
        <td colSpan={5} className="px-5 pt-3 pb-1 text-[12px] font-semibold text-metin">
          {a.metin}
        </td>
      </tr>
    );
  }
  const hesap = a.tip === "hesap";
  return (
    <tr className={cn("align-top", a.vurgu && "bg-vurgu-acik/50")}>
      <td className="sayi py-1 pl-5 break-words text-metin">{a.sembol}</td>
      <td className="py-1 pr-3">
        {hesap ? (
          <>
            <span className="font-mono text-[12px] text-metin">{a.formul}</span>
            {a.islem && <span className="block font-mono text-[11.5px] text-metin-3">= {a.islem.replace(/^=\s*/, "")}</span>}
          </>
        ) : (
          <span className="text-metin-2">{a.aciklama}</span>
        )}
      </td>
      <td
        className={cn(
          "py-1 text-right",
          typeof a.deger === "number" || /^[\d\s.,:/−-]+$/.test(a.metin) ? "sayi" : "text-[12.5px]",
          (hesap || a.vurgu) && "font-semibold",
        )}
      >
        {a.metin}
      </td>
      <td className="py-1 pl-2 text-metin-3">{a.birim}</td>
      <td className="py-1 pr-5">
        {a.kaynak && (
          <span
            className={cn(
              "inline-block max-w-full truncate rounded-[4px] px-1 text-[10.5px] font-medium",
              a.kaynak === "GİRİŞ" ? "bg-vurgu-acik text-vurgu-koyu" : "bg-black/[0.05] text-metin-2",
            )}
            title={a.kaynak}
          >
            {a.kaynak}
          </span>
        )}
      </td>
    </tr>
  );
}
