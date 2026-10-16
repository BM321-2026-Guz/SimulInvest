"""SimulInvest Kontrol Paneli

"SimulInvest Baslat.bat" ve "SimulInvest Durdur.bat" dosyalarının yaptığı işi
tek pencerede toplar: klasör seçimi, başlat/durdur, anlık durum ve canlı log.
Windows ve macOS'ta çalışır; işletim sistemine özel komutlar aşağıdaki
"platform" bölümünde ayrılmıştır.
"""

import json
import os
import queue
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "simulinvest_kontrol_ayarlar.json"
LOG_FILE = APP_DIR / "simulinvest_kontrol.log"

DEFAULTS = {
    "repo": "",  # boşsa tahmin edilir (bkz. guess_folder)
    "ui_repo": "",
    "python": "",  # boşsa <repo>/backend/.venv içindeki python (bkz. venv_python)
    "backend_port": 8000,
    "frontend_port": 5500,
    "open_browser": True,
}


# ---------- platform: Windows / macOS farkları ----------
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
PLATFORM_NAME = "Windows" if IS_WIN else "macOS" if IS_MAC else sys.platform

if IS_WIN:
    # Sunucular için siyah konsol penceresi açılmasın.
    POPEN_KW = {"creationflags": subprocess.CREATE_NO_WINDOW}
else:
    # Her sunucu kendi süreç grubunda başlasın; durdururken alt süreçleriyle birlikte kapanır.
    POPEN_KW = {"start_new_session": True}

FONT_UI = ("Segoe UI", 10, "bold") if IS_WIN else ("Helvetica Neue", 13, "bold") if IS_MAC else ("TkDefaultFont", 10, "bold")
FONT_MONO = ("Consolas", 9) if IS_WIN else ("Menlo", 11) if IS_MAC else ("Monospace", 9)


def venv_python(backend):
    if IS_WIN:
        return backend / ".venv" / "Scripts" / "python.exe"
    return backend / ".venv" / "bin" / "python"


def python_launcher():
    """venv kurmak için kullanılacak Python 3.13 komutu."""
    if IS_WIN:
        py = shutil.which("py")
        return [py, "-3.13"] if py else [sys.executable]
    for name in ("python3.13", "python3"):
        if shutil.which(name):
            return [shutil.which(name)]
    return [sys.executable]


def parse_netstat_listeners(output, port):
    """`netstat -ano` çıktısından portu dinleyen PID'leri çıkarır.

    Durum sütununa ("LISTENING") bakılmaz: Windows'un bazı dil paketleri onu çeviriyor
    (Almanca "ABHÖREN" gibi). Dinleyen soketin karşı adresi her dilde 0.0.0.0:0 veya [::]:0'dır.
    """
    pids = set()
    for line in output.splitlines():
        parts = line.split()
        if (len(parts) >= 5 and parts[0].upper() == "TCP"
                and parts[1].endswith(f":{port}") and parts[2] in ("0.0.0.0:0", "[::]:0")
                and parts[-1].isdigit() and parts[-1] != "0"):
            pids.add(int(parts[-1]))
    return pids


def pids_listening_on(port):
    """Verilen portu dinleyen süreçlerin PID'lerini bulur."""
    try:
        if IS_WIN:
            out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True,
                                 errors="replace", timeout=10, **POPEN_KW).stdout
            return parse_netstat_listeners(out, port)
        out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                             capture_output=True, text=True, timeout=10).stdout
        return {int(p) for p in out.split() if p.isdigit()}
    except Exception:
        return set()


def process_command_line(pid):
    """Sürecin komut satırı; bulunamazsa boş metin."""
    try:
        if IS_WIN:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"],
                capture_output=True, text=True, errors="replace", timeout=15, **POPEN_KW).stdout
        else:
            out = subprocess.run(["ps", "-o", "command=", "-p", str(int(pid))],
                                 capture_output=True, text=True, timeout=10).stdout
        return out.strip()
    except Exception:
        return ""


