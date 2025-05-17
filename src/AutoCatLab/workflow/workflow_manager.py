"""Workflow manager for AutoCatLab."""
from typing import Any, Optional

from .commands.workflow_base import WorkflowBase
from .commands.cleanup_workflow import CleanupManager
from .commands.dft_workflow import StartDFTManager, ResumeDFTManager
from .commands.icohp_workflow import StartICOHPManager, ResumeICOHPManager
from .commands.progress_workflow import ShowProgressManager
from .commands.report_workflow import ShowReportManager


class WorkflowManager:
    """Manages workflow execution."""
    
    def __init__(self, container: Any):
        """Initialize workflow manager.
        
        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self.logger = container.get('logger')
        self.config = container.get('config')
        
    def get_command(self, command_type: str) -> Optional[WorkflowBase]:
        """Get command instance based on type.
        
        Args:
            command_type (str): Type of command to create
            
        Returns:
            Optional[WorkflowBase]: Command instance or None if type not supported
        """
        command_map = {
            'start-dft': StartDFTManager,
            'resume-dft': ResumeDFTManager,
            'start-icohp': StartICOHPManager,
            'resume-icohp': ResumeICOHPManager,
            'show-progress': ShowProgressManager,
            'show-report': ShowReportManager,
            'cleanup': CleanupManager
        }
        
        command_class = command_map.get(command_type.lower())
        return command_class(self.container) if command_class else None
    
    def run(self, command_step: str = None, args: list[str] = None) -> Any:
      
        command = self.get_command(command_step)
        return command.execute(args)
