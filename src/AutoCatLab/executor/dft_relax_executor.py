"""DFT relaxation executor implementation."""
import json
import traceback
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
from ase.io.vasp import read_vasp_xml

from AutoCatLab.executor.util.util import get_initial_magmoms, get_kpoints, get_nbands_cohp, get_LUJ_values, get_restart
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import copy_file, get_bool_env
from AutoCatLab.executor.calculation_executor import CalculationExecutor
from ase.io import read
from ase.calculators.vasp import Vasp
from ase import Atoms


class DFTRelaxExecutor(CalculationExecutor):
    """Executor for DFT relaxation calculations."""

    def save_result(self, config: Dict[str, Any], workflow_detail: WorkflowDetail, batch_detail: WorkflowBatchDetail,
                    execution: WorkflowBatchExecution) -> bool:

        with open(os.path.join(execution.result_material_dir, 'restart.json'), 'r') as f:
            restart_data = json.load(f)
        folder = execution.result_mater_dir
        entry = restart_data["1"]

        cell = np.array(entry["cell"]["array"]["__ndarray__"][2]).reshape((3, 3))
        positions = np.array(entry["positions"]["__ndarray__"][2]).reshape((-1, 3))
        numbers = np.array(entry["numbers"]["__ndarray__"][2])
        pbc = np.array(entry["pbc"]["__ndarray__"][2])
        magmoms = np.array(entry["initial_magmoms"]["__ndarray__"][2])
        charges = np.array(entry["initial_charges"]["__ndarray__"][2])

        atoms = Atoms(numbers=numbers, positions=positions, cell=cell, pbc=pbc)

        # 2. Read functional + forces, stress, energy from vasprun.xml
        vasprun_path = os.path.join(execution.result_material_dir, "vasprun.xml")

        atoms_list = list(read_vasp_xml(vasprun_path))
        atoms_final = atoms_list[-1]

        energy = atoms_final.get_potential_energy()
        forces = atoms_final.get_forces()
        stress = atoms_final.get_stress()

        # 3. Read INCAR parameters
        incar_path = os.path.join(execution.result_material_dir, "INCAR")
        incar_params = {}
        if os.path.exists(incar_path):
            with open(incar_path, 'r') as f:
                for line in f:
                    if "=" in line:
                        key, val = line.strip().split("=", 1)
                        incar_params[key.strip().upper()] = val.strip()

        # 4. Read POTCAR pseudopotentials used
        potcar_path = os.path.join(execution.result_material_dir, "POTCAR")
        pseudopotentials = []
        if os.path.exists(potcar_path):
            with open(potcar_path, 'r') as f:
                lines = f.readlines()
                pseudopotentials = [line.strip().split()[2]
                                    for line in lines if line.startswith("TITEL")]  # Format: "TITEL  = PAW_PBE X"

        # 5. Save to ase db
        with self.container.get("result_ase_db_connector") as connector:
            db = connector.db
            db.write(atoms, folder=folder,
                     data={
                         "magmoms": magmoms.tolist(),
                         "bader_charges": charges.tolist(),
                         "energy": energy,
                         "forces": forces.tolist(),
                         "stress": stress.tolist(),
                         "vasp_functional": incar_params.get("GGA", "PBE"),
                         "incar": incar_params,
                         "pseudopotentials": pseudopotentials,
                         "workflow_name": workflow_detail.calc_unique_name,
                         "batch_id": batch_detail.batch_id,
                         "user": entry.get("user", None)
                     })

        return True

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
            # self.logger.info(f"Executing bulk DFT relaxation for material {execution.material_name}")
            #
            # dir = execution.result_material_dir
            # start_json = Path(dir) / "start.json"
            # calculation_name = execution.calculation_name
            # is_bulk = "BULK" in calculation_name
            # # Get step configuration and submission details
            # submission_detail = config['workflow_steps'][batch_detail.calculation_type]['submission_detail']
            # nTask = submission_detail['nTask']
            # cpusPertask = submission_detail['cpusPertask']
            # gpu = submission_detail['gpu']
            #
            # command = 'srun -n ' + str(nTask) + ' -c ' + str(
            #     cpusPertask) + ' --cpu-bind=cores --gpu-bind=none -G ' + str(gpu) + ' vasp_std'
            #
            # atoms = read(start_json)
            # initial_magmoms = get_initial_magmoms(atoms)
            # atoms.set_initial_magnetic_moments(initial_magmoms)
            # if not is_bulk:
            #     atoms.pbc = [1, 1, 1]
            #
            # kpoints = get_kpoints(atoms, effective_length=30, bulk=is_bulk)
            # user_luj = config['user_luj_values']
            # LUJ_values = get_LUJ_values(atoms, user_luj)
            #
            # # Get VASP parameters directly from config
            # vasp_params = config['workflow_step_parameters'][calculation_name]
            #
            # # Add command and directory to parameters
            # vasp_params.update({
            #     'command': command,
            #     'directory': dir,
            #     'kpts': kpoints,
            #     'ldau_luj': LUJ_values
            # })
            #
            # calc = Vasp(**vasp_params)
            #
            # atoms.set_calculator(calc)
            # if not get_bool_env('local_dev'):
            #     atoms.get_potential_energy()
            # else:
            #     self.logger.info("Running in local development mode. Skipping DFT relaxation.")
            #
            # get_restart('OUTCAR', dir + '/')
            #
            # dos_dir_name = 'BULK_DFT_DOS'
            #
            # if not is_bulk:
            #     dos_dir_name = 'SURFACE_DFT_DOS'
            #
            # copy_file(Path(dir) / 'WAVECAR', Path(dir) / f'../{dos_dir_name}/')
            # copy_file(Path(dir) / 'POTCAR', Path(dir) / f'../{dos_dir_name}/')
            # copy_file(Path(dir) / 'POSCAR', Path(dir) / f'../{dos_dir_name}/')
            # copy_file(Path(dir) / 'restart.json', Path(dir) / f'../{dos_dir_name}/restart.json')

            # raise Exception("Test error DOS")
            self.save_result(config, workflow_detail, batch_detail, execution)
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
