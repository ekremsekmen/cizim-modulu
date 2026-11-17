/*  AÇIK AVAN DEĞİŞMEDEN ÖNCE SORULUR ( 17 Kas — kullanıcı:  "avan projede yaptığımda programı
    kapattığımda gidiyor" ).  Avan bu tarayıcıda TEK projedir ( lib/avan );  yenisi ya da açılan
    dosya öncekinin yerine geçer.  Eskiden açılıştaki "Avan proje" kartı, avan ekranındaki "Yeni"
    ve "Aç", açılışa bırakılan .avan dosyası açık avanın üzerine SORMADAN yazıyordu — yalnız kısa
    ömürlü bir "Geri al" kalıyordu.  Avan boşsa sorulmaz:  kaybedilecek bir şey yoktur.  */
import { useState } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { Dugme, Pencere } from "@/components/ui";
import { api } from "@/lib/api";
import { avanDosyayaKaydet, avanOfisiniOku, avanOzeti, avanProjesiniOku } from "@/lib/avan";

/**  Avan ekranının dışında ( açılış ) açık avanı dosyaya indirir:  seçenekler sunucudan;  trafik
     sonucu yoktur ( kartların kapasite / hızı dosyaya trafikten yazılmaz — avanDosyayaKaydet ).  */
export async function acikAvaniKaydet(istemci: QueryClient) {
  const sec = await istemci.fetchQuery({ queryKey: ["secenekler"], queryFn: api.secenekler });
  avanDosyayaKaydet(avanProjesiniOku(), sec, avanOfisiniOku(), null);
}

/**  sor( devam , yerine ):  açık avan doluysa önce sorar, boşsa hemen devam eder;  yerine geçecek
     proje ( açılan dosya ) açık avanla birebir aynıysa da sormaz — kaybedilecek bir şey yok.  pencere:  sayfaya
     konacak soru.  kaydet:  açık avanı dosyaya indirir ( .avan ).  */
export function useAvanDegisimi(kaydet: () => void | Promise<void>) {
  const [devam, setDevam] = useState<null | { f: () => void; ad: string }>(null);
  const sor = (f: () => void, yerine?: unknown) => {
    const o = avanOzeti();
    if (!o || (yerine !== undefined && JSON.stringify(yerine) === JSON.stringify(avanProjesiniOku()))) return f();
    setDevam({ f, ad: o.ad });
  };
  const bitir = () => {
    const f = devam?.f;
    setDevam(null);
    f?.();
  };
  const pencere = (
    <Pencere
      acik={devam !== null}
      degisti={(a) => !a && setDevam(null)}
      baslik="Açık avan projesi kapanacak"
      aciklama={
        <>
          “{devam?.ad}” bu tarayıcıdaki tek avan projesi.  Yenisi onun yerine geçer;  saklamak için önce dosyaya
          kaydedin.
        </>
      }
    >
      <Dugme
        tur="birincil"
        onClick={async () => {
          await kaydet();
          bitir();
        }}
      >
        Dosyaya kaydet ve devam et
      </Dugme>
      <Dugme onClick={bitir}>Kaydetmeden devam et</Dugme>
      <Dugme tur="hayalet" onClick={() => setDevam(null)}>
        Vazgeç
      </Dugme>
    </Pencere>
  );
  return { sor, pencere };
}
