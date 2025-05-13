"""Cleanup command manager for workflow."""
import shutil
from pathlib import Path
from typing import Any, Dict
from db.models import WorkflowDetail, WorkflowBatchDetail
from .command_base import CommandBase

class CleanupManager(CommandBase):
    """Manager for cleaning up workflow files and database."""
    
    def validate(self, workflow_detail: WorkflowDetail, workflow_batches: list[WorkflowBatchDetail], args: Dict[str, Any]) -> bool:
        """Validate if cleanup can be performed.
        
        Args:
            workflow_detail: Workflow details from database
            workflow_batches: List of workflow batches
            args: Command arguments
            
        Returns:
            bool: True if cleanup can be performed
        """
        # No validation needed as we want to clean up regardless of workflow state
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
       
        try:
            
            output_dir = Path(self.config['workflow_output_directory'])
            
            if output_dir.exists():
                shutil.rmtree(output_dir)            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            return False 