"""Base command class for workflow commands."""
from abc import ABC, abstractmethod
from typing import Any, Dict

from db.models import WorkflowDetail, WorkflowBatchDetail


class CommandBase(ABC):
    """Base class for all workflow commands."""
    
    def __init__(self, container: Any):
        """Initialize command with service container.
        
        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')
    
    @abstractmethod
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if command can be executed.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if command can be executed, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, args: list[str]) -> Any:
        """Execute the command.
        
        Args:
            args: Command arguments
            
        Returns:
            Any: Command execution result
        """
        pass 