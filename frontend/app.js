// SimulInvest geçici arayüzü: backend API'sini (docs/openapi.yaml) doğrudan kullanır.
const API = window.SIMULINVEST_API || "http://localhost:8000";
const TOKEN_KEY = "simulinvest-token";
const EMAIL_KEY = "simulinvest-email";
const TYPE_LABELS = { STOCK: "Hisse", CRYPTO: "Kripto", GOLD: "Altın" };

const $ = (sel) => document.querySelector(sel);
const tl = new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" });
const qtyFmt = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 8 });
const dateFmt = new Intl.DateTimeFormat("tr-TR", { dateStyle: "short", timeStyle: "short" });

const state = { assets: [], filter: "", authMode: "login", portfolio: null };

// ---------- yardımcılar ----------
function storage(action, key, value) {
  try {
    if (action === "get") return localStorage.getItem(key);
    if (action === "set") localStorage.setItem(key, value);
    if (action === "remove") localStorage.removeItem(key);
  } catch {
    return null;
  }
}

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = storage("get", TOKEN_KEY);
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(API + path, { method, headers, body: body && JSON.stringify(body) });
  } catch {
    throw new Error(`Sunucuya ulaşılamadı (${API}). Backend çalışıyor mu?`);
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (res.status === 401 && auth) {
    logout();
    throw new Error("Oturum süresi doldu, tekrar giriş yap.");
  }
  if (!res.ok) throw new Error(data?.message || `Hata: ${res.status}`);
  return data;
}

function pnlClass(value) {
  return value > 0 ? "up" : value < 0 ? "down" : "";
}

