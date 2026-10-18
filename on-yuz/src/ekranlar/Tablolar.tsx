/*  TABLOLAR — hesabın okuduğu tablolar, olduğu gibi ( ray · NPU · halat · ω … ).
    Şema:  /api/uygulama/alanlar → tablolar.  Salt okunur:  mühendis kullanılan
    değere bakar, değiştirmez ( değişiklik ofis standardından ya da girdiden ).  */
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Search } from "lucide-react";
import { api } from "@/lib/api";
import { sayiYaz } from "@/lib/utils";
import { BasvuruSayfasi, GezintiOgesi } from "@/components/Kabuk";
import { Rozet } from "@/components/ui";

export function Tablolar() {
  const sema = useQuery({ queryKey: ["alanlar"], queryFn: api.alanlar });
  const [secili, setSecili] = useState(0);
  const [ara, setAra] = useState("");
  const tablolar = sema.data?.tablolar ?? [];
  const t = tablolar[secili];
  const aranan = ara.trim().toLocaleLowerCase("tr-TR");
  const satirlar = useMemo(
    () =>
      !t ? [] : aranan ? t.satirlar.filter((s) => s.some((h) => sayiYaz(h, true).toLocaleLowerCase("tr-TR").includes(aranan))) : t.satirlar,
    [t, aranan],
  );

  if (!t)
    return (
      <div className="flex h-dvh items-center justify-center gap-2 text-[13px] text-metin-3">
        <Loader2 className="size-4 animate-spin" /> Yükleniyor
      </div>
    );

  return (
    <BasvuruSayfasi
      genis
      baslik="Tablolar"
      aciklama="Hesabın okuduğu tablolar, olduğu gibi.  Bir değer burada yanlışsa hesap da yanlıştır:  kaynağı her tablonun başında."
      gezinti={
        <div className="space-y-px">
          {tablolar.map((x, i) => (
            <GezintiOgesi
              key={x.ad}
              secili={i === secili}
              onClick={() => {
                setSecili(i);
                setAra("");
              }}
              sag={<span className="sayi text-[11px] text-metin-3">{x.satirlar.length}</span>}
            >
              {x.ad}
            </GezintiOgesi>
          ))}
        </div>
      }
    >
      <section className="overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
        <header className="flex items-start justify-between gap-4 border-b border-cizgi px-5 py-3.5">
          <div>
            <h2 className="text-[14px] font-semibold">{t.ad}</h2>
            <p className="mt-0.5 text-[12.5px] text-metin-2">{t.aciklama}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Rozet>{t.kaynak}</Rozet>
            <label className="flex h-8 w-48 items-center gap-2 rounded-kucuk border border-cizgi-2 px-2.5">
              <Search className="size-3.5 text-metin-3" />
              <input
                value={ara}
                onChange={(e) => setAra(e.target.value)}
                placeholder="Satır ara"
                aria-label="Satır ara"
                className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-metin-3"
              />
            </label>
          </div>
        </header>
        <div className="max-h-[calc(100dvh-230px)] overflow-auto">
          <table className="w-full text-[12.5px]">
            <thead className="sticky top-0 z-10 bg-yuzey-2 shadow-[0_1px_0_var(--color-cizgi)]">
              <tr>
                {t.basliklar.map((b, i) => (
                  <th
                    key={b}
                    className={`px-3 py-2 text-[11.5px] font-medium whitespace-nowrap text-metin-2 ${i ? "text-right" : "pl-5 text-left"}`}
                  >
                    {b.replace(/\s{2,}/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-cizgi">
              {satirlar.map((s, i) => (
                <tr key={i} className="hover:bg-vurgu-acik/40">
                  {s.map((h, j) => (
                    <td key={j} className={`sayi px-3 py-1.5 whitespace-nowrap ${j ? "text-right" : "pl-5 font-medium"}`}>
                      {sayiYaz(h, true)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </BasvuruSayfasi>
  );
}
