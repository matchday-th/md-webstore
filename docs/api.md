---
layout: default
title: API Documentation
---

# 🔌 API Documentation

Complete API reference for the Ecommerce System

---

## Authentication Endpoints

### Register User
```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name"
}
```

**Response:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "name": "User Name",
  "token": "jwt_token"
}
```

---

### Login
```
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user_id": "user_id"
}
```

---

## Product Endpoints

### Get All Products
```
GET /products?skip=0&limit=10
Authorization: Bearer {token}
```

**Response:**
```json
{
  "items": [
    {
      "id": "product_id",
      "name": "Product Name",
      "price": 99.99,
      "stock": 50,
      "description": "Product description"
    }
  ],
  "total": 100
}
```

---

### Create Product (Provider Only)
```
POST /products
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Product Name",
  "price": 99.99,
  "stock": 100,
  "description": "Description",
  "category": "Category"
}
```

---

## Order Endpoints

### Create Order
```
POST /orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "product_id": "product_id",
  "quantity": 1,
  "delivery_address": "Street Address"
}
```

**Headers (Idempotency):**
```
Idempotency-Key: unique-request-id
```

---

### Get Order History
```
GET /orders
Authorization: Bearer {token}
```

---

## Dashboard Endpoints

### Admin Dashboard Stats
```
GET /dashboard/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_products": 150,
  "total_stock": 5000,
  "revenue": 125000,
  "total_orders": 320,
  "pending_orders": 15
}
```

---

## Rate Limiting

- **Standard**: 60 requests/minute
- **Purchase**: 5 requests/minute (same product)
- **Admin**: 200 requests/minute

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

---

## Security Features

✅ **Duplicate Prevention**: Idempotency keys prevent duplicate orders  
✅ **Stock Validation**: Real-time stock checking  
✅ **JWT Authentication**: Secure token-based auth  
✅ **Rate Limiting**: DDoS protection  
✅ **Data Encryption**: bcrypt password hashing  

---

## Testing with cURL

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass123","name":"Test"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass123"}'

# Get Products
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/products

# Create Order (with Idempotency)
curl -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Idempotency-Key: order-123" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"123","quantity":1}'
```

---

## Interactive API Docs

Visit `/docs` endpoint on your running server for Swagger UI:
```
http://localhost:8000/docs
```

---

[← Back to Home](/)
