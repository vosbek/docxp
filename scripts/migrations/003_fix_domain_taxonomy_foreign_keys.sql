-- Migration: Fix Domain Taxonomy Foreign Key Constraints
-- Version: 3.0
-- Date: 2025-08-19
-- Description: Fix PostgreSQL foreign key constraint issues in domain_taxonomy table
--              Ensures proper referential integrity for hierarchical domain structure

-- =============================================================================
-- ENTERPRISE DATABASE MIGRATION: DOMAIN TAXONOMY FOREIGN KEY FIX
-- =============================================================================

-- Step 1: Drop existing foreign key constraint if it exists (PostgreSQL)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'domain_taxonomy_parent_domain_id_fkey' 
               AND table_name = 'domain_taxonomy') THEN
        ALTER TABLE domain_taxonomy DROP CONSTRAINT domain_taxonomy_parent_domain_id_fkey;
    END IF;
END $$;

-- Step 2: Ensure domain_id has proper unique constraint
-- Check if unique constraint exists, if not create it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_type = 'UNIQUE' 
                   AND table_name = 'domain_taxonomy' 
                   AND constraint_name = 'domain_taxonomy_domain_id_key') THEN
        ALTER TABLE domain_taxonomy ADD CONSTRAINT domain_taxonomy_domain_id_key UNIQUE (domain_id);
    END IF;
END $$;

-- Step 3: Clean up any orphaned records (enterprise data integrity)
-- Set parent_domain_id to NULL where it references non-existent domain_ids
UPDATE domain_taxonomy 
SET parent_domain_id = NULL 
WHERE parent_domain_id IS NOT NULL 
AND parent_domain_id NOT IN (SELECT domain_id FROM domain_taxonomy);

-- Step 4: Add proper foreign key constraint with enterprise-grade options
ALTER TABLE domain_taxonomy 
ADD CONSTRAINT domain_taxonomy_parent_domain_id_fkey 
FOREIGN KEY (parent_domain_id) 
REFERENCES domain_taxonomy(domain_id) 
ON DELETE SET NULL 
ON UPDATE CASCADE;

-- Step 5: Add essential indexes for enterprise performance
CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_parent_domain_id 
ON domain_taxonomy(parent_domain_id) 
WHERE parent_domain_id IS NOT NULL;

-- Step 6: Create composite index for hierarchy traversal optimization
CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_hierarchy 
ON domain_taxonomy(parent_domain_id, level, category);

-- Step 7: Add check constraints for enterprise data quality
ALTER TABLE domain_taxonomy 
ADD CONSTRAINT chk_domain_taxonomy_level_positive 
CHECK (level >= 0);

ALTER TABLE domain_taxonomy 
ADD CONSTRAINT chk_domain_taxonomy_no_self_reference 
CHECK (domain_id != parent_domain_id);

-- =============================================================================
-- ENTERPRISE VALIDATION FUNCTIONS
-- =============================================================================

-- Function to validate hierarchy integrity
CREATE OR REPLACE FUNCTION validate_domain_taxonomy_hierarchy()
RETURNS TABLE(
    domain_id text,
    issue_type text,
    issue_description text
) AS $$
BEGIN
    -- Check for circular references
    RETURN QUERY
    WITH RECURSIVE hierarchy_check AS (
        SELECT dt.domain_id, dt.parent_domain_id, 1 as depth,
               ARRAY[dt.domain_id] as path
        FROM domain_taxonomy dt
        WHERE dt.parent_domain_id IS NOT NULL
        
        UNION ALL
        
        SELECT hc.domain_id, dt.parent_domain_id, hc.depth + 1,
               hc.path || dt.domain_id
        FROM hierarchy_check hc
        JOIN domain_taxonomy dt ON dt.domain_id = hc.parent_domain_id
        WHERE dt.domain_id != ALL(hc.path)  -- Prevent infinite recursion
        AND hc.depth < 10  -- Max depth safety
    )
    SELECT hc.domain_id, 'CIRCULAR_REFERENCE', 
           'Circular reference detected in hierarchy path: ' || array_to_string(hc.path, ' -> ')
    FROM hierarchy_check hc
    WHERE hc.parent_domain_id = ANY(hc.path);
    
    -- Check for orphaned references (should not happen with FK constraint)
    RETURN QUERY
    SELECT dt.domain_id, 'ORPHANED_REFERENCE',
           'References non-existent parent: ' || dt.parent_domain_id
    FROM domain_taxonomy dt
    WHERE dt.parent_domain_id IS NOT NULL
    AND dt.parent_domain_id NOT IN (SELECT domain_id FROM domain_taxonomy);
    
    -- Check level consistency
    RETURN QUERY
    WITH hierarchy_levels AS (
        SELECT dt.domain_id, dt.level,
               CASE 
                   WHEN dt.parent_domain_id IS NULL THEN 0
                   ELSE (SELECT parent.level + 1 FROM domain_taxonomy parent 
                         WHERE parent.domain_id = dt.parent_domain_id)
               END as calculated_level
        FROM domain_taxonomy dt
    )
    SELECT hl.domain_id, 'LEVEL_INCONSISTENCY',
           'Level ' || hl.level || ' should be ' || hl.calculated_level
    FROM hierarchy_levels hl
    WHERE hl.level != hl.calculated_level;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ENTERPRISE MAINTENANCE PROCEDURES
-- =============================================================================

-- Function to fix hierarchy levels
CREATE OR REPLACE FUNCTION fix_domain_taxonomy_levels()
RETURNS integer AS $$
DECLARE
    fixed_count integer := 0;
