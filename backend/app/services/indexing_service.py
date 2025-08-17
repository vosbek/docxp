"""
Indexing service for managing V1 indexing operations.

Provides high-level operations for:
- Creating and managing indexing jobs
- Tracking file processing progress
- Caching embeddings for cost optimization
- Monitoring indexing health and performance
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.indexing_models import (
    IndexingJob, IndexingJobStatus, IndexingJobType,
    FileProcessingRecord, FileProcessingStatus,
    RepositorySnapshot, EmbeddingCache, CodeEntityData,
    IndexingHealthMetrics
)
from backend.app.core.database import get_session


class IndexingService:
    """Service for managing indexing operations and monitoring."""

    @staticmethod
    async def create_indexing_job(
        repository_id: UUID,
        job_type: IndexingJobType,
        target_commit: Optional[str] = None,
        file_patterns: Optional[Dict] = None,
        config: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> IndexingJob:
        """Create a new indexing job."""
        async with get_session() as session:
            job = IndexingJob(
                id=uuid4(),
                repository_id=repository_id,
                job_type=job_type.value,
                target_commit=target_commit,
                file_patterns=file_patterns,
                config=config or {},
                created_by=created_by
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            return job

    @staticmethod
    async def start_job(job_id: UUID) -> bool:
        """Start an indexing job."""
        async with get_session() as session:
            result = await session.execute(
                select(IndexingJob).where(IndexingJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job or job.status != IndexingJobStatus.PENDING:
                return False
            
            job.status = IndexingJobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await session.commit()
            return True

    @staticmethod
    async def pause_job(job_id: UUID, checkpoint_data: Optional[Dict] = None) -> bool:
        """Pause a running job with checkpoint data."""
        async with get_session() as session:
            result = await session.execute(
                select(IndexingJob).where(IndexingJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job or job.status != IndexingJobStatus.RUNNING:
                return False
            
            job.status = IndexingJobStatus.PAUSED
            if checkpoint_data:
                job.checkpoint_data = checkpoint_data
            await session.commit()
            return True

    @staticmethod
    async def resume_job(job_id: UUID) -> Tuple[bool, Optional[Dict]]:
        """Resume a paused job and return checkpoint data."""
        async with get_session() as session:
            result = await session.execute(
                select(IndexingJob).where(IndexingJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job or job.status != IndexingJobStatus.PAUSED:
                return False, None
            
            job.status = IndexingJobStatus.RUNNING
            checkpoint_data = job.checkpoint_data
            await session.commit()
            return True, checkpoint_data

    @staticmethod
    async def complete_job(
        job_id: UUID, 
        success: bool = True, 
        error_message: Optional[str] = None
    ) -> bool:
        """Complete an indexing job."""
        async with get_session() as session:
            result = await session.execute(
                select(IndexingJob).where(IndexingJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return False
            
            job.status = IndexingJobStatus.COMPLETED if success else IndexingJobStatus.FAILED
            job.completed_at = datetime.utcnow()
            if error_message:
                job.error_message = error_message
            
            await session.commit()
            return True

    @staticmethod
    async def update_job_progress(
        job_id: UUID,
        total_files: Optional[int] = None,
        processed_files: Optional[int] = None,
        failed_files: Optional[int] = None,
        last_processed_file: Optional[str] = None
    ) -> bool:
        """Update job progress statistics."""
        async with get_session() as session:
            result = await session.execute(
                select(IndexingJob).where(IndexingJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return False
            
            if total_files is not None:
                job.total_files = total_files
            if processed_files is not None:
                job.processed_files = processed_files
            if failed_files is not None:
                job.failed_files = failed_files
            if last_processed_file is not None:
                job.last_processed_file = last_processed_file
            
            await session.commit()
            return True

    @staticmethod
    async def add_file_processing_record(
        job_id: UUID,
        file_path: str,
        file_hash: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        processing_order: Optional[int] = None
    ) -> FileProcessingRecord:
        """Add a file processing record."""
        async with get_session() as session:
            record = FileProcessingRecord(
                id=uuid4(),
                indexing_job_id=job_id,
                file_path=file_path,
                file_hash=file_hash,
                file_size=file_size,
                file_type=file_type,
                processing_order=processing_order
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def update_file_processing_status(
        record_id: UUID,
        status: FileProcessingStatus,
        entities_extracted: Optional[int] = None,
        embeddings_generated: Optional[int] = None,
        processing_duration: Optional[float] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None
    ) -> bool:
        """Update file processing status and results."""
        async with get_session() as session:
            result = await session.execute(
                select(FileProcessingRecord).where(FileProcessingRecord.id == record_id)
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return False
            
            record.status = status.value
            if entities_extracted is not None:
                record.entities_extracted = entities_extracted
            if embeddings_generated is not None:
                record.embeddings_generated = embeddings_generated
            if processing_duration is not None:
                record.processing_duration = processing_duration
            if error_message is not None:
                record.error_message = error_message
            if error_type is not None:
                record.error_type = error_type
            
            if status == FileProcessingStatus.PROCESSING:
                record.started_at = datetime.utcnow()
            elif status in [FileProcessingStatus.COMPLETED, FileProcessingStatus.FAILED]:
                record.completed_at = datetime.utcnow()
            
            await session.commit()
            return True

    @staticmethod
    async def get_or_create_embedding(
        content: str,
        content_type: str,
        embedding_model: str,
        embedding_vector: List[float],
        file_extension: Optional[str] = None
    ) -> Tuple[EmbeddingCache, bool]:
        """Get cached embedding or create new one. Returns (embedding, was_created)."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        async with get_session() as session:
            # Try to get existing embedding
            result = await session.execute(
                select(EmbeddingCache).where(
                    and_(
                        EmbeddingCache.content_hash == content_hash,
                        EmbeddingCache.embedding_model == embedding_model
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update usage statistics
                existing.hit_count += 1
                existing.last_used_at = datetime.utcnow()
                await session.commit()
                return existing, False
            
            # Create new embedding cache entry
            embedding_cache = EmbeddingCache(
                id=uuid4(),
                content_hash=content_hash,
                content_type=content_type,
                embedding_model=embedding_model,
                embedding_vector=embedding_vector,
                embedding_dimension=len(embedding_vector),
                sample_content=content[:500] if content else None,
                file_extension=file_extension,
                content_length=len(content) if content else 0
            )
            session.add(embedding_cache)
            await session.commit()
            await session.refresh(embedding_cache)
            return embedding_cache, True

    @staticmethod
    async def create_repository_snapshot(
        repository_id: UUID,
        job_id: UUID,
        commit_hash: str,
        branch_name: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_author: Optional[str] = None,
        commit_date: Optional[datetime] = None
    ) -> RepositorySnapshot:
        """Create a repository snapshot after job completion."""
        async with get_session() as session:
            # Calculate statistics from job results
            job_stats = await session.execute(
                select(
                    func.count(FileProcessingRecord.id).label('total_files'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.COMPLETED.value, 1),
                            else_=0
                        )
                    ).label('indexed_files'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.FAILED.value, 1),
                            else_=0
                        )
                    ).label('failed_files'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.SKIPPED.value, 1),
                            else_=0
                        )
                    ).label('skipped_files'),
                    func.sum(FileProcessingRecord.entities_extracted).label('total_entities'),
                    func.sum(FileProcessingRecord.embeddings_generated).label('total_embeddings'),
                    func.avg(FileProcessingRecord.processing_duration).label('avg_processing_time')
                ).where(FileProcessingRecord.indexing_job_id == job_id)
            )
            stats = job_stats.first()
            
            snapshot = RepositorySnapshot(
                id=uuid4(),
                repository_id=repository_id,
                indexing_job_id=job_id,
                commit_hash=commit_hash,
                branch_name=branch_name,
                commit_message=commit_message,
                commit_author=commit_author,
                commit_date=commit_date,
                total_files=stats.total_files or 0,
                indexed_files=stats.indexed_files or 0,
                failed_files=stats.failed_files or 0,
                skipped_files=stats.skipped_files or 0,
                total_entities=stats.total_entities or 0,
                total_embeddings=stats.total_embeddings or 0,
                avg_file_processing_time=float(stats.avg_processing_time) if stats.avg_processing_time else None
            )
            
            # Calculate success/error rates
            if snapshot.total_files > 0:
                snapshot.success_rate = (snapshot.indexed_files / snapshot.total_files) * 100
                snapshot.error_rate = (snapshot.failed_files / snapshot.total_files) * 100
            
            session.add(snapshot)
            await session.commit()
            await session.refresh(snapshot)
            return snapshot

    @staticmethod
    async def record_health_metric(
        metric_type: str,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        repository_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None
    ) -> IndexingHealthMetrics:
        """Record a health/performance metric."""
        async with get_session() as session:
            metric = IndexingHealthMetrics(
                id=uuid4(),
                metric_type=metric_type,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                repository_id=repository_id,
                indexing_job_id=job_id,
                metadata=metadata
            )
            session.add(metric)
            await session.commit()
            await session.refresh(metric)
            return metric

    @staticmethod
    async def get_active_jobs(repository_id: Optional[UUID] = None) -> List[IndexingJob]:
        """Get all active (pending/running/paused) jobs."""
        async with get_session() as session:
            query = select(IndexingJob).where(
                IndexingJob.status.in_([
                    IndexingJobStatus.PENDING,
                    IndexingJobStatus.RUNNING,
                    IndexingJobStatus.PAUSED
                ])
            ).options(selectinload(IndexingJob.repository))
            
            if repository_id:
                query = query.where(IndexingJob.repository_id == repository_id)
            
            result = await session.execute(query.order_by(desc(IndexingJob.created_at)))
            return result.scalars().all()

    @staticmethod
    async def get_job_progress(job_id: UUID) -> Optional[Dict]:
        """Get detailed progress information for a job."""
        async with get_session() as session:
            # Get job details
            job_result = await session.execute(
                select(IndexingJob).where(IndexingJob.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                return None
            
            # Get file processing statistics
            stats_result = await session.execute(
                select(
                    func.count(FileProcessingRecord.id).label('total_records'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.COMPLETED.value, 1),
                            else_=0
                        )
                    ).label('completed'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.FAILED.value, 1),
                            else_=0
                        )
                    ).label('failed'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.PROCESSING.value, 1),
                            else_=0
                        )
                    ).label('processing'),
                    func.sum(
                        func.case(
                            (FileProcessingRecord.status == FileProcessingStatus.PENDING.value, 1),
                            else_=0
                        )
                    ).label('pending')
                ).where(FileProcessingRecord.indexing_job_id == job_id)
            )
            stats = stats_result.first()
            
            return {
                'job_id': str(job.id),
                'status': job.status,
                'progress_percentage': job.progress_percentage,
                'total_files': job.total_files,
                'processed_files': job.processed_files,
                'failed_files': job.failed_files,
                'file_records': {
                    'total': stats.total_records or 0,
                    'completed': stats.completed or 0,
                    'failed': stats.failed or 0,
                    'processing': stats.processing or 0,
                    'pending': stats.pending or 0
                },
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'estimated_completion': job.estimated_completion.isoformat() if job.estimated_completion else None,
                'can_resume': job.can_resume,
                'error_message': job.error_message
            }

    @staticmethod
    async def get_repository_health(repository_id: UUID) -> Dict:
        """Get health overview for a repository."""
        async with get_session() as session:
            # Get job statistics
            job_stats = await session.execute(
                select(
                    func.count(IndexingJob.id).label('total_jobs'),
                    func.sum(
                        func.case(
                            (IndexingJob.status == IndexingJobStatus.COMPLETED.value, 1),
                            else_=0
                        )
                    ).label('completed_jobs'),
                    func.sum(
                        func.case(
                            (IndexingJob.status == IndexingJobStatus.FAILED.value, 1),
                            else_=0
                        )
                    ).label('failed_jobs'),
                    func.max(IndexingJob.completed_at).label('last_successful_index')
                ).where(IndexingJob.repository_id == repository_id)
            )
            stats = job_stats.first()
            
            # Get latest snapshot
            snapshot_result = await session.execute(
                select(RepositorySnapshot)
                .where(RepositorySnapshot.repository_id == repository_id)
                .order_by(desc(RepositorySnapshot.created_at))
                .limit(1)
            )
            latest_snapshot = snapshot_result.scalar_one_or_none()
            
            return {
                'repository_id': str(repository_id),
                'total_jobs': stats.total_jobs or 0,
                'completed_jobs': stats.completed_jobs or 0,
                'failed_jobs': stats.failed_jobs or 0,
                'success_rate': (
                    (stats.completed_jobs / stats.total_jobs * 100) 
                    if stats.total_jobs > 0 else 0
                ),
                'last_successful_index': (
                    stats.last_successful_index.isoformat() 
                    if stats.last_successful_index else None
                ),
                'latest_snapshot': {
                    'commit_hash': latest_snapshot.commit_hash,
                    'total_entities': latest_snapshot.total_entities,
                    'total_embeddings': latest_snapshot.total_embeddings,
                    'indexed_files': latest_snapshot.indexed_files,
                    'created_at': latest_snapshot.created_at.isoformat()
                } if latest_snapshot else None
            }

    @staticmethod
    async def cleanup_old_cache_entries(days_old: int = 30) -> int:
        """Clean up old embedding cache entries to save space."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        async with get_session() as session:
            result = await session.execute(
                select(func.count(EmbeddingCache.id)).where(
                    EmbeddingCache.last_used_at < cutoff_date
                )
            )
            count = result.scalar()
            
            # Delete old entries
            await session.execute(
                EmbeddingCache.__table__.delete().where(
                    EmbeddingCache.last_used_at < cutoff_date
                )
            )
            await session.commit()
            
            return count