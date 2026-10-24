/*  TARAYICI DEPOSU — proje, avan ve ofis standardı tarayıcıda ( localStorage ) durur;
    ön yüzde depoya yalnız bu dosya dokunur ( depo.test denetler ).
    YAZILAMAZSA ( site verisi engelli, depo dolu ) değer BU SEKMENİN belleğinde
    tutulur:  ekran çalışmayı sürdürür, her ekran uyarır ( Kabuk DepoUyarisi ) —
    sayfa kapanınca gider, kullanıcı dosyaya kaydeder.  24 Eki:  yazma sessizce
    düşüyordu;  yeni ve örnek proje kaydedilemeyip açılışa "bu tarayıcıda yok" diye
    geri atılıyor, dolu depoda değişiklikler sessizce kayboluyordu.
    Yer açılınca ( proje silinince ) sıradaki yazma bellektekileri de depoya yazar,
    uyarı kalkar.                                                              */
import { useSyncExternalStore } from "react";

const bellek = new Map<string, string>();
const dinleyenler = new Set<() => void>();
/**  undefined:  henüz denenmedi ( ilk soruda küçük bir değer yazılıp silinir )  */
let yazilamiyor: boolean | undefined;

function degisti(y: boolean) {
  if (yazilamiyor === y) return;
  yazilamiyor = y;
  dinleyenler.forEach((f) => f());
}

/**  Bellekte bekleyenleri depoya yazar;  hepsi yazıldıysa depo yine çalışıyor  */
function bosalt() {
  for (const [a, d] of bellek) {
    try {
      localStorage.setItem(a, d);
      bellek.delete(a);
    } catch {
      return;
    }
  }
  degisti(false);
}

export function depoOku(anahtar: string): string | null {
  const b = bellek.get(anahtar);
  if (b !== undefined) return b;
  try {
    return localStorage.getItem(anahtar);
  } catch {
    return null;
  }
}

export function depoYaz(anahtar: string, deger: string) {
  try {
    localStorage.setItem(anahtar, deger);
  } catch {
    bellek.set(anahtar, deger);
    degisti(true);
    return;
  }
  bellek.delete(anahtar);
  bosalt();
}

export function depoSil(anahtar: string) {
  const vardi = bellek.delete(anahtar);
  try {
    localStorage.removeItem(anahtar);
  } catch {
    return;
  }
  //  Yer açıldı:  bekleyenler yazılabilir
  if (vardi || bellek.size) bosalt();
}

/**  `anahtar` başka sekmede değişince ( storage olayı ) f yeni metinle ya da silindiyse
     null'la çağrılır;  bellekteki kopya düşer ( depodaki en yenisidir ).  Bırakan döner.  */
export function depoDinle(anahtar: string, f: (metin: string | null) => void) {
  const dinle = (e: StorageEvent) => {
    if (e.key !== anahtar || e.storageArea !== localStorage) return;
    bellek.delete(anahtar);
    f(e.newValue);
  };
  window.addEventListener("storage", dinle);
  return () => window.removeEventListener("storage", dinle);
}

/**  Depo yazılamıyor mu ( değerler yalnız bu sekmenin belleğinde )  */
export function depoYazilamiyor(): boolean {
  if (yazilamiyor === undefined) {
    try {
      localStorage.setItem("asansor:deneme", "1");
      localStorage.removeItem("asansor:deneme");
      yazilamiyor = false;
    } catch {
      yazilamiyor = true;
    }
  }
  return yazilamiyor;
}

export function useDepoYazilamiyor(): boolean {
  return useSyncExternalStore((f) => {
    dinleyenler.add(f);
    return () => {
      dinleyenler.delete(f);
    };
  }, depoYazilamiyor);
}
