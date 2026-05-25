"""Main FastAPI Application"""
from fastapi import FastAPI, HTTPException, status, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uvicorn
import os

from .config import settings
from .database import (
    connect_to_mongo, close_mongo_connection, db,
    UserDB, ProductDB, OrderDB, TransactionLogDB, InventoryDB, DashboardDB,
    get_provider_scopes
)
from .security import (
    create_access_token, get_current_user, duplicate_prevention,
    db_rate_limiter, validate_stock_availability, idempotency_handler
)
from .models import (
    UserCreate, User, ProductCreate, Product, ProductUpdate, OrderCreate, Order, LoginRequest,
    UserRole, OrderStatus, PaymentStatus, RestockRequest, PaymentRequest, SlipUploadRequest, SlipDecisionRequest,
    ProviderShopCreate, ProviderSettingsPayload, ProviderStaffCreatePayload, ProviderStaffUpdatePayload,
    ProviderFullTaxInvoiceStatusPayload
)
from .data_loader import load_excel_data, seed_database
from typing import Optional, List
from bson import ObjectId
import uuid
import bcrypt

VAT_RATE = 0.07
TAX_LABEL = "VAT"
DISCOUNT_RULES = {
    "SAVE10": 0.10,
    "SAVE15": 0.15,
    "VIP20": 0.20,
}

def round_money(value: float) -> float:
    return round(value + 1e-9, 2)

def resolve_discount_rate(subtotal: float, discount_code: Optional[str]) -> tuple[Optional[str], float]:
    normalized_code = (discount_code or "").strip().upper() or None
    if normalized_code and normalized_code in DISCOUNT_RULES:
        return normalized_code, DISCOUNT_RULES[normalized_code]
    if subtotal >= 1000:
        return normalized_code, 0.12
    if subtotal >= 500:
        return normalized_code, 0.07
    if subtotal >= 200:
        return normalized_code, 0.03
    return normalized_code, 0.0

def calculate_order_pricing(items: List[dict], discount_code: Optional[str] = None) -> dict:
    subtotal = round_money(sum(item["quantity"] * item["price_at_purchase"] for item in items))
    normalized_code, discount_rate = resolve_discount_rate(subtotal, discount_code)
    discount_amount = round_money(subtotal * discount_rate)
    grand_total = round_money(max(subtotal - discount_amount, 0))
    taxable_amount = round_money(grand_total / (1 + VAT_RATE)) if grand_total else 0
    tax_amount = round_money(grand_total - taxable_amount)
    commission_amount = 0.0
    provider_net_amount = grand_total

    return {
        "currency": "USD",
        "subtotal": subtotal,
        "discount_code": normalized_code,
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "taxable_amount": taxable_amount,
        "commission_rate": 0,
        "commission_amount": commission_amount,
        "tax_label": TAX_LABEL,
        "tax_rate": VAT_RATE,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "provider_net_amount": provider_net_amount,
        "platform_fee_amount": 0,
    }

async def build_invoice_metadata() -> dict:
    issued_at = datetime.utcnow()
    year_part = issued_at.strftime("%y")
    month_part = issued_at.strftime("%m")
    prefix = f"INV{year_part}{month_part}"
    sequence = 1

    latest_order = await db.db["orders"].find_one(
        {"billing.invoice_number": {"$regex": f"^{prefix}\\d{{5}}$"}},
        sort=[("billing.invoice_number", -1)]
    )
    if latest_order:
        latest_invoice = str((latest_order.get("billing") or {}).get("invoice_number") or "")
        latest_seq = latest_invoice[-5:]
        if latest_seq.isdigit():
            sequence = int(latest_seq) + 1

    return {
        "invoice_number": f"{prefix}{str(sequence).zfill(5)}",
        "issued_at": issued_at,
        "currency": "USD",
    }


def normalize_payment_method(method: Optional[str]) -> str:
    raw = str(method or "").strip().lower()
    if raw in {"credit_card", "card", "บัตรเครดิต", "บัตรเคดิต"}:
        return "credit_card"
    return "qrcode"

class AdminProfilePayload(BaseModel):
    name: str
    email: str
    role: str = "user"
    phone: Optional[str] = ""
    address: Optional[str] = ""

class AdminProductPayload(BaseModel):
    name: str
    sku: str
    category: str
    price: float
    stock: int = 0
    featured: int = 1
    description: Optional[str] = ""
    provider_id: Optional[str] = None

class AdminOrderItemPayload(BaseModel):
    productId: str
    name: Optional[str] = ""
    quantity: int = Field(gt=0)
    price: float = Field(ge=0)

class AdminOrderPayload(BaseModel):
    profile_id: Optional[str] = None
    user_name: str
    status: str = "Pending"
    total: float = Field(ge=0)
    items: List[AdminOrderItemPayload] = Field(default_factory=list)
    notes: Optional[str] = ""

class AdminCheckoutPayload(BaseModel):
    profile_id: str
    items: List[AdminOrderItemPayload] = Field(default_factory=list)
    notes: Optional[str] = ""

def parse_object_id(value: str, field_name: str) -> ObjectId:
    try:
        return ObjectId(str(value))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}"
        )

def normalize_order_status(value: Optional[str]) -> str:
    normalized = (value or "pending").strip().lower()
    allowed_statuses = {"pending", "confirmed", "shipped", "completed", "cancelled", "packed"}
    return normalized if normalized in allowed_statuses else "pending"

class UserProfileUpdatePayload(BaseModel):
    gender: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=120)

def normalize_provider_staff_level(level: Optional[int]) -> int:
    try:
        normalized = int(level or 1)
    except (TypeError, ValueError):
        normalized = 1
    return max(1, min(4, normalized))


def build_provider_staff_permissions(level: Optional[int]) -> dict:
    normalized = normalize_provider_staff_level(level)
    return {
        "dashboard": True,
        "inventory": normalized >= 1,
        "sales_history": normalized >= 2,
        "restock_history": normalized >= 3,
        "settings": normalized >= 4,
    }


def serialize_profile(user: dict) -> dict:
    permission_level = normalize_provider_staff_level(user.get("provider_staff_level")) if user.get("provider_staff_owner_id") else 4
    return {
        "id": str(user["_id"]),
        "name": user.get("username") or user.get("name") or user.get("email", "").split("@")[0],
        "email": user.get("email", ""),
        "role": str(user.get("role", "user")).title(),
        "phone": user.get("phone", ""),
        "address": user.get("address", ""),
        "gender": user.get("gender", ""),
        "age": user.get("age"),
        "is_provider_staff": bool(user.get("provider_staff_owner_id")),
        "provider_staff_owner_id": user.get("provider_staff_owner_id"),
        "provider_staff_level": permission_level,
        "provider_staff_permissions": user.get("provider_staff_permissions") or build_provider_staff_permissions(permission_level),
        "provider_account_type": user.get("provider_account_type") or "provider",
    }


def serialize_provider_staff(user: dict) -> dict:
    level = normalize_provider_staff_level(user.get("provider_staff_level"))
    permissions = user.get("provider_staff_permissions") or build_provider_staff_permissions(level)
    return {
        "id": str(user["_id"]),
        "name": user.get("username") or user.get("email", "").split("@")[0],
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "permission_level": level,
        "permissions": permissions,
        "is_active": bool(user.get("is_active", True)),
    }


def serialize_provider_settings(user: dict) -> dict:
    settings = user.get("provider_settings") or {}
    return {
        "vat_registered": bool(settings.get("vat_registered", False)),
        "tax_id": settings.get("tax_id", "") or "",
        "tax_name": settings.get("tax_name", "") or "",
        "company_name": settings.get("company_name", "") or "",
        "address_mode": settings.get("address_mode", "registered") or "registered",
        "registered_address_line_1": settings.get("registered_address_line_1", "") or "",
        "registered_address_line_2": settings.get("registered_address_line_2", "") or "",
        "branch_address_line_1": settings.get("branch_address_line_1", "") or "",
        "branch_address_line_2": settings.get("branch_address_line_2", "") or "",
        "branch_number": settings.get("branch_number", "") or "",
        "custom_tax_address": settings.get("custom_tax_address", "") or "",
        "note": settings.get("note", "") or "",
    }

async def get_provider_access_context(current_user: str, required_permission: Optional[str] = None) -> dict:
    user = await UserDB.get_user_by_id(current_user)
    if not user or user.get("role") != "provider":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider access required"
        )

    owner_provider_id = str(user.get("provider_staff_owner_id") or current_user)
    permissions = user.get("provider_staff_permissions") or build_provider_staff_permissions(
        user.get("provider_staff_level") if user.get("provider_staff_owner_id") else 4
    )

    if required_permission and not permissions.get(required_permission, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for this page"
        )

    owner_user = await UserDB.get_user_by_id(owner_provider_id)
    if not owner_user or owner_user.get("role") != "provider":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider owner not found"
        )

    return {
        "user": user,
        "owner_user": owner_user,
        "owner_provider_id": owner_provider_id,
        "permissions": permissions,
        "is_staff": bool(user.get("provider_staff_owner_id")),
        "permission_level": normalize_provider_staff_level(
            user.get("provider_staff_level") if user.get("provider_staff_owner_id") else 4
        ),
    }


def serialize_product(product: dict) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product.get("name", ""),
        "sku": product.get("sku", ""),
        "category": product.get("category", ""),
        "price": float(product.get("price", 0) or 0),
        "stock": int(product.get("stock", 0) or 0),
        "featured": int(product.get("featured", 1) or 0),
        "description": product.get("description", "") or "",
        "image_url": product.get("image_url", "") or "",
        "provider_id": product.get("provider_id"),
        "provider_name": product.get("provider_name") or product.get("provider_id") or "",
    }


async def enrich_products_with_provider_names(products: List[dict]) -> List[dict]:
    provider_ids = {
        str(product.get("provider_id"))
        for product in products
        if product.get("provider_id")
    }
    provider_lookup = {}
    for provider_id in provider_ids:
        try:
            provider = await UserDB.get_user_by_id(provider_id)
        except Exception:
            provider = None
        if provider:
            provider_lookup[provider_id] = (
                provider.get("username")
                or provider.get("name")
                or provider.get("email", "").split("@")[0]
                or provider_id
            )
        else:
            provider_lookup[provider_id] = provider_id

    enriched = []
    for product in products:
        item = dict(product)
        provider_id = str(item.get("provider_id")) if item.get("provider_id") else None
        item["provider_id"] = provider_id
        item["provider_name"] = provider_lookup.get(provider_id, provider_id or "Unknown provider")
        if "_id" in item:
            item["_id"] = str(item["_id"])
        enriched.append(item)
    return enriched

