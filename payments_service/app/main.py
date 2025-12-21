from fastapi import FastAPI
from app.api import payments
from dotenv import load_dotenv

app = FastAPI(title="Payments Service")

load_dotenv()

# Include the payments router with a prefix
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])

@app.get("/")
def read_root():
    return {"Hello": "World"}