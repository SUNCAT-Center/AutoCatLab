"""DFT command managers for workflow."""
import traceback
from typing import Any, Dict
from AutoCatLab.db.models import WorkflowBatchDetail, WorkflowDetail
from AutoCatLab.util.util import prompt_yes_no
from .workflow_base import WorkflowBase

class StartDFTManager(WorkflowBase):
    """Manager for starting DFT calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        
        if workflow_detail is not None:
            self.logger.error("Workflow with name {} already exists. Please use resume command to resume the workflow.".format(workflow_detail.calc_unique_name))
            return False
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        try:
            with self.container.get('sqlite_connector') as connector:
                self.logger.info("Starting DFT calculation workflow")
                workflow_detail = self.container.get('workflow_crud').get_workflow(
                    connector.get_session(),
                    self.container.get('config')['workflow_name']
                )

                if not self.validate(workflow_detail, [], args):
                    return False
        
                workflow_data = {
                    'calc_unique_name': self.container.get('config')['workflow_name'],
                    'config_path': str(self.container.get('config')['config_path'])
                }
                workflow_detail = self.container.get('workflow_crud').create_workflow(
                    connector.get_session(),
                    workflow_data
                )
            
                input_processor = self.container.get('input_processor')
                batch_processor = self.container.get('batch_processor')
                job_processor = self.container.get('job_processor')
            
                input_data = input_processor.process(workflow_detail)
                batches, executions = batch_processor.process(workflow_detail, 'dft', input_data)
                result = job_processor.process(batches)
                
                connector.get_session().commit()
                return result

        except Exception as e:
            self.logger.error(f"Error in DFT workflow: {str(e)}")
            self.logger.error("".join(traceback.format_exc()))
            connector.get_session().rollback()
            return False

class ResumeDFTManager(WorkflowBase):
    """Manager for resuming DFT calculations."""
    
    def validate(self, workflow_detail: WorkflowDetail, batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        
        if workflow_detail is None:
            self.logger.error("No workflow found to resume. Please use start command to start the workflow.")
            return False
        
                         
        if not batches:
            self.logger.error("No incomplete DFT batches found. Please check the status of the batches.")
            return False
        
        if not prompt_yes_no(f"Found {len(batches)} resumable DFT batches. Do you want to resume them? [y/N]: "):
            return False
        
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
            
        try:
            self.logger.info("Resuming DFT calculations")

            with self.container.get('sqlite_connector') as connector:
                workflow_detail = self.container.get('workflow_crud').get_workflow(
                    connector.get_session(),
                    self.container.get('config')['workflow_name']
                )

                batches = self.container.get('batch_crud').get_batches(
                    connector.get_session(),
                    workflow_detail.calc_unique_name)
                
                resume_batches = [batch for batch in batches 
                                    if batch.status != 'completed' and batch.calculation_type == 'dft']

                if not self.validate(workflow_detail, resume_batches, args):
                    return False

                batch_processor = self.container.get('batch_processor')
                job_processor = self.container.get('job_processor')


                batch_processor.update_batch_scripts(workflow_detail, resume_batches)
                result = job_processor.process(resume_batches)
                connector.get_session().commit()
                return result
            
        except Exception as e:
            self.logger.error(f"Error resuming DFT calculations: {str(e)}")
            self.logger.error("".join(traceback.format_exc()))
            connector.get_session().rollback()
            return False 