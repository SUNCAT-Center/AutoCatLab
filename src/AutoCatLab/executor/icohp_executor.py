"""ICOHP executor implementation."""
import traceback
from datetime import datetime
import os
from pathlib import Path
import subprocess
from typing import Any, Dict
# from db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
# from executor.util.calculation_helper import write_lobsterIn
from AutoCatLab.executor.calculation_executor import CalculationExecutor
from AutoCatLab.executor.util.util import write_lobsterIn
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import get_bool_env


class ICOHPExecutor(CalculationExecutor):
    """Executor for ICOHP calculations."""

    def save_result(self, config: Dict[str, Any], workflow_detail: WorkflowDetail, batch_detail: WorkflowBatchDetail,
                    execution: WorkflowBatchExecution) -> bool:
        pass

    def execute_calculation(
        self,
        config: Dict[str, Any],
        workflow_detail: WorkflowDetail,
        batch_detail: WorkflowBatchDetail,
        execution: WorkflowBatchExecution
    ) -> bool:
        """Execute ICOHP calculation.
        
        Args:
            config: Configuration dictionary
            workflow_detail: Workflow details from database
            batch_detail: Batch details from database
            execution: Execution details from database
            
        Returns:
            bool: True if calculation executed successfully
        """
        try:
            self.logger.info(f"Executing ICOHP for {execution.material_name}")            

            source_dir = Path(execution.result_material_dir).parent / "BULK_DFT_DOS/"
            dest_dir = Path(execution.result_material_dir)
            
            lobster_params = config['workflow_step_parameters']['BULK_ICOHP']
            
            write_lobsterIn(str(source_dir) + '/', config_params=lobster_params)
            
            if not get_bool_env('local_dev'):
                subprocess.call(f'cd {source_dir} && lobster-4.1.0', shell=True)
            else:
                self.logger.info("Running in local development mode. Skipping ICOHP.")

            lobster_files = [
                'bandOverlaps.lobster',
                'CHARGE.lobster',
                'COBICAR.lobster',
                'COHPCAR.lobster',
                'COOPCAR.lobster',
                'DensityOfEnergy.lobster',
                'DOSCAR.lobster',
                'GROSSPOP.lobster',
                'ICOBILIST.lobster',
                'ICOHPLIST.lobster',
                'ICOOPLIST.lobster',
                'lobsterin',
                'lobsterout',
                'MadelungEnergies.lobster',
                'SitePotentials.lobster']
            
            
            for file in lobster_files:
                src_file = os.path.join(source_dir, file)
                if os.path.exists(src_file):
                    subprocess.call(['mv', src_file, dest_dir])
            
            self.logger.info("Successfully moved LOBSTER output files to destination directory")
            self.logger.info(f"Successfully completed LOBSTER calculation for material {execution.material_name}")
            self.logger.info(f"LOBSTER output files generated in {source_dir}")

            # raise Exception("Test error ICOHP")

            execution.status = 'completed'
            execution.success = True
            execution.error = None
            execution.completed_at = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing ICOHP: {str(e)}")
            self.logger.error("".join(traceback.format_exc()))
            execution.status = 'failed'
            execution.success = False
            execution.error = str(e)
            execution.completed_at = datetime.now()
            return False 