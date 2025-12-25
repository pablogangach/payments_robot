from fastapi import FastAPI
from payments_service.app.api import payments, merchants, customers
from dotenv import load_dotenv

app = FastAPI(title="Payments Service")

load_dotenv()

# Include the payments router with a prefix
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(merchants.router, tags=["merchants"])
app.include_router(customers.router, tags=["customers"])

@app.get("/")
def read_root():
    return {"Hello": "World"}