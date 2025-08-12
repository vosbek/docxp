"""
Configuration management API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.core.database import get_session, ConfigurationTemplate
from app.models.schemas import ConfigurationTemplate as ConfigSchema

router = APIRouter()

@router.get("/templates", response_model=List[ConfigSchema])
async def list_templates(
    db: AsyncSession = Depends(get_session)
):
    """List all configuration templates"""
    query = await db.execute(select(ConfigurationTemplate))
    templates = query.scalars().all()
    
    return [
        ConfigSchema(
            name=t.name,
            description=t.description,
            config=t.config,
            is_default=t.is_default
        )
        for t in templates
    ]

@router.post("/templates", response_model=ConfigSchema)
async def create_template(
    template: ConfigSchema,
    db: AsyncSession = Depends(get_session)
):
    """Create a new configuration template"""
    
    # Check if name already exists
    existing = await db.execute(
        select(ConfigurationTemplate)
        .where(ConfigurationTemplate.name == template.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Template with this name already exists"
        )
    
    # If setting as default, unset other defaults
    if template.is_default:
        await db.execute(
            select(ConfigurationTemplate).update()
            .values(is_default=False)
        )
    
    # Create new template
    db_template = ConfigurationTemplate(
        name=template.name,
        description=template.description,
        config=template.config,
        is_default=template.is_default,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_template)
    await db.commit()
    
    return template

@router.get("/templates/{name}", response_model=ConfigSchema)
async def get_template(
    name: str,
    db: AsyncSession = Depends(get_session)
):
    """Get a specific configuration template"""
    query = await db.execute(
        select(ConfigurationTemplate)
        .where(ConfigurationTemplate.name == name)
    )
    template = query.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return ConfigSchema(
        name=template.name,
        description=template.description,
        config=template.config,
        is_default=template.is_default
    )

@router.delete("/templates/{name}")
async def delete_template(
    name: str,
    db: AsyncSession = Depends(get_session)
):
    """Delete a configuration template"""
    query = await db.execute(
        select(ConfigurationTemplate)
        .where(ConfigurationTemplate.name == name)
    )
    template = query.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "Template deleted successfully"}

@router.get("/defaults")
async def get_default_config():
    """Get default configuration settings"""
    from app.core.config import settings
    
    return {
        "documentation_depth": settings.DEFAULT_DOC_DEPTH,
        "include_diagrams": settings.INCLUDE_DIAGRAMS,
        "include_business_rules": settings.INCLUDE_BUSINESS_RULES,
        "include_api_docs": settings.INCLUDE_API_DOCS,
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "ignore_patterns": settings.IGNORE_PATTERNS,
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "processing_timeout": settings.PROCESSING_TIMEOUT
    }
