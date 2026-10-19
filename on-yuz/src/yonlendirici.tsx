import { lazy, Suspense, useEffect } from "react";
import { createBrowserRouter, Navigate, useLocation, useNavigate, useParams, useRouteError } from "react-router";
import { CircleAlert, Loader2 } from "lucide-react";
import { Acilis } from "@/ekranlar/Acilis";
import { ornekProjesi, projeOku, yeniUygulama } from "@/lib/proje";

/*  ADRESLER  ( programın kökünde — FastAPI derlenmiş dosyaları sunar;  eski /yeni buraya yönlenir )
    /                     açılış
    /uygulama/:id         uygulama projesinin çalışma alanı  ( ?gorunum=hesap · ?cizim=kuyu_plani · ?teslim=1 )
    /avan/:adim           avan projesi  ( trafik · hesaplar · kapak )
    /ofis-standardi       ofis standardı ( sabitler )
    /tablolar             programın tabloları
    /ekranlar             ekran dizini — yalnız geliştirmede
    Açılış dışındaki ekranlar ayrı parçalarda iner ( ilk açılış hafif kalır ).  */
const Calisma = lazy(() => import("@/uygulama/Calisma").then((m) => ({ default: m.Calisma })));
const AvanCalisma = lazy(() => import("@/avan/AvanCalisma").then((m) => ({ default: m.AvanCalisma })));
const OfisStandardi = lazy(() => import("@/ekranlar/OfisStandardi").then((m) => ({ default: m.OfisStandardi })));
const Tablolar = lazy(() => import("@/ekranlar/Tablolar").then((m) => ({ default: m.Tablolar })));
const EkranDizini = import.meta.env.DEV
  ? lazy(() => import("@/ekranlar/EkranDizini").then((m) => ({ default: m.EkranDizini })))
  : null;

function Bekle({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex h-dvh items-center justify-center text-metin-3">
          <Loader2 className="size-4 animate-spin" />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

function YeniUygulama({ ornek }: { ornek?: boolean }) {
  const git = useNavigate();
  useEffect(() => {
    git(`/uygulama/${(ornek ? ornekProjesi() : yeniUygulama()).id}`, { replace: true });
  }, [git, ornek]);
  return null;
}

/**  Proje tarayıcıda yoksa açılışa döner — bilinmeyen adres sessizce yeni proje kurmaz.  */
function UygulamaRota() {
  const { id = "" } = useParams();
  const bildirim = (useLocation().state as { bildirim?: string } | null)?.bildirim;
  const proje = projeOku(id);
  if (!proje) return <Navigate to="/" replace state={{ bulunamadi: id }} />;
  return <Calisma key={id} proje={proje} bildirim={bildirim} />;
}

/**  Beklenmedik hata:  geliştirici sayfası yerine ne olduğu ve nereye dönüleceği.
     Proje tarayıcıda kayıtlıdır;  açılışa dönmek veriyi silmez.  */
function HataEkrani() {
  const hata = useRouteError();
  const metin = hata instanceof Error ? hata.message : String(hata ?? "");
  return (
    <div className="flex h-dvh items-center justify-center px-6">
      <div className="max-w-md text-center">
        <CircleAlert className="mx-auto size-6 text-red" />
        <p className="mt-3 text-[15px] font-semibold">Ekran beklenmedik bir hatayla durdu</p>
        <p className="mt-1 text-[13px] text-metin-2">
          Projeniz tarayıcıda kayıtlı, kaybolmadı.  Açılışa dönüp yeniden deneyin;  sürerse bu iletiyi bildirin.
        </p>
        {metin && <p className="mt-3 rounded-orta bg-yuzey-2 px-3 py-2 font-mono text-[11.5px] text-metin-3">{metin}</p>}
        <a href={import.meta.env.BASE_URL} className="mt-4 inline-block text-[13px] font-medium text-vurgu hover:underline">
          Açılışa dön
        </a>
      </div>
    </div>
  );
}

export const yonlendirici = createBrowserRouter(
  [
    {
      errorElement: <HataEkrani />,
      children: [
        { path: "/", element: <Acilis /> },
        { path: "/uygulama/yeni", element: <YeniUygulama /> },
        { path: "/uygulama/ornek", element: <YeniUygulama ornek /> },
        { path: "/uygulama/:id", element: <Bekle><UygulamaRota /></Bekle> },
        { path: "/avan", element: <Navigate to="/avan/trafik" replace /> },
        { path: "/avan/:adim", element: <Bekle><AvanCalisma /></Bekle> },
        { path: "/ofis-standardi", element: <Bekle><OfisStandardi /></Bekle> },
        { path: "/tablolar", element: <Bekle><Tablolar /></Bekle> },
        ...(EkranDizini ? [{ path: "/ekranlar", element: <Bekle><EkranDizini /></Bekle> }] : []),
        { path: "*", element: <Navigate to="/" replace /> },
      ],
    },
  ],
  { basename: import.meta.env.BASE_URL.replace(/\/$/, "") },
);
