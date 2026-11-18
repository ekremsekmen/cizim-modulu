/*  AÇIK AVAN DEĞİŞMEDEN ÖNCE SORULUR ( 17 Kas — kullanıcı:  "avan projede yaptığımda programı
    kapattığımda gidiyor" ).  Avan bu tarayıcıda TEK projedir ( lib/avan );  yenisi ya da açılan
    dosya öncekinin yerine geçer.  Eskiden açılıştaki "Avan proje" kartı, avan ekranındaki "Yeni"
    ve "Aç", açılışa bırakılan .avan dosyası açık avanın üzerine SORMADAN yazıyordu — yalnız kısa
    ömürlü bir "Geri al" kalıyordu.  Avan boşsa sorulmaz:  kaybedilecek bir şey yoktur.  */
import { useRef, useState } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
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
  const [devam, setDevam] = useState<null | { ad: string }>(null);
  //  DEVAM TEK SEFERLİK ( 18 Kas — yayın öncesi denetim ):  "Dosyaya kaydet ve devam et" açılışta
  //  seçenekleri sunucudan beklerken ikinci basış ikinci dosyayı indiriyor, devam iki kez koşuyordu —
  //  ikinci "yeni avan" boş projeyi "Geri al"ın önceki projesi sayıp kaydı siliyordu.  Bekleyen devam
  //  burada durur, ilk kullanan alır;  Vazgeç ( ya da pencerenin kapanması ) onu düşürür:  kayıt
  //  sonradan biterse devam etmez.
  const bekleyen = useRef<(() => void) | null>(null);
  const suruyor = useRef(false);
  const [kaydediliyor, setKaydediliyor] = useState(false);
  //  Kayıt yapılamadı ( sunucuya ulaşılamadı ):  eskiden pencere sessizce açık kalıyordu
  const [hata, setHata] = useState("");
  const sor = (f: () => void, yerine?: unknown) => {
    const o = avanOzeti();
    if (!o || (yerine !== undefined && JSON.stringify(yerine) === JSON.stringify(avanProjesiniOku()))) return f();
    bekleyen.current = f;
    setHata("");
    setDevam({ ad: o.ad });
  };
  const vazgec = () => {
    bekleyen.current = null;
    setDevam(null);
  };
  const bitir = () => {
    const f = bekleyen.current;
    vazgec();
    f?.();
  };
  const kaydetVeBitir = async () => {
    if (suruyor.current) return;
    suruyor.current = true;
    setKaydediliyor(true);
    setHata("");
    try {
      await kaydet();
      bitir();
    } catch (e) {
      setHata(e instanceof TypeError ? "Sunucuya ulaşılamadı" : e instanceof Error ? e.message : String(e));
    } finally {
      suruyor.current = false;
      setKaydediliyor(false);
    }
  };
  const pencere = (
    <Pencere
      acik={devam !== null}
      degisti={(a) => !a && vazgec()}
      baslik="Açık avan projesi kapanacak"
      aciklama={
        <>
          “{devam?.ad}” bu tarayıcıdaki tek avan projesi.  Yenisi onun yerine geçer;  saklamak için önce dosyaya
          kaydedin.
        </>
      }
    >
      {hata && (
        <p role="alert" className="text-[12.5px] text-red">
          Dosyaya kaydedilemedi ( {hata} ) — yeniden deneyin ya da kaydetmeden devam edin.
        </p>
      )}
      <Dugme tur="birincil" onClick={() => void kaydetVeBitir()} disabled={kaydediliyor}>
        {kaydediliyor && <Loader2 className="animate-spin" />} Dosyaya kaydet ve devam et
      </Dugme>
      <Dugme onClick={bitir}>Kaydetmeden devam et</Dugme>
      <Dugme tur="hayalet" onClick={vazgec}>
        Vazgeç
      </Dugme>
    </Pencere>
  );
  return { sor, pencere };
}
