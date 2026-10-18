/*  OFİS STANDARDI — bütün projelerde geçerli kabuller ( sabitler ).
    Şema:  /api/uygulama/alanlar → sabitler ( gruplar · etiket · varsayılan ).
    Değerler tarayıcıda saklanır ve her hesap isteğine "sabitler" olarak girer;
    sunucu okur, belirsiz ya da okunamayan sayıyı reddeder.                  */
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, RotateCcw, Search } from "lucide-react";
import { api } from "@/lib/api";
import { useOfisStandardi } from "@/lib/proje";
import { cn, cumleDuzeni, sayiYaz } from "@/lib/utils";
import { BasvuruSayfasi, GezintiOgesi } from "@/components/Kabuk";
import { Bolumlu, Dugme, Girdi, Rozet } from "@/components/ui";

export function OfisStandardi() {
  const sema = useQuery({ queryKey: ["alanlar"], queryFn: api.alanlar });
  const [ofis, setOfis] = useOfisStandardi();
  const [proje, setProje] = useState<"uygulama" | "avan">("uygulama");
  const [secili, setSecili] = useState(0);
  const [ara, setAra] = useState("");
  const s = sema.data?.sabitler;

  const degisen = useMemo(() => Object.keys(ofis).filter((k) => ofis[k] !== ""), [ofis]);
  const grupDegisen = (alanlar: string[]) => alanlar.filter((k) => ofis[k] !== undefined && ofis[k] !== "").length;
  const aranan = ara.trim().toLocaleLowerCase("tr-TR");

  if (!s)
    return (
      <div className="flex h-dvh items-center justify-center gap-2 text-[13px] text-metin-3">
        <Loader2 className="size-4 animate-spin" /> Yükleniyor
      </div>
    );

  const gruplar = aranan
    ? [
        {
          baslik: "Arama",
          aciklama: `"${ara}" geçen sabitler`,
          alanlar: Object.keys(s.etiket).filter((k) =>
            (s.etiket[k][0] + " " + (s.etiket[k][1] ?? "")).toLocaleLowerCase("tr-TR").includes(aranan),
          ),
        },
      ]
    : s.gruplar;
  const g = gruplar[Math.min(secili, gruplar.length - 1)];

  return (
    <BasvuruSayfasi
      baslik="Ofis standardı"
      aciklama="Bütün projelerde geçerli kabuller.  Değiştirdiğiniz değer bu tarayıcıda saklanır ve her hesaba girer;  paftada kaynağı OFİS yazar."
      ust={
        <Dugme disabled={!degisen.length} onClick={() => setOfis({})}>
          <RotateCcw /> Tümünü varsayılana döndür
        </Dugme>
      }
      gezinti={
        <div className="space-y-2">
          <div className="px-1 pt-1">
            <Bolumlu
              etiket="Proje türü"
              deger={proje}
              degisti={setProje}
              secenekler={[
                { deger: "uygulama", ad: "Uygulama" },
                { deger: "avan", ad: "Avan" },
              ]}
            />
          </div>
          <label className="mx-1 flex h-8 items-center gap-2 rounded-kucuk border border-cizgi-2 px-2.5">
            <Search className="size-3.5 text-metin-3" />
            <input
              value={ara}
              onChange={(e) => {
                setAra(e.target.value);
                setSecili(0);
              }}
              placeholder="Sabit ara"
              aria-label="Sabit ara"
              className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-metin-3"
            />
          </label>
          <div className="space-y-px">
            {gruplar.map((x, i) => (
              <GezintiOgesi
                key={x.baslik}
                secili={i === secili}
                onClick={() => setSecili(i)}
                sag={grupDegisen(x.alanlar) > 0 && <Rozet tur="vurgu">{grupDegisen(x.alanlar)}</Rozet>}
              >
                {cumleDuzeni(x.baslik)}
              </GezintiOgesi>
            ))}
          </div>
        </div>
      }
    >
      {proje === "avan" ? (
        <AvanOfis />
      ) : (
        <section className="overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
          <header className="border-b border-cizgi px-5 py-3.5">
            <h2 className="text-[14px] font-semibold">{cumleDuzeni(g.baslik)}</h2>
            <p className="mt-0.5 text-[12.5px] text-metin-2">{g.aciklama}</p>
          </header>
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-cizgi text-left text-[11.5px] text-metin-3">
                <th className="px-5 py-2 font-medium">Kabul</th>
                <th className="w-32 px-2 py-2 text-right font-medium">Varsayılan</th>
                <th className="w-44 px-5 py-2 text-right font-medium">Ofis değeri</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cizgi">
              {g.alanlar.map((k) => {
                const [ad, ack] = s.etiket[k] ?? [k];
                const birim = /\(([^()]+)\)\s*$/.exec(ad)?.[1];
                const deger = ofis[k] ?? "";
                const metin = s.metin.includes(k);
                return (
                  <tr key={k} className={cn("align-top", deger !== "" && "bg-vurgu-acik/40")}>
                    <td className="px-5 py-2.5">
                      <label htmlFor={`of-${k}`} className="block font-medium">
                        {birim ? ad.replace(/\s*\([^()]+\)\s*$/, "") : ad}
                      </label>
                      {ack && <p className="mt-0.5 text-[12px] leading-snug text-metin-3">{ack}</p>}
                    </td>
                    <td className="sayi px-2 py-2.5 text-right text-metin-3">{sayiYaz(s.varsayilan[k])}</td>
                    <td className="px-5 py-2">
                      <Girdi
                        id={`of-${k}`}
                        value={deger}
                        placeholder={sayiYaz(s.varsayilan[k])}
                        birim={birim}
                        yazi={metin}
                        onChange={(e) => setOfis({ ...ofis, [k]: e.target.value })}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}
    </BasvuruSayfasi>
  );
}

/*  Avan sabitleri /api/secenekler'den gelir ama ETİKETLERİ bugün index.html'de
    yazılı.  Yeni ön yüz etiket uydurmaz:  sunucu uygulamadaki gibi etiket
    döndürene kadar anahtar adıyla gösterilir ( iskelette sunucuya eklenecek ).  */
function AvanOfis() {
  const sec = useQuery({ queryKey: ["secenekler"], queryFn: api.secenekler });
  const ofis = (sec.data?.ofis_varsayilan ?? {}) as Record<string, unknown>;
  const b = (sec.data?.sabit_b ?? {}) as Record<string, unknown>;
  return (
    <div className="space-y-4">
      <p className="rounded-orta border border-uyari-cizgi bg-uyari-acik px-4 py-3 text-[12.5px] leading-relaxed text-uyari">
        Avan sabitlerinin etiketleri sunucudan gelmiyor ( bugün index.html'de yazılı ).  İskelette{" "}
        <span className="font-mono">/api/secenekler</span> uygulamadaki gibi etiket döndürecek;  burada anahtar adları.
      </p>
      {[
        ["Ofis varsayılanları", ofis],
        ["Sabitler ( B )", b],
      ].map(([ad, d]) => (
        <section key={ad as string} className="overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
          <header className="border-b border-cizgi px-5 py-3 text-[14px] font-semibold">{ad as string}</header>
          <div className="grid grid-cols-2 gap-x-8 px-5 py-2 text-[13px] md:grid-cols-3">
            {Object.entries(d as Record<string, unknown>).map(([k, v]) => (
              <div key={k} className="flex items-baseline justify-between border-b border-cizgi py-1.5">
                <span className="font-mono text-[12px] text-metin-2">{k}</span>
                <span className="sayi">{sayiYaz(v)}</span>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
