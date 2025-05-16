"""Job processor for AutoCatLab."""
from typing import Dict, Any, List
import subprocess

from AutoCatLab.container_base import Container
from AutoCatLab.db.models import WorkflowBatchDetail
from AutoCatLab.util.util import show_message


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
        failed_batches = []
        connector = self.container.get('sqlite_connector')
        for batch in batches:
            try:

                # Submit job using sbatch
                result = subprocess.run(['sbatch', str(batch.script_path)],
                                    capture_output=True,
                                    text=True)
                print("result are", result)
                # result = {
                #     "returncode": 0,
                #     "stdout": "Submitted batch job 12345"
                # }
                if result.returncode == 0:
                # if result["returncode"] == 0:
                    # Parse job ID from output (format: "Submitted batch job 12345")
                    # job_id = result.stdout.strip().split()[-1]
                    job_id = result["stdout"].strip().split()[-1]
                    self.container.get('batch_crud').update_batch(
                        connector.get_session(),
                        batch.batch_id,
                        {'job_id': job_id}
                    )
                else:
                    failed_batches.append(batch)
                    raise Exception(f"Job submission failed: {result.stderr}")

            except Exception as e:
                self.logger.error(f"Failed to submit batch {batch.batch_id}: {str(e)}")
                raise
        if not failed_batches:
            show_message("All jobs submitted successfully", "success")
            self.logger.info("All jobs submitted successfully")
