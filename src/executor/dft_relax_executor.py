"""DFT relaxation executor implementation."""
import os
from pathlib import Path
from typing import Any, Dict
from db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from executor.util.calculation_helper import get_LUJ_values, get_initial_magmoms, get_kpoints, get_restart
from util.util import copy_file
from .calculation_executor import CalculationExecutor
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
            self.logger.info(f"Executing bulk DFT relaxation for material {execution['material_name']}")

            dir = execution.result_material_dir
            restart_json = Path(dir) / "restart.json"
            start_json = Path(dir) /  "start.json"

            # Get step configuration and submission details
            submission_detail = config['workflow_steps'][batch_detail.calculation_type]['submission_detail']
            nTask = submission_detail['nTask']
            cpusPertask = submission_detail['cpusPertask']
            gpu = submission_detail['gpu']

            command = 'srun -n ' + str(nTask) + ' -c ' + str(
                cpusPertask) + ' --cpu-bind=cores --gpu-bind=none -G ' + str(gpu) + ' vasp_std'

            if os.path.exists(restart_json):
                atoms = read(restart_json)
            else:
                atoms = read(start_json)
                initial_magmoms = get_initial_magmoms(atoms)
                atoms.set_initial_magnetic_moments(initial_magmoms)

            kpoints = get_kpoints(atoms, effective_length=30, bulk=True)
            user_luj = config['user_luj_values']
            LUJ_values = get_LUJ_values(atoms, user_luj)

            # Get VASP parameters directly from config
            vasp_params =  config['workflow_step_parameters']['BULK_DFT_RELAX']

            # Add command and directory to parameters
            vasp_params.update({
                'command': command,
                'directory': dir,
                'kpts': kpoints,
                'ldau_luj': LUJ_values
            })

            # Create VASP calculator with all parameters
            calc = Vasp(**vasp_params)

            atoms.set_calculator(calc)
            atoms.get_potential_energy()
            get_restart('OUTCAR', dir)
            # Copy files using utility function instead of direct subprocess call
            copy_file(Path(dir) / 'WAVECAR', Path(dir) / '../BULK_DFT_DOS/')
            copy_file(Path(dir) / 'POTCAR', Path(dir) / '../BULK_DFT_DOS/')
            copy_file(Path(dir) / 'POSCAR', Path(dir) / '../BULK_DFT_DOS/')
            copy_file(Path(dir) / 'restart.json', Path(dir) / '../BULK_DFT_DOS/restart.json')




            execution.status = 'completed'
            execution.success = True
            execution.error = None
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing DFT relaxation: {str(e)}")
            execution.status = 'failed'
            execution.success = False
            execution.error = str(e)
            return False 