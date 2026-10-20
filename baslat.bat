@echo off
chcp 65001 >nul
title Asansor Proje Programi ( hesap + cizim )
cd /d "%~dp0"

echo.
echo ==============================================================
echo    ASANSOR PROJE PROGRAMI  ( HESAP + CIZIM )
echo ==============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo   Python bulunamadi.
  echo   https://www.python.org/downloads/ adresinden Python 3 kurun
  echo   ^(kurulumda "Add Python to PATH" secenegini isaretleyin^)
  echo   ve bu dosyayi yeniden cift tiklayin.
  echo.
  pause & exit /b 1
)

rem  Python 3.12 ya da yenisi ( pyproject.toml ):  eski surumle program acilmiyordu
if not exist ".venv" (
  python -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
  if errorlevel 1 (
    echo   Python 3.12 ya da yenisi gerekli - kurulu olan daha eski.
    echo   https://www.python.org/downloads/ adresinden guncel surumu kurun
    echo   ve bu dosyayi yeniden cift tiklayin.
    echo.
    pause & exit /b 1
  )
  echo   Ilk kurulum yapiliyor ^(yalniz bir kez, ~1 dakika^)...
  python -m venv .venv || (echo   Sanal ortam olusturulamadi. & pause & exit /b 1)
  .venv\Scripts\python.exe -m pip install --upgrade pip -q
)

rem  ── GEREKENLER TAM MI ────────────────────────────────────────
rem  Program guncellendiginde yeni bir kitaplik eklenmis olabilir
rem  ( CAD ciktisi icin ezdxf + pdfminer.six gibi ).  Her acilista
rem  hizlica bakilir: eksik yoksa hicbir sey yapilmaz, bekletmez.
.venv\Scripts\python.exe -c "import importlib.util as u; assert all(u.find_spec(m) for m in ('fastapi','uvicorn','reportlab')); import ezdxf; from pdfminer.high_level import extract_pages" >nul 2>&1
if errorlevel 1 (
  echo   Eksik kitapliklar kuruluyor ^(~1 dakika^)...
  .venv\Scripts\python.exe -m pip install -r requirements.txt -q || (
     echo   Kurulum yapilamadi - internet baglantinizi kontrol edin.
     echo   Program yine de aciliyor: CAD ^(DWG/DXF^) ciktisi disindaki
     echo   butun hesaplar ve PDF'ler calisir.)
  echo.
)

rem  ── ON YUZ ─────────────────────────────────────────────────
rem  Ekran derlenmis dosyalardan sunulur ( on-yuz\dist ).  Program guncellenmisse
rem  bir kez derlenir;  guncelse beklemeden gecer ( araclar\on_yuz_derle.py ).
.venv\Scripts\python.exe -m araclar.on_yuz_derle

.venv\Scripts\python.exe hesap\main.py
echo.
pause
