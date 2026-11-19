/*  KÂĞIT ENİ ( 19 Kas, kullanıcı:  "projeyi indirirken 60 cm ya da 90 cm olarak seçebilmeliyim" ):
    paketin paftası hangi rulo enine dizilsin.  Çizicinin rulosunun ENİ paftanın yüksekliğidir;
    şerit rulo boyunca uzar ( sunucu:  cizim/pafta.KAGIT_ENLERI ).  İsteğe mm gider ( kagit:  600 |
    900 );  seçim bu tarayıcıda hatırlanır ( ofisin çizicisi ) — avan ve uygulama paketi aynısını okur.  */
import { useState } from "react";
import { depoOku, depoYaz } from "./depo";

export type KagitEni = 600 | 900;

export const KAGIT_ENLERI: { deger: `${KagitEni}`; cm: number }[] = [
  { deger: "600", cm: 60 },
  { deger: "900", cm: 90 },
];

const ANAHTAR = "asansor:kagit_eni";

/**  Hatırlanan kâğıt eni;  yoksa ( ya da depoda tanınmayan değer varsa ) ofisin şablonununki:  60 cm  */
export function kagitOku(): KagitEni {
  return depoOku(ANAHTAR) === "900" ? 900 : 600;
}

export function kagitYaz(k: KagitEni) {
  depoYaz(ANAHTAR, String(k));
}

/**  [ kâğıt eni , değiştir ] — değişen seçim hatırlanır  */
export function useKagitEni(): [KagitEni, (k: KagitEni) => void] {
  const [k, setK] = useState<KagitEni>(kagitOku);
  return [
    k,
    (y) => {
      setK(y);
      kagitYaz(y);
    },
  ];
}
