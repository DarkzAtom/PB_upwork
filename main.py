from fastapi import FastAPI

# Routers
from routers.public.parts import router as public_parts_router
from routers.admin.parts import router as admin_parts_router
from routers.public.brands import router as public_brands_router
from routers.admin.brands import router as admin_brands_router
from routers.public.categories import router as public_categories_router
from routers.public.subcategories import router as public_subcategories_router
from routers.admin.subcategories import router as admin_subcategories_router
from routers.admin.fx_rates import router as admin_fxrates_router
from routers.admin.pricing_rules import router as admin_pricingrules_router
from routers.admin.shipping_rates import router as admin_shippingrates_router
from routers.admin.shipping_zones import router as admin_shippingzones_router
from routers.admin.supplier_price import router as admin_supplierprice_router
from routers.admin.suppliers import router as admin_suppliers_router
from routers.admin.warehouses import router as admin_warehouses_router


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


@app.get("/healthz")
def health_check():
	return {"status": "ok"}

