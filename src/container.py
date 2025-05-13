"""Container factory for dependency injection."""
from pathlib import Path

from container_base import Container
from executor.batch_executor_manager import BatchExecutorManager
from initializer.batch_processor import BatchProcessor
from initializer.job_script_generator import JobScriptGenerator
from initializer.input_processor import InputProcessor
from initializer.job_processor import JobProcessor
from util.util import setup_logger, get_config
from workflow.workflow_manager import WorkflowManager
from db.connectors import ASEDBConnector, SQLiteConnector
from db.crud import BatchCRUD, ExecutionCRUD, WorkflowCRUD

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

    ase_db_connector = ASEDBConnector(Path(config['workflow_output_directory']) / config['workflow_input']['value'])
    container.set('ase_db_connector', ase_db_connector)

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