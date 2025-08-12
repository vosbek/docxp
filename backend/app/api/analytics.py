"""
Analytics API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any

from app.core.database import get_session, DocumentationJob, Repository
from app.models.schemas import AnalyticsData

router = APIRouter()

@router.get("/metrics", response_model=AnalyticsData)
async def get_metrics(db: AsyncSession = Depends(get_session)):
    """Get platform analytics metrics"""
    
    # Total jobs
    total_jobs_query = await db.execute(
        select(func.count(DocumentationJob.id))
    )
    total_jobs = total_jobs_query.scalar() or 0
    
    # Successful jobs
    successful_jobs_query = await db.execute(
        select(func.count(DocumentationJob.id))
        .where(DocumentationJob.status == "completed")
    )
    successful_jobs = successful_jobs_query.scalar() or 0
    
    # Failed jobs
    failed_jobs_query = await db.execute(
        select(func.count(DocumentationJob.id))
        .where(DocumentationJob.status == "failed")
    )
    failed_jobs = failed_jobs_query.scalar() or 0
    
    # Average processing time
    avg_time_query = await db.execute(
        select(func.avg(DocumentationJob.processing_time_seconds))
        .where(DocumentationJob.status == "completed")
    )
    avg_processing_time = avg_time_query.scalar() or 0
    
    # Total entities
    total_entities_query = await db.execute(
        select(func.sum(DocumentationJob.entities_count))
    )
    total_entities = total_entities_query.scalar() or 0
    
    # Total business rules
    total_rules_query = await db.execute(
        select(func.sum(DocumentationJob.business_rules_count))
    )
    total_business_rules = total_rules_query.scalar() or 0
    
    # Repositories analyzed
    repos_analyzed_query = await db.execute(
        select(func.count(Repository.id))
    )
    repositories_analyzed = repos_analyzed_query.scalar() or 0
    
    return AnalyticsData(
        total_jobs=total_jobs,
        successful_jobs=successful_jobs,
        failed_jobs=failed_jobs,
        average_processing_time=avg_processing_time,
        total_entities=total_entities,
        total_business_rules=total_business_rules,
        repositories_analyzed=repositories_analyzed
    )

@router.get("/trends")
async def get_trends(
    days: int = 30,
    db: AsyncSession = Depends(get_session)
):
    """Get documentation generation trends"""
    
    # Get jobs over time
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    jobs_query = await db.execute(
        select(DocumentationJob)
        .where(DocumentationJob.created_at >= start_date)
        .order_by(DocumentationJob.created_at)
    )
    jobs = jobs_query.scalars().all()
    
    # Group by day
    trends = {}
    for job in jobs:
        date_key = job.created_at.strftime('%Y-%m-%d')
        if date_key not in trends:
            trends[date_key] = {
                'date': date_key,
                'total': 0,
                'successful': 0,
                'failed': 0,
                'entities': 0,
                'rules': 0
            }
        
        trends[date_key]['total'] += 1
        if job.status == 'completed':
            trends[date_key]['successful'] += 1
            trends[date_key]['entities'] += job.entities_count or 0
            trends[date_key]['rules'] += job.business_rules_count or 0
        elif job.status == 'failed':
            trends[date_key]['failed'] += 1
    
    return list(trends.values())

@router.get("/language-distribution")
async def get_language_distribution(db: AsyncSession = Depends(get_session)):
    """Get programming language distribution across repositories"""
    
    repos_query = await db.execute(select(Repository))
    repos = repos_query.scalars().all()
    
    language_counts = {}
    
    for repo in repos:
        if repo.languages:
            for lang, count in repo.languages.items():
                if lang not in language_counts:
                    language_counts[lang] = 0
                language_counts[lang] += count
    
    # Convert to percentage
    total = sum(language_counts.values())
    if total > 0:
        distribution = {
            lang: round((count / total) * 100, 2)
            for lang, count in language_counts.items()
        }
    else:
        distribution = {}
    
    return distribution

@router.get("/performance-stats")
async def get_performance_stats(db: AsyncSession = Depends(get_session)):
    """Get performance statistics"""
    
    # Get processing times by repository size
    jobs_query = await db.execute(
        select(DocumentationJob)
        .where(DocumentationJob.status == "completed")
    )
    jobs = jobs_query.scalars().all()
    
    stats = {
        'small': {'count': 0, 'avg_time': 0},  # < 100 files
        'medium': {'count': 0, 'avg_time': 0},  # 100-500 files
        'large': {'count': 0, 'avg_time': 0}    # > 500 files
    }
    
    for job in jobs:
        files = job.files_processed or 0
        time = job.processing_time_seconds or 0
        
        if files < 100:
            category = 'small'
        elif files < 500:
            category = 'medium'
        else:
            category = 'large'
        
        stats[category]['count'] += 1
        stats[category]['avg_time'] += time
    
    # Calculate averages
    for category in stats:
        if stats[category]['count'] > 0:
            stats[category]['avg_time'] /= stats[category]['count']
            stats[category]['avg_time'] = round(stats[category]['avg_time'], 2)
    
    return stats
