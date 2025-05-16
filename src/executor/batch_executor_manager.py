"""Batch executor manager for workflow."""
from datetime import datetime
from typing import Any, Dict, Optional
from executor.calculation_executor import CalculationExecutor
from executor.dft_relax_executor import DFTRelaxExecutor
from executor.dft_dos_executor import DFTDOSExecutor
from executor.icohp_executor import ICOHPExecutor
import traceback

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
        
        with self.container.get('sqlite_connector') as connector:
            try:
                self.logger.info(f"Executing batch {batch_id} for workflow {workflow_name}")
                
                workflow_detail = self.container.get('workflow_crud').get_workflow(
                    connector.get_session(),
                    workflow_name)
                    
                if not workflow_detail:
                    self.logger.error(f"Workflow {workflow_name} not found")
                    return False
                    
                batch_detail = self.container.get('batch_crud').get_batch(
                    connector.get_session(),
                    batch_id)
                    
                if not batch_detail:
                    self.logger.error(f"Batch {batch_id} not found")
                    return False
                    
                executions = self.container.get('execution_crud').get_executions(
                    connector.get_session(),
                    batch_id)
                    
                if not executions:
                    self.logger.error(f"No executions found for batch {batch_id}")
                    return False
                    
                batch_detail.status = 'running'
                connector.get_session().commit()
                
                success = True
                for execution in executions:
                    executor = self.get_calculation(execution.calculation_name)
                    
                    execution.status = 'running'
                    execution.started_at = datetime.now()
                    connector.get_session().commit()

                    if not executor.execute_calculation(config, workflow_detail, batch_detail, execution):
                        success = False
                    
                    connector.get_session().commit()

                    if not success:
                        break
                    
                batch_detail.status = 'completed' if success else 'failed'
                batch_detail.success = success
                batch_detail.completed_at = datetime.now()
                connector.get_session().commit()
                return success
                
            except Exception as e:
                
                self.logger.error(f"Error executing batch: {str(e)}" + traceback.format_exc())
                if batch_detail:
                    batch_detail.status = 'failed'
                    batch_detail.success = False
                    batch_detail.error = str(e)
                    batch_detail.completed_at = datetime.now()
                    connector.get_session().commit()
                return False 