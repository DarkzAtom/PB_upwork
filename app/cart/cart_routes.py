from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from decimal import Decimal

from app.cart.cart_schema import CartPriceRequest, CartPriceResponse, CartItemOutput
from app.shipping_rates.shipping_rates_model import ShippingRate
from app.shipping_zones.shipping_zones_model import ShippingZone
from app.parts.parts_model import Part
from app.parts.parts_public_routes import _choose_best_offer, _apply_pricing_rule

from db_routers_connection import get_db


router = APIRouter(prefix="/api/cart", tags=["cart"])


def _get_shipping_zone_id(db: Session, country: str) -> int:
    country = country.upper()
    
    if country in ["PL", "POLAND", "POLSKA"]:
        zone_name = "Poland"
    elif country in ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "CZ"]:
        zone_name = "EU"
    elif country in ["US", "USA", "CA"]:
        zone_name = "North America"
    else:
        zone_name = "Rest of World"
    
    zone = db.query(ShippingZone).filter(ShippingZone.name.ilike(f"%{zone_name}%")).first()
    if not zone:
        raise HTTPException(400, f"Shipping zone not found for country: {country}")
    return zone.id


def _calculate_shipping(db: Session, zone_id: int, warehouse_region: str, total_weight: float) -> Decimal:
    rate = db.query(ShippingRate).filter(
        ShippingRate.shipping_zone_id == zone_id,
        ShippingRate.warehouse_region == warehouse_region,
        ShippingRate.weight_min <= total_weight,
        ShippingRate.weight_max >= total_weight
    ).first()
    
    if rate:
        return Decimal(str(rate.price_pln))
    return Decimal("50.00")  # Fallback


def _get_part_price(db: Session, part_id: int) -> dict:
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, f"Part {part_id} not found")
    
    offer = _choose_best_offer(db, part)
    if not offer:
        raise HTTPException(400, f"Part {part_id} has no available offers")
    
    selling_price = _apply_pricing_rule(db, part, offer)
    availability = offer["availability_status"]
    lead_time = offer["lead_time_days"]
    min_days = (lead_time or 0) + 2
    max_days = (lead_time or 0) + 5
    delivery_range = f"{min_days}–{max_days} days"
    warehouse_region = offer["warehouse"].region if offer.get("warehouse") else "EU"
    
    return {
        "part_number": part.part_number,
        "name": part.name,
        "selling_price": selling_price,
        "availability_status": availability,
        "estimated_delivery_range": delivery_range,
        "warehouse_region": warehouse_region
    }


@router.post("/price", response_model=CartPriceResponse)
def calculate_cart_price(request: CartPriceRequest, db: Session = Depends(get_db)):    
    items_output = []
    subtotal = Decimal("0")
    warehouse_regions = []
    delivery_ranges = []

    for item in request.items:
        part_data = _get_part_price(db, item.part_id)
        
        if not part_data["selling_price"]:
            raise HTTPException(400, f"Part {item.part_id} has no available price")
        
        unit_price = part_data["selling_price"]
        
        items_output.append(CartItemOutput(
            part_id=item.part_id,
            part_number=part_data["part_number"],
            name=part_data["name"],
            quantity=item.quantity,
            unit_price_pln=unit_price
        ))
        
        subtotal += unit_price * item.quantity
        
        if part_data["warehouse_region"]:
            warehouse_regions.append(part_data["warehouse_region"])
        
        if part_data["estimated_delivery_range"]:
            delivery_ranges.append(part_data["estimated_delivery_range"])
                                   
    shipping_zone_id = _get_shipping_zone_id(db, request.delivery_country)
    total_items = sum(item.quantity for item in request.items)
    estimated_weight = total_items * 1.0
    
    warehouse_region = "Non-EU" if "Non-EU" in warehouse_regions else (warehouse_regions[0] if warehouse_regions else "EU")
    shipping_cost = _calculate_shipping(db, shipping_zone_id, warehouse_region, estimated_weight)
    
    if delivery_ranges:
        max_delivery = max(delivery_ranges, key=lambda r: int(r.split("–")[-1].split()[0]) if "–" in r else 0)
        delivery_days = max_delivery
    else:
        delivery_days = "10-15 days"
    
    return CartPriceResponse(
        items=items_output,
        subtotal_pln=subtotal.quantize(Decimal("0.01")),
        shipping_cost_pln=shipping_cost.quantize(Decimal("0.01")),
        total_pln=(subtotal + shipping_cost).quantize(Decimal("0.01")),
        estimated_delivery_days=delivery_days
    )
