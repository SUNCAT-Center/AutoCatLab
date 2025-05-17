"""Batch processor for AutoCatLab."""
import json
import math
from typing import Dict, Any, List, Tuple
from pathlib import Path

from AutoCatLab.container_base import Container
from AutoCatLab.db.models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution
from AutoCatLab.util.util import copy_file


class BatchProcessor:
    """Processes batches for AutoCatLab."""

    def __init__(self, container: Container):
        """Initialize batch processor.
        
        Args:
            container (Container): Service container
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')
        self.batch_crud = container.get('batch_crud')
        self.execution_crud = container.get('execution_crud')
        self.job_script_generator = container.get('job_script_generator')

    def process(self, workflow_detail: WorkflowDetail, calculation: str, input_data: List[Dict[str, Any]]) -> Tuple[
        List[WorkflowBatchDetail], List[WorkflowBatchExecution]]:
        """Process batches for a calculation.
        
        Args:
            calculation (str): Calculation type
            dirs (List[Path]): List of directories
            submission_detail (Dict[str, Any]): Submission details
            
        Returns:
            List[Dict[str, Any]]: List of batch configurations
        """
        self.logger.info(f"Processing batches for {calculation}")
        batch_size = self.config['batch_size']
        batch_count = math.ceil(len(input_data) / batch_size)
        batches = []
        connector = self.container.get('sqlite_connector')
        for i in range(batch_count):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(input_data))
            batch_data = input_data[start_idx:end_idx]

            workflow_batch_data = {
                'workflow_unique_name': workflow_detail.calc_unique_name,
                'calculation_type': calculation,
                'materials': [material['name'] for material in batch_data],
                'result_batch_dir': Path(self.config[
                                             'workflow_output_directory']) / workflow_detail.calc_unique_name / 'results' / f'batch_{i + 1}_{start_idx}_{end_idx}',
                'script_path': Path(self.config[
                                        'workflow_output_directory']) / workflow_detail.calc_unique_name / 'scripts' / f'batch_{i + 1}_{calculation}_{start_idx}_{end_idx}.sh'
            }

            workflow_batch_detail = self.batch_crud.create_batch(connector.get_session(), workflow_batch_data)

            script_path = self.job_script_generator.generate_script(workflow_detail, workflow_batch_detail)
            workflow_batch_executions = []
            for material in batch_data:
                material_dir = Path(workflow_batch_detail.result_batch_dir) / material['name']
                for calculation_step in self.config['workflow_steps'][calculation]['calculations']:
                    calculation_step_dir = material_dir / calculation_step
                    calculation_step_dir.mkdir(parents=True, exist_ok=True)
                    if calculation_step in ['BULK_DFT_RELAX', 'SURFACE_DFT_RELAX', 'POINT_DFT_RELAX']:
                        copy_file(material['json_file_path'], calculation_step_dir / 'start.json')

                    workflow_batch_execution_data = {
                        'workflow_unique_name': workflow_detail.calc_unique_name,
                        'batch_id': workflow_batch_detail.batch_id,
                        'material_name': material['name'],
                        'result_material_dir': str(calculation_step_dir),
                        'calculation_name': calculation_step,
                        'script_path': str(script_path)
                    }

                    workflow_batch_execution = self.execution_crud.create_execution(connector.get_session(),
                                                                                    workflow_batch_execution_data)
                    workflow_batch_executions.append(workflow_batch_execution)
            batches.append(workflow_batch_detail)

        return batches, workflow_batch_executions

    def process_icohp(self, workflow_detail: WorkflowDetail, batches: List[WorkflowBatchDetail], calculation: str) -> \
    Tuple[List[WorkflowBatchDetail], List[WorkflowBatchExecution]]:

        self.logger.info(f"Processing batches for {calculation}")
        connector =  self.container.get('sqlite_connector')
        created_batches = []
        for batch in batches:
            batch_script_dir_name = batch.result_batch_dir.split('/')[-1]
            batch_script_path = batch.script_path.replace(batch.calculation_type, 'icohp')
            materials = json.loads(batch.materials)
            workflow_batch_data = {
                'workflow_unique_name': workflow_detail.calc_unique_name,
                'calculation_type': calculation,
                'materials': materials,
                'result_batch_dir': Path(batch.result_batch_dir).parent / batch_script_dir_name,
                'script_path': batch_script_path
            }

            workflow_batch_detail = self.batch_crud.create_batch(connector.get_session(), workflow_batch_data)

            script_path = self.job_script_generator.generate_script(workflow_detail, workflow_batch_detail)
            workflow_batch_executions = []
            for material in materials:
                material_dir = Path(workflow_batch_detail.result_batch_dir) / material
                for calculation_step in self.config['workflow_steps'][calculation]['calculations']:
                    calculation_step_dir = material_dir / calculation_step
                    calculation_step_dir.mkdir(parents=True, exist_ok=True)
                    if calculation_step in ['BULK_DFT_RELAX', 'SURFACE_DFT_RELAX', 'POINT_DFT_RELAX']:
                        copy_file(material['json_file_path'], calculation_step_dir / 'start.json')

                    workflow_batch_execution_data = {
                        'workflow_unique_name': workflow_detail.calc_unique_name,
                        'batch_id': workflow_batch_detail.batch_id,
                        'material_name': material,
                        'result_material_dir': str(calculation_step_dir),
                        'calculation_name': calculation_step,
                        'script_path': script_path
                    }

                    workflow_batch_execution = self.execution_crud.create_execution(connector.get_session(),
                                                                                    workflow_batch_execution_data)
                    workflow_batch_executions.append(workflow_batch_execution)
            created_batches.append(workflow_batch_detail)

        return created_batches, workflow_batch_executions
