from abc import ABC, abstractmethod
from typing import List
from deburger.analyzers.base import Issue


class PatternDetector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        pass

    @abstractmethod
    def detect(self, file_path: str, code: str, config: dict) -> List[Issue]:
        pass

    def can_detect(self, file_path: str) -> bool:
        return any(file_path.endswith(ext) for ext in self.supported_extensions)
