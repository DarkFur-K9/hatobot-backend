import { useState, useEffect } from "react";

// ── Menu Data (mirror backend MENU_ITEMS) ──
const MENU_ITEMS = [
  { id: "1",  name: "Idli (2 pcs)",       price: 40,  cat: "🌅 Breakfast" },
  { id: "2",  name: "Masala Dosa",         price: 70,  cat: "🌅 Breakfast" },
  { id: "3",  name: "Pongal",              price: 60,  cat: "🌅 Breakfast" },
  { id: "4",  name: "Chettinad Chicken",   price: 220, cat: "🍛 Main Course" },
  { id: "5",  name: "Mutton Kuzhambu",     price: 280, cat: "🍛 Main Course" },
  { id: "6",  name: "Fish Curry",          price: 200, cat: "🍛 Main Course" },
  { id: "7",  name: "Chicken Biryani",     price: 180, cat: "🍛 Main Course" },
  { id: "8",  name: "Veg Biryani",         price: 130, cat: "🍛 Main Course" },
  { id: "9",  name: "Kothu Parotta",       price: 120, cat: "🫓 Snacks" },
  { id: "10", name: "Filter Coffee",       price: 30,  cat: "☕ Beverages" },
];

const CATEGORIES = [...new Set(MENU_ITEMS.map(i => i.cat))];

// ── Helpers ──
function getPhone() {
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    return params.get("phone") || "";
  }
  return "";
}

function buildWhatsAppText(cart) {
  const lines = cart.map(item => `${item.id}x${item.qty}`).join(",");
  return `ORDER:${lines}`;
}

function getTotal(cart) {
  return cart.reduce((sum, item) => sum + item.price * item.qty, 0);
}

