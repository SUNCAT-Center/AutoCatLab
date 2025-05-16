"""Base container class for dependency injection."""
from typing import Any, Dict

class Container:
    """Service container for dependency injection."""
    
    def __init__(self):
        """Initialize container."""
        self._services: Dict[str, Any] = {}
        
    def set(self, name: str, service: Any) -> None:
        """Set a service in the container.
        
        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
        
    def get(self, name: str) -> Any:
        """Get a service from the container.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service not found
        """
        if name not in self._services:
            raise KeyError(f"Service not found: {name}")
        return self._services[name] 