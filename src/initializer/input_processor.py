"""Input processor for AutoCatLab."""
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any
from client.mpi_api import MPIClient
from container import Container
from db.models import WorkflowDetail
from mp_api.client import MPRester
from ase.io import read, write
from pymatgen.io.ase import AseAtomsAdaptor
import ase.db
import shutil
from pymatgen.core import Structure
from util.util import copy_file, create_directory

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
        return f"{original_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def process(self, workflow_detail: WorkflowDetail) -> list[Dict[str, Any]]:
        """Process input for a calculation.
        
        Args:
            calculation (str): Calculation type
            params (Dict[str, Any]): Calculation parameters
            
        Returns:
            Dict[str, Any]: Processed input data
        """
        self.logger.info(f"Processing input for {workflow_detail.calc_unique_name}")

        match self.config['workflow_input']['type']:
            case "location":
                return self._process_location_input()
            case "mp_mpids":
                return self._process_mp_input()
            case "mpi_custom_query":
                return self._process_mpi_custom_query()
            case "ase_db":
                return self._process_ase_db_input()
            case _:
                raise ValueError(f"Unsupported input type: {self.config['workflow_input']['type']}")

    def _process_location_input(self) -> list[Dict[str, Any]]:
        """Process location input."""
        
        input_dir = Path(self.config['workflow_input']['value'])
        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        materials = []
        for ext in [".cif",".json"]:
            files = list(input_dir.glob(f"*{ext}"))
            
            for file in files:
                try:
                    timestamped_name = self._get_timestamped_name(file.stem)   
                    raw_file = Path(self.config['workflow_output_directory']) / self.config['workflow_name'] / 'input' / 'raw' / f"{timestamped_name}{file.suffix}"
                    json_file = Path(self.config['workflow_output_directory']) / self.config['workflow_name'] / 'input' / 'processed' / f"{timestamped_name}.json"
                    
                    # Create parent directories
                    raw_file.parent.mkdir(parents=True, exist_ok=True)
                    json_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    structure = read(str(file))  # Read from original file
                    
                    copy_file(file, raw_file)
                    write(str(json_file), structure, format='json')

                    materials.append({
                        "name": timestamped_name,
                        "structure": structure,
                        "raw_file_path": str(raw_file),
                        "json_file_path": str(json_file),
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error processing file {file}: {str(e)}")
                    continue
        
        return materials

    def _process_mp_input(self) -> list[Dict[str, Any]]:
        """
        Process input from Materials Project.
        
        Returns:
            List of material dictionaries
        """
        if not self.config['workflow_input']['mp_api_key']:
            raise ValueError("Materials Project API key is required for MP input type")
       
        
        
        try:
            with MPRester(self.config['workflow_input']['mp_api_key']) as mpr:
                # Parse the input value as a list of MP IDs
                mp_ids = self.config['workflow_input']['value'].split(",")
                mp_ids = [id.strip() for id in mp_ids]
                
                materials = []
                for mp_id in mp_ids:
                    try:
                        mp_structure = mpr.get_structure_by_material_id(mp_id)
                        
                        structure = AseAtomsAdaptor.get_atoms(mp_structure)                    
                        timestamped_id = self._get_timestamped_name(mp_id)
                        
                        raw_file = self.config['workflow_output_directory'] /  f"{timestamped_id}.cif"
                        json_file = self.config['workflow_output_directory'] / f"{timestamped_id}.json"
                        
                        create_directory(raw_file)
                        create_directory(json_file)
                        
                        write(str(raw_file), structure, format='cif')
                        write(str(json_file), structure, format='json')

                        materials.append({
                            "name": timestamped_id,
                            "structure": structure,
                            "raw_file_path": str(raw_file),
                            "json_file_path": str(json_file),
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing MP ID {mp_id}: {str(e)}")
                        continue
                
                if not materials:
                    raise ValueError("No valid materials found from Materials Project")
                
                return materials
                
        except Exception as e:
            self.logger.error(f"Error processing MP input: {str(e)}")
            raise

    def _process_mpi_custom_query(self) -> list[Dict[str, Any]]:
        """
        Process input from MPI custom query.
        
        Returns:
            List of material dictionaries
        """
        if not self.config['workflow_input']['mpi_api_key']:
            raise ValueError("MPI API key is required for MPI custom query input type")
              
        try:
            # Import here to avoid circular imp
            
            # Initialize MPI client
            client = MPIClient(api_key=self.config['workflow_input']['mpi_api_key'])
            
            # Execute custom query
            results = client.execute_query(self.config['workflow_input']['value'])
            
            # Process results into material format
            materials = []
            for idx, result in enumerate(results):
                try:
                    material_id = result.get("material_id", f"mpi_query_{idx}")
                    timestamped_id = self._get_timestamped_name(material_id)
                    
                    structure_dict = result["structure"]
                    structure = Structure.from_dict(structure_dict)
                    
                    structure = AseAtomsAdaptor.get_atoms(structure)                    
                    
                    raw_file = self.config['workflow_output_directory'] / f"{timestamped_id}.cif"
                    json_file = self.config['workflow_output_directory'] / f"{timestamped_id}.json"     

                    create_directory(raw_file)
                    create_directory(json_file)
                    
                    write(str(raw_file), structure, format='cif')
                    write(str(json_file), structure, format='json')

                    materials.append({
                        "name": timestamped_id,
                        "structure": structure,
                        "raw_file_path": str(raw_file),
                        "json_file_path": str(json_file),
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error processing MPI query result {idx}: {str(e)}")
                    continue
            
            if not materials:
                raise ValueError("No valid materials found from MPI query")
            
            return materials
            
        except Exception as e:
            self.logger.error(f"Error processing MPI custom query: {str(e)}")
            raise

    def _process_ase_db_input(self) -> list[Dict[str, Any]]:
        """
        Process input from ASE database.
        
        Returns:
            List of material dictionaries
        """
        if not self.directory_manager:
            raise ValueError("Directory manager is required for processing ASE DB input")
            
        try:
                        
            db = ase.db.connect(self.config['workflow_input']['value'])
            
            # Get all structures from database
            materials = []
            for row in db.select():
                try:
                    atoms = row.toatoms()
                    material_id = f"ase_db_{row.id}"
                    timestamped_id = self._get_timestamped_name(material_id)
                    formula = atoms.get_chemical_formula()
                   
                    
                    raw_file =  self.config['workflow_output_directory'] / self.config['workflow_name'] / 'input' / 'raw' / f"{timestamped_id}_{formula}.xyz"
                    json_file = self.config['workflow_output_directory'] / self.config['workflow_name'] / 'input' / 'processed' / f"{timestamped_id}.json"                    
                   
                    create_directory(raw_file)
                    create_directory(json_file)
                    
                    write(str(raw_file), atoms, format='cif')
                    write(str(json_file), atoms, format='json')

                    materials.append({
                        "name": timestamped_id,
                        "structure": atoms,
                        "raw_file_path": str(raw_file),
                        "json_file_path": str(json_file),
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error processing row {row.id}: {str(e)}")
                    continue
            
            if not materials:
                raise ValueError("No valid materials found in ASE database")
            
            return materials
            
        except Exception as e:
            self.logger.error(f"Error processing ASE database input: {str(e)}")
            raise
    