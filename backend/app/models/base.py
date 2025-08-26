"""
SQLAlchemy Base Model for DocXP Enterprise
Re-exports the Base model from core.database to maintain import compatibility
"""

# Import the existing Base model from core.database
from app.core.database import Base

# Re-export for backward compatibility
__all__ = ["Base"]