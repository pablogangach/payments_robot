from fastapi import APIRouter, HTTPException, Depends, status
from payments_service.app.core.models.customer import Customer, CustomerCreate
from payments_service.app.core.services.customer_service import CustomerService
from payments_service.app.core.api.dependencies import get_customer_service

router = APIRouter()

@router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    service: CustomerService = Depends(get_customer_service)
):
    try:
        return service.create_customer(customer_in)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/customers/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: str,
    service: CustomerService = Depends(get_customer_service)
):
    try:
        return service.get_customer(customer_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
