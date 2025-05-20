"""Input processor for AutoCatLab."""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

import ase.db
from ase import Atoms
from ase.io import read, write
from mp_api.client import MPRester
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor, MSONAtoms, Atoms

from AutoCatLab.client.mpi_api import MPIClient
from AutoCatLab.container_base import Container
from AutoCatLab.db.models import WorkflowDetail
from AutoCatLab.util.util import prompt_yes_no, create_directory, copy_file
from catkit.gen.surface import SlabGenerator


class InputProcessor:
    """Processes input data for calculations."""

    def __init__(self, container: Container):
        """Initialize input processor.
        
        Args:
            container (Container): Service container
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')

    def _get_timestamped_name(self, original_name: str) -> str:
        """
        Add timestamp suffix to a filename.
        
        Args:
            original_name: Original filename without extension
            
        Returns:
            Filename with timestamp suffix
        """
        return original_name

    def process(self, workflow_detail: WorkflowDetail) -> list[Dict[str, Any]]:
        """Process input for a calculation.
        
        Args:
            calculation (str): Calculation type
            params (Dict[str, Any]): Calculation parameters
            
        Returns:
            Dict[str, Any]: Processed input data
        """
        self.logger.info(f"Processing input for {workflow_detail.calc_unique_name}")
        materials, failed_input = None, []
        match self.config['workflow_input']['type']:
            case "location":
                materials, failed_input = self._process_location_input()
            case "mp_mpids":
                materials, failed_input = self._process_mp_input()
            case "mpi_custom_query":
                materials, failed_input = self._process_mpi_custom_query()
            case "ase_db":
                materials, failed_input = self._process_ase_db_input()
            case _:
                raise ValueError(f"Unsupported input type: {self.config['workflow_input']['type']}")

        if len(materials) == 0:
            self.logger.error(
                f"No valid materials found in input directory. Please check the input directory and try again.")
            raise ValueError("No valid materials found in input directory")

        if len(failed_input) > 0:
            self.logger.error(f"Failed to process {len(failed_input)} files. Please correct the files and try again.")
            raise ValueError("Failed to process some files in input directory")

        for material in materials:
            create_directory(material['raw_file_path'].parent)
            create_directory(material['json_file_path'].parent)
            if self.config['workflow_input']['type'] == "location":
                copy_file(material['raw_file'], material['raw_file_path'])
            else:
                write(str(material['raw_file_path']), material['structure'], format='cif')
            write(str(material['json_file_path']), material['structure'], format='json')
        self.logger.info(f"Processed {len(materials)} materials")
        return materials

    def generate_surface_input_files(self):
        input_dir = Path(self.config['workflow_input']['value'])
        new_input_dir = input_dir.parent / 'new_input_directory'
        create_directory(new_input_dir)
        thickness = 12
        for ext in [".cif", ".json"]:
            files = list(input_dir.glob(f"*{ext}"))
            for file in files:
                atoms = read(str(file))
                for miller in [(1, 0, 0), (0, 1, 0), (1, 1, 0), (1, 1, 1), (2, 1, 1)]:
                    miller_str = ''.join(map(str, miller))  # Convert (1,0,0) to "100"
                    gen = SlabGenerator(
                        atoms,
                        miller_index=miller,
                        layers=thickness,
                        layer_type='ang',
                        standardize_bulk=True,
                        symmetric=True,
                        stoich=True,
                        fixed=0,
                        vacuum=7.5)

                    miller_slabs = gen.get_slabs()

                    for i, slab in enumerate(miller_slabs):
                        file_name = file.stem + f"_SURFACE_{miller_str}_{i + 1}"
                        file_path = new_input_dir / f"{file_name}.json"
                        write(file_path, slab)
                    copy_file(file, new_input_dir)
        self.config['workflow_input']['value'] = new_input_dir

    def _process_location_input(self) -> tuple[list[Dict[str, Any]], list[str]]:
        """Process location input."""
        if self.config['is_bulk_surface']:
            self.generate_surface_input_files()

        input_dir = Path(self.config['workflow_input']['value'])
        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        materials = []
        failed_files = []
        for ext in [".cif", ".json"]:
            files = list(input_dir.glob(f"*{ext}"))

            for file in files:
                try:
                    timestamped_name = self._get_timestamped_name(file.stem)
                    raw_file_path = Path(self.config['workflow_output_directory']) / self.config[
                        'workflow_unique_name'] / 'input' / 'raw' / f"{timestamped_name}{file.suffix}"
                    json_file_path = Path(self.config['workflow_output_directory']) / self.config[
                        'workflow_unique_name'] / 'input' / 'processed' / f"{timestamped_name}.json"

                    materials.append({
                        "name": timestamped_name,
                        "structure": read(str(file)),
                        "raw_file": file,
                        "raw_file_path": raw_file_path,
                        "json_file_path": json_file_path,
                    })
                except Exception as e:
                    self.logger.warning(f"Error processing file {file}: {str(e)}")
                    failed_files.append(str(file))

        return materials, failed_files

    def _process_mp_input(self) -> list[Dict[str, Any]]:
        """
        Process input from Materials Project.
        
        Returns:
            List of material dictionaries
        """
        if not self.config['workflow_input']['mp_api_key']:
            raise ValueError("Materials Project API key is required for MP input type")

        with MPRester(self.config['workflow_input']['mp_api_key']) as mpr:
            mp_ids = self.config['workflow_input']['value'].split(",")
            mp_ids = [id.strip() for id in mp_ids]

            materials = []
            failed_ids = []
            for mp_id in mp_ids:
                try:
                    mp_structure = mpr.get_structure_by_material_id(mp_id)
                    timestamped_id = self._get_timestamped_name(mp_id)

                    # raw_file_path = Path(self.config['workflow_output_directory']) /  f"{timestamped_id}.cif"
                    # json_file_path = Path(self.config['workflow_output_directory']) / f"{timestamped_id}.json"

                    raw_file_path = Path(self.config['workflow_output_directory']) / self.config[
                        'workflow_unique_name'] / 'input' / 'raw' / f"{timestamped_id}.cif"
                    json_file_path = Path(self.config['workflow_output_directory']) / self.config[
                        'workflow_unique_name'] / 'input' / 'processed' / f"{timestamped_id}.json"

                    materials.append({
                        "name": timestamped_id,
                        "structure": AseAtomsAdaptor.get_atoms(mp_structure),
                        "raw_file_path": raw_file_path,
                        "json_file_path": json_file_path,
                    })

                except Exception as e:
                    self.logger.warning(f"Error processing MP ID {mp_id}: {str(e)}")
                    failed_ids.append(mp_id)
                    continue

            if not materials:
                raise ValueError("No valid materials found from Materials Project")

            return materials, failed_ids

    def _process_mpi_custom_query(self) -> tuple[
        list[dict[str, str | MSONAtoms | Atoms | Atoms | Any]], list[str | Any]]:
        """
        Process input from MPI custom query.
        
        Returns:
            List of material dictionaries
        """
        if not self.config['workflow_input']['mp_api_key']:
            raise ValueError("MPI API key is required for MPI custom query input type")

        client = MPIClient(api_key=self.config['workflow_input']['mp_api_key'])

        results = client.execute_query(self.config['workflow_input']['value'])

        materials = []
        failed_ids = []
        for idx, result in enumerate(results):
            try:
                material_id = result.get("material_id", f"mpi_query_{idx}")
                timestamped_id = self._get_timestamped_name(material_id)

                structure_dict = result["structure"]
                structure = Structure.from_dict(structure_dict)

                structure = AseAtomsAdaptor.get_atoms(structure)

                raw_file_path = self.config['workflow_output_directory'] / f"{timestamped_id}.cif"
                json_file_path = self.config['workflow_output_directory'] / f"{timestamped_id}.json"
                materials.append({
                    "name": timestamped_id,
                    "structure": structure,
                    "raw_file_path": raw_file_path,
                    "json_file_path": json_file_path,
                })

            except Exception as e:
                self.logger.warning(f"Error processing MPI query result {idx}: {str(e)}")
                failed_ids.append(idx)
                continue

        if not materials:
            raise ValueError("No valid materials found from MPI query")

        return materials, failed_ids

    def _process_ase_db_input(self) -> tuple[list[dict[str, str | Path | Any]], list[Any]]:
        """
        Process input from ASE database.
        
        Returns:
            List of material dictionaries
        """
        # if not self.directory_manager:
        #     raise ValueError("Directory manager is required for processing ASE DB input")

        db = ase.db.connect(self.config['workflow_input']['value'])

        # Get all structures from database
        materials = []
        failed_input = []
        for row in db.select():
            try:
                atoms = row.toatoms()
                formula = atoms.get_chemical_formula()
                material_id = f"{formula}"
                timestamped_id = self._get_timestamped_name(material_id)

                raw_file_path = Path(self.config['workflow_output_directory']) / self.config[
                    'workflow_unique_name'] / 'input' / 'raw' / f"{timestamped_id}.json"
                json_file_path = Path(self.config['workflow_output_directory']) / self.config[
                    'workflow_unique_name'] / 'input' / 'processed' / f"{timestamped_id}.json"

                materials.append({
                    "name": timestamped_id,
                    "structure": atoms,
                    "raw_file_path": raw_file_path,
                    "json_file_path": json_file_path,
                })

            except Exception as e:
                self.logger.warning(f"Error processing row {row.id}: {str(e)}")
                failed_input.append(row.id)
                continue

        if not materials:
            raise ValueError("No valid materials found in ASE database")

        return materials, failed_input
