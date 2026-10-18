import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router";
import { ArrowRight, Building, FileUp, FlaskConical, ChartLine, Ruler } from "lucide-react";
import { BasvuruBaglantilari, Isaret, UstSerit } from "@/components/Kabuk";
import { Dugme, Rozet } from "@/components/ui";
import { api } from "@/lib/api";
import { projeListesi, useGoreceZaman, useOfisStandardi, type ProjeOzeti } from "@/lib/proje";
import { useDosyaAc } from "./useDosyaAc";
import { cn } from "@/lib/utils";

/*  AÇILIŞ
    Üç iş:  yeni proje başlat ( uygulama · avan ), dosyadan aç, son projeye dön.
    Örnek proje ayrıdır ve öyle görünür — yeni kullanıcı onu kendi projesi sanmaz.  */
export function Acilis() {
  const projeler = projeListesi();
  //  Bilinmeyen proje adresinden gelindiyse ( başka tarayıcının bağlantısı, silinmiş proje )
  const bulunamadi = (useLocation().state as { bulunamadi?: string } | null)?.bulunamadi;
  return (
    <div className="flex min-h-dvh flex-col">
      <UstSerit
        sol={
          <>
            <Isaret />
            <span className="text-[13px] font-semibold">Asansör Proje Programı</span>
          </>
        }
        sag={<BasvuruBaglantilari />}
      />
      <main className="mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 content-start gap-x-10 gap-y-12 px-8 pt-14 pb-16 lg:grid-cols-[1fr_400px]">
        <section aria-labelledby="baslat">
          {bulunamadi && (
            <p role="status" className="mb-6 rounded-orta border border-uyari-cizgi bg-uyari-acik px-4 py-2.5 text-[12.5px] text-uyari">
              Bu proje bu tarayıcıda yok — projeler tarayıcıda saklanır;  başka bilgisayardaysa dosyasını açın.
            </p>
          )}
          <h1 id="baslat" className="text-2xl font-semibold tracking-tight">
            Proje başlat
          </h1>
          <p className="mt-1.5 text-[14px] text-metin-2">
            Hesap ve çizim sunucuda yapılır;  proje bu tarayıcıda ve proje dosyasında saklanır.
          </p>

          <div className="mt-7 grid gap-4 md:grid-cols-2">
            <BaslatKarti
              to="/uygulama/yeni"
              simge={<Building />}
              baslik="Uygulama projesi"
              metin="Mukavemet hesapları, kuyu kesitleri ve planları, elektrik ve topraklama."
              ciktilar={["Hesap PDF'i", "DXF · DWG", "Teslim paketi"]}
              kaynak="TS EN 81-20 · TS EN 81-50 · MMO 208"
              birincil
            />
            <BaslatKarti
              to="/avan/trafik"
              simge={<ChartLine />}
              baslik="Avan proje"
              metin="Trafik hesabı, avan hesapları ve proje kapağı."
              ciktilar={["Trafik paftası", "Avan PDF'i", "Kapak"]}
              kaynak="MMO/697 · ISO 8100-32 · IEEE 80"
            />
          </div>

          <DosyaAc />

          <div className="mt-6 flex items-start gap-3 rounded-buyuk border border-cizgi bg-yuzey px-4 py-3.5">
            <FlaskConical className="mt-0.5 size-4 shrink-0 text-metin-3" />
            <div className="text-[13px] leading-relaxed text-metin-2">
              <Link to="/uygulama/ornek" className="font-medium text-vurgu hover:underline">
                Örnek projeyi aç
              </Link>{" "}
              — programı tanımak için.  Başlığında hep <b className="font-semibold text-metin">ÖRNEK</b> yazar;  değerleri
              yeni projelere taşınmaz.
            </div>
          </div>
        </section>

        <aside aria-labelledby="son">
          <div className="flex items-baseline justify-between">
            <h2 id="son" className="text-[13px] font-semibold">
              Son projeler
            </h2>
            <span className="text-[12px] text-metin-3">bu tarayıcıda</span>
          </div>
          <div className="mt-3 overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
            {projeler.length === 0 ? (
              <div className="px-5 py-10 text-center">
                <Ruler className="mx-auto size-5 text-metin-3" />
                <p className="mt-2 text-[13px] font-medium">Henüz proje yok</p>
                <p className="mt-1 text-[12.5px] text-metin-3">Başlattığınız projeler burada listelenir.</p>
              </div>
            ) : (
              <ul className="divide-y divide-cizgi">
                {projeler.slice(0, 8).map((p) => (
                  <SonProje key={p.id} p={p} />
                ))}
              </ul>
            )}
          </div>
          <p className="mt-3 text-[12px] leading-relaxed text-metin-3">
            Başka bilgisayarda açmak için projeyi dosya olarak kaydedin ( Proje › Dosyaya kaydet ).
          </p>
        </aside>

        {/*  İş akışı:  yeni kullanıcı ne olacağını baştan görür  */}
        <section aria-labelledby="akis" className="lg:col-span-2">
          <h2 id="akis" className="text-[13px] font-semibold">
            Uygulama projesi nasıl ilerler
          </h2>
          <ol className="mt-3 grid gap-3 md:grid-cols-3">
            {[
              ["Girdiler", "Ölçü formundaki değerleri yazın.  Çizim ve hesap yazdıkça gelir;  girmediğiniz alan programın değeriyle, soluk görünür."],
              ["Uygunluk", "Kalan bölümler en üstte, sunucunun önerdiği çareyle.  Bölüme tıklayın:  ona bağlı girdi grupları açılır."],
              ["Teslim", "Girmediğiniz değerleri onaylayın;  hesap PDF'i, çizimler ve proje dosyası tek pakette iner."],
            ].map(([ad, metin], i) => (
              <li key={ad} className="flex gap-3 rounded-buyuk border border-cizgi bg-yuzey px-4 py-3.5">
                <span className="sayi flex size-6 shrink-0 items-center justify-center rounded-full bg-black/[0.06] text-[11.5px] text-metin-2">
                  {i + 1}
                </span>
                <span>
                  <span className="block text-[13px] font-semibold">{ad}</span>
                  <span className="mt-0.5 block text-[12.5px] leading-relaxed text-metin-2">{metin}</span>
                </span>
              </li>
            ))}
          </ol>
        </section>
      </main>
    </div>
  );
}

