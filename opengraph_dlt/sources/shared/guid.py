from abc import ABC, abstractmethod
from enum import Enum


class Collector(ABC):
    name: str

    @abstractmethod
    def guid(self, name: str, node_type: Enum | str, **kwargs) -> str:
        pass
