from abc import ABC, abstractmethod
from enum import Enum


class Collector(ABC):
    Types: type[Enum]

    @abstractmethod
    def guid(self, name: str, kind: Enum | str, **kwargs) -> str:
        pass
