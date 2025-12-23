from fastapi import APIRouter, HTTPException, Depends, status
from payments_service.app.models.merchant import Merchant, MerchantCreate
from payments_service.app.services.merchant_service import MerchantService
from payments_service.app.repositories.merchant_repository import MerchantRepository

router = APIRouter()

# Dependency Injection (Simple for now)
# In production, use a proper container
_merchant_repo = MerchantRepository()
_merchant_service = MerchantService(_merchant_repo)

def get_merchant_service():
    return _merchant_service

@router.post("/merchants", response_model=Merchant, status_code=status.HTTP_201_CREATED)
def create_merchant(
    merchant_in: MerchantCreate,
    service: MerchantService = Depends(get_merchant_service)
):
    try:
        return service.onboard_merchant(merchant_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("/merchants/{merchant_id}", response_model=Merchant)
def get_merchant(
    merchant_id: str,
    service: MerchantService = Depends(get_merchant_service)
):
    try:
        return service.get_merchant(merchant_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
