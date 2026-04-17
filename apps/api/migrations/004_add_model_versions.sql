-- Migration 004: Add model_versions table for P1-T13 Model Version Management
-- Creates table to track model versions with snapshots and rollback support

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Version number in format v{major}.{minor}.{patch}
    version_number VARCHAR(20) NOT NULL,
    
    -- Snapshots of configuration and metrics at version creation time
    config_snapshot JSONB NOT NULL,
    metrics_snapshot JSONB NOT NULL,
    
    -- Version tags (e.g., "production", "best-model")
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Active version flag (only one active version per experiment)
    is_active INTEGER DEFAULT 1,
    
    -- Reference to the source model
    source_model_id UUID REFERENCES models(id) ON DELETE SET NULL,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_experiment FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    CONSTRAINT fk_source_model FOREIGN KEY (source_model_id) REFERENCES models(id) ON DELETE SET NULL,
    CONSTRAINT unique_version_number UNIQUE (experiment_id, version_number)
);

-- Index for quick lookup of active versions
CREATE INDEX IF NOT EXISTS idx_model_versions_active ON model_versions(experiment_id, is_active) WHERE is_active = 1;

-- Index for listing versions by experiment
CREATE INDEX IF NOT EXISTS idx_model_versions_experiment ON model_versions(experiment_id, created_at DESC);

-- Index for tag searches
CREATE INDEX IF NOT EXISTS idx_model_versions_tags ON model_versions USING GIN (tags);

-- Comment on table
COMMENT ON TABLE model_versions IS 'P1-T13: Model version management - tracks version history with snapshots';

COMMENT ON COLUMN model_versions.version_number IS 'Version number in format v{major}.{minor}.{patch}, e.g., v1.0.0';

COMMENT ON COLUMN model_versions.config_snapshot IS 'Snapshot of training configuration at version creation time';

COMMENT ON COLUMN model_versions.metrics_snapshot IS 'Snapshot of training metrics at version creation time';

COMMENT ON COLUMN model_versions.is_active IS 'Active version flag: 1=active, 0=inactive. Only one active version per experiment';

COMMENT ON COLUMN model_versions.source_model_id IS 'Reference to the source model file in models table';
