"""Database connectors for AutoCatLab."""
import sqlite3
from pathlib import Path
from typing import Optional
from ase.db import connect as ase_connect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

class SQLiteConnector:
    """SQLite database connector."""
    
    def __init__(self, db_path: Path):
        """Initialize SQLite connector.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
        self.session = None
        
    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """Get a database session. Reuses existing session if available.
        
        Returns:
            Session: SQLAlchemy session
        """
        if self.session is None:
            self.session = self.SessionLocal()
        return self.session

    def close_session(self) -> None:
        """Close the current database session."""
        if self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        """Context manager entry."""
        self.get_session()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_session()
        

class ASEDBConnector:
    """ASE database connector."""
    
    def __init__(self, db_path: str):
        """Initialize ASE database connector.
        
        Args:
            db_path (str): Path to ASE database file
        """
        self.db_path = Path(db_path)
        self.db = None
        
    def connect(self) -> None:
        """Connect to ASE database."""
        self.db = ase_connect(str(self.db_path))
        
    def disconnect(self) -> None:
        """Disconnect from ASE database."""
        if self.db:
            del self.db
            self.db = None
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect() 