export default function HatoBotCart() {
  const [cart, setCart] = useState({}); // {id: qty}
  const [activeCategory, setActiveCategory] = useState("all");
  const [showSuccess, setShowSuccess] = useState(false);
  const phone = getPhone();

  const cartItems = Object.entries(cart)
    .map(([id, qty]) => ({ ...MENU_ITEMS.find(i => i.id === id), qty }))
    .filter(Boolean);

  const total = getTotal(cartItems);
  const itemCount = cartItems.reduce((s, i) => s + i.qty, 0);

  function setQty(id, delta) {
    setCart(prev => {
      const cur = prev[id] || 0;
      const next = Math.max(0, cur + delta);
      if (next === 0) {
        const { [id]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [id]: next };
    });
  }

  const filteredItems = activeCategory === "all"
    ? MENU_ITEMS
    : MENU_ITEMS.filter(i => i.cat === activeCategory);

  function placeOrder() {
    if (cartItems.length === 0) return;
    const orderText = buildWhatsAppText(cartItems);
    // Send back to WhatsApp
    const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(orderText)}`;
    // Fallback: just open WA with pre-filled text
    window.location.href = waUrl;
  }

  return (
    <div style={styles.root}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div>
            <div style={styles.headerTag}>🏨 Chennai Hotel</div>
            <h1 style={styles.headerTitle}>Our Menu</h1>
          </div>
          {itemCount > 0 && (
            <div style={styles.cartBadge}>
              <span style={styles.cartIcon}>🛒</span>
              <span style={styles.cartCount}>{itemCount}</span>
            </div>
          )}
        </div>

        {/* Category Tabs */}
        <div style={styles.tabsWrapper}>
          <div style={styles.tabs}>
            <button
              style={{ ...styles.tab, ...(activeCategory === "all" ? styles.tabActive : {}) }}
              onClick={() => setActiveCategory("all")}
            >
              All
            </button>
            {CATEGORIES.map(cat => (
              <button
                key={cat}
                style={{ ...styles.tab, ...(activeCategory === cat ? styles.tabActive : {}) }}
                onClick={() => setActiveCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Menu Items */}
      <div style={styles.menuList}>
        {filteredItems.map(item => {
          const qty = cart[item.id] || 0;
          return (
            <div key={item.id} style={styles.menuItem}>
              <div style={styles.itemInfo}>
                <div style={styles.itemName}>{item.name}</div>
                <div style={styles.itemPrice}>₹{item.price}</div>
              </div>
              <div style={styles.stepper}>
                {qty > 0 ? (
                  <>
                    <button style={styles.stepBtn} onClick={() => setQty(item.id, -1)}>−</button>
                    <span style={styles.qtyText}>{qty}</span>
                    <button style={{ ...styles.stepBtn, ...styles.stepBtnAdd }} onClick={() => setQty(item.id, 1)}>+</button>
                  </>
                ) : (
                  <button style={styles.addBtn} onClick={() => setQty(item.id, 1)}>ADD</button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Cart Summary */}
      {cartItems.length > 0 && (
        <div style={styles.cartSummary}>
          <div style={styles.cartHeader}>
            <span style={styles.cartTitle}>🛒 Your Cart</span>
            <span style={styles.cartItemCount}>{itemCount} item{itemCount > 1 ? "s" : ""}</span>
          </div>
          <div style={styles.cartLines}>
            {cartItems.map(item => (
              <div key={item.id} style={styles.cartLine}>
                <div style={styles.cartLineName}>{item.name}</div>
                <div style={styles.cartLineControls}>
                  <button style={styles.miniBtn} onClick={() => setQty(item.id, -1)}>−</button>
                  <span style={styles.miniQty}>{item.qty}</span>
                  <button style={{ ...styles.miniBtn, ...styles.miniBtnAdd }} onClick={() => setQty(item.id, 1)}>+</button>
                </div>
                <div style={styles.cartLinePrice}>₹{item.price * item.qty}</div>
              </div>
            ))}
          </div>
          <div style={styles.cartTotal}>
            <span>Total</span>
            <span style={styles.totalAmount}>₹{total}</span>
          </div>
        </div>
      )}

      {/* Sticky Place Order Button */}
      <div style={{
        ...styles.stickyBar,
        opacity: cartItems.length > 0 ? 1 : 0,
        pointerEvents: cartItems.length > 0 ? "auto" : "none",
      }}>
        <div style={styles.stickyContent}>
          <div>
            <div style={styles.stickyCount}>{itemCount} item{itemCount > 1 ? "s" : ""}</div>
            <div style={styles.stickyTotal}>₹{total}</div>
          </div>
          <button style={styles.placeOrderBtn} onClick={placeOrder}>
            Place Order →
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Styles ──
const styles = {
  root: {
    minHeight: "100vh",
    background: "#f7f7f2",
    fontFamily: "'Segoe UI', sans-serif",
    maxWidth: 480,
    margin: "0 auto",
    paddingBottom: 100,
  },
  header: {
    background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
    color: "#fff",
    paddingBottom: 0,
    position: "sticky",
    top: 0,
    zIndex: 100,
    boxShadow: "0 2px 12px rgba(0,0,0,0.18)",
  },
  headerContent: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: "16px 20px 8px",
  },
  headerTag: {
    fontSize: 11,
    color: "#f4a261",
    fontWeight: 600,
    letterSpacing: 1,
    textTransform: "uppercase",
    marginBottom: 2,
  },
  headerTitle: {
    margin: 0,
    fontSize: 22,
    fontWeight: 800,
    color: "#fff",
    letterSpacing: -0.5,
  },
  cartBadge: {
    background: "#f4a261",
    borderRadius: 20,
    padding: "6px 14px",
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  cartIcon: { fontSize: 16 },
  cartCount: { fontWeight: 800, fontSize: 15, color: "#1a1a2e" },
  tabsWrapper: {
    overflowX: "auto",
    scrollbarWidth: "none",
    WebkitOverflowScrolling: "touch",
    padding: "8px 12px 0",
  },
  tabs: {
    display: "flex",
    gap: 8,
    paddingBottom: 1,
    minWidth: "max-content",
  },
  tab: {
    background: "rgba(255,255,255,0.1)",
    color: "rgba(255,255,255,0.7)",
    border: "none",
    borderRadius: "20px 20px 0 0",
    padding: "8px 14px",
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "all 0.15s",
  },
  tabActive: {
    background: "#f7f7f2",
    color: "#1a1a2e",
  },
  menuList: {
    padding: "12px 16px 0",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  menuItem: {
    background: "#fff",
    borderRadius: 14,
    padding: "14px 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
  },
  itemInfo: { flex: 1 },
  itemName: {
    fontSize: 15,
    fontWeight: 600,
    color: "#1a1a2e",
    marginBottom: 3,
  },
  itemPrice: {
    fontSize: 14,
    color: "#f4a261",
    fontWeight: 700,
  },
  stepper: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginLeft: 12,
  },
  stepBtn: {
    width: 34,
    height: 34,
    borderRadius: "50%",
    border: "2px solid #e0e0e0",
    background: "#fff",
    fontSize: 20,
    fontWeight: 700,
    color: "#555",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    lineHeight: 1,
    padding: 0,
  },
  stepBtnAdd: {
    background: "#1a1a2e",
    border: "2px solid #1a1a2e",
    color: "#fff",
  },
  qtyText: {
    fontSize: 17,
    fontWeight: 800,
    color: "#1a1a2e",
    minWidth: 20,
    textAlign: "center",
  },
  addBtn: {
    background: "#1a1a2e",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "9px 18px",
    fontWeight: 800,
    fontSize: 13,
    letterSpacing: 0.5,
    cursor: "pointer",
  },
  cartSummary: {
    margin: "16px 16px 0",
    background: "#fff",
    borderRadius: 16,
    padding: "16px",
    boxShadow: "0 2px 12px rgba(0,0,0,0.07)",
  },
  cartHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  cartTitle: {
    fontWeight: 800,
    fontSize: 16,
    color: "#1a1a2e",
  },
  cartItemCount: {
    fontSize: 12,
    color: "#888",
    fontWeight: 600,
  },
  cartLines: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    marginBottom: 12,
  },
  cartLine: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  cartLineName: {
    flex: 1,
    fontSize: 14,
    color: "#333",
    fontWeight: 500,
  },
  cartLineControls: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  miniBtn: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    border: "1.5px solid #ddd",
    background: "#fff",
    fontSize: 16,
    fontWeight: 700,
    color: "#555",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 0,
  },
  miniBtnAdd: {
    background: "#1a1a2e",
    border: "1.5px solid #1a1a2e",
    color: "#fff",
  },
  miniQty: {
    fontSize: 15,
    fontWeight: 800,
    minWidth: 18,
    textAlign: "center",
    color: "#1a1a2e",
  },
  cartLinePrice: {
    fontSize: 14,
    fontWeight: 700,
    color: "#f4a261",
    minWidth: 50,
    textAlign: "right",
  },
  cartTotal: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 12,
    borderTop: "1px solid #f0f0f0",
    fontWeight: 700,
    fontSize: 15,
    color: "#1a1a2e",
  },
  totalAmount: {
    fontSize: 20,
    fontWeight: 900,
    color: "#1a1a2e",
  },
  stickyBar: {
    position: "fixed",
    bottom: 0,
    left: "50%",
    transform: "translateX(-50%)",
    width: "100%",
    maxWidth: 480,
    padding: "12px 16px",
    background: "rgba(255,255,255,0.95)",
    backdropFilter: "blur(12px)",
    borderTop: "1px solid #eee",
    boxShadow: "0 -4px 20px rgba(0,0,0,0.1)",
    transition: "opacity 0.2s",
    zIndex: 200,
  },
  stickyContent: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  stickyCount: {
    fontSize: 12,
    color: "#888",
    fontWeight: 600,
  },
  stickyTotal: {
    fontSize: 20,
    fontWeight: 900,
    color: "#1a1a2e",
  },
  placeOrderBtn: {
    background: "linear-gradient(135deg, #f4a261, #e76f51)",
    color: "#fff",
    border: "none",
    borderRadius: 14,
    padding: "14px 28px",
    fontWeight: 800,
    fontSize: 16,
    cursor: "pointer",
    boxShadow: "0 4px 14px rgba(244,162,97,0.4)",
    letterSpacing: 0.3,
  },
};
