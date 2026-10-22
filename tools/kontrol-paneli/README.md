# SimulInvest Kontrol Paneli

SimulInvest'i (backend + arayüz) tek pencereden başlatıp durdurmak için küçük bir masaüstü uygulaması.
**Windows** ve **macOS**'ta çalışır; hangi sistemde olduğunu kendisi anlar ve ona göre komut kullanır.
Ek paket gerekmez, sadece Python'un kendi kütüphanelerini (tkinter dahil) kullanır.

Bu araç günlük geliştirme içindir. Final teslimde proje Docker (`docker-compose up`) ile çalıştırılacak.

## Kullanım

| Sistem  | Açmak için |
|---------|------------|
| Windows | `SimulInvest Kontrol.bat` dosyasına çift tıkla |
| macOS   | `SimulInvest Kontrol.command` dosyasına çift tıkla |

Panel repo içinde olduğu için repo klasörünü **kendisi bulur**, bir şey seçmen gerekmez.
**Başlat**'a basınca sırasıyla:

1. `backend/.venv` yoksa Python ortamını kurar (ilk sefer 1-2 dk)
2. `pip install -r backend/requirements.txt` (paketler kuruluysa birkaç saniye)
3. `backend/.env` yoksa `.env.example`'dan oluşturur ve rastgele bir `JWT_SECRET` üretir
4. Backend'i (`uvicorn`, port 8000) ve arayüzü (`http.server`, port 5500) başlatır
5. Backend hazır olunca tarayıcıda arayüzü açar

macOS'ta repo zip olarak indirildiyse ilk açılışta Gatekeeper uyarı verebilir:
dosyaya sağ tıkla → **Aç**. Çalıştırma izni yoksa: `chmod +x "SimulInvest Kontrol.command"`.

## Özellikler

- **Durum:** Backend (`/health`) ve arayüz için canlı gösterge: port, PID, çalışma süresi.
- **Log:** Sunucu çıktıları canlı akar; kaynağa göre filtre, hata satırları kırmızı. Ayrıca
  `simulinvest_kontrol.log` dosyasına yazılır.
- **Durdur:** Panelin açtığı sunucuları kapatır. Portları (8000 / 5500) panel dışından açılmış
  bir SimulInvest sunucusu tutuyorsa onu da kapatır. Portu **başka bir program** kullanıyorsa
  (örneğin başka bir projenin sunucusu) sormadan kapatmaz, önce onay ister.
- **Ayarlar:** Klasörler, Python yolu ve portlar "Yollar" bölümünden değiştirilebilir.
  `simulinvest_kontrol_ayarlar.json` dosyasına kaydedilir; kişiye özel olduğu için git'e girmez.

## Arayüz klasörü

Arayüz, reponun `frontend/` klasöründen sunulur; ek bir şey yapmaya gerek yoktur. Repoda
`frontend/` olduğu sürece "Arayüz (UI) klasörü" ayarı devre dışı görünür.

Bu ayar sadece arayüzü başka bir klasörden çalıştırmak isteyenler içindir (örneğin henüz
birleşmemiş bir arayüz dalını ayrı bir klasörde denemek). Repoda `frontend/` yoksa panel bu
ayardaki klasörü kullanır.

## Gereksinimler

- Python 3.13, tkinter ile birlikte
  - **Windows:** python.org kurulumu (`py` başlatıcısı ve tkinter varsayılan olarak gelir)
  - **macOS:** python.org kurulumu, ya da Homebrew: `brew install python@3.13 python-tk@3.13`

## Sisteme göre farklar

| İş | Windows | macOS |
|----|---------|-------|
| venv Python'u | `.venv\Scripts\python.exe` | `.venv/bin/python` |
| venv kurulumu | `py -3.13` | `python3.13` / `python3` |
| Portu tutan süreç | `netstat -ano` (dilden bağımsız okunur) | `lsof -iTCP:<port> -sTCP:LISTEN` |
| Sürecin komut satırı | `Get-CimInstance Win32_Process` | `ps -o command=` |
| Süreci kapatma | `taskkill /T /F` | alt süreçlerle birlikte `SIGTERM`, gerekirse `SIGKILL` |
| Dosya açma | `os.startfile` | `open` |
