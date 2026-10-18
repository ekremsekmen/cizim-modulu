import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router";
import { IpucuSaglayici } from "@/components/ui";
import { yonlendirici } from "./yonlendirici";
import "./styles.css";

//  Sunucu verisi TanStack Query'de:  eski yanıt yenisini ezemez ( yarış yok ),
//  yeni hesap gelene kadar önceki sonuç ekranda kalır.
const istemci = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1, staleTime: Infinity } },
});

createRoot(document.getElementById("kok")!).render(
  <QueryClientProvider client={istemci}>
    <IpucuSaglayici>
      <RouterProvider router={yonlendirici} />
    </IpucuSaglayici>
  </QueryClientProvider>,
);
