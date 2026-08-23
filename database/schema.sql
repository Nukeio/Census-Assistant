-- ====================================================================
-- Census Assistant - Supabase & PostgreSQL Production Database Schema
-- Scalable relational and vector knowledge store for Census Operations
-- ====================================================================

-- 1. Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- Enable pgvector if semantic embedding search is enabled in cloud
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Functionaries Table (All Users Sheet)
CREATE TABLE IF NOT EXISTS functionaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sno NUMERIC,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    functionary_type VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(20),
    state_ut VARCHAR(50),
    district VARCHAR(100),
    sub_district VARCHAR(100),
    village_town VARCHAR(150),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_func_user_id ON functionaries(user_id);
CREATE INDEX IF NOT EXISTS idx_func_mobile ON functionaries(mobile_number);
CREATE INDEX IF NOT EXISTS idx_func_name ON functionaries(name);

-- 3. HLB / EB Allocation Table (HLB Allocation Sheet)
CREATE TABLE IF NOT EXISTS hlb_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supervisory_circle_no VARCHAR(50),
    hlb_no VARCHAR(50) NOT NULL,
    supervisor_name VARCHAR(255),
    enumerator_name VARCHAR(255),
    enumerator_user_id VARCHAR(100),
    allotment_date VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hlb_no ON hlb_allocations(hlb_no);
CREATE INDEX IF NOT EXISTS idx_hlb_circle ON hlb_allocations(supervisory_circle_no);
CREATE INDEX IF NOT EXISTS idx_hlb_enum_user_id ON hlb_allocations(enumerator_user_id);
CREATE INDEX IF NOT EXISTS idx_hlb_supervisor ON hlb_allocations(supervisor_name);

-- 4. Manual Chunks & Vector Store (PDF Manuals)
CREATE TABLE IF NOT EXISTS manual_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file VARCHAR(255) NOT NULL,
    doc_title VARCHAR(255) NOT NULL,
    page_number INT,
    section_header VARCHAR(255),
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- Vector embeddings for semantic search
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_manual_source ON manual_chunks(source_file);
CREATE INDEX IF NOT EXISTS idx_manual_page ON manual_chunks(page_number);

-- 5. Notifications & Broadcast Updates
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'Notices', -- 'All', 'Alerts', 'Notices'
    priority VARCHAR(50) DEFAULT 'normal', -- 'urgent', 'normal'
    badge VARCHAR(50),
    timestamp_str VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Activity & Query Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    action_type VARCHAR(50),
    query_text TEXT,
    source_tag VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 7. AI Performance & Usage Statistics
CREATE TABLE IF NOT EXISTS ai_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100),
    query_count INT DEFAULT 1,
    latency_ms NUMERIC,
    status VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Admin Users
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. System Settings
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Seed Default Admin & System Settings
INSERT INTO admin_users (username, password_hash, full_name, role)
VALUES ('admin', encode(digest('admin123', 'sha256'), 'hex'), 'Census Admin Officer', 'admin')
ON CONFLICT (username) DO NOTHING;

INSERT INTO system_settings (key, value)
VALUES 
    ('active_model', 'gemini-2.5-flash'),
    ('technical_assistant_name', 'Shahin Sha A.'),
    ('technical_assistant_phone', '+91 84534 41975'),
    ('supervisor_name', 'S. A. Ahmed'),
    ('circle_name', 'Lakhipur Circle')
ON CONFLICT (key) DO NOTHING;

-- Seed Sample Notifications
INSERT INTO notifications (title, content, category, priority, badge, timestamp_str)
VALUES 
    ('Meeting Schedule - Oct 25', 'Mandatory briefing for regional coordinators regarding data collection protocols and verification workflows.', 'Notices', 'normal', 'Oct 25', '2 hours ago'),
    ('New Demographic Database Uploaded', 'The latest demographic dataset for Lakhipur Circle has been successfully integrated into the central knowledge repository.', 'Alerts', 'normal', 'Database', 'Yesterday'),
    ('Census Deadline Extension', 'Due to field operations requirements in northern districts, the house listing submission deadline has been extended by 48 hours.', 'Alerts', 'urgent', 'Urgent', 'Oct 20');
