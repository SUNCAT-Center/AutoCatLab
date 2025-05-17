"""Progress command manager for workflow."""
from typing import Any, Dict
from AutoCatLab.db.models import WorkflowBatchDetail, WorkflowDetail
from .workflow_base import WorkflowBase

class ShowProgressManager(WorkflowBase):
    """Manager for showing workflow progress."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if progress can be shown.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if progress can be shown
        """
        if workflow_detail is None:
            self.logger.error("No workflow found")
            return False
            
        calculation_type = args.get('calculation_type')
        if calculation_type and calculation_type not in ['dft', 'icohp']:
            self.logger.error(f"Invalid calculation type: {calculation_type}")
            return False
            
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        """Show workflow progress.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            Any: Progress information
        """
        if not self.validate(workflow_detail, args):
            return False
            
        try:
            self.logger.info("Showing workflow progress")
            batches = self.container.get('batch_crud').get_batches(
                self.container.get('sqlite_connector').get_session(),
                workflow_detail.calc_unique_name)
                
            calculation_type = args.get('calculation_type')
            if calculation_type:
                batches = [batch for batch in batches 
                          if batch.calculation_type.upper() == calculation_type.upper()]
                          
            total_batches = len(batches)
            completed_batches = len([b for b in batches if b.status == 'completed'])
            running_batches = len([b for b in batches if b.status == 'running'])
            failed_batches = len([b for b in batches if b.status == 'failed'])
            
            return {
                'workflow_id': workflow_detail.workflow_id,
                'calculation_type': calculation_type or 'all',
                'total_batches': total_batches,
                'completed_batches': completed_batches,
                'running_batches': running_batches,
                'failed_batches': failed_batches,
                'batches': [{
                    'batch_id': batch.batch_id,
                    'status': batch.status,
                    'calculation_type': batch.calculation_type,
                    'start_time': batch.start_time,
                    'end_time': batch.end_time
                } for batch in batches]
            }
            
        except Exception as e:
            self.logger.error(f"Error showing progress: {str(e)}")
            return False 