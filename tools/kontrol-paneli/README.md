# SimulInvest Kontrol Paneli

SimulInvest'i (backend + arayüz) tek pencereden başlatıp durdurmak için küçük bir masaüstü uygulaması.
**Windows** ve **macOS**'ta çalışır; hangi sistemde olduğunu kendisi anlar ve ona göre komut kullanır.
`SimulInvest Baslat.bat` / `SimulInvest Durdur.bat` dosyalarının yerine geçer.

## Özellikler

- **Yollar:** SimulInvest repo klasörü, ayrı UI repo klasörü ve Python "Seç…" düğmeleriyle seçilir; portlar değiştirilebilir.
- **Durum:** Backend (`/health`) ve arayüz için canlı gösterge — port, PID, çalışma süresi.
- **Başlat:** venv kurulumu → `pip install -r requirements.txt` → `.env` (rastgele `JWT_SECRET` ile) → uvicorn + `http.server` → backend hazır olunca tarayıcıyı açar.
- **Durdur:** Panelin açtığı sunucuları ve portları (8000 / 5500) tutan diğer süreçleri kapatır.
- **Log:** Sunucu çıktıları canlı akar; kaynağa göre filtre, hata satırları kırmızı. Ayrıca `simulinvest_kontrol.log` dosyasına yazılır.

## Gereksinimler

- Python 3.13, tkinter ile birlikte
  - **Windows:** python.org kurulumu (`py` başlatıcısı ve tkinter varsayılan olarak gelir)
  - **macOS:** python.org kurulumu, ya da Homebrew: `brew install python@3.13 python-tk@3.13`

## Kullanım

| Sistem  | Açmak için |
|---------|------------|
| Windows | `SimulInvest Kontrol.bat` dosyasına çift tıkla |
| macOS   | `SimulInvest Kontrol.command` dosyasına çift tıkla |

macOS'ta repo zip olarak indirildiyse ilk açılışta Gatekeeper uyarı verebilir:
dosyaya sağ tıkla → **Aç**. Çalıştırma izni yoksa: `chmod +x "SimulInvest Kontrol.command"`.

İlk açılışta repo klasörleri şu yerlerde aranır:

1. Bu klasörün yanında (`../SimulInvest`, `../SimulInvest-ui`)
2. `~/Documents/GitHub/SimulInvest`, `~/Documents/GitHub/SimulInvest-ui`

Bulunamazsa "Yollar" bölümünden seç. Ayarlar `simulinvest_kontrol_ayarlar.json` dosyasına kaydedilir (git'e girmez).

Arayüz SimulInvest reposunun `frontend` klasöründe varsa ayrı UI reposuna gerek yoktur; panel bunu kendisi algılar.

## Sisteme göre farklar

| İş | Windows | macOS |
|----|---------|-------|
| venv Python'u | `.venv\Scripts\python.exe` | `.venv/bin/python` |
| venv kurulumu | `py -3.13` | `python3.13` / `python3` |
| Portu tutan süreç | `netstat -ano` | `lsof -iTCP:<port> -sTCP:LISTEN` |
| Süreci kapatma | `taskkill /T /F` | alt süreçlerle birlikte `SIGTERM`, gerekirse `SIGKILL` |
| Dosya açma | `os.startfile` | `open` |
