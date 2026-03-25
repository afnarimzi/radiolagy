-- Initialize Radiology AI Database
-- This script runs automatically when the PostgreSQL container starts

-- Create database (already created by POSTGRES_DB env var)
-- CREATE DATABASE radiology_ai;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE radiology_ai TO radiology_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The actual tables will be created by the Python application
-- when it starts up using SQLAlchemy's create_all() method