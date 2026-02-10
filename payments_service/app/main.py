from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from payments_service.app.core.api import payments, merchants, customers
from dotenv import load_dotenv

app = FastAPI(title="Payments Service")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; refine this for production later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Include the payments router with a prefix
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(merchants.router, tags=["merchants"])
app.include_router(customers.router, tags=["customers"])

@app.get("/")
def read_root():
    return {"Hello": "World"}