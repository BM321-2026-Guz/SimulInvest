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
const pct = new Intl.NumberFormat("tr-TR", {
  style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
});
const compact = new Intl.NumberFormat("tr-TR", { notation: "compact", maximumFractionDigits: 2 });

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
    if (detail.symbol) renderDetailHead(); // pano açıksa güncel fiyat orada da yenilensin
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
          <td class="num">${tl.format(a.price)}</td>
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
              (h) => `<tr data-symbol="${h.symbol}" class="clickable">
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

// Piyasada veya portföyde bir varlığa tıklanınca ayrıntı panosu açılır.
for (const id of ["#market-groups", "#holdings-body"]) {
  $(id).addEventListener("click", (e) => {
    const row = e.target.closest("tr[data-symbol]");
    if (row) openDetail(row.dataset.symbol);
  });
}

function selectForTrade(symbol) {
  $("#trade-symbol").value = symbol;
  renderMarket();
  updateEstimate();
  $("#trade-qty").focus();
}

// ---------- varlık ayrıntı panosu (issue #49) ----------
const detail = { symbol: null, range: "1mo", history: null, request: 0, opener: null };
const shortDate = new Intl.DateTimeFormat("tr-TR", { day: "numeric", month: "short" });
const shortTime = new Intl.DateTimeFormat("tr-TR", {
  day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
});

// Aynı gruptaki (hisse / kripto / altın) önceki ve sonraki varlık; uçlarda başa sarar.
function neighbours(symbol) {
  const asset = state.assets.find((a) => a.symbol === symbol);
  const list = state.assets.filter((a) => a.type === asset?.type);
  const i = list.findIndex((a) => a.symbol === symbol);
  return { prev: list[(i - 1 + list.length) % list.length], next: list[(i + 1) % list.length] };
}

function openDetail(symbol) {
  if (!state.assets.some((a) => a.symbol === symbol)) return;
  if ($("#detail").hidden) detail.opener = document.activeElement;
  detail.symbol = symbol;
  detail.history = null;
  $("#detail").hidden = false;
  document.body.classList.add("no-scroll");
  renderDetailHead();
  loadPriceHistory();
  $("#detail-close").focus();
}

function closeDetail() {
  $("#detail").hidden = true;
  document.body.classList.remove("no-scroll");
  detail.symbol = null;
  detail.opener?.focus?.();
}

function renderDetailHead() {
  const a = state.assets.find((x) => x.symbol === detail.symbol);
  if (!a) return;
  $("#detail-dot").innerHTML = dot(a.type);
  $("#detail-symbol").textContent = a.symbol;
  $("#detail-type").textContent = TYPE_LABELS[a.type];
  $("#detail-name").textContent = a.name;
  $("#detail-price").textContent = tl.format(a.price);

  const prev = detail.history?.previousClose;
  const change = $("#detail-change");
  if (prev) {
    const diff = a.price - prev;
    change.textContent = `${diff >= 0 ? "+" : ""}${pct.format(diff / prev)} (${signed(diff)})`;
    change.className = pnlClass(diff);
  } else {
    change.textContent = "";
  }

  // Grupta tek varlık varsa (altın) gezinecek başka varlık yok; çubuklar gizlenir.
  const { prev: p, next: n } = neighbours(a.symbol);
  const alone = p.symbol === a.symbol;
  $("#detail-prev").hidden = alone;
  $("#detail-next").hidden = alone;
  $("#detail-prev-label").textContent = `${p.symbol} · ${p.name}`;
  $("#detail-next-label").textContent = `${n.symbol} · ${n.name}`;
}

async function loadPriceHistory() {
  const symbol = detail.symbol;
  const range = detail.range;
  const request = ++detail.request; // hızlı geçişte eski cevap yenisinin üstüne yazmasın
  for (const id of ["#stat-open", "#stat-prev", "#stat-low", "#stat-high"]) $(id).textContent = "—";
  $("#chart-box").innerHTML = '<p class="muted chart-msg">Grafik yükleniyor…</p>';
  try {
    const h = await api(`/api/assets/${encodeURIComponent(symbol)}/history?range=${range}`, {
      auth: false,
    });
    if (request !== detail.request) return;
    detail.history = h;
    $("#stat-open").textContent = h.open == null ? "—" : tl.format(h.open);
    $("#stat-prev").textContent = h.previousClose == null ? "—" : tl.format(h.previousClose);
    $("#stat-low").textContent = h.dayLow == null ? "—" : tl.format(h.dayLow);
    $("#stat-high").textContent = h.dayHigh == null ? "—" : tl.format(h.dayHigh);
    renderChart(h.points, range);
    renderDetailHead();
  } catch (err) {
    if (request !== detail.request) return;
    $("#chart-box").innerHTML = `<p class="muted chart-msg">${escapeHtml(err.message)}</p>`;
  }
}

// Bağımlılıksız SVG çizgi grafik: alan dolgusu, min/max ekseni, üzerine gelince fiyat.
function renderChart(points, range) {
  const box = $("#chart-box");
  if (points.length < 2) {
    box.innerHTML = '<p class="muted chart-msg">Bu aralık için yeterli veri yok.</p>';
    return;
  }
  const W = 600, H = 240, L = 8, R = 72, T = 12, B = 26;
  const prices = points.map((p) => p.price);
  const min = Math.min(...prices), max = Math.max(...prices);
  const span = max - min || max * 0.01 || 1;
  const x = (i) => L + (i / (points.length - 1)) * (W - L - R);
  const y = (v) => T + (1 - (v - min) / span) * (H - T - B);
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.price).toFixed(1)}`).join("");
  const area = `${line}L${x(points.length - 1).toFixed(1)},${H - B}L${x(0).toFixed(1)},${H - B}Z`;
  const tone = prices.at(-1) >= prices[0] ? "up" : "down";
  const fmtX = range === "5d" ? shortTime : shortDate;
  const ticks = [min, (min + max) / 2, max];

  box.innerHTML = `
    <svg class="chart ${tone}" viewBox="0 0 ${W} ${H}" role="img"
         aria-label="${escapeHtml(detail.symbol)} fiyat grafiği: ${tl.format(prices[0])} → ${tl.format(prices.at(-1))}">
      ${ticks.map((v) => `<line class="grid" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>
        <text class="axis" x="${W - R + 6}" y="${y(v) + 4}">${compact.format(v)}</text>`).join("")}
      <path class="area" d="${area}"/>
      <path class="line" d="${line}"/>
      <text class="axis" x="${L}" y="${H - 6}">${fmtX.format(new Date(points[0].time))}</text>
      <text class="axis" x="${W - R}" y="${H - 6}" text-anchor="end">${fmtX.format(new Date(points.at(-1).time))}</text>
      <g class="hover" visibility="hidden">
        <line class="cursor" y1="${T}" y2="${H - B}"/>
        <circle r="4"/>
      </g>
      <rect class="hit" x="${L}" y="0" width="${W - L - R}" height="${H}"/>
    </svg>
    <div class="chart-tip" hidden></div>`;

  const svg = box.querySelector("svg");
  const hover = svg.querySelector(".hover");
  const tip = box.querySelector(".chart-tip");
  svg.querySelector(".hit").addEventListener("mousemove", (e) => {
    const rect = svg.getBoundingClientRect();
    const vx = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.max(0, Math.min(points.length - 1, Math.round(((vx - L) / (W - L - R)) * (points.length - 1))));
    const px = x(i), py = y(points[i].price);
    hover.setAttribute("visibility", "visible");
    hover.querySelector("line").setAttribute("x1", px);
    hover.querySelector("line").setAttribute("x2", px);
    hover.querySelector("circle").setAttribute("cx", px);
    hover.querySelector("circle").setAttribute("cy", py);
    tip.hidden = false;
    tip.innerHTML = `<strong>${tl.format(points[i].price)}</strong><span>${fmtX.format(new Date(points[i].time))}</span>`;
    const left = (px / W) * rect.width;
    tip.style.left = `${Math.min(Math.max(left, 60), rect.width - 60)}px`;
  });
  svg.querySelector(".hit").addEventListener("mouseleave", () => {
    hover.setAttribute("visibility", "hidden");
    tip.hidden = true;
  });
}

