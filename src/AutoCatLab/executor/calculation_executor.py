"""Calculation executor interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution

class CalculationExecutor(ABC):
    """Interface for calculation executors."""
    
    def __init__(self, container: Any):
        """Initialize calculation executor.
        
        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')
    
    @abstractmethod
    def execute_calculation(
        self,
        config: Dict[str, Any],
        workflow_detail: WorkflowDetail,
        batch_detail: WorkflowBatchDetail,
        execution: WorkflowBatchExecution
    ) -> bool:
        """Execute the calculation.
        
        Args:
            config: Configuration dictionary
            workflow_detail: Workflow details from database
            batch_detail: Batch details from database
            execution: Execution details from database
            
        Returns:
            bool: True if calculation executed successfully
        """
        pass 