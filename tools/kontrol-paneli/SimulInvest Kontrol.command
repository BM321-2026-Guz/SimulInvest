#!/bin/bash
# macOS: SimulInvest Kontrol Paneli'ni açar (Finder'da çift tıkla).
cd "$(dirname "$0")" || exit 1

if command -v python3.13 >/dev/null 2>&1; then
  PY=python3.13
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "Python 3 bulunamadı. python.org'dan kur veya: brew install python@3.13"
  read -r -p "Kapatmak için Enter'a bas..."
  exit 1
fi

if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
  echo "Bu Python'da tkinter yok. Homebrew kullanıyorsan: brew install python-tk@3.13"
  read -r -p "Kapatmak için Enter'a bas..."
  exit 1
fi

nohup "$PY" "SimulInvest Kontrol.pyw" >/dev/null 2>&1 &
exit 0
