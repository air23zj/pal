from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declared_attr
from ..core.database import Base

class BaseModel(Base):
    """Base model class that includes audit fields and soft delete."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    @declared_attr
    def __tablename__(cls):
        """Generate __tablename__ automatically from class name."""
        return cls.__name__.lower()

    def soft_delete(self):
        """Soft delete the record."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None

    def update(self, **kwargs):
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow() 