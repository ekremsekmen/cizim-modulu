#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ASANSÖR PROJE PROGRAMI ( HESAP + ÇİZİM )  —  macOS başlatıcı
#  Çift tıklayarak çalıştırın.  Hesap programı hesap/ klasöründe,
#  çizim modülü cizim/ klasöründe;  ikisi aynı sanal ortamı kullanır.
# ═══════════════════════════════════════════════════════════════
cd "$(dirname "$0")" || exit 1

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "   ASANSÖR PROJE PROGRAMI  ( HESAP + ÇİZİM )"
echo "══════════════════════════════════════════════════════════════"
echo ""

PY=""
for c in python3 python3.12 python3.11 python3.10 /usr/bin/python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "  Python bulunamadı."
  echo "  https://www.python.org/downloads/ adresinden Python 3 kurup"
  echo "  bu dosyayı yeniden çift tıklayın."
  echo ""; read -r -p "  Kapatmak için Enter..."; exit 1
fi

if [ ! -d ".venv" ]; then
  echo "  İlk kurulum yapılıyor (yalnız bir kez, ~1 dakika)…"
  "$PY" -m venv .venv || { echo "  Sanal ortam oluşturulamadı."; read -r -p "  Enter..."; exit 1; }
  ./.venv/bin/python -m pip install --upgrade pip -q
fi

#  ── GEREKENLER TAM MI ──────────────────────────────────────────
#  Program güncellendiğinde yeni bir kitaplık eklenmiş olabilir
#  ( CAD çıktısı için ezdxf + pdfminer.six gibi ).  Her açılışta
#  hızlıca bakılır: eksik yoksa hiçbir şey yapılmaz, bekletmez.
if ! ./.venv/bin/python -c "import importlib.util as u; assert all(u.find_spec(m) for m in ('fastapi','uvicorn','reportlab')); import ezdxf; from pdfminer.high_level import extract_pages" >/dev/null 2>&1; then
  echo "  Eksik kitaplıklar kuruluyor (~1 dakika)…"
  if ./.venv/bin/python -m pip install -r requirements.txt -q; then
    echo "  Kurulum tamamlandı."
  else
    echo "  Kurulum yapılamadı — internet bağlantınızı kontrol edin."
    echo "  Program yine de açılıyor: CAD ( DWG/DXF ) çıktısı dışındaki"
    echo "  bütün hesaplar ve PDF'ler çalışır."
  fi
  echo ""
fi

#  ── ÖN YÜZ ─────────────────────────────────────────────────────
#  Ekran derlenmiş dosyalardan sunulur ( on-yuz/dist ).  Program güncellenmişse
#  bir kez derlenir;  güncelse beklemeden geçer ( araclar/on_yuz_derle.py ).
./.venv/bin/python -m araclar.on_yuz_derle

./.venv/bin/python hesap/main.py
echo ""
read -r -p "  Program kapandı. Pencereyi kapatmak için Enter..."
