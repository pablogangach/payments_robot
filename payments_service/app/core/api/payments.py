from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from payments_service.app.core.models.payment import Payment, PaymentCreate
from payments_service.app.core.services.payment_service import PaymentService
from payments_service.app.core.api.dependencies import get_payment_service, get_redis_client

router = APIRouter()

@router.post("/charge", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_charge(
    charge_in: PaymentCreate,
    service: PaymentService = Depends(get_payment_service)
):
    try:
        return service.create_charge(charge_in)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/recent", response_model=List[Payment])
def list_recent_charges(
    service: PaymentService = Depends(get_payment_service)
):
    # Retrieve all for the dashboard, could be limited/sorted
    return service.payment_repo.find_all()

@router.get("/charges/{charge_id}", response_model=Payment)
def get_charge(
    charge_id: str,
    service: PaymentService = Depends(get_payment_service)
):
    try:
        return service.get_payment(charge_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

@router.get("/providers/health")
def get_providers_health(
    redis_client = Depends(get_redis_client)
):
    """
    Returns real-time health status of registered payment providers.
    """
    providers = ["stripe", "paypal", "braintree", "adyen"]
    health_results = []
    
    for p in providers:
        status = "up"
        if redis_client:
            # Check for "down" flag in Redis
            down_flag = redis_client.get(f"provider_health:{p}")
            if down_flag == b"down":
                status = "down"
        
        health_results.append({
            "provider": p,
            "status": status,
            "latency_ms": 150 # Mock latency for now
        })
    
    return health_results