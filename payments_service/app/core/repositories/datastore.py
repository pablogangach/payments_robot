from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Callable

T = TypeVar("T")

class DataStore(ABC, Generic[T]):
    """
    Abstract base class for data storage mechanisms.
    """
    @abstractmethod
    def save(self, key: str, item: T) -> T:
        """Saves an item with the given key."""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Retrieves an item by key."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieves all items in the store."""
        pass

    @abstractmethod
    def find_by(self, predicate: Callable[[T], bool]) -> List[T]:
        """Finds items that match a given predicate."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Deletes an item by key. Returns True if deleted, False if not found."""
        pass

class InMemoryDataStore(DataStore[T]):
    """
    In-memory implementation of the DataStore interface using a dictionary.
    """
    def __init__(self):
        self._data: Dict[str, T] = {}

    def save(self, key: str, item: T) -> T:
        self._data[key] = item
        return item

    def get(self, key: str) -> Optional[T]:
        return self._data.get(key)

    def get_all(self) -> List[T]:
        return list(self._data.values())

    def find_by(self, predicate: Callable[[T], bool]) -> List[T]:
        return [item for item in self._data.values() if predicate(item)]

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False
