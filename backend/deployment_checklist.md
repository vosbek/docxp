# Enterprise Database Deployment Checklist

## Pre-Deployment Validation

### 1. Schema Validation
```bash
# Run the enterprise database service validation
python -c "
from app.services.enterprise_database_service import enterprise_db_service
import asyncio

async def validate():
    results = await enterprise_db_service.validate_schema_integrity()
    print('Schema Validation Results:', results)

asyncio.run(validate())
"
```

### 2. Database Backup
```sql
-- Create backup before migration
pg_dump -h localhost -U postgres -d docxp_db > backup_pre_migration.sql
```

### 3. Migration Execution
```bash
# Run the migration script
psql -h localhost -U postgres -d docxp_db -f scripts/migrations/003_fix_domain_taxonomy_foreign_keys.sql
```

### 4. Post-Migration Validation
```sql
-- Verify foreign key constraints exist
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'domain_taxonomy'::regclass 
AND contype = 'f';

-- Run hierarchy validation
SELECT * FROM validate_domain_taxonomy_hierarchy();

-- Check materialized view
SELECT COUNT(*) FROM domain_taxonomy_hierarchy;
```

### 5. Performance Testing
```sql
-- Test hierarchy query performance
EXPLAIN ANALYZE 
WITH RECURSIVE hierarchy AS (
    SELECT domain_id, name, 0 as level
    FROM domain_taxonomy
    WHERE parent_domain_id IS NULL
    UNION ALL
    SELECT dt.domain_id, dt.name, h.level + 1
    FROM domain_taxonomy dt
    JOIN hierarchy h ON dt.parent_domain_id = h.domain_id
)
SELECT * FROM hierarchy;
```

## Enterprise Production Deployment

### Environment-Specific Configuration

**Development**:
- Enable SQL query logging
- Use aggressive validation checks
- Auto-fix minor issues

**Staging**:
- Mirror production constraints
- Run full validation suite
- Performance benchmarking

**Production**:
- Conservative validation only
- Manual approval for fixes
- Comprehensive monitoring

### Monitoring Setup

1. **Health Check Endpoint**:
```python
@app.get("/api/v1/health/database")
async def database_health():
    return await enterprise_db_service.create_enterprise_health_check()
```

2. **Automated Alerts**:
- Set up alerts for constraint violations
- Monitor foreign key integrity
- Track query performance degradation

3. **Daily Validation**:
```bash
# Cron job for daily validation
0 6 * * * cd /app && python -c "import asyncio; from app.services.enterprise_database_service import enterprise_db_service; asyncio.run(enterprise_db_service.create_enterprise_health_check())"
```

### Rollback Plan

If issues occur:

1. **Stop application services**
2. **Restore from backup**:
   ```bash
   psql -h localhost -U postgres -d docxp_db < backup_pre_migration.sql
   ```
3. **Verify rollback success**
4. **Restart services**

### Post-Deployment Verification

1. **Application Functionality**:
   - Test domain taxonomy creation
   - Verify hierarchy queries work
   - Check classification rules functionality

2. **Performance Baseline**:
   - Measure query response times
   - Monitor database load
   - Track index usage statistics

3. **Data Integrity**:
   - Run validation functions
   - Check constraint violations
   - Verify referential integrity

## Long-term Maintenance

### Weekly Tasks
- Run `validate_domain_taxonomy_hierarchy()`
- Review performance metrics
- Check for orphaned references

### Monthly Tasks  
- Refresh materialized views
- Analyze index usage
- Review and optimize queries

### Quarterly Tasks
- Full schema validation
- Performance benchmarking
- Capacity planning review