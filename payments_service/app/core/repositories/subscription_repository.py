from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from payments_service.app.core.models.subscription import Subscription, SubscriptionCreate
from payments_service.app.core.repositories.models import SubscriptionORM
from payments_service.app.core.utils.datetime_utils import normalize_to_utc

class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, subscription_in: SubscriptionCreate) -> Subscription:
        data = subscription_in.model_dump()
        if 'next_renewal_at' in data:
            data['next_renewal_at'] = normalize_to_utc(data['next_renewal_at'])
            
        db_obj = SubscriptionORM(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return Subscription.model_validate(db_obj, from_attributes=True)

    def find_by_id(self, subscription_id: str) -> Optional[Subscription]:
        db_obj = self.db.query(SubscriptionORM).filter(SubscriptionORM.id == subscription_id).first()
        if db_obj:
            return Subscription.model_validate(db_obj, from_attributes=True)
        return None

    def find_upcoming_renewals(self, start_date: datetime, end_date: datetime) -> List[Subscription]:
        start_date = normalize_to_utc(start_date)
        end_date = normalize_to_utc(end_date)
        
        db_objs = self.db.query(SubscriptionORM).filter(
            SubscriptionORM.next_renewal_at >= start_date,
            SubscriptionORM.next_renewal_at <= end_date,
            SubscriptionORM.status == "active"
        ).all()
        return [Subscription.model_validate(obj, from_attributes=True) for obj in db_objs]
