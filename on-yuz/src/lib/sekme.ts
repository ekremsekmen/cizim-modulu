/*  SEKMELER ARASI EŞİTLEME
    Proje, avan ve ofis standardı tarayıcıda ( localStorage ) durur;  aynı
    proje iki sekmede açıkken son yazan öbürünü sessizce eziyordu.  Bir sekme
    yazınca öbürlerine "storage" olayı gelir ( yazan sekmeye gelmez ):  ekran
    o değeri alır, iki sekme aynı hâli gösterir.

    Döngü olmaz:  alınan değer aynen geri yazılır;  aynı değer yazılınca
    tarayıcı olay üretmez.                                                  */
import { useEffect } from "react";

/**  `anahtar` başka sekmede değişince `al` çağrılır:  yeni değer ya da silindiyse null.
     `al` kararlı olmalı ( useState ayarlayıcısı ya da useCallback ).  */
export function useSekmeEsitle<T>(anahtar: string, al: (deger: T | null) => void) {
  useEffect(() => {
    const dinle = (e: StorageEvent) => {
      if (e.key !== anahtar || e.storageArea !== localStorage) return;
      try {
        al(e.newValue === null ? null : (JSON.parse(e.newValue) as T));
      } catch {
        /*  okunamayan değer:  bu sekmeninki kalır  */
      }
    };
    window.addEventListener("storage", dinle);
    return () => window.removeEventListener("storage", dinle);
  }, [anahtar, al]);
}
