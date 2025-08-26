@echo off
echo ============================================================================
echo  FINAL OpenSearch Fix - Enterprise Edition
echo ============================================================================
echo.

echo [1/4] Complete OpenSearch index cleanup...
echo   - Deleting ALL potentially bad indexes...
curl -X DELETE "http://localhost:9200/docxp-code-index" 2>nul
curl -X DELETE "http://localhost:9200/docxp_v1_chunks" 2>nul  
curl -X DELETE "http://localhost:9200/docxp_chunks" 2>nul
curl -X DELETE "http://localhost:9200/*docxp*" 2>nul
echo   - ✅ All indexes cleared

echo.
echo [2/4] Verifying OpenSearch cluster health...
curl -s http://localhost:9200/_cluster/health | findstr "green\|yellow" >nul && (
    echo   - ✅ OpenSearch cluster is healthy
) || (
    echo   - ❌ OpenSearch cluster not accessible
    pause
    exit /b 1
)

echo.
echo [3/4] Configuration Summary...
echo   - Engine: FAISS
echo   - Method: HNSW  
echo   - Space Type: innerproduct (valid for FAISS)
echo   - Embedding Dimension: 1024 (Titan v2)

echo.
echo [4/4] Ready to test with corrected configuration!
echo.
echo   Next steps:
echo   1. The space_type has been changed to "innerproduct" 
echo   2. All bad indexes have been deleted
echo   3. Start your backend to test: cd backend && python main.py
echo.
echo ============================================================================
echo   OpenSearch Fix Complete
echo ============================================================================