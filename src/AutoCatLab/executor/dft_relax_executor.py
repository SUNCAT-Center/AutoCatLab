"""DFT relaxation executor implementation."""
import json
import traceback
from datetime import datetime
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io.vasp import read_vasp_xml, read_vasp_out
from pymatgen.io.vasp import Vasprun

from AutoCatLab.executor.util.util import get_initial_magmoms, get_kpoints, get_nbands_cohp, get_LUJ_values, get_restart
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import copy_file, get_bool_env
from AutoCatLab.executor.calculation_executor import CalculationExecutor
from ase.io import read
from ase.calculators.vasp import Vasp
from ase import Atoms


class DFTRelaxExecutor(CalculationExecutor):
    """Executor for DFT relaxation calculations."""


    def save_result(self, config, workflow_detail, batch_detail, execution) -> bool:
        folder = execution.result_material_dir

        # 1. Read Atoms from OUTCAR (initial+final data)
        atoms = read_vasp_out(os.path.join(folder, 'OUTCAR'))  # contains initial_magmoms, charges, etc.

        # 2. Read final calculated values from vasprun.xml
        vasprun_path = os.path.join(folder, 'vasprun.xml')
        vasprun = Vasprun(vasprun_path)
        atoms_final = list(read_vasp_xml(vasprun_path))[-1]

        energy = atoms_final.get_potential_energy()
        forces = atoms_final.get_forces()
        stress = atoms_final.get_stress()
        magmoms = atoms.get_magnetic_moments()
        magmom = np.sum(magmoms)
        volume = atoms_final.get_volume()
        mass = atoms_final.get_masses().sum()
        fmax = np.max(np.abs(forces))
        smax = np.max(np.abs(stress))


        # 3. Attach properties to Atoms
        atoms.set_initial_magnetic_moments(atoms.get_initial_magnetic_moments())
        atoms.set_initial_charges(atoms.get_initial_charges())

        atoms.calc = SinglePointCalculator(
            atoms_final,
            energy=energy,
            forces=forces,
            stress=stress,
            magmoms=magmoms
        )

        # incar_params = vasprun.incar.as_dict()
        incar_params = json.dumps(vasprun.incar.as_dict())

        pseudopotentials = [ps["titel"] for ps in vasprun.potcar_spec]
        vasp_version = vasprun.vasp_version
        kpoints = vasprun.kpoints.kpts
        lda_u = vasprun.parameters.get("LDAUU", None)
        lda_ul = vasprun.parameters.get("LDAUL", None)
        lda_uj = vasprun.parameters.get("LDAUJ", None)

        # 5. Optional extra values
        user = os.environ.get("USER", "unknown")  # or pull from execution.metadata
        charge = np.sum(atoms.get_initial_charges())
        with open(os.path.join(execution.result_material_dir, 'restart.json'), 'r') as f:
            restart_data = json.load(f)
            entry = restart_data["1"]
            charges = np.array(entry["initial_charges"]["__ndarray__"][2])

        # 6. Save to ASE DB
        with self.container.get("result_ase_db_connector") as connector:
            db = connector.db
            db.write(
                atoms,
                key_value_pairs={
                    "vasp_functional": json.loads(incar_params).get("GGA", "PBE"),
                    "workflow_name": workflow_detail.calc_unique_name,
                    "batch_id": batch_detail.batch_id,
                    "vasp_version": vasp_version,
                    "incar": incar_params,
                    "volume": volume,
                    "mass": mass,

                },
                data={
                    "calculator": "vasp",
                    "pseudopotentials": pseudopotentials,
                    "user": user,
                    "kpoints": kpoints,
                    "ldauu": lda_u,
                    "ldaul": lda_ul,
                    "ldauj": lda_uj,
                    "forces": forces.tolist(),
                    "stress": stress.tolist(),
                    "magmoms": magmoms.tolist(),
                    "magmom": magmom,
                    "energy": energy,
                    "charge": charge,
                    "charges":charges,
                    "fmax": fmax,
                    "smax": smax
                },
                folder=folder
            )

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

            # raise Exception("Test error RELAX")
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
