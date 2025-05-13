"""ICOHP executor implementation."""
import os
from pathlib import Path
import subprocess
from typing import Any, Dict
from db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from executor.util.calculation_helper import write_lobsterIn
from .calculation_executor import CalculationExecutor

class ICOHPExecutor(CalculationExecutor):
    """Executor for ICOHP calculations."""
    
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

            # Get source and destination directories
            source_dir = Path(execution.result_material_dir).parent / "BULK_DFT_DOS/"
            dest_dir = Path(execution.result_material_dir)
            
            # Get LOBSTER configuration parameters
            lobster_params = config['workflow_step_parameters']['BULK_ICOHP']
            
            # Write lobster input file in destination directory
            write_lobsterIn(source_dir, config_params=lobster_params)
            
            # Run lobster from source directory
            subprocess.call(f'cd {source_dir} && lobster-4.1.0', shell=True)            

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


            # Update execution status
            execution.status = 'completed'
            execution.success = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing ICOHP: {str(e)}")
            execution.status = 'failed'
            execution.success = False
            execution.error = str(e)
            return False 