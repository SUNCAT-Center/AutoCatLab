"""Job processor for AutoCatLab."""
from typing import Dict, Any, List
import subprocess
from container import Container
from db.models import WorkflowBatchDetail

class JobProcessor:
    """Processes jobs for calculations."""
    
    def __init__(self, container: Container):
        """Initialize job processor.
        
        Args:
            container (Container): Service container
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')
        
    def process(self, calculation: str, batches: List[WorkflowBatchDetail]) -> None:
        """Process jobs for a calculation.
        
        Args:
            calculation (str): Calculation type
            batches (List[Dict[str, Any]]): List of batch configurations
        """
        self.logger.info(f"Processing jobs for {calculation}")
        
        for batch in batches:
            try:
                # Submit job using sbatch
                result = subprocess.run(['sbatch', str(batch.script_path)], 
                                     capture_output=True, 
                                     text=True)
                
                if result.returncode == 0:
                    # Parse job ID from output (format: "Submitted batch job 12345")
                    job_id = result.stdout.strip().split()[-1]
                    batch.job_id = job_id
                    self.container.get('batch_crud').update_batch(
                        self.container.get('sqlite_connector').get_session(),
                        batch.batch_id,
                        {'job_id': job_id}
                    )
                else:
                    raise Exception(f"Job submission failed: {result.stderr}")
                
            except Exception as e:
                self.logger.error(f"Failed to submit batch {batch.batch_id}: {str(e)}")
                raise


            
