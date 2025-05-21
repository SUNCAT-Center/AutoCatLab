"""Container factory for dependency injection."""
from pathlib import Path

from AutoCatLab.container_base import Container
from AutoCatLab.executor.batch_executor_manager import BatchExecutorManager
from AutoCatLab.initializer.batch_processor import BatchProcessor
from AutoCatLab.initializer.job_script_generator import JobScriptGenerator
from AutoCatLab.initializer.input_processor import InputProcessor
from AutoCatLab.initializer.job_processor import JobProcessor
from AutoCatLab.util.util import setup_logger, get_config
from AutoCatLab.workflow.workflow_manager import WorkflowManager
from AutoCatLab.db.connectors import ASEDBConnector, SQLiteConnector
from AutoCatLab.db.crud import BatchCRUD, ExecutionCRUD, WorkflowCRUD

def create_container(config_path: str = None) -> Container:
    """Create and configure service container.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured container
    """
    container = Container()
    
    # Load configuration
    config = get_config(Path(config_path))
    container.set('config', config)
    
    # Setup logger
    logger = setup_logger(config)
    container.set('logger', logger)
    
    # Database
    sqlite_connector = SQLiteConnector(Path(config['workflow_output_directory']) / 'db/workflow.db')
    container.set('sqlite_connector', sqlite_connector)

    input_ase_db_connector = ASEDBConnector(config['workflow_input']['value'])
    container.set('input_ase_db_connector', input_ase_db_connector)


    result_ase_db_connector = ASEDBConnector(str(Path(config['workflow_output_directory']) / 'db/results.db'))
    container.set('result_ase_db_connector', result_ase_db_connector)

    workflow_crud = WorkflowCRUD()
    container.set('workflow_crud', workflow_crud)

    batch_crud = BatchCRUD()
    container.set('batch_crud', batch_crud)

    execution_crud = ExecutionCRUD()
    container.set('execution_crud', execution_crud)

    # Initializers
    input_processor = InputProcessor(container)
    container.set('input_processor', input_processor)

    job_script_generator = JobScriptGenerator(config, container)
    container.set('job_script_generator', job_script_generator)
    
    batch_processor = BatchProcessor(container)
    container.set('batch_processor', batch_processor)

    job_processor = JobProcessor(container)
    container.set('job_processor', job_processor)
    
    # Workflow
    workflow_manager = WorkflowManager(container)
    container.set('workflow_manager', workflow_manager)

    batch_executor_manager = BatchExecutorManager(container)
    container.set('batch_executor_manager', batch_executor_manager)


    return container 