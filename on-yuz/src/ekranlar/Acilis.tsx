import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router";
import { ArrowRight, Building, FileUp, FlaskConical, ChartLine, Plus, Ruler } from "lucide-react";
import { BasvuruBaglantilari, Isaret, UstSerit } from "@/components/Kabuk";
import { Dugme, Rozet } from "@/components/ui";
import { api } from "@/lib/api";
import {
  acilisiYaz,
  avanListeDurumu,
  avanOzeti,
  avanProjesiniOku,
  avanProjesiniYaz,
  BOS_AVAN,
  yeniAvanAcilisi,
} from "@/lib/avan";
import { projeListesi, uygulamaListeDurumu, useGoreceZaman, useOfisStandardi, type ProjeOzeti } from "@/lib/proje";
import { TASLAK_DUZENI, taslakKumeleri } from "@/lib/taslak";
import { useDosyaAc } from "./useDosyaAc";
import { acikAvaniKaydet, useAvanDegisimi } from "@/avan/AvanDegisimOnayi";
import { cn } from "@/lib/utils";

/*  AÇILIŞ
    Dört iş:  yeni proje başlat ( uygulama · avan ), dosyadan aç, taslaktan başla ( lib/taslak ),
    son projeye dön.
    Örnek proje ayrıdır ve öyle görünür — yeni kullanıcı onu kendi projesi sanmaz.  */
