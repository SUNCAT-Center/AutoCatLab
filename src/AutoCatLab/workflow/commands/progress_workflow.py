"""Progress command manager for workflow."""
from typing import Any, Dict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from AutoCatLab.db.models import WorkflowBatchDetail, WorkflowDetail
from .workflow_base import WorkflowBase

class ShowProgressManager(WorkflowBase):
    """Manager for showing workflow progress."""
    
    def validate(self, workflow_detail: WorkflowDetail, args: Dict[str, Any]) -> bool:
        """Validate if progress can be shown."""
        if workflow_detail is None:
            self.logger.error("No workflow found")
            return False
            
        calculation_type = args.get('calculation_type')
        if calculation_type and calculation_type not in ['dft', 'icohp']:
            self.logger.error(f"Invalid calculation type: {calculation_type}")
            return False
            
        return True
    
    def execute(self, args: Dict[str, Any]) -> Any:
        """Show workflow progress with fancy display."""
        try:
            conn = self.container.get('sqlite_connector').get_session()
            workflow_crud = self.container.get('workflow_crud')
            batch_crud = self.container.get('batch_crud')
            
            self.logger.info("Getting workflow details...")
            workflow_detail = workflow_crud.get_workflow(conn, self.container.get('config')['workflow_unique_name'])
            self.logger.info(f"Workflow detail: {workflow_detail}")
            
            calculation_type = args.get('calculation_type')
            
            if not self.validate(workflow_detail, args):
                return False
                
            self.logger.info("Showing workflow progress")
            console = Console()
            
            # Get batches
            self.logger.info("Getting batches...")
            batches = batch_crud.get_batches(conn, workflow_detail.calc_unique_name)
            self.logger.info(f"Found {len(batches)} batches")
            
            if calculation_type:
                batches = [batch for batch in batches 
                          if batch.calculation_type.upper() == calculation_type.upper()]
                self.logger.info(f"Filtered to {len(batches)} batches of type {calculation_type}")

            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="header"),
                Layout(name="batches"),
                Layout(name="failed_executions")
            )

            # Calculate statistics for progress bar
            total_executions = sum(len(batch.executions) for batch in batches)
            completed_executions = sum(len([e for e in batch.executions if e.status == 'completed']) for batch in batches)
            
            self.logger.info(f"Total executions: {total_executions}, Completed: {completed_executions}")
            
            # Create combined header with progress
            header_content = Table.grid(padding=1)
            header_content.add_column(style="bold blue")
            header_content.add_column(style="bold")
            
            # Add workflow info
            header_content.add_row("Workflow:", workflow_detail.calc_unique_name)
            header_content.add_row("Status:", f"[{'green' if workflow_detail.status == 'running' else 'yellow'}]{workflow_detail.status}[/]")
            header_content.add_row("Started:", workflow_detail.start_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # Add progress bar
            progress = Progress(
                SpinnerColumn(),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn()
            )
            task = progress.add_task("Progress", total=total_executions, completed=completed_executions)
            header_content.add_row("Progress:", progress)
            
            layout["header"].update(Panel(header_content, title="Workflow Progress", border_style="blue"))

            # Batches display
            batches_table = Table(show_header=True, header_style="bold magenta")
            batches_table.add_column("Batch ID", style="cyan")
            batches_table.add_column("Type", style="yellow")
            batches_table.add_column("Status", style="green")
            batches_table.add_column("Progress", style="blue")
            batches_table.add_column("Started", style="dim")
            batches_table.add_column("Error", style="red")
            
            self.logger.info("Processing batches for display...")
            for batch in batches:
                batch_completed = len([e for e in batch.executions if e.status == 'completed'])
                batch_total = len(batch.executions)
                progress = f"{batch_completed}/{batch_total}"
                
                status_color = {
                    'completed': 'green',
                    'running': 'yellow',
                    'failed': 'red',
                    'created': 'white'
                }.get(batch.status, 'white')
                
                error_msg = ""
                if batch.status == 'failed':
                    first_failed = next((e for e in batch.executions if e.status == 'failed'), None)
                    if first_failed:
                        error_msg = first_failed.error or "Unknown error"
                
                batches_table.add_row(
                    f"Batch {batch.batch_id}",
                    batch.calculation_type,
                    f"[{status_color}]{batch.status}[/]",
                    progress,
                    batch.start_time.strftime('%H:%M:%S') if batch.start_time else 'N/A',
                    error_msg
                )
            
            layout["batches"].update(Panel(batches_table, title="Batches Progress", border_style="yellow"))

            # Failed executions details
            failed_executions_table = Table(show_header=True, header_style="bold red")
            failed_executions_table.add_column("Batch ID", style="cyan")
            failed_executions_table.add_column("Material", style="yellow")
            failed_executions_table.add_column("Calculation_name", style="yellow")
            failed_executions_table.add_column("Error", style="red")
            failed_executions_table.add_column("Failed At", style="dim")
            
            self.logger.info("Processing failed executions...")
            for batch in batches:
                if batch.status == 'failed':
                    first_failed = next((e for e in batch.executions if e.status == 'failed'), None)
                    if first_failed:
                        failed_executions_table.add_row(
                            f"Batch {batch.batch_id}",
                            first_failed.material_name,
                            first_failed.calculation_name,
                            first_failed.error or "Unknown error",
                            first_failed.end_time.strftime('%H:%M:%S') if first_failed.end_time else 'N/A'
                        )
            
            if failed_executions_table.row_count > 0:
                layout["failed_executions"].update(Panel(failed_executions_table, title="Failed Executions", border_style="red"))
            else:
                layout["failed_executions"].update("")

            # Display everything
            console.print(layout)
            return True
            
        except Exception as e:
            self.logger.error(f"Error showing progress: {str(e)}")
            self.logger.error("Traceback:", exc_info=True)
            return False 