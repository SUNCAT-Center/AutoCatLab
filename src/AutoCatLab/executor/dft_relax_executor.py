"""DFT relaxation executor implementation."""
import traceback
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict
from AutoCatLab.executor.util.util import get_initial_magmoms, get_kpoints, get_nbands_cohp, get_LUJ_values, get_restart
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import copy_file, get_bool_env
from AutoCatLab.executor.calculation_executor import CalculationExecutor
from ase.io import read
from ase.calculators.vasp import Vasp

class DFTRelaxExecutor(CalculationExecutor):
    """Executor for DFT relaxation calculations."""
    
    def execute_calculation(
        self,
        config: Dict[str, Any],
        workflow_detail: WorkflowDetail,
        batch_detail: WorkflowBatchDetail,
        execution: WorkflowBatchExecution
    ) -> bool:
        """Execute DFT relaxation calculation.
        
        Args:
            config: Configuration dictionary
            workflow_detail: Workflow details from database
            batch_detail: Batch details from database
            execution: Execution details from database
            
        Returns:
            bool: True if calculation executed successfully
        """
        try:
            self.logger.info(f"Executing bulk DFT relaxation for material {execution.material_name}")

            dir = execution.result_material_dir
            start_json = Path(dir) /  "start.json"
            calculation_name = execution.calculation_name
            is_bulk = "BULK" in calculation_name 
            # Get step configuration and submission details
            submission_detail = config['workflow_steps'][batch_detail.calculation_type]['submission_detail']
            nTask = submission_detail['nTask']
            cpusPertask = submission_detail['cpusPertask']
            gpu = submission_detail['gpu']

            command = 'srun -n ' + str(nTask) + ' -c ' + str(
                cpusPertask) + ' --cpu-bind=cores --gpu-bind=none -G ' + str(gpu) + ' vasp_std'

            atoms = read(start_json)
            initial_magmoms = get_initial_magmoms(atoms)
            atoms.set_initial_magnetic_moments(initial_magmoms)
            if not is_bulk:
                atoms.pbc = [1,1,1]


            kpoints = get_kpoints(atoms, effective_length=30, bulk=is_bulk)
            user_luj = config['user_luj_values']
            LUJ_values = get_LUJ_values(atoms, user_luj)

            # Get VASP parameters directly from config
            vasp_params =  config['workflow_step_parameters'][calculation_name]

            # Add command and directory to parameters
            vasp_params.update({
                'command': command,
                'directory': dir,
                'kpts': kpoints,
                'ldau_luj': LUJ_values
            })

            calc = Vasp(**vasp_params)

            atoms.set_calculator(calc)
            if not get_bool_env('local_dev'):
                atoms.get_potential_energy()
            else:   
                self.logger.info("Running in local development mode. Skipping DFT relaxation.")
            
            get_restart('OUTCAR', dir + '/')
            
            dos_dir_name = 'BULK_DFT_DOS'
            
            if not is_bulk:
                dos_dir_name = 'SURFACE_DFT_DOS'


            copy_file(Path(dir) / 'WAVECAR', Path(dir) / f'../{dos_dir_name}/')
            copy_file(Path(dir) / 'POTCAR', Path(dir) / f'../{dos_dir_name}/')
            copy_file(Path(dir) / 'POSCAR', Path(dir) / f'../{dos_dir_name}/')
            copy_file(Path(dir) / 'restart.json', Path(dir) / f'../{dos_dir_name}/restart.json')

            # raise Exception("Test error DOS")

            execution.status = 'completed'
            execution.success = True
            execution.error = None
            execution.completed_at = datetime.now()
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing DFT relaxation: {str(e)}")
            self.logger.error("".join(traceback.format_exc()))
            execution.status = 'failed'
            execution.success = False
            execution.error = str(e)
            return False 