/*
 * mock-api.js - frontend-only mock backend for the static demo deploy.
 *
 * Patches window.fetch for every /api/* request the pages make and serves
 * them from an in-browser store persisted to localStorage. No real backend,
 * no network calls for /api/* paths. Everything else passes through.
 *
 * Demo accounts (password: demo1234):
 *   user@demo.io      -> shopper
 *   provider@demo.io  -> provider (Kanoon Commerce)
 *   admin@demo.io     -> admin
 */
(function () {
  "use strict";

  var DB_KEY = "md_mock_db_v1";
  var SEED_VERSION = "seed-v1";
  var VAT_RATE = 0.07;
  var LATENCY_MS = 120;

  var SLIP_PLACEHOLDER =
    "data:image/svg+xml;utf8," +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="220" height="300">' +
        '<rect width="220" height="300" fill="#f1f5f9"/>' +
        '<rect x="20" y="20" width="180" height="40" fill="#e21515"/>' +
        '<text x="110" y="45" font-family="sans-serif" font-size="14" fill="#fff" text-anchor="middle">TRANSFER SLIP</text>' +
        '<text x="110" y="150" font-family="sans-serif" font-size="12" fill="#64748b" text-anchor="middle">Mock payment slip</text>' +
        '<text x="110" y="170" font-family="sans-serif" font-size="12" fill="#64748b" text-anchor="middle">(demo data)</text>' +
      "</svg>"
    );

  function img(seed) {
    return "https://picsum.photos/seed/" + seed + "/400/300";
  }

  /* ------------------------------------------------------------------ */
  /* Seed data                                                           */
  /* ------------------------------------------------------------------ */

  function buildSeed() {
    var providers = [
      { provider_id: "prov_kanoon", provider_name: "Kanoon Commerce", logo_url: img("kanoon-logo") },
      { provider_id: "prov_arena", provider_name: "Arena Sports", logo_url: img("arena-logo") },
      { provider_id: "prov_north", provider_name: "Northside Gear", logo_url: img("north-logo") }
    ];

    var shops = [
      { provider_id: "shop_kanoon_main", provider_name: "Kanoon Main Store", email: "shop@kanoon.dev", is_primary: true, owner_provider_id: "prov_kanoon", logo_url: img("kanoon-shop") },
      { provider_id: "shop_kanoon_outlet", provider_name: "Kanoon Outlet", email: "outlet@kanoon.dev", is_primary: false, owner_provider_id: "prov_kanoon", logo_url: img("kanoon-outlet") },
      { provider_id: "shop_arena_main", provider_name: "Arena Flagship", email: "shop@arena.dev", is_primary: true, owner_provider_id: "prov_arena", logo_url: img("arena-shop") },
      { provider_id: "shop_north_main", provider_name: "Northside Depot", email: "shop@north.dev", is_primary: true, owner_provider_id: "prov_north", logo_url: img("north-shop") }
    ];

    var products = [
      { _id: "p_runner", name: "Street Runner Sneakers", sku: "FW-1001", category: "Footwear", price: 2590, stock: 14, provider_id: "prov_kanoon", provider_name: "Kanoon Commerce", image_url: img("runner"), description: "Lightweight everyday running shoe.", featured: 1 },
      { _id: "p_court", name: "Court Classic Trainers", sku: "FW-1002", category: "Footwear", price: 1890, stock: 4, provider_id: "prov_arena", provider_name: "Arena Sports", image_url: img("court"), description: "Retro court silhouette.", featured: 0 },
      { _id: "p_trail", name: "Trail Grip Boots", sku: "FW-1003", category: "Footwear", price: 3290, stock: 0, provider_id: "prov_north", provider_name: "Northside Gear", image_url: img("trail"), description: "All-terrain grip, waterproof shell.", featured: 0 },
      { _id: "p_tee", name: "Matchday Graphic Tee", sku: "AP-2001", category: "Apparel", price: 590, stock: 42, provider_id: "prov_kanoon", provider_name: "Kanoon Commerce", image_url: img("tee"), description: "Soft cotton, unisex fit.", featured: 1 },
      { _id: "p_hoodie", name: "Club Fleece Hoodie", sku: "AP-2002", category: "Apparel", price: 1490, stock: 18, provider_id: "prov_arena", provider_name: "Arena Sports", image_url: img("hoodie"), description: "Heavyweight fleece hoodie.", featured: 0 },
      { _id: "p_shorts", name: "Training Shorts", sku: "AP-2003", category: "Apparel", price: 690, stock: 3, provider_id: "prov_kanoon", provider_name: "Kanoon Commerce", image_url: img("shorts"), description: "Quick-dry training shorts.", featured: 0 },
      { _id: "p_cap", name: "Performance Cap", sku: "AC-3001", category: "Accessories", price: 450, stock: 25, provider_id: "prov_north", provider_name: "Northside Gear", image_url: img("cap"), description: "Adjustable, breathable cap.", featured: 0 },
      { _id: "p_bottle", name: "Insulated Bottle 750ml", sku: "AC-3002", category: "Accessories", price: 390, stock: 30, provider_id: "prov_kanoon", provider_name: "Kanoon Commerce", image_url: img("bottle"), description: "Keeps drinks cold for 12 hours.", featured: 0 },
      { _id: "p_bag", name: "Weekend Duffel Bag", sku: "AC-3003", category: "Accessories", price: 1190, stock: 9, provider_id: "prov_arena", provider_name: "Arena Sports", image_url: img("bag"), description: "40L water-resistant duffel.", featured: 1 }
    ];

    function pricing(subtotal, discount) {
      var grand = round2(subtotal - discount);
      var taxable = round2(grand / (1 + VAT_RATE));
      return {
        subtotal: round2(subtotal),
        discount_amount: round2(discount),
        taxable_amount: taxable,
        tax_amount: round2(grand - taxable),
        grand_total: grand
      };
    }

    function seedOrder(n, daysAgo, statusLabel, paymentStatus, items, extra) {
      var subtotal = 0;
      items.forEach(function (it) { subtotal += it.unit_price * it.quantity; });
      var created = new Date(Date.now() - daysAgo * 86400000);
      var base = {
        order_id: "ord_" + String(1000 + n),
        invoice_number: "INV-2026-" + String(1000 + n),
        receipt_number: paymentStatus === "paid" ? "RCPT-2026-" + String(1000 + n) : "",
        created_at: created.toISOString(),
        customer_name: "Demo Shopper",
        customer_email: "user@demo.io",
        user_email: "user@demo.io",
        status: "active",
        status_label: statusLabel,
        payment_status: paymentStatus,
        payment_method: "qrcode",
        fulfillment_status: "",
        full_tax_invoice_status: "not_issued",
        shipping_address: "123 Your Street, City",
        notes: "",
        slip_image: null,
        items: items,
        pricing: pricing(subtotal, 0),
        payment_history: paymentStatus === "paid"
          ? [{ channel: "qrcode", status: "paid", amount: round2(subtotal), timestamp: created.toISOString(), note: "QR transfer confirmed" }]
          : []
      };
      Object.keys(extra || {}).forEach(function (k) { base[k] = extra[k]; });
      return base;
    }

    function item(productId, qty) {
      var p = null;
      products.forEach(function (cand) { if (cand._id === productId) { p = cand; } });
      return {
        product_id: p._id, name: p.name, sku: p.sku, category: p.category,
        provider_id: p.provider_id, provider_name: p.provider_name,
        quantity: qty, unit_price: p.price, image_url: p.image_url
      };
    }

    var orders = [
      seedOrder(1, 21, "completed", "paid", [item("p_runner", 1), item("p_tee", 2)]),
      seedOrder(2, 14, "paid", "paid", [item("p_hoodie", 1)]),
      seedOrder(3, 10, "shipping", "paid", [item("p_bag", 1), item("p_cap", 1)]),
      seedOrder(4, 6, "paid", "paid", [item("p_bottle", 3)]),
      seedOrder(5, 4, "completed", "refunded", [item("p_shorts", 2)], { fulfillment_status: "product_returned" }),
      seedOrder(6, 2, "awaiting_slip_verification", "pending_slip_verification", [item("p_court", 1)], { slip_image: SLIP_PLACEHOLDER }),
      seedOrder(7, 1, "slip_rejected", "slip_rejected", [item("p_cap", 2)]),
      seedOrder(8, 0, "pending_payment", "pending_payment", [item("p_tee", 1), item("p_bottle", 1)])
    ];

    var restocks = [
      { image_url: img("runner"), product_name: "Street Runner Sneakers", sku: "FW-1001", category: "Footwear", quantity_changed: 10, old_stock: 4, new_stock: 14, reason: "Weekly replenishment", timestamp: new Date(Date.now() - 3 * 86400000).toISOString() },
      { image_url: img("tee"), product_name: "Matchday Graphic Tee", sku: "AP-2001", category: "Apparel", quantity_changed: 20, old_stock: 22, new_stock: 42, reason: "New season stock", timestamp: new Date(Date.now() - 7 * 86400000).toISOString() }
    ];

    return {
      seed_version: SEED_VERSION,
      users: [
        { email: "user@demo.io", username: "Demo Shopper", password: "demo1234", role: "user" },
        { email: "provider@demo.io", username: "Kanoon Commerce", password: "demo1234", role: "provider", provider_id: "prov_kanoon" },
        { email: "admin@demo.io", username: "Demo Admin", password: "demo1234", role: "admin" }
      ],
      user_profiles: {
        "user@demo.io": { gender: "prefer_not_to_say", age: 28 }
      },
      providers: providers,
      shops: shops,
      products: products,
      orders: orders,
      restocks: restocks,
      staff: [
        { id: "staff_1", name: "Ploy S.", email: "ploy@kanoon.dev", phone: "080-111-2222", permission_level: 1, is_active: true },
        { id: "staff_2", name: "Beam T.", email: "beam@kanoon.dev", phone: "080-333-4444", permission_level: 3, is_active: true }
      ],
      provider_settings: {
        vat_registered: true,
        tax_id: "0105546000000",
        tax_name: "Kanoon Commerce Co., Ltd.",
        company_name: "Kanoon Commerce Co., Ltd.",
        address_mode: "registered",
        registered_address_line_1: "88 Sukhumvit Road",
        registered_address_line_2: "Khlong Toei, Bangkok 10110",
        branch_address_line_1: "",
        branch_address_line_2: "",
        branch_number: "",
        custom_tax_address: "",
        note: ""
      },
      studio_profiles: [
        { id: "prof_admin", name: "Demo Admin", email: "admin@demo.io", role: "Admin", phone: "081-000-1111", address: "1 Studio Lane, Bangkok" },
        { id: "prof_user", name: "Demo Shopper", email: "user@demo.io", role: "Buyer", phone: "081-000-2222", address: "123 Your Street, City" }
      ],
      counters: { order: 9, entity: 1 }
    };
  }

  /* ------------------------------------------------------------------ */
  /* Store                                                               */
  /* ------------------------------------------------------------------ */

  var db = null;

  function loadDb() {
    try {
      var raw = localStorage.getItem(DB_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && parsed.seed_version === SEED_VERSION) {
          db = parsed;
          return;
        }
      }
    } catch (e) { /* fall through to reseed */ }
    db = buildSeed();
    saveDb();
  }

  function saveDb() {
    try {
      localStorage.setItem(DB_KEY, JSON.stringify(db));
    } catch (e) { /* storage full (large slip images) - keep in-memory only */ }
  }

  function round2(n) {
    return Math.round((Number(n) || 0) * 100) / 100;
  }

  function nextId(prefix) {
    db.counters.entity += 1;
    return prefix + "_" + Date.now().toString(36) + "_" + db.counters.entity;
  }

  function nextOrderNumbers() {
    var n = 1000 + db.counters.order;
    db.counters.order += 1;
    return { order_id: "ord_" + n, invoice_number: "INV-2026-" + n };
  }

  /* ------------------------------------------------------------------ */
  /* Auth helpers                                                        */
  /* ------------------------------------------------------------------ */

  function makeToken(user) {
    return "mock-token:" + user.role + ":" + user.email;
  }

  function currentUser(headers) {
    var auth = headers && (headers.Authorization || headers.authorization);
    if (!auth) return null;
    var token = String(auth).replace(/^Bearer\s+/i, "");
    var parts = token.split(":");
    if (parts[0] !== "mock-token" || parts.length < 3) return null;
    var email = parts.slice(2).join(":");
    var found = null;
    db.users.forEach(function (u) { if (u.email === email) { found = u; } });
    return found;
  }

  function serializeProfile(user) {
    var extra = db.user_profiles[user.email] || {};
    return {
      id: "uid_" + user.email,
      name: user.username,
      username: user.username,
      email: user.email,
      role: user.role.charAt(0).toUpperCase() + user.role.slice(1),
      phone: extra.phone || "",
      address: extra.address || "",
      gender: extra.gender || "",
      age: extra.age !== undefined ? extra.age : null,
      is_provider_staff: false,
      provider_staff_owner_id: null,
      provider_staff_level: 4,
      provider_staff_permissions: {
        dashboard: true, inventory: true, sales_history: true,
        restock_history: true, settings: true
      },
      provider_account_type: user.role === "provider" ? "provider" : "user"
    };
  }

  /* ------------------------------------------------------------------ */
  /* Pricing / order helpers                                             */
  /* ------------------------------------------------------------------ */

  function computePricing(items, discountCode) {
    var subtotal = 0;
    items.forEach(function (it) { subtotal += (Number(it.unit_price) || 0) * (Number(it.quantity) || 0); });
    var discount = 0;
    if (discountCode && String(discountCode).trim().toUpperCase() === "WELCOME10") {
      discount = round2(subtotal * 0.1);
    }
    var grand = round2(subtotal - discount);
    var taxable = round2(grand / (1 + VAT_RATE));
    return {
      subtotal: round2(subtotal),
      discount_amount: discount,
      taxable_amount: taxable,
      tax_amount: round2(grand - taxable),
      grand_total: grand
    };
  }

  function findProduct(id) {
    var found = null;
    db.products.forEach(function (p) { if (p._id === id) { found = p; } });
    return found;
  }

  function findOrder(id) {
    var found = null;
    db.orders.forEach(function (o) { if (o.order_id === id) { found = o; } });
    return found;
  }

  function itemsFromPayload(payloadItems) {
    var items = [];
    (payloadItems || []).forEach(function (raw) {
      var p = findProduct(raw.product_id || raw.productId);
      if (!p) return;
      var qty = Number(raw.quantity) || 1;
      items.push({
        product_id: p._id, name: p.name, sku: p.sku, category: p.category,
        provider_id: p.provider_id, provider_name: p.provider_name,
        quantity: qty,
        unit_price: Number(raw.price_at_purchase || raw.price || p.price),
        image_url: p.image_url
      });
    });
    return items;
  }

  function restoreStock(order) {
    order.items.forEach(function (it) {
      var p = findProduct(it.product_id);
      if (p) { p.stock += it.quantity; }
    });
  }

  function uniqueList(values) {
    var out = [];
    values.forEach(function (v) { if (v && out.indexOf(v) === -1) { out.push(v); } });
    return out;
  }

  /* Projections ------------------------------------------------------- */

  function toUserOrder(o) {
    return {
      order_id: o.order_id,
      created_at: o.created_at,
      status_label: o.status_label,
      total_amount: o.pricing.grand_total,
      billing: { invoice_number: o.invoice_number },
      items: o.items.map(function (it) {
        return {
          name: it.name, image_url: it.image_url, quantity: it.quantity,
          price_at_purchase: it.unit_price,
          provider_name: it.provider_name, provider_id: it.provider_id
        };
      })
    };
  }

  function toAdminOrder(o) {
    return {
      order_id: o.order_id,
      invoice_number: o.invoice_number,
      created_at: o.created_at,
      customer_name: o.customer_name,
      customer_email: o.customer_email,
      payment_status: o.payment_status,
      payment_method: o.payment_method,
      total_amount: o.pricing.grand_total,
      provider_ids: uniqueList(o.items.map(function (it) { return it.provider_id; })),
      provider_names: uniqueList(o.items.map(function (it) { return it.provider_name; })),
      item_count: o.items.length,
      status_label: o.status_label,
      fulfillment_status: o.fulfillment_status,
      items: o.items.map(function (it) {
        return {
          name: it.name, provider_name: it.provider_name, sku: it.sku,
          quantity: it.quantity, price_at_purchase: it.unit_price,
          line_total: round2(it.unit_price * it.quantity), image_url: it.image_url
        };
      })
    };
  }

  function toSalesEntry(o) {
    return {
      order_id: o.order_id,
      created_at: o.created_at,
      invoice_number: o.invoice_number,
      receipt_number: o.receipt_number,
      customer_name: o.customer_name,
      customer_email: o.customer_email,
      customer_address: o.shipping_address || "",
      customer_tax_id: "",
      payment_status: o.payment_status,
      payment_status_key: o.payment_status,
      status: o.status,
      fulfillment_status: o.fulfillment_status,
      full_tax_invoice_status: o.full_tax_invoice_status,
      grand_total: o.pricing.grand_total,
      provider_total: o.pricing.grand_total,
      subtotal: o.pricing.subtotal,
      discount_amount: o.pricing.discount_amount,
      taxable_amount: o.pricing.taxable_amount,
      tax_amount: o.pricing.tax_amount,
      category: o.items.length ? o.items[0].category : "",
      payment_history: o.payment_history,
      items: o.items.map(function (it) {
        return {
          product_name: it.name, category: it.category, quantity: it.quantity,
          unit_price: it.unit_price, total_amount: round2(it.unit_price * it.quantity),
          image_url: it.image_url
        };
      })
    };
  }

  function toStudioOrder(o) {
    return {
      id: o.order_id,
      created_at: o.created_at,
      invoice_number: o.invoice_number,
      user_name: o.customer_name,
      customer_email: o.customer_email,
      profile_id: o.profile_id || "prof_user",
      payment_status: o.payment_status,
      payment_method: o.payment_method,
      total: o.pricing.grand_total,
      shipping_address: o.shipping_address,
      notes: o.notes,
      pricing: o.pricing,
      items: o.items.map(function (it) {
        return {
          productId: it.product_id, product_id: it.product_id,
          name: it.name, category: it.category, sku: it.sku,
          quantity: it.quantity, price: it.unit_price,
          lineTotal: round2(it.unit_price * it.quantity),
          image_url: it.image_url,
          providerId: it.provider_id, provider_id: it.provider_id
        };
      })
    };
  }

  function toStudioProduct(p) {
    return {
      id: p._id, name: p.name, sku: p.sku, category: p.category,
      price: p.price, stock: p.stock, featured: p.featured || 0,
      description: p.description || ""
    };
  }

  function providerWithShops(provider) {
    var shops = db.shops.filter(function (s) { return s.owner_provider_id === provider.provider_id; })
      .map(function (s) {
        return {
          provider_id: s.provider_id, provider_name: s.provider_name,
          logo_url: s.logo_url || provider.logo_url,
          product_count: db.products.filter(function (p) { return p.provider_id === provider.provider_id; }).length,
          owner_provider_id: s.owner_provider_id
        };
      });
    return {
      provider_id: provider.provider_id,
      provider_name: provider.provider_name,
      logo_url: provider.logo_url,
      shop_count: shops.length,
      shop_names: shops.map(function (s) { return s.provider_name; }),
      shops: shops
    };
  }

  /* ------------------------------------------------------------------ */
  /* Filters / pagination                                                */
  /* ------------------------------------------------------------------ */

  function matchesDateFilter(iso, params) {
    if (!iso) return true;
    var d = new Date(iso);
    if (params.get("year") && d.getFullYear() !== Number(params.get("year"))) return false;
    if (params.get("month") && d.getMonth() + 1 !== Number(params.get("month"))) return false;
    if (params.get("day") && d.getDate() !== Number(params.get("day"))) return false;
    return true;
  }

  function paginate(list, params) {
    var page = Math.max(1, Number(params.get("page")) || 1);
    var size = Math.max(1, Number(params.get("page_size")) || 10);
    var totalPages = Math.max(1, Math.ceil(list.length / size));
    return {
      history: list.slice((page - 1) * size, page * size),
      pagination: { page: page, page_size: size, total_count: list.length, total_pages: totalPages }
    };
  }

  /* ------------------------------------------------------------------ */
  /* Router                                                              */
  /* ------------------------------------------------------------------ */

  function json(body, status) {
    return { status: status || 200, body: body };
  }

  function err(status, detail) {
    return { status: status, body: { detail: detail } };
  }

  var routes = [];

  function route(method, pattern, handler) {
    routes.push({ method: method, pattern: pattern, handler: handler });
  }

  /* ---- auth ---- */

  route("POST", /^\/api\/auth\/login$/, function (ctx) {
    var body = ctx.body || {};
    var user = null;
    db.users.forEach(function (u) { if (u.email === body.email) { user = u; } });
    if (!user || user.password !== body.password) {
      return err(401, "Invalid credentials. Demo accounts: user@demo.io / provider@demo.io / admin@demo.io with password demo1234");
    }
    return json({
      user_id: "uid_" + user.email,
      access_token: makeToken(user),
      token_type: "bearer",
      role: user.role,
      profile: serializeProfile(user)
    });
  });

  route("POST", /^\/api\/auth\/register$/, function (ctx) {
    var body = ctx.body || {};
    var exists = false;
    db.users.forEach(function (u) { if (u.email === body.email) { exists = true; } });
    if (exists) return err(400, "Email already registered");
    var user = {
      email: body.email,
      username: body.username || String(body.email).split("@")[0],
      password: body.password,
      role: body.role || "user"
    };
    db.users.push(user);
    saveDb();
    return json({
      user_id: "uid_" + user.email,
      access_token: makeToken(user),
      token_type: "bearer",
      role: user.role,
      profile: serializeProfile(user)
    });
  });

  /* ---- user ---- */

  route("GET", /^\/api\/user\/profile$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    return json({ profile: serializeProfile(ctx.user) });
  });

  route("PUT", /^\/api\/user\/profile$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    var extra = db.user_profiles[ctx.user.email] || {};
    if (ctx.body) {
      if (ctx.body.gender !== undefined) extra.gender = ctx.body.gender;
      if (ctx.body.age !== undefined) extra.age = ctx.body.age;
    }
    db.user_profiles[ctx.user.email] = extra;
    saveDb();
    return json({ profile: serializeProfile(ctx.user) });
  });

  route("GET", /^\/api\/user\/products$/, function () {
    return json({ products: db.products.slice() });
  });

  route("GET", /^\/api\/user\/providers$/, function () {
    return json({
      providers: db.providers.map(function (p) {
        return { provider_id: p.provider_id, provider_name: p.provider_name };
      })
    });
  });

  route("GET", /^\/api\/user\/orders$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    var mine = db.orders.filter(function (o) { return o.user_email === ctx.user.email; });
    mine.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    return json({ orders: mine.map(toUserOrder) });
  });

  route("POST", /^\/api\/user\/orders\/preview$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    var items = itemsFromPayload(ctx.body && ctx.body.items);
    return json({
      pricing: computePricing(items, ctx.body && ctx.body.discount_code),
      billing: { invoice_number: "INV-2026-" + (1000 + db.counters.order) }
    });
  });

  route("POST", /^\/api\/user\/orders$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    var items = itemsFromPayload(ctx.body && ctx.body.items);
    if (!items.length) return err(400, "No purchasable items in order");
    for (var i = 0; i < items.length; i += 1) {
      var p = findProduct(items[i].product_id);
      if (p.stock < items[i].quantity) {
        return err(400, "Not enough stock for " + p.name + " (available: " + p.stock + ")");
      }
    }
    items.forEach(function (it) { findProduct(it.product_id).stock -= it.quantity; });
    var nums = nextOrderNumbers();
    var order = {
      order_id: nums.order_id,
      invoice_number: nums.invoice_number,
      receipt_number: "",
      created_at: new Date().toISOString(),
      customer_name: ctx.user.username,
      customer_email: ctx.user.email,
      user_email: ctx.user.email,
      status: "active",
      status_label: "pending_payment",
      payment_status: "pending_payment",
      payment_method: (ctx.body && ctx.body.payment_method) || "qrcode",
      fulfillment_status: "",
      full_tax_invoice_status: "not_issued",
      shipping_address: (ctx.body && ctx.body.shipping_address) || "",
      notes: "",
      slip_image: null,
      items: items,
      pricing: computePricing(items, ctx.body && ctx.body.discount_code),
      payment_history: []
    };
    db.orders.push(order);
    saveDb();
    return json({ order_id: order.order_id, billing: { invoice_number: order.invoice_number } });
  });

  route("POST", /^\/api\/user\/orders\/([^/]+)\/submit-slip$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    var order = findOrder(ctx.match[1]);
    if (!order) return err(404, "Order not found");
    order.status_label = "awaiting_slip_verification";
    order.payment_status = "pending_slip_verification";
    order.slip_image = SLIP_PLACEHOLDER;
    if (ctx.body && ctx.body.customer_name) order.customer_name = ctx.body.customer_name;
    saveDb();
    return json({ status: "submitted" });
  });

  route("GET", /^\/api\/user\/shops$/, function () {
    return json({
      shops: db.shops.map(function (s) {
        return { provider_id: s.provider_id, provider_name: s.provider_name };
      })
    });
  });

  route("POST", /^\/api\/user\/shops$/, function (ctx) {
    if (!ctx.user) return err(401, "Not authenticated");
    db.shops.push({
      provider_id: nextId("shop"),
      provider_name: (ctx.body && ctx.body.name) || "New Shop",
      email: (ctx.body && ctx.body.email) || "",
      is_primary: false,
      owner_provider_id: "prov_kanoon",
      logo_url: img("shop-new")
    });
    saveDb();
    return json({ status: "created" });
  });

  /* ---- admin ---- */

  function paidRevenue() {
    var total = 0;
    db.orders.forEach(function (o) {
      if (o.payment_status === "paid" && o.status !== "cancelled") { total += o.pricing.grand_total; }
    });
    return round2(total);
  }

  route("GET", /^\/api\/admin\/dashboard$/, function (ctx) {
    if (!ctx.user) return err(401, "Unauthorized");
    var totalStock = 0;
    db.products.forEach(function (p) { totalStock += p.stock; });
    return json({
      total_products: db.products.length,
      total_stock: totalStock,
      total_revenue: paidRevenue(),
      total_orders: db.orders.length,
      sku_summary: db.products.map(function (p) {
        return { sku: p.sku, product_name: p.name, stock: p.stock, price: p.price, total_value: round2(p.price * p.stock) };
      })
    });
  });

  route("GET", /^\/api\/admin\/inventory-status$/, function () {
    var critical = db.products.filter(function (p) { return p.stock <= 2; }).length;
    var low = db.products.filter(function (p) { return p.stock > 2 && p.stock <= 5; }).length;
    return json({ critical_stock: { count: critical }, low_stock: { count: low } });
  });

  function slipReviewList() {
    return db.orders
      .filter(function (o) { return o.status_label === "awaiting_slip_verification"; })
      .map(function (o) {
        return {
          order_id: o.order_id, invoice_number: o.invoice_number,
          customer_name: o.customer_name, customer_email: o.customer_email,
          total_amount: o.pricing.grand_total, slip_image: o.slip_image
        };
      });
  }

  function reviewSlip(orderId, action) {
    var order = findOrder(orderId);
    if (!order) return err(404, "Order not found");
    if (action === "approve") {
      order.status_label = "paid";
      order.payment_status = "paid";
      order.receipt_number = order.invoice_number.replace("INV", "RCPT");
      order.payment_history.push({
        channel: "qrcode", status: "paid", amount: order.pricing.grand_total,
        timestamp: new Date().toISOString(), note: "Slip approved"
      });
    } else {
      order.status_label = "slip_rejected";
      order.payment_status = "slip_rejected";
    }
    saveDb();
    return json({ status: action });
  }

  route("GET", /^\/api\/(admin|provider)\/slip-reviews$/, function () {
    return json({ orders: slipReviewList() });
  });

  route("POST", /^\/api\/(admin|provider)\/slip-reviews\/([^/]+)\/(approve|reject)$/, function (ctx) {
    return reviewSlip(ctx.match[2], ctx.match[3]);
  });

  route("GET", /^\/api\/admin\/providers$/, function () {
    return json({ providers: db.providers.map(providerWithShops) });
  });

  route("GET", /^\/api\/admin\/orders$/, function (ctx) {
    if (!ctx.user) return err(401, "Unauthorized");
    var list = db.orders.slice();
    list.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    return json({ orders: list.map(toAdminOrder) });
  });

  route("POST", /^\/api\/admin\/provider-shops$/, function (ctx) {
    var providerId = ctx.params.get("provider_id");
    var provider = null;
    db.providers.forEach(function (p) { if (p.provider_id === providerId) { provider = p; } });
    if (!provider) return err(404, "Provider not found");
    var shop = {
      provider_id: nextId("shop"),
      provider_name: (ctx.body && ctx.body.name) || "New Shop",
      email: (ctx.body && ctx.body.email) || "",
      is_primary: false,
      owner_provider_id: provider.provider_id,
      logo_url: provider.logo_url
    };
    db.shops.push(shop);
    saveDb();
    return json({ shop: { provider_name: shop.provider_name } });
  });

  route("DELETE", /^\/api\/admin\/provider-shops\/([^/]+)$/, function (ctx) {
    var before = db.shops.length;
    db.shops = db.shops.filter(function (s) { return s.provider_id !== ctx.match[1]; });
    if (db.shops.length === before) return err(404, "Shop not found");
    saveDb();
    return json({ status: "deleted" });
  });

  /* ---- admin studio ---- */

  route("GET", /^\/api\/admin\/studio\/bootstrap$/, function () {
    var orders = db.orders.slice();
    orders.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    return json({
      profiles: db.studio_profiles.slice(),
      products: db.products.map(toStudioProduct),
      orders: orders.map(toStudioOrder)
    });
  });

  route("POST", /^\/api\/admin\/studio\/profiles$/, function (ctx) {
    var profile = {
      id: nextId("prof"),
      name: (ctx.body && ctx.body.name) || "New Profile",
      email: (ctx.body && ctx.body.email) || "",
      role: (ctx.body && ctx.body.role) || "buyer",
      phone: (ctx.body && ctx.body.phone) || "",
      address: (ctx.body && ctx.body.address) || ""
    };
    db.studio_profiles.push(profile);
    saveDb();
    return json({ profile: profile });
  });

  route("PUT", /^\/api\/admin\/studio\/profiles\/([^/]+)$/, function (ctx) {
    var profile = null;
    db.studio_profiles.forEach(function (p) { if (p.id === ctx.match[1]) { profile = p; } });
    if (!profile) return err(404, "Profile not found");
    ["name", "email", "role", "phone", "address"].forEach(function (k) {
      if (ctx.body && ctx.body[k] !== undefined) profile[k] = ctx.body[k];
    });
    saveDb();
    return json({ profile: profile });
  });

  route("DELETE", /^\/api\/admin\/studio\/profiles\/([^/]+)$/, function (ctx) {
    db.studio_profiles = db.studio_profiles.filter(function (p) { return p.id !== ctx.match[1]; });
    saveDb();
    return json({ status: "deleted" });
  });

  route("POST", /^\/api\/admin\/studio\/products$/, function (ctx) {
    var body = ctx.body || {};
    var product = {
      _id: nextId("p"),
      name: body.name || "New Product",
      sku: body.sku || "SKU-NEW",
      category: body.category || "Accessories",
      price: Number(body.price) || 0,
      stock: Number(body.stock) || 0,
      featured: body.featured ? 1 : 0,
      description: body.description || "",
      provider_id: "prov_kanoon",
      provider_name: "Kanoon Commerce",
      image_url: img("studio-" + Date.now().toString(36))
    };
    db.products.push(product);
    saveDb();
    return json({ product: toStudioProduct(product) });
  });

  route("PUT", /^\/api\/admin\/studio\/products\/([^/]+)$/, function (ctx) {
    var product = findProduct(ctx.match[1]);
    if (!product) return err(404, "Product not found");
    var body = ctx.body || {};
    ["name", "sku", "category", "description"].forEach(function (k) {
      if (body[k] !== undefined) product[k] = body[k];
    });
    if (body.price !== undefined) product.price = Number(body.price) || 0;
    if (body.stock !== undefined) product.stock = Number(body.stock) || 0;
    if (body.featured !== undefined) product.featured = body.featured ? 1 : 0;
    saveDb();
    return json({ product: toStudioProduct(product) });
  });

  route("DELETE", /^\/api\/admin\/studio\/products\/([^/]+)$/, function (ctx) {
    db.products = db.products.filter(function (p) { return p._id !== ctx.match[1]; });
    saveDb();
    return json({ status: "deleted" });
  });

  function studioOrderFromBody(body, existing) {
    var order = existing;
    if (!order) {
      var nums = nextOrderNumbers();
      order = {
        order_id: nums.order_id, invoice_number: nums.invoice_number, receipt_number: "",
        created_at: new Date().toISOString(),
        customer_name: "", customer_email: "", user_email: "user@demo.io",
        status: "active", status_label: "paid", payment_status: "paid",
        payment_method: "qrcode", fulfillment_status: "", full_tax_invoice_status: "not_issued",
        shipping_address: "", notes: "", slip_image: null,
        items: [], pricing: computePricing([], null), payment_history: []
      };
      db.orders.push(order);
    }
    if (body.user_name !== undefined) order.customer_name = body.user_name;
    if (body.profile_id !== undefined) {
      order.profile_id = body.profile_id;
      db.studio_profiles.forEach(function (p) {
        if (p.id === body.profile_id) { order.customer_email = p.email; if (!order.customer_name) order.customer_name = p.name; }
      });
    }
    if (body.status !== undefined) order.payment_status = String(body.status);
    if (body.notes !== undefined) order.notes = body.notes;
    if (body.items !== undefined) {
      var items = itemsFromPayload(body.items);
      if (items.length) order.items = items;
      order.pricing = computePricing(order.items, null);
    }
    if (body.total !== undefined && Number(body.total) > 0) {
      order.pricing.grand_total = round2(body.total);
    }
    return order;
  }

  route("POST", /^\/api\/admin\/studio\/orders$/, function (ctx) {
    var order = studioOrderFromBody(ctx.body || {}, null);
    saveDb();
    return json({ order: toStudioOrder(order) });
  });

  route("PUT", /^\/api\/admin\/studio\/orders\/([^/]+)$/, function (ctx) {
    var order = findOrder(ctx.match[1]);
    if (!order) return err(404, "Order not found");
    studioOrderFromBody(ctx.body || {}, order);
    saveDb();
    return json({ order: toStudioOrder(order) });
  });

  route("DELETE", /^\/api\/admin\/studio\/orders\/([^/]+)$/, function (ctx) {
    db.orders = db.orders.filter(function (o) { return o.order_id !== ctx.match[1]; });
    saveDb();
    return json({ status: "deleted" });
  });

  route("POST", /^\/api\/admin\/studio\/checkout$/, function (ctx) {
    var body = ctx.body || {};
    var items = itemsFromPayload(body.items);
    if (!items.length) return err(400, "Cart is empty");
    items.forEach(function (it) {
      var p = findProduct(it.product_id);
      if (p) { p.stock = Math.max(0, p.stock - it.quantity); }
    });
    var order = studioOrderFromBody({
      profile_id: body.profile_id, items: body.items, notes: body.notes, status: "paid"
    }, null);
    saveDb();
    return json({ order: toStudioOrder(order) });
  });

  /* ---- provider ---- */

  function providerIdFor(user) {
    return (user && user.provider_id) || "prov_kanoon";
  }

  route("GET", /^\/api\/provider\/shops$/, function (ctx) {
    var pid = providerIdFor(ctx.user);
    return json({
      shops: db.shops
        .filter(function (s) { return s.owner_provider_id === pid; })
        .map(function (s) {
          return { provider_id: s.provider_id, provider_name: s.provider_name, is_primary: s.is_primary, email: s.email };
        })
    });
  });

  route("POST", /^\/api\/provider\/shops$/, function (ctx) {
    var pid = providerIdFor(ctx.user);
    db.shops.push({
      provider_id: nextId("shop"),
      provider_name: (ctx.body && ctx.body.name) || "New Shop",
      email: (ctx.body && ctx.body.email) || "",
      is_primary: false, owner_provider_id: pid, logo_url: img("shop-new")
    });
    saveDb();
    return json({ status: "created" });
  });

  route("GET", /^\/api\/provider\/products$/, function (ctx) {
    var list = db.products.slice();
    var category = ctx.params.get("category");
    if (category) list = list.filter(function (p) { return p.category === category; });
    var providerId = ctx.params.get("provider_id");
    if (providerId) list = list.filter(function (p) { return p.provider_id === providerId; });
    return json({ products: list });
  });

  route("POST", /^\/api\/provider\/products$/, function (ctx) {
    var body = ctx.body || {};
    var pid = body.provider_id || providerIdFor(ctx.user);
    var providerName = "Kanoon Commerce";
    db.providers.forEach(function (p) { if (p.provider_id === pid) { providerName = p.provider_name; } });
    var product = {
      _id: nextId("p"),
      name: body.name || "New Product",
      sku: body.sku || "SKU-NEW",
      category: body.category || "Other",
      price: Number(body.price) || 0,
      stock: Number(body.stock) || 0,
      featured: 0,
      description: body.description || "",
      provider_id: pid,
      provider_name: providerName,
      image_url: body.image_url || img("prod-" + Date.now().toString(36))
    };
    db.products.push(product);
    saveDb();
    return json({ product: product });
  });

  route("PUT", /^\/api\/provider\/products\/([^/]+)\/stock$/, function (ctx) {
    var product = findProduct(ctx.match[1]);
    if (!product) return err(404, "Product not found");
    var qty = Number(ctx.body && ctx.body.quantity) || 0;
    var oldStock = product.stock;
    product.stock = Math.max(0, oldStock + qty);
    db.restocks.unshift({
      image_url: product.image_url, product_name: product.name, sku: product.sku,
      category: product.category, quantity_changed: qty,
      old_stock: oldStock, new_stock: product.stock,
      reason: (ctx.body && ctx.body.reason) || "",
      timestamp: new Date().toISOString()
    });
    saveDb();
    return json({ result: { old_stock: oldStock, new_stock: product.stock } });
  });

  route("PUT", /^\/api\/provider\/products\/([^/]+)$/, function (ctx) {
    var product = findProduct(ctx.match[1]);
    if (!product) return err(404, "Product not found");
    var body = ctx.body || {};
    ["name", "sku", "category", "image_url", "description"].forEach(function (k) {
      if (body[k] !== undefined && body[k] !== "") product[k] = body[k];
    });
    if (body.price !== undefined) product.price = Number(body.price) || 0;
    if (body.stock !== undefined) product.stock = Number(body.stock) || 0;
    saveDb();
    return json({ product: product });
  });

  route("DELETE", /^\/api\/provider\/products\/([^/]+)$/, function (ctx) {
    db.products = db.products.filter(function (p) { return p._id !== ctx.match[1]; });
    saveDb();
    return json({ status: "deleted" });
  });

  route("GET", /^\/api\/provider\/dashboard$/, function (ctx) {
    var pid = providerIdFor(ctx.user);
    var myProducts = db.products.filter(function (p) { return p.provider_id === pid; });
    var totalStock = 0;
    myProducts.forEach(function (p) { totalStock += p.stock; });

    var revenue = 0;
    var orderCount = 0;
    var ordersToday = 0;
    var salesByProduct = {};
    var today = new Date().toDateString();
    db.orders.forEach(function (o) {
      if (o.status === "cancelled" || o.payment_status !== "paid") return;
      if (!matchesDateFilter(o.created_at, ctx.params)) return;
      var mine = o.items.filter(function (it) { return it.provider_id === pid; });
      if (!mine.length) return;
      orderCount += 1;
      if (new Date(o.created_at).toDateString() === today) ordersToday += 1;
      mine.forEach(function (it) {
        revenue += it.unit_price * it.quantity;
        salesByProduct[it.name] = (salesByProduct[it.name] || 0) + it.quantity;
      });
    });

    return json({
      total_products: myProducts.length,
      total_categories: uniqueList(myProducts.map(function (p) { return p.category; })).length,
      total_stock: totalStock,
      total_revenue: round2(revenue),
      total_orders: orderCount,
      orders_today: ordersToday,
      sales_by_product: Object.keys(salesByProduct).map(function (name) {
        return { name: name, sales: salesByProduct[name] };
      }),
      low_stock_items: myProducts.filter(function (p) { return p.stock <= 5; })
    });
  });

  route("GET", /^\/api\/provider\/product-categories$/, function () {
    return json({ categories: ["Footwear", "Apparel", "Accessories", "Electronics", "Other"] });
  });

  route("GET", /^\/api\/provider\/settings$/, function () {
    return json({ settings: db.provider_settings });
  });

  route("PUT", /^\/api\/provider\/settings$/, function (ctx) {
    Object.keys(ctx.body || {}).forEach(function (k) { db.provider_settings[k] = ctx.body[k]; });
    saveDb();
    return json({ settings: db.provider_settings });
  });

  route("GET", /^\/api\/provider\/staff$/, function () {
    return json({ staff: db.staff.slice() });
  });

  route("POST", /^\/api\/provider\/staff$/, function (ctx) {
    var body = ctx.body || {};
    db.staff.push({
      id: nextId("staff"),
      name: body.username || "New Staff",
      email: body.email || "",
      phone: body.phone || "",
      permission_level: Number(body.permission_level) || 4,
      is_active: body.is_active !== false
    });
    saveDb();
    return json({ status: "created" });
  });

  route("PUT", /^\/api\/provider\/staff\/([^/]+)$/, function (ctx) {
    var staff = null;
    db.staff.forEach(function (s) { if (s.id === ctx.match[1]) { staff = s; } });
    if (!staff) return err(404, "Staff not found");
    var body = ctx.body || {};
    if (body.username !== undefined) staff.name = body.username;
    if (body.email !== undefined) staff.email = body.email;
    if (body.phone !== undefined) staff.phone = body.phone;
    if (body.permission_level !== undefined) staff.permission_level = Number(body.permission_level) || staff.permission_level;
    if (body.is_active !== undefined) staff.is_active = !!body.is_active;
    saveDb();
    return json({ status: "updated" });
  });

  route("GET", /^\/api\/provider\/sales-history$/, function (ctx) {
    var pid = providerIdFor(ctx.user);
    var list = db.orders.filter(function (o) {
      if (!o.items.some(function (it) { return it.provider_id === pid; })) return false;
      if (!matchesDateFilter(o.created_at, ctx.params)) return false;
      var category = ctx.params.get("category");
      if (category && !o.items.some(function (it) { return it.category === category; })) return false;
      return true;
    });
    list.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    var page = paginate(list.map(toSalesEntry), ctx.params);
    return json({ history: page.history, pagination: page.pagination });
  });

  route("POST", /^\/api\/provider\/orders\/([^/]+)\/actions$/, function (ctx) {
    var order = findOrder(ctx.match[1]);
    if (!order) return err(404, "Order not found");
    var action = ctx.body && ctx.body.action;
    var inventoryRestored = false;
    var deleted = false;

    if (action === "delete") {
      db.orders = db.orders.filter(function (o) { return o.order_id !== order.order_id; });
      deleted = true;
    } else if (action === "cancel") {
      order.status = "cancelled";
      order.fulfillment_status = "cancelled_by_provider";
      restoreStock(order);
      inventoryRestored = true;
    } else if (action === "return_match") {
      order.fulfillment_status = "match_returned";
      restoreStock(order);
      inventoryRestored = true;
    } else if (action === "return_product") {
      order.fulfillment_status = "product_returned";
      restoreStock(order);
      inventoryRestored = true;
    } else if (action === "refund_money") {
      order.payment_status = "refunded";
      order.payment_history.push({
        channel: "qrcode", status: "refunded", amount: order.pricing.grand_total,
        timestamp: new Date().toISOString(), note: "Refund issued"
      });
    } else if (action === "mark_paid") {
      order.payment_status = "paid";
      order.status_label = "paid";
      order.receipt_number = order.invoice_number.replace("INV", "RCPT");
      order.payment_history.push({
        channel: "qrcode", status: "paid", amount: order.pricing.grand_total,
        timestamp: new Date().toISOString(), note: "Marked paid by provider"
      });
    } else {
      return err(400, "Unknown action: " + action);
    }
    saveDb();
    return json({ inventory_restored: inventoryRestored, deleted: deleted });
  });

  route("PUT", /^\/api\/provider\/orders\/([^/]+)\/full-tax-invoice-status$/, function (ctx) {
    var order = findOrder(ctx.match[1]);
    if (!order) return err(404, "Order not found");
    order.full_tax_invoice_status = (ctx.body && ctx.body.status) || "not_issued";
    saveDb();
    return json({ status: order.full_tax_invoice_status });
  });

  route("GET", /^\/api\/provider\/restock-history$/, function (ctx) {
    var list = db.restocks.filter(function (r) {
      if (!matchesDateFilter(r.timestamp, ctx.params)) return false;
      var category = ctx.params.get("category");
      if (category && r.category !== category) return false;
      return true;
    });
    var page = paginate(list, ctx.params);
    return json({ history: page.history, pagination: page.pagination });
  });

  /* ------------------------------------------------------------------ */
  /* fetch patch                                                         */
  /* ------------------------------------------------------------------ */

  var realFetch = window.fetch.bind(window);

  function headersToObject(init, input) {
    var out = {};
    var source = (init && init.headers) || (input && input.headers);
    if (!source) return out;
    if (typeof Headers !== "undefined" && source instanceof Headers) {
      source.forEach(function (value, key) { out[key] = value; });
    } else if (Array.isArray(source)) {
      source.forEach(function (pair) { out[pair[0]] = pair[1]; });
    } else {
      Object.keys(source).forEach(function (k) { out[k] = source[k]; });
    }
    return out;
  }

  window.fetch = function (input, init) {
    var url;
    try {
      url = new URL(typeof input === "string" ? input : input.url, window.location.href);
    } catch (e) {
      return realFetch(input, init);
    }
    if (url.pathname.indexOf("/api/") !== 0) {
      return realFetch(input, init);
    }

    loadDb();

    var method = ((init && init.method) || (typeof input === "object" && input.method) || "GET").toUpperCase();
    var headers = headersToObject(init, typeof input === "object" ? input : null);
    var body = null;
    if (init && typeof init.body === "string") {
      try { body = JSON.parse(init.body); } catch (e) { body = null; }
    }

    var ctx = {
      method: method,
      path: url.pathname,
      params: url.searchParams,
      headers: headers,
      body: body,
      user: currentUser(headers),
      match: null
    };

    var result = null;
    for (var i = 0; i < routes.length; i += 1) {
      var r = routes[i];
      if (r.method !== method) continue;
      var m = url.pathname.match(r.pattern);
      if (!m) continue;
      ctx.match = m;
      try {
        result = r.handler(ctx);
      } catch (e) {
        result = { status: 500, body: { detail: "Mock API error: " + e.message } };
      }
      break;
    }
    if (!result) {
      result = { status: 404, body: { detail: "Mock API: no handler for " + method + " " + url.pathname } };
    }

    return new Promise(function (resolve) {
      setTimeout(function () {
        resolve(new Response(JSON.stringify(result.body), {
          status: result.status,
          headers: { "Content-Type": "application/json" }
        }));
      }, LATENCY_MS);
    });
  };

  /* ------------------------------------------------------------------ */
  /* Public helpers (used by the demo hub page)                          */
  /* ------------------------------------------------------------------ */

  loadDb();

  window.MockApi = {
    loginAs: function (role) {
      var user = null;
      db.users.forEach(function (u) { if (u.role === role) { user = u; } });
      if (!user) return;
      localStorage.setItem("auth_token", makeToken(user));
      localStorage.setItem("user_id", "uid_" + user.email);
    },
    reset: function () {
      localStorage.removeItem(DB_KEY);
      db = buildSeed();
      saveDb();
    }
  };
})();