def serialize_order(order: dict, user_lookup: dict, product_lookup: dict) -> dict:
    items = []
    for item in order.get("items", []):
        product_id = str(item.get("product_id", ""))
        product = product_lookup.get(product_id, {})
        provider_id = str(
            item.get("provider_id")
            or product.get("provider_id")
            or order.get("provider_id")
            or ""
        )
        items.append({
            "productId": product_id,
            "name": item.get("name") or product.get("name", "Unknown product"),
            "quantity": int(item.get("quantity", 0) or 0),
            "price": float(item.get("price_at_purchase", 0) or 0),
            "lineTotal": round(int(item.get("quantity", 0) or 0) * float(item.get("price_at_purchase", 0) or 0), 2),
            "providerId": provider_id or None,
            "providerName": (
                product.get("provider_name")
                or item.get("provider_name")
                or provider_id
                or "Unknown shop"
            ),
            "sku": product.get("sku", "") or "",
            "category": product.get("category", "") or "",
            "image_url": product.get("image_url", "") or "",
        })

    user_id = order.get("user_id")
    profile = user_lookup.get(str(user_id)) if user_id else None

    pricing = order.get("pricing") or {}
    billing = order.get("billing") or {}

    return {
        "id": str(order["_id"]),
        "profile_id": str(user_id) if user_id else None,
        "user_name": order.get("user_name") or (profile.get("name") if profile else "Unknown user"),
        "customer_email": (profile.get("email") if profile else "") or order.get("customer_email", "") or "",
        "status": normalize_order_status(order.get("status")).title(),
        "payment_status": str(order.get("payment_status", "") or "").lower(),
        "invoice_number": billing.get("invoice_number") or "",
        "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
        "updated_at": order.get("updated_at").isoformat() if order.get("updated_at") else None,
        "payment_method": order.get("payment_method", "") or "",
        "shipping_address": order.get("shipping_address", "") or "",
        "pricing": pricing,
        "total": float(order.get("total_amount", 0) or 0),
        "items": items,
        "notes": order.get("notes", "") or "",
    }


def derive_user_order_status(order: dict) -> str:
    payment_status = str(order.get("payment_status", "") or "").lower()
    status = str(order.get("status", "") or "").lower()
    fulfillment_status = str(order.get("fulfillment_status", "") or "").lower()

    if payment_status == PaymentStatus.PENDING_SLIP_VERIFICATION.value:
        return "awaiting_slip_verification"
    if fulfillment_status == "slip_rejected" or payment_status == PaymentStatus.FAILED.value:
        return "slip_rejected"
    if status == OrderStatus.SHIPPED.value:
        return "shipping"
    if status == OrderStatus.COMPLETED.value:
        return "completed"
    if payment_status == PaymentStatus.PAID.value:
        return "paid"
    return "pending_payment"


async def serialize_user_order(order: dict) -> dict:
    product_lookup = {}
    for item in order.get("items", []):
        product_id = str(item.get("product_id", ""))
        if not product_id:
            continue
        product = await ProductDB.get_product_by_id(product_id)
        if product:
            product_lookup[product_id] = product

    items = []
    for item in order.get("items", []):
        product_id = str(item.get("product_id", ""))
        product = product_lookup.get(product_id, {})
        provider_id = str(product.get("provider_id") or item.get("provider_id") or "")
        provider_name = (
            product.get("provider_name")
            or item.get("provider_name")
            or provider_id
            or "Unknown shop"
        )
        items.append({
            "product_id": product_id,
            "name": product.get("name") or item.get("name") or "Unknown product",
            "image_url": product.get("image_url", "") or "",
            "provider_id": provider_id or None,
            "provider_name": provider_name,
            "quantity": int(item.get("quantity", 0) or 0),
            "price_at_purchase": float(item.get("price_at_purchase", 0) or 0),
        })

    return {
        "order_id": str(order.get("_id")),
        "status": str(order.get("status", "")).lower(),
        "payment_status": str(order.get("payment_status", "")).lower(),
        "status_label": derive_user_order_status(order),
        "total_amount": float(order.get("total_amount", 0) or 0),
        "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
        "billing": order.get("billing") or {},
        "pricing": order.get("pricing") or {},
        "fulfillment_status": str(order.get("fulfillment_status", "")).lower(),
        "items": items,
    }


async def serialize_slip_review_order(order: dict) -> dict:
    product_lookup = {}
    for item in order.get("items", []):
        product_id = str(item.get("product_id", ""))
        if not product_id:
            continue
        product = await ProductDB.get_product_by_id(product_id)
        if product:
            product_lookup[product_id] = product

    items = []
    for item in order.get("items", []):
        product_id = str(item.get("product_id", ""))
        product = product_lookup.get(product_id, {})
        items.append({
            "product_id": product_id,
            "name": product.get("name") or item.get("name") or "Unknown product",
            "image_url": product.get("image_url", "") or "",
            "provider_id": product.get("provider_id"),
            "quantity": int(item.get("quantity", 0) or 0),
            "price_at_purchase": float(item.get("price_at_purchase", 0) or 0),
        })

    return {
        "order_id": str(order.get("_id")),
        "customer_name": order.get("customer_name") or order.get("user_name") or "",
        "customer_email": order.get("customer_email", "") or "",
        "payment_status": str(order.get("payment_status", "")).lower(),
        "status": str(order.get("status", "")).lower(),
        "fulfillment_status": str(order.get("fulfillment_status", "")).lower(),
        "slip_image": order.get("slip_image", "") or "",
        "slip_note": order.get("slip_note", "") or "",
        "slip_submitted_at": order.get("slip_submitted_at").isoformat() if order.get("slip_submitted_at") else None,
        "invoice_number": (order.get("billing") or {}).get("invoice_number"),
        "total_amount": float(order.get("total_amount", 0) or 0),
        "items": items,
    }


async def serialize_backoffice_order(order: dict, provider_scope_ids: Optional[set[str]] = None) -> dict:
    product_lookup = {}
    provider_lookup = {}
    user = None
    provider_item_map = order.get("provider_item_map") or {}

    user_id = str(order.get("user_id", "") or "")
    if user_id:
        user = await UserDB.get_user_by_id(user_id)

    for item in order.get("items", []):
        product_id = str(item.get("product_id", "") or "")
        if not product_id:
            continue
        product = await ProductDB.get_product_by_id(product_id)
        if product:
            product_lookup[product_id] = product
            provider_id = str(product.get("provider_id", "") or "")
            if provider_id and provider_id not in provider_lookup:
                provider_user = await UserDB.get_user_by_id(provider_id)
                if provider_user:
                    provider_lookup[provider_id] = (
                        provider_user.get("username")
                        or provider_user.get("email", "").split("@")[0]
                        or provider_id
                    )
                else:
                    provider_lookup[provider_id] = provider_id

    filtered_items = []
    provider_ids = set()
    for item in order.get("items", []):
        product_id = str(item.get("product_id", "") or "")
        product = product_lookup.get(product_id, {})
        provider_id = str(product.get("provider_id", "") or item.get("provider_id", "") or "")
        if not provider_id and product_id:
            for mapped_provider_id, mapped_product_ids in provider_item_map.items():
                mapped_ids = {str(mapped_id) for mapped_id in (mapped_product_ids or [])}
                if product_id in mapped_ids:
                    provider_id = str(mapped_provider_id)
                    break
        if provider_scope_ids and provider_id not in provider_scope_ids:
            continue

        quantity = int(item.get("quantity", 0) or 0)
        price_at_purchase = float(item.get("price_at_purchase", 0) or 0)
        line_total = round(quantity * price_at_purchase, 2)
        provider_ids.add(provider_id)
        filtered_items.append({
            "product_id": product_id,
            "name": product.get("name") or item.get("name") or "Unknown product",
            "image_url": product.get("image_url", "") or "",
            "provider_id": provider_id or None,
            "provider_name": provider_lookup.get(provider_id, provider_id or "-"),
            "sku": product.get("sku", "") or "",
            "category": product.get("category", "") or "",
            "quantity": quantity,
            "price_at_purchase": price_at_purchase,
            "line_total": line_total,
        })

    if provider_scope_ids and not filtered_items:
        order_provider_ids = {
            str(provider_id) for provider_id in (order.get("provider_ids") or [order.get("provider_id")])
            if provider_id
        }
        if not (order_provider_ids & provider_scope_ids):
            return {}

        for item in order.get("items", []):
            quantity = int(item.get("quantity", 0) or 0)
            price_at_purchase = float(item.get("price_at_purchase", 0) or 0)
            filtered_items.append({
                "product_id": str(item.get("product_id", "") or ""),
                "name": item.get("name") or "Unknown product",
                "image_url": "",
                "provider_id": None,
                "provider_name": "-",
                "sku": "",
                "category": "",
                "quantity": quantity,
                "price_at_purchase": price_at_purchase,
                "line_total": round(quantity * price_at_purchase, 2),
            })

    provider_subtotal = round(sum(item["line_total"] for item in filtered_items), 2)
    pricing = order.get("pricing") or {}
    billing = order.get("billing") or {}
    customer_name = (
        order.get("customer_name")
        or order.get("user_name")
        or (user.get("username") if user else "")
        or "Unknown customer"
    )
    customer_email = (
        order.get("customer_email")
        or (user.get("email") if user else "")
        or ""
    )

    return {
        "order_id": str(order.get("_id")),
        "invoice_number": billing.get("invoice_number") or "",
        "customer_name": customer_name,
        "customer_email": customer_email,
        "status": str(order.get("status", "") or "").lower(),
        "payment_status": str(order.get("payment_status", "") or "").lower(),
        "fulfillment_status": str(order.get("fulfillment_status", "") or "").lower(),
        "status_label": derive_user_order_status(order),
        "total_amount": float(order.get("total_amount", 0) or 0),
        "provider_subtotal": provider_subtotal,
        "item_count": sum(item["quantity"] for item in filtered_items),
        "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
        "updated_at": order.get("updated_at").isoformat() if order.get("updated_at") else None,
        "shipping_address": order.get("shipping_address", "") or "",
        "payment_method": order.get("payment_method", "") or "",
        "slip_image": order.get("slip_image", "") or "",
        "slip_note": order.get("slip_note", "") or "",
        "slip_review_note": order.get("slip_review_note", "") or "",
        "provider_ids": [provider_id for provider_id in provider_ids if provider_id],
        "provider_names": [provider_lookup.get(provider_id, provider_id) for provider_id in provider_ids if provider_id],
        "pricing": pricing,
        "items": filtered_items,
    }


def slugify_shop_name(name: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in name.strip())
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "shop"


