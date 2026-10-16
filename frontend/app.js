// SimulInvest geçici arayüzü: backend API'sini (docs/openapi.yaml) doğrudan kullanır.
const API = window.SIMULINVEST_API || "http://localhost:8000";
const TOKEN_KEY = "simulinvest-token";
const EMAIL_KEY = "simulinvest-email";
// Varlık grupları: piyasa, portföy ve al-sat listesi bu sırayla ayrılır.
const GROUPS = [
  { type: "STOCK", title: "BIST Hisseleri", short: "Hisse" },
  { type: "CRYPTO", title: "Kripto Paralar", short: "Kripto" },
  { type: "GOLD", title: "Altın", short: "Altın" },
];
const TYPE_LABELS = Object.fromEntries(GROUPS.map((g) => [g.type, g.short]));

const $ = (sel) => document.querySelector(sel);
const tl = new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" });
const qtyFmt = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 8 });
const dateFmt = new Intl.DateTimeFormat("tr-TR", { dateStyle: "short", timeStyle: "short" });
const timeFmt = new Intl.DateTimeFormat("tr-TR", { timeStyle: "medium" }); // saniyeli

const state = { assets: [], authMode: "login", portfolio: null };

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

function dot(type) {
  return `<span class="dot dot-${type.toLowerCase()}" aria-hidden="true"></span>`;
}

function typeOf(symbol) {
  return state.assets.find((a) => a.symbol === symbol)?.type;
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
    $("#market-updated").textContent = latest ? `Son güncelleme: ${timeFmt.format(latest)}` : "";
  } catch (err) {
    $("#market-groups").innerHTML = `<div class="card empty">${escapeHtml(err.message)}</div>`;
  }
}

