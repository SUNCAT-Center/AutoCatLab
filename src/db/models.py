"""Database models for AutoCatLab."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class WorkflowDetail(Base):
    """Model for workflow details."""
    __tablename__ = 'workflow_details'
    
    calc_unique_name = Column(String(255), primary_key=True)
    config_path = Column(String(255), nullable=False)
    status = Column(String(50), default='created')
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    success = Column(Boolean, default=True)
    error = Column(Text)
    
    # Relationships
    batches = relationship("WorkflowBatchDetail", back_populates="workflow")
    executions = relationship("WorkflowBatchExecution", back_populates="workflow")

class WorkflowBatchDetail(Base):
    """Model for workflow batch details."""
    __tablename__ = 'workflow_batch_details'
    
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_unique_name = Column(String(36), ForeignKey('workflow_details.calc_unique_name'), nullable=False)
    materials = Column(Text, nullable=False)  # JSON string of material names
    calculation_type = Column(Text, nullable=False)  # DFT or ICOHP
    result_batch_dir = Column(String(255), nullable=False)  # Batch directory path
    script_path = Column(String(255), nullable=False)  # Script path
    job_id = Column(String(255))
    status = Column(String(50), default='created')
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    success = Column(Boolean, default=True)
    error = Column(Text)
    
    # Relationships
    workflow = relationship("WorkflowDetail", back_populates="batches")
    executions = relationship("WorkflowBatchExecution", back_populates="batch")

class WorkflowBatchExecution(Base):
    """Model for workflow batch executions."""
    __tablename__ = 'workflow_batch_executions'
    
    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_unique_name = Column(String(36), ForeignKey('workflow_details.calc_unique_name'), nullable=False)
    batch_id = Column(Integer, ForeignKey('workflow_batch_details.batch_id'), nullable=False)
    material_name = Column(String(255), nullable=False)
    result_material_dir = Column(String(255), nullable=False)
    script_path = Column(String(255), nullable=False)
    calculation_name = Column(String(255), nullable=False)
    status = Column(String(50), default='created')
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    success = Column(Boolean, default=True)
    error = Column(Text)
    
    # Relationships
    workflow = relationship("WorkflowDetail", back_populates="executions")
    batch = relationship("WorkflowBatchDetail", back_populates="executions") 