def is_simulinvest_process(command_line):
    """Komut satırı bu panelin (veya .bat başlatıcısının) açtığı sunuculardan birine mi ait?"""
    cmd = command_line.replace("\\", "/").lower()
    return ("uvicorn" in cmd and "app.main:app" in cmd) or "http.server" in cmd


def _descendants(pid):
    """macOS/Linux: bir sürecin tüm alt süreçleri (pgrep -P ile)."""
    found, todo = [], [pid]
    while todo:
        out = subprocess.run(["pgrep", "-P", str(todo.pop())], capture_output=True, text=True).stdout
        kids = [int(p) for p in out.split() if p.isdigit()]
        found += kids
        todo += kids
    return found


def kill_tree(pid):
    """Süreci alt süreçleriyle birlikte kapatır."""
    if IS_WIN:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, **POPEN_KW)
        return
    targets = [pid] + _descendants(pid)
    for p in targets:
        try:
            os.kill(p, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + 3
    while time.time() < deadline:
        alive = [p for p in targets if _alive(p)]
        if not alive:
            return
        time.sleep(0.2)
    for p in targets:
        try:
            os.kill(p, signal.SIGKILL)
        except OSError:
            pass


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def open_file(path):
    if IS_WIN:
        os.startfile(path)
    else:
        subprocess.Popen(["open" if IS_MAC else "xdg-open", str(path)])


def python_missing_hint():
    if IS_WIN:
        return ("Python 3.13 bulunamadı. python.org'dan kur, kurulumda "
                "\"Add python.exe to PATH\" kutusunu işaretle.")
    return "Python 3.13 bulunamadı. python.org'dan kur veya: brew install python@3.13"


def find_repo_root(start=APP_DIR):
    """Panel SimulInvest reposunun içindeyse (tools/kontrol-paneli) repo kökünü bulur.

    `.git` worktree'lerde klasör değil dosyadır; ikisi de kabul edilir.
    """
    for folder in (start, *start.parents):
        if (folder / ".git").exists() and (folder / "docs" / "openapi.yaml").exists():
            return folder
    return None


REPO_ROOT = find_repo_root()


def guess_folder(name):
    """Klasörü repo kökünün yanında, panelin yanında veya Belgeler\\GitHub altında arar."""
    bases = [APP_DIR.parent, Path.home() / "Documents" / "GitHub"]
    if REPO_ROOT:
        bases.insert(0, REPO_ROOT.parent)
    for base in bases:
        if (base / name).is_dir():
            return str(base / name)
    return ""


def repo_has_frontend(repo):
    return bool(repo) and (Path(repo) / "frontend" / "index.html").exists()


def load_config():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    if not cfg["repo"]:
        cfg["repo"] = str(REPO_ROOT) if REPO_ROOT else guess_folder("SimulInvest")
    # Arayüz develop'a birleşene kadar ayrı bir klasörde (worktree) duruyor; sonra gerekmez.
    if not cfg["ui_repo"] and not repo_has_frontend(cfg["repo"]):
        cfg["ui_repo"] = guess_folder("SimulInvest-ui")
    return cfg


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def http_ok(url, timeout=1.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def port_open(port, timeout=0.5):
    """HTTP isteği atmadan portun dinlenip dinlenmediğine bakar (arayüz log'u kirlenmesin)."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


class Service:
    """Uygulamanın kendi başlattığı bir sunucu süreci (çıktısı log'a akar)."""

    def __init__(self, name, log):
        self.name = name
        self.log = log
        self.proc = None
        self.started_at = None

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, args, cwd):
        env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        self.proc = subprocess.Popen(
            args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **POPEN_KW,
        )
        self.started_at = time.time()
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()

    def _pump(self, proc):
        for raw in iter(proc.stdout.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip()
            # Panelin 2 saniyede bir yaptığı sağlık kontrolü log'u doldurmasın.
            if line and '"GET /health HTTP' not in line:
                self.log(line, self.name)
        code = proc.wait()
        self.log(f"Süreç kapandı (çıkış kodu {code}).", self.name)

    def stop(self):
        if self.running:
            kill_tree(self.proc.pid)
        self.proc = None
        self.started_at = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SimulInvest Kontrol Paneli")
        self.geometry("980x700")
        self.minsize(760, 520)

        self.cfg = load_config()
        self.log_queue = queue.Queue()
        self.busy = False
        self.backend = Service("backend", self.log)
        self.frontend = Service("arayüz", self.log)
        self.status = {"backend": False, "frontend": False}

        self._build_ui()
        self.after(100, self._drain_log)
        threading.Thread(target=self._status_loop, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.log(f"Kontrol paneli açıldı ({PLATFORM_NAME}).")
        if not self.cfg["repo"]:
            self.log("SimulInvest repo klasörü bulunamadı; 'Yollar' bölümünden seç.")

    # ---------- arayüz ----------
    def _build_ui(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Big.TButton", padding=(14, 6))

        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # Klasör / dosya yolları
        paths = ttk.LabelFrame(root, text="Yollar", padding=8)
        paths.pack(fill="x")
        paths.columnconfigure(1, weight=1)
        self.vars = {}
        self.path_widgets = {}
        rows = [
            ("repo", "SimulInvest repo klasörü", "dir"),
            ("ui_repo", "Arayüz (UI) repo klasörü", "dir"),
            ("python", "Python (.venv) — boş = otomatik", "file"),
        ]
        for i, (key, label, kind) in enumerate(rows):
            lbl = ttk.Label(paths, text=label)
            lbl.grid(row=i, column=0, sticky="w", padx=(0, 8), pady=2)
            var = tk.StringVar(value=self.cfg.get(key, ""))
            self.vars[key] = var
            entry = ttk.Entry(paths, textvariable=var)
            entry.grid(row=i, column=1, sticky="ew", pady=2)
            btn = ttk.Button(paths, text="Seç…", command=lambda k=key, t=kind: self._browse(k, t))
            btn.grid(row=i, column=2, padx=(6, 0), pady=2)
            self.path_widgets[key] = (lbl, entry, btn)
        self.vars["repo"].trace_add("write", lambda *_: self._update_ui_repo_row())
        self._update_ui_repo_row()

        opts = ttk.Frame(paths)
        opts.grid(row=len(rows), column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Label(opts, text="Backend portu").pack(side="left")
        self.vars["backend_port"] = tk.StringVar(value=str(self.cfg["backend_port"]))
        ttk.Entry(opts, width=7, textvariable=self.vars["backend_port"]).pack(side="left", padx=(4, 14))
        ttk.Label(opts, text="Arayüz portu").pack(side="left")
        self.vars["frontend_port"] = tk.StringVar(value=str(self.cfg["frontend_port"]))
        ttk.Entry(opts, width=7, textvariable=self.vars["frontend_port"]).pack(side="left", padx=(4, 14))
        self.open_browser_var = tk.BooleanVar(value=self.cfg.get("open_browser", True))
        ttk.Checkbutton(opts, text="Hazır olunca tarayıcıyı aç", variable=self.open_browser_var).pack(side="left")
        ttk.Button(opts, text="Ayarları kaydet", command=self._save).pack(side="left", padx=(14, 0))

        # Durum + düğmeler
        mid = ttk.Frame(root)
        mid.pack(fill="x", pady=10)

        status = ttk.LabelFrame(mid, text="Durum", padding=8)
        status.pack(side="left", fill="x", expand=True)
        self.status_widgets = {}
        for i, (key, label) in enumerate([("backend", "Backend"), ("frontend", "Arayüz")]):
            dot = tk.Canvas(status, width=16, height=16, highlightthickness=0)
            dot.grid(row=i, column=0, padx=(0, 6), pady=3)
            oval = dot.create_oval(2, 2, 14, 14, fill="#9e9e9e", outline="")
            ttk.Label(status, text=label, width=9, font=FONT_UI).grid(row=i, column=1, sticky="w")
            text = ttk.Label(status, text="kontrol ediliyor…")
            text.grid(row=i, column=2, sticky="w")
            self.status_widgets[key] = (dot, oval, text)
        self.step_label = ttk.Label(status, text="Hazır.", foreground="#555")
        self.step_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        buttons = ttk.Frame(mid)
        buttons.pack(side="left", padx=(10, 0), fill="y")
        self.start_btn = ttk.Button(buttons, text="▶  Başlat", style="Big.TButton", command=self.start_all)
        self.start_btn.grid(row=0, column=0, sticky="ew", pady=2)
        self.stop_btn = ttk.Button(buttons, text="■  Durdur", style="Big.TButton", command=self.stop_all)
        self.stop_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=2)
        ttk.Button(buttons, text="Arayüzü aç", command=self._open_ui).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(buttons, text="Swagger (API)", command=self._open_docs).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=2)

        # Log
        logf = ttk.LabelFrame(root, text="Log", padding=6)
        logf.pack(fill="both", expand=True)
        bar = ttk.Frame(logf)
        bar.pack(fill="x", pady=(0, 4))
        self.autoscroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="Otomatik kaydır", variable=self.autoscroll).pack(side="left")
        ttk.Label(bar, text="Filtre:").pack(side="left", padx=(14, 4))
        self.filter_var = tk.StringVar(value="Tümü")
        ttk.Combobox(bar, textvariable=self.filter_var, state="readonly", width=10,
                     values=["Tümü", "panel", "backend", "arayüz"]).pack(side="left")
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Button(bar, text="Temizle", command=self._clear_log).pack(side="right")
        ttk.Button(bar, text="Log dosyasını aç", command=self._open_log_file).pack(side="right", padx=(0, 6))

        self.log_text = ScrolledText(logf, wrap="none", font=FONT_MONO,
                                     background="#1e1e1e", foreground="#d4d4d4",
                                     insertbackground="#d4d4d4", state="disabled")
        self.log_text.pack(fill="both", expand=True)
        for tag, color in [("panel", "#4fc1ff"), ("backend", "#b5cea8"), ("arayüz", "#ce9178"),
                           ("error", "#f48771"), ("time", "#808080")]:
            self.log_text.tag_configure(tag, foreground=color)
        self.all_lines = []  # (zaman, kaynak, metin) — filtre için

    def _update_ui_repo_row(self):
        """Arayüz repo içinde varsa (develop'a birleşmişse) ayrı UI klasörü ayarı gerekmez."""
        lbl, entry, btn = self.path_widgets["ui_repo"]
        if repo_has_frontend(self.vars["repo"].get().strip()):
            lbl.configure(text="Arayüz (UI) klasörü — gerekmiyor")
            entry.configure(state="disabled")
            btn.configure(state="disabled")
        else:
            lbl.configure(text="Arayüz (UI) repo klasörü")
            entry.configure(state="normal")
            btn.configure(state="normal")

    def _browse(self, key, kind):
        current = self.vars[key].get()
        if kind == "dir":
            path = filedialog.askdirectory(initialdir=current or None, title="Klasör seç")
        else:
            # macOS'ta python dosyasının uzantısı yok; filtre konmaz.
            types = [("Python", "python.exe"), ("Tümü", "*.*")] if IS_WIN else []
            path = filedialog.askopenfilename(
                initialdir=str(Path(current).parent) if current else None,
                title="Python seç", filetypes=types)
        if path:
            self.vars[key].set(str(Path(path)))
            self._save(quiet=True)

    def _save(self, quiet=False):
        try:
            self.cfg.update(
                repo=self.vars["repo"].get().strip(),
                ui_repo=self.vars["ui_repo"].get().strip(),
                python=self.vars["python"].get().strip(),
                backend_port=int(self.vars["backend_port"].get()),
                frontend_port=int(self.vars["frontend_port"].get()),
                open_browser=self.open_browser_var.get(),
            )
        except ValueError:
            messagebox.showerror("Hata", "Port numaraları sayı olmalı.")
            return False
        save_config(self.cfg)
        if not quiet:
            self.log("Ayarlar kaydedildi.")
        return True

    # ---------- log ----------
    def log(self, text, source="panel"):
        """Herhangi bir thread'den güvenle çağrılabilir."""
        self.log_queue.put((datetime.now().strftime("%H:%M:%S"), source, text))

    def _drain_log(self):
        new = []
        try:
            while True:
                new.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        if new:
            self.all_lines.extend(new)
            if len(self.all_lines) > 5000:
                self.all_lines = self.all_lines[-4000:]
                self._apply_filter()
            else:
                self._write_lines(new)
            try:
                with LOG_FILE.open("a", encoding="utf-8") as f:
                    for t, s, m in new:
                        f.write(f"{t} [{s}] {m}\n")
            except OSError:
                pass
        self.after(100, self._drain_log)

    def _write_lines(self, lines):
        flt = self.filter_var.get()
        self.log_text.configure(state="normal")
        for t, src, msg in lines:
            if flt != "Tümü" and src != flt:
                continue
            is_err = bool(re.search(r"\b(error|hata|traceback|exception)\b", msg, re.I))
            self.log_text.insert("end", f"{t} ", "time")
            self.log_text.insert("end", f"[{src}] ", src)
            self.log_text.insert("end", msg + "\n", "error" if is_err else ())
        self.log_text.configure(state="disabled")
        if self.autoscroll.get():
            self.log_text.see("end")

    def _apply_filter(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._write_lines(self.all_lines)

    def _clear_log(self):
        self.all_lines.clear()
        self._apply_filter()

    def _open_log_file(self):
        if LOG_FILE.exists():
            open_file(LOG_FILE)

    # ---------- durum ----------
    def _status_loop(self):
        while True:
            bp, fp = self.cfg["backend_port"], self.cfg["frontend_port"]
            b = http_ok(f"http://127.0.0.1:{bp}/health")
            f = port_open(fp)
            try:
                self.after(0, self._show_status, b, f)
            except RuntimeError:  # pencere kapandı
                return
            time.sleep(2)

    def _show_status(self, b_ok, f_ok):
        for key, ok, svc, port in [("backend", b_ok, self.backend, self.cfg["backend_port"]),
                                   ("frontend", f_ok, self.frontend, self.cfg["frontend_port"])]:
            dot, oval, label = self.status_widgets[key]
            if ok:
                color = "#2e7d32"
                if svc.running:
                    up = int(time.time() - svc.started_at)
                    text = f"Çalışıyor — port {port}, PID {svc.proc.pid}, {up // 60} dk {up % 60} sn"
                else:
                    text = f"Çalışıyor — port {port} (panel dışından başlatılmış)"
            elif svc.running:
                color, text = "#f9a825", f"Açılıyor… (PID {svc.proc.pid})"
            else:
                color, text = "#c62828", "Kapalı"
            dot.itemconfigure(oval, fill=color)
            label.configure(text=text)
            if self.status[key] != ok:
                self.status[key] = ok
                self.log(f"{'Backend' if key == 'backend' else 'Arayüz'} "
                         f"{'çalışıyor' if ok else 'kapalı'}.")
        self.start_btn.configure(state="disabled" if self.busy else "normal")
        self.stop_btn.configure(state="disabled" if self.busy else "normal")

    def _step(self, text):
        self.after(0, lambda: self.step_label.configure(text=text))
        self.log(text)

    # ---------- başlat ----------
    def _paths(self):
        repo = Path(self.cfg["repo"])
        backend = repo / "backend"
        py = Path(self.cfg["python"]) if self.cfg["python"] else venv_python(backend)
        frontend = Path(self.cfg["ui_repo"]) / "frontend"
        if (repo / "frontend" / "index.html").exists():
            frontend = repo / "frontend"
        return backend, py, frontend

    def start_all(self):
        if self.busy or not self._save(quiet=True):
            return
        self.busy = True
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self._start_worker, daemon=True).start()

    def _run_logged(self, args, cwd=None):
        """Bir komutu çalıştırır, çıktısını log'a yazar, çıkış kodunu döner."""
        env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        p = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **POPEN_KW)
        for raw in iter(p.stdout.readline, b""):
            line = raw.decode("utf-8", errors="replace").rstrip()
            if line:
                self.log(line)
        return p.wait()

    def _start_worker(self):
        try:
            self._start_steps()
        except Exception as e:
            self._fail(f"Beklenmeyen hata: {e}")
        finally:
            self.busy = False

    def _fail(self, msg):
        self._step(f"[HATA] {msg}")
        self.after(0, lambda: messagebox.showerror("SimulInvest", msg))

    def _start_steps(self):
        if not self.cfg["repo"]:
            return self._fail("SimulInvest repo klasörü seçilmedi. 'Yollar' bölümünden seç.")
        backend, py, frontend = self._paths()
        bp, fp = self.cfg["backend_port"], self.cfg["frontend_port"]
        self._step("SimulInvest başlatılıyor…")

        if not (backend / "app" / "main.py").exists():
            return self._fail(f"Backend bulunamadı: {backend}\nRepo klasörünü kontrol et "
                              "veya GitHub Desktop'ta backend olan bir dal seç.")
        if not (frontend / "index.html").exists():
            return self._fail(f"Arayüz bulunamadı: {frontend}\nUI repo klasörünü kontrol et. "
                              "Gerekirse: git worktree add ../SimulInvest-ui feature/eren-demo-ui")

        # 1) Python ortamı
        if not py.exists():
            self._step("[1/4] Python ortamı kuruluyor, ilk sefer 1-2 dakika sürebilir…")
            cmd = python_launcher()
            self.log("Kullanılan Python: " + " ".join(cmd))
            if self._run_logged(cmd + ["-m", "venv", str(backend / ".venv")]) != 0 or not py.exists():
                return self._fail("Python ortamı kurulamadı. " + python_missing_hint())

        self._step("[1/4] Paketler kontrol ediliyor…")
        code = self._run_logged([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
                                 "-r", str(backend / "requirements.txt")])
        if code != 0:
            return self._fail("Paketler kurulamadı. İnternet bağlantını kontrol et.")

        # 2) .env
        env_file = backend / ".env"
        if not env_file.exists():
            self._step("[2/4] .env dosyası oluşturuluyor…")
            text = (backend / ".env.example").read_text(encoding="utf-8")
            text = re.sub(r"(?m)^JWT_SECRET=[ \t]*$", "JWT_SECRET=" + secrets.token_hex(32), text, count=1)
            env_file.write_text(text, encoding="utf-8")
        else:
            self._step("[2/4] .env mevcut.")

        # 3) Sunucular
        if http_ok(f"http://127.0.0.1:{bp}/health"):
            self._step("[3/4] Backend zaten çalışıyor.")
        elif not self.backend.running:
            self._step(f"[3/4] Backend başlatılıyor: http://127.0.0.1:{bp}")
            self.backend.start([str(py), "-m", "uvicorn", "app.main:app", "--reload",
                                "--port", str(bp)], cwd=backend)

        if port_open(fp):
            self._step("      Arayüz zaten çalışıyor.")
        elif not self.frontend.running:
            self._step(f"      Arayüz başlatılıyor: http://127.0.0.1:{fp}")
            self.frontend.start([str(py), "-m", "http.server", str(fp), "--bind", "127.0.0.1"],
                                cwd=frontend)

        # 4) Backend hazır olana kadar bekle
        self._step("[4/4] Backend'in hazır olması bekleniyor…")
        for _ in range(60):
            if http_ok(f"http://127.0.0.1:{bp}/health"):
                break
            if not self.backend.running and not http_ok(f"http://127.0.0.1:{bp}/health"):
                return self._fail("Backend açılırken kapandı. Log'daki hata mesajına bak.\n"
                                  "Sık sebep: .env içindeki JWT_SECRET boş veya 32 karakterden kısa.")
            time.sleep(1)
        else:
            return self._fail("Backend 60 saniyede açılmadı. Log'a bak.\n"
                              "Sık sebep: .env içindeki JWT_SECRET boş veya 32 karakterden kısa.")

        self._step(f"Hazır! Arayüz: http://127.0.0.1:{fp}  ·  Swagger: http://127.0.0.1:{bp}/docs")
        if self.cfg.get("open_browser"):
            webbrowser.open(f"http://127.0.0.1:{fp}")

    # ---------- durdur ----------
    def stop_all(self):
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=self._stop_worker, daemon=True).start()

    def _stop_worker(self):
        try:
            self._stop_steps()
        finally:
            self.busy = False

    def _stop_steps(self):
        self._step("SimulInvest kapatılıyor…")
        self.backend.stop()
        self.frontend.stop()
        # Panel dışından (ör. .bat ile) açılmış SimulInvest sunucuları için portları da temizle.
        # Portu başka bir program kullanıyorsa (başka bir proje gibi) sormadan kapatılmaz.
        for port in (self.cfg["backend_port"], self.cfg["frontend_port"]):
            pids = pids_listening_on(port)
            if not pids:
                self.log(f"Port {port} zaten kapalı.")
                continue
            for pid in pids:
                cmd = process_command_line(pid)
                if is_simulinvest_process(cmd):
                    kill_tree(pid)
                    self.log(f"Port {port} kapatıldı (PID {pid}).")
                elif self._ask(f"Port {port} SimulInvest olmayan bir program tarafından kullanılıyor:\n\n"
                               f"PID {pid}: {cmd or 'komut satırı okunamadı'}\n\n"
                               "Bu program kapatılsın mı?"):
                    kill_tree(pid)
                    self.log(f"Port {port}: başka program kapatıldı (PID {pid}).")
                else:
                    self.log(f"Port {port}: başka bir program kullanıyor (PID {pid}), dokunulmadı.")
        if IS_WIN:
            # Eski .bat başlatıcısının açtığı konsol pencereleri.
            for title in ("SimulInvest Backend*", "SimulInvest Arayuz*"):
                subprocess.run(["taskkill", "/FI", f"WINDOWTITLE eq {title}", "/T", "/F"],
                               capture_output=True, **POPEN_KW)
        self._step("Durduruldu.")

    def _ask(self, question):
        """Evet/hayır sorusu; arka plan thread'inden çağrılırsa ana thread'de sorup cevabı bekler."""
        if threading.current_thread() is threading.main_thread():
            return messagebox.askyesno("SimulInvest", question, icon="warning")
        answer, done = [False], threading.Event()

        def ask():
            answer[0] = messagebox.askyesno("SimulInvest", question, icon="warning")
            done.set()

        self.after(0, ask)
        done.wait()
        return answer[0]

    # ---------- diğer ----------
    def _open_ui(self):
        webbrowser.open(f"http://127.0.0.1:{self.cfg['frontend_port']}")

    def _open_docs(self):
        webbrowser.open(f"http://127.0.0.1:{self.cfg['backend_port']}/docs")

    def _on_close(self):
        if self.backend.running or self.frontend.running:
            # Sunucuların çıktısı bu pencereye bağlı; panel kapanırsa onlar da durmalı.
            if not messagebox.askokcancel(
                    "SimulInvest", "Sunucular çalışıyor. Panel kapanınca sunucular da durdurulacak.\n\n"
                    "Devam edilsin mi?"):
                return
            self._stop_steps()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