BEGIN
    -- Update levels based on actual hierarchy depth
    WITH RECURSIVE hierarchy_levels AS (
        -- Root nodes (no parent)
        SELECT domain_id, 0 as correct_level
        FROM domain_taxonomy
        WHERE parent_domain_id IS NULL
        
        UNION ALL
        
        -- Child nodes
        SELECT dt.domain_id, hl.correct_level + 1
        FROM domain_taxonomy dt
        JOIN hierarchy_levels hl ON hl.domain_id = dt.parent_domain_id
    )
    UPDATE domain_taxonomy 
    SET level = hl.correct_level
    FROM hierarchy_levels hl
    WHERE domain_taxonomy.domain_id = hl.domain_id
    AND domain_taxonomy.level != hl.correct_level;
    
    GET DIAGNOSTICS fixed_count = ROW_COUNT;
    RETURN fixed_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE OPTIMIZATION VIEWS
-- =============================================================================

-- Materialized view for fast hierarchy queries (enterprise performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS domain_taxonomy_hierarchy AS
WITH RECURSIVE domain_tree AS (
    -- Root nodes
    SELECT 
        domain_id,
        domain_id as root_id,
        name,
        category,
        level,
        ARRAY[domain_id] as path,
        domain_id::text as path_string
    FROM domain_taxonomy 
    WHERE parent_domain_id IS NULL
    
    UNION ALL
    
    -- Child nodes
    SELECT 
        dt.domain_id,
        tree.root_id,
        dt.name,
        dt.category,
        dt.level,
        tree.path || dt.domain_id,
        tree.path_string || ' > ' || dt.name
    FROM domain_taxonomy dt
    JOIN domain_tree tree ON tree.domain_id = dt.parent_domain_id
)
SELECT 
    domain_id,
    root_id,
    name,
    category,
    level,
    path,
    path_string,
    array_length(path, 1) as depth
FROM domain_tree;

-- Index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_domain_taxonomy_hierarchy_domain_id 
ON domain_taxonomy_hierarchy(domain_id);

CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_hierarchy_root_id 
ON domain_taxonomy_hierarchy(root_id);

CREATE INDEX IF NOT EXISTS idx_domain_taxonomy_hierarchy_level 
ON domain_taxonomy_hierarchy(level);

-- =============================================================================
-- ENTERPRISE DATA INTEGRITY TRIGGERS
-- =============================================================================

-- Trigger function to maintain hierarchy levels automatically
CREATE OR REPLACE FUNCTION maintain_domain_taxonomy_levels()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate correct level based on parent
    IF NEW.parent_domain_id IS NULL THEN
        NEW.level := 0;
    ELSE
        SELECT level + 1 INTO NEW.level
        FROM domain_taxonomy
        WHERE domain_id = NEW.parent_domain_id;
        
        -- If parent not found, set to 0 (will fail FK constraint anyway)
        IF NEW.level IS NULL THEN
            NEW.level := 0;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trg_maintain_domain_taxonomy_levels ON domain_taxonomy;
CREATE TRIGGER trg_maintain_domain_taxonomy_levels
    BEFORE INSERT OR UPDATE OF parent_domain_id
    ON domain_taxonomy
    FOR EACH ROW
    EXECUTE FUNCTION maintain_domain_taxonomy_levels();

-- Trigger to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_domain_taxonomy_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY domain_taxonomy_hierarchy;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_refresh_domain_taxonomy_hierarchy ON domain_taxonomy;
CREATE TRIGGER trg_refresh_domain_taxonomy_hierarchy
    AFTER INSERT OR UPDATE OR DELETE
    ON domain_taxonomy
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_domain_taxonomy_hierarchy();

-- =============================================================================
-- VALIDATION AND TESTING
-- =============================================================================

-- Run validation to ensure migration worked
DO $$
DECLARE
    issue_count integer;
    fix_count integer;
BEGIN
    -- Count any remaining issues
    SELECT COUNT(*) INTO issue_count
    FROM validate_domain_taxonomy_hierarchy();
    
    IF issue_count > 0 THEN
        RAISE NOTICE 'Found % hierarchy issues after migration', issue_count;
        
        -- Try to fix level issues
        SELECT fix_domain_taxonomy_levels() INTO fix_count;
        RAISE NOTICE 'Fixed % level inconsistencies', fix_count;
    ELSE
        RAISE NOTICE 'Domain taxonomy hierarchy migration completed successfully';
    END IF;
END $$;

-- =============================================================================
-- DOCUMENTATION AND COMMENTS
-- =============================================================================

COMMENT ON TABLE domain_taxonomy IS 'Hierarchical business domain taxonomy with proper referential integrity';
COMMENT ON COLUMN domain_taxonomy.domain_id IS 'Business domain identifier with unique constraint';
COMMENT ON COLUMN domain_taxonomy.parent_domain_id IS 'Foreign key to parent domain with CASCADE options';
COMMENT ON CONSTRAINT domain_taxonomy_parent_domain_id_fkey ON domain_taxonomy IS 'Self-referencing FK with ON DELETE SET NULL for enterprise data safety';
COMMENT ON FUNCTION validate_domain_taxonomy_hierarchy() IS 'Enterprise validation function for hierarchy integrity';
COMMENT ON FUNCTION fix_domain_taxonomy_levels() IS 'Maintenance function to fix level inconsistencies';
COMMENT ON MATERIALIZED VIEW domain_taxonomy_hierarchy IS 'Optimized hierarchy view for fast traversal queries';

-- Migration completed
-- Version: 3.0
-- Fixed foreign key constraints, added enterprise validation, performance optimization
-- Last updated: 2025-08-19