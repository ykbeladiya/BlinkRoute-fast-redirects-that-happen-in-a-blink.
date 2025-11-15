
from collections import OrderedDict
from typing import Optional, Any

class LRUCache:
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.store: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self.store:
            return None
        value = self.store.pop(key)
        self.store[key] = value
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self.store:
            self.store.pop(key)
        elif len(self.store) >= self.capacity:
            self.store.popitem(last=False)
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)
