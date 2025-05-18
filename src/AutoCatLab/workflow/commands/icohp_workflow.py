"""ICOHP command managers for workflow."""
import traceback
from typing import Any, Dict
from AutoCatLab.db.models import WorkflowBatchDetail, WorkflowDetail
from AutoCatLab.util.util import prompt_yes_no
from .workflow_base import WorkflowBase

class StartICOHPManager(WorkflowBase):
    """Manager for starting ICOHP calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        
        if workflow_detail is None:
            self.logger.error("No workflow found to start. Please use start DFT command to start the workflow.")
            return False
        completed_dft_batches = [batch for batch in batches 
                                    if batch.status == 'completed' and batch.calculation_type == 'dft']
        icohp_batches = [batch for batch in batches if  batch.calculation_type == 'icohp']
        
        if icohp_batches or len(icohp_batches) > 0:
            self.logger.error("ICOHP workflow already exists. Please use resume command to resume the workflow.")
            return False
        
        if not completed_dft_batches:
            self.logger.error("No completed DFT batches found. Please check the DFT workflow status.")
            return False
        
        if not prompt_yes_no(f"Found {len(completed_dft_batches)} eligble ICOHP batches. Do you want to run ICOHP for them? [y/N]: "):
            return False  
    
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
       
        with self.container.get('sqlite_connector') as connector:
            
            try:
                self.logger.info("Setting up ICOHP workflow")

                workflow_detail = self.container.get('workflow_crud').get_workflow(
                    connector.get_session(),
                    self.container.get('config')['workflow_unique_name']
                )

                batches = self.container.get('batch_crud').get_batches(
                    connector.get_session(),
                    workflow_detail.calc_unique_name)
                
                completed_dft_batches = [batch for batch in batches 
                                    if batch.status == 'completed' and batch.calculation_type == 'dft']
                
                if not self.validate(workflow_detail, batches, args):
                    return False

                
                batch_processor = self.container.get('batch_processor')
                job_processor = self.container.get('job_processor')
                
                icohp_batches, executions = batch_processor.process_icohp(workflow_detail, completed_dft_batches, 'icohp')
                results = job_processor.process(icohp_batches)
                connector.get_session().commit()
                return results


            except Exception as e:
                self.logger.error(f"Error starting ICOHP calculations: {str(e)}")
                self.logger.error("".join(traceback.format_exc()))
                connector.get_session().rollback()
                return False

class ResumeICOHPManager(WorkflowBase):
    """Manager for resuming ICOHP calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
       
        if workflow_detail is None:
            self.logger.error("No workflow found to resume. Please use start command to start the workflow.")
            return False

            
        resume_batches = [batch for batch in batches 
                         if batch.status != 'completed' and batch.status != 'running' and batch.calculation_type == 'icohp']
                         
        if not resume_batches:
            self.logger.error("No incomplete ICOHP batches found")
            return False

        if not prompt_yes_no(f"Found {len(resume_batches)} resumable ICOHP batches. Do you want to resume them? [y/N]: "):
            return False   
        
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
       
       
        with self.container.get('sqlite_connector') as connector:
            
            try:
                self.logger.info("Resuming ICOHP calculations")

                workflow_detail = self.container.get('workflow_crud').get_workflow(
                    connector.get_session(),
                    self.container.get('config')['workflow_unique_name']
                )

                batches = self.container.get('batch_crud').get_batches(
                    connector.get_session(),
                    workflow_detail.calc_unique_name)
                
                resume_batches = [batch for batch in batches 
                                if batch.status != 'completed' and batch.calculation_type == 'icohp']

                if not self.validate(workflow_detail, batches, args):
                    return False
                    
                batch_processor = self.container.get('batch_processor')
                batch_processor.update_batch_scripts(workflow_detail, resume_batches)
                
                job_processor = self.container.get('job_processor')
                results = job_processor.process(resume_batches)
                connector.get_session().commit()
                return results
                
            except Exception as e:
                self.logger.error(f"Error resuming ICOHP calculations: {str(e)}")
                self.logger.error("".join(traceback.format_exc()))
                connector.get_session().rollback()
                return False 