async def list_provider_shops(owner_provider_id: str) -> List[dict]:
    shops = []
    seen_shop_ids = set()
    owner = await UserDB.get_user_by_id(owner_provider_id)
    if owner and owner.get("role") == "provider":
        shops.append({
            "provider_id": owner_provider_id,
            "provider_name": owner.get("username") or owner.get("email", "").split("@")[0] or owner_provider_id,
            "email": owner.get("email", ""),
            "logo_url": owner.get("logo_url") or owner.get("image_url") or "",
            "is_primary": True,
            "owner_provider_id": None,
        })
        seen_shop_ids.add(owner_provider_id)

    child_shops = await db.db["users"].find({
        "role": "provider",
        "owner_provider_id": owner_provider_id,
        "is_active": True,
    }).sort("created_at", 1).to_list(None)

    for shop in child_shops:
        shop_id = str(shop.get("_id"))
        if shop_id in seen_shop_ids:
            continue
        shops.append({
            "provider_id": shop_id,
            "provider_name": shop.get("username") or shop.get("email", "").split("@")[0] or shop_id,
            "email": shop.get("email", ""),
            "logo_url": shop.get("logo_url") or shop.get("image_url") or "",
            "is_primary": False,
            "owner_provider_id": owner_provider_id,
        })
        seen_shop_ids.add(shop_id)

    provider_scopes = await get_provider_scopes(owner_provider_id)
    scoped_products = await db.db["products"].find({
        "provider_id": {"$in": provider_scopes}
    }).to_list(None)
    products_by_provider = {}
    for product in scoped_products:
        provider_id = str(product.get("provider_id") or "")
        if not provider_id:
            continue
        products_by_provider.setdefault(provider_id, product)

    for provider_id, sample_product in products_by_provider.items():
        if provider_id in seen_shop_ids:
            continue
        shops.append({
            "provider_id": provider_id,
            "provider_name": provider_id,
            "email": "",
            "is_primary": False,
            "owner_provider_id": None,
            "legacy": True,
            "source_product_name": sample_product.get("name", ""),
        })
        seen_shop_ids.add(provider_id)

    return shops

async def require_admin_user(current_user: str) -> dict:
    user = await UserDB.get_user_by_id(current_user)
    if not user or user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

async def enforce_admin_access(current_user: str) -> dict:
    await db_rate_limiter.check_circuit_breaker()
    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return await require_admin_user(current_user)

async def build_admin_studio_snapshot() -> dict:
    users = await db.db["users"].find({}).sort("created_at", -1).to_list(None)
    raw_products = await db.db["products"].find({}).sort("updated_at", -1).to_list(None)
    products = await enrich_products_with_provider_names(raw_products)
    orders = await db.db["orders"].find({}).sort("created_at", -1).to_list(None)

    serialized_profiles = [serialize_profile(user) for user in users]
    user_lookup = {profile["id"]: profile for profile in serialized_profiles}
    product_lookup = {str(product["_id"]): product for product in products}

    return {
        "profiles": serialized_profiles,
        "products": [serialize_product(product) for product in products],
        "orders": [serialize_order(order, user_lookup, product_lookup) for order in orders],
    }


