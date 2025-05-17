"""Job processor for AutoCatLab."""
from typing import Dict, Any, List
import subprocess

from AutoCatLab.container_base import Container
from AutoCatLab.db.models import WorkflowBatchDetail
from AutoCatLab.util.util import get_bool_env, show_message


class JobProcessor:
    """Processes jobs for calculations."""

    def __init__(self, container: Container):
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')

    def process(self, batches: List[WorkflowBatchDetail]) -> None:
        
        if get_bool_env('local_dev'):
            self.logger.info("Running in local development mode. Skipping job submission.")
            # raise Exception("Running in local development mode. Skipping job submission.")
            return
        

        connector = self.container.get('sqlite_connector')
        success = True
        for batch in batches:
            try:
                result = subprocess.run(['sbatch', str(batch.script_path)],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    text=True)
                if result.returncode == 0:               
                    job_id = result.stdout.strip().split()[-1]
                    self.container.get('batch_crud').update_batch(
                        connector.get_session(),
                        batch.batch_id,
                        {'job_id': job_id}
                    )
                else:
                    success = False
                    raise Exception(f"Job submission failed: {result.stderr}")

            except Exception as e:
                self.logger.error(f"Failed to submit batch {batch.batch_id}: {str(e)}")
                raise

        if success:
            show_message("All jobs submitted successfully", "success")
            self.logger.info("All jobs submitted successfully")
