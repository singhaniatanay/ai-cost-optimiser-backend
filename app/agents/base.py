from typing import Protocol, Any

class BaseAgent(Protocol):
    async def run(self, message: Any) -> Any:
        ...

class InvalidInputError(Exception):
    pass

# Base agent (empty) 