function BaslatKarti({
  to,
  simge,
  baslik,
  metin,
  ciktilar,
  kaynak,
  birincil,
}: {
  to: string;
  simge: React.ReactNode;
  baslik: string;
  metin: string;
  ciktilar: string[];
  kaynak: string;
  birincil?: boolean;
}) {
  return (
    <Link
      to={to}
      className={cn(
        "group flex flex-col rounded-buyuk border bg-yuzey p-5 shadow-panel transition-[border-color,box-shadow] hover:shadow-kalkik",
        birincil ? "border-vurgu-cizgi hover:border-vurgu" : "border-cizgi hover:border-cizgi-2",
      )}
    >
      <span
        className={cn(
          "flex size-9 items-center justify-center rounded-orta [&_svg]:size-[18px]",
          birincil ? "bg-vurgu text-white" : "bg-black/[0.05] text-metin",
        )}
      >
        {simge}
      </span>
      <span className="mt-4 text-[16px] font-semibold">{baslik}</span>
      <span className="mt-0.5 text-[11.5px] text-metin-3">{kaynak}</span>
      <span className="mt-2.5 text-[13px] leading-relaxed text-metin-2">{metin}</span>
      <span className="mt-4 flex flex-wrap gap-1.5">
        {ciktilar.map((c) => (
          <Rozet key={c}>{c}</Rozet>
        ))}
      </span>
      <span className="mt-5 flex items-center justify-end border-t border-cizgi pt-3.5">
        <span
          className={cn(
            "inline-flex items-center gap-1 text-[13px] font-medium",
            birincil ? "text-vurgu" : "text-metin",
          )}
        >
          Yeni {baslik.toLocaleLowerCase("tr-TR")} <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
        </span>
      </span>
    </Link>
  );
}

function DosyaAc() {
  const sema = useQuery({ queryKey: ["alanlar"], queryFn: api.alanlar, staleTime: Infinity });
  const [ofis] = useOfisStandardi();
  const dosya = useDosyaAc(sema.data, ofis);
  const [ustunde, setUstunde] = useState(false);
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setUstunde(true);
      }}
      onDragLeave={() => setUstunde(false)}
      onDrop={(e) => {
        e.preventDefault();
        setUstunde(false);
        void dosya.ac(e.dataTransfer.files[0]);
      }}
      className={cn(
        "mt-4 flex items-center gap-4 rounded-buyuk border border-dashed px-5 py-4 transition-colors",
        ustunde ? "border-vurgu bg-vurgu-acik" : "border-cizgi-2 bg-yuzey-2",
      )}
    >
      <span className="flex size-9 items-center justify-center rounded-orta border border-cizgi bg-yuzey">
        <FileUp className="size-4 text-metin-2" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[13.5px] font-medium">Proje dosyası aç</p>
        <p className={cn("text-[12.5px]", dosya.hata ? "text-red" : "text-metin-3")}>
          {dosya.hata || (
            <>
              <span className="font-mono">.uygulama</span> dosyasını buraya bırakın — eski arayüzün dosyaları da açılır
            </>
          )}
        </p>
      </div>
      <Dugme onClick={dosya.sec}>Dosya seç</Dugme>
      {dosya.girdi}
    </div>
  );
}

function SonProje({ p }: { p: ProjeOzeti }) {
  const zaman = useGoreceZaman(p.guncellendi);
  const git = useNavigate();
  const durum = !p.son ? (
    <Rozet>Hesaplanmadı</Rozet>
  ) : p.son.hata ? (
    <Rozet tur="uyari">Hesap durdu</Rozet>
  ) : p.son.uygunDegil ? (
    <Rozet tur="red">{p.son.uygunDegil} bölüm uygun değil</Rozet>
  ) : (
    <Rozet tur="uygun">Uygun</Rozet>
  );
  return (
    <li>
      <button
        type="button"
        onClick={() => git(p.tur === "uygulama" ? `/uygulama/${p.id}` : "/avan/trafik")}
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-yuzey-2"
      >
        <span className="flex size-8 shrink-0 items-center justify-center rounded-orta bg-black/[0.04] text-metin-2">
          {p.tur === "uygulama" ? <Building className="size-4" /> : <ChartLine className="size-4" />}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5">
            <span className="truncate text-[13.5px] font-medium">{p.ad}</span>
            {p.ornek && <Rozet tur="uyari">ÖRNEK</Rozet>}
          </span>
          <span className="block text-[12px] text-metin-3">
            {p.tur === "uygulama" ? "Uygulama" : "Avan"}
            {p.son ? ` · ${p.son.adet} asansör` : ""} · {zaman}
          </span>
        </span>
        {durum}
      </button>
    </li>
  );
}
