import os
from pathlib import Path
from typing import Dict, List, Optional

from container_base import Container
from db.models import WorkflowBatchDetail, WorkflowDetail


class JobScriptGenerator:
    def __init__(self, config: Dict, container: Container):
        """
        Initialize the job script generator.
        
        Args:
            config: Configuration dictionary
            logger: Optional logger instance
        """
        self.config = config
        self.logger = container.get('logger')
    
    def generate_script(self, workflow_detail: WorkflowDetail, workflow_batch_detail: WorkflowBatchDetail) -> str:
       
        step_config = self.config['workflow_steps'][workflow_batch_detail.calculation_type]
        scheduler_config = step_config['scheduler']
        scheduler_type = scheduler_config['type']
        prepend_commands = scheduler_config.get('prepend_commands', [])
        batch_script_file_name_prefix = workflow_batch_detail.script_path.split('/')[-1].split('.')[0]
        script_dir = Path(workflow_batch_detail.script_path).parent
        script_dir.mkdir(parents=True, exist_ok=True)

        script_lines = ["#!/bin/bash"]
        
        # Add scheduler-specific header
        if scheduler_type == 'slurm':
            script_lines.extend(self._generate_slurm_header(batch_script_file_name_prefix, step_config, workflow_detail.calc_unique_name, script_dir))
        elif scheduler_type == 'pbs':
            script_lines.extend(self._generate_pbs_header(batch_script_file_name_prefix, step_config, workflow_detail.calc_unique_name, script_dir))
        else:
            raise ValueError(f"Unsupported scheduler type: {scheduler_type}")
        
        # Add prepend commands
        script_lines.extend(prepend_commands)
        script_lines.append("")  
        
        # Add execution command
        script_lines.append(f"autocatlab execute-batch --batch-id {workflow_batch_detail.batch_id} --workflow-name {workflow_detail.calc_unique_name} --config-path {workflow_detail.config_path}")
        
        script_content = "\n".join(script_lines)

        
        script_path = workflow_batch_detail.script_path
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path
    
    def _generate_slurm_header(self, batch_script_file_name_prefix:str, step_config: Dict, workflow_id: str, script_dir: str) -> List[str]:
        self.logger.info(f"Step config: {step_config}")
        
        """Generate SLURM-specific header for the job script."""
        header = [
            f"#SBATCH --job-name=workflow_{workflow_id}_{batch_script_file_name_prefix}",
            f"#SBATCH -e {script_dir}/{batch_script_file_name_prefix}_error.log",
            f"#SBATCH -o {script_dir}/{batch_script_file_name_prefix}_output.log"
        ]
        
        submission_detail = step_config.get('submission_detail', {})
        
        if submission_detail and 'gpu_queue' in submission_detail and submission_detail['gpu_queue'] is not None:
            self.logger.info("Using GPU settings")
            header.extend([
                f"#SBATCH -q {submission_detail['gpu_queue']}",
                f"#SBATCH -t {submission_detail['time']}",
                f"#SBATCH -N {submission_detail['node']}",
                f"#SBATCH -G {submission_detail['gpu']}",
                "#SBATCH -C gpu",
                "#SBATCH --exclusive"
            ])
            
            # Add nTask and cpusPertask if present and not None
            if ('nTask' in submission_detail and submission_detail['nTask'] is not None and 
                'cpusPertask' in submission_detail and submission_detail['cpusPertask'] is not None):
                header.extend([
                    f"#SBATCH --ntasks={submission_detail['nTask']}",
                    f"#SBATCH --cpus-per-task={submission_detail['cpusPertask']}"
                ])
        # Add CPU-specific settings if present
        elif submission_detail and 'cpu_queue' in submission_detail and submission_detail['cpu_queue'] is not None:
            self.logger.info("Using CPU settings")
            header.extend([
                f"#SBATCH -q {submission_detail['cpu_queue']}",
                f"#SBATCH -t {submission_detail['cpu_time']}",
                f"#SBATCH -N {submission_detail['cpu_node']}",
                "#SBATCH -C cpu",
                "#SBATCH --exclusive"
            ])
        else:
            self.logger.warning(f"No valid submission details found in step config: {step_config}")
        
        return header
    
    def _generate_pbs_header(self,batch_script_file_name_prefix, step_config: Dict, workflow_id: str) -> List[str]:
        """Generate PBS-specific header for the job script."""
        header = [
            f"#PBS -N workflow_{workflow_id}_{batch_script_file_name_prefix}",
            "#PBS -l walltime=24:00:00",
            "#PBS -l nodes=1:ppn=1"
        ]
        
        # Get submission details from step config
        submission_detail = step_config.get('submission_detail', {})
        self.logger.info(f"Submission detail: {submission_detail}")
        
        # Add GPU-specific settings if present
        if submission_detail and 'gpu_queue' in submission_detail:
            self.logger.info("Using GPU settings")
            header.extend([
                f"#PBS -q {submission_detail['gpu_queue']}",
                f"#PBS -l walltime={submission_detail['time']}",
                f"#PBS -l nodes={submission_detail['node']}:gpus={submission_detail['gpu']}",
                "#PBS -l feature=gpu",
                "#PBS -l place=excl"
            ])
            
            # Add nTask and cpusPertask if present and not None
            if ('nTask' in submission_detail and submission_detail['nTask'] is not None and 
                'cpusPertask' in submission_detail and submission_detail['cpusPertask'] is not None):
                header.extend([
                    f"#PBS -l nodes={submission_detail['node']}:ppn={submission_detail['nTask'] * submission_detail['cpusPertask']}"
                ])
        # Add CPU-specific settings if present
        elif submission_detail and 'cpu_queue' in submission_detail:
            self.logger.info("Using CPU settings")
            header.extend([
                f"#PBS -q {submission_detail['cpu_queue']}",
                f"#PBS -l walltime={submission_detail['cpu_time']}",
                f"#PBS -l nodes={submission_detail['cpu_node']}",
                "#PBS -l feature=cpu",
                "#PBS -l place=excl"
            ])
        else:
            self.logger.warning(f"No valid submission details found in step config: {step_config}")
        
        return header 