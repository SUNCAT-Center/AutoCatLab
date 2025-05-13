"""Report command manager for workflow."""
from typing import Any, Dict
from db.models import WorkflowBatchDetail, WorkflowDetail
from .command_base import CommandBase

class ShowReportManager(CommandBase):
    """Manager for showing workflow reports."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if report can be shown.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if report can be shown
        """
        if workflow_detail is None:
            self.logger.error("No workflow found")
            return False
            
        calculation_type = args.get('calculation_type')
        if not calculation_type:
            self.logger.error("Calculation type not specified")
            return False
            
        if calculation_type not in ['dft', 'icohp']:
            self.logger.error(f"Invalid calculation type: {calculation_type}")
            return False
            
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        """Show workflow report.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            Any: Report information
        """
        if not self.validate(workflow_detail, args):
            return False
            
        try:
            self.logger.info("Showing workflow report")
            calculation_type = args['calculation_type']
            
            batches = self.container.get('batch_crud').get_batches(
                self.container.get('sqlite_connector').get_session(),
                workflow_detail.calc_unique_name)
                
            batches = [batch for batch in batches 
                      if batch.calculation_type.upper() == calculation_type.upper()]
                      
            executions = []
            for batch in batches:
                batch_executions = self.container.get('execution_crud').get_executions(
                    self.container.get('sqlite_connector').get_session(),
                    batch.batch_id)
                executions.extend(batch_executions)
                
            return {
                'workflow_id': workflow_detail.workflow_id,
                'calculation_type': calculation_type,
                'start_time': workflow_detail.start_time,
                'end_time': workflow_detail.end_time,
                'status': workflow_detail.status,
                'success': workflow_detail.success,
                'error': workflow_detail.error,
                'batches': [{
                    'batch_id': batch.batch_id,
                    'status': batch.status,
                    'start_time': batch.start_time,
                    'end_time': batch.end_time,
                    'success': batch.success,
                    'error': batch.error,
                    'executions': [{
                        'execution_id': exec.execution_id,
                        'material_name': exec.material_name,
                        'script_name': exec.script_name,
                        'status': exec.status,
                        'start_time': exec.start_time,
                        'end_time': exec.end_time,
                        'success': exec.success,
                        'error': exec.error
                    } for exec in self.container.get('execution_crud').get_executions(
                        self.container.get('sqlite_connector').get_session(),
                        batch.batch_id
                    )]
                } for batch in batches]
            }
            
        except Exception as e:
            self.logger.error(f"Error showing report: {str(e)}")
            return False 