export function Acilis() {
  //  Uygulama projeleri ve avan ( tek proje, kendi kaydından — lib/avan avanOzeti )
  const avan = avanOzeti();
  const avanZamani = useGoreceZaman(avan?.guncellendi ?? 0);
  const git = useNavigate();
  const istemci = useQueryClient();
  //  ( 17 Kas ) Açık avan varken kart ona DEVAM eder;  yenisi ayrı bağlantıdan, önce sorularak
  //  ( AvanDegisimOnayi ) — eskiden kart açık avanın üzerine sormadan boş proje yazıyordu
  const degisim = useAvanDegisimi(() => acikAvaniKaydet(istemci));
  const yeniAvan = () => {
    //  Yeni proje:  açık olan "Geri al" için tutulur ( avan ekranı okur )
    acilisiYaz(yeniAvanAcilisi(avanProjesiniOku()));
    avanProjesiniYaz(BOS_AVAN);
  };
  const projeler = [...projeListesi(), ...(avan ? [avan] : [])].sort((a, b) => b.guncellendi - a.guncellendi);
  //  Bilinmeyen proje adresinden gelindiyse ( başka tarayıcının bağlantısı, silinmiş proje )
  const bulunamadi = (useLocation().state as { bulunamadi?: string } | null)?.bulunamadi;
  const sonProjeler = (
    <section aria-labelledby="son">
      <div className="flex items-baseline justify-between">
        <h2 id="son" className="text-[13px] font-semibold">
          Son projeler
        </h2>
        <span className="text-[12px] text-metin-3">bu tarayıcıda</span>
      </div>
      <div className="mt-3 overflow-hidden rounded-buyuk border border-cizgi bg-yuzey shadow-panel">
        {projeler.length === 0 ? (
          <div className="px-5 py-14 text-center">
            <Ruler className="mx-auto size-5 text-metin-3" />
            <p className="mt-2 text-[13px] font-medium">Henüz proje yok</p>
            <p className="mt-1 text-[12.5px] text-metin-3">Başlattığınız projeler burada listelenir.</p>
          </div>
        ) : (
          <>
            <div aria-hidden className={cn(SUTUNLAR, "hidden border-b border-cizgi bg-yuzey-2 px-4 py-2 text-[11.5px] font-medium text-metin-3 xl:grid")}>
              <span className="pl-11">Proje</span>
              <span>Tür</span>
              <span className="text-right">Asansör</span>
              <span>Güncellendi</span>
              <span>Durum</span>
            </div>
            <ul className="divide-y divide-cizgi">
              {projeler.slice(0, 12).map((p) => (
                <SonProje key={p.id} p={p} />
              ))}
            </ul>
          </>
        )}
      </div>
      <p className="mt-3 text-[12px] leading-relaxed text-metin-3">
        Başka bilgisayarda açmak için projeyi dosya olarak kaydedin ( projenin üst şeridinde Kaydet ).
      </p>
    </section>
  );
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
      {/*  Çalışma masası:  solda eylemler, sağda son projeler tablosu ( geniş ekranı doldurur )  */}
      <main className="mx-auto grid w-full max-w-[1680px] flex-1 grid-cols-1 content-start gap-x-10 gap-y-10 px-5 pt-10 pb-14 sm:px-8 lg:grid-cols-[360px_minmax(0,1fr)] xl:grid-cols-[400px_minmax(0,1fr)] xl:gap-x-14 xl:px-12">
        <section aria-labelledby="baslat">
          {bulunamadi && (
            <p role="status" className="mb-6 rounded-orta border border-uyari-cizgi bg-uyari-acik px-4 py-2.5 text-[12.5px] text-uyari">
              Bu proje bu tarayıcıda yok — projeler tarayıcıda saklanır;  başka bilgisayardaysa dosyasını açın.
            </p>
          )}
          <h1 id="baslat" className="text-2xl font-semibold tracking-tight">
            Proje başlat
          </h1>
          <p className="mt-1.5 text-[13.5px] leading-relaxed text-metin-2">
            Hesap ve çizim sunucuda yapılır;  proje bu tarayıcıda ve proje dosyasında saklanır.
          </p>

          <div className="mt-6 grid gap-3 md:grid-cols-2 lg:grid-cols-1">
            <BaslatKarti
              to="/uygulama/yeni"
              simge={<Building />}
              baslik="Uygulama projesi"
              metin="Mukavemet hesapları, kuyu kesitleri ve planları, elektrik ve topraklama."
              ciktilar={["Hesap PDF'i", "DXF · DWG", "Teslim paketi"]}
              kaynak="TS EN 81-20 · TS EN 81-50 · MMO 208"
              birincil
            />
            <div className="flex flex-col">
              <BaslatKarti
                to="/avan/trafik"
                tikla={avan ? undefined : yeniAvan}
                devam={avan ? { ad: avan.ad, zaman: avanZamani } : undefined}
                simge={<ChartLine />}
                baslik="Avan proje"
                metin="Trafik hesabı, avan hesapları ve proje kapağı."
                ciktilar={["Trafik paftası", "Avan PDF'i", "Kapak"]}
                kaynak="MMO/697 · ISO 8100-32 · IEEE 80"
              />
              {avan && (
                <button
                  type="button"
                  onClick={() =>
                    degisim.sor(() => {
                      yeniAvan();
                      git("/avan/trafik");
                    })
                  }
                  className="mt-1.5 inline-flex items-center gap-1 self-start rounded-kucuk px-1.5 py-1 text-[12.5px] font-medium text-metin-2 hover:bg-black/[0.04] hover:text-metin"
                >
                  <Plus className="size-3.5" /> Yeni avan başlat
                </button>
              )}
              {degisim.pencere}
            </div>
          </div>

          <DosyaAc />

          <div className="mt-3 flex items-start gap-3 rounded-buyuk border border-cizgi bg-yuzey px-4 py-3">
            <FlaskConical className="mt-0.5 size-4 shrink-0 text-metin-3" />
            <div className="text-[12.5px] leading-relaxed text-metin-2">
              <Link to="/uygulama/ornek" className="font-medium text-vurgu hover:underline">
                Örnek projeyi aç
              </Link>{" "}
              — programı tanımak için.  Başlığında hep <b className="font-semibold text-metin">ÖRNEK</b> yazar;  değerleri
              yeni projelere taşınmaz.
            </div>
          </div>
        </section>

        <div className="flex min-w-0 flex-col gap-10">
          {/*  SIRA ( 20 Kas — arayüz taslağı B8:  1440 × 900 ekranda ilk görünen 10 taslak kartıydı, "Son
               projeler" 1.093 px aşağıdaydı ):  kayıtlı proje varsa önce son projeler, taslaklar altında kısa
               liste;  hiç proje yoksa taslak kartları önde  */}
          {projeler.length > 0 ? (
            <>
              {sonProjeler}
              <TaslakListesi kompakt />
            </>
          ) : (
            <>
              <TaslakListesi />
              {sonProjeler}
            </>
          )}

          {/*  İş akışı:  yeni kullanıcı ne olacağını baştan görür  */}
          <section aria-labelledby="akis">
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
        </div>
      </main>
    </div>
  );
}

