"""ICOHP command managers for workflow."""
from typing import Any, Dict
from db.models import WorkflowBatchDetail, WorkflowDetail
from .command_base import CommandBase

class StartICOHPManager(CommandBase):
    """Manager for starting ICOHP calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if ICOHP calculations can be started.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if ICOHP calculations can be started
        """
        if workflow_detail is None:
            self.logger.error("No workflow found")
            return False
            
        batches = self.container.get('batch_crud').get_batches(
            self.container.get('sqlite_connector').get_session(),
            workflow_detail.calc_unique_name)
            
        completed_dft_batches = [batch for batch in batches 
                               if batch.status == 'completed' and batch.calculation_type == 'DFT']
                               
        if not completed_dft_batches:
            self.logger.error("No completed DFT batches found")
            return False
            
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        """Start ICOHP calculations.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            Any: Execution result
        """
        
            
        try:
            self.logger.info("Setting up ICOHP workflow")

            workflow_detail = self.container.get('workflow_crud').get_workflow(
                self.container.get('sqlite_connector').get_session(),
                self.container.get('config')['workflow_name']
            )
            
            if not self.validate(workflow_detail, args):
                return False
            
            batches = self.container.get('batch_crud').get_batches(
            self.container.get('sqlite_connector').get_session(),
            workflow_detail.calc_unique_name)
            
            completed_dft_batches = [batch for batch in batches 
                                if batch.status == 'completed' and batch.calculation_type == 'dft']
            
            batch_processor = self.container.get('batch_processor')
            job_processor = self.container.get('job_processor')
            
            batches = batch_processor.process_icohp(workflow_detail, batches)
            return job_processor.process(workflow_detail, completed_dft_batches, 'start-icohp')
            
        except Exception as e:
            self.logger.error(f"Error starting ICOHP calculations: {str(e)}")
            return False

class ResumeICOHPManager(CommandBase):
    """Manager for resuming ICOHP calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if ICOHP calculations can be resumed.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            bool: True if ICOHP calculations can be resumed
        """
        if workflow_detail is None:
            self.logger.error("No workflow found to resume")
            return False
            
        batches = self.container.get('batch_crud').get_batches(
            self.container.get('sqlite_connector').get_session(),
            workflow_detail.calc_unique_name)
            
        resume_batches = [batch for batch in batches 
                         if batch.status != 'completed' and batch.calculation_type == 'icohp']
                         
        if not resume_batches:
            self.logger.error("No incomplete ICOHP batches found")
            return False
            
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        """Resume ICOHP calculations.
        
        Args:
            workflow_detail: Workflow details from database
            args: Command arguments
            
        Returns:
            Any: Execution result
        """
       
            
        try:
            self.logger.info("Resuming ICOHP calculations")

            workflow_detail = self.container.get('workflow_crud').get_workflow(
                self.container.get('sqlite_connector').get_session(),
                self.container.get('config')['workflow_name']
            )
            
            if not self.validate(workflow_detail, args):
                return False
            
            batches = self.container.get('batch_crud').get_batches(
                self.container.get('sqlite_connector').get_session(),
                workflow_detail.calc_unique_name)
                
            resume_batches = [batch for batch in batches 
                            if batch.status != 'completed' and batch.calculation_type == 'icohp']
           
            job_processor = self.container.get('job_processor')
            
            return job_processor.process(workflow_detail, resume_batches, 'resume-icohp')
            
        except Exception as e:
            self.logger.error(f"Error resuming ICOHP calculations: {str(e)}")
            return False 