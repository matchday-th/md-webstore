"""Database Connection and Operations"""
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import certifi
import uuid
import os

class Database:
    client = None
    db = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    db.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where()
    )
    db.db = db.client[settings.DATABASE_NAME]
    try:
        await db.client.admin.command("ping")
        print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
    except Exception as exc:
        using_local_default = (
            settings.MONGODB_URL == "mongodb://localhost:27017"
            and not any(os.getenv(name) for name in ("MONGODB_URL", "MONGODB_URI", "MONGO_URL", "MONGO_URI"))
        )
        if using_local_default:
            print("⚠️ MongoDB env is not set. Render cannot use localhost:27017.")
        print(f"❌ MongoDB connection failed: {exc}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        print("❌ Disconnected from MongoDB")

# ===================== DATABASE OPERATIONS =====================

class UserDB:
    @staticmethod
    async def create_user(user_data: dict):
        """Create new user"""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        result = await db.db["users"].insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_user_by_email(email: str):
        """Get user by email"""
        return await db.db["users"].find_one({"email": email})
    
    @staticmethod
    async def get_user_by_id(user_id: str):
        """Get user by ID"""
        return await db.db["users"].find_one({"_id": ObjectId(user_id)})

async def get_provider_scopes(provider_id: str):
    """Resolve legacy provider ids that should be visible to this provider account."""
    scopes = [provider_id]
    user = await UserDB.get_user_by_id(provider_id)

    if user and user.get("role") == "provider":
        legacy_provider_emails = {
            "provider@ecommerce.local",
            "provider@example.com",
        }
        if user.get("email") in legacy_provider_emails:
            scopes.append("provider_001")

        child_shops = await db.db["users"].find({
            "role": "provider",
            "owner_provider_id": provider_id,
            "is_active": True,
        }).to_list(None)
        scopes.extend(str(shop.get("_id")) for shop in child_shops if shop.get("_id"))

    return list(dict.fromkeys(scopes))

class ProductDB:
    @staticmethod
    async def update_product(product_id: str, provider_id: str, update_data: dict):
        provider_scopes = await get_provider_scopes(provider_id)
        clean_data = {k: v for k, v in update_data.items() if v is not None}
        clean_data["updated_at"] = datetime.utcnow()
        existing_product = await db.db["products"].find_one(
            {"_id": ObjectId(product_id), "provider_id": {"$in": provider_scopes}}
        )

        if not existing_product:
            return False

        result = await db.db["products"].update_one(
            {"_id": ObjectId(product_id), "provider_id": {"$in": provider_scopes}},
            {"$set": clean_data}
        )

        if "stock" in clean_data and clean_data["stock"] != existing_product.get("stock", 0):
            await InventoryDB.log_stock_change(
                product_id=product_id,
                provider_id=existing_product.get("provider_id"),
                old_stock=existing_product.get("stock", 0),
                new_stock=clean_data["stock"],
                quantity_changed=clean_data["stock"] - existing_product.get("stock", 0),
                reason="Manual edit from provider panel"
            )

        return result.matched_count > 0

    @staticmethod
    async def delete_product(product_id: str, provider_id: str):
        provider_scopes = await get_provider_scopes(provider_id)
        result = await db.db["products"].delete_one(
            {"_id": ObjectId(product_id), "provider_id": {"$in": provider_scopes}}
        )
        return result.deleted_count > 0
    @staticmethod
    async def create_product(product_data: dict):
        """Create new product"""
        product_data["created_at"] = datetime.utcnow()
        product_data["updated_at"] = datetime.utcnow()
        product_data["stock_history"] = []
        result = await db.db["products"].insert_one(product_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_product_by_id(product_id: str):
        """Get product by ID"""
        return await db.db["products"].find_one({"_id": ObjectId(product_id)})
    
    @staticmethod
    async def get_product_by_sku(sku: str):
        """Get product by SKU"""
        return await db.db["products"].find_one({"sku": sku})
    
    @staticmethod
    async def get_products_by_provider(provider_id: str):
        """Get all products by provider"""
        provider_scopes = await get_provider_scopes(provider_id)
        products = await db.db["products"].find({"provider_id": {"$in": provider_scopes}}).to_list(None)
        for product in products:
            product["_id"] = str(product["_id"])
        return products
    
    @staticmethod
    async def update_product_stock(
        product_id: str,
        quantity_change: int,
        reason: str,
        provider_id: Optional[str] = None
    ):
        """
        Update product stock with logging
        quantity_change: positive (add), negative (remove)
        """
        query = {"_id": ObjectId(product_id)}
        if provider_id is not None:
            provider_scopes = await get_provider_scopes(provider_id)
            query["provider_id"] = {"$in": provider_scopes}

        product = await db.db["products"].find_one(query)
        
        if not product:
            return None
        
        old_stock = product["stock"]
        new_stock = old_stock + quantity_change
        
        if new_stock < 0:
            return {"error": "Stock cannot be negative", "code": "INSUFFICIENT_STOCK"}
        
        # Update stock
        updated = await db.db["products"].update_one(
            query,
            {"$set": {"stock": new_stock, "updated_at": datetime.utcnow()}}
        )
        
        # Log to inventory history
        await InventoryDB.log_stock_change(
            product_id=product_id,
            provider_id=product.get("provider_id"),
            old_stock=old_stock,
            new_stock=new_stock,
            quantity_changed=quantity_change,
            reason=reason
        )
        
        return {"old_stock": old_stock, "new_stock": new_stock, "success": True}

class OrderDB:
    @staticmethod
    async def create_order(order_data: dict):
        """Create new order with idempotency key"""
        
        # Generate idempotency key if not exists
        if not order_data.get("idempotency_key"):
            order_data["idempotency_key"] = str(uuid.uuid4())
        
        order_data["created_at"] = datetime.utcnow()
        order_data["updated_at"] = datetime.utcnow()
        
        result = await db.db["orders"].insert_one(order_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_order_by_id(order_id: str):
        """Get order by ID"""
        return await db.db["orders"].find_one({"_id": ObjectId(order_id)})
    
    @staticmethod
    async def get_orders_by_user(user_id: str):
        """Get all orders by user"""
        return await db.db["orders"].find({"user_id": user_id}).to_list(None)
    
    @staticmethod
    async def get_orders_by_provider(provider_id: str):
        """Get all orders for a provider"""
        return await db.db["orders"].find({"provider_id": provider_id}).to_list(None)
    
    @staticmethod
    async def update_order_status(order_id: str, status: str):
        """Update order status"""
        await db.db["orders"].update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )

class TransactionLogDB:
    @staticmethod
    async def log_transaction(
        user_id: str,
        product_id: str,
        quantity: int,
        idempotency_key: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log transaction for duplicate prevention"""
        log_data = {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.utcnow(),
            "status": status,
            "error_message": error_message
        }
        
        await db.db["transaction_logs"].insert_one(log_data)
    
    @staticmethod
    async def check_duplicate_purchase(idempotency_key: str, user_id: str):
        """
        Check if this purchase was already processed
        Returns: existing transaction if found, None otherwise
        """
        return await db.db["transaction_logs"].find_one({
            "idempotency_key": idempotency_key,
            "user_id": user_id,
            "status": "success"
        })
    
    @staticmethod
    async def get_user_purchases_last_minute(user_id: str):
        """Get user's purchases in the last minute (rate limiting check)"""
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        return await db.db["transaction_logs"].find({
            "user_id": user_id,
            "timestamp": {"$gte": one_minute_ago},
            "status": "success"
        }).to_list(None)

class InventoryDB:
    @staticmethod
    async def log_stock_change(
        product_id: str,
        provider_id: str,
        old_stock: int,
        new_stock: int,
        quantity_changed: int,
        reason: str,
        reference_id: Optional[str] = None
    ):
        """Log inventory changes"""
        log = {
            "product_id": product_id,
            "provider_id": provider_id,
            "action": "add" if quantity_changed > 0 else "remove",
            "quantity_changed": quantity_changed,
            "old_stock": old_stock,
            "new_stock": new_stock,
            "reference_id": reference_id,
            "timestamp": datetime.utcnow(),
            "reason": reason
        }
        
        await db.db["inventory_logs"].insert_one(log)
    
    @staticmethod
    async def get_inventory_history(product_id: str, days: int = 30):
        """Get inventory history for a product"""
        date_threshold = datetime.utcnow() - timedelta(days=days)
        return await db.db["inventory_logs"].find({
            "product_id": product_id,
            "timestamp": {"$gte": date_threshold}
        }).to_list(None)

class DashboardDB:
    @staticmethod
    async def get_provider_dashboard(provider_id: str):
        """Get dashboard summary for provider"""
        provider_scopes = await get_provider_scopes(provider_id)
        
        # Total products and stock
        products = await db.db["products"].find(
            {"provider_id": {"$in": provider_scopes}}
        ).to_list(None)
        
        total_products = len(products)
        total_stock = sum(p.get("stock", 0) for p in products)
        total_categories = len({
            (product.get("category") or "").strip()
            for product in products
            if (product.get("category") or "").strip()
        })
        
        # Low stock items (< 5)
        low_stock = [
            {
                "_id": str(product.get("_id")),
                "name": product.get("name"),
                "sku": product.get("sku"),
                "stock": product.get("stock", 0),
                "category": product.get("category"),
                "price": product.get("price", 0),
                "provider_id": product.get("provider_id"),
            }
            for product in products
            if product.get("stock", 0) < 5
        ]
        
        product_lookup = {str(product.get("_id")): product for product in products}
        product_ids = set(product_lookup.keys())

        # Total revenue and orders
        orders = await db.db["orders"].find({
            "$or": [
                {"provider_id": {"$in": provider_scopes}},
                {"provider_ids": {"$in": provider_scopes}},
            ],
            "status": {"$ne": "cancelled"}
        }).to_list(None)

        total_orders = len(orders)
        total_revenue = 0
        for order in orders:
            for item in order.get("items", []):
                if str(item.get("product_id")) not in product_ids:
                    continue
                total_revenue += float(item.get("price_at_purchase", 0) or 0) * int(item.get("quantity", 0) or 0)
        total_revenue = round(total_revenue, 2)
        
        # Orders today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        orders_today = len([o for o in orders if o.get("created_at", datetime.min) >= today_start])
        
        # Sales by product
        sales_by_product = []
        for product in products:
            product_sales = sum(
                sum(item.get("quantity", 0) for item in o.get("items", [])
                    if item.get("product_id") == str(product.get("_id")))
                for o in orders
            )
            sales_by_product.append({
                "product": product.get("name"),
                "sales": product_sales,
                "revenue": product_sales * product.get("price", 0)
            })
        
        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "total_categories": total_categories,
            "low_stock_items": low_stock,
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "orders_today": orders_today,
            "sales_by_product": sales_by_product
        }
