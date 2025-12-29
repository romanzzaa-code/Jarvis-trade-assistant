
from abc import ABC, abstractmethod

class ToolExecutor(ABC):
    @abstractmethod
    def execute(self, command_data: dict) -> str:
        pass