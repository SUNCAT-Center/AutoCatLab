"""DFT DOS executor implementation."""
import json
import traceback
from datetime import datetime
import os
import numpy as np

from pathlib import Path
import subprocess
from typing import Any, Dict

import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io.vasp import read_vasp_out, read_vasp_xml
from pymatgen.io.vasp import Vasprun

from AutoCatLab.executor.calculation_executor import CalculationExecutor
from ase.io import read
from ase.calculators.vasp import Vasp
from AutoCatLab.executor.util.util import get_pdos_data
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import get_bool_env


class DFTDOSExecutor(CalculationExecutor):
    """Executor for DFT DOS calculations."""

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
        pdos_data, center_tm_d, center_ptm_p, center_o_2p = get_pdos_data(execution)

        # 6. Save to ASE DB
        with self.container.get("result_ase_db_connector") as connector:
            db = connector.db
            rows = list(db.select(key=str(Path(folder).parent)))
            if rows:
                db.update(rows[0].id,
                    atoms,
                    key=str(Path(folder).parent),
                    data={
                        execution.calculation_name: {
                            "vasp_functional": json.loads(incar_params).get("GGA", "PBE"),
                            "workflow_name": workflow_detail.calc_unique_name,
                            "batch_id": batch_detail.batch_id,
                            "vasp_version": vasp_version,
                            "incar": incar_params,
                            "volume": volume,
                            "mass": mass,
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
                            "charges": charges,
                            "fmax": fmax,
                            "smax": smax,
                            'd-band_center_tm': center_tm_d,
                            'p-band_center_ptm': center_ptm_p,
                            'p-center_o_2p': center_o_2p,
                            'pdos_data': pdos_data
                        }
                    },
                    folder=str(Path(folder).parent)
                )

        return True

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
            # self.logger.info(f"Executing DFT DOS for {execution.material_name}")
            #
            # dir = execution.result_material_dir
            # restart_json = Path(dir) / "restart.json"
            # calculation_name = execution.calculation_name
            # submission_detail = config['workflow_steps'][batch_detail.calculation_type]['submission_detail']
            # nTask = submission_detail['nTask']
            # cpusPertask = submission_detail['cpusPertask']
            # gpu = submission_detail['gpu']
            # is_bulk = "BULK" in calculation_name
            #
            # command = 'srun -n ' + str(nTask) + ' -c ' + str(
            #     cpusPertask) + ' --cpu-bind=cores --gpu-bind=none -G ' + str(gpu) + ' vasp_std'
            #
            # atoms = read(restart_json)
            # initial_magmoms = get_initial_magmoms(atoms)
            # atoms.set_initial_magnetic_moments(initial_magmoms)
            # if not is_bulk:
            #     atoms.pbc = [1, 1, 1]
            #
            # kpoints = get_kpoints(atoms, effective_length=60, bulk=is_bulk)
            # user_luj = config['user_luj_values']
            # LUJ_values = get_LUJ_values(atoms, user_luj)
            #
            # nbands_cohp = get_nbands_cohp(directory=dir + '/')
            #
            # vasp_params = config['workflow_step_parameters'][calculation_name]
            #
            # vasp_params.update({
            #     'command': command,
            #     'directory': dir,
            #     'kpts': kpoints,
            #     'ldau_luj': LUJ_values,
            #     'nbands': nbands_cohp
            # })
            #
            # calc = Vasp(**vasp_params)
            #
            # atoms.set_calculator(calc)
            #
            # if not get_bool_env('local_dev'):
            #     atoms.get_potential_energy()
            #     potcar_path = Path(dir) / 'POTCAR'
            #     subprocess.run(['sed', '-i', '/SHA256/d; /COPYR/d', str(potcar_path)], check=True)
            # else:
            #     self.logger.info("Running in local development mode. Skipping DFT DOS.")
            #
            # self.logger.info("Successfully processed POTCAR file")
            # raise Exception("Test error")
            self.save_result(config, workflow_detail, batch_detail, execution)
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
