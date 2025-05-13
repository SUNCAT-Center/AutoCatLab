"""DFT command managers for workflow."""
from typing import Any, Dict
from db.models import WorkflowBatchDetail, WorkflowDetail
from .command_base import CommandBase

class StartDFTManager(CommandBase):
    """Manager for starting DFT calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if DFT calculations can be started.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if DFT calculations can be started
        """
        if workflow_detail is not None:
            self.logger.error("Workflow already exists")
            return False
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:

        workflow_detail = self.container.get('workflow_crud').get_workflow(
            self.container.get('sqlite_connector').get_session(),
            self.container.get('config')['workflow_name']
        )

        if not self.validate(workflow_detail, [], args):
            return False
            
        try:
            self.logger.info("Setting up DFT calculations")

            workflow_data = {
                'calc_unique_name': self.container.get('config')['workflow_name'],
                'config_path': str(self.container.get('config')['config_path'])
            }
            workflow_detail = self.container.get('workflow_crud').create_workflow(
                self.container.get('sqlite_connector').get_session(),
                workflow_data
                )
            
            input_processor = self.container.get('input_processor')
            batch_processor = self.container.get('batch_processor')
            job_processor = self.container.get('job_processor')
            
            input_data = input_processor.process(workflow_detail)
            batches, executions = batch_processor.process(workflow_detail, 'dft',input_data)
            # return job_processor.process(workflow_detail, batches)
            return []

        except Exception as e:
            self.logger.error(f"Error starting DFT calculations: {str(e)}")
            return False

class ResumeDFTManager(CommandBase):
    """Manager for resuming DFT calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if DFT calculations can be resumed.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if DFT calculations can be resumed
        """
        if workflow_detail is None:
            self.logger.error("No workflow found to resume")
            return False
            
        batches = self.container.get('batch_crud').get_batches(
            self.container.get('sqlite_connector').get_session(),
            workflow_detail.calc_unique_name)
            
        resume_batches = [batch for batch in batches 
                         if batch.status != 'completed' and batch.calculation_type == 'DFT']
                         
        if not resume_batches:
            self.logger.error("No incomplete DFT batches found")
            return False
            
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        """Resume DFT calculations.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            Any: Execution result
        """
        workflow_detail = self.container.get('workflow_crud').get_workflow(
            self.container.get('sqlite_connector').get_session(),
            self.container.get('config')['workflow_name']
        )

        if not self.validate(workflow_detail, args):
            return False
            
        try:
            self.logger.info("Resuming DFT calculations")
            
            
            batches = self.container.get('batch_crud').get_batches(
                self.container.get('sqlite_connector').get_session(),
                workflow_detail.calc_unique_name)
            resume_batches = [batch for batch in batches 
                            if batch.status != 'completed' and batch.calculation_type == 'DFT']
            
            job_processor = self.container.get('job_processor')
                            
            return job_processor.process(workflow_detail, resume_batches, 'resume-dft')
            
        except Exception as e:
            self.logger.error(f"Error resuming DFT calculations: {str(e)}")
            return False 