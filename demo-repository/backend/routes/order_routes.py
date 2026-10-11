from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
import time

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

class OrderItemSchema(BaseModel):
    product_id: str
    quantity: int
    price: float

class CreateOrderSchema(BaseModel):
    customer_id: str
    items: List[OrderItemSchema]
    shipping_address: str

# In-memory database simulation
PROCESSED_KEYS = set()
ORDERS_DB = {}

@router.post("")
async def create_order(
    payload: CreateOrderSchema,
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Creates an order.
    INTENTIONAL BUG: Race condition in idempotency processing.
    The check occurs before locking, allowing duplicate requests with the same key
    to pass through if submitted concurrently.
    """
    if x_idempotency_key:
        if x_idempotency_key in PROCESSED_KEYS:
            raise HTTPException(status_code=409, detail="Duplicate order request detected")
        
        # Simulate processing delay where race condition triggers
        time.sleep(0.05)
        PROCESSED_KEYS.add(x_idempotency_key)

    total_amount = sum(item.quantity * item.price for item in payload.items)
    order_id = f"ord_{len(ORDERS_DB) + 1001}"
    
    order = {
        "id": order_id,
        "customer_id": payload.customer_id,
        "total_amount": total_amount,
        "status": "CREATED",
        "items": [item.dict() for item in payload.items]
    }
    
    ORDERS_DB[order_id] = order
    return order