async def ensure_default_users() -> None:
    """Seed default users for first-time deployments."""
    existing_users = await db.db["users"].count_documents({})
    if existing_users > 0:
        print(f"✅ Database already has {existing_users} users")
        return

    default_users = [
        ("admin@ecommerce.local", "admin", "admin123", "admin"),
        ("provider@ecommerce.local", "provider", "Provider123", "provider"),
        ("user@ecommerce.local", "user", "User123456", "user"),
    ]

    seeded_users = []
    now = datetime.utcnow()
    for email, username, password, role in default_users:
        seeded_users.append(
            {
                "email": email,
                "username": username,
                "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                "role": role,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        )

    await db.db["users"].insert_many(seeded_users)
    print("✅ Seeded default users for first deployment")
    print("   Admin: admin@ecommerce.local / admin123")
    print("   Provider: provider@ecommerce.local / Provider123")
    print("   User: user@ecommerce.local / User123456")


def build_period_range(
    day: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
) -> Optional[tuple[datetime, datetime]]:
    if day is not None and month is not None and year is not None:
        start = datetime(year, month, day)
        return start, start + timedelta(days=1)
    if month is not None and year is not None:
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return start, end
    if year is not None:
        start = datetime(year, 1, 1)
        return start, datetime(year + 1, 1, 1)
    return None


def attach_period_filter(
    query: dict,
    field_name: str,
    day: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
) -> dict:
    period = build_period_range(day=day, month=month, year=year)
    if period:
        start, end = period
        query[field_name] = {"$gte": start, "$lt": end}
    return query

# ===================== LIFESPAN =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    print("🚀 FastAPI Server Started")
    await ensure_default_users()
    
    # Auto-load Excel data on startup
    try:
        # Check if products already exist
        existing_products = await db.db["products"].count_documents({})
        if existing_products == 0:
            print("📊 No products found in database, loading from Excel...")
            
            # Try multiple possible paths (from /app working directory)
            possible_paths = [
                "backend/Adidas US Sales Datasets.xlsx",        # In Docker
                "Adidas US Sales Datasets.xlsx",                # In backend/ directory
                "../Adidas US Sales Datasets.xlsx",
                "../../Adidas US Sales Datasets.xlsx",
            ]
            
            excel_path = None
            for path in possible_paths:
                print(f"  🔍 Checking: {path}")
                if os.path.exists(path):
                    excel_path = path
                    print(f"  ✓ Found!")
                    break
            
            if excel_path:
                print(f"  📥 Loading from: {excel_path}")
                products = await load_excel_data(excel_path)
                if products:
                    result = await db.db["products"].insert_many(products)
                    print(f"✅ Loaded {len(result.inserted_ids)} products from Excel!")
                else:
                    print(f"❌ No products extracted from Excel")
            else:
                print(f"❌ Excel file not found")
                print(f"   CWD: {os.getcwd()}")
        else:
            print(f"✅ Database already has {existing_products} products")
    except Exception as e:
        import traceback
        print(f"❌ Error auto-loading Excel: {str(e)}")
        traceback.print_exc()
    
    yield
    # Shutdown
    await close_mongo_connection()
    print("🛑 FastAPI Server Stopped")

# ===================== CREATE APP =====================

app = FastAPI(
    title="E-Commerce Admin/Provider/User API",
    description="Multi-vendor e-commerce system with stock protection & rate limiting",
    version="1.0.0",
    lifespan=lifespan
)

# ===================== CORS =====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== AUTHENTICATION ROUTES =====================

@app.post("/api/auth/register")
async def register(user: UserCreate):
    """Register new user"""
    # Check if email exists
    existing = await UserDB.get_user_by_email(user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    
    user_data = {
        "email": user.email,
        "username": user.username,
        "password_hash": hashed_pw.decode(),
        "role": user.role,
        "is_active": True,
        "provider_account_type": "provider" if str(user.role) == "provider" else "user"
    }
    
    user_id = await UserDB.create_user(user_data)
    
    # Create access token
    access_token = create_access_token({"sub": user_id})
    
    created_user = await UserDB.get_user_by_id(user_id)
    return {
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer",
        "role": created_user.get("role", user.role),
        "profile": serialize_profile(created_user),
    }

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    """Login user"""
    print(f"🔍 Login attempt: email={credentials.email}")
    
    user = await UserDB.get_user_by_email(credentials.email)
    print(f"  User found: {bool(user)}")
    
    if not user:
        print(f"  ❌ User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    try:
        password_hash = user["password_hash"]
        is_valid = bcrypt.checkpw(
            credentials.password.encode(), 
            password_hash.encode()
        )
        print(f"  Password valid: {is_valid}")
        
        if not is_valid:
            print(f"  ❌ Password mismatch")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    except Exception as e:
        print(f"  ❌ Password check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token({"sub": str(user["_id"])})
    print(f"  ✅ Login successful, token created")
    
    return {
        "user_id": str(user["_id"]),
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.get("role", "user"),
        "profile": serialize_profile(user),
    }

# ===================== ADMIN DASHBOARD ROUTES =====================

@app.get("/api/admin/dashboard")
async def admin_dashboard(current_user: str = Depends(get_current_user)):
    """Get admin dashboard (SKU summary + sales overview)"""
    await db_rate_limiter.check_circuit_breaker()
    
    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Get all products (admin can see all)
    from .database import db
    products = await db.db["products"].find({}).to_list(None)
    
    # Calculate totals
    total_products = len(products)
    total_stock = sum(p.get("stock", 0) for p in products)
    
    # Get all orders
    orders = await db.db["orders"].find({}).to_list(None)
    total_revenue = sum(o.get("total_amount", 0) for o in orders)
    total_orders = len(orders)
    
    # SKU Summary
    sku_summary = [
        {
            "sku": p.get("sku"),
            "product_name": p.get("name"),
            "provider": p.get("provider_id"),
            "stock": p.get("stock", 0),
            "price": p.get("price"),
            "total_value": p.get("stock", 0) * p.get("price", 0)
        }
        for p in products
    ]
    
    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "sku_summary": sku_summary
    }


@app.get("/api/admin/slip-reviews")
async def admin_slip_reviews(current_user: str = Depends(get_current_user)):
    """Admin: list all pending slip reviews."""
    await enforce_admin_access(current_user)
    orders = await db.db["orders"].find({
        "payment_status": PaymentStatus.PENDING_SLIP_VERIFICATION
    }).sort("slip_submitted_at", -1).to_list(None)
    reviews = []
    for order in orders:
        reviews.append(await serialize_slip_review_order(order))
    return {"orders": reviews}


@app.get("/api/admin/orders")
async def admin_orders(current_user: str = Depends(get_current_user)):
    """Admin: list all orders with full details for backoffice review."""
    await enforce_admin_access(current_user)
    orders = await db.db["orders"].find({}).sort("created_at", -1).to_list(None)
    serialized_orders = []
    for order in orders:
        serialized_orders.append(await serialize_backoffice_order(order))
    return {"orders": serialized_orders}


@app.get("/api/admin/providers")
async def admin_provider_list(current_user: str = Depends(get_current_user)):
    """Admin: list primary providers that can own shops."""
    await enforce_admin_access(current_user)
    providers = await db.db["users"].find({
        "role": "provider",
        "$or": [
            {"owner_provider_id": {"$exists": False}},
            {"owner_provider_id": None},
            {"managed_by_provider_panel": {"$ne": True}},
        ],
        "is_active": True,
    }).sort("created_at", 1).to_list(None)
    raw_products = await db.db["products"].find({}).to_list(None)
    product_counts = {}
    for product in raw_products:
        provider_id = str(product.get("provider_id") or "").strip()
        if not provider_id:
            continue
        product_counts[provider_id] = product_counts.get(provider_id, 0) + 1

    provider_payloads = []
    for provider in providers:
        provider_id = str(provider.get("_id"))
        shops = await list_provider_shops(provider_id)
        detailed_shops = []
        for shop in shops:
            shop_id = str(shop.get("provider_id") or "")
            detailed_shops.append({
                **shop,
                "product_count": product_counts.get(shop_id, 0),
            })
        shop_names = [shop.get("provider_name", "") for shop in detailed_shops if shop.get("provider_name")]
        provider_payloads.append(
            {
                "provider_id": provider_id,
                "provider_name": provider.get("username") or provider.get("email", "").split("@")[0] or provider_id,
                "email": provider.get("email", ""),
                "logo_url": provider.get("logo_url") or provider.get("image_url") or "",
                "shop_count": len(detailed_shops),
                "shop_names": shop_names,
                "shops": detailed_shops,
            }
        )

    return {
        "providers": provider_payloads
    }


@app.delete("/api/admin/provider-shops/{shop_id}")
async def admin_delete_provider_shop(
    shop_id: str,
    current_user: str = Depends(get_current_user)
):
    """Admin: delete a child shop if it has no assigned products."""
    await enforce_admin_access(current_user)
    shop_object_id = parse_object_id(shop_id, "shop_id")
    existing_shop = await db.db["users"].find_one({"_id": shop_object_id})
    if not existing_shop or existing_shop.get("role") != "provider":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if not existing_shop.get("owner_provider_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Primary provider cannot be deleted from here")

    assigned_products = await db.db["products"].count_documents({"provider_id": shop_id})
    if assigned_products > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete shop with {assigned_products} assigned products"
        )

    await db.db["users"].delete_one({"_id": shop_object_id})
    return {"status": "deleted", "shop_id": shop_id}


@app.post("/api/admin/provider-shops")
async def admin_create_provider_shop(
    payload: ProviderShopCreate,
    provider_id: str = Query(...),
    current_user: str = Depends(get_current_user)
):
    """Admin: create a shop under a selected provider."""
    await enforce_admin_access(current_user)

    owner_provider = await UserDB.get_user_by_id(provider_id)
    if not owner_provider or owner_provider.get("role") != "provider":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    shop_name = payload.name.strip()
    if not shop_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop name is required")

    email = (payload.email or "").strip().lower()
    if not email:
        slug = slugify_shop_name(shop_name)
        email = f"{slug}-{uuid.uuid4().hex[:8]}@shop.local"

    existing_user = await UserDB.get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop email already exists")

    now = datetime.utcnow()
    temp_password = uuid.uuid4().hex
    shop_data = {
        "email": email,
        "username": shop_name,
        "password_hash": bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode(),
        "role": "provider",
        "owner_provider_id": provider_id,
        "managed_by_admin_panel": True,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.db["users"].insert_one(shop_data)
    return {
        "shop": {
            "provider_id": str(result.inserted_id),
            "provider_name": shop_name,
            "email": email,
            "owner_provider_id": provider_id,
        }
    }


@app.post("/api/admin/slip-reviews/{order_id}/approve")
async def admin_approve_slip(
    order_id: str,
    payload: SlipDecisionRequest,
    current_user: str = Depends(get_current_user)
):
    await enforce_admin_access(current_user)
    order = await OrderDB.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    provider_ids = order.get("provider_ids") or [order.get("provider_id")]
    await db.db["orders"].update_one(
        {"_id": parse_object_id(order_id, "order_id")},
        {"$set": {
            "payment_status": PaymentStatus.PAID,
            "status": OrderStatus.CONFIRMED,
            "fulfillment_status": "sent_to_provider",
            "provider_statuses": {
                provider_id: "sent_to_provider"
                for provider_id in provider_ids
                if provider_id
            },
            "slip_review_note": (payload.note or "").strip(),
            "slip_reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return {"status": "approved", "order_id": order_id}


@app.post("/api/admin/slip-reviews/{order_id}/reject")
async def admin_reject_slip(
    order_id: str,
    payload: SlipDecisionRequest,
    current_user: str = Depends(get_current_user)
):
    await enforce_admin_access(current_user)
    order = await OrderDB.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    await db.db["orders"].update_one(
        {"_id": parse_object_id(order_id, "order_id")},
        {"$set": {
            "payment_status": PaymentStatus.FAILED,
            "status": OrderStatus.PENDING,
            "fulfillment_status": "slip_rejected",
            "slip_review_note": (payload.note or "").strip(),
            "slip_reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return {"status": "rejected", "order_id": order_id}

@app.get("/api/admin/inventory-status")
async def admin_inventory_status(current_user: str = Depends(get_current_user)):
    """Get inventory status with alerts"""
    from .database import db
    
    products = await db.db["products"].find({}).to_list(None)
    
    # Categorize products
    critical_stock = [p for p in products if p.get("stock", 0) == 0]
    low_stock = [p for p in products if 0 < p.get("stock", 0) < 5]
    good_stock = [p for p in products if p.get("stock", 0) >= 5]
    
    return {
        "critical_stock": {
            "count": len(critical_stock),
            "items": critical_stock
        },
        "low_stock": {
            "count": len(low_stock),
            "items": low_stock
        },
        "good_stock": {
            "count": len(good_stock)
        }
    }

@app.get("/api/admin/studio/bootstrap")
async def admin_studio_bootstrap(current_user: str = Depends(get_current_user)):
    """Admin studio bootstrap data backed by MongoDB."""
    await enforce_admin_access(current_user)
    return await build_admin_studio_snapshot()

@app.post("/api/admin/studio/profiles")
async def admin_create_profile(
    profile: AdminProfilePayload,
    current_user: str = Depends(get_current_user)
):
    """Create a new profile in the users collection."""
    await enforce_admin_access(current_user)

    existing_user = await db.db["users"].find_one({"email": profile.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    password_hash = bcrypt.hashpw(uuid.uuid4().hex.encode(), bcrypt.gensalt()).decode()
    user_data = {
        "email": profile.email.strip(),
        "username": profile.name.strip(),
        "password_hash": password_hash,
        "role": profile.role.strip().lower() or "user",
        "phone": (profile.phone or "").strip(),
        "address": (profile.address or "").strip(),
        "is_active": True,
        "managed_by_admin_studio": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.db["users"].insert_one(user_data)
    created_user = await db.db["users"].find_one({"_id": result.inserted_id})
    return {"profile": serialize_profile(created_user)}

@app.put("/api/admin/studio/profiles/{profile_id}")
async def admin_update_profile(
    profile_id: str,
    profile: AdminProfilePayload,
    current_user: str = Depends(get_current_user)
):
    """Update a profile in the users collection."""
    await enforce_admin_access(current_user)
    profile_object_id = parse_object_id(profile_id, "profile_id")

    existing_user = await db.db["users"].find_one({"email": profile.email, "_id": {"$ne": profile_object_id}})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    result = await db.db["users"].update_one(
        {"_id": profile_object_id},
        {"$set": {
            "email": profile.email.strip(),
            "username": profile.name.strip(),
            "role": profile.role.strip().lower() or "user",
            "phone": (profile.phone or "").strip(),
            "address": (profile.address or "").strip(),
            "updated_at": datetime.utcnow(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    updated_user = await db.db["users"].find_one({"_id": profile_object_id})
    return {"profile": serialize_profile(updated_user)}

@app.delete("/api/admin/studio/profiles/{profile_id}")
async def admin_delete_profile(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a profile from the users collection."""
    await enforce_admin_access(current_user)
    if profile_id == current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete the current admin profile"
        )

    result = await db.db["users"].delete_one({"_id": parse_object_id(profile_id, "profile_id")})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return {"status": "deleted"}

@app.post("/api/admin/studio/products")
async def admin_create_product(
    product: AdminProductPayload,
    current_user: str = Depends(get_current_user)
):
    """Create a product for the admin studio."""
    await enforce_admin_access(current_user)

    existing_product = await ProductDB.get_product_by_sku(product.sku)
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already exists"
        )

    product_data = {
        "name": product.name.strip(),
        "sku": product.sku.strip(),
        "category": product.category.strip(),
        "price": float(product.price),
        "stock": int(product.stock),
        "featured": int(product.featured),
        "description": (product.description or "").strip(),
        "provider_id": product.provider_id or current_user,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "stock_history": [],
    }
    result = await db.db["products"].insert_one(product_data)
    created_product = await db.db["products"].find_one({"_id": result.inserted_id})
    return {"product": serialize_product(created_product)}

@app.put("/api/admin/studio/products/{product_id}")
async def admin_update_product(
    product_id: str,
    product: AdminProductPayload,
    current_user: str = Depends(get_current_user)
):
    """Update a product for the admin studio."""
    await enforce_admin_access(current_user)
    product_object_id = parse_object_id(product_id, "product_id")

    existing_product = await db.db["products"].find_one({"sku": product.sku, "_id": {"$ne": product_object_id}})
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already exists"
        )

    result = await db.db["products"].update_one(
        {"_id": product_object_id},
        {"$set": {
            "name": product.name.strip(),
            "sku": product.sku.strip(),
            "category": product.category.strip(),
            "price": float(product.price),
            "stock": int(product.stock),
            "featured": int(product.featured),
            "description": (product.description or "").strip(),
            "provider_id": product.provider_id or current_user,
            "updated_at": datetime.utcnow(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    updated_product = await db.db["products"].find_one({"_id": product_object_id})
    return {"product": serialize_product(updated_product)}

@app.delete("/api/admin/studio/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a product from the admin studio."""
    await enforce_admin_access(current_user)
    result = await db.db["products"].delete_one({"_id": parse_object_id(product_id, "product_id")})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {"status": "deleted"}

@app.post("/api/admin/studio/orders")
async def admin_create_order(
    order: AdminOrderPayload,
    current_user: str = Depends(get_current_user)
):
    """Create an order without inventory mutation."""
    await enforce_admin_access(current_user)

    order_items = [
        {
            "product_id": item.productId,
            "name": item.name or "",
            "quantity": int(item.quantity),
            "price_at_purchase": float(item.price),
        }
        for item in order.items
    ]

    provider_id = None
    if order_items:
        first_product = await ProductDB.get_product_by_id(order_items[0]["product_id"])
        provider_id = first_product.get("provider_id") if first_product else None

    order_data = {
        "user_id": order.profile_id,
        "user_name": order.user_name.strip(),
        "provider_id": provider_id,
        "items": order_items,
        "status": normalize_order_status(order.status),
        "payment_status": PaymentStatus.PENDING,
        "total_amount": float(order.total),
        "notes": (order.notes or "").strip(),
        "shipping_address": "",
        "payment_method": "admin_manual",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.db["orders"].insert_one(order_data)
    created_order = await db.db["orders"].find_one({"_id": result.inserted_id})
    snapshot = await build_admin_studio_snapshot()
    order_lookup = {entry["id"]: entry for entry in snapshot["orders"]}
    return {"order": order_lookup[str(created_order["_id"])]}

@app.put("/api/admin/studio/orders/{order_id}")
async def admin_update_order(
    order_id: str,
    order: AdminOrderPayload,
    current_user: str = Depends(get_current_user)
):
    """Update an order without inventory mutation."""
    await enforce_admin_access(current_user)
    order_object_id = parse_object_id(order_id, "order_id")

    order_items = [
        {
            "product_id": item.productId,
            "name": item.name or "",
            "quantity": int(item.quantity),
            "price_at_purchase": float(item.price),
        }
        for item in order.items
    ]

    provider_id = None
    if order_items:
        first_product = await ProductDB.get_product_by_id(order_items[0]["product_id"])
        provider_id = first_product.get("provider_id") if first_product else None

    result = await db.db["orders"].update_one(
        {"_id": order_object_id},
        {"$set": {
            "user_id": order.profile_id,
            "user_name": order.user_name.strip(),
            "provider_id": provider_id,
            "items": order_items,
            "status": normalize_order_status(order.status),
            "total_amount": float(order.total),
            "notes": (order.notes or "").strip(),
            "updated_at": datetime.utcnow(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    snapshot = await build_admin_studio_snapshot()
    order_lookup = {entry["id"]: entry for entry in snapshot["orders"]}
    return {"order": order_lookup[order_id]}

@app.delete("/api/admin/studio/orders/{order_id}")
async def admin_delete_order(
    order_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete an order from the admin studio."""
    await enforce_admin_access(current_user)
    result = await db.db["orders"].delete_one({"_id": parse_object_id(order_id, "order_id")})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return {"status": "deleted"}

@app.post("/api/admin/studio/checkout")
async def admin_checkout(
    payload: AdminCheckoutPayload,
    current_user: str = Depends(get_current_user)
):
    """Create a real order and decrement inventory using MongoDB."""
    await enforce_admin_access(current_user)

    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    profile = await UserDB.get_user_by_id(payload.profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    order_items = []
    provider_id = None
    for item in payload.items:
        product = await ProductDB.get_product_by_id(item.productId)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {item.productId}"
            )
        if product.get("stock", 0) < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.get('name', item.productId)}"
            )

        provider_id = provider_id or product.get("provider_id")
        order_items.append({
            "product_id": item.productId,
            "name": product.get("name", item.name or ""),
            "quantity": int(item.quantity),
            "price_at_purchase": float(product.get("price", item.price)),
        })

    pricing = calculate_order_pricing(order_items)
    billing = await build_invoice_metadata()
    order_data = {
        "user_id": payload.profile_id,
        "user_name": profile.get("username", ""),
        "provider_id": provider_id,
        "items": order_items,
        "status": OrderStatus.PENDING,
        "payment_status": PaymentStatus.PENDING,
        "total_amount": pricing["grand_total"],
        "notes": (payload.notes or "").strip(),
        "shipping_address": profile.get("address", ""),
        "payment_method": "credit_card",
        "pricing": pricing,
        "billing": billing,
        "created_by_admin": current_user,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.db["orders"].insert_one(order_data)
    order_id = str(result.inserted_id)

    for item in order_items:
        stock_result = await ProductDB.update_product_stock(
            product_id=item["product_id"],
            quantity_change=-item["quantity"],
            reason=f"Admin checkout {order_id}"
        )
        if isinstance(stock_result, dict) and stock_result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=stock_result["error"]
            )

    snapshot = await build_admin_studio_snapshot()
    order_lookup = {entry["id"]: entry for entry in snapshot["orders"]}
    return {"order": order_lookup[order_id]}

# ===================== PROVIDER ROUTES (Add Products & Services) =====================

@app.get("/api/provider/settings")
async def provider_get_settings(current_user: str = Depends(get_current_user)):
    context = await get_provider_access_context(current_user, "settings")
    return {"settings": serialize_provider_settings(context["owner_user"])}

@app.put("/api/provider/settings")
async def provider_update_settings(
    payload: ProviderSettingsPayload,
    current_user: str = Depends(get_current_user)
):
    allowed_modes = {"registered", "branch", "custom"}
    address_mode = (payload.address_mode or "registered").strip().lower()
    if address_mode not in allowed_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid address mode"
        )

    settings_payload = {
        "vat_registered": bool(payload.vat_registered),
        "tax_id": (payload.tax_id or "").strip(),
        "tax_name": (payload.tax_name or "").strip(),
        "company_name": (payload.company_name or "").strip(),
        "address_mode": address_mode,
        "registered_address_line_1": (payload.registered_address_line_1 or "").strip(),
        "registered_address_line_2": (payload.registered_address_line_2 or "").strip(),
        "branch_address_line_1": (payload.branch_address_line_1 or "").strip(),
        "branch_address_line_2": (payload.branch_address_line_2 or "").strip(),
        "branch_number": (payload.branch_number or "").strip(),
        "custom_tax_address": (payload.custom_tax_address or "").strip(),
        "note": (payload.note or "").strip(),
    }

    context = await get_provider_access_context(current_user, "settings")

    result = await db.db["users"].update_one(
        {"_id": parse_object_id(context["owner_provider_id"], "user_id")},
        {"$set": {
            "provider_settings": settings_payload,
            "updated_at": datetime.utcnow(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    owner_user = await UserDB.get_user_by_id(context["owner_provider_id"])
    return {"settings": serialize_provider_settings(owner_user)}

@app.get("/api/provider/staff")
async def provider_get_staff(current_user: str = Depends(get_current_user)):
    context = await get_provider_access_context(current_user, "settings")
    staff_accounts = await db.db["users"].find({
        "role": "provider",
        "provider_account_type": "staff",
        "provider_staff_owner_id": context["owner_provider_id"],
    }).sort("created_at", 1).to_list(None)
    return {"staff": [serialize_provider_staff(user) for user in staff_accounts]}

@app.post("/api/provider/staff")
async def provider_create_staff(
    payload: ProviderStaffCreatePayload,
    current_user: str = Depends(get_current_user)
):
    context = await get_provider_access_context(current_user, "settings")
    email = (payload.email or "").strip().lower()
    username = (payload.username or "").strip()
    password = payload.password or ""
    if not email or not username or not password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name, email, and password are required")

    existing_user = await UserDB.get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    level = normalize_provider_staff_level(payload.permission_level)
    now = datetime.utcnow()
    staff_data = {
        "email": email,
        "username": username,
        "phone": (payload.phone or "").strip(),
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "role": "provider",
        "provider_account_type": "staff",
        "provider_staff_owner_id": context["owner_provider_id"],
        "provider_staff_level": level,
        "provider_staff_permissions": build_provider_staff_permissions(level),
        "managed_by_provider_panel": True,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.db["users"].insert_one(staff_data)
    created_user = await db.db["users"].find_one({"_id": result.inserted_id})
    return {"staff": serialize_provider_staff(created_user)}

@app.put("/api/provider/staff/{staff_id}")
async def provider_update_staff(
    staff_id: str,
    payload: ProviderStaffUpdatePayload,
    current_user: str = Depends(get_current_user)
):
    context = await get_provider_access_context(current_user, "settings")
    staff_object_id = parse_object_id(staff_id, "staff_id")
    existing_staff = await db.db["users"].find_one({
        "_id": staff_object_id,
        "role": "provider",
        "provider_account_type": "staff",
        "provider_staff_owner_id": context["owner_provider_id"],
    })
    if not existing_staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found")

    updates = {"updated_at": datetime.utcnow()}
    if payload.username is not None:
        updates["username"] = payload.username.strip()
    if payload.phone is not None:
        updates["phone"] = payload.phone.strip()
    if payload.is_active is not None:
        updates["is_active"] = bool(payload.is_active)
    if payload.email is not None:
        next_email = payload.email.strip().lower()
        if next_email and next_email != existing_staff.get("email"):
            duplicate = await UserDB.get_user_by_email(next_email)
            if duplicate and str(duplicate.get("_id")) != staff_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            updates["email"] = next_email
    if payload.password:
        updates["password_hash"] = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    if payload.permission_level is not None:
        level = normalize_provider_staff_level(payload.permission_level)
        updates["provider_staff_level"] = level
        updates["provider_staff_permissions"] = build_provider_staff_permissions(level)

    await db.db["users"].update_one({"_id": staff_object_id}, {"$set": updates})
    updated_staff = await db.db["users"].find_one({"_id": staff_object_id})
    return {"staff": serialize_provider_staff(updated_staff)}

@app.get("/api/provider/shops")
async def provider_get_shops(current_user: str = Depends(get_current_user)):
    """Provider: list accessible shops for product assignment."""
    context = await get_provider_access_context(current_user, "inventory")
    shops = await list_provider_shops(context["owner_provider_id"])
    return {"shops": shops}


@app.post("/api/provider/shops")
async def provider_create_shop(
    payload: ProviderShopCreate,
    current_user: str = Depends(get_current_user)
):
    """Provider: create a child shop managed by the current provider."""
    await db_rate_limiter.check_circuit_breaker()
    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    context = await get_provider_access_context(current_user, "settings")

    shop_name = payload.name.strip()
    if not shop_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop name is required")

    email = (payload.email or "").strip().lower()
    if not email:
        slug = slugify_shop_name(shop_name)
        email = f"{slug}-{uuid.uuid4().hex[:8]}@shop.local"

    existing_user = await UserDB.get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop email already exists")

    now = datetime.utcnow()
    temp_password = uuid.uuid4().hex
    shop_data = {
        "email": email,
        "username": shop_name,
        "password_hash": bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode(),
        "role": "provider",
        "owner_provider_id": context["owner_provider_id"],
        "managed_by_provider_panel": True,
        "provider_account_type": "shop",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.db["users"].insert_one(shop_data)
    return {
        "shop": {
            "provider_id": str(result.inserted_id),
            "provider_name": shop_name,
            "email": email,
            "is_primary": False,
        }
    }

@app.post("/api/provider/products")
async def provider_create_product(
    product: ProductCreate,
    current_user: str = Depends(get_current_user)
):
    """Provider: Create new product"""
    await db_rate_limiter.check_circuit_breaker()
    
    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Check if SKU exists
    existing = await ProductDB.get_product_by_sku(product.sku)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already exists"
        )
    
    context = await get_provider_access_context(current_user, "inventory")
    product_data = product.dict()
    provider_scopes = await get_provider_scopes(current_user)
    target_provider_id = product.provider_id or context["owner_provider_id"]
    if target_provider_id not in provider_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Selected shop is not assigned to this provider"
        )
    product_data["provider_id"] = target_provider_id
    
    product_id = await ProductDB.create_product(product_data)
    
    return {
        "product_id": product_id,
        "message": "Product created successfully"
    }

@app.get("/api/provider/products")
async def provider_get_products(
    category: Optional[str] = None,
    provider_id: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Provider: Get own products"""
    await get_provider_access_context(current_user, "inventory")
    products = await ProductDB.get_products_by_provider(current_user)
    products = await enrich_products_with_provider_names(products)
    normalized_provider_id = (provider_id or "").strip()
    if normalized_provider_id:
        products = [
            product for product in products
            if str(product.get("provider_id", "")) == normalized_provider_id
        ]
    normalized_category = (category or "").strip()
    if normalized_category:
        products = [
            product for product in products
            if (product.get("category") or "").strip().lower() == normalized_category.lower()
        ]
    return {"products": products}


@app.get("/api/provider/product-categories")
async def provider_get_product_categories(current_user: str = Depends(get_current_user)):
    """Provider: Get category list from own products"""
    await get_provider_access_context(current_user, "inventory")
    products = await ProductDB.get_products_by_provider(current_user)
    categories = sorted({
        (product.get("category") or "").strip()
        for product in products
        if (product.get("category") or "").strip()
    })
    return {"categories": categories}

@app.put("/api/provider/products/{product_id}")
async def provider_update_product(
    product_id: str,
    product: ProductUpdate,
    current_user: str = Depends(get_current_user)
):
    """Provider: Update own product"""
    await db_rate_limiter.check_circuit_breaker()

    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    await get_provider_access_context(current_user, "inventory")
    provider_scopes = await get_provider_scopes(current_user)
    existing_product = await ProductDB.get_product_by_id(product_id)
    if not existing_product or existing_product.get("provider_id") not in provider_scopes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if product.sku:
        sku_owner = await ProductDB.get_product_by_sku(product.sku)
        if sku_owner and str(sku_owner["_id"]) != product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists"
            )

    updated = await ProductDB.update_product(product_id, current_user, product.dict())
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return {"message": "Product updated successfully"}

@app.delete("/api/provider/products/{product_id}")
async def provider_delete_product(
    product_id: str,
    current_user: str = Depends(get_current_user)
):
    """Provider: Delete own product"""
    await db_rate_limiter.check_circuit_breaker()

    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    await get_provider_access_context(current_user, "inventory")
    provider_scopes = await get_provider_scopes(current_user)
    existing_product = await ProductDB.get_product_by_id(product_id)
    if not existing_product or existing_product.get("provider_id") not in provider_scopes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    deleted = await ProductDB.delete_product(product_id, current_user)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return {"message": "Product deleted successfully"}

@app.put("/api/provider/products/{product_id}/stock")
async def provider_restock_product(
    product_id: str,
    restock: RestockRequest,
    current_user: str = Depends(get_current_user)
):
    """Provider: Add stock to product"""
    await db_rate_limiter.check_circuit_breaker()

    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    await get_provider_access_context(current_user, "inventory")

    result = await ProductDB.update_product_stock(
        product_id=product_id,
        quantity_change=restock.quantity,
        reason=restock.reason or "Manual restock",
        provider_id=current_user
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": f"Added {restock.quantity} units", "result": result}

@app.get("/api/provider/dashboard")
async def provider_dashboard(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: str = Depends(get_current_user)
):
    """Provider: Get own dashboard"""
    context = await get_provider_access_context(current_user, "dashboard")
    dashboard = await DashboardDB.get_provider_dashboard(
        context["owner_provider_id"],
        month=month,
        year=year,
    )
    return dashboard


@app.get("/api/provider/sales-history")
async def provider_sales_history(
    day: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    category: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Provider: Get bill-style sales history filtered by day/month/year/category."""
    await get_provider_access_context(current_user, "sales_history")
    provider_scopes = await get_provider_scopes(current_user)
    products = await db.db["products"].find(
        {"provider_id": {"$in": provider_scopes}}
    ).to_list(None)
    product_lookup = {str(product["_id"]): product for product in products}
    product_ids = set(product_lookup.keys())

    query = {
        "$or": [
            {"provider_id": {"$in": provider_scopes}},
            {"provider_ids": {"$in": provider_scopes}},
        ]
    }
    attach_period_filter(query, "created_at", day=day, month=month, year=year)
    orders = await db.db["orders"].find(query).sort("created_at", -1).to_list(None)

    normalized_category = (category or "").strip().lower()
    bills = []
    for order in orders:
        bill_items = []
        for item in order.get("items", []):
            product_id = str(item.get("product_id", ""))
            if product_id not in product_ids:
                continue
            product = product_lookup.get(product_id, {})
            product_category = (product.get("category") or "").strip()
            if normalized_category and product_category.lower() != normalized_category:
                continue

            quantity = int(item.get("quantity", 0) or 0)
            unit_price = float(item.get("price_at_purchase", 0) or 0)
            bill_items.append({
                "product_id": product_id,
                "product_name": product.get("name") or item.get("name") or "",
                "image_url": product.get("image_url", "") or "",
                "sku": product.get("sku", "") or "",
                "category": product_category,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": round(quantity * unit_price, 2),
            })

        if not bill_items:
            continue

        pricing = order.get("pricing") or {}
        billing = order.get("billing") or {}
        provider_total = round(sum(item["total_amount"] for item in bill_items), 2)
        categories = sorted({item["category"] for item in bill_items if item.get("category")})
        payment_history = [
            {
                "label": "Order created",
                "channel": normalize_payment_method(order.get("payment_method")),
                "amount": provider_total,
                "status": "created",
                "timestamp": order.get("created_at").isoformat() if order.get("created_at") else None,
                "note": order.get("notes", "") or "",
            }
        ]

        if order.get("slip_submitted_at"):
            payment_history.append({
                "label": "Slip submitted",
                "channel": "transfer slip",
                "amount": provider_total,
                "status": "pending_verification",
                "timestamp": order.get("slip_submitted_at").isoformat() if order.get("slip_submitted_at") else None,
                "note": order.get("slip_note", "") or "",
            })

        if order.get("payment_date"):
            payment_history.append({
                "label": "Payment completed",
                "channel": normalize_payment_method(order.get("payment_method")),
                "amount": float(pricing.get("grand_total", order.get("total_amount", provider_total)) or 0),
                "status": "paid",
                "timestamp": order.get("payment_date").isoformat() if order.get("payment_date") else None,
                "note": order.get("slip_review_note", "") or "",
            })
        elif order.get("slip_reviewed_at"):
            payment_history.append({
                "label": "Slip reviewed",
                "channel": normalize_payment_method(order.get("payment_method")),
                "amount": provider_total,
                "status": str(order.get("payment_status", "") or "reviewed").lower(),
                "timestamp": order.get("slip_reviewed_at").isoformat() if order.get("slip_reviewed_at") else None,
                "note": order.get("slip_review_note", "") or "",
            })

        bills.append({
            "order_id": str(order["_id"]),
            "invoice_number": billing.get("invoice_number") or "",
            "receipt_number": f"R{str(order.get('_id'))[-8:].upper()}",
            "full_tax_invoice_status": billing.get("full_tax_invoice_status") or "not_issued",
            "customer_name": order.get("customer_name") or order.get("user_name") or "Unknown user",
            "customer_email": order.get("customer_email") or "",
            "customer_address": order.get("shipping_address") or "-",
            "customer_tax_id": order.get("customer_tax_id") or "-",
            "status": normalize_order_status(order.get("status")).title(),
            "payment_status": str(order.get("payment_status", "")).title(),
            "payment_status_key": str(order.get("payment_status", "")).lower(),
            "fulfillment_status": str(order.get("fulfillment_status", "") or "").lower(),
            "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
            "paid_at": order.get("payment_date").isoformat() if order.get("payment_date") else None,
            "slip_submitted_at": order.get("slip_submitted_at").isoformat() if order.get("slip_submitted_at") else None,
            "provider_total": provider_total,
            "grand_total": float(pricing.get("grand_total", order.get("total_amount", provider_total)) or 0),
            "subtotal": float(pricing.get("subtotal", provider_total) or 0),
            "discount_amount": float(pricing.get("discount_amount", 0) or 0),
            "tax_amount": float(pricing.get("tax_amount", 0) or 0),
            "taxable_amount": float(pricing.get("taxable_amount", provider_total) or 0),
            "currency": pricing.get("currency", "USD"),
            "category": ", ".join(categories) if categories else "-",
            "item_count": sum(item["quantity"] for item in bill_items),
            "items": bill_items,
            "payment_history": payment_history,
        })

    return {"history": bills}


@app.put("/api/provider/orders/{order_id}/full-tax-invoice-status")
async def provider_update_full_tax_invoice_status(
    order_id: str,
    payload: ProviderFullTaxInvoiceStatusPayload,
    current_user: str = Depends(get_current_user)
):
    await get_provider_access_context(current_user, "sales_history")
    provider_scopes = await get_provider_scopes(current_user)
    normalized_status = str(payload.status or "").strip().lower()
    if normalized_status not in {"issued", "not_issued"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid full tax invoice status")

    order_object_id = parse_object_id(order_id, "order_id")
    order = await db.db["orders"].find_one({
        "_id": order_object_id,
        "$or": [
            {"provider_id": {"$in": provider_scopes}},
            {"provider_ids": {"$in": provider_scopes}},
        ]
    })
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    await db.db["orders"].update_one(
        {"_id": order_object_id},
        {"$set": {
            "billing.full_tax_invoice_status": normalized_status,
            "billing.full_tax_invoice_status_updated_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return {"order_id": order_id, "full_tax_invoice_status": normalized_status}


@app.get("/api/provider/restock-history")
async def provider_restock_history(
    day: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    category: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Provider: Get restock history filtered by day/month/year/category."""
    await get_provider_access_context(current_user, "restock_history")
    provider_scopes = await get_provider_scopes(current_user)
    products = await db.db["products"].find(
        {"provider_id": {"$in": provider_scopes}}
    ).to_list(None)
    product_lookup = {str(product["_id"]): product for product in products}
    product_ids = set(product_lookup.keys())

    query = {
        "provider_id": {"$in": provider_scopes},
        "action": "add",
        "quantity_changed": {"$gt": 0},
    }
    attach_period_filter(query, "timestamp", day=day, month=month, year=year)
    logs = await db.db["inventory_logs"].find(query).sort("timestamp", -1).to_list(None)

    normalized_category = (category or "").strip().lower()
    history = []
    for log in logs:
        product_id = str(log.get("product_id", ""))
        if product_id not in product_ids:
            continue
        product = product_lookup.get(product_id, {})
        product_category = (product.get("category") or "").strip()
        if normalized_category and product_category.lower() != normalized_category:
            continue

        history.append({
            "product_id": product_id,
            "product_name": product.get("name", ""),
            "image_url": product.get("image_url", "") or "",
            "sku": product.get("sku", ""),
            "category": product_category,
            "quantity_changed": int(log.get("quantity_changed", 0) or 0),
            "old_stock": int(log.get("old_stock", 0) or 0),
            "new_stock": int(log.get("new_stock", 0) or 0),
            "reason": log.get("reason", "") or "",
            "timestamp": log.get("timestamp").isoformat() if log.get("timestamp") else None,
        })

    return {"history": history}


@app.get("/api/provider/slip-reviews")
async def provider_slip_reviews(current_user: str = Depends(get_current_user)):
    """Provider: Review pending payment slips for assigned orders."""
    await get_provider_access_context(current_user, "settings")
    provider_scopes = await get_provider_scopes(current_user)
    orders = await db.db["orders"].find({
        "$or": [
            {"provider_id": {"$in": provider_scopes}},
            {"provider_ids": {"$in": provider_scopes}},
        ],
        "payment_status": PaymentStatus.PENDING_SLIP_VERIFICATION,
    }).sort("slip_submitted_at", -1).to_list(None)

    reviews = []
    for order in orders:
        reviews.append(await serialize_slip_review_order(order))
    return {"orders": reviews}


@app.get("/api/provider/orders")
async def provider_orders(current_user: str = Depends(get_current_user)):
    """Provider: list all orders that include this provider's products."""
    await get_provider_access_context(current_user, "settings")
    provider_scopes = await get_provider_scopes(current_user)
    provider_scope_ids = set(provider_scopes)
    orders = await db.db["orders"].find({
        "$or": [
            {"provider_id": {"$in": provider_scopes}},
            {"provider_ids": {"$in": provider_scopes}},
        ],
    }).sort("created_at", -1).to_list(None)

    serialized_orders = []
    for order in orders:
        serialized = await serialize_backoffice_order(order, provider_scope_ids=provider_scope_ids)
        if serialized:
            serialized_orders.append(serialized)
    return {"orders": serialized_orders}


@app.post("/api/provider/slip-reviews/{order_id}/approve")
async def provider_approve_slip(
    order_id: str,
    payload: SlipDecisionRequest,
    current_user: str = Depends(get_current_user)
):
    await get_provider_access_context(current_user, "settings")
    provider_scopes = await get_provider_scopes(current_user)
    order = await OrderDB.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    provider_ids = order.get("provider_ids") or [order.get("provider_id")]
    if not any(provider_id in provider_scopes for provider_id in provider_ids if provider_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Order not assigned to this provider")

    await db.db["orders"].update_one(
        {"_id": parse_object_id(order_id, "order_id")},
        {"$set": {
            "payment_status": PaymentStatus.PAID,
            "status": OrderStatus.CONFIRMED,
            "fulfillment_status": "sent_to_provider",
            "provider_statuses": {
                provider_id: "sent_to_provider"
                for provider_id in provider_ids
                if provider_id
            },
            "slip_review_note": (payload.note or "").strip(),
            "slip_reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return {"status": "approved", "order_id": order_id}


@app.post("/api/provider/slip-reviews/{order_id}/reject")
async def provider_reject_slip(
    order_id: str,
    payload: SlipDecisionRequest,
    current_user: str = Depends(get_current_user)
):
    await get_provider_access_context(current_user, "settings")
    provider_scopes = await get_provider_scopes(current_user)
    order = await OrderDB.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    provider_ids = order.get("provider_ids") or [order.get("provider_id")]
    if not any(provider_id in provider_scopes for provider_id in provider_ids if provider_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Order not assigned to this provider")

    await db.db["orders"].update_one(
        {"_id": parse_object_id(order_id, "order_id")},
        {"$set": {
            "payment_status": PaymentStatus.FAILED,
            "status": OrderStatus.PENDING,
            "fulfillment_status": "slip_rejected",
            "slip_review_note": (payload.note or "").strip(),
            "slip_reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return {"status": "rejected", "order_id": order_id}

# ===================== USER SHOPPING ROUTES =====================

@app.get("/api/user/products")
async def user_browse_products(
    category: Optional[str] = None,
    provider_id: Optional[str] = None
):
    """User: Browse products"""
    from .database import db
    
    query = {}
    if category:
        query["category"] = category
    if provider_id:
        query["provider_id"] = provider_id
    
    products = await db.db["products"].find(query).to_list(None)
    products = await enrich_products_with_provider_names(products)
    
    return {"products": products}

@app.get("/api/user/search")
async def user_search_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    provider_id: Optional[str] = None
):
    """User: Search products by name, SKU, or description"""
    from .database import db
    
    query = {}
    
    # Build search query
    if q:
        # Search in name, SKU, and description
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"sku": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]
    
    if category:
        query["category"] = category
    if provider_id:
        query["provider_id"] = provider_id
    
    products = await db.db["products"].find(query).to_list(None)
    products = await enrich_products_with_provider_names(products)
    
    return {
        "query": q,
        "category": category,
        "count": len(products),
        "products": products
    }

@app.get("/api/user/products/{product_id}")
async def user_get_product(product_id: str):
    """User: Get product details"""
    product = await ProductDB.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    enriched = await enrich_products_with_provider_names([product])
    return enriched[0]


@app.get("/api/user/providers")
async def user_get_providers():
    """User: Get all storefront shops plus any providers with active catalog items."""
    raw_products = await db.db["products"].find({}).to_list(None)
    products = await enrich_products_with_provider_names(raw_products)
    providers = {}
    for product in products:
        provider_id = product.get("provider_id")
        if not provider_id:
            continue
        providers[provider_id] = {
            "provider_id": provider_id,
            "provider_name": product.get("provider_name", provider_id),
        }
    shop_users = await db.db["users"].find({
        "role": "provider",
        "is_active": True,
    }).to_list(None)
    for shop_user in shop_users:
        provider_id = str(shop_user.get("_id"))
        providers.setdefault(provider_id, {
            "provider_id": provider_id,
            "provider_name": shop_user.get("username") or shop_user.get("email", "").split("@")[0] or provider_id,
        })
    return {"providers": list(providers.values())}

@app.post("/api/user/orders/preview")
async def user_preview_order(
    order: OrderCreate,
    current_user: str = Depends(get_current_user)
):
    """Preview billing summary before creating an order"""
    provider_ids = []
    seen_provider_ids = set()
    for item in order.items:
        product = await ProductDB.get_product_by_id(item.product_id)
        if not product:
            continue
        provider_id = product.get("provider_id")
        if provider_id and provider_id not in seen_provider_ids:
            provider_ids.append(provider_id)
            seen_provider_ids.add(provider_id)
    pricing = calculate_order_pricing(
        [item.dict() for item in order.items],
        order.discount_code
    )
    return {
        "pricing": pricing,
        "billing": {
            "currency": pricing["currency"],
            "tax_label": pricing["tax_label"],
        }
        ,
        "provider_ids": provider_ids
    }

@app.post("/api/user/orders")
async def user_create_order(
    order: OrderCreate,
    idempotency_key: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """
    User: Create order (with duplicate purchase prevention)
    
    ป้องกัน:
    1. Stock validation (ไม่ขายเกินจำนวน)
    2. Idempotency key (ถ้า request ซ้ำกันจะ return ผลเดิม)
    3. Rate limiting (ไม่ให้ซื้อเร็วเกินไป)
    """
    
    # === STEP 1: Check rate limiting & circuit breaker ===
    await db_rate_limiter.check_circuit_breaker()
    
    if not await db_rate_limiter.check_user_rate(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests - please wait before placing another order"
        )
    
    # === STEP 2: Generate idempotency key if not provided ===
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())
    
    # === STEP 3: Check if this request was already processed ===
    existing_result = await idempotency_handler.get_result(idempotency_key)
    if existing_result:
        return existing_result
    
    # === STEP 4: Check duplicate purchase from transaction log ===
    duplicate = await TransactionLogDB.check_duplicate_purchase(idempotency_key, current_user)
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate purchase detected"
        )
    
    # === STEP 5: Check purchase rate (same product) ===
    for item in order.items:
        allowed = await duplicate_prevention.check_purchase_rate(
            current_user, item.product_id
        )
        if not allowed:
            await TransactionLogDB.log_transaction(
                user_id=current_user,
                product_id=item.product_id,
                quantity=item.quantity,
                idempotency_key=idempotency_key,
                status="failed",
                error_message="Purchase rate limit exceeded"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Purchasing same product too quickly"
            )
    
    # === STEP 6: Validate stock for all items ===
    for item in order.items:
        if not await validate_stock_availability(item.product_id, item.quantity):
            await TransactionLogDB.log_transaction(
                user_id=current_user,
                product_id=item.product_id,
                quantity=item.quantity,
                idempotency_key=idempotency_key,
                status="failed",
                error_message="Insufficient stock"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {item.product_id}"
            )
    
    # === STEP 7: Calculate total and create order ===
    try:
        pricing = calculate_order_pricing(
            [item.dict() for item in order.items],
            order.discount_code
        )
        billing = await build_invoice_metadata()
        total_amount = pricing["grand_total"]
        
        provider_ids = []
        provider_item_map = {}
        for item in order.items:
            product = await ProductDB.get_product_by_id(item.product_id)
            provider_id = product.get("provider_id") if product else None
            if provider_id:
                provider_ids.append(provider_id)
                provider_item_map.setdefault(provider_id, []).append(item.product_id)
        unique_provider_ids = list(dict.fromkeys(provider_ids))
        primary_provider_id = unique_provider_ids[0] if unique_provider_ids else None
        
        order_data = {
            "user_id": current_user,
            "provider_id": primary_provider_id,
            "provider_ids": unique_provider_ids,
            "provider_item_map": provider_item_map,
            "provider_statuses": {
                provider_id: "pending_payment"
                for provider_id in unique_provider_ids
            },
            "fulfillment_status": "pending_payment",
            "items": [item.dict() for item in order.items],
            "status": OrderStatus.PENDING,
            "payment_status": PaymentStatus.PENDING,
            "total_amount": total_amount,
            "shipping_address": order.shipping_address,
            "payment_method": normalize_payment_method(order.payment_method),
            "discount_code": order.discount_code,
            "pricing": pricing,
            "billing": billing,
            "idempotency_key": idempotency_key
        }
        
        order_id = await OrderDB.create_order(order_data)
        
        # === STEP 8: Deduct stock ===
        for item in order.items:
            result = await ProductDB.update_product_stock(
                product_id=item.product_id,
                quantity_change=-item.quantity,
                reason=f"Order {order_id}"
            )
            
            if isinstance(result, dict) and "error" in result:
                raise Exception(f"Stock update failed: {result['error']}")
        
        # === STEP 9: Log successful transaction ===
        await TransactionLogDB.log_transaction(
            user_id=current_user,
            product_id=order.items[0].product_id,
            quantity=order.items[0].quantity,
            idempotency_key=idempotency_key,
            status="success"
        )
        
        result = {
            "order_id": order_id,
            "status": "created",
            "total_amount": total_amount,
            "pricing": pricing,
            "billing": billing,
            "idempotency_key": idempotency_key
        }
        
        # Store result for idempotency
        await idempotency_handler.store_result(idempotency_key, result)
        
        return result
        
    except Exception as e:
        await db_rate_limiter.record_db_error()
        await TransactionLogDB.log_transaction(
            user_id=current_user,
            product_id=order.items[0].product_id,
            quantity=order.items[0].quantity,
            idempotency_key=idempotency_key,
            status="failed",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing order"
        )

@app.get("/api/user/profile")
async def user_get_profile(current_user: str = Depends(get_current_user)):
    """User: Get own profile"""
    profile = await UserDB.get_user_by_id(current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return {"profile": serialize_profile(profile)}

@app.put("/api/user/profile")
async def user_update_profile(
    payload: UserProfileUpdatePayload,
    current_user: str = Depends(get_current_user)
):
    """User: Update own profile details"""
    allowed_genders = {"male", "female", "other", "prefer_not_to_say"}
    normalized_gender = (payload.gender or "").strip().lower()

    if normalized_gender and normalized_gender not in allowed_genders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid gender"
        )

    context = await get_provider_access_context(current_user, "settings")

    result = await db.db["users"].update_one(
        {"_id": parse_object_id(context["owner_provider_id"], "user_id")},
        {"$set": {
            "gender": normalized_gender,
            "age": int(payload.age) if payload.age is not None else None,
            "updated_at": datetime.utcnow(),
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    profile = await UserDB.get_user_by_id(current_user)
    return {"profile": serialize_profile(profile)}

@app.get("/api/user/orders")
async def user_get_orders(current_user: str = Depends(get_current_user)):
    """User: Get own orders"""
    orders = await OrderDB.get_orders_by_user(current_user)
    serialized_orders = []
    for order in orders:
        serialized_orders.append(await serialize_user_order(order))
    return {"orders": serialized_orders}

@app.get("/api/user/orders/{order_id}")
async def user_get_order_detail(
    order_id: str,
    current_user: str = Depends(get_current_user)
):
    """User: Get order details"""
    order = await OrderDB.get_order_by_id(order_id)
    
    if not order or order.get("user_id") != current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return await serialize_user_order(order)

@app.get("/api/user/orders/{order_id}/invoice")
async def get_order_invoice(
    order_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get invoice and billing breakdown for a user's order"""
    order = await OrderDB.get_order_by_id(order_id)

    if not order or order.get("user_id") != current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return {
        "order_id": order_id,
        "status": order.get("status"),
        "payment_status": order.get("payment_status"),
        "status_label": derive_user_order_status(order),
        "billing": order.get("billing") or {},
        "pricing": order.get("pricing") or {
            "currency": "USD",
            "subtotal": order.get("total_amount", 0),
            "grand_total": order.get("total_amount", 0),
            "tax_label": TAX_LABEL,
        },
        "items": order.get("items", []),
        "shipping_address": order.get("shipping_address"),
        "payment_method": order.get("payment_method"),
    }
# ===================== PAYMENT ROUTES =====================

@app.post("/api/user/orders/{order_id}/payment")
async def process_payment(
    order_id: str,
    payment_info: PaymentRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Process payment for order
    
    Payment validation:
    1. Check if order exists and belongs to user
    2. Validate credit card format
    3. Process payment (mock implementation)
    4. Update order status
    """
    from bson import ObjectId
    
    try:
        # === Step 1: Get order ===
        order = await OrderDB.get_order_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.get("user_id") != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to order"
            )
        
        if order.get("payment_status") == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already paid"
            )
        
        # === Step 2: Validate payer details ===
        if len((payment_info.customer_name or "").strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid customer name"
            )

        email_value = (payment_info.email or "").strip()
        if "@" not in email_value or "." not in email_value.split("@")[-1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email"
            )
        
        # === Step 3: Process payment (mock) ===
        # ⚠️ In production, use Stripe, PayPal, etc.
        payment_successful = True  # Mock: always success for demo
        
        if not payment_successful:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment declined. Please try another card."
            )
        
        # === Step 4: Update order status ===
        await db.db["orders"].update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "payment_status": "paid",
                    "status": OrderStatus.CONFIRMED,
                    "fulfillment_status": "sent_to_provider",
                    "provider_statuses": {
                        provider_id: "sent_to_provider"
                        for provider_id in order.get("provider_ids", [order.get("provider_id")])
                        if provider_id
                    },
                    "updated_at": datetime.utcnow(),
                    "payment_date": datetime.utcnow(),
                    "customer_name": payment_info.customer_name.strip(),
                    "customer_email": email_value
                }
            }
        )
        
        return {
            "status": "success",
            "message": "Payment processed successfully",
            "order_id": order_id,
            "amount": (order.get("pricing") or {}).get("grand_total", order.get("total_amount")),
            "invoice_number": (order.get("billing") or {}).get("invoice_number"),
            "pricing": order.get("pricing"),
            "customer_email": email_value
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing error: {str(e)}"
        )


@app.post("/api/user/orders/{order_id}/submit-slip")
async def submit_payment_slip(
    order_id: str,
    payload: SlipUploadRequest,
    current_user: str = Depends(get_current_user)
):
    """Submit payment slip and move order to waiting-for-verification state."""
    order = await OrderDB.get_order_by_id(order_id)

    if not order or order.get("user_id") != current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.get("payment_status") == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid"
        )

    if not (payload.slip_image or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment slip is required"
        )

    email_value = (payload.email or "").strip()
    if "@" not in email_value or "." not in email_value.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email"
        )

    customer_name = (payload.customer_name or "").strip()
    if len(customer_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer name"
        )

    await db.db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {
            "payment_status": PaymentStatus.PENDING_SLIP_VERIFICATION,
            "status": OrderStatus.PENDING,
            "fulfillment_status": "awaiting_slip_verification",
            "customer_name": customer_name,
            "customer_email": email_value,
            "slip_image": payload.slip_image.strip(),
            "slip_note": (payload.note or "").strip(),
            "slip_submitted_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )

    return {
        "status": "pending_slip_verification",
        "message": "Slip submitted successfully",
        "order_id": order_id,
    }

@app.get("/api/user/orders/{order_id}/payment-status")
async def get_payment_status(
    order_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get payment status for order"""
    order = await OrderDB.get_order_by_id(order_id)
    
    if not order or order.get("user_id") != current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {
        "order_id": order_id,
        "payment_status": order.get("payment_status"),
        "pricing": order.get("pricing"),
        "billing": order.get("billing"),
        "total_amount": order.get("total_amount"),
        "status": order.get("status")
    }

# ===================== HEALTH CHECK =====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "OK", "message": "E-Commerce API is running"}

@app.get("/api/status")
async def api_status():
    """Check database status and product count"""
    try:
        product_count = await db.db["products"].count_documents({})
        user_count = await db.db["users"].count_documents({})
        order_count = await db.db["orders"].count_documents({})
        
        return {
            "status": "OK",
            "database": "Connected",
            "products": product_count,
            "users": user_count,
            "orders": order_count
        }
    except Exception as e:
        return {
            "status": "Error",
            "database": "Disconnected",
            "error": str(e)
        }

# ===================== SEED DATA ENDPOINT =====================

@app.post("/api/admin/seed-excel")
async def admin_seed_excel(current_user: str = Depends(get_current_user)):
    """
    Admin: Seed database from Excel file
    Useful for reloading data or manual trigger
    """
    try:
        # Try multiple possible paths
        possible_paths = [
            "backend/Adidas US Sales Datasets.xlsx",
            "Adidas US Sales Datasets.xlsx",
            "../Adidas US Sales Datasets.xlsx",
            "../../Adidas US Sales Datasets.xlsx",
        ]
        
        excel_path = None
        for path in possible_paths:
            if os.path.exists(path):
                excel_path = path
                break
        
        if not excel_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Excel file not found. Tried: {', '.join(possible_paths)}"
            )
        
        # Load and insert
        products = await load_excel_data(excel_path)
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No products loaded from Excel"
            )
        
        result = await db.db["products"].insert_many(products)
        
        return {
            "status": "success",
            "products_inserted": len(result.inserted_ids),
            "message": f"Successfully loaded {len(result.inserted_ids)} products from Excel"
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error seeding data: {str(e)}"
        )

# ===================== STATIC FILES ROUTES =====================

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
frontend_vue_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend-vue", "dist")
frontend_vue_assets_path = os.path.join(frontend_vue_dist_path, "assets")

if os.path.exists(frontend_vue_dist_path):
    app.mount(
        "/studio",
        StaticFiles(directory=frontend_vue_dist_path, html=True),
        name="flow_studio"
    )

if os.path.exists(frontend_vue_assets_path):
    app.mount(
        "/assets",
        StaticFiles(directory=frontend_vue_assets_path),
        name="flow_studio_assets"
    )

if os.path.exists(frontend_path):
    app.mount(
        "/frontend-assets",
        StaticFiles(directory=frontend_path),
        name="frontend_assets"
    )

@app.get("/")
async def serve_root():
    """Serve login page at root"""
    login_file = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_file):
        return FileResponse(login_file, media_type="text/html")

    studio_file = os.path.join(frontend_vue_dist_path, "index.html")
    if os.path.exists(studio_file):
        return FileResponse(studio_file, media_type="text/html")

    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/login")
async def serve_login_root():
    """Serve login page at /login"""
    login_file = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_file):
        return FileResponse(login_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/login.html")
async def serve_login():
    """Serve login page"""
    login_file = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_file):
        return FileResponse(login_file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/user-store.html")
async def serve_user_store():
    """Serve user store page"""
    file = os.path.join(frontend_path, "user-store.html")
    if os.path.exists(file):
        return FileResponse(file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/order-history.html")
async def serve_order_history():
    """Serve user order history page"""
    file = os.path.join(frontend_path, "order-history.html")
    if os.path.exists(file):
        return FileResponse(file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/user-profile.html")
async def serve_user_profile():
    """Serve user profile page"""
    file = os.path.join(frontend_path, "user-profile.html")
    if os.path.exists(file):
        return FileResponse(file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/admin-dashboard.html")
async def serve_admin_dashboard():
    """Serve admin dashboard"""
    file = os.path.join(frontend_path, "admin-dashboard.html")
    if os.path.exists(file):
        return FileResponse(file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

@app.get("/provider-panel.html")
async def serve_provider_panel():
    """Serve provider panel"""
    file = os.path.join(frontend_path, "provider-panel.html")
    if os.path.exists(file):
        return FileResponse(file, media_type="text/html")
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