function signed(value) {
  return (value > 0 ? "+" : "") + tl.format(value);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ---------- giriş / kayıt ----------
function setAuthMode(mode) {
  state.authMode = mode;
  document.querySelectorAll("#auth-view .tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.mode === mode)
  );
  $("#name-field").hidden = mode !== "register";
  $("#auth-submit").textContent = mode === "register" ? "Kayıt ol" : "Giriş yap";
  $("#auth-form [name=password]").autocomplete =
    mode === "register" ? "new-password" : "current-password";
  $("#auth-error").hidden = true;
}

async function handleAuth(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const body = { email: form.get("email"), password: form.get("password") };
  const isRegister = state.authMode === "register";
  if (isRegister && form.get("displayName")) body.displayName = form.get("displayName");

  const button = $("#auth-submit");
  button.disabled = true;
  try {
    const res = await api(`/api/auth/${isRegister ? "register" : "login"}`, {
      method: "POST",
      body,
      auth: false,
    });
    storage("set", TOKEN_KEY, res.token);
    storage("set", EMAIL_KEY, body.email);
    event.target.reset();
    showApp();
  } catch (err) {
    $("#auth-error").textContent = err.message;
    $("#auth-error").hidden = false;
  } finally {
    button.disabled = false;
  }
}

function logout() {
  storage("remove", TOKEN_KEY);
  storage("remove", EMAIL_KEY);
  $("#app-view").hidden = true;
  $("#auth-view").hidden = false;
}

// ---------- piyasa ----------
async function loadAssets() {
  try {
    state.assets = await api("/api/assets", { auth: false });
    renderMarket();
    renderSymbolOptions();
    const latest = state.assets.map((a) => new Date(a.updatedAt)).sort((a, b) => b - a)[0];
    $("#market-updated").textContent = latest ? `Son güncelleme: ${dateFmt.format(latest)}` : "";
  } catch (err) {
    $("#market-body").innerHTML = `<tr><td colspan="3" class="empty">${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderMarket() {
  const selected = $("#trade-symbol").value;
  const rows = state.assets
    .filter((a) => !state.filter || a.type === state.filter)
    .map(
      (a) => `<tr data-symbol="${a.symbol}" class="${a.symbol === selected ? "selected" : ""}">
        <td><span class="sym">${a.symbol}</span><span class="badge">${TYPE_LABELS[a.type]}</span></td>
        <td>${escapeHtml(a.name)}</td>
        <td class="num">${tl.format(a.price)}</td>
      </tr>`
    );
  $("#market-body").innerHTML = rows.join("") || `<tr><td colspan="3" class="empty">Varlık yok</td></tr>`;
}

function renderSymbolOptions() {
  const select = $("#trade-symbol");
  const current = select.value;
  select.innerHTML = state.assets
    .map((a) => `<option value="${a.symbol}">${a.symbol} · ${escapeHtml(a.name)}</option>`)
    .join("");
  if (current) select.value = current;
  updateEstimate();
}

// ---------- al / sat ----------
function selectedAsset() {
  return state.assets.find((a) => a.symbol === $("#trade-symbol").value);
}

function updateEstimate() {
  const asset = selectedAsset();
  const qty = Number($("#trade-qty").value);
  $("#trade-estimate").textContent = asset && qty > 0 ? tl.format(asset.price * qty) : "—";

  const owned = state.portfolio?.holdings.find((h) => h.symbol === asset?.symbol);
  const parts = [];
  if (asset?.type === "STOCK") parts.push("Hisse adedi tam sayı olmalı.");
  if (owned) parts.push(`Elinde ${qtyFmt.format(owned.quantity)} adet var.`);
  $("#trade-hint").textContent = parts.join(" ");
  $("#trade-qty").step = asset?.type === "STOCK" ? "1" : "any";
}

async function handleTrade(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const body = {
    symbol: form.get("symbol"),
    side: form.get("side"),
    quantity: Number(form.get("quantity")),
  };
  const msg = $("#trade-msg");
  const button = $("#trade-submit");
  button.disabled = true;
  try {
    const tx = await api("/api/trades", { method: "POST", body });
    const verb = tx.side === "BUY" ? "alındı" : "satıldı";
    msg.textContent = `${qtyFmt.format(tx.quantity)} ${tx.symbol} ${verb} · ${tl.format(tx.total)}`;
    msg.className = "msg ok";
    $("#trade-qty").value = "";
    await Promise.all([loadPortfolio(), loadHistory()]);
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "msg fail";
  } finally {
    msg.hidden = false;
    button.disabled = false;
    updateEstimate();
  }
}

// ---------- portföy ve geçmiş ----------
async function loadPortfolio() {
  const p = await api("/api/portfolio");
  state.portfolio = p;
  $("#stat-balance").textContent = tl.format(p.balance);
  $("#stat-total").textContent = tl.format(p.totalValue);
  const pnl = $("#stat-pnl");
  pnl.textContent = signed(p.totalProfitLoss);
  pnl.className = pnlClass(p.totalProfitLoss);

  $("#holdings-body").innerHTML =
    p.holdings
      .map(
        (h) => `<tr>
          <td><span class="sym">${h.symbol}</span><span class="badge">${TYPE_LABELS[h.type]}</span></td>
          <td class="num">${qtyFmt.format(h.quantity)}</td>
          <td class="num">${tl.format(h.averageCost)}</td>
          <td class="num">${tl.format(h.currentPrice)}</td>
          <td class="num ${pnlClass(h.profitLoss)}">${signed(h.profitLoss)}</td>
        </tr>`
      )
      .join("") || `<tr><td colspan="5" class="empty">Portföyün boş. Piyasadan bir varlık seçip alım yap.</td></tr>`;
  updateEstimate();
}

async function loadHistory() {
  const txs = await api("/api/transactions?limit=20");
  $("#history-body").innerHTML =
    txs
      .map(
        (t) => `<tr>
          <td>${dateFmt.format(new Date(t.createdAt))}</td>
          <td class="sym">${t.symbol}</td>
          <td class="${t.side === "BUY" ? "up" : "down"}">${t.side === "BUY" ? "Alış" : "Satış"}</td>
          <td class="num">${qtyFmt.format(t.quantity)}</td>
          <td class="num">${tl.format(t.price)}</td>
          <td class="num">${tl.format(t.total)}</td>
        </tr>`
      )
      .join("") || `<tr><td colspan="6" class="empty">Henüz işlem yok.</td></tr>`;
}

// ---------- başlatma ----------
async function showApp() {
  $("#auth-view").hidden = true;
  $("#app-view").hidden = false;
  $("#user-email").textContent = storage("get", EMAIL_KEY) || "";
  await loadAssets();
  try {
    await Promise.all([loadPortfolio(), loadHistory()]);
  } catch (err) {
    console.warn(err);
  }
}

document.querySelectorAll("#auth-view .tab").forEach((t) =>
  t.addEventListener("click", () => setAuthMode(t.dataset.mode))
);
$("#auth-form").addEventListener("submit", handleAuth);
$("#logout").addEventListener("click", logout);
$("#trade-form").addEventListener("submit", handleTrade);
$("#trade-symbol").addEventListener("change", () => {
  updateEstimate();
  renderMarket();
});
$("#trade-qty").addEventListener("input", updateEstimate);

$("#market-filter").addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  state.filter = tab.dataset.type;
  document.querySelectorAll("#market-filter .tab").forEach((t) => t.classList.toggle("active", t === tab));
  renderMarket();
});

$("#market-body").addEventListener("click", (e) => {
  const row = e.target.closest("tr[data-symbol]");
  if (!row) return;
  $("#trade-symbol").value = row.dataset.symbol;
  renderMarket();
  updateEstimate();
  $("#trade-qty").focus();
});

// Fiyatlar backend'de 60 sn önbellekte; 30 sn'de bir yenilemek yeterli.
setInterval(() => {
  if (!$("#app-view").hidden) {
    loadAssets();
    loadPortfolio().catch(() => {});
  }
}, 30000);

if (storage("get", TOKEN_KEY)) showApp();
else logout();
