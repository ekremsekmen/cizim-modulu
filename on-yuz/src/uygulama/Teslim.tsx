/*  TESLİM — paket ve hesap PDF'i.
    Paket:  /api/indir/uygulama-dwg ( kapak + hesap PDF'i + çizimler DXF / PDF +
    .uygulama proje dosyası, tek ZIP ).  Sunucu hükme bakmadan üretir;  biz
    önce iki şeyi gösteririz:  hükümler ve KULLANICININ GİRMEDİĞİ değerler.
    İkincisinin onayı sorumluluktur:  hesap o değerlerle yapıldı.            */
import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Check, ChevronRight, FileArchive, FileCode, FileText, Loader2, DraftingCompass, ScrollText } from "lucide-react";
import { indir, paketNotu, type Alan, type AlanSemasi, type CokluYanit, type Deger, type UygulamaIstegi } from "@/lib/api";
import { alanOku, gizliAlanlar, type Ham, type UygulamaProjesi } from "@/lib/proje";
import { dosyaGovdesi } from "@/lib/dosya";
import { kapakSayfasi } from "@/lib/kapak";
import { cn, etiketBol, sayiYaz } from "@/lib/utils";
import { Cekmece, Dugme, Rozet } from "@/components/ui";
import { HukumRozeti } from "@/components/HesapBelgesi";

