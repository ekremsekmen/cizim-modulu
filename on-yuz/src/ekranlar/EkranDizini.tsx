/*  EKRAN DİZİNİ — yalnız geliştirmede ( /ekranlar ):  her ekran, ne işe
    yaradığı, hangi uçtan beslendiği ve o durumu kuran bir bağlantı.  Ekran
    ekran geçişte görsel denetim buradan yapılır ( araclar/on_yuz_goruntu.py ).  */
import { useNavigate } from "react-router";
import { ArrowUpRight } from "lucide-react";
import { Isaret } from "@/components/Kabuk";
import { yeniUygulama } from "@/lib/proje";

type Ekran = {
  no: string;
  ad: string;
  is: string;
  uclar: string[];
  ac: () => string;
};

function projeAc(degerler: Record<string, string> = {}, ornek = false) {
  const p = yeniUygulama(ornek);
  if (Object.keys(degerler).length) {
    p.asansorler = [degerler];
    localStorage.setItem(`asansor:proje:${p.id}`, JSON.stringify(p));
  }
  return p.id;
}

const EKRANLAR: Ekran[] = [
  {
    no: "1",
    ad: "Açılış",
    is: "Yeni uygulama / avan projesi, dosyadan aç, son projeler ( durumlarıyla ).  Örnek proje ayrı ve etiketli.",
    uclar: ["— ( tarayıcı belleği )"],
    ac: () => "/",
  },
  {
    no: "2",
    ad: "Uygulama · çalışma alanı",
    is: "Tek ekran:  girdiler ( şemadan ) · çizim · uygunluk.  Yazdıkça hesap ve çizim yenilenir;  grup başlığında o gruba bağlı kalan bölüm sayısı.",
    uclar: ["GET /api/uygulama/alanlar", "POST /api/uygulama/coklu", "POST /api/uygulama/cizimler"],
    ac: () => `/uygulama/${projeAc()}`,
  },
  {
    no: "3",
    ad: "Ölçü kutusu",
    is: "Çizimde ölçüye tıklayınca:  ölçüyü belirleyen girdiler ( eğimiyle ) ve yeni ölçü → girdi değişikliği, sunucu çizimi yeniden kurup doğrular.",
    uclar: ["POST /api/uygulama/olcu", "POST /api/uygulama/olcu_degistir"],
    ac: () => `/uygulama/${projeAc()}?cizim=kuyu_plani`,
  },
  {
    no: "4",
    ad: "Uygulama · hesap görünümü",
    is: "Paftanın ekrandaki okuması:  bölüm → adımlar ( formül · işlem · değer · kaynak ) → hüküm.  Uygunluktaki bölüme tıklamak buraya getirir.",
    uclar: ["POST /api/uygulama/coklu"],
    ac: () => `/uygulama/${projeAc()}?gorunum=hesap`,
  },
  {
    no: "5",
    ad: "Hesap durdu",
    is: "Kuyu kabinden dar:  sunucu geometriyle durur, sebepleri yazar.  Son geçerli çizim ve hükümler yerinde kalır, \"güncel değil\" işaretiyle.",
    uclar: ["POST /api/uygulama/coklu → aktif: false"],
    ac: () => `/uygulama/${projeAc({ kuyu_genisligi: "1200" })}`,
  },
  {
    no: "6",
    ad: "Kural dışı girdi",
    is: "Sunucunun kuralıyla ( en az / en çok / tam sayı ) ön yüzde yakalanır:  istek gitmez, alan işaretlenir, karttan alana gidilir.",
    uclar: ["GET /api/uygulama/alanlar → kurallar"],
    ac: () => `/uygulama/${projeAc({ durak_adedi: "250" })}`,
  },
  {
    no: "7",
    ad: "Teslim",
    is: "Hükümler, sizin girmediğiniz değerler ( onay ), paket içeriği.  Paket:  kapak + hesap PDF'i + çizimler DXF / PDF + .uygulama.",
    uclar: ["POST /api/indir/uygulama-dwg", "POST /api/indir/uygulama-pdf"],
    ac: () => `/uygulama/${projeAc()}?teslim=1`,
  },
  {
    no: "8",
    ad: "Ofis standardı",
    is: "Bütün projelerde geçerli kabuller, gruplu.  Değişen değer işaretli, varsayılan yanında.",
    uclar: ["GET /api/uygulama/alanlar → sabitler"],
    ac: () => "/ofis-standardi",
  },
  {
    no: "9",
    ad: "Tablolar",
    is: "Hesabın okuduğu tablolar olduğu gibi ( ray · NPU · halat · ω … ), kaynağıyla.",
    uclar: ["GET /api/uygulama/alanlar → tablolar"],
    ac: () => "/tablolar",
  },
  {
    no: "10",
    ad: "Avan · trafik",
    is: "Bina, nüfus, asansör tipleri;  sonuç cümlesi, karar ölçütleri, alternatifler, hesap belgesi.",
    uclar: ["GET /api/secenekler", "POST /api/trafik"],
    ac: () => "/avan/trafik",
  },
  {
    no: "11",
    ad: "Avan · hesaplar",
    is: "Asansör adedi, kapasite ve hız trafikten gelir;  motor, kuvvet, aydınlatma, kesit, topraklama.",
    uclar: ["POST /api/avan"],
    ac: () => "/avan/hesaplar",
  },
  {
    no: "12",
    ad: "Avan · kapak",
    is: "Kapak alanları;  asansör satırları hesaptan dolar.  Önizleme sunucunun ürettiği PDF'in kendisi.",
    uclar: ["POST /api/indir/kapak-pdf"],
    ac: () => "/avan/kapak",
  },
];

export function EkranDizini() {
  const git = useNavigate();
  return (
    <div className="min-h-dvh">
      <header className="border-b border-cizgi bg-yuzey">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-8 py-5">
          <Isaret className="size-7" />
          <div>
            <h1 className="text-[17px] font-semibold tracking-tight">Ekran dizini</h1>
            <p className="text-[12.5px] text-metin-2">React · TypeScript · Vite · Tailwind · Radix — çalışan sunucuya bağlı</p>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-8 py-8">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {EKRANLAR.map((e) => (
            <button
              key={e.no}
              type="button"
              onClick={() => git(e.ac())}
              className="group flex flex-col rounded-buyuk border border-cizgi bg-yuzey p-4 text-left shadow-panel transition-shadow hover:border-cizgi-2 hover:shadow-kalkik"
            >
              <span className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span className="sayi flex size-6 items-center justify-center rounded-full bg-black/[0.06] text-[11.5px] text-metin-2">
                    {e.no}
                  </span>
                  <span className="text-[14px] font-semibold">{e.ad}</span>
                </span>
                <ArrowUpRight className="size-4 text-metin-3 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </span>
              <span className="mt-2 flex-1 text-[12.5px] leading-relaxed text-metin-2">{e.is}</span>
              <span className="mt-3 space-y-0.5 border-t border-cizgi pt-2.5">
                {e.uclar.map((u) => (
                  <span key={u} className="block font-mono text-[11px] text-metin-3">
                    {u}
                  </span>
                ))}
              </span>
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}
