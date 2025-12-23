from fastapi import APIRouter, Depends, HTTPException
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from payments_service.app.models.payment import Payment, PaymentCreate
from payments_service.app.services.payment_service import PaymentService, get_payment_service

router = APIRouter()

@router.post("", response_model=Payment, status_code=201)
def create_payment(payment_create: PaymentCreate, service: PaymentService = Depends(get_payment_service)):
    return service.create_payment(payment_create)

@router.get("", response_model=List[Payment])
def get_all_payments(service: PaymentService = Depends(get_payment_service)):
    return service.get_all_payments()

@router.get("/{payment_id}", response_model=Payment)
def get_payment(payment_id: str, service: PaymentService = Depends(get_payment_service)):
    payment = service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.post("/{payment_id}/authorize", response_model=Payment)
def authorize_payment(payment_id: str, service: PaymentService = Depends(get_payment_service)):
    payment = service.authorize_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=400, detail="Payment could not be authorized. Check ID and status.")
    return payment

@router.post("/{payment_id}/settle", response_model=Payment)
def settle_payment(payment_id: str, service: PaymentService = Depends(get_payment_service)):
    payment = service.settle_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=400, detail="Payment could not be settled. Check ID and status.")
    return payment

@router.post("/{payment_id}/cancel", response_model=Payment)
def cancel_payment(payment_id: str, service: PaymentService = Depends(get_payment_service)):
    payment = service.cancel_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=400, detail="Payment could not be cancelled. Check ID and status.")
    return payment