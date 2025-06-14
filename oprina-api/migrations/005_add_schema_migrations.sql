-- Schema Migration Tracking System for Oprina API
-- Phase 2 Infrastructure: Migration Management
-- 
-- This migration creates:
-- - Schema migrations tracking table
-- - Migration management functions
-- - Migration status views
-- - Database versioning system
--
-- Run with: psql -d your_database -f migrations/005_add_schema_migrations.sql

-- Schema migrations table for tracking applied migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Migration identification
    version VARCHAR(255) NOT NULL UNIQUE, -- Migration filename without extension
    filename VARCHAR(500) NOT NULL, -- Full migration filename
    
    -- Migration metadata
    description TEXT, -- Migration description from comments
    checksum VARCHAR(64), -- SHA-256 checksum of migration file
    
    -- Execution tracking
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_time_ms INTEGER, -- How long the migration took
    applied_by VARCHAR(255) DEFAULT CURRENT_USER, -- Who applied the migration
    
    -- Migration status
    status VARCHAR(50) DEFAULT 'success' NOT NULL, -- success, failed, rolled_back
    error_message TEXT, -- Error details if migration failed
    
    -- Rollback support
    rollback_sql TEXT, -- SQL to rollback this migration
    rolled_back_at TIMESTAMPTZ, -- When rollback was executed
    rolled_back_by VARCHAR(255), -- Who executed the rollback
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_migration_status CHECK (status IN ('success', 'failed', 'rolled_back')),
    CONSTRAINT valid_version_format CHECK (version ~ '^\d{3}_[a-z][a-z0-9_]*$')
);

-- Migration dependencies table for tracking migration order
CREATE TABLE IF NOT EXISTS migration_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_version VARCHAR(255) NOT NULL REFERENCES schema_migrations(version),
    depends_on_version VARCHAR(255) NOT NULL REFERENCES schema_migrations(version),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Prevent circular dependencies
    CONSTRAINT no_self_dependency CHECK (migration_version != depends_on_version),
    CONSTRAINT unique_dependency UNIQUE (migration_version, depends_on_version)
);

-- Database schema version table for current state tracking
CREATE TABLE IF NOT EXISTS database_schema_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version information
    current_version VARCHAR(255) NOT NULL, -- Latest applied migration
    schema_hash VARCHAR(64), -- Hash of current schema state
    
    -- Metadata
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(255) DEFAULT CURRENT_USER,
    
    -- Additional info
    total_migrations INTEGER DEFAULT 0,
    database_name VARCHAR(255) DEFAULT CURRENT_DATABASE(),
    
    -- Ensure only one record exists
    CONSTRAINT single_version_record CHECK (id = gen_random_uuid())
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at);
CREATE INDEX IF NOT EXISTS idx_schema_migrations_status ON schema_migrations(status);
CREATE INDEX IF NOT EXISTS idx_migration_dependencies_migration ON migration_dependencies(migration_version);
CREATE INDEX IF NOT EXISTS idx_migration_dependencies_depends_on ON migration_dependencies(depends_on_version);

