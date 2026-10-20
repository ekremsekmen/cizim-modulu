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

#  PYTHON 3.12 YA DA YENİSİ ( pyproject.toml ):  macOS'un kendi python3'ü 3.9'dur
#  ve program onunla hiç açılmıyordu ( 20 Eki ).  İlk uygun sürüm seçilir.
uygun() { "$1" -c 'import sys; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1; }
PY=""
for c in python3.14 python3.13 python3.12 python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if command -v "$c" >/dev/null 2>&1 && uygun "$c"; then PY="$c"; break; fi
done
#  Eski bir Python'la kurulmuş sanal ortam, uygun Python varsa yeniden kurulur
if [ -d ".venv" ] && [ -n "$PY" ] && ! uygun ./.venv/bin/python; then
  echo "  Sanal ortam eski bir Python sürümüyle kurulmuş — yeniden kuruluyor…"
  rm -rf .venv
fi

if [ ! -d ".venv" ]; then
  if [ -z "$PY" ]; then
    echo "  Python 3.12 ya da yenisi bulunamadı."
    echo "  https://www.python.org/downloads/ adresinden Python'un güncel"
    echo "  sürümünü kurup bu dosyayı yeniden çift tıklayın."
    echo ""; read -r -p "  Kapatmak için Enter..."; exit 1
  fi
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
