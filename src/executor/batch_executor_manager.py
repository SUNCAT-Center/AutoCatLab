"""Batch executor manager for workflow."""
from typing import Any, Dict, Optional
from db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from .calculation_executor import CalculationExecutor
from .dft_relax_executor import DFTRelaxExecutor
from .dft_dos_executor import DFTDOSExecutor
from .icohp_executor import ICOHPExecutor

class BatchExecutorManager:
    """Manager for executing calculation batches."""
    
    def __init__(self, container: Any):
        """Initialize batch executor manager.
        
        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')
    
    def get_calculation(self, calculation_name: str) -> Optional[CalculationExecutor]:
        """Get calculation executor instance based on name.
        
        Args:
            calculation_name (str): Name of calculation type
            
        Returns:
            Optional[CalculationExecutor]: Calculation executor instance or None if type not supported
        """
        calculation_map = {
            'BULK_DFT_RELAX': DFTRelaxExecutor,
            'BULK_DFT_DOS': DFTDOSExecutor,
            'BULK_ICOHP': ICOHPExecutor
        }
        
        executor_class = calculation_map.get(calculation_name)
            
        return executor_class(self.container)
    
    def execute_batch(
        self,
        config: Dict[str, Any],
        workflow_name: str,
        batch_id: str
    ) -> bool:
        try:
            self.logger.info(f"Executing batch {batch_id} for workflow {workflow_name}")
            
            workflow_detail = self.container.get('workflow_crud').get_workflow(
                self.container.get('sqlite_connector').get_session(),
                workflow_name)
                
            if not workflow_detail:
                self.logger.error(f"Workflow {workflow_name} not found")
                return False
                
            batch_detail = self.container.get('batch_crud').get_batch(
                self.container.get('sqlite_connector').get_session(),
                batch_id)
                
            if not batch_detail:
                self.logger.error(f"Batch {batch_id} not found")
                return False
                
            executions = self.container.get('execution_crud').get_executions(
                self.container.get('sqlite_connector').get_session(),
                batch_id)
                
            if not executions:
                self.logger.error(f"No executions found for batch {batch_id}")
                return False
                
            batch_detail.status = 'running'
            session = self.container.get('sqlite_connector').get_session()
            session.commit()
            
            # Execute each calculation in the batch
            success = True
            for execution in executions:
                # Get appropriate calculation executor
                executor = self.get_calculation(execution.calculation_name)
                # Update execution status to running before calculation
                execution.status = 'running'
                session = self.container.get('sqlite_connector').get_session()
                session.commit()
                if not executor.execute_calculation(config, workflow_detail, batch_detail, execution):
                    success = False
                
                # Update execution status to completed after calculation
                execution.status = 'completed'
                session.commit()
            # Update batch status
            batch_detail.status = 'completed' if success else 'failed'
            batch_detail.success = success
            session.commit()
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing batch: {str(e)}")
            if batch_detail:
                batch_detail.status = 'failed'
                batch_detail.success = False
                batch_detail.error = str(e)
            return False 