"""
Base database models and utilities.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel


class BaseDBModel(BaseModel):
    """Base model for all database entities."""
    
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when a database record is not found."""
    pass


class DuplicateRecordError(DatabaseError):
    """Raised when trying to create a duplicate record."""
    pass


def serialize_for_db(data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize data for database insertion."""
    serialized = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif value is not None:
            serialized[key] = value
    return serialized


def handle_supabase_response(response) -> Dict[str, Any]:
    """Handle Supabase response and extract data."""
    if hasattr(response, 'data') and response.data:
        return response.data[0] if len(response.data) == 1 else response.data
    return {} 