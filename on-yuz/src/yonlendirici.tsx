import { lazy, Suspense, useEffect } from "react";
import { createBrowserRouter, Navigate, useLocation, useNavigate, useParams } from "react-router";
import { Loader2 } from "lucide-react";
import { Acilis } from "@/ekranlar/Acilis";
import { projeOku, yeniUygulama } from "@/lib/proje";

/*  ADRESLER  ( hepsi /yeni altında — FastAPI derlenmiş dosyaları orada sunar )
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
    git(`/uygulama/${yeniUygulama(ornek).id}`, { replace: true });
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

export const yonlendirici = createBrowserRouter(
  [
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
  { basename: import.meta.env.BASE_URL.replace(/\/$/, "") },
);
