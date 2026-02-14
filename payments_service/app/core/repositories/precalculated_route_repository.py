from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from payments_service.app.core.models.precalculated_route import PrecalculatedRoute, PrecalculatedRouteCreate
from payments_service.app.core.repositories.models import PrecalculatedRouteORM
from payments_service.app.core.utils.datetime_utils import normalize_to_utc

class PrecalculatedRouteRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, route_in: PrecalculatedRouteCreate) -> PrecalculatedRoute:
        # Normalize expires_at
        data = route_in.model_dump()
        if 'expires_at' in data:
            data['expires_at'] = normalize_to_utc(data['expires_at'])
            
        # Upsert logic for subscription_id
        db_obj = self.db.query(PrecalculatedRouteORM).filter(
            PrecalculatedRouteORM.subscription_id == data['subscription_id']
        ).first()
        
        if db_obj:
            for key, value in data.items():
                setattr(db_obj, key, value)
        else:
            db_obj = PrecalculatedRouteORM(**data)
            self.db.add(db_obj)
            
        self.db.commit()
        self.db.refresh(db_obj)
        return PrecalculatedRoute.model_validate(db_obj, from_attributes=True)

    def find_by_subscription_id(self, subscription_id: str) -> Optional[PrecalculatedRoute]:
        db_obj = self.db.query(PrecalculatedRouteORM).filter(
            PrecalculatedRouteORM.subscription_id == subscription_id
        ).first()
        if db_obj:
            return PrecalculatedRoute.model_validate(db_obj, from_attributes=True)
        return None

    def delete_expired(self, current_time: datetime):
        current_time = normalize_to_utc(current_time)
        self.db.query(PrecalculatedRouteORM).filter(
            PrecalculatedRouteORM.expires_at < current_time
        ).delete()
        self.db.commit()