$("#detail-close").addEventListener("click", closeDetail);
$("#detail").addEventListener("click", (e) => {
  if (e.target === $("#detail")) closeDetail(); // panonun dışına tıklanınca kapanır
});
$("#detail-prev").addEventListener("click", () => openDetail(neighbours(detail.symbol).prev.symbol));
$("#detail-next").addEventListener("click", () => openDetail(neighbours(detail.symbol).next.symbol));
$("#detail-trade").addEventListener("click", () => {
  const symbol = detail.symbol;
  closeDetail();
  selectForTrade(symbol);
});
$("#range-tabs").addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (!tab || tab.dataset.range === detail.range) return;
  detail.range = tab.dataset.range;
  document.querySelectorAll("#range-tabs .tab").forEach((t) => t.classList.toggle("active", t === tab));
  loadPriceHistory();
});
// Haber menüsü hazır; içerik GET /api/news (#38) gelince bu filtreye göre listelenecek.
$("#news-tabs").addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  document.querySelectorAll("#news-tabs .tab").forEach((t) => t.classList.toggle("active", t === tab));
});
document.addEventListener("keydown", (e) => {
  if ($("#detail").hidden) return;
  if (e.key === "Escape") closeDetail();
  else if ($("#detail-prev").hidden) return;
  else if (e.key === "ArrowUp") openDetail(neighbours(detail.symbol).prev.symbol);
  else if (e.key === "ArrowDown") openDetail(neighbours(detail.symbol).next.symbol);
  else return;
  e.preventDefault();
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
