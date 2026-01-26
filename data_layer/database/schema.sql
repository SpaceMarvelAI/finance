-- =========================================================
-- DATABASE: financial_automation
-- SCHEMA: public
-- =========================================================

-- ========================
-- COMPANIES
-- ========================
CREATE TABLE public.companies (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50),
    registration_number VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#1976D2',
    secondary_color VARCHAR(7) DEFAULT '#424242',
    currency VARCHAR(3) DEFAULT 'INR',
    fiscal_year_start VARCHAR(5),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    company_aliases TEXT[]
);

CREATE INDEX idx_companies_name ON public.companies(name);

-- ========================
-- USERS
-- ========================
CREATE TABLE public.users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_id VARCHAR(36) NOT NULL,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT users_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

-- ========================
-- CUSTOMERS
-- ========================
CREATE TABLE public.customers (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_code VARCHAR(50),
    tax_id VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    payment_terms_days INTEGER DEFAULT 30,
    credit_limit NUMERIC(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customers_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE INDEX idx_customers_company ON public.customers(company_id);
CREATE INDEX idx_customers_name ON public.customers(customer_name);
CREATE INDEX idx_customers_active ON public.customers(is_active);

-- ========================
-- VENDORS
-- ========================
CREATE TABLE public.vendors (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_code VARCHAR(50),
    tax_id VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    payment_terms_days INTEGER DEFAULT 30,
    credit_limit NUMERIC(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vendors_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE INDEX idx_vendors_company ON public.vendors(company_id);
CREATE INDEX idx_vendors_name ON public.vendors(vendor_name);
CREATE INDEX idx_vendors_active ON public.vendors(is_active);

-- ========================
-- DOCUMENTS
-- ========================
CREATE TABLE public.documents (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_type VARCHAR(10),
    file_size INTEGER,
    document_type VARCHAR(50),
    document_number VARCHAR(100),
    document_date DATE,
    category VARCHAR(50),
    docling_parsed_data JSONB,
    canonical_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    confidence_score NUMERIC(3,2),
    vendor_name VARCHAR(255),
    customer_name VARCHAR(255),
    grand_total NUMERIC(15,2) DEFAULT 0.0,
    tax_total NUMERIC(15,2) DEFAULT 0.0,
    paid_amount NUMERIC(15,2) DEFAULT 0.0,
    outstanding NUMERIC(15,2) DEFAULT 0.0,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT documents_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE INDEX idx_documents_company ON public.documents(company_id);
CREATE INDEX idx_documents_category ON public.documents(category);
CREATE INDEX idx_documents_number ON public.documents(document_number);
CREATE INDEX idx_documents_type ON public.documents(document_type);
CREATE INDEX idx_documents_uploaded ON public.documents(uploaded_at);

-- ========================
-- VENDOR INVOICES (AP)
-- ========================
CREATE TABLE public.vendor_invoices (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    vendor_id VARCHAR(36),
    document_id VARCHAR(36),
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date TIMESTAMP,
    due_date TIMESTAMP,
    subtotal_amount NUMERIC(15,2),
    tax_amount NUMERIC(15,2),
    total_amount NUMERIC(15,2),
    paid_amount NUMERIC(15,2) DEFAULT 0.0,
    outstanding_amount NUMERIC(15,2),
    original_currency VARCHAR(3),
    exchange_rate NUMERIC(10,6),
    inr_amount NUMERIC(15,2),
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_terms_days INTEGER,
    line_items JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vendor_invoices_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES public.companies(id),
    CONSTRAINT vendor_invoices_vendor_id_fkey
        FOREIGN KEY (vendor_id) REFERENCES public.vendors(id),
    CONSTRAINT vendor_invoices_document_id_fkey
        FOREIGN KEY (document_id) REFERENCES public.documents(id)
);

CREATE INDEX idx_vendor_invoices_company ON public.vendor_invoices(company_id);
CREATE INDEX idx_vendor_invoices_date ON public.vendor_invoices(invoice_date);
CREATE INDEX idx_vendor_invoices_due ON public.vendor_invoices(due_date);
CREATE INDEX idx_vendor_invoices_status ON public.vendor_invoices(payment_status);
CREATE INDEX idx_vendor_invoices_vendor ON public.vendor_invoices(vendor_id);

-- ========================
-- CUSTOMER INVOICES (AR)
-- ========================
CREATE TABLE public.customer_invoices (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36),
    document_id VARCHAR(36),
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date TIMESTAMP,
    due_date TIMESTAMP,
    subtotal_amount NUMERIC(15,2),
    tax_amount NUMERIC(15,2),
    total_amount NUMERIC(15,2),
    received_amount NUMERIC(15,2) DEFAULT 0.0,
    outstanding_amount NUMERIC(15,2),
    original_currency VARCHAR(3),
    exchange_rate NUMERIC(10,6),
    inr_amount NUMERIC(15,2),
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_terms_days INTEGER,
    line_items JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_invoices_company_id_fkey
        FOREIGN KEY (company_id) REFERENCES public.companies(id),
    CONSTRAINT customer_invoices_customer_id_fkey
        FOREIGN KEY (customer_id) REFERENCES public.customers(id),
    CONSTRAINT customer_invoices_document_id_fkey
        FOREIGN KEY (document_id) REFERENCES public.documents(id)
);

CREATE INDEX idx_customer_invoices_company ON public.customer_invoices(company_id);
CREATE INDEX idx_customer_invoices_customer ON public.customer_invoices(customer_id);
CREATE INDEX idx_customer_invoices_date ON public.customer_invoices(invoice_date);
CREATE INDEX idx_customer_invoices_due ON public.customer_invoices(due_date);
CREATE INDEX idx_customer_invoices_status ON public.customer_invoices(payment_status);

-- ========================
-- WORKFLOWS
-- ========================
CREATE TABLE public.workflows (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'planned',
    company_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    query TEXT,
    domain VARCHAR(50),
    report_type VARCHAR(100),
    workflow_definition JSONB NOT NULL,
    execution_result JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    output_file_path VARCHAR(500),
    execution_time_ms INTEGER,
    error_message TEXT
);

CREATE INDEX idx_workflows_company ON public.workflows(company_id);
CREATE INDEX idx_workflows_created ON public.workflows(created_at);
CREATE INDEX idx_workflows_status ON public.workflows(status);
CREATE INDEX idx_workflows_user ON public.workflows(user_id);

-- ========================
-- WORKFLOW NODES
-- ========================
CREATE TABLE public.workflow_nodes (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    node_name VARCHAR(255),
    position_x INTEGER,
    position_y INTEGER,
    params JSON,
    input_data JSON,
    output_data JSON,
    status VARCHAR(20),
    execution_time_ms INTEGER,
    error_message TEXT,
    "order" INTEGER,
    created_at TIMESTAMP,
    CONSTRAINT workflow_nodes_workflow_id_fkey
        FOREIGN KEY (workflow_id) REFERENCES public.workflows(id)
);

CREATE INDEX ix_workflow_nodes_workflow_id ON public.workflow_nodes(workflow_id);

-- ========================
-- WORKFLOW EXECUTION LOGS
-- ========================
CREATE TABLE public.workflow_execution_logs (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    step_number INTEGER NOT NULL,
    step_id VARCHAR(50) NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    status VARCHAR(20),
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    error_message TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT workflow_execution_logs_workflow_id_fkey
        FOREIGN KEY (workflow_id) REFERENCES public.workflows(id)
);

CREATE INDEX idx_workflow_logs_workflow ON public.workflow_execution_logs(workflow_id);
CREATE INDEX idx_workflow_logs_created ON public.workflow_execution_logs(created_at);
