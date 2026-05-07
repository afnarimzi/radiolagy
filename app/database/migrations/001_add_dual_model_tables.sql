-- Migration: Add dual-model radiology validation tables
-- Version: 001
-- Description: Creates new tables for dual-model analysis, validation metrics, and performance logging

-- Create dual_radiology_analyses table
CREATE TABLE IF NOT EXISTS dual_radiology_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(50) NOT NULL REFERENCES patient_inputs(case_id),
    gemini_output JSONB NOT NULL,
    groq_output JSONB NOT NULL,
    validation_result JSONB NOT NULL,
    consensus_metrics JSONB NOT NULL,
    final_decision VARCHAR(10) NOT NULL,
    decision_reasoning TEXT,
    retry_count INTEGER DEFAULT 0,
    processing_time_total FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for dual_radiology_analyses
CREATE INDEX IF NOT EXISTS idx_dual_radiology_analyses_case_id ON dual_radiology_analyses(case_id);
CREATE INDEX IF NOT EXISTS idx_dual_radiology_analyses_final_decision ON dual_radiology_analyses(final_decision);
CREATE INDEX IF NOT EXISTS idx_dual_radiology_analyses_created_at ON dual_radiology_analyses(created_at);

-- Create validation_metrics table
CREATE TABLE IF NOT EXISTS validation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(50) NOT NULL REFERENCES patient_inputs(case_id),
    consensus_score FLOAT NOT NULL,
    confidence_correlation FLOAT,
    semantic_similarity FLOAT,
    cohens_kappa FLOAT,
    abnormality_overlap_ratio FLOAT,
    quality_agreement BOOLEAN,
    validation_timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for validation_metrics
CREATE INDEX IF NOT EXISTS idx_validation_metrics_case_id ON validation_metrics(case_id);
CREATE INDEX IF NOT EXISTS idx_validation_metrics_consensus_score ON validation_metrics(consensus_score);
CREATE INDEX IF NOT EXISTS idx_validation_metrics_timestamp ON validation_metrics(validation_timestamp);

-- Create model_performance_logs table
CREATE TABLE IF NOT EXISTS model_performance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(50) NOT NULL REFERENCES patient_inputs(case_id),
    model_name VARCHAR(50) NOT NULL,
    processing_time FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    resource_usage JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for model_performance_logs
CREATE INDEX IF NOT EXISTS idx_model_performance_logs_case_id ON model_performance_logs(case_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_logs_model_name ON model_performance_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_logs_success ON model_performance_logs(success);
CREATE INDEX IF NOT EXISTS idx_model_performance_logs_timestamp ON model_performance_logs(timestamp);

-- Add comments to tables
COMMENT ON TABLE dual_radiology_analyses IS 'Stores dual-model radiology analysis results with validation outcomes';
COMMENT ON TABLE validation_metrics IS 'Stores detailed consensus and validation metrics for dual-model analyses';
COMMENT ON TABLE model_performance_logs IS 'Tracks individual model performance and resource usage';

-- Add comments to key columns
COMMENT ON COLUMN dual_radiology_analyses.gemini_output IS 'Complete Gemini model analysis output in JSON format';
COMMENT ON COLUMN dual_radiology_analyses.groq_output IS 'Complete Groq model analysis output in JSON format';
COMMENT ON COLUMN dual_radiology_analyses.validation_result IS 'Validation analysis results including consensus scores';
COMMENT ON COLUMN dual_radiology_analyses.consensus_metrics IS 'Statistical consensus metrics between models';
COMMENT ON COLUMN dual_radiology_analyses.final_decision IS 'Final validation decision: PASS or FAIL';

COMMENT ON COLUMN validation_metrics.consensus_score IS 'Overall consensus score between models (0-1)';
COMMENT ON COLUMN validation_metrics.cohens_kappa IS 'Cohen''s Kappa inter-rater agreement coefficient';
COMMENT ON COLUMN validation_metrics.semantic_similarity IS 'Semantic similarity score between model findings';

COMMENT ON COLUMN model_performance_logs.model_name IS 'Model identifier: gemini or groq';
COMMENT ON COLUMN model_performance_logs.processing_time IS 'Model processing time in seconds';
COMMENT ON COLUMN model_performance_logs.success IS 'Whether the model analysis completed successfully';