/**  Son projeler tablosunun sütunları ( başlık ve satır aynı ızgarayı paylaşır );  dar ekranda tek satır listesi.  */
const SUTUNLAR = "xl:grid-cols-[minmax(0,1fr)_88px_64px_104px_168px] xl:gap-x-4 xl:items-center";

function BaslatKarti({
  to,
  tikla,
  simge,
  baslik,
  metin,
  ciktilar,
  kaynak,
  birincil,
  devam,
}: {
  /**  Açık proje varsa ( avan ):  kart ona devam eder — adı ve son değiştiği zaman  */
  devam?: { ad: string; zaman: string };
  to: string;
  /**  Gitmeden önce ( avan:  yeni projeyi kur )  */
  tikla?: () => void;
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
      onClick={tikla}
      className={cn(
        "group flex gap-4 rounded-buyuk border bg-yuzey p-4 shadow-panel transition-[border-color,box-shadow] hover:shadow-kalkik",
        birincil ? "border-vurgu-cizgi hover:border-vurgu" : "border-cizgi hover:border-cizgi-2",
      )}
    >
      <span
        className={cn(
          "flex size-9 shrink-0 items-center justify-center rounded-orta [&_svg]:size-[18px]",
          birincil ? "bg-vurgu text-white" : "bg-black/[0.05] text-metin",
        )}
      >
        {simge}
      </span>
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="text-[15px] font-semibold">{baslik}</span>
        <span className="mt-0.5 text-[11.5px] text-metin-3">{kaynak}</span>
        <span className="mt-2 text-[12.5px] leading-relaxed text-metin-2">{metin}</span>
        {devam && (
          <span className="mt-3 flex flex-col rounded-orta bg-black/[0.035] px-2.5 py-1.5">
            <span className="truncate text-[12.5px] font-medium text-metin">{devam.ad}</span>
            <span className="text-[11.5px] text-metin-3">açık avan projesi · {devam.zaman}</span>
          </span>
        )}
        <span className="mt-3 flex flex-wrap gap-1.5">
          {ciktilar.map((c) => (
            <Rozet key={c}>{c}</Rozet>
          ))}
        </span>
        <span
          className={cn(
            "mt-3 inline-flex items-center gap-1 self-end text-[13px] font-medium",
            birincil ? "text-vurgu" : "text-metin",
          )}
        >
          {devam ? "Devam et" : `Yeni ${baslik.toLocaleLowerCase("tr-TR")}`} <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
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
        "mt-3 flex items-center gap-4 rounded-buyuk border border-dashed px-4 py-3.5 transition-colors",
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
              <span className="font-mono">.uygulama</span> ya da <span className="font-mono">.avan</span> dosyasını buraya
              bırakın — her biri kendi kısmında açılır
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
  //  Bütün projenin son hesabı — yalnız kayıttaki girdinin ( lib/durum );  değilse "Hesaplanmadı"
  const d = p.tur === "uygulama" ? uygulamaListeDurumu(p.id) : avanListeDurumu();
  const durum = !d ? (
    <Rozet>Hesaplanmadı</Rozet>
  ) : d.hukum === "durdu" ? (
    <Rozet tur="uyari">Hesap durdu</Rozet>
  ) : d.hukum === "eksik" ? (
    <Rozet tur="uyari">Hesap eksik</Rozet>
  ) : d.hukum === "uygun_degil" ? (
    <Rozet tur="red">{d.uygunDegil ? `${d.uygunDegil} bölüm uygun değil` : "Uygun değil"}</Rozet>
  ) : (
    <Rozet tur="uygun">Uygun</Rozet>
  );
  const adet = p.adet ?? d?.adet;
  const tur = p.tur === "uygulama" ? "Uygulama" : "Avan";
  return (
    <li>
      <button
        type="button"
        onClick={() => git(p.tur === "uygulama" ? `/uygulama/${p.id}` : "/avan/trafik")}
        className={cn(SUTUNLAR, "flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-yuzey-2 xl:grid")}
      >
        <span className="flex min-w-0 flex-1 items-center gap-3">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-orta bg-black/[0.04] text-metin-2">
            {p.tur === "uygulama" ? <Building className="size-4" /> : <ChartLine className="size-4" />}
          </span>
          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-1.5">
              <span className="truncate text-[13.5px] font-medium">{p.ad}</span>
              {p.ornek && <Rozet tur="uyari">ÖRNEK</Rozet>}
            </span>
            {/*  Tablo sığmayan genişlikte sütunlar yerine alt satır  */}
            <span className="block text-[12px] text-metin-3 xl:hidden">
              {tur}
              {adet ? ` · ${adet} asansör` : ""} · {zaman}
            </span>
          </span>
        </span>
        <span className="hidden text-[12.5px] text-metin-2 xl:block">{tur}</span>
        <span className="sayi hidden text-right text-[12.5px] text-metin-2 xl:block">{adet || "—"}</span>
        <span className="hidden text-[12.5px] text-metin-2 xl:block">{zaman}</span>
        <span className="shrink-0">{durum}</span>
      </button>
    </li>
  );
}

/**  Taslak projeler ( lib/taslak ):  hepsi uygun — tıklanınca yeni proje.  kompakt:  kayıtlı proje varken
     son projelerin altında kısa liste ( kartın özeti ve kaynağı üstüne gelince );  bağlantıların adları
     iki biçimde de aynı  */
function TaslakListesi({ kompakt = false }: { kompakt?: boolean }) {
  return (
    <section aria-labelledby="taslak">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="taslak" className="text-[13px] font-semibold">
          Taslak projeler
        </h2>
        <span className="text-[12px] text-metin-3">{TASLAK_DUZENI}</span>
      </div>
      {taslakKumeleri().map(([duzen, liste]) =>
        kompakt ? (
          <div key={duzen} className="mt-2.5 flex flex-wrap items-center gap-x-2 gap-y-1.5">
            <h3 className="w-full text-[12px] font-medium text-metin-2 sm:w-32">{duzen}</h3>
            {liste.map((t) => (
              <Link
                key={t.kimlik}
                to={`/uygulama/taslak/${t.kimlik}`}
                aria-label={`${t.ad} · ${t.duzen} taslağıyla yeni proje`}
                title={`${t.ozet}  —  ${t.kaynak}`}
                className="inline-flex items-center gap-1.5 rounded-orta border border-cizgi bg-yuzey px-2.5 py-1 text-[12.5px] font-medium shadow-panel hover:border-cizgi-2 hover:text-vurgu"
              >
                <span aria-hidden className="size-1.5 rounded-full bg-uygun" />
                {t.ad}
              </Link>
            ))}
          </div>
        ) : (
          <div key={duzen} className="mt-3">
            <h3 className="text-[12px] font-medium text-metin-2">{duzen}</h3>
            <ul className="mt-2 grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
              {liste.map((t) => (
                <li key={t.kimlik}>
                  <Link
                    to={`/uygulama/taslak/${t.kimlik}`}
                    aria-label={`${t.ad} · ${t.duzen} taslağıyla yeni proje`}
                    className="group flex h-full flex-col rounded-buyuk border border-cizgi bg-yuzey p-4 shadow-panel transition-[border-color,box-shadow] hover:border-cizgi-2 hover:shadow-kalkik"
                  >
                    <span className="flex items-center justify-between gap-2">
                      <span className="text-[14px] font-semibold">{t.ad}</span>
                      <Rozet tur="uygun">Uygun</Rozet>
                    </span>
                    <span className="mt-1 text-[12.5px] text-metin-2">{t.ozet}</span>
                    <span className="mt-2 text-[11.5px] text-metin-3">{t.kaynak}</span>
                    <span className="mt-3 inline-flex items-center gap-1 text-[12.5px] font-medium text-vurgu">
                      Bu taslakla başla <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ),
      )}
      <p className="mt-3 text-[12px] leading-relaxed text-metin-3">
        Taslak yeni bir proje olarak açılır;  değerlerini değiştirebilirsiniz, taslağın kendisi değişmez.
        {kompakt && "  Taslağın özeti üstüne gelince görünür."}
      </p>
    </section>
  );
}
