import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Callable, Type
from sqlalchemy.orm import Session
from sqlalchemy import select
import redis

T = TypeVar("T")

class KeyValueStore(ABC, Generic[T]):
    """
    Interface for high-speed key-based storage.
    Optimized for Read-Heavy (Intelligence) or temporary cache.
    """
    @abstractmethod
    def set(self, key: str, value: T) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        pass

class RelationalStore(ABC, Generic[T]):
    """
    Interface for consistent, queryable storage.
    Optimized for Config (Merchant/Customer) and persistent state.
    """
    @abstractmethod
    def save(self, id: Any, entity: T) -> T:
        pass

    @abstractmethod
    def find_by_id(self, id: Any) -> Optional[T]:
        pass

    @abstractmethod
    def query(self, **kwargs) -> List[T]:
        pass

    @abstractmethod
    def list_all(self) -> List[T]:
        pass

class LogAppendStore(ABC, Generic[T]):
    """
    Interface for write-heavy append-only storage.
    Optimized for Ingestion (Raw Logs).
    """
    @abstractmethod
    def append(self, record: T) -> None:
        pass

    @abstractmethod
    def batch_append(self, records: List[T]) -> None:
        pass

    @abstractmethod
    def fetch_recent(self, count: int) -> List[T]:
        pass

# --- Redis Implementation ---

class RedisKeyValueStore(KeyValueStore[T]):
    def __init__(self, redis_client: redis.Redis, model_class: Type[T] = None):
        self.client = redis_client
        self.model_class = model_class

    def _serialize(self, value: T) -> str:
        if isinstance(value, list):
            return json.dumps([v.model_dump() if hasattr(v, "model_dump") else v for v in value])
        if hasattr(value, "model_dump_json"):
            return value.model_dump_json()
        return json.dumps(value)

    def _deserialize(self, value: str) -> T:
        data = json.loads(value)
        if self.model_class == list:
            # This is a bit hacky, but for this use case we know it's List[ProviderPerformance]
            # In a real app we'd use a more robust registry or TypeAdapters
            from payments_service.app.routing.decisioning.models import ProviderPerformance
            return [ProviderPerformance.model_validate(v) for v in data]
        if hasattr(self.model_class, "model_validate"):
            return self.model_class.model_validate(data)
        return data

    def set(self, key: str, value: T):
        self.client.set(key, self._serialize(value))

    def get(self, key: str) -> Optional[T]:
        value = self.client.get(key)
        if value:
            return self._deserialize(value.decode('utf-8') if isinstance(value, bytes) else value)
        return None

    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))

    def get_all(self) -> List[T]:
        keys = self.client.keys("*")
        if not keys:
            return []
        values = self.client.mget(keys)
        return [self._deserialize(v.decode('utf-8') if isinstance(v, bytes) else v) for v in values if v]

# --- Postgres Implementation ---

class PostgresRelationalStore(RelationalStore[T]):
    def __init__(self, session: Session, sqlalchemy_model: Type[Any], pydantic_model: Type[T]):
        self.session = session
        self.sqlalchemy_model = sqlalchemy_model
        self.pydantic_model = pydantic_model

    def _to_sqla(self, entity: T) -> Any:
        data = entity.model_dump() if hasattr(entity, "model_dump") else entity
        # Filter data to only include fields in the SQLAlchemy model
        sqla_data = {k: v for k, v in data.items() if k in self.sqlalchemy_model.__table__.columns}
        return self.sqlalchemy_model(**sqla_data)

    def _to_pydantic(self, sqla_obj: Any) -> T:
        data = {c.name: getattr(sqla_obj, c.name) for c in sqla_obj.__table__.columns}
        return self.pydantic_model.model_validate(data)

    def save(self, id: Any, entity: T) -> T:
        sqla_obj = self._to_sqla(entity)
        self.session.merge(sqla_obj)
        self.session.commit()
        return entity

    def find_by_id(self, id: Any) -> Optional[T]:
        sqla_obj = self.session.get(self.sqlalchemy_model, id)
        return self._to_pydantic(sqla_obj) if sqla_obj else None

    def query(self, **kwargs) -> List[T]:
        sqla_objs = self.session.query(self.sqlalchemy_model).filter_by(**kwargs).all()
        return [self._to_pydantic(obj) for obj in sqla_objs]

    def list_all(self) -> List[T]:
        sqla_objs = self.session.query(self.sqlalchemy_model).all()
        return [self._to_pydantic(obj) for obj in sqla_objs]

# --- In-Memory Implementations ---

class InMemoryKeyValueStore(KeyValueStore[T]):
    def __init__(self):
        self._data: Dict[str, T] = {}

    def set(self, key: str, value: T):
        self._data[key] = value

    def get(self, key: str) -> Optional[T]:
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def get_all(self) -> List[T]:
        return list(self._data.values())

class InMemoryRelationalStore(RelationalStore[T]):
    def __init__(self):
        self._data: Dict[Any, T] = {}

    def save(self, id: Any, entity: T) -> T:
        self._data[id] = entity
        return entity

    def find_by_id(self, id: Any) -> Optional[T]:
        return self._data.get(id)

    def query(self, **kwargs) -> List[T]:
        # Simple filter implementation for in-memory
        results = list(self._data.values())
        for key, value in kwargs.items():
            results = [r for r in results if getattr(r, key, None) == value]
        return results

    def list_all(self) -> List[T]:
        return list(self._data.values())

class InMemoryLogAppendStore(LogAppendStore[T]):
    def __init__(self):
        self._logs: List[T] = []

    def append(self, record: T):
        self._logs.append(record)

    def batch_append(self, records: List[T]):
        self._logs.extend(records)

    def fetch_recent(self, count: int) -> List[T]:
        return self._logs[-count:] if self._logs else []
