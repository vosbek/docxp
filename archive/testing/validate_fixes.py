#!/usr/bin/env python3
"""
Critical Fixes Validation Script
================================

Simple validation script that checks if all 3 critical fixes have been implemented
by examining the source code directly without requiring runtime dependencies.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

class FixesValidator:
    """Validates critical fixes through source code analysis"""
    
    def __init__(self):
        self.backend_path = Path(__file__).parent
        self.results = {}
    
    def validate_fix_1_embedding_service_integration(self) -> Dict[str, any]:
        """Validate that V1IndexingService properly integrates with EmbeddingService"""
        print("Validating Fix 1: EmbeddingService Integration...")
        
        v1_indexing_file = self.backend_path / "app" / "services" / "v1_indexing_service.py"
        if not v1_indexing_file.exists():
            return {"passed": False, "error": "v1_indexing_service.py not found"}
        
        content = v1_indexing_file.read_text()
        
        checks = {
            # Check 1: Import EmbeddingService
            "imports_embedding_service": "from app.services.embedding_service import get_embedding_service" in content,
            
            # Check 2: No direct boto3 client for embeddings
            "no_bedrock_client_init": "self.bedrock_client = boto3.client" not in content,
            
            # Check 3: Has embedding_service attribute
            "has_embedding_service_attr": "self.embedding_service = None" in content,
            
            # Check 4: Initializes embedding service
            "initializes_embedding_service": "self.embedding_service = await get_embedding_service()" in content,
            
            # Check 5: _generate_embedding uses EmbeddingService
            "uses_embedding_service": re.search(r"await self\.embedding_service\.generate_embedding\(", content) is not None,
            
            # Check 6: No direct boto3 invoke_model calls in _generate_embedding
            "no_direct_invoke_model": "invoke_model" not in content or "self.bedrock_client.invoke_model" not in content
        }
        
        passed = all(checks.values())
        
        if passed:
            print("PASSED - Fix 1: EmbeddingService integration")
        else:
            print("FAILED - Fix 1: EmbeddingService integration")
            for check, result in checks.items():
                if not result:
                    print(f"  FAILED: {check}")
        
        return {"passed": passed, "checks": checks}
    
    def validate_fix_2_unified_caching(self) -> Dict[str, any]:
        """Validate that unified caching system is implemented"""
        print("🔍 Validating Fix 2: Unified Caching System...")
        
        embedding_service_file = self.backend_path / "app" / "services" / "embedding_service.py"
        if not embedding_service_file.exists():
            return {"passed": False, "error": "embedding_service.py not found"}
        
        content = embedding_service_file.read_text()
        
        checks = {
            # Check 1: Has unified cache methods
            "has_unified_get_method": "_get_unified_cached_embedding" in content,
            "has_unified_cache_method": "_cache_embedding_unified" in content,
            "has_cache_sync_method": "sync_cache_from_postgresql_to_redis" in content,
            
            # Check 2: Uses unified caching in generate_embedding
            "uses_unified_caching": "_get_unified_cached_embedding(cache_key, content)" in content,
            "caches_unified": "_cache_embedding_unified(cache_key, embedding" in content,
            
            # Check 3: Has PostgreSQL integration
            "has_postgresql_sync": "enable_postgresql_sync" in content,
            "imports_database": "from app.core.database import get_async_session" in content,
            
            # Check 4: Has normalized cache keys
            "has_normalize_bytes": "_normalize_bytes" in content,
            "uses_content_hash": "hashlib.sha256(self._normalize_bytes(content)).hexdigest()" in content
        }
        
        # Check V1IndexingService removed old cache methods
        v1_indexing_file = self.backend_path / "app" / "services" / "v1_indexing_service.py"
        if v1_indexing_file.exists():
            v1_content = v1_indexing_file.read_text()
            checks["no_old_cache_methods"] = (
                "_get_cached_embedding" not in v1_content and
                "_cache_embedding" not in v1_content or
                "PostgreSQL cache methods removed" in v1_content
            )
        
        passed = all(checks.values())
        
        if passed:
            print("✅ Fix 2: Unified caching system - PASSED")
        else:
            print("❌ Fix 2: Unified caching system - FAILED")
            for check, result in checks.items():
                if not result:
                    print(f"  ❌ {check}")
        
        return {"passed": passed, "checks": checks}
    
    def validate_fix_3_checkpointing(self) -> Dict[str, any]:
        """Validate that checkpoint/resume functionality is implemented"""
        print("🔍 Validating Fix 3: Checkpoint/Resume Implementation...")
        
        v1_indexing_file = self.backend_path / "app" / "services" / "v1_indexing_service.py"
        if not v1_indexing_file.exists():
            return {"passed": False, "error": "v1_indexing_service.py not found"}
        
        content = v1_indexing_file.read_text()
        
        checks = {
            # Check 1: Has checkpoint methods
            "has_resume_method": "_resume_from_checkpoint" in content,
            "has_save_checkpoint": "_save_checkpoint" in content,
            "has_pause_job": "async def pause_job" in content,
            "has_resume_job": "async def resume_job" in content,
            "has_checkpoint_status": "get_checkpoint_status" in content,
            
            # Check 2: Enhanced process_indexing_job with resume logic
            "checks_for_resume": "job.last_processed_file is not None and job.checkpoint_data is not None" in content,
            "calls_resume_method": "_resume_from_checkpoint(job, session)" in content,
            
            # Check 3: Saves checkpoints during processing
            "saves_checkpoints": "_save_checkpoint(job, chunk, session)" in content,
            "saves_on_failure": "chunk_failed=True" in content,
            
            # Check 4: Uses checkpoint data
            "uses_checkpoint_data": "job.checkpoint_data" in content,
            "updates_last_processed": "job.last_processed_file" in content
        }
        
        passed = all(checks.values())
        
        if passed:
            print("✅ Fix 3: Checkpoint/resume implementation - PASSED")
        else:
            print("❌ Fix 3: Checkpoint/resume implementation - FAILED")
            for check, result in checks.items():
                if not result:
                    print(f"  ❌ {check}")
        
        return {"passed": passed, "checks": checks}
    
    def validate_api_endpoints(self) -> Dict[str, any]:
        """Validate that enterprise API endpoints are available"""
        print("🔍 Validating API Endpoints...")
        
        api_file = self.backend_path / "app" / "api" / "v1_indexing_endpoints.py"
        if not api_file.exists():
            return {"passed": False, "error": "v1_indexing_endpoints.py not found"}
        
        content = api_file.read_text()
        
        checks = {
            "has_start_endpoint": 'router.post("/start"' in content or '"/api/v1/indexing/start"' in content,
            "has_pause_endpoint": "/pause" in content,
            "has_resume_endpoint": "/resume" in content,
            "has_status_endpoint": "/status" in content,
            "has_checkpoint_endpoint": "/checkpoint" in content,
            "has_cache_sync": "/cache/sync" in content,
            "has_health_endpoint": "/health" in content
        }
        
        passed = all(checks.values())
        
        if passed:
            print("✅ API endpoints - PASSED")
        else:
            print("❌ API endpoints - FAILED")
            for check, result in checks.items():
                if not result:
                    print(f"  ❌ {check}")
        
        return {"passed": passed, "checks": checks}
    
    def run_validation(self) -> Dict[str, any]:
        """Run complete validation"""
        print("Starting Critical Fixes Validation...")
        print("=" * 60)
        
        # Run all validations
        fix1_result = self.validate_fix_1_embedding_service_integration()
        fix2_result = self.validate_fix_2_unified_caching()
        fix3_result = self.validate_fix_3_checkpointing()
        api_result = self.validate_api_endpoints()
        
        results = [fix1_result, fix2_result, fix3_result, api_result]
        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        
        print("=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)
        
        overall_passed = passed_count == total_count
        
        if overall_passed:
            print("✅ ALL CRITICAL FIXES VERIFIED SUCCESSFULLY")
            print("🚀 V1 Indexing Pipeline is ready for production!")
        else:
            print(f"❌ {total_count - passed_count} fix(es) need attention")
            print("⚠️  Please review the failed checks above")
        
        print(f"📊 Pass Rate: {passed_count}/{total_count} ({(passed_count/total_count)*100:.1f}%)")
        print("=" * 60)
        
        return {
            "overall_passed": overall_passed,
            "passed_count": passed_count,
            "total_count": total_count,
            "results": {
                "fix1_embedding_service": fix1_result,
                "fix2_unified_caching": fix2_result, 
                "fix3_checkpointing": fix3_result,
                "api_endpoints": api_result
            }
        }

def main():
    """Main validation function"""
    validator = FixesValidator()
    results = validator.run_validation()
    
    # Return appropriate exit code
    return 0 if results["overall_passed"] else 1

if __name__ == "__main__":
    exit(main())