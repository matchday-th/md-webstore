import initSqlJs from "sql.js";
import wasmUrl from "sql.js/dist/sql-wasm.wasm?url";
import { defaultOrders, defaultProducts, defaultProfiles } from "../seed/defaultData";

const STORAGE_KEY = "ecommerce-flow-studio.db";
const STORAGE_VERSION_KEY = "ecommerce-flow-studio.db.version";
const STORAGE_VERSION = "adidas-seed-v1";

function encodeBuffer(buffer) {
  let binary = "";
  buffer.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary);
}

function decodeBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function rowsFromResult(result) {
  if (!result.length) {
    return [];
  }

  const [{ columns, values }] = result;
  return values.map((valueSet) => {
    const row = {};
    columns.forEach((column, index) => {
      row[column] = valueSet[index];
    });
    return row;
  });
}

class SQLiteService {
  constructor() {
    this.SQL = null;
    this.db = null;
  }

  async init() {
    if (this.db) {
      return;
    }

    this.SQL = await initSqlJs({
      locateFile: () => wasmUrl
    });

    const saved = localStorage.getItem(STORAGE_KEY);
    const savedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
    const shouldReset = savedVersion !== STORAGE_VERSION;

    if (shouldReset) {
      localStorage.removeItem(STORAGE_KEY);
    }

    const effectiveSaved = shouldReset ? null : saved;
    this.db = effectiveSaved ? new this.SQL.Database(decodeBuffer(effectiveSaved)) : new this.SQL.Database();
    this.createSchema();

    if (!effectiveSaved) {
      this.seedDefaults();
      this.persist();
    }
  }

  createSchema() {
    this.db.run(`
      CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        featured INTEGER NOT NULL DEFAULT 0,
        description TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        user_name TEXT NOT NULL,
        status TEXT NOT NULL,
        total REAL NOT NULL,
        items_json TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
    `);
  }

  now() {
    return new Date().toISOString();
  }

  seedDefaults() {
    defaultProfiles.forEach((profile) => {
      const stamp = this.now();
      this.db.run(
        `INSERT INTO profiles (name, email, role, phone, address, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [profile.name, profile.email, profile.role, profile.phone, profile.address, stamp, stamp]
      );
    });

    defaultProducts.forEach((product) => {
      const stamp = this.now();
      this.db.run(
        `INSERT INTO products (name, sku, category, price, stock, featured, description, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          product.name,
          product.sku,
          product.category,
          product.price,
          product.stock,
          product.featured,
          product.description,
          stamp,
          stamp
        ]
      );
    });

    defaultOrders.forEach((order) => {
      const stamp = this.now();
      this.db.run(
        `INSERT INTO orders (profile_id, user_name, status, total, items_json, notes, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          order.profile_id,
          order.user_name,
          order.status,
          order.total,
          order.items_json,
          order.notes,
          stamp,
          stamp
        ]
      );
    });
  }

  persist() {
    const data = this.db.export();
    localStorage.setItem(STORAGE_KEY, encodeBuffer(data));
    localStorage.setItem(STORAGE_VERSION_KEY, STORAGE_VERSION);
  }

  select(sql, params = []) {
    return rowsFromResult(this.db.exec(sql, params));
  }

  run(sql, params = []) {
    this.db.run(sql, params);
    this.persist();
  }

  getProfiles() {
    return this.select(`SELECT * FROM profiles ORDER BY id DESC`);
  }

  saveProfile(profile) {
    const stamp = this.now();

    if (profile.id) {
      this.run(
        `UPDATE profiles
         SET name = ?, email = ?, role = ?, phone = ?, address = ?, updated_at = ?
         WHERE id = ?`,
        [profile.name, profile.email, profile.role, profile.phone, profile.address, stamp, profile.id]
      );
      return profile.id;
    }

    this.run(
      `INSERT INTO profiles (name, email, role, phone, address, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [profile.name, profile.email, profile.role, profile.phone, profile.address, stamp, stamp]
    );

    return this.select(`SELECT last_insert_rowid() AS id`)[0].id;
  }

  deleteProfile(id) {
    this.run(`DELETE FROM profiles WHERE id = ?`, [id]);
  }

  getProducts() {
    return this.select(`SELECT * FROM products ORDER BY featured DESC, id DESC`);
  }

  saveProduct(product) {
    const stamp = this.now();

    if (product.id) {
      this.run(
        `UPDATE products
         SET name = ?, sku = ?, category = ?, price = ?, stock = ?, featured = ?, description = ?, updated_at = ?
         WHERE id = ?`,
        [
          product.name,
          product.sku,
          product.category,
          product.price,
          product.stock,
          product.featured ? 1 : 0,
          product.description,
          stamp,
          product.id
        ]
      );
      return product.id;
    }

    this.run(
      `INSERT INTO products (name, sku, category, price, stock, featured, description, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        product.name,
        product.sku,
        product.category,
        product.price,
        product.stock,
        product.featured ? 1 : 0,
        product.description,
        stamp,
        stamp
      ]
    );

    return this.select(`SELECT last_insert_rowid() AS id`)[0].id;
  }

  deleteProduct(id) {
    this.run(`DELETE FROM products WHERE id = ?`, [id]);
  }

  getOrders() {
    return this.select(`SELECT * FROM orders ORDER BY id DESC`);
  }

  saveOrder(order) {
    const stamp = this.now();

    if (order.id) {
      this.run(
        `UPDATE orders
         SET profile_id = ?, user_name = ?, status = ?, total = ?, items_json = ?, notes = ?, updated_at = ?
         WHERE id = ?`,
        [
          order.profile_id,
          order.user_name,
          order.status,
          order.total,
          order.items_json,
          order.notes,
          stamp,
          order.id
        ]
      );
      return order.id;
    }

    this.run(
      `INSERT INTO orders (profile_id, user_name, status, total, items_json, notes, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        order.profile_id,
        order.user_name,
        order.status,
        order.total,
        order.items_json,
        order.notes,
        stamp,
        stamp
      ]
    );

    return this.select(`SELECT last_insert_rowid() AS id`)[0].id;
  }

  deleteOrder(id) {
    this.run(`DELETE FROM orders WHERE id = ?`, [id]);
  }
}

export const sqliteService = new SQLiteService();
