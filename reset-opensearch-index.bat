@echo off
echo ============================================================================
echo  DocXP OpenSearch Index Reset
echo ============================================================================
echo.
echo Deleting the bad OpenSearch index so it can be recreated with correct mapping...

curl -X DELETE "http://localhost:9200/docxp-code-index" 2>nul
if errorlevel 1 (
    echo   - Index may not exist (this is fine)
) else (
    echo   - ✅ Bad index deleted successfully
)

echo.
echo Also deleting the alternative index name just in case...
curl -X DELETE "http://localhost:9200/docxp_v1_chunks" 2>nul

echo.
echo ============================================================================
echo   Index Reset Complete
echo ============================================================================
echo.
echo The index will be recreated automatically when you start the backend.
echo Run: .\start-complete-system.bat
echo.