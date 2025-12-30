from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from payments_service.app.core.models.payment import Payment, PaymentCreate
from payments_service.app.core.services.payment_service import PaymentService
from payments_service.app.core.api.dependencies import get_payment_service

router = APIRouter()

@router.post("/charges", response_model=Payment, status_code=status.HTTP_201_CREATED)
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

@router.get("/charges/{charge_id}", response_model=Payment)
def get_charge(
    charge_id: str,
    service: PaymentService = Depends(get_payment_service)
):
    try:
        return service.get_payment(charge_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

@router.get("/charges", response_model=List[Payment])
def list_charges(
    service: PaymentService = Depends(get_payment_service)
):
    # This would typically be filtered by merchant_id in a real app
    return service.payment_repo.find_all()