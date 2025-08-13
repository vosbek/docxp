"""
Global error handlers and exception classes for DocXP
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.core.logging_config import get_logger
import traceback

logger = get_logger(__name__)

class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(AppException):
    """Validation error exception"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)

class NotFoundException(AppException):
    """Resource not found exception"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)

class AuthorizationException(AppException):
    """Authorization error exception"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=403, details=details)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
            "detail": str(exc) if logger.level <= 10 else None  # Only in DEBUG mode
        }
    )

async def app_exception_handler(request: Request, exc: AppException):
    """Handler for application-specific exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "request_id": request_id
        }
    )

async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handler for validation exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        f"Validation error: {exc.message}",
        extra={
            "request_id": request_id,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for FastAPI HTTPExceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handler for database exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Database error: {exc}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "message": "A database error occurred. Please try again later.",
            "request_id": request_id
        }
    )

def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    from fastapi import HTTPException
    from sqlalchemy.exc import SQLAlchemyError
    
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    logger.info("Exception handlers registered")
