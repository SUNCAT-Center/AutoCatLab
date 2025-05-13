"""Workflow manager for AutoCatLab."""
from typing import Any, Dict, Optional

from db.models import WorkflowDetail
from .commands.command_base import CommandBase
from .commands.command_dft_manager import StartDFTManager, ResumeDFTManager
from .commands.command_icohp_manager import StartICOHPManager, ResumeICOHPManager
from .commands.command_progress_manager import ShowProgressManager
from .commands.command_report_manager import ShowReportManager
from .commands.command_cleanup_manager import CleanupManager

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
        
    def get_command(self, command_type: str) -> Optional[CommandBase]:
        """Get command instance based on type.
        
        Args:
            command_type (str): Type of command to create
            
        Returns:
            Optional[CommandBase]: Command instance or None if type not supported
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
      
        try:
            command = self.get_command(command_step)
            return command.execute(args)
        except Exception as e:
            self.logger.error(f"Error running workflow: {str(e)}")
            return False
