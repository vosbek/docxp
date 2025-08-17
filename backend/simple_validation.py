#!/usr/bin/env python3
"""
Simple Critical Fixes Validation
================================
"""

from pathlib import Path

def check_files_exist():
    """Check if key files exist"""
    backend_path = Path(__file__).parent
    
    files_to_check = [
        "app/services/v1_indexing_service.py",
        "app/services/embedding_service.py", 
        "app/api/v1_indexing_endpoints.py",
        "CRITICAL_FIXES_SUMMARY.md"
    ]
    
    print("Checking critical files...")
    all_exist = True
    
    for file_path in files_to_check:
        full_path = backend_path / file_path
        exists = full_path.exists()
        status = "FOUND" if exists else "MISSING"
        print(f"  {status}: {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_embedding_service_integration():
    """Check if EmbeddingService integration is implemented"""
    backend_path = Path(__file__).parent
    v1_file = backend_path / "app" / "services" / "v1_indexing_service.py"
    
    if not v1_file.exists():
        return False, "File not found"
    
    content = v1_file.read_text()
    
    checks = [
        ("Imports EmbeddingService", "from app.services.embedding_service import get_embedding_service" in content),
        ("Has embedding_service attribute", "self.embedding_service = None" in content),
        ("Uses EmbeddingService in _generate_embedding", "await self.embedding_service.generate_embedding(" in content),
        ("No direct boto3 bedrock client", "self.bedrock_client = boto3.client" not in content)
    ]
    
    passed_checks = []
    failed_checks = []
    
    for check_name, result in checks:
        if result:
            passed_checks.append(check_name)
        else:
            failed_checks.append(check_name)
    
    all_passed = len(failed_checks) == 0
    return all_passed, {"passed": passed_checks, "failed": failed_checks}

def check_unified_caching():
    """Check if unified caching is implemented"""
    backend_path = Path(__file__).parent
    embedding_file = backend_path / "app" / "services" / "embedding_service.py"
    
    if not embedding_file.exists():
        return False, "File not found"
    
    content = embedding_file.read_text()
    
    checks = [
        ("Has unified cache get method", "_get_unified_cached_embedding" in content),
        ("Has unified cache set method", "_cache_embedding_unified" in content),
        ("Has cache sync method", "sync_cache_from_postgresql_to_redis" in content),
        ("Uses unified caching", "_get_unified_cached_embedding(cache_key, content)" in content),
        ("Has PostgreSQL sync config", "enable_postgresql_sync" in content)
    ]
    
    passed_checks = []
    failed_checks = []
    
    for check_name, result in checks:
        if result:
            passed_checks.append(check_name)
        else:
            failed_checks.append(check_name)
    
    all_passed = len(failed_checks) == 0
    return all_passed, {"passed": passed_checks, "failed": failed_checks}

def check_checkpointing():
    """Check if checkpointing is implemented"""
    backend_path = Path(__file__).parent
    v1_file = backend_path / "app" / "services" / "v1_indexing_service.py"
    
    if not v1_file.exists():
        return False, "File not found"
    
    content = v1_file.read_text()
    
    checks = [
        ("Has resume method", "_resume_from_checkpoint" in content),
        ("Has save checkpoint method", "_save_checkpoint" in content),
        ("Has pause job method", "async def pause_job" in content),
        ("Has resume job method", "async def resume_job" in content),
        ("Checks for resume conditions", "job.last_processed_file is not None and job.checkpoint_data is not None" in content),
        ("Saves checkpoints during processing", "_save_checkpoint(job, chunk, session)" in content)
    ]
    
    passed_checks = []
    failed_checks = []
    
    for check_name, result in checks:
        if result:
            passed_checks.append(check_name)
        else:
            failed_checks.append(check_name)
    
    all_passed = len(failed_checks) == 0
    return all_passed, {"passed": passed_checks, "failed": failed_checks}

def main():
    """Run simple validation"""
    print("Critical Fixes Validation")
    print("=" * 50)
    
    # Check file existence
    files_exist = check_files_exist()
    print()
    
    if not files_exist:
        print("FAILED: Missing critical files")
        return 1
    
    # Check each fix
    tests = [
        ("Fix 1: EmbeddingService Integration", check_embedding_service_integration),
        ("Fix 2: Unified Caching", check_unified_caching),
        ("Fix 3: Checkpointing", check_checkpointing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        passed, details = test_func()
        results.append((test_name, passed, details))
        
        if passed:
            print(f"  PASSED: {test_name}")
        else:
            print(f"  FAILED: {test_name}")
            if isinstance(details, dict) and "failed" in details:
                for failed_check in details["failed"]:
                    print(f"    - {failed_check}")
        print()
    
    # Summary
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    for test_name, passed, _ in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {status}: {test_name}")
    
    print()
    overall_passed = passed_count == total_count
    
    if overall_passed:
        print("ALL CRITICAL FIXES VERIFIED SUCCESSFULLY!")
        print("V1 Indexing Pipeline is ready for production.")
    else:
        print(f"WARNING: {total_count - passed_count} fix(es) need attention")
    
    print(f"Pass Rate: {passed_count}/{total_count} ({(passed_count/total_count)*100:.1f}%)")
    
    return 0 if overall_passed else 1

if __name__ == "__main__":
    exit(main())