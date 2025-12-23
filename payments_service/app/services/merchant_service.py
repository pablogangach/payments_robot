from payments_service.app.models.merchant import Merchant, MerchantCreate
from payments_service.app.repositories.merchant_repository import MerchantRepository

class MerchantService:
    def __init__(self, repository: MerchantRepository):
        self.repository = repository

    def onboard_merchant(self, merchant_create: MerchantCreate) -> Merchant:
        # Check if merchant exists by Tax ID
        existing = self.repository.find_by_tax_id(merchant_create.tax_id)
        if existing:
            # Re-raising as specific error or letting repo raise it.
            # Here we might want to return the existing one or error out.
            # But the test expects 409 Conflict generally.
            raise ValueError("Merchant with this Tax ID already exists")

        merchant = Merchant(**merchant_create.model_dump())
        # Here we would do calls to Stripe/Adyen to create sub-merchant
        # ...
        
        return self.repository.save(merchant)

    def get_merchant(self, merchant_id: str) -> Merchant:
        merchant = self.repository.find_by_id(merchant_id)
        if not merchant:
            raise KeyError("Merchant not found")
        return merchant
