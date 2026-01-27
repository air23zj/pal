from typing import TypeVar, Generic, Type, Optional, List, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi_cache.decorator import cache
from loguru import logger
from contextlib import contextmanager
from ..models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseService(Generic[ModelType]):
    """Base class for all services."""
    
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    @contextmanager
    def transaction(self):
        """Transaction context manager."""
        try:
            yield
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Database transaction failed")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Operation failed: {str(e)}")
            raise

    def _apply_pagination(self, query, skip: int = 0, limit: int = 100):
        """Apply pagination to query."""
        return query.offset(skip).limit(limit)

    def _get_pagination_metadata(self, query, skip: int, limit: int):
        """Get pagination metadata."""
        total = query.count()
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }

    @cache(expire=300)  # Cache for 5 minutes
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            return self.db.query(self.model).filter(
                self.model.id == id,
                self.model.is_deleted == False
            ).first()
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} by ID {id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve record")

    async def create(self, data: dict) -> ModelType:
        """Create a new record."""
        try:
            with self.transaction():
                db_obj = self.model(**data)
                self.db.add(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create record")

    async def update(self, id: int, data: dict) -> Optional[ModelType]:
        """Update a record."""
        try:
            with self.transaction():
                db_obj = await self.get_by_id(id)
                if not db_obj:
                    raise HTTPException(status_code=404, detail="Record not found")
                db_obj.update(**data)
            return db_obj
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update {self.model.__name__} {id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update record")

    async def delete(self, id: int, soft: bool = True) -> bool:
        """Delete a record (soft or hard delete)."""
        try:
            with self.transaction():
                db_obj = await self.get_by_id(id)
                if not db_obj:
                    raise HTTPException(status_code=404, detail="Record not found")
                
                if soft:
                    db_obj.soft_delete()
                else:
                    self.db.delete(db_obj)
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete {self.model.__name__} {id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete record")

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> tuple[List[ModelType], dict]:
        """List records with pagination."""
        try:
            query = self.db.query(self.model)
            if not include_deleted:
                query = query.filter(self.model.is_deleted == False)
            
            # Get pagination metadata before applying limit/offset
            metadata = self._get_pagination_metadata(query, skip, limit)
            
            # Apply pagination
            records = self._apply_pagination(query, skip, limit).all()
            
            return records, metadata
        except Exception as e:
            logger.error(f"Failed to list {self.model.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to list records")

    async def count(self, include_deleted: bool = False) -> int:
        """Count total records."""
        try:
            query = self.db.query(self.model)
            if not include_deleted:
                query = query.filter(self.model.is_deleted == False)
            return query.count()
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to count records") 