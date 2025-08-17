"""
Example usage of the V1 indexing models and service.

This file demonstrates how to:
- Create and manage indexing jobs
- Track file processing progress
- Use embedding cache for cost optimization
- Monitor indexing health and performance
"""

import asyncio
from uuid import uuid4
from datetime import datetime

from backend.app.services.indexing_service import IndexingService
from backend.app.models.indexing_models import (
    IndexingJobType, FileProcessingStatus
)


async def example_full_indexing_workflow():
    """Example of a complete indexing workflow."""
    
    # Assume we have a repository ID
    repository_id = uuid4()  # In real usage, this would be from existing repo
    
    print("1. Creating indexing job...")
    job = await IndexingService.create_indexing_job(
        repository_id=repository_id,
        job_type=IndexingJobType.FULL,
        target_commit="abc123def456",
        file_patterns={
            "include": ["**/*.py", "**/*.js", "**/*.ts"],
            "exclude": ["**/node_modules/**", "**/__pycache__/**"]
        },
        config={
            "embedding_model": "text-embedding-3-small",
            "chunk_size": 1000,
            "overlap": 200
        },
        created_by="indexing_bot"
    )
    print(f"Created job: {job.id}")
    
    print("\n2. Starting job...")
    success = await IndexingService.start_job(job.id)
    print(f"Job started: {success}")
    
    print("\n3. Adding files to process...")
    files_to_process = [
        "src/main.py",
        "src/utils.py", 
        "src/models.py",
        "tests/test_main.py"
    ]
    
    file_records = []
    for i, file_path in enumerate(files_to_process):
        record = await IndexingService.add_file_processing_record(
            job_id=job.id,
            file_path=file_path,
            file_hash=f"hash_{i}",
            file_size=1000 + i * 100,
            file_type="py",
            processing_order=i
        )
        file_records.append(record)
    
    # Update job with total files
    await IndexingService.update_job_progress(
        job_id=job.id,
        total_files=len(files_to_process)
    )
    
    print(f"Added {len(file_records)} files to process")
    
    print("\n4. Simulating file processing...")
    processed_count = 0
    
    for record in file_records:
        # Start processing file
        await IndexingService.update_file_processing_status(
            record_id=record.id,
            status=FileProcessingStatus.PROCESSING
        )
        
        # Simulate processing (check embedding cache)
        sample_content = f"def example_function_{record.file_path}(): pass"
        embedding_vector = [0.1] * 1536  # Mock embedding
        
        cached_embedding, was_created = await IndexingService.get_or_create_embedding(
            content=sample_content,
            content_type="function",
            embedding_model="text-embedding-3-small",
            embedding_vector=embedding_vector,
            file_extension="py"
        )
        
        cache_status = "created" if was_created else "reused"
        print(f"  Processing {record.file_path} - embedding {cache_status}")
        
        # Complete processing
        await IndexingService.update_file_processing_status(
            record_id=record.id,
            status=FileProcessingStatus.COMPLETED,
            entities_extracted=5,
            embeddings_generated=1,
            processing_duration=0.5
        )
        
        processed_count += 1
        await IndexingService.update_job_progress(
            job_id=job.id,
            processed_files=processed_count,
            last_processed_file=record.file_path
        )
    
    print("\n5. Completing job...")
    await IndexingService.complete_job(job.id, success=True)
    
    print("\n6. Creating repository snapshot...")
    snapshot = await IndexingService.create_repository_snapshot(
        repository_id=repository_id,
        job_id=job.id,
        commit_hash="abc123def456",
        branch_name="main",
        commit_message="Update documentation",
        commit_author="Developer",
        commit_date=datetime.utcnow()
    )
    print(f"Created snapshot: {snapshot.id}")
    print(f"  Total entities: {snapshot.total_entities}")
    print(f"  Success rate: {snapshot.success_rate}%")
    
    print("\n7. Recording health metrics...")
    await IndexingService.record_health_metric(
        metric_type="performance",
        metric_name="avg_processing_time",
        metric_value=0.5,
        metric_unit="seconds",
        repository_id=repository_id,
        job_id=job.id
    )
    
    await IndexingService.record_health_metric(
        metric_type="cost",
        metric_name="embedding_cost",
        metric_value=0.02,
        metric_unit="usd",
        repository_id=repository_id,
        job_id=job.id,
        metadata={"model": "text-embedding-3-small", "tokens": 1000}
    )
    
    print("\n8. Getting job progress...")
    progress = await IndexingService.get_job_progress(job.id)
    print(f"Final progress: {progress}")
    
    print("\n9. Getting repository health...")
    health = await IndexingService.get_repository_health(repository_id)
    print(f"Repository health: {health}")


async def example_incremental_indexing():
    """Example of incremental indexing with resume capability."""
    
    repository_id = uuid4()
    
    print("Creating incremental indexing job...")
    job = await IndexingService.create_indexing_job(
        repository_id=repository_id,
        job_type=IndexingJobType.INCREMENTAL,
        target_commit="def456ghi789",
        config={"since_commit": "abc123def456"}
    )
    
    # Start job
    await IndexingService.start_job(job.id)
    
    # Add some files
    files = ["src/new_feature.py", "src/updated_file.py"]
    for file_path in files:
        await IndexingService.add_file_processing_record(
            job_id=job.id,
            file_path=file_path
        )
    
    await IndexingService.update_job_progress(job.id, total_files=len(files))
    
    # Simulate pause (e.g., due to system shutdown)
    checkpoint_data = {
        "last_processed_index": 0,
        "batch_size": 10,
        "current_batch": 1
    }
    
    print("Pausing job with checkpoint...")
    await IndexingService.pause_job(job.id, checkpoint_data)
    
    # Later, resume the job
    print("Resuming job...")
    resumed, checkpoint = await IndexingService.resume_job(job.id)
    print(f"Job resumed: {resumed}")
    print(f"Checkpoint data: {checkpoint}")
    
    # Complete the job
    await IndexingService.complete_job(job.id, success=True)
    
    print("Incremental indexing completed!")


async def example_monitoring_and_health():
    """Example of monitoring multiple jobs and system health."""
    
    print("Getting all active jobs...")
    active_jobs = await IndexingService.get_active_jobs()
    print(f"Found {len(active_jobs)} active jobs")
    
    for job in active_jobs:
        progress = await IndexingService.get_job_progress(job.id)
        print(f"Job {job.id}: {progress['progress_percentage']:.1f}% complete")
    
    print("\nCleaning up old cache entries...")
    cleaned_count = await IndexingService.cleanup_old_cache_entries(days_old=7)
    print(f"Cleaned up {cleaned_count} old cache entries")


async def main():
    """Run all examples."""
    print("=== V1 Indexing System Usage Examples ===\n")
    
    try:
        print("--- Full Indexing Workflow ---")
        await example_full_indexing_workflow()
        
        print("\n--- Incremental Indexing with Resume ---")
        await example_incremental_indexing()
        
        print("\n--- Monitoring and Health ---")
        await example_monitoring_and_health()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        # In a real application, you'd have proper error handling


if __name__ == "__main__":
    # Note: This example assumes the database is set up and accessible
    # In practice, you'd run the migration script first
    print("To run this example:")
    print("1. Ensure PostgreSQL is running")
    print("2. Run the migration: psql -f scripts/migrations/001_add_indexing_models.sql")
    print("3. Configure database connection in backend/app/core/database.py")
    print("4. Then run: python -m backend.app.examples.indexing_usage_example")
    
    # Uncomment to actually run (requires database setup):
    # asyncio.run(main())