export function Teslim({
  acik,
  degisti,
  sema,
  proje,
  hesap,
  istek,
  engel,
  ofis,
  cizimSayisi,
  projeyiAc,
}: {
  acik: boolean;
  degisti: (a: boolean) => void;
  sema: AlanSemasi;
  proje: UygulamaProjesi;
  /**  Son başarılı hesap  */
  hesap: CokluYanit | undefined;
  /**  GÜNCEL girdinin isteği ( kural dışı girdi varsa yok ):  paket ekranda
       görünen girdiyle iner, gecikmeli olanla değil  */
  istek: UygulamaIstegi | null;
  /**  Paketi şimdi indirmeyi engelleyen durum:  ciddi = girdi düzeltilmeli,
       değilse geçici ( hesap yolda );  yalnizPaket:  hesap geçerli, yalnız
       çizim sorunlu — hükümler görünür, hesap PDF'i iner  */
  engel: { metin: string; ciddi: boolean; yalnizPaket?: boolean } | null;
  ofis: Ham;
  cizimSayisi: number;
  projeyiAc: () => void;
}) {
  const [onay, setOnay] = useState(false);
  const [listeAcik, setListeAcik] = useState(false);
  const durdu = !!engel?.ciddi && !engel.yalnizPaket;

  //  Görünür ( gelişmiş olmayan ) alanlardan kullanıcının yazmadıkları:
  //  hesap şemanın varsayılanıyla ( örnek projenin değeriyle ) yapıldı.
  const girilmeyen = useMemo(() => {
    const gizli = gizliAlanlar(sema, proje);
    return proje.asansorler.map((_, i) =>
      sema.gruplar.flatMap((g) =>
        g.alanlar
          .filter(
            (a) =>
              !a.gelismis &&
              !gizli.has(a.anahtar) &&
              a.tur !== "metin" &&
              alanOku(proje, sema, i, a.anahtar) === undefined &&
              (a.varsayilan !== null || a.kaynak === "KATALOG"),
          )
          .map((a) => {
            const d = hesap?.asansorler?.[i]?.girdi?.[a.anahtar] ?? a.varsayilan;
            return {
              grup: g.ad,
              ad: a.anahtar === "mk_yok" ? "Makine dairesi" : etiketBol(a.etiket)[0],
              deger: d === null || d === undefined ? null : degerYaz(a, d),
              birim: typeof d === "number" && a.birim !== "—" ? a.birim : "",
              sayi: typeof d === "number",
              katalog: a.kaynak === "KATALOG",
            };
          }),
      ),
    );
  }, [sema, proje, hesap]);
  const toplam = girilmeyen.reduce((t, l) => t + l.length, 0);

  //  Paketin içindeki .uygulama eski arayüzün biçimindedir:  iki arayüzde de açılır
  //  Kapak sayfası:  dolu alan varsa sunucu paketin başına koyar ( eski arayüz gibi )
  const kapak = kapakSayfasi({ ...proje.kapak, ...proje.kimlik });
  const govde = () => ({ ...istek, kapak_sayfasi: kapak, proje_dosyasi: dosyaGovdesi(proje, sema, ofis) });
  const paket = useMutation({ mutationFn: () => indir("uygulama-dwg", govde()) });
  const pdf = useMutation({ mutationFn: () => indir("uygulama-pdf", govde()) });
  const hata = paket.data?.hata || pdf.data?.hata;
  const notlar = paket.data?.notlar ?? [];

  const kalan = (hesap?.asansorler ?? []).map((a) => (a.bolumler ?? []).filter((b) => b.sonuc?.uygun === false).length);

  return (
    <Cekmece
      acik={acik}
      degisti={degisti}
      baslik="Teslim"
      aciklama="Hesap PDF'i, çizimler ve proje dosyası tek pakette."
    >
      <div className="space-y-6 px-5 py-5">
        {/* 1 — hükümler */}
        <section>
          <Baslik no="1">Hükümler</Baslik>
          {engel && (
            <div
              className={cn(
                "mb-2 rounded-orta border px-3.5 py-3 text-[12.5px]",
                engel.ciddi ? "border-red-cizgi bg-red-acik text-red" : "border-cizgi bg-yuzey-2 text-metin-2",
              )}
            >
              {engel.metin}
            </div>
          )}
          {durdu ? null : (
            <div className="divide-y divide-cizgi overflow-hidden rounded-orta border border-cizgi">
              {(hesap?.ozet?.asansorler ?? []).map((a, i) => (
                <div key={a.no} className="flex items-center justify-between gap-3 px-3.5 py-2.5">
                  <span className="text-[13px] font-medium">{a.tanim}</span>
                  <span className="flex items-center gap-2">
                    {kalan[i] > 0 && <span className="text-[12px] text-metin-3">{kalan[i]} bölüm</span>}
                    <HukumRozeti uygun={a.tumu_uygun} />
                  </span>
                </div>
              ))}
            </div>
          )}
          {!engel?.ciddi && hesap?.ozet && !hesap.ozet.tumu_uygun && (
            <p className="mt-2 text-[12.5px] leading-relaxed text-metin-2">
              Paket indirilebilir;  uygun olmayan bölümler paftada <b className="font-semibold text-red">UYGUN DEĞİLDİR</b>{" "}
              hükmüyle basılır.
            </p>
          )}
        </section>

        {/* 2 — girilmeyen değerler */}
        <section>
          <Baslik no="2">Sizin girmediğiniz değerler</Baslik>
          <div className="rounded-orta border border-uyari-cizgi bg-uyari-acik">
            <button
              type="button"
              onClick={() => setListeAcik(!listeAcik)}
              aria-expanded={listeAcik}
              className="flex w-full items-center gap-2 px-3.5 py-3 text-left"
            >
              <ChevronRight className={cn("size-3.5 text-uyari transition-transform", listeAcik && "rotate-90")} />
              <span className="flex-1 text-[12.5px] text-metin">
                Hesap <b className="font-semibold">{toplam} değeri</b> programın varsayılanıyla yaptı
              </span>
              <Rozet tur="uyari">{toplam}</Rozet>
            </button>
            {listeAcik && (
              <div className="max-h-64 overflow-y-auto border-t border-uyari-cizgi bg-yuzey">
                {girilmeyen.map((liste, i) => (
                  <div key={i}>
                    {proje.asansorler.length > 1 && (
                      <p className="bg-yuzey-2 px-3.5 py-1 text-[11.5px] font-medium text-metin-3">Asansör {i + 1}</p>
                    )}
                    <table className="w-full text-[12.5px]">
                      {[...new Set(liste.map((x) => x.grup))].map((grup) => (
                        <tbody key={grup}>
                          <tr>
                            <th colSpan={2} className="bg-yuzey-2 px-3.5 pt-2 pb-1 text-left text-[11.5px] font-medium text-metin-3">
                              {grup}
                            </th>
                          </tr>
                          {liste
                            .filter((x) => x.grup === grup)
                            .map((x) => (
                              <tr key={x.ad} className="border-t border-cizgi">
                                <td className="py-1.5 pl-3.5 text-metin-2">{x.ad}</td>
                                <td className={cn("py-1.5 pr-3.5 text-right whitespace-nowrap", x.sayi && "sayi")}>
                                  {x.deger !== null ? (
                                    <>
                                      {x.deger} {x.birim && <span className="text-metin-3">{x.birim}</span>}
                                    </>
                                  ) : (
                                    <span className="text-metin-3">{x.katalog ? "imalatçıdan" : "kuraldan"}</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      ))}
                    </table>
                  </div>
                ))}
              </div>
            )}
          </div>
          <label className="mt-3 flex cursor-pointer items-start gap-2.5">
            <input
              type="checkbox"
              checked={onay}
              onChange={(e) => setOnay(e.target.checked)}
              className="mt-0.5 size-4 accent-[var(--color-vurgu)]"
            />
            <span className="text-[12.5px] leading-relaxed text-metin-2">
              Bu değerleri gözden geçirdim;  proje bunlarla hesaplanmıştır.
            </span>
          </label>
        </section>

        {/* 3 — paket */}
        <section>
          <div className="flex items-baseline justify-between">
            <Baslik no="3">Paket</Baslik>
            <button type="button" onClick={projeyiAc} className="text-[12px] font-medium text-vurgu hover:underline">
              Proje bilgileri
            </button>
          </div>
          <ul className="divide-y divide-cizgi overflow-hidden rounded-orta border border-cizgi">
            <Icerik
              simge={<ScrollText />}
              ad="Kapak"
              ek={Object.keys(kapak).length ? `${Object.keys(kapak).length} alan dolu` : "kapak alanları boş — kapak girmez"}
              soluk={!Object.keys(kapak).length}
            />
            <Icerik simge={<FileText />} ad="Uygulama projesi hesapları" ek={`PDF · ${hesap?.asansorler?.[0]?.bolumler?.length ?? "—"} bölüm × ${proje.asansorler.length} asansör`} />
            <Icerik simge={<DraftingCompass />} ad="Çizimler" ek={`DXF / DWG ve PDF · asansör başına ${cizimSayisi || "—"} çizim`} />
            <Icerik simge={<FileCode />} ad="Proje dosyası" ek=".uygulama — geri dönüş noktası" />
          </ul>
        </section>

        {notlar.length > 0 && (
          <div className="space-y-1 rounded-orta border border-uyari-cizgi bg-uyari-acik px-3.5 py-3 text-[12.5px] text-uyari">
            <p className="font-medium">Paket indi — dikkat:</p>
            {notlar.map((n) => (
              <p key={n}>{paketNotu(n)}</p>
            ))}
          </div>
        )}

        {hata && (
          <pre className="rounded-orta border border-red-cizgi bg-red-acik px-3.5 py-3 font-sans text-[12.5px] whitespace-pre-wrap text-red">
            {hata}
          </pre>
        )}
      </div>

      <div className="sticky bottom-0 flex items-center justify-between gap-3 border-t border-cizgi bg-yuzey px-5 py-3.5">
        <Dugme onClick={() => pdf.mutate()} disabled={(!!engel && !engel.yalnizPaket) || pdf.isPending}>
          {pdf.isPending ? <Loader2 className="animate-spin" /> : <FileText />}
          Yalnız hesap PDF'i
        </Dugme>
        <Dugme tur="birincil" boy="buyuk" onClick={() => paket.mutate()} disabled={!!engel || !onay || paket.isPending}>
          {paket.isPending ? <Loader2 className="animate-spin" /> : paket.isSuccess && !paket.data?.hata ? <Check /> : <FileArchive />}
          Paketi indir · ZIP
        </Dugme>
      </div>
    </Cekmece>
  );
}

function Baslik({ no, children }: { no: string; children: React.ReactNode }) {
  return (
    <h3 className="mb-2.5 flex items-center gap-2 text-[13px] font-semibold">
      <span className="sayi flex size-5 items-center justify-center rounded-full bg-black/[0.06] text-[11px] text-metin-2">
        {no}
      </span>
      {children}
    </h3>
  );
}

function Icerik({ simge, ad, ek, soluk }: { simge: React.ReactNode; ad: string; ek: string; soluk?: boolean }) {
  return (
    <li className={cn("flex items-center gap-3 px-3.5 py-2.5", soluk && "opacity-55")}>
      <span className="text-metin-2 [&_svg]:size-4">{simge}</span>
      <span className="flex-1 text-[13px] font-medium">{ad}</span>
      <span className="text-right text-[12px] text-metin-3">{ek}</span>
    </li>
  );
}

/**  Değerin ekrandaki adı:  seçimin metni ( 2 → "2:1" ), makine dairesi var / yok.  */
function degerYaz(a: Alan, d: Deger): string {
  if (a.anahtar === "mk_yok") return d === false || d === "false" ? "Var" : "Yok ( MRL )";
  if (typeof d === "boolean") return d ? "evet" : "hayır";
  return a.secenek_metni?.[String(d)] ?? sayiYaz(d);
}
