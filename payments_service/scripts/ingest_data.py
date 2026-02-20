import os
import csv
import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from payments_service.app.core.repositories.models import CardBINORM, InterchangeFeeORM

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/payments")
BIN_CSV_PATH = "/Users/pabloganga/src/projects/payments_robot/payments_service/data/raw/bin-list.csv"
FEE_JSON_PATH = "/Users/pabloganga/src/projects/payments_robot/payments_service/data/raw/interchange_fees.json"

def ingest_bins(session):
    logger.info("Starting BIN ingestion...")
    if not os.path.exists(BIN_CSV_PATH):
        logger.error(f"BIN CSV not found at {BIN_CSV_PATH}")
        return

    bins = []
    with open(BIN_CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bins.append({
                "bin": row["bin"],
                "brand": row["brand"],
                "type": row["type"],
                "category": row["category"],
                "issuer": row["issuer"],
                "country": row["country"],
                "alpha_2": row["alpha_2"],
                "alpha_3": row["alpha_3"]
            })
            
            # Flush in batches
            if len(bins) >= 10000:
                session.bulk_insert_mappings(CardBINORM, bins)
                session.commit()
                logger.info(f"Ingested {len(bins)} bins...")
                bins = []
        
        if bins:
            session.bulk_insert_mappings(CardBINORM, bins)
            session.commit()
            logger.info(f"Finished BIN ingestion. Final batch size: {len(bins)}")

def ingest_fees(session):
    logger.info("Starting Interchange Fee ingestion...")
    if not os.path.exists(FEE_JSON_PATH):
        logger.error(f"Interchange Fee JSON not found at {FEE_JSON_PATH}")
        return

    with open(FEE_JSON_PATH, mode='r') as f:
        fees_data = json.load(f)
        
    session.bulk_insert_mappings(InterchangeFeeORM, fees_data)
    session.commit()
    logger.info(f"Ingested {len(fees_data)} interchange fee rules.")

def main():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing data optionally?
        # For prototype, we'll just append or fail on PK conflict.
        # Let's truncate for clean start in prototype.
        session.query(CardBINORM).delete()
        session.query(InterchangeFeeORM).delete()
        session.commit()
        
        ingest_bins(session)
        ingest_fees(session)
        logger.info("Data ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