function renderMarket() {
  const selected = $("#trade-symbol").value;
  $("#market-groups").innerHTML = GROUPS.map((g) => {
    const assets = state.assets.filter((a) => a.type === g.type);
    if (!assets.length) return "";
    const rows = assets
      .map(
        (a) => `<tr data-symbol="${a.symbol}" class="${a.symbol === selected ? "selected" : ""}">
          <td><span class="sym">${a.symbol}</span></td>
          <td>${escapeHtml(a.name)}</td>
          <td class="num">${tl.format(a.price)}${
            a.isFallback
              ? ' <span class="badge demo" title="Canlı fiyat alınamadı, demo fiyat gösteriliyor">demo</span>'
              : ""
          }</td>
        </tr>`
      )
      .join("");
    return `<div class="card market-group">
      <div class="card-head"><h2>${dot(g.type)}${g.title}</h2><span class="muted">${assets.length} varlık</span></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Sembol</th><th>Ad</th><th class="num">Fiyat</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
  }).join("");
}

function renderSymbolOptions() {
  const select = $("#trade-symbol");
  const current = select.value;
  select.innerHTML = GROUPS.map((g) => {
    const options = state.assets
      .filter((a) => a.type === g.type)
      .map((a) => `<option value="${a.symbol}">${a.symbol} · ${escapeHtml(a.name)}</option>`)
      .join("");
    return options ? `<optgroup label="${g.title}">${options}</optgroup>` : "";
  }).join("");
  if (current) select.value = current;
  updateEstimate();
}

// ---------- al / sat ----------
function selectedAsset() {
  return state.assets.find((a) => a.symbol === $("#trade-symbol").value);
}

function selectedSide() {
  return document.querySelector("#trade-form [name=side]:checked").value;
}

// Nakitle alınabilecek en fazla miktar: hissede tam adet, kripto/altında 8 ondalık (aşağı yuvarlanır).
function maxBuyable(asset, balance) {
  if (!asset || !(asset.price > 0) || !(balance > 0)) return 0;
  const step = asset.type === "STOCK" ? 1 : 1e-8;
  let qty = Math.floor(balance / asset.price / step) * step;
  // Kayan nokta hatası tutarı bakiyenin üstüne çıkarmasın.
  while (qty > 0 && qty * asset.price > balance) qty -= step;
  return Number(qty.toFixed(asset.type === "STOCK" ? 0 : 8));
}

function maxQuantity(asset) {
  if (!asset || !state.portfolio) return 0;
  if (selectedSide() === "SELL") {
    return state.portfolio.holdings.find((h) => h.symbol === asset.symbol)?.quantity || 0;
  }
  return maxBuyable(asset, state.portfolio.balance);
}

function updateEstimate() {
  const asset = selectedAsset();
  const qty = Number($("#trade-qty").value);
  $("#trade-estimate").textContent = asset && qty > 0 ? tl.format(asset.price * qty) : "—";

  const max = maxQuantity(asset);
  const info = $("#trade-max-info");
  if (!asset || !state.portfolio) {
    info.textContent = "";
  } else if (selectedSide() === "SELL") {
    info.innerHTML = max
      ? `Satabileceğin en fazla: <strong>${qtyFmt.format(max)}</strong> adet`
      : "Bu varlıktan elinde yok.";
  } else {
    info.innerHTML = max
      ? `Nakdinle en fazla <strong>${qtyFmt.format(max)}</strong> adet alabilirsin
         <span class="muted">(${tl.format(max * asset.price)})</span>`
      : "Bu varlıktan 1 adet almaya bile nakdin yetmiyor.";
  }
  info.classList.toggle("over", qty > max);
  $("#trade-max").disabled = !max;

  $("#trade-hint").textContent = asset?.type === "STOCK" ? "Hisse adedi tam sayı olmalı." : "";
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

  const invested = p.holdings.reduce((sum, h) => sum + h.quantity * h.currentPrice, 0);
  const groups = GROUPS.map((g) => {
    const items = p.holdings.filter((h) => h.type === g.type);
    const value = items.reduce((sum, h) => sum + h.quantity * h.currentPrice, 0);
    const pnl = items.reduce((sum, h) => sum + h.profitLoss, 0);
    return { ...g, items, value, pnl };
  }).filter((g) => g.items.length);

  // Varlık türüne göre dağılım (nakit hariç).
  $("#allocation").innerHTML = groups
    .map(
      (g) => `<span class="chip">${dot(g.type)}${g.short}
        <strong>%${Math.round((g.value / invested) * 100)}</strong></span>`
    )
    .join("");

  $("#holdings-body").innerHTML =
    groups
      .map(
        (g) => `<tr class="group">
            <td colspan="4">${dot(g.type)}${g.title}</td>
            <td class="num">${tl.format(g.value)}</td>
            <td class="num ${pnlClass(g.pnl)}">${signed(g.pnl)}</td>
          </tr>` +
          g.items
            .map(
              (h) => `<tr>
                <td><span class="sym">${h.symbol}</span></td>
                <td class="num">${qtyFmt.format(h.quantity)}</td>
                <td class="num">${tl.format(h.averageCost)}</td>
                <td class="num">${tl.format(h.currentPrice)}</td>
                <td class="num">${tl.format(h.quantity * h.currentPrice)}</td>
                <td class="num ${pnlClass(h.profitLoss)}">${signed(h.profitLoss)}</td>
              </tr>`
            )
            .join("")
      )
      .join("") || `<tr><td colspan="6" class="empty">Portföyün boş. Piyasadan bir varlık seçip alım yap.</td></tr>`;
  updateEstimate();
}

async function loadHistory() {
  const txs = await api("/api/transactions?limit=20");
  $("#history-body").innerHTML =
    txs
      .map(
        (t) => `<tr>
          <td>${dateFmt.format(new Date(t.createdAt))}</td>
          <td><span class="sym">${t.symbol}</span>${
            typeOf(t.symbol) ? `<span class="badge">${TYPE_LABELS[typeOf(t.symbol)]}</span>` : ""
          }</td>
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
document
  .querySelectorAll("#trade-form [name=side]")
  .forEach((r) => r.addEventListener("change", updateEstimate));
$("#trade-max").addEventListener("click", () => {
  const max = maxQuantity(selectedAsset());
  if (!max) return;
  $("#trade-qty").value = max;
  updateEstimate();
  $("#trade-qty").focus();
});

$("#market-groups").addEventListener("click", (e) => {
  const row = e.target.closest("tr[data-symbol]");
  if (!row) return;
  $("#trade-symbol").value = row.dataset.symbol;
  renderMarket();
  updateEstimate();
  $("#trade-qty").focus();
});

// Backend fiyatları arka planda 10 sn'de bir yeniliyor; 5 sn'de bir sormak en fazla ~15 sn gecikme
// demek. Sekme görünmezken sorulmaz, geri dönülünce hemen yenilenir.
const REFRESH_MS = 5000;

function refreshPrices() {
  if ($("#app-view").hidden || document.hidden) return;
  loadAssets();
  loadPortfolio().catch(() => {});
}

setInterval(refreshPrices, REFRESH_MS);
document.addEventListener("visibilitychange", refreshPrices);

if (storage("get", TOKEN_KEY)) showApp();
else logout();
