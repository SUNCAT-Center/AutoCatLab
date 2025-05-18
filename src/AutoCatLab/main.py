#!/usr/bin/env python3

import click
from AutoCatLab.container import create_container


@click.group()
def cli():
    """AutoCatLab CLI - A simple command-line interface application."""
    pass

@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
def cleanup(config: str):
    """Clean up workflow files and reset database."""
    try:
        run_workflow(config, command_step='cleanup')
    except Exception as e:
        raise click.Abort()

# autocatlab start-dft --config config.json
@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
def start_dft(config: str):
    """Start DFT calculations workflow."""
    try:
        run_workflow(config, command_step='start-dft') 
    except Exception as e:
        raise click.Abort()

@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
def resume_dft(config: str):
    """Resume interrupted DFT calculations workflow."""
    try:
        run_workflow(config, command_step='resume-dft')
    except Exception as e:
        raise click.Abort()

@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
def start_icohp(config: str):
    """Start ICOHP calculations workflow."""
    try:
        run_workflow(config, command_step='start-icohp')
    except Exception as e:
        raise click.Abort()

@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
def resume_icohp(config: str):
    """Resume interrupted ICOHP calculations workflow."""
    try:
        run_workflow(config, command_step='resume-icohp')
    except Exception as e:
        raise click.Abort()

@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
@click.argument('calculation_type', required=False)
def show_progress(config: str, calculation_type: str = None):
    """Show progress of calculations.
    
    Args:
        calculation_type (str, optional): Type of calculation (dft/icohp)
    """
    try:
        if calculation_type:
            run_workflow(config, command_step='show-progress', args=[calculation_type])
        else:
            run_workflow(config, command_step='show-progress')
    except Exception as e:
        raise click.Abort()

@cli.command()
@click.option('--config', required=True, help='Path to the configuration file')
@click.argument('calculation_type', required=True)
def show_report(config: str, calculation_type: str):
    """Show calculation report.
    
    Args:
        calculation_type (str): Type of calculation (dft/icohp)
    """
    try:
        run_workflow(config, command_step='show-report', args=[calculation_type])
    except Exception as e:
        raise click.Abort()


@cli.command()
@click.option('--config', '--config-path', required=True, help='Path to the configuration file')
@click.option('--workflow-name', required=True, help='Name of the workflow')
@click.option('--batch-id', required=True, help='ID of the batch to execute')
def execute_batch(config: str, workflow_name: str, batch_id: str):
    """Execute a specific batch of calculations.
    
    Args:
        config (str): Path to the configuration file
        workflow_name (str): Name of the workflow
        batch_id (str): ID of the batch to execute
    """
    try:
        run_executor(config, workflow_name, batch_id)
    except Exception as e:
        raise click.Abort()


def run_executor(config_path: str, workflow_name: str, batch_id: str):
    """Run a specific batch execution.
    
    Args:
        config_path (str): Path to the configuration file
        workflow_name (str): Name of the workflow
        batch_id (str): ID of the batch to execute
    """
    try:
        # Create container with dependencies
        container = create_container(config_path)
        
        # Get executor manager and run batch
        executor_manager = container.get('batch_executor_manager')
        config = container.get('config')
        
        success = executor_manager.execute_batch(config, workflow_name, batch_id)
        if not success:
            raise Exception("Batch execution failed")
            
    except Exception as e:
        raise click.Abort()



def run_workflow(file_path: str = None, command_step: str = None, args: list[str] = None):
    """Run a workflow from a specified configuration file.
    
    Args:
        file_path (str, optional): Path to the workflow configuration file. 
            If not provided, uses default config.
        command_step (str, optional): The workflow command step to execute.
        args (list[str], optional): Additional arguments for the workflow.
    """
    container = create_container(file_path)        
    workflow_manager = container.get('workflow_manager')
    workflow_manager.run(command_step, args)


if __name__ == '__main__':
    cli() 