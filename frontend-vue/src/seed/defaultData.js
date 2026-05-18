export const defaultProfiles = [
  {
    name: "Avery Collins",
    email: "avery@studio.dev",
    role: "Admin",
    phone: "+1 202 555 0124",
    address: "42 Mercer Street, New York"
  },
  {
    name: "Mika Tan",
    email: "mika@studio.dev",
    role: "Buyer",
    phone: "+1 202 555 0155",
    address: "88 Spring Road, Seattle"
  }
];

export const defaultProducts = [
  {
    name: "Men's Street Footwear",
    sku: "ADI-MSF-001",
    category: "Footwear",
    price: 44,
    stock: 593320,
    featured: 1,
    description: "Aggregated from Adidas US Sales Datasets. Total sales: $208.8M."
  },
  {
    name: "Men's Athletic Footwear",
    sku: "ADI-MAF-002",
    category: "Footwear",
    price: 44,
    stock: 435526,
    featured: 1,
    description: "Aggregated from Adidas US Sales Datasets. Total sales: $153.7M."
  },
  {
    name: "Women's Street Footwear",
    sku: "ADI-WSF-003",
    category: "Footwear",
    price: 40,
    stock: 392269,
    featured: 1,
    description: "Aggregated from Adidas US Sales Datasets. Total sales: $128.0M."
  },
  {
    name: "Women's Athletic Footwear",
    sku: "ADI-WAF-004",
    category: "Footwear",
    price: 41,
    stock: 317236,
    featured: 0,
    description: "Aggregated from Adidas US Sales Datasets. Total sales: $106.6M."
  },
  {
    name: "Women's Apparel",
    sku: "ADI-WAP-005",
    category: "Apparel",
    price: 52,
    stock: 433827,
    featured: 0,
    description: "Aggregated from Adidas US Sales Datasets. Total sales: $179.0M."
  },
  {
    name: "Men's Apparel",
    sku: "ADI-MAP-006",
    category: "Apparel",
    price: 50,
    stock: 306683,
    featured: 0,
    description: "Aggregated from Adidas US Sales Datasets. Total sales: $123.7M."
  }
];

export const defaultOrders = [
  {
    profile_id: 2,
    user_name: "Mika Tan",
    status: "Packed",
    total: 128,
    items_json: JSON.stringify([
      { productId: 1, name: "Men's Street Footwear", quantity: 1, price: 44 },
      { productId: 2, name: "Men's Athletic Footwear", quantity: 1, price: 44 },
      { productId: 3, name: "Women's Street Footwear", quantity: 1, price: 40 }
    ]),
    notes: "Seeded from Adidas US Sales Datasets aggregate catalog"
  }
];
