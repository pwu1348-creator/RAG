-- RAG System Database Schema
-- 文件解析服务 (Port 8001)

-- 管理员表
CREATE TABLE IF NOT EXISTS admins (
    admin_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(128) UNIQUE,
    phone VARCHAR(32),
    real_name VARCHAR(64),
    role ENUM('super_admin', 'admin') DEFAULT 'admin',
    status ENUM('active', 'inactive', 'locked') DEFAULT 'active',
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(128) UNIQUE,
    avatar_url TEXT,
    department VARCHAR(128),
    status ENUM('active', 'inactive', 'locked') DEFAULT 'active',
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 管理员-用户关联表(记录管理员对用户的管理操作)
CREATE TABLE IF NOT EXISTS admin_user_relations (
    relation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    admin_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    action_type ENUM('create', 'update', 'delete', 'lock', 'unlock', 'reset_password') NOT NULL,
    action_detail JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_admin (admin_id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    kb_id VARCHAR(64) PRIMARY KEY,
    index_id VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    owner_type ENUM('user', 'admin') DEFAULT 'user',
    owner_id VARCHAR(64) NOT NULL,
    status ENUM('active', 'inactive') DEFAULT 'active',
    doc_count INT DEFAULT 0,
    total_chunks INT DEFAULT 0,
    embedding_model VARCHAR(128),
    vector_dimension INT DEFAULT 1024,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_index_id (index_id),
    INDEX idx_owner (owner_type, owner_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    doc_id VARCHAR(64) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(32),
    file_size BIGINT,
    minio_url TEXT,
    minio_bucket VARCHAR(128),
    minio_object VARCHAR(512),
    total_pages INT DEFAULT 0,
    total_chunks INT DEFAULT 0,
    text_length INT DEFAULT 0,
    title VARCHAR(512),
    has_images BOOLEAN DEFAULT FALSE,
    has_tables BOOLEAN DEFAULT FALSE,
    has_formulas BOOLEAN DEFAULT FALSE,
    image_count INT DEFAULT 0,
    parser VARCHAR(64),
    processing_time FLOAT,
    status ENUM('processing', 'completed', 'failed') DEFAULT 'processing',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    extra_metadata JSON,
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 文档分块表
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id VARCHAR(128) PRIMARY KEY,
    doc_id VARCHAR(64) NOT NULL,
    kb_id VARCHAR(64) NOT NULL,
    content TEXT,
    chunk_index INT,
    page_idx INT DEFAULT 0,
    bbox VARCHAR(64),
    chunk_type VARCHAR(32) DEFAULT 'text',
    img_id VARCHAR(128),
    char_count INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_kb_id (kb_id),
    INDEX idx_chunk_index (chunk_index),
    INDEX idx_page_idx (page_idx)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户-知识库关联表
CREATE TABLE IF NOT EXISTS user_kb_relations (
    relation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    kb_id VARCHAR(64) NOT NULL,
    role ENUM('owner', 'editor', 'viewer') DEFAULT 'viewer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_kb (user_id, kb_id),
    INDEX idx_kb (kb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 知识库-文档关联表（多对多）
CREATE TABLE IF NOT EXISTS kb_document_relations (
    relation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(64) NOT NULL,
    doc_id VARCHAR(64) NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    progress INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    UNIQUE KEY uk_kb_doc (kb_id, doc_id),
    INDEX idx_kb (kb_id),
    INDEX idx_doc (doc_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 文档图片表
CREATE TABLE IF NOT EXISTS document_images (
    img_id VARCHAR(128) PRIMARY KEY,
    doc_id VARCHAR(64) NOT NULL,
    kb_id VARCHAR(64) NOT NULL,
    img_url TEXT,
    img_path_local VARCHAR(512),
    page_idx INT DEFAULT 0,
    bbox VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_kb_id (kb_id),
    INDEX idx_page_idx (page_idx)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 登录日志表
CREATE TABLE IF NOT EXISTS login_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_type ENUM('admin', 'user') NOT NULL,
    account_id VARCHAR(64) NOT NULL,
    login_ip VARCHAR(64),
    login_user_agent TEXT,
    login_status ENUM('success', 'failed') NOT NULL,
    fail_reason VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_account (account_type, account_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    operator_type ENUM('admin', 'user') NOT NULL,
    operator_id VARCHAR(64) NOT NULL,
    operation_type VARCHAR(64) NOT NULL,
    operation_target VARCHAR(64),
    operation_detail JSON,
    operation_ip VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_operator (operator_type, operator_id),
    INDEX idx_type (operation_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(64) NOT NULL,
    setting_key VARCHAR(128) NOT NULL,
    setting_value TEXT,
    value_type ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_editable BOOLEAN DEFAULT TRUE,
    is_visible BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_category_key (category, setting_key),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- API配置表(支持多模型)
CREATE TABLE IF NOT EXISTS api_configs (
    api_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    api_type ENUM('embedding', 'llm', 'parser') NOT NULL,
    provider VARCHAR(64) NOT NULL,
    base_url TEXT NOT NULL,
    api_key TEXT,
    model_name VARCHAR(128),
    max_tokens INT DEFAULT 2048,
    timeout INT DEFAULT 30,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    config_json JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (api_type),
    INDEX idx_default (is_default),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 检索设置表
CREATE TABLE IF NOT EXISTS retrieval_settings (
    setting_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(64),
    search_type ENUM('semantic', 'keyword', 'hybrid') DEFAULT 'semantic',
    top_k INT DEFAULT 5,
    similarity_threshold FLOAT DEFAULT 0.7,
    rerank_enabled BOOLEAN DEFAULT FALSE,
    rerank_model VARCHAR(128),
    keyword_weight FLOAT DEFAULT 0.3,
    semantic_weight FLOAT DEFAULT 0.7,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    INDEX idx_kb (kb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 系统统计数据表
CREATE TABLE IF NOT EXISTS system_statistics (
    stat_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stat_type VARCHAR(64) NOT NULL UNIQUE,
    stat_value BIGINT DEFAULT 0,
    stat_extra JSON,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (stat_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 初始化系统统计数据
INSERT INTO system_statistics (stat_type, stat_value) VALUES
    ('total_users', 0),
    ('active_users', 0),
    ('total_documents', 0),
    ('completed_documents', 0),
    ('total_chunks', 0),
    ('total_storage', 0),
    ('total_knowledge_bases', 0);
