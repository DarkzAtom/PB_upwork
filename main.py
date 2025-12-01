from fastapi import FastAPI

# Routers
from app.parts.parts_public_routes import router as public_parts_router
from app.parts.parts_admin_routes import router as admin_parts_router
from app.brands.brands_public_routes import router as public_brands_router
from app.brands.brands_admin_routes import router as admin_brands_router
from app.categories.categories_public_routes import router as public_categories_router
from app.subcategories.subcategories_public_routes import router as public_subcategories_router
from app.subcategories.subcategories_admin_routes import router as admin_subcategories_router
from app.fx_rates.fx_rates_admin_routes import router as admin_fxrates_router
from app.pricing_rules.pricing_rules_admin_routes import router as admin_pricingrules_router
from app.shipping_rates.shipping_rates_admin_routes import router as admin_shippingrates_router
from app.shipping_zones.shipping_zones_admin_routes import router as admin_shippingzones_router
from app.supplier_price.supplier_price_admin_routes import router as admin_supplierprice_router
from app.suppliers.suppliers_admin_routes import router as admin_suppliers_router
from app.warehouses.warehouses_admin_routes import router as admin_warehouses_router
from app.cart.cart_routes import router as cart_router


app = FastAPI(title="PB_upwork API")


# Include routers
app.include_router(public_parts_router)
app.include_router(admin_parts_router)
app.include_router(public_brands_router)
app.include_router(admin_brands_router)
app.include_router(public_categories_router)
app.include_router(public_subcategories_router)
app.include_router(admin_subcategories_router)
app.include_router(admin_fxrates_router)
app.include_router(admin_pricingrules_router)
app.include_router(admin_shippingrates_router)
app.include_router(admin_shippingzones_router)
app.include_router(admin_supplierprice_router)
app.include_router(admin_suppliers_router)
app.include_router(admin_warehouses_router)
app.include_router(cart_router)


@app.get("/healthz")
def health_check():
	return {"status": "ok"}

