"""ICOHP executor implementation."""
import traceback
from datetime import datetime
import os
from pathlib import Path
import subprocess
from typing import Any, Dict
import yaml
from ase.io import read
from yaml import Loader
import numpy as np
import shutil
from ase.io.vasp import read_vasp_out

# from db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
# from executor.util.calculation_helper import write_lobsterIn
from AutoCatLab.executor.calculation_executor import CalculationExecutor
from AutoCatLab.executor.util.util import write_lobsterIn, get_icohp_vs_d, get_madelung_energies, get_doe
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import get_bool_env
from AutoCatLab.executor.util.util import get_icohp_matrix


class ICOHPExecutor(CalculationExecutor):
    """Executor for ICOHP calculations."""

    def save_result(self, config: Dict[str, Any], workflow_detail: WorkflowDetail, batch_detail: WorkflowBatchDetail,
                    execution: WorkflowBatchExecution) -> bool:
        folder = execution.result_material_dir
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'constant'))
        orbital_map = yaml.load(open(os.path.join(base_path, 'valence_orbital_mapping_new.yaml')), Loader)
        orbital_map2 = yaml.load(open(os.path.join(base_path, 'valence_orbital_mapping_new.yaml')), Loader)
        orbital_map3 = yaml.load(open(os.path.join(base_path, 'valence_orbital_mapping_new_metal_d_o2p.yaml')), Loader)
        orbital_map2["O"] = "2s 2p"

        atoms = read(os.path.join(folder, 'OUTCAR'))
        species = atoms.symbols.species()
        orbital = {}
        orbital2 = {}
        orbital3 = {}
        for item in species:
            orbital[item] = orbital_map[item].split()
        for item in species:
            orbital2[item] = orbital_map2[item].split()
        for item in species:
            orbital3[item] = orbital_map3[item].split()

        I_matrix = get_icohp_matrix(atoms, str(folder) + '/ICOHPLIST.lobster')  # take all orbitals for now
        I_sum = np.sum(I_matrix, axis=1)
        I_matrix_s_d = get_icohp_matrix(atoms, str(folder) + '/ICOHPLIST.lobster',
                                        orbitals=orbital)  # take all orbitals for now
        I_sum_s_d = np.sum(I_matrix_s_d, axis=1)
        I_matrix_s_d_o_2s_2p = get_icohp_matrix(atoms, str(folder) + '/ICOHPLIST.lobster',
                                                orbitals=orbital2)
        I_sum_s_d_o_2s_2p = np.sum(I_matrix_s_d_o_2s_2p, axis=1)
        I_matrix_d_o_2p = get_icohp_matrix(atoms, str(folder) + '/ICOHPLIST.lobster',
                                           orbitals=orbital3)
        I_sum_d_o2p = np.sum(I_matrix_d_o_2p, axis=1)
        distances, icohps, pairs = get_icohp_vs_d(atoms, str(folder) + '/ICOHPLIST.lobster')
        doe = get_doe(str(folder) + '/DensityOfEnergy.lobster')
        madelung_energies = get_madelung_energies(str(folder) + '/MadelungEnergies.lobster')
        eband = 0

        for index, row in doe.iterrows():
            if row[0] == 0:
                eband = row["total_int_up-down"]
        doe = doe.to_numpy()
        doe = doe.astype(np.cfloat)

        # 6. Save to ASE DB
        with self.container.get("result_ase_db_connector") as connector:
            db = connector.db
            rows = list(db.select(key=str(Path(folder).parent)))
            if rows:
                db.update(
                    rows[0].id,
                    atoms,
                    key=str(Path(folder).parent),
                    data={
                        execution.calculation_name: {
                            'icohp_matrix': I_matrix,
                            'icohp_sum': I_sum,
                            'icohp_matrix_s_d': I_matrix_s_d,
                            'icohp_sum_s_d': I_sum_s_d,
                            'icohp_sum_s_d_o_2s_2p': I_sum_s_d_o_2s_2p,
                            'icohp_sum_d_o2p': I_sum_d_o2p,
                            'distances': distances,
                            'icohps': icohps,
                            'pairs': pairs,
                            'doe_energy': doe[:, 0],
                            'doe_up': doe[:, 1],
                            'doe_down': doe[:, 2],
                            'idoe_up': doe[:, 3],
                            'idoe_down': doe[:, 4],
                            'eband': float(eband),
                            'madelung_energies': madelung_energies,
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
                'OUTCAR',
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
                dest_file = os.path.join(dest_dir, file)
                if os.path.exists(src_file):
                    if file == 'OUTCAR':
                        shutil.copy2(src_file, dest_file)
                    else:
                        shutil.move(src_file, dest_file)

            self.logger.info("Successfully moved LOBSTER output files to destination directory")
            self.logger.info(f"Successfully completed LOBSTER calculation for material {execution.material_name}")
            self.logger.info(f"LOBSTER output files generated in {source_dir}")

            # raise Exception("Test error ICOHP")

            self.save_result(config, workflow_detail, batch_detail, execution)
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
