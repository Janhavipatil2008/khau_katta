// Point this at your deployed backend URL (e.g. https://khau-katta-api.onrender.com)
const API_BASE = "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

let menuItems = [];
let cart = {}; // { menu_item_id: quantity }
let currentOrderId = null;
let pollTimer = null;

// ---------- Menu ----------
async function loadMenu() {
  const res = await fetch(`${API_BASE}/menu`);
  menuItems = await res.json();
  renderMenu();
}

function renderMenu() {
  const container = document.getElementById("menu-list");
  container.innerHTML = "";
  menuItems.forEach((item) => {
    const div = document.createElement("div");
    div.className = "menu-item";
    div.innerHTML = `
      <h4>${item.name}</h4>
      <div class="meta">₹${item.price} · ~${item.prep_time_minutes} min · ${item.category}</div>
      <button data-id="${item.id}">Add to order</button>
    `;
    div.querySelector("button").addEventListener("click", () => addToCart(item.id));
    container.appendChild(div);
  });
}

// ---------- Cart ----------
function addToCart(itemId) {
  cart[itemId] = (cart[itemId] || 0) + 1;
  renderCart();
}

function renderCart() {
  const list = document.getElementById("cart-list");
  list.innerHTML = "";
  let total = 0;
  Object.entries(cart).forEach(([id, qty]) => {
    const item = menuItems.find((m) => m.id == id);
    if (!item) return;
    const lineTotal = item.price * qty;
    total += lineTotal;
    const row = document.createElement("div");
    row.className = "cart-row";
    row.innerHTML = `<span>${item.name} × ${qty}</span><span>₹${lineTotal}</span>`;
    list.appendChild(row);
  });
  document.getElementById("cart-total").textContent = total;
}

// ---------- Place order ----------
async function placeOrder() {
  const studentName = document.getElementById("student-name").value.trim();
  if (!studentName) return alert("Please enter your name");
  const items = Object.entries(cart).map(([menu_item_id, quantity]) => ({
    menu_item_id: Number(menu_item_id),
    quantity,
  }));
  if (items.length === 0) return alert("Your cart is empty");

  const res = await fetch(`${API_BASE}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_name: studentName, items }),
  });
  if (!res.ok) return alert("Could not place order");
  const order = await res.json();

  cart = {};
  renderCart();
  showOrderResult(order);
  currentOrderId = order.id;
  startTracking(order.id);
}

function showOrderResult(order) {
  document.getElementById("order-result").classList.remove("hidden");
  document.getElementById("result-token").textContent = `#${order.token_number}`;
  document.getElementById("result-status").textContent = order.status;
  const start = new Date(order.pickup_window_start).toLocaleTimeString();
  const end = new Date(order.pickup_window_end).toLocaleTimeString();
  document.getElementById("result-window").textContent = `${start} – ${end}`;
}

// ---------- Live order tracking (polling fallback if WS is unavailable) ----------
function startTracking(orderId) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const res = await fetch(`${API_BASE}/orders/${orderId}`);
    if (!res.ok) return;
    const order = await res.json();
    document.getElementById("result-status").textContent = order.status;
    if (order.status === "Collected") clearInterval(pollTimer);
  }, 4000);
}

// ---------- Live canteen dashboard ----------
async function loadQueueStatus() {
  const res = await fetch(`${API_BASE}/queue/status`);
  if (!res.ok) return;
  const q = await res.json();
  document.getElementById("stat-waiting").textContent = q.people_waiting;
  document.getElementById("stat-preparing").textContent = q.orders_preparing;
  document.getElementById("stat-ready").textContent = q.orders_ready;
  document.getElementById("stat-avgwait").textContent = q.average_wait_minutes;

  const pill = document.getElementById("crowd-pill");
  pill.textContent = `${q.rush_level} crowd`;
  pill.className = "pill pill-" + q.rush_level.toLowerCase();
}

// ---------- WebSocket for real-time push updates ----------
function connectWebSocket() {
  const ws = new WebSocket(`${WS_BASE}/ws/orders`);
  ws.onmessage = () => {
    loadQueueStatus();
    if (currentOrderId) startTracking(currentOrderId);
  };
  ws.onclose = () => setTimeout(connectWebSocket, 3000); // auto-reconnect
  ws.onopen = () => setInterval(() => ws.send("ping"), 20000); // keep-alive
}

// ---------- Init ----------
document.getElementById("place-order-btn").addEventListener("click", placeOrder);

loadMenu();
loadQueueStatus();
setInterval(loadQueueStatus, 8000); // polling fallback for the dashboard
connectWebSocket();
