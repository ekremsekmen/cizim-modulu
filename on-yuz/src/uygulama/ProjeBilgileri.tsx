/*  PROJE BİLGİLERİ — kimlik ( dosya adı, çizimin anteti ), kapak sayfası,
    asansör adedi, proje dosyası.  Kimlik ve kapak hesaba girmez.            */
import { useState } from "react";
import { useNavigate } from "react-router";
import { ChevronRight, Download, FolderOpen, Trash } from "lucide-react";
import type { AlanSemasi } from "@/lib/api";
import type { Ham, UygulamaProjesi } from "@/lib/proje";
import { dosyayaKaydet } from "@/lib/dosya";
import { KAPAK_GRUPLARI } from "@/lib/kapak";
import { cn } from "@/lib/utils";
import { Bolumlu, Cekmece, Dugme } from "@/components/ui";
import { useDosyaAc } from "@/ekranlar/useDosyaAc";

/**  Kimlik kutularında duranlar kapak formunda tekrar sorulmaz  */
const KIMLIKTE = new Set(["project_title", "owner", "sheet_no"]);

export function ProjeBilgileri({
  acik,
  degisti,
  proje,
  guncelle,
  sil,
  sema,
  ofis,
}: {
  acik: boolean;
  degisti: (a: boolean) => void;
  proje: UygulamaProjesi;
  guncelle: (f: (p: UygulamaProjesi) => UygulamaProjesi) => void;
  sil: () => void;
  sema: AlanSemasi;
  ofis: Ham;
}) {
  const git = useNavigate();
  const [kapakAcik, setKapakAcik] = useState(false);
  const [silOnay, setSilOnay] = useState(false);
  const dosya = useDosyaAc(sema, ofis);
  const kimlik = (k: keyof UygulamaProjesi["kimlik"], d: string) =>
    guncelle((p) => ({ ...p, kimlik: { ...p.kimlik, [k]: d } }));
  const kapak = (k: string, d: string) => guncelle((p) => ({ ...p, kapak: { ...p.kapak, [k]: d } }));
  const kapakDolu = Object.values(proje.kapak ?? {}).filter((v) => v.trim()).length;
  const adet = proje.asansorler.length;
  const adetYaz = (n: number) =>
    guncelle((p) => ({
      ...p,
      //  Yeni asansör 1 nolunun kopyası olarak açılır;  azaltmak fazlasını siler
      asansorler:
        n > p.asansorler.length
          ? [...p.asansorler, ...Array.from({ length: n - p.asansorler.length }, () => ({ ...p.asansorler[0] }))]
          : p.asansorler.slice(0, n),
    }));

  return (
    <Cekmece
      acik={acik}
      degisti={degisti}
      baslik="Proje bilgileri"
      aciklama="Hesaba girmez — dosya adında, çizimin antetinde ve kapakta görünür."
      genislik="w-[460px]"
    >
      <div className="space-y-6 px-5 py-5">
        <section className="space-y-3">
          <Alan etiket="Proje adı" id="pb-ad" deger={proje.kimlik.project_title} yaz={(d) => kimlik("project_title", d)} />
          <Alan etiket="İşveren" id="pb-isveren" deger={proje.kimlik.owner} yaz={(d) => kimlik("owner", d)} />
          <Alan etiket="Pafta no" id="pb-pafta" deger={proje.kimlik.sheet_no} yaz={(d) => kimlik("sheet_no", d)} />
        </section>

        <section>
          <button
            type="button"
            onClick={() => setKapakAcik(!kapakAcik)}
            aria-expanded={kapakAcik}
            className="flex w-full items-center gap-1.5 text-left text-[12.5px] font-medium text-metin-2 hover:text-metin"
          >
            <ChevronRight className={cn("size-3.5 transition-transform", kapakAcik && "rotate-90")} />
            Kapak sayfası
            <span className="font-normal text-metin-3">
              · isteğe bağlı{kapakDolu ? ` · ${kapakDolu} alan dolu` : ""}
            </span>
          </button>
          <p className="mt-1 pl-5 text-[12px] leading-relaxed text-metin-3">
            Dolu alan varsa pakete kapak sayfası girer ( avan kapağıyla aynı biçim ).
          </p>
          {kapakAcik && (
            <div className="mt-3 space-y-4 pl-5">
              {KAPAK_GRUPLARI.map((g) => {
                const alanlar = g.alanlar.filter(([k]) => !KIMLIKTE.has(k));
                if (!alanlar.length) return null;
                return (
                  <div key={g.baslik}>
                    <p className="mb-1.5 text-[11.5px] font-medium tracking-wide text-metin-3 uppercase">{g.baslik}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {alanlar.map(([k, e]) => (
                        <Alan key={k} etiket={e} id={`pb-k-${k}`} deger={proje.kapak?.[k] ?? ""} yaz={(d) => kapak(k, d)} kucuk />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section>
          <p className="text-[12.5px] font-medium text-metin-2">Asansör adedi</p>
          <div className="mt-1.5">
            <Bolumlu
              etiket="Asansör adedi"
              deger={String(adet)}
              degisti={(d) => adetYaz(Number(d))}
              secenekler={Array.from({ length: sema.asansor_azami }, (_, i) => ({ deger: String(i + 1), ad: String(i + 1) }))}
            />
          </div>
          <p className="mt-2 text-[12px] leading-relaxed text-metin-3">
            Her asansör ayrı kuyudadır.  Yeni asansör 1 nolu asansörün kopyası olarak açılır;  binaya ait alanlar ( makine
            dairesi, temel ) bütün asansörlerde aynıdır.
          </p>
        </section>

        <section>
          <p className="text-[12.5px] font-medium text-metin-2">Proje dosyası</p>
          <p className="mt-1 text-[12px] leading-relaxed text-metin-3">
            Proje bu tarayıcıda kendiliğinden saklanır.  Dosya ( .uygulama ) eski arayüzle aynı biçimdedir:  ikisinde de
            açılır.
          </p>
          <div className="mt-2.5 flex gap-2">
            <Dugme onClick={() => dosyayaKaydet(proje, sema, ofis)}>
              <Download /> Dosyaya kaydet
            </Dugme>
            <Dugme tur="hayalet" onClick={dosya.sec}>
              <FolderOpen /> Dosyadan aç
            </Dugme>
            {dosya.girdi}
          </div>
          {dosya.hata && <p className="mt-2 text-[12px] text-red">{dosya.hata}</p>}
        </section>

        <section className="border-t border-cizgi pt-5">
          {silOnay ? (
            <div className="flex items-center justify-between gap-3 rounded-orta border border-red-cizgi bg-red-acik px-3.5 py-2.5">
              <span className="text-[12.5px] text-red">Proje bu tarayıcıdan silinsin mi?  Geri alınamaz.</span>
              <span className="flex gap-1.5">
                <Dugme boy="kucuk" onClick={() => setSilOnay(false)}>
                  Vazgeç
                </Dugme>
                <Dugme
                  boy="kucuk"
                  tur="tehlike"
                  onClick={() => {
                    sil();
                    git("/", { replace: true });
                  }}
                >
                  Sil
                </Dugme>
              </span>
            </div>
          ) : (
            <Dugme tur="hayalet" boy="kucuk" className="text-red hover:text-red" onClick={() => setSilOnay(true)}>
              <Trash /> Projeyi sil
            </Dugme>
          )}
        </section>
      </div>
    </Cekmece>
  );
}

function Alan({
  etiket,
  id,
  deger,
  yaz,
  kucuk,
}: {
  etiket: string;
  id: string;
  deger: string;
  yaz: (d: string) => void;
  kucuk?: boolean;
}) {
  return (
    <div>
      <label htmlFor={id} className={cn("font-medium text-metin-2", kucuk ? "text-[12px]" : "text-[12.5px]")}>
        {etiket}
      </label>
      <input
        id={id}
        value={deger}
        maxLength={200}
        onChange={(e) => yaz(e.target.value)}
        className={cn(
          "mt-1 w-full rounded-kucuk border border-cizgi-2 bg-yuzey px-3 outline-none focus:border-vurgu focus:ring-3 focus:ring-vurgu/15",
          kucuk ? "h-8 text-[13px]" : "h-9 text-[13.5px]",
        )}
      />
    </div>
  );
}
