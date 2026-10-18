/*  PROJE DOSYASINI AÇMA — açılışta ve proje bilgilerinde aynı yol.
    Dosya ( eski arayüzün .uygulama biçimi ) yeni bir proje olarak açılır;
    açık proje ezilmez.  Dosyadaki ofis standardı uygulanmaz ( yeni arayüzde
    ofis standardı bütün projelerde geçerlidir ) — farklıysa söylenir.
    Avan dosyası ( .avan ) avan ekranında açılır:  avan tek projedir, önceki
    hâli orada "Geri al" ile döner.                                          */
import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { api, type AlanSemasi } from "@/lib/api";
import { avanDosyasiMi, avanDosyasiniAc, avanOfisiniOku, avanProjesiniOku, avanProjesiniYaz } from "@/lib/avan";
import { dosyaOku } from "@/lib/dosya";
import { yeniUygulama, type Ham } from "@/lib/proje";

export function useDosyaAc(sema: AlanSemasi | undefined, ofis: Ham) {
  const girdiRef = useRef<HTMLInputElement>(null);
  const git = useNavigate();
  const istemci = useQueryClient();
  const [hata, setHata] = useState("");

  const avanAc = async (metin: string, ad: string) => {
    let sec;
    try {
      sec = await istemci.fetchQuery({ queryKey: ["secenekler"], queryFn: api.secenekler });
    } catch {
      return setHata("Sunucuya ulaşılamadı — avan dosyası seçenekler olmadan okunamaz.");
    }
    const o = avanDosyasiniAc(metin, ad, sec, avanOfisiniOku());
    if (typeof o === "string") return setHata(o);
    setHata("");
    const onceki = avanProjesiniOku();
    avanProjesiniYaz(o.proje);
    git("/avan/trafik", { state: { acilis: { ...o, onceki } } });
  };

  const ac = async (f: File | undefined) => {
    if (!f) return;
    if (!sema) return setHata("Sunucuya ulaşılamadı — form şeması olmadan dosya okunamaz.");
    if (f.size > 2 * 1024 * 1024) return setHata("Dosya çok büyük — bir proje dosyası değil.");
    const metin = await f.text();
    let d: unknown = null;
    try {
      d = JSON.parse(metin);
    } catch {
      /*  dosyaOku söyler  */
    }
    if (avanDosyasiMi(d)) return avanAc(metin, f.name);
    const o = dosyaOku(metin, sema, ofis);
    if (!o.tamam) return setHata(o.hata);
    setHata("");
    const p = yeniUygulama(false, o.icerik);
    const satirlar = [`"${f.name}" açıldı.`];
    if (o.ofisFarki.length)
      satirlar.push(
        `Dosyadaki ofis standardı bu tarayıcınınkinden ${o.ofisFarki.length} değerde farklı — hesap bu tarayıcınınkiyle yapılıyor ( Ofis standardı ).`,
      );
    if (o.taninmayan.length)
      satirlar.push(`Bu sürümde olmayan ${o.taninmayan.length} seçim varsayılana döndü:  ${o.taninmayan.join(" · ")}`);
    git(`/uygulama/${p.id}`, { state: { bildirim: satirlar.join("\n") } });
  };

  return {
    hata,
    ac,
    sec: () => girdiRef.current?.click(),
    girdi: (
      <input
        ref={girdiRef}
        type="file"
        accept=".uygulama,.avan,.json"
        className="hidden"
        onChange={(e) => {
          void ac(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    ),
  };
}
