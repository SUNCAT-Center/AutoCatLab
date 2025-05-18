"""DFT DOS executor implementation."""
import traceback
from datetime import datetime
import os
from pathlib import Path
import subprocess
from typing import Any, Dict
from AutoCatLab.executor.calculation_executor import CalculationExecutor
from ase.io import read
from ase.calculators.vasp import Vasp
from AutoCatLab.executor.util.util import get_initial_magmoms, get_kpoints, get_nbands_cohp, get_LUJ_values
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import get_bool_env


class DFTDOSExecutor(CalculationExecutor):
    """Executor for DFT DOS calculations."""
    
    def execute_calculation(
        self,
        config: Dict[str, Any],
        workflow_detail: WorkflowDetail,
        batch_detail: WorkflowBatchDetail,
        execution: WorkflowBatchExecution
    ) -> bool:
        """Execute DFT DOS calculation.
        
        Args:
            config: Configuration dictionary
            workflow_detail: Workflow details from database
            batch_detail: Batch details from database
            execution: Execution details from database
            
        Returns:
            bool: True if calculation executed successfully
        """
        try:
            self.logger.info(f"Executing DFT DOS for {execution.material_name}")
            
            dir = execution.result_material_dir
            restart_json = Path(dir) / "restart.json" 
            start_json = Path(dir) /  "start.json" 
            calculation_name = execution.calculation_name
            submission_detail = config['workflow_steps'][batch_detail.calculation_type]['submission_detail']
            nTask = submission_detail['nTask']
            cpusPertask = submission_detail['cpusPertask']
            gpu = submission_detail['gpu']
            is_bulk = "BULK" in calculation_name 

            command = 'srun -n ' + str(nTask) + ' -c ' + str(cpusPertask) + ' --cpu-bind=cores --gpu-bind=none -G ' + str(gpu) + ' vasp_std'
            
            if os.path.exists(restart_json):
                atoms = read(restart_json)
            else:
                atoms = read(start_json)
                initial_magmoms = get_initial_magmoms(atoms)
                atoms.set_initial_magnetic_moments(initial_magmoms)
    
            kpoints = get_kpoints(atoms, effective_length=60, bulk=is_bulk)
            user_luj =  config['user_luj_values']
            LUJ_values = get_LUJ_values(atoms, user_luj)

            nbands_cohp = get_nbands_cohp(directory=dir + '/')

            vasp_params =  config['workflow_step_parameters'][calculation_name]
            
            vasp_params.update({
                'command': command,
                'directory': dir,
                'kpts': kpoints,
                'ldau_luj': LUJ_values,
                'nbands': nbands_cohp 
            })
            
            calc = Vasp(**vasp_params)
            
            atoms.set_calculator(calc)
            
            if not get_bool_env('local_dev'):
                atoms.get_potential_energy()
                potcar_path = Path(dir) / 'POTCAR'
                subprocess.run(['sed', '-i', '/SHA256/d; /COPYR/d', str(potcar_path)], check=True)
            else:
                self.logger.info("Running in local development mode. Skipping DFT DOS.")


            self.logger.info("Successfully processed POTCAR file")
            # raise Exception("Test error")
            execution.status = 'completed'
            execution.success = True
            execution.error = None
            execution.completed_at = datetime.now()
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing DFT DOS: {str(e)}")
            self.logger.error("".join(traceback.format_exc()))
            execution.status = 'failed'
            execution.success = False
            execution.error = str(e)
            execution.completed_at = datetime.now()
            return False 