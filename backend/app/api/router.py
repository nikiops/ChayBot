from fastapi import APIRouter

from app.api.routes import admin, cart, categories, favorites, orders, payment_tickets, products, system

api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payment_tickets.router, prefix="/payment-tickets", tags=["payment-tickets"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