-- Function to register a migration
CREATE OR REPLACE FUNCTION register_migration(
    p_version VARCHAR(255),
    p_filename VARCHAR(500),
    p_description TEXT DEFAULT NULL,
    p_checksum VARCHAR(64) DEFAULT NULL,
    p_execution_time_ms INTEGER DEFAULT NULL,
    p_rollback_sql TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    migration_id UUID;
BEGIN
    -- Insert migration record
    INSERT INTO schema_migrations (
        version,
        filename,
        description,
        checksum,
        execution_time_ms,
        rollback_sql,
        status
    )
    VALUES (
        p_version,
        p_filename,
        p_description,
        p_checksum,
        p_execution_time_ms,
        p_rollback_sql,
        'success'
    )
    RETURNING id INTO migration_id;
    
    -- Update database schema version
    INSERT INTO database_schema_version (
        current_version,
        total_migrations,
        updated_at
    )
    VALUES (
        p_version,
        (SELECT COUNT(*) FROM schema_migrations WHERE status = 'success'),
        NOW()
    )
    ON CONFLICT ((id = gen_random_uuid())) DO UPDATE SET
        current_version = p_version,
        total_migrations = (SELECT COUNT(*) FROM schema_migrations WHERE status = 'success'),
        updated_at = NOW();
    
    RETURN migration_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check if migration exists
CREATE OR REPLACE FUNCTION migration_exists(p_version VARCHAR(255))
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 FROM schema_migrations 
        WHERE version = p_version AND status = 'success'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get migration status
CREATE OR REPLACE FUNCTION get_migration_status(p_version VARCHAR(255))
RETURNS TABLE(
    version VARCHAR(255),
    filename VARCHAR(500),
    status VARCHAR(50),
    applied_at TIMESTAMPTZ,
    execution_time_ms INTEGER,
    error_message TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm.version,
        sm.filename,
        sm.status,
        sm.applied_at,
        sm.execution_time_ms,
        sm.error_message
    FROM schema_migrations sm
    WHERE sm.version = p_version;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending migrations (not yet applied)
CREATE OR REPLACE FUNCTION get_pending_migrations()
RETURNS TABLE(
    suggested_version VARCHAR(255),
    description TEXT
) AS $$
BEGIN
    -- This is a placeholder - in practice, you'd compare against
    -- available migration files in your migrations directory
    RETURN QUERY
    SELECT 
        'No pending migrations detected'::VARCHAR(255),
        'All known migrations have been applied'::TEXT
    WHERE NOT EXISTS(SELECT 1 FROM schema_migrations WHERE status = 'failed');
END;
$$ LANGUAGE plpgsql;

-- Function to rollback a migration
CREATE OR REPLACE FUNCTION rollback_migration(p_version VARCHAR(255))
RETURNS BOOLEAN AS $$
DECLARE
    rollback_sql_text TEXT;
    migration_record RECORD;
BEGIN
    -- Get migration details
    SELECT * INTO migration_record
    FROM schema_migrations
    WHERE version = p_version AND status = 'success';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Migration % not found or not successfully applied', p_version;
    END IF;
    
    IF migration_record.rollback_sql IS NULL THEN
        RAISE EXCEPTION 'No rollback SQL provided for migration %', p_version;
    END IF;
    
    -- Execute rollback SQL
    EXECUTE migration_record.rollback_sql;
    
    -- Update migration status
    UPDATE schema_migrations
    SET 
        status = 'rolled_back',
        rolled_back_at = NOW(),
        rolled_back_by = CURRENT_USER
    WHERE version = p_version;
    
    -- Update database schema version to previous migration
    UPDATE database_schema_version
    SET 
        current_version = (
            SELECT version 
            FROM schema_migrations 
            WHERE status = 'success' 
            AND applied_at < migration_record.applied_at
            ORDER BY applied_at DESC 
            LIMIT 1
        ),
        total_migrations = (SELECT COUNT(*) FROM schema_migrations WHERE status = 'success'),
        updated_at = NOW();
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create views for migration management

-- Migration history view
CREATE OR REPLACE VIEW migration_history AS
SELECT 
    sm.version,
    sm.filename,
    sm.description,
    sm.status,
    sm.applied_at,
    sm.execution_time_ms,
    sm.applied_by,
    sm.error_message,
    sm.rolled_back_at,
    sm.rolled_back_by,
    CASE 
        WHEN sm.rollback_sql IS NOT NULL THEN 'Yes'
        ELSE 'No'
    END as has_rollback
FROM schema_migrations sm
ORDER BY sm.applied_at DESC;

-- Current schema status view
CREATE OR REPLACE VIEW schema_status AS
SELECT 
    dsv.current_version,
    dsv.total_migrations,
    dsv.updated_at as last_migration_at,
    dsv.database_name,
    sm.filename as current_migration_file,
    sm.description as current_migration_description,
    sm.applied_at as current_migration_applied_at,
    COUNT(CASE WHEN sm2.status = 'failed' THEN 1 END) as failed_migrations,
    COUNT(CASE WHEN sm2.status = 'rolled_back' THEN 1 END) as rolled_back_migrations
FROM database_schema_version dsv
LEFT JOIN schema_migrations sm ON dsv.current_version = sm.version
LEFT JOIN schema_migrations sm2 ON TRUE
GROUP BY dsv.id, sm.id;

-- Migration dependencies view
CREATE OR REPLACE VIEW migration_dependency_tree AS
SELECT 
    md.migration_version,
    sm1.filename as migration_file,
    md.depends_on_version,
    sm2.filename as dependency_file,
    sm1.applied_at as migration_applied_at,
    sm2.applied_at as dependency_applied_at,
    CASE 
        WHEN sm2.applied_at < sm1.applied_at THEN 'Valid'
        ELSE 'Invalid - Dependency applied after migration'
    END as dependency_status
FROM migration_dependencies md
JOIN schema_migrations sm1 ON md.migration_version = sm1.version
JOIN schema_migrations sm2 ON md.depends_on_version = sm2.version
ORDER BY sm1.applied_at;

-- Insert existing migrations into the tracking system
DO $$
DECLARE
    start_time TIMESTAMPTZ := NOW();
BEGIN
    -- Register existing migrations that we know about
    
    -- 001_initial_schema
    PERFORM register_migration(
        '001_initial_schema',
        '001_initial_schema.sql',
        'Initial database schema with core tables: users, sessions, messages, user_tokens, user_activities',
        NULL, -- checksum would be calculated in practice
        NULL, -- execution time unknown for existing migrations
        NULL  -- no rollback SQL for initial schema
    );
    
    -- 002_add_avatar_usage (this migration)
    PERFORM register_migration(
        '002_add_avatar_usage',
        '002_add_avatar_usage.sql',
        'Avatar usage tracking system: avatar_usage_records, usage_quotas, usage_summaries',
        NULL,
        NULL,
        'DROP TABLE IF EXISTS usage_summaries CASCADE; DROP TABLE IF EXISTS usage_quotas CASCADE; DROP TABLE IF EXISTS avatar_usage_records CASCADE;'
    );
    
    -- 003_add_service_tokens
    PERFORM register_migration(
        '003_add_service_tokens',
        '003_add_service_tokens.sql',
        'OAuth service tokens and refresh logging: service_tokens, token_refresh_logs',
        NULL,
        NULL,
        'DROP TABLE IF EXISTS token_refresh_logs CASCADE; DROP TABLE IF EXISTS service_tokens CASCADE;'
    );
    
    -- 004_add_indexes_constraints
    PERFORM register_migration(
        '004_add_indexes_constraints',
        '004_add_indexes_constraints.sql',
        'Performance indexes, data validation constraints, and utility views',
        NULL,
        NULL,
        NULL -- Complex rollback would require dropping specific indexes and constraints
    );
    
    -- 005_add_schema_migrations (this migration)
    PERFORM register_migration(
        '005_add_schema_migrations',
        '005_add_schema_migrations.sql',
        'Schema migration tracking system and database versioning',
        NULL,
        EXTRACT(EPOCH FROM (NOW() - start_time)) * 1000, -- Current execution time
        'DROP TABLE IF EXISTS migration_dependencies CASCADE; DROP TABLE IF EXISTS database_schema_version CASCADE; DROP TABLE IF EXISTS schema_migrations CASCADE;'
    );
    
    -- Set up migration dependencies
    INSERT INTO migration_dependencies (migration_version, depends_on_version) VALUES
        ('002_add_avatar_usage', '001_initial_schema'),
        ('003_add_service_tokens', '001_initial_schema'),
        ('004_add_indexes_constraints', '001_initial_schema'),
        ('004_add_indexes_constraints', '002_add_avatar_usage'),
        ('004_add_indexes_constraints', '003_add_service_tokens'),
        ('005_add_schema_migrations', '001_initial_schema');
    
    RAISE NOTICE 'Registered % existing migrations in tracking system', 
        (SELECT COUNT(*) FROM schema_migrations);
END $$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Schema migration tracking system created successfully!';
    RAISE NOTICE 'Created tables: schema_migrations, migration_dependencies, database_schema_version';
    RAISE NOTICE 'Created management functions and views for migration tracking';
    RAISE NOTICE 'Registered existing migrations in the tracking system';
    
    -- Show current schema status
    RAISE NOTICE 'Current schema version: %', 
        (SELECT current_version FROM database_schema_version LIMIT 1);
    RAISE NOTICE 'Total migrations applied: %', 
        (SELECT total_migrations FROM database_schema_version LIMIT 1);
END $$; 