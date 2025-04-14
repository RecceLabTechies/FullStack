-- Create tables for test_database
-- PostgreSQL doesn't use IF NOT EXISTS with CREATE DATABASE in regular SQL
-- We'll use the app database that was configured in docker-compose

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    company VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    chart_access BOOLEAN NOT NULL,
    report_generation_access BOOLEAN NOT NULL,
    user_management_access BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Campaign performance table
CREATE TABLE IF NOT EXISTS campaign_performance (
    id SERIAL PRIMARY KEY,
    date INTEGER NOT NULL,
    campaign_id VARCHAR(100) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    age_group VARCHAR(50) NOT NULL,
    ad_spend DOUBLE PRECISION NOT NULL,
    views DOUBLE PRECISION NOT NULL,
    leads DOUBLE PRECISION NOT NULL,
    new_accounts DOUBLE PRECISION NOT NULL,
    country VARCHAR(50) NOT NULL,
    revenue DOUBLE PRECISION NOT NULL
);

-- Prophet predictions table
CREATE TABLE IF NOT EXISTS prophet_predictions (
    id SERIAL PRIMARY KEY,
    date INTEGER NOT NULL,
    revenue DOUBLE PRECISION NOT NULL,
    ad_spend DOUBLE PRECISION NOT NULL,
    new_accounts DOUBLE PRECISION NOT NULL
);

-- Insert default users
INSERT INTO users (username, email, role, company, password, chart_access, report_generation_access, user_management_access)
VALUES 
    ('master admin', 'admin@recce.com', 'root', 'reccelabs', 'Admin@123', true, true, true),
    ('guest', 'guest@recce.com', 'member', 'reccelabs', 'Admin@123', true, true, false)
ON CONFLICT (email) DO NOTHING;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_campaign_performance_date ON campaign_performance(date);
CREATE INDEX IF NOT EXISTS idx_prophet_predictions_date ON prophet_predictions(date);

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres; 