from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Callable

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
    def save(self, id: str, entity: T) -> T:
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    def query(self, predicate: Callable[[T], bool]) -> List[T]:
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
        self._data: Dict[str, T] = {}

    def save(self, id: str, entity: T) -> T:
        self._data[id] = entity
        return entity

    def find_by_id(self, id: str) -> Optional[T]:
        return self._data.get(id)

    def query(self, predicate: Callable[[T], bool]) -> List[T]:
        return [item for item in self._data.values() if predicate(item)]

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
