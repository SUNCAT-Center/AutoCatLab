"""CRUD operations for AutoCatLab database."""
from datetime import datetime
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import WorkflowDetail, WorkflowBatchDetail, WorkflowBatchExecution

class WorkflowCRUD:
    """CRUD operations for workflow details."""
    
    @staticmethod
    def create_workflow(db: Session, workflow_data: Dict[str, Any]) -> WorkflowDetail:
        """Create a new workflow."""
        workflow = WorkflowDetail(
            calc_unique_name=workflow_data['calc_unique_name'],
            config_path=workflow_data['config_path'],
            status='created',
            start_time=datetime.now(),
            end_time=None,
            success=None,
            error=None
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow
    
    @staticmethod
    def get_workflow(db: Session, calc_unique_name: str) -> Optional[WorkflowDetail]:
        """Get workflow by ID."""
        
        return db.query(WorkflowDetail).filter(WorkflowDetail.calc_unique_name == calc_unique_name).first()
    
    @staticmethod
    def update_workflow_status(db: Session, calc_unique_name: str, status: str, success: bool = True, error: str = None) -> Optional[WorkflowDetail]:
        """Update workflow status."""
        workflow = WorkflowCRUD.get_workflow(db, calc_unique_name)
        if workflow:
            workflow.status = status
            workflow.success = success
            workflow.error = error
            if status in ['completed', 'failed']:
                workflow.end_time = datetime.now()
            db.commit()
            db.refresh(workflow)
        return workflow

class BatchCRUD:
    """CRUD operations for workflow batch details."""
    
    @staticmethod
    def create_batch(db: Session, batch_data: Dict[str, Any]) -> WorkflowBatchDetail:
        """Create a new batch."""
        batch = WorkflowBatchDetail(
            workflow_unique_name=batch_data['workflow_unique_name'],
            materials= json.dumps(batch_data['materials']),
            result_batch_dir= str(batch_data['result_batch_dir']),
            script_path= str(batch_data['script_path']),
            calculation_type=batch_data['calculation_type'],
            start_time=datetime.now()
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    
    @staticmethod
    def get_batches(db: Session, workflow_unique_name: str) -> Optional[List[WorkflowBatchDetail]]:
        """Get batches by workflow unique name."""
        return db.query(WorkflowBatchDetail).filter(WorkflowBatchDetail.workflow_unique_name == workflow_unique_name).all()
    
    @staticmethod
    def get_batch(db: Session, batch_id: int) -> Optional[WorkflowBatchDetail]:
        """Get batch by ID."""
        return db.query(WorkflowBatchDetail).filter(WorkflowBatchDetail.batch_id == batch_id).first()
    

    @staticmethod
    def update_batch(db: Session, batch_id: int, batch_data: Dict[str, Any]) -> Optional[WorkflowBatchDetail]:
        """Update batch status."""
        batch = BatchCRUD.get_batch(db, batch_id)
        if batch:
            batch.job_id = batch_data['job_id']
            db.commit()
            db.refresh(batch)
        return batch

class ExecutionCRUD:
    """CRUD operations for workflow batch executions."""
    
    @staticmethod
    def create_execution(db: Session, execution_data: Dict[str, Any]) -> WorkflowBatchExecution:
        """Create a new execution."""
        execution = WorkflowBatchExecution(
            workflow_unique_name=execution_data['workflow_unique_name'],
            batch_id=execution_data['batch_id'],
            material_name=execution_data['material_name'],
            result_material_dir=str(execution_data['result_material_dir']),
            script_path=str(execution_data['script_path']),
            calculation_name=execution_data['calculation_name'],
            start_time=datetime.now()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution
    
    
    @staticmethod
    def get_executions(db: Session, batch_id: int) -> Optional[List[WorkflowBatchExecution]]:
        """Get executions by batch ID."""
        return db.query(WorkflowBatchExecution).filter(
            WorkflowBatchExecution.batch_id == batch_id,
            WorkflowBatchExecution.status != 'completed'
            ).all()
    
    @staticmethod
    def get_execution(db: Session, execution_id: int) -> Optional[WorkflowBatchExecution]:
        """Get execution by ID."""
        return db.query(WorkflowBatchExecution).filter(WorkflowBatchExecution.execution_id == execution_id).first()
    
    @staticmethod
    def update_execution_status(db: Session, execution_id: int, status: str, success: bool = True, error: str = None) -> Optional[WorkflowBatchExecution]:
        """Update execution status."""
        execution = ExecutionCRUD.get_execution(db, execution_id)
        if execution:
            execution.status = status
            execution.success = success
            execution.error = error
            if status in ['completed', 'failed']:
                execution.end_time = datetime.now()
            db.commit()
            db.refresh(execution)
        return execution 