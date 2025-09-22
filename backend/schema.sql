-- MySQL Database Setup Script
-- Converted from the provided DDL schema

-- Create database
CREATE DATABASE IF NOT EXISTS timesheet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE timesheet_db;

-- Enable UUID functions (MySQL 8.0+)
-- For older versions, you'll need to use CHAR(36) and generate UUIDs in application

-- ====================================================
-- TENANCY TABLES
-- ====================================================

-- Organisation table
CREATE TABLE organisation (
    organisation_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(200) NOT NULL UNIQUE,
    client_id VARCHAR(300) NOT NULL UNIQUE,
    client_secret VARCHAR(300) NOT NULL UNIQUE,
    redirect_uri VARCHAR(300) NOT NULL UNIQUE,
    authority VARCHAR(300) NOT NULL UNIQUE,
    scopes VARCHAR(300) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tenant separate database table (would be in separate database in production)
CREATE TABLE tenant_separate_db (
    tenant_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    tenant_name VARCHAR(200) NOT NULL UNIQUE,
    organisation_id CHAR(36) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (organisation_id) REFERENCES organisation(organisation_id) ON DELETE CASCADE
);

-- Accounts table
CREATE TABLE accounts (
    accounts_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    organisation_id CHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (organisation_id) REFERENCES organisation(organisation_id) ON DELETE CASCADE
);

-- ====================================================
-- USERS & ROLES TABLES
-- ====================================================

-- Users table
CREATE TABLE users (
    users_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(100),
    employee_id VARCHAR(50) UNIQUE,
    hire_date DATE,
    hourly_rate DECIMAL(10,2),
    `group` VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(255) NOT NULL,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_employee_id (employee_id)
);

-- Roles table
CREATE TABLE roles (
    roles_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- User roles junction table
CREATE TABLE user_roles (
    user_roles_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    users_id CHAR(36) NOT NULL,
    roles_id CHAR(36) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (users_id) REFERENCES users(users_id) ON DELETE CASCADE,
    FOREIGN KEY (roles_id) REFERENCES roles(roles_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role (users_id, roles_id)
);

-- ====================================================
-- PROJECTS TABLES
-- ====================================================

-- Project bill codes table
CREATE TABLE project_bill_code (
    project_billable_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    project_bill_codes VARCHAR(100) NOT NULL,
    project_description VARCHAR(500),
    active BOOLEAN DEFAULT TRUE
);

-- Projects table
CREATE TABLE projects (
    projects_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    accounts_id CHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    client_name VARCHAR(200),
    project_code VARCHAR(50) UNIQUE,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15,2),
    hourly_rate DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active',
    is_billable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (accounts_id) REFERENCES accounts(accounts_id) ON DELETE CASCADE,
    INDEX idx_projects_code (project_code),
    INDEX idx_projects_status (status)
);

-- Project assignments table
CREATE TABLE project_assignments (
    project_assignments_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    pa_users_id CHAR(36) NOT NULL,
    projects_id CHAR(36) NOT NULL,
    bill_code CHAR(36) NOT NULL,
    role_in_project VARCHAR(100),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pa_users_id) REFERENCES users(users_id) ON DELETE CASCADE,
    FOREIGN KEY (projects_id) REFERENCES projects(projects_id) ON DELETE CASCADE,
    FOREIGN KEY (bill_code) REFERENCES project_bill_code(project_billable_id) ON DELETE RESTRICT,
    INDEX idx_pa_user (pa_users_id),
    INDEX idx_pa_project (projects_id)
);

-- ====================================================
-- TIMESHEETS TABLES
-- ====================================================

-- Timesheet table
CREATE TABLE timesheet (
    timesheet_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    projects_assignments_id CHAR(36) NOT NULL,
    monday DECIMAL(10,1),
    tuesday DECIMAL(10,1),
    wednesday DECIMAL(10,1),
    thursday DECIMAL(10,1),
    friday DECIMAL(10,1),
    saturday DECIMAL(10,1),
    sunday DECIMAL(10,1),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_hours_worked DECIMAL(5,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    approved_at TIMESTAMP NULL,
    notes TEXT,
    bill_code CHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (projects_assignments_id) REFERENCES project_assignments(project_assignments_id) ON DELETE CASCADE,
    INDEX idx_timesheet_assignment (projects_assignments_id),
    INDEX idx_timesheet_dates (start_date, end_date),
    INDEX idx_timesheet_status (status)
);

-- ====================================================
-- LEAVE MANAGEMENT TABLES
-- ====================================================

-- Leave types table
CREATE TABLE leave_types (
    leave_type_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_paid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Leave requests table
CREATE TABLE leave_requests (
    leave_requests_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    leave_type_id CHAR(36) NOT NULL,
    users_id CHAR(36) NOT NULL,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days INT NOT NULL,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    approved_at TIMESTAMP NULL,
    rejection_reason TEXT,
    emergency_contact VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(leave_type_id) ON DELETE RESTRICT,
    FOREIGN KEY (users_id) REFERENCES users(users_id) ON DELETE CASCADE,
    INDEX idx_leave_user (users_id),
    INDEX idx_leave_dates (start_date, end_date),
    INDEX idx_leave_status (status)
);

-- Create refresh tokens table for JWT management
CREATE TABLE refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_refresh_tokens_user (user_id),
    INDEX idx_refresh_tokens_hash (token_hash),
    INDEX idx_refresh_tokens_expires (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(users_id) ON DELETE CASCADE
);

-- ====================================================
-- SAMPLE DATA INSERTION
-- ====================================================

-- Insert default organisation
INSERT INTO organisation (organisation_id, name, client_id, client_secret, redirect_uri, authority, scopes) 
VALUES (
    UUID(),
    'Default Organisation',
    'default_client_id',
    'default_client_secret',
    'http://localhost:3000/callback',
    'https://login.microsoftonline.com/common',
    'openid profile email'
);

-- Insert default account
SET @org_id = (SELECT organisation_id FROM organisation WHERE name = 'Default Organisation');
INSERT INTO accounts (accounts_id, organisation_id, name, description) 
VALUES (UUID(), @org_id, 'Default Account', 'Default account for the organisation');

-- Insert default roles
INSERT INTO roles (roles_id, name, description, permissions) VALUES
(UUID(), 'Admin', 'System Administrator', JSON_OBJECT(
    'create_user', true,
    'read_users', true,
    'update_users', true,
    'delete_users', true,
    'create_project', true,
    'read_all_timesheets', true,
    'approve_timesheet', true,
    'approve_leave', true,
    'manage_leave_types', true,
    'assign_project', true,
    'read_assignments', true
)),
(UUID(), 'Manager', 'Project Manager', JSON_OBJECT(
    'create_project', true,
    'read_all_timesheets', true,
    'approve_timesheet', true,
    'approve_leave', true,
    'assign_project', true,
    'read_assignments', true
)),
(UUID(), 'Employee', 'Regular Employee', JSON_OBJECT(
    'create_timesheet_others', false,
    'create_leave_others', false
));

-- Insert default leave types
INSERT INTO leave_types (leave_type_id, name, description, is_paid) VALUES
(UUID(), 'Annual Leave', 'Yearly vacation leave', TRUE),
(UUID(), 'Sick Leave', 'Medical leave', TRUE),
(UUID(), 'Maternity Leave', 'Maternity/Paternity leave', TRUE),
(UUID(), 'Emergency Leave', 'Emergency personal leave', FALSE),
(UUID(), 'Unpaid Leave', 'Unpaid personal leave', FALSE);

-- Insert project bill codes
INSERT INTO project_bill_code (project_billable_id, project_bill_codes, project_description, active) VALUES
(UUID(), 'DEV001', 'Development - Frontend', TRUE),
(UUID(), 'DEV002', 'Development - Backend', TRUE),
(UUID(), 'TEST001', 'Testing - Manual', TRUE),
(UUID(), 'TEST002', 'Testing - Automation', TRUE),
(UUID(), 'PM001', 'Project Management', TRUE),
(UUID(), 'DOC001', 'Documentation', TRUE);

-- Create default admin user (password: admin123)
-- Note: In production, use a secure password hash
INSERT INTO users (users_id, email, username, first_name, last_name, `group`, password_hash) 
VALUES (
    UUID(),
    'admin@example.com',
    'admin',
    'System',
    'Administrator',
    'IT',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJL1JJ.6G'  -- admin123
);

-- Assign admin role to admin user
SET @admin_user_id = (SELECT users_id FROM users WHERE email = 'admin@example.com');
SET @admin_role_id = (SELECT roles_id FROM roles WHERE name = 'Admin');
INSERT INTO user_roles (user_roles_id, users_id, roles_id) 
VALUES (UUID(), @admin_user_id, @admin_role_id);

-- ====================================================
-- INDEXES FOR PERFORMANCE
-- ====================================================

-- Additional indexes for better query performance
CREATE INDEX idx_user_roles_user ON user_roles(users_id);
CREATE INDEX idx_user_roles_role ON user_roles(roles_id);
CREATE INDEX idx_projects_account ON projects(accounts_id);
CREATE INDEX idx_accounts_org ON accounts(organisation_id);

-- ====================================================
-- VIEWS FOR COMMON QUERIES
-- ====================================================

-- View for user details with roles
CREATE VIEW user_details_with_roles AS
SELECT 
    u.users_id,
    u.email,
    u.username,
    u.first_name,
    u.last_name,
    u.department,
    u.employee_id,
    u.is_active,
    GROUP_CONCAT(r.name) as roles,
    u.created_at
FROM users u
LEFT JOIN user_roles ur ON u.users_id = ur.users_id AND ur.is_active = TRUE
LEFT JOIN roles r ON ur.roles_id = r.roles_id AND r.is_active = TRUE
WHERE u.is_active = TRUE
GROUP BY u.users_id;

-- View for project assignments with user and project details
CREATE VIEW project_assignments_detailed AS
SELECT 
    pa.project_assignments_id,
    pa.pa_users_id,
    pa.projects_id,
    pa.role_in_project,
    pa.start_date,
    pa.end_date,
    pa.is_active,
    u.first_name,
    u.last_name,
    u.email,
    p.name as project_name,
    p.client_name,
    p.status as project_status,
    pbc.project_bill_codes,
    pbc.project_description
FROM project_assignments pa
JOIN users u ON pa.pa_users_id = u.users_id
JOIN projects p ON pa.projects_id = p.projects_id
JOIN project_bill_code pbc ON pa.bill_code = pbc.project_billable_id
WHERE pa.is_active = TRUE;

COMMIT;

-- Display success message
SELECT 'Database setup completed successfully!' as status;